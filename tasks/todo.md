# powerswing POC: task list

- [x] Step 1 setup: uv venv (py3.12), requirements.txt, src/ layout, seeds, `python -m src.run_all`
- [x] Step 2 explore: data/README_data.md, loader (5 Hz, per node + job totals), sample plots, big-drop detection + stats
- [x] Step 3 tasks: forecasting 1/5/10 s; drop warning (5 s window, lead time); job/time splits; leave-one-workload-out
- [x] Step 4 baselines: persistence, moving average, rhythm (autocorrelation repeat-last-cycle)
- [x] Step 5 models: LightGBM, tiny TCN (46k params), Chronos-Bolt-Small + TimesFM 2.5 zero-shot, CPU latency
- [x] Step 6 evaluation: MAE/RMSE/MAPE by horizon and workload, drop metrics, PR curve, overlays, bars, horizon chart
- [x] Step 7 simulation: raw / always-burn / predictive (+ pre-ramp, reactive, always-on limiter refs), 100 MW scale-up
- [x] Step 8 deliverables: reports/results.md, notebooks 01-03, summary slide
- [x] Independent review (Codex gpt-5.6-sol, read-only): 1 critical + 4 major + 3 minor, all fixed
- [x] Final clean end-to-end run + re-execute notebooks

## Review
- Codex critical: best model/classifier selected on test -> now validation-only.
- Majors fixed: threshold quantile range, future-peak in sim (now 2.8 kW rating), circular tiling (now jobs chained), wrong residual-violation claim (now data-driven).
- Minors fixed: mean lead over caught events only, causal ffill, sync-skew statistic, edge-device wording.

## Paper track, Step 1: regime study (2026-10-12)
Goal: does a learned predictor beat the simple rhythm rule once arming readiness has a cost?
- [x] src/regime.py: arming sources (ML alarm, rhythm alarm, ML forecast, rhythm forecast, oracle) x threshold sweep x actuator latency
- [x] cost model: fill energy + standby power while armed + per-arming start cost
- [x] operating points chosen on VALIDATION, evaluated on test
- [x] Pareto chart: violations removed vs armed-time fraction
- [x] regime map: best strategy per (latency, standby cost)
- [x] job-clustered paired bootstrap CI: ML vs rhythm
- [ ] Codex review of regime.py
- (parallel) researcher agent vetting Elsayed 2026 + MIT Supercloud datasets

### Step 1 findings (2026-10-12)
- All 4 triggers (learned/rhythm x alarm/forecast) sit on ~one readiness curve; oracle needs 30% armed for 100%, triggers need 45-60% armed for 80%. Learning does not move the frontier much at 80%.
- At >=90% target only learned triggers get there (ML alarm 68% armed, ML forecast 71%); rhythm alarm plateaus ~83%.
- Paired job bootstrap: ML alarm minus rhythm alarm cut = +11 pts, 95% CI [-8, +34] (not significant, ~12 units); ML overhead +0.6 pts [0.3, 1.2].
- Standby cost: always-on loses once standby >0 (2% standby: always-on 5.4% vs ML 4.3% vs oracle 3.7%).
- Data caveat (dataset agent): NVML GetPowerUsage on H100 = 1 s trailing average. Our raw check: largest single step = median 23-33% of a fall -> consistent with smoothing. Real ramps faster, our lead times may be overstated ~0.5 s. NLR README does not state which NVML call.
- Datasets: Elsayed 2026 (H100+B200, single node, 15 min, 1 s averaged, license conflict CC BY vs BY-NC-ND) = maybe; MIT Supercloud (V100, instantaneous 10 Hz, real jobs, 2.4 TB, CC BY-NC-ND) = research-only.
- [x] Codex review of regime.py: 0 critical, 2 major (winner chosen on test; oracle not violation-free), 1 minor (float rounding merge). All fixed, re-run.
### Step 1 after fixes (2026-10-12)
- Winner now chosen on validation. Zero start cost: rhythm forecast "wins" every cell but its test cut is 73% (val >= 80%), ML alarm 86% at higher cost. Start cost 2-10 s: always-on wins most cells. ML never wins on validation selection.
- Lesson: "cheapest that meets 80%" compares different cut levels and val->test thresholds do not transfer reliably with ~12 units. Next: fixed-cut cost comparison or violation-penalty objective, more independent units.
- Oracle now violation-free (100% cut, 30% armed); its cost at high start cost is large because it is not cost-optimised.

