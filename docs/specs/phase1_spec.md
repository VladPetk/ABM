# Phase 1 Implementation Spec — Pillar Engine, Thin Vertical Slice

*Companion to `pillar_engine_roadmap.md` (§6 Phase 1) and `pillar_spec.md`.
This document pins every decision an implementer would otherwise have to
guess, so Phase 1 can be executed without inventing consequential choices.
Every numeric threshold below was measured against the existing engine, not
estimated — see §9.*

**Phase 1 scope:** build the complete pillar scaffold (the `Intervention` and
`Pillar` types, the superset population + pipeline, `apply_intervention`, the
`pytest` harness) and run only stages **S0 and S1** through it. S2–S4 are
Phase 2/3 and must require *no* change to the scaffold — only new
`Intervention` objects and new tests.

---

## 1. Decisions pinned (the ten-minute review)

| # | Decision | Value | Note |
|---|----------|-------|------|
| D1 | Initial condition | `ideology ~ Uniform(-1, 1)²` per agent | **Supersedes `pillar_spec.md`'s "near the centre" wording** — uniform matches every existing scenario and is required for HK phase behavior to be visible. Confirm (§10). |
| D2 | Population size | `n_agents = 400` for tests; builder accepts any `n` | Variance is intensive — `n` does not shift thresholds; 400 keeps the suite fast. |
| D3 | Run length for stage tests | `200` ticks | Engine settles well before 200 (observed). |
| D4 | Ensemble | seeds `0..11` (12 seeds) for stage tests; `0..5` for the canonical HK sweep | ≥10 per roadmap; HK loose is O(n²), so fewer seeds + smaller `n` there. |
| D5 | `param_bundle` semantics | **absolute** (a full assignment of every tunable), not a diff | Applying any stage's bundle fully determines the world; order-independent, idempotent. |
| D6 | Rule addressing | by class name; pipeline holds **at most one instance per class** (builder asserts this) | Matches existing `apply_param`; the assertion catches future violations. |
| D7 | `apply_intervention` on a missing rule/attr | **raise** | Unlike `apply_param`, which silently returns `False`. Fail loud. |
| D8 | Validation style | directional inequalities with empirical margins (§8) | Per roadmap R3. |

---

## 2. Files to create

```
abm/pillars/__init__.py          # exports Pillar, Intervention, apply_intervention, PILLAR
abm/pillars/intervention.py      # Intervention type + apply_intervention
abm/pillars/pillar.py            # Pillar type + build_at_stage helper
abm/pillars/calm_to_camps.py     # THE pillar: superset builder + S0/S1 interventions
tests/conftest.py                # shared constants + ensemble helpers
tests/test_pillar_stages.py      # S0, S1 stage tests
tests/test_canonical.py          # Hegselmann-Krause replication
tests/test_machinery.py          # determinism, idempotence, live-mode smoke
```

Add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

Install dev deps: `pip install -e ".[dev]"` (pytest is already declared).

---

## 3. The `Intervention` type — exact

```python
# abm/pillars/intervention.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional

# One parameter change: (rule class name, attribute name, value).
ParamChange = tuple[str, str, float]

@dataclass(frozen=True)
class Intervention:
    id: str                                  # stable, e.g. "S1_bounded_confidence"
    label: str                               # human name, e.g. "Bounded confidence"
    description: str                         # one plain-English sentence
    param_bundle: tuple[ParamChange, ...]    # ABSOLUTE — a full assignment (D5)
    label_kind: str = "illustrative"         # "control" | "replication" | "illustrative"
    citation: str = ""
    predicted_effect: str = ""
    setup: Optional[Callable] = None         # structural change; None for S0–S3
```

`apply_intervention` — raises on any mismatch (D7):

```python
def apply_intervention(engine, intervention: Intervention) -> None:
    by_class: dict[str, object] = {}
    for rule in list(engine.rules.rules) + list(engine.env_rules):
        name = type(rule).__name__
        if name in by_class:                                  # D6
            raise ValueError(f"pipeline has two {name} instances")
        by_class[name] = rule
    for cls_name, attr, value in intervention.param_bundle:
        rule = by_class.get(cls_name)
        if rule is None:
            raise KeyError(f"{intervention.id}: no {cls_name} in pipeline")
        if not hasattr(rule, attr):
            raise AttributeError(f"{intervention.id}: {cls_name}.{attr} missing")
        setattr(rule, attr, value)
    if intervention.setup is not None:
        intervention.setup(engine)
```

---

