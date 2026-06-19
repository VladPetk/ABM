"""Calibration probe (spec §9): pick the racialization-kick config that best fits
ANES PER AXIS, settling two coupled choices before engine plumbing:

  (a) base treatment of the post-2008 elite-mobilization (econ driver, Hacker-Pierson):
        freeze_*  — hold mob at 2008 (racialization substitutes the loop's push)
        keep_*    — leave the full schedule running (elite divergence intact, hotter)
  (b) the kick peak + 2020->2024 decay (deracialization).

Econ axis is carried by the elite loop (kept), cultural by the racialization kick
(IDPP strength_y, kick profile). Per spec: racialized-economics does NOT justify
loading race onto econ; econ = elite-economic divergence (already in the model).

Indexed to 2008=1.0 (shape). Per-axis + combined per-survey-year RMSE vs ANES.
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

import numpy as np

from abm.pillars.historical_arc import build_engine
from abm.pillars.schedule import run_to
from scripts.anes_preset import ANES_FULL_KWARGS
from scripts.audit.audit_lib import _make_schedule, END_TICK

T_ON, T_PEAK, T_HOLD_END, T_DECAY_END = 84, 108, 120, 132   # 2008/2016/2020/2024
SEEDS = (0, 1, 2, 3, 4)
ANES_YEARS = [1986, 2000, 2008, 2016, 2020, 2024]
YEAR_TICKS = {y: (y - 1980) * 3 for y in ANES_YEARS}
SNAP = sorted(YEAR_TICKS.values())
# (econ, cult, comb) per year.
ANES = {1986: (0.3209, 0.1216, 0.9572), 2000: (0.3879, 0.2840, 1.3917),
        2008: (0.5840, 0.4011, 1.8980), 2016: (0.7018, 0.6294, 2.6083),
        2020: (0.8382, 0.7832, 3.1986), 2024: (0.7599, 0.7335, 2.9308)}

# config = (label, peak, decay_frac, mob_mult)
# mob_mult trims the post-2008 mobilization INCREMENT (the 2010/2020 steps) above
# the 2008 level, read from the NOMINAL schedule (not the polluted env value):
#   mob(t) = mob_2008 + mult*(nominal_sched(t) - mob_2008). mult=0 freeze, 1 keep.
# Econ rides this (Hacker-Pierson elite divergence); cult rides the kick (peak).
CONFIGS = [
    ("schedule",     None, None, 1.0),
    ("m0.0_p0.15",   0.15, 0.35, 0.0),
    ("m0.4_p0.15",   0.15, 0.35, 0.4),
    ("m0.7_p0.10",   0.10, 0.35, 0.7),
    ("m0.7_p0.15",   0.15, 0.35, 0.7),
    ("m1.0_p0.05",   0.05, 0.35, 1.0),
]


def _mob_key(t):
    if t < 30:
        return "1980"
    if t < 42:
        return "1990-00"
    if t < 60:
        return "gingrich_1994"
    if t < 90:
        return "2000-10"
    if t < 120:
        return "2010-20"
    return "2020-25"


def _strength(peak, decay, t):
    if peak is None or t < T_ON:
        return 0.0
    if t < T_PEAK:
        return peak * (t - T_ON) / (T_PEAK - T_ON)
    if t < T_HOLD_END:
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


def _axes(eng):
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    if (parties == 0).sum() == 0 or (parties == 1).sum() == 0:
        return 0.0, 0.0, 0.0
    diff = pos[parties == 0].mean(0) - pos[parties == 1].mean(0)
    return abs(float(diff[0])), abs(float(diff[1])), float(np.linalg.norm(diff))


def _worker(arg):
    label, seed = arg
    cfg = next(c for c in CONFIGS if c[0] == label)
    _, peak, decay, mob_mult = cfg
    eng = build_engine(seed=seed, **ANES_FULL_KWARGS)
    sched = _make_schedule("full")
    idpp = _find(eng, "IdentityToIdeologyPull")
    mob_sched = dict(eng.env.attrs.get("activist_mobilization_schedule") or {})
    mob2008 = dict(mob_sched.get("2000-10") or {})        # nominal mob at 2008
    snaps = {}
    for t in range(1, END_TICK + 1):
        run_to(eng, sched, t)
        # partial-mob trim on the post-2008 increment, from the NOMINAL schedule
        if peak is not None and mob_mult != 1.0 and t >= T_ON and mob2008:
            nom = mob_sched.get(_mob_key(t)) or {}
            eng.env.attrs["activist_mobilization"] = {
                p: mob2008.get(p, nom.get(p, 0.0))
                + mob_mult * (nom.get(p, 0.0) - mob2008.get(p, nom.get(p, 0.0)))
                for p in nom}
        if peak is not None and idpp is not None:
            idpp.strength_y = _strength(peak, decay, t)
        if t in SNAP:
            e, c, comb = _axes(eng)
            snaps[t] = {"econ": e, "cult": c, "comb": comb}
    return {"label": label, "seed": seed, "snaps": snaps}


def main():
    from abm.calibration_parallel import run_seeds_parallel
    res = run_seeds_parallel(_worker, [(c[0], s) for c in CONFIGS for s in SEEDS])
    by = {}
    for r in res:
        by.setdefault(r["label"], []).append(r["snaps"])

    def avg(label, tick, key):
        return float(np.mean([s[tick][key] for s in by[label]]))

    axes = ["econ", "cult", "comb"]
    t08 = YEAR_TICKS[2008]
    print(f"Racialization KICK calibration — per axis, indexed 2008=1.0, {len(SEEDS)} seeds")
    print("=" * 78)
    # indexed ANES per axis
    anes_idx = {ax: {y: ANES[y][i] / ANES[2008][i] for y in ANES_YEARS}
                for i, ax in enumerate(axes)}

    for ax in axes:
        print(f"\n[{ax}] indexed 2008=1.0 :")
        print(f"    {'config':<14}" + "".join(f"{('y'+str(y)):>9}" for y in ANES_YEARS) + f"{'RMSE':>9}")
        print(f"    {'ANES':<14}" + "".join(f"{anes_idx[ax][y]:>9.3f}" for y in ANES_YEARS))
        for label, *_ in CONFIGS:
            base = avg(label, t08, ax)
            row = [avg(label, YEAR_TICKS[y], ax) / base for y in ANES_YEARS]
            rmse = float(np.sqrt(np.mean([(row[k] - anes_idx[ax][ANES_YEARS[k]]) ** 2
                                          for k in range(len(ANES_YEARS))])))
            print(f"    {label:<14}" + "".join(f"{v:>9.3f}" for v in row) + f"{rmse:>9.4f}")

    print("\nPick: lowest combined RMSE with econ NOT badly under and cult tracking "
          "the 2020 peak / 2024 dip. (econ rides the kept elite loop; cult rides the kick.)")


if __name__ == "__main__":
    main()
