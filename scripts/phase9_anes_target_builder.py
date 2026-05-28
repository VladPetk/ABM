"""Phase 9 §11.7 — Rebuild per-decade empirical targets from real ANES.

Vlad processed ANES 1986-2024 into `data/phase9_empirical/derived/`.
This script reads `respondent_coordinates.csv` (22,761 rows with year,
party, weight, econ, cult), buckets waves into the engine's five
decades, weight-samples 1000 points per decade, builds Silverman-
bandwidth 50x50 KDEs on [-1, 1]², and writes the .npy files the
existing calibration_phase9 harness expects.

Decade bucketing:
  1980 ← 1986, 1988
  1990 ← 1990, 1992, 1994, 1996, 1998
  2000 ← 2000, 2004, 2008
  2010 ← 2012, 2016
  2020 ← 2020, 2024

The ANES-derived targets OVERWRITE the synthesized .npy files in
data/phase9_empirical/ — but we back them up first to
data/phase9_empirical/synth_backup/ so the synthesized targets are
recoverable.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "phase9_empirical"
DERIVED = DATA / "derived"

DECADES = [1980, 1990, 2000, 2010, 2020]
DECADE_WAVES = {
    1980: [1986, 1988],
    1990: [1990, 1992, 1994, 1996, 1998],
    2000: [2000, 2004, 2008],
    2010: [2012, 2016],
    2020: [2020, 2024],
}
N_POINTCLOUD = 1000        # match the existing build target
GRID_N = 50                # match calibration_phase9 harness expectations


def main():
    df = pd.read_csv(DERIVED / "respondent_coordinates.csv")
    print(f"Loaded {len(df)} ANES respondents across "
          f"{df['year'].nunique()} waves")

    # Back up existing synthesized targets
    backup_dir = DATA / "synth_backup"
    backup_dir.mkdir(exist_ok=True)
    for f in DATA.glob("phase9_empirical_*.npy"):
        # Don't double-backup; only back up files that lack `_synth` suffix
        target = backup_dir / f.name
        if not target.exists():
            shutil.copy(f, target)
    print(f"Backed up synthesized targets to {backup_dir}")

    # Shared grid coords (same convention as before)
    grid = np.linspace(-1.0, 1.0, GRID_N)
    np.save(DATA / "phase9_empirical_grid_x.npy", grid)
    np.save(DATA / "phase9_empirical_grid_y.npy", grid)

    rng = np.random.default_rng(20260528)
    stats_table = []

    for decade in DECADES:
        waves = DECADE_WAVES[decade]
        sub = df[df["year"].isin(waves)].copy()
        print(f"  {decade}: {len(sub)} respondents from waves {waves}")

        # Weighted re-sample to N_POINTCLOUD respondents
        w = sub["weight"].values
        w = w / w.sum()
        idx = rng.choice(len(sub), size=N_POINTCLOUD, replace=True, p=w)
        cloud = sub.iloc[idx][["econ", "cult"]].values.astype(float)

        # Clip to [-1, 1]² to match engine domain
        cloud = np.clip(cloud, -1.0, 1.0)

        # Build KDE on the standard 50x50 grid
        kde = gaussian_kde(cloud.T, bw_method="silverman")
        XX, YY = np.meshgrid(grid, grid)
        pts = np.vstack([XX.ravel(), YY.ravel()])
        Z = kde(pts).reshape(XX.shape)
        # Normalize integral to 1
        integral = float(np.trapz(np.trapz(Z, grid, axis=1), grid))
        if integral > 0:
            Z = Z / integral

        # Save
        np.save(DATA / f"phase9_empirical_pointcloud_{decade}.npy", cloud)
        np.save(DATA / f"phase9_empirical_kde_{decade}.npy", Z)

        # Per-decade summary stats
        vx = float(cloud[:, 0].var())
        vy = float(cloud[:, 1].var())
        cxy = float(np.corrcoef(cloud.T)[0, 1])
        mx = float(cloud[:, 0].mean())
        my = float(cloud[:, 1].mean())
        stats_table.append({
            "decade": decade, "n_in_cloud": N_POINTCLOUD,
            "n_anes_source": len(sub),
            "var_x": vx, "var_y": vy, "corr_xy": cxy,
            "mean_x": mx, "mean_y": my,
            "waves": waves,
        })
        print(f"    var_x={vx:.3f} var_y={vy:.3f} corr={cxy:+.3f}")

    # Save metadata
    with open(DATA / "phase9_empirical_build_anes.json", "w") as f:
        json.dump({
            "source": "ANES 1986-2024 (Vlad's data/phase9_empirical/derived/)",
            "n_respondents_total": len(df),
            "decade_waves": {str(k): v for k, v in DECADE_WAVES.items()},
            "stats": stats_table,
            "build_date": "2026-05-28",
        }, f, indent=2)
    print(f"\nWrote new ANES-derived targets to {DATA}")
    print(f"Synthesized backup at {backup_dir}")


if __name__ == "__main__":
    main()
