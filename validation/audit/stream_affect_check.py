"""Scratch audit: inspect the canonical shipped pipeline + affect/alignment
trajectory. READ-ONLY analysis (does not modify engine)."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import numpy as np
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from scripts.anes_preset import ANES_FULL_KWARGS

print("=== canonical ANES_FULL_KWARGS relevant keys ===")
for k in ("n_issues","constraint_rate","evidence_regrade","endogenous_elite",
          "data_fed_elite","tier_c_identity_pull_x","tier_c_identity_pull_y",
          "tier_c_party_pull_strength","sandbox_animus_mult","fj_alpha_scale"):
    print(f"  {k} = {ANES_FULL_KWARGS.get(k)}")

eng = build_engine(seed=0, **ANES_FULL_KWARGS)
print("\n=== pipeline rules (per-agent) ===")
for r in eng.rules.rules:
    print("  ", type(r).__name__)
print("=== env rules ===")
for r in eng.env_rules:
    print("  ", type(r).__name__)

# Is IdentitySorting / IdentityAlignment actually present?
names = [type(r).__name__ for r in eng.rules.rules]
print("\nIdentitySorting in pipeline:", "IdentitySorting" in names)
print("IdentityAlignment in pipeline:", "IdentityAlignment" in names)
print("MeasuredAlignment in pipeline:", "MeasuredAlignment" in names)
print("ConstraintOp in pipeline:", "ConstraintOp" in names)

# AffectiveUpdate identity_weight on shipped path
for r in eng.rules.rules:
    if type(r).__name__ == "AffectiveUpdate":
        print("\nAffectiveUpdate.identity_weight =", r.identity_weight)
        print("AffectiveUpdate.lr =", r.lr, " baseline =", r.baseline,
              " saturation =", r.saturation)
    if type(r).__name__ == "MediatedAnimus":
        print("MediatedAnimus.lr =", r.lr)
    if type(r).__name__ == "PartyPull":
        print("PartyPull.strength =", r.strength)
    if type(r).__name__ == "BacklashRepulsion":
        print("BacklashRepulsion.strength =", r.strength)

print("\nenv identity_alignment_affect_weight =",
      eng.env.attrs.get("identity_alignment_affect_weight"))
print("env party_issue_coupling =", eng.env.attrs.get("party_issue_coupling"))

# Run the arc and record affect + alignment per decade tick
sched = build_schedule(
    factional_seeding=ANES_FULL_KWARGS.get("factional_seeding", False),
    faction_anchor_events=ANES_FULL_KWARGS.get("faction_anchor_events", True),
    evidence_regrade=ANES_FULL_KWARGS.get("evidence_regrade", False),
    exogenous_shocks=ANES_FULL_KWARGS.get("exogenous_shocks", False))

def out_affect(eng):
    vals = []
    aligns = []
    for a in eng.agents:
        p = a.state.attrs.get("party")
        if p not in (0,1):
            continue
        aff = a.state.attrs.get("affect") or {}
        out = 1-p
        w = aff.get(out)
        if w is not None:
            vals.append(float(np.clip(w,-1,1)))
        aligns.append(float(a.state.attrs.get("identity_alignment",0.0)))
    return (np.mean(vals) if vals else None,
            np.mean(aligns) if aligns else None)

snap = {0:1980, 30:1990, 60:2000, 90:2010, 120:2020, 135:2025}
print("\n=== shipped trajectory (seed 0) ===")
print("tick  year  aff_out   mean_align")
a0, al0 = out_affect(eng)
print(f"{0:4d}  {1980}  {a0:+.4f}  {al0:.4f}")
for tick in (30,60,90,120,135):
    run_to(eng, sched, tick)
    a, al = out_affect(eng)
    print(f"{tick:4d}  {snap[tick]}  {a:+.4f}  {al:.4f}")
