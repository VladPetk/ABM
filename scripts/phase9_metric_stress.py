"""Phase 9 §11.4 — Metric forensics: what is Wasserstein-2 actually measuring?

Vlad authorized questioning whether 2D Wasserstein is the right metric for
"shape" comparison. This script perturbs the 2020 empirical cloud with
controlled transformations and measures how w2 responds.

Hypotheses to test:
  H1 — w2 is dominated by mean and total-variance differences; anisotropy
       (var_x vs var_y mismatch) shows up as a similar-magnitude penalty.
  H2 — sub-sampling at n_sub=250 retains the signal we care about.
  H3 — the metric punishes shape mismatches at scales comparable to model
       error (Tier C w2_2020 ~ 0.40 vs perfect-match ~ 0.05 sub-sampling
       noise floor).

Outputs to docs/results/phase9_metric_stress.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

# Make abm importable from a script
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from abm.calibration_phase9 import (  # noqa: E402
    wasserstein_2d,
    shape_descriptors,
    load_empirical_targets,
    EMPIRICAL_DECADES,
)


def _stats(label: str, cloud: np.ndarray) -> dict:
    d = shape_descriptors(cloud)
    return {
        "label": label,
        "var_x": d["var_x"],
        "var_y": d["var_y"],
        "corr_xy": d["corr_xy"],
        "mean_abs_x": d["mean_abs_x"],
        "mean_abs_y": d["mean_abs_y"],
        "n": int(cloud.shape[0]),
    }


def main():
    target_dir = ROOT / "data" / "phase9_empirical"
    targets = load_empirical_targets(target_dir)

    # Use 2020 — the decade where the var(y) gap is most acute.
    empirical_2020 = targets[2020]["pointcloud"]
    print("Empirical 2020:", _stats("empirical_2020", empirical_2020))

    rng = np.random.default_rng(20260527)

    results = []

    # 1) Identity baseline -- self vs self with different sub-sample seeds.
    #    Tells us the sub-sampling noise floor.
    w_self = []
    for seed in range(10):
        w = wasserstein_2d(empirical_2020, empirical_2020, n_sub=250, seed=seed)
        w_self.append(w)
    print(f"Self-vs-self (sub-sample noise floor) w2 mean={np.mean(w_self):.4f} std={np.std(w_self):.4f}")
    results.append({
        "test": "self_vs_self_subsample_noise",
        "w2_mean": float(np.mean(w_self)),
        "w2_std": float(np.std(w_self)),
        "n_seeds": 10,
    })

    # 2) Mean shifts -- shift the cloud rigidly by delta on x or y.
    for axis in ["x", "y"]:
        for delta in [0.05, 0.1, 0.2, 0.3]:
            shift = np.array([delta if axis == "x" else 0.0,
                              delta if axis == "y" else 0.0])
            shifted = empirical_2020 + shift
            w = wasserstein_2d(empirical_2020, shifted, n_sub=250, seed=0)
            results.append({
                "test": f"mean_shift_{axis}_{delta}",
                "axis": axis, "delta": delta, "w2": float(w),
            })

    # 3) Anisotropic scaling -- multiply axis values by s.
    #    Tests how w2 responds to var_x and var_y mismatches.
    for axis in ["x", "y"]:
        for scale in [0.3, 0.5, 0.7, 1.3, 1.5]:
            scaled = empirical_2020.copy()
            scaled[:, 0 if axis == "x" else 1] *= scale
            w = wasserstein_2d(empirical_2020, scaled, n_sub=250, seed=0)
            s = shape_descriptors(scaled)
            results.append({
                "test": f"scale_{axis}_{scale}",
                "axis": axis, "scale": scale,
                "var_x_new": s["var_x"], "var_y_new": s["var_y"],
                "w2": float(w),
            })

    # 4) Y-axis collapse -- multiply only y by s ∈ {0.1, 0.2, 0.4, 0.6}.
    #    This is the exact mismatch we observe: var(y) ~3-6x too small.
    for scale in [0.1, 0.2, 0.3, 0.4, 0.6]:
        scaled = empirical_2020.copy()
        scaled[:, 1] *= scale
        w = wasserstein_2d(empirical_2020, scaled, n_sub=250, seed=0)
        s = shape_descriptors(scaled)
        results.append({
            "test": f"y_collapse_{scale}",
            "y_scale": scale,
            "var_y_new": s["var_y"],
            "w2": float(w),
            "var_y_ratio_to_empirical": s["var_y"] / 0.27 if 0.27 else float("nan"),
        })

    # 5) Rotation -- rotate by angle theta degrees.
    for theta_deg in [5, 15, 30, 45]:
        th = np.deg2rad(theta_deg)
        R = np.array([[np.cos(th), -np.sin(th)],
                      [np.sin(th),  np.cos(th)]])
        rotated = empirical_2020 @ R.T
        w = wasserstein_2d(empirical_2020, rotated, n_sub=250, seed=0)
        results.append({
            "test": f"rotation_{theta_deg}deg",
            "theta_deg": theta_deg,
            "w2": float(w),
        })

    # 6) Isotropic Gaussian noise -- adds variance without changing shape.
    for noise_sd in [0.05, 0.1, 0.15, 0.2]:
        noisy = empirical_2020 + rng.normal(0, noise_sd, empirical_2020.shape)
        w = wasserstein_2d(empirical_2020, noisy, n_sub=250, seed=0)
        results.append({
            "test": f"iso_noise_sd_{noise_sd}",
            "noise_sd": noise_sd,
            "w2": float(w),
        })

    # 7) Gaussian fits — how do model-like Gaussian approximations compare?
    emp_mean = empirical_2020.mean(axis=0)
    emp_cov = np.cov(empirical_2020.T)
    print("Empirical mean:", emp_mean, "Empirical cov:", emp_cov)

    # Gaussian #1: matched to empirical mean+cov
    g_matched = rng.multivariate_normal(emp_mean, emp_cov, size=1000)
    w_matched = wasserstein_2d(empirical_2020, g_matched, n_sub=250, seed=0)
    results.append({
        "test": "gaussian_matched_moments",
        "w2": float(w_matched),
        "note": "Gaussian with same mean+cov as empirical — measures KDE-vs-Gaussian shape mismatch",
    })

    # Gaussian #2: matched x but y-collapsed (mimics our model)
    cov_y_collapsed = emp_cov.copy()
    cov_y_collapsed[1, 1] *= 0.15  # var(y) ~6x too small
    cov_y_collapsed[0, 1] *= 0.4   # corr correspondingly affected
    cov_y_collapsed[1, 0] *= 0.4
    g_yc = rng.multivariate_normal(emp_mean, cov_y_collapsed, size=1000)
    w_yc = wasserstein_2d(empirical_2020, g_yc, n_sub=250, seed=0)
    s_yc = shape_descriptors(g_yc)
    results.append({
        "test": "gaussian_y_collapsed",
        "var_x": s_yc["var_x"], "var_y": s_yc["var_y"],
        "w2": float(w_yc),
        "note": "Gaussian with empirical mean+x-var but y-var ~6x too small (mimics Tier C end state)",
    })

    # Save
    out_path = ROOT / "docs" / "results" / "phase9_metric_stress.json"
    out_data = {
        "empirical_2020_stats": _stats("empirical_2020", empirical_2020),
        "tests": results,
    }
    out_path.write_text(json.dumps(out_data, indent=2))
    print(f"Wrote {out_path}")

    # Print headline table
    print("\nHeadline results:")
    print(f"{'test':<45} {'w2':>8}")
    print("-" * 55)
    for r in results:
        if "test" in r and "w2" in r:
            print(f"{r['test']:<45} {r['w2']:>8.4f}")


if __name__ == "__main__":
    main()
