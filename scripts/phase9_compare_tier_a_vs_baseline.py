"""Phase 9 — build side-by-side baseline vs Tier A Wasserstein table.

Reads `phase9_baseline_score.json` and `phase9_tier_a_score.json`,
computes per-decade delta and the spec §7.4 significance gate
(`delta > 2 * max(baseline_ci, tier_a_ci)`), and writes
`phase9_tier_a_vs_baseline.csv`.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path


def main():
    with open("phase9_baseline_score.json", "r", encoding="utf-8") as f:
        base = json.load(f)
    with open("phase9_tier_a_score.json", "r", encoding="utf-8") as f:
        ta = json.load(f)

    decades = ["1980", "1990", "2000", "2010", "2020"]
    rows = []
    for d in decades:
        b_mean = base["per_decade"][d]["wasserstein_mean"]
        b_ci = base["per_decade"][d]["wasserstein_ci95_halfwidth"]
        t_mean = ta["per_decade"][d]["wasserstein_mean"]
        t_ci = ta["per_decade"][d]["wasserstein_ci95_halfwidth"]
        delta = b_mean - t_mean
        gate = 2.0 * max(b_ci, t_ci)
        significant = delta > gate
        rows.append({
            "decade": d,
            "baseline_w2_mean": f"{b_mean:.4f}",
            "baseline_w2_ci": f"{b_ci:.4f}",
            "tier_a_w2_mean": f"{t_mean:.4f}",
            "tier_a_w2_ci": f"{t_ci:.4f}",
            "delta": f"{delta:+.4f}",
            "gate_2xci": f"{gate:.4f}",
            "delta_significant": str(bool(significant)),
        })

    out_path = Path("phase9_tier_a_vs_baseline.csv")
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"[dump] {out_path.resolve()}")
    print()
    print(f"{'decade':<8} {'base_w2':>9} {'base_ci':>9} "
          f"{'tierA_w2':>9} {'tierA_ci':>9} {'delta':>9} "
          f"{'gate':>8} {'sig?':>6}")
    sum_base = 0.0
    sum_ta = 0.0
    for r in rows:
        print(
            f"{r['decade']:<8} {r['baseline_w2_mean']:>9} "
            f"{r['baseline_w2_ci']:>9} {r['tier_a_w2_mean']:>9} "
            f"{r['tier_a_w2_ci']:>9} {r['delta']:>9} "
            f"{r['gate_2xci']:>8} {r['delta_significant']:>6}"
        )
        sum_base += float(r["baseline_w2_mean"])
        sum_ta += float(r["tier_a_w2_mean"])
    print(f"\nsummed Wasserstein  baseline={sum_base:.4f}  "
          f"tier_a={sum_ta:.4f}  delta={sum_base - sum_ta:+.4f}")


if __name__ == "__main__":
    main()
