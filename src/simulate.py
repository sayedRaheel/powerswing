"""Step 7: smoothing simulation on test traces, then scale-up to a 100 MW site.

Fill-type strategies only ADD power on top of the real load (filler GPU work or battery discharge):
  raw              no smoothing
  always_burn      hold power at >= FLOOR_FRAC x recent peak (rolling PEAK_WINDOW_S max) at all times
  predictive       a ramp-down limiter armed only when the models predict a fall: the drop-warning
                   classifier alarms, OR the LightGBM forecast says power will fall by more than
                   FORECAST_TRIGGER_FRAC of peak within the next 5 s. The actuator needs
                   ACTUATOR_LATENCY_S to engage, so a trigger at time a protects from a + latency until
                   a + latency + ARM_HOLD_S. While engaged, output = max(load, previous output - allowed
                   step): the fill tapers off at the grid ramp limit instead of vanishing.
  predictive_preramp  same triggers, but the GPU power cap also starts lowering output gradually toward the
                   forecast level BEFORE the drop arrives. Less filler energy is burned, but some real work
                   is deferred (reported as deferred_pct: the job runs slightly longer).
Reference strategies (not in the brief, added so the comparison is honest):
  reactive         same limiter, armed only after a fast fall is measured (no forecast) + same latency.
  always_on_limiter limiter permanently armed. Needs no prediction at all but assumes an actuator that is
                   always ready (e.g. firmware power smoothing or an always-on battery inverter).

Ramp metrics use a 1 s window: ramp(t) = |out(t) - out(t - 1 s)| per second.
A violation is a contiguous run of samples whose downward ramp exceeds the grid limit
(default 10% of peak per second). "Peak" for a node is its rated GPU power, 4 x 700 W = 2.8 kW.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import DT_S, FIG_DIR, PROC_DIR, REPORT_DIR, SEED
from src.features import FS
from src.load import load_traces
from src.plotstyle import COLORS, WORKLOAD_LABEL, apply_style

TABLES = REPORT_DIR / "tables"


@dataclass
class SimParams:
    ramp_limit_frac_per_s: float = 0.10  # grid limit, fraction of peak per second
    floor_frac: float = 0.80  # always-burn floor, fraction of recent peak
    peak_window_s: float = 60.0  # "recent peak" window for always-burn
    actuator_latency_s: float = 1.0  # time for fill / storage to engage after a decision
    arm_hold_s: float = 6.0  # how long one alarm keeps the limiter armed
    safety: float = 0.9  # limiter ramps at 90% of the grid limit
    forecast_trigger_frac: float = 0.15  # forecast fall (fraction of peak) within 5 s that arms the limiter
    site_mw: float = 100.0
    price_per_mwh: float = 80.0
    site_instances: int = 400  # node traces sampled to build the randomly offset site
    site_hours: float = 2.0  # length of the simulated site window


STRATEGIES = ("raw", "always_burn", "predictive", "predictive_preramp", "reactive", "always_on_limiter")


NODE_RATED_W = 4 * 700.0  # 4 x H100 SXM at 700 W TDP: known in advance, so decisions stay causal


def node_peak(p: np.ndarray | None = None) -> float:
    """Reference peak for a node. Uses the fixed rating, never the trace's own (future) maximum."""
    return NODE_RATED_W


def limiter(p: np.ndarray, armed: np.ndarray, step_w: float) -> np.ndarray:
    """Ramp-down limiter that only adds power. Engages when armed, then tapers out on its own."""
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


def preramp_limiter(p: np.ndarray, armed: np.ndarray, target: np.ndarray, step_w: float) -> np.ndarray:
    """Limiter plus a pre-emptive power cap.

    While armed, a cap descends from the current output toward the forecast level at the allowed rate,
    so part of a coming drop is taken early (real work is deferred, not wasted). When a drop arrives the
    limiter fills whatever is left. When the arming lapses the cap is released at the allowed rate.
    """
    out = p.copy()
    cap = np.inf
    filling = False
    for t in range(1, len(p)):
        prev = out[t - 1]
        if armed[t]:
            start = prev if not np.isfinite(cap) else min(cap, prev)
            cap = max(start - step_w, target[t])
        elif np.isfinite(cap):
            cap += step_w
            if cap >= p[t]:
                cap = np.inf
        v = min(p[t], cap)
        if armed[t] or filling:
            v = max(v, prev - step_w)
        out[t] = v
        filling = v > p[t] + 1e-9
    return out


