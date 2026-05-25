"""Shared constants, helpers, and session-scoped ensembles for the suite.

Each expensive ensemble (S0/S1 variance pairs, S2/S3 positional engines, the
three HK epsilon sweeps) is computed exactly once per `pytest` invocation
and shared across the tests that reuse it.
"""
from __future__ import annotations

import numpy as np
import pytest

from abm.core.outlets import US_MEDIA_OUTLETS_2024, diet_target
from abm.metrics.affective import ideological_constraint
from abm.metrics.polarization import variance
from abm.pillars import PILLAR, apply_intervention, build_at_stage
from abm.pillars.calm_to_camps import build_engine as build_pillar_engine
from abm.scenarios.compass_basic import build as build_compass


def party_separation(engine) -> float:
    """Distance between the two parties' mean ideology positions —
    the headline ratchet-test metric (phase3 spec §9)."""
    parties = np.array([a.state.attrs["party"] for a in engine.agents])
    pos = engine.positions()
    return float(
        np.linalg.norm(pos[parties == 0].mean(axis=0) - pos[parties == 1].mean(axis=0))
    )

# Ensemble sizes (Phase 1 D4).
STAGE_SEEDS = tuple(range(12))
HK_SEEDS = tuple(range(6))

# N = 250 keeps the suite fast; thresholds were re-measured here.
N = 250
TICKS = 200

HK_N = 200

OUTLETS_BY_ID = {o.id: o for o in US_MEDIA_OUTLETS_2024}


# --- general helpers ------------------------------------------------------

def constraint_avg(engine) -> float:
    """Mean of x and y ideological constraint (party-issue |Pearson r|)."""
    ic = ideological_constraint(engine.agents)
    return (ic["x"] + ic["y"]) / 2.0


def diet_extremity(agent) -> float:
    """How partisan an agent's media diet is — distance of its diet's
    weighted-mean outlet position from the centre."""
    return float(
        np.linalg.norm(diet_target(agent.state.attrs["media_diet"], OUTLETS_BY_ID))
    )


def positional_engine(stage_index: int, seed: int):
    """build_at_stage at the test N, then zero AffectiveUpdate (Phase 2 D6:
    AffectiveUpdate is positionally inert and never draws from the RNG, so
    zeroing it leaves every position bit-identical while removing its
    O(n^2) cost). Use for every positional test."""
    eng = build_pillar_engine(seed=seed, n_agents=N)
    apply_intervention(eng, PILLAR.interventions[stage_index])
    for rule in eng.rules.rules:
        if type(rule).__name__ == "AffectiveUpdate":
            rule.lr = 0.0
    return eng


# --- pillar S0 / S1 ensembles (variance pairs) ----------------------------

def _run_pillar_stage(stage_index: int, seed: int) -> tuple[float, float]:
    eng = positional_engine(stage_index, seed)
    v0 = variance(eng.positions())
    eng.run(TICKS)
    v1 = variance(eng.positions())
    return v0, v1


def _stage_variance_ensemble(stage_index: int) -> tuple[list[float], list[float]]:
    initials, finals = [], []
    for seed in STAGE_SEEDS:
        v0, v1 = _run_pillar_stage(stage_index, seed)
        initials.append(v0)
        finals.append(v1)
    return initials, finals


@pytest.fixture(scope="session")
def s0_ensemble() -> tuple[list[float], list[float]]:
    return _stage_variance_ensemble(0)


@pytest.fixture(scope="session")
def s1_ensemble() -> tuple[list[float], list[float]]:
    return _stage_variance_ensemble(1)


# --- pillar S2 / S3 ensembles (post-run engines, kept whole) --------------
# S2 is reused by both the constraint test and the S3 paired test, so the
# engines themselves (not just summaries) are cached.

def _run_stage_engines(stage_index: int) -> list:
    engines = []
    for seed in STAGE_SEEDS:
        eng = positional_engine(stage_index, seed)
        eng.run(TICKS)
        engines.append(eng)
    return engines


@pytest.fixture(scope="session")
def s1_engines() -> list:
    return _run_stage_engines(1)


@pytest.fixture(scope="session")
def s2_engines() -> list:
    return _run_stage_engines(2)


@pytest.fixture(scope="session")
def s3_engines() -> list:
    return _run_stage_engines(3)


@pytest.fixture(scope="session")
def s4_engines() -> list:
    return _run_stage_engines(4)


# Snapshot of t=0 network metrics per seed — used by test_s4_narrows_exposure
# to compare against the post-run state without re-running the build.
@pytest.fixture(scope="session")
def initial_network_metrics() -> list[tuple[float, float]]:
    from abm.metrics.network import (
        cross_cutting_tie_fraction,
        party_modularity,
    )
    out = []
    for seed in STAGE_SEEDS:
        eng = build_pillar_engine(seed=seed, n_agents=N)
        net = eng.env.attrs["network"]
        out.append(
            (
                cross_cutting_tie_fraction(eng.agents, net),
                party_modularity(eng.agents, net),
            )
        )
    return out


# --- canonical HK ensembles -----------------------------------------------

def _hk_final_var(epsilon: float, seed: int) -> float:
    eng = build_compass(
        n_agents=HK_N,
        epsilon=epsilon,
        attraction=0.08,
        repulsion=0.0,
        noise=0.01,
        seed=seed,
    )
    eng.run(TICKS)
    return variance(eng.positions())


@pytest.fixture(scope="session")
def hk_loose_finals() -> list[float]:
    return [_hk_final_var(2.0, seed) for seed in HK_SEEDS]


@pytest.fixture(scope="session")
def hk_mid_finals() -> list[float]:
    return [_hk_final_var(0.30, seed) for seed in HK_SEEDS]


@pytest.fixture(scope="session")
def hk_tight_finals() -> list[float]:
    return [_hk_final_var(0.15, seed) for seed in HK_SEEDS]
