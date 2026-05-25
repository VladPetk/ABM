"""
MediaOutlet — a named information source with an ideological position.

Outlets aren't agents (they don't update their own views); they're stationary
attractors that pull subscribers toward them. Each scenario can declare its
own outlet roster (real US media for elite_dynamics, hypothetical for others).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class MediaOutlet:
    id: int
    name: str
    position: np.ndarray        # ideology (x, y) in [-1, 1]²
    color: str = "#74797f"      # neutral ink by default; viz overrides per outlet


# Approximate empirical positions for major US outlets on a
# free-market(+x) / cultural-conservative(+y) compass. Calibrated against
# media-bias rating aggregators (AllSides, Ad Fontes); rough but in the
# right direction. Easy to tweak when richer data is available.
US_MEDIA_OUTLETS_2024 = [
    MediaOutlet(id=0, name="MSNBC",        position=np.array([-0.55, -0.35]), color="#1f3565"),
    MediaOutlet(id=1, name="New York Times", position=np.array([-0.40, -0.20]), color="#2a4a52"),
    MediaOutlet(id=2, name="Local TV",     position=np.array([ 0.00,  0.05]), color="#74797f"),
    MediaOutlet(id=3, name="Wall St Journal", position=np.array([ 0.50,  0.15]), color="#553f6b"),
    MediaOutlet(id=4, name="Fox News",     position=np.array([ 0.65,  0.45]), color="#8b2530"),
]


def diet_for_party(party_pos: np.ndarray, outlets: list[MediaOutlet], rng) -> dict[int, float]:
    """
    Generate a starting media diet for an agent given their party's position.
    Outlets closer (in ideology) to the agent's party get higher weights,
    softened by exp falloff so people don't get a 100%-aligned diet by default.
    Adds small noise so two same-party agents have slightly different diets.
    """
    weights = {}
    for o in outlets:
        d = float(np.linalg.norm(o.position - party_pos))
        w = float(np.exp(-d * 1.6)) + float(rng.uniform(0, 0.25))
        weights[o.id] = w
    total = sum(weights.values()) or 1.0
    return {k: v / total for k, v in weights.items()}


def diet_target(diet: dict[int, float], outlets_by_id: dict[int, MediaOutlet]) -> np.ndarray:
    """Weighted-mean of consumed outlets' positions — the agent's media pull target."""
    if not diet:
        return np.zeros(2)
    total = sum(diet.values()) or 1.0
    target = np.zeros(2)
    for oid, w in diet.items():
        outlet = outlets_by_id.get(oid)
        if outlet is None:
            continue
        target = target + (w / total) * outlet.position
    return target
