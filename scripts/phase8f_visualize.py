"""Generate a PDF of 2D ideology-space snapshots of the historical arc.

Runs the Phase 8f historical scenario for one seed and captures
agent positions every 5 years (every 15 ticks). Plots each snapshot
as a 2D scatter in (economic, cultural) ideology, colored by party
with greys for Independents. Saves all into a single PDF.

Usage:
    PYTHONPATH=. python scripts/phase8f_visualize.py [out_pdf_path]
"""
from __future__ import annotations

import os
import sys
import pickle
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

from abm.metrics.affective import affective_polarization, ideological_constraint
from abm.metrics.polarization import variance as variance_metric
from abm.pillars import historical_arc as ha
from abm.pillars.schedule import run_to


SEED = 0
N = 250
INDEPENDENT_FRACTION = 0.12
TICKS_PER_YEAR = 3
YEARS = [1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025]
PARTY_COLORS = {0: "#1f3565", 1: "#8b2530", 2: "#888888"}


def year_to_tick(year):
    return (year - 1980) * TICKS_PER_YEAR


def safe_float(v, key=None):
    if isinstance(v, dict):
        if key is not None and key in v:
            return float(v[key])
        return float(np.mean(list(v.values())))
    return float(v)


def snapshot(engine, year):
    n = len(engine.agents)
    positions = np.zeros((n, 2))
    parties = np.zeros(n, dtype=int)
    strength = np.zeros(n)
    for i, agent in enumerate(engine.agents):
        positions[i] = agent.state.ideology
        parties[i] = int(agent.state.attrs.get("party", 2))
        strength[i] = float(agent.state.attrs.get("identity_strength", 0.5))
    var = safe_float(variance_metric(positions))
    cons_raw = ideological_constraint(engine.agents)
    cons = safe_float(cons_raw)
    aff = safe_float(affective_polarization(engine.agents))
    return {
        "year": year,
        "positions": positions,
        "parties": parties,
        "strength": strength,
        "metrics": {"variance": var, "constraint": cons, "affect": aff},
    }


def plot_snapshot(snap, ax):
    pos = snap["positions"]
    parties = snap["parties"]
    strength = snap["strength"]
    sizes_base = {0: 30, 1: 30, 2: 22}

    for p in [2, 0, 1]:
        mask = parties == p
        if not mask.any():
            continue
        alphas = 0.40 + 0.50 * strength[mask] if p in (0, 1) else np.full(mask.sum(), 0.45)
        base = np.array(matplotlib.colors.to_rgb(PARTY_COLORS[p]))
        rgba = np.zeros((mask.sum(), 4))
        rgba[:, :3] = base
        rgba[:, 3] = alphas
        ax.scatter(pos[mask, 0], pos[mask, 1], c=rgba, s=sizes_base[p], edgecolors="none")

    for p in [0, 1]:
        mask = parties == p
        if mask.any():
            cx, cy = pos[mask, 0].mean(), pos[mask, 1].mean()
            ax.scatter([cx], [cy], c=PARTY_COLORS[p], s=380, marker="X",
                       edgecolors="white", linewidths=1.8, zorder=10)

    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.axhline(0, color="#cccccc", linewidth=0.7, zorder=0)
    ax.axvline(0, color="#cccccc", linewidth=0.7, zorder=0)
    ax.set_xlabel("Economic axis (left to right)")
    ax.set_ylabel("Cultural axis (progressive to traditional)")

    n_total = len(parties)
    n_ind = int((parties == 2).sum())
    n_dem = int((parties == 0).sum())
    n_rep = int((parties == 1).sum())
    m = snap["metrics"]
    title = "%d  N=%d (D=%d, R=%d, Ind=%d)\nvar=%.2f  constraint=%.2f  affect=%+.2f" % (
        snap["year"], n_total, n_dem, n_rep, n_ind,
        m["variance"], m["constraint"], m["affect"],
    )
    ax.set_title(title, fontsize=10)
    ax.set_aspect("equal")
    ax.grid(True, color="#eeeeee", linewidth=0.5, zorder=-1)


def run_capture():
    print("Building engine seed=%d N=%d ind=%.2f" % (SEED, N, INDEPENDENT_FRACTION), flush=True)
    engine = ha.build_engine(seed=SEED, n_agents=N, independent_fraction=INDEPENDENT_FRACTION)
    schedule = ha.build_schedule()
    snaps = [snapshot(engine, 1980)]
    for year in YEARS[1:]:
        target = year_to_tick(year)
        run_to(engine, schedule, target)
        print("  reached %d (tick %d)" % (year, target), flush=True)
        snaps.append(snapshot(engine, year))
    return snaps


def render_pdf(snaps, pdf_path):
    with PdfPages(str(pdf_path)) as pdf:
        # Cover
        fig = plt.figure(figsize=(8.5, 11))
        fig.suptitle("polarlab Historical Arc Visualization\nPhase 8f engine, 1980 to 2025 every 5 years",
                     fontsize=14, y=0.96)
        ax = fig.add_subplot(111)
        ax.axis("off")
        intro = (
            "This PDF shows snapshots of the 2D ideology grid at five-year intervals\n"
            "from 1980 to 2025, under the Phase 8f historical arc on a single seed.\n\n"
            "Each dot is an agent. Position = (economic axis, cultural axis), both in [-1, 1].\n"
            "Color: blue Democrats, red Republicans, grey Independents (12% of population).\n"
            "Saturation: brighter dots have stronger party identity.\n"
            "Large X markers: party centroids.\n\n"
            "Title metrics per snapshot:\n"
            "  variance = population spread\n"
            "  constraint = cross-axis party sorting (mean of (cx, cy))\n"
            "  affect = mean out-party warmth (more negative = more polarized)\n\n"
            "Single seed (seed=0). Multi-seed ensemble numbers are in phase8f_results.md."
        )
        ax.text(0.5, 0.55, intro, ha="center", va="top", fontsize=11,
                transform=ax.transAxes, family="monospace")
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)
        print("cover saved", flush=True)

        for i in range(0, len(snaps), 2):
            fig, axes = plt.subplots(1, 2, figsize=(11, 5.6))
            plot_snapshot(snaps[i], axes[0])
            if i + 1 < len(snaps):
                plot_snapshot(snaps[i + 1], axes[1])
            else:
                axes[1].axis("off")
            fig.tight_layout()
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)
            print("page %d saved" % (i // 2 + 1), flush=True)


def main():
    pdf_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("phase8f_visualization.pdf")
    snaps_pkl = Path(str(pdf_path).replace(".pdf", "_snaps.pkl"))
    mode = sys.argv[2] if len(sys.argv) > 2 else "all"

    if mode == "render" and snaps_pkl.exists():
        with open(snaps_pkl, "rb") as f:
            snaps = pickle.load(f)
        print("loaded %d snaps" % len(snaps), flush=True)
    else:
        snaps = run_capture()
        with open(snaps_pkl, "wb") as f:
            pickle.dump(snaps, f)
        print("saved %s" % snaps_pkl, flush=True)
        if mode == "capture":
            return

    render_pdf(snaps, pdf_path)
    print("PDF saved: %s" % pdf_path, flush=True)


if __name__ == "__main__":
    main()
