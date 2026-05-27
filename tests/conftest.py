"""Shared constants, helpers, and session-scoped ensembles for the suite.

Each expensive ensemble (S0/S1 variance pairs, S2/S3 positional engines, the
three HK epsilon sweeps) is computed exactly once per `pytest` invocation
and shared across the tests that reuse it.
"""
from __future__ import annotations

import numpy as np
import pytest

from abm.calibration_parallel import run_seeds_parallel
from abm.core.outlets import US_MEDIA_OUTLETS_2024, diet_target
from abm.metrics.affective import ideological_constraint
from abm.metrics.polarization import variance
from abm.pillars import PILLAR, apply_intervention, build_at_stage
from abm.pillars.calm_to_camps import build_engine as build_pillar_engine
from abm.scenarios.compass_basic import build as build_compass

from ._parallel_workers import (
    affect_engine_worker,
    hk_final_var_worker,
    initial_network_metrics_worker,
    pillar_stage_engine_worker,
    pillar_stage_variance_worker,
    release_metrics_with_independents_worker,
    release_metrics_worker,
)


def party_separation(engine) -> float:
    """Distance between the two parties' mean ideology positions —
    the headline ratchet-test metric (phase3 spec §9)."""
    parties = np.array([a.state.attrs["party"] for a in engine.agents])
    pos = engine.positions()
    return float(
        np.linalg.norm(pos[parties == 0].mean(axis=0) - pos[parties == 1].mean(axis=0))
    )

# Ensemble sizes (Phase 1 D4; Phase 8c §7 S1: pillar 12 → 20 seeds).
# The bump from 12 to 20 reduces SE by ~22%; required for honest CI
# reporting per the §7 stats pass. Compute multiplier ~1.7×; runtime
# under the parallel-seed runner (Phase 8c §1.5) absorbs this fully.
STAGE_SEEDS = tuple(range(20))
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
    """build_at_stage at the test N, then zero the **affect channel**
    (AffectiveUpdate.lr + BoundedConfidenceInfluence.affect_weight +
    TieRewiring.affect_weight_rewire). With all three at zero the affect
    channel is positionally inert — affect never updates and is never
    read — and the run leaves positions bit-identical to the full
    Phase 5 bundle (Phase 5 §11 calibration: macro positional metrics
    differ by <0.005 between affect-on and affect-off). Use for every
    positional test that cares about positions, not affect.

    For affect-reading tests, use `s1_affect_engines` / `s3_affect_engines`
    (which keep all three at their bundle values)."""
    eng = build_pillar_engine(seed=seed, n_agents=N)
    apply_intervention(eng, PILLAR.interventions[stage_index])
    for rule in eng.rules.rules:
        name = type(rule).__name__
        if name == "AffectiveUpdate":
            rule.lr = 0.0
        elif name == "BoundedConfidenceInfluence":
            # Phase 5 A4: without this, BC reads affect per neighbour,
            # and zeroing lr alone is no longer positionally inert.
            rule.affect_weight = 0.0
        elif name == "BacklashRepulsion":
            # Phase 6: would-be no-op at strength 0 in S0-S4 bundles,
            # but zero defensively in case a future test runs the fast
            # path on an intervention bundle that turns it on.
            rule.strength = 0.0
    for rule in eng.env_rules:
        if type(rule).__name__ == "TieRewiring":
            rule.affect_weight_rewire = 0.0
    return eng


# --- pillar S0 / S1 ensembles (variance pairs) ----------------------------

def _run_pillar_stage(stage_index: int, seed: int) -> tuple[float, float]:
    """Serial fallback. Used only outside of the parallel ensembles
    (e.g. ad-hoc test code that may call this directly)."""
    eng = positional_engine(stage_index, seed)
    v0 = variance(eng.positions())
    eng.run(TICKS)
    v1 = variance(eng.positions())
    return v0, v1


def _stage_variance_ensemble(stage_index: int) -> tuple[list[float], list[float]]:
    """Phase 8c §1.5: parallel-seed execution; bit-identical to serial."""
    args = [(stage_index, seed) for seed in STAGE_SEEDS]
    results = run_seeds_parallel(pillar_stage_variance_worker, args)
    initials = [v0 for v0, _v1 in results]
    finals = [v1 for _v0, v1 in results]
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
    """Phase 8c §1.5: parallel-seed execution; bit-identical to serial."""
    args = [(stage_index, seed) for seed in STAGE_SEEDS]
    return run_seeds_parallel(pillar_stage_engine_worker, args)


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


# --- Phase 5: affect-bearing engines --------------------------------------
# `positional_engine` zeros AffectiveUpdate.lr because it's positionally
# inert and that's a speed win for positional tests. The Iyengar test
# (and any other affect-reading assertion) needs affect to actually
# update, so we provide a parallel pair of fixtures without the lr-zero
# optimisation.


def _affect_engine(stage_index: int, seed: int):
    """Like `positional_engine`, but keep AffectiveUpdate.lr at the
    bundle value — affect actually updates during the run."""
    eng = build_pillar_engine(seed=seed, n_agents=N)
    apply_intervention(eng, PILLAR.interventions[stage_index])
    return eng


def _run_affect_engines(stage_index: int) -> list:
    """Phase 8c §1.5: parallel-seed execution; bit-identical to serial."""
    args = [(stage_index, seed) for seed in STAGE_SEEDS]
    return run_seeds_parallel(affect_engine_worker, args)


