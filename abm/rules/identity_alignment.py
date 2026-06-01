"""
Identity alignment — explicit mega-identity stacking state (Mason 2018).

Step 1 (web_demo evidence re-grade, decision D3b). The engine already
*implicitly* coupled identity to affect: `IdentitySorting` differentiates
each agent's `identities` vector away from the out-party, and
`AffectiveUpdate` reads those identities into its `identity_term`. This
rule makes the stacking an **explicit per-agent state** so affect can be
driven by *alignment* directly — the "missing master mechanism" the causal
model (`docs/polarization_causal_model.md` §4.2, L4) flags.

`identity_alignment ∈ [0, 1]` measures how strongly an agent's
cross-cutting identities point in their own party's canonical identity
direction (the `party_identity_centers` sign). 0 = cross-pressured /
unaligned; 1 = fully stacked mega-identity. It **relaxes** toward the
instantaneous identity-derived target at `rate` per tick, so the state
carries inertia (Mason: mega-identities build up gradually, then bite).

`AffectiveUpdate` reads this state and amplifies out-party animus for
stacked agents (gated by `identity_alignment_affect_weight` in env.attrs).

Gating / bit-identity discipline: the rule is a strict no-op unless
`env.attrs["evidence_regrade"]` is truthy — it returns an empty delta
*before drawing any rng*, so every default-path scenario (pillar, Phase
4–9 historical default) is bit-identical with the flag off. Independents
(party=2) and party-less agents carry no alignment.

Reads:
  env.attrs["evidence_regrade"]              -- master gate (bool)
  env.attrs["party_identity_centers"]        -- {party_id: ndarray}
  agent.state.attrs["party"]
  agent.state.attrs["identities"]            -- 1D ndarray in [-1, 1]
  agent.state.attrs["identity_alignment"]    -- current scalar (optional)

Writes (delta):
  d_attrs["identity_alignment"] = rate * (target - current)   -- additive
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


class IdentityAlignment:
    def __init__(self, rate: float = 0.10):
        # Relaxation rate toward the identity-derived alignment target.
        # 0.10 ≈ a ~7-tick (~2.3 yr) adjustment timescale — slow enough
        # to lag the identity vector (mega-identities accrete), fast
        # enough to track the multi-decade sort.
        self.rate = rate

    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta:
        # Master gate — strict no-op (no rng draw) when off.
        if not env.attrs.get("evidence_regrade"):
            return StateDelta()
        party = agent.state.attrs.get("party")
        if party is None or party == 2:
            return StateDelta()
        ids = agent.state.attrs.get("identities")
        if ids is None or len(ids) == 0:
            return StateDelta()

        # Party's canonical identity direction: sign of the party-identity
        # centroid mean (party 0 seeded negative, party 1 positive in
        # historical_arc). Fall back to party parity if env lacks it.
        centers = env.attrs.get("party_identity_centers") or {}
        c = centers.get(party)
        if c is None:
            sign = 1.0 if party == 1 else -1.0
        else:
            sign = 1.0 if float(np.mean(np.asarray(c))) >= 0.0 else -1.0

        # Alignment target: mean identity projection onto the party
        # direction, clipped to [0, 1]. Negative projections (an agent
        # whose identities point the *other* way) read as fully
        # unaligned (0), not negative.
        target = float(np.clip(np.mean(np.asarray(ids, dtype=float) * sign), 0.0, 1.0))
        current = float(agent.state.attrs.get("identity_alignment", 0.0))
        delta = self.rate * (target - current)
        if delta == 0.0:
            return StateDelta()
        return StateDelta(d_attrs={"identity_alignment": delta})
