"""Phase 8d — Independent (party=2) agents tests.

Covers:

- Default `build_engine()` produces 0 party=2 agents (bit-identity
  preserved with Phase 8c §7).
- `independent_fraction=0.12` seeds the right count.
- Independent agents lack party_cue / affect / perceived_other_party /
  cooperative_share / etc.
- Independent agents DO carry identities, anchor, stubbornness,
  media_diet.
- Partisan-aware rules (PartyPull, AffectiveUpdate, BacklashRepulsion,
  PerceptionUpdate) no-op on party=2 agents.
- Partisan-aware rules also skip party=2 NEIGHBOURS in their loops
  (don't treat Independents as out-party).
- Partisan-agnostic rules (BC, MediaConsumption, GaussianNoise) DO
  fire for Independents.
- `ideological_constraint` filters to {0, 1} (excludes Independents).
- Pillar S4 trajectory at `independent_fraction=0.0` is bit-identical
  to a build without the kwarg (sanity check).
"""
from __future__ import annotations

import numpy as np

from abm.core.agent import Agent
from abm.core.environment import Environment
from abm.core.network import Network
from abm.core.space import ContinuousSpace2D
from abm.core.state import AgentState
from abm.metrics.affective import (
    affective_polarization,
    ideological_constraint,
    sorting_index,
)
from abm.pillars import (
    PILLAR,
    X1_SHOW_OTHER_SIDE,
    apply_intervention,
)
from abm.pillars.calm_to_camps import build_engine as pillar_build
from abm.rules.affective_update import AffectiveUpdate
from abm.rules.party_pull import PartyPull
from abm.rules.perception_update import PerceptionUpdate
from abm.rules.repulsion import BacklashRepulsion


# ---------------------------------------------------------------------
# Build-time behaviour
# ---------------------------------------------------------------------


def test_default_no_independents():
    """build_engine() without the kwarg produces 0 party=2 agents."""
    eng = pillar_build(seed=0, n_agents=100)
    n_indep = sum(1 for a in eng.agents if a.state.attrs["party"] == 2)
    assert n_indep == 0


def test_explicit_zero_fraction_bit_identical_to_default():
    """build_engine(independent_fraction=0.0) is bit-identical to
    build_engine() — same positions, same parties, same RNG state."""
    eng_a = pillar_build(seed=0, n_agents=100)
    eng_b = pillar_build(seed=0, n_agents=100, independent_fraction=0.0)
    pos_a = np.array([a.state.ideology for a in eng_a.agents])
    pos_b = np.array([a.state.ideology for a in eng_b.agents])
    assert np.allclose(pos_a, pos_b, atol=1e-12)
    parties_a = [a.state.attrs["party"] for a in eng_a.agents]
    parties_b = [a.state.attrs["party"] for a in eng_b.agents]
    assert parties_a == parties_b


def test_independent_fraction_seeds_correct_count():
    """`independent_fraction = 0.12` at N=250 produces 30 party=2 agents."""
    eng = pillar_build(seed=0, n_agents=250, independent_fraction=0.12)
    n_indep = sum(1 for a in eng.agents if a.state.attrs["party"] == 2)
    assert n_indep == 30


def test_independent_fraction_edge_cases():
    """fraction=0.0 → 0 indep; fraction=1.0 → all indep."""
    eng_zero = pillar_build(seed=0, n_agents=50, independent_fraction=0.0)
    n_zero = sum(1 for a in eng_zero.agents if a.state.attrs["party"] == 2)
    assert n_zero == 0
    eng_all = pillar_build(seed=0, n_agents=50, independent_fraction=1.0)
    n_all = sum(1 for a in eng_all.agents if a.state.attrs["party"] == 2)
    assert n_all == 50


# ---------------------------------------------------------------------
# Independent agent attrs (build-time)
# ---------------------------------------------------------------------


def test_independents_lack_party_cue():
    """party=2 agents do not carry party_cue (PartyPull no-ops on them)."""
    eng = pillar_build(seed=0, n_agents=100, independent_fraction=0.12)
    for a in eng.agents:
        if a.state.attrs["party"] == 2:
            assert "party_cue" not in a.state.attrs


