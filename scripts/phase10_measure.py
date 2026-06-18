"""Phase 10 — measurement script for the redesigned X1–X7 library.

Fires each intervention at four release ticks across the historical
arc (1990 / 2000 / 2010 / 2020) and measures Δsep / Δaff over a
30-tick counterfactual window against a no-intervention control at
the same seed and release tick.

Why a sweep across release ticks: efficacy of depolarization
interventions plausibly varies with the *state of polarization* at
the time of application. Mason 2018 and Drutman 2020 both predict
pre-cascade interventions land differently from post-cascade ones.
Single-tick measurement at 2025 would (a) extrapolate counterfactual
past the ANES horizon and (b) measure each X only at the
hardest-case (most-polarized) starting state. Sweeping across four
decades lets the writeup say "RCV at 1990 lands real; at 2020 it
lands partial" — that is itself a finding.

Output: ``docs/results/phase10_measurement.json`` with per-
(release_year, intervention, seed) measurements + a per-cell
aggregate (mean ± 95% CI) + bucket classification + falsification
check + provenance-tag summary.

Worker function ``_worker`` is top-level (required for Windows
``multiprocessing`` spawn — closures don't pickle). Per the
established Phase 9 pattern, BLAS thread vars are forced to 1
before any numpy import.

Usage:
    .venv/Scripts/python.exe scripts/phase10_measure.py
    .venv/Scripts/python.exe scripts/phase10_measure.py --seeds 5
    .venv/Scripts/python.exe scripts/phase10_measure.py --release-ticks 90 120
    .venv/Scripts/python.exe scripts/phase10_measure.py --interventions X1 X5
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

import numpy as np


# --- Sweep design --------------------------------------------------------

# Release ticks: 4 decade-aligned points spanning 1980 → 2025. Each
# release lets the counterfactual run 30 more ticks (~10 years) within
# the engine's historical horizon (135 ticks = end of 2025).
RELEASE_TICKS = {
    1990: 30,
    2000: 60,
    2010: 90,
    2020: 120,
}

# 30 ticks ≈ 10 years counterfactual. Carried from the redesign brief.
COUNTERFACTUAL_TICKS = 30

# Default ensemble size — matches ``phase9_anes_score.py`` discipline.
DEFAULT_SEEDS = 9

# Intervention ids — must match the ids in the library. "control" is
# the no-intervention baseline trajectory at the same release tick.
INTERVENTION_IDS = (
    "control",
    "X1_show_other_side",
    "X2_fix_algorithm",
    "X3_quit_cable_news",
    "X4_bipartisan_dialogue",
    "X5_deprogramming",
    "X6_shared_institutions",
    "X7_perception_correction",
)

# anes_full preset — single source of truth shared with
# scripts/publish_web_data.py (Step 1 / D4 reconciliation). Previously a
# *divergent* copy lived here (noise 0.08, no momentum/fj/x-cap); it now
# imports the canonical shipped-baseline config so the intervention
# scoreboard is measured on exactly the engine the demo ships. See
# scripts/anes_preset.py.
from scripts.anes_preset import ANES_FULL_KWARGS


# --- Bucket classification (matches ``tests/test_phase6.py``) ----------

def classify_sep(dsep: float) -> str:
    """Issue-sorting axis: helpful = negative (sep falls)."""
    if abs(dsep) < 0.05:
        return "null"
    if -0.15 < dsep < -0.05:
        return "partial"
    if dsep <= -0.15:
        return "real"
    if dsep > 0.05:
        return "backfire"
    return "unclassified"


def classify_aff(daff: float) -> str:
    """Affect axis: helpful = positive (warmth recovers).

    Sign flip vs ``classify_sep``: ``affective_polarization`` reads
    more-negative = more-polarized, so a positive Δ is the helpful
    direction (out-party warmth recovers toward 0).
    """
    if abs(daff) < 0.05:
        return "null"
    if 0.05 < daff < 0.15:
        return "partial"
    if daff >= 0.15:
        return "real"
    if daff < -0.05:
        return "backfire"
    return "unclassified"


# --- Worker (top-level for multiprocessing) ----------------------------

def _worker(args: tuple) -> dict:
    """One simulation: build at seed S, run to release_tick, optionally
    apply intervention, run COUNTERFACTUAL_TICKS more, snapshot.

    args = (seed: int, release_tick: int, intervention_id: str)
    """
    seed, release_tick, intervention_id = args
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from abm.pillars.intervention import apply_intervention
    from abm.pillars.interventions_phase6 import INTERVENTIONS_PHASE6
    from scripts.phase8f_lib import measure_all

    by_id = {iv.id: iv for iv in INTERVENTIONS_PHASE6}

    eng = build_engine(seed=seed, **ANES_FULL_KWARGS)
    sched = build_schedule(
        factional_seeding=ANES_FULL_KWARGS.get("factional_seeding", False),
        faction_anchor_events=ANES_FULL_KWARGS.get("faction_anchor_events", True),
        evidence_regrade=ANES_FULL_KWARGS.get("evidence_regrade", False),
        exogenous_shocks=ANES_FULL_KWARGS.get("exogenous_shocks", False),
    )

    # 1. Run to release_tick (this is the "pre-intervention" state).
    if release_tick > 0:
        run_to(eng, sched, release_tick)
    pre_metrics = measure_all(eng)

    # 2. Apply intervention (or skip for control).
    if intervention_id != "control":
        iv = by_id.get(intervention_id)
        if iv is None:
            raise KeyError(
                f"intervention id {intervention_id!r} not in library"
            )
        apply_intervention(eng, iv)

    # 3. Run COUNTERFACTUAL_TICKS more.
    target_tick = release_tick + COUNTERFACTUAL_TICKS
    run_to(eng, sched, target_tick)
    post_metrics = measure_all(eng)

    return {
        "seed": int(seed),
        "release_tick": int(release_tick),
        "intervention_id": intervention_id,
        "pre": {k: float(v) for k, v in pre_metrics.items()},
        "post": {k: float(v) for k, v in post_metrics.items()},
    }


# --- Aggregation -------------------------------------------------------

def _aggregate(
    raw_results: list[dict],
    seeds: tuple[int, ...],
    release_ticks_to_run: list[int] | None = None,
) -> dict:
    """Build the per-(release_tick, intervention) aggregate. Δ for each
    intervention is computed against the control at the same
    (release_tick, seed) — so the Δ measures the *additional* effect
    of the intervention beyond natural drift over the counterfactual
    window."""
    from abm.calibration_parallel import ci_95

    # Index by (release_tick, intervention_id, seed).
    by_key: dict[tuple, dict] = {}
    for r in raw_results:
        key = (r["release_tick"], r["intervention_id"], r["seed"])
        by_key[key] = r

    if release_ticks_to_run is None:
        active_release_items = list(RELEASE_TICKS.items())
    else:
        run_set = set(release_ticks_to_run)
        active_release_items = [
            (yr, tk) for yr, tk in RELEASE_TICKS.items() if tk in run_set
        ]

    aggregate: dict = {}
    for release_year, release_tick in active_release_items:
        per_intervention: dict = {}
        for iv_id in INTERVENTION_IDS:
            if iv_id == "control":
                continue
            d_seps: list[float] = []
            d_affs: list[float] = []
            for s in seeds:
                control = by_key.get((release_tick, "control", s))
                experimental = by_key.get((release_tick, iv_id, s))
                if control is None or experimental is None:
                    continue
                # Δ vs control at the same release_tick, same seed.
                d_sep = (
                    experimental["post"]["party_sep"]
                    - control["post"]["party_sep"]
                )
                d_aff = (
                    experimental["post"]["affect"]
                    - control["post"]["affect"]
                )
                d_seps.append(d_sep)
                d_affs.append(d_aff)
            if not d_seps:
                per_intervention[iv_id] = {"error": "no seeds completed"}
                continue
            dsep_mean = float(np.mean(d_seps))
            daff_mean = float(np.mean(d_affs))
            dsep_lo, dsep_hi = ci_95(d_seps)
            daff_lo, daff_hi = ci_95(d_affs)
            per_intervention[iv_id] = {
                "n_seeds": len(d_seps),
                "delta_sep": {
                    "mean": dsep_mean,
                    "ci95": [float(dsep_lo), float(dsep_hi)],
                    "per_seed": [float(v) for v in d_seps],
                    "bucket": classify_sep(dsep_mean),
                },
                "delta_aff": {
                    "mean": daff_mean,
                    "ci95": [float(daff_lo), float(daff_hi)],
                    "per_seed": [float(v) for v in d_affs],
                    "bucket": classify_aff(daff_mean),
                },
            }
        aggregate[str(release_year)] = per_intervention
    return aggregate


# --- Provenance-tag summary --------------------------------------------

# Per-intervention provenance tag tallies derived from the redesign
# brief §0.1 tags (L:M, L:D, T, C). Hard-coded here for the writeup
# transparency-number per brief §"Sequence into Phase 10 work" step 7.
PROVENANCE_TAGS = {
    "X1_show_other_side": {
        "L:M": 1,  # strength=0.05 (Bail envelope)
        "L:D": 2,  # asymmetric=None; identity_weight=0.6
        "T":   1,  # threat_amplification=1.5
        "C":   0,
    },
    "X2_fix_algorithm": {
        "L:M": 1,  # affect_weight=0 (Guess 2023 / Allcott 2024 null)
        "L:D": 0, "T": 0, "C": 0,
    },
    "X3_quit_cable_news": {
        "L:M": 0,
        "L:D": 1,  # zero MSNBC+Fox (Levendusky 2013 / Allcott 2020 direction)
        "T":   1,  # 20% treated fraction
        "C":   0,
    },
    "X4_bipartisan_dialogue": {
        "L:M": 2,  # identity_weight_override=0.1; duration=6
        "L:D": 1,  # faction resistance factor=0.5
        "T":   2,  # identity_pull_y factor=0.5; treated fraction=0.20
        "C":   0,
    },
    "X5_deprogramming": {
        "L:M": 0,
        "L:D": 0,
        "T":   0,
        "C":   1,  # treated fraction 0.20 (deradicalization reach — [N], contested)
    },
    "X6_shared_institutions": {
        "L:M": 1,  # +1 tie (Mousa 2020 / Lowe 2021 envelope)
        "L:D": 2,  # affect reset direction; threat reset direction
        "T":   0,
        "C":   1,  # affect-reset-to-0 value
    },
    "X7_perception_correction": {
        "L:M": 1,  # duration=3 (Druckman 2022)
        "L:D": 1,  # perception reset direction
        "T":   2,  # correction_rate=0.05; treated fraction=0.20
        "C":   0,
    },
}


# --- Falsification checks ----------------------------------------------

# Per the redesign brief §0.3 — each intervention specifies what
# observation would force a redesign. Translated here to a callable
# check that takes the (dsep, daff) means and returns (passed, reason).
def _check_falsification(iv_id: str, dsep: float, daff: float) -> dict:
    """Return ``{"passed": bool, "reason": str}`` per the brief's
    §X.Falsification text."""
    if iv_id == "X1_show_other_side":
        # R-phase R-D: threat-gated backfire. Faithful = null-to-conditional
        # backfire (Guess & Coppock null on average; Mutz/Bail conditional under
        # threat). Falsify on a HELPFUL read (threat mechanism inverted) or a
        # runaway/over-broad backfire — not on the now-expected per-release null.
        if dsep < -0.05:
            return {"passed": False, "reason": f"Δsep={dsep:+.3f} < −0.05 — exposure reads helpful; threat mechanism inverted"}
        if dsep > 0.30:
            return {"passed": False, "reason": f"Δsep={dsep:+.3f} > +0.30 — backfire firing too broadly/runaway; gate or strength wrong"}
        return {"passed": True, "reason": "Δsep ∈ [−0.05, +0.30] — null-to-conditional-backfire as predicted"}
    if iv_id == "X2_fix_algorithm":
        if abs(dsep) > 0.10:
            return {"passed": False, "reason": f"|Δsep|={abs(dsep):.3f} > 0.10 — affect channel doing unexpected work"}
        if daff > 0.10:
            return {"passed": False, "reason": f"Δaff={daff:+.3f} > +0.10 — unexpectedly large; check saturation"}
        return {"passed": True, "reason": "null on both axes as predicted"}
    if iv_id == "X3_quit_cable_news":
        if dsep < 0:
            return {"passed": False, "reason": f"Δsep={dsep:+.3f} < 0 — diet-inward-of-centroid mechanism doesn't survive"}
        if dsep > 0.30:
            return {"passed": False, "reason": f"Δsep={dsep:+.3f} > +0.30 — backfire amplified beyond Phase 6"}
        return {"passed": True, "reason": "Δsep ∈ [0, +0.30] as predicted"}
    if iv_id == "X4_bipartisan_dialogue":
        if daff > 0.10:
            return {"passed": False, "reason": f"Δaff={daff:+.3f} > +0.10 — engine over-converting identity_weight to affect"}
        if daff < 0:
            return {"passed": False, "reason": f"Δaff={daff:+.3f} < 0 — prime doesn't survive IdentityToIdeologyPull interaction"}
        return {"passed": True, "reason": "Δaff ∈ [0, +0.10] as predicted"}
    if iv_id == "X5_deprogramming":
        # Deprogramming pulls the faction tail in → helpful (Δsep ≤ 0) where
        # factions exist; decade-gated (exact null pre-emergence). The
        # cross-decade mean may be ~null (two no-op decades dilute it) — that
        # is honest, not a failure. Falsify only on the wrong sign at scale.
        if dsep > 0.05:
            return {"passed": False, "reason": f"Δsep={dsep:+.3f} > +0.05 — clearing faction anchors *raised* separation; mechanism is backwards"}
        if dsep < -0.30:
            return {"passed": False, "reason": f"Δsep={dsep:+.3f} < -0.30 — implausibly large for a 20%-reach program"}
        return {"passed": True, "reason": "Δsep ∈ [-0.30, +0.05] — helpful-or-null as predicted (decade-gated)"}
    if iv_id == "X6_shared_institutions":
        if daff < 0:
            return {"passed": False, "reason": f"Δaff={daff:+.3f} < 0 — saturation isn't capping volume effect, or Enos pattern wins"}
        if daff > 0.30:
            return {"passed": False, "reason": f"Δaff={daff:+.3f} > +0.30 — magnitude exceeds Mousa/Pettigrew envelope"}
        return {"passed": True, "reason": "Δaff ∈ [0, +0.30] as predicted"}
    if iv_id == "X7_perception_correction":
        if daff > 0.10:
            return {"passed": False, "reason": f"Δaff={daff:+.3f} > +0.10 — engine over-converting perception to affect"}
        if abs(daff) < 0.005 and abs(dsep) < 0.005:
            return {"passed": False, "reason": "Δaff and Δsep both ≈ 0 — correction-rate boost insufficient; Phase 11 needs bias-maintenance"}
        return {"passed": True, "reason": "Δaff within ±0.10 as predicted"}
    return {"passed": True, "reason": "no falsification rule defined"}


# --- main --------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--seeds", type=int, default=DEFAULT_SEEDS,
        help=f"Number of seeds (default {DEFAULT_SEEDS})."
    )
    parser.add_argument(
        "--release-ticks", type=int, nargs="+", default=None,
        help=(
            f"Release ticks to sweep (default all 4: "
            f"{list(RELEASE_TICKS.values())})."
        ),
    )
    parser.add_argument(
        "--interventions", type=str, nargs="+", default=None,
        help=(
            "Intervention ids to run (default all 7 + control). "
            "Specify like 'X1' or full ids like 'X1_show_other_side'."
        ),
    )
    parser.add_argument(
        "--out", default="docs/results/phase10_measurement.json",
        help="Output JSON path.",
    )
    parser.add_argument(
        "--processes", type=int, default=None,
        help="Pool size; defaults to min(work_units, ncpu).",
    )
    args = parser.parse_args()

    from abm.calibration_parallel import run_seeds_parallel

    seeds = tuple(range(args.seeds))

    # Resolve release ticks.
    if args.release_ticks:
        ticks = [int(t) for t in args.release_ticks]
        # Build year-lookup the inverse way.
        year_for_tick = {v: k for k, v in RELEASE_TICKS.items()}
        unknown = [t for t in ticks if t not in year_for_tick]
        if unknown:
            print(
                f"warning: release ticks {unknown} not in the default "
                f"sweep set {list(RELEASE_TICKS.values())}",
                file=sys.stderr,
            )
        release_ticks_to_run = ticks
    else:
        release_ticks_to_run = list(RELEASE_TICKS.values())

    # Resolve interventions.
    if args.interventions:
        # Allow short aliases ("X1" → "X1_show_other_side").
        full_ids = []
        for spec in args.interventions:
            matches = [
                iv_id for iv_id in INTERVENTION_IDS
                if iv_id == spec or iv_id.startswith(spec + "_")
            ]
            if not matches:
                raise SystemExit(
                    f"intervention id {spec!r} doesn't match any of "
                    f"{INTERVENTION_IDS}"
                )
            full_ids.append(matches[0])
        # Always include control so Δ can be computed.
        if "control" not in full_ids:
            full_ids.insert(0, "control")
        ivs_to_run = tuple(full_ids)
    else:
        ivs_to_run = INTERVENTION_IDS

    # Build the work list. 1 tuple per (release_tick, intervention,
    # seed). Each is one independent simulation.
    work_args = [
        (s, t, iv)
        for s in seeds
        for t in release_ticks_to_run
        for iv in ivs_to_run
    ]

    print("=" * 78)
    print("Phase 10 — intervention measurement sweep")
    print(f"  seeds:              {args.seeds}")
    print(f"  release_ticks:      {release_ticks_to_run}")
    print(f"  interventions:      {ivs_to_run}")
    print(f"  counterfactual:     +{COUNTERFACTUAL_TICKS} ticks")
    print(f"  total work units:   {len(work_args)}")
    print(f"  processes:          {args.processes or 'auto'}")
    print("=" * 78)

    t0 = time.time()
    raw_results = run_seeds_parallel(
        _worker, work_args, processes=args.processes,
    )
    elapsed = time.time() - t0
    print(f"\n[runtime] {elapsed:.1f}s wall ({len(work_args)/elapsed:.2f} runs/s)")

    # Aggregate per cell.
    aggregate = _aggregate(raw_results, seeds, release_ticks_to_run)

    # Falsification + provenance summaries.
    falsification: dict = {}
    for release_year, per_iv in aggregate.items():
        per: dict = {}
        for iv_id, cell in per_iv.items():
            if "error" in cell:
                per[iv_id] = {"passed": False, "reason": cell["error"]}
                continue
            dsep = cell["delta_sep"]["mean"]
            daff = cell["delta_aff"]["mean"]
            per[iv_id] = _check_falsification(iv_id, dsep, daff)
        falsification[release_year] = per

    # Provenance counts roll-up across all interventions.
    prov_total = {"L:M": 0, "L:D": 0, "T": 0, "C": 0}
    for iv_id, tags in PROVENANCE_TAGS.items():
        if iv_id not in {full for full in ivs_to_run if full != "control"}:
            continue
        for tag, count in tags.items():
            prov_total[tag] += count

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "config": {
            "seeds": list(seeds),
            "release_ticks": release_ticks_to_run,
            "release_years": {
                str(v): k for k, v in RELEASE_TICKS.items() if v in release_ticks_to_run
            },
            "interventions": list(ivs_to_run),
            "counterfactual_ticks": COUNTERFACTUAL_TICKS,
            "preset": "anes_full",
            "preset_kwargs": ANES_FULL_KWARGS,
        },
        "raw_results": raw_results,
        "aggregate": aggregate,
        "falsification": falsification,
        "provenance_tags": {
            "per_intervention": {
                k: v for k, v in PROVENANCE_TAGS.items()
                if k in {full for full in ivs_to_run if full != "control"}
            },
            "total": prov_total,
        },
        "elapsed_seconds": elapsed,
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[out]   wrote {out_path}")

    # Pretty-print a summary table.
    print("\n" + "=" * 78)
    print("Bucket summary (Δ vs control, mean across seeds)")
    print("=" * 78)
    header = (
        f"{'release':>8} | {'intervention':<28} | "
        f"{'Δsep':>8} | {'sep bucket':<10} | "
        f"{'Δaff':>8} | {'aff bucket':<10}"
    )
    print(header)
    print("-" * len(header))
    for release_year, per_iv in aggregate.items():
        for iv_id, cell in per_iv.items():
            if "error" in cell:
                print(
                    f"{release_year:>8} | {iv_id:<28} | "
                    f"  ERROR  | -          |   ERROR  | -          "
                )
                continue
            print(
                f"{release_year:>8} | {iv_id:<28} | "
                f"{cell['delta_sep']['mean']:>+8.3f} | "
                f"{cell['delta_sep']['bucket']:<10} | "
                f"{cell['delta_aff']['mean']:>+8.3f} | "
                f"{cell['delta_aff']['bucket']:<10}"
            )
        print("-" * len(header))

    # Falsification roll-up.
    n_fail = 0
    print("\n" + "=" * 78)
    print("Falsification checks (per redesign_briefs.md §0.3)")
    print("=" * 78)
    for release_year, per_iv in falsification.items():
        for iv_id, result in per_iv.items():
            tag = "PASS" if result["passed"] else "FAIL"
            if not result["passed"]:
                n_fail += 1
            print(f"  {release_year} {iv_id:<28} [{tag}] {result['reason']}")
    print(f"\n{n_fail} falsification check(s) failed across the sweep.")

    # Provenance summary.
    print("\n" + "=" * 78)
    print("Provenance-tag summary (across all run interventions)")
    print("=" * 78)
    total = sum(prov_total.values())
    if total > 0:
        for tag, count in prov_total.items():
            frac = 100.0 * count / total
            print(f"  {tag:<5} {count:>3}  ({frac:5.1f}%)")
    print(
        f"\n  total knobs across {len(PROVENANCE_TAGS)} interventions: "
        f"{total}"
    )


if __name__ == "__main__":
    main()
