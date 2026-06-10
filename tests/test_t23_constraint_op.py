"""MHV S2 T2.3 — ConstraintOp isolation guards.

Pins: the no-op gates (legacy paths stay bit-identical), the anti-centroid
AST guard carried over from the S1 pilot (review_math §A2 caveat ii — the
operator must never reference a party/centroid/corner target), the
on-axis fixed-point property, correlation monotonicity in rate, BOUNDED
collapse (the runaway-to-rank-1 tripwire), compass-neutrality of the
residual noise, and the emergent-mode pipeline surgery (IdentitySorting
out, coupling schedule pinned).
"""
from __future__ import annotations

import ast
import inspect

import numpy as np
import pytest

from abm.core.state import StateDelta
from abm.rules.constraint_op import ConstraintOp


# --------------------------------------------------------------------------
# pure-rule guards
# --------------------------------------------------------------------------

def test_anti_centroid_ast_guard():
    """The S1 pilot's P3 anti-confound guard, made permanent: the
    executable body of ConstraintOp.apply references no party / centroid
    / corner / target term. The operator is correlation-inducing, never
    position-herding."""
    src = inspect.getsource(ConstraintOp.apply)
    tree = ast.parse("class _C:\n" + src if src.startswith("    ") else src)
    # walk to the function node regardless of wrapper
    fn = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "apply":
            fn = node
            break
    assert fn is not None
    body = fn.body
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(getattr(body[0], "value", None), ast.Constant)):
        body = body[1:]
    code_text = "\n".join(ast.unparse(n) for n in body)
    banned = ["target", "party", "centroid", "corner"]
    hits = [b for b in banned if b in code_text]
    assert not hits, f"ConstraintOp references centroid-like term(s): {hits}"


def test_noop_gates_consume_no_rng():
    class _A:
        class state:
            attrs = {}
    rng = np.random.default_rng(0)
    s0 = rng.bit_generator.state
    # rate 0 + resid 0 → strict no-op before any draw
    d = ConstraintOp(rate=0.0, resid_sigma=0.0).apply(_A, None, _Env({}), rng)
    assert isinstance(d, StateDelta) and not d.d_attrs
    # active rule, but legacy agent (no issues / no runtime) → no-op
    d = ConstraintOp(rate=0.1, resid_sigma=0.1).apply(_A, None, _Env({}), rng)
    assert not d.d_attrs
    assert rng.bit_generator.state == s0


class _Env:
    def __init__(self, attrs):
        self.attrs = attrs


def test_on_axis_agent_does_not_move():
    """An agent already on its neighbourhood-consensus axis is a fixed
    point of the constraint pull — however far from the neighbour mean.
    (The operator removes off-axis spread; it never herds positions.)"""
    from abm.core.issues import load_loadings, build_runtime
    rt = build_runtime(load_loadings())

    class _S:  # agent/neighbour stubs
        def __init__(self, v):
            self.state = type("st", (), {})()
            self.state.attrs = {"issues": np.asarray(v, float),
                                "stubbornness": 0.0}
            self.state.ideology = np.zeros(2)

    u = np.ones(7) / np.sqrt(7.0)
    me = _S(2.0 * u * 0.4)          # exactly on the axis, far from mean
    nbr = [_S(0.1 * u), _S(0.3 * u)]

    import abm.rules.constraint_op as mod
    orig = mod.neighbor_agents
    mod.neighbor_agents = lambda a, s, e: nbr
    try:
        env = _Env({"issue_runtime": rt})
        d = ConstraintOp(rate=0.5).apply(me, None, env, np.random.default_rng(0))
    finally:
        mod.neighbor_agents = orig
    dv = d.d_attrs.get("issues", np.zeros(7))
    assert float(np.abs(dv).max()) < 1e-12


def test_resid_noise_is_compass_neutral():
    """The dispersion counterweight lives in the block-residual space:
    its block means vanish, so a single emitted delta never moves the
    compass projection."""
    from abm.core.issues import load_loadings, build_runtime, project1
    rt = build_runtime(load_loadings())

    class _S:
        def __init__(self):
            self.state = type("st", (), {})()
            self.state.attrs = {"issues": np.zeros(7), "stubbornness": 0.0}

    env = _Env({"issue_runtime": rt})
    d = ConstraintOp(rate=0.0, resid_sigma=0.05).apply(
        _S(), None, env, np.random.default_rng(3))
    dv = d.d_attrs["issues"]
    assert float(np.abs(dv).max()) > 0.0          # it does disperse items
    assert float(np.abs(project1(dv, rt)).max()) < 1e-15   # compass untouched


