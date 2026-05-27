# Phase 7 Implementation Spec — Calibration: tick-to-real-time, step sizes against panel data

*The final phase. Phases 1-6 produced a model that reproduces the
**qualitative** catalog of polarization mechanisms, sorting dynamics,
and intervention outcomes — Iyengar's affect-outpaces-ideology ratio,
Mason's mega-identity sorting, Bail's exposure backfire, Guess/Nyhan's
algorithmic null, Levendusky's bounded dialogue effects, Hetherington's
elite-driven mass sorting. Phase 7 makes the model **quantitatively
defensible**: it pins what one tick represents in real-world time, and
tunes the step-size constants against published longitudinal data
(ANES out-party thermometer 1978-2020; Pew partisan-affect surveys;
DW-NOMINATE).*

*Like Phases 3-6, calibration is a measure-then-bless gate (§11).
Unlike them, Phase 7 also includes **sensitivity checks** for the
findings flagged by prior phases — particularly Phase 6's X3 outlet-
roster sensitivity and X5 centroid-pull magnitude.*

---

## 1. Scope and decisions pinned

Three groups: (C1) tick-to-real-time mapping; (C2) step-size
recalibration against panel data; (C3) sensitivity audit of prior
findings.

| # | Decision | Choice |
|---|----------|--------|
| C1 | **One tick = a fixed real-world duration**, pinned by anchoring the pillar's S0→S3 affect trajectory to the **ANES out-party thermometer fall from 1978 → 2020** (~42 years, ~28-point cooling from ~48° to ~20°, Finkel et al. 2020). The pillar's `TICKS = 200` ticks of S0→S3 produce mean `Δaffective_polarization ≈ -0.85` (Phase 5 §11). Pinning this 0.85 to the empirical 28-point thermometer drop gives **1 tick ≈ 0.21 years** (~2.5 months). This is a *single* calibration scalar, stored as `TICKS_PER_YEAR` in a new `abm/calibration.py` module. Every metric and intervention can then be reported in years, not ticks. |
| C2 | **Step-size recalibration is not a free re-tune of every parameter** — that would erase Phases 4-6 measurement work. It is targeted: only the **three pulls that drive trajectory speed** (`BoundedConfidenceInfluence.strength`, `PartyPull.strength`, `MediaConsumption.strength`) are re-checked against panel data. If their current values produce an S0→S3 affect trajectory consistent with the ANES headline within ±20%, no change; if not, scale uniformly to match. **Crucially: changes must preserve every Phase 4-6 directional test threshold** — the measure-then-bless rule. |
| C3 | **Per-agent heterogeneity is *not* added in Phase 7.** The carryover items from Phase 4 (heterogeneous `epsilon`/`α`/anchor decay) and Phase 5 (heterogeneous affect `lr`) are deferred to a post-MVP Phase 8 if needed. Phase 7 stays focused on global-scalar calibration and sensitivity. |
| C4 | **A `calibration.py` module ships** with: `TICKS_PER_YEAR` (the single pinned scalar); `ticks_to_years(ticks)` / `years_to_ticks(years)` helpers; a registry of empirical calibration anchors (the ANES thermometer trajectory, the DW-NOMINATE elite-divergence rate, the Allcott 2020 Facebook-deactivation 0.04 SD effect-size as a Phase 6 X3 sensitivity benchmark). |
| C5 | **A sensitivity audit ships** as a runnable harness (`scripts/phase7_sensitivity.py`) covering: (a) Phase 6 X3 outlet-roster sensitivity — shift Fox/MSNBC outward and re-measure X3's bucket; (b) Phase 6 X5 centroid-pull magnitude — sweep R3d {0.25×, 0.50×, 0.75×, 1.0×} and report which crosses the "real" threshold; (c) the FJ alpha calibration — sweep `FJ_ALPHA` and confirm the position-histogram "no-collapse" property survives; (d) the involuntary-tie share — confirm Phase 4 §13's t=0 cross-cutting fraction is robust to `INVOLUNTARY_PER_AGENT ∈ {0, 1, 2, 3}`. These are *reports*, not asserts — the model's qualitative findings should hold across the swept ranges; if any flips, surface it. |
| C6 | **`methods.md` ships** as the final documentation artifact: a short, citation-pinned record of every calibration choice made in Phases 0-7, the empirical evidence each rests on, and the residual uncertainties. This is the artifact that backs the "intellectually rigorous" claim of the eventual public-facing product. |

