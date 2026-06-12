"""T0.4 drift guards (MHV spec docs/internal/mhv_spec.md S0/T0.4).

User adjudication 2026-06-10: momentum RELOCATED to a presentation-side
EMA (engine kwarg stays, default 0.0; the canonical preset no longer sets
it); fj_alpha_scale kept as a tagged mechanism.

MHV S4 T4.6 (2026-06-12): the legacy-2D IC soft-cap guards
(test_soft_cap_*, test_hard_cap_path_unchanged) and their helpers were
RETIRED together with the soft-cap kwargs (tier_d_ic_partisan_x_cap /
tier_d_ic_wrongside_tail_target) — the canonical D=7 IC reproduces the
wrong-side econ tails natively (tests/test_t21_issue_state.py), so the cap
only ever fired on the legacy 2D path. Pre-registered at methods §5.23;
executed at the T4.6 test-retirement pass (docs/internal/test_retirement_ledger.md).
"""
import abm.pillars.historical_arc as H
from scripts.anes_preset import ANES_FULL_KWARGS


def test_preset_momentum_relocated():
    # canonical preset no longer carries momentum; engine default is off
    assert "momentum" not in ANES_FULL_KWARGS
    eng = H.build_engine(seed=0, **ANES_FULL_KWARGS)
    assert float(eng.env.attrs.get("momentum", 0.0)) == 0.0
