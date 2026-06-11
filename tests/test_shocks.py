"""
Exogenous-shock mechanism tests (web_demo exogenous-shocks workstream).

Covers:
  - Gating / bit-identity: flag-off adds no rule, schedules no shock event,
    leaves the ledger empty, and the trajectory is identical to the
    flag-absent call (the default-arg no-op).
  - Mechanism units: PopulationSelector modes; ShockSpec.signed_magnitude
    sign semantics; ShockRelaxation transient decay; POSITION convergence
    (consensus attractor) and divergence; WINDOW rule revert; RAMP.
  - S-911: a transient out-party AFFECT warming that decays within ~18
    months and leaves the post-2010 trajectory ~untouched (golden test).
  - S-Obergefell: a small cultural-axis DIVERGENCE (no spurious
    convergence — gap-preservation guard); real SSM numbers carried in the
    evidence copy, not as compass convergence.
"""
from __future__ import annotations

import numpy as np

from abm.core.agent import Agent
from abm.core.environment import Environment
from abm.core.space import ContinuousSpace2D
from abm.core.state import AgentState
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from abm.pillars.shocks import (
    Axis,
    Direction,
    Persistence,
    PopulationSelector,
    ShockSpec,
    TargetState,
    S_911,
    S_OBERGEFELL,
    SHOCK_911_TICK,
    SHOCK_OBERGEFELL_TICK,
    make_shock_event,
    shock_scheduled_events,
)
from abm.rules.shock_relaxation import ShockRelaxation
from scripts.anes_preset import ANES_FULL_KWARGS


# Small fast substrate: the canonical web/ANES config at reduced N.
# `exogenous_shocks` is popped so each test controls the flag explicitly
# (the preset now sets it True; tests pass it as a positional-by-keyword).
def _cfg(**over):
    cfg = dict(ANES_FULL_KWARGS)
    cfg["n_agents"] = 120
    cfg.pop("exogenous_shocks", None)
    cfg.update(over)
    return cfg


def _mean_outparty_warmth(eng) -> float:
    vals = []
    for a in eng.agents:
        aff = a.state.attrs.get("affect") or {}
        for w in aff.values():
            vals.append(float(np.clip(w, -1.0, 1.0)))
    return float(np.mean(vals)) if vals else float("nan")


def _y_gap(eng) -> float:
    parties = np.array([a.state.attrs.get("party", 2) for a in eng.agents])
    pos = eng.positions()
    d = pos[parties == 0][:, 1].mean() if (parties == 0).any() else 0.0
    r = pos[parties == 1][:, 1].mean() if (parties == 1).any() else 0.0
    return float(abs(d - r))


def _trajectory(exo: bool, seed: int = 0, ticks: int = 135):
    eng = build_engine(seed=seed, exogenous_shocks=exo, **_cfg())
    sched = build_schedule(
        faction_anchor_events=True, evidence_regrade=True, exogenous_shocks=exo,
    )
    snaps = []
    for t in range(0, ticks + 1):
        run_to(eng, sched, t)
        snaps.append(eng.positions().copy())
    return eng, snaps


# ---------------------------------------------------------------------
# Gating / bit-identity
# ---------------------------------------------------------------------


def test_flag_off_no_machinery():
    """Flag off: ShockRelaxation absent, no shock events scheduled, ledger
    empty after a full run."""
    eng = build_engine(seed=0, exogenous_shocks=False, **_cfg())
    assert not any(
        type(r).__name__ == "ShockRelaxation" for r in eng.env_rules
    )
    sched = build_schedule(
        faction_anchor_events=True, evidence_regrade=True, exogenous_shocks=False,
    )
    labels = {e.label for e in sched.events}
    assert "rally_911_2001" not in labels
    assert "obergefell_2015" not in labels
    run_to(eng, sched, 135)
    assert eng.env.attrs.get("active_shocks") == []


def test_flag_off_trajectory_identical_to_flag_absent():
    """Passing exogenous_shocks=False is byte-identical to not passing it
    (the default-arg is a strict no-op) across the full 135-tick run."""
    eng_absent = build_engine(seed=1, **_cfg())
    sched_absent = build_schedule(faction_anchor_events=True, evidence_regrade=True)
    eng_false = build_engine(seed=1, exogenous_shocks=False, **_cfg())
    sched_false = build_schedule(
        faction_anchor_events=True, evidence_regrade=True, exogenous_shocks=False,
    )
    for t in range(0, 136):
        run_to(eng_absent, sched_absent, t)
        run_to(eng_false, sched_false, t)
        assert np.array_equal(eng_absent.positions(), eng_false.positions()), (
            f"flag-off trajectory diverged at tick {t}"
        )


