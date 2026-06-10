"""MHV T0.6 — de-saturate the operating point (staged sweep instrument).

The shipped anes_full config sits on three saturations (mhv_spec T0.6;
engine_knob_audit Phases 1-2; phase5 v2):

  1. elite corner-pin: drift_mult=3.0 drives both elite centroids into
     opposite compass corners by ~2010 (elite_sep = 2*sqrt(2) exactly);
     sim elite growth 2.30x vs DW-NOMINATE 1.51x (dwnom_shape_resid 2.75).
  2. affect floor: cooling compresses against warmth = -1 (audit Phase 1);
     the affect-bands investigation independently found over-produced animus.
  3. BC near-silent: per-agent eps ~ 0.30-scaled vs within-party neighbour
     distances ~0.4 at the sorted state, strength 0.015 (default 0.08).

Stages (run incrementally; results accumulate in t06_desaturate.json):
  A  diagnose the shipped point (8 seeds): corner-pin onset, floor
     fractions, BC effective gain, section-11 cells
  B  drift_mult sweep        {1.0, 1.25, 1.5, 1.75, 2.0, 2.5}
  C  sandbox_animus_mult     {0.6, 0.8}
  D  tier_c_bc_epsilon x bc_strength  {0.40, 0.50} x {0.015, 0.03}
  E  joint candidates: cross the per-axis picks, evaluate the FULL
     acceptance gate (user-adopted 2026-06-10):
       de-saturation hards: no corner-pin; dwnom_shape_resid <= 1.4;
         floor fraction materially down; BC gain >= 2x shipped
       ANES hards: s11_anes_bands tally >= 18/24; w2_total <= shipped*1.15;
         2020/2025 x {affect, party_sep} cells no-regress vs shipped;
         no cell > 2 band-widths out; no shipped-in-band cell exits by
         > 1 band-width
     If nothing passes: report the Pareto frontier and STOP (no commit).

Run: .venv/Scripts/python.exe scripts/audit/t06_desaturate.py --stage A
Writes docs/internal/audit/t06_desaturate.json (+ .md summary at E).
"""
from __future__ import annotations

import argparse
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

SEEDS = list(range(8))
END_TICK = 135
S11_TICKS = [(1980, 21), (1990, 42), (2000, 72), (2010, 102), (2020, 126), (2025, 135)]
W2_TICKS = [(1980, 21), (1990, 42), (2000, 72), (2010, 102), (2020, 126)]
BC_TEMP = 0.05
DWNOM_GROWTH = {1990: 1.00, 2000: 1.16, 2010: 1.37, 2020: 1.48, 2025: 1.51}
DECADE_TICKS = {1990: 42, 2000: 72, 2010: 102, 2020: 126, 2025: 135}

OUT_JSON = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                        "docs", "internal", "audit", "t06_desaturate.json"))
SHIPPED_SCORE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                             "docs", "results", "phase9_anes_score_anes_full.json"))


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------

