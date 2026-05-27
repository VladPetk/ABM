"""Phase 8c D6 — affect-gate firing-rate diagnostic.

Standalone read-only diagnostic. Reports, at S4-end + after each
intervention's release-phase run:

  (a) Fraction of out-party encounters at which the BacklashRepulsion
      affect-gate threshold (-0.3) fires. 1.0 means the gate fires on
      every encounter (gate is a constant, not a conditional); <1.0
      means it's actually conditional.
  (b) Median post-S4 out-party warmth per agent (per seed median).
  (c) Count of agents whose median out-party warmth is below -0.3.

R2's concern: in the shipped calibration, the gate may effectively
always be open (warmth post-S4 is uniformly below -0.3), making it
a constant rather than a conditional. This diagnostic reports the
firing-rate so the reader can see whether the gate is doing work.

Phase 8c §1.5: runs the per-seed work via `run_seeds_parallel` for
~9× wall-clock speedup. Per-seed outputs are bit-identical to serial.

Read-only — does NOT change any thresholds, magnitudes, or
mechanisms. Run: `python scripts/phase8c_diagnostics.py`.
"""
from __future__ import annotations

import numpy as np

from abm.calibration_parallel import run_seeds_parallel
from abm.pillars import INTERVENTIONS_PHASE6, PILLAR, apply_intervention
from abm.pillars.calm_to_camps import build_engine

N = 250
TICKS = 200
SEEDS = tuple(range(12))


def affect_gate_stats(eng, threshold: float = -0.3) -> dict:
    """Compute the three D6 statistics on the current engine state."""
    net = eng.env.attrs["network"]
    gate_fires = 0
    gate_total = 0
    per_agent_median_warmth = []
    for a in eng.agents:
        own_party = a.state.attrs.get("party")
        affect_dict = a.state.attrs.get("affect") or {}
        warmths = [float(np.clip(v, -1.0, 1.0)) for v in affect_dict.values()]
        if warmths:
            per_agent_median_warmth.append(float(np.median(warmths)))
        for j in net.neighbors(a.id):
            neighbor = eng.space.agents_by_id[j]
            other = neighbor.state.attrs.get("party")
            if other is None or other == own_party:
                continue
            gate_total += 1
            w = float(np.clip(affect_dict.get(other, 0.0), -1.0, 1.0))
            if w < threshold:
                gate_fires += 1
    return {
        "gate_fire_rate": gate_fires / gate_total if gate_total else 0.0,
        "median_warmth": (
            float(np.median(per_agent_median_warmth))
            if per_agent_median_warmth else 0.0
        ),
        "cold_agent_count": sum(
            1 for w in per_agent_median_warmth if w < threshold
        ),
        "total_out_party_encounters": gate_total,
    }


def _s4_diagnostic_worker(seed: int) -> dict:
    """Build pillar engine to S4, run TICKS, return D6 stats."""
    eng = build_engine(seed=seed, n_agents=N)
    apply_intervention(eng, PILLAR.interventions[4])
    eng.run(TICKS)
    return affect_gate_stats(eng)


def _release_diagnostic_worker(args) -> dict:
    """`args = (intervention_id, seed)`. Run to S4, apply intervention,
    run TICKS, return D6 stats."""
    iv_id, seed = args
    intervention = next(iv for iv in INTERVENTIONS_PHASE6 if iv.id == iv_id)
    eng = build_engine(seed=seed, n_agents=N)
    apply_intervention(eng, PILLAR.interventions[4])
    eng.run(TICKS)
    apply_intervention(eng, intervention)
    eng.run(TICKS)
    return affect_gate_stats(eng)


def main():
    print("=" * 72)
    print("Phase 8c D6 — affect-gate firing-rate diagnostic")
    print(f"  N={N}, TICKS={TICKS}, seeds=0..{SEEDS[-1]}")
    print(f"  Gate threshold: BACKLASH_AFFECT_THRESHOLD = -0.3")
    print("  (Phase 8c §1.5: parallel-seed execution; bit-identical to serial)")
    print("=" * 72)

    # ----- S4-end snapshot (no intervention applied) ------------------
    print("\n[S4-end] affect-gate state before any intervention fires")
    s4_stats = run_seeds_parallel(_s4_diagnostic_worker, SEEDS)
    mean_rate = float(np.mean([s["gate_fire_rate"] for s in s4_stats]))
    mean_warmth = float(np.mean([s["median_warmth"] for s in s4_stats]))
    mean_cold = float(np.mean([s["cold_agent_count"] for s in s4_stats]))
    mean_total = float(np.mean([s["total_out_party_encounters"] for s in s4_stats]))
    print(f"  gate-firing rate: {mean_rate:.3f} (mean across seeds)")
    print(f"  median per-agent out-party warmth: {mean_warmth:+.3f}")
    print(f"  cold agents (warmth < -0.3): {mean_cold:.1f}/{N}")
    print(f"  total out-party encounters per tick: {mean_total:.0f}")
    if mean_rate > 0.95:
        print(
            "  NOTE: gate-firing rate > 0.95 — the gate is effectively a "
            "constant at this calibration. The conditional interpretation "
            "(R1 fires only on already-cold agents) is not load-bearing "
            "at S4-end because nearly every agent is already cold."
        )

    # ----- Per-intervention release-phase snapshot --------------------
    print("\n[release-phase] gate state after each intervention runs")
    iv_seed_args = [(iv.id, s) for iv in INTERVENTIONS_PHASE6 for s in SEEDS]
    flat = run_seeds_parallel(_release_diagnostic_worker, iv_seed_args)
    by_iv: dict[str, list] = {iv.id: [] for iv in INTERVENTIONS_PHASE6}
    for (iv_id, _seed), stats in zip(iv_seed_args, flat):
        by_iv[iv_id].append(stats)
    for iv in INTERVENTIONS_PHASE6:
        seed_stats = by_iv[iv.id]
        rate = float(np.mean([s["gate_fire_rate"] for s in seed_stats]))
        warmth = float(np.mean([s["median_warmth"] for s in seed_stats]))
        cold = float(np.mean([s["cold_agent_count"] for s in seed_stats]))
        print(f"\n  [{iv.id}]  ({iv.label})")
        print(f"    gate-firing rate: {rate:.3f}")
        print(f"    median per-agent out-party warmth: {warmth:+.3f}")
        print(f"    cold agents (warmth < -0.3): {cold:.1f}/{N}")

    print("\n" + "=" * 72)


if __name__ == "__main__":
    main()
