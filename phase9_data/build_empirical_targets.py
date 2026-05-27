"""
phase9_data/build_empirical_targets.py
========================================

Build per-decade empirical voter-ideology distributions in 2D
([-1, 1] x [-1, 1], economic x social/cultural), aggregated from
US political-typology waves AND raw-data-derived synthetic clouds:

    Typology sources (from build_empirical_targets.py legacy):
    - Pew Political Typology waves (1987, 1994, 1999, 2005, 2011, 2014, 2017, 2021)
    - More in Common "Hidden Tribes" (2018)

    Raw-data-style synthetic clouds (added in augmentation pass; see
    raw_data_synthesis.py and augmentation_notes.md):
    - ANES Cumulative File (1948-2020) -- moment-matched Gaussian
    - GSS Cumulative File (1972-2022) -- moment-matched Gaussian
    - CCES / CES (2006-2022, 2010+ decades only) -- bimodal mixture
    - DW-NOMINATE House+Senate elites (Voteview cumulative) -- light
      partisan-mean constraint on extremes

    Cross-checks (qualitative anchors only, not sampled):
    - Treier & Hillygus (2009) two-dimensional structure
    - Levendusky 2009 sorting trajectory
    - Echelon Insights 2021 quadrant visualization

Each typology group has:
    - centroid (x_econ, y_social) in [-1, 1]^2
    - population share (sum 1.0 per wave)

We map waves to decades:
    1980 <- 1987 Times Mirror (only first wave; pre-1987 data sparse)
    1990 <- 1994, 1999 (averaged)
    2000 <- 2005
    2010 <- 2011, 2014
    2020 <- 2017, 2021, Hidden Tribes 2018

Augmentation pass (new): for each decade we ALSO sample a raw-style
point cloud (ANES + GSS + CCES + DW-NOMINATE elite) via
`raw_data_synthesis.sample_raw_combined`, and combine the two clouds
with per-decade weights `RAW_DECADE_WEIGHTS` (raw fraction) and
`1 - RAW_DECADE_WEIGHTS` (typology fraction). Default raw fraction is
0.60-0.70 per decade. This dilutes the Pew-typology k-means
correlation artifact (see methodology doc Sec 7 and
`augmentation_notes.md`).

For each decade we:
    1. Synthesize typology cloud (Pew + HT) the legacy way.
    2. Synthesize raw cloud (ANES + GSS + CCES + DW-NOMINATE elite).
    3. Down-sample typology cloud to (1 - raw_weight) * N_TOTAL.
    4. Concatenate raw + typology -> combined cloud.
    5. Fit Gaussian KDE on 50x50 grid covering [-1, 1]^2.
    6. Normalize KDE to integrate to 1.
    7. Save: kde grid as .npy, point cloud as .npy.

Normalization assumption: every source's compass coords expressed as
([economic axis], [social/cultural axis]), with:
    - economic axis: -1 = strongly redistributive/big-gov, +1 = laissez-faire
    - social axis: -1 = progressive/secular/inclusive, +1 = traditional/religious/restrictive

Per-cluster covariance for typology sources: isotropic SD = 0.15
(default). For the 1980 typology synthetic, SD = 0.18 per Levendusky
2009 pre-sorting era.

Do NOT modify any abm/ engine code. This is a research data pipeline.
"""

import os
import sys
import numpy as np
from scipy.stats import gaussian_kde

# Make sibling module importable when this file is run as a script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from raw_data_synthesis import (
    sample_raw_combined,
    RAW_DECADE_SOURCES,
    ANES_MOMENTS, GSS_MOMENTS, CCES_MOMENTS,
    DWNOMINATE_PARTY_MEANS,
)

# ---------------------------------------------------------------------------
# 0. Configuration
# ---------------------------------------------------------------------------

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
N_PER_SOURCE = 2000
GRID_N = 50
SD_DEFAULT = 0.15
SD_1980 = 0.18  # wider pre-sorting variance per Levendusky 2009
GRID_RANGE = (-1.0, 1.0)

