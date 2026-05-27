"""Parallel-seed helper (Phase 8c §1.5).

`run_seeds_parallel(worker_fn, seeds, processes=None)` runs `worker_fn`
on each seed in a worker process, returns results in **seed order** —
the same order as `[worker_fn(s) for s in seeds]`. Bit-identical to
serial execution provided `worker_fn` only depends on its `seed`
argument (no shared mutable state).

Determinism guarantees:

- Results are returned in input order (pool.map preserves it).
- Each worker process has its own numpy RNG state — engines built
  inside the worker use `np.random.default_rng(seed)`, so each
  seed's run is identical regardless of which worker runs it or
  in what order.
- BLAS thread oversubscription is avoided by forcing
  `OMP_NUM_THREADS = OPENBLAS_NUM_THREADS = MKL_NUM_THREADS = 1`
  inside each worker before importing numpy. This is correctness-
  critical, not just performance: BLAS-level summation order can
  produce float drift across runs, breaking bit-identity.

Verified empirically on the pillar (Phase 8c §1.5 benchmark):
12 seeds, N=250, TICKS=200 — serial 48s, parallel 5.4s (9× speedup),
per-seed metric diff 0.00e+00, per-seed position diff 0.00e+00.

Usage:

    from abm.calibration_parallel import run_seeds_parallel

    def my_worker(seed: int) -> dict:
        from abm.pillars.calm_to_camps import build_engine
        # ... build, run, measure ...
        return {"sep": ..., "aff": ...}

    seeds = tuple(range(12))
    results = run_seeds_parallel(my_worker, seeds)
    # results[i] corresponds to seeds[i], same as serial.

**Worker function constraint:** must be importable at module level
(top-level `def`, not a closure / lambda / inner function). On
Windows, `multiprocessing` uses the `spawn` start method, which
pickles the worker by reference — closures don't pickle.
"""
from __future__ import annotations

import os
from typing import Callable, Iterable, List, TypeVar

# Force single-threaded BLAS in *worker* processes. These env vars are
# read by numpy/MKL/OpenBLAS at *import* time, so they only take effect
# in processes where they're set before numpy is imported. Setting them
# here in the parent has no effect on the parent (numpy is already
# imported by the time this module loads). The pool initializer below
# sets them before any numpy import in the worker process.
_BLAS_ENV = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}


def ci_95(values: list[float]) -> tuple[float, float]:
    """Phase 8e §5.4: 95% confidence interval for a small ensemble
    via the t-distribution. Use over `point ± SE` for honest report-
    ing per round-2 R2 ask.

    Returns `(lo, hi)`. For n < 2 returns (mean, mean) (no spread).
    """
    import numpy as np
    arr = np.asarray(values, dtype=float)
    n = len(arr)
    if n < 2:
        return (float(arr.mean()) if n else 0.0, float(arr.mean()) if n else 0.0)
    mean = float(arr.mean())
    se = float(arr.std(ddof=1) / np.sqrt(n))
    # t-critical for 2-tailed 95% CI at df=n-1. For n=15: t≈2.145;
    # n=20: t≈2.093. Use scipy if available, else approximate via
    # the lookup below for common n.
    try:
        from scipy.stats import t
        crit = float(t.ppf(0.975, n - 1))
    except ImportError:
        # Hardcoded t-critical lookup for the common ensemble sizes
        # used in this project. Approximate to 4 decimal places.
        _T_TABLE = {
            5: 2.7764, 6: 2.5706, 10: 2.2622, 12: 2.2010,
            15: 2.1448, 20: 2.0930,
        }
        crit = _T_TABLE.get(n, 2.0)  # fallback ~ normal at large n
    return (mean - crit * se, mean + crit * se)


def _pool_initializer():
    """Run in each worker before any task. Sets BLAS thread count to 1
    to prevent oversubscription (and avoid the rare float-drift risk
    from BLAS summation order)."""
    for k, v in _BLAS_ENV.items():
        os.environ[k] = v


T = TypeVar("T")


def run_seeds_parallel(
    worker_fn: Callable[[int], T],
    seeds: Iterable[int],
    *,
    processes: int | None = None,
    chunksize: int = 1,
) -> List[T]:
    """Run `worker_fn(seed)` for each seed in parallel; return results
    in input order. Bit-identical to `[worker_fn(s) for s in seeds]`.

    `processes` defaults to `min(len(seeds), os.cpu_count() or 1)`. Pass
    `processes=1` to force serial execution (uses the same code path —
    no Pool — for debug / comparison).

    `chunksize` controls how many seeds each worker pulls at a time;
    1 is safest (no biased distribution) but for cheap workers a
    larger chunksize reduces IPC overhead.
    """
    seeds = list(seeds)
    if not seeds:
        return []
    if processes == 1:
        return [worker_fn(s) for s in seeds]
    import multiprocessing as mp
    n_proc = processes if processes is not None else min(
        len(seeds), os.cpu_count() or 1
    )
    # `spawn` start method is the default on Windows and macOS; explicit
    # for cross-platform reproducibility. `fork` (Linux default) inherits
    # the parent's already-loaded numpy, so the BLAS env vars set in
    # `_pool_initializer` arrive too late. `spawn` re-imports numpy
    # fresh in each worker, after the initializer runs.
    ctx = mp.get_context("spawn")
    with ctx.Pool(processes=n_proc, initializer=_pool_initializer) as pool:
        return pool.map(worker_fn, seeds, chunksize=chunksize)
