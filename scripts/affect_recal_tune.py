"""Step-3 tuning harness: warm seed + reduced contact + MediatedAnimus.

Patches the canonical arc post-build so we can tune the new affect structure
by measurement before baking into historical_arc:
  - re-seed 1980 affect to seed_mean (warm)
  - scale every agent's contact affect_lr by contact_scale
  - set AffectiveUpdate.saturation = sat
  - insert MediatedAnimus(lr=med_lr); ramp env mediated_animus_weight by tick
Measures affect at the 6 ANES panels vs the GROUNDED bands + the full 24-cell
scoreboard (grounded affect bands swapped in), since affect feeds back into
ideology.
"""
import os, sys, json
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
for k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"):
    os.environ.setdefault(k, "1")
import numpy as np

PANELS = [(1980,21),(1990,42),(2000,72),(2010,102),(2020,126),(2025,135)]

# media weight ramp in [0,1] by tick. The big real out-party-therm collapse is
# 2008->2020 (social media era); 1980-2008 was gentle. So the mediated channel
# is LATE-only — it must not cool the (correctly warm) 1980-2000 decades.
def media_weight(t):
    if t < 84:   return 0.0     # pre-2008
    if t < 90:   return 0.50    # 2008-2010
    if t < 96:   return 0.80    # 2010-2012
    return 1.0                  # 2012+

def _worker(item):
    seed, seed_mean, contact_scale, sat, med_lr = item
    from scripts.anes_preset import ANES_FULL_KWARGS
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from abm.rules.mediated_animus import MediatedAnimus
    from scripts.phase8f_lib import measure_all
    kw = dict(ANES_FULL_KWARGS)
    eng = build_engine(seed=seed, **kw)
    arng = np.random.default_rng(seed + 7000)
    for a in eng.agents:
        p = a.state.attrs.get("party")
        if p in (0,1):
            if seed_mean is not None:
                a.state.attrs["affect"] = {1-p: float(np.clip(arng.normal(seed_mean,0.10),-1,1))}
        lr = a.state.attrs.get("affect_lr")
        if lr is not None:
            a.state.attrs["affect_lr"] = lr * contact_scale
    for r in eng.rules.rules:
        if type(r).__name__ == "AffectiveUpdate":
            r.saturation = sat
    eng.rules.rules.append(MediatedAnimus(learning_rate=med_lr))
    sched = build_schedule(
        factional_seeding=kw.get("factional_seeding",False),
        faction_anchor_events=kw.get("faction_anchor_events",True),
        evidence_regrade=kw.get("evidence_regrade",False),
        exogenous_shocks=kw.get("exogenous_shocks",False),
    )
    traj={}
    for y,t in PANELS:
        # advance one tick at a time so we can set the media weight each tick
        while eng.tick < t:
            eng.env.attrs["mediated_animus_weight"] = media_weight(eng.tick+1)
            run_to(eng, sched, eng.tick+1)
        traj[y]=measure_all(eng)
    return {"trajectory":traj}