def t06_worker(arg):
    """arg = (overrides_items_tuple, seed). Runs the full arc capturing
    saturation diagnostics + section-11 metrics + W2 position snapshots."""
    overrides, seed = arg
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from scripts.anes_preset import ANES_FULL_KWARGS
    from scripts.phase8f_lib import measure_all

    kwargs = dict(ANES_FULL_KWARGS)
    kwargs.update(dict(overrides))
    eng = build_engine(seed=seed, **kwargs)
    sched = build_schedule(
        factional_seeding=kwargs.get("factional_seeding", False),
        faction_anchor_events=kwargs.get("faction_anchor_events", True),
        evidence_regrade=kwargs.get("evidence_regrade", False),
        exogenous_shocks=kwargs.get("exogenous_shocks", False),
    )

    s11_at = {t: y for (y, t) in S11_TICKS}
    w2_at = {t: y for (y, t) in W2_TICKS}

    elite_traj = []      # per tick [e0x, e0y, e1x, e1y]
    s11 = {}
    snapshots = {}
    diag = {}

    def elite_row():
        ep = eng.env.attrs.get("parties", {})
        e0 = np.asarray(ep.get(0, np.zeros(2)), float)
        e1 = np.asarray(ep.get(1, np.zeros(2)), float)
        return [float(e0[0]), float(e0[1]), float(e1[0]), float(e1[1])]

    def saturation_diag():
        """Affect floor fractions + BC effective gain, at the current tick."""
        # floor: partisans' out-party warmth
        warmth = []
        for a in eng.agents:
            p = a.state.attrs.get("party")
            if p not in (0, 1):
                continue
            af = a.state.attrs.get("affect") or {}
            v = af.get(1 - p)
            if v is not None:
                warmth.append(float(np.clip(v, -1.0, 1.0)))
        warmth = np.array(warmth, float)
        # BC gain: replicate the rule's graded weight over network edges,
        # including the live affect modulator (events ramp affect_weight).
        bc = None
        for r in eng.rules.rules:
            if type(r).__name__ == "BoundedConfidenceInfluence":
                bc = r
                break
        net = eng.env.attrs["network"]
        eps_scale = float(eng.env.attrs.get("bc_epsilon_scale", 1.0))
        by_id = {int(a.id): a for a in eng.agents}
        ws_all = []
        for i, jj in net.edges():
            for a_id, b_id in ((i, jj), (jj, i)):
                a = by_id.get(int(a_id)); b = by_id.get(int(b_id))
                if a is None or b is None:
                    continue
                eps = float(a.state.attrs.get("epsilon", bc.epsilon)) * eps_scale
                d = float(np.linalg.norm(
                    np.asarray(a.state.ideology) - np.asarray(b.state.ideology)))
                w = 1.0 / (1.0 + np.exp(np.clip((d - eps) / BC_TEMP, -50, 50)))
                if bc.affect_weight > 0.0:
                    pa = a.state.attrs.get("party"); pb = b.state.attrs.get("party")
                    if pa is not None and pb is not None and pa != pb:
                        warm = float(np.clip(
                            (a.state.attrs.get("affect") or {}).get(pb, 0.0), -1, 1))
                        w *= float(np.clip(1.0 + bc.affect_weight * warm, 0.1, 2.0))
                ws_all.append(w)
        ws_all = np.array(ws_all, float) if ws_all else np.zeros(1)
        return {
            "affect_mean": float(warmth.mean()) if len(warmth) else 0.0,
            "floor_le_095": float((warmth <= -0.95).mean()) if len(warmth) else 0.0,
            "floor_le_099": float((warmth <= -0.99).mean()) if len(warmth) else 0.0,
            "bc_mean_weight": float(ws_all.mean()),
            "bc_frac_w_gt_05": float((ws_all > 0.5).mean()),
            "bc_strength_live": float(bc.strength) if bc is not None else 0.0,
        }

    elite_traj.append(elite_row())
    for t in range(1, END_TICK + 1):
        run_to(eng, sched, t)
        elite_traj.append(elite_row())
        if t in s11_at:
            y = s11_at[t]
            s11[y] = measure_all(eng)
            diag[y] = saturation_diag()
        if t in w2_at:
            snapshots[w2_at[t]] = np.array(
                [a.state.ideology for a in eng.agents], dtype=float)

    # corner-pin + DW-NOMINATE shape from the elite trajectory
    E = np.array(elite_traj, float)          # [T+1, 4]
    elite_sep = np.sqrt(((E[:, 0:2] - E[:, 2:4]) ** 2).sum(1))
    abs_max = np.abs(E).max(1)
    pin_ticks = np.where(abs_max >= 1.0 - 1e-9)[0]
    first_pin = int(pin_ticks[0]) if len(pin_ticks) else None
    d0 = elite_sep[DECADE_TICKS[1990]]
    resid = 0.0
    if d0 > 1e-6:
        for yr in (1990, 2000, 2010, 2020, 2025):
            resid += (elite_sep[DECADE_TICKS[yr]] / d0 - DWNOM_GROWTH[yr]) ** 2
    return {
        "s11": s11, "diag": diag,
        "snapshots": {y: v.tolist() for y, v in snapshots.items()},
        "elite_sep_decades": {yr: float(elite_sep[t]) for yr, t in DECADE_TICKS.items()},
        "elite_abs_max_final": float(abs_max[-1]),
        "first_corner_pin_tick": first_pin,
        "dwnom_shape_resid": float(resid),
    }


# ---------------------------------------------------------------------------
# Aggregation + gate
# ---------------------------------------------------------------------------

