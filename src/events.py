"""Automatic detection and characterisation of "big drop" events.

Definition (from the brief): power falls by more than 30% of the recent peak within 1 second.
  recent_peak[t] = max power over the previous PEAK_LOOKBACK_S seconds (inclusive of t)
  candidate[t]   = p[t] - min(p[t+1 .. t+1s]) > DROP_FRAC * recent_peak[t]
  onset          = first sample of each run of candidates, with a refractory period so one
                   physical drop is counted once.
To avoid counting noise on an idle node we also require recent_peak >= MIN_PEAK_W.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

from src.config import DROP_FRAC, DROP_WINDOW_S, DT_S, PEAK_LOOKBACK_S, REFRACTORY_S

MIN_PEAK_W = 1000.0  # 4-GPU node idles near 300 W; drops are only meaningful from a loaded state


def rolling_max_past(p: np.ndarray, n: int) -> np.ndarray:
    """max(p[t-n+1 .. t]) for every t (shorter window at the start)."""
    s = pd.Series(p)
    return s.rolling(n, min_periods=1).max().to_numpy()


def future_min(p: np.ndarray, n: int) -> np.ndarray:
    """min(p[t+1 .. t+n]) for every t; NaN where the window runs past the end."""
    out = np.full(len(p), np.nan)
    if len(p) > n:
        w = sliding_window_view(p[1:], n).min(axis=1)
        out[: len(w)] = w
    return out


def detect_drops(p: np.ndarray) -> np.ndarray:
    """Return sample indices of big-drop onsets in a power trace."""
    n_win = int(round(DROP_WINDOW_S / DT_S))
    peak = rolling_max_past(p, int(round(PEAK_LOOKBACK_S / DT_S)))
    fmin = future_min(p, n_win)
    cand = (p - fmin > DROP_FRAC * peak) & (peak >= MIN_PEAK_W)
    cand = np.nan_to_num(cand, nan=0).astype(bool)
    idx = np.flatnonzero(cand)
    onsets: list[int] = []
    refr = int(round(REFRACTORY_S / DT_S))
    for i in idx:
        if not onsets or i - onsets[-1] > refr:
            onsets.append(int(i))
    return np.asarray(onsets, dtype=int)


def characterise_drops(p: np.ndarray, onsets: np.ndarray) -> pd.DataFrame:
    """Size, duration and ramp rate for each onset.

    size_w       p[onset] - bottom, where bottom = min power in the 5 s after onset
    size_pct     size as % of recent peak
    duration_s   time from onset until power recovers half way back from the bottom
                 (NaN if it never recovers before the trace ends, e.g. job end)
    ramp_max_wps steepest single-step fall between onset and bottom (W/s)
    ramp_avg_wps size / time-to-bottom (W/s)
    """
    peak = rolling_max_past(p, int(round(PEAK_LOOKBACK_S / DT_S)))
    look = int(round(5.0 / DT_S))
    rows = []
    for o in onsets:
        seg = p[o : o + look + 1]
        b_rel = int(np.argmin(seg))
        bottom = seg[b_rel]
        size = p[o] - bottom
        half = bottom + 0.5 * size
        after = p[o + b_rel :]
        rec = np.flatnonzero(after >= half)
        dur = (b_rel + rec[0]) * DT_S if len(rec) else np.nan
        falls = -np.diff(p[o : o + b_rel + 1]) / DT_S if b_rel > 0 else np.array([0.0])
        rows.append({
            "onset_idx": int(o),
            "onset_s": o * DT_S,
            "start_w": p[o],
            "bottom_w": bottom,
            "size_w": size,
            "size_pct": 100 * size / peak[o],
            "time_to_bottom_s": b_rel * DT_S,
            "duration_s": dur,
            "ramp_max_wps": float(falls.max()),
            "ramp_avg_wps": size / max(b_rel * DT_S, DT_S),
        })
    return pd.DataFrame(rows)


def drop_labels(n: int, onsets: np.ndarray, window_s: float) -> np.ndarray:
    """y[t] = 1 if a drop onset falls in (t, t + window_s]."""
    y = np.zeros(n, dtype=np.int8)
    w = int(round(window_s / DT_S))
    for o in onsets:
        y[max(0, o - w) : o] = 1
    return y
