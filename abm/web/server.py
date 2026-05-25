"""
FastAPI app + WebSocket bridge between the Python engine and a static frontend.

Run with:
    uvicorn abm.web.server:app --host 0.0.0.0 --port 8000 --reload

WebSocket protocol (JSON, at /api/ws):
  client -> server
    {"type": "load", "scenario": <key>, "params": {...}}   build fresh engine
    {"type": "play"}                                       start ticking
    {"type": "pause"}                                      stop ticking
    {"type": "step"}                                       single tick
    {"type": "reset"}                                      rebuild with current scenario/params
    {"type": "param", "name": <slider>, "value": <num>}    live-mutate rule attr
    {"type": "speed", "value": <fps>}                      ticks/sec target
    {"type": "select_agent", "id": <int|null>}             pin/unpin inspector target
    {"type": "set_diet", "agent_id": <int>, "diet": {outlet_id: weight}}
                                                           rewrite an agent's media diet live

  server -> client
    {"type": "scenarios", "items": [...]}                  sent on connect
    {"type": "loaded", "key": ..., "detail": {...}, "viz": {...}}
       viz.outlets = [{id, name, position, color}, ...]    when scenario has outlets
    {"type": "tick", "t": int, "agents": [[x, y, group], ...],
                     "parties": {gid: [x, y]}, "metrics": {...},
                     "event": {tick, target, strength} | null}
    {"type": "inspect", "agent": {..., "media_diet": {outlet_id: weight}}}
"""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from ..metrics import (
    affective_polarization,
    ideological_constraint,
    sorting_index,
    variance,
)
from ..scenarios import REGISTRY
from .scenarios_meta import (
    DEFAULT_SCENARIO,
    SCENARIOS,
    apply_param,
    detail_for_ui,
    list_for_ui,
)

log = logging.getLogger("abm.web")

# --- static frontend mount ----------------------------------------------------

WEBSITE_DIR = Path(__file__).resolve().parents[2] / "website"

app = FastAPI(title="polarlab")


@app.get("/api/scenarios")
def get_scenarios():
    return {"items": list_for_ui(), "default": DEFAULT_SCENARIO}


@app.get("/api/scenarios/{key}")
def get_scenario_detail(key: str):
    if key not in SCENARIOS:
        return {"error": "unknown scenario"}, 404
    return detail_for_ui(key)


# --- per-session engine state -------------------------------------------------

class Session:
    def __init__(self):
        self.scenario_key: str = DEFAULT_SCENARIO
        self.params: dict = dict(SCENARIOS[DEFAULT_SCENARIO]["default_params"])
        self.engine = None
        self.running = False
        self.fps = 20
        self.pinned_agent_id: int | None = None
        self._build()

    def _build(self):
        builder = REGISTRY[self.scenario_key]
        self.engine = builder(**self.params)
        self.pinned_agent_id = None

    def load(self, scenario_key: str, params_overrides: dict | None = None):
        if scenario_key not in SCENARIOS:
            return
        self.scenario_key = scenario_key
        self.params = dict(SCENARIOS[scenario_key]["default_params"])
        if params_overrides:
            self.params.update({k: v for k, v in params_overrides.items() if k in self.params})
        self._build()

    def reset(self):
        self._build()

    def set_param(self, name: str, value):
        # Update stored param so reset reproduces this state
        if name in self.params:
            self.params[name] = value
        # Live-mutate the engine's rule
        apply_param(self.engine, self.scenario_key, name, value)


# --- serialization helpers ----------------------------------------------------

def _engine_snapshot(session: Session) -> dict:
    eng = session.engine
    positions = eng.positions().tolist()
    groups = eng.attr_array("group", default=0).astype(int).tolist()
    # combine into [x, y, group]
    agents = [[round(p[0], 4), round(p[1], 4), int(g)] for p, g in zip(positions, groups)]

    parties = {}
    party_dict = eng.env.attrs.get("parties") or {}
    for pid, center in party_dict.items():
        parties[int(pid)] = [float(center[0]), float(center[1])]

    # Metrics
    pos_arr = eng.positions()
    aff = affective_polarization(eng.agents)
    ic = ideological_constraint(eng.agents)
    si = sorting_index(eng.agents)
    metrics = {
        "polarization": float(variance(pos_arr)),
        "affect": None if np.isnan(aff) else float(aff),
        "constraint": float((ic["x"] + ic["y"]) / 2),
        "sorting": None if np.isnan(si) else float(si),
    }

    # Cross-talk approximation: fraction of agents within affect_radius of an out-party agent
    # (placeholder simple version — use party-group adjacency in same screen position)
    metrics["cross_talk"] = _cross_talk(eng)
    metrics["largest_faction"] = _largest_faction(groups)
    metrics["bimodality"] = _bimodality(pos_arr[:, 0])

    last_event = eng.env.attrs.get("last_event")
    event = None
    if last_event and eng.tick - last_event["tick"] < 30:
        event = {
            "tick": int(last_event["tick"]),
            "target": [float(last_event["target"][0]), float(last_event["target"][1])],
            "age": int(eng.tick - last_event["tick"]),
        }

    return {
        "type": "tick",
        "t": int(eng.tick),
        "agents": agents,
        "parties": parties,
        "metrics": metrics,
        "event": event,
    }


