"""T2.5 instrument — pillar scale re-pick on the issues substrate.

The D=7 rebuild shifted two scales: item-space pair distances are
inflated by within-block residual texture (BC partially starved at
eps=0.30 — the pillar-side twin of the T0.6 arc finding), and the
block-means lens compresses the projection's within-party SD. This sweep
measures the two failing pinned quantities (S1 variance ratio < 0.92;
S2-end within-party SD_x in [0.14, 0.30]) plus collateral quantities
(S2-S1 constraint gap, pooled |r| bundling) across a small
(bc_epsilon, party_cue_sigma) grid, mirroring the test protocols
exactly (N=250, TICKS=200; positional engines for variance/constraint,
affect-on for wp_sd).

Run:  .venv/Scripts/python.exe scripts/audit/t25_pillar_repick.py
Writes docs/internal/audit/t25_pillar_repick.json
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from abm.calibration_parallel import run_seeds_parallel

N = 250
TICKS = 200
SEEDS = list(range(12))
EPS_GRID = (0.30, 0.35, 0.40)
SIGMA_GRID = (0.25, 0.30, 0.35)


def _engine(stage, seed, eps, sigma_pc, positional):
    import abm.pillars.calm_to_camps as cc
    from abm.pillars import PILLAR, apply_intervention
    cc.PARTY_CUE_SIGMA = sigma_pc          # build-time constant override
    eng = cc.build_engine(seed=seed, n_agents=N)
    apply_intervention(eng, PILLAR.interventions[stage])
    for r in eng.rules.rules:
        name = type(r).__name__
        if name == "BoundedConfidenceInfluence":
            r.epsilon = eps
            if positional:
                r.affect_weight = 0.0
        elif positional and name == "AffectiveUpdate":
            r.lr = 0.0
        elif positional and name == "BacklashRepulsion":
            r.strength = 0.0
    if positional:
        for r in eng.env_rules:
            if type(r).__name__ == "TieRewiring":
                r.affect_weight_rewire = 0.0
    return eng


def worker(args):
    seed, eps, sigma_pc = args
    from abm.metrics.polarization import variance
    from abm.metrics.affective import ideological_constraint

    def _constraint(e):
        ic = ideological_constraint(e.agents)
        return (ic["x"] + ic["y"]) / 2.0

    def _mean_abs_r(e):
        V = np.array([a.state.attrs["issues"] for a in e.agents])
        C = np.nan_to_num(np.corrcoef(V, rowvar=False), nan=0.0)
        return float(np.abs(C[np.triu_indices(7, 1)]).mean())

    out = {}
    e0 = _engine(0, seed, eps, sigma_pc, positional=True)
    e0.run(TICKS)
    out["s0_var"] = variance(e0.positions())

    e1 = _engine(1, seed, eps, sigma_pc, positional=True)
    e1.run(TICKS)
    out["s1_var"] = variance(e1.positions())
    out["s1_constraint"] = _constraint(e1)

    e2 = _engine(2, seed, eps, sigma_pc, positional=True)
    e2.run(TICKS)
    out["s2_constraint"] = _constraint(e2)
    out["s2_abs_r"] = _mean_abs_r(e2)

    # wp_sd protocol: affect ON (mirrors s2_within_party_sd_worker)
    e2a = _engine(2, seed, eps, sigma_pc, positional=False)
    e2a.run(TICKS)
    parties = np.array([a.state.attrs["party"] for a in e2a.agents])
    pos = e2a.positions()
    out["wp_sd_x_p0"] = float(pos[parties == 0, 0].std())
    out["wp_sd_x_p1"] = float(pos[parties == 1, 0].std())
    return out


def main():
    work = [(s, e, sg) for e in EPS_GRID for sg in SIGMA_GRID for s in SEEDS]
    flat = run_seeds_parallel(worker, work)

    cells = {}
    for (s, e, sg), r in zip(work, flat):
        cells.setdefault((e, sg), []).append(r)

    summary = {}
    print(f"{'eps':>5s} {'s_pc':>5s} | {'S1/S0':>6s} {'wp0':>6s} {'wp1':>6s} "
          f"{'cgap':>6s} {'|r|S2':>6s}")
    for (e, sg), runs in cells.items():
        m = {k: float(np.mean([r[k] for r in runs])) for k in runs[0]}
        ratio = m["s1_var"] / m["s0_var"]
        cgap = m["s2_constraint"] - m["s1_constraint"]
        summary[f"eps{e}_sig{sg}"] = {**{k: round(v, 4) for k, v in m.items()},
                                      "s1_ratio": round(ratio, 4),
                                      "cgap": round(cgap, 4)}
        flag = " <-- " if (ratio < 0.90 and m["wp_sd_x_p0"] >= 0.145
                          and m["wp_sd_x_p1"] >= 0.145 and cgap > 0.02) else ""
        print(f"{e:>5.2f} {sg:>5.2f} | {ratio:>6.3f} {m['wp_sd_x_p0']:>6.3f} "
              f"{m['wp_sd_x_p1']:>6.3f} {cgap:>6.3f} {m['s2_abs_r']:>6.3f}{flag}")

    outp = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..",
        "docs", "internal", "audit", "t25_pillar_repick.json"))
    with open(outp, "w") as f:
        json.dump({"seeds": SEEDS, "n": N, "ticks": TICKS,
                   "summary": summary}, f, indent=2)
    print(f"wrote {outp}")


if __name__ == "__main__":
    main()
