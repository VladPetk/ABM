"""MHV S3 / T3.1 — typed input-channel infrastructure (abm/pillars/inputs.py).

Isolation guards for the data-fed series loader + interpolation + the two
EnvRule consumers (generic env-attr writer and the party-centroid channel).
The real series files are exercised by T3.2 / T3.3; here we use synthetic
fixtures so the mechanism is pinned independently of the data.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np
import pytest

from abm.core.agent import Agent
from abm.core.state import AgentState
from abm.pillars.inputs import (
    DEFAULT_TICKS_PER_YEAR,
    EnvAttrSeries,
    PartyCentroidSeries,
    Series,
    load_series,
    tick_to_year,
)


# --- Series interpolation ------------------------------------------------

def test_series_linear_interp_and_endpoint_clamp():
    s = Series({"a": [[1980, 0.0], [2010, 3.0]]}, meta={})
    # midpoint
    assert s.at(1995)["a"] == pytest.approx(1.5)
    # endpoints
    assert s.at(1980)["a"] == pytest.approx(0.0)
    assert s.at(2010)["a"] == pytest.approx(3.0)
    # clamp outside the anchor range — no extrapolation past the envelope
    assert s.at(1900)["a"] == pytest.approx(0.0)
    assert s.at(2100)["a"] == pytest.approx(3.0)


def test_series_sorts_unsorted_anchors():
    s = Series({"a": [[2010, 3.0], [1980, 0.0]]}, meta={})
    assert s.at(1995)["a"] == pytest.approx(1.5)


def test_series_rejects_bad_channel_shape():
    with pytest.raises(ValueError):
        Series({"a": [1.0, 2.0, 3.0]}, meta={})  # not (k, 2)
    with pytest.raises(ValueError):
        Series({"a": np.zeros((0, 2))}, meta={})  # empty


# --- load_series + provenance discipline ---------------------------------

def _write(tmp_path, payload):
    p = tmp_path / "series.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def test_load_series_happy_path(tmp_path):
    p = _write(tmp_path, {
        "name": "demo", "unit": "x", "source": "y", "lne_tag": "L",
        "channels": {"a": [[1980, 0.0], [2010, 1.0]]},
    })
    s = load_series(p)
    assert s.names == ["a"]
    assert s.meta["lne_tag"] == "L"
    assert s.at(1995)["a"] == pytest.approx(0.5)


@pytest.mark.parametrize("payload", [
    {"unit": "x", "source": "y", "lne_tag": "L", "channels": {"a": [[0, 0]]}},  # no name
    {"name": "d", "unit": "x", "source": "y", "lne_tag": "Q",                    # bad tag
     "channels": {"a": [[0, 0]]}},
    {"name": "d", "unit": "x", "source": "y", "lne_tag": "L"},                   # no channels
])
def test_load_series_rejects_unprovenanced(tmp_path, payload):
    with pytest.raises(ValueError):
        load_series(_write(tmp_path, payload))


# --- tick → year ----------------------------------------------------------

def test_tick_to_year():
    assert tick_to_year(0) == pytest.approx(1980.0)
    assert tick_to_year(DEFAULT_TICKS_PER_YEAR) == pytest.approx(1981.0)
    assert tick_to_year(135) == pytest.approx(1980.0 + 135 / 3)  # 2025


# --- EnvAttrSeries --------------------------------------------------------

def test_env_attr_series_writes_interpolated_values():
    s = Series({"media": [[1980, 0.0], [2010, 0.30]]}, meta={})
    rule = EnvAttrSeries(s)
    env = SimpleNamespace(attrs={})
    # tick 45 → year 1995 → halfway → 0.15
    rule.apply(env, [], None, None, tick=45)
    assert env.attrs["media"] == pytest.approx(0.15)


def test_env_attr_series_rename():
    s = Series({"raw": [[1980, 1.0], [2010, 1.0]]}, meta={})
    rule = EnvAttrSeries(s, rename={"raw": "media_strength"})
    env = SimpleNamespace(attrs={})
    rule.apply(env, [], None, None, tick=0)
    assert env.attrs["media_strength"] == pytest.approx(1.0)
    assert "raw" not in env.attrs


# --- PartyCentroidSeries --------------------------------------------------

def _agent(aid, party, cue):
    return Agent(id=aid, state=AgentState(
        ideology=np.zeros(2),
        attrs={"party": party, "party_cue": np.asarray(cue, dtype=float)},
    ))


def test_party_centroid_series_sets_centroids_and_propagates_cue():
    s = Series({
        "p0_econ": [[1980, -0.10], [2010, -0.40]],
        "p0_cult": [[1980, 0.0], [2010, -0.40]],
        "p1_econ": [[1980, 0.20], [2010, 0.40]],
        "p1_cult": [[1980, 0.10], [2010, 0.30]],
    }, meta={})
    rule = PartyCentroidSeries(s)
    env = SimpleNamespace(attrs={"parties": {
        0: np.array([-0.10, 0.0]),
        1: np.array([0.20, 0.10]),
    }})
    a0 = _agent(0, 0, [-0.10, 0.0])
    a1 = _agent(1, 1, [0.20, 0.10])
    # tick 45 → 1995 → halfway between the 1980 and 2010 anchors
    rule.apply(env, [a0, a1], None, None, tick=45)
    np.testing.assert_allclose(env.attrs["parties"][0], [-0.25, -0.20])
    np.testing.assert_allclose(env.attrs["parties"][1], [0.30, 0.20])
    # cue shifted by exactly (new - old) party centroid
    np.testing.assert_allclose(a0.state.attrs["party_cue"], [-0.25, -0.20])
    np.testing.assert_allclose(a1.state.attrs["party_cue"], [0.30, 0.20])


def test_party_centroid_series_leaves_unlisted_party_alone():
    # Independents (party 2) have no centroid channel — must be untouched.
    s = Series({
        "p0_econ": [[1980, 0.0], [2010, 0.0]],
        "p0_cult": [[1980, 0.0], [2010, 0.0]],
    }, meta={})
    rule = PartyCentroidSeries(s)
    env = SimpleNamespace(attrs={"parties": {
        0: np.array([0.0, 0.0]),
        2: np.array([0.05, -0.05]),
    }})
    rule.apply(env, [], None, None, tick=10)
    np.testing.assert_allclose(env.attrs["parties"][2], [0.05, -0.05])


def test_party_centroid_series_clamps_to_domain():
    s = Series({
        "p1_econ": [[1980, 2.0], [2010, 2.0]],  # absurd — must clamp to +1
        "p1_cult": [[1980, 0.0], [2010, 0.0]],
    }, meta={})
    rule = PartyCentroidSeries(s)
    env = SimpleNamespace(attrs={"parties": {1: np.array([0.3, 0.0])}})
    rule.apply(env, [], None, None, tick=0)
    assert env.attrs["parties"][1][0] == pytest.approx(1.0)
