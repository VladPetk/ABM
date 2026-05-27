# Phase 8c — Roadmap

*Organizational doc. Phase 8c addresses the must-do + high-value items
from the two external expert reviews (`review_synthesis.md`,
`review_polarization_expert.md`, `review_abm_math_expert.md`). The
defer tier — HK phase-diagram test, income/inequality channel,
detailed demographic stratification, full factorial / Sobol
identifiability decomposition — is explicitly OUT of 8c scope.*

*This document organizes the in-scope work into ordered sub-phases
with scope, dependencies, estimated work size, and the judgment
forks the roadmap itself surfaces. Each sub-phase will get its own
spec at the normal spec-gated cadence after Vlad confirms the
roadmap.*

---

## Confirmed in-scope (the full list)

**Engine extensions (6):**
- E1. Per-outlet, per-agent media exposure (X3 category-error fix).
- E2. Positive-going affect channel (`AffectiveUpdate` rewrite).
- E3. Agent-level cooperative-conditions mute (Pettigrew 2009
  secondary transfer).
- E4. Perception-gap (meta-perception) construct.
- E5. Identity-threat mechanism (Mutz 2018 status-threat).
- E6. Asymmetric `BacklashRepulsion` (Bail 2018 R-leaning).

**Intervention library cleanup (5):**
- I1. X3 re-implementation against per-outlet exposure.
- I2. X6 re-measurement under agent-level cooperative mute.
- I3. X1 asymmetric + magnitude correction.
- I4. X4 reframe (shared-identity prime *or* contact-program rename).
- I5. X7 perception-gap-correction intervention (new).

**Statistical-robustness pass (3):**
- S1. Pillar 12 → 20 seeds; historical-arc 5 → 15 seeds; re-bless any
  labels that shift.
- S2. Bucket-cutoff sensitivity sweep ({0.03/0.10}, {0.05/0.15},
  {0.08/0.20}).
- S3. Point-estimate ± SE in methods.md and all results docs.

**Docs + tags + math fixes (6):**
- D1. Provenance L/N/E audit (cooperative-mute → E; ADR-001 + Mutz /
  Huckfeldt-Sprague; Wong et al. → E; graded logistic flag departure;
  X4 anchor; Iyengar/Finkel attribution).
- D2. Phase 6 R5 sign-convention contradiction (§1 vs §9).
- D3. Phase 5 §3.2 normalization where issue distance can reach 1.89,
  not 1.0; valence baseline adjusted accordingly.
- D4. methods.md §3.1 ANES projection explicit note (test guards
  trajectory shape, not anchor agreement).
- D5. FJ realization clarity in methods.md §3 (per-rule (1−s) scaling
  sums pulls before damping — departs from canonical FJ).
- D6. Affect-gate diagnostic firing rate reported in §11.

---

## Proposed sub-phase ordering

Seven sub-phases. The order reflects dependencies (docs/math first
to surface inconsistencies; engine extensions before the intervention
re-measurements that depend on them; statistical pass last so every
label re-bless uses the new ensemble).

### 8c.1 — Docs, tags, and small math fixes (D1–D6)

**Scope.** Six low-risk, no-compute, no-engine-change items:
provenance audit, sign-convention fix, normalization fix, ANES note,
FJ clarity, affect-gate firing-rate diagnostic.

**Out of scope.** Any engine logic; any threshold re-measurement.
Doc-only changes plus the §3.2 normalization arithmetic correction.

**Dependencies.** None. Should land first because (a) the §3.2
normalization correction affects downstream affect measurements, and
(b) the provenance audit informs how new mechanisms in 8c.2–8c.6 are
labelled when introduced.

**Size.** Half-day to a day. No compute.

---

### 8c.2 — AffectiveUpdate rewrite: positive-going channel + agent-level cooperative mute (E2, E3, I2)

**Scope.** Rewrite `AffectiveUpdate.apply` to support positive-going
valence (in-party warmth growth, cooperative-encounter positives,
exogenous warmth shocks via the Schedule). Add `agent.state.attrs[
"cooperative_share"]` (or equivalent) for Pettigrew 2009 secondary-
transfer: contact reduces overall prejudice formation, not just
toward contact targets. Re-measure pillar S2-S4 affect trajectory;
re-bless any pillar thresholds that shift. Re-measure X6 under the
new agent-level cooperative mute; bless the new label.

**Out of scope.** Per-outlet media (separate sub-phase); perception-
gap or identity-threat dynamics (8c.4, 8c.5).

