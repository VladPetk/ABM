"""MHV S2 T2.1 — build the frozen issue-loadings data file.

One-shot generator for ``data/mhv/issue_loadings.json``: the D=7 ANES issue
battery (the S1-pilot-validated items), its measured 1986-wave correlation
structure, party-conditional item means/SDs, the 3-block latent map, and the
compass-readout definition. Estimated ONCE from the raw ANES cumulative file,
then frozen and committed — the engine never re-fits any of this (mhv_spec
S2/M1; s2_spec.md §1).

Recode recipe is the canonical one from ``scripts/anes_2d_compass.py``
(data/phase9_empirical/derived/recode_log.csv) — same items, same theoretical
endpoints, same reversals, same [-1, 1] mapping — so the engine's issue space
and the empirical compass pipeline share units exactly.

Wave choice: 1980 lacks VCF0839/0852/0853 entirely; **1986 is the earliest
wave carrying all seven items** and stands in as the "~1980 baseline"
(user-approved at S1; the caveat ships inside the JSON provenance block).

Blocks (S2 AGREE record): econ {VCF0803, VCF0809, VCF0839};
cultural-moral {VCF0838, VCF0852, VCF0853}; racial {VCF0830}. The compass
readout matches the empirical pipeline exactly: x = econ-core mean,
y = cultural-CORE mean where the cultural core = cultural-moral + racial
(VCF0830 sits in the cultural core there, in the racial block here — the
block map is the latent structure, the readout is the lens).

Run: .venv/Scripts/python.exe scripts/build_issue_loadings.py
"""
from __future__ import annotations

import csv
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_ANES = os.path.join(ROOT, "data", "phase9_empirical", "raw", "timeseries_csv.csv")
OUT = os.path.join(ROOT, "data", "mhv", "issue_loadings.json")

IC_WAVE = "1986"
PARTY_VAR = "VCF0301"   # 7-pt party ID; 1-3 D (incl. leaners), 4 I, 5-7 R
WEIGHT_VAR = "VCF0009z"

# (lo, hi, missing_codes, reverse) — verbatim from anes_2d_compass.py ITEMS.
ITEMS = {
    "VCF0803": (1, 7, (0, 9), False, "econ",
                "lib-cons 7-pt self-placement"),
    "VCF0809": (1, 7, (0, 9), False, "econ",
                "guaranteed jobs/income"),
    "VCF0839": (1, 7, (0, 9), True, "econ",
                "services-spending REVERSED"),
    "VCF0838": (1, 4, (0, 9), True, "cultural_moral",
                "abortion 4-pt REVERSED"),
    "VCF0852": (1, 5, (8, 9), False, "cultural_moral",
                "adjust moral views to changes"),
    "VCF0853": (1, 5, (8, 9), True, "cultural_moral",
                "more emphasis on traditional values REVERSED"),
    "VCF0830": (1, 7, (0, 9), False, "racial",
                "aid to blacks"),
}
LABELS = list(ITEMS)
ECON = [i for i, k in enumerate(LABELS) if ITEMS[k][4] == "econ"]
CULT_MORAL = [i for i, k in enumerate(LABELS) if ITEMS[k][4] == "cultural_moral"]
RACIAL = [i for i, k in enumerate(LABELS) if ITEMS[k][4] == "racial"]


def nearest_psd_corr(C: np.ndarray) -> np.ndarray:
    C = (C + C.T) / 2.0
    w, V = np.linalg.eigh(C)
    w = np.clip(w, 1e-6, None)
    C = (V * w) @ V.T
    d = np.sqrt(np.diag(C))
    C = C / np.outer(d, d)
    np.fill_diagonal(C, 1.0)
    return C


