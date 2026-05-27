"""Phase 6 — the public-facing intervention library.

Five named interventions, each a recognisable real-world depolarization
lever, each grounded in published literature, each mapping cleanly to
a model mechanism. The educational payoff is the contrast between
what an intuitive observer expects each intervention to do, and what
the model — calibrated on Bail, Guess, Levendusky, Hetherington,
Gidron et al. — actually shows it does.

Each intervention is a **release-phase bundle** — applied at the end
of the polarized S4 state, then the engine runs ``TICKS`` more to
measure the effect. The ``label_kind`` tags below are the §11-blessed
empirical buckets; if a future change moves an intervention out of its
bucket, the consolidated test in ``tests/test_phase6.py`` fails and
the tag is re-blessed (move the tag, not the threshold).
"""
from __future__ import annotations

import numpy as np

from .calm_to_camps import S4_HOMOPHILOUS_NETWORK
from .intervention import Intervention


# --- Shared S4 base bundle (the starting state every X-intervention ----
# modifies) ------------------------------------------------------------

# Every X-intervention is a *delta* from S4. We derive `_S4_BASE`
# directly from `S4_HOMOPHILOUS_NETWORK.param_bundle` — single source
# of truth. If a Phase 7 change adds a new tunable to S4's bundle, the
# X-interventions inherit it automatically; no risk of silent drift.
_S4_BASE: tuple = S4_HOMOPHILOUS_NETWORK.param_bundle


# --- Phase 6 R3 build constants ---------------------------------------

# X4 (Phase 8c §4 re-implementation) — Levendusky 2021 *Our Common
# Bonds* shared-identity-prime mechanism. A sampled fraction of
# agents has their `identity_weight` (in AffectiveUpdate's valence
# formula) temporarily downweighted from 0.5 → `X4_PRIMED_IDENTITY_WEIGHT`
# = 0.1, representing backgrounded partisan categorisation under
# superordinate (American national) identity salience. After
# `X4_PRIME_DURATION_TICKS` ticks (= 30 ticks ≈ 10 years), the
# override expires and identity_weight reverts to the rule-level
# default. **Vlad's Fork 2-b override (20% sampled subset)** — models
# a targeted civic program rather than a broad national rollout.
# RNG seed preserved from the Phase 6/7 dialogue setup for cross-
# version reproducibility of §11 measurements.
X4_PRIME_SAMPLE_FRACTION = 0.20
X4_PRIMED_IDENTITY_WEIGHT = 0.1
X4_PRIME_DURATION_TICKS = 30
X4_DIALOGUE_RNG_SEED = 42

# X6 — number of new cross-party *involuntary* (kin/workplace/neighborhood)
# ties added per agent on intervention. Quadruples the F3 stratum
# (default INVOLUNTARY_PER_AGENT = 1 → effective 4 after X6). Represents
# the contact-hypothesis literature: structural shared-life contact via
# mixed neighborhoods, workplaces, public schools, military service,
# civic institutions (Allport 1954; Pettigrew & Tropp 2006; Mutz 2006).
X6_NEW_INVOLUNTARY_PER_AGENT = 3
X6_INSTITUTIONS_RNG_SEED = 43

# X1 (Phase 8c §6) — asymmetric BacklashRepulsion multiplier dict
# applied at intervention time. {0: 0.7, 1: 1.3} = 1.86× ratio
# (Vlad's Fork 6-A confirmed default). Anchored by Bail 2018: in the
# cross-cutting-exposure experiment, R-users showed ~+0.13 SD shift
# toward conservatism while D-users showed ~+0.04 SD shift toward
# liberalism — a roughly 3.25× ratio. The 1.86× shipped default is
# a conservative reading; alternative 1.5× / 3× choices are §7
# sensitivity items.
X1_ASYMMETRIC_RATIO = {0: 0.7, 1: 1.3}


# X3 — partisan-cable outlet ids (Phase 8c §3 §3-A default).
# MSNBC (id=0) and Fox News (id=4) per `US_MEDIA_OUTLETS_2024`. NYT
# (id=1), Local TV (id=2), WSJ (id=3) stay in the diet — they're
# the centripetal force the model bundled in with cable in Phase 7.
# "Cable news" is a specific empirical category (Levendusky 2013;
# Allcott et al. 2020), distinct from partisan newspapers.
X3_PARTISAN_CABLE_OUTLET_IDS = {0, 4}


