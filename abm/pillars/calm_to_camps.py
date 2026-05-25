"""'Calm to camps' — the reference pillar.

Five-stage progression:
  S0 Baseline -> S1 Bounded confidence -> S2 Party identity ->
  S3 Partisan media -> S4 Homophilous social network

Phase 1 wires the **full superset** population, env and rule pipeline,
and ships only the S0 and S1 Interventions. S2-S4 will arrive as new
`Intervention` objects without changing the builder. Every later
mechanism is constructed at strength 0 so it is an exact no-op.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.engine import Engine
from ..core.environment import Environment
from ..core.network import generate_homophilous_network
from ..core.outlets import US_MEDIA_OUTLETS_2024, diet_for_party
from ..core.rules import RulePipeline
from ..core.space import ContinuousSpace2D
from ..core.state import AgentState
from ..rules.affective_update import AffectiveUpdate
from ..rules.elite_drift import EliteDrift
from ..rules.identity_sorting import IdentitySorting
from ..rules.influence import BoundedConfidenceInfluence
from ..rules.media_consumption import MediaConsumption
from ..rules.noise import GaussianNoise
from ..rules.party_pull import PartyPull
from ..rules.tie_rewiring import TieRewiring
from .intervention import Intervention
from .pillar import Pillar


TITLE = "Calm to camps"

PARTY_CENTERS = {
    0: np.array([-0.5, 0.0]),
    1: np.array([0.5, 0.0]),
}
PARTY_NAMES = {0: "Left Party", 1: "Right Party"}
PARTY_COLORS = {0: "#1f3565", 1: "#8b2530"}

# Phase 3 §3: latent social position. Partly party-correlated, partly random;
# never updated by any rule (it is the anchor that lets the tie network ratchet).
SOCIAL_BIAS = 0.30
SOCIAL_NOISE = 0.30

# Phase 3 §4: homophilous network generator parameters. Calibrated so mean
# degree lands in 6-10 at the n_agents the pillar typically runs at.
NET_TAU = 0.40
NET_P_LOCAL = 0.35
NET_P_BRIDGE = 0.002


def build_engine(seed: int = 0, n_agents: int = 400) -> Engine:
    """Construct the superset engine with every pillar mechanism present
    but every force off. Applying an Intervention's bundle turns on the
    stages that are in scope.
    """
    rng = np.random.default_rng(seed)

    outlets = list(US_MEDIA_OUTLETS_2024)
    outlets_by_id = {o.id: o for o in outlets}

    n_identities = 3
    identity_bias = 0.3
    party_identity_centers = {
        0: -identity_bias * np.ones(n_identities),
        1: +identity_bias * np.ones(n_identities),
    }

    agents: list[Agent] = []
    for i in range(n_agents):
        pos = rng.uniform(-1.0, 1.0, size=2)
        party = 0 if pos[0] < 0 else 1
        diet = diet_for_party(PARTY_CENTERS[party], outlets, rng)
        identities = np.clip(
            party_identity_centers[party] + rng.normal(0, 0.3, size=n_identities),
            -1.0,
            1.0,
        )
        attrs = {
            "group": party,
            "party": party,
            "identity_strength": float(rng.beta(2, 2)),
            "identities": identities,
            "affect": {1 - party: 0.0},
            "media_diet": diet,
            "cohort": "all",
            "origin": pos.copy(),
        }
        agents.append(Agent(id=i, state=AgentState(ideology=pos, attrs=attrs)))

    # --- Phase 3: social_coord + homophilous tie network -----------------
    # Built with a SEPARATE RNG stream (spec E1) so the main build stream is
    # untouched and S0-S3 populations stay bit-identical to Phase 1/2.
    net_rng = np.random.default_rng(seed + 9973)
    for a in agents:
        sign = -1.0 if a.state.attrs["party"] == 0 else 1.0
        a.state.attrs["social_coord"] = float(
            np.clip(
                sign * SOCIAL_BIAS + net_rng.normal(0.0, SOCIAL_NOISE),
                -1.0,
                1.0,
            )
        )
    network = generate_homophilous_network(
        agents,
        net_rng,
        tau=NET_TAU,
        p_local=NET_P_LOCAL,
        p_bridge=NET_P_BRIDGE,
    )

    party_centers = {pid: c.copy() for pid, c in PARTY_CENTERS.items()}
    env = Environment(
        attrs={
            "parties": party_centers,
            "outlets": outlets_by_id,
            "network": network,
            "viz": {
                "title": TITLE,
                "group_names": PARTY_NAMES,
                "group_colors": PARTY_COLORS,
                "show_parties": True,
                "party_centers": party_centers,
                "show_last_event": True,
                "outlets": [
                    {
                        "id": o.id,
                        "name": o.name,
                        "position": [float(o.position[0]), float(o.position[1])],
                        "color": o.color,
                    }
                    for o in outlets
                ],
            },
        }
    )
    space = ContinuousSpace2D(bounds=((-1.0, 1.0), (-1.0, 1.0)))

    rules = [
        # cross_tie_weight=1.0 keeps the BC rule on its fast (plain-mean) path
        # for S0-S3; S4's bundle flips it low to engage the exposure gate.
        BoundedConfidenceInfluence(epsilon=0.30, strength=0.0, cross_tie_weight=1.0),
        PartyPull(strength=0.0),
        MediaConsumption(strength=0.0),
        AffectiveUpdate(radius=1.5, learning_rate=0.0, identity_weight=0.5),
        IdentitySorting(sort_rate=0.0, step=0.05, differentiation=0.5),
        GaussianNoise(sigma=0.01),
    ]
    # TieRewiring lives at rewire_rate=0 — an exact no-op until S4 turns it on.
    env_rules = [EliteDrift(rate=0.0), TieRewiring(rewire_rate=0.0)]

    # Enforce D6: at most one instance per class — applying a bundle by
    # class name is ambiguous otherwise.
    seen: set[str] = set()
    for r in rules + env_rules:
        name = type(r).__name__
        if name in seen:
            raise AssertionError(f"superset pipeline has two {name} instances")
        seen.add(name)

    return Engine(
        agents=agents,
        env=env,
        space=space,
        rules=RulePipeline(rules),
        env_rules=env_rules,
        seed=seed,
    )


# --- Interventions (absolute bundles, D5) ---------------------------------

S0_BASELINE = Intervention(
    id="S0_baseline",
    label="Baseline",
    description="No social forces — only small Gaussian noise.",
    label_kind="control",
    citation="",
    predicted_effect="No clustering; variance stays within the noise band.",
    param_bundle=(
        ("GaussianNoise", "sigma", 0.01),
        ("BoundedConfidenceInfluence", "strength", 0.0),
        ("PartyPull", "strength", 0.0),
        ("MediaConsumption", "strength", 0.0),
        ("AffectiveUpdate", "lr", 0.0),
        ("IdentitySorting", "sort_rate", 0.0),
        ("EliteDrift", "rate", 0.0),
        # Phase 3 E4: every bundle carries the new tunables; S0-S3 are inert.
        ("BoundedConfidenceInfluence", "cross_tie_weight", 1.0),
        ("TieRewiring", "rewire_rate", 0.0),
    ),
)

S1_BOUNDED_CONFIDENCE = Intervention(
    id="S1_bounded_confidence",
    label="Bounded confidence",
    description="Agents shift toward neighbors within ideological "
                "distance epsilon. Loose epsilon -> one consensus; tight "
                "epsilon -> fragmented clusters.",
    label_kind="replication",
    citation="Hegselmann & Krause 2002; Deffuant et al. 2000",
    predicted_effect="Population variance falls relative to baseline.",
    param_bundle=(
        ("GaussianNoise", "sigma", 0.01),
        ("BoundedConfidenceInfluence", "epsilon", 0.30),
        ("BoundedConfidenceInfluence", "strength", 0.08),
        ("PartyPull", "strength", 0.0),
        ("MediaConsumption", "strength", 0.0),
        ("AffectiveUpdate", "lr", 0.0),
        ("IdentitySorting", "sort_rate", 0.0),
        ("EliteDrift", "rate", 0.0),
        ("BoundedConfidenceInfluence", "cross_tie_weight", 1.0),
        ("TieRewiring", "rewire_rate", 0.0),
    ),
)


S2_PARTY_IDENTITY = Intervention(
    id="S2_party_identity",
    label="Party identity",
    description="Agents drift toward their party's centre; party identity "
                "starts to predict issue position.",
    label_kind="illustrative",
    citation="Hetherington 2001; Levendusky 2009",
    predicted_effect="Clusters align to party centroids; ideological "
                     "constraint (party-issue correlation) rises.",
    param_bundle=(
        ("GaussianNoise", "sigma", 0.01),
        ("BoundedConfidenceInfluence", "epsilon", 0.30),
        ("BoundedConfidenceInfluence", "strength", 0.08),
        ("PartyPull", "strength", 0.04),
        ("AffectiveUpdate", "lr", 0.01),
        ("MediaConsumption", "strength", 0.0),
        ("IdentitySorting", "sort_rate", 0.0),
        ("EliteDrift", "rate", 0.0),
        ("BoundedConfidenceInfluence", "cross_tie_weight", 1.0),
        ("TieRewiring", "rewire_rate", 0.0),
    ),
)

S3_PARTISAN_MEDIA = Intervention(
    id="S3_partisan_media",
    label="Partisan media",
    description="Each agent drifts toward the outlets in its media diet; "
                "heavy partisan diets pull hardest.",
    label_kind="illustrative",
    citation="Levendusky 2013; Martin & Yurukoglu 2017",
    predicted_effect="Heavy partisan-media consumers are pushed further "
                     "from centre than light consumers.",
    param_bundle=(
        ("GaussianNoise", "sigma", 0.01),
        ("BoundedConfidenceInfluence", "epsilon", 0.30),
        ("BoundedConfidenceInfluence", "strength", 0.08),
        ("PartyPull", "strength", 0.04),
        ("AffectiveUpdate", "lr", 0.01),
        ("MediaConsumption", "strength", 0.04),
        ("IdentitySorting", "sort_rate", 0.0),
        ("EliteDrift", "rate", 0.0),
        ("BoundedConfidenceInfluence", "cross_tie_weight", 1.0),
        ("TieRewiring", "rewire_rate", 0.0),
    ),
)


S4_HOMOPHILOUS_NETWORK = Intervention(
    id="S4_homophilous_network",
    label="Homophilous network",
    description="People are influenced through a homophilous social network "
                "that rewires slowly; cross-cutting exposure narrows.",
    label_kind="illustrative",
    citation="McPherson et al. 2001; Mutz 2006; Kan, Porter & Mason 2023",
    predicted_effect="Cross-cutting ties fall and the sorted state becomes "
                     "sticky (a ratchet) — amplification, not creation.",
    param_bundle=(
        ("GaussianNoise", "sigma", 0.01),
        ("BoundedConfidenceInfluence", "epsilon", 0.30),
        ("BoundedConfidenceInfluence", "strength", 0.08),
        ("PartyPull", "strength", 0.04),
        ("AffectiveUpdate", "lr", 0.01),
        ("MediaConsumption", "strength", 0.04),
        ("IdentitySorting", "sort_rate", 0.0),
        ("EliteDrift", "rate", 0.0),
        # S4 flips the two Phase 3 tunables on (§8, §13 addendum):
        # cross_tie_weight=0.10 — soft gate. Tie neighbours pull at full
        #   weight; non-tie neighbours pull at 10%. At S4's own
        #   epsilon=0.30 the in-range non-tie count is modest, so the
        #   soft gate has bite during S4 proper. The early hard-gate
        #   calibration (0.0) was retired by the addendum because it
        #   made the ratchet near-tautological; the soft gate forces the
        #   stronger test (camps stay apart even when agents still hear
        #   the other side, attenuated).
        # rewire_rate=0.02 — the spec starting value, kept. Drives the
        #   network from 19% cross-cutting ties to ~0.2% over TICKS;
        #   modularity 0.30 -> 0.49.
        ("BoundedConfidenceInfluence", "cross_tie_weight", 0.10),
        ("TieRewiring", "rewire_rate", 0.02),
    ),
    setup=None,
)


PILLAR = Pillar(
    id="calm_to_camps",
    title=TITLE,
    build_engine=build_engine,
    interventions=(
        S0_BASELINE,
        S1_BOUNDED_CONFIDENCE,
        S2_PARTY_IDENTITY,
        S3_PARTISAN_MEDIA,
        S4_HOMOPHILOUS_NETWORK,
    ),
)
