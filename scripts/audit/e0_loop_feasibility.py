"""
E0 — loop-feasibility gate for the emergence-recovery workstream
(docs/internal/emergence_spec.md, Tier 1).

THROWAWAY standalone harness — NOT the shipped engine. A minimal numpy
implementation of the activist-tail -> elite -> cue -> mass feedback loop, to
answer one gate question before any engine change:

  Is there ANY regime (loop gain x tail-definition x counter-force) where the
  loop produces STABLE, PARTIAL, REALISTIC emergent bipolarization?
    - reaches ANES-ish separation (~1.0-1.1)         [not fizzle]
    - does NOT run to the corners                     [not runaway]
    - keeps within-party variance (~0.27-0.41)        [not collapse]
    - is stable (plateaus, not oscillating/exploding)
    - mass lags elite (mass-elite gap > 0)            [the real asymmetry]

Nothing positional is fed. The only "input" is a tiny initial party asymmetry
(the symmetry-breaking seed; in the real model Tier-2 shocks supply this). If a
realistic stable regime exists, map it and proceed to E1 on the real engine. If
none does, that ceiling is the honest finding.

Run: PYTHONPATH=. .venv/Scripts/python.exe scripts/audit/e0_loop_feasibility.py
"""
from __future__ import annotations

import json
from itertools import product
from pathlib import Path

import numpy as np

OUT_MD = Path(__file__).resolve().parents[2] / "docs" / "internal" / "audit" / "e0_loop_feasibility.md"

# ANES reference windows (the realistic target) — from the shipped bands.
SEP_LO, SEP_HI = 0.90, 1.30          # ~ANES 2020-25 party_sep
WPSD_LO, WPSD_HI = 0.22, 0.42        # within-party SD band
CORNER_MAX = 0.08                    # boundary occupancy ceiling


def _softsat(x: np.ndarray, s: float) -> np.ndarray:
    """Radial soft saturation: extremity ceiling at ~s, smooth (no corner pile-up).
    The saturating nonlinearity that gives the loop a stable *interior* fixed
    point instead of fizzle-or-runaway."""
    return s * np.tanh(x / s)


