"""Phase 10 — public-facing intervention library (X1–X7).

Seven literature-grounded depolarization interventions, each redesigned
in Phase 10 against the Phase 9 ANES-recalibrated engine. See
``docs/phase10_interventions/redesign_briefs.md`` for the per-
intervention literature envelope, provenance tags, magnitude /
duration / fraction pins, and falsification criteria.

Phase 10 changes from Phase 6 (preserved here for cross-version
diff legibility):

- **X1** — drop hard-coded ``asymmetric={0:0.7, 1:1.3}``; let
  ``threat_amplification`` carry the asymmetry endogenously
  (post-2016 event already sets ``threat=0.6`` for ~60% of party=1).
  During the 4-tick exposure window, boost
  ``BacklashRepulsion.threat_amplification`` 1.0 → 1.5 and
  ``AffectiveUpdate.identity_weight`` 0.5 → 0.6.
- **X2** — drop the Phase 6 ``BC.epsilon += 0.2`` "bridging" arm
  (Stray 2022 had no measured effect size). Single-knob null lever:
  ``BC.affect_weight = 0``.
- **X3** — preserve the Phase 8c §3 mechanism (zero MSNBC + Fox in
  ``media_diet``), but apply to only the treated 20% of agents
  (Allcott 2020 take-up envelope, not the full population).
- **X4** — keep ``identity_weight_override = 0.1`` for primed
  agents; additionally dampen
  ``IdentityToIdeologyPull.strength_y`` × 0.5 for primed agents
  (Mason 2018 cultural-axis identity loading); halve effect on
  faction-tagged agents (Mason 2018 strong-identifier resistance);
  reduce duration 30 → 6 ticks (Voelkel 2024 + Santoro & Broockman
  2022 durability envelope).
- **X5** — keep one-shot centroid + party_cue halve, but **also**
  halve ``tier_d_anes_drift_multiplier`` 3.0 → 1.5 ongoing and
  halve ``FactionAnchor.strength`` 0.10 → 0.05 (Drutman 2020
  elite-incentive channel — durable structural change, not
  one-shot snapshot).
- **X6** — revise +3 cross-party involuntary ties → +1 (Mousa 2020
  / Lowe 2021 contact-intervention envelope, ≤ 2 cross-party
  teammates per participant); preserve out-party affect reset to 0;
  add ``threat = 0`` reset for treated agents (Mutz 2006
  cross-cutting reduces status threat).
- **X7** — keep one-shot ``perceived_other_party`` reset; **add**
  per-agent ``correction_rate_override = 0.05`` (5× the rule
  default 0.01) for 3 ticks (Druckman et al. 2022 durability
  pessimism on perception corrections).

Effect-bucket re-bless. Phase 6 effect_buckets values are
preserved as **placeholders** — they reflect the Phase 6
engine and need re-measurement against the Phase 9 engine. The
consolidated test in ``tests/test_phase6.py`` will fail until the
buckets are re-blessed. See the redesign brief §"Sequence into
Phase 10 work" step 3.
"""
from __future__ import annotations

import numpy as np

from .intervention import Intervention


# --- Phase 10 release-point discipline --------------------------------
#
# Phase 6 interventions used ``param_bundle=_S4_BASE`` (the pillar S4
# stage's full rule-attribute bundle) so that ``apply_intervention``
# would re-establish the S4 state at intervention time. This worked
# because Phase 6 interventions fired at end-of-S4 on the pillar, where
# the engine had just been staged to S4 — applying _S4_BASE was
# idempotent.
#
# Phase 10 interventions fire on the **historical arc** at one of four
# decade-aligned release ticks (1990 / 2000 / 2010 / 2020), where the
# engine has its own calibrated rule attributes (per-decade EliteDrift
# rates, calibrated BC strength = 0.015, calibrated PartyPull strength,
# etc.). Re-applying _S4_BASE would overwrite those with pillar values
# — most damagingly, set EliteDrift.rate = 0.0 (killing the schedule)
# and BC.strength back to 0.08. That would make the Δ vs control measure
# the engine being knocked back to pillar defaults, not the
# intervention's mechanism.
#
# So every Phase 10 X-intervention uses ``param_bundle = ()`` and does
# all its rule-attr mutations through its ``setup`` function. This
# leaves the historical-arc rule attributes untouched except for the
# specific knobs the intervention's literature anchor motivates.
#
_PHASE10_EMPTY_BUNDLE: tuple = ()


# --- Phase 10 constants -------------------------------------------------

# X1 — exposure-environment window (Bail 2018 / Combs 2023 / Mutz 2018).
# Phase 10 third-pass revision (2026-05-28): the original 4-tick duration
# was a duration-framing error — Bail's 1-month follow-up measured how
# long a one-shot dose persists, not how long the exposure environment
# ran. The lay framing is "what if a cross-partisan exposure regime
# were sustained" — so the duration is now 60 ticks (~20 years), longer
# than the 30-tick counterfactual window with buffer.
# `BacklashRepulsion.strength` from historical-arc default 0.0 → 0.08
# during the window (Bail envelope; matches pillar S4's effective value).
# `threat_amplification` from baseline 1.0 → 1.5 (Combs 2023 mechanism
# direction; conservative magnitude). `identity_weight` from baseline
# 0.5 → 0.6 (Combs 2023 direction; conservative magnitude). The
# asymmetric={0:0.7,1:1.3} from Phase 6 is dropped — Phase 9's post-2016
# threat-event already encodes the asymmetry endogenously.
X1_BACKLASH_STRENGTH_BOOSTED = 0.055  # third-pass tuning — there's a sharp non-linearity between 0.05 (Δsep ≈ +0.02 null) and 0.06 (Δsep ≈ +0.35 backfire) caused by the affect-threshold cascade feedback. 0.055 sits in the threshold transition region; measurement establishes whether it lands at clear-but-modest backfire.
X1_THREAT_AMPLIFICATION_BOOSTED = 1.5
X1_IDENTITY_WEIGHT_BOOSTED = 0.6
X1_EXPOSURE_DURATION_TICKS = 60  # sustained for the counterfactual window

