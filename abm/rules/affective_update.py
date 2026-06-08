"""
Affective update — out-party affect dynamics (Iyengar et al. 2019; Mason 2018;
Finkel et al. 2020; Pettigrew 2009 secondary-transfer).

Phase 8c §2 rewrites the rule to support **two valence channels**:

  - **Negative-going (default).** Out-party encounters produce coolness.
    The shape is unchanged from Phase 5:
        valence = -(identity_weight * identity_distance
                    + (1 - identity_weight) * issue_distance
                    + baseline)
    On every out-party encounter the agent contributes at least the
    `baseline` worth of coolness (Mason mega-identity logic).

  - **Positive-going (Phase 8c).** When the encounter is over a
    `cooperative=True` edge AND the agent's current warmth toward
    the neighbour's party is at or above `coop_positive_threshold`
    (default -0.2 — cold-but-not-extreme), valence is a small
    positive constant (`coop_positive_magnitude`, default +0.05) —
    representing warming via cooperative-conditions contact. Below
    the threshold, even on a cooperative edge, the path stays
    negative (cold agents don't warm easily — Pettigrew & Tropp
    2006). The cooperative-edge flag is the *trigger* for the
    positive path; the broader **agent-level mute** (below) handles
    the negative-path attenuation.

Phase 8c also replaces the **edge-level cooperative mute** (Phase 7)
with an **agent-level** mute (Pettigrew 2009 secondary-transfer):
each agent carries a `cooperative_share` ∈ [0, 1] attribute (default
0.0). The agent's negative valence on *every* out-party encounter
is multiplied by:

    neg_mute = 1.0 - cooperative_share * (1.0 - cooperative_mute)

so a fully-cooperative agent (`cooperative_share = 1.0`) gets
`neg_mute = cooperative_mute = 0.5` (Pettigrew & Tropp anchor),
a non-cooperative agent (`cooperative_share = 0.0`) gets
`neg_mute = 1.0` (no muting). The edge-level mute is gone — only
the cooperative-edge *flag* survives, as the positive-path trigger.

**Pillar-fallback discipline.** Agents without `cooperative_share`
read 0.0; no muting; pillar S0-S4 bit-identical to Phase 8b. The
positive-going path requires `network.is_cooperative(...)` true
and warmth above threshold; the pillar's baseline progression has
no cooperative edges, so the positive path never triggers in S0-S4
— pillar bit-identical preserved.

In-party warmth is **not** updated (Finkel et al. 2020: in-party
warmth is roughly stable, out-party animus is what moves). Adding
an in-party warmth channel is Phase 8d / backlog.

Reads:
  agent.state.attrs["party"]
  agent.state.attrs["affect"]              -- dict {other_party_id: warmth}
  agent.state.attrs["identities"]          -- ndarray (optional)
  agent.state.attrs["affect_lr"]           -- per-agent lr (optional; Phase 8b M1)
  agent.state.attrs["cooperative_share"]   -- (optional; Phase 8c §2 E3)
  neighbor.state.attrs["party"]
  neighbor.state.attrs["identities"]       -- (optional)
  env.attrs["network"]                     -- (optional; used for coop-edge check)

Writes (delta):
  d_attrs["affect"] = {other_party_id: cumulative_warmth_change}
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.network import neighbor_agents
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


class AffectiveUpdate:
    def __init__(
        self,
        radius: float = 1.5,
        learning_rate: float = 0.01,
        identity_weight: float = 0.5,
        baseline: float = 0.10,
        cooperative_mute: float = 0.5,
        coop_positive_threshold: float = -0.2,
        coop_positive_magnitude: float = 0.05,
        threat_amplification: float = 1.0,
        saturation: float = 0.0,
    ):
        # `radius` is the issue-distance normalisation scale (the
        # divisor in `d_iss / self.radius`). It is **not** a query
        # radius — neighbour iteration is network-mediated (ADR-001).
        # The name is kept for backward compatibility with every
        # scenario's `AffectiveUpdate(radius=1.5, ...)` call.
        self.radius = radius
        self.lr = learning_rate
        self.identity_weight = identity_weight
        # Per-encounter coolness floor (Phase 5 §3.2). Without it,
        # close-enough out-party neighbours could *warm* the agent —
        # contradicting the empirical record. Keep small (~0.1).
        self.baseline = baseline
        # Phase 8c §2 (replaces Phase 7 edge-level mute):
        # `cooperative_mute` is the per-encounter multiplier applied
        # to negative valence for a *fully cooperative* agent
        # (cooperative_share = 1.0). 0.5 corresponds to Pettigrew &
        # Tropp 2006's "contact halves prejudice" reading. The
        # mute is now scaled by the agent's cooperative_share at
        # apply-time; the edge-level path is gone.
        self.cooperative_mute = cooperative_mute
        # Phase 8c §2 E2: positive-going valence channel.
        # `coop_positive_threshold`: warmth above this value triggers
        # the positive-going path on a cooperative edge. Below this
        # value, even on a cooperative edge, the path stays negative
        # (Pettigrew & Tropp 2006: very cold agents don't warm easily).
        # `coop_positive_magnitude`: constant per-encounter positive
        # valence on the cooperative-positive path. +0.05 = half the
        # negative baseline floor, sign-flipped.
        self.coop_positive_threshold = coop_positive_threshold
        self.coop_positive_magnitude = coop_positive_magnitude
        # Phase 8c §5 E5.2: identity-threat amplifier on negative-going
        # valence. When the agent's `perceived_threat ∈ [0, 1]` is
        # non-zero, the negative valence is multiplied by
        # `1 + threat_amplification * perceived_threat`. Threat is
        # identity-defensive (Mutz 2018), so it amplifies *negative*
        # valence only; positive-going cooperative valence is NOT
        # amplified. `threat_amplification = 1.0` means a fully-
        # threatened agent (`perceived_threat = 1.0`) experiences
        # *double* the negative valence on every out-party encounter.
        # The pillar's S0-S4 baseline never sets `perceived_threat`,
        # so this is bit-identical to Phase 8c §4 for the pillar.
        self.threat_amplification = threat_amplification
        # Phase 9 §11.7-G — affect-saturation strength. Default 0.0 →
        # no saturation, bit-identical to pre-Phase-9. When > 0, each
        # per-encounter delta is multiplied by max(0, 1 − s · w²),
        # where w is the agent's current warmth toward the out-party
        # (after deltas already accumulated this tick). At s=1.0 the
        # cooling rate drops to zero as warmth approaches ±1, matching
        # the empirically-observed diminishing-returns shape of
        # out-party affect (Iyengar et al. 2019 fig. 1 saturation;
        # Mason 2018 ch. 6 ceiling effect). The accumulating clip at
        # ±1 still applies as the hard backstop.
        self.saturation = float(saturation)

    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta:
        if self.lr == 0:
            return StateDelta()
        agent_party = agent.state.attrs.get("party")
        # Phase 8d: Independents (party=2) are affect-neutral per Klar
        # & Krupnikov 2016 — they're not affectively engaged with
        # either party. No `affect` dict to update. Short-circuit.
        if agent_party is None or agent_party == 2:
            return StateDelta()
        neighbors = neighbor_agents(agent, space, env)
        if not neighbors:
            return StateDelta()
        # Phase 8b M1: per-agent affect_lr heterogeneity (engaged
        # partisans process out-party affect more strongly; Mason
        # 2018; Iyengar et al. 2019). Falls back to the rule's
        # `self.lr` for any scenario that doesn't seed per-agent
        # affect_lr — bit-identical to Phase 8a for the pillar.
        lr = float(agent.state.attrs.get("affect_lr", self.lr))
        if lr == 0:
            return StateDelta()

        my_ids = agent.state.attrs.get("identities")
        # Phase 8c §4 I4: X4 shared-identity prime can temporarily
        # downweight an agent's identity_distance contribution to
        # valence. The override is set by X4's setup
        # (`identity_weight_override`); the env-rule
        # `IdentityPrimeExpiry` clears it after the prime window
        # (`identity_prime_expires_at`). When the override is None
        # (default), use the rule-level `self.identity_weight`. The
        # override applies per-agent, not per-rule.
        effective_identity_weight = agent.state.attrs.get(
            "identity_weight_override"
        )
        if effective_identity_weight is None:
            effective_identity_weight = self.identity_weight
        use_ids = (
            effective_identity_weight > 0
            and my_ids is not None
            and len(my_ids) > 0
        )
        my_ids_arr = np.asarray(my_ids) if use_ids else None

        # Phase 8c §2 E3: agent-level cooperative-share mute (replaces
        # Phase 7 edge-level mute). Default 0.0 — pillar-fallback for
        # scenarios that don't seed cooperative_share. The mute is
        # applied uniformly to the agent's negative valence on EVERY
        # out-party encounter, not just cooperative-edge ones
        # (Pettigrew 2009 secondary-transfer reading).
        coop_share = float(
            np.clip(agent.state.attrs.get("cooperative_share", 0.0), 0.0, 1.0)
        )
        # Web-demo sandbox "contact / mixing" dial: an environment-level
        # cooperative-share floor (Pettigrew-Tropp secondary transfer applied
        # population-wide; read at apply-time so it covers cohort-replaced
        # agents too). Default 0.0 → no change → bit-identical for the pillar
        # and every default-path scenario.
        _contact_floor = float(env.attrs.get("sandbox_contact_share", 0.0))
        if _contact_floor > coop_share:
            coop_share = _contact_floor
        neg_mute = 1.0 - coop_share * (1.0 - self.cooperative_mute)
        # Phase 8c §5 E5.2: identity-threat amplifier. Read with
        # fallback 0.0 (pillar-fallback: pillar agents don't carry
        # `perceived_threat`; `threat_factor = 1.0` → no amplification
        # → bit-identical to §4 in the pillar).
        threat = float(
            np.clip(agent.state.attrs.get("perceived_threat", 0.0), 0.0, 1.0)
        )
        threat_factor = 1.0 + self.threat_amplification * threat
        # Phase 8e §2: party-issue coupling scales the issue_term
        # (ideological-distance) contribution to disagreement. Default
        # 1.0 (Phase 8d behaviour); historical_arc rises from 0.40 in
        # 1980 (party-as-coalition, weak coupling) to 1.10 by 2020-25.
        # Pillar bit-identity preserved at the default 1.0.
        coupling = float(env.attrs.get("party_issue_coupling", 1.0))

        # Step 1 (web_demo evidence re-grade, D3b): explicit
        # identity-alignment → affect channel (Mason 2018 mega-identity).
        # Stacked agents (high `identity_alignment`, maintained by the
        # IdentityAlignment rule) feel *more* out-party animus. Gated by
        # `identity_alignment_affect_weight` in env.attrs — default 0.0
        # → align_factor 1.0 → bit-identical for every default-path
        # scenario. Amplifies negative-going valence only (identity is
        # an animus driver, not a warmth driver), parallel to the threat
        # amplifier. Computed once per agent (it reads the agent's own
        # alignment state, not the neighbour's).
        align_w = float(env.attrs.get("identity_alignment_affect_weight", 0.0))
        if align_w > 0.0:
            a_align = float(
                np.clip(agent.state.attrs.get("identity_alignment", 0.0), 0.0, 1.0)
            )
            align_factor = 1.0 + align_w * a_align
        else:
            align_factor = 1.0

        # Phase 8c §2 E2: cooperative-positive path. The network is
        # consulted only for the positive-path trigger now; pre-Phase-8c
        # `cooperative_mute != 1.0` short-circuit is replaced by a
        # "is any agent cooperative_share > 0 OR does this scenario have
        # cooperative edges?" check that defaults conservatively to
        # fetching the network (cheap dict lookup).
        own_affect = agent.state.attrs.get("affect") or {}
        network = env.attrs.get("network")
        # Phase 8c §4 E4.3: read perceived out-party positions if the
        # agent carries `perceived_other_party`. When the agent has a
        # perception of the out-party's centroid, d_iss is computed
        # against that perceived position (so misperception amplifies
        # cooling). When the agent doesn't carry the attr (pillar
        # S0-S4: bit-identity preserved), or doesn't have an entry
        # for this specific out-party, fall back to the neighbour's
        # actual ideology — Phase 5/8b math.
        perceived = agent.state.attrs.get("perceived_other_party") or {}

        affect_delta: dict = {}
        for neighbor in neighbors:
            other_party = neighbor.state.attrs.get("party")
            # Phase 8d: skip Independent (party=2) neighbours — they're
            # not "out-party" to the partisan agent. Partisans don't
            # develop organised affect toward Independents in the
            # literature (Klar & Krupnikov 2016: affective polarization
            # is a partisan-vs-partisan phenomenon, not partisan-vs-
            # unaffiliated).
            if (
                other_party is None
                or other_party == agent_party
                or other_party == 2
            ):
                continue
            # d_iss target: perceived out-party position if available,
            # else neighbour's actual ideology (Phase 5/8b fallback).
            target_position = perceived.get(other_party)
            if target_position is None:
                target_position = neighbor.state.ideology
            d_iss = float(
                np.linalg.norm(agent.state.ideology - target_position)
            )
            # Normalise issue distance against `radius = 1.5`. Phase 8c
            # D3 clarification: on the [-1, 1]^2 compass, the max
            # ideological distance is 2*sqrt(2) ≈ 2.83, so issue_term
            # lives in roughly [0, 1.89], NOT [0, 1]. The extreme
            # corner pairs contribute additional coolness; the
            # cumulative affect is clipped by the metric reader at
            # [-1, 1], so cannot diverge. (Rescaling to a literal
            # [0, 1] is a Phase 8c backlog item.)
            issue_term = d_iss / self.radius
            if use_ids:
                their_ids = neighbor.state.attrs.get("identities")
                if their_ids is not None and len(their_ids) == len(my_ids_arr):
                    # Mean per-dimension absolute difference, rescaled
                    # to [0, 1] (identities live in [-1, 1], so |Δ|
                    # lives in [0, 2]; halving puts the mean in [0, 1]).
                    diffs = np.abs(my_ids_arr - np.asarray(their_ids))
                    identity_term = float(np.mean(diffs)) / 2.0
                else:
                    identity_term = issue_term
            else:
                identity_term = issue_term

            # Phase 8c §2 E2: positive-going path. Triggered when the
            # edge is cooperative AND the agent's current warmth is at
            # or above the cooperative-positive threshold (not too
            # cold to warm). The positive magnitude is a small constant
            # — see `coop_positive_magnitude` docstring.
            own_warmth = float(np.clip(own_affect.get(other_party, 0.0), -1.0, 1.0))
            is_coop_edge = (
                network is not None
                and network.is_cooperative(agent.id, neighbor.id)
            )
            if is_coop_edge and own_warmth >= self.coop_positive_threshold:
                valence = +self.coop_positive_magnitude
            else:
                # Negative-going path. Phase 5 sign fix preserved;
                # Phase 8c §2 applies the agent-level mute uniformly
                # (replaces Phase 7 edge-level mute). Phase 8c §4 I4
                # uses `effective_identity_weight`, which is the
                # per-agent override (X4 shared-identity prime, 0.1
                # during active prime) or the rule-level
                # `self.identity_weight` otherwise.
                # Phase 8e §2: party-issue coupling scales the
                # ideological-distance contribution. At low coupling
                # (1980 = 0.40), ideological distance contributes
                # less to out-party animus — matching the empirical
                # 1980 where parties were coalitions, not ideological
                # camps.
                disagreement = (
                    effective_identity_weight * identity_term
                    + (1.0 - effective_identity_weight) * coupling * issue_term
                )
                # Phase 8c §5 E5.2: threat amplifies negative-going
                # valence (identity-defensive — Mutz 2018). Positive
                # valence in the cooperative-edge branch above is NOT
                # amplified.
                valence = (
                    -(disagreement + self.baseline)
                    * neg_mute * threat_factor * align_factor
                )

            # Phase 9 §11.7-G — soft saturation: per-encounter delta
            # is dampened as the agent's warmth approaches ±1. Without
            # this the only floor is the metric-reader's hard clip at
            # ±1, which produces a step-function-like cooling profile
            # that over-shoots ANES affect bands at every decade. Soft
            # saturation matches the diminishing-returns shape (Iyengar
            # et al. 2019 fig. 1; Mason 2018 ch. 6).
            if self.saturation > 0.0:
                w_now = own_warmth + affect_delta.get(other_party, 0.0)
                sat = max(0.0, 1.0 - self.saturation * w_now * w_now)
                step = lr * valence * sat
            else:
                step = lr * valence
            affect_delta[other_party] = (
                affect_delta.get(other_party, 0.0) + step
            )

        if not affect_delta:
            return StateDelta()
        return StateDelta(d_attrs={"affect": affect_delta})
