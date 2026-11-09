Reading additional input from stdin...
OpenAI Codex v0.164.0
--------
workdir: /Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing
model: gpt-5.6-sol
provider: openai
approval: never
sandbox: read-only
reasoning effort: low
reasoning summaries: none
session id: 01a1c29d-8df1-7102-8136-80fa68fa5672
--------
user
Focused re-review, round 2. Your round-1 review is reports/review/pesgm_codex_r1_2026-11-09.md (final section from '# Verdict: READY AFTER FIXES' near the end). The author applied findings 1-5, 7 (caption only, kept single-column figure) and 8 (text paragraph), and moved the AI-use text into an Acknowledgment section per IEEE policy. Finding 6 (affiliation) is pending the author's decision. The diff is in paper/template.tex (rendered: paper/main.tex, paper/main.pdf). Check: each fix applied correctly, no new overclaims or inconsistencies, numbers unchanged, PDF still 4 pages and builds. Output: verdict READY / READY AFTER FIXES / NOT READY, then only remaining issues with exact replacement text. Do not edit files. No em dashes.
hook: SessionStart
hook: SessionStart Completed
codex
I’ll compare the round-1 findings against the source and rendered artifacts, then run a read-only build/check if the project setup permits it. I’ll report only unresolved issues with paste-ready replacement text.
exec
/bin/zsh -lc "sed -n '/"'^# Verdict: READY AFTER FIXES/,$p'"' reports/review/pesgm_codex_r1_2026-11-09.md && git diff -- paper/template.tex paper/main.tex && rg -n \"Acknowledg|AI|affiliat|Fig\\.|Figure|%|MW|MWh|baseline|improv|outperform|state-of-the-art\" paper/template.tex paper/main.tex && pdfinfo paper/main.pdf | rg '"'^(Pages|Page size|CreationDate|ModDate)'"'" in /Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing
 succeeded in 0ms:
# Verdict: READY AFTER FIXES

The numerical audit passed. Every reported result in [paper/main.tex](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex) agrees, after stated rounding, with the arXiv paper and generating artifacts. This includes the matched ablation, AP tables, latency results, readiness operating points, bootstrap intervals, transfer results, dataset sizes, and always-burn and oracle values.

The PDF is four pages, letter size, has no overfull boxes or unresolved references, and therefore has one page available. The main remaining problems are evidence framing, two regressions from the reviewed arXiv wording, missing citations, and physical interpretation for a PES audience.

1. Abstract presents an idealized simulation as a general capability and implies the 10 percent ramp limit is an actual utility requirement.

   [paper/main.tex:24](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:24)

   “Utilities place on large loads” is not established by the cited evidence, and the paper studies an illustrative threshold rather than a documented interconnection requirement. “Storage removes these violations” is also too categorical for an idealized simulator without state of charge, efficiency, or power and energy limits.

   Replace lines 24 to 27 with:

   ```tex
   Large AI training jobs can swing GPU power by tens of percent within a second, and synchronized jobs can
   create fast load ramps of concern at large grid-connected facilities. In an idealized simulation,
   fill-type smoothing, using filler GPU work or storage, can reduce violations of an illustrative ramp
   threshold, but it must be engaged before the fall and keeping it engaged has a cost.
   Forecasting can decide when to engage it.
   ```

   Also replace [paper/main.tex:98](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:98):

   ```tex
   A violation starts when the node's 1~s down-ramp exceeds 10\% of rated power.
   ```

   with:

   ```tex
   For this study, a violation starts when the node's 1~s down-ramp exceeds an illustrative threshold of
   10\% of rated power per second; this is a normalized study threshold, not a specific utility requirement.
   ```

2. “Real user jobs” is stronger than the Supercloud evidence and reverses a correction already accepted in the arXiv review.

   The release contains scheduler-observed, labelled cluster jobs using public datasets and open-source models. It does not establish that these were production user workloads.

   Make these exact replacements:

   [paper/main.tex:37](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:37)

   ```tex
   Across three public datasets covering H100, B200 and V100 nodes and both benchmark and labelled cluster jobs,
   ```

   [paper/main.tex:66](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:66)

   ```tex
   \item A three-dataset study (H100, B200, V100; benchmarks and labelled cluster jobs) with job-clustered confidence
   ```

   [paper/main.tex:80](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:80)

   ```tex
   nvidia-smi at 10~Hz, 1,292 node-hours of labelled cluster jobs.
   ```

   [paper/main.tex:214](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:214)

   ```tex
   rhythm replay on NLR (pooled AP 0.96 vs 0.67) and on labelled Supercloud jobs
   ```

   [paper/main.tex:248](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:248)

   ```tex
   between benchmark runs, and each NLR inference workload is a single session. Supercloud adds
   scheduler-observed labelled jobs on older V100 nodes.
   ```

   [paper/main.tex:258](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:258)

   ```tex
   the same violation removal on H100 benchmark traces, and ranks violations better (higher AP) on labelled
   V100 cluster jobs, provided the site is represented in training.
   ```

3. The matched ablation establishes a ranking effect, but the readiness comparison uses a separately configured earlier big-drop model.

   The conference version omits the arXiv disclosure that the big-drop model in Table II is not the matched-ablation model. As written, readers can reasonably infer that the 64.3 percent result comes from the matched model. Therefore, the matched experiment supports attributing the AP difference to the target, but does not by itself isolate the target’s causal effect on the simulated engaged-time curve.

   Replace [paper/main.tex:119](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:119) through line 122 with:

   ```tex
   target window; it needs no training. The \emph{learned} predictor is LightGBM~\cite{lightgbm} on 56 trailing features
   (lags, differences, rolling statistics, time since recent steps and drops, rhythm period, phase and
   rhythm forecasts), one model per actuator latency. The matched label ablation uses identical fixed
   model settings for the two labels, apart from the prevalence-derived class weight. The big-drop model
   in the readiness comparison is an earlier configuration with different leaf-size and early-stopping
   choices, so that comparison does not isolate the label alone. A shape-only variant divides every level
   feature by the trailing 60~s maximum.
   ```

   Replace [paper/main.tex:173](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:173) through line 177 with:

   ```tex
   The earlier configured big-drop trigger needs more engaged time than the control-aligned trigger
   (64.3\% at 90\%; difference $-$15.9 points, CI $-$25.7 to $-$3.9). At 95\% removal the interval includes
   zero (CI $-$26.3 to 0.5). Because these two readiness models were not identically configured, the
   matched ablation provides the cleaner evidence for the target's effect: AP 0.58 versus 0.96 on the
   control-aligned event.
   ```

   Replace the opening of the conclusion at [paper/main.tex:255](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:255) with:

   ```tex
   In our NLR experiments, training on the controller's event, a ramp-limit violation inside the
   actuator's engagement window, ranked relevant events substantially better than training the same
   pipeline on a generic large-drop label.
   ```

4. “Energy overhead” is inappropriate for the storage interpretation and reverses another arXiv correction.

   The reported quantity combines fill energy and assumed standby draw. For storage it is charge absorbed before later discharge and losses, not necessarily net energy overhead.

   Replace [paper/main.tex:102](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:102) through line 104 with:

   ```tex
   still filling, and report violations removed against engaged time. We also report an energy metric
   consisting of fill energy plus an assumed standby draw of 0--5\% of rated power while engaged. For
   storage, this is absorbed charge before any later discharge or loss, which the simulation does not model.
   ```

   Replace [paper/main.tex:203](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:203) through line 207 with:

   ```tex
   With operating points chosen on validation and a standby draw of 2\% of rated power, a 90\% target
   gives 86.8\% removal at 45.6\% engaged time and a 3.7\% reported energy metric for the learned trigger;
   rhythm replay meets the target only by staying engaged 99.2\% of the time, with a 5.4\% energy metric,
   versus 5.4\% for always-on.
   ```

5. Two technical claims lack references: LightGBM and the architecture-dependent NVML averaging behavior.

   Replace [paper/main.tex:90](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:90) with:

   ```tex
   \textbf{Sensor harmonization.} NVML documents that on recent architectures the default power reading is
   averaged over about 1~s, while older GPUs such as the V100 report instantaneous power~\cite{nvml}.
   ```

   The LightGBM citation is included in Finding 3.

   Add before [paper/main.tex:277](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:277):

   ```tex
   \bibitem{lightgbm} G.~Ke, Q.~Meng, T.~Finley, et al., ``LightGBM: A highly efficient gradient boosting decision tree,'' in \emph{Advances in Neural Information Processing Systems}, vol.~30, 2017.
   \bibitem{nvml} NVIDIA, ``NVML API reference guide: Device queries,'' 2026. [Online]. Available: \url{https://docs.nvidia.com/deploy/nvml-api/latest/api/group__nvmlDeviceQueries.html}
   ```

   Change [paper/main.tex:267](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:267) from:

   ```tex
   \begin{thebibliography}{9}
   ```

   to:

   ```tex
   \begin{thebibliography}{99}
   ```

6. The author affiliation is unconventional and may be rejected by a submission-system or publication check.

   “Yeshiva University alumnus” is not a current institutional affiliation. Unless the university has explicitly authorized its use, list the current independent affiliation and location.

   Replace [paper/main.tex:17](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:17) through line 19 with:

   ```tex
   \author{\IEEEauthorblockN{Sayed Raheel}
   \IEEEauthorblockA{Independent Researcher, New York, NY, USA\\
   \texttt{shussai1@mail.yu.edu}}}
   ```

   Confirm that continued use of the university email is permitted and that the MIRA author record matches the PDF exactly.

7. The forest plot is too compressed for a conference column.

   The long dataset labels consume most of the plot width, leaving a very narrow numerical region. This is the weakest formatting element in the PDF.

   Replace [paper/main.tex:221](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:221) through line 227 with:

   ```tex
   \begin{figure*}[t]
   \centering
   \includegraphics[width=0.78\textwidth]{fig_forest.pdf}
   \caption{AP difference between the learned control-aligned trigger and rhythm replay, with 95\%
   cluster-bootstrap intervals. Red: learned significantly better; blue: rhythm significantly better;
   grey: inconclusive. Unseen-site rows use shape-only features.}
   \label{fig:forest}
   \end{figure*}
   ```

   Rebuild and ensure that the float does not separate the plot excessively from Section IV-C.

8. Use the fifth page to address the likely PES reviewer objection: the paper currently reads more like an ML benchmark than a power-systems study.

   The four-page version provides no actuator power rating, required energy capacity, facility-level aggregation example, or sensitivity to the assumed 10 percent threshold and six-second hold. A PES reviewer may reject quickly because AP and engaged time do not establish implementability by a BESS, supercapacitor, or facility control system.

   The best use of the fifth page is a compact “Power-system interpretation” subsection containing:

   - The illustrative status of the ramp limit.
   - Limiter peak power and energy requirements on representative traces.
   - A facility-scale conversion or clearly qualified scaling example.
   - Sensitivity to ramp threshold, hold time, and actuator latency.
   - A distinction between filler-compute consumption and storage charge/discharge.

   If no additional simulations can be completed, add after [paper/main.tex:252](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:252):

   ```tex
   \emph{Power-system interpretation.} The 10\%/s threshold and idealized fill-only limiter define a
   comparative forecasting experiment, not a complete storage design. Engaged time is a readiness metric,
   not an energy-capacity or converter-rating requirement. A deployable design must additionally size
   charge and discharge power, usable energy, state-of-charge margin and thermal headroom from the
   facility-level load trace. It must also account for efficiency, recovery after an event, simultaneous
   jobs and the applicable interconnection ramp requirement. The present results therefore show when a
   predictive controller would request readiness under the stated simulator, rather than demonstrating
   compliance by a particular storage installation.
   ```

The keywords are appropriate, the title is relevant to the PES GM large-dynamic-load theme, Tables I and II are readable, and the abstract, results, and conclusion become internally consistent once Findings 2 through 4 are applied.
tokens used
69,945
# Verdict: READY AFTER FIXES

The numerical audit passed. Every reported result in [paper/main.tex](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex) agrees, after stated rounding, with the arXiv paper and generating artifacts. This includes the matched ablation, AP tables, latency results, readiness operating points, bootstrap intervals, transfer results, dataset sizes, and always-burn and oracle values.

The PDF is four pages, letter size, has no overfull boxes or unresolved references, and therefore has one page available. The main remaining problems are evidence framing, two regressions from the reviewed arXiv wording, missing citations, and physical interpretation for a PES audience.

