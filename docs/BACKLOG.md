# polarlab — Backlog

*Running list of future work deferred from the active phase queue.
These are items the project considers worth doing eventually but
that are not in the current phase scope. Items are added when they
get flagged and stay until they're either pulled into a phase or
explicitly dropped.*

---

## High-interest follow-ups

### Sociodemographic stratification

**What it is.** Add real race, religion, education, and
urbanity attributes per agent, replacing the current 3-vector
abstract `identities`. Stratify population at build to match
empirical demographic distributions; let stratification interact
with party assignment, affect, and tie formation. Could enable
modeling specific historical realignments: the Obama coalition,
the diploma divide (Sides, Tausanovitch & Vavreck 2022), the
education-driven 2016 realignment, the racial-resentment-driven
asymmetric polarization (Hacker & Pierson 2020 structural read).

**Why deferred from 8c.** Substantial engine change requiring new
agent attributes, new build distributions, and new mechanisms (each
demographic dimension affects party identification differently, and
the interactions are non-trivial). Also requires per-decade
demographic calibration anchors. Big scope.

**Why worth picking up later.** Mason 2018's mega-identity argument
is *about* this stratification — the current 3-vector
`identities` is a stand-in. Adding real demographics would make the
historical replication considerably more realistic (e.g., the
1980 build's geometric tension that Phase 8b couldn't resolve may
actually be a missing-demographics issue, since 1980 partisans had
party-without-issue-coupling that's hard to represent without
demographic-coalition structure). Could also enable
demographically-targeted interventions in the demo.

**Rough effort.** A real chunk — likely comparable to Phase 8b
(several weeks of design + implementation + calibration). Worth
its own phase.

### Media as a reciprocal loop (audience ⇄ outlet feedback)

**What it is.** Media is currently a **one-way forcing**: exogenous penetration
(cable/broadband/social-media adoption — legitimately fed) scales a pull toward
**fixed, hand-set outlet positions** (`MediaConsumption` → `outlet.position`),
and each agent's `media_diet` is set at birth and never re-selected as the agent
drifts. So both arms of the real media feedback loop are absent:
- **Supply side** — outlets positioning their *slant toward their audience*
  (Gentzkow & Shapiro 2010 "What Drives Media Slant?", *Econometrica* — slant is
  substantially demand-driven; Mullainathan & Shleifer 2005; the "outrage
  industry" escalation, Berry & Sobieraj). Nothing moves `outlet.position`.
- **Demand side** — dynamic selective exposure (choose congenial media →
  reinforce → choose more; Stroud *Niche News*, Prior *Post-Broadcast
  Democracy*). The diet doesn't co-evolve (only a partial static echo via
  `bc_affect_weight`).

This is **structurally the same deficiency as blindspot #7** (positional sorting
input-carried, not emergent) but for the media channel — an *audience-tail →
outlet-slant* feedback would mirror the emergence-recovery *activist-tail → elite*
loop. The project already half-flagged it: the media-outlet-drift workstream's
**Phase A (scheduled drift)** is hand-drawn and on a separate branch, and its
**Phase B (the actual feedback loop) was left pending and never built.**

**Why deferred.** A parallel endogenous loop — would roughly double the
emergence-recovery workstream; and media is the *secondary* channel for positional
sorting (in the honesty budget the media-fed input carried ~0 of the affect rise),
so the elite–mass loop is the priority. Surfaced and deferred 2026-06-14.

**Why worth picking up later.** Once the elite-loop emergence work lands, the same
activist-tail/saturating-cue pattern transfers directly to media; closing it would
make the media channel honestly emergent too and unlock structural media
interventions (deplatforming, algorithm transparency) — pairs with the
"First-class outlets as network nodes" item below.

**Rough effort.** Moderate — a new outlet-responsiveness rule + dynamic
diet-selection, plus calibration + re-bless. Smaller than the elite loop (outlets
are few; penetration stays exogenous).

---

