"""Phase 4 §13 — measure the structural ratchet gap.

Runs the existing test_pillar_stages._release_run paradigm: polarise through
S4, then release (drop polarising forces, reopen epsilon, freeze rewiring).
World A keeps its evolved homophilous network; World B has it replaced by
a homophily-free random graph of matched mean degree. The ratchet claim:
World A stays apart; World B re-merges.
"""
from __future__ import annotations

import numpy as np

from abm.core.network import Network
from abm.pillars import PILLAR, apply_intervention
from abm.pillars.calm_to_camps import build_engine

N = 250
TICKS = 200
RELEASE_TICKS = TICKS
RELEASE_EPSILON = 1.0
SEEDS = tuple(range(12))


def positional(stage: int, seed: int):
    eng = build_engine(seed=seed, n_agents=N)
    apply_intervention(eng, PILLAR.interventions[stage])
    for r in eng.rules.rules:
        if type(r).__name__ == "AffectiveUpdate":
            r.lr = 0.0
    return eng


def party_sep(eng):
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    return float(
        np.linalg.norm(pos[parties == 0].mean(axis=0) - pos[parties == 1].mean(axis=0))
    )


def random_graph_matched_degree(node_ids, mean_degree, rng):
    ids = list(node_ids)
    n = len(ids)
    target_edges = (n * mean_degree) // 2
    adjacency = {i: set() for i in ids}
    placed = 0
    while placed < target_edges:
        i, j = int(rng.integers(n)), int(rng.integers(n))
        if i == j or ids[j] in adjacency[ids[i]]:
            continue
        adjacency[ids[i]].add(ids[j])
        adjacency[ids[j]].add(ids[i])
        placed += 1
    return Network(adjacency)


def release_run(seed, swap_network):
    eng = positional(4, seed)
    eng.run(TICKS)
    for r in eng.rules.rules:
        name = type(r).__name__
        if name == "PartyPull":
            r.strength = 0.0
        elif name == "MediaConsumption":
            r.strength = 0.0
        elif name == "BoundedConfidenceInfluence":
            r.epsilon = RELEASE_EPSILON
    for r in eng.env_rules:
        if type(r).__name__ == "TieRewiring":
            r.rewire_rate = 0.0
    if swap_network:
        net = eng.env.attrs["network"]
        n = len(eng.agents)
        m = sum(net.degree(a.id) for a in eng.agents)
        mean_degree = max(1, m // n)
        rng = np.random.default_rng(seed + 12345)
        eng.env.attrs["network"] = random_graph_matched_degree(
            [a.id for a in eng.agents], mean_degree, rng
        )
    eng.run(RELEASE_TICKS)
    return party_sep(eng)


def main():
    print(f"Ratchet release experiment — N={N}, TICKS={TICKS}, seeds=0..{SEEDS[-1]}")
    sep_a, sep_b = [], []
    for seed in SEEDS:
        a = release_run(seed, swap_network=False)
        b = release_run(seed, swap_network=True)
        sep_a.append(a)
        sep_b.append(b)
        print(f"  seed={seed}  A={a:.3f}  B={b:.3f}  gap={a - b:+.3f}")
    print(f"\nWorld A (kept evolved homophilous graph): mean sep = {np.mean(sep_a):.3f}")
    print(f"World B (matched-degree random graph):    mean sep = {np.mean(sep_b):.3f}")
    print(f"Gap (A - B):                              {np.mean(sep_a) - np.mean(sep_b):+.3f}")


if __name__ == "__main__":
    main()
