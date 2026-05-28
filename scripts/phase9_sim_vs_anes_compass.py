"""Phase 9 — Side-by-side comparison: simulated engine vs ANES,
per decade bucket. Each row is a decade; left column = ANES (pooled
across the decade's ANES waves), right column = polarlab engine
at that decade endpoint (pooled across N seeds).

Decade bucketing matches phase9_anes_target_builder.py:
  1980 ← 1986, 1988
  1990 ← 1990, 1992, 1994, 1996, 1998
  2000 ← 2000, 2004, 2008
  2010 ← 2012, 2016
  2020 ← 2020, 2024

Output: docs/phase9_empirical/sim_vs_anes_side_by_side.png
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

# Phase 9 §11.7-E — snapshot ticks aligned to ANES bucket centroids.
DECADE_TICKS = [
    (1980, 21),    # 1987 (ANES 1986+1988 bucket centre)
    (1990, 42),    # 1994 (ANES 1990-1998 bucket centre)
    (2000, 72),    # 2004 (ANES 2000-2008 bucket centre)
    (2010, 102),   # 2014 (ANES 2012+2016 bucket centre)
    (2020, 126),   # 2022 (ANES 2020+2024 bucket centre)
]
ANES_DECADE_WAVES = {
    1980: [1986, 1988],
    1990: [1990, 1992, 1994, 1996, 1998],
    2000: [2000, 2004, 2008],
    2010: [2012, 2016],
    2020: [2020, 2024],
}

GRID_LO, GRID_HI, GRID_N = -1.05, 1.05, 81
GRID_AXIS = np.linspace(GRID_LO, GRID_HI, GRID_N)
_xx, _yy = np.meshgrid(GRID_AXIS, GRID_AXIS, indexing="ij")
_GRID_PTS = np.vstack([_xx.ravel(), _yy.ravel()])
_CELL_AREA = (GRID_AXIS[1] - GRID_AXIS[0]) ** 2

PARTY_COLORS = {"D": "tab:blue", "R": "tab:red"}


def _build_kwargs():
    # Import the source-of-truth preset from the scorer.
    from scripts.phase9_anes_score import PRESETS
    return dict(PRESETS["anes_full"])


def _worker(seed: int) -> dict:
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to

    eng = build_engine(seed=seed, **_build_kwargs())
    sched = build_schedule(factional_seeding=False, faction_anchor_events=True)
    # Phase 9 §11.7-E — every snapshot runs to its bucket-centroid tick.
    snapshots = {}
    for year, tick in DECADE_TICKS:
        run_to(eng, sched, tick)
        snapshots[year] = {
            "pos": np.array([a.state.ideology for a in eng.agents], dtype=float),
            "party": np.array(
                [a.state.attrs.get("party", -1) for a in eng.agents], dtype=int
            ),
        }
    return snapshots


def _kde_grid(xy, bw):
    if len(xy) < 5:
        return np.full((GRID_N, GRID_N), np.nan)
    kde = gaussian_kde(xy.T, bw_method=bw)
    z = kde(_GRID_PTS).reshape(GRID_N, GRID_N)
    integ = z.sum() * _CELL_AREA
    if integ > 0:
        z = z / integ
    return z


def _ovl(fA, fB):
    if np.isnan(fA).any() or np.isnan(fB).any():
        return float("nan")
    return float(np.minimum(fA, fB).sum() * _CELL_AREA)


def _draw_panel(ax, xy_d, xy_r, xy_all, bw, title, fAll=None, fD=None, fR=None):
    if fAll is None:
        fAll = _kde_grid(xy_all, bw)
    if fD is None:
        fD = _kde_grid(xy_d, bw)
    if fR is None:
        fR = _kde_grid(xy_r, bw)
    if not np.isnan(fAll).any():
        ax.contourf(GRID_AXIS, GRID_AXIS, fAll.T, levels=8, cmap="Greys", alpha=0.35)
    if not np.isnan(fD).any():
        ax.contour(GRID_AXIS, GRID_AXIS, fD.T, levels=4,
                   colors=PARTY_COLORS["D"], linewidths=1.0, alpha=0.9)
    if not np.isnan(fR).any():
        ax.contour(GRID_AXIS, GRID_AXIS, fR.T, levels=4,
                   colors=PARTY_COLORS["R"], linewidths=1.0, alpha=0.9)
    if len(xy_d):
        cD = xy_d.mean(axis=0)
        ax.scatter([cD[0]], [cD[1]], c=PARTY_COLORS["D"], s=50,
                   edgecolor="black", linewidth=0.6, zorder=5)
    if len(xy_r):
        cR = xy_r.mean(axis=0)
        ax.scatter([cR[0]], [cR[1]], c=PARTY_COLORS["R"], s=50,
                   edgecolor="black", linewidth=0.6, zorder=5)
    ax.axhline(0, color="black", lw=0.4, alpha=0.3)
    ax.axvline(0, color="black", lw=0.4, alpha=0.3)
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.set_title(title, fontsize=9)
    return _ovl(fD, fR)


def main():
    from abm.calibration_parallel import run_seeds_parallel

    # --- ANES data ---
    csv = Path("data/phase9_empirical/derived/respondent_coordinates.csv")
    print(f"Loading ANES from {csv}")
    df = pd.read_csv(csv)

    anes_by_decade = {}
    for decade, waves in ANES_DECADE_WAVES.items():
        sub = df[df["year"].isin(waves)].copy()
        # Use weights via per-sample replication is overkill — just use raw
        # for the KDE since gaussian_kde supports weights.
        d_sub = sub[sub["party"] == "D"]
        r_sub = sub[sub["party"] == "R"]
        anes_by_decade[decade] = {
            "D": d_sub[["econ", "cult"]].to_numpy(),
            "D_w": d_sub["weight"].to_numpy(),
            "R": r_sub[["econ", "cult"]].to_numpy(),
            "R_w": r_sub["weight"].to_numpy(),
            "ALL": sub[["econ", "cult"]].to_numpy(),
            "ALL_w": sub["weight"].to_numpy(),
        }

    # --- Engine runs ---
    n_seeds = 9
    print(f"Running engine {n_seeds} seeds in parallel ...")
    results = run_seeds_parallel(_worker, list(range(n_seeds)))
    eng_by_decade = {}
    for decade, _ in DECADE_TICKS:
        d_pos, r_pos, all_pos = [], [], []
        for snap in results:
            pos = snap[decade]["pos"]
            party = snap[decade]["party"]
            d_pos.append(pos[party == 0])
            r_pos.append(pos[party == 1])
            all_pos.append(pos[(party == 0) | (party == 1)])
        eng_by_decade[decade] = {
            "D": np.vstack(d_pos),
            "R": np.vstack(r_pos),
            "ALL": np.vstack(all_pos),
        }

    # --- Shared bandwidth: fit on pooled ANES + engine combined so the
    # KDE smoothing is the same for both columns ---
    pooled_all = []
    for decade, _ in DECADE_TICKS:
        pooled_all.append(anes_by_decade[decade]["ALL"])
        pooled_all.append(eng_by_decade[decade]["ALL"])
    pooled_all = np.vstack(pooled_all)
    bw_kde = gaussian_kde(pooled_all.T, bw_method="scott")
    bw = float(bw_kde.factor)
    print(f"  shared Scott bw factor = {bw:.4f}")

    # --- Render side-by-side: 5 rows (decades) × 2 cols (ANES, engine) ---
    n_dec = len(DECADE_TICKS)
    fig, axes = plt.subplots(
        n_dec, 2, figsize=(7.4, 3.5 * n_dec),
        sharex=True, sharey=True,
    )
    axes = np.atleast_2d(axes)

    print("\nPer-decade OVL (ANES | engine):")
    for i, (decade, _) in enumerate(DECADE_TICKS):
        # ANES — fit weighted KDE for densities (gaussian_kde supports weights)
        a_d = anes_by_decade[decade]
        # For KDE smoothing fairness use the SAME bw factor as both sides
        fAll_a = (
            gaussian_kde(a_d["ALL"].T, bw_method=bw, weights=a_d["ALL_w"])
            (_GRID_PTS).reshape(GRID_N, GRID_N) if len(a_d["ALL"]) >= 5 else
            np.full((GRID_N, GRID_N), np.nan)
        )
        fD_a = (
            gaussian_kde(a_d["D"].T, bw_method=bw, weights=a_d["D_w"])
            (_GRID_PTS).reshape(GRID_N, GRID_N) if len(a_d["D"]) >= 5 else
            np.full((GRID_N, GRID_N), np.nan)
        )
        fR_a = (
            gaussian_kde(a_d["R"].T, bw_method=bw, weights=a_d["R_w"])
            (_GRID_PTS).reshape(GRID_N, GRID_N) if len(a_d["R"]) >= 5 else
            np.full((GRID_N, GRID_N), np.nan)
        )
        for F in (fAll_a, fD_a, fR_a):
            integ = F.sum() * _CELL_AREA
            if integ > 0:
                F /= integ

        ovl_a = _draw_panel(
            axes[i, 0],
            a_d["D"], a_d["R"], a_d["ALL"], bw,
            f"ANES {decade}  N={len(a_d['ALL']):,}",
            fAll=fAll_a, fD=fD_a, fR=fR_a,
        )
        axes[i, 0].set_title(
            f"ANES {decade}  N={len(a_d['ALL']):,}  OVL={ovl_a:.2f}",
            fontsize=9,
        )

        e_d = eng_by_decade[decade]
        ovl_e = _draw_panel(
            axes[i, 1],
            e_d["D"], e_d["R"], e_d["ALL"], bw,
            f"engine {decade}",
        )
        axes[i, 1].set_title(
            f"polarlab {decade}  N={len(e_d['ALL']):,}  OVL={ovl_e:.2f}",
            fontsize=9,
        )

        print(f"  {decade}: ANES OVL={ovl_a:.3f}   engine OVL={ovl_e:.3f}")

    for ax in axes[-1, :]:
        ax.set_xlabel("Economic (← lib   cons →)", fontsize=9)
    for i in range(n_dec):
        axes[i, 0].set_ylabel("Cultural (← lib   cons →)", fontsize=9)

    fig.suptitle(
        f"ANES (left) vs polarlab anes_full preset (right) — "
        f"shared bandwidth, {n_seeds} engine seeds pooled",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    out_path = Path("docs/phase9_empirical/sim_vs_anes_side_by_side.png")
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    print(f"\n[dump] {out_path}")


if __name__ == "__main__":
    main()
