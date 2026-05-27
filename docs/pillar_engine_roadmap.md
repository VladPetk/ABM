# Engine Roadmap — Building One Validated Pillar

*Scope: the simulation engine only. No UI, no website, no user-journey design.
The goal is to take the engine from where it is today to a state where it can
run one complete journey "pillar" — a staged progression of mechanisms — in a
way that is reproducible, composable, and validated against the literature.*

---

## 1. What this document is

A pillar is one ordered story the engine can tell: a society starts neutral,
and we add one mechanism at a time, each with a known, literature-backed
directional prediction. The reference pillar we are targeting:

> **baseline → bounded confidence → party identity → partisan media → homophilous social network**

The stage list is **final** and fully specified in `pillar_spec.md`. The fifth
stage is a homophilous tie network — the well-supported "social circles"
mechanism, not the contested algorithmic filter bubble (see §4, R2).
Public-facing copy may still call it an "echo chamber"; what the engine models
and what the project claims is network homophily.

This is deliberately an engine-first plan. We are not building interventions
the public will click yet. We are building the machinery that a single
validated journey needs, and proving it on the cheapest possible content
first.

---

## 2. Where the engine stands today

The codebase is in good shape and the architecture is the right one. The core
(`abm/core/`, `abm/rules/`, `abm/scenarios/`, `abm/metrics/`) is pure Python
with no framework imports. Rules are composable: each returns a `StateDelta`,
deltas are summed and applied synchronously, so rule order does not bias
dynamics. Agent and environment state are open `attrs` dicts, so new fields
need no class changes. This is a solid foundation and none of it needs to be
torn up.

**What already exists and works**

- Mechanisms (as `Rule` / `EnvRule` classes): bounded confidence
  (`BoundedConfidenceInfluence`), Mäs-Flache argument exchange
  (`ArgumentExchange`), party-cue pull (`PartyPull`), identity sorting
  (`IdentitySorting`), affective update (`AffectiveUpdate`), per-agent media
  diet (`MediaConsumption`), episodic media shocks (`MediaShock`), elite drift
  (`EliteDrift`), backlash repulsion (`BacklashRepulsion`), noise.
- Five scenarios wiring those rules: `compass_basic`, `actb`,
  `two_party_sorting`, `multi_party_4`, `elite_dynamics`.
- Metrics: variance, mean pairwise distance, bimodality, affective
  polarization, sorting index, ideological constraint, plus a cross-talk
  approximation in the web layer.
- A clean engine/UI seam: `abm/web/scenarios_meta.py` already separates
  academic rule names from plain-English labels and live-mutates rule
  attributes via `apply_param`.

I ran the engine to confirm behavior: `compass_basic` (Hegselmann-Krause)
converges (variance 0.66 → 0.55 over 100 ticks), and `actb` (Mäs-Flache)
bi-polarizes without any repulsion (variance 0.66 → 1.46, bimodality rising) —
both as the literature predicts.

**What is missing or broken — the gap between here and "one validated pillar"**

| # | Gap | Why it blocks the pillar |
|---|-----|--------------------------|
| G1 | **No "pillar" / "stage" abstraction.** Every scenario hard-wires its full rule pipeline at `build()` time. | A pillar needs mechanisms to switch on *in sequence* over one population. There is no object representing "the ordered steps." |
| G2 | **`apply_param` can change a rule's scalar attribute, but cannot add or remove a rule.** (`scenarios_meta.py`) | "Add party identity" mid-journey is currently impossible unless the rule is already in the pipeline. |
| G3 | **No agent-subset targeting.** Rules apply to every agent uniformly. | Later interventions ("put *these* agents in an echo chamber", "lower knowledge *here*") need cohorts. Not needed for stage 1 of the pillar, but the design must not preclude it. |
| G4 | **No network / exposure layer.** `ContinuousSpace2D` returns *every* agent within a geometric radius. There is no model of *who you can see*. | The "echo chamber" stage is fundamentally about restricting exposure. The engine currently cannot express it. This is the one genuinely new capability the pillar needs. |
| G5 | **No automated test suite.** `pytest` is declared as a dev dependency but `tests/` does not exist. "Validation" is `scripts/compare.py`, which prints numbers for a human to eyeball. | "Validated" requires assertions that fail loudly when dynamics drift. |
| G6 | **`compare.py elite` is broken.** It calls `build()` with `partisan_media_strength=`, an argument `elite_dynamics.build()` does not accept — confirmed `TypeError` on run. | One third of the existing validation does not execute at all. |
| G7 | **Single-seed validation.** Every `compare.py` run uses `seed=0`. | A stochastic model validated on one seed is an anecdote. Validation must run an ensemble. |
| G8 | **Minor debt:** `PartisanMediaExposure` (scalar `media_diet`) is dead code, superseded by `MediaConsumption` (dict diet); the `epsilon` slider is mapped to *two* unrelated rule attributes (`BoundedConfidenceInfluence.epsilon` **and** `AffectiveUpdate.radius`, which `build()` initialises to a different value, 1.5). | Not blocking, but each is a latent inconsistency that will corrupt a validation target if left. |

