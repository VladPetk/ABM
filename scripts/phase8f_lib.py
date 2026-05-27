"""Phase 8f library — measurement, overrides, variant registry,
schedule patching. Imported by phase8f_diagnostic_runner.py and the
later experiment drivers.

Variants are registered in `VARIANTS`. To add a new one, edit this
file (or call register_variant). Each variant is a list of override
tuples; see _apply_overrides / _patch_schedules.
"""
from __future__ import annotations

import os
import numpy as np

from abm.metrics.affective import affective_polarization, ideological_constraint
from abm.metrics.network import cross_cutting_tie_fraction, party_modularity
from abm.metrics.polarization import variance
from abm.pillars import historical_arc as ha
from abm.pillars.schedule import run_to


PRIMARY_TARGETS = {
    1990: {"constraint": (0.35, 0.50), "party_sep": (0.50, 0.65),
           "affect": (-0.45, -0.30), "within_party_sd": (0.18, 0.32)},
    2000: {"constraint": (0.45, 0.60), "party_sep": (0.55, 0.70),
           "affect": (-0.55, -0.40), "within_party_sd": (0.18, 0.30)},
    2010: {"constraint": (0.55, 0.70), "party_sep": (0.60, 0.75),
           "affect": (-0.65, -0.50), "within_party_sd": (0.17, 0.28)},
    2020: {"constraint": (0.60, 0.75), "party_sep": (0.65, 0.80),
           "affect": (-0.78, -0.60), "within_party_sd": (0.15, 0.25)},
    2025: {"constraint": (0.62, 0.78), "party_sep": (0.68, 0.82),
           "affect": (-0.85, -0.65), "within_party_sd": (0.15, 0.22)},
}
INITIAL_TARGETS_1980 = {
    "variance": (0.45, 0.60), "constraint": (0.25, 0.40),
    "party_sep": (0.45, 0.60), "affect": (-0.35, -0.20),
    "within_party_sd": (0.20, 0.35), "xc_fraction": (0.30, 0.40),
}


def party_sep_metric(eng):
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    if (parties == 0).sum() == 0 or (parties == 1).sum() == 0:
        return 0.0
    return float(np.linalg.norm(
        pos[parties == 0].mean(axis=0) - pos[parties == 1].mean(axis=0)
    ))


def within_party_sd_x(eng):
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    sds = []
    for p in (0, 1):
        mask = parties == p
        if mask.sum() > 1:
            sds.append(float(pos[mask, 0].std()))
    return float(np.mean(sds)) if sds else 0.0


def constraint_avg(eng):
    ic = ideological_constraint(eng.agents)
    return (ic["x"] + ic["y"]) / 2.0


def measure_all(eng):
    return {
        "variance": float(variance(eng.positions())),
        "constraint": constraint_avg(eng),
        "party_sep": party_sep_metric(eng),
        "affect": affective_polarization(eng.agents),
        "within_party_sd": within_party_sd_x(eng),
        "xc_fraction": cross_cutting_tie_fraction(
            eng.agents, eng.env.attrs["network"]),
        "modularity": party_modularity(
            eng.agents, eng.env.attrs["network"]),
    }


def in_band(value, band) -> bool:
    lo, hi = band
    return lo <= value <= hi


# --- post-build helpers ----------------------------------------------


def _strip_media_cue(eng):
    for a in eng.agents:
        a.state.attrs.pop("media_cue", None)


def _strip_party_cue(eng):
    for a in eng.agents:
        a.state.attrs.pop("party_cue", None)


def _half_indep_bc_weight(eng):
    """Give Independents a low BC weight by tagging them, then
    BoundedConfidenceInfluence consults it via env. Stub for now."""
    pass


def _zero_media(eng):
    """Replace MediaConsumption.strength with 0 AND patch the schedule
    events that would re-enable it. Hack: monkeypatch the events here.
    """
    for r in eng.rules.rules:
        if type(r).__name__ == "MediaConsumption":
            r.strength = 0.0
            r.__class__.apply_original = r.__class__.apply
            r.__class__.apply = lambda self, *a, **k: __import__(
                "abm.core.state", fromlist=["StateDelta"]
            ).StateDelta()


def _stub_partisan_exit(eng):
    """Stub for future per-tick rule that moves misaligned partisans
    to party=2 (Independent)."""
    pass


def _add_y_axis_sort_by(eng, mag):
    import numpy as np
    parties = eng.env.attrs.get("parties", {})
    if 0 in parties:
        parties[0] = np.clip(parties[0] + np.array([0.0, -mag]), -1.0, 1.0)
    if 1 in parties:
        parties[1] = np.clip(parties[1] + np.array([0.0, +mag]), -1.0, 1.0)
    for a in eng.agents:
        cue = a.state.attrs.get("party_cue")
        if cue is None:
            continue
        p = a.state.attrs.get("party")
        if p == 0:
            a.state.attrs["party_cue"] = np.clip(cue + np.array([0.0, -mag]), -1.0, 1.0)
        elif p == 1:
            a.state.attrs["party_cue"] = np.clip(cue + np.array([0.0, +mag]), -1.0, 1.0)


