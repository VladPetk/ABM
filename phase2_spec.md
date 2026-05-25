# Phase 2 Implementation Spec — Pillar Stages S2 & S3

*Companion to `pillar_engine_roadmap.md` (§6 Phase 2), `pillar_spec.md`, and
`phase1_spec.md`. Phase 1 already built the full superset population, env, and
rule pipeline — every mechanism S2 and S3 need is present at strength 0. So
Phase 2 is pure assembly: two new `Intervention` objects, their validation
tests, and one small cleanup. No new package files, no builder changes, no
engine changes. Every numeric threshold below was measured against the real
engine — see §8.*

---

## 1. Decisions pinned (the ten-minute review)

| # | Decision | Value |
|---|----------|-------|
| D1 | S2 bundle | S1 + `PartyPull.strength = 0.04` + `AffectiveUpdate.lr = 0.01` |
| D2 | S3 bundle | S2 + `MediaConsumption.strength = 0.04` |
| D3 | `EliteDrift` and `IdentitySorting` | stay at 0 — optional intensifiers, not in the validated core (`pillar_spec.md`) |
| D4 | S2 validation metric | `ideological_constraint` (positional, robust). **Not** `affective_polarization` — it has an unresolved sign issue (§6). |
| D5 | S3 validation design | **paired** S3-vs-S2: correlate diet extremity with the per-agent radial effect of media. Unpaired raw drift is too noisy to test (measured — §8). |
| D6 | Tests zero `AffectiveUpdate.lr` | `AffectiveUpdate` never moves an agent and never draws from the RNG, so zeroing it leaves every position bit-identical while removing its O(n²) cost. Proven by a dedicated test (§5). |
| D7 | Validation style | directional, ensemble — same as Phase 1 (roadmap R3). |

---

## 2. Files

```
modify  abm/pillars/calm_to_camps.py   # add S2 + S3 Interventions; extend PILLAR
modify  tests/test_pillar_stages.py    # add S2, S3, and the inertness test
modify  tests/conftest.py              # add 2 helpers
delete  abm/rules/partisan_media.py    # dead code (G8 — §7)
modify  abm/rules/__init__.py          # drop the PartisanMediaExposure export (G8)
```

---

## 3. The S2 and S3 Interventions — exact bundles

Bundles are absolute (Phase 1 decision D5): each lists the same eight tunables
as S0/S1, so any stage's bundle fully determines the world.

**S2 — Party identity** (`label_kind="illustrative"`):

```python
S2_PARTY_IDENTITY = Intervention(
    id="S2_party_identity",
    label="Party identity",
    description="Agents drift toward their party's centre; party identity "
                "starts to predict issue position.",
    label_kind="illustrative",
    citation="Hetherington 2001; Levendusky 2009",
    predicted_effect="Clusters align to party centroids; ideological "
                     "constraint (party-issue correlation) rises.",
    param_bundle=(
        ("GaussianNoise", "sigma", 0.01),
        ("BoundedConfidenceInfluence", "epsilon", 0.30),
        ("BoundedConfidenceInfluence", "strength", 0.08),
        ("PartyPull", "strength", 0.04),
        ("AffectiveUpdate", "lr", 0.01),
        ("MediaConsumption", "strength", 0.0),
        ("IdentitySorting", "sort_rate", 0.0),
        ("EliteDrift", "rate", 0.0),
    ),
)
```

**S3 — Partisan media** (`label_kind="illustrative"`): identical to S2 plus
the media-diet force on.

```python
S3_PARTISAN_MEDIA = Intervention(
    id="S3_partisan_media",
    label="Partisan media",
    description="Each agent drifts toward the outlets in its media diet; "
                "heavy partisan diets pull hardest.",
    label_kind="illustrative",
    citation="Levendusky 2013; Martin & Yurukoglu 2017",
    predicted_effect="Heavy partisan-media consumers are pushed further "
                     "from centre than light consumers.",
    param_bundle=(
        ("GaussianNoise", "sigma", 0.01),
        ("BoundedConfidenceInfluence", "epsilon", 0.30),
        ("BoundedConfidenceInfluence", "strength", 0.08),
        ("PartyPull", "strength", 0.04),
        ("AffectiveUpdate", "lr", 0.01),
        ("MediaConsumption", "strength", 0.04),
        ("IdentitySorting", "sort_rate", 0.0),
        ("EliteDrift", "rate", 0.0),
    ),
)
```

