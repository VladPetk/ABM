"""Phase 4 §13 — measure-then-bless gate.

Run after Slice 3 to produce the seven numbers the spec asks the human
to sign off on:

  1. F1 effect on S0 — variance drift over TICKS (expect < 5%).
  2. F1 effect on S1 — final variance vs. S0 (expect a clear fall;
     smaller drop than Phase 3).
  3. Canonical HK is untouched (sanity).
  4. F2 effect on the pillar — variance / constraint / ratchet gap with
     F2 on (temperature = 0.05) vs. F2 off (temperature = 0.0).
  5. F3 effect on the network — t=0 cross-cutting tie fraction target band
     18-25%; tune INVOLUNTARY_PER_AGENT if outside.
  6. Re-blessed pillar thresholds — final-S1 variance, S1/S0 ratio,
     S2-S1 constraint gap, S3 paired correlation mean, S4 cross-cutting
     drop, S4 modularity rise, ratchet gap.
  7. Position histogram at S4 end-state — peak / tail counts.

Run: `python scripts/phase4_calibration.py`. Reports to stdout.
"""
from __future__ import annotations

import numpy as np

from abm.metrics.affective import ideological_constraint
from abm.metrics.network import cross_cutting_tie_fraction, party_modularity
from abm.metrics.polarization import variance
from abm.pillars import PILLAR, apply_intervention
from abm.pillars.calm_to_camps import build_engine
from abm.scenarios.compass_basic import build as build_compass

N = 250
TICKS = 200
SEEDS = tuple(range(12))


def positional(stage: int, seed: int):
    eng = build_engine(seed=seed, n_agents=N)
    apply_intervention(eng, PILLAR.interventions[stage])
    for r in eng.rules.rules:
        if type(r).__name__ == "AffectiveUpdate":
            r.lr = 0.0
    return eng


def constraint_avg(eng):
    ic = ideological_constraint(eng.agents)
    return (ic["x"] + ic["y"]) / 2.0


def diet_extremity(agent, outlets_by_id):
    from abm.core.outlets import diet_target
    return float(
        np.linalg.norm(diet_target(agent.state.attrs["media_diet"], outlets_by_id))
    )


def party_sep(eng):
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    return float(
        np.linalg.norm(pos[parties == 0].mean(axis=0) - pos[parties == 1].mean(axis=0))
    )


def measure_stage(stage: int, also_engines: bool = False):
    inits, finals, eng_out = [], [], []
    for seed in SEEDS:
        eng = positional(stage, seed)
        v0 = variance(eng.positions())
        eng.run(TICKS)
        v1 = variance(eng.positions())
        inits.append(v0)
        finals.append(v1)
        if also_engines:
            eng_out.append(eng)
    return (inits, finals, eng_out)


