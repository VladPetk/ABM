"""Score shipped affect trajectory vs grounded ANES affect bands.
Single seed (web ships seed 0) + a few seeds for spread. READ-ONLY."""
import sys, os, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import numpy as np
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from scripts.anes_preset import ANES_FULL_KWARGS

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

def run_seed(seed):
    eng=build_engine(seed=seed, **ANES_FULL_KWARGS)
    sched=build_schedule(
        factional_seeding=ANES_FULL_KWARGS.get("factional_seeding",False),
        faction_anchor_events=ANES_FULL_KWARGS.get("faction_anchor_events",True),
        evidence_regrade=ANES_FULL_KWARGS.get("evidence_regrade",False),
        exogenous_shocks=ANES_FULL_KWARGS.get("exogenous_shocks",False))
    res={}
    for t in (30,60,90,120,135):
        run_to(eng,sched,t)
        res[t]=mean_aff(eng)
    return res

seeds=[0,1,2]
allres={s:run_seed(s) for s in seeds}
print("Grounded ANES affect bands vs shipped engine:")
print(f"{'year':>5} {'band':>20} {'seed0':>8} {'seed1':>8} {'seed2':>8} {'ens-mean':>9} {'in-band?':>9}")
for t,yr in tick_year.items():
    b=bands[yr]["band"]
    s0=allres[0][t]; s1=allres[1][t]; s2=allres[2][t]
    ens=np.mean([s0,s1,s2])
    inb = b[0]<=ens<=b[1]
    s0inb = b[0]<=s0<=b[1]
    print(f"{yr:>5} [{b[0]:+.3f},{b[1]:+.3f}] {s0:+.4f} {s1:+.4f} {s2:+.4f} {ens:+.4f}  ens={'Y' if inb else 'N'} s0={'Y' if s0inb else 'N'}")