def _override(base: tuple, *overrides):
    """Return a bundle = base with each `(class, attr, value)` in
    `overrides` replacing the matching entry in `base`. Bundle order
    preserved; absolute discipline preserved."""
    keys = {(c, a): i for i, (c, a, _) in enumerate(base)}
    out = list(base)
    for cls, attr, val in overrides:
        if (cls, attr) not in keys:
            raise KeyError(f"override {(cls, attr)} not in base bundle")
        out[keys[(cls, attr)]] = (cls, attr, val)
    return tuple(out)


# --- X1 — "Show people the other side" -------------------------------

X1_SHOW_OTHER_SIDE = Intervention(
    id="X1_show_other_side",
    label="Show people the other side",
    description=(
        "Cross-partisan exposure: programs and feeds that surface "
        "opposing voices, on the theory that seeing the other side will "
        "humanise them. Phase 8c §6 adds Bail 2018's asymmetric "
        "reading — Republican users are more susceptible to "
        "cross-cutting backfire than Democratic users."
    ),
    label_kind="intervention",
    # Phase 8c §6 re-bless: bucket re-measured after asymmetric
    # BacklashRepulsion. Placeholder reflects the pre-§6 reading;
    # actual bucket is set by §11 measurement after this section.
    effect_buckets={"issue_sorting": "backfire", "affect": "null"},
    citation=(
        "Bail et al. 2018 (PNAS 115:9216, asymmetric backfire — "
        "R-users ~3.25× more affected than D-users); Levendusky 2021; "
        "Mutz 2006. Phase 8c §6 implements the asymmetry; the 1.86× "
        "shipped ratio is a conservative reading of Bail's effect."
    ),
    expected_naive_effect=(
        "Seeing the other side will humanise them and reduce out-party "
        "hostility — bringing the camps closer together."
    ),
    predicted_effect=(
        "Phase 8c §6: backfire on issue sorting, asymmetric per Bail "
        "2018. Republican-side agents (party 1) push 1.3× harder "
        "away from cross-cutting neighbours; Democratic-side agents "
        "(party 0) push 0.7×. The asymmetric multiplier doesn't move "
        "the population mean Δsep dramatically (both halves still "
        "drift apart, just at different rates), but per-party drift "
        "differs visibly. The actual macro bucket is re-measured by "
        "§11 — direction expected to remain backfire on issue sorting."
    ),
    param_bundle=_override(
        _S4_BASE,
        ("BacklashRepulsion", "strength", 0.05),
        ("BacklashRepulsion", "asymmetric", X1_ASYMMETRIC_RATIO),
    ),
    setup=None,
)


# --- X2 — "Fix the algorithm" ----------------------------------------

X2_FIX_ALGORITHM = Intervention(
    id="X2_fix_algorithm",
    label="Fix the algorithm",
    description=(
        "Reset social-media feeds to chronological/non-curated; reduce "
        "algorithmic recommendation. The flagship policy ask of the "
        "last decade."
    ),
    label_kind="intervention",
    effect_buckets={"issue_sorting": "null", "affect": "null"},
    citation=(
        "Guess et al. 2023 (Science 381:398); Nyhan et al. 2023 (Nature); "
        "Ross Arguedas et al. 2022 (Reuters Institute review)"
    ),
    expected_naive_effect=(
        "Without the algorithm amplifying our divisions, polarization "
        "will subside."
    ),
    predicted_effect=(
        "Null on both axes. The Meta/US 2020 Election Study switched "
        "users to chronological feeds for 3 months and found "
        "essentially no effect — polarization lives in the people and "
        "the network structure, not the feed."
    ),
    param_bundle=_override(
        _S4_BASE,
        ("BoundedConfidenceInfluence", "affect_weight", 0.0),
    ),
    setup=None,
)


# --- X3 — "Quit cable news" ------------------------------------------

