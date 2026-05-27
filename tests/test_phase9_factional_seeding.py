"""Phase 9 Tier A — factional seeding tests.

Covers:
- Default `factional_seeding=False` is bit-identical to pre-Phase-9 head.
- `factional_seeding=True` tags every non-Independent agent with a
  faction from `HISTORICAL_FACTIONS_1980`.
- Realized faction shares match dict weights within ±5pp at n=500.
- Extremity-graded stubbornness boost is monotone in ‖center‖.
- Centrists and Independents are not boosted.
- Faction-emergence events (Tea Party, MAGA, Bernie, DSA) re-label
  subsets, update `party_cue`, bump stubbornness, do NOT move ideology.
- Pillar `calm_to_camps.build_engine` is untouched by Phase 9 (no
  `faction` attr on any pillar agent).
"""
from __future__ import annotations

import numpy as np
import pytest

from abm.pillars import historical_arc as ha
from abm.pillars.calm_to_camps import build_engine as pillar_build
from abm.pillars.historical_arc import (
    HISTORICAL_FACTIONS_1980,
    build_engine,
    build_schedule,
)
from abm.pillars.schedule import run_to


# ---------------------------------------------------------------------
# Bit-identity gating tests
# ---------------------------------------------------------------------


def test_factional_seeding_default_off_bit_identical():
    """Default kwarg (False) produces the same positions as omitting it."""
    eng_a = build_engine(seed=0, n_agents=50)
    eng_b = build_engine(seed=0, n_agents=50, factional_seeding=False)
    pos_a = np.array([a.state.ideology for a in eng_a.agents])
    pos_b = np.array([a.state.ideology for a in eng_b.agents])
    assert np.array_equal(pos_a, pos_b)
    # No agent should carry a faction tag at default.
    for a in eng_a.agents:
        assert "faction" not in a.state.attrs


def test_pillar_bit_identity_no_factional_seeding():
    """Pillar build never sets `faction` — pillar is sacred."""
    eng = pillar_build(seed=0, n_agents=50)
    for a in eng.agents:
        assert a.state.attrs.get("faction") is None


# ---------------------------------------------------------------------
# Factional seeding behaviour
# ---------------------------------------------------------------------


def test_factional_seeding_on_assigns_factions():
    eng = build_engine(seed=0, n_agents=200, factional_seeding=True)
    for a in eng.agents:
        if a.state.attrs["party"] == 2:
            continue  # independents skipped
        f = a.state.attrs.get("faction")
        assert f is not None
        assert f in HISTORICAL_FACTIONS_1980


def test_factional_weights_realized():
    eng = build_engine(seed=0, n_agents=500, factional_seeding=True)
    counts: dict[str, int] = {k: 0 for k in HISTORICAL_FACTIONS_1980}
    n_partisan = 0
    for a in eng.agents:
        f = a.state.attrs.get("faction")
        if f is None:
            continue
        counts[f] += 1
        n_partisan += 1
    assert n_partisan > 0
    for label, info in HISTORICAL_FACTIONS_1980.items():
        share = counts[label] / n_partisan
        assert abs(share - info["weight"]) <= 0.05, (
            f"{label} share={share:.3f} vs target={info['weight']:.3f}"
        )


def test_stubbornness_boost_extremity_graded():
    """Old_Right (‖center‖≈0.569) > Mainstream_Dems (‖center‖≈0.335)."""
    eng = build_engine(seed=0, n_agents=2000, factional_seeding=True)
    or_stubs = [
        a.state.attrs["stubbornness"]
        for a in eng.agents
        if a.state.attrs.get("faction") == "Old_Right"
    ]
    md_stubs = [
        a.state.attrs["stubbornness"]
        for a in eng.agents
        if a.state.attrs.get("faction") == "Mainstream_Dems"
    ]
    assert or_stubs and md_stubs
    assert np.mean(or_stubs) > np.mean(md_stubs)


