"""
Measured identity alignment — MHV S2 T2.4 (M3-light).

Replaces the `IdentityAlignment` relaxation rule on the emergent-constraint
path. `identity_alignment` is no longer a relaxed/scheduled stock; it is a
MEASURED per-agent readout of current state (review_polisci.md §2.2 / §A4:
the alignment trio — the relaxation rule, AffectiveUpdate's `align_factor`,
and `MediatedAnimus`'s multiplier — was one signal applied three times, with
the signal itself ~83% schedule-carried). After T2.4 the signal is computed
from state each tick and can only rise through real state movement: issue
positions sorting onto the party axis (PartyPull / BC / ConstraintOp) and
generational turnover. Downstream consumers (`MediatedAnimus`,
AffectiveUpdate's `align_factor`) read the same attr name, unchanged.

The exact formula (pinned by tests/test_t24_measured_alignment.py):

    id_stack    = clip( sign_p * mean(identities), 0, 1 )
    issue_stack = clip( p * ((v - m) @ u), 0, 1 )
    identity_alignment = sqrt( id_stack * issue_stack )

where
  - `sign_p` is the party's canonical identity direction (the
    `party_identity_centers` sign — same convention the legacy rule and the
    build-time seeding used),
  - `p` = +1 for party 1 (Rep), -1 for party 0 (Dem),
  - `u`, `m` are the FROZEN 1986 party-gap axis and midpoint over the issue
    items (`issue_runtime["align_u"/"align_m"]`, computed once from the
    committed loadings file — measured data, never re-fit from the running
    population),
  - `v` is the agent's issue vector.

Geometric mean of the two stackings: the Mason (2018) mega-identity
construct is identity AND issue-package both pointing at the same party
pole — an agent is "stacked" only when both hold. Each factor alone
reproduces a familiar quantity (id_stack is exactly the legacy seeding
formula; issue_stack is the projection onto the empirical party axis), and
the geometric mean keeps the readout in [0, 1] on the same magnitude scale
the consumers were tuned against.

Mechanics: the rule emits `d_attrs["identity_alignment"] = measured -
current` through the ordinary delta pipeline (I3: no outcome writes outside
deltas), so the attr equals the measurement of the previous agent-phase
snapshot — a one-tick lag, vs the ~7-tick lag of the retired relaxation.

No-op gates (before any computation): missing issue runtime, degenerate
party-gap axis (the D=2 identity loadings have dem == rep means → no
empirical axis → the readout is OFF and the attr stays unseeded),
Independents / party-less agents (they carry no alignment, as before).
Never draws rng.

Reads:
  env.attrs["issue_runtime"]            -- align_u / align_m (frozen)
  env.attrs["party_identity_centers"]   -- {party_id: ndarray}
  agent.state.attrs["party" / "identities" / "issues" / "identity_alignment"]

Writes (delta):
  d_attrs["identity_alignment"] = measured - current
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


def measure_alignment(identities, party, issues, party_identity_centers,
                      rt) -> float | None:
    """The T2.4 measured-alignment formula (module-level so the build-time
    seeding, the cohort-replacement reseed, and the tests compute the exact
    same number). Returns None when the readout is undefined (no empirical
    party-gap axis, non-partisan, or missing state)."""
    u = rt.get("align_u")
    if u is None or party not in (0, 1):
        return None
    if identities is None or len(identities) == 0 or issues is None:
        return None
    c = (party_identity_centers or {}).get(party)
    if c is None:
        sign_p = 1.0 if party == 1 else -1.0
    else:
        sign_p = 1.0 if float(np.mean(np.asarray(c))) >= 0.0 else -1.0
    id_stack = float(np.clip(
        sign_p * float(np.mean(np.asarray(identities, dtype=float))),
        0.0, 1.0))
    p = 1.0 if party == 1 else -1.0
    v = np.asarray(issues, dtype=float)
    issue_stack = float(np.clip(
        p * float((v - rt["align_m"]) @ u), 0.0, 1.0))
    return float(np.sqrt(id_stack * issue_stack))


class MeasuredAlignment:
    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta:
        rt = env.attrs.get("issue_runtime")
        if rt is None:
            return StateDelta()
        measured = measure_alignment(
            agent.state.attrs.get("identities"),
            agent.state.attrs.get("party"),
            agent.state.attrs.get("issues"),
            env.attrs.get("party_identity_centers"),
            rt,
        )
        if measured is None:
            return StateDelta()
        delta = measured - float(
            agent.state.attrs.get("identity_alignment", 0.0))
        if delta == 0.0:
            return StateDelta()
        return StateDelta(d_attrs={"identity_alignment": delta})
