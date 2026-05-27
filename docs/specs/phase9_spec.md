# Phase 9 — Empirical-Distribution Calibration (Tier A)

*Match the historical-arc simulation's per-decade 2D ideology
distribution to the empirical KDE targets gathered in
`phase9_data/`. Builds on the Phase 9 cluster-diversity
investigation (see `phase9_cluster_diversity_report.md`) which
identified extremity-graded Friedkin-Johnsen stubbornness on
faction-seeded agents as the necessary and almost-sufficient
mechanism for preserving visible faction structure.*

---

## 0. Status & scope

- **Tier:** A (minimum-viable). Tier B/C deferred pending Tier A's fit result.
- **Engine reach:** `abm/pillars/historical_arc.py` only. Pillar
  (`calm_to_camps.py`) is bit-identical at default kwargs.
- **Forbidden knobs:** unchanged — TICKS_PER_YEAR, FJ_ALPHA,
  BC_TEMPERATURE, BC_AFFECT_WEIGHT, TR_AFFECT_WEIGHT_REWIRE,
  BACKLASH_AFFECT_THRESHOLD, COOPERATIVE_MUTE, PARTY_CUE_SIGMA,
  X1–X7 bucket labels not touched.
- **Sacred:** 73 pillar tests must stay green bit-identically.
- **Phase 8f §11 gate:** must hold ≥18/24 cells in band.

---

## 1. Target distributions

Already produced in Phase 9 data-gathering. Live at:

```
phase9_data/phase9_empirical_kde_<decade>.npy        # (50, 50), integrates to 1
phase9_data/phase9_empirical_pointcloud_<decade>.npy # (1000, 2), KDE-resampled
phase9_data/phase9_empirical_grid_x.npy              # (50,)
phase9_data/phase9_empirical_grid_y.npy              # (50,)
```

Decades: 1980, 1990, 2000, 2010, 2020.

Methodology: typology (Pew + Hidden Tribes, 30–40% weight) +
raw-style moment-matched (ANES + GSS + CCES + DW-NOM, 60–70%).
Documented in `phase9_empirical_targets.md` (augmented 2026-05-27).

Headline empirical trajectory the model must reproduce:
- `corr(x, y)`: 0.26 → 0.27 → 0.37 → 0.41 → 0.57 (monotone rise; Levendusky/Mason sorting).
- `var(x)`: 0.24 → 0.23 → 0.25 → 0.28 → 0.29 (rising party separation).
- `var(y)`: 0.21 → 0.22 → 0.26 → 0.26 → 0.27 (cultural-axis dispersion settles by 2000).
- `mean(|x|)`: 0.42 → 0.41 → 0.42 → 0.45 → 0.46.

---

## 2. Fit metric

### 2.1 Primary: 2D Wasserstein distance

Robust to multi-modal vs unimodal vs elliptical shapes. Measures the
mass-transport cost between the model's point cloud at a target year
and the empirical point cloud at the same decade.

Implementation: `POT` (Python Optimal Transport) `ot.emd2`.
- Sub-sample to 250 model points × 1000 target points per decade
  (exact EMD on n=250 is tractable; deterministic via seeded RNG).
- Sub-sampling RNG seed: `(decade_index * 31337) ^ run_seed` so
  the sub-sample is bit-identical per (decade, seed) pair.
- Distance metric for the cost matrix: squared Euclidean (`'sqeuclidean'`)
  on `[-1, 1]²` coordinates. Wasserstein-2 squared.

Loss reported per decade, then aggregated as a sum across
{1980, 1990, 2000, 2010, 2020}.

### 2.2 Secondary: shape-descriptor cross-check

Auxiliary diagnostic table — describes *how* the shape differs, not
used as the loss:

- `corr(x, y)` (model vs target)
- `var(x)`, `var(y)`
- `mean(|x|)`, `mean(|y|)`
- Number of KDE local maxima above density threshold 0.6 (proxy for
  "visible cluster count" — handles multi-centroid vs blob without
  forcing a particular k)
- Quadrant mass distribution (4-tuple summing to 1)

These appear in `phase9_results.md` alongside the Wasserstein table.

### 2.3 Why Wasserstein over KL

KL diverges when the model has zero density where the target has
mass (very common with cluster-mixture models). Wasserstein behaves
sanely on disjoint supports and naturally compares multi-modal vs
elliptical vs Gaussian-blob shapes. The 2018 *Cuturi*-school work on
optimal transport in ML established Wasserstein as the default for
distribution-shape calibration; it's the right primitive here.

