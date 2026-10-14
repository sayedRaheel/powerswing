"""Step 6: metrics and charts for forecasting and drop warning."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, precision_recall_curve

from src.config import DT_S, FIG_DIR, HORIZONS_S
from src.events import detect_drops
from src.features import FS, WARN_STEPS
from src.plotstyle import COLORS, WORKLOAD_LABEL, apply_style

LEAD_MIN_STEPS = FS  # "at least 1 s of warning"
MERGE_GAP_STEPS = FS  # alarm episodes closer than 1 s are merged
_ONSET_CACHE: dict[int, np.ndarray] = {}


def _onsets(p: np.ndarray) -> np.ndarray:
    key = id(p)
    if key not in _ONSET_CACHE:
        _ONSET_CACHE[key] = detect_drops(p)
    return _ONSET_CACHE[key]


# ----------------------------------------------------------------------------- forecasting

def forecast_metrics(y: np.ndarray, yhat: np.ndarray) -> dict[str, float]:
    e = yhat - y
    return {
        "MAE": float(np.mean(np.abs(e))),
        "RMSE": float(np.sqrt(np.mean(e**2))),
        "MAPE": float(100 * np.mean(np.abs(e) / np.maximum(np.abs(y), 1.0))),
    }


def forecast_table(df: pd.DataFrame, preds: dict[str, dict[int, np.ndarray]], by: str | None = None) -> pd.DataFrame:
    """Long table: model, horizon, [group], MAE, RMSE, MAPE."""
    rows = []
    groups = [(None, np.ones(len(df), bool))] if by is None else [(g, (df[by] == g).to_numpy()) for g in sorted(df[by].unique())]
    for name, fc in preds.items():
        for h in HORIZONS_S:
            y = df[f"y_{h}s"].to_numpy()
            for g, m in groups:
                r = {"model": name, "horizon_s": h, **forecast_metrics(y[m], fc[h][m])}
                if by is not None:
                    r[by] = g
                rows.append(r)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- drop warning

def _episodes(idx: np.ndarray, alarm: np.ndarray) -> list[tuple[int, int]]:
    """Contiguous alarm runs (in sample index), merging gaps shorter than MERGE_GAP_STEPS."""
    on = idx[alarm]
    if len(on) == 0:
        return []
    eps = []
    s = e = on[0]
    for i in on[1:]:
        if i - e <= MERGE_GAP_STEPS:
            e = i
        else:
            eps.append((s, e))
            s = e = i
    eps.append((s, e))
    return eps


def event_eval(rows: pd.DataFrame, score: np.ndarray, thr: float, power: dict[str, np.ndarray]) -> dict[str, float]:
    """Event-level drop-warning metrics for one threshold.

    rows must hold every evaluable sample (stride 1) of each trace: trace_id, idx, y_drop.
    """
    alarm_all = score >= thr
    n_ev = caught = 0
    leads: list[float] = []
    n_eps = false_eps = 0
    hours = len(rows) * DT_S / 3600
    for tid, g in rows.groupby("trace_id", sort=False):
        idx = g["idx"].to_numpy()
        al = alarm_all[g["_row"].to_numpy()]
        p = power[tid]
        onsets = _onsets(p)
        lo, hi = idx.min(), idx.max()
        onsets = onsets[(onsets - WARN_STEPS >= lo) & (onsets <= hi)]
        alarm_at = np.zeros(len(p), bool)
        alarm_at[idx[al]] = True
        for o in onsets:
            n_ev += 1
            win = alarm_at[o - WARN_STEPS : o]  # samples o-25 .. o-1
            if win[: WARN_STEPS - LEAD_MIN_STEPS + 1].any():  # alarm at o-25 .. o-5
                caught += 1
                # lead = time from the first alarm in the 5 s window to the onset (caught events only)
                leads.append((WARN_STEPS - np.argmax(win)) * DT_S)
        eps = _episodes(idx, al)
        n_eps += len(eps)
        for s, e in eps:
            if not np.any((onsets > s) & (onsets <= e + WARN_STEPS)):
                false_eps += 1
    return {
        "threshold": thr,
        "events": n_ev,
        "recall_1s": caught / max(n_ev, 1),
        "mean_lead_s": float(np.mean(leads)) if leads else 0.0,  # among events caught >= 1 s early
        "alarm_episodes": n_eps,
        "episode_precision": (n_eps - false_eps) / max(n_eps, 1),
        "false_alarms_per_hour": false_eps / hours,
    }


def sample_metrics(y: np.ndarray, score: np.ndarray, thr: float) -> dict[str, float]:
    a = score >= thr
    tp = np.sum(a & (y == 1))
    prec = tp / max(a.sum(), 1)
    rec = tp / max((y == 1).sum(), 1)
    return {"precision": prec, "recall": rec, "F1": 2 * prec * rec / max(prec + rec, 1e-9),
            "AP": float(average_precision_score(y, score))}


PICK_LOG: list[dict] = []  # records whether each threshold search reached its target


def pick_threshold(rows: pd.DataFrame, score: np.ndarray, power: dict[str, np.ndarray],
                   target_recall: float = 0.85) -> float:
    """Highest threshold whose event recall (>=1 s lead) on validation reaches the target.

    Recall can only fall as the threshold rises, so a binary search over 1,000 score quantiles
    (0 to 0.999) finds it in about 10 evaluations. If even the lowest candidate misses the target,
    that candidate is returned. Each outcome is appended to PICK_LOG.
    """
    cand = np.unique(np.quantile(score, np.linspace(0.0, 0.999, 1000)))  # ascending

    def rec(i: int) -> float:
        return event_eval(rows, score, float(cand[i]), power)["recall_1s"]

    lo, hi = 0, len(cand) - 1
    r_lo = rec(lo)
    if r_lo < target_recall:
        PICK_LOG.append({"threshold": float(cand[lo]), "val_recall": r_lo, "target_met": False})
        return float(cand[lo])
    while lo < hi:  # invariant: rec(lo) >= target
        mid = (lo + hi + 1) // 2
        if rec(mid) >= target_recall:
            lo = mid
        else:
            hi = mid - 1
    PICK_LOG.append({"threshold": float(cand[lo]), "val_recall": rec(lo), "target_met": True})
    return float(cand[lo])


def prep_rows(df: pd.DataFrame) -> pd.DataFrame:
    rows = df[["trace_id", "idx", "y_drop"]].reset_index(drop=True).copy()
    rows["_row"] = np.arange(len(rows))
    return rows


# ----------------------------------------------------------------------------- charts

MODEL_ORDER = ["persistence", "moving_avg", "rhythm", "lightgbm", "tcn", "chronos_bolt_small", "timesfm_2p5"]
MODEL_LABEL = {
    "persistence": "Persistence", "moving_avg": "Moving avg", "rhythm": "Rhythm repeat",
    "lightgbm": "LightGBM", "tcn": "Tiny TCN", "chronos_bolt_small": "Chronos-Bolt (zero-shot)", "timesfm_2p5": "TimesFM 2.5 (zero-shot)",
}
MODEL_COLOR = {
    "persistence": "#c4cad1", "moving_avg": "#a3abb5", "rhythm": "#6f7a86",
    "lightgbm": COLORS["model"], "tcn": COLORS["model2"], "chronos_bolt_small": COLORS["model3"], "timesfm_2p5": "#c05fa0",
}


def plot_model_bars(tab: pd.DataFrame, h: int, fname: str, title: str) -> None:
    apply_style()
    t = tab[tab["horizon_s"] == h].set_index("model").reindex([m for m in MODEL_ORDER if m in set(tab["model"])])
    fig, ax = plt.subplots(figsize=(8, 3.6))
    bars = ax.barh([MODEL_LABEL[m] for m in t.index], t["MAE"], color=[MODEL_COLOR[m] for m in t.index])
    for b, v in zip(bars, t["MAE"]):
        ax.text(v, b.get_y() + b.get_height() / 2, f" {v:.0f} W", va="center", fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Mean absolute error per 4-GPU node (W), lower is better")
    ax.set_title(title, loc="left")
    fig.tight_layout()
    fig.savefig(FIG_DIR / fname, dpi=140)
    plt.close(fig)


def plot_error_by_horizon(tab: pd.DataFrame, fname: str, title: str) -> None:
    apply_style()
    fig, ax = plt.subplots(figsize=(7, 4))
    for m in [m for m in MODEL_ORDER if m in set(tab["model"])]:
        t = tab[tab["model"] == m].sort_values("horizon_s")
        lw = 2.4 if m in ("lightgbm", "tcn") else 1.4
        ax.plot(t["horizon_s"], t["MAE"], "o-", lw=lw, color=MODEL_COLOR[m], label=MODEL_LABEL[m])
    ax.set_xticks(list(HORIZONS_S))
    ax.set_xlabel("Forecast horizon (s)")
    ax.set_ylabel("MAE per node (W)")
    ax.set_title(title, loc="left")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / fname, dpi=140)
    plt.close(fig)


def plot_pr(curves: dict[str, tuple[np.ndarray, np.ndarray, float]], fname: str) -> None:
    apply_style()
    fig, ax = plt.subplots(figsize=(6, 4.6))
    colors = {"lightgbm": COLORS["model"], "tcn": COLORS["model2"], "rhythm_alarm": "#6f7a86"}
    labels = {"lightgbm": "LightGBM", "tcn": "Tiny TCN", "rhythm_alarm": "Rhythm alarm (baseline)"}
    for k, (pr, rc, ap) in curves.items():
        ax.plot(rc, pr, color=colors[k], lw=2, label=f"{labels[k]} (AP {ap:.2f})")
    ax.set_xlabel("Recall (share of pre-drop seconds flagged)")
    ax.set_ylabel("Precision")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_title("Drop warning: precision vs recall (test set)", loc="left")
    ax.legend(loc="lower left")
    fig.tight_layout()
    fig.savefig(FIG_DIR / fname, dpi=140)
    plt.close(fig)


def pr_curve(y: np.ndarray, s: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    pr, rc, _ = precision_recall_curve(y, s)
    step = max(1, len(pr) // 2000)
    return pr[::step], rc[::step], float(average_precision_score(y, s))


def plot_overlays(df: pd.DataFrame, preds: dict[str, dict[int, np.ndarray]], score: np.ndarray, thr: float,
                  power: dict[str, np.ndarray], picks: list[tuple[str, int, str]], h: int, fname: str) -> None:
    """Actual vs predicted (h seconds ahead) on example windows, drops and alarms marked."""
    apply_style()
    fig, axes = plt.subplots(len(picks), 1, figsize=(13, 2.9 * len(picks)))
    axes = np.atleast_1d(axes)
    for ax, (tid, center, label) in zip(axes, picks):
        m = (df["trace_id"] == tid).to_numpy()
        idx = df.loc[m, "idx"].to_numpy()
        w = (idx >= center - 60 * FS) & (idx < center + 60 * FS)
        ii = idx[w]
        t = ii * DT_S
        tt = t + h  # a forecast made at t is about time t + h
        p = power[tid]
        ax.plot(t, p[ii] / 1e3, color=COLORS["raw"], lw=1.4, label="actual")
        ax.plot(tt, preds["rhythm"][h][m][w] / 1e3, color="#a3abb5", lw=1, ls="--", label=f"rhythm baseline ({h}s ahead)")
        ax.plot(tt, preds["lightgbm"][h][m][w] / 1e3, color=COLORS["model"], lw=1.2, label=f"LightGBM ({h}s ahead)")
        on = detect_drops(p)
        on = on[(on >= ii.min()) & (on <= ii.max())]
        ax.plot(on * DT_S, p[on] / 1e3, "v", color=COLORS["drop"], ms=8, label="big drop starts")
        al = score[m][w] >= thr
        ymin = ax.get_ylim()[0]
        ax.fill_between(t, ymin, ymin + 0.08 * (ax.get_ylim()[1] - ymin), where=al, color=COLORS["burn"], alpha=0.6,
                        step="mid", label="drop warning on")
        ax.set_xlim(t.min(), t.max())
        ax.set_title(label, loc="left")
        ax.set_ylabel("node kW")
    axes[0].legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, 1.35))
    axes[-1].set_xlabel("seconds into trace")
    fig.tight_layout()
    fig.savefig(FIG_DIR / fname, dpi=140)
    plt.close(fig)


def workload_label(w: str) -> str:
    return WORKLOAD_LABEL.get(w, w)