def _arm_from_triggers(trig: np.ndarray, latency: int, hold: int) -> np.ndarray:
    """armed[t] = some trigger fired in [t - latency - hold, t - latency]."""
    n = len(trig)
    c = np.concatenate([[0], np.cumsum(trig.astype(int))])
    t = np.arange(n)
    hi = np.clip(t - latency + 1, 0, n)
    lo = np.clip(t - latency - hold, 0, n)
    return (c[hi] - c[lo]) > 0


def apply_strategy(name: str, p: np.ndarray, alarm: np.ndarray, sp: SimParams,
                   fc_min: np.ndarray | None = None) -> np.ndarray:
    """alarm: drop-classifier alarms per sample. fc_min: lowest LightGBM forecast over the next 5 s."""
    peak = node_peak(p)
    step = sp.safety * sp.ramp_limit_frac_per_s * peak * DT_S
    lat = int(round(sp.actuator_latency_s / DT_S))
    hold = int(round(sp.arm_hold_s / DT_S))
    if name == "raw":
        return p.copy()
    if name == "always_burn":
        rp = pd.Series(p).rolling(int(sp.peak_window_s / DT_S), min_periods=1).max().to_numpy()
        return np.maximum(p, sp.floor_frac * rp)
    if name in ("predictive", "predictive_preramp"):
        fc = np.where(np.isfinite(fc_min), fc_min, p) if fc_min is not None else p
        trig = alarm | ((p - fc) > sp.forecast_trigger_frac * peak)
        armed = _arm_from_triggers(trig, lat, hold)
        if name == "predictive":
            return limiter(p, armed, step)
        return preramp_limiter(p, armed, fc, step)
    if name == "reactive":
        fall = np.zeros(len(p), bool)
        fall[1:] = (p[:-1] - p[1:]) > step  # a fall faster than the allowed ramp has been measured
        return limiter(p, _arm_from_triggers(fall, lat, hold), step)
    if name == "always_on_limiter":
        return limiter(p, np.ones(len(p), bool), step)
    raise KeyError(name)


def ramp_stats(out: np.ndarray, base: np.ndarray, peak: float, limit_frac: float) -> dict[str, float]:
    r = np.zeros(len(out))
    r[FS:] = (out[FS:] - out[:-FS])  # W change over the last 1 s
    limit = limit_frac * peak
    down = -r > limit
    anyv = np.abs(r) > limit

    def runs(mask: np.ndarray) -> int:
        return int(np.sum(mask[1:] & ~mask[:-1]) + mask[0])

    return {
        "max_ramp_w_per_s": float(np.abs(r).max()),
        "max_ramp_pct_peak_per_s": float(100 * np.abs(r).max() / peak),
        "max_down_ramp_pct_peak_per_s": float(100 * max(-r.min(), 0) / peak),
        "down_violations": runs(down),
        "all_violations": runs(anyv),
        "extra_energy_pct": float(100 * np.clip(out - base, 0, None).sum() / base.sum()),
        "extra_energy_kwh": float(np.clip(out - base, 0, None).sum() * DT_S / 3.6e6),
        "deferred_pct": float(100 * np.clip(base - out, 0, None).sum() / base.sum()),
        "hours": len(out) * DT_S / 3600,
    }


def alarms_for_tests() -> tuple[dict[str, tuple], float]:
    """Per trace: (idx, alarm, lowest LightGBM forecast over 1-5 s) from the saved test predictions."""
    info = json.load(open(PROC_DIR / "model_info.json"))
    best = info["best_classifier"]
    thr = info["thresholds"][best]
    pr = pd.read_parquet(PROC_DIR / "test_predictions.parquet",
                         columns=["trace_id", "idx", f"score_{best}", "lightgbm_1s", "lightgbm_5s"])
    out = {}
    for tid, g in pr.groupby("trace_id", sort=False):
        fmin = np.minimum(g["lightgbm_1s"].to_numpy(), g["lightgbm_5s"].to_numpy())
        out[tid] = (g["idx"].to_numpy(), g[f"score_{best}"].to_numpy() >= thr, fmin)
    return out, thr