---

## 3. Mechanism — Tier A

Three additions to `historical_arc.build_engine`, gated behind a
`factional_seeding: bool = False` kwarg.

### 3.1 HISTORICAL_FACTIONS_1980

Module-level dict in `historical_arc.py`. **1980-appropriate labels.**
Factions that emerged later (MAGA, DSA, Tea Party) are introduced via
scheduled re-labeling events (§4).

| Label | (x_center, y_center) | Weight | Party draw |
|---|---|---|---|
| `New_Left` | (-0.55, -0.40) | 0.08 | 0 (Dem) |
| `Mainstream_Dems` | (-0.30, -0.15) | 0.22 | 0 |
| `Blue_Dog_Dems` | (-0.20, +0.20) | 0.12 | 0 (cross-pressured) |
| `Centrists` | (+0.00, +0.00) | 0.12 | sigmoid(x) per existing K-schedule |
| `Classical_Liberals` | (+0.30, -0.30) | 0.06 | 1 (Rep, cross-pressured) |
| `Mainstream_Reps` | (+0.30, +0.15) | 0.22 | 1 |
| `Old_Right` | (+0.45, +0.35) | 0.12 | 1 |
| `New_Right_Religious` | (+0.40, +0.55) | 0.06 | 1 |

Weights sum to 1.00. Within-faction draw: `pos = center + N(0, 0.05)`,
clipped to `[-1, 1]²`. Sources for centroid placement:
- New_Left / Blue_Dog_Dems / Classical_Liberals positions per
  Treier & Hillygus 2009 *POQ* 73(4):679 (2D-IRT on 1980 ANES).
- Reagan_Coalition splitting (`Mainstream_Reps` ⊕ `Old_Right` ⊕
  `New_Right_Religious`) per Carmines & Stimson 1989 *Issue Evolution*.
- Cross-pressured strata (`Blue_Dog_Dems`, `Classical_Liberals`)
  per Hare et al. 2018 *Research & Politics* 5(2).

**Mass-population sources, not elite.** Centroids stay inside
`|x| < 0.55, |y| < 0.60` — voter-bound rather than legislator-bound
(DW-NOMINATE caveat).

### 3.2 Factional party_cue

Replace the centroid-based cue draw for partisans:

```python
# Existing (Phase 8a/8e):
# party_cue = PARTY_CENTERS_1980[party] + rng.normal(0, sigma_pc, size=2)

# Phase 9 Tier A (when factional_seeding=True):
party_cue = faction_center + rng.normal(0, 0.04, size=2)
```

The factional cue anchors PartyPull to the faction sub-centroid, not
the party centroid. Without this, PartyPull immediately drags every
agent off its faction position toward `PARTY_CENTERS_1980[party]`.

Centrists (faction-label `Centrists`, party drawn by sigmoid) keep
the existing `PARTY_CENTERS_1980[party]`-based cue — they're not
faction-anchored. Independents (party=2) keep no party_cue (Phase 8d).

### 3.3 Extremity-graded stubbornness

For each faction-seeded partisan, after the existing Beta(2, 5) draw:

```python
extremity = float(np.linalg.norm(faction_center))   # ‖(x, y)‖
stubbornness = min(0.90, stubbornness + 0.5 * extremity)
```

Mechanism intuition (Sears & Funk 1999 / Abramowitz & Saunders 2008 /
Mason 2015): extreme partisans are panel-stable; they shift least
across decades. The boost magnitude 0.5 is the prior agent's
proof-of-concept value (`kitchen_sink_v3`); a sweep over {0.3, 0.5,
0.7} in step 4 will confirm or refine.

Centrists and Independents do not receive the boost.

---

## 4. Faction-emergence events (light Tier C content folded in)

Added to the historical schedule. Each event re-labels existing
agents — no new spawns, population size unchanged.

| Year | Event | Affected | Sub-centroid | Δstubbornness |
|---|---|---|---|---|
| 2009 | Tea Party | ~7% of Mainstream_Reps (random draw, seeded) | (+0.55, +0.30) | +0.15 |
| 2015 | MAGA | ~9% of Mainstream_Reps + ~40% of New_Right_Religious | (+0.50, +0.55) | +0.15 |
| 2016 | Bernie surge | ~5% of Mainstream_Dems | (-0.55, -0.30) | +0.10 |
| 2018 | DSA emergence | ~3% of New_Left | (-0.70, -0.55) | +0.10 |