# Augmentation re-weighting: per decade, what fraction of the combined
# point cloud comes from raw-style sources vs typology sources?
# Raw sources include ANES, GSS, CCES (2010+), DW-NOMINATE elite.
# 1980: 60% raw (ANES+GSS are well-documented for this decade,
#                Levendusky/B&G analyses anchor the moments)
# 1990: 65% raw (B&G AJS 2008 covers 1990s extensively)
# 2000: 70% raw (Treier-Hillygus direct measurement available)
# 2010: 70% raw (CCES enters with large N)
# 2020: 65% raw (Pew 2017+2021 typology has high-quality recent data
#                so we keep it weighted modestly)
RAW_DECADE_WEIGHTS = {
    1980: 0.60,
    1990: 0.65,
    2000: 0.70,
    2010: 0.70,
    2020: 0.65,
}

# Per-decade total point count after augmentation. We keep the
# combined N >= the legacy N so KDE smoothness is preserved.
N_TOTAL_PER_DECADE = {
    1980: 5000,  # was 2000
    1990: 5000,  # was 4000
    2000: 5000,  # was 2000
    2010: 6000,  # was 4000
    2020: 7000,  # was 6000
}

rng = np.random.default_rng(20260527)


# ---------------------------------------------------------------------------
# 1. Typology centroids per wave
#
# Each entry: name -> (x_econ, y_social, share)
# x_econ:  -1 progressive/redistributive .. +1 conservative/laissez-faire
# y_social: -1 progressive/secular/inclusive .. +1 traditional/restrictive
# ---------------------------------------------------------------------------

PEW_1987 = {  # Times Mirror; centroids inferred from group descriptions
    "Enterprisers":     ( 0.65,  0.35, 0.10),
    "Moralists":        ( 0.45,  0.75, 0.11),
    "Upbeats":          ( 0.35,  0.10, 0.09),
    "Disaffecteds":     ( 0.15,  0.30, 0.09),
    "Followers":        (-0.10, -0.10, 0.07),
    "Seculars":         (-0.45, -0.55, 0.08),
    "Sixties_Dems":     (-0.55, -0.35, 0.11),
    "New_Dealers":      (-0.40,  0.30, 0.10),
    "Passive_Poor":     (-0.30,  0.10, 0.07),
    "Partisan_Poor":    (-0.55,  0.05, 0.09),
    "Bystanders_drop":  ( 0.00,  0.00, 0.09),
}

PEW_1994 = {
    "Enterprisers":     ( 0.70,  0.40, 0.13),
    "Moralists":        ( 0.45,  0.78, 0.16),
    "Libertarians":     ( 0.55, -0.30, 0.08),
    "New_Economy_Ind":  ( 0.05, -0.05, 0.10),
    "Embittered":       ( 0.10,  0.35, 0.09),
    "Seculars":         (-0.45, -0.55, 0.07),
    "New_Dems":         (-0.20, -0.10, 0.11),
    "New_Dealers":      (-0.40,  0.30, 0.11),
    "Partisan_Poor":    (-0.55,  0.05, 0.10),
    "Bystanders_drop":  ( 0.00,  0.00, 0.05),
}

PEW_1999 = {  # post-realignment consolidation
    "Staunch_Cons":     ( 0.70,  0.55, 0.10),
    "Moderate_Repubs":  ( 0.35,  0.10, 0.11),
    "Populist_Repubs":  ( 0.20,  0.65, 0.10),
    "New_Prosperity":   ( 0.30, -0.20, 0.10),
    "Disaffecteds":     ( 0.05,  0.25, 0.09),
    "Liberal_Dems":     (-0.65, -0.55, 0.10),
    "Soc_Cons_Dems":    (-0.30,  0.45, 0.13),
    "New_Dems":         (-0.20, -0.10, 0.10),
    "Partisan_Poor":    (-0.55,  0.05, 0.07),
    "Bystanders_drop":  ( 0.00,  0.00, 0.10),
}

