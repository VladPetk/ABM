"""Phase 9 — Empirical-distribution calibration harness.

Score an engine run against per-decade empirical KDE / pointcloud
targets in `data/phase9_empirical/`. The primary metric is 2D Wasserstein-2
distance via POT (`ot.emd2`) with squared-Euclidean cost on
sub-sampled point clouds (n_sub=250 per side per the spec §2.1).

Shape descriptors (corr, var, mean(|.|), local-max count, quadrant
mass) are auxiliary diagnostics — they describe *how* a model cloud
differs from the target shape, but are not part of the loss.

POT fallback: if `import ot` fails (or POT is unavailable), the
harness falls back to a per-axis `scipy.stats.wasserstein_distance`
averaged across x and y. This is a *degraded* proxy — it ignores
the joint dependence structure and undercounts the cost of a
distribution that has the right marginals but wrong covariance. A
warning is logged and `degraded=True` is flagged on the return
record. The fallback exists so the harness still runs in
environments where POT cannot be installed.

Coordinate convention follows `phase9_empirical_targets.md` §2:
x ∈ [-1, 1] economic axis (negative = redistributive),
y ∈ [-1, 1] social/cultural axis (negative = secular/cosmopolitan).
This matches the engine's 2D ideology space directly.

Sub-sampling determinism (spec §2.1): per (decade_idx, run_seed) the
sub-sample seed is `(decade_idx * 31337) ^ run_seed`, so identical
(decade, seed) inputs produce identical sub-samples.
"""
from __future__ import annotations

import logging
import warnings
from pathlib import Path
from typing import Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)

EMPIRICAL_DECADES = [1980, 1990, 2000, 2010, 2020]

# Try to import POT once at module import time. If it fails the
# fallback path is used. We do not raise — degraded operation is
# allowed by the spec (§7 risk register #5).
try:
    import ot as _ot  # type: ignore
    _POT_AVAILABLE = True
except Exception:  # pragma: no cover - import-time guard
    _ot = None
    _POT_AVAILABLE = False
    warnings.warn(
        "POT (Python Optimal Transport) is not available. "
        "calibration_phase9.wasserstein_2d will fall back to a "
        "per-axis scipy.stats.wasserstein_distance proxy, which is "
        "degraded — it ignores the joint dependence structure. "
        "Install POT with `pip install POT` for the primary metric.",
        RuntimeWarning,
        stacklevel=2,
    )


def pot_available() -> bool:
    """Return True iff POT is importable (primary path active)."""
    return _POT_AVAILABLE


# ------------------------------------------------------------------
# Target loading
# ------------------------------------------------------------------


def load_empirical_targets(data_dir: str | Path) -> Dict[int, Dict[str, np.ndarray]]:
    """Load the per-decade empirical KDE + pointcloud + grid axes.

    Returns a dict keyed by decade (int) with values:
        {"kde": (50, 50), "pointcloud": (1000, 2),
         "grid_x": (50,), "grid_y": (50,)}

    The grid axes are shared across decades but copied into each
    record for self-contained downstream use.
    """
    data_dir = Path(data_dir)
    grid_x = np.load(data_dir / "phase9_empirical_grid_x.npy")
    grid_y = np.load(data_dir / "phase9_empirical_grid_y.npy")
    out: Dict[int, Dict[str, np.ndarray]] = {}
    for dec in EMPIRICAL_DECADES:
        kde = np.load(data_dir / f"phase9_empirical_kde_{dec}.npy")
        pc = np.load(data_dir / f"phase9_empirical_pointcloud_{dec}.npy")
        out[dec] = {
            "kde": kde,
            "pointcloud": pc,
            "grid_x": grid_x,
            "grid_y": grid_y,
        }
    return out


# ------------------------------------------------------------------
# KDE building
# ------------------------------------------------------------------


def kde_from_positions(
    positions: np.ndarray, grid_x: np.ndarray, grid_y: np.ndarray
) -> np.ndarray:
    """Build a 2D KDE from positions on the (grid_x, grid_y) target grid.

    Uses `scipy.stats.gaussian_kde` with Silverman bandwidth (matches
    the empirical-target build per `phase9_empirical_targets.md` §5.2),
    evaluated on the meshgrid and normalized to integrate to 1.0 over
    the grid via the trapezoid rule.

    Parameters
    ----------
    positions : (N, 2) ndarray
    grid_x, grid_y : (G,) ndarrays of axis coordinates.

    Returns
    -------
    (Gy, Gx) ndarray — density values; row index = y, col index = x,
    matching the empirical target convention.
    """
    from scipy.stats import gaussian_kde

    positions = np.asarray(positions, dtype=float)
    if positions.ndim != 2 or positions.shape[1] != 2:
        raise ValueError(
            f"positions must be (N, 2), got {positions.shape}"
        )
    if positions.shape[0] < 2:
        # gaussian_kde requires >=2 points; degenerate input → zeros.
        return np.zeros((len(grid_y), len(grid_x)), dtype=float)

    kde = gaussian_kde(positions.T, bw_method="silverman")
    XX, YY = np.meshgrid(grid_x, grid_y)
    pts = np.vstack([XX.ravel(), YY.ravel()])
    Z = kde(pts).reshape(XX.shape)

    # Normalize via trapezoid (same convention as empirical build).
    integral = float(np.trapz(np.trapz(Z, grid_x, axis=1), grid_y))
    if integral > 0:
        Z = Z / integral
    return Z


