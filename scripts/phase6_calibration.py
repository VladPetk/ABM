"""Phase 6 §11 — measure-then-bless each intervention's bucket.

Runs the release-phase experiment for each X-intervention across the
STAGE_SEEDS ensemble, and reports the secondary metrics needed to
bless the label_kind. The labels in `interventions_phase6.py` are
*predicted*; this script's output is what actually commits them.

For each intervention reports:
  - Δparty_separation         (the bucket metric)
  - Δcross_cutting_tie_fraction
  - Δaffective_polarization
  - Δideological_constraint
  - Δvariance

And global sanity checks:
  - post-S4 mean affect (must be < -0.3 for X1's R1 gate to fire)
  - canonical HK unchanged
  - Phase 8c D6: affect-gate firing-rate diagnostic

Phase 8c §1.5: runs the per-seed work via `run_seeds_parallel` for
~9× wall-clock speedup. Per-seed outputs are bit-identical to serial.

Run: `python scripts/phase6_calibration.py`.
"""
from __future__ import annotations

import numpy as np

from abm.calibration_parallel import run_seeds_parallel
from abm.metrics.affective import affective_polarization, ideological_constraint
from abm.metrics.network import cross_cutting_tie_fraction
from abm.metrics.polarization import variance
from abm.pillars import (
    INTERVENTIONS_PHASE6,
    PILLAR,
    apply_intervention,
)
from abm.pillars.calm_to_camps import build_engine
from abm.scenarios.compass_basic import build as build_compass

N = 250
TICKS = 200
SEEDS = tuple(range(12))


def party_sep(eng):
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    return float(
        np.linalg.norm(pos[parties == 0].mean(axis=0) - pos[parties == 1].mean(axis=0))
    )


def constraint_avg(eng):
    ic = ideological_constraint(eng.agents)
    return (ic["x"] + ic["y"]) / 2.0


# --- workers (top-level for `multiprocessing.spawn`) -----------------


def _s4_end_diagnostic_worker(seed: int) -> dict:
    """Run S0→S4 + TICKS post-S4; return affect + gate-firing diagnostic."""
    eng = build_engine(seed=seed, n_agents=N)
    apply_intervention(eng, PILLAR.interventions[4])
    eng.run(TICKS)
    aff = affective_polarization(eng.agents)
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
            if w < -0.3:
                gate_fires += 1
    return {
        "aff": aff,
        "gate_fire_rate": gate_fires / gate_total if gate_total else 0.0,
        "median_warmth": (
            float(np.median(per_agent_median_warmth))
            if per_agent_median_warmth else 0.0
        ),
        "cold_count": sum(
            1 for w in per_agent_median_warmth if w < -0.3
        ),
    }


def _intervention_release_worker(args) -> dict:
    """`args = (intervention_id, seed)`. Build, run to S4, measure
    before, apply intervention, run TICKS, measure after, return deltas."""
    iv_id, seed = args
    intervention = next(iv for iv in INTERVENTIONS_PHASE6 if iv.id == iv_id)
    eng = build_engine(seed=seed, n_agents=N)
    apply_intervention(eng, PILLAR.interventions[4])
    eng.run(TICKS)
    before = {
        "sep": party_sep(eng),
        "xc": cross_cutting_tie_fraction(eng.agents, eng.env.attrs["network"]),
        "aff": affective_polarization(eng.agents),
        "con": constraint_avg(eng),
        "var": variance(eng.positions()),
    }
    apply_intervention(eng, intervention)
    eng.run(TICKS)
    after = {
        "sep": party_sep(eng),
        "xc": cross_cutting_tie_fraction(eng.agents, eng.env.attrs["network"]),
        "aff": affective_polarization(eng.agents),
        "con": constraint_avg(eng),
        "var": variance(eng.positions()),
    }
    return {k: after[k] - before[k] for k in before}


def _hk_worker(args) -> float:
    """`args = (epsilon, seed)`. Build compass scenario, run, return variance."""
    eps, seed = args
    eng = build_compass(
        n_agents=200, epsilon=eps, attraction=0.08,
        repulsion=0.0, noise=0.01, seed=seed,
    )
    eng.run(TICKS)
    return variance(eng.positions())


# --- classifiers (Phase 6 R5 / Phase 7 two-axis) ---------------------


def classify_sep(dsep):
    """Issue-sorting axis (helpful = negative)."""
    if abs(dsep) < 0.05:
        return "null"
    if -0.15 < dsep < -0.05:
        return "partial"
    if dsep <= -0.15:
        return "real"
    if dsep > 0.05:
        return "backfire"
    return "unclassified"


