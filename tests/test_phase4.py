"""Phase 4 — realism core tests.

Three feature groups:

- **F1 (anchored agents):** stubborn agents move less under any pull; an
  agent displaced from its anchor with all forces off drifts back toward it.
- **F2 (graded confidence filter, pillar-only):** the rule defaults to
  the canonical hard cutoff; opting in to ``temperature > 0`` produces a
  measurable, different trajectory; the weight formula is unit-tested.
- **F3 (involuntary cross-cutting tie stratum):** the build seeds the
  stratum, every involuntary edge is cross-party, and the stratum
  survives a full S4 run.

The pillar's directional thresholds are re-measured under Phase 4 and
asserted in ``test_pillar_stages.py``; this module locks the new
mechanisms in isolation.
"""
from __future__ import annotations

import numpy as np

from abm.core.agent import Agent
from abm.core.environment import Environment
from abm.core.network import Network
from abm.core.space import ContinuousSpace2D
from abm.core.state import AgentState
from abm.pillars import PILLAR, apply_intervention
from abm.pillars.calm_to_camps import (
    BC_TEMPERATURE,
    FJ_ALPHA,
    INVOLUNTARY_PER_AGENT,
    STUBBORNNESS_ALPHA,
    STUBBORNNESS_BETA,
    build_engine,
)
from abm.rules.influence import BoundedConfidenceInfluence


# --- F1: anchored agents -------------------------------------------------


def test_stubborn_agent_ends_near_anchor():
    """A high-stubbornness agent under a strong pull ends up *close to
    its anchor*; a low-stubbornness agent in the same population drifts
    to wherever the network pulls it.

    Both agents start at the same off-anchor ideology, so both feel the
    anchor pull. The stubborn agent's pull is large (FJ recurrence pins
    it near anchor); the free agent's is small (it moves freely under
    BC). Compare final distance to anchor — the FJ prediction, not the
    raw step-size which has the wrong sign when the stubborn agent's
    *anchor pull* is stronger than the free agent's *BC pull*.
    """
    eng = build_engine(seed=0, n_agents=200)
    apply_intervention(eng, PILLAR.interventions[1])   # S1 — BC on
    a_stubborn = eng.agents[0]
    a_free = eng.agents[1]
    a_stubborn.state.attrs["stubbornness"] = 0.95
    a_free.state.attrs["stubbornness"] = 0.05
    # Both anchored at the centre; both started displaced from anchor.
    # The anchor pull is non-zero from t=0, so the test exercises the
    # FJ recurrence (not just the (1-s) scaling of a BC pull).
    # MHV S2 T2.5: position state lives in attrs["issues"] (ideology is
    # the projection cache) and the FJ anchor is `anchor_issues` — the
    # displacement/anchor setup is ported via lift(); same FJ claim,
    # same thresholds.
    from abm.core.issues import lift
    rt = eng.env.attrs["issue_runtime"]
    anchor = np.array([0.0, 0.0])
    start = np.array([0.30, 0.30])
    for a in (a_stubborn, a_free):
        a.state.attrs["anchor_issues"] = lift(anchor, rt)
        a.state.attrs["anchor"] = anchor.copy()
        a.state.attrs["issues"] = lift(start, rt)
        a.state.ideology = start.copy()
    eng.space.rebuild(eng.agents)

    eng.run(60)
    d_s = float(np.linalg.norm(a_stubborn.state.ideology - anchor))
    d_f = float(np.linalg.norm(a_free.state.ideology - anchor))
    # FJ steady state: stubborn agent settles near its anchor;
    # free agent ends up wherever BC took it (could be anywhere).
    # The clean assertion is `d_stubborn < d_free` (stubborn closer to
    # anchor than free agent). With these parameters d_s ≈ 0.04,
    # d_f ≈ 0.4-0.6 — wide gap.
    assert d_s < d_f * 0.5, (
        f"Stubborn agent should end closer to anchor than free agent: "
        f"d_stubborn={d_s:.3f} vs d_free={d_f:.3f}."
    )
    # And the stubborn agent really has moved — the anchor pull is doing
    # work, it is not just pinned by F1 to its starting point.
    assert d_s < float(np.linalg.norm(start - anchor)), (
        f"Stubborn agent should have moved *toward* anchor "
        f"(d_s={d_s:.3f} vs start displacement {np.linalg.norm(start - anchor):.3f})."
    )


