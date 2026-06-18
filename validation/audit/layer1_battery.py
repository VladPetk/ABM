"""Layer-1 generic validation gate (G1) — the de-circularization harness.

The audit's F2: the model is calibrated AND scored on the same ANES recode, so
"it fits" is partly circular. The fix (reversibility_spec.md §4) is to validate
the MECHANISM LAYER *generically* first — does the coupled rule set behave
sensibly across regimes, judged on directional/behavioural criteria, NOT US
bands — and only then check the US-fit (G2 = the §11 scorecard).

This harness runs the engine across a forcing x restoring matrix (all via
`build_engine` kwargs; the engine is untouched; the canonical build stays
bit-identical) and evaluates the PRE-REGISTERED G1 criteria from the spec. It is
deliberately runnable BEFORE the R-mechanisms are finished: it then shows the
honest baseline (C4 does not yet reverse) and becomes the target each increment
is measured against.

Run: .venv/Scripts/python.exe validation/audit/layer1_battery.py

NOT a bless. Single seed for the directional signal (matches the probe).
"""
import sys
sys.path.insert(0, ".")
import numpy as np
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from scripts.phase8f_lib import measure_all
from scripts.anes_preset import ANES_FULL_KWARGS

SEED = 0
# Snapshot every 9 ticks (3 yrs) so peak/decline and the "sustained over >=12
# ticks" criterion have resolution; 135 = end-2025.
SNAPS = list(range(15, 136, 9))
if SNAPS[-1] != 135:
    SNAPS.append(135)

# --- The restoring-mechanism stack (RESTORING knobs). Extend as R3-R6 land. ---
# Today: R1 (contact->affect warming) + R2 (cross-pressure damping). The probe
# showed R2 hits ConstraintOp not PartyPull, so it barely touches party_sep --
# until R2 is retargeted + R4/R5/R6 added, C4 will NOT meet G1-reverse on sep.
# BASE = always-on MECHANISM-LAYER corrections (not regime-varying). R7 (affect
# rest state) belongs here: a valid affect mechanism HAS an equilibrium in every
# regime, so it must be on even in C3 (where G1-flat is measured). (R5's media-
# direction fix, when built, will also live here — a correction, not a knob.)
BASE = dict(
    affect_rest_rate=0.015, affect_rest_anchor=-0.15,  # R7 — affect equilibrium
)

# RESTORING = regime-varying restoring FORCES (a society can have more/less of
# these). Applied only to C2/C4.
RESTORING_STRONG = dict(
    contact_warming=True, contact_coop_frac=0.8, contact_warm_threshold=-1.0,
    contact_warm_magnitude=0.10, contact_coop_share=0.6,
    xpressure_sorting_damp=0.7, xpressure_affect_damp=0.7,
    bridge_rewire=0.5,  # R3 — cross-cutting tie formation (feeds R1, mixes net)
    bc_affect_weight_floor=0.6,  # R4 — warmth re-opens cross-party BC convergence
    thermostatic_gain=0.10, thermostatic_reference=0.4,  # R6 — gentle homeostat (lowers equilibrium)
)

# --- Forcing-down: zero the US-specific EXOGENOUS drivers, keep mechanisms. ---
# The mob_* schedule IS the forcing (it mobilizes the activist->elite->mass loop);
# zeroing it leaves the loop mechanism intact but unmobilized. elite_gain is the
# loop's response GAIN (a mechanism param), left at canonical. Plus drop the rigid
# common-mode level shifts. Dated events off via FORCING_OFF_SCHED. So C3 is a
# clean "mechanism layer at rest, no external drivers" test: any rise here is
# INTRINSIC mechanism drift (ConstraintOp / PartyPull / affect), not forcing.
FORCING_LOW = dict(mob_base=0.0, mob_peak=0.0, mob_backload=0.0,
                   cultural_common_mode=False, economic_common_mode=False)
# C4 "Sweden-like": enough early forcing to BUILD a sorted state, weak late, so
# strong restoring can overcome it -> peak-then-decline (the probe's config).
FORCING_SWEDEN = dict(mob_peak=0.8, elite_gain=1.0)
# Turn off the dated event/shock injectors (for the truly-neutral C3).
FORCING_OFF_SCHED = dict(faction_anchor_events=False, exogenous_shocks=False)

CONFIGS = [
    ("C1 polarizing  (F-high, R-off )", {}),
    ("C2 resisted    (F-high, R-strong)", dict(RESTORING_STRONG)),
    ("C3 neutral     (F-low,  R-off )", dict(FORCING_LOW, **FORCING_OFF_SCHED)),
    ("C4 depolarizing(F-sweden, R-strong)", dict(RESTORING_STRONG, **FORCING_SWEDEN)),
]


def run(extra):
    k = dict(ANES_FULL_KWARGS)
    k.update(BASE)      # always-on mechanism-layer corrections (R7)
    k.update(extra)     # per-regime forcing / restoring
    eng = build_engine(seed=SEED, **k)
    sched = build_schedule(
        factional_seeding=k.get("factional_seeding", False),
        faction_anchor_events=k.get("faction_anchor_events", True),
        evidence_regrade=k.get("evidence_regrade", False),
        exogenous_shocks=k.get("exogenous_shocks", False))
    traj = {}
    for tick in SNAPS:
        run_to(eng, sched, tick)
        m = measure_all(eng)
        traj[tick] = (m["party_sep"], m["affect"], m["constraint"])
    return traj


