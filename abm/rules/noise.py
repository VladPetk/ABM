"""
Gaussian noise — small random ideological drift each tick.

Keeps the system from freezing at brittle equilibria and models the fact
that real opinion shifts aren't purely driven by social pressure.

Phase 4 (F1, Friedkin-Johnsen anchoring): this rule also carries the
anchor pull. The FJ recurrence wants the anchor term applied once per
tick regardless of how many other rules fire; pinning it to
``GaussianNoise`` — which is on in every pillar stage including S0 —
keeps it order-independent. Agents without a ``stubbornness`` attr or
without an ``anchor`` attr (every existing non-pillar scenario) bypass
the FJ logic entirely, so canonical / ACTB / compass behaviour is
unchanged.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


class GaussianNoise:
    def __init__(self, sigma: float = 0.01):
        self.sigma = sigma

    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta:
        s = float(agent.state.attrs.get("stubbornness", 0.0))
        anchor = agent.state.attrs.get("anchor")
        # Phase 8b M1: per-agent fj_alpha heterogeneity (engaged
        # partisans more anchored; Achen & Bartels 2016). Falls back
        # to env-level fj_alpha if per-agent not set — bit-identical
        # to Phase 8a for the pillar.
        alpha = float(agent.state.attrs.get(
            "fj_alpha", env.attrs.get("fj_alpha", 0.0)
        ))
        fj_active = s > 0.0 and anchor is not None and alpha > 0.0

        if self.sigma <= 0:
            if not fj_active:
                return StateDelta()
            # Anchor pull still fires even when noise is off — F1 is
            # structural, not noise-coupled.
            return StateDelta(
                d_ideology=alpha * s * (anchor - agent.state.ideology)
            )

        noise = rng.normal(0.0, self.sigma, size=2)
        if not fj_active:
            return StateDelta(d_ideology=noise)
        # Brownian motion scales with mobility (1 - s); anchor pull adds
        # to it. Stubborn agents jitter less and decay toward their
        # innate position.
        return StateDelta(
            d_ideology=(1.0 - s) * noise + alpha * s * (anchor - agent.state.ideology)
        )
