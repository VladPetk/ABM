"""One-shot generator for ``data/mhv/party_centroid_series.json`` (MHV S3 T3.2).

The data-fed elite/party-position input: the measured ANES *voter* party
centroids (econ/cult means) by survey year, 1986–2024, with a pre-Reagan 1980
anchor prepended so the series spans engine tick 0 (Jan 1980).

Decision D-S3-1 (docs/internal/s3_spec.md): the series is driven by ANES voter
centroids, NOT DW-NOMINATE. The compass is the mass public; the drift mechanism
was already calibrated to voter velocities + provenance-re-attributed to voters;
and the elite (NOMINATE) series carries the *opposite* asymmetry (R-led ~3:1 vs
the voter D-led ~2:1). DW-NOMINATE is cited as corroborating elite evidence and
the mass-elite gap is logged as a documented blindspot — it is not wired in.

Source: data/phase9_empirical/derived/party_centroids.csv (ANES CDF recodes; the
same pipeline as the §11 compass). Provenance L. Pre-Reagan 1980 anchor from
historical_arc.PARTY_CENTERS_PRE_REAGAN_ANES (Phase 9 §11.7-E; E-graded, kept
explicit in the channels so the 1980→1986 segment is an honest interpolation
rather than a flat hold).

Run: .venv/Scripts/python.exe scripts/build_party_centroid_series.py
"""
from __future__ import annotations

import csv
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "data", "phase9_empirical", "derived", "party_centroids.csv")
OUT = os.path.join(ROOT, "data", "mhv", "party_centroid_series.json")

# Pre-Reagan 1980 anchor (engine tick 0). Mirrors
# historical_arc.PARTY_CENTERS_PRE_REAGAN_ANES; kept here as literals so this
# generator stays import-free. D = party 0, R = party 1.
PRE_REAGAN_1980 = {
    0: {"econ": -0.05, "cult": +0.05},
    1: {"econ": +0.18, "cult": +0.10},
}
_TAG = {"D": 0, "R": 1}


def main() -> None:
    rows_by_party: dict[int, dict[str, list]] = {
        0: {"econ": [], "cult": []},
        1: {"econ": [], "cult": []},
    }
    # Seed the 1980 pre-Reagan anchor.
    for pid, c in PRE_REAGAN_1980.items():
        rows_by_party[pid]["econ"].append([1980.0, c["econ"]])
        rows_by_party[pid]["cult"].append([1980.0, c["cult"]])

    with open(SRC, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["party"] not in _TAG:  # skip Independents — no centroid channel
                continue
            pid = _TAG[r["party"]]
            year = float(r["year"])
            rows_by_party[pid]["econ"].append([year, round(float(r["econ_mean"]), 6)])
            rows_by_party[pid]["cult"].append([year, round(float(r["cult_mean"]), 6)])

    channels = {}
    for pid in (0, 1):
        channels[f"p{pid}_econ"] = sorted(rows_by_party[pid]["econ"])
        channels[f"p{pid}_cult"] = sorted(rows_by_party[pid]["cult"])

    payload = {
        "name": "anes_party_centroid_series",
        "description": (
            "Measured ANES voter party centroids (econ/cult compass means) by "
            "survey year, 1986-2024, with a pre-Reagan 1980 anchor. The data-fed "
            "elite/party-position input that replaces the scheduled EliteDrift on "
            "the canonical arc (MHV S3 T3.2). ANES voter, NOT DW-NOMINATE "
            "(decision D-S3-1); mass-elite gap is a documented blindspot."
        ),
        "unit": "compass coordinate, [-1, 1] (x=economic, y=cultural)",
        "source": (
            "data/phase9_empirical/derived/party_centroids.csv (ANES CDF recodes, "
            "1986-2024); 1980 anchor = PARTY_CENTERS_PRE_REAGAN_ANES (Phase 9 "
            "§11.7-E)"
        ),
        "lne_tag": "L",
        "x": "year",
        "generator": "scripts/build_party_centroid_series.py",
        "channels": channels,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    print(f"wrote {OUT}")
    for name, rows in channels.items():
        print(f"  {name}: {len(rows)} anchors  {rows[0]} .. {rows[-1]}")


if __name__ == "__main__":
    main()