---

## 3. The core design decision

There are two ways to make mechanisms switch on in sequence. We should commit
to one before writing code.

**Option A — rebuild per stage.** Each stage rebuilds the engine with a
different rule pipeline. Simple, but every stage transition discards the
running society and restarts from t=0. Bad for the journey (the whole point is
watching a *continuous* society change).

**Option B — superset pipeline, strengths as the dial. ✅ Recommended.**
Build the pillar's population *once*, with every attribute any later stage will
need (party, identities, media diet, cohort tags). Build the rule pipeline
*once* containing every mechanism in the pillar — but with later/contested
mechanisms at **strength 0**, where they are exact no-ops (every rule already
early-returns on zero strength; this is existing behavior). Advancing a stage
is then nothing more than applying a **bundle of strength changes**.

This is the same idea from our earlier conversation — *the parameter is the
engine, the intervention is the interface* — applied to the pillar's own
steps. It gives us, for free:

- **Live mode** (the journey): mutate strengths on the running engine; the
  society continues evolving as each force is added. Reuses `apply_param`.
- **Cold mode** (validation): build fresh, apply a stage's *cumulative* bundle
  at t=0, run, assert. Each stage is independently testable.
- One unified entry point. A pillar stage and a future free-play intervention
  ("add a media campaign") are the *same kind of object*: a named bundle of
  changes.

The one exception is **G4, the exposure layer** — restricting who an agent can
see is structural, not a strength. That needs a real engine change (a
pluggable exposure provider, §6 Phase 3), which is why the echo-chamber stage
is sequenced last and gated on a research decision.

**The data contract.** Define one small declarative type — call it
`Intervention` — and a `Pillar` is an ordered list of them:

```
Intervention:
  id              # stable identifier
  label           # human name ("Add partisan media")
  description     # one sentence, plain English
  param_bundle    # {(RuleName, attr): value}  — the strength changes
  setup           # optional fn(engine) for structural changes (Phase 3+)
  citation        # the paper(s) this stage is grounded in
  predicted_effect# the directional claim ("affective polarization deepens")
  validation      # reference to the test that checks it
```

A `Stage` of a pillar is just an `Intervention` whose `param_bundle` is the
*cumulative* state of the world up to that step. The engine never needs to
know about pillars or stages — it only needs to reliably apply a bundle. All
pillar/stage structure lives in a metadata layer (a new `abm/pillars/`
package), exactly as `scenarios_meta.py` is the metadata layer today.

---

## 4. Research decisions — resolved

The research file (`political_polarization_research.md`) is strong — a genuine
literature review with citations, correctly separating affective from
ideological polarization and mapping the canonical ABM families. Five research
questions had to be answered before coding. All five are now **resolved**;
the rationale is recorded here so it travels with the plan.

**R1 — Pillar finalized.** The five-stage pillar in §5 is committed:
baseline → bounded confidence → party identity → partisan media → homophilous
social network. The full definition — mechanism, citation, predicted effect,
validation target and honesty label per stage — lives in `pillar_spec.md`.

**R2 — The echo-chamber stage is a homophilous tie network.** The contested
claim is the *algorithmic filter bubble* (Reuters Institute review 2022; Guess
et al. 2023 and Nyhan et al. 2023 null findings) — that is not what we model.
The robust claim is *network homophily*: political discussion networks are
politically lopsided, a finding that predates social media (McPherson,
Smith-Lovin & Cook 2001; Mutz 2006; Huckfeldt & Sprague 1995). S4 models a
homophilous tie network and claims **amplification, not creation** — the social
circle does not invent views, it insulates the sorting that S2/S3 produced and
makes de-polarization slow. The echo chamber is a *ratchet, not an engine*.
Implementation: a static homophily-biased network first; tie co-evolution
(rewiring) is a later extension. Public copy may still say "echo chamber"; the
model and the claim are network homophily.