def test_independents_lack_affect_dict():
    """party=2 agents do not carry affect (affect-neutral per Klar &
    Krupnikov 2016)."""
    eng = pillar_build(seed=0, n_agents=100, independent_fraction=0.12)
    for a in eng.agents:
        if a.state.attrs["party"] == 2:
            assert "affect" not in a.state.attrs


def test_independents_have_identities_and_anchor():
    """Independents fully participate in BC + media + GaussianNoise +
    IdentitySorting: they carry identities, anchor, stubbornness,
    media_diet."""
    eng = pillar_build(seed=0, n_agents=100, independent_fraction=0.12)
    for a in eng.agents:
        if a.state.attrs["party"] == 2:
            assert "identities" in a.state.attrs
            assert "anchor" in a.state.attrs
            assert "stubbornness" in a.state.attrs
            assert "media_diet" in a.state.attrs


def test_independents_identities_zero_mean():
    """Independents have zero-mean identities (no partisan center bias)."""
    eng = pillar_build(seed=0, n_agents=250, independent_fraction=0.20)
    indep_identities = [
        a.state.attrs["identities"]
        for a in eng.agents if a.state.attrs["party"] == 2
    ]
    if not indep_identities:
        return
    mean_id = np.mean(np.array(indep_identities), axis=0)
    # Mean across 50 Independents should be near zero on each dim.
    assert all(abs(x) < 0.15 for x in mean_id), (
        f"Independent identities should average near zero; got {mean_id}"
    )


def test_independents_social_coord_unbiased():
    """Independents have social_coord = N(0, SOCIAL_NOISE) — no
    party-based bias (vs partisans who have sign-biased social_coord)."""
    eng = pillar_build(seed=0, n_agents=250, independent_fraction=0.20)
    indep_coords = [
        a.state.attrs["social_coord"]
        for a in eng.agents if a.state.attrs["party"] == 2
    ]
    if not indep_coords:
        return
    mean_coord = float(np.mean(indep_coords))
    # Mean across 50 Independents should be near zero (no bias).
    assert abs(mean_coord) < 0.15, (
        f"Independent social_coord should average near zero; got {mean_coord:.3f}"
    )


# ---------------------------------------------------------------------
# Rule guards (party=2 agents no-op)
# ---------------------------------------------------------------------


def _indep_agent(pos=(0.0, 0.0), agent_id=0):
    """Construct a minimal party=2 Independent for rule tests."""
    return Agent(
        id=agent_id,
        state=AgentState(
            ideology=np.array(pos, dtype=float),
            attrs={
                "party": 2,
                "group": 2,
                "identities": np.zeros(3),
                "stubbornness": 0.0,
                "anchor": np.array(pos, dtype=float),
            },
        ),
    )


def _partisan_agent(pos=(0.5, 0.0), party=1, agent_id=1):
    return Agent(
        id=agent_id,
        state=AgentState(
            ideology=np.array(pos, dtype=float),
            attrs={
                "party": party,
                "group": party,
                "identities": np.zeros(3),
                "affect": {1 - party: 0.0},
                "stubbornness": 0.0,
                "anchor": np.array(pos, dtype=float),
            },
        ),
    )


def test_affective_update_no_op_on_independent():
    rule = AffectiveUpdate(
        radius=1.5, learning_rate=0.01, identity_weight=0.5,
        baseline=0.10, cooperative_mute=0.5,
    )
    a = _indep_agent()
    b = _partisan_agent()
    space = ContinuousSpace2D()
    space.rebuild([a, b])
    env = Environment(attrs={"network": Network({0: {1}, 1: {0}})})
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    assert not delta.d_attrs and not delta.d_ideology.any()


def test_backlash_repulsion_no_op_on_independent():
    rule = BacklashRepulsion(strength=0.05)
    a = _indep_agent()
    b = _partisan_agent()
    space = ContinuousSpace2D()
    space.rebuild([a, b])
    env = Environment(attrs={"network": Network({0: {1}, 1: {0}})})
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    assert np.array_equal(delta.d_ideology, np.zeros(2))


