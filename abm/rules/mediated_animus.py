"""
Mediated (parasocial) out-party animus — a CONTACT-INDEPENDENT affect channel.

`AffectiveUpdate` cools an agent's out-party warmth only on a *direct out-party
network encounter*. But homophilous sorting collapses cross-party ties over the
arc (out-party neighbours roughly halve 1980→2025), so the contact-gated channel
*starves* exactly when real-world animus is accelerating — producing a concave
(front-loaded) affect curve where reality is convex (flat-warm early, collapse
late). See docs/affect_bands_investigation.md.

This rule supplies the missing mechanism: out-party animus that grows via the
agent's own **aligned identity** and the **partisan-media environment**, with NO
network neighbour required. It is the well-documented parasocial channel —
people grow to loathe out-partisans they never meet, through stacked identity
and media caricature (Mason 2018 *Uncivil Agreement*; Iyengar et al. 2019).

Per tick, each partisan agent's out-party warmth changes by:

    Δ = -lr * mediated_animus_weight * identity_alignment

where:
  - `lr` is the channel magnitude (rule-level),
  - `mediated_animus_weight` ∈ env.attrs is the dated media-exposure level
    (cable/Fox → social-media adoption ramp; 0.0 default),
  - `identity_alignment` ∈ agent.attrs is the Mason mega-identity stock
    (already accelerates 0.21→0.41 over the arc).

Both `mediated_animus_weight` and `identity_alignment` rise over the arc, so the
product accelerates — convexity EMERGES from endogenous state + a dated driver,
rather than being painted on via a calendar-time learning-rate ramp.

**No saturation.** Unlike `AffectiveUpdate`, this channel deliberately does not
damp as warmth approaches the floor — its whole purpose is to keep biting once
the network has sorted and contact has starved. The metric-reader's clip at ±1
is the hard backstop.

**Off by default.** `lr = 0` OR `mediated_animus_weight = 0` (the default) make
the rule an exact no-op, so the pillar and every non-arc scenario stay
bit-identical. Independents (party=2) carry no out-party animus (Klar &
Krupnikov 2016), consistent with `AffectiveUpdate`.

Reads:
  agent.state.attrs["party"]
  agent.state.attrs["affect"]              -- dict {other_party_id: warmth}
  agent.state.attrs["identity_alignment"]  -- Mason mega-identity stock (opt; 0.0)
  env.attrs["mediated_animus_weight"]      -- dated media-exposure level (opt; 0.0)

Writes (delta):
  d_attrs["affect"] = {other_party: cooling}   -- summed with AffectiveUpdate's
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


class MediatedAnimus:
    def __init__(self, learning_rate: float = 0.0):
        self.lr = float(learning_rate)

    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta:
        if self.lr == 0.0:
            return StateDelta()
        party = agent.state.attrs.get("party")
        # Independents (party=2) / missing party: no out-party animus.
        if party is None or party == 2:
            return StateDelta()
        weight = float(env.attrs.get("mediated_animus_weight", 0.0))
        if weight <= 0.0:
            return StateDelta()
        alignment = float(
            np.clip(agent.state.attrs.get("identity_alignment", 0.0), 0.0, 1.0)
        )
        if alignment <= 0.0:
            return StateDelta()

        mag = -self.lr * weight * alignment   # negative-going (cooling)
        affect_delta: dict = {}
        own_affect = agent.state.attrs.get("affect") or {}
        for other_party in own_affect.keys():
            if other_party in (0, 1) and other_party != party:
                affect_delta[other_party] = mag
        # Binary-arc fallback: ensure the canonical out-party is covered
        # even if the agent has no affect entry yet.
        out = 1 - party if party in (0, 1) else None
        if out is not None and out not in affect_delta:
            affect_delta[out] = mag

        if not affect_delta:
            return StateDelta()
        return StateDelta(d_attrs={"affect": affect_delta})
