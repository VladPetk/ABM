"""Per-rule isolation drift-guards (engine knob audit, 2026-06).

Closes the gap flagged in CLAUDE.md / ENGINE_KNOBS: several *active* rules
ship with no behavioral isolation test — a regression in any one of them
would not be caught by the pillar (composition) or the arc golden tests
(empirical), only here. Each test runs ONE rule on a clean minimal
substrate carrying exactly the attrs that rule reads, sweeps its primary
knob, and pins the sign + monotonicity of its theoretical role.

Pattern mirrors `compass_basic` / `test_canonical.py` (the only pre-
existing isolation layer, which covered only Hegselmann-Krause BC).

These are fast (small N, 3 seeds) and deterministic. They pin DIRECTION,
not calibrated magnitudes — magnitudes belong to the pillar/arc layers.
"""
from __future__ import annotations

import numpy as np
import pytest

from abm.core.agent import Agent
from abm.core.engine import Engine
from abm.core.environment import Environment
from abm.core.network import Network
from abm.core.rules import RulePipeline
from abm.core.space import ContinuousSpace2D
from abm.core.state import AgentState

from abm.rules.elite_drift import EliteDrift
from abm.rules.identity_sorting import IdentitySorting
from abm.rules.identity_to_position import IdentityToIdeologyPull
from abm.rules.identity_alignment import IdentityAlignment
from abm.rules.mediated_animus import MediatedAnimus
from abm.rules.perception_update import PerceptionUpdate
from abm.rules.party_realignment import ProtectedPartyRealignment
from abm.rules.faction_anchor import FactionAnchor

from abm.metrics.affective import affective_polarization, sorting_index

SEEDS = (0, 1, 2)
BOUNDS = ((-1.0, 1.0), (-1.0, 1.0))


def _engine(agents, env_rules, agent_rules, env_attrs, seed):
    return Engine(agents=agents, env=Environment(attrs=env_attrs),
                  space=ContinuousSpace2D(bounds=BOUNDS),
                  rules=RulePipeline(agent_rules), env_rules=env_rules, seed=seed)


def _party_sep(eng):
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    return float(np.linalg.norm(pos[parties == 0].mean(0) - pos[parties == 1].mean(0)))


def _mean_align(eng):
    a = [float(x.state.attrs.get("identity_alignment", 0.0))
         for x in eng.agents if x.state.attrs.get("party") in (0, 1)]
    return float(np.mean(a))


def _avg_over_seeds(fn):
    return float(np.mean([fn(s) for s in SEEDS]))


# --- EliteDrift -----------------------------------------------------------

def _elite_drift_sep(rate, seed):
    rng = np.random.default_rng(seed)
    n = 100
    agents = []
    for i in range(n):
        party = 0 if i < n // 2 else 1
        cue = np.array([-0.2 if party == 0 else 0.2, 0.0])
        agents.append(Agent(id=i, state=AgentState(
            ideology=cue.copy(), attrs={"party": party, "party_cue": cue.copy()})))
    eng = _engine(agents, [EliteDrift(rate=rate)], [],
                  {"network": Network.complete(range(n)),
                   "parties": {0: np.array([-0.2, 0.0]), 1: np.array([0.2, 0.0])}}, seed)
    eng.run(50)
    p = eng.env.attrs["parties"]
    return float(np.linalg.norm(p[0] - p[1]))


def test_elite_drift_separates_centroids_monotonically():
    """Higher drift rate => party centroids diverge faster (DW-NOMINATE
    elite divergence; McCarty/Poole/Rosenthal 2006)."""
    s0 = _avg_over_seeds(lambda s: _elite_drift_sep(0.0, s))
    s_lo = _avg_over_seeds(lambda s: _elite_drift_sep(0.005, s))
    s_hi = _avg_over_seeds(lambda s: _elite_drift_sep(0.02, s))
    assert s0 < s_lo < s_hi, (s0, s_lo, s_hi)
    # rate=0 must leave the initial 0.4 gap untouched (exact no-op).
    assert abs(s0 - 0.4) < 1e-9, s0


