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
    """Mean out-party warmth across all (agent, other-party) pairs.

    Returns a number in [-1, 1]. **More negative = more affectively
    polarized** (out-party animus is higher). Following Phase 5's
    corrected ``AffectiveUpdate`` dynamics, this number is *negative-
    going* through S2 and S3 — the operational mirror of Iyengar et al.
    2019's "out-party thermometer" trajectory.

    **S4 nuance: the metric can read *less* negative at S4 than at
    S2/S3.** Cause: S4's tie-rewiring isolates some agents from any
    out-party network neighbour. ``AffectiveUpdate`` is network-mediated
    — it only fires when an agent encounters an out-party neighbour —
    so isolated agents' warmth freezes at whatever it last reached, or
    stays at the t=0 seed value of 0.0 if they never met the other side.
    Averaged across the population, those near-zero entries dilute the
    mean. Read as "S4 sorts so hard that some agents stop forming
    out-party animus altogether" — not "S4 cools the warmth back up."
    """
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
    Returns nan if agents lack identities.

    Phase 8d: Independents (party=2) are excluded — the metric
    measures partisan-identity alignment, which is undefined for
    agents with no partisan identity. Same filter as
    `ideological_constraint`.
    """
    parties = np.array([a.state.attrs.get("party", -1) for a in agents])
    # Phase 8d: only include party in {0, 1} (exclude Independents
    # and missing-party agents).
    mask = (parties == 0) | (parties == 1)
    if mask.sum() < 2:
        return float("nan")
    ids_list = [a.state.attrs.get("identities") for a in agents]
    have_ids = [
        i for i, x in enumerate(ids_list)
        if x is not None and mask[i]
    ]
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


def ideological_constraint_per_axis(agents) -> dict[str, float]:
    """Phase 8f §3 (audit small-fix) — alias-friendly explicit
    per-axis decomposition of `ideological_constraint`. Returns the
    same dict (`{"x": ..., "y": ...}`) but makes the component
    split explicit in the name. The Phase 8f investigation
    identified that the average `(cx + cy) / 2` had a hidden
    y-axis ceiling (the constraint plateau) — making per-axis
    visible to callers is the metric-side hygiene fix.
    """
    return ideological_constraint(agents)


def ideological_constraint(agents) -> dict[str, float]:
    """|Pearson r| between party membership and each issue axis.

    Phase 8d: Independents (party=2) are excluded from the
    correlation. The metric measures how well party (0 vs 1) predicts
    issue position; Independents have no partisan identity, so
    including them as a third category would distort the correlation
    rather than enrich it.
    """
    parties = np.array([a.state.attrs.get("party", -1) for a in agents])
    # Phase 8d: only include party in {0, 1}. Independents (party=2)
    # and missing-party agents excluded.
    mask = (parties == 0) | (parties == 1)
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