def run(sp: SimParams | None = None, log=print) -> dict:
    sp = sp or SimParams()
    TABLES.mkdir(parents=True, exist_ok=True)
    traces, meta = load_traces(only_model=True)
    test_ids = set(meta.loc[meta["split"] == "test", "trace_id"])
    wl = dict(zip(meta["trace_id"], meta["workload"]))
    alarms, _ = alarms_for_tests()
    node_rows, outs = [], {}
    for tid, g in traces[traces["trace_id"].isin(test_ids)].groupby("trace_id", sort=True):
        p = g["power_w"].to_numpy(dtype=float)
        al = np.zeros(len(p), bool)
        fmin = np.full(len(p), np.nan)
        idx, a, fm = alarms[tid]
        al[idx] = a
        fmin[idx] = fm
        peak = node_peak(p)
        outs[tid] = {}
        for s in STRATEGIES:
            o = apply_strategy(s, p, al, sp, fmin)
            outs[tid][s] = o
            node_rows.append({"trace_id": tid, "workload": wl[tid], "strategy": s, "peak_w": peak,
                              **ramp_stats(o, p, peak, sp.ramp_limit_frac_per_s)})
    nodes = pd.DataFrame(node_rows)
    nodes.to_csv(TABLES / "smoothing_per_trace.csv", index=False)

    raw_kwh = {}
    for tid, d in outs.items():
        raw_kwh[tid] = d["raw"].sum() * DT_S / 3.6e6
    nodes["raw_kwh"] = nodes["trace_id"].map(raw_kwh)
    summ = nodes.groupby("strategy").apply(lambda g: pd.Series({
        "down_violations_per_node_hour": g["down_violations"].sum() / g["hours"].sum(),
        "all_violations_per_node_hour": g["all_violations"].sum() / g["hours"].sum(),
        "median_max_down_ramp_pct_peak_per_s": g["max_down_ramp_pct_peak_per_s"].median(),
        "extra_energy_pct": 100 * g["extra_energy_kwh"].sum() / g["raw_kwh"].sum(),
        "deferred_compute_pct": (g["deferred_pct"] * g["raw_kwh"]).sum() / g["raw_kwh"].sum(),
    }), include_groups=False).reindex(list(STRATEGIES))
    raw_v = summ.loc["raw", "down_violations_per_node_hour"]
    summ["down_violation_cut_pct"] = 100 * (1 - summ["down_violations_per_node_hour"] / raw_v)
    raw_a = summ.loc["raw", "all_violations_per_node_hour"]
    summ["all_violation_cut_pct"] = 100 * (1 - summ["all_violations_per_node_hour"] / raw_a)
    by_wl = nodes.groupby(["workload", "strategy"]).apply(lambda g: pd.Series({
        "down_violations_per_node_hour": g["down_violations"].sum() / g["hours"].sum(),
        "extra_energy_pct": 100 * g["extra_energy_kwh"].sum() / g["raw_kwh"].sum(),
    }), include_groups=False).reset_index()
    summ.round(3).to_csv(TABLES / "smoothing_summary.csv")
    by_wl.round(3).to_csv(TABLES / "smoothing_by_workload.csv", index=False)

    site = site_scaleup(outs, wl, sp)
    site.round(3).to_csv(TABLES / "site_scaleup.csv", index=False)
    plot_before_after(outs, wl, sp)
    plot_site(site)
    plot_tradeoff(summ)
    json.dump(asdict(sp), open(TABLES / "sim_params.json", "w"), indent=1)
    log(summ.round(2).to_string())
    log(site.round(2).to_string(index=False))
    return {"summary": summ, "site": site, "by_workload": by_wl}


