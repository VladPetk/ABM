"""PROTOTYPE (sandbox, no committed change): add an ECONOMIC common-mode channel.

The cultural common-mode channel (cultural_common_mode, shipped d97048f) fixed the
cultural axis. The from-scratch ANES+GSS battery still shows the ECONOMIC center of
mass pinned ~0 the whole arc, while ANES (cross-checked by GSS helppoor+eqwlth)
rises to ~+0.15 in the mid-90s then declines to ~-0.05 by 2024 (non-monotone).
Same architecture gap as the cultural axis: a differential (sorting) channel but no
common-mode (society-wide level) channel on econ. Cohort replacement is monotone and
cannot make the non-monotone hump -> needs an EXOGENOUS thermostatic policy-mood
forcing (Erikson-MacKuen-Stimson; Wlezien thermostat).

This prototype mirrors exp_commonmode.py but on the ECON (x) axis, snapping the econ
common mode to a candidate m_econ(t) each tick (rigid translation of the issue
vector -> sorting-invariant). It compares TWO candidate exogenous forcings and grades
econ COM, econ gap (F3), R-in-LL (F5), party_sep, corr against ANES. Built ON TOP of
the canonical kwargs (which already include the cultural common-mode channel).

We do NOT replay the ANES econ series. Candidate (A) is the real downloaded Stimson
Annual Policy Mood via a single affine map. Candidate (B) is a parsimonious
thermostatic curve whose inflection YEARS are policy events, corroborated (not driven)
by Stimson's direction.
"""
import sys, json
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.anes_preset import ANES_FULL_KWARGS
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to

HERE = Path(__file__).resolve().parent
YEARS = [1986, 1992, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024]
# ANES partisan econ center of mass (validation/anchors_anes.json, n-weighted).
ANES_ECON = {1986: 0.065, 1992: 0.075, 1996: 0.146, 2000: 0.106, 2004: 0.046,
             2008: 0.016, 2012: 0.095, 2016: 0.090, 2020: -0.025, 2024: -0.050}
# ANES R/D econ gap (F3) and R-in-LL (F5) anchors.
ANES_ECON_D = {1986: -0.074, 1992: -0.120, 1996: -0.070, 2000: -0.085, 2004: -0.220,
               2008: -0.217, 2012: -0.178, 2016: -0.266, 2020: -0.418, 2024: -0.400}
ANES_ECON_R = {1986: 0.246, 1992: 0.288, 1996: 0.375, 2000: 0.303, 2004: 0.305,
               2008: 0.367, 2012: 0.443, 2016: 0.436, 2020: 0.420, 2024: 0.360}
ANES_R_LL = {1986: 0.118, 1992: 0.091, 2000: 0.082, 2008: 0.109, 2016: 0.053, 2024: 0.084}

MOOD = {int(k): v for k, v in json.load(open(HERE / "data/stimson_mood_annual.json")).items()}
_my = sorted(MOOD)


def stimson_mood(year):
    return float(np.interp(year, _my, [MOOD[y] for y in _my]))


# ---- Candidate A: real Stimson, single affine map econ = a - b*mood ----
# (a, b) chosen so the series spans the robust endpoints: +0.09 at the mid-90s
# trough-of-mood (1995, mood 59.0) and -0.05 at 2024 (mood 64.3). b is the single
# gain; a is the centering constant. This is the *literal exogenous* candidate.
_b = (0.09 - (-0.05)) / (64.259 - 59.018)
_a = 0.09 + 59.018 * _b


def m_econ_stimson(year):
    return _a - _b * stimson_mood(year)


# ---- Candidate B: parsimonious thermostatic curve (Stimson-corroborated) ----
# Inflection YEARS anchored to the documented policy timeline; relative heights
# follow the thermostatic narrative; ONE amplitude A is the fitted scalar.
#   1980 Reagan tax-revolt baseline (mildly conservative)
#   1996 welfare-reform / Gingrich peak  ("end of big government")
#   2012 still right-of-center post-crisis, realignment not yet matured
#   2024 post-2008 thermostatic leftward reaction matured (redistribution salience)
# Corroborated by real Stimson: mood turns conservative INTO the mid-90s
# (69.1@1991 -> 59.0@1995) and liberal THROUGH the 2010s (54.8@2012 -> 65.9@2020).
_ANCHORS_YR = [1980, 1996, 2012, 2024]
_ANCHORS_G = [0.30, 1.00, 0.45, -0.55]   # unit-amplitude shape


def m_econ_curve(year, amp):
    return amp * float(np.interp(year, _ANCHORS_YR, _ANCHORS_G))


def build():
    kw = dict(ANES_FULL_KWARGS)            # cultural common-mode already ON here
    eng = build_engine(seed=0, **kw)
    sched = build_schedule(
        factional_seeding=kw.get("factional_seeding", False),
        faction_anchor_events=kw.get("faction_anchor_events", True),
        evidence_regrade=kw.get("evidence_regrade", False),
        exogenous_shocks=kw.get("exogenous_shocks", False))
    return eng, sched


