"""build_sandbox_data.py — pre-render the sandbox grid (whole alternate histories).

The interactive sandbox lets the user dial 5 knobs (5 positions each) and watch
the resulting alternate 1980→2025 play out on the compass. Rather than run the
engine in the browser, we PRE-RENDER all 5^5 = 3,125 combinations here and serve
each lazily as a small static file (same `cf/` convention as the intervention
branches; see build_branch_data.py).

Each run applies the knob-vector as `build_engine` kwargs FROM THE START (whole
alternate history — the center cell of the grid is exactly the shipped arc), runs
seed 0 to 2025, and stores a DECIMATED per-frame cloud (for the compass) plus the
four macro series (for the live metrics strip: separation, out-party warmth,
modularity, identity alignment).

The five dials (grid v5, emergence-recovery v1 polish;
docs/internal/sandbox_knob_redesign.md). Each dial OWNS ONE distinct readout, is
TWO-SIDED around the arc (center detent idx 2 of all five → "all centered" == the
shipped baseline), and has its off-center detents fit to LINEARIZE the owned
readout (scripts/audit/sandbox_dial_sweep.py). The polarization metrics are
READOUTS, not knobs:

    leaders     elite_gain (+ceiling), endogenous loop -> SEPARATION
    identities  tier_c_identity_pull_x/y (×mult)        -> MEGA-IDENTITY (align)
    dailylife   sandbox_animus_mult ↔ sandbox_contact   -> ANIMUS (affect), 2-sided
    within      sandbox_diversity σ + inverse bc_strength -> WITHIN-PARTY SPREAD
    ties        sandbox_rewire_mult (TieRewiring rate)  -> ECHO CHAMBERS (modularity)

ILLUSTRATIVE ONLY — these crank the model past calibration. Not a finding, and
NOT a claim that any dial raises the emergent fraction (it doesn't — it just cranks
knobs; the honest emergent/forcing split lives in the Methods honesty panel).

Output: web_demo/cf/sandbox/<key>.json  (key = 5 digits 0-4, one per knob in
KNOB_ORDER) + web_demo/cf/sandbox/index.json manifest.

Usage:
    .venv/Scripts/python.exe scripts/build_sandbox_data.py            # full 3,125
    .venv/Scripts/python.exe scripts/build_sandbox_data.py --limit 8  # pilot
    .venv/Scripts/python.exe scripts/build_sandbox_data.py --workers 12
"""
from __future__ import annotations

