"""S4 calibration target vector + fit/holdout split (MHV S4 / T4.1).

Assembles, from already-committed empirical sources, the single target
structure the S4 fit (T4.2) and holdout battery (T4.4) consume. No engine run
here -- this is the *empirical* (target) side only; T4.2 runs the engine and
compares.

Sources (all committed / derived from committed inputs):
  * ANES per-wave bands  -- scripts/phase8f_lib.py ANES_PRIMARY_TARGETS +
    ANES_INITIAL_TARGETS_1980 (grounded affect bands wired via use_anes_bands;
    affect == data/phase9_empirical/derived/affect_bands.json, asserted below).
  * ANES 2D cloud (Wasserstein) -- the phase9 per-decade KDE/pointcloud
    (abm/calibration_phase9.py); referenced by decade tick, used by T4.2.
  * GSS constraint + B&G dual  -- data/mhv/gss_constraint_series.json (T4.0).

Design decisions (s4_spec.md, AGREE 2026-06-12):
  * FIT window = 1980/1990/2000 decades (ANES waves <=2008); the 2010 bucket
    (ANES 2012+2016) straddles 2012, so the whole 2010 bucket goes to HOLDOUT --
    a slightly stronger, cleaner temporal cut than the spec's "<=2012" (the late
    steep rise is fully held out and must be EXTRAPOLATED).
  * Constraint: ANES band is the in-window FIT target (same econ/cult 2-axis
    compass the engine projects to -> directly commensurable). The GSS series is
    the HELD-OUT INSTRUMENT (cut 2) and centers the constraint_rate prior.
  * 5-knob fit set (party_pull, fj_alpha_scale, constraint_rate, animus_mult,
    noise_sigma); each observable tags the knob family it informs.

Holdout cuts (POWER bands, pre-registered + frozen here, s4_spec.md §5):
  1 temporal   -- predict 2010/2020/2025 ANES cells within ANES band widened by
                  1x band-width (=2x total); 1980->year change sign stable.
  2 instrument -- fit on ANES -> predict the GSS constraint/B&G slope within
                  +/-50% and same sign (band wide: ANES-vs-GSS are different
                  instruments with a ~20% level gap, not eyeballed moments).
  3 statistic  -- fit on {party_sep, affect, within_party_sd} -> predict
                  {pr_attitude, modularity, xc_fraction, bg_partisan_align}
                  within +/-1 prior-SD, signs correct.
  4 power      -- each prediction reported as a seed-band (>=8 seeds); the band
                  must CONTAIN the empirical value for >=3 of the 4 cuts.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.phase8f_lib import (
    ANES_INITIAL_TARGETS_1980,
    ANES_PRIMARY_TARGETS,
)
from scripts.phase9_anes_score import SECTION11_TICKS  # [(year, tick), ...]

ROOT = Path(__file__).resolve().parents[2]
GSS_JSON = ROOT / "data" / "mhv" / "gss_constraint_series.json"
OUT = ROOT / "docs" / "internal" / "audit" / "s4_targets.json"

FIT_DECADES = [1980, 1990, 2000]
HOLDOUT_DECADES = [2010, 2020, 2025]
ALL_DECADES = FIT_DECADES + HOLDOUT_DECADES

# observable -> knob family it primarily informs (5-knob set)
KNOB_FAMILY = {
    "party_sep": ["party_pull", "fj_alpha_scale"],   # level + rate/shape
    "affect": ["animus_mult"],
    "constraint": ["constraint_rate"],
    "within_party_sd": ["noise_sigma"],
    "w2_cloud": ["party_pull", "fj_alpha_scale", "noise_sigma"],  # joint distributional
}
ANES_HALFWIDTH = 0.07  # the +/-0.07 band-width used in ANES_PRIMARY_TARGETS

# decade -> tick (extraction point for the engine; T4.2)
DECADE_TICK = {y: t for y, t in SECTION11_TICKS}


def _anes_band(decade, key):
    if decade == 1980:
        return ANES_INITIAL_TARGETS_1980.get(key)
    return ANES_PRIMARY_TARGETS[decade].get(key)


def _mid(band):
    return None if band is None else 0.5 * (band[0] + band[1])


def _widen(band, factor_halfwidths=1.0):
    """Widen a band by `factor_halfwidths` * ANES_HALFWIDTH on each side."""
    if band is None:
        return None
    d = factor_halfwidths * ANES_HALFWIDTH
    return [round(band[0] - d, 4), round(band[1] + d, 4)]


def build_targets():
    gss = json.loads(GSS_JSON.read_text())

    # --- verify grounded affect bands are wired (T4.1 acceptance) ---
    aff = json.loads((ROOT / "data" / "phase9_empirical" / "derived"
                      / "affect_bands.json").read_text())["bands"]
    for dec in (1990, 2000, 2010, 2020):
        b_code = ANES_PRIMARY_TARGETS[dec]["affect"]
        b_file = aff[str(dec)]["band"]
        if abs(b_code[0] - b_file[0]) > 0.02 or abs(b_code[1] - b_file[1]) > 0.02:
            raise AssertionError(
                f"affect band {dec} unwired: code {b_code} vs file {b_file}")

    # --- per-decade ANES fit/holdout target cells ---
    decades = {}
    for dec in ALL_DECADES:
        cells = {}
        for key in ("party_sep", "affect", "constraint", "within_party_sd"):
            band = _anes_band(dec, key)
            cells[key] = {
                "band": list(band) if band else None,
                "point": _mid(band),
                "instrument": "ANES",
                "knobs": KNOB_FAMILY[key],
            }
        cells["w2_cloud"] = {
            "instrument": "ANES_KDE",
            "note": "phase9 per-decade KDE/pointcloud Wasserstein-2 (T4.2 scorer)",
            "knobs": KNOB_FAMILY["w2_cloud"],
        }
        decades[dec] = {
            "tick": DECADE_TICK.get(dec),
            "role": "fit" if dec in FIT_DECADES else "holdout",
            "cells": cells,
        }

    # --- holdout cut definitions (frozen, pre-registered) ---
    gss_by_dec = gss["by_decade"]
    gss_slopes = gss["slopes"]
    holdout = {
        "cut1_temporal": {
            "predict_decades": HOLDOUT_DECADES,
            "observables": ["party_sep", "affect", "constraint", "within_party_sd"],
            "band_rule": "ANES band widened by 1 band-width each side (2x total)",
            "widened_bands": {
                dec: {k: _widen(_anes_band(dec, k))
                      for k in ("party_sep", "affect", "constraint", "within_party_sd")}
                for dec in HOLDOUT_DECADES
            },
            "extra": "sign of 1980->year change must be seed-stable",
        },
        "cut2_instrument": {
            "fit_on": ["ANES party_sep/affect/within_sd/constraint + cloud"],
            "predict": ["GSS constraint_index trend", "GSS bg_partisan_align trend"],
            "gss_target": {
                "constraint_index": {
                    "by_decade": {d: gss_by_dec[d]["constraint_index"] for d in gss_by_dec},
                    "slope_per_year": gss_slopes["constraint_index"]["per_year"],
                },
                "bg_partisan_align": {
                    "by_decade": {d: gss_by_dec[d]["bg_partisan_align"] for d in gss_by_dec},
                    "slope_per_year": gss_slopes["bg_partisan_align"]["per_year"],
                },
            },
            "band_rule": "engine-predicted slope within +/-50% of GSS slope, same sign",
        },
        "cut3_statistic": {
            "fit_on": ["party_sep", "affect", "within_party_sd"],
            "predict": ["pr_attitude", "modularity", "xc_fraction", "bg_partisan_align"],
            "band_rule": "within +/-1 prior-SD of empirical, signs correct",
        },
        "cut4_power": {
            "rule": "each prediction reported as a >=8-seed band; band must CONTAIN "
                    "the empirical value for >=3 of the 4 cuts (one cut may fail).",
        },
    }

    # --- constraint_rate prior centering hint (from GSS slope) ---
    priors_note = {
        "constraint_rate": {
            "center_hint": "GSS issue-constraint slope +%.5f/yr (T4.0)"
                           % gss_slopes["constraint_index"]["per_year"],
            "proposed_prior": [0.005, 0.06],
        },
    }

    return {
        "meta": {
            "stage": "MHV S4 / T4.1",
            "fit_decades": FIT_DECADES,
            "holdout_decades": HOLDOUT_DECADES,
            "fit_set": ["party_pull", "fj_alpha_scale", "constraint_rate",
                        "animus_mult", "noise_sigma"],
            "frozen": ["idpull", "bc_strength", "drift_mult"],
            "affect_bands": "grounded (data/phase9_empirical/derived/affect_bands.json) -- wired",
            "constraint_fit_instrument": "ANES (in-window); GSS = held-out instrument (cut2)",
        },
        "decades": decades,
        "holdout_cuts": holdout,
        "priors_note": priors_note,
    }


def main():
    t = build_targets()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(t, indent=2))
    print(f"wrote {OUT.relative_to(ROOT)}")
    print("\nFIT decades:", FIT_DECADES, " HOLDOUT:", HOLDOUT_DECADES)
    print("\n=== ANES fit/holdout target points (mid-band) ===")
    print(f"{'dec':>5} {'role':>8} {'tick':>5} {'sep':>6} {'affect':>7} "
          f"{'constr':>7} {'wp_sd':>6}")
    for dec in ALL_DECADES:
        c = t["decades"][dec]
        cells = c["cells"]
        def p(k):
            v = cells[k]["point"]
            return f"{v:.3f}" if v is not None else "  -  "
        print(f"{dec:>5} {c['role']:>8} {str(c['tick']):>5} "
              f"{p('party_sep'):>6} {p('affect'):>7} {p('constraint'):>7} "
              f"{p('within_party_sd'):>6}")
    print("\n=== cut2 held-out GSS instrument (engine fit to ANES must predict) ===")
    g = t["holdout_cuts"]["cut2_instrument"]["gss_target"]
    for m in ("constraint_index", "bg_partisan_align"):
        bd = g[m]["by_decade"]
        print(f"  {m:18s} " + " ".join(f"{k}:{bd[k]:.3f}" for k in sorted(bd))
              + f"  slope {g[m]['slope_per_year']:+.5f}/yr")
    print("\n=== cut1 temporal widened bands (frozen) ===")
    for dec in HOLDOUT_DECADES:
        wb = t["holdout_cuts"]["cut1_temporal"]["widened_bands"][dec]
        print(f"  {dec}: sep {wb['party_sep']}  affect {wb['affect']}  "
              f"constr {wb['constraint']}  wp_sd {wb['within_party_sd']}")


if __name__ == "__main__":
    main()