For each affected agent, the event:
1. Sets `attrs["faction"] = <new_label>`.
2. Updates `party_cue = sub_centroid + N(0, 0.04)` (factional cue updates).
3. Bumps `stubbornness = min(0.95, stubbornness + Δ)`.
4. **Does NOT** move the agent's current ideology position — the
   event re-anchors the agent's *target*, not its current state.
   The agent drifts toward the new sub-centroid under existing PartyPull.

Sources:
- Tea Party 2009: Skocpol & Williamson 2012 *The Tea Party and the
  Remaking of Republican Conservatism*.
- MAGA 2015: Sides, Tesler & Vavreck 2018 *Identity Crisis*.
- Bernie 2016: Heaney & Rojas 2015 *Party in the Street* + ANES 2016
  self-placement.
- DSA 2018: membership data (DSA national reports: 6k → 56k members
  2015–2018) + Schwartz 2017 *Jacobin* coverage.

The existing `_event_2016_trump_election` and `_event_2016_status_threat`
are preserved — they shift the GOP centroid and fire threat. The new
MAGA event is the *factional* counterpart, distinct from the
centroid-level shift.

---

## 5. Pillar bit-identity

`calm_to_camps.build_engine` does not accept `factional_seeding`.
Pillar agent build is unchanged. Pillar's `Schedule` does not include
the faction-emergence events.

The 4 new ScheduledEvent entries live only in
`historical_arc.build_engine`'s schedule, not pillar's.

Validation: run all 73 pillar tests bit-identically against
pre-Phase-9 head before merging.

---

## 6. Implementation order

### Step 1 — calibration harness (no engine touch)

New: `abm/calibration_phase9.py`.

Functions:
- `kde_from_positions(positions: np.ndarray, grid_x, grid_y) -> np.ndarray` —
  build a 50×50 KDE on the same grid as the targets, Silverman bandwidth.
- `wasserstein_2d(model_points, target_points, seed) -> float` —
  POT-based EMD with sub-sampling.
- `shape_descriptors(positions) -> dict` — corr, var, mean(|·|),
  KDE local-max count, quadrant mass.
- `score_engine_run(engine, schedule, decades, target_dir) -> pd.DataFrame` —
  end-to-end: run the engine, snapshot at each decade end, return
  per-decade Wasserstein + descriptors.

POT dependency check: if `import ot` fails, fall back to a
sub-sampled Sinkhorn approximation via `scipy.stats.wasserstein_distance`
applied per-axis as a degraded proxy (with a warning). Document the
fallback in the harness docstring.

Score the existing Phase 8f baseline (`factional_seeding=False`,
`independent_fraction=0.12`) at 9 seeds. Write
`phase9_baseline_score.json` and `phase9_baseline_descriptors.csv`.

### Step 2 — Tier A in historical_arc.py

1. Add `HISTORICAL_FACTIONS_1980` module-level constant.
2. Add `factional_seeding: bool = False` kwarg to `build_engine`.
3. In the agent-build loop, when `factional_seeding=True`:
   - Sample faction from the weighted dict.
   - Override initial position draw to `center + N(0, 0.05)`.
   - For partisans (non-`Centrists`): factional cue + stubbornness boost.
   - Tag `attrs["faction"] = <label>`.
4. Pillar `calm_to_camps.build_engine` unchanged.

### Step 3 — schedule events

Add the 4 `ScheduledEvent` entries to `historical_arc.build_engine`'s
schedule. Each event handler is a top-level function (picklable for
parallel workers) reading `engine.agents`, filtering by faction tag,
sampling the affected subset per a seeded RNG, and applying the
re-label.

### Step 4 — validation

Run in order:
1. **Pillar tests:** `pytest tests/ -k "not phase9 and not historical_arc"` — must be 73 sacred green bit-identical.
2. **Tier A measurement:** `calibration_phase9.score_engine_run` at 9 seeds, `factional_seeding=True`.
3. **Wasserstein delta:** Tier A must improve loss across all 5 decades vs baseline.
4. **Phase 8f §11 cells:** re-run `phase8f_diagnostic_runner.py` with `factional_seeding=True`. Must hold ≥18/24 in band.
5. **Stubbornness-boost sweep:** {0.3, 0.5, 0.7} on the 2025 endpoint Wasserstein. Bless the value that minimizes loss subject to §11 gate.

### Step 5 — documentation + commit

- `phase9_results.md`: loss table, shape-descriptor trajectory, §11 cell deltas, ablations, faction-emergence event traces.
- `methods.md` update: new §6 "Empirical-distribution calibration (Phase 9)" — Wasserstein method, target provenance, ablation summary, honest caveats.
- Commit per standard discipline.

