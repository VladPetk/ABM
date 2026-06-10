"""Phase 3 — pairwise interaction / sign-stability screen.

Factorial screen across the load-bearing build_engine knobs, over the FULL
historical arc. For each ordered pair (A, B) we measure the effect of A
(high - low) on A's primary target metric while B is held low vs high. If
the SIGN of A's effect flips with B, the interaction is flagged for
literature review. Checked at every decade snapshot + final tick, not just
the last tick.

Run:  .venv/Scripts/python.exe scripts/audit/phase3_pairwise.py
Writes docs/internal/audit/phase3_pairwise.json
"""
from __future__ import annotations

import itertools
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from abm.calibration_parallel import run_seeds_parallel
from scripts.audit.audit_lib import override_series_worker, DECADE_TICKS

SEEDS = list(range(6))

# Load-bearing knobs: (name, low, high, build_engine override fn, target metric, expected sign)
# expected sign: +1 = target rises as knob rises, -1 = falls.
# `identity_pull` and `noise` set two kwargs at once.

def _ovr_drift(v):       return {"tier_d_anes_drift_multiplier": v}
def _ovr_party_pull(v):  return {"tier_c_party_pull_strength": v}
def _ovr_bc(v):          return {"tier_c_bc_strength": v}
def _ovr_idpull(v):      return {"tier_c_identity_pull_x": 0.02 * v,
                                 "tier_c_identity_pull_y": 0.04 * v}
def _ovr_idmult(v):      return {"sandbox_identity_mult": v}
def _ovr_animus(v):      return {"sandbox_animus_mult": v}
def _ovr_noise(v):       return {"tier_d_aniso_noise_sigma_x": v,
                                 "tier_d_aniso_noise_sigma_y": v}

# MHV T0.1: the sigma_pc row (tier_d_anes_sigma_pc_multiplier, 1.0-2.5,
# target within_party_sd) was retired — the kwarg is now a deprecated no-op
# (1.6 folded into PARTY_CUE_SIGMA_HISTORICAL_ANES). The published
# phase3_pairwise.json predates this and still includes it.
KNOBS = [
    # name,            low,   high,  ovr_fn,          target,              sign
    ("drift_mult",     1.0,   6.0,   _ovr_drift,      "party_sep",         +1),
    ("party_pull",     0.0,   0.10,  _ovr_party_pull, "party_sep",         +1),
    ("bc_strength",    0.0,   0.10,  _ovr_bc,         "party_sep",         -1),
    ("identity_pull",  0.5,   2.0,   _ovr_idpull,     "constraint",        +1),
    ("identity_mult",  0.5,   2.0,   _ovr_idmult,     "identity_alignment",+1),
    ("animus_mult",    0.5,   2.0,   _ovr_animus,     "affect",            -1),
    ("noise_sigma",    0.02,  0.10,  _ovr_noise,      "within_party_sd",   +1),
]
KNOB_BY_NAME = {k[0]: k for k in KNOBS}
CENTER = {  # shipped/center value for each knob (held when not varied)
    "drift_mult": 3.0, "party_pull": 0.04, "bc_strength": 0.015,
    "identity_pull": 1.0, "identity_mult": 1.0, "animus_mult": 1.0,
    "noise_sigma": 0.04,
}


def _center_overrides():
    o = {}
    for name, *_ , in KNOBS:
        o.update(KNOB_BY_NAME[name][3](CENTER[name]))
    return o


def _config(setvals):
    """setvals: {knob_name: value}. Returns merged overrides starting from
    all-center."""
    o = {}
    for name in CENTER:
        v = setvals.get(name, CENTER[name])
        o.update(KNOB_BY_NAME[name][3](v))
    return o


