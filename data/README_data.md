# Data: NLR "Dataset of Generative AI Workload Power Profiles"

Source: NLR (formerly NREL) Data Catalog, submission 312, CC BY 4.0.
Download: https://data.nlr.gov/system/files/312/1775845072-dataset.zip (1.07 GB zipped, 2.9 GB unzipped, 3,191 files).
Paper: Vercellino et al., "Measurement of Generative AI Workload Power Profiles for Whole-Facility Data Center Infrastructure Planning", arXiv:2604.07345.
System: NLR Kestrel HPC, GPU nodes with 4 x NVIDIA H100 each (plus 2 CPU sockets, 128 cores).
Measured with the WattAMeter tool. Collected September 2025 to January 2026.

The ZIP is extracted to `data/raw/nlr/`. It also contains a `.git/` folder, a `.activate.sh` pointing at the
authors' cluster paths and the authors' own scripts. None of those are executed by this project.

## Folder layout

| Folder | What it holds |
|---|---|
| `00_raw_datasets/` | Original per-device logs. `nvml_*` = GPU, `rapl_*` = CPU. This project uses **only the NVML (GPU) logs**. |
| `01_aggregated_datasets/` | The authors' resampled parquet files plus `metadata.csv` and `postprocess.py` per workload. Training parquet files sum **GPU + CPU** over all nodes, so they are not used for modelling (we rebuild GPU-only traces from raw). Their metadata is used for documentation. |
| `02_analysis_scripts/` | Authors' notebooks and plots from the paper. Not used. |
| `03_whole-facility_profiles/` | **Simulated** (not measured) facility profiles from NLR's DIPLOEE tool: 1 MW inference (283 nodes) and 10 MW colocation (2,840 nodes) at 20/40/60/80% utilisation. Not used for training or testing, because they are synthetic. |

## Raw GPU log format (`nvml_wattameter_*.log`)

Whitespace-separated text, `#` comment lines at the top. Columns:

| Column | Unit | Notes |
|---|---|---|
| `timestamp` | `YYYY-MM-DD_HH:MM:SS.ffffff` | wall clock, local to the cluster |
| `reading-time[ns]` | ns | time the NVML read took |
| `gpu-0[mW]` ... `gpu-3[mW]` | milliwatts | instantaneous board power per H100 |
| `gpu-0[C]` ... `gpu-3[C]` | deg C | GPU temperature (present, not used) |

CPU logs (`rapl_*`) hold cumulative energy (uJ) and power (W) per CPU socket and core domain. Not used here.

## Workloads

| Workload | Folder | Nodes | Jobs / runs | Native rate | Duration | Notes |
|---|---|---|---|---|---|---|
| Llama2-70B LoRA fine-tuning | `training_llama2_70b_lora/{2,4,8,16}node` | 2, 4, 8, 16 | 5, 5, 6, 5 jobs | 5 Hz (0.2 s) | 25 to 60 min per job | one log per node per job |
| Stable Diffusion training | `training_stable_diffusion/{1,2,4,8,16}node` | 1, 2, 4, 8, 16 | 5, 6, 5, 5, 4 jobs | 5 Hz | 25 min to 7 h | the 1-node jobs are in raw only, not in the authors' aggregated set |
| Llama3.1-70B offline inference (vLLM) | `inference_offline_llama3_70b` | 1 | 1,200 runs, one 14 h log | 10 Hz (0.1 s) | runs 10 to 97 s | 40 batch sizes (25 to 1000) x max output tokens {512, 1024}, separated by short pauses |
| Llama3.1-70B online, finite requests | `inference_online_finite_llama3_70b` | 1 | 1,026 runs, one 20 h log | 10 Hz | runs ~36 s | InstructCoder prompts, 1,000 prompts per run, request rate 10 to 1000 req/s, output length 256 to 1024 |
| Llama3.1-70B online, fixed rate | `inference_online_rate_llama3_70b` | 1 | 200 runs, one 18 h log | 10 Hz | 180 s each | request rate 1 to 100 req/s |

Per-run inference metadata (batch size, request rate, throughput, TTFT, TPOT, peak/mean power) is in
`01_aggregated_datasets/*/metadata.csv` and the raw `log.json` / `vllm_bench.log` files.

Not in the dataset: job crash events, checkpoint timestamps, step/iteration markers, communication phase
labels, power-cap settings, facility-level (PDU or meter) power, or any non-H100 hardware. Phases visible in
the traces (compute, pauses, evaluation) are inferred from the power shape only.

