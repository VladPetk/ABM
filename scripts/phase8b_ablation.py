"""Phase 8b mechanism ablation.

For each of the 5 mechanisms (M1 heterogeneity, M2 ResidentialMigration,
M3 CohortReplacement, M4 asymmetric, M5 IdentitySorting), measure the
2025 end-state with that mechanism disabled. Reports the contribution
of each mechanism to the final fit.

Disable rules:
- M1 heterogeneity: set per-agent epsilon/fj_alpha/affect_lr to the
  rule-level constants (so heterogeneity has no effect).
- M2: ResidentialMigration.migration_rate = 0.
- M3: CohortReplacement.replacement_rate = 0.
- M4: EliteDrift.asymmetric = {0: 1, 1: 1} (symmetric); party_cue σ
  symmetric at 0.25 — done at build via a flag.
- M5: IdentitySorting.sort_rate = 0 throughout (all decade boundaries
  set to 0).
"""
from __future__ import annotations

import numpy as np

from abm.metrics.affective import affective_polarization, ideological_constraint
from abm.metrics.network import cross_cutting_tie_fraction
from abm.metrics.polarization import variance
from abm.pillars.historical_arc import (
    build_engine,
    build_schedule,
    final_tick,
)
from abm.pillars.schedule import run_to


SEEDS = tuple(range(15))   # Phase 8c §7 S1: historical 5 → 15 seeds


def constraint_avg(eng):
    ic = ideological_constraint(eng.agents)
    return (ic["x"] + ic["y"]) / 2.0


def party_sep(eng):
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    return float(np.linalg.norm(
        pos[parties == 0].mean(axis=0) - pos[parties == 1].mean(axis=0)
    ))


def measure_2025(disable=None):
    """Run to 2025 with the named mechanism disabled. Returns ensemble
    means."""
    results = {k: [] for k in (
        "variance", "constraint", "party_sep", "affect", "xc_fraction"
    )}
    for seed in SEEDS:
        eng = build_engine(seed=seed, n_agents=250)
        sched = build_schedule()

        if disable == "M1":
            # Reset per-agent heterogeneity to rule-level uniform values.
            for a in eng.agents:
                a.state.attrs["epsilon"] = 0.30
                a.state.attrs["fj_alpha"] = 0.05
                a.state.attrs["affect_lr"] = 0.01

        if disable == "M2":
            for r in eng.env_rules:
                if type(r).__name__ == "ResidentialMigration":
                    r.migration_rate = 0.0

        if disable == "M3":
            for r in eng.env_rules:
                if type(r).__name__ == "CohortReplacement":
                    r.replacement_rate = 0.0

        if disable == "M4":
            # Symmetric EliteDrift + symmetric party_cue σ.
            for r in eng.env_rules:
                if type(r).__name__ == "EliteDrift":
                    r.asymmetric = {0: 1.0, 1: 1.0}
            for a in eng.agents:
                # Re-roll party_cue with symmetric σ=0.25.
                party = a.state.attrs["party"]
                centroid = np.array(
                    [-0.30, 0.0]) if party == 0 else np.array([0.30, 0.0]
                )
                a.state.attrs["party_cue"] = (
                    centroid + np.random.default_rng(
                        seed * 1000 + a.id).normal(0, 0.25, size=2)
                )

        if disable == "M5":
            # Zero IdentitySorting throughout. Patch ALL events that
            # touch IdentitySorting — decade boundaries (1990, 2000,
            # 2010, 2020) AND the Trump-era bump/revert (2016, 2018).
            for r in eng.rules.rules:
                if type(r).__name__ == "IdentitySorting":
                    r.sort_rate = 0.0
            from abm.pillars.historical_arc import (
                ELITE_DRIFT_SCHEDULE,
                _event_2010_citizens_united,
                _event_2010_social_media_ramp_mid,
                _set_elite_drift_rate,
            )

            def _noop(_eng):
                pass

            def _decade_1990_only_elite(_eng):
                _set_elite_drift_rate(_eng, ELITE_DRIFT_SCHEDULE["1990-00"])

            def _decade_2000_only_elite(_eng):
                _set_elite_drift_rate(_eng, ELITE_DRIFT_SCHEDULE["2000-10"])

            def _decade_2020_only_elite(_eng):
                _set_elite_drift_rate(_eng, ELITE_DRIFT_SCHEDULE["2020-25"])
                # 2020 covid event: keep affect spike, skip IS.
                for r_ in _eng.rules.rules:
                    if type(r_).__name__ == "AffectiveUpdate":
                        _eng.env.attrs["_affect_lr_pre_2020"] = r_.lr
                        r_.lr = r_.lr * 1.5

            def _decade_2010_only_others(_eng):
                _event_2010_citizens_united(_eng)
                _event_2010_social_media_ramp_mid(_eng)

            new_events = []
            for evt in sched.events:
                lbl = evt.label
                if lbl == "decade_1990":
                    new_events.append(type(evt)(
                        evt.tick, lbl, evt.description,
                        _decade_1990_only_elite
                    ))
                elif lbl == "decade_2000":
                    new_events.append(type(evt)(
                        evt.tick, lbl, evt.description,
                        _decade_2000_only_elite
                    ))
                elif lbl == "decade_2010_and_citizens_united":
                    new_events.append(type(evt)(
                        evt.tick, lbl, evt.description,
                        _decade_2010_only_others
                    ))
                elif lbl == "covid_jan6_2020":
                    new_events.append(type(evt)(
                        evt.tick, lbl, evt.description,
                        _decade_2020_only_elite
                    ))
                elif lbl in ("trump_2016", "trump_bump_revert_2018"):
                    # M5 disabled: skip the IdentitySorting bump+revert.
                    new_events.append(type(evt)(
                        evt.tick, lbl, evt.description, _noop
                    ))
                else:
                    new_events.append(evt)
            from abm.pillars.schedule import Schedule
            sched = Schedule(new_events)

        # Run to 2025.
        run_to(eng, sched, final_tick())

        if disable == "M5":
            # Defensively re-zero IdentitySorting in case any event set it.
            for r in eng.rules.rules:
                if type(r).__name__ == "IdentitySorting":
                    r.sort_rate = 0.0

        results["variance"].append(float(variance(eng.positions())))
        results["constraint"].append(constraint_avg(eng))
        results["party_sep"].append(party_sep(eng))
        results["affect"].append(affective_polarization(eng.agents))
        results["xc_fraction"].append(cross_cutting_tie_fraction(
            eng.agents, eng.env.attrs["network"]
        ))
    return {k: float(np.mean(v)) for k, v in results.items()}