def main():
    # Build the work set. For each pair (A, B), we need the 4 corner cells
    # (A_lo/B_lo, A_hi/B_lo, A_lo/B_hi, A_hi/B_hi) with all other knobs at
    # center. Dedup configs across pairs via a label keyed on the setvals.
    cell_labels = {}   # frozenset(setvals.items()) -> label
    work = []

    def cell(setvals):
        key = tuple(sorted(setvals.items()))
        if key not in cell_labels:
            label = "|".join(f"{k}={v}" for k, v in key) or "center"
            cell_labels[key] = label
            ovr = _config(setvals)
            for s in SEEDS:
                work.append((label, s, tuple(sorted(ovr.items()))))
        return cell_labels[key]

    # Ordered pairs: (A, B) screens A's target with B as background, and
    # (B, A) screens B's target with A as background. Cells are deduped.
    pairs = list(itertools.permutations([k[0] for k in KNOBS], 2))
    pair_cells = {}
    for A, B in pairs:
        Alo, Ahi = KNOB_BY_NAME[A][1], KNOB_BY_NAME[A][2]
        Blo, Bhi = KNOB_BY_NAME[B][1], KNOB_BY_NAME[B][2]
        pair_cells[(A, B)] = {
            "ll": cell({A: Alo, B: Blo}),
            "hl": cell({A: Ahi, B: Blo}),
            "lh": cell({A: Alo, B: Bhi}),
            "hh": cell({A: Ahi, B: Bhi}),
        }

    print(f"{len(cell_labels)} unique configs x {len(SEEDS)} seeds "
          f"= {len(work)} arc runs ({len(pairs)} pairs)...")
    flat = run_seeds_parallel(override_series_worker, work)

    # Aggregate: label -> {tickkey -> {metric: mean over seeds}}
    snap_keys = [str(t) for t in DECADE_TICKS.values()] + ["final"]
    agg = {}
    buckets = {}
    for r in flat:
        buckets.setdefault(r["label"], []).append(r)
    for label, runs in buckets.items():
        d = {}
        for sk in snap_keys:
            src = "final" if sk == "final" else "snaps"
            ms = {}
            allm = (runs[0]["final"] if sk == "final" else runs[0]["snaps"][sk]).keys()
            for m in allm:
                vals = [(rr["final"] if sk == "final" else rr["snaps"][sk]).get(m)
                        for rr in runs]
                vals = [v for v in vals if isinstance(v, (int, float))]
                if vals:
                    ms[m] = float(np.mean(vals))
            d[sk] = ms
        agg[label] = d

    # For each pair, compute effect of A at B-lo and B-hi on A's target.
    results = []
    for A, B in pairs:
        cells = pair_cells[(A, B)]
        targetA = KNOB_BY_NAME[A][4]
        signA = KNOB_BY_NAME[A][5]
        row = {"A": A, "B": B, "target": targetA, "expected_sign": signA,
               "by_tick": {}}
        flips = []
        for sk in snap_keys:
            eff_Blo = agg[cells["hl"]][sk].get(targetA, float("nan")) - \
                      agg[cells["ll"]][sk].get(targetA, float("nan"))
            eff_Bhi = agg[cells["hh"]][sk].get(targetA, float("nan")) - \
                      agg[cells["lh"]][sk].get(targetA, float("nan"))
            row["by_tick"][sk] = {"effA_at_Blo": round(eff_Blo, 4),
                                  "effA_at_Bhi": round(eff_Bhi, 4)}
            # sign flip if the two effects have opposite sign and both
            # are non-trivial.
            if (eff_Blo == eff_Blo and eff_Bhi == eff_Bhi
                    and abs(eff_Blo) > 0.01 and abs(eff_Bhi) > 0.01
                    and np.sign(eff_Blo) != np.sign(eff_Bhi)):
                flips.append(sk)
            # also flag wrong-sign vs expectation at the final tick
        row["sign_flips_at"] = flips
        # wrong expected sign at final?
        ef = row["by_tick"]["final"]
        row["wrong_expected_sign_final"] = bool(
            (ef["effA_at_Blo"] == ef["effA_at_Blo"])
            and np.sign(ef["effA_at_Blo"]) == -signA
            and abs(ef["effA_at_Blo"]) > 0.01
        )
        results.append(row)

    flagged = [r for r in results if r["sign_flips_at"] or r["wrong_expected_sign_final"]]

    out = {
        "seeds": SEEDS,
        "knobs": {k[0]: {"low": k[1], "high": k[2], "center": CENTER[k[0]],
                         "target": k[4], "expected_sign": k[5]} for k in KNOBS},
        "n_pairs": len(pairs),
        "results": results,
        "flagged": flagged,
        "agg": agg,
    }
    outp = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                        "docs", "internal", "audit", "phase3_pairwise.json"))
    with open(outp, "w") as f:
        json.dump(out, f, indent=2)

    print(f"\n{len(pairs)} pairs screened; {len(flagged)} flagged "
          f"(sign-flip or wrong expected sign).")
    for r in flagged:
        print(f"  FLAG {r['A']:14s} x {r['B']:14s} target={r['target']:18s} "
              f"flips@{r['sign_flips_at']} wrong_final={r['wrong_expected_sign_final']}")
    print(f"wrote {outp}")


if __name__ == "__main__":
    main()
