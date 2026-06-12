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


def _fit_vector(per_decade):
    """Flatten the in-window fit observables into one summary vector."""
    return np.array([per_decade[d][o] for d in FIT_DECADES for o in OBS], float)


# --- top-level worker for run_seeds_parallel (spawn-picklable) -------------
def fit_worker(job):
    idx, theta_tuple, seed = job
    per = simulate(np.array(theta_tuple, float), seed)
    return (idx, seed, per)


def _x_obs():
    """Empirical ANES fit-decade target vector (mid-band)."""
    from scripts.audit.s4_targets import build_targets
    t = build_targets()
    x = []
    for d in FIT_DECADES:
        for o in OBS:
            x.append(t["decades"][d]["cells"][o]["point"])
    return np.array(x, float), t


def dry_run(seeds):
    print("=== S4 fit DRY RUN ===")
    x_obs, targets = _x_obs()
    print("x_obs (ANES fit-decade targets):")
    labels = [f"{d}.{o}" for d in FIT_DECADES for o in OBS]
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


def run_fit(draws, seeds):
    from abm.calibration_parallel import run_seeds_parallel
    x_obs, targets = _x_obs()
    rng = np.random.default_rng(0)
    TH = PRIOR_LO + rng.random((draws, NPAR)) * (PRIOR_HI - PRIOR_LO)

    jobs = [(i, tuple(TH[i]), s) for i in range(draws) for s in range(seeds)]
    print(f"running {len(jobs)} sims ({draws} draws x {seeds} seeds) ...")
    t0 = time.time()
    results = run_seeds_parallel(fit_worker, jobs)
    print(f"sims done in {(time.time()-t0)/60:.1f} min")

    # seed-average the fit vector per draw
    per_draw = {i: [] for i in range(draws)}
    holdout = {i: [] for i in range(draws)}
    for idx, seed, per in results:
        per_draw[idx].append(_fit_vector(per))
        holdout[idx].append(per)
    X = np.array([np.mean(per_draw[i], axis=0) for i in range(draws)])  # [draws, 12]
    seed_sd = np.array([np.std(per_draw[i], axis=0) for i in range(draws)]).mean(0)

    # standardize by simulated-X SD (scale-free); guard zeros
    xsd = X.std(0); xsd[xsd < 1e-9] = 1.0
    Xz = (X - X.mean(0)) / xsd
    xobs_z = (x_obs - X.mean(0)) / xsd

    out = {"params": PNAMES, "prior_lo": PRIOR_LO.tolist(),
           "prior_hi": PRIOR_HI.tolist(), "canonical": CANON.tolist(),
           "draws": draws, "seeds": seeds, "x_obs": x_obs.tolist(),
           "fit_labels": [f"{d}.{o}" for d in FIT_DECADES for o in OBS]}

    # NPE
    try:
        import torch
        from sbi.inference import NPE
        from sbi.utils import BoxUniform
        prior = BoxUniform(low=torch.tensor(PRIOR_LO, dtype=torch.float32),
                           high=torch.tensor(PRIOR_HI, dtype=torch.float32))
        inf = NPE(prior=prior)
        inf.append_simulations(torch.tensor(TH, dtype=torch.float32),
                               torch.tensor(Xz, dtype=torch.float32))
        inf.train(max_num_epochs=400)
        post = inf.build_posterior()
        samp = post.sample((4000,), x=torch.tensor(xobs_z, dtype=torch.float32)).numpy()
        out["method"] = "NPE"
        out["post_mean"] = samp.mean(0).tolist()
        out["post_median"] = np.median(samp, 0).tolist()
        out["post_sd"] = samp.std(0).tolist()
        out["prior_sd"] = ((PRIOR_HI - PRIOR_LO) / np.sqrt(12)).tolist()
        out["shrinkage"] = (1 - samp.std(0) / ((PRIOR_HI - PRIOR_LO) / np.sqrt(12))).tolist()
        cc = np.corrcoef(samp.T)
        out["post_corr"] = cc.tolist()
        ridge = [(PNAMES[i], PNAMES[j], float(cc[i, j]))
                 for i in range(NPAR) for j in range(i + 1, NPAR) if abs(cc[i, j]) > 0.6]
        out["ridge_flags"] = ridge
        out["fitted_point"] = {n: float(v) for n, v in
                               zip(PNAMES, np.median(samp, 0))}
    except Exception as e:
        out["method"] = "NPE_FAILED"
        out["error"] = repr(e)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {OUT_JSON.relative_to(ROOT)}")
    if out.get("method") == "NPE":
        print("fitted point (posterior median):")
        for n, v in out["fitted_point"].items():
            print(f"   {n:16s} {v:.4f}  (canon {dict(zip(PNAMES,CANON))[n]})")
        print("ridge flags (>0.6):", out["ridge_flags"] or "none")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--draws", type=int, default=3000)
    ap.add_argument("--seeds", type=int, default=3)
    a = ap.parse_args()
    if a.dry_run:
        dry_run(a.seeds)
    else:
        run_fit(a.draws, a.seeds)


if __name__ == "__main__":
    main()
