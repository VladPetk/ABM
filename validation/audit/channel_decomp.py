"""Decompose out-party cooling: AffectiveUpdate (contact, with align_factor)
vs MediatedAnimus (parasocial). Instrument by zeroing each channel and
re-running to 2025. READ-ONLY (copies kwargs; does not edit engine)."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import numpy as np
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from scripts.anes_preset import ANES_FULL_KWARGS

def mean_aff(eng):
    vals=[]
    for a in eng.agents:
        p=a.state.attrs.get("party")
        if p not in (0,1): continue
        aff=a.state.attrs.get("affect") or {}
        w=aff.get(1-p)
        if w is not None: vals.append(float(np.clip(w,-1,1)))
    return float(np.mean(vals)) if vals else None

def run(kw_over):
    kw=dict(ANES_FULL_KWARGS); kw.update(kw_over)
    eng=build_engine(seed=0, **kw)
    sched=build_schedule(
        factional_seeding=kw.get("factional_seeding",False),
        faction_anchor_events=kw.get("faction_anchor_events",True),
        evidence_regrade=kw.get("evidence_regrade",False),
        exogenous_shocks=kw.get("exogenous_shocks",False))
    run_to(eng,sched,135)
    return mean_aff(eng)

base = run({})
# Kill MediatedAnimus via sandbox_animus_mult only affects BOTH lr's; instead
# set MediatedAnimus off by also looking at identity_alignment_affect_weight.
# We can't easily zero one without editing; use the exposed multipliers:
#  - sandbox_animus_mult scales AffectiveUpdate.lr AND MediatedAnimus.lr.
# So instead, zero the align channel by setting evidence_regrade-derived weight?
# Simplest faithful probe: scale sandbox_animus_mult to 0 (kills contact lr +
# parasocial lr) to see floor, and compare.
no_animus = run({"sandbox_animus_mult": 0.0})
print(f"2025 aff_out  CANONICAL          = {base:+.4f}")
print(f"2025 aff_out  sandbox_animus=0   = {no_animus:+.4f}  (floor from seed+other channels)")
print(f"  total cooling attributable to animus lrs = {base-no_animus:+.4f}")
