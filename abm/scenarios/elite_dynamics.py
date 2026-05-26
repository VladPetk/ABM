"""
Cable news era scenario — Stage 3.1, now with per-agent media diet across
real-world outlets.

Builds on two_party_sorting and adds:

- **EliteDrift** (EnvRule): party centers drift outward each tick.
- **MediaShock** (EnvRule): periodic external events push the whole crowd.
- **MediaConsumption** (Rule): each agent drifts toward the weighted-mean
  position of the outlets in their `media_diet`. Outlets are named entities
  (Fox News, MSNBC, NYT, WSJ, Local TV) at empirical positions. Click an
  agent in the UI to see and edit their diet.

Diet at init: party-biased — agents whose party sits closer to Fox News
consume more Fox by default; the opposite for MSNBC-aligned agents.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.engine import Engine
from ..core.environment import Environment
from ..core.network import Network
from ..core.outlets import US_MEDIA_OUTLETS_2024, diet_for_party
from ..core.rules import RulePipeline
from ..core.space import ContinuousSpace2D
from ..core.state import AgentState
from ..rules.affective_update import AffectiveUpdate
from ..rules.elite_drift import EliteDrift
from ..rules.identity_sorting import IdentitySorting
from ..rules.influence import BoundedConfidenceInfluence
from ..rules.media_consumption import MediaConsumption
from ..rules.media_shock import MediaShock
from ..rules.noise import GaussianNoise
from ..rules.party_pull import PartyPull


TITLE = "Cable news era"

PARTY_CENTERS_INITIAL = {
    0: np.array([-0.3, 0.0]),
    1: np.array([0.3, 0.0]),
}
PARTY_NAMES = {0: "Left Party", 1: "Right Party"}
PARTY_COLORS = {0: "#1f3565", 1: "#8b2530"}


def build(
    n_agents: int = 600,
    epsilon: float = 0.3,
    attraction: float = 0.05,
    party_pull: float = 0.04,
    affect_radius: float = 1.5,
    affect_lr: float = 0.01,
    n_identities: int = 3,
    sort_rate: float = 0.05,
    sort_step: float = 0.1,
    identity_weight: float = 0.5,
    identity_bias: float = 0.3,
    elite_drift_rate: float = 0.0008,
    media_period: int = 120,
    media_strength: float = 0.06,
    media_consumption_strength: float = 0.04,
    noise: float = 0.01,
    seed: int = 0,
) -> Engine:
    rng = np.random.default_rng(seed)

    # Outlets — five real-world US news sources at approximate compass positions.
    outlets = list(US_MEDIA_OUTLETS_2024)
    outlets_by_id = {o.id: o for o in outlets}

    party_identity_centers = {
        0: -identity_bias * np.ones(n_identities) if n_identities > 0 else None,
        1: +identity_bias * np.ones(n_identities) if n_identities > 0 else None,
    }

    agents: list[Agent] = []
    for i in range(n_agents):
        pos = rng.uniform(-1.0, 1.0, size=2)
        party = 0 if pos[0] < 0 else 1
        diet = diet_for_party(PARTY_CENTERS_INITIAL[party], outlets, rng)
        attrs = {
            "group": party,
            "party": party,
            "identity_strength": float(rng.beta(2, 2)),
            "affect": {1 - party: 0.0},
            "media_diet": diet,
            "origin": pos.copy(),
        }
        if n_identities > 0:
            base = party_identity_centers[party]
            attrs["identities"] = np.clip(base + rng.normal(0, 0.3, size=n_identities), -1.0, 1.0)
        agents.append(Agent(id=i, state=AgentState(ideology=pos, attrs=attrs)))

    party_centers = {pid: c.copy() for pid, c in PARTY_CENTERS_INITIAL.items()}

    env = Environment(
        attrs={
            "parties": party_centers,
            "outlets": outlets_by_id,                     # rules need lookup
            # ADR-001: complete graph reproduces the pre-ADR population-wide
            # behaviour exactly for influence-rule purposes.
            "network": Network.complete(range(n_agents)),
            "viz": {
                "title": TITLE,
                "group_names": PARTY_NAMES,
                "group_colors": PARTY_COLORS,
                "show_parties": True,
                "party_centers": party_centers,
                "show_last_event": True,
                # Outlet markers + names for the frontend.
                "outlets": [
                    {"id": o.id, "name": o.name,
                     "position": [float(o.position[0]), float(o.position[1])],
                     "color": o.color}
                    for o in outlets
                ],
            },
        }
    )
    space = ContinuousSpace2D(bounds=((-1.0, 1.0), (-1.0, 1.0)))
    rules: list = [
        BoundedConfidenceInfluence(epsilon=epsilon, strength=attraction),
        PartyPull(strength=party_pull),
        MediaConsumption(strength=media_consumption_strength),
        AffectiveUpdate(
            radius=affect_radius,
            learning_rate=affect_lr,
            identity_weight=identity_weight if n_identities > 0 else 0.0,
        ),
    ]
    if n_identities > 0 and sort_rate > 0:
        rules.append(IdentitySorting(sort_rate=sort_rate, step=sort_step))
    rules.append(GaussianNoise(sigma=noise))

    env_rules = []
    if elite_drift_rate > 0:
        env_rules.append(EliteDrift(rate=elite_drift_rate))
    if media_period > 0 and media_strength > 0:
        env_rules.append(MediaShock(period=media_period, strength=media_strength))

    return Engine(
        agents=agents, env=env, space=space,
        rules=RulePipeline(rules), env_rules=env_rules, seed=seed,
    )