def run_config(overrides: dict, seeds=SEEDS):
    from abm.calibration_parallel import run_seeds_parallel
    key = tuple(sorted(overrides.items()))
    work = [(key, s) for s in seeds]
    return run_seeds_parallel(t06_worker, work)


def aggregate_config(results):
    """Seed-mean the diagnostics + s11 metrics; return summary dict."""
    from scripts.phase8f_lib import aggregate
    trajs = [{int(y): m for y, m in r["s11"].items()} for r in results]
    means, ses = aggregate(trajs)
    diag_years = sorted({int(y) for r in results for y in r["diag"]})
    diag = {}
    for y in diag_years:
        keys = results[0]["diag"][y].keys()
        diag[y] = {k: float(np.mean([r["diag"][y][k] for r in results])) for k in keys}
    out = {
        "means": {int(y): means[y] for y in means},
        "ses": {int(y): ses[y] for y in ses},
        "diag": diag,
        "dwnom_shape_resid": float(np.mean([r["dwnom_shape_resid"] for r in results])),
        "first_corner_pin_tick": [r["first_corner_pin_tick"] for r in results],
        "elite_abs_max_final": float(np.mean([r["elite_abs_max_final"] for r in results])),
        "elite_sep_decades": {yr: float(np.mean([r["elite_sep_decades"][yr] for r in results]))
                              for yr in results[0]["elite_sep_decades"]},
    }
    return out


def s11_cells(means, ses):
    """Score the 24 cells against the ANES band set (the live gate)."""
    from scripts.phase8f_lib import (get_primary_targets,
                                     get_initial_targets_1980, in_band)
    pri = get_primary_targets(use_anes_bands=True)
    init = get_initial_targets_1980(use_anes_bands=True)
    cells = []
    for year in (1990, 2000, 2010, 2020, 2025):
        for metric in ("constraint", "party_sep", "affect", "within_party_sd"):
            lo, hi = pri[year][metric]
            v = means[year][metric]
            cells.append({"year": year, "metric": metric, "value": float(v),
                          "band_lo": lo, "band_hi": hi,
                          "in_band": bool(in_band(v, (lo, hi)))})
    for metric in ("variance", "constraint", "party_sep", "within_party_sd"):
        lo, hi = init[metric]
        v = means[1980][metric]
        cells.append({"year": 1980, "metric": metric, "value": float(v),
                      "band_lo": lo, "band_hi": hi,
                      "in_band": bool(in_band(v, (lo, hi)))})
    return cells


def _band_dist(cell):
    """Distance outside the band, in band-width units (0 if inside)."""
    w = cell["band_hi"] - cell["band_lo"]
    if w <= 0:
        return 0.0
    v = cell["value"]
    if v < cell["band_lo"]:
        return (cell["band_lo"] - v) / w
    if v > cell["band_hi"]:
        return (v - cell["band_hi"]) / w
    return 0.0


def w2_total_for(results):
    """Wasserstein cloud distance vs data/phase9_empirical (POT path)."""
    from pathlib import Path
    from abm.calibration_phase9 import EMPIRICAL_DECADES, score_engine_run
    tot_per_seed = []
    for seed, r in enumerate(results):
        snaps = {int(y): np.array(v, float) for y, v in r["snapshots"].items()}
        df = score_engine_run(positions_by_decade=snaps,
                              target_dir=Path("data/phase9_empirical"),
                              seed_for_subsample=seed)
        tot_per_seed.append(
            sum(float(df[df["decade"] == d]["wasserstein"].mean())
                for d in EMPIRICAL_DECADES))
    return float(np.mean(tot_per_seed))


