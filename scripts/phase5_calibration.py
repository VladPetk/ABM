"""Phase 5 §11 — measure-then-bless gate.

Produces the seven numbers the spec asks the human to sign off on:

  1. A1 sign-fix: affective_polarization at S2, S3, S4 ensemble means
     (expect monotonically *decreasing*, i.e. more out-party animus).
  2. Iyengar gap: |d-affect| vs d-constraint across S0→S3.
  3. A4 modulator effect: S4 with affect_weight=0.3 vs 0.0
     (final variance, party separation, cross-cutting, modularity).
  4. A5 rewiring effect: S4 with affect_weight_rewire=0.30 vs 0.0
     (cross-cutting drop).
  5. Phase 4 thresholds re-blessed.
  6. Canonical HK suite is untouched (sanity).
  7. S4 position histogram (no-collapse check).
"""
from __future__ import annotations

import numpy as np

from abm.metrics.affective import affective_polarization, ideological_constraint
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
    return eng


def constraint_avg(eng):
    ic = ideological_constraint(eng.agents)
    return (ic["x"] + ic["y"]) / 2.0


def party_sep(eng):
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    return float(
        np.linalg.norm(pos[parties == 0].mean(axis=0) - pos[parties == 1].mean(axis=0))
    )


def diet_extremity(agent, outlets_by_id):
    from abm.core.outlets import diet_target
    return float(
        np.linalg.norm(diet_target(agent.state.attrs["media_diet"], outlets_by_id))
    )


def run_stage(stage, ticks=TICKS, also_engines=False):
    inits, finals, eng_out = [], [], []
    for seed in SEEDS:
        eng = positional(stage, seed)
        v0 = variance(eng.positions())
        eng.run(ticks)
        v1 = variance(eng.positions())
        inits.append(v0)
        finals.append(v1)
        if also_engines:
            eng_out.append(eng)
    return inits, finals, eng_out