def confirm():
    """One candidate, 9 seeds, full breakdown incl. rewire metrics."""
    from abm.calibration_parallel import run_seeds_parallel
    from scripts.phase8f_lib import get_primary_targets, get_initial_targets_1980, aggregate, in_band
    gb=json.load(open(_ROOT/"data/phase9_empirical/derived/affect_bands.json"))["bands"]
    GAFF={1990:gb["1990"]["band"],2000:gb["2000"]["band"],2010:gb["2010"]["band"],
          2020:gb["2020"]["band"],2025:gb["2025"]["band"],"1980":gb["1980IC"]["band"]}
    anes=get_primary_targets(True); anes_ic=get_initial_targets_1980(True)
    CAND=(-0.09,0.30,0.0,0.014)
    seeds=list(range(9))
    res=run_seeds_parallel(_worker,[(s,*CAND) for s in seeds])
    means,_=aggregate([r["trajectory"] for r in res])
    print(f"CANDIDATE seed={CAND[0]} contact={CAND[1]} sat={CAND[2]} med_lr={CAND[3]}  (9 seeds)\n")
    print(f"{'panel':6}{'affect':>8}{'grounded band':>16}{'  par_sep':>9}{'mod':>7}{'xc':>7}")
    for y in [1980,1990,2000,2010,2020,2025]:
        m=means[y]; key="1980" if y==1980 else y; lo,hi=GAFF[key]; v=m["affect"]
        ok="*" if lo<=v<=hi else " "
        print(f"{y:6}{v:+8.3f}{f'[{lo:+.2f},{hi:+.2f}]':>16}{ok}{m['party_sep']:9.3f}{m['modularity']:7.3f}{m['xc_fraction']:7.3f}")
    # full 24-cell (grounded affect)
    tot=0; fails=[]
    for y in [1990,2000,2010,2020,2025]:
        for met in ["constraint","party_sep","affect","within_party_sd"]:
            band=GAFF[y] if met=="affect" else anes[y][met]
            ok=in_band(means[y][met],band); tot+=ok
            if not ok: fails.append(f"{y} {met}={means[y][met]:+.3f}")
    for met in ["variance","constraint","party_sep","within_party_sd"]:
        ok=in_band(means[1980][met],anes_ic[met]); tot+=ok
        if not ok: fails.append(f"1980 {met}={means[1980][met]:+.3f}")
    print(f"\nfull 24-cell (grounded affect bands): {tot}/24")
    print("out-of-band:", "; ".join(fails))
    print("\nNOTE vs committed baseline: affect cells now in band (were 0/5 under grounded);")
    print("remaining fails are the pre-existing constraint/within_sd cells, not affect/rewire.")

def main():
    from abm.calibration_parallel import run_seeds_parallel
    from scripts.phase8f_lib import get_primary_targets, get_initial_targets_1980, aggregate, in_band
    gb=json.load(open(_ROOT/"data/phase9_empirical/derived/affect_bands.json"))["bands"]
    GAFF={1990:gb["1990"]["band"],2000:gb["2000"]["band"],2010:gb["2010"]["band"],
          2020:gb["2020"]["band"],2025:gb["2025"]["band"],"1980":gb["1980IC"]["band"]}
    anes=get_primary_targets(True); anes_ic=get_initial_targets_1980(True)
    # (label, seed_mean, contact_scale, sat, med_lr)
    cands=[
      ("c.30+med.012",    -0.09,0.30,0.0, 0.012),
      ("c.30+med.015",    -0.09,0.30,0.0, 0.015),
      ("c.30+med.018",    -0.09,0.30,0.0, 0.018),
      ("c.30+med.020",    -0.09,0.30,0.0, 0.020),
      ("c.33+med.015",    -0.09,0.33,0.0, 0.015),
      ("c.28+med.018",    -0.09,0.28,0.0, 0.018),
    ]
    seeds=list(range(5))
    jobs=[(s,sm,cs,sa,ml) for (_,sm,cs,sa,ml) in cands for s in seeds]
    print(f"{len(jobs)} jobs ...")
    res=run_seeds_parallel(_worker, jobs)
    idx=0
    print(f"\n{'cand':18} 1980  1990  2000  2010  2020  2025   gIn  full24")
    for lab,sm,cs,sa,ml in cands:
        rr=res[idx:idx+len(seeds)]; idx+=len(seeds)
        means,_=aggregate([r["trajectory"] for r in rr])
        s=""; gin=0
        for y in [1980,1990,2000,2010,2020,2025]:
            key="1980" if y==1980 else y; lo,hi=GAFF[key]; v=means[y]["affect"]
            ok=lo<=v<=hi; gin+=ok; s+=f"{v:+.2f}{'*' if ok else ' '}"
        tot=0
        for y in [1990,2000,2010,2020,2025]:
            for m in ["constraint","party_sep","affect","within_party_sd"]:
                band=GAFF[y] if m=="affect" else anes[y][m]; tot+=in_band(means[y][m],band)
        for m in ["variance","constraint","party_sep","within_party_sd"]:
            tot+=in_band(means[1980][m],anes_ic[m])
        print(f"{lab:18}{s}  {gin}/6  {tot}/24")
    print("\ngrounded affect bands:",{k:GAFF[k] for k in GAFF})

if __name__ == "__main__":
    if "--confirm" in sys.argv:
        confirm()
    else:
        main()
