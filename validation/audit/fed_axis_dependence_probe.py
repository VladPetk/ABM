"""Adversarial probe: does the endogenous loop DEPEND on the fed align_u axis?

Finding under test: "ActivistEliteCue freezes each party's amplification axis to
the 1986 ANES party-gap direction (align_u); the loop only amplifies MAGNITUDE
along a hard-coded fed direction and cannot DISCOVER which direction parties
sort."

Two checks:
 (A) Reproduce the static direction-check: re-label the fixed 1980 IC along
     (i) population principal axis, (ii) fed align_u, (iii) economic x-axis.
     If they agree, the fed axis ~= the population's own cleavage.
 (B) DYNAMIC dependence: run the full arc but OVERRIDE the frozen party_axis
     to the population's own principal axis (computed from the live 1980 cloud),
     and compare final party_sep to the canonical fed-axis run. If the final
     magnitude is ~unchanged, the fed direction is NOT load-bearing for the
     outcome — it is a stabilizer that coincides with the emergent axis.
"""
from __future__ import annotations

import numpy as np

from abm.core.issues import project1
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from scripts.anes_preset import ANES_FULL_KWARGS
from scripts.phase8f_lib import party_sep_metric

END_TICK = 135


def principal_axis(pos):
    c = np.cov((pos - pos.mean(0)).T)
    w, v = np.linalg.eigh(c)
    return v[:, int(np.argmax(w))]


def relabel_sep(pos, n_dem, n_rep, u):
    proj = pos @ u
    order = np.argsort(proj)
    dem = order[:n_dem]
    rep = order[len(order) - n_rep:]
    return float(np.linalg.norm(pos[rep].mean(0) - pos[dem].mean(0)))


def static_check(seed):
    eng = build_engine(seed=seed, **ANES_FULL_KWARGS)
    pos_all = eng.positions()
    party_all = np.array([a.state.attrs["party"] for a in eng.agents])
    mask = np.isin(party_all, (0, 1))
    pos = pos_all[mask]
    party = party_all[mask]
    n_dem = int((party == 0).sum())
    n_rep = int((party == 1).sum())

    u_pc = principal_axis(pos)
    rt = eng.env.attrs.get("issue_runtime")
    au = rt.get("align_u")
    d2 = np.asarray(project1(np.asarray(au, float), rt), float)
    u_au = d2 / np.linalg.norm(d2)

    pc_ang = np.degrees(np.arctan2(abs(u_pc[1]), abs(u_pc[0])))
    au_ang = np.degrees(np.arctan2(abs(u_au[1]), abs(u_au[0])))

    return {
        "baseline": party_sep_metric(eng),
        "pc": relabel_sep(pos, n_dem, n_rep, u_pc),
        "pc_ang": pc_ang,
        "au": relabel_sep(pos, n_dem, n_rep, u_au),
        "au_ang": au_ang,
        "xaxis": relabel_sep(pos, n_dem, n_rep, np.array([1.0, 0.0])),
        "u_pc": u_pc.tolist(),
        "u_au": u_au.tolist(),
    }


def dynamic_run(seed, override_axis=None):
    """Run full arc. If override_axis given (dict pid->2D unit vec), force
    env.attrs['party_axis'] to it AFTER tick 0 build (before any loop tick) and
    re-assert each tick so the canonical first-tick freeze cannot overwrite it."""
    eng = build_engine(seed=seed, **ANES_FULL_KWARGS)
    sched = build_schedule(
        faction_anchor_events=True, evidence_regrade=True, exogenous_shocks=True)
    if override_axis is not None:
        eng.env.attrs["party_axis"] = {p: list(v) for p, v in override_axis.items()}
    for t in range(1, END_TICK + 1):
        run_to(eng, sched, t)
        if override_axis is not None:
            # guard against any re-freeze (it shouldn't, axis is set, but be safe)
            eng.env.attrs["party_axis"] = {p: list(v) for p, v in override_axis.items()}
    return party_sep_metric(eng)


if __name__ == "__main__":
    print("=== STATIC direction-check (re-label fixed 1980 IC) ===")
    rows = [static_check(s) for s in range(5)]
    for k in ("baseline", "pc", "au", "xaxis", "pc_ang", "au_ang"):
        vals = [r[k] for r in rows]
        print(f"  {k:10s} mean={np.mean(vals):.4f} std={np.std(vals):.4f}")
    # angle between fed axis and population PC
    angs = []
    for r in rows:
        a = np.array(r["u_pc"]); b = np.array(r["u_au"])
        ca = abs(float(a @ b)) / (np.linalg.norm(a) * np.linalg.norm(b))
        angs.append(np.degrees(np.arccos(min(1.0, ca))))
    print(f"  angle(PC, fed_au) mean={np.mean(angs):.2f} deg")

    print("\n=== DYNAMIC dependence (final party_sep, full arc) ===")
    for seed in range(3):
        # canonical fed axis
        fed = dynamic_run(seed, override_axis=None)
        # build pop principal axis from this seed's 1980 cloud, R=+pc, D=-pc
        eng0 = build_engine(seed=seed, **ANES_FULL_KWARGS)
        pos_all = eng0.positions()
        party_all = np.array([a.state.attrs["party"] for a in eng0.agents])
        m = np.isin(party_all, (0, 1))
        u_pc = principal_axis(pos_all[m])
        # orient PC so its dot with fed axis sign matches R=+; use centroid gap to orient
        dem_c = pos_all[party_all == 0].mean(0)
        rep_c = pos_all[party_all == 1].mean(0)
        if (rep_c - dem_c) @ u_pc < 0:
            u_pc = -u_pc
        ovr = {0: (-u_pc).tolist(), 1: u_pc.tolist()}
        pc_run = dynamic_run(seed, override_axis=ovr)
        # also a deliberately WRONG axis: pure cultural y-axis to see if loop ignites differently
        ywrong = {0: [0.0, -1.0], 1: [0.0, 1.0]}
        y_run = dynamic_run(seed, override_axis=ywrong)
        print(f"  seed {seed}: fed_au={fed:.4f}  pop_PC={pc_run:.4f}  "
              f"y_axis={y_run:.4f}")
