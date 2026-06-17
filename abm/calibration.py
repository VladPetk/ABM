"""Calibration constants — the bridge between simulation ticks and
real-world time.

Phase 7 anchors the engine to one published empirical trajectory: the
American National Election Studies (ANES) out-party feeling-thermometer
fall from ~48° (1978) to ~20° (2020) — a 28-point drop over 42 years
(Iyengar et al. 2019 *ARPS* 22:129; Finkel et al. 2020 *Science*
370:533). The pillar's S0→S3 affective-polarization trajectory under
Phase 5 (Δ ≈ -0.85 over 200 ticks) projects to roughly -0.53 over a
42-year window — within ~5% of the ANES headline of -0.56 on the
model's [-1, 1] axis. Pinning this gives **one tick ≈ 0.33 years**;
rounded to a clean integer fraction, **1 year = 3 ticks**. (This "~5%"
is a PILLAR-trajectory projection used to pin the tick-to-year scalar
only; it is NOT a fidelity claim about the shipped arc's affect, which
is currently out of the grounded ANES bands — see methods.md §3.1 and
blindspot #1.)

The single scalar ``TICKS_PER_YEAR = 3.0`` is the project's public,
defensible mapping. Every metric and intervention can be reported in
years rather than ticks; the eventual web product can label x-axes
"1955 → 2022" rather than "tick 0 → 200".

See ``methods.md`` for the calibration argument and Phase 7 sensitivity
sweeps. The ``EMPIRICAL_ANCHORS`` registry below is the project's
auditable record of which published findings each pinning rests on.
"""
from __future__ import annotations

# Phase 7 §3: the calibration scalar. Pinned by anchoring the pillar's
# S0→S3 affective_polarization trajectory to the ANES out-party-
# thermometer fall (~28 points / ~42 years / [-0.56 on the model's
# [-1, 1] axis]). The pillar's measured Δaff over the same window is
# ~-0.53 — within ~5% of the empirical anchor. Rounded to a clean
# integer: 1 year = 3 ticks; 1 tick ≈ 4 months.
# (The "~5%" pins the tick scalar off the PILLAR trajectory; it is not a
# claim about the shipped arc's affect — see the docstring caveat above.)
TICKS_PER_YEAR: float = 3.0


def ticks_to_years(ticks: float) -> float:
    """Convert tick count to years. 200 ticks ≈ 67 years."""
    return ticks / TICKS_PER_YEAR


def years_to_ticks(years: float) -> int:
    """Convert years to tick count (rounded). 42 years = 126 ticks."""
    return int(round(years * TICKS_PER_YEAR))


# Empirical calibration anchors — the auditable record of which
# published findings each pinning decision rests on. See methods.md
# §3 for the longer-form citation and reasoning.
EMPIRICAL_ANCHORS = {
    "out_party_thermometer": {
        "source": (
            "Iyengar, Lelkes, Levendusky, Malhotra & Westwood 2019 "
            "(ARPS 22:129); Finkel et al. 2020 (Science 370:533)"
        ),
        "metric": "Δ out-party feeling thermometer, 1978 → 2020",
        "value_raw": -28.0,           # degrees on [0, 100]
        "value_normalised": -0.56,    # on the model's [-1, 1] axis
        "duration_years": 42.0,
        "model_check": (
            "pillar S0→S3 measured Δaffective_polarization ≈ -0.85 over "
            "200 ticks; restricted to a 42-year window at "
            "TICKS_PER_YEAR=3 (126 ticks) projects to ~-0.53 — within "
            "~5% of the ANES anchor. NOTE (2026-06 peer-review audit, F3/F16): "
            "this is a PILLAR-trajectory projection used only to pin the "
            "tick-to-year scalar; it is NOT a fidelity claim about the "
            "SHIPPED ARC's affect, which is currently OUT of the grounded "
            "ANES bands at all five decades (too cold) — see methods.md §3.1 "
            "and blindspot #1. Do not cite this as arc affect validation."
        ),
    },
    "dw_nominate_divergence": {
        "source": "McCarty, Poole & Rosenthal 2006 (Polarized America)",
        "metric": "Δ Democratic-Republican median NOMINATE score, ~1970-2020",
        "value_raw": 0.4,             # NOMINATE units
        "duration_years": 50.0,
        "model_check": (
            "EliteDrift.rate ≈ 0.0026 per tick reproduces the elite-"
            "divergence rate if active. EliteDrift is inert in the "
            "pillar's S0-S4 baseline; this anchor is a sanity check "
            "for any scenario that enables it."
        ),
    },
    "pettigrew_tropp_contact": {
        "source": (
            "Pettigrew & Tropp 2006 (JPSP 90:751, meta-analysis of "
            "515 studies, r ≈ -0.21 between contact and prejudice)"
        ),
        "metric": (
            "Contact under Allport conditions halves prejudice "
            "formation rate (approximate meta-analytic reading)"
        ),
        "value_normalised": 0.5,      # the cooperative_mute multiplier
        "model_check": (
            "AffectiveUpdate.cooperative_mute = 0.5 — out-party "
            "encounters over cooperative edges (X6's added ties) "
            "produce half-strength negative valence. Calibration is "
            "deliberate, not bucket-engineered: see Phase 7 spec §6."
        ),
    },
    "facebook_deactivation": {
        "source": (
            "Allcott, Braghieri, Eichmeyer & Gentzkow 2020 (AER "
            "110:629); Guess et al. 2023 (Science 381:398); "
            "Nyhan et al. 2023 (Nature)"
        ),
        "metric": (
            "Δ issue + affective polarization, 4-week to 3-month "
            "Facebook/algorithmic feed intervention"
        ),
        "value_raw_sd": -0.04,        # small SD reduction (Allcott)
        "value_meta": "essentially null (Guess/Nyhan)",
        "duration_years": 0.25,       # ~3 months
        "model_check": (
            "X2 'Fix the algorithm' simulates a sustained algorithmic-"
            "affect-muting policy (not Allcott's 4-week deactivation) "
            "and measures Δsep ≈ -0.02, Δaff ≈ -0.01 — qualitatively "
            "consistent with the null finding of the Meta/2020 studies; "
            "not an apples-to-apples replication of Allcott's "
            "short-window effect-size."
        ),
    },
}
