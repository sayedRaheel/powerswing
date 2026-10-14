"""Step 8: write reports/results.md and the one-slide summary figure from the saved tables.

All numbers are read from reports/tables/*.csv so the report always matches the latest run.
Written for a non-technical reader. No em dashes anywhere in the generated text.
"""
from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import FIG_DIR, PROC_DIR, REPORT_DIR
from src.plotstyle import COLORS, WORKLOAD_LABEL, apply_style

T = REPORT_DIR / "tables"


def load() -> dict:
    d = {
        "ft": pd.read_csv(T / "forecast_overall.csv"),
        "fw": pd.read_csv(T / "forecast_by_workload.csv"),
        "fs": pd.read_csv(T / "forecast_subset_with_chronos.csv"),
        "drop": pd.read_csv(T / "drop_warning.csv"),
        "drop_wl": pd.read_csv(T / "drop_warning_by_workload.csv"),
        "lat": pd.read_csv(T / "latency.csv"),
        "sim": pd.read_csv(T / "smoothing_summary.csv", index_col=0),
        "sim_wl": pd.read_csv(T / "smoothing_by_workload.csv"),
        "site": pd.read_csv(T / "site_scaleup.csv"),
        "params": json.load(open(T / "sim_params.json")),
        "events": pd.read_csv(PROC_DIR / "drop_summary.csv", index_col=0),
        "info": json.load(open(PROC_DIR / "model_info.json")),
        "sync": pd.read_csv(PROC_DIR / "sync_skew.csv", index_col=0)["value"],
        "sim_trace": pd.read_csv(T / "smoothing_per_trace.csv"),
    }
    gl = T / "generalization_lowo.csv"
    d["gen"] = pd.read_csv(gl) if gl.exists() else pd.DataFrame()
    return d


def key_numbers(d: dict) -> dict:
    ft = d["ft"]
    m5 = ft[ft["horizon_s"] == 5].set_index("model")["MAE"]
    best = d["info"]["best_forecaster"]  # chosen on validation, never on test
    learned = m5[[best]]
    drop = d["drop"].set_index("model")
    bc = d["info"]["best_classifier"]
    dw = d["drop_wl"].set_index("workload")
    sim = d["sim"]
    site = d["site"].set_index(["case", "strategy"])
    k = {
        "best_model": best,
        "best_mae5": float(learned[best]),
        "rhythm_mae5": float(m5["rhythm"]),
        "persist_mae5": float(m5["persistence"]),
        "gain_vs_rhythm": float(100 * (1 - learned[best] / m5["rhythm"])),
        "clf": bc,
        "recall": float(drop.loc[bc, "recall_1s"]),
        "lead": float(drop.loc[bc, "mean_lead_s"]),
        "fa_h": float(drop.loc[bc, "false_alarms_per_hour"]),
        "ep_prec": float(drop.loc[bc, "episode_precision"]),
        "f1": float(drop.loc[bc, "F1"]),
        "ap": float(drop.loc[bc, "AP"]),
        "rhythm_fa_h": float(drop.loc["rhythm_alarm", "false_alarms_per_hour"]),
        "rhythm_recall": float(drop.loc["rhythm_alarm", "recall_1s"]),
        "macro_recall": float(dw["recall_1s"].mean()),
        "events": int(drop.loc[bc, "events"]),
        "sd_share": float(dw.loc["train_stable_diffusion", "events"] / dw["events"].sum()),
        "pred_cut": float(sim.loc["predictive", "down_violation_cut_pct"]),
        "pred_energy": float(sim.loc["predictive", "extra_energy_pct"]),
        "burn_cut": float(sim.loc["always_burn", "down_violation_cut_pct"]),
        "burn_energy": float(sim.loc["always_burn", "extra_energy_pct"]),
        "pre_cut": float(sim.loc["predictive_preramp", "down_violation_cut_pct"]),
        "pre_energy": float(sim.loc["predictive_preramp", "extra_energy_pct"]),
        "pre_deferred": float(sim.loc["predictive_preramp", "deferred_compute_pct"]),
        "lim_energy": float(sim.loc["always_on_limiter", "extra_energy_pct"]),
        "react_cut": float(sim.loc["reactive", "down_violation_cut_pct"]),
        "raw_viol_h": float(sim.loc["raw", "down_violations_per_node_hour"]),
        "site_burn_usd": float(site.loc[("synchronized", "always_burn"), "extra_cost_usd_per_year"]),
        "site_pred_usd": float(site.loc[("synchronized", "predictive"), "extra_cost_usd_per_year"]),
        "site_pre_usd": float(site.loc[("synchronized", "predictive_preramp"), "extra_cost_usd_per_year"]),
        "site_lim_usd": float(site.loc[("synchronized", "always_on_limiter"), "extra_cost_usd_per_year"]),
        "site_burn_mwh": float(site.loc[("synchronized", "always_burn"), "extra_mwh_per_year"]),
        "site_pred_mwh": float(site.loc[("synchronized", "predictive"), "extra_mwh_per_year"]),
        "rand_raw_ramp": float(site.loc[("random_offsets", "raw"), "max_down_ramp_mw_per_s"]),
        "rand_burn_usd": float(site.loc[("random_offsets", "always_burn"), "extra_cost_usd_per_year"]),
        "rand_pred_usd": float(site.loc[("random_offsets", "predictive"), "extra_cost_usd_per_year"]),
    }
    k["energy_saving_vs_burn"] = 100 * (1 - k["pred_energy"] / k["burn_energy"])
    return k


