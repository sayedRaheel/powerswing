"""Small helpers shared by the LightGBM process and the PyTorch process (no heavy imports here)."""
from __future__ import annotations

import time

import numpy as np
import pandas as pd


def power_dict(traces: pd.DataFrame) -> dict[str, np.ndarray]:
    """trace_id -> node power array (W), in a stable order."""
    return {tid: g["power_w"].to_numpy(dtype=float) for tid, g in traces.groupby("trace_id", sort=True)}


def time_per_call(fn, n: int = 200) -> float:
    """Median wall time in milliseconds for a single-prediction call."""
    fn()
    ts = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        ts.append(time.perf_counter() - t0)
    return float(np.median(ts) * 1000)
