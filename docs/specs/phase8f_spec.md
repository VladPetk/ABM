# Phase 8f — Spec

*Compound spec, 8c-style. Three sub-phases (8f.1 → 8f.2 → 8f.3).
Ships the `combo_JJ` augmentation surfaced by the iterative deep
investigation (see `phase8f_investigation_report.md`), adds the
companion 1980-fix that the investigation flagged as carry-over,
and runs a systematic blind-spot audit on aggregate metrics so the
next y-axis-style structural miss surfaces in audit rather than in
a six-month review cycle.*

*All ensemble work goes through `abm/calibration_parallel.py`.
Pillar invariants forbidden. 73 sacred tests stay green
bit-identically.*

---

## 0. Whole-phase decisions pinned

| # | Decision | Choice |
|---|----------|--------|
| W1 | **Order: 8f.1 → 8f.2 → 8f.3.** Ship combo_JJ first (the headline architectural fix + four parameter shifts the investigation validated). Then add the 1980-soft-sigmoid pair fix (the one carry-over miss the investigation flagged). Then run the audit on the final integrated build. |
| W2 | **Confined to historical_arc.** The pillar is untouched: `calm_to_camps.py` not modified; pillar's `AffectiveUpdate`/`PartyPull`/`MediaConsumption` constructed at their existing defaults; pillar agents don't seed `media_cue` or the new sigmoid-k schedule. All 8f changes live in `historical_arc.py` (constants + builder + Schedule events). The keystone bit-identity test (Phase 8e's `test_pillar_S4_bit_identical_at_zero_fraction`) carries through unchanged. |
| W3 | **No forbidden knob tuned.** TICKS_PER_YEAR, FJ_ALPHA, BC_TEMPERATURE, BC_AFFECT_WEIGHT, TR_AFFECT_WEIGHT_REWIRE, BACKLASH_AFFECT_THRESHOLD, COOPERATIVE_MUTE, PARTY_CUE_SIGMA all stay frozen at their pillar values. The historical-arc parameter shifts (`MEDIA_CUE_SIGMA` 0.15→0.40, `PARTY_CENTERS_1980` y-component 0→±0.08, `ELITE_DRIFT_SCHEDULE` reshape) are historical-scenario-local — they live in `historical_arc.py`. The two historical-local rule-strength overrides (`AffectiveUpdate.baseline = 0.0`, `PartyPull.strength = 0.07`) are passed at construction in `historical_arc.build_engine` — the rule classes' constructor defaults stay at pillar values (0.10 and 0.05 respectively). |
| W4 | **Honest narrative on curve-fitting vs structural.** Per the investigation report: ~1 structural fix (y-axis party centers — unblocks the constraint plateau) + 2 literature-defensible shifts (PartyPull 0.07 within Hetherington range; MEDIA_CUE_SIGMA 0.40 within ANES dispersion) + 2 honest curve-fits (`baseline = 0.0` was a Phase 5 modeling choice; ELITE_DRIFT reshape is post-hoc to mid-decade sep). Methods.md §8f documents this split. |
| W5 | **Parallel-seed runner everywhere.** Combo_JJ measured at 20 seeds (investigation already at 5 seeds; verify at 20). 1980-fix verified at 20 seeds. Audit's verification scripts use `run_seeds_parallel`. |
| W6 | **Audit is documentation + small fixes, not new mechanism.** §8f.3 walks each aggregate metric, decomposes into components, verifies achievable ranges. Anything small enough to fix (a metric semantics clarification, an obvious component-split that should land in the existing codebase) gets fixed in 8f.3. Anything structural (a new mechanism, a deeper architectural change) gets logged as Phase 8g candidate. |

---

## §1 — Ship combo_JJ (8f.1)

**Goal.** Land the five coordinated changes from the investigation's
combo_JJ variant. Confined to `historical_arc.py`.

### §1.1 The five changes pinned

1. **Y-axis party-center bias.** `PARTY_CENTERS_1980` gains
   y-component ±0.08:
   - Party 0: `(-0.30, -0.08)` (was `(-0.30, 0.0)`)
   - Party 1: `(+0.30, +0.08)` (was `(+0.30, 0.0)`)

   This is the **architectural fix** that unblocks the constraint
   plateau diagnosed by the investigation. The Phase 8b/8e pillar
   had party centers only on the x-axis, so the y-component of
   `ideological_constraint` (`(cx + cy) / 2`) was inert at noise
   level ~0.20 and `(0.92 + 0.20) / 2 = 0.56` was a structural
   ceiling. With y-component ±0.08, both axes can sort and the
   constraint endpoint can reach the empirical 0.62-0.78 band.

   Magnitude calibration (Fork 1A, document): 0.08 is the smallest
   y-bias that unblocks the plateau within the empirical band. The
   investigation tested 0.08, 0.10, 0.15, 0.25 — 0.08 produces
   constraint endpoint 0.75 (in band); larger values overshoot.

2. **`MEDIA_CUE_SIGMA` 0.15 → 0.40.** Lifts within-party SD. The
   Phase 8e 0.15 value was calibrated against legislator-band
   dispersion (DW-NOMINATE ~0.15-0.20); the ANES voter band is
   ~0.33-0.47, requiring broader per-agent media diet dispersion.
   Defensible within the ANES self-placement range (Fork 1B
   default: 0.40 — investigation-confirmed).

3. **`AffectiveUpdate.baseline` 0.10 → 0.0 (historical-only).** Fixes
   1990-2010 affect over-cooling. The Phase 5 `baseline = 0.10`
   represents a per-encounter coolness floor: every out-party
   encounter contributes at least 0.10 worth of coolness regardless
   of ideological distance. The investigation found this floor
   drives 1990-2010 over-cool: ideological-proximity-proportional
   cooling alone (baseline=0.0) tracks ANES band more accurately.
   Pillar keeps `baseline = 0.10` (Phase 5 default unchanged); the
   historical scenario overrides at construction time.

4. **`PartyPull.strength` 0.04 → 0.07 (historical-only).** Fixes
   party_sep U-shape. Stronger party-side anchoring than the pillar
   default. Defensible against Hetherington 2001 elite-cue
   magnitude range. Historical-only override (constructor kwarg).

5. **`ELITE_DRIFT_SCHEDULE` reshape, front-loaded.** Peak in
   1990-2010 (the empirical "great sort" decades per Mason 2018),
   tapering after. New schedule:
   - 1980-90: 0.005 (was 0.0025)
   - 1990-00: 0.008 (was 0.0035)
   - 2000-10: 0.008 (was 0.0045)
   - 2010-20: 0.007 (was 0.0060 — Citizens United still elevated)
   - 2020-25: 0.006 (was 0.0060)

### §1.2 Files

```
modify  abm/pillars/historical_arc.py
    PARTY_CENTERS_1980 (add y bias)
    MEDIA_CUE_SIGMA → 0.40
    ELITE_DRIFT_SCHEDULE → new values
    build_engine: construct AffectiveUpdate with baseline=0.0
                  construct PartyPull with strength=0.07
                  pass y-axis bias to per-agent party_cue at build
```

### §1.3 Pillar bit-identity preserved

- `calm_to_camps.py` not modified.
- Pillar's `PARTY_CENTERS` (no y bias) unchanged.
- Pillar's `MEDIA_CUE_SIGMA` doesn't exist (pillar doesn't seed
  `media_cue`).
- Pillar's `AffectiveUpdate.baseline` = 0.10 (Phase 5 default,
  unchanged at the class level).