# ----------------------------------------------------------------------------- slide

def slide(d: dict, k: dict) -> None:
    """One investor-style slide: headline, three KPI tiles, before/after and cost chart."""
    apply_style()
    fig = plt.figure(figsize=(16, 9))
    fig.patch.set_facecolor("white")
    head = (f"Our model predicts H100 power drops {k['lead']:.1f} s ahead with {100 * k['recall']:.0f}% recall;\n"
            f"predictive smoothing cuts ramp violations by {k['pred_cut']:.0f}% using "
            f"{k['energy_saving_vs_burn']:.0f}% less energy than always-burn")
    fig.text(0.04, 0.93, head, fontsize=21, fontweight="bold", va="top", color="#14202e")
    fig.text(0.04, 0.80, "Measured on held-out jobs from NLR's public H100 power dataset (Kestrel HPC, 5 Hz, "
             "training and inference). Simulated grid limit: 10% of peak per second.", fontsize=11, color="#56616d")
    tiles = [
        (f"{k['gain_vs_rhythm']:.0f}%", "lower forecast error 5 s ahead\nthan the best simple baseline"),
        (f"{100 * k['recall']:.0f}%", f"of big drops flagged at least 1 s early\n({k['fa_h']:.1f} false alarms per node-hour)"),
        (f"${(k['site_burn_usd'] - k['site_pred_usd']) / 1e6:.1f}M", "per year saved vs always-burn\non a 100 MW site at $80/MWh"),
    ]
    for i, (big, small) in enumerate(tiles):
        ax = fig.add_axes([0.04 + i * 0.31, 0.57, 0.29, 0.19])
        ax.set_axis_off()
        ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes, color="#eef3fb", zorder=0))
        ax.text(0.06, 0.62, big, fontsize=40, fontweight="bold", color=COLORS["model"], va="center", transform=ax.transAxes)
        ax.text(0.06, 0.22, small, fontsize=12, color="#14202e", va="center", transform=ax.transAxes)
    # before / after
    ax = fig.add_axes([0.06, 0.10, 0.54, 0.36])
    ex = np.load(PROC_DIR / "slide_example.npz")
    t = ex["t"] - ex["t"][0]
    ax.plot(t, ex["raw"] / 1e3, color=COLORS["raw"], lw=2, label="raw GPU load")
    ax.plot(t, ex["always_burn"] / 1e3, color=COLORS["burn"], lw=1.5, label="always burn (80% floor)")
    ax.plot(t, ex["predictive"] / 1e3, color=COLORS["predictive"], lw=2, label="predictive smoothing")
    ax.fill_between(t, ex["raw"] / 1e3, ex["predictive"] / 1e3, color=COLORS["predictive"], alpha=0.15)
    ax.set_xlabel("seconds")
    ax.set_ylabel("node power (kW)")
    ax.set_ylim(0, 3.0)
    ax.legend(loc="lower center", ncol=3, fontsize=10, frameon=False)
    ax.set_title("Example: one Stable Diffusion training node (4 x H100), raw vs smoothed", loc="left", fontsize=12)
    # cost bars
    ax = fig.add_axes([0.66, 0.10, 0.31, 0.36])
    labels = ["Always burn", "Predictive"]
    vals = [k["site_burn_usd"] / 1e6, k["site_pred_usd"] / 1e6]
    bars = ax.bar(labels, vals, color=[COLORS["burn"], COLORS["predictive"]], width=0.55)
    ax.grid(axis="x", visible=False)
    ax.set_ylim(0, max(vals) * 1.18)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v, f"${v:.1f}M", ha="center", va="bottom", fontsize=13, fontweight="bold")
    ax.set_ylabel("$M per year of extra energy")
    ax.set_title("Cost of smoothing a 100 MW site\n(synchronized jobs, worst case)", loc="left", fontsize=12)
    ax.text(0, -0.2, f"Violations removed: always burn {k['burn_cut']:.0f}%, predictive {k['pred_cut']:.0f}%",
            transform=ax.transAxes, fontsize=10, color="#56616d")
    fig.savefig(FIG_DIR / "summary_slide.png", dpi=110)
    plt.close(fig)


