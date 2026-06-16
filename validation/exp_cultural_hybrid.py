"""FALSIFY-FIRST sandbox (NO engine change, NOT committed as engine): the cultural
HYBRID for blindspot #10. Tests whether an EVENT-TIMED cultural accelerant + an
early dampener, routed through the existing cultural cue channel (party_cue ->
PartyPull), reproduces the back-loaded real cultural sorting curve without harming
econ / sorting / affect / the cultural common-mode.

DRIVER + INDEPENDENCE JUSTIFICATION. A signed cultural-cue rate schedule whose
TIMING is set by DOCUMENTED EVENTS, never by the ANES cultural-gap series:
  - early dampener (1986-2008): culture was a weak party cleavage pre-"great sort"
    (Mason 2018 dates the sort post-1990s; ANES+GSS both show cult gap ~0.12 in 1986).
    A small negative differential cue pulls the model's over-separated early parties
    together. One scalar (d_early).
  - accelerant (2012-2020): the "Great Awokening" / "Racing Apart" cultural sorting
    surge — onset ~2012 (BLM 2013), Ferguson 2014 catalyst, peak 2020 (Floyd), slight
    decline 2024. Smooth event-anchored ramp; one scalar (a_peak). Timing is the
    documented event sequence, NOT read off ANES.
Only 2 amplitudes are fit; the inflection YEARS are exogenous events. This is the
(L mechanism + E exogenous timing + N amplitude) hybrid. The accelerant is applied
to party_cue[y] (the cultural elite cue) and carried to the mass by the EXISTING
PartyPull — it is NOT a direct position relabel and NOT timed by the answer.

ECON (x) is never touched. The cultural common-mode rule (on) re-centers y each tick,
so the differential nudge cannot move the cultural LEVEL.

============================ VERDICT: FALSIFIED on H1 ============================
Seeds 0-2, d_early=0.085 / a_peak=0.05 (figure: figures/cultural_hybrid_falsified.png).
- H1 (raise 2012-2020 cult gap toward real, CONCENTRATED): **FAIL.** 2020 cult gap
  stays 0.67-0.73 (real 0.783; div -0.05..-0.11), and the lift is within seed noise
  (seed 1: none). The model STILL PEAKS AT 2016, not 2020 — the event-locked surge
  TIMING is not reproduced. Root cause: the activist->elite->mass loop amplifies along
  a FIXED 2D direction (fixed econ:cult ratio), so the cultural gap's timing is BOUND
  to econ's; a differential cultural cue, routed through the (PartyPull/FJ-damped)
  existing channel, can shift the cultural LEVEL modestly but cannot DECOUPLE/RE-TIME
  it. Genuinely fixing the mis-pacing needs a STRUCTURAL change (axis-specific
  mobilization/direction in the loop, or a second cultural loop) — beyond a hand-drawn
  cue and beyond the existing primitives.
- H2 (remove 1986-90 over-separation): **PARTIAL.** The early dampener reliably cuts
  the early over-sep ~40% across seeds (+0.099->+0.057 / +0.082->+0.039 / +0.228->
  +0.193), but doesn't eliminate it AND over-corrects the mid-period (1996-2008 turns
  slightly under). A side-effect, not a clean fix.
- H3 (no harm): **PASS.** Econ untouched (|d| <= 0.010), no party_sep overshoot
  (sep@2020 ~1.0-1.05 < real 1.147), cultural common-mode center preserved
  (-0.030..-0.045), affect within range.
Conclusion: the hybrid as scoped (event-timed cue through the existing loop) is
HARMLESS but INSUFFICIENT — it cannot reproduce the back-loaded cultural surge,
because the single-direction loop binds cultural timing to econ timing. NOT
recommended to build as a cue schedule; document blindspot #10 as a known miss, or
pursue the deeper structural decoupling separately.
=================================================================================
"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.anes_preset import ANES_FULL_KWARGS
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to

YEARS = [1986, 1988, 1990, 1992, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024]
REAL_CULT = {1986: 0.122, 1988: 0.204, 1990: 0.173, 1992: 0.295, 1996: 0.307,
             2000: 0.284, 2004: 0.442, 2008: 0.401, 2012: 0.519, 2016: 0.629,
             2020: 0.783, 2024: 0.734}
REAL_ECON = {1986: 0.321, 1988: 0.376, 1990: 0.326, 1992: 0.408, 1996: 0.445,
             2000: 0.388, 2004: 0.524, 2008: 0.584, 2012: 0.621, 2016: 0.702,
             2020: 0.838, 2024: 0.760}
REAL_SEP = {y: float(np.hypot(REAL_ECON[y], REAL_CULT[y])) for y in YEARS}
TPY = 3.0


def cue_target(year, d_early, a_peak):
    """CUMULATIVE per-party cultural cue offset (signed, + = party pushed apart on
    y). Event-anchored SHAPE; d_early (early suppression magnitude) and a_peak
    (2012-2020 release magnitude) are the only fitted scalars. The model mis-TIMES
    culture (peaks ~2016, misses the 2020 surge), so the shape SUPPRESSES pre-2012
    (parties weren't culturally sorted yet — Mason) then RELEASES 2012->2020 (the
    Awokening: BLM 2013 / Ferguson 2014 / Floyd 2020)."""
    rel = 2015.0   # release onset — Ferguson 2014/2015 (the documented catalyst)
    if year <= rel:
        # ramp 0 (1980) -> -d_early by 1995, hold the suppression through the catalyst
        return -d_early * float(np.clip((year - 1980.0) / 15.0, 0.0, 1.0))
    # rel -> 2020 release: from -d_early up to +a_peak; slight 2024 pullback
    f = float(np.clip((year - rel) / (2020.0 - rel), 0.0, 1.0))
    val = -d_early + (a_peak + d_early) * f
    if year > 2020.0:
        val -= (a_peak + d_early) * 0.10 * float(np.clip((year - 2020.0) / 4.0, 0.0, 1.0))
    return val


def cult_cue_increment(year, d_early, a_peak):
    """Per-tick increment = derivative of the cumulative target (so accumulated cue
    = cue_target, not a runaway sum)."""
    dt = 1.0 / TPY
    return cue_target(year, d_early, a_peak) - cue_target(year - dt, d_early, a_peak)


def build(seed):
    kw = dict(ANES_FULL_KWARGS)
    eng = build_engine(seed=seed, **kw)
    sched = build_schedule(
        factional_seeding=kw.get("factional_seeding", False),
        faction_anchor_events=kw.get("faction_anchor_events", True),
        evidence_regrade=kw.get("evidence_regrade", False),
        exogenous_shocks=kw.get("exogenous_shocks", False))
    return eng, sched


def apply_cult_cue(eng, year, d_early, a_peak):
    """Intensify/relax the cultural elite cue on party_cue[y], event-timed. The
    existing PartyPull carries it to the mass next tick. Differential (D down /
    R up), so the cultural LEVEL is untouched; econ (x) is never touched."""
    r = cult_cue_increment(year, d_early, a_peak)
    if abs(r) < 1e-12:
        return
    for a in eng.agents:
        p = a.state.attrs.get("party")
        if p not in (0, 1):
            continue
        cue = a.state.attrs.get("party_cue")
        if cue is None:
            continue
        sign = 1.0 if p == 1 else -1.0
        cue[1] = float(np.clip(cue[1] + r * sign, -1.0, 1.0))


def metrics(eng):
    party = np.array([a.state.attrs.get("party") for a in eng.agents])
    pos = np.array([a.state.ideology for a in eng.agents])
    D, R = pos[party == 0], pos[party == 1]
    m = (party == 0) | (party == 1)
    aff = []
    for a in eng.agents:
        p = a.state.attrs.get("party")
        if p in (0, 1):
            d = a.state.attrs.get("affect") or {}
            v = d.get(1 - p)
            if v is not None:
                aff.append(float(v))
    return dict(
        econ_gap=float(R[:, 0].mean() - D[:, 0].mean()),
        cult_gap=float(R[:, 1].mean() - D[:, 1].mean()),
        sep=float(np.hypot(R[:, 0].mean() - D[:, 0].mean(), R[:, 1].mean() - D[:, 1].mean())),
        corr=float(np.corrcoef(pos[m, 0], pos[m, 1])[0, 1]),
        cult_center=float(pos[m, 1].mean()),
        affect=float(np.mean(aff)) if aff else np.nan)


def run(seed, d_early=0.0, a_peak=0.0):
    eng, sched = build(seed)
    rec = {}
    for t in range(1, 136):
        run_to(eng, sched, t)
        year = 1980 + t / TPY
        if d_early or a_peak:
            apply_cult_cue(eng, year, d_early, a_peak)
        yr = int(round(year))
        if yr in YEARS and yr not in rec:
            rec[yr] = metrics(eng)
    return rec


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--d_early", type=float, default=0.012)
    ap.add_argument("--a_peak", type=float, default=0.022)
    ap.add_argument("--seeds", type=int, nargs="+", default=[0])
    args = ap.parse_args()

    for seed in args.seeds:
        base = run(seed)
        hyb = run(seed, args.d_early, args.a_peak)
        print(f"\n###### seed {seed}  (d_early={args.d_early}, a_peak={args.a_peak}) ######")
        print(f"{'yr':>5} | {'real_cult':>9} {'base':>6} {'hybrid':>6} {'div':>6} | "
              f"{'real_econ':>9} {'h_econ':>6} | {'h_sep':>6} {'real_sep':>8} | {'h_aff':>6}")
        for y in YEARS:
            print(f"{y:>5} | {REAL_CULT[y]:>9.3f} {base[y]['cult_gap']:>6.3f} "
                  f"{hyb[y]['cult_gap']:>6.3f} {hyb[y]['cult_gap']-REAL_CULT[y]:>+6.3f} | "
                  f"{REAL_ECON[y]:>9.3f} {hyb[y]['econ_gap']:>6.3f} | "
                  f"{hyb[y]['sep']:>6.3f} {REAL_SEP[y]:>8.3f} | {hyb[y]['affect']:>6.2f}")
        # verdicts
        early = [y for y in YEARS if y <= 1990]
        e_base = np.mean([base[y]['cult_gap'] - REAL_CULT[y] for y in early])
        e_hyb = np.mean([hyb[y]['cult_gap'] - REAL_CULT[y] for y in early])
        c20 = hyb[2020]['cult_gap']
        econ_div = np.mean([abs(hyb[y]['econ_gap'] - base[y]['econ_gap']) for y in YEARS])
        print(f"  H1 (2020 cult {c20:.3f} → real 0.783; 2016 {hyb[2016]['cult_gap']:.3f}→0.629): "
              f"{'toward real' if c20 > base[2020]['cult_gap'] + 0.03 else 'NO LIFT'}")
        print(f"  H2 (early86-90 over-sep base {e_base:+.3f} → hybrid {e_hyb:+.3f}): "
              f"{'REDUCED' if abs(e_hyb) < abs(e_base) - 0.02 else 'not reduced'}")
        print(f"  H3 econ |Δ| vs base {econ_div:.4f} (want ~0); sep@2020 {hyb[2020]['sep']:.3f} "
              f"(real 1.147, ceiling); cult_center@2024 {hyb[2024]['cult_center']:+.3f} "
              f"(common-mode); affect@2024 {hyb[2024]['affect']:.2f}")
