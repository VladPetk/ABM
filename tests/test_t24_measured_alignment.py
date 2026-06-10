"""MHV S2 T2.4 — measured identity alignment (M3-light) guards.

Pins: the EXACT measured-alignment formula (recomputed independently from
the frozen loadings file, per the spec's "exact formula fixed in execution,
pinned by test"), the rule's measured-minus-current delta semantics and
no-op gates, the tick-0 seeding consistency, the emergent rise over the
arc, the M3-light pipeline surgery (MeasuredAlignment in / IdentityAlignment
out / AffectiveUpdate.identity_weight 0.0), the cohort-replacement reseed
consistency, the IDENTITY_ALIGNMENT shock guard, the X1 identity-lever
skip, and the untouched legacy path.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pytest

from abm.core.issues import build_runtime, load_loadings, LOADINGS_PATH
from abm.core.state import StateDelta
from abm.rules.measured_alignment import MeasuredAlignment, measure_alignment


class _Env:
    def __init__(self, attrs):
        self.attrs = attrs


class _Stub:
    def __init__(self, attrs):
        self.state = type("st", (), {})()
        self.state.attrs = attrs


# --------------------------------------------------------------------------
# formula + pure-rule guards
# --------------------------------------------------------------------------

def test_formula_pinned_against_raw_loadings():
    """Recompute the formula independently from the committed JSON —
    geometric mean of identity stacking and the projection of the issue
    vector onto the FROZEN 1986 party-gap axis (midpoint-centred)."""
    with open(LOADINGS_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    dem = np.array(raw["party_conditional"]["dem"]["item_means"], float)
    rep = np.array(raw["party_conditional"]["rep"]["item_means"], float)
    gap = rep - dem
    u = gap / np.linalg.norm(gap)
    m = (rep + dem) / 2.0

    rt = build_runtime(load_loadings())
    rng = np.random.default_rng(7)
    centers = {0: np.array([-0.2, -0.2, -0.2]), 1: np.array([0.2, 0.2, 0.2])}
    for party in (0, 1):
        for _ in range(20):
            ids = rng.uniform(-1, 1, 3)
            v = rng.uniform(-1, 1, 7)
            p = 1.0 if party == 1 else -1.0
            id_stack = float(np.clip(p * ids.mean(), 0.0, 1.0))
            issue_stack = float(np.clip(p * float((v - m) @ u), 0.0, 1.0))
            expect = float(np.sqrt(id_stack * issue_stack))
            got = measure_alignment(ids, party, v, centers, rt)
            assert got == pytest.approx(expect, abs=1e-12)
            assert 0.0 <= got <= 1.0


def test_rule_emits_measured_minus_current():
    rt = build_runtime(load_loadings())
    env = _Env({"issue_runtime": rt,
                "party_identity_centers": {0: np.array([-0.2] * 3),
                                           1: np.array([0.2] * 3)}})
    ids = np.array([0.5, 0.3, 0.4])
    v = np.linspace(-0.6, 0.6, 7)
    a = _Stub({"party": 1, "identities": ids, "issues": v,
               "identity_alignment": 0.30})
    rng = np.random.default_rng(0)
    s0 = rng.bit_generator.state
    d = MeasuredAlignment().apply(a, None, env, rng)
    measured = measure_alignment(ids, 1, v, env.attrs["party_identity_centers"], rt)
    assert d.d_attrs["identity_alignment"] == pytest.approx(measured - 0.30)
    assert rng.bit_generator.state == s0       # measurement never draws rng


def test_noop_gates():
    rt7 = build_runtime(load_loadings())
    rng = np.random.default_rng(0)
    a = _Stub({"party": 1, "identities": np.ones(3),
               "issues": np.zeros(7), "identity_alignment": 0.2})
    # no runtime → legacy path → no-op
    d = MeasuredAlignment().apply(a, None, _Env({}), rng)
    assert isinstance(d, StateDelta) and not d.d_attrs
    # D=2 identity loadings → degenerate party gap → readout off
    from abm.core.issues import identity_loadings_2d
    rt2 = build_runtime(identity_loadings_2d())
    assert rt2["align_u"] is None
    a2 = _Stub({"party": 1, "identities": np.ones(3),
                "issues": np.zeros(2)})
    d = MeasuredAlignment().apply(a2, None, _Env({"issue_runtime": rt2}), rng)
    assert not d.d_attrs
    # Independents carry no alignment
    a3 = _Stub({"party": 2, "identities": np.ones(3), "issues": np.zeros(7)})
    d = MeasuredAlignment().apply(a3, None, _Env({"issue_runtime": rt7}), rng)
    assert not d.d_attrs


# --------------------------------------------------------------------------
# engine-level guards
# --------------------------------------------------------------------------

def _emergent_engine(seed=0, **kw):
    from abm.pillars.historical_arc import build_engine
    return build_engine(seed=seed, n_issues=7, constraint_rate=0.02,
                        constraint_resid_sigma=0.01, evidence_regrade=True,
                        **kw)


def test_seed_is_measured_at_tick0():
    eng = _emergent_engine()
    rt = eng.env.attrs["issue_runtime"]
    centers = eng.env.attrs["party_identity_centers"]
    n_part = 0
    for a in eng.agents:
        party = a.state.attrs.get("party")
        if party in (0, 1):
            n_part += 1
            expect = measure_alignment(
                a.state.attrs["identities"], party,
                a.state.attrs["issues"], centers, rt)
            assert a.state.attrs["identity_alignment"] == pytest.approx(
                expect, abs=1e-12)
        else:
            assert "identity_alignment" not in a.state.attrs
    assert n_part > 100


def test_alignment_rises_over_emergent_arc():
    from abm.pillars.historical_arc import build_schedule
    from abm.pillars.schedule import run_to

    eng = _emergent_engine()

    def _mean_align(e):
        vals = [a.state.attrs["identity_alignment"] for a in e.agents
                if a.state.attrs.get("party") in (0, 1)
                and "identity_alignment" in a.state.attrs]
        return float(np.mean(vals))

    a0 = _mean_align(eng)
    run_to(eng, build_schedule(evidence_regrade=True), 90)
    a90 = _mean_align(eng)
    assert a90 > a0 + 0.02      # the readout rises through real sorting
    for a in eng.agents:
        if "identity_alignment" in a.state.attrs:
            assert 0.0 <= a.state.attrs["identity_alignment"] <= 1.0


def test_pipeline_surgery_m3_light():
    eng = _emergent_engine()
    names = [type(r).__name__ for r in eng.rules.rules]
    assert "MeasuredAlignment" in names
    assert "IdentityAlignment" not in names
    assert "IdentitySorting" not in names
    affect = next(r for r in eng.rules.rules
                  if type(r).__name__ == "AffectiveUpdate")
    assert affect.identity_weight == 0.0


def test_legacy_path_unchanged():
    from abm.pillars.historical_arc import build_engine

    eng = build_engine(seed=0, evidence_regrade=True)
    names = [type(r).__name__ for r in eng.rules.rules]
    assert "IdentityAlignment" in names
    assert "MeasuredAlignment" not in names
    affect = next(r for r in eng.rules.rules
                  if type(r).__name__ == "AffectiveUpdate")
    assert affect.identity_weight == 0.5


def test_replacement_reseed_is_measured():
    from abm.rules.cohort_replacement import CohortReplacement

    eng = _emergent_engine()
    rt = eng.env.attrs["issue_runtime"]
    centers = eng.env.attrs["party_identity_centers"]
    pre_ids = {a.id: a.state.attrs["identities"].copy() for a in eng.agents}
    CohortReplacement(replacement_rate=1.0).apply(
        eng.env, eng.agents, eng.space, eng.rng, tick=60)
    replaced = [a for a in eng.agents
                if not np.array_equal(a.state.attrs["identities"],
                                      pre_ids[a.id])]
    assert len(replaced) > 50
    checked = 0
    for a in replaced:
        party = a.state.attrs.get("party")
        if party not in (0, 1):
            continue
        expect = measure_alignment(
            a.state.attrs["identities"], party,
            a.state.attrs["issues"], centers, rt)
        assert a.state.attrs["identity_alignment"] == pytest.approx(
            expect, abs=1e-12)
        checked += 1
    assert checked > 50


def test_identity_alignment_shock_guard():
    from abm.pillars.shocks import (Direction, Persistence,
                                    PopulationSelector, ShockSpec,
                                    TargetState, make_shock_event)

    spec = ShockSpec(
        label="test_align_shock", description="t", actual_date="2000-01",
        kind="test", onset_tick=0,
        target_state=TargetState.IDENTITY_ALIGNMENT,
        direction=Direction.DIVERGENCE, magnitude=0.1,
        population=PopulationSelector.all(),
        persistence=Persistence.TRANSIENT,
        evidence_grade="LOW", evidence_source="t", evidence_note="t",
        decay_rate=0.1,
    )
    fn = make_shock_event(spec)
    with pytest.raises(ValueError, match="measured readout"):
        fn(_emergent_engine(exogenous_shocks=True))
    # legacy path: same shock applies fine
    from abm.pillars.historical_arc import build_engine
    fn(build_engine(seed=0, evidence_regrade=True, exogenous_shocks=True))


def test_x1_identity_lever_skipped_emergent():
    from abm.pillars.interventions_phase6 import _x1_setup

    eng = _emergent_engine()
    _x1_setup(eng)
    affect = next(r for r in eng.rules.rules
                  if type(r).__name__ == "AffectiveUpdate")
    assert affect.identity_weight == 0.0       # retired coupling stays retired
    backlash = next(r for r in eng.rules.rules
                    if type(r).__name__ == "BacklashRepulsion")
    assert backlash.strength > 0.0             # the core X1 mechanism still fires

    from abm.pillars.historical_arc import build_engine
    leg = build_engine(seed=0, evidence_regrade=True)
    _x1_setup(leg)
    affect_l = next(r for r in leg.rules.rules
                    if type(r).__name__ == "AffectiveUpdate")
    assert affect_l.identity_weight == 0.6
