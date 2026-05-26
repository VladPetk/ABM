"""
show_all_mpl.py — quick static view of the entire engine (post Phase 7):
the calm_to_camps pillar (S0-S4) journey + the six Phase 6 release-phase
interventions (X1-X6) branched from the same S4 polarized state. Writes
one self-contained HTML with a base64 PNG.

    python scripts/show_all_mpl.py
"""
from __future__ import annotations

import base64
import copy
import io
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Patch

from abm.metrics.affective import affective_polarization
from abm.metrics.network import cross_cutting_tie_fraction, party_modularity
from abm.metrics.polarization import variance
from abm.pillars import PILLAR, INTERVENTIONS_PHASE6, apply_intervention
from abm.pillars.calm_to_camps import build_engine

PARTY = {0: "#1f3565", 1: "#8b2530"}
BUCKET_COLORS = {
    "backfire": "#c0392b",
    "null": "#7f8c8d",
    "partial": "#e67e22",
    "real": "#27ae60",
}
N, TICKS_PER_STAGE, RELEASE_TICKS, SEED = 180, 60, 100, 0


def party_separation(eng):
    pos = eng.positions()
    parties = eng.attr_array("party", default=0).astype(int)
    if (parties == 0).sum() and (parties == 1).sum():
        return float(np.linalg.norm(
            pos[parties == 0].mean(0) - pos[parties == 1].mean(0)
        ))
    return 0.0


def metrics(eng):
    pos = eng.positions()
    net = eng.env.attrs["network"]
    try:
        aff = float(affective_polarization(eng.agents))
    except Exception:
        aff = float("nan")
    return dict(
        variance=variance(pos),
        sep=party_separation(eng),
        affect=aff,
        xcut=cross_cutting_tie_fraction(eng.agents, net),
        modularity=party_modularity(eng.agents, net),
    )


def run_journey():
    eng = build_engine(seed=SEED, n_agents=N)
    snapshots = []
    for s in PILLAR.interventions:
        apply_intervention(eng, s)
        eng.run(TICKS_PER_STAGE)
        snapshots.append((s, copy.deepcopy(eng), metrics(eng)))
    return snapshots


def run_interventions(s4_engine):
    out = []
    for x in INTERVENTIONS_PHASE6:
        e = copy.deepcopy(s4_engine)
        apply_intervention(e, x)
        e.run(RELEASE_TICKS)
        out.append((x, e, metrics(e)))
    return out


def draw_cloud(ax, eng, title, subtitle, border_color=None):
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
                                     linewidths=0.25, alpha=0.50, zorder=1))
    ax.add_collection(LineCollection(cross, colors="#d69e2e",
                                     linewidths=0.55, alpha=0.85, zorder=2))
    ax.scatter(pos[:, 0], pos[:, 1], s=8, zorder=3, edgecolors="none",
               c=[PARTY[int(p)] for p in parties])
    ax.set_xlim(-1.08, 1.08); ax.set_ylim(-1.08, 1.08)
    ax.set_xticks([]); ax.set_yticks([])
    ax.axhline(0, color="#dddddd", lw=0.6, zorder=0)
    ax.axvline(0, color="#dddddd", lw=0.6, zorder=0)
    ax.set_title(title, fontsize=10, fontweight="bold")
    if subtitle:
        ax.text(0.5, -0.06, subtitle, fontsize=8.5, transform=ax.transAxes,
                ha="center", va="top", color="#333")
    if border_color:
        for spine in ax.spines.values():
            spine.set_edgecolor(border_color); spine.set_linewidth(2.4)