PEW_2005 = {
    "Enterprisers":     ( 0.75,  0.50, 0.09),
    "Social_Cons":      ( 0.35,  0.75, 0.13),
    "Pro_Gov_Cons":     (-0.10,  0.60, 0.09),
    "Upbeats":          ( 0.20, -0.05, 0.11),
    "Disaffecteds":     ( 0.05,  0.30, 0.10),
    "Conservative_Dems":(-0.30,  0.45, 0.15),
    "Disadvantaged_D":  (-0.45,  0.10, 0.10),
    "Liberals":         (-0.70, -0.65, 0.17),
    "Bystanders_drop":  ( 0.00,  0.00, 0.06),
}

PEW_2011 = {  # post-Tea-Party
    "Staunch_Cons":     ( 0.75,  0.65, 0.09),
    "Main_Street_R":    ( 0.55,  0.40, 0.11),
    "Libertarians":     ( 0.55, -0.30, 0.09),
    "Disaffecteds":     ( 0.05,  0.30, 0.11),
    "Post_Moderns":     (-0.20, -0.30, 0.13),
    "New_Coalition_D":  (-0.30,  0.20, 0.10),
    "Hard_Pressed_D":   (-0.30,  0.35, 0.13),
    "Solid_Liberals":   (-0.75, -0.70, 0.14),
    "Bystanders_drop":  ( 0.00,  0.00, 0.10),
}

PEW_2014 = {  # Solid Liberals 15%, others as reported
    "Steadfast_Cons":   ( 0.65,  0.75, 0.12),
    "Business_Cons":    ( 0.70,  0.10, 0.10),
    "Young_Outsiders":  ( 0.40, -0.30, 0.14),
    "Hard_Pressed_S":   (-0.15,  0.35, 0.13),
    "Next_Gen_Left":    (-0.40, -0.55, 0.12),
    "Faith_Family_L":   (-0.40,  0.55, 0.15),
    "Solid_Liberals":   (-0.80, -0.75, 0.15),
    "Bystanders_drop":  ( 0.00,  0.00, 0.09),
}

PEW_2017 = {
    "Core_Cons":        ( 0.80,  0.60, 0.13),
    "Country_First":    ( 0.55,  0.80, 0.06),
    "Market_Skeptic_R": ( 0.10,  0.55, 0.12),
    "New_Era_Repubs":   ( 0.50,  0.10, 0.11),
    "Devout_Diverse":   (-0.25,  0.40, 0.09),
    "Disaffected_Dems": (-0.35,  0.05, 0.14),
    "Opportunity_Dems": (-0.40, -0.20, 0.12),
    "Solid_Liberals":   (-0.85, -0.75, 0.16),
    "Bystanders_drop":  ( 0.00,  0.00, 0.08),
}

PEW_2021 = {
    "Faith_Flag":       ( 0.55,  0.85, 0.10),
    "Committed_Cons":   ( 0.75,  0.45, 0.07),
    "Populist_Right":   ( 0.20,  0.70, 0.11),
    "Ambivalent_Right": ( 0.45, -0.10, 0.12),
    "Stressed_Side":    ( 0.10,  0.20, 0.15),
    "Outsider_Left":    (-0.55, -0.50, 0.10),
    "Dem_Mainstays":    (-0.50,  0.20, 0.16),
    "Establishment_Lib":(-0.65, -0.45, 0.13),
    "Progressive_Left": (-0.90, -0.85, 0.06),
}

HIDDEN_TRIBES_2018 = {
    "Progressive_Activ":(-0.85, -0.80, 0.08),
    "Traditional_Libs": (-0.55, -0.45, 0.11),
    "Passive_Libs":     (-0.30, -0.20, 0.15),
    "Politically_Dis":  (-0.05,  0.10, 0.26),
    "Moderates":        ( 0.10,  0.15, 0.15),
    "Traditional_Cons": ( 0.55,  0.65, 0.19),
    "Devoted_Cons":     ( 0.85,  0.85, 0.06),
}


