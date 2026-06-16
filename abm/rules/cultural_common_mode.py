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


# ── shared rigid common-mode machinery (axis-parametric) ──────────────────────
# Both common-mode channels (cultural = axis 1, economic = axis 0) express the
# society-wide LEVEL m(t) as a rigid translation of the whole compass frame
# (positions + anchors + party cues + elite centroids together) along ONE axis.
# A rigid translation is sorting-invariant: it moves the population's level
# WITHOUT touching the differential (party_sep, within-party spread, econ–cult
# correlation are unchanged). On the n_issues substrate the TRUTH is the 7D issue
# vector and ideology is re-projected from it every tick (engine.step), so the
# shift must hit the issue vector via ``lift``: since ``project(lift(e_ax·d)) ==
# e_ax·d``, this is exactly a rigid 2D translation along ``axis`` that persists.

def _partisan_mean_axis(agents, axis: int):
    """Population mean of ideology[axis] over partisans (party 0/1), or None."""
    vals = [a.state.ideology[axis] for a in agents
            if a.state.attrs.get("party") in (0, 1)]
    return float(np.mean(vals)) if vals else None


def rigid_common_mode_shift(env, agents, axis: int, delta: float) -> None:
    """Apply a rigid common-mode translation of magnitude ``delta`` along
    ``axis`` (0 = economic, 1 = cultural) to every agent's issue vector (or
    ideology on the legacy 2D path), their anchors/cues, and the elite
    centroids. Sorting-invariant. Shared by CommonModeCulture / CommonModeEconomic."""
    if abs(delta) < 1e-12:
        return
    rt = env.attrs.get("issue_runtime")
    if rt is not None:
        from ..core.issues import lift, project1
        e = np.zeros(2, dtype=float)
        e[axis] = delta
        bump = lift(e, rt)
        for a in agents:
            v = a.state.attrs.get("issues")
            if v is not None:
                a.state.attrs["issues"] = np.clip(v + bump, -1.0, 1.0)
                av = a.state.attrs.get("anchor_issues")
                if av is not None:
                    a.state.attrs["anchor_issues"] = np.clip(av + bump, -1.0, 1.0)
                a.state.ideology = project1(a.state.attrs["issues"], rt)
            else:
                a.state.ideology[axis] += delta
            for key in ("anchor", "origin", "party_cue"):
                p = a.state.attrs.get(key)
                if p is not None and hasattr(p, "__len__") and len(p) == 2:
                    p[axis] += delta
    else:
        for a in agents:
            a.state.ideology[axis] += delta
            for key in ("anchor", "origin", "party_cue"):
                p = a.state.attrs.get(key)
                if p is not None and hasattr(p, "__len__") and len(p) == 2:
                    p[axis] += delta

    parties = env.attrs.get("parties") or {}
    for pid in list(parties):
        p = np.asarray(parties[pid], dtype=float)
        p[axis] += delta
        parties[pid] = p


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
        # axis 1 = cultural. Rigid, sorting-invariant translation (see helper).
        rigid_common_mode_shift(env, agents, axis=1, delta=delta)


