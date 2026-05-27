# Phase 8b — Historical Replication Implementation Spec

*Companion to `phase8b_historical_replication_design.md` (v2,
confirmed). All 14 design forks at defaults. This spec pins the
implementation details — exact tick numbers, heterogeneity
magnitudes, event activation parameters, per-decade pre-registered
targets with citations, the calibration harness API, file layouts.*

*One new judgment fork emerged from pinning — see §3.3.
Implementer's call: flagged-and-defaulted per the
"calibration-within-confirmed-form" pattern (Phase 8a's
PARTY_CUE_SIGMA was the same shape — design confirmed the form,
spec pinned the value).*

---

## 1. Scope and decisions pinned

| # | Decision | Choice |
|---|----------|--------|
| H1 | The historical scenario is a **standalone module** `abm/pillars/historical_arc.py`. Pillar untouched; pillar's 73-test suite must stay green. |
| H2 | Time mapping: `TICKS_PER_YEAR = 3.0` (Phase 7 constant, unchanged). 1980 → 2025 = **135 ticks**. Decade boundaries: tick 30 (1990), tick 60 (2000), tick 90 (2010), tick 120 (2020), tick 135 (2025). |
| H3 | Seed count: **5 historical seeds**, range(5). Pillar tests keep range(12). |
| H4 | Five mechanisms (§3-§7), all implementing the **Phase 8a fallback pattern**: rules read agent/env attrs first, fall back to rule-level constants. Non-pillar scenarios see no behaviour change. |
| H5 | Six events, scheduled at fixed ticks. Mix of step/ramp per event (§8). |
| H6 | Per-decade calibration loop (§10): literature-anchored starts → measure → bounded adjust within per-decade scope → accept-miss-and-document if still out of band → never touch forbidden knobs. |
| H7 | Targets pre-registered in §9 below before any calibration; do not slide post-hoc. |
| H8 | Honesty discipline: §11 lists the 73 tests that must stay green; §12 documents the per-decade results. |

---

## 2. Files

```
modify  abm/rules/influence.py            # BC reads agent.attrs["epsilon"] with fallback
modify  abm/rules/noise.py                # GaussianNoise reads agent.attrs["fj_alpha"] with fallback
modify  abm/rules/affective_update.py     # AffectiveUpdate reads agent.attrs["affect_lr"] with fallback
create  abm/rules/residential_migration.py  # M2: Big Sort
create  abm/rules/cohort_replacement.py     # M3: cohort replacement EnvRule
create  abm/pillars/historical_arc.py     # the standalone scenario
create  abm/pillars/schedule.py           # the Schedule type
create  scripts/phase8b_calibration.py    # decade-by-decade calibration harness
create  scripts/phase8b_run.py            # one-shot end-to-end historical run for the public-facing demo
create  tests/test_phase8b_mechanisms.py  # unit tests for the 5 mechanisms (pillar-fallback discipline)
create  tests/test_phase8b_historical.py  # the decade-by-decade calibration assertions
```

**Pillar files do not change.** `calm_to_camps.py`, the
intervention library, the Phase 4-8a tests, the canonical /
machinery / network tests: untouched.

---

## 3. M1 — Per-agent heterogeneity on `epsilon`, `α`, `affect_lr`

### 3.1 The pattern

Each parameter follows the Phase 8a `party_cue` pattern: per-agent
attr seeded at build (only in the historical scenario); rule reads
the attr first; falls back to its rule-level constant when the
attr is absent (every existing scenario, including the pillar).

| Parameter | Pillar default (rule-level) | Per-agent attr key |
|---|---|---|
| `BoundedConfidenceInfluence.epsilon` | `0.30` | `agent.state.attrs["epsilon"]` |
| `GaussianNoise` anchor rate (from `env.attrs["fj_alpha"]`) | `0.05` | `agent.state.attrs["fj_alpha"]` |
| `AffectiveUpdate.lr` | `0.01` (set by bundle) | `agent.state.attrs["affect_lr"]` |