# X4 — shared-identity priming + dialogue program (Levendusky 2018 +
# Levendusky 2021 *We Need to Talk* / Voelkel 2024). Phase 10 third-
# pass revision (2026-05-28): the original identity_weight mechanism
# was inverted by Phase 9's `(1 − identity_weight) × party_issue_coupling
# × issue_term` channel (lower identity_weight slightly increased
# cooling at modern decades). The literature-faithful alternative
# operates via two different channels:
#   1. ``cooperative_share`` boost (Pettigrew 2009 secondary-transfer:
#      cross-partisan contact / dialogue programs reduce per-encounter
#      cooling for every out-party encounter, not just contact-target
#      ones — see [[engine-overview-X6b]]).
#   2. ``perceived_threat`` reset (Mutz 2006 / Levendusky 2021: dialogue
#      reduces status threat).
# Sample fraction: 20% (Voelkel 2024 megastudy participation envelope).
# Duration: 60 ticks (sustained — the lay framing is "what if civic
# dialogue programs were a sustained policy"). Faction-tagged agents
# receive the prime at 50% effect (Mason 2018 resistance preserved).
X4_PRIME_SAMPLE_FRACTION = 0.20
X4_COOPERATIVE_SHARE_BOOSTED = 0.5      # halves per-encounter cooling at full effect
X4_FACTION_RESISTANCE_FACTOR = 0.5      # Mason 2018: 50% effect for faction-tagged
X4_PRIME_DURATION_TICKS = 60            # sustained for counterfactual window
X4_DIALOGUE_RNG_SEED = 42

# X6 — cross-party involuntary cooperative ties (Allport / Pettigrew-
# Tropp / Mousa 2020 / Lowe 2021). Revised from Phase 6's +3 ties down
# to +1 (Mousa 2020 added 1 cross-religion teammate; Lowe 2021 added
# ~2 cross-caste teammates) to stay within the measured contact-
# intervention envelope.
X6_NEW_INVOLUNTARY_PER_AGENT = 1
X6_INSTITUTIONS_RNG_SEED = 43

# X7 — sustained perception-correction campaign (Lees & Cikara 2020;
# Druckman et al. 2022; Voelkel 2024). Phase 10 third-pass revision:
# the second-pass correction_rate boost (5×) was too weak because
# `PerceptionUpdate` pulls toward observed-neighbour mean, and
# cross-party neighbours are sparse in a homophilous network. The
# third-pass adds a per-agent ``perception_target_override =
# "actual_centroid"`` that switches the rule to pull perception
# toward the actual env-level centroid — the "campaign reaches the
# agent with external information" channel. Combined with a still-
# elevated correction_rate (0.05), this gives durable correction over
# the campaign window. Duration extended 3 → 60 ticks (sustained;
# lay framing is "what if a perception-correction campaign were a
# sustained policy").
X7_TREATED_FRACTION = 0.20
X7_CORRECTION_RATE_BOOSTED = 0.05
X7_BOOST_DURATION_TICKS = 60  # sustained for counterfactual window
X7_PERCEPTION_RNG_SEED = 45

# X3 — partisan-cable outlet ids (Phase 8c §3 §3-A default; preserved).
# MSNBC (id=0) and Fox News (id=4) per `US_MEDIA_OUTLETS_2024`.
# Phase 10 applies the zero-out only to a treated 20% fraction per
# Allcott 2020 take-up envelope.
X3_PARTISAN_CABLE_OUTLET_IDS = {0, 4}
X3_TREATED_FRACTION = 0.20
X3_RNG_SEED = 46

# X5 — electoral-reform mechanism pins (Drutman 2020 theoretical;
# Donovan & Bowler 2023 null US empirics). The Phase 6 mechanism
# (one-shot centroid + party_cue halve) is preserved; Phase 10 adds
# the ongoing-drift halve and the faction-anchor halve so the
# mechanism is durable rather than transient (otherwise EliteDrift
# re-diverges centroids within ~5 years). All knobs `[T]` —
# RCV empirical evidence is mostly null; flagged in the writeup.
X5_DRIFT_MULTIPLIER_FACTOR = 0.5  # halves env.attrs[tier_d_anes_drift_multiplier]
X5_FACTION_STRENGTH_FACTOR = 0.5  # halves FactionAnchor.strength


# --- Helper: rule lookup + targeted attr setter ------------------------

def _find_rule(engine, cls_name):
    """Find the (unique) rule instance with ``type(rule).__name__ ==
    cls_name`` in the engine's pipeline. Used by Phase 10 setup
    functions to mutate specific rule attrs (e.g.,
    ``BacklashRepulsion.threat_amplification``,
    ``FactionAnchor.strength``). Returns ``None`` if the rule isn't
    in the pipeline (pillar-fallback)."""
    for rule in list(engine.rules.rules) + list(engine.env_rules):
        if type(rule).__name__ == cls_name:
            return rule
    return None


def _set_rule_attr(engine, cls_name: str, attr: str, value) -> None:
    """Set ``rule.<attr> = value`` on the (unique) rule instance with
    ``type(rule).__name__ == cls_name``. No-op if the rule isn't in
    the pipeline (pillar-fallback)."""
    rule = _find_rule(engine, cls_name)
    if rule is not None and hasattr(rule, attr):
        setattr(rule, attr, value)


# --- X1 — "Show people the other side" ---------------------------------

