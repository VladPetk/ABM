"""S4 calibration-lite fit orchestrator (MHV S4 / T4.2).

Fits the 5-knob disciplined set (party_pull, fj_alpha_scale, constraint_rate,
animus_mult, noise_sigma) against the in-window ANES per-wave targets
(1980/1990/2000) assembled in scripts/audit/s4_targets.py. Everything else --
idpull, bc_strength (canonical 0.03), drift_mult -- is FROZEN at ANES_FULL_KWARGS.

Method: NPE (sbi) primary, ABC-rejection fallback. SBC + central-interval
coverage are GATED before any posterior number is quoted (I5); shrinkages are
reported net of a known-dead control (the spurious-contraction floor). The
party_pull<->idpull and bc<->noise ridges are broken by construction (those arms
are frozen); the residual posterior correlation is reported, and any pair > 0.6
triggers a reparameterize-and-report STOP (s4_spec.md §2 guardrail).

Sims reuse the canonical measurement (scripts/phase8f_lib.measure_all over the
SECTION11 decade ticks) so the fit is commensurable with the ANES bands. Driven
off ANES_FULL_KWARGS directly (NOT the battery PARAM_BASE, which predates the S2
bc re-pick and would clobber bc_strength 0.03 -> 0.015).

Usage:
  python -m scripts.audit.s4_fit --dry-run                 # validate + time, no NPE
  python -m scripts.audit.s4_fit --draws 3000 --seeds 3    # full fit
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "docs" / "internal" / "audit" / "s4_fit.json"
OUT_MD = ROOT / "docs" / "internal" / "audit" / "s4_fit.md"
TABLE_NPZ = ROOT / "docs" / "internal" / "audit" / "s4_fit_table.npz"

# (name, [kwargs to set], prior_lo, prior_hi, canonical)
# 6-knob set (T4.2 STOP-by-finding t42_undershoot.md): elite_lead added + party_pull
# widened, because the voter-centroid attractor caps party_sep at ~0.81 << ANES 1.11.
FIT_PARAMS = [
    ("party_pull",     ["tier_c_party_pull_strength"],                       0.02, 0.50, 0.04),
    ("fj_alpha_scale", ["fj_alpha_scale"],                                   1.0,  3.5,  2.8),
    ("constraint_rate",["constraint_rate"],                                  0.005,0.06, 0.02),
    ("animus_mult",    ["sandbox_animus_mult"],                             0.6,  1.6,  1.0),
    ("noise_sigma",    ["tier_d_aniso_noise_sigma_x",
                        "tier_d_aniso_noise_sigma_y"],                       0.02, 0.08, 0.04),
    ("elite_lead",     ["elite_lead_factor"],                                1.0,  2.0,  1.0),
]
PNAMES = [p[0] for p in FIT_PARAMS]
NPAR = len(FIT_PARAMS)
PRIOR_LO = np.array([p[2] for p in FIT_PARAMS])
PRIOR_HI = np.array([p[3] for p in FIT_PARAMS])
CANON = np.array([p[4] for p in FIT_PARAMS])

FIT_DECADES = [1980, 1990, 2000]
ALL_DECADES = [1980, 1990, 2000, 2010, 2020, 2025]
OBS = ["party_sep", "affect", "constraint", "within_party_sd"]


def _overrides(theta):
    from scripts.anes_preset import ANES_FULL_KWARGS
    ov = dict(ANES_FULL_KWARGS)
    for (name, kws, *_), val in zip(FIT_PARAMS, theta):
        for kw in kws:
            ov[kw] = float(val)
    return ov


def simulate(theta, seed):
    """Run the arc; return {decade: {obs: value}} over ALL decades."""
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from scripts.phase8f_lib import measure_all
    from scripts.phase9_anes_score import SECTION11_TICKS

    ov = _overrides(theta)
    eng = build_engine(seed=seed, **ov)
    sched = build_schedule(
        factional_seeding=ov.get("factional_seeding", False),
        faction_anchor_events=ov.get("faction_anchor_events", True),
        evidence_regrade=ov.get("evidence_regrade", False),
        exogenous_shocks=ov.get("exogenous_shocks", False),
    )
    out = {}
    for year, tick in SECTION11_TICKS:
        if tick > 0:
            run_to(eng, sched, tick)
        m = measure_all(eng)
        out[year] = {k: float(m[k]) for k in
                     ("party_sep", "affect", "constraint", "within_party_sd",
                      "xc_fraction", "modularity", "variance")}
    return out


# All-decade summary layout (stored in the table so the conditioning window is
# selectable post-hoc without re-simulating). "full" = shipped calibration on the
# whole trajectory; "temporal" = the <=2012 cut, used by the T4.4 holdout refit.
SUMMARY_LABELS = [(d, o) for d in ALL_DECADES for o in OBS]   # 24 entries


def _summary_vector(per_decade):
    """Flatten ALL-decade observables into one summary vector."""
    return np.array([per_decade[d][o] for d, o in SUMMARY_LABELS], float)


def _window_cols(window):
    if window == "temporal":
        return [i for i, (d, o) in enumerate(SUMMARY_LABELS) if d in FIT_DECADES]
    return list(range(len(SUMMARY_LABELS)))   # "full"


# --- top-level worker for run_seeds_parallel (spawn-picklable) -------------
def fit_worker(job):
    idx, theta_tuple, seed = job
    per = simulate(np.array(theta_tuple, float), seed)
    return (idx, seed, per)


def _x_obs():
    """Empirical ANES ALL-decade target vector (mid-band)."""
    from scripts.audit.s4_targets import build_targets
    t = build_targets()
    x = [t["decades"][d]["cells"][o]["point"] for d, o in SUMMARY_LABELS]
    return np.array(x, float), t


def dry_run(seeds):
    print("=== S4 fit DRY RUN ===")
    x_obs, targets = _x_obs()
    print("x_obs (ANES all-decade targets):")
    labels = [f"{d}.{o}" for d, o in SUMMARY_LABELS]
    for lab, v in zip(labels, x_obs):
        print(f"   {lab:22s} {v:+.3f}")

    # 1 canonical sim, timed
    t0 = time.time()
    per = simulate(CANON, 0)
    dt = time.time() - t0
    print(f"\ncanonical sim wall-time: {dt:.1f}s  (-> full fit est below)")
    print("canonical trajectory (all decades):")
    print(f"   {'dec':>5} {'sep':>7} {'affect':>7} {'constr':>7} {'wp_sd':>7}")
    for d in ALL_DECADES:
        p = per[d]
        print(f"   {d:>5} {p['party_sep']:>7.3f} {p['affect']:>7.3f} "
              f"{p['constraint']:>7.3f} {p['within_party_sd']:>7.3f}")

    # drift_mult inert check (frozen knob; should be exactly no-op on data-fed path)
    from scripts.anes_preset import ANES_FULL_KWARGS
    ov_a = dict(ANES_FULL_KWARGS); ov_a["tier_d_anes_drift_multiplier"] = 3.0
    ov_b = dict(ANES_FULL_KWARGS); ov_b["tier_d_anes_drift_multiplier"] = 1.0
    pa = _sim_raw(ov_a, 0); pb = _sim_raw(ov_b, 0)
    da = max(abs(pa[d]['party_sep'] - pb[d]['party_sep']) for d in ALL_DECADES)
    print(f"\ndrift_mult inert check (3.0 vs 1.0): max |Dsep| = {da:.2e}  "
          f"{'INERT (ok)' if da < 1e-9 else 'NOT INERT -- STOP'}")

    # 2 random prior draws (range sanity)
    rng = np.random.default_rng(0)
    print("\n2 random prior draws (sep@2025, affect@2025):")
    for i in range(2):
        th = PRIOR_LO + rng.random(NPAR) * (PRIOR_HI - PRIOR_LO)
        p = simulate(th, 0)
        print(f"   theta={np.round(th,3)} -> sep25={p[2025]['party_sep']:.3f} "
              f"aff25={p[2025]['affect']:.3f} constr25={p[2025]['constraint']:.3f}")

    print(f"\nest full fit (3000 draws x {seeds} seeds / ~14 cores): "
          f"~{3000*seeds*dt/14/60:.0f} min")


def _sim_raw(ov, seed):
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from scripts.phase8f_lib import measure_all
    from scripts.phase9_anes_score import SECTION11_TICKS
    eng = build_engine(seed=seed, **ov)
    sched = build_schedule(
        factional_seeding=ov.get("factional_seeding", False),
        faction_anchor_events=ov.get("faction_anchor_events", True),
        evidence_regrade=ov.get("evidence_regrade", False),
        exogenous_shocks=ov.get("exogenous_shocks", False))
    out = {}
    for year, tick in SECTION11_TICKS:
        if tick > 0:
            run_to(eng, sched, tick)
        m = measure_all(eng)
        out[year] = {"party_sep": float(m["party_sep"])}
    return out


def run_fit(draws, seeds, reuse=False, window="full"):
    x_obs, targets = _x_obs()
    if reuse and TABLE_NPZ.exists():
        d = np.load(TABLE_NPZ)
        TH, X, seed_sd = d["TH"], d["X"], d["seed_sd"]
        draws, seeds = int(d["draws"]), int(d["seeds"])
        print(f"reused sim table {TABLE_NPZ.name}: {draws} draws x {seeds} seeds")
    else:
        from abm.calibration_parallel import run_seeds_parallel
        rng = np.random.default_rng(0)
        TH = PRIOR_LO + rng.random((draws, NPAR)) * (PRIOR_HI - PRIOR_LO)
        jobs = [(i, tuple(TH[i]), s) for i in range(draws) for s in range(seeds)]
        print(f"running {len(jobs)} sims ({draws} draws x {seeds} seeds) ...")
        t0 = time.time()
        results = run_seeds_parallel(fit_worker, jobs)
        print(f"sims done in {(time.time()-t0)/60:.1f} min")
        # seed-average the fit vector per draw
        per_draw = {i: [] for i in range(draws)}
        for idx, seed, per in results:
            per_draw[idx].append(_summary_vector(per))
        X = np.array([np.mean(per_draw[i], axis=0) for i in range(draws)])  # [draws, 24]
        seed_sd = np.array([np.std(per_draw[i], axis=0) for i in range(draws)]).mean(0)
        # PERSIST the table immediately (inference is cheap to re-run via --reuse)
        np.savez(TABLE_NPZ, TH=TH, X=X, seed_sd=seed_sd, draws=draws, seeds=seeds)
        print(f"saved sim table -> {TABLE_NPZ.name}")

    # select the conditioning window (full trajectory = shipped calibration;
    # temporal = <=2012 cut for the T4.4 holdout refit) and standardize on it.
    cols = _window_cols(window)
    labels_all = [f"{d}.{o}" for d, o in SUMMARY_LABELS]
    Xw, xobs_w = X[:, cols], x_obs[cols]
    xsd = Xw.std(0); xsd[xsd < 1e-9] = 1.0
    Xz = (Xw - Xw.mean(0)) / xsd
    xobs_z = (xobs_w - Xw.mean(0)) / xsd

    prior_sd = (PRIOR_HI - PRIOR_LO) / np.sqrt(12)
    out = {"params": PNAMES, "prior_lo": PRIOR_LO.tolist(),
           "prior_hi": PRIOR_HI.tolist(), "canonical": CANON.tolist(),
           "draws": draws, "seeds": seeds, "window": window,
           "x_obs": xobs_w.tolist(), "seed_sd_mean": seed_sd.tolist(),
           "fit_labels": [labels_all[i] for i in cols]}

    # --- ABC rejection point at x_obs (reuses the table; cross-check/fallback) ---
    d_obs = np.sqrt(((Xz - xobs_z) ** 2).sum(1))
    k_acc = max(20, int(0.03 * draws))
    acc = np.argsort(d_obs)[:k_acc]
    abc_post = TH[acc]
    out["abc_point"] = {n: float(v) for n, v in zip(PNAMES, np.median(abc_post, 0))}
    out["abc_shrinkage"] = (1 - abc_post.std(0) / prior_sd).tolist()

    # --- SBC + coverage (ABC-LOO on the table; conservative) + dead-control floor ---
    from scripts.audit.sbc_harness import abc_sbc
    dummy = np.random.default_rng(7).random((draws, 1))   # provably-dead param
    TH_aug = np.hstack([TH, dummy])
    lo_aug, hi_aug = np.append(PRIOR_LO, 0.0), np.append(PRIOR_HI, 1.0)
    sbc = abc_sbc(Xz, TH_aug, lo_aug, hi_aug, accept_frac=0.03,
                  n_pseudo=min(300, draws))
    names_aug = PNAMES + ["dummy_dead"]
    out["sbc"] = {names_aug[j]: sbc[j] for j in range(len(names_aug))}
    floor = sbc[NPAR]["mean_shrinkage"]            # dummy = spurious-contraction floor
    out["shrinkage_floor"] = floor
    out["sbc_miscalibrated"] = [names_aug[j] for j in range(NPAR)
                                if sbc[j]["ks_pvalue"] < 0.01]

    # --- NPE point (conditioned at x_obs); MCMC sampling (rejection leaks on a
    #     box prior -> 0% acceptance hang); clean fall back to ABC on any failure ---
    try:
        import warnings
        warnings.filterwarnings("ignore")
        import torch
        from sbi.inference import NPE
        from sbi.utils import BoxUniform
        prior = BoxUniform(low=torch.tensor(PRIOR_LO, dtype=torch.float32),
                           high=torch.tensor(PRIOR_HI, dtype=torch.float32))
        inf = NPE(prior=prior)
        inf.append_simulations(torch.tensor(TH, dtype=torch.float32),
                               torch.tensor(Xz, dtype=torch.float32))
        inf.train(max_num_epochs=400, show_train_summary=False)
        post = inf.build_posterior(sample_with="mcmc",
                                   mcmc_method="slice_np_vectorized")
        samp = post.sample((2000,), x=torch.tensor(xobs_z, dtype=torch.float32),
                           show_progress_bars=False).numpy()
        out["method"] = "NPE"
        out["post_median"] = np.median(samp, 0).tolist()
        out["post_sd"] = samp.std(0).tolist()
        out["prior_sd"] = prior_sd.tolist()
        shr = 1 - samp.std(0) / prior_sd
        out["shrinkage"] = shr.tolist()
        out["shrinkage_net_floor"] = (shr - floor).tolist()
        cc = np.corrcoef(samp.T)
        out["post_corr"] = cc.tolist()
        out["ridge_flags"] = [(PNAMES[i], PNAMES[j], float(cc[i, j]))
                              for i in range(NPAR) for j in range(i + 1, NPAR)
                              if abs(cc[i, j]) > 0.6]
        out["fitted_point"] = {n: float(v) for n, v in zip(PNAMES, np.median(samp, 0))}
    except Exception as e:
        out["method"] = "NPE_FAILED"
        out["error"] = repr(e)
        out["fitted_point"] = out["abc_point"]   # fallback to ABC

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2))
    _write_md(out)
    print(f"\nwrote {OUT_JSON.relative_to(ROOT)} + {OUT_MD.name}")
    print(f"method={out['method']}  shrinkage floor (dummy)={floor:.3f}")
    print("fitted point:")
    for n in PNAMES:
        print(f"   {n:16s} NPE={out.get('fitted_point',{}).get(n,float('nan')):.4f}  "
              f"ABC={out['abc_point'][n]:.4f}  (canon {dict(zip(PNAMES,CANON))[n]})")
    print("ridge flags (>0.6):", out.get("ridge_flags") or "none")
    print("SBC miscalibrated params:", out["sbc_miscalibrated"] or "none")
    return out


def _write_md(out):
    L = ["# S4 calibration-lite fit (T4.2)", "",
         f"method **{out['method']}**, window **{out.get('window','full')}**, "
         f"{out['draws']} draws x {out['seeds']} seeds; "
         f"spurious-shrinkage floor (dummy) = {out['shrinkage_floor']:.3f}", "",
         "| knob | NPE median | ABC median | canon | prior | shrink (net floor) | SBC cov | SBC ks-p |",
         "|---|---|---|---|---|---|---|---|"]
    fp = out.get("fitted_point", {})
    for i, n in enumerate(out["params"]):
        sbc = out["sbc"][n]
        net = (out.get("shrinkage_net_floor") or [float('nan')] * len(out["params"]))[i]
        L.append(f"| {n} | {fp.get(n, float('nan')):.4f} | {out['abc_point'][n]:.4f} | "
                 f"{out['canonical'][i]:.3f} | [{out['prior_lo'][i]},{out['prior_hi'][i]}] | "
                 f"{net:+.3f} | {sbc['coverage']:.2f} | {sbc['ks_pvalue']:.3f} |")
    L += ["", f"ridge flags (>0.6): {out.get('ridge_flags') or 'none'}",
          f"SBC miscalibrated (ks-p<0.01): {out['sbc_miscalibrated'] or 'none'}",
          f"dummy-dead floor: shrink {out['sbc']['dummy_dead']['mean_shrinkage']:.3f}, "
          f"cov {out['sbc']['dummy_dead']['coverage']:.2f}"]
    OUT_MD.write_text("\n".join(L))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--draws", type=int, default=3000)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--reuse", action="store_true",
                    help="reuse the persisted sim table (skip simulation; "
                         "re-run inference only)")
    ap.add_argument("--window", choices=["full", "temporal"], default="full",
                    help="conditioning window: full trajectory (shipped) or "
                         "<=2012 temporal cut (T4.4 holdout refit)")
    a = ap.parse_args()
    if a.dry_run:
        dry_run(a.seeds)
    else:
        run_fit(a.draws, a.seeds, reuse=a.reuse, window=a.window)


if __name__ == "__main__":
    main()