def _add_y_axis_sort(eng):
    _add_y_axis_sort_by(eng, 0.25)


def _add_y_axis_sort_15(eng):
    _add_y_axis_sort_by(eng, 0.15)


def _add_y_axis_sort_10(eng):
    _add_y_axis_sort_by(eng, 0.10)


def _add_y_axis_sort_08(eng):
    _add_y_axis_sort_by(eng, 0.08)


def _bump_party_centers_outward(eng):
    """One-shot push: move env party centers further apart by 0.10
    each. Just lets us probe what a stronger centroid produces."""
    import numpy as np
    parties = eng.env.attrs.get("parties", {})
    if 0 in parties:
        parties[0] = np.clip(parties[0] + np.array([-0.10, 0.0]), -1.0, 1.0)
    if 1 in parties:
        parties[1] = np.clip(parties[1] + np.array([+0.10, 0.0]), -1.0, 1.0)
    # Also propagate to party_cue
    for a in eng.agents:
        cue = a.state.attrs.get("party_cue")
        if cue is None:
            continue
        p = a.state.attrs.get("party")
        if p == 0:
            a.state.attrs["party_cue"] = np.clip(cue + np.array([-0.10, 0.0]), -1.0, 1.0)
        elif p == 1:
            a.state.attrs["party_cue"] = np.clip(cue + np.array([+0.10, 0.0]), -1.0, 1.0)


POST_BUILD_FNS = {
    "strip_media_cue": _strip_media_cue,
    "strip_party_cue": _strip_party_cue,
    "zero_media": _zero_media,
    "bump_centers_outward": _bump_party_centers_outward,
    "add_y_axis_sort": _add_y_axis_sort,
    "add_y_axis_sort_15": _add_y_axis_sort_15,
    "add_y_axis_sort_10": _add_y_axis_sort_10,
    "add_y_axis_sort_08": _add_y_axis_sort_08,
}


# --- overrides applier -----------------------------------------------


def apply_overrides(eng, overrides):
    for ov in overrides:
        kind = ov[0]
        if kind == "rule":
            _, cls_name, attr, value = ov
            for r in eng.rules.rules:
                if type(r).__name__ == cls_name:
                    setattr(r, attr, value)
                    break
            else:
                raise KeyError(f"rule {cls_name} not in pipeline")
        elif kind == "env":
            _, key, value = ov
            eng.env.attrs[key] = value
        elif kind == "env_rule":
            _, cls_name, attr, value = ov
            for r in eng.env_rules:
                if type(r).__name__ == cls_name:
                    setattr(r, attr, value)
                    break
            else:
                raise KeyError(f"env_rule {cls_name} not in pipeline")
        elif kind == "post_build":
            _, fn_name = ov
            POST_BUILD_FNS[fn_name](eng)
        elif kind == "build_kwarg":
            pass


def patch_schedules(overrides):
    saved = {}
    for ov in overrides:
        if ov[0] != "schedule_decade":
            continue
        _, which, mapping = ov
        if which == "coupling":
            saved.setdefault("coupling", dict(ha.PARTY_ISSUE_COUPLING_SCHEDULE))
            ha.PARTY_ISSUE_COUPLING_SCHEDULE.update(mapping)
        elif which == "elite":
            saved.setdefault("elite", dict(ha.ELITE_DRIFT_SCHEDULE))
            ha.ELITE_DRIFT_SCHEDULE.update(mapping)
        elif which == "id_sort":
            saved.setdefault("id_sort", dict(ha.IDENTITY_SORTING_SCHEDULE))
            ha.IDENTITY_SORTING_SCHEDULE.update(mapping)
        elif which == "elite_asym":
            saved.setdefault("elite_asym", dict(ha.ELITE_DRIFT_ASYMMETRIC))
            ha.ELITE_DRIFT_ASYMMETRIC.clear()
            ha.ELITE_DRIFT_ASYMMETRIC.update(mapping)
    return saved


def restore_schedules(saved):
    for k, original in saved.items():
        if k == "coupling":
            ha.PARTY_ISSUE_COUPLING_SCHEDULE.clear()
            ha.PARTY_ISSUE_COUPLING_SCHEDULE.update(original)
        elif k == "elite":
            ha.ELITE_DRIFT_SCHEDULE.clear()
            ha.ELITE_DRIFT_SCHEDULE.update(original)
        elif k == "id_sort":
            ha.IDENTITY_SORTING_SCHEDULE.clear()
            ha.IDENTITY_SORTING_SCHEDULE.update(original)
        elif k == "elite_asym":
            ha.ELITE_DRIFT_ASYMMETRIC.clear()
            ha.ELITE_DRIFT_ASYMMETRIC.update(original)