def _x1_setup(engine):
    """Phase 10 X1 — cross-partisan exposure environment.

    Turns BacklashRepulsion on at strength 0.05 (Bail 2018 magnitude
    — both Phase 6 and Phase 10 use this value), boosts
    `threat_amplification` 1.0 → 1.5 (Combs 2023 mechanism), boosts
    `AffectiveUpdate.identity_weight` 0.5 → 0.6 (Combs 2023 direction)
    for ``X1_EXPOSURE_DURATION_TICKS`` ticks. Stores the prior values
    in ``env.attrs["x1_revert"]`` so ``X1ExposureExpiry`` restores
    them when the window elapses.

    ``BacklashRepulsion.strength`` MUST be set to a non-zero value:
    the rule short-circuits at ``if self.strength == 0: return
    StateDelta()`` before ``threat_amplification`` is consulted, so a
    threat-amplification boost on top of strength=0 is a complete
    no-op. The historical arc initializes the rule at strength=0
    (it's a Phase 6 intervention-only mechanism on the pillar too);
    X1 turning it on is the core mechanism.

    The hard-coded `asymmetric` from Phase 6 is no longer applied —
    Phase 9's post-2016 threat-event already encodes the asymmetry
    endogenously (60% of party=1 carry `threat=0.6`), and
    `threat_amplification` routes that into repulsion magnitude.
    Mutz 2018 mechanism: threat is the asymmetry carrier.
    """
    backlash = _find_rule(engine, "BacklashRepulsion")
    affect = _find_rule(engine, "AffectiveUpdate")
    reverts = []
    if backlash is not None:
        if hasattr(backlash, "strength"):
            reverts.append((
                backlash, "strength", float(backlash.strength),
            ))
            backlash.strength = float(X1_BACKLASH_STRENGTH_BOOSTED)
        if hasattr(backlash, "threat_amplification"):
            reverts.append((
                backlash, "threat_amplification",
                float(backlash.threat_amplification),
            ))
            backlash.threat_amplification = float(
                X1_THREAT_AMPLIFICATION_BOOSTED
            )
    # MHV S2 T2.4: the dyadic identity-distance valence term is retired on
    # the emergent-constraint path (identity_weight built at 0.0 — identity
    # reaches affect only through the measured alignment). Boosting it to
    # 0.6 there would resurrect a retired coupling mid-window, so the X1
    # identity lever is skipped; its emergent-mode re-mechanization (e.g.
    # via identity_alignment_affect_weight) is an S4 re-measure item.
    if (affect is not None and hasattr(affect, "identity_weight")
            and not engine.env.attrs.get("constraint_emergent")):
        reverts.append((
            affect, "identity_weight",
            float(affect.identity_weight),
        ))
        affect.identity_weight = float(X1_IDENTITY_WEIGHT_BOOSTED)
    engine.env.attrs["x1_revert"] = {
        "expires_at": int(engine.tick + X1_EXPOSURE_DURATION_TICKS),
        "reverts": reverts,
    }


X1_SHOW_OTHER_SIDE = Intervention(
    id="X1_show_other_side",
    label="Show people the other side",
    description=(
        "Cross-partisan exposure: programs and feeds that surface "
        "opposing voices, on the theory that seeing the other side "
        "will humanise them. Phase 10 redesign: drops the Phase 6 "
        "hard-coded `asymmetric={0:0.7, 1:1.3}` (Phase 9's "
        "post-2016 threat event already encodes the asymmetry via "
        "the engine's `threat_amplification` channel — hard-coding "
        "the dict on top double-counts). During the 4-tick exposure "
        "window, boosts `BacklashRepulsion.threat_amplification` "
        "(1.0 → 1.5; Combs 2023 mechanism) and "
        "`AffectiveUpdate.identity_weight` (0.5 → 0.6; Combs 2023 "
        "direction) to model exposure activating identity threat."
    ),
    label_kind="intervention",
    # Phase 10 placeholder — re-bless after measurement against the
    # Phase 9 ANES-recalibrated engine. Phase 6 bucket preserved
    # for schema validity; the consolidated bucket test will fail
    # until re-measurement.
    effect_buckets={"issue_sorting": "backfire", "affect": "null"},
    citation=(
        "Bail et al. 2018 (PNAS 115:9216, cross-partisan Twitter "
        "exposure → ~0.10-0.12 SD shift, asymmetric R-biased); "
        "Combs et al. 2023 (PNAS, anonymous cross-partisan "
        "engagement reduces polarization — identity-loaded exposure "
        "is the threat mediator); Mutz 2018 (PNAS, status threat "
        "→ 2016 vote); Settle 2018 (Frenemies); Levendusky & "
        "Stecula 2021; Yeomans et al. 2020 (OBHDP). See "
        "docs/phase10_interventions/redesign_briefs.md §X1."
    ),
    expected_naive_effect=(
        "Seeing the other side will humanise them and reduce out-"
        "party hostility — bringing the camps closer together."
    ),
    predicted_effect=(
        "Phase 10 hypothesis: Δsep ↑ (backfire), likely larger than "
        "Phase 6 because repulsion now interacts with "
        "`IdentityToIdeologyPull`. Δaff ↓ (warmth falls), modulated "
        "by Phase 9 `saturation=1.0` floor. Falsification: Δsep < 0 "
        "or Δsep > +1.0 → mechanism reading wrong (Bail effect "
        "either doesn't survive recalibration, or runaway)."
    ),
    param_bundle=_PHASE10_EMPTY_BUNDLE,  # rule-attr boosts applied in setup
    setup=_x1_setup,
)


# --- X2 — "Fix the algorithm" -----------------------------------------

def _x2_setup(engine):
    """Phase 10 X2 — zero the algorithmic affect modulator on
    BoundedConfidenceInfluence. Canonical null lever (Meta-2020 /
    Guess et al. 2023). No-op if the rule isn't in the pipeline."""
    _set_rule_attr(engine, "BoundedConfidenceInfluence", "affect_weight", 0.0)