## Paper track, Step 2: more data + beat rhythm (2026-10-12)
User: "get more data, combine, train more models, try to beat rhythmic ones, find a publishable angle".
Constraint: only 32 GB free disk -> stream-download, reduce to 5 Hz node parquet, delete raw.
Licenses: Elsayed figshare CC BY 4.0 (GitHub says BY-NC-ND, conflict); MIT Supercloud CC BY-NC-ND -> research/paper use only, never product, never redistribute.
Research questions:
 RQ1 cross-site/cross-hardware: does a model trained on pooled diverse data beat rhythm on UNSEEN datasets/workloads (fixes LOWO failure)?
 RQ2 better target: predict time-to-next-drop / min power over next k s directly, to close the gap to the oracle (30% armed).
Plan:
- [ ] A. Elsayed loader (H100 + B200 8-GPU, 1 s averaged NVML) -> data/processed/ext_elsayed_*
- [ ] B. MIT Supercloud labelled-job subset loader (V100, 10 Hz instantaneous) -> data/processed/ext_supercloud_*
- [ ] C. Normalize all power to fraction of node rated power (x 2800 W "NLR-equivalent") so one feature pipeline works across hardware
- [ ] D. Pooled training + leave-one-dataset-out + leave-one-workload-out vs rhythm (tuned on val)
- [ ] E. Direct time-to-drop / min-future-power targets + arming from them; compare on readiness curve with oracle
- [ ] F. Codex review, results write-up
- [x] A. Elsayed loader: 32 unique sessions, 8 h, H100+B200 8-GPU, drops every 5-16 s (clockwork), 1 s NVML averaging visible, zip README says CC BY-NC-ND.
- [x] B. Supercloud loader: 560 labelled jobs (80/class x 7), 973 traces, 1,292 node-h, 4.4 GB raw streamed, 248 MB parquet. V100 instantaneous -> drop detector fires 507/h (flicker). 4 h timezone shift handled.
- [x] E. Control-aligned target (src/aligned.py): NLR test AP learned 0.939 vs rhythm replay 0.580 (old drop clf 0.607); learned wins every workload.
  Readiness (val-chosen, test-scored, 2% standby, 1 s latency): target 90% -> learned 92.3% cut at 45% armed vs rhythm 83.3% (cannot reach) at 67% armed; cut diff +9.1 pts CI [3.7, 19.6]. Target 95% -> learned 95.1% at 52% armed; diff +11.8 [6.0, 23.4]. Oracle 100% at 30% armed. Table reports/tables/regime_targets.csv.
- [ ] D. src/crossdata.py running (in-domain / leave-one-dataset-out / pooled; AP + bootstrap + readiness). Log data/processed/crossdata.log
- [x] Codex review aligned.py: 0 critical. Major 1: aligned target trained for 1 s latency only -> report aligned sources at 1 s; latency-specific models = TODO. Major 2: val used for early stopping AND threshold choice -> TODO final run: split val units into halves (early-stop half / threshold half), for aligned + crossdata. Minor: oracle clipped at trace start; per-workload AP pooled by sample.
- [x] D. crossdata RAW (reports/tables/crossdata_*_raw.csv): in-domain learned > rhythm on NLR (+0.36 AP, CI [0.32,0.42]), Elsayed (+0.12, ns, 6 units), Supercloud (+0.02 sig but pos_rate 0.89 = flicker, meaningless). LODO: NLR -0.06 ns, Elsayed -0.14 sig worse, Supercloud +0.006 ns -> NO transfer. Pooled: NLR +0.34, Elsayed +0.09 ns, Supercloud +0.03.
- [ ] D2. Sensor harmonization: Supercloud 1 s trailing mean (match NVML H100 averaging), rerun -> crossdata_*_harmonized.csv
- [ ] D3. Shape-only features (drop absolute level) + few-minute site adaptation test
- [x] D2 harmonized (crossdata_*_harmonized.csv): Supercloud pos_rate fixed. In-domain: NLR +0.36 [0.32,0.42]; Elsayed +0.12 ns (6 units); Supercloud 0.817 vs 0.668 +0.15 [0.11,0.19] (112 jobs). LODO: NLR +0.08 [-0.01,0.15] ns; Elsayed -0.11 sig; Supercloud -0.20 sig. Pooled: NLR +0.36, Elsayed +0.09 ns, Supercloud +0.15 [0.11,0.18].
- [x] D3 transfer (reports/tables/transfer_harmonized.csv): shape-only features keep in-domain AP (NLR 0.939, Elsayed 0.880, SC 0.820) and make LODO->NLR significant (0.658 vs 0.580 [+0.02,+0.12]); LODO Elsayed tie (0.706 vs 0.769); LODO SC still loses (0.473 vs 0.668). Site adaptation by continued boosting: NLR +60 min -> 0.742 sig; Elsayed and SC adaptation hurts/no help (overfits tiny local data). Adaptation method weak -> future work.