1. Abstract presents an idealized simulation as a general capability and implies the 10 percent ramp limit is an actual utility requirement.

   [paper/main.tex:24](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:24)

   “Utilities place on large loads” is not established by the cited evidence, and the paper studies an illustrative threshold rather than a documented interconnection requirement. “Storage removes these violations” is also too categorical for an idealized simulator without state of charge, efficiency, or power and energy limits.

   Replace lines 24 to 27 with:

   ```tex
   Large AI training jobs can swing GPU power by tens of percent within a second, and synchronized jobs can
   create fast load ramps of concern at large grid-connected facilities. In an idealized simulation,
   fill-type smoothing, using filler GPU work or storage, can reduce violations of an illustrative ramp
   threshold, but it must be engaged before the fall and keeping it engaged has a cost.
   Forecasting can decide when to engage it.
   ```

   Also replace [paper/main.tex:98](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:98):

   ```tex
   A violation starts when the node's 1~s down-ramp exceeds 10\% of rated power.
   ```

   with:

   ```tex
   For this study, a violation starts when the node's 1~s down-ramp exceeds an illustrative threshold of
   10\% of rated power per second; this is a normalized study threshold, not a specific utility requirement.
   ```

2. “Real user jobs” is stronger than the Supercloud evidence and reverses a correction already accepted in the arXiv review.

   The release contains scheduler-observed, labelled cluster jobs using public datasets and open-source models. It does not establish that these were production user workloads.

   Make these exact replacements:

   [paper/main.tex:37](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:37)

   ```tex
   Across three public datasets covering H100, B200 and V100 nodes and both benchmark and labelled cluster jobs,
   ```

   [paper/main.tex:66](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:66)

   ```tex
   \item A three-dataset study (H100, B200, V100; benchmarks and labelled cluster jobs) with job-clustered confidence
   ```

   [paper/main.tex:80](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:80)

   ```tex
   nvidia-smi at 10~Hz, 1,292 node-hours of labelled cluster jobs.
   ```

   [paper/main.tex:214](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:214)

   ```tex
   rhythm replay on NLR (pooled AP 0.96 vs 0.67) and on labelled Supercloud jobs
   ```

   [paper/main.tex:248](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:248)

   ```tex
   between benchmark runs, and each NLR inference workload is a single session. Supercloud adds
   scheduler-observed labelled jobs on older V100 nodes.
   ```

   [paper/main.tex:258](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:258)

   ```tex
   the same violation removal on H100 benchmark traces, and ranks violations better (higher AP) on labelled
   V100 cluster jobs, provided the site is represented in training.
   ```

3. The matched ablation establishes a ranking effect, but the readiness comparison uses a separately configured earlier big-drop model.

   The conference version omits the arXiv disclosure that the big-drop model in Table II is not the matched-ablation model. As written, readers can reasonably infer that the 64.3 percent result comes from the matched model. Therefore, the matched experiment supports attributing the AP difference to the target, but does not by itself isolate the target’s causal effect on the simulated engaged-time curve.

   Replace [paper/main.tex:119](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:119) through line 122 with:

   ```tex
   target window; it needs no training. The \emph{learned} predictor is LightGBM~\cite{lightgbm} on 56 trailing features
   (lags, differences, rolling statistics, time since recent steps and drops, rhythm period, phase and
   rhythm forecasts), one model per actuator latency. The matched label ablation uses identical fixed
   model settings for the two labels, apart from the prevalence-derived class weight. The big-drop model
   in the readiness comparison is an earlier configuration with different leaf-size and early-stopping
   choices, so that comparison does not isolate the label alone. A shape-only variant divides every level
   feature by the trailing 60~s maximum.
   ```

   Replace [paper/main.tex:173](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:173) through line 177 with:

   ```tex
   The earlier configured big-drop trigger needs more engaged time than the control-aligned trigger
   (64.3\% at 90\%; difference $-$15.9 points, CI $-$25.7 to $-$3.9). At 95\% removal the interval includes
   zero (CI $-$26.3 to 0.5). Because these two readiness models were not identically configured, the
   matched ablation provides the cleaner evidence for the target's effect: AP 0.58 versus 0.96 on the
   control-aligned event.
   ```

   Replace the opening of the conclusion at [paper/main.tex:255](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:255) with:

   ```tex
   In our NLR experiments, training on the controller's event, a ramp-limit violation inside the
   actuator's engagement window, ranked relevant events substantially better than training the same
   pipeline on a generic large-drop label.
   ```

4. “Energy overhead” is inappropriate for the storage interpretation and reverses another arXiv correction.

   The reported quantity combines fill energy and assumed standby draw. For storage it is charge absorbed before later discharge and losses, not necessarily net energy overhead.

   Replace [paper/main.tex:102](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:102) through line 104 with:

   ```tex
   still filling, and report violations removed against engaged time. We also report an energy metric
   consisting of fill energy plus an assumed standby draw of 0--5\% of rated power while engaged. For
   storage, this is absorbed charge before any later discharge or loss, which the simulation does not model.
   ```

   Replace [paper/main.tex:203](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:203) through line 207 with:

   ```tex
   With operating points chosen on validation and a standby draw of 2\% of rated power, a 90\% target
   gives 86.8\% removal at 45.6\% engaged time and a 3.7\% reported energy metric for the learned trigger;
   rhythm replay meets the target only by staying engaged 99.2\% of the time, with a 5.4\% energy metric,
   versus 5.4\% for always-on.
   ```

5. Two technical claims lack references: LightGBM and the architecture-dependent NVML averaging behavior.

   Replace [paper/main.tex:90](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:90) with:

   ```tex
   \textbf{Sensor harmonization.} NVML documents that on recent architectures the default power reading is
   averaged over about 1~s, while older GPUs such as the V100 report instantaneous power~\cite{nvml}.
   ```

   The LightGBM citation is included in Finding 3.

   Add before [paper/main.tex:277](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:277):

   ```tex
   \bibitem{lightgbm} G.~Ke, Q.~Meng, T.~Finley, et al., ``LightGBM: A highly efficient gradient boosting decision tree,'' in \emph{Advances in Neural Information Processing Systems}, vol.~30, 2017.
   \bibitem{nvml} NVIDIA, ``NVML API reference guide: Device queries,'' 2026. [Online]. Available: \url{https://docs.nvidia.com/deploy/nvml-api/latest/api/group__nvmlDeviceQueries.html}
   ```

   Change [paper/main.tex:267](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:267) from:

   ```tex
   \begin{thebibliography}{9}
   ```

   to:

   ```tex
   \begin{thebibliography}{99}
   ```

6. The author affiliation is unconventional and may be rejected by a submission-system or publication check.

   “Yeshiva University alumnus” is not a current institutional affiliation. Unless the university has explicitly authorized its use, list the current independent affiliation and location.

   Replace [paper/main.tex:17](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:17) through line 19 with:

   ```tex
   \author{\IEEEauthorblockN{Sayed Raheel}
   \IEEEauthorblockA{Independent Researcher, New York, NY, USA\\
   \texttt{shussai1@mail.yu.edu}}}
   ```

   Confirm that continued use of the university email is permitted and that the MIRA author record matches the PDF exactly.

7. The forest plot is too compressed for a conference column.

   The long dataset labels consume most of the plot width, leaving a very narrow numerical region. This is the weakest formatting element in the PDF.

   Replace [paper/main.tex:221](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:221) through line 227 with:

   ```tex
   \begin{figure*}[t]
   \centering
   \includegraphics[width=0.78\textwidth]{fig_forest.pdf}
   \caption{AP difference between the learned control-aligned trigger and rhythm replay, with 95\%
   cluster-bootstrap intervals. Red: learned significantly better; blue: rhythm significantly better;
   grey: inconclusive. Unseen-site rows use shape-only features.}
   \label{fig:forest}
   \end{figure*}
   ```

   Rebuild and ensure that the float does not separate the plot excessively from Section IV-C.

8. Use the fifth page to address the likely PES reviewer objection: the paper currently reads more like an ML benchmark than a power-systems study.

   The four-page version provides no actuator power rating, required energy capacity, facility-level aggregation example, or sensitivity to the assumed 10 percent threshold and six-second hold. A PES reviewer may reject quickly because AP and engaged time do not establish implementability by a BESS, supercapacitor, or facility control system.

   The best use of the fifth page is a compact “Power-system interpretation” subsection containing:

   - The illustrative status of the ramp limit.
   - Limiter peak power and energy requirements on representative traces.
   - A facility-scale conversion or clearly qualified scaling example.
   - Sensitivity to ramp threshold, hold time, and actuator latency.
   - A distinction between filler-compute consumption and storage charge/discharge.

   If no additional simulations can be completed, add after [paper/main.tex:252](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:252):

   ```tex
   \emph{Power-system interpretation.} The 10\%/s threshold and idealized fill-only limiter define a
   comparative forecasting experiment, not a complete storage design. Engaged time is a readiness metric,
   not an energy-capacity or converter-rating requirement. A deployable design must additionally size
   charge and discharge power, usable energy, state-of-charge margin and thermal headroom from the
   facility-level load trace. It must also account for efficiency, recovery after an event, simultaneous
   jobs and the applicable interconnection ramp requirement. The present results therefore show when a
   predictive controller would request readiness under the stated simulator, rather than demonstrating
   compliance by a particular storage installation.
   ```

The keywords are appropriate, the title is relevant to the PES GM large-dynamic-load theme, Tables I and II are readable, and the abstract, results, and conclusion become internally consistent once Findings 2 through 4 are applied.
diff --git a/paper/main.tex b/paper/main.tex
index 461f37b..d7a80d5 100644
--- a/paper/main.tex
+++ b/paper/main.tex
@@ -21,10 +21,11 @@
 \maketitle
 
 \begin{abstract}
-Large AI training jobs swing GPU power by tens of percent within a second, and synchronized jobs can
-violate the ramp limits that utilities place on large loads. Fill-type smoothing (filler GPU work,
-storage) removes these violations but must be engaged before the fall, and keeping it engaged costs
-energy. Forecasting can decide when to engage it. We find that the choice of training target matters
+Large AI training jobs can swing GPU power by tens of percent within a second, and synchronized jobs can
+create fast load ramps of concern at large grid-connected facilities. In an idealized simulation,
+fill-type smoothing, using filler GPU work or storage, can reduce violations of an illustrative ramp
+threshold, but it must be engaged before the fall and keeping it engaged has a cost.
+Forecasting can decide when to engage it. We find that the choice of training target matters
 substantially. In a matched-pipeline ablation, a gradient-boosted classifier trained on the usual target,
 ``a large power drop is coming'', ranks the violations a ramp limiter must catch poorly (average precision
 0.58). Trained on the controller's own event, ``a ramp-limit violation will occur while a
@@ -34,7 +35,7 @@ traces, against 0.67 for no-learning rhythm replay of the same target. With a th
 validation for a 90\% removal target, the learned trigger removes 86.8\% of test
 violations with the actuator engaged 45.6\% of the time, while rhythm replay meets
 the target only by staying engaged 99.2\% of the time, i.e.\ effectively always on.
-Across three public datasets covering H100, B200 and V100 nodes and both benchmark and real user jobs,
+Across three public datasets covering H100, B200 and V100 nodes and both benchmark and labelled cluster jobs,
 the learned trigger has significantly higher AP than rhythm replay on two datasets when that site is in the
 training data, after harmonizing sensor averaging; the third is inconclusive. Transfer to an unseen
 site is unreliable, which we report as an open problem.
@@ -63,7 +64,7 @@ predictor. Our contributions:
 a limiter armed now would cover, instead of a generic ``large drop''.
 \item A readiness analysis (violations removed versus time engaged) comparing learned triggers, rhythm
 replay, an always-on limiter and a perfect-foresight oracle in one simulator.
-\item A three-dataset study (H100, B200, V100; benchmarks and real jobs) with job-clustered confidence
+\item A three-dataset study (H100, B200, V100; benchmarks and labelled cluster jobs) with job-clustered confidence
 intervals, a sensor-harmonization step, and a negative result on unseen sites.
 \end{itemize}
 
@@ -77,7 +78,7 @@ independent unit. \textbf{Elsayed et al.}~\cite{elsayed}: single 8$\times$H100 a
 running diffusion and Llama 1B--8B fine-tuning sweeps, 15-minute sessions, 32 unique
 sessions. \textbf{MIT Supercloud}~\cite{supercloud}: a stratified subset of 560 labelled jobs (80 per
 model class: VGG, ResNet, Inception, U-Net, BERT, DistilBERT, GNN) on nodes with one or two V100s,