def site_scaleup(outs: dict[str, dict[str, np.ndarray]], wl: dict[str, str], sp: SimParams) -> pd.DataFrame:
    """100 MW of GPU nodes built from test traces.

    synchronized: the whole site behaves like one giant lockstep job (each test trace in turn is
                  scaled to 100 MW; metrics averaged over traces, weighted by duration). This matches
                  what we saw in the data: every node of a multi-node job swings at the same instant.
    random_offsets: site_instances nodes, each running randomly drawn test jobs back to back from a random
                  starting point, summed and scaled so total rated capacity = 100 MW. Job-to-job seams
                  are real transitions between jobs; controller state resets at each seam.
    Annual figures assume the measured duty cycle runs all year (8,760 h).
    """
    rng = np.random.default_rng(SEED)
    tids = sorted(outs)
    rows = []
    hours_year = 8760.0
    # --- synchronized
    for s in STRATEGIES:
        extra, base, viol, hrs = 0.0, 0.0, 0, 0.0
        for tid in tids:
            p = outs[tid]["raw"]
            o = outs[tid][s]
            scale = sp.site_mw / node_peak(p)  # MW per W of this node
            extra += np.clip(o - p, 0, None).sum() * scale
            base += p.sum() * scale
            st = ramp_stats(o, p, node_peak(p), sp.ramp_limit_frac_per_s)
            viol += st["down_violations"]
            hrs += st["hours"]
        avg_mw = base / (hrs * 3600 / DT_S)
        frac = extra / base
        rows.append(_site_row("synchronized", s, avg_mw, frac, viol / hrs, sp, hours_year))
    # --- random offsets: each instance runs whole test jobs back to back (job after job, no looping
    # of a single trace), starting at a random point inside its first job
    n = int(sp.site_hours * 3600 / DT_S)
    scale = sp.site_mw * 1e6 / (sp.site_instances * NODE_RATED_W)  # summed rated capacity = 100 MW
    sums = {s: np.zeros(n) for s in STRATEGIES}
    extra = {s: 0.0 for s in STRATEGIES}  # filler energy summed per node (deferred work elsewhere does not cancel it)
    for _ in range(sp.site_instances):
        seq = [tids[int(rng.integers(len(tids)))]]
        off = int(rng.integers(0, len(outs[seq[0]]["raw"])))
        while sum(len(outs[t]["raw"]) for t in seq) - off < n:
            seq.append(tids[int(rng.integers(len(tids)))])
        raw_t = np.concatenate([outs[t]["raw"] for t in seq])[off : off + n] * scale
        for s in STRATEGIES:
            o = np.concatenate([outs[t][s] for t in seq])[off : off + n] * scale
            sums[s] += o
            extra[s] += np.clip(o - raw_t, 0, None).sum()
    site_peak = sp.site_mw * 1e6
    for s in STRATEGIES:
        st = ramp_stats(sums[s], sums["raw"], site_peak, sp.ramp_limit_frac_per_s)
        avg_mw = sums["raw"].mean() / 1e6
        frac = extra[s] / sums["raw"].sum()
        r = _site_row("random_offsets", s, avg_mw, frac, st["down_violations"] / st["hours"], sp, hours_year)
        r["max_down_ramp_mw_per_s"] = st["max_down_ramp_pct_peak_per_s"] / 100 * sp.site_mw
        rows.append(r)
    df = pd.DataFrame(rows)
    np.save(PROC_DIR / "site_random_offsets.npy", np.stack([sums[s] for s in STRATEGIES]))
    return df


def _site_row(case: str, s: str, avg_mw: float, frac: float, viol_per_h: float, sp: SimParams, hours_year: float) -> dict:
    mwh = frac * avg_mw * hours_year
    return {
        "case": case, "strategy": s, "avg_site_load_mw": avg_mw, "extra_energy_pct": 100 * frac,
        "extra_mwh_per_year": mwh, "extra_cost_usd_per_year": mwh * sp.price_per_mwh,
        "down_violations_per_hour": viol_per_h,
    }