**R3 — Validation is qualitative / directional.** Each stage must produce the
*expected direction* of effect; matching published magnitudes exactly is not
required for the first pillar. Quantitative calibration (and the unit bridge
from vote-share / thermometer degrees into the model's [-1, 1] space) is
deferred.

**R4 — Moot for this pillar.** The Mäs-Flache `h`-threshold question applied
only to the argument-exchange route, which is *not* a stage in the final
pillar. It is deferred along with the `actb` scenario.

**R5 — Simplified rules are labelled "illustrative."** `AffectiveUpdate`,
`PartyPull` and `MediaConsumption` are abstractions of their source papers,
not literal replications. Each stage carries an explicit "replication" vs.
"illustrative mechanism" tag (see `pillar_spec.md`), and the Methods page will
use the same tags. Only the bounded-confidence stage is tagged "replication."

**Residual (light, handled in-phase, not a blocking lit review).** Two small
items remain: choosing the S4 network-generation method and an
exposure-diversity metric (Phase 3), and calibrating the starting strength
values (Phase 2).

---

## 5. Pillar stages mapped to the engine

The committed pillar. It shows how much is already built (the answer: most of
stages 0–3) and isolates where the real work is.

| Stage | Mechanism added | Engine rule | Status | Citation | Predicted effect (validation target) |
|-------|-----------------|-------------|--------|----------|--------------------------------------|
| S0 Baseline | none (noise only) | `GaussianNoise` | ✅ exists | — | No clustering and no bimodality; any drift is pure noise diffusion. |
| S1 Bounded confidence | who you'll listen to | `BoundedConfidenceInfluence` | ✅ exists | Hegselmann-Krause 2002 | Loose ε → one consensus blob; tight ε → multiple clusters. Reproduce the HK phase behavior. |
| S2 Party identity | elite cue / party loyalty | `PartyPull` (+ parties in env) | ✅ exists | Hetherington 2001; Levendusky 2009 | Clusters align to party centroids; ideological constraint (party-issue correlation) rises. |
| S3 Partisan media | media diet pulls consumers out | `MediaConsumption` (+ `EliteDrift`) | ✅ exists | Levendusky 2013; Martin-Yurukoglu 2017 | Heavy-diet agents drift further than light-diet agents; affective polarization deepens. |
| S4 Homophilous network | who you actually know | **new exposure provider** | ❌ **to build (G4)** | McPherson et al. 2001; Mutz 2006 | Cross-cutting exposure falls; the sorted state becomes *sticky* — de-polarization slows. Amplification, not creation. |

The headline: the mechanisms for S0–S3 already exist as tested-by-eye rules.
The pillar work for those stages is *assembly and validation*, not new
modelling. The genuinely new engine capability is S4's exposure provider.

---

## 6. The work, phased

Sequenced as a **vertical slice**: prove the entire apparatus end-to-end on the
smallest possible pillar first, then widen. This surfaces every integration
seam early and keeps a runnable, demoable artifact alive at all times.

### Phase 0 — Decide (no code)

- Close research gaps R1–R5.
- Write `pillar_spec.md`: the final stage list; per stage the mechanism,
  citation, predicted effect, validation target, and replication/illustrative
  label.
- Lock the `Intervention` data contract from §3.
- **Done when:** `pillar_spec.md` exists and every stage has a concrete,
  checkable validation target written down.

### Phase 1 — Thin vertical slice (S0 → S1 only)

The point of Phase 1 is to build the *whole machine* and run only two stages
through it. Two stages is enough to exercise every seam.

- New package `abm/pillars/`: a `Pillar` (population builder + ordered
  `Intervention` list) and the `Intervention` type.
- Build the pillar population **once** with the superset of attributes; build
  the rule pipeline **once** with every pillar mechanism present, later ones at
  strength 0.
- `apply_intervention(engine, intervention)` — generalize `apply_param` from a
  single scalar to a bundle. Phase 1 only needs scalar bundles.
- New `tests/` directory + `pytest` config. First tests:
  - S0: variance stays within noise band over N ticks.
  - S1: with loose ε the population converges; with tight ε it does not —
    the Hegselmann-Krause phase behavior.
  - **Multi-seed:** every assertion runs over an ensemble (≥10 seeds) and
    checks the ensemble mean against a tolerance, not a single run.
- Fix **G6** (`compare.py elite`) en route, or fold `compare.py` into the new
  harness and retire it.
- **Done when:** `pytest` is green, the 2-stage pillar runs deterministically
  in both live and cold mode, and the HK prediction is asserted across seeds.

### Phase 2 — Widen the pillar (add S2, S3)

The mechanisms exist; this phase is assembly + validation.

- Add `PartyPull`, `MediaConsumption`, `EliteDrift` to the superset pipeline at
  strength 0; give parties/diets to the population at build time.
- Define the S2 and S3 cumulative bundles as `Intervention`s.
- Validation tests: S2 — ideological constraint rises when `PartyPull` engages;
  S3 — partition agents by media-diet weight and assert heavy-diet drift >
  light-diet drift.
- Add any missing metric the targets need (e.g. per-cohort mean drift).
- Resolve **G8** here: delete dead `PartisanMediaExposure`; give
  `AffectiveUpdate.radius` its own lever instead of sharing the `epsilon`
  slider.
- **Done when:** a 4-stage pillar runs, each stage has a passing validation
  test, and a regression snapshot of the pillar's metric trajectory is pinned.

### Phase 3 — The exposure provider (S4) — the real new capability

This is the only phase that changes the engine itself rather than assembling
existing parts.

- Introduce a pluggable **exposure provider**: an interface the influence rules
  query for "who can this agent see," replacing the implicit "everyone within
  radius." Default provider = current geometric behavior (no behavior change
  for S0–S3).