Extend the pillar (the only other change in `calm_to_camps.py`):

```python
PILLAR = Pillar(
    id="calm_to_camps",
    title=TITLE,
    build_engine=build_engine,
    interventions=(S0_BASELINE, S1_BOUNDED_CONFIDENCE,
                   S2_PARTY_IDENTITY, S3_PARTISAN_MEDIA),
)
```

That is the entire engine-facing change. `show_pillar.py` and the test
machinery already read `PILLAR.interventions`, so both pick up four stages
with no edit.

---

## 4. Test helpers (add to `tests/conftest.py`)

```python
from abm.metrics.affective import ideological_constraint
from abm.core.outlets import diet_target, US_MEDIA_OUTLETS_2024
import numpy as np

OUTLETS_BY_ID = {o.id: o for o in US_MEDIA_OUTLETS_2024}

def constraint_avg(engine) -> float:
    ic = ideological_constraint(engine.agents)
    return (ic["x"] + ic["y"]) / 2.0

def diet_extremity(agent) -> float:
    """How partisan an agent's media diet is — distance of its diet's
    weighted-mean outlet position from the centre."""
    return float(np.linalg.norm(diet_target(agent.state.attrs["media_diet"],
                                            OUTLETS_BY_ID)))

def positional_engine(stage_index: int, seed: int):
    """build_at_stage, then zero AffectiveUpdate (D6: positionally inert,
    big speedup). Use for every positional test."""
    eng = build_at_stage(PILLAR, stage_index, seed)
    for rule in eng.rules.rules:
        if type(rule).__name__ == "AffectiveUpdate":
            rule.lr = 0.0
    return eng
```

---

## 5. The tests (add to `tests/test_pillar_stages.py`)

### test_affective_update_is_positionally_inert

Justifies D6. Build at S2 twice — once with `AffectiveUpdate.lr = 0.01` (the
real bundle), once with `lr = 0.0` — run both 60 ticks, assert
`np.array_equal` of final positions. (`AffectiveUpdate` writes only the
`affect` attribute and never calls the RNG, so this must hold.) One seed is
enough.

### test_s2_party_identity_raises_constraint

```
for seed in STAGE_SEEDS:
    constraint_S1 = constraint_avg( run( positional_engine(1, seed), TICKS ) )
    constraint_S2 = constraint_avg( run( positional_engine(2, seed), TICKS ) )
assert mean(constraint_S2) > mean(constraint_S1) + 0.04
```

*Measured: S1 ≈ 0.46, S2 ≈ 0.54 — gap ≈ 0.08, driven by the economic axis
(party→x correlation rises ~0.84 → ~0.99 once `PartyPull` engages). The 0.04
margin clears it; re-confirm at the test's `N` (§8).*

### test_s3_partisan_media_pushes_heavy_consumers_out

The **paired** test (D5). For each seed, S2 and S3 are built from the *same*
seed, so they hold the identical population — same agents, same media diets,
same origins. The per-agent radial gap between the two runs isolates exactly
what `MediaConsumption` did.

```
for seed in STAGE_SEEDS:
    eng2 = run( positional_engine(2, seed), TICKS )
    eng3 = run( positional_engine(3, seed), TICKS )
    radius2 = [ norm(a.state.ideology) for a in eng2.agents ]
    radius3 = [ norm(a.state.ideology) for a in eng3.agents ]
    media_effect = radius3 - radius2                      # per agent
    extremity    = [ diet_extremity(a) for a in eng3.agents ]
    corr[seed]   = pearson(extremity, media_effect)
assert mean(corr) > 0.5
```

*Measured: corr ≈ 0.75, every seed in 0.71–0.79. The 0.5 threshold has wide
margin. This is non-circular: it asks whether the agents `MediaConsumption`
pushed outward are the ones with partisan diets — a yes/no the parameters
cannot quietly tune away.*

All three tests use `positional_engine` (D6), so they run at the speed of the
Phase 1 S1 test. Reuse whatever shared-ensemble fixture the Phase 1 runtime
fix introduced — the S2/S3 ensembles should be computed once and cached.

---

## 6. Calibration flag — decided: keep as-is for now

A real finding from the measurement. **Decision (recorded): keep S3 as
specified for now; revisit via ad-hoc tuning later.** The detail below stands
as the rationale and the to-do for that later pass.

