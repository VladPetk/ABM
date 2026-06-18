"""Probe (one-off): is X2 inert because the knob is mis-wired, and does zeroing
the LIVE channel produce an earned (~null) result rather than a spurious effect?

Three conditions at release 2000 (tick 60), Δ vs same-seed control, measured at
+10y (tick 90) and 2025 (tick 135), 5 seeds:
  control       — no intervention
  X2-current    — the shipped lever: BoundedConfidenceInfluence.affect_weight = 0
                  (a field the rule shadows with env.attrs['bc_affect_weight'])
  X2-fixed      — zero the LIVE channel: MediaPenetrationSeries.bc_aw_per_adoption = 0
                  + env.attrs['bc_affect_weight'] = 0 (kills the social-media -> BC
                  homophilous affect amplifier, which is what "fix the algorithm" means)

Expectation: X2-current ~ exactly 0 (mis-wired no-op); X2-fixed small/null
(Meta-2020 earned null) — NOT a large depolarization.
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

from abm.pillars.intervention import apply_intervention
from abm.pillars.interventions_phase6 import INTERVENTIONS_PHASE6
from abm.pillars.schedule import run_to
from scripts.anes_preset import ANES_FULL_KWARGS
from scripts.phase8f_lib import affective_polarization, party_sep_metric
from scripts.audit.audit_lib import (
    build_engine, _make_schedule, _find_rule, END_TICK,
)

X2 = next(iv for iv in INTERVENTIONS_PHASE6 if iv.id == "X2_fix_algorithm")
# Sweep release decades: at 2000 the social-media->BC channel is still ~0 (no
# adoption yet), so removing it can't show anything. 2010/2020 fire it when the
# channel is live and near peak — the channel's real macro impact, if any.
RELEASES = (60, 90, 120)
SEEDS = (0, 1, 2, 3, 4)


def _apply_fixed_x2(eng):
    """Candidate faithful X2: kill the live social-media -> BC affect channel."""
    mp = _find_rule(eng, "MediaPenetrationSeries")
    if mp is not None and hasattr(mp, "bc_aw_per_adoption"):
        mp.bc_aw_per_adoption = 0.0
    eng.env.attrs["bc_affect_weight"] = 0.0
    # also zero the rule attr for the no-env-fed fallback / pillar parity
    bc = _find_rule(eng, "BoundedConfidenceInfluence")
    if bc is not None and hasattr(bc, "affect_weight"):
        bc.affect_weight = 0.0


def _run(seed, cond, release):
    eng = build_engine(seed=seed, **ANES_FULL_KWARGS)
    sched = _make_schedule("full")
    h = min(release + 30, END_TICK)
    snaps = {}
    for t in range(1, END_TICK + 1):
        run_to(eng, sched, t)
        if t == release:
            if cond == "current":
                apply_intervention(eng, X2)
            elif cond == "fixed":
                _apply_fixed_x2(eng)
        if t in (h, END_TICK):
            snaps[t] = (float(affective_polarization(eng.agents)),
                        float(party_sep_metric(eng)))
    return snaps, h


def main():
    print(f"X2 channel probe — release sweep {RELEASES}, {len(SEEDS)} seeds")
    print("Delta vs control: aff (+ = warmer = helpful), sep (- = closer = helpful)")
    print("bc_affect_weight ramps with social-media adoption (~0 pre-2008, peak ~2012).")
    print("=" * 78)
    for release in RELEASES:
        yr = 1980 + release // 3
        base = {}
        for s in SEEDS:
            base[s], h = _run(s, "control", release)
        print(f"\n-- release {yr} (tick {release}), +10y horizon = tick {h} --")
        for cond in ("current", "fixed"):
            runs = {}
            for s in SEEDS:
                runs[s], _ = _run(s, cond, release)
            for t, lab in ((h, "+10y"), (END_TICK, "2025")):
                daff = np.mean([runs[s][t][0] - base[s][t][0] for s in SEEDS])
                dsep = np.mean([runs[s][t][1] - base[s][t][1] for s in SEEDS])
                print(f"  X2-{cond:<8} @ {lab:<5} | dAff {daff:>+8.4f} | dSep {dsep:>+8.4f}")
    print("=" * 78)
    print("current ~0 everywhere -> mis-wired no-op. fixed ~0 even at 2010/2020 -> "
          "channel genuinely negligible (earned null, faithful to media paradox / "
          "Meta-2020). fixed sizable -> channel matters; magnitude question.")


if __name__ == "__main__":
    main()
