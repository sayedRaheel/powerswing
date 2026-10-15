"""Build the paper draft (paper/main.tex + figures) from the result tables, so every number in the text
comes from a file the pipeline wrote. Run after src.aligned, src.regime, src.crossdata, src.transfer.

    python -m src.paper            # writes paper/main.tex, paper/fig_*.pdf, paper/numbers.json
    tectonic paper/main.tex        # builds paper/main.pdf (if tectonic is installed)

Placeholders in the template look like <<name>> and are filled from numbers.json.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import PROC_DIR, REPORT_DIR, ROOT

TABLES = REPORT_DIR / "tables"
OUT = ROOT / "paper"
DS_LABEL = {"nlr": "NLR (4xH100)", "elsayed": "Elsayed (8xH100/B200)", "supercloud": "Supercloud (1-2xV100)"}


# ---------------------------------------------------------------- numbers

def dataset_stats() -> pd.DataFrame:
    rows = []
    m = pd.read_csv(PROC_DIR / "traces_meta.csv")
    m = m[m["use_for_model"]]
    # independent units: training jobs, and each inference benchmark as one continuous session
    units = np.where(m["phase"] == "training", "job_" + m["job_id"].astype(str), "session_" + m["workload"])
    rows.append({"dataset": "nlr", "node_h": m["duration_s"].sum() / 3600, "units": len(set(units)),
                 "test_units": len(set(units[m["split"] == "test"])), "traces": len(m)})
    for name in ("elsayed", "supercloud"):
        e = pd.read_csv(PROC_DIR / f"ext_{name}_meta.csv", dtype={"job_id": str})
        rows.append({"dataset": name, "node_h": e["duration_s"].sum() / 3600, "units": e["job_id"].nunique(),
                     "test_units": e.loc[e["split"] == "test", "job_id"].nunique(), "traces": len(e)})
    return pd.DataFrame(rows).set_index("dataset")


def numbers() -> dict[str, str]:
    n: dict[str, float | str] = {}
    al = json.load(open(PROC_DIR / "aligned_info.json"))
    n["nlr_ap_ml"] = al["L1_test_ap"]
    n["nlr_ap_rh"] = al["L1_test_ap_rhythm"]
    n["nlr_ap_old"] = al["test_ap_old_drop_clf"]
    n["nlr_ap_rhalarm"] = al["test_ap_rhythm_alarm"]
    # matched label ablation (src/ablation.py): big-drop label through the exact aligned pipeline
    ab = json.load(open(PROC_DIR / "ablation_info.json"))
    for k in ("matched_aligned_ap", "matched_drop_ap", "matched_diff", "matched_diff_lo", "matched_diff_hi",
              "matched_drop_ap_on_drop_label", "matched_aligned_ap_on_drop_label"):
        n[f"abl_{k}"] = ab[k]
    for w in ("train_llama2_70b_lora", "train_stable_diffusion", "inference_offline", "inference_online_finite", "inference_online_rate"):
        n[f"wl_{w}_ml"] = al.get(f"test_ap_{w}", np.nan)
        n[f"wl_{w}_rh"] = al.get(f"test_ap_rhythm_{w}", np.nan)
    for L in (0, 0.2, 0.5, 1, 2, 3):
        n[f"lat{str(L).replace('.', 'p')}_ml"] = al[f"L{L:g}_test_ap"]
        n[f"lat{str(L).replace('.', 'p')}_rh"] = al[f"L{L:g}_test_ap_rhythm"]

    tg = pd.read_csv(TABLES / "regime_targets.csv")
    for t in (80, 90, 95):
        for sb in (0, 2):
            g = tg[(tg["target"] == t) & (tg["standby_pct"] == sb)].set_index("strategy")
            for s in ("ml_aligned", "rhythm_aligned", "ml_alarm", "always_on", "oracle"):
                n[f"t{t}_sb{sb}_{s}_cut"] = g.loc[s, "test_cut_pct"]
                n[f"t{t}_sb{sb}_{s}_armed"] = g.loc[s, "armed_pct"]
                n[f"t{t}_sb{sb}_{s}_ovh"] = g.loc[s, "test_overhead_pct"]
            d = g.loc["diff_cut_ml_minus_rhythm_aligned"]
            n[f"t{t}_sb{sb}_diff"], n[f"t{t}_sb{sb}_lo"], n[f"t{t}_sb{sb}_hi"] = d["test_cut_pct"], d["test_overhead_pct"], d["armed_pct"]

    par = pd.read_csv(TABLES / "regime_pareto_test.csv")
    p1 = par[(par["latency_s"] == 1.0)]
    n["rh_max_cut"] = p1.loc[p1["strategy"] == "rhythm_aligned", "cut_pct"].max()
    # descriptive (full test sweep): least armed time reaching a removal level
    for t in (80, 90, 95):
        for s_, k in (("ml_aligned", "ml"), ("rhythm_aligned", "rh"), ("ml_alarm", "alarm")):
            g = p1[(p1["strategy"] == s_) & (p1["cut_pct"] >= t)]
            n[f"arm{t}_{k}"] = g["armed_pct"].min() if len(g) else float("nan")
    n["ml_max_cut"] = p1.loc[p1["strategy"] == "ml_aligned", "cut_pct"].max()
    n["oracle_armed"] = p1.loc[p1["strategy"] == "oracle", "armed_pct"].iloc[0]
    an = pd.read_csv(TABLES / "regime_armed_needed.csv").set_index("target")
    for t in (80, 90, 95):
        for c in an.columns:
            n[f"an{t}_{c}"] = an.loc[float(t), c]
    sm = pd.read_csv(TABLES / "smoothing_summary.csv", index_col=0)
    n["burn_cut"], n["burn_ovh"] = sm.loc["always_burn", "down_violation_cut_pct"], sm.loc["always_burn", "extra_energy_pct"]
    n["raw_viol_h"] = sm.loc["raw", "down_violations_per_node_hour"]

    ap = pd.read_csv(TABLES / "crossdata_ap_harmonized.csv")
    ap = ap[ap["workload"] == "all"]
    for r in ap.itertuples():
        k = f"x_{r.config}_{r.test_dataset}"
        n[f"{k}_ml"], n[f"{k}_rh"], n[f"{k}_lo"], n[f"{k}_hi"] = r.ap_ml, r.ap_rhythm, r.ap_diff_lo, r.ap_diff_hi
    tr = pd.read_csv(TABLES / "transfer_harmonized.csv")
    for r in tr.itertuples():
        m_ = f"{int(r.site_minutes)}" if r.setting == "lodo_shape_adapted" else ""
        k = f"tr_{r.setting}{m_}_{r.test_dataset}"
        if r.setting == "lodo_shape_adapted":  # mean and range over independent draws of local data
            n[f"{k}_ml"], n[f"{k}_min"], n[f"{k}_max"] = r.ap_ml_rep_mean, r.ap_ml_rep_min, r.ap_ml_rep_max
        else:
            n[f"{k}_ml"], n[f"{k}_lo"], n[f"{k}_hi"] = r.ap_ml, r.ap_diff_lo, r.ap_diff_hi
    pw = pd.read_csv(TABLES / "crossdata_ap_harmonized.csv")
    pw = pw[(pw["config"] == "pooled") & (pw["workload"] != "all")]
    n["sc_classes_sig"] = int(((pw["test_dataset"] == "supercloud") & (pw["ap_diff_lo"] > 0)).sum())
    n["sc_classes"] = int((pw["test_dataset"] == "supercloud").sum())
    # validation-chosen operating points per dataset (1 decision per second, src/crossdata.py)
    rd = pd.read_csv(TABLES / "crossdata_readiness_harmonized.csv")
    for r in rd.itertuples():
        k = f"rd_{r.config}_{r.test_dataset}_{r.source}_{int(r.target)}"
        n[f"{k}_cut"], n[f"{k}_armed"] = r.test_cut_pct, r.test_armed_pct

    st = dataset_stats()
    for d in st.index:
        n[f"{d}_node_h"], n[f"{d}_units"], n[f"{d}_test_units"] = st.loc[d, "node_h"], st.loc[d, "units"], st.loc[d, "test_units"]

    out = {}
    for k, v in n.items():
        if isinstance(v, str):
            out[k] = v
        elif k.endswith(("_units", "_test_units", "classes_sig", "classes")) or k.endswith("node_h"):
            out[k] = f"{v:,.0f}"
        elif k.startswith(("t8", "t9", "arm", "an", "rd_")) or k.endswith(("_cut", "_armed", "_ovh", "max_cut", "oracle_armed", "viol_h")) \
                or k in ("burn_cut", "burn_ovh") or re.match(r"t\d+_sb\d+_(diff|lo|hi)", k):
            out[k] = f"{v:.1f}"
        else:
            out[k] = f"{v:.2f}"
    out = {k: (f"$-${v[1:]}" if v.startswith("-") else v) for k, v in out.items()}  # typographic minus
    json.dump(out, open(OUT / "numbers.json", "w"), indent=1)
    return out


# ---------------------------------------------------------------- figures

def fig_readiness() -> None:
    par = pd.read_csv(TABLES / "regime_pareto_test.csv")
    p = par[par["latency_s"] == 1.0]
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    style = [("ml_aligned", "#b91c1c", "-", "Learned, aligned target"),
             ("rhythm_aligned", "#1d4ed8", "-", "Rhythm replay, aligned target"),
             ("ml_alarm", "#f59e0b", "--", "Learned, big-drop target"),
             ("rhythm_alarm", "#93c5fd", "--", "Rhythm, big-drop target")]
    for s, c, ls, lab in style:
        g = p[p["strategy"] == s].sort_values("armed_pct")
        ax.plot(g["armed_pct"], g["cut_pct"], ls, color=c, lw=1.4, label=lab)
    o = p[p["strategy"] == "oracle"]
    ax.scatter(o["armed_pct"], o["cut_pct"], marker="*", s=90, color="black", zorder=4, label="Oracle")
    a = par[par["strategy"] == "always_on"]
    ax.scatter(a["armed_pct"], a["cut_pct"], marker="D", s=30, color="#15803d", zorder=4, label="Always-on")
    ax.set_xlim(0, 102)
    ax.set_ylim(0, 102)
    ax.set_xlabel("Engaged time (%)", fontsize=8)
    ax.set_ylabel("Ramp violations removed (%)", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.grid(alpha=0.3, lw=0.5)
    ax.legend(fontsize=6, loc="lower right", frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "fig_readiness.pdf", bbox_inches="tight")
    plt.close(fig)


def fig_forest() -> None:
    ap = pd.read_csv(TABLES / "crossdata_ap_harmonized.csv")
    ap = ap[ap["workload"] == "all"]
    tr = pd.read_csv(TABLES / "transfer_harmonized.csv")
    rows = []
    for ds in ("nlr", "supercloud", "elsayed"):
        for cfg, lab in (("in_domain", "in-domain"), ("pooled", "pooled")):
            r = ap[(ap["config"] == cfg) & (ap["test_dataset"] == ds)].iloc[0]
            rows.append((DS_LABEL[ds], lab, r.ap_diff, r.ap_diff_lo, r.ap_diff_hi))
        r = tr[(tr["setting"] == "lodo_shape") & (tr["test_dataset"] == ds)].iloc[0]
        rows.append((DS_LABEL[ds], "unseen site, shape-only", r.ap_diff, r.ap_diff_lo, r.ap_diff_hi))
    fig, ax = plt.subplots(figsize=(3.5, 2.7))
    y = np.arange(len(rows))[::-1]
    for yi, (ds, lab, d, lo, hi) in zip(y, rows):
        c = "#b91c1c" if lo > 0 else ("#1d4ed8" if hi < 0 else "#6b7280")
        ax.errorbar(d, yi, xerr=[[d - lo], [hi - d]], fmt="o", color=c, ms=4, capsize=2, lw=1)
    ax.axvline(0, color="black", lw=0.7)
    ax.set_yticks(y, [f"{ds}: {lab}" for ds, _lab, *_ in rows for lab in [_lab]], fontsize=6)
    ax.set_xlabel("AP difference, learned minus rhythm", fontsize=8)
    ax.tick_params(axis="x", labelsize=7)
    ax.grid(axis="x", alpha=0.3, lw=0.5)
    fig.tight_layout()
    fig.savefig(OUT / "fig_forest.pdf", bbox_inches="tight")
    plt.close(fig)


def fig_example() -> None:
    """One NLR Llama LoRA window: power, aligned-target violations, and where each trigger arms."""
    from src.aligned import violation_starts
    from src.load import load_traces
    from src.simulate import NODE_RATED_W

    tr, meta = load_traces(only_model=True)
    tid = sorted(meta.loc[(meta["split"] == "test") & (meta["workload"] == "train_llama2_70b_lora"), "trace_id"])[0]
    p = tr.loc[tr["trace_id"] == tid, "power_w"].to_numpy(float)
    sc = pd.read_parquet(PROC_DIR / "aligned_scores_test_L1.parquet")
    sc = sc[sc["trace_id"] == tid]
    s0 = 3000
    win = slice(s0, s0 + 300)
    t = np.arange(len(p))[win] * 0.2
    fig, ax = plt.subplots(figsize=(3.5, 1.9))
    ax.plot(t, p[win] / 1e3, color="black", lw=1)
    v = violation_starts(p, 0.1 * NODE_RATED_W)
    v = v[(v >= s0) & (v < s0 + 300)]
    ax.scatter(v * 0.2, p[v] / 1e3, color="#b91c1c", s=12, zorder=3, label="limit violation")
    ax.set_xlabel("time (s)", fontsize=8)
    ax.set_ylabel("node GPU kW", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=6, frameon=False, loc="lower left")
    fig.tight_layout()
    fig.savefig(OUT / "fig_example.pdf")
    plt.close(fig)


# ---------------------------------------------------------------- main

def run() -> None:
    OUT.mkdir(exist_ok=True)
    nums = numbers()
    fig_readiness()
    fig_forest()
    fig_example()
    fill(OUT / "template.tex", OUT / "main.tex", nums)
    # arXiv version: self-contained folder (tex + figures) ready to tar and upload
    arx = OUT / "arxiv"
    if (arx / "template.tex").exists():
        for f in ("fig_readiness.pdf", "fig_forest.pdf", "fig_example.pdf"):
            shutil.copy(OUT / f, arx / f)
        fill(arx / "template.tex", arx / "main.tex", nums)


def fill(tpl_path: Path, out_path: Path, nums: dict[str, str]) -> None:
    """Replace every <<name>> in the template with its number; fail loudly on any missing name."""
    tpl = tpl_path.read_text()
    missing = sorted(set(re.findall(r"<<([a-zA-Z0-9_]+)>>", tpl)) - set(nums))
    if missing:
        raise KeyError(f"{tpl_path.name}: placeholders without numbers: {missing}")
    out_path.write_text(re.sub(r"<<([a-zA-Z0-9_]+)>>", lambda m: nums[m.group(1)], tpl))
    print(f"paper: wrote {out_path} with {len(nums)} numbers")


if __name__ == "__main__":
    run()
