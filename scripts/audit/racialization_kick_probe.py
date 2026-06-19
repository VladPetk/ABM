"""Probe (one-off): racialization as a KICK (rise -> hold -> partial decay) vs a
monotone HOLD — does deracialization (2020->2024 Latino/minority dealignment;
the ANES series peaks 2020, dips 2024) reproduce, and does the one-way ratchet
(blindspot #11) even LET the kick decay? Spec docs/internal/racialization_spillover_spec.md.

The single racialization knob = IdentityToIdeologyPull.strength_y, time-profiled:
  ramp  2008(t84) -> 2016(t108):  0 -> peak
  hold  2016(t108)-> 2020(t120):  peak
  decay 2020(t120)-> 2024(t132):  peak -> peak*decay_frac   (deracialization)
mob frozen at 2008 (the racialization REPLACES the post-2008 grab-bag), as in
racialization_fit_compare.py.

Three questions:
  [Q1 fit]    does the kick bend the late (2024) overshoot back toward ANES?
  [Q2 ratchet] does party_sep actually DECLINE 2020->2024 when the pull relaxes,
               or does the ratchet hold (positions stick)?
  [Q3 asym]   does AFFECT stay sticky (not un-warm) while position dips? (the
               R-phase reversibility asymmetry; affect kept rising 2020-2024.)

Conditions: schedule (ref), rac_hold (monotone), rac_kick (rise/hold/decay).
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
from scripts.phase8f_lib import affective_polarization
from scripts.audit.audit_lib import _make_schedule, END_TICK

PEAK = 0.30
DECAY_FRAC = 0.25            # relax to 25% of peak by 2024 (modest; graded LOW)
T_ON, T_PEAK, T_DECAY_END = 84, 108, 132      # 2008 / 2016 / 2024
SEEDS = (0, 1, 2, 3, 4)
CONDS = ["schedule", "rac_hold", "rac_kick"]
ANES_YEARS = [1986, 2000, 2008, 2016, 2020, 2024]
YEAR_TICKS = {y: (y - 1980) * 3 for y in ANES_YEARS}
SNAP = sorted(YEAR_TICKS.values())
# ANES combined (scaled_separation) at those years, for the 2008-indexed shape.
ANES_COMB = {1986: 0.9572, 2000: 1.3917, 2008: 1.8980,
             2016: 2.6083, 2020: 3.1986, 2024: 2.9308}


def _strength(cond, t):
    if cond == "rac_hold":
        if t < T_ON:
            return 0.0
        if t < T_PEAK:
            return PEAK * (t - T_ON) / (T_PEAK - T_ON)
        return PEAK
    if cond == "rac_kick":
        if t < T_ON:
            return 0.0
        if t < T_PEAK:
            return PEAK * (t - T_ON) / (T_PEAK - T_ON)
        if t < 120:                       # hold 2016->2020
            return PEAK
        if t <= T_DECAY_END:              # decay 2020->2024
            frac = (t - 120) / (T_DECAY_END - 120)
            return PEAK * (1.0 - (1.0 - DECAY_FRAC) * frac)
        return PEAK * DECAY_FRAC
    return 0.0


def _find(eng, name):
    for r in list(eng.rules.rules) + list(getattr(eng, "env_rules", [])):
        if type(r).__name__ == name:
            return r
    return None


def _comb(eng):
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
    cond, seed = arg
    eng = build_engine(seed=seed, **ANES_FULL_KWARGS)
    sched = _make_schedule("full")
    idpp = _find(eng, "IdentityToIdeologyPull")
    mob_frozen = None
    snaps = {}
    for t in range(1, END_TICK + 1):
        run_to(eng, sched, t)
        if t == T_ON:
            mob_frozen = dict(eng.env.attrs.get("activist_mobilization") or {})
        if cond != "schedule":
            if t >= T_ON and mob_frozen is not None:
                eng.env.attrs["activist_mobilization"] = dict(mob_frozen)
            if idpp is not None:
                idpp.strength_y = _strength(cond, t)
        if t in SNAP:
            snaps[t] = {"comb": _comb(eng),
                        "aff": float(affective_polarization(eng.agents)),
                        "corr": _corr(eng)}
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

    t08 = YEAR_TICKS[2008]
    print(f"Racialization KICK vs HOLD — peak={PEAK}, decay->{DECAY_FRAC}x by 2024, "
          f"{len(SEEDS)} seeds")
    print("=" * 76)

    print("\n[Q1 fit] combined party_sep, INDEXED to 2008=1.0 (vs ANES shape):")
    print(f"    {'cond':<12}" + "".join(f"{('y'+str(y)):>9}" for y in ANES_YEARS))
    anes_idx = {y: ANES_COMB[y] / ANES_COMB[2008] for y in ANES_YEARS}
    print(f"    {'ANES':<12}" + "".join(f"{anes_idx[y]:>9.3f}" for y in ANES_YEARS))
    for c in CONDS:
        base = avg(c, t08, "comb")
        print(f"    {c:<12}" + "".join(
            f"{avg(c, YEAR_TICKS[y], 'comb') / base:>9.3f}" for y in ANES_YEARS))

    print("\n[Q2 ratchet] does party_sep DECLINE 2020->2024 (raw units)?  "
          "(ANES dips 3.20->2.93 = -8.4%)")
    for c in CONDS:
        s20, s24 = avg(c, YEAR_TICKS[2020], "comb"), avg(c, YEAR_TICKS[2024], "comb")
        pct = 100.0 * (s24 - s20) / s20 if s20 else float("nan")
        verdict = "DECLINES" if s24 < s20 - 1e-4 else ("flat" if abs(s24 - s20) <= 1e-4 else "rises")
        print(f"    {c:<12} 2020={s20:.4f}  2024={s24:.4f}  ({pct:+.1f}%)  -> {verdict}")

    print("\n[Q3 asym] AFFECT (out-party warmth; more negative = MORE animus) — "
          "should stay sticky/cold while position dips:")
    for c in CONDS:
        a20, a24 = avg(c, YEAR_TICKS[2020], "aff"), avg(c, YEAR_TICKS[2024], "aff")
        print(f"    {c:<12} 2020={a20:+.4f}  2024={a24:+.4f}  (Δ {a24-a20:+.4f})")

    print("\n[signature] spillover corr(identity, issue) — kick should PEAK then dip:")
    for c in CONDS:
        vals = [avg(c, YEAR_TICKS[y], "corr") for y in [2008, 2016, 2020, 2024]]
        print(f"    {c:<12} 2008={vals[0]:.3f}  2016={vals[1]:.3f}  "
              f"2020={vals[2]:.3f}  2024={vals[3]:.3f}")


if __name__ == "__main__":
    main()
