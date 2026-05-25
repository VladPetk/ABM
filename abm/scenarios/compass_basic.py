"""
Basic political-compass scenario — no parties, no media, just dynamics.

Agents start uniformly random on [-1, 1]^2. Each is tagged with a fixed
`group` attribute equal to its starting quadrant, so the viz can show
whether starting tribes mix or remain separated as the simulation runs.

By default this is now Hegselmann-Krause attraction + noise only —
backlash repulsion is empirically contested, so it's opt-in (set
`repulsion > 0`). Compare against `actb` (Mäs-Flache argument exchange,
no repulsion) and `two_party_sorting` (two-layer identity model).
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.engine import Engine
from ..core.environment import Environment
from ..core.rules import RulePipeline
from ..core.space import ContinuousSpace2D
from ..core.state import AgentState
from ..rules.influence import BoundedConfidenceInfluence
from ..rules.noise import GaussianNoise
from ..rules.repulsion import BacklashRepulsion


TITLE = "Compass Basic — Hegselmann-Krause"

GROUP_NAMES = {
    0: "Libertarian Left",
    1: "Libertarian Right",
    2: "Authoritarian Left",
    3: "Authoritarian Right",
}
GROUP_COLORS = {
    0: "#1f3565",   # libertarian left   — deep navy
    1: "#553f6b",   # libertarian right  — deep aubergine
    2: "#2a4a52",   # authoritarian left — deep teal
    3: "#8b2530",   # authoritarian right — deep oxblood
}


def _quadrant(pos: np.ndarray) -> int:
    x, y = pos
    if x < 0 and y < 0:
        return 0
    if x >= 0 and y < 0:
        return 1
    if x < 0 and y >= 0:
        return 2
    return 3


def build(
    n_agents: int = 300,
    epsilon: float = 0.3,
    attraction: float = 0.1,
    repulsion: float = 0.0,
    repulsion_range: float = 1.5,
    noise: float = 0.01,
    seed: int = 0,
) -> Engine:
    rng = np.random.default_rng(seed)
    agents: list[Agent] = []
    for i in range(n_agents):
        pos = rng.uniform(-1.0, 1.0, size=2)
        agents.append(
            Agent(
                id=i,
                state=AgentState(
                    ideology=pos,
                    attrs={"group": _quadrant(pos), "origin": pos.copy()},
                ),
            )
        )
    env = Environment(
        attrs={
            "viz": {
                "title": TITLE,
                "group_names": GROUP_NAMES,
                "group_colors": GROUP_COLORS,
                "show_parties": False,
            }
        }
    )
    space = ContinuousSpace2D(bounds=((-1.0, 1.0), (-1.0, 1.0)))
    rules = RulePipeline(
        [
            BoundedConfidenceInfluence(epsilon=epsilon, strength=attraction),
            BacklashRepulsion(epsilon=epsilon, max_range=repulsion_range, strength=repulsion),
            GaussianNoise(sigma=noise),
        ]
    )
    return Engine(agents=agents, env=env, space=space, rules=rules, seed=seed)
