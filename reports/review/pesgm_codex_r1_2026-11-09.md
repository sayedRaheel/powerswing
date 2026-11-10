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
session id: 01a1c29b-7bf8-73f0-8924-ed997ab80be6
--------
user
You are an independent reviewer for an IEEE PES General Meeting 2027 submission (max 5 pages, IEEE conference format). Paper: paper/main.pdf (source paper/main.tex, generated from paper/template.tex by src/paper.py from result tables in data/processed and reports/). The longer arXiv version paper/arxiv/main.tex already passed 3 review rounds (see reports/review/arxiv_codex_r3_2026-10-15.md). Task: (1) check every number in paper/main.tex against the arXiv version and the generating tables (data/processed/ablation_info.json, reports/*.csv); (2) find any claim stronger than the evidence, especially in the abstract and the new 'Matched label ablation' paragraph; (3) check consistency between abstract, results and conclusion (e.g. conclusion still attributes the gain to the target; is that now supported by the matched ablation?); (4) PES GM fit: anything a power-systems reviewer will reject quickly, and whether using the 5th page for a missing element would help; (5) formatting issues (author block, keywords, references, figure readability). Output: verdict READY / READY AFTER FIXES / NOT READY, then numbered findings with exact file:line and the exact replacement text for each fix. Do not edit files. No em dashes.
hook: SessionStart
hook: SessionStart Completed
codex
I’ll audit the conference source, the accepted-review context, the arXiv source, and every generating table. I’ll use the code-review skill because this is a source-grounded review, then inspect the rendered PDF for layout and readability.
exec
/bin/zsh -lc "sed -n '1,240p' /Users/sayedraheel/.codex/skills/code-review/SKILL.md" in /Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing
 succeeded in 0ms:
---
name: code-review
description: >
  Automated code review for pull requests using specialized review patterns.
  Analyzes code for quality, security, performance, and best practices. Use when
  the user asks to review code, review a PR, audit code quality, check for security
  issues, or says "review this," "code audit," or "check this PR." For refactoring
  existing code, see code-refactoring. For running coding agents, see coding-agent.
related_skills: [code-refactoring, code-documentation, commit-work, backend-development, backend-coding-agent, frontend-coding-agent]
metadata:
  author: anthropic-community
  version: 1.2.0
source: anthropics/claude-code
license: Apache-2.0
---

# Code Review

## Workflow

### Step 0: Get the Diff

Choose the appropriate input mode:

| Input Mode | How to Get It |
|-----------|---------------|
| GitHub PR | `gh pr diff <number>` — or `gh pr view <number> --json files,additions,deletions` |
| Local git diff | `git diff main...HEAD` or `git diff HEAD~1` |
| Pasted code/snippet | User pastes directly — treat as a single-file review |
| File path | `cat <file>` or `read <file>` — review the whole file |
| Specific function | Extract context around the function; note any callers if visible |

**Large diffs (>500 lines changed):** Break into file-by-file passes. Prioritize: (1) security-sensitive files, (2) core logic changes, (3) tests, (4) config.

**Files to skip automatically:**
- Lock files (`package-lock.json`, `yarn.lock`, `Cargo.lock`, `poetry.lock`)
- Auto-generated files (`*.pb.go`, `schema.graphql` if generated, migration files with only schema)
- Formatting-only changes (whitespace, line length fixes without logic)
- Binary files, assets, fonts

### Step 1: Understand the Change
- Read the PR description or diff summary
- Identify the change category: feature, bugfix, refactor, config, dependency update
- Note the PR size and risk level before applying reviews

### Step 2: Run Category Reviews
Apply in this order, skipping inapplicable categories:

1. **Security** — always run
2. **Code Quality** — always run
3. **Performance** — skip for config-only, docs, or trivial changes
4. **Testing** — skip only if no logic changed (pure docs, types, or config)

### Step 3: Format and Deliver
Use the Review Output Format below. On large PRs with Critical issues, omit the Nits section — don't bury blockers in noise.

---

## Severity Decision Guide

Use this to decide where each finding belongs:

| Severity | When to use |
|----------|-------------|
| 🔴 Critical | Security vulnerability; data loss risk; correctness bug that will break in production; blocks merge |
| 🟡 Suggestion | Best practice violation; missing tests for new logic; maintainability concern; performance issue in a hot path |
| 🟢 Nit | Style preference; naming that could be slightly clearer; minor polish; subjective improvements |
| ✅ What's Good | Patterns worth calling out positively; good test coverage; clean abstractions |

**Rule:** If you have 3+ Criticals, omit Nits entirely. Signal > noise.

---

## Review Categories

### 1. Security Review
Check for:
- SQL injection vulnerabilities
- XSS (Cross-Site Scripting)
- Command injection
- Insecure deserialization
- Hardcoded secrets/credentials
- Improper authentication/authorization
- Insecure direct object references
- Missing rate limiting on auth endpoints
- API keys/tokens in logs or error messages

### 2. Performance Review

*Skip for: config-only changes, pure refactors with no algorithmic change, docs, or trivial single-field changes.*

Check for:
- N+1 queries
- Missing database indexes
- Unnecessary re-renders (React)
- Memory leaks
- Blocking operations in async code
- Missing caching opportunities
- Large bundle sizes (new heavy deps)

### 3. Code Quality Review
Check for:
- Code duplication (DRY violations)
- Functions doing too much (SRP violations)
- Deep nesting / complex conditionals
- Magic numbers/strings
- Poor naming
- Missing error handling
- Incomplete type coverage
- API contract changes / backward compatibility breaks

### 4. Testing Review

*Skip for: pure config, dependency bumps with no API change, or documentation-only PRs.*

Check for:
- Missing test coverage for new code
- Tests that don't test behavior (test implementation, not outcome)
- Flaky test patterns (time-dependent, network calls without mocks)
- Missing edge cases
- Mocked external dependencies without integration test coverage

---

## Review Output Format

```markdown
## Code Review Summary

### 🔴 Critical (Must Fix)
- **[File:Line]** [Issue description]
  - **Why:** [Explanation]
  - **Fix:** [Suggested fix]

### 🟡 Suggestions (Should Consider)
- **[File:Line]** [Issue description]
  - **Why:** [Explanation]
  - **Fix:** [Suggested fix]

### 🟢 Nits (Optional)
- **[File:Line]** [Minor suggestion]

### ✅ What's Good
- [Positive feedback on good patterns]
```

---

## Common Patterns to Flag

### Security — JavaScript/TypeScript
```javascript
// BAD: SQL injection
const query = `SELECT * FROM users WHERE id = ${userId}`;

// GOOD: Parameterized query
const query = 'SELECT * FROM users WHERE id = $1';
await db.query(query, [userId]);
```

### Security — Python
```python
# BAD: SQL injection
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# GOOD: Parameterized query
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

### Performance — JavaScript
```javascript
// BAD: N+1 query
users.forEach(async user => {
  const posts = await getPosts(user.id);
});

// GOOD: Batch query
const userIds = users.map(u => u.id);
const posts = await getPostsForUsers(userIds);
```

### Error Handling — JavaScript
```javascript
// BAD: Swallowing errors
try {
  await riskyOperation();
} catch (e) {}

// GOOD: Handle or propagate
try {
  await riskyOperation();
} catch (e) {
  logger.error('Operation failed', { error: e });
  throw new AppError('Operation failed', { cause: e });
}
```

### Error Handling — Python
```python
# BAD: Bare except swallowing errors
try:
    risky_operation()
except:
    pass

# GOOD: Specific exception + logging
try:
    risky_operation()
except ValueError as e:
    logger.error("Validation failed: %s", e)
    raise
```

---

## Review Checklist

- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] Error handling complete
- [ ] Types/interfaces defined
- [ ] Tests added for new code
- [ ] No obvious performance issues
- [ ] Code is readable and documented
- [ ] Breaking changes documented
- [ ] API contracts unchanged (or migration path noted)

---

## Examples

### Example: Review a GitHub PR

**User says:** "Review PR #42 on our repo"

**Actions:**
1. `gh pr diff 42` — fetch the diff
2. Check size: if >500 lines, prioritize by risk (security files first)
3. Skip lock files, auto-generated files
4. Apply Security + Code Quality always; Performance + Testing if applicable

codex
The review skill’s software-specific checks are not relevant here, so I’m applying its evidence-first severity and exact-location format to the manuscript. I’m now building a line-numbered inventory of claims and numeric values, then tracing each to the arXiv text or generated artifacts.
exec
/bin/zsh -lc "pwd && rg --files paper data/processed reports | sort | sed -n '1,240p'
printf '\\n--- conference source ---\\n'
nl -ba paper/main.tex | sed -n '1,320p'
printf '\\n--- arxiv source ---\\n'
nl -ba paper/arxiv/main.tex | sed -n '1,420p'
printf '\\n--- prior review ---\\n'
sed -n '1,280p' reports/review/arxiv_codex_r3_2026-10-15.md" in /Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing
 succeeded in 0ms:
/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing
data/processed/ablation_info.json
data/processed/aligned_info.json
data/processed/aligned_scores_test.parquet
data/processed/aligned_scores_test_L0.2.parquet
data/processed/aligned_scores_test_L0.5.parquet
data/processed/aligned_scores_test_L0.parquet
data/processed/aligned_scores_test_L1.parquet
data/processed/aligned_scores_test_L2.parquet
data/processed/aligned_scores_test_L3.parquet
data/processed/aligned_scores_val.parquet
data/processed/aligned_scores_val_L0.2.parquet
data/processed/aligned_scores_val_L0.5.parquet
data/processed/aligned_scores_val_L0.parquet
data/processed/aligned_scores_val_L1.parquet
data/processed/aligned_scores_val_L2.parquet
data/processed/aligned_scores_val_L3.parquet
data/processed/chronos_subset_idx.npy
data/processed/crossdata.log
data/processed/crossdata_harmonized.log
data/processed/drop_events.parquet
data/processed/drop_rate_by_nodes.csv
data/processed/drop_summary.csv
data/processed/ext_elsayed_meta.csv
data/processed/ext_elsayed_traces.parquet
data/processed/ext_supercloud_class_counts.csv
data/processed/ext_supercloud_meta.csv
data/processed/ext_supercloud_traces.parquet
data/processed/final_logs/aligned.log
data/processed/final_logs/chain.log
data/processed/final_logs/crossdata.log
data/processed/final_logs/regime.log
data/processed/final_logs/transfer.log
data/processed/jobs.parquet
data/processed/lgb_aligned.txt
data/processed/lgb_aligned_L0.2.txt
data/processed/lgb_aligned_L0.5.txt
data/processed/lgb_aligned_L0.txt
data/processed/lgb_aligned_L1.txt
data/processed/lgb_aligned_L2.txt
data/processed/lgb_aligned_L3.txt
data/processed/lgb_clf.txt
data/processed/lgb_reg_10s.txt
data/processed/lgb_reg_1s.txt
data/processed/lgb_reg_5s.txt
data/processed/model_info.json
data/processed/nets_chronos.parquet
data/processed/nets_latency.json
data/processed/nets_test.parquet
data/processed/nets_timesfm.parquet
data/processed/nets_val_forecast_tcn.parquet
data/processed/nets_val_score_tcn.npy
data/processed/regime_test_raw.parquet
data/processed/regime_val_raw.parquet
data/processed/site_random_offsets.npy
data/processed/slide_example.npz
data/processed/sync_skew.csv
data/processed/table_test.parquet
data/processed/table_train.parquet
data/processed/table_val.parquet
data/processed/tcn.pt
data/processed/test_predictions.parquet
data/processed/traces.parquet
data/processed/traces_meta.csv
data/processed/transfer.log
data/processed/val_roles_nlr.json
data/processed/xd_meta.csv
data/processed/xd_table_harmonized.parquet
data/processed/xd_table_raw.parquet
paper/arxiv/abstract_for_arxiv.txt
paper/arxiv/fig_example.pdf
paper/arxiv/fig_forest.pdf
paper/arxiv/fig_readiness.pdf
paper/arxiv/main.pdf
paper/arxiv/main.tex
paper/arxiv/template.tex
paper/arxiv_submission.tar.gz
paper/email_nlr_authors.md
paper/fig_example.pdf
paper/fig_forest.pdf
paper/fig_readiness.pdf
paper/main.pdf
paper/main.tex
paper/numbers.json
paper/template.tex
reports/figures/drop_warning_pr_curve.png
reports/figures/eda_drop_stats.png
reports/figures/eda_sample_traces.png
reports/figures/eda_single_vs_multinode.png
reports/figures/error_by_horizon.png
reports/figures/error_by_horizon_with_chronos.png
reports/figures/forecast_overlays_5s.png
reports/figures/model_comparison_5s.png
reports/figures/model_comparison_5s_with_chronos.png
reports/figures/regime_map.png
reports/figures/regime_pareto.png
reports/figures/site_scaleup.png
reports/figures/smoothing_before_after.png
reports/figures/smoothing_tradeoff.png
reports/figures/summary_slide.png
reports/results.md
reports/review/arxiv_codex_r1_2026-10-15.md
reports/review/arxiv_codex_r2_2026-10-15.md
reports/review/arxiv_codex_r3_2026-10-15.md
reports/review/arxiv_kimi_r1_2026-10-15.md
reports/review/codex_final_review_r3_2026-10-13.md
reports/review/codex_peer_review_2026-10-12.md
reports/review/pesgm_codex_r1_2026-11-09.md
reports/review/prior_art_2026-10-12.md
reports/tables/crossdata_ap_harmonized.csv
reports/tables/crossdata_ap_raw.csv
reports/tables/crossdata_readiness_harmonized.csv
reports/tables/crossdata_readiness_raw.csv
reports/tables/drop_warning.csv
reports/tables/drop_warning_by_workload.csv
reports/tables/forecast_by_workload.csv
reports/tables/forecast_overall.csv
reports/tables/forecast_subset_with_chronos.csv
reports/tables/generalization_lowo.csv
reports/tables/key_numbers.json
reports/tables/latency.csv
reports/tables/regime_armed_needed.csv
reports/tables/regime_map.csv
reports/tables/regime_ml_vs_rhythm_ci.csv
reports/tables/regime_pareto_test.csv
reports/tables/regime_targets.csv
reports/tables/sim_params.json
reports/tables/site_scaleup.csv
reports/tables/smoothing_by_workload.csv
reports/tables/smoothing_per_trace.csv
reports/tables/smoothing_summary.csv
reports/tables/transfer_harmonized.csv

--- conference source ---
     1	\documentclass[conference]{IEEEtran}
     2	\usepackage{iftex}
     3	\ifXeTeX
     4	  \usepackage{fontspec}
     5	  \setmainfont{texgyretermes}[Extension=.otf,UprightFont=*-regular,BoldFont=*-bold,ItalicFont=*-italic,BoldItalicFont=*-bolditalic]
     6	\fi
     7	\usepackage{graphicx}
     8	\usepackage{amsmath}
     9	\usepackage{booktabs}
    10	\usepackage{url}
    11	\usepackage[hidelinks]{hyperref}
    12	
    13	\begin{document}
    14	
    15	\title{Predict the Breach, Not the Drop:\\Control-Aligned Learning for Smoothing\\AI Training Power Swings}
    16	
    17	\author{\IEEEauthorblockN{Sayed Raheel}
    18	\IEEEauthorblockA{Independent Researcher; Yeshiva University alumnus\\
    19	\texttt{shussai1@mail.yu.edu}}}
    20	
    21	\maketitle
    22	
    23	\begin{abstract}
    24	Large AI training jobs swing GPU power by tens of percent within a second, and synchronized jobs can
    25	violate the ramp limits that utilities place on large loads. Fill-type smoothing (filler GPU work,
    26	storage) removes these violations but must be engaged before the fall, and keeping it engaged costs
    27	energy. Forecasting can decide when to engage it. We find that the choice of training target matters
    28	substantially. In a matched-pipeline ablation, a gradient-boosted classifier trained on the usual target,
    29	``a large power drop is coming'', ranks the violations a ramp limiter must catch poorly (average precision
    30	0.58). Trained on the controller's own event, ``a ramp-limit violation will occur while a
    31	limiter armed now would be armed'', the same pipeline reaches 0.96 (difference 95\% CI
    32	0.28 to 0.49) on held-out H100 training and inference
    33	traces, against 0.67 for no-learning rhythm replay of the same target. With a threshold chosen on
    34	validation for a 90\% removal target, the learned trigger removes 86.8\% of test
    35	violations with the actuator engaged 45.6\% of the time, while rhythm replay meets
    36	the target only by staying engaged 99.2\% of the time, i.e.\ effectively always on.
    37	Across three public datasets covering H100, B200 and V100 nodes and both benchmark and real user jobs,
    38	the learned trigger has significantly higher AP than rhythm replay on two datasets when that site is in the
    39	training data, after harmonizing sensor averaging; the third is inconclusive. Transfer to an unseen
    40	site is unreliable, which we report as an open problem.
    41	\end{abstract}
    42	
    43	\begin{IEEEkeywords}
    44	data centers, AI workloads, ramp rate, load forecasting, power smoothing, energy storage
    45	\end{IEEEkeywords}
    46	
    47	\section{Introduction}
    48	Training a large model alternates compute-heavy and communication-heavy phases, so GPU power moves in
    49	fast, large steps. Because all nodes of a job step together, a synchronized job appears to the grid as
    50	one large swing; industry reports describe swings of tens to hundreds of megawatts and evaluate software
    51	power burning, GPU power floors and rack storage as mitigations~\cite{msft_stab}. Hardware filters and
    52	storage that react to the measured load are being developed~\cite{easyrider,activefilter}; predictive
    53	storage control has been studied with perfect preview~\cite{hessdpc} and with short delay-compensating
    54	predictors~\cite{lyu}; and AI data center load has been forecast at minute scales~\cite{mughees}. We are
    55	not aware of work that studies how the forecasting target affects smoothing performance.
    56	
    57	A fill-type actuator must be engaged before the fall arrives, but engagement costs energy and readiness
    58	(a hot inverter, pre-warmed filler kernels). A forecaster can engage the actuator only when needed. The
    59	obvious competitor is free: training power is periodic, so ``replay the last cycle'' is a strong
    60	predictor. Our contributions:
    61	\begin{itemize}
    62	\item A control-aligned prediction target: a ramp-limit violation that falls entirely inside the window
    63	a limiter armed now would cover, instead of a generic ``large drop''.
    64	\item A readiness analysis (violations removed versus time engaged) comparing learned triggers, rhythm
    65	replay, an always-on limiter and a perfect-foresight oracle in one simulator.
    66	\item A three-dataset study (H100, B200, V100; benchmarks and real jobs) with job-clustered confidence
    67	intervals, a sensor-harmonization step, and a negative result on unseen sites.
    68	\end{itemize}
    69	
    70	\section{Data}
    71	\textbf{NLR}~\cite{nlr}: 4$\times$H100 nodes running MLPerf Llama2-70B LoRA and Stable Diffusion
    72	training on 1--16 nodes, plus three vLLM Llama3.1-70B inference benchmarks, NVML power at 5--10~Hz,
    73	248 node-hours (at most four nodes per job, which run nearly in lockstep, are kept; all
    74	are weighted equally in metrics). Training jobs are split whole into train, validation and test; each
    75	inference benchmark is a single continuous session split in time, so its test portion counts as one
    76	independent unit. \textbf{Elsayed et al.}~\cite{elsayed}: single 8$\times$H100 and 8$\times$B200 nodes
    77	running diffusion and Llama 1B--8B fine-tuning sweeps, 15-minute sessions, 32 unique
    78	sessions. \textbf{MIT Supercloud}~\cite{supercloud}: a stratified subset of 560 labelled jobs (80 per
    79	model class: VGG, ResNet, Inception, U-Net, BERT, DistilBERT, GNN) on nodes with one or two V100s,
    80	nvidia-smi at 10~Hz, 1,292 node-hours of real user jobs.
    81	
    82	All traces are averaged onto a 0.2~s grid and expressed as ``NLR-equivalent watts'' (power $\times$
    83	2.8~kW divided by the node's rated GPU power), so a 10\%/s limit means the same fraction of rated power
    84	everywhere. Jobs are assigned whole to train, validation and test (about 60/20/20). For the
    85	control-aligned models, validation units are split into two halves, one for early stopping and one for
    86	choosing operating points; for NLR inference the validation halves are alternate hour blocks of the
    87	same session and so are not independent. (The big-drop baselines from earlier work were early-stopped on all
    88	validation units.)
    89	
    90	\textbf{Sensor harmonization.} NVML documents that on recent architectures the default power reading is
    91	averaged over about 1~s, while older GPUs such as the V100 report instantaneous power. The NLR
    92	documentation does not state which reading was logged. Raw V100 traces flicker: without harmonization,
    93	91\% of Supercloud test seconds are labelled ``violation imminent''. We apply a 1~s trailing mean to
    94	Supercloud so that all three datasets are compared at similar effective bandwidth.
    95	
    96	\section{Problem and methods}
    97	\subsection{Ramp limit, limiter and readiness}
    98	A violation starts when the node's 1~s down-ramp exceeds 10\% of rated power. A fill-type limiter adds
    99	power only when the load falls faster than the limit allows, then tapers at 90\% of the allowed rate. A trigger
   100	issued at row $t$ acts one sample later (each row averages $[t, t{+}0.2\,\mathrm{s})$), engages the
   101	limiter after an actuator latency $L$ (1~s unless stated) and arms it for 6~s; the limiter keeps
   102	filling until it meets the load. We count as \emph{engaged} every sample where the limiter is armed or
   103	still filling, and report violations removed against engaged time, plus energy overhead with a standby
   104	draw of 0--5\% of rated power while engaged. References: always-on, always-burn (a floor at 80\% of the trailing 60~s peak,
   105	which removes only 6.7\% of violations for 6.8\% extra energy) and an oracle that
   106	arms just in time for every violation, including those induced by the limiter itself.
   107	
   108	\subsection{Targets}
   109	The \emph{big-drop} target labels $t$ positive if a fall of more than 30\% of the recent peak within
   110	1~s starts in the next 5~s. The \emph{control-aligned} target labels $t$ positive if the whole 1~s ramp window
   111	of a raw violation lies inside the 6~s window during which a trigger at $t$ keeps the limiter armed, so
   112	the limiter is armed throughout that fall. Violations induced by the limiter itself are not labelled.
   113	Many violations (e.g.\ the 22\% square wave of Llama LoRA training) are not big drops, so the two
   114	targets differ substantially.
   115	
   116	\subsection{Predictors}
   117	\emph{Rhythm replay} estimates the period $P$ from a trailing 120~s autocorrelation, predicts
   118	$\hat p(t+k)=p(t+k-P\lceil k/P\rceil)$, and scores the largest predicted 1~s down-ramp inside the
   119	target window; it needs no training. The \emph{learned} predictor is LightGBM on 56 trailing features
   120	(lags, differences, rolling statistics, time since recent steps and drops, rhythm period, phase and
   121	rhythm forecasts), one model per actuator latency. A shape-only variant divides every level feature by
   122	the trailing 60~s maximum.
   123	
   124	\subsection{Evaluation}
   125	Ranking quality is average precision (AP) on test rows. Uncertainty is a paired bootstrap over
   126	independent clusters (training jobs, or inference sessions; 1000 resamples). Operating points are chosen
   127	on the validation threshold half and scored on test. All intervals are conditional on the single fitted
   128	model and split: they resample test clusters but do not retrain. Cross-dataset comparisons score one
   129	decision per second; the NLR readiness analysis scores every 0.2~s row.
   130	
   131	\section{Results}
   132	\subsection{Training target}
   133	On NLR test traces, rhythm replay ranks the control-aligned event with AP 0.67; LightGBM trained
   134	on the control-aligned target reaches 0.96, and the gain holds for each workload (Table~\ref{tab:wl}).
   135	\emph{Matched label ablation.} Training the big-drop label through the same pipeline (same rows, features,
   136	LightGBM settings, early-stopping data and metric, and square-root class-weighting rule, which gives weight
   137	1.75 for the aligned and 2.57 for the big-drop target) yields AP 0.58 on the aligned event
   138	against 0.96, a paired cluster-bootstrap difference of 0.37 (95\% CI
   139	0.28 to 0.49, 12 clusters). The big-drop model is good at its own task
   140	(AP 0.93 on the big-drop event, where the aligned model reaches
   141	0.48): the two labels describe different events.
   142	Results are stable across actuator latencies (AP 0.96 at 0~s, 0.95
   143	at 3~s; rhythm replay 0.68 and 0.67).
   144	
   145	\begin{table}[t]
   146	\centering
   147	\caption{NLR test AP on the control-aligned target (1~s latency).}
   148	\label{tab:wl}
   149	\begin{tabular}{lcc}
   150	\toprule
   151	Workload & Learned & Rhythm replay\\
   152	\midrule
   153	Llama2-70B LoRA training & 1.00 & 0.81\\
   154	Stable Diffusion training & 0.96 & 0.73\\
   155	Offline inference & 0.55 & 0.29\\
   156	Online inference, finite & 0.76 & 0.09\\
   157	Online inference, fixed rate & 0.65 & 0.36\\
   158	\bottomrule
   159	\end{tabular}
   160	\end{table}
   161	
   162	\subsection{Readiness}
   163	Fig.~\ref{fig:ready} sweeps each trigger's threshold (about 200 validation-score quantiles) on NLR test
   164	traces. Every trigger can reach high removal by staying engaged long enough; what differs is the engaged
   165	time needed (Table~\ref{tab:arm}). Table~\ref{tab:arm} reads the best threshold off each test curve, so
   166	it is a retrospective comparison of attainable trade-offs, not a deployable operating point; the
   167	validation-chosen operating points follow below.
   168	To remove 90\% of violations, the control-aligned learned trigger needs 48.4\%
   169	engaged time, whereas rhythm replay of the same target reaches 90\% only at 99.2\%,
   170	i.e.\ it is no better than always-on. The paired cluster-bootstrap difference is
   171	$-$50.8 points (95\% CI $-$57.4 to
   172	$-$8.8), and $-$40.8 points at 95\% removal (CI
   173	$-$49.1 to $-$31.4). The learned big-drop trigger
   174	needs more engaged time than the control-aligned one (64.3\% at 90\%; difference
   175	$-$15.9 points, CI $-$25.7 to $-$3.9). At 95\%
   176	removal the interval includes zero (CI $-$26.3 to 0.5), so with
   177	12 test clusters the target's effect is clearest in ranking quality (AP 0.58 vs 0.96). The oracle removes all violations at 29.8\% engaged time, which bounds what
   178	better prediction could still gain.
   179	
   180	\begin{table}[t]
   181	\centering
   182	\caption{Engaged time (\% of time) needed to reach a violation-removal level, NLR test, 1~s latency.}
   183	\label{tab:arm}
   184	\begin{tabular}{lccc}
   185	\toprule
   186	Removal & Learned, aligned & Rhythm, aligned & Learned, big-drop\\
   187	\midrule
   188	80\% & 43.1 & 51.5 & 53.0\\
   189	90\% & 48.4 & 99.2 & 64.3\\
   190	95\% & 58.4 & 99.2 & 74.8\\
   191	\bottomrule
   192	\end{tabular}
   193	\end{table}
   194	
   195	\begin{figure}[t]
   196	\centering
   197	\includegraphics[width=\columnwidth]{fig_readiness.pdf}
   198	\caption{Violations removed versus engaged time on NLR test traces (1~s latency, dense threshold sweep).
   199	Always-on removes everything but is always engaged.}
   200	\label{fig:ready}
   201	\end{figure}
   202	
   203	With operating points chosen on validation and a standby draw of 2\% of rated power, a 90\% target
   204	gives 86.8\% removal at 45.6\% engaged time and
   205	3.7\% energy overhead for the learned trigger; rhythm replay meets the target only
   206	by staying engaged 99.2\% of the time (5.4\%
   207	overhead, versus 5.4\% for always-on). At an 80\% target the validation-chosen
   208	learned threshold undershoots on test (73.7\% removal), a reminder that operating
   209	points chosen on few validation jobs transfer imperfectly.
   210	
   211	\subsection{Across sites and GPUs}
   212	Fig.~\ref{fig:forest} summarizes the learned-minus-rhythm AP difference. Trained on the test site's own
   213	training jobs (in-domain) or on all three datasets (pooled), the learned trigger significantly beats
   214	rhythm replay on NLR (pooled AP 0.96 vs 0.67) and on real Supercloud jobs
   215	(pooled 0.88 vs 0.74; exploratory per-class intervals, without multiplicity correction, are
   216	positive for 7 of 7 model classes). On Elsayed the point estimate favours learning
   217	(0.92 vs 0.88) but the interval includes zero with six test
   218	sessions, and rhythm replay is better on its diffusion sessions; we hypothesize that their very regular
   219	cadence suits replay, but two test sessions do not allow a firm conclusion.
   220	
   221	\begin{figure}[t]
   222	\centering
   223	\includegraphics[width=\columnwidth]{fig_forest.pdf}
   224	\caption{AP difference between the learned control-aligned trigger and rhythm replay, with 95\%
   225	cluster bootstrap intervals. Red: learned significantly better; blue: rhythm significantly better.}
   226	\label{fig:forest}
   227	\end{figure}
   228	
   229	\subsection{Unseen sites}
   230	When the test dataset is excluded from training, the learned trigger is not better than rhythm replay
   231	anywhere. With shape-only features it reaches AP 0.65 on NLR (rhythm
   232	0.67, CI of difference $-$0.06 to 0.02),
   233	0.85 on Elsayed (rhythm 0.88), and
   234	0.66 on Supercloud, significantly below rhythm replay
   235	(0.74; CI $-$0.12 to $-$0.04).
   236	Continuing to train on 60 minutes of the new site's data (mean of five independent draws) gives
   237	0.71 on NLR (range 0.62 to
   238	0.77) and 0.64 on Supercloud (range
   239	0.58 to 0.69), so a short
   240	calibration period does not reliably recover the in-domain advantage. Rhythm replay needs no site data;
   241	in our experiments a learned trigger needed the site in its training set.
   242	
   243	\section{Discussion and limitations}
   244	\emph{Sensors.} If NLR and Elsayed power is NVML's 1~s average, true ramps are faster than measured and
   245	measured lead times are optimistic. \emph{Simulation.} The actuator is an idealized limiter with fixed
   246	latency, hold time and standby draw; storage capacity, state of charge, efficiency and wear are not modelled, and standby cost is an
   247	assumed fraction of rated power.
   248	\emph{Workloads.} NLR and Elsayed are scripted benchmarks; NLR inference falls are dominated by gaps
   249	between benchmark runs, and each NLR inference workload is a single session. Supercloud adds real jobs
   250	on older V100 nodes. \emph{Scale.} Results are per node; synchronized multi-node jobs scale the same
   251	swing, while desynchronized jobs partly cancel. \emph{Licences.} Supercloud is CC BY-NC-ND and the Elsayed
   252	archive README states CC BY-NC-ND; both were used for research only and are not redistributed.
   253	
   254	\section{Conclusion}
   255	For fill-type smoothing of AI power swings, a forecaster should be trained on the controller's event, a
   256	ramp-limit violation inside the actuator's engagement window, rather than on a generic large drop. With
   257	that target a small gradient-boosted model needs substantially less engaged time than rhythm replay for
   258	the same violation removal on H100 benchmark traces, and ranks violations better (higher AP) on real
   259	V100 jobs, provided the site is represented in training. Closing the gap to the oracle and making learned triggers transfer to
   260	new sites are the natural next steps.
   261	
   262	\section*{Code availability and use of AI tools}
   263	Code is available from the author on request; the datasets are public from their original sources.
   264	Analysis code and text were drafted with the help of AI coding and writing assistants and independently
   265	reviewed by a separate AI model. The author checked the results and is responsible for the content.
   266	
   267	\begin{thebibliography}{9}
   268	\bibitem{msft_stab} E.~Choukse, B.~Warrier, S.~Heath, et al., ``Power stabilization for AI training datacenters,'' arXiv:2508.14318, 2025.
   269	\bibitem{easyrider} D.~Jensen, G.~Wilkins, O.~Nnorom~Jr., H.~Budd, R.~Rajagopal, J.~Rivas-Davila, and P.~Levis, ``EasyRider: Mitigating power transients in datacenter-scale training workloads,'' arXiv:2604.15522, 2026.
   270	\bibitem{activefilter} D.~Jensen, G.~Wilkins, O.~Nnorom~Jr., H.~Budd, P.~Levis, and J.~Rivas, ``Active filter design for buffering datacenter-scale power fluctuations from training AI,'' arXiv:2609.13490, 2026.
   271	\bibitem{hessdpc} H.~You, C.~Lou, and J.~Yang, ``Source side mitigation of AI datacenter power fluctuations with a hybrid energy storage system and residual differentiable predictive control,'' arXiv:2606.04869, 2026.
   272	\bibitem{lyu} X.~Lyu, W.~Du, S.~M.~Mohiuddin, and B.~A.~Ross, ``Communication delay robust control of BESS for AI training load smoothing,'' arXiv:2609.22542, 2026.
   273	\bibitem{mughees} M.~Mughees, Y.~Li, Y.~Chen, and Y.~R.~Li, ``Short-term load forecasting for AI-data center,'' arXiv:2503.07756, 2025 (accepted to IEEE PES General Meeting 2025).
   274	\bibitem{nlr} R.~Vercellino, J.~Willard, G.~Campos, W.~da~Silva~Pereira, O.~Hull, M.~Selensky, and J.~Mueller, ``Measurement of generative AI workload power profiles for whole-facility data center infrastructure planning,'' arXiv:2604.07345, 2026. Data: ``Dataset of Generative AI Workload Power Profiles,'' National Laboratory of the Rockies, doi:10.7799/3025227.
   275	\bibitem{elsayed} A.~A.~E.~Elsayed, A.~A.~Al-Obaidi, and H.~E.~Z.~Farag, ``Characterization of high-resolution AI data center training workloads on single and multiple GPU nodes,'' \emph{Scientific Data}, vol.~13, art.~1268, 2026, doi:10.1038/s41597-026-07496-6. Data: figshare, doi:10.6084/m9.figshare.31654879.
   276	\bibitem{supercloud} S.~Samsi, M.~L.~Weiss, D.~Bestor, et al., ``The MIT Supercloud dataset,'' in \emph{Proc. IEEE High Performance Extreme Computing Conf. (HPEC)}, 2021, pp.~1--8, doi:10.1109/HPEC49654.2021.9622850.
   277	\end{thebibliography}
   278	
   279	\end{document}

--- arxiv source ---
     1	\documentclass[11pt]{article}
     2	\usepackage{iftex}
     3	\ifPDFTeX
     4	  \usepackage[T1]{fontenc}
     5	  \usepackage{lmodern}
     6	\fi
     7	\usepackage[margin=1in]{geometry}
     8	\usepackage{graphicx}
     9	\usepackage{amsmath,amssymb}
    10	\usepackage{booktabs}
    11	\usepackage{multirow}
    12	\usepackage{url}
    13	\usepackage[hidelinks]{hyperref}
    14	\usepackage{caption}
    15	\usepackage[section,above]{placeins}
    16	\captionsetup{font=small}
    17	
    18	\title{Predict the Breach, Not the Drop:\\Control-Aligned Learning for Smoothing AI Training Power Swings}
    19	\author{Sayed Raheel\\\small Independent Researcher; Yeshiva University alumnus\\\small\texttt{shussai1@mail.yu.edu}}
    20	\date{}
    21	
    22	\begin{document}
    23	\maketitle
    24	
    25	\begin{abstract}
    26	Large AI training jobs move GPU power by tens of percent within a second, and synchronized jobs add
    27	these swings together into fast load ramps of the kind that ramp-rate limits on large loads are meant to
    28	prevent. Fill-type smoothing (filler GPU
    29	work or storage that adds power while the load falls) can remove these violations, but it has to be
    30	engaged before the fall arrives, and keeping it engaged costs energy. A forecaster can decide when to
    31	engage it. We show that what the forecaster is trained to predict matters.
    32	In a matched-pipeline ablation, a gradient-boosted classifier trained on a generic
    33	target, ``a large power drop is coming'', ranks the events a ramp limiter must catch poorly (average
    34	precision, AP, 0.58 on held-out NLR H100 data). Trained on the controller's own event,
    35	``a ramp-limit violation will occur while a limiter triggered now would be engaged'', the same pipeline
    36	reaches AP 0.96 (difference 95\% CI 0.28 to
    37	0.49), against 0.67 for a no-learning rhythm-replay baseline of the same
    38	target. In a limiter simulation with a threshold chosen on validation
    39	data for a 90\% removal target, the learned trigger removes 86.8\% of test violations
    40	with the actuator engaged 45.6\% of the time, while rhythm replay meets the target
    41	only by staying engaged 99.2\% of the time, i.e.\ effectively always on. Across
    42	three public datasets (H100, B200 and V100 nodes; scripted benchmarks and labelled cluster jobs), the learned trigger
    43	ranks violations significantly better than rhythm replay on two datasets when the site is represented in
    44	training (95\% cluster-bootstrap intervals exclude zero); the third is inconclusive. On a site never seen in training, the learned trigger is never
    45	better than rhythm replay in AP, and an hour of local data does not reliably recover the advantage. We
    46	report this as an open problem.
    47	\end{abstract}
    48	
    49	\section{Introduction}
    50	
    51	Training a large neural network alternates compute-heavy and communication-heavy phases, so GPU power
    52	moves in fast, large steps. Nodes in a synchronized data-parallel job step together, so their power
    53	changes add rather than cancel and the job can look to the grid like one large, fast swing. Industry reports describe swings of tens to hundreds of megawatts and
    54	evaluate software power burning, GPU power floors and rack-level storage as mitigations~\cite{msft_stab}.
    55	Hardware filters and storage that react to the measured load are being developed~\cite{easyrider,
    56	activefilter}; predictive storage control has been studied with perfect preview~\cite{hess} and with
    57	short delay-compensating predictors~\cite{delaycomp}; and AI data center load has been forecast at minute
    58	scales~\cite{stlf}.
    59	
    60	This paper studies one specific decision: \emph{when to engage} a fill-type actuator. The actuator (filler
    61	GPU kernels, a battery, a supercapacitor) adds power only while the load falls faster than the allowed
    62	ramp. It must be ready before the fall: kernels must be launched, an inverter must be hot. Readiness has a
    63	cost, so it should be engaged only when needed. A forecaster can make that call. The obvious competitor is
    64	free: training power is periodic, so ``replay the last cycle'' is a strong predictor.
    65	
    66	Our contributions are:
    67	\begin{itemize}
    68	\item \textbf{A control-aligned prediction target.} Instead of a generic ``large drop'', the label is the
    69	event the controller acts on: a ramp-limit violation whose whole 1~s ramp window lies inside the window
    70	during which a limiter triggered now would be armed. In a matched-pipeline ablation, retargeting raises AP from 0.58 to 0.96 on held-out NLR
    71	data (Section~\ref{sec:res-target}).
    72	\item \textbf{A readiness analysis} that puts learned triggers, rhythm replay, an always-on limiter and a
    73	perfect-foresight oracle on one curve of violations removed versus time engaged, with operating points
    74	chosen on validation data and scored on test data (Section~\ref{sec:res-ready}).
    75	\item \textbf{A three-dataset study} (H100, B200, V100; scripted benchmarks and labelled cluster jobs) with
    76	cluster-bootstrap confidence intervals, a sensor-harmonization step, and a \textbf{negative result}: a
    77	learned trigger did not transfer to an unseen site (Sections~\ref{sec:res-cross}--\ref{sec:res-unseen}).
    78	\end{itemize}
    79	We are not aware of prior work that studies how the forecasting target affects smoothing performance.
    80	
    81	\section{Data}
    82	\label{sec:data}
    83	
    84	\begin{table}[t]
    85	\centering
    86	\caption{Datasets. Node-hours are those used for modeling. Units are independent training jobs or sessions; each NLR inference benchmark is one session.}
    87	\label{tab:data}
    88	\footnotesize
    89	\begin{tabular}{@{}l l p{4.2cm} l r r@{}}
    90	\toprule
    91	Dataset & GPUs/node & Workloads & Sensor & Node-h & Units (test) \\
    92	\midrule
    93	NLR~\cite{nlr} & 4$\times$H100 & MLPerf Llama2-70B LoRA, SD; vLLM inference & NVML 5--10 Hz & 248 & 49 (12) \\
    94	Elsayed et al.~\cite{elsayed} & 8$\times$H100 / B200 & diffusion, Llama 1B--8B fine-tuning & NVML & 8 & 32 (6) \\
    95	MIT Supercloud~\cite{supercloud} & 1--2$\times$V100 & 7 model classes, labelled cluster jobs & nvidia-smi 10 Hz & 1,292 & 560 (112) \\
    96	\bottomrule
    97	\end{tabular}
    98	\end{table}
    99	
   100	Table~\ref{tab:data} summarizes the three public datasets.
   101	
   102	\textbf{NLR}~\cite{nlr} records 4$\times$H100 nodes running MLPerf Llama2-70B LoRA and Stable Diffusion
   103	training on 1 to 16 nodes, plus three vLLM Llama3.1-70B inference benchmarks (offline, online with a
   104	finite request set, online at a fixed rate). We keep at most four nodes per training job; these run
   105	nearly in lockstep and all are weighted equally in the metrics. Training jobs are split whole into train,
   106	validation and test. Each inference benchmark is a single continuous session, cut into one-hour blocks and
   107	split in time; its test blocks therefore count as a single independent cluster, which gives 12 test
   108	clusters in total.
   109	
   110	\textbf{Elsayed et al.}~\cite{elsayed} record single 8$\times$H100 and 8$\times$B200 nodes running diffusion
   111	training and Llama 1B--8B fine-tuning sweeps in 15-minute sessions (32 unique sessions).
   112	
   113	\textbf{MIT Supercloud}~\cite{supercloud}: we use a stratified subset of 560 labelled jobs, 80 per model
   114	class (VGG, ResNet, Inception, U-Net, BERT, DistilBERT, GNN), on two-V100 nodes (one or two GPU streams
   115	per trace; up to four retained nodes per job, 973 trace segments). These are scheduler-observed jobs on a shared
   116	cluster; the release uses open-source model implementations and public datasets, so they are not
   117	necessarily production workloads, but they are not scripted for power measurement.
   118	
   119	\textbf{Common preprocessing.} All traces are averaged onto a 0.2~s grid (row $t$ averages
   120	$[t, t+0.2\,\mathrm{s})$) and expressed as ``NLR-equivalent watts'': node GPU power times 2.8~kW divided by
   121	the node's rated GPU power (2.8~kW for 4$\times$H100, 5.6~kW for 8$\times$H100, 8.0~kW for 8$\times$B200 assuming 1~kW per
   122	B200, and an assumed 250~W per logged V100). We study an illustrative down-ramp threshold of 10\% of rated power per
   123	second, which therefore means the same thing on every node; it is not a specific utility's requirement. Jobs are assigned whole to train, validation and test (about 60/20/20, seed 42). For the
   124	control-aligned models the validation units are split again into two halves: one for early stopping and
   125	one for choosing operating points. For NLR inference, one-hour validation blocks are assigned to these halves after a seeded shuffle;
   126	they come from the same sessions and are not independent.
   127	
   128	\textbf{Sensor harmonization.} NVML documents that its default power reading is averaged over a 1~s
   129	interval on Ampere (except GA100) and newer GPUs, which includes the H100 and B200, while on GA100 and
   130	older architectures, including the V100, it returns instantaneous power~\cite{nvml}. The NLR
   131	documentation does not state which reading was logged. Raw V100 traces flicker: without harmonization,
   132	91\% of Supercloud test seconds would be labelled ``violation imminent''. We apply a 1~s trailing mean to
   133	Supercloud so that all three datasets are compared at a similar effective bandwidth. This is an
   134	assumption, discussed in Section~\ref{sec:limits}.
   135	
   136	\begin{figure}[t]
   137	\centering
   138	\includegraphics[width=0.6\textwidth]{fig_example.pdf}
   139	\caption{Sixty seconds of one NLR Llama2-70B LoRA test node. Red dots mark exceedances of the illustrative
   140	study threshold (1~s fall larger than 10\% of rated node power). Many are steps of a regular square wave rather than
   141	``big drops''.}
   142	\label{fig:example}
   143	\end{figure}
   144	
   145	\section{Problem and methods}
   146	\label{sec:methods}
   147	
   148	\subsection{Ramp limit, limiter and readiness}
   149	
   150	Let $p_t$ be node power at row $t$ (0.2~s steps) and $F=5$ the number of rows per second. A down-ramp
   151	violation starts at row $v$ when $p_{v-F} - p_v > 0.1\,P_{\mathrm{rated}}$ and this did not hold at $v-1$;
   152	its ramp window is $[v-F, v]$ (Fig.~\ref{fig:example}).
   153	
   154	The \emph{limiter} adds power only. When armed, or while still filling, its output is
   155	\begin{equation}
   156	o_t = \max\bigl(p_t,\; o_{t-1} - 0.9\cdot 0.1\,P_{\mathrm{rated}}/F\bigr),
   157	\end{equation}
   158	so it tapers at 90\% of the allowed rate (a safety margin) until it meets the load; otherwise $o_t = p_t$.
   159	
   160	A trigger issued at row $t$ acts after a one-row decision delay (row $t$ is complete only at $t+1$) and
   161	an actuator latency $L$ (1~s unless stated), so engagement starts at $e = t + 1 + L F$. Each trigger arms
   162	the limiter for the half-open window $[e, e+H)$ with hold $H$ = 6~s = 30 rows. We count as
   163	\emph{engaged} every row where the limiter is armed or still filling. Performance is the share of raw
   164	violations removed against the share of time engaged. The energy metric is the fill energy plus a standby
   165	draw (we report 0 and 2\% of rated power) while engaged, as a share of job energy. For filler compute this is
   166	extra consumption; for storage it is charge absorbed before any later discharge or loss, which we do not
   167	model.
   168	
   169	References: \emph{always-on} (always armed), \emph{always-burn} (a power floor at 80\% of the trailing 60~s peak, which removes only
   170	6.7\% of violations for 6.8\% extra energy), and an \emph{oracle} that arms just in
   171	time for every violation, iterating until violations induced by the limiter itself are also covered.
   172	
   173	\subsection{Targets}
   174	
   175	The \textbf{big-drop} target labels row $t$ positive if a big-drop onset lies in the next 5~s. An onset
   176	is a row where power falls by more than 30\% of the trailing 10~s peak within the following 1~s, with that
   177	peak at least 1~kW; candidates within 5~s after an onset are merged into it. The \textbf{control-aligned} target labels row $t$ positive if a raw
   178	violation starts at some $v$ with
   179	\begin{equation}
   180	v \in [e + F,\; e + H - 1], \qquad e = t + 1 + LF,
   181	\end{equation}
   182	that is, the whole ramp window $[v-F, v]$ lies inside the armed window $[e, e+H)$. Violations induced by
   183	the limiter itself are not labelled. Many violations are not big drops: the Llama LoRA workload is a
   184	square wave of about 22\% of rated power (Fig.~\ref{fig:example}), so the two targets differ
   185	substantially. We train one model per actuator latency $L \in \{0, 0.2, 0.5, 1, 2, 3\}$~s.
   186	
   187	\subsection{Predictors}
   188	
   189	\textbf{Rhythm replay} estimates the period $P$ from a trailing 120~s autocorrelation, recomputed every
   190	second: it searches lags of 2 to 40~s, requires a peak correlation of at least 0.3, and takes the first
   191	local peak within 90\% of the strongest (rows with no accepted period score zero). It predicts $\hat p_{t+k} = p_{t+k-P\lceil k/P\rceil}$, and scores row $t$ by the largest predicted
   192	1~s down-ramp whose window lies inside the same target window. It needs no training.
   193	
   194	The \textbf{learned} predictor is LightGBM~\cite{lightgbm} on 56 trailing features: current power, lags
   195	and differences over 0.2 to 20~s, rolling mean, standard deviation, minimum and maximum over 1 to 60~s,
   196	time since the last up-step, down-step and drop, autocorrelation and FFT rhythm estimates (period,
   197	strength, phase) and rhythm-replay forecasts at 1, 5 and 10~s. It uses learning rate 0.05, 63 leaves,
   198	at least 200 rows per leaf, 0.8 feature and row subsampling, $\ell_2$ penalty 1, square-root class
   199	weighting, seed 42, and at most 3000 rounds with 100-round early stopping (binary log-loss) on the
   200	early-stopping half of validation. For pooled and leave-one-dataset-out training each dataset receives
   201	equal total sample weight. The earlier big-drop classifier used in the readiness comparisons uses the same
   202	features, 100 rows per leaf, at most 2000 rounds and AP-based early stopping on all validation data; the
   203	matched ablation of Section~\ref{sec:res-target} removes these differences. A \textbf{shape-only} variant, used for transfer, divides every level feature by one watt plus the
   204	trailing 60~s maximum.
   205	
   206	\subsection{Evaluation}
   207	
   208	NLR models (Sections~\ref{sec:res-target} and \ref{sec:res-ready}) are trained on one row per second
   209	and scored on every 0.2~s row; cross-dataset models (Sections~\ref{sec:res-cross} and
   210	\ref{sec:res-unseen}) are trained and scored on one row per second. Ranking quality is AP on
   211	test rows. Uncertainty is a paired bootstrap over independent clusters
   212	(training jobs; each inference session is one cluster; 1000 resamples). The intervals resample test
   213	clusters for a single fitted model and split; they do not retrain, so they omit training and split
   214	variability. Operating points (thresholds) are chosen on the threshold half of validation and then
   215	scored on test. We call a difference significant when its 95\% interval excludes zero; intervals are
   216	not adjusted for multiple comparisons. For the readiness curves we sweep about 200 thresholds taken from validation-score
   217	quantiles.
   218	
   219	\section{Results}
   220	
   221	\subsection{The training target}
   222	\label{sec:res-target}
   223	
   224	On NLR test traces rhythm replay ranks the control-aligned event with AP 0.67. LightGBM trained
   225	on the control-aligned target reaches 0.96, and the gain over rhythm replay holds for every
   226	workload (Table~\ref{tab:wl}).
   227	
   228	\textbf{Matched label ablation.} To isolate the effect of the label, we train the big-drop label through
   229	the same pipeline as the control-aligned model: same training rows, features, fixed LightGBM settings,
   230	early-stopping half, stopping metric and square-root class-weighting rule. Because that rule depends on
   231	label prevalence, the numerical class weight changes with the label (1.75 for the aligned target versus 2.57 for the big-drop target). Scored on the control-aligned event, the
   232	big-drop model reaches AP 0.58 against 0.96 for the aligned model,
   233	a paired cluster-bootstrap difference of 0.37 (95\% CI 0.28 to
   234	0.49, 12 clusters). The big-drop model is not weak at its own task: on the big-drop
   235	event it reaches AP 0.93, where the aligned model reaches only
   236	0.48. The two labels describe different events, and each model is good
   237	at the one it was trained on. (The separately configured big-drop classifier from our earlier pipeline
   238	gives a similar 0.58 on the aligned event.)
   239	The inference workloads are hardest; their falls are dominated by the gaps between benchmark runs.
   240	Results barely depend on actuator latency (Table~\ref{tab:lat}): the regular structure that makes
   241	violations predictable 1~s ahead also makes them predictable 3~s ahead.
   242	
   243	\begin{table}[t]
   244	\centering
   245	\begin{minipage}[t]{0.55\textwidth}
   246	\centering
   247	\caption{NLR test AP on the control-aligned target, 1~s latency. Per-workload rows are point estimates;
   248	each inference workload is a single session, so no interval is computed.}
   249	\label{tab:wl}
   250	\small
   251	\begin{tabular}{@{}lcc@{}}
   252	\toprule
   253	Workload & Learned & Rhythm replay \\
   254	\midrule
   255	Llama2-70B LoRA training & 1.00 & 0.81 \\
   256	Stable Diffusion training & 0.96 & 0.73 \\
   257	Offline inference & 0.55 & 0.29 \\
   258	Online inference, finite & 0.76 & 0.09 \\
   259	Online inference, fixed rate & 0.65 & 0.36 \\
   260	\midrule
   261	All & 0.96 & 0.67 \\
   262	\bottomrule
   263	\end{tabular}
   264	\end{minipage}\hfill
   265	\begin{minipage}[t]{0.4\textwidth}
   266	\centering
   267	\caption{NLR test AP by actuator latency.}
   268	\label{tab:lat}
   269	\small
   270	\begin{tabular}{@{}rcc@{}}
   271	\toprule
   272	$L$ (s) & Learned & Rhythm \\
   273	\midrule
   274	0 & 0.96 & 0.68 \\
   275	0.2 & 0.96 & 0.68 \\
   276	0.5 & 0.96 & 0.68 \\
   277	1 & 0.96 & 0.67 \\
   278	2 & 0.96 & 0.67 \\
   279	3 & 0.95 & 0.67 \\
   280	\bottomrule
   281	\end{tabular}
   282	\end{minipage}
   283	\end{table}
   284	
   285	\subsection{Readiness on NLR}
   286	\label{sec:res-ready}
   287	
   288	Fig.~\ref{fig:ready} sweeps each trigger's threshold on NLR test traces. Every trigger can reach high
   289	removal by staying engaged long enough; what differs is how much engaged time it needs.
   290	
   291	\textbf{Validation-chosen operating points} are the deployable result (Table~\ref{tab:ops}). For a 90\%
   292	removal target, the learned control-aligned trigger removes 86.8\% of test violations
   293	at 45.6\% engaged time, slightly short of target. Rhythm replay reaches
   294	99.8\% only by staying engaged 99.2\% of the time,
   295	which is the always-on solution. With a 2\% standby draw the reported energy metrics are
   296	3.7\% and 5.4\% (always-on: 5.4\%).
   297	At an 80\% target both triggers undershoot on test (73.7\% and
   298	74.4\%): thresholds chosen on a few validation jobs transfer imperfectly. The
   299	perfect-foresight oracle removes all violations at 29.8\% engaged time. It is an iterative
   300	just-in-time heuristic rather than a proven minimum, but it indicates how much better prediction could
   301	still gain.
   302	
   303	\begin{table}[t]
   304	\centering
   305	\caption{Validation-chosen operating points scored on NLR test traces (1~s latency). Removal and engaged
   306	time in \%; reported energy metric in \% of baseline job energy with a 2\% standby draw.}
   307	\label{tab:ops}
   308	\small
   309	\begin{tabular}{@{}llccc@{}}
   310	\toprule
   311	Target & Trigger & Removed & Engaged & Energy metric \\
   312	\midrule
   313	\multirow{3}{*}{80\%} & Learned, aligned & 73.7 & 35.9 & 2.9 \\
   314	 & Rhythm, aligned & 74.4 & 43.3 & 3.2 \\
   315	 & Learned, big-drop & 88.0 & 61.4 & 4.3 \\
   316	\midrule
   317	\multirow{3}{*}{90\%} & Learned, aligned & 86.8 & 45.6 & 3.7 \\
   318	 & Rhythm, aligned & 99.8 & 99.2 & 5.4 \\
   319	 & Learned, big-drop & 92.7 & 69.1 & 4.6 \\
   320	\midrule
   321	\multirow{3}{*}{95\%} & Learned, aligned & 91.6 & 49.7 & 4.0 \\
   322	 & Rhythm, aligned & 99.8 & 99.2 & 5.4 \\
   323	 & Learned, big-drop & 95.4 & 75.8 & 4.8 \\
   324	\midrule
   325	 & Always-on & 100.0 & 100.0 & 5.4 \\
   326	 & Oracle & 100.0 & 29.8 & 3.6 \\
   327	\bottomrule
   328	\end{tabular}
   329	\end{table}
   330	
   331	\textbf{Attainable trade-offs (retrospective).} Table~\ref{tab:arm} reads, from each test curve, the least
   332	engaged time at which a removal level is reached. Because the threshold is picked on test, this compares
   333	attainable trade-offs rather than deployable operating points. To remove 90\% of violations the learned
   334	control-aligned trigger needs 48.4\% engaged time and rhythm replay
   335	99.2\%: a paired cluster-bootstrap difference of $-$50.8
   336	points (95\% CI $-$57.4 to $-$8.8). The interval is
   337	asymmetric because the statistic is a minimum over thresholds: in most resamples rhythm replay needs more
   338	than 95\% engagement, but some cluster mixtures cross 90\% removal at 50--80\%. At 95\% removal the
   339	difference is $-$40.8 points (CI $-$49.1 to
   340	$-$31.4). Against the learned big-drop trigger the difference is
   341	$-$15.9 points at 90\% (CI $-$25.7 to $-$3.9)
   342	but not significant at 95\% (CI $-$26.3 to 0.5); with 12 test
   343	clusters the effect of the target is clearest in ranking quality.
   344	
   345	\begin{table}[t]
   346	\centering
   347	\caption{Retrospective: least engaged time (\%) on the NLR test curve that reaches each removal level,
   348	1~s latency. Thresholds are read off the test curve.}
   349	\label{tab:arm}
   350	\small
   351	\begin{tabular}{@{}lccc@{}}
   352	\toprule
   353	Removal & Learned, aligned & Rhythm, aligned & Learned, big-drop \\
   354	\midrule
   355	80\% & 43.1 & 51.5 & 53.0 \\
   356	90\% & 48.4 & 99.2 & 64.3 \\
   357	95\% & 58.4 & 99.2 & 74.8 \\
   358	\bottomrule
   359	\end{tabular}
   360	\end{table}
   361	
   362	\begin{figure}[t]
   363	\centering
   364	\includegraphics[width=0.6\textwidth]{fig_readiness.pdf}
   365	\caption{Violations removed versus engaged time on NLR test traces (1~s latency, about 200 thresholds from
   366	validation-score quantiles). Always-on removes everything but is always engaged; the star is the iterative
   367	perfect-foresight oracle.}
   368	\label{fig:ready}
   369	\end{figure}
   370	
   371	\subsection{Across sites and GPUs}
   372	\label{sec:res-cross}
   373	
   374	Table~\ref{tab:cross} and Fig.~\ref{fig:forest} compare AP in three configurations: trained on the test
   375	site's own training jobs (in-domain), trained on all three datasets (pooled), and trained on the other two
   376	only (unseen site). In-domain or pooled, the learned trigger ranks violations significantly better than
   377	rhythm replay on NLR and on Supercloud. On Supercloud, exploratory per-class intervals (not
   378	corrected for multiplicity) are positive for 7 of 7 model classes. On
   379	Elsayed the point estimate favours learning but the interval includes zero with only six test sessions,
   380	and rhythm replay is better on its two diffusion test sessions; their very regular cadence may suit
   381	replay, but two sessions do not allow a firm conclusion.
   382	
   383	\begin{table}[t]
   384	\centering
   385	\caption{Test AP, learned versus rhythm replay, with the 95\% cluster-bootstrap interval of the
   386	difference. Unseen site uses the ordinary features (shape-only results in Table~\ref{tab:transfer}).}
   387	\label{tab:cross}
   388	\small
   389	\begin{tabular}{@{}llccc@{}}
   390	\toprule
   391	Test dataset & Training data & Learned & Rhythm & Difference CI \\
   392	\midrule
   393	\multirow{3}{*}{NLR} & in-domain & 0.96 & 0.67 & [0.22, 0.36] \\
   394	 & pooled & 0.96 & 0.67 & [0.22, 0.37] \\
   395	 & unseen site & 0.53 & 0.67 & [$-$0.23, $-$0.02] \\
   396	\midrule
   397	\multirow{3}{*}{Supercloud} & in-domain & 0.88 & 0.74 & [0.11, 0.19] \\
   398	 & pooled & 0.88 & 0.74 & [0.11, 0.18] \\
   399	 & unseen site & 0.68 & 0.74 & [$-$0.10, $-$0.02] \\
   400	\midrule
   401	\multirow{3}{*}{Elsayed} & in-domain & 0.93 & 0.88 & [$-$0.11, 0.09] \\
   402	 & pooled & 0.92 & 0.88 & [$-$0.13, 0.08] \\
   403	 & unseen site & 0.84 & 0.88 & [$-$0.43, 0.05] \\
   404	\bottomrule
   405	\end{tabular}
   406	\end{table}
   407	
   408	\begin{figure}[t]
   409	\centering
   410	\includegraphics[width=0.6\textwidth]{fig_forest.pdf}
   411	\caption{AP difference, learned control-aligned trigger minus rhythm replay, with 95\% cluster-bootstrap
   412	intervals. Red: learned significantly better; blue: rhythm significantly better; grey: inconclusive. The
   413	unseen-site rows use shape-only features.}
   414	\label{fig:forest}
   415	\end{figure}
   416	
   417	AP is a ranking measure, not a smoothing result. Table~\ref{tab:xready} reports validation-chosen
   418	operating points for a 90\% removal target on each dataset (one decision per second, no confidence
   419	intervals). The learned trigger lands below target on Elsayed and slightly below on the others; rhythm
   420	replay meets the target on NLR and Supercloud only by staying engaged almost all the time, and misses it

--- prior review ---
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

exec
/bin/zsh -lc "nl -ba paper/main.tex | sed -n '120,420p'
printf '\\n--- ablation ---\\n'; jq . data/processed/ablation_info.json
printf '\\n--- csv contents ---\\n'; for f in reports/*.csv reports/tables/*.csv; do [ -f \""'$f" ] || continue; printf '"'\\n### %s\\n' \""'$f"; sed -n '"'1,40p' \""'$f"; done
printf '"'\\n--- json tables ---\\n'; for f in reports/tables/*.json paper/numbers.json; do printf '\\n### %s\\n' \""'$f"; jq . "$f"; done' in /Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing
 exited 1 in 0ms:
   120	(lags, differences, rolling statistics, time since recent steps and drops, rhythm period, phase and
   121	rhythm forecasts), one model per actuator latency. A shape-only variant divides every level feature by
   122	the trailing 60~s maximum.
   123	
   124	\subsection{Evaluation}
   125	Ranking quality is average precision (AP) on test rows. Uncertainty is a paired bootstrap over
   126	independent clusters (training jobs, or inference sessions; 1000 resamples). Operating points are chosen
   127	on the validation threshold half and scored on test. All intervals are conditional on the single fitted
   128	model and split: they resample test clusters but do not retrain. Cross-dataset comparisons score one
   129	decision per second; the NLR readiness analysis scores every 0.2~s row.
   130	
   131	\section{Results}
   132	\subsection{Training target}
   133	On NLR test traces, rhythm replay ranks the control-aligned event with AP 0.67; LightGBM trained
   134	on the control-aligned target reaches 0.96, and the gain holds for each workload (Table~\ref{tab:wl}).
   135	\emph{Matched label ablation.} Training the big-drop label through the same pipeline (same rows, features,
   136	LightGBM settings, early-stopping data and metric, and square-root class-weighting rule, which gives weight
   137	1.75 for the aligned and 2.57 for the big-drop target) yields AP 0.58 on the aligned event
   138	against 0.96, a paired cluster-bootstrap difference of 0.37 (95\% CI
   139	0.28 to 0.49, 12 clusters). The big-drop model is good at its own task
   140	(AP 0.93 on the big-drop event, where the aligned model reaches
   141	0.48): the two labels describe different events.
   142	Results are stable across actuator latencies (AP 0.96 at 0~s, 0.95
   143	at 3~s; rhythm replay 0.68 and 0.67).
   144	
   145	\begin{table}[t]
   146	\centering
   147	\caption{NLR test AP on the control-aligned target (1~s latency).}
   148	\label{tab:wl}
   149	\begin{tabular}{lcc}
   150	\toprule
   151	Workload & Learned & Rhythm replay\\
   152	\midrule
   153	Llama2-70B LoRA training & 1.00 & 0.81\\
   154	Stable Diffusion training & 0.96 & 0.73\\
   155	Offline inference & 0.55 & 0.29\\
   156	Online inference, finite & 0.76 & 0.09\\
   157	Online inference, fixed rate & 0.65 & 0.36\\
   158	\bottomrule
   159	\end{tabular}
   160	\end{table}
   161	
   162	\subsection{Readiness}
   163	Fig.~\ref{fig:ready} sweeps each trigger's threshold (about 200 validation-score quantiles) on NLR test
   164	traces. Every trigger can reach high removal by staying engaged long enough; what differs is the engaged
   165	time needed (Table~\ref{tab:arm}). Table~\ref{tab:arm} reads the best threshold off each test curve, so
   166	it is a retrospective comparison of attainable trade-offs, not a deployable operating point; the
   167	validation-chosen operating points follow below.
   168	To remove 90\% of violations, the control-aligned learned trigger needs 48.4\%
   169	engaged time, whereas rhythm replay of the same target reaches 90\% only at 99.2\%,
   170	i.e.\ it is no better than always-on. The paired cluster-bootstrap difference is
   171	$-$50.8 points (95\% CI $-$57.4 to
   172	$-$8.8), and $-$40.8 points at 95\% removal (CI
   173	$-$49.1 to $-$31.4). The learned big-drop trigger
   174	needs more engaged time than the control-aligned one (64.3\% at 90\%; difference
   175	$-$15.9 points, CI $-$25.7 to $-$3.9). At 95\%
   176	removal the interval includes zero (CI $-$26.3 to 0.5), so with
   177	12 test clusters the target's effect is clearest in ranking quality (AP 0.58 vs 0.96). The oracle removes all violations at 29.8\% engaged time, which bounds what
   178	better prediction could still gain.
   179	
   180	\begin{table}[t]
   181	\centering
   182	\caption{Engaged time (\% of time) needed to reach a violation-removal level, NLR test, 1~s latency.}
   183	\label{tab:arm}
   184	\begin{tabular}{lccc}
   185	\toprule
   186	Removal & Learned, aligned & Rhythm, aligned & Learned, big-drop\\
   187	\midrule
   188	80\% & 43.1 & 51.5 & 53.0\\
   189	90\% & 48.4 & 99.2 & 64.3\\
   190	95\% & 58.4 & 99.2 & 74.8\\
   191	\bottomrule
   192	\end{tabular}
   193	\end{table}
   194	
   195	\begin{figure}[t]
   196	\centering
   197	\includegraphics[width=\columnwidth]{fig_readiness.pdf}
   198	\caption{Violations removed versus engaged time on NLR test traces (1~s latency, dense threshold sweep).
   199	Always-on removes everything but is always engaged.}
   200	\label{fig:ready}
   201	\end{figure}
   202	
   203	With operating points chosen on validation and a standby draw of 2\% of rated power, a 90\% target
   204	gives 86.8\% removal at 45.6\% engaged time and
   205	3.7\% energy overhead for the learned trigger; rhythm replay meets the target only
   206	by staying engaged 99.2\% of the time (5.4\%
   207	overhead, versus 5.4\% for always-on). At an 80\% target the validation-chosen
   208	learned threshold undershoots on test (73.7\% removal), a reminder that operating
   209	points chosen on few validation jobs transfer imperfectly.
   210	
   211	\subsection{Across sites and GPUs}
   212	Fig.~\ref{fig:forest} summarizes the learned-minus-rhythm AP difference. Trained on the test site's own
   213	training jobs (in-domain) or on all three datasets (pooled), the learned trigger significantly beats
   214	rhythm replay on NLR (pooled AP 0.96 vs 0.67) and on real Supercloud jobs
   215	(pooled 0.88 vs 0.74; exploratory per-class intervals, without multiplicity correction, are
   216	positive for 7 of 7 model classes). On Elsayed the point estimate favours learning
   217	(0.92 vs 0.88) but the interval includes zero with six test
   218	sessions, and rhythm replay is better on its diffusion sessions; we hypothesize that their very regular
   219	cadence suits replay, but two test sessions do not allow a firm conclusion.
   220	
   221	\begin{figure}[t]
   222	\centering
   223	\includegraphics[width=\columnwidth]{fig_forest.pdf}
   224	\caption{AP difference between the learned control-aligned trigger and rhythm replay, with 95\%
   225	cluster bootstrap intervals. Red: learned significantly better; blue: rhythm significantly better.}
   226	\label{fig:forest}
   227	\end{figure}
   228	
   229	\subsection{Unseen sites}
   230	When the test dataset is excluded from training, the learned trigger is not better than rhythm replay
   231	anywhere. With shape-only features it reaches AP 0.65 on NLR (rhythm
   232	0.67, CI of difference $-$0.06 to 0.02),
   233	0.85 on Elsayed (rhythm 0.88), and
   234	0.66 on Supercloud, significantly below rhythm replay
   235	(0.74; CI $-$0.12 to $-$0.04).
   236	Continuing to train on 60 minutes of the new site's data (mean of five independent draws) gives
   237	0.71 on NLR (range 0.62 to
   238	0.77) and 0.64 on Supercloud (range
   239	0.58 to 0.69), so a short
   240	calibration period does not reliably recover the in-domain advantage. Rhythm replay needs no site data;
   241	in our experiments a learned trigger needed the site in its training set.
   242	
   243	\section{Discussion and limitations}
   244	\emph{Sensors.} If NLR and Elsayed power is NVML's 1~s average, true ramps are faster than measured and
   245	measured lead times are optimistic. \emph{Simulation.} The actuator is an idealized limiter with fixed
   246	latency, hold time and standby draw; storage capacity, state of charge, efficiency and wear are not modelled, and standby cost is an
   247	assumed fraction of rated power.
   248	\emph{Workloads.} NLR and Elsayed are scripted benchmarks; NLR inference falls are dominated by gaps
   249	between benchmark runs, and each NLR inference workload is a single session. Supercloud adds real jobs
   250	on older V100 nodes. \emph{Scale.} Results are per node; synchronized multi-node jobs scale the same
   251	swing, while desynchronized jobs partly cancel. \emph{Licences.} Supercloud is CC BY-NC-ND and the Elsayed
   252	archive README states CC BY-NC-ND; both were used for research only and are not redistributed.
   253	
   254	\section{Conclusion}
   255	For fill-type smoothing of AI power swings, a forecaster should be trained on the controller's event, a
   256	ramp-limit violation inside the actuator's engagement window, rather than on a generic large drop. With
   257	that target a small gradient-boosted model needs substantially less engaged time than rhythm replay for
   258	the same violation removal on H100 benchmark traces, and ranks violations better (higher AP) on real
   259	V100 jobs, provided the site is represented in training. Closing the gap to the oracle and making learned triggers transfer to
   260	new sites are the natural next steps.
   261	
   262	\section*{Code availability and use of AI tools}
   263	Code is available from the author on request; the datasets are public from their original sources.
   264	Analysis code and text were drafted with the help of AI coding and writing assistants and independently
   265	reviewed by a separate AI model. The author checked the results and is responsible for the content.
   266	
   267	\begin{thebibliography}{9}
   268	\bibitem{msft_stab} E.~Choukse, B.~Warrier, S.~Heath, et al., ``Power stabilization for AI training datacenters,'' arXiv:2508.14318, 2025.
   269	\bibitem{easyrider} D.~Jensen, G.~Wilkins, O.~Nnorom~Jr., H.~Budd, R.~Rajagopal, J.~Rivas-Davila, and P.~Levis, ``EasyRider: Mitigating power transients in datacenter-scale training workloads,'' arXiv:2604.15522, 2026.
   270	\bibitem{activefilter} D.~Jensen, G.~Wilkins, O.~Nnorom~Jr., H.~Budd, P.~Levis, and J.~Rivas, ``Active filter design for buffering datacenter-scale power fluctuations from training AI,'' arXiv:2609.13490, 2026.
   271	\bibitem{hessdpc} H.~You, C.~Lou, and J.~Yang, ``Source side mitigation of AI datacenter power fluctuations with a hybrid energy storage system and residual differentiable predictive control,'' arXiv:2606.04869, 2026.
   272	\bibitem{lyu} X.~Lyu, W.~Du, S.~M.~Mohiuddin, and B.~A.~Ross, ``Communication delay robust control of BESS for AI training load smoothing,'' arXiv:2609.22542, 2026.
   273	\bibitem{mughees} M.~Mughees, Y.~Li, Y.~Chen, and Y.~R.~Li, ``Short-term load forecasting for AI-data center,'' arXiv:2503.07756, 2025 (accepted to IEEE PES General Meeting 2025).
   274	\bibitem{nlr} R.~Vercellino, J.~Willard, G.~Campos, W.~da~Silva~Pereira, O.~Hull, M.~Selensky, and J.~Mueller, ``Measurement of generative AI workload power profiles for whole-facility data center infrastructure planning,'' arXiv:2604.07345, 2026. Data: ``Dataset of Generative AI Workload Power Profiles,'' National Laboratory of the Rockies, doi:10.7799/3025227.
   275	\bibitem{elsayed} A.~A.~E.~Elsayed, A.~A.~Al-Obaidi, and H.~E.~Z.~Farag, ``Characterization of high-resolution AI data center training workloads on single and multiple GPU nodes,'' \emph{Scientific Data}, vol.~13, art.~1268, 2026, doi:10.1038/s41597-026-07496-6. Data: figshare, doi:10.6084/m9.figshare.31654879.
   276	\bibitem{supercloud} S.~Samsi, M.~L.~Weiss, D.~Bestor, et al., ``The MIT Supercloud dataset,'' in \emph{Proc. IEEE High Performance Extreme Computing Conf. (HPEC)}, 2021, pp.~1--8, doi:10.1109/HPEC49654.2021.9622850.
   277	\end{thebibliography}
   278	
   279	\end{document}

--- ablation ---
{
  "matched_aligned_ap": 0.9584076057131854,
  "matched_drop_ap": 0.5834481258924112,
  "matched_aligned_best_iter": 1172,
  "matched_drop_best_iter": 1016,
  "clusters": 12,
  "matched_diff": 0.37495947982077416,
  "matched_diff_lo": 0.27697394369975403,
  "matched_diff_hi": 0.49313199048791173,
  "matched_drop_ap_on_drop_label": 0.928417277013083,
  "matched_aligned_ap_on_drop_label": 0.4752888061387732
}

--- csv contents ---
zsh:3: no matches found: reports/*.csv

exec
/bin/zsh -lc "for f in reports/tables/*.csv; do printf '\\n### %s\\n' \""'$f"; sed -n '"'1,80p' \""'$f"; done
printf '"'\\n--- json ---\\n'; for f in reports/tables/*.json paper/numbers.json; do printf '\\n### %s\\n' \""'$f"; jq -c . "$f"; done
printf '"'\\n--- pdf info/text ---\\n'; pdfinfo paper/main.pdf | sed -n '1,30p'; pdftotext -layout paper/main.pdf - | sed -n '1,420p'
printf '\\n--- log/warnings if present ---\\n'; find paper -maxdepth 1 -type f \\( -name '*.log' -o -name '*.blg' \\) -print -exec sh -c 'rg -n \"Warning|Overfull|Underfull|undefined|Error\" \""'$1"'"' _ {} \\;" in /Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing
 succeeded in 42ms:

### reports/tables/crossdata_ap_harmonized.csv
config,test_dataset,workload,ap_ml,ap_rhythm,pos_rate,units,ap_diff,ap_diff_lo,ap_diff_hi
in_domain,nlr,all,0.9579,0.6747,0.2497,12,0.2833,0.2151,0.3645
in_domain,nlr,train_llama2_70b_lora,0.997,0.8065,0.4143,4,0.1905,0.1709,0.2115
in_domain,nlr,train_stable_diffusion,0.9609,0.7287,0.2064,5,0.2322,0.1965,0.3257
in_domain,elsayed,all,0.9341,0.8829,0.5199,6,0.0512,-0.1099,0.0865
in_domain,elsayed,elsayed_diffusion,0.6964,0.8341,0.3171,2,-0.1377,-0.4491,-0.1048
in_domain,elsayed,elsayed_llm_finetune,0.9752,0.9012,0.6214,4,0.0741,-0.0735,0.0956
in_domain,supercloud,all,0.8793,0.7357,0.4782,112,0.1436,0.1067,0.1877
in_domain,supercloud,sc_bert,0.8715,0.744,0.4831,16,0.1275,0.0264,0.3503
in_domain,supercloud,sc_distilbert,0.7375,0.0996,0.075,16,0.6379,0.2355,0.7239
in_domain,supercloud,sc_gnn,0.9524,0.8788,0.4102,16,0.0735,0.0185,0.1074
in_domain,supercloud,sc_inception,0.9543,0.898,0.7349,16,0.0563,0.0257,0.0993
in_domain,supercloud,sc_resnet,0.5717,0.3751,0.3381,16,0.1966,0.0929,0.3184
in_domain,supercloud,sc_unet,0.7969,0.6908,0.5309,16,0.1061,0.0583,0.14
in_domain,supercloud,sc_vgg,0.8178,0.6695,0.4886,16,0.1482,0.0699,0.2179
lodo,nlr,all,0.5311,0.6747,0.2497,12,-0.1435,-0.2345,-0.018
lodo,nlr,train_llama2_70b_lora,0.7225,0.8065,0.4143,4,-0.084,-0.1329,-0.0384
lodo,nlr,train_stable_diffusion,0.4829,0.7287,0.2064,5,-0.2458,-0.3284,-0.114
lodo,elsayed,all,0.8382,0.8829,0.5199,6,-0.0446,-0.4251,0.0461
lodo,elsayed,elsayed_diffusion,0.3808,0.8341,0.3171,2,-0.4532,-0.4897,-0.4293
lodo,elsayed,elsayed_llm_finetune,0.9227,0.9012,0.6214,4,0.0215,-0.1618,0.048
lodo,supercloud,all,0.6758,0.7357,0.4782,112,-0.0599,-0.1014,-0.0205
lodo,supercloud,sc_bert,0.5308,0.744,0.4831,16,-0.2132,-0.316,-0.0621
lodo,supercloud,sc_distilbert,0.114,0.0996,0.075,16,0.0144,0.0038,0.0408
lodo,supercloud,sc_gnn,0.7949,0.8788,0.4102,16,-0.0839,-0.2052,-0.0149
lodo,supercloud,sc_inception,0.8508,0.898,0.7349,16,-0.0471,-0.0873,-0.0055
lodo,supercloud,sc_resnet,0.4581,0.3751,0.3381,16,0.0831,0.0073,0.1546
lodo,supercloud,sc_unet,0.646,0.6908,0.5309,16,-0.0448,-0.1207,0.0089
lodo,supercloud,sc_vgg,0.6457,0.6695,0.4886,16,-0.0238,-0.0836,0.0228
pooled,nlr,all,0.9606,0.6747,0.2497,12,0.2859,0.2185,0.3738
pooled,nlr,train_llama2_70b_lora,0.9967,0.8065,0.4143,4,0.1902,0.1705,0.2118
pooled,nlr,train_stable_diffusion,0.9712,0.7287,0.2064,5,0.2425,0.1978,0.3511
pooled,elsayed,all,0.9169,0.8829,0.5199,6,0.034,-0.1323,0.0841
pooled,elsayed,elsayed_diffusion,0.6553,0.8341,0.3171,2,-0.1788,-0.4887,-0.161
pooled,elsayed,elsayed_llm_finetune,0.9725,0.9012,0.6214,4,0.0713,-0.1152,0.094
pooled,supercloud,all,0.8766,0.7357,0.4782,112,0.1409,0.1057,0.1824
pooled,supercloud,sc_bert,0.8751,0.744,0.4831,16,0.1311,0.03,0.3296
pooled,supercloud,sc_distilbert,0.7289,0.0996,0.075,16,0.6293,0.239,0.7187
pooled,supercloud,sc_gnn,0.9442,0.8788,0.4102,16,0.0654,0.018,0.1083
pooled,supercloud,sc_inception,0.9533,0.898,0.7349,16,0.0553,0.0269,0.1002
pooled,supercloud,sc_resnet,0.5641,0.3751,0.3381,16,0.189,0.084,0.3141
pooled,supercloud,sc_unet,0.7932,0.6908,0.5309,16,0.1024,0.0518,0.1351
pooled,supercloud,sc_vgg,0.8133,0.6695,0.4886,16,0.1438,0.0699,0.2095

### reports/tables/crossdata_ap_raw.csv
config,test_dataset,workload,ap_ml,ap_rhythm,pos_rate,units,ap_diff,ap_diff_lo,ap_diff_hi
in_domain,nlr,all,0.9386,0.5798,0.1621,20,0.3588,0.3168,0.4208
in_domain,nlr,inference_offline,0.4154,0.1966,0.199,3,0.2188,0.2064,0.232
in_domain,nlr,inference_online_finite,0.7154,0.0625,0.0625,4,0.6529,0.63,0.6854
in_domain,nlr,inference_online_rate,0.4853,0.259,0.1232,4,0.2263,0.1143,0.2836
in_domain,nlr,train_llama2_70b_lora,0.9952,0.7329,0.2655,4,0.2623,0.2362,0.2867
in_domain,nlr,train_stable_diffusion,0.9483,0.6346,0.1335,5,0.3137,0.2791,0.3944
in_domain,elsayed,all,0.8859,0.7687,0.3573,6,0.1172,-0.0597,0.1633
in_domain,elsayed,elsayed_diffusion,0.7204,0.7657,0.2056,2,-0.0452,-0.0643,-0.0152
in_domain,elsayed,elsayed_llm_finetune,0.9016,0.7656,0.4332,4,0.136,-0.0074,0.1678
in_domain,supercloud,all,0.9929,0.9685,0.8929,112,0.0244,0.0107,0.0427
in_domain,supercloud,sc_bert,0.9911,0.9867,0.9621,16,0.0044,-0.002,0.0213
in_domain,supercloud,sc_distilbert,0.8261,0.7461,0.6434,16,0.0801,0.0631,0.0939
in_domain,supercloud,sc_gnn,0.9706,0.9092,0.6642,16,0.0614,-0.0134,0.1486
in_domain,supercloud,sc_inception,0.9993,0.9982,0.9944,16,0.0011,0.0003,0.0023
in_domain,supercloud,sc_resnet,0.9893,0.888,0.8219,16,0.1013,0.0125,0.2136
in_domain,supercloud,sc_unet,0.9976,0.9936,0.9498,16,0.004,0.0003,0.0074
in_domain,supercloud,sc_vgg,0.9933,0.9939,0.9922,16,-0.0006,-0.005,0.0042
lodo,nlr,all,0.5159,0.5798,0.1621,20,-0.064,-0.1512,0.0825
lodo,nlr,inference_offline,0.1866,0.1966,0.199,3,-0.01,-0.0152,-0.0008
lodo,nlr,inference_online_finite,0.1195,0.0625,0.0625,4,0.057,0.0412,0.075
lodo,nlr,inference_online_rate,0.1467,0.259,0.1232,4,-0.1123,-0.1785,-0.0357
lodo,nlr,train_llama2_70b_lora,0.6394,0.7329,0.2655,4,-0.0935,-0.1776,-0.016
lodo,nlr,train_stable_diffusion,0.787,0.6346,0.1335,5,0.1524,0.1115,0.2144
lodo,elsayed,all,0.6341,0.7687,0.3573,6,-0.1346,-0.2927,-0.0971
lodo,elsayed,elsayed_diffusion,0.4328,0.7657,0.2056,2,-0.3329,-0.3899,-0.1728
lodo,elsayed,elsayed_llm_finetune,0.6584,0.7656,0.4332,4,-0.1071,-0.1351,-0.0796
lodo,supercloud,all,0.9747,0.9685,0.8929,112,0.0062,-0.0029,0.0156
lodo,supercloud,sc_bert,0.9821,0.9867,0.9621,16,-0.0046,-0.0085,0.0101
lodo,supercloud,sc_distilbert,0.7385,0.7461,0.6434,16,-0.0076,-0.0483,0.0378
lodo,supercloud,sc_gnn,0.8903,0.9092,0.6642,16,-0.0189,-0.1963,0.059
lodo,supercloud,sc_inception,0.9978,0.9982,0.9944,16,-0.0004,-0.0014,0.0005
lodo,supercloud,sc_resnet,0.9469,0.888,0.8219,16,0.0588,-0.0008,0.1649
lodo,supercloud,sc_unet,0.9958,0.9936,0.9498,16,0.0022,0.0005,0.0039
lodo,supercloud,sc_vgg,0.9946,0.9939,0.9922,16,0.0008,-0.0014,0.0021
pooled,nlr,all,0.9186,0.5798,0.1621,20,0.3388,0.2999,0.3721
pooled,nlr,inference_offline,0.2072,0.1966,0.199,3,0.0106,0.0084,0.0126
pooled,nlr,inference_online_finite,0.5024,0.0625,0.0625,4,0.4399,0.3655,0.5196
pooled,nlr,inference_online_rate,0.3244,0.259,0.1232,4,0.0654,-0.0165,0.1245
pooled,nlr,train_llama2_70b_lora,0.9923,0.7329,0.2655,4,0.2594,0.239,0.2795
pooled,nlr,train_stable_diffusion,0.9452,0.6346,0.1335,5,0.3106,0.2709,0.3871
pooled,elsayed,all,0.8571,0.7687,0.3573,6,0.0884,-0.1621,0.1586
pooled,elsayed,elsayed_diffusion,0.6965,0.7657,0.2056,2,-0.0691,-0.2028,-0.0691
pooled,elsayed,elsayed_llm_finetune,0.8768,0.7656,0.4332,4,0.1112,-0.174,0.1706
pooled,supercloud,all,0.9936,0.9685,0.8929,112,0.0251,0.0128,0.0456
pooled,supercloud,sc_bert,0.9932,0.9867,0.9621,16,0.0065,0.0008,0.0249
pooled,supercloud,sc_distilbert,0.8198,0.7461,0.6434,16,0.0737,0.0466,0.0873
pooled,supercloud,sc_gnn,0.9722,0.9092,0.6642,16,0.063,-0.0066,0.1598
pooled,supercloud,sc_inception,0.9994,0.9982,0.9944,16,0.0012,0.0004,0.0024
pooled,supercloud,sc_resnet,0.987,0.888,0.8219,16,0.0989,0.0105,0.2297
pooled,supercloud,sc_unet,0.9978,0.9936,0.9498,16,0.0042,0.0002,0.0086
pooled,supercloud,sc_vgg,0.995,0.9939,0.9922,16,0.0012,-0.0019,0.0038

### reports/tables/crossdata_readiness_harmonized.csv
config,test_dataset,source,target,val_reached,test_cut_pct,test_armed_pct
in_domain,nlr,learned,80.0,True,74.525,34.76
in_domain,nlr,learned,90.0,True,87.882,43.975
in_domain,nlr,learned,95.0,True,91.974,48.464
in_domain,nlr,rhythm,80.0,True,74.513,41.705
in_domain,nlr,rhythm,90.0,True,99.783,99.149
in_domain,nlr,rhythm,95.0,True,99.783,99.149
in_domain,elsayed,learned,80.0,True,67.254,39.698
in_domain,elsayed,learned,90.0,True,81.057,53.111
in_domain,elsayed,learned,95.0,True,88.693,68.49
in_domain,elsayed,rhythm,80.0,True,66.226,50.929
in_domain,elsayed,rhythm,90.0,True,67.254,51.766
in_domain,elsayed,rhythm,95.0,True,91.336,69.742
in_domain,supercloud,learned,80.0,True,77.817,42.454
in_domain,supercloud,learned,90.0,True,88.322,54.18
in_domain,supercloud,learned,95.0,True,95.626,66.04
in_domain,supercloud,rhythm,80.0,True,99.8,99.306
in_domain,supercloud,rhythm,90.0,True,99.8,99.306
in_domain,supercloud,rhythm,95.0,True,99.8,99.306
lodo,nlr,learned,80.0,True,73.634,43.585
lodo,nlr,learned,90.0,True,90.277,58.043
lodo,nlr,learned,95.0,True,95.596,66.973
lodo,nlr,rhythm,80.0,True,74.513,41.705
lodo,nlr,rhythm,90.0,True,99.783,99.149
lodo,nlr,rhythm,95.0,True,99.783,99.149
lodo,elsayed,learned,80.0,True,74.89,47.186
lodo,elsayed,learned,90.0,True,83.994,53.881
lodo,elsayed,learned,95.0,True,90.015,67.553
lodo,elsayed,rhythm,80.0,True,66.226,50.929
lodo,elsayed,rhythm,90.0,True,67.254,51.766
lodo,elsayed,rhythm,95.0,True,91.336,69.742
lodo,supercloud,learned,80.0,True,82.763,64.974
lodo,supercloud,learned,90.0,True,92.77,80.533
lodo,supercloud,learned,95.0,True,97.015,89.777
lodo,supercloud,rhythm,80.0,True,99.8,99.306
lodo,supercloud,rhythm,90.0,True,99.8,99.306
lodo,supercloud,rhythm,95.0,True,99.8,99.306
pooled,nlr,learned,80.0,True,74.561,36.026
pooled,nlr,learned,90.0,True,88.183,44.05
pooled,nlr,learned,95.0,True,93.165,48.907
pooled,nlr,rhythm,80.0,True,74.513,41.705
pooled,nlr,rhythm,90.0,True,99.783,99.149
pooled,nlr,rhythm,95.0,True,99.783,99.149
pooled,elsayed,learned,80.0,True,81.645,51.215
pooled,elsayed,learned,90.0,True,83.407,55.399
pooled,elsayed,learned,95.0,True,86.784,61.413
pooled,elsayed,rhythm,80.0,True,66.226,50.929
pooled,elsayed,rhythm,90.0,True,67.254,51.766
pooled,elsayed,rhythm,95.0,True,91.336,69.742
pooled,supercloud,learned,80.0,True,80.558,45.058
pooled,supercloud,learned,90.0,True,87.741,53.639
pooled,supercloud,learned,95.0,True,95.395,65.755
pooled,supercloud,rhythm,80.0,True,99.8,99.306
pooled,supercloud,rhythm,90.0,True,99.8,99.306
pooled,supercloud,rhythm,95.0,True,99.8,99.306

### reports/tables/crossdata_readiness_raw.csv
config,test_dataset,source,target,val_reached,test_cut_pct,test_armed_pct
in_domain,nlr,learned,80.0,True,74.946,31.127
in_domain,nlr,learned,90.0,True,91.841,41.358
in_domain,nlr,learned,95.0,True,95.499,50.282
in_domain,nlr,rhythm,80.0,True,73.779,35.902
in_domain,nlr,rhythm,90.0,False,83.562,67.141
in_domain,nlr,rhythm,95.0,False,83.562,67.141
in_domain,elsayed,learned,80.0,True,57.562,32.584
in_domain,elsayed,learned,90.0,True,90.602,64.735
in_domain,elsayed,learned,95.0,True,95.007,80.099
in_domain,elsayed,rhythm,80.0,True,90.455,60.832
in_domain,elsayed,rhythm,90.0,True,91.043,64.05
in_domain,elsayed,rhythm,95.0,True,94.273,69.397
in_domain,supercloud,learned,80.0,False,82.787,69.02
in_domain,supercloud,learned,90.0,False,82.787,69.02
in_domain,supercloud,learned,95.0,False,82.787,69.02
in_domain,supercloud,rhythm,80.0,False,74.916,65.017
in_domain,supercloud,rhythm,90.0,False,74.916,65.017
in_domain,supercloud,rhythm,95.0,False,74.916,65.017
lodo,nlr,learned,80.0,True,77.93,46.416
lodo,nlr,learned,90.0,True,90.493,68.839
lodo,nlr,learned,95.0,True,94.633,81.036
lodo,nlr,rhythm,80.0,True,73.779,35.902
lodo,nlr,rhythm,90.0,False,83.562,67.141
lodo,nlr,rhythm,95.0,False,83.562,67.141
lodo,elsayed,learned,80.0,True,80.47,52.9
lodo,elsayed,learned,90.0,True,90.162,61.713
lodo,elsayed,learned,95.0,False,90.162,61.713
lodo,elsayed,rhythm,80.0,True,90.455,60.832
lodo,elsayed,rhythm,90.0,True,91.043,64.05
lodo,elsayed,rhythm,95.0,True,94.273,69.397
lodo,supercloud,learned,80.0,True,84.035,73.145
lodo,supercloud,learned,90.0,True,93.46,85.069
lodo,supercloud,learned,95.0,False,93.46,85.069
lodo,supercloud,rhythm,80.0,False,74.916,65.017
lodo,supercloud,rhythm,90.0,False,74.916,65.017
lodo,supercloud,rhythm,95.0,False,74.916,65.017
pooled,nlr,learned,80.0,True,73.586,30.842
pooled,nlr,learned,90.0,True,94.344,48.719
pooled,nlr,learned,95.0,True,96.919,58.507
pooled,nlr,rhythm,80.0,True,73.779,35.902
pooled,nlr,rhythm,90.0,False,83.562,67.141
pooled,nlr,rhythm,95.0,False,83.562,67.141
pooled,elsayed,learned,80.0,True,85.756,55.873
pooled,elsayed,learned,90.0,True,93.979,69.96
pooled,elsayed,learned,95.0,True,95.448,82.547
pooled,elsayed,rhythm,80.0,True,90.455,60.832
pooled,elsayed,rhythm,90.0,True,91.043,64.05
pooled,elsayed,rhythm,95.0,True,94.273,69.397
pooled,supercloud,learned,80.0,False,81.174,68.08
pooled,supercloud,learned,90.0,False,81.174,68.08
pooled,supercloud,learned,95.0,False,81.174,68.08
pooled,supercloud,rhythm,80.0,False,74.916,65.017
pooled,supercloud,rhythm,90.0,False,74.916,65.017
pooled,supercloud,rhythm,95.0,False,74.916,65.017

### reports/tables/drop_warning.csv
model,threshold,events,recall_1s,mean_lead_s,alarm_episodes,episode_precision,false_alarms_per_hour,precision,recall,F1,AP
lightgbm,0.7312716186240797,4280,0.8242990654205608,4.8660430839002276,3689,0.9723502304147466,2.2841417611031556,0.9730661220321675,0.7835484081968286,0.868083916952653,0.9272654441159791
tcn,0.7816887493133573,4280,0.8240654205607477,4.860277856535299,3746,0.9578216764548853,3.538180375042143,0.9678603797262438,0.7783436276479437,0.8628178103263431,0.914572726241983
rhythm_alarm,0.002432144964113832,4280,0.8345794392523365,4.8853863381858895,8938,0.398746923249049,120.34291984478783,0.20037084822719037,0.7966958520608876,0.3202085148574347,0.5424889609166736

### reports/tables/drop_warning_by_workload.csv
workload,threshold,events,recall_1s,mean_lead_s,alarm_episodes,episode_precision,false_alarms_per_hour,precision,recall,F1,AP
inference_offline,0.7312716186240797,367,0.4223433242506812,3.908387096774194,225,0.8,15.168539325842696,0.7758784425451092,0.26673196212863204,0.3969873663751215,0.571388584868678
inference_online_finite,0.7312716186240797,219,0.6986301369863014,4.125490196078432,182,0.9175824175824175,3.8809831824062093,0.8425531914893617,0.47013698630136985,0.603516998827667,0.7559971119653971
inference_online_rate,0.7312716186240797,132,0.0,0.0,0,0.0,0.0,0.0,0.0,0.0,0.07507667782552743
train_llama2_70b_lora,0.7312716186240797,315,0.24126984126984127,4.439473684210526,112,0.7142857142857143,3.021052962834754,0.8629821531375935,0.19034920634920635,0.3119017894298793,0.4417390037178177
train_stable_diffusion,0.7312716186240797,3247,0.9682784108407761,4.9596055979643765,3170,0.9968454258675079,0.4279854960470784,0.9885711363665418,0.9526208808130582,0.9702631149700749,0.9893739160204104

### reports/tables/forecast_by_workload.csv
model,horizon_s,MAE,RMSE,MAPE,workload
persistence,1,160.76598017043668,408.5633785280544,12.45799711967979,inference_offline
persistence,1,67.37196928581797,205.61742165750445,5.600267246255542,inference_online_finite
persistence,1,90.13970573737414,199.4666667598919,4.7200229058468,inference_online_rate
persistence,1,117.23360519096451,229.1564412456167,5.337836828798135,train_llama2_70b_lora
persistence,1,154.37515119252717,433.31716770527504,10.436524555394978,train_stable_diffusion
persistence,5,297.0937840732212,618.4276280560839,23.112901272340682,inference_offline
persistence,5,284.7681480354348,557.4721578733796,29.04123936008634,inference_online_finite
persistence,5,131.9682470616373,331.7083348116419,9.649519343430606,inference_online_rate
persistence,5,448.9838686756268,517.6815756345482,19.984914414299983,train_llama2_70b_lora
persistence,5,240.12575010006353,579.8041026057068,16.723024626001305,train_stable_diffusion
persistence,10,315.2684077753074,612.3879720469743,24.039164042203122,inference_offline
persistence,10,541.6720341593406,861.2155822762675,58.62259806896412,inference_online_finite
persistence,10,198.00925264169373,489.3719644007603,17.16329567829678,inference_online_rate
persistence,10,87.61524235821611,243.06048706222808,6.012190647329217,train_llama2_70b_lora
persistence,10,265.70894993874356,623.3905164546478,19.826011831125836,train_stable_diffusion
moving_avg,1,247.54276831996506,485.98015164661916,20.285640297421917,inference_offline
moving_avg,1,194.98687698514368,396.1481025814213,19.454638868655536,inference_online_finite
moving_avg,1,101.71081993155912,240.8845572654894,7.046032851643397,inference_online_rate
moving_avg,1,302.78206930162423,371.1769081023044,13.515603418943675,train_llama2_70b_lora
moving_avg,1,212.7438856689584,450.4475651787146,14.752804527700352,train_stable_diffusion
moving_avg,5,282.27356261310933,513.2792675440835,22.609611769126868,inference_offline
moving_avg,5,405.6601958178223,683.8505004607805,43.17463398044111,inference_online_finite
moving_avg,5,151.2500201872087,386.75769209003795,12.739145924095736,inference_online_rate
moving_avg,5,292.7855424085219,370.51069438043976,13.86645327314805,train_llama2_70b_lora
moving_avg,5,246.3367996470989,506.96193102275066,17.973724466908642,train_stable_diffusion
moving_avg,10,289.711303911974,506.5600583433522,22.58751118726795,inference_offline
moving_avg,10,659.8492255222861,960.8987009823485,72.88812166580384,inference_online_finite
moving_avg,10,213.7341672087239,527.0882046049111,20.171698590691566,inference_online_rate
moving_avg,10,224.8388998601811,324.2526796296526,11.952877263016035,train_llama2_70b_lora
moving_avg,10,195.48750141154522,458.0234016489767,16.63233620365442,train_stable_diffusion
rhythm,1,222.15671328258958,488.67230164978827,16.510838246367594,inference_offline
rhythm,1,67.5043803574988,206.21083069947747,5.626681489959986,inference_online_finite
rhythm,1,89.2724915913943,214.7874453477993,5.1314426607046135,inference_online_rate
rhythm,1,61.854172261072605,214.5920379166569,3.3625837978224666,train_llama2_70b_lora
rhythm,1,54.26604933767085,206.79956806653124,4.348707859857755,train_stable_diffusion
rhythm,5,301.6248544461939,606.1943723382025,22.822398447602385,inference_offline
rhythm,5,284.9036134653048,557.7024420721289,29.068466078326033,inference_online_finite
rhythm,5,138.30876190705777,348.5204618839245,10.535904490805779,inference_online_rate
rhythm,5,71.18565365599274,223.59003863715395,4.887141404227142,train_llama2_70b_lora
rhythm,5,79.0269499446756,294.566302513468,6.879623529629806,train_stable_diffusion
rhythm,10,310.61727820120024,600.9819746152931,23.285197399067386,inference_offline
rhythm,10,541.6722858839588,861.2155848014487,58.62264879246653,inference_online_finite
rhythm,10,200.21872608762268,498.3647691496196,17.77500103184611,inference_online_rate
rhythm,10,68.14641498670201,237.02430664391377,5.274857927953514,train_llama2_70b_lora
rhythm,10,104.75107858926627,368.0619481755529,9.721680323383199,train_stable_diffusion
lightgbm,1,94.90907306064213,268.90053707729686,7.651879315901512,inference_offline
lightgbm,1,39.290213105050505,136.5472084022341,3.164429515898349,inference_online_finite
lightgbm,1,68.42649254910258,182.36622434632883,3.9982824191386905,inference_online_rate
lightgbm,1,24.694424839740844,78.10718584211845,1.3793443902257287,train_llama2_70b_lora
lightgbm,1,23.61721664715833,94.20737005872301,1.5525923359248492,train_stable_diffusion
lightgbm,5,181.8653878902013,440.0813461068254,18.44073083363019,inference_offline
lightgbm,5,128.22938600216912,280.8579176314228,14.268728574498022,inference_online_finite
lightgbm,5,126.57129075637718,337.07445226981315,13.978393874246553,inference_online_rate
lightgbm,5,38.89402265033669,132.97127551467247,2.8384283493409925,train_llama2_70b_lora
lightgbm,5,50.157962215548515,214.00395908942832,4.810838009373933,train_stable_diffusion
lightgbm,10,195.9736040995151,447.9567432798492,19.13749564445912,inference_offline
lightgbm,10,168.2101609180219,329.6437287140087,19.41979686379536,inference_online_finite
lightgbm,10,176.06603062911077,454.7934051640626,22.255819661331145,inference_online_rate
lightgbm,10,45.244563800794886,171.7662168188391,4.155152868485139,train_llama2_70b_lora
lightgbm,10,64.88517702232257,252.1852338867734,6.967757900626265,train_stable_diffusion
tcn,1,112.63730535533432,292.50422172032233,9.330862974315373,inference_offline
tcn,1,56.1631972588205,160.69319638755758,4.60560139238681,inference_online_finite
tcn,1,73.28004529161497,187.03160053256497,4.398184689975449,inference_online_rate
tcn,1,26.398086923004158,77.09448361329397,1.4685609574243694,train_llama2_70b_lora
tcn,1,25.057698695826115,97.29149042444047,1.6863817245084654,train_stable_diffusion
tcn,5,186.76751997493216,437.86157751011893,18.499665525556892,inference_offline
tcn,5,146.95752807842482,307.8444010391262,14.79143273197262,inference_online_finite
tcn,5,133.8409788308336,337.9375834757292,14.673090325121288,inference_online_rate
tcn,5,44.685167506892924,150.75942094579142,3.1337377087649263,train_llama2_70b_lora
tcn,5,52.647735049231855,232.76031588811668,5.047134124961096,train_stable_diffusion
tcn,10,205.46215873675973,454.5998591590788,19.72727644093522,inference_offline
tcn,10,190.6805014641138,387.20393829351417,20.989288920433076,inference_online_finite
tcn,10,190.89055156472685,479.35774133033425,22.802911821038965,inference_online_rate
tcn,10,53.015940335544656,196.5166536212822,4.607436758920009,train_llama2_70b_lora
tcn,10,74.64826331013008,305.35923441769773,8.00494811300123,train_stable_diffusion

### reports/tables/forecast_overall.csv
model,horizon_s,MAE,RMSE,MAPE
persistence,1,132.89780835668785,359.0174250491695,8.44787381112756
persistence,5,287.9507043001874,548.9053179081501,18.37495721288594
persistence,10,244.78080735890177,572.0079699492883,19.956610578232546
moving_avg,1,225.26226164434297,416.10310818888223,14.566580198901827
moving_avg,5,265.298538410291,487.8193932927967,19.035399265565175
moving_avg,10,250.480189276285,505.6899710232276,21.093443966221788
rhythm,1,71.39639992310019,238.40905751241036,5.101162395819681
rhythm,5,114.9067704154282,345.12093469698186,9.703193309181527
rhythm,10,155.8269161692113,440.3423369400969,14.497690172443766
lightgbm,1,33.84520102907962,124.04747529305995,2.2679615054228166
lightgbm,5,69.60932312314247,240.1832847005652,6.860822110952855
lightgbm,10,87.50448203253153,284.46295297475405,9.51052446388651
tcn,1,38.061387490836836,131.56845875464975,2.6300282487498996
tcn,5,74.8617536054456,254.09779411976544,7.163812080981616
tcn,10,98.31495919773087,323.34170849401977,10.382888597320733

### reports/tables/forecast_subset_with_chronos.csv
model,horizon_s,MAE,RMSE,MAPE
persistence,1,115.0785641171875,307.4540782006281,8.09504708142331
persistence,5,279.27152429223634,524.6539302815246,19.156624914304683
persistence,10,292.42708654321285,614.9398268475417,26.876888976550617
moving_avg,1,218.98067777368163,416.52204162689173,16.181206552456555
moving_avg,5,279.6916806669922,507.9954361524012,22.061272460413296
moving_avg,10,334.79720419628904,617.0981527966949,31.097387849218272
rhythm,1,96.75880030004883,281.3976003943291,7.415015072170636
rhythm,5,168.39102055151363,420.32755164927454,14.185315576168922
rhythm,10,256.72213450146484,573.5542181246544,25.008732498291064
lightgbm,1,49.7472312202189,166.1157404377163,3.7382179700264735
lightgbm,5,106.73461284622095,308.7401574418433,11.163486876070815
lightgbm,10,144.40038663748214,382.42270408967727,16.68493093440304
tcn,1,59.815859815917975,180.4902648402464,4.702112968180802
tcn,5,114.34108827685547,313.4638093788403,11.239530059869937
tcn,10,159.08065655029299,415.3359129672924,17.622694432208256
chronos_bolt_small,1,111.56931737988282,284.81805609737125,8.9049399455428
chronos_bolt_small,5,198.96810032763673,428.4495979122133,17.549134469247658
chronos_bolt_small,10,249.1053250413818,528.7382487012345,26.66035191942786
timesfm_2p5,1,68.13083852478027,195.32691307427456,5.213807315318001
timesfm_2p5,5,144.36229884521484,373.15190013941327,13.891380534468869
timesfm_2p5,10,229.16907125341797,525.1534136087209,24.91970304693524

### reports/tables/generalization_lowo.csv
held_out_workload,lgb_mae_1s,rhythm_mae_1s,persist_mae_1s,lgb_mae_5s,rhythm_mae_5s,persist_mae_5s,lgb_mae_10s,rhythm_mae_10s,persist_mae_10s,lgb_gain_vs_rhythm_5s_pct,drop_recall_1s,drop_mean_lead_s,false_alarms_per_hour,drop_AP,rhythm_alarm_AP
inference_offline,153.724,222.157,160.766,285.995,301.625,297.094,322.065,310.617,315.268,5.182,0.027,2.275,15.843,0.187,0.175
inference_online_finite,75.907,67.504,67.372,327.183,284.904,284.768,539.648,541.672,541.672,-14.84,0.0,0.0,0.0,0.116,0.079
inference_online_rate,82.743,89.272,90.14,150.139,138.309,131.968,237.095,200.219,198.009,-8.554,0.023,3.267,17.587,0.044,0.057
train_llama2_70b_lora,97.241,61.854,117.234,380.494,71.186,448.984,288.904,68.146,87.615,-434.51,0.593,3.543,346.666,0.067,0.118
train_stable_diffusion,195.157,54.266,154.375,210.216,79.027,240.126,252.254,104.751,265.709,-166.006,0.989,4.922,125.186,0.173,0.721

### reports/tables/latency.csv
model,ms_per_prediction
LightGBM (feature computation + 3 horizons + drop classifier),10.34
rhythm / persistence / moving-avg baselines (feature computation),6.72
"tiny TCN (46,148 params, all 4 outputs)",1.18
"chronos-bolt-small (48M params, zero-shot)",19.35
"timesfm-2.5 (200M params, zero-shot)",190.74

### reports/tables/regime_armed_needed.csv
target,ml_aligned_armed,rhythm_aligned_armed,ml_alarm_armed,diff_vs_rhythm_aligned,diff_vs_rhythm_aligned_lo,diff_vs_rhythm_aligned_hi,diff_vs_ml_alarm,diff_vs_ml_alarm_lo,diff_vs_ml_alarm_hi
80.0,43.07,51.55,52.97,-8.48,-64.75,-2.95,-9.89,-22.18,-4.41
90.0,48.39,99.16,64.29,-50.76,-57.38,-8.82,-15.89,-25.7,-3.89
95.0,58.38,99.16,74.78,-40.78,-49.08,-31.36,-16.4,-26.26,0.48

### reports/tables/regime_map.csv
start_s,standby_pct,latency_s,winner,winner_overhead_pct,winner_cut_pct,ml_alarm_cut,ml_alarm_overhead,rhythm_alarm_cut,rhythm_alarm_overhead,ml_forecast_cut,ml_forecast_overhead,rhythm_forecast_cut,rhythm_forecast_overhead,ml_aligned_cut,ml_aligned_overhead,rhythm_aligned_cut,rhythm_aligned_overhead,reactive_cut,reactive_overhead,always_on_cut,always_on_overhead,always_burn_cut,always_burn_overhead,oracle_cut,oracle_overhead
0.0,0.0,0.0,rhythm_aligned,2.241,79.266,89.868,2.796,76.041,2.157,77.894,2.527,75.271,2.132,76.402,2.182,79.266,2.241,39.35,2.528,100.0,2.935,6.739,6.783,100.0,2.889
0.0,0.0,0.2,rhythm_aligned,2.211,79.35,89.832,2.795,75.848,2.151,76.354,2.444,74.801,2.126,77.16,2.209,79.35,2.211,16.185,1.833,100.0,2.935,6.739,6.783,100.0,2.889
0.0,0.0,0.5,ml_aligned,2.059,73.742,89.759,2.794,75.788,2.141,76.101,2.38,74.669,2.116,73.742,2.059,79.314,2.193,15.776,1.258,100.0,2.935,6.739,6.783,100.0,2.889
0.0,0.0,1.0,ml_aligned,2.042,73.706,88.002,2.774,74.32,2.095,77.942,2.348,74.224,2.089,73.706,2.042,74.404,2.103,15.981,0.467,100.0,2.935,6.739,6.783,100.0,2.889
0.0,0.0,2.0,ml_aligned,2.068,74.428,89.037,2.784,75.584,2.112,76.029,2.304,74.452,2.081,74.428,2.068,78.977,2.162,16.27,0.478,100.0,2.935,6.739,6.783,100.0,2.889
0.0,0.0,3.0,ml_aligned,2.071,74.079,88.905,2.782,75.511,2.127,78.592,2.336,74.344,2.1,74.079,2.071,78.881,2.158,16.245,0.481,100.0,2.935,6.739,6.783,100.0,2.889
0.0,0.5,0.0,rhythm_forecast,2.387,75.271,89.868,3.194,76.041,2.424,77.894,2.79,75.271,2.387,76.402,2.436,79.266,2.537,39.35,2.893,100.0,3.562,6.739,6.783,100.0,3.076
0.0,0.5,0.2,rhythm_aligned,2.506,79.35,89.832,3.193,75.848,2.418,76.354,2.707,74.801,2.381,77.16,2.466,79.35,2.506,16.185,2.198,100.0,3.562,6.739,6.783,100.0,3.076
0.0,0.5,0.5,ml_aligned,2.296,73.742,89.759,3.192,75.788,2.408,76.101,2.643,74.669,2.371,73.742,2.296,79.314,2.488,15.776,1.623,100.0,3.562,6.739,6.783,100.0,3.076
0.0,0.5,1.0,ml_aligned,2.267,73.706,88.002,3.159,74.32,2.353,77.942,2.616,74.224,2.342,73.706,2.267,74.404,2.374,15.981,0.833,100.0,3.562,6.739,6.783,100.0,3.076
0.0,0.5,2.0,ml_aligned,2.297,74.428,89.037,3.181,75.584,2.379,76.029,2.566,74.452,2.336,74.428,2.297,78.977,2.455,16.27,0.844,100.0,3.562,6.739,6.783,100.0,3.076
0.0,0.5,3.0,ml_aligned,2.302,74.079,88.905,3.179,75.511,2.395,78.592,2.607,74.344,2.354,74.079,2.302,78.881,2.452,16.245,0.847,100.0,3.562,6.739,6.783,100.0,3.076
0.0,1.0,0.0,rhythm_forecast,2.642,75.271,89.868,3.592,76.041,2.692,77.894,3.052,75.271,2.642,76.402,2.691,79.266,2.832,39.35,3.259,100.0,4.189,6.739,6.783,100.0,3.263
0.0,1.0,0.2,rhythm_forecast,2.636,74.801,89.832,3.591,75.848,2.686,76.354,2.969,74.801,2.636,77.16,2.722,79.35,2.802,16.185,2.563,100.0,4.189,6.739,6.783,100.0,3.263
0.0,1.0,0.5,ml_aligned,2.533,73.742,89.759,3.59,75.788,2.676,76.101,2.905,74.669,2.626,73.742,2.533,79.314,2.783,15.776,1.989,100.0,4.189,6.739,6.783,100.0,3.263
0.0,1.0,1.0,ml_aligned,2.492,73.706,88.002,3.544,74.32,2.612,77.942,2.884,74.224,2.596,73.706,2.492,74.404,2.646,15.981,1.198,100.0,4.189,6.739,6.783,100.0,3.263
0.0,1.0,2.0,ml_aligned,2.525,74.428,89.037,3.579,75.584,2.647,76.029,2.828,74.452,2.59,74.428,2.525,78.977,2.749,16.27,1.21,100.0,4.189,6.739,6.783,100.0,3.263
0.0,1.0,3.0,ml_aligned,2.533,74.079,88.905,3.577,75.511,2.662,78.592,2.879,74.344,2.609,74.079,2.533,78.881,2.746,16.245,1.212,100.0,4.189,6.739,6.783,100.0,3.263
0.0,2.0,0.0,rhythm_forecast,3.152,75.271,89.868,4.389,76.041,3.227,77.894,3.577,75.271,3.152,76.402,3.2,79.266,3.423,39.35,3.99,100.0,5.443,6.739,6.783,100.0,3.637
0.0,2.0,0.2,rhythm_forecast,3.146,74.801,89.832,4.387,75.848,3.221,76.354,3.494,74.801,3.146,77.16,3.235,79.35,3.392,16.185,3.294,100.0,5.443,6.739,6.783,100.0,3.637
0.0,2.0,0.5,ml_aligned,3.007,73.742,89.759,4.385,75.788,3.211,76.101,3.43,74.669,3.136,73.742,3.007,79.314,3.372,15.776,2.72,100.0,5.443,6.739,6.783,100.0,3.637
0.0,2.0,1.0,ml_aligned,2.943,73.706,88.002,4.314,74.32,3.128,77.942,3.42,74.224,3.103,73.706,2.943,74.404,3.189,15.981,1.929,100.0,5.443,6.739,6.783,100.0,3.637
0.0,2.0,2.0,ml_aligned,2.981,74.428,89.037,4.373,75.584,3.181,76.029,3.352,74.452,3.1,74.428,2.981,78.977,3.337,16.27,1.941,100.0,5.443,6.739,6.783,100.0,3.637
0.0,2.0,3.0,ml_aligned,2.995,74.079,88.905,4.371,75.511,3.196,78.592,3.423,74.344,3.119,74.079,2.995,78.881,3.334,16.245,1.944,100.0,5.443,6.739,6.783,100.0,3.637
0.0,5.0,0.0,rhythm_forecast,4.683,75.271,89.868,6.777,76.041,4.832,77.894,5.152,75.271,4.683,76.402,4.727,79.266,5.196,39.35,6.183,100.0,9.205,6.739,6.783,100.0,4.758
0.0,5.0,0.2,rhythm_forecast,4.677,74.801,89.832,6.774,75.848,4.826,76.354,5.068,74.801,4.677,77.16,4.775,79.35,5.164,16.185,5.487,100.0,9.205,6.739,6.783,100.0,4.758
0.0,5.0,0.5,ml_aligned,4.43,73.742,89.759,6.772,75.788,4.815,76.101,5.004,74.669,4.666,73.742,4.43,79.314,5.141,15.776,4.912,100.0,9.205,6.739,6.783,100.0,4.758
0.0,5.0,1.0,ml_aligned,4.294,73.706,88.002,6.624,74.32,4.679,77.942,5.028,74.224,4.623,73.706,4.294,74.404,4.818,15.981,4.122,100.0,9.205,6.739,6.783,100.0,4.758
0.0,5.0,2.0,ml_aligned,4.351,74.428,89.037,6.757,75.584,4.784,76.029,4.924,74.452,4.628,74.428,4.351,78.977,5.1,16.27,4.135,100.0,9.205,6.739,6.783,100.0,4.758
0.0,5.0,3.0,ml_aligned,4.381,74.079,88.905,6.754,75.511,4.798,78.592,5.054,74.344,4.647,74.079,4.381,78.881,5.097,16.245,4.138,100.0,9.205,6.739,6.783,100.0,4.758
0.0,10.0,0.0,rhythm_forecast,7.235,75.271,89.868,10.758,76.041,7.508,77.894,7.777,75.271,7.235,76.402,7.272,79.266,8.15,39.35,9.839,100.0,15.475,6.739,6.783,100.0,6.626
0.0,10.0,0.2,rhythm_forecast,7.228,74.801,89.832,10.754,75.848,7.5,76.354,7.692,74.801,7.228,77.16,7.342,79.35,8.116,16.185,9.141,100.0,15.475,6.739,6.783,100.0,6.626
0.0,10.0,0.5,ml_aligned,6.8,73.742,89.759,10.75,75.788,7.489,76.101,7.627,74.669,7.217,73.742,6.8,79.314,8.088,15.776,8.566,100.0,15.475,6.739,6.783,100.0,6.626
0.0,10.0,1.0,ml_aligned,6.547,73.706,88.002,10.474,74.32,7.263,77.942,7.708,74.224,7.158,73.706,6.547,74.404,7.533,15.981,7.777,100.0,15.475,6.739,6.783,100.0,6.626
0.0,10.0,2.0,ml_aligned,6.634,74.428,89.037,10.729,75.584,7.455,76.029,7.544,74.452,7.176,74.428,6.634,78.977,8.039,16.27,7.791,100.0,15.475,6.739,6.783,100.0,6.626
0.0,10.0,3.0,ml_aligned,6.691,74.079,88.905,10.726,75.511,7.469,78.592,7.772,74.344,7.194,74.079,6.691,78.881,8.037,16.245,7.794,100.0,15.475,6.739,6.783,100.0,6.626
2.0,0.0,0.0,ml_alarm,2.991,99.783,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,39.35,14.655,100.0,2.997,6.739,6.783,100.0,14.579
2.0,0.0,0.2,ml_alarm,2.991,99.783,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,16.185,13.93,100.0,2.997,6.739,6.783,100.0,14.579
2.0,0.0,0.5,ml_alarm,2.991,99.783,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,15.776,13.334,100.0,2.997,6.739,6.783,100.0,14.579
2.0,0.0,1.0,rhythm_aligned,3.113,83.767,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,83.767,3.113,15.981,12.517,100.0,2.997,6.739,6.783,100.0,14.579
2.0,0.0,2.0,ml_alarm,2.99,99.759,99.759,2.99,99.759,2.99,99.759,2.99,99.759,2.99,99.759,2.99,99.759,2.99,16.27,12.536,100.0,2.997,6.739,6.783,100.0,14.579
2.0,0.0,3.0,ml_alarm,2.99,99.759,99.759,2.99,99.759,2.99,99.759,2.99,99.759,2.99,99.759,2.99,99.759,2.99,16.245,12.557,100.0,2.997,6.739,6.783,100.0,14.579
2.0,0.5,0.0,rhythm_forecast,3.658,83.237,99.783,3.612,83.369,3.638,99.783,3.612,83.237,3.658,99.783,3.612,83.598,4.097,39.35,15.02,100.0,3.624,6.739,6.783,100.0,14.766
2.0,0.5,0.2,rhythm_forecast,3.657,83.177,99.783,3.612,83.345,3.638,99.783,3.612,83.177,3.657,99.783,3.612,83.574,4.094,16.185,14.296,100.0,3.624,6.739,6.783,100.0,14.766
2.0,0.5,0.5,rhythm_forecast,3.656,83.117,99.783,3.612,83.321,3.64,99.783,3.612,83.117,3.656,99.783,3.612,83.586,4.095,15.776,13.699,100.0,3.624,6.739,6.783,100.0,14.766
2.0,0.5,1.0,rhythm_aligned,3.536,83.767,99.783,3.612,83.261,3.617,99.783,3.612,83.117,3.642,99.783,3.612,83.767,3.536,15.981,12.882,100.0,3.624,6.739,6.783,100.0,14.766
2.0,0.5,2.0,rhythm_forecast,3.631,83.165,99.759,3.612,83.381,3.641,99.759,3.612,83.165,3.631,99.759,3.612,83.574,4.087,16.27,12.902,100.0,3.624,6.739,6.783,100.0,14.766
2.0,0.5,3.0,rhythm_forecast,3.641,83.273,99.759,3.612,83.406,3.642,99.759,3.612,83.273,3.641,99.759,3.612,83.61,4.088,16.245,12.923,100.0,3.624,6.739,6.783,100.0,14.766
2.0,1.0,0.0,rhythm_forecast,4.078,83.237,99.783,4.234,83.369,4.06,99.783,4.234,83.237,4.078,99.783,4.234,83.598,4.518,39.35,15.386,100.0,4.251,6.739,6.783,100.0,14.953
2.0,1.0,0.2,rhythm_forecast,4.077,83.177,99.783,4.234,83.345,4.06,99.783,4.234,83.177,4.077,99.783,4.234,83.574,4.515,16.185,14.661,100.0,4.251,6.739,6.783,100.0,14.953
2.0,1.0,0.5,rhythm_forecast,4.076,83.117,99.783,4.234,83.321,4.062,99.783,4.234,83.117,4.076,99.783,4.234,83.586,4.516,15.776,14.065,100.0,4.251,6.739,6.783,100.0,14.953
2.0,1.0,1.0,rhythm_aligned,3.959,83.767,99.783,4.234,83.261,4.038,99.783,4.234,83.117,4.061,99.783,4.234,83.767,3.959,15.981,13.248,100.0,4.251,6.739,6.783,100.0,14.953
2.0,1.0,2.0,rhythm_forecast,4.05,83.165,99.759,4.234,83.381,4.063,99.759,4.234,83.165,4.05,99.759,4.234,83.574,4.507,16.27,13.267,100.0,4.251,6.739,6.783,100.0,14.953
2.0,1.0,3.0,rhythm_forecast,4.06,83.273,99.759,4.234,83.406,4.063,99.759,4.234,83.273,4.06,99.759,4.234,83.61,4.509,16.245,13.288,100.0,4.251,6.739,6.783,100.0,14.953
2.0,2.0,0.0,rhythm_forecast,4.918,83.237,99.783,5.478,83.369,4.904,99.783,5.478,83.237,4.918,76.402,8.481,83.598,5.361,39.35,16.117,100.0,5.505,6.739,6.783,100.0,15.327
2.0,2.0,0.2,rhythm_forecast,4.917,83.177,99.783,5.478,83.345,4.904,99.783,5.478,83.177,4.917,77.16,8.592,83.574,5.357,16.185,15.392,100.0,5.505,6.739,6.783,100.0,15.327
2.0,2.0,0.5,rhythm_forecast,4.915,83.117,99.783,5.478,83.321,4.906,99.783,5.478,83.117,4.915,77.665,8.822,83.586,5.358,15.776,14.796,100.0,5.505,6.739,6.783,100.0,15.327
2.0,2.0,1.0,rhythm_aligned,4.805,83.767,99.783,5.478,83.261,4.878,99.783,5.478,83.117,4.9,99.783,5.478,83.767,4.805,15.981,13.979,100.0,5.505,6.739,6.783,100.0,15.327
2.0,2.0,2.0,rhythm_forecast,4.888,83.165,99.759,5.477,83.381,4.905,99.759,5.477,83.165,4.888,78.761,9.119,83.574,5.349,16.27,13.998,100.0,5.505,6.739,6.783,100.0,15.327
2.0,2.0,3.0,rhythm_forecast,4.898,83.273,99.759,5.477,83.406,4.906,99.759,5.477,83.273,4.898,78.063,8.679,83.61,5.351,16.245,14.02,100.0,5.505,6.739,6.783,100.0,15.327
2.0,5.0,0.0,rhythm_aligned,10.772,79.266,99.783,9.208,83.369,7.437,81.035,12.319,76.619,10.111,76.402,10.008,79.266,10.772,39.35,18.31,100.0,9.267,6.739,6.783,100.0,16.448
2.0,5.0,0.2,rhythm_aligned,10.768,79.35,99.783,9.208,83.345,7.436,81.095,12.237,76.51,10.11,77.16,10.132,79.35,10.768,16.185,17.585,100.0,9.267,6.739,6.783,100.0,16.448
2.0,5.0,0.5,rhythm_aligned,10.76,79.314,99.783,9.208,75.788,10.773,81.119,12.177,76.366,10.1,77.665,10.371,79.314,10.76,15.776,16.988,100.0,9.267,6.739,6.783,100.0,16.448
2.0,5.0,1.0,rhythm_aligned,10.238,75.523,99.783,9.208,77.521,10.239,83.081,11.78,79.326,10.695,79.206,10.493,75.523,10.238,15.981,16.172,100.0,9.267,6.739,6.783,100.0,16.448
2.0,5.0,2.0,rhythm_aligned,10.701,78.977,99.759,9.207,75.584,10.735,81.059,12.083,76.149,10.059,78.761,10.685,78.977,10.701,16.27,16.192,100.0,9.267,6.739,6.783,100.0,16.448
2.0,5.0,3.0,rhythm_aligned,10.695,78.881,99.759,9.207,75.511,10.732,80.866,12.079,76.029,10.059,78.063,10.239,78.881,10.695,16.245,16.214,100.0,9.267,6.739,6.783,100.0,16.448
2.0,10.0,0.0,rhythm_aligned,13.726,79.266,89.868,17.024,76.041,13.461,81.035,15.166,76.619,12.777,76.402,12.553,79.266,13.726,39.35,21.966,100.0,15.537,6.739,6.783,100.0,18.316
2.0,10.0,0.2,rhythm_aligned,13.72,79.35,89.832,17.017,75.848,13.457,81.095,15.083,76.51,12.775,77.16,12.698,79.35,13.72,16.185,21.239,100.0,15.537,6.739,6.783,100.0,18.316
2.0,10.0,0.5,rhythm_aligned,13.708,79.314,89.759,17.011,75.788,13.447,81.119,15.022,76.366,12.765,77.665,12.952,79.314,13.708,15.776,20.642,100.0,15.537,6.739,6.783,100.0,18.316
2.0,10.0,1.0,rhythm_aligned,12.978,75.331,88.002,16.991,77.521,12.986,82.708,14.693,76.667,12.785,79.206,13.117,75.331,12.978,15.981,19.827,100.0,15.537,6.739,6.783,100.0,18.316
2.0,10.0,2.0,rhythm_aligned,13.64,78.977,89.037,16.999,75.584,13.406,81.059,14.926,76.149,12.721,78.761,13.296,78.977,13.64,16.27,19.849,100.0,15.537,6.739,6.783,100.0,18.316
2.0,10.0,3.0,rhythm_aligned,13.635,78.881,88.905,16.991,75.511,13.402,80.866,14.921,76.029,12.721,78.063,12.839,78.881,13.635,16.245,19.871,100.0,15.537,6.739,6.783,100.0,18.316
10.0,0.0,0.0,ml_alarm,3.238,99.783,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,39.35,63.163,100.0,3.244,6.739,6.783,100.0,61.339
10.0,0.0,0.2,ml_alarm,3.238,99.783,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,16.185,62.322,100.0,3.244,6.739,6.783,100.0,61.339
10.0,0.0,0.5,ml_alarm,3.238,99.783,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,15.776,61.639,100.0,3.244,6.739,6.783,100.0,61.339
10.0,0.0,1.0,ml_alarm,3.238,99.783,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,15.981,60.717,100.0,3.244,6.739,6.783,100.0,61.339
10.0,0.0,2.0,ml_alarm,3.237,99.759,99.759,3.237,99.759,3.237,99.759,3.237,99.759,3.237,99.759,3.237,99.759,3.237,16.27,60.766,100.0,3.244,6.739,6.783,100.0,61.339
10.0,0.0,3.0,ml_alarm,3.238,99.759,99.759,3.238,99.759,3.238,99.759,3.238,99.759,3.238,99.759,3.238,99.759,3.238,16.245,60.862,100.0,3.244,6.739,6.783,100.0,61.339
10.0,0.5,0.0,ml_alarm,3.86,99.783,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.86,39.35,63.529,100.0,3.871,6.739,6.783,100.0,61.526

### reports/tables/regime_ml_vs_rhythm_ci.csv
start_s,standby_pct,latency_s,pair,metric,ml_minus_rhythm,ci_lo,ci_hi
0.0,0.0,0.0,ml_alarm-rhythm_alarm,overhead_pct,0.639,0.168,1.184
0.0,0.0,0.0,ml_alarm-rhythm_alarm,cut_pct,13.827,-7.569,41.717
0.0,0.0,0.0,ml_aligned-rhythm_aligned,overhead_pct,-0.059,-0.297,0.142
0.0,0.0,0.0,ml_aligned-rhythm_aligned,cut_pct,-2.864,-12.857,4.313
0.0,0.0,0.2,ml_alarm-rhythm_alarm,overhead_pct,0.644,0.171,1.212
0.0,0.0,0.2,ml_alarm-rhythm_alarm,cut_pct,13.983,-7.471,38.781
0.0,0.0,0.2,ml_aligned-rhythm_aligned,overhead_pct,-0.002,-0.265,0.233
0.0,0.0,0.2,ml_aligned-rhythm_aligned,cut_pct,-2.19,-11.01,5.117
0.0,0.0,0.5,ml_alarm-rhythm_alarm,overhead_pct,0.653,0.204,1.264
0.0,0.0,0.5,ml_alarm-rhythm_alarm,cut_pct,13.971,-9.636,41.339
0.0,0.0,0.5,ml_aligned-rhythm_aligned,overhead_pct,-0.134,-0.353,0.034
0.0,0.0,0.5,ml_aligned-rhythm_aligned,cut_pct,-5.572,-17.143,0.693
0.0,0.0,1.0,ml_alarm-rhythm_alarm,overhead_pct,0.679,0.213,1.235
0.0,0.0,1.0,ml_alarm-rhythm_alarm,cut_pct,13.682,-7.892,39.275
0.0,0.0,1.0,ml_aligned-rhythm_aligned,overhead_pct,-0.061,-0.253,0.07
0.0,0.0,1.0,ml_aligned-rhythm_aligned,cut_pct,-0.698,-6.551,3.274
0.0,0.0,2.0,ml_alarm-rhythm_alarm,overhead_pct,0.672,0.199,1.255
0.0,0.0,2.0,ml_alarm-rhythm_alarm,cut_pct,13.454,-8.585,37.45
0.0,0.0,2.0,ml_aligned-rhythm_aligned,overhead_pct,-0.093,-0.322,0.057
0.0,0.0,2.0,ml_aligned-rhythm_aligned,cut_pct,-4.549,-13.946,2.256
0.0,0.0,3.0,ml_alarm-rhythm_alarm,overhead_pct,0.655,0.2,1.239
0.0,0.0,3.0,ml_alarm-rhythm_alarm,cut_pct,13.394,-9.944,38.142
0.0,0.0,3.0,ml_aligned-rhythm_aligned,overhead_pct,-0.087,-0.263,0.073
0.0,0.0,3.0,ml_aligned-rhythm_aligned,cut_pct,-4.801,-15.462,1.691
0.0,0.5,0.0,ml_alarm-rhythm_alarm,overhead_pct,0.77,0.234,1.431
0.0,0.5,0.0,ml_alarm-rhythm_alarm,cut_pct,13.827,-8.134,38.963
0.0,0.5,0.0,ml_aligned-rhythm_aligned,overhead_pct,-0.1,-0.397,0.16
0.0,0.5,0.0,ml_aligned-rhythm_aligned,cut_pct,-2.864,-13.178,3.948
0.0,0.5,0.2,ml_alarm-rhythm_alarm,overhead_pct,0.774,0.224,1.457
0.0,0.5,0.2,ml_alarm-rhythm_alarm,cut_pct,13.983,-9.062,38.587
0.0,0.5,0.2,ml_aligned-rhythm_aligned,overhead_pct,-0.041,-0.314,0.204
0.0,0.5,0.2,ml_aligned-rhythm_aligned,cut_pct,-2.19,-11.977,5.091
0.0,0.5,0.5,ml_alarm-rhythm_alarm,overhead_pct,0.783,0.164,1.424
0.0,0.5,0.5,ml_alarm-rhythm_alarm,cut_pct,13.971,-8.335,38.217
0.0,0.5,0.5,ml_aligned-rhythm_aligned,overhead_pct,-0.192,-0.434,-0.015
0.0,0.5,0.5,ml_aligned-rhythm_aligned,cut_pct,-5.572,-15.383,0.836
0.0,0.5,1.0,ml_alarm-rhythm_alarm,overhead_pct,0.806,0.245,1.547
0.0,0.5,1.0,ml_alarm-rhythm_alarm,cut_pct,13.682,-8.408,38.414
0.0,0.5,1.0,ml_aligned-rhythm_aligned,overhead_pct,-0.107,-0.315,0.032
0.0,0.5,1.0,ml_aligned-rhythm_aligned,cut_pct,-0.698,-6.116,3.41
0.0,0.5,2.0,ml_alarm-rhythm_alarm,overhead_pct,0.802,0.237,1.474
0.0,0.5,2.0,ml_alarm-rhythm_alarm,cut_pct,13.454,-9.173,40.405
0.0,0.5,2.0,ml_aligned-rhythm_aligned,overhead_pct,-0.159,-0.373,0.01
0.0,0.5,2.0,ml_aligned-rhythm_aligned,cut_pct,-4.549,-14.871,2.149
0.0,0.5,3.0,ml_alarm-rhythm_alarm,overhead_pct,0.785,0.211,1.501
0.0,0.5,3.0,ml_alarm-rhythm_alarm,cut_pct,13.394,-7.228,38.055
0.0,0.5,3.0,ml_aligned-rhythm_aligned,overhead_pct,-0.15,-0.375,0.024
0.0,0.5,3.0,ml_aligned-rhythm_aligned,cut_pct,-4.801,-14.903,1.635
0.0,1.0,0.0,ml_alarm-rhythm_alarm,overhead_pct,0.9,0.243,1.723
0.0,1.0,0.0,ml_alarm-rhythm_alarm,cut_pct,13.827,-7.798,37.654
0.0,1.0,0.0,ml_aligned-rhythm_aligned,overhead_pct,-0.141,-0.457,0.138
0.0,1.0,0.0,ml_aligned-rhythm_aligned,cut_pct,-2.864,-12.58,4.077
0.0,1.0,0.2,ml_alarm-rhythm_alarm,overhead_pct,0.905,0.327,1.711
0.0,1.0,0.2,ml_alarm-rhythm_alarm,cut_pct,13.983,-7.988,38.147
0.0,1.0,0.2,ml_aligned-rhythm_aligned,overhead_pct,-0.08,-0.375,0.21
0.0,1.0,0.2,ml_aligned-rhythm_aligned,cut_pct,-2.19,-10.826,5.102
0.0,1.0,0.5,ml_alarm-rhythm_alarm,overhead_pct,0.914,0.281,1.74
0.0,1.0,0.5,ml_alarm-rhythm_alarm,cut_pct,13.971,-7.232,40.312
0.0,1.0,0.5,ml_aligned-rhythm_aligned,overhead_pct,-0.25,-0.521,-0.042
0.0,1.0,0.5,ml_aligned-rhythm_aligned,cut_pct,-5.572,-15.308,0.857
0.0,1.0,1.0,ml_alarm-rhythm_alarm,overhead_pct,0.933,0.235,1.757
0.0,1.0,1.0,ml_alarm-rhythm_alarm,cut_pct,13.682,-8.022,36.81
0.0,1.0,1.0,ml_aligned-rhythm_aligned,overhead_pct,-0.153,-0.383,-0.009
0.0,1.0,1.0,ml_aligned-rhythm_aligned,cut_pct,-0.698,-5.789,3.225
0.0,1.0,2.0,ml_alarm-rhythm_alarm,overhead_pct,0.932,0.278,1.761
0.0,1.0,2.0,ml_alarm-rhythm_alarm,cut_pct,13.454,-9.246,37.947
0.0,1.0,2.0,ml_aligned-rhythm_aligned,overhead_pct,-0.224,-0.473,-0.041
0.0,1.0,2.0,ml_aligned-rhythm_aligned,cut_pct,-4.549,-14.459,2.292
0.0,1.0,3.0,ml_alarm-rhythm_alarm,overhead_pct,0.915,0.228,1.685
0.0,1.0,3.0,ml_alarm-rhythm_alarm,cut_pct,13.394,-10.125,41.23
0.0,1.0,3.0,ml_aligned-rhythm_aligned,overhead_pct,-0.213,-0.476,-0.025
0.0,1.0,3.0,ml_aligned-rhythm_aligned,cut_pct,-4.801,-14.187,1.729
0.0,2.0,0.0,ml_alarm-rhythm_alarm,overhead_pct,1.161,0.235,2.18
0.0,2.0,0.0,ml_alarm-rhythm_alarm,cut_pct,13.827,-6.821,38.254
0.0,2.0,0.0,ml_aligned-rhythm_aligned,overhead_pct,-0.223,-0.596,0.131
0.0,2.0,0.0,ml_aligned-rhythm_aligned,cut_pct,-2.864,-12.691,4.28
0.0,2.0,0.2,ml_alarm-rhythm_alarm,overhead_pct,1.166,0.315,2.158
0.0,2.0,0.2,ml_alarm-rhythm_alarm,cut_pct,13.983,-8.546,39.494
0.0,2.0,0.2,ml_aligned-rhythm_aligned,overhead_pct,-0.157,-0.496,0.208

### reports/tables/regime_pareto_test.csv
strategy,latency_s,thr,violations,raw_violations,overhead_J,base_J,armed_s,hours,episodes,cut_pct,overhead_pct,armed_pct,episodes_per_h
always_burn,,,7750.0,8310,24589687.5628,362538781.2864,0.0,45.1002,0.0,6.7389,6.7826,0.0,0.0
always_on,,,0.0,8310,10641835.2878,362538781.2864,162360.6,45.1002,40.0,100.0,2.9354,100.0,0.8869
ml_alarm,0.0,0.0,18.0,8310,10618710.475,362538781.2864,160995.6,45.1002,40.0,99.7834,2.929,99.1593,0.8869
ml_alarm,0.0,0.0002,18.0,8310,10618710.475,362538781.2864,160541.2,45.1002,79.0,99.7834,2.929,98.8794,1.7517
ml_alarm,0.0,0.0004,18.0,8310,10618710.475,362538781.2864,157996.2,45.1002,353.0,99.7834,2.929,97.3119,7.827
ml_alarm,0.0,0.0013,18.0,8310,10618531.9038,362538781.2864,154116.6,45.1002,443.0,99.7834,2.9289,94.9224,9.8226
ml_alarm,0.0,0.0029,26.0,8310,10610781.889,362538781.2864,150764.8,45.1002,661.0,99.6871,2.9268,92.858,14.6563
ml_alarm,0.0,0.0053,101.0,8310,10547769.1168,362538781.2864,140929.4,45.1002,1908.0,98.7846,2.9094,86.8002,42.3058
ml_alarm,0.0,0.0072,217.0,8310,10484379.5526,362538781.2864,132295.0,45.1002,2641.0,97.3887,2.8919,81.4822,58.5585
ml_alarm,0.0,0.0138,507.0,8310,10315657.2898,362538781.2864,115177.8,45.1002,3610.0,93.8989,2.8454,70.9395,80.0441
ml_alarm,0.0,0.0249,842.0,8310,10136813.9163,362538781.2864,103094.8,45.1002,4056.0,89.8676,2.7961,63.4974,89.9331
ml_alarm,0.0,0.0423,1299.0,8310,9894778.6469,362538781.2864,91403.2,45.1002,4517.0,84.3682,2.7293,56.2964,100.1548
ml_alarm,0.0,0.066,1881.0,8310,9585118.8866,362538781.2864,79924.2,45.1002,4684.0,77.3646,2.6439,49.2264,103.8577
ml_alarm,0.0,0.0998,2515.0,8310,9220336.188,362538781.2864,69694.6,45.1002,4644.0,69.7353,2.5433,42.9258,102.9708
ml_alarm,0.0,0.1467,3065.0,8310,8902800.0488,362538781.2864,61371.8,45.1002,4519.0,63.1167,2.4557,37.7997,100.1992
ml_alarm,0.0,0.208,3508.0,8310,8614766.2716,362538781.2864,55037.6,45.1002,4377.0,57.7858,2.3762,33.8984,97.0506
ml_alarm,0.0,0.2899,3870.0,8310,8319163.9401,362538781.2864,49807.2,45.1002,4199.0,53.4296,2.2947,30.6769,93.1039
ml_alarm,0.0,0.3993,4174.0,8310,8055206.7334,362538781.2864,45261.8,45.1002,3987.0,49.7714,2.2219,27.8773,88.4032
ml_alarm,0.0,0.5499,4433.0,8310,7711013.6324,362538781.2864,41471.4,45.1002,3776.0,46.6546,2.1269,25.5428,83.7247
ml_alarm,0.0,0.7352,4650.0,8310,7308675.9445,362538781.2864,38615.6,45.1002,3565.0,44.0433,2.016,23.7838,79.0463
ml_alarm,0.0,0.901,4941.0,8310,6518356.8923,362538781.2864,35602.8,45.1002,3319.0,40.5415,1.798,21.9282,73.5917
ml_alarm,0.0,0.9886,5173.0,8310,5909844.1415,362538781.2864,32703.0,45.1002,3110.0,37.7497,1.6301,20.1422,68.9576
ml_alarm,0.0,0.9972,5202.0,8310,5830958.2155,362538781.2864,31691.2,45.1002,3084.0,37.4007,1.6084,19.519,68.3811
ml_alarm,0.0,0.9988,5291.0,8310,5605192.5275,362538781.2864,29651.4,45.1002,2997.0,36.3297,1.5461,18.2627,66.4521
ml_alarm,0.0,0.9991,5315.0,8310,5542576.7501,362538781.2864,28753.6,45.1002,2974.0,36.0409,1.5288,17.7097,65.9421
ml_alarm,0.0,0.9992,5328.0,8310,5508115.8331,362538781.2864,28215.6,45.1002,2962.0,35.8845,1.5193,17.3784,65.676
ml_alarm,0.0,0.9993,5353.0,8310,5431983.5703,362538781.2864,27654.6,45.1002,2937.0,35.5836,1.4983,17.0328,65.1217
ml_alarm,0.0,0.9994,5382.0,8310,5363140.3773,362538781.2864,27062.8,45.1002,2908.0,35.2347,1.4793,16.6683,64.4787
ml_alarm,0.0,0.9995,5412.0,8310,5306110.7135,362538781.2864,26473.2,45.1002,2878.0,34.8736,1.4636,16.3052,63.8135
ml_alarm,0.0,0.9996,5433.0,8310,5266699.3293,362538781.2864,25878.0,45.1002,2857.0,34.6209,1.4527,15.9386,63.3479
ml_alarm,0.0,0.9997,5460.0,8310,5218492.1243,362538781.2864,25236.0,45.1002,2831.0,34.296,1.4394,15.5432,62.7714
ml_alarm,0.0,0.9997,5488.0,8310,5166422.9327,362538781.2864,24397.8,45.1002,2805.0,33.9591,1.4251,15.0269,62.1949
ml_alarm,0.0,0.9997,5508.0,8310,5123440.2259,362538781.2864,23552.0,45.1002,2785.0,33.7184,1.4132,14.506,61.7514
ml_alarm,0.0,0.9998,5531.0,8310,5080330.2883,362538781.2864,22624.0,45.1002,2762.0,33.4416,1.4013,13.9344,61.2415
ml_alarm,0.0,0.9998,5559.0,8310,5028814.6083,362538781.2864,21615.0,45.1002,2734.0,33.1047,1.3871,13.313,60.6206
ml_alarm,0.0,0.9998,5615.0,8310,4919812.5843,362538781.2864,20475.8,45.1002,2681.0,32.4308,1.357,12.6113,59.4455
ml_alarm,0.0,0.9998,5690.0,8310,4774271.5177,362538781.2864,19294.2,45.1002,2608.0,31.5283,1.3169,11.8835,57.8268
ml_alarm,0.0,0.9998,5793.0,8310,4590883.3136,362538781.2864,18120.6,45.1002,2507.0,30.2888,1.2663,11.1607,55.5874
ml_alarm,0.2,0.0,18.0,8310,10618710.475,362538781.2864,160994.8,45.1002,40.0,99.7834,2.929,99.1588,0.8869
ml_alarm,0.2,0.0002,18.0,8310,10618710.475,362538781.2864,160540.4,45.1002,79.0,99.7834,2.929,98.8789,1.7517
ml_alarm,0.2,0.0004,18.0,8310,10618710.475,362538781.2864,157995.4,45.1002,353.0,99.7834,2.929,97.3114,7.827
ml_alarm,0.2,0.0013,18.0,8310,10618536.0292,362538781.2864,154114.0,45.1002,443.0,99.7834,2.9289,94.9208,9.8226
ml_alarm,0.2,0.0029,26.0,8310,10607729.1766,362538781.2864,150752.6,45.1002,661.0,99.6871,2.926,92.8505,14.6563
ml_alarm,0.2,0.0053,106.0,8310,10545762.5687,362538781.2864,140903.2,45.1002,1908.0,98.7244,2.9089,86.7841,42.3058
ml_alarm,0.2,0.0072,220.0,8310,10482757.5845,362538781.2864,132263.8,45.1002,2640.0,97.3526,2.8915,81.463,58.5364
ml_alarm,0.2,0.0138,511.0,8310,10310893.0883,362538781.2864,115141.8,45.1002,3609.0,93.8508,2.8441,70.9173,80.0219
ml_alarm,0.2,0.0249,845.0,8310,10131924.6625,362538781.2864,103053.4,45.1002,4055.0,89.8315,2.7947,63.4719,89.911
ml_alarm,0.2,0.0423,1305.0,8310,9886609.4971,362538781.2864,91354.2,45.1002,4517.0,84.296,2.727,56.2662,100.1548
ml_alarm,0.2,0.066,1885.0,8310,9569837.9441,362538781.2864,79868.0,45.1002,4684.0,77.3165,2.6397,49.1917,103.8577
ml_alarm,0.2,0.0998,2533.0,8310,9212033.9271,362538781.2864,69643.0,45.1002,4645.0,69.5187,2.541,42.894,102.993
ml_alarm,0.2,0.1467,3088.0,8310,8888239.5007,362538781.2864,61323.8,45.1002,4519.0,62.84,2.4517,37.7701,100.1992
ml_alarm,0.2,0.208,3532.0,8310,8605254.3276,362538781.2864,55006.2,45.1002,4374.0,57.497,2.3736,33.879,96.9841
ml_alarm,0.2,0.2899,3895.0,8310,8308372.7775,362538781.2864,49771.6,45.1002,4198.0,53.1288,2.2917,30.655,93.0817
ml_alarm,0.2,0.3993,4199.0,8310,8048243.0108,362538781.2864,45227.4,45.1002,3987.0,49.4705,2.22,27.8561,88.4032
ml_alarm,0.2,0.5499,4449.0,8310,7705996.2957,362538781.2864,41434.8,45.1002,3776.0,46.4621,2.1256,25.5202,83.7247
ml_alarm,0.2,0.7352,4663.0,8310,7304789.0817,362538781.2864,38581.8,45.1002,3565.0,43.8869,2.0149,23.763,79.0463
ml_alarm,0.2,0.901,4941.0,8310,6537633.5887,362538781.2864,35598.8,45.1002,3319.0,40.5415,1.8033,21.9258,73.5917
ml_alarm,0.2,0.9886,5172.0,8310,5934819.1151,362538781.2864,32720.4,45.1002,3110.0,37.7617,1.637,20.1529,68.9576
ml_alarm,0.2,0.9972,5200.0,8310,5844249.3569,362538781.2864,31697.0,45.1002,3084.0,37.4248,1.612,19.5226,68.3811
ml_alarm,0.2,0.9988,5290.0,8310,5610784.0897,362538781.2864,29651.0,45.1002,2997.0,36.3418,1.5476,18.2624,66.4521
ml_alarm,0.2,0.9991,5315.0,8310,5542697.9453,362538781.2864,28750.2,45.1002,2974.0,36.0409,1.5289,17.7076,65.9421
ml_alarm,0.2,0.9992,5328.0,8310,5508243.8739,362538781.2864,28212.8,45.1002,2962.0,35.8845,1.5194,17.3766,65.676
ml_alarm,0.2,0.9993,5353.0,8310,5432022.8263,362538781.2864,27652.2,45.1002,2937.0,35.5836,1.4983,17.0313,65.1217
ml_alarm,0.2,0.9994,5382.0,8310,5363179.6333,362538781.2864,27061.0,45.1002,2908.0,35.2347,1.4793,16.6672,64.4787
ml_alarm,0.2,0.9995,5412.0,8310,5306149.9695,362538781.2864,26471.6,45.1002,2878.0,34.8736,1.4636,16.3042,63.8135
ml_alarm,0.2,0.9996,5433.0,8310,5266738.5853,362538781.2864,25876.4,45.1002,2857.0,34.6209,1.4527,15.9376,63.3479
ml_alarm,0.2,0.9997,5460.0,8310,5218542.7035,362538781.2864,25234.6,45.1002,2831.0,34.296,1.4394,15.5423,62.7714
ml_alarm,0.2,0.9997,5488.0,8310,5166429.7783,362538781.2864,24396.0,45.1002,2805.0,33.9591,1.4251,15.0258,62.1949
ml_alarm,0.2,0.9997,5508.0,8310,5123485.5791,362538781.2864,23550.2,45.1002,2785.0,33.7184,1.4132,14.5049,61.7514
ml_alarm,0.2,0.9998,5531.0,8310,5080368.7959,362538781.2864,22622.2,45.1002,2762.0,33.4416,1.4013,13.9333,61.2415
ml_alarm,0.2,0.9998,5559.0,8310,5028853.1159,362538781.2864,21613.2,45.1002,2734.0,33.1047,1.3871,13.3119,60.6206
ml_alarm,0.2,0.9998,5612.0,8310,4931999.7399,362538781.2864,20487.2,45.1002,2681.0,32.4669,1.3604,12.6183,59.4455
ml_alarm,0.2,0.9998,5686.0,8310,4797301.1413,362538781.2864,19316.6,45.1002,2608.0,31.5764,1.3233,11.8973,57.8268
ml_alarm,0.2,0.9998,5790.0,8310,4609014.8746,362538781.2864,18139.0,45.1002,2507.0,30.3249,1.2713,11.172,55.5874
ml_alarm,0.5,0.0,18.0,8310,10618710.475,362538781.2864,160994.0,45.1002,40.0,99.7834,2.929,99.1583,0.8869
ml_alarm,0.5,0.0002,18.0,8310,10618710.475,362538781.2864,160539.6,45.1002,79.0,99.7834,2.929,98.8784,1.7517
ml_alarm,0.5,0.0004,18.0,8310,10618710.475,362538781.2864,157994.6,45.1002,353.0,99.7834,2.929,97.3109,7.827
ml_alarm,0.5,0.0013,18.0,8310,10618533.0962,362538781.2864,154112.2,45.1002,443.0,99.7834,2.9289,94.9197,9.8226
ml_alarm,0.5,0.0029,26.0,8310,10606475.8444,362538781.2864,150744.6,45.1002,664.0,99.6871,2.9256,92.8456,14.7228

### reports/tables/regime_targets.csv
target,standby_pct,strategy,test_cut_pct,test_overhead_pct,armed_pct
80.0,0.0,ml_alarm,88.002,2.774,61.402
80.0,0.0,rhythm_alarm,74.32,2.095,41.215
80.0,0.0,ml_forecast,77.942,2.348,42.749
80.0,0.0,rhythm_forecast,74.224,2.089,40.428
80.0,0.0,ml_aligned,73.706,2.042,35.924
80.0,0.0,rhythm_aligned,74.404,2.103,43.308
80.0,0.0,always_on,100.0,2.935,100.0
80.0,0.0,oracle,100.0,2.889,29.802
80.0,0.0,diff_cut_ml_minus_rhythm_aligned,-0.698,-6.031,3.323
80.0,2.0,ml_alarm,88.002,4.314,61.402
80.0,2.0,rhythm_alarm,74.32,3.128,41.215
80.0,2.0,ml_forecast,77.942,3.42,42.749
80.0,2.0,rhythm_forecast,74.224,3.103,40.428
80.0,2.0,ml_aligned,73.706,2.943,35.924
80.0,2.0,rhythm_aligned,74.404,3.189,43.308
80.0,2.0,always_on,100.0,5.443,100.0
80.0,2.0,oracle,100.0,3.637,29.802
80.0,2.0,diff_cut_ml_minus_rhythm_aligned,-0.698,-6.285,3.118
80.0,5.0,ml_alarm,88.002,6.624,61.402
80.0,5.0,rhythm_alarm,74.32,4.679,41.215
80.0,5.0,ml_forecast,77.942,5.028,42.749
80.0,5.0,rhythm_forecast,74.224,4.623,40.428
80.0,5.0,ml_aligned,73.706,4.294,35.924
80.0,5.0,rhythm_aligned,74.404,4.818,43.308
80.0,5.0,always_on,100.0,9.205,100.0
80.0,5.0,oracle,100.0,4.758,29.802
80.0,5.0,diff_cut_ml_minus_rhythm_aligned,-0.698,-6.108,3.222
90.0,0.0,ml_alarm,92.732,2.833,69.147
90.0,0.0,rhythm_alarm,99.615,2.923,99.048
90.0,0.0,ml_forecast,83.081,2.472,47.01
90.0,0.0,rhythm_forecast,99.627,2.923,99.043
90.0,0.0,ml_aligned,86.775,2.535,45.634
90.0,0.0,rhythm_aligned,99.783,2.929,99.159
90.0,0.0,always_on,100.0,2.935,100.0
90.0,0.0,oracle,100.0,2.889,29.802
90.0,0.0,diff_cut_ml_minus_rhythm_aligned,-13.008,-24.109,-4.912
90.0,2.0,ml_alarm,92.732,4.567,69.147
90.0,2.0,rhythm_alarm,99.483,5.398,98.902
90.0,2.0,ml_forecast,83.081,3.65,47.01
90.0,2.0,rhythm_forecast,99.386,5.387,98.831
90.0,2.0,ml_aligned,86.775,3.679,45.634
90.0,2.0,rhythm_aligned,99.783,5.416,99.159
90.0,2.0,always_on,100.0,5.443,100.0
90.0,2.0,oracle,100.0,3.637,29.802
90.0,2.0,diff_cut_ml_minus_rhythm_aligned,-13.008,-23.949,-4.522
90.0,5.0,ml_alarm,92.732,7.168,69.147
90.0,5.0,rhythm_alarm,99.483,9.118,98.902
90.0,5.0,ml_forecast,83.081,5.419,47.01
90.0,5.0,rhythm_forecast,99.386,9.105,98.831
90.0,5.0,ml_aligned,86.775,5.396,45.634
90.0,5.0,rhythm_aligned,99.783,9.146,99.159
90.0,5.0,always_on,100.0,9.205,100.0
90.0,5.0,oracle,100.0,4.758,29.802
90.0,5.0,diff_cut_ml_minus_rhythm_aligned,-13.008,-23.921,-4.748
95.0,0.0,ml_alarm,95.379,2.869,75.791
95.0,0.0,rhythm_alarm,99.615,2.923,99.048
95.0,0.0,ml_forecast,94.753,2.796,75.984
95.0,0.0,rhythm_forecast,99.627,2.923,99.043
95.0,0.0,ml_aligned,91.649,2.717,49.748
95.0,0.0,rhythm_aligned,99.783,2.929,99.159
95.0,0.0,always_on,100.0,2.935,100.0
95.0,0.0,oracle,100.0,2.889,29.802
95.0,0.0,diff_cut_ml_minus_rhythm_aligned,-8.135,-13.834,-3.431
95.0,2.0,ml_alarm,95.379,4.77,75.791
95.0,2.0,rhythm_alarm,99.483,5.398,98.902
95.0,2.0,ml_forecast,94.753,4.702,75.984
95.0,2.0,rhythm_forecast,99.386,5.387,98.831
95.0,2.0,ml_aligned,91.649,3.964,49.748
95.0,2.0,rhythm_aligned,99.783,5.416,99.159
95.0,2.0,always_on,100.0,5.443,100.0
95.0,2.0,oracle,100.0,3.637,29.802
95.0,2.0,diff_cut_ml_minus_rhythm_aligned,-8.135,-13.582,-3.256
95.0,5.0,ml_alarm,95.379,7.621,75.791
95.0,5.0,rhythm_alarm,99.483,9.118,98.902
95.0,5.0,ml_forecast,94.753,7.56,75.984
95.0,5.0,rhythm_forecast,99.386,9.105,98.831
95.0,5.0,ml_aligned,91.649,5.836,49.748
95.0,5.0,rhythm_aligned,99.783,9.146,99.159
95.0,5.0,always_on,100.0,9.205,100.0

### reports/tables/site_scaleup.csv
case,strategy,avg_site_load_mw,extra_energy_pct,extra_mwh_per_year,extra_cost_usd_per_year,down_violations_per_hour,max_down_ramp_mw_per_s
synchronized,raw,79.747,0.0,0.0,0.0,184.257,
synchronized,always_burn,79.747,6.783,47382.551,3790604.072,171.84,
synchronized,predictive,79.747,2.576,17995.546,1439643.716,29.823,
synchronized,predictive_preramp,79.747,1.549,10822.864,865829.148,29.556,
synchronized,reactive,79.747,0.574,4011.56,320924.807,154.767,
synchronized,always_on_limiter,79.747,2.935,20506.048,1640483.804,0.0,
random_offsets,raw,77.828,0.0,0.0,0.0,0.0,2.077
random_offsets,always_burn,77.828,7.498,51122.607,4089808.557,0.0,1.014
random_offsets,predictive,77.828,2.345,15990.378,1279230.261,0.0,1.201
random_offsets,predictive_preramp,77.828,1.263,8610.273,688821.88,0.0,1.233
random_offsets,reactive,77.828,0.541,3688.313,295065.061,0.0,1.908
random_offsets,always_on_limiter,77.828,2.718,18533.671,1482693.689,0.0,1.1

### reports/tables/smoothing_by_workload.csv
workload,strategy,down_violations_per_node_hour,extra_energy_pct
inference_offline,always_burn,136.333,4.298
inference_offline,always_on_limiter,0.0,3.663
inference_offline,predictive,144.333,1.876
inference_offline,predictive_preramp,141.0,1.799
inference_offline,raw,229.0,0.0
inference_offline,reactive,155.333,0.809
inference_online_finite,always_burn,28.393,43.003
inference_online_finite,always_on_limiter,0.0,3.187
inference_online_finite,predictive,11.255,2.929
inference_online_finite,predictive_preramp,11.255,0.843
inference_online_finite,raw,72.133,0.0
inference_online_finite,reactive,61.39,0.673
inference_online_rate,always_burn,138.587,10.136
inference_online_rate,always_on_limiter,0.0,1.432
inference_online_rate,predictive,127.337,0.563
inference_online_rate,predictive_preramp,127.337,0.55
inference_online_rate,raw,151.884,0.0
inference_online_rate,reactive,15.597,1.331
train_llama2_70b_lora,always_burn,292.15,1.71
train_llama2_70b_lora,always_on_limiter,0.0,2.11
train_llama2_70b_lora,predictive,2.698,2.091
train_llama2_70b_lora,predictive_preramp,2.698,0.252
train_llama2_70b_lora,raw,295.035,0.0
train_llama2_70b_lora,reactive,289.638,0.059
train_stable_diffusion,always_burn,150.774,4.923
train_stable_diffusion,always_on_limiter,0.0,3.422
train_stable_diffusion,predictive,14.491,3.169
train_stable_diffusion,predictive_preramp,14.406,2.329
train_stable_diffusion,raw,151.964,0.0
train_stable_diffusion,reactive,131.736,0.64

### reports/tables/smoothing_per_trace.csv
trace_id,workload,strategy,peak_w,max_ramp_w_per_s,max_ramp_pct_peak_per_s,max_down_ramp_pct_peak_per_s,down_violations,all_violations,extra_energy_pct,extra_energy_kwh,deferred_pct,hours
inference_offline_b11,inference_offline,raw,2800.0,2250.368,80.37028571428571,73.04860714285715,228,407,0.0,0.0,0.0,1.0
inference_offline_b11,inference_offline,always_burn,2800.0,1265.1968000000002,45.18560000000001,19.592996428571414,132,256,4.520250234756346,0.10737377555555559,0.0,1.0
inference_offline_b11,inference_offline,predictive,2800.0,2241.1445000000003,80.04087500000001,72.38710714285713,148,325,1.6948332064723264,0.04025897480555553,0.0,1.0
inference_offline_b11,inference_offline,predictive_preramp,2800.0,2241.1445000000003,80.04087500000001,72.38710714285713,148,327,1.6099921289289667,0.03824366451410587,0.6435583644389683,1.0
inference_offline_b11,inference_offline,reactive,2800.0,2250.368,80.37028571428571,72.38710714285713,159,345,0.731706889410646,0.017380925222222208,0.0,1.0
inference_offline_b11,inference_offline,always_on_limiter,2800.0,1530.2530000000013,54.651892857142904,9.000000000000016,0,190,3.7891310828066205,0.09000681141666661,0.0,1.0
inference_offline_b12,inference_offline,raw,2800.0,2265.359,80.90567857142857,72.84819642857143,220,391,0.0,0.0,0.0,1.0
inference_offline_b12,inference_offline,always_burn,2800.0,1258.4645000000005,44.945160714285734,19.849074999999985,127,248,4.126187400000958,0.09862370737222224,0.0,1.0
inference_offline_b12,inference_offline,predictive,2800.0,2259.5644999999995,80.69873214285712,72.84819642857143,139,308,1.9293198289051339,0.04611440436111108,0.0,1.0
inference_offline_b12,inference_offline,predictive_preramp,2800.0,2168.4925000000003,77.44616071428572,72.84819642857143,136,307,1.8628644543416906,0.04452599482492402,0.5742626329182584,1.0
inference_offline_b12,inference_offline,reactive,2800.0,2259.5644999999995,80.69873214285712,72.84819642857143,147,323,0.8856071308116126,0.021167690666666652,0.0,1.0
inference_offline_b12,inference_offline,always_on_limiter,2800.0,1546.0150000000015,55.21482142857148,9.000000000000016,0,181,3.646340407975461,0.08715445386111105,0.0,1.0
inference_offline_b13,inference_offline,raw,2800.0,2262.9139999999998,80.81835714285712,72.03242857142858,239,416,0.0,0.0,0.0,1.0
inference_offline_b13,inference_offline,always_burn,2800.0,1267.9148999999998,45.28267499999999,19.838403571428575,150,284,4.250059924387797,0.1011055908388889,0.0,1.0
inference_offline_b13,inference_offline,predictive,2800.0,2262.9139999999998,80.81835714285712,71.19787500000001,146,325,2.0036986741353124,0.04766641927777774,0.0,1.0
inference_offline_b13,inference_offline,predictive_preramp,2800.0,2188.764,78.17014285714286,71.19787500000001,139,320,1.923418846501907,0.04575662516905379,0.6529779125096341,1.0
inference_offline_b13,inference_offline,reactive,2800.0,2262.9139999999998,80.81835714285712,72.03242857142858,160,341,0.8080907771007664,0.01922384552777777,0.0,1.0
inference_offline_b13,inference_offline,always_on_limiter,2800.0,1571.493500000001,56.12476785714289,9.000000000000016,0,191,3.5532454340336437,0.08452892086111106,0.0,1.0
inference_online_finite_b16,inference_online_finite,raw,2800.0,1923.771,68.70610714285715,66.98828571428572,72,162,0.0,0.0,0.0,1.0
inference_online_finite_b16,inference_online_finite,always_burn,2800.0,584.0065,20.857374999999998,17.592710714285708,23,58,41.961372071372224,0.6346762836833333,0.0,1.0
inference_online_finite_b16,inference_online_finite,predictive,2800.0,1923.771,68.70610714285715,66.98828571428572,12,102,2.5542830984918843,0.03863417291666659,0.0,1.0
inference_online_finite_b16,inference_online_finite,predictive_preramp,2800.0,1923.771,68.70610714285715,66.98828571428572,12,111,0.9993997512125984,0.01511617205783417,2.6298044980887387,1.0
inference_online_finite_b16,inference_online_finite,reactive,2800.0,1861.3359999999998,66.47628571428571,66.47628571428571,57,146,0.8643935302670064,0.01307416908333331,0.0,1.0
inference_online_finite_b16,inference_online_finite,always_on_limiter,2800.0,1271.7254999999998,45.418767857142846,9.000000000000016,0,90,2.935931377315116,0.044406698916666584,0.0,1.0
inference_online_finite_b17,inference_online_finite,raw,2800.0,1919.8544999999997,68.56623214285713,68.56623214285713,70,164,0.0,0.0,0.0,1.0
inference_online_finite_b17,inference_online_finite,always_burn,2800.0,1167.1559999999997,41.68414285714285,18.435150000000004,33,76,44.30889901234177,0.6602299005444445,0.0,1.0
inference_online_finite_b17,inference_online_finite,predictive,2800.0,1618.5744999999997,57.806232142857134,54.54885714285714,9,103,3.2759781854698544,0.04881409377777768,0.0,1.0
inference_online_finite_b17,inference_online_finite,predictive_preramp,2800.0,1618.5744999999997,57.806232142857134,54.54885714285714,9,109,0.75884235731053,0.011307218758843272,3.576102359091499,1.0
inference_online_finite_b17,inference_online_finite,reactive,2800.0,1919.8544999999997,68.56623214285713,68.56623214285713,66,160,0.4505346325973495,0.0067132436666666575,0.0,1.0
inference_online_finite_b17,inference_online_finite,always_on_limiter,2800.0,1270.5524999999998,45.37687499999999,9.000000000000016,0,95,3.4394273183819766,0.051249586583333236,0.0,1.0
inference_online_finite_b18,inference_online_finite,raw,2800.0,1844.8335000000002,65.88691071428572,65.88691071428572,72,169,0.0,0.0,0.0,1.0
inference_online_finite_b18,inference_online_finite,always_burn,2800.0,546.2586999999999,19.50923928571428,18.030575,32,73,45.92357691208486,0.6780363575888889,0.0,1.0
inference_online_finite_b18,inference_online_finite,predictive,2800.0,1279.1475,45.683839285714285,44.50317857142857,12,110,3.6149556687766173,0.053372832416666564,0.0,1.0
inference_online_finite_b18,inference_online_finite,predictive_preramp,2800.0,1279.1475,45.683839285714285,44.50317857142857,12,116,1.3893271461854653,0.02051265125759544,2.323432567055731,1.0
inference_online_finite_b18,inference_online_finite,reactive,2800.0,1759.3864999999996,62.83523214285713,62.83523214285713,56,153,1.0758335429855699,0.015884090611111085,0.0,1.0
inference_online_finite_b18,inference_online_finite,always_on_limiter,2800.0,1279.1475,45.683839285714285,9.000000000000016,0,96,3.899294697573771,0.057570941805555456,0.0,1.0
inference_online_finite_b19,inference_online_finite,raw,2800.0,1678.3945000000003,59.94266071428573,59.94266071428573,68,148,0.0,0.0,0.0,0.9094444444444445
inference_online_finite_b19,inference_online_finite,always_burn,2800.0,488.24490000000037,17.43731785714287,16.049657142857143,23,58,39.651259631941414,0.5538276725222223,0.0,0.9094444444444445
inference_online_finite_b19,inference_online_finite,predictive,2800.0,1678.3945000000003,59.94266071428573,59.94266071428573,11,91,2.2384915134874497,0.031266057027777724,0.0,0.9094444444444445
inference_online_finite_b19,inference_online_finite,predictive_preramp,2800.0,1678.3945000000003,59.94266071428573,59.94266071428573,11,99,0.18531980394137268,0.002588448302571611,4.761551909124387,0.9094444444444445
inference_online_finite_b19,inference_online_finite,reactive,2800.0,1678.3945000000003,59.94266071428573,59.94266071428573,61,141,0.2763946171056382,0.0038605327777777713,0.0,0.9094444444444445
inference_online_finite_b19,inference_online_finite,always_on_limiter,2800.0,1269.4340000000002,45.33692857142858,9.000000000000016,0,77,2.435673294775217,0.03402018711111105,0.0,0.9094444444444445
inference_online_rate_b14,inference_online_rate,raw,2800.0,2105.8180000000007,75.20778571428575,75.20778571428575,60,122,0.0,0.0,0.0,1.0
inference_online_rate_b14,inference_online_rate,always_burn,2800.0,1221.9385,43.64066071428571,19.857896428571426,52,111,9.53786471332738,0.2170327888777778,0.0,1.0
inference_online_rate_b14,inference_online_rate,predictive,2800.0,2105.8180000000007,75.20778571428575,75.20778571428575,46,113,0.43476527197448334,0.009893023472222207,0.0,1.0
inference_online_rate_b14,inference_online_rate,predictive_preramp,2800.0,2105.8180000000007,75.20778571428575,75.20778571428575,46,113,0.4061090989678838,0.009240956229383665,0.020580409877375853,1.0
inference_online_rate_b14,inference_online_rate,reactive,2800.0,1321.3505000000002,47.19108928571429,46.65294642857145,13,79,1.1923845464843685,0.027132544999999956,0.0,1.0
inference_online_rate_b14,inference_online_rate,always_on_limiter,2800.0,1252.587,44.73525,9.000000000000016,0,64,1.29738983619128,0.0295219258055555,0.0,1.0
inference_online_rate_b15,inference_online_rate,raw,2800.0,1726.3245000000002,61.65444642857143,57.50525,103,195,0.0,0.0,0.0,1.0
inference_online_rate_b15,inference_online_rate,always_burn,2800.0,616.2508999999995,22.0089607142857,19.690499999999993,90,170,10.034385686000183,0.22605405927222225,0.0,1.0
inference_online_rate_b15,inference_online_rate,predictive,2800.0,1726.3245000000002,61.65444642857143,57.50525,88,181,0.4520749228971541,0.010184317666666647,0.0,1.0
inference_online_rate_b15,inference_online_rate,predictive_preramp,2800.0,1726.3245000000002,61.65444642857143,57.50525,88,181,0.4502920449504044,0.0101441530955946,0.015702515746036847,1.0
inference_online_rate_b15,inference_online_rate,reactive,2800.0,1381.6280000000004,49.34385714285716,49.23691071428571,20,80,1.0575149814446043,0.02382363622222217,0.0,1.0
inference_online_rate_b15,inference_online_rate,always_on_limiter,2800.0,1250.7185,44.66851785714285,9.000000000000016,0,56,1.213702351755269,0.02734221624999995,0.0,1.0
inference_online_rate_b16,inference_online_rate,raw,2800.0,1942.0964999999999,69.36058928571428,69.36058928571428,185,341,0.0,0.0,0.0,1.0
inference_online_rate_b16,inference_online_rate,always_burn,2800.0,686.9153999999999,24.532692857142848,19.77550714285714,170,321,10.280417184469446,0.23124513093333335,0.0,1.0
inference_online_rate_b16,inference_online_rate,predictive,2800.0,1942.0964999999999,69.36058928571428,69.36058928571428,163,318,0.45971367355905207,0.010340684305555538,0.0,1.0
inference_online_rate_b16,inference_online_rate,predictive_preramp,2800.0,1942.0964999999999,69.36058928571428,69.36058928571428,163,315,0.45100587772419465,0.010144813325629323,0.02828528615734722,1.0
inference_online_rate_b16,inference_online_rate,reactive,2800.0,1255.9574999999998,44.85562499999999,33.93537500000001,11,95,1.3593822503827246,0.030577604083333276,0.0,1.0
inference_online_rate_b16,inference_online_rate,always_on_limiter,2800.0,1255.9574999999998,44.85562499999999,9.000000000000016,0,80,1.4086954293979084,0.03168684238888883,0.0,1.0
inference_online_rate_b17,inference_online_rate,raw,2800.0,2020.5565,72.16273214285714,72.16273214285714,246,467,0.0,0.0,0.0,0.910888888888889
inference_online_rate_b17,inference_online_rate,always_burn,2800.0,575.5012999999999,20.553617857142854,19.54116785714286,230,441,10.762252865473938,0.2178859016888889,0.0,0.910888888888889
inference_online_rate_b17,inference_online_rate,predictive,2800.0,1954.7935,69.81405357142857,69.6585,201,423,0.9467382849592446,0.019167076583333307,0.0,0.910888888888889
inference_online_rate_b17,inference_online_rate,predictive_preramp,2800.0,1950.438,69.6585,69.6585,201,422,0.9343865879146175,0.01891701177983939,0.03041771565422358,0.910888888888889
inference_online_rate_b17,inference_online_rate,reactive,2800.0,1721.373,61.477607142857146,40.96133928571429,17,132,1.758255438608394,0.035596549944444396,0.0,0.910888888888889
inference_online_rate_b17,inference_online_rate,always_on_limiter,2800.0,1235.125,44.111607142857146,9.000000000000016,0,106,1.8531334375511443,0.037517391111111055,0.0,0.910888888888889
train_llama2_70b_lora_16n_10742843_x3105c0s37b0n0,train_llama2_70b_lora,raw,2800.0,2089.9759999999997,74.642,74.642,166,344,0.0,0.0,0.0,0.5711111111111111
train_llama2_70b_lora_16n_10742843_x3105c0s37b0n0,train_llama2_70b_lora,always_burn,2800.0,1258.4569999999999,44.944892857142854,19.64547142857144,162,325,2.8799780103205177,0.03550987955555557,0.0,0.5711111111111111
train_llama2_70b_lora_16n_10742843_x3105c0s37b0n0,train_llama2_70b_lora,predictive,2800.0,1492.3250000000012,53.29732142857147,13.87864285714287,3,165,2.5392677827901715,0.031308951944444385,0.0,0.5711111111111111
train_llama2_70b_lora_16n_10742843_x3105c0s37b0n0,train_llama2_70b_lora,predictive_preramp,2800.0,1512.186,54.00664285714286,13.87864285714287,3,171,0.22745672091637723,0.002804521678602426,9.681928694602442,0.5711111111111111
train_llama2_70b_lora_16n_10742843_x3105c0s37b0n0,train_llama2_70b_lora,reactive,2800.0,2089.9759999999997,74.642,74.642,159,338,0.07211534365526547,0.0008891759444444434,0.0,0.5711111111111111
train_llama2_70b_lora_16n_10742843_x3105c0s37b0n0,train_llama2_70b_lora,always_on_limiter,2800.0,1492.3250000000012,53.29732142857147,9.000000000000016,0,163,2.5470967825163395,0.03140548283333327,0.0,0.5711111111111111
train_llama2_70b_lora_16n_10742843_x3105c0s41b0n0,train_llama2_70b_lora,raw,2800.0,2091.9890000000005,74.71389285714288,74.71389285714288,165,345,0.0,0.0,0.0,0.5711666666666667
train_llama2_70b_lora_16n_10742843_x3105c0s41b0n0,train_llama2_70b_lora,always_burn,2800.0,1329.317,47.47560714285715,19.582914285714292,162,325,2.9637138945165833,0.036620993733333364,0.0,0.5711666666666667
train_llama2_70b_lora_16n_10742843_x3105c0s41b0n0,train_llama2_70b_lora,predictive,2800.0,1439.3809999999999,51.40646428571428,14.659642857142867,3,166,2.5855857575637287,0.03194867088888883,0.0,0.5711666666666667
train_llama2_70b_lora_16n_10742843_x3105c0s41b0n0,train_llama2_70b_lora,predictive_preramp,2800.0,1445.344,51.61942857142857,14.659642857142867,3,171,0.24319991552044748,0.00300508851367187,9.760511108759715,0.5711666666666667
train_llama2_70b_lora_16n_10742843_x3105c0s41b0n0,train_llama2_70b_lora,reactive,2800.0,1783.5870000000002,63.699535714285716,63.699535714285716,160,339,0.07457239352631723,0.0009214503333333318,0.0,0.5711666666666667
train_llama2_70b_lora_16n_10742843_x3105c0s41b0n0,train_llama2_70b_lora,always_on_limiter,2800.0,1439.3809999999999,51.40646428571428,9.000000000000016,0,163,2.594330202800223,0.03205672122222216,0.0,0.5711666666666667
train_llama2_70b_lora_16n_10742843_x3106c0s13b0n0,train_llama2_70b_lora,raw,2800.0,1990.206,71.0787857142857,71.0787857142857,163,343,0.0,0.0,0.0,0.5711111111111111

### reports/tables/smoothing_summary.csv
strategy,down_violations_per_node_hour,all_violations_per_node_hour,median_max_down_ramp_pct_peak_per_s,extra_energy_pct,deferred_compute_pct,down_violation_cut_pct,all_violation_cut_pct
raw,184.257,351.75,70.859,0.0,0.0,0.0,0.0
always_burn,171.84,343.28,19.708,6.783,0.0,6.739,2.408
predictive,29.823,210.021,58.71,2.576,0.0,83.815,40.292
predictive_preramp,29.556,280.287,58.71,1.549,2.951,83.959,20.316
reactive,154.767,312.837,68.627,0.574,0.0,16.005,11.063
always_on_limiter,0.0,171.773,9.0,2.935,0.0,100.0,51.166

### reports/tables/transfer_harmonized.csv
test_dataset,setting,site_minutes,ap_ml,ap_rhythm,pos_rate,units,ap_diff,ap_diff_lo,ap_diff_hi,draw0_ap_ml,draw0_ap_rhythm,draw0_ap_diff,draw0_ap_diff_lo,draw0_ap_diff_hi,ap_ml_rep_mean,ap_ml_rep_min,ap_ml_rep_max,reps
nlr,lodo_shape,0.0,0.6496,0.6747,0.2497,12,-0.0251,-0.062,0.0204,,,,,,,,,
nlr,lodo_shape_adapted,5.0,,0.6747,0.2497,12,,,,0.6496,0.6747,-0.0251,-0.0638,0.0199,0.63,0.5573,0.6496,5.0
nlr,lodo_shape_adapted,15.0,,0.6747,0.2497,12,,,,0.5524,0.6747,-0.1223,-0.3506,0.1297,0.5927,0.5513,0.6496,5.0
nlr,lodo_shape_adapted,60.0,,0.6747,0.2497,12,,,,0.6362,0.6747,-0.0384,-0.2822,0.1643,0.7086,0.6246,0.7665,5.0
nlr,in_domain_shape,,0.9585,0.6747,0.2497,12,0.2839,0.216,0.3692,,,,,,,,,
elsayed,lodo_shape,0.0,0.8504,0.8829,0.5199,6,-0.0325,-0.3948,0.0415,,,,,,,,,
elsayed,lodo_shape_adapted,5.0,,0.8829,0.5199,6,,,,0.7636,0.8829,-0.1193,-0.3702,0.0206,0.8214,0.7636,0.8504,5.0
elsayed,lodo_shape_adapted,15.0,,0.8829,0.5199,6,,,,0.6614,0.8829,-0.2215,-0.4765,0.0117,0.7824,0.6614,0.877,5.0
elsayed,lodo_shape_adapted,60.0,,0.8829,0.5199,6,,,,0.853,0.8829,-0.0299,-0.4509,0.0698,0.8412,0.7954,0.9078,5.0
elsayed,in_domain_shape,,0.8825,0.8829,0.5199,6,-0.0003,-0.2035,0.085,,,,,,,,,
supercloud,lodo_shape,0.0,0.6592,0.7357,0.4782,112,-0.0765,-0.1198,-0.0356,,,,,,,,,
supercloud,lodo_shape_adapted,5.0,,0.7357,0.4782,112,,,,0.6592,0.7357,-0.0765,-0.1174,-0.0338,0.6227,0.5855,0.6592,5.0
supercloud,lodo_shape_adapted,15.0,,0.7357,0.4782,112,,,,0.6501,0.7357,-0.0856,-0.1332,-0.0419,0.6421,0.5714,0.6707,5.0
supercloud,lodo_shape_adapted,60.0,,0.7357,0.4782,112,,,,0.5818,0.7357,-0.1539,-0.2089,-0.0999,0.6383,0.5818,0.6923,5.0
supercloud,in_domain_shape,,0.8817,0.7357,0.4782,112,0.1461,0.1147,0.1851,,,,,,,,,

--- json ---

### reports/tables/key_numbers.json
{"best_model":"lightgbm","best_mae5":69.60932312314247,"rhythm_mae5":114.9067704154282,"persist_mae5":287.9507043001874,"gain_vs_rhythm":39.4210429276879,"clf":"lightgbm","recall":0.8242990654205608,"lead":4.8660430839002276,"fa_h":2.2841417611031556,"ep_prec":0.9723502304147466,"f1":0.868083916952653,"ap":0.9272654441159792,"rhythm_fa_h":120.34291984478784,"rhythm_recall":0.8345794392523365,"macro_recall":0.46610434266951994,"events":4280,"sd_share":0.7586448598130842,"pred_cut":83.815,"pred_energy":2.576,"burn_cut":6.739,"burn_energy":6.783,"pre_cut":83.959,"pre_energy":1.549,"pre_deferred":2.951,"lim_energy":2.935,"react_cut":16.005,"raw_viol_h":184.257,"site_burn_usd":3790604.072,"site_pred_usd":1439643.716,"site_pre_usd":865829.148,"site_lim_usd":1640483.804,"site_burn_mwh":47382.551,"site_pred_mwh":17995.546,"rand_raw_ramp":2.077,"rand_burn_usd":4089808.557,"rand_pred_usd":1279230.261,"energy_saving_vs_burn":62.02270381836945}

### reports/tables/sim_params.json
{"ramp_limit_frac_per_s":0.1,"floor_frac":0.8,"peak_window_s":60.0,"actuator_latency_s":1.0,"arm_hold_s":6.0,"safety":0.9,"forecast_trigger_frac":0.15,"site_mw":100.0,"price_per_mwh":80.0,"site_instances":400,"site_hours":2.0}

### paper/numbers.json
{"nlr_ap_ml":"0.96","nlr_ap_rh":"0.67","nlr_ap_old":"0.58","nlr_ap_rhalarm":"0.40","abl_matched_aligned_ap":"0.96","abl_matched_drop_ap":"0.58","abl_matched_diff":"0.37","abl_matched_diff_lo":"0.28","abl_matched_diff_hi":"0.49","abl_matched_drop_ap_on_drop_label":"0.93","abl_matched_aligned_ap_on_drop_label":"0.48","wl_train_llama2_70b_lora_ml":"1.00","wl_train_llama2_70b_lora_rh":"0.81","wl_train_stable_diffusion_ml":"0.96","wl_train_stable_diffusion_rh":"0.73","wl_inference_offline_ml":"0.55","wl_inference_offline_rh":"0.29","wl_inference_online_finite_ml":"0.76","wl_inference_online_finite_rh":"0.09","wl_inference_online_rate_ml":"0.65","wl_inference_online_rate_rh":"0.36","lat0_ml":"0.96","lat0_rh":"0.68","lat0p2_ml":"0.96","lat0p2_rh":"0.68","lat0p5_ml":"0.96","lat0p5_rh":"0.68","lat1_ml":"0.96","lat1_rh":"0.67","lat2_ml":"0.96","lat2_rh":"0.67","lat3_ml":"0.95","lat3_rh":"0.67","t80_sb0_ml_aligned_cut":"73.7","t80_sb0_ml_aligned_armed":"35.9","t80_sb0_ml_aligned_ovh":"2.0","t80_sb0_rhythm_aligned_cut":"74.4","t80_sb0_rhythm_aligned_armed":"43.3","t80_sb0_rhythm_aligned_ovh":"2.1","t80_sb0_ml_alarm_cut":"88.0","t80_sb0_ml_alarm_armed":"61.4","t80_sb0_ml_alarm_ovh":"2.8","t80_sb0_always_on_cut":"100.0","t80_sb0_always_on_armed":"100.0","t80_sb0_always_on_ovh":"2.9","t80_sb0_oracle_cut":"100.0","t80_sb0_oracle_armed":"29.8","t80_sb0_oracle_ovh":"2.9","t80_sb0_diff":"$-$0.7","t80_sb0_lo":"$-$6.0","t80_sb0_hi":"3.3","t80_sb2_ml_aligned_cut":"73.7","t80_sb2_ml_aligned_armed":"35.9","t80_sb2_ml_aligned_ovh":"2.9","t80_sb2_rhythm_aligned_cut":"74.4","t80_sb2_rhythm_aligned_armed":"43.3","t80_sb2_rhythm_aligned_ovh":"3.2","t80_sb2_ml_alarm_cut":"88.0","t80_sb2_ml_alarm_armed":"61.4","t80_sb2_ml_alarm_ovh":"4.3","t80_sb2_always_on_cut":"100.0","t80_sb2_always_on_armed":"100.0","t80_sb2_always_on_ovh":"5.4","t80_sb2_oracle_cut":"100.0","t80_sb2_oracle_armed":"29.8","t80_sb2_oracle_ovh":"3.6","t80_sb2_diff":"$-$0.7","t80_sb2_lo":"$-$6.3","t80_sb2_hi":"3.1","t90_sb0_ml_aligned_cut":"86.8","t90_sb0_ml_aligned_armed":"45.6","t90_sb0_ml_aligned_ovh":"2.5","t90_sb0_rhythm_aligned_cut":"99.8","t90_sb0_rhythm_aligned_armed":"99.2","t90_sb0_rhythm_aligned_ovh":"2.9","t90_sb0_ml_alarm_cut":"92.7","t90_sb0_ml_alarm_armed":"69.1","t90_sb0_ml_alarm_ovh":"2.8","t90_sb0_always_on_cut":"100.0","t90_sb0_always_on_armed":"100.0","t90_sb0_always_on_ovh":"2.9","t90_sb0_oracle_cut":"100.0","t90_sb0_oracle_armed":"29.8","t90_sb0_oracle_ovh":"2.9","t90_sb0_diff":"$-$13.0","t90_sb0_lo":"$-$24.1","t90_sb0_hi":"$-$4.9","t90_sb2_ml_aligned_cut":"86.8","t90_sb2_ml_aligned_armed":"45.6","t90_sb2_ml_aligned_ovh":"3.7","t90_sb2_rhythm_aligned_cut":"99.8","t90_sb2_rhythm_aligned_armed":"99.2","t90_sb2_rhythm_aligned_ovh":"5.4","t90_sb2_ml_alarm_cut":"92.7","t90_sb2_ml_alarm_armed":"69.1","t90_sb2_ml_alarm_ovh":"4.6","t90_sb2_always_on_cut":"100.0","t90_sb2_always_on_armed":"100.0","t90_sb2_always_on_ovh":"5.4","t90_sb2_oracle_cut":"100.0","t90_sb2_oracle_armed":"29.8","t90_sb2_oracle_ovh":"3.6","t90_sb2_diff":"$-$13.0","t90_sb2_lo":"$-$23.9","t90_sb2_hi":"$-$4.5","t95_sb0_ml_aligned_cut":"91.6","t95_sb0_ml_aligned_armed":"49.7","t95_sb0_ml_aligned_ovh":"2.7","t95_sb0_rhythm_aligned_cut":"99.8","t95_sb0_rhythm_aligned_armed":"99.2","t95_sb0_rhythm_aligned_ovh":"2.9","t95_sb0_ml_alarm_cut":"95.4","t95_sb0_ml_alarm_armed":"75.8","t95_sb0_ml_alarm_ovh":"2.9","t95_sb0_always_on_cut":"100.0","t95_sb0_always_on_armed":"100.0","t95_sb0_always_on_ovh":"2.9","t95_sb0_oracle_cut":"100.0","t95_sb0_oracle_armed":"29.8","t95_sb0_oracle_ovh":"2.9","t95_sb0_diff":"$-$8.1","t95_sb0_lo":"$-$13.8","t95_sb0_hi":"$-$3.4","t95_sb2_ml_aligned_cut":"91.6","t95_sb2_ml_aligned_armed":"49.7","t95_sb2_ml_aligned_ovh":"4.0","t95_sb2_rhythm_aligned_cut":"99.8","t95_sb2_rhythm_aligned_armed":"99.2","t95_sb2_rhythm_aligned_ovh":"5.4","t95_sb2_ml_alarm_cut":"95.4","t95_sb2_ml_alarm_armed":"75.8","t95_sb2_ml_alarm_ovh":"4.8","t95_sb2_always_on_cut":"100.0","t95_sb2_always_on_armed":"100.0","t95_sb2_always_on_ovh":"5.4","t95_sb2_oracle_cut":"100.0","t95_sb2_oracle_armed":"29.8","t95_sb2_oracle_ovh":"3.6","t95_sb2_diff":"$-$8.1","t95_sb2_lo":"$-$13.6","t95_sb2_hi":"$-$3.3","rh_max_cut":"99.8","arm80_ml":"43.1","arm80_rh":"51.6","arm80_alarm":"53.0","arm90_ml":"48.4","arm90_rh":"99.2","arm90_alarm":"64.3","arm95_ml":"58.4","arm95_rh":"99.2","arm95_alarm":"74.8","ml_max_cut":"99.8","oracle_armed":"29.8","an80_ml_aligned_armed":"43.1","an80_rhythm_aligned_armed":"51.5","an80_ml_alarm_armed":"53.0","an80_diff_vs_rhythm_aligned":"$-$8.5","an80_diff_vs_rhythm_aligned_lo":"$-$64.8","an80_diff_vs_rhythm_aligned_hi":"$-$3.0","an80_diff_vs_ml_alarm":"$-$9.9","an80_diff_vs_ml_alarm_lo":"$-$22.2","an80_diff_vs_ml_alarm_hi":"$-$4.4","an90_ml_aligned_armed":"48.4","an90_rhythm_aligned_armed":"99.2","an90_ml_alarm_armed":"64.3","an90_diff_vs_rhythm_aligned":"$-$50.8","an90_diff_vs_rhythm_aligned_lo":"$-$57.4","an90_diff_vs_rhythm_aligned_hi":"$-$8.8","an90_diff_vs_ml_alarm":"$-$15.9","an90_diff_vs_ml_alarm_lo":"$-$25.7","an90_diff_vs_ml_alarm_hi":"$-$3.9","an95_ml_aligned_armed":"58.4","an95_rhythm_aligned_armed":"99.2","an95_ml_alarm_armed":"74.8","an95_diff_vs_rhythm_aligned":"$-$40.8","an95_diff_vs_rhythm_aligned_lo":"$-$49.1","an95_diff_vs_rhythm_aligned_hi":"$-$31.4","an95_diff_vs_ml_alarm":"$-$16.4","an95_diff_vs_ml_alarm_lo":"$-$26.3","an95_diff_vs_ml_alarm_hi":"0.5","burn_cut":"6.7","burn_ovh":"6.8","raw_viol_h":"184.3","x_in_domain_nlr_ml":"0.96","x_in_domain_nlr_rh":"0.67","x_in_domain_nlr_lo":"0.22","x_in_domain_nlr_hi":"0.36","x_in_domain_elsayed_ml":"0.93","x_in_domain_elsayed_rh":"0.88","x_in_domain_elsayed_lo":"$-$0.11","x_in_domain_elsayed_hi":"0.09","x_in_domain_supercloud_ml":"0.88","x_in_domain_supercloud_rh":"0.74","x_in_domain_supercloud_lo":"0.11","x_in_domain_supercloud_hi":"0.19","x_lodo_nlr_ml":"0.53","x_lodo_nlr_rh":"0.67","x_lodo_nlr_lo":"$-$0.23","x_lodo_nlr_hi":"$-$0.02","x_lodo_elsayed_ml":"0.84","x_lodo_elsayed_rh":"0.88","x_lodo_elsayed_lo":"$-$0.43","x_lodo_elsayed_hi":"0.05","x_lodo_supercloud_ml":"0.68","x_lodo_supercloud_rh":"0.74","x_lodo_supercloud_lo":"$-$0.10","x_lodo_supercloud_hi":"$-$0.02","x_pooled_nlr_ml":"0.96","x_pooled_nlr_rh":"0.67","x_pooled_nlr_lo":"0.22","x_pooled_nlr_hi":"0.37","x_pooled_elsayed_ml":"0.92","x_pooled_elsayed_rh":"0.88","x_pooled_elsayed_lo":"$-$0.13","x_pooled_elsayed_hi":"0.08","x_pooled_supercloud_ml":"0.88","x_pooled_supercloud_rh":"0.74","x_pooled_supercloud_lo":"0.11","x_pooled_supercloud_hi":"0.18","tr_lodo_shape_nlr_ml":"0.65","tr_lodo_shape_nlr_lo":"$-$0.06","tr_lodo_shape_nlr_hi":"0.02","tr_lodo_shape_adapted5_nlr_ml":"0.63","tr_lodo_shape_adapted5_nlr_min":"0.56","tr_lodo_shape_adapted5_nlr_max":"0.65","tr_lodo_shape_adapted15_nlr_ml":"0.59","tr_lodo_shape_adapted15_nlr_min":"0.55","tr_lodo_shape_adapted15_nlr_max":"0.65","tr_lodo_shape_adapted60_nlr_ml":"0.71","tr_lodo_shape_adapted60_nlr_min":"0.62","tr_lodo_shape_adapted60_nlr_max":"0.77","tr_in_domain_shape_nlr_ml":"0.96","tr_in_domain_shape_nlr_lo":"0.22","tr_in_domain_shape_nlr_hi":"0.37","tr_lodo_shape_elsayed_ml":"0.85","tr_lodo_shape_elsayed_lo":"$-$0.39","tr_lodo_shape_elsayed_hi":"0.04","tr_lodo_shape_adapted5_elsayed_ml":"0.82","tr_lodo_shape_adapted5_elsayed_min":"0.76","tr_lodo_shape_adapted5_elsayed_max":"0.85","tr_lodo_shape_adapted15_elsayed_ml":"0.78","tr_lodo_shape_adapted15_elsayed_min":"0.66","tr_lodo_shape_adapted15_elsayed_max":"0.88","tr_lodo_shape_adapted60_elsayed_ml":"0.84","tr_lodo_shape_adapted60_elsayed_min":"0.80","tr_lodo_shape_adapted60_elsayed_max":"0.91","tr_in_domain_shape_elsayed_ml":"0.88","tr_in_domain_shape_elsayed_lo":"$-$0.20","tr_in_domain_shape_elsayed_hi":"0.09","tr_lodo_shape_supercloud_ml":"0.66","tr_lodo_shape_supercloud_lo":"$-$0.12","tr_lodo_shape_supercloud_hi":"$-$0.04","tr_lodo_shape_adapted5_supercloud_ml":"0.62","tr_lodo_shape_adapted5_supercloud_min":"0.59","tr_lodo_shape_adapted5_supercloud_max":"0.66","tr_lodo_shape_adapted15_supercloud_ml":"0.64","tr_lodo_shape_adapted15_supercloud_min":"0.57","tr_lodo_shape_adapted15_supercloud_max":"0.67","tr_lodo_shape_adapted60_supercloud_ml":"0.64","tr_lodo_shape_adapted60_supercloud_min":"0.58","tr_lodo_shape_adapted60_supercloud_max":"0.69","tr_in_domain_shape_supercloud_ml":"0.88","tr_in_domain_shape_supercloud_lo":"0.11","tr_in_domain_shape_supercloud_hi":"0.19","sc_classes_sig":"7","sc_classes":"7","rd_in_domain_nlr_learned_80_cut":"74.5","rd_in_domain_nlr_learned_80_armed":"34.8","rd_in_domain_nlr_learned_90_cut":"87.9","rd_in_domain_nlr_learned_90_armed":"44.0","rd_in_domain_nlr_learned_95_cut":"92.0","rd_in_domain_nlr_learned_95_armed":"48.5","rd_in_domain_nlr_rhythm_80_cut":"74.5","rd_in_domain_nlr_rhythm_80_armed":"41.7","rd_in_domain_nlr_rhythm_90_cut":"99.8","rd_in_domain_nlr_rhythm_90_armed":"99.1","rd_in_domain_nlr_rhythm_95_cut":"99.8","rd_in_domain_nlr_rhythm_95_armed":"99.1","rd_in_domain_elsayed_learned_80_cut":"67.3","rd_in_domain_elsayed_learned_80_armed":"39.7","rd_in_domain_elsayed_learned_90_cut":"81.1","rd_in_domain_elsayed_learned_90_armed":"53.1","rd_in_domain_elsayed_learned_95_cut":"88.7","rd_in_domain_elsayed_learned_95_armed":"68.5","rd_in_domain_elsayed_rhythm_80_cut":"66.2","rd_in_domain_elsayed_rhythm_80_armed":"50.9","rd_in_domain_elsayed_rhythm_90_cut":"67.3","rd_in_domain_elsayed_rhythm_90_armed":"51.8","rd_in_domain_elsayed_rhythm_95_cut":"91.3","rd_in_domain_elsayed_rhythm_95_armed":"69.7","rd_in_domain_supercloud_learned_80_cut":"77.8","rd_in_domain_supercloud_learned_80_armed":"42.5","rd_in_domain_supercloud_learned_90_cut":"88.3","rd_in_domain_supercloud_learned_90_armed":"54.2","rd_in_domain_supercloud_learned_95_cut":"95.6","rd_in_domain_supercloud_learned_95_armed":"66.0","rd_in_domain_supercloud_rhythm_80_cut":"99.8","rd_in_domain_supercloud_rhythm_80_armed":"99.3","rd_in_domain_supercloud_rhythm_90_cut":"99.8","rd_in_domain_supercloud_rhythm_90_armed":"99.3","rd_in_domain_supercloud_rhythm_95_cut":"99.8","rd_in_domain_supercloud_rhythm_95_armed":"99.3","rd_lodo_nlr_learned_80_cut":"73.6","rd_lodo_nlr_learned_80_armed":"43.6","rd_lodo_nlr_learned_90_cut":"90.3","rd_lodo_nlr_learned_90_armed":"58.0","rd_lodo_nlr_learned_95_cut":"95.6","rd_lodo_nlr_learned_95_armed":"67.0","rd_lodo_nlr_rhythm_80_cut":"74.5","rd_lodo_nlr_rhythm_80_armed":"41.7","rd_lodo_nlr_rhythm_90_cut":"99.8","rd_lodo_nlr_rhythm_90_armed":"99.1","rd_lodo_nlr_rhythm_95_cut":"99.8","rd_lodo_nlr_rhythm_95_armed":"99.1","rd_lodo_elsayed_learned_80_cut":"74.9","rd_lodo_elsayed_learned_80_armed":"47.2","rd_lodo_elsayed_learned_90_cut":"84.0","rd_lodo_elsayed_learned_90_armed":"53.9","rd_lodo_elsayed_learned_95_cut":"90.0","rd_lodo_elsayed_learned_95_armed":"67.6","rd_lodo_elsayed_rhythm_80_cut":"66.2","rd_lodo_elsayed_rhythm_80_armed":"50.9","rd_lodo_elsayed_rhythm_90_cut":"67.3","rd_lodo_elsayed_rhythm_90_armed":"51.8","rd_lodo_elsayed_rhythm_95_cut":"91.3","rd_lodo_elsayed_rhythm_95_armed":"69.7","rd_lodo_supercloud_learned_80_cut":"82.8","rd_lodo_supercloud_learned_80_armed":"65.0","rd_lodo_supercloud_learned_90_cut":"92.8","rd_lodo_supercloud_learned_90_armed":"80.5","rd_lodo_supercloud_learned_95_cut":"97.0","rd_lodo_supercloud_learned_95_armed":"89.8","rd_lodo_supercloud_rhythm_80_cut":"99.8","rd_lodo_supercloud_rhythm_80_armed":"99.3","rd_lodo_supercloud_rhythm_90_cut":"99.8","rd_lodo_supercloud_rhythm_90_armed":"99.3","rd_lodo_supercloud_rhythm_95_cut":"99.8","rd_lodo_supercloud_rhythm_95_armed":"99.3","rd_pooled_nlr_learned_80_cut":"74.6","rd_pooled_nlr_learned_80_armed":"36.0","rd_pooled_nlr_learned_90_cut":"88.2","rd_pooled_nlr_learned_90_armed":"44.0","rd_pooled_nlr_learned_95_cut":"93.2","rd_pooled_nlr_learned_95_armed":"48.9","rd_pooled_nlr_rhythm_80_cut":"74.5","rd_pooled_nlr_rhythm_80_armed":"41.7","rd_pooled_nlr_rhythm_90_cut":"99.8","rd_pooled_nlr_rhythm_90_armed":"99.1","rd_pooled_nlr_rhythm_95_cut":"99.8","rd_pooled_nlr_rhythm_95_armed":"99.1","rd_pooled_elsayed_learned_80_cut":"81.6","rd_pooled_elsayed_learned_80_armed":"51.2","rd_pooled_elsayed_learned_90_cut":"83.4","rd_pooled_elsayed_learned_90_armed":"55.4","rd_pooled_elsayed_learned_95_cut":"86.8","rd_pooled_elsayed_learned_95_armed":"61.4","rd_pooled_elsayed_rhythm_80_cut":"66.2","rd_pooled_elsayed_rhythm_80_armed":"50.9","rd_pooled_elsayed_rhythm_90_cut":"67.3","rd_pooled_elsayed_rhythm_90_armed":"51.8","rd_pooled_elsayed_rhythm_95_cut":"91.3","rd_pooled_elsayed_rhythm_95_armed":"69.7","rd_pooled_supercloud_learned_80_cut":"80.6","rd_pooled_supercloud_learned_80_armed":"45.1","rd_pooled_supercloud_learned_90_cut":"87.7","rd_pooled_supercloud_learned_90_armed":"53.6","rd_pooled_supercloud_learned_95_cut":"95.4","rd_pooled_supercloud_learned_95_armed":"65.8","rd_pooled_supercloud_rhythm_80_cut":"99.8","rd_pooled_supercloud_rhythm_80_armed":"99.3","rd_pooled_supercloud_rhythm_90_cut":"99.8","rd_pooled_supercloud_rhythm_90_armed":"99.3","rd_pooled_supercloud_rhythm_95_cut":"99.8","rd_pooled_supercloud_rhythm_95_armed":"99.3","nlr_node_h":"248","nlr_units":"49","nlr_test_units":"12","elsayed_node_h":"8","elsayed_units":"32","elsayed_test_units":"6","supercloud_node_h":"1,292","supercloud_units":"560","supercloud_test_units":"112"}

--- pdf info/text ---
Creator:         LaTeX with hyperref
Producer:        xdvipdfmx (0.1)
CreationDate:    Mon Nov  9 18:18:30 2026 EST
Custom Metadata: no
Metadata Stream: no
Tagged:          no
UserProperties:  no
Suspects:        no
Form:            none
JavaScript:      no
Pages:           4
Encrypted:       no
Page size:       612 x 792 pts (letter)
Page rot:        0
File size:       88036 bytes
Optimized:       no
PDF version:     1.5
                  Predict the Breach, Not the Drop:
               Control-Aligned Learning for Smoothing
                      AI Training Power Swings
                                                              Sayed Raheel
                                        Independent Researcher; Yeshiva University alumnus
                                                    shussai1@mail.yu.edu


    Abstract—Large AI training jobs swing GPU power by tens of          power is periodic, so “replay the last cycle” is a strong
percent within a second, and synchronized jobs can violate the          predictor. Our contributions:
ramp limits that utilities place on large loads. Fill-type smoothing
                                                                          • A control-aligned prediction target: a ramp-limit violation
(filler GPU work, storage) removes these violations but must be
engaged before the fall, and keeping it engaged costs energy.                that falls entirely inside the window a limiter armed now
Forecasting can decide when to engage it. We find that the choice            would cover, instead of a generic “large drop”.
of training target matters substantially. In a matched-pipeline           • A readiness analysis (violations removed versus time
ablation, a gradient-boosted classifier trained on the usual target,         engaged) comparing learned triggers, rhythm replay, an
“a large power drop is coming”, ranks the violations a ramp
limiter must catch poorly (average precision 0.58). Trained on               always-on limiter and a perfect-foresight oracle in one
the controller’s own event, “a ramp-limit violation will occur               simulator.
while a limiter armed now would be armed”, the same pipeline              • A three-dataset study (H100, B200, V100; benchmarks
reaches 0.96 (difference 95% CI 0.28 to 0.49) on held-out H100               and real jobs) with job-clustered confidence intervals,
training and inference traces, against 0.67 for no-learning rhythm           a sensor-harmonization step, and a negative result on
replay of the same target. With a threshold chosen on validation
for a 90% removal target, the learned trigger removes 86.8% of               unseen sites.
test violations with the actuator engaged 45.6% of the time, while
                                                                                                    II. DATA
rhythm replay meets the target only by staying engaged 99.2%
of the time, i.e. effectively always on. Across three public datasets      NLR [7]: 4×H100 nodes running MLPerf Llama2-70B
covering H100, B200 and V100 nodes and both benchmark and               LoRA and Stable Diffusion training on 1–16 nodes, plus three
real user jobs, the learned trigger has significantly higher AP         vLLM Llama3.1-70B inference benchmarks, NVML power at
than rhythm replay on two datasets when that site is in the
training data, after harmonizing sensor averaging; the third is         5–10 Hz, 248 node-hours (at most four nodes per job, which
inconclusive. Transfer to an unseen site is unreliable, which we        run nearly in lockstep, are kept; all are weighted equally in
report as an open problem.                                              metrics). Training jobs are split whole into train, validation and
    Index Terms—data centers, AI workloads, ramp rate, load             test; each inference benchmark is a single continuous session
forecasting, power smoothing, energy storage                            split in time, so its test portion counts as one independent
                                                                        unit. Elsayed et al. [8]: single 8×H100 and 8×B200 nodes
                        I. INTRODUCTION                                 running diffusion and Llama 1B–8B fine-tuning sweeps, 15-
                                                                        minute sessions, 32 unique sessions. MIT Supercloud [9]:
   Training a large model alternates compute-heavy and                  a stratified subset of 560 labelled jobs (80 per model class:
communication-heavy phases, so GPU power moves in fast,                 VGG, ResNet, Inception, U-Net, BERT, DistilBERT, GNN)
large steps. Because all nodes of a job step together, a syn-           on nodes with one or two V100s, nvidia-smi at 10 Hz, 1,292
chronized job appears to the grid as one large swing; industry          node-hours of real user jobs.
reports describe swings of tens to hundreds of megawatts                   All traces are averaged onto a 0.2 s grid and expressed
and evaluate software power burning, GPU power floors and               as “NLR-equivalent watts” (power × 2.8 kW divided by the
rack storage as mitigations [1]. Hardware filters and storage           node’s rated GPU power), so a 10%/s limit means the same
that react to the measured load are being developed [2],                fraction of rated power everywhere. Jobs are assigned whole
[3]; predictive storage control has been studied with perfect           to train, validation and test (about 60/20/20). For the control-
preview [4] and with short delay-compensating predictors [5];           aligned models, validation units are split into two halves, one
and AI data center load has been forecast at minute scales [6].         for early stopping and one for choosing operating points; for
We are not aware of work that studies how the forecasting               NLR inference the validation halves are alternate hour blocks
target affects smoothing performance.                                   of the same session and so are not independent. (The big-
   A fill-type actuator must be engaged before the fall arrives,        drop baselines from earlier work were early-stopped on all
but engagement costs energy and readiness (a hot inverter, pre-         validation units.)
warmed filler kernels). A forecaster can engage the actuator               Sensor harmonization. NVML documents that on recent
only when needed. The obvious competitor is free: training              architectures the default power reading is averaged over about
1 s, while older GPUs such as the V100 report instantaneous                                       TABLE I
power. The NLR documentation does not state which reading                  NLR TEST AP ON THE CONTROL-ALIGNED TARGET (1 S LATENCY).
was logged. Raw V100 traces flicker: without harmonization,
                                                                             Workload                       Learned   Rhythm replay
91% of Supercloud test seconds are labelled “violation immi-
nent”. We apply a 1 s trailing mean to Supercloud so that all                Llama2-70B LoRA training        1.00         0.81
                                                                             Stable Diffusion training       0.96         0.73
three datasets are compared at similar effective bandwidth.                  Offline inference               0.55         0.29
                                                                             Online inference, finite        0.76         0.09
                  III. PROBLEM AND METHODS                                   Online inference, fixed rate    0.65         0.36
A. Ramp limit, limiter and readiness
    A violation starts when the node’s 1 s down-ramp exceeds
10% of rated power. A fill-type limiter adds power only when                                      IV. RESULTS
the load falls faster than the limit allows, then tapers at 90%      A. Training target
of the allowed rate. A trigger issued at row t acts one sample
                                                                        On NLR test traces, rhythm replay ranks the control-aligned
later (each row averages [t, t+0.2 s)), engages the limiter after
                                                                     event with AP 0.67; LightGBM trained on the control-aligned
an actuator latency L (1 s unless stated) and arms it for 6 s;
                                                                     target reaches 0.96, and the gain holds for each workload
the limiter keeps filling until it meets the load. We count
                                                                     (Table I). Matched label ablation. Training the big-drop label
as engaged every sample where the limiter is armed or still
                                                                     through the same pipeline (same rows, features, LightGBM
filling, and report violations removed against engaged time,
                                                                     settings, early-stopping data and metric, and square-root class-
plus energy overhead with a standby draw of 0–5% of rated
                                                                     weighting rule, which gives weight 1.75 for the aligned and
power while engaged. References: always-on, always-burn (a
                                                                     2.57 for the big-drop target) yields AP 0.58 on the aligned
floor at 80% of the trailing 60 s peak, which removes only
                                                                     event against 0.96, a paired cluster-bootstrap difference of 0.37
6.7% of violations for 6.8% extra energy) and an oracle that
                                                                     (95% CI 0.28 to 0.49, 12 clusters). The big-drop model is good
arms just in time for every violation, including those induced
                                                                     at its own task (AP 0.93 on the big-drop event, where the
by the limiter itself.
                                                                     aligned model reaches 0.48): the two labels describe different
B. Targets                                                           events. Results are stable across actuator latencies (AP 0.96 at
                                                                     0 s, 0.95 at 3 s; rhythm replay 0.68 and 0.67).
   The big-drop target labels t positive if a fall of more than
30% of the recent peak within 1 s starts in the next 5 s. The
                                                                     B. Readiness
control-aligned target labels t positive if the whole 1 s ramp
window of a raw violation lies inside the 6 s window during             Fig. 1 sweeps each trigger’s threshold (about 200 validation-
which a trigger at t keeps the limiter armed, so the limiter is      score quantiles) on NLR test traces. Every trigger can reach
armed throughout that fall. Violations induced by the limiter        high removal by staying engaged long enough; what differs
itself are not labelled. Many violations (e.g. the 22% square        is the engaged time needed (Table II). Table II reads the best
wave of Llama LoRA training) are not big drops, so the two           threshold off each test curve, so it is a retrospective comparison
targets differ substantially.                                        of attainable trade-offs, not a deployable operating point; the
                                                                     validation-chosen operating points follow below. To remove
C. Predictors                                                        90% of violations, the control-aligned learned trigger needs
   Rhythm replay estimates the period P from a trailing 120 s        48.4% engaged time, whereas rhythm replay of the same target
autocorrelation, predicts p̂(t + k) = p(t + k − P ⌈k/P ⌉),           reaches 90% only at 99.2%, i.e. it is no better than always-on.
and scores the largest predicted 1 s down-ramp inside the            The paired cluster-bootstrap difference is −50.8 points (95%
target window; it needs no training. The learned predictor is        CI −57.4 to −8.8), and −40.8 points at 95% removal (CI
LightGBM on 56 trailing features (lags, differences, rolling         −49.1 to −31.4). The learned big-drop trigger needs more
statistics, time since recent steps and drops, rhythm period,        engaged time than the control-aligned one (64.3% at 90%;
phase and rhythm forecasts), one model per actuator latency.         difference −15.9 points, CI −25.7 to −3.9). At 95% removal
A shape-only variant divides every level feature by the trailing     the interval includes zero (CI −26.3 to 0.5), so with 12 test
60 s maximum.                                                        clusters the target’s effect is clearest in ranking quality (AP
                                                                     0.58 vs 0.96). The oracle removes all violations at 29.8%
D. Evaluation                                                        engaged time, which bounds what better prediction could still
   Ranking quality is average precision (AP) on test rows.           gain.
Uncertainty is a paired bootstrap over independent clusters             With operating points chosen on validation and a standby
(training jobs, or inference sessions; 1000 resamples). Oper-        draw of 2% of rated power, a 90% target gives 86.8% removal
ating points are chosen on the validation threshold half and         at 45.6% engaged time and 3.7% energy overhead for the
scored on test. All intervals are conditional on the single fitted   learned trigger; rhythm replay meets the target only by staying
model and split: they resample test clusters but do not retrain.     engaged 99.2% of the time (5.4% overhead, versus 5.4% for
Cross-dataset comparisons score one decision per second; the         always-on). At an 80% target the validation-chosen learned
NLR readiness analysis scores every 0.2 s row.                       threshold undershoots on test (73.7% removal), a reminder
                                TABLE II
   ENGAGED TIME (% OF TIME) NEEDED TO REACH A VIOLATION-REMOVAL LEVEL,                                                     NLR (4xH100): in-domain
                          NLR TEST, 1 S LATENCY.                                                                              NLR (4xH100): pooled

               Removal                  Learned, aligned   Rhythm, aligned    Learned, big-drop               NLR (4xH100): unseen site, shape-only

               80%                           43.1               51.5                  53.0                        Supercloud (1-2xV100): in-domain
               90%                           48.4               99.2                  64.3                           Supercloud (1-2xV100): pooled
               95%                           58.4               99.2                  74.8
                                                                                                     Supercloud (1-2xV100): unseen site, shape-only
                                                                                                                  Elsayed (8xH100/B200): in-domain
                              100
                                                                                                                     Elsayed (8xH100/B200): pooled
Ramp violations removed (%)




                                                                                                     Elsayed (8xH100/B200): unseen site, shape-only
                               80
                                                                                                                                                      −0.25 0.00 0.25
                                                                                                                                          AP difference, learned minus rhythm
                               60
                                                                                                   Fig. 2. AP difference between the learned control-aligned trigger and rhythm
                               40                                 Learned, aligned target          replay, with 95% cluster bootstrap intervals. Red: learned significantly better;
                                                                  Rhythm replay, aligned target    blue: rhythm significantly better.
                                                                  Learned, big-drop target
                               20                                 Rhythm, big-drop target
                                                                  Oracle                           data; in our experiments a learned trigger needed the site in
                                                                  Always-on                        its training set.
                                0
                                    0          20          40          60        80          100                   V. DISCUSSION AND LIMITATIONS
                                                       Engaged time (%)                               Sensors. If NLR and Elsayed power is NVML’s 1 s average,
                                                                                                   true ramps are faster than measured and measured lead times
Fig. 1. Violations removed versus engaged time on NLR test traces (1 s                             are optimistic. Simulation. The actuator is an idealized limiter
latency, dense threshold sweep). Always-on removes everything but is always                        with fixed latency, hold time and standby draw; storage capac-
engaged.
                                                                                                   ity, state of charge, eﬀiciency and wear are not modelled, and
                                                                                                   standby cost is an assumed fraction of rated power. Workloads.
that operating points chosen on few validation jobs transfer                                       NLR and Elsayed are scripted benchmarks; NLR inference
imperfectly.                                                                                       falls are dominated by gaps between benchmark runs, and
                                                                                                   each NLR inference workload is a single session. Supercloud
C. Across sites and GPUs                                                                           adds real jobs on older V100 nodes. Scale. Results are per
   Fig. 2 summarizes the learned-minus-rhythm AP difference.                                       node; synchronized multi-node jobs scale the same swing,
Trained on the test site’s own training jobs (in-domain) or                                        while desynchronized jobs partly cancel. Licences. Supercloud
on all three datasets (pooled), the learned trigger significantly                                  is CC BY-NC-ND and the Elsayed archive README states
beats rhythm replay on NLR (pooled AP 0.96 vs 0.67) and                                            CC BY-NC-ND; both were used for research only and are not
on real Supercloud jobs (pooled 0.88 vs 0.74; exploratory per-                                     redistributed.
class intervals, without multiplicity correction, are positive for                                                         VI. CONCLUSION
7 of 7 model classes). On Elsayed the point estimate favours                                          For fill-type smoothing of AI power swings, a forecaster
learning (0.92 vs 0.88) but the interval includes zero with                                        should be trained on the controller’s event, a ramp-limit viola-
six test sessions, and rhythm replay is better on its diffusion                                    tion inside the actuator’s engagement window, rather than on
sessions; we hypothesize that their very regular cadence suits                                     a generic large drop. With that target a small gradient-boosted
replay, but two test sessions do not allow a firm conclusion.                                      model needs substantially less engaged time than rhythm
D. Unseen sites                                                                                    replay for the same violation removal on H100 benchmark
                                                                                                   traces, and ranks violations better (higher AP) on real V100
   When the test dataset is excluded from training, the learned                                    jobs, provided the site is represented in training. Closing the
trigger is not better than rhythm replay anywhere. With shape-                                     gap to the oracle and making learned triggers transfer to new
only features it reaches AP 0.65 on NLR (rhythm 0.67, CI of                                        sites are the natural next steps.
difference −0.06 to 0.02), 0.85 on Elsayed (rhythm 0.88), and
0.66 on Supercloud, significantly below rhythm replay (0.74;                                                 CODE AVAILABILITY AND USE OF AI TOOLS
CI −0.12 to −0.04). Continuing to train on 60 minutes of the                                         Code is available from the author on request; the datasets are
new site’s data (mean of five independent draws) gives 0.71                                        public from their original sources. Analysis code and text were
on NLR (range 0.62 to 0.77) and 0.64 on Supercloud (range                                          drafted with the help of AI coding and writing assistants and
0.58 to 0.69), so a short calibration period does not reliably                                     independently reviewed by a separate AI model. The author
recover the in-domain advantage. Rhythm replay needs no site                                       checked the results and is responsible for the content.
                                REFERENCES
[1] E. Choukse, B. Warrier, S. Heath, et al., “Power stabilization for AI
    training datacenters,” arXiv:2508.14318, 2025.
[2] D. Jensen, G. Wilkins, O. Nnorom Jr., H. Budd, R. Rajagopal,
    J. Rivas-Davila, and P. Levis, “EasyRider: Mitigating power transients
    in datacenter-scale training workloads,” arXiv:2604.15522, 2026.
[3] D. Jensen, G. Wilkins, O. Nnorom Jr., H. Budd, P. Levis, and J. Rivas,
    “Active filter design for buffering datacenter-scale power fluctuations from
    training AI,” arXiv:2609.13490, 2026.
[4] H. You, C. Lou, and J. Yang, “Source side mitigation of AI datacenter
    power fluctuations with a hybrid energy storage system and residual
    differentiable predictive control,” arXiv:2606.04869, 2026.
[5] X. Lyu, W. Du, S. M. Mohiuddin, and B. A. Ross, “Communica-
    tion delay robust control of BESS for AI training load smoothing,”
    arXiv:2609.22542, 2026.
[6] M. Mughees, Y. Li, Y. Chen, and Y. R. Li, “Short-term load forecasting for
    AI-data center,” arXiv:2503.07756, 2025 (accepted to IEEE PES General
    Meeting 2025).
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
[9] S. Samsi, M. L. Weiss, D. Bestor, et al., “The MIT Supercloud dataset,” in
    Proc. IEEE High Performance Extreme Computing Conf. (HPEC), 2021,
    pp. 1–8, doi:10.1109/HPEC49654.2021.9622850.

--- log/warnings if present ---
paper/build.log
3:warning: main.tex:55: Underfull \hbox (badness 1824) in paragraph at lines 47--55
4:warning: main.tex:238: Underfull \vbox (badness 10000) has occurred while \output is active
5:warning: main.tex:255: Underfull \hbox (badness 4429) in paragraph at lines 254--255
7:warning: main.tex:55: Underfull \hbox (badness 1824) in paragraph at lines 47--55
8:warning: main.tex:238: Underfull \vbox (badness 10000) has occurred while \output is active
9:warning: main.tex:255: Underfull \hbox (badness 4429) in paragraph at lines 254--255

codex
The core ablation values trace correctly to `ablation_info.json`, including AP 0.5834 versus 0.9584 and the 0.2770 to 0.4931 interval. I have found a substantive wording regression from the arXiv review: the conference paper again calls Supercloud workloads “real jobs,” although the accepted correction was “labelled cluster jobs.” I’m checking the remaining controller metrics and whether the conclusion overstates what the matched ablation establishes.
exec
/bin/zsh -lc "pdfinfo paper/main.pdf | rg 'Pages|Page size|File size|CreationDate|ModDate'
printf '\\n--- targeted tables ---\\n'; for f in reports/tables/regime_armed_needed.csv reports/tables/regime_map.csv reports/tables/regime_ml_vs_rhythm_ci.csv reports/tables/regime_pareto_test.csv reports/tables/regime_targets.csv reports/tables/latency.csv reports/tables/transfer_harmonized.csv reports/tables/site_scaleup.csv reports/tables/key_numbers.json; do printf '\\n### %s\\n' \""'$f"; if [[ "$f" == *.json ]]; then jq . "$f"; else sed -n '"'1,220p' \""'$f"; fi; done
printf '"'\\n--- template comparison and generated tokens ---\\n'; rg -n \"86\\.8|45\\.6|48\\.4|99\\.2|29\\.8|50\\.8|40\\.8|15\\.9|25\\.7|26\\.3|73\\.7|3\\.7|5\\.4|6\\.7|6\\.8|0\\.65|0\\.71|0\\.64|real jobs|labelled cluster\" paper/arxiv/main.tex paper/arxiv/template.tex paper/template.tex paper/main.tex reports data/processed/ablation_info.json | sed -n '1,320p'
printf '\\n--- git status / generation mapping ---\\n'; git status --short; rg -n \"ablation|matched|paper|regime_armed|numbers.json|template\" src/paper.py | sed -n '1,260p'" in /Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing
 succeeded in 0ms:
CreationDate:    Mon Nov  9 18:18:30 2026 EST
Pages:           4
Page size:       612 x 792 pts (letter)
File size:       88036 bytes

--- targeted tables ---

### reports/tables/regime_armed_needed.csv
target,ml_aligned_armed,rhythm_aligned_armed,ml_alarm_armed,diff_vs_rhythm_aligned,diff_vs_rhythm_aligned_lo,diff_vs_rhythm_aligned_hi,diff_vs_ml_alarm,diff_vs_ml_alarm_lo,diff_vs_ml_alarm_hi
80.0,43.07,51.55,52.97,-8.48,-64.75,-2.95,-9.89,-22.18,-4.41
90.0,48.39,99.16,64.29,-50.76,-57.38,-8.82,-15.89,-25.7,-3.89
95.0,58.38,99.16,74.78,-40.78,-49.08,-31.36,-16.4,-26.26,0.48

### reports/tables/regime_map.csv
start_s,standby_pct,latency_s,winner,winner_overhead_pct,winner_cut_pct,ml_alarm_cut,ml_alarm_overhead,rhythm_alarm_cut,rhythm_alarm_overhead,ml_forecast_cut,ml_forecast_overhead,rhythm_forecast_cut,rhythm_forecast_overhead,ml_aligned_cut,ml_aligned_overhead,rhythm_aligned_cut,rhythm_aligned_overhead,reactive_cut,reactive_overhead,always_on_cut,always_on_overhead,always_burn_cut,always_burn_overhead,oracle_cut,oracle_overhead
0.0,0.0,0.0,rhythm_aligned,2.241,79.266,89.868,2.796,76.041,2.157,77.894,2.527,75.271,2.132,76.402,2.182,79.266,2.241,39.35,2.528,100.0,2.935,6.739,6.783,100.0,2.889
0.0,0.0,0.2,rhythm_aligned,2.211,79.35,89.832,2.795,75.848,2.151,76.354,2.444,74.801,2.126,77.16,2.209,79.35,2.211,16.185,1.833,100.0,2.935,6.739,6.783,100.0,2.889
0.0,0.0,0.5,ml_aligned,2.059,73.742,89.759,2.794,75.788,2.141,76.101,2.38,74.669,2.116,73.742,2.059,79.314,2.193,15.776,1.258,100.0,2.935,6.739,6.783,100.0,2.889
0.0,0.0,1.0,ml_aligned,2.042,73.706,88.002,2.774,74.32,2.095,77.942,2.348,74.224,2.089,73.706,2.042,74.404,2.103,15.981,0.467,100.0,2.935,6.739,6.783,100.0,2.889
0.0,0.0,2.0,ml_aligned,2.068,74.428,89.037,2.784,75.584,2.112,76.029,2.304,74.452,2.081,74.428,2.068,78.977,2.162,16.27,0.478,100.0,2.935,6.739,6.783,100.0,2.889
0.0,0.0,3.0,ml_aligned,2.071,74.079,88.905,2.782,75.511,2.127,78.592,2.336,74.344,2.1,74.079,2.071,78.881,2.158,16.245,0.481,100.0,2.935,6.739,6.783,100.0,2.889
0.0,0.5,0.0,rhythm_forecast,2.387,75.271,89.868,3.194,76.041,2.424,77.894,2.79,75.271,2.387,76.402,2.436,79.266,2.537,39.35,2.893,100.0,3.562,6.739,6.783,100.0,3.076
0.0,0.5,0.2,rhythm_aligned,2.506,79.35,89.832,3.193,75.848,2.418,76.354,2.707,74.801,2.381,77.16,2.466,79.35,2.506,16.185,2.198,100.0,3.562,6.739,6.783,100.0,3.076
0.0,0.5,0.5,ml_aligned,2.296,73.742,89.759,3.192,75.788,2.408,76.101,2.643,74.669,2.371,73.742,2.296,79.314,2.488,15.776,1.623,100.0,3.562,6.739,6.783,100.0,3.076
0.0,0.5,1.0,ml_aligned,2.267,73.706,88.002,3.159,74.32,2.353,77.942,2.616,74.224,2.342,73.706,2.267,74.404,2.374,15.981,0.833,100.0,3.562,6.739,6.783,100.0,3.076
0.0,0.5,2.0,ml_aligned,2.297,74.428,89.037,3.181,75.584,2.379,76.029,2.566,74.452,2.336,74.428,2.297,78.977,2.455,16.27,0.844,100.0,3.562,6.739,6.783,100.0,3.076
0.0,0.5,3.0,ml_aligned,2.302,74.079,88.905,3.179,75.511,2.395,78.592,2.607,74.344,2.354,74.079,2.302,78.881,2.452,16.245,0.847,100.0,3.562,6.739,6.783,100.0,3.076
0.0,1.0,0.0,rhythm_forecast,2.642,75.271,89.868,3.592,76.041,2.692,77.894,3.052,75.271,2.642,76.402,2.691,79.266,2.832,39.35,3.259,100.0,4.189,6.739,6.783,100.0,3.263
0.0,1.0,0.2,rhythm_forecast,2.636,74.801,89.832,3.591,75.848,2.686,76.354,2.969,74.801,2.636,77.16,2.722,79.35,2.802,16.185,2.563,100.0,4.189,6.739,6.783,100.0,3.263
0.0,1.0,0.5,ml_aligned,2.533,73.742,89.759,3.59,75.788,2.676,76.101,2.905,74.669,2.626,73.742,2.533,79.314,2.783,15.776,1.989,100.0,4.189,6.739,6.783,100.0,3.263
0.0,1.0,1.0,ml_aligned,2.492,73.706,88.002,3.544,74.32,2.612,77.942,2.884,74.224,2.596,73.706,2.492,74.404,2.646,15.981,1.198,100.0,4.189,6.739,6.783,100.0,3.263
0.0,1.0,2.0,ml_aligned,2.525,74.428,89.037,3.579,75.584,2.647,76.029,2.828,74.452,2.59,74.428,2.525,78.977,2.749,16.27,1.21,100.0,4.189,6.739,6.783,100.0,3.263
0.0,1.0,3.0,ml_aligned,2.533,74.079,88.905,3.577,75.511,2.662,78.592,2.879,74.344,2.609,74.079,2.533,78.881,2.746,16.245,1.212,100.0,4.189,6.739,6.783,100.0,3.263
0.0,2.0,0.0,rhythm_forecast,3.152,75.271,89.868,4.389,76.041,3.227,77.894,3.577,75.271,3.152,76.402,3.2,79.266,3.423,39.35,3.99,100.0,5.443,6.739,6.783,100.0,3.637
0.0,2.0,0.2,rhythm_forecast,3.146,74.801,89.832,4.387,75.848,3.221,76.354,3.494,74.801,3.146,77.16,3.235,79.35,3.392,16.185,3.294,100.0,5.443,6.739,6.783,100.0,3.637
0.0,2.0,0.5,ml_aligned,3.007,73.742,89.759,4.385,75.788,3.211,76.101,3.43,74.669,3.136,73.742,3.007,79.314,3.372,15.776,2.72,100.0,5.443,6.739,6.783,100.0,3.637
0.0,2.0,1.0,ml_aligned,2.943,73.706,88.002,4.314,74.32,3.128,77.942,3.42,74.224,3.103,73.706,2.943,74.404,3.189,15.981,1.929,100.0,5.443,6.739,6.783,100.0,3.637
0.0,2.0,2.0,ml_aligned,2.981,74.428,89.037,4.373,75.584,3.181,76.029,3.352,74.452,3.1,74.428,2.981,78.977,3.337,16.27,1.941,100.0,5.443,6.739,6.783,100.0,3.637
0.0,2.0,3.0,ml_aligned,2.995,74.079,88.905,4.371,75.511,3.196,78.592,3.423,74.344,3.119,74.079,2.995,78.881,3.334,16.245,1.944,100.0,5.443,6.739,6.783,100.0,3.637
0.0,5.0,0.0,rhythm_forecast,4.683,75.271,89.868,6.777,76.041,4.832,77.894,5.152,75.271,4.683,76.402,4.727,79.266,5.196,39.35,6.183,100.0,9.205,6.739,6.783,100.0,4.758
0.0,5.0,0.2,rhythm_forecast,4.677,74.801,89.832,6.774,75.848,4.826,76.354,5.068,74.801,4.677,77.16,4.775,79.35,5.164,16.185,5.487,100.0,9.205,6.739,6.783,100.0,4.758
0.0,5.0,0.5,ml_aligned,4.43,73.742,89.759,6.772,75.788,4.815,76.101,5.004,74.669,4.666,73.742,4.43,79.314,5.141,15.776,4.912,100.0,9.205,6.739,6.783,100.0,4.758
0.0,5.0,1.0,ml_aligned,4.294,73.706,88.002,6.624,74.32,4.679,77.942,5.028,74.224,4.623,73.706,4.294,74.404,4.818,15.981,4.122,100.0,9.205,6.739,6.783,100.0,4.758
0.0,5.0,2.0,ml_aligned,4.351,74.428,89.037,6.757,75.584,4.784,76.029,4.924,74.452,4.628,74.428,4.351,78.977,5.1,16.27,4.135,100.0,9.205,6.739,6.783,100.0,4.758
0.0,5.0,3.0,ml_aligned,4.381,74.079,88.905,6.754,75.511,4.798,78.592,5.054,74.344,4.647,74.079,4.381,78.881,5.097,16.245,4.138,100.0,9.205,6.739,6.783,100.0,4.758
0.0,10.0,0.0,rhythm_forecast,7.235,75.271,89.868,10.758,76.041,7.508,77.894,7.777,75.271,7.235,76.402,7.272,79.266,8.15,39.35,9.839,100.0,15.475,6.739,6.783,100.0,6.626
0.0,10.0,0.2,rhythm_forecast,7.228,74.801,89.832,10.754,75.848,7.5,76.354,7.692,74.801,7.228,77.16,7.342,79.35,8.116,16.185,9.141,100.0,15.475,6.739,6.783,100.0,6.626
0.0,10.0,0.5,ml_aligned,6.8,73.742,89.759,10.75,75.788,7.489,76.101,7.627,74.669,7.217,73.742,6.8,79.314,8.088,15.776,8.566,100.0,15.475,6.739,6.783,100.0,6.626
0.0,10.0,1.0,ml_aligned,6.547,73.706,88.002,10.474,74.32,7.263,77.942,7.708,74.224,7.158,73.706,6.547,74.404,7.533,15.981,7.777,100.0,15.475,6.739,6.783,100.0,6.626
0.0,10.0,2.0,ml_aligned,6.634,74.428,89.037,10.729,75.584,7.455,76.029,7.544,74.452,7.176,74.428,6.634,78.977,8.039,16.27,7.791,100.0,15.475,6.739,6.783,100.0,6.626
0.0,10.0,3.0,ml_aligned,6.691,74.079,88.905,10.726,75.511,7.469,78.592,7.772,74.344,7.194,74.079,6.691,78.881,8.037,16.245,7.794,100.0,15.475,6.739,6.783,100.0,6.626
2.0,0.0,0.0,ml_alarm,2.991,99.783,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,39.35,14.655,100.0,2.997,6.739,6.783,100.0,14.579
2.0,0.0,0.2,ml_alarm,2.991,99.783,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,16.185,13.93,100.0,2.997,6.739,6.783,100.0,14.579
2.0,0.0,0.5,ml_alarm,2.991,99.783,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,15.776,13.334,100.0,2.997,6.739,6.783,100.0,14.579
2.0,0.0,1.0,rhythm_aligned,3.113,83.767,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,83.767,3.113,15.981,12.517,100.0,2.997,6.739,6.783,100.0,14.579
2.0,0.0,2.0,ml_alarm,2.99,99.759,99.759,2.99,99.759,2.99,99.759,2.99,99.759,2.99,99.759,2.99,99.759,2.99,16.27,12.536,100.0,2.997,6.739,6.783,100.0,14.579
2.0,0.0,3.0,ml_alarm,2.99,99.759,99.759,2.99,99.759,2.99,99.759,2.99,99.759,2.99,99.759,2.99,99.759,2.99,16.245,12.557,100.0,2.997,6.739,6.783,100.0,14.579
2.0,0.5,0.0,rhythm_forecast,3.658,83.237,99.783,3.612,83.369,3.638,99.783,3.612,83.237,3.658,99.783,3.612,83.598,4.097,39.35,15.02,100.0,3.624,6.739,6.783,100.0,14.766
2.0,0.5,0.2,rhythm_forecast,3.657,83.177,99.783,3.612,83.345,3.638,99.783,3.612,83.177,3.657,99.783,3.612,83.574,4.094,16.185,14.296,100.0,3.624,6.739,6.783,100.0,14.766
2.0,0.5,0.5,rhythm_forecast,3.656,83.117,99.783,3.612,83.321,3.64,99.783,3.612,83.117,3.656,99.783,3.612,83.586,4.095,15.776,13.699,100.0,3.624,6.739,6.783,100.0,14.766
2.0,0.5,1.0,rhythm_aligned,3.536,83.767,99.783,3.612,83.261,3.617,99.783,3.612,83.117,3.642,99.783,3.612,83.767,3.536,15.981,12.882,100.0,3.624,6.739,6.783,100.0,14.766
2.0,0.5,2.0,rhythm_forecast,3.631,83.165,99.759,3.612,83.381,3.641,99.759,3.612,83.165,3.631,99.759,3.612,83.574,4.087,16.27,12.902,100.0,3.624,6.739,6.783,100.0,14.766
2.0,0.5,3.0,rhythm_forecast,3.641,83.273,99.759,3.612,83.406,3.642,99.759,3.612,83.273,3.641,99.759,3.612,83.61,4.088,16.245,12.923,100.0,3.624,6.739,6.783,100.0,14.766
2.0,1.0,0.0,rhythm_forecast,4.078,83.237,99.783,4.234,83.369,4.06,99.783,4.234,83.237,4.078,99.783,4.234,83.598,4.518,39.35,15.386,100.0,4.251,6.739,6.783,100.0,14.953
2.0,1.0,0.2,rhythm_forecast,4.077,83.177,99.783,4.234,83.345,4.06,99.783,4.234,83.177,4.077,99.783,4.234,83.574,4.515,16.185,14.661,100.0,4.251,6.739,6.783,100.0,14.953
2.0,1.0,0.5,rhythm_forecast,4.076,83.117,99.783,4.234,83.321,4.062,99.783,4.234,83.117,4.076,99.783,4.234,83.586,4.516,15.776,14.065,100.0,4.251,6.739,6.783,100.0,14.953
2.0,1.0,1.0,rhythm_aligned,3.959,83.767,99.783,4.234,83.261,4.038,99.783,4.234,83.117,4.061,99.783,4.234,83.767,3.959,15.981,13.248,100.0,4.251,6.739,6.783,100.0,14.953
2.0,1.0,2.0,rhythm_forecast,4.05,83.165,99.759,4.234,83.381,4.063,99.759,4.234,83.165,4.05,99.759,4.234,83.574,4.507,16.27,13.267,100.0,4.251,6.739,6.783,100.0,14.953
2.0,1.0,3.0,rhythm_forecast,4.06,83.273,99.759,4.234,83.406,4.063,99.759,4.234,83.273,4.06,99.759,4.234,83.61,4.509,16.245,13.288,100.0,4.251,6.739,6.783,100.0,14.953
2.0,2.0,0.0,rhythm_forecast,4.918,83.237,99.783,5.478,83.369,4.904,99.783,5.478,83.237,4.918,76.402,8.481,83.598,5.361,39.35,16.117,100.0,5.505,6.739,6.783,100.0,15.327
2.0,2.0,0.2,rhythm_forecast,4.917,83.177,99.783,5.478,83.345,4.904,99.783,5.478,83.177,4.917,77.16,8.592,83.574,5.357,16.185,15.392,100.0,5.505,6.739,6.783,100.0,15.327
2.0,2.0,0.5,rhythm_forecast,4.915,83.117,99.783,5.478,83.321,4.906,99.783,5.478,83.117,4.915,77.665,8.822,83.586,5.358,15.776,14.796,100.0,5.505,6.739,6.783,100.0,15.327
2.0,2.0,1.0,rhythm_aligned,4.805,83.767,99.783,5.478,83.261,4.878,99.783,5.478,83.117,4.9,99.783,5.478,83.767,4.805,15.981,13.979,100.0,5.505,6.739,6.783,100.0,15.327
2.0,2.0,2.0,rhythm_forecast,4.888,83.165,99.759,5.477,83.381,4.905,99.759,5.477,83.165,4.888,78.761,9.119,83.574,5.349,16.27,13.998,100.0,5.505,6.739,6.783,100.0,15.327
2.0,2.0,3.0,rhythm_forecast,4.898,83.273,99.759,5.477,83.406,4.906,99.759,5.477,83.273,4.898,78.063,8.679,83.61,5.351,16.245,14.02,100.0,5.505,6.739,6.783,100.0,15.327
2.0,5.0,0.0,rhythm_aligned,10.772,79.266,99.783,9.208,83.369,7.437,81.035,12.319,76.619,10.111,76.402,10.008,79.266,10.772,39.35,18.31,100.0,9.267,6.739,6.783,100.0,16.448
2.0,5.0,0.2,rhythm_aligned,10.768,79.35,99.783,9.208,83.345,7.436,81.095,12.237,76.51,10.11,77.16,10.132,79.35,10.768,16.185,17.585,100.0,9.267,6.739,6.783,100.0,16.448
2.0,5.0,0.5,rhythm_aligned,10.76,79.314,99.783,9.208,75.788,10.773,81.119,12.177,76.366,10.1,77.665,10.371,79.314,10.76,15.776,16.988,100.0,9.267,6.739,6.783,100.0,16.448
2.0,5.0,1.0,rhythm_aligned,10.238,75.523,99.783,9.208,77.521,10.239,83.081,11.78,79.326,10.695,79.206,10.493,75.523,10.238,15.981,16.172,100.0,9.267,6.739,6.783,100.0,16.448
2.0,5.0,2.0,rhythm_aligned,10.701,78.977,99.759,9.207,75.584,10.735,81.059,12.083,76.149,10.059,78.761,10.685,78.977,10.701,16.27,16.192,100.0,9.267,6.739,6.783,100.0,16.448
2.0,5.0,3.0,rhythm_aligned,10.695,78.881,99.759,9.207,75.511,10.732,80.866,12.079,76.029,10.059,78.063,10.239,78.881,10.695,16.245,16.214,100.0,9.267,6.739,6.783,100.0,16.448
2.0,10.0,0.0,rhythm_aligned,13.726,79.266,89.868,17.024,76.041,13.461,81.035,15.166,76.619,12.777,76.402,12.553,79.266,13.726,39.35,21.966,100.0,15.537,6.739,6.783,100.0,18.316
2.0,10.0,0.2,rhythm_aligned,13.72,79.35,89.832,17.017,75.848,13.457,81.095,15.083,76.51,12.775,77.16,12.698,79.35,13.72,16.185,21.239,100.0,15.537,6.739,6.783,100.0,18.316
2.0,10.0,0.5,rhythm_aligned,13.708,79.314,89.759,17.011,75.788,13.447,81.119,15.022,76.366,12.765,77.665,12.952,79.314,13.708,15.776,20.642,100.0,15.537,6.739,6.783,100.0,18.316
2.0,10.0,1.0,rhythm_aligned,12.978,75.331,88.002,16.991,77.521,12.986,82.708,14.693,76.667,12.785,79.206,13.117,75.331,12.978,15.981,19.827,100.0,15.537,6.739,6.783,100.0,18.316
2.0,10.0,2.0,rhythm_aligned,13.64,78.977,89.037,16.999,75.584,13.406,81.059,14.926,76.149,12.721,78.761,13.296,78.977,13.64,16.27,19.849,100.0,15.537,6.739,6.783,100.0,18.316
2.0,10.0,3.0,rhythm_aligned,13.635,78.881,88.905,16.991,75.511,13.402,80.866,14.921,76.029,12.721,78.063,12.839,78.881,13.635,16.245,19.871,100.0,15.537,6.739,6.783,100.0,18.316
10.0,0.0,0.0,ml_alarm,3.238,99.783,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,39.35,63.163,100.0,3.244,6.739,6.783,100.0,61.339
10.0,0.0,0.2,ml_alarm,3.238,99.783,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,16.185,62.322,100.0,3.244,6.739,6.783,100.0,61.339
10.0,0.0,0.5,ml_alarm,3.238,99.783,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,15.776,61.639,100.0,3.244,6.739,6.783,100.0,61.339
10.0,0.0,1.0,ml_alarm,3.238,99.783,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,15.981,60.717,100.0,3.244,6.739,6.783,100.0,61.339
10.0,0.0,2.0,ml_alarm,3.237,99.759,99.759,3.237,99.759,3.237,99.759,3.237,99.759,3.237,99.759,3.237,99.759,3.237,16.27,60.766,100.0,3.244,6.739,6.783,100.0,61.339
10.0,0.0,3.0,ml_alarm,3.238,99.759,99.759,3.238,99.759,3.238,99.759,3.238,99.759,3.238,99.759,3.238,99.759,3.238,16.245,60.862,100.0,3.244,6.739,6.783,100.0,61.339
10.0,0.5,0.0,ml_alarm,3.86,99.783,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.86,39.35,63.529,100.0,3.871,6.739,6.783,100.0,61.526
10.0,0.5,0.2,ml_alarm,3.86,99.783,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.86,16.185,62.687,100.0,3.871,6.739,6.783,100.0,61.526
10.0,0.5,0.5,ml_alarm,3.86,99.783,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.86,15.776,62.004,100.0,3.871,6.739,6.783,100.0,61.526
10.0,0.5,1.0,rhythm_forecast,3.867,99.783,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.867,99.783,3.86,99.783,3.86,15.981,61.082,100.0,3.871,6.739,6.783,100.0,61.526
10.0,0.5,2.0,ml_alarm,3.859,99.759,99.759,3.859,99.759,3.859,99.759,3.859,99.759,3.859,99.759,3.859,99.759,3.859,16.27,61.132,100.0,3.871,6.739,6.783,100.0,61.526
10.0,0.5,3.0,ml_alarm,3.859,99.759,99.759,3.859,99.759,3.859,99.759,3.859,99.759,3.859,99.759,3.859,99.759,3.859,16.245,61.227,100.0,3.871,6.739,6.783,100.0,61.526
10.0,1.0,0.0,ml_alarm,4.481,99.783,99.783,4.481,99.783,4.481,99.783,4.481,99.783,4.481,99.783,4.481,99.783,4.481,39.35,63.894,100.0,4.498,6.739,6.783,100.0,61.713
10.0,1.0,0.2,ml_alarm,4.481,99.783,99.783,4.481,99.783,4.481,99.783,4.481,99.783,4.481,99.783,4.481,99.783,4.481,16.185,63.052,100.0,4.498,6.739,6.783,100.0,61.713
10.0,1.0,0.5,ml_alarm,4.481,99.783,99.783,4.481,99.783,4.481,99.783,4.481,99.783,4.481,99.783,4.481,99.783,4.481,15.776,62.37,100.0,4.498,6.739,6.783,100.0,61.713
10.0,1.0,1.0,rhythm_forecast,4.489,99.783,99.783,4.481,99.783,4.481,99.783,4.481,99.783,4.489,99.783,4.481,99.783,4.481,15.981,61.448,100.0,4.498,6.739,6.783,100.0,61.713
10.0,1.0,2.0,ml_alarm,4.481,99.759,99.759,4.481,99.759,4.481,99.759,4.481,99.759,4.481,99.759,4.481,99.759,4.481,16.27,61.498,100.0,4.498,6.739,6.783,100.0,61.713
10.0,1.0,3.0,ml_alarm,4.481,99.759,99.759,4.481,99.759,4.481,99.759,4.481,99.759,4.481,99.759,4.481,99.759,4.481,16.245,61.593,100.0,4.498,6.739,6.783,100.0,61.713
10.0,2.0,0.0,ml_alarm,5.725,99.783,99.783,5.725,99.783,5.725,99.783,5.725,99.783,5.725,99.783,5.725,99.783,5.725,39.35,64.625,100.0,5.752,6.739,6.783,100.0,62.087
10.0,2.0,0.2,ml_alarm,5.725,99.783,99.783,5.725,99.783,5.725,99.783,5.725,99.783,5.725,99.783,5.725,99.783,5.725,16.185,63.783,100.0,5.752,6.739,6.783,100.0,62.087
10.0,2.0,0.5,ml_alarm,5.725,99.783,99.783,5.725,99.783,5.725,99.783,5.725,99.783,5.725,99.783,5.725,99.783,5.725,15.776,63.1,100.0,5.752,6.739,6.783,100.0,62.087
10.0,2.0,1.0,rhythm_forecast,5.732,99.783,99.783,5.725,99.783,5.725,99.783,5.725,99.783,5.732,99.783,5.725,99.783,5.725,15.981,62.179,100.0,5.752,6.739,6.783,100.0,62.087
10.0,2.0,2.0,ml_alarm,5.724,99.759,99.759,5.724,99.759,5.724,99.759,5.724,99.759,5.724,99.759,5.724,99.759,5.724,16.27,62.229,100.0,5.752,6.739,6.783,100.0,62.087
10.0,2.0,3.0,ml_alarm,5.724,99.759,99.759,5.724,99.759,5.724,99.759,5.724,99.759,5.724,99.759,5.724,99.759,5.724,16.245,62.324,100.0,5.752,6.739,6.783,100.0,62.087
10.0,5.0,0.0,ml_alarm,9.455,99.783,99.783,9.455,99.783,9.455,99.783,9.455,99.783,9.455,99.783,9.455,99.783,9.455,39.35,66.819,100.0,9.514,6.739,6.783,100.0,63.208
10.0,5.0,0.2,ml_alarm,9.455,99.783,99.783,9.455,99.783,9.455,99.783,9.455,99.783,9.455,99.783,9.455,99.783,9.455,16.185,65.976,100.0,9.514,6.739,6.783,100.0,63.208
10.0,5.0,0.5,ml_alarm,9.455,99.783,99.783,9.455,99.783,9.455,99.783,9.455,99.783,9.455,99.783,9.455,99.783,9.455,15.776,65.293,100.0,9.514,6.739,6.783,100.0,63.208
10.0,5.0,1.0,rhythm_aligned,10.192,83.767,99.783,9.455,99.783,9.455,99.783,9.455,99.783,9.462,99.783,9.455,83.767,10.192,15.981,64.372,100.0,9.514,6.739,6.783,100.0,63.208
10.0,5.0,2.0,ml_alarm,9.454,99.759,99.759,9.454,99.759,9.454,99.759,9.454,99.759,9.454,99.759,9.454,99.759,9.454,16.27,64.423,100.0,9.514,6.739,6.783,100.0,63.208
10.0,5.0,3.0,ml_alarm,9.454,99.759,99.759,9.454,99.759,9.455,99.759,9.455,99.759,9.454,99.759,9.454,99.759,9.455,16.245,64.519,100.0,9.514,6.739,6.783,100.0,63.208
10.0,10.0,0.0,rhythm_forecast,15.042,83.237,99.783,15.672,83.369,14.959,99.783,15.672,83.237,15.042,99.783,15.672,83.598,17.192,39.35,70.475,100.0,15.784,6.739,6.783,100.0,65.076
10.0,10.0,0.2,rhythm_forecast,15.038,83.177,99.783,15.672,83.345,14.957,99.783,15.672,83.177,15.038,99.783,15.672,83.574,17.18,16.185,69.63,100.0,15.784,6.739,6.783,100.0,65.076
10.0,10.0,0.5,rhythm_forecast,15.035,83.117,99.783,15.672,83.321,14.975,99.783,15.672,83.117,15.035,99.783,15.672,83.586,17.186,15.776,68.947,100.0,15.784,6.739,6.783,100.0,65.076
10.0,10.0,1.0,rhythm_aligned,14.422,83.767,99.783,15.672,83.261,14.873,99.783,15.672,83.117,15.003,99.783,15.672,83.767,14.422,15.981,68.026,100.0,15.784,6.739,6.783,100.0,65.076
10.0,10.0,2.0,rhythm_forecast,14.978,83.165,99.759,15.671,83.381,14.971,99.759,15.671,83.165,14.978,99.759,15.671,83.574,17.155,16.27,68.079,100.0,15.784,6.739,6.783,100.0,65.076
10.0,10.0,3.0,rhythm_forecast,14.943,83.273,99.759,15.671,83.406,14.969,99.759,15.672,83.273,14.943,99.759,15.671,83.61,17.17,16.245,68.175,100.0,15.784,6.739,6.783,100.0,65.076

### reports/tables/regime_ml_vs_rhythm_ci.csv
start_s,standby_pct,latency_s,pair,metric,ml_minus_rhythm,ci_lo,ci_hi
0.0,0.0,0.0,ml_alarm-rhythm_alarm,overhead_pct,0.639,0.168,1.184
0.0,0.0,0.0,ml_alarm-rhythm_alarm,cut_pct,13.827,-7.569,41.717
0.0,0.0,0.0,ml_aligned-rhythm_aligned,overhead_pct,-0.059,-0.297,0.142
0.0,0.0,0.0,ml_aligned-rhythm_aligned,cut_pct,-2.864,-12.857,4.313
0.0,0.0,0.2,ml_alarm-rhythm_alarm,overhead_pct,0.644,0.171,1.212
0.0,0.0,0.2,ml_alarm-rhythm_alarm,cut_pct,13.983,-7.471,38.781
0.0,0.0,0.2,ml_aligned-rhythm_aligned,overhead_pct,-0.002,-0.265,0.233
0.0,0.0,0.2,ml_aligned-rhythm_aligned,cut_pct,-2.19,-11.01,5.117
0.0,0.0,0.5,ml_alarm-rhythm_alarm,overhead_pct,0.653,0.204,1.264
0.0,0.0,0.5,ml_alarm-rhythm_alarm,cut_pct,13.971,-9.636,41.339
0.0,0.0,0.5,ml_aligned-rhythm_aligned,overhead_pct,-0.134,-0.353,0.034
0.0,0.0,0.5,ml_aligned-rhythm_aligned,cut_pct,-5.572,-17.143,0.693
0.0,0.0,1.0,ml_alarm-rhythm_alarm,overhead_pct,0.679,0.213,1.235
0.0,0.0,1.0,ml_alarm-rhythm_alarm,cut_pct,13.682,-7.892,39.275
0.0,0.0,1.0,ml_aligned-rhythm_aligned,overhead_pct,-0.061,-0.253,0.07
0.0,0.0,1.0,ml_aligned-rhythm_aligned,cut_pct,-0.698,-6.551,3.274
0.0,0.0,2.0,ml_alarm-rhythm_alarm,overhead_pct,0.672,0.199,1.255
0.0,0.0,2.0,ml_alarm-rhythm_alarm,cut_pct,13.454,-8.585,37.45
0.0,0.0,2.0,ml_aligned-rhythm_aligned,overhead_pct,-0.093,-0.322,0.057
0.0,0.0,2.0,ml_aligned-rhythm_aligned,cut_pct,-4.549,-13.946,2.256
0.0,0.0,3.0,ml_alarm-rhythm_alarm,overhead_pct,0.655,0.2,1.239
0.0,0.0,3.0,ml_alarm-rhythm_alarm,cut_pct,13.394,-9.944,38.142
0.0,0.0,3.0,ml_aligned-rhythm_aligned,overhead_pct,-0.087,-0.263,0.073
0.0,0.0,3.0,ml_aligned-rhythm_aligned,cut_pct,-4.801,-15.462,1.691
0.0,0.5,0.0,ml_alarm-rhythm_alarm,overhead_pct,0.77,0.234,1.431
0.0,0.5,0.0,ml_alarm-rhythm_alarm,cut_pct,13.827,-8.134,38.963
0.0,0.5,0.0,ml_aligned-rhythm_aligned,overhead_pct,-0.1,-0.397,0.16
0.0,0.5,0.0,ml_aligned-rhythm_aligned,cut_pct,-2.864,-13.178,3.948
0.0,0.5,0.2,ml_alarm-rhythm_alarm,overhead_pct,0.774,0.224,1.457
0.0,0.5,0.2,ml_alarm-rhythm_alarm,cut_pct,13.983,-9.062,38.587
0.0,0.5,0.2,ml_aligned-rhythm_aligned,overhead_pct,-0.041,-0.314,0.204
0.0,0.5,0.2,ml_aligned-rhythm_aligned,cut_pct,-2.19,-11.977,5.091
0.0,0.5,0.5,ml_alarm-rhythm_alarm,overhead_pct,0.783,0.164,1.424
0.0,0.5,0.5,ml_alarm-rhythm_alarm,cut_pct,13.971,-8.335,38.217
0.0,0.5,0.5,ml_aligned-rhythm_aligned,overhead_pct,-0.192,-0.434,-0.015
0.0,0.5,0.5,ml_aligned-rhythm_aligned,cut_pct,-5.572,-15.383,0.836
0.0,0.5,1.0,ml_alarm-rhythm_alarm,overhead_pct,0.806,0.245,1.547
0.0,0.5,1.0,ml_alarm-rhythm_alarm,cut_pct,13.682,-8.408,38.414
0.0,0.5,1.0,ml_aligned-rhythm_aligned,overhead_pct,-0.107,-0.315,0.032
0.0,0.5,1.0,ml_aligned-rhythm_aligned,cut_pct,-0.698,-6.116,3.41
0.0,0.5,2.0,ml_alarm-rhythm_alarm,overhead_pct,0.802,0.237,1.474
0.0,0.5,2.0,ml_alarm-rhythm_alarm,cut_pct,13.454,-9.173,40.405
0.0,0.5,2.0,ml_aligned-rhythm_aligned,overhead_pct,-0.159,-0.373,0.01
0.0,0.5,2.0,ml_aligned-rhythm_aligned,cut_pct,-4.549,-14.871,2.149
0.0,0.5,3.0,ml_alarm-rhythm_alarm,overhead_pct,0.785,0.211,1.501
0.0,0.5,3.0,ml_alarm-rhythm_alarm,cut_pct,13.394,-7.228,38.055
0.0,0.5,3.0,ml_aligned-rhythm_aligned,overhead_pct,-0.15,-0.375,0.024
0.0,0.5,3.0,ml_aligned-rhythm_aligned,cut_pct,-4.801,-14.903,1.635
0.0,1.0,0.0,ml_alarm-rhythm_alarm,overhead_pct,0.9,0.243,1.723
0.0,1.0,0.0,ml_alarm-rhythm_alarm,cut_pct,13.827,-7.798,37.654
0.0,1.0,0.0,ml_aligned-rhythm_aligned,overhead_pct,-0.141,-0.457,0.138
0.0,1.0,0.0,ml_aligned-rhythm_aligned,cut_pct,-2.864,-12.58,4.077
0.0,1.0,0.2,ml_alarm-rhythm_alarm,overhead_pct,0.905,0.327,1.711
0.0,1.0,0.2,ml_alarm-rhythm_alarm,cut_pct,13.983,-7.988,38.147
0.0,1.0,0.2,ml_aligned-rhythm_aligned,overhead_pct,-0.08,-0.375,0.21
0.0,1.0,0.2,ml_aligned-rhythm_aligned,cut_pct,-2.19,-10.826,5.102
0.0,1.0,0.5,ml_alarm-rhythm_alarm,overhead_pct,0.914,0.281,1.74
0.0,1.0,0.5,ml_alarm-rhythm_alarm,cut_pct,13.971,-7.232,40.312
0.0,1.0,0.5,ml_aligned-rhythm_aligned,overhead_pct,-0.25,-0.521,-0.042
0.0,1.0,0.5,ml_aligned-rhythm_aligned,cut_pct,-5.572,-15.308,0.857
0.0,1.0,1.0,ml_alarm-rhythm_alarm,overhead_pct,0.933,0.235,1.757
0.0,1.0,1.0,ml_alarm-rhythm_alarm,cut_pct,13.682,-8.022,36.81
0.0,1.0,1.0,ml_aligned-rhythm_aligned,overhead_pct,-0.153,-0.383,-0.009
0.0,1.0,1.0,ml_aligned-rhythm_aligned,cut_pct,-0.698,-5.789,3.225
0.0,1.0,2.0,ml_alarm-rhythm_alarm,overhead_pct,0.932,0.278,1.761
0.0,1.0,2.0,ml_alarm-rhythm_alarm,cut_pct,13.454,-9.246,37.947
0.0,1.0,2.0,ml_aligned-rhythm_aligned,overhead_pct,-0.224,-0.473,-0.041
0.0,1.0,2.0,ml_aligned-rhythm_aligned,cut_pct,-4.549,-14.459,2.292
0.0,1.0,3.0,ml_alarm-rhythm_alarm,overhead_pct,0.915,0.228,1.685
0.0,1.0,3.0,ml_alarm-rhythm_alarm,cut_pct,13.394,-10.125,41.23
0.0,1.0,3.0,ml_aligned-rhythm_aligned,overhead_pct,-0.213,-0.476,-0.025
0.0,1.0,3.0,ml_aligned-rhythm_aligned,cut_pct,-4.801,-14.187,1.729
0.0,2.0,0.0,ml_alarm-rhythm_alarm,overhead_pct,1.161,0.235,2.18
0.0,2.0,0.0,ml_alarm-rhythm_alarm,cut_pct,13.827,-6.821,38.254
0.0,2.0,0.0,ml_aligned-rhythm_aligned,overhead_pct,-0.223,-0.596,0.131
0.0,2.0,0.0,ml_aligned-rhythm_aligned,cut_pct,-2.864,-12.691,4.28
0.0,2.0,0.2,ml_alarm-rhythm_alarm,overhead_pct,1.166,0.315,2.158
0.0,2.0,0.2,ml_alarm-rhythm_alarm,cut_pct,13.983,-8.546,39.494
0.0,2.0,0.2,ml_aligned-rhythm_aligned,overhead_pct,-0.157,-0.496,0.208
0.0,2.0,0.2,ml_aligned-rhythm_aligned,cut_pct,-2.19,-12.599,5.048
0.0,2.0,0.5,ml_alarm-rhythm_alarm,overhead_pct,1.175,0.262,2.31
0.0,2.0,0.5,ml_alarm-rhythm_alarm,cut_pct,13.971,-8.344,41.319
0.0,2.0,0.5,ml_aligned-rhythm_aligned,overhead_pct,-0.365,-0.685,-0.115
0.0,2.0,0.5,ml_aligned-rhythm_aligned,cut_pct,-5.572,-16.286,0.903
0.0,2.0,1.0,ml_alarm-rhythm_alarm,overhead_pct,1.186,0.366,2.216
0.0,2.0,1.0,ml_alarm-rhythm_alarm,cut_pct,13.682,-8.45,38.365
0.0,2.0,1.0,ml_aligned-rhythm_aligned,overhead_pct,-0.246,-0.498,-0.077
0.0,2.0,1.0,ml_aligned-rhythm_aligned,cut_pct,-0.698,-6.072,3.195
0.0,2.0,2.0,ml_alarm-rhythm_alarm,overhead_pct,1.192,0.34,2.217
0.0,2.0,2.0,ml_alarm-rhythm_alarm,cut_pct,13.454,-7.178,38.646
0.0,2.0,2.0,ml_aligned-rhythm_aligned,overhead_pct,-0.356,-0.664,-0.121
0.0,2.0,2.0,ml_aligned-rhythm_aligned,cut_pct,-4.549,-15.161,2.063
0.0,2.0,3.0,ml_alarm-rhythm_alarm,overhead_pct,1.175,0.354,2.281
0.0,2.0,3.0,ml_alarm-rhythm_alarm,cut_pct,13.394,-9.978,37.278
0.0,2.0,3.0,ml_aligned-rhythm_aligned,overhead_pct,-0.339,-0.638,-0.104
0.0,2.0,3.0,ml_aligned-rhythm_aligned,cut_pct,-4.801,-14.739,1.565
0.0,5.0,0.0,ml_alarm-rhythm_alarm,overhead_pct,1.945,0.358,3.84
0.0,5.0,0.0,ml_alarm-rhythm_alarm,cut_pct,13.827,-6.812,37.941
0.0,5.0,0.0,ml_aligned-rhythm_aligned,overhead_pct,-0.469,-1.026,0.042
0.0,5.0,0.0,ml_aligned-rhythm_aligned,cut_pct,-2.864,-13.235,4.348
0.0,5.0,0.2,ml_alarm-rhythm_alarm,overhead_pct,1.949,0.405,3.615
0.0,5.0,0.2,ml_alarm-rhythm_alarm,cut_pct,13.983,-7.978,38.981
0.0,5.0,0.2,ml_aligned-rhythm_aligned,overhead_pct,-0.388,-0.935,0.094
0.0,5.0,0.2,ml_aligned-rhythm_aligned,cut_pct,-2.19,-11.634,5.051
0.0,5.0,0.5,ml_alarm-rhythm_alarm,overhead_pct,1.957,0.501,3.696
0.0,5.0,0.5,ml_alarm-rhythm_alarm,cut_pct,13.971,-6.943,38.495
0.0,5.0,0.5,ml_aligned-rhythm_aligned,overhead_pct,-0.711,-1.206,-0.331
0.0,5.0,0.5,ml_aligned-rhythm_aligned,cut_pct,-5.572,-16.005,0.963
0.0,5.0,1.0,ml_alarm-rhythm_alarm,overhead_pct,1.945,0.456,3.781
0.0,5.0,1.0,ml_alarm-rhythm_alarm,cut_pct,13.682,-7.294,38.737
0.0,5.0,1.0,ml_aligned-rhythm_aligned,overhead_pct,-0.524,-0.897,-0.273
0.0,5.0,1.0,ml_aligned-rhythm_aligned,cut_pct,-0.698,-6.008,3.248
0.0,5.0,2.0,ml_alarm-rhythm_alarm,overhead_pct,1.973,0.414,3.755
0.0,5.0,2.0,ml_alarm-rhythm_alarm,cut_pct,13.454,-10.073,40.602
0.0,5.0,2.0,ml_aligned-rhythm_aligned,overhead_pct,-0.749,-1.18,-0.388
0.0,5.0,2.0,ml_aligned-rhythm_aligned,cut_pct,-4.549,-14.932,2.168
0.0,5.0,3.0,ml_alarm-rhythm_alarm,overhead_pct,1.956,0.315,3.836
0.0,5.0,3.0,ml_alarm-rhythm_alarm,cut_pct,13.394,-8.437,37.261
0.0,5.0,3.0,ml_aligned-rhythm_aligned,overhead_pct,-0.717,-1.152,-0.357
0.0,5.0,3.0,ml_aligned-rhythm_aligned,cut_pct,-4.801,-15.376,1.965
0.0,10.0,0.0,ml_alarm-rhythm_alarm,overhead_pct,3.251,0.712,6.185
0.0,10.0,0.0,ml_alarm-rhythm_alarm,cut_pct,13.827,-7.827,40.766
0.0,10.0,0.0,ml_aligned-rhythm_aligned,overhead_pct,-0.878,-1.711,-0.119
0.0,10.0,0.0,ml_aligned-rhythm_aligned,cut_pct,-2.864,-12.91,4.313
0.0,10.0,0.2,ml_alarm-rhythm_alarm,overhead_pct,3.253,0.646,6.421
0.0,10.0,0.2,ml_alarm-rhythm_alarm,cut_pct,13.983,-6.385,39.462
0.0,10.0,0.2,ml_aligned-rhythm_aligned,overhead_pct,-0.774,-1.656,0.062
0.0,10.0,0.2,ml_aligned-rhythm_aligned,cut_pct,-2.19,-12.172,4.89
0.0,10.0,0.5,ml_alarm-rhythm_alarm,overhead_pct,3.261,0.776,6.381
0.0,10.0,0.5,ml_alarm-rhythm_alarm,cut_pct,13.971,-9.019,41.061
0.0,10.0,0.5,ml_aligned-rhythm_aligned,overhead_pct,-1.288,-2.026,-0.675
0.0,10.0,0.5,ml_aligned-rhythm_aligned,cut_pct,-5.572,-16.108,0.879
0.0,10.0,1.0,ml_alarm-rhythm_alarm,overhead_pct,3.211,0.741,6.488
0.0,10.0,1.0,ml_alarm-rhythm_alarm,cut_pct,13.682,-7.974,39.126
0.0,10.0,1.0,ml_aligned-rhythm_aligned,overhead_pct,-0.987,-1.531,-0.586
0.0,10.0,1.0,ml_aligned-rhythm_aligned,cut_pct,-0.698,-6.409,3.234
0.0,10.0,2.0,ml_alarm-rhythm_alarm,overhead_pct,3.274,0.717,6.5
0.0,10.0,2.0,ml_alarm-rhythm_alarm,cut_pct,13.454,-8.585,38.914
0.0,10.0,2.0,ml_aligned-rhythm_aligned,overhead_pct,-1.405,-2.085,-0.831
0.0,10.0,2.0,ml_aligned-rhythm_aligned,cut_pct,-4.549,-15.007,1.848
0.0,10.0,3.0,ml_alarm-rhythm_alarm,overhead_pct,3.256,0.512,6.644
0.0,10.0,3.0,ml_alarm-rhythm_alarm,cut_pct,13.394,-10.218,39.568
0.0,10.0,3.0,ml_aligned-rhythm_aligned,overhead_pct,-1.347,-2.027,-0.769
0.0,10.0,3.0,ml_aligned-rhythm_aligned,cut_pct,-4.801,-14.339,1.674
2.0,0.0,0.0,ml_alarm-rhythm_alarm,overhead_pct,0.0,0.0,0.0
2.0,0.0,0.0,ml_alarm-rhythm_alarm,cut_pct,0.0,0.0,0.0
2.0,0.0,0.0,ml_aligned-rhythm_aligned,overhead_pct,0.0,0.0,0.0
2.0,0.0,0.0,ml_aligned-rhythm_aligned,cut_pct,0.0,0.0,0.0
2.0,0.0,0.2,ml_alarm-rhythm_alarm,overhead_pct,0.0,0.0,0.0
2.0,0.0,0.2,ml_alarm-rhythm_alarm,cut_pct,0.0,0.0,0.0
2.0,0.0,0.2,ml_aligned-rhythm_aligned,overhead_pct,0.0,0.0,0.0
2.0,0.0,0.2,ml_aligned-rhythm_aligned,cut_pct,0.0,0.0,0.0
2.0,0.0,0.5,ml_alarm-rhythm_alarm,overhead_pct,0.0,0.0,0.0
2.0,0.0,0.5,ml_alarm-rhythm_alarm,cut_pct,0.0,0.0,0.0
2.0,0.0,0.5,ml_aligned-rhythm_aligned,overhead_pct,0.0,0.0,0.0
2.0,0.0,0.5,ml_aligned-rhythm_aligned,cut_pct,0.0,0.0,0.0
2.0,0.0,1.0,ml_alarm-rhythm_alarm,overhead_pct,0.0,0.0,0.0
2.0,0.0,1.0,ml_alarm-rhythm_alarm,cut_pct,0.0,0.0,0.0
2.0,0.0,1.0,ml_aligned-rhythm_aligned,overhead_pct,-0.123,-0.439,0.443
2.0,0.0,1.0,ml_aligned-rhythm_aligned,cut_pct,16.017,6.114,30.162
2.0,0.0,2.0,ml_alarm-rhythm_alarm,overhead_pct,0.0,0.0,0.0
2.0,0.0,2.0,ml_alarm-rhythm_alarm,cut_pct,0.0,0.0,0.0
2.0,0.0,2.0,ml_aligned-rhythm_aligned,overhead_pct,0.0,0.0,0.0
2.0,0.0,2.0,ml_aligned-rhythm_aligned,cut_pct,0.0,0.0,0.0
2.0,0.0,3.0,ml_alarm-rhythm_alarm,overhead_pct,0.0,0.0,0.0
2.0,0.0,3.0,ml_alarm-rhythm_alarm,cut_pct,0.0,0.0,0.0
2.0,0.0,3.0,ml_aligned-rhythm_aligned,overhead_pct,0.0,0.0,0.0
2.0,0.0,3.0,ml_aligned-rhythm_aligned,cut_pct,0.0,0.0,0.0
2.0,0.5,0.0,ml_alarm-rhythm_alarm,overhead_pct,-0.025,-0.369,0.681
2.0,0.5,0.0,ml_alarm-rhythm_alarm,cut_pct,16.414,6.163,32.161
2.0,0.5,0.0,ml_aligned-rhythm_aligned,overhead_pct,-0.485,-1.035,0.368
2.0,0.5,0.0,ml_aligned-rhythm_aligned,cut_pct,16.185,5.79,31.578
2.0,0.5,0.2,ml_alarm-rhythm_alarm,overhead_pct,-0.025,-0.355,0.636
2.0,0.5,0.2,ml_alarm-rhythm_alarm,cut_pct,16.438,6.163,32.484
2.0,0.5,0.2,ml_aligned-rhythm_aligned,overhead_pct,-0.481,-1.029,0.37
2.0,0.5,0.2,ml_aligned-rhythm_aligned,cut_pct,16.209,5.961,32.278
2.0,0.5,0.5,ml_alarm-rhythm_alarm,overhead_pct,-0.028,-0.36,0.645
2.0,0.5,0.5,ml_alarm-rhythm_alarm,cut_pct,16.462,5.867,31.053
2.0,0.5,0.5,ml_aligned-rhythm_aligned,overhead_pct,-0.482,-0.996,0.411
2.0,0.5,0.5,ml_aligned-rhythm_aligned,cut_pct,16.197,5.865,30.344
2.0,0.5,1.0,ml_alarm-rhythm_alarm,overhead_pct,-0.005,-0.33,0.712
2.0,0.5,1.0,ml_alarm-rhythm_alarm,cut_pct,16.522,6.356,32.707
2.0,0.5,1.0,ml_aligned-rhythm_aligned,overhead_pct,0.076,-0.294,0.78
2.0,0.5,1.0,ml_aligned-rhythm_aligned,cut_pct,16.017,6.088,31.095
2.0,0.5,2.0,ml_alarm-rhythm_alarm,overhead_pct,-0.029,-0.367,0.588
2.0,0.5,2.0,ml_alarm-rhythm_alarm,cut_pct,16.378,6.978,31.219
2.0,0.5,2.0,ml_aligned-rhythm_aligned,overhead_pct,-0.474,-1.057,0.37
2.0,0.5,2.0,ml_aligned-rhythm_aligned,cut_pct,16.185,5.851,31.877
2.0,0.5,3.0,ml_alarm-rhythm_alarm,overhead_pct,-0.03,-0.373,0.647
2.0,0.5,3.0,ml_alarm-rhythm_alarm,cut_pct,16.354,6.015,31.033
2.0,0.5,3.0,ml_aligned-rhythm_aligned,overhead_pct,-0.476,-0.992,0.526
2.0,0.5,3.0,ml_aligned-rhythm_aligned,cut_pct,16.149,6.711,30.677
2.0,1.0,0.0,ml_alarm-rhythm_alarm,overhead_pct,0.174,-0.229,0.992
2.0,1.0,0.0,ml_alarm-rhythm_alarm,cut_pct,16.414,5.618,31.325
2.0,1.0,0.0,ml_aligned-rhythm_aligned,overhead_pct,-0.284,-0.885,0.63
2.0,1.0,0.0,ml_aligned-rhythm_aligned,cut_pct,16.185,6.13,30.881
2.0,1.0,0.2,ml_alarm-rhythm_alarm,overhead_pct,0.174,-0.234,0.964
2.0,1.0,0.2,ml_alarm-rhythm_alarm,cut_pct,16.438,6.099,31.905
2.0,1.0,0.2,ml_aligned-rhythm_aligned,overhead_pct,-0.281,-0.887,0.649
2.0,1.0,0.2,ml_aligned-rhythm_aligned,cut_pct,16.209,6.135,30.777
2.0,1.0,0.5,ml_alarm-rhythm_alarm,overhead_pct,0.172,-0.238,0.971
2.0,1.0,0.5,ml_alarm-rhythm_alarm,cut_pct,16.462,6.238,31.473
2.0,1.0,0.5,ml_aligned-rhythm_aligned,overhead_pct,-0.281,-0.877,0.687
2.0,1.0,0.5,ml_aligned-rhythm_aligned,cut_pct,16.197,5.642,31.138
2.0,1.0,1.0,ml_alarm-rhythm_alarm,overhead_pct,0.197,-0.198,1.008
2.0,1.0,1.0,ml_alarm-rhythm_alarm,cut_pct,16.522,6.554,32.232
2.0,1.0,1.0,ml_aligned-rhythm_aligned,overhead_pct,0.275,-0.148,1.028
2.0,1.0,1.0,ml_aligned-rhythm_aligned,cut_pct,16.017,5.572,29.11
2.0,1.0,2.0,ml_alarm-rhythm_alarm,overhead_pct,0.171,-0.254,0.98
2.0,1.0,2.0,ml_alarm-rhythm_alarm,cut_pct,16.378,6.062,30.506
2.0,1.0,2.0,ml_aligned-rhythm_aligned,overhead_pct,-0.274,-0.875,0.784
2.0,1.0,2.0,ml_aligned-rhythm_aligned,cut_pct,16.185,6.6,30.945
2.0,1.0,3.0,ml_alarm-rhythm_alarm,overhead_pct,0.17,-0.242,1.005
2.0,1.0,3.0,ml_alarm-rhythm_alarm,cut_pct,16.354,5.953,30.781
2.0,1.0,3.0,ml_aligned-rhythm_aligned,overhead_pct,-0.275,-0.887,0.656
2.0,1.0,3.0,ml_aligned-rhythm_aligned,cut_pct,16.149,5.854,31.146
2.0,2.0,0.0,ml_alarm-rhythm_alarm,overhead_pct,0.573,0.007,1.648
2.0,2.0,0.0,ml_alarm-rhythm_alarm,cut_pct,16.414,5.742,31.037
2.0,2.0,0.0,ml_aligned-rhythm_aligned,overhead_pct,3.12,-0.069,5.392

### reports/tables/regime_pareto_test.csv
strategy,latency_s,thr,violations,raw_violations,overhead_J,base_J,armed_s,hours,episodes,cut_pct,overhead_pct,armed_pct,episodes_per_h
always_burn,,,7750.0,8310,24589687.5628,362538781.2864,0.0,45.1002,0.0,6.7389,6.7826,0.0,0.0
always_on,,,0.0,8310,10641835.2878,362538781.2864,162360.6,45.1002,40.0,100.0,2.9354,100.0,0.8869
ml_alarm,0.0,0.0,18.0,8310,10618710.475,362538781.2864,160995.6,45.1002,40.0,99.7834,2.929,99.1593,0.8869
ml_alarm,0.0,0.0002,18.0,8310,10618710.475,362538781.2864,160541.2,45.1002,79.0,99.7834,2.929,98.8794,1.7517
ml_alarm,0.0,0.0004,18.0,8310,10618710.475,362538781.2864,157996.2,45.1002,353.0,99.7834,2.929,97.3119,7.827
ml_alarm,0.0,0.0013,18.0,8310,10618531.9038,362538781.2864,154116.6,45.1002,443.0,99.7834,2.9289,94.9224,9.8226
ml_alarm,0.0,0.0029,26.0,8310,10610781.889,362538781.2864,150764.8,45.1002,661.0,99.6871,2.9268,92.858,14.6563
ml_alarm,0.0,0.0053,101.0,8310,10547769.1168,362538781.2864,140929.4,45.1002,1908.0,98.7846,2.9094,86.8002,42.3058
ml_alarm,0.0,0.0072,217.0,8310,10484379.5526,362538781.2864,132295.0,45.1002,2641.0,97.3887,2.8919,81.4822,58.5585
ml_alarm,0.0,0.0138,507.0,8310,10315657.2898,362538781.2864,115177.8,45.1002,3610.0,93.8989,2.8454,70.9395,80.0441
ml_alarm,0.0,0.0249,842.0,8310,10136813.9163,362538781.2864,103094.8,45.1002,4056.0,89.8676,2.7961,63.4974,89.9331
ml_alarm,0.0,0.0423,1299.0,8310,9894778.6469,362538781.2864,91403.2,45.1002,4517.0,84.3682,2.7293,56.2964,100.1548
ml_alarm,0.0,0.066,1881.0,8310,9585118.8866,362538781.2864,79924.2,45.1002,4684.0,77.3646,2.6439,49.2264,103.8577
ml_alarm,0.0,0.0998,2515.0,8310,9220336.188,362538781.2864,69694.6,45.1002,4644.0,69.7353,2.5433,42.9258,102.9708
ml_alarm,0.0,0.1467,3065.0,8310,8902800.0488,362538781.2864,61371.8,45.1002,4519.0,63.1167,2.4557,37.7997,100.1992
ml_alarm,0.0,0.208,3508.0,8310,8614766.2716,362538781.2864,55037.6,45.1002,4377.0,57.7858,2.3762,33.8984,97.0506
ml_alarm,0.0,0.2899,3870.0,8310,8319163.9401,362538781.2864,49807.2,45.1002,4199.0,53.4296,2.2947,30.6769,93.1039
ml_alarm,0.0,0.3993,4174.0,8310,8055206.7334,362538781.2864,45261.8,45.1002,3987.0,49.7714,2.2219,27.8773,88.4032
ml_alarm,0.0,0.5499,4433.0,8310,7711013.6324,362538781.2864,41471.4,45.1002,3776.0,46.6546,2.1269,25.5428,83.7247
ml_alarm,0.0,0.7352,4650.0,8310,7308675.9445,362538781.2864,38615.6,45.1002,3565.0,44.0433,2.016,23.7838,79.0463
ml_alarm,0.0,0.901,4941.0,8310,6518356.8923,362538781.2864,35602.8,45.1002,3319.0,40.5415,1.798,21.9282,73.5917
ml_alarm,0.0,0.9886,5173.0,8310,5909844.1415,362538781.2864,32703.0,45.1002,3110.0,37.7497,1.6301,20.1422,68.9576
ml_alarm,0.0,0.9972,5202.0,8310,5830958.2155,362538781.2864,31691.2,45.1002,3084.0,37.4007,1.6084,19.519,68.3811
ml_alarm,0.0,0.9988,5291.0,8310,5605192.5275,362538781.2864,29651.4,45.1002,2997.0,36.3297,1.5461,18.2627,66.4521
ml_alarm,0.0,0.9991,5315.0,8310,5542576.7501,362538781.2864,28753.6,45.1002,2974.0,36.0409,1.5288,17.7097,65.9421
ml_alarm,0.0,0.9992,5328.0,8310,5508115.8331,362538781.2864,28215.6,45.1002,2962.0,35.8845,1.5193,17.3784,65.676
ml_alarm,0.0,0.9993,5353.0,8310,5431983.5703,362538781.2864,27654.6,45.1002,2937.0,35.5836,1.4983,17.0328,65.1217
ml_alarm,0.0,0.9994,5382.0,8310,5363140.3773,362538781.2864,27062.8,45.1002,2908.0,35.2347,1.4793,16.6683,64.4787
ml_alarm,0.0,0.9995,5412.0,8310,5306110.7135,362538781.2864,26473.2,45.1002,2878.0,34.8736,1.4636,16.3052,63.8135
ml_alarm,0.0,0.9996,5433.0,8310,5266699.3293,362538781.2864,25878.0,45.1002,2857.0,34.6209,1.4527,15.9386,63.3479
ml_alarm,0.0,0.9997,5460.0,8310,5218492.1243,362538781.2864,25236.0,45.1002,2831.0,34.296,1.4394,15.5432,62.7714
ml_alarm,0.0,0.9997,5488.0,8310,5166422.9327,362538781.2864,24397.8,45.1002,2805.0,33.9591,1.4251,15.0269,62.1949
ml_alarm,0.0,0.9997,5508.0,8310,5123440.2259,362538781.2864,23552.0,45.1002,2785.0,33.7184,1.4132,14.506,61.7514
ml_alarm,0.0,0.9998,5531.0,8310,5080330.2883,362538781.2864,22624.0,45.1002,2762.0,33.4416,1.4013,13.9344,61.2415
ml_alarm,0.0,0.9998,5559.0,8310,5028814.6083,362538781.2864,21615.0,45.1002,2734.0,33.1047,1.3871,13.313,60.6206
ml_alarm,0.0,0.9998,5615.0,8310,4919812.5843,362538781.2864,20475.8,45.1002,2681.0,32.4308,1.357,12.6113,59.4455
ml_alarm,0.0,0.9998,5690.0,8310,4774271.5177,362538781.2864,19294.2,45.1002,2608.0,31.5283,1.3169,11.8835,57.8268
ml_alarm,0.0,0.9998,5793.0,8310,4590883.3136,362538781.2864,18120.6,45.1002,2507.0,30.2888,1.2663,11.1607,55.5874
ml_alarm,0.2,0.0,18.0,8310,10618710.475,362538781.2864,160994.8,45.1002,40.0,99.7834,2.929,99.1588,0.8869
ml_alarm,0.2,0.0002,18.0,8310,10618710.475,362538781.2864,160540.4,45.1002,79.0,99.7834,2.929,98.8789,1.7517
ml_alarm,0.2,0.0004,18.0,8310,10618710.475,362538781.2864,157995.4,45.1002,353.0,99.7834,2.929,97.3114,7.827
ml_alarm,0.2,0.0013,18.0,8310,10618536.0292,362538781.2864,154114.0,45.1002,443.0,99.7834,2.9289,94.9208,9.8226
ml_alarm,0.2,0.0029,26.0,8310,10607729.1766,362538781.2864,150752.6,45.1002,661.0,99.6871,2.926,92.8505,14.6563
ml_alarm,0.2,0.0053,106.0,8310,10545762.5687,362538781.2864,140903.2,45.1002,1908.0,98.7244,2.9089,86.7841,42.3058
ml_alarm,0.2,0.0072,220.0,8310,10482757.5845,362538781.2864,132263.8,45.1002,2640.0,97.3526,2.8915,81.463,58.5364
ml_alarm,0.2,0.0138,511.0,8310,10310893.0883,362538781.2864,115141.8,45.1002,3609.0,93.8508,2.8441,70.9173,80.0219
ml_alarm,0.2,0.0249,845.0,8310,10131924.6625,362538781.2864,103053.4,45.1002,4055.0,89.8315,2.7947,63.4719,89.911
ml_alarm,0.2,0.0423,1305.0,8310,9886609.4971,362538781.2864,91354.2,45.1002,4517.0,84.296,2.727,56.2662,100.1548
ml_alarm,0.2,0.066,1885.0,8310,9569837.9441,362538781.2864,79868.0,45.1002,4684.0,77.3165,2.6397,49.1917,103.8577
ml_alarm,0.2,0.0998,2533.0,8310,9212033.9271,362538781.2864,69643.0,45.1002,4645.0,69.5187,2.541,42.894,102.993
ml_alarm,0.2,0.1467,3088.0,8310,8888239.5007,362538781.2864,61323.8,45.1002,4519.0,62.84,2.4517,37.7701,100.1992
ml_alarm,0.2,0.208,3532.0,8310,8605254.3276,362538781.2864,55006.2,45.1002,4374.0,57.497,2.3736,33.879,96.9841
ml_alarm,0.2,0.2899,3895.0,8310,8308372.7775,362538781.2864,49771.6,45.1002,4198.0,53.1288,2.2917,30.655,93.0817
ml_alarm,0.2,0.3993,4199.0,8310,8048243.0108,362538781.2864,45227.4,45.1002,3987.0,49.4705,2.22,27.8561,88.4032
ml_alarm,0.2,0.5499,4449.0,8310,7705996.2957,362538781.2864,41434.8,45.1002,3776.0,46.4621,2.1256,25.5202,83.7247
ml_alarm,0.2,0.7352,4663.0,8310,7304789.0817,362538781.2864,38581.8,45.1002,3565.0,43.8869,2.0149,23.763,79.0463
ml_alarm,0.2,0.901,4941.0,8310,6537633.5887,362538781.2864,35598.8,45.1002,3319.0,40.5415,1.8033,21.9258,73.5917
ml_alarm,0.2,0.9886,5172.0,8310,5934819.1151,362538781.2864,32720.4,45.1002,3110.0,37.7617,1.637,20.1529,68.9576
ml_alarm,0.2,0.9972,5200.0,8310,5844249.3569,362538781.2864,31697.0,45.1002,3084.0,37.4248,1.612,19.5226,68.3811
ml_alarm,0.2,0.9988,5290.0,8310,5610784.0897,362538781.2864,29651.0,45.1002,2997.0,36.3418,1.5476,18.2624,66.4521
ml_alarm,0.2,0.9991,5315.0,8310,5542697.9453,362538781.2864,28750.2,45.1002,2974.0,36.0409,1.5289,17.7076,65.9421
ml_alarm,0.2,0.9992,5328.0,8310,5508243.8739,362538781.2864,28212.8,45.1002,2962.0,35.8845,1.5194,17.3766,65.676
ml_alarm,0.2,0.9993,5353.0,8310,5432022.8263,362538781.2864,27652.2,45.1002,2937.0,35.5836,1.4983,17.0313,65.1217
ml_alarm,0.2,0.9994,5382.0,8310,5363179.6333,362538781.2864,27061.0,45.1002,2908.0,35.2347,1.4793,16.6672,64.4787
ml_alarm,0.2,0.9995,5412.0,8310,5306149.9695,362538781.2864,26471.6,45.1002,2878.0,34.8736,1.4636,16.3042,63.8135
ml_alarm,0.2,0.9996,5433.0,8310,5266738.5853,362538781.2864,25876.4,45.1002,2857.0,34.6209,1.4527,15.9376,63.3479
ml_alarm,0.2,0.9997,5460.0,8310,5218542.7035,362538781.2864,25234.6,45.1002,2831.0,34.296,1.4394,15.5423,62.7714
ml_alarm,0.2,0.9997,5488.0,8310,5166429.7783,362538781.2864,24396.0,45.1002,2805.0,33.9591,1.4251,15.0258,62.1949
ml_alarm,0.2,0.9997,5508.0,8310,5123485.5791,362538781.2864,23550.2,45.1002,2785.0,33.7184,1.4132,14.5049,61.7514
ml_alarm,0.2,0.9998,5531.0,8310,5080368.7959,362538781.2864,22622.2,45.1002,2762.0,33.4416,1.4013,13.9333,61.2415
ml_alarm,0.2,0.9998,5559.0,8310,5028853.1159,362538781.2864,21613.2,45.1002,2734.0,33.1047,1.3871,13.3119,60.6206
ml_alarm,0.2,0.9998,5612.0,8310,4931999.7399,362538781.2864,20487.2,45.1002,2681.0,32.4669,1.3604,12.6183,59.4455
ml_alarm,0.2,0.9998,5686.0,8310,4797301.1413,362538781.2864,19316.6,45.1002,2608.0,31.5764,1.3233,11.8973,57.8268
ml_alarm,0.2,0.9998,5790.0,8310,4609014.8746,362538781.2864,18139.0,45.1002,2507.0,30.3249,1.2713,11.172,55.5874
ml_alarm,0.5,0.0,18.0,8310,10618710.475,362538781.2864,160994.0,45.1002,40.0,99.7834,2.929,99.1583,0.8869
ml_alarm,0.5,0.0002,18.0,8310,10618710.475,362538781.2864,160539.6,45.1002,79.0,99.7834,2.929,98.8784,1.7517
ml_alarm,0.5,0.0004,18.0,8310,10618710.475,362538781.2864,157994.6,45.1002,353.0,99.7834,2.929,97.3109,7.827
ml_alarm,0.5,0.0013,18.0,8310,10618533.0962,362538781.2864,154112.2,45.1002,443.0,99.7834,2.9289,94.9197,9.8226
ml_alarm,0.5,0.0029,26.0,8310,10606475.8444,362538781.2864,150744.6,45.1002,664.0,99.6871,2.9256,92.8456,14.7228
ml_alarm,0.5,0.0053,112.0,8310,10543896.4084,362538781.2864,140880.8,45.1002,1909.0,98.6522,2.9083,86.7703,42.328
ml_alarm,0.5,0.0072,228.0,8310,10480944.6865,362538781.2864,132236.4,45.1002,2640.0,97.2563,2.891,81.4461,58.5364
ml_alarm,0.5,0.0138,524.0,8310,10313114.3913,362538781.2864,115115.6,45.1002,3609.0,93.6943,2.8447,70.9012,80.0219
ml_alarm,0.5,0.0249,851.0,8310,10129317.701,362538781.2864,103014.8,45.1002,4053.0,89.7593,2.794,63.4482,89.8666
ml_alarm,0.5,0.0423,1316.0,8310,9882186.4457,362538781.2864,91312.6,45.1002,4515.0,84.1637,2.7258,56.2406,100.1105
ml_alarm,0.5,0.066,1897.0,8310,9557732.3271,362538781.2864,79823.6,45.1002,4682.0,77.1721,2.6363,49.1644,103.8134
ml_alarm,0.5,0.0998,2547.0,8310,9205033.6023,362538781.2864,69599.8,45.1002,4644.0,69.3502,2.539,42.8674,102.9708
ml_alarm,0.5,0.1467,3100.0,8310,8878886.1129,362538781.2864,61286.6,45.1002,4517.0,62.6955,2.4491,37.7472,100.1548
ml_alarm,0.5,0.208,3543.0,8310,8586510.8072,362538781.2864,54971.2,45.1002,4375.0,57.3646,2.3684,33.8575,97.0063
ml_alarm,0.5,0.2899,3908.0,8310,8292504.2058,362538781.2864,49738.4,45.1002,4200.0,52.9723,2.2873,30.6345,93.126
ml_alarm,0.5,0.3993,4210.0,8310,8034534.2907,362538781.2864,45196.6,45.1002,3987.0,49.3381,2.2162,27.8372,88.4032
ml_alarm,0.5,0.5499,4455.0,8310,7698473.3305,362538781.2864,41410.6,45.1002,3776.0,46.3899,2.1235,25.5053,83.7247
ml_alarm,0.5,0.7352,4672.0,8310,7295126.576,362538781.2864,38549.0,45.1002,3565.0,43.7786,2.0122,23.7428,79.0463
ml_alarm,0.5,0.901,4941.0,8310,6549202.466,362538781.2864,35589.6,45.1002,3319.0,40.5415,1.8065,21.9201,73.5917
ml_alarm,0.5,0.9886,5169.0,8310,5956359.3787,362538781.2864,32735.4,45.1002,3110.0,37.7978,1.643,20.1622,68.9576
ml_alarm,0.5,0.9972,5197.0,8310,5872495.9697,362538781.2864,31717.6,45.1002,3084.0,37.4609,1.6198,19.5353,68.3811
ml_alarm,0.5,0.9988,5288.0,8310,5630935.4929,362538781.2864,29666.6,45.1002,2997.0,36.3658,1.5532,18.272,66.4521
ml_alarm,0.5,0.9991,5312.0,8310,5561717.1833,362538781.2864,28763.0,45.1002,2974.0,36.077,1.5341,17.7155,65.9421
ml_alarm,0.5,0.9992,5325.0,8310,5527243.1183,362538781.2864,28225.6,45.1002,2962.0,35.9206,1.5246,17.3845,65.676
ml_alarm,0.5,0.9993,5353.0,8310,5437279.2081,362538781.2864,27653.6,45.1002,2937.0,35.5836,1.4998,17.0322,65.1217
ml_alarm,0.5,0.9994,5382.0,8310,5368434.0265,362538781.2864,27063.0,45.1002,2908.0,35.2347,1.4808,16.6685,64.4787
ml_alarm,0.5,0.9995,5412.0,8310,5311386.4133,362538781.2864,26473.8,45.1002,2878.0,34.8736,1.4651,16.3056,63.8135
ml_alarm,0.5,0.9996,5434.0,8310,5266424.7139,362538781.2864,25874.0,45.1002,2857.0,34.6089,1.4527,15.9361,63.3479
ml_alarm,0.5,0.9997,5461.0,8310,5217888.4451,362538781.2864,25232.0,45.1002,2831.0,34.284,1.4393,15.5407,62.7714
ml_alarm,0.5,0.9997,5488.0,8310,5170540.6827,362538781.2864,24398.0,45.1002,2805.0,33.9591,1.4262,15.027,62.1949
ml_alarm,0.5,0.9997,5509.0,8310,5123173.1417,362538781.2864,23548.2,45.1002,2785.0,33.7064,1.4131,14.5036,61.7514
ml_alarm,0.5,0.9998,5532.0,8310,5080063.2041,362538781.2864,22620.8,45.1002,2762.0,33.4296,1.4012,13.9324,61.2415
ml_alarm,0.5,0.9998,5561.0,8310,5028295.0827,362538781.2864,21611.2,45.1002,2734.0,33.0806,1.387,13.3106,60.6206
ml_alarm,0.5,0.9998,5614.0,8310,4931441.7067,362538781.2864,20484.6,45.1002,2681.0,32.4428,1.3603,12.6167,59.4455
ml_alarm,0.5,0.9998,5688.0,8310,4796743.1081,362538781.2864,19314.2,45.1002,2608.0,31.5523,1.3231,11.8959,57.8268
ml_alarm,0.5,0.9998,5789.0,8310,4614093.9525,362538781.2864,18142.0,45.1002,2507.0,30.3369,1.2727,11.1739,55.5874
ml_alarm,1.0,0.0,18.0,8310,10618710.475,362538781.2864,160991.6,45.1002,40.0,99.7834,2.929,99.1568,0.8869
ml_alarm,1.0,0.0001,18.0,8310,10618710.475,362538781.2864,160987.6,45.1002,41.0,99.7834,2.929,99.1544,0.9091
ml_alarm,1.0,0.0001,18.0,8310,10618710.475,362538781.2864,160973.6,45.1002,43.0,99.7834,2.929,99.1457,0.9534
ml_alarm,1.0,0.0001,18.0,8310,10618710.475,362538781.2864,160931.4,45.1002,48.0,99.7834,2.929,99.1197,1.0643
ml_alarm,1.0,0.0001,18.0,8310,10618710.475,362538781.2864,160885.4,45.1002,53.0,99.7834,2.929,99.0914,1.1752
ml_alarm,1.0,0.0001,18.0,8310,10618710.475,362538781.2864,160847.4,45.1002,60.0,99.7834,2.929,99.068,1.3304
ml_alarm,1.0,0.0001,18.0,8310,10618710.475,362538781.2864,160777.4,45.1002,68.0,99.7834,2.929,99.0249,1.5078
ml_alarm,1.0,0.0001,18.0,8310,10618710.475,362538781.2864,160724.6,45.1002,74.0,99.7834,2.929,98.9924,1.6408
ml_alarm,1.0,0.0001,18.0,8310,10618710.475,362538781.2864,160628.4,45.1002,70.0,99.7834,2.929,98.9331,1.5521
ml_alarm,1.0,0.0001,18.0,8310,10618710.475,362538781.2864,160583.4,45.1002,71.0,99.7834,2.929,98.9054,1.5743
ml_alarm,1.0,0.0002,18.0,8310,10618710.475,362538781.2864,160537.2,45.1002,79.0,99.7834,2.929,98.8769,1.7517
ml_alarm,1.0,0.0002,18.0,8310,10618710.475,362538781.2864,160494.8,45.1002,87.0,99.7834,2.929,98.8508,1.929
ml_alarm,1.0,0.0002,18.0,8310,10618710.475,362538781.2864,160424.6,45.1002,93.0,99.7834,2.929,98.8076,2.0621
ml_alarm,1.0,0.0002,18.0,8310,10618710.475,362538781.2864,160372.0,45.1002,106.0,99.7834,2.929,98.7752,2.3503
ml_alarm,1.0,0.0002,18.0,8310,10618710.475,362538781.2864,160294.2,45.1002,122.0,99.7834,2.929,98.7273,2.7051
ml_alarm,1.0,0.0002,18.0,8310,10618710.475,362538781.2864,160224.8,45.1002,135.0,99.7834,2.929,98.6845,2.9933
ml_alarm,1.0,0.0002,18.0,8310,10618710.475,362538781.2864,160136.8,45.1002,148.0,99.7834,2.929,98.6303,3.2816
ml_alarm,1.0,0.0002,18.0,8310,10618710.475,362538781.2864,160041.0,45.1002,165.0,99.7834,2.929,98.5713,3.6585
ml_alarm,1.0,0.0002,18.0,8310,10618710.475,362538781.2864,159961.0,45.1002,181.0,99.7834,2.929,98.5221,4.0133
ml_alarm,1.0,0.0002,18.0,8310,10618710.475,362538781.2864,159851.2,45.1002,195.0,99.7834,2.929,98.4544,4.3237
ml_alarm,1.0,0.0002,18.0,8310,10618710.475,362538781.2864,159699.8,45.1002,216.0,99.7834,2.929,98.3612,4.7893
ml_alarm,1.0,0.0003,18.0,8310,10618710.475,362538781.2864,159575.2,45.1002,233.0,99.7834,2.929,98.2844,5.1663
ml_alarm,1.0,0.0003,18.0,8310,10618710.475,362538781.2864,159430.2,45.1002,247.0,99.7834,2.929,98.1951,5.4767
ml_alarm,1.0,0.0003,18.0,8310,10618710.475,362538781.2864,159276.2,45.1002,261.0,99.7834,2.929,98.1003,5.7871
ml_alarm,1.0,0.0003,18.0,8310,10618710.475,362538781.2864,159135.2,45.1002,275.0,99.7834,2.929,98.0134,6.0975
ml_alarm,1.0,0.0003,18.0,8310,10618710.475,362538781.2864,158945.6,45.1002,290.0,99.7834,2.929,97.8967,6.4301
ml_alarm,1.0,0.0003,18.0,8310,10618710.475,362538781.2864,158800.2,45.1002,300.0,99.7834,2.929,97.8071,6.6519
ml_alarm,1.0,0.0003,18.0,8310,10618710.475,362538781.2864,158628.4,45.1002,323.0,99.7834,2.929,97.7013,7.1618
ml_alarm,1.0,0.0004,18.0,8310,10618710.475,362538781.2864,158408.0,45.1002,331.0,99.7834,2.929,97.5655,7.3392
ml_alarm,1.0,0.0004,18.0,8310,10618710.475,362538781.2864,158182.8,45.1002,342.0,99.7834,2.929,97.4268,7.5831
ml_alarm,1.0,0.0004,18.0,8310,10618710.475,362538781.2864,157992.2,45.1002,353.0,99.7834,2.929,97.3094,7.827
ml_alarm,1.0,0.0004,18.0,8310,10618710.475,362538781.2864,157759.8,45.1002,359.0,99.7834,2.929,97.1663,7.9601
ml_alarm,1.0,0.0004,18.0,8310,10618710.475,362538781.2864,157542.2,45.1002,371.0,99.7834,2.929,97.0323,8.2261
ml_alarm,1.0,0.0005,18.0,8310,10618710.475,362538781.2864,157344.0,45.1002,385.0,99.7834,2.929,96.9102,8.5366
ml_alarm,1.0,0.0005,18.0,8310,10618710.475,362538781.2864,157127.0,45.1002,398.0,99.7834,2.929,96.7766,8.8248
ml_alarm,1.0,0.0005,18.0,8310,10618710.475,362538781.2864,156962.0,45.1002,403.0,99.7834,2.929,96.6749,8.9357
ml_alarm,1.0,0.0006,18.0,8310,10618710.475,362538781.2864,156722.6,45.1002,405.0,99.7834,2.929,96.5275,8.98
ml_alarm,1.0,0.0006,18.0,8310,10618710.475,362538781.2864,156475.4,45.1002,406.0,99.7834,2.929,96.3752,9.0022
ml_alarm,1.0,0.0006,18.0,8310,10618710.475,362538781.2864,156267.0,45.1002,412.0,99.7834,2.929,96.2469,9.1352
ml_alarm,1.0,0.0007,18.0,8310,10618710.475,362538781.2864,156068.6,45.1002,415.0,99.7834,2.929,96.1247,9.2017
ml_alarm,1.0,0.0007,18.0,8310,10618710.475,362538781.2864,155864.4,45.1002,417.0,99.7834,2.929,95.9989,9.2461
ml_alarm,1.0,0.0008,18.0,8310,10618710.475,362538781.2864,155626.4,45.1002,417.0,99.7834,2.929,95.8523,9.2461
ml_alarm,1.0,0.0008,18.0,8310,10618688.0526,362538781.2864,155432.4,45.1002,418.0,99.7834,2.929,95.7328,9.2683
ml_alarm,1.0,0.0009,18.0,8310,10618652.3438,362538781.2864,155209.8,45.1002,419.0,99.7834,2.929,95.5957,9.2904
ml_alarm,1.0,0.0009,18.0,8310,10618652.3438,362538781.2864,155030.6,45.1002,422.0,99.7834,2.929,95.4854,9.3569
ml_alarm,1.0,0.001,18.0,8310,10618639.6312,362538781.2864,154869.2,45.1002,426.0,99.7834,2.929,95.3859,9.4456
ml_alarm,1.0,0.0011,18.0,8310,10618626.813,362538781.2864,154701.2,45.1002,429.0,99.7834,2.929,95.2825,9.5122
ml_alarm,1.0,0.0011,18.0,8310,10618608.8774,362538781.2864,154547.8,45.1002,433.0,99.7834,2.929,95.188,9.6009
ml_alarm,1.0,0.0012,18.0,8310,10618603.0618,362538781.2864,154398.8,45.1002,435.0,99.7834,2.929,95.0962,9.6452
ml_alarm,1.0,0.0013,18.0,8310,10618598.5132,362538781.2864,154258.8,45.1002,440.0,99.7834,2.929,95.01,9.7561
ml_alarm,1.0,0.0013,18.0,8310,10618585.4774,362538781.2864,154104.6,45.1002,450.0,99.7834,2.929,94.915,9.9778
ml_alarm,1.0,0.0014,18.0,8310,10618580.9324,362538781.2864,153968.6,45.1002,454.0,99.7834,2.929,94.8313,10.0665
ml_alarm,1.0,0.0015,18.0,8310,10618480.229,362538781.2864,153808.4,45.1002,461.0,99.7834,2.9289,94.7326,10.2217
ml_alarm,1.0,0.0015,18.0,8310,10618411.583,362538781.2864,153649.2,45.1002,475.0,99.7834,2.9289,94.6345,10.5321
ml_alarm,1.0,0.0016,18.0,8310,10618366.4016,362538781.2864,153505.4,45.1002,479.0,99.7834,2.9289,94.546,10.6208
ml_alarm,1.0,0.0017,18.0,8310,10618266.5648,362538781.2864,153352.2,45.1002,485.0,99.7834,2.9289,94.4516,10.7538
ml_alarm,1.0,0.0018,18.0,8310,10618201.3564,362538781.2864,153184.8,45.1002,490.0,99.7834,2.9288,94.3485,10.8647
ml_alarm,1.0,0.0018,19.0,8310,10618035.302,362538781.2864,153043.2,45.1002,497.0,99.7714,2.9288,94.2613,11.0199
ml_alarm,1.0,0.0019,19.0,8310,10617870.5096,362538781.2864,152881.6,45.1002,504.0,99.7714,2.9288,94.1618,11.1751
ml_alarm,1.0,0.002,19.0,8310,10617786.4064,362538781.2864,152688.2,45.1002,512.0,99.7714,2.9287,94.0426,11.3525
ml_alarm,1.0,0.0021,19.0,8310,10617564.3138,362538781.2864,152520.8,45.1002,526.0,99.7714,2.9287,93.9395,11.6629
ml_alarm,1.0,0.0021,19.0,8310,10617501.02,362538781.2864,152378.0,45.1002,544.0,99.7714,2.9287,93.8516,12.062
ml_alarm,1.0,0.0022,20.0,8310,10617244.067,362538781.2864,152188.0,45.1002,555.0,99.7593,2.9286,93.7346,12.3059
ml_alarm,1.0,0.0023,20.0,8310,10617143.7576,362538781.2864,152025.6,45.1002,556.0,99.7593,2.9286,93.6345,12.3281
ml_alarm,1.0,0.0024,20.0,8310,10616930.8528,362538781.2864,151874.4,45.1002,563.0,99.7593,2.9285,93.5414,12.4833
ml_alarm,1.0,0.0025,21.0,8310,10616547.2624,362538781.2864,151725.2,45.1002,579.0,99.7473,2.9284,93.4495,12.8381
ml_alarm,1.0,0.0025,22.0,8310,10611571.7634,362538781.2864,151519.6,45.1002,600.0,99.7353,2.927,93.3229,13.3037
ml_alarm,1.0,0.0026,23.0,8310,10611282.2448,362538781.2864,151322.8,45.1002,613.0,99.7232,2.9269,93.2017,13.592
ml_alarm,1.0,0.0027,24.0,8310,10605973.0502,362538781.2864,151118.4,45.1002,625.0,99.7112,2.9255,93.0758,13.858
ml_alarm,1.0,0.0028,24.0,8310,10605675.8966,362538781.2864,150925.2,45.1002,647.0,99.7112,2.9254,92.9568,14.3458
ml_alarm,1.0,0.0029,27.0,8310,10604821.127,362538781.2864,150730.2,45.1002,670.0,99.6751,2.9252,92.8367,14.8558
ml_alarm,1.0,0.003,27.0,8310,10604472.9392,362538781.2864,150456.8,45.1002,697.0,99.6751,2.9251,92.6683,15.4545
ml_alarm,1.0,0.0031,27.0,8310,10603940.3966,362538781.2864,150227.2,45.1002,727.0,99.6751,2.9249,92.5269,16.1197
ml_alarm,1.0,0.0032,29.0,8310,10603095.0544,362538781.2864,149965.8,45.1002,758.0,99.651,2.9247,92.3659,16.807
ml_alarm,1.0,0.0032,30.0,8310,10602590.4676,362538781.2864,149694.8,45.1002,795.0,99.639,2.9245,92.199,17.6274
ml_alarm,1.0,0.0033,31.0,8310,10601713.9892,362538781.2864,149386.8,45.1002,856.0,99.627,2.9243,92.0093,18.98
ml_alarm,1.0,0.0034,33.0,8310,10600231.3774,362538781.2864,149096.2,45.1002,907.0,99.6029,2.9239,91.8303,20.1108
ml_alarm,1.0,0.0035,39.0,8310,10597924.8478,362538781.2864,148704.0,45.1002,955.0,99.5307,2.9233,91.5887,21.1751
ml_alarm,1.0,0.0037,42.0,8310,10591015.993,362538781.2864,148252.2,45.1002,1014.0,99.4946,2.9213,91.3105,22.4833
ml_alarm,1.0,0.0038,46.0,8310,10587943.592,362538781.2864,147853.0,45.1002,1077.0,99.4465,2.9205,91.0646,23.8802
ml_alarm,1.0,0.0039,51.0,8310,10585133.0618,362538781.2864,147405.2,45.1002,1129.0,99.3863,2.9197,90.7888,25.0332
ml_alarm,1.0,0.004,57.0,8310,10582385.5934,362538781.2864,146885.0,45.1002,1203.0,99.3141,2.919,90.4684,26.674
ml_alarm,1.0,0.0041,60.0,8310,10579726.0224,362538781.2864,146337.6,45.1002,1262.0,99.278,2.9182,90.1312,27.9822
ml_alarm,1.0,0.0042,63.0,8310,10577650.1026,362538781.2864,145755.6,45.1002,1340.0,99.2419,2.9177,89.7728,29.7116
ml_alarm,1.0,0.0044,68.0,8310,10574972.1946,362538781.2864,145204.6,45.1002,1409.0,99.1817,2.9169,89.4334,31.2416
ml_alarm,1.0,0.0045,70.0,8310,10568452.9018,362538781.2864,144559.6,45.1002,1488.0,99.1576,2.9151,89.0361,32.9932
ml_alarm,1.0,0.0046,77.0,8310,10563189.5958,362538781.2864,143903.6,45.1002,1570.0,99.0734,2.9137,88.6321,34.8114
ml_alarm,1.0,0.0048,87.0,8310,10558463.7628,362538781.2864,143146.4,45.1002,1637.0,98.9531,2.9124,88.1657,36.297
ml_alarm,1.0,0.0049,98.0,8310,10552190.5192,362538781.2864,142374.4,45.1002,1723.0,98.8207,2.9106,87.6902,38.2038
ml_alarm,1.0,0.0051,109.0,8310,10546506.0404,362538781.2864,141601.4,45.1002,1820.0,98.6883,2.9091,87.2141,40.3546
ml_alarm,1.0,0.0053,121.0,8310,10541479.9202,362538781.2864,140842.6,45.1002,1907.0,98.5439,2.9077,86.7468,42.2837
ml_alarm,1.0,0.0054,133.0,8310,10535250.4954,362538781.2864,140084.4,45.1002,2011.0,98.3995,2.906,86.2798,44.5896
ml_alarm,1.0,0.0056,142.0,8310,10529396.9915,362538781.2864,139164.8,45.1002,2088.0,98.2912,2.9044,85.7134,46.2969
ml_alarm,1.0,0.0058,151.0,8310,10523040.4934,362538781.2864,138323.4,45.1002,2170.0,98.1829,2.9026,85.1952,48.1151
ml_alarm,1.0,0.006,163.0,8310,10516965.848,362538781.2864,137445.2,45.1002,2250.0,98.0385,2.9009,84.6543,49.889
ml_alarm,1.0,0.0062,171.0,8310,10512257.4604,362538781.2864,136545.8,45.1002,2336.0,97.9422,2.8996,84.1003,51.7958
ml_alarm,1.0,0.0063,190.0,8310,10503297.612,362538781.2864,135628.4,45.1002,2393.0,97.7136,2.8972,83.5353,53.0597
ml_alarm,1.0,0.0065,200.0,8310,10497178.2452,362538781.2864,134825.0,45.1002,2466.0,97.5933,2.8955,83.0405,54.6783
ml_alarm,1.0,0.0067,211.0,8310,10491246.5472,362538781.2864,134013.6,45.1002,2532.0,97.4609,2.8938,82.5407,56.1417
ml_alarm,1.0,0.007,230.0,8310,10483562.9964,362538781.2864,133114.4,45.1002,2588.0,97.2323,2.8917,81.9869,57.3834
ml_alarm,1.0,0.0072,247.0,8310,10474764.1148,362538781.2864,132182.6,45.1002,2641.0,97.0277,2.8893,81.413,58.5585
ml_alarm,1.0,0.0074,264.0,8310,10466633.4128,362538781.2864,131467.6,45.1002,2712.0,96.8231,2.887,80.9726,60.1328
ml_alarm,1.0,0.0076,277.0,8310,10460167.6103,362538781.2864,130625.0,45.1002,2781.0,96.6667,2.8853,80.4536,61.6627
ml_alarm,1.0,0.0079,282.0,8310,10455893.3144,362538781.2864,129766.8,45.1002,2846.0,96.6065,2.8841,79.9251,63.104
ml_alarm,1.0,0.0081,292.0,8310,10450137.1542,362538781.2864,128926.8,45.1002,2900.0,96.4862,2.8825,79.4077,64.3013
ml_alarm,1.0,0.0083,302.0,8310,10444026.7169,362538781.2864,128165.4,45.1002,2974.0,96.3658,2.8808,78.9387,65.9421
ml_alarm,1.0,0.0086,311.0,8310,10438985.4217,362538781.2864,127357.8,45.1002,3036.0,96.2575,2.8794,78.4413,67.3168
ml_alarm,1.0,0.0088,323.0,8310,10432500.0589,362538781.2864,126588.2,45.1002,3080.0,96.1131,2.8776,77.9673,68.2924
ml_alarm,1.0,0.0091,339.0,8310,10424087.0968,362538781.2864,125567.8,45.1002,3125.0,95.9206,2.8753,77.3388,69.2902

### reports/tables/regime_targets.csv
target,standby_pct,strategy,test_cut_pct,test_overhead_pct,armed_pct
80.0,0.0,ml_alarm,88.002,2.774,61.402
80.0,0.0,rhythm_alarm,74.32,2.095,41.215
80.0,0.0,ml_forecast,77.942,2.348,42.749
80.0,0.0,rhythm_forecast,74.224,2.089,40.428
80.0,0.0,ml_aligned,73.706,2.042,35.924
80.0,0.0,rhythm_aligned,74.404,2.103,43.308
80.0,0.0,always_on,100.0,2.935,100.0
80.0,0.0,oracle,100.0,2.889,29.802
80.0,0.0,diff_cut_ml_minus_rhythm_aligned,-0.698,-6.031,3.323
80.0,2.0,ml_alarm,88.002,4.314,61.402
80.0,2.0,rhythm_alarm,74.32,3.128,41.215
80.0,2.0,ml_forecast,77.942,3.42,42.749
80.0,2.0,rhythm_forecast,74.224,3.103,40.428
80.0,2.0,ml_aligned,73.706,2.943,35.924
80.0,2.0,rhythm_aligned,74.404,3.189,43.308
80.0,2.0,always_on,100.0,5.443,100.0
80.0,2.0,oracle,100.0,3.637,29.802
80.0,2.0,diff_cut_ml_minus_rhythm_aligned,-0.698,-6.285,3.118
80.0,5.0,ml_alarm,88.002,6.624,61.402
80.0,5.0,rhythm_alarm,74.32,4.679,41.215
80.0,5.0,ml_forecast,77.942,5.028,42.749
80.0,5.0,rhythm_forecast,74.224,4.623,40.428
80.0,5.0,ml_aligned,73.706,4.294,35.924
80.0,5.0,rhythm_aligned,74.404,4.818,43.308
80.0,5.0,always_on,100.0,9.205,100.0
80.0,5.0,oracle,100.0,4.758,29.802
80.0,5.0,diff_cut_ml_minus_rhythm_aligned,-0.698,-6.108,3.222
90.0,0.0,ml_alarm,92.732,2.833,69.147
90.0,0.0,rhythm_alarm,99.615,2.923,99.048
90.0,0.0,ml_forecast,83.081,2.472,47.01
90.0,0.0,rhythm_forecast,99.627,2.923,99.043
90.0,0.0,ml_aligned,86.775,2.535,45.634
90.0,0.0,rhythm_aligned,99.783,2.929,99.159
90.0,0.0,always_on,100.0,2.935,100.0
90.0,0.0,oracle,100.0,2.889,29.802
90.0,0.0,diff_cut_ml_minus_rhythm_aligned,-13.008,-24.109,-4.912
90.0,2.0,ml_alarm,92.732,4.567,69.147
90.0,2.0,rhythm_alarm,99.483,5.398,98.902
90.0,2.0,ml_forecast,83.081,3.65,47.01
90.0,2.0,rhythm_forecast,99.386,5.387,98.831
90.0,2.0,ml_aligned,86.775,3.679,45.634
90.0,2.0,rhythm_aligned,99.783,5.416,99.159
90.0,2.0,always_on,100.0,5.443,100.0
90.0,2.0,oracle,100.0,3.637,29.802
90.0,2.0,diff_cut_ml_minus_rhythm_aligned,-13.008,-23.949,-4.522
90.0,5.0,ml_alarm,92.732,7.168,69.147
90.0,5.0,rhythm_alarm,99.483,9.118,98.902
90.0,5.0,ml_forecast,83.081,5.419,47.01
90.0,5.0,rhythm_forecast,99.386,9.105,98.831
90.0,5.0,ml_aligned,86.775,5.396,45.634
90.0,5.0,rhythm_aligned,99.783,9.146,99.159
90.0,5.0,always_on,100.0,9.205,100.0
90.0,5.0,oracle,100.0,4.758,29.802
90.0,5.0,diff_cut_ml_minus_rhythm_aligned,-13.008,-23.921,-4.748
95.0,0.0,ml_alarm,95.379,2.869,75.791
95.0,0.0,rhythm_alarm,99.615,2.923,99.048
95.0,0.0,ml_forecast,94.753,2.796,75.984
95.0,0.0,rhythm_forecast,99.627,2.923,99.043
95.0,0.0,ml_aligned,91.649,2.717,49.748
95.0,0.0,rhythm_aligned,99.783,2.929,99.159
95.0,0.0,always_on,100.0,2.935,100.0
95.0,0.0,oracle,100.0,2.889,29.802
95.0,0.0,diff_cut_ml_minus_rhythm_aligned,-8.135,-13.834,-3.431
95.0,2.0,ml_alarm,95.379,4.77,75.791
95.0,2.0,rhythm_alarm,99.483,5.398,98.902
95.0,2.0,ml_forecast,94.753,4.702,75.984
95.0,2.0,rhythm_forecast,99.386,5.387,98.831
95.0,2.0,ml_aligned,91.649,3.964,49.748
95.0,2.0,rhythm_aligned,99.783,5.416,99.159
95.0,2.0,always_on,100.0,5.443,100.0
95.0,2.0,oracle,100.0,3.637,29.802
95.0,2.0,diff_cut_ml_minus_rhythm_aligned,-8.135,-13.582,-3.256
95.0,5.0,ml_alarm,95.379,7.621,75.791
95.0,5.0,rhythm_alarm,99.483,9.118,98.902
95.0,5.0,ml_forecast,94.753,7.56,75.984
95.0,5.0,rhythm_forecast,99.386,9.105,98.831
95.0,5.0,ml_aligned,91.649,5.836,49.748
95.0,5.0,rhythm_aligned,99.783,9.146,99.159
95.0,5.0,always_on,100.0,9.205,100.0
95.0,5.0,oracle,100.0,4.758,29.802
95.0,5.0,diff_cut_ml_minus_rhythm_aligned,-8.135,-14.46,-3.128

### reports/tables/latency.csv
model,ms_per_prediction
LightGBM (feature computation + 3 horizons + drop classifier),10.34
rhythm / persistence / moving-avg baselines (feature computation),6.72
"tiny TCN (46,148 params, all 4 outputs)",1.18
"chronos-bolt-small (48M params, zero-shot)",19.35
"timesfm-2.5 (200M params, zero-shot)",190.74

### reports/tables/transfer_harmonized.csv
test_dataset,setting,site_minutes,ap_ml,ap_rhythm,pos_rate,units,ap_diff,ap_diff_lo,ap_diff_hi,draw0_ap_ml,draw0_ap_rhythm,draw0_ap_diff,draw0_ap_diff_lo,draw0_ap_diff_hi,ap_ml_rep_mean,ap_ml_rep_min,ap_ml_rep_max,reps
nlr,lodo_shape,0.0,0.6496,0.6747,0.2497,12,-0.0251,-0.062,0.0204,,,,,,,,,
nlr,lodo_shape_adapted,5.0,,0.6747,0.2497,12,,,,0.6496,0.6747,-0.0251,-0.0638,0.0199,0.63,0.5573,0.6496,5.0
nlr,lodo_shape_adapted,15.0,,0.6747,0.2497,12,,,,0.5524,0.6747,-0.1223,-0.3506,0.1297,0.5927,0.5513,0.6496,5.0
nlr,lodo_shape_adapted,60.0,,0.6747,0.2497,12,,,,0.6362,0.6747,-0.0384,-0.2822,0.1643,0.7086,0.6246,0.7665,5.0
nlr,in_domain_shape,,0.9585,0.6747,0.2497,12,0.2839,0.216,0.3692,,,,,,,,,
elsayed,lodo_shape,0.0,0.8504,0.8829,0.5199,6,-0.0325,-0.3948,0.0415,,,,,,,,,
elsayed,lodo_shape_adapted,5.0,,0.8829,0.5199,6,,,,0.7636,0.8829,-0.1193,-0.3702,0.0206,0.8214,0.7636,0.8504,5.0
elsayed,lodo_shape_adapted,15.0,,0.8829,0.5199,6,,,,0.6614,0.8829,-0.2215,-0.4765,0.0117,0.7824,0.6614,0.877,5.0
elsayed,lodo_shape_adapted,60.0,,0.8829,0.5199,6,,,,0.853,0.8829,-0.0299,-0.4509,0.0698,0.8412,0.7954,0.9078,5.0
elsayed,in_domain_shape,,0.8825,0.8829,0.5199,6,-0.0003,-0.2035,0.085,,,,,,,,,
supercloud,lodo_shape,0.0,0.6592,0.7357,0.4782,112,-0.0765,-0.1198,-0.0356,,,,,,,,,
supercloud,lodo_shape_adapted,5.0,,0.7357,0.4782,112,,,,0.6592,0.7357,-0.0765,-0.1174,-0.0338,0.6227,0.5855,0.6592,5.0
supercloud,lodo_shape_adapted,15.0,,0.7357,0.4782,112,,,,0.6501,0.7357,-0.0856,-0.1332,-0.0419,0.6421,0.5714,0.6707,5.0
supercloud,lodo_shape_adapted,60.0,,0.7357,0.4782,112,,,,0.5818,0.7357,-0.1539,-0.2089,-0.0999,0.6383,0.5818,0.6923,5.0
supercloud,in_domain_shape,,0.8817,0.7357,0.4782,112,0.1461,0.1147,0.1851,,,,,,,,,

### reports/tables/site_scaleup.csv
case,strategy,avg_site_load_mw,extra_energy_pct,extra_mwh_per_year,extra_cost_usd_per_year,down_violations_per_hour,max_down_ramp_mw_per_s
synchronized,raw,79.747,0.0,0.0,0.0,184.257,
synchronized,always_burn,79.747,6.783,47382.551,3790604.072,171.84,
synchronized,predictive,79.747,2.576,17995.546,1439643.716,29.823,
synchronized,predictive_preramp,79.747,1.549,10822.864,865829.148,29.556,
synchronized,reactive,79.747,0.574,4011.56,320924.807,154.767,
synchronized,always_on_limiter,79.747,2.935,20506.048,1640483.804,0.0,
random_offsets,raw,77.828,0.0,0.0,0.0,0.0,2.077
random_offsets,always_burn,77.828,7.498,51122.607,4089808.557,0.0,1.014
random_offsets,predictive,77.828,2.345,15990.378,1279230.261,0.0,1.201
random_offsets,predictive_preramp,77.828,1.263,8610.273,688821.88,0.0,1.233
random_offsets,reactive,77.828,0.541,3688.313,295065.061,0.0,1.908
random_offsets,always_on_limiter,77.828,2.718,18533.671,1482693.689,0.0,1.1

### reports/tables/key_numbers.json
{
  "best_model": "lightgbm",
  "best_mae5": 69.60932312314247,
  "rhythm_mae5": 114.9067704154282,
  "persist_mae5": 287.9507043001874,
  "gain_vs_rhythm": 39.4210429276879,
  "clf": "lightgbm",
  "recall": 0.8242990654205608,
  "lead": 4.8660430839002276,
  "fa_h": 2.2841417611031556,
  "ep_prec": 0.9723502304147466,
  "f1": 0.868083916952653,
  "ap": 0.9272654441159792,
  "rhythm_fa_h": 120.34291984478784,
  "rhythm_recall": 0.8345794392523365,
  "macro_recall": 0.46610434266951994,
  "events": 4280,
  "sd_share": 0.7586448598130842,
  "pred_cut": 83.815,
  "pred_energy": 2.576,
  "burn_cut": 6.739,
  "burn_energy": 6.783,
  "pre_cut": 83.959,
  "pre_energy": 1.549,
  "pre_deferred": 2.951,
  "lim_energy": 2.935,
  "react_cut": 16.005,
  "raw_viol_h": 184.257,
  "site_burn_usd": 3790604.072,
  "site_pred_usd": 1439643.716,
  "site_pre_usd": 865829.148,
  "site_lim_usd": 1640483.804,
  "site_burn_mwh": 47382.551,
  "site_pred_mwh": 17995.546,
  "rand_raw_ramp": 2.077,
  "rand_burn_usd": 4089808.557,
  "rand_pred_usd": 1279230.261,
  "energy_saving_vs_burn": 62.02270381836945
}

--- template comparison and generated tokens ---
paper/arxiv/template.tex:42:three public datasets (H100, B200 and V100 nodes; scripted benchmarks and labelled cluster jobs), the learned trigger
paper/arxiv/template.tex:75:\item \textbf{A three-dataset study} (H100, B200, V100; scripted benchmarks and labelled cluster jobs) with
paper/arxiv/template.tex:95:MIT Supercloud~\cite{supercloud} & 1--2$\times$V100 & 7 model classes, labelled cluster jobs & nvidia-smi 10 Hz & <<supercloud_node_h>> & <<supercloud_units>> (<<supercloud_test_units>>) \\
paper/main.tex:34:validation for a 90\% removal target, the learned trigger removes 86.8\% of test
paper/main.tex:35:violations with the actuator engaged 45.6\% of the time, while rhythm replay meets
paper/main.tex:36:the target only by staying engaged 99.2\% of the time, i.e.\ effectively always on.
paper/main.tex:66:\item A three-dataset study (H100, B200, V100; benchmarks and real jobs) with job-clustered confidence
paper/main.tex:105:which removes only 6.7\% of violations for 6.8\% extra energy) and an oracle that
paper/main.tex:157:Online inference, fixed rate & 0.65 & 0.36\\
paper/main.tex:168:To remove 90\% of violations, the control-aligned learned trigger needs 48.4\%
paper/main.tex:169:engaged time, whereas rhythm replay of the same target reaches 90\% only at 99.2\%,
paper/main.tex:171:$-$50.8 points (95\% CI $-$57.4 to
paper/main.tex:172:$-$8.8), and $-$40.8 points at 95\% removal (CI
paper/main.tex:175:$-$15.9 points, CI $-$25.7 to $-$3.9). At 95\%
paper/main.tex:176:removal the interval includes zero (CI $-$26.3 to 0.5), so with
paper/main.tex:177:12 test clusters the target's effect is clearest in ranking quality (AP 0.58 vs 0.96). The oracle removes all violations at 29.8\% engaged time, which bounds what
paper/main.tex:189:90\% & 48.4 & 99.2 & 64.3\\
paper/main.tex:190:95\% & 58.4 & 99.2 & 74.8\\
paper/main.tex:204:gives 86.8\% removal at 45.6\% engaged time and
paper/main.tex:205:3.7\% energy overhead for the learned trigger; rhythm replay meets the target only
paper/main.tex:206:by staying engaged 99.2\% of the time (5.4\%
paper/main.tex:207:overhead, versus 5.4\% for always-on). At an 80\% target the validation-chosen
paper/main.tex:208:learned threshold undershoots on test (73.7\% removal), a reminder that operating
paper/main.tex:231:anywhere. With shape-only features it reaches AP 0.65 on NLR (rhythm
paper/main.tex:237:0.71 on NLR (range 0.62 to
paper/main.tex:238:0.77) and 0.64 on Supercloud (range
paper/main.tex:249:between benchmark runs, and each NLR inference workload is a single session. Supercloud adds real jobs
paper/arxiv/main.tex:39:data for a 90\% removal target, the learned trigger removes 86.8\% of test violations
paper/arxiv/main.tex:40:with the actuator engaged 45.6\% of the time, while rhythm replay meets the target
paper/arxiv/main.tex:41:only by staying engaged 99.2\% of the time, i.e.\ effectively always on. Across
paper/arxiv/main.tex:42:three public datasets (H100, B200 and V100 nodes; scripted benchmarks and labelled cluster jobs), the learned trigger
paper/arxiv/main.tex:75:\item \textbf{A three-dataset study} (H100, B200, V100; scripted benchmarks and labelled cluster jobs) with
paper/arxiv/main.tex:95:MIT Supercloud~\cite{supercloud} & 1--2$\times$V100 & 7 model classes, labelled cluster jobs & nvidia-smi 10 Hz & 1,292 & 560 (112) \\
paper/arxiv/main.tex:170:6.7\% of violations for 6.8\% extra energy), and an \emph{oracle} that arms just in
paper/arxiv/main.tex:259:Online inference, fixed rate & 0.65 & 0.36 \\
paper/arxiv/main.tex:292:removal target, the learned control-aligned trigger removes 86.8\% of test violations
paper/arxiv/main.tex:293:at 45.6\% engaged time, slightly short of target. Rhythm replay reaches
paper/arxiv/main.tex:294:99.8\% only by staying engaged 99.2\% of the time,
paper/arxiv/main.tex:296:3.7\% and 5.4\% (always-on: 5.4\%).
paper/arxiv/main.tex:297:At an 80\% target both triggers undershoot on test (73.7\% and
paper/arxiv/main.tex:299:perfect-foresight oracle removes all violations at 29.8\% engaged time. It is an iterative
paper/arxiv/main.tex:313:\multirow{3}{*}{80\%} & Learned, aligned & 73.7 & 35.9 & 2.9 \\
paper/arxiv/main.tex:317:\multirow{3}{*}{90\%} & Learned, aligned & 86.8 & 45.6 & 3.7 \\
paper/arxiv/main.tex:318: & Rhythm, aligned & 99.8 & 99.2 & 5.4 \\
paper/arxiv/main.tex:322: & Rhythm, aligned & 99.8 & 99.2 & 5.4 \\
paper/arxiv/main.tex:323: & Learned, big-drop & 95.4 & 75.8 & 4.8 \\
paper/arxiv/main.tex:325: & Always-on & 100.0 & 100.0 & 5.4 \\
paper/arxiv/main.tex:326: & Oracle & 100.0 & 29.8 & 3.6 \\
paper/arxiv/main.tex:334:control-aligned trigger needs 48.4\% engaged time and rhythm replay
paper/arxiv/main.tex:335:99.2\%: a paired cluster-bootstrap difference of $-$50.8
paper/arxiv/main.tex:339:difference is $-$40.8 points (CI $-$49.1 to
paper/arxiv/main.tex:341:$-$15.9 points at 90\% (CI $-$25.7 to $-$3.9)
paper/arxiv/main.tex:342:but not significant at 95\% (CI $-$26.3 to 0.5); with 12 test
paper/arxiv/main.tex:356:90\% & 48.4 & 99.2 & 64.3 \\
paper/arxiv/main.tex:357:95\% & 58.4 & 99.2 & 74.8 \\
paper/arxiv/main.tex:437:Elsayed & 83.4 / 55.4 & 67.3 / 51.8 \\
paper/arxiv/main.tex:474:Unseen site, shape-only & 0.65 & 0.66 & 0.85 \\
paper/arxiv/main.tex:476:+ 5 min of site data & 0.63 (0.56--0.65) & 0.62 (0.59--0.66) & 0.82 (0.76--0.85) \\
paper/arxiv/main.tex:477:+ 15 min & 0.59 (0.55--0.65) & 0.64 (0.57--0.67) & 0.78 (0.66--0.88) \\
paper/arxiv/main.tex:478:+ 60 min & 0.71 (0.62--0.77) & 0.64 (0.58--0.69) & 0.84 (0.80--0.91) \\
paper/template.tex:66:\item A three-dataset study (H100, B200, V100; benchmarks and real jobs) with job-clustered confidence
paper/template.tex:249:between benchmark runs, and each NLR inference workload is a single session. Supercloud adds real jobs
reports/review/arxiv_codex_r2_2026-10-15.md:21:  MIT Supercloud~\cite{supercloud} & 1--2$\times$V100 & 7 model classes, labelled cluster jobs & nvidia-smi 10 Hz & <<supercloud_node_h>> & <<supercloud_units>> (<<supercloud_test_units>>) \\
reports/review/arxiv_codex_r3_2026-10-15.md:3:- **Resolved — “real user jobs.”** Replaced with “labelled cluster jobs”; the prose correctly describes scheduler-observed jobs without claiming production use.
reports/results.md:12:4. **Prediction makes smoothing cheap.** Keeping power at a high floor all the time ("always burn") wastes 6.8% extra energy and still leaves most grid ramp violations in place. Smoothing only when the model expects a drop removes 84% of violations for 2.6% extra energy, 62% less than always-burn. For a 100 MW site that is about **$3.8M versus $1.4M per year** of extra electricity at $80/MWh.
reports/results.md:21:| Predictive smoothing cuts ramp violations by at least 50% while using less extra energy than always-burn | 84% fewer down-ramp violations, 2.6% vs 6.8% extra energy | **MET** |
reports/results.md:38:| inference_offline | 14.0 | 1588 | 113.4 | 1950.9 | 75.4 | 2.4 | 3.0 | 2090.9 |
reports/results.md:39:| inference_online_finite | 19.9 | 1185 | 59.5 | 1370.5 | 63.7 | 5.0 | 30.8 | 1468.2 |
reports/results.md:71:| Infer offline batch | 301.6 | 181.9 | 186.8 | 39.7 |
reports/results.md:74:| Train Llama2-70B LoRA | 71.2 | 38.9 | 44.7 | 45.4 |
reports/results.md:83:| Rhythm repeat | 96.8 | 168.4 | 256.7 |
reports/results.md:84:| LightGBM | 49.7 | 106.7 | 144.4 |
reports/results.md:113:| Train Stable Diffusion | 3247 | 96.8 | 5.0 | 0.4 |
reports/results.md:128:| Train Llama2-70B LoRA | 380.5 | 71.2 | -434.5 | 59.3 | 346.7 |
reports/results.md:138:| rhythm / persistence / moving-avg baselines (feature computation) | 6.72 |
reports/results.md:154:| Always burn (80% floor) | 171.8 | 6.7 | 19.7 | 6.8 | 0.0 |
reports/results.md:155:| Predictive (ML-armed fill) | 29.8 | 83.8 | 58.7 | 2.6 | 0.0 |
reports/results.md:164:- **Always-burn is expensive and still fails the grid limit.** An 80% floor allows a 20% instant fall, which is twice the 10%/s limit, so it removes only 7% of violations while burning 6.8% extra energy.
reports/results.md:177:| All synchronized | Always burn (80% floor) | 6.8 | 47382.6 | 3.8 | 171.8 |
reports/results.md:178:| All synchronized | Predictive (ML-armed fill) | 2.6 | 17995.5 | 1.4 | 29.8 |
reports/results.md:187:| Random offsets | Always-on limiter, instant actuator (reference) | 2.7 | 18533.7 | 1.5 | 0.0 |
reports/review/prior_art_2026-10-12.md:8:- arXiv 2606.04869. HESS + residual differentiable predictive control, perfect 0.64 s preview, synthetic workloads, grid side only, "forecasting errors are not considered".
reports/tables/regime_map.csv:2:0.0,0.0,0.0,rhythm_aligned,2.241,79.266,89.868,2.796,76.041,2.157,77.894,2.527,75.271,2.132,76.402,2.182,79.266,2.241,39.35,2.528,100.0,2.935,6.739,6.783,100.0,2.889
reports/tables/regime_map.csv:3:0.0,0.0,0.2,rhythm_aligned,2.211,79.35,89.832,2.795,75.848,2.151,76.354,2.444,74.801,2.126,77.16,2.209,79.35,2.211,16.185,1.833,100.0,2.935,6.739,6.783,100.0,2.889
reports/tables/regime_map.csv:4:0.0,0.0,0.5,ml_aligned,2.059,73.742,89.759,2.794,75.788,2.141,76.101,2.38,74.669,2.116,73.742,2.059,79.314,2.193,15.776,1.258,100.0,2.935,6.739,6.783,100.0,2.889
reports/tables/regime_map.csv:5:0.0,0.0,1.0,ml_aligned,2.042,73.706,88.002,2.774,74.32,2.095,77.942,2.348,74.224,2.089,73.706,2.042,74.404,2.103,15.981,0.467,100.0,2.935,6.739,6.783,100.0,2.889
reports/tables/regime_map.csv:6:0.0,0.0,2.0,ml_aligned,2.068,74.428,89.037,2.784,75.584,2.112,76.029,2.304,74.452,2.081,74.428,2.068,78.977,2.162,16.27,0.478,100.0,2.935,6.739,6.783,100.0,2.889
reports/tables/regime_map.csv:7:0.0,0.0,3.0,ml_aligned,2.071,74.079,88.905,2.782,75.511,2.127,78.592,2.336,74.344,2.1,74.079,2.071,78.881,2.158,16.245,0.481,100.0,2.935,6.739,6.783,100.0,2.889
reports/tables/regime_map.csv:8:0.0,0.5,0.0,rhythm_forecast,2.387,75.271,89.868,3.194,76.041,2.424,77.894,2.79,75.271,2.387,76.402,2.436,79.266,2.537,39.35,2.893,100.0,3.562,6.739,6.783,100.0,3.076
reports/tables/regime_map.csv:9:0.0,0.5,0.2,rhythm_aligned,2.506,79.35,89.832,3.193,75.848,2.418,76.354,2.707,74.801,2.381,77.16,2.466,79.35,2.506,16.185,2.198,100.0,3.562,6.739,6.783,100.0,3.076
reports/tables/regime_map.csv:10:0.0,0.5,0.5,ml_aligned,2.296,73.742,89.759,3.192,75.788,2.408,76.101,2.643,74.669,2.371,73.742,2.296,79.314,2.488,15.776,1.623,100.0,3.562,6.739,6.783,100.0,3.076
reports/tables/regime_map.csv:11:0.0,0.5,1.0,ml_aligned,2.267,73.706,88.002,3.159,74.32,2.353,77.942,2.616,74.224,2.342,73.706,2.267,74.404,2.374,15.981,0.833,100.0,3.562,6.739,6.783,100.0,3.076
reports/tables/regime_map.csv:12:0.0,0.5,2.0,ml_aligned,2.297,74.428,89.037,3.181,75.584,2.379,76.029,2.566,74.452,2.336,74.428,2.297,78.977,2.455,16.27,0.844,100.0,3.562,6.739,6.783,100.0,3.076
reports/tables/regime_map.csv:13:0.0,0.5,3.0,ml_aligned,2.302,74.079,88.905,3.179,75.511,2.395,78.592,2.607,74.344,2.354,74.079,2.302,78.881,2.452,16.245,0.847,100.0,3.562,6.739,6.783,100.0,3.076
reports/tables/regime_map.csv:14:0.0,1.0,0.0,rhythm_forecast,2.642,75.271,89.868,3.592,76.041,2.692,77.894,3.052,75.271,2.642,76.402,2.691,79.266,2.832,39.35,3.259,100.0,4.189,6.739,6.783,100.0,3.263
reports/tables/regime_map.csv:15:0.0,1.0,0.2,rhythm_forecast,2.636,74.801,89.832,3.591,75.848,2.686,76.354,2.969,74.801,2.636,77.16,2.722,79.35,2.802,16.185,2.563,100.0,4.189,6.739,6.783,100.0,3.263
reports/tables/regime_map.csv:16:0.0,1.0,0.5,ml_aligned,2.533,73.742,89.759,3.59,75.788,2.676,76.101,2.905,74.669,2.626,73.742,2.533,79.314,2.783,15.776,1.989,100.0,4.189,6.739,6.783,100.0,3.263
reports/tables/regime_map.csv:17:0.0,1.0,1.0,ml_aligned,2.492,73.706,88.002,3.544,74.32,2.612,77.942,2.884,74.224,2.596,73.706,2.492,74.404,2.646,15.981,1.198,100.0,4.189,6.739,6.783,100.0,3.263
reports/tables/regime_map.csv:18:0.0,1.0,2.0,ml_aligned,2.525,74.428,89.037,3.579,75.584,2.647,76.029,2.828,74.452,2.59,74.428,2.525,78.977,2.749,16.27,1.21,100.0,4.189,6.739,6.783,100.0,3.263
reports/tables/regime_map.csv:19:0.0,1.0,3.0,ml_aligned,2.533,74.079,88.905,3.577,75.511,2.662,78.592,2.879,74.344,2.609,74.079,2.533,78.881,2.746,16.245,1.212,100.0,4.189,6.739,6.783,100.0,3.263
reports/tables/regime_map.csv:20:0.0,2.0,0.0,rhythm_forecast,3.152,75.271,89.868,4.389,76.041,3.227,77.894,3.577,75.271,3.152,76.402,3.2,79.266,3.423,39.35,3.99,100.0,5.443,6.739,6.783,100.0,3.637
reports/tables/regime_map.csv:21:0.0,2.0,0.2,rhythm_forecast,3.146,74.801,89.832,4.387,75.848,3.221,76.354,3.494,74.801,3.146,77.16,3.235,79.35,3.392,16.185,3.294,100.0,5.443,6.739,6.783,100.0,3.637
reports/tables/regime_map.csv:22:0.0,2.0,0.5,ml_aligned,3.007,73.742,89.759,4.385,75.788,3.211,76.101,3.43,74.669,3.136,73.742,3.007,79.314,3.372,15.776,2.72,100.0,5.443,6.739,6.783,100.0,3.637
reports/tables/regime_map.csv:23:0.0,2.0,1.0,ml_aligned,2.943,73.706,88.002,4.314,74.32,3.128,77.942,3.42,74.224,3.103,73.706,2.943,74.404,3.189,15.981,1.929,100.0,5.443,6.739,6.783,100.0,3.637
reports/tables/regime_map.csv:24:0.0,2.0,2.0,ml_aligned,2.981,74.428,89.037,4.373,75.584,3.181,76.029,3.352,74.452,3.1,74.428,2.981,78.977,3.337,16.27,1.941,100.0,5.443,6.739,6.783,100.0,3.637
reports/tables/regime_map.csv:25:0.0,2.0,3.0,ml_aligned,2.995,74.079,88.905,4.371,75.511,3.196,78.592,3.423,74.344,3.119,74.079,2.995,78.881,3.334,16.245,1.944,100.0,5.443,6.739,6.783,100.0,3.637
reports/tables/regime_map.csv:26:0.0,5.0,0.0,rhythm_forecast,4.683,75.271,89.868,6.777,76.041,4.832,77.894,5.152,75.271,4.683,76.402,4.727,79.266,5.196,39.35,6.183,100.0,9.205,6.739,6.783,100.0,4.758
reports/tables/regime_map.csv:27:0.0,5.0,0.2,rhythm_forecast,4.677,74.801,89.832,6.774,75.848,4.826,76.354,5.068,74.801,4.677,77.16,4.775,79.35,5.164,16.185,5.487,100.0,9.205,6.739,6.783,100.0,4.758
reports/tables/regime_map.csv:28:0.0,5.0,0.5,ml_aligned,4.43,73.742,89.759,6.772,75.788,4.815,76.101,5.004,74.669,4.666,73.742,4.43,79.314,5.141,15.776,4.912,100.0,9.205,6.739,6.783,100.0,4.758
reports/tables/regime_map.csv:29:0.0,5.0,1.0,ml_aligned,4.294,73.706,88.002,6.624,74.32,4.679,77.942,5.028,74.224,4.623,73.706,4.294,74.404,4.818,15.981,4.122,100.0,9.205,6.739,6.783,100.0,4.758
reports/tables/regime_map.csv:30:0.0,5.0,2.0,ml_aligned,4.351,74.428,89.037,6.757,75.584,4.784,76.029,4.924,74.452,4.628,74.428,4.351,78.977,5.1,16.27,4.135,100.0,9.205,6.739,6.783,100.0,4.758
reports/tables/regime_map.csv:31:0.0,5.0,3.0,ml_aligned,4.381,74.079,88.905,6.754,75.511,4.798,78.592,5.054,74.344,4.647,74.079,4.381,78.881,5.097,16.245,4.138,100.0,9.205,6.739,6.783,100.0,4.758
reports/tables/regime_map.csv:32:0.0,10.0,0.0,rhythm_forecast,7.235,75.271,89.868,10.758,76.041,7.508,77.894,7.777,75.271,7.235,76.402,7.272,79.266,8.15,39.35,9.839,100.0,15.475,6.739,6.783,100.0,6.626
reports/tables/regime_map.csv:33:0.0,10.0,0.2,rhythm_forecast,7.228,74.801,89.832,10.754,75.848,7.5,76.354,7.692,74.801,7.228,77.16,7.342,79.35,8.116,16.185,9.141,100.0,15.475,6.739,6.783,100.0,6.626
reports/tables/regime_map.csv:34:0.0,10.0,0.5,ml_aligned,6.8,73.742,89.759,10.75,75.788,7.489,76.101,7.627,74.669,7.217,73.742,6.8,79.314,8.088,15.776,8.566,100.0,15.475,6.739,6.783,100.0,6.626
reports/tables/regime_map.csv:35:0.0,10.0,1.0,ml_aligned,6.547,73.706,88.002,10.474,74.32,7.263,77.942,7.708,74.224,7.158,73.706,6.547,74.404,7.533,15.981,7.777,100.0,15.475,6.739,6.783,100.0,6.626
reports/tables/regime_map.csv:36:0.0,10.0,2.0,ml_aligned,6.634,74.428,89.037,10.729,75.584,7.455,76.029,7.544,74.452,7.176,74.428,6.634,78.977,8.039,16.27,7.791,100.0,15.475,6.739,6.783,100.0,6.626
reports/tables/regime_map.csv:37:0.0,10.0,3.0,ml_aligned,6.691,74.079,88.905,10.726,75.511,7.469,78.592,7.772,74.344,7.194,74.079,6.691,78.881,8.037,16.245,7.794,100.0,15.475,6.739,6.783,100.0,6.626
reports/tables/regime_map.csv:38:2.0,0.0,0.0,ml_alarm,2.991,99.783,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,39.35,14.655,100.0,2.997,6.739,6.783,100.0,14.579
reports/tables/regime_map.csv:39:2.0,0.0,0.2,ml_alarm,2.991,99.783,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,16.185,13.93,100.0,2.997,6.739,6.783,100.0,14.579
reports/tables/regime_map.csv:40:2.0,0.0,0.5,ml_alarm,2.991,99.783,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,15.776,13.334,100.0,2.997,6.739,6.783,100.0,14.579
reports/tables/regime_map.csv:41:2.0,0.0,1.0,rhythm_aligned,3.113,83.767,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,99.783,2.991,83.767,3.113,15.981,12.517,100.0,2.997,6.739,6.783,100.0,14.579
reports/tables/regime_map.csv:42:2.0,0.0,2.0,ml_alarm,2.99,99.759,99.759,2.99,99.759,2.99,99.759,2.99,99.759,2.99,99.759,2.99,99.759,2.99,16.27,12.536,100.0,2.997,6.739,6.783,100.0,14.579
reports/tables/regime_map.csv:43:2.0,0.0,3.0,ml_alarm,2.99,99.759,99.759,2.99,99.759,2.99,99.759,2.99,99.759,2.99,99.759,2.99,99.759,2.99,16.245,12.557,100.0,2.997,6.739,6.783,100.0,14.579
reports/tables/regime_map.csv:44:2.0,0.5,0.0,rhythm_forecast,3.658,83.237,99.783,3.612,83.369,3.638,99.783,3.612,83.237,3.658,99.783,3.612,83.598,4.097,39.35,15.02,100.0,3.624,6.739,6.783,100.0,14.766
reports/tables/regime_map.csv:45:2.0,0.5,0.2,rhythm_forecast,3.657,83.177,99.783,3.612,83.345,3.638,99.783,3.612,83.177,3.657,99.783,3.612,83.574,4.094,16.185,14.296,100.0,3.624,6.739,6.783,100.0,14.766
reports/tables/regime_map.csv:46:2.0,0.5,0.5,rhythm_forecast,3.656,83.117,99.783,3.612,83.321,3.64,99.783,3.612,83.117,3.656,99.783,3.612,83.586,4.095,15.776,13.699,100.0,3.624,6.739,6.783,100.0,14.766
reports/tables/regime_map.csv:47:2.0,0.5,1.0,rhythm_aligned,3.536,83.767,99.783,3.612,83.261,3.617,99.783,3.612,83.117,3.642,99.783,3.612,83.767,3.536,15.981,12.882,100.0,3.624,6.739,6.783,100.0,14.766
reports/tables/regime_map.csv:48:2.0,0.5,2.0,rhythm_forecast,3.631,83.165,99.759,3.612,83.381,3.641,99.759,3.612,83.165,3.631,99.759,3.612,83.574,4.087,16.27,12.902,100.0,3.624,6.739,6.783,100.0,14.766
reports/tables/regime_map.csv:49:2.0,0.5,3.0,rhythm_forecast,3.641,83.273,99.759,3.612,83.406,3.642,99.759,3.612,83.273,3.641,99.759,3.612,83.61,4.088,16.245,12.923,100.0,3.624,6.739,6.783,100.0,14.766
reports/tables/regime_map.csv:50:2.0,1.0,0.0,rhythm_forecast,4.078,83.237,99.783,4.234,83.369,4.06,99.783,4.234,83.237,4.078,99.783,4.234,83.598,4.518,39.35,15.386,100.0,4.251,6.739,6.783,100.0,14.953
reports/tables/regime_map.csv:51:2.0,1.0,0.2,rhythm_forecast,4.077,83.177,99.783,4.234,83.345,4.06,99.783,4.234,83.177,4.077,99.783,4.234,83.574,4.515,16.185,14.661,100.0,4.251,6.739,6.783,100.0,14.953
reports/tables/regime_map.csv:52:2.0,1.0,0.5,rhythm_forecast,4.076,83.117,99.783,4.234,83.321,4.062,99.783,4.234,83.117,4.076,99.783,4.234,83.586,4.516,15.776,14.065,100.0,4.251,6.739,6.783,100.0,14.953
reports/tables/regime_map.csv:53:2.0,1.0,1.0,rhythm_aligned,3.959,83.767,99.783,4.234,83.261,4.038,99.783,4.234,83.117,4.061,99.783,4.234,83.767,3.959,15.981,13.248,100.0,4.251,6.739,6.783,100.0,14.953
reports/tables/regime_map.csv:54:2.0,1.0,2.0,rhythm_forecast,4.05,83.165,99.759,4.234,83.381,4.063,99.759,4.234,83.165,4.05,99.759,4.234,83.574,4.507,16.27,13.267,100.0,4.251,6.739,6.783,100.0,14.953
reports/tables/regime_map.csv:55:2.0,1.0,3.0,rhythm_forecast,4.06,83.273,99.759,4.234,83.406,4.063,99.759,4.234,83.273,4.06,99.759,4.234,83.61,4.509,16.245,13.288,100.0,4.251,6.739,6.783,100.0,14.953
reports/tables/regime_map.csv:56:2.0,2.0,0.0,rhythm_forecast,4.918,83.237,99.783,5.478,83.369,4.904,99.783,5.478,83.237,4.918,76.402,8.481,83.598,5.361,39.35,16.117,100.0,5.505,6.739,6.783,100.0,15.327
reports/tables/regime_map.csv:57:2.0,2.0,0.2,rhythm_forecast,4.917,83.177,99.783,5.478,83.345,4.904,99.783,5.478,83.177,4.917,77.16,8.592,83.574,5.357,16.185,15.392,100.0,5.505,6.739,6.783,100.0,15.327
reports/tables/regime_map.csv:58:2.0,2.0,0.5,rhythm_forecast,4.915,83.117,99.783,5.478,83.321,4.906,99.783,5.478,83.117,4.915,77.665,8.822,83.586,5.358,15.776,14.796,100.0,5.505,6.739,6.783,100.0,15.327
reports/tables/regime_map.csv:59:2.0,2.0,1.0,rhythm_aligned,4.805,83.767,99.783,5.478,83.261,4.878,99.783,5.478,83.117,4.9,99.783,5.478,83.767,4.805,15.981,13.979,100.0,5.505,6.739,6.783,100.0,15.327
reports/tables/regime_map.csv:60:2.0,2.0,2.0,rhythm_forecast,4.888,83.165,99.759,5.477,83.381,4.905,99.759,5.477,83.165,4.888,78.761,9.119,83.574,5.349,16.27,13.998,100.0,5.505,6.739,6.783,100.0,15.327
reports/tables/regime_map.csv:61:2.0,2.0,3.0,rhythm_forecast,4.898,83.273,99.759,5.477,83.406,4.906,99.759,5.477,83.273,4.898,78.063,8.679,83.61,5.351,16.245,14.02,100.0,5.505,6.739,6.783,100.0,15.327
reports/tables/regime_map.csv:62:2.0,5.0,0.0,rhythm_aligned,10.772,79.266,99.783,9.208,83.369,7.437,81.035,12.319,76.619,10.111,76.402,10.008,79.266,10.772,39.35,18.31,100.0,9.267,6.739,6.783,100.0,16.448
reports/tables/regime_map.csv:63:2.0,5.0,0.2,rhythm_aligned,10.768,79.35,99.783,9.208,83.345,7.436,81.095,12.237,76.51,10.11,77.16,10.132,79.35,10.768,16.185,17.585,100.0,9.267,6.739,6.783,100.0,16.448
reports/tables/regime_map.csv:64:2.0,5.0,0.5,rhythm_aligned,10.76,79.314,99.783,9.208,75.788,10.773,81.119,12.177,76.366,10.1,77.665,10.371,79.314,10.76,15.776,16.988,100.0,9.267,6.739,6.783,100.0,16.448
reports/tables/regime_map.csv:65:2.0,5.0,1.0,rhythm_aligned,10.238,75.523,99.783,9.208,77.521,10.239,83.081,11.78,79.326,10.695,79.206,10.493,75.523,10.238,15.981,16.172,100.0,9.267,6.739,6.783,100.0,16.448
reports/tables/regime_map.csv:66:2.0,5.0,2.0,rhythm_aligned,10.701,78.977,99.759,9.207,75.584,10.735,81.059,12.083,76.149,10.059,78.761,10.685,78.977,10.701,16.27,16.192,100.0,9.267,6.739,6.783,100.0,16.448
reports/tables/regime_map.csv:67:2.0,5.0,3.0,rhythm_aligned,10.695,78.881,99.759,9.207,75.511,10.732,80.866,12.079,76.029,10.059,78.063,10.239,78.881,10.695,16.245,16.214,100.0,9.267,6.739,6.783,100.0,16.448
reports/tables/regime_map.csv:68:2.0,10.0,0.0,rhythm_aligned,13.726,79.266,89.868,17.024,76.041,13.461,81.035,15.166,76.619,12.777,76.402,12.553,79.266,13.726,39.35,21.966,100.0,15.537,6.739,6.783,100.0,18.316
reports/tables/regime_map.csv:69:2.0,10.0,0.2,rhythm_aligned,13.72,79.35,89.832,17.017,75.848,13.457,81.095,15.083,76.51,12.775,77.16,12.698,79.35,13.72,16.185,21.239,100.0,15.537,6.739,6.783,100.0,18.316
reports/tables/regime_map.csv:70:2.0,10.0,0.5,rhythm_aligned,13.708,79.314,89.759,17.011,75.788,13.447,81.119,15.022,76.366,12.765,77.665,12.952,79.314,13.708,15.776,20.642,100.0,15.537,6.739,6.783,100.0,18.316
reports/tables/regime_map.csv:71:2.0,10.0,1.0,rhythm_aligned,12.978,75.331,88.002,16.991,77.521,12.986,82.708,14.693,76.667,12.785,79.206,13.117,75.331,12.978,15.981,19.827,100.0,15.537,6.739,6.783,100.0,18.316
reports/tables/regime_map.csv:72:2.0,10.0,2.0,rhythm_aligned,13.64,78.977,89.037,16.999,75.584,13.406,81.059,14.926,76.149,12.721,78.761,13.296,78.977,13.64,16.27,19.849,100.0,15.537,6.739,6.783,100.0,18.316
reports/tables/regime_map.csv:73:2.0,10.0,3.0,rhythm_aligned,13.635,78.881,88.905,16.991,75.511,13.402,80.866,14.921,76.029,12.721,78.063,12.839,78.881,13.635,16.245,19.871,100.0,15.537,6.739,6.783,100.0,18.316
reports/tables/regime_map.csv:74:10.0,0.0,0.0,ml_alarm,3.238,99.783,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,39.35,63.163,100.0,3.244,6.739,6.783,100.0,61.339
reports/tables/regime_map.csv:75:10.0,0.0,0.2,ml_alarm,3.238,99.783,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,16.185,62.322,100.0,3.244,6.739,6.783,100.0,61.339
reports/tables/regime_map.csv:76:10.0,0.0,0.5,ml_alarm,3.238,99.783,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,15.776,61.639,100.0,3.244,6.739,6.783,100.0,61.339
reports/tables/regime_map.csv:77:10.0,0.0,1.0,ml_alarm,3.238,99.783,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,99.783,3.238,15.981,60.717,100.0,3.244,6.739,6.783,100.0,61.339
reports/tables/regime_map.csv:78:10.0,0.0,2.0,ml_alarm,3.237,99.759,99.759,3.237,99.759,3.237,99.759,3.237,99.759,3.237,99.759,3.237,99.759,3.237,16.27,60.766,100.0,3.244,6.739,6.783,100.0,61.339
reports/tables/regime_map.csv:79:10.0,0.0,3.0,ml_alarm,3.238,99.759,99.759,3.238,99.759,3.238,99.759,3.238,99.759,3.238,99.759,3.238,99.759,3.238,16.245,60.862,100.0,3.244,6.739,6.783,100.0,61.339
reports/tables/regime_map.csv:80:10.0,0.5,0.0,ml_alarm,3.86,99.783,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.86,39.35,63.529,100.0,3.871,6.739,6.783,100.0,61.526
reports/tables/regime_map.csv:81:10.0,0.5,0.2,ml_alarm,3.86,99.783,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.86,16.185,62.687,100.0,3.871,6.739,6.783,100.0,61.526
reports/tables/regime_map.csv:82:10.0,0.5,0.5,ml_alarm,3.86,99.783,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.86,15.776,62.004,100.0,3.871,6.739,6.783,100.0,61.526
reports/tables/regime_map.csv:83:10.0,0.5,1.0,rhythm_forecast,3.867,99.783,99.783,3.86,99.783,3.86,99.783,3.86,99.783,3.867,99.783,3.86,99.783,3.86,15.981,61.082,100.0,3.871,6.739,6.783,100.0,61.526
reports/tables/regime_map.csv:84:10.0,0.5,2.0,ml_alarm,3.859,99.759,99.759,3.859,99.759,3.859,99.759,3.859,99.759,3.859,99.759,3.859,99.759,3.859,16.27,61.132,100.0,3.871,6.739,6.783,100.0,61.526
reports/tables/regime_map.csv:85:10.0,0.5,3.0,ml_alarm,3.859,99.759,99.759,3.859,99.759,3.859,99.759,3.859,99.759,3.859,99.759,3.859,99.759,3.859,16.245,61.227,100.0,3.871,6.739,6.783,100.0,61.526
reports/tables/regime_map.csv:86:10.0,1.0,0.0,ml_alarm,4.481,99.783,99.783,4.481,99.783,4.481,99.783,4.481,99.783,4.481,99.783,4.481,99.783,4.481,39.35,63.894,100.0,4.498,6.739,6.783,100.0,61.713
reports/tables/regime_map.csv:87:10.0,1.0,0.2,ml_alarm,4.481,99.783,99.783,4.481,99.783,4.481,99.783,4.481,99.783,4.481,99.783,4.481,99.783,4.481,16.185,63.052,100.0,4.498,6.739,6.783,100.0,61.713
reports/tables/regime_map.csv:88:10.0,1.0,0.5,ml_alarm,4.481,99.783,99.783,4.481,99.783,4.481,99.783,4.481,99.783,4.481,99.783,4.481,99.783,4.481,15.776,62.37,100.0,4.498,6.739,6.783,100.0,61.713
reports/tables/regime_map.csv:89:10.0,1.0,1.0,rhythm_forecast,4.489,99.783,99.783,4.481,99.783,4.481,99.783,4.481,99.783,4.489,99.783,4.481,99.783,4.481,15.981,61.448,100.0,4.498,6.739,6.783,100.0,61.713
reports/tables/regime_map.csv:90:10.0,1.0,2.0,ml_alarm,4.481,99.759,99.759,4.481,99.759,4.481,99.759,4.481,99.759,4.481,99.759,4.481,99.759,4.481,16.27,61.498,100.0,4.498,6.739,6.783,100.0,61.713
reports/tables/regime_map.csv:91:10.0,1.0,3.0,ml_alarm,4.481,99.759,99.759,4.481,99.759,4.481,99.759,4.481,99.759,4.481,99.759,4.481,99.759,4.481,16.245,61.593,100.0,4.498,6.739,6.783,100.0,61.713
reports/tables/regime_map.csv:92:10.0,2.0,0.0,ml_alarm,5.725,99.783,99.783,5.725,99.783,5.725,99.783,5.725,99.783,5.725,99.783,5.725,99.783,5.725,39.35,64.625,100.0,5.752,6.739,6.783,100.0,62.087
reports/tables/regime_map.csv:93:10.0,2.0,0.2,ml_alarm,5.725,99.783,99.783,5.725,99.783,5.725,99.783,5.725,99.783,5.725,99.783,5.725,99.783,5.725,16.185,63.783,100.0,5.752,6.739,6.783,100.0,62.087
reports/tables/regime_map.csv:94:10.0,2.0,0.5,ml_alarm,5.725,99.783,99.783,5.725,99.783,5.725,99.783,5.725,99.783,5.725,99.783,5.725,99.783,5.725,15.776,63.1,100.0,5.752,6.739,6.783,100.0,62.087
reports/tables/regime_map.csv:95:10.0,2.0,1.0,rhythm_forecast,5.732,99.783,99.783,5.725,99.783,5.725,99.783,5.725,99.783,5.732,99.783,5.725,99.783,5.725,15.981,62.179,100.0,5.752,6.739,6.783,100.0,62.087
reports/tables/regime_map.csv:96:10.0,2.0,2.0,ml_alarm,5.724,99.759,99.759,5.724,99.759,5.724,99.759,5.724,99.759,5.724,99.759,5.724,99.759,5.724,16.27,62.229,100.0,5.752,6.739,6.783,100.0,62.087
reports/tables/regime_map.csv:97:10.0,2.0,3.0,ml_alarm,5.724,99.759,99.759,5.724,99.759,5.724,99.759,5.724,99.759,5.724,99.759,5.724,99.759,5.724,16.245,62.324,100.0,5.752,6.739,6.783,100.0,62.087
reports/tables/regime_map.csv:98:10.0,5.0,0.0,ml_alarm,9.455,99.783,99.783,9.455,99.783,9.455,99.783,9.455,99.783,9.455,99.783,9.455,99.783,9.455,39.35,66.819,100.0,9.514,6.739,6.783,100.0,63.208
reports/tables/regime_map.csv:99:10.0,5.0,0.2,ml_alarm,9.455,99.783,99.783,9.455,99.783,9.455,99.783,9.455,99.783,9.455,99.783,9.455,99.783,9.455,16.185,65.976,100.0,9.514,6.739,6.783,100.0,63.208
reports/tables/regime_map.csv:100:10.0,5.0,0.5,ml_alarm,9.455,99.783,99.783,9.455,99.783,9.455,99.783,9.455,99.783,9.455,99.783,9.455,99.783,9.455,15.776,65.293,100.0,9.514,6.739,6.783,100.0,63.208
reports/tables/regime_map.csv:101:10.0,5.0,1.0,rhythm_aligned,10.192,83.767,99.783,9.455,99.783,9.455,99.783,9.455,99.783,9.462,99.783,9.455,83.767,10.192,15.981,64.372,100.0,9.514,6.739,6.783,100.0,63.208
reports/tables/regime_map.csv:102:10.0,5.0,2.0,ml_alarm,9.454,99.759,99.759,9.454,99.759,9.454,99.759,9.454,99.759,9.454,99.759,9.454,99.759,9.454,16.27,64.423,100.0,9.514,6.739,6.783,100.0,63.208
reports/tables/regime_map.csv:103:10.0,5.0,3.0,ml_alarm,9.454,99.759,99.759,9.454,99.759,9.455,99.759,9.455,99.759,9.454,99.759,9.454,99.759,9.455,16.245,64.519,100.0,9.514,6.739,6.783,100.0,63.208
reports/tables/regime_map.csv:104:10.0,10.0,0.0,rhythm_forecast,15.042,83.237,99.783,15.672,83.369,14.959,99.783,15.672,83.237,15.042,99.783,15.672,83.598,17.192,39.35,70.475,100.0,15.784,6.739,6.783,100.0,65.076
reports/tables/regime_map.csv:105:10.0,10.0,0.2,rhythm_forecast,15.038,83.177,99.783,15.672,83.345,14.957,99.783,15.672,83.177,15.038,99.783,15.672,83.574,17.18,16.185,69.63,100.0,15.784,6.739,6.783,100.0,65.076
reports/tables/regime_map.csv:106:10.0,10.0,0.5,rhythm_forecast,15.035,83.117,99.783,15.672,83.321,14.975,99.783,15.672,83.117,15.035,99.783,15.672,83.586,17.186,15.776,68.947,100.0,15.784,6.739,6.783,100.0,65.076
reports/tables/regime_map.csv:107:10.0,10.0,1.0,rhythm_aligned,14.422,83.767,99.783,15.672,83.261,14.873,99.783,15.672,83.117,15.003,99.783,15.672,83.767,14.422,15.981,68.026,100.0,15.784,6.739,6.783,100.0,65.076
reports/tables/regime_map.csv:108:10.0,10.0,2.0,rhythm_forecast,14.978,83.165,99.759,15.671,83.381,14.971,99.759,15.671,83.165,14.978,99.759,15.671,83.574,17.155,16.27,68.079,100.0,15.784,6.739,6.783,100.0,65.076
reports/tables/regime_map.csv:109:10.0,10.0,3.0,rhythm_forecast,14.943,83.273,99.759,15.671,83.406,14.969,99.759,15.672,83.273,14.943,99.759,15.671,83.61,17.17,16.245,68.175,100.0,15.784,6.739,6.783,100.0,65.076
reports/tables/forecast_by_workload.csv:11:persistence,5,240.12575010006353,579.8041026057068,16.723024626001305,train_stable_diffusion
reports/tables/forecast_by_workload.csv:19:moving_avg,1,101.71081993155912,240.8845572654894,7.046032851643397,inference_online_rate
reports/tables/forecast_by_workload.csv:24:moving_avg,5,151.2500201872087,386.75769209003795,12.739145924095736,inference_online_rate
reports/tables/forecast_by_workload.csv:29:moving_avg,10,213.7341672087239,527.0882046049111,20.171698590691566,inference_online_rate
reports/tables/forecast_by_workload.csv:31:moving_avg,10,195.48750141154522,458.0234016489767,16.63233620365442,train_stable_diffusion
reports/tables/forecast_by_workload.csv:36:rhythm,1,54.26604933767085,206.79956806653124,4.348707859857755,train_stable_diffusion
reports/tables/forecast_by_workload.csv:41:rhythm,5,79.0269499446756,294.566302513468,6.879623529629806,train_stable_diffusion
reports/tables/forecast_by_workload.csv:65:tcn,1,26.398086923004158,77.09448361329397,1.4685609574243694,train_llama2_70b_lora
reports/tables/forecast_by_workload.csv:67:tcn,5,186.76751997493216,437.86157751011893,18.499665525556892,inference_offline
reports/tables/forecast_by_workload.csv:72:tcn,10,205.46215873675973,454.5998591590788,19.72727644093522,inference_offline
reports/tables/key_numbers.json:21: "burn_cut": 6.739,
reports/tables/key_numbers.json:22: "burn_energy": 6.783,
reports/tables/key_numbers.json:30: "site_pred_usd": 1439643.716,
reports/tables/forecast_subset_with_chronos.csv:4:persistence,10,292.42708654321285,614.9398268475417,26.876888976550617
reports/tables/forecast_subset_with_chronos.csv:8:rhythm,1,96.75880030004883,281.3976003943291,7.415015072170636
reports/tables/forecast_subset_with_chronos.csv:10:rhythm,10,256.72213450146484,573.5542181246544,25.008732498291064
reports/tables/forecast_subset_with_chronos.csv:11:lightgbm,1,49.7472312202189,166.1157404377163,3.7382179700264735
reports/tables/forecast_subset_with_chronos.csv:12:lightgbm,5,106.73461284622095,308.7401574418433,11.163486876070815
reports/tables/transfer_harmonized.csv:2:nlr,lodo_shape,0.0,0.6496,0.6747,0.2497,12,-0.0251,-0.062,0.0204,,,,,,,,,
reports/tables/transfer_harmonized.csv:3:nlr,lodo_shape_adapted,5.0,,0.6747,0.2497,12,,,,0.6496,0.6747,-0.0251,-0.0638,0.0199,0.63,0.5573,0.6496,5.0
reports/tables/transfer_harmonized.csv:4:nlr,lodo_shape_adapted,15.0,,0.6747,0.2497,12,,,,0.5524,0.6747,-0.1223,-0.3506,0.1297,0.5927,0.5513,0.6496,5.0
reports/tables/transfer_harmonized.csv:12:supercloud,lodo_shape,0.0,0.6592,0.7357,0.4782,112,-0.0765,-0.1198,-0.0356,,,,,,,,,
reports/tables/transfer_harmonized.csv:13:supercloud,lodo_shape_adapted,5.0,,0.7357,0.4782,112,,,,0.6592,0.7357,-0.0765,-0.1174,-0.0338,0.6227,0.5855,0.6592,5.0
reports/tables/transfer_harmonized.csv:14:supercloud,lodo_shape_adapted,15.0,,0.7357,0.4782,112,,,,0.6501,0.7357,-0.0856,-0.1332,-0.0419,0.6421,0.5714,0.6707,5.0
reports/review/codex_final_review_r3_2026-10-13.md:3:The round-2 implementation fixes are largely correct, and I found no discrepancies among the 268 generated values in `paper/numbers.json`, their source tables, and `paper/main.tex`. The PDF also matches the generated TeX. The remaining blocking issue is how the headline readiness result is selected and described: 48.4% versus 99.2% is a retrospective test-frontier statistic, not a validation-selected deployable operating point.
reports/review/codex_final_review_r3_2026-10-13.md:32:- **The abstract’s central 48.4% versus 99.2% result is selected using test outcomes, contrary to the methods statement.**  
reports/review/codex_final_review_r3_2026-10-13.md:35:  That conflicts with the blanket statement that “operating points are chosen on validation” and that readiness intervals are conditional on that choice at [paper/main.tex:121](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:121>). The genuinely validation-selected 90% target produces 86.775% test removal at 45.634% engaged for learned aligned, versus 99.783% at 99.159% for rhythm ([regime_targets.csv:42](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/regime_targets.csv:42>)).
reports/review/codex_final_review_r3_2026-10-13.md:63:  The point and interval exactly reproduce [regime_armed_needed.csv:3](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/regime_armed_needed.csv:3>). The statistic is a discontinuous minimum-over-thresholds functional. In my reproduction, rhythm required over 95% engagement in 84.8% of bootstrap samples, but some resampled cluster mixtures crossed 90% removal near 50–60% engagement, creating the long upper tail. The bootstrap median was about −49.3, close to the −50.8 point. This is heterogeneity/bimodality, not a sign error, but a distribution plot and more than 1000 resamples would be more informative than the percentile endpoints alone.
reports/review/codex_final_review_r3_2026-10-13.md:87:The round-2 implementation fixes are largely correct, and I found no discrepancies among the 268 generated values in `paper/numbers.json`, their source tables, and `paper/main.tex`. The PDF also matches the generated TeX. The remaining blocking issue is how the headline readiness result is selected and described: 48.4% versus 99.2% is a retrospective test-frontier statistic, not a validation-selected deployable operating point.
reports/review/codex_final_review_r3_2026-10-13.md:116:- **The abstract’s central 48.4% versus 99.2% result is selected using test outcomes, contrary to the methods statement.**  
reports/review/codex_final_review_r3_2026-10-13.md:119:  That conflicts with the blanket statement that “operating points are chosen on validation” and that readiness intervals are conditional on that choice at [paper/main.tex:121](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/paper/main.tex:121>). The genuinely validation-selected 90% target produces 86.775% test removal at 45.634% engaged for learned aligned, versus 99.783% at 99.159% for rhythm ([regime_targets.csv:42](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/regime_targets.csv:42>)).
reports/review/codex_final_review_r3_2026-10-13.md:147:  The point and interval exactly reproduce [regime_armed_needed.csv:3](</Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/regime_armed_needed.csv:3>). The statistic is a discontinuous minimum-over-thresholds functional. In my reproduction, rhythm required over 95% engagement in 84.8% of bootstrap samples, but some resampled cluster mixtures crossed 90% removal near 50–60% engagement, creating the long upper tail. The bootstrap median was about −49.3, close to the −50.8 point. This is heterogeneity/bimodality, not a sign error, but a distribution plot and more than 1000 resamples would be more informative than the percentile endpoints alone.
reports/tables/latency.csv:3:rhythm / persistence / moving-avg baselines (feature computation),6.72
reports/review/codex_peer_review_2026-10-12.md:35:  - Reported ML alarm plus LightGBM forecast: 29.823 violations/hour, 83.81% removed, 2.576% extra energy.
reports/review/codex_peer_review_2026-10-12.md:42:- **[critical] The 82% recall headline is composition-weighted and misleading.** Stable Diffusion supplies 3,247 of 4,280 test events and has 96.8% recall. The other workloads have 42.2%, 69.9%, 0%, and 24.1% recall. See [drop_warning_by_workload.csv:2](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/drop_warning_by_workload.csv:2). Excluding Stable Diffusion, event-weighted recall is approximately 37.2%. Macro recall is only 46.6%, already acknowledged in [key_numbers.json:16](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/reports/tables/key_numbers.json:16). “We can warn about drops” is not supported as a workload-general claim.
reports/review/codex_peer_review_2026-10-12.md:44:- **[critical] The effective sample size is tiny and heavily pseudoreplicated.** The 803,803 test rows reduce to 9 independent training jobs, exactly one test job per workload and node-count stratum, plus the trailing portions of only 3 continuous inference sessions. Up to four nearly lockstep nodes from each training job are scored separately. See the splitting logic in [src/load.py:192](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/load.py:192), node cap in [src/load.py:208](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/src/load.py:208), and an explicit four-node duplicate test job in [traces_meta.csv:18](/Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing/data/processed/traces_meta.csv:18). Deduplicating training events by taking one node per job reduces 4,280 events to approximately 2,736. One 6.84-hour Stable Diffusion job alone contributes 1,205 of those deduplicated events.
reports/tables/site_scaleup.csv:3:synchronized,always_burn,79.747,6.783,47382.551,3790604.072,171.84,
reports/tables/site_scaleup.csv:4:synchronized,predictive,79.747,2.576,17995.546,1439643.716,29.823,
reports/tables/regime_armed_needed.csv:3:90.0,48.39,99.16,64.29,-50.76,-57.38,-8.82,-15.89,-25.7,-3.89
reports/tables/regime_targets.csv:6:80.0,0.0,ml_aligned,73.706,2.042,35.924
reports/tables/regime_targets.csv:9:80.0,0.0,oracle,100.0,2.889,29.802
reports/tables/regime_targets.csv:15:80.0,2.0,ml_aligned,73.706,2.943,35.924
reports/tables/regime_targets.csv:17:80.0,2.0,always_on,100.0,5.443,100.0
reports/tables/regime_targets.csv:18:80.0,2.0,oracle,100.0,3.637,29.802
reports/tables/regime_targets.csv:24:80.0,5.0,ml_aligned,73.706,4.294,35.924
reports/tables/regime_targets.csv:27:80.0,5.0,oracle,100.0,4.758,29.802
reports/tables/regime_targets.csv:33:90.0,0.0,ml_aligned,86.775,2.535,45.634
reports/tables/regime_targets.csv:36:90.0,0.0,oracle,100.0,2.889,29.802
reports/tables/regime_targets.csv:42:90.0,2.0,ml_aligned,86.775,3.679,45.634
reports/tables/regime_targets.csv:43:90.0,2.0,rhythm_aligned,99.783,5.416,99.159
reports/tables/regime_targets.csv:44:90.0,2.0,always_on,100.0,5.443,100.0
reports/tables/regime_targets.csv:45:90.0,2.0,oracle,100.0,3.637,29.802
reports/tables/regime_targets.csv:49:90.0,5.0,ml_forecast,83.081,5.419,47.01
reports/tables/regime_targets.csv:51:90.0,5.0,ml_aligned,86.775,5.396,45.634
reports/tables/regime_targets.csv:54:90.0,5.0,oracle,100.0,4.758,29.802
reports/tables/regime_targets.csv:63:95.0,0.0,oracle,100.0,2.889,29.802
reports/tables/regime_targets.csv:70:95.0,2.0,rhythm_aligned,99.783,5.416,99.159
reports/tables/regime_targets.csv:71:95.0,2.0,always_on,100.0,5.443,100.0
reports/tables/regime_targets.csv:72:95.0,2.0,oracle,100.0,3.637,29.802
reports/tables/regime_targets.csv:81:95.0,5.0,oracle,100.0,4.758,29.802
reports/tables/crossdata_ap_harmonized.csv:28:lodo,supercloud,sc_unet,0.646,0.6908,0.5309,16,-0.0448,-0.1207,0.0089
reports/tables/crossdata_ap_harmonized.csv:29:lodo,supercloud,sc_vgg,0.6457,0.6695,0.4886,16,-0.0238,-0.0836,0.0228
reports/tables/crossdata_ap_harmonized.csv:34:pooled,elsayed,elsayed_diffusion,0.6553,0.8341,0.3171,2,-0.1788,-0.4887,-0.161
reports/tables/crossdata_ap_harmonized.csv:38:pooled,supercloud,sc_distilbert,0.7289,0.0996,0.075,16,0.6293,0.239,0.7187
reports/tables/forecast_overall.csv:12:lightgbm,5,69.60932312314247,240.1832847005652,6.860822110952855
reports/tables/crossdata_readiness_raw.csv:4:in_domain,nlr,learned,95.0,True,95.499,50.282
reports/tables/crossdata_readiness_raw.csv:5:in_domain,nlr,rhythm,80.0,True,73.779,35.902
reports/tables/crossdata_readiness_raw.csv:23:lodo,nlr,rhythm,80.0,True,73.779,35.902
reports/tables/crossdata_readiness_raw.csv:41:pooled,nlr,rhythm,80.0,True,73.779,35.902
reports/tables/crossdata_readiness_raw.csv:46:pooled,elsayed,learned,95.0,True,95.448,82.547
reports/tables/drop_warning_by_workload.csv:5:train_llama2_70b_lora,0.7312716186240797,315,0.24126984126984127,4.439473684210526,112,0.7142857142857143,3.021052962834754,0.8629821531375935,0.19034920634920635,0.3119017894298793,0.4417390037178177
reports/tables/regime_ml_vs_rhythm_ci.csv:6:0.0,0.0,0.2,ml_alarm-rhythm_alarm,overhead_pct,0.644,0.171,1.212
reports/tables/regime_ml_vs_rhythm_ci.csv:10:0.0,0.0,0.5,ml_alarm-rhythm_alarm,overhead_pct,0.653,0.204,1.264
reports/tables/regime_ml_vs_rhythm_ci.csv:22:0.0,0.0,3.0,ml_alarm-rhythm_alarm,overhead_pct,0.655,0.2,1.239
reports/tables/regime_ml_vs_rhythm_ci.csv:25:0.0,0.0,3.0,ml_aligned-rhythm_aligned,cut_pct,-4.801,-15.462,1.691
reports/tables/regime_ml_vs_rhythm_ci.csv:63:0.0,1.0,1.0,ml_alarm-rhythm_alarm,cut_pct,13.682,-8.022,36.81
reports/tables/regime_ml_vs_rhythm_ci.csv:75:0.0,2.0,0.0,ml_alarm-rhythm_alarm,cut_pct,13.827,-6.821,38.254
reports/tables/regime_ml_vs_rhythm_ci.csv:99:0.0,5.0,0.0,ml_alarm-rhythm_alarm,cut_pct,13.827,-6.812,37.941
reports/tables/regime_ml_vs_rhythm_ci.csv:108:0.0,5.0,0.5,ml_aligned-rhythm_aligned,overhead_pct,-0.711,-1.206,-0.331
reports/tables/regime_ml_vs_rhythm_ci.csv:110:0.0,5.0,1.0,ml_alarm-rhythm_alarm,overhead_pct,1.945,0.456,3.781
reports/tables/regime_ml_vs_rhythm_ci.csv:114:0.0,5.0,2.0,ml_alarm-rhythm_alarm,overhead_pct,1.973,0.414,3.755
reports/tables/regime_ml_vs_rhythm_ci.csv:120:0.0,5.0,3.0,ml_aligned-rhythm_aligned,overhead_pct,-0.717,-1.152,-0.357
reports/tables/regime_ml_vs_rhythm_ci.csv:122:0.0,10.0,0.0,ml_alarm-rhythm_alarm,overhead_pct,3.251,0.712,6.185
reports/tables/regime_ml_vs_rhythm_ci.csv:126:0.0,10.0,0.2,ml_alarm-rhythm_alarm,overhead_pct,3.253,0.646,6.421
reports/tables/regime_ml_vs_rhythm_ci.csv:138:0.0,10.0,2.0,ml_alarm-rhythm_alarm,overhead_pct,3.274,0.717,6.5
reports/tables/regime_ml_vs_rhythm_ci.csv:178:2.0,0.5,0.5,ml_alarm-rhythm_alarm,overhead_pct,-0.028,-0.36,0.645
reports/tables/regime_ml_vs_rhythm_ci.csv:182:2.0,0.5,1.0,ml_alarm-rhythm_alarm,overhead_pct,-0.005,-0.33,0.712
reports/tables/regime_ml_vs_rhythm_ci.csv:190:2.0,0.5,3.0,ml_alarm-rhythm_alarm,overhead_pct,-0.03,-0.373,0.647
reports/tables/regime_ml_vs_rhythm_ci.csv:193:2.0,0.5,3.0,ml_aligned-rhythm_aligned,cut_pct,16.149,6.711,30.677
reports/tables/regime_ml_vs_rhythm_ci.csv:200:2.0,1.0,0.2,ml_aligned-rhythm_aligned,overhead_pct,-0.281,-0.887,0.649
reports/tables/regime_ml_vs_rhythm_ci.csv:216:2.0,1.0,3.0,ml_aligned-rhythm_aligned,overhead_pct,-0.275,-0.887,0.656
reports/tables/regime_ml_vs_rhythm_ci.csv:236:2.0,2.0,2.0,ml_aligned-rhythm_aligned,overhead_pct,3.77,0.902,5.985
reports/tables/regime_ml_vs_rhythm_ci.csv:264:2.0,5.0,3.0,ml_aligned-rhythm_aligned,overhead_pct,-0.457,-1.631,0.717
reports/tables/regime_ml_vs_rhythm_ci.csv:283:2.0,10.0,2.0,ml_alarm-rhythm_alarm,cut_pct,13.454,-6.882,39.416
reports/tables/regime_ml_vs_rhythm_ci.csv:285:2.0,10.0,2.0,ml_aligned-rhythm_aligned,cut_pct,-0.217,-7.268,6.745
reports/tables/regime_ml_vs_rhythm_ci.csv:410:10.0,10.0,0.0,ml_alarm-rhythm_alarm,overhead_pct,0.714,-1.125,4.331
reports/tables/regime_ml_vs_rhythm_ci.csv:414:10.0,10.0,0.2,ml_alarm-rhythm_alarm,overhead_pct,0.715,-1.017,4.282
reports/tables/regime_pareto_test.csv:2:always_burn,,,7750.0,8310,24589687.5628,362538781.2864,0.0,45.1002,0.0,6.7389,6.7826,0.0,0.0
reports/tables/regime_pareto_test.csv:9:ml_alarm,0.0,0.0053,101.0,8310,10547769.1168,362538781.2864,140929.4,45.1002,1908.0,98.7846,2.9094,86.8002,42.3058
reports/tables/regime_pareto_test.csv:19:ml_alarm,0.0,0.3993,4174.0,8310,8055206.7334,362538781.2864,45261.8,45.1002,3987.0,49.7714,2.2219,27.8773,88.4032
reports/tables/regime_pareto_test.csv:20:ml_alarm,0.0,0.5499,4433.0,8310,7711013.6324,362538781.2864,41471.4,45.1002,3776.0,46.6546,2.1269,25.5428,83.7247
reports/tables/regime_pareto_test.csv:21:ml_alarm,0.0,0.7352,4650.0,8310,7308675.9445,362538781.2864,38615.6,45.1002,3565.0,44.0433,2.016,23.7838,79.0463
reports/tables/regime_pareto_test.csv:22:ml_alarm,0.0,0.901,4941.0,8310,6518356.8923,362538781.2864,35602.8,45.1002,3319.0,40.5415,1.798,21.9282,73.5917
reports/tables/regime_pareto_test.csv:26:ml_alarm,0.0,0.9991,5315.0,8310,5542576.7501,362538781.2864,28753.6,45.1002,2974.0,36.0409,1.5288,17.7097,65.9421
reports/tables/regime_pareto_test.csv:30:ml_alarm,0.0,0.9995,5412.0,8310,5306110.7135,362538781.2864,26473.2,45.1002,2878.0,34.8736,1.4636,16.3052,63.8135
reports/tables/regime_pareto_test.csv:31:ml_alarm,0.0,0.9996,5433.0,8310,5266699.3293,362538781.2864,25878.0,45.1002,2857.0,34.6209,1.4527,15.9386,63.3479
reports/tables/regime_pareto_test.csv:34:ml_alarm,0.0,0.9997,5508.0,8310,5123440.2259,362538781.2864,23552.0,45.1002,2785.0,33.7184,1.4132,14.506,61.7514
reports/tables/regime_pareto_test.csv:42:ml_alarm,0.2,0.0004,18.0,8310,10618710.475,362538781.2864,157995.4,45.1002,353.0,99.7834,2.929,97.3114,7.827
reports/tables/regime_pareto_test.csv:45:ml_alarm,0.2,0.0053,106.0,8310,10545762.5687,362538781.2864,140903.2,45.1002,1908.0,98.7244,2.9089,86.7841,42.3058
reports/tables/regime_pareto_test.csv:54:ml_alarm,0.2,0.2899,3895.0,8310,8308372.7775,362538781.2864,49771.6,45.1002,4198.0,53.1288,2.2917,30.655,93.0817
reports/tables/regime_pareto_test.csv:56:ml_alarm,0.2,0.5499,4449.0,8310,7705996.2957,362538781.2864,41434.8,45.1002,3776.0,46.4621,2.1256,25.5202,83.7247
reports/tables/regime_pareto_test.csv:57:ml_alarm,0.2,0.7352,4663.0,8310,7304789.0817,362538781.2864,38581.8,45.1002,3565.0,43.8869,2.0149,23.763,79.0463
reports/tables/regime_pareto_test.csv:67:ml_alarm,0.2,0.9996,5433.0,8310,5266738.5853,362538781.2864,25876.4,45.1002,2857.0,34.6209,1.4527,15.9376,63.3479
reports/tables/regime_pareto_test.csv:70:ml_alarm,0.2,0.9997,5508.0,8310,5123485.5791,362538781.2864,23550.2,45.1002,2785.0,33.7184,1.4132,14.5049,61.7514
reports/tables/regime_pareto_test.csv:81:ml_alarm,0.5,0.0053,112.0,8310,10543896.4084,362538781.2864,140880.8,45.1002,1909.0,98.6522,2.9083,86.7703,42.328
reports/tables/regime_pareto_test.csv:92:ml_alarm,0.5,0.5499,4455.0,8310,7698473.3305,362538781.2864,41410.6,45.1002,3776.0,46.3899,2.1235,25.5053,83.7247
reports/tables/regime_pareto_test.csv:93:ml_alarm,0.5,0.7352,4672.0,8310,7295126.576,362538781.2864,38549.0,45.1002,3565.0,43.7786,2.0122,23.7428,79.0463
reports/tables/regime_pareto_test.csv:95:ml_alarm,0.5,0.9886,5169.0,8310,5956359.3787,362538781.2864,32735.4,45.1002,3110.0,37.7978,1.643,20.1622,68.9576
reports/tables/regime_pareto_test.csv:97:ml_alarm,0.5,0.9988,5288.0,8310,5630935.4929,362538781.2864,29666.6,45.1002,2997.0,36.3658,1.5532,18.272,66.4521
reports/tables/regime_pareto_test.csv:103:ml_alarm,0.5,0.9996,5434.0,8310,5266424.7139,362538781.2864,25874.0,45.1002,2857.0,34.6089,1.4527,15.9361,63.3479
reports/tables/regime_pareto_test.csv:106:ml_alarm,0.5,0.9997,5509.0,8310,5123173.1417,362538781.2864,23548.2,45.1002,2785.0,33.7064,1.4131,14.5036,61.7514
reports/tables/regime_pareto_test.csv:116:ml_alarm,1.0,0.0001,18.0,8310,10618710.475,362538781.2864,160885.4,45.1002,53.0,99.7834,2.929,99.0914,1.1752
reports/tables/regime_pareto_test.csv:128:ml_alarm,1.0,0.0002,18.0,8310,10618710.475,362538781.2864,160136.8,45.1002,148.0,99.7834,2.929,98.6303,3.2816
reports/tables/regime_pareto_test.csv:134:ml_alarm,1.0,0.0003,18.0,8310,10618710.475,362538781.2864,159430.2,45.1002,247.0,99.7834,2.929,98.1951,5.4767
reports/tables/regime_pareto_test.csv:137:ml_alarm,1.0,0.0003,18.0,8310,10618710.475,362538781.2864,158945.6,45.1002,290.0,99.7834,2.929,97.8967,6.4301
reports/tables/regime_pareto_test.csv:146:ml_alarm,1.0,0.0005,18.0,8310,10618710.475,362538781.2864,157127.0,45.1002,398.0,99.7834,2.929,96.7766,8.8248
reports/tables/regime_pareto_test.csv:149:ml_alarm,1.0,0.0006,18.0,8310,10618710.475,362538781.2864,156475.4,45.1002,406.0,99.7834,2.929,96.3752,9.0022
reports/tables/regime_pareto_test.csv:156:ml_alarm,1.0,0.0009,18.0,8310,10618652.3438,362538781.2864,155030.6,45.1002,422.0,99.7834,2.929,95.4854,9.3569
reports/tables/regime_pareto_test.csv:158:ml_alarm,1.0,0.0011,18.0,8310,10618626.813,362538781.2864,154701.2,45.1002,429.0,99.7834,2.929,95.2825,9.5122
reports/tables/regime_pareto_test.csv:162:ml_alarm,1.0,0.0013,18.0,8310,10618585.4774,362538781.2864,154104.6,45.1002,450.0,99.7834,2.929,94.915,9.9778

--- git status / generation mapping ---
?? paper/PESGM2027_SUBMISSION.md
?? reports/review/pesgm_codex_r1_2026-11-09.md
1:"""Build the paper draft (paper/main.tex + figures) from the result tables, so every number in the text
4:    python -m src.paper            # writes paper/main.tex, paper/fig_*.pdf, paper/numbers.json
5:    tectonic paper/main.tex        # builds paper/main.pdf (if tectonic is installed)
7:Placeholders in the template look like <<name>> and are filled from numbers.json.
26:OUT = ROOT / "paper"
54:    # matched label ablation (src/ablation.py): big-drop label through the exact aligned pipeline
55:    ab = json.load(open(PROC_DIR / "ablation_info.json"))
56:    for k in ("matched_aligned_ap", "matched_drop_ap", "matched_diff", "matched_diff_lo", "matched_diff_hi",
57:              "matched_drop_ap_on_drop_label", "matched_aligned_ap_on_drop_label"):
87:    an = pd.read_csv(TABLES / "regime_armed_needed.csv").set_index("target")
134:    json.dump(out, open(OUT / "numbers.json", "w"), indent=1)
229:    fill(OUT / "template.tex", OUT / "main.tex", nums)
232:    if (arx / "template.tex").exists():
235:        fill(arx / "template.tex", arx / "main.tex", nums)
239:    """Replace every <<name>> in the template with its number; fail loudly on any missing name."""
245:    print(f"paper: wrote {out_path} with {len(nums)} numbers")

exec
/bin/zsh -lc 'tmpdir=$(mktemp -d); pdftoppm -f 3 -singlefile -png -r 180 paper/main.pdf "$tmpdir/page3" >/dev/null 2>&1; printf '"'%s\\n' \""'$tmpdir/page3.png"' in /Users/sayedraheel/Desktop/Research_and_Books/Sapient/powerswing
 succeeded in 0ms:
mktemp: mkdtemp failed on /var/folders/9h/r99pdx1j64ngx3rfbtkbvc8r0000gn/T/tmp.HcPl2tdsHy: Operation not permitted
/page3.png

2026-11-09T23:19:30.995124Z ERROR codex_core::tools::router: error=unable to process image: invalid or unsupported image data
codex
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
