"""Phase 7 §5 — sensitivity audit harness.

Runs the four sweeps documented in `methods.md §5` and `phase7_spec.md
§5`, prints a report. **Reports, doesn't assert** — the regression
guards (X3 backfire at default outlets; no-collapse at default
FJ_ALPHA) live in `tests/test_phase7.py`. The sweeps here explore
neighbourhood behaviour around the defaults so a human reader can
audit whether the model's findings are robust to the calibration
choices, or contingent on them.

Sweeps:
  5.1  X3 outlet-roster sensitivity (Δsep for X3 under default vs.
       polarised vs. no-Local-TV outlets).
  5.2  X5 centroid-pull magnitude (Δsep for X5 at 0.0× / 0.25× /
       0.50× / 0.75× / 1.0×).
  5.3  Phase 4 FJ_ALPHA sweep (position-histogram at 0.02 / 0.05 /
       0.08 / 0.10).
  5.4  Phase 4 INVOLUNTARY_PER_AGENT sweep (t=0 cross-cutting
       fraction at 0 / 1 / 2 / 3).

Run: `python -X utf8 scripts/phase7_sensitivity.py`. Output goes to
stdout; the implementer manually folds findings into methods.md §5.
"""
from __future__ import annotations

from copy import deepcopy

import numpy as np

from abm.core.outlets import MediaOutlet
from abm.metrics.network import cross_cutting_tie_fraction
from abm.metrics.polarization import variance
from abm.pillars import PILLAR, apply_intervention
from abm.pillars.calm_to_camps import build_engine

N = 250
TICKS = 200
SEEDS = tuple(range(12))


def party_sep(eng):
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    return float(
        np.linalg.norm(pos[parties == 0].mean(axis=0) - pos[parties == 1].mean(axis=0))
    )


# ---------------------------------------------------------------- 5.1 X3 outlets


def sweep_x3_outlets():
    """X3 'Quit cable news' — Δsep under three outlet rosters.

    Patches the roster at `abm.pillars.calm_to_camps.US_MEDIA_OUTLETS_2024`
    (the *binding* `build_engine` actually reads), not the upstream
    `abm.core.outlets` reference (which `calm_to_camps` imported once
    at module load).
    """
    import abm.pillars.calm_to_camps as _ctc
    print("\n[5.1] X3 'Quit cable news' — outlet-roster sensitivity")

    original_roster = list(_ctc.US_MEDIA_OUTLETS_2024)

    def shift_outlet(o, name, new_pos):
        if o.name != name:
            return o
        return MediaOutlet(
            o.id, o.name, np.array(new_pos, dtype=float), o.color
        )

    rosters = {
        "default": original_roster,
        "polarized": [
            shift_outlet(
                shift_outlet(o, "Fox News", [0.85, 0.65]),
                "MSNBC", [-0.85, -0.65],
            )
            for o in original_roster
        ],
        "no_local_tv": [
            o for o in original_roster if o.name != "Local TV"
        ],
    }
    from abm.pillars import X3_QUIT_CABLE_NEWS
    for label, roster in rosters.items():
        _ctc.US_MEDIA_OUTLETS_2024 = tuple(roster)
        diffs = []
        for seed in SEEDS:
            eng = build_engine(seed=seed, n_agents=N)
            apply_intervention(eng, PILLAR.interventions[4])
            eng.run(TICKS)
            sep_before = party_sep(eng)
            apply_intervention(eng, X3_QUIT_CABLE_NEWS)
            eng.run(TICKS)
            sep_after = party_sep(eng)
            diffs.append(sep_after - sep_before)
        mean = float(np.mean(diffs))
        print(f"  outlets={label:>12s}: Δsep = {mean:+.4f}")
    _ctc.US_MEDIA_OUTLETS_2024 = tuple(original_roster)


# ---------------------------------------------------------------- 5.2 X5 magnitude


