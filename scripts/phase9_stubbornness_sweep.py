"""Phase 9 Step 4 — sweep `faction_stubbornness_boost` over {0.3, 0.5, 0.7}.

For each value, re-scores the Tier A engine at 9 seeds (per-decade
Wasserstein) AND re-measures the Phase 8f §11 cells. Bless the value
that minimizes summed Wasserstein subject to the §11 gate (>= 18/24)
passing.

Outputs:
- `phase9_stubbornness_sweep.json` — full per-boost result.
- console table summarising boost, per-decade W2, sum, §11 tally, gate pass.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


BOOSTS = [0.3, 0.5, 0.7]


def _run_score(boost: float) -> dict:
    out_json = f"phase9_tier_a_score_boost_{boost:.1f}.json"
    out_csv = f"phase9_tier_a_descriptors_boost_{boost:.1f}.csv"
    env = dict(os.environ)
    env["PHASE9_BOOST"] = f"{boost}"
    env["PHASE9_OUT_JSON"] = out_json
    env["PHASE9_OUT_CSV"] = out_csv
    env["PYTHONPATH"] = "."
    print(f"\n--- sweep: boost={boost} (W2) ---")
    proc = subprocess.run(
        [sys.executable, "scripts/phase9_score_tier_a.py"],
        env=env, check=True,
    )
    with open(out_json, "r", encoding="utf-8") as f:
        return json.load(f)


def _run_section11(boost: float) -> dict:
    out_json = f"phase9_section11_boost_{boost:.1f}.json"
    env = dict(os.environ)
    env["PHASE9_BOOST"] = f"{boost}"
    env["PHASE9_SEC11_OUT"] = out_json
    env["PYTHONPATH"] = "."
    print(f"\n--- sweep: boost={boost} (§11) ---")
    proc = subprocess.run(
        [sys.executable, "scripts/phase9_section11_under_tier_a.py"],
        env=env, check=True,
    )
    with open(out_json, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    results = []
    for b in BOOSTS:
        w = _run_score(b)
        s = _run_section11(b)
        per_decade = {
            d: w["per_decade"][d]["wasserstein_mean"]
            for d in ["1980", "1990", "2000", "2010", "2020"]
        }
        summed = sum(per_decade.values())
        results.append({
            "boost": b,
            "per_decade_w2": per_decade,
            "summed_w2": summed,
            "tally_24": s["tally_24"],
            "tally_4x5": s["tally_4x5"],
            "gate_pass_18_of_24": s["gate_pass_18_of_24"],
        })

    print("\n\n=== Stubbornness sweep summary ===")
    print(f"{'boost':<6} {'1980':>7} {'1990':>7} {'2000':>7} {'2010':>7} "
          f"{'2020':>7} {'sum':>7} {'§11':>7} {'gate':>6}")
    for r in results:
        d = r["per_decade_w2"]
        print(
            f"{r['boost']:<6} {d['1980']:>7.4f} {d['1990']:>7.4f} "
            f"{d['2000']:>7.4f} {d['2010']:>7.4f} {d['2020']:>7.4f} "
            f"{r['summed_w2']:>7.4f} {r['tally_24']:>3d}/24 "
            f"{('PASS' if r['gate_pass_18_of_24'] else 'FAIL'):>6}"
        )

    # Bless: minimum summed_w2 among gate-passing variants. If none pass,
    # report the minimum summed_w2 and note no gate-passing variant.
    passing = [r for r in results if r["gate_pass_18_of_24"]]
    if passing:
        blessed = min(passing, key=lambda r: r["summed_w2"])
        bless_reason = "min summed W2 among §11-passing"
    else:
        blessed = min(results, key=lambda r: r["summed_w2"])
        bless_reason = "NO §11-passing variant; reporting min summed W2 overall"

    print(f"\nblessed: boost={blessed['boost']}  ({bless_reason})")

    with open("phase9_stubbornness_sweep.json", "w", encoding="utf-8") as f:
        json.dump({
            "results": results,
            "blessed": blessed,
            "bless_reason": bless_reason,
        }, f, indent=2)


if __name__ == "__main__":
    main()
