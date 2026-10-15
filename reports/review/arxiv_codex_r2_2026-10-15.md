The ablation and generated results are reproducible, but the paper is not quite ready: four factual errors and one overclaimed “label-only” statement remain.

## Resolved

- The matched ablation uses the same 550,364 training rows, 56 features, 587,790 early-stopping rows, LightGBM settings, binary-log-loss stopping metric, 100-round patience, and seed 42 as `aligned.py`.
- My independent in-memory rerun reproduced every stored result exactly: aligned AP 0.9584076, big-drop AP 0.5834481, difference 0.3749595, CI [0.2769740, 0.4931320], and best iterations 1172/1016.
- The bootstrap is correct: paired row scores, 1,000 seeded resamples, with nine held-out training jobs plus three whole inference sessions as the 12 clusters.
- All 383 generated values recompute exactly from the current JSON/CSV tables. All 217 placeholders expand correctly, and `main.tex` is an exact expansion of `template.tex`.
- Resolved round-1 items: big-drop definition; unseen-site threshold calibration; equal dataset weighting; per-workload interval caveat; significance definition and multiplicity caveat; LightGBM/rhythm reproducibility details; scoring frequency; oracle wording; cross-dataset removal/engagement trade-off; storage-model limitations; limiter safety factor; 60-second figure duration; always-burn definition; and NLR 49/12 unit counts.
- “Perfect preview” is supported: the cited controller receives the generated future disturbance directly and does not model forecast errors. [ArXiv paper](https://arxiv.org/html/2606.04869)

The `1.00` workload AP remains honest two-decimal rounding of 0.99695; it is only a presentation nit.

## Still open

- [template.tex:96](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/arxiv/template.tex:96) still says “real user jobs.”

  Replace the row with:

  ```tex
  MIT Supercloud~\cite{supercloud} & 1--2$\times$V100 & 7 model classes, labelled cluster jobs & nvidia-smi 10 Hz & <<supercloud_node_h>> & <<supercloud_units>> (<<supercloud_test_units>>) \\
  ```

- [template.tex:295](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/arxiv/template.tex:295) and [template.tex:305](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/arxiv/template.tex:305) still call absorbed storage charge “overhead.”

  Replace with:

  ```tex
  which is the always-on solution. With a 2\% standby draw the reported energy metrics are
  <<t90_sb2_ml_aligned_ovh>>\% and <<t90_sb2_rhythm_aligned_ovh>>\% (always-on: <<t90_sb2_always_on_ovh>>\%).
  ```

  ```tex
  \caption{Validation-chosen operating points scored on NLR test traces (1~s latency). Removal and engaged
  time in \%; reported energy metric in \% of baseline job energy with a 2\% standby draw.}
  ```

  ```tex
  Target & Trigger & Removed & Engaged & Energy metric \\
  ```

- [template.tex:450](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/arxiv/template.tex:450) still calls overlapping random samples “independent draws,” and its one-class condition is incomplete.

  Replace lines 449–452 with:

  ```tex
  inconclusive difference but remain significantly worse on Supercloud. Continuing to boost the unseen-site
  model on 5, 15 or 60 minutes of the new site's training data (mean and range over five random draws)
  does not reliably recover the in-domain advantage. A draw is left unadapted if either its local fitting
  subset or its early-stopping tail contains only one class.
  ```

- The round-1 threshold/synchrony wording has two remnants. Replace [template.tex:51](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/arxiv/template.tex:51)–53 with:

  ```tex
  Training a large neural network alternates compute-heavy and communication-heavy phases, so GPU power
  moves in fast, large steps. Nodes participating in a synchronized data-parallel job can step together,
  causing their GPU-power changes to add rather than cancel.
  ```

  Replace [template.tex:140](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/arxiv/template.tex:140)–142 with:

  ```tex
  \caption{Sixty seconds of one NLR Llama2-70B LoRA test node. Red dots mark exceedances of the illustrative
  study threshold (1~s fall larger than 10\% of rated node power). Many are steps of a regular square wave
  rather than ``big drops''.}
  ```

## New problems

- The ablation does not literally hold every numerical hyperparameter fixed. Both models use the same square-root class-weighting rule, but `scale_pos_weight` is 1.7534 for the aligned label and 2.5728 for the big-drop label because their prevalences differ. Therefore “changes only the label,” “same hyperparameters,” and “only the label differs” are too strong.

  In [template.tex:32](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/arxiv/template.tex:32) and line 70, replace `a matched ablation that changes only the label` with:

  ```tex
  a matched-pipeline ablation
  ```

  Replace [template.tex:229](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/arxiv/template.tex:229)–231 with:

  ```tex
  \textbf{Matched target ablation.} We train the big-drop label with the same training rows, features,
  fixed LightGBM settings, early-stopping half, stopping metric and square-root class-weighting rule as
  the aligned model. Because that rule depends on label prevalence, its numerical class weight changes
  with the label.
  ```

  Replace [template.tex:489](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/arxiv/template.tex:489)–491 with:

  ```tex
  of the LoRA square wave, are not positive examples for the big-drop model. In the matched ablation all
  fixed pipeline choices and the class-weighting rule are held constant; the target labels and their
  prevalence-derived class weight change together. The result therefore supports the choice of training
  target, but is not a fixed-weight label-only substitution (Section~\ref{sec:res-target}).
  ```

- [template.tex:133](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/arxiv/template.tex:133) says 91%; the raw table gives 89.2915%.

  ```tex
  89\% of Supercloud test seconds would be labelled ``violation imminent''. We apply a 1~s trailing mean to
  ```

- [template.tex:116](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/arxiv/template.tex:116) confuses trace segments with nodes. The data contain at most four retained nodes per job; one node was split, producing five trace segments for that job.

  ```tex
  class (VGG, ResNet, Inception, U-Net, BERT, DistilBERT, GNN), on two-V100 nodes (one or two GPU streams
  per trace; up to four retained nodes per job, yielding 973 trace segments).
  ```

  Correspondingly, replace [template.tex:502](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/arxiv/template.tex:502)–505 with:

  ```tex
  training or split variability; NLR has 12 test clusters and Elsayed six. Up to four near-synchronous
  nodes per NLR job, and up to four retained nodes per Supercloud job, are weighted equally. Metrics pool
  rows, so longer and larger jobs weigh more in point estimates; the bootstrap resamples whole jobs (or
  whole NLR inference sessions) but does not change this weighting.
  ```

- [template.tex:126](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/arxiv/template.tex:126) says the inference validation blocks alternate. They are assigned after a seeded shuffle and do not always alternate chronologically.

  ```tex
  one for choosing operating points. For NLR inference, one-hour validation blocks are assigned between
  these halves after a seeded shuffle; they come from the same sessions and are not independent.
  ```

**VERDICT: READY AFTER FIXES**