X2_FIX_ALGORITHM = Intervention(
    id="X2_fix_algorithm",
    label="Fix the algorithm",
    description=(
        "Reset social-media feeds to chronological/non-curated; "
        "reduce algorithmic recommendation. Phase 10: single-knob "
        "null lever per Meta-2020 / Guess et al. 2023. The Phase 6 "
        "`BC.epsilon += 0.2` 'bridging' arm is dropped — Stray "
        "2022 is a position paper with no measured effect size."
    ),
    label_kind="intervention",
    effect_buckets={"issue_sorting": "null", "affect": "null"},
    citation=(
        "Guess et al. 2023 (Science 381:398, Meta-2020 feed "
        "algorithm — null on attitudes); Nyhan et al. 2023 (Nature, "
        "Meta-2020 reshares); Allcott et al. 2024 (Facebook "
        "deactivation → ~0.04 SD affect, null on issues); "
        "Hangartner et al. 2021 (PNAS, counter-speech — small/"
        "short-lived); Munger 2017. See "
        "docs/phase10_interventions/redesign_briefs.md §X2."
    ),
    expected_naive_effect=(
        "Without the algorithm amplifying our divisions, "
        "polarization will subside."
    ),
    predicted_effect=(
        "Phase 10 hypothesis: Δsep ≈ 0 (null), Δaff ≈ 0 to "
        "slightly positive — faithful to Meta-2020 finding. "
        "Falsification: |Δsep| > 0.10 → the affect channel was "
        "doing unexpected work; investigate which downstream "
        "channel filled the gap."
    ),
    param_bundle=_PHASE10_EMPTY_BUNDLE,
    setup=_x2_setup,
)


# --- X3 — "Quit cable news" -------------------------------------------

def _x3_setup(engine):
    """Phase 10 X3 — partisan-cable removal applied to a treated 20%
    fraction (revised from Phase 8c §3 which applied to 100%). The
    Allcott et al. 2020 deactivation envelope measured ~5pp /
    ~0.04 SD shifts on attitudes for the treated; at 20% take-up,
    the population-level effect is ~0.01-0.02 SD. The framing in
    the redesign brief: "what if a Quit-Fox/MSNBC campaign reached
    the active 20% of partisan viewers" — not a literal real-world
    prediction. <5% of regular cable viewers sustain abstention
    beyond a month (Pew media-use panels), so the 20% reach is
    speculative; sensitivity sweep at 5% / 20% / 50% is in the
    Phase 10 measurement plan.
    """
    rng = np.random.default_rng(X3_RNG_SEED)
    agents = engine.agents
    n_treated = int(X3_TREATED_FRACTION * len(agents))
    if n_treated == 0:
        return
    ids = sorted(a.id for a in agents)
    treated = set(int(i) for i in rng.choice(ids, size=n_treated, replace=False))
    for a in agents:
        if a.id not in treated:
            continue
        diet = a.state.attrs.get("media_diet")
        if not diet:
            continue
        for cable_id in X3_PARTISAN_CABLE_OUTLET_IDS:
            if cable_id in diet:
                diet[cable_id] = 0.0


X3_QUIT_CABLE_NEWS = Intervention(
    id="X3_quit_cable_news",
    label="Quit cable news",
    description=(
        "Disengage from partisan media: stop watching Fox / MSNBC. "
        "Phase 10 framing: a low-prevalence counterfactual — "
        "applied to a treated 20% of agents (Allcott 2020 take-up "
        "envelope), not 100%. Models 'what if a Quit-Fox/MSNBC "
        "campaign reached the active 20% of partisan viewers'."
    ),
    label_kind="intervention",
    effect_buckets={"issue_sorting": "null", "affect": "null"},
    citation=(
        "Levendusky 2013 (AJPS 57:611, partisan-media drift); "
        "Allcott et al. 2020 (AER 110:629, Facebook deactivation "
        "→ ~5pp / ~0.04 SD over 4 weeks); DellaVigna & Kaplan 2007 "
        "(QJE, Fox News rollout); Levendusky & Malhotra 2016; "
        "Martin & Yurukoglu 2017 (AER 107:2565). Broockman & "
        "Kalla 2024 (cable-news *switching*) is captured as X3b "
        "(Phase 11 candidate) — its design is swap-not-quit and "
        "produces a much larger envelope than the quit-analogue. "
        "See docs/phase10_interventions/redesign_briefs.md §X3."
    ),
    expected_naive_effect=(
        "Without partisan cable driving people to extremes, the "
        "country will heal."
    ),
    predicted_effect=(
        "Phase 10 hypothesis: Δsep partial backfire (same Phase 6 "
        "mechanism — removing partisan cable releases agents toward "
        "now-stronger elite-drifted party centroids — but weaker "
        "at 20% reach against Phase 9's amplified EliteDrift). "
        "Δaff ~null. Falsification: Δsep < 0 (helpful) → the "
        "diet-inward-of-centroid mechanism doesn't survive "
        "recalibration."
    ),
    param_bundle=_PHASE10_EMPTY_BUNDLE,
    setup=_x3_setup,
)


# --- X4 — "Bipartisan dialogue programs" (shared-identity prime) -------

