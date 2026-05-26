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
from ..core.network import Network, generate_involuntary_edges
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
from ..rules.repulsion import BacklashRepulsion
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

# Phase 4 — realism core.
# F1 (Friedkin-Johnsen anchoring): each agent carries a fixed `anchor`
# (= initial ideology) and `stubbornness` ~ Beta(2, 5). Every ideology-
# moving rule multiplies its delta by (1 - stubbornness); `GaussianNoise`
# additionally pulls toward `anchor` at rate `FJ_ALPHA * stubbornness`.
STUBBORNNESS_ALPHA = 2.0
STUBBORNNESS_BETA = 5.0
FJ_ALPHA = 0.05
# F2 (graded confidence filter, pillar-only opt-in): the rule defaults to
# 0.0 (hard cutoff = canonical Hegselmann-Krause) so `compass_basic` and
# the canonical replication tests are unchanged. The pillar uses 0.05.
BC_TEMPERATURE = 0.05
# F3 (involuntary cross-cutting tie stratum): per-agent target count of
# kin/workplace ties that cross party by construction and never rewire.
# Pinned to Mutz (2006)'s ~20% total cross-cutting-tie target via the §13
# measure-then-bless gate. The first calibration at per_agent=2 put t=0
# cross-cutting at 0.39 (above the 0.30 ceiling); dropped to 1 per the
# spec's adjustment rule. Measured t=0 cross-cutting at per_agent=1 lands
# in band (see §13 calibration report).
INVOLUNTARY_PER_AGENT = 1

# Phase 5 — affect as a first-class channel.
# A1 (AffectiveUpdate dynamics): per-encounter coolness baseline and the
# issue-vs-identity blend weight. AffectiveUpdate.lr stays on the bundle.
AFFECT_BASELINE = 0.10
AFFECT_IDENTITY_WEIGHT = 0.5
# A4 (BC affect modulator) and A5 (TR affect-aware drop): the pillar
# opt-in values. Both rules default to 0.0 — the pillar wires them on at
# S2+. Vlad pinned A4 at 0.3 (milder than the spec's draft 0.5) so the
# affect→sorting nudge is real without the cliff behaviour Phase 4
# removed; A5 stays at 0.30 per the spec default.
BC_AFFECT_WEIGHT = 0.3
TR_AFFECT_WEIGHT_REWIRE = 0.30

# Phase 6 — repulsion + null levers.
# R1 (affect-gated BacklashRepulsion): out-party encounters only convert
# to push-away when the agent's warmth is below this threshold. The
# pillar's S0-S4 carry the rule at strength 0; Phase 6 interventions
# turn it on (X1 "Show people the other side" sets strength=0.05).
BACKLASH_AFFECT_THRESHOLD = -0.3

