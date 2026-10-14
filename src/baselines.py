"""Step 4: simple baselines. All are causal and read the precomputed feature table.

persistence   p(t+h) = p(t)
moving_avg    p(t+h) = mean of the last 5 s
rhythm        detect the dominant cycle with a sliding autocorrelation (120 s window, periods 2-40 s)
              and repeat the last cycle; falls back to persistence when no clear rhythm (ACF < 0.3)

For the drop warning task the matching baseline is "rhythm alarm": the score is the fall the
repeated last cycle implies over the next 5 s, as a fraction of the recent peak.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import HORIZONS_S

BASELINES: tuple[str, ...] = ("persistence", "moving_avg", "rhythm")


def predict_baseline(name: str, df: pd.DataFrame, h: int) -> np.ndarray:
    if name == "persistence":
        return df["p"].to_numpy()
    if name == "moving_avg":
        return df["mean5"].to_numpy()
    if name == "rhythm":
        return df[f"rhythm_{h}s"].to_numpy()
    raise KeyError(name)


def all_baseline_forecasts(df: pd.DataFrame) -> dict[str, dict[int, np.ndarray]]:
    return {b: {h: predict_baseline(b, df, h) for h in HORIZONS_S} for b in BASELINES}


def rhythm_alarm_score(df: pd.DataFrame) -> np.ndarray:
    """Higher = repeated last cycle predicts a bigger fall in the next 5 s."""
    return df["rhythm_fall5_frac"].to_numpy()
