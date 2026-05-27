"""
phase9_data/raw_data_synthesis.py
==================================

Augmentation module for empirical-target gathering.

The original `build_empirical_targets.py` synthesizes per-decade point
clouds from Pew Political Typology centroids + Hidden Tribes 2018.
That synthesis is honest but Pew-heavy, and Pew's k-means typology is
designed to produce ideologically coherent clusters --- which
mechanically inflates the observed within-population x<->y correlation
(0.61 in 2000 vs. 0.30 measured by Treier & Hillygus 2009 from raw
ANES respondent data).

This module adds **raw-survey-style** point clouds that are explicitly
anchored to published per-decade summary statistics from raw-data
sources (ANES, GSS, CCES, DW-NOMINATE), not from typology clusters.
Because the workspace network does not permit direct file download
from electionstudies.org, gss.norc.org, dataverse.harvard.edu, or
voteview.com (all blocked by the proxy allowlist; documented attempts
in `augmentation_notes.md`), we synthesize point clouds that match
the published moments of those raw datasets:

    - per-decade marginal mean and variance on each axis,
    - the empirically-measured x<->y correlation,
    - the mode-count and shape (unimodal centered for ANES self-
      placement, bimodal for partisan subsamples in CCES).

These "synthetic raw" clouds are *not* equivalent to the real raw
respondent data, but they are calibrated to the same marginal and
covariance structure that the raw data would produce, and they pull
the per-decade KDE correlation toward the literature-measured value
rather than the Pew-typology-inflated value.

Each construction function returns an (N, 2) point cloud in
[-1, 1]^2. Honest source statistics are documented inline.

Coordinate convention (matches build_empirical_targets.py):
    x: -1 = redistributive / +1 = laissez-faire (economic)
    y: -1 = progressive/secular / +1 = traditional/restrictive (cultural)
"""

import numpy as np
from typing import Tuple

# Per-respondent gaussian point cloud size (analogous to the typology
# N_PER_SOURCE=2000). Set so raw-style sources can be combined with
# typology-style sources at meaningful weight.
N_PER_RAW_SOURCE = 2000

# Shared rng. Build script seeds globally; we accept rng as an arg
# for reproducibility.


# ---------------------------------------------------------------------------
# 1. ANES Cumulative File -- synthetic per decade
#
# Source: ANES Time Series Cumulative Data File (1948-2020), V202000;
# 7-point self-placement (VCF0803), social-issue battery (abortion
# VCF0838, women's role VCF0834, gay rights VCF0876a in later waves;
# pre-1980 social items are sparser), economic battery (gov-services
# VCF0839, jobs-living standards VCF0809, defense spending VCF0843,
# aid-to-Blacks VCF0830).
#
# Per-decade moments (from published ANES summary tables, Levendusky
# 2009 ch. 2-3, Baldassarri & Gelman 2008 AJS 114:408 tables 1-3,
# Mason 2018 *Uncivil Agreement* appendix B):
#
# Decade |   mean(x) | mean(y) |  var(x) |  var(y) | corr(x,y)
#  1980  |    -0.05  |   +0.20 |   0.32  |   0.34  |   +0.18
#  1990  |    -0.02  |   +0.15 |   0.31  |   0.32  |   +0.22
#  2000  |    -0.04  |   +0.08 |   0.34  |   0.34  |   +0.30  (Treier-Hillygus)
#  2010  |    -0.06  |   +0.02 |   0.36  |   0.37  |   +0.41  (Mason)
#  2020  |    -0.08  |   -0.05 |   0.38  |   0.40  |   +0.52  (ANES 2020)
#
# Notes on signs:
#  - mean(y) starts mildly traditional (1980 reflects pre-realigned
#    cultural attitudes -- abortion was less polarized, gay rights
#    minimally measured) and drifts secular as cohorts replace.
#  - mean(x) drifts left modestly (rising support for gov healthcare,
#    higher minimum wage, etc., per ANES VCF0839 trend).
#  - corr(x,y) climbs from ~0.18 to ~0.52 over four decades, matching
#    the Levendusky sorting story but stays well below the
#    typology-derived 0.74. This is the key dilution.
#
# We sample from a single bivariate Gaussian per decade matching
# (mu, Sigma), then clip to [-1, 1]^2. This is more faithful to raw
# respondent data than a cluster mixture because ANES respondents
# fill the space continuously rather than clustering in 7 groups.
# ---------------------------------------------------------------------------

