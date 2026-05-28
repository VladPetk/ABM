"""Phase 9 §11.4 — Empirical target audit.

Compare the loaded per-decade pointclouds (data/phase9_empirical/*.npy)
to:
  (a) the brief's stated "Empirical target" row,
  (b) the literature reference table in phase9_empirical_targets.md §3.5.1
      (ANES-anchored moments), and §6.1 (post-augmentation combined cloud).

Goal: identify whether the brief's numbers are stale, and what the
"true" empirical numbers should be.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from abm.calibration_phase9 import (  # noqa: E402
    load_empirical_targets,
    EMPIRICAL_DECADES,
    shape_descriptors,
)


def main():
    target_dir = ROOT / "data" / "phase9_empirical"
    targets = load_empirical_targets(target_dir)

    print(f"{'Decade':<8} {'var_x':>8} {'var_y':>8} {'corr':>7} "
          f"{'|x|':>7} {'|y|':>7} {'q_ll':>7} {'q_lr':>7} {'q_ul':>7} {'q_ur':>7}")
    print("-" * 90)
    for dec in EMPIRICAL_DECADES:
        pc = targets[dec]["pointcloud"]
        d = shape_descriptors(pc)
        q = d["quadrant_mass"]
        print(f"{dec:<8d} {d['var_x']:>8.3f} {d['var_y']:>8.3f} "
              f"{d['corr_xy']:>7.3f} {d['mean_abs_x']:>7.3f} {d['mean_abs_y']:>7.3f} "
              f"{q[0]:>7.3f} {q[1]:>7.3f} {q[2]:>7.3f} {q[3]:>7.3f}")

    print("\nLiterature targets per phase9_empirical_targets.md §3.5.1 (ANES-only):")
    print("Decade   var_x  var_y  corr_xy")
    print("1980     0.32   0.34   +0.18")
    print("1990     0.31   0.32   +0.22")
    print("2000     0.34   0.34   +0.30")
    print("2010     0.36   0.37   +0.41")
    print("2020     0.38   0.40   +0.52")

    print("\nLiterature targets per phase9_empirical_targets.md §6.1 (post-augmentation combined cloud):")
    print("Decade   var_x  var_y  corr_xy")
    print("1980     0.24   0.21   +0.26")
    print("1990     0.23   0.22   +0.27")
    print("2000     0.25   0.26   +0.37")
    print("2010     0.28   0.26   +0.41")
    print("2020     0.29   0.27   +0.57")

    print("\nBrief's 'Empirical target' row:  corr_2020 ~+0.45, var_y_2020 ~0.27, var_y_1980 ~0.34")
    print("(Different sources give different numbers; reconcile in §11.4 of phase9_results.md.)")


if __name__ == "__main__":
    main()
