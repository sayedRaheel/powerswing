# Final peer review — Round 3

The round-2 implementation fixes are largely correct, and I found no discrepancies among the 268 generated values in `paper/numbers.json`, their source tables, and `paper/main.tex`. The PDF also matches the generated TeX. The remaining blocking issue is how the headline readiness result is selected and described: 48.4% versus 99.2% is a retrospective test-frontier statistic, not a validation-selected deployable operating point.

## Verification of round-2 fixes

1. **PASS — half-open arm window.**  
   [`_arm`](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/regime.py:82>) implements
   \[
   [\text{trigger}+\text{lat},\ \text{trigger}+\text{lat}+\text{hold})
   \]
   exactly. With 6 s at 5 Hz, a trigger arms 30 samples, not 31. The simulation uses this function consistently at [src/regime.py:222](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/regime.py:222>) and [src/regime.py:244](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/regime.py:244>).

2. **PASS — aligned label, rhythm score, latency, and off-by-one convention.**  
   [`lat_samples`](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/aligned.py:39>) adds the one-sample decision delay. For \(L=1\) s, engagement begins six samples after the feature row: five latency samples plus one completed-bin delay.  
   [`aligned_labels`](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/aligned.py:76>) uses
   \[
   v\in[e+FS,\ e+\text{hold}-1],
   \]
   and [`rhythm_aligned_score`](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/aligned.py:90>) evaluates exactly the same offsets through `range(lat + FS, lat + w)`. This is consistent with the declared endpoint-containment semantics and the simulator’s half-open window.

3. **PASS in substance — dense L=1 grid and `armed_needed`.**  
   Dense validation-score quantiles are constructed at [src/regime.py:181](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/regime.py:181>), substituted only at the headline 1 s latency at [src/regime.py:242](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/regime.py:242>), and consumed by [`armed_needed`](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/regime.py:406>).  
   Literal wording caveat: the code uses 200 linear quantiles plus ten extreme-tail quantiles, yielding 209 unique thresholds for the continuous learned scores, not exactly 200. Thus [paper/main.tex:152](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:152>) should say “about 200” or “209 validation-score thresholds.”

4. **PASS — bootstrap, transfer columns, and forest labels.**  
   Whole-dataset and subgroup bootstraps are both configured for 1000 draws at [src/crossdata.py:39](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/crossdata.py:39>) and used for workload subgroups at [src/crossdata.py:211](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/crossdata.py:211>).  
   Adaptation rows correctly distinguish draw-0 quantities from the five-draw mean/range at [src/transfer.py:121](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/transfer.py:121>); the paper generator uses `ap_ml_rep_mean/min/max`, not `draw0_*`, at [src/paper.py:93](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/paper.py:93>). The forest plot distinguishes in-domain, pooled, and unseen-site rows at [src/paper.py:155](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/paper.py:155>).

## Critical

- **The abstract’s central 48.4% versus 99.2% result is selected using test outcomes, contrary to the methods statement.**  
  [`armed_needed`](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/regime.py:406>) searches each strategy’s test curve and takes the minimum test engaged time satisfying the target at lines 417–425. It repeats that selection inside every test bootstrap. These are the values presented as the principal result at [paper/main.tex:30](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:30>) and [paper/main.tex:151](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:151>).

  That conflicts with the blanket statement that “operating points are chosen on validation” and that readiness intervals are conditional on that choice at [paper/main.tex:121](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:121>). The genuinely validation-selected 90% target produces 86.775% test removal at 45.634% engaged for learned aligned, versus 99.783% at 99.159% for rhythm ([regime_targets.csv:42](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/regime_targets.csv:42>)).

  This does not contaminate model fitting, but it makes the headline a retrospective inverse-Pareto test statistic, not a deployable operating point. Either label it explicitly that way throughout—including the abstract—or use nested/cross-fitted validation selection for the central operational claim.

## Major