# ------------------------------------------------------------------
# Wasserstein
# ------------------------------------------------------------------


def _subsample(
    points: np.ndarray, n: int, rng: np.random.Generator
) -> np.ndarray:
    """Seeded sub-sampling without replacement (or with, if n > len)."""
    points = np.asarray(points, dtype=float)
    k = len(points)
    if k == 0:
        return points
    if k <= n:
        return points
    idx = rng.choice(k, size=n, replace=False)
    return points[idx]


def wasserstein_2d(
    model_points: np.ndarray,
    target_points: np.ndarray,
    n_sub: int = 250,
    seed: int = 0,
) -> float:
    """2D Wasserstein-2 distance between two point clouds (sub-sampled).

    Primary path (POT available): exact EMD via `ot.emd2` with a
    squared-Euclidean cost matrix on `n_sub` points per side; returns
    the sqrt of the W2-squared value (so the return is W2 in the same
    units as the input coordinates — units of `[-1, 1]`).

    Fallback path (POT unavailable): mean of per-axis
    `scipy.stats.wasserstein_distance` for x and y. This ignores
    joint structure and is documented as degraded — see module
    docstring.

    Sub-sampling: both clouds are reduced to `n_sub` points using a
    seeded RNG. The same `seed` is used for both sides so a given
    (decade, run_seed) pair produces a bit-identical comparison.
    """
    rng_a = np.random.default_rng(seed)
    rng_b = np.random.default_rng(seed ^ 0xA5A5)
    a = _subsample(np.asarray(model_points, dtype=float), n_sub, rng_a)
    b = _subsample(np.asarray(target_points, dtype=float), n_sub, rng_b)

    if len(a) == 0 or len(b) == 0:
        return float("nan")

    if _POT_AVAILABLE:
        # Uniform weights, squared-Euclidean cost. ot.emd2 returns the
        # transport cost, which under sqeuclidean is the W2 squared.
        wa = np.full(len(a), 1.0 / len(a))
        wb = np.full(len(b), 1.0 / len(b))
        # Cost matrix: (n_a, n_b) of |a_i - b_j|^2.
        diff = a[:, None, :] - b[None, :, :]
        M = np.einsum("ijk,ijk->ij", diff, diff)
        cost_sq = float(_ot.emd2(wa, wb, M))
        return float(np.sqrt(max(cost_sq, 0.0)))
    # Degraded fallback.
    from scipy.stats import wasserstein_distance
    wx = wasserstein_distance(a[:, 0], b[:, 0])
    wy = wasserstein_distance(a[:, 1], b[:, 1])
    return float(0.5 * (wx + wy))


def wasserstein_2d_dict(
    model_points: np.ndarray,
    target_points: np.ndarray,
    n_sub: int = 250,
    seed: int = 0,
) -> Dict[str, object]:
    """Same as wasserstein_2d but returns a dict including the
    `degraded` flag so callers can record whether the primary or
    fallback path was used."""
    return {
        "wasserstein": wasserstein_2d(
            model_points, target_points, n_sub=n_sub, seed=seed
        ),
        "degraded": not _POT_AVAILABLE,
    }


# ------------------------------------------------------------------
# Shape descriptors
# ------------------------------------------------------------------


def _count_kde_local_maxima(
    Z: np.ndarray, threshold: float = 0.6
) -> int:
    """Count cells in Z that (a) exceed `threshold` and (b) are a
    local maximum in their 3×3 neighborhood. Fast approximation —
    boundary cells are eligible if their existing neighbors are all
    strictly less. The threshold is in units of the KDE density,
    matching `phase9_spec.md` §2.2.
    """
    Z = np.asarray(Z, dtype=float)
    ny, nx = Z.shape
    count = 0
    for i in range(ny):
        for j in range(nx):
            v = Z[i, j]
            if v < threshold:
                continue
            is_max = True
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    if di == 0 and dj == 0:
                        continue
                    ii, jj = i + di, j + dj
                    if 0 <= ii < ny and 0 <= jj < nx:
                        if Z[ii, jj] > v:
                            is_max = False
                            break
                if not is_max:
                    break
            if is_max:
                count += 1
    return count