# --- IdentitySorting ------------------------------------------------------

def _identity_sorting_index(sort_rate, seed):
    rng = np.random.default_rng(seed)
    n = 160
    agents = []
    for i in range(n):
        party = 0 if i < n // 2 else 1
        base = -0.1 if party == 0 else 0.1
        ids = np.clip(np.array([base + rng.normal(0, 0.3) for _ in range(3)]), -1, 1)
        agents.append(Agent(id=i, state=AgentState(
            ideology=np.zeros(2), attrs={"party": party, "identities": ids})))
    eng = _engine(agents, [], [IdentitySorting(sort_rate=sort_rate, step=0.15,
                  differentiation=0.5)], {"network": Network.complete(range(n))}, seed)
    eng.run(80)
    return sorting_index(eng.agents)


def test_identity_sorting_raises_alignment_monotonically():
    """Higher sort_rate => stronger party-identity alignment (Mason 2018
    mega-identity stacking)."""
    lo = _avg_over_seeds(lambda s: _identity_sorting_index(0.0, s))
    mid = _avg_over_seeds(lambda s: _identity_sorting_index(0.03, s))
    hi = _avg_over_seeds(lambda s: _identity_sorting_index(0.1, s))
    assert lo < mid < hi, (lo, mid, hi)


# --- IdentityToIdeologyPull -----------------------------------------------

def _identity_pull_sep(strength, seed):
    rng = np.random.default_rng(seed)
    n = 160
    agents = []
    for i in range(n):
        party = 0 if i < n // 2 else 1
        base = -0.5 if party == 0 else 0.5
        ids = np.clip(np.array([base + rng.normal(0, 0.2) for _ in range(3)]), -1, 1)
        agents.append(Agent(id=i, state=AgentState(
            ideology=np.array([rng.normal(0, 0.05), rng.normal(0, 0.05)]),
            attrs={"party": party, "identities": ids, "stubbornness": 0.0})))
    eng = _engine(agents, [], [IdentityToIdeologyPull(strength_x=strength,
                  strength_y=strength)],
                  {"network": Network.complete(range(n)), "party_issue_coupling": 1.0}, seed)
    eng.run(50)
    return _party_sep(eng)


def test_identity_to_ideology_pull_separates_monotonically():
    """Higher coupling strength => party-aligned identities pull positions
    apart (Mason 2018 identity->ideology channel)."""
    lo = _avg_over_seeds(lambda s: _identity_pull_sep(0.0, s))
    mid = _avg_over_seeds(lambda s: _identity_pull_sep(0.02, s))
    hi = _avg_over_seeds(lambda s: _identity_pull_sep(0.08, s))
    assert lo < mid < hi, (lo, mid, hi)
    assert lo < 0.1, lo  # strength=0 is an exact no-op (no separation)


# --- IdentityAlignment ----------------------------------------------------

def _identity_alignment_level(rate, seed):
    rng = np.random.default_rng(seed)
    n = 160
    agents = []
    for i in range(n):
        party = 0 if i < n // 2 else 1
        sign = -1.0 if party == 0 else 1.0
        ids = np.clip(np.array([sign * 0.6 + rng.normal(0, 0.1) for _ in range(3)]), -1, 1)
        agents.append(Agent(id=i, state=AgentState(
            ideology=np.zeros(2),
            attrs={"party": party, "identities": ids, "identity_alignment": 0.0})))
    eng = _engine(agents, [], [IdentityAlignment(rate=rate)],
                  {"network": Network.complete(range(n)), "evidence_regrade": True,
                   "party_identity_centers": {0: np.array([-0.6, -0.6, -0.6]),
                                              1: np.array([0.6, 0.6, 0.6])}}, seed)
    eng.run(10)
    return _mean_align(eng)