## Engineering / methodology deferred from 8c

### HK phase-diagram test (ε × T sweep)

ABM/math reviewer flagged: the graded logistic filter recovers HK
exactly at `T = 0` but the operational `T = 0.05` may shift the
fragmentation/consolidation phase boundary at tight ε (Lorenz 2007
covers exactly this question for smoothed BC variants). A single
ε × T parameter sweep figure would either validate "HK as T→0"
more strongly or expose a known phenomenon. Methodological
correctness check; quick to run. Not pedagogically urgent.

### Income / inequality channel

McCarty, Poole & Rosenthal 2006 *Polarized America* ties US
polarization tightly to inequality. The current model has no
inequality state and no mechanism by which economic distance
shapes either elite or mass sorting. Adding it would: (a) explain
some long-run trend the current model can't account for, (b) enable
inequality-targeted interventions, (c) ground asymmetric
polarization in something structural rather than positional.

### Formal identifiability decomposition

ABM/math reviewer flagged: Phase 8b's ablation table reports
per-mechanism contributions, but with 5 seeds and overlapping
mechanisms (M1 heterogeneity overlaps with M3 cohort replacement,
both injecting time-varying heterogeneity), per-mechanism Δs below
~0.02 are below the noise floor. A formal Sobol sensitivity
analysis or full 2^5 factorial design would put the attribution
claims on firmer statistical ground. Publication-grade work; not
pedagogically required.

### Strict forward-prediction validation (the original "Phase 8c")

The discipline-strict version of the historical-replication test
that Phase 8b deferred: calibrate 1980-90, then *predict*
1990-2000 without re-tuning, see if it holds. Then calibrate
1990-2000, predict 2000-2010, etc. This is the falsification
version of the test. Phase 8b's "decade-by-decade with bounded
per-decade adjustment" is the consistency-check version. The
forward-prediction version is stronger; it's also harder to pass.
Worth attempting once the Phase 8c mechanism additions stabilize.

### Per-rule isolation test layer (close the drift-guard gap)

A coverage audit (2026-06-02) found that rule drift-guarding is
**phase-organized and integration-style**, not systematic: tests
build a full pillar or arc and assert on the composed result. The
only true *single-rule isolation* test is `compass_basic` +
`test_canonical.py` (the Hegselmann–Krause / bounded-confidence
reduction). There is no per-rule isolation layer, so a few **active**
rules execute inside integration runs but have **no test asserting
their specific behavior** — silent magnitude/trajectory drift would
pass unnoticed:

- **`IdentityAlignment`** — highest priority. It runs in the **shipped
  web build** (`evidence_regrade=True`) and emits the
  `identity_alignment` macro metric (the Step-2 "doubling" fix), yet no
  test references it by class name or metric. A headline series with no
  pin.
- **`IdentityToIdeologyPull`** — historical-arc only, active, unasserted.
- **`ProtectedPartyRealignment`** — historical-arc only, active,
  unasserted.
- **`MediaShock`** — fired via event handlers (not the static pipeline);
  confirm it's wired in the arc schedule, then guard it.
- (`PerceptionBoostExpiry` — minor; companion expiry to the tested
  `PerceptionUpdate`.)