- **The validation halves are not independent for NLR inference.**  
  [`nlr_unit`](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/aligned.py:61>) treats inference hour blocks as separate units when assigning early-stopping and threshold roles. Blocks from the same continuous session therefore occur in both validation halves at [src/aligned.py:143](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/aligned.py:143>). Cross-data evaluation repeats this pattern before later merging those blocks into one bootstrap cluster at [src/crossdata.py:99](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/crossdata.py:99>). This contradicts the paper’s “validation units are split” description and introduces dependence between early stopping and operating-point selection. I found no test-to-training leakage otherwise.

- **The confidence intervals omit training, split, and threshold-grid uncertainty.**  
  [`ap_with_ci`](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/crossdata.py:130>) resamples only the fixed model’s test clusters; it never retrains. The readiness bootstrap similarly holds the fitted scores and single train/validation split fixed at [src/regime.py:428](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/regime.py:428>). “Significantly outperforms” therefore means conditional on this fitted model and split. This is especially weak for NLR’s 12 test clusters and Elsayed’s six. Repeat whole-job splits/seeds or use a nested clustered bootstrap that retrains.

- **Clustered intervals do not remove node-level pseudoreplication from the point estimand or training.**  
  Up to four near-synchronous nodes from one NLR job remain in the model dataset at [src/load.py:208](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/load.py:208>). Pooled AP and readiness metrics weight all their rows and events, even though uncertainty later clusters by job. The reported 248 NLR node-hours are specifically the capped modeling subset, calculated at [src/paper.py:33](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/paper.py:33>), but neither the cap nor the resulting weighting is disclosed in the paper. Add one-node-per-job or job-macro sensitivity results.

- **The cross-dataset conclusion overreaches the reported metric.**  
  The NLR and Supercloud “significant” cross-site claims are supported for AP: pooled differences are \(+0.286\) and \(+0.141\), with positive intervals ([crossdata_ap_harmonized.csv:30](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/crossdata_ap_harmonized.csv:30>), [line 36](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/crossdata_ap_harmonized.csv:36>)). They do not establish superior physical smoothing or energy overhead. At nominal validation-selected 90% targets, learned removal is only 87.9% on NLR, 81.1% on Elsayed, and 88.3% on Supercloud ([crossdata_readiness_harmonized.csv:3](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/crossdata_readiness_harmonized.csv:3>), [line 9](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/crossdata_readiness_harmonized.csv:9>), [line 15](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/crossdata_readiness_harmonized.csv:15>)). The conclusion at [paper/main.tex:239](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:239>) should explicitly say “outperforms in AP.”

- **The energy-system evidence remains an idealized software simulation.**  
  The limiter has no storage power/capacity, state of charge, recharge, efficiency, degradation, rebound, or measured actuator dynamics; readiness cost is an assumed fraction of rated power at [src/regime.py:254](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/regime.py:254>). Sensor harmonization also assumes a 1 s trailing mean makes V100 measurements comparable to H100/B200 despite the NLR measurement mode being unknown ([paper/main.tex:87](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:87>)). These limitations are acknowledged, but they substantially weaken suitability for PES GM without sensitivity analyses or a physical actuator case study.

## Minor

- **All generated numeric values reconcile.** I independently reconstructed all 268 fields in `paper/numbers.json` from the CSV/JSON artifacts and found zero mismatches. `paper/main.tex` is also an exact expansion of the template and numbers file. The workload APs, latency APs, readiness table, validation-selected operating points, cross-dataset APs, and transfer mean/ranges are numerically supported.

- **The abstract conflates two comparisons.** At [paper/main.tex:28](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:28>), “the same model raises AP … from 0.67 … to 0.96” is logically wrong: 0.67 is rhythm replay, whereas retargeting the LightGBM model raises it from 0.58 to 0.96. The results section states this correctly.