**Out of scope.**

- Heterogeneous per-agent parameters (Phase 8 if needed).
- Multi-country / cross-national calibration (would require an
  electoral-system parameter and a separate scenario builder).
- Real-time interactive controls in a UI (post-Phase-7).
- Calibration against social-media-platform-specific data (the model
  doesn't have platforms; X2 "Fix the algorithm" represents the
  algorithmic affect-muting channel abstractly).

---

## 2. Files

```
create  abm/calibration.py                 # C1 + C4: TICKS_PER_YEAR, helpers, empirical anchors
modify  abm/pillars/calm_to_camps.py       # if C2 prescribes scaling, applied here
modify  abm/metrics/__init__.py            # export the calibration helpers for downstream readers
create  tests/test_phase7.py               # C1 unit + C2 directional regression + C3 sensitivity smoke
create  scripts/phase7_calibration.py      # the §11 measure-then-bless harness
create  scripts/phase7_sensitivity.py      # the C5 sensitivity audit
create  methods.md                         # C6: the documentation artifact
modify  phase4_spec.md, phase5_spec.md, phase6_spec.md   # cross-link the calibration choices into the prior specs (no semantic change)
```

`abm/core/*`, `abm/rules/*`, `abm/pillars/intervention.py`,
`interventions_phase6.py`, and the canonical / machinery / network /
phase4 / phase5 / phase6 test modules: **no change** — Phase 7 is
documentation + a single calibration scalar + sensitivity reports.

---

## 3. C1 — Tick-to-real-time mapping

### 3.1 The anchor

The Iyengar / Finkel et al. 2020 / ANES record provides the
quantitative anchor: out-party feeling-thermometer scores fell from
**~48° to ~20°** between 1978 and 2020 — a **28-point drop over 42
years**. Normalising the thermometer's [0, 100] range to the model's
[-1, +1] affect axis, that's a Δ of (28 / 50) ≈ **0.56** on the
model's scale across 42 years.

The pillar produces a much larger Δ over 200 ticks (S0→S3 measured at
-0.85, Phase 5 §11). The mismatch is intentional: the pillar's S0→S3
is the *full* stylized arc from "neutral society" to "media-saturated
sorted society," which spans more than 42 years of real US history if
we take the 1950s "calm" baseline. The S0→S3 trajectory therefore
maps to roughly **60-70 years** in the calibration story (mid-1950s
to mid-2020s), giving 200 ticks ≈ 65 years ≈ **0.33 years per tick**.