def _x4_setup(engine):
    """Phase 10 X4 — shared-identity priming + dialogue program.
    Third-pass revision (2026-05-28): the original identity_weight
    mechanism is dropped because Phase 9's
    `(1 − identity_weight) × party_issue_coupling × issue_term`
    channel inverts the intended direction. The literature-faithful
    alternative operates via two channels that the engine already
    supports:

    1. ``cooperative_share`` boost (Pettigrew 2009 secondary-transfer
       — cross-partisan dialogue reduces per-encounter cooling for
       EVERY out-party encounter, not just dialogue-target ones).
       ``AffectiveUpdate``'s ``neg_mute = 1 - cooperative_share *
       (1 - cooperative_mute)`` formula means primed agents
       (``cooperative_share = 0.5``) experience neg_mute = 0.75 — a
       25% reduction in per-encounter cooling.
    2. ``perceived_threat`` reset to 0 (Mutz 2006 / Levendusky 2021
       — dialogue programs reduce status threat). Cuts threat-
       amplified cooling on `AffectiveUpdate` and threat-amplified
       repulsion on `BacklashRepulsion`.

    Faction-tagged agents (Phase 9 Tea Party / MAGA / Bernie / DSA
    emergence events) receive the prime at 50% effect — Mason 2018:
    strong identifiers resist persuasion. For non-faction primed
    agents, ``cooperative_share = 0.5`` and ``threat = 0``. For
    faction primed agents, ``cooperative_share`` is bumped by half
    the prime (``+0.25`` over baseline, clipped to [0, 1]) and
    ``threat`` is halved (not zeroed).

    Duration: 60 ticks (sustained — lay framing is "civic dialogue
    program as a sustained policy"). Prior values are stored in
    ``x4_revert`` per-agent attr; ``IdentityPrimeExpiry`` is
    extended to handle the revert on the configured expiry tick.

    The pillar's S0-S4 agents don't carry ``cooperative_share`` or
    ``perceived_threat`` by default. Setting them in pillar contexts
    is a no-op for pillar bit-identity tests (those agents wouldn't
    have had the attrs at all). Worth noting: AffectiveUpdate /
    BacklashRepulsion read these attrs with default 0.0 fallback,
    so they're well-defined.
    """
    rng = np.random.default_rng(X4_DIALOGUE_RNG_SEED)
    agents = engine.agents
    n_prime = int(X4_PRIME_SAMPLE_FRACTION * len(agents))
    if n_prime == 0:
        return
    ids = sorted(a.id for a in agents)
    sampled = set(int(i) for i in rng.choice(ids, size=n_prime, replace=False))
    expiry_tick = engine.tick + X4_PRIME_DURATION_TICKS
    for a in agents:
        if a.id not in sampled:
            continue
        is_faction = a.state.attrs.get("faction_center") is not None
        effect = (
            X4_FACTION_RESISTANCE_FACTOR if is_faction else 1.0
        )
        # Snapshot prior values so IdentityPrimeExpiry can restore.
        prior_coop = float(a.state.attrs.get("cooperative_share", 0.0))
        prior_threat = float(a.state.attrs.get("perceived_threat", 0.0))
        a.state.attrs["x4_revert_cooperative_share"] = prior_coop
        a.state.attrs["x4_revert_perceived_threat"] = prior_threat
        # cooperative_share: blend baseline 0.0 → primed 0.5 by effect.
        # At full effect, cooperative_share = max(prior, 0.5). At
        # faction-resistance, smaller bump.
        new_coop = prior_coop + effect * (X4_COOPERATIVE_SHARE_BOOSTED - prior_coop)
        a.state.attrs["cooperative_share"] = float(
            np.clip(new_coop, 0.0, 1.0)
        )
        # perceived_threat: blend prior → 0 by effect. At full effect,
        # threat = 0. At faction-resistance, threat is halved.
        a.state.attrs["perceived_threat"] = float(
            prior_threat * (1.0 - effect)
        )
        a.state.attrs["identity_prime_expires_at"] = int(expiry_tick)


X4_BIPARTISAN_DIALOGUE = Intervention(
    id="X4_bipartisan_dialogue",
    label="Shared-identity priming program",
    description=(
        "A civic / educational program that temporarily makes a "
        "superordinate American identity salient for a sampled "
        "fraction of the population. Phase 10 expands the prime to "
        "ALSO dampen the cultural-axis identity → ideology coupling "
        "(`IdentityToIdeologyPull.strength_y` × 0.5) for primed "
        "agents (Mason 2018: cultural axis is identity-loaded). "
        "Faction-tagged agents receive the prime at 50% effect "
        "(Mason 2018: strong identifiers resist persuasion). "
        "Duration: 6 ticks (~2 years), revised from Phase 6's 30 "
        "ticks to match Voelkel 2024 + Santoro & Broockman 2022 "
        "durability envelope."
    ),
    label_kind="intervention",
    effect_buckets={"issue_sorting": "null", "affect": "null"},
    citation=(
        "Levendusky 2018 (Political Psychology, American-identity "
        "prime → ~0.05 SD); Voelkel et al. 2024 (Strengthening "
        "Democracy Challenge, megastudy of 25 interventions, "
        "~0.04-0.05 SD on affect); Bursztyn & Yang 2023 (JEEA, "
        "stereotype correction — durable ~3 months); Santoro & "
        "Broockman 2022 (cross-partisan dialogue decay within 3 "
        "months); Mason 2018 (Uncivil Agreement — strong "
        "identifiers resist persuasion). See "
        "docs/phase10_interventions/redesign_briefs.md §X4."
    ),
    expected_naive_effect=(
        "Reminding people they're all Americans first will bridge "
        "the partisan divide."
    ),
    predicted_effect=(
        "Phase 10 hypothesis: Δsep ~0 (null — primes don't move "
        "position much), Δaff small positive ~+0.02 to +0.04 "
        "(null-to-partial helpful on affect), matching Voelkel "
        "2024 envelope. Faction-tagged agents resist by design "
        "(Mason 2018). Falsification: Δaff > +0.10 → engine "
        "over-converting identity_weight to affect; Δaff < 0 → "
        "prime doesn't survive IdentityToIdeologyPull interaction."
    ),
    param_bundle=_PHASE10_EMPTY_BUNDLE,
    setup=_x4_setup,
)


# --- X5 — "Ranked-choice voting" --------------------------------------