- **The asymmetric \([-57.4,-8.8]\) interval is plausible, not evidence of an implementation bug.**  
  The point and interval exactly reproduce [regime_armed_needed.csv:3](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/regime_armed_needed.csv:3>). The statistic is a discontinuous minimum-over-thresholds functional. In my reproduction, rhythm required over 95% engagement in 84.8% of bootstrap samples, but some resampled cluster mixtures crossed 90% removal near 50–60% engagement, creating the long upper tail. The bootstrap median was about −49.3, close to the −50.8 point. This is heterogeneity/bimodality, not a sign error, but a distribution plot and more than 1000 resamples would be more informative than the percentile endpoints alone.

- The module-level target formula at [src/aligned.py:8](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/aligned.py:8>) is stale and does not match the corrected implementation’s upper bound.

- The legacy `_arm_from_triggers` in [src/simulate.py:111](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/simulate.py:111>) still uses the old hold-plus-one convention and omits the new decision delay. It does not drive the new readiness headline, but two incompatible simulator conventions remain in the repository.

- Cross-dataset decisions are sampled once per second through `STRIDE = 5` at [src/crossdata.py:37](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/crossdata.py:37>), whereas the NLR headline operates at 5 Hz. This should be disclosed.

- Forest-plot “unseen site” rows specifically use the shape-only transfer model, while in-domain and pooled rows use the ordinary feature model. The labels should say “unseen site, shape-only.”

- The seven Supercloud subgroup claims use seven unadjusted 95% intervals. “Significant for 7 of 7” should be identified as exploratory or corrected for multiplicity.

- The current manuscript still contains author placeholders and three incomplete references at [paper/main.tex:17](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:17>) and [paper/main.tex:248](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:248>). Submitted literally, this is a desk-rejection risk.

## Predicted decision

| Venue | Predicted decision | Rationale |
|---|---|---|
| IEEE PES GM 2027 | **Reject / major revision** | Interesting target-design result and substantially improved artifact, but the abstract’s operational headline is test-frontier-selected, uncertainty is conditional on one fitted split, and the actuator/sensor model is not yet strong enough for a grid-facing conclusion. |
| Climate Change AI-style workshop | **Borderline, leaning weak accept after correction; weak reject as submitted** | The three-dataset comparison, honest negative transfer result, and released analysis are useful workshop contributions. Acceptance becomes plausible if the readiness result is explicitly labeled retrospective, claims are restricted to AP where appropriate, and the incomplete manuscript metadata is fixed. |
tokens used
198,756
# Final peer review — Round 3

The round-2 implementation fixes are largely correct, and I found no discrepancies among the 268 generated values in `paper/numbers.json`, their source tables, and `paper/main.tex`. The PDF also matches the generated TeX. The remaining blocking issue is how the headline readiness result is selected and described: 48.4% versus 99.2% is a retrospective test-frontier statistic, not a validation-selected deployable operating point.

## Verification of round-2 fixes

1. **PASS — half-open arm window.**  
   [`_arm`](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/regime.py:82>) implements
   \[
   [\text{trigger}+\text{lat},\ \text{trigger}+\text{lat}+\text{hold})
   \]
   exactly. With 6 s at 5 Hz, a trigger arms 30 samples, not 31. The simulation uses this function consistently at [src/regime.py:222](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/regime.py:222>) and [src/regime.py:244](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/regime.py:244>).

2. **PASS — aligned label, rhythm score, latency, and off-by-one convention.**  
   [`lat_samples`](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/aligned.py:39>) adds the one-sample decision delay. For \(L=1\) s, engagement begins six samples after the feature row: five latency samples plus one completed-bin delay.  
   [`aligned_labels`](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/aligned.py:76>) uses
   \[
   v\in[e+FS,\ e+\text{hold}-1],
   \]
   and [`rhythm_aligned_score`](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/aligned.py:90>) evaluates exactly the same offsets through `range(lat + FS, lat + w)`. This is consistent with the declared endpoint-containment semantics and the simulator’s half-open window.

