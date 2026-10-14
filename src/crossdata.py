"""Paper track, step 2D: does the control-aligned learned trigger beat rhythm replay across sites and GPUs?

Datasets (power normalised to "NLR-equivalent watts" = power x 2800 / node rated power, so the same
features, 10%/s ramp limit and drop rules mean the same fraction of rated power everywhere):
  nlr         NLR, 4 x H100 nodes, 5 Hz, MLPerf training + vLLM inference          (CC BY 4.0)
  elsayed     Elsayed et al. 2026, 8 x H100 / 8 x B200 nodes, NVML 1 s averaged     (CC BY-NC-ND per README)
  supercloud  MIT Supercloud subset, 2 x V100 nodes, 10 Hz instantaneous, real jobs (CC BY-NC-ND, research only)

Experiments, all scored on each dataset's own TEST split (whole jobs held out):
  in_domain   train on that dataset's train split, early-stop on its val split
  lodo        leave-one-dataset-out: train/early-stop on the OTHER datasets only
  pooled      train/early-stop on all datasets
Compared on the control-aligned target (src/aligned.py): learned LightGBM vs rhythm replay (no learning).
Metrics: average precision (AP) with a paired bootstrap over independent units (training job, or
inference hour block), and the readiness needed for a violation-cut target with the threshold chosen
on the test dataset's own validation split. For lodo this threshold is the only thing calibrated on
the held-out dataset (no training rows, no early stopping), and AP needs no threshold at all.
Decisions are made once per second (stride 5) for every source, so the comparison stays fair.
"""
from __future__ import annotations

import json

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from src.aligned import aligned_labels, hold_samples, lat_samples, rhythm_aligned_score, val_roles
from src.config import DT_S, PROC_DIR, REPORT_DIR, SEED
from src.features import trace_table
from src.load import load_traces
from src.regime import _arm, _down_violation_starts, _limiter
from src.simulate import NODE_RATED_W, SimParams

TABLES = REPORT_DIR / "tables"
STRIDE = 5
DATASETS = ("nlr", "elsayed", "supercloud")
N_BOOT = 1000  # whole-dataset intervals
N_BOOT_SUB = 1000  # per-workload intervals
TARGETS = (80.0, 90.0, 95.0)
# Sensor harmonisation: NLR and Elsayed H100/B200 power is NVML's ~1 s trailing average, Supercloud V100
# power is instantaneous. A 1 s trailing mean (5 samples at 5 Hz) puts Supercloud on the same footing.
# VARIANT "raw" skips it (kept for the record: 89% of Supercloud seconds then count as "violation coming").
VARIANT = "harmonized"
SMOOTH_SAMPLES = {"supercloud": 5}


# ---------------------------------------------------------------- data

def _all_traces() -> tuple[dict[str, np.ndarray], pd.DataFrame]:
    """Normalised power per trace + one meta table for all three datasets."""
    p_by: dict[str, np.ndarray] = {}
    metas = []
    tr, meta = load_traces(only_model=True)
    meta = meta.assign(dataset="nlr", rated_w=NODE_RATED_W)
    meta["unit"] = np.where(meta["phase"] == "training", "nlr_job_" + meta["job_id"].astype(str), meta["trace_id"])
    for tid, g in tr.groupby("trace_id"):
        p_by[tid] = g["power_w"].to_numpy(float)
    metas.append(meta[["trace_id", "dataset", "workload", "split", "unit", "rated_w"]])
    for name in ("elsayed", "supercloud"):
        t = pd.read_parquet(PROC_DIR / f"ext_{name}_traces.parquet", columns=["trace_id", "power_w"])
        m = pd.read_csv(PROC_DIR / f"ext_{name}_meta.csv", dtype={"job_id": str})
        m["unit"] = f"{name}_job_" + m["job_id"].astype(str)
        rated = dict(zip(m["trace_id"], m["rated_w"]))
        for tid, g in t.groupby("trace_id"):
            p = g["power_w"].to_numpy(float) * NODE_RATED_W / rated[tid]
            k = SMOOTH_SAMPLES.get(name, 1) if VARIANT == "harmonized" else 1
            p_by[tid] = pd.Series(p).rolling(k, min_periods=1).mean().to_numpy() if k > 1 else p
        metas.append(m.assign(dataset=name)[["trace_id", "dataset", "workload", "split", "unit", "rated_w"]])
    return p_by, pd.concat(metas, ignore_index=True)


