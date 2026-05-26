"""
Two-party sorting scenario — Stage 2 core.

Implements the two-layer (issue + identity) agent model from the
political-polarization literature (Mason 2018 "mega-identity"; Iyengar
et al. 2019). Two parties are anchored on the economic axis; agents
inherit a party from their starting half and a heterogeneous identity
strength.

Identity-sorting (the Mason mechanism) is opt-in via `n_identities` and
`sort_rate`. With sort_rate=0 (default), identities are not tracked and
AffectiveUpdate uses pure ideological similarity — keeping the canonical
two-layer baseline. Turn it on to compare: sorted populations should show
stronger affective polarization at equal ideological distance.

Default rule pipeline:
    BoundedConfidenceInfluence
    PartyPull
    AffectiveUpdate    (identity-weighted when identities present)
    IdentitySorting    (only added when sort_rate > 0)
    GaussianNoise
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.engine import Engine
from ..core.environment import Environment
from ..core.network import Network
from ..core.rules import RulePipeline
from ..core.space import ContinuousSpace2D
from ..core.state import AgentState
from ..rules.affective_update import AffectiveUpdate
from ..rules.identity_sorting import IdentitySorting
from ..rules.influence import BoundedConfidenceInfluence
from ..rules.noise import GaussianNoise
from ..rules.party_pull import PartyPull


TITLE = "Two-Party Sorting"

PARTY_CENTERS = {
    0: np.array([-0.5, 0.0]),
    1: np.array([0.5, 0.0]),
}
PARTY_NAMES = {0: "Left Party", 1: "Right Party"}
PARTY_COLORS = {0: "#1f3565", 1: "#8b2530"}   # deep navy / deep oxblood


def build(
    n_agents: int = 600,
    epsilon: float = 0.3,
    attraction: float = 0.05,
    party_pull: float = 0.04,
    affect_radius: float = 1.5,
    affect_lr: float = 0.01,
    n_identities: int = 0,
    sort_rate: float = 0.0,
    sort_step: float = 0.05,
    identity_weight: float = 0.5,
    identity_bias: float = 0.3,
    noise: float = 0.01,
    seed: int = 0,
) -> Engine:
    rng = np.random.default_rng(seed)
    party_identity_centers = {
        0: -identity_bias * np.ones(n_identities),
        1: +identity_bias * np.ones(n_identities),
    }
    agents: list[Agent] = []
    for i in range(n_agents):
        pos = rng.uniform(-1.0, 1.0, size=2)
        party = 0 if pos[0] < 0 else 1
        attrs = {
            "group": party,
            "party": party,
            "identity_strength": float(rng.beta(2, 2)),
            "affect": {1 - party: 0.0},
            "origin": pos.copy(),
        }
        if n_identities > 0:
            base = party_identity_centers[party]
            attrs["identities"] = np.clip(base + rng.normal(0, 0.3, size=n_identities), -1.0, 1.0)
        agents.append(Agent(id=i, state=AgentState(ideology=pos, attrs=attrs)))

    env = Environment(
        attrs={
            "parties": PARTY_CENTERS,
            # ADR-001: complete-graph network reproduces the prior
            # population-wide influence behaviour.
            "network": Network.complete(range(n_agents)),
            "viz": {
                "title": TITLE,
                "group_names": PARTY_NAMES,
                "group_colors": PARTY_COLORS,
                "show_parties": True,
                "party_centers": PARTY_CENTERS,
            },
        }
    )
    space = ContinuousSpace2D(bounds=((-1.0, 1.0), (-1.0, 1.0)))
    rules: list = [
        BoundedConfidenceInfluence(epsilon=epsilon, strength=attraction),
        PartyPull(strength=party_pull),
        AffectiveUpdate(
            radius=affect_radius,
            learning_rate=affect_lr,
            identity_weight=identity_weight if n_identities > 0 else 0.0,
        ),
    ]
    if n_identities > 0 and sort_rate > 0:
        rules.append(IdentitySorting(sort_rate=sort_rate, step=sort_step))
    rules.append(GaussianNoise(sigma=noise))
    return Engine(agents=agents, env=env, space=space, rules=RulePipeline(rules), seed=seed)