def aggregate(trajectories):
    years = [1980, 1990, 2000, 2010, 2020, 2025]
    means, ses = {}, {}
    for year in years:
        per_metric = {}
        for m in trajectories[0][year]:
            per_metric[m] = [t[year][m] for t in trajectories]
        means[year] = {m: float(np.mean(v)) for m, v in per_metric.items()}
        ses[year] = {m: float(np.std(v, ddof=1) / np.sqrt(len(v)))
                     for m, v in per_metric.items()}
    return means, ses


def print_trajectory(name, means):
    print(f"\n=== variant: {name} ===")
    header = (f"  year   constraint   party_sep      affect    wp_sd  "
              f"   xc    mod")
    print(header)
    for year in [1980, 1990, 2000, 2010, 2020, 2025]:
        m = means[year]
        row = (f"  {year}  {m['constraint']:+8.3f}   "
               f"{m['party_sep']:+8.3f}   {m['affect']:+8.3f}  "
               f"{m['within_party_sd']:+6.3f}  "
               f"{m['xc_fraction']:+5.3f}  {m['modularity']:+5.3f}")
        print(row)
    in_band_count = 0
    total = 0
    miss_lines = []
    for year in [1990, 2000, 2010, 2020, 2025]:
        for metric, band in PRIMARY_TARGETS[year].items():
            total += 1
            v = means[year][metric]
            if in_band(v, band):
                in_band_count += 1
            else:
                miss_lines.append(
                    f"    {year} {metric:<16} {v:+.3f}  "
                    f"target [{band[0]:+.2f},{band[1]:+.2f}]"
                )
    if miss_lines:
        print("  misses:")
        for ln in miss_lines:
            print

def _bump_party_cue_sigma_05(eng):
    """Re-seed party_cue with wider sigma to lift within_party_sd.
    Only the historical-scenario PARTY_CUE_SIGMA_HISTORICAL is in
    scope (the calm_to_camps PARTY_CUE_SIGMA constant is forbidden)."""
    import numpy as np
    rng = np.random.default_rng(31337)
    parties = eng.env.attrs.get("parties", {})
    for a in eng.agents:
        if "party_cue" not in a.state.attrs:
            continue
        p = a.state.attrs.get("party")
        if p not in (0, 1):
            continue
        sigma = 0.50 if p == 1 else 0.40
        centroid = parties[p]
        a.state.attrs["party_cue"] = centroid + rng.normal(0.0, sigma, size=2)


def _bump_party_cue_sigma_07(eng):
    import numpy as np
    rng = np.random.default_rng(31337)
    parties = eng.env.attrs.get("parties", {})
    for a in eng.agents:
        if "party_cue" not in a.state.attrs:
            continue
        p = a.state.attrs.get("party")
        if p not in (0, 1):
            continue
        sigma = 0.70 if p == 1 else 0.50
        centroid = parties[p]
        a.state.attrs["party_cue"] = centroid + rng.normal(0.0, sigma, size=2)


def _bump_media_cue_sigma_30(eng):
    """Wider media_cue (was σ=0.15)."""
    import numpy as np
    rng = np.random.default_rng(54321)
    for a in eng.agents:
        if "media_cue" not in a.state.attrs:
            continue
        a.state.attrs["media_cue"] = rng.normal(0.0, 0.30, size=2)


POST_BUILD_FNS["bump_party_cue_05"] = _bump_party_cue_sigma_05
POST_BUILD_FNS["bump_party_cue_07"] = _bump_party_cue_sigma_07
POST_BUILD_FNS["bump_media_cue_30"] = _bump_media_cue_sigma_30


def _bump_media_cue_sigma_40(eng):
    import numpy as np
    rng = np.random.default_rng(54321)
    for a in eng.agents:
        if "media_cue" not in a.state.attrs:
            continue
        a.state.attrs["media_cue"] = rng.normal(0.0, 0.40, size=2)


def _bump_media_cue_sigma_50(eng):
    import numpy as np
    rng = np.random.default_rng(54321)
    for a in eng.agents:
        if "media_cue" not in a.state.attrs:
            continue
        a.state.attrs["media_cue"] = rng.normal(0.0, 0.50, size=2)


POST_BUILD_FNS["bump_media_cue_40"] = _bump_media_cue_sigma_40
POST_BUILD_FNS["bump_media_cue_50"] = _bump_media_cue_sigma_50


def _add_y_axis_sort_09(eng):
    _add_y_axis_sort_by(eng, 0.09)


def _add_y_axis_sort_07(eng):
    _add_y_axis_sort_by(eng, 0.07)


POST_BUILD_FNS["add_y_axis_sort_09"] = _add_y_axis_sort_09
POST_BUILD_FNS["add_y_axis_sort_07"] = _add_y_axis_sort_07
