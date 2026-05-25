"""
ACTB scenario — Mäs-Flache Argument-Communication Theory of Bi-polarization.

Pure test of the claim that bi-polarization can emerge from homophily +
argument adoption *without* any negative influence. The only rules active
are ArgumentExchange and a small noise term. Compare against compass_basic
(which needs repulsion to drive corners) — ACTB should still produce
clusters at extremes purely from biased argument adoption.

Same initial setup as compass_basic so visuals are directly comparable.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.engine import Engine
from ..core.environment import Environment
from ..core.rules import RulePipeline
from ..core.space import ContinuousSpace2D
from ..core.state import AgentState
from ..rules.argument_exchange import ArgumentExchange
from ..rules.noise import GaussianNoise


TITLE = "ACTB — bi-polarization without repulsion"

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
    homophily_radius: float = 0.3,
    step: float = 0.02,
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
            ArgumentExchange(homophily_radius=homophily_radius, step=step),
            GaussianNoise(sigma=noise),
        ]
    )
    return Engine(agents=agents, env=env, space=space, rules=rules, seed=seed)
