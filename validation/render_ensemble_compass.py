"""ENSEMBLE static compass + headline aggregate numbers (presentation-only; abm/
UNCHANGED). The published web ANIMATION keeps representative seed 1 (per-agent
trajectory continuity + characters + ghost-fade can't be pooled across seeds). The
static/reference compass and the headline overlap/separation numbers use the model's
ENSEMBLE: agents POOLED across clean seeds 0-7 into one representative density (a
legitimate object — it is the model's own mixture distribution; the pooled centroids
/ gaps / R-in-LL share equal the multi-seed ensemble center). This reflects the
model's true center (econ@1996 ~0.40, R-in-LL ~12.3%) instead of seed 1's high
realization (R-in-LL 18.7%). It is representativeness, NOT warming toward ANES.
"""
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
import sys
sys.path.insert(0, str(ROOT))
from scripts.anes_preset import ANES_FULL_KWARGS
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to

PARTY_COLORS = {0: "#1f3565", 1: "#8b2530"}
GRID = np.linspace(-1.05, 1.05, 81); GX, GY = np.meshgrid(GRID, GRID)
GPOS = np.vstack([GX.ravel(), GY.ravel()]); BW = 0.30
SEEDS = list(range(8))
TICKS = {1996: 48, 2020: 120}
ANES_CENT = {1996: {0: (-0.070, 0.067), 1: (0.375, 0.374)},
             2020: {0: (-0.418, -0.420), 1: (0.420, 0.363)}}
# ANES partisan gaps / R-in-LL (validation/anchors_anes.json + quadrant_occupancy)
ANES = {1996: dict(eg=0.445, cg=0.307, sep=0.540, rll=0.068),
        2020: dict(eg=0.838, cg=0.783, sep=1.147, rll=None)}  # 2020 R-LL below


def pooled(seeds, ticks):
    """Pool agent (pos,party) across clean unprotected seeds at each tick."""
    acc = {t: {"pos": [], "party": []} for t in ticks}
    for s in seeds:
        kw = dict(ANES_FULL_KWARGS)
        eng = build_engine(seed=s, **kw)
        sched = build_schedule(factional_seeding=False, faction_anchor_events=True,
                               evidence_regrade=kw["evidence_regrade"],
                               exogenous_shocks=kw["exogenous_shocks"])
        want = set(ticks)
        for t in range(1, max(ticks) + 1):
            run_to(eng, sched, t)
            if t in want:
                acc[t]["pos"].append(np.array([a.state.ideology for a in eng.agents]))
                acc[t]["party"].append(np.array([a.state.attrs.get("party") for a in eng.agents]))
    return {t: (np.vstack(acc[t]["pos"]), np.concatenate(acc[t]["party"])) for t in ticks}


def metrics(pos, party):
    D, R = pos[party == 0], pos[party == 1]
    eg = float(R[:, 0].mean() - D[:, 0].mean()); cg = float(R[:, 1].mean() - D[:, 1].mean())
    return dict(eg=eg, cg=cg, sep=float(np.hypot(eg, cg)),
                rll=float(np.mean((R[:, 0] <= 0) & (R[:, 1] <= 0))),
                mD=D.mean(0), mR=R.mean(0))


def kde(xy):
    if xy.shape[0] < 5:
        return None
    return gaussian_kde(xy.T, bw_method=BW)(GPOS).reshape(GX.shape)


def draw(ax, pos, party, yr, m):
    msk = np.isin(party, (0, 1))
    f = kde(pos[msk])
    if f is not None:
        ax.contourf(GRID, GRID, f, levels=8, cmap="Greys", alpha=0.35)
    for p in (0, 1):
        fp = kde(pos[party == p])
        if fp is not None:
            ax.contour(GRID, GRID, fp, levels=4, colors=PARTY_COLORS[p], linewidths=0.9, alpha=0.85)
        ax.scatter(*(m["mR"] if p == 1 else m["mD"]), c=PARTY_COLORS[p], s=55,
                   edgecolor="black", linewidth=0.7, zorder=6)
        ex, cy = ANES_CENT[yr][p]
        ax.scatter(ex, cy, marker="*", s=240, facecolor="none", edgecolor=PARTY_COLORS[p],
                   linewidth=1.6, zorder=7)
    ax.axhline(0, color="k", lw=0.5, alpha=0.35); ax.axvline(0, color="k", lw=0.5, alpha=0.35)
    ax.set_xlim(-1.05, 1.05); ax.set_ylim(-1.05, 1.05); ax.set_aspect("equal")
    ax.set_xlabel("Economic (← lib   cons →)", fontsize=9)
    ax.set_title(f"{yr} (ensemble, 8 seeds pooled)\nsep={m['sep']:.3f}  econ-gap={m['eg']:.3f}  "
                 f"R-in-LL={m['rll']*100:.0f}%", fontsize=10)


pool = pooled(SEEDS, list(TICKS.values()))
print("=== ENSEMBLE headline numbers (pooled clean seeds 0-7) ===")
mm = {}
for yr, t in TICKS.items():
    m = metrics(*pool[t]); mm[yr] = m
    print(f"{yr}: econ-gap {m['eg']:.3f}  cult-gap {m['cg']:.3f}  sep {m['sep']:.3f}  "
          f"R-in-LL {m['rll']*100:.1f}%")

fig, axes = plt.subplots(1, 2, figsize=(11.2, 5.9), sharex=True, sharey=True)
for ax, yr in zip(axes, (1996, 2020)):
    draw(ax, *pool[TICKS[yr]], yr, mm[yr])
axes[0].set_ylabel("Cultural (← lib   cons →)", fontsize=9)
legend = [Line2D([0], [0], color=PARTY_COLORS[0], lw=2, label="Democrats"),
          Line2D([0], [0], color=PARTY_COLORS[1], lw=2, label="Republicans"),
          Line2D([0], [0], marker="o", color="w", markerfacecolor="#444", markersize=8, label="model centroid (ensemble)"),
          Line2D([0], [0], marker="*", color="w", markeredgecolor="#444", markerfacecolor="none", markersize=14, label="ANES centroid")]
fig.legend(handles=legend, loc="lower center", ncol=4, fontsize=9, frameon=False, bbox_to_anchor=(0.5, -0.02))
fig.suptitle("ENSEMBLE static compass (8 seeds pooled) — the model's representative center, "
             "not a single high-realization seed", fontsize=12)
fig.tight_layout(rect=[0, 0.05, 1, 0.96])
p = OUT / "ensemble_compass_1996_2020.png"; fig.savefig(p, dpi=150); plt.close(fig)
print("WROTE", p)
json.dump({str(y): {k: (float(v) if np.isscalar(v) else None) for k, v in mm[y].items() if k != 'mD' and k != 'mR'} for y in mm},
          open(Path(__file__).resolve().parent / "ensemble_headline.json", "w"), indent=1)
