"""Paper track, step 1: when does a learned predictor pay off for power smoothing?

The base simulation (src/simulate.py) treats arming the actuator as free, so any alarm source that
fires often enough looks as good as the ML model. Here readiness has a price:

  overhead = fill energy                                  (power added to hide a fall)
           + standby_frac x rated power x time armed     (hot battery inverter / pre-warmed filler)
           + start_s x rated power x arming episodes      (one-off cost each time the actuator wakes)

all expressed as % of the job's own GPU energy.

Arming sources compared (each swept over its threshold):
  ml_alarm         LightGBM drop classifier score >= threshold
  rhythm_alarm     "repeat the last cycle" fall score >= threshold (no learning)
  ml_forecast      LightGBM forecast says power falls > f x rated within 5 s
  rhythm_forecast  rhythm forecast says the same
  oracle           perfect foresight: armed exactly in time for every real violation (upper bound)
Fixed references: always_on (always armed, pays standby all the time), reactive (armed after a
measured fast fall), always_burn (80% floor, no standby).

Operating points are chosen on VALIDATION traces (cheapest point that removes >= TARGET_CUT of
violations there), then scored on TEST. Uncertainty: paired bootstrap over independent units
(training job; for inference, one-hour blocks, since each inference workload is a single session).
"""
from __future__ import annotations

import json
from dataclasses import dataclass

import lightgbm as lgb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from numba import njit

from src.config import DT_S, FIG_DIR, PROC_DIR, REPORT_DIR, SEED
from src.features import FS
from src.load import load_traces
from src.plotstyle import apply_style
from src.aligned import lat_samples
from src.simulate import NODE_RATED_W, SimParams

TABLES = REPORT_DIR / "tables"
TARGET_CUT = 80.0  # % of raw down-ramp violations a strategy must remove to count as "doing the job"
LATENCIES_S = (0.0, 0.2, 0.5, 1.0, 2.0, 3.0)
STANDBY_FRACS = (0.0, 0.005, 0.01, 0.02, 0.05, 0.10)  # standby draw while armed, fraction of rated power
START_S = (0.0, 2.0, 10.0)  # energy per arming episode, in seconds of rated power
SOURCES = ("ml_alarm", "rhythm_alarm", "ml_forecast", "rhythm_forecast", "ml_aligned", "rhythm_aligned")
N_BOOT = 1000


@dataclass
class Unit:
    """One trace with everything needed to simulate it."""
    tid: str
    unit: str  # independence unit for the bootstrap
    workload: str
    p: np.ndarray
    signals: dict[str, np.ndarray]  # per-sample arming score per source (NaN where not predicted)


# ---------------------------------------------------------------- fast kernels

@njit(cache=True)
def _limiter(p: np.ndarray, armed: np.ndarray, step_w: float) -> np.ndarray:
    """Same logic as simulate.limiter: ramp-down limiter that only adds power."""
    out = p.copy()
    filling = False
    for t in range(1, len(p)):
        if armed[t] or filling:
            v = max(p[t], out[t - 1] - step_w)
            out[t] = v
            filling = v > p[t] + 1e-9
        else:
            out[t] = p[t]
    return out


def _arm(trig: np.ndarray, lat: int, hold: int) -> np.ndarray:
    """armed[t] = a trigger fired in [t - lat - hold + 1, t - lat]: each trigger arms exactly `hold`
    samples, the half-open window [trigger + lat, trigger + lat + hold)."""
    n = len(trig)
    c = np.concatenate([[0], np.cumsum(trig.astype(np.int64))])
    t = np.arange(n)
    hi = np.clip(t - lat + 1, 0, n)
    lo = np.clip(t - lat - hold + 1, 0, n)
    return (c[hi] - c[lo]) > 0


def _down_violation_starts(out: np.ndarray, limit_w: float) -> np.ndarray:
    r = np.zeros(len(out))
    r[FS:] = out[FS:] - out[:-FS]
    down = -r > limit_w
    return np.flatnonzero(down & ~np.concatenate([[False], down[:-1]]))


