"""
Solara dashboard — live political compass with reactive parameters.

Run with:
    solara run abm.viz.solara_app

The viz module is the only place that knows about Solara/Plotly. Engine and
rules are imported as pure Python; swapping the UI is a single-file change.
Scenarios provide their own viz metadata (titles, group colors, party
anchors) via env.attrs["viz"], so the dashboard stays scenario-agnostic.
"""
from __future__ import annotations

import threading
import time

import numpy as np
import plotly.graph_objects as go
import solara

from ..metrics import (
    affective_polarization,
    bimodality,
    ideological_constraint,
    mean_pairwise_distance,
    quadrant_counts,
    sorting_index,
    variance,
)
from ..scenarios import REGISTRY

# --- reactive parameter state --------------------------------------------------

SCENARIO_NAMES = list(REGISTRY.keys())

scenario = solara.reactive(SCENARIO_NAMES[0])
n_agents = solara.reactive(300)
epsilon = solara.reactive(0.30)
attraction = solara.reactive(0.10)
repulsion = solara.reactive(0.00)
noise = solara.reactive(0.01)
party_pull_strength = solara.reactive(0.04)
affect_lr = solara.reactive(0.01)
n_identities = solara.reactive(3)
sort_rate = solara.reactive(0.05)
identity_weight = solara.reactive(0.5)
elite_drift_rate = solara.reactive(0.0008)
media_period = solara.reactive(120)
media_strength = solara.reactive(0.06)
partisan_media_strength = solara.reactive(0.03)
seed = solara.reactive(0)
fps = solara.reactive(20)

tick_count = solara.reactive(0)
running = solara.reactive(False)
engine_box: solara.Reactive = solara.reactive(None)

# Time-series buffer. Capped (ring) to avoid unbounded growth.
HISTORY_CAP = 1000
metric_history: solara.Reactive = solara.reactive(None)


def _new_history() -> dict[str, list]:
    return {"tick": [], "variance": [], "affective": [], "constraint": [], "sorting": []}


def _record_metrics():
    """Capture metrics for the current tick (called from manual step + ticker)."""
    eng = engine_box.value
    if eng is None:
        return
    h = metric_history.value
    if h is None or (h["tick"] and h["tick"][-1] == eng.tick):
        return
    pos = eng.positions()
    var_pos = variance(pos)
    aff = affective_polarization(eng.agents)
    ic = ideological_constraint(eng.agents)
    si = sorting_index(eng.agents)
    h["tick"].append(eng.tick)
    h["variance"].append(var_pos)
    h["affective"].append(np.nan if np.isnan(aff) else (1.0 - float(aff)) / 2.0)  # ∈ [0, 1]; higher = more polarized
    h["constraint"].append((ic["x"] + ic["y"]) / 2.0)
    h["sorting"].append(si)
    # Ring trim
    if len(h["tick"]) > HISTORY_CAP:
        for k in h:
            del h[k][: len(h[k]) - HISTORY_CAP]
    # Trigger reactivity by reassigning
    metric_history.value = {k: list(v) for k, v in h.items()}


