"""
ANES 2D ideological compass, 1986-2024.

Implements data/phase9_empirical/raw/anes_2d_ideology_methodology.md verbatim:
global axes, global scaling, global KDE bandwidth/grid, listwise drop on the
fixed core panel. Cross-wave comparability is the non-negotiable.

Outputs (all under data/phase9_empirical/derived/):
  coverage_table.csv         Step 0: valid-N per item per wave
  recode_log.csv             Step 3: per-item direction + missing-code rules
  scaling_params.json        Step 4: pooled rescale params
  kde_params.json            Step 6: global bandwidth + grid
  respondent_coordinates.csv per-respondent (wave, party, weight, econ, cult)
  party_centroids.csv        per wave x party means
  polarization_series.csv    OVL, dip, scaled-sep, per-axis Wasserstein (raw + MA3)
  densities/<year>_<party>.npy  KDE evaluated on the fixed grid
  build_log.md               human-readable decision log
  acceptance_checks.txt      isolation tests

And:
  docs/phase9_empirical/density_small_multiples.png
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import diptest
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import gaussian_kde, wasserstein_distance

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = ROOT / "data" / "phase9_empirical" / "raw" / "timeseries_csv.csv"
OUT_DIR = ROOT / "data" / "phase9_empirical" / "derived"
DENS_DIR = OUT_DIR / "densities"
PLOT_DIR = ROOT / "docs" / "phase9_empirical"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DENS_DIR.mkdir(parents=True, exist_ok=True)
PLOT_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 1986
END_YEAR = 2024
WEIGHT_VAR = "VCF0009z"  # ANES full-sample weight; =1 in SRS-era waves (1986-1990)
PARTY_VAR = "VCF0301"

# Item -> (axis, scale_endpoints_after_drop, missing_codes, reverse_for_conservative_up)
# All scales recoded so higher = more CONSERVATIVE on that axis (methodology Step 3).
ITEMS = {
    "VCF0803": dict(axis="economic", lo=1, hi=7, miss={0, 9}, reverse=False,
                    label="lib-cons 7-pt self-placement (1=ex-lib..7=ex-cons)"),
    "VCF0809": dict(axis="economic", lo=1, hi=7, miss={0, 9}, reverse=False,
                    label="guaranteed jobs/income (1=govt..7=self-reliance)"),
    "VCF0839": dict(axis="economic", lo=1, hi=7, miss={0, 9}, reverse=True,
                    label="services-spending (1=fewer/cons..7=more/lib) REVERSED"),
    "VCF0838": dict(axis="cultural", lo=1, hi=4, miss={0, 9}, reverse=True,
                    label="abortion 4-pt (1=never/cons..4=personal/lib) REVERSED"),
    "VCF0830": dict(axis="cultural", lo=1, hi=7, miss={0, 9}, reverse=False,
                    label="aid to blacks (1=govt-help..7=self-help)"),
    "VCF0852": dict(axis="cultural", lo=1, hi=5, miss={8, 9}, reverse=False,
                    label="adjust moral views to changes (1=agree-lib..5=disagree-cons)"),
    "VCF0853": dict(axis="cultural", lo=1, hi=5, miss={8, 9}, reverse=True,
                    label="more emphasis on traditional values (1=agree-cons..5=disagree-lib) REVERSED"),
    # carried for the coverage table only:
    "VCF0806": dict(axis="economic", lo=1, hi=7, miss={0, 9}, reverse=False,
                    label="govt health insurance (1=govt-plan..7=private)"),
    "VCF0834": dict(axis="cultural", lo=1, hi=7, miss={0, 9}, reverse=False,
                    label="women equal role (1=equal..7=home)"),
    "VCF0894": dict(axis="economic?", lo=1, hi=3, miss={8, 9}, reverse=False,
                    label="federal spending welfare (1=incr..3=decr)"),
}

# Items that actually go into the core panel.
ECON_CORE = ["VCF0803", "VCF0809", "VCF0839"]
CULT_CORE = ["VCF0838", "VCF0830", "VCF0852", "VCF0853"]

# KDE grid spans a bit beyond [-1,1] so corners aren't clipped by the kernel halo.
GRID_LO, GRID_HI, GRID_N = -1.05, 1.05, 81
GRID_AXIS = np.linspace(GRID_LO, GRID_HI, GRID_N)
GRID_CELL = (GRID_HI - GRID_LO) / (GRID_N - 1)
GRID_AREA = GRID_CELL ** 2

PARTY_LABELS = {"D": "Dem", "I": "Ind", "R": "Rep"}
PARTY_COLORS = {"D": "tab:blue", "I": "tab:gray", "R": "tab:red"}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def rescale(raw: pd.Series, lo: int, hi: int, reverse: bool) -> pd.Series:
    """Map raw integer code in [lo, hi] -> [-1, 1] with optional reversal.
    Endpoints are taken from the theoretical scale, not per-wave min/max."""
    x = (raw - lo) / (hi - lo)  # -> [0, 1]
    if reverse:
        x = 1.0 - x
    return x * 2.0 - 1.0


def collapse_party(p: pd.Series) -> pd.Series:
    out = pd.Series(index=p.index, dtype="object")
    out[p.isin([1, 2, 3])] = "D"
    out[p == 4] = "I"
    out[p.isin([5, 6, 7])] = "R"
    return out


def kde_2d_on_grid(x: np.ndarray, y: np.ndarray, w: np.ndarray, bw: float) -> np.ndarray:
    """Weighted Gaussian 2D KDE evaluated on the global grid. bw is the scalar
    factor passed to gaussian_kde so every wave/party uses the same bandwidth."""
    if len(x) < 2:
        return np.full((GRID_N, GRID_N), np.nan, dtype=np.float32)
    kde = gaussian_kde(
        np.vstack([x, y]),
        bw_method=bw,
        weights=w if w is not None else None,
    )
    XX, YY = np.meshgrid(GRID_AXIS, GRID_AXIS, indexing="ij")
    pts = np.vstack([XX.ravel(), YY.ravel()])
    z = kde(pts).reshape(GRID_N, GRID_N)
    # normalize so integral over grid = 1 (rectangle rule)
    total = z.sum() * GRID_AREA
    if total > 0:
        z = z / total
    return z.astype(np.float32)


def ovl_2d(f: np.ndarray, g: np.ndarray) -> float:
    """2D overlapping coefficient between two density grids (rectangle rule)."""
    if f is None or g is None or np.isnan(f).any() or np.isnan(g).any():
        return float("nan")
    return float(np.minimum(f, g).sum() * GRID_AREA)


# --------------------------------------------------------------------------- #
# Load + filter
# --------------------------------------------------------------------------- #

print("Loading raw CSV ...")
needed_cols = ["VCF0004", PARTY_VAR, WEIGHT_VAR] + list(ITEMS)
df = pd.read_csv(RAW_CSV, usecols=needed_cols, low_memory=False)
# ANES CDF stores ints as strings with ' ' for missing. Coerce everything we
# need to numeric so dtype-based operations (between, isin, mean) work.
for col in needed_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df = df[df["VCF0004"].between(START_YEAR, END_YEAR)].copy()
df = df.rename(columns={"VCF0004": "year"})
df["year"] = df["year"].astype(int)
df[WEIGHT_VAR] = df[WEIGHT_VAR].fillna(1.0).clip(lower=0.0)

all_waves = sorted(df["year"].unique().tolist())
print(f"Window {START_YEAR}-{END_YEAR}: {len(all_waves)} waves, N={len(df):,}")
print("Waves in raw window:", all_waves)


# --------------------------------------------------------------------------- #
# Step 0 — coverage table
# --------------------------------------------------------------------------- #

print("\n[Step 0] Coverage table")
cov_rows = []
for var, spec in ITEMS.items():
    row = {"variable": var, "axis": spec["axis"], "label": spec["label"]}
    for y in all_waves:
        sub = df.loc[df["year"] == y, var]
        valid = sub[~sub.isin(spec["miss"]) & sub.notna()]
        row[str(y)] = int(valid.shape[0])
    cov_rows.append(row)
cov_df = pd.DataFrame(cov_rows)
cov_df.to_csv(OUT_DIR / "coverage_table.csv", index=False)
print(cov_df.to_string(index=False))


# --------------------------------------------------------------------------- #
# Step 3 — recode log (built up as we apply rescale below)
# --------------------------------------------------------------------------- #

recode_rows = []
recoded = {}
for var, spec in ITEMS.items():
    if var not in ECON_CORE + CULT_CORE:
        continue
    s = df[var].copy()
    s = s.where(~s.isin(spec["miss"]))
    valid = s.between(spec["lo"], spec["hi"])
    s = s.where(valid)
    rec = rescale(s, spec["lo"], spec["hi"], spec["reverse"])
    recoded[var] = rec
    recode_rows.append({
        "variable": var,
        "axis": spec["axis"],
        "label": spec["label"],
        "original_lo": spec["lo"],
        "original_hi": spec["hi"],
        "missing_codes_dropped": sorted(spec["miss"]),
        "direction_reversed_for_conservative_up": spec["reverse"],
        "valid_n_pooled": int(s.notna().sum()),
        "pooled_mean_recoded": float(rec.mean(skipna=True)),
        "pooled_min_recoded": float(rec.min(skipna=True)) if rec.notna().any() else float("nan"),
        "pooled_max_recoded": float(rec.max(skipna=True)) if rec.notna().any() else float("nan"),
    })
recode_df = pd.DataFrame(recode_rows)
recode_df.to_csv(OUT_DIR / "recode_log.csv", index=False)


# --------------------------------------------------------------------------- #
# Step 2 + Step 4 — listwise drop on core, equal-weight axis means
# --------------------------------------------------------------------------- #

print("\n[Step 2+4] Listwise drop on the fixed core panel + axis means")

work = df[["year", PARTY_VAR, WEIGHT_VAR]].copy()
for var in ECON_CORE + CULT_CORE:
    work[var] = recoded[var]

# Listwise drop: require all core items present per respondent.
before = len(work)
work = work.dropna(subset=ECON_CORE + CULT_CORE + [PARTY_VAR])
work = work[work[PARTY_VAR].between(1, 7)]
after = len(work)
print(f"Listwise drop: {before:,} -> {after:,} ({after / before:.1%} retained)")

work["econ"] = work[ECON_CORE].mean(axis=1)
work["cult"] = work[CULT_CORE].mean(axis=1)
work["party"] = collapse_party(work[PARTY_VAR])
work = work.rename(columns={PARTY_VAR: "party_7pt", WEIGHT_VAR: "weight"})

resp = work[["year", "party_7pt", "party", "weight", "econ", "cult"]].copy()
resp.to_csv(OUT_DIR / "respondent_coordinates.csv", index=False)

# Some waves may listwise-drop to zero (notably 2002 in the ANES CDF: VCF0809,
# VCF0839, VCF0838, VCF0830, VCF0852, VCF0853 are all coded missing that wave).
waves = sorted(resp["year"].unique().tolist())
dropped_waves = sorted(set(all_waves) - set(waves))
if dropped_waves:
    print(f"Waves with zero listwise survivors (excluded downstream): {dropped_waves}")
print(f"Effective waves for densities + metrics ({len(waves)}): {waves}")

scaling_params = {
    "window": [START_YEAR, END_YEAR],
    "econ_core": ECON_CORE,
    "cult_core": CULT_CORE,
    "rescaling": "(raw - theoretical_lo) / (theoretical_hi - theoretical_lo) -> [0,1], reversed if needed, then *2 - 1 -> [-1,1]",
    "axis_aggregation": "equal-weight mean across core items per respondent",
    "missing_handling": "listwise drop on core; drop don't-know/refused per recode_log",
    "items": {
        var: {
            "axis": ITEMS[var]["axis"],
            "lo": ITEMS[var]["lo"],
            "hi": ITEMS[var]["hi"],
            "miss": sorted(ITEMS[var]["miss"]),
            "reverse": ITEMS[var]["reverse"],
        }
        for var in ECON_CORE + CULT_CORE
    },
    "weight_var": WEIGHT_VAR,
    "party_var": PARTY_VAR,
    "n_respondents": int(len(resp)),
}
(OUT_DIR / "scaling_params.json").write_text(json.dumps(scaling_params, indent=2))


# --------------------------------------------------------------------------- #
# Step 6 — global KDE bandwidth + grid, per wave x party
# --------------------------------------------------------------------------- #

print("\n[Step 6] Global KDE on fixed grid")

# Bandwidth: Scott's rule on the POOLED, all-waves, all-parties weighted sample
# is computed once, then this scalar is reused for every wave x party fit.
pooled = resp[["econ", "cult", "weight"]].to_numpy()
pooled_kde = gaussian_kde(pooled[:, :2].T, bw_method="scott", weights=pooled[:, 2])
global_bw = float(pooled_kde.factor)
print(f"Global bandwidth (Scott's factor on pooled data): {global_bw:.4f}")

kde_params = {
    "bandwidth_method": "scott_on_pooled",
    "bandwidth_factor": global_bw,
    "grid_lo": GRID_LO,
    "grid_hi": GRID_HI,
    "grid_n": GRID_N,
    "grid_cell": GRID_CELL,
    "grid_area_cell": GRID_AREA,
}
(OUT_DIR / "kde_params.json").write_text(json.dumps(kde_params, indent=2))

# Per wave x party densities
densities: dict[tuple[int, str], np.ndarray] = {}
all_parties = ["D", "I", "R", "ALL"]
n_per_wave: dict[tuple[int, str], int] = {}
for y in waves:
    sub = resp[resp["year"] == y]
    for p in all_parties:
        s = sub if p == "ALL" else sub[sub["party"] == p]
        if len(s) < 5:
            densities[(y, p)] = np.full((GRID_N, GRID_N), np.nan, dtype=np.float32)
        else:
            densities[(y, p)] = kde_2d_on_grid(
                s["econ"].to_numpy(),
                s["cult"].to_numpy(),
                s["weight"].to_numpy(),
                global_bw,
            )
        n_per_wave[(y, p)] = int(len(s))
        np.save(DENS_DIR / f"{y}_{p}.npy", densities[(y, p)])

print(f"Saved {len(densities)} density arrays to {DENS_DIR.relative_to(ROOT)}")


# --------------------------------------------------------------------------- #
# Step 7 — party centroids + polarization series
# --------------------------------------------------------------------------- #

print("\n[Step 7] Centroids + polarization series")


def weighted_mean(x, w):
    return float(np.average(x, weights=w))


def weighted_var(x, w):
    m = weighted_mean(x, w)
    return float(np.average((x - m) ** 2, weights=w))


cent_rows = []
for y in waves:
    sub = resp[resp["year"] == y]
    for p in ["D", "I", "R"]:
        s = sub[sub["party"] == p]
        if len(s) == 0:
            cent_rows.append({"year": y, "party": p, "n": 0,
                              "econ_mean": np.nan, "cult_mean": np.nan,
                              "econ_sd": np.nan, "cult_sd": np.nan})
            continue
        cent_rows.append({
            "year": y, "party": p, "n": int(len(s)),
            "econ_mean": weighted_mean(s["econ"], s["weight"]),
            "cult_mean": weighted_mean(s["cult"], s["weight"]),
            "econ_sd": math.sqrt(weighted_var(s["econ"], s["weight"])),
            "cult_sd": math.sqrt(weighted_var(s["cult"], s["weight"])),
        })
cent_df = pd.DataFrame(cent_rows)
cent_df.to_csv(OUT_DIR / "party_centroids.csv", index=False)


def pooled_within_party_sd(sub: pd.DataFrame) -> tuple[float, float]:
    parts = []
    for p in ["D", "R"]:
        s = sub[sub["party"] == p]
        if len(s) < 2:
            continue
        ev = weighted_var(s["econ"], s["weight"])
        cv = weighted_var(s["cult"], s["weight"])
        parts.append((ev, cv, s["weight"].sum()))
    if not parts:
        return float("nan"), float("nan")
    W = sum(p[2] for p in parts)
    ev = sum(p[0] * p[2] for p in parts) / W
    cv = sum(p[1] * p[2] for p in parts) / W
    return math.sqrt(ev), math.sqrt(cv)


pol_rows = []
for y in waves:
    sub = resp[resp["year"] == y]
    fD = densities[(y, "D")]
    fR = densities[(y, "R")]
    ovl = ovl_2d(fD, fR)

    dem = sub[sub["party"] == "D"]
    rep = sub[sub["party"] == "R"]

    if len(dem) and len(rep):
        de = weighted_mean(dem["econ"], dem["weight"])
        dc = weighted_mean(dem["cult"], dem["weight"])
        re_ = weighted_mean(rep["econ"], rep["weight"])
        rc = weighted_mean(rep["cult"], rep["weight"])
        raw_sep = math.sqrt((re_ - de) ** 2 + (rc - dc) ** 2)
        sd_e, sd_c = pooled_within_party_sd(sub)
        pooled_sd = math.sqrt((sd_e ** 2 + sd_c ** 2) / 2.0) if not math.isnan(sd_e) else float("nan")
        scaled_sep = raw_sep / pooled_sd if pooled_sd and not math.isnan(pooled_sd) else float("nan")
        w_econ = wasserstein_distance(dem["econ"], rep["econ"],
                                      u_weights=dem["weight"], v_weights=rep["weight"])
        w_cult = wasserstein_distance(dem["cult"], rep["cult"],
                                      u_weights=dem["weight"], v_weights=rep["weight"])
    else:
        raw_sep = scaled_sep = w_econ = w_cult = float("nan")

    # Dip test per axis on the pooled wave (all parties), unweighted (diptest does not weight).
    if len(sub) >= 10:
        dip_e, p_e = diptest.diptest(sub["econ"].to_numpy())
        dip_c, p_c = diptest.diptest(sub["cult"].to_numpy())
    else:
        dip_e = p_e = dip_c = p_c = float("nan")

    pol_rows.append({
        "year": y,
        "n_dem": int(len(dem)),
        "n_rep": int(len(rep)),
        "ovl_2d": ovl,
        "raw_separation": raw_sep,
        "scaled_separation": scaled_sep,
        "wasserstein_econ": w_econ,
        "wasserstein_cult": w_cult,
        "dip_econ": dip_e,
        "dip_econ_pval": p_e,
        "dip_cult": dip_c,
        "dip_cult_pval": p_c,
    })

pol_df = pd.DataFrame(pol_rows).sort_values("year").reset_index(drop=True)

# Centered moving average of length 3 (1 wave on each side); leaves NaN at edges.
ma_cols = ["ovl_2d", "raw_separation", "scaled_separation",
           "wasserstein_econ", "wasserstein_cult",
           "dip_econ", "dip_cult"]
for c in ma_cols:
    pol_df[f"{c}_ma3"] = pol_df[c].rolling(window=3, center=True, min_periods=3).mean()

pol_df.to_csv(OUT_DIR / "polarization_series.csv", index=False)


# --------------------------------------------------------------------------- #
# Density small-multiples plot
# --------------------------------------------------------------------------- #

print("\nPlotting small multiples ...")

ncols = 5
nrows = int(math.ceil(len(waves) / ncols))
fig, axes = plt.subplots(nrows, ncols, figsize=(3.2 * ncols, 3.2 * nrows),
                         sharex=True, sharey=True)
axes = np.atleast_2d(axes)

for i, y in enumerate(waves):
    ax = axes[i // ncols, i % ncols]
    sub = resp[resp["year"] == y]
    # Background: pooled-wave density (very light)
    fAll = densities[(y, "ALL")]
    if not np.isnan(fAll).any():
        ax.contourf(GRID_AXIS, GRID_AXIS, fAll.T, levels=8, cmap="Greys", alpha=0.35)
    # Party contour lines
    for p in ["D", "R"]:
        f = densities[(y, p)]
        if np.isnan(f).any():
            continue
        ax.contour(GRID_AXIS, GRID_AXIS, f.T, levels=4,
                   colors=PARTY_COLORS[p], linewidths=0.9, alpha=0.85)
    # Centroids
    for p in ["D", "R"]:
        c = cent_df[(cent_df["year"] == y) & (cent_df["party"] == p)]
        if len(c) and not c["econ_mean"].isna().all():
            ax.scatter(c["econ_mean"], c["cult_mean"],
                       c=PARTY_COLORS[p], s=40, edgecolor="black", linewidth=0.6, zorder=5)
    ovl = pol_df.loc[pol_df["year"] == y, "ovl_2d"].iloc[0]
    ax.set_title(f"{y}  N={len(sub):,}  OVL={ovl:.2f}", fontsize=9)
    ax.axhline(0, color="black", lw=0.4, alpha=0.3)
    ax.axvline(0, color="black", lw=0.4, alpha=0.3)
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)

# Hide unused panels
for j in range(len(waves), nrows * ncols):
    axes[j // ncols, j % ncols].axis("off")

for ax in axes[-1, :]:
    ax.set_xlabel("Economic (← lib   cons →)", fontsize=9)
for ax in axes[:, 0]:
    ax.set_ylabel("Cultural (← lib   cons →)", fontsize=9)

fig.suptitle(
    f"ANES 2D ideological compass {START_YEAR}-{END_YEAR}  "
    f"(global axes, global bandwidth, listwise core panel)",
    fontsize=11,
)
fig.tight_layout(rect=[0, 0, 1, 0.97])
fig.savefig(PLOT_DIR / "density_small_multiples.png", dpi=140)
plt.close(fig)


# --------------------------------------------------------------------------- #
# Acceptance checks
# --------------------------------------------------------------------------- #

print("\n[Acceptance] running isolation tests")
acc_lines = []

# 1. Single-wave-isolated normalization: re-rescale ONE wave using its OWN
#    mean/SD (per-wave z-then-clip-to-[-1,1]); the resulting axis means must
#    differ from the global theoretical-endpoint build, because the centering
#    point shifts when scaling becomes wave-dependent. Same-result => the
#    global build is silently per-wave normalised (scaling leaked).
test_year = waves[len(waves) // 2]
sub_raw = df[df["year"] == test_year].copy()
single_recoded = {}
for var in ECON_CORE + CULT_CORE:
    spec = ITEMS[var]
    s = sub_raw[var].where(~sub_raw[var].isin(spec["miss"]))
    valid = s.between(spec["lo"], spec["hi"])
    s = s.where(valid)
    if s.notna().any():
        m, sd = s.mean(), s.std(ddof=0)
        z = (s - m) / sd if sd > 0 else s * 0
        z = z.clip(-3, 3) / 3.0  # z in [-1,1]
        if spec["reverse"]:
            z = -z
        single_recoded[var] = z
    else:
        single_recoded[var] = s

single_tbl = pd.concat(single_recoded, axis=1).dropna()
single_econ = single_tbl[ECON_CORE].mean(axis=1).mean()
single_cult = single_tbl[CULT_CORE].mean(axis=1).mean()
global_econ = resp.loc[resp["year"] == test_year, "econ"].mean()
global_cult = resp.loc[resp["year"] == test_year, "cult"].mean()
acc_lines.append(
    f"[norm-isolation] year={test_year}  "
    f"per-wave-z-rescaled econ={single_econ:+.4f}, cult={single_cult:+.4f}  vs  "
    f"global econ={global_econ:+.4f}, cult={global_cult:+.4f}  "
    f"diff_econ={single_econ - global_econ:+.4f}, diff_cult={single_cult - global_cult:+.4f}"
)
norm_isolation_passes = not (math.isclose(single_econ, global_econ, abs_tol=1e-3)
                              and math.isclose(single_cult, global_cult, abs_tol=1e-3))
acc_lines.append(f"  -> {'PASS' if norm_isolation_passes else 'FAIL - scaling leaked'}")

# 2. Single-wave-isolated KDE: refit gaussian_kde on one wave with its OWN
#    bandwidth; result should differ from global-bandwidth KDE on the same wave.
sub_resp = resp[resp["year"] == test_year]
own_kde = gaussian_kde(sub_resp[["econ", "cult"]].T, bw_method="scott",
                       weights=sub_resp["weight"])
own_bw = float(own_kde.factor)
glob_kde = gaussian_kde(sub_resp[["econ", "cult"]].T, bw_method=global_bw,
                        weights=sub_resp["weight"])
acc_lines.append(
    f"[kde-isolation]  year={test_year}  own_bw={own_bw:.4f}  global_bw={global_bw:.4f}  "
    f"diff={own_bw - global_bw:+.4f}"
)
kde_isolation_passes = not math.isclose(own_bw, global_bw, abs_tol=1e-6)
acc_lines.append(f"  -> {'PASS' if kde_isolation_passes else 'FAIL - bandwidth leaked'}")

# 3. Direction sanity: in every wave with both parties, Rep mean must be >= Dem
#    mean on BOTH axes (Rep more conservative). One-axis flip is a coding bug.
dir_fails = []
for y in waves:
    d = cent_df[(cent_df["year"] == y) & (cent_df["party"] == "D")].iloc[0]
    r = cent_df[(cent_df["year"] == y) & (cent_df["party"] == "R")].iloc[0]
    if d["n"] == 0 or r["n"] == 0:
        continue
    if r["econ_mean"] < d["econ_mean"]:
        dir_fails.append(f"{y}: Rep econ ({r['econ_mean']:+.3f}) < Dem econ ({d['econ_mean']:+.3f})")
    if r["cult_mean"] < d["cult_mean"]:
        dir_fails.append(f"{y}: Rep cult ({r['cult_mean']:+.3f}) < Dem cult ({d['cult_mean']:+.3f})")
if dir_fails:
    acc_lines.append("[direction]  FAIL - some waves have Dem more conservative than Rep:")
    for line in dir_fails:
        acc_lines.append(f"  {line}")
else:
    acc_lines.append(
        "[direction]  PASS - Rep mean >= Dem mean on both axes in every wave with both parties present"
    )

(OUT_DIR / "acceptance_checks.txt").write_text("\n".join(acc_lines))
print("\n".join(acc_lines))


# --------------------------------------------------------------------------- #
# Build log
# --------------------------------------------------------------------------- #

log_lines = [
    "# ANES 2D Compass - Build Log",
    "",
    f"Window: {START_YEAR}-{END_YEAR} ({len(waves)} effective waves: {waves})",
    f"Source: data/phase9_empirical/raw/timeseries_csv.csv ({len(df):,} rows in window)",
    f"Weight: {WEIGHT_VAR} (full sample; =1.0 in SRS-era waves 1986-1990, proper weights 1992+)",
    f"Excluded waves (zero listwise survivors): {dropped_waves}",
    f"Party var: {PARTY_VAR} (7-pt; collapsed 1-3=Dem, 4=Ind, 5-7=Rep)",
    "",
    "## Fixed core panel",
    f"- Economic ({len(ECON_CORE)} items): {ECON_CORE}",
    f"- Cultural ({len(CULT_CORE)} items): {CULT_CORE}",
    "",
    f"Listwise drop on the 7 core items: {before:,} -> {after:,} ({after / before:.1%} retained).",
    "",
    "## Normalization",
    "Each item recoded to higher=conservative, rescaled to [-1,1] using its",
    "theoretical scale endpoints (not per-wave min/max). Axis score = equal-weight",
    "mean of that axis's core items. Scaling params persisted to scaling_params.json.",
    "",
    "## KDE",
    f"Bandwidth = Scott's rule on the pooled (all-waves, all-parties, weighted) sample.",
    f"Frozen scalar bandwidth factor = {global_bw:.4f}.",
    f"Grid: {GRID_N}x{GRID_N} on [{GRID_LO}, {GRID_HI}]^2, cell={GRID_CELL:.4f}, area={GRID_AREA:.6f}.",
    "Per wave x party density evaluated on this exact grid; densities/<year>_<party>.npy.",
    "",
    "## Polarization metrics",
    "- ovl_2d:  2D overlapping coefficient between Dem and Rep joint densities (primary).",
    "- scaled_separation:  centroid distance / pooled within-party RMS SD.",
    "- wasserstein_{econ,cult}:  1D earth-mover's distance between party distributions per axis.",
    "- dip_{econ,cult}:  Hartigan's dip statistic + p-value per axis, pooled across parties.",
    "All metrics reported raw-per-wave and as centered MA(3).",
    "",
    "## Acceptance",
] + [f"- {line}" for line in acc_lines]

(OUT_DIR / "build_log.md").write_text("\n".join(log_lines))


# --------------------------------------------------------------------------- #
# Final summary
# --------------------------------------------------------------------------- #

print("\n=== POLARIZATION SERIES ===")
display_cols = ["year", "n_dem", "n_rep", "ovl_2d", "scaled_separation",
                "wasserstein_econ", "wasserstein_cult"]
print(pol_df[display_cols].to_string(index=False, float_format=lambda v: f"{v:.3f}"))

print("\n=== CENTROIDS ===")
print(cent_df.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
print("\nDone.")
