"""Shared paths, constants and seeding for the power-swing POC."""
from __future__ import annotations

import os
import random
from pathlib import Path

import numpy as np

ROOT: Path = Path(__file__).resolve().parent.parent
RAW_DIR: Path = ROOT / "data" / "raw"
NLR_DIR: Path = RAW_DIR / "nlr"
ZIP_PATH: Path = RAW_DIR / "dataset.zip"
PROC_DIR: Path = ROOT / "data" / "processed"
FIG_DIR: Path = ROOT / "reports" / "figures"
REPORT_DIR: Path = ROOT / "reports"

SEED: int = 42

# Uniform analysis rate. Training logs are 5 Hz natively, inference logs are 10 Hz
# and get averaged down to 5 Hz so every trace shares one grid.
FS_HZ: float = 5.0
DT_S: float = 1.0 / FS_HZ

# Forecast horizons (seconds) and the drop-warning window.
HORIZONS_S: tuple[int, ...] = (1, 5, 10)
WARN_WINDOW_S: float = 5.0

# Big-drop definition: power falls by more than DROP_FRAC of the recent peak within DROP_WINDOW_S.
DROP_FRAC: float = 0.30
DROP_WINDOW_S: float = 1.0
PEAK_LOOKBACK_S: float = 10.0
REFRACTORY_S: float = 5.0  # a new drop cannot start within this many seconds of the previous one

# Inference logs are one continuous session per workload; cut them into blocks so they
# can be split in time (train early, test late) like independent traces.
INFERENCE_BLOCK_S: float = 3600.0

# Cap on nodes per multi-node training job used for modelling (nodes in one job move in lockstep).
MAX_NODES_PER_JOB_MODEL: int = 4


def seed_everything(seed: int = SEED) -> None:
    """Fix the Python and NumPy RNGs. LightGBM gets its seed via params.

    PyTorch is deliberately NOT imported here: it ships its own OpenMP runtime that crashes LightGBM
    when both load in one process on macOS. The PyTorch models seed themselves in src/nets.py,
    which runs in a separate process.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def ensure_dirs() -> None:
    for d in (PROC_DIR, FIG_DIR):
        d.mkdir(parents=True, exist_ok=True)
