"""Steps 3 to 6: build datasets, fit baselines and models, evaluate, save predictions and charts."""
from __future__ import annotations

import json
import subprocess
import sys
import time

import numpy as np
import pandas as pd

from src.baselines import all_baseline_forecasts, rhythm_alarm_score
from src.config import HORIZONS_S, PROC_DIR, REPORT_DIR, ROOT
from sklearn.metrics import average_precision_score

from src.evaluate import (
    PICK_LOG,
    event_eval,
    forecast_table,
    pick_threshold,
    plot_error_by_horizon,
    plot_model_bars,
    plot_overlays,
    plot_pr,
    pr_curve,
    prep_rows,
    sample_metrics,
)
from src.features import build_features, feature_columns, trace_table
from src.load import load_traces
from src.models import train_lgb
from src.utils import power_dict, time_per_call

TRAIN_STRIDE = 5  # 1 decision per second for training rows
TABLES = REPORT_DIR / "tables"


def build_tables(traces: pd.DataFrame, meta: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Feature/target tables per split. Train at 1 Hz, val/test at full 5 Hz (needed for lead time)."""
    out: dict[str, list[pd.DataFrame]] = {"train": [], "val": [], "test": []}
    wl = dict(zip(meta["trace_id"], meta["workload"]))
    split = dict(zip(meta["trace_id"], meta["split"]))
    for tid, g in traces.groupby("trace_id", sort=True):
        p = g["power_w"].to_numpy(dtype=float)
        s = split[tid]
        df = trace_table(tid, p, stride=TRAIN_STRIDE if s == "train" else 1)
        df["workload"] = wl[tid]
        out[s].append(df)
    return {k: pd.concat(v, ignore_index=True) for k, v in out.items()}


def drop_eval_block(rows: pd.DataFrame, y: np.ndarray, score: np.ndarray, thr: float, power) -> dict:
    return {**event_eval(rows, score, thr, power), **sample_metrics(y, score, thr)}


def run(log=print, reuse_nets: bool = False) -> dict:
    """reuse_nets=True skips retraining the PyTorch models if their outputs already exist."""
    TABLES.mkdir(parents=True, exist_ok=True)
    traces, meta = load_traces(only_model=True)
    power = power_dict(traces)
    t0 = time.time()
    tabs = build_tables(traces, meta)
    for k, v in tabs.items():
        v.to_parquet(PROC_DIR / f"table_{k}.parquet", index=False)  # reused by generalize.py
    tr, va, te = tabs["train"], tabs["val"], tabs["test"]
    feats = feature_columns(tr.drop(columns=["workload"]))
    log(f"tables built in {time.time() - t0:.0f}s: train {len(tr):,} val {len(va):,} test {len(te):,} rows, {len(feats)} features")

    # ---------------- baselines
    preds: dict[str, dict[int, np.ndarray]] = all_baseline_forecasts(te)

    # ---------------- LightGBM
    t0 = time.time()
    va_es = va.iloc[::TRAIN_STRIDE]
    lgbm = train_lgb(tr, va_es, feats)
    preds["lightgbm"] = lgbm.forecast(te)
    log(f"LightGBM trained in {time.time() - t0:.0f}s, rounds={[b.best_iteration for b in lgbm.regs.values()]}, clf={lgbm.clf.best_iteration}")

    lgbm.clf.save_model(str(PROC_DIR / "lgb_clf.txt"))
    for h, b in lgbm.regs.items():
        b.save_model(str(PROC_DIR / f"lgb_reg_{h}s.txt"))

    # ---------------- TCN + Chronos in a separate process (OpenMP clash between torch and LightGBM)
    t0 = time.time()
    if not (reuse_nets and (PROC_DIR / "nets_test.parquet").exists()):
        subprocess.run([sys.executable, "-m", "src.nets"], check=True, cwd=ROOT)
    nets = pd.read_parquet(PROC_DIR / "nets_test.parquet")
    preds["tcn"] = {h: nets[f"tcn_{h}s"].to_numpy(dtype=float) for h in HORIZONS_S}
    tcn_score_te = nets["score_tcn"].to_numpy(dtype=float)
    log(f"PyTorch stage finished in {time.time() - t0:.0f}s")

    # ---------------- model selection on VALIDATION only (test stays untouched until the end)
    va_fc = {"lightgbm": lgbm.forecast(va)}
    tcn_va = pd.read_parquet(PROC_DIR / "nets_val_forecast_tcn.parquet")
    va_fc["tcn"] = {h: tcn_va[f"tcn_{h}s"].to_numpy(dtype=float) for h in HORIZONS_S}
    va_mae5 = {k: float(np.mean(np.abs(v[5] - va["y_5s"].to_numpy()))) for k, v in va_fc.items()}
    best_fc = min(va_mae5, key=va_mae5.get)
    log(f"validation MAE 5 s: {va_mae5} -> primary forecaster {best_fc}")

    # ---------------- forecasting metrics (full test set, all but Chronos)
    ft = forecast_table(te, preds)
    ftw = forecast_table(te, preds, by="workload")

    # ---------------- Chronos zero-shot, compared on its stratified subset (same points for every model)
    sub_idx = np.load(PROC_DIR / "chronos_subset_idx.npy")
    sub = te.iloc[sub_idx].reset_index(drop=True)
    sub_preds = {k: {h: v[h][sub_idx] for h in HORIZONS_S} for k, v in preds.items()}
    ch_path = PROC_DIR / "nets_chronos.parquet"
    if ch_path.exists():
        ch = pd.read_parquet(ch_path)
        sub_preds["chronos_bolt_small"] = {h: ch[f"chronos_bolt_small_{h}s"].to_numpy() for h in HORIZONS_S}
    tf_path = PROC_DIR / "nets_timesfm.parquet"
    if tf_path.exists():
        tf = pd.read_parquet(tf_path)
        sub_preds["timesfm_2p5"] = {h: tf[f"timesfm_2p5_{h}s"].to_numpy() for h in HORIZONS_S}
    ft_sub = forecast_table(sub, sub_preds)

    # ---------------- drop warning
    rows_va, rows_te = prep_rows(va), prep_rows(te)
    y_te = te["y_drop"].to_numpy()
    scores_va = {
        "lightgbm": lgbm.drop_score(va),
        "tcn": np.load(PROC_DIR / "nets_val_score_tcn.npy").astype(float),
        "rhythm_alarm": rhythm_alarm_score(va),
    }
    scores_te = {"lightgbm": lgbm.drop_score(te), "tcn": tcn_score_te, "rhythm_alarm": rhythm_alarm_score(te)}
    drop_rows, thresholds = [], {}
    for name in scores_te:
        thr = pick_threshold(rows_va, scores_va[name], power)
        thresholds[name] = thr
        r = drop_eval_block(rows_te, y_te, scores_te[name], thr, power)
        drop_rows.append({"model": name, **r})
    drop_tab = pd.DataFrame(drop_rows)
    # primary classifier chosen by VALIDATION average precision
    y_va = va["y_drop"].to_numpy()
    va_ap = {k: float(average_precision_score(y_va, s)) for k, s in scores_va.items() if k != "rhythm_alarm"}
    best_clf = max(va_ap, key=va_ap.get)
    log(f"validation AP: {va_ap} -> primary classifier {best_clf}; threshold searches: {PICK_LOG}")
    dw = []
    for w in sorted(te["workload"].unique()):
        m = (te["workload"] == w).to_numpy()
        r = prep_rows(te[m])
        dw.append({"workload": w, **drop_eval_block(r, y_te[m], scores_te[best_clf][m], thresholds[best_clf], power)})
    drop_by_wl = pd.DataFrame(dw)

    # ---------------- latency (single prediction, CPU)
    lat = latency_table(lgbm, power, te)

    # ---------------- save
    ft.to_csv(TABLES / "forecast_overall.csv", index=False)
    ftw.to_csv(TABLES / "forecast_by_workload.csv", index=False)
    ft_sub.to_csv(TABLES / "forecast_subset_with_chronos.csv", index=False)
    drop_tab.to_csv(TABLES / "drop_warning.csv", index=False)
    drop_by_wl.to_csv(TABLES / "drop_warning_by_workload.csv", index=False)
    lat.to_csv(TABLES / "latency.csv", index=False)
    keep = te[["trace_id", "idx", "workload", "p", "y_drop"] + [f"y_{h}s" for h in HORIZONS_S]].copy()
    for k, v in preds.items():
        for h in HORIZONS_S:
            keep[f"{k}_{h}s"] = v[h].astype(np.float32)
    for k, v in scores_te.items():
        keep[f"score_{k}"] = v.astype(np.float32)
    keep.to_parquet(PROC_DIR / "test_predictions.parquet", index=False)
    json.dump({"thresholds": thresholds, "best_classifier": best_clf, "best_forecaster": best_fc,
               "val_ap": va_ap, "val_mae5": va_mae5, "threshold_search": PICK_LOG, "features": feats},
              open(PROC_DIR / "model_info.json", "w"), indent=1)

    # ---------------- charts
    plot_model_bars(ft, 5, "model_comparison_5s.png", "Forecast error 5 s ahead, all test traces")
    if len(ft_sub):
        plot_model_bars(ft_sub, 5, "model_comparison_5s_with_chronos.png",
                        f"Forecast error 5 s ahead, {len(sub):,} sampled test points (incl. zero-shot Chronos)")
        plot_error_by_horizon(ft_sub, "error_by_horizon_with_chronos.png", "Error grows with horizon (sampled test points)")
    plot_error_by_horizon(ft, "error_by_horizon.png", "Error by forecast horizon, all test traces")
    plot_pr({k: pr_curve(y_te, s) for k, s in scores_te.items()}, "drop_warning_pr_curve.png")
    picks = overlay_picks(te, power)
    plot_overlays(te, preds, scores_te["lightgbm"], thresholds["lightgbm"], power, picks, 5, "forecast_overlays_5s.png")

    log(ft[ft["horizon_s"] == 5].to_string(index=False))
    log(drop_tab.round(3).to_string(index=False))
    return {"forecast": ft, "drop": drop_tab, "thresholds": thresholds}


def overlay_picks(te: pd.DataFrame, power: dict[str, np.ndarray]) -> list[tuple[str, int, str]]:
    """One illustrative 2-minute window per workload family, centred on a drop."""
    from src.events import detect_drops
    from src.plotstyle import WORKLOAD_LABEL

    picks = []
    for w in ["train_llama2_70b_lora", "train_stable_diffusion", "inference_offline", "inference_online_finite"]:
        tids = sorted(te.loc[te["workload"] == w, "trace_id"].unique())
        for tid in tids:
            on = detect_drops(power[tid])
            on = on[(on > 400) & (on < len(power[tid]) - 400)]
            if len(on) >= 2:
                picks.append((tid, int(on[len(on) // 2]), WORKLOAD_LABEL[w]))
                break
    return picks


def latency_table(lgbm, power: dict[str, np.ndarray], te: pd.DataFrame) -> pd.DataFrame:
    """Median single-prediction latency on CPU (1 thread), including feature computation where relevant."""
    hist = power[te["trace_id"].iloc[0]][:1200]  # 240 s of history covers every feature window

    def lgb_call() -> None:
        X = build_features(hist).iloc[[-1]][lgbm.features]
        for b in lgbm.regs.values():
            b.predict(X, num_threads=1)
        lgbm.clf.predict(X, num_threads=1)

    rows = {
        "LightGBM (feature computation + 3 horizons + drop classifier)": time_per_call(lgb_call, 50),
        "rhythm / persistence / moving-avg baselines (feature computation)": time_per_call(lambda: build_features(hist), 50),
    }
    rows.update(json.load(open(PROC_DIR / "nets_latency.json")))
    return pd.DataFrame({"model": list(rows), "ms_per_prediction": list(rows.values())}).round(2)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--reuse-nets", action="store_true", help="reuse cached TCN/Chronos/TimesFM outputs")
    run(reuse_nets=ap.parse_args().reuse_nets)
