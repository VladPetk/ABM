"""
show_pillar_mpl.py - quick-and-dirty static view of the network-primary
pillar (ADR-001). Runs S0-S4 isolated, draws the final agent cloud + the
social tie network for each stage, plus variance and cross-cutting-fraction
curves. Writes one self-contained HTML (a base64 PNG).

Counterpart to the animated plotly show_pillar.py - this one is static,
fast, and dependency-light.

    python scripts/show_pillar_mpl.py
"""
from __future__ import annotations

import base64
import io
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

from abm.metrics.network import cross_cutting_tie_fraction, party_modularity
from abm.metrics.polarization import variance
from abm.pillars import PILLAR, apply_intervention
from abm.pillars.calm_to_camps import build_engine

PARTY = {0: "#1f3565", 1: "#8b2530"}
N, STEPS, EVERY, SEED = 240, 150, 10, 0


def run_stage(idx):
    eng = build_engine(seed=SEED, n_agents=N)
    apply_intervention(eng, PILLAR.interventions[idx])
    ticks, var, xc, mod = [], [], [], []
    for t in range(STEPS + 1):
        if t % EVERY == 0 or t == STEPS:
            net = eng.env.attrs["network"]
            ticks.append(t)
            var.append(variance(eng.positions()))
            xc.append(cross_cutting_tie_fraction(eng.agents, net))
            mod.append(party_modularity(eng.agents, net))
        if t < STEPS:
            eng.step()
    return eng, ticks, var, xc, mod


def main():
    labels = [iv.label for iv in PILLAR.interventions]
    runs = [run_stage(i) for i in range(len(labels))]

    print(f"\nnetwork-primary pillar  (seed {SEED}, {N} agents, {STEPS} ticks)\n")
    for i, (eng, tk, var, xc, mod) in enumerate(runs):
        print(f"  S{i} {labels[i]:<22} variance {var[0]:.3f} -> {var[-1]:.3f}"
              f"   x-cut {xc[0]:.3f} -> {xc[-1]:.3f}"
              f"   modularity {mod[0]:.3f} -> {mod[-1]:.3f}")
    print()

    fig = plt.figure(figsize=(20, 9))
    gs = fig.add_gridspec(2, 10, height_ratios=[1.35, 1.0], hspace=0.30, wspace=0.55)

    for i, (eng, tk, var, xc, mod) in enumerate(runs):
        ax = fig.add_subplot(gs[0, 2 * i:2 * i + 2])
        pos = eng.positions()
        parties = eng.attr_array("party", default=0).astype(int)
        adj = eng.env.attrs["network"].adjacency
        same, cross = [], []
        for a, nbrs in adj.items():
            for b in nbrs:
                if b > a:
                    seg = [pos[a], pos[b]]
                    (same if parties[a] == parties[b] else cross).append(seg)
        ax.add_collection(LineCollection(same, colors="#c2c5c9",
                                         linewidths=0.3, alpha=0.55, zorder=1))
        ax.add_collection(LineCollection(cross, colors="#d69e2e",
                                         linewidths=0.6, alpha=0.85, zorder=2))
        ax.scatter(pos[:, 0], pos[:, 1], s=10, zorder=3, edgecolors="none",
                   c=[PARTY[int(p)] for p in parties])
        ax.set_xlim(-1.08, 1.08)
        ax.set_ylim(-1.08, 1.08)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.axhline(0, color="#dddddd", lw=0.6, zorder=0)
        ax.axvline(0, color="#dddddd", lw=0.6, zorder=0)
        ax.set_title(f"S{i}  {labels[i]}\nvariance {var[-1]:.3f}    "
                     f"cross-cut {xc[-1]:.3f}", fontsize=10)

    axv = fig.add_subplot(gs[1, 0:5])
    axx = fig.add_subplot(gs[1, 5:10])
    for i, (eng, tk, var, xc, mod) in enumerate(runs):
        axv.plot(tk, var, lw=2.2, label=f"S{i} {labels[i]}")
        axx.plot(tk, xc, lw=2.2, label=f"S{i} {labels[i]}")
    axv.set_title("Polarization — ideology variance over time", fontsize=11)
    axv.set_xlabel("tick")
    axv.set_ylabel("variance")
    axv.legend(fontsize=8, loc="upper right")
    axx.set_title("Network sorting — cross-cutting tie fraction over time",
                  fontsize=11)
    axx.set_xlabel("tick")
    axx.set_ylabel("cross-cutting fraction")
    axx.legend(fontsize=8, loc="upper right")
    for ax in (axv, axx):
        ax.grid(True, alpha=0.25)

    fig.suptitle("Network-primary pillar (ADR-001) — S0-S4 isolated   "
                 "[grey edges: same-party ties · gold edges: cross-cutting ties]",
                 fontsize=13, y=0.99)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=108, bbox_inches="tight")
    plt.close(fig)
    b64 = base64.b64encode(buf.getvalue()).decode()

    out = Path("pillar_network_primary.html").resolve()
    out.write_text(
        "<html><head><meta charset='utf-8'><title>Network-primary pillar</title>"
        "</head><body style='font-family:sans-serif;max-width:1500px;margin:24px auto'>"
        "<h2>Network-primary pillar — visual check (ADR-001)</h2>"
        "<p>Influence now flows along social-network ties, not geometric "
        "proximity. Each panel is one stage run in isolation; edges are the "
        "tie network (grey = same-party, gold = cross-cutting).</p>"
        f"<img style='width:100%' src='data:image/png;base64,{b64}'>"
        "</body></html>",
        encoding="utf-8",
    )
    print(f"  written: {out}\n")


if __name__ == "__main__":
    main()
