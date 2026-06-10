"""S1 addendum — robustness investigation of the covariance-signature pilot.

Standalone, pure-numpy, NO engine changes. Reuses the substrate/operators of
`pilot_cov_signature.py` unchanged (imports them; does not modify the original
artifact or its generator).

Motivation: the pilot's PRIMARY gate passed, but the robustness cut (cosine
WITHOUT party_sep, scale-free weighting) came in at 0.488 (D=7) / 0.485 (D=10)
vs the 0.45 line. Decomposing the stored Jacobians shows the overlap is carried
by (a) an *interaction* term — party_pull alone provably does not move
within-party PR (signature deltas ~1e-16), but at the joint operating point it
catalyzes constraint_op's collapse by aligning the neighbourhood consensus
axes, so d(within_pr)/d(s_pp) < 0 — and (b) a thin 3-observable vector in which
the row-normalizing scale-free weighting inflates near-null rows. The pilot
also computed but did not include bg_issue_pooled / per-party variants in the
cosine vector, although mhv_spec S1 P4 lists them.

This addendum answers three questions:
  Q1. Does the no-party_sep cosine drop back under 0.45 once the observable
      vector carries the spec's full P4 list (per-party PR, per-party
      constraint, B&G dual incl. bg_issue_pooled)?
  Q2. Is the 0.488 knife-edge in the operating point, or robust across
      (s_pp, s_co) combinations?
  Q3. Is the within_pr overlap really an interaction (vanishes at s_co=0)
      rather than a direct effect of party_pull?

Run:  .venv/Scripts/python.exe scripts/audit/pilot_cov_addendum.py
Writes docs/internal/audit/pilot_cov_addendum.{json,md}
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

import numpy as np

import pilot_cov_signature as base

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_JSON = os.path.join(ROOT, "docs", "internal", "audit", "pilot_cov_addendum.json")
OUT_MD = os.path.join(ROOT, "docs", "internal", "audit", "pilot_cov_addendum.md")

SEEDS = list(range(16))          # doubled vs pilot's 8 for tighter FD means
FD_REL = base.FD_REL             # same +-20% central FD step
# Q2 grid: symmetric sweep + asymmetric points around the pilot's (0.04, 0.04)
OP_POINTS = [(0.02, 0.02), (0.04, 0.04), (0.08, 0.08), (0.02, 0.04), (0.04, 0.02)]

# observable key sets ------------------------------------------------------- #
# enriched per spec P4: party_sep + per-party PR + per-party constraint +
# B&G dual (partisan + pooled issue alignment). within_pr / constraint means
# kept alongside so the pilot's original thin sets are computable from the
# same Jacobian (derivative of a mean = mean of derivatives).
ALL_KEYS = ["party_sep", "pr_dem", "pr_rep", "con_dem", "con_rep",
            "bg_partisan", "bg_issue_pooled", "within_pr", "constraint"]
SETS = {
    "enriched_with_partysep": ["party_sep", "pr_dem", "pr_rep", "con_dem",
                               "con_rep", "bg_partisan", "bg_issue_pooled"],
    "enriched_without_partysep": ["pr_dem", "pr_rep", "con_dem", "con_rep",
                                  "bg_partisan", "bg_issue_pooled"],
    # the pilot's original sets, for like-for-like comparison
    "thin_with_partysep": ["party_sep", "within_pr", "constraint", "bg_partisan"],
    "thin_without_partysep": ["within_pr", "constraint", "bg_partisan"],
}


def enriched_obs(V, party, p_dir):
    D = V.shape[1]
    mD, mR = V[party == 0].mean(0), V[party == 1].mean(0)
    party_sep = float(np.linalg.norm(mD - mR))
    prs, cons = [], []
    for pv in (0, 1):
        C = base._corr(V[party == pv])
        prs.append(base._pr(C))
        off = C[np.triu_indices(D, k=1)]
        cons.append(float(np.mean(np.abs(off))))
    composite = V @ p_dir
    lab = np.where(party == 1, 1.0, -1.0)
    bg_partisan = float(abs(np.corrcoef(composite, lab)[0, 1]))
    Cp = base._corr(V)
    bg_issue_pooled = float(np.mean(np.abs(Cp[np.triu_indices(D, k=1)])))
    return {
        "party_sep": party_sep,
        "pr_dem": prs[0], "pr_rep": prs[1],
        "con_dem": cons[0], "con_rep": cons[1],
        "bg_partisan": bg_partisan,
        "bg_issue_pooled": bg_issue_pooled,
        "within_pr": float(np.mean(prs)),
        "constraint": float(np.mean(cons)),
    }


def _vec(ob):
    return np.array([ob[k] for k in ALL_KEYS])


def _cos(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return float("nan")
    return float(np.dot(a, b) / (na * nb))


def jacobian_at(C, spp0, sco0):
    """Central-FD Jacobian columns of the full observable vector at the joint
    operating point (spp0, sco0), averaged over SEEDS; plus seed-SD of the
    observable vector at the point (for SD-standardization)."""
    Jpp, Jco, base_vecs = [], [], []
    for seed in SEEDS:
        rng = np.random.default_rng(5000 + seed)
        V0, party, Arow, p_dir = base.make_substrate(C, rng)
        targets = base.make_targets(p_dir)

        def obs_at(spp, sco):
            return _vec(enriched_obs(
                base.run(V0, party, Arow, targets, spp, sco), party, p_dir))

        hp, hc = FD_REL * spp0, FD_REL * sco0
        Jpp.append((obs_at(spp0 + hp, sco0) - obs_at(spp0 - hp, sco0)) / (2 * hp))
        Jco.append((obs_at(spp0, sco0 + hc) - obs_at(spp0, sco0 - hc)) / (2 * hc))
        base_vecs.append(obs_at(spp0, sco0))
    Jpp, Jco = np.array(Jpp), np.array(Jco)
    sd = np.std(np.array(base_vecs), axis=0)
    floor = max(np.median(sd), 1e-6)
    sd_floored = np.maximum(sd, floor * 1e-3)
    return Jpp.mean(0), Jco.mean(0), sd_floored


def cosines_for_sets(jpp, jco, sd_floored):
    out = {}
    for setname, keys in SETS.items():
        idx = [ALL_KEYS.index(k) for k in keys]
        kp, kc = jpp[idx], jco[idx]
        w_sd = 1.0 / sd_floored[idx]
        c_sd = _cos(kp * w_sd, kc * w_sd)
        row = np.sqrt(kp ** 2 + kc ** 2)
        w_sf = 1.0 / np.maximum(row, 1e-12)
        c_sf = _cos(kp * w_sf, kc * w_sf)
        out[setname] = {"sd_standardized": c_sd, "scale_free": c_sf}
    return out


def interaction_check(C):
    """Q3: d(within_pr)/d(s_pp) with constraint OFF vs ON (s_co = 0 / 0.04),
    at s_pp = 0.04. If the overlap is an interaction, the s_co=0 derivative
    is ~0 and the s_co=0.04 derivative is the pilot's -6.2-ish value."""
    out = {}
    for sco in (0.0, 0.04):
        ds = []
        for seed in SEEDS:
            rng = np.random.default_rng(7000 + seed)
            V0, party, Arow, p_dir = base.make_substrate(C, rng)
            targets = base.make_targets(p_dir)

            def pr_at(spp):
                return enriched_obs(
                    base.run(V0, party, Arow, targets, spp, sco),
                    party, p_dir)["within_pr"]

            h = FD_REL * 0.04
            ds.append((pr_at(0.04 + h) - pr_at(0.04 - h)) / (2 * h))
        ds = np.array(ds)
        out[f"sco={sco:g}"] = {
            "d_withinpr_d_spp_mean": float(ds.mean()),
            "d_withinpr_d_spp_sd": float(ds.std()),
            "snr": float(abs(ds.mean()) / (ds.std() + 1e-12)),
        }
    return out


