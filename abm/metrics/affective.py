"""
Affective and identity-based polarization metrics.

These need access to agent.state.attrs (party, affect), not just positions —
hence a separate module from the position-only metrics in polarization.py.

- affective_polarization(agents): mean out-party warmth across the population,
  clipped to [-1, 1]. More negative = more affectively polarized.
  Mirrors the operationalization in Reiljan (2020) / Wagner (2021).
- ideological_constraint(agents): per-axis |Pearson r| between party id and
  issue position. Higher = parties are better sorted along that axis
  (Baldassarri & Gelman 2008).
- sorting_index(agents): mean |Pearson r| between party id and each
  identity dimension. The Mason 2018 mega-identity quantity — how aligned
  cross-cutting identities are with party.
"""
from __future__ import annotations

import numpy as np


def affective_polarization(agents) -> float:
    """Mean out-party warmth across all (agent, other-party) pairs."""
    vals: list[float] = []
    for a in agents:
        affect = a.state.attrs.get("affect")
        if not affect:
            continue
        for warmth in affect.values():
            vals.append(float(np.clip(warmth, -1.0, 1.0)))
    if not vals:
        return float("nan")
    return float(np.mean(vals))


def sorting_index(agents) -> float:
    """Mean |Pearson r| between party id and each identity dimension.
    Returns nan if agents lack identities."""
    parties = np.array([a.state.attrs.get("party", -1) for a in agents])
    mask = parties >= 0
    if mask.sum() < 2:
        return float("nan")
    ids_list = [a.state.attrs.get("identities") for a in agents]
    have_ids = [i for i, x in enumerate(ids_list) if x is not None]
    if len(have_ids) < 2:
        return float("nan")
    n_dims = len(ids_list[have_ids[0]])
    if n_dims == 0:
        return float("nan")
    p = parties[have_ids].astype(float)
    if p.std() == 0:
        return 0.0
    mat = np.array([ids_list[i] for i in have_ids])
    corrs = []
    for d in range(n_dims):
        col = mat[:, d]
        if col.std() == 0:
            corrs.append(0.0)
        else:
            corrs.append(abs(float(np.corrcoef(p, col)[0, 1])))
    return float(np.mean(corrs))


def ideological_constraint(agents) -> dict[str, float]:
    """|Pearson r| between party membership and each issue axis."""
    parties = np.array([a.state.attrs.get("party", -1) for a in agents])
    mask = parties >= 0
    if mask.sum() < 2:
        return {"x": float("nan"), "y": float("nan")}
    positions = np.array([a.state.ideology for a in agents])[mask]
    p = parties[mask].astype(float)
    if p.std() == 0:
        return {"x": 0.0, "y": 0.0}
    out: dict[str, float] = {}
    for axis, name in [(0, "x"), (1, "y")]:
        col = positions[:, axis]
        if col.std() == 0:
            out[name] = 0.0
        else:
            r = float(np.corrcoef(p, col)[0, 1])
            out[name] = abs(r)
    return out
