"""MHV S3 T3.3 — data-fed media channel.

Guards the MediaPenetrationSeries consumer (the penetration → coupling map)
and the gated wiring (default off → bit-identical; on → the rules read the
env slots). Coupling magnitudes are checked against the values the discrete
step events used, so the re-expression is faithful.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from abm.pillars.inputs import (
    MEDIA_PENETRATION_SERIES_PATH,
    MediaPenetrationSeries,
    load_series,
)
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from scripts.anes_preset import ANES_FULL_KWARGS


@pytest.fixture(scope="module")
def media_series():
    return load_series(MEDIA_PENETRATION_SERIES_PATH)


def _apply_at(rule, year_tick):
    env = SimpleNamespace(attrs={})
    rule.apply(env, [], None, None, tick=year_tick)
    return env.attrs


def test_media_series_loads_with_provenance(media_series):
    assert media_series.meta["lne_tag"] in ("L", "N", "E")
    assert set(media_series.names) == {"social_media", "internet", "partisan_media"}


def test_partisan_media_reproduces_fd_fox_steps(media_series):
    rule = MediaPenetrationSeries(media_series)
    # 1987.6 (FD repeal) → partisan_media 0.5 → media_strength 0.04*0.5 = 0.02
    t_1987 = round((1987.6 - 1980) * 3)
    assert _apply_at(rule, t_1987)["media_strength"] == pytest.approx(0.02, abs=2e-3)
    # 1997+ (post Fox) → partisan_media 1.0 → media_strength 0.04
    t_1998 = round((1998 - 1980) * 3)
    assert _apply_at(rule, t_1998)["media_strength"] == pytest.approx(0.04, abs=1e-3)
    # pre-FD → 0
    assert _apply_at(rule, 0)["media_strength"] == pytest.approx(0.0)


def test_social_media_reproduces_regrade_ramp(media_series):
    rule = MediaPenetrationSeries(media_series)
    # The demoted evidence-regrade ramp was ~0.02 @2008 / ~0.04 @2010 / ~0.05 @2012.
    aw = lambda yr: _apply_at(rule, round((yr - 1980) * 3))["bc_affect_weight"]
    assert aw(2008) == pytest.approx(0.024, abs=8e-3)
    assert aw(2010) == pytest.approx(0.040, abs=8e-3)
    assert aw(2012) == pytest.approx(0.050, abs=8e-3)


def test_data_fed_media_off_is_bit_identical_env():
    # Default path must not introduce the env coupling slots.
    eng = build_engine(seed=0, **ANES_FULL_KWARGS)
    assert "media_strength" not in eng.env.attrs
    assert "bc_affect_weight" not in eng.env.attrs


def test_data_fed_media_on_sets_env_slots_and_rules_read_them():
    kwargs = dict(ANES_FULL_KWARGS)
    kwargs["data_fed_media"] = True
    eng = build_engine(seed=0, **kwargs)
    sched = build_schedule(faction_anchor_events=True, evidence_regrade=True,
                           exogenous_shocks=True)
    # Advance past Fox (1996, tick 48) and social-media onset (2008, tick 84).
    run_to(eng, sched, 90)
    assert eng.env.attrs["media_strength"] == pytest.approx(0.04, abs=1e-3)
    assert eng.env.attrs["bc_affect_weight"] > 0.0
