"""Probe (one-off): does a SINGLE post-2008 racialization forcing — routed
through the dormant identity->ideology spillover channel — add the post-2008
sorting acceleration, and does it carry the Tesler "spillover" signature?

Design: docs/internal/racialization_spillover_spec.md §5.

Conditions (full emergent arc, ANES_FULL_KWARGS):
  control   — canonical.
  idpp_y    — turn IdentityToIdeologyPull strength_y = 0.20 ON at tick 84 (2008).
  idpp_xy   — turn strength_x = strength_y = 0.15 ON at tick 84.

The pull is off (0.0) before tick 84, so pre-84 MUST equal control (an
internal-validity check the forcing is time-gated to post-2008).

Measured per tick:
  party_sep        — the sorting outcome.
  spillover_corr   — within-population corr( mean(identities), ideology . axis ),
                     axis = unit(cent_R - cent_D). Rising = identity becomes more
                     predictive of issue position = the Tesler spillover signature.

Reads we report:
  * acceleration ratio of CONTROL (post-2008 slope / pre-2008 slope) vs ANES ~2.5x
    -> is there a numeric gap, or is the idea purely legibility?
  * sign + size of the IDPP effect on post-2008 party_sep, and where it lands.
  * whether IDPP raises spillover_corr (distinguishes spillover from a gain bump).

NOTE the spec's sign risk (§4.3): on the emergent path identity centroids are
static at +-0.20 while the elite loop drives mass out toward +-0.65, so the pull
toward the static centroid may go INWARD (reduce sorting). This probe settles it.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

import numpy as np

from abm.pillars.historical_arc import build_engine
from abm.pillars.schedule import run_to
from scripts.anes_preset import ANES_FULL_KWARGS
from scripts.phase8f_lib import party_sep_metric
from scripts.audit.audit_lib import _make_schedule, END_TICK

RELEASE = 84                       # tick 84 = 2008 (social-media ramp start)
SEEDS = (0, 1, 2, 3, 4)
CONDS = ["control", "idpp_y", "idpp_xy"]
SNAP_TICKS = [18, 60, RELEASE, 108, 126, END_TICK]   # 1986/2000/2008/2016/2020/2025

# ANES scaled_separation (data/phase9_empirical/derived/polarization_series.csv).
ANES_SEP = {1986: 0.957, 2008: 1.898, 2020: 3.199}
ANES_RATIO = (
    (ANES_SEP[2020] - ANES_SEP[2008]) / (2020 - 2008)
) / (
    (ANES_SEP[2008] - ANES_SEP[1986]) / (2008 - 1986)
)


def _find(eng, name):
    for r in list(eng.rules.rules) + list(getattr(eng, "env_rules", [])):
        if type(r).__name__ == name:
            return r
    return None


def _spillover_corr(agents) -> float:
    """corr( mean(identities), ideology . partisan_axis ) over party 0/1 agents."""
    pos, ident, party = [], [], []
    for a in agents:
        p = a.state.attrs.get("party")
        if p not in (0, 1):
            continue
        ids = a.state.attrs.get("identities")
        if ids is None or len(ids) == 0:
            continue
        pos.append(np.asarray(a.state.ideology, dtype=float))
        ident.append(float(np.mean(ids)))
        party.append(p)
    if len(pos) < 3:
        return float("nan")
    pos = np.asarray(pos)
    party = np.asarray(party)
    cent_d = pos[party == 0].mean(0)
    cent_r = pos[party == 1].mean(0)
    axis = cent_r - cent_d
    n = float(np.linalg.norm(axis))
    if n < 1e-9:
        return float("nan")
    axis = axis / n
    proj = pos @ axis
    ident = np.asarray(ident)
    if np.std(proj) < 1e-9 or np.std(ident) < 1e-9:
        return float("nan")
    return float(np.corrcoef(ident, proj)[0, 1])


def _worker(arg):
    cond, seed = arg
    eng = build_engine(seed=seed, **ANES_FULL_KWARGS)
    sched = _make_schedule("full")
    sep, corr = {}, {}
    for t in range(1, END_TICK + 1):
        run_to(eng, sched, t)
        if t == RELEASE and cond != "control":
            r = _find(eng, "IdentityToIdeologyPull")
            if r is not None:
                if cond == "idpp_y":
                    r.strength_y = 0.20
                elif cond == "idpp_xy":
                    r.strength_x = 0.15
                    r.strength_y = 0.15
        if t in SNAP_TICKS:
            sep[t] = float(party_sep_metric(eng))
            corr[t] = _spillover_corr(eng.agents)
    return {"cond": cond, "seed": seed, "sep": sep, "corr": corr}


def main():
    from abm.calibration_parallel import run_seeds_parallel
    work = [(c, s) for c in CONDS for s in SEEDS]
    res = run_seeds_parallel(_worker, work)
    by = {(r["cond"], r["seed"]): r for r in res}

    def mean_sep(cond, t):
        return float(np.mean([by[(cond, s)]["sep"][t] for s in SEEDS]))

    def mean_corr(cond, t):
        vals = [by[(cond, s)]["corr"][t] for s in SEEDS]
        vals = [v for v in vals if not np.isnan(v)]
        return float(np.mean(vals)) if vals else float("nan")

    print(f"Racialization-spillover probe — IDPP ON at tick {RELEASE} (2008), "
          f"{len(SEEDS)} seeds")
    print("=" * 78)

    # --- 1. Control acceleration ratio vs ANES -------------------------------
    pre = (mean_sep("control", RELEASE) - mean_sep("control", 18)) / (RELEASE - 18)
    post = (mean_sep("control", 126) - mean_sep("control", RELEASE)) / (126 - RELEASE)
    ratio = post / pre if abs(pre) > 1e-9 else float("nan")
    print("\n[1] CONTROL post-2008 acceleration (does the model already bend at 2008?)")
    print(f"    pre-2008 slope (t18->t84)   = {pre:+.5f} /tick")
    print(f"    post-2008 slope (t84->t126) = {post:+.5f} /tick")
    print(f"    model acceleration ratio    = {ratio:.2f}x   "
          f"(ANES scaled_sep ratio = {ANES_RATIO:.2f}x)")
    print("    -> ratio << ANES => numeric gap a forcing could fill; "
          "ratio ~ ANES => value is legibility, not gap-filling.")

    # --- 2. party_sep: Δ vs control at each snapshot -------------------------
    print("\n[2] party_sep — Δ vs control (sign check: + = added sorting, "
          "- = pulled inward)")
    hdr = "    " + f"{'cond':<10}" + "".join(f"{('t'+str(t)):>10}" for t in SNAP_TICKS)
    print(hdr)
    for cond in CONDS:
        row = f"    {cond:<10}"
        for t in SNAP_TICKS:
            if cond == "control":
                row += f"{mean_sep(cond, t):>10.4f}"
            else:
                row += f"{mean_sep(cond, t) - mean_sep('control', t):>+10.4f}"
        print(row)
    print(f"    (pre-{RELEASE} Δ must be ~0 — forcing is time-gated to post-2008)")

    # --- 3. spillover signature ---------------------------------------------
    print("\n[3] spillover_corr — corr(identity, issue position). "
          "Rising under IDPP = Tesler signature.")
    print(hdr)
    for cond in CONDS:
        row = f"    {cond:<10}"
        for t in SNAP_TICKS:
            if cond == "control":
                row += f"{mean_corr(cond, t):>10.3f}"
            else:
                row += f"{mean_corr(cond, t) - mean_corr('control', t):>+10.3f}"
        print(row)

    print("\n" + "=" * 78)
    print("READ: legs if idpp ADDS post-2008 party_sep (right sign/window) AND "
          "raises spillover_corr.\n      Redirect (spec §4.3) if Δparty_sep is "
          "negative (inward pull) or ~0 (too weak).")


if __name__ == "__main__":
    main()