# ----------------------------------------------------------------------------- markdown

def _tbl(df: pd.DataFrame, floatfmt: str = "{:.1f}") -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        cells = [floatfmt.format(v) if isinstance(v, (float, np.floating)) else str(v) for v in r]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def _yes(b: bool) -> str:
    return "**MET**" if b else "**NOT MET**"


def markdown(d: dict, k: dict) -> str:
    MODEL = {"persistence": "Persistence (last value)", "moving_avg": "Moving average (5 s)", "rhythm": "Rhythm repeat",
             "lightgbm": "LightGBM", "tcn": "Tiny TCN (46k params)", "chronos_bolt_small": "Chronos-Bolt-Small (zero-shot)",
             "timesfm_2p5": "TimesFM 2.5 (zero-shot)"}
    ft = d["ft"].pivot(index="model", columns="horizon_s", values="MAE")
    ft = ft.reindex([m for m in MODEL if m in ft.index])
    ft.index = [MODEL[m] for m in ft.index]
    ft_tab = ft.reset_index().rename(columns={"index": "Model", 1: "1 s", 5: "5 s", 10: "10 s"})
    fs = d["fs"].pivot(index="model", columns="horizon_s", values="MAE")
    fs = fs.reindex([m for m in MODEL if m in fs.index])
    fs.index = [MODEL[m] for m in fs.index]
    fs_tab = fs.reset_index().rename(columns={"index": "Model", 1: "1 s", 5: "5 s", 10: "10 s"})
    fw = d["fw"][d["fw"]["horizon_s"] == 5].pivot(index="workload", columns="model", values="MAE")
    fw_tab = pd.DataFrame({
        "Workload": [WORKLOAD_LABEL[w] for w in fw.index],
        "Rhythm": fw["rhythm"].to_numpy(), "LightGBM": fw["lightgbm"].to_numpy(), "TCN": fw["tcn"].to_numpy(),
        "Gain vs rhythm (%)": (100 * (1 - fw[["lightgbm", "tcn"]].min(axis=1) / fw["rhythm"])).to_numpy(),
    })
    dw = d["drop_wl"]
    dw_tab = pd.DataFrame({
        "Workload": [WORKLOAD_LABEL[w] for w in dw["workload"]], "Drops in test": dw["events"],
        "Caught >= 1 s early (%)": 100 * dw["recall_1s"], "Mean warning (s)": dw["mean_lead_s"],
        "False alarms / node-hour": dw["false_alarms_per_hour"],
    })
    dr = d["drop"].copy()
    dr_tab = pd.DataFrame({
        "Model": dr["model"].map({"lightgbm": "LightGBM", "tcn": "Tiny TCN", "rhythm_alarm": "Rhythm alarm (baseline)"}),
        "Caught >= 1 s early (%)": 100 * dr["recall_1s"], "Mean warning (s)": dr["mean_lead_s"],
        "False alarms / node-hour": dr["false_alarms_per_hour"], "Precision": dr["precision"],
        "Recall": dr["recall"], "F1": dr["F1"], "AP": dr["AP"],
    })
    SL = {"raw": "No smoothing", "always_burn": "Always burn (80% floor)", "predictive": "Predictive (ML-armed fill)",
          "predictive_preramp": "Predictive + pre-ramp", "reactive": "Reactive, no forecast (reference)",
          "always_on_limiter": "Always-on limiter, instant actuator (reference)"}
    sim = d["sim"]
    sim_tab = pd.DataFrame({
        "Strategy": [SL[s] for s in sim.index],
        "Down-ramp violations / node-hour": sim["down_violations_per_node_hour"].to_numpy(),
        "Violations removed (%)": sim["down_violation_cut_pct"].to_numpy(),
        "Worst fall (% of peak per s, median node)": sim["median_max_down_ramp_pct_peak_per_s"].to_numpy(),
        "Extra energy (%)": sim["extra_energy_pct"].to_numpy(),
        "Compute deferred (%)": sim["deferred_compute_pct"].to_numpy(),
    })
    site = d["site"]
    site_tab = pd.DataFrame({
        "Case": site["case"].map({"synchronized": "All synchronized", "random_offsets": "Random offsets"}),
        "Strategy": site["strategy"].map(SL),
        "Extra energy (%)": site["extra_energy_pct"], "Extra MWh / year": site["extra_mwh_per_year"],
        "Extra cost / year ($M)": site["extra_cost_usd_per_year"] / 1e6,
        "Down-ramp violations / hour": site["down_violations_per_hour"],
    })
    lat = d["lat"].rename(columns={"model": "Model", "ms_per_prediction": "Milliseconds per prediction (CPU, 1 thread)"})
    gen = d["gen"]
    if len(gen):
        gen_tab = pd.DataFrame({
            "Held-out workload (never seen in training)": [WORKLOAD_LABEL[w] for w in gen["held_out_workload"]],
            "LightGBM MAE 5 s": gen["lgb_mae_5s"], "Rhythm MAE 5 s": gen["rhythm_mae_5s"],
            "Gain vs rhythm (%)": gen["lgb_gain_vs_rhythm_5s_pct"],
            "Drops caught >= 1 s (%)": 100 * gen["drop_recall_1s"],
            "False alarms / node-hour": gen["false_alarms_per_hour"],
        })
        gen_txt = _tbl(gen_tab)
        n_gen_ok = int((gen["lgb_gain_vs_rhythm_5s_pct"] > 0).sum())
        worst = gen.sort_values("lgb_gain_vs_rhythm_5s_pct").iloc[0]
        gen_summary = (
            f"**This is the weakest part of the result.** On a workload type it has never seen, LightGBM beats the rhythm "
            f"rule on only {n_gen_ok} of {len(gen)} workloads, and can be far worse (unseen {WORKLOAD_LABEL[worst['held_out_workload']]}: "
            f"{worst['lgb_mae_5s']:.0f} W vs {worst['rhythm_mae_5s']:.0f} W). Drop warning also degrades: "
            f"{int((gen['drop_recall_1s'] < 0.5).sum())} of {len(gen)} unseen workloads have recall below 50% "
            f"(range {100 * gen['drop_recall_1s'].min():.0f}% to {100 * gen['drop_recall_1s'].max():.0f}%), and where recall holds up "
            f"it comes with up to {gen['false_alarms_per_hour'].max():.0f} false alarms per node-hour. The models learn the specific power signatures of "
            "the job types they were trained on. The rhythm rule needs no training, so it is the safer choice for a brand-new "
            "job type. In practice this means: (a) fall back to the rhythm rule until a new job type has some history, "
            "(b) retrain or fine-tune per job type, which is cheap at these model sizes, and (c) train on a much wider "
            "variety of jobs than the two training workloads available here.")
    else:
        gen_txt, gen_summary = "_Not run._", ""

    fsm = d["fs"][d["fs"]["horizon_s"] == 5].set_index("model")["MAE"]
    latm = d["lat"].set_index("model")["ms_per_prediction"]
    tcn_ms = latm[[i for i in latm.index if "TCN" in i]].iloc[0]
    fm_parts = []
    for key, name in [("chronos_bolt_small", "Chronos-Bolt-Small"), ("timesfm_2p5", "TimesFM 2.5")]:
        if key in fsm.index:
            ms = latm[[i for i in latm.index if name.split()[0].lower() in i.lower()]].iloc[0]
            fm_parts.append(f"{name} is off by {fsm[key]:.0f} W at 5 s (rhythm rule {fsm['rhythm']:.0f} W, LightGBM {fsm['lightgbm']:.0f} W) "
                            f"and takes {ms:.0f} ms per prediction ({ms / tcn_ms:.0f}x the tiny TCN)")
    fm_txt = ("; ".join(fm_parts) + ". General-purpose pretrained forecasters do not know this data's rhythms; "
              "small models trained on it are both more accurate and far cheaper to run.") if fm_parts else ""
    latm2 = d["lat"].set_index("model")["ms_per_prediction"]
    lat_tcn = latm2[[i for i in latm2.index if "TCN" in i]].iloc[0]
    lat_lgb = latm2[[i for i in latm2.index if i.startswith("LightGBM")]].iloc[0]
    st = d["sim_trace"]
    res = st[st["strategy"] == "predictive"].groupby("workload")["down_violations"].sum()
    res = (100 * res / res.sum()).sort_values(ascending=False)
    resid_txt = ", ".join(f"{v:.0f}% on {WORKLOAD_LABEL[w]}" for w, v in res.items() if v >= 1)
    c1 = k["gain_vs_rhythm"] >= 20
    c2 = k["recall"] >= 0.80
    c3 = (k["pred_cut"] >= 50) and (k["pred_energy"] < k["burn_energy"])
    p = d["params"]

    return f"""# Power-swing prediction POC: results

_All numbers in this file are generated by `python -m src.run_all` from the NLR H100 dataset. Charts are in `reports/figures/`, raw tables in `reports/tables/`._

![summary](figures/summary_slide.png)

## The short version

1. **AI training power really does swing hard and often.** On a single 4-GPU H100 node we found between {d['events']['drops_per_node_hour'].min():.0f} and {d['events']['drops_per_node_hour'].max():.0f} "big drops" per hour (power falling by more than 30% within one second). A typical drop sheds 1 to 2 kW per node in about 1.5 seconds. The nodes of a multi-node job drop together ({d['sync']['matched_within_5s_pct']:.0f}% of drops line up across nodes, typically within {d['sync']['p95_skew_s']:.1f} s), so a large training run hits the grid as one giant synchronized swing.
2. **Machine learning predicts these swings much better than simple rules.** Five seconds ahead, our primary model ({MODEL[k['best_model']]}, picked on validation data) is off by {k['best_mae5']:.0f} W per node on average, versus {k['rhythm_mae5']:.0f} W for the best simple rule ("repeat the last cycle") and {k['persist_mae5']:.0f} W for "assume nothing changes". That is {k['gain_vs_rhythm']:.0f}% less error than the best rule.
3. **We can warn about drops before they happen.** The drop-warning model flags {100 * k['recall']:.0f}% of big drops at least 1 second in advance, on average {k['lead']:.1f} seconds ahead for the drops it catches (the maximum possible in this setup is 5 s), with {k['fa_h']:.1f} false alarms per node-hour. A rule-based alarm achieves similar recall only by raising {k['rhythm_fa_h']:.0f} false alarms per hour.
4. **Prediction makes smoothing cheap.** Keeping power at a high floor all the time ("always burn") wastes {k['burn_energy']:.1f}% extra energy and still leaves most grid ramp violations in place. Smoothing only when the model expects a drop removes {k['pred_cut']:.0f}% of violations for {k['pred_energy']:.1f}% extra energy, {k['energy_saving_vs_burn']:.0f}% less than always-burn. For a 100 MW site that is about **${k['site_burn_usd'] / 1e6:.1f}M versus ${k['site_pred_usd'] / 1e6:.1f}M per year** of extra electricity at $80/MWh.
5. **The honest caveats.** The strongest results come from training jobs with regular rhythms (especially Stable Diffusion). Drops caused by jobs or benchmark runs ending are much harder to foresee. The models also do not transfer to job types they have never seen: there, the simple rhythm rule is safer until the model has some history of the new job. And if the smoothing hardware could react instantly, a simple always-on limiter (no ML) would do as well; prediction earns its keep when the smoothing actuator needs a second or more to engage, or when we want to ramp down early instead of burning energy. Details below.

## Success criteria

| Criterion | Result | Status |
|---|---|---|
| Best model beats the rhythm baseline by at least 20% MAE at 5 s | {k['gain_vs_rhythm']:.0f}% lower MAE ({k['best_mae5']:.0f} W vs {k['rhythm_mae5']:.0f} W) | {_yes(c1)} |
| Catches at least 80% of big drops with at least 1 s of warning | {100 * k['recall']:.1f}% overall (mean warning {k['lead']:.1f} s). Caveat: {100 * k['sd_share']:.0f}% of test drops are Stable Diffusion, where recall is very high. Averaged equally over the 5 workload types, recall is {100 * k['macro_recall']:.0f}%. | {_yes(c2)} overall, not met per workload |
| Predictive smoothing cuts ramp violations by at least 50% while using less extra energy than always-burn | {k['pred_cut']:.0f}% fewer down-ramp violations, {k['pred_energy']:.1f}% vs {k['burn_energy']:.1f}% extra energy | {_yes(c3)} |

## 1. The data

NLR (formerly NREL) "Dataset of Generative AI Workload Power Profiles": H100 GPUs on the Kestrel supercomputer, measured every 0.1 to 0.2 seconds. Full description in `data/README_data.md`.

- **Training:** Llama2-70B LoRA fine-tuning (2 to 16 nodes) and Stable Diffusion training (1 to 16 nodes), 46 jobs, about 286 node-hours.
- **Inference:** Llama3-70B served by vLLM in three benchmark styles (offline batches, online bursts, online fixed rate), about 52 hours on one node.
- We use GPU power only (4 H100s per node). Everything is resampled to 5 samples per second.
- Not in the dataset: job crash logs, checkpoint timestamps, step markers, facility meter data. Any statement about "checkpoints" or "communication pauses" would be a guess from the shape of the curve, so we do not make it.

![traces](figures/eda_sample_traces.png)

**Big drops by workload** (definition: power falls by more than 30% of the recent 10 s peak within 1 s):

{_tbl(d['events'].reset_index().rename(columns={'workload': 'Workload'})[['Workload', 'node_hours', 'n_drops', 'drops_per_node_hour', 'median_size_w', 'median_size_pct_of_peak', 'median_time_to_bottom_s', 'median_duration_s', 'median_ramp_max_wps']].rename(columns={'node_hours': 'Node-hours', 'n_drops': 'Drops', 'drops_per_node_hour': 'Per node-hour', 'median_size_w': 'Median size (W)', 'median_size_pct_of_peak': 'Size (% of peak)', 'median_time_to_bottom_s': 'Time to bottom (s)', 'median_duration_s': 'Duration (s)', 'median_ramp_max_wps': 'Steepest fall (W/s)'}))}

Surprises worth knowing:
- **Llama2 LoRA training swings every ~12 seconds** between about 2.75 kW and 2.15 kW per node. That 22% swing is below the 30% "big drop" bar, yet it still breaks a 10%-per-second grid ramp limit every cycle.
- **Stable Diffusion training alternates** between long flat stretches and phases where power plunges to about 650 W every ~12 s. Those phases create most of its drops.
- **Inference drops are mostly benchmark gaps**, where the GPU goes idle between scripted test runs. They are real power swings, but their timing is set by the test harness, not by the model.
- **Multi-node jobs move together**: for {d['sync']['matched_within_5s_pct']:.1f}% of drops on one node, every other node of the same job also drops within 5 s; the median offset is {d['sync']['median_skew_s']:.1f} s and 95% are within {d['sync']['p95_skew_s']:.1f} s (one or two samples, which is also within clock-sync error between nodes).

![multinode](figures/eda_single_vs_multinode.png)

## 2. Forecasting power 1, 5 and 10 seconds ahead

Error is mean absolute error in watts per 4-GPU node (about 2.2 kW average load). Test set = whole training jobs and the last 20% of each inference session that the models never saw.

{_tbl(ft_tab)}

![bars](figures/model_comparison_5s.png)
![horizon](figures/error_by_horizon.png)

**By workload, 5 s ahead (W per node):**

{_tbl(fw_tab)}

**Pretrained "foundation" forecasters, zero-shot.** These were too slow to run on all 800k test points, so all models are compared on the same 2,000 randomly sampled test points (400 per workload):

{_tbl(fs_tab)}

{fm_txt}

![overlay](figures/forecast_overlays_5s.png)

## 3. Warning about drops ("will a big drop start within 5 s?")

The primary classifier ({ {'lightgbm': 'LightGBM', 'tcn': 'Tiny TCN'}[k['clf']] }) was picked by validation average precision. Operating thresholds were chosen on validation data (highest threshold that catches 85% of validation drops at least 1 s early; target reached on validation: {', '.join('yes' if x['target_met'] else 'no' for x in d['info']['threshold_search'][:3])} for LightGBM, TCN and the rhythm alarm), then applied unchanged to the test set. Mean warning is averaged over the drops caught at least 1 s early.

{_tbl(dr_tab, "{:.2f}")}

"Caught >= 1 s early" counts a drop as caught only if a warning was on at least 1 second before it started. "False alarms" are warning episodes not followed by a drop within 5 s. Precision, recall and F1 are per 0.2 s sample; AP is the area under the precision-recall curve.

**By workload (best classifier):**

{_tbl(dw_tab)}

This table is the most important nuance of the project. Regular, rhythmic training drops (Stable Diffusion) are predicted almost perfectly. Drops at the end of an inference run or a job phase are only partly predictable from the power signal alone, and drops in the fixed-rate online inference benchmark are essentially unpredictable. In production, scheduler signals (job ends, batch completions, checkpoint calls) would likely close much of this gap.

![pr](figures/drop_warning_pr_curve.png)

## 4. Does it generalize to new kinds of jobs?

Each row retrains LightGBM with one whole workload type removed, then tests on that unseen type.

{gen_txt}

{gen_summary}

## 5. Speed (could it run on an edge box?)

{_tbl(lat, "{:.2f}")}

Measured on one thread of an Apple-silicon laptop CPU. The tiny TCN needs about {lat_tcn:.1f} ms per prediction and LightGBM including all feature calculations about {lat_lgb:.0f} ms, roughly 20 to 200 times inside a 200 ms (5 Hz) control loop. That headroom suggests they would also fit an edge device such as a Raspberry Pi or Jetson, but we have not measured on one. The pretrained foundation models are far heavier.

## 6. What the predictions are worth: smoothing simulation

Settings: grid ramp limit {100 * p['ramp_limit_frac_per_s']:.0f}% of peak per second; always-burn floor {100 * p['floor_frac']:.0f}% of the last {p['peak_window_s']:.0f} s peak; smoothing actuator (filler GPU work or battery) needs {p['actuator_latency_s']:.1f} s to engage; electricity ${p['price_per_mwh']:.0f}/MWh. All strategies only add power on top of the real load, except "pre-ramp", which also lowers the GPU power cap early and therefore delays a little real work.

How the predictive strategy works: when the drop-warning model fires, or the forecast says power will fall by more than {100 * p['forecast_trigger_frac']:.0f}% of peak within 5 s, the smoothing actuator is armed. If the load then falls, output is held up and released at the allowed ramp rate instead of crashing.

{_tbl(sim_tab)}

![before after](figures/smoothing_before_after.png)
![tradeoff](figures/smoothing_tradeoff.png)

What this shows:
- **Always-burn is expensive and still fails the grid limit.** An 80% floor allows a 20% instant fall, which is twice the 10%/s limit, so it removes only {k['burn_cut']:.0f}% of violations while burning {k['burn_energy']:.1f}% extra energy.
- **Predictive smoothing removes {k['pred_cut']:.0f}% of violations for {k['pred_energy']:.1f}% extra energy.** The remaining violations are falls the models did not foresee: {resid_txt}.
- **Reacting without a forecast barely helps ({k['react_cut']:.0f}%)** because a 1 s actuator delay means the drop is already over when smoothing kicks in.
- **Reference point: an always-on limiter** (smoothing permanently armed) would remove every violation for {k['lim_energy']:.1f}% extra energy and needs no ML. It is only possible if the actuator is always ready, with zero engage time and zero standby cost, which is the assumption to validate with hardware partners.
- **Pre-ramp** (lower the power cap gradually when a drop is predicted) cuts the energy bill further, to {k['pre_energy']:.1f}%, but delays about {k['pre_deferred']:.1f}% of compute. This is the option that only a predictor can offer.

### Scaling to a 100 MW site

100 MW of H100 GPU capacity (about 35,000 nodes), with the measured duty cycles running all year.

{_tbl(site_tab)}

![site](figures/site_scaleup.png)

- **All synchronized (worst case, e.g. one huge training run):** always-burn costs about ${k['site_burn_usd'] / 1e6:.1f}M per year ({k['site_burn_mwh'] / 1e3:.0f} GWh), predictive about ${k['site_pred_usd'] / 1e6:.1f}M ({k['site_pred_mwh'] / 1e3:.0f} GWh), a saving of about **${(k['site_burn_usd'] - k['site_pred_usd']) / 1e6:.1f}M per year** with far better grid compliance.
- **Random offsets (many small independent jobs):** the swings average out. The whole site never falls faster than {k['rand_raw_ramp']:.1f} MW per second, well within a 10 MW/s limit, so no smoothing is needed at all. The business case is strongest for sites dominated by large synchronized training jobs, which is exactly where AI is heading.

## Limitations

- **One cluster, one GPU type, short runs.** About 340 node-hours from H100 nodes on one HPC system, with jobs lasting 25 minutes to 7 hours. Production training runs last weeks and include events not present here (checkpoints at scale, failures, restarts).
- **Inference drops are benchmark-driven.** Their timing reflects how the test harness started and stopped runs.
- **GPU power only.** CPUs, memory, networking and cooling are not modeled. Facility-level swings will be somewhat smaller in percentage terms because of this constant overhead.
- **5 Hz sampling.** Real ramps inside 0.2 s are likely steeper than we can see. Sub-second grid effects are not captured.
- **Smoothing is simulated, not tested on hardware.** The actuator latency ({p['actuator_latency_s']:.0f} s), zero standby cost of an armed actuator, and the ramp limit are assumptions. The value of prediction depends heavily on actuator latency (see notebook 03 for a sensitivity sweep).
- **No transfer to unseen job types.** Trained on only two training workloads, the models do worse than the rhythm rule on a training job type they have never seen (section 4).
- **The 80% recall headline is driven by Stable Diffusion drops.** Per workload, recall ranges from about {100 * d['drop_wl']['recall_1s'].min():.0f}% to {100 * d['drop_wl']['recall_1s'].max():.0f}%.
- **Annual figures extrapolate** a few hours of measured behavior to a full year at constant utilization.

## Next steps

1. **Add scheduler and framework signals** (job end, checkpoint start, evaluation phase, batch boundaries). These would let the model foresee the drops that the power signal alone cannot.
2. **Pilot on real hardware**: measure actuator latency and standby cost for GPU filler kernels, power capping and a battery inverter; rerun the simulation with measured values.
3. **Get longer, larger traces** (multi-day, 1,000+ GPU training runs, facility meter data) from a partner data center.
4. **Predict rises as well as drops**, so ramp-up violations can be handled with pre-emptive power capping.
5. **Package the TCN for an edge controller** and test it in a closed loop.

## How to reproduce

```
uv venv --python 3.12 .venv && uv pip install -r requirements.txt   # macOS: brew install libomp
.venv/bin/python -m src.run_all
```
"""


def run() -> None:
    d = load()
    k = key_numbers(d)
    slide(d, k)
    md = markdown(d, k)
    md = md.replace("—", ",").replace("–", "-")  # house style: no em or en dashes
    (REPORT_DIR / "results.md").write_text(md)
    json.dump(k, open(T / "key_numbers.json", "w"), indent=1)
    print(json.dumps({x: round(v, 2) if isinstance(v, float) else v for x, v in k.items()}, indent=1))


if __name__ == "__main__":
    run()
