"""Phase 8e §5.5 — explicit serial-vs-parallel determinism diff test.

Round-2 R2 asked for an explicit determinism diff (not just trust)
on the parallel-seed runner introduced in Phase 8c §1.5. This test
runs a small ensemble both serially and in parallel and asserts
bit-identical per-seed results.
"""
from __future__ import annotations

import numpy as np

from abm.calibration_parallel import run_seeds_parallel
from tests._parallel_workers import (
    pillar_stage_variance_worker,
    release_metrics_worker,
)


def test_parallel_seed_runner_is_bit_identical_to_serial():
    """Phase 8e §5.5: the parallel-seed runner produces per-seed
    results bit-identical to a serial loop. atol=0 (true bit-identity,
    not just float-close)."""
    seeds = list(range(6))
    args = [(3, s) for s in seeds]  # stage_index=3, six seeds

    serial = [pillar_stage_variance_worker(a) for a in args]
    parallel = run_seeds_parallel(pillar_stage_variance_worker, args)

    # Per-seed tuples (v0, v1) must match exactly.
    for i, (s, p) in enumerate(zip(serial, parallel)):
        assert s == p, (
            f"Determinism broken at seed {seeds[i]}: serial={s}, parallel={p}"
        )


def test_parallel_runner_release_metrics_bit_identical():
    """Same test for the release_metrics_worker — the X-intervention
    measurement path used for §11."""
    seeds = list(range(4))
    args = [("X2_fix_algorithm", s) for s in seeds]

    serial = [release_metrics_worker(a) for a in args]
    parallel = run_seeds_parallel(release_metrics_worker, args)

    for i, (s, p) in enumerate(zip(serial, parallel)):
        assert s["sep"] == p["sep"], (
            f"sep mismatch at seed {seeds[i]}: serial={s['sep']}, parallel={p['sep']}"
        )
        assert s["aff"] == p["aff"], (
            f"aff mismatch at seed {seeds[i]}: serial={s['aff']}, parallel={p['aff']}"
        )
