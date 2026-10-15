## Round-2 items

- **Resolved — “real user jobs.”** Replaced with “labelled cluster jobs”; the prose correctly describes scheduler-observed jobs without claiming production use.
- **Resolved — storage “overhead.”** Replaced by “reported energy metric,” including the table heading and caption.
- **Resolved — adaptation draws.** Now says “five random draws,” and correctly covers one-class fitting subsets and early-stopping tails.
- **Resolved — synchrony and threshold wording.** Both the introduction and figure caption now use appropriately qualified language.
- **Resolved — label-only overclaim.** The abstract and contribution use “matched-pipeline ablation”; the methods and discussion disclose that prevalence-derived class weight changes with the target.
- **Resolved — 91% deviation.** Independent reconstruction gives:
  - Raw: `913300 / 1000997 = 0.912390`
  - Smoothed: `478650 / 1000997 = 0.478173`, matching the harmonized CSV’s `0.4782`.
  
  The raw CSV is demonstrably stale: even unchanged NLR and Elsayed have different raw/harmonized positive rates. Keeping 91% is correct.
- **Resolved — nodes versus trace segments.** Metadata confirms 560 jobs, 973 segments, at most four unique retained nodes per job, and one job with five segments because one node was split.
- **Resolved — inference validation blocks.** The seeded-shuffle wording matches `val_roles()`.

## New issues

1. **Open — class-weight association is ambiguous.** The values are correct: aligned `1.7534`, big-drop `2.5728`. However, the current unlabeled “1.75 versus 2.57” follows prose mentioning big-drop first and can be read backwards.

   In [template.tex](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/arxiv/template.tex:231), replace the parenthetical with:

   ```tex
   (1.75 for the aligned target versus 2.57 for the big-drop target).
   ```

2. **Open — “Every number” is literally too broad.** Method constants and descriptive values are not generated from result tables.

   In [template.tex](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/arxiv/template.tex:537), replace:

   ```tex
   Every number in this paper is generated from result tables written by the analysis pipeline.
   ```

   with:

   ```tex
   The reported model and controller metrics are generated from result tables written by the analysis pipeline.
   ```

## Build/readiness

`main.tex` is an exact expansion of all 217 template placeholders, with none unresolved. All references, citations, environments, and graphics resolve. The current 11-page PDF was built from the current source; its log contains no errors or unresolved-reference warnings, only three harmless underfull-box notices.

External spot checks also support the sensor statement in the [NVML documentation](https://docs.nvidia.com/deploy/nvml-api/latest/api/group__nvmlDeviceQueries.html) and the characterization of the [MIT Supercloud dataset](https://github.com/MIT-AI-Accelerator/MIT-Supercloud-Dataset).

READY AFTER FIXES
