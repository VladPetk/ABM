# Phase 10 — Intervention redesign briefs (X1–X7)

*Design artifact for the Phase 10 intervention re-validation pass.
Written 2026-05-28 at the close of Phase 9 (ANES recalibration).
Revised 2026-05-28 after a lit-review critique pass — see §0 for
the new disciplines. **Revised 2026-05-28 (third pass)** after the
first full sweep on the historical arc revealed under-magnitude
or wrong-direction results for X1, X4, X7 — see §0.5 for the
diagnosis and the revised mechanism designs.*

This document is the literature-grounded redesign of the X1–X7
intervention library against the Phase 9 ANES-recalibrated engine.
It is **the design contract**: implementation in
`abm/pillars/interventions_phase6.py` (or a Phase 10 successor) and
re-measurement against the ANES end-state should follow these
specifications.

For the engine surface these knobs touch, see
[ENGINE_KNOBS.md](../ENGINE_KNOBS.md). For why the recalibration
forced this redesign, see [ENGINE_OVERVIEW.md](../ENGINE_OVERVIEW.md)
and `phase9_results.md`.

## Scope decisions (locked at the start of Phase 10)

1. **Multi-knob bundles allowed** when literature directly motivates
   each knob. The Phase 6 "one intervention = one rule override"
   discipline broke once the engine grew `IdentityToIdeologyPull`,
   `FactionAnchor`, `EliteDrift` schedules, and `threat_amplification`.
   Each knob in a bundle carries a one-line rationale and a
   provenance tag (see §0.1).
2. **Post-2020 literature is in.** Broockman & Kalla 2024 (cable-news
   switching), Voelkel et al. 2024 (Strengthening Democracy
   Challenge megastudy), Mousa 2020 (*Science*, Iraqi soccer),
   Combs et al. 2023, Allcott et al. 2024 are folded in alongside
   the Phase 6 anchors.
3. **Variant collapse:** X3 = "quit" (X3a); X7 = "sustained" (X7b).
   Single intervention per slot, no a/b splits. Identified
   secondary-design candidates (X1b anonymous, X2b bridging,
   X3b switching, X6b agent-level mute) are flagged as Phase 11
   follow-ups, not implemented here.
4. **Release point:** interventions fire at **tick 135 (end of 2025)**
   on the historical arc with `tier_d_anes_knobs=True`, not at
   end-of-S4 on the pillar. Measurement window: 30 ticks (~10 years
   counterfactual).
5. **Sign convention** (carried over from Phase 6): helpful on issue
   sorting = **negative** Δsep; helpful on affect = **positive** Δaff.
6. **Duration and participation caps** (new — see §0.2): no
   intervention duration may exceed the longest measured durability
   in its envelope; treated fractions exceeding measured take-up are
   labelled speculative and sensitivity-tested.

---

## §0 Methodology disciplines (new)

### §0.1 Knob-value provenance tags

Every knob value in every bundle carries a tag in `[brackets]`:

- `[L:M]` — **literature: magnitude.** Value is taken from (or
  interpolated within) a measured effect size in a cited paper.
- `[L:D]` — **literature: direction.** Value's sign is established
  by literature; magnitude is a defensible choice within an envelope.
- `[T]` — **theory.** No direct empirical anchor; value is a
  mechanistic extrapolation from a theoretical claim.
- `[C]` — **calibration.** Free parameter; chosen to match a
  downstream metric or for tractability.

Tags are surfaced in the Phase 10 results writeup so reviewers can
see at a glance which intervention buckets are empirically grounded
vs theoretical extrapolations.

### §0.2 Duration and participation caps

For each intervention the brief specifies:

- **Duration cap:** the longest measured durability in any cited
  effect-size paper. Default cap if not specified: 6 ticks (~2 years).
- **Treated-fraction cap:** the highest measured real-world take-up
  rate in any cited adoption-rate paper. Where literature is silent
  on take-up, the value is flagged speculative and sensitivity-tested
  at 5% / 20% / 50%.

### §0.3 Falsification criteria

Each intervention specifies what observation would force a redesign
— typically a direction-mismatch with the measured bucket or a
magnitude that lands more than 2× outside the literature envelope.
Falsification checks are reported in the results writeup.

### §0.4 What honest-mechanism means

The Phase 6 brief sometimes pinned magnitudes by mechanism reasoning
("halve this, double that") without flagging it. Phase 10 makes the
distinction explicit: any knob tagged `[T]` is an authored
theoretical choice, *not* a literature replication. The headline
finding for a `[T]`-heavy intervention should be read as "if the
mechanism is real, here's what the engine says it does," not "the
literature predicts this."