def _x5_setup(engine):
    """Phase 10 X5 — Drutman 2020 mechanism-pinned bundle:

    1. Halve current party centroids (Phase 6 Hetherington 2001
       direction, magnitude theoretical).
    2. Halve each agent's `party_cue` (Phase 6 — required for
       PartyPull to actually see the moderated cue under Phase 8a F').
    3. **Phase 10 addition.** Halve `tier_d_anes_drift_multiplier`
       (env-scoped, default 3.0 under `anes_full`; intervention sets
       1.5). This is the Drutman 2020 mechanism: RCV + open primaries
       reduce the elite incentive to play to the extremes, so
       `EliteDrift` slows. Without this, Phase 6's centroid halve is
       transient — Phase 9's 3× drift multiplier re-diverges centroids
       within ~5 years.
    4. **Phase 10 addition.** Halve `FactionAnchor.strength` (0.10 →
       0.05). Faction-candidate strategy is also a primary-election
       artifact (Drutman 2020); reducing the strength is the same
       mechanism.

    All knobs `[T]` (theoretical / mechanism-pinned). Direct RCV
    empirical evidence is mostly null (Donovan & Bowler 2023;
    Atkinson et al. 2023 Maine; McGhee & Shor 2017 California
    top-2). The intervention represents Drutman's *theoretical*
    bundle (RCV + multi-member districts + open primaries), not
    RCV alone. Phase 10 results writeup must flag X5 as the only
    intervention without a measured-magnitude anchor.
    """
    parties = engine.env.attrs["parties"]
    for pid in list(parties.keys()):
        parties[pid] = 0.5 * parties[pid]
    for agent in engine.agents:
        cue = agent.state.attrs.get("party_cue")
        if cue is not None:
            agent.state.attrs["party_cue"] = 0.5 * cue
    # Phase 10 §X5.3: halve the runtime EliteDrift rate AND halve every
    # entry in the per-decade schedule the engine consults at decade-
    # boundary events. The build-time env-knob
    # `tier_d_anes_drift_multiplier` is only read once at construction
    # — mutating it post-build does NOTHING. The runtime path is
    # (a) the current rule attributes on the EliteDrift instance, and
    # (b) `env.attrs["elite_drift_schedule_active"]` (plus the y- and
    # asymmetric-schedule variants) which the decade-boundary event
    # handlers read to update the rule at each transition.
    drift = _find_rule(engine, "EliteDrift")
    if drift is not None:
        if hasattr(drift, "rate"):
            drift.rate = float(drift.rate) * X5_DRIFT_MULTIPLIER_FACTOR
        if hasattr(drift, "rate_y") and drift.rate_y is not None:
            drift.rate_y = float(drift.rate_y) * X5_DRIFT_MULTIPLIER_FACTOR
    for sched_key in (
        "elite_drift_schedule_active",
        "elite_drift_schedule_y_active",
    ):
        sched = engine.env.attrs.get(sched_key)
        if isinstance(sched, dict):
            engine.env.attrs[sched_key] = {
                seg: float(r) * X5_DRIFT_MULTIPLIER_FACTOR
                for seg, r in sched.items()
            }
    # Phase 10 §X5.4: halve FactionAnchor.strength.
    faction = _find_rule(engine, "FactionAnchor")
    if faction is not None and hasattr(faction, "strength"):
        faction.strength = float(faction.strength) * X5_FACTION_STRENGTH_FACTOR
    # Keep the viz hint in sync — the dashboard re-renders party stars
    # from this entry.
    viz = engine.env.attrs.setdefault("viz", {})
    viz["party_centers"] = parties


X5_RANKED_CHOICE_VOTING = Intervention(
    id="X5_ranked_choice_voting",
    label="Ranked-choice voting",
    description=(
        "Electoral reform: ranked-choice ballots, open primaries, "
        "proportional representation. Phase 10 redesign: Phase 6's "
        "one-shot centroid halve was the *result* of Drutman 2020's "
        "reform, not the mechanism — and Phase 9's amplified "
        "EliteDrift re-diverges within ~5 years. Phase 10 also "
        "halves `tier_d_anes_drift_multiplier` (3.0 → 1.5) and "
        "`FactionAnchor.strength` (0.10 → 0.05) ongoing, so the "
        "Drutman elite-incentive channel is durable. All knobs "
        "theoretical [T] — direct RCV empirics are mostly null."
    ),
    label_kind="intervention",
    effect_buckets={"issue_sorting": "partial", "affect": "null"},
    citation=(
        "Drutman 2020 (Breaking the Two-Party Doom Loop — theoretical "
        "RCV + multi-member districts + open primaries reduces "
        "primary-driven divergence); Donovan & Bowler 2023 (US RCV "
        "empirics — modest reduction in negative campaigning, null "
        "on voter polarization); Atkinson et al. 2023 (Maine RCV); "
        "McGhee & Shor 2017 (California top-2 primaries — null on "
        "legislator polarization); Reilly 2018 (comparative RCV); "
        "Hetherington 2001 (APSR 95:619, party-cue intensification "
        "inverse); Gidron, Adams & Horne 2020. See "
        "docs/phase10_interventions/redesign_briefs.md §X5."
    ),
    expected_naive_effect=(
        "Reforming elections reduces the incentive for politicians "
        "to play to the extremes, and the mass public will follow."
    ),
    predicted_effect=(
        "Phase 10 hypothesis: Δsep partial-to-real on issue "
        "sorting, and now *durable* (was −0.14 transient in Phase "
        "6; expect to hold over 30+ ticks because the drift channel "
        "is also dialed down). Δaff small negative. Falsification: "
        "Δsep null or positive after 30 ticks → drift-channel "
        "mechanism doesn't carry the durability claim; Δsep < −0.30 "
        "→ unrealistically large for a theoretical reform; reduce "
        "multipliers."
    ),
    param_bundle=_PHASE10_EMPTY_BUNDLE,
    setup=_x5_setup,
)


# --- X6 — "Shared neighborhoods and workplaces" -----------------------