---

## 7. Risk register

1. **Stubbornness change shifts Phase 8f party_sep.** The boost
   slows ideology-moving deltas, including the great-sort dynamics.
   Mitigation: the boost applies only to faction-seeded extremes
   (high ‖faction_center‖), so mainstream-cohort agents are
   minimally affected. Verify via §11 gate.

2. **Faction weights are eyeballed.** §3.1 weights come from rough
   ANES/Pew typology fractions, not measured. Sensitivity to ±5pp
   on each weight should be sub-dominant to the Wasserstein
   structure-shape effect, but a sweep over (DSA + MAGA) weights
   {3, 5, 7, 10}% × {5, 7, 10, 12}% is documented as a Phase 9b
   robustness check.

3. **The 4 faction-emergence events compound Phase 8f's existing
   `_event_2016_trump_election` and `_event_2016_status_threat`.**
   Net effect: 2016 GOP gets +centroid shift (existing), +threat
   firing (existing), +MAGA factional re-label for ~9% of
   `Mainstream_Reps` + ~40% of `New_Right_Religious` (new). Verify
   the combined 2010-2020 trajectory stays in Phase 8f §11 cells.

4. **Wasserstein on n=250 sub-samples has Monte Carlo noise.**
   Estimated bias ≈ O(n^{-1/2}) ≈ 0.06. Report the per-decade
   loss with 95% CI across seeds; require Tier A to improve by
   > 2× the CI half-width to count.

5. **POT dependency.** If `ot` isn't available in the workstation
   env, the harness falls back to a degraded per-axis Wasserstein.
   Document the fallback explicitly. Recommend `pip install POT` if
   not present — it's a single-package add with no surprising deps.

6. **Faction-label anachronism on emergence events.** The DSA
   emergence in 2018 is real-world late, not 2018-precise (DSA was
   founded 1982 with 6k members, ballooned 2015-2020). The label
   is correct; the *factional emergence* timing in the schedule is
   honest within ±2 years. Documented in `phase9_results.md`.

---

## 8. Sign-off

Tier A is parsimonious: 3 build-loop additions + 4 scheduled events
+ 1 kwarg. Pillar bit-identical. §11 gate preserved or
re-blessed per measure-then-bless discipline. Wasserstein loss
table is the primary headline; shape descriptors are the
diagnostic story.

Tier B (BC eps reduction, PartyPull damp, EliteDrift recalibrate)
and Tier C (additional event-driven faction dynamics) remain
options if Tier A's Wasserstein fit is insufficient on any decade.

---

## 9. Tier C — addendum (2026-05-27, after Tier A negative result)

Tier A failed both gates structurally (`phase9_results.md` §4):
factional ICs hard-bind party to position from t=0, so 1980
arrives already at modern polarization. Tier C inverts the
mechanism: **ICs stay broad-Gaussian (1980 §11 cells preserved);
factions emerge temporally as scheduled events fire post-2009.**

### 9.1 Mechanism

New rule `abm/rules/faction_anchor.py`:

```python
class FactionAnchor:
    """Pulls each agent toward its `faction_center` attr at strength
    `s * (1 - stubbornness) * (center - ideology)`. No-op for agents
    without a `faction_center` attr — so the rule is inert at t=0
    and inert in the pillar (which never tags factions)."""
    def __init__(self, strength: float = 0.04):
        self.strength = strength

    def apply(self, engine):
        for a in engine.agents:
            center = a.state.attrs.get("faction_center")
            if center is None:
                continue
            stubbornness = a.state.attrs.get("stubbornness", 0.0)
            delta = self.strength * (1.0 - stubbornness) * (
                center - a.state.ideology
            )
            a.state.ideology = np.clip(
                a.state.ideology + delta, -1.0, 1.0
            )
```

Rule placement: in the pipeline after `PartyPull`, before
`BoundedConfidenceInfluence`. So PartyPull pulls toward `party_cue`
(unchanged, party-centroid-noise), then FactionAnchor adds a
faction-specific tug for tagged agents, then BC homogenizes.

**Pillar bit-identity**: pillar agents never have `faction_center`
set → rule is no-op → pillar tests bit-identical even if the rule
is added to both pipelines. Safer than gating with a flag.

### 9.2 Event semantics under Tier C

The 4 existing faction-emergence events (`_event_2009_tea_party`,
`_event_2015_maga`, `_event_2016_bernie`, `_event_2018_dsa`) need
two changes:

