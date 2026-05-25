"""
Polarization measures over a population of 2D ideology points.

- variance: total dispersion across both axes (sum of per-axis variance).
  Falls as opinions converge, rises with disagreement spread.
- mean_pairwise_distance: average distance between any two agents. Robust
  proxy for polarization; doesn't drop just because everyone moved together.
- bimodality: per-axis bimodality coefficient (Pearson's b). Above ~5/9
  suggests two-peaked distribution; classic signal of partisan split.
- quadrant_counts: how the population splits across the four compass
  quadrants.
"""
from __future__ import annotations

import numpy as np
from scipy.spatial.distance import pdist


def variance(positions: np.ndarray) -> float:
    if len(positions) < 2:
        return 0.0
    return float(np.var(positions, axis=0).sum())


def mean_pairwise_distance(positions: np.ndarray) -> float:
    if len(positions) < 2:
        return 0.0
    return float(pdist(positions).mean())


def bimodality(values: np.ndarray) -> float:
    """Sarle's bimodality coefficient. >5/9 ≈ 0.555 suggests bimodal."""
    n = len(values)
    if n < 4:
        return 0.0
    m = values.mean()
    s = values.std(ddof=1)
    if s == 0:
        return 0.0
    z = (values - m) / s
    g = (z**3).mean()
    k = (z**4).mean() - 3.0
    num = g * g + 1.0
    denom = k + 3.0 * ((n - 1) ** 2) / ((n - 2) * (n - 3))
    if denom <= 0:
        return 0.0
    return float(num / denom)


def quadrant_counts(positions: np.ndarray) -> dict[str, int]:
    if len(positions) == 0:
        return {"lib_left": 0, "lib_right": 0, "auth_left": 0, "auth_right": 0}
    x, y = positions[:, 0], positions[:, 1]
    return {
        "lib_left":   int(((x < 0) & (y < 0)).sum()),
        "lib_right":  int(((x >= 0) & (y < 0)).sum()),
        "auth_left":  int(((x < 0) & (y >= 0)).sum()),
        "auth_right": int(((x >= 0) & (y >= 0)).sum()),
    }
