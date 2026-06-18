"""Audit probe: measure the per-tick magnitude of each position-moving rule's
emitted StateDelta in the CANONICAL build, to test whether
BoundedConfidenceInfluence is a live convergence force or effectively inert.

Read-only: builds the engine via the public build_engine + ANES_FULL_KWARGS,
runs it forward, and at selected ticks re-applies each rule individually
against the pre-tick snapshot to read its raw d_attrs['issues'] / d_ideology.
Does NOT mutate the committed engine; uses a private rng clone so the probe
does not perturb the run.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import numpy as np
from abm.pillars.historical_arc import build_engine
from scripts.anes_preset import ANES_FULL_KWARGS
from abm.core.issues import issues_of

POS_RULES = ["BoundedConfidenceInfluence", "PartyPull", "MediaConsumption",
             "ConstraintOp", "IdentityToIdeologyPull", "GaussianNoise",
             "FactionAnchor", "BacklashRepulsion"]

def rule_name(r):
    return type(r).__name__

def probe_tick(engine, year):
    """For each position-moving rule, compute its emitted issue-space delta for
    every agent against the current (pre-step) snapshot. Returns dict
    name -> rms over agents of ||delta||."""
    out = {}
    rt = engine.env.attrs.get("issue_runtime")
    D = rt["D"] if rt else 2
    # private rng so we don't consume the engine's stream
    probe_rng = np.random.default_rng(12345)
    for r in engine.rules.rules:
        nm = rule_name(r)
        if nm not in POS_RULES:
            continue
        mags = []
        for agent in engine.agents:
            d = r.apply(agent, engine.space, engine.env, probe_rng)
            dv = d.d_attrs.get("issues")
            if dv is None:
                di = d.d_ideology
                if di is None or not np.any(di):
                    mags.append(0.0)
                    continue
                # lift 2D to issue space magnitude-equivalently: just use norm
                mags.append(float(np.linalg.norm(di)))
            else:
                mags.append(float(np.linalg.norm(dv)))
        out[nm] = (float(np.mean(mags)), float(np.max(mags)))
    return out

def main():
    engine = build_engine(seed=0, **ANES_FULL_KWARGS)
    # report which rules are present + key BC params
    for r in engine.rules.rules:
        nm = rule_name(r)
        if nm == "BoundedConfidenceInfluence":
            print(f"BC: epsilon={r.epsilon} strength={r.strength} "
                  f"temperature={r.temperature} affect_weight={r.affect_weight}")
        if nm == "ConstraintOp":
            print(f"ConstraintOp: rate={r.rate} resid_sigma={r.resid_sigma}")
        if nm == "MediaConsumption":
            print(f"MediaConsumption: strength={r.strength}")
        if nm == "PartyPull":
            print(f"PartyPull: strength={r.strength}")

    checkpoints = {0: 1980, 30: 1990, 60: 2000, 90: 2010, 120: 2020, 135: 2025}
    results = {}
    for tick in range(0, 136):
        if tick in checkpoints:
            yr = checkpoints[tick]
            # env-phase has been run as part of step; probe AFTER stepping to tick
            results[yr] = probe_tick(engine, yr)
        if tick < 135:
            engine.step()

    print("\n=== per-tick rule emitted-delta magnitude (mean ||d|| over agents, [max]) ===")
    header = "year     " + "".join(f"{n[:12]:>14}" for n in POS_RULES)
    print(header)
    for yr in sorted(results):
        row = f"{yr:<8} "
        for n in POS_RULES:
            if n in results[yr]:
                mean, mx = results[yr][n]
                row += f"{mean:>9.5f}/{mx:.3f}"
            else:
                row += f"{'--':>14}"
        print(row)

    # also: env-attr media_strength / bc_affect_weight at each checkpoint to see
    # what the data-fed channel injects
    print("\n=== env-fed channel values (re-run, reading env.attrs) ===")
    eng2 = build_engine(seed=0, **ANES_FULL_KWARGS)
    for tick in range(0, 136):
        if tick in checkpoints:
            print(f"{checkpoints[tick]}: media_strength="
                  f"{eng2.env.attrs.get('media_strength')} "
                  f"bc_affect_weight={eng2.env.attrs.get('bc_affect_weight')} "
                  f"media_diet_outlets={len(eng2.env.attrs.get('outlets') or {})}")
        if tick < 135:
            eng2.step()

if __name__ == "__main__":
    main()