- Implement a **static homophily-biased tie network** as the S4 exposure
  provider — ties formed with probability decaying in ideological / party
  distance; tie-formation homophily is the key parameter. (Tie co-evolution /
  rewiring is a later extension, not in the first pillar.)
- Add **G3**, agent-cohort targeting, here — a homophilous circle naturally
  applies to a *subset*, and this is the first stage that needs subsets.
- Add an exposure-diversity metric (cross-cutting share of each agent's ties)
  so the stage's effect is measurable.
- Validation = the **"ratchet" test**: a society carried to a polarized state
  then released (forces off) de-polarizes *more slowly* with the homophilous
  network than without — operationalizing "amplification, not creation."
- **Done when:** S4 exists, the cross-cutting-exposure metric responds, and the
  ratchet test passes — an honest, modest effect, not an oversized one.

### Phase 4 — Hardening

- Multi-seed ensemble runner as a first-class tool (mean ± CI over seeds).
- Full-pillar regression snapshots; a determinism audit (one RNG, seed
  threaded everywhere, no hidden `default_rng()` calls — note `_cross_talk` in
  the web layer currently spawns its own).
- A short `methods.md` documenting every calibration choice and its source —
  this is the artifact that backs the "intellectually rigorous" claim.
- **Done when:** the whole pillar has pinned regression coverage and a
  written, sourced methods note.

---

## 7. Validation harness — specification

This is the heart of "validated," so it gets its own spec.

- **Framework:** `pytest`, new `tests/` directory.
- **Canonical replication tests** (the "well-known simulations behave as
  expected" requirement): with the pillar mechanisms isolated, the engine must
  reproduce the textbook results — Hegselmann-Krause consensus/fragmentation
  across the ε threshold; Mäs-Flache bi-polarization without repulsion. These
  pin the engine to the literature independently of the pillar.
- **Per-stage prediction tests:** one test per pillar stage asserting that
  stage's directional prediction from `pillar_spec.md`.
- **Ensemble, not anecdote:** every stochastic assertion runs over ≥10 (target
  ≥20) seeds and tests the ensemble mean against a tolerance. No single-seed
  pass/fail.
- **Regression snapshots:** the pillar's metric trajectory at a fixed seed set
  is pinned to a file; any code change that shifts dynamics fails the snapshot
  and forces a conscious re-blessing.
- **Replaces `compare.py`:** the new harness subsumes it. Fix or retire the
  broken `elite` path (G6) rather than leaving it.

---

## 8. Definition of done — "one pillar in the engine"

The engine is ready for the journey work when:

1. A `Pillar` object exists: one population, one superset pipeline, an ordered
   list of `Intervention` stages.
2. Advancing a stage works in **both** modes — live (mutate a running engine)
   and cold (fresh build for validation) — deterministically under a seed.
3. Every stage has a passing, multi-seed validation test tied to a citation.
4. The canonical replication tests (HK, Mäs-Flache) pass.
5. The exposure layer (G4) exists and the echo-chamber stage runs.
6. `pytest` is green; the pillar has regression snapshots; `methods.md`
   documents the calibration.
7. No UI code was written. The engine exposes a clean `apply_intervention`
   seam and nothing above it assumes a particular front-end.

---

## 9. Decisions on record

The five questions that gated Phase 0, and the calls made:

| # | Question | Decision |
|---|----------|----------|
| 1 | Pillar definition | Committed: the five stages of §5; S4 is a homophilous tie network. |
| 2 | Echo-chamber model | Homophilous tie network — static first, co-evolving later. Claim = amplification, not creation. |
| 3 | Validation strictness | Qualitative / directional for the first pillar; quantitative calibration deferred. |
| 4 | Honesty labelling | Per-stage "replication" vs. "illustrative" tags; only bounded confidence is "replication." |
| 5 | Live-state on stage change | **Continuous** — the society keeps its positions; the journey never resets between stages. Validation still uses cold per-stage builds. |

With these settled, Phase 0 is complete and the work can begin at Phase 1.
