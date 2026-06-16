"""Independent GSS cross-check of the ECONOMIC common-mode trend.

ANES says the partisan ECON center of mass moved rightward into the mid-90s and
leftward by the 2020s; the model (pre-fix) misses it. Here we confirm the same
secular econ tide from a *different* dataset (GSS) and different items (helppoor,
eqwlth — redistribution preferences), built from raw, and compare its SHAPE to the
exogenous Stimson-corroborated mood curve the fix feeds. If GSS independently shows
the same rightward-90s/leftward-2020s arc, matching it is not ANES over-fitting.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DTA = ROOT / "data/gss_raw/gss7224_r3.dta"
HERE = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(ROOT))
from abm.rules.cultural_common_mode import economic_mood_offset

ECON = {"helppoor": +1, "eqwlth": +1}  # higher raw = more rightward (less redistribute)


def main():
    cols = ["year", "partyid", "wtssall"] + list(ECON)
    df = pd.read_stata(DTA, columns=cols, convert_categoricals=False)
    df["w"] = pd.to_numeric(df["wtssall"], errors="coerce").fillna(0.0)
    # rightward z-index per item, pooled-standardized, then averaged
    zs = []
    for it, sign in ECON.items():
        v = pd.to_numeric(df[it], errors="coerce")
        v = v.where((v >= 0) & (v < 90))  # GSS missing codes
        zs.append(sign * (v - v.mean()) / v.std())
    df["econR"] = np.nanmean(np.vstack([z.values for z in zs]), axis=0)
    pid = pd.to_numeric(df["partyid"], errors="coerce")
    df["partisan"] = (pid <= 6) & (pid != 3)  # drop pure independents (3) + apolitical(7)

    def wmean(sub):
        m = sub["econR"].notna() & (sub["w"] > 0)
        if m.sum() < 30:
            return np.nan
        return float(np.average(sub.loc[m, "econR"], weights=sub.loc[m, "w"]))

    years = sorted(int(y) for y in df["year"].dropna().unique())
    pub, par = {}, {}
    for y in years:
        sub = df[df["year"] == y]
        pub[y] = wmean(sub)
        par[y] = wmean(sub[sub["partisan"]])

    # de-mean the partisan GSS index over the post-1985 window (the fix's window)
    win = [y for y in years if 1986 <= y <= 2024 and not np.isnan(par[y])]
    base = np.mean([par[y] for y in win])
    print("GSS partisan econ-RIGHTWARD index (z, de-meaned over 1986-2024) vs mood curve")
    print(f"{'yr':>5} {'GSS_par':>9} {'mood_curve':>11}")
    gss_series, curve_series = [], []
    for y in win:
        gv = par[y] - base
        cv = economic_mood_offset(float(y))
        gss_series.append(gv); curve_series.append(cv)
        print(f"{y:>5} {gv:>+9.3f} {cv:>+11.3f}")
    r = np.corrcoef(gss_series, curve_series)[0, 1]
    print(f"\ncorr(GSS partisan econ-rightward index, fed mood curve) = {r:+.3f}  (n={len(win)})")
    # also report the mid-90s vs 2020s contrast in GSS
    mid = np.mean([par[y] - base for y in win if 1994 <= y <= 2000])
    late = np.mean([par[y] - base for y in win if y >= 2018])
    print(f"GSS partisan econ index: mid-90s(94-00) {mid:+.3f}  vs  late(>=2018) {late:+.3f}  "
          f"(rightward-then-left: {'CONFIRMED' if mid > late else 'NOT confirmed'})")


if __name__ == "__main__":
    main()