def plot_before_after(outs: dict[str, dict[str, np.ndarray]], wl: dict[str, str], sp: SimParams) -> None:
    """Before/after power for one example window per training workload."""
    apply_style()
    from src.events import detect_drops

    picks = []
    for w in ["train_stable_diffusion", "train_llama2_70b_lora", "inference_offline"]:
        for tid in sorted(outs):
            if wl[tid] != w:
                continue
            p = outs[tid]["raw"]
            on = detect_drops(p)
            on = on[(on > 600) & (on < len(p) - 600)]
            if len(on) >= 3:
                picks.append((tid, int(on[len(on) // 2])))
                break
    fig, axes = plt.subplots(len(picks), 1, figsize=(13, 3.3 * len(picks)))
    axes = np.atleast_1d(axes)
    tid0, c0 = picks[0]
    np.savez(PROC_DIR / "slide_example.npz", t=np.arange(c0 - 40 * FS, c0 + 50 * FS) * DT_S,
             **{k: outs[tid0][k][c0 - 40 * FS : c0 + 50 * FS] for k in ("raw", "always_burn", "predictive")})
    for ax, (tid, c) in zip(axes, picks):
        s, e = c - 40 * FS, c + 50 * FS
        t = np.arange(s, e) * DT_S
        d = outs[tid]
        ax.plot(t, d["raw"][s:e] / 1e3, color=COLORS["raw"], lw=1.6, label="raw load")
        ax.plot(t, d["always_burn"][s:e] / 1e3, color=COLORS["burn"], lw=1.2, label=f"always burn (floor {int(sp.floor_frac * 100)}%)")
        ax.plot(t, d["predictive"][s:e] / 1e3, color=COLORS["predictive"], lw=1.6, label="predictive (ML-armed fill)")
        ax.fill_between(t, d["raw"][s:e] / 1e3, d["predictive"][s:e] / 1e3, color=COLORS["predictive"], alpha=0.15)
        ax.set_title(WORKLOAD_LABEL[wl[tid]], loc="left")
        ax.set_ylabel("node kW")
    axes[0].legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.3))
    axes[-1].set_xlabel("seconds into trace")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "smoothing_before_after.png", dpi=140)
    plt.close(fig)


STRAT_LABEL = {
    "raw": "No smoothing", "always_burn": "Always burn (80% floor)", "predictive": "Predictive (ML-armed fill)",
    "predictive_preramp": "Predictive + pre-ramp", "reactive": "Reactive (no forecast)",
    "always_on_limiter": "Always-on limiter (instant actuator)",
}
STRAT_COLOR = {
    "raw": COLORS["raw"], "always_burn": COLORS["burn"], "predictive": COLORS["predictive"],
    "predictive_preramp": COLORS["model2"], "reactive": COLORS["reactive"], "always_on_limiter": COLORS["model3"],
}


def plot_site(site: pd.DataFrame) -> None:
    apply_style()
    arr = np.load(PROC_DIR / "site_random_offsets.npy")
    t = np.arange(arr.shape[1]) * DT_S / 60
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.2), gridspec_kw={"width_ratios": [1.5, 1]})
    sl = slice(0, int(10 * 60 / DT_S))
    for i, s in enumerate(STRATEGIES):
        if s in ("raw", "always_burn", "predictive"):
            axes[0].plot(t[sl], arr[i, sl] / 1e6, color=STRAT_COLOR[s], lw=0.9, label=STRAT_LABEL[s])
    axes[0].set_title("100 MW site, jobs at random offsets (first 10 min)", loc="left")
    axes[0].set_xlabel("minutes")
    axes[0].set_ylabel("site GPU MW")
    axes[0].legend()
    show = ["always_burn", "always_on_limiter", "predictive", "predictive_preramp"]
    d = site[(site["case"] == "synchronized") & site["strategy"].isin(show)].set_index("strategy").reindex(show)
    v = d["extra_cost_usd_per_year"] / 1e6
    bars = axes[1].barh([STRAT_LABEL[s] for s in show], v, color=[STRAT_COLOR[s] for s in show])
    for b_, vi in zip(bars, v):
        axes[1].text(vi, b_.get_y() + b_.get_height() / 2, f" ${vi:.1f}M", va="center", fontsize=9)
    axes[1].invert_yaxis()
    axes[1].set_xlabel("$M per year of extra energy at $80/MWh")
    axes[1].set_title("100 MW site, synchronized jobs (worst case)", loc="left")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "site_scaleup.png", dpi=140)
    plt.close(fig)


def plot_tradeoff(summ: pd.DataFrame) -> None:
    """Energy spent vs ramp violations removed, one point per strategy."""
    apply_style()
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    for s, r in summ.iterrows():
        ax.scatter(r["extra_energy_pct"], r["down_violation_cut_pct"], s=110, color=STRAT_COLOR[s], zorder=3)
        lab = STRAT_LABEL[s] + (f" (+{r['deferred_compute_pct']:.1f}% compute deferred)" if r["deferred_compute_pct"] > 0.05 else "")
        ax.annotate(lab, (r["extra_energy_pct"], r["down_violation_cut_pct"]), xytext=(8, -3),
                    textcoords="offset points", fontsize=8)
    ax.set_xlabel("Extra energy burned (% of the job's energy)")
    ax.set_ylabel("Grid ramp violations removed (%)")
    ax.set_xlim(-0.3, max(summ["extra_energy_pct"]) * 1.6)
    ax.set_ylim(-5, 108)
    ax.set_title("Smoothing: violations removed vs energy spent (test traces)", loc="left")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "smoothing_tradeoff.png", dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    run()