3. **PASS in substance — dense L=1 grid and `armed_needed`.**  
   Dense validation-score quantiles are constructed at [src/regime.py:181](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/regime.py:181>), substituted only at the headline 1 s latency at [src/regime.py:242](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/regime.py:242>), and consumed by [`armed_needed`](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/regime.py:406>).  
   Literal wording caveat: the code uses 200 linear quantiles plus ten extreme-tail quantiles, yielding 209 unique thresholds for the continuous learned scores, not exactly 200. Thus [paper/main.tex:152](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:152>) should say “about 200” or “209 validation-score thresholds.”

4. **PASS — bootstrap, transfer columns, and forest labels.**  
   Whole-dataset and subgroup bootstraps are both configured for 1000 draws at [src/crossdata.py:39](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/crossdata.py:39>) and used for workload subgroups at [src/crossdata.py:211](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/crossdata.py:211>).  
   Adaptation rows correctly distinguish draw-0 quantities from the five-draw mean/range at [src/transfer.py:121](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/transfer.py:121>); the paper generator uses `ap_ml_rep_mean/min/max`, not `draw0_*`, at [src/paper.py:93](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/paper.py:93>). The forest plot distinguishes in-domain, pooled, and unseen-site rows at [src/paper.py:155](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/paper.py:155>).

## Critical

- **The abstract’s central 48.4% versus 99.2% result is selected using test outcomes, contrary to the methods statement.**  
  [`armed_needed`](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/regime.py:406>) searches each strategy’s test curve and takes the minimum test engaged time satisfying the target at lines 417–425. It repeats that selection inside every test bootstrap. These are the values presented as the principal result at [paper/main.tex:30](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:30>) and [paper/main.tex:151](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:151>).

  That conflicts with the blanket statement that “operating points are chosen on validation” and that readiness intervals are conditional on that choice at [paper/main.tex:121](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:121>). The genuinely validation-selected 90% target produces 86.775% test removal at 45.634% engaged for learned aligned, versus 99.783% at 99.159% for rhythm ([regime_targets.csv:42](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/regime_targets.csv:42>)).

  This does not contaminate model fitting, but it makes the headline a retrospective inverse-Pareto test statistic, not a deployable operating point. Either label it explicitly that way throughout—including the abstract—or use nested/cross-fitted validation selection for the central operational claim.

## Major

- **The validation halves are not independent for NLR inference.**  
  [`nlr_unit`](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/aligned.py:61>) treats inference hour blocks as separate units when assigning early-stopping and threshold roles. Blocks from the same continuous session therefore occur in both validation halves at [src/aligned.py:143](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/aligned.py:143>). Cross-data evaluation repeats this pattern before later merging those blocks into one bootstrap cluster at [src/crossdata.py:99](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/crossdata.py:99>). This contradicts the paper’s “validation units are split” description and introduces dependence between early stopping and operating-point selection. I found no test-to-training leakage otherwise.

- **The confidence intervals omit training, split, and threshold-grid uncertainty.**  
  [`ap_with_ci`](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/crossdata.py:130>) resamples only the fixed model’s test clusters; it never retrains. The readiness bootstrap similarly holds the fitted scores and single train/validation split fixed at [src/regime.py:428](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/regime.py:428>). “Significantly outperforms” therefore means conditional on this fitted model and split. This is especially weak for NLR’s 12 test clusters and Elsayed’s six. Repeat whole-job splits/seeds or use a nested clustered bootstrap that retrains.

- **Clustered intervals do not remove node-level pseudoreplication from the point estimand or training.**  
  Up to four near-synchronous nodes from one NLR job remain in the model dataset at [src/load.py:208](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/load.py:208>). Pooled AP and readiness metrics weight all their rows and events, even though uncertainty later clusters by job. The reported 248 NLR node-hours are specifically the capped modeling subset, calculated at [src/paper.py:33](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/paper.py:33>), but neither the cap nor the resulting weighting is disclosed in the paper. Add one-node-per-job or job-macro sensitivity results.

