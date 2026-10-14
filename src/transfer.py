"""Paper track, step 2D3: can a learned trigger be made to work at a NEW site?

Two ideas, both tested leave-one-dataset-out on the harmonised cross-dataset table (src/crossdata.py):

1. Shape-only features. Absolute power levels (W) differ by GPU type and idle floor even after
   normalising to rated power. Re-express every level feature relative to the node's own trailing
   60 s maximum, and keep the timing / rhythm features, so the model sees only the *shape*.
2. Few-minute site adaptation. Start from the model trained on the other datasets and continue
   boosting on K minutes of the new site's own TRAIN-split data (K = 5, 15, 60), early-stopped on
   those same minutes' tail. Rhythm replay needs no data at all, so this measures how much site data
   learning needs before it pays off.

Scored on the held-out dataset's TEST split with the same paired unit-level bootstrap as crossdata.
"""
from __future__ import annotations

import json

import lightgbm as lgb
import numpy as np
import pandas as pd

from src.config import PROC_DIR, REPORT_DIR, SEED
from sklearn.metrics import average_precision_score

from src.crossdata import DATASETS, N_BOOT_SUB, VARIANT, add_val_roles, ap_with_ci

TABLES = REPORT_DIR / "tables"
ADAPT_MIN = (5, 15, 60)
N_REPS = 5  # independent draws of local site data per duration
# features that carry an absolute power level (normalised W); everything else is timing / shape
LEVEL_PREFIXES = ("p", "lag", "mean", "min", "max", "std", "peak10", "d", "rhythm_1s", "rhythm_5s", "rhythm_10s",
                  "rhythm_d")


def _is_level(c: str) -> bool:
    if c in ("p", "peak10"):
        return True
    return any(c.startswith(x) for x in LEVEL_PREFIXES[1:]) and not c.startswith("rel_")


def shape_table(tab: pd.DataFrame, feats: list[str]) -> tuple[pd.DataFrame, list[str]]:
    """Divide level features by the trailing 60 s max so only shape remains."""
    ref = tab["max60"].to_numpy() + 1.0
    out = {}
    for c in feats:
        out[f"s_{c}"] = tab[c].to_numpy() / ref if _is_level(c) else tab[c].to_numpy()
    s = pd.DataFrame(out, index=tab.index)
    return pd.concat([tab[["trace_id", "idx", "dataset", "workload", "split", "unit", "cluster", "vrole", "y_aligned", "score_rhythm_aligned"]], s], axis=1), list(s.columns)


def _params(pos: float) -> dict:
    return {"objective": "binary", "learning_rate": 0.05, "num_leaves": 63, "min_data_in_leaf": 200,
            "feature_fraction": 0.8, "bagging_fraction": 0.8, "bagging_freq": 1, "lambda_l2": 1.0,
            "scale_pos_weight": float(np.sqrt((1 - pos) / pos)), "seed": SEED, "verbose": -1, "num_threads": 8}


def fit(tab: pd.DataFrame, feats: list[str], sets: tuple[str, ...]) -> lgb.Booster:
    tr = tab[tab["dataset"].isin(sets) & (tab["split"] == "train")]
    va = tab[tab["dataset"].isin(sets) & (tab["split"] == "val") & (tab["vrole"] == "es")]
    w = tr["dataset"].map(1.0 / tr["dataset"].value_counts()).to_numpy()
    dtr = lgb.Dataset(tr[feats], tr["y_aligned"].astype(int), weight=w / w.mean())
    dva = lgb.Dataset(va[feats], va["y_aligned"].astype(int), reference=dtr)
    return lgb.train(_params(tr["y_aligned"].mean()), dtr, 3000, valid_sets=[dva],
                     callbacks=[lgb.early_stopping(100, verbose=False)])


def site_minutes(tab: pd.DataFrame, ds: str, minutes: int, rng: np.random.Generator) -> pd.DataFrame:
    """First rows of randomly ordered TRAIN-split traces of the new site, totalling `minutes` (1 row = 1 s)."""
    d = tab[(tab["dataset"] == ds) & (tab["split"] == "train")]
    tids = np.array(d["trace_id"].unique(), dtype=object)
    rng.shuffle(tids)
    need, parts = minutes * 60, []
    for t in tids:
        g = d[d["trace_id"] == t].sort_values("idx")
        parts.append(g.iloc[:need])
        need -= len(parts[-1])
        if need <= 0:
            break
    return pd.concat(parts)