def _stats(p: np.ndarray, out: np.ndarray, armed: np.ndarray | None, limit_w: float) -> np.ndarray:
    """[violations, fill_J, armed_s, episodes, base_J, hours]

    "Armed" time counts every sample where the actuator is engaged: explicitly armed, or still tapering
    a fill after the arming window ended (the limiter keeps filling until it meets the load)."""
    v = len(_down_violation_starts(out, limit_w))
    fill = np.clip(out - p, 0, None).sum() * DT_S
    if armed is None:
        a_s, ep = 0.0, 0
    else:
        eng = armed | (out > p + 1e-9)
        a_s = eng.sum() * DT_S
        ep = int(eng[0]) + int(np.sum(eng[1:] & ~eng[:-1]))
    return np.array([v, fill, a_s, ep, p.sum() * DT_S, len(p) * DT_S / 3600])


# ---------------------------------------------------------------- data

def _unit_id(tid: str, meta_row: pd.Series) -> str:
    """Bootstrap cluster: the training job, or the whole inference session (its hour blocks are not
    independent: train, val and test blocks come from the same continuous session)."""
    return f"job_{meta_row['job_id']}" if meta_row["phase"] == "training" else f"session_{meta_row['workload']}"


def _val_predictions() -> pd.DataFrame:
    """Re-create LightGBM val-set outputs from the saved boosters (the main pipeline only saves test)."""
    info = json.load(open(PROC_DIR / "model_info.json"))
    feats = info["features"]
    val = pd.read_parquet(PROC_DIR / "table_val.parquet")
    X = val[feats]
    out = val[["trace_id", "idx", "workload", "p", "rhythm_1s", "rhythm_5s", "rhythm_fall5_frac"]].copy()
    out["score_lightgbm"] = lgb.Booster(model_file=str(PROC_DIR / "lgb_clf.txt")).predict(X, num_threads=8)
    for h in (1, 5):
        b = lgb.Booster(model_file=str(PROC_DIR / f"lgb_reg_{h}s.txt"))
        out[f"lightgbm_{h}s"] = val["p"].to_numpy() + b.predict(X, num_threads=8)
    return out.rename(columns={"rhythm_fall5_frac": "score_rhythm_alarm"})


def load_units(split: str) -> list[Unit]:
    """Validation uses only the "thr" half of units (the "es" half early-stopped the aligned models)."""
    traces, meta = load_traces(only_model=True)
    meta = meta[meta["split"] == split].set_index("trace_id")
    if split == "val":
        roles = json.load(open(PROC_DIR / "val_roles_nlr.json"))
        meta = meta[meta.index.map(roles.get) == "thr"]
    if split == "test":
        pr = pd.read_parquet(PROC_DIR / "test_predictions.parquet")
    else:
        pr = _val_predictions()
    # control-aligned scores from src/aligned.py: one learned model and one rhythm replay per latency
    for L in LATENCIES_S:
        al = pd.read_parquet(PROC_DIR / f"aligned_scores_{split}_L{L:g}.parquet").rename(
            columns={"score_aligned": f"ml_aligned@{L:g}", "score_rhythm_aligned": f"rhythm_aligned@{L:g}"})
        pr = pr.merge(al, on=["trace_id", "idx"], how="left")
    pr_g = dict(tuple(pr.groupby("trace_id", sort=False)))
    units = []
    for tid, g in traces[traces["trace_id"].isin(meta.index)].groupby("trace_id", sort=True):
        p = g["power_w"].to_numpy(dtype=float)
        q = pr_g[tid]
        idx = q["idx"].to_numpy()

        def place(x: np.ndarray) -> np.ndarray:
            a = np.full(len(p), np.nan)
            a[idx] = x
            return a

        sig = {
            "ml_alarm": place(q["score_lightgbm"].to_numpy()),
            "rhythm_alarm": place(q["score_rhythm_alarm"].to_numpy()),
            # forecast sources: predicted fall over the next 1-5 s as a fraction of rated power
            "ml_forecast": place((q["p"].to_numpy() - np.minimum(q["lightgbm_1s"], q["lightgbm_5s"]).to_numpy()) / NODE_RATED_W),
            "rhythm_forecast": place((q["p"].to_numpy() - np.minimum(q["rhythm_1s"], q["rhythm_5s"]).to_numpy()) / NODE_RATED_W),
        }
        for L in LATENCIES_S:
            for src in ("ml_aligned", "rhythm_aligned"):
                sig[f"{src}@{L:g}"] = place(q[f"{src}@{L:g}"].to_numpy())
        m = meta.loc[tid]
        units.append(Unit(tid, _unit_id(tid, m), m["workload"], p, sig))
    return units