def run_for_D(D):
    if D == 7:
        C, _, _ = base.build_real_ic_1986()
        ic_path = "real_anes_1986"
    else:
        C, _, _ = base.build_synthetic_ic(D)
        ic_path = "synthetic"
    print(f"[D={D}] ic_path={ic_path}")
    points = {}
    for (spp0, sco0) in OP_POINTS:
        jpp, jco, sd = jacobian_at(C, spp0, sco0)
        points[f"spp={spp0:g},sco={sco0:g}"] = {
            "jpp_mean": jpp.tolist(), "jco_mean": jco.tolist(),
            "sd": sd.tolist(),
            "cosines": cosines_for_sets(jpp, jco, sd),
        }
        print(f"  op point ({spp0:g},{sco0:g}) done")
    inter = interaction_check(C)
    return {"D": D, "ic_path": ic_path, "operating_points": points,
            "interaction_check": inter}


def write_md(out):
    L = []
    A = L.append
    A("# S1 addendum - robustness investigation of the cov-signature pilot\n")
    A("*Generated by `scripts/audit/pilot_cov_addendum.py`. Companion to "
      "[`pilot_cov_signature.md`](pilot_cov_signature.md); same substrate and "
      "operators, 16 seeds. No engine changes.*\n")
    A("\nThe pilot's marginal cell was the no-party_sep / scale-free cosine "
      "(0.488 / 0.485 vs the 0.45 line). Three questions: (Q1) does the spec's "
      "full P4 observable list fix it; (Q2) is it knife-edge in the operating "
      "point; (Q3) is the within-PR overlap an interaction term rather than a "
      "direct party_pull effect?\n")

    A("\n## Q1+Q2: cosine grid (operating point x observable set)\n")
    A("\nObservable sets: **enriched** = party_sep, PR(dem), PR(rep), "
      "constraint(dem), constraint(rep), B&G partisan, B&G issue pooled "
      "(the spec P4 list); **thin** = the pilot's original 4-vector.\n")
    for tag in ("D7", "D10"):
        r = out["results"][tag]
        A(f"\n### D={r['D']} ({r['ic_path']})\n")
        A("\n| op point (s_pp, s_co) | set | SD-standardized | scale-free |")
        A("|---|---|---|---|")
        for pt, pd in r["operating_points"].items():
            for setname in ("enriched_with_partysep", "enriched_without_partysep",
                            "thin_with_partysep", "thin_without_partysep"):
                c = pd["cosines"][setname]
                A(f"| {pt} | {setname} | {c['sd_standardized']:.3f} | "
                  f"{c['scale_free']:.3f} |")

    A("\n## Q3: interaction check - d(within_pr)/d(s_pp) with constraint off/on\n")
    A("\n| D | s_co | d(within_pr)/d(s_pp) mean | seed SD | SNR |")
    A("|---|---|---|---|---|")
    for tag in ("D7", "D10"):
        r = out["results"][tag]
        for sco, v in r["interaction_check"].items():
            A(f"| {r['D']} | {sco} | {v['d_withinpr_d_spp_mean']:+.3f} | "
              f"{v['d_withinpr_d_spp_sd']:.3f} | {v['snr']:.2f} |")

    A("\n## Summary\n")
    A(out["summary"])
    with open(OUT_MD, "w") as f:
        f.write("\n".join(L))


