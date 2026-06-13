"""Per-year, per-party, per-ITEM ANES means — the A6 ground truth.

The realism battery's per-issue check (A6) needs the ANES marginal of each of
the 7 compass items *over time*, by party — the thing the block-mean compass
projection hides (and the racial item VCF0830, which is folded into the y-axis
and is otherwise structurally invisible). The committed `issue_loadings.json`
only carries the frozen 1986 wave; this script recodes every available wave.

Recode recipe is byte-identical to `scripts/build_issue_loadings.py` / the
canonical `anes_2d_compass.py` (same items, same reverse flags, same party map,
same [-1,1] rescale) — so the per-item means are commensurable with the seeded
substrate. Output cached to
`data/phase9_empirical/derived/anes_item_means_by_year.json` so the 156 MB raw
read happens once.

Run:  .venv/Scripts/python.exe scripts/audit/build_anes_item_means.py
"""
from __future__ import annotations

import csv
import json
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_ANES = os.path.join(ROOT, "data", "phase9_empirical", "raw", "timeseries_csv.csv")
OUT = os.path.join(ROOT, "data", "phase9_empirical", "derived",
                   "anes_item_means_by_year.json")

YEAR_VAR = "VCF0004"
PARTY_VAR = "VCF0301"     # 7-pt party ID; 1-3 D (incl. leaners), 4 I, 5-7 R
WEIGHT_VAR = "VCF0009z"

# (lo, hi, missing_codes, reverse, block, label) — verbatim from build_issue_loadings.ITEMS
ITEMS = {
    "VCF0803": (1, 7, (0, 9), False, "econ", "lib-cons 7-pt self-placement"),
    "VCF0809": (1, 7, (0, 9), False, "econ", "guaranteed jobs/income"),
    "VCF0839": (1, 7, (0, 9), True, "econ", "services-spending REVERSED"),
    "VCF0838": (1, 4, (0, 9), True, "cultural_moral", "abortion 4-pt REVERSED"),
    "VCF0852": (1, 5, (8, 9), False, "cultural_moral", "adjust moral views"),
    "VCF0853": (1, 5, (8, 9), True, "cultural_moral", "traditional values REVERSED"),
    "VCF0830": (1, 7, (0, 9), False, "racial", "aid to blacks"),
}
LABELS = list(ITEMS)
_PARTY = {1: 0, 2: 0, 3: 0, 5: 1, 6: 1, 7: 1, 4: 2}
_TAG = {0: "dem", 1: "rep", 2: "ind"}


def _recode_item(it, raw):
    lo, hi, miss, rev, _blk, _lab = ITEMS[it]
    try:
        x = int(float(raw))
    except (ValueError, TypeError):
        return np.nan
    if x in miss or not (lo <= x <= hi):
        return np.nan
    z = (x - lo) / (hi - lo) * 2.0 - 1.0
    return -z if rev else z


def main():
    # accumulate weighted sums per (year, party, item)
    acc: dict = {}    # acc[year][party_tag][item] = [wsum, wxsum, n]
    with open(RAW_ANES, newline="") as f:
        for row in csv.DictReader(f):
            year = row.get(YEAR_VAR, "").strip()
            if not year:
                continue
            try:
                p7 = int(float(row.get(PARTY_VAR, "")))
            except (ValueError, TypeError):
                continue
            party = _PARTY.get(p7)
            if party is None:
                continue
            try:
                w = float(row.get(WEIGHT_VAR, "") or 1.0)
            except ValueError:
                w = 1.0
            tag = _TAG[party]
            ydict = acc.setdefault(year, {})
            pdict = ydict.setdefault(tag, {})
            for it in LABELS:
                v = _recode_item(it, row.get(it, ""))
                if np.isnan(v):
                    continue
                cell = pdict.setdefault(it, [0.0, 0.0, 0])
                cell[0] += w
                cell[1] += w * v
                cell[2] += 1

    out = {"_meta": {"source": "ANES CDF timeseries_csv.csv (raw)",
                     "recode": "verbatim build_issue_loadings.ITEMS",
                     "items": {k: {"block": v[4], "label": v[5]}
                               for k, v in ITEMS.items()},
                     "party_map": "VCF0301 1-3=dem, 4=ind, 5-7=rep; weight VCF0009z"},
           "by_year": {}}
    for year in sorted(acc, key=lambda y: int(y) if y.isdigit() else 0):
        if not year.isdigit():
            continue
        yi = int(year)
        rec = {}
        for tag in ("dem", "rep", "ind"):
            pd = acc[year].get(tag, {})
            rec[tag] = {}
            for it in LABELS:
                c = pd.get(it)
                if c and c[0] > 0 and c[2] >= 30:   # need >=30 respondents
                    rec[tag][it] = {"mean": c[1] / c[0], "n": c[2]}
        out["by_year"][str(yi)] = rec

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"), ensure_ascii=False)
    years = sorted(int(y) for y in out["by_year"])
    print(f"wrote {OUT}")
    print(f"  years: {years[0]}..{years[-1]} ({len(years)} waves)")
    # spot check: racial item Dem vs Rep trajectory
    print("  VCF0830 (aid to blacks) Dem/Rep means by available wave:")
    for y in years:
        d = out["by_year"][str(y)].get("dem", {}).get("VCF0830")
        r = out["by_year"][str(y)].get("rep", {}).get("VCF0830")
        if d and r:
            print(f"    {y}: dem {d['mean']:+.3f}  rep {r['mean']:+.3f}  gap {r['mean']-d['mean']:+.3f}")


if __name__ == "__main__":
    main()
