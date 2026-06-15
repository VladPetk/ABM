"""
CommonModeCulture — the society-wide cultural baseline channel (reality-validation
workstream, branch model-reality-validation).

WHY THIS EXISTS. The engine had only a *differential* (party-sorting) channel on
the cultural axis: the symmetric endogenous elite loop (``activist_elite.py``)
keeps the two party elites' midpoint ≈ 0, and ``PartyPull`` drags the mass to
track that midpoint, so cultural position is effectively collapsed onto party.
The from-scratch ANES+GSS validation (``validation/``) showed the consequence:
the partisan cultural *center of mass* sits ~0.10–0.20 too progressive in the
mid-period (1990s–2000s), when real voters were culturally TRADITIONAL, even
though the 2020s endpoint matches (so band tests were blind to it). This is the
society-wide secular cultural trend the engine could not represent.

THE MECHANISM (emergent, not fed). Secular cultural liberalization is, in the
data, ~69 % **cohort replacement** and ~31 % within-cohort period drift (GSS
1972–2024 age–period decomposition; cf. Firebaugh & Davis 1988; Brooks &
Bolzendahl 2004; Baunach 2012). We model the dominant driver directly: each agent
carries a ``birth_year``; its cultural baseline follows the **measured ANES
birth-cohort gradient** (older cohorts traditional, younger progressive). The
society-wide common mode ``m(t)`` is the population mean of that baseline, and it
declines **emergently** as traditional cohorts are replaced by progressive ones.
This rule expresses ``m(t)`` as a rigid common-mode shift of the cultural frame
(positions + anchors + party cues + elite centroids together), so it moves the
societal *level* WITHOUT touching the *differential* (party_sep, within-party
spread, econ–cult correlation are unchanged — a rigid translation is
sorting-invariant; validated in ``validation/exp_commonmode.py``).

WHAT IS FED. Only two demographic *primitives*: the generational gradient
``CULTURAL_BIRTH_GRADIENT`` (a measured per-cohort fact) and the turnover rate
(a demographic fact). The aggregate cultural trajectory is NOT fed — it emerges
from the gradient × the turnover. Provenance: **L** (cohort-replacement mechanism)
+ **N** (the rigid common-mode expression; functional form is the design choice).

GATED. Installed only when ``cultural_common_mode=True``; absent on the default
path → bit-identical to head.
"""
from __future__ import annotations

import numpy as np

# Measured ANES cultural mean by birth decade, compass units (+ = traditional);
# validation/anes_from_raw.py over the cumulative file. Born 1910s ≈ +0.17 →
# born 2000s ≈ -0.29; ≈ -0.044 compass-units per decade of birth.
CULTURAL_BIRTH_GRADIENT = {
    1900: 0.169, 1910: 0.165, 1920: 0.142, 1930: 0.157, 1940: 0.103,
    1950: 0.056, 1960: 0.046, 1970: -0.009, 1980: -0.084, 1990: -0.201,
    2000: -0.288, 2010: -0.340,
}
_GX = sorted(CULTURAL_BIRTH_GRADIENT)
_GY = [CULTURAL_BIRTH_GRADIENT[k] for k in _GX]


def cultural_birth_baseline(birth_year: float) -> float:
    """Cultural traditionalism baseline (compass units) for a birth year,
    by linear interpolation over the measured gradient (clamped at the ends)."""
    return float(np.interp(birth_year, _GX, _GY))


def sample_initial_birth_years(n: int, rng: np.random.Generator,
                               mean_birth: float = 1940.0, sd: float = 18.0):
    """Birth years for the 1980 adult electorate. Centered so the initial mean
    baseline ≈ ANES 1986 partisan cultural center (+0.10 ⇒ born ~1940); clipped
    to people who were adults in 1980 (born 1905–1962)."""
    return np.clip(rng.normal(mean_birth, sd, size=n), 1905.0, 1962.0)


def replacement_birth_year(tick: int, rng: np.random.Generator,
                           ticks_per_year: float = 3.0,
                           tick_0_year: float = 1980.0) -> float:
    """A young-adult entrant's birth year at a given tick (age 18–26)."""
    entry_year = tick_0_year + tick / ticks_per_year
    return float(entry_year - rng.uniform(18.0, 26.0))


class CommonModeCulture:
    """EnvRule. Track the society-wide cultural baseline m(t) (set by the
    birth-year composition) via a rigid common-mode frame shift.

    relax = 1.0 snaps the common mode to m(t) each tick (the target itself moves
    only slowly, via turnover, so this just strips any spurious common-mode drift
    the sorting forces would otherwise inject — the differential is untouched)."""

    def __init__(self, relax: float = 1.0):
        self.relax = float(relax)

    def apply(self, env, agents, space, rng, tick: int) -> None:
        partisans = [a for a in agents if a.state.attrs.get("party") in (0, 1)]
        if not partisans:
            return
        # target common mode = mean generational baseline of current partisans
        births = [a.state.attrs.get("birth_year") for a in partisans]
        if any(b is None for b in births):
            return  # birth years not seeded → inert (bit-identical safety)
        target = float(np.mean([cultural_birth_baseline(b) for b in births]))
        current = float(np.mean([a.state.ideology[1] for a in partisans]))
        delta = self.relax * (target - current)
        if abs(delta) < 1e-12:
            return

        # On the n_issues substrate the TRUTH is the 7D issue vector and ideology
        # is re-projected from it every tick (engine.step), so a shift to ideology
        # alone is cosmetic. Shift the issue vector via lift([0, delta]) — and
        # since project(lift([0,d])) == [0,d], this is exactly a rigid 2D cultural
        # translation (sorting-invariant) that persists.
        rt = env.attrs.get("issue_runtime")
        if rt is not None:
            from ..core.issues import lift, project1
            bump = lift(np.array([0.0, delta]), rt)
            for a in agents:
                v = a.state.attrs.get("issues")
                if v is not None:
                    a.state.attrs["issues"] = np.clip(v + bump, -1.0, 1.0)
                    av = a.state.attrs.get("anchor_issues")
                    if av is not None:
                        a.state.attrs["anchor_issues"] = np.clip(av + bump, -1.0, 1.0)
                    a.state.ideology = project1(a.state.attrs["issues"], rt)
                else:
                    a.state.ideology[1] += delta
                for key in ("anchor", "origin", "party_cue"):
                    p = a.state.attrs.get(key)
                    if p is not None and hasattr(p, "__len__") and len(p) == 2:
                        p[1] += delta
        else:
            for a in agents:
                a.state.ideology[1] += delta
                for key in ("anchor", "origin", "party_cue"):
                    p = a.state.attrs.get(key)
                    if p is not None and hasattr(p, "__len__") and len(p) == 2:
                        p[1] += delta

        parties = env.attrs.get("parties") or {}
        for pid in list(parties):
            p = np.asarray(parties[pid], dtype=float)
            p[1] += delta
            parties[pid] = p
