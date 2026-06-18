"""Test the load-bearing 'media-diet pulls inward' claim that the events-brake
attribution rests on (methods.md §5.14). Compute, per partisan agent in the
canonical build at several years, the agent's media diet target vs (a) the
agent's own position and (b) the party centroid. If the diet target sits
INWARD of the party centroid, media is a centripetal brake; if OUTWARD, it
is a centrifugal (polarizing) force.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import numpy as np
from abm.pillars.historical_arc import build_engine
from scripts.anes_preset import ANES_FULL_KWARGS
from abm.core.outlets import diet_target

def report(engine, year):
    outlets = engine.env.attrs["outlets"]
    parties = np.array([a.state.attrs.get("party") for a in engine.agents])
    pos = engine.positions()
    for p, lbl in [(0, "Dem"), (1, "Rep")]:
        idx = np.where(parties == p)[0]
        if len(idx) == 0:
            continue
        centroid = pos[idx].mean(axis=0)
        targets = []
        for i in idx:
            diet = engine.agents[i].state.attrs.get("media_diet")
            if diet:
                targets.append(diet_target(diet, outlets))
        targets = np.array(targets)
        mean_target = targets.mean(axis=0)
        # |target| vs |centroid|: inward means target closer to 0 than centroid
        print(f"  {year} {lbl}: centroid=({centroid[0]:+.3f},{centroid[1]:+.3f}) "
              f"|c|={np.linalg.norm(centroid):.3f}  "
              f"diet_target=({mean_target[0]:+.3f},{mean_target[1]:+.3f}) "
              f"|t|={np.linalg.norm(mean_target):.3f}  "
              f"{'INWARD' if np.linalg.norm(mean_target) < np.linalg.norm(centroid) else 'OUTWARD'}")

def main():
    eng = build_engine(seed=0, **ANES_FULL_KWARGS)
    cps = {0:1980, 60:2000, 90:2010, 120:2020, 135:2025}
    for t in range(136):
        if t in cps:
            report(eng, cps[t])
        if t < 135:
            eng.step()

if __name__ == "__main__":
    main()