def evaluate_gate(summary, results, shipped):
    """The user-adopted T0.6 acceptance gate. Returns (verdict, checks)."""
    checks = {}
    # --- de-saturation hards ---
    checks["no_corner_pin"] = all(p is None for p in summary["first_corner_pin_tick"])
    checks["dwnom_resid_le_1.4"] = summary["dwnom_shape_resid"] <= 1.4
    floor_now = summary["diag"][2025]["floor_le_095"]
    checks["floor_materially_down"] = floor_now <= 0.5 * shipped["floor_le_095_2025"] \
        if shipped["floor_le_095_2025"] > 0.0 else True
    # BC effective gain = strength x mean logistic weight (the actual
    # influence magnitude; stage D showed weight alone tops out ~0.65
    # because cross-party edges sit far outside any plausible eps).
    d25 = summary["diag"][2025]
    bc_now = d25["bc_strength_live"] * d25["bc_mean_weight"]
    checks["bc_gain_2x"] = bc_now >= 2.0 * shipped["bc_gain_2025"]
    # --- ANES hards ---
    cells = s11_cells(summary["means"], summary["ses"])
    tally = sum(c["in_band"] for c in cells)
    checks["tally_ge_18"] = tally >= 18
    w2 = w2_total_for(results)
    checks["w2_le_1.15x"] = w2 <= 1.15 * shipped["w2_total"]
    # headline anchors no-regress
    ship_cells = {(c["year"], c["metric"]): c for c in shipped["cells"]}
    anchors_ok = True
    for (y, m) in [(2020, "affect"), (2025, "affect"),
                   (2020, "party_sep"), (2025, "party_sep")]:
        new = next(c for c in cells if c["year"] == y and c["metric"] == m)
        old = ship_cells[(y, m)]
        if old["in_band"] and not new["in_band"]:
            anchors_ok = False
        if (not old["in_band"]) and _band_dist(new) > _band_dist(old) + 1e-9:
            anchors_ok = False
    checks["headline_anchors_no_regress"] = anchors_ok
    # per-cell guards
    checks["no_cell_gt_2bw"] = all(_band_dist(c) <= 2.0 for c in cells)
    exits_ok = True
    for c in cells:
        old = ship_cells[(c["year"], c["metric"])]
        if old["in_band"] and not c["in_band"] and _band_dist(c) > 1.0:
            exits_ok = False
    checks["no_inband_exit_gt_1bw"] = exits_ok
    verdict = all(checks.values())
    return verdict, checks, tally, w2, cells


def shipped_reference(db):
    """Shipped gate reference: scorecard JSON + stage-A diagnostics."""
    with open(SHIPPED_SCORE, encoding="utf-8") as f:
        sc = json.load(f)
    a = db["stages"]["A"]["summary"]
    bands = sc["s11_anes_bands"]
    return {
        "w2_total": sc["w2_total"],
        "cells": bands["cells_4x5"] + bands["cells_init"],
        "tally": bands["tally_24"],
        "floor_le_095_2025": a["diag"]["2025"]["floor_le_095"],
        "bc_gain_2025": (a["diag"]["2025"]["bc_strength_live"]
                         * a["diag"]["2025"]["bc_mean_weight"]),
    }


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------

def _load_db():
    if os.path.exists(OUT_JSON):
        with open(OUT_JSON, encoding="utf-8") as f:
            return json.load(f)
    return {"stages": {}}


def _save_db(db):
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=1)


def _summ_no_snapshots(results):
    s = aggregate_config(results)
    return s


def _print_config_line(tag, s):
    d25 = s["diag"][2025] if 2025 in s["diag"] else s["diag"]["2025"]
    cells = s11_cells(s["means"], s["ses"])
    tally = sum(c["in_band"] for c in cells)
    pins = s["first_corner_pin_tick"]
    pin_s = ",".join("-" if p is None else str(p) for p in pins)
    print(f"{tag:42s} resid={s['dwnom_shape_resid']:5.2f} pin@[{pin_s}] "
          f"sep25={s['means'][2025]['party_sep']:.2f} "
          f"aff25={s['means'][2025]['affect']:+.2f} "
          f"wp25={s['means'][2025]['within_party_sd']:.2f} "
          f"floor={d25['floor_le_095']:.2f} bcw={d25['bc_mean_weight']:.3f} "
          f"s11={tally}/24")


def stage_A(db):
    print("Stage A — diagnose the shipped operating point (8 seeds)")
    results = run_config({})
    s = aggregate_config(results)
    db["stages"]["A"] = {"summary": _jsonable(s)}
    # decade-resolved saturation table
    print(f"{'year':>6} {'affect':>8} {'<=-.95':>7} {'<=-.99':>7} "
          f"{'bc_w':>7} {'bc>0.5':>7} {'bc_str':>7}")
    for y in sorted(s["diag"]):
        d = s["diag"][y]
        print(f"{y:>6} {d['affect_mean']:>8.3f} {d['floor_le_095']:>7.3f} "
              f"{d['floor_le_099']:>7.3f} {d['bc_mean_weight']:>7.4f} "
              f"{d['bc_frac_w_gt_05']:>7.3f} {d['bc_strength_live']:>7.3f}")
    print(f"corner-pin first tick per seed: {s['first_corner_pin_tick']}")
    print(f"dwnom_shape_resid={s['dwnom_shape_resid']:.3f} "
          f"elite_sep_2025={s['elite_sep_decades'][2025]:.3f}")
    _print_config_line("SHIPPED", s)
    _save_db(db)