### 3.2 The heterogeneity model

Each per-agent value is computed at build as a deterministic
function of `identity_strength` plus a Beta-distributed jitter:

```python
# Per-agent epsilon:
hetero_term = 2 * (identity_strength - 0.5)  # range [-1, +1]
jitter = 2 * (rng.beta(2, 5) - 0.286)  # mean ~0, Beta-shaped
agent_epsilon = 0.30 * (1.0 - EPSILON_HETERO_FACTOR * hetero_term
                        + EPSILON_JITTER * jitter)

# Per-agent FJ anchor rate:
agent_fj_alpha = 0.05 * (1.0 + FJ_HETERO_FACTOR * hetero_term
                          + FJ_JITTER * jitter)

# Per-agent affect_lr:
agent_affect_lr = 0.01 * (1.0 + LR_HETERO_FACTOR * hetero_term
                            + LR_JITTER * jitter)
```

The **signs** follow the literature:
- `epsilon`: negative correlation with engagement (engaged
  partisans are more close-minded; Taber & Lodge 2006 "motivated
  skepticism"; Zaller 1992 "reception axiom").
- `α` (anchor): positive correlation (engaged partisans more
  anchored; Achen & Bartels 2016 "team-identified voters").
- `affect_lr`: positive correlation (engaged partisans process
  affect more strongly; Mason 2018 mega-identity).

### 3.3 Heterogeneity magnitudes — NEW JUDGMENT FORK FLAGGED

The design fork B-Heterogeneity-Shapes confirmed "Beta distributions
correlated with identity_strength." Spec-pinning needs concrete
magnitudes. **This is a new fork** the design didn't anticipate;
flagging per Vlad's instruction and proceeding with defaults.

**B-Heterogeneity-Magnitude (NEW, defaulted):**

| Parameter | Hetero factor | Jitter factor | Effective per-agent range |
|---|---|---|---|
| `epsilon` | 0.40 | 0.10 | ~[0.16, 0.45] (high-id agents at 0.20; low-id at 0.40) |
| `fj_alpha` | 0.60 | 0.10 | ~[0.020, 0.090] (high-id at 0.080; low-id at 0.020) |
| `affect_lr` | 0.80 | 0.10 | ~[0.002, 0.020] (high-id at 0.018; low-id at 0.003) |

**Rationale for the magnitudes:**
- `epsilon` 40%: Taber & Lodge 2006 effect sizes on motivated
  skepticism are substantial but not extreme. 40% range gives
  engaged-partisan agents ~30% lower epsilon than disengaged.
- `α` 60%: Achen & Bartels' "team-identified voters" are
  strongly anchored. 60% range gives the engaged tail anchor
  rates ~2× the disengaged median.
- `affect_lr` 80%: Mason 2018 + Iyengar et al. 2019 — engaged
  partisans process out-party affect with much higher
  amplification. 80% gives ~6× ratio between engaged and
  disengaged tails.
- Jitter 10% on each: small Beta(2, 5)-shaped noise; fat tail.

**Alternatives if Vlad wants to override the defaults:**
- All three at uniform 50% — symmetric defaults, less faithful to
  the heterogeneity-of-engagement literature.
- All three at 100% — maximal heterogeneity; risks producing
  agents with parameters near 0 or impossibly high.
- Hand-tuned per-parameter to hit a specific 1990 target — would
  break the "calibrate per-decade, not by hand" discipline.

**This is the one new fork that surfaces during spec-pinning.**
Vlad instructed: "If the spec-pinning surfaces a new judgment fork
the design didn't anticipate, stop and flag — otherwise proceed."
The default is defensible (literature-anchored signs; reasonable
magnitudes). Proceeding with the defaults *and* flagging
explicitly in §15 so Vlad can override.

### 3.4 Rule implementations

Three rule changes, all following the Phase 8a fallback pattern:

```python
# In BoundedConfidenceInfluence.apply:
epsilon = float(agent.state.attrs.get("epsilon", self.epsilon))
# use `epsilon` in the rest of the rule

# In GaussianNoise.apply (anchor pull):
alpha = float(agent.state.attrs.get(
    "fj_alpha", env.attrs.get("fj_alpha", 0.0)
))
# use `alpha`

# In AffectiveUpdate.apply:
lr = float(agent.state.attrs.get("affect_lr", self.lr))
# use `lr` in the rest
```

Non-pillar scenarios (which don't set these attrs) get the
rule-level / env-level constants — bit-identical to Phase 8a.

---

## 4. M2 — `ResidentialMigration` (Bishop's Big Sort)

### 4.1 The rule

A new `EnvRule` that, each tick, with probability `migration_rate`
per agent, shifts the agent's `social_coord` toward the in-party
mean `social_coord` (with a noise term for the "inadvertent"
component).

```python
class ResidentialMigration:
    """Bishop 2008 / Brown & Enos 2021: Americans geographically
    sort by partisan preference over decades.

    Each tick, each agent with probability `migration_rate` shifts
    its `social_coord` toward the in-party mean social_coord, plus
    a noise term representing the ~70% "inadvertent" share Brown &
    Enos document.

    `migration_rate = 0` is an exact no-op — pillar baseline."""

    def __init__(
        self,
        migration_rate: float = 0.0,
        intentional_share: float = 0.30,
        max_step: float = 0.05,
    ):
        self.migration_rate = migration_rate
        self.intentional_share = intentional_share
        self.max_step = max_step

    def apply(self, env, agents, space, rng, tick):
        if self.migration_rate <= 0:
            return
        # Compute per-party social_coord means.
        by_party_means = {}
        by_party_agents = {}
        for a in agents:
            party = a.state.attrs.get("party")
            if party is None:
                continue
            by_party_agents.setdefault(party, []).append(a)
        for party, party_agents in by_party_agents.items():
            coords = [a.state.attrs.get("social_coord", 0.0)
                      for a in party_agents]
            by_party_means[party] = float(np.mean(coords))
        # Per-agent migration.
        for a in agents:
            if rng.random() > self.migration_rate:
                continue
            party = a.state.attrs.get("party")
            if party not in by_party_means:
                continue
            target = by_party_means[party]
            current = a.state.attrs.get("social_coord", 0.0)
            # Intentional component: shift toward in-party mean.
            intentional = self.intentional_share * (target - current)
            # Inadvertent component: random lifestyle drift.
            inadvertent = (1 - self.intentional_share) * rng.normal(
                0.0, self.max_step
            )
            new = current + np.clip(intentional + inadvertent,
                                    -self.max_step, self.max_step)
            a.state.attrs["social_coord"] = float(np.clip(new, -1.0, 1.0))
```

### 4.2 Pillar invariant

The pillar's `social_coord` is fixed (Phase 3 §3 — "never updated
by any rule"). `ResidentialMigration.migration_rate = 0` is the
pillar default, so the rule is an exact no-op in every pillar run.

In the historical scenario, `migration_rate` is scheduled (low
1980-90, ramping post-2000 per Bishop's documented timing).

---

## 5. M3 — `CohortReplacement`

### 5.1 The rule

An `EnvRule` that, each tick, replaces a small fraction of agents
with new agents drawn from a *cohort distribution* that shifts by
decade.

```python
class CohortReplacement:
    """Phillips 2022 / generational cohort replacement.

    Each tick, with probability `replacement_rate`, an agent is
    replaced with a new agent drawn from the current cohort's
    distribution. Replaced agent: oldest first (proxied by
    smallest agent id; ids are stable, so this is "FIFO replace").

    Cohort distribution shifts by tick:
      1980-1995 (ticks 0-45): Boomer cohort - centrist-leaning.
      1995-2015 (ticks 45-105): Gen-X / early Millennial - slight L.
      2015-2025 (ticks 105-135): late Millennial / Gen-Z -
                                  L-leaning, higher college share."""

    def __init__(self, replacement_rate: float = 0.0):
        self.replacement_rate = replacement_rate
```

`replacement_rate = 0` is the pillar default (no-op).

### 5.2 Cohort distributions

| Cohort | Tick range | Initial ideology distribution | Identity strength | Identities centre |
|---|---|---|---|---|
| Boomer | 0-45 | `x ~ N(0, 0.45)`, `y ~ N(0, 0.45)` | Beta(2, 2) | `[0, 0, 0]` |
| Gen-X / early Millennial | 45-105 | `x ~ N(-0.05, 0.45)`, `y ~ N(0.05, 0.45)` | Beta(2, 2.2) | `[0, 0, 0.1]` |
| Late Millennial / Gen-Z | 105-135 | `x ~ N(-0.10, 0.45)`, `y ~ N(0.10, 0.45)` | Beta(1.8, 2) | `[0, 0, 0.15]` |

Modest shifts; not dramatic. Phillips 2022 finds cohort effects
are real but smaller than period effects.

### 5.3 Replacement mechanics

When an agent is selected for replacement:
1. Generate a new agent from the current cohort's distribution.
2. Inherit the replaced agent's `id` (so network ties stay
   structurally intact — the "node" persists; the "person"
   changes).
3. Wipe the replaced agent's affect, anchor, party_cue. Re-seed
   from the new agent's distribution.
4. The network connections persist (the inherited id keeps them).

This is a stylized abstraction. The literature distinguishes
*compositional* effects (new people joining electorate) from
*conversion* effects (existing people changing); cohort
replacement here is the compositional channel.

---

## 6. M4 — Asymmetric polarization

### 6.1 Per-party `PARTY_CUE_SIGMA`

The historical scenario seeds `party_cue` with **per-party σ**:
- σ_dem = 0.22 (slightly narrower than the pillar default)
- σ_rep = 0.30 (slightly wider — Hacker & Pierson asymmetry)

The pillar's symmetric σ=0.25 is unchanged.

### 6.2 `EliteDrift.asymmetric`

The historical scenario activates `EliteDrift` with
`asymmetric={0: 0.5, 1: 1.5}` (Dems drift left at 50% of base rate;
Reps drift right at 150% of base rate). Base rate scheduled by
decade (see §8). The pillar's `EliteDrift.rate = 0` (inert).

---

## 7. M5 — IdentitySorting with time-varying rate

The historical scenario activates `IdentitySorting` with a
piecewise-constant `sort_rate` per decade:

| Decade | sort_rate |
|---|---|
| 1980-90 | 0.005 |
| 1990-00 | 0.015 |
| 2000-10 | 0.025 |
| 2010-20 | 0.025 |
| 2020-25 | 0.020 |

Pillar's `IdentitySorting.sort_rate = 0` unchanged.

---

## 8. Event schedule

Six events at fixed ticks. Each is a `(tick, callable)` pair on
the scenario's `Schedule`.

| Year | Tick | Event | Type | Action |
|---|---|---|---|---|
| 1987 | 21 | Fairness Doctrine repealed | step | `MediaConsumption.strength: 0 → 0.02` |
| 1996 | 48 | Fox News launched | step | `MediaConsumption.strength: 0.02 → 0.04` |
| 2008-12 | 84-96 | Social media mass adoption | ramp (12 ticks) | `BC.affect_weight: 0 → 0.3` linear over the window |
| 2010 | 90 | Citizens United | step | `EliteDrift.rate: 0 → 0.003` (with asymmetric={0:0.5, 1:1.5}) |
| 2016 | 108 | Trump election | step + identity-sorting bump | `IdentitySorting.sort_rate += 0.005` for 6 ticks (2 years) |
| 2020-21 | 120-123 | COVID + 2020 election + Jan 6 | step then revert | `AffectiveUpdate.lr × 1.5` for 3 ticks, then revert |

Implementation: a `Schedule` carries an ordered list of `(tick,
event_fn)` pairs. The scenario's `run_to(target_tick)` method
advances the engine in chunks bounded by upcoming events; each
event's `event_fn(engine)` mutates parameters.

Plus the **per-decade IdentitySorting transitions** at ticks 30,
60, 90, 120 — these are also Schedule entries (5 piecewise-constant
boundaries).

---

## 9. Per-decade pre-registered targets

Targets are pinned **before any calibration runs**. The discipline
is: measure each decade's end-state; if all primary metrics in
band, bless the decade's calibration; if any out of band, attempt
*bounded* per-decade-knob adjustment (≤2 retries); if still out of
band, document as a miss and continue.

### 9.1 The targets (primary metrics gate; secondary report)

| Metric | 1990 | 2000 | 2010 | 2020 | 2025 | Confidence |
|---|---|---|---|---|---|---|
| **Ideological constraint** (PRIMARY) | [0.35, 0.50] | [0.45, 0.60] | [0.55, 0.70] | [0.60, 0.75] | [0.62, 0.78] | high |
| **Party separation** (PRIMARY) | [0.50, 0.65] | [0.55, 0.70] | [0.60, 0.75] | [0.65, 0.80] | [0.68, 0.82] | high |
| **Affective polarization** (PRIMARY) | [-0.45, -0.30] | [-0.55, -0.40] | [-0.65, -0.50] | [-0.78, -0.60] | [-0.85, -0.65] | high |
| **Within-party SD_x** (PRIMARY) | [0.18, 0.32] | [0.18, 0.30] | [0.17, 0.28] | [0.15, 0.25] | [0.15, 0.22] | medium-high |
| Variance (secondary) | [0.40, 0.55] | [0.30, 0.45] | [0.20, 0.35] | [0.15, 0.25] | [0.13, 0.20] | medium |
| Cross-cutting tie fraction (secondary) | [0.25, 0.35] | [0.20, 0.30] | [0.18, 0.28] | [0.15, 0.25] | [0.15, 0.25] | medium |
| Party modularity (secondary) | [0.15, 0.25] | [0.20, 0.30] | [0.25, 0.38] | [0.30, 0.42] | [0.32, 0.45] | low-medium |

### 9.2 Sources by metric

- **Ideological constraint, party separation, within-party SD**:
  DW-NOMINATE per-Congress (Lewis et al., voteview.com); ANES
  cumulative file; Baldassarri & Gelman 2008 (*AJS* 114:408)
  longitudinal correlation tables.
- **Affective polarization**: Iyengar et al. 2019 (*ARPS*
  22:129) figure 1; Finkel et al. 2020 (*Science* 370:533)
  figure 1; ANES feeling-thermometer time series scaled to
  [-1, 1].
- **Variance**: derived from ANES self-placement spread.
- **Cross-cutting tie fraction**: Mutz 2006 (*Hearing the Other
  Side*) historical reconstruction; Levendusky 2021 (*Our Common
  Bonds*); Brown & Enos 2021 (*Nature Human Behaviour* —
  precinct-level partisan exposure).
- **Party modularity**: derived from cross-cutting + party-density
  estimates; literature is sparser, hence low confidence.

### 9.3 Initial-condition (1980) targets

Pre-build calibration: build a population whose 1980 measurements
hit:

| Metric | 1980 target band |
|---|---|
| Variance | [0.45, 0.60] |
| Ideological constraint | [0.25, 0.40] |
| Party separation | [0.45, 0.60] |
| Affective polarization | [-0.35, -0.20] |
| Within-party SD_x | [0.20, 0.35] |
| Cross-cutting tie fraction | [0.30, 0.40] |
| Identity sorting (sorting_index) | [0.20, 0.35] |

---

## 10. The calibration harness

`scripts/phase8b_calibration.py` runs the smart-calibration loop:

### 10.1 Loop structure

```
for decade in (1980-90, 1990-00, 2000-10, 2010-20, 2020-25):
    pre-register targets (already in §9)
    set per-decade knobs to literature-anchored starts
    run 5-seed ensemble for the decade
    measure decade-end metrics
    if all primary in band:
        bless calibration; commit knobs; continue
    else:
        attempt bounded adjustment (max 2 retries):
            for each out-of-band primary metric:
                adjust the most-mechanistically-linked knob
                bound by ±20% of literature-anchored value
            re-run; re-measure
        if still out of band: document miss; continue
```

### 10.2 Knob → metric mapping (for bounded adjustment)

Used by the calibration loop to choose which knob to adjust when a
metric is out of band:

| Out-of-band metric | Primary knob to adjust |
|---|---|
| Ideological constraint too low | `IdentitySorting.sort_rate` ↑ |
| Ideological constraint too high | `IdentitySorting.sort_rate` ↓ |
| Party separation too low | `EliteDrift.rate` ↑ (or asymmetric multiplier) |
| Party separation too high | `EliteDrift.rate` ↓ |
| Affective polarization too high (more negative) | none — accept; AffectiveUpdate.lr is per-agent + scheduled |
| Affective polarization too weak | `affect_lr` heterogeneity factor ↑ at decade boundary |
| Within-party SD too low | residential migration intentional_share ↓ |
| Within-party SD too high | residential migration intentional_share ↑ |
| Cross-cutting tie fraction too low | network rewiring (already scheduled) |
| Cross-cutting tie fraction too high | network rewiring intensification |

### 10.3 Forbidden — never adjust to fit a decade

These are the curve-fitting guardrails:

- `TICKS_PER_YEAR`, `FJ_ALPHA`, `BC_TEMPERATURE`,
  `BC_AFFECT_WEIGHT`, `TR_AFFECT_WEIGHT_REWIRE`,
  `BACKLASH_AFFECT_THRESHOLD`, `COOPERATIVE_MUTE`,
  `PARTY_CUE_SIGMA` constants.
- The pillar's S0-S4 bundle parameter values.
- HK canonical-test thresholds.
- The X1-X6 intervention bucket labels under the pillar's S4
  end-state.

If a decade can't be calibrated using only the per-decade-tunable
knobs, document the miss and continue. **Hard stop if tempted to
touch a forbidden knob.**

---

## 11. Tests

### 11.1 New: `tests/test_phase8b_mechanisms.py`

For each of the 5 mechanisms, a pillar-fallback test confirming
that the pillar (no per-agent heterogeneity, no residential
migration, no cohort replacement, no time-varying IdentitySorting,
no asymmetric EliteDrift) behaves bit-identically to Phase 8a.

8-10 tests total — one per mechanism's fallback + a few sanity
checks (per-agent attrs seeded correctly in the historical
scenario; pillar agents don't have these attrs; cohort distribution
generator produces in-range values; etc.).

### 11.2 New: `tests/test_phase8b_historical.py`

The decade-by-decade calibration assertions. Each decade has:

```python
def test_decade_1980_1990_targets():
    """Pre-registered targets for 1980-90 should be hit by the
    blessed calibration. If not, the test fails and the calibration
    is re-blessed."""
    metrics = run_decade_ensemble(decade=0, seeds=range(5))
    for metric, band in PRE_REGISTERED_TARGETS["1990"].items():
        if metric in PRIMARY_METRICS:
            assert band[0] <= metrics[metric] <= band[1], (
                f"1990 {metric} = {metrics[metric]} out of band {band}."
            )
```

One test per decade (5 tests). Plus an "all 73 pillar tests still
green" smoke that re-runs the pillar's HK/machinery/Phase 4-8a
assertions to confirm no historical-scenario change leaked.

### 11.3 Existing tests must stay green

All 73 existing tests run unchanged. The implementation pattern
(agent-attr-first-with-fallback) preserves bit-identical pillar
behaviour.

---

## 12. Build sequencing

Five slices.

- **Slice 1 — heterogeneity (M1).** Rule changes in
  `influence.py`, `noise.py`, `affective_update.py` to read agent
  attrs with fallback. New unit tests confirming pillar fallback.
- **Slice 2 — ResidentialMigration (M2) + CohortReplacement (M3).**
  Two new rule files. Unit tests confirming `rate = 0` no-op.
- **Slice 3 — Schedule + historical_arc.py (build scaffold).**
  The Schedule type; the 1980 cold-build with all per-agent attrs
  seeded; the 6-event schedule wired.
- **Slice 4 — Calibration harness.** `scripts/phase8b_calibration.
  py` with the bounded-adjustment loop.
- **Slice 5 — Decade-by-decade execution.** Run 1980-90 → ... →
  2020-25. Document each decade's outcome.

Gate after each slice: all 73 existing tests still green. If any
breaks, hard stop.

---

## 13. Re-validation procedure

After Slice 5, the implementer reports:

1. **Per-decade calibration outcomes.** For each of 1990, 2000,
   2010, 2020, 2025 endpoints: target band vs measured value vs
   bucket (in / above / below); the per-decade knob settings
   blessed.
2. **Misses.** Any out-of-band metric, with mechanism diagnosis
   (which mechanism would need extension to bring it in band).
3. **Mechanism ablation (if cheap).** For each of M2-M5,
   measure the 2025 end-state with that mechanism's rate set
   to 0. Reports the contribution of each mechanism to the
   historical fit.
4. **Forbidden-knob audit.** Confirm no forbidden constant was
   touched. The 73-test green-light is the regression guard.
5. **Phase 8c follow-ups.** List of mechanism gaps the calibration
   exposed (e.g., "perception-gap dynamics may be needed if
   affective polarization undershoots at 2020").

---

## 14. Done checklist

- [ ] Spec confirmed; B-Heterogeneity-Magnitude default accepted
      or overridden.
- [ ] M1-M5 implemented with pillar fallback; pillar 73-test suite
      green.
- [ ] `historical_arc.py` builds at 1980 with all per-agent attrs
      seeded; initial-condition measurements in band.
- [ ] Schedule applies 6 events at correct ticks; 4 IdentitySorting
      transitions at decade boundaries.
- [ ] Calibration harness runs decade-by-decade; bounded
      adjustments respected; misses documented.
- [ ] Per-decade test assertions pass for hit decades; miss
      decades documented in `methods.md`.
- [ ] Mechanism ablation reported.
- [ ] No forbidden knob touched.
- [ ] No UI / website file touched.

---

## 15. New judgment fork (one), per spec-pinning

**B-Heterogeneity-Magnitude (NEW):** the specific magnitudes for
per-agent heterogeneity correlation with `identity_strength`. The
design's B-Heterogeneity-Shapes confirmed "Beta correlated with
identity_strength"; the magnitudes (40% epsilon, 60% α, 80%
affect_lr) are the implementer's calibration choice within that
form.

Default (per §3.3): `EPSILON_HETERO_FACTOR=0.40`,
`FJ_HETERO_FACTOR=0.60`, `LR_HETERO_FACTOR=0.80`, each with jitter
factor 0.10. Signs per literature: epsilon negative; α and
affect_lr positive.

**Alternatives:**
- Uniform 50% across all three — symmetric defaults, less faithful
  to the engagement-heterogeneity literature.
- All at 100% — maximal heterogeneity; risks producing
  parameter-near-zero agents.
- Lower at 20% / 40% / 60% — gentler heterogeneity; safer if the
  defaults produce instability.
- Hand-tuned per-decade — breaks the per-decade-scope discipline.

**Proceeding with defaults** per Vlad's "calibration-within-
confirmed-form" pattern (Phase 8a's PARTY_CUE_SIGMA was set the
same way: design confirmed the form, spec pinned a value). If the
defaults produce calibration trouble in §13, the implementer
flags it in the result and can propose adjustment within the
explicit cushion (±50% of these magnitudes).

---

*Standing by to proceed with implementation.*
