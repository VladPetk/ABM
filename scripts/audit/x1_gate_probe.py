"""Diagnostic (one-off): is X1's BacklashRepulsion gate effectively
UNCONDITIONAL on the R-phase engine, and what does a threat-gated alternative
restrict it to?

The gate fires when partisan out-party warmth < affect_threshold (-0.3). By the
polarized era nearly all partisans are colder than -0.3, so the gate is
practically always open — the backfire fires for ~everyone (docs: ~99.8%),
which cannot express the CONDITIONAL, threat-moderated backfire the literature
debates (Mutz 2018 threat-carrier; Combs 2023 anonymity flips it; Guess &
Coppock 2020 null on average).

This reports, at three ticks, the partisan population's:
  - frac warmth < -0.3   (current gate-open fraction)
  - mean warmth
  - frac perceived_threat > 0   (the threat-gated alternative's firing pop)
  - mean threat (over threatened)
Baseline (no intervention) — BacklashRepulsion is strength 0 in the baseline, so
warmth/threat distributions are intervention-independent at apply time.
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

from abm.pillars.schedule import run_to
from scripts.anes_preset import ANES_FULL_KWARGS
from scripts.audit.audit_lib import build_engine, _make_schedule

THRESH = -0.3
SEEDS = (0, 1, 2)
TICKS = {2010: 90, 2016: 108, 2020: 120}


def _partisan_stats(eng):
    warms, threats = [], []
    for a in eng.agents:
        p = a.state.attrs.get("party")
        if p not in (0, 1):
            continue
        aff = a.state.attrs.get("affect") or {}
        # the out-party warmth (min over out-parties — the coldest, which is what
        # the gate checks per encounter; here summarize by the out-party mean)
        ow = [v for op, v in aff.items() if op not in (p, 2)]
        if ow:
            warms.append(float(np.clip(np.mean(ow), -1, 1)))
        threats.append(float(np.clip(a.state.attrs.get("perceived_threat", 0.0), 0, 1)))
    return np.array(warms), np.array(threats)


def main():
    print("X1 BacklashRepulsion gate diagnostic — partisan population, baseline arc")
    print(f"current gate: backfire fires when out-party warmth < {THRESH}")
    print("=" * 78)
    print(f"{'year':>6} | {'frac warmth<-0.3':>16} | {'mean warmth':>11} | "
          f"{'frac threat>0':>13} | {'mean threat(thr>0)':>18}")
    print("-" * 78)
    for yr, tick in TICKS.items():
        fr_cold, mw, fr_threat, mt = [], [], [], []
        for s in SEEDS:
            eng = build_engine(seed=s, **ANES_FULL_KWARGS)
            sched = _make_schedule("full")
            for t in range(1, tick + 1):
                run_to(eng, sched, t)
            w, th = _partisan_stats(eng)
            fr_cold.append(float(np.mean(w < THRESH)))
            mw.append(float(np.mean(w)))
            fr_threat.append(float(np.mean(th > 0)))
            mt.append(float(np.mean(th[th > 0])) if np.any(th > 0) else 0.0)
        print(f"{yr:>6} | {np.mean(fr_cold):>15.1%} | {np.mean(mw):>+11.3f} | "
              f"{np.mean(fr_threat):>12.1%} | {np.mean(mt):>18.3f}")
    print("-" * 78)
    print("frac warmth<-0.3 ~ 100% -> current gate is effectively UNCONDITIONAL. "
          "frac threat>0 = the population a threat-gated backfire would fire for "
          "(Mutz/Combs conditional backfire).")


if __name__ == "__main__":
    main()