# ── Economic common-mode channel (reality-validation, branch econ-common-mode-mood) ──
# WHY THIS EXISTS. After the cultural channel shipped (d97048f), the from-scratch
# ANES+GSS battery (validation/) showed the SAME architecture gap on the ECONOMIC
# axis: a differential (party-sorting) channel but no common-mode (society-wide
# level) one. The symmetric endogenous elite loop keeps the elite econ midpoint ≈ 0
# and PartyPull drags the mass onto it, so the partisan economic *center of mass*
# is pinned ≈ 0 the whole arc — while ANES (cross-checked by GSS helppoor+eqwlth)
# rises to ~+0.15 (rightward) in the mid-90s and declines to ~−0.05 by 2024. The
# decomposition: ~84 % of the mid-90s Republican-econ residual is this common-mode
# LEVEL error, not a sorting-gap error (validation/FIX_INVESTIGATION_ECON.md).
#
# WHY A FED FORCING (not emergent like the cultural channel). The cultural common
# mode is EMERGENT — it is the mean of a measured birth-cohort gradient, and cohort
# replacement (monotone) generates the monotone cultural decline. The economic tide
# is NON-MONOTONE (rightward to the mid-90s, then leftward), so a monotone
# demographic primitive cannot generate it. The mechanism is instead the
# **thermostatic policy mood** (Erikson–MacKuen–Stimson, *The Macro Polity*;
# Wlezien's thermostat): the public's economic policy preference moves rightward
# under the Reagan→Clinton "end of big government" era (welfare reform / Gingrich
# 1994–96) and leftward in the post-2008 thermostatic reaction. This is an
# EXOGENOUS forcing — an input, not the party-sorting answer.
#
# WHAT IS FED, AND THE HONESTY CAVEAT. We feed a society-wide economic-mood offset
# series ``m_econ(year)`` and snap the econ common mode to it each tick (rigid,
# sorting-invariant). The series is a parsimonious thermostatic curve whose
# INFLECTION YEARS are documented policy events (1980 Reagan baseline → 1996
# welfare-reform peak → post-2008 leftward reaction) and whose single free scalar
# is the amplitude ``ECON_MOOD_AMPLITUDE``. We did NOT replay the ANES econ series.
# We DID download the real Stimson Annual Policy Mood (stimson.web.unc.edu,
# Mood5224.xlsx → validation/data/stimson_mood_annual.json) and use it to
# CORROBORATE the curve's direction/timing: Stimson independently shows mood
# turning conservative INTO the mid-90s (69.1@1991 → 59.0@1995) and liberal THROUGH
# the 2010s (54.8@2012 → 65.9@2020). We do NOT use Stimson as the literal tick-by-
# tick driver because it is a *government-spending* mood, not economic *self-
# placement*: fed literally it injects a spurious +0.20 econ spike at 2012 (the
# Tea-Party government-spending swing that self-placement refused) — falsified in
# validation/exp_econ_commonmode.py. Provenance: **L** (thermostatic common-mode
# mechanism) + **N** (the curve's functional form) + **E** (amplitude / shape
# extrapolated). This is a weaker honesty claim than the emergent cultural channel
# (it is a fed forcing) — documented as such.
#
# GATED. Installed only when ``economic_common_mode=True`` → bit-identical to head.

# Economic policy-mood offset, unit-amplitude shape. Linear interpolation over
# event-anchored years; ×ECON_MOOD_AMPLITUDE gives the compass-unit offset.
ECON_MOOD_ANCHOR_YEARS = [1980.0, 1996.0, 2012.0, 2024.0]
ECON_MOOD_ANCHOR_SHAPE = [0.30, 1.00, 0.45, -0.55]
# The single fitted scalar: peak econ common-mode offset (compass units) at the
# 1996 welfare-reform high-water mark. 0.09 lands the mid-90s partisan econ center
# at ≈+0.09 (the robust GSS-corroborated level), closing the diagnosed −0.13
# mid-period level error to ≈−0.02 while preserving sorting. Matching the noisier
# ANES mid-90s +0.15 hump exactly would over-fit a non-robust survey artifact (cf.
# the cultural channel matching GSS +0.07 over the ANES +0.22 hump).
ECON_MOOD_AMPLITUDE = 0.09
_ECON_TPY = 3.0          # ticks per year (engine TPY)
_ECON_Y0 = 1980.0        # tick 0 = 1980


def economic_mood_offset(year: float, amplitude: float = ECON_MOOD_AMPLITUDE) -> float:
    """Exogenous economic policy-mood common-mode offset (compass units) for a
    calendar year. Thermostatic curve, event-anchored, single amplitude scalar."""
    return float(amplitude) * float(
        np.interp(year, ECON_MOOD_ANCHOR_YEARS, ECON_MOOD_ANCHOR_SHAPE))


class CommonModeEconomic:
    """EnvRule. Track the society-wide ECONOMIC baseline m_econ(t) (an exogenous
    thermostatic policy-mood forcing) via a rigid common-mode frame shift on the
    economic axis. Mirrors CommonModeCulture but the target is fed (year → curve),
    not emergent.

    relax = 1.0 snaps the econ common mode to m_econ(t) each tick; because the
    target moves only slowly, this strips any spurious common-mode drift the
    sorting forces would otherwise inject, leaving the differential untouched."""

    def __init__(self, relax: float = 1.0,
                 amplitude: float = ECON_MOOD_AMPLITUDE,
                 ticks_per_year: float = _ECON_TPY,
                 tick_0_year: float = _ECON_Y0):
        self.relax = float(relax)
        self.amplitude = float(amplitude)
        self.tpy = float(ticks_per_year)
        self.y0 = float(tick_0_year)

    def apply(self, env, agents, space, rng, tick: int) -> None:
        current = _partisan_mean_axis(agents, axis=0)
        if current is None:
            return
        year = self.y0 + tick / self.tpy
        target = economic_mood_offset(year, self.amplitude)
        delta = self.relax * (target - current)
        # axis 0 = economic. Rigid, sorting-invariant translation (see helper).
        rigid_common_mode_shift(env, agents, axis=0, delta=delta)
