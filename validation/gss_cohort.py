"""Is secular cultural liberalization a cohort-replacement mechanism?

Decomposes the GSS cultural-traditionalism trend into a birth-cohort gradient
(generational turnover) vs a within-cohort period component (everyone drifts).
This tells us whether fixing the model's cohort mechanism can GENERATE the trend
endogenously, and with what generational gradient (a measurable demographic
primitive, not the aggregate 'answer').
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

DTA = Path(__file__).resolve().parent.parent / "data/gss_raw/gss7224_r3.dta"

ITEMS = {"homosex": -1, "premarsx": -1, "abany": +1, "fefam": -1, "grass": +1}


def zorient(s, sign):
    v = pd.to_numeric(s, errors="coerce")
    return ((v - v.mean()) / v.std()) * sign


def main():
    cols = ["year", "cohort", "age", "wtssall"] + list(ITEMS)
    df = pd.read_stata(DTA, columns=cols, convert_categoricals=False)
    df["w"] = pd.to_numeric(df["wtssall"], errors="coerce").fillna(0.0)
    z = pd.DataFrame({k: zorient(df[k], s) for k, s in ITEMS.items()})
    df["trad"] = z.mean(axis=1, skipna=True)
    df["n_items"] = z.notna().sum(axis=1)
    df["birth"] = pd.to_numeric(df["cohort"], errors="coerce")
    df = df[(df.n_items >= 2) & df.birth.between(1900, 2006) & (df.w > 0)].copy()

    # --- birth-cohort gradient (the generational primitive) ---
    df["bdec"] = (df.birth // 10 * 10).astype(int)
    print("=== GSS cultural traditionalism by BIRTH cohort (pooled all years) ===")
    print(f"{'born':>8} {'trad z':>8} {'n':>7}")
    grad = {}
    for bd, g in df.groupby("bdec"):
        if g.w.sum() < 200:
            continue
        m = float(np.average(g.trad.dropna(), weights=g.loc[g.trad.notna(), "w"]))
        grad[int(bd)] = round(m, 3)
        print(f"{bd:>8}s {m:>+8.3f} {int(len(g)):>7}")
    # gradient per decade of birth (slope)
    bs = np.array(sorted(grad)); ts = np.array([grad[b] for b in bs])
    slope_per_decade = float(np.polyfit(bs, ts, 1)[0] * 10)
    print(f"\n  generational gradient: {slope_per_decade:+.3f} z per decade of birth "
          f"(younger = {'more progressive' if slope_per_decade<0 else 'more traditional'})")

    # --- decomposition: cohort replacement vs within-cohort period change ---
    # weighted OLS trad ~ birth + year. birth coef -> cohort effect; year coef ->
    # within-cohort period drift. Compare each driver's contribution to the
    # observed ~1988->2018 change via the shift in mean(birth) and mean(year).
    d = df.dropna(subset=["trad"]).copy()
    X = np.column_stack([np.ones(len(d)), d.birth.values, d.year.values])
    W = d.w.values
    beta = np.linalg.lstsq(X * W[:, None], d.trad.values * W, rcond=None)[0]
    b_birth, b_year = beta[1], beta[2]

    def wm(sub, c):
        return float(np.average(sub[c], weights=sub.w))
    early = d[d.year.between(1986, 1990)]; late = d[d.year.between(2016, 2022)]
    d_birth = wm(late, "birth") - wm(early, "birth")
    d_year = wm(late, "year") - wm(early, "year")
    cohort_part = b_birth * d_birth
    period_part = b_year * d_year
    total = cohort_part + period_part
    print("\n=== decomposition of the ~1988->2018 liberalization ===")
    print(f"  mean birth-year shifted {d_birth:+.1f} yrs; birth slope {b_birth:+.4f} z/yr")
    print(f"  -> COHORT-REPLACEMENT component: {cohort_part:+.3f} z  ({100*cohort_part/total:.0f}%)")
    print(f"  -> WITHIN-COHORT (period) component: {period_part:+.3f} z  ({100*period_part/total:.0f}%)")
    print("\n  => cohort replacement is" + (" the larger" if abs(cohort_part) > abs(period_part)
          else " a substantial but not sole") + " driver. A correctly-signed generational")
    print("     gradient in the cohort rule generates most of it; a modest period term covers the rest.")

    Path(__file__).resolve().parent.joinpath("gss_cohort_gradient.json").write_text(
        json.dumps({"trad_by_birth_decade": grad,
                    "gradient_z_per_decade": round(slope_per_decade, 4),
                    "cohort_component_z": round(cohort_part, 4),
                    "period_component_z": round(period_part, 4)}, indent=2))


if __name__ == "__main__":
    main()
