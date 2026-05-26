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

# X4 — number of cross-party dialogue pairs (~16% of n=250 at the
# default agent count; Levendusky 2021's participant-level effect at
# realistic real-world participation rates). RNG seed is fixed so the
# §11 measurement is reproducible across runs.
N_DIALOGUE_PAIRS = 20
X4_DIALOGUE_RNG_SEED = 42

# X6 — number of new cross-party *involuntary* (kin/workplace/neighborhood)
# ties added per agent on intervention. Quadruples the F3 stratum
# (default INVOLUNTARY_PER_AGENT = 1 → effective 4 after X6). Represents
# the contact-hypothesis literature: structural shared-life contact via
# mixed neighborhoods, workplaces, public schools, military service,
# civic institutions (Allport 1954; Pettigrew & Tropp 2006; Mutz 2006).
X6_NEW_INVOLUNTARY_PER_AGENT = 3
X6_INSTITUTIONS_RNG_SEED = 43


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
        "humanise them."
    ),
    label_kind="intervention",
    # Phase 7 two-axis labels — blessed by §11 measurement.
    effect_buckets={"issue_sorting": "backfire", "affect": "null"},
    citation=(
        "Bail et al. 2018 (PNAS 115:9216); Levendusky 2021; Mutz 2006"
    ),
    expected_naive_effect=(
        "Seeing the other side will humanise them and reduce out-party "
        "hostility — bringing the camps closer together."
    ),
    predicted_effect=(
        "Backfire on issue sorting (Δsep ≈ +0.50). Exposure to opposing "
        "views *increases* polarization for already-hostile agents "
        "(Bail's headline finding) — the R1 affect-gate fires reliably "
        "because post-S4 affect is well below -0.3. Negligible effect "
        "on affect (Δaff ≈ -0.01, noise)."
    ),
    param_bundle=_override(
        _S4_BASE,
        ("BacklashRepulsion", "strength", 0.05),
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

X3_QUIT_CABLE_NEWS = Intervention(
    id="X3_quit_cable_news",
    label="Quit cable news",
    description=(
        "Disengage from partisan media: stop watching Fox/MSNBC, "
        "deactivate social media, switch to balanced sources."
    ),
    # §11-blessed: backfire on issue sorting, null on affect.
    # Δsep = +0.27 (worsens issue sorting); Δaff = -0.01 (noise on
    # affect axis). Honest finding — at the polarized end-state,
    # removing the partisan-media force *worsens* sorting because the
    # modeled US media diet pulls each agent toward `diet_target` (the
    # weighted-mean outlet position), which for most diets sits
    # **inward** of the party centroids (Phase 2 §6 calibration note:
    # "media is a mild *centering* force here"). Once that centripetal
    # pull disappears, PartyPull drags the camps further apart. The lay
    # framing: "Quitting cable news at the *polarized end-state*
    # doesn't help — it removes the one thing quietly pulling people
    # toward common ground."
    #
    # LIMITATION (Phase 7 sensitivity check): this backfire reading
    # depends on the calibration of `US_MEDIA_OUTLETS_2024` in
    # `abm/core/outlets.py` — specifically that the weighted-mean
    # diet target sits inward of the party centroids. A roster shifted
    # more extreme (e.g. Fox at [0.85, 0.65] instead of [0.6, 0.4])
    # would move the diet target outward of the party centroids; X3
    # would then become null or partial. The result here is real for
    # *the 2024 US media landscape as the model encodes it*, not a
    # universal claim about partisan-media effects.
    label_kind="intervention",
    effect_buckets={"issue_sorting": "backfire", "affect": "null"},
    citation=(
        "Allcott, Braghieri, Eichmeyer & Gentzkow 2020 (AER 110:629); "
        "Levendusky 2013 (AJPS 57:611, reverse direction)"
    ),
    expected_naive_effect=(
        "Without partisan media driving people to extremes, the "
        "country will heal."
    ),
    predicted_effect=(
        "Backfire at the polarized end-state. The modeled US media "
        "diet pulls inward of the party centroids (centrist outlets "
        "dilute partisan ones), so removing it lets PartyPull drag "
        "the camps further apart — Δsep ≈ +0.27 over a release period."
    ),
    param_bundle=_override(
        _S4_BASE,
        ("MediaConsumption", "strength", 0.0),
    ),
    setup=None,
)


# --- X4 — "Bipartisan dialogue programs" -----------------------------

def _x4_setup(engine):
    """Pair `N_DIALOGUE_PAIRS` cross-party agents with a new voluntary
    tie and reset their out-party affect to 0.0 — the "warm framing"
    that distinguishes Levendusky's dialogue-program effect from Bail's
    cold-exposure backfire.

    Reads agents from the engine, samples participants using a fresh
    RNG (independent of the engine's stream — these are *external*
    facilitators), pairs them across party (one left + one right per
    dialogue), and writes to env.attrs["network"] + agent affect.

    Participants are sampled at a fixed seed for reproducibility of the
    §11 measurement; the participating *agent ids* are constant across
    seeds (but the parties / positions of those ids vary, so the
    intervention's effect still has per-seed variance).
    """
    rng = np.random.default_rng(X4_DIALOGUE_RNG_SEED)
    net = engine.env.attrs["network"]
    agents = engine.agents
    by_id = {a.id: a for a in agents}
    left = [a.id for a in agents if a.state.attrs.get("party") == 0]
    right = [a.id for a in agents if a.state.attrs.get("party") == 1]
    if not left or not right:
        return
    k = min(N_DIALOGUE_PAIRS, len(left), len(right))
    # Sample without replacement from each side.
    li = rng.choice(left, size=k, replace=False)
    ri = rng.choice(right, size=k, replace=False)
    for i, j in zip(li, ri):
        if not net.has_edge(int(i), int(j)):
            net.add_edge(int(i), int(j), involuntary=False)
        # Warm framing — reset out-party affect to neutral. Don't write
        # *warmer* than 0 (Finkel et al. 2020: in-party warmth is
        # roughly stable; honest about modest real-world findings).
        by_id[int(i)].state.attrs["affect"][1] = 0.0
        by_id[int(j)].state.attrs["affect"][0] = 0.0


X4_BIPARTISAN_DIALOGUE = Intervention(
    id="X4_bipartisan_dialogue",
    label="Bipartisan dialogue programs",
    description=(
        "Structured cross-party conversations: Braver Angels, More in "
        "Common, Living Room Conversations, depolarization weekends."
    ),
    # §11-blessed: null on both axes. Spec draft predicted partial;
    # the measurement shows Δsep = -0.02 and Δaff = -0.004 — both
    # below the 0.05 null threshold. 20 pairs (~16% participation at
    # n=250) is too small a share of the population to move macro
    # metrics on either axis, matching Levendusky 2021's own finding:
    # real effects at the *participant* level, modest at the population
    # level.
    label_kind="intervention",
    effect_buckets={"issue_sorting": "null", "affect": "null"},
    citation=(
        "Levendusky 2021 (Our Common Bonds); Mutz 2006 (Hearing the "
        "Other Side); More in Common / Braver Angels program reports"
    ),
    expected_naive_effect=(
        "Sitting people down with the other side in a structured "
        "setting will rebuild trust at the population level."
    ),
    predicted_effect=(
        "Null at the population level. Among the ~16% of agents who "
        "participate, affect cools and cross-cutting ties grow — "
        "Levendusky 2021's real participant-level effect. But that "
        "minority can't shift party separation: measured Δsep ≈ -0.02 "
        "over the release period. The intervention works for the "
        "people in the room and almost nobody else."
    ),
    # X4 doesn't change any rule strengths — it works entirely through
    # the setup hook (structural network and affect edit).
    param_bundle=_S4_BASE,
    setup=_x4_setup,
)


# --- X5 — "Ranked-choice voting" -------------------------------------

def _x5_setup(engine):
    """Halve both party centroids toward [0, 0] — the modelled effect
    of electoral reforms that remove the elite incentive to stake out
    extreme positions (ranked-choice voting, open primaries, PR). The
    causal chain is Hetherington 2001's (in reverse): elite moderation
    leads mass sorting.

    RCV doesn't erase party — it moderates elites — so we halve, not
    zero. The choice is the R3d judgment fork.
    """
    parties = engine.env.attrs["parties"]
    for pid in list(parties.keys()):
        parties[pid] = 0.5 * parties[pid]
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

    Phase 7: the added edges are tagged ``cooperative=True``. This
    activates ``AffectiveUpdate.cooperative_mute`` (default 0.5) on
    out-party encounters across these edges — the Allport-conditions
    abstraction that distinguishes prejudice-reducing contact (X6)
    from prejudice-amplifying exposure (X1's BacklashRepulsion path).
    Existing F3 baseline involuntary edges are NOT cooperative — the
    literature is explicit that contact alone is insufficient.

    Sampling uses a fresh RNG (`X6_INSTITUTIONS_RNG_SEED`) so the
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
        # (Allport conditions → AffectiveUpdate mutes negative valence
        # on this edge).
        net.add_edge(i, j, involuntary=True, cooperative=True)
        placed += 1
    # Reset every agent's out-party affect to 0.0 — the warm/cooperative
    # interpretation of contact hypothesis (Pettigrew & Tropp 2006:
    # contact under Allport's conditions roughly halves prejudice).
    # In Phase 7 the cooperative-mute mechanism keeps subsequent
    # cross-party encounters on these new edges from re-cooling affect
    # at full speed.
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
    # §11-blessed: null on issue sorting, **backfire on affect** —
    # despite the Phase 7 cooperative-conditions mechanism. Honest
    # measurement under COOPERATIVE_MUTE = 0.5 (Pettigrew & Tropp
    # 2006-anchored): Δsep = -0.04, Δaff = -0.23.
    #
    # The cooperative mute reduced X6's affect backfire by ~12%
    # (from -0.26 without the mute to -0.23 with it — a real but
    # insufficient improvement). The mechanism: edge-level mute halves
    # per-encounter coolness on the new institutional ties, but X6
    # also *quadruples* the cross-party tie count (+0.25 XC fraction),
    # so total volume of cross-party encounters per tick is up.
    # Volume × half-strength still exceeds baseline drift across 200
    # ticks; accumulated animus deepens rather than recovers.
    #
    # This is a defensible literature reading of Pettigrew & Tropp:
    # contact reduces *per-encounter* prejudice formation but doesn't
    # reverse population-level accumulated animus on its own. The
    # cooperative-mute mechanism is a conservative edge-level
    # interpretation; a less conservative alternative (Pettigrew 2009
    # secondary-transfer-effect — agent-level animus reduction
    # generalising across out-groups) would be more aggressive and
    # might tip X6 into partial or real on affect. That alternative is
    # documented in `phase7_spec.md` §5.1 as a sensitivity item, NOT
    # implemented here — per the "do not tune past the literature-
    # anchored value to chase a bucket" discipline.
    label_kind="intervention",
    effect_buckets={"issue_sorting": "null", "affect": "backfire"},
    citation=(
        "Allport 1954 (The Nature of Prejudice); Pettigrew & Tropp "
        "2006 (JPSP 90:751, meta-analysis: r ≈ -0.21 across 515 "
        "studies); Mutz 2006 (Hearing the Other Side); Brown & Enos "
        "2021 (Nature Human Behaviour, residential partisan "
        "segregation — reverse direction)"
    ),
    expected_naive_effect=(
        "Living, working, and playing alongside the other side — in "
        "ordinary non-political settings — will heal the divide where "
        "political argument cannot."
    ),
    predicted_effect=(
        "Backfire on affect (the cooperative-conditions mechanism — "
        "edge-level mute on Allport-conditions ties — reduces but "
        "does not reverse animus accumulation in this engine). Null "
        "on issue sorting — F1 anchoring + active PartyPull tether "
        "each agent to its starting side. The lay framing: 'Building "
        "shared institutions exposes people to the other side, but "
        "even cooperative contact doesn't on its own reverse the "
        "animus already accumulated — and the increased exposure "
        "produces more cooling events than the cooperative framing "
        "mutes.'"
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
)
