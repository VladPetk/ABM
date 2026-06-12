"""MHV S4 T4.3 — measure the dark-matter budget fractions on the fitted config.

File-based (spawn-safe) so run_seeds_parallel's multiprocessing works — do NOT
run this logic via a `python - <<HEREDOC` stdin script (Windows spawn cannot
re-import __main__ from stdin and the worker pool deadlocks).

Prints the emergent+input-carried fraction per headline metric, so the S4
alignment ratchet (0.50 -> 0.60) can be confirmed against a measured number
before the floor is moved.
"""
from __future__ import annotations

import numpy as np

from abm.calibration_parallel import run_seeds_parallel

SEEDS = tuple(range(6))
ALL_FREEZE = ("elite_drift", "identity_sorting", "coupling", "party_k", "social_media")
METRICS = ["party_sep", "affect", "identity_alignment"]


def main():
    from scripts.audit.audit_lib import freeze_worker
    work = ([(s, (), "full") for s in SEEDS]
            + [(s, ALL_FREEZE, "empty") for s in SEEDS])
    flat = run_seeds_parallel(freeze_worker, work)
    base, froz = flat[: len(SEEDS)], flat[len(SEEDS):]
    print("dark-matter budget fractions (fitted config, 6 seeds):")
    for m in METRICS:
        b0 = np.mean([r["series"][0][m] for r in base])
        b1 = np.mean([r["series"][-1][m] for r in base])
        f1 = np.mean([r["series"][-1][m] for r in froz])
        print(f"  {m:20s} frac={(f1 - b0) / (b1 - b0):.3f}   "
              f"(base {b0:.3f}->{b1:.3f}, frozen {f1:.3f})")


if __name__ == "__main__":
    main()