- **The cross-dataset conclusion overreaches the reported metric.**  
  The NLR and Supercloud “significant” cross-site claims are supported for AP: pooled differences are \(+0.286\) and \(+0.141\), with positive intervals ([crossdata_ap_harmonized.csv:30](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/crossdata_ap_harmonized.csv:30>), [line 36](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/crossdata_ap_harmonized.csv:36>)). They do not establish superior physical smoothing or energy overhead. At nominal validation-selected 90% targets, learned removal is only 87.9% on NLR, 81.1% on Elsayed, and 88.3% on Supercloud ([crossdata_readiness_harmonized.csv:3](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/crossdata_readiness_harmonized.csv:3>), [line 9](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/crossdata_readiness_harmonized.csv:9>), [line 15](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/crossdata_readiness_harmonized.csv:15>)). The conclusion at [paper/main.tex:239](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:239>) should explicitly say “outperforms in AP.”

- **The energy-system evidence remains an idealized software simulation.**  
  The limiter has no storage power/capacity, state of charge, recharge, efficiency, degradation, rebound, or measured actuator dynamics; readiness cost is an assumed fraction of rated power at [src/regime.py:254](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/regime.py:254>). Sensor harmonization also assumes a 1 s trailing mean makes V100 measurements comparable to H100/B200 despite the NLR measurement mode being unknown ([paper/main.tex:87](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:87>)). These limitations are acknowledged, but they substantially weaken suitability for PES GM without sensitivity analyses or a physical actuator case study.

## Minor

- **All generated numeric values reconcile.** I independently reconstructed all 268 fields in `paper/numbers.json` from the CSV/JSON artifacts and found zero mismatches. `paper/main.tex` is also an exact expansion of the template and numbers file. The workload APs, latency APs, readiness table, validation-selected operating points, cross-dataset APs, and transfer mean/ranges are numerically supported.

- **The abstract conflates two comparisons.** At [paper/main.tex:28](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:28>), “the same model raises AP … from 0.67 … to 0.96” is logically wrong: 0.67 is rhythm replay, whereas retargeting the LightGBM model raises it from 0.58 to 0.96. The results section states this correctly.

- **The asymmetric \([-57.4,-8.8]\) interval is plausible, not evidence of an implementation bug.**  
  The point and interval exactly reproduce [regime_armed_needed.csv:3](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/regime_armed_needed.csv:3>). The statistic is a discontinuous minimum-over-thresholds functional. In my reproduction, rhythm required over 95% engagement in 84.8% of bootstrap samples, but some resampled cluster mixtures crossed 90% removal near 50–60% engagement, creating the long upper tail. The bootstrap median was about −49.3, close to the −50.8 point. This is heterogeneity/bimodality, not a sign error, but a distribution plot and more than 1000 resamples would be more informative than the percentile endpoints alone.

- The module-level target formula at [src/aligned.py:8](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/aligned.py:8>) is stale and does not match the corrected implementation’s upper bound.

- The legacy `_arm_from_triggers` in [src/simulate.py:111](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/simulate.py:111>) still uses the old hold-plus-one convention and omits the new decision delay. It does not drive the new readiness headline, but two incompatible simulator conventions remain in the repository.

- Cross-dataset decisions are sampled once per second through `STRIDE = 5` at [src/crossdata.py:37](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/crossdata.py:37>), whereas the NLR headline operates at 5 Hz. This should be disclosed.

- Forest-plot “unseen site” rows specifically use the shape-only transfer model, while in-domain and pooled rows use the ordinary feature model. The labels should say “unseen site, shape-only.”

- The seven Supercloud subgroup claims use seven unadjusted 95% intervals. “Significant for 7 of 7” should be identified as exploratory or corrected for multiplicity.

- The current manuscript still contains author placeholders and three incomplete references at [paper/main.tex:17](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:17>) and [paper/main.tex:248](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:248>). Submitted literally, this is a desk-rejection risk.

## Predicted decision

| Venue | Predicted decision | Rationale |