## 4. The `Pillar` type — exact

```python
# abm/pillars/pillar.py
from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class Pillar:
    id: str
    title: str
    build_engine: Callable[[int], "Engine"]    # seed -> fresh superset engine (all forces off)
    interventions: tuple[Intervention, ...]    # ordered: S0, S1, ...

def build_at_stage(pillar: Pillar, stage_index: int, seed: int) -> "Engine":
    """Cold mode: fresh engine with stage `stage_index`'s cumulative bundle
    applied. NOT stepped — caller runs it."""
    engine = pillar.build_engine(seed)
    apply_intervention(engine, pillar.interventions[stage_index])
    return engine
```

---

## 5. The superset population & pipeline (`calm_to_camps.py`)

`build_engine(seed)` constructs the **full** superset population, env, and
pipeline — even though Phase 1 only exercises S0/S1 — so Phase 2 needs no
builder change. This is essentially `abm/scenarios/elite_dynamics.py`'s
construction with the hard-wired rule strengths set to zero. **Reuse that
code as the template.**

**Population** — `n_agents` agents (default 400), one shared
`rng = np.random.default_rng(seed)` for both positions and the engine:

| Attribute | Value |
|-----------|-------|
| `ideology` | `rng.uniform(-1, 1, size=2)` (D1) |
| `party` | `0 if ideology[0] < 0 else 1` |
| `identity_strength` | `rng.beta(2, 2)` |
| `identities` | `clip(c + rng.normal(0, 0.3, size=3), -1, 1)`, `c = -0.3·𝟙` (party 0) / `+0.3·𝟙` (party 1) |
| `affect` | `{1 - party: 0.0}` |
| `media_diet` | `diet_for_party(PARTY_CENTERS[party], outlets, rng)` — reuse `abm/core/outlets.py` |
| `cohort` | `"all"` (subset tag for future targeting) |
| `group` | `= party` |
| `origin` | `ideology.copy()` |

(Network `ties` are **not** built in Phase 1 — they belong to the Phase 3
exposure provider.)

**Environment:** `parties = {0: [-0.5, 0.0], 1: [0.5, 0.0]}`,
`outlets = {o.id: o for o in US_MEDIA_OUTLETS_2024}`, plus a `viz` dict
(copy the pattern from `elite_dynamics.py`).

**Pipeline** — every rule constructed once, all forces off (this *is* the S0
baseline state). Builder asserts one instance per class (D6):

| Rule | Constructed as | Type |
|------|----------------|------|
| `BoundedConfidenceInfluence` | `(epsilon=0.30, strength=0.0)` | agent |
| `PartyPull` | `(strength=0.0)` | agent |
| `MediaConsumption` | `(strength=0.0)` | agent |
| `AffectiveUpdate` | `(radius=1.5, learning_rate=0.0, identity_weight=0.5)` | agent |
| `IdentitySorting` | `(sort_rate=0.0, step=0.05, differentiation=0.5)` | agent |
| `GaussianNoise` | `(sigma=0.01)` | agent |
| `EliteDrift` | `(rate=0.0)` | env |

Agent-rule order is irrelevant (the engine sums deltas); put `GaussianNoise`
last by convention. `BacklashRepulsion` and `MediaShock` are **not** in the
pillar pipeline.

> **Attribute-name gotcha:** `AffectiveUpdate`'s constructor parameter is
> `learning_rate`, but it is stored as `self.lr`. Bundles must address it as
> `("AffectiveUpdate", "lr", ...)`.

---

## 6. The S0 and S1 interventions — exact bundles

Bundles are absolute (D5): each lists *every* tunable.

**S0 — Baseline** (`label_kind="control"`):

```python
param_bundle = (
    ("GaussianNoise", "sigma", 0.01),
    ("BoundedConfidenceInfluence", "strength", 0.0),
    ("PartyPull", "strength", 0.0),
    ("MediaConsumption", "strength", 0.0),
    ("AffectiveUpdate", "lr", 0.0),
    ("IdentitySorting", "sort_rate", 0.0),
    ("EliteDrift", "rate", 0.0),
)
```

**S1 — Bounded confidence** (`label_kind="replication"`,
`citation="Hegselmann & Krause 2002; Deffuant et al. 2000"`): identical to S0
plus the bounded-confidence force on:

```python
param_bundle = (
    ("GaussianNoise", "sigma", 0.01),
    ("BoundedConfidenceInfluence", "epsilon", 0.30),
    ("BoundedConfidenceInfluence", "strength", 0.08),
    ("PartyPull", "strength", 0.0),
    ("MediaConsumption", "strength", 0.0),
    ("AffectiveUpdate", "lr", 0.0),
    ("IdentitySorting", "sort_rate", 0.0),
    ("EliteDrift", "rate", 0.0),
)
```

---

## 7. The tests — exact, with empirical thresholds

`tests/conftest.py` provides: `STAGE_SEEDS = range(12)`, `HK_SEEDS = range(6)`,
`N = 400`, `TICKS = 200`, and a helper `final_variance(engine, ticks)` that
runs the engine and returns `abm.metrics.polarization.variance` of the final
positions.

### test_pillar_stages.py

**S0 — nothing organized happens.** For each seed in `STAGE_SEEDS`: build at
S0, record variance at t=0, run `TICKS`, record variance at t=200.

```
assert  mean(|var200 - var0| / var0)  <  0.05
```

*Observed: ~0.00 (variance 0.664 → 0.664, seed sd 0.001).* A real
attraction/repulsion bug shifts variance ≥15%, so this catches it.

**S1 — bounded confidence pulls the society together.** Run the S0 and S1
ensembles (same seeds, `TICKS`):

```
assert  mean(var200 @ S1)  <  0.85 * mean(var200 @ S0)
```

*Observed: S1 0.533 vs S0 0.664 → ratio 0.80; worst single seed 0.82.* The
0.85 bar passes every seed today and fails if bounded confidence stops
converging.

### test_canonical.py — Hegselmann-Krause replication

Independent of the pillar: use `abm/scenarios/compass_basic.py` directly
(`n=200`, `noise=0.01`, `attraction=0.08`, `repulsion=0.0`, `HK_SEEDS`,
`TICKS`). This is the "well-known simulation behaves as expected" check.

```
loose (epsilon = 2.0):   assert mean(var200) < 0.05      # observed ~0.001 — one cluster
tight (epsilon = 0.15):  assert mean(var200) > 0.45      # observed ~0.64  — fragmented
monotonic:               assert var(eps=2.0) < var(eps=0.30) < var(eps=0.15)
```

### test_machinery.py

- **Determinism:** `build_at_stage(PILLAR, 1, seed=7)` run `TICKS`, done
  twice → `np.array_equal` of final positions.
- **Idempotence:** applying S1's bundle twice leaves identical rule
  attributes as applying it once.
- **Live-mode smoke:** build one engine, `apply_intervention(S0)`, run 50,
  `apply_intervention(S1)`, run 150 — completes without error and is
  deterministic across two runs at the same seed. (Live mode is *not*
  asserted equal to cold mode — the trajectories differ by design.)

---

## 8. Bundled cleanup (small, in-scope)

Fix **G6** while here: in `scripts/compare.py`, `run_elite_comparison` calls
`build_elite(..., partisan_media_strength=...)`, but `elite_dynamics.build`
has no such parameter. Rename both occurrences to `media_consumption_strength`
(or remove the argument — it defaults sensibly). Confirm `python
scripts/compare.py elite` then runs.

---

## 9. How the thresholds were obtained

Every number in §7 was measured by running the current engine
(`compass_basic`, which is exactly Hegselmann-Krause + Gaussian noise):
uniform initial condition, `noise=0.01`, 200 ticks, 6 seeds. S0 used
`attraction=0.0`; S1 used `attraction=0.08, epsilon=0.30`. They are
reproducible facts about the engine as it stands, not targets invented to be
hit — so a test written to them is not circular.

---

## 10. Done checklist (matches roadmap §6 Phase 1)

- [ ] `abm/pillars/` package with `Intervention`, `Pillar`, `apply_intervention`.
- [ ] `calm_to_camps.PILLAR` — superset population + pipeline + S0/S1 interventions.
- [ ] `tests/` runs under `pytest`; all tests in §7 green.
- [ ] Determinism, idempotence, live-mode smoke pass.
- [ ] HK canonical replication passes.
- [ ] `scripts/compare.py elite` no longer errors (G6).
- [ ] No UI / website file touched; the existing 5 scenarios still import and run.

**One item needs your confirmation before coding:** decision **D1** — the
pillar population starts *uniform* on [-1, 1]², which supersedes
`pillar_spec.md`'s "near the centre" phrasing. Uniform is required for the HK
phase behavior to be visible and matches every existing scenario. Say the word
and I align `pillar_spec.md`; or if you want a near-centre start, the S1
threshold in §7 must be re-measured.