The validated S3 claim — **heavy media consumers end up more extreme than
light ones** — holds robustly (§5, corr 0.75). But the *aggregate* effect is
the opposite of `pillar_spec.md`'s wording "party clusters separate faster."
Measured party separation: **S2 ≈ 1.00 → S3 ≈ 0.57** — adding partisan media
pulls the two camps *closer together*.

Why: `MediaConsumption` pulls each agent toward `diet_target`, the
weighted-mean position of its outlets. With the current `US_MEDIA_OUTLETS_2024`
roster and the `diet_for_party` generator (every diet includes centrist Local
TV, soft exponential falloff), those diet targets sit *inward* of the party
centres at x = ±0.5. So on average media is a mild *centering* force here.

Both things are true at once: media widens the gap *between* heavy and light
consumers while nudging the *average* inward. The first is the Levendusky
finding and is what the test checks. The second contradicts the "separates the
parties" narrative.

**What this means for Phase 2.** Nothing changes — the S3 bundle and the §5
validation test stand as written. The paired correlation test measures the
heavy-vs-light differential, which holds regardless of calibration, so the
test passes either way and Phase 2 implementation is unblocked.

**The one carry-forward.** S3's *validated* claim is the differential one:
"heavy partisan-media consumers drift further from centre than light ones."
S3 must not be described as "separating the parties" — with the current
numbers it does not. When S3 copy is written (UI phase), use the differential
wording.

**Deferred to ad-hoc tuning later.** Making the aggregate also polarize is a
small recalibration — sharpen `diet_for_party`'s falloff, cut the Local TV
weight, push outlet positions more extreme, or raise
`MediaConsumption.strength`. Not needed for Phase 2; revisit when convenient.

---

## 7. G8 cleanup (in scope)

`PartisanMediaExposure` (`abm/rules/partisan_media.py`) is dead — superseded by
`MediaConsumption`, and a repository search finds zero references outside its
own definition. Delete the file and remove its import/export from
`abm/rules/__init__.py`. Confirm `python -c "import abm.rules"` and the five
existing scenarios still import.

The other half of G8 — the `epsilon` slider double-mapping in
`scenarios_meta.py` — touches only the legacy website scenarios, not the
pillar (pillar bundles address rule attributes directly). Defer it to whenever
the website is next worked on; it is out of Phase 2's engine-only scope.

---

## 8. How the thresholds were obtained

Measured by running the real superset engine with the S1/S2/S3 bundles
applied, uniform initial condition, 200 ticks:

- **S2 constraint:** `ideological_constraint` average — S1 ≈ 0.46, S2 ≈ 0.54
  (n = 120–140, 4 seeds). The economic-axis component drives it (~0.84 →
  ~0.99); the cultural-axis component stays near 0 and adds noise.
- **S3 paired correlation:** Pearson r between `diet_extremity` and
  `radius_S3 − radius_S2` — 0.715, 0.729, 0.787, 0.772 across four seeds
  (n = 90). Mean 0.75, very tight.
- **Party separation:** S2 ≈ 1.00, S3 ≈ 0.57 (§6).

These runs used small `n` because `AffectiveUpdate` at radius 1.5 is O(n²);
with D6's fast path the tests themselves run at full `N`. The implementer
should re-measure each threshold at the test `N` and confirm the margin
holds before committing — same discipline as `phase1_spec.md` §9. The S3
correlation was so stable across seeds it needs no adjustment; the S2 gap is
smaller, so confirm it explicitly.

---

## 9. Done checklist

- [ ] `S2_PARTY_IDENTITY`, `S3_PARTISAN_MEDIA` added; `PILLAR.interventions`
      has four stages.
- [ ] Three new tests pass: positional-inertness, S2 constraint, S3 paired
      correlation.
- [ ] Test thresholds re-measured at the test `N`; margins confirmed.
- [ ] `pytest` green across the whole suite (Phase 1 tests still pass).
- [ ] `partisan_media.py` deleted; `abm.rules` and the five scenarios still
      import.
- [ ] `show_pillar.py` shows four stages with no edit (sanity check:
      `python scripts/show_pillar.py` and `--mode journey`).
- [ ] §6 calibration decision recorded — S3's narrative matches what the
      engine actually does.
- [ ] No UI/website file touched.
