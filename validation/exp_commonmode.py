"""PROTOTYPE (sandbox, no committed change): add a COMMON-MODE cultural channel.

Concept: the engine only has a differential (sorting) channel; the cultural
center is pinned to the symmetric elite midpoint (~0). We add a rigid common-mode
cultural-frame shift so the population's cultural LEVEL can track a societal
trajectory m(t), while the differential (sorting) is untouched.

Test P1 (channel viability): snap the common mode to the empirical target each
tick (rigid translation of positions + anchors + cues + elite centroids together,
so no rule fights it). Then check: does F0/F5 correct AND are the sorting metrics
(party_sep, R-D cult gap, econ-cult correlation) preserved? If yes, the
architecture supports the fix and we can make m(t) emergent (P2, separate).
"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.anes_preset import ANES_FULL_KWARGS
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to

YEARS = [1986, 1992, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024]
ANES_CULT = {1986: 0.103, 1992: 0.102, 1996: 0.216, 2000: 0.217, 2004: 0.128,
             2008: 0.089, 2012: 0.119, 2016: 0.043, 2020: -0.052, 2024: -0.057}
ANES_R_LL = {1986: 0.118, 1992: 0.091, 2000: 0.082, 2008: 0.109, 2016: 0.053, 2024: 0.084}
# linear-interpolatable target m(t) by year (clamp outside)
_xs = sorted(ANES_CULT)
def m_target(year):
    return float(np.interp(year, _xs, [ANES_CULT[y] for y in _xs]))


def build():
    kw = dict(ANES_FULL_KWARGS)
    eng = build_engine(seed=0, **kw)
    sched = build_schedule(
        factional_seeding=kw.get("factional_seeding", False),
        faction_anchor_events=kw.get("faction_anchor_events", True),
        evidence_regrade=kw.get("evidence_regrade", False),
        exogenous_shocks=kw.get("exogenous_shocks", False))
    return eng, sched


def common_mode_shift(eng, year):
    """Rigid cultural-frame shift so partisan mean -> m(year), applied to the
    ISSUE vector (the truth on the n_issues substrate) so it persists through the
    per-tick re-projection. project(lift([0,d]))==[0,d], so this is exactly a
    rigid 2D cultural translation -> sorting-invariant."""
    from abm.core.issues import lift, project1
    rt = eng.env.attrs.get("issue_runtime")
    party = np.array([a.state.attrs.get("party") for a in eng.agents])
    pos = np.array([a.state.ideology for a in eng.agents])
    m = (party == 0) | (party == 1)
    delta = m_target(year) - pos[m, 1].mean()
    bump = lift(np.array([0.0, delta]), rt) if rt is not None else None
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
            a.state.ideology[1] += delta
        for key in ("anchor", "party_cue"):
            vv = a.state.attrs.get(key)
            if vv is not None and hasattr(vv, "__len__") and len(vv) == 2:
                vv[1] += delta
    parties = eng.env.attrs.get("parties") or {}
    for pid in parties:
        parties[pid] = np.asarray(parties[pid], dtype=float)
        parties[pid][1] += delta


def metrics(eng):
    party = np.array([a.state.attrs.get("party") for a in eng.agents])
    pos = np.array([a.state.ideology for a in eng.agents])
    D, R = pos[party == 0], pos[party == 1]
    m = (party == 0) | (party == 1)
    sep = float(np.hypot(*(R.mean(0) - D.mean(0))))
    cultgap = float(R[:, 1].mean() - D[:, 1].mean())
    corr = float(np.corrcoef(pos[m, 0], pos[m, 1])[0, 1])
    return {"cult_com": float(pos[m, 1].mean()), "party_sep": sep, "cult_gap": cultgap,
            "corr": corr, "R_LL": float(np.mean((R[:, 0] <= 0) & (R[:, 1] <= 0)))}


def run(apply_cm):
    eng, sched = build()
    rec = {}
    for t in range(1, 136):
        run_to(eng, sched, t)
        if apply_cm:
            common_mode_shift(eng, 1980 + t / 3)
        yr = int(round(1980 + t / 3))
        if yr in YEARS and yr not in rec:
            rec[yr] = metrics(eng)
    return rec


base = run(False)
cm = run(True)

print("=== cultural center of mass (target = ANES) ===")
print(f"{'yr':>5} {'ANES':>7} {'base':>8} {'common-mode':>12}")
for yr in YEARS:
    print(f"{yr:>5} {ANES_CULT[yr]:>7.3f} {base[yr]['cult_com']:>8.3f} {cm[yr]['cult_com']:>12.3f}")

print("\n=== SORTING preserved? party_sep / cult_gap / corr (base vs common-mode) ===")
print(f"{'yr':>5} {'sep b/cm':>16} {'cultgap b/cm':>18} {'corr b/cm':>16}")
for yr in YEARS:
    print(f"{yr:>5} {base[yr]['party_sep']:>7.3f}/{cm[yr]['party_sep']:<7.3f} "
          f"{base[yr]['cult_gap']:>8.3f}/{cm[yr]['cult_gap']:<8.3f} "
          f"{base[yr]['corr']:>7.3f}/{cm[yr]['corr']:<7.3f}")

print("\n=== Republican wrong-quadrant (LL) — base vs common-mode vs ANES ===")
for yr in sorted(ANES_R_LL):
    print(f"{yr:>5}: base {base[yr]['R_LL']:.3f}  common-mode {cm[yr]['R_LL']:.3f}  ANES {ANES_R_LL[yr]:.3f}")