import argparse
import itertools
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── the locked grid v2 (audit 2026-06; docs/intervention_knob_audit.md) ──
# Each knob = 5 detents; each detent is a dict of build_engine overrides. The
# CENTER detent of every knob (CENTER_IDX) equals the shipped arc, so the center
# cell is bit-identical to the calibrated 1980→2025 baseline.
#
# All five are CAUSES (things you set). The polarization metrics — separation,
# out-party animus, within-party spread, mega-identity alignment — are the
# READOUTS you watch (no knob is also a readout). Each knob is sign-stable
# across every position of the other four (12/12 in the audit robustness screen).
KNOB_ORDER = ["leaders", "identities", "dailylife", "within", "ties"]
# ── grid v5 (emergence-recovery v1 polish): the 5-dial redesign ──────────────
# docs/internal/sandbox_knob_redesign.md. The v4 grid had four structural faults:
# two dials fought over `sep`, two over `spread` (one perversely — "Open-mindedness"
# tightened within-party spread), the network/echo-chamber readout had NO dial, and
# the centers sat at different detents per knob. v5 fixes all four:
#   (1) ONE dial OWNS ONE readout — no collisions.
#   (2) every dial is TWO-SIDED around the arc, which sits at the CENTER detent
#       (idx 2) of all five — so "all centered" == the calibrated 1980→2025 arc.
#   (3) the off-center detents LINEARIZE THE OWNED READOUT (not the raw param) —
#       fit by scripts/audit/sandbox_dial_sweep.py so the whole slider feels alive.
#   (4) every detent is a real build_engine config (illustrative-past-calibration,
#       same wall as before) — NO faked effects, NO claim it raises the emergent
#       fraction; the honest emergent/forcing split lives in the Methods panel.
# Owned readouts (one each): separation←leaders · mega-identity←identities ·
# animus←dailylife · within-party spread←within · echo-chambers(modularity)←ties.
GRID = {
    # 1. LEADERS moderate↔extreme — owns SEPARATION. The endogenous loop's
    #    elite_gain (leapfrog over the activist tail, Bawn et al. 2012) co-scaled
    #    with elite_ceiling (the saturating bound). Pushing gain<1/low-ceiling at
    #    the low end and gain~4.5/ceiling~1.3 at the high end defeats the tanh
    #    squash, so the camps fly apart EVENLY across the whole slider (sweep-
    #    verified 2025 sep ≈ 0.74 → 0.92 → 1.10 → 1.26 → 1.41, steps ~0.18/0.18/
    #    0.16/0.14). Center = the adopted E4 ABC point (== the shipped arc).
    "leaders":    [{"elite_gain": g, "elite_ceiling": c} for g, c in
                   ((0.55, 0.50), (1.05, 0.66), (1.7689, 0.8237), (3.0, 1.05), (4.5, 1.30))],
    # 2. IDENTITIES cross-cutting↔stacked — owns MEGA-IDENTITY (alignment). Mason
    #    mega-identity via IdentityToIdeologyPull strength (×0.0–3.0 of the shipped
    #    0.02/0.04). Re-pointed to OWN alignment (the diagonal collapse) so it no
    #    longer collides with leaders on sep. Center ×1.0 == the arc.
    "identities": [
        {"tier_c_identity_pull_x": 0.02 * f, "tier_c_identity_pull_y": 0.04 * f}
        for f in (0.0, 0.5, 1.0, 2.0, 3.0)
    ],
    # 3. DAILY LIFE segregated↔mixed — owns ANIMUS (affect). TWO-SIDED: left of
    #    center raises parasocial animus (sandbox_animus_mult — colder/segregated),
    #    right raises cooperative contact (sandbox_contact — warmer/mixed). Center =
    #    the arc (animus_mult 0.655, contact 0.0). Sweep: aff ≈ -0.86 → -0.79 →
    #    -0.655 → -0.59 → -0.51 (sep/spread/align stay flat — clean ownership).
    "dailylife":  [
        {"sandbox_animus_mult": 1.6,   "sandbox_contact": 0.0},
        {"sandbox_animus_mult": 1.1,   "sandbox_contact": 0.0},
        {"sandbox_animus_mult": 0.655, "sandbox_contact": 0.0},   # arc
        {"sandbox_animus_mult": 0.655, "sandbox_contact": 0.5},
        {"sandbox_animus_mult": 0.655, "sandbox_contact": 1.0},
    ],
    # 4. WITHIN each party lockstep↔free-thinking — owns WITHIN-PARTY SPREAD. Merges
    #    the two broken v4 dials (kills the σ dead-zone AND retires the perverse
    #    "Open-mindedness" label): attack spread from BOTH ends — lockstep = low
    #    GaussianNoise σ + high BC conformity (converge to the party mean); free =
    #    high σ + zero BC conformity. ε stays 0.40 (within-party, never the cross-
    #    party-merge regime). Sweep: spread ≈ 0.23 → 0.26 → 0.285 → 0.30 → 0.36.
    "within":     [
        {"sandbox_diversity": 0.004,  "tier_c_bc_strength": 0.22, "tier_c_bc_epsilon": 0.40},
        {"sandbox_diversity": 0.022,  "tier_c_bc_strength": 0.09, "tier_c_bc_epsilon": 0.40},
        {"sandbox_diversity": 0.0478, "tier_c_bc_strength": 0.03, "tier_c_bc_epsilon": 0.40},  # arc
        {"sandbox_diversity": 0.105,  "tier_c_bc_strength": 0.01, "tier_c_bc_epsilon": 0.40},
        {"sandbox_diversity": 0.205,  "tier_c_bc_strength": 0.0,  "tier_c_bc_epsilon": 0.40},
    ],
    # 5. SOCIAL TIES open↔echo-chambered — owns ECHO CHAMBERS (modularity). The new
    #    dial for the orphaned network readout: sandbox_rewire_mult scales the
    #    homophilous TieRewiring rate (0.03 × mult). Left = ties stay mixed (low
    #    modularity), right = rewiring builds clusters. Sweep: modularity ≈ 0.05 →
    #    0.11 → 0.19 → 0.26 → 0.32 (even, full span). Requires `modularity` exported
    #    in _macro (added below). The most visually fun — the cloud literally clusters.
    "ties":       [{"sandbox_rewire_mult": v} for v in (0.0, 0.5, 1.0, 2.25, 4.0)],
}
# Center detent of EVERY knob = idx 2 = the shipped arc, so the center cell
# (all-centered) is bit-identical to the calibrated 1980→2025 baseline.
CENTER_IDX = {"leaders": 2, "identities": 2, "dailylife": 2, "within": 2, "ties": 2}
KNOB_LABELS = {
    "leaders": "Leaders", "identities": "Identities",
    "dailylife": "Daily life", "within": "Within each party",
    "ties": "Social ties",
}

END = 135
TICK_STEP = 2          # store every other tick (~1 frame / 8 months)
N_AGENTS_KEEP = 160    # downsample the cloud for the KDE field (density est. is robust)

# stable, representative agent subset (stride across the full population)
_KEEP_IDX = np.linspace(0, 249, N_AGENTS_KEEP).round().astype(int)
_KEEP_IDX = sorted(set(int(i) for i in _KEEP_IDX))

_STORE_TICKS = list(range(0, END + 1, TICK_STEP))
if _STORE_TICKS[-1] != END:
    _STORE_TICKS.append(END)
_STORE_SET = set(_STORE_TICKS)


def _overrides(idx_tuple):
    ov = {}
    for k, i in zip(KNOB_ORDER, idx_tuple):
        ov.update(GRID[k][i])
    return ov


