"""Matched label ablation: does the training TARGET explain the AP gain, or the pipeline differences?

The original big-drop classifier (src/models.py) differs from the control-aligned one (src/aligned.py) in
more than its label: leaf size, round cap, early-stopping metric and early-stopping rows. Here the
big-drop label is trained through the exact aligned pipeline (same rows, features, hyperparameters,
early-stopping half and metric), and both models are scored on the control-aligned event (L = 1 s) on
NLR test rows, with a paired cluster bootstrap of the AP difference.

    python -m src.ablation    # writes data/processed/ablation_info.json
"""
from __future__ import annotations

import json

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from src.aligned import _label_split
from src.config import PROC_DIR, SEED
from src.load import load_traces
from src.simulate import SimParams

N_BOOT = 1000


def _params(pos: float) -> dict:
    """Identical to src/aligned.py run(); only the label prevalence enters (class weighting)."""
    return {"objective": "binary", "learning_rate": 0.05, "num_leaves": 63, "min_data_in_leaf": 200,
            "feature_fraction": 0.8, "bagging_fraction": 0.8, "bagging_freq": 1, "lambda_l2": 1.0,
            "scale_pos_weight": float(np.sqrt((1 - pos) / pos)), "seed": SEED, "verbose": -1, "num_threads": 8}


def _fit(tr: pd.DataFrame, va_es: pd.DataFrame, feats: list[str], label: str) -> lgb.Booster:
    dtr = lgb.Dataset(tr[feats], tr[label].astype(int))
    dva = lgb.Dataset(va_es[feats], va_es[label].astype(int), reference=dtr)
    return lgb.train(_params(tr[label].mean()), dtr, 3000, valid_sets=[dva],
                     callbacks=[lgb.early_stopping(100, verbose=False)])


def cluster_bootstrap(y: np.ndarray, a: np.ndarray, b: np.ndarray, cl: np.ndarray, rng: np.random.Generator,
                      n: int = N_BOOT) -> tuple[float, float]:
    """95% percentile interval of AP(a) - AP(b), resampling whole clusters with replacement."""
    ids = np.unique(cl)
    rows = {c: np.flatnonzero(cl == c) for c in ids}
    d = []
    for _ in range(n):
        r = np.concatenate([rows[c] for c in rng.choice(ids, len(ids))])
        if y[r].min() == y[r].max():
            continue
        d.append(average_precision_score(y[r], a[r]) - average_precision_score(y[r], b[r]))
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def run(log=print) -> dict[str, float]:
    sp = SimParams()
    feats = json.load(open(PROC_DIR / "model_info.json"))["features"]
    traces, meta = load_traces(only_model=True)
    meta = meta.set_index("trace_id")
    trace_role = json.load(open(PROC_DIR / "val_roles_nlr.json"))  # same es/thr halves as src/aligned.py
    cols = feats + ["y_drop"]
    tr, va, te = (_label_split(s, traces, sp, cols) for s in ("train", "val", "test"))
    va_es = va[va["trace_id"].map(trace_role) == "es"]
    yk = "y_L1"
    m_al = _fit(tr, va_es, feats, yk)
    m_dr = _fit(tr, va_es, feats, "y_drop")
    s_al, s_dr = m_al.predict(te[feats], num_threads=8), m_dr.predict(te[feats], num_threads=8)
    y = te[yk].to_numpy().astype(int)
    # cluster = training job, or whole inference session (as in src/regime.py _unit_id)
    m = meta.loc[te["trace_id"]]
    cl = np.where(m["phase"].to_numpy() == "training", "job_" + m["job_id"].astype(str).to_numpy(),
                  "session_" + m["workload"].to_numpy())
    out = {"matched_aligned_ap": float(average_precision_score(y, s_al)),
           "matched_drop_ap": float(average_precision_score(y, s_dr)),
           "matched_aligned_best_iter": int(m_al.best_iteration), "matched_drop_best_iter": int(m_dr.best_iteration),
           "clusters": int(len(np.unique(cl)))}
    out["matched_diff"] = out["matched_aligned_ap"] - out["matched_drop_ap"]
    out["matched_diff_lo"], out["matched_diff_hi"] = cluster_bootstrap(y, s_al, s_dr, cl, np.random.default_rng(SEED))
    # also: the big-drop model on its own label, so the comparison is not a strawman
    out["matched_drop_ap_on_drop_label"] = float(average_precision_score(te["y_drop"].astype(int), s_dr))
    out["matched_aligned_ap_on_drop_label"] = float(average_precision_score(te["y_drop"].astype(int), s_al))
    json.dump(out, open(PROC_DIR / "ablation_info.json", "w"), indent=1)
    log(f"ablation: {out}")
    return out


if __name__ == "__main__":
    run()
