"""Paper track, step 2E: train the predictor on what the controller actually needs.

The original drop classifier learns "a >30% fall within 1 s starts in the next 5 s". The ramp limiter
cares about something else: will the 1 s down-ramp exceed the grid limit (10% of rated per second)
at a time when the actuator, triggered now, would be engaged? Many violations (e.g. the Llama LoRA
22% square wave) are not "big drops", so the original target never teaches the model about them.

Control-aligned target, for actuator latency L (plus a one-sample decision delay), lead margin m = 1 s
and hold H (both as in the simulator):
    y(t) = 1  if a raw down-ramp violation starts at v with v in [e + FS, e + H - 1],  e = t + lat_samples(L)
i.e. the whole 1 s ramp window [v - FS, v] lies inside the half-open armed window [e, e + H).

One model per actuator latency (the trigger window moves with latency). Validation is split by
independent unit into two halves: "es" for early stopping, "thr" for threshold / operating-point
choice in src/regime.py, so no validation row is used twice.

Outputs data/processed/aligned_scores_{val,test}_L{latency}.parquet (trace_id, idx, score_aligned,
score_rhythm_aligned); the 1 s files are also written without the suffix for src/crossdata.py users.
"""
from __future__ import annotations

import json

import lightgbm as lgb
import numpy as np
import pandas as pd

from src.config import DT_S, PROC_DIR, SEED
from src.features import FS
from src.load import load_traces
from src.simulate import NODE_RATED_W, SimParams

LATENCIES_S = (0.0, 0.2, 0.5, 1.0, 2.0, 3.0)  # same grid as src/regime.py
# Each 0.2 s row averages samples in [t, t + 0.2 s), so the information in row t is only complete at the
# end of the bin. Every trigger therefore acts one sample later than its row index (decision delay).
DECISION_DELAY = 1


def lat_samples(latency_s: float) -> int:
    """Samples from a row's index until a trigger issued on it engages the actuator."""
    return int(round(latency_s / DT_S)) + DECISION_DELAY


def hold_samples(sp: SimParams) -> int:
    return int(round(sp.arm_hold_s / DT_S))


def val_roles(units: pd.DataFrame, group_cols: list[str]) -> dict[str, str]:
    """Split validation units into "es" (early stopping) and "thr" (threshold choice), alternating
    within each group (e.g. workload) after a seeded shuffle, so both halves see every group."""
    rng = np.random.default_rng(SEED)
    roles: dict[str, str] = {}
    for _, g in units.drop_duplicates("unit").groupby(group_cols):
        u = np.array(sorted(g["unit"]))
        rng.shuffle(u)
        for i, x in enumerate(u):
            roles[x] = "es" if i % 2 == 0 else "thr"
    return roles


def nlr_unit(meta: pd.DataFrame) -> pd.Series:
    """Independent unit for NLR traces: the training job, or the inference hour block."""
    tid = meta.index.to_series() if "trace_id" not in meta.columns else meta["trace_id"]
    return pd.Series(np.where(meta["phase"] == "training", "nlr_job_" + meta["job_id"].astype(str), tid),
                     index=meta.index)


def violation_starts(p: np.ndarray, limit_w: float) -> np.ndarray:
    """Start index of each run where the 1 s down-ramp exceeds the limit (same rule as the simulator)."""
    r = np.zeros(len(p))
    r[FS:] = p[FS:] - p[:-FS]
    down = -r > limit_w
    return np.flatnonzero(down & ~np.concatenate([[False], down[:-1]]))


def aligned_labels(p: np.ndarray, idx: np.ndarray, sp: SimParams, latency_s: float | None = None) -> np.ndarray:
    """y at rows idx: a trigger at t arms the limiter for the half-open window [e, e + hold) with
    e = t + L (L includes the one-sample decision delay). A violation detected at v (1 s ramp over
    [v - FS, v]) is labelled positive when that whole 1 s window lies inside the armed window:
    v in [e + FS, e + hold - 1]. Violations induced by the limiter itself are not labelled."""
    limit = sp.ramp_limit_frac_per_s * NODE_RATED_W
    v = violation_starts(p, limit)
    e = idx + lat_samples(sp.actuator_latency_s if latency_s is None else latency_s)
    lo = e + FS
    hi = e + hold_samples(sp) - 1
    # count violation starts in [lo, hi] with two binary searches
    return (np.searchsorted(v, hi, side="right") - np.searchsorted(v, lo, side="left")) > 0


def rhythm_aligned_score(p: np.ndarray, idx: np.ndarray, period_s: np.ndarray, sp: SimParams,
                         latency_s: float | None = None) -> np.ndarray:
    """Same target, no learning: replay the last cycle and measure the largest predicted 1 s down-ramp
    inside the trigger window, as a fraction of rated power. Uses only samples up to t (causal).

    Future sample t+k is predicted as p[t + k - P * ceil(k / P)] with P the causal period estimate.
    Rows without a detected rhythm get score 0 (persistence predicts no ramp).
    """
    lat = lat_samples(sp.actuator_latency_s if latency_s is None else latency_s)
    w = hold_samples(sp)
    P = np.where(np.isfinite(period_s), np.round(period_s / DT_S), 0).astype(int)
    has = P > 0
    Ps = np.where(has, P, 1)

    def at(k: int) -> np.ndarray:
        """Predicted power at t + k (k may be <= 0, then it is the real past sample)."""
        if k <= 0:
            return p[np.clip(idx + k, 0, len(p) - 1)]
        back = Ps * np.ceil(k / Ps).astype(int)
        return p[np.clip(idx + k - back, 0, len(p) - 1)]

    best = np.zeros(len(idx))
    for u in range(lat + FS, lat + w):  # same protected window as aligned_labels
        best = np.maximum(best, at(u - FS) - at(u))
    return np.where(has, best / NODE_RATED_W, 0.0)


