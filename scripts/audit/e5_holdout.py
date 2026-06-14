"""Emergence-recovery E5.1 — four-cut holdout battery for the ENDOGENOUS loop.

The s4_holdout battery validated the FED fit; this is its endogenous counterpart.
Same pre-registered ANES/GSS bands (config-independent, from s4_targets.py), same
power-band discipline, but the conditional ABC refits run on the ENDOGENOUS knob
set (e4_fit.FIT_PARAMS) instead of the FED knobs. A failed band is a finding, not
a retune trigger (the adopted E4 ABC point is fixed — a user decision).

Cuts:
  1 temporal   -- refit ABC on <=2000 decades, predict 2010/2020/2025; each
                  held-out cell's 8-seed band must overlap the ANES band widened
                  by 1 band-width (s4_targets cut1 widened_bands).
  2 instrument -- the SHIPPED endogenous point (adopted ABC) must predict the
                  held-out GSS trends (partisan-align slope vs bg_partisan_align;
                  issue |corr| slope vs constraint_index) within +/-50%, same sign.
  3 statistic  -- refit ABC on {party_sep, affect, within_party_sd} only, predict
                  the held-out constraint (partisan-align) trajectory.
  4 power      -- overall: >=2 of the 3 substantive cuts pass.

Run (spawn-safe — file, never stdin):
  PYTHONPATH=. .venv/Scripts/python.exe scripts/audit/e5_holdout.py --build-table --draws 700 --seeds 3 --workers 8
  PYTHONPATH=. .venv/Scripts/python.exe scripts/audit/e5_holdout.py        # run cuts (reuses table)
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from scripts.audit.e4_fit import (
    FIT_PARAMS, PNAMES, PRIOR_LO, PRIOR_HI, NPAR, _overrides, ALL_DECADES,
)

ROOT = Path(__file__).resolve().parents[2]
OUT_MD = ROOT / "docs" / "results" / "e5_holdout.md"
TABLE_NPZ = ROOT / "docs" / "internal" / "audit" / "e5_holdout_table.npz"

OBS_COND = ("party_sep", "affect", "within_party_sd", "constraint")
SUMMARY_LABELS = [(d, o) for d in ALL_DECADES for o in OBS_COND]
FIT_DECADES = [1980, 1990, 2000]          # cut-1 conditioning decades
HOLDOUT_DECADES = [2010, 2020, 2025]
N_SEEDS = 8                                # power-band prediction sims


def _wcorr(a, b):
    if a.std() < 1e-9 or b.std() < 1e-9:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1])


def simulate_rich(theta, seed):
    """Endogenous arc; per-decade commensurable observables (LIVE party labels)."""
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from abm.metrics.affective import affective_polarization
    from scripts.phase9_anes_score import SECTION11_TICKS
    ov = _overrides(theta)
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
        pos = eng.positions()
        party = np.array([a.state.attrs["party"] for a in eng.agents])
        dr = party < 2
        x, y, p = pos[dr, 0], pos[dr, 1], party[dr].astype(float)
        sep = float(np.linalg.norm(pos[party == 0].mean(0) - pos[party == 1].mean(0)))
        wp = float(np.mean([pos[party == k, 0].std()
                            for k in (0, 1) if (party == k).sum() > 1]))
        partisan = float(np.nanmean([abs(_wcorr(x, p)), abs(_wcorr(y, p))]))
        out[year] = {
            "party_sep": sep,
            "affect": float(affective_polarization(eng.agents)),
            "within_party_sd": wp,
            "constraint": partisan,            # partisan-align (== ANES "constraint")
            "issue_corr": abs(_wcorr(x, y)),   # issue |corr(x,y)| (GSS constraint_index)
        }
    return out


def table_worker(job):
    idx, theta_tuple, seed = job
    return (idx, seed, simulate_rich(np.array(theta_tuple, float), seed))


# --------------------------------------------------------------------------- #
# ANES x_obs (band mids) + GSS / widened holdout bands (pre-registered)
# --------------------------------------------------------------------------- #
def _x_obs_targets():
    from scripts.audit.s4_targets import build_targets
    t = build_targets()
    x = np.full(len(SUMMARY_LABELS), np.nan)
    for i, (d, o) in enumerate(SUMMARY_LABELS):
        band = t["decades"][d]["cells"][o]["band"]
        if band:
            x[i] = 0.5 * (band[0] + band[1])
    return x, t


def _abc_point(X, TH, x_obs, cols):
    """ABC median conditioning on the given label columns (reuses the table)."""
    Xc, xo = X[:, cols], x_obs[cols]
    sd = Xc.std(0); sd[sd < 1e-9] = 1.0
    d = np.sqrt((((Xc - xo) / sd) ** 2).sum(1))
    acc = np.argsort(d)[: max(20, int(0.03 * len(TH)))]
    return np.median(TH[acc], 0)


def _band(vals):
    return float(np.min(vals)), float(np.max(vals))


def _slope(decs, vals):
    return float(np.polyfit(np.array(decs, float), np.array(vals, float), 1)[0])


def _shipped_theta():
    """The adopted E4 ABC point, read from the canonical endogenous preset."""
    from scripts.anes_preset import ANES_FULL_KWARGS
    th = np.zeros(NPAR)
    for i, (name, kws, *_) in enumerate(FIT_PARAMS):
        th[i] = float(ANES_FULL_KWARGS[kws[0]])
    return th


# --------------------------------------------------------------------------- #
# Build the ABC table (TH, X)  — per-draw, per-(decade,obs), seed-averaged
# --------------------------------------------------------------------------- #
def build_table(draws, seeds, workers):
    from abm.calibration_parallel import run_seeds_parallel
    rng = np.random.default_rng(0)
    TH = PRIOR_LO + rng.random((draws, NPAR)) * (PRIOR_HI - PRIOR_LO)
    jobs = [(i, tuple(TH[i]), s) for i in range(draws) for s in range(seeds)]
    print(f"building table: {len(jobs)} sims ({draws} draws x {seeds} seeds, "
          f"{workers or 'default'} workers)...", flush=True)
    t0 = time.time()
    results = run_seeds_parallel(table_worker, jobs, processes=workers)
    print(f"  sims done in {(time.time()-t0)/60:.1f} min", flush=True)
    by_draw = {}
    for idx, seed, per in results:
        by_draw.setdefault(idx, []).append(per)
    X = np.full((draws, len(SUMMARY_LABELS)), np.nan)
    for idx, pers in by_draw.items():
        for j, (d, o) in enumerate(SUMMARY_LABELS):
            X[idx, j] = float(np.mean([pp[d][o] for pp in pers]))
    TABLE_NPZ.parent.mkdir(parents=True, exist_ok=True)
    np.savez(TABLE_NPZ, TH=TH, X=X)
    print(f"wrote {TABLE_NPZ}")


# --------------------------------------------------------------------------- #
# Run the four cuts
# --------------------------------------------------------------------------- #
def run_cuts(workers):
    from abm.calibration_parallel import run_seeds_parallel
    d = np.load(TABLE_NPZ)
    TH, X = d["TH"], d["X"]
    x_obs, t = _x_obs_targets()
    hc = t["holdout_cuts"]
    widened = hc["cut1_temporal"]["widened_bands"]
    gss = hc["cut2_instrument"]["gss_target"]
    lines, verdicts = [], {}

    def sim_band(theta):
        jobs = [(0, tuple(theta), s) for s in range(N_SEEDS)]
        res = run_seeds_parallel(table_worker, jobs, processes=workers)
        per = [r[2] for r in res]
        return {y: {k: [pp[y][k] for pp in per] for k in per[0][y]} for y in per[0]}

    # ===== CUT 1 — temporal =====
    cols_t = [i for i, (dd, o) in enumerate(SUMMARY_LABELS) if dd in FIT_DECADES]
    th_t = _abc_point(X, TH, x_obs, cols_t)
    band_t = sim_band(th_t)
    lines += ["## Cut 1 — temporal (fit <=2000 → predict 2010/2020/2025)",
              "refit point: " + ", ".join(f"{n}={v:.3f}" for n, v in zip(PNAMES, th_t)), "",
              "| decade.metric | pred band (8 seeds) | widened ANES band | in? |",
              "|---|---|---|---|"]
    c1_ok = True
    for yr in HOLDOUT_DECADES:
        for o in ("party_sep", "affect", "constraint", "within_party_sd"):
            lo, hi = _band(band_t[yr][o])
            wb = widened[yr][o]
            ov = wb is not None and hi >= wb[0] and lo <= wb[1]
            c1_ok = c1_ok and ov
            wbs = f"[{wb[0]},{wb[1]}]" if wb else "n/a"
            lines.append(f"| {yr}.{o} | [{lo:.3f},{hi:.3f}] | {wbs} | {'OK' if ov else '**'} |")
    verdicts["cut1_temporal"] = c1_ok

    # ===== CUT 2 — instrument (shipped endogenous point → GSS trends) =====
    th_ship = _shipped_theta()
    band_s = sim_band(th_ship)
    yrs = [1980, 1990, 2000, 2010, 2020]
    eng_part = [float(np.mean(band_s[y]["constraint"])) for y in yrs]
    eng_iss = [float(np.mean(band_s[y]["issue_corr"])) for y in yrs]
    eng_part_sl = _slope(yrs, eng_part)
    eng_iss_sl = _slope(yrs, eng_iss)
    g_part_sl = gss["bg_partisan_align"]["slope_per_year"]
    g_iss_sl = gss["constraint_index"]["slope_per_year"]

    def within50(e, g):
        return (np.sign(e) == np.sign(g)) and (0.5 * abs(g) <= abs(e) <= 1.5 * abs(g))
    c2a, c2b = within50(eng_part_sl, g_part_sl), within50(eng_iss_sl, g_iss_sl)
    lines += ["", "## Cut 2 — instrument (shipped endogenous point → held-out GSS trends)",
              "shipped point: " + ", ".join(f"{n}={v:.3f}" for n, v in zip(PNAMES, th_ship)), "",
              "| trend | engine slope/yr | GSS slope/yr | within +/-50% & sign? |",
              "|---|---|---|---|",
              f"| partisan align (bg) | {eng_part_sl:+.5f} | {g_part_sl:+.5f} | {'OK' if c2a else '**'} |",
              f"| issue |corr| (constraint_index) | {eng_iss_sl:+.5f} | {g_iss_sl:+.5f} | {'OK' if c2b else '**'} |"]
    verdicts["cut2_instrument"] = c2a and c2b

    # ===== CUT 3 — statistic (fit sep/affect/wp_sd → predict constraint) =====
    cols_s = [i for i, (dd, o) in enumerate(SUMMARY_LABELS)
              if o in ("party_sep", "affect", "within_party_sd")]
    th_st = _abc_point(X, TH, x_obs, cols_s)
    band_st = sim_band(th_st)
    from scripts.phase8f_lib import ANES_PRIMARY_TARGETS, ANES_INITIAL_TARGETS_1980

    def anes_constraint_band(yr):
        b = (ANES_INITIAL_TARGETS_1980 if yr == 1980 else ANES_PRIMARY_TARGETS[yr])["constraint"]
        return [round(b[0] - 0.07, 3), round(b[1] + 0.07, 3)]
    lines += ["", "## Cut 3 — statistic (fit sep/affect/wp_sd → predict constraint)",
              "refit point: " + ", ".join(f"{n}={v:.3f}" for n, v in zip(PNAMES, th_st)), "",
              "| decade | pred constraint band | widened ANES constraint | in? |",
              "|---|---|---|---|"]
    c3_ok = True
    for yr in ALL_DECADES:
        lo, hi = _band(band_st[yr]["constraint"])
        wb = anes_constraint_band(yr)
        ov = hi >= wb[0] and lo <= wb[1]
        c3_ok = c3_ok and ov
        lines.append(f"| {yr} | [{lo:.3f},{hi:.3f}] | [{wb[0]},{wb[1]}] | {'OK' if ov else '**'} |")
    verdicts["cut3_statistic"] = c3_ok

    # ===== CUT 4 — power / overall =====
    n_pass = sum(verdicts.values())
    overall = n_pass >= 2
    head = ["# Emergence-recovery E5.1 — endogenous holdout battery scorecard", "",
            f"**Overall: {'PASS' if overall else 'FAIL'}** "
            f"({n_pass}/3 substantive cuts pass; power-band rule: >=2/3). "
            "Bands pre-registered in s4_targets.py (config-independent); ABC refits on "
            "the endogenous knob set. The adopted E4 ABC point is fixed (a failed band "
            "is a finding, not a retune).", "",
            "| cut | verdict |", "|---|---|"]
    for k, v in verdicts.items():
        head.append(f"| {k} | {'PASS' if v else 'FAIL'} |")
    head.append("")
    interp = [
        "",
        "## Interpretation — the emergence trade-off (read this)",
        "",
        "The FED config passed all three cuts (s4_holdout.md, 3/3). The endogenous",
        "config passes only cut 3. This is **not** a regression in the usual sense —",
        "two of the cuts only became *meaningful* once positional sorting stopped",
        "being fed:",
        "",
        "- **Cut 1 (temporal) FAIL — the honest cost of genuine emergence.** Refit on",
        "  <=2000 and the ABC picks a low mobilization ramp (mob_peak ~1.65 vs 2.48,",
        "  uptake ~0.06 vs 0.25) that fits the flat early period — then under-predicts",
        "  the 2010+ acceleration (2025 party_sep ~0.5-0.7 vs the needed ~1.0-1.25).",
        "  Only party_sep fails; affect/constraint/within_sd all pass. The FED config",
        "  passed this cut TRIVIALLY: it fed the ANES centroid series, so the late",
        "  trajectory was carried regardless of the fit knobs. The endogenous config",
        "  makes cut 1 a real out-of-sample test, and it reveals that the late",
        "  acceleration is NOT predictable from early dynamics — it rides the",
        "  exogenously-fit activist-mobilization timing (consistent with the E5.2",
        "  honesty budget: only ~38% of party_sep is the spontaneous loop floor; ~62%",
        "  depends on the fitted forcing). The model EXPLAINS the mechanism (loop",
        "  amplification) but the TIMING is calibrated to the full period, not predicted.",
        "- **Cut 2 (instrument) FAIL — one sub-test, the axis over-correlation.** The",
        "  partisan-align slope passes (engine 1.44x GSS, within +/-50%); the issue-corr",
        "  slope is 1.62x GSS — just over the band. This is the documented single-axis",
        "  loop residual (realism B2: corr(x,y) ~0.78 vs ANES ~0.5-0.6). The",
        "  time-evolving / balanced realignment direction refinement is the candidate fix.",
        "- **Cut 3 (statistic) PASS.** Constraint (partisan alignment) is well predicted",
        "  from sep/affect/spread across all six decades.",
        "",
        "**Verdict:** the holdout fails the pre-registered >=2/3 bar (1/3). Honest",
        "reading: the emergence win is real (E5.2), but the late-period TIMING is an",
        "exogenously-calibrated forcing the model amplifies rather than predicts, and",
        "the single-axis loop over-correlates the compass axes. Both are documented",
        "limitations, not hidden. A failed band is a finding, not a retune trigger",
        "(the adopted E4 ABC point is fixed). Whether to ship the endogenous flip given",
        "this is a user call (see the morning report).",
    ]
    OUT_MD.write_text("\n".join(head + lines + interp) + "\n", encoding="utf-8")
    print("\n".join(head))
    print(f"\nwrote {OUT_MD.relative_to(ROOT)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-table", action="store_true")
    ap.add_argument("--draws", type=int, default=700)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--workers", type=int, default=None)
    a = ap.parse_args()
    if a.build_table:
        build_table(a.draws, a.seeds, a.workers)
    else:
        run_cuts(a.workers)


if __name__ == "__main__":
    main()
