"""
Elite drift — party centers polarize over time.

Models the monotonic elite-polarization trend documented by McCarty,
Poole & Rosenthal (2006) via DW-NOMINATE: party leaders' positions
diverge from the political center over decades. Mass agents follow via
PartyPull, reproducing Hetherington (2001): mass partisanship rises when
elite cues become clearer.

Each tick, each party's center is pushed away from the centroid of all
party centers at a constant rate, until it hits the [-1, 1] bounds.
With 2 parties this just separates them along their initial axis; with
more parties they fan outward toward the corners.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D


class EliteDrift:
    def __init__(self, rate: float = 0.0005, asymmetric: dict[int, float] | None = None):
        """
        rate: per-tick drift magnitude
        asymmetric: optional {party_id: rate_multiplier} for asymmetric drift
                    (e.g., {0: 0.5, 1: 1.5} for one party drifting faster —
                    McCarty et al.'s "Republicans moved further right" pattern)
        """
        self.rate = rate
        self.asymmetric = asymmetric or {}

    def apply(
        self,
        env: Environment,
        agents: list[Agent],
        space: ContinuousSpace2D,
        rng: np.random.Generator,
        tick: int,
    ) -> None:
        if self.rate <= 0:
            return
        parties = env.attrs.get("parties")
        if not parties or len(parties) < 2:
            return
        positions = np.array(list(parties.values()), dtype=float)
        centroid = positions.mean(axis=0)
        # Per-party deltas (used both for env centroids and per-agent
        # party_cue propagation — Phase 8b architecture: under F',
        # PartyPull reads agent.party_cue, so an EliteDrift that
        # only moved env centroids would silently fail to propagate
        # to mass behaviour. Pillar uses rate=0 so this branch is
        # inert there).
        per_party_step: dict = {}
        for pid in list(parties.keys()):
            direction = parties[pid] - centroid
            d = float(np.linalg.norm(direction))
            if d < 1e-9:
                # Degenerate: nudge in a random direction so the rule can take hold
                direction = rng.normal(0, 1, size=2)
                d = float(np.linalg.norm(direction))
                if d < 1e-9:
                    continue
            mult = self.asymmetric.get(pid, 1.0)
            step = self.rate * mult * direction / d
            # Record the *applied* step (post-clip) so per-agent cue
            # propagation tracks what actually happened to the env
            # centroid. Without this, a saturated centroid would
            # silently leave cues drifting past where the env says
            # the party stands — a footgun under sustained drift.
            old_val = parties[pid].copy()
            parties[pid] = np.clip(old_val + step, -1.0, 1.0)
            per_party_step[pid] = parties[pid] - old_val

        # Phase 8b: propagate the per-party shift to agents' personal
        # `party_cue` attrs (under F', cues are what PartyPull reads).
        # Pillar invariant: rate=0 above short-circuits; for any
        # scenario without per-agent party_cue (compass_basic, etc.),
        # this loop is a no-op.
        for a in agents:
            cue = a.state.attrs.get("party_cue")
            if cue is None:
                continue
            party = a.state.attrs.get("party")
            if party not in per_party_step:
                continue
            a.state.attrs["party_cue"] = np.clip(
                cue + per_party_step[party], -1.0, 1.0
            )

        # Update viz hint so the dashboard rerenders party stars at new positions
        viz = env.attrs.setdefault("viz", {})
        viz["party_centers"] = parties