**Dependencies.** D3 (Phase 5 §3.2 normalization fix) must land
first — the new valence formula depends on the corrected
normalization. Otherwise self-contained.

**Size.** 2–3 days. Pillar re-measurement = full 73-test suite +
intervention bucket re-bless on X6.

---

### 8c.3 — Per-outlet, per-agent media exposure (E1, I1)

**Scope.** Refactor `MediaConsumption` so each agent has a per-outlet
exposure weight rather than a single aggregated `diet_target`. New
agent attribute `media_exposure: {outlet_id: weight}`. Each outlet
exerts its own pull on the agent (centrifugal partisan-cable + the
distinct centripetal force of broadcast/local) — R1's "category
error" fix. Pillar-fallback discipline: existing scenarios get the
aggregated `diet_target` path; historical_arc opts into per-outlet.
X3 re-implementation: "quit cable news" now means zeroing exposure to
partisan-cable outlets specifically, leaving centrist/broadcast alone.
Re-measure X3 bucket.

**Out of scope.** Anything other than the media-exposure refactor and
the X3 re-measurement.

**Dependencies.** None mechanically (independent of 8c.2), but should
land after 8c.2 so X3's re-measurement happens against the corrected
affect dynamics.

**Size.** 2 days. Pillar re-measurement (X3 was the only intervention
with a backfire-on-issue-sorting reading; re-blessing is contained).

---

### 8c.4 — Perception-gap (meta-perception) construct + X7 (E4, I5)

**Scope.** New agent attribute `perceived_other_party`: each agent
carries a perceived position for the other party's centroid (initially
seeded with an overestimate of extremity — the empirical perception-
gap finding from Levendusky & Malhotra 2016, Ahler & Sood 2018,
Druckman et al. 2022). New dynamics: perceived position updates with
encounters (slow correction toward observed reality) and with
exogenous events (media-driven re-misperception). Wire perception-gap
into AffectiveUpdate's valence so the gap drives affect (when an
agent perceives the out-party as more extreme than reality, affect
cools faster than the encounter alone would). X7 "Correct the
perception gap" intervention: one-shot reset of all agents'
`perceived_other_party` to the actual centroid.

**Out of scope.** Identity-threat (separate sub-phase, though they
may couple — see fork 4 below). Continuous endogenous gap-drift
mechanics beyond the basic encounter update.

**Dependencies.** 8c.2 (AffectiveUpdate must already support
gap-driven valence shape; the gap is wired into the rewritten apply
method).

**Size.** 3–4 days. New attribute + new dynamics rule + intervention
+ bucket measurement + methods.md anchoring section.

---

### 8c.5 — Identity-threat mechanism (E5)

**Scope.** New agent attribute or env attribute `perceived_threat`:
agents (or party-level) experience identity threat in response to
exogenous events (Mutz 2018 status-threat — the empirical anchor
for the 2016 affect spike). Threat amplifies BacklashRepulsion and
AffectiveUpdate intensity while active. Mechanism is endogenous-plus-
event-triggered. The historical scenario schedules a 2016 threat
event; the pillar runs with the mechanism inert. No new intervention
in 8c.5 — this is mechanism only.

**Out of scope.** No new intervention library entry. Identity-threat
is a mechanism extension that fuels the 2016 affect spike in
historical_arc, not a depolarization lever.

**Dependencies.** Optionally couples with 8c.4 (perceived-out-party-
extremeness → perceived-threat). The judgment fork on coupling is
flagged below (Fork 4).

**Size.** 2 days. New attribute + new rule + Schedule entry for 2016
+ pillar invariant verification.

---

### 8c.6 — Asymmetric BacklashRepulsion + X1 + X4 reframe (E6, I3, I4)

**Scope.** Add per-party asymmetric multiplier to `BacklashRepulsion`
(Bail 2018: Republican users more susceptible). Existing
`affect_threshold` stays. X1 re-implementation under the asymmetric
push; re-measure; magnitude should come down toward Bail's effect
size (currently +0.50, empirically should be < 0.10). X4 reframe per
fork 2 below.

**Out of scope.** Anything beyond the BacklashRepulsion asymmetry, X1
re-measurement, and the X4 reframe decision.

**Dependencies.** 8c.2 (AffectiveUpdate rewrite — X1's mechanism
fires on affect-below-threshold; the new positive-going affect
trajectory may change firing rates). 8c.5 (identity-threat couples
with BacklashRepulsion intensity if the asymmetric multiplier is
threat-aware).