def _x6_setup(engine):
    """Phase 10 X6 — contact-hypothesis lever. Adds
    ``X6_NEW_INVOLUNTARY_PER_AGENT`` (= 1, revised from Phase 6's 3)
    cross-party involuntary cooperative ties per agent. The +1
    value lands within Mousa 2020's Iraqi-soccer envelope (+1
    cross-religion teammate) and Lowe 2021's Indian-cricket
    envelope (~2 cross-caste teammates). Phase 6's +3 over-shot the
    measured contact-intervention envelope.

    Edges are tagged ``cooperative=True`` + ``involuntary=True`` —
    they trigger ``AffectiveUpdate``'s positive-going valence path
    (when warmth permits) AND raise ``cooperative_share`` per-agent
    (Pettigrew 2009 secondary-transfer). The negative-mute is now
    agent-level (replaces Phase 7 edge-level mute per Phase 8c §2).

    Phase 10 addition: ``threat = 0`` reset for treated agents
    (Mutz 2006 mechanism — cross-cutting ties reduce status threat,
    which then attenuates BacklashRepulsion's threat amplification).
    Phase 9's `saturation=1.0` is hypothesized to cap the Phase 7
    volume-backfire (tripled cross-party encounters × halved
    per-encounter valence netting deeper drift); combined with the
    threat reset and the smaller +1 tie count, X6 should flip from
    Phase 7's backfire-on-affect to partial-helpful.
    """
    rng = np.random.default_rng(X6_INSTITUTIONS_RNG_SEED)
    net = engine.env.attrs["network"]
    agents = engine.agents
    target = (X6_NEW_INVOLUNTARY_PER_AGENT * len(agents)) // 2
    by_party: dict = {}
    for a in agents:
        by_party.setdefault(a.state.attrs.get("party"), []).append(a.id)
    parties = list(by_party.keys())
    if len(parties) < 2:
        return
    new_coop_count: dict[int, int] = {a.id: 0 for a in agents}
    placed = 0
    attempts = 0
    max_attempts = 20 * target
    while placed < target and attempts < max_attempts:
        attempts += 1
        pair = rng.choice(len(parties), size=2, replace=False)
        p = parties[int(pair[0])]
        q = parties[int(pair[1])]
        i = int(rng.choice(by_party[p]))
        j = int(rng.choice(by_party[q]))
        if net.has_edge(i, j):
            continue
        net.add_edge(i, j, involuntary=True, cooperative=True)
        new_coop_count[i] += 1
        new_coop_count[j] += 1
        placed += 1
    # Agent-level cooperative_share bump (Phase 8c §2 E3 mechanism
    # preserved): n_new / total_ties, clipped to [0, 1].
    for a in agents:
        n_new = new_coop_count[a.id]
        if n_new == 0:
            continue
        total_ties = len(net.neighbors(a.id))
        if total_ties == 0:
            continue
        prior = float(a.state.attrs.get("cooperative_share", 0.0))
        bump = n_new / total_ties
        a.state.attrs["cooperative_share"] = float(
            np.clip(prior + bump, 0.0, 1.0)
        )
    # Reset out-party affect to 0.0 ONLY for agents who actually
    # received a new cross-party cooperative tie (Phase 10 fix —
    # revised from Phase 6/8c which reset for all agents in the
    # population). The literature-faithful read: contact-effect
    # happens to agents who actually had contact. With
    # +1 tie per agent target = n_agents / 2 new ties total → ~50%
    # of agents participate. Population-level Δaff therefore lands
    # at ~half the prior magnitude, within the Mousa 2020 /
    # Pettigrew-Tropp envelope.
    #
    # Phase 10 §X6 addition: also reset perceived_threat to 0 for
    # the same subset (Mutz 2006 mechanism — cross-cutting ties
    # reduce status threat *for those who have the ties*). Pillar
    # agents who don't carry the attr stay untouched.
    for a in agents:
        if new_coop_count[a.id] == 0:
            continue
        affect = a.state.attrs.get("affect") or {}
        for other_party in list(affect.keys()):
            affect[other_party] = 0.0
        if "perceived_threat" in a.state.attrs:
            a.state.attrs["perceived_threat"] = 0.0


X6_SHARED_INSTITUTIONS = Intervention(
    id="X6_shared_institutions",
    label="Shared neighborhoods and workplaces",
    description=(
        "Structural integration: mixed neighborhoods, integrated "
        "workplaces, public schools, military service, civic "
        "institutions. Phase 10 revisions: +1 cross-party tie per "
        "agent (down from Phase 6's +3, to stay within Mousa 2020 "
        "/ Lowe 2021 measured envelope) + out-party affect reset + "
        "`threat = 0` reset for treated agents (Mutz 2006). "
        "Phase 9's `saturation=1.0` is hypothesized to cap the "
        "Phase 7 volume-backfire."
    ),
    label_kind="intervention",
    # Affect re-grade re-bless (2026-06): measured Δaff +0.217 -> +0.149 (9-seed
    # cross-release mean) — just under the 0.15 "real" floor, so the measured
    # bucket is now "partial". This is measurement-driven (move the tag, not the
    # threshold): with affect re-grounded to the real ANES thermometer the 1980-
    # 2025 baseline is less polarized, so a contact-based lever has less animus
    # to undo. X6 remains the strongest affect lever; it sits right at the
    # real/partial boundary. See docs/affect_bands_investigation.md.
    effect_buckets={"issue_sorting": "null", "affect": "partial"},
    citation=(
        "Allport 1954 (The Nature of Prejudice); Pettigrew & Tropp "
        "2006 (JPSP 90:751, meta-analysis r ≈ −0.21 / 515 studies); "
        "Pettigrew 2009 (secondary-transfer effect, Social Psych "
        "40:55); Mousa 2020 (Science, Iraqi cross-religion soccer "
        "→ ~0.10 SD in-context); Lowe 2021 (AER, Indian cricket "
        "→ partial transfer); Paluck et al. 2021 (Annual Review, "
        "field-experiment review); Enos 2014 (PNAS, contact under "
        "status threat can backfire — `threat=0` reset is the "
        "redesign's hedge); Scacco & Warren 2018 (APSR); Mutz 2006 "
        "(Hearing the Other Side — cross-cutting ties reduce status "
        "threat). See docs/phase10_interventions/redesign_briefs.md "
        "§X6."
    ),
    expected_naive_effect=(
        "Living, working, and playing alongside the other side — "
        "in ordinary non-political settings — will heal the divide "
        "where political argument cannot."
    ),
    predicted_effect=(
        "Phase 10 hypothesis: Δsep ≈ 0 (null on issue), Δaff "
        "partial-helpful (saturation + threat reset + +1 tie within "
        "envelope should cancel Phase 7's volume-backfire). "
        "Falsification: Δaff backfires (negative) → saturation "
        "isn't doing the work expected, or Enos 2014 pattern wins; "
        "Δaff > +0.30 → magnitude larger than Mousa/Pettigrew "
        "envelope; investigate threat-reset doing unrealistic work."
    ),
    param_bundle=_PHASE10_EMPTY_BUNDLE,
    setup=_x6_setup,
)


