"""Forcing-ledger scratch check (peer review, READ-ONLY analysis).
Quantify: (1) does the econ common-mode channel set the partisan econ
center-of-mass directly to the fed curve? (2) is party_sep invariant to it?
Run 1 seed, 2 configs (econ channel ON vs OFF), short arc to ~2 minutes.
"""
import numpy as np
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from scripts.anes_preset import (ANES_FULL_KWARGS, ANES_FULL_COMMONMODE_KWARGS)
from abm.rules.cultural_common_mode import economic_mood_offset

def run(kw, label, ticks=(72,135)):
    eng = build_engine(seed=0, **dict(kw))
    sched = build_schedule(faction_anchor_events=True, evidence_regrade=True, exogenous_shocks=True)
    out={}
    for t in range(1, max(ticks)+1):
        run_to(eng, sched, t)
        if t in ticks:
            pos=eng.positions(); parties=np.array([a.state.attrs["party"] for a in eng.agents])
            mp = parties!=2  # partisans
            econ_com = float(pos[mp,0].mean())
            cult_com = float(pos[mp,1].mean())
            sep = float(np.linalg.norm(pos[parties==0].mean(0)-pos[parties==1].mean(0)))
            year = 1980 + t/3
            out[t]=(year, econ_com, cult_com, sep, economic_mood_offset(year))
    return out, label

for kw,label in [(ANES_FULL_KWARGS,"ECON_ON (canonical)"),(ANES_FULL_COMMONMODE_KWARGS,"ECON_OFF")]:
    o,l=run(kw,label)
    print(f"=== {l} ===")
    for t,(yr,e,c,s,mood) in o.items():
        print(f"  t={t} yr={yr:.0f}  econ_com={e:+.4f}  cult_com={c:+.4f}  party_sep={s:.4f}  fed_mood={mood:+.4f}")
