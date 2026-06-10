"""Part 1 — break the separation ridge with an elite-position (DW-NOMINATE)
target, and replace ABC with a proper NPE (sbi) posterior.

Pipeline:
  1. Generate prior sims in parallel (each (theta, seed) -> battery vector,
     now including the elite-centroid / DW-NOMINATE stats).
  2. Finite-difference Jacobian + Gauss-Newton Fisher at the shipped config,
     on (a) the full battery and (b) the battery WITHOUT the new elite stats,
     so we can isolate what the elite target added. Report eigenspectra,
     effective rank, and the party_pull / idpull_x structure.
  3. Train NPE (sbi) on the prior sims; sample the posterior at the shipped
     observation; report per-param posterior shrinkage + the party_pull <->
     idpull_x posterior correlation, vs the phase-5 ABC (no elite stats).

Honest note: sbi/torch now installed. NPE replaces the phase-5 ABC stand-in.

Run:  .venv/Scripts/python.exe scripts/audit/phase6_npe_ridge.py
Writes docs/internal/audit/phase6_npe_ridge.json
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
from scripts.audit.battery import PARAM_NAMES, PARAM_BASE, battery_worker
from scripts.audit.phase5_identifiability import PRIOR_LO, PRIOR_HI

JAC_SEEDS = list(range(8))
JAC_REL_STEP = 0.15
N_PRIOR = 1500
PRIOR_SEEDS = [0, 1]
ELITE_PREFIXES = ("elite_sep", "mass_elite_gap", "mass_extremity", "dwnom_")


def _vec(d, names):
    return [d[n] for n in names]


def _fisher(Jstd):
    F = Jstd.T @ Jstd
    ev, V = np.linalg.eigh(F)
    o = np.argsort(ev)[::-1]
    return ev[o], V[:, o]


def _eff_rank(ev):
    ev = np.clip(ev, 0, None)
    if ev.sum() <= 0:
        return 0.0
    p = ev / ev.sum()
    p = p[p > 0]
    return float(np.exp(-(p * np.log(p)).sum()))   # participation/entropy rank


def main():
    npar = len(PARAM_NAMES)

    # --- baseline (8 seeds): names, mean, MC SD ---
    print("baseline (8 seeds)...")
    bres = run_seeds_parallel(battery_worker,
                              [(tuple(PARAM_BASE.tolist()), s) for s in JAC_SEEDS])
    NAMES = list(bres[0][2].keys())
    bmat = np.array([_vec(d, NAMES) for _t, _s, d in bres])
    s_base = bmat.mean(0)
    sd_seed = bmat.std(0, ddof=1)
    floor = max(1e-3, 0.1 * float(np.median(sd_seed[sd_seed > 0])))
    scale = np.maximum(sd_seed, floor)
    nstats = len(NAMES)
    elite_idx = [i for i, n in enumerate(NAMES) if n.startswith(ELITE_PREFIXES)]
    base_idx = [i for i in range(nstats) if i not in elite_idx]
    print(f"  {nstats} stats ({len(elite_idx)} new elite stats: "
          f"{[NAMES[i] for i in elite_idx]})")

    # --- Jacobian (finite diff) ---
    print("Jacobian...")
    jwork, meta = [], []
    for j in range(npar):
        for sgn in (+1, -1):
            th = PARAM_BASE.copy(); th[j] *= (1.0 + sgn * JAC_REL_STEP)
            for s in JAC_SEEDS:
                jwork.append((tuple(th.tolist()), s)); meta.append((j, sgn))
    jres = run_seeds_parallel(battery_worker, jwork)
    acc = {}
    for (j, sgn), (_t, _s, d) in zip(meta, jres):
        acc.setdefault((j, sgn), []).append(_vec(d, NAMES))
    J = np.zeros((nstats, npar))
    for j in range(npar):
        hi = np.array(acc[(j, +1)]).mean(0); lo = np.array(acc[(j, -1)]).mean(0)
        J[:, j] = (hi - lo) / (2.0 * JAC_REL_STEP)
    Jstd = J / scale[:, None]

    ev_full, V_full = _fisher(Jstd)
    ev_base, _ = _fisher(Jstd[base_idx, :])     # battery WITHOUT elite stats
    lam = ev_full[0] if ev_full[0] > 0 else 1.0
    lamb = ev_base[0] if ev_base[0] > 0 else 1.0

    def _ratios(ev, l):
        return [round(float(e / l), 5) for e in ev]

    # party_pull / idpull_x Jacobian columns: cosine similarity (how parallel)
    jp = PARAM_NAMES.index("party_pull"); ji = PARAM_NAMES.index("idpull_x")
    def _cos(idx):
        a, b = Jstd[idx, jp], Jstd[idx, ji]
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        return float(a @ b / (na * nb)) if na > 1e-9 and nb > 1e-9 else 0.0
    cos_full = _cos(slice(None)); cos_base = _cos(base_idx)

    # --- NPE (sbi) ---
    print(f"prior sims: {N_PRIOR} draws x {len(PRIOR_SEEDS)} seeds...")
    rng = np.random.default_rng(7)
    thetas = PRIOR_LO + (PRIOR_HI - PRIOR_LO) * rng.random((N_PRIOR, npar))
    pwork = [(tuple(thetas[m].tolist()), s) for m in range(N_PRIOR) for s in PRIOR_SEEDS]
    pres = run_seeds_parallel(battery_worker, pwork)
    TH = np.array([list(t) for (t, _s, _d) in pres], dtype=np.float32)
    X = np.array([_vec(d, NAMES) for (_t, _s, d) in pres], dtype=np.float32)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    print("training NPE (sbi)...")
    import torch
    from sbi.inference import NPE
    from sbi.utils import BoxUniform
    torch.manual_seed(0)
    # z-score stats for training stability
    xm, xs = X.mean(0), X.std(0) + 1e-6
    Xz = (X - xm) / xs
    x_obs = (s_base.astype(np.float32) - xm) / xs
    prior = BoxUniform(low=torch.tensor(PRIOR_LO, dtype=torch.float32),
                       high=torch.tensor(PRIOR_HI, dtype=torch.float32))
    inf = NPE(prior=prior)
    inf.append_simulations(torch.tensor(TH), torch.tensor(Xz))
    inf.train(max_num_epochs=300)
    post = inf.build_posterior()
    samples = post.sample((4000,), x=torch.tensor(x_obs)).numpy()

    prior_sd = (PRIOR_HI - PRIOR_LO) / np.sqrt(12.0)
    post_mean = samples.mean(0); post_sd = samples.std(0)
    shrink = 1.0 - post_sd / prior_sd
    rec_err = np.abs(post_mean - PARAM_BASE) / prior_sd
    pcorr = np.corrcoef(samples.T)
    pp_id_corr = float(pcorr[jp, ji])

    out = {
        "n_stats": nstats, "elite_stats": [NAMES[i] for i in elite_idx],
        "fisher_full_ratios": _ratios(ev_full, lam),
        "fisher_noelite_ratios": _ratios(ev_base, lamb),
        "eff_rank_full": round(_eff_rank(ev_full), 3),
        "eff_rank_noelite": round(_eff_rank(ev_base), 3),
        "party_pull_idpull_jac_cosine_full": round(cos_full, 3),
        "party_pull_idpull_jac_cosine_noelite": round(cos_base, 3),
        "npe": {
            "n_train": len(TH),
            "post_sd": {PARAM_NAMES[j]: round(float(post_sd[j]), 4) for j in range(npar)},
            "shrinkage": {PARAM_NAMES[j]: round(float(shrink[j]), 3) for j in range(npar)},
            "recovery_err_priorSD": {PARAM_NAMES[j]: round(float(rec_err[j]), 3) for j in range(npar)},
            "party_pull_idpull_post_corr": round(pp_id_corr, 3),
            "post_corr": {PARAM_NAMES[i]: {PARAM_NAMES[j]: round(float(pcorr[i, j]), 2)
                                           for j in range(npar)} for i in range(npar)},
        },
        "phase5_reference": {
            "abc_party_pull_idpull_corr": -0.52,
            "note": "phase5 had NO elite stats and used ABC, not NPE.",
        },
    }
    outp = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                        "docs", "internal", "audit", "phase6_npe_ridge.json"))
    with open(outp, "w") as f:
        json.dump(out, f, indent=2)

    print("\n=== Fisher eigval ratios ===")
    print("WITH elite stats   :", out["fisher_full_ratios"])
    print("WITHOUT elite stats:", out["fisher_noelite_ratios"])
    print(f"effective rank: with={out['eff_rank_full']}  without={out['eff_rank_noelite']}")
    print(f"\nparty_pull vs idpull_x Jacobian-column cosine "
          f"(1=parallel/confounded): without={cos_base:.3f}  with={cos_full:.3f}")
    print(f"NPE party_pull<->idpull_x posterior corr: {pp_id_corr:+.3f} "
          f"(phase5 ABC was -0.52)")
    print(f"\n{'param':14s} {'shrink':>7s} {'recErr':>7s}")
    for j, nm in enumerate(PARAM_NAMES):
        print(f"{nm:14s} {shrink[j]:>7.2f} {rec_err[j]:>7.2f}")
    print(f"\nwrote {outp}")


if __name__ == "__main__":
    main()
