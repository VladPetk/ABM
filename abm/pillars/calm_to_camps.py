"""'Calm to camps' — the reference pillar.

Five-stage progression:
  S0 Baseline -> S1 Bounded confidence -> S2 Party identity ->
  S3 Partisan media -> S4 Homophilous social network

Phase 1 wires the **full superset** population, env and rule pipeline,
and ships only the S0 and S1 Interventions. S2-S4 will arrive as new
`Intervention` objects without changing the builder. Every later
mechanism is constructed at strength 0 so it is an exact no-op.

MHV S2 T2.5 — the pillar is REBUILT as the no-events composition control
on the new state (s2_spec §6): agents carry D=7 issue vectors (the same
frozen-loadings substrate the arc's emergent mode runs on), `ideology` is
the cached block-means projection, and the emergent rule set replaces the
legacy identity machinery — `ConstraintOp` (off at S0/S1, on from S2)
where `IdentitySorting` used to sit (it was at sort_rate=0.0 in every
stage bundle — the pillar never actually ran it), `MeasuredAlignment` as
the alignment readout, and `AffectiveUpdate.identity_weight=0.0` (the
M3-light collapse: identity reaches affect only through the measured
alignment). The pillar's IC stays stylized — uniform 2D compass positions,
party by sign — lifted to items with within-block residuals from the
frozen correlation structure (`replacement_draw` semantics), NOT the
arc's empirical party-conditional seeding: the pillar is a mechanism
control, not an empirical build. Its job is unchanged: same rules as the
shipped arc, no dated events/schedules, so an arc regression can be
bisected into rule-interaction vs event-handler.
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
from ..core.issues import build_runtime, load_loadings, project1, replacement_draw
from ..rules.affective_update import AffectiveUpdate
from ..rules.constraint_op import ConstraintOp
from ..rules.elite_drift import EliteDrift
from ..rules.faction_anchor import FactionAnchor
from ..rules.identity_prime import IdentityPrimeExpiry
from ..rules.influence import BoundedConfidenceInfluence
from ..rules.measured_alignment import MeasuredAlignment, measure_alignment
from ..rules.media_consumption import MediaConsumption
from ..rules.noise import GaussianNoise
from ..rules.party_pull import PartyPull
from ..rules.perception_update import PerceptionUpdate
from ..rules.repulsion import BacklashRepulsion
from ..rules.threat_dynamics import ThreatDecay
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

# Phase 8a — PartyPull F' (personal party_cue).
# Each agent's `party_cue` is sampled at build time from
# N(party_centroid, PARTY_CUE_SIGMA²) — representing the specific
# elite / sub-group / leader they identify with (Levendusky 2009
# "noisy cue-taking"; Mason 2018 sub-group identity; Bawn et al. 2012
# coalitional parties). PartyPull pulls each agent toward its personal
# cue, not the party-wide centroid.
#
# §11 measure-then-bless outcome: at σ=0.25 (Vlad's confirmed default;
# 12 seeds, N=250, TICKS=200), within-party SD_x at S2-end lifts from
# Phase 7's ~0.14 (just below the DW-NOMINATE legislator floor) to
# ~0.155 — inside the legislator band (~0.15-0.20) but below the ANES
# voter band (~0.33-0.47). The spec's analytic prediction of [0.20,
# 0.35] underestimated `BoundedConfidenceInfluence`'s pull toward the
# local mean, which partially cancels per-agent cue dispersion. Even
# at the cushion ceiling σ=0.35 the SD only reaches ~0.17. The
# remaining S3/S4 over-tightness is `MediaConsumption`-driven and out
# of Phase 8a's P-Scope=PartyPull-only.
#
# Non-pillar scenarios (compass_basic, etc.) do not set `party_cue`
# on their agents; `PartyPull.apply` falls back to the env-level
# centroid in that case, preserving bit-identical behaviour.
#
# MHV S2 T2.5 re-pick: 0.25 → 0.35 (the §11 bless's documented cushion
# ceiling). On the D=7 substrate the block-means lens compresses the
# projection's within-party SD (the x readout is a 3-item mean), and
# PartyPull's native per-issue pull transmits the cue dispersion
# differently — at σ=0.25 the S2-end SD_x measured 0.137, just below
# the [0.14, 0.30] DW-NOMINATE band the phase-8a test pins. The sweep
# (scripts/audit/t25_pillar_repick.py) shows σ=0.35 restores 0.151-0.154
# at the chosen ε. The empirical band is unchanged — the knob moved,
# not the threshold.
PARTY_CUE_SIGMA = 0.35

# MHV S2 T2.5 — the emergent constraint operating point for the pillar
# stages S2+. Same values as the arc's prior center (methods §5.20): the
# pillar composes the SAME mechanisms at a comparable operating point so
# rule-interaction regressions bisect cleanly; the values are stylized
# pillar parameters (like BC ε/0.08), not a calibration claim.
PILLAR_CONSTRAINT_RATE = 0.02
PILLAR_CONSTRAINT_RESID = 0.01

# MHV S2 T2.5 re-pick: pillar BC confidence radius 0.30 → 0.35. Item-space
# RMS distances carry within-block residual texture the 2D compass never
# had, so at ε=0.30 the S1 variance ratio degraded to 0.922 (vs the
# pinned <0.92; legacy measured ~0.83) — the pillar-side twin of the
# T0.6 arc finding (BC starved by the substrate's distance scale). The
# sweep puts ε=0.35 at ratio 0.891 with the wp_sd band still met; ε=0.40
# (the arc's T2.6 re-pick value) over-compresses wp_sd to the band floor.
# Stylized pillar parameter; the arc re-picks its own preset at T2.6.
PILLAR_BC_EPSILON = 0.35


def build_engine(
    seed: int = 0,
    n_agents: int = 400,
    independent_fraction: float = 0.0,
) -> Engine:
    """Construct the superset engine with every pillar mechanism present
    but every force off. Applying an Intervention's bundle turns on the
    stages that are in scope.

    Phase 8d adds the `independent_fraction` kwarg. Default 0.0 →
    bit-identical to Phase 8c §7 (no Independents seeded). Non-zero →
    `int(independent_fraction * n_agents)` agents are assigned
    `party = 2` (pure independents / unaffiliated, per Klar &
    Krupnikov 2016 *Independent Politics*). Independents have no
    `party_cue`, no `affect` dict, no `perceived_other_party` etc.,
    so the partisan-aware rules (PartyPull, AffectiveUpdate,
    BacklashRepulsion, PerceptionUpdate, IdentityPrimeExpiry,
    ThreatDecay, MeasuredAlignment) no-op on them. They DO participate
    in BoundedConfidenceInfluence, MediaConsumption, TieRewiring,
    GaussianNoise, ConstraintOp.
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

    # Phase 8d: pre-sample which agent ids will be independents. The
    # `n_indep == 0` early-return preserves bit-identity to Phase 8c
    # §7 when the kwarg is at its default 0.0 (the permutation call
    # would otherwise consume RNG draws and shift downstream values).
    n_indep = int(independent_fraction * n_agents)
    if n_indep > 0:
        indep_ids = set(int(i) for i in rng.permutation(n_agents)[:n_indep])
    else:
        indep_ids = set()

    agents: list[Agent] = []
    for i in range(n_agents):
        if i in indep_ids:
            # Phase 8d Independent agent (party=2). Broad centered
            # position (N(0, 0.4)) — not centrist by definition; some
            # Independents are ideological extremists who don't fit
            # either party. Zero-mean identities; partisan-agnostic
            # media diet (outlet centroid). Same stubbornness +
            # identity_strength distributions as partisans.
            pos_x = float(np.clip(rng.normal(0, 0.4), -1.0, 1.0))
            pos_y = float(np.clip(rng.normal(0, 0.4), -1.0, 1.0))
            pos = np.array([pos_x, pos_y])
            indep_identities = np.clip(
                rng.normal(0, 0.3, size=n_identities), -1.0, 1.0,
            )
            indep_identity_strength = float(rng.beta(2, 2))
            indep_stubbornness = float(
                rng.beta(STUBBORNNESS_ALPHA, STUBBORNNESS_BETA)
            )
            # Centrist diet — diet_for_party at origin pulls toward
            # outlet centroid, not toward a partisan camp.
            indep_diet = diet_for_party(np.zeros(2), outlets, rng)
            attrs = {
                "group": 2,
                "party": 2,
                "identity_strength": indep_identity_strength,
                "identities": indep_identities,
                # No affect, no party_cue, no perceived_other_party,
                # no cooperative_share — the partisan-aware rules
                # short-circuit on missing attrs / party == 2.
                "media_diet": indep_diet,
                "cohort": "all",
                "origin": pos.copy(),
                "anchor": pos.copy(),
                "stubbornness": indep_stubbornness,
            }
            agents.append(Agent(id=i, state=AgentState(ideology=pos, attrs=attrs)))
            continue
        pos = rng.uniform(-1.0, 1.0, size=2)
        party = 0 if pos[0] < 0 else 1
        diet = diet_for_party(PARTY_CENTERS[party], outlets, rng)
        identities = np.clip(
            party_identity_centers[party] + rng.normal(0, 0.3, size=n_identities),
            -1.0,
            1.0,
        )
        # Phase 8a F': personal party cue, fixed for life. Drawn from
        # the main RNG stream. **Note**: this `rng.normal(...)` call
        # consumes 2 draws per agent from the main stream, which shifts
        # downstream draws (`identity_strength`, `stubbornness`, and
        # subsequent agents' positions) relative to Phase 7. Pillar
        # populations are therefore NOT bit-identical to Phase 7 even
        # with the same seed. Non-pillar scenarios are unaffected —
        # they don't call this builder. The network stream (`net_rng`)
        # is independent and unaffected.
        party_cue = PARTY_CENTERS[party] + rng.normal(
            0.0, PARTY_CUE_SIGMA, size=2
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
            # Phase 8a F': the specific elite/sub-group cue this agent
            # identifies with (Levendusky 2009 plural cue-taking).
            "party_cue": party_cue,
        }
        agents.append(Agent(id=i, state=AgentState(ideology=pos, attrs=attrs)))

    # --- MHV S2 T2.5: D=7 issue substrate -------------------------------
    # Each agent's stylized 2D position is lifted to the seven ANES items
    # with within-block residuals from the frozen correlation structure,
    # recentered so the block-means projection equals the drawn position
    # exactly (`replacement_draw` semantics; the [-1,1] item clip can pull
    # extreme agents slightly inward, so `ideology` is set to the actual
    # projection — the latent uniform position remains the party-
    # assignment variable only). Dedicated rng stream: the main build
    # stream is untouched.
    _loadings = load_loadings()
    _issue_runtime = build_runtime(_loadings)
    _issue_rng = np.random.default_rng(10_000_019 + seed)
    for a in agents:
        _v = replacement_draw(a.state.ideology, _issue_runtime, _issue_rng)
        a.state.attrs["issues"] = _v
        a.state.attrs["anchor_issues"] = _v.copy()
        _p = project1(_v, _issue_runtime)
        a.state.ideology = _p
        a.state.attrs["anchor"] = _p.copy()
        a.state.attrs["origin"] = _p.copy()
        # T2.4 measured-alignment readout, seeded consistent with the
        # MeasuredAlignment rule (partisans only; see measured_alignment.py).
        _ma = measure_alignment(
            a.state.attrs.get("identities"), a.state.attrs.get("party"),
            _v, party_identity_centers, _issue_runtime,
        )
        if _ma is not None:
            a.state.attrs["identity_alignment"] = _ma

    # --- Phase 3: social_coord + homophilous tie network -----------------
    # Built with a SEPARATE RNG stream (spec E1) so the main build stream is
    # untouched and S0-S3 populations stay bit-identical to Phase 1/2.
    net_rng = np.random.default_rng(seed + 9973)
    for a in agents:
        # Phase 8d: Independents get sign=0 (no party-based social-coord
        # bias). Bit-identity at independent_fraction=0.0 preserved
        # because no agent has party==2 then; party=0 stays at -1,
        # party=1 stays at +1, RNG order unchanged.
        party = a.state.attrs["party"]
        if party == 0:
            sign = -1.0
        elif party == 1:
            sign = 1.0
        else:
            sign = 0.0
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
            # MHV S2 T2.5 — live issues mode (the apply site and every
            # native kernel read the runtime) + the emergent-mode flag
            # (read by the X1 setup guard; the pillar has no events or
            # shocks, so the other readers never fire here).
            "issue_runtime": _issue_runtime,
            "issue_rng": _issue_rng,
            "constraint_emergent": True,
            # Read by MeasuredAlignment for the identity-stacking sign.
            "party_identity_centers": {
                pid: c.copy() for pid, c in party_identity_centers.items()
            },
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
            epsilon=PILLAR_BC_EPSILON, strength=0.0,
            temperature=BC_TEMPERATURE, affect_weight=0.0,
        ),
        PartyPull(strength=0.0),
        # Phase 9 Tier C: FactionAnchor added at default strength 0.04.
        # Pillar agents never carry `faction_center` → rule is no-op
        # for every pillar agent on every tick. Pillar stays bit-
        # identical (the rule self-gates on the attr; no flag-based
        # gate needed). See `phase9_spec.md §9.1` and §9.4.
        FactionAnchor(strength=0.04),
        MediaConsumption(strength=0.0),
        # Phase 5 A1: pass the corrected-sign baseline + identity weight.
        # Phase 7: cooperative_mute attenuates valence on Allport-
        # conditions edges (added by X6 only). Default 0.5 per
        # Pettigrew & Tropp 2006.
        AffectiveUpdate(
            radius=1.5,
            learning_rate=0.0,
            # MHV S2 T2.5 (M3-light, matching the arc's emergent stack):
            # the dyadic identity-distance valence term is retired —
            # identity reaches affect only through the measured alignment.
            # AFFECT_IDENTITY_WEIGHT is kept above as the documented
            # legacy value (methods §5.21).
            identity_weight=0.0,
            baseline=AFFECT_BASELINE,
            cooperative_mute=COOPERATIVE_MUTE,
        ),
        # MHV S2 T2.5: ConstraintOp where IdentitySorting used to sit
        # (the legacy rule was at sort_rate=0.0 in every stage bundle —
        # never active). Off at build; the S2+ bundles turn it on at the
        # pillar operating point. NOTE: resid_sigma must be zeroed with
        # rate in the S0/S1 bundles — the residual noise is active even
        # at rate=0 by design (it is the dispersion counterweight).
        ConstraintOp(rate=0.0, resid_sigma=0.0),
        # T2.4 measured-alignment readout (pure measurement through the
        # delta pipeline; no consumer reads it in the pillar — the env
        # alignment-affect weight is unset — but the metric stream is
        # what the arc-vs-pillar bisection compares).
        MeasuredAlignment(),
        # Phase 6 R1: BacklashRepulsion is added to the pipeline at
        # strength 0 (exact no-op for S0-S4 baseline). Phase 6
        # interventions in `interventions_phase6.py` turn it on.
        BacklashRepulsion(
            epsilon=0.30, max_range=1.5, strength=0.0,
            affect_threshold=BACKLASH_AFFECT_THRESHOLD,
        ),
        # Phase 8c §4 E4: PerceptionUpdate present in the superset
        # pipeline but inert in pillar S0-S4 (correction_rate=0.0).
        # Pillar agents don't seed `perceived_other_party`; the rule
        # no-ops in that case regardless of rate. The historical-arc
        # scenario activates it. Adding the rule here at strength 0
        # preserves the pipeline-shape invariant tested in
        # `tests/test_phase6.py::test_apply_intervention_preserves_pipeline_structure`.
        PerceptionUpdate(correction_rate=0.0),
        GaussianNoise(sigma=0.01),
    ]
    # TieRewiring at rewire_rate=0; Phase 8c §4 IdentityPrimeExpiry
    # added to the env-rule pipeline so X4's prime overrides are
    # cleared at their configured expiry tick. Inert until X4 fires
    # (no agent has `identity_prime_expires_at`).
    # Phase 10: PerceptionBoostExpiry and X1ExposureExpiry added
    # for the X7 sustained-correction and X1 exposure-environment
    # interventions respectively. Both are inert until their
    # corresponding intervention sets the watched state.
    from ..rules.intervention_expiry import (
        PerceptionBoostExpiry,
        X1ExposureExpiry,
    )
    env_rules = [
        EliteDrift(rate=0.0),
        TieRewiring(rewire_rate=0.0),
        IdentityPrimeExpiry(),
        PerceptionBoostExpiry(),
        X1ExposureExpiry(),
        # Phase 8c §5 E5: ThreatDecay added at decay_rate=0 (inert).
        # Pillar agents never carry `perceived_threat`; the rule
        # no-ops in both senses (the early-return at decay_rate=0
        # AND the per-agent skip when threat is absent/zero).
        ThreatDecay(decay_rate=0.0),
    ]

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
        ("ConstraintOp", "rate", 0.0),
        ("ConstraintOp", "resid_sigma", 0.0),
        ("EliteDrift", "rate", 0.0),
        ("TieRewiring", "rewire_rate", 0.0),
        ("TieRewiring", "affect_weight_rewire", 0.0),
        ("BacklashRepulsion", "strength", 0.0),
        ("BacklashRepulsion", "affect_threshold", BACKLASH_AFFECT_THRESHOLD),
        # Phase 8c §6 E6.1: asymmetric = None preserves symmetric
        # pillar behaviour (bit-identical to pre-§6). X1 overrides
        # to {0: 0.7, 1: 1.3} per Bail 2018.
        ("BacklashRepulsion", "asymmetric", None),
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
        ("BoundedConfidenceInfluence", "epsilon", PILLAR_BC_EPSILON),
        ("BoundedConfidenceInfluence", "strength", 0.08),
        ("BoundedConfidenceInfluence", "temperature", BC_TEMPERATURE),
        ("BoundedConfidenceInfluence", "affect_weight", 0.0),
        ("PartyPull", "strength", 0.0),
        ("MediaConsumption", "strength", 0.0),
        ("AffectiveUpdate", "lr", 0.0),
        ("ConstraintOp", "rate", 0.0),
        ("ConstraintOp", "resid_sigma", 0.0),
        ("EliteDrift", "rate", 0.0),
        ("TieRewiring", "rewire_rate", 0.0),
        ("TieRewiring", "affect_weight_rewire", 0.0),
        ("BacklashRepulsion", "strength", 0.0),
        ("BacklashRepulsion", "affect_threshold", BACKLASH_AFFECT_THRESHOLD),
        # Phase 8c §6 E6.1: asymmetric = None preserves symmetric
        # pillar behaviour (bit-identical to pre-§6). X1 overrides
        # to {0: 0.7, 1: 1.3} per Bail 2018.
        ("BacklashRepulsion", "asymmetric", None),
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
        ("BoundedConfidenceInfluence", "epsilon", PILLAR_BC_EPSILON),
        ("BoundedConfidenceInfluence", "strength", 0.08),
        ("BoundedConfidenceInfluence", "temperature", BC_TEMPERATURE),
        ("BoundedConfidenceInfluence", "affect_weight", BC_AFFECT_WEIGHT),
        ("PartyPull", "strength", 0.04),
        ("AffectiveUpdate", "lr", 0.01),
        ("MediaConsumption", "strength", 0.0),
        ("ConstraintOp", "rate", PILLAR_CONSTRAINT_RATE),
        ("ConstraintOp", "resid_sigma", PILLAR_CONSTRAINT_RESID),
        ("EliteDrift", "rate", 0.0),
        ("TieRewiring", "rewire_rate", 0.0),
        ("TieRewiring", "affect_weight_rewire", TR_AFFECT_WEIGHT_REWIRE),
        ("BacklashRepulsion", "strength", 0.0),
        ("BacklashRepulsion", "affect_threshold", BACKLASH_AFFECT_THRESHOLD),
        # Phase 8c §6 E6.1: asymmetric = None preserves symmetric
        # pillar behaviour (bit-identical to pre-§6). X1 overrides
        # to {0: 0.7, 1: 1.3} per Bail 2018.
        ("BacklashRepulsion", "asymmetric", None),
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
        ("BoundedConfidenceInfluence", "epsilon", PILLAR_BC_EPSILON),
        ("BoundedConfidenceInfluence", "strength", 0.08),
        ("BoundedConfidenceInfluence", "temperature", BC_TEMPERATURE),
        ("BoundedConfidenceInfluence", "affect_weight", BC_AFFECT_WEIGHT),
        ("PartyPull", "strength", 0.04),
        ("AffectiveUpdate", "lr", 0.01),
        ("MediaConsumption", "strength", 0.04),
        ("ConstraintOp", "rate", PILLAR_CONSTRAINT_RATE),
        ("ConstraintOp", "resid_sigma", PILLAR_CONSTRAINT_RESID),
        ("EliteDrift", "rate", 0.0),
        ("TieRewiring", "rewire_rate", 0.0),
        ("TieRewiring", "affect_weight_rewire", TR_AFFECT_WEIGHT_REWIRE),
        ("BacklashRepulsion", "strength", 0.0),
        ("BacklashRepulsion", "affect_threshold", BACKLASH_AFFECT_THRESHOLD),
        # Phase 8c §6 E6.1: asymmetric = None preserves symmetric
        # pillar behaviour (bit-identical to pre-§6). X1 overrides
        # to {0: 0.7, 1: 1.3} per Bail 2018.
        ("BacklashRepulsion", "asymmetric", None),
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
        ("BoundedConfidenceInfluence", "epsilon", PILLAR_BC_EPSILON),
        ("BoundedConfidenceInfluence", "strength", 0.08),
        ("BoundedConfidenceInfluence", "temperature", BC_TEMPERATURE),
        ("BoundedConfidenceInfluence", "affect_weight", BC_AFFECT_WEIGHT),
        ("PartyPull", "strength", 0.04),
        ("AffectiveUpdate", "lr", 0.01),
        ("MediaConsumption", "strength", 0.04),
        ("ConstraintOp", "rate", PILLAR_CONSTRAINT_RATE),
        ("ConstraintOp", "resid_sigma", PILLAR_CONSTRAINT_RESID),
        ("EliteDrift", "rate", 0.0),
        # Post-ADR-001 S4 turns on tie rewiring only. Exposure narrowing is
        # now structural — influence already flows along edges, so a
        # homophilous network simply has few cross-party edges, and
        # rewiring deepens that. No gate parameter is involved.
        ("TieRewiring", "rewire_rate", 0.02),
        ("TieRewiring", "affect_weight_rewire", TR_AFFECT_WEIGHT_REWIRE),
        ("BacklashRepulsion", "strength", 0.0),
        ("BacklashRepulsion", "affect_threshold", BACKLASH_AFFECT_THRESHOLD),
        # Phase 8c §6 E6.1: asymmetric = None preserves symmetric
        # pillar behaviour (bit-identical to pre-§6). X1 overrides
        # to {0: 0.7, 1: 1.3} per Bail 2018.
        ("BacklashRepulsion", "asymmetric", None),
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
