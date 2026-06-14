"""Engine-wide knob audit — shared harness.

Used by the four audit phase scripts (`phase1_isolation.py`,
`phase2_freeze.py`, `phase3_pairwise.py`). Everything here is built to be
importable at module level so the worker functions pickle under the
Windows `spawn` start method used by `run_seeds_parallel`.

All full-arc runs use the canonical shipped config (`ANES_FULL_KWARGS`,
the substrate the web demo serves), seed-swept. Macro metrics per tick
are the same `measure_all` keys the publish pipeline captures, plus
`identity_alignment`.
"""
from __future__ import annotations

import numpy as np

from abm.pillars.historical_arc import (
    build_engine,
    build_schedule,
    _decade_boundary_1990,
    _decade_boundary_2000,
    _decade_boundary_2010,
    _decade_boundary_2020,
)
from abm.pillars.schedule import Schedule, ScheduledEvent, run_to
from scripts.anes_preset import ANES_FULL_KWARGS
from scripts.phase8f_lib import measure_all

# Tick layout (1980-relative, TICKS_PER_YEAR = 3).
END_TICK = 135
# Decade-bucket-centred snapshot ticks the phase9 scorer reads.
DECADE_TICKS = {1990: 42, 2000: 72, 2010: 102, 2020: 126, 2025: 135}


# ---------------------------------------------------------------------------
# Macro capture
# ---------------------------------------------------------------------------

def _macro(eng) -> dict:
    """measure_all + mean partisan identity_alignment, all floats."""
    m = dict(measure_all(eng))
    aligns = [
        float(a.state.attrs.get("identity_alignment", 0.0))
        for a in eng.agents
        if a.state.attrs.get("party") in (0, 1)
    ]
    m["identity_alignment"] = float(np.mean(aligns)) if aligns else 0.0
    return {k: (float(v) if isinstance(v, (int, float, np.floating)) else v)
            for k, v in m.items()
            if not isinstance(v, dict)}


# ---------------------------------------------------------------------------
# Schedule variants
# ---------------------------------------------------------------------------

def _decade_only_schedule() -> Schedule:
    """Only the smooth per-decade schedule-setters, none of the punctuated
    one-shot shocks (Fox, Obama, CU, Trump, threat, COVID, factions,
    Gingrich, exogenous shocks, social-media ramps). Lets the elite-drift /
    identity-sorting / coupling schedules still advance while every dated
    event is removed — the 'dated events frozen' config."""
    return Schedule([
        ScheduledEvent(30, "decade_1990", "decade boundary 1990",
                       _decade_boundary_1990),
        ScheduledEvent(60, "decade_2000", "decade boundary 2000",
                       _decade_boundary_2000),
        ScheduledEvent(90, "decade_2010", "decade boundary 2010",
                       _decade_boundary_2010),
        ScheduledEvent(120, "decade_2020", "decade boundary 2020",
                       _decade_boundary_2020),
    ])


def _make_schedule(mode: str) -> Schedule:
    if mode == "full":
        return build_schedule(
            faction_anchor_events=True,
            evidence_regrade=True,
            exogenous_shocks=True,
        )
    if mode == "decade_only":
        return _decade_only_schedule()
    if mode == "empty":
        return Schedule([])
    raise ValueError(f"unknown schedule mode {mode!r}")


# ---------------------------------------------------------------------------
# Freeze clamps — re-assert a schedule's 1980 value after each tick
# ---------------------------------------------------------------------------

def _find_rule(eng, name):
    for r in list(eng.rules.rules) + list(eng.env_rules):
        if type(r).__name__ == name:
            return r
    return None


def _capture_baseline(eng) -> dict:
    """Tick-0 (1980) values of every freezable knob."""
    base = {}
    ed = _find_rule(eng, "EliteDrift")
    if ed is not None:
        base["elite_drift"] = (ed.rate, ed.rate_y,
                               dict(ed.asymmetric) if ed.asymmetric else {})
    isr = _find_rule(eng, "IdentitySorting")
    if isr is not None:
        base["identity_sorting"] = isr.sort_rate
    bc = _find_rule(eng, "BoundedConfidenceInfluence")
    if bc is not None:
        base["social_media_bc_aw"] = bc.affect_weight
    base["coupling"] = float(eng.env.attrs.get("party_issue_coupling", 1.0))
    base["mediated_animus_weight"] = float(
        eng.env.attrs.get("mediated_animus_weight", 0.0))
    base["party_k_schedule"] = dict(eng.env.attrs.get(
        "party_assignment_k_schedule", {}))
    # 1980 K value — the segment that holds at build.
    ks = base["party_k_schedule"]
    base["party_k_1980"] = ks.get("1980-90", next(iter(ks.values()), None)) if ks else None
    return base