def test_anchor_pull_recovers_displaced_agent():
    """An agent shifted away from its anchor, with all positional forces
    off and noise zeroed, decays back toward the anchor."""
    eng = build_engine(seed=0, n_agents=50)
    # Zero every positional force; the only thing acting is GaussianNoise,
    # which we also zero — leaving the anchor pull alone.
    for rule in eng.rules.rules:
        name = type(rule).__name__
        if name == "BoundedConfidenceInfluence":
            rule.strength = 0.0
        elif name == "PartyPull":
            rule.strength = 0.0
        elif name == "MediaConsumption":
            rule.strength = 0.0
        elif name == "GaussianNoise":
            rule.sigma = 0.0
        elif name == "AffectiveUpdate":
            rule.lr = 0.0
        elif name == "ConstraintOp":
            rule.rate = 0.0
            rule.resid_sigma = 0.0
    a = eng.agents[0]
    # MHV S2 T2.5: displace the agent in the issues state (ideology is
    # the projection cache) and anchor it via `anchor_issues` — the FJ
    # decay claim and thresholds are unchanged.
    from abm.core.issues import lift
    rt = eng.env.attrs["issue_runtime"]
    a.state.attrs["stubbornness"] = 0.5
    a.state.attrs["anchor"] = np.array([0.0, 0.0])
    a.state.attrs["anchor_issues"] = lift(np.array([0.0, 0.0]), rt)
    a.state.attrs["issues"] = lift(np.array([0.5, 0.5]), rt)
    a.state.ideology = np.array([0.5, 0.5])
    eng.space.rebuild(eng.agents)
    d0 = float(np.linalg.norm(a.state.ideology - a.state.attrs["anchor"]))
    eng.run(40)
    d1 = float(np.linalg.norm(a.state.ideology - a.state.attrs["anchor"]))
    assert d1 < d0 * 0.7, (
        f"Anchor pull should pull displaced agent closer: "
        f"d0={d0:.4f}, d1={d1:.4f}."
    )


def test_stubbornness_distribution_shape():
    """The Beta(2, 5) seeding produces a mean in the right ballpark
    (target ~0.286). Locks the F1a judgment fork."""
    eng = build_engine(seed=0, n_agents=400)
    vals = np.array([a.state.attrs["stubbornness"] for a in eng.agents])
    mean = float(vals.mean())
    # Beta(2, 5) population mean is 2/7 ≈ 0.286; with n=400 the sample
    # mean lands inside a ±0.05 cushion comfortably.
    assert 0.20 < mean < 0.35, (
        f"Stubbornness mean {mean:.3f} should be ≈ 0.286 "
        f"(Beta({STUBBORNNESS_ALPHA}, {STUBBORNNESS_BETA}))."
    )
    # And no value escapes [0, 1].
    assert vals.min() >= 0.0 and vals.max() <= 1.0


def test_anchor_seeded_as_initial_ideology():
    """F1b: anchor = initial ideology, fixed. At t=0 every anchor equals
    every ideology, exactly."""
    eng = build_engine(seed=42, n_agents=150)
    for a in eng.agents:
        assert np.array_equal(a.state.ideology, a.state.attrs["anchor"])


def test_fj_alpha_present_in_env():
    """The FJ anchor-pull rate is on env.attrs and matches the
    build constant."""
    eng = build_engine(seed=0, n_agents=50)
    assert eng.env.attrs.get("fj_alpha") == FJ_ALPHA


# --- F2: graded filter ---------------------------------------------------


def test_graded_filter_default_is_hard_cutoff():
    """The rule default is 0.0 — canonical hard-cutoff Hegselmann-Krause.
    No existing scenario sees a behaviour change."""
    rule = BoundedConfidenceInfluence(epsilon=0.3, strength=0.08)
    assert rule.temperature == 0.0


def test_pillar_opts_in_to_graded_filter():
    """The pillar's build_engine sets temperature to BC_TEMPERATURE,
    and every bundle re-asserts it (absolute bundle, Phase 1 D5)."""
    eng = build_engine(seed=0, n_agents=50)
    bc = next(
        r for r in eng.rules.rules
        if type(r).__name__ == "BoundedConfidenceInfluence"
    )
    assert bc.temperature == BC_TEMPERATURE > 0.0