def shape_descriptors(positions: np.ndarray) -> Dict[str, object]:
    """Auxiliary diagnostics — corr, var, mean(|.|), KDE local-max
    count, quadrant mass.

    `quadrant_mass` is the (LL, LR, UL, UR) tuple where:
        LL = x<0, y<0    LR = x>=0, y<0
        UL = x<0, y>=0   UR = x>=0, y>=0
    summing to 1.0 (boundary x=0 / y=0 goes to the upper / right cell).

    `n_local_max` is computed from a 50×50 KDE on `[-1, 1]²` with
    Silverman bandwidth (the same KDE recipe as the empirical
    targets), so it's directly comparable to the empirical KDE's
    local-max count.
    """
    pos = np.asarray(positions, dtype=float)
    n = pos.shape[0]
    out: Dict[str, object] = {}
    if n < 2:
        out.update({
            "corr_xy": 0.0, "var_x": 0.0, "var_y": 0.0,
            "mean_abs_x": 0.0, "mean_abs_y": 0.0,
            "n_local_max": 0,
            "quadrant_mass": (0.25, 0.25, 0.25, 0.25),
        })
        return out

    x, y = pos[:, 0], pos[:, 1]
    out["var_x"] = float(np.var(x, ddof=0))
    out["var_y"] = float(np.var(y, ddof=0))
    out["mean_abs_x"] = float(np.mean(np.abs(x)))
    out["mean_abs_y"] = float(np.mean(np.abs(y)))
    sx, sy = np.std(x), np.std(y)
    if sx > 0 and sy > 0:
        out["corr_xy"] = float(np.corrcoef(x, y)[0, 1])
    else:
        out["corr_xy"] = 0.0

    # Quadrant mass.
    q_ll = float(np.mean((x < 0) & (y < 0)))
    q_lr = float(np.mean((x >= 0) & (y < 0)))
    q_ul = float(np.mean((x < 0) & (y >= 0)))
    q_ur = float(np.mean((x >= 0) & (y >= 0)))
    out["quadrant_mass"] = (q_ll, q_lr, q_ul, q_ur)

    # KDE local maxima on canonical [-1,1] grid for comparability
    # with the empirical 50×50 KDE.
    grid = np.linspace(-1.0, 1.0, 50)
    try:
        Z = kde_from_positions(pos, grid, grid)
        out["n_local_max"] = int(_count_kde_local_maxima(Z, threshold=0.6))
    except Exception:
        out["n_local_max"] = 0
    return out


# ------------------------------------------------------------------
# Per-decade scoring
# ------------------------------------------------------------------


def score_engine_run(
    positions_by_decade: Dict[int, np.ndarray],
    target_dir: str | Path,
    seed_for_subsample: int = 0,
):
    """Score a single engine run against the empirical targets.

    Parameters
    ----------
    positions_by_decade : dict[int → (N, 2) ndarray]
        Model agent positions at each decade endpoint. Must contain
        all of `EMPIRICAL_DECADES` (1980, 1990, 2000, 2010, 2020).
    target_dir : path-like
        Directory holding `phase9_empirical_*.npy`.
    seed_for_subsample : int
        Combined with the decade index per spec §2.1 to seed
        sub-sampling. Pass the engine's `seed` here.

    Returns
    -------
    pandas.DataFrame with columns
        [decade, wasserstein, corr_xy, var_x, var_y,
         mean_abs_x, mean_abs_y, n_local_max,
         q_ll, q_lr, q_ul, q_ur, degraded].
    """
    import pandas as pd

    targets = load_empirical_targets(target_dir)
    rows = []
    for dec_idx, decade in enumerate(EMPIRICAL_DECADES):
        if decade not in positions_by_decade:
            raise KeyError(
                f"positions_by_decade missing decade {decade}"
            )
        model_pos = positions_by_decade[decade]
        target_pc = targets[decade]["pointcloud"]
        sub_seed = (dec_idx * 31337) ^ int(seed_for_subsample)
        w = wasserstein_2d(model_pos, target_pc, n_sub=250, seed=sub_seed)
        desc = shape_descriptors(model_pos)
        q_ll, q_lr, q_ul, q_ur = desc["quadrant_mass"]
        rows.append({
            "decade": decade,
            "wasserstein": w,
            "corr_xy": desc["corr_xy"],
            "var_x": desc["var_x"],
            "var_y": desc["var_y"],
            "mean_abs_x": desc["mean_abs_x"],
            "mean_abs_y": desc["mean_abs_y"],
            "n_local_max": desc["n_local_max"],
            "q_ll": q_ll, "q_lr": q_lr,
            "q_ul": q_ul, "q_ur": q_ur,
            "degraded": not _POT_AVAILABLE,
        })
    return pd.DataFrame(rows)