def _cross_talk(eng) -> float:
    """Fraction of agent pairs (within close range) that span parties. 0..1."""
    parties = [a.state.attrs.get("party") for a in eng.agents]
    if not any(p is not None for p in parties):
        # No parties — approximate with "fraction of close neighbor pairs on opposite sides of x=0"
        pos = eng.positions()
        if len(pos) < 2:
            return 0.0
        # Sample 200 random pairs
        n = len(pos)
        rng = np.random.default_rng(0)
        idxs = rng.integers(0, n, size=(200, 2))
        diffs = pos[idxs[:, 0]] - pos[idxs[:, 1]]
        close = np.linalg.norm(diffs, axis=1) < 0.4
        opposite_sign = (pos[idxs[:, 0], 0] * pos[idxs[:, 1], 0]) < 0
        if close.sum() == 0:
            return 0.0
        return float((close & opposite_sign).sum() / close.sum())
    # With parties: sample pairs within proximity, count cross-party
    pos = eng.positions()
    n = len(pos)
    rng = np.random.default_rng(0)
    idxs = rng.integers(0, n, size=(200, 2))
    diffs = pos[idxs[:, 0]] - pos[idxs[:, 1]]
    close = np.linalg.norm(diffs, axis=1) < 0.4
    cross = np.array([parties[i] != parties[j] for i, j in idxs])
    if close.sum() == 0:
        return 0.0
    return float((close & cross).sum() / close.sum())


def _largest_faction(groups: list[int]) -> float:
    if not groups:
        return 0.0
    counts = {}
    for g in groups:
        counts[g] = counts.get(g, 0) + 1
    return float(max(counts.values()) / len(groups))


def _bimodality(values) -> float:
    n = len(values)
    if n < 4:
        return 0.0
    m = values.mean()
    s = values.std(ddof=1)
    if s == 0:
        return 0.0
    z = (values - m) / s
    g = (z**3).mean()
    k = (z**4).mean() - 3.0
    denom = k + 3.0 * ((n - 1) ** 2) / ((n - 2) * (n - 3))
    if denom <= 0:
        return 0.0
    return float((g * g + 1.0) / denom)


def _inspect_payload(session: Session) -> dict:
    aid = session.pinned_agent_id
    if aid is None or aid < 0 or aid >= len(session.engine.agents):
        return {"type": "inspect", "agent": None}
    a = session.engine.agents[aid]
    party = a.state.attrs.get("party")
    affect = a.state.attrs.get("affect", {}) or {}
    # Find six nearest neighbors for the network mini-map
    pos = session.engine.positions()
    me = np.array(a.state.ideology)
    dists = np.linalg.norm(pos - me, axis=1)
    dists[aid] = np.inf
    near_idx = np.argsort(dists)[:6]
    neighbours = []
    for idx in near_idx:
        n = session.engine.agents[int(idx)]
        np_pos = n.state.ideology
        neighbours.append({
            "id": int(n.id),
            "x": float(np_pos[0]),
            "y": float(np_pos[1]),
            "group": int(n.state.attrs.get("group", 0)),
            "party": None if n.state.attrs.get("party") is None else int(n.state.attrs.get("party")),
            "d": float(dists[idx]),
        })
    # Diversity: average distance to nearest 6
    diversity = float(np.mean([n["d"] for n in neighbours])) if neighbours else 0.0
    # Media diet: in elite_dynamics it's a dict {outlet_id: weight};
    # older scenarios may have a scalar (or nothing). We pass both forms
    # so the frontend can decide what to render.
    raw_diet = a.state.attrs.get("media_diet")
    if isinstance(raw_diet, dict):
        media_diet = {int(k): float(v) for k, v in raw_diet.items()}
    elif isinstance(raw_diet, (int, float)):
        media_diet = float(raw_diet)            # legacy scalar
    else:
        media_diet = None

    return {
        "type": "inspect",
        "agent": {
            "id": int(a.id),
            "x": float(a.state.ideology[0]),
            "y": float(a.state.ideology[1]),
            "group": int(a.state.attrs.get("group", 0)),
            "party": None if party is None else int(party),
            "identity_strength": float(a.state.attrs.get("identity_strength", 0.5)) if party is not None else None,
            "media_diet": media_diet,
            "affect": {int(k): float(v) for k, v in affect.items()},
            "neighbours": neighbours,
            "diversity": diversity,
        },
    }