@pytest.fixture(scope="session")
def s0_affect_engines() -> list:
    return _run_affect_engines(0)


# --- Phase 6: per-intervention release-phase fixture ----------------------
# Each X-intervention is applied at the end of an S4 run, then the engine
# runs `TICKS` more. Δparty_separation = sep_after - sep_S4_end. The
# session-scoped fixture caches the result map so the consolidated bucket
# test and any further investigation tests share one set of runs.


def _release_metrics(intervention, seed):
    """S0→S4 (`TICKS`), apply intervention, run `TICKS`, return
    {'sep': (before, after), 'aff': (before, after)} for the two-axis
    bucketing (Phase 7)."""
    from abm.metrics.affective import affective_polarization

    eng = build_pillar_engine(seed=seed, n_agents=N)
    apply_intervention(eng, PILLAR.interventions[4])
    eng.run(TICKS)
    sep_before = party_separation(eng)
    aff_before = affective_polarization(eng.agents)
    apply_intervention(eng, intervention)
    eng.run(TICKS)
    sep_after = party_separation(eng)
    aff_after = affective_polarization(eng.agents)
    return {"sep": (sep_before, sep_after), "aff": (aff_before, aff_after)}


@pytest.fixture(scope="session")
def intervention_buckets() -> dict[str, dict[str, float]]:
    """`{intervention.id: {"sep": Δparty_separation, "aff": Δaffective_polarization}}`
    means across STAGE_SEEDS.

    Sign conventions:
      - Δsep: negative = helpful (camps closer), positive = backfire.
      - Δaff: positive = helpful (warmer / less animus), negative =
        backfire (more animus). Note the OPPOSITE sign convention from
        Δsep — `affective_polarization` itself is more-negative = more
        polarized.

    Phase 8c §1.5: parallel-seed execution. All
    `len(INTERVENTIONS_PHASE6) * len(STAGE_SEEDS)` runs go into a
    single Pool batch — biggest single wall-clock win in the suite.
    Bit-identical to serial.
    """
    from abm.pillars import INTERVENTIONS_PHASE6
    args = [(iv.id, seed) for iv in INTERVENTIONS_PHASE6 for seed in STAGE_SEEDS]
    flat = run_seeds_parallel(release_metrics_worker, args)
    out: dict[str, dict[str, float]] = {}
    for iv in INTERVENTIONS_PHASE6:
        sep_diffs: list[float] = []
        aff_diffs: list[float] = []
        for (iv_id, _seed), m in zip(args, flat):
            if iv_id != iv.id:
                continue
            sep_diffs.append(m["sep"][1] - m["sep"][0])
            aff_diffs.append(m["aff"][1] - m["aff"][0])
        out[iv.id] = {
            "sep": float(np.mean(sep_diffs)),
            "aff": float(np.mean(aff_diffs)),
        }
    return out


@pytest.fixture(scope="session")
def intervention_buckets_with_independents() -> dict[str, dict[str, float]]:
    """Phase 8d §5: same as `intervention_buckets` but builds the
    pillar at `independent_fraction = 0.12` (12% pure Independents).
    Sensitivity reading — variant buckets are reported in methods.md
    §4.5 alongside the canonical binary-party numbers.
    """
    from abm.pillars import INTERVENTIONS_PHASE6
    args = [(iv.id, seed) for iv in INTERVENTIONS_PHASE6 for seed in STAGE_SEEDS]
    flat = run_seeds_parallel(release_metrics_with_independents_worker, args)
    out: dict[str, dict[str, float]] = {}
    for iv in INTERVENTIONS_PHASE6:
        sep_diffs: list[float] = []
        aff_diffs: list[float] = []
        for (iv_id, _seed), m in zip(args, flat):
            if iv_id != iv.id:
                continue
            sep_diffs.append(m["sep"][1] - m["sep"][0])
            aff_diffs.append(m["aff"][1] - m["aff"][0])
        out[iv.id] = {
            "sep": float(np.mean(sep_diffs)),
            "aff": float(np.mean(aff_diffs)),
        }
    return out


@pytest.fixture(scope="session")
def s1_affect_engines() -> list:
    return _run_affect_engines(1)


@pytest.fixture(scope="session")
def s3_affect_engines() -> list:
    return _run_affect_engines(3)


# Snapshot of t=0 network metrics per seed — used by test_s4_narrows_exposure
# to compare against the post-run state without re-running the build.
@pytest.fixture(scope="session")
def initial_network_metrics() -> list[tuple[float, float]]:
    """Phase 8c §1.5: parallel-seed execution; bit-identical to serial."""
    return run_seeds_parallel(initial_network_metrics_worker, STAGE_SEEDS)


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
    """Phase 8c §1.5: parallel-seed execution; bit-identical to serial."""
    return run_seeds_parallel(
        hk_final_var_worker, [(2.0, s) for s in HK_SEEDS],
    )


@pytest.fixture(scope="session")
def hk_mid_finals() -> list[float]:
    """Phase 8c §1.5: parallel-seed execution; bit-identical to serial."""
    return run_seeds_parallel(
        hk_final_var_worker, [(0.30, s) for s in HK_SEEDS],
    )


@pytest.fixture(scope="session")
def hk_tight_finals() -> list[float]:
    """Phase 8c §1.5: parallel-seed execution; bit-identical to serial."""
    return run_seeds_parallel(
        hk_final_var_worker, [(0.15, s) for s in HK_SEEDS],
    )
