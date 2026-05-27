"""
Historical arc scenario — 1980 → 2025 (Phase 8b).

Standalone scenario. The pillar (`calm_to_camps`) is untouched.
This scenario:

- Builds a population at 1980 with per-agent heterogeneity
  (epsilon, fj_alpha, affect_lr correlated with identity_strength
  per Phase 8b M1 §3.2 magnitudes) and asymmetric `PARTY_CUE_SIGMA`
  (σ_dem = 0.22, σ_rep = 0.30; Phase 8b M4).
- Activates ResidentialMigration (M2) and CohortReplacement (M3)
  with scheduled rates.
- Carries a Schedule of 6 historical events post-1980 plus 4
  decade-boundary IdentitySorting transitions (M5).
- Runs decade-by-decade via `run_to(engine, schedule, tick)`.

Compute reminder: 135 ticks, 5 seeds (B-Seeds confirmed default for
historical-arc, vs pillar's 12). ~10-12 min per ensemble.

The 1980 initial-condition targets are pre-registered in
`phase8b_historical_replication_spec.md §9.3`. Per-decade targets
are pre-registered in §9.1-§9.2. Targets do not slide.
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
from ..rules.cohort_replacement import CohortReplacement
from ..rules.elite_drift import EliteDrift
from ..rules.identity_prime import IdentityPrimeExpiry
from ..rules.identity_sorting import IdentitySorting
from ..rules.influence import BoundedConfidenceInfluence
from ..rules.media_consumption import MediaConsumption
from ..rules.noise import GaussianNoise
from ..rules.party_pull import PartyPull
from ..rules.perception_update import PerceptionUpdate
from ..rules.repulsion import BacklashRepulsion
from ..rules.residential_migration import ResidentialMigration
from ..rules.threat_dynamics import ThreatDecay
from ..rules.tie_rewiring import TieRewiring
from .calm_to_camps import (
    BACKLASH_AFFECT_THRESHOLD,
    BC_AFFECT_WEIGHT,
    BC_TEMPERATURE,
    COOPERATIVE_MUTE,
    FJ_ALPHA,
    INVOLUNTARY_PER_AGENT,
    NET_P_BRIDGE,
    NET_P_LOCAL,
    NET_TAU,
    SOCIAL_BIAS,
    SOCIAL_NOISE,
    TR_AFFECT_WEIGHT_REWIRE,
)
from .schedule import Schedule, ScheduledEvent

# --- Build constants -----------------------------------------------------

TITLE = "Historical Arc — 1980 to 2025"

# 1980 party centroids: less extreme than the pillar's ±0.5 (which
# represents the late-modern polarized state). 1980 was post-Southern-
# realignment but pre-Reagan-era full divergence.
PARTY_CENTERS_1980 = {
    # Phase 8f §1.1 (combo_JJ): y-axis bias ±0.08 added. The Phase
    # 8b/8e centers were x-only; that left the y-component of
    # `ideological_constraint = (cx + cy) / 2` inert at the noise
    # level ~0.20, capping constraint at (0.92 + 0.20)/2 = 0.56 —
    # the constraint plateau diagnosed by the Phase 8f investigation.
    # The y bias unblocks the plateau. Magnitude 0.08 = smallest
    # value that produces in-band constraint trajectory; tested at
    # 0.08, 0.10, 0.15, 0.25 (latter values overshoot).
    0: np.array([-0.30, -0.08]),
    1: np.array([+0.30, +0.08]),
}
PARTY_NAMES = {0: "Democrats (1980)", 1: "Republicans (1980)"}
PARTY_COLORS = {0: "#1f3565", 1: "#8b2530"}

# Asymmetric PARTY_CUE_SIGMA per Phase 8b M4 (Hacker & Pierson 2020).
PARTY_CUE_SIGMA_HISTORICAL = {
    0: 0.22,   # Dems: narrower cue distribution
    1: 0.30,   # Reps: wider cue distribution
}

# Per-agent heterogeneity magnitudes (Phase 8b M1 §3.2; B-Heterogeneity-
# Magnitude defaulted at 40/60/80 per Vlad's confirm).
EPSILON_HETERO_FACTOR = 0.40
FJ_HETERO_FACTOR = 0.60
LR_HETERO_FACTOR = 0.80
HETERO_JITTER_FACTOR = 0.10

# Decade-by-decade IdentitySorting schedule (Phase 8b M5).
# Tick ranges: 0-30 (1980-90), 30-60 (1990-2000), 60-90 (2000-10),
# 90-120 (2010-20), 120-135 (2020-25).
IDENTITY_SORTING_SCHEDULE = {
    "1980-90": 0.005,
    "1990-00": 0.015,
    "2000-10": 0.030,
    "2010-20": 0.040,
    "2020-25": 0.030,
}

# Mechanism scheduled rates (per-decade tunable per spec §10.2).
# Defaults are literature-anchored starting values; the calibration
# harness adjusts within bounded scope.
RESIDENTIAL_MIGRATION_RATE_DEFAULT = 0.02
COHORT_REPLACEMENT_RATE = 0.003  # ~0.9%/yr at 3 ticks/yr; demography fixed

# EliteDrift per-decade rate schedule. McCarty-Poole-Rosenthal 2006
# documents continuous elite divergence from the 1970s onward (not
# concentrated at Citizens United 2010). Activate from 1980 at low
# rate, ramp through decades. Asymmetric throughout per Hacker &
# Pierson 2020 (R-heavy drift).
ELITE_DRIFT_SCHEDULE = {
    # Phase 8f §1.1 (combo_JJ): reshaped, front-loaded. Peak at
    # 1990-2010 (the empirical "great sort" era per Mason 2018);
    # tapering after. The investigation found this profile drives
    # mid-decade party_sep more accurately than the Phase 8e/8b
    # monotonically-rising schedule. Pre-8f schedule retained in
    # `phase8b_historical_replication_spec.md` for historical record.
    "1980-90": 0.005,
    "1990-00": 0.008,
    "2000-10": 0.008,
    "2010-20": 0.007,   # Citizens United still elevated
    "2020-25": 0.006,
}
ELITE_DRIFT_ASYMMETRIC = {0: 0.5, 1: 1.5}

# Phase 8c §4 E4 — perception-gap construct. Agents seed their
# `perceived_other_party` at build with the actual centroid plus a
# bias toward extremity on the dominant (x) axis, anchored to
# Levendusky & Malhotra 2016 / Ahler & Sood 2018 (Americans
# over-estimate out-party extremity by ~17-25%). Default
# `extreme_bias = 0.25` per Fork 4-C; jitter standard deviation
# `perception_noise = 0.15`. PerceptionUpdate then corrects this
# slowly toward observed neighbour positions at `correction_rate`.
PERCEPTION_EXTREME_BIAS = 0.25
PERCEPTION_NOISE = 0.15
PERCEPTION_CORRECTION_RATE = 0.01

# Phase 8c §5 E5 — identity-threat (Mutz 2018). The 2016 event fires
# a one-shot status-threat spike: `THREAT_2016_MAGNITUDE = 0.5` for
# `THREAT_2016_R_FRACTION = 0.60` of party=1 (Republican) agents.
# Mutz's finding was specific to white Republican respondents driving
# the 2016 status-threat response. `THREAT_DECAY_RATE = 0.05` gives
# half-life ~14 ticks ≈ 4.7 years — the 2016 spike decays to ~half
# strength by 2020 and to noise by 2025, roughly matching the ANES
# affect-spike pattern.
THREAT_2016_MAGNITUDE = 0.5
THREAT_2016_R_FRACTION = 0.60
THREAT_DECAY_RATE = 0.05
THREAT_2016_RNG_SEED = 44

# Phase 8e §2 — party-issue coupling schedule. Rises across decades
# per Mason 2018's "great sort" arriving gradually post-1990 (R1
# polarization expert's 1980-truthfulness diagnosis). 1.0 at 2010-20
# matches Phase 8d's default behaviour; lower values for earlier
# decades represent the empirical un-coupling of party and ideology
# in the post-Reagan / pre-Trump era. Used by PartyPull (scales pull
# magnitude) and AffectiveUpdate (scales issue_term contribution to
# disagreement). Pillar reads with fallback 1.0 → bit-identical to
# Phase 8d.
PARTY_ISSUE_COUPLING_SCHEDULE = {
    "1980-90": 0.40,
    "1990-00": 0.60,
    "2000-10": 0.80,
    "2010-20": 1.00,
    "2020-25": 1.10,
}

# Phase 8f §2 — per-decade sigmoid-sharpness schedule for party
# assignment. Build-time analog of the §8e party-issue coupling
# (which is the dynamics analog). At 1980 with K=2.5, the sigmoid
# `P(party=1 | x) = 1/(1+exp(-K*x))` gives only ~68% sign-aligned
# at |x|=0.3, so ~32% of 1980 partisans are "cross-pressured"
# (party doesn't match ideology sign) — fuzzy party assignment per
# the polarization reviewer's round-1 "party-as-coalition without
# coupling" diagnosis. Rises across decades to K=8.0 at modern era,
# matching the existing sharpness used in Phase 8b/8e.
PARTY_ASSIGNMENT_K = {
    # Phase 8f §2 routine fork — calibrated. Each iteration:
    # - K=2.5 was too fuzzy: 1980 party_sep collapsed to 0.41,
    #   downstream 1990/2000/2010 party_sep also dropped below band
    #   (cohort didn't fully sort even by 2010).
    # - K=4.0 fixed 1980 party_sep (→ 0.54 in-band) but downstream
    #   1990/2000 party_sep fell out (-0.05) and 1980 within-SD
    #   over-shot band ceiling — net -2 cells vs the no-schedule
    #   K=8 baseline (8f.1: 22/25 → 8f.2 K=4.0: 20/25).
    # - K=5.0 in 1980 chosen as a softer compromise: ~88%
    #   sign-aligned at |x|=0.3 (vs 95% at K=8, 80% at K=4) —
    #   mild fuzziness that reduces 1980 party_sep into band
    #   without crippling downstream realignment.
    # Rises across decades to K=8.0 at modern era (matches the
    # existing 8b/8e sharpness used pre-§2).
    "1980-90": 5.0,
    "1990-00": 6.0,
    "2000-10": 7.0,
    "2010-20": 8.0,
    "2020-25": 8.0,
}

# Phase 8e §3 — per-agent `media_cue` bias. Each partisan agent
# perceives outlets as shifted by a personal bias vector drawn from
# N(0, MEDIA_CUE_SIGMA) at build. Mirrors Phase 8a's `party_cue`
# pattern for the within-party SD collapse fix. Pillar agents do
# NOT carry media_cue → MediaConsumption fallback to no bias →
# bit-identical to Phase 8d. Independents have centrist diet
# already; they don't seed media_cue either.
#
# Phase 8f §1.1 (combo_JJ): σ raised 0.15 → 0.40. The Phase 8e value
# (0.15) was calibrated against legislator-band dispersion (DW-
# NOMINATE ~0.15-0.20); the ANES voter band is ~0.33-0.47 and
# requires broader per-agent diet dispersion. The investigation
# found 0.40 lifts within-party SD into the empirical voter band
# without over-shooting constraint endpoint. Within the ANES
# self-placement range (defensible per the investigation report).
MEDIA_CUE_SIGMA = 0.40


def _per_agent_heterogeneity(identity_strength: float, rng: np.random.Generator):
    """Compute per-agent (epsilon, fj_alpha, affect_lr) given
    identity_strength + a small Beta(2, 5)-shaped jitter. Phase 8b
    M1 §3.2 default magnitudes (40 / 60 / 80%)."""
    hetero_term = 2.0 * (identity_strength - 0.5)  # [-1, +1]
    jitter = 2.0 * (rng.beta(2.0, 5.0) - 0.286)  # mean ~0
    epsilon = 0.30 * (
        1.0 - EPSILON_HETERO_FACTOR * hetero_term
        + HETERO_JITTER_FACTOR * jitter
    )
    fj_alpha = 0.05 * (
        1.0 + FJ_HETERO_FACTOR * hetero_term
        + HETERO_JITTER_FACTOR * jitter
    )
    affect_lr = 0.01 * (
        1.0 + LR_HETERO_FACTOR * hetero_term
        + HETERO_JITTER_FACTOR * jitter
    )
    # Numerical safety clips — keep parameters in defensible ranges.
    return (
        float(np.clip(epsilon, 0.05, 0.60)),
        float(np.clip(fj_alpha, 0.005, 0.15)),
        float(np.clip(affect_lr, 0.001, 0.03)),
    )


# --- Build function ------------------------------------------------------


def build_engine(
    seed: int = 0,
    n_agents: int = 250,
    independent_fraction: float = 0.0,
    phase8e_baseline: bool = False,
) -> Engine:
    """Cold-build at 1980. Population matches the §9.3 initial-
    condition target band:

      Variance ≈ 0.50; constraint ≈ 0.30; party sep ≈ 0.55;
      affect ≈ -0.27; within-party SD ≈ 0.28; XC ties ≈ 0.35;
      sorting_index ≈ 0.27.

    The initial-condition distributions are tuned to land in the
    1980 band; the run dynamics then carry the population through
    the decades.

    Phase 8d: `independent_fraction` kwarg (default 0.0 → bit-
    identical to Phase 8b) seeds `int(fraction * n_agents)` agents
    as Independents (party=2, no party_cue / affect / perception /
    threat / cooperative_share / per-agent heterogeneity). They
    fully participate in BC + media + tie rewiring + GaussianNoise +
    IdentitySorting. Phase 8d historical re-run defaults to 0.12
    (the Klar & Krupnikov 2016 / ANES "pure independents" share).
    """
    rng = np.random.default_rng(seed)
    net_rng = np.random.default_rng(seed + 9973)

    # Phase 8d: pre-sample which agent ids will be Independents.
    # `n_indep == 0` early-exit preserves bit-identity to Phase 8b
    # at the default 0.0 (no `rng.permutation` draw).
    n_indep = int(independent_fraction * n_agents)
    if n_indep > 0:
        indep_ids = set(int(i) for i in rng.permutation(n_agents)[:n_indep])
    else:
        indep_ids = set()

    outlets = list(US_MEDIA_OUTLETS_2024)
    outlets_by_id = {o.id: o for o in outlets}

    n_identities = 3
    # 1980 identity centres — modest pre-realignment alignment
    # (sort underway but not consolidated). Mason's "great sort"
    # is mostly 1990s onward.
    identity_bias_1980 = 0.20
    party_identity_centers = {
        0: -identity_bias_1980 * np.ones(n_identities),
        1: +identity_bias_1980 * np.ones(n_identities),
    }

    agents: list[Agent] = []
    for i in range(n_agents):
        if i in indep_ids:
            # Phase 8d Independent (party=2). Broader-centered initial
            # position (N(0, 0.4)) — not centrist by definition, just
            # not partisan-aligned. Identities zero-mean. Centrist
            # media diet. NO party_cue / affect / perception / threat /
            # cooperative_share / per-agent heterogeneity attrs.
            indep_pos_x = float(np.clip(rng.normal(0, 0.4), -1.0, 1.0))
            indep_pos_y = float(np.clip(rng.normal(0, 0.4), -1.0, 1.0))
            indep_pos = np.array([indep_pos_x, indep_pos_y])
            indep_identities = np.clip(
                rng.normal(0, 0.3, size=n_identities), -1.0, 1.0,
            )
            indep_id_strength = float(rng.beta(2.0, 2.0))
            indep_stubbornness = float(rng.beta(2.0, 5.0))
            indep_diet = diet_for_party(np.zeros(2), outlets, rng)
            indep_attrs = {
                "group": 2,
                "party": 2,
                "identity_strength": indep_id_strength,
                "identities": indep_identities,
                "media_diet": indep_diet,
                "cohort": "boomer",
                "origin": indep_pos.copy(),
                "anchor": indep_pos.copy(),
                "stubbornness": indep_stubbornness,
            }
            agents.append(Agent(
                id=i, state=AgentState(ideology=indep_pos, attrs=indep_attrs)
            ))
            continue
        # Initial position drawn from a broad 1980 sort. Calibration
        # iteration showed sign-based party assignment + Gaussian
        # positions has a structural party_sep floor ≈ 0.72 (any
        # sign-filtered half-Gaussian has mean ≈ 0.36 from the
        # origin). Use *probabilistic* party assignment instead —
        # sigmoid of x with mild steepness — so ~15-20% of agents are
        # "off-side" (1980 Southern Democrats, Northeastern
        # Republicans). This reduces 1980 party_sep into the target
        # band while keeping a meaningful initial sort.
        side = -1.0 if i < n_agents // 2 else 1.0
        pos_x = float(np.clip(side * 0.15 + rng.normal(0, 0.45), -1.0, 1.0))
        pos_y = float(np.clip(rng.normal(0, 0.45), -1.0, 1.0))
        pos = np.array([pos_x, pos_y])
        # Phase 8f §2: probabilistic party assignment with per-decade
        # K. At 1980 K=2.5 → ~68% sign-aligned at |x|=0.3 → many
        # cross-pressured partisans (party-as-coalition without
        # tight coupling, per the round-1 polarization-expert
        # diagnosis). K rises across decades to 8.0 at modern era.
        # Cohort replacement uses cohort-aware K.
        k_1980 = PARTY_ASSIGNMENT_K["1980-90"]
        p_party_1 = 1.0 / (1.0 + np.exp(-k_1980 * pos_x))
        party = 1 if rng.random() < p_party_1 else 0

        diet = diet_for_party(PARTY_CENTERS_1980[party], outlets, rng)
        identity_strength = float(rng.beta(2.0, 2.0))
        identities = np.clip(
            party_identity_centers[party] + rng.normal(0, 0.3, size=n_identities),
            -1.0, 1.0,
        )
        stubbornness = float(rng.beta(2.0, 5.0))

        # Per-agent heterogeneity (M1).
        agent_eps, agent_alpha, agent_lr = _per_agent_heterogeneity(
            identity_strength, rng
        )

        # Per-party party_cue σ (M4 asymmetric).
        sigma_pc = PARTY_CUE_SIGMA_HISTORICAL[party]
        party_cue = PARTY_CENTERS_1980[party] + rng.normal(
            0.0, sigma_pc, size=2
        )

        # 1980 affect — ANES out-party therm ~40° = mild-moderate
        # coolness ≈ -0.20 normalised to [-1, 1]. Seed at build with
        # noise so the cold-build measurement lands inside the target
        # band rather than at zero.
        initial_affect = float(np.clip(
            rng.normal(-0.25, 0.10), -1.0, 1.0
        ))
        # Phase 8c §4 E4.1: perceived out-party centroid, biased
        # outward on the dominant (x) axis. The bias direction is
        # set by the out-party's actual sign (positive x for the
        # right party, negative for the left); agents seed perceptions
        # for ALL out-parties (i.e., parties other than their own).
        other_party = 1 - party
        other_centroid = PARTY_CENTERS_1980[other_party]
        # Dominant-axis bias direction: away from origin (more extreme
        # than reality) on the x dimension.
        bias_sign = 1.0 if other_centroid[0] >= 0.0 else -1.0
        perceived_other = np.array([
            other_centroid[0] + bias_sign * PERCEPTION_EXTREME_BIAS,
            other_centroid[1],
        ]) + rng.normal(0.0, PERCEPTION_NOISE, size=2)
        perceived_other = np.clip(perceived_other, -1.0, 1.0)
        attrs = {
            "group": party,
            "party": party,
            "identity_strength": identity_strength,
            "identities": identities,
            "affect": {other_party: initial_affect},
            "media_diet": diet,
            "cohort": "boomer",   # initial cohort label
            "origin": pos.copy(),
            "anchor": pos.copy(),
            "stubbornness": stubbornness,
            "party_cue": party_cue,
            # Phase 8b M1: per-agent heterogeneity attrs.
            "epsilon": agent_eps,
            "fj_alpha": agent_alpha,
            "affect_lr": agent_lr,
        }
        # Phase 8e §4 decomposition kwarg: skip 8c §4/§5 + 8e.3 seeding
        # when running baseline cells (A/B in the decomposition).
        if not phase8e_baseline:
            # Phase 8c §4 E4: perceived out-party centroid (biased
            # outward at build per Levendusky & Malhotra 2016).
            attrs["perceived_other_party"] = {other_party: perceived_other}
            # Phase 8c §5 E5: identity-threat scalar. Seeded at 0.0 at
            # build; the 2016 event fires a threat spike for a subset
            # of party=1 agents. ThreatDecay decays it.
            attrs["perceived_threat"] = 0.0
            # Phase 8e §3: per-agent media_cue bias. Partisans only.
            attrs["media_cue"] = rng.normal(0.0, MEDIA_CUE_SIGMA, size=2)
        agents.append(Agent(id=i, state=AgentState(ideology=pos, attrs=attrs)))

    # social_coord — same Phase 3 pattern, modest in 1980 (residential
    # sorting underway but moderate). Phase 8d: Independents (party=2)
    # get sign=0 (no party-based bias). At independent_fraction=0.0
    # bit-identical to Phase 8b (no party=2 agents exist).
    for a in agents:
        party = a.state.attrs["party"]
        if party == 0:
            sign = -1.0
        elif party == 1:
            sign = 1.0
        else:
            sign = 0.0
        a.state.attrs["social_coord"] = float(np.clip(
            sign * SOCIAL_BIAS + net_rng.normal(0.0, SOCIAL_NOISE),
            -1.0, 1.0,
        ))

    network = Network.homophilous(
        agents,
        net_rng,
        tau=NET_TAU,
        p_local=NET_P_LOCAL,
        p_bridge=NET_P_BRIDGE,
    )
    generate_involuntary_edges(
        network, agents, net_rng, per_agent=INVOLUNTARY_PER_AGENT
    )

    party_centers = {pid: c.copy() for pid, c in PARTY_CENTERS_1980.items()}
    env = Environment(attrs={
        "parties": party_centers,
        "outlets": outlets_by_id,
        "network": network,
        "fj_alpha": FJ_ALPHA,
        # Phase 8e §2: party-issue coupling at 1980 baseline.
        # Updated at each decade-boundary event. When
        # phase8e_baseline=True the coupling is fixed at 1.0 (the
        # pre-§8e default behaviour) for the 8b-baseline decomposition.
        "party_issue_coupling": (
            1.0 if phase8e_baseline
            else PARTY_ISSUE_COUPLING_SCHEDULE["1980-90"]
        ),
        # Phase 8e §4 decomposition flag (read by Schedule events).
        "phase8e_baseline": phase8e_baseline,
        # Phase 8f §2 — cohort-aware sigmoid-K for cohort replacement.
        # `cohort_for_tick(tick)` gives the active cohort label;
        # CohortReplacement reads this dict to pick the K for new
        # arrivals.
        "party_assignment_k_schedule": dict(PARTY_ASSIGNMENT_K),
        # M3 hooks for cohort replacement at runtime.
        "party_cue_sigma_replacement": 0.25,   # symmetric for replacements
        "cohort_diet_factory": (lambda pty, rng_: diet_for_party(
            party_centers[pty], outlets, rng_
        )),
        "viz": {
            "title": TITLE,
            "group_names": PARTY_NAMES,
            "group_colors": PARTY_COLORS,
            "show_parties": True,
            "party_centers": party_centers,
        },
    })
    space = ContinuousSpace2D(bounds=((-1.0, 1.0), (-1.0, 1.0)))

    # Pipeline — every rule the historical arc uses. Phase 8b M5:
    # IdentitySorting is *on* (sort_rate scheduled per decade).
    # Phase 8b M2/M3: ResidentialMigration + CohortReplacement
    # active env rules. EliteDrift remains 0 here; the 2010 event
    # turns it on with asymmetric drift (M4).
    rules = [
        BoundedConfidenceInfluence(
            epsilon=0.30, strength=0.08,   # ON from 1980
            temperature=BC_TEMPERATURE, affect_weight=0.0,
        ),
        # Phase 8f §1.1 (combo_JJ): historical-only PartyPull strength
        # 0.04 → 0.07. Pillar default unchanged (calm_to_camps.py uses
        # bundle-level 0.04 — Phase 8a value). Within Hetherington
        # 2001 elite-cue magnitude range (defensible).
        PartyPull(strength=0.07),   # ON from 1980 (8f §1.1 historical-only)
        MediaConsumption(strength=0.0),   # OFF — turns on at 1987 (Fairness)
        # Phase 8f §1.1 (combo_JJ): historical-only baseline 0.10 → 0.0.
        # Pillar default (Phase 5 baseline=0.10) unchanged at the rule
        # class level — pillar's calm_to_camps.py constructs
        # AffectiveUpdate at baseline=AFFECT_BASELINE=0.10. The
        # historical scenario overrides to 0.0 to remove the
        # "every-encounter-cools-at-least-0.10" floor that was
        # driving 1990-2010 affect over-cool. The cooling now scales
        # proportionally with ideological distance + identity term;
        # remains negative-going via the Phase 5 sign fix.
        AffectiveUpdate(
            radius=1.5, learning_rate=0.01,
            identity_weight=0.5, baseline=0.0,   # 8f §1.1: 0.10 → 0.0
            cooperative_mute=COOPERATIVE_MUTE,
        ),
        IdentitySorting(
            sort_rate=IDENTITY_SORTING_SCHEDULE["1980-90"],
            step=0.05, differentiation=0.5,
        ),
        BacklashRepulsion(
            epsilon=0.30, max_range=1.5, strength=0.0,
            affect_threshold=BACKLASH_AFFECT_THRESHOLD,
        ),
        # Phase 8c §4: PerceptionUpdate active in the historical arc
        # at correction_rate = 0.01 (slow correction toward observed
        # out-party positions). Agents are seeded with biased
        # perceptions at build (extreme_bias = 0.25); the rule slowly
        # corrects toward observed neighbours, modeling the partial
        # correction that empirical contact produces (Levendusky &
        # Malhotra 2016: contact corrects perception, but slowly).
        PerceptionUpdate(
            correction_rate=0.0 if phase8e_baseline else PERCEPTION_CORRECTION_RATE
        ),
        GaussianNoise(sigma=0.01),
    ]
    env_rules = [
        # Phase 8b: EliteDrift active from 1980 at low rate, ramping
        # via decade-boundary scheduled transitions. Continuous
        # elite divergence per McCarty-Poole-Rosenthal 2006;
        # Citizens United 2010 is the discrete bump, not the
        # onset.
        EliteDrift(
            rate=ELITE_DRIFT_SCHEDULE["1980-90"],
            asymmetric=ELITE_DRIFT_ASYMMETRIC,
        ),
        TieRewiring(
            rewire_rate=0.02,
            affect_weight_rewire=TR_AFFECT_WEIGHT_REWIRE,
        ),
        ResidentialMigration(
            migration_rate=RESIDENTIAL_MIGRATION_RATE_DEFAULT,
        ),
        CohortReplacement(replacement_rate=COHORT_REPLACEMENT_RATE),
        # Phase 8c §4 I4: clears X4 shared-identity-prime overrides
        # at the configured expiry tick. Inert until X4 fires.
        IdentityPrimeExpiry(),
        # Phase 8c §5 E5: decays `perceived_threat` toward zero each
        # tick. Inert until the 2016 status-threat event sets non-
        # zero threat for a fraction of agents. `THREAT_DECAY_RATE
        # = 0.05` gives half-life ~14 ticks ≈ 4.7 years.
        ThreatDecay(
            decay_rate=0.0 if phase8e_baseline else THREAT_DECAY_RATE
        ),
    ]

    # Sanity: at most one instance per class.
    seen: set[str] = set()
    for r in rules + env_rules:
        name = type(r).__name__
        if name in seen:
            raise AssertionError(f"pipeline has two {name} instances")
        seen.add(name)

    return Engine(
        agents=agents,
        env=env,
        space=space,
        rules=RulePipeline(rules),
        env_rules=env_rules,
        seed=seed,
    )


# --- The schedule -------------------------------------------------------


def _set_rule(rules, cls_name, attr, value):
    for r in rules:
        if type(r).__name__ == cls_name:
            setattr(r, attr, value)
            return
    raise KeyError(f"rule {cls_name} not in pipeline")


def _event_1987_fairness_doctrine(engine):
    """Fairness Doctrine repealed — partisan broadcast media kicks in."""
    _set_rule(engine.rules.rules, "MediaConsumption", "strength", 0.02)


def _event_1996_fox_news(engine):
    """Fox News launches — partisan media intensifies."""
    _set_rule(engine.rules.rules, "MediaConsumption", "strength", 0.04)


def _event_2008_social_media_ramp_start(engine):
    """Social media mass adoption begins — BC affect_weight ramp."""
    _set_rule(
        engine.rules.rules, "BoundedConfidenceInfluence",
        "affect_weight", 0.10,
    )


def _event_2008_obama_warmth(engine):
    """Phase 8c §2 E2.3: Obama 2008 election → one-shot warmth bump.

    Phase 8e §4 decomposition: skipped when env.attrs["phase8e_baseline"]
    is True (the 8b-baseline cells don't get the warmth event).
    """
    if engine.env.attrs.get("phase8e_baseline"):
        return
    for a in engine.agents:
        affect = a.state.attrs.get("affect")
        if not affect:
            continue
        for other_party in list(affect.keys()):
            new_val = float(np.clip(affect[other_party] + 0.05, -1.0, 1.0))
            affect[other_party] = new_val


def _event_2010_social_media_ramp_mid(engine):
    """Social media mass adoption mid-ramp."""
    _set_rule(
        engine.rules.rules, "BoundedConfidenceInfluence",
        "affect_weight", 0.20,
    )


def _event_2010_citizens_united(engine):
    """Citizens United — discrete bump in elite-divergence rate
    (asymmetric, R-heavy). This is the *transition*, not the onset
    — EliteDrift was already active from 1980 at lower rate
    (McCarty-Poole-Rosenthal continuous divergence)."""
    for r in engine.env_rules:
        if type(r).__name__ == "EliteDrift":
            r.rate = ELITE_DRIFT_SCHEDULE["2010-20"]


def _event_2012_social_media_ramp_end(engine):
    """Social media mass adoption peak."""
    _set_rule(
        engine.rules.rules, "BoundedConfidenceInfluence",
        "affect_weight", 0.30,
    )


def _event_2016_trump_election(engine):
    """Trump election — GOP coalition shift + identity sorting bump."""
    # Shift GOP party centroid slightly outward (asymmetric drift
    # acceleration the elite drift rule will continue).
    parties = engine.env.attrs["parties"]
    parties[1] = parties[1] + np.array([0.05, 0.0])
    # Bump identity sorting for the next 2 years (6 ticks).
    for r in engine.rules.rules:
        if type(r).__name__ == "IdentitySorting":
            r.sort_rate = min(0.040, r.sort_rate + 0.005)


def _event_2016_status_threat(engine):
    """Phase 8c §5 E5.5: 2016 status-threat spike (Mutz 2018). Sets
    `perceived_threat = THREAT_2016_MAGNITUDE = 0.5` for
    `THREAT_2016_R_FRACTION = 60%` of party=1 (Republican) agents.

    Phase 8e §4 decomposition: skipped under phase8e_baseline=True
    (baseline cells don't get the threat event)."""
    if engine.env.attrs.get("phase8e_baseline"):
        return
    rng = np.random.default_rng(THREAT_2016_RNG_SEED)
    r_agent_ids = sorted(
        a.id for a in engine.agents if a.state.attrs.get("party") == 1
    )
    if not r_agent_ids:
        return
    n_threatened = int(THREAT_2016_R_FRACTION * len(r_agent_ids))
    if n_threatened == 0:
        return
    sampled = set(int(i) for i in rng.choice(
        r_agent_ids, size=n_threatened, replace=False,
    ))
    for a in engine.agents:
        if a.id in sampled:
            a.state.attrs["perceived_threat"] = float(THREAT_2016_MAGNITUDE)


def _event_2018_trump_bump_revert(engine):
    """The Trump-era identity-sorting bump reverts to the decade's
    scheduled rate after 2 years."""
    for r in engine.rules.rules:
        if type(r).__name__ == "IdentitySorting":
            r.sort_rate = IDENTITY_SORTING_SCHEDULE["2010-20"]


def _event_2020_covid_jan6(engine):
    """COVID + 2020 election + January 6 — affective polarization
    spike. AffectiveUpdate.lr × 1.5 for 1 year (3 ticks)."""
    for r in engine.rules.rules:
        if type(r).__name__ == "AffectiveUpdate":
            # Apply a multiplier through a tagged attr the apply
            # method doesn't read — instead boost via lr itself
            # (saved for revert).
            engine.env.attrs["_affect_lr_pre_2020"] = r.lr
            r.lr = r.lr * 1.5


def _event_2021_affect_revert(engine):
    """Affect spike reverts after 2020-21."""
    for r in engine.rules.rules:
        if type(r).__name__ == "AffectiveUpdate":
            r.lr = engine.env.attrs.get("_affect_lr_pre_2020", 0.01)


# Decade-boundary IdentitySorting transitions (Phase 8b M5).
def _set_identity_sorting(engine, rate):
    for r in engine.rules.rules:
        if type(r).__name__ == "IdentitySorting":
            r.sort_rate = rate


def _set_elite_drift_rate(engine, rate):
    for r in engine.env_rules:
        if type(r).__name__ == "EliteDrift":
            r.rate = rate


def _decade_boundary_1990(engine):
    _set_identity_sorting(engine, IDENTITY_SORTING_SCHEDULE["1990-00"])
    _set_elite_drift_rate(engine, ELITE_DRIFT_SCHEDULE["1990-00"])
    # Phase 8e §2: party-issue coupling rises with the great sort.
    # Phase 8e §4: under phase8e_baseline=True, coupling stays at 1.0.
    if not engine.env.attrs.get("phase8e_baseline"):
        engine.env.attrs["party_issue_coupling"] = PARTY_ISSUE_COUPLING_SCHEDULE["1990-00"]


def _decade_boundary_2000(engine):
    _set_identity_sorting(engine, IDENTITY_SORTING_SCHEDULE["2000-10"])
    _set_elite_drift_rate(engine, ELITE_DRIFT_SCHEDULE["2000-10"])
    if not engine.env.attrs.get("phase8e_baseline"):
        engine.env.attrs["party_issue_coupling"] = PARTY_ISSUE_COUPLING_SCHEDULE["2000-10"]


def _decade_boundary_2010(engine):
    _set_identity_sorting(engine, IDENTITY_SORTING_SCHEDULE["2010-20"])
    # EliteDrift rate is set by Citizens United event at the same tick.
    if not engine.env.attrs.get("phase8e_baseline"):
        engine.env.attrs["party_issue_coupling"] = PARTY_ISSUE_COUPLING_SCHEDULE["2010-20"]


def _decade_boundary_2020(engine):
    _set_identity_sorting(engine, IDENTITY_SORTING_SCHEDULE["2020-25"])
    _set_elite_drift_rate(engine, ELITE_DRIFT_SCHEDULE["2020-25"])
    if not engine.env.attrs.get("phase8e_baseline"):
        engine.env.attrs["party_issue_coupling"] = PARTY_ISSUE_COUPLING_SCHEDULE["2020-25"]


def build_schedule() -> Schedule:
    """Build the historical event schedule.

    All ticks are 1980-relative. TICKS_PER_YEAR = 3.

    Event ticks:
      tick 21 (1987): Fairness Doctrine repealed
      tick 30 (1990): decade boundary — IdentitySorting transition
      tick 48 (1996): Fox News launched
      tick 60 (2000): decade boundary — IdentitySorting transition
      tick 84 (2008): social media ramp start
      tick 90 (2010): decade boundary, Citizens United, ramp mid
      tick 96 (2012): social media ramp end
      tick 108 (2016): Trump election
      tick 114 (2018): Trump-era IdentitySorting bump reverts
      tick 120 (2020): COVID/Jan6 affect spike, decade boundary
      tick 123 (2021): affect spike reverts
    """
    events = [
        ScheduledEvent(21, "fairness_doctrine_1987",
                       "Fairness Doctrine repealed (1987)",
                       _event_1987_fairness_doctrine),
        ScheduledEvent(30, "decade_1990",
                       "Decade boundary 1990 — IdentitySorting up",
                       _decade_boundary_1990),
        ScheduledEvent(48, "fox_news_1996",
                       "Fox News launched (1996)",
                       _event_1996_fox_news),
        ScheduledEvent(60, "decade_2000",
                       "Decade boundary 2000 — IdentitySorting up",
                       _decade_boundary_2000),
        ScheduledEvent(84, "social_media_ramp_start_and_obama_2008",
                       "Social media mass adoption begins (2008) + "
                       "Obama warmth bump",
                       _combined(_event_2008_social_media_ramp_start,
                                  _event_2008_obama_warmth)),
        ScheduledEvent(90, "decade_2010_and_citizens_united",
                       "Decade boundary 2010 + Citizens United + ramp mid",
                       _combined(_decade_boundary_2010,
                                  _event_2010_citizens_united,
                                  _event_2010_social_media_ramp_mid)),
        ScheduledEvent(96, "social_media_ramp_end_2012",
                       "Social media mass adoption peak (2012)",
                       _event_2012_social_media_ramp_end),
        ScheduledEvent(108, "trump_2016_and_status_threat",
                       "Trump election (2016) + Mutz 2018 status-threat "
                       "spike for 60% of party=1 agents",
                       _combined(_event_2016_trump_election,
                                  _event_2016_status_threat)),
        ScheduledEvent(114, "trump_bump_revert_2018",
                       "Trump-era IdentitySorting bump reverts (2018)",
                       _event_2018_trump_bump_revert),
        ScheduledEvent(120, "covid_jan6_2020",
                       "COVID + 2020 election + Jan 6 + decade boundary",
                       _combined(_decade_boundary_2020,
                                  _event_2020_covid_jan6)),
        ScheduledEvent(123, "affect_revert_2021",
                       "Affect spike reverts after 2020-21",
                       _event_2021_affect_revert),
    ]
    return Schedule(events)


def _combined(*funcs):
    """Return a function that calls each given func with the same
    engine argument, in order."""
    def fn(engine):
        for f in funcs:
            f(engine)
    return fn


# Tick layout.
DECADE_BOUNDARIES = {
    1990: 30,
    2000: 60,
    2010: 90,
    2020: 120,
    2025: 135,
}


def initial_tick() -> int:
    return 0


def final_tick() -> int:
    return 135