def build_table(force: bool = False) -> pd.DataFrame:
    """Features + aligned label + rhythm-replay score for every trace, one row per second."""
    path = PROC_DIR / f"xd_table_{VARIANT}.parquet"
    if path.exists() and not force:
        return pd.read_parquet(path)
    sp = SimParams()
    p_by, meta = _all_traces()
    parts = []
    for r in meta.itertuples(index=False):
        p = p_by[r.trace_id]
        if len(p) < 400:
            continue
        df = trace_table(r.trace_id, p, stride=STRIDE)
        idx = df["idx"].to_numpy()
        df["y_aligned"] = aligned_labels(p, idx, sp)
        df["score_rhythm_aligned"] = rhythm_aligned_score(p, idx, df["period_s"].to_numpy(float), sp)
        df = df.drop(columns=[c for c in df.columns if c.startswith("y_") and c != "y_aligned"])
        df["dataset"], df["workload"], df["split"], df["unit"] = r.dataset, r.workload, r.split, r.unit
        parts.append(df.astype({c: "float32" for c in df.select_dtypes("float64").columns}))
    out = pd.concat(parts, ignore_index=True)
    out.to_parquet(path, index=False)
    meta.to_csv(PROC_DIR / "xd_meta.csv", index=False)
    return out


def add_val_roles(tab: pd.DataFrame) -> pd.DataFrame:
    """vrole = "es" (early stopping) or "thr" (threshold choice) for validation rows, split by unit
    within each (dataset, workload) so no validation row is used for both."""
    va = tab.loc[tab["split"] == "val", ["dataset", "workload", "unit"]]
    roles = val_roles(va, ["dataset", "workload"])
    tab["vrole"] = tab["unit"].map(roles).where(tab["split"] == "val", "")
    # bootstrap cluster: NLR inference hour blocks of one session are not independent -> one cluster per session
    inf = (tab["dataset"] == "nlr") & tab["workload"].str.startswith("inference")
    tab["cluster"] = np.where(inf, "nlr_session_" + tab["workload"], tab["unit"])
    return tab


# ---------------------------------------------------------------- model

def train(tab: pd.DataFrame, feats: list[str], train_sets: tuple[str, ...]) -> lgb.Booster:
    tr = tab[tab["dataset"].isin(train_sets) & (tab["split"] == "train")]
    va = tab[tab["dataset"].isin(train_sets) & (tab["split"] == "val") & (tab["vrole"] == "es")]
    # weight datasets equally so the biggest one (supercloud) does not drown the others
    w = tr["dataset"].map(1.0 / tr["dataset"].value_counts()).to_numpy()
    w = w / w.mean()
    pos = tr["y_aligned"].mean()
    params = {"objective": "binary", "learning_rate": 0.05, "num_leaves": 63, "min_data_in_leaf": 200,
              "feature_fraction": 0.8, "bagging_fraction": 0.8, "bagging_freq": 1, "lambda_l2": 1.0,
              "scale_pos_weight": float(np.sqrt((1 - pos) / pos)), "seed": SEED, "verbose": -1, "num_threads": 8}
    dtr = lgb.Dataset(tr[feats], tr["y_aligned"].astype(int), weight=w)
    dva = lgb.Dataset(va[feats], va["y_aligned"].astype(int), reference=dtr)
    return lgb.train(params, dtr, 3000, valid_sets=[dva], callbacks=[lgb.early_stopping(100, verbose=False)])


# ---------------------------------------------------------------- metrics

def ap_with_ci(d: pd.DataFrame, rng: np.random.Generator, n_boot: int = N_BOOT) -> dict[str, float]:
    """AP of learned vs rhythm and a paired unit-level bootstrap of the difference."""
    y, a, b = d["y_aligned"].to_numpy(), d["score_ml"].to_numpy(), d["score_rhythm_aligned"].to_numpy()
    out = {"ap_ml": average_precision_score(y, a), "ap_rhythm": average_precision_score(y, b),
           "pos_rate": y.mean(), "units": d["cluster"].nunique()}
    groups = list(d.groupby("cluster").indices.values())
    diffs = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(groups), len(groups))
        ii = np.concatenate([groups[k] for k in pick])
        if y[ii].min() == y[ii].max():
            continue
        diffs.append(average_precision_score(y[ii], a[ii]) - average_precision_score(y[ii], b[ii]))
    out["ap_diff"] = out["ap_ml"] - out["ap_rhythm"]
    out["ap_diff_lo"], out["ap_diff_hi"] = np.percentile(diffs, [2.5, 97.5])
    return out


