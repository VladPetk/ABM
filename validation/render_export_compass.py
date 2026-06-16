"""Re-render the 1996 + 2020 compass from the CORRECTED published export
(web/data/baseline/baseline.json — the representative canonical seed). Confirms the
separation the demo now shows. Compass style matches scripts/anes_2d_compass.py."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.stats import gaussian_kde

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "figures"; OUT.mkdir(exist_ok=True)
PARTY_COLORS = {0: "#1f3565", 1: "#8b2530"}
GRID = np.linspace(-1.05, 1.05, 81)
GX, GY = np.meshgrid(GRID, GRID); GPOS = np.vstack([GX.ravel(), GY.ravel()])
BW = 0.28
# ANES partisan centroids (validation/anchors_anes.json) for reference stars.
ANES = {1996: {0: (-0.070, 0.067), 1: (0.375, 0.374)},
        2020: {0: (-0.418, -0.420), 1: (0.420, 0.363)}}

d = json.load(open(ROOT / "web/data/baseline/baseline.json"))


def at(yr):
    t = int(round((yr - d["tick_0_year"]) * d["ticks_per_year"]))
    tk = d["ticks"][t]
    return np.array(tk["positions"]), np.array(tk["party"])


def kde(xy):
    if xy.shape[0] < 5:
        return None
    return gaussian_kde(xy.T, bw_method=BW)(GPOS).reshape(GX.shape)


def draw(ax, yr):
    pos, party = at(yr)
    m = np.isin(party, (0, 1))
    f = kde(pos[m])
    if f is not None:
        ax.contourf(GRID, GRID, f, levels=8, cmap="Greys", alpha=0.35)
    for p in (0, 1):
        sub = pos[party == p]
        fp = kde(sub)
        if fp is not None:
            ax.contour(GRID, GRID, fp, levels=4, colors=PARTY_COLORS[p], linewidths=0.9, alpha=0.85)
        if len(sub):
            ax.scatter(*sub.mean(0), c=PARTY_COLORS[p], s=55, edgecolor="black", linewidth=0.7, zorder=6)
        ex, cy = ANES[yr][p]
        ax.scatter(ex, cy, marker="*", s=240, facecolor="none", edgecolor=PARTY_COLORS[p], linewidth=1.6, zorder=7)
    R, D = pos[party == 1], pos[party == 0]
    sep = float(np.hypot(R[:, 0].mean() - D[:, 0].mean(), R[:, 1].mean() - D[:, 1].mean()))
    eg = float(R[:, 0].mean() - D[:, 0].mean())
    ax.axhline(0, color="black", lw=0.5, alpha=0.35); ax.axvline(0, color="black", lw=0.5, alpha=0.35)
    ax.set_xlim(-1.05, 1.05); ax.set_ylim(-1.05, 1.05); ax.set_aspect("equal")
    ax.set_title(f"{yr}   sep={sep:.3f}  econ-gap={eg:.3f}", fontsize=11)
    ax.set_xlabel("Economic (← lib   cons →)", fontsize=9)


fig, axes = plt.subplots(1, 2, figsize=(11.2, 5.9), sharex=True, sharey=True)
draw(axes[0], 1996); draw(axes[1], 2020)
axes[0].set_ylabel("Cultural (← lib   cons →)", fontsize=9)
legend = [Line2D([0], [0], color=PARTY_COLORS[0], lw=2, label="Democrats"),
          Line2D([0], [0], color=PARTY_COLORS[1], lw=2, label="Republicans"),
          Line2D([0], [0], marker="o", color="w", markerfacecolor="#444", markersize=8, label="model centroid"),
          Line2D([0], [0], marker="*", color="w", markeredgecolor="#444", markerfacecolor="none", markersize=14, label="ANES centroid")]
fig.legend(handles=legend, loc="lower center", ncol=4, fontsize=9, frameon=False, bbox_to_anchor=(0.5, -0.02))
fig.suptitle("Corrected published export (Method-B ensemble subsample) — 1996 & 2020 compass", fontsize=12)
fig.tight_layout(rect=[0, 0.05, 1, 0.96])
p = OUT / "methodb_published_1996_2020.png"; fig.savefig(p, dpi=150); plt.close(fig)
print("WROTE", p)
