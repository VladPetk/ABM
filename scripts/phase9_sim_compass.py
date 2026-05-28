"""Phase 9 — Render the engine's 2D ideological compass at each decade
endpoint, in the same style as the ANES small-multiples plot
(docs/phase9_empirical/density_small_multiples.png).

Runs the anes_full preset across N seeds in parallel, pools agent
positions per decade, fits per-party KDEs on a fixed [-1, 1]² grid
with a shared Scott bandwidth, and renders one subplot per decade
with party contour overlays + centroids + 2D OVL annotation.

Output: docs/phase9_empirical/sim_density_small_multiples.png
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

import math

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gaussian_kde

# --- decade snapshot ticks (1980 = tick 0; 3 ticks/year) ---
DECADE_TICKS = [
    (1980, 0),
    (1990, 30),
    (2000, 60),
    (2010, 90),
    (2020, 120),
    (2025, 135),
]

# --- KDE grid (match the ANES build: 81×81 on [-1.05, 1.05]²) ---
GRID_LO, GRID_HI, GRID_N = -1.05, 1.05, 81
GRID_AXIS = np.linspace(GRID_LO, GRID_HI, GRID_N)
_xx, _yy = np.meshgrid(GRID_AXIS, GRID_AXIS, indexing="ij")
_GRID_PTS = np.vstack([_xx.ravel(), _yy.ravel()])  # (2, N²)
_CELL_AREA = (GRID_AXIS[1] - GRID_AXIS[0]) ** 2

PARTY_COLORS = {"D": "tab:blue", "R": "tab:red"}


def _build_kwargs():
    return dict(
        n_agents=250,
        independent_fraction=0.12,
        factional_seeding=False,
        faction_anchor_strength=0.04,
        faction_anchor_events=True,
        event_stubbornness_bump_multiplier=1.0,
        tier_d_axis_balance=True,
        tier_d_lever1_off=True,
        tier_d_cohort_y_signs_fix=True,
        tier_d_anes_knobs=True,
        tier_d_anes_drift_multiplier=3.0,
        tier_d_anes_sigma_pc_multiplier=1.6,
        tier_c_identity_pull_x=0.015,
        tier_c_identity_pull_y=0.040,
        tier_d_aniso_noise_sigma_x=0.08,
        tier_d_aniso_noise_sigma_y=0.08,
        tier_c_party_pull_strength=0.04,
        tier_c_bc_strength=0.015,
    )


def _worker(seed: int) -> dict:
    """Run one seed of the engine; return per-decade {pos: (N,2), party: (N,)}."""
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to

    eng = build_engine(seed=seed, **_build_kwargs())
    sched = build_schedule(factional_seeding=False, faction_anchor_events=True)

    snapshots: dict[int, dict] = {}
    snapshots[1980] = {
        "pos": np.array([a.state.ideology for a in eng.agents], dtype=float),
        "party": np.array(
            [a.state.attrs.get("party", -1) for a in eng.agents], dtype=int
        ),
    }
    for year, tick in DECADE_TICKS[1:]:
        run_to(eng, sched, tick)
        snapshots[year] = {
            "pos": np.array([a.state.ideology for a in eng.agents], dtype=float),
            "party": np.array(
                [a.state.attrs.get("party", -1) for a in eng.agents], dtype=int
            ),
        }
    return snapshots


def _kde_on_grid(xy: np.ndarray, bw: float | str) -> np.ndarray:
    """Fit gaussian_kde and evaluate on the standard grid.

    xy: (N, 2) array of positions.
    Returns: (GRID_N, GRID_N) density array normalized to integrate to 1.
    """
    if len(xy) < 5:
        return np.full((GRID_N, GRID_N), np.nan)
    kde = gaussian_kde(xy.T, bw_method=bw)
    z = kde(_GRID_PTS).reshape(GRID_N, GRID_N)
    integral = z.sum() * _CELL_AREA
    if integral > 0:
        z = z / integral
    return z


def _ovl_2d(fA: np.ndarray, fB: np.ndarray) -> float:
    """2D overlapping coefficient = ∫∫ min(fA, fB) on the shared grid."""
    if np.isnan(fA).any() or np.isnan(fB).any():
        return float("nan")
    return float(np.minimum(fA, fB).sum() * _CELL_AREA)


def main():
    from abm.calibration_parallel import run_seeds_parallel

    n_seeds = 9
    seeds = list(range(n_seeds))
    print(f"Running {n_seeds} seeds in parallel ...")
    results = run_seeds_parallel(_worker, seeds)

    # Pool positions per decade per party across seeds (party=0 → D, 1 → R).
    pooled: dict[int, dict[str, np.ndarray]] = {}
    for year, _ in DECADE_TICKS:
        d_xy, r_xy, all_xy = [], [], []
        for snap in results:
            pos = snap[year]["pos"]
            party = snap[year]["party"]
            d_xy.append(pos[party == 0])
            r_xy.append(pos[party == 1])
            all_xy.append(pos[(party == 0) | (party == 1)])
        pooled[year] = {
            "D": np.vstack(d_xy) if d_xy else np.zeros((0, 2)),
            "R": np.vstack(r_xy) if r_xy else np.zeros((0, 2)),
            "ALL": np.vstack(all_xy) if all_xy else np.zeros((0, 2)),
        }
        print(f"  {year}: nD={len(pooled[year]['D'])} nR={len(pooled[year]['R'])}")

    # Shared global bandwidth — fit on ALL pooled agents across all
    # decades + parties so every wave/party uses the same Scott BW
    # (matches the ANES build's frozen-bandwidth approach).
    all_points = np.vstack([pooled[y]["ALL"] for y, _ in DECADE_TICKS])
    bw_kde = gaussian_kde(all_points.T, bw_method="scott")
    global_bw = float(bw_kde.factor)
    print(f"  global Scott bw factor = {global_bw:.4f}")

    # Build densities + per-decade OVL
    densities = {}
    ovls = {}
    centroids = {}
    for year, _ in DECADE_TICKS:
        for label in ("D", "R", "ALL"):
            densities[(year, label)] = _kde_on_grid(pooled[year][label], global_bw)
        ovls[year] = _ovl_2d(
            densities[(year, "D")], densities[(year, "R")]
        )
        centroids[(year, "D")] = (
            pooled[year]["D"].mean(axis=0)
            if len(pooled[year]["D"]) else (np.nan, np.nan)
        )
        centroids[(year, "R")] = (
            pooled[year]["R"].mean(axis=0)
            if len(pooled[year]["R"]) else (np.nan, np.nan)
        )

    # --- Render small multiples (same style as ANES plot) ---
    years = [y for y, _ in DECADE_TICKS]
    ncols = 3
    nrows = int(math.ceil(len(years) / ncols))
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(3.6 * ncols, 3.6 * nrows),
        sharex=True, sharey=True,
    )
    axes = np.atleast_2d(axes)

    for i, year in enumerate(years):
        ax = axes[i // ncols, i % ncols]
        # Background: pooled-wave density
        fAll = densities[(year, "ALL")]
        if not np.isnan(fAll).any():
            ax.contourf(
                GRID_AXIS, GRID_AXIS, fAll.T,
                levels=8, cmap="Greys", alpha=0.35,
            )
        # Party contour lines
        for label in ("D", "R"):
            f = densities[(year, label)]
            if np.isnan(f).any():
                continue
            ax.contour(
                GRID_AXIS, GRID_AXIS, f.T, levels=4,
                colors=PARTY_COLORS[label], linewidths=0.9, alpha=0.85,
            )
        # Centroids
        for label in ("D", "R"):
            c = centroids[(year, label)]
            if not np.any(np.isnan(c)):
                ax.scatter(
                    [c[0]], [c[1]], c=PARTY_COLORS[label], s=40,
                    edgecolor="black", linewidth=0.6, zorder=5,
                )
        n_total = len(pooled[year]["ALL"])
        ovl = ovls[year]
        ax.set_title(
            f"{year}  N={n_total:,}  OVL={ovl:.2f}",
            fontsize=9,
        )
        ax.axhline(0, color="black", lw=0.4, alpha=0.3)
        ax.axvline(0, color="black", lw=0.4, alpha=0.3)
        ax.set_xlim(-1.05, 1.05)
        ax.set_ylim(-1.05, 1.05)

    # Hide unused panels
    for j in range(len(years), nrows * ncols):
        axes[j // ncols, j % ncols].axis("off")

    for ax in axes[-1, :]:
        ax.set_xlabel("Economic (← lib   cons →)", fontsize=9)
    for ax in axes[:, 0]:
        ax.set_ylabel("Cultural (← lib   cons →)", fontsize=9)

    fig.suptitle(
        f"polarlab simulated 2D ideological compass 1980-2025  "
        f"(anes_full preset, {n_seeds} seeds pooled, global bandwidth)",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    out_path = Path("docs/phase9_empirical/sim_density_small_multiples.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    print(f"\n[dump] {out_path}")
    print("\nPer-decade OVL:")
    for year in years:
        print(f"  {year}: OVL={ovls[year]:.3f}")


if __name__ == "__main__":
    main()
