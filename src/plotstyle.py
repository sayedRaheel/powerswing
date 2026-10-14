"""One consistent look for every chart in the report."""
from __future__ import annotations

import matplotlib.pyplot as plt

COLORS: dict[str, str] = {
    "raw": "#3b4a5a",
    "model": "#2a6fdb",
    "model2": "#14a39a",
    "model3": "#8a5cd6",
    "baseline": "#a3abb5",
    "drop": "#e0493b",
    "burn": "#e08a1e",
    "predictive": "#2a6fdb",
    "reactive": "#a3abb5",
    "good": "#1f9d55",
}

WORKLOAD_LABEL: dict[str, str] = {
    "train_llama2_70b_lora": "Train Llama2-70B LoRA",
    "train_stable_diffusion": "Train Stable Diffusion",
    "inference_offline": "Infer offline batch",
    "inference_online_finite": "Infer online (finite)",
    "inference_online_rate": "Infer online (rate)",
}


def apply_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#e6e9ed",
        "grid.linewidth": 0.6,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "legend.frameon": False,
        "font.family": "sans-serif",
    })
