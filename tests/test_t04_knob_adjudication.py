"""T0.4 drift guards (MHV spec docs/internal/mhv_spec.md S0/T0.4).

User adjudication 2026-06-10: momentum RELOCATED to a presentation-side
EMA (engine kwarg stays, default 0.0; the canonical preset no longer sets
it); the hard IC x-cap RECALIBRATED to an ANES-anchored soft cap (the
wrong-side 1980 economic tail is thinned to the measured ANES 1980s rates
instead of clipped to zero); fj_alpha_scale kept as a tagged mechanism.

MHV S2 T2.6 (user sign-off 2026-06-10): the canonical preset flipped to
the D=7 emergent substrate, where the wrong-side tails are NATIVE to the
item-level seeding (pinned by tests/test_t21_issue_state.py) and the
soft-cap kwargs are retired from the preset. The soft-cap tests below
become **legacy-2D-path guards**: they pin the (still live) legacy
mechanism on an explicit legacy config rather than the canonical preset.
Kill candidates at the post-S4 legacy-path retirement pass.
"""
import numpy as np

import abm.pillars.historical_arc as H
from scripts.anes_preset import ANES_FULL_KWARGS

# weighted ANES 1980-1990 wrong-side rates past +-0.45
# (data/phase9_empirical/derived/respondent_coordinates.csv)
TARGET_D, TARGET_R = 0.0376, 0.0160

# The explicit legacy-2D configuration the soft-cap guards pin: the
# canonical preset as it stood pre-flip (no issue substrate, no emergent
# constraint, legacy BC, soft-cap kwargs restored).
LEGACY_2D_OVERRIDES = {
    "n_issues": None,
    "constraint_rate": 0.0,
    "constraint_resid_sigma": 0.0,
    "tier_c_bc_strength": 0.015,
    "tier_c_bc_epsilon": None,
    "tier_d_ic_partisan_x_cap": 0.45,
    "tier_d_ic_wrongside_tail_target": {0: 0.0376, 1: 0.0160},
}


def _ic_rates(n_seeds=16, **overrides):
    rd, rr = [], []
    kw = dict(ANES_FULL_KWARGS)
    kw.update(LEGACY_2D_OVERRIDES)
    kw.update(overrides)
    for seed in range(n_seeds):
        eng = H.build_engine(seed=seed, **kw)
        pos = eng.positions()
        party = np.array([a.state.attrs["party"] for a in eng.agents])
        rd.append(float((pos[party == 0, 0] > 0.45).mean()))
        rr.append(float((pos[party == 1, 0] < -0.45).mean()))
    return float(np.mean(rd)), float(np.mean(rr))


def test_preset_momentum_relocated():
    # canonical preset no longer carries momentum; engine default is off
    assert "momentum" not in ANES_FULL_KWARGS
    eng = H.build_engine(seed=0, **ANES_FULL_KWARGS)
    assert float(eng.env.attrs.get("momentum", 0.0)) == 0.0


def test_soft_cap_reproduces_anes_tail_rates():
    rd, rr = _ic_rates()
    # generous bands: 16 seeds x ~110 partisans/side -> sd ~ 0.4-0.6 pp
    assert abs(rd - TARGET_D) < 0.015, f"D tail {rd:.3%} vs target {TARGET_D:.3%}"
    assert abs(rr - TARGET_R) < 0.012, f"R tail {rr:.3%} vs target {TARGET_R:.3%}"


def test_hard_cap_path_unchanged():
    # without the target dict, the cap is still a hard truncation (0%)
    rd, rr = _ic_rates(n_seeds=6, tier_d_ic_wrongside_tail_target=None)
    assert rd == 0.0 and rr == 0.0


def test_soft_cap_requires_cap_threshold():
    # target dict without a cap threshold -> no thinning machinery, no crash
    eng = H.build_engine(
        seed=0, n_agents=80, tier_d_axis_balance=True, tier_d_anes_knobs=True,
        tier_d_ic_partisan_x_cap=None,
        tier_d_ic_wrongside_tail_target={0: 0.04, 1: 0.02},
    )
    assert eng.positions().shape[0] == 80