def main():
    print("=" * 72)
    print("Phase 8b — mechanism ablation at 2025 end-state")
    print("=" * 72)
    print()

    baseline = measure_2025(disable=None)
    print(f"{'mechanism':<20s}  {'constraint':>10s}  {'party_sep':>10s}  "
          f"{'affect':>10s}  {'variance':>10s}  {'xc_frac':>10s}")
    print(f"{'BASELINE (full)':<20s}  "
          f"{baseline['constraint']:>+10.4f}  {baseline['party_sep']:>+10.4f}  "
          f"{baseline['affect']:>+10.4f}  {baseline['variance']:>+10.4f}  "
          f"{baseline['xc_fraction']:>+10.4f}")
    print()
    print("Δ from baseline when each mechanism is disabled:")
    for m_label, m_id in [
        ("disable M1 hetero", "M1"),
        ("disable M2 Big Sort", "M2"),
        ("disable M3 cohort", "M3"),
        ("disable M4 asymmetric", "M4"),
        ("disable M5 IdentSort", "M5"),
    ]:
        ablated = measure_2025(disable=m_id)
        d_constraint = ablated["constraint"] - baseline["constraint"]
        d_party_sep = ablated["party_sep"] - baseline["party_sep"]
        d_affect = ablated["affect"] - baseline["affect"]
        d_variance = ablated["variance"] - baseline["variance"]
        d_xc = ablated["xc_fraction"] - baseline["xc_fraction"]
        print(f"{m_label:<20s}  "
              f"{d_constraint:>+10.4f}  {d_party_sep:>+10.4f}  "
              f"{d_affect:>+10.4f}  {d_variance:>+10.4f}  "
              f"{d_xc:>+10.4f}")
    print()
    print("=" * 72)


if __name__ == "__main__":
    main()
