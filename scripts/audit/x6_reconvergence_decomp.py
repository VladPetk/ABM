"""Diagnostic (one-off): decompose WHY X6's affect effect re-converges to the
no-intervention baseline by 2025.

User observation (2026-06-18): X6 "Shared neighborhoods/workplaces" released in
2000 shows a clear out-party-warmth gain at +10y, but by 2025 the branch lands
on ~the same out-party warmth as no intervention. Two candidate causes:
  (A) exogenous forcings (elite/media/coupling/events) re-drive the cooling and
      drown out the knob change;
  (B) endogenous self-regularization — the R7 affect rest-state (mean reversion
      toward -0.30) + cohort replacement (treated agents turn over) wash out a
      one-time reset.

Design: for each regime, run control vs X6 (applied at the release tick) as two
same-seed full trajectories to 2025 (exactly how phase10 measures Δ), capture
out-party affect each tick, report Δaff(t) = X6 - control at the immediate post,
the +30t (~10y) measurement horizon, and 2025.

Regimes:
  shipped      — the canonical R-phase engine + full schedule (what the demo shows)
  rest-off     — affect_rest_rate = 0  (kills R7 mean reversion)
  cohort-off   — cohort_replacement_rate = 0  (treated agents never turn over)
  frozen       — ALL forcings clamped at 1980 + empty schedule (no events/drift)

If Δaff washes out under `frozen` too, the cause is endogenous (B). If it
PERSISTS under `frozen` but washes out `shipped`, forcings are the cause (A).
`rest-off` / `cohort-off` attribute the endogenous share.

NOT committed; run with .venv/Scripts/python.exe scripts/audit/x6_reconvergence_decomp.py
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
    build_engine, _apply_freeze, _capture_baseline, _make_schedule, END_TICK,
)

X6 = next(iv for iv in INTERVENTIONS_PHASE6 if iv.id == "X6_shared_institutions")
RELEASE = 60          # 2000
HORIZON = RELEASE + 30  # 2010 — the phase10 measurement horizon
SEEDS = (0, 1, 2, 3, 4)

ALL_FREEZE = {"elite_drift", "identity_sorting", "coupling", "party_k",
              "social_media", "data_fed_inputs", "endogenous_loop"}

REGIMES = {
    "shipped":    dict(overrides={}, freeze=None, mode="full"),
    "rest-off":   dict(overrides={"affect_rest_rate": 0.0}, freeze=None, mode="full"),
    "cohort-off": dict(overrides={"cohort_replacement_rate": 0.0}, freeze=None, mode="full"),
    "frozen":     dict(overrides={}, freeze=ALL_FREEZE, mode="empty"),
}


def _traj(seed, overrides, freeze, mode, apply_x6):
    kwargs = dict(ANES_FULL_KWARGS)
    kwargs.update(overrides or {})
    eng = build_engine(seed=seed, **kwargs)
    sched = _make_schedule(mode)
    base = _capture_baseline(eng) if freeze else None
    if freeze:
        _apply_freeze(eng, freeze, base)
    aff, sep = [], []
    for t in range(0, END_TICK + 1):
        run_to(eng, sched, t)
        if freeze:
            _apply_freeze(eng, freeze, base)
        if apply_x6 and t == RELEASE:
            apply_intervention(eng, X6)
        aff.append(float(affective_polarization(eng.agents)))
        sep.append(float(party_sep_metric(eng)))
    return np.array(aff), np.array(sep)


def main():
    print("=" * 92)
    print(f"X6 re-convergence decomposition — release tick {RELEASE} (2000), "
          f"{len(SEEDS)} seeds, to 2025")
    print("Δaff = X6 - control (positive = warmer = helpful). "
          "out-party warmth in [-1,1].")
    print("=" * 92)
    hdr = (f"{'regime':<11} | {'Δaff@rel+1':>10} | {'Δaff@+30t(2010)':>15} | "
           f"{'Δaff@2025':>10} | {'retained%':>9} | {'Δsep@2025':>10}")
    print(hdr)
    print("-" * len(hdr))
    out = {}
    for name, cfg in REGIMES.items():
        d_imm, d_h, d_end, d_sep_end = [], [], [], []
        for s in SEEDS:
            ca, cs = _traj(s, cfg["overrides"], cfg["freeze"], cfg["mode"], False)
            xa, xs = _traj(s, cfg["overrides"], cfg["freeze"], cfg["mode"], True)
            da, ds = xa - ca, xs - cs
            d_imm.append(da[RELEASE])        # immediately after the reset
            d_h.append(da[HORIZON])          # +10y (measurement horizon)
            d_end.append(da[END_TICK])       # 2025
            d_sep_end.append(ds[END_TICK])
        m_imm, m_h, m_end = np.mean(d_imm), np.mean(d_h), np.mean(d_end)
        retained = (m_end / m_imm * 100.0) if abs(m_imm) > 1e-6 else float("nan")
        print(f"{name:<11} | {m_imm:>+10.3f} | {m_h:>+15.3f} | {m_end:>+10.3f} | "
              f"{retained:>8.0f}% | {np.mean(d_sep_end):>+10.3f}")
        out[name] = dict(imm=m_imm, h=m_h, end=m_end, retained=retained)
    print("-" * len(hdr))
    print("\nReading:")
    print("  • 'retained%' = how much of the immediate post-reset warming survives to 2025.")
    print("  • frozen retains  -> washout is ENDOGENOUS (rest-state/cohort), not forcings.")
    print("  • frozen persists -> forcings re-drive the cooling (forcing-override).")
    print("  • rest-off vs cohort-off vs shipped attribute the endogenous share.")


if __name__ == "__main__":
    main()