def _apply_freeze(eng, freeze: set, base: dict) -> None:
    """Re-assert frozen knobs to their 1980 baseline. Called after each tick."""
    if "elite_drift" in freeze and "elite_drift" in base:
        ed = _find_rule(eng, "EliteDrift")
        if ed is not None:
            rate, rate_y, asym = base["elite_drift"]
            ed.rate = rate
            ed.rate_y = rate_y
            ed.asymmetric = dict(asym)
    if "identity_sorting" in freeze and "identity_sorting" in base:
        isr = _find_rule(eng, "IdentitySorting")
        if isr is not None:
            isr.sort_rate = base["identity_sorting"]
    if "coupling" in freeze:
        eng.env.attrs["party_issue_coupling"] = base["coupling"]
    if "party_k" in freeze and base.get("party_k_1980") is not None:
        k0 = base["party_k_1980"]
        eng.env.attrs["party_assignment_k_schedule"] = {
            seg: k0 for seg in base["party_k_schedule"]
        }
    if "social_media" in freeze:
        bc = _find_rule(eng, "BoundedConfidenceInfluence")
        if bc is not None and "social_media_bc_aw" in base:
            bc.affect_weight = base["social_media_bc_aw"]
        eng.env.attrs["mediated_animus_weight"] = base["mediated_animus_weight"]
    # MHV S3 T3.5 — pin the data-fed input series (elite party centroids +
    # media coupling) at their 1980 value. The input rules self-gate on this
    # flag and stop writing, so the centroids stay at the build IC and the
    # media coupling falls back to the (1980 = off) rule values. This is the
    # "input-carried" instrument: the budget can now distinguish emergent vs
    # data-fed-input vs residual-schedule contributions.
    if "data_fed_inputs" in freeze:
        eng.env.attrs["_freeze_data_fed_inputs"] = True
    # Emergence-recovery E5.2 — pin the endogenous activist->elite->mass loop
    # (ActivistEliteCue self-gates on this flag and stops moving the elite /
    # pushing party_cue). The loop-OFF counterfactual: the share of party_sep's
    # rise that collapses when frozen is the loop-attributable (emergent) share.
    if "endogenous_loop" in freeze:
        eng.env.attrs["_freeze_endogenous_loop"] = True


# ---------------------------------------------------------------------------
# Full-arc runner
# ---------------------------------------------------------------------------

def run_arc(
    seed: int,
    overrides: dict | None = None,
    freeze: set | None = None,
    schedule_mode: str = "full",
    capture: str = "series",
) -> dict:
    """Run the historical arc once.

    overrides: kwargs merged over ANES_FULL_KWARGS.
    freeze: set of schedule names to clamp at their 1980 value each tick.
    schedule_mode: 'full' | 'decade_only' | 'empty'.
    capture: 'series' (per-tick macro list) | 'final' (last tick only).
    """
    freeze = set(freeze or ())
    kwargs = dict(ANES_FULL_KWARGS)
    if overrides:
        kwargs.update(overrides)
    eng = build_engine(seed=seed, **kwargs)
    sched = _make_schedule(schedule_mode)
    base = _capture_baseline(eng)
    # Clamp at tick 0 too (party_k / coupling may carry build-time values).
    _apply_freeze(eng, freeze, base)

    series = [_macro(eng)]
    for t in range(1, END_TICK + 1):
        run_to(eng, sched, t)
        _apply_freeze(eng, freeze, base)
        series.append(_macro(eng))

    if capture == "final":
        return {"seed": seed, "final": series[-1]}
    return {"seed": seed, "series": series}


# ---------------------------------------------------------------------------
# Workers (top-level, picklable)
# ---------------------------------------------------------------------------

def freeze_worker(arg):
    """arg = (seed, freeze_tuple, schedule_mode). Returns full series."""
    seed, freeze_tuple, schedule_mode = arg
    return run_arc(seed, freeze=set(freeze_tuple),
                   schedule_mode=schedule_mode, capture="series")


def override_worker(arg):
    """arg = (seed, overrides_items_tuple). Returns final macro only."""
    seed, overrides_items = arg
    overrides = dict(overrides_items)
    return run_arc(seed, overrides=overrides, capture="final")


def override_series_worker(arg):
    """arg = (label, seed, overrides_items_tuple). Returns final macro plus
    decade-snapshot macro for full-arc sign checks."""
    label, seed, overrides_items = arg
    overrides = dict(overrides_items)
    res = run_arc(seed, overrides=overrides, capture="series")
    series = res["series"]
    snaps = {str(t): series[t] for t in DECADE_TICKS.values()}
    return {"label": label, "seed": seed, "final": series[-1], "snaps": snaps}