A second anchor — partisan elite divergence per DW-NOMINATE — adds
~0.4 NOMINATE units over the same ~50-year window. The model's
`EliteDrift.rate = 0.0005` is off in the pillar's S0-S4 (the rule is
inert at the default); if a future scenario turns it on, the
calibration should produce ~0.4 / 50 = 0.008 NOMINATE-units-per-year,
which at 0.33 yr/tick is ~0.0026 per tick — well within the rule's
configurable range, but **not pinned here** (EliteDrift is not in the
pillar's active progression).

**Decision (judgment fork C1a):** pin `TICKS_PER_YEAR = 3.0` (one tick
= ~4 months). This rounds 0.33 to a clean 3, and produces the
following readable conversions:

- 1 year = 3 ticks
- 4-year election cycle = 12 ticks
- 10 years = 30 ticks
- 1 generation (≈30 years) = 90 ticks
- The pillar's `TICKS = 200` ≈ **67 years** of stylized history

### 3.2 The module

```python
# abm/calibration.py
"""Calibration constants — the bridge between simulation ticks and
real-world time (Phase 7 §3, anchored to Iyengar / Finkel et al. 2020
ANES thermometer trajectory).
"""
from __future__ import annotations

# Phase 7 §3: ticks-per-year, pinned by anchoring the pillar's S0→S3
# affective_polarization trajectory (Δ ≈ -0.85) to the ANES
# out-party-thermometer fall of ~28 points over 42 years (Finkel et al.
# 2020), normalised to the model's [-1, +1] affect axis.
# See methods.md §3.
TICKS_PER_YEAR: float = 3.0


def ticks_to_years(ticks: float) -> float:
    return ticks / TICKS_PER_YEAR


def years_to_ticks(years: float) -> int:
    return int(round(years * TICKS_PER_YEAR))


# Empirical calibration anchors — readable record of what each pinning
# decision was checked against. See methods.md for the citations.
EMPIRICAL_ANCHORS = {
    "out_party_thermometer": {
        "source": "Iyengar et al. 2019 (ARPS); Finkel et al. 2020 (Science 370:533)",
        "metric": "Δ out-party feeling thermometer, 1978-2020",
        "value_raw": -28.0,            # degrees on [0, 100]
        "value_normalised": -0.56,     # on the model's [-1, 1] axis
        "duration_years": 42.0,
        "expected_in_model": "affective_polarization Δ ≈ -0.56 across 42 years ≈ 126 ticks (S0→S2 in the pillar)",
    },
    "dw_nominate_divergence": {
        "source": "McCarty, Poole & Rosenthal 2006",
        "metric": "Δ Democratic-Republican median NOMINATE score, 1970-2020",
        "value_raw": 0.4,              # NOMINATE units
        "duration_years": 50.0,
        "expected_in_model": "EliteDrift.rate ≈ 0.0026 per tick if active",
    },
    "facebook_deactivation": {
        "source": "Allcott, Braghieri, Eichmeyer & Gentzkow 2020 (AER 110:629)",
        "metric": "Δ issue + affective polarization, 4-week Facebook deactivation",
        "value_raw_sd": -0.04,         # SD reduction
        "duration_years": 4 / 52,      # ~4 weeks
        "expected_in_model": "X3 'Quit cable news' Δsep ≈ -0.04 normalised, over ~0.3 ticks — too short to measure cleanly; X3's full-bundle measurement (200 ticks) reflects a sustained behavioural shift, not Allcott's 4-week experiment",
    },
}
```

---

## 4. C2 — Step-size recalibration

### 4.1 The check

The pillar's measured S0→S3 trajectory at the Phase 5 §11 numbers:
- variance: 0.669 → 0.135 (drops by ~80%).
- ideological_constraint: 0.46 → 0.61 (rises by ~33%).
- affective_polarization: 0.0 → -0.85 (cooling by 0.85 on the [-1, 1]
  axis, or **42.5 points** on a [0, 100] thermometer-like rescale).

The ANES thermometer fall is ~28 points over 42 years; if the pillar's
S0→S3 covers ~67 years (200 ticks at 3 ticks/year), the *proportional*
fall over the equivalent 42-year window of the pillar is
`-0.85 * (42/67) = -0.53` on the model's axis ≈ **26.6 points** on the
thermometer rescale.

**The pillar's cooling rate matches Finkel/ANES within 5%.** No
recalibration of the three pulls is required. C2 is a **directional
regression**: the test pins this measured agreement and triggers on a
future change that drifts the model away from the ANES anchor by more
than ±20%.

### 4.2 The test

```python
def test_pillar_affect_trajectory_matches_anes_within_band():
    """The pillar's S0→S3 affective cooling, restricted to a 42-year
    window (Iyengar 1978-2020), should land within ±20% of the ANES
    headline (28-point thermometer fall ≈ -0.56 on the model's axis)."""
    # Run pillar S3 at the calibrated TICKS_PER_YEAR=3, measure affect
    # at ticks = 0 and at ticks = 42 * TICKS_PER_YEAR = 126.
    # Assert: |measured Δ| in [0.45, 0.67] = [-20%, +20%] around -0.56.
```

### 4.3 If the test fails (Phase 8+)

If a future change drifts the trajectory out of band, the
implementer **does not silently re-tune** — they report and ask. The
calibration anchors are public-facing claims; changing them is a
modelling decision, not a code change. The §11 procedure (below)
applies.

---

## 5. C3 — Sensitivity audit

### 5.1 Phase 6 X3 outlet-roster sensitivity

The Phase 6 §11 measurement flagged X3 as backfire (Δsep = +0.27),
contingent on `US_MEDIA_OUTLETS_2024`'s positioning (the diet target
sits inward of the party centroids). Phase 7 verifies:

- **Sweep 1:** shift Fox `[0.6, 0.4]` → `[0.85, 0.65]` and MSNBC
  `[-0.55, -0.35]` → `[-0.85, -0.65]` (more polarized outlet roster);
  re-measure X3. If the diet target now sits **outward** of party
  centroids, X3 should flip to *helpful* (the centripetal pull becomes
  a centrifugal pull; removing it now helps).
- **Sweep 2:** drop Local TV `[0, 0.05]` from the roster (the
  centrist anchor); re-measure X3. Removing the diluting centrist
  outlet should make diets more extreme and partially restore X3 →
  partial/null.