def stage_B(db):
    print("Stage B — drift_mult sweep")
    grid = [1.0, 1.25, 1.5, 1.75, 2.0, 2.5]
    out = {}
    for v in grid:
        results = run_config({"tier_d_anes_drift_multiplier": v})
        s = aggregate_config(results)
        out[str(v)] = _jsonable(s)
        _print_config_line(f"drift={v}", s)
    db["stages"]["B"] = out
    _save_db(db)


def stage_C(db):
    print("Stage C — sandbox_animus_mult sweep")
    out = {}
    for v in [0.6, 0.8]:
        results = run_config({"sandbox_animus_mult": v})
        s = aggregate_config(results)
        out[str(v)] = _jsonable(s)
        _print_config_line(f"animus={v}", s)
    db["stages"]["C"] = out
    _save_db(db)


def stage_D(db):
    print("Stage D — bc epsilon x strength sweep")
    out = {}
    for eps in [0.40, 0.50]:
        for st in [0.015, 0.03]:
            results = run_config({"tier_c_bc_epsilon": eps,
                                  "tier_c_bc_strength": st})
            s = aggregate_config(results)
            out[f"eps={eps},str={st}"] = _jsonable(s)
            _print_config_line(f"bc eps={eps} str={st}", s)
    db["stages"]["D"] = out
    _save_db(db)


def stage_E(db, combos):
    """combos: list of override dicts (the candidate interior points)."""
    print("Stage E — joint candidates + full acceptance gate")
    shipped = shipped_reference(db)
    out = {}
    for ov in combos:
        tag = ",".join(f"{k.split('_')[-1] if not k.startswith('tier_c_bc') else k[10:]}={v}"
                       for k, v in sorted(ov.items()))
        results = run_config(ov)
        s = aggregate_config(results)
        verdict, checks, tally, w2, cells = evaluate_gate(s, results, shipped)
        out[tag] = {"overrides": ov, "summary": _jsonable(s),
                    "gate": {"verdict": verdict, "checks": checks,
                             "tally": tally, "w2_total": w2},
                    "cells": cells}
        _print_config_line(tag, s)
        flags = " ".join(k for k, v in checks.items() if not v)
        print(f"   gate={'PASS' if verdict else 'FAIL'} tally={tally}/24 "
              f"w2={w2:.3f} (shipped {shipped['w2_total']:.3f})"
              + (f"  FAILED: {flags}" if flags else ""))
    db["stages"].setdefault("E", {}).update(out)
    _save_db(db)


