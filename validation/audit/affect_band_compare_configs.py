"""Compare affect trajectory across config layers to isolate what pushed
affect out of band. READ-ONLY."""
import sys, os, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import numpy as np
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from scripts import anes_preset as ap

bands = json.load(open("data/phase9_empirical/derived/affect_bands.json"))["bands"]
tick_year = {30:"1990", 60:"2000", 90:"2010", 120:"2020", 135:"2025"}

def mean_aff(eng):
    vals=[]
    for a in eng.agents:
        p=a.state.attrs.get("party")
        if p not in (0,1): continue
        aff=a.state.attrs.get("affect") or {}
        w=aff.get(1-p)
        if w is not None: vals.append(float(np.clip(w,-1,1)))
    return float(np.mean(vals)) if vals else None

def run_cfg(kw, seed=0):
    eng=build_engine(seed=seed, **kw)
    sched=build_schedule(
        factional_seeding=kw.get("factional_seeding",False),
        faction_anchor_events=kw.get("faction_anchor_events",True),
        evidence_regrade=kw.get("evidence_regrade",False),
        exogenous_shocks=kw.get("exogenous_shocks",False))
    res={}
    for t in (30,60,90,120,135):
        run_to(eng,sched,t); res[t]=mean_aff(eng)
    return res

configs = {
 "ENDOGENOUS (pre-common-mode E5)": ap.ANES_FULL_ENDOGENOUS_KWARGS,
 "+CULTURAL common-mode": ap.ANES_FULL_COMMONMODE_KWARGS,
 "+ECON common-mode (CANONICAL)": ap.ANES_FULL_COMMONMODE_ECON_KWARGS,
}
out = {name: run_cfg(kw) for name,kw in configs.items()}
print(f"{'year':>5} {'band':>20} " + " ".join(f"{n[:22]:>23}" for n in configs))
for t,yr in tick_year.items():
    b=bands[yr]["band"]
    cells=[]
    for n in configs:
        v=out[n][t]; inb=b[0]<=v<=b[1]
        cells.append(f"{v:+.4f}({'Y' if inb else 'N'})")
    print(f"{yr:>5} [{b[0]:+.3f},{b[1]:+.3f}] " + " ".join(f"{c:>23}" for c in cells))