def _capture(eng):
    pos = [
        [round(float(eng.agents[i].state.ideology[0]), 2),
         round(float(eng.agents[i].state.ideology[1]), 2)]
        for i in _KEEP_IDX
    ]
    party = [int(eng.agents[i].state.attrs.get("party", 2)) for i in _KEEP_IDX]
    return pos, party


def _macro(eng, measure_all):
    m = measure_all(eng)
    aligns = [
        float(a.state.attrs.get("identity_alignment", 0.0))
        for a in eng.agents if a.state.attrs.get("party") in (0, 1)
    ]
    # within-party spread (the diversity-knob readout): mean per-axis SD of
    # each party's cloud, averaged over the two parties.
    spreads = []
    for p in (0, 1):
        P = np.array([
            a.state.ideology for a in eng.agents
            if a.state.attrs.get("party") == p
        ])
        if len(P) > 1:
            spreads.append(float(P.std(axis=0).mean()))
    return {
        "sep": round(float(m["party_sep"]), 3),
        "aff": round(float(m["affect"]), 3),
        "spread": round(float(np.mean(spreads)) if spreads else 0.0, 3),
        "align": round(float(np.mean(aligns)) if aligns else 0.0, 3),
        # grid v5: the echo-chamber readout the new `ties` dial owns. measure_all
        # already computes party_modularity; it just was never exported here.
        "mod": round(float(m["modularity"]), 3),
    }


def run_one(args):
    """Worker: build + run one combo, write its file, return (key, bytes)."""
    idx_tuple, out_dir = args
    import sys
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))
    from scripts.anes_preset import ANES_FULL_KWARGS
    from scripts.phase8f_lib import measure_all
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to

    kwargs = dict(ANES_FULL_KWARGS)
    kwargs.update(_overrides(idx_tuple))
    eng = build_engine(seed=0, **kwargs)
    sched = build_schedule(
        factional_seeding=kwargs.get("factional_seeding", False),
        faction_anchor_events=kwargs.get("faction_anchor_events", True),
        evidence_regrade=kwargs.get("evidence_regrade", False),
        exogenous_shocks=kwargs.get("exogenous_shocks", False),
    )

    frames_pos, frames_party, macro = [], [], []
    p, pa = _capture(eng); frames_pos.append(p); frames_party.append(pa)
    macro.append(_macro(eng, measure_all))
    for t in range(1, END + 1):
        run_to(eng, sched, t)
        if t in _STORE_SET:
            p, pa = _capture(eng); frames_pos.append(p); frames_party.append(pa)
            macro.append(_macro(eng, measure_all))

    key = "".join(str(i) for i in idx_tuple)
    payload = {
        "key": key,
        "knobs": _overrides(idx_tuple),
        "ticks": _STORE_TICKS,
        "pos": frames_pos,
        "party": frames_party,
        "macro": macro,
    }
    out_path = Path(out_dir) / f"sandbox_{key}.json"
    text = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    out_path.write_text(text, encoding="utf-8")
    return key, len(text.encode("utf-8"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(_PROJECT_ROOT / "web_demo" / "cf" / "sandbox"))
    ap.add_argument("--limit", type=int, default=0, help="only first N combos (pilot)")
    ap.add_argument("--workers", type=int, default=0, help="0 = cpu-2")
    args = ap.parse_args()

    import os
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    workers = args.workers or max(1, (os.cpu_count() or 4) - 2)

    combos = list(itertools.product(*[range(len(GRID[k])) for k in KNOB_ORDER]))
    if args.limit:
        combos = combos[:args.limit]

    print(f"grid: {len(combos)} combos · {len(_STORE_TICKS)} frames · "
          f"{len(_KEEP_IDX)} agents · {workers} workers", flush=True)
    t0 = time.time()
    total_bytes = 0
    done = 0
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for key, nbytes in ex.map(run_one, [(c, str(out_dir)) for c in combos]):
            total_bytes += nbytes
            done += 1
            if done % 50 == 0 or done == len(combos):
                rate = done / (time.time() - t0)
                eta = (len(combos) - done) / rate if rate else 0
                print(f"  {done}/{len(combos)}  ({rate:.1f}/s, eta {eta:.0f}s, "
                      f"{total_bytes/1024/1024:.0f} MB)", flush=True)

    manifest = {
        "contract_version": 1, "kind": "sandbox",
        "knob_order": KNOB_ORDER,
        "knobs": {k: {"label": KNOB_LABELS[k], "detents": GRID[k]} for k in KNOB_ORDER},
        "center_key": "".join(str(CENTER_IDX[k]) for k in KNOB_ORDER),
        "ticks": _STORE_TICKS, "n_agents": len(_KEEP_IDX),
        "n_files": len(combos),
    }
    (out_dir / "index.json").write_text(
        json.dumps(manifest, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")

    avg = total_bytes / max(1, len(combos))
    print(f"\ndone: {len(combos)} files, {total_bytes/1024/1024:.0f} MB "
          f"(avg {avg/1024:.0f} KB), {time.time()-t0:.0f}s", flush=True)
    print(f"manifest: {out_dir / 'index.json'}", flush=True)


if __name__ == "__main__":
    main()
