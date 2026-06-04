"""sandbox_knob_screen.py — data-driven screening for the sandbox sliders.

Goal: pick the handful of knobs that most strongly AND most DISTINCTLY move the
compass, so the interactive sandbox exposes dials that actually do something.

For each candidate knob we sweep it across a plausible range (from the shipped
`anes_full` config), run the full 1980→2025 arc at seed 0, and read the 2025
outcome metrics:

  sep   — party separation (centroid gap)         — "how far apart the camps are"
  aff   — out-party warmth (more negative = colder) — "how much they hate"
  wpsd  — within-party spread                       — "how tight each camp is"
  mod   — network modularity                        — "how walled-off the bubbles are"
  align — mean mega-identity alignment              — "how stacked identity is"

The per-knob SPAN (max−min across its values) of each metric says how
expressive that knob is on that axis. A good final set = 5 knobs that each
dominate a *different* axis (expressive + non-redundant).

NOTE: this screens knobs applied build-time over the FULL run, to rank raw
expressiveness. The shipped sandbox will branch at a fixed date (e.g. 1995), so
IC/draw-heavy knobs (cue_correlation, cue_sigma_pc) will read weaker there than
the per-tick rule knobs (drift/party_pull/bc/identity_pull). Flagged below.

Usage:
    .venv/Scripts/python.exe scripts/sandbox_knob_screen.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.anes_preset import ANES_FULL_KWARGS          # noqa: E402
from scripts.phase8f_lib import measure_all                # noqa: E402
from abm.pillars.historical_arc import build_engine, build_schedule  # noqa: E402
from abm.pillars.schedule import run_to                    # noqa: E402

END = 135
METRICS = ["sep", "aff", "wpsd", "mod", "align"]


def run_final(overrides: dict) -> dict:
    kwargs = dict(ANES_FULL_KWARGS)
    kwargs.update(overrides)
    eng = build_engine(seed=0, **kwargs)
    sched = build_schedule(
        factional_seeding=kwargs.get("factional_seeding", False),
        faction_anchor_events=kwargs.get("faction_anchor_events", True),
        evidence_regrade=kwargs.get("evidence_regrade", False),
        exogenous_shocks=kwargs.get("exogenous_shocks", False),
    )
    for t in range(1, END + 1):
        run_to(eng, sched, t)
    m = measure_all(eng)
    aligns = [
        float(a.state.attrs.get("identity_alignment", 0.0))
        for a in eng.agents if a.state.attrs.get("party") in (0, 1)
    ]
    return {
        "sep": float(m["party_sep"]),
        "aff": float(m["affect"]),
        "wpsd": float(m["within_party_sd"]),
        "mod": float(m["modularity"]),
        "align": float(np.mean(aligns)) if aligns else 0.0,
    }


# name -> (override-fn(value), [values], "per-tick" | "ic/draw")
CANDIDATES = {
    # separation movers (already screened)
    "elite_drift(x)":   (lambda v: {"tier_d_anes_drift_multiplier": v}, [0.0, 1.5, 3.0, 5.0, 8.0], "per-tick"),
    "party_pull":       (lambda v: {"tier_c_party_pull_strength": v}, [0.0, 0.02, 0.04, 0.10, 0.20], "per-tick"),
    "bc_strength":      (lambda v: {"tier_c_bc_strength": v}, [0.0, 0.015, 0.05, 0.10, 0.20], "per-tick"),
    "identity_pull(x)": (lambda v: {"tier_c_identity_pull_x": 0.020 * v, "tier_c_identity_pull_y": 0.040 * v}, [0.0, 0.5, 1.0, 2.0, 3.0], "per-tick"),
    # NEW dials (just exposed) — meant to unlock distinct axes
    "animus_mult":      (lambda v: {"sandbox_animus_mult": v}, [0.5, 1.0, 2.0, 4.0, 8.0], "per-tick"),
    "identity_mult":    (lambda v: {"sandbox_identity_mult": v}, [0.0, 0.5, 1.0, 2.0, 3.0], "per-tick"),
    "rewire_mult":      (lambda v: {"sandbox_rewire_mult": v}, [0.0, 1.0, 3.0, 6.0, 10.0], "per-tick"),
}


def main():
    t0 = time.time()
    print("baseline (anes_full, seed 0)...", flush=True)
    base = run_final({})
    print("  " + "  ".join(f"{k}={base[k]:+.3f}" for k in METRICS), flush=True)

    spans: dict[str, dict] = {}
    for name, (fn, vals, kind) in CANDIDATES.items():
        print(f"\n{name}  [{kind}]", flush=True)
        rows = []
        for v in vals:
            r = run_final(fn(v))
            rows.append((v, r))
            print(f"  {v:>6} -> " + "  ".join(f"{k}={r[k]:+.3f}" for k in METRICS), flush=True)
        spans[name] = {k: max(r[k] for _, r in rows) - min(r[k] for _, r in rows) for k in METRICS}

    print("\n\n=== SPAN (max-min across each knob's range) ===", flush=True)
    head = f"{'knob':<18}" + "".join(f"{k:>9}" for k in METRICS) + "   kind"
    print(head, flush=True)
    print("-" * len(head), flush=True)
    for name, (_, _, kind) in CANDIDATES.items():
        s = spans[name]
        print(f"{name:<18}" + "".join(f"{s[k]:>9.3f}" for k in METRICS) + f"   {kind}", flush=True)

    print(f"\ndone in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