def _x3_setup(engine):
    """Phase 8c §3 I1: zero each agent's partisan-cable outlet weights
    (MSNBC + Fox News) while leaving broadcast / local / partisan
    newspaper weights unchanged.

    Per the per-outlet rewrite (Phase 8c §3 E1) and Fork 3-B default
    (do not re-normalise), the agent's total media intake drops by the
    cable share; remaining outlets continue to pull at their original
    absolute weights. The centripetal pull of broadcast (which the
    Phase 7 X3 bundled-and-killed) survives; the centrifugal pull of
    partisan cable is removed. This is R1's "category-error" fix to
    the Phase 7 X3.
    """
    for a in engine.agents:
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
        "Disengage from partisan media: stop watching Fox / MSNBC, "
        "while keeping broadcast / local / general-news outlets in "
        "the diet. Models the empirical Levendusky 2013 / Allcott "
        "2020 finding that *partisan cable specifically* is the "
        "centrifugal force, distinct from broadcast / local."
    ),
    # Phase 8c §3 §11-blessed: null on both axes. Re-measured at
    # 12 seeds: Δsep = -0.0009 (SE 0.003), Δaff = -0.0137 (SE 0.001).
    # The Phase 7 X3 zeroed MediaConsumption.strength entirely,
    # bundling the centripetal broadcast pull with the centrifugal
    # partisan-cable pull and yielding a "backfire" bucket (Δsep =
    # +0.27 in that reading). The Phase 8c §3 X3 zeros only
    # MSNBC + Fox News weights; broadcast/local/WSJ/NYT keep their
    # original absolute pulls. Removing only the centrifugal piece
    # produces a tiny *helpful* nudge on issue sorting (well within
    # the null band) and a tiny shift on affect. Honest reading:
    # **partisan cable specifically does not, in this model, drive
    # macro-level polarization beyond what other forces are already
    # doing**. R1's category-error diagnosis is borne out by the
    # measurement.
    label_kind="intervention",
    effect_buckets={"issue_sorting": "null", "affect": "null"},
    citation=(
        "Levendusky 2013 (AJPS 57:611, partisan-cable centrifugal "
        "effect); Allcott, Braghieri, Eichmeyer & Gentzkow 2020 "
        "(AER 110:629, Facebook deactivation); Martin & Yurukoglu "
        "2017 (AER 107:2565, Fox News causal effect on Republican "
        "vote share). Phase 8c §3 D1 reframe: the Phase 7 X3 bundled "
        "all media into one diet target, collapsing the centripetal "
        "broadcast effect (Levendusky 2013) with the centrifugal "
        "partisan-cable effect; the §3 rewrite separates the two."
    ),
    expected_naive_effect=(
        "Without partisan cable driving people to extremes, the "
        "country will heal."
    ),
    predicted_effect=(
        "Null on both axes (Δsep = -0.001, Δaff = -0.014). The "
        "Phase 7 X3 zeroed ALL media exposure (Δsep = +0.27, "
        "backfire — but R1 diagnosed this as a category error: the "
        "old X3 was killing the centripetal broadcast pull along "
        "with the centrifugal cable pull). The Phase 8c §3 X3 zeros "
        "only the partisan-cable outlets; broadcast / local / WSJ / "
        "NYT keep their absolute pulls. Result: partisan cable's "
        "exit, on its own, doesn't measurably move party separation "
        "or out-party affect in this engine. The lay framing: "
        "'Turning off Fox / MSNBC doesn't, in this model, change "
        "the macro picture once you account for the moderating "
        "broadcast outlets that stay in your diet.'"
    ),
    param_bundle=_S4_BASE,  # no strength change — the setup zeros weights
    setup=_x3_setup,
)


# --- X4 — "Bipartisan dialogue programs" -----------------------------

