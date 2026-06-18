"""Quantify the fed→earned honesty gain across the re-cal frontier.

For each candidate the party_sep emergent fraction is the honesty-budget
`free_flowing` = (all_frozen_final - b0) / (baseline_final - b0): how much of the
rise survives with every empirical/external driver frozen at 1980. Cutting the
mob_* forcing lowers the baseline rise (denominator) while the all-frozen floor is
~unchanged → free_flowing RISES. This measures whether the affect/fit cost of the
mob cut actually buys a meaningful emergent-fraction gain (the central audit goal:
party_sep was 0.28 emergent / 0.72 forced).

Uses the official freeze machinery (audit_lib.run_arc). NOT a bless.
Run: PYTHONPATH=. .venv/Scripts/python.exe validation/audit/recal_budget_check.py
"""
import sys
sys.path.insert(0, ".")
import numpy as np
from scripts.audit.audit_lib import run_arc

SEEDS = (0, 1)
ALL_FREEZE = {"elite_drift", "identity_sorting", "coupling", "party_k",
              "social_media", "data_fed_inputs"}
MOB0 = 2.4838
FIXED = dict(
    media_centrifugal=0.7, affect_rest_rate=0.02, affect_rest_anchor=-0.30,
    affect_saturation=1.0, affect_lr_scale=0.30, contact_warming=True,
    contact_coop_frac=0.3, contact_warm_threshold=-0.6,
    contact_warm_magnitude=0.04, contact_coop_share=0.15,
)
CANDS = {
    "canonical (shipped)": {},
    "corrections only (no cut)": dict(FIXED, mob_peak=MOB0),
    "corrections + 30% cut": dict(FIXED, mob_peak=MOB0 * 0.70),
    "corrections + 40% cut": dict(FIXED, mob_peak=MOB0 * 0.60),
}


def _sep(seed, overrides, freeze, mode):
    r = run_arc(seed, overrides=overrides, freeze=freeze, schedule_mode=mode,
                capture="series")
    return r["series"][0]["party_sep"], r["series"][-1]["party_sep"]


def main():
    print("RE-CAL FED→EARNED BUDGET CHECK —", len(SEEDS), "seeds (party_sep)\n")
    print(f"  {'candidate':<28}{'b0':>7}{'final':>8}{'allFrz':>8}{'free%':>8}")
    for name, ov in CANDS.items():
        b0s, fins, frzs = [], [], []
        for s in SEEDS:
            b0, fin = _sep(s, ov, set(), "full")
            _, frz = _sep(s, ov, ALL_FREEZE, "empty")
            b0s.append(b0); fins.append(fin); frzs.append(frz)
        b0 = float(np.mean(b0s)); fin = float(np.mean(fins)); frz = float(np.mean(frzs))
        free = (frz - b0) / (fin - b0) if abs(fin - b0) > 1e-9 else float("nan")
        print(f"  {name:<28}{b0:>7.3f}{fin:>8.3f}{frz:>8.3f}{free*100:>7.0f}%")


if __name__ == "__main__":
    main()
