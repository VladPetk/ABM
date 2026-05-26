"""
Multi-party scenario — 4 parties anchored at the compass corners.

Tests the institutional finding (Gidron, Adams & Horne 2020): multiparty
systems show lower average affective polarization than two-party ones,
because cross-cutting affect becomes possible (an agent can dislike one
out-party while feeling neutral toward another).

Identity sorting (Mason mega-identity) is on by default — this is the
scenario where the sorting dynamic is most interesting, since 4 parties
let identity stacks form with more variety.

Default rule pipeline:
    BoundedConfidenceInfluence
    PartyPull               (toward nearest party center)
    AffectiveUpdate         (identity-weighted)
    IdentitySorting
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


TITLE = "Multi-Party (4)"

PARTY_CENTERS = {
    0: np.array([-0.5, -0.5]),    # libertarian left
    1: np.array([0.5, -0.5]),     # libertarian right
    2: np.array([-0.5, 0.5]),     # authoritarian left
    3: np.array([0.5, 0.5]),      # authoritarian right
}
PARTY_NAMES = {
    0: "Lib Left",
    1: "Lib Right",
    2: "Auth Left",
    3: "Auth Right",
}
PARTY_COLORS = {
    0: "#1f3565",   # libertarian left  — deep navy
    1: "#553f6b",   # libertarian right — deep aubergine
    2: "#2a4a52",   # authoritarian left — deep teal
    3: "#8b2530",   # authoritarian right — deep oxblood
}


def _nearest_party(pos: np.ndarray) -> int:
    best_id, best_d = 0, float("inf")
    for pid, center in PARTY_CENTERS.items():
        d = float(np.linalg.norm(pos - center))
        if d < best_d:
            best_d, best_id = d, pid
    return best_id


def build(
    n_agents: int = 700,
    epsilon: float = 0.3,
    attraction: float = 0.05,
    party_pull: float = 0.04,
    affect_radius: float = 1.5,
    affect_lr: float = 0.01,
    n_identities: int = 3,
    sort_rate: float = 0.02,
    sort_step: float = 0.05,
    identity_weight: float = 0.5,
    identity_bias: float = 0.3,
    noise: float = 0.01,
    seed: int = 0,
) -> Engine:
    rng = np.random.default_rng(seed)
    other_parties = lambda p: [pid for pid in PARTY_CENTERS if pid != p]
    party_identity_centers = {
        pid: rng.uniform(-identity_bias, identity_bias, size=n_identities) if n_identities > 0 else None
        for pid in PARTY_CENTERS
    }

    agents: list[Agent] = []
    for i in range(n_agents):
        pos = rng.uniform(-1.0, 1.0, size=2)
        party = _nearest_party(pos)
        attrs = {
            "group": party,
            "party": party,
            "identity_strength": float(rng.beta(2, 2)),
            "affect": {pid: 0.0 for pid in other_parties(party)},
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