-nvidia-smi at 10~Hz, 1,292 node-hours of real user jobs.
+nvidia-smi at 10~Hz, 1,292 node-hours of labelled cluster jobs.
 
 All traces are averaged onto a 0.2~s grid and expressed as ``NLR-equivalent watts'' (power $\times$
 2.8~kW divided by the node's rated GPU power), so a 10\%/s limit means the same fraction of rated power
@@ -88,20 +89,22 @@ same session and so are not independent. (The big-drop baselines from earlier wo
 validation units.)
 
 \textbf{Sensor harmonization.} NVML documents that on recent architectures the default power reading is
-averaged over about 1~s, while older GPUs such as the V100 report instantaneous power. The NLR
+averaged over about 1~s, while older GPUs such as the V100 report instantaneous power~\cite{nvml}. The NLR
 documentation does not state which reading was logged. Raw V100 traces flicker: without harmonization,
 91\% of Supercloud test seconds are labelled ``violation imminent''. We apply a 1~s trailing mean to
 Supercloud so that all three datasets are compared at similar effective bandwidth.
 
 \section{Problem and methods}
 \subsection{Ramp limit, limiter and readiness}
-A violation starts when the node's 1~s down-ramp exceeds 10\% of rated power. A fill-type limiter adds
+For this study, a violation starts when the node's 1~s down-ramp exceeds an illustrative threshold of
+10\% of rated power per second; this is a normalized study threshold, not a specific utility requirement. A fill-type limiter adds
 power only when the load falls faster than the limit allows, then tapers at 90\% of the allowed rate. A trigger
 issued at row $t$ acts one sample later (each row averages $[t, t{+}0.2\,\mathrm{s})$), engages the
 limiter after an actuator latency $L$ (1~s unless stated) and arms it for 6~s; the limiter keeps
 filling until it meets the load. We count as \emph{engaged} every sample where the limiter is armed or
-still filling, and report violations removed against engaged time, plus energy overhead with a standby
-draw of 0--5\% of rated power while engaged. References: always-on, always-burn (a floor at 80\% of the trailing 60~s peak,
+still filling, and report violations removed against engaged time. We also report an energy metric
+consisting of fill energy plus an assumed standby draw of 0--5\% of rated power while engaged; for
+storage, this is absorbed charge before any later discharge or loss, which the simulation does not model. References: always-on, always-burn (a floor at 80\% of the trailing 60~s peak,
 which removes only 6.7\% of violations for 6.8\% extra energy) and an oracle that
 arms just in time for every violation, including those induced by the limiter itself.
 
@@ -116,9 +119,11 @@ targets differ substantially.
 \subsection{Predictors}
 \emph{Rhythm replay} estimates the period $P$ from a trailing 120~s autocorrelation, predicts
 $\hat p(t+k)=p(t+k-P\lceil k/P\rceil)$, and scores the largest predicted 1~s down-ramp inside the
-target window; it needs no training. The \emph{learned} predictor is LightGBM on 56 trailing features
+target window; it needs no training. The \emph{learned} predictor is LightGBM~\cite{lightgbm} on 56 trailing features
 (lags, differences, rolling statistics, time since recent steps and drops, rhythm period, phase and
-rhythm forecasts), one model per actuator latency. A shape-only variant divides every level feature by
+rhythm forecasts), one model per actuator latency. The big-drop model in the readiness comparison is an
+earlier configuration with different leaf-size and early-stopping choices, so that comparison does not
+isolate the label alone; the matched ablation does. A shape-only variant divides every level feature by
 the trailing 60~s maximum.
 
 \subsection{Evaluation}
@@ -170,11 +175,12 @@ engaged time, whereas rhythm replay of the same target reaches 90\% only at 99.2
 i.e.\ it is no better than always-on. The paired cluster-bootstrap difference is
 $-$50.8 points (95\% CI $-$57.4 to
 $-$8.8), and $-$40.8 points at 95\% removal (CI
-$-$49.1 to $-$31.4). The learned big-drop trigger
+$-$49.1 to $-$31.4). The earlier configured big-drop trigger
 needs more engaged time than the control-aligned one (64.3\% at 90\%; difference
 $-$15.9 points, CI $-$25.7 to $-$3.9). At 95\%
 removal the interval includes zero (CI $-$26.3 to 0.5), so with
-12 test clusters the target's effect is clearest in ranking quality (AP 0.58 vs 0.96). The oracle removes all violations at 29.8\% engaged time, which bounds what
+12 test clusters and non-identical configurations, the matched ablation is the cleaner evidence for the
+target's effect (AP 0.58 vs 0.96). The oracle removes all violations at 29.8\% engaged time, which bounds what
 better prediction could still gain.
 
 \begin{table}[t]
@@ -202,16 +208,16 @@ Always-on removes everything but is always engaged.}
 
 With operating points chosen on validation and a standby draw of 2\% of rated power, a 90\% target
 gives 86.8\% removal at 45.6\% engaged time and
-3.7\% energy overhead for the learned trigger; rhythm replay meets the target only
+a 3.7\% energy metric for the learned trigger; rhythm replay meets the target only
 by staying engaged 99.2\% of the time (5.4\%
-overhead, versus 5.4\% for always-on). At an 80\% target the validation-chosen
+energy metric, versus 5.4\% for always-on). At an 80\% target the validation-chosen
 learned threshold undershoots on test (73.7\% removal), a reminder that operating
 points chosen on few validation jobs transfer imperfectly.
 
 \subsection{Across sites and GPUs}
 Fig.~\ref{fig:forest} summarizes the learned-minus-rhythm AP difference. Trained on the test site's own
 training jobs (in-domain) or on all three datasets (pooled), the learned trigger significantly beats
-rhythm replay on NLR (pooled AP 0.96 vs 0.67) and on real Supercloud jobs
+rhythm replay on NLR (pooled AP 0.96 vs 0.67) and on labelled Supercloud jobs
 (pooled 0.88 vs 0.74; exploratory per-class intervals, without multiplicity correction, are
 positive for 7 of 7 model classes). On Elsayed the point estimate favours learning
 (0.92 vs 0.88) but the interval includes zero with six test
@@ -222,7 +228,8 @@ cadence suits replay, but two test sessions do not allow a firm conclusion.
 \centering
 \includegraphics[width=\columnwidth]{fig_forest.pdf}
 \caption{AP difference between the learned control-aligned trigger and rhythm replay, with 95\%
-cluster bootstrap intervals. Red: learned significantly better; blue: rhythm significantly better.}
+cluster-bootstrap intervals. Red: learned significantly better; blue: rhythm significantly better;
+grey: inconclusive. Unseen-site rows use shape-only features.}
 \label{fig:forest}
 \end{figure}
 
@@ -246,25 +253,34 @@ measured lead times are optimistic. \emph{Simulation.} The actuator is an ideali
 latency, hold time and standby draw; storage capacity, state of charge, efficiency and wear are not modelled, and standby cost is an
 assumed fraction of rated power.
 \emph{Workloads.} NLR and Elsayed are scripted benchmarks; NLR inference falls are dominated by gaps
-between benchmark runs, and each NLR inference workload is a single session. Supercloud adds real jobs
-on older V100 nodes. \emph{Scale.} Results are per node; synchronized multi-node jobs scale the same
+between benchmark runs, and each NLR inference workload is a single session. Supercloud adds
+scheduler-observed labelled jobs on older V100 nodes. \emph{Scale.} Results are per node; synchronized multi-node jobs scale the same
 swing, while desynchronized jobs partly cancel. \emph{Licences.} Supercloud is CC BY-NC-ND and the Elsayed
 archive README states CC BY-NC-ND; both were used for research only and are not redistributed.
+\emph{Power-system interpretation.} The 10\%/s threshold and idealized fill-only limiter define a
+comparative forecasting experiment, not a complete storage design. Engaged time is a readiness metric,
+not an energy-capacity or converter-rating requirement. A deployable design must also size charge and
+discharge power, usable energy, state-of-charge margin and thermal headroom from the facility-level load
+trace, and account for efficiency, recovery after an event, simultaneous jobs and the applicable
+interconnection ramp requirement. The results show when a predictive controller would request readiness
+under the stated simulator, not compliance by a particular storage installation.
 
 \section{Conclusion}
-For fill-type smoothing of AI power swings, a forecaster should be trained on the controller's event, a
-ramp-limit violation inside the actuator's engagement window, rather than on a generic large drop. With
-that target a small gradient-boosted model needs substantially less engaged time than rhythm replay for
-the same violation removal on H100 benchmark traces, and ranks violations better (higher AP) on real
-V100 jobs, provided the site is represented in training. Closing the gap to the oracle and making learned triggers transfer to
+In our NLR experiments, training on the controller's event, a ramp-limit violation inside the actuator's
+engagement window, ranked relevant events substantially better than training the same pipeline on a
+generic large-drop label. With that target a small gradient-boosted model needs substantially less engaged time than rhythm replay for
+the same violation removal on H100 benchmark traces, and ranks violations better (higher AP) on labelled
+V100 cluster jobs, provided the site is represented in training. Closing the gap to the oracle and making learned triggers transfer to
 new sites are the natural next steps.
 
-\section*{Code availability and use of AI tools}
+\section*{Code availability}
 Code is available from the author on request; the datasets are public from their original sources.
+
+\section*{Acknowledgment}
 Analysis code and text were drafted with the help of AI coding and writing assistants and independently
 reviewed by a separate AI model. The author checked the results and is responsible for the content.
 
-\begin{thebibliography}{9}
+\begin{thebibliography}{99}
 \bibitem{msft_stab} E.~Choukse, B.~Warrier, S.~Heath, et al., ``Power stabilization for AI training datacenters,'' arXiv:2508.14318, 2025.
 \bibitem{easyrider} D.~Jensen, G.~Wilkins, O.~Nnorom~Jr., H.~Budd, R.~Rajagopal, J.~Rivas-Davila, and P.~Levis, ``EasyRider: Mitigating power transients in datacenter-scale training workloads,'' arXiv:2604.15522, 2026.
 \bibitem{activefilter} D.~Jensen, G.~Wilkins, O.~Nnorom~Jr., H.~Budd, P.~Levis, and J.~Rivas, ``Active filter design for buffering datacenter-scale power fluctuations from training AI,'' arXiv:2609.13490, 2026.
@@ -274,6 +290,8 @@ reviewed by a separate AI model. The author checked the results and is responsib
 \bibitem{nlr} R.~Vercellino, J.~Willard, G.~Campos, W.~da~Silva~Pereira, O.~Hull, M.~Selensky, and J.~Mueller, ``Measurement of generative AI workload power profiles for whole-facility data center infrastructure planning,'' arXiv:2604.07345, 2026. Data: ``Dataset of Generative AI Workload Power Profiles,'' National Laboratory of the Rockies, doi:10.7799/3025227.
 \bibitem{elsayed} A.~A.~E.~Elsayed, A.~A.~Al-Obaidi, and H.~E.~Z.~Farag, ``Characterization of high-resolution AI data center training workloads on single and multiple GPU nodes,'' \emph{Scientific Data}, vol.~13, art.~1268, 2026, doi:10.1038/s41597-026-07496-6. Data: figshare, doi:10.6084/m9.figshare.31654879.
 \bibitem{supercloud} S.~Samsi, M.~L.~Weiss, D.~Bestor, et al., ``The MIT Supercloud dataset,'' in \emph{Proc. IEEE High Performance Extreme Computing Conf. (HPEC)}, 2021, pp.~1--8, doi:10.1109/HPEC49654.2021.9622850.