**Size.** 1–2 days. Small engine change + two intervention
re-measurements + X4 decision.

---

### 8c.7 — Statistical-robustness pass (S1, S2, S3)

**Scope.** Bump seed counts: pillar 12 → 20; historical-arc 5 → 15.
Re-run §11 bucket measurements at the larger ensembles; re-bless any
labels that shift. Bucket-cutoff sensitivity sweep at {0.03/0.10},
{0.05/0.15}, {0.08/0.20} — report bucket labels under each cutoff
configuration and defend the chosen 0.05/0.15 (or replace if the
sweep argues for different). Add SE reporting to methods.md and all
results docs (every published metric gets point ± SE).

**Out of scope.** New mechanisms; new interventions. Pure statistical
re-measurement.

**Dependencies.** Must be last. All engine extensions (8c.2–8c.6) and
all intervention re-measurements (X1, X3, X4, X6, X7) must land
first; the statistical pass re-measures the final library at the
larger ensembles.

**Size.** 2–3 days. Compute: pillar 12→20 (~1.7× pillar runtime
multiplier) + historical 5→15 (3× historical runtime multiplier) +
cutoff sweep × library size. Estimated 8–15 hours of compute
overall.

---

## Sub-phase ordering with dependencies

```
8c.1 (docs + math)
  ↓
8c.2 (affect rewrite + agent-level coop + X6)
  ↓
8c.3 (per-outlet media + X3)           ←┐
  ↓                                      │ no hard order between 8c.3/4/5/6;
8c.4 (perception-gap + X7)              │ dependencies are mainly that they
  ↓                                      │ all need 8c.2 first.
8c.5 (identity-threat)                  │
  ↓                                      │
8c.6 (asymmetric repulsion + X1 + X4)  ←┘
  ↓
8c.7 (statistical-robustness pass)
```

The middle sub-phases (8c.3–8c.6) can in principle run in any order
once 8c.2 lands; the proposed sequence (3 → 4 → 5 → 6) reflects
rough work-size ordering and the natural narrative flow. If a
particular sub-phase surfaces a blocking issue, the order can shift.

**Total estimated work:** 12–18 days across 7 sub-phases. Compute
budget for 8c.7 alone: 8–15 hours.

---

## Judgment forks the roadmap surfaces

Six genuinely new forks emerged from organizing the work. Each is
flagged here for Vlad's call; they'll be re-flagged at each
sub-phase's spec time.

### Fork 1 — Cooperative mute: replace or supplement?

**8c.2 decision.** Vlad's brief said the agent-level cooperative
mute is "an alternative to *or replacement for* the current edge-
level mute." Two paths:

- **(a) Replace edge-level entirely.** Cleaner; one mechanism; more
  faithful to Pettigrew 2009 secondary transfer (contact reduces
  overall prejudice, not just at contact targets). Simpler model.
- **(b) Keep edge-level + add agent-level.** Two mechanisms;
  edge-level captures per-encounter Allport-conditions; agent-level
  captures generalization. More nuance, more parameters, harder to
  defend single-handed.

**Roadmap default: (a) replace.** Cleanest reading of the
secondary-transfer literature; matches the polarization expert's
critique that X6 needs a literature-faithful agent-level mute. Open
to (b) if Vlad wants both readings reported side-by-side.

### Fork 2 — X4 reframe: rename or re-implement?

**8c.6 decision.** Vlad's brief said either re-implement as shared-
identity-prime intervention *or* rename to a contact-program
citation that matches the existing mechanism. Two paths:

- **(a) Rename + re-anchor.** Keep the current mechanism (add cross-
  party voluntary ties + affect reset); re-anchor citation to Mutz
  2006 / Allport / Pettigrew & Tropp. Zero engine work. Honest about
  what the model actually does.
- **(b) Re-implement as shared-identity prime.** New small setup
  function: one-shot reset of `identities` toward a shared-American
  centroid for participants; possibly a one-shot affect bump.
  Re-anchor citation to Levendusky 2021 *Our Common Bonds* (correctly
  this time). New mechanism but small.

**Roadmap default: (a) rename + re-anchor.** Less engine work;
preserves the X4 mechanism that has been measured already; honest
provenance. (b) is also fine if Vlad wants the Levendusky 2021
anchor to actually correspond to the implemented mechanism. (b)
costs ~1 day of additional engine work.

