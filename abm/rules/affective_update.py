"""
Affective update — out-party animus dynamics (Iyengar et al. 2019; Mason 2018;
Finkel et al. 2020), corrected in Phase 5.

For each out-party network neighbour, the agent's affect toward that
party updates with a **negative-going valence**:

    valence = -(identity_weight * identity_distance
                + (1 - identity_weight) * issue_distance
                + baseline)

So every out-party encounter contributes at least the `baseline` worth of
coolness (the Mason mega-identity logic — any out-party encounter is a
salience event for partisan identity), with additional coolness scaled by
how far the neighbour is on issue and identity dimensions.

Phase 5 fixes the sign issue of the prior `1 - 2d/radius` formula, which
*warmed* agents toward near out-party neighbours (the opposite of
Iyengar's headline). The new dynamic produces monotonically-decreasing
out-party warmth through the S2-S4 progression — the operational mirror
of "out-party thermometer scores fell from ~48° to ~20° since the 1970s"
(Finkel et al. 2020).

In-party warmth is **not** updated — Finkel et al. 2020: in-party warmth
is roughly stable, out-party animus is what moves. Adding a symmetric
in-party term is a Phase 7+ option.

Reads:
  agent.state.attrs["party"]
  agent.state.attrs["affect"]       -- dict {other_party_id: warmth}
  agent.state.attrs["identities"]   -- ndarray (optional)
  neighbor.state.attrs["party"]
  neighbor.state.attrs["identities"] (optional)

Writes (delta):
  d_attrs["affect"] = {other_party_id: cumulative_warmth_change}  (negative-going)
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
        # Phase 7: Allport-conditions multiplier. Out-party encounters
        # over `network.is_cooperative` edges produce attenuated
        # negative valence — `valence *= cooperative_mute`. Default
        # 0.5 corresponds to Pettigrew & Tropp 2006's meta-analytic
        # "contact under cooperative conditions halves prejudice
        # formation rate" reading. 1.0 = no muting (legacy Phase 5
        # behaviour); 0.0 = perfect cooperation produces no animus.
        self.cooperative_mute = cooperative_mute

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
        if agent_party is None:
            return StateDelta()
        neighbors = neighbor_agents(agent, space, env)
        if not neighbors:
            return StateDelta()

        my_ids = agent.state.attrs.get("identities")
        use_ids = (
            self.identity_weight > 0
            and my_ids is not None
            and len(my_ids) > 0
        )
        my_ids_arr = np.asarray(my_ids) if use_ids else None

        # Phase 7: only fetch the network if cooperative muting is in
        # play. With cooperative_mute = 1.0 (no muting) the lookup is
        # skipped — keeps Phase 5 behaviour bit-identical for non-X6 runs.
        network = env.attrs.get("network") if self.cooperative_mute != 1.0 else None

        affect_delta: dict = {}
        for neighbor in neighbors:
            other_party = neighbor.state.attrs.get("party")
            if other_party is None or other_party == agent_party:
                continue
            d_iss = float(
                np.linalg.norm(agent.state.ideology - neighbor.state.ideology)
            )
            # Normalise issue distance into roughly [0, 1] — the most
            # extreme corner pairs can exceed 1, contributing additional
            # coolness; the cumulative affect is clipped by the metric
            # reader so cannot diverge.
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

            disagreement = (
                self.identity_weight * identity_term
                + (1.0 - self.identity_weight) * issue_term
            )
            # Negative-going valence: every out-party encounter
            # contributes at least `baseline` coolness, plus more for
            # disagreement on either axis. Sign fix vs. the pre-Phase-5
            # rule, which emitted positive valence for close encounters.
            valence = -(disagreement + self.baseline)
            # Phase 7: contact via a cooperative-conditions edge
            # (Allport-conditions institutional contact, set by X6's
            # setup) produces attenuated coolness. The multiplier
            # `cooperative_mute` is calibrated to Pettigrew & Tropp
            # 2006's "contact halves prejudice" finding.
            if network is not None and network.is_cooperative(
                agent.id, neighbor.id
            ):
                valence *= self.cooperative_mute
            affect_delta[other_party] = (
                affect_delta.get(other_party, 0.0) + self.lr * valence
            )

        if not affect_delta:
            return StateDelta()
        return StateDelta(d_attrs={"affect": affect_delta})