def thresholds(units: list[Unit], n: int = 30, dense: bool = False) -> dict[str, np.ndarray]:
    """Threshold grid per source from validation score quantiles. dense=True: 200 quantiles, used at
    the headline latency where "least engaged time for a removal level" needs fine resolution."""
    # full range: from "always armed" (lowest score) to the extreme upper tail
    if dense:
        qs = np.unique(np.concatenate([np.linspace(0.0, 0.995, 200), 1 - np.geomspace(0.005, 0.0002, 10)]))
    else:
        qs = np.concatenate([[0.0], np.linspace(0.05, 0.45, 5), 1 - np.geomspace(0.5, 0.0005, n)])
    grid = {}
    for s in units[0].signals:  # every source, and every latency-specific aligned source
        x = np.concatenate([u.signals[s][np.isfinite(u.signals[s])] for u in units])
        grid[s] = np.unique(np.quantile(x, qs))
    return grid


# ---------------------------------------------------------------- simulation

HEADLINE_LATENCY_S = 1.0


def simulate(units: list[Unit], grid: dict[str, np.ndarray], sp: SimParams,
             dense_grid: dict[str, np.ndarray] | None = None) -> pd.DataFrame:
    """Per (unit trace, strategy, threshold, latency): raw counts. Costs are applied later, cheaply."""
    step = sp.safety * sp.ramp_limit_frac_per_s * NODE_RATED_W * DT_S
    limit = sp.ramp_limit_frac_per_s * NODE_RATED_W
    hold = int(round(sp.arm_hold_s / DT_S))
    rows = []
    for u in units:
        p = u.p
        raw_v = len(_down_violation_starts(p, limit))
        base = dict(tid=u.tid, unit=u.unit, workload=u.workload, raw_violations=raw_v)
        always = np.ones(len(p), bool)
        rows.append({**base, "strategy": "always_on", "thr": np.nan, "latency_s": np.nan,
                     **_named(_stats(p, _limiter(p, always, step), always, limit))})
        rp = pd.Series(p).rolling(int(sp.peak_window_s / DT_S), min_periods=1).max().to_numpy()
        rows.append({**base, "strategy": "always_burn", "thr": np.nan, "latency_s": np.nan,
                     **_named(_stats(p, np.maximum(p, sp.floor_frac * rp), None, limit))})
        fall = np.zeros(len(p), bool)
        fall[1:] = (p[:-1] - p[1:]) > step
        starts = _down_violation_starts(p, limit)
        for L in LATENCIES_S:
            lat = lat_samples(L)
            a = _arm(fall, lat, hold)
            rows.append({**base, "strategy": "reactive", "thr": np.nan, "latency_s": L,
                         **_named(_stats(p, _limiter(p, a, step), a, limit))})
            # oracle: trigger so the limiter is engaged 1 s before each real violation starts. A fill that
            # ends between drops can itself cause a new violation, so keep adding triggers for any
            # violation left in the output until none remain (perfect foresight of the controlled output).
            trig = np.zeros(len(p), bool)
            trig[np.clip(starts - FS - lat, 0, len(p) - 1)] = True
            for _ in range(10):
                a = _arm(trig, lat, hold)
                left = _down_violation_starts(_limiter(p, a, step), limit)
                if len(left) == 0:
                    break
                trig[np.clip(left - FS - lat, 0, len(p) - 1)] = True
            rows.append({**base, "strategy": "oracle", "thr": np.nan, "latency_s": L,
                         **_named(_stats(p, _limiter(p, a, step), a, limit))})
            for s in SOURCES:
                key = f"{s}@{L:g}" if f"{s}@{L:g}" in u.signals else s  # aligned sources: model for this latency
                sig = np.nan_to_num(u.signals[key], nan=-np.inf)
                g = dense_grid if (dense_grid is not None and L == HEADLINE_LATENCY_S) else grid
                for th in g[key]:
                    a = _arm(sig >= th, lat, hold)
                    rows.append({**base, "strategy": s, "thr": th, "latency_s": L,
                                 **_named(_stats(p, _limiter(p, a, step), a, limit))})
    return pd.DataFrame(rows)