# ---------------------------------------------------------------------------
# 2. Decade composition (typology side)
# ---------------------------------------------------------------------------

DECADE_SOURCES = {
    1980: [("Pew_1987", PEW_1987, SD_1980)],
    1990: [
        ("Pew_1994", PEW_1994, SD_DEFAULT),
        ("Pew_1999", PEW_1999, SD_DEFAULT),
    ],
    2000: [("Pew_2005", PEW_2005, SD_DEFAULT)],
    2010: [
        ("Pew_2011", PEW_2011, SD_DEFAULT),
        ("Pew_2014", PEW_2014, SD_DEFAULT),
    ],
    2020: [
        ("Pew_2017", PEW_2017, SD_DEFAULT),
        ("Pew_2021", PEW_2021, SD_DEFAULT),
        ("HiddenTribes_2018", HIDDEN_TRIBES_2018, SD_DEFAULT),
    ],
}


# ---------------------------------------------------------------------------
# 3. Helpers
# ---------------------------------------------------------------------------

def synthesize_from_typology(
    typology: dict,
    n_total: int = N_PER_SOURCE,
    sd: float = SD_DEFAULT,
    rng: np.random.Generator = rng,
) -> np.ndarray:
    """Drop *_drop entries, renormalize shares, sample n_total points."""
    groups = [
        (name, x, y, share)
        for name, (x, y, share) in typology.items()
        if not name.endswith("_drop")
    ]
    shares = np.array([s for _, _, _, s in groups], dtype=np.float64)
    shares /= shares.sum()
    counts = np.floor(shares * n_total).astype(int)
    counts[-1] = n_total - counts[:-1].sum()

    points = []
    for (name, x, y, _share), n in zip(groups, counts):
        if n <= 0:
            continue
        cluster = rng.normal(loc=[x, y], scale=sd, size=(n, 2))
        points.append(cluster)
    pts = np.vstack(points)
    return np.clip(pts, -1.0, 1.0)


def fit_kde_grid(points: np.ndarray, grid_n: int = GRID_N) -> tuple:
    """Fit scipy gaussian_kde, evaluate on grid_n x grid_n grid in [-1,1]^2."""
    x = np.linspace(*GRID_RANGE, grid_n)
    y = np.linspace(*GRID_RANGE, grid_n)
    X, Y = np.meshgrid(x, y)
    coords = np.vstack([X.ravel(), Y.ravel()])
    kde = gaussian_kde(points.T, bw_method="silverman")
    Z = kde(coords).reshape(grid_n, grid_n)
    cell_area = (GRID_RANGE[1] - GRID_RANGE[0]) ** 2 / (grid_n * grid_n)
    Z = Z / (Z.sum() * cell_area)
    return X, Y, Z