- Pillar's `PartyPull.strength` per stage bundle unchanged.
- Pillar's `ELITE_DRIFT.rate` = 0 in S0-S4 (no change).

### §1.4 Tests

- Existing 8e+8d historical tests still pass (they don't pin
  specific decade values; they pin party=2 attrs, fraction counts,
  bit-identity at `independent_fraction=0.0`).
- 73-test pillar invariant — green.
- New: smoke-test that `build_engine` constructs `AffectiveUpdate`
  at `baseline=0.0` and `PartyPull` at `strength=0.07` in the
  historical scenario.

### §1.5 Measure-then-bless gate

20-seed run of the historical scenario reproduces the
investigation's 19/24 in-band primary cells. The two persistent
misses (1980 party_sep overshoot, 2000 within-party SD just below
band-floor) carry forward into §8f.2.

---

## §2 — 1980 soft-sigmoid party-assignment schedule (8f.2)

**Goal.** Fix the 1980 party_sep overshoot (0.66 vs band [0.45,
0.60]) that combo_JJ leaves behind. Per the polarization reviewer's
round-1 diagnosis: 1980 had party-as-coalition *without* tight
ideological coupling, so sigmoid party assignment in 1980 should be
*fuzzy* (many cross-pressured partisans whose ideology doesn't
sharply predict party).

### §2.1 Mechanism — per-decade `PARTY_ASSIGNMENT_K`

The current build assigns party probabilistically:
`P(party=1 | x) = sigmoid(K * x)` with `K = 8.0` (gives ~95%
sign-aligned at |x|=0.3 — sharp partisan-vs-ideology coupling).

8f.2 adds a per-decade schedule. The build-time K is read for the
1980 cohort; cohort replacement (M3) uses the cohort's K:

```python
PARTY_ASSIGNMENT_K = {
    "1980-90": 2.5,    # very fuzzy — party-as-coalition era
    "1990-00": 4.0,    # post-Reagan realignment underway
    "2000-10": 6.0,    # consolidation
    "2010-20": 8.0,    # full coupling (matches Phase 8e default)
    "2020-25": 8.0,    # Trump-era continues at peak
}
```

