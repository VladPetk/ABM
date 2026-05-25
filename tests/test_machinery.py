"""Machinery tests — determinism, idempotence, live-mode smoke."""
from __future__ import annotations

import numpy as np

from abm.pillars import PILLAR, apply_intervention, build_at_stage
from abm.pillars.calm_to_camps import S0_BASELINE, S1_BOUNDED_CONFIDENCE, build_engine


def _final_positions(stage_index: int, seed: int, ticks: int = 50) -> np.ndarray:
    engine = build_at_stage(PILLAR, stage_index, seed)
    engine.run(ticks)
    return engine.positions()


def test_determinism():
    """Same pillar + same seed -> identical final positions."""
    a = _final_positions(stage_index=1, seed=7, ticks=50)
    b = _final_positions(stage_index=1, seed=7, ticks=50)
    assert np.array_equal(a, b)


def _rule_attrs_snapshot(engine) -> dict:
    """Snapshot every (rule class, attr) value addressable from a bundle."""
    snap: dict[tuple[str, str], float] = {}
    for rule in list(engine.rules.rules) + list(engine.env_rules):
        cls = type(rule).__name__
        for attr in vars(rule):
            v = getattr(rule, attr)
            if isinstance(v, (int, float)):
                snap[(cls, attr)] = float(v)
    return snap


def test_idempotence():
    """Applying S1's bundle twice == applying it once."""
    eng_once = build_engine(seed=3)
    apply_intervention(eng_once, S1_BOUNDED_CONFIDENCE)
    once = _rule_attrs_snapshot(eng_once)

    eng_twice = build_engine(seed=3)
    apply_intervention(eng_twice, S1_BOUNDED_CONFIDENCE)
    apply_intervention(eng_twice, S1_BOUNDED_CONFIDENCE)
    twice = _rule_attrs_snapshot(eng_twice)

    assert once == twice


def _live_run(seed: int) -> np.ndarray:
    eng = build_engine(seed=seed)
    apply_intervention(eng, S0_BASELINE)
    eng.run(50)
    apply_intervention(eng, S1_BOUNDED_CONFIDENCE)
    eng.run(150)
    return eng.positions()


def test_live_mode_smoke_and_determinism():
    """Live mode (apply -> run -> apply -> run) runs and is deterministic."""
    a = _live_run(seed=11)
    b = _live_run(seed=11)
    assert np.array_equal(a, b)


def test_apply_intervention_raises_on_missing_rule():
    """D7 — apply_intervention raises (does not silently no-op) on a missing rule."""
    from abm.pillars import Intervention

    bogus = Intervention(
        id="bogus",
        label="bogus",
        description="",
        param_bundle=(("DoesNotExist", "strength", 0.5),),
    )
    eng = build_engine(seed=0)
    try:
        apply_intervention(eng, bogus)
    except KeyError:
        return
    raise AssertionError("apply_intervention should have raised KeyError")


def test_apply_intervention_raises_on_missing_attr():
    """D7 — apply_intervention raises on missing attribute."""
    from abm.pillars import Intervention

    bogus = Intervention(
        id="bogus_attr",
        label="bogus_attr",
        description="",
        param_bundle=(("GaussianNoise", "no_such_attr", 0.5),),
    )
    eng = build_engine(seed=0)
    try:
        apply_intervention(eng, bogus)
    except AttributeError:
        return
    raise AssertionError("apply_intervention should have raised AttributeError")
