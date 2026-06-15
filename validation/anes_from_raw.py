"""Recompute ANES 2D ideology anchors directly from the raw cumulative file.

Independent of abm/ and scripts/. The recode recipe (which VCF items, which
direction) is documented in data/phase9_empirical/derived/scaling_params.json and
the methodology .md; we re-implement it here from raw so the result does not
depend on the existing pipeline, then cross-check against the derived product.

Outputs validation/anchors_anes.json and prints a cross-check table.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/phase9_empirical/raw/timeseries_csv.csv"
DERIVED = ROOT / "data/phase9_empirical/derived/party_centroids.csv"
OUT = Path(__file__).resolve().parent / "anchors_anes.json"

# item -> (lo, hi, reverse). lo/hi = theoretical valid range; anything outside -> missing.
ITEMS = {
    # economic: higher final value = more laissez-faire / right
    "VCF0803": ("econ", 1, 7, False),  # lib-cons self placement (econ-laden)
    "VCF0809": ("econ", 1, 7, False),  # govt health insurance scale
    "VCF0839": ("econ", 1, 7, True),   # govt services/spending (reversed)
    # cultural: higher final value = more traditional
    "VCF0838": ("cult", 1, 4, True),   # abortion (reversed: 4=always allow -> progressive)
    "VCF0830": ("cult", 1, 7, False),  # aid to minorities / role of govt on race
    "VCF0852": ("cult", 1, 5, False),  # newer/older lifestyles tolerance
    "VCF0853": ("cult", 1, 5, True),   # moral relativism (reversed)
}
ECON = [k for k, v in ITEMS.items() if v[0] == "econ"]
CULT = [k for k, v in ITEMS.items() if v[0] == "cult"]
YEAR, PARTY, WEIGHT = "VCF0004", "VCF0301", "VCF0009z"
THERM_D, THERM_R = "VCF0218", "VCF0224"  # party feeling thermometers (0-97)


def to_num(s):
    return pd.to_numeric(s.astype(str).str.strip(), errors="coerce")


def recode_item(raw, lo, hi, reverse):
    v = to_num(raw)
    v = v.where((v >= lo) & (v <= hi))          # out-of-range -> NaN
    x = (v - lo) / (hi - lo)                      # -> [0,1]
    if reverse:
        x = 1.0 - x
    return x * 2.0 - 1.0                           # -> [-1,1]


def wmean(vals, w):
    m = vals.notna() & w.notna()
    if m.sum() == 0:
        return np.nan, 0.0
    return np.average(vals[m], weights=w[m]), w[m].sum()


def wstd(vals, w):
    m = vals.notna() & w.notna()
    if m.sum() < 2:
        return np.nan
    mu = np.average(vals[m], weights=w[m])
    return float(np.sqrt(np.average((vals[m] - mu) ** 2, weights=w[m])))


def wcorr(x, y, w):
    m = x.notna() & y.notna() & w.notna()
    if m.sum() < 3:
        return np.nan
    x, y, w = x[m], y[m], w[m]
    mx, my = np.average(x, weights=w), np.average(y, weights=w)
    cov = np.average((x - mx) * (y - my), weights=w)
    sx = np.sqrt(np.average((x - mx) ** 2, weights=w))
    sy = np.sqrt(np.average((y - my) ** 2, weights=w))
    return float(cov / (sx * sy)) if sx > 0 and sy > 0 else np.nan


def main():
    cols = list(ITEMS) + [YEAR, PARTY, WEIGHT, THERM_D, THERM_R]
    df = pd.read_csv(RAW, usecols=cols, low_memory=False)

    # recode ideology items
    for k, (_, lo, hi, rev) in ITEMS.items():
        df[k + "_z"] = recode_item(df[k], lo, hi, rev)
    df["econ"] = df[[k + "_z" for k in ECON]].mean(axis=1)
    df["cult"] = df[[k + "_z" for k in CULT]].mean(axis=1)
    # listwise: require ALL core items for a 2D coordinate (matches derived recipe)
    have_all = df[[k + "_z" for k in ECON + CULT]].notna().all(axis=1)

    # 3-pt party from 7-pt (leaners counted as partisans): 1-3 D, 4 I, 5-7 R
    p = to_num(df[PARTY])
    df["party3"] = np.where(p.between(1, 3), "D",
                     np.where(p == 4, "I",
                       np.where(p.between(5, 7), "R", None)))
    df["w"] = to_num(df[WEIGHT]).fillna(0.0)

    # out-party thermometer (0-97 valid). D -> rates R (THERM_R); R -> rates D (THERM_D)
    td = to_num(df[THERM_D]).where(lambda s: s.between(0, 100))
    tr = to_num(df[THERM_R]).where(lambda s: s.between(0, 100))
    df["outtherm"] = np.where(df["party3"] == "D", tr,
                       np.where(df["party3"] == "R", td, np.nan))

    window = range(1980, 2025)
    centroids, corrs, therm, quad = {}, {}, {}, {}
    coord = df[have_all]
    for yr, g in coord.groupby(YEAR):
        if yr not in window:
            continue
        yc = {}
        for party in ("D", "I", "R"):
            sub = g[g.party3 == party]
            ex, n = wmean(sub.econ, sub.w)
            cy, _ = wmean(sub.cult, sub.w)
            yc[party] = {
                "econ": None if np.isnan(ex) else round(float(ex), 4),
                "cult": None if np.isnan(cy) else round(float(cy), 4),
                "econ_sd": wstd(sub.econ, sub.w),
                "cult_sd": wstd(sub.cult, sub.w),
                "n_unw": int(len(sub)),
            }
        centroids[int(yr)] = yc
        # axis correlation: pooled over partisans (the "constraint"/over-correlation check)
        part = g[g.party3.isin(["D", "R"])]
        corrs[int(yr)] = round(wcorr(part.econ, part.cult, part.w), 4)
        # quadrant occupancy by party: fraction in each (econ-sign, cult-sign) quadrant.
        # UR=laissez+traditional, UL=redist+traditional, LL=redist+progressive, LR=laissez+progressive
        for party in ("D", "R"):
            sub = g[g.party3 == party]
            w = sub.w.values
            tot = w.sum() if w.sum() > 0 else 1.0
            e, c = sub.econ.values, sub.cult.values
            quad[(int(yr), party)] = {
                "UR": round(float(w[(e > 0) & (c > 0)].sum() / tot), 4),
                "UL": round(float(w[(e <= 0) & (c > 0)].sum() / tot), 4),
                "LL": round(float(w[(e <= 0) & (c <= 0)].sum() / tot), 4),
                "LR": round(float(w[(e > 0) & (c <= 0)].sum() / tot), 4),
            }

    # thermometer uses ALL respondents with a valid out-party rating (not just coord set)
    for yr, g in df.groupby(YEAR):
        if yr not in window:
            continue
        m, _ = wmean(g.outtherm, g.w)
        if not np.isnan(m):
            therm[int(yr)] = round(float(m), 2)

    result = {
        "source": "ANES cumulative timeseries, recomputed from raw",
        "items": {k: list(v) for k, v in ITEMS.items()},
        "party_centroids": centroids,
        "axis_correlation_partisan": corrs,
        "outparty_thermometer_0_97": therm,
        "quadrant_occupancy": {f"{y}_{p}": v for (y, p), v in quad.items()},
    }
    OUT.write_text(json.dumps(result, indent=2))
    print(f"wrote {OUT}")

    # ---- cross-check vs existing derived party_centroids.csv ----
    der = pd.read_csv(DERIVED)
    print("\n=== cross-check: from-raw vs derived party_centroids.csv ===")
    print(f"{'year':>5} {'party':>5} | {'econ raw/der':>16} {'cult raw/der':>16} | {'dEcon':>6} {'dCult':>6}")
    maxdiff = 0.0
    for _, row in der.iterrows():
        yr, party = int(row.year), row.party
        if yr not in centroids or party not in centroids[yr]:
            continue
        mine = centroids[yr][party]
        if mine["econ"] is None:
            continue
        de = mine["econ"] - row.econ_mean
        dc = mine["cult"] - row.cult_mean
        maxdiff = max(maxdiff, abs(de), abs(dc))
        if yr % 8 == 0 or abs(de) > 0.05 or abs(dc) > 0.05:
            print(f"{yr:>5} {party:>5} | {mine['econ']:>7.3f}/{row.econ_mean:>7.3f} "
                  f"{mine['cult']:>7.3f}/{row.cult_mean:>7.3f} | {de:>6.3f} {dc:>6.3f}")
    print(f"\nmax |diff| from-raw vs derived: {maxdiff:.4f}")
    print("(small diff => derived pipeline faithful & recipe reproduced; large => investigate)")


if __name__ == "__main__":
    main()