### Fork 3 — X3 re-implementation: clean split or sub-variants?

**8c.3 decision.** Two paths:

- **(a) Re-implement X3 against per-outlet exposure.** "Quit cable
  news" = zero exposure to partisan-cable outlets (Fox, MSNBC),
  leaving broadcast/local exposure intact. One intervention, one
  bucket reading. The centripetal/centrifugal forces separate
  naturally because the model now tracks them separately.
- **(b) Keep X3 as-is + add X3a "Quit partisan cable" and X3b "Cut
  all media."** Three interventions in the library; explicit test
  of which media-quit channel matters. More demonstrative but
  inflates the intervention menu.

**Roadmap default: (a) clean re-implementation.** Matches the
"category error" framing — the model should not bundle distinct
empirical phenomena into one intervention. X3's bucket may change
under (a); that's the honest re-measurement.

### Fork 4 — Perception-gap vs identity-threat: independent or coupled?

**8c.4 / 8c.5 design decision.** Two paths:

- **(a) Independent constructs.** Each agent carries
  `perceived_other_party` (positional misperception); `perceived_
  threat` is a separate scalar/event-triggered attribute. The two
  do not feed each other directly. Cleaner separation; easier to
  ablate independently.
- **(b) Coupled.** `perceived_threat` is derived from `perceived_
  other_party` (when out-party perceived as extreme, threat rises).
  Mutz 2018 status-threat dynamics naturally couple with perceived
  out-party threat-extremity. Stronger model; more parameters; harder
  to ablate cleanly.

**Roadmap default: (a) independent.** Easier to test and ablate;
identity-threat can be triggered by exogenous events independent of
perception-gap state. Allows clean attribution in 8c.7's ablation.
(b) is the richer model but adds an internal feedback loop that
needs care.

### Fork 5 — Positive-going affect triggers: which sources?

**8c.2 design decision.** Vlad's brief mentions Obama-2008,
post-9/11, and 2016 thermometer reversals. The mechanism question:
*what* in the model corresponds to a positive-going affect update?
Candidates:

- **(a) Exogenous shocks only.** Schedule events fire one-shot
  positive affect bumps (e.g., Obama 2008 → 9-tick warming;
  post-9/11 → one-shot unity bump). Easy to implement; tied
  directly to historical events.
- **(b) Cooperative encounters (Pettigrew 2009 secondary transfer).**
  Cooperative-tagged edges produce positive-going valence under
  certain conditions, not just attenuated negative.
- **(c) In-party warmth growth.** Affect toward in-party (currently
  not modelled — only out-party warmth is tracked) grows with
  in-party encounters.
- **(d) All three.** Maximally rich; matches Mason 2018's full
  identity-affect picture.

**Roadmap default: (a) + (b).** Exogenous shocks (events) for the
big empirical reversals + cooperative-encounter positives (Pettigrew
secondary transfer). Skip in-party warmth as separate channel for
now (the model's `affect` dict currently keys on out-party only;
adding in-party would be a substantive extension). (c) is genuinely
out of 8c scope.

### Fork 6 — Statistical-robustness compute budget

**8c.7 budget confirmation.** Pillar 12→20 seeds + historical 5→15
seeds + bucket-cutoff sensitivity sweep = estimated 8–15 hours of
compute. The seed-bump alone re-runs every §11 measurement; the
sensitivity sweep re-classifies every intervention under three
cutoff schemes. Compute budget is approved per Vlad's brief but
worth re-confirming when 8c.7 actually starts.

**No fork** — this is just a budget check, not a modeling decision.
But worth pinning explicitly at 8c.7 spec time.

---

## What this roadmap does NOT cover

- **The HK phase-diagram test** (R2's recommendation #6) — explicitly
  deferred per Vlad.
- **Income / inequality channel** — deferred.
- **Detailed demographic stratification** (race × religion × education
  × geography beyond cohort replacement) — deferred.
- **Full factorial / Sobol identifiability decomposition** — deferred.

These would be Phase 8d candidates if they prove necessary after 8c.

---

## Sign-off

Sub-phases 8c.1–8c.7 organize the confirmed work. Six judgment
forks need Vlad's calls (or his go-ahead on the roadmap defaults).
The estimated 12–18-day total + 8–15-hour compute budget is
substantial but tractable.

**Standing by for Vlad's confirm on the roadmap before any
sub-phase spec is written.** Each sub-phase will get its own spec
at the normal spec-gated cadence after roadmap confirmation.