def _named(v: np.ndarray) -> dict[str, float]:
    return dict(zip(["violations", "fill_J", "armed_s", "episodes", "base_J", "hours"], v))


def costed(df: pd.DataFrame, standby: float, start_s: float) -> pd.DataFrame:
    """Add overhead_J for a given readiness cost."""
    d = df.copy()
    d["overhead_J"] = d["fill_J"] + standby * NODE_RATED_W * d["armed_s"] + start_s * NODE_RATED_W * d["episodes"]
    return d


def summarize(d: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Pool traces: % violations removed and overhead as % of job energy."""
    g = d.groupby(keys, dropna=False)[["violations", "raw_violations", "overhead_J", "base_J", "armed_s", "hours", "episodes"]].sum()
    g["cut_pct"] = 100 * (1 - g["violations"] / g["raw_violations"])
    g["overhead_pct"] = 100 * g["overhead_J"] / g["base_J"]
    g["armed_pct"] = 100 * g["armed_s"] / (g["hours"] * 3600)
    g["episodes_per_h"] = g["episodes"] / g["hours"]
    return g.reset_index()


def pick_on_val(val_s: pd.DataFrame) -> pd.DataFrame:
    """Per (strategy, latency): cheapest threshold whose VALIDATION cut >= TARGET_CUT (else best cut)."""
    picks = []
    for (s, L), g in val_s.groupby(["strategy", "latency_s"], dropna=False):
        ok = g[g["cut_pct"] >= TARGET_CUT]
        r = ok.nsmallest(1, "overhead_pct") if len(ok) else g.nlargest(1, "cut_pct")
        picks.append(r)
    return pd.concat(picks)[["strategy", "latency_s", "thr"]]


def _match(test_df: pd.DataFrame, picks: pd.DataFrame) -> pd.DataFrame:
    """Rows of test_df at the validation-chosen operating points (fixed strategies match on NaN thr)."""
    key = ["strategy", "latency_s", "thr"]
    # val and test share one threshold grid, so exact float equality is safe; NaN -> sentinel to merge
    t = test_df.copy()
    p = picks.copy()
    for d in (t, p):
        for c in ("latency_s", "thr"):
            d[c] = d[c].fillna(-1.0)
    out = t.merge(p, on=key)
    for c in ("latency_s", "thr"):
        out[c] = out[c].replace(-1, np.nan)
    return out


def bootstrap_diff(rows: pd.DataFrame, a: str, b: str, metric: str, rng: np.random.Generator) -> tuple[float, float, float]:
    """Paired bootstrap over independent units of (metric of a) - (metric of b). Returns mean, lo, hi."""
    pa = rows[rows["strategy"] == a].groupby("unit")[["violations", "raw_violations", "overhead_J", "base_J"]].sum()
    pb = rows[rows["strategy"] == b].groupby("unit")[["violations", "raw_violations", "overhead_J", "base_J"]].sum()
    units = pa.index.intersection(pb.index).to_numpy()

    def m(x: pd.DataFrame) -> float:
        if metric == "cut_pct":
            return 100 * (1 - x["violations"].sum() / max(x["raw_violations"].sum(), 1))
        return 100 * x["overhead_J"].sum() / x["base_J"].sum()

    point = m(pa.loc[units]) - m(pb.loc[units])
    boots = []
    for _ in range(N_BOOT):
        s = rng.choice(units, len(units), replace=True)
        boots.append(m(pa.loc[s]) - m(pb.loc[s]))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return point, lo, hi


# ---------------------------------------------------------------- main

def run(log=print) -> dict[str, pd.DataFrame]:
    sp = SimParams()
    TABLES.mkdir(parents=True, exist_ok=True)
    log("regime: loading val/test units")
    val_u, test_u = load_units("val"), load_units("test")
    grid, dense = thresholds(val_u), thresholds(val_u, dense=True)
    log(f"regime: simulating {len(val_u)} val + {len(test_u)} test traces")
    val_raw, test_raw = simulate(val_u, grid, sp, dense), simulate(test_u, grid, sp, dense)
    test_raw.to_parquet(PROC_DIR / "regime_test_raw.parquet", index=False)
    val_raw.to_parquet(PROC_DIR / "regime_val_raw.parquet", index=False)

    keys = ["strategy", "latency_s", "thr"]
    rng = np.random.default_rng(SEED)
    cells, ci_rows = [], []
    for start in START_S:
        for sb in STANDBY_FRACS:
            vs = summarize(costed(val_raw, sb, start), keys)
            picks = pick_on_val(vs)
            tc = costed(test_raw, sb, start)
            chosen = _match(tc, picks)
            ts = summarize(chosen, keys)
            vsel = _match(vs, picks)  # validation metrics at the validation-chosen points
            for L in LATENCIES_S:
                # the winner is decided on VALIDATION, then reported with its TEST metrics
                cand = vsel[((vsel["latency_s"] == L) | vsel["latency_s"].isna()) & (vsel["strategy"] != "oracle")]
                ok = cand[cand["cut_pct"] >= TARGET_CUT]
                best = ok.nsmallest(1, "overhead_pct") if len(ok) else cand.nlargest(1, "cut_pct")
                w = best["strategy"].iloc[0]
                wt = ts[(ts["strategy"] == w) & ((ts["latency_s"] == L) | ts["latency_s"].isna())]
                row = {"start_s": start, "standby_pct": 100 * sb, "latency_s": L,
                       "winner": w, "winner_overhead_pct": wt["overhead_pct"].iloc[0],
                       "winner_cut_pct": wt["cut_pct"].iloc[0]}
                for s in (*SOURCES, "reactive", "always_on", "always_burn", "oracle"):
                    r = ts[(ts["strategy"] == s) & ((ts["latency_s"] == L) | ts["latency_s"].isna())]
                    if len(r):
                        row[f"{s}_cut"] = r["cut_pct"].iloc[0]
                        row[f"{s}_overhead"] = r["overhead_pct"].iloc[0]
                cells.append(row)
                # the paper's key paired comparison: learned vs simple alarm at the same costs
                for a_, b_ in (("ml_alarm", "rhythm_alarm"), ("ml_aligned", "rhythm_aligned")):
                    sub = chosen[(chosen["latency_s"] == L) & chosen["strategy"].isin([a_, b_])]
                    for metric in ("overhead_pct", "cut_pct"):
                        pt, lo, hi = bootstrap_diff(sub, a_, b_, metric, rng)
                        ci_rows.append({"start_s": start, "standby_pct": 100 * sb, "latency_s": L, "pair": f"{a_}-{b_}",
                                        "metric": metric, "ml_minus_rhythm": pt, "ci_lo": lo, "ci_hi": hi})
    regime = pd.DataFrame(cells)
    ci = pd.DataFrame(ci_rows)
    regime.round(3).to_csv(TABLES / "regime_map.csv", index=False)
    ci.round(3).to_csv(TABLES / "regime_ml_vs_rhythm_ci.csv", index=False)

    targets_table(val_raw, test_raw).round(3).to_csv(TABLES / "regime_targets.csv", index=False)
    armed_needed(test_raw).round(2).to_csv(TABLES / "regime_armed_needed.csv", index=False)

    # Pareto (descriptive, full threshold sweep on test, zero readiness cost, 1 s latency)
    pareto = summarize(costed(test_raw, 0.0, 0.0), keys)
    pareto.round(4).to_csv(TABLES / "regime_pareto_test.csv", index=False)
    plot_pareto(pareto)
    plot_regime(regime)
    log(regime[(regime["start_s"] == 0)].pivot(index="standby_pct", columns="latency_s", values="winner").to_string())
    return {"regime": regime, "ci": ci, "pareto": pareto}


def targets_table(val_raw: pd.DataFrame, test_raw: pd.DataFrame, latency: float = 1.0,
                  targets: tuple[float, ...] = (80.0, 90.0, 95.0), standby: tuple[float, ...] = (0.0, 0.02, 0.05)) -> pd.DataFrame:
    """For each violation-cut target: the validation-chosen operating point of every source, scored on
    test, plus a paired unit bootstrap of learned-aligned minus rhythm-aligned cut."""
    global TARGET_CUT
    keys = ["strategy", "latency_s", "thr"]
    rng = np.random.default_rng(SEED)
    rows, keep = [], TARGET_CUT
    for target in targets:
        TARGET_CUT = target
        for sb in standby:
            picks = pick_on_val(summarize(costed(val_raw, sb, 0.0), keys))
            ch = _match(costed(test_raw, sb, 0.0), picks)
            ts = summarize(ch, keys)
            for s in (*SOURCES, "always_on", "oracle"):
                r = ts[(ts["strategy"] == s) & ((ts["latency_s"] == latency) | ts["latency_s"].isna())]
                rows.append({"target": target, "standby_pct": 100 * sb, "strategy": s, "test_cut_pct": r["cut_pct"].iloc[0],
                             "test_overhead_pct": r["overhead_pct"].iloc[0], "armed_pct": r["armed_pct"].iloc[0]})
            sub = ch[(ch["latency_s"] == latency) & ch["strategy"].isin(["ml_aligned", "rhythm_aligned"])]
            pt, lo, hi = bootstrap_diff(sub, "ml_aligned", "rhythm_aligned", "cut_pct", rng)
            rows.append({"target": target, "standby_pct": 100 * sb, "strategy": "diff_cut_ml_minus_rhythm_aligned",
                         "test_cut_pct": pt, "test_overhead_pct": lo, "armed_pct": hi})
    TARGET_CUT = keep
    return pd.DataFrame(rows)


def armed_needed(test_raw: pd.DataFrame, latency: float = 1.0, targets: tuple[float, ...] = (80.0, 90.0, 95.0),
                 sources: tuple[str, ...] = ("ml_aligned", "rhythm_aligned", "ml_alarm"), n_boot: int = 1000) -> pd.DataFrame:
    """Least engaged time (% of time) at which each source reaches a violation-removal level on test,
    with a paired bootstrap over independent units of the learned-minus-rhythm difference.
    Descriptive (full threshold sweep), complementing the validation-chosen operating points."""
    d = test_raw[(test_raw["latency_s"] == latency) & test_raw["strategy"].isin(sources)]
    cols = ["violations", "raw_violations", "armed_s", "hours"]
    per = d.groupby(["unit", "strategy", "thr"])[cols].sum()
    units = per.index.get_level_values("unit").unique().to_numpy()
    per_u = {u: per.xs(u, level="unit") for u in units}

    def need(sel: np.ndarray) -> dict[tuple[str, float], float]:
        agg = sum((per_u[u] for u in sel[1:]), per_u[sel[0]].copy()) if len(sel) > 1 else per_u[sel[0]]
        cut = 100 * (1 - agg["violations"] / agg["raw_violations"].clip(lower=1))
        arm = 100 * agg["armed_s"] / (agg["hours"] * 3600)
        out = {}
        for s in sources:
            for t in targets:
                ok = arm.loc[s][cut.loc[s] >= t]
                out[(s, t)] = float(ok.min()) if len(ok) else 100.0
        return out

    point = need(units)
    rng = np.random.default_rng(SEED)
    boots = [need(rng.choice(units, len(units), replace=True)) for _ in range(n_boot)]
    rows = []
    for t in targets:
        r = {"target": t, **{f"{s}_armed": point[(s, t)] for s in sources}}
        for other in ("rhythm_aligned", "ml_alarm"):
            diffs = [b[("ml_aligned", t)] - b[(other, t)] for b in boots]
            r[f"diff_vs_{other}"] = point[("ml_aligned", t)] - point[(other, t)]
            r[f"diff_vs_{other}_lo"], r[f"diff_vs_{other}_hi"] = np.percentile(diffs, [2.5, 97.5])
        rows.append(r)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- plots

SRC_STYLE = {
    "ml_alarm": ("#c2410c", "Learned alarm (LightGBM)"),
    "rhythm_alarm": ("#2563eb", "Rhythm alarm (no learning)"),
    "ml_forecast": ("#ea580c", "Learned forecast trigger"),
    "rhythm_forecast": ("#60a5fa", "Rhythm forecast trigger"),
    "ml_aligned": ("#7f1d1d", "Learned, control-aligned target"),
    "rhythm_aligned": ("#1e3a8a", "Rhythm replay, control-aligned target"),
}
WIN_COLOR = {"ml_aligned": "#7f1d1d", "rhythm_aligned": "#1e3a8a", "ml_alarm": "#c2410c", "ml_forecast": "#f59e0b", "rhythm_alarm": "#2563eb",
             "rhythm_forecast": "#60a5fa", "always_on": "#16a34a", "reactive": "#a855f7", "always_burn": "#6b7280"}
WIN_LABEL = {"ml_aligned": "Learned aligned", "rhythm_aligned": "Rhythm aligned", "ml_alarm": "Learned alarm", "ml_forecast": "Learned forecast", "rhythm_alarm": "Rhythm alarm",
             "rhythm_forecast": "Rhythm forecast", "always_on": "Always-on limiter", "reactive": "Reactive",
             "always_burn": "Always burn"}


def plot_pareto(par: pd.DataFrame, latency: float = 1.0) -> None:
    """Violations removed vs fraction of time the actuator must be armed: the cost driver of readiness."""
    apply_style()
    fig, ax = plt.subplots(figsize=(8, 5))
    for s, (c, lab) in SRC_STYLE.items():
        g = par[(par["strategy"] == s) & (par["latency_s"] == latency)].sort_values("armed_pct")
        ax.plot(g["armed_pct"], g["cut_pct"], "-o", ms=3, color=c, label=lab)
    for s, mk, lab in [("oracle", "*", "Oracle (perfect foresight)"), ("reactive", "s", "Reactive")]:
        g = par[(par["strategy"] == s) & (par["latency_s"] == latency)]
        ax.scatter(g["armed_pct"], g["cut_pct"], marker=mk, s=140, color="black" if s == "oracle" else "#a855f7", label=lab, zorder=4)
    g = par[par["strategy"] == "always_on"]
    ax.scatter(g["armed_pct"], g["cut_pct"], marker="D", s=80, color="#16a34a", label="Always-on limiter", zorder=4)
    ax.set_xscale("log")
    ax.set_xlabel("Time the actuator is armed (% of time, log scale)")
    ax.set_ylabel("Grid ramp violations removed (%)")
    ax.axhline(TARGET_CUT, color="grey", lw=0.8, ls="--")
    ax.set_title(f"How much readiness each trigger needs (test traces, {latency:g} s actuator latency)", loc="left")
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "regime_pareto.png", dpi=140)
    plt.close(fig)


def plot_regime(reg: pd.DataFrame) -> None:
    """Winner per (actuator latency, standby cost), one panel per start-up cost."""
    apply_style()
    starts = sorted(reg["start_s"].unique())
    fig, axes = plt.subplots(1, len(starts), figsize=(5.2 * len(starts), 4.4), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, st in zip(axes, starts):
        g = reg[reg["start_s"] == st]
        lats = sorted(g["latency_s"].unique())
        sbs = sorted(g["standby_pct"].unique())
        for i, sb in enumerate(sbs):
            for j, L in enumerate(lats):
                r = g[(g["standby_pct"] == sb) & (g["latency_s"] == L)].iloc[0]
                ok = r["winner_cut_pct"] >= TARGET_CUT
                ax.add_patch(plt.Rectangle((j, i), 1, 1, color=WIN_COLOR.get(r["winner"], "#999"), alpha=0.85 if ok else 0.3))
                ax.text(j + 0.5, i + 0.5, f"{WIN_LABEL.get(r['winner'], r['winner'])}\n{r['winner_overhead_pct']:.1f}%",
                        ha="center", va="center", fontsize=6.5, color="white" if ok else "black")
        ax.set_xlim(0, len(lats))
        ax.set_ylim(0, len(sbs))
        ax.set_xticks(np.arange(len(lats)) + 0.5, [f"{x:g}" for x in lats])
        ax.set_yticks(np.arange(len(sbs)) + 0.5, [f"{x:g}" for x in sbs])
        ax.set_xlabel("actuator latency (s)")
        ax.set_title(f"start-up cost {st:g} s of rated power", loc="left", fontsize=10)
    axes[0].set_ylabel("standby draw while armed (% of rated)")
    fig.suptitle(f"Cheapest strategy that removes >= {TARGET_CUT:.0f}% of violations (chosen on validation, scored on test)", x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "regime_map.png", dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    run()
