"""Opaque reader for the shipped engine output. No abm/ import.

Treats web/data/baseline/seed_*.json purely as data. Provides per-year party
centroids, quadrant occupancy, axis correlation, affect, and within-party spread,
plus a multi-seed band so the battery never flags Monte-Carlo noise as a miss.
"""
import json
import os
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "web/data/baseline"
PARTY = {"D": 0, "R": 1, "I": 2}

# When MODEL_JSON is set, the canonical seed loads from that file (used to grade
# fresh baseline/emergent runs instead of the shipped canonical baseline).
_OVERRIDE = os.environ.get("MODEL_JSON")


def _canonical_seed():
    """The shipped canonical baseline seed (the only FULL per-tick export). Read
    from the manifest so this tracks the publish CANONICAL_SEED (was 0; the
    representative-seed presentation fix moved it to 1). Falls back to 0."""
    try:
        return int(json.load(open(BASE.parent / "manifest.json"))["canonical_seed"])
    except Exception:
        return 0


CANON_SEED = _canonical_seed()


def _load(seed):
    if _OVERRIDE and seed == CANON_SEED:
        return json.load(open(_OVERRIDE))
    return json.load(open(BASE / f"seed_{seed}.json"))


def year_to_tick(d, yr):
    return int(round((yr - d["tick_0_year"]) * d["ticks_per_year"]))


def _tick(d, yr):
    t = year_to_tick(d, yr)
    tk = d["ticks"][t]
    return np.array(tk["positions"]), np.array(tk["party"])


def metrics_for_seed(seed, years):
    d = _load(seed)
    out = {}
    for yr in years:
        if year_to_tick(d, yr) >= d["n_ticks"]:
            continue
        pos, party = _tick(d, yr)
        row = {}
        for lab, code in PARTY.items():
            sub = pos[party == code]
            if len(sub) == 0:
                continue
            e, c = sub[:, 0], sub[:, 1]
            row[lab] = {
                "econ": float(e.mean()), "cult": float(c.mean()),
                "econ_sd": float(e.std()), "cult_sd": float(c.std()),
                "n": int(len(sub)),
                "UR": float(np.mean((e > 0) & (c > 0))),
                "UL": float(np.mean((e <= 0) & (c > 0))),
                "LL": float(np.mean((e <= 0) & (c <= 0))),
                "LR": float(np.mean((e > 0) & (c <= 0))),
            }
        mask = (party == 0) | (party == 1)
        if mask.sum() > 3:
            row["corr"] = float(np.corrcoef(pos[mask, 0], pos[mask, 1])[0, 1])
        row["affect"] = float(d["macro"][year_to_tick(d, yr)]["affect"])
        out[yr] = row
    return out


def model_band(years, seeds=None):
    """Canonical (seed 0) metrics + an analytic sampling-noise floor.

    Only seed 0 carries per-tick agent positions; the variance-band seeds export
    `macro` scalars but `ticks: null`, so a cross-seed cloud band isn't available
    from the shipped files. Instead we attach the analytic standard error of a
    party-mean coordinate (sd/sqrt(n)) so the battery can tell a real gap from
    Monte-Carlo noise. A centroid-difference SE ~ sqrt(2)*that; a shift of 0.2 is
    many SE and not noise.
    """
    canon = metrics_for_seed(CANON_SEED, years)
    noise = {}
    for yr, row in canon.items():
        ses = []
        for p in ("D", "R"):
            if p in row and row[p]["n"] > 1:
                n = row[p]["n"]
                ses.append(row[p]["econ_sd"] / (n ** 0.5))
                ses.append(row[p]["cult_sd"] / (n ** 0.5))
        noise[yr] = float(np.mean(ses)) if ses else 0.03
    return canon, noise
