"""Deliverable B — synthetic-recovery + local-identifiability harness.

Runs on the CPU-parallel forward sim (no GPU sim exists in this repo). Three
analyses over the 10 load-bearing parameters (battery.PARAMS):

  B.2  Local sensitivity: central finite-difference Jacobian of the 47-stat
       battery w.r.t. each parameter at the shipped config (relative step),
       seed-averaged. Standardize by per-stat Monte-Carlo SD -> Gauss-Newton
       Fisher F = J^T J. Report Jacobian, eigenspectrum, flat eigenvectors.
  B.1  Synthetic recovery via ABC rejection (NPE/sbi unavailable -> ABC is the
       honest fully-parallel SBI substitute): sample a prior, simulate, rank by
       battery distance to a known ground truth (the shipped config), report the
       approximate posterior per parameter (shrinkage = how much we learned).
  B.3  Classify each parameter: IDENTIFIED / RIDGE / INERT, using the flat-
       eigenvector structure (participation ratio) cross-checked against the
       ABC posterior shrinkage + posterior correlations.

Special call-outs: PARTY_ASSIGNMENT_K_ANES (K_mult) and the mega-identity
multiplier (identity_mult) — inert vs ridge, with a why-trace for inert.

Run:  .venv/Scripts/python.exe scripts/audit/phase5_identifiability.py
Writes docs/internal/audit/phase5_identifiability.json
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

import numpy as np

from abm.calibration_parallel import run_seeds_parallel
from scripts.audit.battery import (
    PARAMS, PARAM_NAMES, PARAM_BASE, battery_worker, run_arc_rich, compute_battery,
)

# Prior ranges (uniform) for the ABC recovery — plausible bands around shipped.
# MHV T0.1: sigma_pc and K_mult were retired from battery.PARAMS (dead/no-op
# knobs); their PRIOR entries are kept only as documentation of the published
# 10-param run (docs/internal/identifiability_analysis.md). A re-run uses 8 params.
PRIOR = {
    "drift_mult":   (1.0, 6.0),
    "party_pull":   (0.0, 0.10),
    "bc_strength":  (0.0, 0.06),
    "idpull_x":     (0.0, 0.05),
    "idpull_y":     (0.0, 0.08),
    "sigma_pc":     (1.0, 2.5),
    "noise_sigma":  (0.02, 0.10),
    "identity_mult":(0.3, 2.5),
    "animus_mult":  (0.3, 2.5),
    "K_mult":       (0.5, 2.0),
}
PRIOR_LO = np.array([PRIOR[n][0] for n in PARAM_NAMES])
PRIOR_HI = np.array([PRIOR[n][1] for n in PARAM_NAMES])

JAC_SEEDS = list(range(8))
JAC_REL_STEP = 0.15            # +/- 15% relative perturbation
ABC_M = 1600                   # prior draws
ABC_SEEDS = [0, 1]             # seeds per prior draw
ABC_ACCEPT = 0.03              # top fraction accepted


def _stat_matrix(results, names):
    """results: list of (theta, seed, dict). Returns dict theta_tuple ->
    list of stat-vectors (one per seed)."""
    by = {}
    for theta, seed, d in results:
        by.setdefault(theta, []).append([d[n] for n in names])
    return by


def _vecs(results, names):
    return [[d[n] for n in names] for (_t, _s, d) in results]


def main():
    # --- baseline: stat names, mean vector, per-stat MC SD (8 seeds) ---
    print("baseline (8 seeds) ...")
    base_work = [(tuple(PARAM_BASE.tolist()), s) for s in JAC_SEEDS]
    base_res = run_seeds_parallel(battery_worker, base_work)
    NAMES = list(base_res[0][2].keys())
    base_mat = np.array(_vecs(base_res, NAMES))      # [seeds, nstats]
    s_base = base_mat.mean(0)
    sd_seed = base_mat.std(0, ddof=1)
    # standardization scale: MC SD floored so near-deterministic stats don't blow up
    floor = max(1e-3, 0.1 * float(np.median(sd_seed[sd_seed > 0])))
    scale = np.maximum(sd_seed, floor)
    nstats, npar = len(NAMES), len(PARAMS)

    # --- B.2 Jacobian (central finite diff, relative step, seed-avg) ---
    print(f"Jacobian: {npar} params x 2 dirs x {len(JAC_SEEDS)} seeds ...")
    jwork = []
    meta = []
    for j in range(npar):
        for sgn in (+1, -1):
            th = PARAM_BASE.copy()
            th[j] = th[j] * (1.0 + sgn * JAC_REL_STEP)
            for s in JAC_SEEDS:
                jwork.append((tuple(th.tolist()), s))
                meta.append((j, sgn))
    jres = run_seeds_parallel(battery_worker, jwork)
    # aggregate per (j, sgn): mean stat vector over seeds
    acc = {}
    for (j, sgn), (_t, _s, d) in zip(meta, jres):
        acc.setdefault((j, sgn), []).append([d[n] for n in NAMES])
    J = np.zeros((nstats, npar))           # d stat / d (relative theta), raw
    for j in range(npar):
        hi = np.array(acc[(j, +1)]).mean(0)
        lo = np.array(acc[(j, -1)]).mean(0)
        # relative step in theta units: 2 * JAC_REL_STEP (fractional)
        J[:, j] = (hi - lo) / (2.0 * JAC_REL_STEP)
    J_std = J / scale[:, None]             # standardized by MC SD
    colnorm = np.linalg.norm(J_std, axis=0)

    # Fisher (Gauss-Newton) + eigendecomposition
    F = J_std.T @ J_std
    evals, evecs = np.linalg.eigh(F)       # ascending
    order = np.argsort(evals)[::-1]
    evals = evals[order]; evecs = evecs[:, order]
    lam_max = float(evals[0]) if evals[0] > 0 else 1.0

    # flat directions: eigenvalue below tol * lam_max
    FLAT_TOL = 1e-2
    flat = []
    for k in range(npar):
        if evals[k] < FLAT_TOL * lam_max:
            v = evecs[:, k]
            pr = (float((v**2).sum())**2) / float((v**4).sum() + 1e-300)  # participation ratio
            dom = int(np.argmax(np.abs(v)))
            flat.append({"eigval": float(evals[k]), "eigval_ratio": float(evals[k] / lam_max),
                         "participation_ratio": pr, "dominant_param": PARAM_NAMES[dom],
                         "vector": {PARAM_NAMES[i]: round(float(v[i]), 3) for i in range(npar)}})

    # --- B.1 ABC recovery (ground truth = shipped config) ---
    print(f"ABC: {ABC_M} prior draws x {len(ABC_SEEDS)} seeds = {ABC_M*len(ABC_SEEDS)} runs ...")
    rng = np.random.default_rng(12345)
    thetas = PRIOR_LO + (PRIOR_HI - PRIOR_LO) * rng.random((ABC_M, npar))
    awork = [(tuple(thetas[m].tolist()), s) for m in range(ABC_M) for s in ABC_SEEDS]
    ares = run_seeds_parallel(battery_worker, awork)
    # aggregate per theta over seeds
    abuckets = {}
    for theta, seed, d in ares:
        abuckets.setdefault(theta, []).append([d[n] for n in NAMES])
    theta_keys = [tuple(thetas[m].tolist()) for m in range(ABC_M)]
    S = np.array([np.mean(abuckets[k], 0) for k in theta_keys])     # [M, nstats]
    TH = np.array(theta_keys)                                        # [M, npar]

    # global sensitivity: |corr(stat, param)| across the prior design
    gsens = np.zeros((nstats, npar))
    for i in range(nstats):
        for j in range(npar):
            if S[:, i].std() > 1e-12 and TH[:, j].std() > 1e-12:
                gsens[i, j] = abs(np.corrcoef(S[:, i], TH[:, j])[0, 1])

    # ABC distance to ground truth (shipped). Standardize stats by prior-SD.
    pscale = np.maximum(S.std(0), floor)
    s_obs = s_base
    d = np.sqrt((((S - s_obs) / pscale) ** 2).sum(1))
    k_acc = max(20, int(ABC_ACCEPT * ABC_M))
    acc_idx = np.argsort(d)[:k_acc]
    post = TH[acc_idx]
    prior_sd = (PRIOR_HI - PRIOR_LO) / np.sqrt(12.0)
    post_mean = post.mean(0); post_sd = post.std(0)
    shrink = 1.0 - post_sd / prior_sd
    rec_err = np.abs(post_mean - PARAM_BASE) / prior_sd     # in prior-SD units
    post_corr = np.corrcoef(post.T)

    # --- B.3 classification ---
    # global sensitivity per param = strongest stat correlation across the prior
    global_sens = gsens.max(0)            # [npar]
    classification = {}
    cn_max = float(colnorm.max()) if colnorm.max() > 0 else 1.0
    CN_FLAT = 0.05      # column norm below this (rel to max) = locally flat
    GS_DEAD = 0.10      # global sensitivity below this = no effect anywhere
    for j, nm in enumerate(PARAM_NAMES):
        cn_rel = float(colnorm[j] / cn_max)
        gs = float(global_sens[j])
        why = []
        owns_solo = any(fd["dominant_param"] == nm and fd["participation_ratio"] < 1.5
                        for fd in flat)
        ridge_dirs = [fd for fd in flat if fd["participation_ratio"] >= 1.5
                      and abs(fd["vector"][nm]) > 0.4]
        partners = sorted({p for fd in ridge_dirs for p in PARAM_NAMES
                           if abs(fd["vector"][p]) > 0.4 and p != nm})
        if cn_rel < CN_FLAT and gs < GS_DEAD:
            verdict = "INERT_GLOBAL"
            why.append(f"Jacobian colnorm {cn_rel:.3f}x max AND global sensitivity "
                       f"{gs:.2f} (~0 across the whole prior) — dead everywhere")
            if owns_solo:
                why.append("owns a solo flat eigenvector (PR<1.5)")
        elif cn_rel < CN_FLAT:
            verdict = "FLAT_AT_SHIPPED"
            why.append(f"local Jacobian colnorm {cn_rel:.3f}x max but global sensitivity "
                       f"{gs:.2f} — active across the prior, flat only at the shipped value")
        elif ridge_dirs:
            verdict = "RIDGE"
            why.append(f"in a flat trade-off ridge with {partners}")
        else:
            verdict = "IDENTIFIED"
        classification[nm] = {
            "verdict": verdict,
            "jac_colnorm_rel": round(cn_rel, 4),
            "global_sensitivity": round(gs, 3),
            "abc_shrinkage": round(float(shrink[j]), 3),
            "abc_recovery_err_priorSD": round(float(rec_err[j]), 3),
            "ridge_partners": partners,
            "why": why,
        }

    # top global-sensitivity stat per param (for the writeup)
    top_stat = {}
    for j, nm in enumerate(PARAM_NAMES):
        order_i = np.argsort(gsens[:, j])[::-1][:4]
        top_stat[nm] = [(NAMES[i], round(float(gsens[i, j]), 3)) for i in order_i]

    out = {
        "param_names": PARAM_NAMES,
        "param_base": PARAM_BASE.tolist(),
        "stat_names": NAMES,
        "baseline_stats": {NAMES[i]: round(float(s_base[i]), 4) for i in range(nstats)},
        "jacobian_standardized": {NAMES[i]: {PARAM_NAMES[j]: round(float(J_std[i, j]), 3)
                                             for j in range(npar)} for i in range(nstats)},
        "jac_colnorm": {PARAM_NAMES[j]: round(float(colnorm[j]), 3) for j in range(npar)},
        "fisher_eigenvalues": [round(float(e), 4) for e in evals],
        "fisher_eigval_ratios": [round(float(e / lam_max), 5) for e in evals],
        "flat_directions": flat,
        "abc": {
            "n_prior": ABC_M, "n_seeds": len(ABC_SEEDS), "n_accepted": int(k_acc),
            "post_mean": {PARAM_NAMES[j]: round(float(post_mean[j]), 4) for j in range(npar)},
            "post_sd": {PARAM_NAMES[j]: round(float(post_sd[j]), 4) for j in range(npar)},
            "shrinkage": {PARAM_NAMES[j]: round(float(shrink[j]), 3) for j in range(npar)},
            "recovery_err_priorSD": {PARAM_NAMES[j]: round(float(rec_err[j]), 3) for j in range(npar)},
            "post_corr": {PARAM_NAMES[i]: {PARAM_NAMES[j]: round(float(post_corr[i, j]), 2)
                                           for j in range(npar)} for i in range(npar)},
        },
        "global_sensitivity_top_stats": top_stat,
        "classification": classification,
    }
    outp = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                        "docs", "internal", "audit", "phase5_identifiability.json"))
    with open(outp, "w") as f:
        json.dump(out, f, indent=2)

    # --- console summary ---
    print("\n=== Fisher eigenspectrum (ratio to max) ===")
    print(" ".join(f"{r:.1e}" for r in out["fisher_eigval_ratios"]))
    print(f"\n=== flat directions (eigval < {FLAT_TOL}x max) ===")
    for fd in flat:
        print(f" ratio={fd['eigval_ratio']:.1e} PR={fd['participation_ratio']:.2f} "
              f"dom={fd['dominant_param']:13s} "
              f"{ {k:v for k,v in fd['vector'].items() if abs(v)>0.3} }")
    print(f"\n{'param':14s} {'verdict':16s} {'colnorm':>8s} {'globsens':>8s} {'shrink':>7s} {'recErr':>7s}")
    for nm in PARAM_NAMES:
        c = classification[nm]
        print(f"{nm:14s} {c['verdict']:16s} {c['jac_colnorm_rel']:>8.4f} "
              f"{c['global_sensitivity']:>8.2f} {c['abc_shrinkage']:>7.2f} "
              f"{c['abc_recovery_err_priorSD']:>7.2f}")
    print(f"\nwrote {outp}")


if __name__ == "__main__":
    main()