At 1980 with K=2.5: at |x|=0.3 (typical position), the sigmoid
gives P(party=1) ≈ `1 / (1 + exp(-0.75)) ≈ 0.68` — only 68% sign-
aligned vs ~95% under K=8. So ~32% of 1980 partisans are
"cross-pressured" (party doesn't match the sign of their position),
which reduces the 1980 partisan-centroid separation.

### §2.2 Pair with 8e party-issue coupling

The Phase 8e `PARTY_ISSUE_COUPLING_SCHEDULE` is the **dynamics**
analog of the same idea: how strongly party-distance drives per-tick
updates. `PARTY_ASSIGNMENT_K` is the **build-time** analog: how
sharply party assignment depends on ideology at draw. Both rise
together across decades — initial 1980 has fuzzy assignment AND
weak coupling; modern era has sharp assignment AND tight coupling.

### §2.3 Files

```
modify  abm/pillars/historical_arc.py
    PARTY_ASSIGNMENT_K schedule
    build_engine: read 1980-90 K for build
    CohortReplacement integration: cohort_for_tick → cohort-aware K
modify  abm/rules/cohort_replacement.py
    _replace_agent_inplace: use cohort-aware K from env
```

### §2.4 Tests

- New `tests/test_phase8f_assignment_k.py`:
  - 1980 build at K=2.5 produces ~32% cross-pressured partisans.
  - 2010+ build at K=8.0 reproduces the Phase 8e/8d behaviour
    (~95% sign-aligned).
  - Cohort replacement uses the cohort's K for new agents.
- Pillar invariant: pillar doesn't seed `PARTY_ASSIGNMENT_K` (uses
  the existing fixed K=8 in `calm_to_camps.py`). Bit-identical.

### §2.5 Measure-then-bless gate

20-seed run: 1980 party_sep target [0.45, 0.60]. If lands in band,
20/24 primary cells covered. If still high (e.g. 0.61), document
honestly and either tighten K (e.g. K=2.0) or accept as honest
near-miss.

---

## §3 — Blind-spot metrics audit (8f.3)

**Goal.** Catch the next y-axis-style structural blindspot before
it costs another six-month miss. Walk each aggregate metric,
decompose into components, verify achievable ranges, document
hidden ceilings.

### §3.1 Metrics in scope

For each:
- **variance** (positional spread)
- **ideological_constraint** (party-issue correlation, |Pearson r|)
- **party_sep** (centroid distance)
- **affective_polarization** (mean out-party warmth)
- **within_party_sd** (per-party position dispersion)
- **cross_cutting_tie_fraction** (any-pair ties across parties)
- **partisan_cross_cutting_fraction** (8e §1 — partisan-only)
- **party_modularity** (Newman Q under party partition)
- **sorting_index** (Mason 2018 — mean party-identity correlation)

For each, audit:
1. **Decomposition** — what components is it averaging?
2. **Achievable range** under current mechanism inventory — can
   each component span its target range, or is one structurally
   pinned?
3. **Behaviour under three-party population** (Independents)
4. **Mechanism-firing visibility** — for metrics that depend on
   conditional firing (affect-gate, e.g.), is the firing rate
   actually reported?
5. **Verdict**: stable / minor fix here / Phase 8g+ structural

### §3.2 Output

`phase8f_metrics_audit.md` — one entry per metric, ~50-100 lines.
Each entry:

```
### <metric>
Definition: ...
Decomposition: ... components ...
Achievable range under current mechanisms: ...
Hidden ceilings flagged: ...
Three-party behaviour: ...
Verdict: stable | small-fix-here | 8g+ structural
```

### §3.3 Small fixes implementable here

- If a metric has an obvious component-split that should land in
  the codebase (e.g. `ideological_constraint_per_axis` returning
  the x/y components separately), add it.
- If a metric's three-party behaviour needs a documentation note in
  methods.md, add it.

### §3.4 Defer to Phase 8g+

- Anything requiring a new mechanism / rule.
- Anything requiring a deeper architectural change (like the y-axis
  fix in 8f.1).

---

## §4 — Whole-phase close

After §3 closes:

1. Full pytest suite at 20 pillar seeds + 15 historical seeds.
   Target: ~180 tests green.
2. Independent reviewer subagent on the whole §8f diff.
3. Comprehensive 8f result post:
   - 8f.1 in-band cell count after combo_JJ at 20 seeds.
   - 8f.2 1980 party_sep landing.
   - 8f.3 audit findings, fixes applied, items deferred to 8g.

**No further confirm needed.** 8f closes the response cycle to the
8e investigation report's findings.
