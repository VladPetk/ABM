"""
CohortReplacement — generational turnover (Phase 8b M3).

Each tick, each agent has probability ``replacement_rate`` of being
replaced by a new agent drawn from the current cohort's distribution.
The replaced agent's ``id`` is inherited so network ties stay
structurally intact (the *node* persists; the *person* changes).

Cohort distribution shifts by tick range (the historical scenario
schedules this; the rule itself reads the cohort from
``env.attrs["cohort_spec"]``):

  - Boomer (ticks 0-45 = 1980-95): centrist-leaning
  - Gen-X / early Millennial (ticks 45-105 = 1995-2015): slight L
  - Late Millennial / Gen-Z (ticks 105-135 = 2015-25): L-leaning,
    higher college share

Source: Phillips 2022 *Political Behavior* 44:1483 (period / cohort
/ life-cycle decomposition of affective polarization).

**Pillar invariant**: ``replacement_rate = 0`` is an exact no-op.
The pillar runs with a fixed population. Only the historical
scenario activates replacement.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D
from ..core.state import AgentState


# Cohort spec — per-cohort initial-condition distributions. The
# historical scenario picks the active cohort based on tick.
COHORTS = {
    "boomer": {
        "x_mean": 0.0, "x_sd": 0.45,
        "y_mean": 0.0, "y_sd": 0.45,
        "identity_strength_alpha": 2.0,
        "identity_strength_beta": 2.0,
        "identities_mean_shift": 0.0,
    },
    "genx_early_millennial": {
        "x_mean": -0.05, "x_sd": 0.45,
        "y_mean": 0.05, "y_sd": 0.45,
        "identity_strength_alpha": 2.0,
        "identity_strength_beta": 2.2,
        "identities_mean_shift": 0.1,
    },
    "late_millennial_genz": {
        "x_mean": -0.10, "x_sd": 0.45,
        "y_mean": 0.10, "y_sd": 0.45,
        "identity_strength_alpha": 1.8,
        "identity_strength_beta": 2.0,
        "identities_mean_shift": 0.15,
    },
}


def cohort_for_tick(tick: int) -> str:
    """Pick the active cohort label for a given tick (1980 = tick 0)."""
    if tick < 45:
        return "boomer"
    if tick < 105:
        return "genx_early_millennial"
    return "late_millennial_genz"


class CohortReplacement:
    def __init__(
        self,
        replacement_rate: float = 0.0,
    ):
        # ~0.3% per tick = ~1% per year at TICKS_PER_YEAR=3, matching
        # demographic turnover.
        self.replacement_rate = replacement_rate

    def apply(
        self,
        env: Environment,
        agents: list[Agent],
        space: ContinuousSpace2D,
        rng: np.random.Generator,
        tick: int,
    ) -> None:
        if self.replacement_rate <= 0:
            return
        cohort_label = cohort_for_tick(tick)
        cohort = dict(COHORTS[cohort_label])  # Phase 8f §2: cohort dict copy + label
        cohort["_label"] = cohort_label

        # Pre-compute per-party current affect means. New arrivals
        # inherit the same-party current mean affect, NOT zero —
        # Phillips 2022 is about young cohorts entering with cohort-
        # typical attitudes, not blank-slate animus. (Original
        # implementation reset to zero, which made M3 ablation
        # over-report cohort replacement's contribution to affective
        # cooling.)
        by_party_affect = {0: [], 1: []}
        for other in agents:
            other_party = other.state.attrs.get("party")
            if other_party is None:
                continue
            other_affect = (other.state.attrs.get("affect") or {})
            v = other_affect.get(1 - other_party)
            if v is not None:
                by_party_affect[other_party].append(float(v))
        by_party_affect_mean = {
            p: (float(np.mean(v)) if v else 0.0)
            for p, v in by_party_affect.items()
        }

        for a in agents:
            if rng.random() > self.replacement_rate:
                continue
            # Phase 8d: preserve party=2 (Independent) status across
            # cohort replacement. Empirically, people don't switch
            # partisan/Independent identity at the population-
            # replacement scale; the independent fraction stays stable.
            if a.state.attrs.get("party") == 2:
                _replace_independent_inplace(a, cohort, env, rng)
            else:
                _replace_agent_inplace(
                    a, cohort, env, rng, by_party_affect_mean
                )


def _replace_agent_inplace(
    agent: Agent,
    cohort: dict,
    env: Environment,
    rng: np.random.Generator,
    by_party_affect_mean: dict = None,
) -> None:
    """Wipe and re-seed an agent's state from the cohort distribution.
    Inherits the agent's id (network ties stay structurally intact).

    `by_party_affect_mean` is the current same-party out-party-warmth
    mean — new arrivals inherit it rather than starting at zero
    (Phillips 2022 cohort theory, not blank-slate). If None,
    defaults to 0 (legacy behaviour)."""
    # New ideology drawn from the cohort distribution.
    new_x = float(np.clip(
        rng.normal(cohort["x_mean"], cohort["x_sd"]), -1.0, 1.0
    ))
    new_y = float(np.clip(
        rng.normal(cohort["y_mean"], cohort["y_sd"]), -1.0, 1.0
    ))
    new_pos = np.array([new_x, new_y])
    # Phase 8f §2 — cohort-aware sigmoid party assignment for new
    # arrivals. The pre-§2 sign-only assignment (party = 0 if x<0
    # else 1) was a hard threshold; under the per-decade K schedule
    # the cohort's K determines fuzziness. Fallback to sign-only
    # when no schedule is in env (compass_basic / pillar). The
    # cohort label ("boomer" / "genx_early_millennial" /
    # "late_millennial_genz") maps to a decade window; pick the
    # K appropriate to that cohort's adult-formation era.
    k_schedule = env.attrs.get("party_assignment_k_schedule")
    if k_schedule is not None:
        # Cohort-formation-era → K. Boomers formed in 1980-90;
        # genx_early_millennial in 1990-2010; late_millennial_genz
        # in 2010+. (Stylised mapping.)
        cohort_label = cohort.get("_label") or "late_millennial_genz"
        k_for_cohort = {
            "boomer": k_schedule.get("1980-90", 8.0),
            "genx_early_millennial": k_schedule.get("2000-10", 8.0),
            "late_millennial_genz": k_schedule.get("2020-25", 8.0),
        }.get(cohort_label, 8.0)
        # Phase 9 Tier D (`phase9_tier_d_spec.md §2`): mirror the
        # build-time lever-1 substitution. When the env flag is on,
        # the sigmoid reads (0.55·x + 0.45·y) instead of x alone, so
        # cohort replacement doesn't silently re-import x-dominance
        # every decade. Default path bit-identical.
        if env.attrs.get("tier_d_axis_balance"):
            sigmoid_arg = 0.55 * new_x + 0.45 * new_y
        else:
            sigmoid_arg = new_x
        p_party_1 = 1.0 / (1.0 + np.exp(-k_for_cohort * sigmoid_arg))
        new_party = 1 if rng.random() < p_party_1 else 0
    else:
        new_party = 0 if new_x < 0 else 1

    # Identity strength drawn from the cohort's Beta distribution.
    new_id_strength = float(rng.beta(
        cohort["identity_strength_alpha"],
        cohort["identity_strength_beta"],
    ))

    # Stubbornness Beta(2, 5) (Phase 4 F1 distribution — unchanged
    # across cohorts; the cohort distinction is in identity, not
    # personality).
    new_stubbornness = float(rng.beta(2.0, 5.0))

    # New agent's identities — base centred per cohort's mean shift,
    # with the Phase 4 noise pattern.
    new_identities = np.clip(
        np.array([0.0, 0.0, cohort["identities_mean_shift"]])
        + rng.normal(0, 0.3, size=3),
        -1.0, 1.0,
    )

    # Phase 8b post-review fix: new arrivals inherit the same-party
    # current mean affect (Phillips 2022 cohort theory), not zero. The
    # zero default produced an ablation artifact making M3 appear to
    # be the dominant mechanism — the dominance was the affect-reset,
    # not generational turnover proper.
    if by_party_affect_mean is not None and new_party in by_party_affect_mean:
        initial_warmth = by_party_affect_mean[new_party]
    else:
        initial_warmth = 0.0
    new_affect = {1 - new_party: initial_warmth}
    new_anchor = new_pos.copy()

    # party_cue — keep symmetric σ=0.25 default (the historical
    # scenario's per-party σ choice was set at build, not per-tick).
    # If the agent already has a party_cue set, use its σ_pc; else
    # default to PARTY_CUE_SIGMA from the env if registered, else
    # 0.25 (Phase 8a default).
    sigma_pc = float(env.attrs.get("party_cue_sigma_replacement", 0.25))
    centroid = env.attrs.get("parties", {}).get(
        new_party, np.array([-0.5 if new_party == 0 else 0.5, 0.0])
    )
    new_party_cue = centroid + rng.normal(0.0, sigma_pc, size=2)

    # Per-agent heterogeneity attrs — re-seed using the deterministic
    # correlation with identity_strength (Phase 8b M1 magnitudes).
    hetero_term = 2.0 * (new_id_strength - 0.5)  # [-1, +1]
    new_epsilon = 0.30 * (1.0 - 0.40 * hetero_term)
    new_fj_alpha = 0.05 * (1.0 + 0.60 * hetero_term)
    new_affect_lr = 0.01 * (1.0 + 0.80 * hetero_term)

    # Media diet inherits the same generator the historical builder
    # used. The replacement-time media diet is picked by the env's
    # registered helper if present; otherwise the agent keeps its
    # existing diet (the persons changes; their media diet not
    # re-rolled — a stylization).
    diet_factory = env.attrs.get("cohort_diet_factory")
    if diet_factory is not None:
        new_diet = diet_factory(new_party, rng)
    else:
        new_diet = agent.state.attrs.get("media_diet", {})

    # In-place mutation of the agent's state. id is preserved by
    # virtue of mutating in place — caller doesn't need to do anything.
    agent.state.ideology = new_pos
    agent.state.attrs["party"] = new_party
    agent.state.attrs["group"] = new_party
    agent.state.attrs["identity_strength"] = new_id_strength
    agent.state.attrs["stubbornness"] = new_stubbornness
    agent.state.attrs["identities"] = new_identities
    agent.state.attrs["affect"] = new_affect
    agent.state.attrs["anchor"] = new_anchor
    agent.state.attrs["origin"] = new_pos.copy()
    agent.state.attrs["party_cue"] = new_party_cue
    agent.state.attrs["epsilon"] = new_epsilon
    agent.state.attrs["fj_alpha"] = new_fj_alpha
    agent.state.attrs["affect_lr"] = new_affect_lr
    agent.state.attrs["media_diet"] = new_diet


def _replace_independent_inplace(
    agent: Agent,
    cohort: dict,
    env: Environment,
    rng: np.random.Generator,
) -> None:
    """Phase 8d: replace an Independent (party=2) agent with another
    Independent — preserve partisan-status across cohort replacement.
    No party_cue, no affect dict, no perceived_other_party. The new
    Independent uses the cohort's spatial distribution but does NOT
    inherit the cohort's partisan-leaning identity shift (Independents
    have zero-mean identities by definition).
    """
    new_x = float(np.clip(
        rng.normal(0.0, 0.4), -1.0, 1.0  # broad-centered (Phase 8d W9)
    ))
    new_y = float(np.clip(
        rng.normal(0.0, 0.4), -1.0, 1.0
    ))
    new_pos = np.array([new_x, new_y])
    new_id_strength = float(rng.beta(
        cohort["identity_strength_alpha"],
        cohort["identity_strength_beta"],
    ))
    new_stubbornness = float(rng.beta(2.0, 5.0))
    # Zero-mean identities (no partisan center bias).
    new_identities = np.clip(rng.normal(0, 0.3, size=3), -1.0, 1.0)
    # Centrist diet for new Independent. The cohort_diet_factory
    # expects party 0 or 1; Independents always get a centrist diet
    # built directly from US_MEDIA_OUTLETS_2024 at origin position.
    from ..core.outlets import diet_for_party, US_MEDIA_OUTLETS_2024
    new_diet = diet_for_party(np.zeros(2), US_MEDIA_OUTLETS_2024, rng)
    agent.state.ideology = new_pos
    agent.state.attrs["party"] = 2
    agent.state.attrs["group"] = 2
    agent.state.attrs["identity_strength"] = new_id_strength
    agent.state.attrs["stubbornness"] = new_stubbornness
    agent.state.attrs["identities"] = new_identities
    agent.state.attrs["anchor"] = new_pos.copy()
    agent.state.attrs["origin"] = new_pos.copy()
    agent.state.attrs["media_diet"] = new_diet
    # Independent has no party_cue, no affect dict, no perceived_*.
    # Don't add them. If the old replaced agent was somehow partisan
    # (shouldn't happen — we branch on party=2 caller-side), this
    # would leave stale partisan attrs. Defensively, clean them:
    for stale_key in (
        "party_cue", "affect", "perceived_other_party",
        "cooperative_share", "identity_weight_override",
        "identity_prime_expires_at", "perceived_threat",
        "epsilon", "fj_alpha", "affect_lr",
    ):
        agent.state.attrs.pop(stale_key, None)
