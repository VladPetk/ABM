"""R-phase R3 isolation test — cross-cutting (bridge) tie formation (gated).

With probability `p_bridge_rewire`, a rewiring agent forms its NEW tie to a
cross-party "bridge" (closest cross-party candidate, flagged cooperative so the
R1 warming path can fire) instead of the homophilous closest. Default 0.0 → no
bridge and no extra rng draw → byte-identical.
See docs/internal/reversibility_spec.md (R3).
"""
from __future__ import annotations

import numpy as np

from abm.core.agent import Agent
from abm.core.environment import Environment
from abm.core.network import Network
from abm.core.space import ContinuousSpace2D
from abm.core.state import AgentState
from abm.pillars.historical_arc import build_engine
from abm.rules.tie_rewiring import TieRewiring
from scripts.anes_preset import ANES_FULL_KWARGS


def _world(n_per_party=4):
    """A homophilous ring: each agent tied to one same-party neighbour, with
    cross-party agents available as non-neighbours to bridge to."""
    agents = []
    adj = {}
    rng = np.random.default_rng(0)
    for p in (0, 1):
        for k in range(n_per_party):
            i = p * n_per_party + k
            # same-party agents cluster near their pole; positions distinct
            x = (0.4 if p == 0 else -0.4) + 0.02 * k
            agents.append(Agent(id=i, state=AgentState(
                ideology=np.array([x, 0.0], dtype=float),
                attrs={"party": p, "social_coord": 0.1 * k,
                       "affect": {1 - p: -0.2}, "stubbornness": 0.0})))
    # one voluntary same-party tie per agent (ring within party)
    for p in (0, 1):
        base = p * n_per_party
        for k in range(n_per_party):
            i, j = base + k, base + (k + 1) % n_per_party
            adj.setdefault(i, set()).add(j)
            adj.setdefault(j, set()).add(i)
    net = Network(adj)
    space = ContinuousSpace2D()
    space.rebuild(agents)
    env = Environment(attrs={"network": net})
    return agents, space, env, net


def _run(p_bridge, seed=1, ticks=3):
    agents, space, env, net = _world()
    rule = TieRewiring(rewire_rate=1.0, n_candidates=10, p_bridge_rewire=p_bridge)
    rng = np.random.default_rng(seed)
    for t in range(ticks):
        rule.apply(env, agents, space, rng, t)
    party = {a.id: a.state.attrs["party"] for a in agents}
    coop = list(net._cooperative)
    return net, coop, party


def test_off_path_forms_no_cooperative_bridges():
    """p_bridge_rewire=0 → homophily only → no cooperative edges ever created."""
    _, coop, _ = _run(p_bridge=0.0)
    assert coop == []


def test_on_path_forms_cross_party_cooperative_bridges():
    """p_bridge_rewire=1 → every new tie targets a cross-party bridge, flagged
    cooperative. At least one cross-party cooperative edge must appear."""
    _, coop, party = _run(p_bridge=1.0)
    assert coop, "expected cross-party cooperative bridges to form"
    for (i, j) in coop:
        assert party[i] != party[j], f"bridge {(i, j)} is not cross-party"


def test_off_path_is_deterministic():
    """Two off-path runs with the same seed are identical (rng stream unchanged
    — the bridge branch short-circuits before any extra draw)."""
    net_a, _, _ = _run(p_bridge=0.0, seed=7)
    net_b, _, _ = _run(p_bridge=0.0, seed=7)
    assert net_a.adjacency == net_b.adjacency


def _tie_rule(eng):
    rs = [r for r in eng.env_rules if type(r).__name__ == "TieRewiring"]
    assert rs, "TieRewiring not in env_rules"
    return rs[0]


def test_build_off_bridge_zero():
    eng = build_engine(seed=0, **ANES_FULL_KWARGS)
    assert _tie_rule(eng).p_bridge_rewire == 0.0


def test_build_on_passes_bridge():
    k = dict(ANES_FULL_KWARGS)
    k.update(bridge_rewire=0.3)
    eng = build_engine(seed=0, **k)
    assert _tie_rule(eng).p_bridge_rewire == 0.3