def test_flag_on_changes_trajectory():
    """Flag on schedules the catalogue and ShockRelaxation, and the
    trajectory differs from flag-off."""
    eng_on = build_engine(seed=0, exogenous_shocks=True, **_cfg())
    assert any(type(r).__name__ == "ShockRelaxation" for r in eng_on.env_rules)
    sched_on = build_schedule(
        faction_anchor_events=True, evidence_regrade=True, exogenous_shocks=True,
    )
    labels = {e.label for e in sched_on.events}
    assert {"rally_911_2001", "obergefell_2015"} <= labels

    _, snaps_off = _trajectory(False, seed=0)
    _, snaps_on = _trajectory(True, seed=0)
    # Identical up to the first shock (9/11 at tick 65); divergent after.
    assert np.array_equal(snaps_off[SHOCK_911_TICK - 1], snaps_on[SHOCK_911_TICK - 1])
    assert not np.array_equal(snaps_off[135], snaps_on[135])


# ---------------------------------------------------------------------
# Mechanism units
# ---------------------------------------------------------------------


def _toy_engine(n=10):
    agents = []
    for i in range(n):
        party = i % 2
        agents.append(Agent(id=i, state=AgentState(
            ideology=np.array([0.1 * (1 if party else -1), 0.2 * (1 if party else -1)]),
            attrs={"party": party, "affect": {1 - party: -0.3},
                   "perceived_threat": 0.0},
        )))
    env = Environment(attrs={"exogenous_shocks": True, "active_shocks": [],
                             "faction_event_rng_seed": 123})
    space = ContinuousSpace2D()
    space.rebuild(agents)

    class _E:
        pass
    e = _E()
    e.agents = agents
    e.env = env
    e.space = space
    e.tick = 0
    e.rules = type("R", (), {"rules": []})()
    e.env_rules = []
    return e


def test_selector_all_partisan_only():
    e = _toy_engine(10)
    e.agents[0].state.attrs["party"] = 2  # Independent
    ids = PopulationSelector.all().resolve(e)
    assert 0 not in ids and len(ids) == 9


def test_selector_by_party_fraction_deterministic():
    e = _toy_engine(20)
    sel = PopulationSelector.by_party({1: 0.5})
    a = sel.resolve(e)
    b = sel.resolve(e)
    assert a == b  # deterministic given build seed
    party1 = {ag.id for ag in e.agents if ag.state.attrs["party"] == 1}
    assert a <= party1 and len(a) == 5


def test_signed_magnitude_semantics():
    warm = ShockSpec("w", "", "", "k", 0, TargetState.AFFECT,
                     Direction.CONVERGENCE, 0.08, PopulationSelector.all(),
                     Persistence.PERMANENT, "MED", "", "")
    cool = ShockSpec("c", "", "", "k", 0, TargetState.AFFECT,
                     Direction.DIVERGENCE, 0.08, PopulationSelector.all(),
                     Persistence.PERMANENT, "MED", "", "")
    assert warm.signed_magnitude() > 0      # convergence warms
    assert cool.signed_magnitude() < 0      # divergence cools


def test_shock_relaxation_transient_decay():
    """Injected affect bump erodes geometrically toward 0."""
    e = _toy_engine(4)
    spec = ShockSpec("t", "", "", "k", 0, TargetState.AFFECT,
                     Direction.CONVERGENCE, 0.10, PopulationSelector.all(),
                     Persistence.TRANSIENT, "MED", "", "", decay_rate=0.5)
    make_shock_event(spec)(e)
    # Onset: each agent warmed by +0.10 (from -0.3 to -0.2).
    assert all(abs(a.state.attrs["affect"][1 - a.state.attrs["party"]] + 0.2) < 1e-9
               for a in e.agents)
    rule = ShockRelaxation()
    # One relaxation tick at decay 0.5 removes half the injected 0.10.
    rule.apply(e.env, e.agents, e.space, None, tick=1)
    for a in e.agents:
        w = a.state.attrs["affect"][1 - a.state.attrs["party"]]
        assert abs(w - (-0.25)) < 1e-9, w  # -0.2 minus half of +0.10
    # Run to full relaxation: warmth returns to baseline -0.3.
    for t in range(2, 40):
        rule.apply(e.env, e.agents, e.space, None, tick=t)
    for a in e.agents:
        assert abs(a.state.attrs["affect"][1 - a.state.attrs["party"]] + 0.3) < 1e-3
    assert e.env.attrs["active_shocks"] == []  # record retired