def econ_shift(eng, target):
    """Rigid ECON-axis frame shift so partisan econ mean -> target, on the issue
    vector (truth on the n_issues substrate). project(lift([d,0]))==[d,0] -> a rigid
    2D econ translation (sorting-invariant)."""
    from abm.core.issues import lift, project1
    rt = eng.env.attrs.get("issue_runtime")
    party = np.array([a.state.attrs.get("party") for a in eng.agents])
    pos = np.array([a.state.ideology for a in eng.agents])
    m = (party == 0) | (party == 1)
    delta = float(target - pos[m, 0].mean())
    bump = lift(np.array([delta, 0.0]), rt) if rt is not None else None
    for a in eng.agents:
        if rt is not None:
            v = a.state.attrs.get("issues")
            if v is not None:
                a.state.attrs["issues"] = np.clip(v + bump, -1.0, 1.0)
                av = a.state.attrs.get("anchor_issues")
                if av is not None:
                    a.state.attrs["anchor_issues"] = np.clip(av + bump, -1.0, 1.0)
                a.state.ideology = project1(a.state.attrs["issues"], rt)
        else:
            a.state.ideology[0] += delta
        for key in ("anchor", "party_cue"):
            vv = a.state.attrs.get(key)
            if vv is not None and hasattr(vv, "__len__") and len(vv) == 2:
                vv[0] += delta
    parties = eng.env.attrs.get("parties") or {}
    for pid in parties:
        parties[pid] = np.asarray(parties[pid], dtype=float)
        parties[pid][0] += delta


def metrics(eng):
    party = np.array([a.state.attrs.get("party") for a in eng.agents])
    pos = np.array([a.state.ideology for a in eng.agents])
    D, R = pos[party == 0], pos[party == 1]
    m = (party == 0) | (party == 1)
    return {"econ_com": float(pos[m, 0].mean()),
            "D_econ": float(D[:, 0].mean()), "R_econ": float(R[:, 0].mean()),
            "party_sep": float(np.hypot(*(R.mean(0) - D.mean(0)))),
            "corr": float(np.corrcoef(pos[m, 0], pos[m, 1])[0, 1]),
            "R_LL": float(np.mean((R[:, 0] <= 0) & (R[:, 1] <= 0)))}


def run(mode, amp=0.09):
    eng, sched = build()
    rec = {}
    for t in range(1, 136):
        run_to(eng, sched, t)
        yr_f = 1980 + t / 3
        if mode == "stimson":
            econ_shift(eng, m_econ_stimson(yr_f))
        elif mode == "curve":
            econ_shift(eng, m_econ_curve(yr_f, amp))
        yr = int(round(yr_f))
        if yr in YEARS and yr not in rec:
            rec[yr] = metrics(eng)
    return rec


base = run("base")
stim = run("stimson")
curv = run("curve", amp=0.09)

print("=== ECON center of mass (target = ANES partisan econ COM) ===")
print(f"{'yr':>5} {'ANES':>7} {'base':>8} {'stimson':>9} {'curve':>8}")
for yr in YEARS:
    print(f"{yr:>5} {ANES_ECON[yr]:>+7.3f} {base[yr]['econ_com']:>+8.3f} "
          f"{stim[yr]['econ_com']:>+9.3f} {curv[yr]['econ_com']:>+8.3f}")

print("\n=== ECON gap R-D (F3): ANES vs base vs curve ===")
print(f"{'yr':>5} {'ANES_gap':>9} {'base_gap':>9} {'curve_gap':>9}")
for yr in YEARS:
    ag = ANES_ECON_R[yr] - ANES_ECON_D[yr]
    print(f"{yr:>5} {ag:>9.3f} {base[yr]['R_econ']-base[yr]['D_econ']:>9.3f} "
          f"{curv[yr]['R_econ']-curv[yr]['D_econ']:>9.3f}")

print("\n=== Republican wrong-quadrant LL (F5): base vs stimson vs curve vs ANES ===")
for yr in sorted(ANES_R_LL):
    print(f"{yr:>5}: base {base[yr]['R_LL']:.3f}  stimson {stim[yr]['R_LL']:.3f}  "
          f"curve {curv[yr]['R_LL']:.3f}  ANES {ANES_R_LL[yr]:.3f}")

print("\n=== SORTING preserved? party_sep / corr (base / curve) ===")
for yr in YEARS:
    print(f"{yr:>5} sep {base[yr]['party_sep']:.3f}/{curv[yr]['party_sep']:.3f}  "
          f"corr {base[yr]['corr']:.3f}/{curv[yr]['corr']:.3f}")

# econ center error summary (mid-period 1994-2004 emphasis)
def mid_err(rec):
    e = [rec[y]['econ_com'] - ANES_ECON[y] for y in YEARS if 1994 <= y <= 2004]
    return np.mean(e)
print(f"\nmid-period(94-04) econ COM error: base {mid_err(base):+.3f}  "
      f"stimson {mid_err(stim):+.3f}  curve {mid_err(curv):+.3f}")
