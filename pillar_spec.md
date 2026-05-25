# Pillar Spec — "How a Calm Society Becomes Two Camps"

*Phase 0 deliverable. The finalized definition of the first journey pillar:
its five stages, the engine mechanism behind each, the literature each rests
on, the predicted effect, and the validation target. This is the contract the
engine work in `pillar_engine_roadmap.md` builds against. It does not describe
UI.*

---

## The pillar

One society, five stages. Each stage adds exactly one mechanism. The society is
**continuous**: stages stack on the running population — positions carry over,
nothing resets between stages. (Validation runs each stage from a cold build;
the journey itself never does.)

> baseline → bounded confidence → party identity → partisan media → homophilous network

The arc: a neutral society is stable; people start listening only to those they
find reasonable; party cues give the clusters an address; partisan media pulls
heavy consumers outward; and the social network locks the result in place. The
first four stages *produce* polarization. The fifth does not — it *insulates*
it. That asymmetry is the intellectual payoff of the pillar.

Each stage is an `Intervention` in the sense of roadmap §3: a named, cumulative
bundle of parameter changes, plus — for S4 only — a `setup` hook for the
structural change.

---

## Stage-by-stage

### S0 — Baseline

- **Tangible framing:** "A society where nobody influences anybody."
- **Mechanism:** `GaussianNoise` only. Every other rule at strength 0.
- **Citation:** none — this is the experimental control.
- **Predicted effect:** nothing organized. No clusters, no bimodality. Agents
  random-walk slightly from noise alone.
- **Validation target:** after N ticks the population shows no clustering and
  no bimodality; variance change is consistent with pure noise diffusion (no
  collapse, no runaway).
- **Label:** control.

### S1 — Bounded confidence

- **Tangible framing:** "People stop listening to anyone too far from their own
  view."
- **Mechanism:** `BoundedConfidenceInfluence` switches on. Key parameters:
  `epsilon` (confidence radius, start 0.30), `strength` (start 0.08).
- **Citation:** Hegselmann & Krause 2002; Deffuant et al. 2000.
- **Predicted effect:** the Hegselmann-Krause result — a loose `epsilon` drives
  the whole population to a single consensus blob; a tight `epsilon` leaves
  several stable clusters that never merge.
- **Validation target:** sweep `epsilon`; assert loose `epsilon` yields one
  cluster (variance collapses) and tight `epsilon` yields ≥2 persistent
  clusters. Doubles as the canonical HK replication test.
- **Label:** replication — the rule is a faithful (relaxed) Hegselmann-Krause
  model.

### S2 — Party identity

- **Tangible framing:** "People take a side, and start drifting toward their
  team."
- **Mechanism:** `PartyPull` switches on (`strength` start 0.04).
  `AffectiveUpdate` switches on as well (start 0.01) to begin tracking
  out-party warmth — it feeds the affective-polarization metric and moves no
  ideology itself. Requires: two party centres in the environment; every agent
  carries `party` and `identity_strength` (present from build). `IdentitySorting`
  is available as an optional intensifier within this stage but is not required
  for the core prediction.
- **Citation:** Hetherington 2001; Levendusky 2009; (affect) Iyengar et al.
  2019.
- **Predicted effect:** clusters align to their party centroid; ideological
  constraint (party–issue correlation) rises; out-party warmth begins to fall.
- **Validation target:** ideological constraint at end-of-stage exceeds both
  its start-of-stage value and S1's value, across seeds.
- **Label:** illustrative mechanism — `PartyPull` abstracts elite-cue-taking
  rather than replicating a specific model.

### S3 — Partisan media

- **Tangible framing:** "Each person's media diet starts dragging them
  outward."
- **Mechanism:** `MediaConsumption` switches on (`strength` start 0.04).
  Requires: every agent carries a `media_diet` over named outlets, and outlets
  live in the environment (present from build). `EliteDrift` — party centres
  themselves drifting apart — is available as an optional co-active intensifier
  within this stage.
- **Citation:** Levendusky 2013; Martin & Yurukoglu 2017; (elite drift)
  McCarty, Poole & Rosenthal 2006.
- **Predicted effect:** heavy partisan-media consumers drift further toward the
  extremes than light consumers; party clusters separate faster; affective
  polarization deepens.
- **Validation target:** partition agents by media-diet partisanship; assert
  the mean outward drift of the heavy-diet quartile exceeds that of the
  light-diet quartile, across seeds.
- **Label:** illustrative mechanism.

### S4 — Homophilous network ("echo chamber")

- **Tangible framing:** "People's social circles close around them."
  (Public-facing copy may call this an echo chamber.)