## What our loader (`src/load.py`) produces

`data/processed/traces.parquet`, one row per sample:

| Column | Meaning |
|---|---|
| `trace_id` | one node of one training job, or one 1-hour block of an inference session |
| `t_s` | seconds since trace start, uniform 0.2 s grid (5 Hz) |
| `power_w` | node GPU power = sum of the 4 H100s, watts |
| `gpu0_w` ... `gpu3_w` | per-GPU power, watts |
| `timestamp` | wall-clock time of the grid point |

`data/processed/traces_meta.csv`: `workload, phase, model, node_count, job_id, node, duration_s, split, use_for_model`.
`data/processed/jobs.parquet`: job-level GPU power summed over every node of a training job.

Cleaning steps:
1. Per-GPU readings above 800 W or below 0 W are treated as sensor errors (same rule as the dataset authors) and set to missing.
2. Each log is averaged onto a uniform 0.2 s grid (inference 10 Hz is averaged down to 5 Hz so all traces share one rate).
3. Gaps up to 2 s are forward-filled (the last reading is held, so no future data leaks in). No gap longer than 1 s exists in any GPU log, so nothing was dropped for gaps.
4. Nodes of the same training job are put on a common time origin so they can be summed into a job total.
5. Inference sessions are cut into 1-hour blocks (a short tail block under 30 min is dropped).

Totals: 470 node-traces, 6.09 million samples, about 338 node-hours.

## Splits (no leakage)

- Training workloads: whole **jobs** are assigned to train / val / test (about 60/20/20), stratified by model and node count, seed 42. All nodes of a job stay together.
- Inference workloads: one continuous session each, split **in time**: first 60% of hourly blocks train, next 20% val, last 20% test.
- Nodes within a training job are nearly identical (see `reports/figures/eda_single_vs_multinode.png`), so modelling uses at most 4 nodes per job (`use_for_model`). EDA uses all nodes.
- Generalisation tests additionally hold out a whole workload type from training (see `reports/results.md`).

## Big-drop events (`src/events.py`)

Definition: at time t, power falls by more than 30% of the recent peak (max over the previous 10 s) within the next 1 s, while the recent peak is at least 1 kW per node (the node idles near 300 W). One drop per 5 s refractory window.

| Workload | Node-hours | Drops | Per node-hour | Median size | Size % of peak | Median time to bottom | Median duration (to half recovery) | Median steepest fall |
|---|---|---|---|---|---|---|---|---|
| Train Llama2-70B LoRA | 111.3 | 3,590 | 32 | 1.0 kW | 37% | 1.2 s | 5.2 s | 1.8 kW/s |
| Train Stable Diffusion | 175.2 | 20,745 | 118 | 2.1 kW | 75% | 1.6 s | 2.4 s | 2.2 kW/s |
| Infer offline batch | 14.0 | 1,588 | 113 | 2.0 kW | 75% | 2.4 s | 3.0 s | 2.1 kW/s |
| Infer online (finite) | 19.9 | 1,185 | 60 | 1.4 kW | 64% | 5.0 s | 30.8 s | 1.5 kW/s |
| Infer online (rate) | 17.9 | 432 | 24 | 1.4 kW | 56% | 3.8 s | 4.4 s | 2.1 kW/s |

(Steepest fall is the largest single 0.2 s step, expressed in W/s, per 4-GPU node. The 5 Hz sampling caps how steep a
measured ramp can look, so true ramps are likely faster.)

Things to know about these events:
- **Llama2 LoRA training** runs a steady ~12 s square wave between about 2.75 kW and 2.15 kW per node (a ~22% swing). That regular swing is *below* the 30% threshold, so most of its counted drops are the occasional deeper dips to ~1.8 kW and job start/end.
- **Stable Diffusion training** has long flat ~2.2 kW stretches, then phases at ~2.75 kW that plunge to ~650 W every ~12 s. Those phases produce most of its drops.
- **Inference** drops are dominated by the GPU going idle between benchmark runs (the harness starts a new run every 10 to 180 s). They are real power swings but are shaped by how the benchmark was scripted.
- **Multi-node jobs move in lockstep**: every node of a job swings at the same moment, so a 16-node job's total swing is ~16x a single node's. This is the synchronised worst case for the grid.
- Drop rate per node-hour falls with node count for Stable Diffusion (175 at 1 node to 42 at 16 nodes) and rises for Llama2 LoRA (11 to 49): `data/processed/drop_rate_by_nodes.csv`.
