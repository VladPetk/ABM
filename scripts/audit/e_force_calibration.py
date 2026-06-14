"""
Force-calibration diagnostic (emergence-recovery, pre-E3).

E2 found the endogenous loop reaches the right MAGNITUDE but the wrong SHAPE: it
jumps to equilibrium by ~1990 and plateaus, vs the real gradual 1990->2020 rise.
Two hypotheses: (a) missing time-structured forcing (Tier-2 shocks, E3), or
(b) the force is too strong — elites over-weight the activist fringe (gain 2.5
leapfrogs BEYOND the top-10% tail) and the mass takes cues too fast.

The light 3-agent literature pass (this session) supports (b): elites track /
sit at-or-just-beyond their activist base (Bawn; Bafumi-Herron; Hall's
general-election ceiling) — NOT 2.5x beyond it; and the aggregate sort took ~30
years (Levendusky), gated by awareness + a stubborn majority.

This diagnostic sweeps the elite force DOWN toward literature-plausible values
and measures the 1980->2025 trajectory SHAPE (not just the endpoint) against the
ANES-calibrated FED baseline. Question: does a gentler, literature-plausible loop
recover the gradual shape from the dynamics ALONE, before any shocks?

Run: PYTHONPATH=. .venv/Scripts/python.exe scripts/audit/e_force_calibration.py
"""
from __future__ import annotations

import json
from itertools import product
from pathlib import Path

import numpy as np

from abm.pillars.historical_arc import build_engine
from scripts.anes_preset import ANES_FULL_KWARGS

OUT_MD = Path(__file__).resolve().parents[2] / "docs" / "internal" / "audit" / "e_force_calibration.md"
DECADES = [(1980, 0), (1990, 30), (2000, 60), (2010, 90), (2020, 120), (2025, 135)]


def _sep_live(eng) -> float:
    pos = eng.positions()
    party = np.array([a.state.attrs.get("party") for a in eng.agents])
    return float(np.linalg.norm(pos[party == 0].mean(0) - pos[party == 1].mean(0)))


def decade_seps(kw: dict, seed: int = 0) -> dict:
    eng = build_engine(seed=seed, **kw)
    want = {t: yr for yr, t in DECADES}
    rec = {}
    for t in range(136):
        if t in want:
            rec[want[t]] = _sep_live(eng)
        if t < 135:
            eng.step()
    return rec


def main() -> None:
    # Reference: the ANES-calibrated FED baseline (shipped arc) shape.
    ref = decade_seps(dict(ANES_FULL_KWARGS))
    ref_years = [yr for yr, _ in DECADES]
    print("FED baseline (ANES-calibrated reference) decade sep:")
    print("  " + "  ".join(f"{yr}:{ref[yr]:.2f}" for yr in ref_years))
    full_ref = ref[2025] - ref[1980]
    ref_frac90 = (ref[1990] - ref[1980]) / full_ref
    print(f"  frac of total rise complete by 1990: {ref_frac90:.0%}\n")

    gains = (1.0, 1.3, 1.7, 2.5)             # 2.5 = E0 default (too hot); 1.0 = elite==activist base
    tails = (0.10, 0.25)                     # top-10% fringe vs broader engaged base
    pulls = (0.03, 0.08, 0.15, 0.297)        # rate-limiting sweep: very slow -> fitted uptake

    rows = []
    for gain, tail, pull in product(gains, tails, pulls):
        kw = dict(ANES_FULL_KWARGS)
        kw.update(endogenous_elite=True, data_fed_elite=False,
                  elite_gain=gain, elite_tail_q=tail,
                  tier_c_party_pull_strength=pull)
        d = decade_seps(kw)
        sse = float(sum((d[yr] - ref[yr]) ** 2 for yr in ref_years))
        rise = d[2025] - d[1980]
        frac90 = (d[1990] - d[1980]) / rise if abs(rise) > 1e-9 else float("nan")
        # fraction of the rise that lands LATE (2010->2025): ANES is back-loaded
        # (accelerating); a fixed-strength loop is front-loaded (~0 here).
        frac_late = (d[2025] - d[2010]) / rise if abs(rise) > 1e-9 else float("nan")
        rows.append(dict(gain=gain, tail=tail, pull=pull, sse=sse, frac90=frac90,
                         frac_late=frac_late, final=d[2025],
                         seps={yr: round(d[yr], 3) for yr in ref_years}))

    rows.sort(key=lambda r: r["sse"])
    print(f"ref: frac90={ref_frac90:.0%}  frac_late={(ref[2025]-ref[2010])/full_ref:.0%} "
          "(ANES is back-loaded/accelerating)\n")
    print(f"{'gain':>5}{'tail':>6}{'pull':>7}{'sse':>7}{'frac90':>8}{'fracLate':>9}{'final':>7}   decade seps")
    for r in rows:
        s = " ".join(f"{r['seps'][yr]:.2f}" for yr in ref_years)
        print(f"{r['gain']:>5}{r['tail']:>6}{r['pull']:>7}{r['sse']:>7.3f}"
              f"{r['frac90']:>8.0%}{r['frac_late']:>9.0%}{r['final']:>7.2f}   {s}")

    best = rows[0]
    print(f"\nBEST shape-match: gain={best['gain']} tail={best['tail']} pull={best['pull']} "
          f"(sse={best['sse']:.3f}, frac90={best['frac90']:.0%}, final={best['final']:.2f})")
    print(f"Reference frac90={ref_frac90:.0%}; E0-default gain=2.5 cells show frac90>>ref "
          f"(too-fast jump). Lower gain -> {'GRADUAL recovered' if best['gain']<2.0 else 'still fast'}.")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(
        "# Force-calibration diagnostic (emergence-recovery, pre-E3)\n\n"
        f"FED baseline (ANES-calibrated) decade sep: "
        + ", ".join(f"{yr}:{ref[yr]:.2f}" for yr in ref_years)
        + f" (frac of rise by 1990 = {ref_frac90:.0%}).\n\n"
        "Endogenous loop, elite force swept DOWN toward literature-plausible values "
        "(gain 2.5 = E0 default/too-hot → 1.0 = elite≈activist base; broader tail; "
        "slower uptake). Lower `sse` = closer to the ANES gradual shape; `frac90` = "
        "fraction of the total 1980→2025 rise already complete by 1990 "
        f"(target ≈ {ref_frac90:.0%}; a fast jump shows ≫that).\n\n"
        f"`frac_late` = fraction of the rise in 2010->2025 (ANES = "
        f"{(ref[2025]-ref[2010])/full_ref:.0%}, back-loaded/accelerating; a fixed-strength "
        f"loop is front-loaded, ~0%).\n\n"
        "| gain | tail | pull | sse | frac90 | frac_late | final | 1980 | 1990 | 2000 | 2010 | 2020 | 2025 |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
        + "".join(
            f"| {r['gain']} | {r['tail']} | {r['pull']} | {r['sse']:.3f} | "
            f"{r['frac90']:.0%} | {r['frac_late']:.0%} | {r['final']:.2f} | "
            + " | ".join(f"{r['seps'][yr]:.2f}" for yr in ref_years) + " |\n"
            for r in rows)
        + f"\n**Best shape-match:** gain={best['gain']}, tail={best['tail']}, "
        f"pull={best['pull']} (sse={best['sse']:.3f}, frac90={best['frac90']:.0%}, "
        f"final={best['final']:.2f}).\n\n```json\n" + json.dumps(rows, indent=1) + "\n```\n",
        encoding="utf-8",
    )
    print(f"\nwrote {OUT_MD}")


if __name__ == "__main__":
    main()
