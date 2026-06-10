"""SBC + coverage harness for simulation-based inference (MHV T0.5).

review_math.md §9 P1.4: no shrinkage or posterior-correlation number gets
quoted without (a) a rank-uniformity check (simulation-based calibration,
Talts et al. 2018 arXiv:1804.06788) and (b) a synthetic coverage check.

`abc_sbc` does both for ABC-rejection at near-zero cost by leave-one-out
over an existing reference table: each prior draw in turn plays the
pseudo-observation, its ABC posterior is the accepted nearest neighbours
among the REMAINING draws, and the pseudo-true theta's rank in each
posterior marginal must be uniform if the inference is calibrated.

Caveat (documented, accepted): each table row's stats are a small-seed
mean while the real observed vector is a many-seed mean, so the
pseudo-observations are NOISIER than the real one — coverage estimated
here is slightly conservative (intervals look wider than needed).

Written engine-agnostic so a future NPE run (phase6-style, or the S4
calibration) can wrap its posterior sampler with `sbc_from_sampler`.
"""
from __future__ import annotations

import numpy as np


def _ks_uniform(u):
    """One-sample KS statistic + asymptotic p-value of u ~ U(0,1)."""
    u = np.sort(np.asarray(u, float))
    n = len(u)
    if n == 0:
        return 0.0, 1.0
    grid = np.arange(1, n + 1) / n
    d = float(np.max(np.maximum(grid - u, u - (grid - 1.0 / n))))
    # Kolmogorov asymptotic survival function
    t = (np.sqrt(n) + 0.12 + 0.11 / np.sqrt(n)) * d
    p = 2.0 * sum((-1.0) ** (k - 1) * np.exp(-2.0 * (k * t) ** 2)
                  for k in range(1, 101))
    return d, float(min(max(p, 0.0), 1.0))


def abc_sbc(S, TH, prior_lo, prior_hi, accept_frac=0.03, n_pseudo=200,
            interval=0.90, rng=None):
    """Leave-one-out SBC + coverage for ABC rejection on a reference table.

    S  : [M, nstats] summary matrix, columns ALREADY standardized the same
         way the production ABC distance standardizes them.
    TH : [M, npar] the prior draws that produced S.
    Returns per-parameter: rank-KS statistic + p-value, central-interval
    coverage at `interval`, and mean shrinkage across pseudo-observations
    (so a production shrinkage can be read against this self-calibrated
    baseline as well as against the dead-control floor).
    """
    S = np.asarray(S, float)
    TH = np.asarray(TH, float)
    M, npar = TH.shape
    rng = rng or np.random.default_rng(0)
    idx = rng.choice(M, size=min(n_pseudo, M), replace=False)
    k_acc = max(20, int(accept_frac * (M - 1)))
    prior_sd = (np.asarray(prior_hi, float) - np.asarray(prior_lo, float)) / np.sqrt(12.0)

    lo_q, hi_q = (1.0 - interval) / 2.0, 1.0 - (1.0 - interval) / 2.0
    ranks = np.zeros((len(idx), npar))
    covered = np.zeros((len(idx), npar), dtype=bool)
    shrinks = np.zeros((len(idx), npar))
    for r, m in enumerate(idx):
        d = np.sqrt(((S - S[m]) ** 2).sum(1))
        d[m] = np.inf                       # leave-one-out
        acc = np.argsort(d)[:k_acc]
        post = TH[acc]
        true = TH[m]
        # mid-rank (ties broken at half) normalized to (0,1)
        ranks[r] = ((post < true).sum(0) + 0.5 * (post == true).sum(0)) / k_acc
        ql = np.quantile(post, lo_q, axis=0)
        qh = np.quantile(post, hi_q, axis=0)
        covered[r] = (true >= ql) & (true <= qh)
        shrinks[r] = 1.0 - post.std(0) / prior_sd

    out = {}
    for j in range(npar):
        ks, p = _ks_uniform(ranks[:, j])
        out[j] = {
            "ks_stat": round(ks, 4),
            "ks_pvalue": round(p, 4),
            "coverage": round(float(covered[:, j].mean()), 4),
            "coverage_target": interval,
            "mean_shrinkage": round(float(shrinks[:, j].mean()), 4),
        }
    return out


def sbc_from_sampler(sample_posterior, simulate, prior_draws, prior_lo,
                     prior_hi, n_post=500, interval=0.90):
    """SBC for an arbitrary amortized posterior (e.g. an NPE): for each
    prior draw theta*, simulate a pseudo-observation, sample the posterior,
    rank theta* in each marginal. Same return shape as `abc_sbc`.

    sample_posterior(x_obs, n) -> [n, npar];  simulate(theta) -> stat vec.
    Compute cost is the caller's problem (one sim + one posterior sample
    per draw) — that is the price of quoting NPE shrinkages honestly.
    """
    prior_draws = np.asarray(prior_draws, float)
    n, npar = prior_draws.shape
    prior_sd = (np.asarray(prior_hi, float) - np.asarray(prior_lo, float)) / np.sqrt(12.0)
    lo_q, hi_q = (1.0 - interval) / 2.0, 1.0 - (1.0 - interval) / 2.0
    ranks = np.zeros((n, npar))
    covered = np.zeros((n, npar), dtype=bool)
    shrinks = np.zeros((n, npar))
    for r in range(n):
        x = simulate(prior_draws[r])
        post = np.asarray(sample_posterior(x, n_post), float)
        true = prior_draws[r]
        ranks[r] = ((post < true).sum(0) + 0.5 * (post == true).sum(0)) / len(post)
        covered[r] = ((true >= np.quantile(post, lo_q, axis=0)) &
                      (true <= np.quantile(post, hi_q, axis=0)))
        shrinks[r] = 1.0 - post.std(0) / prior_sd
    out = {}
    for j in range(npar):
        ks, p = _ks_uniform(ranks[:, j])
        out[j] = {"ks_stat": round(ks, 4), "ks_pvalue": round(p, 4),
                  "coverage": round(float(covered[:, j].mean()), 4),
                  "coverage_target": interval,
                  "mean_shrinkage": round(float(shrinks[:, j].mean()), 4)}
    return out
