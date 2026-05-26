"""Unit tests for the ``Network`` class (ADR-001 substrate).

Pure data-structure tests on the graph object itself, plus an end-to-end
HK-equivalence check: bounded-confidence on a complete-graph ``Network``
should produce the same clustering verdict as the canonical mean-field
Hegselmann-Krause rule — ADR-001 §7's rigor claim, at unit-test scale.
"""
from __future__ import annotations

import numpy as np

from abm.core.agent import Agent
from abm.core.network import Network, generate_homophilous_network
from abm.core.state import AgentState
from abm.metrics.polarization import variance
from abm.scenarios.compass_basic import build as build_compass


# --- Network: complete graph ---------------------------------------------

def test_complete_has_full_degree():
    net = Network.complete(range(5))
    for i in range(5):
        assert net.degree(i) == 4
        assert i not in net.neighbors(i)
    # n*(n-1)/2 unique undirected edges.
    assert len(list(net.edges())) == 10


def test_complete_is_symmetric():
    net = Network.complete(range(6))
    for (i, j) in net.edges():
        assert i < j
        assert j in net.neighbors(i)
        assert i in net.neighbors(j)


# --- Network: homophilous wrapper ----------------------------------------

def _make_agents(n: int, rng: np.random.Generator) -> list[Agent]:
    """Toy agents carrying the attrs the homophilous generator reads."""
    agents = []
    for i in range(n):
        pos = rng.uniform(-1.0, 1.0, size=2)
        agents.append(
            Agent(
                id=i,
                state=AgentState(
                    ideology=pos,
                    attrs={"social_coord": float(rng.uniform(-1.0, 1.0))},
                ),
            )
        )
    return agents


def test_homophilous_is_symmetric():
    rng = np.random.default_rng(0)
    agents = _make_agents(40, rng)
    net = Network.homophilous(agents, rng)
    for (i, j) in net.edges():
        assert j in net.neighbors(i)
        assert i in net.neighbors(j)


def test_homophilous_wraps_generator_adjacency():
    rng = np.random.default_rng(0)
    agents = _make_agents(20, rng)
    raw = generate_homophilous_network(agents, np.random.default_rng(0))
    wrapped = Network(
        generate_homophilous_network(agents, np.random.default_rng(0))
    )
    for i in range(20):
        assert raw[i] == wrapped.neighbors(i)


# --- Network: edge add / remove + involuntary stratum --------------------

def test_add_remove_edge_round_trip():
    net = Network({0: set(), 1: set(), 2: set()})
    net.add_edge(0, 1)
    assert net.has_edge(0, 1) and net.has_edge(1, 0)
    assert net.degree(0) == 1 and net.degree(1) == 1
    net.remove_edge(0, 1)
    assert not net.has_edge(0, 1)
    assert net.degree(0) == 0


def test_involuntary_edges_are_marked_and_cleared():
    net = Network({0: set(), 1: set(), 2: set()})
    net.add_edge(0, 1, involuntary=True)
    net.add_edge(1, 2)  # voluntary
    assert net.is_involuntary(0, 1)
    assert net.is_involuntary(1, 0)         # canonicalisation
    assert not net.is_involuntary(1, 2)
    net.remove_edge(0, 1)
    assert not net.is_involuntary(0, 1)


def test_cooperative_edges_are_marked_independently_of_involuntary():
    """Phase 7: an edge can be cooperative without being involuntary,
    or both (X6's added ties), or neither (the default)."""
    net = Network({0: set(), 1: set(), 2: set(), 3: set()})
    net.add_edge(0, 1, involuntary=True, cooperative=True)    # X6-style
    net.add_edge(1, 2, involuntary=True, cooperative=False)   # F3-style
    net.add_edge(2, 3, involuntary=False, cooperative=True)   # cooperative voluntary (hypothetical)
    assert net.is_involuntary(0, 1) and net.is_cooperative(0, 1)
    assert net.is_involuntary(1, 2) and not net.is_cooperative(1, 2)
    assert not net.is_involuntary(2, 3) and net.is_cooperative(2, 3)
    # Symmetric.
    assert net.is_cooperative(1, 0)
    assert not net.is_cooperative(3, 2) is False  # i.e. is_cooperative(3, 2) is True
    # Removal clears both flags.
    net.remove_edge(0, 1)
    assert not net.is_involuntary(0, 1) and not net.is_cooperative(0, 1)


def test_cooperative_initializer_accepts_explicit_set():
    """Network constructor accepts an explicit cooperative-edge set."""
    net = Network(
        {0: {1}, 1: {0}},
        involuntary={(0, 1)},
        cooperative={(0, 1)},
    )
    assert net.is_involuntary(0, 1)
    assert net.is_cooperative(0, 1)


def test_edges_yields_each_edge_once():
    net = Network({0: {1, 2}, 1: {0, 2}, 2: {0, 1}})
    assert sorted(net.edges()) == [(0, 1), (0, 2), (1, 2)]


# --- HK equivalence on a complete graph (ADR-001 §7) ---------------------

def test_hk_loose_epsilon_complete_graph_converges():
    """Loose epsilon on a complete graph -> single consensus, same as classic HK."""
    eng = build_compass(
        n_agents=80, epsilon=2.0, attraction=0.08,
        repulsion=0.0, noise=0.01, seed=0,
    )
    eng.run(200)
    assert variance(eng.positions()) < 0.05


def test_hk_tight_epsilon_complete_graph_fragments():
    """Tight epsilon on a complete graph -> persistent fragmentation, same as classic HK."""
    eng = build_compass(
        n_agents=80, epsilon=0.15, attraction=0.08,
        repulsion=0.0, noise=0.01, seed=0,
    )
    eng.run(200)
    assert variance(eng.positions()) > 0.30
