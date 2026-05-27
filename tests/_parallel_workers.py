"""Top-level worker functions for parallel-seed execution in
session-scoped fixtures (Phase 8c §1.5).

Workers must be defined at module scope (not inside conftest or as
closures) so `multiprocessing.spawn` can re-import them in worker
processes. Each worker takes a small picklable argument and returns
a picklable result.

Verified empirically bit-identical to the serial implementations
they replace. The 9× wall-clock speedup comes from running the 12
STAGE_SEEDS in parallel rather than serially.
"""
from __future__ import annotations

from abm.metrics.affective import affective_polarization, ideological_constraint
from abm.metrics.polarization import variance
from abm.pillars import PILLAR, apply_intervention
from abm.pillars.calm_to_camps import build_engine as build_pillar_engine
from abm.scenarios.compass_basic import build as build_compass


# Constants — mirror conftest.py defaults. Workers can't import from
# conftest (pytest registers it as a plugin, not a regular module),
# so the constants are duplicated here. If conftest's N or TICKS
# change, this module must change in lockstep.
N = 250
TICKS = 200
HK_N = 200


def _positional_engine(stage_index: int, seed: int):
    """Like `conftest.positional_engine`: build at stage, zero the
    affect channel so positions are deterministic without affect
    interfering with positional tests."""
    eng = build_pillar_engine(seed=seed, n_agents=N)
    apply_intervention(eng, PILLAR.interventions[stage_index])
    for rule in eng.rules.rules:
        name = type(rule).__name__
        if name == "AffectiveUpdate":
            rule.lr = 0.0
        elif name == "BoundedConfidenceInfluence":
            rule.affect_weight = 0.0
        elif name == "BacklashRepulsion":
            rule.strength = 0.0
    for rule in eng.env_rules:
        if type(rule).__name__ == "TieRewiring":
            rule.affect_weight_rewire = 0.0
    return eng


def pillar_stage_variance_worker(args):
    """Args: (stage_index, seed). Returns (v0, v1) variance pair."""
    stage_index, seed = args
    eng = _positional_engine(stage_index, seed)
    v0 = variance(eng.positions())
    eng.run(TICKS)
    v1 = variance(eng.positions())
    return v0, v1


def pillar_stage_engine_worker(args):
    """Args: (stage_index, seed). Returns post-run pillar engine
    (positional path — affect zeroed)."""
    stage_index, seed = args
    eng = _positional_engine(stage_index, seed)
    eng.run(TICKS)
    return eng


def affect_engine_worker(args):
    """Args: (stage_index, seed). Returns post-run pillar engine with
    affect channel ON (no positional-inert optimisation)."""
    stage_index, seed = args
    eng = build_pillar_engine(seed=seed, n_agents=N)
    apply_intervention(eng, PILLAR.interventions[stage_index])
    eng.run(TICKS)
    return eng


def initial_network_metrics_worker(seed):
    """Build pillar engine; return (cross_cutting_tie_fraction,
    party_modularity) at t=0 (no run)."""
    from abm.metrics.network import cross_cutting_tie_fraction, party_modularity
    eng = build_pillar_engine(seed=seed, n_agents=N)
    net = eng.env.attrs["network"]
    return (
        cross_cutting_tie_fraction(eng.agents, net),
        party_modularity(eng.agents, net),
    )


def release_metrics_worker(args):
    """Args: (intervention_id, seed). Build, run to S4, measure, apply
    intervention, run TICKS, return {'sep': (before, after),
    'aff': (before, after)}."""
    from abm.pillars import INTERVENTIONS_PHASE6
    iv_id, seed = args
    intervention = next(iv for iv in INTERVENTIONS_PHASE6 if iv.id == iv_id)
    eng = build_pillar_engine(seed=seed, n_agents=N)
    apply_intervention(eng, PILLAR.interventions[4])
    eng.run(TICKS)
    # party_separation inline (avoid conftest dep)
    import numpy as np
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    sep_before = float(np.linalg.norm(
        pos[parties == 0].mean(axis=0) - pos[parties == 1].mean(axis=0)
    ))
    aff_before = affective_polarization(eng.agents)
    apply_intervention(eng, intervention)
    eng.run(TICKS)
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    sep_after = float(np.linalg.norm(
        pos[parties == 0].mean(axis=0) - pos[parties == 1].mean(axis=0)
    ))
    aff_after = affective_polarization(eng.agents)
    return {"sep": (sep_before, sep_after), "aff": (aff_before, aff_after)}


def release_metrics_with_independents_worker(args):
    """Phase 8d: same as release_metrics_worker but builds the pillar
    with `independent_fraction = 0.12` (12% pure Independents). Args:
    (intervention_id, seed). Returns the same {'sep', 'aff'} dict.
    """
    from abm.pillars import INTERVENTIONS_PHASE6
    iv_id, seed = args
    intervention = next(iv for iv in INTERVENTIONS_PHASE6 if iv.id == iv_id)
    eng = build_pillar_engine(seed=seed, n_agents=N, independent_fraction=0.12)
    apply_intervention(eng, PILLAR.interventions[4])
    eng.run(TICKS)
    import numpy as np
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    sep_before = float(np.linalg.norm(
        pos[parties == 0].mean(axis=0) - pos[parties == 1].mean(axis=0)
    ))
    aff_before = affective_polarization(eng.agents)
    apply_intervention(eng, intervention)
    eng.run(TICKS)
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    sep_after = float(np.linalg.norm(
        pos[parties == 0].mean(axis=0) - pos[parties == 1].mean(axis=0)
    ))
    aff_after = affective_polarization(eng.agents)
    return {"sep": (sep_before, sep_after), "aff": (aff_before, aff_after)}


def hk_final_var_worker(args):
    """Args: (epsilon, seed). Build compass scenario, run TICKS, return
    final variance."""
    epsilon, seed = args
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
