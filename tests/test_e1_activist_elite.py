"""E1 isolation guard — the endogenous activist-elite loop.

Stands the `ActivistEliteCue` rule up on a clean 2D substrate (compass_basic
style — no issues, no fed series) and proves it produces *emergent* partial
bipolarization from a tiny seed, with nothing positional fed. The contrast test
(loop OFF -> fizzle) shows the loop is what drives the sorting. Parameters here
are illustrative (in the E0 realistic regime); the shipped calibration is E4.
"""
from __future__ import annotations

import numpy as np

from abm.core.agent import Agent
from abm.core.engine import Engine
from abm.core.environment import Environment
from abm.core.network import Network
from abm.core.rules import RulePipeline
from abm.core.space import ContinuousSpace2D
from abm.core.state import AgentState
from abm.rules.activist_elite import ActivistEliteCue
from abm.rules.noise import GaussianNoise
from abm.rules.party_pull import PartyPull


def _build(n=250, seed=0, *, with_elite=True, gain=2.5, ceiling=0.65, tail_q=0.10,
           party_pull=0.24, fj_alpha=0.17, sigma_cue=0.34, noise=0.012,
           seed_asym=0.05):
    rng = np.random.default_rng(seed)
    party = rng.integers(0, 2, size=n)
    cent = {0: np.array([-seed_asym, 0.0]), 1: np.array([seed_asym, 0.0])}
    agents = []
    for i in range(n):
        p = int(party[i])
        pos = np.clip(cent[p] + rng.normal(0.0, 0.30, size=2), -1.0, 1.0)
        offset = rng.normal(0.0, sigma_cue, size=2)
        agents.append(Agent(id=i, state=AgentState(
            ideology=pos.copy(),
            attrs={
                "party": p, "group": p,
                "identity_strength": float(rng.beta(2.0, 2.0)),
                "stubbornness": float(rng.beta(2.0, 5.0)),
                "fj_alpha": fj_alpha,
                "anchor": pos.copy(),
                "origin": pos.copy(),
                "party_cue": np.clip(cent[p] + offset, -1.0, 1.0),
            })))
    env = Environment(attrs={
        "network": Network.complete(range(n)),
        "parties": {0: cent[0].copy(), 1: cent[1].copy()},
    })
    space = ContinuousSpace2D(bounds=((-1.0, 1.0), (-1.0, 1.0)))
    rules = RulePipeline([PartyPull(strength=party_pull), GaussianNoise(sigma=noise)])
    env_rules = [ActivistEliteCue(tail_q=tail_q, gain=gain, ceiling=ceiling)] \
        if with_elite else []
    return Engine(agents=agents, env=env, space=space, rules=rules,
                  env_rules=env_rules, seed=seed)


def _metrics(eng) -> dict:
    pos = eng.positions()
    party = eng.attr_array("party")
    sep = float(np.linalg.norm(pos[party == 0].mean(0) - pos[party == 1].mean(0)))
    wp_sd = float(np.mean([pos[party == p].std(0).mean() for p in (0, 1)]))
    corner = float(np.mean(np.any(np.abs(pos) > 0.9, axis=1)))
    parties = eng.env.attrs["parties"]
    elite_sep = float(np.linalg.norm(np.asarray(parties[0]) - np.asarray(parties[1])))
    return dict(sep=sep, wp_sd=wp_sd, corner=corner, elite_sep=elite_sep,
                gap=elite_sep - sep)


def test_emergent_bipolarization():
    """The loop amplifies a tiny 0.1 seed into realistic, stable, PARTIAL
    bipolarization — nothing positional fed."""
    res, sep0s = [], []
    for s in (0, 1, 2):
        eng = _build(seed=s, with_elite=True)
        sep0s.append(_metrics(eng)["sep"])
        eng.run(135)
        res.append(_metrics(eng))
    sep0 = float(np.mean(sep0s))
    sep = float(np.mean([r["sep"] for r in res]))
    wp_sd = float(np.mean([r["wp_sd"] for r in res]))
    corner = float(np.mean([r["corner"] for r in res]))
    gap = float(np.mean([r["gap"] for r in res]))
    assert sep0 < 0.25, f"seed should start near-symmetric; sep0={sep0:.3f}"
    assert 0.85 <= sep <= 1.35, f"emergent sep out of realistic range: {sep:.3f}"
    assert 0.18 <= wp_sd <= 0.45, f"within-party SD out of band: {wp_sd:.3f}"
    assert corner < 0.10, f"corner runaway: {corner:.2%}"
    assert gap > 0.0, f"mass should lag elite (emergent gap>0); gap={gap:.3f}"


def test_loop_is_necessary():
    """Without the activist-elite rule the cue stays fixed near origin → no
    emergent separation. Proves the loop drives the sorting (isolation)."""
    seps = []
    for s in (0, 1, 2):
        eng = _build(seed=s, with_elite=False)
        eng.run(135)
        seps.append(_metrics(eng)["sep"])
    sep = float(np.mean(seps))
    assert sep < 0.45, f"no-loop baseline should fizzle; got sep={sep:.3f}"


def test_elite_leads_mass():
    """Elites are MORE extreme than the mass they emerge from (the activist-tail
    leverage): elite separation exceeds mass separation."""
    eng = _build(seed=0, with_elite=True)
    eng.run(135)
    m = _metrics(eng)
    assert m["elite_sep"] > m["sep"] > 0.5, (
        f"elite should lead mass; elite_sep={m['elite_sep']:.3f} sep={m['sep']:.3f}")
