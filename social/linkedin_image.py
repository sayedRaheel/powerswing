"""LinkedIn image: a real NLR power trace with limit violations, plus the two headline results."""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.aligned import violation_starts
from src.load import load_traces
from src.simulate import NODE_RATED_W

OUT = Path("social/linkedin_image.png")
INK, MUTED, RED, BLUE, GREY, BG = "#0f172a", "#64748b", "#dc2626", "#2563eb", "#cbd5e1", "#ffffff"

tr, meta = load_traces(only_model=True)
tid = sorted(meta.loc[(meta["split"] == "test") & (meta["workload"] == "train_llama2_70b_lora"), "trace_id"])[0]
p = tr.loc[tr["trace_id"] == tid, "power_w"].to_numpy(float)
s0, n = 3000, 300
t = np.arange(n) * 0.2
v = violation_starts(p, 0.1 * NODE_RATED_W)
v = v[(v >= s0) & (v < s0 + n)]

plt.rcParams["font.family"] = "Helvetica Neue"
fig = plt.figure(figsize=(12, 12), dpi=100, facecolor=BG)

fig.text(0.07, 0.93, "Can ML predict GPU power swings?", fontsize=40, weight="bold", color=INK)
fig.text(0.07, 0.885, "AI training makes data-centre power jump within seconds. Here is a real one.",
         fontsize=19, color=MUTED)

ax = fig.add_axes([0.07, 0.56, 0.86, 0.29])
ax.plot(t, p[s0:s0 + n] / 1e3, color=INK, lw=1.6)
ax.scatter((v - s0) * 0.2, p[v] / 1e3, color=RED, s=55, zorder=3, label="swing faster than the grid limit")
ax.set_xlabel("seconds", fontsize=15, color=MUTED)
ax.set_ylabel("GPU power (kW)", fontsize=15, color=MUTED)
ax.tick_params(labelsize=13, colors=MUTED)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.legend(fontsize=15, frameon=False, loc="lower left")
ax.text(1.0, 1.02, "H100 node, Llama 2 70B fine-tuning (public NLR data)", transform=ax.transAxes,
        ha="right", fontsize=12, color=MUTED)


def bars(rect: list[float], title: str, vals: list[float], labels: list[str], fmt: str, colors: list[str],
         xmax: float) -> None:
    a = fig.add_axes(rect)
    y = np.arange(len(vals))[::-1]
    a.barh(y, vals, color=colors, height=0.6)
    for yi, val, lab in zip(y, vals, labels):
        a.text(0, yi + 0.42, lab, fontsize=16, color=INK, va="bottom")
        a.text(val + xmax * 0.02, yi, fmt.format(val), fontsize=24, weight="bold", color=INK, va="center")
    a.set_xlim(0, xmax * 1.25)
    a.set_ylim(-0.6, len(vals) - 0.1)
    a.axis("off")
    a.set_title(title, fontsize=20, weight="bold", color=INK, loc="left", pad=14)


bars([0.07, 0.25, 0.38, 0.22], "Prediction quality", [0.67, 0.96],
     ["Follow the training rhythm", "ML model"], "{:.2f}", [GREY, BLUE], 1.0)
bars([0.55, 0.25, 0.38, 0.22], "Smoother on-time to remove 90%", [99, 48],
     ["Follow the training rhythm", "ML model"], "{:.0f}%", [GREY, BLUE], 100)

fig.text(0.07, 0.185, "To remove 90% of the swings that break the grid limit,", fontsize=17, color=INK)
fig.text(0.07, 0.15, "the ML-triggered smoother runs about half as often, so far less energy is wasted.",
         fontsize=17, color=INK)
fig.text(0.07, 0.07, "Sayed Raheel  |  github.com/sayedRaheel/powerswing", fontsize=14, color=MUTED)

OUT.parent.mkdir(exist_ok=True)
fig.savefig(OUT, facecolor=BG)
print(OUT.resolve())
