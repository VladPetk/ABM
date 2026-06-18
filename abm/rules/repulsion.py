"""
Affect-gated backlash repulsion — the Bail 2018 backfire mechanism.

For each out-party network neighbour, the agent's affect toward that
party is checked: if warmth < ``affect_threshold`` (default ``-0.3``),
the encounter contributes a push **away** from the neighbour. Push
magnitude scales linearly with the absolute warmth (`(-warmth)`, clipped)
and with the existing inverse-square ring profile in
``[epsilon, max_range]``. Above the threshold (warm or neutral), no
backfire fires.

This is the **honest model of backfire**: it fires conditionally on
existing animus (Bail et al. 2018 *PNAS* 115:9216), not universally
on every cross-party encounter (the pre-Phase-6 Macy-Flache 1997 form,
which the empirical record does not support — Guess et al. 2023, Nyhan
et al. 2023 find null average effects of cross-cutting exposure;
Levendusky 2021 finds *positive* effects under warm framing). In-party
neighbours never contribute backlash — the mechanism is identity-threat-
driven and only fires across party.

Combines with Phase 4 F1 (Friedkin-Johnsen stubbornness scaling at the
apply site) and Phase 5 A1 (affect attribute being the agent's stored
warmth, capped only by the metric read).

``strength = 0`` is an exact no-op (the rule returns immediately) — the
pillar's baseline progression S0-S4 carries the rule at strength 0;
Phase 6 interventions turn it on.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.issues import issues_of, rms_distance
from ..core.network import neighbor_agents
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


class BacklashRepulsion:
    def __init__(
        self,
        epsilon: float = 0.3,
        max_range: float = 1.5,
        strength: float = 0.05,
        affect_threshold: float = -0.3,
        threat_amplification: float = 1.0,
        asymmetric: dict[int, float] | None = None,
        threat_gated: bool = False,
    ):
        self.epsilon = epsilon
        self.max_range = max_range
        self.strength = strength
        # Phase 6 R1: out-party neighbours only contribute backlash when
        # the agent's warmth toward their party is below this threshold.
        # Default -0.3 means "noticeably cold but not extreme."
        # +inf disables the gate (every out-party encounter triggers
        # backlash — the pre-Phase-6 Macy-Flache form); -inf disables
        # backlash entirely.
        self.affect_threshold = affect_threshold
        # Phase 8c §5 E5.3: identity-threat amplifier on push
        # magnitude. When `perceived_threat ∈ [0, 1]` is non-zero,
        # the push is multiplied by `1 + threat_amplification *
        # perceived_threat`. Pillar agents don't carry the attr →
        # `threat_factor = 1.0` → bit-identical to Phase 8c §4
        # behaviour. Same default amplification (1.0) as
        # `AffectiveUpdate`: doubles push at full threat.
        self.threat_amplification = threat_amplification
        # Phase 8c §6 E6.1: per-party asymmetric multiplier on push
        # magnitude. When None (the pillar default), every agent gets
        # multiplier 1.0 — bit-identical to §5 behaviour. When set
        # (e.g. {0: 0.7, 1: 1.3} per Vlad's Fork 6-A confirm, a 1.86×
        # ratio), each agent's push is multiplied by
        # asymmetric.get(agent.party, 1.0). The historical-arc scenario
        # opts in via `{0: 0.7, 1: 1.3}` (Bail 2018: Republican users
        # more susceptible to cross-cutting backfire); X1 setup sets
        # the same asymmetric dict on the rule when it fires.
        self.asymmetric = asymmetric
        # R-phase R-D — threat-GATED backfire (opt-in; default False →
        # bit-identical, so the pillar backlash tests and every default path are
        # unchanged). The warmth gate (`affect_threshold`) is effectively
        # unconditional in the polarized era (~95% of partisans sit below −0.3),
        # so the backfire fired near-universally — which cannot express the
        # CONDITIONAL, threat-moderated backfire the literature debates (Mutz
        # 2018: status threat is the *carrier*; Combs 2023: anonymous exposure
        # with no identity threat *helps*; Guess & Coppock 2020: null on average).
        # When True, the push is scaled by `threat_amplification × perceived_threat`
        # instead of `1 + threat_amplification × perceived_threat`, so it is ZERO
        # for unthreatened agents and fires only for the threatened subset (the
        # engine's post-2016 status-threat population). X1 opts in.
        self.threat_gated = bool(threat_gated)

    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta:
        if self.strength == 0:
            return StateDelta()
        # Phase 8d: Independents (party=2) have no in-party identity
        # threat to defend → no backlash. Short-circuit before
        # neighbour iteration.
        own_party_early = agent.state.attrs.get("party")
        if own_party_early is None or own_party_early == 2:
            return StateDelta()
        neighbours = neighbor_agents(agent, space, env)
        if not neighbours:
            return StateDelta()

        own_party = agent.state.attrs.get("party")
        own_affect = agent.state.attrs.get("affect") or {}
        # MHV S2 T2.2 — native D-dim path: the repulsion ring test uses
        # the RMS distance and the push acts on the full issue vectors.
        # At D=2 both equal the 2D arithmetic bit-for-bit.
        my_v = issues_of(agent, env)
        push = np.zeros(2 if my_v is None else len(my_v))
        count = 0
        for n in neighbours:
            other = n.state.attrs.get("party")
            # In-party neighbours and party-less agents never contribute
            # to backlash — Bail's mechanism is identity-threat driven.
            # Phase 8d: also skip Independent (party=2) neighbours —
            # they're not "out-party" and don't trigger identity-threat
            # backlash for partisan agents.
            if other is None or other == own_party or other == 2:
                continue
            warmth = float(np.clip(own_affect.get(other, 0.0), -1.0, 1.0))
            if warmth >= self.affect_threshold:
                # Not hot enough — no backfire from this encounter.
                continue
            if my_v is not None:
                diff = my_v - n.state.attrs["issues"]
                d = float(rms_distance(my_v, n.state.attrs["issues"]))
            else:
                diff = agent.state.ideology - n.state.ideology
                d = float(np.linalg.norm(diff))
            # Keep the [epsilon, max_range] ring semantics — too-close =
            # below ideological-distance threshold; too-far = no
            # meaningful exposure (Macy-Flache).
            if d <= self.epsilon or d > self.max_range or d < 1e-9:
                continue
            # Linear scaling in (-warmth): a -1 (clip floor) agent
            # pushes at full inverse-square strength; a -0.3 (just past
            # threshold) agent pushes at 30%.
            magnitude = (-warmth) / (d * d)
            push += magnitude * diff
            count += 1

        if count == 0:
            return StateDelta()
        # Phase 8c §5 E5.3: threat amplifies push magnitude. Pillar
        # agents read `perceived_threat = 0.0` (no attr) → factor 1.0
        # → bit-identical to §4 behaviour. Historical-arc agents with
        # post-2016 threat amplify their backlash push.
        threat = float(
            np.clip(agent.state.attrs.get("perceived_threat", 0.0), 0.0, 1.0)
        )
        # R-phase R-D: threat-gated → push ∝ threat (zero for unthreatened
        # agents, conditional backfire). Default → the additive amplifier
        # (bit-identical to every pre-R-D path).
        if self.threat_gated:
            threat_factor = self.threat_amplification * threat
        else:
            threat_factor = 1.0 + self.threat_amplification * threat
        # Phase 8c §6 E6.1: per-party asymmetric multiplier. Pillar
        # default (None) → factor 1.0 → bit-identical to §5.
        if self.asymmetric is not None:
            asym_factor = float(self.asymmetric.get(own_party, 1.0))
        else:
            asym_factor = 1.0
        d = self.strength * threat_factor * asym_factor * push / count
        # F1: Friedkin-Johnsen scaling — stubborn agents move less.
        s = float(agent.state.attrs.get("stubbornness", 0.0))
        if my_v is not None:
            return StateDelta(d_attrs={"issues": (1.0 - s) * d})
        return StateDelta(d_ideology=(1.0 - s) * d)
