# Phase 8e — Polish Spec

*Compound spec, 8c-style. Five sub-phases (8e.1 → 8e.5),
implemented section-by-section in order. Closes the response cycle
that began with the first external reviews (R1, R2). No third
external review after 8e — see `review2_synthesis.md` for the
ranked action list this spec answers.*

*All ensemble work goes through `abm/calibration_parallel.py`
(Phase 8c §1.5). No serial seed loops permitted in this phase.*

*Discipline (Vlad-set, this conversation): defaults + document for
routine forks; hard-stop only for truly large architectural
changes / unbudgeted resources / overrides of locked-in calls;
pillar invariants forbidden; 73 sacred tests stay green
bit-identically; don't touch UI/website files.*

---

## 0. Whole-phase decisions pinned

| # | Decision | Choice |
|---|----------|--------|
| W1 | **Order: 8e.1 → 8e.2 → 8e.3 → 8e.4 → 8e.5.** Target reassessment must precede 1980 truthfulness (we need to know what we're targeting). 1980 fix must precede trajectory accuracy (downstream calibration depends on a true 1980 IC). Trajectory accuracy must precede decomposition + X7 historical (we want the decomposition to reflect the *polished* engine). Polish items go last. |
| W2 | **Parallel-seed runner everywhere.** Every ensemble (cutoff sweep, X6 magnitude sweep, 4-cell decomposition, historical re-run, X7 historical) uses `run_seeds_parallel`. The serial-vs-parallel determinism diff test in 8e.5 documents bit-identity. |
| W3 | **Pillar invariants still binding.** 73 sacred tests green bit-identically through every section. The party-issue coupling parameter (8e.2) lives in historical_arc with default 1.0 (the existing magnitude); pillar reads with fallback to 1.0 so pillar trajectory unchanged. Same fallback for `media_cue` (8e.3): pillar agents don't carry it; MediaConsumption reads with fallback to no per-agent bias (current behaviour). |
| W4 | **Don't tune forbidden knobs.** TICKS_PER_YEAR, FJ_ALPHA, BC_TEMPERATURE, BC_AFFECT_WEIGHT, TR_AFFECT_WEIGHT_REWIRE, BACKLASH_AFFECT_THRESHOLD, COOPERATIVE_MUTE, PARTY_CUE_SIGMA stay frozen. X1-X7 intervention bucket labels are re-blessable only by §11 measure-then-bless. |
| W5 | **Honest reporting throughout.** Bucket flips under sensitivity sweeps documented as such; if 4-cell decomposition shows affect-in-band is compositional more than mechanism, the headline must be re-stated in methods.md. Per the round-2 synthesis: "the next cycle needs to be smaller and surgical." |
| W6 | **No new spec written between sub-phases.** This compound spec is the contract. Each sub-phase closes via its measure-then-bless gate; the post-8e result post is comprehensive across all five. |

---

## §1 — Target-range reassessment (8e.1)

**Goal.** Walk through the pre-registered Phase 8b targets (§9 of
`phase8b_historical_replication_spec.md`) in light of (a) the
Independents addition breaking some metric semantics, (b) round-2
reviewer input, (c) honest second look at literature anchors.
Decide per-metric: keep / widen / replace. Re-bless tolerance bands
explicitly. Add a partisan-only cross-cutting submetric. Write
`phase8e_targets.md` containing the revised targets — leaves the
original 8b spec intact as historical record.

### §1.1 Per-metric decisions pinned

| Metric | 8b band (2025) | 8e decision | Rationale |
|---|---|---|---|
| Ideological constraint | [0.62, 0.78] | **Keep** | Literature-anchored to ANES partisan-ideology correlation 1980→present. The endpoint band is roughly 1σ around Baldassarri & Gelman 2008's ~0.70 (US 2004-08 figure). Partisan-only filter unaffected by Independents. Honest miss family: cumulative drift undershoots. |
| Party separation | [0.68, 0.82] | **Keep** but expect Independents to widen the gap; document explicitly | Partisan centroid separation. Independents pull partisans inward via BC + Media — a literature-faithful direction (Mason 2018 cross-cutting effect). The band is correct empirically; the 8d run widens the miss but truthfully reports the dynamic. |
| Affective polarization | [-0.85, -0.65] | **Keep** | ANES out-party thermometer band. 8d 2025 endpoint in band (-0.82). Honest miss family: early decades (1990-2010) over-cold by 0.05-0.10. |
| Within-party SD_x | [0.15, 0.22] | **Keep** | DW-NOMINATE / ANES SD anchor. 8b post-2000 collapse persists at 0.10 vs band floor 0.15 — Phase 8e.3 addresses via `media_cue` per-agent. |
| Variance (secondary) | [0.13, 0.20] | **Widen to [0.08, 0.20]** | The 8b empirical anchor for variance was an inference, not a direct literature point. Independents' broader N(0, 0.4) IC + inward pull on partisans compress total variance below 0.13; documented as honest. The widened band accommodates both binary and three-party builds. **Routine fork — document.** |
| Cross-cutting tie fraction | [0.15, 0.25] | **Split into two metrics** | New `partisan_cross_cutting_fraction` (partisan↔partisan ties only) keeps the band [0.15, 0.25] — apples-to-apples with 8b binary measurement. The existing `cross_cutting_tie_fraction` (any ties between different party labels) gets a new band [0.30, 0.45] under three-party population, calibrated to ANES network-survey estimates that Independents form ties broadly across partisan lines. Both reported. |
| Modularity | [0.32, 0.45] | **Widen to [0.20, 0.40]** | Under three-way population, modularity has a third loose Independent community → smaller measured modularity. 8b band was calibrated under two-party; the broader band accommodates either. |

### §1.2 New metric — `partisan_cross_cutting_fraction`

```python
def partisan_cross_cutting_fraction(agents, network) -> float:
    """Fraction of partisan-partisan ties that are cross-cutting (party
    0 vs party 1). Excludes Independent ties entirely. Apples-to-apples
    with the Phase 8b 2-party measurement."""
    partisan_edges = 0
    cross_cutting = 0
    party_by_id = {a.id: a.state.attrs.get("party") for a in agents}
    for i, j in network.edges():
        p_i, p_j = party_by_id.get(i), party_by_id.get(j)
        if p_i not in (0, 1) or p_j not in (0, 1):
            continue
        partisan_edges += 1
        if p_i != p_j:
            cross_cutting += 1
    return cross_cutting / partisan_edges if partisan_edges else 0.0
```

Lives in `abm/metrics/network.py` next to the existing
`cross_cutting_tie_fraction`. At independent_fraction=0.0 the two
metrics give identical numbers (no Independent ties to filter).

### §1.3 Files

```
create  phase8e_targets.md                   # revised targets
modify  abm/metrics/network.py               # partisan_cross_cutting_fraction
modify  scripts/phase8d_historical_replication.py  # use revised bands
modify  scripts/phase8b_calibration.py       # use revised bands (historical record stays)
```

### §1.4 Tests

- New test in `tests/test_phase8d_independents.py`:
  `test_partisan_cross_cutting_fraction_filters_party_2` — verifies
  the submetric excludes Independent ties.
- New regression test: at `independent_fraction=0.0`,
  `partisan_cross_cutting_fraction` equals `cross_cutting_tie_fraction`
  bit-identically.

### §1.5 Measure-then-bless gate

The revised bands are documentation, not code. The §11 consolidated
bucket test is unaffected. The 73-pillar suite is unaffected.
Independent reviewer subagent verifies bands are honestly justified.

---

## §2 — 1980 truthfulness (8e.2)

**Goal.** Per round-1 R1 polarization expert: 1980 isn't a
sigmoid-Gaussian generator limit — it's that the model structurally
encodes party-as-ideological-distance, while empirical 1980 was
party-as-coalition *without* that coupling. Implement a
party-issue coupling parameter that scales the strength of
party-distance contributions in the dynamics, low in 1980 and rising
across decades.

### §2.1 Decision: coupling lives in dynamics, not build

**Fork chosen (default per Vlad's brief; document):** coupling
lives in the dynamics as a per-decade env-attr scaling parameter,
not in the build. Rationale:

- **Dynamics version** scales how strongly party position affects
  per-tick updates throughout the decade. Implements Mason 2018's
  "mega-identity" arrival as a *gradual coupling tightening*, not
  a discrete 1980 seeding change.
- **Build version** would couple party↔ideology more weakly at
  1980 via initial-condition randomness, then leave the dynamics
  alone. This conflates two things — the initial state and the
  dynamics-driven coupling — and makes it harder to attribute
  later decade outcomes.

The dynamics version composes cleanly with existing 8b/8c
mechanisms (EliteDrift→cue, IdentitySorting, MediaConsumption) and
runs *exactly* the same code path as today with a per-decade
multiplier. Pillar-fallback: coupling defaults to 1.0 (the existing
behaviour); pillar bit-identity preserved.

### §2.2 Mechanism: `party_issue_coupling` schedule

New env attribute `party_issue_coupling: float` (default 1.0 in
pillar; per-decade schedule in historical_arc). Read by:

- `PartyPull.apply` — scales the (party_cue − ideology) pull
  magnitude. Higher coupling → stronger pull → bigger party-driven
  ideological shift.
- `AffectiveUpdate.apply` — scales the `issue_term` weight in the
  disagreement formula (i.e., `(1 - identity_weight) * issue_term`
  becomes `(1 - identity_weight) * issue_term * party_issue_coupling`).

Both reads are with fallback to 1.0 so pillar agents (and any
scenario without the env attr) behave bit-identical to Phase 8d.

### §2.3 Historical schedule

```python
# Phase 8e §2: party-issue coupling rises across decades. 1980 had
# party-as-coalition with weak party-issue coupling (R1 R1 review).
PARTY_ISSUE_COUPLING_SCHEDULE = {
    "1980-90": 0.40,   # 1980 party-as-coalition (weak coupling)
    "1990-00": 0.60,   # post-Reagan realignment underway
    "2000-10": 0.80,   # consolidation
    "2010-20": 1.00,   # full coupling (matches Phase 8d default)
    "2020-25": 1.10,   # post-Trump amplification (mild overshoot)
}
```

The schedule is updated at each decade boundary via the existing
`_decade_boundary_*` event functions in `historical_arc.py`. The 1.0
midpoint at 2010-20 matches Phase 8d's behaviour exactly; lower
values for earlier decades represent the empirical un-coupling.

### §2.4 1980 IC re-calibration

With coupling = 0.40 in 1980, partisan agents pull less strongly
toward their party_cue → smaller party_sep, lower party-issue
correlation (constraint), more party-as-coalition shape. The
sigmoid-k = 8 IC generator stays as-is; the coupling is what
delivers the 1980 truthfulness, not the IC distribution.

### §2.5 Files

```
modify  abm/rules/party_pull.py              # read party_issue_coupling
modify  abm/rules/affective_update.py        # scale issue_term by coupling
modify  abm/pillars/historical_arc.py        # PARTY_ISSUE_COUPLING_SCHEDULE + decade-boundary updates
create  tests/test_phase8e_coupling.py       # coupling read + fallback + decade schedule
```

### §2.6 Tests

1. Pillar at `party_issue_coupling` absent: PartyPull / AffectiveUpdate
   bit-identical to Phase 8d.
2. With `party_issue_coupling = 0.5`, PartyPull's d_ideology magnitude
   is half the magnitude at coupling = 1.0.
3. AffectiveUpdate's `issue_term` contribution scales with coupling.
4. Historical_arc env carries the schedule; decade-boundary events
   update env.attrs["party_issue_coupling"] to the schedule's value.
5. Historical 1980 IC: with coupling = 0.40 at start, constraint
   drops into band [0.25, 0.40] AND party_sep drops into band
   [0.45, 0.60].

### §2.7 Measure-then-bless gate

- Pillar 73-test suite + 8c/8d tests stay green (159 → 161 with the
  two new coupling tests).
- Historical re-run shows 1980 ICs more in band: target constraint
  ∈ [0.25, 0.40] and party_sep ∈ [0.45, 0.60] both achieved (band
  hit re-blessed by measurement).
- Honest report: the 1980 geometric-tension family of misses
  diagnosed in Phase 8b moves into band.

---

## §3 — Trajectory accuracy (8e.3)

**Goal.** Re-run historical with the 1980 fix from §2; then
implement per-agent `media_cue` analog to address the within-party
SD post-2000 structural collapse.

### §3.1 `media_cue` per-agent

Mirrors Phase 8a's `party_cue` exactly. Each agent draws a personal
`media_cue ∈ [-1, 1]²` at build time. `MediaConsumption.apply` reads
this and *biases the diet target* per-agent:

```python
# Phase 8e §3 — agent-level media diet bias. Each agent's effective
# diet target is the population diet target (weighted-mean of
# media_diet × outlets) plus a small personal bias.
#
# Pillar-fallback: agents without `media_cue` use the bias = 0
# (current behaviour). Bit-identical to Phase 8d.

personal_bias = float(agent.state.attrs.get("media_cue", 0.0))  # broadcast scalar; vectorize as needed
target_with_bias = unbiased_target + personal_bias * MEDIA_CUE_STRENGTH
```

Or, simpler and more accurate to the `party_cue` analog:

```python
# `media_cue` is an additive bias to each outlet's position before
# the per-agent pull is computed. So an agent who is biased toward
# +x media perceives all outlets as slightly shifted +x. The pull
# magnitude stays constant; the direction shifts per-agent.
```

**Routine fork (document):** which formulation. Default — the
simpler additive-bias version. The personal bias is `N(0, σ)` with
σ = 0.15 (calibrated to give within-party SD ~0.18 at 2025).
**Alternative**: per-agent perceived diet-target shift. Both
formulations are equivalent in steady state but differ in transient
dynamics; the simpler version preserves bit-identity at `media_cue`
absent or = 0.

### §3.2 Build seeding

`calm_to_camps.build_engine` does NOT seed `media_cue` (pillar
bit-identical). `historical_arc.build_engine` seeds
`media_cue = rng.normal(0, MEDIA_CUE_SIGMA, size=2)` per partisan
agent (Independents skip — they have no partisan media bias by
construction; their `media_diet` is already centrist).

### §3.3 Re-run + measure

After §2 + §3.1 + §3.2 land, run the historical re-run at 15 seeds
and report per-decade trajectories. Compare to Phase 8d.

### §3.4 Files

```
modify  abm/rules/media_consumption.py       # read media_cue with fallback
modify  abm/pillars/historical_arc.py        # seed media_cue per partisan
create  tests/test_phase8e_media_cue.py       # build + pillar-fallback + within-party SD direction
```

### §3.5 Measure-then-bless gate

- Pillar 73-test suite + 8c/8d tests + §2 + §3 tests stay green.
- Historical 2025 within-party SD: target band [0.15, 0.22].
  Phase 8d was at 0.10; expected to move to 0.18 with the per-agent
  bias active. If still below band, document; the structural
  improvement direction is what matters.
- Constraint endpoint and party_sep endpoint: report; the 8b
  near-miss family may shift.

---

## §4 — 4-cell decomposition + X7 historical (8e.4)

**Goal.** Two distinct items, both honesty-required per round-2 R2 and R1 respectively.

### §4.1 4-cell decomposition (R2 #1 in round-2 synthesis)

Run the historical arc at 15 seeds × 4 cells:

| Cell | Engine | Independents | Expected |
|---|---|---|---|
| A | 8b baseline | 0.0 | -0.90 (Phase 8b measurement) |
| B | 8b baseline | 0.12 | ? (Independents only effect) |
| C | augmented (8c+8d+8e.1-3) | 0.0 | ? (mechanism only effect) |
| D | augmented | 0.12 | -0.82 (full Phase 8d measurement) |

The decomposition disambiguates: if (D - A) ≈ (B - A) + (C - A),
the effects are additive. If (D - A) ≈ (B - A) and (C - A) ≈ 0,
the entire improvement is compositional. If (D - A) ≈ (C - A) and
(B - A) ≈ 0, the entire improvement is mechanism. The honest answer
goes into methods.md §4.6.

**Implementation.** Cell A is `historical_arc.py` at the **pre-§8e
state** (git tag the 8d closing commit). Cell B same engine with
`independent_fraction = 0.12`. Cell C the §8e-current engine at
`independent_fraction = 0.0`. Cell D the §8e-current engine at
`independent_fraction = 0.12`.

To run Cell A and B without reverting code: introduce a `phase8e_disable_8c_mechanisms` env attr or build kwarg that turns off the 8c §2-§6 mechanisms (positive-going channel, agent-level mute, perception-gap, identity-threat, asymmetric backlash). Actually — simpler: parameterise the rule settings at build time and pass disabling values for the baseline cells. The cell-A/B builds use `coop_positive_magnitude = 0`, no `perceived_other_party` seeded, `THREAT_DECAY_RATE = 0` (and skip the 2016 event), `BacklashRepulsion.asymmetric = None`, AffectiveUpdate `cooperative_mute` not on cooperative edges (no X6 in baseline so already inert). The most cleanly-toggle-able mechanism is `perceived_other_party` (skip seeding for baseline cells).

**Routine fork — pick implementation default and document:** simpler parameterisation rather than git-checkout. Add a `phase8e_baseline: bool = False` kwarg to `historical_arc.build_engine` that suppresses 8c §4-§5 seeding (perceived_other_party, perceived_threat) AND suppresses the 2016 threat event firing AND the Obama 2008 warmth event firing. (8c §2 positive-going + agent-level mute are already inert in historical baseline because no X6 fires.)

### §4.2 X7 historical measurement (R1 #2 in round-2)

Fire X7 in the historical scenario at tick 90 (=2010) and tick 105
(=2015). Measure trajectory delta vs the un-fired baseline. Two
measurements, both with 15-seed ensembles.

X7 in the historical context resets `perceived_other_party` to the
actual party centroid for all agents that carry the attr (12% of
the population is Independents who don't, the 88% partisans do).
The trajectory delta is measured at 2025 endpoint vs 8d baseline:
Δaffect, Δconstraint, Δparty_sep, Δwithin_party_sd.

### §4.3 Files

```
modify  abm/pillars/historical_arc.py        # phase8e_baseline kwarg
create  scripts/phase8e_decomposition.py     # 4-cell A/B/C/D measurement
create  scripts/phase8e_x7_historical.py     # X7 fired at 2010 + 2015
```

### §4.4 Measure-then-bless gate

- Decomposition reported with point ± SE per cell. The "compositional
  vs mechanism" attribution is the honest output — documented in
  methods.md §4.6.
- X7 historical: report two trajectory deltas (X7 at 2010, X7 at
  2015). The numbers feed into methods.md §4.5 sensitivity table
  (X7 row gets a new "historical context" entry).

---

## §5 — Academic polish (8e.5)

Five items from the round-2 synthesis ranked-action list. All small.

### §5.1 X6 `coop_positive_magnitude` sensitivity sweep

`scripts/phase8e_coop_positive_sweep.py` — runs X6's §11
release-phase measurement at `coop_positive_magnitude ∈ {0.02, 0.05,
0.08, 0.10}`. Reports the per-axis bucket under each value. If X6's
"real on affect" bucket holds across the sweep, the headline is
robust; if it flips at lower magnitudes, methods.md §5.3 documents
the dependence honestly.

### §5.2 2016 identity-threat amplitude disambiguation

Two options per round-2 R2:

- **Option A: tune `THREAT_2016_MAGNITUDE` to a pre-2016 ANES point**
  (e.g., 2008 thermometer dip) AND treat the 2016 spike as a
  forward prediction. Cleaner but requires re-calibration.
- **Option B: explicitly state the 0.5 magnitude is post-hoc fit**
  to the 2016 spike, with citation Mutz 2018 as the *direction*
  anchor but not magnitude.

**Default: Option B.** Post-hoc fit is honest and matches the
spec's L/E provenance discipline (the *direction* is L, the
*magnitude* is E). Methods.md §3.5 gets an explicit "Provenance:
**direction L (Mutz 2018), magnitude E (post-hoc to fit the 2016
ANES spike)**" note.

### §5.3 Affect-gate firing-rate diagnostic actually in §11

The D6 diagnostic (8c §1) added it to `scripts/phase6_calibration.py`
and `scripts/phase8c_diagnostics.py` but **not to the canonical §11
measurement reporting**. The round-2 R1 catch.

Fix: extend `tests/test_phase6.py::test_intervention_library_directions_hold`
(or a sibling test) to report the affect-gate firing rate alongside
the bucket measurements. Alternatively (cleaner): when
`scripts/phase6_calibration.py` re-runs §11, the firing-rate
diagnostic is now included in its standard output. The §11
measurement's `intervention_buckets` fixture in conftest gets a
parallel `affect_gate_firing_rate` fixture that reports the rate at
S4-end and per-X-intervention release-end. Numbers go into
methods.md §5.4 alongside other diagnostics.

### §5.4 95% CI bands

Existing methods.md §4.3 reports `point ± SE` for every measurement.
8e.5 tightens this: every reported number gets a 95% CI band derived
from the t-distribution at n_seeds = 20 (pillar) or n_seeds = 15
(historical). The format becomes:

```
Δsep = +0.490 ± 0.006 [95% CI: +0.478, +0.502]
```

Implementation: a helper in `abm/calibration_parallel.py` —
`ci_95(values, n_seeds)` returning `(lo, hi)` — and methods.md
tables updated.

### §5.5 Serial-vs-parallel determinism diff test

New test `tests/test_parallel_determinism.py` runs a small
intervention buckets measurement at 6 seeds (a) serially and (b)
parallel, asserts the per-seed values are bit-identical (atol 0,
not 1e-12).

### §5.6 Files

```
create  scripts/phase8e_coop_positive_sweep.py
create  scripts/phase8e_4cell_decomposition.py   (renamed from §4)
create  scripts/phase8e_x7_historical.py
modify  scripts/phase6_calibration.py            # firing-rate in §11 output
modify  tests/conftest.py                         # affect_gate_firing_rate fixture
create  tests/test_parallel_determinism.py
modify  abm/calibration_parallel.py              # ci_95 helper
modify  methods.md                                # §3.5 disambiguation; §4.3 CI bands; §4.6 decomposition result; §5 X6 sensitivity
modify  phase8e_targets.md                       # closing summary
```

### §5.7 Measure-then-bless gate

- All sweeps + tests pass.
- methods.md updates land.
- Phase 8c §6 §11 buckets remain blessed under the canonical 0.05
  X6 magnitude. If the sweep shows the bucket is robust at {0.02,
  0.05, 0.08, 0.10}, the "real on affect" claim strengthens; if it
  flips, the claim is qualified.

---

## §6 — Whole-phase close

After 8e.5 closes:

1. Run the full pytest suite at 20 pillar seeds + 15 historical
   seeds. Target: ~165-170 tests green.
2. Independent reviewer subagent on the whole §8e diff.
3. Run the 4-cell decomposition + X7 historical + X6 sensitivity
   sweep, capture results.
4. Update methods.md with all changes: §3.5 provenance, §4.3 CI
   bands, §4.5 X7 historical, §4.6 4-cell decomposition, §5.3
   X6 sensitivity, §5.4 firing-rate diagnostic.
5. Write a comprehensive 8e result post covering all sub-phases.

**No further confirm needed.** Per Vlad's brief, 8e closes the
response cycle.