def adapt(base: lgb.Booster, local: pd.DataFrame, feats: list[str]) -> lgb.Booster:
    """Continue boosting from `base` on local data; the last 25% of each local trace is the stopping set."""
    local = local.sort_values(["trace_id", "idx"])
    pos_in_trace = local.groupby("trace_id").cumcount() / local.groupby("trace_id")["idx"].transform("size")
    fit_, stop = local[pos_in_trace < 0.75], local[pos_in_trace >= 0.75]
    if fit_["y_aligned"].nunique() < 2 or stop["y_aligned"].nunique() < 2:
        return base
    p = {**_params(fit_["y_aligned"].mean()), "learning_rate": 0.02, "min_data_in_leaf": 20}
    dtr = lgb.Dataset(fit_[feats], fit_["y_aligned"].astype(int))
    dva = lgb.Dataset(stop[feats], stop["y_aligned"].astype(int), reference=dtr)
    return lgb.train(p, dtr, 500, valid_sets=[dva], init_model=base,
                     callbacks=[lgb.early_stopping(50, verbose=False)])


def run(log=print) -> pd.DataFrame:
    tab = add_val_roles(pd.read_parquet(PROC_DIR / f"xd_table_{VARIANT}.parquet"))
    feats = json.load(open(PROC_DIR / "model_info.json"))["features"]
    stab, sfeats = shape_table(tab, feats)
    rng = np.random.default_rng(SEED)
    rows = []
    for ds in DATASETS:
        others = tuple(x for x in DATASETS if x != ds)
        te = stab[(stab["dataset"] == ds) & (stab["split"] == "test")].copy()
        base = fit(stab, sfeats, others)
        te["score_ml"] = base.predict(te[sfeats], num_threads=8)
        r = ap_with_ci(te, rng)
        rows.append({"test_dataset": ds, "setting": "lodo_shape", "site_minutes": 0, **r})
        log(f"transfer: {ds:10s} lodo shape-only      AP {r['ap_ml']:.3f} vs rhythm {r['ap_rhythm']:.3f} [{r['ap_diff_lo']:+.3f},{r['ap_diff_hi']:+.3f}]")
        for m in ADAPT_MIN:
            # repeat with different local samples: one draw of a few jobs is not a result
            aps = []
            for rep in range(N_REPS):
                local = site_minutes(stab, ds, m, np.random.default_rng(SEED + 1000 * rep + m))
                model = adapt(base, local, sfeats)
                te["score_ml"] = model.predict(te[sfeats], num_threads=8)
                if rep == 0:
                    r = ap_with_ci(te, rng, N_BOOT_SUB)
                aps.append(average_precision_score(te["y_aligned"], te["score_ml"]))
            # ap_ml / CI columns of adapted rows describe draw 0 only; the paper uses the 5-draw mean/range
            rows.append({"test_dataset": ds, "setting": "lodo_shape_adapted", "site_minutes": m,
                         **{f"draw0_{k}" if k.startswith("ap_") else k: v for k, v in r.items()},
                         "ap_rhythm": r["ap_rhythm"], "ap_ml_rep_mean": float(np.mean(aps)),
                         "ap_ml_rep_min": float(np.min(aps)), "ap_ml_rep_max": float(np.max(aps)), "reps": N_REPS})
            log(f"transfer: {ds:10s} + {m:3d} min of site AP mean {np.mean(aps):.3f} (range {np.min(aps):.3f}-{np.max(aps):.3f}, "
                f"{N_REPS} draws) vs rhythm {r['ap_rhythm']:.3f}")
        # in-domain reference with shape-only features
        model = fit(stab, sfeats, (ds,))
        te["score_ml"] = model.predict(te[sfeats], num_threads=8)
        r = ap_with_ci(te, rng)
        rows.append({"test_dataset": ds, "setting": "in_domain_shape", "site_minutes": np.nan, **r})
        log(f"transfer: {ds:10s} in-domain shape-only AP {r['ap_ml']:.3f} vs rhythm {r['ap_rhythm']:.3f}")
    out = pd.DataFrame(rows)
    out.round(4).to_csv(TABLES / f"transfer_{VARIANT}.csv", index=False)
    return out


if __name__ == "__main__":
    run()