1. **Stop overwriting `party_cue`.** Under Tier A, events overwrote
   `party_cue` to the sub-centroid — that compounded with
   PartyPull's existing pull and contributed to over-anchoring.
   Under Tier C, `party_cue` stays at its original party-centroid-
   noise value; PartyPull keeps pulling toward party, FactionAnchor
   adds the faction-specific tug.
2. **Set `attrs["faction_center"] = sub_centroid`.** This is what
   FactionAnchor reads. The current `attrs["faction"] = label` is
   kept for diagnostics.

The stubbornness bumps (+0.15 / +0.10) stay as specified in §4.

### 9.3 ICs under Tier C

**No factional ICs.** `factional_seeding` stays at its default
`False`. The 1980 build is bit-identical to Phase 8f. The
"factional structure" emerges entirely from the post-2009 events.

This is the cleanest preservation of the §11 1980 cells (which
Tier A broke). The trade-off: 1980 visualization has no visible
faction sub-modes; sub-modes appear progressively as events fire
from 2009 onward — closer to the historical narrative.

### 9.4 New kwargs

`historical_arc.build_engine` gains:
- `faction_anchor_strength: float = 0.04` — passed to FactionAnchor
  constructor.
- `faction_anchor_events: bool = True` — gates whether the 4
  emergence events fire. Default True under historical_arc (we want
  them to fire); pillar build never invokes these events anyway.
- `event_stubbornness_bump_multiplier: float = 1.0` — multiplies
  the per-event Δstubbornness (0.15 → 0.15×mult, 0.10 → 0.10×mult).
  Lets us sweep stubbornness anchoring without code edits.

`abm/rules/faction_anchor.py.FactionAnchor` itself takes only
`strength`. The rule is added to BOTH pillar and historical_arc
pipelines unconditionally — it self-gates on the `faction_center`
attribute being present.

### 9.5 Sweep design

12-cell sweep:
- `faction_anchor_strength ∈ {0.02, 0.04, 0.06, 0.08}`
- `event_stubbornness_bump_multiplier ∈ {0.5, 1.0, 1.5}`

At 5 seeds per cell. Score Wasserstein + §11. Bless the cell that
minimizes summed Wasserstein subject to §11 cells ≥ 18/24.

### 9.6 Validation gates

Same as Tier A:
1. Pillar tests bit-identical (the new rule + new events are inert
   without `faction_center` attr).
2. Phase 8f §11 cells: must hold ≥18/24 under Tier C blessed config.
3. Wasserstein: at least 2 of 5 decades must improve significantly
   vs baseline (specifically 2010 and 2020, where faction-emergence
   events have had time to act).

### 9.7 What gets retired vs preserved from Tier A

- **Retired:** `factional_seeding=True` flow is left in code but no
  longer the recommended path. Tests that exercise it stay green.
- **Preserved:** `HISTORICAL_FACTIONS_1980` dict is unused under Tier
  C (no factional IC), but kept for the visualization tier if Vlad
  later wants to ship it as the demo product. The 4 emergence
  events are re-wired (per §9.2), not removed.

### 9.8 Risk register (Tier C)

1. **Strength × stubbornness compounding.** Stubbornness bump from
   events (+0.15) reduces the FactionAnchor pull by a factor of
   roughly (1 - 0.15·multiplier). Net pull on a tagged agent is
   `strength · (1 - stubbornness)`. At default stubbornness 0.29
   and bump 0.15, effective pull is 0.04·(1 - 0.44) ≈ 0.022. Sweep
   range covers this — strength=0.08 with multiplier=0.5 gives
   effective pull ≈ 0.045, comparable to PartyPull's 0.07.

2. **Event timing.** 2009 / 2015 / 2016 / 2018 give the rule
   ~16 / 10 / 9 / 7 years to act by 2025. Strength=0.04 with 16 ticks
   moves a tagged Mainstream_Rep from ideology ~0.30 toward
   Tea_Party sub-centroid (+0.55, +0.30) by roughly 0.4·(0.04·0.71)·16
   ≈ 0.18 — meaningful but not extreme. Reality check by 2025.

3. **2010 ENS-band wp_sd.** The events tag only 3-9% of partisans.
   The bulk of within-party SD is unaffected. Hypothesis: §11 wp_sd
   stays close to Phase 8f baseline (which is already in band).
   Risk: if FactionAnchor's pull on tagged agents is strong enough,
   it could *increase* wp_sd above the upper band edge by 2025.
   Sweep will catch this.
