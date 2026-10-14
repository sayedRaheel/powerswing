"""Generalisation check: retrain LightGBM with one whole workload type removed from training and
validation, then test only on that unseen workload. Compared with the rhythm baseline (which needs
no training) and with the in-distribution LightGBM numbers.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.baselines import rhythm_alarm_score
from src.config import PROC_DIR, REPORT_DIR
from src.evaluate import event_eval, forecast_metrics, pick_threshold, prep_rows, sample_metrics
from src.load import load_traces
from src.utils import power_dict
from src.models import train_lgb

TABLES = REPORT_DIR / "tables"


def run(log=print) -> pd.DataFrame:
    tr = pd.read_parquet(PROC_DIR / "table_train.parquet")
    va = pd.read_parquet(PROC_DIR / "table_val.parquet")
    te = pd.read_parquet(PROC_DIR / "table_test.parquet")
    feats = json.load(open(PROC_DIR / "model_info.json"))["features"]
    traces, _ = load_traces(only_model=True)
    power = power_dict(traces)
    rows = []
    for w in sorted(te["workload"].unique()):
        trw, vaw = tr[tr["workload"] != w], va[va["workload"] != w].iloc[::5]
        tew = te[te["workload"] == w].reset_index(drop=True)
        m = train_lgb(trw, vaw, feats, rounds=600, learning_rate=0.15)  # faster settings for 5 retrains
        fc = m.forecast(tew)
        score = m.drop_score(tew)
        # threshold picked on the *other* workloads' validation data (the unseen one is truly unseen)
        va_full = va[va["workload"] != w].reset_index(drop=True)
        thr = pick_threshold(prep_rows(va_full), m.drop_score(va_full), power)
        ev = event_eval(prep_rows(tew), score, thr, power)
        sm = sample_metrics(tew["y_drop"].to_numpy(), score, thr)
        r_score = rhythm_alarm_score(tew)
        r = {"held_out_workload": w}
        for h in (1, 5, 10):
            y = tew[f"y_{h}s"].to_numpy()
            r[f"lgb_mae_{h}s"] = forecast_metrics(y, fc[h])["MAE"]
            r[f"rhythm_mae_{h}s"] = forecast_metrics(y, tew[f"rhythm_{h}s"].to_numpy())["MAE"]
            r[f"persist_mae_{h}s"] = forecast_metrics(y, tew["p"].to_numpy())["MAE"]
        r["lgb_gain_vs_rhythm_5s_pct"] = 100 * (1 - r["lgb_mae_5s"] / r["rhythm_mae_5s"])
        r.update({"drop_recall_1s": ev["recall_1s"], "drop_mean_lead_s": ev["mean_lead_s"],
                  "false_alarms_per_hour": ev["false_alarms_per_hour"], "drop_AP": sm["AP"],
                  "rhythm_alarm_AP": sample_metrics(tew["y_drop"].to_numpy(), r_score, np.median(r_score))["AP"]})
        rows.append(r)
        log(f"  held out {w}: LGB 5s MAE {r['lgb_mae_5s']:.0f} vs rhythm {r['rhythm_mae_5s']:.0f}, drop recall@1s {ev['recall_1s']:.2f}")
    df = pd.DataFrame(rows)
    TABLES.mkdir(parents=True, exist_ok=True)
    df.round(3).to_csv(TABLES / "generalization_lowo.csv", index=False)
    return df


if __name__ == "__main__":
    run()