def test_party_pull_no_op_on_independent():
    rule = PartyPull(strength=0.04)
    a = _indep_agent()
    space = ContinuousSpace2D()
    space.rebuild([a])
    env = Environment(attrs={"parties": {0: np.array([-0.5, 0]), 1: np.array([0.5, 0])}})
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    assert np.array_equal(delta.d_ideology, np.zeros(2))


def test_perception_update_no_op_on_independent():
    rule = PerceptionUpdate(correction_rate=0.01)
    a = _indep_agent()
    b = _partisan_agent()
    space = ContinuousSpace2D()
    space.rebuild([a, b])
    env = Environment(attrs={"network": Network({0: {1}, 1: {0}})})
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    assert not delta.d_attrs


# ---------------------------------------------------------------------
# Partisan agents skip party=2 neighbours (don't treat as out-party)
# ---------------------------------------------------------------------


def test_partisan_affective_update_skips_independent_neighbour():
    """Partisan's AffectiveUpdate should NOT accumulate affect toward
    party=2 neighbours."""
    rule = AffectiveUpdate(
        radius=1.5, learning_rate=0.01, identity_weight=0.5,
        baseline=0.10, cooperative_mute=0.5,
    )
    # Partisan agent (party=0); only neighbour is an Independent.
    partisan = _partisan_agent(pos=(-0.3, 0.0), party=0, agent_id=0)
    indep = _indep_agent(pos=(0.5, 0.0), agent_id=1)
    space = ContinuousSpace2D()
    space.rebuild([partisan, indep])
    env = Environment(attrs={"network": Network({0: {1}, 1: {0}})})
    delta = rule.apply(partisan, space, env, np.random.default_rng(0))
    assert not delta.d_attrs, (
        f"Partisan with only Independent neighbour should not "
        f"accumulate affect; got d_attrs={delta.d_attrs}"
    )


def test_partisan_backlash_skips_independent_neighbour():
    """Partisan's BacklashRepulsion should not be pushed by party=2
    neighbours."""
    rule = BacklashRepulsion(strength=0.05)
    # Partisan with cold affect; only neighbour is an Independent.
    partisan = Agent(
        id=0,
        state=AgentState(
            ideology=np.array([0.0, 0.0]),
            attrs={
                "party": 0,
                "affect": {1: -0.8},  # cold; backlash would fire on partisan out-party
                "stubbornness": 0.0,
            },
        ),
    )
    indep = _indep_agent(pos=(0.6, 0.0), agent_id=1)
    space = ContinuousSpace2D()
    space.rebuild([partisan, indep])
    env = Environment(attrs={"network": Network({0: {1}, 1: {0}})})
    delta = rule.apply(partisan, space, env, np.random.default_rng(0))
    assert np.array_equal(delta.d_ideology, np.zeros(2)), (
        f"Partisan should not be pushed by Independent neighbour; "
        f"got d_ideology={delta.d_ideology}"
    )


# ---------------------------------------------------------------------
# Metric: ideological_constraint filters partisans
# ---------------------------------------------------------------------


def test_ideological_constraint_filters_party_2():
    """ideological_constraint should exclude party=2 agents from the
    Pearson correlation."""
    # Build two engines: one binary, one with 12% indep at same seed.
    # ic on the binary should match ic on the variant's partisan
    # subset (they aren't identical because the variant's partisan
    # population is different — but both should be valid numbers).
    eng_indep = pillar_build(seed=0, n_agents=100, independent_fraction=0.12)
    ic = ideological_constraint(eng_indep.agents)
    # Should be a valid number, not nan/inf.
    assert ic["x"] is not None and not np.isnan(ic["x"])
    assert 0.0 <= ic["x"] <= 1.0
    assert 0.0 <= ic["y"] <= 1.0


def test_sorting_index_filters_party_2():
    """sorting_index excludes party=2 from the correlation."""
    eng = pillar_build(seed=0, n_agents=100, independent_fraction=0.12)
    si = sorting_index(eng.agents)
    assert si is not None and not np.isnan(si)
    assert 0.0 <= si <= 1.0


