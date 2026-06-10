"""Deliverable B — synthetic-recovery + local-identifiability harness (v2).

v2 = MHV T0.5 inference hygiene (review_math.md §9 P0/P1). The published
v1 numbers (docs/internal/audit/phase5_identifiability.json, written up in
docs/internal/identifiability_analysis.md) are contaminated: a discrete
stat (`nmodes_x`, seed-SD exactly 0) hit the MC-SD floor and carried ~99%
of two Jacobian columns, manufacturing the rank-1 cliff and the
party_pull/idpull_x cosine ~= 1.0. v2 changes, in order of consequence:

  1. Fisher/Jacobian consumes CONTINUOUS-tagged stats only
     (battery.STAT_TAGS); discrete stats stay in ABC as soft summaries.
  2. Principled noise model, NO bare floor: per-stat standardization scale
     sigma_i = sqrt(MC_var_i + (EPS_TARGET * prior_range_SD_i)^2), with
     MC variance from 24 baseline seeds (the S1 addendum showed 8 is not
     enough) and a target-measurement-error term proportional to the
     stat's dynamic range across the ABC prior design. The second term is
     load-bearing: schedule-deterministic stats (elite_sep_* — the elite
     trajectory is drift_mult x schedule, seed-free) have MC-SD ~ 1e-16
     of float noise, and a pure-MC-SD scale lets them carry the entire
     Fisher (the v1 bug in another coat — a v2.0 dry-run reproduced it as
     a fake rank-1 spectrum with 1e-29 eigenvalue ratios). The
     target-error reading: no stat can be matched to better than
     EPS_TARGET of its plausible variation.
  3. A known-dead control parameter (`dummy_dead`, noop by construction)
     rides through ABC; its shrinkage is the spurious-contraction floor
     and all shrinkages are also reported net of it.
  4. SBC + coverage (scripts/audit/sbc_harness.py, leave-one-out over the
     ABC reference table) gate the shrinkage numbers. Calibration caveat:
     rejection-ABC posteriors are conservative (over-wide), so SBC shows
     over-coverage + mid-piled ranks for identified params — shrinkages
     are LOWER bounds.
  5. Scale-free column-cosine matrices (hybrid-noise and prior-SD
     standardizations) + effective ranks are standard output — the
     robustness companion the math review asked for (P0.3).

Analyses (unchanged in intent):
  B.2  Local sensitivity: central finite-difference Jacobian at the
       shipped config, seed-averaged; Gauss-Newton Fisher F = J^T J.
  B.1  Synthetic recovery via ABC rejection (ground truth = shipped).
  B.3  Classify each parameter IDENTIFIED / RIDGE / FLAT_AT_SHIPPED /
       INERT_GLOBAL from flat-eigenvector structure + ABC shrinkage.

Run:  .venv/Scripts/python.exe scripts/audit/phase5_identifiability.py
Writes docs/internal/audit/phase5_identifiability_v2.json
(v1 JSON is kept as the published-run record.)
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
    PARAMS, PARAMS_ALL, PARAM_NAMES, PARAM_BASE, STAT_TAGS, battery_worker,
)
from scripts.audit.sbc_harness import abc_sbc

# v2 parameter vector = 8 live params + the dead control (battery.PARAMS_ALL).
P_NAMES = [p[0] for p in PARAMS_ALL]
P_BASE = np.array([p[1] for p in PARAMS_ALL], dtype=float)
P_KINDS = [p[2] for p in PARAMS_ALL]

# Prior ranges (uniform) for the ABC recovery — plausible bands around shipped.
# MHV T0.1: sigma_pc and K_mult were retired from battery.PARAMS (dead/no-op
# knobs); their PRIOR entries are kept only as documentation of the published
# 10-param run (docs/internal/identifiability_analysis.md).
PRIOR = {
    "drift_mult":   (1.0, 6.0),
    "party_pull":   (0.0, 0.10),
    "bc_strength":  (0.0, 0.06),
    "idpull_x":     (0.0, 0.05),
    "idpull_y":     (0.0, 0.08),
    "sigma_pc":     (1.0, 2.5),    # retired (T0.1) — documentation only
    "noise_sigma":  (0.02, 0.10),
    "identity_mult":(0.3, 2.5),
    "animus_mult":  (0.3, 2.5),
    "K_mult":       (0.5, 2.0),    # retired (T0.1) — documentation only
    "dummy_dead":   (0.3, 2.5),    # T0.5 known-dead control (noop)
}
PRIOR_LO = np.array([PRIOR[n][0] for n in P_NAMES])
PRIOR_HI = np.array([PRIOR[n][1] for n in P_NAMES])

BASE_SEEDS = list(range(24))   # v2: SD estimation needs >8 seeds (S1 addendum)
JAC_SEEDS = list(range(8))
JAC_REL_STEP = 0.15            # +/- 15% relative perturbation
ABC_M = 1600                   # prior draws
ABC_SEEDS = [0, 1]             # seeds per prior draw
ABC_ACCEPT = 0.03              # top fraction accepted
EPS_TARGET = 0.01              # target measurement error: 1% of a stat's
                               # SD across the prior design (see docstring 2)


def _vecs(results, names):
    return [[d[n] for n in names] for (_t, _s, d) in results]


def _cosine_matrix(Jm):
    """Pairwise cosine of Jacobian columns (zero columns -> zero rows)."""
    cn = np.linalg.norm(Jm, axis=0)
    cn_safe = np.where(cn > 0, cn, 1.0)
    Jn = Jm / cn_safe
    return Jn.T @ Jn


def _eff_rank(evals):
    """Participation ratio of a (nonneg) eigen-spectrum."""
    ev = np.clip(np.asarray(evals, float), 0.0, None)
    s = ev.sum()
    return float(s * s / ((ev ** 2).sum() + 1e-300)) if s > 0 else 0.0


def main():
    npar = len(P_NAMES)

    # --- baseline: stat names, mean vector, per-stat MC SD (24 seeds) ---
    print(f"baseline ({len(BASE_SEEDS)} seeds) ...")
    base_work = [(tuple(P_BASE.tolist()), s) for s in BASE_SEEDS]
    base_res = run_seeds_parallel(battery_worker, base_work)
    NAMES = list(base_res[0][2].keys())
    base_mat = np.array(_vecs(base_res, NAMES))      # [seeds, nstats]
    s_base = base_mat.mean(0)
    sd_seed = base_mat.std(0, ddof=1)
    nstats = len(NAMES)
    cont_idx = np.array([i for i, n in enumerate(NAMES)
                         if STAT_TAGS[n] == "continuous"], dtype=int)
    discrete_excluded = [n for n in NAMES if STAT_TAGS[n] == "discrete"]
    print(f"stats: {nstats} total, {len(cont_idx)} continuous "
          f"({len(discrete_excluded)} discrete excluded from Fisher)")

    # --- Jacobian sims (central finite diff; raw J, standardized later) ---
    live = [j for j in range(npar) if P_KINDS[j] != "noop"]
    print(f"Jacobian: {len(live)} live params x 2 dirs x {len(JAC_SEEDS)} seeds ...")
    jwork, meta = [], []
    for j in live:
        for sgn in (+1, -1):
            th = P_BASE.copy()
            th[j] = th[j] * (1.0 + sgn * JAC_REL_STEP)
            for s in JAC_SEEDS:
                jwork.append((tuple(th.tolist()), s))
                meta.append((j, sgn))
    jres = run_seeds_parallel(battery_worker, jwork)
    acc = {}
    for (j, sgn), (_t, _s, d) in zip(meta, jres):
        acc.setdefault((j, sgn), []).append([d[n] for n in NAMES])
    J_full = np.zeros((nstats, npar))      # all stats, raw units
    for j in live:
        hi = np.array(acc[(j, +1)]).mean(0)
        lo = np.array(acc[(j, -1)]).mean(0)
        J_full[:, j] = (hi - lo) / (2.0 * JAC_REL_STEP)
    # noop columns stay exactly 0 by construction (negative control).

    # --- ABC sims (also supplies the prior-design dynamic range that the
    #     Fisher noise model needs, so they run before the Fisher math) ---
    print(f"ABC: {ABC_M} prior draws x {len(ABC_SEEDS)} seeds = {ABC_M*len(ABC_SEEDS)} runs ...")
    rng = np.random.default_rng(12345)
    thetas = PRIOR_LO + (PRIOR_HI - PRIOR_LO) * rng.random((ABC_M, npar))
    awork = [(tuple(thetas[m].tolist()), s) for m in range(ABC_M) for s in ABC_SEEDS]
    ares = run_seeds_parallel(battery_worker, awork)
    abuckets = {}
    for theta, seed, d in ares:
        abuckets.setdefault(theta, []).append([d[n] for n in NAMES])
    theta_keys = [tuple(thetas[m].tolist()) for m in range(ABC_M)]
    S = np.array([np.mean(abuckets[k], 0) for k in theta_keys])     # [M, nstats]
    TH = np.array(theta_keys)                                        # [M, npar]
    pscale_full = S.std(0)                 # per-stat SD across the prior design

    # --- Fisher standardization (the v2 noise model) ---
    # sigma_i = sqrt(MC_var + (EPS_TARGET * prior_range_SD)^2). Excluded:
    # discrete stats, and stats fully constant (zero MC SD AND zero prior
    # range — nothing to standardize, nothing to learn).
    fisher_idx, dropped_const = [], []
    for i in cont_idx:
        if sd_seed[i] <= 0.0 and pscale_full[i] <= 0.0:
            dropped_const.append(NAMES[i])
        else:
            fisher_idx.append(i)
    fisher_idx = np.array(fisher_idx, dtype=int)
    F_NAMES = [NAMES[i] for i in fisher_idx]
    scale = np.sqrt(sd_seed[fisher_idx] ** 2
                    + (EPS_TARGET * pscale_full[fisher_idx]) ** 2)
    near_det = [NAMES[i] for i in fisher_idx
                if sd_seed[i] < 1e-3 * max(pscale_full[i], 1e-300)]
    print(f"Fisher: {len(F_NAMES)} stats ({len(dropped_const)} constant dropped: "
          f"{dropped_const}); {len(near_det)} near-deterministic stats kept under "
          f"the target-error term: {near_det}")

    J = J_full[fisher_idx, :]
    J_std = J / scale[:, None]
    colnorm = np.linalg.norm(J_std, axis=0)

    # Fisher (Gauss-Newton) + eigendecomposition
    F = J_std.T @ J_std
    evals, evecs = np.linalg.eigh(F)       # ascending
    order = np.argsort(evals)[::-1]
    evals = evals[order]; evecs = evecs[:, order]
    lam_max = float(evals[0]) if evals[0] > 0 else 1.0

    FLAT_TOL = 1e-2
    flat = []
    for k in range(npar):
        if evals[k] < FLAT_TOL * lam_max:
            v = evecs[:, k]
            pr = (float((v**2).sum())**2) / float((v**4).sum() + 1e-300)
            dom = int(np.argmax(np.abs(v)))
            flat.append({"eigval": float(evals[k]), "eigval_ratio": float(evals[k] / lam_max),
                         "participation_ratio": pr, "dominant_param": P_NAMES[dom],
                         "vector": {P_NAMES[i]: round(float(v[i]), 3) for i in range(npar)}})

    # --- B.1 ABC recovery (ground truth = shipped config) ---
    # global sensitivity: |corr(stat, param)| across the prior design
    gsens = np.zeros((nstats, npar))
    for i in range(nstats):
        for j in range(npar):
            if S[:, i].std() > 1e-12 and TH[:, j].std() > 1e-12:
                gsens[i, j] = abs(np.corrcoef(S[:, i], TH[:, j])[0, 1])

    # ABC distance: ALL stats (incl. discrete — soft summaries with real
    # prior-variance), standardized by prior-SD. v2: no floor; stats with
    # ~zero prior-SD are excluded (they are uninformative, and dividing by
    # a floored epsilon is the v1 bug in another coat).
    abc_mask = pscale_full > 1e-9
    abc_dropped = [NAMES[i] for i in range(nstats) if not abc_mask[i]]
    S_std = S[:, abc_mask] / pscale_full[abc_mask]
    s_obs_std = s_base[abc_mask] / pscale_full[abc_mask]
    d = np.sqrt(((S_std - s_obs_std) ** 2).sum(1))
    k_acc = max(20, int(ABC_ACCEPT * ABC_M))
    acc_idx = np.argsort(d)[:k_acc]
    post = TH[acc_idx]
    prior_sd = (PRIOR_HI - PRIOR_LO) / np.sqrt(12.0)
    post_mean = post.mean(0); post_sd = post.std(0)
    shrink = 1.0 - post_sd / prior_sd
    j_dummy = P_NAMES.index("dummy_dead")
    spurious_floor = float(shrink[j_dummy])
    shrink_net = shrink - spurious_floor
    rec_err = np.abs(post_mean - P_BASE) / prior_sd     # in prior-SD units
    post_corr = np.corrcoef(post.T)

    # --- SBC + coverage over the reference table (T0.5 item 5) ---
    print("SBC (leave-one-out over the ABC reference table) ...")
    sbc = abc_sbc(S_std, TH, PRIOR_LO, PRIOR_HI,
                  accept_frac=ABC_ACCEPT, n_pseudo=200,
                  rng=np.random.default_rng(777))
    sbc_named = {P_NAMES[j]: sbc[j] for j in range(npar)}

    # --- scale-free column-cosine check (standard output, P0.3) ---
    # (a) the hybrid noise standardization (the Fisher's own metric);
    # (b) pure prior-SD standardization (scale-free w.r.t. the seeding-
    # noise estimate). If a cosine conclusion flips between the two, it
    # was metric-induced.
    pscale_fisher = np.maximum(pscale_full[fisher_idx], 1e-12)
    J_prior = J / pscale_fisher[:, None]
    cos_noise = _cosine_matrix(J_std)
    cos_pr = _cosine_matrix(J_prior)
    def _cos_report(C):
        off = []
        for a in range(npar):
            for b in range(a + 1, npar):
                if P_KINDS[a] == "noop" or P_KINDS[b] == "noop":
                    continue
                off.append((P_NAMES[a], P_NAMES[b], round(float(C[a, b]), 3)))
        off.sort(key=lambda t: -abs(t[2]))
        gram_ev = np.linalg.eigvalsh(C[np.ix_(live, live)])
        return {"top_pairs": [list(t) for t in off[:8]],
                "eff_rank_cosine_gram": round(_eff_rank(gram_ev), 2)}
    cosine_out = {
        "noise_standardized": _cos_report(cos_noise),
        "prior_sd_standardized": _cos_report(cos_pr),
        "note": "cosine of Jacobian effect-columns; eff_rank is the "
                "participation ratio of the live-param cosine Gram spectrum",
    }

    # --- B.3 classification ---
    global_sens = gsens.max(0)
    classification = {}
    cn_max = float(colnorm.max()) if colnorm.max() > 0 else 1.0
    CN_FLAT = 0.05
    GS_DEAD = 0.10
    for j, nm in enumerate(P_NAMES):
        cn_rel = float(colnorm[j] / cn_max)
        gs = float(global_sens[j])
        why = []
        owns_solo = any(fd["dominant_param"] == nm and fd["participation_ratio"] < 1.5
                        for fd in flat)
        ridge_dirs = [fd for fd in flat if fd["participation_ratio"] >= 1.5
                      and abs(fd["vector"][nm]) > 0.4]
        partners = sorted({p for fd in ridge_dirs for p in P_NAMES
                           if abs(fd["vector"][p]) > 0.4 and p != nm})
        if P_KINDS[j] == "noop":
            verdict = "CONTROL_DEAD"
            why.append("known-dead by construction (noop); its ABC shrinkage "
                       f"{shrink[j]:.2f} is the spurious-contraction floor")
        elif cn_rel < CN_FLAT and gs < GS_DEAD:
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
            "abc_shrinkage_net_of_floor": round(float(shrink_net[j]), 3),
            "abc_recovery_err_priorSD": round(float(rec_err[j]), 3),
            "sbc": sbc_named[nm],
            "ridge_partners": partners,
            "why": why,
        }

    top_stat = {}
    for j, nm in enumerate(P_NAMES):
        order_i = np.argsort(gsens[:, j])[::-1][:4]
        top_stat[nm] = [(NAMES[i], round(float(gsens[i, j]), 3)) for i in order_i]

    out = {
        "version": 2,
        "hygiene": {
            "baseline_seeds": len(BASE_SEEDS),
            "noise_model": f"sigma = sqrt(mc_var_24seed + ({EPS_TARGET} * prior_design_sd)^2)",
            "fisher_stats": F_NAMES,
            "discrete_excluded_from_fisher": discrete_excluded,
            "constant_excluded_from_fisher": dropped_const,
            "near_deterministic_kept": near_det,
            "abc_zero_priorsd_excluded": abc_dropped,
            "spurious_shrinkage_floor_dummy": round(spurious_floor, 3),
        },
        "param_names": P_NAMES,
        "param_base": P_BASE.tolist(),
        "stat_names": NAMES,
        "baseline_stats": {NAMES[i]: round(float(s_base[i]), 4) for i in range(nstats)},
        "baseline_seed_sd": {NAMES[i]: round(float(sd_seed[i]), 6) for i in range(nstats)},
        "prior_design_sd": {NAMES[i]: round(float(pscale_full[i]), 6) for i in range(nstats)},
        "jacobian_standardized": {F_NAMES[i]: {P_NAMES[j]: round(float(J_std[i, j]), 3)
                                               for j in range(npar)} for i in range(len(F_NAMES))},
        "jac_colnorm": {P_NAMES[j]: round(float(colnorm[j]), 3) for j in range(npar)},
        "fisher_eigenvalues": [round(float(e), 4) for e in evals],
        "fisher_eigval_ratios": [round(float(e / lam_max), 6) for e in evals],
        "fisher_eff_rank": round(_eff_rank(evals), 2),
        "fisher_rank_at_1e-2": int((evals > FLAT_TOL * lam_max).sum()),
        "flat_directions": flat,
        "column_cosines": cosine_out,
        "abc": {
            "n_prior": ABC_M, "n_seeds": len(ABC_SEEDS), "n_accepted": int(k_acc),
            "post_mean": {P_NAMES[j]: round(float(post_mean[j]), 4) for j in range(npar)},
            "post_sd": {P_NAMES[j]: round(float(post_sd[j]), 4) for j in range(npar)},
            "shrinkage": {P_NAMES[j]: round(float(shrink[j]), 3) for j in range(npar)},
            "shrinkage_net_of_floor": {P_NAMES[j]: round(float(shrink_net[j]), 3) for j in range(npar)},
            "recovery_err_priorSD": {P_NAMES[j]: round(float(rec_err[j]), 3) for j in range(npar)},
            "post_corr": {P_NAMES[i]: {P_NAMES[j]: round(float(post_corr[i, j]), 2)
                                       for j in range(npar)} for i in range(npar)},
        },
        "sbc": sbc_named,
        "global_sensitivity_top_stats": top_stat,
        "classification": classification,
    }
    outp = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                        "docs", "internal", "audit",
                                        "phase5_identifiability_v2.json"))
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    # --- console summary ---
    print("\n=== Fisher eigenspectrum (ratio to max) ===")
    print(" ".join(f"{r:.1e}" for r in out["fisher_eigval_ratios"]))
    print(f"eff rank (PR) = {out['fisher_eff_rank']}, "
          f"rank at 1e-2 tol = {out['fisher_rank_at_1e-2']}")
    print(f"\n=== flat directions (eigval < {FLAT_TOL}x max) ===")
    for fd in flat:
        print(f" ratio={fd['eigval_ratio']:.1e} PR={fd['participation_ratio']:.2f} "
              f"dom={fd['dominant_param']:13s} "
              f"{ {k:v for k,v in fd['vector'].items() if abs(v)>0.3} }")
    print("\n=== column cosines (top pairs) ===")
    for tag in ("noise_standardized", "prior_sd_standardized"):
        c = cosine_out[tag]
        print(f" {tag}: eff_rank={c['eff_rank_cosine_gram']} "
              f"top={c['top_pairs'][:3]}")
    print(f"\nspurious shrinkage floor (dummy_dead): {spurious_floor:.3f}")
    print(f"\n{'param':14s} {'verdict':16s} {'colnorm':>8s} {'globsens':>8s} "
          f"{'shrink':>7s} {'net':>7s} {'cov90':>6s} {'ksP':>6s}")
    for nm in P_NAMES:
        c = classification[nm]
        print(f"{nm:14s} {c['verdict']:16s} {c['jac_colnorm_rel']:>8.4f} "
              f"{c['global_sensitivity']:>8.2f} {c['abc_shrinkage']:>7.2f} "
              f"{c['abc_shrinkage_net_of_floor']:>7.2f} "
              f"{c['sbc']['coverage']:>6.2f} {c['sbc']['ks_pvalue']:>6.2f}")
    print(f"\nwrote {outp}")


if __name__ == "__main__":
    main()