def main():
    rows, parties, weights = [], [], []
    with open(RAW_ANES, newline="") as f:
        for row in csv.DictReader(f):
            if row.get("VCF0004") != IC_WAVE:
                continue
            rec = []
            for it, (lo, hi, miss, rev, _blk, _lab) in ITEMS.items():
                v = row.get(it, "").strip()
                try:
                    x = int(float(v))
                except (ValueError, TypeError):
                    rec.append(np.nan)
                    continue
                if x in miss or not (lo <= x <= hi):
                    rec.append(np.nan)
                else:
                    z = (x - lo) / (hi - lo) * 2 - 1
                    rec.append(-z if rev else z)
            try:
                p7 = int(float(row.get(PARTY_VAR, "")))
            except (ValueError, TypeError):
                p7 = None
            party = (0 if p7 in (1, 2, 3) else 1 if p7 in (5, 6, 7)
                     else 2 if p7 == 4 else None)
            try:
                w = float(row.get(WEIGHT_VAR, "") or 1.0)
            except ValueError:
                w = 1.0
            rows.append(rec)
            parties.append(party)
            weights.append(w)

    A = np.array(rows, float)
    party = np.array([(-1 if p is None else p) for p in parties], int)
    w = np.array(weights, float)
    D = len(LABELS)

    # pooled pairwise-complete correlations (the S1 pilot recipe, unweighted
    # pairwise — 1986 is an SRS-era wave, weights are ~1)
    C = np.full((D, D), np.nan)
    n_pair = np.zeros((D, D), int)
    for i in range(D):
        for j in range(D):
            m = ~np.isnan(A[:, i]) & ~np.isnan(A[:, j])
            n_pair[i, j] = int(m.sum())
            if m.sum() > 30:
                C[i, j] = np.corrcoef(A[m, i], A[m, j])[0, 1]
    C = np.nan_to_num(C, nan=0.0)
    np.fill_diagonal(C, 1.0)
    C_psd = nearest_psd_corr(C)

    # party-conditional per-item weighted means/SDs (pairwise-available)
    def wstats(mask):
        mu, sd = [], []
        for i in range(D):
            m = mask & ~np.isnan(A[:, i])
            ww = w[m]
            x = A[m, i]
            mean = float(np.average(x, weights=ww))
            var = float(np.average((x - mean) ** 2, weights=ww))
            mu.append(round(mean, 5))
            sd.append(round(float(np.sqrt(var)), 5))
        return mu, sd, int(mask.sum())

    out_party = {}
    for p, tag in ((0, "dem"), (1, "rep"), (2, "ind")):
        mu, sd, n = wstats(party == p)
        out_party[tag] = {"item_means": mu, "item_sds": sd, "n": n}
    mu_all, sd_all, n_all = wstats(party >= -1)

    out = {
        "version": 1,
        "built": str(date.today()),
        "source": "data/phase9_empirical/raw/timeseries_csv.csv (ANES CDF)",
        "generator": "scripts/build_issue_loadings.py",
        "wave": int(IC_WAVE),
        "wave_caveat": (
            "1980 lacks VCF0839/0852/0853 entirely; 1986 is the earliest "
            "wave with all 7 items and stands in for the ~1980 baseline "
            "(user-approved at MHV S1; see methods.md)"),
        "recode": "(raw-lo)/(hi-lo)*2-1 -> [-1,1], reversed where flagged; "
                  "identical to anes_2d_compass.py / recode_log.csv",
        "party_var": PARTY_VAR + " (1-3 D incl. leaners, 4 I, 5-7 R)",
        "weight_var": WEIGHT_VAR,
        "items": [
            {"var": k, "block": ITEMS[k][4], "label": ITEMS[k][5],
             "lo": ITEMS[k][0], "hi": ITEMS[k][1],
             "miss": list(ITEMS[k][2]), "reverse": ITEMS[k][3]}
            for k in LABELS
        ],
        "blocks": {"econ": ECON, "cultural_moral": CULT_MORAL, "racial": RACIAL},
        "compass_readout": {
            "x": "mean of econ block items",
            "y": "mean of cultural_moral + racial block items "
                 "(= the empirical pipeline's cultural core, incl. VCF0830)",
            "x_idx": ECON, "y_idx": sorted(CULT_MORAL + RACIAL),
        },
        "corr_1986_raw": [[round(float(v), 5) for v in r] for r in C],
        "corr_1986_psd": [[round(float(v), 5) for v in r] for r in C_psd],
        "n_pairwise_min": int(n_pair[np.triu_indices(D, 1)].min()),
        "n_rows_wave": int(len(A)),
        "party_conditional": out_party,
        "pooled": {"item_means": mu_all, "item_sds": sd_all, "n": n_all},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)

    # console summary
    print(f"wave {IC_WAVE}: {len(A)} rows, pairwise-min n = {out['n_pairwise_min']}")
    for tag, d in out_party.items():
        ix, iy = ECON, sorted(CULT_MORAL + RACIAL)
        x = np.mean([d["item_means"][i] for i in ix])
        y = np.mean([d["item_means"][i] for i in iy])
        print(f"  {tag:4s} n={d['n']:5d}  compass=({x:+.3f}, {y:+.3f})")
    off = C_psd[np.triu_indices(D, 1)]
    print(f"corr offdiag: mean|r|={np.abs(off).mean():.3f} max={off.max():.3f}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