def _series(traj, idx):
    return np.array([traj[t][idx] for t in SNAPS])


def _peak_then_drop(s, sustain_ticks=12):
    """Sustained decline: max drop from a peak to a LATER point that holds for
    >= sustain_ticks. Returns (drop, peak_tick, end_val)."""
    best = 0.0
    pk_tick = SNAPS[0]
    for i in range(len(SNAPS)):
        for j in range(i + 1, len(SNAPS)):
            if SNAPS[j] - SNAPS[i] >= sustain_ticks:
                drop = s[i] - s[j]
                if drop > best:
                    best, pk_tick = drop, SNAPS[i]
    return best, pk_tick


def main():
    print("LAYER-1 GENERIC VALIDATION GATE (G1) — seed", SEED, "\n")
    R = {}
    for name, extra in CONFIGS:
        R[name] = run(extra)
        sep = _series(R[name], 0)
        aff = _series(R[name], 1)
        print("== " + name + " ==")
        print(f"   2025: party_sep {sep[-1]:+.3f}  affect {aff[-1]:+.3f}  "
              f"constraint {R[name][135][2]:+.3f}")
        d_sep, pk_s = _peak_then_drop(sep)
        d_aff, pk_a = _peak_then_drop(-aff)  # affect WARMS = -affect drops
        print(f"   sep peak->end drop {d_sep:+.3f} (peak @ {pk_s}); "
              f"affect warming peak->end {d_aff:+.3f} (peak @ {pk_a})\n")

    c1, c2, c3, c4 = (R[c[0]] for c in CONFIGS)
    s1, s2, s4 = _series(c1, 0)[-1], _series(c2, 0)[-1], _series(c4, 0)[-1]
    a1, a2, a4 = _series(c1, 1)[-1], _series(c2, 1)[-1], _series(c4, 1)[-1]

    print("PRE-REGISTERED G1 CRITERIA (spec §4):")
    # 1 rise
    rise = (s1 >= 1.0) and (a1 <= -0.6)
    print(f"  G1-rise   (C1 sep>=1.0 & affect<=-0.6): sep {s1:+.3f} aff {a1:+.3f}  "
          f"-> {'PASS' if rise else 'FAIL'}")
    # 2 flat
    ds3 = _series(c3, 0)[-1] - _series(c3, 0)[0]
    da3 = _series(c3, 1)[-1] - _series(c3, 1)[0]
    flat = (abs(ds3) <= 0.10) and (abs(da3) <= 0.08)
    print(f"  G1-flat   (C3 |dsep|<=0.10 & |daff|<=0.08): dsep {ds3:+.3f} daff {da3:+.3f}  "
          f"-> {'PASS' if flat else 'FAIL'}")
    # 3 reverse (the falsification core)
    sep4 = _series(c4, 0)
    aff4 = _series(c4, 1)
    drop_s, _ = _peak_then_drop(sep4)
    drop_a, _ = _peak_then_drop(-aff4)
    reverse = (drop_s >= 0.10) and (drop_a >= 0.10)
    print(f"  G1-reverse(C4 sep drop>=0.10 & affect warm>=0.10, sustained): "
          f"sep {drop_s:+.3f} aff {drop_a:+.3f}  -> {'PASS' if reverse else 'FAIL'}")
    # 4 ordering
    order = (s1 > s2 > s4) and (a1 < a2 < a4)
    print(f"  G1-order  (sep C1>C2>C4 & affect C1<C2<C4): "
          f"sep {s1:.3f}>{s2:.3f}>{s4:.3f}  aff {a1:.3f}<{a2:.3f}<{a4:.3f}  "
          f"-> {'PASS' if order else 'FAIL'}")
    n_pass = sum([rise, flat, reverse, order])
    print(f"\n  G1 SUMMARY: {n_pass}/4 criteria pass "
          f"(G1-ablation is a separate per-mechanism pass).")
    # Diagnostic split: which AXIS blocks each failing criterion.
    if not flat:
        blk = "affect" if abs(da3) > 0.08 and abs(ds3) <= 0.10 else "both"
        print(f"  NOTE flat: blocked by {blk} (C3 sep Δ {ds3:+.3f}, affect Δ {da3:+.3f}).")
    if not reverse:
        leg = ("affect leg" if drop_s >= 0.10 and drop_a < 0.10
               else ("sep leg" if drop_a >= 0.10 else "both legs"))
        print(f"  NOTE reverse: blocked by {leg} (sep {drop_s:+.3f}, affect {drop_a:+.3f}). "
              "Position reverses via R2+R3(+R6); the affect leg needs R7 (rest "
              "state) PAIRED with the P3a affect-magnitude re-cal — R7 alone "
              "cannot overcome the canonical over-cooling.")


if __name__ == "__main__":
    main()