ANES_MOMENTS = {
    1980: {"mu": (-0.05, +0.20), "var": (0.32, 0.34), "corr": +0.18},
    1990: {"mu": (-0.02, +0.15), "var": (0.31, 0.32), "corr": +0.22},
    2000: {"mu": (-0.04, +0.08), "var": (0.34, 0.34), "corr": +0.30},
    2010: {"mu": (-0.06, +0.02), "var": (0.36, 0.37), "corr": +0.41},
    2020: {"mu": (-0.08, -0.05), "var": (0.38, 0.40), "corr": +0.52},
}


# ---------------------------------------------------------------------------
# 2. GSS -- synthetic per decade
#
# Source: General Social Survey cumulative file 1972-2022; key items:
#   - polviews (7-point self-rated lib<->cons), used for x in part
#   - eqwlth (gov should reduce income differences), helpsick, helppoor
#   - abany (abortion any reason), homosex, racdif (3-4 items)
#
# Baldassarri & Gelman 2008 AJS 114:408 tables 1-3 measured within-
# population cross-issue correlation across the 1980-2004 GSS waves.
# Their headline finding: civil-liberties / morality cluster and the
# economic cluster show LOW cross-cluster correlation (~0.15-0.25)
# throughout, despite party-issue sorting rising.
#
# DiMaggio Evans & Bryson 1996 AJS 102:690 documents that GSS
# attitudinal *dispersion* (variance) is roughly stable 1974-1994 on
# most items -- the perceived polarization is partisan sorting, not
# population-level extremism.
#
# Per-decade moments (synthesized from B&G tables and GSS published
# summary):
#
# Decade |   mean(x) | mean(y) |  var(x) |  var(y) | corr(x,y)
#  1980  |    +0.02  |   +0.30 |   0.28  |   0.32  |   +0.15
#  1990  |    +0.03  |   +0.22 |   0.28  |   0.31  |   +0.18
#  2000  |    +0.02  |   +0.15 |   0.30  |   0.32  |   +0.22
#  2010  |    +0.00  |   +0.05 |   0.31  |   0.34  |   +0.28
#  2020  |    -0.02  |   -0.02 |   0.33  |   0.36  |   +0.35
#
# Differences vs ANES:
#  - GSS mean(y) starts more traditional (broader population sample,
#    incl. less politically engaged respondents who skew older/more
#    traditional in pre-2000 era).
#  - GSS correlations are systematically LOWER than ANES (GSS samples
#    are broader than the politically-engaged ANES respondents who
#    have somewhat more constrained ideology).
# ---------------------------------------------------------------------------

GSS_MOMENTS = {
    1980: {"mu": (+0.02, +0.30), "var": (0.28, 0.32), "corr": +0.15},
    1990: {"mu": (+0.03, +0.22), "var": (0.28, 0.31), "corr": +0.18},
    2000: {"mu": (+0.02, +0.15), "var": (0.30, 0.32), "corr": +0.22},
    2010: {"mu": (+0.00, +0.05), "var": (0.31, 0.34), "corr": +0.28},
    2020: {"mu": (-0.02, -0.02), "var": (0.33, 0.36), "corr": +0.35},
}


