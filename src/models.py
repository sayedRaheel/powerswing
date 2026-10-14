"""Step 5: learned models.

LightGBM on the engineered features: one regressor per horizon predicting the change in power,
and one binary classifier for "big drop starts within 5 s".

The PyTorch models (tiny TCN, zero-shot Chronos) live in src/nets.py. They run in a separate
process because PyTorch and LightGBM ship different OpenMP runtimes that crash when loaded together
on macOS.
"""
from __future__ import annotations

from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import pandas as pd

from src.config import HORIZONS_S, SEED

# ----------------------------------------------------------------------------- LightGBM

LGB_REG_PARAMS: dict = {
    "objective": "l1",
    "learning_rate": 0.05,
    "num_leaves": 63,
    "min_data_in_leaf": 100,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "lambda_l2": 1.0,
    "seed": SEED,
    "deterministic": True,
    "num_threads": 8,
    "verbose": -1,
}
LGB_CLF_PARAMS: dict = {**LGB_REG_PARAMS, "objective": "binary", "metric": "average_precision"}


@dataclass
class LGBModels:
    regs: dict[int, lgb.Booster]
    clf: lgb.Booster
    features: list[str]

    def forecast(self, df: pd.DataFrame) -> dict[int, np.ndarray]:
        X = df[self.features]
        return {h: df["p"].to_numpy() + self.regs[h].predict(X, num_threads=8) for h in self.regs}

    def drop_score(self, df: pd.DataFrame) -> np.ndarray:
        return self.clf.predict(df[self.features], num_threads=8)


def train_lgb(train: pd.DataFrame, val: pd.DataFrame, features: list[str], rounds: int = 2000,
              learning_rate: float = 0.05) -> LGBModels:
    """Fit horizon regressors on the power *change* and the drop classifier, early-stopped on val."""
    reg_params = {**LGB_REG_PARAMS, "learning_rate": learning_rate}
    regs: dict[int, lgb.Booster] = {}
    for h in HORIZONS_S:
        ytr = train[f"y_{h}s"] - train["p"]
        yva = val[f"y_{h}s"] - val["p"]
        dtr = lgb.Dataset(train[features], ytr, free_raw_data=False)
        dva = lgb.Dataset(val[features], yva, reference=dtr)
        regs[h] = lgb.train(reg_params, dtr, rounds, valid_sets=[dva],
                            callbacks=[lgb.early_stopping(100, verbose=False)])
    pos = train["y_drop"].mean()
    params = {**LGB_CLF_PARAMS, "learning_rate": learning_rate, "scale_pos_weight": float((1 - pos) / max(pos, 1e-6)) ** 0.5}
    dtr = lgb.Dataset(train[features], train["y_drop"])
    dva = lgb.Dataset(val[features], val["y_drop"], reference=dtr)
    clf = lgb.train(params, dtr, rounds, valid_sets=[dva], callbacks=[lgb.early_stopping(100, verbose=False)])
    return LGBModels(regs, clf, features)