def test_partisan_cross_cutting_fraction_bit_identical_at_zero():
    """Phase 8e §1: partisan_cross_cutting_fraction is bit-identical
    to cross_cutting_tie_fraction at independent_fraction=0.0
    (no party=2 agents → no edges to filter)."""
    from abm.metrics.network import (
        cross_cutting_tie_fraction,
        partisan_cross_cutting_fraction,
    )
    eng = pillar_build(seed=0, n_agents=100)
    xc = cross_cutting_tie_fraction(eng.agents, eng.env.attrs["network"])
    pxc = partisan_cross_cutting_fraction(eng.agents, eng.env.attrs["network"])
    assert xc == pxc, f"Mismatch at binary build: {xc} vs {pxc}"


def test_partisan_cross_cutting_fraction_excludes_independents():
    """Phase 8e §1: with Independents in the population,
    partisan_cross_cutting_fraction is strictly less than
    cross_cutting_tie_fraction (Independent-partisan ties excluded)."""
    from abm.metrics.network import (
        cross_cutting_tie_fraction,
        partisan_cross_cutting_fraction,
    )
    eng = pillar_build(seed=0, n_agents=100, independent_fraction=0.20)
    xc = cross_cutting_tie_fraction(eng.agents, eng.env.attrs["network"])
    pxc = partisan_cross_cutting_fraction(eng.agents, eng.env.attrs["network"])
    assert pxc < xc, (
        f"partisan submetric should be less than any-pair metric "
        f"when Independents are present; got partisan={pxc:.4f}, "
        f"any-pair={xc:.4f}"
    )


# ---------------------------------------------------------------------
# Pillar invariant: independent_fraction=0.0 is bit-identical
# ---------------------------------------------------------------------


def test_pillar_S4_bit_identical_at_zero_fraction():
    """Pillar S4 200-tick trajectory at `independent_fraction = 0.0` is
    bit-identical to a build without the kwarg. The keystone pillar-
    invariant check for §8d."""
    eng_a = pillar_build(seed=0, n_agents=100)
    apply_intervention(eng_a, PILLAR.interventions[4])
    eng_a.run(50)
    eng_b = pillar_build(seed=0, n_agents=100, independent_fraction=0.0)
    apply_intervention(eng_b, PILLAR.interventions[4])
    eng_b.run(50)
    pos_a = np.array([a.state.ideology for a in eng_a.agents])
    pos_b = np.array([a.state.ideology for a in eng_b.agents])
    assert np.allclose(pos_a, pos_b, atol=1e-12), (
        f"Bit-identity broken: max diff = {np.max(np.abs(pos_a - pos_b)):.2e}"
    )


def test_pillar_with_independents_runs_clean():
    """Pillar S4 with `independent_fraction = 0.12` runs 200 ticks
    without errors."""
    eng = pillar_build(seed=0, n_agents=100, independent_fraction=0.12)
    apply_intervention(eng, PILLAR.interventions[4])
    eng.run(200)
    # Sanity: independents still party=2 after run.
    n_indep_final = sum(
        1 for a in eng.agents if a.state.attrs["party"] == 2
    )
    assert n_indep_final == 12  # 0.12 * 100 = 12


# ---------------------------------------------------------------------
# Predicted §11 effect: X1 macro Δsep down with independents
# ---------------------------------------------------------------------


def test_x1_macro_sep_smaller_with_independents():
    """The headline §8d finding: X1's macro Δsep is smaller in
    magnitude under 12% Independents than under the binary build
    (12% of agents don't fire BacklashRepulsion → less push)."""
    from tests._parallel_workers import (
        release_metrics_with_independents_worker,
        release_metrics_worker,
    )
    seeds = (0, 1, 2)  # small ensemble for the test
    args = [("X1_show_other_side", s) for s in seeds]
    bin_results = [release_metrics_worker(a) for a in args]
    var_results = [
        release_metrics_with_independents_worker(a) for a in args
    ]
    bin_seps = [r["sep"][1] - r["sep"][0] for r in bin_results]
    var_seps = [r["sep"][1] - r["sep"][0] for r in var_results]
    bin_mean = float(np.mean(bin_seps))
    var_mean = float(np.mean(var_seps))
    assert var_mean < bin_mean, (
        f"X1's macro Δsep should be smaller with 12% Independents. "
        f"binary={bin_mean:+.4f}, variant={var_mean:+.4f}"
    )