def test_resid_noise_vanishes_at_d2():
    from abm.core.issues import identity_loadings_2d, build_runtime
    rt = build_runtime(identity_loadings_2d())

    class _S:
        def __init__(self):
            self.state = type("st", (), {})()
            self.state.attrs = {"issues": np.zeros(2), "stubbornness": 0.0}

    env = _Env({"issue_runtime": rt})
    d = ConstraintOp(rate=0.0, resid_sigma=0.05).apply(
        _S(), None, env, np.random.default_rng(3))
    assert not d.d_attrs   # empty: the D=2 residual space is 0-dim


# --------------------------------------------------------------------------
# engine-level guards
# --------------------------------------------------------------------------

def _mean_abs_r(eng):
    V = np.array([a.state.attrs["issues"] for a in eng.agents])
    C = np.nan_to_num(np.corrcoef(V, rowvar=False), nan=0.0)
    return float(np.abs(C[np.triu_indices(7, 1)]).mean())


def _pr_within_party(eng):
    """Within-party PR — the operator's own footprint. (Pooled PR also
    absorbs partisan alignment: party_pull separating the party packages
    correlates ALL items pooled, which is its job, not ConstraintOp's.)"""
    V = np.array([a.state.attrs["issues"] for a in eng.agents])
    party = np.array([a.state.attrs.get("party", 2) for a in eng.agents])
    prs = []
    for p in (0, 1):
        M = V[party == p]
        if len(M) < 10:
            continue
        C = np.nan_to_num(np.corrcoef(M, rowvar=False), nan=0.0)
        w = np.clip(np.linalg.eigvalsh(C), 1e-9, None)
        prs.append(float((w.sum() ** 2) / (w ** 2).sum()))
    return float(np.mean(prs))


def _run(rate, ticks, seed=0, resid=0.01):
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    eng = build_engine(seed=seed, n_issues=7, evidence_regrade=True,
                       exogenous_shocks=True, constraint_rate=rate,
                       constraint_resid_sigma=resid)
    sched = build_schedule(evidence_regrade=True, exogenous_shocks=True)
    run_to(eng, sched, ticks)
    return eng


def test_constraint_collapse_monotone_in_rate():
    r_off = _mean_abs_r(_run(0.0, 30))
    r_low = _mean_abs_r(_run(0.01, 30))
    r_high = _mean_abs_r(_run(0.04, 30))
    assert r_high > r_low > r_off


def test_bounded_collapse_over_double_horizon():
    """The runaway-to-rank-1 tripwire (roadmap §6, the #1 S2 risk): at a
    plausible operating rate, run TWICE the arc horizon — constraint must
    rise (it collapses) but the issue space must keep clearly more than
    one effective dimension and |r| must stay well off 1.0."""
    eng = _run(0.02, 272)
    r = _mean_abs_r(eng)
    pr_wp = _pr_within_party(eng)
    assert r > 0.25          # it genuinely collapsed from the ~0.16 seed
    assert r < 0.90          # ... but nowhere near lockstep
    # the operator's own footprint: WITHIN-party effective dimensionality
    # must stay clearly multi-dimensional (pooled PR also absorbs
    # partisan alignment, which is party_pull's job, not this rule's)
    assert pr_wp > 2.0


def test_emergent_mode_pipeline_surgery():
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to

    eng = build_engine(seed=0, n_issues=7, constraint_rate=0.02)
    names = [type(r).__name__ for r in eng.rules.rules]
    assert "ConstraintOp" in names
    assert "IdentitySorting" not in names
    assert eng.env.attrs["party_issue_coupling"] == 1.0
    # the 1990 decade event must NOT re-impose the coupling schedule
    sched = build_schedule()
    run_to(eng, sched, 31)
    assert eng.env.attrs["party_issue_coupling"] == 1.0


def test_legacy_mode_unchanged():
    from abm.pillars.historical_arc import build_engine

    eng = build_engine(seed=0)
    names = [type(r).__name__ for r in eng.rules.rules]
    assert "IdentitySorting" in names
    assert "ConstraintOp" not in names


def test_constraint_requires_issues():
    from abm.pillars.historical_arc import build_engine

    with pytest.raises(ValueError):
        build_engine(seed=0, constraint_rate=0.02)
