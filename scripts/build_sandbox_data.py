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

The five dials (audit 2026-06; docs/intervention_knob_audit.md) — all are
CAUSES (each sign-stable at any position of the other four, 12/12 in the
robustness screen). The polarization metrics are READOUTS, not knobs:

    identity   tier_c_identity_pull_x/y (×mult)   -> Mason mega-identity
    elite      elite_lead_factor                  -> elite divergence
    openness   tier_c_bc_epsilon (+ _bc_strength) -> open-mindedness (ε; depolarizes)
    contact    sandbox_contact                    -> cooperative mixing (warms)
    diversity  sandbox_diversity                  -> within-party free-thinking

    (MHV S5 T5.1 re-map: identity + elite v2 knobs went inert on the data-fed
    emergent substrate; re-pointed to the live levers above. openness + diversity
    centers re-pinned to the S4 arc so the center cell stays the shipped baseline.)

ILLUSTRATIVE ONLY — these crank the model past calibration. Not a finding.

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
KNOB_ORDER = ["identity", "elite", "openness", "contact", "diversity"]
# ── grid v3 (MHV S5 T5.1): re-mapped onto the S4 data-fed emergent substrate ──
# Two v2 dials went inert under MHV and were re-mapped to live levers (verified
# sign-stable on the fitted config); openness + diversity centers were re-pinned
# to the S4 arc so the center cell stays bit-identical to the shipped baseline:
#   identity : sandbox_identity_mult (inert since the T2.4 measured-alignment
#              rebuild) → IdentityToIdeologyPull strength (×mult of the Mason
#              0.02/0.04), the live identity→issue-alignment lever.
#   elite    : tier_d_anes_drift_multiplier (inert on the S3 data-fed path —
#              the scheduled EliteDrift it scaled is gone) → elite_lead_factor,
#              the live S4 elite-divergence carrier (1.0 = elites track the
#              voter mean; higher = elites lead the base outward).
GRID = {
    # identity → IdentityToIdeologyPull strength (Mason mega-identity: identity
    # drives issue position; ×0.0–3.0 of the shipped 0.02/0.04). More → more sep.
    "identity":  [
        {"tier_c_identity_pull_x": 0.02 * f, "tier_c_identity_pull_y": 0.04 * f}
        for f in (0.0, 0.5, 1.0, 2.0, 3.0)
    ],
    # elite divergence → elite_lead_factor (how far elite cues lead the voter
    # mean; the live S4 carrier — DW-NOMINATE mass-elite gap). More → more sep.
    "elite":     [{"elite_lead_factor": v} for v in (1.0, 1.4, 1.798, 2.2, 2.6)],
    # open-mindedness = confidence radius ε co-scaled with influence strength —
    # the REAL Hegselmann-Krause open-mindedness (closed → open). Depolarizes.
    "openness":  [
        {"tier_c_bc_epsilon": 0.15, "tier_c_bc_strength": 0.0},
        {"tier_c_bc_epsilon": 0.40, "tier_c_bc_strength": 0.03},    # arc (S2 BC wake)
        {"tier_c_bc_epsilon": 0.70, "tier_c_bc_strength": 0.07},
        {"tier_c_bc_epsilon": 1.20, "tier_c_bc_strength": 0.13},
        {"tier_c_bc_epsilon": 3.00, "tier_c_bc_strength": 0.20},
    ],
    # contact / mixing → cooperative-share floor (Pettigrew-Tropp). Warms affect.
    "contact":   [{"sandbox_contact": v} for v in (0.0, 0.25, 0.5, 0.75, 1.0)],
    # within-party diversity → GaussianNoise σ (lockstep → free-thinking).
    # Center (idx 1) re-pinned to the S4 fitted within-party σ (0.0478).
    "diversity": [{"sandbox_diversity": v} for v in (0.02, 0.0478, 0.08, 0.15, 0.25)],
}
# center detent per knob = the shipped arc value (so the center cell == the arc):
# identity ×1.0 (0.02/0.04), elite_lead 1.798, ε0.40/0.03, contact 0.0, σ0.0478.
CENTER_IDX = {"identity": 2, "elite": 2, "openness": 1, "contact": 0, "diversity": 1}
KNOB_LABELS = {
    "identity": "Mega-identity", "elite": "Elite extremism",
    "openness": "Open-mindedness", "contact": "Contact & mixing",
    "diversity": "Within-party diversity",
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
