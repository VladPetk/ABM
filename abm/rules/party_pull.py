"""
Party pull — plural elite-cue mechanism (Hetherington 2001; Levendusky
2009; Mason 2018; Bawn et al. 2012).

Each agent drifts toward its **personal `party_cue`** — the specific
elite / sub-group / leader they identify with — with magnitude
modulated by `identity_strength`. The cue is fixed at build time
from `N(party_centroid, σ²)` (Phase 8a F'). Different agents within
the same party follow different cues.

**§11 measure-then-bless outcome (Phase 8a):** the spec predicted F'
would lift within-party SD at S2-end from ~0.14 (Phase 7) into the
[0.20, 0.35] band — between DW-NOMINATE legislators and ANES voters.
Measurement at σ=0.25 produced ~0.155 — inside the DW-NOMINATE
legislator band (~0.15-0.20) but **below** the ANES voter band
(~0.33-0.47). Cause: `BoundedConfidenceInfluence`'s network-mediated
pull toward the local mean partially cancels per-agent cue dispersion.
Even at the spec's cushion ceiling σ=0.35 the SD only reaches ~0.17.
The S3/S4 over-tightness is mostly `MediaConsumption`-driven, which
Phase 8a deliberately left out of scope (P-Scope=PartyPull-only). The
honest reading: F' is a measurable but partial fix; full ANES voter
dispersion requires also dispersing `MediaConsumption`'s diet target,
which is Phase 8c+ work.

Non-pillar scenarios (`compass_basic`, `actb`, `multi_party_4`,
`two_party_sorting`, `elite_dynamics`) do not seed `party_cue`. In
that case, this rule falls back to the env-level party centroid
(`env.attrs["parties"][party_id]`), bit-identical to the pre-Phase-8a
behaviour for every existing non-pillar scenario.

Reads:
  agent.state.attrs["party"]              -- party id
  agent.state.attrs["party_cue"]          -- ndarray; falls back to centroid
  agent.state.attrs["identity_strength"]  -- [0, 1], default 0.5
  agent.state.attrs["stubbornness"]       -- [0, 1], default 0 (F1)
  env.attrs["parties"]                    -- {party_id: ndarray ideology}
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.issues import issues_of, lift
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


class PartyPull:
    def __init__(self, strength: float = 0.05):
        self.strength = strength

    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta:
        if self.strength == 0:
            return StateDelta()
        party = agent.state.attrs.get("party")
        parties = env.attrs.get("parties", {})
        if party is None or party not in parties:
            return StateDelta()
        # Phase 8a F': prefer the agent's personal cue if seeded;
        # fall back to the env-level centroid for non-pillar scenarios
        # (compass_basic, etc.) — bit-identical to pre-8a behaviour
        # for everything that doesn't set `party_cue`.
        target = agent.state.attrs.get("party_cue")
        if target is None:
            target = parties[party]
        ident = float(agent.state.attrs.get("identity_strength", 0.5))
        # Phase 8e §2: party-issue coupling — scales the per-tick pull
        # magnitude. Defaults to 1.0 (the existing Phase 8d behaviour)
        # so the pillar and any scenario without the env attr stays
        # bit-identical. Historical_arc carries a per-decade schedule
        # (PARTY_ISSUE_COUPLING_SCHEDULE), starting at 0.40 in 1980
        # (party-as-coalition, weak party-issue coupling per Mason
        # 2018's "great sort" arriving gradually post-1990) and
        # rising to 1.10 by 2020-25.
        coupling = float(env.attrs.get("party_issue_coupling", 1.0))
        stubbornness = float(agent.state.attrs.get("stubbornness", 0.0))
        # MHV S2 T2.2 — native D-dim path: the 2D cue is LIFTED
        # (block-broadcast) and each ISSUE is pulled toward the party's
        # package position. This is cue-taking made explicit at the item
        # level: elite cues bundle issues, which is exactly the
        # party_pull → constraint catalysis the S1 pilot measured. At
        # D=2 lift is the identity and the arithmetic matches the 2D
        # path bit-for-bit.
        from ..core.issues import issues_of, lift
        v = issues_of(agent, env)
        if v is not None:
            tgt = lift(np.asarray(target, dtype=float), env.attrs["issue_runtime"])
            d = self.strength * coupling * ident * (tgt - v)
            return StateDelta(d_attrs={"issues": (1.0 - stubbornness) * d})
        d = self.strength * coupling * ident * (target - agent.state.ideology)
        # F1: Friedkin-Johnsen scaling — stubborn agents move less.
        return StateDelta(d_ideology=(1.0 - stubbornness) * d)