def stage_F(db):
    """Ridge re-run at a DIAGNOSTIC interior point (analysis-only — the
    gate STOPPED, nothing ships). Answers review_math P1.6: is the
    party_pull<->idpull_x ridge intrinsic to the mass observables, or a
    corner artifact of the saturated shipped point? Interior point:
    drift 1.5 (pin delayed to ~tick 71), animus 0.8 (floor 0.29->0.23),
    bc eps 0.4 / strength 0.03 (gain ~2.9x) — each axis moved well off
    its saturation, ANES fit NOT required (this point does not ship).
    Noise model = T0.5 v2: sqrt(MC-var@24seeds + (1% prior-range-SD)^2),
    prior-range-SD reused from phase5_identifiability_v2.json (same
    dynamic-range yardstick for both points, so cosines are comparable).
    """
    from abm.calibration_parallel import run_seeds_parallel
    from scripts.audit.battery import (PARAM_NAMES, STAT_TAGS,
                                       battery_worker_extra)
    print("Stage F — ridge re-run at the diagnostic interior point")
    theta_int = {"drift_mult": 1.5, "party_pull": 0.04, "bc_strength": 0.03,
                 "idpull_x": 0.020, "idpull_y": 0.040, "noise_sigma": 0.04,
                 "identity_mult": 1.0, "animus_mult": 0.8}
    base = np.array([theta_int[n] for n in PARAM_NAMES], float)
    extra = (("tier_c_bc_epsilon", 0.4),)
    v2 = json.load(open(os.path.join(os.path.dirname(OUT_JSON),
                                     "phase5_identifiability_v2.json"),
                        encoding="utf-8"))
    # baseline (24 seeds) for MC-SD at the interior point
    bwork = [(tuple(base.tolist()), s, extra) for s in range(24)]
    bres = run_seeds_parallel(battery_worker_extra, bwork)
    NAMES = list(bres[0][2].keys())
    bmat = np.array([[d[n] for n in NAMES] for (_t, _s, d) in bres])
    sd_seed = bmat.std(0, ddof=1)
    pscale = np.array([v2["prior_design_sd"][n] for n in NAMES])
    keep = np.array([STAT_TAGS[n] == "continuous"
                     and (sd_seed[i] > 0 or pscale[i] > 0)
                     for i, n in enumerate(NAMES)])
    scale = np.sqrt(sd_seed[keep] ** 2 + (0.01 * pscale[keep]) ** 2)
    # Jacobian +/-15%, 8 seeds
    npar = len(PARAM_NAMES)
    jwork, meta = [], []
    for j in range(npar):
        for sgn in (+1, -1):
            th = base.copy(); th[j] *= (1.0 + sgn * 0.15)
            for s in range(8):
                jwork.append((tuple(th.tolist()), s, extra))
                meta.append((j, sgn))
    jres = run_seeds_parallel(battery_worker_extra, jwork)
    acc = {}
    for (j, sgn), (_t, _s, d) in zip(meta, jres):
        acc.setdefault((j, sgn), []).append([d[n] for n in NAMES])
    J = np.zeros((int(keep.sum()), npar))
    for j in range(npar):
        hi = np.array(acc[(j, +1)]).mean(0)[keep]
        lo = np.array(acc[(j, -1)]).mean(0)[keep]
        J[:, j] = (hi - lo) / 0.30
    J_std = J / scale[:, None]
    J_prior = J / np.maximum(pscale[keep], 1e-12)[:, None]

    def cosmat(Jm):
        cn = np.linalg.norm(Jm, axis=0); cn = np.where(cn > 0, cn, 1.0)
        Jn = Jm / cn
        return Jn.T @ Jn

    def report(C, tag):
        pairs = []
        for a in range(npar):
            for b in range(a + 1, npar):
                pairs.append((PARAM_NAMES[a], PARAM_NAMES[b],
                              round(float(C[a, b]), 3)))
        pairs.sort(key=lambda t: -abs(t[2]))
        ev = np.linalg.eigvalsh(C)
        er = float((ev.sum() ** 2) / (ev ** 2).sum())
        print(f" {tag}: eff_rank={er:.2f} top={pairs[:4]}")
        return {"top_pairs": [list(p) for p in pairs[:8]],
                "eff_rank_cosine_gram": round(er, 2),
                "pp_idx": round(float(
                    C[PARAM_NAMES.index('party_pull'),
                      PARAM_NAMES.index('idpull_x')]), 3),
                "pp_idy": round(float(
                    C[PARAM_NAMES.index('party_pull'),
                      PARAM_NAMES.index('idpull_y')]), 3)}

    out = {"interior_point": theta_int,
           "extra_overrides": dict(extra),
           "noise_std": report(cosmat(J_std), "noise_standardized"),
           "prior_sd_std": report(cosmat(J_prior), "prior_sd_standardized")}
    db["stages"]["F"] = _jsonable(out)
    _save_db(db)


def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        return float(o)
    return o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True,
                    choices=["A", "B", "C", "D", "E", "F"])
    ap.add_argument("--combo", action="append", default=[],
                    help="Stage E: JSON override dict, repeatable.")
    args = ap.parse_args()
    db = _load_db()
    if args.stage == "A":
        stage_A(db)
    elif args.stage == "B":
        stage_B(db)
    elif args.stage == "C":
        stage_C(db)
    elif args.stage == "D":
        stage_D(db)
    elif args.stage == "E":
        combos = [json.loads(c) for c in args.combo]
        if not combos:
            raise SystemExit("stage E needs --combo '{...}' candidates")
        stage_E(db, combos)
    elif args.stage == "F":
        stage_F(db)


if __name__ == "__main__":
    main()