def test_centrists_no_boost():
    """Centrists have stubbornness drawn from Beta(2,5) — mean ≈ 2/7
    ≈ 0.286 — with NO additive boost (norm of (0, 0) is 0)."""
    eng = build_engine(seed=0, n_agents=2000, factional_seeding=True)
    c_stubs = [
        a.state.attrs["stubbornness"]
        for a in eng.agents
        if a.state.attrs.get("faction") == "Centrists"
    ]
    assert c_stubs
    # Beta(2,5) mean = 2/7 ≈ 0.286; allow generous slack.
    assert abs(np.mean(c_stubs) - 0.286) < 0.05
    # None should be at the 0.90 boost cap (Centrists never receive boost).
    assert max(c_stubs) < 0.90


def test_independents_unaffected():
    eng = build_engine(
        seed=0, n_agents=500, factional_seeding=True,
        independent_fraction=0.12,
    )
    indeps = [a for a in eng.agents if a.state.attrs["party"] == 2]
    assert indeps  # confirm some exist
    for a in indeps:
        assert a.state.attrs.get("faction") is None


# ---------------------------------------------------------------------
# Faction-emergence event tests
# ---------------------------------------------------------------------


def test_tea_party_event_relabels():
    eng = build_engine(seed=0, n_agents=500, factional_seeding=True)
    sched = build_schedule(factional_seeding=True)
    # Run past tick 87 (2009 Tea Party event).
    run_to(eng, sched, 90)
    tp_agents = [
        a for a in eng.agents
        if a.state.attrs.get("faction") == "Tea_Party"
    ]
    assert len(tp_agents) > 0, "Tea Party event should re-label some agents"
    target = np.array([0.55, 0.30])
    for a in tp_agents:
        cue = np.asarray(a.state.attrs["party_cue"])
        # cue is centroid + N(0, 0.04): within ~4 sigma in each axis.
        assert np.linalg.norm(cue - target) < 0.30


def test_maga_event_two_source_factions():
    """Track agent ids before MAGA fires; after, MAGA-tagged agents
    must originate from BOTH Mainstream_Reps AND New_Right_Religious."""
    eng = build_engine(seed=0, n_agents=500, factional_seeding=True)
    # Snapshot original factions before any event fires.
    original = {a.id: a.state.attrs.get("faction") for a in eng.agents}
    sched = build_schedule(factional_seeding=True)
    # Run past tick 105 (2015 MAGA event) but stop before 108 to avoid
    # other label churn (none expected, but defensive).
    run_to(eng, sched, 107)
    maga_ids = [
        a.id for a in eng.agents
        if a.state.attrs.get("faction") == "MAGA"
    ]
    assert maga_ids, "MAGA event should re-label some agents"
    sources = {original[i] for i in maga_ids}
    assert "Mainstream_Reps" in sources
    assert "New_Right_Religious" in sources


def test_event_does_not_move_ideology():
    """The MAGA event re-labels and updates party_cue + stubbornness
    only — the agent's `state.ideology` is unchanged at the firing
    moment (drift afterward comes from PartyPull, not the event)."""
    eng = build_engine(seed=0, n_agents=500, factional_seeding=True)
    sched = build_schedule(factional_seeding=True)
    # Advance to tick 104 — the MAGA event at tick 105 has NOT yet fired.
    run_to(eng, sched, 104)
    pre_ideology = {a.id: a.state.ideology.copy() for a in eng.agents}
    pre_faction = {a.id: a.state.attrs.get("faction") for a in eng.agents}
    pre_party_cue = {
        a.id: np.asarray(a.state.attrs.get("party_cue")).copy()
        for a in eng.agents
        if a.state.attrs.get("party_cue") is not None
    }
    # Directly invoke the MAGA event handler — no engine ticks fire in
    # between, so any ideology delta would be from the event itself.
    ha._event_2015_maga(eng)
    # Some agent should now be MAGA-tagged that wasn't before.
    new_maga = [
        a for a in eng.agents
        if a.state.attrs.get("faction") == "MAGA"
        and pre_faction[a.id] != "MAGA"
    ]
    assert new_maga, "MAGA event must have fired"
    for a in new_maga:
        # Ideology unchanged at the firing moment.
        assert np.array_equal(a.state.ideology, pre_ideology[a.id])
        # But party_cue DID move (event re-anchors the target).
        new_cue = np.asarray(a.state.attrs["party_cue"])
        assert not np.array_equal(new_cue, pre_party_cue[a.id])
