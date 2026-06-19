"""Two clean tests the expert review (spec §10) demanded before any decoupling claim.

TEST 1 - matched-sorting signature contrast (§6.2 done right).
  The original elite_2.0 control UNDERSHOT party_sep (0.90 vs rac 1.11), so the
  "spillover != gain bump" comparison was never at matched sorting. Fix: sweep BOTH
  families from the frozen-2008-mob baseline and read spillover_corr as a FUNCTION
  of party_sep -- a corr-vs-sorting frontier. If the racialization family's corr
  sits ABOVE the elite-gain family's at matched party_sep, the mechanism is
  genuinely distinguishable (no exact-match fudge needed).
    elite_M : frozen mob x M  (turn the existing axis up; NO identity spillover)
    rac_P   : frozen mob + IdentityToIdeologyPull strength_y ramped to peak P, held

TEST 2 - hold-at-peak (the reversibility honesty check).
  Is the kick's 2020->2024 decline endogenous, or does it REQUIRE removing the
  forcing? Compare rac_hold (peak held, no decay) vs rac_kick (peak then decay).
  If hold does NOT decline (sorting sticky/rising) while kick does, the honest
  claim is "ratchet releases only GIVEN an exogenous release; restoring forces
  then act -- NOT endogenous depolarization."

frozen mob = hold activist_mobilization at its 2008 value for t>=84 (the post-2008
elite grab-bag removed, so the kick/elite-gain is the only post-2008 driver).
"""
from __future__ import annotations

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

import json
import numpy as np

from abm.pillars.historical_arc import build_engine
from abm.pillars.schedule import run_to
from scripts.anes_preset import ANES_FULL_KWARGS
from scripts.audit.audit_lib import _make_schedule, END_TICK

T_ON, T_PEAK, T_HOLD_END, T_DECAY_END = 84, 108, 120, 132   # 2008/2016/2020/2024
SEEDS = (0, 1, 2, 3, 4)
SNAP = [108, 120, 132]   # 2016 / 2020 / 2024

# (label, kind, param, decay_frac)  kind in {elite, rac}
CONDS = [
    ("elite_2.0",      "elite", 2.0,  None),
    ("elite_3.0",      "elite", 3.0,  None),
    ("elite_4.0",      "elite", 4.0,  None),
    ("rac_hold_0.10",  "rac",   0.10, None),
    ("rac_hold_0.20",  "rac",   0.20, None),
    ("rac_hold_0.30",  "rac",   0.30, None),
    ("rac_kick_0.20",  "rac",   0.20, 0.35),
]


def _kick_strength(peak, decay, t):
    if t < T_ON:
        return 0.0
    if t < T_PEAK:
        return peak * (t - T_ON) / (T_PEAK - T_ON)
    if decay is None or t < T_HOLD_END:
        return peak
    if t <= T_DECAY_END:
        frac = (t - T_HOLD_END) / (T_DECAY_END - T_HOLD_END)
        return peak * (1.0 - (1.0 - decay) * frac)
    return peak * decay


def _find(eng, name):
    for r in list(eng.rules.rules) + list(getattr(eng, "env_rules", [])):
        if type(r).__name__ == name:
            return r
    return None


def _sep(eng):
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    if (parties == 0).sum() == 0 or (parties == 1).sum() == 0:
        return 0.0
    return float(np.linalg.norm(pos[parties == 0].mean(0) - pos[parties == 1].mean(0)))


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
    label, seed = arg
    _, kind, param, decay = next(c for c in CONDS if c[0] == label)
    eng = build_engine(seed=seed, **ANES_FULL_KWARGS)
    sched = _make_schedule("full")
    idpp = _find(eng, "IdentityToIdeologyPull")
    mob2008 = None
    snaps = {}
    for t in range(1, END_TICK + 1):
        run_to(eng, sched, t)
        if t == T_ON:
            mob2008 = dict(eng.env.attrs.get("activist_mobilization") or {})
        if t >= T_ON and mob2008 is not None:
            mult = param if kind == "elite" else 1.0
            eng.env.attrs["activist_mobilization"] = {p: v * mult for p, v in mob2008.items()}
        if kind == "rac" and idpp is not None:
            idpp.strength_y = _kick_strength(param, decay, t)
        if t in SNAP:
            snaps[t] = {"sep": _sep(eng), "corr": _corr(eng)}
    return {"label": label, "seed": seed, "snaps": snaps}


