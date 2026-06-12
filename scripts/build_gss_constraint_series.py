"""Build the per-year GSS constraint + Baldassarri-&-Gelman dual series (MHV S4 / T4.0).

Computes, from the raw GSS Cumulative Cross-Sectional file, the two empirical
targets the S4 calibration fits the engine's emergent constraint against:

  * ``constraint_index``     -- ISSUE alignment: |corr(econ-axis, cult-axis)|,
                               pooled over Dem+Rep respondents.
  * ``constraint_index_wp``  -- the within-party version (mean over the two
                               parties of the within-party |corr|).
  * ``bg_partisan_align``    -- PARTISAN alignment (Baldassarri & Gelman 2008):
                               mean(|corr(econ-axis, party)|, |corr(cult-axis, party)|).

These mirror, item-for-item, the engine battery definitions in
``scripts/audit/battery.py`` (``constraint_index`` = |corr_xy| pooled;
``bg_partisan_align`` = mean of the two party-issue |corr|; within-party variant),
so the S4 fit compares like with like. The engine compass is 2D with
x = economic, y = cultural-moral + racial (S2 block-means readout); the GSS
econ-axis / cult-axis composites below are built to match that split.

Party coding mirrors the engine, which correlates issues with a BINARY Dem/Rep
label and excludes independents: GSS partyid 0-2 -> Dem(0), 4-6 -> Rep(1),
3 (pure independent) and 7 (other) dropped. A 7-point-partyid variant is also
emitted for reference (B&G's richer measure).

Both indices are |corr|-based, hence sign-invariant; item orientation below
("higher = conservative") only matters for building coherent multi-item axis
composites. Each orientation is validated against polviews (lib<->cons self-id):
a correctly oriented conservative item must correlate positively with polviews.

Raw input (gitignored, user-downloaded -- see .gitignore / s4_spec.md T4.0):
  data/gss_raw/gss7224_r3.dta   (GSS 1972-2024 Cumulative, NORC Release 3)
Committed output:
  data/mhv/gss_constraint_series.json

Sources (logged in docs/literature.md, same change, per CLAUDE.md I6):
  - Smith, Davern, Freese & Morgan, General Social Survey 1972-2024 Cumulative
    (NORC at U. Chicago, Release 3, 2024). Weight: WTSSALL.
  - Baldassarri & Gelman 2008, "Partisans without Constraint", AJS 114:408-446
    -- the issue-alignment vs party-alignment ("dual") distinction this measures.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DTA = ROOT / "data" / "gss_raw" / "gss7224_r3.dta"
OUT = ROOT / "data" / "mhv" / "gss_constraint_series.json"

# --- the fixed full-window battery ------------------------------------------
# (item, domain, (lo, hi) valid code range, reverse?) -- reverse=True means the
# raw scale runs liberal->conservative-DOWN so we flip it to higher=conservative.
# domain "econ" -> x-axis; "race"/"moral" -> y-axis (cultural-moral + racial),
# matching the engine block-means compass. affrmact/wrkwayup excluded from the
# fixed core (1994+ only) to keep the axis composition stable across the window.
BATTERY = [
    # economic / role of government
    ("eqwlth",   "econ", (1, 7), False),  # 1 govt reduce diff .. 7 no action
    ("helppoor", "econ", (1, 5), False),  # 1 govt act .. 5 people help selves
    ("helpsick", "econ", (1, 5), False),  # 1 govt help .. 5 selves
    ("natfare",  "econ", (1, 3), False),  # welfare spending 1 too little..3 too much
    ("natheal",  "econ", (1, 3), False),  # health spending
    # racial (-> cultural y-axis, per engine merge)
    ("helpblk",  "race", (1, 5), False),  # 1 govt help blacks .. 5 no special
    ("natrace",  "race", (1, 3), False),  # spending improving black condition
    ("racdif1",  "race", (1, 2), False),  # diffs due to discrimination? 1 yes 2 no
    # moral / cultural (-> cultural y-axis)
    ("abany",    "moral", (1, 2), False),  # allow abortion any reason 1 yes 2 no
    ("homosex",  "moral", (1, 4), True),   # 1 always wrong..4 not wrong (drop 5)
    ("premarsx", "moral", (1, 4), True),   # premarital sex 1 always wrong..4 not
    ("pornlaw",  "moral", (1, 3), True),   # 1 illegal-all..3 legal-all
    ("prayer",   "moral", (1, 2), False),  # 1 approve ban..2 disapprove (want prayer)
    ("cappun",   "moral", (1, 2), True),   # 1 favor death pen..2 oppose
    ("gunlaw",   "moral", (1, 2), False),  # 1 favor permit..2 oppose permit
    ("fefam",    "moral", (1, 4), True),   # 1 agree woman-tend-home..4 disagree
    ("fepol",    "moral", (1, 2), True),   # 1 agree women-unsuited..2 disagree
]
ECON = [it for it, d, *_ in BATTERY if d == "econ"]
RACE = [it for it, d, *_ in BATTERY if d == "race"]
MORAL = [it for it, d, *_ in BATTERY if d == "moral"]
CULT = RACE + MORAL  # engine y-axis = cultural-moral + racial

# GSS year -> engine decade bucket label (centres mirror the ANES phase9 buckets
# ~1987 / 1994 / 2004 / 2014 / 2022).
DECADE_BUCKETS = {
    1980: [1984, 1985, 1986, 1987, 1988, 1989],
    1990: [1990, 1991, 1993, 1994, 1996, 1998],
    2000: [2000, 2002, 2004, 2006, 2008],
    2010: [2010, 2012, 2014, 2016, 2018],
    2020: [2021, 2022, 2024],
}
MIN_CELL_N = 150  # drop a year/decade cell below this many usable respondents


def w_mean(x, w):
    return np.sum(w * x) / np.sum(w)


def w_std(x, w):
    m = w_mean(x, w)
    return np.sqrt(np.sum(w * (x - m) ** 2) / np.sum(w))


def w_corr(x, y, w):
    """Weighted Pearson correlation."""
    mx, my = w_mean(x, w), w_mean(y, w)
    cov = np.sum(w * (x - mx) * (y - my)) / np.sum(w)
    sx = np.sqrt(np.sum(w * (x - mx) ** 2) / np.sum(w))
    sy = np.sqrt(np.sum(w * (y - my) ** 2) / np.sum(w))
    if sx < 1e-9 or sy < 1e-9:
        return np.nan
    return cov / (sx * sy)


def _z(col, w):
    """Weighted z-score of a column (NaN-safe; NaNs stay NaN)."""
    m = col.notna().values
    out = np.full(len(col), np.nan)
    if m.sum() < 2:
        return out
    x = col.values[m].astype(float)
    ww = w[m]
    mu = w_mean(x, ww)
    sd = w_std(x, ww)
    if sd < 1e-9:
        return out
    out[m] = (x - mu) / sd
    return out


def _composite(df, items, w, min_items):
    """Row-wise mean of z-scored, oriented items; needs >= min_items present."""
    zs = np.column_stack([_z(df[it], w) for it in items])
    present = np.sum(~np.isnan(zs), axis=1)
    comp = np.nanmean(zs, axis=1)
    comp[present < min_items] = np.nan
    return comp


def compute_indices(df, w):
    """Compute the dual indices on a respondent subset (already oriented)."""
    econ = _composite(df, ECON, w, min_items=2)
    cult = _composite(df, CULT, w, min_items=3)
    party = df["party_bin"].values  # 0 Dem / 1 Rep / nan
    pid7 = df["partyid"].values     # 0..6 (already filtered to 0-6)

    both = ~np.isnan(econ) & ~np.isnan(cult)
    dr = both & ~np.isnan(party)  # Dem/Rep with both axes

    res = {"n_both": int(both.sum()), "n_dr": int(dr.sum())}
    if dr.sum() < MIN_CELL_N:
        return None

    ww = w
    # ISSUE alignment (constraint): pooled |corr(econ, cult)| over Dem+Rep
    res["constraint_index"] = abs(w_corr(econ[dr], cult[dr], ww[dr]))
    # within-party
    wp = []
    for pv in (0.0, 1.0):
        m = dr & (party == pv)
        if m.sum() > 2:
            c = w_corr(econ[m], cult[m], ww[m])
            if not np.isnan(c):
                wp.append(abs(c))
    res["constraint_index_wp"] = float(np.mean(wp)) if wp else None
    # PARTISAN alignment (binary Dem/Rep) -- engine-commensurable
    cx = abs(w_corr(econ[dr], party[dr], ww[dr]))
    cy = abs(w_corr(cult[dr], party[dr], ww[dr]))
    res["partisan_align_econ"] = float(cx)
    res["partisan_align_cult"] = float(cy)
    res["bg_partisan_align"] = float((cx + cy) / 2.0)
    # 7-point-partyid variant (B&G richer measure; includes independents 3? no --
    # pid7 here is 0-6 over Dem/Ind/Rep; use all with both axes)
    m7 = both & ~np.isnan(pid7)
    if m7.sum() > 2:
        cx7 = abs(w_corr(econ[m7], pid7[m7], ww[m7]))
        cy7 = abs(w_corr(cult[m7], pid7[m7], ww[m7]))
        res["bg_partisan_align_pid7"] = float((cx7 + cy7) / 2.0)
    return res


def main():
    items = [it for it, *_ in BATTERY]
    cols = ["year", "partyid", "polviews", "wtssall"] + items
    print(f"reading {DTA.name} ...")
    df = pd.read_stata(DTA, columns=cols, convert_categoricals=False)

    # weight: wtssall, fallback 1.0
    df["wtssall"] = df["wtssall"].fillna(1.0)

    # orient + mask each item to higher=conservative
    for it, dom, (lo, hi), rev in BATTERY:
        s = df[it].where((df[it] >= lo) & (df[it] <= hi))
        if rev:
            s = (lo + hi) - s
        df[it] = s

    # polviews validation sample (1..7, higher=conservative)
    pv = df["polviews"].where((df["polviews"] >= 1) & (df["polviews"] <= 7))
    print("\n=== orientation validation: corr(item, polviews), expect > 0 ===")
    wv = df["wtssall"].values.astype(float)
    bad = []
    for it, *_ in BATTERY:
        m = df[it].notna() & pv.notna()
        c = w_corr(df[it].values[m].astype(float), pv.values[m].astype(float), wv[m])
        flag = "" if c > 0 else "  <-- WRONG SIGN"
        if c <= 0:
            bad.append(it)
        print(f"  {it:10s} r={c:+.3f}{flag}")
    if bad:
        raise SystemExit(f"orientation error in: {bad} -- fix BATTERY reverse flags")

    # party: binary Dem(0-2)/Rep(4-6), drop Ind(3) & other(7); keep 0-6 for pid7
    pid = df["partyid"]
    df = df[(pid >= 0) & (pid <= 6)].copy()
    pb = np.full(len(df), np.nan)
    pb[df["partyid"].isin([0, 1, 2]).values] = 0.0
    pb[df["partyid"].isin([4, 5, 6]).values] = 1.0
    df["party_bin"] = pb

    # per-year series
    per_year = []
    for y in sorted(df["year"].dropna().unique()):
        sub = df[df["year"] == y]
        w = sub["wtssall"].values.astype(float)
        r = compute_indices(sub, w)
        if r is None:
            continue
        r = {"year": int(y), **r}
        per_year.append(r)

    # per-decade pooled
    by_decade = {}
    for label, years in DECADE_BUCKETS.items():
        sub = df[df["year"].isin(years)]
        if len(sub) == 0:
            continue
        w = sub["wtssall"].values.astype(float)
        r = compute_indices(sub, w)
        if r is None:
            continue
        by_decade[str(label)] = {"years": years, **r}

    # simple OLS slope per decade of the two headline indices (per year)
    def slope(metric):
        xs = np.array([d["year"] for d in per_year], float)
        ys = np.array([d.get(metric, np.nan) for d in per_year], float)
        m = ~np.isnan(ys)
        if m.sum() < 3:
            return None
        A = np.polyfit(xs[m], ys[m], 1)
        return {"per_year": float(A[0]), "intercept": float(A[1]),
                "first_year": int(xs[m].min()), "last_year": int(xs[m].max())}

    out = {
        "provenance": {
            "source": "GSS 1972-2024 Cumulative (NORC Release 3); WTSSALL weighted",
            "raw_file": "data/gss_raw/gss7224_r3.dta (gitignored, user-downloaded)",
            "generated_by": "scripts/build_gss_constraint_series.py",
            "method": ("issue alignment = |corr(econ-axis, cult-axis)| pooled over "
                       "Dem+Rep; partisan alignment = mean(|corr(econ,party)|, "
                       "|corr(cult,party)|) with binary Dem(0-2)/Rep(4-6); "
                       "axis = weighted-z item mean; mirrors scripts/audit/battery.py"),
            "battery_econ": ECON,
            "battery_cult_racial": RACE,
            "battery_cult_moral": MORAL,
            "party_coding": "partyid 0-2->Dem, 4-6->Rep, 3 & 7 dropped",
            "citation": "Baldassarri & Gelman 2008 AJS 114:408 (issue vs party alignment)",
            "engine_targets": ["constraint_index", "constraint_index_wp", "bg_partisan_align"],
        },
        "per_year": per_year,
        "by_decade": by_decade,
        "slopes": {
            "constraint_index": slope("constraint_index"),
            "bg_partisan_align": slope("bg_partisan_align"),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))

    # report
    print(f"\nwrote {OUT.relative_to(ROOT)}  ({len(per_year)} year-cells, "
          f"{len(by_decade)} decade-cells)")
    print("\n=== by decade (pooled) ===")
    print(f"{'dec':>5} {'n_dr':>6} {'constraint':>11} {'wp':>7} {'bg_partisan':>12}")
    for k in sorted(by_decade):
        d = by_decade[k]
        wp = d.get("constraint_index_wp")
        print(f"{k:>5} {d['n_dr']:>6} {d['constraint_index']:>11.3f} "
              f"{(wp if wp is not None else float('nan')):>7.3f} "
              f"{d['bg_partisan_align']:>12.3f}")
    print("\nslopes (per year):")
    for k, v in out["slopes"].items():
        if v:
            print(f"  {k:18s} {v['per_year']:+.5f}/yr  ({v['first_year']}-{v['last_year']})")


if __name__ == "__main__":
    main()