# --- WebSocket endpoint -------------------------------------------------------

@app.websocket("/api/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    session = Session()

    # Send initial scenarios catalog + loaded scenario
    await ws.send_text(json.dumps({"type": "scenarios", "items": list_for_ui(), "default": DEFAULT_SCENARIO}))
    await ws.send_text(json.dumps({
        "type": "loaded",
        "key": session.scenario_key,
        "detail": detail_for_ui(session.scenario_key),
        "viz": _viz_payload(session),
    }))
    await ws.send_text(json.dumps(_engine_snapshot(session)))

    stop_event = asyncio.Event()

    async def ticker():
        while not stop_event.is_set():
            if session.running:
                session.engine.step()
                try:
                    await ws.send_text(json.dumps(_engine_snapshot(session)))
                    if session.pinned_agent_id is not None:
                        await ws.send_text(json.dumps(_inspect_payload(session)))
                except Exception:
                    return
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=max(1.0 / max(session.fps, 1), 0.02))
            except asyncio.TimeoutError:
                pass

    ticker_task = asyncio.create_task(ticker())

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            t = msg.get("type")

            if t == "load":
                session.load(msg.get("scenario", DEFAULT_SCENARIO), msg.get("params"))
                await ws.send_text(json.dumps({
                    "type": "loaded",
                    "key": session.scenario_key,
                    "detail": detail_for_ui(session.scenario_key),
                    "viz": _viz_payload(session),
                }))
                await ws.send_text(json.dumps(_engine_snapshot(session)))

            elif t == "play":
                session.running = True

            elif t == "pause":
                session.running = False

            elif t == "step":
                session.engine.step()
                await ws.send_text(json.dumps(_engine_snapshot(session)))

            elif t == "reset":
                session.reset()
                await ws.send_text(json.dumps(_engine_snapshot(session)))
                if session.pinned_agent_id is not None:
                    await ws.send_text(json.dumps(_inspect_payload(session)))

            elif t == "param":
                session.set_param(msg["name"], msg["value"])

            elif t == "speed":
                session.fps = max(1, min(60, int(msg.get("value", 20))))

            elif t == "select_agent":
                aid = msg.get("id")
                session.pinned_agent_id = None if aid is None else int(aid)
                await ws.send_text(json.dumps(_inspect_payload(session)))

            elif t == "set_diet":
                aid = int(msg.get("agent_id"))
                diet = msg.get("diet") or {}
                # Normalize diet to non-negative + sum > 0
                clean = {int(k): max(0.0, float(v)) for k, v in diet.items()}
                if sum(clean.values()) > 0 and 0 <= aid < len(session.engine.agents):
                    session.engine.agents[aid].state.attrs["media_diet"] = clean
                    # If the user is inspecting this agent, send the updated card.
                    if session.pinned_agent_id == aid:
                        await ws.send_text(json.dumps(_inspect_payload(session)))

    except WebSocketDisconnect:
        pass
    finally:
        stop_event.set()
        await ticker_task


def _viz_payload(session: Session) -> dict:
    viz = session.engine.env.attrs.get("viz", {})
    out = {
        "title": viz.get("title", "Sim"),
        "group_names": {int(k): v for k, v in viz.get("group_names", {}).items()},
        "group_colors": {int(k): v for k, v in viz.get("group_colors", {}).items()},
        "show_parties": bool(viz.get("show_parties", False)),
    }
    # Outlets, when the scenario has them — already JSON-safe in scenario builder.
    if "outlets" in viz:
        out["outlets"] = viz["outlets"]
    return out


# --- mount static frontend last (so /api routes win) --------------------------
if WEBSITE_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEBSITE_DIR), html=True), name="website")
