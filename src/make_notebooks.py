"""Generate the three walkthrough notebooks (kept as code so they stay in sync with src/)."""
from __future__ import annotations

import nbformat as nbf

from src.config import ROOT

SETUP = """import os, sys, warnings
warnings.filterwarnings("ignore")
# make `src` importable whether the notebook runs from notebooks/ or the repo root
ROOT = os.path.abspath(".." if os.path.basename(os.getcwd()) == "notebooks" else ".")
sys.path.insert(0, ROOT); os.chdir(ROOT)
import pandas as pd, numpy as np
from IPython.display import Image, display, Markdown
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 30)"""


def nb(cells: list[tuple[str, str]]) -> nbf.NotebookNode:
    n = nbf.v4.new_notebook()
    n.cells = [nbf.v4.new_markdown_cell(c) if k == "md" else nbf.v4.new_code_cell(c) for k, c in cells]
    n.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    return n


EXPLORE = [
    ("md", "# 01 Explore: H100 power traces and big drops\nLoads the NLR GenAI power-profile dataset, "
           "shows example traces and characterises big-drop events. See `data/README_data.md` for the full data description."),
    ("code", SETUP),
    ("code", "from src.load import load_traces\ntraces, meta = load_traces()\nprint(len(traces), 'samples in', len(meta), 'node-traces')\n"
             "meta.groupby(['workload', 'node_count', 'split']).size().unstack(fill_value=0)"),
    ("md", "## Example traces\nEach trace is one 4-GPU node, sampled at 5 Hz. Red markers are detected big drops "
           "(power falls by more than 30% of the 10 s peak within 1 s)."),
    ("code", "from src import explore\nsumm = explore.run()\ndisplay(Image('reports/figures/eda_sample_traces.png'))"),
    ("md", "## Single node vs whole multi-node job\nAll nodes of a training job swing at the same instant, so the job total is a scaled copy of one node."),
    ("code", "display(Image('reports/figures/eda_single_vs_multinode.png'))"),
    ("md", "## Big-drop statistics by workload"),
    ("code", "display(summ)\ndisplay(Image('reports/figures/eda_drop_stats.png'))"),
    ("code", "pd.read_csv('data/processed/drop_rate_by_nodes.csv')"),
]

MODELS = [
    ("md", "# 02 Models: forecasting and drop warning\nRuns features, baselines, LightGBM, the tiny TCN and the zero-shot "
           "foundation models, then evaluates on held-out test jobs. Set `RETRAIN = False` to only display the cached results "
           "written by `python -m src.run_all` (full retraining takes about 25 minutes on a laptop)."),
    ("code", SETUP + "\nRETRAIN = False"),
    ("code", "from src import modeling, generalize\nif RETRAIN:\n    modeling.run()\n    generalize.run()"),
    ("md", "## Forecast error (all test traces)"),
    ("code", "ft = pd.read_csv('reports/tables/forecast_overall.csv')\nft.pivot(index='model', columns='horizon_s', values='MAE').round(1)"),
    ("code", "display(Image('reports/figures/model_comparison_5s.png'))\ndisplay(Image('reports/figures/error_by_horizon.png'))"),
    ("md", "## By workload (MAE, W per node)"),
    ("code", "fw = pd.read_csv('reports/tables/forecast_by_workload.csv')\nfw[fw.horizon_s == 5].pivot(index='workload', columns='model', values='MAE').round(0)"),
    ("md", "## Including zero-shot foundation models (stratified sample of test points)"),
    ("code", "fs = pd.read_csv('reports/tables/forecast_subset_with_chronos.csv')\ndisplay(fs.pivot(index='model', columns='horizon_s', values='MAE').round(1))\n"
             "display(Image('reports/figures/model_comparison_5s_with_chronos.png'))"),
    ("md", "## Drop warning (will a big drop start within 5 s?)"),
    ("code", "display(pd.read_csv('reports/tables/drop_warning.csv').round(3))\ndisplay(pd.read_csv('reports/tables/drop_warning_by_workload.csv').round(3))\n"
             "display(Image('reports/figures/drop_warning_pr_curve.png'))"),
    ("md", "## Actual vs predicted on example windows"),
    ("code", "display(Image('reports/figures/forecast_overlays_5s.png'))"),
    ("md", "## Generalisation to unseen workload types (LightGBM retrained without that workload)"),
    ("code", "pd.read_csv('reports/tables/generalization_lowo.csv').round(2)"),
    ("md", "## Inference latency on CPU (single prediction, 1 thread)"),
    ("code", "pd.read_csv('reports/tables/latency.csv')"),
]

SIM = [
    ("md", "# 03 Smoothing simulation: what the predictions are worth\nCompares no smoothing, always-burn, and "
           "model-armed predictive smoothing on the test traces, then scales to a 100 MW site. "
           "Change the parameters in `SimParams` to explore other grid limits, floors or actuator latencies."),
    ("code", SETUP),
    ("code", "from src.simulate import SimParams, run\nsp = SimParams()  # e.g. SimParams(ramp_limit_frac_per_s=0.05, actuator_latency_s=2.0)\nsp"),
    ("code", "res = run(sp)\nres['summary'].round(2)"),
    ("md", "## Before / after on example windows"),
    ("code", "display(Image('reports/figures/smoothing_before_after.png'))"),
    ("md", "## By workload"),
    ("code", "res['by_workload'].pivot(index='workload', columns='strategy', values='down_violations_per_node_hour').round(1)"),
    ("md", "## 100 MW site, yearly cost of the extra energy at $80/MWh"),
    ("code", "display(res['site'].round(2))\ndisplay(Image('reports/figures/site_scaleup.png'))"),
    ("md", "## Sensitivity: actuator latency\nPrediction only matters if the fill or storage cannot react instantly."),
    ("code", "rows = []\nfor lat in [0.2, 0.5, 1.0, 2.0, 3.0]:\n    r = run(SimParams(actuator_latency_s=lat), log=lambda *_: None)['summary']\n"
             "    rows.append({'latency_s': lat, **{f'{s}_cut_%': r.loc[s, 'down_violation_cut_pct'] for s in ['predictive', 'reactive', 'always_on_limiter']},\n"
             "                 'predictive_energy_%': r.loc['predictive', 'extra_energy_pct']})\nrun(sp, log=lambda *_: None)  # restore default outputs\npd.DataFrame(rows).round(1)"),
]


def main(force: bool = False) -> None:
    """Write the notebooks. Existing (possibly executed) notebooks are kept unless force=True."""
    out = ROOT / "notebooks"
    out.mkdir(exist_ok=True)
    for name, cells in [("01_explore.ipynb", EXPLORE), ("02_models.ipynb", MODELS), ("03_simulation.ipynb", SIM)]:
        if force or not (out / name).exists():
            nbf.write(nb(cells), out / name)


if __name__ == "__main__":
    main(force=True)
