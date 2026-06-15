"""sandbox_dial_sweep.py — single-dial readout sweep for the 5-dial redesign.

Emergence-recovery v1 polish (sandbox knob redesign,
docs/internal/sandbox_knob_redesign.md). For each proposed dial, run the 5
candidate detents (other four held at the arc center) on the canonical endogenous
config (seed 0, full 1980->2025 arc) and print the 2025 readouts:

    sep (separation) · aff (animus/affect) · spread (within-party) ·
    align (mega-identity) · mod (echo-chamber modularity)

Use it to lock detents that LINEARIZE THE READOUT each dial owns (memo open
questions: dial 1 leaders, dial 4 within-party, dial 3 low-side mechanism, dial 5
rewire ladder) before re-rendering the 3,125-cell grid. Every detent is a real
build_engine config — no faked effects.

Run: PYTHONPATH=. .venv/Scripts/python.exe scripts/audit/sandbox_dial_sweep.py
"""
from __future__ import annotations

import numpy as np

from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from scripts.anes_preset import ANES_FULL_KWARGS
from scripts.phase8f_lib import measure_all

END = 135

# Candidate detents per dial (CENTER = idx2 = the shipped arc, so all-centered ==
# the calibrated baseline). Tune these until the owned readout steps ~evenly.
CANDIDATES = {
    # 1. Leaders moderate<->extreme — owns SEPARATION. elite_gain + ceiling.
    #    Defeat the tanh squash: push gain <1 / low ceiling at the low end and
    #    gain ~4-5 / ceiling ~1.2 at the high end.
    "leaders": [
        {"elite_gain": 0.55, "elite_ceiling": 0.50},
        {"elite_gain": 1.05, "elite_ceiling": 0.66},
        {"elite_gain": 1.7689, "elite_ceiling": 0.8237},   # CENTER (E4 arc)
        {"elite_gain": 3.0, "elite_ceiling": 1.05},
        {"elite_gain": 4.5, "elite_ceiling": 1.30},
    ],
    # 2. Identities cross-cutting<->stacked — owns MEGA-IDENTITY (align).
    "identities": [
        {"tier_c_identity_pull_x": 0.02 * f, "tier_c_identity_pull_y": 0.04 * f}
        for f in (0.0, 0.5, 1.0, 2.0, 3.0)
    ],
    # 3. Daily life segregated<->mixed — owns ANIMUS (affect). Two-sided:
    #    left = more parasocial animus (colder), right = cooperative contact (warmer).
    #    CENTER = arc (sandbox_animus_mult 0.655, sandbox_contact 0.0).
    "dailylife": [
        {"sandbox_animus_mult": 1.6, "sandbox_contact": 0.0},
        {"sandbox_animus_mult": 1.1, "sandbox_contact": 0.0},
        {"sandbox_animus_mult": 0.655, "sandbox_contact": 0.0},   # CENTER
        {"sandbox_animus_mult": 0.655, "sandbox_contact": 0.5},
        {"sandbox_animus_mult": 0.655, "sandbox_contact": 1.0},
    ],
    # 4. Within each party lockstep<->free-thinking — owns WITHIN-PARTY SPREAD.
    #    Attack spread from both ends: lockstep = low noise + high BC conformity;
    #    free = high noise + zero BC conformity. eps stays 0.40 (within-party).
    "within": [
        {"sandbox_diversity": 0.004, "tier_c_bc_strength": 0.22, "tier_c_bc_epsilon": 0.40},
        {"sandbox_diversity": 0.022, "tier_c_bc_strength": 0.09, "tier_c_bc_epsilon": 0.40},
        {"sandbox_diversity": 0.0478, "tier_c_bc_strength": 0.03, "tier_c_bc_epsilon": 0.40},  # CENTER
        {"sandbox_diversity": 0.105, "tier_c_bc_strength": 0.01, "tier_c_bc_epsilon": 0.40},
        {"sandbox_diversity": 0.205, "tier_c_bc_strength": 0.0, "tier_c_bc_epsilon": 0.40},
    ],
    # 5. Social ties open<->echo-chambered — owns ECHO CHAMBERS (modularity).
    #    sandbox_rewire_mult scales TieRewiring rewire_rate (0.03 * mult).
    "ties": [
        {"sandbox_rewire_mult": 0.0},
        {"sandbox_rewire_mult": 0.5},
        {"sandbox_rewire_mult": 1.0},     # CENTER (arc)
        {"sandbox_rewire_mult": 2.25},
        {"sandbox_rewire_mult": 4.0},
    ],
}


def _readouts(eng) -> dict:
    m = measure_all(eng)
    aligns = [float(a.state.attrs.get("identity_alignment", 0.0))
              for a in eng.agents if a.state.attrs.get("party") in (0, 1)]
    spreads = []
    for p in (0, 1):
        P = np.array([a.state.ideology for a in eng.agents
                      if a.state.attrs.get("party") == p])
        if len(P) > 1:
            spreads.append(float(P.std(axis=0).mean()))
    return {
        "sep": float(m["party_sep"]), "aff": float(m["affect"]),
        "spread": float(np.mean(spreads)) if spreads else 0.0,
        "align": float(np.mean(aligns)) if aligns else 0.0,
        "mod": float(m["modularity"]),
    }


def _run(overrides: dict) -> dict:
    kwargs = dict(ANES_FULL_KWARGS)
    kwargs.update(overrides)
    eng = build_engine(seed=0, **kwargs)
    sched = build_schedule(
        factional_seeding=kwargs.get("factional_seeding", False),
        faction_anchor_events=kwargs.get("faction_anchor_events", True),
        evidence_regrade=kwargs.get("evidence_regrade", False),
        exogenous_shocks=kwargs.get("exogenous_shocks", False),
    )
    for t in range(1, END + 1):
        run_to(eng, sched, t)
    return _readouts(eng)


OWNS = {"leaders": "sep", "identities": "align", "dailylife": "aff",
        "within": "spread", "ties": "mod"}


def main() -> None:
    for dial, detents in CANDIDATES.items():
        print(f"\n=== {dial}  (owns {OWNS[dial]}) ===")
        print(f"{'idx':>3} {'sep':>7} {'aff':>7} {'spread':>7} {'align':>7} {'mod':>7}   detent")
        owned = []
        for i, det in enumerate(detents):
            r = _run(det)
            owned.append(r[OWNS[dial]])
            star = " *OWN*" if i == 2 else ""
            print(f"{i:>3} {r['sep']:>7.3f} {r['aff']:>7.3f} {r['spread']:>7.3f} "
                  f"{r['align']:>7.3f} {r['mod']:>7.3f}   {det}{star}")
        steps = np.diff(owned)
        print(f"    owned readout ({OWNS[dial]}): {[round(v,3) for v in owned]}  "
              f"steps {[round(s,3) for s in steps]}")


if __name__ == "__main__":
    main()