def _make_engine():
    name = scenario.value
    if name == "compass_basic":
        eng = REGISTRY[name](
            n_agents=n_agents.value,
            epsilon=epsilon.value,
            attraction=attraction.value,
            repulsion=repulsion.value,
            noise=noise.value,
            seed=seed.value,
        )
    elif name == "actb":
        eng = REGISTRY[name](
            n_agents=n_agents.value,
            homophily_radius=epsilon.value,
            step=attraction.value,
            noise=noise.value,
            seed=seed.value,
        )
    elif name == "two_party_sorting":
        eng = REGISTRY[name](
            n_agents=n_agents.value,
            epsilon=epsilon.value,
            attraction=attraction.value,
            party_pull=party_pull_strength.value,
            affect_lr=affect_lr.value,
            n_identities=n_identities.value,
            sort_rate=sort_rate.value,
            identity_weight=identity_weight.value,
            noise=noise.value,
            seed=seed.value,
        )
    elif name == "multi_party_4":
        eng = REGISTRY[name](
            n_agents=n_agents.value,
            epsilon=epsilon.value,
            attraction=attraction.value,
            party_pull=party_pull_strength.value,
            affect_lr=affect_lr.value,
            n_identities=n_identities.value,
            sort_rate=sort_rate.value,
            identity_weight=identity_weight.value,
            noise=noise.value,
            seed=seed.value,
        )
    elif name == "elite_dynamics":
        eng = REGISTRY[name](
            n_agents=n_agents.value,
            epsilon=epsilon.value,
            attraction=attraction.value,
            party_pull=party_pull_strength.value,
            affect_lr=affect_lr.value,
            n_identities=n_identities.value,
            sort_rate=sort_rate.value,
            identity_weight=identity_weight.value,
            elite_drift_rate=elite_drift_rate.value,
            media_period=media_period.value,
            media_strength=media_strength.value,
            partisan_media_strength=partisan_media_strength.value,
            noise=noise.value,
            seed=seed.value,
        )
    else:
        eng = REGISTRY[name](n_agents=n_agents.value, seed=seed.value)
    engine_box.value = eng
    tick_count.value = 0
    metric_history.value = _new_history()
    _record_metrics()


# --- background ticker (singleton thread) --------------------------------------

_ticker_started = False
_ticker_lock = threading.Lock()


def _ensure_ticker():
    global _ticker_started
    with _ticker_lock:
        if _ticker_started:
            return
        _ticker_started = True

    def loop():
        while True:
            if running.value and engine_box.value is not None:
                engine_box.value.step()
                tick_count.value = engine_box.value.tick
                _record_metrics()
            time.sleep(max(1.0 / max(fps.value, 1), 0.01))

    threading.Thread(target=loop, daemon=True).start()


# --- compass figure ------------------------------------------------------------


def _compass_figure(engine) -> go.Figure:
    viz = engine.env.attrs.get("viz", {})
    group_names = viz.get("group_names", {})
    group_colors = viz.get("group_colors", {})
    title = viz.get("title", "Political Compass")
    show_parties = viz.get("show_parties", False)
    party_centers = viz.get("party_centers", {})

    pos = engine.positions()
    groups = engine.attr_array("group", default=0).astype(int)

    fig = go.Figure()
    for gid in sorted(set(groups.tolist())):
        mask = groups == gid
        if not mask.any():
            continue
        fig.add_trace(
            go.Scatter(
                x=pos[mask, 0],
                y=pos[mask, 1],
                mode="markers",
                marker=dict(
                    size=8,
                    color=group_colors.get(gid, "#9ca3af"),
                    opacity=0.75,
                    line=dict(width=0),
                ),
                name=group_names.get(gid, f"Group {gid}"),
                hovertemplate="(%{x:.2f}, %{y:.2f})<extra></extra>",
            )
        )

    if show_parties and party_centers:
        for pid, center in party_centers.items():
            fig.add_trace(
                go.Scatter(
                    x=[center[0]], y=[center[1]],
                    mode="markers+text",
                    marker=dict(size=18, color=group_colors.get(pid, "#fff"),
                                symbol="star", line=dict(width=2, color="#fff")),
                    text=[group_names.get(pid, f"P{pid}")],
                    textposition="top center",
                    textfont=dict(color="#fff", size=11),
                    showlegend=False,
                )
            )

    # Recent media-shock marker (fades over ~30 ticks after firing)
    last_event = engine.env.attrs.get("last_event")
    if viz.get("show_last_event") and last_event:
        age = engine.tick - last_event["tick"]
        if 0 <= age < 30:
            opacity = max(0.0, 1.0 - age / 30.0)
            tx, ty = last_event["target"]
            fig.add_trace(
                go.Scatter(
                    x=[tx], y=[ty],
                    mode="markers+text",
                    marker=dict(
                        size=30, color="#fbbf24", symbol="x-thin",
                        opacity=opacity, line=dict(width=4, color="#fbbf24"),
                    ),
                    text=[f"📡 t={last_event['tick']}"],
                    textposition="bottom center",
                    textfont=dict(color="#fbbf24", size=10),
                    showlegend=False,
                )
            )

    fig.update_layout(
        xaxis=dict(
            range=[-1.05, 1.05],
            zeroline=True, zerolinecolor="#888", zerolinewidth=1,
            showgrid=True, gridcolor="#222",
            title="← Left          Economic axis          Right →",
        ),
        yaxis=dict(
            range=[-1.05, 1.05],
            zeroline=True, zerolinecolor="#888", zerolinewidth=1,
            showgrid=True, gridcolor="#222",
            title="← Libertarian     Social axis     Authoritarian →",
            scaleanchor="x", scaleratio=1,
        ),
        width=640, height=640,
        margin=dict(l=60, r=20, t=50, b=60),
        template="plotly_dark",
        title=f"{title} — tick {engine.tick}",
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
    )
    return fig


