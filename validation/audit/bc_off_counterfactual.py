"""Counterfactual: how much does BoundedConfidenceInfluence actually change the
shipped trajectory? Compare canonical vs BC-strength-0, on key macro metrics.

If BC is a live convergence force, zeroing it should visibly change the arc.
If it's effectively inert (the T0.6 'dead channel' finding), the endpoint
should be ~unchanged.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import numpy as np
from abm.pillars.historical_arc import build_engine
from scripts.anes_preset import ANES_FULL_KWARGS

def macro(engine):
    pos = engine.positions()
    parties = np.array([a.state.attrs.get("party") for a in engine.agents])
    dem = pos[parties == 0]
    rep = pos[parties == 1]
    sep = float(np.linalg.norm(rep.mean(axis=0) - dem.mean(axis=0)))
    # within-party SD on x
    wp_sd_x = float(np.mean([dem[:,0].std(), rep[:,0].std()]))
    # pooled mean |pairwise issue correlation| as a constraint proxy on ideology axes
    var = float(pos.var(axis=0).mean())
    return dict(sep=sep, wp_sd_x=wp_sd_x, var=var)

def run(bc_strength):
    kw = dict(ANES_FULL_KWARGS)
    kw["tier_c_bc_strength"] = bc_strength
    eng = build_engine(seed=0, **kw)
    eng.run(135)
    return macro(eng)

def main():
    base = run(0.03)     # canonical
    off  = run(0.0)      # BC disabled
    hi   = run(0.12)     # BC 4x stronger
    print("metric        canonical(0.03)   BC-off(0.0)    BC-4x(0.12)   off-vs-canon  4x-vs-canon")
    for k in base:
        b, o, h = base[k], off[k], hi[k]
        print(f"{k:<12}  {b:>12.4f}   {o:>12.4f}   {h:>12.4f}   "
              f"{(o-b):>+10.4f}   {(h-b):>+10.4f}")

if __name__ == "__main__":
    main()
