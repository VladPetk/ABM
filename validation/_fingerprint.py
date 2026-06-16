"""Fingerprint the canonical arc (seed 0) for bit-identity checks."""
import sys, hashlib, json
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.anes_preset import ANES_FULL_KWARGS
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to

mode = sys.argv[1] if len(sys.argv) > 1 else "canonical"
kw = dict(ANES_FULL_KWARGS)
if mode == "econ_on":
    kw["economic_common_mode"] = True

eng = build_engine(seed=0, **kw)
sched = build_schedule(
    factional_seeding=kw.get("factional_seeding", False),
    faction_anchor_events=kw.get("faction_anchor_events", True),
    evidence_regrade=kw.get("evidence_regrade", False),
    exogenous_shocks=kw.get("exogenous_shocks", False))

h = hashlib.sha256()
for t in range(1, 136):
    run_to(eng, sched, t)
    pos = np.array([a.state.ideology for a in eng.agents])
    h.update(np.ascontiguousarray(pos).tobytes())
pos = np.array([a.state.ideology for a in eng.agents])
party = np.array([a.state.attrs.get("party") for a in eng.agents])
m = (party == 0) | (party == 1)
print(json.dumps({
    "mode": mode,
    "hash": h.hexdigest(),
    "econ_com@135": round(float(pos[m, 0].mean()), 6),
    "cult_com@135": round(float(pos[m, 1].mean()), 6),
    "sep@135": round(float(np.hypot(*(pos[party == 1].mean(0) - pos[party == 0].mean(0)))), 6),
}))
