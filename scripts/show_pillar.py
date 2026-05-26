"""
show_pillar.py - watch the calm_to_camps pillar (S0-S4) in action.

Two ways to inspect the pillar, one per --mode:

  stages   (default)  Each stage built fresh and run in isolation, side
                      by side. Auto-adapts to however many stages exist.

  journey             One continuous society: run a stage, switch on the
                      next, keep running. The live, path-dependent story.

Each view writes one interactive HTML with three stacked figures:

  * animated agent clouds with the social tie network drawn on top -
    faint grey edges join same-party agents, gold edges are
    cross-cutting (cross-party) ties;
  * polarization (ideology variance) over time;
  * network sorting - cross-cutting tie fraction and party modularity.
    Flat through S0-S3 (the tie network is inert there), moving in S4.

    python scripts/show_pillar.py
    python scripts/show_pillar.py --mode journey
    python scripts/show_pillar.py --seed 3 --steps 200 --agents 250

Engine-only viewer: does not touch the website or the Solara dashboard.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from abm.metrics.network import cross_cutting_tie_fraction, party_modularity
from abm.metrics.polarization import variance
from abm.pillars import PILLAR, apply_intervention
from abm.pillars.calm_to_camps import build_engine

PARTY_COLORS = {0: "#1f3565", 1: "#8b2530"}
STAGE_LINE = ["#74797f", "#1f3565", "#8b2530", "#553f6b", "#2a4a52"]
SAME_EDGE = "rgba(120,125,130,0.22)"
CROSS_EDGE = "rgba(214,158,46,0.85)"


@dataclass
class Run:
    """Everything one engine run records, snapshot by snapshot."""
    parties: np.ndarray
    ticks: list = field(default_factory=list)
    pos: list = field(default_factory=list)     # N x 2 position arrays
    nets: list = field(default_factory=list)    # network dict snapshots
    var: list = field(default_factory=list)
    xcut: list = field(default_factory=list)
    mod: list = field(default_factory=list)


# --- helpers (defined before anything that uses them) ----------------------

def _parties(engine) -> np.ndarray:
    return engine.attr_array("party", default=0).astype(int)


def _colors(parties) -> list:
    return [PARTY_COLORS.get(int(p), "#74797f") for p in parties]


def _record(run: Run, engine, t: int) -> None:
    """Snapshot positions, the network, and the three metrics at tick t."""
    pos = engine.positions()
    net = engine.env.attrs["network"]
    run.ticks.append(t)
    run.pos.append(pos.copy())
    # Snapshot the adjacency so the animation freezes the graph at this tick.
    run.nets.append({i: set(net.neighbors(i)) for i in net.node_ids})
    run.var.append(variance(pos))
    run.xcut.append(cross_cutting_tie_fraction(engine.agents, net))
    run.mod.append(party_modularity(engine.agents, net))


def _cloud(go, pos, colors):
    return go.Scatter(
        x=pos[:, 0], y=pos[:, 1], mode="markers",
        marker=dict(size=5, color=colors, opacity=0.85),
        showlegend=False, hoverinfo="skip",
    )


def _edges(go, pos, net, parties):
    """Two line traces: same-party ties (faint grey) and cross-party ties
    (gold). Watching the gold edges thin out is the S4 story."""
    sx, sy, cx, cy = [], [], [], []
    for i, nbrs in net.items():
        for j in nbrs:
            if j <= i:
                continue
            if parties[i] == parties[j]:
                sx += [pos[i, 0], pos[j, 0], None]
                sy += [pos[i, 1], pos[j, 1], None]
            else:
                cx += [pos[i, 0], pos[j, 0], None]
                cy += [pos[i, 1], pos[j, 1], None]
    same = go.Scatter(x=sx, y=sy, mode="lines", showlegend=False,
                      hoverinfo="skip", line=dict(color=SAME_EDGE, width=0.7))
    cross = go.Scatter(x=cx, y=cy, mode="lines", showlegend=False,
                       hoverinfo="skip", line=dict(color=CROSS_EDGE, width=1.2))
    return same, cross


def _panel(go, run: Run, f: int, colors):
    """The three traces for one cloud panel at frame f: edges then markers."""
    same, cross = _edges(go, run.pos[f], run.nets[f], run.parties)
    return same, cross, _cloud(go, run.pos[f], colors)


def _controls(ticks) -> dict:
    play = dict(type="buttons", showactive=False, x=0.02, y=1.22, buttons=[
        dict(label="Play", method="animate",
             args=[None, dict(frame=dict(duration=90, redraw=True), fromcurrent=True)]),
        dict(label="Pause", method="animate",
             args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")]),
    ])
    slider = dict(active=0, x=0.12, len=0.85, y=1.14, currentvalue=dict(prefix="tick "),
                  steps=[dict(method="animate", label=str(t),
                              args=[[str(t)], dict(frame=dict(duration=0, redraw=True),
                                                   mode="immediate")])
                         for t in ticks])
    return dict(updatemenus=[play], sliders=[slider])


def _boundaries(fig, boundaries) -> None:
    for t, lbl in boundaries:
        fig.add_vline(x=t, line=dict(color="#8b2530", width=1, dash="dot"))
        fig.add_annotation(x=t, y=1.0, yref="paper", text=lbl, showarrow=False,
                           textangle=-90, xanchor="left", font=dict(size=10))


def _write_html(out: Path, *figs) -> None:
    import plotly.io as pio
    parts = ["<html><head><meta charset='utf-8'></head><body>"]
    for i, fig in enumerate(figs):
        parts.append(pio.to_html(
            fig, full_html=False, auto_play=False,
            include_plotlyjs="cdn" if i == 0 else False,
        ))
    parts.append("</body></html>")
    out.write_text("".join(parts), encoding="utf-8")


# --- engine runs -----------------------------------------------------------

def run_isolated(stage_index, seed, steps, every, n_agents) -> Run:
    """Build one stage fresh at t=0 and run it alone."""
    engine = build_engine(seed, n_agents=n_agents)
    apply_intervention(engine, PILLAR.interventions[stage_index])
    run = Run(parties=_parties(engine))
    for t in range(steps + 1):
        if t % every == 0 or t == steps:
            _record(run, engine, t)
        if t < steps:
            engine.step()
    return run


def run_journey(seed, steps_per_stage, every, n_agents):
    """One society: apply each stage in turn, running between switches."""
    engine = build_engine(seed, n_agents=n_agents)
    run = Run(parties=_parties(engine))
    boundaries, t = [], 0
    for interv in PILLAR.interventions:
        apply_intervention(engine, interv)
        boundaries.append((t, interv.label))
        for _ in range(steps_per_stage):
            if t % every == 0:
                _record(run, engine, t)
            engine.step()
            t += 1
    _record(run, engine, t)
    return run, boundaries


# --- views -----------------------------------------------------------------

def show_stages(seed, steps, every, n_agents, out) -> None:
    interventions = PILLAR.interventions
    runs = [run_isolated(i, seed, steps, every, n_agents)
            for i in range(len(interventions))]
    labels = [iv.label for iv in interventions]
    ticks = runs[0].ticks
    n = len(runs)

    print(f"\ncalm_to_camps - each stage isolated  "
          f"(seed {seed}, {n_agents} agents, {steps} ticks)\n")
    print("  " + f"{'tick':>6}" + "".join(f"{l[:16]:>18}" for l in labels))
    for r, tk in enumerate(ticks):
        print(f"  {tk:>6}" + "".join(f"{runs[s].var[r]:>18.4f}" for s in range(n)))
    print()
    for iv, run in zip(interventions, runs):
        print(f"  {iv.label:<22} variance {run.var[0]:.3f} -> {run.var[-1]:.3f}"
              f"   x-cut {run.xcut[0]:.3f} -> {run.xcut[-1]:.3f}"
              f"   modularity {run.mod[0]:.3f} -> {run.mod[-1]:.3f}")
    print()

    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        print("  plotly not installed - console summary only.\n")
        return

    colors = [_colors(r.parties) for r in runs]
    cloud = make_subplots(rows=1, cols=n, subplot_titles=labels,
                          horizontal_spacing=min(0.06, 0.8 / max(n - 1, 1)))
    for i, run in enumerate(runs):
        for tr in _panel(go, run, 0, colors[i]):
            cloud.add_trace(tr, row=1, col=i + 1)
    cloud.frames = [
        go.Frame(name=str(ticks[f]), traces=list(range(3 * n)),
                 data=[tr for i in range(n)
                       for tr in _panel(go, runs[i], f, colors[i])])
        for f in range(len(ticks))
    ]
    cloud.update_xaxes(range=[-1.08, 1.08], showgrid=False, zeroline=True)
    cloud.update_yaxes(range=[-1.08, 1.08], showgrid=False, zeroline=True)
    cloud.update_layout(
        title=f"Each stage isolated - agent clouds + tie network (seed {seed})",
        height=470, margin=dict(t=140), **_controls(ticks))

    var_fig = go.Figure()
    for i, (iv, run) in enumerate(zip(interventions, runs)):
        var_fig.add_trace(go.Scatter(x=run.ticks, y=run.var, name=iv.label,
                                     line=dict(color=STAGE_LINE[i % len(STAGE_LINE)],
                                               width=3)))
    var_fig.update_layout(title="Polarization (ideology variance) - each stage from t=0",
                          xaxis_title="tick", yaxis_title="variance",
                          height=360, margin=dict(t=60))

    net_fig = make_subplots(rows=1, cols=2,
                            subplot_titles=["Cross-cutting tie fraction",
                                            "Party modularity Q"])
    for i, (iv, run) in enumerate(zip(interventions, runs)):
        c = STAGE_LINE[i % len(STAGE_LINE)]
        net_fig.add_trace(go.Scatter(x=run.ticks, y=run.xcut, name=iv.label,
                                     line=dict(color=c, width=3)), row=1, col=1)
        net_fig.add_trace(go.Scatter(x=run.ticks, y=run.mod, name=iv.label,
                                     showlegend=False,
                                     line=dict(color=c, width=3)), row=1, col=2)
    net_fig.update_xaxes(title_text="tick")
    net_fig.update_layout(
        title="Network sorting - flat through S0-S3 (inert tie network), moves in S4",
        height=360, margin=dict(t=70))

    _write_html(out, cloud, var_fig, net_fig)
    print(f"  Interactive view written to: {out}\n")


def show_journey(seed, steps, every, n_agents, out) -> None:
    run, boundaries = run_journey(seed, steps, every, n_agents)
    bset = {t: lbl for t, lbl in boundaries}

    print(f"\ncalm_to_camps - continuous journey  "
          f"(seed {seed}, {n_agents} agents, {steps} ticks/stage)\n")
    print(f"  {'tick':>6}  {'variance':>10}  {'x-cut':>8}  {'modularity':>11}  stage starts")
    for k, tk in enumerate(run.ticks):
        mark = f"  <- {bset[tk]}" if tk in bset else ""
        print(f"  {tk:>6}  {run.var[k]:>10.4f}  {run.xcut[k]:>8.3f}  "
              f"{run.mod[k]:>11.3f}{mark}")
    print()

    try:
        import plotly.graph_objects as go
    except ImportError:
        print("  plotly not installed - console summary only.\n")
        return

    colors = _colors(run.parties)
    cloud = go.Figure(list(_panel(go, run, 0, colors)))
    cloud.frames = [
        go.Frame(name=str(run.ticks[f]), traces=[0, 1, 2],
                 data=list(_panel(go, run, f, colors)))
        for f in range(len(run.ticks))
    ]
    cloud.update_xaxes(range=[-1.08, 1.08], showgrid=False, zeroline=True)
    cloud.update_yaxes(range=[-1.08, 1.08], showgrid=False, zeroline=True)
    cloud.update_layout(
        title=f"The journey - one society, agent clouds + tie network (seed {seed})",
        height=580, width=620, margin=dict(t=140), **_controls(run.ticks))

    var_fig = go.Figure()
    var_fig.add_trace(go.Scatter(x=run.ticks, y=run.var, name="variance",
                                 line=dict(color="#1f3565", width=3)))
    _boundaries(var_fig, boundaries)
    var_fig.update_layout(title="Polarization across the journey (dotted = a stage switches on)",
                          xaxis_title="tick", yaxis_title="variance",
                          height=360, margin=dict(t=60))

    net_fig = go.Figure()
    net_fig.add_trace(go.Scatter(x=run.ticks, y=run.xcut, name="cross-cutting tie fraction",
                                 line=dict(color="#d69e2e", width=3)))
    net_fig.add_trace(go.Scatter(x=run.ticks, y=run.mod, name="party modularity Q",
                                 line=dict(color="#2a4a52", width=3)))
    _boundaries(net_fig, boundaries)
    net_fig.update_layout(title="Network sorting across the journey (moves once S4 switches on)",
                          xaxis_title="tick", height=360, margin=dict(t=60))

    _write_html(out, cloud, var_fig, net_fig)
    print(f"  Interactive view written to: {out}\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["stages", "journey"], default="stages")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--steps", type=int, default=150,
                    help="ticks per stage (isolated run length, or journey segment)")
    ap.add_argument("--every", type=int, default=10)
    ap.add_argument("--agents", type=int, default=200,
                    help="population size (kept modest so the edge animation stays snappy)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    out = Path(args.out or f"pillar_{args.mode}.html").resolve()
    if args.mode == "stages":
        show_stages(args.seed, args.steps, args.every, args.agents, out)
    else:
        show_journey(args.seed, args.steps, args.every, args.agents, out)
    print("  Open it in a browser and hit Play.\n")


if __name__ == "__main__":
    main()