## Paper track, Step 3: final run + draft (2026-10-12)
- [x] Fixes: val halves (es/thr), per-latency aligned models, decision delay 1 sample, 6 s target window = hold, full threshold sweeps, engaged = armed or filling, NLR inference cluster = session, 1000 boots, 5 adaptation draws.
- [x] Final chain (aligned -> regime -> crossdata -> transfer) ALL_DONE 22:55. Logs data/processed/final_logs/.
- [x] KEY NUMBERS: NLR AP learned 0.97 vs rhythm 0.72 (old big-drop clf 0.56). Engaged time for 90% removal: learned 55.8% vs rhythm 99.2% (diff -43.4, CI -52.3..-10.2); 95%: 69.8 vs 99.2 (CI -43.9..-19.0); vs big-drop learned ns. Pooled: NLR 0.97/0.72 sig, Supercloud 0.91/0.77 sig (7/7 classes), Elsayed 0.94/0.91 ns (diffusion favours rhythm). Unseen site: learned never better (SC sig worse). 60 min adaptation does not reliably recover.
- [x] Paper: src/paper.py + paper/template.tex -> paper/main.tex, main.pdf (3 pages, tectonic). Email draft paper/email_nlr_authors.md.
- [ ] Codex round 2 review (running)
- [x] Codex round 2: critical = label window shifted ~1 s past arm window + arm lasted hold+1; major = coarse sweep. Fixed (half-open _arm, label v in [e+FS, e+hold-1], dense 200-quantile grid at L=1).
- [x] Round-3 chain ALL_DONE 2026-10-13 01:31. FINAL NUMBERS: NLR AP learned 0.96 vs rhythm 0.67 (big-drop clf 0.58). Engaged time needed (NLR test, 1 s): 90% removal learned 48.4% vs rhythm 99.2% (diff -50.8, CI -57.4..-8.8); 95%: 58.4 vs 99.2 (CI -49.1..-31.4); vs big-drop learned 64.3% at 90% (diff -15.9, CI -25.7..-3.9, now sig), 95% CI -26.3..0.5 ns. Oracle 29.8%. Pooled: NLR 0.96/0.67 sig; SC 0.88/0.74 sig 7/7; Elsayed 0.92/0.88 ns. LODO full feats NLR 0.53 (sig worse); shape-only NLR 0.65/0.67 ns, SC 0.66/0.74 sig worse; 60 min adapt NLR 0.71 (0.62-0.77), SC 0.64.
- [x] Paper rebuilt (3 pages); stale "not significant vs big-drop" sentence fixed.
- [ ] Codex round 3 (final) running -> reports/review/codex_final_review_r3_raw.md. After it: escalate to Raheel per lane (max 3 rounds).
- [x] Codex r3 (reports/review/codex_final_review_r3_2026-10-13.md): fixes 1-4 PASS; 268/268 numbers reconcile. CRITICAL: Table II / abstract 48.4 vs 99.2 is test-frontier (best threshold read off test) -> abstract now leads with validation-chosen op point (86.8% removal @45.6% engaged vs rhythm 99.2%); Table II labelled retrospective. Wording fixes applied: AP-only cross-site claim, node cap disclosed, NLR inference val halves dependence disclosed, CIs conditional on single fit, stride disclosed, ~200 thresholds, 7/7 exploratory, forest "unseen site, shape-only", aligned.py docstring. Paper now 4 pages.
- [ ] ESCALATED to Raheel (3 rounds done). Open (need code+rerun, user decision): retrain-based/nested bootstrap or repeated splits; one-node-per-job sensitivity; NLR inference val halves by session; physical actuator/storage model; legacy simulate.py convention. Pred: PES GM reject/major rev; CCAI workshop borderline -> weak accept after fixes.

## arXiv paper (2026-10-15)
- [x] paper/arxiv/template.tex -> main.tex (11 pp, article class, pdflatex-safe ASCII), filled by src/paper.py from numbers.json; tarball paper/arxiv_submission.tar.gz
- [x] References verified on live arXiv/DOI pages (subagent); NVML wording fixed (Ampere except GA100+ averaged; GA100/V100 instantaneous); licences: NLR = NLR dataset licence (not CC), Elsayed figshare CC BY vs zip README BY-NC-ND, Supercloud CC BY-NC-ND
- [x] NEW src/ablation.py matched-pipeline ablation: aligned AP 0.958 vs big-drop label 0.583, diff 0.37 [0.28, 0.49], 12 clusters; drop model AP 0.93 on own label (not a strawman)
- [x] Reviews: fact-check subagent x2, Codex r1 (NOT READY) -> r2 (READY AFTER FIXES) -> r3 (READY AFTER FIXES, 2 wording nits applied), Kimi r1 (READY AFTER FIXES). All in reports/review/arxiv_*.
- [ ] USER: arXiv account/endorsement, affiliation, confirm AI-use statement, submit tarball (cs.LG primary, eess.SY cross-list suggested)
