I found no arithmetic or transcription errors in the current snapshot: all 208 placeholder occurrences expand exactly from `numbers.json`, `main.tex` matches that expansion, and the PDF is current. The reported significance statements agree with the displayed CIs. The sensor and licence statements also match the [NVML documentation](https://docs.nvidia.com/deploy/nvml-api/latest/api/group__nvmlDeviceQueries.html), [NLR licence](https://data.nlr.gov/node/312/license), and [MIT Supercloud licence](https://registry.opendata.aws/dcc/).

## Blocking

- **Lines 18, 30–35, 65–68, 208–210, 453–458, 487–493: the central “target matters” claim is not identified by the experiment.** The big-drop and aligned classifiers differ in minimum leaf size (100 versus 200), round cap (2000 versus 3000), early-stopping metric (AP versus default binary loss), early-stopping rows (all validation units sampled at 1 Hz versus a separate validation-unit half at 5 Hz), and deterministic settings. Calling this “retargeting” or concluding that the prediction target caused the AP increase is unsupported.

  The preferred fix is a matched ablation using identical rows, hyperparameters, stopping metric, and validation roles. Without that rerun, use these exact replacements:

  Lines 18:

  ```tex
  \title{Control-Aligned Prediction for Smoothing AI Training Power Swings}
  ```

  Lines 30–35:

  ```tex
  We compare two LightGBM pipelines. A classifier trained to warn of generic large drops obtains average
  precision (AP) <<nlr_ap_old>> when evaluated on the controller's event. A separately configured classifier
  trained directly on that control-aligned event obtains AP <<nlr_ap_ml>>, against <<nlr_ap_rh>> for a
  no-learning rhythm-replay baseline. The two learned pipelines share their features and training rows but
  differ in regularization and early-stopping configuration, so this comparison does not isolate the effect
  of the label.
  ```

  Lines 65–68:

  ```tex
  \item \textbf{A control-aligned prediction pipeline.} Instead of a generic ``large drop'', its label is the
  event the controller acts on: a ramp-limit exceedance whose whole 1~s ramp window lies inside the window
  during which a limiter triggered now would be armed. The control-aligned and big-drop LightGBM pipelines
  obtain AP <<nlr_ap_ml>> and <<nlr_ap_old>>, respectively, on held-out NLR data; this is not a label-only
  ablation (Section~\ref{sec:res-target}).
  ```

  Lines 208–210:

  ```tex
  On NLR test rows rhythm replay ranks the control-aligned event with AP <<nlr_ap_rh>>. The previously
  trained big-drop LightGBM pipeline obtains <<nlr_ap_old>> when scored on that event, while the separately
  configured control-aligned LightGBM pipeline obtains <<nlr_ap_ml>>. Because their training configurations
  differ, the contrast is a pipeline comparison rather than an estimate of the label's causal effect.
  ```

  Lines 453–458:

  ```tex
  \textbf{Why alignment may help.} The big-drop label describes one kind of event (large falls) at one
  horizon (the next 5~s), whereas the limiter needs a fall steep enough to cross the study threshold inside
  the window defined by its latency and hold time. Many exceedances, including steps of the LoRA square
  wave, do not qualify as big drops. The two LightGBM pipelines use the same features and training rows, but
  their leaf-size, boosting-round cap, early-stopping metric and early-stopping validation rows differ.
  Consequently, the present comparison does not isolate the effect of changing the label.
  ```

  Lines 487–493:

  ```tex
  For fill-type smoothing of AI power swings, a control-aligned predictor is a promising alternative to a
  generic drop warning. On NLR test curves, the control-aligned LightGBM pipeline reaches a given removal
  level with less engaged time than rhythm replay retrospectively, with thresholds read off the test curve
  (Table~\ref{tab:arm}). It also ranks the aligned event above rhythm replay on NLR and labelled V100 cluster
  jobs when the site is represented in model fitting. Its improvement over the separately configured
  big-drop pipeline cannot, however, be attributed solely to the target without a matched ablation.
  Improving transfer and closing the gap to the perfect-foresight reference remain open problems.
  ```

- **Lines 167–168: the big-drop definition omits two implemented conditions.** `events.py` requires a trailing peak of at least 1 kW and consolidates candidate onsets within a 5 s refractory interval. Both affect the comparator and reproducibility.

  Replace with:

  ```tex
  The \textbf{big-drop} detector marks a candidate onset when power falls by more than 30\% of the trailing
  10~s peak within the following 1~s, provided that peak is at least 1~kW. Candidate onsets separated by at
  most 5~s are consolidated to the first onset. Row $t$ is positive when a retained onset lies in
  $(t,t+5\,\mathrm{s}]$.
  ```

- **Lines 413–427: “unseen site” overstates zero-shot deployment.** AP is legitimately threshold-free and zero-shot, but every leave-one-dataset-out readiness threshold is selected using the target site’s own labelled threshold-validation split. “Rhythm replay needs no site data at all” is therefore false for the reported operating point. The five adaptation draws are random draws, not statistically independent experiments.

  Replace the whole passage with:

  ```tex
  When the test dataset is excluded from model fitting, no dataset has a 95\% interval excluding zero in
  favour of the learned trigger. With ordinary features the interval favours rhythm replay on NLR and
  Supercloud (Table~\ref{tab:cross}); shape-only features make NLR inconclusive but remain worse on
  Supercloud. Continuing to boost on 5, 15 or 60 minutes of local training-split data does not consistently
  recover the in-domain AP advantage (mean and range over five random draws; a draw containing only one
  class leaves the base model unchanged). Thus these experiments do not demonstrate a reliable AP
  advantage without site-represented model fitting.

  The readiness comparison is not fully zero-shot: thresholds for both learned and rhythm scores are
  selected on the held-out site's own threshold-validation split. Here ``unseen'' therefore refers to model
  fitting, not threshold calibration. With ordinary features, the learned trigger on NLR removes
  <<rd_lodo_nlr_learned_90_cut>>\% of violations at <<rd_lodo_nlr_learned_90_armed>>\% engaged time,
  against <<rd_lodo_nlr_rhythm_90_cut>>\% at <<rd_lodo_nlr_rhythm_90_armed>>\% for rhythm replay. We have
  no interval for this operating-point comparison and do not claim transfer from it.
  ```

## Should fix

- **Lines 26–28, 48–50, 114–117, 133–135: the paper treats an illustrative per-node threshold as an actual grid limit.** No site interconnection requirement or facility load is measured, and 10% of GPU rating per second is an assumed scenario.

  Replace lines 26–28 with:

  ```tex
  Large AI training jobs can move GPU power by tens of percent within a second, and synchronized jobs can
  create fast aggregate load ramps. We study an illustrative per-node down-ramp threshold of 10\% of rated
  GPU power in 1~s; exceedance of this study threshold is not evidence that a site violated an actual
  interconnection requirement.
  ```

  Replace lines 48–50 with:

  ```tex
  Training a large neural network alternates compute-heavy and communication-heavy phases, so GPU power
  moves in fast, large steps. Nodes participating in a synchronized data-parallel job can step together,
  causing their GPU-power changes to add rather than cancel.
  ```

  Replace lines 114–117 with:

  ```tex
  \textbf{Common preprocessing.} All traces are averaged onto a 0.2~s grid (row $t$ averages
  $[t,t+0.2\,\mathrm{s})$) and expressed as ``NLR-equivalent watts'': node GPU power times 2.8~kW divided
  by the node's rated GPU power. We use 2.8~kW for four H100s, 5.6~kW for eight H100s, 8.0~kW for eight
  B200s, and 250~W per recorded Supercloud V100 stream. The last value assumes the PCIe V100 rating and
  should be tied to the cluster hardware documentation. We define an illustrative down-ramp threshold of
  10\% of rated GPU power per second; it is not asserted to be a universal grid or interconnection limit.
  ```

  The V100 rating needs a source because NVIDIA specifies 250 W for PCIe and 300 W for SXM2 in its [V100 datasheet](https://images.nvidia.com/content/technologies/volta/pdf/tesla-volta-v100-datasheet-letter-fnl-web.pdf). If the exact installed limit cannot be established, report a 250/300 W sensitivity.

  Replace the figure caption at lines 133–135 with:

  ```tex
  \caption{Sixty seconds of one NLR Llama2-70B LoRA test node. Red dots mark exceedances of the illustrative
  study threshold (1~s fall larger than 10\% of rated node GPU power). Many are steps of a regular square
  wave rather than ``big drops''.}
  ```

- **Lines 27–28, 57–59, 157–159, 275–281, 472–474: storage charging is incorrectly treated as energy overhead.** The simulator adds grid-side load. For storage, that means charging; the integral is stored energy, not net energy consumption, because later discharge and losses are absent.

  Replace lines 57–59 with:

  ```tex
  This paper studies one specific decision: \emph{when to engage} a fill-type actuator. Filler GPU work
  consumes additional power, while the storage interpretation represents charging to add grid-side load
  during a fall. Later storage discharge is outside the model. The actuator must be ready before the fall:
  kernels must be launched or a power converter must be ready.
  ```

  Replace lines 157–159 with:

  ```tex
  We count as \emph{engaged} every row where the limiter is armed or still filling. Performance is the
  share of raw exceedances removed against the share of time engaged. The reported energy metric is fill
  energy plus a standby draw of 0--10\% of rated power while engaged, divided by baseline GPU energy.
  For filler compute this is additional consumption; for storage it is absorbed charge before any later
  discharge or round-trip loss. Reported operating-point tables set start-up energy to zero.
  ```

  In Table 4, replace `Overhead` with:

  ```tex
  Energy metric
  ```

  Replace the simulation limitation at lines 472–474 with:

  ```tex
  \emph{Simulation.} The actuator is an idealized one-sided limiter with fixed latency, hold time and
  standby draw. Actuator power limits, storage capacity, state of charge, subsequent discharge,
  round-trip efficiency, wear and measured dynamics are not modelled. The storage results therefore
  describe required charging energy, not net storage loss.
  ```

- **Lines 39, 72, 92, 110–112, 347, 475–477, 491–492: “real user jobs, not benchmarks” is unsupported.** The [dataset README](https://github.com/MIT-AI-Accelerator/MIT-Supercloud-Dataset/blob/main/README.md?plain=1) describes scheduler-observed labelled jobs, but also says they use open-source implementations and public datasets, including TensorFlow’s benchmark suite. It does not establish production use.

  Replace lines 110–112 with:

  ```tex
  \textbf{MIT Supercloud}~\cite{supercloud}: we use a stratified subset of 560 labelled jobs, 80 per model
  class (VGG, ResNet, Inception, U-Net, BERT, DistilBERT, GNN). The data are scheduler-observed jobs from a
  production HPC cluster, but the release identifies open-source model implementations and public
  datasets; it does not establish that every run was a production workload rather than a benchmark or
  experiment. Nodes contain two V100s; 1--2 GPU streams are present in the selected trace files.
  ```

  Globally replace:

  ```tex
  benchmarks and real user jobs
  ```

  with:

  ```tex
  scripted benchmark sessions and labelled cluster jobs
  ```

  and replace:

  ```tex
  real Supercloud jobs
  ```

  with:

  ```tex
  labelled Supercloud cluster jobs
  ```

- **Lines 39–42, 344–350, 381–383: “significantly” suggests formal hypothesis testing and ignores multiplicity.** The numerical claim is correct—the intervals exclude zero on NLR and Supercloud—but the exact inferential statement should name the interval.

  Replace lines 39–42 with:

  ```tex
  Across three public datasets (H100, B200 and V100 nodes; scripted benchmark sessions and labelled cluster
  jobs), the 95\% paired cluster-bootstrap interval for learned-minus-rhythm AP excludes zero on NLR and
  Supercloud when the site is represented in model fitting; it includes zero on Elsayed. When a site is
  excluded from fitting, no dataset shows an interval excluding zero in favour of learning, and five
  one-hour adaptation draws do not consistently recover the in-domain advantage.
  ```

  Replace lines 344–350 with:

  ```tex
  Table~\ref{tab:cross} and Fig.~\ref{fig:forest} compare AP for in-domain, pooled and leave-one-dataset-out
  fitting. For both in-domain and pooled fitting, the learned-minus-rhythm 95\% interval lies above zero on
  NLR and Supercloud. On Supercloud, exploratory, unadjusted per-class intervals lie above zero for
  <<sc_classes_sig>> of <<sc_classes>> model classes. On Elsayed the interval includes zero with only six
  test sessions; rhythm replay has the larger point estimate on its two diffusion test sessions, but two
  sessions do not support a firm workload-level conclusion.
  ```

  Replace the forest caption with:

  ```tex
  \caption{AP difference, learned control-aligned trigger minus rhythm replay, with 95\% cluster-bootstrap
  intervals. Red: interval entirely above zero; blue: entirely below zero; grey: includes zero. These
  intervals are not multiplicity-adjusted. The unseen-site rows use shape-only features.}
  ```

- **Lines 180–191, 195–201: important reproducibility details are missing.** Add the ACF search bounds, complete LightGBM parameters, different stopping metrics, shape denominator, and cross-dataset weights.

  Replace lines 180–191 with:

  ```tex
  \textbf{Rhythm replay} estimates the period $P$ from a trailing 120~s autocorrelation, recomputed every
  second. It searches 2--40~s lags, requires peak correlation at least 0.3, and selects the first local peak
  within 90\% of the strongest peak. It predicts
  $\hat p_{t+k}=p_{t+k-P\lceil k/P\rceil}$ and scores row $t$ by the largest predicted 1~s down-ramp inside
  the target window, divided by rated node power. Rows without an accepted period receive score zero.

  The \textbf{learned} predictor is LightGBM~\cite{lightgbm} on 56 causal trailing features. Its aligned
  model uses learning rate 0.05, 63 leaves, at least 200 rows per leaf, 0.8 feature and row subsampling
  (bagging every round), $\ell_2$ penalty 1, at most 3000 rounds, square-root class weighting, seed 42 and
  100-round early stopping on binary loss using the early-stopping validation half. The big-drop model uses
  the same features and training rows but at least 100 rows per leaf, at most 2000 rounds, and AP-based
  early stopping on a 1~Hz sample of all validation units. The \textbf{shape-only} variant divides each
  level-valued feature by one watt plus the trailing 60~s maximum, leaving timing and dimensionless
  features unchanged.
  ```

  Add after line 201:

  ```tex
  For pooled and leave-one-dataset-out fitting, each training dataset receives equal total sample weight;
  early-stopping validation rows are unweighted.
  ```

- **Lines 270–271 and 335–337: the implemented “oracle” is not proven to bound all possible triggers.** It is a particular iterative perfect-foresight heuristic, not an optimization for minimum engagement.

  Replace lines 270–271 with:

  ```tex
  The perfect-foresight reference removes all violations at <<oracle_armed>>\% engaged time. It is an
  iterative just-in-time trigger heuristic, not a proven minimum-engagement bound.
  ```

  Replace the readiness-figure caption with:

  ```tex
  \caption{Violations removed versus engaged time on NLR test traces (1~s latency, about 200 thresholds from
  validation-score quantiles). Always-on removes everything but is always engaged; the star is the
  iterative perfect-foresight reference and is not claimed to be an optimal lower bound.}
  ```

- **Lines 387–391: the operating-point interpretation hides a removal-versus-engagement trade-off.** On NLR and Supercloud, learning engages much less but also removes roughly 12 percentage points fewer violations than rhythm replay.

  Replace with:

  ```tex
  AP is a ranking measure, not a smoothing result. Table~\ref{tab:xready} reports validation-chosen
  operating points for a 90\% removal target on each dataset (one decision per second, no confidence
  intervals). On NLR and Supercloud, learning uses much less engaged time but also removes fewer test
  violations than rhythm replay; on Elsayed it removes more while engaging slightly longer. These
  operating-point comparisons are descriptive because no intervals are available.
  ```

- **Lines 468–471: the estimand gives longer and multi-node jobs more weight.** Bootstrap clustering accounts for dependence but does not make point estimates job-weighted. Supercloud has 973 node traces from 560 jobs, up to four selected node traces per job.

  Replace with:

  ```tex
  \emph{Uncertainty and weighting.} Intervals are conditional on one fitted model and split and omit
  training and split variability; NLR has 12 test clusters and Elsayed six. AP and smoothing summaries pool
  rows or events, so longer traces and multi-node jobs receive more point-estimate weight. NLR retains up to
  four nodes per training job, and the Supercloud subset contains 973 node traces from 560 jobs, with up to
  four selected nodes per job. Bootstrap resampling is by job (or whole inference session), which handles
  within-job dependence but does not change this row-weighted estimand. The NLR inference validation halves
  are time blocks from the same sessions and are not independent.
  ```

## Nits

- **Lines 32 and 67–68: “held-out H100 traces” sounds more independent than the NLR inference evaluation is.** Training jobs are independently held out, but inference test rows are later blocks from sessions also represented in training.

  Replace both occurrences of:

  ```tex
  held-out H100 traces
  ```

  with:

  ```tex
  held-out NLR training jobs and later test blocks of the three inference sessions
  ```

- **Lines 190–191: “divides by the trailing maximum” is not mathematically exact.** The implementation adds one watt to the denominator.

  If the fuller predictor replacement above is not adopted, replace with:

  ```tex
  A \textbf{shape-only} variant, used for transfer, divides every level-valued feature by one watt plus the
  trailing 60~s maximum.
  ```

NOT READY