def _history_figure() -> go.Figure:
    h = metric_history.value or _new_history()
    ticks = h["tick"]

    fig = go.Figure()
    # Always-on: ideological dispersion (normalized to ~[0, 1])
    if h["variance"]:
        var_norm = [min(v / 0.667, 1.5) for v in h["variance"]]
        fig.add_trace(go.Scatter(x=ticks, y=var_norm, name="ideological dispersion (var / 0.667)",
                                 mode="lines", line=dict(color="#9ca3af", width=2)))
    # Identity-aware metrics — only meaningful when parties exist
    aff_series = [v for v in h["affective"] if not np.isnan(v)]
    if aff_series:
        fig.add_trace(go.Scatter(x=ticks, y=h["affective"], name="affective polarization",
                                 mode="lines", line=dict(color="#ef4444", width=2.5)))
    con_series = [v for v in h["constraint"] if not np.isnan(v)]
    if con_series and not all(np.isnan(v) for v in h["constraint"]):
        fig.add_trace(go.Scatter(x=ticks, y=h["constraint"], name="ideological constraint",
                                 mode="lines", line=dict(color="#3b82f6", width=2)))
    sort_series = [v for v in h["sorting"] if not np.isnan(v)]
    if sort_series:
        fig.add_trace(go.Scatter(x=ticks, y=h["sorting"], name="sorting index (Mason)",
                                 mode="lines", line=dict(color="#f59e0b", width=2)))

    fig.update_layout(
        xaxis_title="tick",
        yaxis=dict(title="metric (0 = none → 1 = max)", range=[-0.05, 1.4]),
        template="plotly_dark",
        height=300, margin=dict(l=50, r=20, t=30, b=40),
        title="Polarization over time",
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
    )
    return fig


# --- the page ------------------------------------------------------------------