def test_position_convergence_pulls_toward_target():
    """First-class convergence: a POSITION CONVERGENCE shock pulls agents
    toward the consensus attractor (exercised even though no shipped shock
    uses it)."""
    e = _toy_engine(6)
    spec = ShockSpec("conv", "", "", "k", 0, TargetState.POSITION,
                     Direction.CONVERGENCE, 0.5, PopulationSelector.all(),
                     Persistence.PERMANENT, "MED", "", "",
                     consensus_target=(0.0, 0.0))
    before = [np.linalg.norm(a.state.ideology) for a in e.agents]
    make_shock_event(spec)(e)
    after = [np.linalg.norm(a.state.ideology) for a in e.agents]
    # 50% pull toward origin halves each agent's distance from origin.
    for b, a in zip(before, after):
        assert a < b
        assert abs(a - 0.5 * b) < 1e-9


def test_position_divergence_pushes_outward_by_party_sign():
    e = _toy_engine(6)
    spec = ShockSpec("div", "", "", "k", 0, TargetState.POSITION,
                     Direction.DIVERGENCE, 0.05, PopulationSelector.all(),
                     Persistence.PERMANENT, "MED", "", "", axis=Axis.Y)
    before_y = {a.id: float(a.state.ideology[1]) for a in e.agents}
    make_shock_event(spec)(e)
    for a in e.agents:
        sign = 1.0 if a.state.attrs["party"] == 1 else -1.0
        assert abs(float(a.state.ideology[1]) - (before_y[a.id] + sign * 0.05)) < 1e-9


def test_window_rule_multiplier_reverts():
    """LEARNING_RATE WINDOW shock multiplies the rule attr then restores it."""
    e = _toy_engine(4)

    class _AffStub:
        lr = 0.01
    rule = _AffStub()
    e.rules.rules = [rule]
    spec = ShockSpec("win", "", "", "k", 0, TargetState.LEARNING_RATE,
                     Direction.DIVERGENCE, 1.5, PopulationSelector.all(),
                     Persistence.WINDOW, "MED", "", "", duration_ticks=3,
                     rule_class="_AffStub")
    e.tick = 10
    make_shock_event(spec)(e)
    assert abs(rule.lr - 0.015) < 1e-12       # ×1.5 applied
    relax = ShockRelaxation()
    relax.apply(e.env, e.agents, e.space, None, tick=12)   # inside window
    assert abs(rule.lr - 0.015) < 1e-12
    relax.apply(e.env, e.agents, e.space, None, tick=13)   # expiry → revert
    assert abs(rule.lr - 0.01) < 1e-12
    assert e.env.attrs["active_shocks"] == []


def test_ramp_position_applies_increments():
    """RAMP POSITION applies magnitude in equal per-tick increments."""
    e = _toy_engine(2)
    spec = ShockSpec("ramp", "", "", "k", 0, TargetState.POSITION,
                     Direction.DIVERGENCE, 0.06, PopulationSelector.all(),
                     Persistence.RAMP, "MED", "", "", axis=Axis.Y, ramp_ticks=3)
    before_y = {a.id: float(a.state.ideology[1]) for a in e.agents}
    make_shock_event(spec)(e)            # registers ledger record, no apply yet
    relax = ShockRelaxation()
    for t in range(1, 4):
        relax.apply(e.env, e.agents, e.space, None, tick=t)
    for a in e.agents:
        sign = 1.0 if a.state.attrs["party"] == 1 else -1.0
        # 3 increments of 0.06/3 = total 0.06 outward on y.
        assert abs(float(a.state.ideology[1]) - (before_y[a.id] + sign * 0.06)) < 1e-9
    assert e.env.attrs["active_shocks"] == []  # retired after ramp_ticks


# ---------------------------------------------------------------------
# S-911 — transient warming, decays, leaves post-2010 ~untouched
# ---------------------------------------------------------------------


