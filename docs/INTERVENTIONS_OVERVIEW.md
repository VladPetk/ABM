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

> **Status — updated 2026-06-18** for the R-phase (audit-fix +
> reversibility) and the subsequent **R-A…R-D intervention-faithfulness
> pass**. The buckets, mechanisms, and per-release numbers below are blessed
> against the R-phase canonical engine
> (`ANES_FULL_KWARGS = ANES_FULL_RPHASE_KWARGS`). Two pre-existing stale
> claims are also corrected here: X5 is **"Deprogramming & exit programs,"**
> not ranked-choice voting (that swap landed at MHV S5), and X6's affect
> effect is now genuinely **durable to 2025** rather than re-converging.
> The workstream record — exact mechanisms, decompositions, and re-bless
> decisions — is in
> [`internal/intervention_durability_findings.md`](internal/intervention_durability_findings.md)
> §7–§8.

---

## 1. What this is

The intervention library is seven named depolarization levers
applied to the Phase 9 ANES-recalibrated engine. Each is a
real-world ask a non-expert recognises ("show people the other
side," "fix the algorithm," "shared neighborhoods and workplaces")
backed by published literature and mapped to specific engine mechanisms.
Each is measured on two axes — *issue sorting* (Δparty_separation)
and *affect* (Δaffective_polarization) — and labelled with one of
four buckets: **null** / **partial** / **real** / **backfire**.

The library exists to do one thing publicly and honestly: contrast
**what people most loudly demand** against **what the empirical
literature, made visible through the model, says happens**. The
contrast — most loudly-demanded interventions don't move the macro
picture, one structural lever (shared institutions / contact) durably
helps, and cross-party exposure backfires only under active identity
threat (null on average) — is the project's whole pedagogical payoff.

The library is **closed as of Phase 10** (7 interventions, blessed
buckets, redesign brief locked, measurement script reproducible),
with the post-R-phase intervention-faithfulness pass (R-A…R-D,
2026-06-18) re-blessing four levers against the corrected engine:
X1 (threat-gated), X2 (earned null), X5 (deprogramming), X6 (durable
contact). Phase 11 candidates exist (X1b anonymous, X2b bridging, X3b
switching, X6b secondary-transfer-only) but they're additions,
not refactors.

---

## 2. The library at a glance

| ID | Name | Bucket (sep / aff) | Lay framing |
|---|---|---|---|
| **X1** | Show people the other side | null / null* | Cross-partisan exposure (programs, feeds) |
| **X2** | Fix the algorithm | null / null | Reset social feeds to chronological / non-curated |
| **X3** | Quit cable news | null / null | Disengage from partisan media |
| **X4** | Bipartisan dialogue programs | null / null† | Civic dialogue + shared-identity priming |
| **X5** | Deprogramming & exit programs | null / null | Counter-extremism on the organized tail |
| **X6** | Shared neighborhoods and workplaces | null / **partial**‡ | Structural shared-life contact (durable to 2025) |
| **X7** | Correct the perception gap | null / null | Sustained civic perception-correction campaign |

*X1 issue-sorting is **null on average** but **decade-varying**: with
the R-phase threat-gated backfire (`BacklashRepulsion.threat_gated`)
a Bail-magnitude conditional backfire surfaces only at the **2010
release**, whose sustained-exposure window overlaps the 2016
status-threat spike. Per-release 5-seed Δsep: 1990 0.000 / 2000 0.000
/ 2010 +0.077 / 2020 +0.025; cross-release mean +0.026 (null). See §4.1.

†X4 affect is null at the bucket cutoff but trends helpful at
the Voelkel 2024 ~0.04 SD floor across all release decades —
honest direction-match without crossing the partial threshold.

‡X6 affect is **partial** and now **durable**. R-phase R-C added a
sustained cooperative-share floor so the contact effect persists to
2025 instead of decaying (it had retained only ~9% by 2025). 5-seed
+30t cross-release Δaff +0.133 (per-release +0.098 / +0.125 / +0.139
/ +0.168 at 1990 / 2000 / 2010 / 2020 — partial; only the most-
polarized 2020 release tips to "real"); the 2025 durable Δaff is now
~+0.078 (was ~+0.017). The declared single bucket is **partial**. See §4.6.

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
varies with the state of polarization*. Two levers are now explicitly
**decade-varying**: X1's conditional backfire surfaces only at the 2010
release (whose window overlaps the 2016 status-threat spike), and X5
(deprogramming) is **exactly null pre-emergence** (1990 / 2000 have no
factions to reach) and only registers a sub-threshold negative once the
Tea-Party / MAGA / Bernie / DSA blocs exist (2010 / 2020) — itself a
finding: a targeted-tail program can only act where the tail exists.

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
persist." X5 (faction exit) and X6 (contact) are structural one-shot
setups — but X6's R-phase R-C fix makes its effect genuinely *persistent*
by holding a cohort-proof cooperative-share floor for the rest of the
run (the one-shot dose alone retained only ~9% by 2025; see §4.6).
X5's faction exit is permanent for the treated agents but doesn't
re-tag future radicalizations. X2 and X3 are algorithmic / behavioural
(no expiry mechanism needed; X2's channel zero is a durable platform
change).

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

**Mechanism (R-phase R-D, 2026-06-18).** Turns on `BacklashRepulsion`
at `strength=0.20` (re-anchored from 0.055), boosts
`threat_amplification` 1.0 → 1.5, and — the key change — sets
`BacklashRepulsion.threat_gated = True` for a sustained 60-tick window.
With the gate on, the repulsion push scales by
`threat_amplification × perceived_threat`, so it fires **only for the
threatened subset** rather than for every cold partisan. Phase 9's
post-2016 threat event encodes who is threatened (≈28% of agents post-
2016 carry status threat), so the conditional backfire is endogenous to
the polarized era. (On the emergent-constraint path the dyadic
`AffectiveUpdate.identity_weight` term is retired, so the old 0.5 → 0.6
identity boost is skipped there — it would resurrect a retired coupling.)

**What was fixed.** The old "backfire" tag came from an effectively
**unconditional** affect gate: in the polarized regime ~95% of
partisans sat below the `warmth < −0.3` warmth threshold
(`x1_gate_probe.py` measured 74% / 95% / 96% at 2010 / 2016 / 2020), so
the mechanism fired almost everywhere and over-claimed Bail 2018 against
the scholarly consensus. Threat-gating makes the backfire *conditional*,
matching the literature: null on average, with a Bail-magnitude backfire
only under active identity/status threat.

**Literature anchor.** Bail et al. 2018 (*PNAS*, ~0.10–0.12 SD
shift, asymmetric R-biased) — the conditional backfire premise;
Guess & Coppock 2020 (no general attitudinal backlash across three
experiments) and Wood & Porter 2019 (factual-correction backfire
"elusive" across 10k+ subjects) — the **null-on-average** consensus;
Combs et al. 2023 (anonymous engagement REDUCES polarization —
anonymity removes the identity-threat mediator); Mutz 2018 (status
threat → 2016 vote — threat is the asymmetry carrier); Settle 2018
(*Frenemies*); Levendusky & Stecula 2021; Yeomans et al. 2020.

**Evidence grade (MHV T0.2): LOW / CONTESTED.** The backfire
*direction* rests on Bail 2018 and has not replicated as a general
phenomenon (Guess & Coppock 2020; Wood & Porter 2019). The R-phase
fix is precisely the response to that grade: the engine now reproduces
the **null average** the consensus supports while preserving the
conditional, threat-moderated backfire the literature debates — rather
than asserting an unconditional backfire the old near-universal gate
could not avoid.

**Engine reading.** **Null on both axes on average; decade-varying.**
Per-release 5-seed Δsep: 1990 **0.000**, 2000 **0.000** (pre-threat),
2010 **+0.077** (a Bail-magnitude *partial* backfire — its sustained-
exposure window catches the fresh 2016 status-threat spike), 2020
**+0.025** (threat has decayed). Cross-release mean **+0.026 → null**.
The naive lay expectation ("seeing the other side humanises them") is
neither confirmed nor universally inverted: in this model, cross-party
exposure **does nothing on average and backfires only when it lands
during active identity threat** — the demo's decade-picker surfaces the
conditional backfire at the 2010 (2016-threat-era) release.

### 4.2 X2 — Fix the algorithm

**Mechanism (R-phase R-A wiring fix, 2026-06-18).** Zeroes the
social-media→`BoundedConfidenceInfluence` affect modulator that biases
the BC averaging step toward already-warmer neighbours. The fix is a
*wiring* correction: on the canonical `data_fed_media` path the live
modulator is `env.attrs["bc_affect_weight"]`, written every tick by
`MediaPenetrationSeries` from the social-media penetration curve, and
the rule reads that env value in **preference** to its own
`.affect_weight`. So the Phase-6 lever (set the rule's own
`affect_weight = 0`) was **shadowed** — a complete no-op, measured
exactly 0.000 at every release and horizon. X2 now zeroes the *live*
channel (`MediaPenetrationSeries.bc_aw_per_adoption = 0` plus the
release-tick env value, with the rule-field zero kept as the
no-series / pillar fallback).

**Literature anchor.** Guess et al. 2023 (*Science*, Meta-2020,
4 papers — null on attitudes); Allcott et al. 2024 (*AER*,
Facebook deactivation, ~0.04 SD affect, null on issues); Stray
2022 (bridging-based ranking framework — theoretical, no RCT, dropped).

**Engine reading.** **Null on both axes** — and now an **earned**
null. The deltas track social-media adoption (0.000 in 1990 →
−0.00014 in 2020), proof the lever genuinely operates the channel
rather than touching a dead knob. The macro effect stays ~null because
the algorithmic channel is *deliberately* weak (the "media paradox,"
blindspot #1; Meta-2020 null), so removing it changes essentially
nothing — which is exactly the finding. The flagship policy ask of the
last decade lands as the model's flagship null result; before
2026-06-18 that null was a wiring artifact, now it is a real
reproduction of the Meta-2020 null.

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
peer-review audit, P6 / F6):** the audit found that, because the diet
targets sat *inward* of the party centroids, `MediaConsumption` was
**centripetal on the position axis** — the opposite sign of the
Levendusky 2013 / DellaVigna-Kaplan / Martin-Yurukoglu polarizing-media
literature. **FIXED in the R-phase (R5, 2026-06-18; methods §5.32):** the
shipped canonical now sets `media_centrifugal=0.7`, which sharpens the
partisan diet onto same-pole outlets so the diet target sits *at/beyond*
the party pole — media is now **centrifugal (polarizing) on position**,
matching the literature. (The X3 "quit cable news" Δsep stays in the null
bucket — removing a now-mildly-polarizing diet is a small effect — but the
*sign* of the underlying media force is corrected.)

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

### 4.5 X5 — Deprogramming & exit programs

> **Note.** X5 was **"Ranked-choice voting"** through Phase 10. It was
> replaced at **MHV S5 (T5.0)** because the RCV lever's durable arm
> halved `tier_d_anes_drift_multiplier`, which went **inert** on the
> S3 data-fed elite path (the scheduled `EliteDrift` it scaled was gone),
> so RCV measured as a spurious backfire. The replacement is the
> library's only **targeted-tail** intervention.

**Mechanism (MHV S5 T5.0).** On a treated **50%** of *faction-tagged*
agents — those the emergence events gave a `faction_center` (Tea Party,
MAGA, Bernie, DSA) — two levers fire: (1) **exit the faction** by
clearing `faction_center`, so the `FactionAnchor` rule (which self-gates
on a present center) permanently stops tugging the agent toward its
faction sub-centroid; and (2) **moderate the now-extremist identity** by
halving `identity_strength`, which `PartyPull` reads as a linear
modulator, so a deradicalized agent sorts more weakly toward its party
package. The lever is `FactionAnchor` (`faction_anchor_events`), live and
shipped. Pre-emergence releases (1990 / 2000) have **no** tagged agents,
so the intervention is an **exact no-op** there — you cannot deprogram a
faction that hasn't emerged.

**Literature anchor.** Horgan 2009 (*Walking Away from Terrorism*);
Koehler 2017 (*Understanding Deradicalization*); Berger 2018
(*Extremism*, MIT Press); Gielen 2019 (*Terrorism & Political
Violence* — deradicalization-program evaluation review; effects
**modest / contested**); Bjørgo & Horgan 2009 (*Leaving Terrorism
Behind*). Real-world analogues: Life After Hate, EXIT networks.

**Engine reading.** **Null on both axes** — measured, decade-gated.
Cross-release mean Δsep −0.0062, Δaff +0.0004 (9 seeds × 4 decades).
Exactly 0 at 1990 / 2000 (no factions emerged yet), correctly signed
but sub-threshold where factions exist (Δsep −0.0037 at 2010,
−0.0212 at 2020). Confirmed robust across an escalation ladder
(exit-only −0.0049, +identity −0.0102, +50% reach −0.0212 at 2020 —
all still null). The honest finding: **a targeted counter-extremism
program on the organized extreme does not scale to aggregate
separation** — the tail is a thin slice of a population whose
separation is set by the broad middle. Program efficacy is itself
modest/contested in the literature, so the 50%-reach + full-exit
magnitude is graded **`[N]`** (a design choice in a contested
envelope), **not** the four `[T]` knobs RCV carried.

### 4.6 X6 — Shared neighborhoods and workplaces

**Mechanism (R-phase R-C, 2026-06-18 — sustained institutions).**
The **initial** contact warming is the prior mechanism: add **1 cross-
party involuntary cooperative tie per agent** (Mousa 2020 / Lowe 2021
envelope — revised down from Phase 7's +3, which over-shot); for the
~50% of agents who actually receive a new tie, reset out-party `affect`
to 0 (the Allport "halving" reading) and reset `perceived_threat` to 0
(Mutz 2006 — cross-cutting ties reduce status threat). The R-phase fix
adds the missing **durable** channel: shared neighborhoods and
workplaces are *persistent* structural features, so X6 now also holds a
cohort-proof, population-wide cooperative-share **floor**
(`env.attrs["sandbox_contact_share"] = 1.0`) for the rest of the run.
That value sets `AffectiveUpdate`'s `neg_mute` to 0.5 — the Pettigrew &
Tropp 2006 "contact halves prejudice" meta-analytic anchor (a literature
value, not a free knob) — and because it lives at the env level it is
read at apply-time, so cohort-replaced agents inherit it too.

**Why the fix was needed.** The doc previously claimed a "persistent
effect," but the one-shot dose alone **decayed to ~9% retained by 2025**:
R7 affect mean-reversion (toward −0.30) was the primary washout channel
and cohort turnover the secondary one (the decomposition showed
`shipped ≈ frozen`, so this was endogenous mean-reversion, not forcing
dilution). The sustained floor keeps ongoing shared life muting
out-party cooling rather than letting it reassert.

**Literature anchor.** Allport 1954; Pettigrew & Tropp 2006
(*JPSP* 90:751, meta-analysis r ≈ -0.21 across 515 studies);
Pettigrew 2009 (secondary-transfer); Mousa 2020 (*Science*,
Iraqi cross-religion soccer, +1 tie); Lowe 2021 (*AER*, Indian
cricket, +2 ties); Paluck et al. 2021; Enos 2014 (contact
under status-threat can backfire — the `threat=0` reset is the
hedge); Scacco & Warren 2018; Mutz 2006.

**Engine reading.** **Partial helpful on affect — and now durable.**
5-seed +30t cross-release Δaff **+0.133** (per-release +0.098 /
+0.125 / +0.139 / +0.168 at 1990 / 2000 / 2010 / 2020 — **partial**;
only the most-polarized 2020 release tips to "real"), and the **2025
durable Δaff is now ~+0.078** (was ~+0.017 before the fix), so the
"persistent effect" claim is now genuinely **true**. The declared public
bucket is **partial** on the cross-release mean. Δsep is null
(−0.006 to −0.008). The sustained mechanism also *raised* the magnitude
(+10y cross-release ~+0.086 → +0.133) — an honest consequence of
sustained-vs-one-shot contact, anchored to the Pettigrew halving and
still inside the partial envelope (< the +0.30 cap), not juicing. X6
remains the strongest — and the only durable — affect lever. Null on
issue sorting: Mason 2018 / Gidron et al. 2020 predict contact moves
prejudice / affect more than issue positions, and the model confirms.
The lay framing: *the contact hypothesis works in the model, persists,
and lands at the magnitude the meta-analysis predicts*.

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

### 5.1 The conditional backfire — X1

Cross-partisan exposure is the depolarization lever most often
demanded in popular media and the one Bail's 2018 PNAS paper
found backfires under threat. After the R-phase R-D fix, the engine
reads it as **null on average with a conditional backfire** — not the
strong, decade-invariant backfire the doc previously claimed. The old
+0.33 figure came from an effectively **unconditional** affect gate
(~95% of partisans below the warmth threshold; §4.1), which over-
claimed Bail against the scholarly consensus. Threat-gating
(`BacklashRepulsion.threat_gated`) makes the repulsion fire only for the
post-2016 status-threat population, so the backfire surfaces only when
sustained exposure lands during active identity threat — the 2010
release (Δsep +0.077), with a null cross-release mean (+0.026).

This is still the cleanest naive-vs-engine contrast in the library, but
the honest framing is now **"exposure does nothing on average and
backfires only under active identity threat"** — faithful both to the
**null-on-average** consensus (Guess & Coppock 2020; Wood & Porter
2019) and to the **conditional** backfire (Bail 2018; Mutz 2018; Combs
2023). Graded **LOW / CONTESTED (MHV T0.2)**. There are now **zero
unconditional backfires** in the library.

### 5.2 The empirically-supported worker — X6

One intervention durably moves the needle.

**X6 (shared neighborhoods, workplaces, institutions)** lands
partial-helpful on affect within the Pettigrew-Tropp / Mousa
empirical envelope, and — after the R-phase R-C fix — that effect now
**persists to 2025** (the durable Δaff ≈ +0.078, where the one-shot
dose alone had retained only ~9%). The mechanism is the contact-
hypothesis literature's clearest empirical finding (r ≈ -0.21 across
515 studies); the engine reproduces it via a sustained cooperative-
share floor anchored to the meta-analytic "contact halves prejudice"
value. Lay framing: *the intervention with the strongest empirical
evidence behind it actually works in the model, persists, and lands
at the magnitude the meta-analysis predicts*.

(X5 was the second "worker" when it was ranked-choice voting; as
**Deprogramming & exit programs** it is now a null — see §5.3.)

### 5.3 The popular-but-doesn't-work — X2, X3, X4, X5, X7

Five nulls, distinct reasons:

- **X2** is an **earned** null — it genuinely zeroes the live
  social-media affect channel (`bc_affect_weight`), and the macro
  picture barely moves because that channel is deliberately weak
  (media paradox / Meta-2020). Before the R-phase R-A wiring fix it
  was a *dead-knob* null (the lever was shadowed and did exactly
  nothing); now it is a real reproduction of the Guess et al. 2023 null.
- **X3** is null because at 20% reach removing partisan cable is a
  small effect against the (R-phase-corrected, now centrifugal) media
  channel — genuinely LIVE (it zeroes Fox/MSNBC for the treated 20%),
  matching the Allcott 2020 20%-reach envelope.
- **X4** is null at the bucket cutoff because reach is 20% and
  duration matters less than mechanism — Voelkel 2024's
  ~0.04 SD floor is reproduced (Δaff ≈ +0.002 to +0.006), helpful in
  direction.
- **X5 (deprogramming)** is null because a targeted counter-extremism
  program reaches only the thin organized tail, which does not scale
  to aggregate separation — and it is **exactly** null pre-emergence
  (no factions to reach). Decade-gated, `[N]`-graded.
- **X7** is null *despite the mechanism working*: perception is
  successfully corrected for treated agents (genuinely LIVE), but the
  correction only matters at cross-party encounters, which are rare in
  a homophilous network (Lees & Cikara r ≈ −0.07; propagation limit,
  blindspot #2).

Unlike X2's former dead knob, **X3 / X4 / X7 are all confirmed LIVE
levers producing earned, measured-small nulls** (R-phase R-B), each
matching a real literature finding. The five distinct null reasons let
the demo say something more than "the popular interventions don't
work" — it lets it say *why each one doesn't*, with the engine's
per-mechanism diagnostics visible.

---

## 6. Provenance — what's literature, what's theory

Per-knob provenance tags (`[L:M]` / `[L:D]` / `[T]` / `[N]` / `[C]`)
are recorded in
[`phase10_interventions/redesign_briefs.md §0.1`](phase10_interventions/redesign_briefs.md).

<!-- TODO: verify — the exact cross-library per-knob tally below predates
     the X5 RCV→Deprogramming swap (which dropped 4 `[T]` knobs and added an
     `[N]`-graded deprogramming lever) and the R-phase X1/X2/X6 mechanism
     edits. Recompute from redesign_briefs.md §0.1 against the current
     interventions_phase6.py before re-blessing the counts. -->

Qualitatively after the swaps:

- **X6 (contact)** is the most empirically anchored — the sustained-
  contact floor is pinned to the Pettigrew & Tropp 2006 "contact halves
  prejudice" meta-analytic value (`[L:M]`).
- **X5 (deprogramming)** no longer carries RCV's four `[T]` knobs; its
  reach + full-exit magnitude is graded **`[N]`** — a design choice in
  the modest/contested deradicalization-efficacy envelope (Horgan /
  Koehler / Gielen).
- **X2 (algorithm)** is an `[L:M]`-anchored earned null (Meta-2020).
- **X1 (exposure)** rests on a `[T]`/`[L:D]` mix — the threat-gated
  conditional backfire is a mechanism pin combining Bail-direction with
  the Guess-Coppock null average.

The writeup discipline is unchanged: any `[T]`- or `[N]`-graded
intervention's bucket label should be read as *"the engine says this
mechanism produces this effect"*, not *"the literature predicts this
effect."*

---

## 7. Honest limitations

1. **Sustained-policy framing for X1, X4, X7.** Literature
   measures one-shot doses with short follow-ups; the engine
   measures sustained 60-tick interventions. X4's direction-
   rightness and X7's correction window are extrapolations on
   the sustained-policy framing.
2. **20% treated-fraction speculation.** X3, X4, X7 use 20%
   reach as a `[T]` value (X5 uses a 50% reach over the thin
   faction-tagged tail). The 5% / 20% / 50% sensitivity
   sweep is deferred to Phase 11.
3. **X7 propagation limit.** The null reading depends on the
   homophilous-network assumption. A less-sorted network would
   propagate perception correction further (blindspot #2).
4. **X1 threat-gating is a design choice.** The R-phase fix makes
   the backfire conditional on the engine's `perceived_threat`
   field (`BacklashRepulsion.threat_gated`); which agents are
   threatened, and when, is set by Phase 9's post-2016 threat
   schedule. The null-on-average / 2010-backfire split is therefore
   an honest *mechanism* prediction, not an out-of-sample one —
   the conditional backfire is visible only because the engine
   already encodes who carries status threat in the polarized era.
   (The old "no clean moderate backfire between 0.05 and 0.06 /
   reported +0.33" limitation is obsolete: with threat-gating the
   strength→Δsep response is smooth, re-anchored at strength 0.20.)
5. **X6 durability rests on a sustained floor.** X6's persistence
   to 2025 comes from holding a cohort-proof cooperative-share floor
   (`sandbox_contact_share`) for the rest of the run — the
   sustained-institutions design choice (Pettigrew-Tropp anchor),
   not an emergent property of the one-shot contact dose (which
   mean-reverts via R7 and erodes via cohort turnover).
6. **X5 evidence is `[N]`, not theoretical-electoral.** As
   deprogramming, X5's reach + full-exit magnitude is a design
   choice in a contested deradicalization-efficacy envelope
   (Gielen 2019 review); the lay framing has to flag `[N]` and the
   targeted-tail-doesn't-scale finding.

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
  the results doc — `[L:M]` / `[L:D]` / `[T]` / `[N]` / `[C]`. The UI
  can surface this so users see which buckets are empirically
  grounded vs theoretical / design extrapolations (e.g. X5's `[N]`
  deprogramming reach).
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
consolidated bucket test in `tests/test_phase6.py`
(`test_intervention_library_directions_hold`) is the regression
lock — it measures each lever's Δ on the **ANES historical arc**
(the `intervention_buckets_arc` fixture, 9 seeds × 4 release
decades — the substrate the public buckets are blessed against),
and fails if any measured bucket drifts off its declared tag.

The story the library tells, in one sentence: *most depolarization
interventions people loudly demand don't move the macro picture in
this model; the one durable helper is structural (shared institutions
/ contact); cross-party exposure backfires only under active identity
threat (null on average, never unconditionally); and the engine can
tell you, for each one, **why**.*
