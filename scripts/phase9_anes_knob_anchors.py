"""Phase 9 §11.7-B — Empirical anchors for re-deriving historical knobs.

Reads `data/phase9_empirical/derived/respondent_coordinates.csv` and emits
the per-decade ANES anchors needed to re-set:

  - PARTY_CUE_SIGMA_HISTORICAL  (from within-party SD on each axis)
  - PARTY_ASSIGNMENT_K          (from sign-alignment of party-with-x)
  - ELITE_DRIFT_SCHEDULE        (from per-decade centroid velocity)
  - PARTY_CENTERS_1980          (from 1980-bucket centroid)

Decade bucketing matches phase9_anes_target_builder.py:
  1980 ← 1986, 1988
  1990 ← 1990, 1992, 1994, 1996, 1998
  2000 ← 2000, 2004, 2008
  2010 ← 2012, 2016
  2020 ← 2020, 2024
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "phase9_empirical" / "derived" / "respondent_coordinates.csv"
OUT = ROOT / "docs" / "results" / "phase9_anes_knob_anchors.json"

DECADE_WAVES = {
    1980: [1986, 1988],
    1990: [1990, 1992, 1994, 1996, 1998],
    2000: [2000, 2004, 2008],
    2010: [2012, 2016],
    2020: [2020, 2024],
}


def _wmean(x, w):
    return float(np.average(x, weights=w))


def _wsd(x, w):
    m = _wmean(x, w)
    return float(np.sqrt(np.average((x - m) ** 2, weights=w)))


def _wcorr(x, y, w):
    mx = _wmean(x, w)
    my = _wmean(y, w)
    cov = np.average((x - mx) * (y - my), weights=w)
    sx = np.sqrt(np.average((x - mx) ** 2, weights=w))
    sy = np.sqrt(np.average((y - my) ** 2, weights=w))
    return float(cov / (sx * sy)) if sx > 0 and sy > 0 else 0.0


def main():
    df = pd.read_csv(CSV)
    print(f"Loaded {len(df)} ANES respondents")
    # Restrict to two-party (drop I) for engine-relevant comparisons
    # but also keep ALL-population stats for context.

    rows = []
    for decade, waves in DECADE_WAVES.items():
        sub = df[df["year"].isin(waves)].copy()
        w_all = sub["weight"].values
        x = sub["econ"].values
        y = sub["cult"].values

        # All-population stats (matches phase9_empirical/.npy targets)
        all_stats = {
            "n": int(len(sub)),
            "var_x": float(np.average((x - _wmean(x, w_all)) ** 2, weights=w_all)),
            "var_y": float(np.average((y - _wmean(y, w_all)) ** 2, weights=w_all)),
            "sd_x": _wsd(x, w_all),
            "sd_y": _wsd(y, w_all),
            "corr": _wcorr(x, y, w_all),
            "mean_x": _wmean(x, w_all),
            "mean_y": _wmean(y, w_all),
        }

        # Two-party-only stats
        dr = sub[sub["party"].isin(["D", "R"])].copy()
        wd = dr["weight"].values
        dx = dr["econ"].values
        dy = dr["cult"].values
        party_d = dr[dr["party"] == "D"]
        party_r = dr[dr["party"] == "R"]
        cent_d = (
            _wmean(party_d["econ"].values, party_d["weight"].values),
            _wmean(party_d["cult"].values, party_d["weight"].values),
        )
        cent_r = (
            _wmean(party_r["econ"].values, party_r["weight"].values),
            _wmean(party_r["cult"].values, party_r["weight"].values),
        )
        party_sep = float(np.sqrt(
            (cent_d[0] - cent_r[0]) ** 2 + (cent_d[1] - cent_r[1]) ** 2
        ))

        wp_sd_x_d = _wsd(party_d["econ"].values, party_d["weight"].values)
        wp_sd_y_d = _wsd(party_d["cult"].values, party_d["weight"].values)
        wp_sd_x_r = _wsd(party_r["econ"].values, party_r["weight"].values)
        wp_sd_y_r = _wsd(party_r["cult"].values, party_r["weight"].values)

        # Pooled within-party SD (matches phase8f_lib.within_party_sd
        # which weights by party count).
        n_d = len(party_d)
        n_r = len(party_r)
        wp_sd_x_pool = float(np.sqrt(
            (n_d * wp_sd_x_d ** 2 + n_r * wp_sd_x_r ** 2) / (n_d + n_r)
        ))
        wp_sd_y_pool = float(np.sqrt(
            (n_d * wp_sd_y_d ** 2 + n_r * wp_sd_y_r ** 2) / (n_d + n_r)
        ))

        # Sign-alignment: fraction of partisans whose econ sign matches
        # party sign (D <-> negative econ, R <-> positive econ).
        d_econ_neg_frac = float(np.average(
            party_d["econ"].values < 0, weights=party_d["weight"].values
        ))
        r_econ_pos_frac = float(np.average(
            party_r["econ"].values > 0, weights=party_r["weight"].values
        ))
        align_x = float(np.average(
            ((dr["party"] == "D") & (dr["econ"] < 0))
            | ((dr["party"] == "R") & (dr["econ"] > 0)),
            weights=wd,
        ))
        align_y = float(np.average(
            ((dr["party"] == "D") & (dr["cult"] < 0))
            | ((dr["party"] == "R") & (dr["cult"] > 0)),
            weights=wd,
        ))

        # Independent fraction (relative to D+I+R)
        n_i = len(sub[sub["party"] == "I"])
        indep_frac = float(np.average(
            sub["party"] == "I", weights=sub["weight"].values
        ))

        twopty_stats = {
            "n_two_party": int(len(dr)),
            "party_sep": party_sep,
            "cent_d_x": cent_d[0], "cent_d_y": cent_d[1],
            "cent_r_x": cent_r[0], "cent_r_y": cent_r[1],
            "wp_sd_x_pool": wp_sd_x_pool,
            "wp_sd_y_pool": wp_sd_y_pool,
            "wp_sd_x_d": wp_sd_x_d, "wp_sd_y_d": wp_sd_y_d,
            "wp_sd_x_r": wp_sd_x_r, "wp_sd_y_r": wp_sd_y_r,
            "align_x": align_x,
            "align_y": align_y,
            "indep_frac": indep_frac,
        }
        rows.append({"decade": decade, **all_stats, **twopty_stats})

    # Centroid velocities (per-decade Δ on each axis, for each party)
    velocities = []
    decades_sorted = sorted(DECADE_WAVES.keys())
    for i in range(1, len(decades_sorted)):
        prev = rows[i - 1]
        cur = rows[i]
        velocities.append({
            "from": prev["decade"], "to": cur["decade"],
            "n_ticks": (cur["decade"] - prev["decade"]) * 3,  # 3 ticks/yr
            "dD_x": cur["cent_d_x"] - prev["cent_d_x"],
            "dD_y": cur["cent_d_y"] - prev["cent_d_y"],
            "dR_x": cur["cent_r_x"] - prev["cent_r_x"],
            "dR_y": cur["cent_r_y"] - prev["cent_r_y"],
            "dsep": cur["party_sep"] - prev["party_sep"],
        })
        # Per-tick rates for direct use in ELITE_DRIFT_SCHEDULE:
        v = velocities[-1]
        v["per_tick_D_x"] = v["dD_x"] / v["n_ticks"]
        v["per_tick_D_y"] = v["dD_y"] / v["n_ticks"]
        v["per_tick_R_x"] = v["dR_x"] / v["n_ticks"]
        v["per_tick_R_y"] = v["dR_y"] / v["n_ticks"]

    # Sigmoid K back-solver. ANES align_x → K such that
    # E[ P(sign(x)==party) ] = align_x, given the engine's IC draw
    # (pos_x = side·0.15 + N(0, 0.45)). Since the IC draw is complicated,
    # we instead use the simple "half-population" identity: at align_x,
    # the implied K satisfies
    #     align_x ≈ 0.5 * (1 + erf( |mu| / (sigma * sqrt(2)) ))
    # ish — but easier: invert directly given empirical x-distribution.
    # For each respondent, P(party = sign(x) | K, x) = sigmoid(K*x);
    # mean over weighted respondents = empirical align_x. We grid-search K.
    print("\nSigmoid K back-solve (engine sigmoid_arg = pos_x):")
    print(" decade  align_x  K (calibrated to match align_x)")
    k_anchors = {}
    for decade, waves in DECADE_WAVES.items():
        sub = df[(df["year"].isin(waves)) & (df["party"].isin(["D", "R"]))].copy()
        if len(sub) == 0:
            continue
        x = sub["econ"].values
        w = sub["weight"].values
        align_x = float(np.average(
            ((sub["party"] == "D") & (x < 0))
            | ((sub["party"] == "R") & (x > 0)),
            weights=w,
        ))
        # Grid search K
        ks = np.linspace(0.5, 12.0, 230)
        # P(R | x, K) = sigmoid(K*x); empirical Pr(R|x) at given K's
        # expected sign-alignment is:
        #   E[Pr(party = sign(x))] = E[ sigmoid(K*x) * 1{x>0}
        #                              + (1-sigmoid(K*x)) * 1{x<0} ]
        # Inverts to E[1{x>0} P(R|x) + 1{x<0} P(D|x)] using only x.
        # We use the empirical x-distribution as the marginal:
        x_pos = x > 0
        x_neg = x < 0
        align_at_k = []
        for K in ks:
            p_r = 1.0 / (1.0 + np.exp(-K * x))
            implied_align = float(np.average(
                np.where(x_pos, p_r, np.where(x_neg, 1.0 - p_r, 0.5)),
                weights=w,
            ))
            align_at_k.append(implied_align)
        align_at_k = np.array(align_at_k)
        best_k = float(ks[np.argmin(np.abs(align_at_k - align_x))])
        k_anchors[decade] = {
            "align_x": align_x, "K_match": best_k,
            "implied_align_at_K_match": float(
                align_at_k[np.argmin(np.abs(align_at_k - align_x))]
            ),
        }
        print(f"  {decade}    {align_x:.3f}    {best_k:.2f}")

    # Save everything
    out = {
        "source": str(CSV.relative_to(ROOT)),
        "n_total": int(len(df)),
        "decades": rows,
        "centroid_velocities": velocities,
        "sigmoid_K_anchors": k_anchors,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\n[dump] {OUT}")

    # Human-readable summary
    print("\n" + "=" * 78)
    print("ANES anchors for re-deriving historical_arc knobs:")
    print("=" * 78)
    print("\nPer-decade two-party stats (weighted):")
    print("  decade  party_sep  wp_sd_x  wp_sd_y  D=(x,y)         R=(x,y)")
    for r in rows:
        print(f"  {r['decade']}    {r['party_sep']:.3f}    "
              f"{r['wp_sd_x_pool']:.3f}    {r['wp_sd_y_pool']:.3f}    "
              f"({r['cent_d_x']:+.3f},{r['cent_d_y']:+.3f})  "
              f"({r['cent_r_x']:+.3f},{r['cent_r_y']:+.3f})")
    print(f"\nIndependent fraction: ~{rows[0]['indep_frac']:.2f} (1980) ... "
          f"{rows[-1]['indep_frac']:.2f} (2020)")
    print("\nCentroid velocities (per-tick rates, 3 ticks/yr):")
    for v in velocities:
        print(f"  {v['from']}->{v['to']} ({v['n_ticks']} ticks):  "
              f"D_x={v['per_tick_D_x']:+.4f}  D_y={v['per_tick_D_y']:+.4f}  "
              f"R_x={v['per_tick_R_x']:+.4f}  R_y={v['per_tick_R_y']:+.4f}")


if __name__ == "__main__":
    main()