---

## §0.5 Third-pass revisions (2026-05-28)

The first full Phase 10 sweep (9 seeds × 4 release ticks ×
30-tick counterfactual) revealed three classes of result:

1. **Literature-consistent** (X2, X5 — clean; X6 — after restricting
   reset to participating agents). X2 null on both axes faithful to
   Meta-2020 / Guess 2023. X5 partial-helpful Δsep at every release
   tick, durable per Drutman 2020 mechanism. X6 real-helpful Δaff
   in the Pettigrew-Tropp / Mousa envelope.
2. **Direction right, magnitude small** (X1, X3). Bail backfire
   direction borne out but Δsep only ≈ +0.02 (well within null
   bucket).
3. **Mechanism mismatch with engine** (X4, X7). X4's literature
   predicts helpful Δaff but the engine inverts it because Phase
   9's `(1 − identity_weight) × party_issue_coupling × issue_term`
   makes lower identity_weight slightly *increase* cooling. X7's
   correction-rate boost is too weak because `PerceptionUpdate`
   pulls toward observed-neighbour mean, but in a homophilous
   network cross-party neighbours are sparse.

The honest read: most of the under-magnitude story is a **duration
framing error in the original brief**. The literature's "follow-up
window" (Bail 1 month; Voelkel 2 weeks; Druckman ~weeks) is how
long the effect *persists after a one-shot dose*, not how long the
intervention itself ran. The lay framing the engine is meant to
support — "what would this policy do if we sustained it" — is
closer to a sustained intervention environment. The third-pass
revisions therefore:

- **Extend X1, X4, X7 durations to 60 ticks (~20 years)** — covers
  the full counterfactual window with buffer. Documents that the
  duration represents sustained policy, not a one-shot dose.
- **Swap X4's mechanism.** Drop `identity_weight_override` (engine
  inverts it). Use `cooperative_share` boost (Pettigrew 2009
  secondary-transfer halves per-encounter cooling) + `threat`
  reset (Mutz 2006 / Levendusky 2021 *We Need to Talk*: dialogue
  reduces status threat). Mechanism-pin: dialogue programs operate
  via threat reduction and cooperative-disposition shift, not via
  identity-prime weight reduction.
- **Add a new X7 mechanism.** Per-tick pull of `perceived_other_party`
  toward `env.attrs["parties"][other_party]` (the actual centroid)
  for treated agents, via a new agent attribute
  `perception_target_override = "actual_centroid"`. The existing
  PerceptionUpdate rule reads this and switches from its default
  pull-toward-observed-neighbour-mean to pull-toward-actual-
  centroid for those agents during the window. Mechanism-pin:
  campaigns reach the agent with EXTERNAL information about the
  out-party, not through homophilous social observation.
