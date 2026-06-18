"""Bit-identity fingerprint: canonical anes_full seed 0, 2025 endpoint."""
import sys
sys.path.insert(0, ".")
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from scripts.phase8f_lib import measure_all
from scripts.anes_preset import ANES_FULL_KWARGS

k = dict(ANES_FULL_KWARGS)
eng = build_engine(seed=0, **k)
sched = build_schedule(
    factional_seeding=k.get("factional_seeding", False),
    faction_anchor_events=k.get("faction_anchor_events", True),
    evidence_regrade=k.get("evidence_regrade", False),
    exogenous_shocks=k.get("exogenous_shocks", False))
run_to(eng, sched, 135)
m = measure_all(eng)
print("FP", round(m["party_sep"], 9), round(m["affect"], 9),
      round(m["constraint"], 9), round(m.get("identity_alignment", 0.0), 9),
      round(m["within_party_sd"], 9))