def sweep_x5_magnitude():
    """X5 centroid-pull sensitivity (LEGACY — characterised the retired
    "ranked-choice voting" centroid-pull lever; X5 is now "Deprogramming
    & exit programs" (a faction-exit lever), so this magnitude axis no
    longer maps to the X5 mechanism. Kept for historical reference)."""
    from abm.pillars.interventions_phase6 import X5_DEPROGRAMMING  # noqa: F401
    print("\n[5.2] X5 (legacy RCV centroid-pull sensitivity sweep)")

    for pull in (0.00, 0.25, 0.50, 0.75, 1.00):
        diffs = []
        for seed in SEEDS:
            eng = build_engine(seed=seed, n_agents=N)
            apply_intervention(eng, PILLAR.interventions[4])
            eng.run(TICKS)
            sep_before = party_sep(eng)
            # Manually apply the centroid pull at this magnitude.
            parties = eng.env.attrs["parties"]
            for pid in list(parties.keys()):
                parties[pid] = pull * parties[pid]
            eng.run(TICKS)
            sep_after = party_sep(eng)
            diffs.append(sep_after - sep_before)
        mean = float(np.mean(diffs))
        print(f"  pull = {pull:.2f}×: Δsep = {mean:+.4f}")


# ---------------------------------------------------------------- 5.3 FJ_ALPHA


def sweep_fj_alpha():
    """Position-histogram at end-of-S4 across FJ_ALPHA values."""
    print("\n[5.3] FJ_ALPHA sweep — no-collapse property")

    # 0.14 added at MHV T0.6: the shipped historical arc runs an effective
    # alpha = 0.05 x fj_alpha_scale 2.8 = 0.14 (methods.md §5.15), which sat
    # outside the documented sweep range — the queued T0.4 honesty flag.
    for fj_alpha in (0.02, 0.05, 0.08, 0.10, 0.14):
        radii_all = []
        for seed in SEEDS:
            eng = build_engine(seed=seed, n_agents=N)
            eng.env.attrs["fj_alpha"] = fj_alpha
            apply_intervention(eng, PILLAR.interventions[4])
            eng.run(TICKS)
            radii_all.append(
                np.array([np.linalg.norm(a.state.ideology) for a in eng.agents])
            )
        radii = np.concatenate(radii_all)
        mid = float(((radii >= 0.20) & (radii < 0.50)).mean())
        extreme = float((radii >= 0.80).mean())
        center = float((radii < 0.20).mean())
        print(
            f"  α = {fj_alpha:.2f}: <0.20 = {center:.3f}, "
            f"[0.20, 0.50) = {mid:.3f}, ≥0.80 = {extreme:.3f}"
        )


# ---------------------------------------------------------------- 5.4 INVOLUNTARY_PER_AGENT


def sweep_involuntary():
    """t=0 cross-cutting tie fraction across INVOLUNTARY_PER_AGENT."""
    print("\n[5.4] INVOLUNTARY_PER_AGENT sweep — t=0 cross-cutting fraction")

    import abm.pillars.calm_to_camps as _ctc

    original = _ctc.INVOLUNTARY_PER_AGENT
    for per_agent in (0, 1, 2, 3):
        _ctc.INVOLUNTARY_PER_AGENT = per_agent
        xcs = []
        for seed in SEEDS:
            eng = build_engine(seed=seed, n_agents=N)
            xcs.append(
                cross_cutting_tie_fraction(eng.agents, eng.env.attrs["network"])
            )
        mean = float(np.mean(xcs))
        print(f"  per_agent = {per_agent}: t=0 mean cross-cutting fraction = {mean:.4f}")
    _ctc.INVOLUNTARY_PER_AGENT = original


# ---------------------------------------------------------------- main


def main():
    print("=" * 72)
    print("Phase 7 §5 — sensitivity audit")
    print(f"  N={N}, TICKS={TICKS}, seeds=0..{SEEDS[-1]}")
    print("=" * 72)
    sweep_x3_outlets()
    sweep_x5_magnitude()
    sweep_fj_alpha()
    sweep_involuntary()
    print("\n" + "=" * 72)


if __name__ == "__main__":
    main()
