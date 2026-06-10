"""MHV S2 T2.1 — issue-state guards: loadings integrity, N=2 reduction
exactness (I1), native seeding moments, dormant-wiring bit-identity.

The substrate these pin: abm/core/issues.py + the frozen loadings file
data/mhv/issue_loadings.json + the dormant n_issues path in build_engine.
T2.2 (kernels go live) extends these; it must not weaken them.
"""
from __future__ import annotations

import hashlib

import numpy as np
import pytest

from abm.core.issues import (
    chol_corr,
    identity_loadings_2d,
    load_loadings,
    project_compass,
    rms_distance,
    seed_issue_vectors,
)


@pytest.fixture(scope="module")
def loadings():
    return load_loadings()


def test_loadings_file_integrity(loadings):
    # 7 items, three blocks partitioning 0..6, readout = empirical cores
    assert len(loadings["items"]) == 7
    blocks = loadings["blocks"]
    all_idx = sorted(blocks["econ"] + blocks["cultural_moral"] + blocks["racial"])
    assert all_idx == list(range(7))
    ro = loadings["compass_readout"]
    assert ro["x_idx"] == blocks["econ"]
    assert sorted(ro["y_idx"]) == sorted(blocks["cultural_moral"] + blocks["racial"])
    # the y readout must equal the empirical pipeline's cultural core
    items = [it["var"] for it in loadings["items"]]
    y_vars = {items[i] for i in ro["y_idx"]}
    assert y_vars == {"VCF0838", "VCF0830", "VCF0852", "VCF0853"}
    # frozen correlation matrix is a PSD correlation matrix
    C = np.asarray(loadings["corr_1986_psd"], float)
    assert np.allclose(C, C.T)
    assert np.allclose(np.diag(C), 1.0)
    assert np.linalg.eigvalsh(C).min() > 0
    # weak-1980s-constraint sanity: mean |offdiag| in a loose empirical band
    off = C[np.triu_indices(7, 1)]
    assert 0.05 < np.abs(off).mean() < 0.35


def test_n2_reduction_projection_is_identity_bitexact():
    ld2 = identity_loadings_2d()
    rng = np.random.default_rng(7)
    V = rng.uniform(-1, 1, size=(400, 2))
    assert np.array_equal(project_compass(V, ld2), V)


def test_n2_reduction_distance_is_euclidean_bitexact():
    rng = np.random.default_rng(8)
    a = rng.uniform(-1, 1, size=(400, 2))
    b = rng.uniform(-1, 1, size=(400, 2))
    d = rms_distance(a, b)
    ref = np.sqrt(((a - b) ** 2).sum(axis=-1))   # the 2D engine's arithmetic
    assert np.array_equal(d, ref)


def test_rms_distance_scale_invariance_across_d():
    # a maximally-disagreeing pair spans the same numeric range at any D
    for D in (2, 7, 10):
        a = -np.ones((1, D))
        b = np.ones((1, D))
        assert np.isclose(rms_distance(a, b)[0], 2.0 * np.sqrt(2.0))


def test_seeding_moments_and_native_tail(loadings):
    rng = np.random.default_rng(0)
    parties = np.array([0] * 8000 + [1] * 8000 + [2] * 2000)
    V = seed_issue_vectors(parties, loadings, rng, chol=chol_corr(loadings))
    assert V.shape == (18000, 7)
    assert V.min() >= -1.0 and V.max() <= 1.0
    P = project_compass(V, loadings)
    ro = loadings["compass_readout"]
    for p, tag in ((0, "dem"), (1, "rep")):
        m = parties == p
        mu_items = np.asarray(
            loadings["party_conditional"][tag]["item_means"], float)
        # projected centroid tracks the measured item means (clip shrinks a
        # little, hence the 0.03 tolerance)
        assert abs(P[m, 0].mean() - mu_items[ro["x_idx"]].mean()) < 0.03
        assert abs(P[m, 1].mean() - mu_items[ro["y_idx"]].mean()) < 0.03
        # within-party projected spread lands in the ANES wp_sd neighborhood
        assert 0.25 < P[m, 0].std() < 0.40
    # the wrong-side econ tail exists NATIVELY (what retires the T0.4 soft
    # cap): present, party-ordered (D > R), and in a loose empirical band.
    # Exact pinning against the 1980-90 pooled targets is T2.2's job.
    dem_tail = float((P[parties == 0, 0] > 0.45).mean())
    rep_tail = float((P[parties == 1, 0] < -0.45).mean())
    assert 0.005 < dem_tail < 0.15
    assert 0.005 < rep_tail < 0.10
    assert dem_tail > rep_tail


def _macro_sha(eng, sched, ticks=12):
    from abm.pillars.schedule import run_to
    h = hashlib.sha256()
    for t in range(1, ticks + 1):
        run_to(eng, sched, t)
        h.update(eng.positions().tobytes())
    return h.hexdigest()


def test_n2_live_engine_bit_identity():
    """THE I1 engine-level reduction proof (upgraded at T2.2, when the
    kernels went live): with n_issues=2 the whole position state flows
    through the issues apply path — native BC/PartyPull/Noise kernels,
    lift, projection — and the trajectory must be bit-identical to the
    plain 2D run. Any kernel whose D=2 arithmetic deviates from the 2D
    code by a single ulp fails this."""
    from abm.pillars.historical_arc import build_engine, build_schedule

    eng_a = build_engine(seed=3)
    eng_b = build_engine(seed=3, n_issues=2)
    assert "issues" not in eng_a.agents[0].state.attrs
    assert eng_b.agents[0].state.attrs["issues"].shape == (2,)
    sched_a = build_schedule()
    sched_b = build_schedule()
    # 24 ticks: past the 1987 Fairness-Doctrine event so the
    # MediaConsumption native path is exercised, not just BC/pull/noise.
    assert _macro_sha(eng_a, sched_a, ticks=24) == _macro_sha(eng_b, sched_b, ticks=24)


def test_n2_reduction_engine_path():
    from abm.pillars.historical_arc import build_engine

    eng = build_engine(seed=1, n_issues=2)
    V = eng.agents[0].state.attrs["issues"]
    assert V.shape == (2,)


def test_bad_n_issues_raises():
    from abm.pillars.historical_arc import build_engine

    with pytest.raises(ValueError):
        build_engine(seed=0, n_issues=5)
