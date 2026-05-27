"""
ResidentialMigration — Bishop's Big Sort (Phase 8b M2).

Each tick, each agent with probability ``migration_rate`` shifts its
``social_coord`` toward the in-party mean social_coord, with an
"inadvertent" random component representing the ~70% lifestyle-
correlated share Brown & Enos 2021 document (Bishop 2008 *The Big
Sort* + Brown & Enos 2021 *Nature Human Behaviour* — precinct-level
partisan-exposure measurements).

``intentional_share`` mixes the two channels:
  intentional × (in_party_mean - current_social_coord)
  + (1 - intentional) × N(0, max_step)

Net shift clipped to ±``max_step`` per tick. social_coord stays in
[-1, 1].

This is an ``EnvRule`` — it mutates per-agent state (the
social_coord attr) once per tick using a single pass.

**Pillar invariant**: ``migration_rate = 0`` is an exact no-op (the
rule returns immediately). The pillar runs with social_coord fixed
forever (Phase 3 design intent — social_coord as the ratchet
anchor). Only the historical scenario activates migration.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D


class ResidentialMigration:
    def __init__(
        self,
        migration_rate: float = 0.0,
        intentional_share: float = 0.30,
        max_step: float = 0.05,
    ):
        self.migration_rate = migration_rate
        # Brown & Enos 2021: ~30% of geographic sorting is intentional
        # partisan; ~70% is inadvertent lifestyle correlation.
        self.intentional_share = intentional_share
        # Per-tick cap on social_coord shift, keeps migration gradual.
        self.max_step = max_step

    def apply(
        self,
        env: Environment,
        agents: list[Agent],
        space: ContinuousSpace2D,
        rng: np.random.Generator,
        tick: int,
    ) -> None:
        if self.migration_rate <= 0:
            return
        # Compute per-party social_coord means once per tick.
        by_party: dict[object, list[float]] = {}
        for a in agents:
            party = a.state.attrs.get("party")
            if party is None:
                continue
            sc = a.state.attrs.get("social_coord")
            if sc is None:
                continue
            by_party.setdefault(party, []).append(float(sc))
        if not by_party:
            return
        by_party_mean = {p: float(np.mean(v)) for p, v in by_party.items()}

        # Per-agent migration.
        for a in agents:
            if rng.random() > self.migration_rate:
                continue
            party = a.state.attrs.get("party")
            if party not in by_party_mean:
                continue
            target = by_party_mean[party]
            current = float(a.state.attrs.get("social_coord", 0.0))
            # Intentional pull toward in-party mean.
            intentional = self.intentional_share * (target - current)
            # Inadvertent random component (lifestyle correlation
            # noise) — Brown & Enos's ~70% share.
            inadvertent = (1.0 - self.intentional_share) * float(
                rng.normal(0.0, self.max_step)
            )
            step = float(np.clip(
                intentional + inadvertent,
                -self.max_step, self.max_step,
            ))
            new = float(np.clip(current + step, -1.0, 1.0))
            a.state.attrs["social_coord"] = new