- **Mechanism:** the engine's **exposure provider** swaps from "everyone within
  geometric radius" to a **homophilous tie network** — each agent is influenced
  through its ties, and ties were formed with a homophily bias (tie probability
  decaying in ideological / party distance). Key parameter: tie-formation
  homophily. A static network first; tie co-evolution (rewiring) is a later
  extension. This is the one stage that needs a structural engine change rather
  than a strength change — applied through the `Intervention.setup` hook (see
  roadmap G4 / Phase 3).
- **Citation:** McPherson, Smith-Lovin & Cook 2001; Mutz 2006; Huckfeldt &
  Sprague 1995; (mechanism) Flache & Macy 2011; DellaPosta, Shi & Macy 2015.
- **What it does NOT claim:** algorithmic filter-bubble causation. Guess et al.
  2023 and Nyhan et al. 2023 found null effects for algorithmic curation; the
  claim here is interpersonal network homophily only.
- **Predicted effect:** amplification, not creation. Cross-cutting exposure
  falls; the sorted state becomes *sticky*. The network does not push the
  clusters further apart on its own — it makes the existing separation
  resistant to reversal.
- **Validation target — the "ratchet" test:** run two societies through S0–S3
  to a polarized state, then switch the active forces off. The society with the
  homophilous network relaxes back toward the centre *more slowly* than the one
  without. This operationalizes "insulates, doesn't create."
- **Label:** illustrative mechanism.

---

## The superset population

Every agent is built once, at t=0, carrying every attribute any later stage
will need — so no stage transition ever requires a rebuild:

| Attribute | Purpose | Inert until |
|-----------|---------|-------------|
| `ideology` | 2D position, initialised near the centre with small spread | active S1 |
| `party` | party assignment (e.g. by starting side) | S2 |
| `identity_strength`, `identities` | identity-strength scalar and cross-cutting identity vector | S2 |
| `affect` | out-party warmth dict; populated by `AffectiveUpdate` | S2 |
| `media_diet` | weights over named outlets | S3 |
| network ties | per-agent tie list, formed at build with a homophily bias | S4 |
| `cohort` | subset tag for future targeted interventions; default `"all"` | future |
| `group`, `origin` | viz colour group and starting position | — |

---

## The superset pipeline

Built once, every mechanism present; everything except noise starts at
strength 0 — an exact no-op, since every rule already early-returns on zero
strength:

| Rule | Type | Active from | Start → stage strength |
|------|------|-------------|------------------------|
| `GaussianNoise` | agent | S0 | on (≈0.01) |
| `BoundedConfidenceInfluence` | agent | S1 | 0 → 0.08 |
| `PartyPull` | agent | S2 | 0 → 0.04 |
| `AffectiveUpdate` | agent | S2 | 0 → 0.01 |
| `IdentitySorting` | agent | S2 (optional) | 0 |
| `MediaConsumption` | agent | S3 | 0 → 0.04 |
| `EliteDrift` | env | S3 (optional) | 0 |
| `BacklashRepulsion` | agent | — (comparison runs only) | 0 |

S4 is not a row here — it is an exposure-provider swap applied via
`Intervention.setup`, not a strength change.

All strength values above are **first guesses**, to be calibrated in Phase 2
so each stage's validation target is met with a visible but not violent
effect.

---

## Validation summary

| Stage | Expected direction | Metric | Pass condition |
|-------|--------------------|--------|----------------|
| S0 | no organized change | variance, bimodality | no clustering, no bimodality |
| S1 | converge or cluster | variance, cluster count | HK phase behavior across `epsilon` |
| S2 | parties sort | ideological constraint | rises vs. S1 |
| S3 | heavy consumers extremize | per-quartile outward drift | heavy-diet drift > light-diet drift |
| S4 | sorting becomes sticky | de-polarization rate, forces off | slower with network than without |

Every assertion runs over an ensemble of ≥10 seeds (target 20) and tests the
ensemble mean against a tolerance. Directional only — magnitudes are not
pinned (decision R3).

Two **canonical replication tests** sit alongside the per-stage tests, pinning
the engine to the literature independently of the pillar: Hegselmann-Krause
consensus/fragmentation across the `epsilon` threshold, and Mäs-Flache
bi-polarization without repulsion (`actb` scenario).

---

## Residual calibration items

Not blocking — resolved inside the phase noted:

- **S4 network generation** — the exact tie-formation model (homophily-biased
  random graph vs. alternatives) and the cross-cutting-exposure metric.
  *Phase 3.*
- **Starting strengths** — the values in the pipeline table are first guesses;
  calibrate against the validation targets. *Phase 2.*
- **S4 composition** — whether the homophilous network *gates* the S1 geometric
  influence channel or *adds* a second channel alongside it. A design call,
  best made once the exposure-provider interface exists. *Phase 3.*