def summarize(res):
    """Worst no-party_sep cosine per set across the grid, both D."""
    worst = {"enriched_without_partysep": 0.0, "thin_without_partysep": 0.0}
    at = {k: "" for k in worst}
    for tag in ("D7", "D10"):
        for pt, pd in res[tag]["operating_points"].items():
            for setname in worst:
                for wt in ("sd_standardized", "scale_free"):
                    v = abs(pd["cosines"][setname][wt])
                    if v > worst[setname]:
                        worst[setname] = v
                        at[setname] = f"{tag} {pt} {wt}"
    lines = []
    for setname in worst:
        lines.append(f"- worst |cosine| {setname}: **{worst[setname]:.3f}** "
                     f"(at {at[setname]})")
    inter7 = res["D7"]["interaction_check"]
    lines.append(
        f"- interaction: D=7 d(within_pr)/d(s_pp) = "
        f"{inter7['sco=0']['d_withinpr_d_spp_mean']:+.3f} at s_co=0 vs "
        f"{inter7['sco=0.04']['d_withinpr_d_spp_mean']:+.3f} at s_co=0.04 -> "
        f"{'interaction-mediated (vanishes when constraint is off)' if abs(inter7['sco=0']['d_withinpr_d_spp_mean']) < 0.1 * abs(inter7['sco=0.04']['d_withinpr_d_spp_mean']) else 'NOT purely interaction-mediated - investigate'}")
    return "\n".join(lines)


def main():
    base._assert_constraint_not_centroid()
    res = {"D7": run_for_D(7), "D10": run_for_D(10)}
    out = {
        "spec": "docs/internal/mhv_spec.md S1 addendum (robustness investigation)",
        "config": {"n_agents": base.N_AGENTS, "horizon": base.HORIZON,
                   "seeds": SEEDS, "fd_rel": FD_REL, "op_points": OP_POINTS,
                   "observable_sets": SETS},
        "results": res,
    }
    out["summary"] = summarize(res)
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(out, f, indent=2)
    write_md(out)
    print("\n" + out["summary"])
    print("wrote", OUT_JSON)
    print("wrote", OUT_MD)


if __name__ == "__main__":
    main()
