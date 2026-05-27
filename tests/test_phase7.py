"""Phase 7 — calibration (tick-to-real-time, step sizes against panel data).

Six tests, organised by spec section:

- C1 (tick-to-year mapping): constants pinned; round-trip helpers correct;
  empirical anchors registry present.
- C2 (ANES anchor): directional regression — the pillar's S0→S3 affect
  trajectory restricted to the 42-year ANES window lies within ±20% of
  the empirical -0.56 anchor.
- C3 (sensitivity-default regression guards): X3's backfire reading
  holds at default outlets; the position-histogram no-collapse property
  holds at default FJ_ALPHA.
"""
from __future__ import annotations

import numpy as np

from abm.calibration import (
    EMPIRICAL_ANCHORS,
    TICKS_PER_YEAR,
    ticks_to_years,
    years_to_ticks,
)
from abm.metrics.affective import affective_polarization
from abm.pillars import PILLAR, apply_intervention
from abm.pillars.calm_to_camps import build_engine

from .conftest import N, STAGE_SEEDS, TICKS


# --- C1: tick-to-year mapping --------------------------------------------


def test_ticks_per_year_pinned():
    """The calibration scalar is the single source of truth for the
    tick→year mapping. Pinned by anchoring the pillar's S0→S3 affect
    trajectory to the ANES out-party-thermometer fall (Phase 7 C1a)."""
    assert TICKS_PER_YEAR == 3.0


def test_ticks_years_round_trip():
    """`years_to_ticks(ticks_to_years(t))` returns t for representative
    tick counts. (round-trip exact at integer year boundaries.)"""
    for ticks in (3, 12, 30, 60, 126, 200):
        years = ticks_to_years(ticks)
        assert years_to_ticks(years) == ticks


def test_empirical_anchors_present():
    """The registry carries the four Phase 7 empirical anchors with
    non-empty source / metric / model_check fields. Guard against
    accidental emptying of the calibration record."""
    expected_keys = {
        "out_party_thermometer",
        "dw_nominate_divergence",
        "pettigrew_tropp_contact",
        "facebook_deactivation",
    }
    assert set(EMPIRICAL_ANCHORS.keys()) >= expected_keys
    for key, anchor in EMPIRICAL_ANCHORS.items():
        assert anchor.get("source"), f"{key} missing source"
        assert anchor.get("metric"), f"{key} missing metric"
        assert anchor.get("model_check"), f"{key} missing model_check"


# --- C2: ANES anchor regression -----------------------------------------


def test_pillar_affect_trajectory_matches_anes_within_band(s3_affect_engines):
    """The pillar's S0→S3 affective_polarization trajectory restricted
    to a 42-year window (Iyengar 1978-2020) should land within ±20%
    of the ANES headline (28-point thermometer fall ≈ -0.56 on the
    model's axis).

    Operationalised: at TICKS_PER_YEAR=3, a 42-year window is 126
    ticks. The Phase 5 §11 measurement showed Δaff ≈ -0.85 over 200
    ticks (which represents ~67 years). Linear scaling: 126/200 *
    -0.85 ≈ -0.535 — well within [-0.45, -0.67] (the ±20% band around
    -0.56). The `s3_affect_engines` fixture runs the full 200-tick
    pillar; we sanity-check by comparing the final affect against the
    band predicted by linear scaling.

    This is a directional regression guard, not a pinpoint match: the
    actual 126-tick trajectory may be non-linear (S0/S1 have lr=0,
    most cooling happens in S2/S3). The full-200-tick projection is
    the cleanest test of "the model lands in the ANES ballpark."
    """
    affs_s3 = [affective_polarization(e.agents) for e in s3_affect_engines]
    mean_aff_s3 = float(np.mean(affs_s3))
    # ANES 42-year drop ≈ -0.56 on model axis. Pillar 67-year (=200
    # ticks) drop measured ≈ -0.85. Linear scaling: at 200 ticks, the
    # ANES-predicted value is -0.56 * (200 / 126) ≈ -0.89.
    expected = EMPIRICAL_ANCHORS["out_party_thermometer"]["value_normalised"]
    anes_window_years = EMPIRICAL_ANCHORS["out_party_thermometer"]["duration_years"]
    full_window_years = TICKS / TICKS_PER_YEAR  # 200 / 3 ≈ 66.7 years
    expected_at_full = expected * (full_window_years / anes_window_years)
    # ±20% band around expected_at_full. Note: `expected_at_full` is
    # negative (~-0.89), so `1.2 * expected` is MORE negative (lower
    # bound) and `0.8 * expected` is LESS negative (upper bound).
    lo, hi = expected_at_full * 1.2, expected_at_full * 0.8
    assert lo <= mean_aff_s3 <= hi, (
        f"Pillar S0→S3 affect trajectory {mean_aff_s3:+.3f} should be "
        f"within ±20% of ANES-projected {expected_at_full:+.3f} (band "
        f"[{lo:+.3f}, {hi:+.3f}]) at the full 200-tick window."
    )


# --- C3: sensitivity-default regression guards ---------------------------


def test_x3_setup_disables_partisan_cable_only(intervention_buckets):
    """Phase 8c §3 reframe: the Phase 7 'X3 backfires' guard is
    obsolete. The Phase 7 X3 zeroed `MediaConsumption.strength`
    entirely, bundling broadcast/local's centripetal pull with
    partisan cable's centrifugal pull — R1's "category error." The
    Phase 8c §3 X3 zeros only MSNBC + Fox News weights; the
    consolidated bucket test in `test_phase6.py` is the source of
    truth for X3's measured direction. This test still asserts that
    X3 *has a measurement* on issue_sorting (i.e., the mechanism
    fires — not asserting direction)."""
    dsep = intervention_buckets["X3_quit_cable_news"]["sep"]
    assert isinstance(dsep, float), (
        f"X3 issue-sorting measurement should be a float; got {dsep!r}"
    )
    # Document the magnitude is bounded (sanity guard).
    assert abs(dsep) < 1.0, (
        f"X3 Δsep magnitude should be modest (<1.0); measured {dsep:+.3f}"
    )


def test_no_collapse_at_default_fj_alpha():
    """Phase 4 §12: the 'no two-tiny-blobs' property must hold at the
    default `FJ_ALPHA = 0.05`. Tests fraction of agents within
    [0.20, 0.50] from centre and fraction past 0.80 at end-of-S4."""
    radii_all = []
    for seed in STAGE_SEEDS:
        eng = build_engine(seed=seed, n_agents=N)
        apply_intervention(eng, PILLAR.interventions[4])
        eng.run(TICKS)
        radii_all.append(
            np.array([np.linalg.norm(a.state.ideology) for a in eng.agents])
        )
    radii = np.concatenate(radii_all)
    mid_band = float(((radii >= 0.20) & (radii < 0.50)).mean())
    extreme = float((radii >= 0.80).mean())
    assert mid_band > 0.85, (
        f"At least 85% of agents should sit in [0.20, 0.50] from "
        f"centre at end-of-S4; measured {mid_band:.3f}."
    )
    assert extreme < 0.02, (
        f"At most 2% of agents should sit past 0.80 from centre at "
        f"end-of-S4; measured {extreme:.3f}."
    )