- (`ArgumentExchange` and `X1ExposureExpiry` are *not* gaps: the former
  is in no pipeline; the latter is intervention-triggered and covered
  indirectly via X1's phase10 measurement.)

**The fix is a per-rule isolation suite (the `compass_basic` pattern)
— NOT adding these to the pillar.** The pillar is the *eventless
composition* layer (it tests how rules compound, with no exogenous
events, so an arc regression can be bisected into rule-interaction vs
event-handler); piling single mechanisms into it would break that
control and still wouldn't isolation-test them. Build a minimal
scenario per rule that exercises it alone on a clean substrate and
asserts its effect, starting with `IdentityAlignment`. See the
three-layer model (Isolation / Composition / Empirical) documented in
`CLAUDE.md` → "How rules are drift-guarded."

**Rough effort.** Small-to-moderate and incremental — one isolation
test per rule, ~3–4 to clear the active gaps. No engine change, just
new tests.

---

## Smaller items flagged but not picked up

### Modularity undershoot in the historical scenario

Phase 8b results §3.5: party modularity undershoots empirical
target by ~0.05-0.10 from 2010 onward. Cross-cutting drops are in
band, so it isn't a tie-rewiring rate issue exactly — the trade-off
between cross-cutting and modularity needs its own sweep.

### Alternative initial-condition generator

Phase 8b's 1980 build can't simultaneously hit
variance + constraint + party_separation. Phase 8b results frame
this as a "geometric limitation of the sigmoid-Gaussian generator";
the polarization reviewer reframes it as "the model encodes
party-as-ideological-distance, but 1980 had party-as-coalition
*without* that coupling." Either a two-cluster mixture generator
or a richer party representation (potentially via the
sociodemographic stratification above) would unblock this.

### Asymmetric structural channel beyond drift rate

Phase 8b implements asymmetric polarization as asymmetric
`EliteDrift.rate` and per-party `PARTY_CUE_SIGMA`. The deeper
asymmetry — that the Republican shift is *structural*
(donor-driven, plutocratic, racially-resentment-organized per
Hacker & Pierson 2020) — isn't captured. Possibly subsumes into
the sociodemographic stratification or the income/inequality
channel above.

### Multi-country / electoral-system parameter

The pillar's two-party structure is fixed. Cross-national /
proportional-representation / multi-party institutional dynamics
(Gidron 2020; McCoy & Somer 2019) are out of scope. Would
substantially expand what the demo can compare against, but is its
own project-scale piece of work.

### First-class outlets as network nodes

The current model treats outlets as separate attractor targets
rather than as network nodes. Tightening the partisan-media model
would let interventions like "platform deplatforming" or
"algorithm transparency" become structural rather than parameter
changes.

### Richer generational cohorts (beyond anonymous turnover)

M3 cohort replacement (Phase 8b) does anonymous population
turnover — agents leave, new ones arrive seeded with same-party
mean affect. What's missing is *generational identity*: tagging
each agent with a birth cohort (1940s, 1960s, 1980s, etc.),
seeding cohort-specific ideology / identity-strength
distributions, and surfacing the generational signal in
measurement and visualization so the demo can show "Boomers vs
Millennials vs Gen Z drift differently over time." Would let
historical events (CRA, social media inflection, COVID) hit
specific generations rather than the population uniformly. Useful
pairing with future visualization work — cohort color or marker
could make the generational story visible. Distinct from the
demographic stratification item above (which is about static
race/religion/education attributes); this is about temporal
cohort effects. Mentioned by Vlad as worth doing eventually.

### GPU port + N-scaling investigation

Current engine is numpy-based with N=250 agents per simulation —
small-array regime where GPU launch overhead would dominate per-tick
work, and porting numpy → CuPy/JAX/PyTorch is a substantial
refactor. Not a 8c win. But GPU becomes attractive if scaling to:
N≈10,000+ agents (more realistic population, richer demographic
stratification); very large seed ensembles (100+ seeds for tight
CIs on bucket-boundary effects); batched parameter sweeps (running
many scenarios simultaneously). Pair with the sociodemographic
stratification item above — if both land, the model can represent
real demographic distributions at realistic population scales. CPU
multiprocessing across seeds (added in 8c.1) captures the easy
parallelism wins; GPU is for the next scale tier.

---

## Process notes

- Items move *into* a phase when they get pulled into spec work.
  When that happens, mark them here as "→ Phase 8c.X" rather than
  deleting, so the trail is visible.
- Items get added here whenever a reviewer, calibration result, or
  conversation surfaces a real future-work candidate that isn't in
  current scope.
- This list is *not* a commitment to do all of these. It's a
  parking lot for ideas worth keeping but not now.