def main():
    print(f"Running pillar journey  (N={N}, {TICKS_PER_STAGE} ticks/stage, seed={SEED})...")
    stages = run_journey()
    s4_engine, s4_m = stages[-1][1], stages[-1][2]
    print(f"Running 6 interventions branching from S4  ({RELEASE_TICKS} release ticks)...")
    interventions = run_interventions(s4_engine)

    print("\nPillar journey:")
    print(f"  {'stage':<28} {'var':>6}  {'sep':>6}  {'affect':>8}  {'x-cut':>6}  {'Q':>5}")
    for s, _, m in stages:
        print(f"  {s.label:<28} {m['variance']:6.3f}  {m['sep']:6.2f}  "
              f"{m['affect']:+8.2f}  {m['xcut']:6.3f}  {m['modularity']:5.2f}")
    print("\nInterventions (Δ from end-of-S4 state):")
    print(f"  {'lever':<38} {'Δsep':>7} {'Δaff':>7}  {'issue':<9} {'affect':<9}")
    for x, _, m in interventions:
        b = x.effect_buckets or {}
        print(f"  {x.label:<38} {m['sep']-s4_m['sep']:+7.3f} "
              f"{m['affect']-s4_m['affect']:+7.3f}  "
              f"{b.get('issue_sorting','?'):<9} {b.get('affect','?'):<9}")
    print()

    fig = plt.figure(figsize=(22, 14.5))
    gs = fig.add_gridspec(3, 6, height_ratios=[1.0, 1.0, 0.65],
                          hspace=0.42, wspace=0.18)

    for i, (s, eng, m) in enumerate(stages):
        ax = fig.add_subplot(gs[0, i])
        subtitle = (f"var {m['variance']:.2f}  sep {m['sep']:.2f}  "
                    f"aff {m['affect']:+.2f}\nx-cut {m['xcut']:.3f}  "
                    f"Q {m['modularity']:.2f}")
        draw_cloud(ax, eng, f"S{i}  {s.label}", subtitle)

    leg = fig.add_subplot(gs[0, 5])
    leg.axis("off")
    leg.text(0.0, 0.95, "Legend", fontsize=11, fontweight="bold",
             transform=leg.transAxes)
    leg.legend(handles=[
        Patch(facecolor=PARTY[0], label="Party 0 (Left)"),
        Patch(facecolor=PARTY[1], label="Party 1 (Right)"),
        Patch(facecolor="#c2c5c9", label="Same-party tie"),
        Patch(facecolor="#d69e2e", label="Cross-cutting tie"),
    ], loc="upper left", bbox_to_anchor=(0.0, 0.90),
        fontsize=9, frameon=False)
    leg.text(0.0, 0.46, "Intervention buckets:", fontsize=10, fontweight="bold",
             transform=leg.transAxes)
    leg.legend(handles=[Patch(facecolor=c, label=l) for l, c in BUCKET_COLORS.items()],
               loc="upper left", bbox_to_anchor=(0.0, 0.42),
               fontsize=9, frameon=False)

    for i, (x, eng, m) in enumerate(interventions):
        ax = fig.add_subplot(gs[1, i])
        dsep = m['sep'] - s4_m['sep']
        daff = m['affect'] - s4_m['affect']
        b = x.effect_buckets or {}
        subtitle = (f"Δsep {dsep:+.2f}  Δaff {daff:+.2f}\n"
                    f"issue: {b.get('issue_sorting','?')}   "
                    f"affect: {b.get('affect','?')}")
        bc = BUCKET_COLORS.get(b.get('issue_sorting'), "#777")
        short = x.id.replace("_", " ").upper().split(" ", 1)
        title = f"{short[0]}  {x.label[:30]}"
        draw_cloud(ax, eng, title, subtitle, border_color=bc)

    labels = [x.label for x, _, _ in interventions]
    dseps = [m['sep'] - s4_m['sep'] for _, _, m in interventions]
    daffs = [m['affect'] - s4_m['affect'] for _, _, m in interventions]
    issue_colors = [BUCKET_COLORS.get((x.effect_buckets or {}).get('issue_sorting'), "#777")
                    for x, _, _ in interventions]
    affect_colors = [BUCKET_COLORS.get((x.effect_buckets or {}).get('affect'), "#777")
                     for x, _, _ in interventions]

    ax_a = fig.add_subplot(gs[2, 0:3])
    y = np.arange(len(labels))
    ax_a.barh(y, dseps, color=issue_colors, edgecolor="white")
    ax_a.set_yticks(y); ax_a.set_yticklabels(labels, fontsize=9)
    ax_a.invert_yaxis()
    ax_a.axvline(0, color="#444", lw=0.8)
    ax_a.set_xlabel("Δ party separation  (+ = camps further apart, i.e. worse)", fontsize=9)
    ax_a.set_title("Δ issue sorting (Δsep)  — bar color = issue_sorting bucket",
                   fontsize=10, fontweight="bold")
    ax_a.grid(True, alpha=0.25, axis="x")

    ax_b = fig.add_subplot(gs[2, 3:6])
    ax_b.barh(y, daffs, color=affect_colors, edgecolor="white")
    ax_b.set_yticks(y); ax_b.set_yticklabels(labels, fontsize=9)
    ax_b.invert_yaxis()
    ax_b.axvline(0, color="#444", lw=0.8)
    ax_b.set_xlabel("Δ affective polarization  (more-negative = colder, i.e. worse)", fontsize=9)
    ax_b.set_title("Δ affect (Δaff)  — bar color = affect bucket",
                   fontsize=10, fontweight="bold")
    ax_b.grid(True, alpha=0.25, axis="x")

    fig.suptitle(
        "polarlab — calm-to-camps pillar (S0→S4) + 6 release-phase interventions (X1–X6)   "
        "[intervention panel border = issue-sorting bucket]",
        fontsize=14, y=0.997, fontweight="bold",
    )

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    b64 = base64.b64encode(buf.getvalue()).decode()

    out = Path("pillar_and_interventions.html").resolve()
    out.write_text(
        "<html><head><meta charset='utf-8'>"
        "<title>polarlab — pillar + interventions</title></head>"
        "<body style='font-family:sans-serif;max-width:1700px;margin:24px auto'>"
        "<h2>polarlab — calm-to-camps pillar + Phase 6 intervention library</h2>"
        "<p>Top row: the 5-stage pillar journey (S0 baseline → S1 bounded "
        "confidence → S2 party identity → S3 partisan media → S4 homophilous "
        "network). Middle row: the 6 release-phase interventions, each "
        "branched from the same end-of-S4 state — panel border colored by "
        "issue-sorting bucket (red=backfire, grey=null, orange=partial, "
        "green=real). Bottom: Δ-from-S4 for each intervention on the two "
        "measurement axes.</p>"
        f"<img style='width:100%' src='data:image/png;base64,{b64}'>"
        "</body></html>",
        encoding="utf-8",
    )
    print(f"  written: {out}\n")


if __name__ == "__main__":
    main()
