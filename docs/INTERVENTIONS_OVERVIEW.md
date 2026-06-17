# polarlab — Interventions Overview

*A single-day briefing on the public-facing intervention library
at the close of Phase 10. Higher-altitude companion to the per-
intervention briefs in `phase10_interventions/redesign_briefs.md`
(the literature-pinned design contract) and the measurement
record in `results/phase10_results.md` (the landed scoreboard) —
synthesises, doesn't repeat. Read this for "what the library is
and what it teaches"; read the briefs for "exactly which
literature each knob is anchored to."*

For the engine these interventions modify, see
[`ENGINE_OVERVIEW.md`](ENGINE_OVERVIEW.md) and
[`ENGINE_KNOBS.md`](ENGINE_KNOBS.md).

---

## 1. What this is

The intervention library is seven named depolarization levers
applied to the Phase 9 ANES-recalibrated engine. Each is a
real-world ask a non-expert recognises ("show people the other
side," "fix the algorithm," "ranked-choice voting") backed by
published literature and mapped to specific engine mechanisms.
Each is measured on two axes — *issue sorting* (Δparty_separation)
and *affect* (Δaffective_polarization) — and labelled with one of
four buckets: **null** / **partial** / **real** / **backfire**.

The library exists to do one thing publicly and honestly: contrast
**what people most loudly demand** against **what the empirical
literature, made visible through the model, says happens**. The
contrast — most loudly-demanded interventions don't work, two
structural ones do, one popular one backfires — is the project's
whole pedagogical payoff.

The library is **closed as of Phase 10**: 7 interventions, blessed
buckets, redesign brief locked, measurement script reproducible.
Phase 11 candidates exist (X1b anonymous, X2b bridging, X3b
switching, X6b secondary-transfer-only) but they're additions,
not refactors.

---

## 2. The library at a glance

| ID | Name | Bucket (sep / aff) | Lay framing |
|---|---|---|---|
| **X1** | Show people the other side | **backfire** / null | Cross-partisan exposure (programs, feeds) |
| **X2** | Fix the algorithm | null / null | Reset social feeds to chronological / non-curated |
| **X3** | Quit cable news | null / null | Disengage from partisan media |
| **X4** | Bipartisan dialogue programs | null / null* | Civic dialogue + shared-identity priming |
| **X5** | Ranked-choice voting | **partial** / null | Electoral reform (RCV + open primaries) |
| **X6** | Shared neighborhoods and workplaces | null / **real**† | Structural shared-life contact (real at 2020, partial earlier) |
| **X7** | Correct the perception gap | null / null | Sustained civic perception-correction campaign |

*X4 affect is null at the bucket cutoff but trends helpful at
the Voelkel 2024 ~0.04 SD floor across all release decades —
honest direction-match without crossing the partial threshold.

†X6 affect re-blessed partial→real at MHV S2 T2.6 (user sign-off
2026-06-10): on the emergent D=7 canonical substrate the
cross-release mean Δaff measures +0.172, over the 0.15 real
boundary X6 had been flagged as sitting on. The full-protocol S4
phase-10 re-measure revisits all tags and the per-decade detail
in §4.6 (which still describes the pre-flip engine).

Measured across **four release ticks (1990 / 2000 / 2010 /
2020)** × 30-tick counterfactual horizon × 9 seeds = 252
intervention runs + 36 control runs = 288 simulations. Full
measurement at
[`results/phase10_measurement.json`](results/phase10_measurement.json).

---

## 3. The intervention contract

### 3.1 Release point

All Phase 10 interventions fire on the historical-arc scenario
(`abm/pillars/historical_arc.py`) at one of four decade-aligned
ticks:

- **1990** (tick 30) — pre-Fox-News, pre-cable-cascade
- **2000** (tick 60) — pre-Tea-Party, pre-social-media
- **2010** (tick 90) — post-Citizens-United, peak Tea Party
- **2020** (tick 120) — post-Trump, peak affective polarization

Sweeping across these characterises *how intervention efficacy
varies with the state of polarization*. X5 (RCV) shows weakest
effect at 2010 (peak Tea Party) and strongest at 2000 (pre-
cascade) — itself a finding, matching the Drutman 2020 / Mason
2018 "pre-cascade interventions land harder" thesis.

### 3.2 Counterfactual

Each intervention is run for **30 ticks (~10 years)**
post-application. Δ vs the no-intervention control at the same
release tick and seed measures the *additional* effect of the
intervention beyond natural drift.

### 3.3 Duration semantics

Sustained-policy framing: X1, X4, X7 use 60-tick durations
(covering the full counterfactual window with buffer). The lay
question the engine is meant to answer is "what would this policy
do if we sustained it" — not "how long does a one-shot dose
persist." X5 and X6 are inherently structural / institutional
(one-shot setup, persistent effect). X2 and X3 are
algorithmic / behavioural (no expiry mechanism needed).

### 3.4 Bucket thresholds

|Δ| < 0.05 → **null**; 0.05 – 0.15 helpful-direction → **partial**;
≥ 0.15 helpful-direction → **real**; > 0.05 opposite-direction →
**backfire**.

Sign convention: helpful on issue sorting = **negative** Δsep
(camps closer); helpful on affect = **positive** Δaff (warmth
recovers — the metric reads more-negative as more-polarized).

---

## 4. How each intervention works

### 4.1 X1 — Show people the other side

**Mechanism.** Turns on `BacklashRepulsion` at `strength=0.055`,
boosts `threat_amplification` 1.0 → 1.5 and
`AffectiveUpdate.identity_weight` 0.5 → 0.6 for a sustained
60-tick window. Phase 9's post-2016 threat event already encodes
the Bail-asymmetry (60% of party=1 carry `threat=0.6`); the
intervention amplifies that mechanism rather than re-imposing
a hard-coded asymmetric dict on top.

**Literature anchor.** Bail et al. 2018 (*PNAS*, ~0.10–0.12 SD
shift, asymmetric R-biased); Combs et al. 2023 (anonymous
engagement REDUCES polarization — identity-loaded exposure is
the threat mediator); Mutz 2018 (status threat → 2016 vote);
Settle 2018 (*Frenemies*); Levendusky & Stecula 2021; Yeomans
et al. 2020.

**Evidence grade (MHV T0.2): LOW / CONTESTED.** The backfire
*direction* rests on Bail 2018 and has not replicated as a general
phenomenon: Guess & Coppock 2020 found no attitudinal backlash in
three experiments, and Wood & Porter 2019 found factual-correction
backfire "elusive" across 10k+ subjects. In-engine, the backfire is
delivered by `BacklashRepulsion`, whose affect gate (`warmth < −0.3`)
fires for **99.8% of partisan agents** in the polarized regime where
interventions are measured (methods.md §5.4.bis) — the mechanism is
nearly unconditional there, so the engine cannot express the
conditional, threat-moderated backfire the literature debates.

**Engine reading.** **Strong backfire** (Δsep +0.32 to +0.37)
across all four release decades. Decade-invariant — unlike X5
and X6, X1's effect doesn't depend on starting state. The
affect-gated repulsion cascades: a small initial push moves
agents past the `affect_threshold = -0.3`, which triggers more
repulsion, which moves them further. The naive lay expectation
("seeing the other side humanises them") is exactly inverted at
population scale — *conditional on the Bail-2018 backfire being the
rule rather than the exception (see the evidence grade above)*.

### 4.2 X2 — Fix the algorithm

**Mechanism.** Single-knob: zero `BoundedConfidenceInfluence.
affect_weight`. Removes the engine's algorithmic affect modulator
that biases the BC averaging step toward already-warmer
neighbours.

**Literature anchor.** Guess et al. 2023 (*Science*, Meta-2020,
4 papers — null on attitudes); Allcott et al. 2024 (*AER*,
Facebook deactivation, ~0.04 SD affect, null on issues); Stray
2022 (bridging-based ranking framework — theoretical, no RCT).

**Engine reading.** **Null on both axes** — exact reproduction
of the Meta-2020 null finding. The flagship policy ask of the
last decade lands as the model's flagship null result.

### 4.3 X3 — Quit cable news

**Mechanism.** Setup-only mutation: zero each treated agent's
MSNBC + Fox News weights in `media_diet`. Phase 10 applies to a
**20% treated fraction** (Allcott 2020 take-up envelope), not
full population.

**Literature anchor.** Levendusky 2013 (*AJPS*, partisan-media
drift); Allcott et al. 2020 (*AER* 110:629, Facebook deactivation
~5pp shift, ~0.04 SD); DellaVigna & Kaplan 2007; Levendusky &
Malhotra 2016; Martin & Yurukoglu 2017. Broockman & Kalla 2024
(cable *switching*, ~0.5 SD) captured as Phase 11 X3b candidate.

**Engine reading.** **Null with backfire-direction trend** (Δsep
+0.003 to +0.007). At 20% reach diluted by Phase 9's amplified
`EliteDrift`, the centrifugal partisan-cable removal is mostly
washed out. Direction is consistent with Phase 6's finding (and
with the model's diet-target-inward-of-centroids artefact) but
the magnitude lives in the null bucket. **Honest framing (2026-06
peer-review audit, P6 / F6):** because the diet targets sit *inward*
of the party centroids, `MediaConsumption` is **centripetal on the
position axis** — the opposite sign of the Levendusky 2013 /
DellaVigna-Kaplan / Martin-Yurukoglu polarizing-media literature, so
*removing* cable nudges separation *up* (the backfire-direction trend),
not down. The model's polarizing-media effect lives only on the
**affect** channel (`MediatedAnimus`). This sign-mismatch is flagged
for R-phase (R5) reconciliation.

### 4.4 X4 — Bipartisan dialogue programs

**Mechanism (Phase 10 third-pass).** Samples 20% of agents; for
each, boosts `cooperative_share` to 0.5 (Pettigrew 2009
secondary-transfer halves per-encounter cooling) and resets
`perceived_threat` to 0 (Mutz 2006 / Levendusky 2021 — dialogue
reduces status threat). Faction-tagged agents receive the prime
at 50% effect (Mason 2018 strong-identifier resistance). Duration:
60 ticks sustained.

**Why the mechanism swap from Phase 6/8c's `identity_weight`
override:** Phase 9's `(1 − identity_weight) × party_issue_coupling
× issue_term` channel inverts the prediction — lower
`identity_weight` slightly *increases* cooling at modern decades
where coupling is large. The `cooperative_share` channel is the
literature-faithful Pettigrew 2009 secondary-transfer reading
and bypasses the inversion.

**Literature anchor.** Levendusky 2018; Voelkel et al. 2024
(Strengthening Democracy Challenge megastudy, ~0.04–0.05 SD on
affect); Bursztyn & Yang 2023; Santoro & Broockman 2022 (decay
within 3 months); Levendusky 2021 *We Need to Talk*; Mason 2018.

**Engine reading.** **Direction-correct null** — Δaff +0.002 to
+0.006 (helpful direction at the Voelkel 2024 envelope floor).
The prime works as the literature predicts but the macro shift
sits in the null bucket because reach is only 20% and the engine
has strong centripetal-to-polarization forces. The lay framing:
*civic dialogue helps the participants, but at 20% population
reach it doesn't move the macro picture*.

### 4.5 X5 — Ranked-choice voting

**Mechanism.** One-shot setup halves both party centroids and each
agent's `party_cue` (Hetherington 2001 elite-cue intensity, in
reverse). Phase 10 also halves `tier_d_anes_drift_multiplier` (3.0
→ 1.5) and `FactionAnchor.strength` (0.10 → 0.05), ongoing — so
`EliteDrift` and faction-strategic incentives are durably reduced
(Drutman 2020 mechanism). Without the ongoing channels, Phase 6's
one-shot centroid halve was transient (Phase 9's drift schedule
re-diverged within ~5 years).

**Literature anchor.** Drutman 2020 *Breaking the Two-Party Doom
Loop* (theoretical — bundles RCV + multi-member districts + open
primaries); Donovan & Bowler 2023 (US RCV empirics, modest
campaign-tone effects, **null on voter polarization**); Atkinson
et al. 2023 (Maine RCV — null); McGhee & Shor 2017 (California
top-2 — null on legislator polarization); Reilly 2018
(comparative); Hetherington 2001; Gidron, Adams & Horne 2020.

**Engine reading.** **Partial helpful on issue sorting at every
release decade** — Δsep -0.056 to -0.127. Pre-Trump 2000 is the
strongest (-0.127); peak Tea-Party 2010 the weakest (-0.056).
This is the cleanest "structural reform actually moves the
needle" finding. All four knobs flagged `[T]` (theoretical) —
direct empirical RCV evidence is mostly null; the engine reports
the Drutman *mechanism's* prediction, not a literature
replication.

### 4.6 X6 — Shared neighborhoods and workplaces

**Mechanism.** Add **1 cross-party involuntary cooperative tie
per agent** (Mousa 2020 / Lowe 2021 envelope — revised down
from Phase 7's +3, which over-shot). For agents who actually
receive a new tie (~50% of population), reset out-party
`affect` to 0 (the Allport "halving" reading) and reset
`perceived_threat` to 0 (Mutz 2006 — cross-cutting ties
reduce status threat). Restricting the affect/threat reset to
participants (vs the Phase 6 "all agents") was the key
calibration: the prior mechanism overshot the Pettigrew-Tropp
envelope by 3-4×.

**Literature anchor.** Allport 1954; Pettigrew & Tropp 2006
(*JPSP* 90:751, meta-analysis r ≈ -0.21 across 515 studies);
Pettigrew 2009 (secondary-transfer); Mousa 2020 (*Science*,
Iraqi cross-religion soccer, +1 tie); Lowe 2021 (*AER*, Indian
cricket, +2 ties); Paluck et al. 2021; Enos 2014 (contact
under status-threat can backfire); Scacco & Warren 2018; Mutz
2006.

**Engine reading.** **Partial-to-real helpful on affect** — on the
2026-06 affect-re-graded substrate, Δaff is +0.092/+0.140/+0.146 at
1990–2010 (**partial**) and +0.218 at 2020 (**real**); cross-release
mean +0.149, right on the real/partial boundary, so the declared public
bucket is now **partial** (was real). Still within the Pettigrew-Tropp
envelope; X6 remains the strongest affect lever. The decade-dependence
is honest: the re-grounded baseline is less polarized early (so contact
has less to undo) and most polarized in 2020 (so contact recovers most).
Null on issue sorting: Mason 2018 / Gidron et al. 2020
predict contact moves prejudice / affect more than issue
positions, and the model confirms. The lay framing: *the
contact hypothesis works in the model, at the magnitude the
meta-analysis predicts*.

### 4.7 X7 — Correct the perception gap

**Mechanism.** One-shot reset of treated 20%'s
`perceived_other_party` to actual env centroid (the snapshot).
Then for the 60-tick sustained window: per-agent
`correction_rate_override = 0.05` (5× the rule default) AND
`perception_target_override = "actual_centroid"` (switches
`PerceptionUpdate` to pull toward env-level actual centroid
rather than observed-neighbour mean — the "campaign reaches the
agent with external information" channel). Without the target
override, perception drifts back toward homophilous-neighbour
observations within ~30 ticks.

**Literature anchor.** Ahler & Sood 2018 (*JOP*, misperceptions
~20pp); Lees & Cikara 2020 (*NHB*, meta-correction r ≈ -0.07);
Druckman et al. 2022 (*NHB*, durability pessimism); Voelkel et
al. 2024 (perception-correction arm ~0.04 SD on affect);
Moore-Berg et al. 2020; More in Common 2018 *Perception Gap*.

**Engine reading.** **Null on both axes.** The mechanism works
(treated agents' perceptions correct fast to actual centroids
during the campaign), but population-level affect barely follows.
The interpretive finding: *the perception gap is real, correcting
it works at the individual level, but it only matters at the
moment of cross-party encounter, which is rare in a homophilous
network*. This is one of the cleaner illustrations of the
project's calibrated-cynicism payoff — the intervention does
exactly what its proponents claim it does, and the model still
says it doesn't move the macro picture.

---

## 5. Three lanes (the public-facing story)

### 5.1 The popular-but-backfires — X1

Cross-partisan exposure is the depolarization lever most often
demanded in popular media and the one Bail's 2018 PNAS paper
found backfires under threat. In the Phase 10 engine, it
backfires *strongly* and *robustly* across decades — Δsep ≈ +0.33
at every release. The mechanism cascades: small initial pushes
trip the affect-threshold gate, which triggers more repulsion.

This is the cleanest naive-vs-engine contrast in the library and
the project's headline pedagogical exhibit — **graded LOW/CONTESTED
(MHV T0.2)**: the backfire premise did not replicate in Guess &
Coppock 2020 or Wood & Porter 2019, and the engine's affect gate
fires for 99.8% of partisans at measurement time (§4.1), so the
robustness is partly built in. Present it as "what follows if
Bail-style backfire is the rule," not as settled science.

### 5.2 The empirically-supported workers — X5 and X6

Two interventions move the needle.

**X5 (RCV / open primaries / multi-member districts)** lands
partial-helpful on issue sorting at every decade, durable through
the counterfactual window. The mechanism is theoretical (`[T]`-
heavy) but the engine's mechanistic prediction is consistent —
elite-incentive change → less primary-driven divergence →
partial-real depolarization. Direct RCV empirics are mostly
null, so the engine reports the theory's prediction; the lay
framing has to be honest about the `[T]` flag.

**X6 (shared neighborhoods, workplaces, institutions)** lands
real-helpful on affect within the Pettigrew-Tropp / Mousa
empirical envelope. The mechanism is the contact-hypothesis
literature's clearest empirical finding (r ≈ -0.21 across 515
studies); the engine reproduces it. Lay framing: *the
intervention with the strongest empirical evidence behind it
actually works in the model — at exactly the magnitude the
meta-analysis predicts*.

### 5.3 The popular-but-doesn't-work — X2, X3, X4, X7

Four nulls, distinct reasons:

- **X2** is null because the Meta-2020 study is null — direct
  empirical reproduction of the Guess et al. 2023 finding.
- **X3** is null because at 20% reach the centrifugal partisan-
  cable removal is diluted by Phase 9's amplified elite drift.
- **X4** is null at the bucket cutoff because reach is 20% and
  duration matters less than mechanism — Voelkel 2024's
  ~0.04 SD floor is reproduced as Δaff ≈ +0.004.
- **X7** is null *despite the mechanism working*: perception is
  successfully corrected for treated agents, but the engine
  reports the perception correction only matters at cross-party
  encounters, which are rare.

The four distinct null reasons let the demo say something more
than "the popular interventions don't work" — it lets it say
*why each one doesn't*, with the engine's per-mechanism diagnostics
visible.

---

## 6. Provenance — what's literature, what's theory

Per-knob provenance tags (`[L:M]` / `[L:D]` / `[T]` / `[C]`)
are recorded in
[`phase10_interventions/redesign_briefs.md §0.1`](phase10_interventions/redesign_briefs.md).
Cross-library tally:

- `[L:M]` literature-magnitude — 6 knobs (25%)
- `[L:D]` literature-direction — 7 knobs (29%)
- `[T]` theoretical / mechanism-pin — 10 knobs (42%)
- `[C]` calibration choice — 1 knob (4%)

**X5 (RCV)** carries the heaviest theoretical load (4/4 `[T]`).
**X6 (contact)** is the most empirically anchored (mostly `[L:M]`).
**X2 (algorithm)** is a single `[L:M]` knob. The writeup
discipline is that any `[T]`-heavy intervention's bucket label
should be read as *"the engine says this mechanism produces
this effect"*, not *"the literature predicts this effect."*

---

## 7. Honest limitations

1. **Sustained-policy framing for X1, X4, X7.** Literature
   measures one-shot doses with short follow-ups; the engine
   measures sustained 60-tick interventions. The X1 magnitude
   (+0.33) and X4 direction-rightness are extrapolations.
2. **20% treated-fraction speculation.** X3, X4, X7 use 20%
   reach as a `[T]` value. The 5% / 20% / 50% sensitivity
   sweep is deferred to Phase 11.
3. **X7 propagation limit.** The null reading depends on the
   homophilous-network assumption. A less-sorted network would
   propagate perception correction further.
4. **X1 affect-threshold cascade non-linearity.** There's no
   clean "moderate backfire" strength between 0.05 (null) and
   0.06 (strong backfire). The reported +0.33 is the engine's
   honest output, not a tunable midpoint.
5. **X5 evidence is theoretical.** Direct US RCV empirics
   (Donovan & Bowler 2023; Atkinson et al. 2023) are mostly
   null; the engine reports the Drutman 2020 mechanism's
   theoretical prediction. The lay framing has to flag `[T]`.

---

## 8. Phase 11 candidates

Identified during Phase 10 scope collapse, deferred:

- **X1b** "anonymous cross-partisan deliberation" (Combs et al.
  2023) — tests whether anonymity flips Bail backfire to helpful.
- **X2b** "bridging-based ranking" (Stray 2022) — `BC.epsilon`
  bump on a treated subset. Small-magnitude `[T]`.
- **X3b** "switching" (Broockman & Kalla 2024, ~0.5 SD individual)
  — partisan-outlet swap distinct from X3a quit.
- **X6b** "agent-level cooperative mute via secondary transfer
  alone" — isolates Pettigrew 2009's mechanism from the +1
  tie + affect/threat reset.
- **X3 / X4 / X7 treated-fraction sensitivity sweep** at 5% /
  20% / 50% per the brief's §0.2 discipline.

---

## 9. What the library is for

The library is a *teaching artifact* for a public, non-expert
audience. The eventual UI will let a user choose a release decade,
apply an intervention, watch the counterfactual unfold, and
compare against the no-intervention baseline. The pedagogical
payoff is the contrast between **what they thought would happen**
and **what the engine, anchored to the empirical literature, says
happens**.

Three things keep the library honest as it heads into the UI:

- **Per-knob provenance.** Every knob's tag is in the brief and
  the results doc — `[L:M]` / `[L:D]` / `[T]` / `[C]`. The UI
  can surface this so users see which buckets are empirically
  grounded vs theoretical extrapolations.
- **Falsification rules.** Every intervention specifies what
  observation would force a redesign (brief §0.3). The Phase 10
  scoreboard reports per-cell pass/fail; the discipline is
  "move the tag if measurement contradicts, don't fudge the
  rule."
- **The measurement script is reproducible.**
  `scripts/phase10_measure.py` at 9 seeds × 4 releases × 8 cells
  runs in ~60s. Any future engine change re-runs the sweep and
  forces re-blessing.

This document is the highest-altitude synthesis. The per-
intervention briefs are the citation-pinned design contract. The
Phase 10 measurement JSON is the empirical record. The
consolidated bucket test in `tests/test_phase6.py` is the
regression lock (currently measuring on the pillar — a Phase 11
extension would add a historical-arc bucket fixture).

The story the library tells, in one sentence: *most depolarization
interventions people loudly demand don't move the macro picture
in this model; the two that do are structural (electoral reform,
shared institutions); the one most-demanded backfires hard; and
the engine can tell you, for each null, **why**.*
