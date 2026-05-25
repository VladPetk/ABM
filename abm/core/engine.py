"""
Engine — owns agents, environment, space, and rule pipelines.

Tick has two phases:

1. **Env phase** — each EnvRule runs once and may mutate env state and/or
   agent state directly (modeling external forces: elite cues, media
   shocks, institutional shifts). Space is rebuilt afterward so that
   per-agent rules see the post-env world.
2. **Agent phase** — every Rule produces a StateDelta per agent against
   the same pre-tick snapshot. Deltas are summed across the pipeline and
   applied at once. Synchronous: rule order within the pipeline doesn't
   bias dynamics.
"""
from __future__ import annotations

import numpy as np

from .agent import Agent
from .environment import Environment
from .rules import EnvRule, RulePipeline, merge_attr
from .space import ContinuousSpace2D
from .state import StateDelta


class Engine:
    def __init__(
        self,
        agents: list[Agent],
        env: Environment,
        space: ContinuousSpace2D,
        rules: RulePipeline,
        env_rules: list[EnvRule] | None = None,
        seed: int = 0,
    ):
        self.agents = agents
        self.env = env
        self.space = space
        self.rules = rules
        self.env_rules: list[EnvRule] = list(env_rules) if env_rules else []
        self.rng = np.random.default_rng(seed)
        self.tick = 0
        self.space.rebuild(self.agents)

    def step(self) -> None:
        # --- Env phase ---
        if self.env_rules:
            for env_rule in self.env_rules:
                env_rule.apply(self.env, self.agents, self.space, self.rng, self.tick)
            self.space.rebuild(self.agents)

        # --- Agent phase ---
        deltas: dict[int, StateDelta] = {}
        for agent in self.agents:
            deltas[agent.id] = self.rules.apply(agent, self.space, self.env, self.rng)
        for agent in self.agents:
            d = deltas[agent.id]
            new_ideology = agent.state.ideology + d.d_ideology
            agent.state.ideology = self.space.clip(new_ideology)
            for k, v in d.d_attrs.items():
                agent.state.attrs[k] = merge_attr(agent.state.attrs.get(k), v)
        self.space.rebuild(self.agents)
        self.tick += 1

    def run(self, n_steps: int) -> None:
        for _ in range(n_steps):
            self.step()

    def positions(self) -> np.ndarray:
        if not self.agents:
            return np.zeros((0, 2))
        return np.array([a.state.ideology for a in self.agents])

    def attr_array(self, key: str, default=0) -> np.ndarray:
        return np.array([a.state.attrs.get(key, default) for a in self.agents])