+\bibitem{lightgbm} G.~Ke, Q.~Meng, T.~Finley, et al., ``LightGBM: A highly efficient gradient boosting decision tree,'' in \emph{Advances in Neural Information Processing Systems}, vol.~30, 2017.
+\bibitem{nvml} NVIDIA, ``NVML API reference guide: Device queries,'' 2026. [Online]. Available: \url{https://docs.nvidia.com/deploy/nvml-api/latest/api/group__nvmlDeviceQueries.html}
 \end{thebibliography}
 
 \end{document}
diff --git a/paper/template.tex b/paper/template.tex
index 99eda74..1d71a15 100644
--- a/paper/template.tex
+++ b/paper/template.tex
@@ -21,10 +21,11 @@
 \maketitle
 
 \begin{abstract}
-Large AI training jobs swing GPU power by tens of percent within a second, and synchronized jobs can
-violate the ramp limits that utilities place on large loads. Fill-type smoothing (filler GPU work,
-storage) removes these violations but must be engaged before the fall, and keeping it engaged costs
-energy. Forecasting can decide when to engage it. We find that the choice of training target matters
+Large AI training jobs can swing GPU power by tens of percent within a second, and synchronized jobs can
+create fast load ramps of concern at large grid-connected facilities. In an idealized simulation,
+fill-type smoothing, using filler GPU work or storage, can reduce violations of an illustrative ramp
+threshold, but it must be engaged before the fall and keeping it engaged has a cost.
+Forecasting can decide when to engage it. We find that the choice of training target matters
 substantially. In a matched-pipeline ablation, a gradient-boosted classifier trained on the usual target,
 ``a large power drop is coming'', ranks the violations a ramp limiter must catch poorly (average precision
 <<abl_matched_drop_ap>>). Trained on the controller's own event, ``a ramp-limit violation will occur while a
@@ -34,7 +35,7 @@ traces, against <<nlr_ap_rh>> for no-learning rhythm replay of the same target.
 validation for a 90\% removal target, the learned trigger removes <<t90_sb0_ml_aligned_cut>>\% of test
 violations with the actuator engaged <<t90_sb0_ml_aligned_armed>>\% of the time, while rhythm replay meets
 the target only by staying engaged <<t90_sb0_rhythm_aligned_armed>>\% of the time, i.e.\ effectively always on.
-Across three public datasets covering H100, B200 and V100 nodes and both benchmark and real user jobs,
+Across three public datasets covering H100, B200 and V100 nodes and both benchmark and labelled cluster jobs,
 the learned trigger has significantly higher AP than rhythm replay on two datasets when that site is in the
 training data, after harmonizing sensor averaging; the third is inconclusive. Transfer to an unseen
 site is unreliable, which we report as an open problem.
@@ -63,7 +64,7 @@ predictor. Our contributions:
 a limiter armed now would cover, instead of a generic ``large drop''.
 \item A readiness analysis (violations removed versus time engaged) comparing learned triggers, rhythm
 replay, an always-on limiter and a perfect-foresight oracle in one simulator.
-\item A three-dataset study (H100, B200, V100; benchmarks and real jobs) with job-clustered confidence
+\item A three-dataset study (H100, B200, V100; benchmarks and labelled cluster jobs) with job-clustered confidence
 intervals, a sensor-harmonization step, and a negative result on unseen sites.
 \end{itemize}
 
@@ -77,7 +78,7 @@ independent unit. \textbf{Elsayed et al.}~\cite{elsayed}: single 8$\times$H100 a
 running diffusion and Llama 1B--8B fine-tuning sweeps, 15-minute sessions, <<elsayed_units>> unique
 sessions. \textbf{MIT Supercloud}~\cite{supercloud}: a stratified subset of 560 labelled jobs (80 per
 model class: VGG, ResNet, Inception, U-Net, BERT, DistilBERT, GNN) on nodes with one or two V100s,
-nvidia-smi at 10~Hz, <<supercloud_node_h>> node-hours of real user jobs.
+nvidia-smi at 10~Hz, <<supercloud_node_h>> node-hours of labelled cluster jobs.
 
 All traces are averaged onto a 0.2~s grid and expressed as ``NLR-equivalent watts'' (power $\times$
 2.8~kW divided by the node's rated GPU power), so a 10\%/s limit means the same fraction of rated power
@@ -88,20 +89,22 @@ same session and so are not independent. (The big-drop baselines from earlier wo
 validation units.)
 
 \textbf{Sensor harmonization.} NVML documents that on recent architectures the default power reading is
-averaged over about 1~s, while older GPUs such as the V100 report instantaneous power. The NLR
+averaged over about 1~s, while older GPUs such as the V100 report instantaneous power~\cite{nvml}. The NLR
 documentation does not state which reading was logged. Raw V100 traces flicker: without harmonization,
 91\% of Supercloud test seconds are labelled ``violation imminent''. We apply a 1~s trailing mean to
 Supercloud so that all three datasets are compared at similar effective bandwidth.
 
 \section{Problem and methods}
 \subsection{Ramp limit, limiter and readiness}
-A violation starts when the node's 1~s down-ramp exceeds 10\% of rated power. A fill-type limiter adds
+For this study, a violation starts when the node's 1~s down-ramp exceeds an illustrative threshold of
+10\% of rated power per second; this is a normalized study threshold, not a specific utility requirement. A fill-type limiter adds
 power only when the load falls faster than the limit allows, then tapers at 90\% of the allowed rate. A trigger
 issued at row $t$ acts one sample later (each row averages $[t, t{+}0.2\,\mathrm{s})$), engages the
 limiter after an actuator latency $L$ (1~s unless stated) and arms it for 6~s; the limiter keeps
 filling until it meets the load. We count as \emph{engaged} every sample where the limiter is armed or
-still filling, and report violations removed against engaged time, plus energy overhead with a standby
-draw of 0--5\% of rated power while engaged. References: always-on, always-burn (a floor at 80\% of the trailing 60~s peak,
+still filling, and report violations removed against engaged time. We also report an energy metric
+consisting of fill energy plus an assumed standby draw of 0--5\% of rated power while engaged; for
+storage, this is absorbed charge before any later discharge or loss, which the simulation does not model. References: always-on, always-burn (a floor at 80\% of the trailing 60~s peak,
 which removes only <<burn_cut>>\% of violations for <<burn_ovh>>\% extra energy) and an oracle that
 arms just in time for every violation, including those induced by the limiter itself.
 
@@ -116,9 +119,11 @@ targets differ substantially.
 \subsection{Predictors}
 \emph{Rhythm replay} estimates the period $P$ from a trailing 120~s autocorrelation, predicts
 $\hat p(t+k)=p(t+k-P\lceil k/P\rceil)$, and scores the largest predicted 1~s down-ramp inside the
-target window; it needs no training. The \emph{learned} predictor is LightGBM on 56 trailing features
+target window; it needs no training. The \emph{learned} predictor is LightGBM~\cite{lightgbm} on 56 trailing features
 (lags, differences, rolling statistics, time since recent steps and drops, rhythm period, phase and
-rhythm forecasts), one model per actuator latency. A shape-only variant divides every level feature by
+rhythm forecasts), one model per actuator latency. The big-drop model in the readiness comparison is an
+earlier configuration with different leaf-size and early-stopping choices, so that comparison does not
+isolate the label alone; the matched ablation does. A shape-only variant divides every level feature by
 the trailing 60~s maximum.
 
 \subsection{Evaluation}
@@ -170,11 +175,12 @@ engaged time, whereas rhythm replay of the same target reaches 90\% only at <<an
 i.e.\ it is no better than always-on. The paired cluster-bootstrap difference is
 <<an90_diff_vs_rhythm_aligned>> points (95\% CI <<an90_diff_vs_rhythm_aligned_lo>> to
 <<an90_diff_vs_rhythm_aligned_hi>>), and <<an95_diff_vs_rhythm_aligned>> points at 95\% removal (CI
-<<an95_diff_vs_rhythm_aligned_lo>> to <<an95_diff_vs_rhythm_aligned_hi>>). The learned big-drop trigger
+<<an95_diff_vs_rhythm_aligned_lo>> to <<an95_diff_vs_rhythm_aligned_hi>>). The earlier configured big-drop trigger
 needs more engaged time than the control-aligned one (<<an90_ml_alarm_armed>>\% at 90\%; difference
 <<an90_diff_vs_ml_alarm>> points, CI <<an90_diff_vs_ml_alarm_lo>> to <<an90_diff_vs_ml_alarm_hi>>). At 95\%
 removal the interval includes zero (CI <<an95_diff_vs_ml_alarm_lo>> to <<an95_diff_vs_ml_alarm_hi>>), so with
-12 test clusters the target's effect is clearest in ranking quality (AP <<nlr_ap_old>> vs <<nlr_ap_ml>>). The oracle removes all violations at <<oracle_armed>>\% engaged time, which bounds what
+12 test clusters and non-identical configurations, the matched ablation is the cleaner evidence for the
+target's effect (AP <<abl_matched_drop_ap>> vs <<abl_matched_aligned_ap>>). The oracle removes all violations at <<oracle_armed>>\% engaged time, which bounds what
 better prediction could still gain.
 
 \begin{table}[t]
@@ -202,16 +208,16 @@ Always-on removes everything but is always engaged.}
 
 With operating points chosen on validation and a standby draw of 2\% of rated power, a 90\% target
 gives <<t90_sb2_ml_aligned_cut>>\% removal at <<t90_sb2_ml_aligned_armed>>\% engaged time and
-<<t90_sb2_ml_aligned_ovh>>\% energy overhead for the learned trigger; rhythm replay meets the target only
+a <<t90_sb2_ml_aligned_ovh>>\% energy metric for the learned trigger; rhythm replay meets the target only
 by staying engaged <<t90_sb2_rhythm_aligned_armed>>\% of the time (<<t90_sb2_rhythm_aligned_ovh>>\%
-overhead, versus <<t90_sb2_always_on_ovh>>\% for always-on). At an 80\% target the validation-chosen
+energy metric, versus <<t90_sb2_always_on_ovh>>\% for always-on). At an 80\% target the validation-chosen
 learned threshold undershoots on test (<<t80_sb2_ml_aligned_cut>>\% removal), a reminder that operating
 points chosen on few validation jobs transfer imperfectly.
 
 \subsection{Across sites and GPUs}
 Fig.~\ref{fig:forest} summarizes the learned-minus-rhythm AP difference. Trained on the test site's own
 training jobs (in-domain) or on all three datasets (pooled), the learned trigger significantly beats
-rhythm replay on NLR (pooled AP <<x_pooled_nlr_ml>> vs <<x_pooled_nlr_rh>>) and on real Supercloud jobs
+rhythm replay on NLR (pooled AP <<x_pooled_nlr_ml>> vs <<x_pooled_nlr_rh>>) and on labelled Supercloud jobs
 (pooled <<x_pooled_supercloud_ml>> vs <<x_pooled_supercloud_rh>>; exploratory per-class intervals, without multiplicity correction, are
 positive for <<sc_classes_sig>> of <<sc_classes>> model classes). On Elsayed the point estimate favours learning
 (<<x_pooled_elsayed_ml>> vs <<x_pooled_elsayed_rh>>) but the interval includes zero with six test
@@ -222,7 +228,8 @@ cadence suits replay, but two test sessions do not allow a firm conclusion.
 \centering
 \includegraphics[width=\columnwidth]{fig_forest.pdf}
 \caption{AP difference between the learned control-aligned trigger and rhythm replay, with 95\%
-cluster bootstrap intervals. Red: learned significantly better; blue: rhythm significantly better.}
+cluster-bootstrap intervals. Red: learned significantly better; blue: rhythm significantly better;
+grey: inconclusive. Unseen-site rows use shape-only features.}
 \label{fig:forest}
 \end{figure}
 
@@ -246,25 +253,34 @@ measured lead times are optimistic. \emph{Simulation.} The actuator is an ideali
 latency, hold time and standby draw; storage capacity, state of charge, efficiency and wear are not modelled, and standby cost is an
 assumed fraction of rated power.
 \emph{Workloads.} NLR and Elsayed are scripted benchmarks; NLR inference falls are dominated by gaps
-between benchmark runs, and each NLR inference workload is a single session. Supercloud adds real jobs
-on older V100 nodes. \emph{Scale.} Results are per node; synchronized multi-node jobs scale the same
+between benchmark runs, and each NLR inference workload is a single session. Supercloud adds
+scheduler-observed labelled jobs on older V100 nodes. \emph{Scale.} Results are per node; synchronized multi-node jobs scale the same
 swing, while desynchronized jobs partly cancel. \emph{Licences.} Supercloud is CC BY-NC-ND and the Elsayed
 archive README states CC BY-NC-ND; both were used for research only and are not redistributed.
+\emph{Power-system interpretation.} The 10\%/s threshold and idealized fill-only limiter define a
+comparative forecasting experiment, not a complete storage design. Engaged time is a readiness metric,
+not an energy-capacity or converter-rating requirement. A deployable design must also size charge and
+discharge power, usable energy, state-of-charge margin and thermal headroom from the facility-level load
+trace, and account for efficiency, recovery after an event, simultaneous jobs and the applicable
+interconnection ramp requirement. The results show when a predictive controller would request readiness
+under the stated simulator, not compliance by a particular storage installation.
 
 \section{Conclusion}
-For fill-type smoothing of AI power swings, a forecaster should be trained on the controller's event, a
-ramp-limit violation inside the actuator's engagement window, rather than on a generic large drop. With
-that target a small gradient-boosted model needs substantially less engaged time than rhythm replay for
-the same violation removal on H100 benchmark traces, and ranks violations better (higher AP) on real
-V100 jobs, provided the site is represented in training. Closing the gap to the oracle and making learned triggers transfer to
+In our NLR experiments, training on the controller's event, a ramp-limit violation inside the actuator's
+engagement window, ranked relevant events substantially better than training the same pipeline on a
+generic large-drop label. With that target a small gradient-boosted model needs substantially less engaged time than rhythm replay for
+the same violation removal on H100 benchmark traces, and ranks violations better (higher AP) on labelled
+V100 cluster jobs, provided the site is represented in training. Closing the gap to the oracle and making learned triggers transfer to
 new sites are the natural next steps.
 
-\section*{Code availability and use of AI tools}
+\section*{Code availability}
 Code is available from the author on request; the datasets are public from their original sources.
+
+\section*{Acknowledgment}
 Analysis code and text were drafted with the help of AI coding and writing assistants and independently
 reviewed by a separate AI model. The author checked the results and is responsible for the content.
 
-\begin{thebibliography}{9}
+\begin{thebibliography}{99}
 \bibitem{msft_stab} E.~Choukse, B.~Warrier, S.~Heath, et al., ``Power stabilization for AI training datacenters,'' arXiv:2508.14318, 2025.
 \bibitem{easyrider} D.~Jensen, G.~Wilkins, O.~Nnorom~Jr., H.~Budd, R.~Rajagopal, J.~Rivas-Davila, and P.~Levis, ``EasyRider: Mitigating power transients in datacenter-scale training workloads,'' arXiv:2604.15522, 2026.
 \bibitem{activefilter} D.~Jensen, G.~Wilkins, O.~Nnorom~Jr., H.~Budd, P.~Levis, and J.~Rivas, ``Active filter design for buffering datacenter-scale power fluctuations from training AI,'' arXiv:2609.13490, 2026.