def test_identity_alignment_accretes_faster_with_rate():
    """At a fixed horizon, a higher relaxation rate accretes more
    mega-identity alignment (Mason 2018)."""
    lo = _avg_over_seeds(lambda s: _identity_alignment_level(0.0, s))
    mid = _avg_over_seeds(lambda s: _identity_alignment_level(0.05, s))
    hi = _avg_over_seeds(lambda s: _identity_alignment_level(0.2, s))
    assert lo < mid < hi, (lo, mid, hi)
    assert abs(lo) < 1e-12, lo  # rate=0 never moves alignment


def test_identity_alignment_no_op_without_regrade_gate():
    """Strict no-op (no rng draw, empty delta) when evidence_regrade is
    off — the gating discipline that keeps the default path bit-identical."""
    n = 50
    agents = [Agent(id=i, state=AgentState(
        ideology=np.zeros(2),
        attrs={"party": i % 2, "identities": np.array([0.6, 0.6, 0.6]),
               "identity_alignment": 0.0})) for i in range(n)]
    eng = _engine(agents, [], [IdentityAlignment(rate=0.5)],
                  {"network": Network.complete(range(n)),  # no evidence_regrade
                   "party_identity_centers": {0: np.array([-0.6, -0.6, -0.6]),
                                              1: np.array([0.6, 0.6, 0.6])}}, 0)
    eng.run(20)
    assert _mean_align(eng) == 0.0


# --- MediatedAnimus -------------------------------------------------------

def _mediated_animus_warmth(lr, seed):
    n = 160
    agents = []
    for i in range(n):
        party = 0 if i < n // 2 else 1
        agents.append(Agent(id=i, state=AgentState(
            ideology=np.zeros(2),
            attrs={"party": party, "affect": {1 - party: 0.0}, "identity_alignment": 0.5})))
    eng = _engine(agents, [], [MediatedAnimus(learning_rate=lr)],
                  {"network": Network.complete(range(n)), "mediated_animus_weight": 1.0}, seed)
    eng.run(40)
    return affective_polarization(eng.agents)


def test_mediated_animus_cools_monotonically_without_contact():
    """Higher parasocial learning_rate => colder out-party warmth, with NO
    network contact required (Mason 2018; Iyengar et al. 2019)."""
    lo = _avg_over_seeds(lambda s: _mediated_animus_warmth(0.0, s))
    mid = _avg_over_seeds(lambda s: _mediated_animus_warmth(0.01, s))
    hi = _avg_over_seeds(lambda s: _mediated_animus_warmth(0.05, s))
    assert hi < mid < lo, (lo, mid, hi)
    assert lo == 0.0  # lr=0 exact no-op


def test_mediated_animus_no_op_without_weight():
    """Zero mediated_animus_weight => exact no-op even with lr>0 (gate)."""
    w = _avg_over_seeds(lambda s: _med_no_weight(s))
    assert w == 0.0


def _med_no_weight(seed):
    n = 60
    agents = [Agent(id=i, state=AgentState(
        ideology=np.zeros(2),
        attrs={"party": i % 2, "affect": {1 - (i % 2): 0.0},
               "identity_alignment": 0.8})) for i in range(n)]
    eng = _engine(agents, [], [MediatedAnimus(learning_rate=0.05)],
                  {"network": Network.complete(range(n))}, seed)  # weight unset -> 0.0
    eng.run(20)
    return affective_polarization(eng.agents)


# --- PerceptionUpdate -----------------------------------------------------

def _perception_error(rate, seed):
    n = 160
    agents = []
    for i in range(n):
        party = 0 if i < n // 2 else 1
        actual_other = np.array([0.5 if party == 0 else -0.5, 0.0])
        biased = actual_other * 1.6
        agents.append(Agent(id=i, state=AgentState(
            ideology=np.array([-0.5 if party == 0 else 0.5, 0.0]),
            attrs={"party": party, "perceived_other_party": {1 - party: biased}})))
    eng = _engine(agents, [], [PerceptionUpdate(correction_rate=rate)],
                  {"network": Network.complete(range(n)),
                   "parties": {0: np.array([-0.5, 0.0]), 1: np.array([0.5, 0.0])}}, seed)
    eng.run(30)
    es = []
    for a in eng.agents:
        p = a.state.attrs["party"]
        perc = a.state.attrs["perceived_other_party"][1 - p]
        actual = np.array([0.5 if p == 0 else -0.5, 0.0])
        es.append(float(np.linalg.norm(perc - actual)))
    return float(np.mean(es))


