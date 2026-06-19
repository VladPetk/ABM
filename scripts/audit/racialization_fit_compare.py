"""Identifiability check (spec docs/internal/racialization_spillover_spec.md §6).

Compares, on the ANES survey-year grid, three ways of producing the post-2008
sorting acceleration — plus an elite-gain contrast for the §6.2 signature test:

  raw       — the emergent mechanisms with the post-2008 sorting grab-bag FROZEN
              at its 2008 value (activist_mobilization held; the 2010/2020 steps
              neutralized). The "gap" line: what the mechanisms do unaided.
  schedule  — canonical ANES_FULL_KWARGS, full schedule. The status quo (many knobs).
  rac_*     — raw + ONE racialization knob: IdentityToIdeologyPull ramped 2008->2016
              (the spillover channel REPLACES the grab-bag). k=1.
  elite_*   — raw + a compensating elite-gain bump (frozen mob x M). Same family as
              the schedule (turn the existing axis up), NO identity spillover —
              the §6.2 contrast: does rac raise the spillover signature MORE than a
              gain bump at comparable sorting?

party_sep = ||Dem_centroid - Rep_centroid||; decomposed:
  econ = |dx|, cult = |dy|, combined = norm  (model axes: x=econ, y=cult).
ANES counterparts (data/phase9_empirical/derived/polarization_series.csv):
  econ <- wasserstein_econ, cult <- wasserstein_cult, combined <- scaled_separation.

Per §6.1 the comparison is SHAPE, parsimony-adjusted: each series is indexed to
its 2008 value (=1.0) and scored by per-survey-year RMSE of the indexed shape —
a uniform magnitude undershoot does not count against the k=1 model.

Outputs docs/internal/racialization_fit_data.json (indexed series for the graphs)
and prints the per-year shape-RMSE table + the §6.2 signature contrast.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

import numpy as np

from abm.pillars.historical_arc import build_engine
from abm.pillars.schedule import run_to
from scripts.anes_preset import ANES_FULL_KWARGS
from scripts.audit.audit_lib import _make_schedule, END_TICK

RELEASE = 84            # 2008
RAMP_END = 108          # 2016 (racialization onset window 2008->2016)
SEEDS = (0, 1, 2, 3, 4)
CONDS = ["raw", "schedule", "rac_0.25", "rac_0.40", "elite_2.0"]

# ANES survey years -> ticks (year-1980)*3. All within 0..135.
ANES_YEARS = [1986, 1988, 1990, 1992, 1994, 1996, 1998, 2000,
              2004, 2008, 2012, 2016, 2020, 2024]
YEAR_TICKS = {y: (y - 1980) * 3 for y in ANES_YEARS}
SNAP_TICKS = sorted(YEAR_TICKS.values())

# ANES empirical per-axis + combined (the calibration target).
ANES = {
    1986: (0.3209, 0.1216, 0.9572), 1988: (0.3756, 0.2037, 1.2086),
    1990: (0.3256, 0.1734, 1.0223), 1992: (0.4075, 0.2950, 1.4155),
    1994: (0.4037, 0.3152, 1.4363), 1996: (0.4449, 0.3069, 1.5857),
    1998: (0.3743, 0.3202, 1.3581), 2000: (0.3879, 0.2840, 1.3917),
    2004: (0.5241, 0.4416, 1.8978), 2008: (0.5840, 0.4011, 1.8980),
    2012: (0.6206, 0.5186, 2.3419), 2016: (0.7018, 0.6294, 2.6083),
    2020: (0.8382, 0.7832, 3.1986), 2024: (0.7599, 0.7335, 2.9308),
}  # (econ, cult, combined)


def _parse(cond):
    if cond == "raw":
        return dict(freeze=True, mult=1.0, idpp=None)
    if cond == "schedule":
        return dict(freeze=False, mult=1.0, idpp=None)
    if cond.startswith("rac_"):
        return dict(freeze=True, mult=1.0, idpp=float(cond[4:]))
    if cond.startswith("elite_"):
        return dict(freeze=True, mult=float(cond[6:]), idpp=None)
    raise ValueError(cond)


def _find(eng, name):
    for r in list(eng.rules.rules) + list(getattr(eng, "env_rules", [])):
        if type(r).__name__ == name:
            return r
    return None


def _sep_axes(eng):
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    if (parties == 0).sum() == 0 or (parties == 1).sum() == 0:
        return 0.0, 0.0, 0.0
    d = pos[parties == 0].mean(0)
    r = pos[parties == 1].mean(0)
    diff = d - r
    return abs(float(diff[0])), abs(float(diff[1])), float(np.linalg.norm(diff))


def _corr(eng):
    pos, ident, party = [], [], []
    for a in eng.agents:
        p = a.state.attrs.get("party")
        if p not in (0, 1):
            continue
        ids = a.state.attrs.get("identities")
        if ids is None or len(ids) == 0:
            continue
        pos.append(np.asarray(a.state.ideology, dtype=float))
        ident.append(float(np.mean(ids)))
        party.append(p)
    if len(pos) < 3:
        return float("nan")
    pos = np.asarray(pos); party = np.asarray(party); ident = np.asarray(ident)
    axis = pos[party == 1].mean(0) - pos[party == 0].mean(0)
    n = float(np.linalg.norm(axis))
    if n < 1e-9:
        return float("nan")
    proj = pos @ (axis / n)
    if np.std(proj) < 1e-9 or np.std(ident) < 1e-9:
        return float("nan")
    return float(np.corrcoef(ident, proj)[0, 1])


def _worker(arg):
    cond, seed = arg
    cfg = _parse(cond)
    eng = build_engine(seed=seed, **ANES_FULL_KWARGS)
    sched = _make_schedule("full")
    idpp = _find(eng, "IdentityToIdeologyPull")
    mob_frozen = None
    snaps = {}
    for t in range(1, END_TICK + 1):
        run_to(eng, sched, t)
        if t == RELEASE:
            mob_frozen = dict(eng.env.attrs.get("activist_mobilization") or {})
        if t >= RELEASE and cfg["freeze"] and mob_frozen is not None:
            eng.env.attrs["activist_mobilization"] = {
                p: v * cfg["mult"] for p, v in mob_frozen.items()}
        if t >= RELEASE and cfg["idpp"] is not None and idpp is not None:
            frac = min(1.0, (t - RELEASE) / float(RAMP_END - RELEASE))
            idpp.strength_y = cfg["idpp"] * frac
        if t in SNAP_TICKS:
            e, c, comb = _sep_axes(eng)
            snaps[t] = {"econ": e, "cult": c, "comb": comb, "corr": _corr(eng)}
    return {"cond": cond, "seed": seed, "snaps": snaps}


def main():
    from abm.calibration_parallel import run_seeds_parallel
    res = run_seeds_parallel(_worker, [(c, s) for c in CONDS for s in SEEDS])
    by = {}
    for r in res:
        by.setdefault(r["cond"], []).append(r["snaps"])

    def avg(cond, tick, key):
        vals = [s[tick][key] for s in by[cond]]
        vals = [v for v in vals if not (isinstance(v, float) and np.isnan(v))]
        return float(np.mean(vals)) if vals else float("nan")

    # Build indexed-to-2008 series per axis per condition.
    t2008 = YEAR_TICKS[2008]
    axes = ["econ", "cult", "comb"]
    series = {}   # series[axis][cond] = [v at each year]
    for ax in axes:
        series[ax] = {}
        a2008 = {c: avg(c, t2008, ax) for c in CONDS}
        for c in CONDS:
            base = a2008[c] if abs(a2008[c]) > 1e-9 else 1.0
            series[ax][c] = [avg(c, YEAR_TICKS[y], ax) / base for y in ANES_YEARS]
        anes2008 = ANES[2008][axes.index(ax)]
        series[ax]["ANES"] = [ANES[y][axes.index(ax)] / anes2008 for y in ANES_YEARS]

    # Per-year shape RMSE vs ANES (indexed), per axis per condition.
    def rmse(ax, cond):
        m = np.array(series[ax][cond]); a = np.array(series[ax]["ANES"])
        return float(np.sqrt(np.mean((m - a) ** 2)))

    print(f"Racialization fit/identifiability — {len(SEEDS)} seeds, "
          f"indexed to 2008=1.0 (SHAPE, per spec §6.1)")
    print("=" * 72)
    print("\n[§6.1] per-survey-year shape RMSE vs ANES (lower = better SHAPE fit):")
    print(f"    {'condition':<12}{'econ':>10}{'cult':>10}{'combined':>10}")
    for c in [x for x in CONDS if not x.startswith("elite_")]:
        print(f"    {c:<12}{rmse('econ', c):>10.4f}{rmse('cult', c):>10.4f}"
              f"{rmse('comb', c):>10.4f}")
    rac_conds = [c for c in CONDS if c.startswith("rac_")]
    best_rac = min(rac_conds, key=lambda c: rmse("comb", c))
    print(f"    -> best racialization (combined shape): {best_rac}")

    # §6.2 — signature contrast: rac vs elite_gain at matched sorting.
    elite = next((c for c in CONDS if c.startswith("elite_")), None)
    print("\n[§6.2] signature contrast — does rac raise spillover_corr MORE than "
          "an elite-gain bump\n        at comparable sorting? (2025-ish, tick 132)")
    t132 = YEAR_TICKS[2024]
    print(f"    {'condition':<12}{'party_sep':>11}{'spillover_corr':>16}")
    for c in ["raw", best_rac, elite, "schedule"]:
        if c is None:
            continue
        print(f"    {c:<12}{avg(c, t132, 'comb'):>11.4f}{avg(c, t132, 'corr'):>16.3f}")

    out = {
        "years": ANES_YEARS, "axes": axes, "conds": CONDS, "best_rac": best_rac,
        "series": series,
        "rmse": {ax: {c: rmse(ax, c) for c in CONDS} for ax in axes},
    }
    outp = _ROOT / "docs" / "internal" / "racialization_fit_data.json"
    outp.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nwrote {outp}")


if __name__ == "__main__":
    main()