@@ -274,6 +290,8 @@ reviewed by a separate AI model. The author checked the results and is responsib
 \bibitem{nlr} R.~Vercellino, J.~Willard, G.~Campos, W.~da~Silva~Pereira, O.~Hull, M.~Selensky, and J.~Mueller, ``Measurement of generative AI workload power profiles for whole-facility data center infrastructure planning,'' arXiv:2604.07345, 2026. Data: ``Dataset of Generative AI Workload Power Profiles,'' National Laboratory of the Rockies, doi:10.7799/3025227.
 \bibitem{elsayed} A.~A.~E.~Elsayed, A.~A.~Al-Obaidi, and H.~E.~Z.~Farag, ``Characterization of high-resolution AI data center training workloads on single and multiple GPU nodes,'' \emph{Scientific Data}, vol.~13, art.~1268, 2026, doi:10.1038/s41597-026-07496-6. Data: figshare, doi:10.6084/m9.figshare.31654879.
 \bibitem{supercloud} S.~Samsi, M.~L.~Weiss, D.~Bestor, et al., ``The MIT Supercloud dataset,'' in \emph{Proc. IEEE High Performance Extreme Computing Conf. (HPEC)}, 2021, pp.~1--8, doi:10.1109/HPEC49654.2021.9622850.
+\bibitem{lightgbm} G.~Ke, Q.~Meng, T.~Finley, et al., ``LightGBM: A highly efficient gradient boosting decision tree,'' in \emph{Advances in Neural Information Processing Systems}, vol.~30, 2017.
+\bibitem{nvml} NVIDIA, ``NVML API reference guide: Device queries,'' 2026. [Online]. Available: \url{https://docs.nvidia.com/deploy/nvml-api/latest/api/group__nvmlDeviceQueries.html}
 \end{thebibliography}
 
 \end{document}
paper/main.tex:15:\title{Predict the Breach, Not the Drop:\\Control-Aligned Learning for Smoothing\\AI Training Power Swings}
paper/main.tex:24:Large AI training jobs can swing GPU power by tens of percent within a second, and synchronized jobs can
paper/main.tex:32:limiter armed now would be armed'', the same pipeline reaches 0.96 (difference 95\% CI
paper/main.tex:35:validation for a 90\% removal target, the learned trigger removes 86.8\% of test
paper/main.tex:36:violations with the actuator engaged 45.6\% of the time, while rhythm replay meets
paper/main.tex:37:the target only by staying engaged 99.2\% of the time, i.e.\ effectively always on.
paper/main.tex:45:data centers, AI workloads, ramp rate, load forecasting, power smoothing, energy storage
paper/main.tex:55:predictors~\cite{lyu}; and AI data center load has been forecast at minute scales~\cite{mughees}. We are
paper/main.tex:84:2.8~kW divided by the node's rated GPU power), so a 10\%/s limit means the same fraction of rated power
paper/main.tex:88:same session and so are not independent. (The big-drop baselines from earlier work were early-stopped on all
paper/main.tex:94:91\% of Supercloud test seconds are labelled ``violation imminent''. We apply a 1~s trailing mean to
paper/main.tex:100:10\% of rated power per second; this is a normalized study threshold, not a specific utility requirement. A fill-type limiter adds
paper/main.tex:101:power only when the load falls faster than the limit allows, then tapers at 90\% of the allowed rate. A trigger
paper/main.tex:106:consisting of fill energy plus an assumed standby draw of 0--5\% of rated power while engaged; for
paper/main.tex:107:storage, this is absorbed charge before any later discharge or loss, which the simulation does not model. References: always-on, always-burn (a floor at 80\% of the trailing 60~s peak,
paper/main.tex:108:which removes only 6.7\% of violations for 6.8\% extra energy) and an oracle that
paper/main.tex:112:The \emph{big-drop} target labels $t$ positive if a fall of more than 30\% of the recent peak within
paper/main.tex:116:Many violations (e.g.\ the 22\% square wave of Llama LoRA training) are not big drops, so the two
paper/main.tex:143:against 0.96, a paired cluster-bootstrap difference of 0.37 (95\% CI
paper/main.tex:168:Fig.~\ref{fig:ready} sweeps each trigger's threshold (about 200 validation-score quantiles) on NLR test
paper/main.tex:173:To remove 90\% of violations, the control-aligned learned trigger needs 48.4\%
paper/main.tex:174:engaged time, whereas rhythm replay of the same target reaches 90\% only at 99.2\%,
paper/main.tex:176:$-$50.8 points (95\% CI $-$57.4 to
paper/main.tex:177:$-$8.8), and $-$40.8 points at 95\% removal (CI
paper/main.tex:179:needs more engaged time than the control-aligned one (64.3\% at 90\%; difference
paper/main.tex:180:$-$15.9 points, CI $-$25.7 to $-$3.9). At 95\%
paper/main.tex:183:target's effect (AP 0.58 vs 0.96). The oracle removes all violations at 29.8\% engaged time, which bounds what
paper/main.tex:188:\caption{Engaged time (\% of time) needed to reach a violation-removal level, NLR test, 1~s latency.}
paper/main.tex:194:80\% & 43.1 & 51.5 & 53.0\\
paper/main.tex:195:90\% & 48.4 & 99.2 & 64.3\\
paper/main.tex:196:95\% & 58.4 & 99.2 & 74.8\\
paper/main.tex:209:With operating points chosen on validation and a standby draw of 2\% of rated power, a 90\% target
paper/main.tex:210:gives 86.8\% removal at 45.6\% engaged time and
paper/main.tex:211:a 3.7\% energy metric for the learned trigger; rhythm replay meets the target only
paper/main.tex:212:by staying engaged 99.2\% of the time (5.4\%
paper/main.tex:213:energy metric, versus 5.4\% for always-on). At an 80\% target the validation-chosen
paper/main.tex:214:learned threshold undershoots on test (73.7\% removal), a reminder that operating
paper/main.tex:218:Fig.~\ref{fig:forest} summarizes the learned-minus-rhythm AP difference. Trained on the test site's own
paper/main.tex:230:\caption{AP difference between the learned control-aligned trigger and rhythm replay, with 95\%
paper/main.tex:260:\emph{Power-system interpretation.} The 10\%/s threshold and idealized fill-only limiter define a
paper/main.tex:279:\section*{Acknowledgment}
paper/main.tex:280:Analysis code and text were drafted with the help of AI coding and writing assistants and independently
paper/main.tex:281:reviewed by a separate AI model. The author checked the results and is responsible for the content.
paper/main.tex:284:\bibitem{msft_stab} E.~Choukse, B.~Warrier, S.~Heath, et al., ``Power stabilization for AI training datacenters,'' arXiv:2508.14318, 2025.
paper/main.tex:286:\bibitem{activefilter} D.~Jensen, G.~Wilkins, O.~Nnorom~Jr., H.~Budd, P.~Levis, and J.~Rivas, ``Active filter design for buffering datacenter-scale power fluctuations from training AI,'' arXiv:2609.13490, 2026.
paper/main.tex:287:\bibitem{hessdpc} H.~You, C.~Lou, and J.~Yang, ``Source side mitigation of AI datacenter power fluctuations with a hybrid energy storage system and residual differentiable predictive control,'' arXiv:2606.04869, 2026.
paper/main.tex:288:\bibitem{lyu} X.~Lyu, W.~Du, S.~M.~Mohiuddin, and B.~A.~Ross, ``Communication delay robust control of BESS for AI training load smoothing,'' arXiv:2609.22542, 2026.
paper/main.tex:289:\bibitem{mughees} M.~Mughees, Y.~Li, Y.~Chen, and Y.~R.~Li, ``Short-term load forecasting for AI-data center,'' arXiv:2503.07756, 2025 (accepted to IEEE PES General Meeting 2025).
paper/main.tex:290:\bibitem{nlr} R.~Vercellino, J.~Willard, G.~Campos, W.~da~Silva~Pereira, O.~Hull, M.~Selensky, and J.~Mueller, ``Measurement of generative AI workload power profiles for whole-facility data center infrastructure planning,'' arXiv:2604.07345, 2026. Data: ``Dataset of Generative AI Workload Power Profiles,'' National Laboratory of the Rockies, doi:10.7799/3025227.
paper/main.tex:291:\bibitem{elsayed} A.~A.~E.~Elsayed, A.~A.~Al-Obaidi, and H.~E.~Z.~Farag, ``Characterization of high-resolution AI data center training workloads on single and multiple GPU nodes,'' \emph{Scientific Data}, vol.~13, art.~1268, 2026, doi:10.1038/s41597-026-07496-6. Data: figshare, doi:10.6084/m9.figshare.31654879.
paper/template.tex:15:\title{Predict the Breach, Not the Drop:\\Control-Aligned Learning for Smoothing\\AI Training Power Swings}
paper/template.tex:24:Large AI training jobs can swing GPU power by tens of percent within a second, and synchronized jobs can
paper/template.tex:32:limiter armed now would be armed'', the same pipeline reaches <<abl_matched_aligned_ap>> (difference 95\% CI
paper/template.tex:35:validation for a 90\% removal target, the learned trigger removes <<t90_sb0_ml_aligned_cut>>\% of test
paper/template.tex:36:violations with the actuator engaged <<t90_sb0_ml_aligned_armed>>\% of the time, while rhythm replay meets
paper/template.tex:37:the target only by staying engaged <<t90_sb0_rhythm_aligned_armed>>\% of the time, i.e.\ effectively always on.
paper/template.tex:45:data centers, AI workloads, ramp rate, load forecasting, power smoothing, energy storage
paper/template.tex:55:predictors~\cite{lyu}; and AI data center load has been forecast at minute scales~\cite{mughees}. We are
paper/template.tex:84:2.8~kW divided by the node's rated GPU power), so a 10\%/s limit means the same fraction of rated power
paper/template.tex:88:same session and so are not independent. (The big-drop baselines from earlier work were early-stopped on all
paper/template.tex:94:91\% of Supercloud test seconds are labelled ``violation imminent''. We apply a 1~s trailing mean to
paper/template.tex:100:10\% of rated power per second; this is a normalized study threshold, not a specific utility requirement. A fill-type limiter adds
paper/template.tex:101:power only when the load falls faster than the limit allows, then tapers at 90\% of the allowed rate. A trigger
paper/template.tex:106:consisting of fill energy plus an assumed standby draw of 0--5\% of rated power while engaged; for
paper/template.tex:107:storage, this is absorbed charge before any later discharge or loss, which the simulation does not model. References: always-on, always-burn (a floor at 80\% of the trailing 60~s peak,
paper/template.tex:108:which removes only <<burn_cut>>\% of violations for <<burn_ovh>>\% extra energy) and an oracle that
paper/template.tex:112:The \emph{big-drop} target labels $t$ positive if a fall of more than 30\% of the recent peak within
paper/template.tex:116:Many violations (e.g.\ the 22\% square wave of Llama LoRA training) are not big drops, so the two
paper/template.tex:143:against <<abl_matched_aligned_ap>>, a paired cluster-bootstrap difference of <<abl_matched_diff>> (95\% CI
paper/template.tex:168:Fig.~\ref{fig:ready} sweeps each trigger's threshold (about 200 validation-score quantiles) on NLR test
paper/template.tex:173:To remove 90\% of violations, the control-aligned learned trigger needs <<an90_ml_aligned_armed>>\%
paper/template.tex:174:engaged time, whereas rhythm replay of the same target reaches 90\% only at <<an90_rhythm_aligned_armed>>\%,
paper/template.tex:176:<<an90_diff_vs_rhythm_aligned>> points (95\% CI <<an90_diff_vs_rhythm_aligned_lo>> to
paper/template.tex:177:<<an90_diff_vs_rhythm_aligned_hi>>), and <<an95_diff_vs_rhythm_aligned>> points at 95\% removal (CI
paper/template.tex:179:needs more engaged time than the control-aligned one (<<an90_ml_alarm_armed>>\% at 90\%; difference
paper/template.tex:180:<<an90_diff_vs_ml_alarm>> points, CI <<an90_diff_vs_ml_alarm_lo>> to <<an90_diff_vs_ml_alarm_hi>>). At 95\%
paper/template.tex:183:target's effect (AP <<abl_matched_drop_ap>> vs <<abl_matched_aligned_ap>>). The oracle removes all violations at <<oracle_armed>>\% engaged time, which bounds what
paper/template.tex:188:\caption{Engaged time (\% of time) needed to reach a violation-removal level, NLR test, 1~s latency.}
paper/template.tex:194:80\% & <<an80_ml_aligned_armed>> & <<an80_rhythm_aligned_armed>> & <<an80_ml_alarm_armed>>\\
paper/template.tex:195:90\% & <<an90_ml_aligned_armed>> & <<an90_rhythm_aligned_armed>> & <<an90_ml_alarm_armed>>\\
paper/template.tex:196:95\% & <<an95_ml_aligned_armed>> & <<an95_rhythm_aligned_armed>> & <<an95_ml_alarm_armed>>\\
paper/template.tex:209:With operating points chosen on validation and a standby draw of 2\% of rated power, a 90\% target
paper/template.tex:210:gives <<t90_sb2_ml_aligned_cut>>\% removal at <<t90_sb2_ml_aligned_armed>>\% engaged time and
paper/template.tex:211:a <<t90_sb2_ml_aligned_ovh>>\% energy metric for the learned trigger; rhythm replay meets the target only
paper/template.tex:212:by staying engaged <<t90_sb2_rhythm_aligned_armed>>\% of the time (<<t90_sb2_rhythm_aligned_ovh>>\%
paper/template.tex:213:energy metric, versus <<t90_sb2_always_on_ovh>>\% for always-on). At an 80\% target the validation-chosen
paper/template.tex:214:learned threshold undershoots on test (<<t80_sb2_ml_aligned_cut>>\% removal), a reminder that operating
paper/template.tex:218:Fig.~\ref{fig:forest} summarizes the learned-minus-rhythm AP difference. Trained on the test site's own
paper/template.tex:230:\caption{AP difference between the learned control-aligned trigger and rhythm replay, with 95\%
paper/template.tex:260:\emph{Power-system interpretation.} The 10\%/s threshold and idealized fill-only limiter define a
paper/template.tex:279:\section*{Acknowledgment}
paper/template.tex:280:Analysis code and text were drafted with the help of AI coding and writing assistants and independently
paper/template.tex:281:reviewed by a separate AI model. The author checked the results and is responsible for the content.
paper/template.tex:284:\bibitem{msft_stab} E.~Choukse, B.~Warrier, S.~Heath, et al., ``Power stabilization for AI training datacenters,'' arXiv:2508.14318, 2025.
paper/template.tex:286:\bibitem{activefilter} D.~Jensen, G.~Wilkins, O.~Nnorom~Jr., H.~Budd, P.~Levis, and J.~Rivas, ``Active filter design for buffering datacenter-scale power fluctuations from training AI,'' arXiv:2609.13490, 2026.
paper/template.tex:287:\bibitem{hessdpc} H.~You, C.~Lou, and J.~Yang, ``Source side mitigation of AI datacenter power fluctuations with a hybrid energy storage system and residual differentiable predictive control,'' arXiv:2606.04869, 2026.
paper/template.tex:288:\bibitem{lyu} X.~Lyu, W.~Du, S.~M.~Mohiuddin, and B.~A.~Ross, ``Communication delay robust control of BESS for AI training load smoothing,'' arXiv:2609.22542, 2026.
paper/template.tex:289:\bibitem{mughees} M.~Mughees, Y.~Li, Y.~Chen, and Y.~R.~Li, ``Short-term load forecasting for AI-data center,'' arXiv:2503.07756, 2025 (accepted to IEEE PES General Meeting 2025).
paper/template.tex:290:\bibitem{nlr} R.~Vercellino, J.~Willard, G.~Campos, W.~da~Silva~Pereira, O.~Hull, M.~Selensky, and J.~Mueller, ``Measurement of generative AI workload power profiles for whole-facility data center infrastructure planning,'' arXiv:2604.07345, 2026. Data: ``Dataset of Generative AI Workload Power Profiles,'' National Laboratory of the Rockies, doi:10.7799/3025227.
paper/template.tex:291:\bibitem{elsayed} A.~A.~E.~Elsayed, A.~A.~Al-Obaidi, and H.~E.~Z.~Farag, ``Characterization of high-resolution AI data center training workloads on single and multiple GPU nodes,'' \emph{Scientific Data}, vol.~13, art.~1268, 2026, doi:10.1038/s41597-026-07496-6. Data: figshare, doi:10.6084/m9.figshare.31654879.
CreationDate:    Mon Nov  9 18:20:58 2026 EST
Pages:           4
Page size:       612 x 792 pts (letter)

codex
The requested edits are present in both the template and rendered TeX, and the current PDF is still four pages. I’m now checking the exact surrounding prose, references, logs, and regeneration path for subtle inconsistencies introduced by the revisions.
exec
/bin/zsh -lc "sed -n '1,320p' paper/main.tex; rg -n \"template\\.tex|main\\.tex|latexmk|pdflatex|render|generate\" Makefile paper scripts README* 2>/dev/null | head -200; find paper -maxdepth 1 -type f -name '*.log' -o -name '*.aux' -o -name '*.out' | sort; if test -f paper/main.log; then rg -n \"Warning|Overfull|Underfull|undefined|multiply defined|Error\" paper/main.log; fi; git status --short" in /Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing
 succeeded in 0ms:
\documentclass[conference]{IEEEtran}
\usepackage{iftex}
\ifXeTeX
  \usepackage{fontspec}
  \setmainfont{texgyretermes}[Extension=.otf,UprightFont=*-regular,BoldFont=*-bold,ItalicFont=*-italic,BoldItalicFont=*-bolditalic]
\fi
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{booktabs}
\usepackage{url}
\usepackage[hidelinks]{hyperref}

\begin{document}

\title{Predict the Breach, Not the Drop:\\Control-Aligned Learning for Smoothing\\AI Training Power Swings}

\author{\IEEEauthorblockN{Sayed Raheel}
\IEEEauthorblockA{Independent Researcher; Yeshiva University alumnus\\
\texttt{shussai1@mail.yu.edu}}}

\maketitle

\begin{abstract}
Large AI training jobs can swing GPU power by tens of percent within a second, and synchronized jobs can
create fast load ramps of concern at large grid-connected facilities. In an idealized simulation,
fill-type smoothing, using filler GPU work or storage, can reduce violations of an illustrative ramp
threshold, but it must be engaged before the fall and keeping it engaged has a cost.
Forecasting can decide when to engage it. We find that the choice of training target matters
substantially. In a matched-pipeline ablation, a gradient-boosted classifier trained on the usual target,
``a large power drop is coming'', ranks the violations a ramp limiter must catch poorly (average precision
0.58). Trained on the controller's own event, ``a ramp-limit violation will occur while a
limiter armed now would be armed'', the same pipeline reaches 0.96 (difference 95\% CI
0.28 to 0.49) on held-out H100 training and inference
traces, against 0.67 for no-learning rhythm replay of the same target. With a threshold chosen on
validation for a 90\% removal target, the learned trigger removes 86.8\% of test
violations with the actuator engaged 45.6\% of the time, while rhythm replay meets
the target only by staying engaged 99.2\% of the time, i.e.\ effectively always on.
Across three public datasets covering H100, B200 and V100 nodes and both benchmark and labelled cluster jobs,
the learned trigger has significantly higher AP than rhythm replay on two datasets when that site is in the
training data, after harmonizing sensor averaging; the third is inconclusive. Transfer to an unseen
site is unreliable, which we report as an open problem.
\end{abstract}

\begin{IEEEkeywords}
data centers, AI workloads, ramp rate, load forecasting, power smoothing, energy storage
\end{IEEEkeywords}

\section{Introduction}
Training a large model alternates compute-heavy and communication-heavy phases, so GPU power moves in
fast, large steps. Because all nodes of a job step together, a synchronized job appears to the grid as
one large swing; industry reports describe swings of tens to hundreds of megawatts and evaluate software
power burning, GPU power floors and rack storage as mitigations~\cite{msft_stab}. Hardware filters and
storage that react to the measured load are being developed~\cite{easyrider,activefilter}; predictive
storage control has been studied with perfect preview~\cite{hessdpc} and with short delay-compensating
predictors~\cite{lyu}; and AI data center load has been forecast at minute scales~\cite{mughees}. We are
not aware of work that studies how the forecasting target affects smoothing performance.

A fill-type actuator must be engaged before the fall arrives, but engagement costs energy and readiness
(a hot inverter, pre-warmed filler kernels). A forecaster can engage the actuator only when needed. The
obvious competitor is free: training power is periodic, so ``replay the last cycle'' is a strong
predictor. Our contributions:
\begin{itemize}
\item A control-aligned prediction target: a ramp-limit violation that falls entirely inside the window
a limiter armed now would cover, instead of a generic ``large drop''.
\item A readiness analysis (violations removed versus time engaged) comparing learned triggers, rhythm
replay, an always-on limiter and a perfect-foresight oracle in one simulator.
\item A three-dataset study (H100, B200, V100; benchmarks and labelled cluster jobs) with job-clustered confidence
intervals, a sensor-harmonization step, and a negative result on unseen sites.
\end{itemize}

\section{Data}
\textbf{NLR}~\cite{nlr}: 4$\times$H100 nodes running MLPerf Llama2-70B LoRA and Stable Diffusion
training on 1--16 nodes, plus three vLLM Llama3.1-70B inference benchmarks, NVML power at 5--10~Hz,
248 node-hours (at most four nodes per job, which run nearly in lockstep, are kept; all
are weighted equally in metrics). Training jobs are split whole into train, validation and test; each
inference benchmark is a single continuous session split in time, so its test portion counts as one
independent unit. \textbf{Elsayed et al.}~\cite{elsayed}: single 8$\times$H100 and 8$\times$B200 nodes
running diffusion and Llama 1B--8B fine-tuning sweeps, 15-minute sessions, 32 unique
sessions. \textbf{MIT Supercloud}~\cite{supercloud}: a stratified subset of 560 labelled jobs (80 per
model class: VGG, ResNet, Inception, U-Net, BERT, DistilBERT, GNN) on nodes with one or two V100s,
nvidia-smi at 10~Hz, 1,292 node-hours of labelled cluster jobs.

All traces are averaged onto a 0.2~s grid and expressed as ``NLR-equivalent watts'' (power $\times$
2.8~kW divided by the node's rated GPU power), so a 10\%/s limit means the same fraction of rated power
everywhere. Jobs are assigned whole to train, validation and test (about 60/20/20). For the
control-aligned models, validation units are split into two halves, one for early stopping and one for
choosing operating points; for NLR inference the validation halves are alternate hour blocks of the
same session and so are not independent. (The big-drop baselines from earlier work were early-stopped on all
validation units.)

\textbf{Sensor harmonization.} NVML documents that on recent architectures the default power reading is
averaged over about 1~s, while older GPUs such as the V100 report instantaneous power~\cite{nvml}. The NLR
documentation does not state which reading was logged. Raw V100 traces flicker: without harmonization,
91\% of Supercloud test seconds are labelled ``violation imminent''. We apply a 1~s trailing mean to
Supercloud so that all three datasets are compared at similar effective bandwidth.

\section{Problem and methods}
\subsection{Ramp limit, limiter and readiness}
For this study, a violation starts when the node's 1~s down-ramp exceeds an illustrative threshold of
10\% of rated power per second; this is a normalized study threshold, not a specific utility requirement. A fill-type limiter adds
power only when the load falls faster than the limit allows, then tapers at 90\% of the allowed rate. A trigger
issued at row $t$ acts one sample later (each row averages $[t, t{+}0.2\,\mathrm{s})$), engages the
limiter after an actuator latency $L$ (1~s unless stated) and arms it for 6~s; the limiter keeps
filling until it meets the load. We count as \emph{engaged} every sample where the limiter is armed or
still filling, and report violations removed against engaged time. We also report an energy metric
consisting of fill energy plus an assumed standby draw of 0--5\% of rated power while engaged; for
storage, this is absorbed charge before any later discharge or loss, which the simulation does not model. References: always-on, always-burn (a floor at 80\% of the trailing 60~s peak,
which removes only 6.7\% of violations for 6.8\% extra energy) and an oracle that
arms just in time for every violation, including those induced by the limiter itself.

\subsection{Targets}
The \emph{big-drop} target labels $t$ positive if a fall of more than 30\% of the recent peak within
1~s starts in the next 5~s. The \emph{control-aligned} target labels $t$ positive if the whole 1~s ramp window
of a raw violation lies inside the 6~s window during which a trigger at $t$ keeps the limiter armed, so
the limiter is armed throughout that fall. Violations induced by the limiter itself are not labelled.
Many violations (e.g.\ the 22\% square wave of Llama LoRA training) are not big drops, so the two
targets differ substantially.

\subsection{Predictors}
\emph{Rhythm replay} estimates the period $P$ from a trailing 120~s autocorrelation, predicts
$\hat p(t+k)=p(t+k-P\lceil k/P\rceil)$, and scores the largest predicted 1~s down-ramp inside the
target window; it needs no training. The \emph{learned} predictor is LightGBM~\cite{lightgbm} on 56 trailing features
(lags, differences, rolling statistics, time since recent steps and drops, rhythm period, phase and
rhythm forecasts), one model per actuator latency. The big-drop model in the readiness comparison is an
earlier configuration with different leaf-size and early-stopping choices, so that comparison does not
isolate the label alone; the matched ablation does. A shape-only variant divides every level feature by
the trailing 60~s maximum.

\subsection{Evaluation}
Ranking quality is average precision (AP) on test rows. Uncertainty is a paired bootstrap over
independent clusters (training jobs, or inference sessions; 1000 resamples). Operating points are chosen
on the validation threshold half and scored on test. All intervals are conditional on the single fitted
model and split: they resample test clusters but do not retrain. Cross-dataset comparisons score one
decision per second; the NLR readiness analysis scores every 0.2~s row.

\section{Results}
\subsection{Training target}
On NLR test traces, rhythm replay ranks the control-aligned event with AP 0.67; LightGBM trained
on the control-aligned target reaches 0.96, and the gain holds for each workload (Table~\ref{tab:wl}).
\emph{Matched label ablation.} Training the big-drop label through the same pipeline (same rows, features,
LightGBM settings, early-stopping data and metric, and square-root class-weighting rule, which gives weight
1.75 for the aligned and 2.57 for the big-drop target) yields AP 0.58 on the aligned event
against 0.96, a paired cluster-bootstrap difference of 0.37 (95\% CI
0.28 to 0.49, 12 clusters). The big-drop model is good at its own task
(AP 0.93 on the big-drop event, where the aligned model reaches
0.48): the two labels describe different events.
Results are stable across actuator latencies (AP 0.96 at 0~s, 0.95
at 3~s; rhythm replay 0.68 and 0.67).

\begin{table}[t]
\centering
\caption{NLR test AP on the control-aligned target (1~s latency).}
\label{tab:wl}
\begin{tabular}{lcc}
\toprule
Workload & Learned & Rhythm replay\\
\midrule
Llama2-70B LoRA training & 1.00 & 0.81\\
Stable Diffusion training & 0.96 & 0.73\\
Offline inference & 0.55 & 0.29\\
Online inference, finite & 0.76 & 0.09\\
Online inference, fixed rate & 0.65 & 0.36\\
\bottomrule
\end{tabular}
\end{table}

\subsection{Readiness}
Fig.~\ref{fig:ready} sweeps each trigger's threshold (about 200 validation-score quantiles) on NLR test
traces. Every trigger can reach high removal by staying engaged long enough; what differs is the engaged
time needed (Table~\ref{tab:arm}). Table~\ref{tab:arm} reads the best threshold off each test curve, so
it is a retrospective comparison of attainable trade-offs, not a deployable operating point; the
validation-chosen operating points follow below.
To remove 90\% of violations, the control-aligned learned trigger needs 48.4\%
engaged time, whereas rhythm replay of the same target reaches 90\% only at 99.2\%,
i.e.\ it is no better than always-on. The paired cluster-bootstrap difference is
$-$50.8 points (95\% CI $-$57.4 to
$-$8.8), and $-$40.8 points at 95\% removal (CI
$-$49.1 to $-$31.4). The earlier configured big-drop trigger
needs more engaged time than the control-aligned one (64.3\% at 90\%; difference
$-$15.9 points, CI $-$25.7 to $-$3.9). At 95\%
removal the interval includes zero (CI $-$26.3 to 0.5), so with
12 test clusters and non-identical configurations, the matched ablation is the cleaner evidence for the
target's effect (AP 0.58 vs 0.96). The oracle removes all violations at 29.8\% engaged time, which bounds what
better prediction could still gain.

\begin{table}[t]
\centering
\caption{Engaged time (\% of time) needed to reach a violation-removal level, NLR test, 1~s latency.}
\label{tab:arm}
\begin{tabular}{lccc}
\toprule
Removal & Learned, aligned & Rhythm, aligned & Learned, big-drop\\
\midrule
80\% & 43.1 & 51.5 & 53.0\\
90\% & 48.4 & 99.2 & 64.3\\
95\% & 58.4 & 99.2 & 74.8\\
\bottomrule
\end{tabular}
\end{table}

\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{fig_readiness.pdf}
\caption{Violations removed versus engaged time on NLR test traces (1~s latency, dense threshold sweep).
Always-on removes everything but is always engaged.}
\label{fig:ready}
\end{figure}

With operating points chosen on validation and a standby draw of 2\% of rated power, a 90\% target
gives 86.8\% removal at 45.6\% engaged time and
a 3.7\% energy metric for the learned trigger; rhythm replay meets the target only
by staying engaged 99.2\% of the time (5.4\%
energy metric, versus 5.4\% for always-on). At an 80\% target the validation-chosen
learned threshold undershoots on test (73.7\% removal), a reminder that operating
points chosen on few validation jobs transfer imperfectly.

\subsection{Across sites and GPUs}
Fig.~\ref{fig:forest} summarizes the learned-minus-rhythm AP difference. Trained on the test site's own
training jobs (in-domain) or on all three datasets (pooled), the learned trigger significantly beats
rhythm replay on NLR (pooled AP 0.96 vs 0.67) and on labelled Supercloud jobs
(pooled 0.88 vs 0.74; exploratory per-class intervals, without multiplicity correction, are
positive for 7 of 7 model classes). On Elsayed the point estimate favours learning
(0.92 vs 0.88) but the interval includes zero with six test
sessions, and rhythm replay is better on its diffusion sessions; we hypothesize that their very regular
cadence suits replay, but two test sessions do not allow a firm conclusion.

\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{fig_forest.pdf}
\caption{AP difference between the learned control-aligned trigger and rhythm replay, with 95\%
cluster-bootstrap intervals. Red: learned significantly better; blue: rhythm significantly better;
grey: inconclusive. Unseen-site rows use shape-only features.}
\label{fig:forest}
\end{figure}

\subsection{Unseen sites}
When the test dataset is excluded from training, the learned trigger is not better than rhythm replay
anywhere. With shape-only features it reaches AP 0.65 on NLR (rhythm
0.67, CI of difference $-$0.06 to 0.02),
0.85 on Elsayed (rhythm 0.88), and
0.66 on Supercloud, significantly below rhythm replay
(0.74; CI $-$0.12 to $-$0.04).
Continuing to train on 60 minutes of the new site's data (mean of five independent draws) gives
0.71 on NLR (range 0.62 to
0.77) and 0.64 on Supercloud (range
0.58 to 0.69), so a short
calibration period does not reliably recover the in-domain advantage. Rhythm replay needs no site data;
in our experiments a learned trigger needed the site in its training set.

\section{Discussion and limitations}
\emph{Sensors.} If NLR and Elsayed power is NVML's 1~s average, true ramps are faster than measured and
measured lead times are optimistic. \emph{Simulation.} The actuator is an idealized limiter with fixed
latency, hold time and standby draw; storage capacity, state of charge, efficiency and wear are not modelled, and standby cost is an
assumed fraction of rated power.
\emph{Workloads.} NLR and Elsayed are scripted benchmarks; NLR inference falls are dominated by gaps
between benchmark runs, and each NLR inference workload is a single session. Supercloud adds
scheduler-observed labelled jobs on older V100 nodes. \emph{Scale.} Results are per node; synchronized multi-node jobs scale the same
swing, while desynchronized jobs partly cancel. \emph{Licences.} Supercloud is CC BY-NC-ND and the Elsayed
archive README states CC BY-NC-ND; both were used for research only and are not redistributed.
\emph{Power-system interpretation.} The 10\%/s threshold and idealized fill-only limiter define a
comparative forecasting experiment, not a complete storage design. Engaged time is a readiness metric,
not an energy-capacity or converter-rating requirement. A deployable design must also size charge and
discharge power, usable energy, state-of-charge margin and thermal headroom from the facility-level load
trace, and account for efficiency, recovery after an event, simultaneous jobs and the applicable
interconnection ramp requirement. The results show when a predictive controller would request readiness
under the stated simulator, not compliance by a particular storage installation.

\section{Conclusion}
In our NLR experiments, training on the controller's event, a ramp-limit violation inside the actuator's
engagement window, ranked relevant events substantially better than training the same pipeline on a
generic large-drop label. With that target a small gradient-boosted model needs substantially less engaged time than rhythm replay for
the same violation removal on H100 benchmark traces, and ranks violations better (higher AP) on labelled
V100 cluster jobs, provided the site is represented in training. Closing the gap to the oracle and making learned triggers transfer to
new sites are the natural next steps.

\section*{Code availability}
Code is available from the author on request; the datasets are public from their original sources.

\section*{Acknowledgment}
Analysis code and text were drafted with the help of AI coding and writing assistants and independently
reviewed by a separate AI model. The author checked the results and is responsible for the content.

\begin{thebibliography}{99}
\bibitem{msft_stab} E.~Choukse, B.~Warrier, S.~Heath, et al., ``Power stabilization for AI training datacenters,'' arXiv:2508.14318, 2025.
\bibitem{easyrider} D.~Jensen, G.~Wilkins, O.~Nnorom~Jr., H.~Budd, R.~Rajagopal, J.~Rivas-Davila, and P.~Levis, ``EasyRider: Mitigating power transients in datacenter-scale training workloads,'' arXiv:2604.15522, 2026.
\bibitem{activefilter} D.~Jensen, G.~Wilkins, O.~Nnorom~Jr., H.~Budd, P.~Levis, and J.~Rivas, ``Active filter design for buffering datacenter-scale power fluctuations from training AI,'' arXiv:2609.13490, 2026.
\bibitem{hessdpc} H.~You, C.~Lou, and J.~Yang, ``Source side mitigation of AI datacenter power fluctuations with a hybrid energy storage system and residual differentiable predictive control,'' arXiv:2606.04869, 2026.
\bibitem{lyu} X.~Lyu, W.~Du, S.~M.~Mohiuddin, and B.~A.~Ross, ``Communication delay robust control of BESS for AI training load smoothing,'' arXiv:2609.22542, 2026.
\bibitem{mughees} M.~Mughees, Y.~Li, Y.~Chen, and Y.~R.~Li, ``Short-term load forecasting for AI-data center,'' arXiv:2503.07756, 2025 (accepted to IEEE PES General Meeting 2025).
\bibitem{nlr} R.~Vercellino, J.~Willard, G.~Campos, W.~da~Silva~Pereira, O.~Hull, M.~Selensky, and J.~Mueller, ``Measurement of generative AI workload power profiles for whole-facility data center infrastructure planning,'' arXiv:2604.07345, 2026. Data: ``Dataset of Generative AI Workload Power Profiles,'' National Laboratory of the Rockies, doi:10.7799/3025227.
\bibitem{elsayed} A.~A.~E.~Elsayed, A.~A.~Al-Obaidi, and H.~E.~Z.~Farag, ``Characterization of high-resolution AI data center training workloads on single and multiple GPU nodes,'' \emph{Scientific Data}, vol.~13, art.~1268, 2026, doi:10.1038/s41597-026-07496-6. Data: figshare, doi:10.6084/m9.figshare.31654879.
\bibitem{supercloud} S.~Samsi, M.~L.~Weiss, D.~Bestor, et al., ``The MIT Supercloud dataset,'' in \emph{Proc. IEEE High Performance Extreme Computing Conf. (HPEC)}, 2021, pp.~1--8, doi:10.1109/HPEC49654.2021.9622850.
\bibitem{lightgbm} G.~Ke, Q.~Meng, T.~Finley, et al., ``LightGBM: A highly efficient gradient boosting decision tree,'' in \emph{Advances in Neural Information Processing Systems}, vol.~30, 2017.
\bibitem{nvml} NVIDIA, ``NVML API reference guide: Device queries,'' 2026. [Online]. Available: \url{https://docs.nvidia.com/deploy/nvml-api/latest/api/group__nvmlDeviceQueries.html}
\end{thebibliography}

\end{document}
README.md:50:  make_notebooks.py       regenerates the notebooks
README.md:77:.venv/bin/python -m src.report                # regenerate results.md + slide from saved tables
paper/PESGM2027_SUBMISSION.md:13:- PDF to upload: `paper/main.pdf` (rebuild: `.venv/bin/python -m src.paper && cd paper && rm -f main.pdf && tectonic -X compile main.tex`).
paper/arxiv/main.tex:537:obtain them from the original sources. The reported model and controller metrics are generated from result tables written by the analysis
paper/arxiv/template.tex:537:obtain them from the original sources. The reported model and controller metrics are generated from result tables written by the analysis
paper/build.log
paper/main.log
19:LaTeX Font Warning: Font shape `TU/ptm/m/n' undefined
30:LaTeX Font Warning: Font shape `TU/ptm/bx/n' undefined
34:LaTeX Font Warning: Font shape `TU/ptm/m/it' undefined
38:LaTeX Font Warning: Font shape `TU/ptm/bx/it' undefined
462:Underfull \hbox (badness 1824) in paragraph at lines 49--57
476:Underfull \hbox (badness 1661) in paragraph at lines 290--291
482:Underfull \hbox (badness 3088) in paragraph at lines 290--291
488:Underfull \hbox (badness 1742) in paragraph at lines 291--292
494:Underfull \hbox (badness 3088) in paragraph at lines 291--292
500:Underfull \hbox (badness 2970) in paragraph at lines 291--292
506:Underfull \hbox (badness 2707) in paragraph at lines 294--295
526:LaTeX Font Warning: Some font shapes were not available, defaults substituted.
 M paper/arxiv/fig_example.pdf
 M paper/arxiv/fig_forest.pdf
 M paper/arxiv/fig_readiness.pdf
 M paper/fig_example.pdf
 M paper/fig_forest.pdf
 M paper/fig_readiness.pdf
 M paper/main.pdf
 M paper/main.tex
 M paper/template.tex
?? paper/PESGM2027_SUBMISSION.md
?? reports/review/pesgm_codex_r1_2026-11-09.md
?? reports/review/pesgm_codex_r2_2026-11-09.md

codex
The checked-in build log has only font-substitution and underfull-box warnings, with no overfull boxes or unresolved references. The workspace is read-only, so an isolated rebuild cannot create temporary output here; I’m validating the existing PDF and log timestamps and source-to-render consistency instead.
exec
/bin/zsh -lc "tail -80 paper/build.log; tail -50 paper/main.log; stat -f '%N %Sm %z' -t '%Y-%m-%d %H:%M:%S %Z' paper/template.tex paper/main.tex paper/main.pdf paper/build.log paper/main.log; cmp -s paper/template.tex paper/main.tex; echo CMP_EXIT="'$?; rg -n "undefined references|undefined citations|There were undefined|Rerun to get|Overfull|Emergency stop|Fatal error" paper/build.log paper/main.log || true; pdftotext -layout paper/main.pdf - | tail -100' in /Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing
 succeeded in 0ms:
note: "version 2" Tectonic command-line interface activated
note: Running TeX ...
warning: main.tex:55: Underfull \hbox (badness 1824) in paragraph at lines 47--55
warning: main.tex:238: Underfull \vbox (badness 10000) has occurred while \output is active
warning: main.tex:255: Underfull \hbox (badness 4429) in paragraph at lines 254--255
note: Rerunning TeX because "main.out" changed ...
warning: main.tex:55: Underfull \hbox (badness 1824) in paragraph at lines 47--55
warning: main.tex:238: Underfull \vbox (badness 10000) has occurred while \output is active
warning: main.tex:255: Underfull \hbox (badness 4429) in paragraph at lines 254--255
warning: warnings were issued by the TeX engine; use --print and/or --keep-logs for details.
note: Running xdvipdfmx ...
note: Writing `main.pdf` (79.4990234375 KiB)
note: Skipped writing 2 intermediate files (use --keep-intermediates to keep them)
Underfull \hbox (badness 3088) in paragraph at lines 290--291
\TU/texgyretermes(0)/m/n/8 Workload Power Profiles,” National Laboratory of the
 Rockies,
 []


Underfull \hbox (badness 1742) in paragraph at lines 291--292
\TU/texgyretermes(0)/m/n/8 acterization of high-resolution AI data center train
ing workloads
 []


Underfull \hbox (badness 3088) in paragraph at lines 291--292
\TU/texgyretermes(0)/m/n/8 on single and multiple GPU nodes,” \TU/texgyretermes
(0)/m/it/8 Scientific Data\TU/texgyretermes(0)/m/n/8 , vol. 13,
 []


Underfull \hbox (badness 2970) in paragraph at lines 291--292
\TU/texgyretermes(0)/m/n/8 art. 1268, 2026, doi:10.1038/s41597-026-07496-6. Dat
a: figshare,
 []


Underfull \hbox (badness 2707) in paragraph at lines 294--295
[]\TU/texgyretermes(0)/m/n/8 NVIDIA, “NVML API reference guide: Device queries,
” 2026.
 []


** Conference Paper **
Before submitting the final camera ready copy, remember to:

 1. Manually equalize the lengths of two columns on the last page
 of your paper;

 2. Ensure that any PostScript and/or PDF output post-processing
 uses only Type 1 fonts and that every step in the generation
 process uses the appropriate paper size.

[4

] (main.aux)

LaTeX Font Warning: Some font shapes were not available, defaults substituted.

Package rerunfilecheck Info: File `main.out' has not changed.
(rerunfilecheck)             Checksum: B7BD05C0B68B51DC37ED92CACF108E13;1828.
 )
Output written on main.xdv (4 pages, 188432 bytes).
paper/template.tex 2026-11-09 18:20:48 EST 22135
paper/main.tex 2026-11-09 18:20:58 EST 20122
paper/main.pdf 2026-11-09 18:20:59 EST 91253
paper/build.log 2026-10-12 22:59:03 EDT 900
paper/main.log 2026-11-09 18:20:59 EST 19874
CMP_EXIT=1
latency, dense threshold sweep). Always-on removes everything but is always
                                                                                                   on NLR (range 0.62 to 0.77) and 0.64 on Supercloud (range
engaged.                                                                                           0.58 to 0.69), so a short calibration period does not reliably
                                                                                                   recover the in-domain advantage. Rhythm replay needs no site
                                                                                                   data; in our experiments a learned trigger needed the site in
vs 0.96). The oracle removes all violations at 29.8% engaged                                       its training set.
time, which bounds what better prediction could still gain.
   With operating points chosen on validation and a standby                                                            V. DISCUSSION AND LIMITATIONS
draw of 2% of rated power, a 90% target gives 86.8% removal
                                                                                                      Sensors. If NLR and Elsayed power is NVML’s 1 s average,
at 45.6% engaged time and a 3.7% energy metric for the
                                                                                                   true ramps are faster than measured and measured lead times
learned trigger; rhythm replay meets the target only by staying
                                                                                                   are optimistic. Simulation. The actuator is an idealized limiter
engaged 99.2% of the time (5.4% energy metric, versus 5.4%
                                                                                                   with fixed latency, hold time and standby draw; storage ca-
for always-on). At an 80% target the validation-chosen learned
                                                                                                   pacity, state of charge, eﬀiciency and wear are not modelled,
threshold undershoots on test (73.7% removal), a reminder
                                                                                                   and standby cost is an assumed fraction of rated power.
that operating points chosen on few validation jobs transfer
                                                                                                   Workloads. NLR and Elsayed are scripted benchmarks; NLR
imperfectly.
                                                                                                   inference falls are dominated by gaps between benchmark
C. Across sites and GPUs                                                                           runs, and each NLR inference workload is a single session.
   Fig. 2 summarizes the learned-minus-rhythm AP difference.                                       Supercloud adds scheduler-observed labelled jobs on older
Trained on the test site’s own training jobs (in-domain) or                                        V100 nodes. Scale. Results are per node; synchronized multi-
on all three datasets (pooled), the learned trigger significantly                                  node jobs scale the same swing, while desynchronized jobs
beats rhythm replay on NLR (pooled AP 0.96 vs 0.67) and on                                         partly cancel. Licences. Supercloud is CC BY-NC-ND and
labelled Supercloud jobs (pooled 0.88 vs 0.74; exploratory per-                                    the Elsayed archive README states CC BY-NC-ND; both
class intervals, without multiplicity correction, are positive for                                 were used for research only and are not redistributed. Power-
7 of 7 model classes). On Elsayed the point estimate favours                                       system interpretation. The 10%/s threshold and idealized fill-
learning (0.92 vs 0.88) but the interval includes zero with                                        only limiter define a comparative forecasting experiment, not
six test sessions, and rhythm replay is better on its diffusion                                    a complete storage design. Engaged time is a readiness metric,
sessions; we hypothesize that their very regular cadence suits                                     not an energy-capacity or converter-rating requirement. A
replay, but two test sessions do not allow a firm conclusion.                                      deployable design must also size charge and discharge power,
                                                                                                   usable energy, state-of-charge margin and thermal headroom
D. Unseen sites                                                                                    from the facility-level load trace, and account for eﬀiciency,
   When the test dataset is excluded from training, the learned                                    recovery after an event, simultaneous jobs and the applicable
trigger is not better than rhythm replay anywhere. With shape-                                     interconnection ramp requirement. The results show when a
predictive controller would request readiness under the stated
simulator, not compliance by a particular storage installation.
                           VI. CONCLUSION
   In our NLR experiments, training on the controller’s event, a
ramp-limit violation inside the actuator’s engagement window,
ranked relevant events substantially better than training the
same pipeline on a generic large-drop label. With that target a
small gradient-boosted model needs substantially less engaged
time than rhythm replay for the same violation removal on
H100 benchmark traces, and ranks violations better (higher
AP) on labelled V100 cluster jobs, provided the site is repre-
sented in training. Closing the gap to the oracle and making
learned triggers transfer to new sites are the natural next steps.
                          CODE AVAILABILITY
   Code is available from the author on request; the datasets
are public from their original sources.
                          ACKNOWLEDGMENT
   Analysis code and text were drafted with the help of AI
coding and writing assistants and independently reviewed by
a separate AI model. The author checked the results and is
responsible for the content.
                              REFERENCES
 [1] E. Choukse, B. Warrier, S. Heath, et al., “Power stabilization for AI
     training datacenters,” arXiv:2508.14318, 2025.
 [2] D. Jensen, G. Wilkins, O. Nnorom Jr., H. Budd, R. Rajagopal,
     J. Rivas-Davila, and P. Levis, “EasyRider: Mitigating power transients
     in datacenter-scale training workloads,” arXiv:2604.15522, 2026.
 [3] D. Jensen, G. Wilkins, O. Nnorom Jr., H. Budd, P. Levis, and J. Rivas,
     “Active filter design for buffering datacenter-scale power fluctuations
     from training AI,” arXiv:2609.13490, 2026.
 [4] H. You, C. Lou, and J. Yang, “Source side mitigation of AI datacenter
     power fluctuations with a hybrid energy storage system and residual
     differentiable predictive control,” arXiv:2606.04869, 2026.
 [5] X. Lyu, W. Du, S. M. Mohiuddin, and B. A. Ross, “Communica-
     tion delay robust control of BESS for AI training load smoothing,”
     arXiv:2609.22542, 2026.
 [6] M. Mughees, Y. Li, Y. Chen, and Y. R. Li, “Short-term load forecasting
     for AI-data center,” arXiv:2503.07756, 2025 (accepted to IEEE PES
     General Meeting 2025).
 [7] R. Vercellino, J. Willard, G. Campos, W. da Silva Pereira, O. Hull,
     M. Selensky, and J. Mueller, “Measurement of generative AI work-
     load power profiles for whole-facility data center infrastructure plan-
     ning,” arXiv:2604.07345, 2026. Data: “Dataset of Generative AI
     Workload Power Profiles,” National Laboratory of the Rockies,
     doi:10.7799/3025227.
 [8] A. A. E. Elsayed, A. A. Al-Obaidi, and H. E. Z. Farag, “Char-
     acterization of high-resolution AI data center training workloads
     on single and multiple GPU nodes,” Scientific Data, vol. 13,
     art. 1268, 2026, doi:10.1038/s41597-026-07496-6. Data: figshare,
     doi:10.6084/m9.figshare.31654879.
 [9] S. Samsi, M. L. Weiss, D. Bestor, et al., “The MIT Supercloud dataset,”
     in Proc. IEEE High Performance Extreme Computing Conf. (HPEC),
     2021, pp. 1–8, doi:10.1109/HPEC49654.2021.9622850.
[10] G. Ke, Q. Meng, T. Finley, et al., “LightGBM: A highly eﬀicient gradient
     boosting decision tree,” in Advances in Neural Information Processing
     Systems, vol. 30, 2017.
[11] NVIDIA, “NVML API reference guide: Device queries,” 2026.
     [Online]. Available: https://docs.nvidia.com/deploy/nvml-api/latest/api/
     group__nvmlDeviceQueries.html

codex
# Verdict: READY AFTER FIXES

1. Author affiliation remains unresolved.

Replace:

```tex
\author{\IEEEauthorblockN{Sayed Raheel}
\IEEEauthorblockA{Independent Researcher; Yeshiva University alumnus\\
\texttt{shussai1@mail.yu.edu}}}
```

with:

```tex
\author{\IEEEauthorblockN{Sayed Raheel}
\IEEEauthorblockA{Independent Researcher, New York, NY, USA\\
\texttt{shussai1@mail.yu.edu}}}
```

Confirm that use of the university email is permitted and that the submission-system author record matches the PDF exactly.
tokens used
22,255
# Verdict: READY AFTER FIXES

1. Author affiliation remains unresolved.

Replace:

```tex
\author{\IEEEauthorblockN{Sayed Raheel}
\IEEEauthorblockA{Independent Researcher; Yeshiva University alumnus\\
\texttt{shussai1@mail.yu.edu}}}
```

with:

```tex
\author{\IEEEauthorblockN{Sayed Raheel}
\IEEEauthorblockA{Independent Researcher, New York, NY, USA\\
\texttt{shussai1@mail.yu.edu}}}
```

Confirm that use of the university email is permitted and that the submission-system author record matches the PDF exactly.