def _x4_setup(engine):
    """Phase 8c §4 I4 — Levendusky 2021 *Our Common Bonds* shared-
    identity prime. Samples `X4_PRIME_SAMPLE_FRACTION` (20% per
    Vlad's Fork 2-b override) of agents; for each, sets
    `identity_weight_override = X4_PRIMED_IDENTITY_WEIGHT` (0.1) and
    `identity_prime_expires_at = engine.tick + X4_PRIME_DURATION_TICKS`
    (30 ticks ≈ 10 years).

    AffectiveUpdate reads `identity_weight_override` per-agent and
    uses that value in place of the rule-level `identity_weight` for
    the duration of the prime. After the expiry tick, the env-rule
    `IdentityPrimeExpiry` clears the override and the agent reverts
    to default identity-weighted valence.

    The mechanism replaces the Phase 6/7 X4 (cross-party dialogue
    pairs + affect reset). Sampling uses the same RNG seed
    (`X4_DIALOGUE_RNG_SEED = 42`) for cross-version reproducibility
    of §11 measurements; sample size adapts to the population.

    The shared-identity-prime reading is the literature-faithful
    Levendusky 2021 anchor (R1 polarization-expert recommendation +
    Vlad's Fork 2-b confirm). The Phase 7 dialogue-pairs anchor that
    actually matched Mutz 2006 / Allport 1954 has been removed; X4
    now models a temporary backgrounding of partisan identity under
    superordinate national-identity salience.
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
        if a.id in sampled:
            a.state.attrs["identity_weight_override"] = float(
                X4_PRIMED_IDENTITY_WEIGHT
            )
            a.state.attrs["identity_prime_expires_at"] = int(expiry_tick)


X4_BIPARTISAN_DIALOGUE = Intervention(
    id="X4_bipartisan_dialogue",
    label="Shared-identity priming program",
    description=(
        "A civic / educational program that temporarily makes a "
        "superordinate American identity salient for a fraction of "
        "the population — Levendusky 2021 'Our Common Bonds'. For "
        "the prime window, primed agents background their partisan "
        "identity when evaluating out-party encounters (lower "
        "identity_weight in the affect-formation formula). "
        "Operationalises the experimental literature's finding that "
        "shared-identity primes reduce out-party hostility for the "
        "duration of salience."
    ),
    # §11-blessed: null on both axes. Re-measured at 12 seeds:
    # Δsep = -0.029 (SE 0.003), Δaff = -0.013 (SE 0.001). The
    # 20% × 30-tick prime is too small to move macro metrics
    # meaningfully — exactly what Levendusky 2021 reports
    # experimentally (modest individual-level effects, small
    # population-level effects). Honest reading: a targeted civic
    # program scaled to 20% of the population for 10 years
    # backgrounds partisan identity for the primed minority, but
    # the macro shift is below the null threshold. (X4's intended
    # broader rollout — population-wide priming — would be a
    # different intervention; Phase 8d candidate.)
    label_kind="intervention",
    effect_buckets={"issue_sorting": "null", "affect": "null"},
    citation=(
        "Levendusky 2021 (Our Common Bonds: Cultivating National "
        "Attachments in Polarized America); Transue 2007 (AJPS "
        "51:78); Wright & Esses 2017 — superordinate-identity priming "
        "experimental findings. Replaces the Phase 6/7 X4 "
        "dialogue-program mechanism (Mutz 2006 / Allport / Pettigrew "
        "& Tropp anchor) per R1 polarization-expert recommendation."
    ),
    expected_naive_effect=(
        "Reminding people they're all Americans first will bridge "
        "the partisan divide."
    ),
    predicted_effect=(
        "Re-implemented in Phase 8c §4 as Levendusky 2021 shared-"
        "identity prime. 20% of agents (Vlad's Fork 2-b override) "
        "get `identity_weight_override = 0.1` for 30 ticks (~10 "
        "years). The reduced identity-weight cuts the disagreement "
        "term and produces less coolness on every out-party "
        "encounter — for the primed minority, during the window. "
        "Population-level effect is measured by §11; Levendusky 2021 "
        "finds modest experimental effects, so a partial-or-null "
        "reading is expected. Actual bucket is set by measurement."
    ),
    param_bundle=_S4_BASE,
    setup=_x4_setup,
)


# --- X7 — "Correct the perception gap" -------------------------------

def _x7_setup(engine):
    """Phase 8c §4 I5 — Levendusky & Malhotra 2016 / Ahler & Sood 2018
    / Druckman et al. 2022 perception-gap correction. One-shot reset
    of every agent's `perceived_other_party` toward the actual env-
    level centroid for each out-party.

    The Americans-systematically-overestimate-out-party-extremity
    finding suggests that even brief presentation of accurate out-
    party median positions corrects misperception (the "perception
    gap" literature). X7 implements this as: for every agent that
    carries `perceived_other_party`, set the perceived position to
    the actual party centroid from `env.attrs["parties"]`.

    **Honest about scope:** X7 is a no-op for agents that don't
    carry `perceived_other_party`. In the pillar (Path A: pillar
    agents never seed perception), X7 has nothing to correct and
    the §11 release-phase bucket measures null on both axes. The
    meaningful X7 measurement is in the historical_arc scenario,
    where perception is seeded with extreme_bias = 0.25 at build
    and PerceptionUpdate runs at strength=0.01 between events. The
    pillar's null reading is honest about what the pillar models.
    """
    parties = engine.env.attrs.get("parties") or {}
    if not parties:
        return
    for a in engine.agents:
        perceived = a.state.attrs.get("perceived_other_party")
        if perceived is None:
            continue
        for party_id, centroid in parties.items():
            if party_id == a.state.attrs.get("party"):
                continue
            if party_id in perceived:
                perceived[party_id] = np.array(centroid, dtype=float)


X7_PERCEPTION_CORRECTION = Intervention(
    id="X7_perception_correction",
    label="Correct the perception gap",
    description=(
        "Civic / educational program presenting accurate out-party "
        "median positions to a population that systematically over-"
        "estimates the other side's extremity (the 'perception gap'). "
        "One-shot reset of perceived out-party centroids to the "
        "actual centroids."
    ),
    # §11-blessed: null on both axes (pillar release-phase
    # measurement). X7 in the pillar is a no-op — pillar agents
    # don't carry perceived_other_party (Path A bit-identity
    # discipline), so X7's setup finds nothing to reset. Measured
    # Δsep = -0.029, Δaff = -0.013 — identical to the
    # "no-intervention" natural drift during 200 ticks of release.
    # The meaningful X7 measurement is in the historical arc, where
    # agents carry biased perceptions; that historical measurement
    # is a Phase 8c §7 sensitivity / historical-arc result, not the
    # pillar-release bucket.
    label_kind="intervention",
    effect_buckets={"issue_sorting": "null", "affect": "null"},
    citation=(
        "Levendusky & Malhotra 2016 (Political Communication 33:283 — "
        "perception-gap correction reduces partisan animus); Ahler & "
        "Sood 2018 (J. of Politics 80:964); Druckman et al. 2022; "
        "More in Common 'Perception Gap' report 2018."
    ),
    expected_naive_effect=(
        "Showing people that the other side is less extreme than "
        "they think will reduce hostility."
    ),
    predicted_effect=(
        "New in Phase 8c §4. In the pillar release-phase (where "
        "agents don't model perception — Path A), X7 is a no-op and "
        "measures null/null. In the historical-arc scenario (where "
        "agents carry perceived_other_party with extreme_bias = 0.25 "
        "at build), X7 corrects the bias to actual centroids and "
        "AffectiveUpdate's d_iss term shrinks — producing measurable "
        "affect warming over the release window. The honest reading: "
        "X7's effect depends on whether the population HAS a "
        "perception gap to correct. In stylised pillar contexts, no. "
        "In empirically-calibrated historical contexts, yes."
    ),
    param_bundle=_S4_BASE,
    setup=_x7_setup,
)


# --- X5 — "Ranked-choice voting" -------------------------------------

def _x5_setup(engine):
    """Halve both party centroids toward [0, 0] AND halve every agent's
    personal `party_cue` (Phase 8a F'). The modelled effect of
    electoral reforms that remove the elite incentive to stake out
    extreme positions (ranked-choice voting, open primaries, PR).
    The causal chain is Hetherington 2001's (in reverse): elite
    moderation propagates to mass moderation — in the model, that
    requires moving both the env-level centroids AND each agent's
    individual elite cue toward the centre. Under Phase 8a F' the
    pillar's PartyPull pulls toward per-agent cues, so an X5 setup
    that touched only the env centroids would silently no-op for
    the pillar — that's exactly the regression Phase 8a's full-suite
    run caught.

    RCV doesn't erase party — it moderates elites — so we halve, not
    zero. The choice is the R3d judgment fork.
    """
    parties = engine.env.attrs["parties"]
    for pid in list(parties.keys()):
        parties[pid] = 0.5 * parties[pid]
    # Phase 8a fix: also halve each agent's personal cue. Without this,
    # PartyPull (now reading `party_cue` rather than the centroid)
    # ignores the env-level halving and X5's mechanism is a no-op for
    # the pillar's agents.
    for agent in engine.agents:
        cue = agent.state.attrs.get("party_cue")
        if cue is not None:
            agent.state.attrs["party_cue"] = 0.5 * cue
    # Keep the viz hint in sync — the dashboard re-renders party stars
    # from this entry.
    viz = engine.env.attrs.setdefault("viz", {})
    viz["party_centers"] = parties


X5_RANKED_CHOICE_VOTING = Intervention(
    id="X5_ranked_choice_voting",
    label="Ranked-choice voting",
    description=(
        "Electoral reform: ranked-choice ballots, open primaries, "
        "proportional representation. Removes the elite incentive to "
        "play to the extremes (FairVote, Unite America)."
    ),
    # §11-blessed: partial on issue sorting, null on affect.
    # Δsep = -0.14 (just shy of the -0.15 "real" threshold); Δaff =
    # -0.01 (noise on affect). Halving centroids (the modelled RCV
    # strength — R3d default) moves issue sorting meaningfully but
    # doesn't clear "real," and barely touches affect. This matches
    # Gidron, Adams & Horne 2020's cross-national finding: institutional
    # levers shift issue sorting more than affect. Doubling the
    # centroid pull (R3d "all the way") would likely cross "real" on
    # issue sorting — but that's a different intervention ("erase
    # party," not "moderate elites").
    label_kind="intervention",
    effect_buckets={"issue_sorting": "partial", "affect": "null"},
    citation=(
        "Hetherington 2001 (APSR 95:619); McCarty, Poole & Rosenthal "
        "2006 (Polarized America); Gidron, Adams & Horne 2020; "
        "McCoy & Somer 2019 (Annals of AAPSS)"
    ),
    expected_naive_effect=(
        "Reforming elections reduces the incentive for politicians to "
        "play to the extremes, and the mass public will follow."
    ),
    predicted_effect=(
        "Partial. With party centroids halved, PartyPull pulls toward "
        "more moderate centroids; party separation drops Δsep ≈ -0.14 "
        "over the release period — meaningful but not large. "
        "Ideological constraint barely moves (Δ ≈ -0.02): the "
        "*correlation* between party and issue holds even when the "
        "centroids shift. Affective polarization barely responds, as "
        "the cross-national evidence predicts (Gidron et al. 2020)."
    ),
    param_bundle=_S4_BASE,
    setup=_x5_setup,
)


# --- X6 — "Shared neighborhoods and workplaces" ----------------------

def _x6_setup(engine):
    """Add ``X6_NEW_INVOLUNTARY_PER_AGENT`` cross-party involuntary
    edges per agent (representing residential / workplace / civic
    institutional integration — military service, public schools,
    mixed neighborhoods, workplaces, religious congregations), AND
    reset every agent's out-party affect to 0.0.

    Phase 8c §2 (replaces Phase 7 edge-level mute mechanism):

    - The added edges are still tagged ``cooperative=True``. The
      cooperative-edge flag now triggers ``AffectiveUpdate``'s
      *positive-going* valence path (warming on cooperative
      encounters when warmth is above ``coop_positive_threshold``),
      not the negative-mute path.
    - The **negative-mute mechanism is now agent-level**
      (Pettigrew 2009 secondary-transfer): each participating agent's
      ``cooperative_share`` attribute is incremented by the count of
      new cooperative ties they receive divided by their post-X6
      total tie count, clipped to ``[0, 1]``. The agent-level mute
      applies to *every* out-party encounter (not just cooperative-
      edge ones), proportional to ``cooperative_share``.

    Sampling uses a fresh RNG (``X6_INSTITUTIONS_RNG_SEED``) so the
    §11 measurement is reproducible. The new ties also carry
    ``involuntary=True`` so ``TieRewiring`` cannot drop them — the
    institutional structure persists through any subsequent rewiring.
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
    # Track new cooperative-tie count per agent so we can compute
    # agent-level cooperative_share after the placement loop.
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
        # Both flags: involuntary (exempt from rewiring) + cooperative
        # (Phase 8c §2: triggers positive-going valence path in
        # AffectiveUpdate; the negative-mute is now agent-level
        # via cooperative_share, computed after placement below).
        net.add_edge(i, j, involuntary=True, cooperative=True)
        new_coop_count[i] += 1
        new_coop_count[j] += 1
        placed += 1
    # Phase 8c §2 E3: bump agent-level cooperative_share. Formula:
    # cooperative_share = (new coop ties) / (total ties post-X6),
    # clipped to [0, 1]. Agents who receive more new cooperative
    # ties relative to their tie count get more mute; well-connected
    # agents are diluted (which is the right reading — secondary
    # transfer is per-agent, not per-edge).
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
    # Reset every agent's out-party affect to 0.0 — the warm/cooperative
    # interpretation of contact hypothesis (Pettigrew & Tropp 2006:
    # contact under Allport's conditions roughly halves prejudice).
    # Under the Phase 8c §2 agent-level mute, this reset combines with
    # the cooperative_share bump above to give X6 its full punch:
    # immediate warmth recovery + reduced cooling rate going forward.
    for a in agents:
        affect = a.state.attrs.get("affect") or {}
        for other_party in list(affect.keys()):
            affect[other_party] = 0.0


X6_SHARED_INSTITUTIONS = Intervention(
    id="X6_shared_institutions",
    label="Shared neighborhoods and workplaces",
    description=(
        "Structural integration: mixed neighborhoods, integrated "
        "workplaces, public schools, military service, civic "
        "institutions (community sports leagues, religious "
        "congregations, PTAs). The contact-hypothesis lever."
    ),
    # §11-blessed (Phase 8c §2 re-measurement): null on issue sorting,
    # **real on affect**. Honest measurement under the Phase 8c §2
    # agent-level cooperative-share mute (Pettigrew 2009 secondary-
    # transfer) plus the cooperative-positive valence path: Δsep =
    # -0.04, Δaff = +0.235.
    #
    # The bucket flipped from "backfire" (Phase 7 edge-level mute,
    # Δaff = -0.23) to **"real"** (Phase 8c §2 agent-level mute,
    # Δaff = +0.235) under the same Pettigrew & Tropp 2006 anchor
    # value (`cooperative_mute = 0.5`). The mechanism change is what
    # moved the result, not a knob retune: agent-level mute applies
    # to EVERY out-party encounter of participating agents (not just
    # encounters on the new cooperative edges), and the cooperative-
    # positive path adds small per-encounter warming on those edges
    # when warmth is above the threshold. Together the two effects
    # reverse X6's affect trajectory at the population level.
    #
    # Honest literature reading: this is the Pettigrew 2009 secondary-
    # transfer interpretation of intergroup contact (contact reduces
    # overall prejudice formation, not just toward contact targets) —
    # which the reviewers (R1 polarization expert, R2 ABM/math expert)
    # both argued for in Phase 8b/c review. The Phase 7 edge-level
    # interpretation was the conservative reading that shipped first;
    # Phase 8c §2 implements the broader reading.
    #
    # Null on issue sorting (Δsep = -0.04): F1 anchoring + active
    # PartyPull still tether each agent to its starting side; the
    # affect channel recovers but position-level sorting doesn't
    # unwind. Gidron, Adams & Horne 2020: affect / prejudice is what
    # contact moves; institutional levers move issue sorting more.
    label_kind="intervention",
    effect_buckets={"issue_sorting": "null", "affect": "real"},
    citation=(
        "Allport 1954 (The Nature of Prejudice); Pettigrew & Tropp "
        "2006 (JPSP 90:751, meta-analysis: r ≈ -0.21 across 515 "
        "studies); Pettigrew 2009 (Secondary transfer effect of "
        "intergroup contact, Social Psychology 40:55); Mutz 2006 "
        "(Hearing the Other Side); Brown & Enos 2021 (Nature Human "
        "Behaviour, residential partisan segregation — reverse "
        "direction)"
    ),
    expected_naive_effect=(
        "Living, working, and playing alongside the other side — in "
        "ordinary non-political settings — will heal the divide where "
        "political argument cannot."
    ),
    predicted_effect=(
        "Real on affect (Δaff = +0.235; the agent-level cooperative "
        "mechanism — Pettigrew 2009 secondary-transfer — reduces "
        "per-encounter coolness on every out-party encounter for "
        "participating agents, AND cooperative-edge encounters add "
        "small warming when warmth is not yet extreme). Null on "
        "issue sorting (Δsep = -0.04) — F1 anchoring + active "
        "PartyPull tether each agent to its starting side. The lay "
        "framing: 'Building shared institutions doesn't change what "
        "people believe, but it does change how they feel about each "
        "other — exactly what the contact-hypothesis literature "
        "predicts.'"
    ),
    param_bundle=_S4_BASE,
    setup=_x6_setup,
)


# --- The library -------------------------------------------------------

INTERVENTIONS_PHASE6: tuple[Intervention, ...] = (
    X1_SHOW_OTHER_SIDE,
    X2_FIX_ALGORITHM,
    X3_QUIT_CABLE_NEWS,
    X4_BIPARTISAN_DIALOGUE,
    X5_RANKED_CHOICE_VOTING,
    X6_SHARED_INSTITUTIONS,
    X7_PERCEPTION_CORRECTION,
)