# Phase 7 — cooperative-conditions abstraction.
# AffectiveUpdate's valence on an out-party encounter is multiplied by
# this factor when the edge is tagged `cooperative=True` on the
# network. Represents Allport (1954) conditions (equal status,
# cooperative task, institutional support) that distinguish
# prejudice-reducing contact from ordinary cross-party encounters.
# Default 0.5 = "half-strength animus formation" — anchored to
# Pettigrew & Tropp (2006) JPSP 90:751 meta-analytic finding that
# contact under Allport conditions roughly halves prejudice (r ≈ -0.21
# across 515 studies — translated to a "halving" valence multiplier).
# The F3 baseline involuntary edges (kin/workplace) are NOT cooperative
# by default — the literature is explicit that contact alone is
# insufficient; only X6's added edges carry the cooperative tag.
COOPERATIVE_MUTE = 0.5


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
            # F1: Friedkin-Johnsen anchor (= where you started) and
            # stubbornness ~ Beta(2, 5) — most agents barely move, a thin
            # tail of free movers. Drawn from the main RNG stream.
            "anchor": pos.copy(),
            "stubbornness": float(
                rng.beta(STUBBORNNESS_ALPHA, STUBBORNNESS_BETA)
            ),
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
    network = Network.homophilous(
        agents,
        net_rng,
        tau=NET_TAU,
        p_local=NET_P_LOCAL,
        p_bridge=NET_P_BRIDGE,
    )
    # F3 (Phase 4): add a cross-party involuntary-tie stratum (kin /
    # workplace — Mutz & Mondak 2006). Uses the same `net_rng` stream so
    # the involuntary edges are reproducible without disturbing the main
    # RNG. These edges are exempt from `TieRewiring` and survive every run.
    generate_involuntary_edges(
        network, agents, net_rng, per_agent=INVOLUNTARY_PER_AGENT
    )

    party_centers = {pid: c.copy() for pid, c in PARTY_CENTERS.items()}
    env = Environment(
        attrs={
            "parties": party_centers,
            "outlets": outlets_by_id,
            "network": network,
            # F1: Friedkin-Johnsen anchor-pull rate, read by GaussianNoise.
            "fj_alpha": FJ_ALPHA,
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
        # Influence is now network-mediated by construction (ADR-001) — the
        # candidate set comes from env.attrs["network"], not a radius query.
        # Phase 4 F2: pillar opts in to the graded filter (rule default is
        # 0.0 = canonical hard cutoff, used by every non-pillar scenario).
        # Phase 5 A4: affect_weight stays at 0.0 here — bundles turn it on
        # at S2+ (BC_AFFECT_WEIGHT). Same opt-in discipline as `temperature`.
        BoundedConfidenceInfluence(
            epsilon=0.30, strength=0.0,
            temperature=BC_TEMPERATURE, affect_weight=0.0,
        ),
        PartyPull(strength=0.0),
        MediaConsumption(strength=0.0),
        # Phase 5 A1: pass the corrected-sign baseline + identity weight.
        # Phase 7: cooperative_mute attenuates valence on Allport-
        # conditions edges (added by X6 only). Default 0.5 per
        # Pettigrew & Tropp 2006.
        AffectiveUpdate(
            radius=1.5,
            learning_rate=0.0,
            identity_weight=AFFECT_IDENTITY_WEIGHT,
            baseline=AFFECT_BASELINE,
            cooperative_mute=COOPERATIVE_MUTE,
        ),
        IdentitySorting(sort_rate=0.0, step=0.05, differentiation=0.5),
        # Phase 6 R1: BacklashRepulsion is added to the pipeline at
        # strength 0 (exact no-op for S0-S4 baseline). Phase 6
        # interventions in `interventions_phase6.py` turn it on.
        BacklashRepulsion(
            epsilon=0.30, max_range=1.5, strength=0.0,
            affect_threshold=BACKLASH_AFFECT_THRESHOLD,
        ),
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
        ("BoundedConfidenceInfluence", "temperature", BC_TEMPERATURE),
        ("BoundedConfidenceInfluence", "affect_weight", 0.0),
        ("PartyPull", "strength", 0.0),
        ("MediaConsumption", "strength", 0.0),
        ("AffectiveUpdate", "lr", 0.0),
        ("IdentitySorting", "sort_rate", 0.0),
        ("EliteDrift", "rate", 0.0),
        ("TieRewiring", "rewire_rate", 0.0),
        ("TieRewiring", "affect_weight_rewire", 0.0),
        ("BacklashRepulsion", "strength", 0.0),
        ("BacklashRepulsion", "affect_threshold", BACKLASH_AFFECT_THRESHOLD),
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
        ("BoundedConfidenceInfluence", "temperature", BC_TEMPERATURE),
        ("BoundedConfidenceInfluence", "affect_weight", 0.0),
        ("PartyPull", "strength", 0.0),
        ("MediaConsumption", "strength", 0.0),
        ("AffectiveUpdate", "lr", 0.0),
        ("IdentitySorting", "sort_rate", 0.0),
        ("EliteDrift", "rate", 0.0),
        ("TieRewiring", "rewire_rate", 0.0),
        ("TieRewiring", "affect_weight_rewire", 0.0),
        ("BacklashRepulsion", "strength", 0.0),
        ("BacklashRepulsion", "affect_threshold", BACKLASH_AFFECT_THRESHOLD),
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
        ("BoundedConfidenceInfluence", "temperature", BC_TEMPERATURE),
        ("BoundedConfidenceInfluence", "affect_weight", BC_AFFECT_WEIGHT),
        ("PartyPull", "strength", 0.04),
        ("AffectiveUpdate", "lr", 0.01),
        ("MediaConsumption", "strength", 0.0),
        ("IdentitySorting", "sort_rate", 0.0),
        ("EliteDrift", "rate", 0.0),
        ("TieRewiring", "rewire_rate", 0.0),
        ("TieRewiring", "affect_weight_rewire", TR_AFFECT_WEIGHT_REWIRE),
        ("BacklashRepulsion", "strength", 0.0),
        ("BacklashRepulsion", "affect_threshold", BACKLASH_AFFECT_THRESHOLD),
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
        ("BoundedConfidenceInfluence", "temperature", BC_TEMPERATURE),
        ("BoundedConfidenceInfluence", "affect_weight", BC_AFFECT_WEIGHT),
        ("PartyPull", "strength", 0.04),
        ("AffectiveUpdate", "lr", 0.01),
        ("MediaConsumption", "strength", 0.04),
        ("IdentitySorting", "sort_rate", 0.0),
        ("EliteDrift", "rate", 0.0),
        ("TieRewiring", "rewire_rate", 0.0),
        ("TieRewiring", "affect_weight_rewire", TR_AFFECT_WEIGHT_REWIRE),
        ("BacklashRepulsion", "strength", 0.0),
        ("BacklashRepulsion", "affect_threshold", BACKLASH_AFFECT_THRESHOLD),
    ),
)


S4_HOMOPHILOUS_NETWORK = Intervention(
    id="S4_homophilous_network",
    label="Homophilous network",
    description="The homophilous social network co-evolves: ties rewire "
                "toward similarity, narrowing cross-cutting exposure.",
    label_kind="illustrative",
    citation="McPherson et al. 2001; Mutz 2006; Kan, Porter & Mason 2023",
    predicted_effect="Cross-cutting ties fall, party modularity rises; the "
                     "sorted state becomes sticky (structural ratchet).",
    param_bundle=(
        ("GaussianNoise", "sigma", 0.01),
        ("BoundedConfidenceInfluence", "epsilon", 0.30),
        ("BoundedConfidenceInfluence", "strength", 0.08),
        ("BoundedConfidenceInfluence", "temperature", BC_TEMPERATURE),
        ("BoundedConfidenceInfluence", "affect_weight", BC_AFFECT_WEIGHT),
        ("PartyPull", "strength", 0.04),
        ("AffectiveUpdate", "lr", 0.01),
        ("MediaConsumption", "strength", 0.04),
        ("IdentitySorting", "sort_rate", 0.0),
        ("EliteDrift", "rate", 0.0),
        # Post-ADR-001 S4 turns on tie rewiring only. Exposure narrowing is
        # now structural — influence already flows along edges, so a
        # homophilous network simply has few cross-party edges, and
        # rewiring deepens that. No gate parameter is involved.
        ("TieRewiring", "rewire_rate", 0.02),
        ("TieRewiring", "affect_weight_rewire", TR_AFFECT_WEIGHT_REWIRE),
        ("BacklashRepulsion", "strength", 0.0),
        ("BacklashRepulsion", "affect_threshold", BACKLASH_AFFECT_THRESHOLD),
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