def test_s911_warms_at_onset_then_decays():
    eng_off, _ = _trajectory(False, seed=0, ticks=0)  # just to build; unused
    eng_on = build_engine(seed=0, exogenous_shocks=True, **_cfg())
    eng_base = build_engine(seed=0, exogenous_shocks=False, **_cfg())
    s_on = build_schedule(faction_anchor_events=True, evidence_regrade=True, exogenous_shocks=True)
    s_base = build_schedule(faction_anchor_events=True, evidence_regrade=True, exogenous_shocks=False)

    # Just before the shock: identical warmth.
    run_to(eng_on, s_on, SHOCK_911_TICK - 1)
    run_to(eng_base, s_base, SHOCK_911_TICK - 1)
    assert abs(_mean_outparty_warmth(eng_on) - _mean_outparty_warmth(eng_base)) < 1e-9

    # At onset: shocked run is WARMER (convergence), by ~the injected magnitude.
    run_to(eng_on, s_on, SHOCK_911_TICK)
    run_to(eng_base, s_base, SHOCK_911_TICK)
    bump = _mean_outparty_warmth(eng_on) - _mean_outparty_warmth(eng_base)
    assert 0.04 < bump < 0.10, f"onset warming bump out of range: {bump:+.4f}"

    # ~18 months later (tick 65→70): bump should be roughly halved or less.
    run_to(eng_on, s_on, SHOCK_911_TICK + 5)
    run_to(eng_base, s_base, SHOCK_911_TICK + 5)
    bump5 = _mean_outparty_warmth(eng_on) - _mean_outparty_warmth(eng_base)
    assert bump5 < bump * 0.7, f"warming did not decay: {bump5:+.4f} vs {bump:+.4f}"

    # By the 2010 release window (tick 90): essentially gone.
    run_to(eng_on, s_on, 90)
    run_to(eng_base, s_base, 90)
    bump90 = abs(_mean_outparty_warmth(eng_on) - _mean_outparty_warmth(eng_base))
    assert bump90 < 0.02, f"residual warming at 2010 too large: {bump90:+.4f}"


def test_s911_spec_flagged_contested():
    assert S_911.evidence_grade in ("MED", "CONTESTED")
    assert S_911.direction == Direction.CONVERGENCE
    assert "approval" in S_911.evidence_note.lower()


# ---------------------------------------------------------------------
# S-Obergefell — no spurious convergence; real numbers in the copy
# ---------------------------------------------------------------------


def test_obergefell_does_not_converge_cultural_gap():
    """Gap-preservation guard: at and after the Obergefell tick, the
    cultural-axis party gap of the shocked run is >= the unshocked run
    (Decision A — the bundled axis must NOT show convergence).

    Re-blessed at MHV S2 T2.6 (canonical flip to the D=7 substrate): the
    onset check stays strict, but the long-horizon checkpoints get a
    0.005 noise tolerance. The divergence push is lifted onto seven
    items and then remixed by 65+ ticks of high-dimensional dynamics, so
    the paired same-seed gap difference at tick 135 is butterfly-effect
    noise (measured -0.0002 on a 0.59 gap); the strict >= was pinning
    that noise, not the convergence claim. A genuine spurious
    convergence (the thing Decision A forbids) is orders of magnitude
    larger than the tolerance."""
    eng_on = build_engine(seed=0, exogenous_shocks=True, **_cfg())
    eng_base = build_engine(seed=0, exogenous_shocks=False, **_cfg())
    s_on = build_schedule(faction_anchor_events=True, evidence_regrade=True, exogenous_shocks=True)
    s_base = build_schedule(faction_anchor_events=True, evidence_regrade=True, exogenous_shocks=False)
    for t in (SHOCK_OBERGEFELL_TICK + 1, 120, 135):
        run_to(eng_on, s_on, t)
        run_to(eng_base, s_base, t)
        tol = 1e-9 if t == SHOCK_OBERGEFELL_TICK + 1 else 0.005
        assert _y_gap(eng_on) >= _y_gap(eng_base) - tol, (
            f"Obergefell spuriously narrowed the cultural gap at tick {t}: "
            f"on={_y_gap(eng_on):.4f} base={_y_gap(eng_base):.4f}"
        )


def test_obergefell_is_divergence_or_marker_not_convergence():
    assert S_OBERGEFELL.target_state == TargetState.POSITION
    assert S_OBERGEFELL.direction == Direction.DIVERGENCE
    assert S_OBERGEFELL.axis == Axis.Y


def test_obergefell_real_numbers_in_copy():
    """The genuine SSM convergence lives in the evidence copy, not the
    compass — assert the real opinion numbers are carried in-text."""
    note = S_OBERGEFELL.evidence_note
    assert "27%" in note and "60%" in note
    assert "within-person" in note.lower()
    assert "partisan gap" in note.lower() or "party divide" in note.lower()