def main():
    print("=" * 72)
    print("Phase 4 §13 measure-then-bless")
    print(f"  N={N}, TICKS={TICKS}, seeds=0..{SEEDS[-1]}")
    print("=" * 72)

    # ----------------------------------------------------------------- F3.5
    # Network shape at t=0 — the F3a calibration gate. Report this FIRST
    # so the human can decide whether to tune INVOLUNTARY_PER_AGENT before
    # we burn 30 minutes on the other measurements.
    print("\n[F3.5] Network shape at t=0 (the calibration gate)")
    xc_t0, deg_t0, inv_t0 = [], [], []
    for seed in SEEDS:
        eng = build_engine(seed=seed, n_agents=N)
        net = eng.env.attrs["network"]
        xc_t0.append(cross_cutting_tie_fraction(eng.agents, net))
        deg_t0.append(np.mean([net.degree(a.id) for a in eng.agents]))
        inv_t0.append(
            sum(1 for (i, j) in net.edges() if net.is_involuntary(i, j))
        )
    print(f"  Mean cross-cutting fraction t=0:   {np.mean(xc_t0):.3f} "
          f"(target band 0.18-0.25)")
    print(f"  Mean degree:                       {np.mean(deg_t0):.2f}")
    print(f"  Mean involuntary edge count:       {np.mean(inv_t0):.1f}")
    print(f"  Per-seed XC: {[round(x, 3) for x in xc_t0]}")

    # ----------------------------------------------------------------- F1
    print("\n[F1] Pillar stages under F1+F2+F3")
    s0 = measure_stage(0)
    print(f"  S0 drift (final/initial mean): "
          f"{np.mean(s0[1]) / np.mean(s0[0]):.3f} "
          f"(expect within ±5% of 1.0)")
    print(f"  S0 final variance mean:      {np.mean(s0[1]):.3f}")

    s1 = measure_stage(1)
    print(f"  S1 final variance mean:      {np.mean(s1[1]):.3f}")
    print(f"  S1/S0 variance ratio:        {np.mean(s1[1]) / np.mean(s0[1]):.3f} "
          f"(expect <1 but greater than Phase 3's ~0.83)")

    # ----------------------------------------------------------------- F2
    print("\n[F2] Pillar with F2 off (temperature=0.0)")
    # Compare S1 with and without graded filter.
    s1_off_finals = []
    for seed in SEEDS:
        eng = positional(1, seed)
        for r in eng.rules.rules:
            if type(r).__name__ == "BoundedConfidenceInfluence":
                r.temperature = 0.0
        eng.run(TICKS)
        s1_off_finals.append(variance(eng.positions()))
    print(f"  S1 final variance (F2 off):  {np.mean(s1_off_finals):.3f}")
    print(f"  S1 final variance (F2 on):   {np.mean(s1[1]):.3f}")
    print(f"  Ratio F2-on / F2-off:        "
          f"{np.mean(s1[1]) / np.mean(s1_off_finals):.3f}")

    # ----------------------------------------------------------------- S2, S3
    s2 = measure_stage(2, also_engines=True)
    print(f"\n[S2] Final variance mean:      {np.mean(s2[1]):.3f}")
    s2_constraint = [constraint_avg(e) for e in s2[2]]
    s1_constraint = []
    for seed in SEEDS:
        eng = positional(1, seed)
        eng.run(TICKS)
        s1_constraint.append(constraint_avg(eng))
    print(f"  S1 constraint mean:          {np.mean(s1_constraint):.3f}")
    print(f"  S2 constraint mean:          {np.mean(s2_constraint):.3f}")
    print(f"  S2 - S1 constraint gap:      "
          f"{np.mean(s2_constraint) - np.mean(s1_constraint):+.3f}")

    s3 = measure_stage(3, also_engines=True)
    print(f"\n[S3] Final variance mean:      {np.mean(s3[1]):.3f}")
    from abm.core.outlets import US_MEDIA_OUTLETS_2024
    outlets_by_id = {o.id: o for o in US_MEDIA_OUTLETS_2024}
    corrs = []
    for eng2, eng3 in zip(s2[2], s3[2]):
        r2 = np.array([np.linalg.norm(a.state.ideology) for a in eng2.agents])
        r3 = np.array([np.linalg.norm(a.state.ideology) for a in eng3.agents])
        eff = r3 - r2
        ext = np.array([diet_extremity(a, outlets_by_id) for a in eng3.agents])
        if eff.std() > 0 and ext.std() > 0:
            corrs.append(float(np.corrcoef(ext, eff)[0, 1]))
    print(f"  Paired correlation mean:     {np.mean(corrs):.3f}")
    print(f"  Per-seed: {[round(c, 3) for c in corrs]}")

    # ----------------------------------------------------------------- S4
    s4 = measure_stage(4, also_engines=True)
    print(f"\n[S4] Final variance mean:      {np.mean(s4[1]):.3f}")
    xc_after = [cross_cutting_tie_fraction(e.agents, e.env.attrs["network"])
                for e in s4[2]]
    mod_after = [party_modularity(e.agents, e.env.attrs["network"])
                 for e in s4[2]]
    # Re-compute t=0 modularity for the comparison.
    mod_t0 = []
    for seed in SEEDS:
        eng = build_engine(seed=seed, n_agents=N)
        mod_t0.append(party_modularity(eng.agents, eng.env.attrs["network"]))
    print(f"  Cross-cutting drop t=0 -> S4: "
          f"{np.mean(xc_t0):.3f} -> {np.mean(xc_after):.3f} "
          f"(drop {np.mean(xc_t0) - np.mean(xc_after):+.3f})")
    print(f"  Modularity rise t=0 -> S4:   "
          f"{np.mean(mod_t0):.3f} -> {np.mean(mod_after):.3f} "
          f"(rise {np.mean(mod_after) - np.mean(mod_t0):+.3f})")
    inv_after = []
    for e in s4[2]:
        net = e.env.attrs["network"]
        inv_after.append(
            sum(1 for (i, j) in net.edges() if net.is_involuntary(i, j))
        )
    print(f"  Involuntary edges preserved: "
          f"t=0 mean {np.mean(inv_t0):.1f} -> S4 mean {np.mean(inv_after):.1f} "
          f"({'OK' if np.allclose(inv_t0, inv_after) else 'CHANGED'})")

    # Party separation (the ratchet headline number, before release).
    sep_s4 = [party_sep(e) for e in s4[2]]
    print(f"  Party separation at S4 end:  {np.mean(sep_s4):.3f}")

    # ----------------------------------------------------------------- Position histogram
    print("\n[S4 position histogram — does the society collapse?]")
    radii = []
    for e in s4[2]:
        r = np.array([np.linalg.norm(a.state.ideology) for a in e.agents])
        radii.append(r)
    radii = np.concatenate(radii)
    print(f"  Total agents counted: {len(radii)}")
    print(f"  Within 0.20 of centre: {(radii < 0.20).mean():.3f}")
    print(f"  Between 0.20 and 0.50: "
          f"{((radii >= 0.20) & (radii < 0.50)).mean():.3f}")
    print(f"  Between 0.50 and 0.80: "
          f"{((radii >= 0.50) & (radii < 0.80)).mean():.3f}")
    print(f"  At or past 0.80:      {(radii >= 0.80).mean():.3f}")

    # ----------------------------------------------------------------- Canonical
    print("\n[Canonical HK suite — sanity check, must be unchanged]")
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
    print("Done.")


if __name__ == "__main__":
    main()