def run_loop(
    seed: int, *,
    n: int = 250, ticks: int = 135,
    tail_q: float = 0.10,            # activist tail = top fraction by extremity
    elite_gain: float = 1.5,         # elite = centroid + gain*(tail - centroid); >1 leapfrogs
    uptake: float = 0.12,            # mass partial cue-uptake (FJ-damped)
    homophily: float = 0.02,         # within-party echo (pull to own centroid)
    counter: float = 0.03,           # FJ-anchor counter-force strength
    elite_ceiling: float = 0.65,     # saturating elite extremity (the bounding nonlinearity)
    sigma_cue: float = 0.30,         # per-agent cue spread (preserves within-party SD)
    seed_asym: float = 0.05,         # initial party lean (symmetry-breaking seed)
    intensity_weight: bool = True,
    noise: float = 0.012,
) -> dict:
    rng = np.random.default_rng(seed)
    party = rng.integers(0, 2, size=n)
    pos = rng.normal(0.0, 0.30, size=(n, 2))
    # tiny symmetry-breaking seed on the economic axis
    pos[:, 0] += np.where(party == 1, seed_asym, -seed_asym)
    pos = np.clip(pos, -1.0, 1.0)
    anchor = pos.copy()
    intensity = rng.beta(2.0, 2.0, size=n)      # identity-strength proxy
    stub = rng.beta(2.0, 5.0, size=n)           # stubbornness (FJ damping)
    # per-agent fixed cue offset: agents pull toward elite + own offset, so a
    # party translates toward its elite while KEEPING its internal spread
    # (mirrors the real engine's per-agent party_cue = centroid + noise).
    cue_offset = rng.normal(0.0, sigma_cue, size=(n, 2))

    sep_traj = []
    elite = {0: np.zeros(2), 1: np.zeros(2)}
    for _t in range(ticks):
        new = pos.copy()
        # --- activist tail -> elite (each party), with saturating leapfrog ---
        for p in (0, 1):
            m = party == p
            if not m.any():
                continue
            cps = pos[m]
            cent = cps.mean(0)
            nrm = np.linalg.norm(cent)
            dirv = cent / nrm if nrm > 1e-9 else np.array([1.0 if p == 1 else -1.0, 0.0])
            proj = cps @ dirv                    # extremity along the party direction
            w = intensity[m] if intensity_weight else np.ones(m.sum())
            k = max(1, int(np.ceil(tail_q * m.sum())))
            idx = np.argsort(proj)[-k:]          # the most-extreme tail
            tail_mean = np.average(cps[idx], axis=0, weights=w[idx])
            raw = cent + elite_gain * (tail_mean - cent)
            elite[p] = _softsat(raw, elite_ceiling)   # saturating elite — the bounding nonlinearity
        # --- mass response ---
        for p in (0, 1):
            m = party == p
            if not m.any():
                continue
            cent = pos[m].mean(0)
            target = elite[p] + cue_offset[m]          # per-agent cue (spread-preserving)
            d_uptake = uptake * (target - pos[m]) * (1.0 - stub[m])[:, None]
            d_echo = homophily * (cent - pos[m])
            d_counter = counter * (anchor[m] - pos[m])     # FJ anchor (spread-preserving)
            new[m] = pos[m] + d_uptake + d_echo + d_counter
        new = new + rng.normal(0.0, noise, size=(n, 2))
        # mass bounded only by the elite ceiling (above) + the FJ anchor; hard
        # clip is a rarely-touched safety, NOT the stabilizer.
        pos = np.clip(new, -1.0, 1.0)
        sep_traj.append(float(np.linalg.norm(pos[party == 0].mean(0) - pos[party == 1].mean(0))))

    sep_final = float(np.mean(sep_traj[-9:]))    # smoothed endpoint
    corner_frac = float(np.mean(np.any(np.abs(pos) > 0.9, axis=1)))
    wp_sd = float(np.mean([pos[party == p].std(0).mean() for p in (0, 1)]))
    elite_sep = float(np.linalg.norm(elite[0] - elite[1]))
    stable = bool(np.std(sep_traj[-20:]) < 0.05)
    return dict(
        sep_final=sep_final, corner_frac=corner_frac, wp_sd=wp_sd,
        elite_sep=elite_sep, mass_elite_gap=elite_sep - sep_final,
        stable=stable, seed_sep0=float(sep_traj[0]),
    )


def classify(r: dict) -> str:
    if not r["stable"]:
        return "UNSTABLE"
    if r["sep_final"] < 0.40:
        return "FIZZLE"
    if r["corner_frac"] > 0.20 or r["wp_sd"] < 0.15 or r["sep_final"] > 1.60:
        return "RUNAWAY"
    if (SEP_LO <= r["sep_final"] <= SEP_HI and WPSD_LO <= r["wp_sd"] <= WPSD_HI
            and r["corner_frac"] <= CORNER_MAX and r["mass_elite_gap"] > 0):
        return "REALISTIC"
    return "PARTIAL"   # stable, non-degenerate, but outside the realistic window


