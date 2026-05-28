"""Phase 9 — measure within-party cluster shape (eigenvalue ratio +
principal-axis angle) for ANES and the engine, to diagnose whether
the engine's clusters are round vs the ANES-elongated ones.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np
import pandas as pd


def _shape_stats(xy, label):
    if len(xy) < 5:
        return
    cov = np.cov(xy.T)
    evals, evecs = np.linalg.eigh(cov)
    major, minor = float(evals[1]), float(evals[0])
    ratio = major / minor if minor > 0 else float("inf")
    v = evecs[:, -1]
    angle_deg = float(np.degrees(np.arctan2(v[1], v[0])))
    if angle_deg < -90:
        angle_deg += 180
    if angle_deg > 90:
        angle_deg -= 180
    corr = float(cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1]))
    print(
        f"  {label:>18}: "
        f"sx={np.sqrt(cov[0, 0]):.3f} sy={np.sqrt(cov[1, 1]):.3f}  "
        f"corr={corr:+.3f}  "
        f"axis_angle={angle_deg:+5.1f}deg  "
        f"major/minor={ratio:.2f}"
    )


def _worker(seed):
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from scripts.phase9_anes_score import PRESETS

    eng = build_engine(seed=seed, **PRESETS["anes_full"])
    sched = build_schedule(factional_seeding=False, faction_anchor_events=True)
    out = {}
    for year, tick in [(2010, 102), (2020, 126)]:
        run_to(eng, sched, tick)
        out[year] = {
            "pos": np.array([a.state.ideology for a in eng.agents]),
            "party": np.array(
                [a.state.attrs.get("party", -1) for a in eng.agents]
            ),
        }
    return out


def main():
    from abm.calibration_parallel import run_seeds_parallel

    print("ANES within-party shape:")
    df = pd.read_csv("data/phase9_empirical/derived/respondent_coordinates.csv")
    for decade, waves in [
        (2010, [2012, 2016]),
        (2020, [2020, 2024]),
    ]:
        sub = df[(df["year"].isin(waves)) & (df["party"].isin(["D", "R"]))]
        for party_label in ("D", "R"):
            xy = sub[sub["party"] == party_label][["econ", "cult"]].to_numpy()
            _shape_stats(xy, f"ANES {decade} {party_label}")
        print()

    print("\nEngine within-party shape (anes_full, 5 seeds pooled):")
    results = run_seeds_parallel(_worker, list(range(5)))
    for year in (2010, 2020):
        for party_id, party_label in [(0, "D"), (1, "R")]:
            xy = np.vstack([
                r[year]["pos"][r[year]["party"] == party_id]
                for r in results
            ])
            _shape_stats(xy, f"engine {year} {party_label}")
        print()


if __name__ == "__main__":
    main()
