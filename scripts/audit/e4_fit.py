"""
E4 — joint ABC calibration of the endogenous emergence loop (emergence-recovery).

Fits the endogenous-arc knobs to the ANES per-decade SHAPE (the gradual climb +
the 2010s acceleration + the endpoint), on `endogenous_elite=True` with events:

  elite_gain      — elite leapfrog over the activist tail (lit: elite≈activist base)
  mob_base/peak   — activist-mobilization 1980 / 2020-25 levels
  mob_backload    — the convexity (flat-early/steep-late → the ANES back-loading)
  mob_asym        — R/D mobilization asymmetry (Hacker-Pierson)
  uptake          — mass cue-uptake rate (tier_c_party_pull_strength; the ~30yr sort)
  fj_alpha_scale  — FJ anchoring (rate-limiting / the gap)

ABC-rejection: sample the prior, simulate (multi-seed), score vs the ANES bands
(s4_targets), keep the best acceptance fraction, report the median posterior + the
single best point + its trajectory. Reuses the committed targets + the parallel
runner. SBC/ridge is NOT run here (ABC point + shrinkage only — a documented
simplification vs s4_fit's NPE machinery); the four-cut holdout is E4's validation.

Run (spawn-safe — file, never stdin):
  PYTHONPATH=. .venv/Scripts/python.exe scripts/audit/e4_fit.py --draws 1500 --seeds 3
  ... --dry        # 1 canonical sim + timing + target print
  ... --reuse      # reuse the persisted sim table (re-score without re-simulating)
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "docs" / "internal" / "audit" / "e4_fit.json"
OUT_MD = ROOT / "docs" / "internal" / "audit" / "e4_fit.md"
TABLE_NPZ = ROOT / "docs" / "internal" / "audit" / "e4_fit_table.npz"

# (name, [build_engine kwargs], prior_lo, prior_hi, E3-default)
FIT_PARAMS = [
    ("elite_gain",     ["elite_gain"],                    0.8,  3.0,  2.5),
    ("mob_base",       ["mob_base"],                      0.05, 0.50, 0.20),
    ("mob_peak",       ["mob_peak"],                      0.70, 3.00, 1.20),
    ("mob_backload",   ["mob_backload"],                  0.0,  2.5,  0.60),
    ("mob_asym",       ["mob_asym"],                      0.0,  0.35, 0.18),
    ("uptake",         ["tier_c_party_pull_strength"],    0.04, 0.30, 0.297),
    ("fj_alpha_scale", ["fj_alpha_scale"],                1.0,  3.5,  2.195),
]
PNAMES = [p[0] for p in FIT_PARAMS]
NPAR = len(FIT_PARAMS)
PRIOR_LO = np.array([p[2] for p in FIT_PARAMS])
PRIOR_HI = np.array([p[3] for p in FIT_PARAMS])
E3DEF = np.array([p[4] for p in FIT_PARAMS])

ALL_DECADES = [1980, 1990, 2000, 2010, 2020, 2025]
# observable -> weight in the fit distance (party_sep is the emergence target)
OBS_W = {"party_sep": 1.0, "affect": 0.4, "within_party_sd": 0.4}


def _overrides(theta):
    from scripts.anes_preset import ANES_FULL_KWARGS
    ov = dict(ANES_FULL_KWARGS)
    ov["endogenous_elite"] = True
    ov["data_fed_elite"] = False
    for (name, kws, *_), val in zip(FIT_PARAMS, theta):
        for kw in kws:
            ov[kw] = float(val)
    return ov


def simulate(theta, seed):
    """Run the endogenous arc with events; return {decade: {obs: value}}."""
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
                     ("party_sep", "affect", "within_party_sd", "constraint")}
    return out


def fit_worker(job):
    idx, theta_tuple, seed = job
    return (idx, seed, simulate(np.array(theta_tuple, float), seed))


def _targets():
    """ANES per-decade band mid-points + half-widths from s4_targets."""
    from scripts.audit.s4_targets import build_targets
    t = build_targets()
    mid, half = {}, {}
    for d in ALL_DECADES:
        cells = t["decades"][d]["cells"]
        for o in OBS_W:
            band = cells[o]["band"]
            if band:
                mid[(d, o)] = 0.5 * (band[0] + band[1])
                half[(d, o)] = max(0.5 * (band[1] - band[0]), 1e-3)
    return mid, half


def distance(per_decade, mid, half):
    """Weighted normalized RMS distance to the ANES bands (all decades)."""
    s, w = 0.0, 0.0
    for (d, o), m in mid.items():
        z = (per_decade[d][o] - m) / half[(d, o)]
        s += OBS_W[o] * z * z
        w += OBS_W[o]
    return float(np.sqrt(s / w))


def _sample_prior(n, rng):
    return PRIOR_LO + rng.random((n, NPAR)) * (PRIOR_HI - PRIOR_LO)


def dry_run():
    mid, half = _targets()
    print("ANES targets (mid ± half):")
    for d in ALL_DECADES:
        row = "  ".join(f"{o}={mid[(d,o)]:.2f}±{half[(d,o)]:.2f}"
                        for o in OBS_W if (d, o) in mid)
        print(f"  {d}: {row}")
    t0 = time.time()
    per = simulate(E3DEF, 0)
    dt = time.time() - t0
    print(f"\nE3-default sim wall-time: {dt:.1f}s")
    print(f"  {'dec':>5} {'sep':>7} {'affect':>8} {'wp_sd':>7}")
    for d in ALL_DECADES:
        p = per[d]
        print(f"  {d:>5} {p['party_sep']:>7.3f} {p['affect']:>8.3f} {p['within_party_sd']:>7.3f}")
    print(f"  distance(E3-default) = {distance(per, mid, half):.3f}")


def run_fit(draws, seeds, accept_frac=0.03, reuse=False):
    from abm.calibration_parallel import run_seeds_parallel
    mid, half = _targets()
    seeds = list(range(seeds))

    if reuse and TABLE_NPZ.exists():
        z = np.load(TABLE_NPZ, allow_pickle=True)
        TH = z["theta"]
        dists = z["dists"]
        print(f"[reuse] loaded table: {TH.shape[0]} draws")
    else:
        rng = np.random.default_rng(0)
        TH = _sample_prior(draws, rng)
        jobs = [(i, tuple(TH[i]), s) for i in range(draws) for s in seeds]
        print(f"running {len(jobs)} sims ({draws} draws x {len(seeds)} seeds)...")
        t0 = time.time()
        results = run_seeds_parallel(fit_worker, jobs)
        print(f"  sims done in {(time.time()-t0)/60:.1f} min")
        # aggregate: per draw, average per-decade obs across seeds, then distance
        by_draw = {}
        for idx, seed, per in results:
            by_draw.setdefault(idx, []).append(per)
        dists = np.full(draws, np.inf)
        for idx, pers in by_draw.items():
            avg = {d: {o: float(np.mean([p[d][o] for p in pers])) for o in OBS_W}
                   for d in ALL_DECADES}
            dists[idx] = distance(avg, mid, half)
        TABLE_NPZ.parent.mkdir(parents=True, exist_ok=True)
        np.savez(TABLE_NPZ, theta=TH, dists=dists)

    order = np.argsort(dists)
    k = max(5, int(accept_frac * len(dists)))
    acc = order[:k]
    post = TH[acc]
    abc_point = {n: float(v) for n, v in zip(PNAMES, np.median(post, 0))}
    best_i = int(order[0])
    best_point = {n: float(v) for n, v in zip(PNAMES, TH[best_i])}
    prior_sd = (PRIOR_HI - PRIOR_LO) / np.sqrt(12)
    shrink = {n: float(1 - s / sd) for n, s, sd in
              zip(PNAMES, post.std(0), prior_sd)}

    # best-point trajectory (re-sim the single best at all seeds, averaged)
    best_per = [simulate(TH[best_i], s) for s in seeds]
    best_traj = {d: {o: float(np.mean([p[d][o] for p in best_per])) for o in OBS_W}
                 for d in ALL_DECADES}

    out = {
        "_meta": "MHV emergence-recovery E4 — endogenous-loop ABC fit to ANES shape",
        "draws": int(len(dists)), "seeds": len(seeds), "accept_frac": accept_frac,
        "abc_point": abc_point, "best_point": best_point,
        "best_distance": float(dists[best_i]),
        "abc_distance_median": float(np.median(dists[acc])),
        "shrinkage": shrink,
        "best_trajectory": best_traj,
        "anes_targets": {f"{d}.{o}": mid[(d, o)] for (d, o) in mid},
    }
    OUT_JSON.write_text(json.dumps(out, indent=2))
    _write_md(out, mid, half)
    print(f"\nbest distance {dists[best_i]:.3f}; ABC-median distance {np.median(dists[acc]):.3f}")
    print(f"{'knob':>16} {'ABC':>9} {'best':>9} {'E3def':>9}  shrink")
    for n, dflt in zip(PNAMES, E3DEF):
        print(f"{n:>16} {abc_point[n]:>9.4f} {best_point[n]:>9.4f} {dflt:>9.4f}  {shrink[n]:+.2f}")
    print(f"\nbest trajectory vs ANES (sep):")
    print("  dec   sep   ANES")
    for d in ALL_DECADES:
        print(f"  {d}  {best_traj[d]['party_sep']:.2f}  {mid[(d,'party_sep')]:.2f}")
    print(f"\nwrote {OUT_JSON}")
    return out


def _write_md(out, mid, half):
    L = ["# E4 — endogenous-loop ABC fit to the ANES shape\n",
         f"{out['draws']} draws × {out['seeds']} seeds, accept_frac {out['accept_frac']}. "
         f"best distance **{out['best_distance']:.3f}**, ABC-median {out['abc_distance_median']:.3f}.\n",
         "ABC-rejection only (no NPE/SBC — documented simplification vs s4_fit); the "
         "four-cut holdout is the validation.\n",
         "| knob | ABC median | best | E3-default | shrink |",
         "|---|---|---|---|---|"]
    for n, dflt in zip(PNAMES, E3DEF):
        L.append(f"| {n} | {out['abc_point'][n]:.4f} | {out['best_point'][n]:.4f} | "
                 f"{dflt:.4f} | {out['shrinkage'][n]:+.2f} |")
    L += ["\n**Best-point trajectory vs ANES (mid-band):**\n",
          "| decade | sep (sim) | sep (ANES) | affect (sim) | affect (ANES) | wp_sd (sim) | wp_sd (ANES) |",
          "|---|---|---|---|---|---|---|"]
    bt = out["best_trajectory"]
    for d in ALL_DECADES:
        L.append(f"| {d} | {bt[d]['party_sep']:.2f} | {mid[(d,'party_sep')]:.2f} | "
                 f"{bt[d]['affect']:.2f} | {mid[(d,'affect')]:.2f} | "
                 f"{bt[d]['within_party_sd']:.2f} | {mid[(d,'within_party_sd')]:.2f} |")
    OUT_MD.write_text("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=1500)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--accept-frac", type=float, default=0.03)
    ap.add_argument("--reuse", action="store_true")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    if a.dry:
        dry_run()
    else:
        run_fit(a.draws, a.seeds, accept_frac=a.accept_frac, reuse=a.reuse)


if __name__ == "__main__":
    main()