def build_decade(decade: int) -> dict:
    """Build a decade's combined point cloud + KDE + per-source breakdown.

    Augmented pipeline:
      1. Synthesize typology point cloud (Pew + Hidden Tribes) as before.
      2. Synthesize raw-style point cloud (ANES + GSS + CCES + DW-NOM).
      3. Combine with re-weighting: raw gets RAW_DECADE_WEIGHTS[decade]
         fraction of the final N_TOTAL_PER_DECADE points, typology gets
         the remainder.
    """
    # --- typology side (legacy pipeline) ---
    typ_sources = DECADE_SOURCES[decade]
    typ_per_source = {}
    typ_points_list = []
    for name, typology, sd in typ_sources:
        pts = synthesize_from_typology(typology, sd=sd)
        typ_points_list.append(pts)
        typ_per_source[name] = pts
    typ_combined = np.vstack(typ_points_list)

    # --- raw side (augmentation) ---
    raw_weight = RAW_DECADE_WEIGHTS[decade]
    n_total = N_TOTAL_PER_DECADE[decade]
    n_raw = int(round(raw_weight * n_total))
    n_typ = n_total - n_raw

    raw_combined, raw_per_source = sample_raw_combined(decade, n_raw, rng)

    # Downsample typology cloud to n_typ
    if n_typ < len(typ_combined):
        idx = rng.choice(len(typ_combined), n_typ, replace=False)
        typ_combined_ds = typ_combined[idx]
    elif n_typ > len(typ_combined):
        idx = rng.choice(len(typ_combined), n_typ, replace=True)
        typ_combined_ds = typ_combined[idx]
    else:
        typ_combined_ds = typ_combined

    # --- combine ---
    if len(raw_combined) > 0:
        combined = np.vstack([raw_combined, typ_combined_ds])
    else:
        combined = typ_combined_ds
    X, Y, Z = fit_kde_grid(combined)

    # KDE-resampled 1000-agent cloud for visualization parity
    kde = gaussian_kde(combined.T, bw_method="silverman")
    resampled = kde.resample(1000, seed=rng).T
    resampled = np.clip(resampled, -1.0, 1.0)

    per_source = {**typ_per_source, **raw_per_source}

    return {
        "decade": decade,
        "X": X,
        "Y": Y,
        "Z": Z,
        "combined_points": combined,
        "per_source": per_source,
        "resampled": resampled,
        "raw_weight": raw_weight,
        "n_raw": len(raw_combined),
        "n_typ": len(typ_combined_ds),
        "raw_combined": raw_combined,
        "typ_combined": typ_combined_ds,
    }


# ---------------------------------------------------------------------------
# 4. Build + save
# ---------------------------------------------------------------------------

def main():
    summary_lines = []
    summary_lines.append(
        "decade,n_typ_sources,n_raw_sources,n_typ_points,n_raw_points,"
        "n_points_combined,raw_weight,corr_xy,var_x,var_y,mean_abs_x,kde_sum_check"
    )
    decade_objects = {}
    for decade in sorted(DECADE_SOURCES.keys()):
        obj = build_decade(decade)
        decade_objects[decade] = obj
        cell_area = (GRID_RANGE[1] - GRID_RANGE[0]) ** 2 / (GRID_N * GRID_N)
        integral = obj["Z"].sum() * cell_area
        n_typ_sources = len(DECADE_SOURCES[decade])
        n_raw_sources = len(RAW_DECADE_SOURCES[decade])
        n_points = len(obj["combined_points"])
        pts = obj["combined_points"]
        corr_xy = float(np.corrcoef(pts[:, 0], pts[:, 1])[0, 1])
        var_x = float(pts[:, 0].var())
        var_y = float(pts[:, 1].var())
        mean_abs_x = float(np.abs(pts[:, 0]).mean())
        summary_lines.append(
            f"{decade},{n_typ_sources},{n_raw_sources},"
            f"{obj['n_typ']},{obj['n_raw']},{n_points},"
            f"{obj['raw_weight']:.2f},"
            f"{corr_xy:+.4f},{var_x:.4f},{var_y:.4f},{mean_abs_x:.4f},"
            f"{integral:.6f}"
        )
        np.save(os.path.join(OUT_DIR, f"phase9_empirical_kde_{decade}.npy"), obj["Z"])
        np.save(os.path.join(OUT_DIR, f"phase9_empirical_pointcloud_{decade}.npy"), obj["resampled"])
        np.save(os.path.join(OUT_DIR, f"phase9_empirical_sources_{decade}.npy"), obj["combined_points"])

    x = np.linspace(*GRID_RANGE, GRID_N)
    y = np.linspace(*GRID_RANGE, GRID_N)
    np.save(os.path.join(OUT_DIR, "phase9_empirical_grid_x.npy"), x)
    np.save(os.path.join(OUT_DIR, "phase9_empirical_grid_y.npy"), y)

    with open(os.path.join(OUT_DIR, "phase9_empirical_build_summary.csv"), "w") as f:
        f.write("\n".join(summary_lines))
        f.write("\n")

    print("\n".join(summary_lines))
    print(f"\nWrote phase9_data outputs to: {OUT_DIR}")
    return decade_objects


if __name__ == "__main__":
    main()
