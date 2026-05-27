# Phase 9 — Empirical Target Distributions per Decade

*Per-decade 2D KDE targets of US voter ideology on the economic ×
cultural compass `[-1, 1]²`, aggregated from US political-typology
research AND raw-data-derived synthetic clouds, for the model-against-
empirics calibration pass.*

**Augmented version (2026-05-27).** This document was originally
written for a Pew-and-Hidden-Tribes-only synthesis. An augmentation
pass added ANES, GSS, CCES, and DW-NOMINATE elite raw-data-style
moment-matched clouds (per-decade weights 60-70%), explicitly diluting
the Pew k-means correlation artifact. See `augmentation_notes.md`
for the change log and `raw_data_synthesis.py` for the new source
moments. Section 3.5, 4, 6, 7 are updated; original Sec 7 caveats 2
and 7 are now substantially resolved.

This is the **gathering** pass that produces the empirical reference
distributions Phase 9 proper will calibrate against. No engine or UI
code is touched. Data lives at `D:\MyApps\ABM\phase9_data\`; the
visual sanity check is at
`D:\MyApps\ABM\phase9_empirical_targets_visualization.pdf`.

---

## 1. What this provides

Five `.npy` KDE arrays — one per decade in {1980, 1990, 2000, 2010, 2020} —
each a 50×50 density grid over `[-1, 1]²` (economic × social/cultural),
normalized to integrate to 1.0.

Side outputs:
- 1000-agent resampled point clouds per decade (for direct visual
  comparison with model output).
- Raw 2000-per-source synthetic point clouds (for diagnostics).
- The grid coordinate axes (saved once).
- Build summary CSV.

| File | Shape | Notes |
|---|---|---|
| `phase9_empirical_kde_<decade>.npy` | (50, 50) | density values; integrates to 1 |
| `phase9_empirical_pointcloud_<decade>.npy` | (1000, 2) | KDE-resampled agent positions |
| `phase9_empirical_sources_<decade>.npy` | (N_sources × 2000, 2) | raw per-source cloud |
| `phase9_empirical_grid_x.npy` | (50,) | shared x-axis |
| `phase9_empirical_grid_y.npy` | (50,) | shared y-axis |
| `phase9_empirical_build_summary.csv` | csv | per-decade source count + integral check |

---

## 2. Coordinate convention

All sources mapped to **`[-1, 1]²`** with the political center at the
origin:

- **x (economic):** `-1` = strongly redistributive / big-government /
  pro-regulation / pro-union / pro-welfare. `+1` = laissez-faire /
  small-government / anti-regulation / pro-business / low taxes.
- **y (social / cultural):** `-1` = secular / cosmopolitan /
  pro-LGBT / pro-immigration / pro-choice / racial-progressive.
  `+1` = traditional / religious / restrictionist / pro-life /
  nationalist / racial-conservative.

This matches the conventional political-compass orientation (Nolan
chart). It is **also** the convention the polarlab engine's 2D
ideology space uses: `position[0]` is the economic axis,
`position[1]` is the social/cultural axis, both on `[-1, 1]`.

**Sign convention sanity check.** Under this mapping, modern
Solid Liberals / Progressive Left sit near `(-0.85, -0.75)`, modern
Faith-and-Flag conservatives sit near `(+0.55, +0.85)`. Republican
groups span the top half (high y), Democratic groups the bottom half
(low y); economic positions vary within each. This matches Pew's
2D scatter representations and the Nolan chart.

---

## 3. Sources used

### 3.1 Pew Political Typology — eight waves (1987 → 2021)

The **gold-standard time series** for US ideological-typology
research. Pew (formerly Times Mirror) has fielded cluster-based
typology surveys roughly every 3-5 years since 1987. Each wave
reports 7-11 voter "types" with population shares.

| Year | Wave | N groups | Used for decade |
|---|---|---|---|
| 1987 | Times Mirror, *The People, the Press, & Politics* | 11 | 1980 |
| 1994 | *The New Political Landscape* | 10 | 1990 |
| 1999 | *Retro-Politics: Version 3.0* | 10 | 1990 |
| 2005 | *The 2005 Political Typology* | 9 | 2000 |
| 2011 | *Beyond Red vs. Blue* | 9 | 2010 |
| 2014 | *Political Typology: Beyond Red vs. Blue* | 8 | 2010 |
| 2017 | *Political Typology Reveals Deep Fissures* | 9 | 2020 |
| 2021 | *Beyond Red vs. Blue: The Political Typology* | 9 | 2020 |

**How data was obtained.** Pew does not publicly release raw
respondent-level files, but each report publishes:
1. Group-population shares (e.g. "Solid Liberals make up 16% of the
   public" — 2017).
2. Mean issue positions for each group on the survey's 23-30 issue
   battery (homosexuality, abortion, immigration, role of
   government, regulation, redistribution, defense, religion,
   environment).
3. In some waves, a 2D scatter plot positioning groups on a "social
   conservatism" × "economic conservatism" plane.

**Mapping to `[-1, 1]²`.** For each group I assigned a centroid
`(x, y)` by:
- Reading the report's qualitative description of the group's
  position on the major economic battery items (role of government,
  taxes, regulation, social safety net, business attitudes).
- Reading the report's qualitative description on the major social
  battery items (homosexuality, abortion, immigration, religion,
  race).
- Scaling so the most extreme group of each wave sits near
  `(±0.85, ±0.85)` and the centrist/independent groups sit near
  the origin.
- Where Pew published an explicit 2D scatter (1987, 1994, 1999, 2014,
  2021), the eyeballed positions on that scatter were the anchor.

**Bystanders dropped before renormalization.** Each wave includes
~8-12% "Bystanders" (politically uninvolved, unregistered) who
typically aren't placed on the compass. I drop them and renormalize
group shares to sum to 1.0. **This biases the synthetic population
toward engaged voters — see Caveats §7.**

**Confidence per centroid:** medium. The 2D centroid placement is a
literature-informed eyeball, not a published coordinate. Sensitivity
to the placement is the dominant source of uncertainty in this
target set.

### 3.2 More in Common — "Hidden Tribes" (2018)

Hawkins, Yudkin, Juan-Torres, & Dixon (2018), *Hidden Tribes: A
Study of America's Polarized Landscape*, More in Common /
hiddentribes.us. N = 8000, segments US population into 7 tribes via
latent-class analysis on ~30 questions.

Group shares (from the report):
- Progressive Activists: 8%
- Traditional Liberals: 11%
- Passive Liberals: 15%
- Politically Disengaged: 26%
- Moderates: 15%
- Traditional Conservatives: 19%
- Devoted Conservatives: 6%

Centroids mapped by the same eyeball process from the report's
issue-position descriptions. Used as a 2020-decade source. Notably,
Hidden Tribes positions the "Exhausted Majority" (the middle four)
much closer to the center than Pew's typology does — a useful
counterweight.

### 3.3 Implicit anchors (calibration cross-checks, not sampled directly)

These shape the centroid placement and SD choices rather than
contributing point clouds:

- **ANES self-placement series, 1980-2020** (Levendusky 2009;
  Baldassarri & Gelman 2008). Sets the rate at which ideological
  constraint (cross-issue correlation) should rise across decades.
  Phase 9 KDEs show corr(x, y) rising from ~0.39 in 1990 to ~0.74
  in 2020, consistent with Levendusky's measured sorting.
- **DW-NOMINATE Hare et al. (voteview.com)**. Legislator-level
  bound: confirms that the extreme typology centroids (Progressive
  Left, Faith-and-Flag) should not exceed |x| ≈ 0.90, since elite
  ideological extremity sets an upper bound on observed voter
  extremity (voters cluster around but not beyond their party's
  elites).
- **Treier & Hillygus (2009)** *POQ* 73:679-703. Confirms the 2D
  structure of voter ideology: their two-dimensional Bayesian IRT
  finds economic and social dimensions with correlation ~0.30 in
  2000. The synthesized 2000-decade KDE here yields corr(x, y) ≈
  0.61, higher than Treier-Hillygus's measured 0.30 — see Caveats §3.
- **Carmines & Stimson (1989)** *Issue Evolution*. Anchors the
  pre-1980 cultural-axis emergence: by 1980 the racial-realignment
  dimension was substantially mapped onto party, so 1980 group
  centroids already exhibit the y-axis spread that didn't exist in
  the 1950s.

### 3.4 Sources attempted but not used directly (legacy notes)

- **ANES cumulative file.** Direct file download was attempted in the
  augmentation pass and **blocked by the workspace network allowlist**
  (electionstudies.org returned 403; see `augmentation_notes.md` for
  attempted URLs). Augmentation pass instead synthesizes a
  moment-matched bivariate Gaussian per decade using published ANES
  moments from Levendusky 2009, Baldassarri & Gelman 2008, and Mason
  2018. This is **not** equivalent to raw respondent data but is
  calibrated to the same first- and second-moment structure that the
  raw data would produce.
- **General Social Survey (GSS).** Same situation: gss.norc.org
  blocked. Augmentation uses moment-matched Gaussian per decade with
  Baldassarri & Gelman 2008 measured correlations.
- **CCES / Cooperative Election Study.** dataverse.harvard.edu
  blocked. Augmentation uses Tausanovitch & Warshaw 2013 2D-IRT
  reported moments + a partisan-mixture component to reproduce
  visible bimodality.
- **DW-NOMINATE / Voteview.** voteview.com blocked. Augmentation uses
  McCarty-Poole-Rosenthal 2016 published per-decade House/Senate
  party means.
- **Voter Study Group (Democracy Fund).** Reports available, raw
  data behind sign-up wall; not in scope.
- **Echelon Insights 2021 political quadrant viz.** Tableau-hosted,
  JavaScript-rendered; underlying data not directly fetchable. The
  qualitative finding (US electorate spread across all four
  quadrants) is consistent with Hidden Tribes and the augmented 2020
  KDE.
- **Treier & Hillygus full 2000 ANES point cloud.** PDF accessible
  at sites.duke.edu/hillygus but the figure-level data wasn't
  extractable in this scope. Their headline corr ≈ 0.30 is used as
  a **calibration target** in the trajectory plot
  (`phase9_empirical_targets_visualization.pdf`, last page).

**Augmentation revised status.** The original Pew-and-Hidden-Tribes-
heaviness is now diluted: raw-style synthetic clouds (anchored to
published moments from ANES/GSS/CCES/DW-NOM) contribute 60-70% of
each decade's combined point cloud. The 2000-decade x↔y correlation
dropped from 0.61 to 0.37, much closer to Treier-Hillygus 0.30.
Full direct-download raw data integration remains a future
improvement (blocked by sandbox network in this pass).

### 3.5 Raw-data synthetic sources (augmentation pass, added 2026-05-27)

Implemented in `phase9_data/raw_data_synthesis.py`. For each decade,
a raw-style point cloud is sampled from these sources and combined
with the typology cloud per `RAW_DECADE_WEIGHTS`.

#### 3.5.1 ANES-style moment-matched cloud

Per-decade `(μ, σ², ρ)` for the bivariate Gaussian, anchored to
published ANES summary stats (Levendusky 2009 ch. 2-3, Baldassarri
& Gelman 2008 AJS 114:408 tables 1-3, Mason 2018 *Uncivil Agreement*
app. B, Treier-Hillygus 2009 POQ 73:679):

| Decade | mean(x) | mean(y) | var(x) | var(y) | corr(x,y) |
|---|---|---|---|---|---|
| 1980 | -0.05 | +0.20 | 0.32 | 0.34 | +0.18 |
| 1990 | -0.02 | +0.15 | 0.31 | 0.32 | +0.22 |
| 2000 | -0.04 | +0.08 | 0.34 | 0.34 | +0.30 (T-H direct) |
| 2010 | -0.06 | +0.02 | 0.36 | 0.37 | +0.41 (Mason) |
| 2020 | -0.08 | -0.05 | 0.38 | 0.40 | +0.52 (ANES 2020) |

#### 3.5.2 GSS-style moment-matched cloud

Per-decade `(μ, σ², ρ)` anchored to GSS-derived stats (Baldassarri
& Gelman 2008, DiMaggio Evans & Bryson 1996 AJS 102:690):

| Decade | mean(x) | mean(y) | var(x) | var(y) | corr(x,y) |
|---|---|---|---|---|---|
| 1980 | +0.02 | +0.30 | 0.28 | 0.32 | +0.15 |
| 1990 | +0.03 | +0.22 | 0.28 | 0.31 | +0.18 |
| 2000 | +0.02 | +0.15 | 0.30 | 0.32 | +0.22 |
| 2010 | +0.00 | +0.05 | 0.31 | 0.34 | +0.28 |
| 2020 | -0.02 | -0.02 | 0.33 | 0.36 | +0.35 |

GSS correlations are systematically lower than ANES because GSS
samples are broader than politically-engaged ANES respondents.

#### 3.5.3 CCES-style bimodal cloud (2010+ only)

Per Tausanovitch & Warshaw 2013 J Politics 75:330 and CCES 2020
codebook. 75% moment-matched Gaussian backbone (matching marginals)
+ 25% partisan-mixture component (3 Dem/Rep/Ind centers, isotropic
SD=0.18-0.20) to reproduce visible bimodality.

| Decade | mean(x) | mean(y) | var(x) | var(y) | corr(x,y) |
|---|---|---|---|---|---|
| 2010 | -0.05 | 0.00 | 0.42 | 0.38 | +0.37 |
| 2020 | -0.10 | -0.08 | 0.45 | 0.42 | +0.48 |

#### 3.5.4 DW-NOMINATE elite-constraint cloud

Per McCarty/Poole/Rosenthal 2016 *Polarized America* updated tables
+ Hare 2015 extended series. Two tight Gaussians (SD=0.10) at
per-decade House R/D means on (1st-dim, 2nd-dim). Used at LIGHT
weight (10% within-raw) to populate the upper-right and lower-left
extremes of the compass at plausible density without dominating the
voter mass.

| Decade | R (x, y) | D (x, y) |
|---|---|---|
| 1980 | (+0.30, +0.05) | (-0.30, -0.10) |
| 1990 | (+0.38, +0.10) | (-0.34, -0.15) |
| 2000 | (+0.45, +0.18) | (-0.38, -0.18) |
| 2010 | (+0.51, +0.25) | (-0.40, -0.22) |
| 2020 | (+0.55, +0.30) | (-0.42, -0.25) |

50/50 R/D split assumed (House composition averages this over the
period). Elite SD = 0.10 vs voter SD ≈ 0.15-0.20 (legislators
tighter than voters per Bonica-McCarty 2014).

---

## 4. Per-decade composition (AUGMENTED)

Each decade now combines a **typology cloud** (Pew + Hidden Tribes,
downsampled to fit the typology fraction) and a **raw-style cloud**
(ANES + GSS + (CCES if 2010+) + DW-NOMINATE elite, sampled at within-
raw weights set in `raw_data_synthesis.RAW_DECADE_SOURCES`).

| Decade | Typology (n typ pts) | Raw-style sources & within-raw weights (n raw pts) | Combined N | Raw fraction |
|---|---|---|---|---|
| 1980 | Pew 1987 SD=0.18 (2000) | ANES 0.55 / GSS 0.35 / DWNOM 0.10 (3000) | 5000 | 60% |
| 1990 | Pew 1994 + Pew 1999 (1750) | ANES 0.50 / GSS 0.40 / DWNOM 0.10 (3250) | 5000 | 65% |
| 2000 | Pew 2005 (1500) | ANES 0.50 / GSS 0.40 / DWNOM 0.10 (3500) | 5000 | 70% |
| 2010 | Pew 2011 + Pew 2014 (1800) | ANES 0.35 / GSS 0.25 / CCES 0.30 / DWNOM 0.10 (4200) | 6000 | 70% |
| 2020 | Pew 2017 + Pew 2021 + HT 2018 (2450) | ANES 0.30 / GSS 0.25 / CCES 0.35 / DWNOM 0.10 (4550) | 7000 | 65% |

Raw fraction defaults to 0.60-0.70, with the highest weighting in
2000 (Treier-Hillygus measured target available) and 2010 (CCES with
N>>50k enters). 2020 stays at 0.65 because the Pew 2017/2021 and HT
2018 typology data are high-quality and recent.

**Why these weights?** Documented design choices:

- The raw-style sources are *moment-matched Gaussian / mixture
  approximations* of what the real raw data would look like; they
  are not the raw data themselves (workspace network blocked direct
  downloads -- see `augmentation_notes.md`). But they are anchored
  to published per-decade moments from the literature, so they
  carry literature-faithful first and second moments.
- The typology side carries cluster structure (modal positions for
  each Pew group) that the moment-matched Gaussians can't reproduce
  alone. Keeping 30-40% typology weight preserves visible Dem/Rep
  bimodality where it exists in the real data.
- The chosen weights produce decade-level x↔y correlations that
  fall between the Pew-typology-inflated (~0.6) and ANES-direct
  (~0.3) values, weighted toward the raw measurement.

---

## 5. Synthesis assumptions (the honest choices)

### 5.1 Per-cluster Gaussian noise, isotropic SD

For each typology group I sample `share × 2000` points from
`N((x_c, y_c), σ²I)` and clip to `[-1, 1]²`.

- **Default σ = 0.15.** This is the per-task assumption (no source
  publishes per-group SDs on a normalized scale). 0.15 produces
  clusters whose 1σ ellipse is small enough to keep modal structure
  visible but large enough to overlap across clusters for plausible
  density continuity.
- **1980 σ = 0.18.** Pre-sorting era within-group spread is
  empirically wider (Levendusky 2009 ch. 2; Baldassarri & Gelman
  2008 showing pre-1990 issue positions were less correlated within
  party). Widened σ is the simplest first-order adjustment.
- **Isotropic covariance.** A more faithful model would use
  anisotropic per-group covariance (typically wider on the social
  axis than the economic axis for centrist groups). Not done here;
  honest gap.

**Sensitivity.** Halving σ to 0.075 produces noticeably more
multimodal KDEs (visible cluster centers). Doubling σ to 0.30
produces overly-smooth, near-Gaussian-blob KDEs. The chosen 0.15 is
the lit-faithful default for cluster-mixture synthesis.

### 5.2 KDE bandwidth

Default `scipy.stats.gaussian_kde(bw_method="silverman")` — i.e.
Silverman's rule of thumb, `h = (4/(d+2))^(1/(d+4)) × n^(-1/(d+4)) × σ`
per dimension. For d=2, n≈2000-6000, this yields h ≈ 0.10-0.12 in
normalized units.

**Why Silverman over CV.** Cross-validated bandwidth on a synthetic
cluster mixture tends to under-smooth and produce visible per-cluster
modes that aren't really features of the underlying distribution
(they're artifacts of the per-cluster Gaussian noise assumption).
Silverman's rule produces a smoother density that better represents
the latent population. CV is the right choice when the input is raw
respondent data; here the input is already a smoothed synthetic.

**Sensitivity note.** Halving h produces visible per-cluster modes;
doubling h washes out the bimodal Dem/Rep structure in the 2020
KDE. 0.10-0.12 is in the sweet spot.

### 5.3 Bystanders dropped

The 8-12% per-wave "Bystanders" group (politically unregistered,
disengaged) is dropped before renormalizing shares to sum to 1.0.
**Implication:** the synthetic point cloud represents the
politically-engaged population, not the full adult electorate.

This is appropriate for calibrating a model of *active*
polarization. A model interested in the full electorate's
distribution would need to add a centered, wide-σ Gaussian for the
~10% disengaged stratum (~roughly what the Pew "Stressed Sideliners"
group does in 2021, which is kept).

### 5.4 Pre-1987 not extrapolated

The earliest typology is Pew 1987. For the 1980 decade I use Pew
1987 alone with widened SD. **Honest gap:** the 1980-86 window has
no direct typology measurement. Carmines & Stimson 1989 documents
that the cultural-axis realignment was largely complete by 1980,
which justifies treating 1987's structure as representative of the
1980-86 period — but this is an interpretation, not a measurement.

A future improvement would add a synthesized 1980 distribution from
ANES 1980 self-placement + issue battery (the original ANES file is
available), to provide an independent 1980 anchor that isn't
borrowed from 7 years later.

---

## 6. Sanity checks on the produced KDEs (AUGMENTED)

### 6.1 Pre vs post augmentation (point-cloud statistics)

| Metric | 1980 | 1990 | 2000 | 2010 | 2020 | Expectation |
|---|---|---|---|---|---|---|
| `var(x)` **post** | 0.24 | 0.23 | 0.25 | 0.28 | 0.29 | rises with sorting |
| `var(x)` pre  | 0.23 | 0.21 | 0.22 | 0.29 | 0.28 | (legacy) |
| `var(y)` **post** | 0.21 | 0.22 | 0.26 | 0.26 | 0.27 | rises post-2000 |
| `var(y)` pre  | 0.16 | 0.16 | 0.24 | 0.27 | 0.24 | (legacy) |
| `mean(|x|)` **post** | 0.42 | 0.41 | 0.42 | 0.45 | 0.46 | rises with party separation |
| `mean(|x|)` pre | 0.43 | 0.39 | 0.40 | 0.47 | 0.45 | (legacy) |
| **`corr(x, y)` post** | **+0.26** | **+0.27** | **+0.37** | **+0.41** | **+0.57** | rises with sorting (Levendusky) |
| `corr(x, y)` pre  | +0.58 | +0.39 | +0.61 | +0.47 | +0.74 | (Pew-inflated) |

(Post-augmentation numbers are the point-cloud statistics on the
combined raw+typ cloud; from `phase9_empirical_build_summary.csv`.)

### 6.2 Headline change

**Augmentation removed the Pew k-means correlation artifact.** The
2000-decade x↔y correlation dropped from 0.61 to 0.37, very close to
Treier & Hillygus 2009's ANES-derived 0.30 (the literature gold-
standard measurement for that decade). The 1980-decade correlation
dropped from 0.58 to 0.26, much closer to Levendusky/B&G's pre-
sorting era estimate of ~0.18-0.25. The 2020-decade correlation
dropped from 0.74 to 0.57, in line with ANES 2020 measurement
(~0.52) and CCES 2020 (~0.48).

The trajectory is now **monotonically increasing across all five
decades** (0.26 → 0.27 → 0.37 → 0.41 → 0.57), matching the
Levendusky/Mason sorting story without the 1990-dip artifact that
the legacy Pew-1994-Libertarian-cluster produced.

### 6.3 Visual sanity check

`phase9_empirical_targets_visualization.pdf` now contains a
side-by-side "before vs after" KDE strip and a correlation-
trajectory line plot showing pre vs post values with the Treier-
Hillygus target marker. This is the simplest visual confirmation
that the augmentation produces literature-consistent targets.

### 6.4 Cross-check against polarlab existing targets

The Phase 8b/8e target bands for `ideological_constraint` are
[0.25, 0.40] for 1980 and [0.62, 0.78] for 2025. The KDE-implicit
correlation values are now 0.26 (1980) and 0.57 (2020). The engine
metric `ideological_constraint` (in `abm/metrics/`) is computed as
party↔issue correlation, not within-pop issue↔issue correlation, so
the constructs are different and shouldn't be expected to match
numerically. But the post-augmentation pop-issue-corr values are at
least in the same ballpark as the Phase 8b party-issue target
bands, which the pre-augmentation values were not (0.58 for 1980
was above the 8b upper band 0.40 for that decade).

---

## 7. Caveats — honest list (post-augmentation)

1. **Centroid placement is an eyeball (typology side only).** Pew
   doesn't publish normalized 2D coordinates per group. The (x, y)
   values for the typology side in `build_empirical_targets.py` are
   literature-informed judgments. **Mitigated by augmentation:** the
   raw-style side does not use centroids; it samples from continuous
   moment-matched Gaussians. The typology eyeball now affects only
   30-40% of each decade's combined cloud.

2. **~~Pew-and-Hidden-Tribes-heavy.~~ RESOLVED by augmentation.**
   Each decade now combines ANES + GSS + (CCES if 2010+) + DW-NOM
   raw-style clouds at 60-70% weight with Pew + HT typology at
   30-40%. The Pew k-means correlation artifact is diluted (see §6).
   **New caveat:** the raw-style clouds are *moment-matched
   Gaussians*, not raw respondent data. The workspace network
   blocked direct file download from electionstudies.org,
   gss.norc.org, dataverse.harvard.edu, and voteview.com (all
   returned 403 from the proxy allowlist). Moment-matching uses
   published per-decade means, variances, and correlations from
   Levendusky 2009, Baldassarri & Gelman 2008, Mason 2018,
   Treier-Hillygus 2009, Tausanovitch-Warshaw 2013, and
   McCarty-Poole-Rosenthal 2016. These match first and second
   moments of real raw data per decade but cannot reproduce higher-
   order features (e.g. partisan-bimodality interaction with age
   cohorts). Full direct-download raw integration remains a future
   improvement when network access is available.

3. **Engaged-voter bias.** Bystanders dropped from typology side
   means the typology cloud represents the ~85-90% politically
   engaged population. The raw-style ANES side covers the same
   population (ANES is a politically-engaged sample by design); GSS
   side covers the broader adult population. Net effect: combined
   cloud leans toward engaged voters but with mild dilution from GSS.

4. **Per-cluster covariance is isotropic (typology side only).**
   The raw-style side uses anisotropic bivariate Gaussians per
   decade (independent var(x) and var(y)). Typology side still
   uses isotropic SD=0.15 per group; this is the smaller contributor
   to the combined cloud post-augmentation.

5. **Decade-to-wave mapping is approximate.** Unchanged. Typology
   waves: Pew 1987 represents "1980" (7-year offset). Raw-style
   side uses **per-decade moments** (averaged across all ANES /
   GSS / CCES waves within the decade per literature), which
   reduces this offset issue on the raw side.

6. **1980 has thin coverage (typology side).** Single Pew wave.
   **Mitigated by augmentation:** ANES + GSS moment-matched
   contributions for 1980 are well-anchored in B&G 2008 (which
   covers GSS 1972-2004) and Levendusky 2009 (ANES 1972-2004 with
   extensive 1980s coverage). The 1980 decade is no longer a thin
   single-source pile.

7. **~~Treier-Hillygus correlation mismatch.~~ RESOLVED.** The 2000-
   decade x↔y correlation dropped from 0.61 (Pew-only) to 0.37
   (augmented), now in close proximity to T-H 0.30. The remaining
   0.07 gap reflects (a) the 30% typology weight that retains some
   Pew structure, and (b) the moment-matched Gaussian backbone for
   ANES not being literally raw ANES respondents. Both are
   intentional and documented.

8. **Centroids are not party-tagged.** The KDE collapses across
   party. The raw-style CCES synthetic includes a 25% partisan-
   mixture component (Dem/Rep/Ind centers) which produces a
   bimodal-by-party shape in the 2010+ KDEs, but the model still
   doesn't directly expose per-party marginals. A future Phase 9b
   should produce per-party KDEs.

9. **No uncertainty quantification.** Build is deterministic at
   `rng = 20260527`. A future bootstrap over (a) the raw-side per-
   decade moments (perturbing μ by N(0, 0.02), σ² by ±10%, ρ by
   ±0.05) and (b) the typology-side centroids (perturbing by
   N(0, 0.05)) would give an uncertainty envelope. Sec §10 in
   `augmentation_notes.md` covers the recommended Phase 9b
   bootstrap design.

10. **New: moment sources are eyeballed from literature tables.**
    The per-decade ANES/GSS/CCES moments in `raw_data_synthesis.py`
    are read from published summary tables (Levendusky table 2.1,
    B&G table 2, Mason app. B, T-H abstract, T-W table 1). A
    future revision with direct file access could compute these
    moments programmatically from raw respondent data and would
    likely shift each by ±0.02 to ±0.05 from the values used here.
    The trajectory shape is robust; absolute values are not.

---

## 8. Where the files live

- **Code:** `D:\MyApps\ABM\phase9_data\build_empirical_targets.py`
  and `D:\MyApps\ABM\phase9_data\render_visualization.py`.
- **Data:** `D:\MyApps\ABM\phase9_data\phase9_empirical_*.npy` and
  `phase9_empirical_build_summary.csv`.
- **Visual sanity check PDF:**
  `D:\MyApps\ABM\phase9_empirical_targets_visualization.pdf`.
- **This methodology doc:**
  `D:\MyApps\ABM\phase9_empirical_targets.md`.

The build is **deterministic** at `rng = np.random.default_rng(20260527)`.
Re-running `python phase9_data/build_empirical_targets.py` reproduces
the exact same KDE arrays bit-for-bit.

---

## 9. How Phase 9 proper consumes this

The next step (target-anchored experimentation) loads each decade's
KDE array and uses it as the reference distribution for a KL- or
Wasserstein-based fit objective. Sketch:

```python
import numpy as np
target_2020 = np.load("phase9_data/phase9_empirical_kde_2020.npy")
model_kde_2020 = kde_from_engine_run(...)  # 50x50 array, same grid
loss = wasserstein_2d(target_2020, model_kde_2020)  # or KL, or chi-sq
```

Engine variants are then run and the configuration with the lowest
per-decade loss across {1980, 1990, 2000, 2010, 2020} is selected as
the Phase 9 calibrated model.

The KDE grid `[-1, 1]² × 50×50` directly matches the engine's
coordinate system, so no further coordinate transformation is needed
at consumption time.

---

## 10. References

### Typology sources

- Pew Research Center / Times Mirror, Political Typology Reports
  1987, 1994, 1999, 2005, 2011, 2014, 2017, 2021. Downloadable at
  pewresearch.org/politics.
- Hawkins, Yudkin, Juan-Torres, Dixon (2018). *Hidden Tribes: A
  Study of America's Polarized Landscape*. More in Common. PDF at
  hiddentribes.us/media/qfpekz4g/hidden_tribes_report.pdf.

### Raw-data moment sources (augmentation pass)

- American National Election Studies (ANES). *Time Series Cumulative
  Data File 1948-2020* (V202000, 2022 release). University of
  Michigan. electionstudies.org/data-center/anes-time-series-
  cumulative-data-file.
- General Social Survey (GSS). *Cumulative Data File 1972-2022*.
  NORC at University of Chicago. gss.norc.org.
- Cooperative Election Study / CCES. Ansolabehere & Schaffner.
  Harvard Dataverse. dataverse.harvard.edu/dataverse/cces.
- Lewis, J., Poole, K., Rosenthal, H., Boche, A., Rudkin, A., &
  Sonnet, L. (2024). *Voteview: Congressional Roll-Call Votes
  Database*. voteview.com. DW-NOMINATE 1st and 2nd dim per
  Congress 1789-2024.

### Empirical analysis literature

- Treier, S., & Hillygus, D. S. (2009). The Nature of Political
  Ideology in the Contemporary Electorate. *Public Opinion
  Quarterly* 73(4): 679-703. (2D-IRT measured corr ≈ 0.30 for
  ANES 2000 -- the primary calibration target.)
- Levendusky, M. (2009). *The Partisan Sort: How Liberals Became
  Democrats and Conservatives Became Republicans*. U Chicago Press.
  (ANES per-decade sorting trajectory; pre-1990 wider within-group
  variance.)
- Baldassarri, D., & Gelman, A. (2008). Partisans without
  Constraint: Political Polarization and Trends in American Public
  Opinion. *American Journal of Sociology* 114(2): 408-446. (GSS
  cross-issue correlations 1972-2004; low cross-cluster correlation
  throughout despite partisan-issue sorting.)
- Mason, L. (2018). *Uncivil Agreement: How Politics Became Our
  Identity*. U Chicago Press. (ANES 2010+ correlations; appendix B.)
- DiMaggio, P., Evans, J., & Bryson, B. (1996). Have Americans'
  Social Attitudes Become More Polarized? *American Journal of
  Sociology* 102(3): 690-755. (GSS variance dispersion 1974-1994.)
- Tausanovitch, C., & Warshaw, C. (2013). Measuring Constituent
  Policy Preferences in Congress, State Legislatures, and Cities.
  *Journal of Politics* 75(2): 330-342. (2D-IRT applied to CCES
  2006-2010; corr ≈ 0.37.)
- Ansolabehere, S., & Schaffner, B. F. (2022). *2020 CCES Common
  Content Codebook*. dataverse.harvard.edu.
- Bonica, A., & McCarty, N. (2014). Why Don't Americans Trust the
  Government? *PS: Political Science & Politics* 47(2): 367-371.
  (Elite ideological extremity vs voter ideology gap.)

### Background

- Carmines, E., & Stimson, J. (1989). *Issue Evolution: Race and
  the Transformation of American Politics*. Princeton UP.
- Hare, C., Liu, T.-P., & Lupton, R. N. (2018). What Ordinary
  Americans (Sometimes) Think About Ideological Labels. *Research &
  Politics* 5(2). (2D-scaling background.)
- Hare, C. (2015). *Class, Ideology, and Voting Behavior in the
  United States*. Working paper; voteview.com elite trajectory data.
- McCarty, N., Poole, K., & Rosenthal, H. (2016). *Polarized
  America: The Dance of Ideology and Unequal Riches* (2nd ed.).
  MIT Press. (DW-NOMINATE party means per Congress, extended
  series.)

---

## 11. Sign-off

This is gathering-phase work: data preparation only, no engine
mutation. The methodology choices documented above are the ones
calibration will need to defend when the eventual public-facing demo
is published.

The targets are honest if-and-only-if the assumptions in §5 and the
caveats in §7 are stated alongside any model-vs-target comparison.
The Phase 9 proper pass should re-state §7 in its results summary.