def _sim_curve(d: pd.DataFrame, p_by: dict[str, np.ndarray], col: str, thrs: np.ndarray, sp: SimParams) -> pd.DataFrame:
    """Pooled violation cut and armed time for each threshold (decisions only at table rows)."""
    step = sp.safety * sp.ramp_limit_frac_per_s * NODE_RATED_W * DT_S
    limit = sp.ramp_limit_frac_per_s * NODE_RATED_W
    lat, hold = lat_samples(sp.actuator_latency_s), hold_samples(sp)
    acc = np.zeros((len(thrs), 4))  # violations, raw violations, armed samples, samples
    for tid, rows in d.groupby("trace_id").indices.items():
        p = p_by[tid]
        idx = d["idx"].to_numpy()[rows]
        sc = d[col].to_numpy()[rows]
        raw_v = len(_down_violation_starts(p, limit))
        for k, th in enumerate(thrs):
            trig = np.zeros(len(p), bool)
            trig[idx[sc >= th]] = True
            a = _arm(trig, lat, hold)
            out = _limiter(p, a, step)
            eng = a | (out > p + 1e-9)  # engaged = armed or still tapering a fill
            acc[k] += [len(_down_violation_starts(out, limit)), raw_v, eng.sum(), len(p)]
    return pd.DataFrame({"thr": thrs, "cut_pct": 100 * (1 - acc[:, 0] / np.maximum(acc[:, 1], 1)),
                         "armed_pct": 100 * acc[:, 2] / acc[:, 3]})


def readiness(val: pd.DataFrame, test: pd.DataFrame, p_by: dict[str, np.ndarray], sp: SimParams) -> list[dict]:
    """For each target: threshold chosen on val (lowest armed time reaching the target), scored on test."""
    rows = []
    for col, name in (("score_ml", "learned"), ("score_rhythm_aligned", "rhythm")):
        qs = np.unique(np.concatenate([np.linspace(0.0, 0.99, 60), 1 - np.geomspace(0.01, 0.001, 5)]))
        thrs = np.unique(np.quantile(val[col], qs))
        cv, ct = _sim_curve(val, p_by, col, thrs, sp), _sim_curve(test, p_by, col, thrs, sp)
        for tgt in TARGETS:
            ok = cv[cv["cut_pct"] >= tgt]
            k = ok["armed_pct"].idxmin() if len(ok) else cv["cut_pct"].idxmax()
            rows.append({"source": name, "target": tgt, "val_reached": bool(len(ok)),
                         "test_cut_pct": ct.loc[k, "cut_pct"], "test_armed_pct": ct.loc[k, "armed_pct"]})
    return rows


# ---------------------------------------------------------------- main

def run(log=print) -> dict[str, pd.DataFrame]:
    sp = SimParams()
    TABLES.mkdir(parents=True, exist_ok=True)
    log("crossdata: building table")
    tab = add_val_roles(build_table())
    feats = json.load(open(PROC_DIR / "model_info.json"))["features"]
    log(f"crossdata: rows={len(tab):,} " + str(tab.groupby(['dataset', 'split']).size().unstack().to_dict()))
    p_by, _ = _all_traces()
    rng = np.random.default_rng(SEED)
    ap_rows, rd_rows = [], []
    configs = {f"in_domain:{d}": (d,) for d in DATASETS}
    configs |= {f"lodo:{d}": tuple(x for x in DATASETS if x != d) for d in DATASETS}
    configs["pooled"] = DATASETS
    for cname, sets in configs.items():
        log(f"crossdata: training {cname} on {sets}")
        model = train(tab, feats, sets)
        targets = [cname.split(":")[1]] if ":" in cname else list(DATASETS)
        for ds in targets:
            te = tab[(tab["dataset"] == ds) & (tab["split"] == "test")].copy()
            va = tab[(tab["dataset"] == ds) & (tab["split"] == "val") & (tab["vrole"] == "thr")].copy()
            te["score_ml"] = model.predict(te[feats], num_threads=8)
            va["score_ml"] = model.predict(va[feats], num_threads=8)
            r = ap_with_ci(te, rng)
            ap_rows.append({"config": cname.split(":")[0], "test_dataset": ds, "workload": "all", **r})
            for wl, g in te.groupby("workload"):
                if g["y_aligned"].nunique() == 2 and g["cluster"].nunique() >= 2:
                    ap_rows.append({"config": cname.split(":")[0], "test_dataset": ds, "workload": wl, **ap_with_ci(g, rng, N_BOOT_SUB)})
            for rr in readiness(va, te, p_by, sp):
                rd_rows.append({"config": cname.split(":")[0], "test_dataset": ds, **rr})
            log(f"crossdata:   {cname:22s} -> {ds:10s} AP learned={r['ap_ml']:.3f} rhythm={r['ap_rhythm']:.3f} "
                f"diff={r['ap_diff']:+.3f} [{r['ap_diff_lo']:+.3f}, {r['ap_diff_hi']:+.3f}] units={r['units']}")
    ap, rd = pd.DataFrame(ap_rows), pd.DataFrame(rd_rows)
    ap.round(4).to_csv(TABLES / f"crossdata_ap_{VARIANT}.csv", index=False)
    rd.round(3).to_csv(TABLES / f"crossdata_readiness_{VARIANT}.csv", index=False)
    return {"ap": ap, "readiness": rd}


if __name__ == "__main__":
    run()