def _label_split(split: str, traces: pd.DataFrame, sp: SimParams, cols: list[str]) -> pd.DataFrame:
    """Feature table of one split plus aligned labels and rhythm-replay scores for every latency."""
    tab = pd.read_parquet(PROC_DIR / f"table_{split}.parquet", columns=cols + ["trace_id", "idx", "workload"])
    p_by = {t: g["power_w"].to_numpy(float) for t, g in traces[traces["trace_id"].isin(set(tab["trace_id"]))].groupby("trace_id")}
    idx_all = tab["idx"].to_numpy()
    per_all = tab["period_s"].to_numpy(float)
    groups = tab.groupby("trace_id", sort=False).indices
    for L in LATENCIES_S:
        y = np.zeros(len(tab), bool)
        rs = np.zeros(len(tab))
        for tid, rows in groups.items():
            y[rows] = aligned_labels(p_by[tid], idx_all[rows], sp, L)
            rs[rows] = rhythm_aligned_score(p_by[tid], idx_all[rows], per_all[rows], sp, L)
        tab[f"y_L{L:g}"] = y
        tab[f"r_L{L:g}"] = rs
    return tab


def run(log=print) -> dict[str, float]:
    from sklearn.metrics import average_precision_score

    sp = SimParams()
    feats = json.load(open(PROC_DIR / "model_info.json"))["features"]
    traces, meta = load_traces(only_model=True)
    meta = meta.set_index("trace_id")
    unit = nlr_unit(meta)
    vm = meta[meta["split"] == "val"].assign(unit=unit)
    roles = val_roles(vm.reset_index(), ["workload"])
    trace_role = {t: roles[u] for t, u in unit[vm.index].items()}
    json.dump(trace_role, open(PROC_DIR / "val_roles_nlr.json", "w"), indent=1)
    tr, va, te = (_label_split(s, traces, sp, feats) for s in ("train", "val", "test"))
    va_es = va[va["trace_id"].map(trace_role) == "es"]
    va_thr = va[va["trace_id"].map(trace_role) == "thr"]
    log(f"aligned: rows train={len(tr):,} val_es={len(va_es):,} val_thr={len(va_thr):,} test={len(te):,}")
    out: dict[str, float] = {}
    for L in LATENCIES_S:
        yk, rk = f"y_L{L:g}", f"r_L{L:g}"
        pos = tr[yk].mean()
        params = {"objective": "binary", "learning_rate": 0.05, "num_leaves": 63, "min_data_in_leaf": 200,
                  "feature_fraction": 0.8, "bagging_fraction": 0.8, "bagging_freq": 1, "lambda_l2": 1.0,
                  "scale_pos_weight": float(np.sqrt((1 - pos) / pos)), "seed": SEED, "verbose": -1, "num_threads": 8}
        dtr = lgb.Dataset(tr[feats], tr[yk].astype(int))
        dva = lgb.Dataset(va_es[feats], va_es[yk].astype(int), reference=dtr)
        clf = lgb.train(params, dtr, 3000, valid_sets=[dva], callbacks=[lgb.early_stopping(100, verbose=False)])
        clf.save_model(str(PROC_DIR / f"lgb_aligned_L{L:g}.txt"))
        for name, d in (("val", va_thr), ("test", te)):
            sc = clf.predict(d[feats], num_threads=8)
            df = pd.DataFrame({"trace_id": d["trace_id"], "idx": d["idx"], "score_aligned": sc, "score_rhythm_aligned": d[rk]})
            df.to_parquet(PROC_DIR / f"aligned_scores_{name}_L{L:g}.parquet", index=False)
            if L == 1.0:
                df.to_parquet(PROC_DIR / f"aligned_scores_{name}.parquet", index=False)
            out[f"L{L:g}_{name}_ap"] = float(average_precision_score(d[yk], sc))
            out[f"L{L:g}_{name}_ap_rhythm"] = float(average_precision_score(d[yk], d[rk]))
        log(f"aligned: L={L:g}s best_iter={clf.best_iteration} pos={pos:.3f} test AP learned={out[f'L{L:g}_test_ap']:.3f} "
            f"rhythm={out[f'L{L:g}_test_ap_rhythm']:.3f}")
        if L == 1.0:
            sc = clf.predict(te[feats], num_threads=8)
            for wname, g in te.assign(s=sc).groupby("workload"):
                if g[yk].nunique() == 2:
                    out[f"test_ap_{wname}"] = float(average_precision_score(g[yk], g["s"]))
                    out[f"test_ap_rhythm_{wname}"] = float(average_precision_score(g[yk], g[rk]))
                    log(f"aligned:   {wname:28s} learned AP={out[f'test_ap_{wname}']:.3f} rhythm AP={out[f'test_ap_rhythm_{wname}']:.3f}")
            old = pd.read_parquet(PROC_DIR / "test_predictions.parquet", columns=["trace_id", "idx", "score_lightgbm", "score_rhythm_alarm"])
            m = te[["trace_id", "idx", yk]].merge(old, on=["trace_id", "idx"])
            out["test_ap_old_drop_clf"] = float(average_precision_score(m[yk], m["score_lightgbm"]))
            out["test_ap_rhythm_alarm"] = float(average_precision_score(m[yk], m["score_rhythm_alarm"]))
            log(f"aligned: same target, old drop classifier AP={out['test_ap_old_drop_clf']:.3f}, rhythm alarm AP={out['test_ap_rhythm_alarm']:.3f}")
    json.dump(out, open(PROC_DIR / "aligned_info.json", "w"), indent=1)
    return out


if __name__ == "__main__":
    run()
