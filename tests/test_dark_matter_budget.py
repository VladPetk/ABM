"""MHV S2 — dark-matter budget gates (mhv_spec §6, adopted at S2 sign-off).

The budgets bound how much of the shipped 1980→2025 arc may be carried by
hand-drawn machinery rather than rule interaction. Floors (fraction of the
baseline change that survives the all-frozen-no-events counterfactual —
every category-C schedule clamped at its 1980 value, every dated event
removed; the phase-2 freeze instrument's protocol, run on the canonical
shipped preset):

    party separation        ≥ 0.60
    affective polarization  ≥ 0.60
    identity alignment      ≥ 0.50  (PRE-REGISTERED ratchet to ≥ 0.60
                                     after the S4 fit — move the floor
                                     in this file at S4, nowhere else)

Derivation (s2_spec.md §10): sep/affect floors are today-minus-freeze-CI
anti-regression bounds; the alignment floor is the S2 co-dominance bar
(3× the legacy 17% schedule-carried reading). Escape hatch: an S4
holdout-validated fit that genuinely demands more schedule-carried change
is a finding — floors may be lowered OPENLY in methods.md with reasoning,
never silently here.

Measured at the T2.6 canonical flip (8 seeds, phase2_freeze.json):
sep 1.10 / affect 0.87 / alignment 1.07 — the emergent core now carries
the arc; the residual schedule levers are elite drift (~30% of sep) and
the social-media ramp (~21% of affect), which S3's typed-inputs caps
(≤0.15 / ≤0.15 / ≤0.10) exist to retire.
"""
from __future__ import annotations

import numpy as np
import pytest

from abm.calibration_parallel import run_seeds_parallel

SEEDS = tuple(range(6))
ALL_FREEZE = ("elite_drift", "identity_sorting", "coupling",
              "party_k", "social_media")

FLOORS = {
    "party_sep": 0.60,
    "affect": 0.60,
    "identity_alignment": 0.50,   # S4 ratchet: 0.60 (pre-registered)
}


@pytest.fixture(scope="module")
def budget_fractions() -> dict[str, float]:
    """Fraction of the baseline 1980→2025 change that survives the
    all-frozen-no-events counterfactual, per metric (ensemble means,
    the phase2_freeze computation)."""
    from scripts.audit.audit_lib import freeze_worker

    work = ([(s, (), "full") for s in SEEDS]
            + [(s, ALL_FREEZE, "empty") for s in SEEDS])
    flat = run_seeds_parallel(freeze_worker, work)
    base_runs = flat[: len(SEEDS)]
    frozen_runs = flat[len(SEEDS):]

    out: dict[str, float] = {}
    for m in FLOORS:
        b0 = float(np.mean([r["series"][0][m] for r in base_runs]))
        b1 = float(np.mean([r["series"][-1][m] for r in base_runs]))
        f1 = float(np.mean([r["series"][-1][m] for r in frozen_runs]))
        full_rise = b1 - b0
        assert abs(full_rise) > 1e-6, (
            f"baseline {m} did not move over the arc ({b0:.4f} -> {b1:.4f}) "
            "— the budget fraction is undefined; investigate before "
            "touching the floors."
        )
        out[m] = (f1 - b0) / full_rise
    return out


@pytest.mark.parametrize("metric", sorted(FLOORS))
def test_dark_matter_floor(budget_fractions, metric):
    frac = budget_fractions[metric]
    assert frac >= FLOORS[metric], (
        f"{metric}: only {frac:.2f} of the 1980->2025 change survives the "
        f"all-frozen-no-events counterfactual (floor {FLOORS[metric]:.2f}) "
        "— the arc is leaning on hand-drawn schedules beyond the adopted "
        "budget (mhv_spec §6). If an S4 holdout-validated fit genuinely "
        "demands this, lower the floor OPENLY in methods.md with "
        "reasoning; never silently here."
    )