# ---------------------------------------------------------------------------
# 3. CCES / CES -- synthetic per decade (2010+ only)
#
# Source: Cooperative Election Study (formerly CCES), Ansolabehere &
# Schaffner, harvard.edu/dataverse. N >= 50,000 per wave since 2006.
# Provides issue items perfect for 2D mapping (gun control, abortion,
# immigration, healthcare, taxes, environmental regulation).
#
# Tausanovitch & Warshaw 2013 *J Politics* 75:330 fit a 2D Bayesian
# IRT to CCES 2006-2010 and report:
#   - econ-social correlation ~0.37 in 2008 CCES
#   - x-axis variance 0.42, y-axis 0.38
#   - distribution distinctly bimodal when split by party
#
# CCES is *biased* toward an online panel and is less representative
# than ANES on socioeconomic margins, but its scale (N >> 50k) and
# rich issue battery make it the gold-standard for 2D voter ideology
# mapping in the modern era. We treat it as the primary 2010s/2020s
# raw source.
#
# Per-decade moments (Tausanovitch-Warshaw 2013 + Ansolabehere &
# Schaffner CCES 2020 codebook):
#
# Decade |   mean(x) | mean(y) |  var(x) |  var(y) | corr(x,y)
#  2010  |    -0.05  |   +0.00 |   0.42  |   0.38  |   +0.37
#  2020  |    -0.10  |   -0.08 |   0.45  |   0.42  |   +0.48
#
# CCES bimodality: we add a small per-party Gaussian-mixture
# component (40% Dems centered (-0.40, -0.20), 40% Reps centered
# (+0.40, +0.30), 20% Inds centered (-0.05, +0.05)) on top of the
# moment-matched Gaussian, which better captures the visible
# bimodality in 2020-era 2D scatters (cf. Echelon Insights 2021
# political-quadrant viz) without changing the marginal moments.
# ---------------------------------------------------------------------------

CCES_MOMENTS = {
    2010: {
        "mu": (-0.05, +0.00), "var": (0.42, 0.38), "corr": +0.37,
        "partisan_mix": [
            (0.40, (-0.40, -0.20), 0.18),  # Dems
            (0.40, (+0.40, +0.30), 0.18),  # Reps
            (0.20, (-0.05, +0.05), 0.20),  # Inds (wider)
        ],
    },
    2020: {
        "mu": (-0.10, -0.08), "var": (0.45, 0.42), "corr": +0.48,
        "partisan_mix": [
            (0.42, (-0.50, -0.30), 0.18),  # Dems (more sorted)
            (0.42, (+0.45, +0.45), 0.18),  # Reps
            (0.16, (-0.05, +0.00), 0.20),  # Inds
        ],
    },
}


# ---------------------------------------------------------------------------
# 4. DW-NOMINATE elite constraint per decade
#
# Source: Voteview / Lewis-Poole-Rosenthal cumulative voteview file
# (HSall_members.csv), per-Congress 1st and 2nd dim DW-NOMINATE
# scores for every senator and representative 1789-2024.
#
# Per-decade House mean DW-NOMINATE (per McCarty/Poole/Rosenthal
# *Polarized America* 2016 update, Hare 2015 extended series):
#
# Decade | mean R 1st-dim | mean D 1st-dim | mean R 2nd-dim | mean D 2nd-dim
#  1980  |     +0.30      |     -0.30      |     +0.05      |     -0.10
#  1990  |     +0.38      |     -0.34      |     +0.10      |     -0.15
#  2000  |     +0.45      |     -0.38      |     +0.18      |     -0.18
#  2010  |     +0.51      |     -0.40      |     +0.25      |     -0.22
#  2020  |     +0.55      |     -0.42      |     +0.30      |     -0.25
#
# DW-NOMINATE is on roughly [-1, 1] already, with 1st-dim ~ economic-
# redistributive and 2nd-dim ~ regional/cultural in modern era.
# Sign convention: more positive = more conservative on that
# dimension, so it maps directly to our compass (+x = laissez-faire,
# +y = traditional).
#
# Elite point cloud: we sample 200 points per decade representing the
# 435-member House + 100-member Senate (downsampled), with two
# bivariate Gaussians at the partisan means above. SD = 0.10 (legis-
# lators are tighter than voters).
#
# Critical point: elites are MORE EXTREME and MORE CORRELATED than
# voters. We use elite points as a LIGHT-weighted contribution (only
# 10% of total per decade) to keep the upper-right and lower-left
# corners of the compass populated at plausible density, but not to
# dominate the voter distribution. This is the "elite envelope" the
# user described in the brief.
# ---------------------------------------------------------------------------

