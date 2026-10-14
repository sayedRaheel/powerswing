"""Causal feature engineering and prediction targets.

Every feature at sample t uses only p[0..t]. Targets look forward. Feature groups:
  lags / differences, rolling stats over 1-60 s, step timers, time since last confirmed drop,
  rhythm features from a sliding autocorrelation (dominant period and the "repeat last cycle"
  forecast) and FFT phase of the dominant frequency.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

from src.config import DT_S, HORIZONS_S, PEAK_LOOKBACK_S, WARN_WINDOW_S
from src.events import detect_drops, drop_labels

FS = int(round(1 / DT_S))  # samples per second (5)
H_STEPS: dict[int, int] = {h: h * FS for h in HORIZONS_S}
MAX_H = max(H_STEPS.values())
WARN_STEPS = int(round(WARN_WINDOW_S * FS))

ACF_WIN = 120 * FS  # 120 s window for rhythm detection
ACF_MIN_LAG, ACF_MAX_LAG = 2 * FS, 40 * FS  # periods between 2 s and 40 s
RHYTHM_STRIDE = FS  # recompute rhythm every 1 s, hold in between
ACF_MIN_STRENGTH = 0.3  # below this there is no usable rhythm
STEP_W = 300.0  # a single-sample change bigger than this counts as a step (node W)
WARMUP = 30 * FS  # first rows of each trace are dropped (not enough history)


def _rolling(p: pd.Series, n: int, fn: str) -> np.ndarray:
    return getattr(p.rolling(n, min_periods=1), fn)().to_numpy()


def _time_since(mask: np.ndarray, cap_s: float = 600.0) -> np.ndarray:
    """Seconds since the last True in mask (inclusive), capped."""
    idx = np.where(mask, np.arange(len(mask)), -10**9)
    last = np.maximum.accumulate(idx)
    out = (np.arange(len(mask)) - last) * DT_S
    return np.minimum(out, cap_s)


def rhythm_estimates(p: np.ndarray) -> dict[str, np.ndarray]:
    """Sliding autocorrelation + FFT on a 120 s window, every RHYTHM_STRIDE samples.

    Returns per-sample arrays (held constant between recomputations):
      period (samples, 0 = no rhythm), acf_strength, fft_period_s, fft_power_frac, fft_sin, fft_cos.
    """
    n = len(p)
    pad = np.concatenate([np.full(ACF_WIN - 1, p[0]), p])
    starts = np.arange(0, n, RHYTHM_STRIDE)
    period = np.zeros(len(starts))
    strength = np.zeros(len(starts))
    fft_k = np.zeros(len(starts))
    fft_frac = np.zeros(len(starts))
    fft_phase_end = np.zeros(len(starts))
    lags = np.arange(ACF_MAX_LAG + 2)
    kmin, kmax = int(np.ceil(ACF_WIN / ACF_MAX_LAG)), ACF_WIN // ACF_MIN_LAG
    windows = sliding_window_view(pad, ACF_WIN)  # window i ends at sample i
    for c0 in range(0, len(starts), 4000):
        sl = starts[c0 : c0 + 4000]
        x = windows[sl].astype(float)
        x = x - x.mean(axis=1, keepdims=True)
        # autocorrelation via FFT (zero padded)
        F = np.fft.rfft(x, n=2 * ACF_WIN, axis=1)
        ac = np.fft.irfft(F * np.conj(F), axis=1)[:, lags]
        var = ac[:, :1]
        ac = np.divide(ac, var, out=np.zeros_like(ac), where=var > 1e-6)
        a = ac[:, ACF_MIN_LAG : ACF_MAX_LAG + 1]
        left, mid, right = ac[:, ACF_MIN_LAG - 1 : ACF_MAX_LAG], a, ac[:, ACF_MIN_LAG + 1 : ACF_MAX_LAG + 2]
        is_peak = (mid > left) & (mid >= right)
        peak_vals = np.where(is_peak, mid, -np.inf)
        best = peak_vals.max(axis=1)
        # first peak that is at least 90% of the best one (avoids picking a harmonic multiple)
        ok = peak_vals >= 0.9 * best[:, None]
        first = np.argmax(ok, axis=1)
        has = np.isfinite(best) & (best >= ACF_MIN_STRENGTH)
        period[c0 : c0 + len(sl)] = np.where(has, first + ACF_MIN_LAG, 0)
        strength[c0 : c0 + len(sl)] = np.where(np.isfinite(best), best, 0.0)
        # dominant FFT bin in the same period range
        X = np.fft.rfft(x, axis=1)
        pw = np.abs(X) ** 2
        band = pw[:, kmin : kmax + 1]
        kb = np.argmax(band, axis=1) + kmin
        tot = pw[:, 1:].sum(axis=1)
        fft_k[c0 : c0 + len(sl)] = kb
        fft_frac[c0 : c0 + len(sl)] = np.divide(band.max(axis=1), tot, out=np.zeros(len(sl)), where=tot > 0)
        ph = np.angle(X[np.arange(len(sl)), kb])
        fft_phase_end[c0 : c0 + len(sl)] = ph + 2 * np.pi * kb * (ACF_WIN - 1) / ACF_WIN
    # expand to every sample: hold values, advance FFT phase analytically
    rep = np.minimum(np.arange(n) // RHYTHM_STRIDE, len(starts) - 1)
    offset = np.arange(n) - starts[rep]
    k = fft_k[rep]
    theta = fft_phase_end[rep] + 2 * np.pi * k * offset / ACF_WIN
    return {
        "period": period[rep].astype(int),
        "acf_strength": strength[rep],
        "fft_period_s": np.where(k > 0, ACF_WIN / np.maximum(k, 1) * DT_S, 0.0),
        "fft_power_frac": fft_frac[rep],
        "fft_sin": np.sin(theta),
        "fft_cos": np.cos(theta),
    }


def rhythm_forecast(p: np.ndarray, period: np.ndarray, steps: int) -> np.ndarray:
    """Repeat-last-cycle forecast of p[t+steps]; persistence where no rhythm was found."""
    t = np.arange(len(p))
    P = np.maximum(period, 1)
    k = np.ceil(steps / P)
    idx = (t + steps - k * P).astype(int)
    out = p[np.clip(idx, 0, len(p) - 1)]
    return np.where((period > 0) & (idx >= 0), out, p)


def build_features(p: np.ndarray) -> pd.DataFrame:
    """All causal features for every sample of one trace."""
    s = pd.Series(p)
    n = len(p)
    f: dict[str, np.ndarray] = {"p": p}
    for k in (1, 2, 3, 5, 10, 25, 50):
        f[f"d{k}"] = p - s.shift(k).bfill().to_numpy()
    for k in (5, 10, 25, 50, 100):
        f[f"lag{k}"] = s.shift(k).bfill().to_numpy()
    for sec in (1, 5, 10, 30, 60):
        w = sec * FS
        mx = _rolling(s, w, "max")
        f[f"mean{sec}"] = _rolling(s, w, "mean")
        f[f"std{sec}"] = np.nan_to_num(_rolling(s, w, "std"))
        f[f"min{sec}"] = _rolling(s, w, "min")
        f[f"max{sec}"] = mx
        f[f"rel_max{sec}"] = p / np.maximum(mx, 1.0)
    peak10 = _rolling(s, int(PEAK_LOOKBACK_S * FS), "max")
    d1 = np.diff(p, prepend=p[0])
    f["t_since_upstep"] = _time_since(d1 > STEP_W)
    f["t_since_downstep"] = _time_since(d1 < -STEP_W)
    # time since last *confirmed* drop: an onset at o is only known at o + 1 s
    on = detect_drops(p)
    confirmed = np.zeros(n, bool)
    c = on + FS
    confirmed[c[c < n]] = True
    f["t_since_drop"] = _time_since(confirmed)
    rh = rhythm_estimates(p)
    f.update({k: v for k, v in rh.items()})
    f["period_s"] = rh["period"] * DT_S
    f["phase_in_period"] = np.where(rh["period"] > 0, (f["t_since_upstep"] / np.maximum(f["period_s"], DT_S)) % 1.0, -1.0)
    for h, st in H_STEPS.items():
        f[f"rhythm_{h}s"] = rhythm_forecast(p, rh["period"], st)
        f[f"rhythm_d{h}s"] = f[f"rhythm_{h}s"] - p
    # rhythm-implied fall over the next 5 s: min of the repeated last cycle
    mins = np.min(np.stack([rhythm_forecast(p, rh["period"], j) for j in range(1, WARN_STEPS + 1)]), axis=0)
    f["rhythm_fall5_frac"] = (p - mins) / np.maximum(peak10, 1.0)
    f["peak10"] = peak10
    df = pd.DataFrame(f)
    df = df.drop(columns=["period"])
    return df.astype(np.float32)


def build_targets(p: np.ndarray) -> pd.DataFrame:
    """Forecast targets (future power and delta) and the 5 s drop-warning label."""
    n = len(p)
    out: dict[str, np.ndarray] = {}
    for h, st in H_STEPS.items():
        fut = np.full(n, np.nan)
        fut[: n - st] = p[st:]
        out[f"y_{h}s"] = fut
    out["y_drop"] = drop_labels(n, detect_drops(p), WARN_WINDOW_S)
    return pd.DataFrame(out)


def trace_table(tid: str, p: np.ndarray, stride: int = 1) -> pd.DataFrame:
    """Features + targets for one trace, restricted to rows with full history and full future."""
    X = build_features(p)
    Y = build_targets(p)
    df = pd.concat([X, Y], axis=1)
    df["idx"] = np.arange(len(p))
    df = df.iloc[WARMUP : len(p) - MAX_H : stride]
    df.insert(0, "trace_id", tid)
    return df


FEATURE_EXCLUDE = {"trace_id", "idx", "y_drop"} | {f"y_{h}s" for h in HORIZONS_S}


def feature_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in FEATURE_EXCLUDE]
