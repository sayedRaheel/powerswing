# powerswing: predicting AI data-center power swings

> **IEEE copyright notice:** This work has been submitted to the IEEE for possible publication (IEEE PES General Meeting 2027). Copyright may be transferred without notice, after which this version may no longer be accessible.


Proof of concept: can machine learning predict GPU power swings in AI workloads seconds ahead, better than simple
rules, and how much grid smoothing does that buy?

Data: NLR (formerly NREL) "Dataset of Generative AI Workload Power Profiles", H100 GPUs on the Kestrel HPC system,
CC BY 4.0 ([data](https://data.nlr.gov/submissions/312), [paper](https://arxiv.org/abs/2604.07345)).

**Read the results first: [`reports/results.md`](reports/results.md)** (plain-English summary, key numbers, charts,
limitations, next steps). One-slide summary: `reports/figures/summary_slide.png`.

## Quick start

```bash
# macOS only: LightGBM needs the OpenMP runtime
brew install libomp

uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt

# downloads nothing by itself: put the ZIP at data/raw/dataset.zip first
curl -L -A "Mozilla/5.0" -o data/raw/dataset.zip https://data.nlr.gov/system/files/312/1775845072-dataset.zip

.venv/bin/python -m src.run_all     # about 35 to 45 minutes on an Apple-silicon laptop
```

The first run of the zero-shot models downloads `amazon/chronos-bolt-small` and `google/timesfm-2.5-200m-pytorch`
from the Hugging Face Hub. If that fails, the pipeline skips them and carries on.

## Layout

```
data/raw/                 dataset ZIP + extracted files (not committed)
data/processed/           clean traces, feature tables, predictions, model files (not committed)
data/README_data.md       what is in the dataset: files, columns, units, workloads, splits, drop statistics
src/
  config.py               paths, constants, seeds
  load.py                 raw NVML logs -> uniform 5 Hz per-node traces, job totals, leakage-free splits
  events.py               big-drop detection and characterisation
  explore.py              Step 2 figures and drop statistics
  features.py             causal features (lags, rolling stats, slopes, step timers, rhythm/FFT phase) + targets
  baselines.py            persistence, moving average, rhythm repeat (autocorrelation), rhythm alarm
  models.py               LightGBM forecasters and drop classifier
  nets.py                 tiny TCN (46k params) + zero-shot Chronos-Bolt-Small and TimesFM 2.5 (PyTorch)
  evaluate.py             metrics (MAE/RMSE/MAPE, event recall with lead time, false alarms/hour) and charts
  modeling.py             Steps 3 to 6 orchestration
  generalize.py           leave-one-workload-out test
  simulate.py             Step 7 smoothing strategies + 100 MW scale-up
  report.py               writes reports/results.md and the summary slide
  make_notebooks.py       regenerates the notebooks
  run_all.py              one command for everything
notebooks/                01_explore, 02_models, 03_simulation (run top to bottom)
reports/results.md        the write-up
reports/figures/          all charts
reports/tables/           every number in the write-up as CSV
```

## Design notes

- **No leakage.** Training jobs are split whole (all nodes of a job in one split); inference sessions are split in
  time. Every feature at time t uses only data up to t. A drop only counts as "caught" if the warning was on at
  least 1 s before it started.
- **Reproducible.** Fixed seed 42 everywhere; LightGBM runs in deterministic mode. The TCN trains on the Apple GPU
  (MPS) when available, which is not bit-for-bit deterministic; expect tiny run-to-run differences in TCN numbers.
- **Two processes.** PyTorch and LightGBM ship different OpenMP runtimes that crash when loaded together on macOS,
  so `modeling.py` runs `nets.py` in a child process.
- **Smoothing is simulated.** All parameters (grid ramp limit, burn floor, actuator latency, price) live in
  `SimParams` in `src/simulate.py`; notebook 03 shows how to change them and includes an actuator-latency sweep.

## Useful commands

```bash
.venv/bin/python -m src.load                  # rebuild clean traces only
.venv/bin/python -m src.explore               # Step 2 figures
.venv/bin/python -m src.modeling --reuse-nets # re-evaluate without retraining the PyTorch models
.venv/bin/python -m src.simulate              # smoothing simulation only
.venv/bin/python -m src.report                # regenerate results.md + slide from saved tables
```