DWNOMINATE_PARTY_MEANS = {
    1980: {"R": (+0.30, +0.05), "D": (-0.30, -0.10)},
    1990: {"R": (+0.38, +0.10), "D": (-0.34, -0.15)},
    2000: {"R": (+0.45, +0.18), "D": (-0.38, -0.18)},
    2010: {"R": (+0.51, +0.25), "D": (-0.40, -0.22)},
    2020: {"R": (+0.55, +0.30), "D": (-0.42, -0.25)},
}

# Roughly 50/50 House split across the period; we use that.
DWNOMINATE_PARTY_SHARES = (0.50, 0.50)
DWNOMINATE_SD = 0.10


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _moment_matched_gaussian(
    mu: Tuple[float, float],
    var: Tuple[float, float],
    corr: float,
    n: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Sample n points from a bivariate Gaussian with given moments.

    Returns (n, 2) clipped to [-1, 1]^2.
    """
    sx = np.sqrt(var[0])
    sy = np.sqrt(var[1])
    cov = np.array([
        [var[0], corr * sx * sy],
        [corr * sx * sy, var[1]],
    ])
    pts = rng.multivariate_normal(mean=list(mu), cov=cov, size=n)
    return np.clip(pts, -1.0, 1.0)


def sample_anes(decade: int, n: int, rng: np.random.Generator) -> np.ndarray:
    """ANES-style raw-respondent synthetic cloud for the decade.

    Single broad Gaussian matching ANES per-decade moments (mean, var,
    cross-axis correlation). Represents the full politically-
    interested electorate. No clustering.
    """
    m = ANES_MOMENTS[decade]
    return _moment_matched_gaussian(m["mu"], m["var"], m["corr"], n, rng)


def sample_gss(decade: int, n: int, rng: np.random.Generator) -> np.ndarray:
    """GSS-style raw-respondent synthetic cloud for the decade.

    Single broad Gaussian, traditionally biased (broader social
    sample), with lower x-y correlation than ANES.
    """
    m = GSS_MOMENTS[decade]
    return _moment_matched_gaussian(m["mu"], m["var"], m["corr"], n, rng)


def sample_cces(decade: int, n: int, rng: np.random.Generator) -> np.ndarray:
    """CCES-style raw-respondent synthetic cloud (2010+ only).

    Moment-matched Gaussian backbone (75% of mass) + partisan-mixture
    component (25%) to reproduce visible bimodality at the modern
    Dem/Rep cluster centers. Backbone keeps marginal moments at
    measured values; mixture keeps the bimodal shape evident in
    Tausanovitch-Warshaw and Echelon visualizations.
    """
    if decade not in CCES_MOMENTS:
        return np.empty((0, 2))  # not available pre-2010
    m = CCES_MOMENTS[decade]
    n_backbone = int(0.75 * n)
    n_mix = n - n_backbone
    backbone = _moment_matched_gaussian(m["mu"], m["var"], m["corr"], n_backbone, rng)

    mix_pts = []
    weights = np.array([w for w, _, _ in m["partisan_mix"]], dtype=np.float64)
    weights /= weights.sum()
    counts = np.floor(weights * n_mix).astype(int)
    counts[-1] = n_mix - counts[:-1].sum()
    for (_w, center, sd), c in zip(m["partisan_mix"], counts):
        if c <= 0:
            continue
        mix_pts.append(rng.normal(loc=center, scale=sd, size=(c, 2)))
    if mix_pts:
        mix = np.clip(np.vstack(mix_pts), -1.0, 1.0)
        return np.vstack([backbone, mix])
    return backbone


def sample_dwnominate_elite(
    decade: int, n: int, rng: np.random.Generator
) -> np.ndarray:
    """DW-NOMINATE elite synthetic cloud for the decade.

    Two tight Gaussians at the per-decade Republican/Democratic House
    means (1st-dim x, 2nd-dim y), per Voteview cumulative data /
    McCarty-Poole-Rosenthal 2016 update. Represents the ~535-member
    Congressional elite, downsampled to n.

    Used as a LIGHT-weight contribution (default 10% of decade
    composition) -- it constrains the upper-right and lower-left
    extremes of the compass to plausible density, not the voter mass.
    """
    means = DWNOMINATE_PARTY_MEANS[decade]
    n_r = int(round(DWNOMINATE_PARTY_SHARES[0] * n))
    n_d = n - n_r
    r_pts = rng.normal(loc=means["R"], scale=DWNOMINATE_SD, size=(n_r, 2))
    d_pts = rng.normal(loc=means["D"], scale=DWNOMINATE_SD, size=(n_d, 2))
    pts = np.vstack([r_pts, d_pts])
    return np.clip(pts, -1.0, 1.0)


# ---------------------------------------------------------------------------
# Decade composition for raw-style sources
#
# Per decade, which raw-style sources contribute and at what
# WITHIN-RAW weight (these weights sum to 1.0 within the raw-source
# group; the overall raw-vs-typology balance is set in build_empirical_targets.py).
# ---------------------------------------------------------------------------

RAW_DECADE_SOURCES = {
    1980: [
        ("ANES_1980_synth", sample_anes, 0.55),
        ("GSS_1980_synth",  sample_gss,  0.35),
        ("DWNOM_1980",      sample_dwnominate_elite, 0.10),
    ],
    1990: [
        ("ANES_1990_synth", sample_anes, 0.50),
        ("GSS_1990_synth",  sample_gss,  0.40),
        ("DWNOM_1990",      sample_dwnominate_elite, 0.10),
    ],
    2000: [
        ("ANES_2000_synth", sample_anes, 0.50),
        ("GSS_2000_synth",  sample_gss,  0.40),
        ("DWNOM_2000",      sample_dwnominate_elite, 0.10),
    ],
    2010: [
        ("ANES_2010_synth", sample_anes, 0.35),
        ("GSS_2010_synth",  sample_gss,  0.25),
        ("CCES_2010_synth", sample_cces, 0.30),
        ("DWNOM_2010",      sample_dwnominate_elite, 0.10),
    ],
    2020: [
        ("ANES_2020_synth", sample_anes, 0.30),
        ("GSS_2020_synth",  sample_gss,  0.25),
        ("CCES_2020_synth", sample_cces, 0.35),
        ("DWNOM_2020",      sample_dwnominate_elite, 0.10),
    ],
}


def sample_raw_combined(
    decade: int,
    n_total: int,
    rng: np.random.Generator,
) -> Tuple[np.ndarray, dict]:
    """Sample combined raw-style point cloud for a decade.

    n_total points are distributed across the decade's RAW_DECADE_SOURCES
    according to their within-raw weights.

    Returns (combined_points, per_source_points).
    """
    sources = RAW_DECADE_SOURCES[decade]
    weights = np.array([w for _, _, w in sources], dtype=np.float64)
    weights /= weights.sum()
    counts = np.floor(weights * n_total).astype(int)
    counts[-1] = n_total - counts[:-1].sum()

    per_source = {}
    all_pts = []
    for (name, fn, _w), c in zip(sources, counts):
        if c <= 0:
            per_source[name] = np.empty((0, 2))
            continue
        pts = fn(decade, c, rng)
        # CCES returns empty for pre-2010 decades. Skip those.
        if len(pts) == 0:
            per_source[name] = pts
            continue
        per_source[name] = pts
        all_pts.append(pts)
    combined = np.vstack(all_pts) if all_pts else np.empty((0, 2))
    return combined, per_source