def main() -> None:
    SEEDS = (0, 1, 2)
    gains = (1.5, 2.0, 2.5, 3.0)
    ceils = (0.55, 0.65, 0.75)              # saturating elite extremity ceiling
    sigmas = (0.22, 0.28, 0.34)             # per-agent cue spread (within-party SD)
    counters = (0.02, 0.05, 0.08)           # FJ-anchor counter-force

    rows = []
    for gain, ceil, sigma, counter in product(gains, ceils, sigmas, counters):
        runs = [run_loop(s, elite_gain=gain, elite_ceiling=ceil, sigma_cue=sigma,
                         counter=counter, homophily=0.0) for s in SEEDS]
        agg = {k: float(np.mean([r[k] for r in runs]))
               for k in ("sep_final", "corner_frac", "wp_sd", "elite_sep", "mass_elite_gap")}
        agg["stable"] = all(r["stable"] for r in runs)
        verdicts = [classify(r) for r in runs]
        # cell verdict = modal across seeds
        cell = max(set(verdicts), key=verdicts.count)
        rows.append(dict(gain=gain, ceil=ceil, sigma=sigma, counter=counter,
                         verdict=cell, **agg))

    realistic = [r for r in rows if r["verdict"] == "REALISTIC"]
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1

    # --- console report ---
    print(f"E0 loop-feasibility — {len(rows)} cells x {len(SEEDS)} seeds\n")
    print("verdict counts:", counts)
    print(f"\nREALISTIC regime: {len(realistic)} / {len(rows)} cells")
    if realistic:
        print(f"{'gain':>5}{'ceil':>6}{'counter':>8}{'sigma':>6}"
              f"{'sep':>7}{'wpSD':>7}{'corner':>8}{'gap':>7}")
        for r in sorted(realistic, key=lambda x: -x["sep_final"]):
            print(f"{r['gain']:>5}{r['ceil']:>6}{r['counter']:>8}{r['sigma']:>6}"
                  f"{r['sep_final']:>7.2f}{r['wp_sd']:>7.2f}{r['corner_frac']:>8.2%}"
                  f"{r['mass_elite_gap']:>7.2f}")
    else:
        print("  (none — mapping nearest PARTIAL cells)")
        partials = sorted([r for r in rows if r["verdict"] == "PARTIAL"],
                          key=lambda x: abs(x["sep_final"] - 1.1))[:8]
        for r in partials:
            print(f"  gain={r['gain']} ceil={r['ceil']} counter={r['counter']} "
                  f"sigma={r['sigma']}: sep={r['sep_final']:.2f} wpSD={r['wp_sd']:.2f} "
                  f"corner={r['corner_frac']:.2%} gap={r['mass_elite_gap']:.2f}")

    verdict = "PASS — a stable realistic emergent regime EXISTS" if realistic \
        else "FAIL — no stable realistic regime in the swept space"
    print(f"\nGATE: {verdict}")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(
        "# E0 — loop-feasibility gate (emergence-recovery)\n\n"
        f"Throwaway standalone harness (`scripts/audit/e0_loop_feasibility.py`), "
        f"{len(rows)} cells x {len(SEEDS)} seeds. Nothing positional fed; only a "
        f"tiny initial party asymmetry seeds symmetry-breaking.\n\n"
        f"**GATE: {verdict}.**\n\n"
        f"Verdict counts: `{counts}`.\n\n"
        f"REALISTIC = sep in [{SEP_LO},{SEP_HI}], wpSD in [{WPSD_LO},{WPSD_HI}], "
        f"corner<={CORNER_MAX:.0%}, stable, mass<elite. "
        f"{len(realistic)}/{len(rows)} cells.\n\n"
        + ("| gain | ceil | counter | sigma | sep | wpSD | corner | mass-elite gap |\n"
           "|---|---|---|---|---|---|---|---|\n"
           + "".join(
               f"| {r['gain']} | {r['ceil']} | {r['counter']} | {r['sigma']} | "
               f"{r['sep_final']:.2f} | {r['wp_sd']:.2f} | {r['corner_frac']:.2%} | "
               f"{r['mass_elite_gap']:.2f} |\n"
               for r in sorted(realistic, key=lambda x: -x["sep_final"]))
           if realistic else "_No realistic cells; see console for nearest PARTIAL cells._\n")
        + "\n_All rows:_\n\n```json\n" + json.dumps(rows, indent=1) + "\n```\n"
    )
    print(f"\nwrote {OUT_MD}")


if __name__ == "__main__":
    main()
