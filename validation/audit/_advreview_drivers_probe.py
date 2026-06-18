"""Which rules drive sep? And is the warming tick the 2001 shock?"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import numpy as np
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from scripts.anes_preset import ANES_FULL_KWARGS


def macro(engine):
    pos = engine.positions()
    parties = np.array([a.state.attrs.get("party") for a in engine.agents])
    dem = pos[parties == 0]; rep = pos[parties == 1]
    sep = float(np.linalg.norm(rep.mean(axis=0) - dem.mean(axis=0)))
    warms = []
    for a in engine.agents:
        p = a.state.attrs.get("party")
        if p in (0, 1):
            aff = a.state.attrs.get("affect") or {}
            if (1 - p) in aff:
                warms.append(float(np.clip(aff[1 - p], -1, 1)))
    return sep, (float(np.mean(warms)) if warms else float("nan"))


def trajectory(**ov):
    kw = dict(ANES_FULL_KWARGS); kw.update(ov)
    eng = build_engine(seed=0, **kw)
    sched = build_schedule(
        factional_seeding=kw.get("factional_seeding", False),
        faction_anchor_events=kw.get("faction_anchor_events", True),
        evidence_regrade=kw.get("evidence_regrade", False),
        exogenous_shocks=kw.get("exogenous_shocks", False))
    S, A = [], []
    for t in range(0, 136):
        run_to(eng, sched, t)
        s, a = macro(eng); S.append(s); A.append(a)
    return np.array(S), np.array(A)


def main():
    base_s, base_a = trajectory()
    # which tick warms? year = 1980 + tick/3
    daff = np.diff(base_a)
    warm_ticks = np.where(daff > 1e-4)[0]
    for t in warm_ticks:
        print(f"affect WARMS at step {t}->{t+1}  year ~{1980 + (t+1)/3:.1f}  "
              f"delta {daff[t]:+.4f}")

    # exogenous shocks OFF -> does the warming tick disappear?
    ns_s, ns_a = trajectory(exogenous_shocks=False)
    dns = np.diff(ns_a)
    print(f"\nwith exogenous_shocks OFF: warming ticks = {int((dns>1e-4).sum())} "
          f"(largest {dns.max():+.4f})")

    # Drivers: PartyPull off, ActivistElite gain low
    pp_s, pp_a = trajectory(tier_c_party_pull_strength=0.0)
    el_s, el_a = trajectory(elite_gain=0.0)
    print(f"\nsep end:  canonical {base_s[-1]:.3f}")
    print(f"          PartyPull off (strength 0): {pp_s[-1]:.3f}  ({pp_s[-1]-base_s[-1]:+.3f})")
    print(f"          ActivistElite gain 0:       {el_s[-1]:.3f}  ({el_s[-1]-base_s[-1]:+.3f})")


if __name__ == "__main__":
    main()
