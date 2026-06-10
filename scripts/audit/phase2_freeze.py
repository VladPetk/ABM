"""Phase 2 — scheduler interrogation ("freeze test").

For every category-C time-schedule we pin it at its 1980 value and re-run
the full arc, quantifying how much of the historical trajectory is genuine
emergent mechanism vs imposed curve. The headline number is the
"all-frozen" run: every category-C schedule pinned at 1980 + no dated
events, so whatever movement survives is pure rule interaction on static
parameters.

Run:  .venv/Scripts/python.exe scripts/audit/phase2_freeze.py
Writes docs/internal/audit/phase2_freeze.json
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
from scripts.audit.audit_lib import freeze_worker, END_TICK

SEEDS = list(range(8))
METRICS = ["party_sep", "affect", "identity_alignment", "constraint",
           "modularity", "within_party_sd", "xc_fraction"]

# (config_name, freeze_set, schedule_mode)
CONFIGS = [
    ("baseline", (), "full"),
    ("freeze_elite_drift", ("elite_drift",), "full"),
    ("freeze_identity_sorting", ("identity_sorting",), "full"),
    ("freeze_coupling", ("coupling",), "full"),
    ("freeze_party_k", ("party_k",), "full"),
    ("freeze_social_media", ("social_media",), "full"),
    ("drop_dated_events", (), "decade_only"),
    ("freeze_all_schedules", ("elite_drift", "identity_sorting", "coupling",
                              "party_k", "social_media"), "full"),
    ("all_frozen_no_events", ("elite_drift", "identity_sorting", "coupling",
                              "party_k", "social_media"), "empty"),
]


def _mean_series(runs):
    """runs: list of {'series': [ {metric:val}, ... ]}. Returns
    {metric: [mean_over_seeds at each tick]}."""
    n_ticks = len(runs[0]["series"])
    out = {}
    for m in METRICS:
        arr = np.array([[r["series"][t].get(m, np.nan) for t in range(n_ticks)]
                        for r in runs], dtype=float)
        out[m] = np.nanmean(arr, axis=0).tolist()
    return out


def main():
    # Build all (config, seed) work items into one parallel batch.
    work = []
    index = []
    for name, freeze, mode in CONFIGS:
        for s in SEEDS:
            work.append((s, tuple(freeze), mode))
            index.append(name)

    print(f"running {len(work)} arc runs ({len(CONFIGS)} configs x {len(SEEDS)} seeds)...")
    flat = run_seeds_parallel(freeze_worker, work)

    by_config = {name: [] for name, _, _ in CONFIGS}
    for name, res in zip(index, flat):
        by_config[name].append(res)

    series = {name: _mean_series(runs) for name, runs in by_config.items()}

    # Quantify "fraction of arc retained" per metric vs baseline.
    base = series["baseline"]
    report = {}
    for name, _, _ in CONFIGS:
        s = series[name]
        row = {}
        for m in METRICS:
            t0 = base[m][0]
            full_final = base[m][-1]
            this_final = s[m][-1]
            full_rise = full_final - t0
            this_rise = this_final - t0
            frac = (this_rise / full_rise) if abs(full_rise) > 1e-6 else float("nan")
            row[m] = {
                "t0": round(t0, 4),
                "final": round(this_final, 4),
                "baseline_final": round(full_final, 4),
                "frac_of_arc_retained": (round(frac, 3)
                                         if frac == frac else None),
            }
        report[name] = row

    out = {
        "seeds": SEEDS,
        "end_tick": END_TICK,
        "metrics": METRICS,
        "configs": [c[0] for c in CONFIGS],
        "report": report,
        "series": series,
    }
    outp = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                        "docs", "internal", "audit", "phase2_freeze.json"))
    with open(outp, "w") as f:
        json.dump(out, f, indent=2)

    # Console summary — fraction of the 1980->2025 rise retained.
    print(f"\n{'config':28s} " + " ".join(f"{m[:9]:>9s}" for m in METRICS))
    for name, _, _ in CONFIGS:
        cells = []
        for m in METRICS:
            fr = report[name][m]["frac_of_arc_retained"]
            cells.append(f"{(fr if fr is not None else float('nan')):>9.2f}")
        print(f"{name:28s} " + " ".join(cells))
    print("\n(values = fraction of the baseline 1980->2025 change that survives "
          "when that schedule is frozen; ~1.0 = schedule irrelevant, "
          "~0.0 = schedule IS the arc)")
    print(f"wrote {outp}")


if __name__ == "__main__":
    main()