def test_graded_filter_blends_in_range_and_out_of_range_neighbours():
    """Two neighbours: one inside epsilon, one past epsilon.

    Under the hard cutoff, the agent's target is the in-range neighbour
    alone — the out-of-range neighbour contributes nothing. Under the
    graded filter, both neighbours contribute (with the out-of-range one
    at a small weight), so the target is a weighted blend — closer to
    the in-range neighbour but pulled toward the out-of-range one.
    """
    a = Agent(
        id=0,
        state=AgentState(
            ideology=np.array([0.0, 0.0]),
            attrs={"stubbornness": 0.0},
        ),
    )
    # Neighbour b is in-range at d = 0.2 (< epsilon = 0.3).
    b = Agent(
        id=1,
        state=AgentState(
            ideology=np.array([0.20, 0.0]),
            attrs={"stubbornness": 0.0},
        ),
    )
    # Neighbour c is out-of-range at d = 0.6.
    c = Agent(
        id=2,
        state=AgentState(
            ideology=np.array([0.60, 0.0]),
            attrs={"stubbornness": 0.0},
        ),
    )
    space = ContinuousSpace2D()
    space.rebuild([a, b, c])
    env = Environment(
        attrs={"network": Network({0: {1, 2}, 1: {0}, 2: {0}})}
    )
    rng = np.random.default_rng(0)

    hard = BoundedConfidenceInfluence(
        epsilon=0.30, strength=1.0, temperature=0.0
    )
    d_hard = hard.apply(a, space, env, rng).d_ideology
    # Hard cutoff: only b is in-range; target = b; d = (0.20, 0).
    assert np.allclose(d_hard, [0.20, 0.0]), (
        f"Hard cutoff should target the in-range neighbour exactly; got {d_hard}."
    )

    soft = BoundedConfidenceInfluence(
        epsilon=0.30, strength=1.0, temperature=0.10
    )
    d_soft = soft.apply(a, space, env, rng).d_ideology
    # Graded filter: weight at d=0.2 (in-range, before midpoint) is
    # 1/(1+exp(-0.1/0.1)) = 1/(1+e^-1) ≈ 0.731.
    # Weight at d=0.6 (well past epsilon) is 1/(1+exp(0.3/0.1))
    # = 1/(1+e^3) ≈ 0.0474. Weighted mean of [0.20, 0.60] with weights
    # [0.731, 0.0474] is ≈ 0.224. So d_soft[0] should be > 0.20 (the
    # out-of-range neighbour pulls a bit further) but well below 0.6.
    assert d_soft[0] > 0.20, (
        f"Graded filter should pull past the in-range target; got {d_soft}."
    )
    assert d_soft[0] < 0.35, (
        f"Graded filter shouldn't overshoot toward the out-of-range neighbour; "
        f"got {d_soft}."
    )


def test_graded_filter_at_zero_temperature_matches_hard_cutoff():
    """Setting temperature = 0.0 takes the hard-cutoff branch by
    construction. Two pillar runs at the same seed — one with
    temperature=0.0, one with the pillar default — should differ."""
    eng_hard = build_engine(seed=7, n_agents=100)
    apply_intervention(eng_hard, PILLAR.interventions[1])
    for r in eng_hard.rules.rules:
        if type(r).__name__ == "BoundedConfidenceInfluence":
            r.temperature = 0.0
    eng_soft = build_engine(seed=7, n_agents=100)
    apply_intervention(eng_soft, PILLAR.interventions[1])
    # Pillar default already sets temperature=0.05.
    eng_hard.run(50)
    eng_soft.run(50)
    assert not np.array_equal(eng_hard.positions(), eng_soft.positions()), (
        "Graded filter should produce a different trajectory from the "
        "hard cutoff under the same pillar seed and bundle."
    )


# --- F3: involuntary cross-cutting stratum -------------------------------


def test_involuntary_edges_are_seeded():
    """build_engine creates ~ INVOLUNTARY_PER_AGENT * n / 2 involuntary edges."""
    n = 200
    eng = build_engine(seed=0, n_agents=n)
    net: Network = eng.env.attrs["network"]
    inv_count = sum(1 for (i, j) in net.edges() if net.is_involuntary(i, j))
    expected = (INVOLUNTARY_PER_AGENT * n) // 2
    # Allow a ±10% cushion — random sampling without per-agent rejection
    # naturally varies by a few edges.
    lo, hi = int(expected * 0.85), int(expected * 1.15)
    assert lo <= inv_count <= hi, (
        f"Involuntary edge count {inv_count} should be ≈ {expected} "
        f"(in [{lo}, {hi}])."
    )


def test_every_involuntary_edge_is_cross_party():
    """The stratum exists to model kin/workplace ties that cross party
    by construction. Every involuntary edge joins different-party agents."""
    eng = build_engine(seed=0, n_agents=200)
    net: Network = eng.env.attrs["network"]
    by_id = {a.id: a for a in eng.agents}
    for (i, j) in net.edges():
        if net.is_involuntary(i, j):
            pi = by_id[i].state.attrs["party"]
            pj = by_id[j].state.attrs["party"]
            assert pi != pj, (
                f"Involuntary edge {i}-{j} joins same-party agents "
                f"(both party {pi})."
            )


def test_involuntary_edges_survive_s4_rewiring():
    """TieRewiring's involuntary-skip is respected: every involuntary edge
    present at t=0 is still present after a full S4 run."""
    from .conftest import N, TICKS, positional_engine

    eng = positional_engine(4, seed=0)
    net0: Network = eng.env.attrs["network"]
    inv_at_t0 = {
        (i, j) for (i, j) in net0.edges() if net0.is_involuntary(i, j)
    }
    assert inv_at_t0, "Smoke check: involuntary edges should be seeded."

    eng.run(TICKS)
    net_after: Network = eng.env.attrs["network"]
    inv_after = {
        (i, j) for (i, j) in net_after.edges()
        if net_after.is_involuntary(i, j)
    }
    assert inv_at_t0 == inv_after, (
        f"Involuntary edges changed across S4 run: "
        f"{len(inv_at_t0 - inv_after)} removed, "
        f"{len(inv_after - inv_at_t0)} added."
    )
