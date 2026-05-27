"""Phase 8c §7 S2 — bucket-cutoff sensitivity sweep.

Re-runs the §11 release-phase experiment for each X-intervention
across three cutoff configurations and reports the bucket labels
under each. The default 0.05/0.15 cutoffs are checked against
0.03/0.10 (tighter) and 0.08/0.20 (looser).

For each (intervention, cutoff_config) cell, reports the bucket
label on both axes (issue_sorting and affect). The sweep answers
Fork 7-A: "do the labels survive the cutoff perturbation, or are
they fragile to threshold choice?"

Run: `python scripts/phase8c_cutoff_sweep.py`.
"""
from __future__ import annotations

import sys

import numpy as np

from abm.calibration_parallel import run_seeds_parallel
from abm.metrics.affective import affective_polarization
from abm.pillars import INTERVENTIONS_PHASE6, PILLAR, apply_intervention
from abm.pillars.calm_to_camps import build_engine

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

SEEDS = tuple(range(20))   # Phase 8c §7 S1
N = 250
TICKS = 200


def _release_worker(args) -> dict:
    """Worker function for parallel-seed §11 release-phase measurement.
    Top-level so multiprocessing.spawn can import it."""
    iv_id, seed = args
    intervention = next(iv for iv in INTERVENTIONS_PHASE6 if iv.id == iv_id)
    eng = build_engine(seed=seed, n_agents=N)
    apply_intervention(eng, PILLAR.interventions[4])
    eng.run(TICKS)
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    sep_before = float(np.linalg.norm(
        pos[parties == 0].mean(axis=0) - pos[parties == 1].mean(axis=0)
    ))
    aff_before = affective_polarization(eng.agents)
    apply_intervention(eng, intervention)
    eng.run(TICKS)
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    sep_after = float(np.linalg.norm(
        pos[parties == 0].mean(axis=0) - pos[parties == 1].mean(axis=0)
    ))
    aff_after = affective_polarization(eng.agents)
    return {"sep": (sep_before, sep_after), "aff": (aff_before, aff_after)}


CUTOFF_CONFIGS = {
    "tight (0.03 / 0.10)": (0.03, 0.10),
    "default (0.05 / 0.15)": (0.05, 0.15),
    "loose (0.08 / 0.20)": (0.08, 0.20),
}


def classify_sep(dsep: float, null_cut: float, real_cut: float) -> str:
    """Issue-sorting axis (helpful = negative). Parametrised on the
    null/real cutoffs."""
    if abs(dsep) < null_cut:
        return "null"
    if -real_cut < dsep < -null_cut:
        return "partial"
    if dsep <= -real_cut:
        return "real"
    if dsep > null_cut:
        return "backfire"
    return "unclassified"


def classify_aff(daff: float, null_cut: float, real_cut: float) -> str:
    """Affect axis (helpful = positive — warmth recovers)."""
    if abs(daff) < null_cut:
        return "null"
    if null_cut < daff < real_cut:
        return "partial"
    if daff >= real_cut:
        return "real"
    if daff < -null_cut:
        return "backfire"
    return "unclassified"


def main():
    print("=" * 72)
    print("Phase 8c §7 S2 — bucket-cutoff sensitivity sweep")
    print(f"  N=250, TICKS=200, seeds=0..{SEEDS[-1]} ({len(SEEDS)} seeds)")
    print("=" * 72)

    # Collect raw deltas for every intervention at the new seed count.
    print("\n[measuring] running each intervention at 20 seeds...")
    by_iv: dict = {}
    for iv in INTERVENTIONS_PHASE6:
        args = [(iv.id, s) for s in SEEDS]
        results = run_seeds_parallel(_release_worker, args)
        seps = [r["sep"][1] - r["sep"][0] for r in results]
        affs = [r["aff"][1] - r["aff"][0] for r in results]
        by_iv[iv.id] = {
            "sep_mean": float(np.mean(seps)),
            "sep_se": float(np.std(seps, ddof=1) / np.sqrt(len(seps))),
            "aff_mean": float(np.mean(affs)),
            "aff_se": float(np.std(affs, ddof=1) / np.sqrt(len(affs))),
        }
        print(
            f"  {iv.id}: sep = {by_iv[iv.id]['sep_mean']:+.4f} "
            f"+- {by_iv[iv.id]['sep_se']:.4f}, "
            f"aff = {by_iv[iv.id]['aff_mean']:+.4f} "
            f"+- {by_iv[iv.id]['aff_se']:.4f}"
        )

    # Sweep the three cutoff configs.
    print("\n[sweep] bucket labels under each cutoff config")
    print("\n" + "-" * 88)
    header = f"{'Intervention':<30}"
    for config_name in CUTOFF_CONFIGS:
        header += f"  {config_name:<28}"
    print(header)
    print("-" * 88)
    for iv in INTERVENTIONS_PHASE6:
        row = f"{iv.id:<30}"
        for config_name, (null_c, real_c) in CUTOFF_CONFIGS.items():
            sep_b = classify_sep(by_iv[iv.id]["sep_mean"], null_c, real_c)
            aff_b = classify_aff(by_iv[iv.id]["aff_mean"], null_c, real_c)
            cell = f"sep={sep_b}/aff={aff_b}"
            row += f"  {cell:<28}"
        print(row)
    print("-" * 88)

    # Stability analysis — does each X stay in the same bucket pair?
    print("\n[stability] interventions that flip buckets across cutoffs")
    flips = []
    for iv in INTERVENTIONS_PHASE6:
        sep_labels = set()
        aff_labels = set()
        for null_c, real_c in CUTOFF_CONFIGS.values():
            sep_labels.add(
                classify_sep(by_iv[iv.id]["sep_mean"], null_c, real_c)
            )
            aff_labels.add(
                classify_aff(by_iv[iv.id]["aff_mean"], null_c, real_c)
            )
        if len(sep_labels) > 1 or len(aff_labels) > 1:
            flips.append((iv.id, sep_labels, aff_labels))
    if not flips:
        print(
            "  No interventions flip across the three cutoff schemes. "
            "Default 0.05/0.15 cutoffs are robust at the 20-seed ensemble."
        )
    else:
        for iv_id, sep_labels, aff_labels in flips:
            print(f"  {iv_id}:")
            if len(sep_labels) > 1:
                print(f"    issue_sorting flips: {sep_labels}")
            if len(aff_labels) > 1:
                print(f"    affect flips:        {aff_labels}")

    print("\n" + "=" * 72)


if __name__ == "__main__":
    main()
