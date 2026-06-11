"""One-shot generator for ``data/mhv/media_penetration_series.json`` (MHV S3 T3.3).

The data-fed media channel: penetration/adoption curves that replace the
discrete Fairness-Doctrine-1987 / Fox-News-1996 / social-media-2008-12 step
events. Decision D-S3-3: built from public data, weak coupling per the
media-paradox blindspot cluster (Boxell 2017 age-gradient; Guess 2023 /
Allcott 2024 nulls; Prior 2013 / Guess 2021 heavy-tailed diets).

Channels:
- ``social_media``  — % of US adults using social media (fraction). Source:
  Pew Research Center "Social Media Use" trend. The genuinely data-fed curve;
  drives the BoundedConfidence affect_weight (homophilous echo amplifier).
  NOTE: pre-2012 anchors are approximate pending final verification at the
  T3.5 flip (Pew's 2023 methodology shift also affects comparability).
- ``internet``      — % of US adults using the internet (fraction). Source:
  Pew Research Center "Internet/Broadband" fact sheet (verified 2000-2024;
  1995 from Pew/NTIA). Context channel (not wired to a coupling yet).
- ``partisan_media``— re-expression of the FD-1987 / Fox-1996 partisan-media
  REGIME steps as a 0->1 penetration curve anchored to the documented onset
  DATES (Fairness Doctrine repealed Aug 1987; Fox News launched Oct 1996).
  Drives MediaConsumption.strength. The dates are hard facts; the curve shape
  re-expresses the existing two-step schedule (provenance N/E — a
  re-expression, not a new measurement).

Run: .venv/Scripts/python.exe scripts/build_media_penetration_series.py
"""
from __future__ import annotations

import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "data", "mhv", "media_penetration_series.json")

# Pew "Social Media Use" trend, % of US adults (fraction). Approx pre-2012.
SOCIAL_MEDIA = [
    [1980, 0.0], [2004, 0.0], [2005, 0.05], [2006, 0.11], [2008, 0.26],
    [2009, 0.34], [2010, 0.43], [2011, 0.50], [2012, 0.53], [2014, 0.58],
    [2016, 0.69], [2018, 0.69], [2019, 0.72], [2021, 0.72], [2023, 0.75],
    [2024, 0.75],
]
# Pew internet use, % of US adults (fraction). 2000-2024 verified from the
# Pew Internet/Broadband fact sheet; 1990/1995 from Pew/NTIA early tracking.
INTERNET = [
    [1990, 0.0], [1995, 0.14], [2000, 0.52], [2005, 0.68], [2008, 0.74],
    [2010, 0.76], [2012, 0.83], [2015, 0.86], [2019, 0.90], [2021, 0.93],
    [2024, 0.96],
]
# Partisan-media regime curve: 0 pre-FD, 0.5 across the talk-radio era
# (FD repeal Aug 1987 -> Fox Oct 1996), 1.0 once partisan cable news lands.
# Steep ramps at the onset dates approximate the original two-step schedule.
PARTISAN_MEDIA = [
    [1980, 0.0], [1987.0, 0.0], [1987.6, 0.5], [1996.0, 0.5],
    [1996.8, 1.0], [2025, 1.0],
]


def main() -> None:
    payload = {
        "name": "media_penetration_series",
        "description": (
            "Data-fed media channel (MHV S3 T3.3): social-media + internet "
            "adoption (Pew) and a partisan-media regime curve re-expressing the "
            "FD-1987 / Fox-1996 steps on their documented onset dates. Replaces "
            "the discrete media step events; weak coupling per the media-paradox "
            "blindspot cluster. Pre-2012 social-media anchors approximate "
            "(verify at the T3.5 flip)."
        ),
        "unit": "fraction of US adults (social_media, internet); regime index "
                "0-1 (partisan_media)",
        "source": (
            "Pew Research Center: 'Social Media Use' trend + 'Internet/Broadband' "
            "fact sheet (internet 2000-2024 verified). partisan_media: "
            "re-expression of the FD-repeal (Aug 1987) / Fox-News-launch (Oct "
            "1996) regime steps (dates HIGH; curve shape N/E)."
        ),
        "lne_tag": "L",
        "x": "year",
        "generator": "scripts/build_media_penetration_series.py",
        "channels": {
            "social_media": SOCIAL_MEDIA,
            "internet": INTERNET,
            "partisan_media": PARTISAN_MEDIA,
        },
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    print(f"wrote {OUT}")
    for name, rows in payload["channels"].items():
        print(f"  {name}: {len(rows)} anchors  {rows[0]} .. {rows[-1]}")


if __name__ == "__main__":
    main()
