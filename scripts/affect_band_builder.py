"""Build per-decade affect (out-party warmth) bands from real ANES.

Companion to `scripts/phase9_anes_target_builder.py` (which builds the
issue-polarization KDE/pointcloud targets from `respondent_coordinates.csv`).
The issue-pol bands in `phase8f_lib.ANES_PRIMARY_TARGETS` were derived directly
from ANES respondent coordinates; the **affect** band was the lone exception —
it was hand-scaled off Iyengar 2019 / Finkel 2020 figure 1, because the ANES
2D-ideology recode never extracted a feeling thermometer. This script closes
that gap: it derives the affect band from the SAME ANES cumulative file, the
same partisan universe, the same decade bucketing, and an EXPLICIT mapping.

--------------------------------------------------------------------------
The mapping (the one real modeling choice — see docs/affect_bands_investigation.md)
--------------------------------------------------------------------------
The engine's `affect` metric (abm/metrics/affective.py) is mean OUT-PARTY
warmth, seeded at 0 (neutral) and going negative, in [-1, 1]. The ANES feeling
thermometer is 0-100 with 50 explicitly labelled "neither warm nor cold". The
PRINCIPLED bijection is therefore the scale midpoint:

    aff = (deg - 50) / 50          # deg = 50 + 50*aff;  50°↔0, 0°↔-1, 100°↔+1

This is the mapping used to SCORE the engine against reality, deliberately.
The web demo's *display* mapping `deg = (1+aff)*50 + 12` (web_demo/rc-shared.jsx)
is a separate, free affine transform chosen so the sim line overlays the
empirical line — it is NOT used here. Using a display-fit offset to set scoring
bands would be circular (you can always pick the transform that "passes").
The honest scoring map is the midpoint one; what it reveals (engine over-cold
vs reality) is a real finding to fix in the engine, not hide in the transform.

Variables (ANES Time Series Cumulative Data File):
  VCF0004  year
  VCF0301  party id, 7-pt (1-3 Dem, 4 Ind, 5-7 Rep)
  VCF0218  feeling thermometer - Democratic Party
  VCF0224  feeling thermometer - Republican Party
  VCF0009z full-sample cross-section weight
Out-party rating: Dems (1-3) rate the Republican Party (VCF0224); Reps (5-7)
rate the Democratic Party (VCF0218). Independents (4) are EXCLUDED, consistent
with ideological_constraint / party_sep (partisan-only metrics). Valid degrees
0-96; 97/98/99 are ANES DK/NA codes and dropped.

Outputs (data/phase9_empirical/derived/):
  outparty_thermometer.csv   per-wave + per-decade weighted out-party therm
  affect_bands.json          per-decade affect band + full provenance
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
RAW = ROOT / "data" / "phase9_empirical" / "raw" / "timeseries_csv.csv"
DERIVED = ROOT / "data" / "phase9_empirical" / "derived"

# Same decade bucketing as scripts/phase9_anes_target_builder.py.
DECADE_WAVES = {
    1990: [1990, 1992, 1994, 1996, 1998],
    2000: [2000, 2004, 2008],
    2010: [2012, 2016],
    2020: [2020, 2024],
}
IC_1980_WAVES = [1986, 1988]   # the 1980 initial-conditions panel

# Band half-width FLOOR (affect units). The dominant real uncertainty is NOT
# sampling (SE ~ 0.005 here) but (a) instrument choice — the party thermometer
# VCF0218/24 vs the "ordinary partisans" thermometer VCF0201/02 (Druckman &
# Levendusky: the party item overstates animus toward ordinary voters), and
# (b) the mapping. We set the band to the wider of the decade's across-wave
# half-range and this floor, and label it an instrument/temporal allowance.
HALFWIDTH_FLOOR = 0.05


def aff_from_deg(deg: float) -> float:
    """Principled midpoint mapping: 50° = neutral = 0."""
    return (deg - 50.0) / 50.0


def _wmean(x, w):
    w = np.asarray(w, dtype=float)
    if w.sum() <= 0:
        w = np.ones_like(x, dtype=float)
    return float(np.average(x, weights=w))


def _wse(x, w):
    """Weighted SE using Kish effective n."""
    w = np.asarray(w, dtype=float)
    if w.sum() <= 0:
        w = np.ones_like(x, dtype=float)
    m = np.average(x, weights=w)
    var = np.average((x - m) ** 2, weights=w)
    neff = (w.sum() ** 2) / np.sum(w ** 2)
    return float(np.sqrt(var / neff))


def main():
    print(f"Reading {RAW.name} ...")
    cols = ["VCF0004", "VCF0301", "VCF0218", "VCF0224", "VCF0009z"]
    df = pd.read_csv(RAW, usecols=cols, low_memory=False)
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["VCF0004", "VCF0301"])
    pid = df["VCF0301"]
    dem, rep = pid.between(1, 3), pid.between(5, 7)

    def valid(t):
        return t.where((t >= 0) & (t <= 96))

    out = pd.Series(np.nan, index=df.index)
    out[dem] = valid(df["VCF0224"])[dem]   # Dems rate Rep party
    out[rep] = valid(df["VCF0218"])[rep]   # Reps rate Dem party
    df["out"] = out
    df["w"] = df["VCF0009z"].fillna(1.0)
    df = df.dropna(subset=["out"])

    # Per-wave table
    per_wave = []
    for y, g in df.groupby("VCF0004"):
        per_wave.append({
            "year": int(y), "n": int(len(g)),
            "out_deg": round(_wmean(g["out"].values, g["w"].values), 2),
        })

    def bucket_stats(waves):
        g = df[df["VCF0004"].isin(waves)]
        deg = _wmean(g["out"].values, g["w"].values)
        se = _wse(g["out"].values, g["w"].values)
        wave_degs = [w["out_deg"] for w in per_wave if w["year"] in waves]
        return deg, se, int(len(g)), wave_degs

    # 1980 initial-conditions panel + the four mainframe decades.
    rows = {}
    rows["1980IC"] = bucket_stats(IC_1980_WAVES)
    for dec, waves in DECADE_WAVES.items():
        rows[dec] = bucket_stats(waves)

    # Current hand-scaled affect bands (phase8f_lib.ANES_PRIMARY_TARGETS /
    # ANES_INITIAL_TARGETS_1980) for side-by-side comparison.
    current = {"1980IC": (-0.35, -0.20), 1990: (-0.45, -0.30),
               2000: (-0.55, -0.40), 2010: (-0.65, -0.50),
               2020: (-0.78, -0.60)}

    bands = {}
    print(f"\n{'panel':8}{'out°':>7}{'±se':>6}{'n':>7}{'aff_mid':>9}"
          f"{'  -> band (principled)':>24}{'   current (hand-scaled)':>26}")
    for key in ["1980IC", 1990, 2000, 2010, 2020]:
        deg, se, n, wave_degs = rows[key]
        center = aff_from_deg(deg)
        # across-wave half-range in affect units
        if len(wave_degs) >= 2:
            half_range = (aff_from_deg(max(wave_degs))
                          - aff_from_deg(min(wave_degs))) / 2.0
        else:
            half_range = 0.0
        hw = max(half_range, HALFWIDTH_FLOOR)
        lo, hi = round(center - hw, 3), round(center + hw, 3)
        bands[str(key)] = {
            "out_party_deg": round(deg, 2), "se_deg": round(se, 2),
            "n": n, "waves": (IC_1980_WAVES if key == "1980IC"
                              else DECADE_WAVES[key]),
            "aff_center": round(center, 3),
            "band": [lo, hi], "halfwidth": round(hw, 3),
            "halfwidth_source": ("across-wave range" if half_range > HALFWIDTH_FLOOR
                                 else f"floor {HALFWIDTH_FLOOR}"),
        }
        cb = current[key]
        print(f"{str(key):8}{deg:7.1f}{se:6.2f}{n:7d}{center:9.3f}"
              f"      [{lo:+.2f}, {hi:+.2f}]          [{cb[0]:+.2f}, {cb[1]:+.2f}]")

    # 2025: NO ANES data past 2024. Extrapolate from the 2020 bucket with a
    # wider band, explicitly flagged. (The 2020->2024 series flattened:
    # 19.0 -> 20.4, so we hold ~the 2020 level rather than project colder.)
    deg25 = rows[2020][0]
    c25 = aff_from_deg(deg25)
    bands["2025"] = {
        "out_party_deg": round(deg25, 2), "se_deg": None, "n": None,
        "waves": [], "aff_center": round(c25, 3),
        "band": [round(c25 - 0.10, 3), round(c25 + 0.10, 3)],
        "halfwidth": 0.10, "halfwidth_source": "EXTRAPOLATED (no ANES past 2024)",
        "note": "held at 2020-bucket level; 2020->2024 therm flattened (19.0->20.4)",
    }
    print(f"{'2025':8}{deg25:7.1f}{'   -':>6}{'   -':>7}{c25:9.3f}"
          f"      [{c25-0.10:+.2f}, {c25+0.10:+.2f}]   EXTRAPOLATED (no data past 2024)")

    out_csv = DERIVED / "outparty_thermometer.csv"
    pd.DataFrame(per_wave).to_csv(out_csv, index=False)
    meta = {
        "source": "ANES Time Series Cumulative Data File 1986-2024",
        "instrument": "party feeling thermometer VCF0218/VCF0224, partisans only "
                      "(VCF0301 1-3/5-7), Independents excluded, weighted VCF0009z",
        "mapping": "PRINCIPLED midpoint: aff = (deg - 50)/50 (50 = ANES neutral). "
                   "NOT the web display map deg=(1+aff)*50+12.",
        "halfwidth_floor": HALFWIDTH_FLOOR,
        "decade_waves": {str(k): v for k, v in DECADE_WAVES.items()},
        "ic_1980_waves": IC_1980_WAVES,
        "per_wave": per_wave,
        "bands": bands,
        "build_date": "2026-06",
    }
    out_json = DERIVED / "affect_bands.json"
    with open(out_json, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"\nWrote {out_csv}")
    print(f"Wrote {out_json}")
    print("\nNOTE: bands NOT wired into phase8f_lib yet — this is the grounded")
    print("estimate for review (step 2). Engine currently runs colder than these")
    print("(over-produces animus); reconciling that is step 3.")


if __name__ == "__main__":
    main()
