"""Phase 8e §5.1 — X6 coop_positive_magnitude sensitivity sweep.

Sweeps `AffectiveUpdate.coop_positive_magnitude` across {0.02, 0.05,
0.08, 0.10} and re-runs X6's §11 release-phase measurement. The
canonical value (0.05) lands X6 at "real on affect" (Δaff = +0.235).
If the bucket flips at lower/higher magnitudes, the headline is
fragile and methods.md §5.3 documents the sensitivity.

Per round-2 R1 + R2 #1 recommendation. All ensembles run via the
parallel-seed runner.

Run: `python scripts/phase8e_coop_positive_sweep.py`.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

from abm.calibration_parallel import run_seeds_parallel
from abm.metrics.affective import affective_polarization
from abm.pillars import PILLAR, X6_SHARED_INSTITUTIONS, apply_intervention
from abm.pillars.calm_to_camps import build_engine
from abm.rules.affective_update import AffectiveUpdate

SEEDS = tuple(range(20))
N = 250
TICKS = 200

MAGNITUDES = [0.02, 0.05, 0.08, 0.10]


def _party_sep(eng):
    parties = np.array([a.state.attrs.get("party") for a in eng.agents])
    pos = eng.positions()
    if (parties == 0).sum() == 0 or (parties == 1).sum() == 0:
        return 0.0
    return float(np.linalg.norm(
        pos[parties == 0].mean(axis=0) - pos[parties == 1].mean(axis=0)
    ))


def classify_aff(daff: float) -> str:
    if abs(daff) < 0.05:
        return "null"
    if 0.05 < daff < 0.15:
        return "partial"
    if daff >= 0.15:
        return "real"
    if daff < -0.05:
        return "backfire"
    return "unclassified"


def _worker(args) -> dict:
    """Args: (magnitude, seed). Build, S4, release with X6 at modified
    coop_positive_magnitude."""
    magnitude, seed = args
    eng = build_engine(seed=seed, n_agents=N)
    apply_intervention(eng, PILLAR.interventions[4])
    eng.run(TICKS)
    # Override the AffectiveUpdate's coop_positive_magnitude.
    for r in eng.rules.rules:
        if type(r).__name__ == "AffectiveUpdate":
            r.coop_positive_magnitude = magnitude
    sep_before = _party_sep(eng)
    aff_before = affective_polarization(eng.agents)
    apply_intervention(eng, X6_SHARED_INSTITUTIONS)
    eng.run(TICKS)
    sep_after = _party_sep(eng)
    aff_after = affective_polarization(eng.agents)
    return {
        "magnitude": magnitude,
        "sep_delta": sep_after - sep_before,
        "aff_delta": aff_after - aff_before,
    }


def main():
    print("=" * 78)
    print("Phase 8e §5.1 — X6 coop_positive_magnitude sensitivity sweep")
    print(f"  N={N}, TICKS={TICKS}, {len(SEEDS)} seeds × {len(MAGNITUDES)} magnitudes")
    print("=" * 78)

    all_args = [(m, s) for m in MAGNITUDES for s in SEEDS]
    results = run_seeds_parallel(_worker, all_args)

    # Group by magnitude.
    by_mag: dict[float, list] = {m: [] for m in MAGNITUDES}
    for r in results:
        by_mag[r["magnitude"]].append(r)

    print("\n  magnitude   Δsep ± SE         Δaff ± SE         affect bucket")
    print("  --------- ----------------  ----------------  ------------")
    sweep_summary = {}
    for m in MAGNITUDES:
        seps = [r["sep_delta"] for r in by_mag[m]]
        affs = [r["aff_delta"] for r in by_mag[m]]
        sep_mean = float(np.mean(seps))
        sep_se = float(np.std(seps, ddof=1) / np.sqrt(len(seps)))
        aff_mean = float(np.mean(affs))
        aff_se = float(np.std(affs, ddof=1) / np.sqrt(len(affs)))
        bucket = classify_aff(aff_mean)
        sweep_summary[str(m)] = {
            "sep_mean": sep_mean,
            "sep_se": sep_se,
            "aff_mean": aff_mean,
            "aff_se": aff_se,
            "affect_bucket": bucket,
        }
        print(
            f"  {m:>9}  {sep_mean:+.4f} ± {sep_se:.4f}  "
            f"{aff_mean:+.4f} ± {aff_se:.4f}  {bucket}"
        )

    print(
        f"\n[stability] X6 affect-bucket robustness across the sweep:"
    )
    buckets = sorted(set(v["affect_bucket"] for v in sweep_summary.values()))
    if len(buckets) == 1:
        print(
            f"  Stable: all four magnitudes land at {buckets[0]!r}. "
            f"X6's affect headline is robust to the calibration choice."
        )
    else:
        print(
            f"  FRAGILE: buckets span {buckets} across {len(MAGNITUDES)} "
            f"magnitudes. methods.md §5.3 must document this."
        )

    out_path = Path("phase8e_coop_positive_sweep.json")
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(sweep_summary, fp, indent=2)
    print(f"\n[dump] {out_path.resolve()}")
    print("\n" + "=" * 78)


if __name__ == "__main__":
    main()
