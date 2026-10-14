"""Step 2: data exploration figures and drop-event statistics."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import DT_S, FIG_DIR, PROC_DIR
from src.events import characterise_drops, detect_drops
from src.load import load_traces
from src.plotstyle import COLORS, WORKLOAD_LABEL, apply_style


def all_events(traces: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """Detect and characterise drops on every trace."""
    rows = []
    for tid, g in traces.groupby("trace_id", sort=False, observed=True):
        p = g["power_w"].to_numpy()
        ev = characterise_drops(p, detect_drops(p))
        ev["trace_id"] = tid
        rows.append(ev)
    ev = pd.concat(rows, ignore_index=True)
    return ev.merge(meta[["trace_id", "workload", "node_count", "split"]], on="trace_id")


def event_summary(ev: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    hours = meta.groupby("workload")["duration_s"].sum() / 3600
    g = ev.groupby("workload")
    out = pd.DataFrame({
        "node_hours": hours,
        "n_drops": g.size(),
    })
    out["drops_per_node_hour"] = out["n_drops"] / out["node_hours"]
    out["median_size_w"] = g["size_w"].median()
    out["median_size_pct_of_peak"] = g["size_pct"].median()
    out["median_time_to_bottom_s"] = g["time_to_bottom_s"].median()
    out["median_duration_s"] = g["duration_s"].median()
    out["p90_duration_s"] = g["duration_s"].quantile(0.9)
    out["median_ramp_max_wps"] = g["ramp_max_wps"].median()
    out["median_ramp_avg_wps"] = g["ramp_avg_wps"].median()
    return out.round(1)


def plot_samples(traces: pd.DataFrame, meta: pd.DataFrame, jobs: pd.DataFrame) -> None:
    """Training vs inference and single vs multi-node example traces."""
    apply_style()
    picks = [
        ("train_llama2_70b_lora", "Training: Llama2-70B LoRA (one node of a 16-node job)", 16),
        ("train_stable_diffusion", "Training: Stable Diffusion (single-node job)", 1),
        ("inference_offline", "Inference: Llama3-70B offline batch", 1),
        ("inference_online_rate", "Inference: Llama3-70B online, fixed request rate", 1),
    ]
    fig, axes = plt.subplots(len(picks), 2, figsize=(14, 2.6 * len(picks)),
                             gridspec_kw={"width_ratios": [2, 1]})
    for row, (wl, title, nn) in zip(axes, picks):
        m = meta[(meta["workload"] == wl) & (meta["node_count"] == nn)].sort_values("trace_id")
        tid = m["trace_id"].iloc[min(2, len(m) - 1)]
        g = traces[traces["trace_id"] == tid]
        p, t = g["power_w"].to_numpy(), g["t_s"].to_numpy()
        on = detect_drops(p)
        row[0].plot(t / 60, p / 1e3, lw=0.4, color=COLORS["raw"])
        row[0].plot(t[on] / 60, p[on] / 1e3, "v", ms=4, color=COLORS["drop"], label="big drop")
        row[0].set_title(title, loc="left")
        row[0].set_ylabel("node kW")
        row[0].set_xlabel("minutes")
        # zoom on a 4-minute window that contains drops
        c = on[len(on) // 2] if len(on) else len(p) // 2
        s, e = max(0, c - int(120 / DT_S)), min(len(p), c + int(120 / DT_S))
        row[1].plot(t[s:e], p[s:e] / 1e3, lw=0.8, color=COLORS["raw"])
        o = on[(on >= s) & (on < e)]
        row[1].plot(t[o], p[o] / 1e3, "v", ms=6, color=COLORS["drop"])
        row[1].set_title("4-minute zoom", loc="left")
        row[1].set_xlabel("seconds")
    axes[0, 0].legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "eda_sample_traces.png", dpi=130)
    plt.close(fig)

    # single vs multi-node: one node vs the whole-job total, same workload
    fig, axes = plt.subplots(2, 2, figsize=(14, 5.5), sharex="col")
    for col, (wl, nn) in enumerate([("train_llama2_70b_lora", 16), ("train_stable_diffusion", 16)]):
        j = jobs[(jobs["workload"] == wl) & (jobs["node_count"] == nn)]
        jid = sorted(j["job_id"].unique())[0]
        jj = j[j["job_id"] == jid]
        m = meta[meta["job_id"] == jid].sort_values("trace_id")
        for tid in m["trace_id"].iloc[:4]:
            g = traces[traces["trace_id"] == tid]
            axes[0, col].plot(g["t_s"] / 60, g["power_w"] / 1e3, lw=0.4, alpha=0.8)
        axes[0, col].set_title(f"{WORKLOAD_LABEL[wl]}: 4 of {nn} nodes overlaid", loc="left")
        axes[0, col].set_ylabel("node kW")
        axes[1, col].plot(jj["t_s"] / 60, jj["power_w"] / 1e3, lw=0.4, color=COLORS["raw"])
        axes[1, col].set_title(f"Whole job ({nn} nodes, {nn * 4} GPUs) summed", loc="left")
        axes[1, col].set_ylabel("job kW")
        axes[1, col].set_xlabel("minutes")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "eda_single_vs_multinode.png", dpi=130)
    plt.close(fig)


def plot_event_stats(ev: pd.DataFrame, summ: pd.DataFrame) -> None:
    apply_style()
    order = list(summ.index)
    labels = [WORKLOAD_LABEL[w] for w in order]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    axes[0].barh(labels, summ["drops_per_node_hour"], color=COLORS["model"])
    axes[0].set_title("Big drops per node-hour", loc="left")
    for ax, col, ttl in [(axes[1], "size_pct", "Drop size (% of recent peak)"),
                         (axes[2], "ramp_max_wps", "Steepest fall (W/s per node)")]:
        data = [ev.loc[ev["workload"] == w, col].dropna().to_numpy() for w in order]
        ax.boxplot(data, orientation="horizontal", tick_labels=labels, showfliers=False)
        ax.set_title(ttl, loc="left")
    for ax in axes[1:]:
        ax.set_yticklabels([])
    fig.tight_layout()
    fig.savefig(FIG_DIR / "eda_drop_stats.png", dpi=130)
    plt.close(fig)


def sync_skew(traces: pd.DataFrame, meta: pd.DataFrame) -> dict[str, float]:
    """How simultaneous are drops across the nodes of one multi-node training job?

    For every drop on the job's first node, find the nearest drop on each other node (within 5 s).
    Times are on the job's common clock (all nodes share the same 0.2 s grid origin).
    """
    gaps, matched, total = [], 0, 0
    mm = meta[(meta["phase"] == "training") & (meta["node_count"] > 1)]
    for _, g in mm.groupby("job_id"):
        on = {}
        for tid in g["trace_id"]:
            tr = traces[traces["trace_id"] == tid]
            t = tr["timestamp"].to_numpy()
            idx = detect_drops(tr["power_w"].to_numpy())
            on[tid] = t[idx]
        ref, others = g["trace_id"].iloc[0], list(g["trace_id"].iloc[1:])
        for t0 in on[ref]:
            for o in others:
                total += 1
                if len(on[o]) == 0:
                    continue
                d = np.abs((on[o] - t0) / np.timedelta64(1, "ms")) / 1000.0
                if d.min() <= 5.0:
                    matched += 1
                    gaps.append(d.min())
    gaps = np.asarray(gaps)
    return {"node_pairs_checked": total, "matched_within_5s_pct": 100 * matched / max(total, 1),
            "median_skew_s": float(np.median(gaps)), "p95_skew_s": float(np.quantile(gaps, 0.95)),
            "max_skew_s": float(gaps.max()), "within_0_4s_pct": float(100 * np.mean(gaps <= 0.4))}


def run() -> pd.DataFrame:
    traces, meta = load_traces()
    jobs = pd.read_parquet(PROC_DIR / "jobs.parquet")
    ev = all_events(traces, meta)
    ev.to_parquet(PROC_DIR / "drop_events.parquet", index=False)
    summ = event_summary(ev, meta)
    summ.to_csv(PROC_DIR / "drop_summary.csv")
    plot_samples(traces, meta, jobs)
    plot_event_stats(ev, summ)
    # small per-node-count table for the data README
    hours = meta.groupby(["workload", "node_count"])["duration_s"].sum() / 3600
    cnt = ev.groupby(["workload", "node_count"]).size()
    (cnt / hours).round(1).rename("drops_per_node_hour").to_csv(PROC_DIR / "drop_rate_by_nodes.csv")
    sk = sync_skew(traces, meta)
    pd.Series(sk).to_csv(PROC_DIR / "sync_skew.csv", header=["value"])
    print("cross-node drop synchronization:", {k: round(v, 2) for k, v in sk.items()})
    print(summ.to_string())
    return summ


if __name__ == "__main__":
    run()
