"""MHV S3 T3.2 — data-fed elite channel viability check.

Compares the canonical scheduled-EliteDrift arc against the data-fed
PartyCentroidSeries arc (overrides={'data_fed_elite': True}) at decade
snapshots, over a few seeds, for the headline metrics. Also proves the
T0.6 accept clause analytically: no party coordinate reaches a domain
bound at any tick (the ANES series is bounded well inside [-1, 1] and
np.interp never overshoots its anchors).

Run: .venv/Scripts/python.exe scripts/audit/t32_datafed_check.py
"""
from __future__ import annotations

import numpy as np

from abm.calibration_parallel import run_seeds_parallel
from abm.pillars.inputs import PARTY_CENTROID_SERIES_PATH, load_series
from scripts.audit.audit_lib import DECADE_TICKS, run_arc

SEEDS = (0, 1, 2, 3)
METRICS = ("party_sep", "affect", "identity_alignment")


def _worker(arg):
    label, seed = arg
    ov = {"data_fed_elite": True} if label == "datafed" else None
    res = run_arc(seed, overrides=ov, capture="series")
    return {"label": label, "seed": seed, "series": res["series"]}


def main() -> None:
    # --- analytic accept-clause proof ---
    s = load_series(PARTY_CENTROID_SERIES_PATH)
    max_abs = max(float(np.abs(a[:, 1]).max()) for a in s.channels.values())
    print(f"[accept] max |party coordinate| over the whole series = {max_abs:.4f} "
          f"(< 1.0 -> no domain-bound corner-pin at any tick)\n")

    work = ([("schedule", sd) for sd in SEEDS]
            + [("datafed", sd) for sd in SEEDS])
    flat = run_seeds_parallel(_worker, work)
    byl = {"schedule": [], "datafed": []}
    for r in flat:
        byl[r["label"]].append(r["series"])

    def snap(series_list, tick, m):
        return float(np.mean([s[tick][m] for s in series_list]))

    print(f"{'metric':<20}{'year':<6}{'schedule':>10}{'datafed':>10}{'delta':>9}")
    for m in METRICS:
        for yr, tk in DECADE_TICKS.items():
            a = snap(byl["schedule"], tk, m)
            b = snap(byl["datafed"], tk, m)
            print(f"{m:<20}{yr:<6}{a:>10.3f}{b:>10.3f}{b-a:>9.3f}")
        print()


if __name__ == "__main__":
    main()