def test_perception_update_shrinks_error_monotonically():
    """Higher correction_rate => biased out-party perception converges to
    the actual neighbour position faster (X7 perception-gap mechanism)."""
    lo = _avg_over_seeds(lambda s: _perception_error(0.0, s))
    mid = _avg_over_seeds(lambda s: _perception_error(0.05, s))
    hi = _avg_over_seeds(lambda s: _perception_error(0.3, s))
    assert hi < mid < lo, (lo, mid, hi)


# --- ProtectedPartyRealignment --------------------------------------------

def test_protected_realignment_flips_only_sustained_crossers():
    """A protected agent parked across the divide for >= sustain_ticks
    converts party; one held inside its own half never flips."""
    # Group A: party-0 agents sitting at x=+0.5 (clear other side).
    # Group B: party-0 agents at x=-0.5 (own side) — must NOT flip.
    n = 40
    agents = []
    for i in range(n):
        x = 0.5 if i < n // 2 else -0.5
        agents.append(Agent(id=i, state=AgentState(
            ideology=np.array([x, 0.0]),
            attrs={"party": 0, "do_not_replace": True, "affect": {1: -0.3},
                   "party_cue": np.array([-0.5, 0.0])})))
    eng = _engine(agents, [ProtectedPartyRealignment(x_threshold=0.12, sustain_ticks=6)],
                  [], {"network": Network.complete(range(n)),
                       "parties": {0: np.array([-0.5, 0.0]), 1: np.array([0.5, 0.0])}}, 0)
    eng.run(10)
    crossers = [a for a in eng.agents if a.state.attrs.get("_orig_x", a.state.ideology[0]) > 0]
    flipped_cross = sum(1 for a in eng.agents[: n // 2] if a.state.attrs["party"] == 1)
    flipped_own = sum(1 for a in eng.agents[n // 2:] if a.state.attrs["party"] == 1)
    assert flipped_cross == n // 2, flipped_cross  # all sustained crossers flip
    assert flipped_own == 0, flipped_own           # none on own side flip


def test_protected_realignment_threshold_gates_flips():
    """Raising x_threshold above the crosser's displacement suppresses the
    flip — the sustain/threshold gate is load-bearing, not cosmetic."""
    def flips(thr):
        n = 30
        agents = [Agent(id=i, state=AgentState(
            ideology=np.array([0.4, 0.0]),
            attrs={"party": 0, "do_not_replace": True, "affect": {1: -0.3},
                   "party_cue": np.array([-0.5, 0.0])})) for i in range(n)]
        eng = _engine(agents, [ProtectedPartyRealignment(x_threshold=thr, sustain_ticks=6)],
                      [], {"network": Network.complete(range(n)),
                           "parties": {0: np.array([-0.5, 0.0]), 1: np.array([0.5, 0.0])}}, 0)
        eng.run(12)
        return sum(1 for a in eng.agents if a.state.attrs["party"] == 1)
    assert flips(0.2) == 30   # 0.4 > 0.2 -> all flip
    assert flips(0.6) == 0    # 0.4 < 0.6 -> none flip


# --- FactionAnchor --------------------------------------------------------

def _faction_distance(strength, seed):
    rng = np.random.default_rng(seed)
    n = 120
    center = np.array([0.7, 0.4])
    agents = [Agent(id=i, state=AgentState(
        ideology=np.array([rng.normal(0, 0.1), rng.normal(0, 0.1)]),
        attrs={"party": 1, "faction": "X", "faction_center": center.copy(),
               "stubbornness": 0.0})) for i in range(n)]
    eng = _engine(agents, [], [FactionAnchor(strength=strength)],
                  {"network": Network.complete(range(n))}, seed)
    eng.run(30)
    return float(np.mean([np.linalg.norm(a.state.ideology - center) for a in eng.agents]))


def test_faction_anchor_pulls_toward_center_monotonically():
    """Higher faction-anchor strength => tagged agents converge on their
    faction sub-centroid faster (Phase 9 Tier C emergence factions)."""
    lo = _avg_over_seeds(lambda s: _faction_distance(0.0, s))
    mid = _avg_over_seeds(lambda s: _faction_distance(0.05, s))
    hi = _avg_over_seeds(lambda s: _faction_distance(0.2, s))
    assert hi < mid < lo, (lo, mid, hi)


def test_faction_anchor_no_op_without_center():
    """No faction_center attr => exact no-op (the self-gating that keeps
    the pillar / pre-emergence path bit-identical)."""
    n = 60
    agents = [Agent(id=i, state=AgentState(
        ideology=np.array([0.1, 0.1]), attrs={"party": 1, "stubbornness": 0.0}))
        for i in range(n)]
    before = np.array([a.state.ideology.copy() for a in agents])
    eng = _engine(agents, [], [FactionAnchor(strength=0.2)],
                  {"network": Network.complete(range(n))}, 0)
    eng.run(10)
    after = eng.positions()
    assert np.allclose(before, after)


# --- X5 "Deprogramming & exit programs" (MHV S5 T5.0) ---------------------

class _StubEngine:
    """Minimal carrier the X5 setup reads (`engine.agents` only)."""
    def __init__(self, agents):
        self.agents = agents


def _tagged_agents(n_tag, n_untag):
    """n_tag faction-tagged agents (faction_center + identity_strength) +
    n_untag untagged."""
    agents = []
    for i in range(n_tag):
        agents.append(Agent(id=i, state=AgentState(
            ideology=np.array([0.5, 0.5]),
            attrs={"party": 1, "faction_center": np.array([0.6, 0.6]),
                   "identity_strength": 0.8})))
    for j in range(n_untag):
        agents.append(Agent(id=n_tag + j, state=AgentState(
            ideology=np.array([0.1, 0.1]),
            attrs={"party": 0, "identity_strength": 0.8})))
    return agents


def test_x5_deprogramming_clears_treated_fraction_of_tagged():
    """X5 clears `faction_center` AND halves `identity_strength` on exactly
    the treated fraction of faction-tagged agents (faction exit +
    identity moderation), and leaves untagged agents untouched."""
    from abm.pillars.interventions_phase6 import (
        _x5_deprogramming_setup, X5_TREATED_FRACTION,
        X5_IDENTITY_MODERATE_FACTOR,
    )
    n_tag, n_untag = 50, 70
    agents = _tagged_agents(n_tag, n_untag)
    _x5_deprogramming_setup(_StubEngine(agents))
    treated = [a for a in agents[:n_tag]
               if a.state.attrs.get("faction_center") is None]
    untreated_tagged = [a for a in agents[:n_tag]
                        if a.state.attrs.get("faction_center") is not None]
    assert len(treated) == int(X5_TREATED_FRACTION * n_tag)  # exactly 20%
    # Treated: identity moderated; untreated-tagged: identity untouched.
    assert all(
        a.state.attrs["identity_strength"] == 0.8 * X5_IDENTITY_MODERATE_FACTOR
        for a in treated
    )
    assert all(a.state.attrs["identity_strength"] == 0.8
               for a in untreated_tagged)
    # Untagged agents never lose the faction attr or get moderated.
    assert all("faction_center" not in a.state.attrs for a in agents[n_tag:])
    assert all(a.state.attrs["identity_strength"] == 0.8
               for a in agents[n_tag:])


def test_x5_deprogramming_no_op_without_factions():
    """Pre-emergence releases have no tagged agents → exact no-op (the
    decade-gating: you cannot deprogram a faction that hasn't emerged)."""
    from abm.pillars.interventions_phase6 import _x5_deprogramming_setup
    agents = _tagged_agents(0, 40)
    before = [dict(a.state.attrs) for a in agents]
    _x5_deprogramming_setup(_StubEngine(agents))
    assert [dict(a.state.attrs) for a in agents] == before