@solara.component
def Page():
    _ensure_ticker()
    if engine_box.value is None:
        _make_engine()

    _ = tick_count.value  # re-render on tick

    engine = engine_box.value
    pos = engine.positions()
    var = variance(pos)
    mpd = mean_pairwise_distance(pos)
    bx = bimodality(pos[:, 0])
    by = bimodality(pos[:, 1])
    q = quadrant_counts(pos)
    aff = affective_polarization(engine.agents)
    ic = ideological_constraint(engine.agents)
    si = sorting_index(engine.agents)

    has_parties = any(a.state.attrs.get("party") is not None for a in engine.agents)
    has_identities = any(a.state.attrs.get("identities") is not None for a in engine.agents)
    is_actb = scenario.value == "actb"
    is_sorting_scenario = scenario.value in ("two_party_sorting", "multi_party_4", "elite_dynamics")
    is_elite_dynamics = scenario.value == "elite_dynamics"

    with solara.Sidebar():
        solara.Markdown("## Scenario")
        solara.Select(
            label="Scenario",
            value=scenario,
            values=SCENARIO_NAMES,
            on_value=lambda _: (_make_engine(), setattr(running, "value", False)),
        )

        solara.Markdown("## Parameters")
        solara.SliderInt("Agents", value=n_agents, min=50, max=1000, step=50)
        solara.SliderFloat(
            "Homophily radius (ε)" if is_actb else "Tolerance (ε)",
            value=epsilon, min=0.05, max=1.0, step=0.05,
        )
        solara.SliderFloat(
            "ACTB step" if is_actb else "Attraction",
            value=attraction, min=0.0, max=0.5, step=0.01,
        )
        if scenario.value == "compass_basic":
            solara.SliderFloat("Backlash repulsion (opt-in)", value=repulsion, min=0.0, max=0.5, step=0.01)
        if is_sorting_scenario:
            solara.SliderFloat("Party pull", value=party_pull_strength, min=0.0, max=0.2, step=0.01)
            solara.SliderFloat("Affect learning rate", value=affect_lr, min=0.0, max=0.05, step=0.005)
            solara.SliderInt("Identity dimensions", value=n_identities, min=0, max=10)
            solara.SliderFloat("Identity sorting rate", value=sort_rate, min=0.0, max=0.1, step=0.005)
            solara.SliderFloat("Identity weight in affect", value=identity_weight, min=0.0, max=1.0, step=0.05)
        if is_elite_dynamics:
            solara.Markdown("**Stage 3.1 — media & elite**")
            solara.SliderFloat("Elite drift rate", value=elite_drift_rate, min=0.0, max=0.003, step=0.0001)
            solara.SliderInt("Media shock period", value=media_period, min=20, max=500, step=10)
            solara.SliderFloat("Media shock strength", value=media_strength, min=0.0, max=0.2, step=0.01)
            solara.SliderFloat("Partisan media strength", value=partisan_media_strength, min=0.0, max=0.1, step=0.005)
        solara.SliderFloat("Noise σ", value=noise, min=0.0, max=0.05, step=0.002)
        solara.SliderInt("Seed", value=seed, min=0, max=999)
        solara.SliderInt("FPS", value=fps, min=1, max=60)

        solara.Markdown("## Controls")

        def on_step():
            if engine_box.value:
                engine_box.value.step()
                tick_count.value = engine_box.value.tick
                _record_metrics()

        def on_toggle():
            running.value = not running.value

        def on_reset():
            running.value = False
            _make_engine()

        with solara.Row():
            solara.Button("Step", on_click=on_step, disabled=running.value)
            solara.Button("Pause" if running.value else "Play", on_click=on_toggle, color="primary")
            solara.Button("Reset", on_click=on_reset)

        solara.Markdown(
            "Slider changes apply on **Reset** (so dynamics stay reproducible)."
        )

    with solara.Column():
        solara.FigurePlotly(_compass_figure(engine))
        solara.FigurePlotly(_history_figure())

        with solara.Card("Position-based metrics"):
            solara.Markdown(
                f"""
**Tick:** {engine.tick}  •  **Agents:** {len(engine.agents)}

- **Variance**: `{var:.3f}`  •  **Mean pairwise dist**: `{mpd:.3f}`
- **Bimodality** — econ: `{bx:.3f}`, social: `{by:.3f}` *(>0.555 ≈ bimodal)*
- **Quadrants:**  LL `{q['lib_left']}`  LR `{q['lib_right']}`  AL `{q['auth_left']}`  AR `{q['auth_right']}`
                """
            )

        if has_parties:
            aff_str = "n/a" if np.isnan(aff) else f"{aff:+.3f}"
            with solara.Card("Identity-based metrics (Stage 2)"):
                identity_line = ""
                if has_identities:
                    si_str = "n/a" if np.isnan(si) else f"{si:.3f}"
                    identity_line = (
                        f"\n- **Sorting index** (Mason mega-identity, mean |corr(party, identity)|): `{si_str}`"
                    )
                solara.Markdown(
                    f"""
- **Affective polarization** (mean out-party warmth, lower = more polarized): `{aff_str}`
- **Ideological constraint** — econ: `{ic['x']:.3f}`, social: `{ic['y']:.3f}` *(0 = unsorted, 1 = perfectly sorted)*{identity_line}

> Affective polarization captures out-party *dislike* — distinct from
> ideological distance. Iyengar et al. 2019: this is the variable that
> has moved fastest in real-world US data.
                """
                )