def main():
    print("=" * 72)
    print("Phase 5 §11 measure-then-bless")
    print(f"  N={N}, TICKS={TICKS}, seeds=0..{SEEDS[-1]}")
    print("=" * 72)

    print("\n[A1] Sign-fix — affective_polarization through stages")
    affects, constraints = {}, {}
    s0_engines = []
    for stage in range(5):
        affs, cons = [], []
        for seed in SEEDS:
            eng = positional(stage, seed)
            eng.run(TICKS)
            affs.append(affective_polarization(eng.agents))
            cons.append(constraint_avg(eng))
            if stage == 0:
                s0_engines.append(eng)
        affects[stage] = np.mean(affs)
        constraints[stage] = np.mean(cons)
        print(f"  S{stage}: affective_polarization mean = {affects[stage]:+.4f}, "
              f"ideological_constraint mean = {constraints[stage]:.4f}")

    print(f"\n[Iyengar gap] S0 -> S3:")
    d_aff = abs(affects[3] - affects[0])
    d_con = constraints[3] - constraints[0]
    print(f"  ||d-affective_polarization|: {d_aff:.4f}")
    print(f"   d-ideological_constraint:  {d_con:+.4f}")
    print(f"   Affect / Constraint ratio: {d_aff / max(d_con, 1e-9):.3f}")
    print(f"  (Pass condition: |d-affect| > d-constraint — Iyengar et al. 2019)")

    # ---------------- A4 modulator effect: affect_weight 0.3 vs 0.0 -----
    print("\n[A4] Modulator effect: BC.affect_weight 0.3 vs 0.0")
    for weight in (0.0, 0.3):
        s4_finals, s4_engs = [], []
        for seed in SEEDS:
            eng = positional(4, seed)
            for r in eng.rules.rules:
                if type(r).__name__ == "BoundedConfidenceInfluence":
                    r.affect_weight = weight
            eng.run(TICKS)
            s4_finals.append(variance(eng.positions()))
            s4_engs.append(eng)
        xcs = [cross_cutting_tie_fraction(e.agents, e.env.attrs["network"]) for e in s4_engs]
        mods = [party_modularity(e.agents, e.env.attrs["network"]) for e in s4_engs]
        seps = [party_sep(e) for e in s4_engs]
        print(f"  affect_weight={weight}: "
              f"variance {np.mean(s4_finals):.3f}, "
              f"party sep {np.mean(seps):.3f}, "
              f"XC {np.mean(xcs):.3f}, "
              f"mod {np.mean(mods):.3f}")

    # ---------------- A5 rewiring effect: TR.affect_weight_rewire 0.30 vs 0.0 ----
    print("\n[A5] Rewiring effect: TR.affect_weight_rewire 0.30 vs 0.0")
    for weight in (0.0, 0.30):
        s4_engs = []
        for seed in SEEDS:
            eng = positional(4, seed)
            for r in eng.env_rules:
                if type(r).__name__ == "TieRewiring":
                    r.affect_weight_rewire = weight
            eng.run(TICKS)
            s4_engs.append(eng)
        xcs = [cross_cutting_tie_fraction(e.agents, e.env.attrs["network"]) for e in s4_engs]
        mods = [party_modularity(e.agents, e.env.attrs["network"]) for e in s4_engs]
        print(f"  affect_weight_rewire={weight}: "
              f"XC {np.mean(xcs):.3f}, "
              f"mod {np.mean(mods):.3f}")

    # ---------------- Re-measure all Phase 4 thresholds -------------------
    print("\n[Phase 4 re-bless] Pillar thresholds at S0..S4")
    s0 = run_stage(0)
    print(f"  S0 drift (final/initial mean): "
          f"{np.mean(s0[1]) / np.mean(s0[0]):.3f} (expect ~1.0)")
    s1 = run_stage(1)
    print(f"  S1/S0 variance ratio: {np.mean(s1[1]) / np.mean(s0[1]):.3f} "
          f"(threshold 0.92)")
    s2 = run_stage(2, also_engines=True)
    s1_constraint = [constraint_avg(e) for e in [positional(1, seed) for seed in SEEDS]]
    # Re-run S1 to get end-of-S1 constraint:
    s1_eng = []
    for seed in SEEDS:
        eng = positional(1, seed)
        eng.run(TICKS)
        s1_eng.append(eng)
    s1_constraint = [constraint_avg(e) for e in s1_eng]
    s2_constraint = [constraint_avg(e) for e in s2[2]]
    print(f"  S2 - S1 constraint gap: "
          f"{np.mean(s2_constraint) - np.mean(s1_constraint):+.3f} "
          f"(threshold +0.02)")

    s3 = run_stage(3, also_engines=True)
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
    print(f"  S3 paired correlation mean: {np.mean(corrs):.3f} "
          f"(threshold 0.10); seeds-positive: "
          f"{sum(1 for c in corrs if c > 0)}/{len(corrs)} (threshold 9)")

    s4 = run_stage(4, also_engines=True)
    xc_t0, mod_t0 = [], []
    for seed in SEEDS:
        eng = build_engine(seed=seed, n_agents=N)
        net = eng.env.attrs["network"]
        xc_t0.append(cross_cutting_tie_fraction(eng.agents, net))
        mod_t0.append(party_modularity(eng.agents, net))
    xc_after = [cross_cutting_tie_fraction(e.agents, e.env.attrs["network"]) for e in s4[2]]
    mod_after = [party_modularity(e.agents, e.env.attrs["network"]) for e in s4[2]]
    print(f"  XC drop t=0 -> S4: {np.mean(xc_t0):.3f} -> {np.mean(xc_after):.3f} "
          f"(drop {np.mean(xc_t0) - np.mean(xc_after):+.3f}; threshold 0.10)")
    print(f"  Modularity rise t=0 -> S4: {np.mean(mod_t0):.3f} -> {np.mean(mod_after):.3f} "
          f"(rise {np.mean(mod_after) - np.mean(mod_t0):+.3f}; threshold 0.10)")

    print("\n[S4 position histogram — no-collapse check]")
    radii = []
    for e in s4[2]:
        r = np.array([np.linalg.norm(a.state.ideology) for a in e.agents])
        radii.append(r)
    radii = np.concatenate(radii)
    print(f"  Within 0.20 of centre: {(radii < 0.20).mean():.3f}")
    print(f"  Between 0.20 and 0.50: {((radii >= 0.20) & (radii < 0.50)).mean():.3f}")
    print(f"  Between 0.50 and 0.80: {((radii >= 0.50) & (radii < 0.80)).mean():.3f}")
    print(f"  At or past 0.80:      {(radii >= 0.80).mean():.3f}")

    # ---------------- Canonical HK suite (sanity) ----------------------
    print("\n[Canonical HK] eps sweep — must be unchanged")
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