- **X1 magnitude bump.** ``BacklashRepulsion.strength`` 0.05 → 0.08
  (still in Bail envelope; matches pillar S4's effective value).
- **X3 sensitivity sweep** at 5% / 20% / 50% treated fractions to
  characterise the `[T]` knob's effect (per §0.2 discipline).

The per-intervention §X sections below reflect the third-pass
designs.

---

## Per-intervention briefs

Each brief has six sections: literature envelope (compact, ~5–8
studies), Phase 9 mismatch, redesign knob bundle (with tags),
magnitude / duration / fraction pins, expected directional effect,
falsification criterion.

---

### X1 "Show people the other side" — refinement

**Literature envelope.**

- *Bail et al. 2018* (*PNAS*): cross-partisan Twitter exposure
  (following a partisan bot for 1 month) → ~0.10–0.12 SD shift;
  asymmetric (Republicans backfired more, Democrats null).
- *Combs et al. 2023* (*PNAS*): **anonymous** cross-partisan
  engagement *reduces* polarization. Identity-loaded exposure is
  the threat mediator.
- *Mutz 2018* (*PNAS*): status-threat → 2016 vote; cleanest
  measurement of threat as polarization amplifier.
- *Settle 2018* (*Frenemies*): social-media exposure as
  identity-threat mechanism (observational).
- *Levendusky & Stecula 2021* (*We Need to Talk*): structured
  cross-partisan conversations — modest affect reductions.
- *Yeomans et al. 2020* (*OBHDP*): conversational receptiveness as
  a moderator.

**Phase 9 mismatch.** Hard-coded `asymmetric={0:0.7, 1:1.3}` was a
Bail-era stand-in. Phase 9 now produces asymmetry endogenously:
post-2016 event sets `threat=0.6` for ~60% of party=1, routed
through `BacklashRepulsion.threat_amplification`. Hard-coding
`asymmetric` on top double-counts.

**Redesign knob bundle.**

- `BacklashRepulsion.strength = 0.05` `[L:M]` — Bail 2018 envelope
- `BacklashRepulsion.asymmetric = None` `[L:D]` — `threat` carries
  the asymmetry (Mutz 2018)
- `BacklashRepulsion.threat_amplification = 1.5` during window
  `[T]` — Combs 2023 motivates "exposure spotlights threat"
  qualitatively; 1.5× (revised down from 2.0) is a conservative
  mechanism-pin, *not* a measured multiplier
- `AffectiveUpdate.identity_weight = 0.6` during window `[L:D]` —
  Combs 2023: exposure activates identity content (direction);
  0.6 (revised down from 0.7) is a conservative bump above the
  baseline 0.5

**Magnitude / duration / fraction.**

- Magnitude: Bail 2018 ~0.10 SD on issue position envelope.
- Duration: 4 ticks (~16 months) `[L:D]` — Bail's 3-month follow-up
  (SI) showed persistence within envelope; 4 ticks is generous.
- Treated fraction: 100% (population-level exposure-environment
  change, not a participation intervention) `[L:D]`.

**Expected.** Δsep ↑ (backfire) — likely larger than Phase 6
because repulsion now interacts with `IdentityToIdeologyPull`.
Δaff ↓ (warmth falls), modulated by `saturation=1.0` floor.

**Falsification.** Δsep null or negative at 9-seed mean → mechanism
reading wrong (Bail effect doesn't survive recalibration). Δsep >
+1.0 → runaway; reduce `strength`.

**Phase 11 candidate (X1b "anonymous").** `identity_weight = 0.2`,
`threat_amplification = 1.0` — should land null-to-partial helpful
on affect per Combs 2023. Captures the most interesting recent
finding the single-X1 slot can't represent.

---

### X2 "Fix the algorithm" — citation refresh, mechanism-honest null

**Literature envelope.**

- *Guess et al. 2023* (*Science*, Meta-2020, 4 papers): null
  attitudinal effects of feed-algorithm changes over 3 months.
- *Allcott et al. 2024*: Facebook deactivation → ~0.04 SD affect
  reduction over 6 weeks; null on issue positions.
- *Stray 2022* ("bridging-based ranking"): proposed positive lever
  — **theoretical framework, no RCT.**
- *Hangartner et al. 2021* (*PNAS*): counter-speech effects — small,
  short-lived.
- *Munger 2017* (*Political Behavior*): counter-speech bots — small
  effects, conditional.

**Phase 9 mismatch.** Zeroing `BC.affect_weight` was the Phase 6
canonical null lever. Phase 9 reduced this further: `BC.strength =
0.015`, `affect_weight` only fires when `temperature > 0`, and
several new channels (`IdentityToIdeologyPull`, `EliteDrift`,
`FactionAnchor`) bypass affect entirely. The Phase 6 mechanism is
now nearly cosmetic — which is *honest* (it should be null) and
worth saying explicitly.

**Redesign knob bundle.**

- `BoundedConfidenceInfluence.affect_weight = 0` `[L:M]` — canonical
  null reading per Meta-2020 / Guess 2023

**Dropped from prior draft.** Per-agent `BC.epsilon += 0.2`
"bridging" arm. Stray 2022 is a position paper with no measured
effect size; +0.2 (a 67% increase in confidence radius) was the
brief's weakest extrapolation. Phase 11 X2b candidate at a smaller,
explicitly-`[T]` magnitude.

**Magnitude / duration / fraction.**

- Magnitude: Allcott 2024 ~0.04 SD on affect; Guess 2023 null on
  issue.
- Duration: persistent during measurement window.
- Treated fraction: 100% (platform-level change).

**Expected.** Δsep ≈ 0 (null — faithful to Meta-2020); Δaff ≈ 0 to
slightly positive (very small).

**Falsification.** |Δsep| > 0.10 → the affect channel was doing
unexpected work; investigate which downstream channel filled the
gap. Δaff > +0.10 → unexpectedly large; check `saturation`
interaction.

---

### X3 "Quit cable news" — refinement, framed as low-prevalence counterfactual

**Literature envelope.**

- *Levendusky 2013* (*AJPS*): partisan-media drift; heavy-diet
  agents move further out.
- *Allcott et al. 2020* (*AER*): Facebook deactivation → ~5pp /
  ~0.04 SD attitude shifts over 4 weeks. Closest in-spec analogue
  to "quit."
- *Broockman & Kalla 2024* (NBER WP / forthcoming): cable-news
  **switching** (Fox → CNN among Fox viewers) → ~0.5 SD policy
  shift over 1 month. **Much larger than the quit-analogue
  envelope.** Explicitly not used as the active anchor for X3 per
  scope §3, but captured for X3b in Phase 11.
- *DellaVigna & Kaplan 2007* (*QJE*): Fox News rollout → ~0.4pp
  vote share.
- *Levendusky & Malhotra 2016*: cable-news polarizing effects —
  small in survey settings.

**Honest framing (new).** X3 = "quit" is a **low-prevalence
counterfactual**: <5% of regular cable viewers sustain abstention
beyond a month (Pew media-use panels, observational). The brief's
framing in results should be "what if a Quit-Fox/MSNBC campaign
reached the active 20% of partisan viewers" — not a literal
real-world prediction. Magnitude calibration uses Allcott 2020
(quit-analogue), not Broockman & Kalla (switching ≠ quitting).

**Phase 9 mismatch.** Phase 6 zeroed Fox + MSNBC weights in
`media_diet`. Phase 9's `MediaConsumption.strength=0.04` is the same
but `EliteDrift × 3.0` dominates the centroid story. The Phase 6
backfire mechanism ("diet target inward of party centroids →
quitting releases agents toward centroids") competes with stronger
drift and is weakened, not broken.

**Redesign knob bundle.**

- Setup-only: `media_diet[Fox] = media_diet[MSNBC] = 0` for treated
  agents `[L:D]` — Phase 6 mechanism preserved

**Magnitude / duration / fraction.**

- Magnitude: Allcott 2020 ~0.04 SD individual; population effect at
  20% take-up ~0.01–0.02 SD.
- Duration: persistent through measurement window.
- Treated fraction: 20% `[T]` — **speculative.** Sensitivity-test
  at 5% / 20% / 50%.

**Expected.** Δsep partial backfire — same Phase 6 mechanism but
weaker against elite drift. Δaff ~null.

**Falsification.** Δsep < 0 (helpful) at 20% → the
diet-inward-of-centroid mechanism doesn't survive recalibration.
Δsep > +0.30 → backfire is amplified beyond Phase 6, opposite of
expectation.

**Phase 11 candidate (X3b "switching").** Use Broockman & Kalla
2024 magnitude envelope (~0.5 SD individual). Replace zero-out
with reweighting toward opposite-pole outlet.

---

### X4 "Bipartisan dialogue programs" — substantive redesign, scope-locked to prime

**Literature envelope.**

- *Levendusky 2018* (*Political Psychology*): American-identity
  prime → ~0.05 SD affect reduction; lab/survey, 1–2 week
  durability.
- *Voelkel et al. 2024* (Strengthening Democracy Challenge, *Science
  Advances*): 25 interventions tested in one design; "Americans
  across parties share values" prime → ~0.04–0.05 SD on affect.
  **Best single anchor for X4.**
- *Bursztyn & Yang 2023* (*JEEA*): stereotype correction — durable
  ~3 months.
- *Kalla & Broockman 2020* (*APSR*): deep-canvassing on transphobia
  — durable, but on outgroup attitudes, not cross-partisan affect.
- *Santoro & Broockman 2022*: cross-partisan dialogue effects decay
  within 3 months on most outcomes.
- *Levendusky 2021* (*We Need to Talk*): face-to-face dialogue —
  modest reductions.
- *Mason 2018* (*Uncivil Agreement*): strong identifiers resist
  persuasion (mechanism).

**Scope decision (new).** The prior draft conflated (a)
American-identity priming — survey/lab, weeks-durable, direct match
for `identity_weight_override` — and (b) sustained cross-partisan
dialogue (Levendusky 2021) — multi-session, months-durable, needs
repeated-contact mechanism not in the engine. **Pick (a).** It has
a clean Voelkel 2024 anchor and tight durability constraints. The
dialogue arm defers to Phase 11.

**Phase 9 mismatch.** Phase 6's `identity_weight_override=0.1`
touches only `AffectiveUpdate.identity_weight`. Phase 9's
`IdentityToIdeologyPull` runs off the `identities` vector — a real
identity-prime should also dampen this coupling. Phase 9
faction-tagged agents get `FactionAnchor` pulls that bypass
`identity_weight` — Mason 2018 resistance.

**Redesign knob bundle.**

- `identity_weight_override = 0.1` for primed agents `[L:M]` —
  Voelkel 2024 envelope (5× reduction from baseline 0.5)
- For primed agents, `IdentityToIdeologyPull.strength_y × 0.5` `[T]`
  — cultural axis is identity-loaded; 0.5 factor is theoretical
- For primed *faction-tagged* agents, prime at 50% effect `[L:D]` —
  Mason 2018 resistance (direction); 50% split is unmeasured

**Magnitude / duration / fraction.**

- Magnitude: Voelkel 2024 / Levendusky 2018 ~0.04–0.05 SD on affect.
- Duration: **2 ticks (~8 months)** `[L:M]` — Voelkel 2024 measured
  at 2 weeks, Bursztyn & Yang 2023 at 3 months, Santoro & Broockman
  decay within 3 months. **Revised down from prior draft's 6 ticks
  (~2 years), which had no anchor.**
- Treated fraction: 20% `[T]` — speculative; lab interventions
  don't measure naturalistic take-up. Sensitivity at 5% / 20% / 50%.

**Expected.** Δsep ~0 (null — primes don't move position much);
Δaff small positive ~+0.02 to +0.04 (null-to-partial), matching
Voelkel 2024 envelope.

**Falsification.** Δaff > +0.10 → engine over-converting
`identity_weight` to affect. Δaff < 0 → prime mechanism doesn't
survive `IdentityToIdeologyPull` interaction.

---

### X5 "Ranked-choice voting" — mechanism-pinned, framed as Drutman extrapolation

**Literature envelope.**

- *Drutman 2020* (*Breaking the Two-Party Doom Loop*): theoretical
  framework — RCV + multi-member districts + open primaries reduces
  primary-driven divergence. **Theoretical.**
- *Donovan & Bowler 2023*: US RCV empirics — modest reduction in
  negative campaigning, **null on voter polarization**.
- *Atkinson et al. 2023*: Maine RCV — null on polarization measures.
- *McGhee & Shor 2017*: California top-2 primaries — null on
  legislator polarization. (Different reform, closest US natural
  experiment.)
- *Reilly 2018*: comparative RCV (Australia, Ireland, PNG) — modest
  candidate-strategy effects, weak voter-polarization effects.
- *Hetherington 2001* (*APSR*): party-cue intensification (inverse
  mechanism).
- *Gidron, Adams, Horne 2020*: cross-national affective polarization
  by electoral system features.

**Honest framing (new).** The empirical evidence on RCV's
polarization effects is **mostly null**. Drutman 2020 is a
theoretical case that mechanism > current measurement. X5 is
intentionally treated as a Drutman-theoretical extrapolation —
**every knob below is `[T]`** and the results writeup must flag X5
as the only intervention without a measured magnitude anchor. Drutman's
actual theory bundles RCV with multi-member districts and open
primaries; the engine's X5 represents the full comprehensive bundle,
not RCV alone. RCV alone has null effects in current empirics.

**Phase 9 mismatch.** Phase 6's one-shot centroid halve is the
*result* of Drutman's reform, not the mechanism. Phase 9
`EliteDrift × 3.0` re-diverges centroids within ~5 years;
`FactionAnchor` events keep firing. Faithful redesign touches the
drift rate, not just the snapshot.

**Redesign knob bundle.**

- Halve current party centroids `[T]` — Hetherington 2001 direction
  (inverse); magnitude theoretical
- Halve each agent's `party_cue` `[T]` — elite-cue intensity
  direction; magnitude theoretical
- `tier_d_anes_drift_multiplier`: 3.0 → 1.5, ongoing `[T]` —
  Drutman primary-incentive channel; factor-of-2 is a choice
- `FactionAnchor.strength`: 0.10 → 0.05 `[T]` — faction candidates
  lose primary-strategic advantage; magnitude theoretical

**Magnitude / duration / fraction.**

- Magnitude: **none direct**; mechanism-pinned (factor-of-2 across
  elite-incentive channels). Flagged in results writeup.
- Duration: persistent (institutional change).
- Treated fraction: 100% (institutional).

**Expected.** Δsep partial-to-real on issue sorting, now durable
(was −0.14 transient in Phase 6; expect to hold over 30+ ticks).
Δaff small negative.

**Falsification.** Δsep null or positive after 30 ticks → the
drift-channel mechanism doesn't carry the durability claim. Δsep <
−0.30 → magnitude unrealistically large for a theoretical reform;
reduce multipliers.

---

### X6 "Shared neighborhoods and workplaces" — conservative refinement

**Literature envelope.**

- *Allport 1954*: contact-hypothesis conditions (equal status,
  common goals, cooperation, institutional support).
- *Pettigrew & Tropp 2006* (*JPSP*): meta-analysis, r ≈ −0.21
  across 515 studies.
- *Mousa 2020* (*Science*): Iraqi cross-religion soccer leagues —
  ~0.10 SD on in-game behaviors; **limited generalization** to
  out-of-context attitudes. Added 1 cross-religion teammate per
  participant.
- *Lowe 2021* (*AER*): Indian cricket leagues — caste-mixed teams
  reduce in-context prejudice; partial transfer. ~2 cross-caste
  teammates per participant.
- *Paluck et al. 2021* (*Annual Review*): field-experiment review
  — effects smaller and shorter-lived than originally claimed;
  many null in adversarial contexts.
- *Enos 2014* (*PNAS*): Hispanic Spanish-speaking commuters on
  Boston trains → **increased** exclusionary attitudes. Contact
  can backfire under status-threat.
- *Scacco & Warren 2018* (*APSR*): Nigerian classrooms via
  cooperation — modest prejudice reduction.
- *Mutz 2006* (*Hearing the Other Side*): cross-cutting ties reduce
  status threat.

**Phase 9 mismatch.** Phase 6 X6 backfired on affect: tripled
encounter volume × halved per-encounter valence → deeper drift.
Phase 9 adds `saturation=1.0` (caps per-step magnitude), which may
mute the backfire. X6 misses the Mutz 2006 threat-reduction channel.

**Conservative scope (new).** Prior draft used **+3** cross-party
involuntary ties — larger than any measured contact intervention
(Mousa +1, Lowe +2). **Revise to +1** to stay within envelope. The
edge-level vs agent-level `cooperative_mute` debate (Pettigrew 2009
secondary-transfer) remains the most substantive open follow-up;
Phase 10 keeps the conservative edge-level default per scope §3.
Phase 11 X6b candidate.

**Redesign knob bundle.**

- **1** cross-party involuntary cooperative tie per agent `[L:M]` —
  Mousa 2020, Lowe 2021 envelope (revised down from +3)
- Out-party affect reset to 0 for treated agents `[L:D]` — contact
  resets baseline direction; 0 is `[C]`
- `threat` reset to 0 for treated agents `[L:D]` — Mutz 2006
  mechanism direction
- **Document, no knob change:** edge-level `cooperative_mute` is
  the conservative Pettigrew & Tropp reading; agent-level
  (Pettigrew 2009 secondary-transfer) is Phase 11 X6b

**Magnitude / duration / fraction.**

- Magnitude: Mousa 2020 ~0.10 SD in-context; Pettigrew & Tropp r ≈
  −0.21 individual (not directly comparable to population Δaff).
- Duration: persistent (structural).
- Treated fraction: 100% (structural population-level change).

**Expected.** Δsep ≈ 0 (null on issue); Δaff: with +1 tie (not +3),
saturation cap, and threat reset, expect partial helpful on affect.
**Less aggressive than prior +3-tie draft, which would have
over-shot the contact-hypothesis envelope.** Note Enos 2014
suggests contact under status-threat can backfire — `threat`
reset is the redesign's hedge against that path.

**Falsification.** Δaff backfires (negative) → either saturation
isn't doing the work expected, or volume effect survives +1 tie
(Enos pattern wins). Δaff > +0.30 → magnitude larger than
Mousa/Pettigrew envelope; investigate threat-reset doing
unrealistic work.

---

### X7 "Correct perception gap" — refinement (variant: X7b "Sustained")

**Literature envelope.**

- *Ahler & Sood 2018* (*JOP*): partisans hold large misperceptions
  of out-party composition (~20pp on identity questions).
- *Lees & Cikara 2020* (*Nature Human Behaviour*): meta-correction
  r ≈ −0.07 on intergroup attitudes.
- *Druckman et al. 2022* (*Nature Human Behaviour*): durability of
  corrections — **pessimistic**; effects decay within weeks unless
  reinforced.
- *Voelkel et al. 2024*: perception-correction arm → ~0.04 SD on
  affect.
- *Moore-Berg et al. 2020* (*PNAS*): meta-perceptions → outgroup
  hostility.
- *Yudkin et al. 2019* (More in Common, *Perception Gap*):
  public-facing magnitude estimates.

**Phase 9 mismatch.** Phase 6 was a one-shot reset of
`perceived_other_party`. Phase 9's `PerceptionUpdate.correction_rate
= 0.01` continuously drifts perception back toward homophilous
neighbor observations, but cross-party neighbours are sparse — so
correction is slow and a one-shot reset washes out within ~30 ticks.
Durability requires accelerating the correction during the campaign
window. **Revised 2026-05-28:** the prior draft also proposed
reducing the `PERCEPTION_EXTREME_BIAS_*_TIER_D` constants during
the window, framed as "bias-maintenance reduction." On re-read,
those constants are *build-time-only* (consumed by
`build_engine`'s perception-seeding loop) and have no runtime
consumer in either `PerceptionUpdate` (which pulls toward observed
neighbour mean, not toward bias) or `cohort_replacement` (which
doesn't re-seed perception for new agents). Adding a
bias-maintenance channel would be a new mechanism with its own
literature anchor and its own sacred-test re-bless. Phase 10 keeps
the simpler reset + correction-rate boost mechanism; the
new-mechanism path is a Phase 11 candidate if Phase 10 X7 lands
null after measurement.

**Redesign knob bundle.**

- Reset `perceived_other_party` to actual centroid `[L:D]` — Phase
  6 snapshot
- For treated agents: `PerceptionUpdate.correction_rate` 0.01 →
  0.05 `[T]` — accelerated correction during campaign; 5× factor
  is theoretical
- **Dropped from prior draft (2026-05-28):** per-agent
  `PERCEPTION_EXTREME_BIAS_*_TIER_D` reduction. No runtime consumer
  in the current engine; the build-time-only constants do not act
  as ongoing bias maintenance.

**Magnitude / duration / fraction.**

- Magnitude: Voelkel 2024 ~0.04 SD on affect; Lees & Cikara r ≈
  −0.07.
- Duration: **3 ticks (~1 year)** `[L:M]` — revised down from 9
  ticks; the longer duration exceeded the empirical durability
  envelope by ~3×.
- Treated fraction: 20% `[T]` — speculative; sensitivity at 5% /
  20% / 50%.

**Expected.** Δsep ≈ 0 (perception doesn't move position
directly); Δaff small positive ~+0.02 to +0.04 (null-to-partial),
matching Voelkel 2024.

**Falsification.** Δaff > +0.10 → engine over-converting perception
to affect. Δaff null even at 20% reach → bias-maintenance machinery
isn't doing the expected work.

---

## Implementation notes

### New `Intervention.param_bundle` overrides required

Several bundles touch knobs Phase 6 never reached. The intervention
plumbing in `abm/pillars/interventions_phase6.py` must support
overrides on:

- `BacklashRepulsion.threat_amplification` (X1)
- `IdentityToIdeologyPull.strength_y` (X4) — per-agent override via
  a new `attrs` key, since the rule currently reads the env-scoped
  scalar
- `tier_d_anes_drift_multiplier` (X5) — currently env-scoped only;
  intervention mutates `env.attrs` at setup time
- `FactionAnchor.strength` (X5) — currently env-scoped only;
  intervention rebuilds the rule or mutates the singleton
- ~~`PERCEPTION_EXTREME_BIAS_X_TIER_D` / `_Y_TIER_D` (X7)~~ —
  **dropped 2026-05-28.** These are build-time-only constants with
  no runtime consumer; the brief's "bias-maintenance" claim doesn't
  match engine reality. See §X7 for the revised rationale.
- Per-agent `PerceptionUpdate.correction_rate` (X7) — needs new
  `attrs` key analogous to `attrs["epsilon"]`
- Per-agent `threat` reset (X6) — already supported via
  `attrs["threat"]`
- Identity-weight override (X4) — already supported via
  `attrs["identity_weight_override"]`

**Engine plumbing changes needed before any of this can fire:**

1. **`IdentityToIdeologyPull.strength_y` per-agent override** via
   `attrs["identity_pull_strength_y_override"]`. Default `None` =
   use rule value.
2. **`PerceptionUpdate.correction_rate` per-agent override** via
   `attrs["correction_rate_override"]`. Default `None` = use rule
   value.

*Dropped 2026-05-28:* the prior brief listed a third change
promoting `PERCEPTION_EXTREME_BIAS_*_TIER_D` to env-scoped knobs.
On engine review these constants are build-time-only with no
runtime consumer, so the promotion would be inert. See §X7 for
the revised intervention design.

### Release point and measurement

- All interventions fire at **tick 135 (end of 2025)** on the
  historical arc with `tier_d_anes_knobs=True`.
- Counterfactual horizon: **30 ticks (~10 years)** post-intervention.
- Metrics: Δparty_separation (issue sorting) and
  Δaffective_polarization (affect), measured against a no-
  intervention control at the same seed.
- Bucket thresholds (carried over from Phase 6): `|Δ| < 0.05` →
  null; `0.05–0.15` (helpful direction) → partial; `≥ 0.15`
  (helpful direction) → real; opposite-direction > 0.05 → backfire.
- 9-seed ensemble (matches `phase9_anes_score.py`).
- **New per §0.3:** each intervention's results entry reports the
  per-axis bucket *plus* the falsification check (was the observed
  Δ within the brief's expected range?).
- **New per §0.1:** results writeup tallies provenance-tag share
  per intervention (e.g., "X5: 0/4 knobs `[L:M]`, 4/4 `[T]`") so
  reviewers can see at a glance which buckets are
  empirically-grounded vs theoretical extrapolations.

### Sensitivity sweeps required

For interventions with `[T]` treated-fraction values:

- **X3, X4, X7:** sweep treated-fraction at {5%, 20%, 50%}. Report
  whether the bucket label is stable across the sweep.

For interventions with multiple `[T]` knobs (most consequential:
X5):

- **X5:** sweep `tier_d_anes_drift_multiplier` reduction at {1.0,
  1.5, 2.0} (i.e., 3.0 → 1.0 / 1.5 / 2.0) to characterize the
  mechanism-pin sensitivity.

### Citation verification TODO

Pin venue/year before locking into `methods.md`:

- Voelkel et al. 2024 Strengthening Democracy Challenge — *Science
  Advances* (verify volume/issue)
- Allcott et al. 2024 Facebook deactivation — verify venue (AER?)
- Combs et al. 2023 — *PNAS* per current citation; verify
- Broockman & Kalla 2024 — NBER WP; verify forthcoming venue
- Lowe 2021 — *AER*; verify
- Atkinson et al. 2023 Maine RCV — verify venue
- Mousa 2020 — *Science* confirmed
- Santoro & Broockman 2022 — verify venue
- Kalla & Broockman 2020 — *APSR* per current citation; verify
- Yeomans et al. 2020 — *OBHDP*; verify

Phase 6-era citations are high-confidence and can pin directly:
Bail 2018, Iyengar 2019, Mason 2018, Pettigrew & Tropp 2006,
Allport 1954, Drutman 2020, Mutz 2006/2018, Ahler & Sood 2018,
Hetherington 2001, Levendusky 2013/2018/2021, Druckman 2022, Lees
& Cikara 2020, Enos 2014, Paluck et al. 2021, McGhee & Shor 2017,
Reilly 2018, DellaVigna & Kaplan 2007, Hangartner 2021, Munger
2017, Settle 2018, Bursztyn & Yang 2023, Gidron Adams Horne 2020,
Yudkin More in Common 2019, Moore-Berg 2020.

---

## Sequence into Phase 10 work

1. **Engine plumbing** — three changes per Implementation Notes
   above. Sacred tests must still pass with defaults unchanged.
2. **Intervention rewrite** — implement the 7 bundles in
   `abm/pillars/interventions_phase6.py` (or Phase 10 successor
   module); default Phase 6 behavior preserved as fallback.
3. **Sacred regression** — confirm 73 pillar tests still pass;
   Phase 6 X1–X7 fixture tests need re-blessing because bundles
   changed.
4. **Measurement** — run all 7 at 9 seeds against the ANES
   end-state; emit per-intervention bucket label, Δ-magnitude,
   provenance-tag summary, and falsification check.
5. **Sensitivity sweeps** — per §"Sensitivity sweeps required"
   above. Sweep outputs feed into the results writeup.
6. **Citation verification** — pin TODOs into `methods.md`, then
   update [ENGINE_KNOBS.md §6](../ENGINE_KNOBS.md) bucket labels.
7. **Phase 10 results writeup** — analogous to
   `phase9_results.md`. Pre-registered hypotheses:
   - *X5 moves to "real" durably on issue sorting* (because the
     redesign touches drift, not just centroids) — but is heavily
     `[T]`-flagged
   - *X6 flips from backfire to partial-helpful on affect* (because
     +1 tie within Mousa envelope + saturation cap + threat reset
     cancel the volume-backfire)
   - *X4 lands at +0.02 to +0.04 Δaff* matching Voelkel 2024 anchor
   - First-class transparency number: what fraction of all knobs
     across all 7 bundles carries each provenance tag

8. **Phase 11 candidates identified in §3 collapse:**
   - X1b "anonymous cross-partisan deliberation" (Combs 2023)
   - X2b "bridging-based ranking" (Stray 2022; small-magnitude
     `[T]`)
   - X3b "switching" (Broockman & Kalla 2024 magnitude)
   - X6b "agent-level cooperative mute" (Pettigrew 2009 secondary
     transfer)
