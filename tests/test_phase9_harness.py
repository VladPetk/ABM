"""Phase 9 Step 1 — calibration harness unit tests.

Validates `abm.calibration_phase9`:
- target loading
- Wasserstein on identical / disjoint clouds
- shape-descriptor sanity on a Gaussian blob
- POT-fallback path via monkeypatching the module flag
"""
from __future__ import annotations

import importlib
from pathlib import Path

import numpy as np
import pytest

import abm.calibration_phase9 as cp9

DATA_DIR = Path(__file__).parent.parent / "phase9_data"


def test_load_empirical_targets():
    targets = cp9.load_empirical_targets(DATA_DIR)
    assert set(targets.keys()) == set(cp9.EMPIRICAL_DECADES)
    for decade, rec in targets.items():
        assert rec["kde"].shape == (50, 50), (
            f"{decade} KDE shape {rec['kde'].shape} != (50, 50)"
        )
        assert rec["pointcloud"].shape == (1000, 2), (
            f"{decade} pointcloud shape != (1000, 2)"
        )
        assert rec["grid_x"].shape == (50,)
        assert rec["grid_y"].shape == (50,)
        # KDE integrates to ~1 on the grid (trapezoid; within 5%).
        gx, gy = rec["grid_x"], rec["grid_y"]
        integral = float(np.trapz(np.trapz(rec["kde"], gx, axis=1), gy))
        assert abs(integral - 1.0) < 0.05, (
            f"{decade} KDE integral {integral:.4f} not within 5% of 1.0"
        )


def test_wasserstein_identical():
    rng = np.random.default_rng(0)
    # Use exactly n_sub points so sub-sampling is a no-op and both
    # sides become the *same* set of points → W2 must be 0 modulo
    # floating-point rounding.
    pts = rng.normal(scale=0.3, size=(250, 2))
    w = cp9.wasserstein_2d(pts, pts, n_sub=250, seed=42)
    assert w < 0.01, f"identical-cloud W2 = {w}"


def test_wasserstein_disjoint():
    rng = np.random.default_rng(1)
    a = rng.normal(loc=(-0.8, -0.8), scale=0.05, size=(500, 2))
    b = rng.normal(loc=(+0.8, +0.8), scale=0.05, size=(500, 2))
    w = cp9.wasserstein_2d(a, b, n_sub=250, seed=0)
    # Centers separated by sqrt(2)*1.6 ≈ 2.26; W2 should exceed 1.0.
    assert w > 1.0, f"disjoint W2 = {w} (expected > 1.0)"


def test_shape_descriptors_basic():
    sigma = 0.2
    rng = np.random.default_rng(7)
    pts = rng.normal(scale=sigma, size=(5000, 2))
    desc = cp9.shape_descriptors(pts)
    # corr near 0 (independent draws).
    assert abs(desc["corr_xy"]) < 0.05, desc["corr_xy"]
    # var near σ².
    assert abs(desc["var_x"] - sigma ** 2) < 0.01
    assert abs(desc["var_y"] - sigma ** 2) < 0.01
    # mean(|x|) ≈ σ·sqrt(2/π).
    expected_mean_abs = sigma * np.sqrt(2.0 / np.pi)
    assert abs(desc["mean_abs_x"] - expected_mean_abs) < 0.01
    assert abs(desc["mean_abs_y"] - expected_mean_abs) < 0.01
    # Quadrant mass sums to 1.
    q = desc["quadrant_mass"]
    assert abs(sum(q) - 1.0) < 1e-9


def test_pot_fallback_path(monkeypatch):
    """Force the degraded code path and confirm wasserstein_2d still
    returns a finite value and the `degraded` flag flips to True."""
    monkeypatch.setattr(cp9, "_POT_AVAILABLE", False)
    monkeypatch.setattr(cp9, "_ot", None)

    rng = np.random.default_rng(3)
    a = rng.normal(loc=(-0.5, 0.0), scale=0.1, size=(400, 2))
    b = rng.normal(loc=(+0.5, 0.0), scale=0.1, size=(400, 2))
    w = cp9.wasserstein_2d(a, b, n_sub=200, seed=5)
    assert np.isfinite(w)
    assert w > 0.3, (
        f"fallback W (per-axis mean) = {w}; expected ~0.5 for x-shift"
    )

    rec = cp9.wasserstein_2d_dict(a, b, n_sub=200, seed=5)
    assert rec["degraded"] is True
    assert np.isfinite(rec["wasserstein"])
    assert cp9.pot_available() is False
