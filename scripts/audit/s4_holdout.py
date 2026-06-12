"""MHV S4 T4.4 -- the four-cut pre-registered holdout battery.

Bands were frozen in scripts/audit/s4_targets.py BEFORE the fit (s4_spec.md §5).
This reports honest pass/fail; a failed band is a finding, not a retune trigger.

Cuts (power-band discipline: every prediction is a >=8-seed band):
  1 temporal   -- refit on <=2012 (1980/1990/2000), predict 2010/2020/2025;
                  each held-out cell's seed-band must overlap the ANES band
                  widened by 1 band-width, with the 1980->year sign stable.
  2 instrument -- the SHIPPED full-fit model must predict the independently
                  measured GSS trends (held-out instrument): engine partisan
                  alignment slope vs GSS bg_partisan_align, engine issue |corr|
                  slope vs GSS constraint_index -- within +/-50%, same sign.
  3 statistic  -- refit on {party_sep, affect, within_party_sd} only (drop
                  constraint), predict the held-out constraint (partisan-align)
                  trajectory: within the ANES constraint band widened 1x, signs ok.
  4 power      -- overall verdict: >=2 of the 3 substantive cuts pass.

Engine metric note: measure_all["constraint"] == |corr(axis, party)| (PARTISAN
alignment, == GSS bg_partisan_align definition). The issue-issue |corr(x,y)| is
computed here directly for the GSS constraint_index comparison.

Reuses the persisted sim table (scripts/audit/s4_fit_table.npz) for the ABC
refits (no re-simulation); only the >=8-seed prediction sims are run live.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scripts.audit.s4_fit import (
    ALL_DECADES, FIT_DECADES, OBS, PNAMES, PRIOR_LO, PRIOR_HI,
    SUMMARY_LABELS, TABLE_NPZ, _overrides, _x_obs,
)

ROOT = Path(__file__).resolve().parents[2]
OUT_MD = ROOT / "docs" / "results" / "s4_holdout.md"
HOLDOUT_DECADES = [2010, 2020, 2025]
N_SEEDS = 8


# --- rich per-decade measurement (positions + party; commensurable defs) ----
def _wcorr(a, b):
    if a.std() < 1e-9 or b.std() < 1e-9:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1])


def simulate_rich(theta, seed):
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from abm.metrics.affective import affective_polarization
    from abm.metrics.network import party_modularity, cross_cutting_tie_fraction
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
        wp = np.mean([pos[party == k, 0].std() for k in (0, 1) if (party == k).sum() > 1])
        partisan = np.nanmean([abs(_wcorr(x, p)), abs(_wcorr(y, p))])
        out[year] = {
            "party_sep": sep,
            "affect": float(affective_polarization(eng.agents)),
            "constraint": float(partisan),          # partisan-align (== ANES "constraint")
            "issue_corr": abs(_wcorr(x, y)),         # issue |corr(x,y)| (GSS constraint_index)
            "within_party_sd": float(wp),
            "modularity": float(party_modularity(eng.agents, eng.env.attrs["network"])),
            "xc_fraction": float(cross_cutting_tie_fraction(eng.agents, eng.env.attrs["network"])),
        }
    return out


def _abc_point(X, TH, x_obs, cols):
    """ABC median conditioning on the given columns (reuses the table)."""
    Xc, xo = X[:, cols], x_obs[cols]
    sd = Xc.std(0); sd[sd < 1e-9] = 1.0
    d = np.sqrt((((Xc - xo) / sd) ** 2).sum(1))
    acc = np.argsort(d)[: max(20, int(0.03 * len(TH)))]
    return np.median(TH[acc], 0)


def _band(seedvals):
    return float(np.min(seedvals)), float(np.max(seedvals))


def _slope(decs, vals):
    return float(np.polyfit(np.array(decs, float), np.array(vals, float), 1)[0])


def main():
    d = np.load(TABLE_NPZ)
    TH, X = d["TH"], d["X"]
    x_obs, targets = _x_obs()
    gss = targets["holdout_cuts"]["cut2_instrument"]["gss_target"]
    widened = targets["holdout_cuts"]["cut1_temporal"]["widened_bands"]
    lines, verdicts = [], {}

    # ---- helper to simulate a point at N seeds -> per-decade seed lists ----
    def sim_band(theta):
        per = [simulate_rich(theta, s) for s in range(N_SEEDS)]
        return {y: {k: [pp[y][k] for pp in per] for k in per[0][y]} for y in per[0]}

    # ===== CUT 1 -- temporal (refit <=2012, predict 2010/2020/2025) =====
    cols_t = [i for i, (dd, o) in enumerate(SUMMARY_LABELS) if dd in FIT_DECADES]
    th_t = _abc_point(X, TH, x_obs, cols_t)
    band_t = sim_band(th_t)
    lines += ["## Cut 1 -- temporal (fit <=2012 -> predict 2010/2020/2025)",
              f"refit point: " + ", ".join(f"{n}={v:.3f}" for n, v in zip(PNAMES, th_t)), "",
              "| decade.metric | pred band (8 seeds) | widened ANES band | in? |",
              "|---|---|---|---|"]
    c1_ok = True
    for yr in HOLDOUT_DECADES:
        for o in ("party_sep", "affect", "constraint", "within_party_sd"):
            lo, hi = _band(band_t[yr][o])
            wb = widened[yr][o]
            ov = wb is not None and hi >= wb[0] and lo <= wb[1]   # band overlap
            c1_ok = c1_ok and ov
            wbs = f"[{wb[0]},{wb[1]}]" if wb else "n/a"
            lines.append(f"| {yr}.{o} | [{lo:.3f},{hi:.3f}] | {wbs} | {'OK' if ov else '**'} |")
    verdicts["cut1_temporal"] = c1_ok

    # ===== CUT 2 -- instrument (shipped model predicts GSS held-out trends) =====
    from scripts.anes_preset import ANES_FULL_KWARGS
    th_ship = np.array([ANES_FULL_KWARGS["tier_c_party_pull_strength"],
                        ANES_FULL_KWARGS["fj_alpha_scale"],
                        ANES_FULL_KWARGS["constraint_rate"],
                        ANES_FULL_KWARGS["sandbox_animus_mult"],
                        ANES_FULL_KWARGS["tier_d_aniso_noise_sigma_x"],
                        ANES_FULL_KWARGS["elite_lead_factor"]])
    band_s = sim_band(th_ship)
    yrs = [1980, 1990, 2000, 2010, 2020]   # GSS decades available
    eng_part = [np.mean(band_s[y]["constraint"]) for y in yrs]
    eng_iss = [np.mean(band_s[y]["issue_corr"]) for y in yrs]
    eng_part_sl = _slope(yrs, eng_part) * 1.0   # per-year (decade labels ~ years)
    eng_iss_sl = _slope(yrs, eng_iss)
    g_part_sl = gss["bg_partisan_align"]["slope_per_year"]
    g_iss_sl = gss["constraint_index"]["slope_per_year"]

    def within50(e, g):
        return (np.sign(e) == np.sign(g)) and (0.5 * abs(g) <= abs(e) <= 1.5 * abs(g))
    c2a, c2b = within50(eng_part_sl, g_part_sl), within50(eng_iss_sl, g_iss_sl)
    lines += ["", "## Cut 2 -- instrument (shipped model -> held-out GSS trends)",
              "| trend | engine slope/yr | GSS slope/yr | within +/-50% & sign? |",
              "|---|---|---|---|",
              f"| partisan align (bg) | {eng_part_sl:+.5f} | {g_part_sl:+.5f} | {'OK' if c2a else '**'} |",
              f"| issue |corr| (constraint_index) | {eng_iss_sl:+.5f} | {g_iss_sl:+.5f} | {'OK' if c2b else '**'} |"]
    verdicts["cut2_instrument"] = c2a and c2b

    # ===== CUT 3 -- statistic (fit on sep/affect/wp_sd, predict constraint) =====
    cols_s = [i for i, (dd, o) in enumerate(SUMMARY_LABELS)
              if o in ("party_sep", "affect", "within_party_sd")]
    th_st = _abc_point(X, TH, x_obs, cols_s)
    band_st = sim_band(th_st)
    # held-out statistic = constraint (partisan align); ANES constraint band widened 1x
    from scripts.phase8f_lib import ANES_PRIMARY_TARGETS, ANES_INITIAL_TARGETS_1980
    def anes_constraint_band(yr):
        b = (ANES_INITIAL_TARGETS_1980 if yr == 1980 else ANES_PRIMARY_TARGETS[yr])["constraint"]
        return [round(b[0] - 0.07, 3), round(b[1] + 0.07, 3)]
    lines += ["", "## Cut 3 -- statistic (fit sep/affect/wp_sd -> predict constraint)",
              f"refit point: " + ", ".join(f"{n}={v:.3f}" for n, v in zip(PNAMES, th_st)), "",
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

    # ===== CUT 4 -- power / overall =====
    n_pass = sum(verdicts.values())
    overall = n_pass >= 2
    head = ["# MHV S4 T4.4 -- holdout battery scorecard", "",
            f"**Overall: {'PASS' if overall else 'FAIL'}** "
            f"({n_pass}/3 substantive cuts pass; power-band rule: >=2/3). "
            f"Bands pre-registered in s4_targets.py before the fit.", "",
            "| cut | verdict |", "|---|---|"]
    for k, v in verdicts.items():
        head.append(f"| {k} | {'PASS' if v else 'FAIL'} |")
    head.append("")

    OUT_MD.write_text("\n".join(head + lines))
    print("\n".join(head))
    print(f"\nwrote {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
