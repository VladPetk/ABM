"""Realism battery (MHV realism-check spec, T-RB1) — measure-then-bless REPORT.

Runs the canonical shipped config (ANES_FULL_KWARGS) at N seeds and scores the
core realism checks agreed in docs/internal/realism_check_spec.md:

  Tier A (internal ANES fidelity)
    A1  per-party, per-axis centroid endpoints vs ANES VOTER centroids
    A2  §11 per-decade band scorecard (>=18/24)
    A3  per-decade 2D Wasserstein-2 vs the ANES pointcloud
    A4  out-party affect vs ANES thermometer bands (with S4-dilution caveat)
    A5  sorting-faster-than-constraint vs the held-out GSS instrument
    A6  per-ISSUE trajectory (racial VCF0830 + econ VCF0803) vs ANES item means
  Tier B (external structural / face validity)
    B1  party overlap collapse + sep growth shape (Pew / NHB)
    B2  cross-pressured / off-diagonal fraction + x~y slope (Treier-Hillygus)
  Tier C (face/sanity) — C1/C2/C3 are pinned as pytests; C3 also summarised here.

ALL party-conditional measurements use LIVE per-tick labels (agents realign).
This is a REPORT, not a CI gate (spec AGREE #4): it prints numbers + verdicts
and dumps JSON; honest tier labels and caveats live in the report it feeds.

Run:  .venv/Scripts/python.exe scripts/audit/realism_battery.py --seeds 9
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.anes_preset import ANES_FULL_KWARGS  # noqa: E402

# (label, tick, centre_year) — ANES bucket-centroid ticks (phase9 convention).
SNAPS = [(1980, 21, 1987), (1990, 42, 1994), (2000, 72, 2004),
         (2010, 102, 2014), (2020, 126, 2022), (2025, 135, 2025)]
W2_DECADES = [1980, 1990, 2000, 2010, 2020]   # EMPIRICAL_DECADES (W2 buckets)

DATA = os.path.join(ROOT, "data")
ITEM_IDX = {"VCF0803": 0, "VCF0809": 1, "VCF0839": 2, "VCF0838": 3,
            "VCF0852": 4, "VCF0853": 5, "VCF0830": 6}


def _load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _anes_centroid(series, party, year):
    ch = series["channels"]
    e = np.interp(year, *zip(*[(r[0], r[1]) for r in ch[f"p{party}_econ"]]))
    c = np.interp(year, *zip(*[(r[0], r[1]) for r in ch[f"p{party}_cult"]]))
    return float(e), float(c)


def _nearest_wave(item_means, year):
    yrs = sorted(int(y) for y in item_means["by_year"])
    return str(min(yrs, key=lambda y: abs(y - year)))


def run_seed(seed):
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from scripts.phase8f_lib import measure_all
    k = dict(ANES_FULL_KWARGS)
    eng = build_engine(seed=seed, **k)
    sched = build_schedule(
        factional_seeding=k.get("factional_seeding", False),
        faction_anchor_events=k.get("faction_anchor_events", True),
        evidence_regrade=k.get("evidence_regrade", False),
        exogenous_shocks=k.get("exogenous_shocks", False))
    traj, rich = {}, {}
    for label, tick, _yr in SNAPS:
        if tick > 0:
            run_to(eng, sched, tick)
        traj[label] = measure_all(eng)
        rich[label] = {
            "ide": np.array([a.state.ideology for a in eng.agents], float),
            "party": np.array([a.state.attrs["party"] for a in eng.agents], int),
            "issues": np.array([a.state.attrs["issues"] for a in eng.agents], float),
        }
    return traj, rich


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=9)
    ap.add_argument("--out", default=os.path.join(DATA, "..", "docs", "results",
                                                  "realism_measurement.json"))
    args = ap.parse_args()
    seeds = list(range(args.seeds))

    party_series = _load_json(os.path.join(DATA, "mhv", "party_centroid_series.json"))
    item_means = _load_json(os.path.join(
        DATA, "phase9_empirical", "derived", "anes_item_means_by_year.json"))
    gss = _load_json(os.path.join(DATA, "mhv", "gss_constraint_series.json"))

    print(f"running {len(seeds)} seeds on ANES_FULL_KWARGS ...", flush=True)
    trajs, richs = [], []
    for s in seeds:
        t, r = run_seed(s)
        trajs.append(t)
        richs.append(r)
        print(f"  seed {s} done", flush=True)

    R = {"seeds": seeds, "checks": {}}
    P = print

    # ---- A1: per-party, per-axis centroid endpoints vs ANES voter centroids ----
    P("\n===== A1  per-party centroid endpoints vs ANES voter centroids (+/-0.07) =====")
    a1 = {}
    for label, tick, cyr in [(1990, 42, 1994), (2025, 135, 2025)]:
        for pid, pname in ((0, "Dem"), (1, "Rep")):
            xs, ys = [], []
            for r in richs:
                d = r[label]
                m = d["party"] == pid
                xs.append(d["ide"][m, 0].mean()); ys.append(d["ide"][m, 1].mean())
            sx, sy = float(np.mean(xs)), float(np.mean(ys))
            ax, ay = _anes_centroid(party_series, pid, cyr)
            ok = abs(sx - ax) <= 0.07 and abs(sy - ay) <= 0.07
            a1[f"{label}_{pname}"] = {"sim": [sx, sy], "anes": [ax, ay],
                                      "d": [sx - ax, sy - ay], "in_band": ok}
            P(f"  {cyr} {pname}: sim ({sx:+.3f},{sy:+.3f})  ANES ({ax:+.3f},{ay:+.3f})"
              f"  d=({sx-ax:+.3f},{sy-ay:+.3f})  {'OK' if ok else 'MISS'}")
    R["checks"]["A1"] = a1

    # ---- A2: §11 band scorecard ----
    P("\n===== A2  §11 ANES band scorecard (>=18/24) =====")
    from scripts.phase8f_lib import aggregate, get_primary_targets, get_initial_targets_1980
    from scripts.phase9_anes_score import _score_cells
    means, ses = aggregate(trajs)
    pri = get_primary_targets(use_anes_bands=True)
    init = get_initial_targets_1980(use_anes_bands=True)
    cells_4x5, cells_init, n45, ninit, n24 = _score_cells(means, ses, pri, init)
    P(f"  {n24}/24 cells in band ({n45}/20 mainframe + {ninit}/4 IC)  "
      f"{'PASS' if n24 >= 18 else 'FAIL'} (>=18)")
    for c in cells_4x5 + cells_init:
        if not c["in_band"]:
            P(f"    OUT  {c['year']} {c['metric']:<16} v={c['value']:+.3f}"
              f"  band[{c['band_lo']:+.3f},{c['band_hi']:+.3f}]")
    R["checks"]["A2"] = {"n24": n24, "n_mainframe": n45, "n_ic": ninit,
                         "pass": n24 >= 18,
                         "cells": cells_4x5 + cells_init}

    # ---- A3: Wasserstein-2 ----
    P("\n===== A3  per-decade 2D Wasserstein-2 vs ANES pointcloud =====")
    try:
        from abm.calibration_phase9 import score_engine_run, pot_available
        from pathlib import Path
        if not pot_available():
            P("  POT unavailable — W2 skipped"); R["checks"]["A3"] = {"skipped": True}
        else:
            import pandas as pd
            dfs = []
            for s, r in zip(seeds, richs):
                snap = {dec: r[dec]["ide"] for dec in W2_DECADES}
                df = score_engine_run(positions_by_decade=snap,
                                      target_dir=Path(DATA) / "phase9_empirical",
                                      seed_for_subsample=s)
                dfs.append(df)
            comb = pd.concat(dfs, ignore_index=True)
            per_dec, w2_total = {}, 0.0
            for dec in W2_DECADES:
                wv = comb[comb["decade"] == dec]["wasserstein"]
                m = float(wv.mean()); per_dec[str(dec)] = m; w2_total += m
                P(f"  {dec}: W2 {m:.4f}")
            P(f"  w2_total = {w2_total:.4f}")
            R["checks"]["A3"] = {"w2_total": w2_total, "per_decade": per_dec}
    except Exception as e:
        P(f"  W2 error: {e}"); R["checks"]["A3"] = {"error": str(e)}

    # ---- A4: affect vs thermometer (surfaced from A2 affect cells) ----
    P("\n===== A4  out-party affect vs ANES thermometer (S4-dilution caveat) =====")
    a4 = {}
    for c in cells_4x5:
        if c["metric"] == "affect":
            a4[str(c["year"])] = {"value": c["value"], "band": [c["band_lo"], c["band_hi"]],
                                  "in_band": c["in_band"]}
            P(f"  {c['year']}: affect {c['value']:+.3f}  band[{c['band_lo']:+.3f},"
              f"{c['band_hi']:+.3f}]  {'OK' if c['in_band'] else 'MISS'}")
    R["checks"]["A4"] = a4

    # ---- A5: sorting (partisan-align) vs constraint (issue-corr) slopes vs GSS ----
    P("\n===== A5  sorting-vs-constraint slopes vs held-out GSS instrument =====")
    yrs = [1987, 1994, 2004, 2014, 2022]
    eng_partisan = [means[lab]["constraint"] for lab in (1980, 1990, 2000, 2010, 2020)]
    eng_issuecorr = []
    for lab in (1980, 1990, 2000, 2010, 2020):
        cs = [abs(np.corrcoef(r[lab]["ide"][:, 0], r[lab]["ide"][:, 1])[0, 1]) for r in richs]
        eng_issuecorr.append(float(np.mean(cs)))
    e_part_sl = float(np.polyfit(yrs, eng_partisan, 1)[0])
    e_iss_sl = float(np.polyfit(yrs, eng_issuecorr, 1)[0])
    g_part_sl = float(gss["slopes"]["bg_partisan_align"]["per_year"])
    g_iss_sl = float(gss["slopes"]["constraint_index"]["per_year"])
    def _ok(e, g):
        return (g is not None and np.sign(e) == np.sign(g) and abs(e - g) <= 0.5 * abs(g))
    P(f"  partisan-align slope/yr: engine {e_part_sl:+.5f}  GSS {g_part_sl}  "
      f"{'OK' if _ok(e_part_sl, g_part_sl) else 'CHECK'}")
    P(f"  issue-corr   slope/yr: engine {e_iss_sl:+.5f}  GSS {g_iss_sl}  "
      f"{'OK' if _ok(e_iss_sl, g_iss_sl) else 'CHECK'}")
    P(f"  sorting faster than constraint? engine {e_part_sl:+.5f} vs {e_iss_sl:+.5f}"
      f"  -> {'YES' if e_part_sl > e_iss_sl else 'NO'}")
    R["checks"]["A5"] = {"engine_partisan_slope": e_part_sl, "engine_issuecorr_slope": e_iss_sl,
                         "gss_partisan_slope": g_part_sl, "gss_issuecorr_slope": g_iss_sl}

    # ---- A6: per-issue trajectory (racial VCF0830 + econ VCF0803) vs ANES ----
    P("\n===== A6  per-issue trajectory vs ANES item means =====")
    a6 = {}
    for item in ("VCF0803", "VCF0830"):
        idx = ITEM_IDX[item]; a6[item] = {}
        P(f"  {item} ({item_means['_meta']['items'][item]['label']}) — sim vs ANES, Dem/Rep/gap:")
        for label, tick, cyr in SNAPS:
            wave = _nearest_wave(item_means, cyr)
            am = item_means["by_year"][wave]
            ad = am.get("dem", {}).get(item, {}).get("mean")
            ar = am.get("rep", {}).get(item, {}).get("mean")
            sd, sr = [], []
            for r in richs:
                d = r[label]
                sd.append(d["issues"][d["party"] == 0, idx].mean())
                sr.append(d["issues"][d["party"] == 1, idx].mean())
            sdm, srm = float(np.mean(sd)), float(np.mean(sr))
            sgap = srm - sdm
            agap = (ar - ad) if (ad is not None and ar is not None) else None
            a6[item][str(cyr)] = {"sim_dem": sdm, "sim_rep": srm, "sim_gap": sgap,
                                  "anes_dem": ad, "anes_rep": ar, "anes_gap": agap,
                                  "anes_wave": wave}
            agstr = f"{agap:+.3f}" if agap is not None else "  n/a"
            P(f"    {cyr}(ANES{wave}): sim D{sdm:+.3f} R{srm:+.3f} gap{sgap:+.3f}"
              f"  | ANES gap {agstr}")
    R["checks"]["A6"] = a6

    # ---- B1: overlap collapse on the inter-party axis ----
    P("\n===== B1  overlap collapse (% Rep more liberal than median Dem) =====")
    b1 = {}
    for label, tick, cyr in SNAPS:
        fracs, seps = [], []
        for r in richs:
            d = r[label]; ide = d["ide"]; pt = d["party"]
            D = ide[pt == 0]; Rp = ide[pt == 1]
            if len(D) < 2 or len(Rp) < 2:
                continue
            u = Rp.mean(0) - D.mean(0); u = u / (np.linalg.norm(u) + 1e-12)
            dproj = D @ u; rproj = Rp @ u
            fracs.append(float((rproj < np.median(dproj)).mean()))
            seps.append(float(np.linalg.norm(Rp.mean(0) - D.mean(0))))
        b1[str(cyr)] = {"frac_rep_below_med_dem": float(np.mean(fracs)),
                        "party_sep": float(np.mean(seps))}
        P(f"  {cyr}: {np.mean(fracs)*100:4.1f}% Rep more liberal than median Dem"
          f"   (sep {np.mean(seps):.3f})")
    R["checks"]["B1"] = b1

    # ---- B2: cross-pressured / off-diagonal + x~y slope ----
    P("\n===== B2  cross-pressured fraction + x~y slope (Treier-Hillygus) =====")
    b2 = {}
    for label, tick, cyr in [(2000, 72, 2004), (2025, 135, 2025)]:
        offs, corrs, slopes = [], [], []
        for r in richs:
            ide = r[label]["ide"]; x, y = ide[:, 0], ide[:, 1]
            offs.append(float(((np.sign(x) * np.sign(y)) < 0).mean()))
            corrs.append(float(np.corrcoef(x, y)[0, 1]))
            slopes.append(float(np.polyfit(y, x, 1)[0]))
        b2[str(cyr)] = {"off_diagonal_frac": float(np.mean(offs)),
                        "corr_xy": float(np.mean(corrs)),
                        "slope_x_on_y": float(np.mean(slopes))}
        P(f"  {cyr}: off-diagonal {np.mean(offs)*100:4.1f}%   corr(x,y) {np.mean(corrs):+.3f}"
          f"   slope x~y {np.mean(slopes):+.3f}")
    R["checks"]["B2"] = b2

    # ---- C3: corner occupancy at 2025 ----
    P("\n===== C3  corner/boundary occupancy at 2025 (<3% target, <5% hard) =====")
    cf = []
    for r in richs:
        ide = r[2025]["ide"]
        cf.append(float((np.abs(ide).max(1) > 0.9).mean()))
    cfm = float(np.mean(cf))
    P(f"  |coord|>0.9 fraction: {cfm*100:.2f}%  "
      f"{'OK' if cfm < 0.03 else 'SOFT-MISS' if cfm < 0.05 else 'FAIL'}")
    R["checks"]["C3"] = {"frac_gt_0_9": cfm}

    out = os.path.abspath(args.out)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(R, f, indent=2)
    P(f"\nwrote {out}")


if __name__ == "__main__":
    main()