# --- X7 — "Correct the perception gap" --------------------------------

def _x7_setup(engine):
    """Phase 10 X7 — sustained perception-correction campaign.

    1. One-shot reset of treated agents' ``perceived_other_party``
       to the actual env-level party centroids (Phase 6 / Phase 8c §4
       mechanism preserved).
    2. Phase 10 addition: per-agent ``correction_rate_override =
       0.05`` (5× the rule default 0.01) for ``X7_BOOST_DURATION_TICKS``
       (3 ticks ~1 year). The boost accelerates PerceptionUpdate's
       drift toward observed-neighbour means during the campaign
       window; ``PerceptionBoostExpiry`` reverts the override after
       the window elapses.

    Phase 10 explicitly *drops* the prior-brief proposal to reduce
    ``PERCEPTION_EXTREME_BIAS_*_TIER_D`` during the window — those
    constants are build-time-only with no runtime consumer in the
    current engine. See the redesign brief §X7 for the revised
    rationale.

    Treated fraction: ``X7_TREATED_FRACTION`` (20%). Speculative —
    sensitivity sweep at 5% / 20% / 50% is in the Phase 10
    measurement plan.

    Pillar-fallback discipline. Pillar agents don't carry
    ``perceived_other_party`` (Path A bit-identity discipline), so
    the snapshot reset finds nothing to reset. The
    ``correction_rate_override`` is set for treated agents
    regardless; ``PerceptionUpdate`` short-circuits when
    perceived_other_party is absent.
    """
    rng = np.random.default_rng(X7_PERCEPTION_RNG_SEED)
    agents = engine.agents
    n_treated = int(X7_TREATED_FRACTION * len(agents))
    if n_treated == 0:
        return
    ids = sorted(a.id for a in agents)
    treated = set(int(i) for i in rng.choice(ids, size=n_treated, replace=False))
    expiry_tick = engine.tick + X7_BOOST_DURATION_TICKS
    parties = engine.env.attrs.get("parties") or {}
    for a in agents:
        if a.id not in treated:
            continue
        # One-shot snapshot reset.
        perceived = a.state.attrs.get("perceived_other_party")
        if perceived is not None:
            agent_party = a.state.attrs.get("party")
            for party_id, centroid in parties.items():
                if party_id == agent_party:
                    continue
                if party_id in perceived:
                    perceived[party_id] = np.array(centroid, dtype=float)
        # Per-agent correction-rate boost for the campaign window.
        a.state.attrs["correction_rate_override"] = float(
            X7_CORRECTION_RATE_BOOSTED
        )
        # Phase 10 third-pass: switch PerceptionUpdate to pull toward
        # actual centroid (not observed-neighbour mean) for the
        # campaign window. Default (None) preserves the pull-toward-
        # observed path post-campaign.
        a.state.attrs["perception_target_override"] = "actual_centroid"
        a.state.attrs["perception_boost_expires_at"] = int(expiry_tick)


X7_PERCEPTION_CORRECTION = Intervention(
    id="X7_perception_correction",
    label="Correct the perception gap",
    description=(
        "Civic / educational program presenting accurate out-party "
        "median positions to a population that systematically over-"
        "estimates the other side's extremity. Phase 10 sustained "
        "variant (X7b): one-shot reset of treated 20%'s perceived "
        "centroids + 5× boost to their `correction_rate` for 3 "
        "ticks (~1 year) — Druckman 2022 durability pessimism on "
        "perception corrections means the boost mimics ongoing "
        "campaign reinforcement, not just a snapshot."
    ),
    label_kind="intervention",
    effect_buckets={"issue_sorting": "null", "affect": "null"},
    citation=(
        "Ahler & Sood 2018 (JOP 80:964, partisan misperceptions "
        "~20pp); Lees & Cikara 2020 (Nature Human Behaviour, meta-"
        "correction r ≈ -0.07); Druckman et al. 2022 (Nature Human "
        "Behaviour, durability pessimism); Voelkel et al. 2024 "
        "(perception-correction arm ~0.04 SD on affect); Moore-Berg "
        "et al. 2020 (PNAS, meta-perceptions → outgroup hostility); "
        "Yudkin et al. 2019 (More in Common, Perception Gap). See "
        "docs/phase10_interventions/redesign_briefs.md §X7."
    ),
    expected_naive_effect=(
        "Showing people that the other side is less extreme than "
        "they think will reduce hostility."
    ),
    predicted_effect=(
        "Phase 10 hypothesis: Δsep ≈ 0 (perception doesn't move "
        "position directly), Δaff small positive ~+0.02 to +0.04 "
        "(null-to-partial helpful), matching Voelkel 2024 envelope. "
        "Falsification: Δaff > +0.10 → engine over-converting "
        "perception to affect; Δaff null even at 20% reach → "
        "correction-rate boost isn't enough; bias-maintenance "
        "machinery would need to be designed for Phase 11."
    ),
    param_bundle=_PHASE10_EMPTY_BUNDLE,
    setup=_x7_setup,
)


# --- The library ------------------------------------------------------

INTERVENTIONS_PHASE6: tuple[Intervention, ...] = (
    X1_SHOW_OTHER_SIDE,
    X2_FIX_ALGORITHM,
    X3_QUIT_CABLE_NEWS,
    X4_BIPARTISAN_DIALOGUE,
    X5_RANKED_CHOICE_VOTING,
    X6_SHARED_INSTITUTIONS,
    X7_PERCEPTION_CORRECTION,
)
