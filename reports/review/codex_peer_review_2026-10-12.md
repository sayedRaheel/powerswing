## Summary

This is a useful, unusually transparent POC, but not yet a defensible paper. I found no obvious train/test leakage in the forecasting pipeline. Splits, feature computation, validation-only model selection, and the main predictive simulation are mostly causal.

The central paper claim does not survive a stronger baseline check. The existing rhythm alarm, when connected to the same forecast-armed limiter, removes 83.25% of violations using 2.38% extra energy. The reported ML controller removes 83.81% using 2.58%. Thus, under the simulator’s own zero-cost arming assumption, the simple rule is effectively as good and slightly cheaper. The paper currently omits this comparison.

The most defensible contribution is narrower:

> On workload families represented in training, causal LightGBM forecasting reduces 5-second per-node MAE relative to the implemented seasonal-rhythm heuristic.

LightGBM beats that heuristic for all five workloads in [forecast_by_workload.csv](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/forecast_by_workload.csv:37). My regrouping also found wins on all 9 held-out training jobs and all 3 trailing inference sessions. This remains an in-distribution result, not evidence of workload-general power prediction.

The official [NLR catalog](https://data.nlr.gov/submissions/312) confirms that these are 5/10 Hz workload measurements and that its facility profiles are modeled rather than measured. The associated [paper](https://arxiv.org/abs/2604.07345) likewise frames facility scaling as model-based.

## Strengths

- No obvious test leakage. Training jobs remain intact across splits, inference is split chronologically, and at most four correlated nodes per job are used. See [src/load.py:180](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/load.py:180).

- Feature causality is handled carefully. Rolling statistics end at the current sample, rhythm windows are historical, and a detected drop enters `t_since_drop` only after the one-second detection window has elapsed. See [src/features.py:114](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/features.py:114) and [src/features.py:135](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/features.py:135).

- Model and threshold selection use validation data rather than test data. LightGBM versus TCN selection, classifier selection, and the 85% validation-recall thresholds are separated correctly. See [src/modeling.py:92](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/modeling.py:92) and [src/evaluate.py:128](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/evaluate.py:128).

- The simulator does not obviously read future realized power when making predictive decisions. It uses saved causal forecasts, delays arming by the assumed latency, and normalizes by a fixed H100 rating rather than the future maximum of each trace. See [src/simulate.py:62](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/simulate.py:62) and [src/simulate.py:111](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/simulate.py:111).

- The leave-one-workload-out experiment is valuable and honestly reported. It exposes severe failure on unseen workload types instead of hiding it. See [generalization_lowo.csv](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/generalization_lowo.csv:2).

- The in-distribution forecasting result is not solely a Stable Diffusion artifact. From the saved predictions, removing Stable Diffusion gives a 41.0% LightGBM gain over rhythm, close to the reported 39.4%.

- Limitations concerning benchmark-driven inference drops, 5 Hz resolution, GPU-only measurement, and simulated actuation are stated more candidly than in many POCs. See [reports/results.md:194](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/results.md:194).

## Weaknesses

- **[critical] The omitted rhythm-armed controller invalidates the ML smoothing headline.** The rhythm alarm already catches 83.46% of events versus 82.43% for LightGBM, although with more alarm episodes. See [drop_warning.csv:2](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/drop_warning.csv:2) and [drop_warning.csv:4](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/drop_warning.csv:4). But false arming has no modeled energy or standby cost. The limiter adds power only when the realized load actually falls, as shown in [src/simulate.py:70](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/simulate.py:70). I replayed the saved test predictions through the same controller:

  - Reported ML alarm plus LightGBM forecast: 29.823 violations/hour, 83.81% removed, 2.576% extra energy.
  - Rhythm alarm plus rhythm forecast: 30.865 violations/hour, 83.25% removed, 2.383% extra energy.
  - Rhythm alarm alone: identical to the preceding rhythm result.
  - LightGBM forecast without the classifier: 34.434 violations/hour, 81.31% removed, 2.421% extra energy.

  The first result exactly reproduces [smoothing_summary.csv:4](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/smoothing_summary.csv:4), validating the audit calculation. The evidence supports forecast-armed smoothing, but not a material ML advantage.

- **[critical] The 82% recall headline is composition-weighted and misleading.** Stable Diffusion supplies 3,247 of 4,280 test events and has 96.8% recall. The other workloads have 42.2%, 69.9%, 0%, and 24.1% recall. See [drop_warning_by_workload.csv:2](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/drop_warning_by_workload.csv:2). Excluding Stable Diffusion, event-weighted recall is approximately 37.2%. Macro recall is only 46.6%, already acknowledged in [key_numbers.json:16](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/key_numbers.json:16). “We can warn about drops” is not supported as a workload-general claim.

- **[critical] The effective sample size is tiny and heavily pseudoreplicated.** The 803,803 test rows reduce to 9 independent training jobs, exactly one test job per workload and node-count stratum, plus the trailing portions of only 3 continuous inference sessions. Up to four nearly lockstep nodes from each training job are scored separately. See the splitting logic in [src/load.py:192](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/load.py:192), node cap in [src/load.py:208](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/load.py:208), and an explicit four-node duplicate test job in [traces_meta.csv:18](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/data/processed/traces_meta.csv:18). Deduplicating training events by taking one node per job reduces 4,280 events to approximately 2,736. One 6.84-hour Stable Diffusion job alone contributes 1,205 of those deduplicated events.

- **[critical] “ML beats simple rules” is not established against sufficiently strong rules.** The baseline set is persistence, a five-second mean, and one fixed autocorrelation implementation. See [src/baselines.py:18](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/baselines.py:18). The rhythm window, allowed periods, and strength threshold are not validation-tuned. LightGBM receives the rhythm forecasts and rhythm-fall score as input features, so it effectively learns corrections to the baseline. See [src/features.py:145](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/features.py:145). No tuned seasonal rule, autoregression, linear residual model, phase template, nearest-cycle method, or schedule-aware heuristic is evaluated. For forecasting, whether a tuned rule matches LightGBM remains unknown. For smoothing, the current rhythm rule already nearly matches it.

- **[major] The event “onset” is not a physical onset.** `detect_drops` declares a candidate at time \(t\) by examining the minimum over \(t+1\) through \(t+1\) second, then calls the first such candidate an onset. See [src/events.py:27](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/events.py:27) and [src/events.py:36](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/events.py:36). For an abrupt step at time \(\tau\), the reported onset is commonly near \(\tau-1\) second. For a gradual fall it may occur during the fall. Consequently, “one second before the drop starts” and the 4.9-second mean lead do not have a clean physical interpretation. This is not feature leakage, but it is a label-semantics error.

- **[major] No uncertainty analysis is provided.** MAE, recall, false-alarm rate, and energy savings are all point estimates computed over correlated samples. See [src/evaluate.py:31](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/evaluate.py:31). There are no clustered confidence intervals, paired job-level tests, bootstrap distributions, threshold stability analyses, or multiple seeds. The apparent numerical precision in the annual-dollar figures is therefore unjustified.

- **[major] The warning operating point is optimized for the dominant event mix.** A single global threshold targets 85% micro event recall on validation. See [src/evaluate.py:128](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/evaluate.py:128). That yields zero alarms and zero recall for fixed-rate online inference, while offline inference suffers 15.2 false alarms per hour. The chosen operating point is not workload-robust.

- **[major] Inference evaluation is not an independent deployment test.** Each inference workload is one continuous benchmark session divided into hourly blocks. See [src/load.py:157](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/load.py:157). Train, validation, and test therefore share hardware, harness logic, request-generation patterns, and likely experiment ordering. The drops are mostly gaps between benchmark runs, not serving-system events. See [data/README_data.md:97](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/data/README_data.md:97).

- **[major] Leave-one-workload-out results contradict broad generalization.** LightGBM beats rhythm on only one of five held-out workload types and is catastrophically worse on unseen training workloads. See [generalization_lowo.csv:2](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/generalization_lowo.csv:2). For example, unseen LoRA is 380.5 W versus 71.2 W. The model predicts familiar trace families, not arbitrary AI workloads.

- **[major] The control and energy models are too idealized for an energy-systems claim.** Battery discharge and GPU filler work are treated interchangeably even though one shifts energy and the other consumes it. There is no power limit, energy capacity, state of charge, efficiency, recharge, standby draw, rebound, or degradation. All value is controlled by assumed latency, six-second arming duration, and a 10%/s limit. See [src/simulate.py:44](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/simulate.py:44). The always-on limiter gives zero violations for only 2.94% energy, versus 2.58% for predictive but with residual violations. See [smoothing_summary.csv:4](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/smoothing_summary.csv:4).

- **[major] “Compute deferred” is not actually simulated.** It is calculated as curtailed energy divided by baseline energy. See [src/simulate.py:165](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/simulate.py:165). There is no throughput model, work queue, execution extension, or later energy recovery. The claim that pre-ramping delays 3% of compute is unsupported.

- **[major] The 100 MW dollar figures are scenario arithmetic, not validated estimates.** The synchronized case scales each single-node trace to an entire 100 MW site, extrapolating synchrony observed on at most 16 nodes to roughly 35,000 nodes. The random-offset case samples 400 test traces uniformly for only two simulated hours and scales them to rated capacity. See [src/simulate.py:244](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/simulate.py:244). Workload mix, job sizes, PUE, non-GPU loads, scheduler behavior, and correlation structure are unspecified. The $3.8M versus $1.4M figures in [site_scaleup.csv:3](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/site_scaleup.csv:3) should be labeled illustrative scenario outputs.

- **[major] Five-hertz averaging weakens the ramp conclusions.** Inference is averaged from 10 Hz to 5 Hz, and training is already only 5 Hz. See [src/load.py:97](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/load.py:97). Sub-200 ms transitions are smeared, peak ramp rates are underestimated, and the simulator cannot represent fast inverter, PSU, or grid-interface dynamics. A one-second ramp metric does not repair this missing bandwidth.

- **[minor] The synchronization statement overstates the implemented statistic.** The code reports the fraction of reference-node/other-node pairs with a nearest event within five seconds. See [src/explore.py:122](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/explore.py:122). The prose interprets it as the fraction of reference events for which every other node dropped. Those are different quantities.

- **[minor] Several secondary metrics invite overinterpretation.** AP and sample precision treat overlapping 0.2-second labels as separate observations. Mean lead is conditional only on caught events and selects the first alarm in the five-second window. See [src/evaluate.py:93](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/evaluate.py:93). Also, the simulator calls `min(1s forecast, 5s forecast)` the “lowest forecast over the next 5 s,” although intermediate horizons are not predicted. See [src/simulate.py:172](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/simulate.py:172).

## Questions for authors

1. What physical instant is the event time intended to represent: first visible decline, threshold crossing, or a one-second-ahead decision anchor?
2. Why was the validated rhythm alarm not connected to the predictive limiter?
3. What cost is assigned to arming, and why should 120 false alarms/hour matter when false arming is free in the simulator?
4. What actuator is intended: filler kernels, GPU power caps, UPS battery, rack battery, or facility storage? These require different dynamics and energy accounting.
5. How do conclusions change when metrics are macro-averaged by job and workload, with lockstep nodes deduplicated?
6. How stable are the results across different job splits, event thresholds, autocorrelation parameters, and sampling rates?
7. What deployment distribution justifies uniformly replaying these five workload types or assuming an entire 100 MW facility is synchronized?
8. Are benchmark run boundaries or request metadata available? If so, how much warning comes from predictable harness cadence rather than intrinsic workload behavior?

## Predicted decisions

| Venue | Decision | Rationale |
|---|---|---|
| Top systems or ML venue | **Strong reject** | Limited methodological novelty, 12 quasi-independent test units, no uncertainty, no cross-workload generalization, weak baselines, and a simulated systems contribution that collapses under the omitted rhythm controller. |
| e-Energy or SmartGridComm | **Reject** | Strong topic fit and useful public data, but the energy/control result lacks a physical actuator model, realistic facility aggregation, statistical uncertainty, and the most important controller baseline. |
| Workshop | **Borderline** | The artifact, candid limitations, and negative generalization result are useful. It becomes weak-accept quality if the ML smoothing claim is corrected and the rhythm-controller result is included. |

## Required additions

Ranked by impact per effort:

1. **Add the missing control baselines and ablations. Low effort, decisive impact.** Evaluate rhythm alarm plus limiter, rhythm forecast plus limiter, classifier-only, forecast-only, tuned threshold rules, always-armed with standby cost, and an oracle. Report violation-energy Pareto curves. The current headline must be revised if the audited rhythm result persists.

2. **Report independent-unit statistics. Low effort, high impact.** Treat each training job and each continuous inference session as the clustering unit. Deduplicate synchronized nodes. Provide job-level paired errors, macro workload metrics, clustered bootstrap confidence intervals, and split-seed sensitivity.

3. **Fix the event definition and re-run lead-time evaluation. Low to medium effort, high impact.** Define physical onset using a causal change point or first sustained negative ramp. Separately define the future drop criterion. Report recall versus required lead time, lead distributions including misses, and results at 20%, 30%, and 40% drop thresholds.

4. **Tune strong simple baselines on validation. Medium effort, high impact.** Include workload-agnostic autoregression, linear residual correction on the rhythm forecast, online phase templates, nearest-cycle matching, change-point rules, and workload-specific seasonal-naive models. Give every baseline the same history and validation budget as LightGBM.

5. **Replace the ideal limiter with a physical actuator model. Medium to high effort, essential for an energy venue.** Use measured or sourced latency, standby power, maximum response power, energy capacity, efficiency, recharge, rebound, and power-cap throughput curves. Separate GPU filler, capping, and battery cases.

6. **Make aggregation credible. Medium effort, high impact.** Construct site traces from jobs as correlated node groups, not independently sampled node traces. Sweep job-size distributions and synchronization fractions. Include CPU, network, cooling, and PUE sensitivity. Run multiple random site realizations with intervals.



## Verification by Claude (2026-10-12)
Rhythm-armed controller reproduced independently: ML 83.81% cut / 2.576% energy, rhythm 83.25% / 2.383%. CONFIRMED.
