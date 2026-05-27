"""Generate a PDF of 2D ideology-space snapshots for a Phase 9 variant.

Like phase8f_visualize.py but loads variants from
scripts.phase9_cluster_diversity.VARIANTS and labels factions.

Usage:
    PYTHONPATH=. python scripts/phase9_visualize.py <variant_name> [out_pdf_path]
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

# Re-import phase9 module — VARIANTS lives there
sys.path.insert(0, str(Path(__file__).parent))
import phase9_cluster_diversity as p9

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
    faction_names = []
    for i, agent in enumerate(engine.agents):
        positions[i] = agent.state.ideology
        parties[i] = int(agent.state.attrs.get("party", 2))
        strength[i] = float(agent.state.attrs.get("identity_strength", 0.5))
        faction_names.append(agent.state.attrs.get("faction_name"))
    var = safe_float(variance_metric(positions))
    cons_raw = ideological_constraint(engine.agents)
    cons = safe_float(cons_raw)
    aff = safe_float(affective_polarization(engine.agents))
    # Compute cluster-diversity metrics
    kstar, sil = p9.effective_k(positions)
    pr = p9.participation_ratio(positions)
    bim_y = p9.bimodality(positions[:, 1])
    return {
        "year": year,
        "positions": positions,
        "parties": parties,
        "strength": strength,
        "faction_names": faction_names,
        "metrics": {"variance": var, "constraint": cons, "affect": aff,
                    "k_star": kstar, "pr": pr, "bim_y": bim_y, "sil": sil},
    }


def plot_snapshot(snap, ax):
    pos = snap["positions"]
    parties = snap["parties"]
    strength = snap["strength"]
    sizes_base = {0: 28, 1: 28, 2: 20}

    for p in [2, 0, 1]:
        mask = parties == p
        if not mask.any():
            continue
        alphas = 0.40 + 0.45 * strength[mask] if p in (0, 1) else np.full(mask.sum(), 0.45)
        base = np.array(matplotlib.colors.to_rgb(PARTY_COLORS[p]))
        rgba = np.zeros((mask.sum(), 4))
        rgba[:, :3] = base
        rgba[:, 3] = alphas
        ax.scatter(pos[mask, 0], pos[mask, 1], c=rgba, s=sizes_base[p], edgecolors="none")

    for p in [0, 1]:
        mask = parties == p
        if mask.any():
            cx, cy = pos[mask, 0].mean(), pos[mask, 1].mean()
            ax.scatter([cx], [cy], c=PARTY_COLORS[p], s=300, marker="X",
                       edgecolors="white", linewidths=1.6, zorder=10)

    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.axhline(0, color="#cccccc", linewidth=0.7, zorder=0)
    ax.axvline(0, color="#cccccc", linewidth=0.7, zorder=0)
    ax.set_xlabel("Economic (left to right)", fontsize=8)
    ax.set_ylabel("Cultural (progressive to traditional)", fontsize=8)

    n_total = len(parties)
    m = snap["metrics"]
    title = "%d  k*=%.1f  PR=%.2f  bimY=%.2f\nvar=%.2f  cons=%.2f  aff=%+.2f" % (
        snap["year"], m["k_star"], m["pr"], m["bim_y"],
        m["variance"], m["constraint"], m["affect"],
    )
    ax.set_title(title, fontsize=8)
    ax.set_aspect("equal")
    ax.grid(True, color="#eeeeee", linewidth=0.5, zorder=-1)


def run_capture(variant_name):
    print(f"Building engine seed={SEED} N={N} ind={INDEPENDENT_FRACTION} variant={variant_name}", flush=True)
    engine = ha.build_engine(seed=SEED, n_agents=N, independent_fraction=INDEPENDENT_FRACTION)
    p9.VARIANTS[variant_name](engine, seed=SEED)
    schedule = ha.build_schedule()
    snaps = [snapshot(engine, 1980)]
    for year in YEARS[1:]:
        target = year_to_tick(year)
        run_to(engine, schedule, target)
        print(f"  reached {year} (tick {target})", flush=True)
        snaps.append(snapshot(engine, year))
    return snaps


def render_pdf(snaps, pdf_path, variant_name):
    with PdfPages(str(pdf_path)) as pdf:
        # Cover
        fig = plt.figure(figsize=(8.5, 11))
        fig.suptitle(f"Phase 9 Cluster Diversity Visualization\nVariant: {variant_name}\n1980 to 2025, every 5 years",
                     fontsize=13, y=0.96)
        ax = fig.add_subplot(111)
        ax.axis("off")
        intro = (
            f"Variant: {variant_name}\n"
            f"Single seed (seed={SEED}), N={N}, Independents={INDEPENDENT_FRACTION:.0%}\n\n"
            "Each dot = one agent. Position = (economic axis, cultural axis), both in [-1, 1].\n"
            "Blue = Democrat, Red = Republican, Grey = Independent.\n"
            "Saturation = identity strength.  X marker = party centroid.\n\n"
            "Key diagnostic metrics in each subplot title:\n"
            "  k*  = effective number of clusters (silhouette-best k); larger = more cluster diversity\n"
            "  PR  = participation ratio (covariance dimensionality)\n"
            "  bimY = bimodality on cultural axis (0..1; >0.55 = bimodal)\n"
            "  var, cons, aff = standard polsim metrics\n\n"
            "Compare to the baseline historical-arc PDF (phase8f_visualization.pdf):\n"
            "  Baseline k* falls from 5.6 (1980) -> 2.0 (2000+) — visible cluster diversity collapses.\n"
            "  Phase 9 best variant aims to keep k* >= 3 across the arc.\n\n"
            "Faction set seeded at 1980 (from US_FACTIONS in scripts/phase9_cluster_diversity.py):\n"
            "  DSA_socialists (-0.65, -0.50)        progressive_liberals (-0.40, -0.55)\n"
            "  mainstream_dems (-0.30, -0.10)       blue_dog_dems (-0.15, +0.25)\n"
            "  evangelical_dems (-0.20, +0.40)      libertarian_reps (+0.55, -0.30)\n"
            "  classical_liberals (+0.25, -0.10)    mainstream_reps (+0.30, +0.15)\n"
            "  MAGA_populists (+0.45, +0.50)        sovereign_hard_right (+0.70, +0.65)\n"
            "  crunchy_centrists (-0.05, +0.10) — cross-pressured\n"
        )
        ax.text(0.5, 0.55, intro, ha="center", va="top", fontsize=9,
                transform=ax.transAxes, family="monospace")
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

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


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/phase9_visualize.py <variant_name> [out_pdf_path]")
        sys.exit(1)
    variant = sys.argv[1]
    pdf_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(f"phase9_visualize_{variant}.pdf")
    snaps = run_capture(variant)
    render_pdf(snaps, pdf_path, variant)
    print(f"PDF saved: {pdf_path}", flush=True)


if __name__ == "__main__":
    main()