def main():
    from abm.calibration_parallel import run_seeds_parallel
    res = run_seeds_parallel(_worker, [(c[0], s) for c in CONDS for s in SEEDS])
    by = {}
    for r in res:
        by.setdefault(r["label"], []).append(r["snaps"])

    def avg(label, tick, key):
        vals = [s[tick][key] for s in by[label]]
        vals = [v for v in vals if not (isinstance(v, float) and np.isnan(v))]
        return float(np.mean(vals)) if vals else float("nan")

    print(f"Racialization clean tests — {len(SEEDS)} seeds")
    print("=" * 72)

    print("\n[TEST 1] spillover_corr as a function of party_sep at 2024 "
          "(frontier; matched-sorting contrast):")
    print(f"    {'family/cond':<16}{'party_sep':>11}{'spillover_corr':>16}")
    frontier = {"elite": [], "rac": []}
    for label, kind, param, decay in CONDS:
        if decay is not None:
            continue   # exclude the kick (decayed) from the level frontier
        s, c = avg(label, 132, "sep"), avg(label, 132, "corr")
        fam = "elite" if kind == "elite" else "rac"
        frontier[fam].append((s, c))
        print(f"    {label:<16}{s:>11.4f}{c:>16.3f}")
    # interpolate elite corr at each rac party_sep to compare at matched sorting
    print("\n    matched-sorting read (elite corr interpolated to each rac sep):")
    el = sorted(frontier["elite"])
    es = [p[0] for p in el]; ec = [p[1] for p in el]
    for s, c in sorted(frontier["rac"]):
        ei = float(np.interp(s, es, ec)) if es[0] <= s <= es[-1] else float("nan")
        gap = (c - ei) if not np.isnan(ei) else float("nan")
        tag = "(rac sep beyond elite range)" if np.isnan(ei) else ""
        print(f"    rac sep={s:.3f} corr={c:.3f}  vs elite@sep corr={ei:.3f}  "
              f"-> rac-elite = {gap:+.3f} {tag}")

    print("\n[TEST 2] hold-at-peak vs decaying kick (reversibility honesty), peak 0.20:")
    print(f"    {'cond':<16}{'sep 2020':>10}{'sep 2024':>10}{'2020->2024':>12}")
    for label in ("rac_hold_0.20", "rac_kick_0.20"):
        s20, s24 = avg(label, 120, "sep"), avg(label, 132, "sep")
        pct = 100.0 * (s24 - s20) / s20 if s20 else float("nan")
        verdict = "DECLINES" if s24 < s20 - 1e-3 else ("flat" if abs(s24 - s20) <= 1e-3 else "rises")
        print(f"    {label:<16}{s20:>10.4f}{s24:>10.4f}{pct:>11.1f}%  {verdict}")
    print("    read: hold rises/flat (NO endogenous decline) + kick declines "
          "=> decline REQUIRES the exogenous release; restoring forces then act.")

    out = {"frontier": frontier,
           "test2": {lab: {str(t): {"sep": avg(lab, t, "sep"), "corr": avg(lab, t, "corr")}
                           for t in SNAP} for lab in ("rac_hold_0.20", "rac_kick_0.20")}}
    (_ROOT / "docs" / "internal" / "racialization_clean_tests.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    print("\nwrote docs/internal/racialization_clean_tests.json")


if __name__ == "__main__":
    main()
