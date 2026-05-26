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

Run: `python scripts/phase6_calibration.py`.
"""
from __future__ import annotations

import numpy as np

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


def measure_intervention(intervention, seed):
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
    return before, after


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


def main():
    print("=" * 72)
    print("Phase 6 §11 — bucket each intervention by measurement")
    print(f"  N={N}, TICKS={TICKS}, seeds=0..{SEEDS[-1]}")
    print("=" * 72)

    # ------------------------------------ sanity: post-S4 affect < -0.3
    print("\n[sanity] post-S4 mean affective_polarization across seeds")
    affs = []
    for seed in SEEDS:
        eng = build_engine(seed=seed, n_agents=N)
        apply_intervention(eng, PILLAR.interventions[4])
        eng.run(TICKS)
        affs.append(affective_polarization(eng.agents))
    mean_aff = float(np.mean(affs))
    print(f"  mean = {mean_aff:+.3f} "
          f"({'CROSSES -0.3 — R1 gate fires for X1' if mean_aff < -0.3 else 'WARN: above -0.3, X1 backfire weakened'})")

    # ------------------------------------ per-intervention release
    results = {}
    for iv in INTERVENTIONS_PHASE6:
        deltas = {k: [] for k in ("sep", "xc", "aff", "con", "var")}
        for seed in SEEDS:
            before, after = measure_intervention(iv, seed)
            for k in deltas:
                deltas[k].append(after[k] - before[k])
        means = {k: float(np.mean(deltas[k])) for k in deltas}
        results[iv.id] = means
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
    for eps, label in ((2.0, "loose"), (0.30, "mid"), (0.15, "tight")):
        finals = []
        for seed in range(6):
            eng = build_compass(
                n_agents=200, epsilon=eps, attraction=0.08,
                repulsion=0.0, noise=0.01, seed=seed,
            )
            eng.run(TICKS)
            finals.append(variance(eng.positions()))
        print(f"  HK eps={eps} ({label}) final variance: {np.mean(finals):.3f}")

    print("\n" + "=" * 72)


if __name__ == "__main__":
    main()