**Report, don't assert.** The sweep results go into `methods.md` as
the honest qualification on X3's backfire claim. A static `test_phase7`
test asserts only that the **default-roster** X3 result is still
backfire (Δsep > 0.05) — a directional regression guard.

### 5.2 Phase 6 X5 centroid-pull magnitude

X5's measured Δsep = -0.14 sat just under the -0.15 "real" threshold.
The R3d alternatives were {0.50× (default), 0.25× more aggressive,
0.75× milder, 1.0× = identity i.e. no change}. Phase 7 sweeps:

- **0.75×:** mild moderation, expect Δsep ≈ -0.07 (still partial).
- **0.50×:** the current default — Δsep ≈ -0.14 (partial).
- **0.25×:** aggressive moderation, expect Δsep ≈ -0.25 (real).
- **0.00×:** centroids zero'd — expect Δsep < -0.40 (extreme real).

Report all four. `methods.md` documents which value RCV best
corresponds to (likely 0.5× — RCV moderates, doesn't erase party). A
follow-up could pin a separate intervention X5b "Drastic electoral
reform" at 0.25× — but that is a Phase 8 design call, not Phase 7.

### 5.3 Phase 4 FJ alpha sensitivity

The position histogram "no-collapse" property (Phase 4 §12) depends
on `FJ_ALPHA = 0.05`. Sweep `FJ_ALPHA ∈ {0.02, 0.05, 0.08, 0.10}` at
S4-end and report:
- Fraction of agents within 0.20 of centre.
- Fraction past 0.80.
- Party separation.

**Assert** that the no-collapse property holds at the current 0.05
default (regression guard); report the trajectory across the sweep.

### 5.4 Phase 4 INVOLUNTARY_PER_AGENT sensitivity

Sweep `INVOLUNTARY_PER_AGENT ∈ {0, 1, 2, 3}` and report t=0
`cross_cutting_tie_fraction` (already measured at 0.305 for per_agent=1
in Phase 4 §13; here we check the full sweep). Confirm the 0.18-0.25
target band is approached only at per_agent=0 (no involuntary
stratum) — honest acknowledgment that the per_agent=1 setting lands
above the spec's tight band but at the spec's floor (per_agent=0
defeats F3 entirely).

---

## 6. C4 — `calibration.py` module

Already defined in §3.2. Three exports:
- `TICKS_PER_YEAR` (the scalar).
- `ticks_to_years(ticks)` / `years_to_ticks(years)` (helpers).
- `EMPIRICAL_ANCHORS` (the registry).

Re-exported from `abm.metrics.__init__` for convenience — any code
plotting a metric trajectory can convert tick-axis to year-axis with
one import.

---

## 7. C6 — `methods.md`

The final documentation artifact. ~3-5 pages, no code, citation-pinned.
Sections:

1. **What the model represents.** One paragraph: a stylized US-like
   society in the post-WW2 to mid-2020s era; 250-400 agents = a
   "village-scale" society; one tick ≈ 4 months of stylized history.
2. **The five-stage pillar.** What S0-S4 each correspond to in
   real-world time (S0 = ~1955 quiet, S1-S2 = 1960s-90s sorting,
   S3 = 1990s-2010s media fragmentation, S4 = 2010s-onwards
   network sorting). Honest: the timeline is schematic, not literal.
3. **Calibration anchors.** Three: ANES thermometer (C1), DW-NOMINATE
   (C2, latent), Allcott Facebook deactivation (C5 sensitivity benchmark).
   For each: citation, value, what the model is checked against.
4. **The honesty-labels schema.** What each `label_kind` means (control
   / replication / illustrative / null / partial / real / backfire),
   with one example per kind from the live library.
5. **Known limitations.** A brief, honest list:
   - The timeline mapping is schematic — 200 ticks ≈ 67 years is a
     stylization, not a literal claim that any specific tick is 1995.
   - The two-party structure is fixed; multi-party / cross-national
     dynamics are out of scope.
   - The outlet roster is `US_MEDIA_OUTLETS_2024`-specific; X3's
     backfire reading is contingent on it (Phase 7 §5.1 sweep).
   - Agent heterogeneity is along `stubbornness` only; per-agent
     `epsilon`/`α`/`lr` are deferred to Phase 8.
   - Affect dynamics dilute under tie isolation in S4 (Phase 5 §11
     anomaly: not "S4 reverses sign-fix," "S4 sorts so hard that some
     agents stop forming animus altogether"); documented in the
     `affective_polarization` metric's docstring.
6. **What the model is for.** One paragraph: a teaching artifact for
   non-experts; the 5 intervention buckets are the primary public-facing
   payoff; results are *illustrative within a citation envelope*, not
   policy predictions.

---

## 8. C5 — Sensitivity audit harness

`scripts/phase7_sensitivity.py`. Runs §5.1-§5.4 sweeps and prints a
report. **Reports, doesn't assert** — the test suite has tighter
regression guards on the default values, while the harness explores
neighbourhood behaviour for the human reader.

Outputs go into stdout and `methods.md` (manually folded by the
implementer after the run).

---

## 9. Tests

### 9.1 New: `tests/test_phase7.py`

Six tests.

**C1 — tick-to-year mapping.**

- `test_ticks_per_year_pinned`: `TICKS_PER_YEAR == 3.0` (the C1a
  judgment fork's pinned value).
- `test_ticks_years_round_trip`: `years_to_ticks(ticks_to_years(t)) == t`
  for representative tick counts {3, 12, 30, 200}.
- `test_empirical_anchors_present`: `EMPIRICAL_ANCHORS` carries the
  three anchors with non-empty citation, value, source. Just a sanity
  guard that the anchor registry isn't accidentally emptied.

**C2 — ANES anchor regression.**

- `test_pillar_affect_trajectory_matches_anes_within_band`: described
  in §4.2. Builds at S3, runs `42 * TICKS_PER_YEAR = 126` ticks,
  asserts `|affective_polarization|` falls into the [0.45, 0.67]
  band (±20% around the ANES headline -0.56).

**C3 sensitivity — directional guards (asserted, not exploratory).**

- `test_x3_still_backfires_at_default_outlets`: re-run X3's bucket
  test at the default `US_MEDIA_OUTLETS_2024`; assert `Δsep > 0.05`.
  This is the regression guard for the X3 honesty label.
- `test_position_histogram_no_collapse_at_default_fj_alpha`: build
  at S4, run `TICKS`, assert fraction within [0.20, 0.50] from centre
  > 0.85, fraction past 0.80 < 0.02. The Phase 4 no-collapse property
  pinned at the default `FJ_ALPHA = 0.05`.

### 9.2 Regression guards (must still pass)

- **Canonical HK, machinery, Phase 4-6 tests** — unchanged. Phase 7 is
  documentation + a calibration scalar; no rule changes.

---

## 10. Build sequencing

Three slices.

- **Slice 1 — C1 + C4.** Create `abm/calibration.py` with
  `TICKS_PER_YEAR`, helpers, `EMPIRICAL_ANCHORS`. Add C1 unit tests.
  Gate: C1 tests pass; canonical / machinery / Phase 4-6 tests still
  pass at the same thresholds (no engine change).
- **Slice 2 — C2 anchor regression.** Add the ANES-anchor test
  (`test_pillar_affect_trajectory_matches_anes_within_band`). Gate:
  test passes at the current Phase 5 trajectory (-0.85 over 200 ticks
  reduces proportionally to ~-0.53 over 126 ticks — within band).
- **Slice 3 — C3 + C5 + C6.** Sensitivity audit harness, X3-and-
  no-collapse regression guards, `methods.md`. Gate: harness runs;
  test passes; `methods.md` exists with the six §7 sections.

---

## 11. Re-validation — measure, then bless

After Slice 3 is green, the implementer measures and reports:

1. **C1 mapping check.** Run the pillar 126 ticks of S3 (= 42 years
   at TICKS_PER_YEAR=3) and report mean `affective_polarization`.
   Expect within [-0.45, -0.67]; if outside, surface and either
   re-pin `TICKS_PER_YEAR` or note the model's miscalibration in
   methods.md.
2. **C2 trajectory.** Report S0→S1, S1→S2, S2→S3 affective + ideological
   trajectories. The ANES headline should be reproducible from these.
3. **C5 X3 outlet sweep.** Report Δsep for X3 under {default,
   polarized roster, no-Local-TV} outlet configurations. Confirm
   the default's backfire reading is robust under "no-Local-TV" but
   may invert under "polarized roster" (an honest qualification).
4. **C5 X5 centroid sweep.** Report Δsep for X5 under {0.00×, 0.25×,
   0.50×, 0.75×, 1.0×} centroid pulls. Confirm 0.25× crosses "real"
   if a Phase 8 X5b is desired.
5. **C5 FJ alpha sweep.** Position-histogram at {0.02, 0.05, 0.08,
   0.10}. Confirm the no-collapse property survives the neighbourhood.
6. **C5 INVOLUNTARY_PER_AGENT sweep.** t=0 cross-cutting fraction at
   {0, 1, 2, 3}. Confirm Phase 4 §13's per_agent=1 choice is honestly
   defended (above the spec band but at the spec floor).

Report all six to the user; commit the harness output into
`methods.md`'s §5 limitations.

---

## 12. Judgment forks — flagged for explicit confirmation

| ID | Decision | Default | Alternatives |
|----|----------|---------|--------------|
| C1a | `TICKS_PER_YEAR` | **3.0** (1 tick ≈ 4 months) — pins S0→S3 ≈ 67 years, S0→S2 ≈ 42-year ANES window | 2.0 (longer arc — S0→S3 ≈ 100 years); 4.0 (shorter — ~50 years); leave unpinned (treat ticks as abstract units) |
| C2a | Re-tune the three pulls if ANES anchor falls outside ±20% | report, don't auto-tune (preserves Phase 4-6 measurement work) | auto-scale all three pulls by the same factor (cleaner but erases tuning); re-pin per-pull (deeper recalibration) |
| C3a | Whether to add Phase 8 X5b "drastic reform" (centroid pull 0.25×) | not in Phase 7 — flagged for follow-up | add now (a "real" intervention) — but it's not a single recognisable real-world lever, just X5 turned up |
| C5a | Whether the X3 backfire claim depends on outlet roster | sensitivity sweep reports it; default-roster backfire is the regression guard | re-pin X3 to whichever outlet calibration is most defensible; or split X3 into X3a "Quit at calm baseline" (helpful) vs X3b "Quit at sorted end-state" (backfire) — but that's a Phase 8 redesign |
| C6a | Per-agent heterogeneity (Phase 4/5 carryovers) | deferred to Phase 8 — Phase 7 is global-scalar only | add per-agent `epsilon`/`α`/`lr` jitter now (more realistic; more parameters to calibrate) |

If the user does not override one before implementation begins, the
default is taken.

---

## 13. Supersedes, open items, done checklist

**Supersedes.** Nothing — Phase 7 is purely additive
(documentation + a calibration scalar + sensitivity reports).

**Open items (deferred, Phase 8 if needed).**

- Per-agent heterogeneous `epsilon`/`α`/`lr` (Phase 4/5 carryovers).
- Anchor decay (slow drift of `anchor` toward current ideology over
  decades — would let the FJ anchor track generational replacement).
- Cross-national / multi-party scenarios.
- X5b "drastic electoral reform" as a separate intervention (Phase 7
  C3a flagged but not built).
- X5 setup idempotency (Phase 6 carryover — currently halving twice
  halves twice; matters for an interactive UI but not for the §11
  measurement).
- `AffectiveUpdate.radius` is vestigial in name; could be renamed to
  `issue_norm` for clarity (Phase 5 review nit, deferred).

**Done checklist.**

- [ ] C1: `abm/calibration.py` exists with `TICKS_PER_YEAR=3.0`,
      helpers, `EMPIRICAL_ANCHORS`. C1 unit tests pass.
- [ ] C2: ANES-anchor trajectory test passes at the current Phase 5
      step sizes (no re-tuning required).
- [ ] C3: X3 default-outlet backfire regression guard passes;
      no-collapse property at default `FJ_ALPHA` passes.
- [ ] C5: sensitivity audit harness runs; outputs reported.
- [ ] C6: `methods.md` exists with the six §7 sections, citation-pinned.
- [ ] Canonical HK / machinery / Phase 4-6 tests still pass at the
      same thresholds (no engine change in Phase 7).
- [ ] Judgment forks (C1a, C2a, C3a, C5a, C6a) confirmed by the user
      or noted as defaulted.
- [ ] No UI / website file touched.

With Phase 7 done and signed off, the engine carries a single, public,
defensible mapping from ticks to real-world time; the three principal
pulls have been checked against the ANES headline; the prior phases'
findings have been audited for sensitivity; and `methods.md` documents
every calibration choice the project has made, with citations. The
research engine is then **complete enough to be shown to a lay
audience** with an intellectually honest record of what it does and
does not claim. UI / website work is the next phase, outside this
spec's scope.
