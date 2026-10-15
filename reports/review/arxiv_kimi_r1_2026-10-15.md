  ## Blocking (must fix before posting)

  **1. Abstract, template.tex line 30 — unsupported comparative claim.**
  ```
  engage it. We show that what the forecaster is trained to predict matters more than which model is used.
  ```
  The paper trains exactly one model class (LightGBM); no model-class comparison exists anywhere in it, so "matters more than which model is used" is not supported by any experiment here. A reviewer will flag this in the first paragraph. Replace line 30 with:
  ```
  engage it. We show that what the forecaster is trained to predict matters.
  ```
  (or, if you want to keep the contrast, scope it to the evidence: "…matters more than the choice between the two predictors we compare:" — the target change is +0.38 AP vs +0.29 AP for learned-over-replay on the aligned target. The unscoped sentence is the one that is indefensible.)

  ## Should fix

  **2. Line 423–424 — unseen-site operating point silently uses the new site's validation data.** For `lodo`, `crossdata.py` chooses the threshold on the held-out site's own validation split (`val`/`thr` rows of the *target* dataset). As written, "unseen site" + "validation-chosen" reads as zero site data. Replace:
  ```
  Validation-chosen operating points tell a slightly different story: with ordinary features, the
  ```
  with:
  ```
  Validation-chosen operating points tell a slightly different story (here the threshold is the only thing calibrated on the new site, on its own validation split; AP uses no site data): with ordinary features, the
  ```

  **3. Lines 167–168 — big-drop definition is not reproducible as stated.** `src/events.py` additionally imposes a 5 s refractory period (`REFRACTORY_S`) and requires the trailing 10 s peak ≥ 1 kW (`MIN_PEAK_W`); both change the label stream. Replace:
  ```
  The \textbf{big-drop} target labels row $t$ positive if a fall of more than 30\% of the trailing 10~s peak
  within 1~s starts in the next 5~s.
  ```
  with:
  ```
  The \textbf{big-drop} target labels row $t$ positive if a fall of more than 30\% of the trailing 10~s peak
  within 1~s starts in the next 5~s (onsets separated by a 5~s refractory period, counted only when the
  trailing peak exceeds 1~kW, so idle-node noise is excluded).
  ```

  **4. Line 345–346 — pooled/LODO training weights datasets equally; undisclosed.** `crossdata.py::train` and `transfer.py::fit` set per-row weights `1/count(dataset)` (normalized), so the 1,292 node-hours of Supercloud do not drown the 8 of Elsayed. All "pooled" and "unseen site" numbers depend on this. After "trained on the other two only (unseen site)." add:
  ```
  Models trained on more than one dataset weight each dataset equally.
  ```

  **5. Line 219 (Table `wl` caption) — per-workload APs carry no intervals, and cannot.** "The gain holds for every workload" (line 210) rests on five point estimates; each inference workload is a single session (one cluster), so no bootstrap interval exists. Change the caption:
  ```
  \caption{NLR test AP on the control-aligned target, 1~s latency.}
  ```
  to:
  ```
  \caption{NLR test AP on the control-aligned target, 1~s latency. Per-workload rows are point estimates; each inference workload is a single session, so no interval is computed.}
  ```

  ## Nits

  - **Line 126** — "without harmonization, 89\% of Supercloud seconds would be labelled ``violation imminent''": the 0.8929 is measured on Supercloud **test** rows at 1 Hz decisions. Say "89\% of Supercloud test seconds".
  - **Line 226** — Llama2-70B LoRA learned AP prints as `1.00` (true value 0.99695). Rounding is honest, but "1.00" reads as a perfect score; consider printing `0.997` for that cell.
  - **Line 31** — "the usual target": nothing cited establishes this target as usual practice (it is your own earlier pipeline's target). "a natural target" or "a generic drop target" is safer.
  - **Lines 187–189** — reproducibility: feature_fraction 0.8, bagging 0.8/1, L2 1.0, ≤3000 rounds, 100-round patience are all unstated; one parenthetical would close the gap. Likewise the aligned/big-drop models train on 1 Hz rows (`TRAIN_STRIDE`) but are scored at 5 Hz — worth one clause in Section 3.4.
  - **Line 115–116** — "the node's rated GPU power": the ratings used are 700 W/GPU (H100), 1000 W/GPU (B200, *assumed* — the dataset states no B200 TDP, `ext_elsayed.py` line 41), 250 W/GPU (V100). One parenthetical makes the normalization reproducible.
  - **Line 159** — "a standby draw of 0 to 5\%": the code also sweeps 10% standby and per-episode start costs (0/2/10 s); none are reported. Harmless, but "we report 0--5\%" would be exact.
  - **Line 53** — `hess` characterized as "perfect preview": consistent with its finite-horizon predictive control over a known disturbance model, but worth a re-read of that paper's exact assumption before posting.

  **Could not verify in this workspace** (pipeline intermediates absent; internally consistent): node-hours and unit counts (248/49/12, 8/32/6, 1,292/560/112 — but 32×15 min = 8 h ✓, 7×80=560 ✓, 12 test clusters = bootstrap units ✓), "1 to 16 nodes", "15-minute sessions", "22% square wave", and the NLR licence name. No leakage found: features and rhythm replay are causal, splits are whole-job, es/thr validation halves are disjoint for the aligned models, and the big-drop model's full-validation early stopping is disclosed.

  **Verdict: READY AFTER FIXES**
