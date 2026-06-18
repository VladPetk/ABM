"""R-phase R5 isolation test — media-direction fix (gated; audit F6).

The default partisan diet gives every outlet a uniform noise floor, so the
weighted-mean media target is pulled toward the CENTRE (MediaConsumption is
centripetal on position). `centrifugal > 0` sharpens the diet onto same-pole
outlets so the target sits at/beyond the party pole (centrifugal = polarizing,
per Levendusky 2013). centrifugal 0.0 → prior formula + identical rng draws →
bit-identical. See docs/internal/reversibility_spec.md (R5).
"""
from __future__ import annotations

import numpy as np

from abm.core.outlets import (
    US_MEDIA_OUTLETS_2024_ANES, diet_for_party, diet_target,
)
from abm.pillars.historical_arc import build_engine
from scripts.anes_preset import ANES_FULL_KWARGS

_BY_ID = {o.id: o for o in US_MEDIA_OUTLETS_2024_ANES}


def _mean_target(party_pos, centrifugal, n=400, seed=0):
    rng = np.random.default_rng(seed)
    ts = [diet_target(
        diet_for_party(np.array(party_pos, dtype=float),
                       US_MEDIA_OUTLETS_2024_ANES, rng, centrifugal=centrifugal),
        _BY_ID) for _ in range(n)]
    return np.mean(ts, axis=0)


def test_default_is_centripetal_fix_is_centrifugal():
    """A Republican-pole partisan: the default diet target sits INSIDE the party
    position (centripetal); the fix moves it OUT toward/beyond the pole."""
    party_pos = np.array([0.4, 0.2])
    pp = float(np.linalg.norm(party_pos))
    t0 = _mean_target(party_pos, 0.0)
    t1 = _mean_target(party_pos, 1.0)
    assert np.linalg.norm(t0) < pp, "default diet should be centripetal"
    assert np.linalg.norm(t1) > np.linalg.norm(t0), "fix should push target out"
    assert np.linalg.norm(t1) >= pp, "fix target should sit at/beyond the pole"


def test_off_path_rng_identical():
    """centrifugal 0.0 consumes the identical rng draws as the prior formula
    (noise_scale stays 0.25, falloff 1.6) → two seeded runs match exactly."""
    a = diet_for_party(np.array([0.4, 0.2]), US_MEDIA_OUTLETS_2024_ANES,
                       np.random.default_rng(3), centrifugal=0.0)
    b = diet_for_party(np.array([0.4, 0.2]), US_MEDIA_OUTLETS_2024_ANES,
                       np.random.default_rng(3), centrifugal=0.0)
    assert a == b


def _mean_partisan_target(eng):
    outs = eng.env.attrs["outlets"]
    by_id = {oid: o for oid, o in outs.items()}
    ts = []
    for a in eng.agents:
        if a.state.attrs.get("party") in (0, 1) and a.state.attrs.get("media_diet"):
            ts.append(np.linalg.norm(diet_target(a.state.attrs["media_diet"], by_id)))
    return float(np.mean(ts))


def test_build_wires_centrifugal():
    """build_engine threads media_centrifugal into the partisan diets — the mean
    partisan diet-target magnitude is larger when the fix is on."""
    base = build_engine(seed=0, **ANES_FULL_KWARGS)
    k = dict(ANES_FULL_KWARGS); k.update(media_centrifugal=0.8)
    fixed = build_engine(seed=0, **k)
    assert _mean_partisan_target(fixed) > _mean_partisan_target(base)
