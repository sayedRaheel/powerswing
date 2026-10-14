"""One command for the whole pipeline: `python -m src.run_all`.

Stages: load + clean -> explore -> features/baselines/models/evaluation -> generalisation ->
smoothing simulation -> report (results.md + summary slide).
"""
from __future__ import annotations

import time
import warnings

from src.config import ensure_dirs, seed_everything


def main(reuse_nets: bool = False) -> None:
    warnings.filterwarnings("ignore")
    seed_everything()
    ensure_dirs()
    t0 = time.time()

    def log(msg: str) -> None:
        print(f"[{time.time() - t0:7.0f}s] {msg}", flush=True)

    from src import explore, generalize, load, make_notebooks, modeling, report, simulate

    log("Step 1-2: loading raw logs and building clean traces")
    load.build_processed()
    log("Step 2: exploration figures and drop statistics")
    explore.run()
    log("Steps 3-6: features, baselines, LightGBM, TCN, Chronos, evaluation")
    modeling.run(log=log, reuse_nets=reuse_nets)
    log("Step 3: held-out workload generalisation")
    generalize.run(log=log)
    log("Step 7: smoothing simulation and 100 MW scale-up")
    simulate.run(log=log)
    log("Step 8: report and summary slide")
    report.run()
    make_notebooks.main()
    log("done: see reports/results.md and reports/figures/summary_slide.png")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Run the full power-swing pipeline.")
    ap.add_argument("--reuse-nets", action="store_true",
                    help="reuse cached TCN/Chronos/TimesFM outputs instead of retraining (saves ~18 min)")
    main(reuse_nets=ap.parse_args().reuse_nets)
