# ANES 2D Compass - Build Log

Window: 1986-2024 (14 effective waves: [1986, 1988, 1990, 1992, 1994, 1996, 1998, 2000, 2004, 2008, 2012, 2016, 2020, 2024])
Source: data/phase9_empirical/raw/timeseries_csv.csv (44,308 rows in window)
Weight: VCF0009z (full sample; =1.0 in SRS-era waves 1986-1990, proper weights 1992+)
Excluded waves (zero listwise survivors): [2002]
Party var: VCF0301 (7-pt; collapsed 1-3=Dem, 4=Ind, 5-7=Rep)

## Fixed core panel
- Economic (3 items): ['VCF0803', 'VCF0809', 'VCF0839']
- Cultural (4 items): ['VCF0838', 'VCF0830', 'VCF0852', 'VCF0853']

Listwise drop on the 7 core items: 44,308 -> 22,761 (51.4% retained).

## Normalization
Each item recoded to higher=conservative, rescaled to [-1,1] using its
theoretical scale endpoints (not per-wave min/max). Axis score = equal-weight
mean of that axis's core items. Scaling params persisted to scaling_params.json.

## KDE
Bandwidth = Scott's rule on the pooled (all-waves, all-parties, weighted) sample.
Frozen scalar bandwidth factor = 0.2022.
Grid: 81x81 on [-1.05, 1.05]^2, cell=0.0263, area=0.000689.
Per wave x party density evaluated on this exact grid; densities/<year>_<party>.npy.

## Polarization metrics
- ovl_2d:  2D overlapping coefficient between Dem and Rep joint densities (primary).
- scaled_separation:  centroid distance / pooled within-party RMS SD.
- wasserstein_{econ,cult}:  1D earth-mover's distance between party distributions per axis.
- dip_{econ,cult}:  Hartigan's dip statistic + p-value per axis, pooled across parties.
All metrics reported raw-per-wave and as centered MA(3).

## Acceptance
- [norm-isolation] year=2000  per-wave-z-rescaled econ=+0.0341, cult=+0.0091  vs  global econ=+0.1120, cult=+0.2123  diff_econ=-0.0779, diff_cult=-0.2032
-   -> PASS
- [kde-isolation]  year=2000  own_bw=0.4058  global_bw=0.2022  diff=+0.2036
-   -> PASS
- [direction]  PASS - Rep mean >= Dem mean on both axes in every wave with both parties present