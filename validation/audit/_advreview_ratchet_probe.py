"""Adversarial-review probe for the 'one-way ratchet' finding.

Q1. Is the baseline sep / aff_out trajectory monotone, or are there
    plateaus / reversals under the model's own dynamics?
Q2. Are the common-mode rules sorting-invariant (do they change sep)?
Q3. Does PerceptionUpdate measurably warm affect (a convergent channel
    the finding omitted)? Does BC-off change the arc?
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import numpy as np
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from scripts.anes_preset import ANES_FULL_KWARGS


def macro(engine):
    pos = engine.positions()
    parties = np.array([a.state.attrs.get("party") for a in engine.agents])
    dem = pos[parties == 0]
    rep = pos[parties == 1]
    sep = float(np.linalg.norm(rep.mean(axis=0) - dem.mean(axis=0)))
    # out-party warmth (mean over partisans of warmth toward the other party)
    warms = []
    for a in engine.agents:
        p = a.state.attrs.get("party")
        if p in (0, 1):
            aff = a.state.attrs.get("affect") or {}
            other = 1 - p
            if other in aff:
                warms.append(float(np.clip(aff[other], -1, 1)))
    aff_out = float(np.mean(warms)) if warms else float("nan")
    return sep, aff_out


def trajectory(**overrides):
    kw = dict(ANES_FULL_KWARGS)
    kw.update(overrides)
    eng = build_engine(seed=0, **kw)
    sched = build_schedule(
        factional_seeding=kw.get("factional_seeding", False),
        faction_anchor_events=kw.get("faction_anchor_events", True),
        evidence_regrade=kw.get("evidence_regrade", False),
        exogenous_shocks=kw.get("exogenous_shocks", False),
    )
    seps, affs = [], []
    for t in range(0, 136):
        run_to(eng, sched, t)
        s, a = macro(eng)
        seps.append(s)
        affs.append(a)
    return np.array(seps), np.array(affs)


def describe(name, seps, affs):
    dsep = np.diff(seps)
    daff = np.diff(affs)
    print(f"\n=== {name} ===")
    print(f"  sep:  start {seps[0]:.3f}  end {seps[-1]:.3f}  "
          f"max {seps.max():.3f}@{seps.argmax()}  min {seps.min():.3f}@{seps.argmin()}")
    print(f"        ticks with sep DECREASING (depolarizing): {int((dsep < -1e-4).sum())}/135  "
          f"(largest single drop {dsep.min():+.4f})")
    print(f"  aff:  start {affs[0]:.3f}  end {affs[-1]:.3f}  "
          f"max {affs.max():.3f}@{affs.argmax()}  min {affs.min():.3f}@{affs.argmin()}")
    print(f"        ticks with aff WARMING (depolarizing): {int((daff > 1e-4).sum())}/135  "
          f"(largest single warm {daff.max():+.4f})")


def main():
    base_s, base_a = trajectory()
    describe("CANONICAL baseline", base_s, base_a)

    # common-mode OFF -> does sep change? (sorting-invariance test)
    cm_s, cm_a = trajectory(cultural_common_mode=False, economic_common_mode=False)
    print("\n--- common-mode ON vs OFF (sorting-invariance of the rigid shift) ---")
    print(f"  sep end:  CM-on {base_s[-1]:.4f}   CM-off {cm_s[-1]:.4f}   diff {base_s[-1]-cm_s[-1]:+.4f}")
    print(f"  max |sep diff| over arc: {np.abs(base_s-cm_s).max():.4f}")

    # PerceptionUpdate effect on affect (set its rate to 0 via a kwarg? it's hardcoded.
    # Instead compare end affect to a run where we can't easily disable it — skip if no kwarg.)

    # BC off
    bc_s, bc_a = trajectory(tier_c_bc_strength=0.0)
    print("\n--- BC on vs off ---")
    print(f"  sep end:  BC-on {base_s[-1]:.4f}   BC-off {bc_s[-1]:.4f}   diff {base_s[-1]-bc_s[-1]:+.4f}")
    print(f"  aff end:  BC-on {base_a[-1]:.4f}   BC-off {bc_a[-1]:.4f}   diff {base_a[-1]-bc_a[-1]:+.4f}")


if __name__ == "__main__":
    main()