def classify_aff(daff):
    """Affect axis (helpful = positive — warmth recovers)."""
    if abs(daff) < 0.05:
        return "null"
    if 0.05 < daff < 0.15:
        return "partial"
    if daff >= 0.15:
        return "real"
    if daff < -0.05:
        return "backfire"
    return "unclassified"


# --- main -----------------------------------------------------------


def main():
    print("=" * 72)
    print("Phase 6 §11 — bucket each intervention by measurement")
    print(f"  N={N}, TICKS={TICKS}, seeds=0..{SEEDS[-1]}")
    print("  (Phase 8c §1.5: parallel-seed execution; bit-identical to serial)")
    print("=" * 72)

    # ------------------------------------ sanity + D6 diagnostic
    print("\n[sanity] post-S4 affective_polarization + D6 affect-gate firing rate")
    s4_results = run_seeds_parallel(_s4_end_diagnostic_worker, SEEDS)
    affs = [r["aff"] for r in s4_results]
    gate_fire_rates = [r["gate_fire_rate"] for r in s4_results]
    median_warmths_per_seed = [r["median_warmth"] for r in s4_results]
    cold_agent_counts = [r["cold_count"] for r in s4_results]
    mean_aff = float(np.mean(affs))
    print(f"  mean affective_polarization = {mean_aff:+.3f} "
          f"({'CROSSES -0.3 — R1 gate fires for X1' if mean_aff < -0.3 else 'WARN: above -0.3, X1 backfire weakened'})")
    print(
        f"\n[Phase 8c D6] affect-gate firing-rate diagnostic at S4-end "
        f"(post-S4 ensemble)"
    )
    print(
        f"  mean gate-firing rate across out-party encounters: "
        f"{np.mean(gate_fire_rates):.3f} (1.0 = gate fires on EVERY "
        f"encounter; <1.0 means the gate is a conditional, not a constant)"
    )
    print(
        f"  median per-agent out-party warmth across seeds: "
        f"{np.median(median_warmths_per_seed):+.3f}"
    )
    print(
        f"  mean count of agents with median out-party warmth < -0.3 "
        f"(per seed; out of N={N}): {np.mean(cold_agent_counts):.1f}"
    )

    # ------------------------------------ per-intervention release
    # Flatten (intervention, seed) pairs into a single parallel batch
    # — more efficient than 6 separate Pool spawns.
    print("\n[release-phase] per-intervention measurement")
    iv_seed_args = [(iv.id, s) for iv in INTERVENTIONS_PHASE6 for s in SEEDS]
    flat_results = run_seeds_parallel(_intervention_release_worker, iv_seed_args)
    # Reshape into {iv_id: list-of-12-deltas-dicts}
    by_iv: dict[str, list] = {iv.id: [] for iv in INTERVENTIONS_PHASE6}
    for (iv_id, _seed), deltas in zip(iv_seed_args, flat_results):
        by_iv[iv_id].append(deltas)

    for iv in INTERVENTIONS_PHASE6:
        deltas_list = by_iv[iv.id]
        means = {
            k: float(np.mean([d[k] for d in deltas_list]))
            for k in deltas_list[0]
        }
        sep_bucket = classify_sep(means["sep"])
        aff_bucket = classify_aff(means["aff"])
        print(f"\n[{iv.id}]  ({iv.label})")
        print(f"  d-party_separation:           {means['sep']:+.4f}  -> issue_sorting: {sep_bucket}")
        print(f"  d-affective_polarization:     {means['aff']:+.4f}  -> affect:        {aff_bucket}")
        print(f"  d-cross_cutting_tie_fraction: {means['xc']:+.4f}")
        print(f"  d-ideological_constraint:     {means['con']:+.4f}")
        print(f"  d-variance:                   {means['var']:+.4f}")
        declared_sep = iv.effect_buckets.get("issue_sorting", "<none>")
        declared_aff = iv.effect_buckets.get("affect", "<none>")
        sep_match = "MATCH" if sep_bucket == declared_sep else "MISMATCH"
        aff_match = "MATCH" if aff_bucket == declared_aff else "MISMATCH"
        print(f"    declared: issue_sorting={declared_sep} ({sep_match}); "
              f"affect={declared_aff} ({aff_match})")

    # ------------------------------------ canonical HK still untouched
    print("\n[canonical HK] eps sweep — must be unchanged")
    hk_args = [(eps, s) for eps in (2.0, 0.30, 0.15) for s in range(6)]
    hk_results = run_seeds_parallel(_hk_worker, hk_args)
    for i, (eps, label) in enumerate(((2.0, "loose"), (0.30, "mid"), (0.15, "tight"))):
        finals = hk_results[i*6:(i+1)*6]
        print(f"  HK eps={eps} ({label}) final variance: {np.mean(finals):.3f}")

    print("\n" + "=" * 72)


if __name__ == "__main__":
    main()
