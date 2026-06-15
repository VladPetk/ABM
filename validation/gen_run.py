"""Generate fresh baseline (flag off) and emergent (flag on) runs in the
seed_0.json schema subset the battery needs, so we can grade both apples-to-apples
on the CURRENT engine (the shipped seed_0.json is stale). Usage:
    python validation/gen_run.py baseline   -> validation/run_baseline.json
    python validation/gen_run.py emergent    -> validation/run_emergent.json
"""
import sys, json
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.anes_preset import ANES_FULL_KWARGS
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to

mode = sys.argv[1] if len(sys.argv) > 1 else "baseline"
kw = dict(ANES_FULL_KWARGS)
if mode == "emergent":
    kw["cultural_common_mode"] = True
    kw["cohort_replacement_rate"] = 0.007

eng = build_engine(seed=0, **kw)
sched = build_schedule(
    factional_seeding=kw.get("factional_seeding", False),
    faction_anchor_events=kw.get("faction_anchor_events", True),
    evidence_regrade=kw.get("evidence_regrade", False),
    exogenous_shocks=kw.get("exogenous_shocks", False))


def snap(eng):
    pos = [list(map(float, a.state.ideology)) for a in eng.agents]
    party = [int(a.state.attrs.get("party")) for a in eng.agents]
    # out-party affect mean over partisans
    aff = []
    for a in eng.agents:
        p = a.state.attrs.get("party")
        if p in (0, 1):
            d = a.state.attrs.get("affect") or {}
            v = d.get(1 - p)
            if v is not None:
                aff.append(float(v))
    return {"positions": pos, "party": party}, {"affect": float(np.mean(aff)) if aff else 0.0}


ticks, macro = [], []
t0, m0 = snap(eng); ticks.append(t0); macro.append(m0)
for t in range(1, 136):
    run_to(eng, sched, t)
    tk, mc = snap(eng); ticks.append(tk); macro.append(mc)

out = {"n_agents": len(eng.agents), "n_ticks": 136, "seed": 0,
       "tick_0_year": 1980.0, "ticks_per_year": 3.0,
       "agent_static": [{"id": i} for i in range(len(eng.agents))],
       "ticks": ticks, "macro": macro}
path = Path(__file__).resolve().parent / f"run_{mode}.json"
path.write_text(json.dumps(out))
print(f"wrote {path}  (mode={mode})")
