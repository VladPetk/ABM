# Phase 9 — Raw-data sources for re-deriving empirical targets

*Companion to `phase9_empirical_targets.md`. The current targets in
`data/phase9_empirical/` are derived from **published moments tables**
(Levendusky 2009 ch. 2, Baldassarri & Gelman 2008, Mason 2018 app. B,
Treier-Hillygus 2009, etc.), not from raw respondent data. The
sandbox's network allowlist blocked direct file downloads. The
following list lets a host-machine user fetch the raw files and
re-compute per-decade (var_x, var_y, corr_xy) directly.*

---

## Direct-download priority order (highest signal, lowest friction)

### 1. GSS Cumulative File (highest priority — no login, longest series)

- **Download page**: https://gss.norc.org/get-the-data/stata
- **Direct file (Stata, easiest)**: https://gss.norc.org/Documents/stata/GSS_stata.zip
- **Alternative (SPSS)**: https://gss.norc.org/Documents/spss/GSS_spss.zip
- **Codebook**: https://gss.norc.org/get-documentation
- **Coverage**: 1972–2022, ~70,000 respondents total, ~1500–3000/year.
- **License**: public domain.

**Variables to extract (and the engine convention they map to):**

| GSS variable | Description | Maps to | Convention |
|---|---|---|---|
| `polviews` | 7-pt liberal-conservative self-ID (1=extremely liberal → 7=extremely conservative) | x (general ideology) | rescale `(v-4)/3` → [-1, +1]; +1 = conservative |
| `eqwlth` | 7-pt "gov should reduce income differences" (1=should reduce → 7=no business) | x (economic) | `(v-4)/3`; +1 = laissez-faire |
| `helpsick` | 5-pt "gov should help with medical bills" (1=should → 5=no responsibility) | x | `(v-3)/2`; +1 = laissez-faire |
| `abany` | dichotomous "abortion any reason" (1=yes/legal → 2=no) | y (cultural) | `(v-1.5)*2`; +1 = traditional (abortion no) |
| `homosex` | 4-pt "sex relations with same-sex" (1=always wrong → 4=not wrong) | y | `−(v-2.5)/1.5`; +1 = traditional |
| `racdif1-4` | 4 items on racial inequality causes (each 1=yes → 2=no) | y | average then `(v-1.5)*2`; +1 = traditional |
| `prayer` | 4-pt school prayer | y | rescale to ±1; +1 = traditional |
| `partyid` | 7-pt party ID (0=strong Dem → 6=strong Rep) | party (stratifier) | not for x/y axis |
| `year` | survey year | decade bucket | — |

**Engine-faithful 2D recipe for GSS:**
```python
# After loading the SPSS/Stata file into pandas:
df['x'] = (df[['polviews', 'eqwlth', 'helpsick']]
          .apply(lambda c: (c - c.mean()) / c.std())  # z-score each item
          .mean(axis=1))                              # average to one axis
df['x'] = df['x'].clip(-2, 2) / 2   # roughly map to [-1, 1]

df['y'] = (df[['abany', 'homosex', 'racdif1', 'racdif2', 'racdif3', 'racdif4']]
          .apply(_z_with_sign_flip_where_needed)
          .mean(axis=1))
df['y'] = df['y'].clip(-2, 2) / 2

# Sign check: cross-tab with party — Dems (low partyid) should
# average to negative x AND negative y.
print(df.groupby('partyid')[['x','y']].mean())  # Strong Dem row should be (-, -)

# Per-decade stats:
df['decade'] = (df['year'] // 10) * 10
print(df.groupby('decade')[['x','y']].agg(['mean','var']))
print(df.groupby('decade').apply(lambda d: d['x'].corr(d['y'])))
```

**Expected per-decade output to compare against
`raw_data_synthesis.GSS_MOMENTS`:**

| Decade | mean(x) | mean(y) | var(x) | var(y) | corr |
|---|---|---|---|---|---|
| 1980 | +0.02 | +0.30 | 0.28 | 0.32 | +0.15 |
| 1990 | +0.03 | +0.22 | 0.28 | 0.31 | +0.18 |
| 2000 | +0.02 | +0.15 | 0.30 | 0.32 | +0.22 |
| 2010 | +0.00 | +0.05 | 0.31 | 0.34 | +0.28 |
| 2020 | -0.02 | -0.02 | 0.33 | 0.36 | +0.35 |

If the actual GSS numbers differ materially from these, the synthetic
targets are wrong and should be updated. **The most likely correction
is on var(y)**: the synthesized targets might be too narrow if the
actual GSS data has more dispersion than the moment table I used.

---

### 2. Voteview / DW-NOMINATE (no login, direct download, ~5 MB)

- **Page**: https://voteview.com/data
- **Direct file (all-Congress members)**: https://voteview.com/static/data/out/members/HSall_members.csv
- **Direct file (per-Congress party medians)**: https://voteview.com/static/data/out/parties/HSall_parties.csv
- **License**: CC-BY (free for any use).

**Variables you need:** `congress` (number), `chamber` (House/Senate),
`party_code` (100=Dem, 200=Rep), `nominate_dim1` (1st dim, ~economic),
`nominate_dim2` (2nd dim, ~cultural/regional), `bioname` (legislator name).

**Per-decade recipe:**
```python
df = pd.read_csv("HSall_members.csv")
df = df[df['chamber'] == 'House']
df['year'] = 1789 + (df['congress'] - 1) * 2
df['decade'] = (df['year'] // 10) * 10
df = df[df['party_code'].isin([100, 200])]  # Dems + Reps only
party_means = df.groupby(['decade', 'party_code'])[['nominate_dim1', 'nominate_dim2']].mean()
print(party_means.loc[[1980, 1990, 2000, 2010, 2020]])
```

**Expected output to compare with `DWNOMINATE_PARTY_MEANS`:**

| Decade | R (1st, 2nd) | D (1st, 2nd) |
|---|---|---|
| 1980 | (+0.30, +0.05) | (-0.30, -0.10) |
| 1990 | (+0.38, +0.10) | (-0.34, -0.15) |
| 2000 | (+0.45, +0.18) | (-0.38, -0.18) |
| 2010 | (+0.51, +0.25) | (-0.40, -0.22) |
| 2020 | (+0.55, +0.30) | (-0.42, -0.25) |

**Sign-convention note**: DW-NOMINATE 2nd-dim sign flips across some
Congresses because the dimension is only identified up to sign.
Voteview publishes a "stable orientation" version where the
post-realignment sign matches the convention "more positive = more
conservative on the 2nd-dim axis". The CSV should have this; verify by
spot-checking known Republicans (e.g., Reagan, Gingrich, McConnell)
have **positive** nominate_dim2 in modern Congress.

---

### 3. CCES 2020 Common Content (no login, modern bimodal data)

- **Dataverse page**: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/E9N6PH
- **Direct CSV download** (after clicking through Dataverse): typically
  `CES20_Common_OUTPUT_vv.csv` (~150 MB raw; or filtered subset).
- **Codebook**: same Dataverse page → "Documentation" tab.
- **License**: CC-0 (public domain).
- **N**: ~60,000 respondents in 2020.

**Variables to extract:**

| CCES variable | Description | Maps to | Convention |
|---|---|---|---|
| `ideo5` | 5-pt liberal-conservative self-ID | x | rescale `(v-3)/2`; +1 = conservative |
| `CC20_350a-h` (various) | health-care government role, taxes, regulation, trade | x | rescale issue by issue, average |
| `CC20_330a-c` | abortion items | y | (v−mid)/range; +1 = traditional |
| `CC20_322a-d` | gay rights, transgender, etc. | y | as above |
| `CC20_331a-d` | immigration policy | y | as above |
| `CC20_320a-d` | gun control (often clusters with cultural) | y | as above |
| `pid7` | 7-pt party ID | party | stratifier |
| `weight` | survey weight | — | use this for population-level stats |

**Per-respondent recipe**: standardize and average each axis, then
compute weighted variance and covariance. Expected (from
`raw_data_synthesis.CCES_MOMENTS[2020]`):

| Year | mean(x) | mean(y) | var(x) | var(y) | corr |
|---|---|---|---|---|---|
| 2020 | -0.10 | -0.08 | 0.45 | 0.42 | +0.48 |

**This is the highest-N modern source. If real CCES 2020 has var_y >
0.42, that's an upward correction to our targets.**

---

### 4. ANES Cumulative File (requires free login; gold standard for 1948-2020 time series)

- **Page**: https://electionstudies.org/data-center/anes-time-series-cumulative-data-file/
- **Login**: free registration at https://electionstudies.org
- **File** (after login): `anes_timeseries_cdf_csv_20221219.zip` (or
  Stata/SPSS variants).
- **Codebook**: same page.
- **License**: free for academic + research use.

**Critical variables (per `raw_data_synthesis.ANES_MOMENTS`):**

| ANES variable | Description | Maps to | Convention |
|---|---|---|---|
| `VCF0803` | 7-pt lib-cons self-placement | x (general) | `(v-4)/3`; +1 = cons |
| `VCF0809` | gov-services tradeoff scale (7-pt) | x (economic) | `(v-4)/3`; +1 = laissez-faire |
| `VCF0839` | gov healthcare role | x | rescale similarly |
| `VCF0838` | abortion 4-pt | y | `(v−2.5)/1.5`; +1 = traditional |
| `VCF0834` | women's role 7-pt | y | `−(v-4)/3`; +1 = traditional |
| `VCF0876a` | gay job protection / military | y | rescale; +1 = traditional |
| `VCF0301` | 7-pt party ID | party | stratifier |
| `VCF0004` | year | year | — |
| `VCF0006` | unique respondent ID | — | for panel-aware computation |

**Per-decade recipe**: same structure as GSS. Expected values:

| Decade | mean(x) | mean(y) | var(x) | var(y) | corr |
|---|---|---|---|---|---|
| 1980 | -0.05 | +0.20 | 0.32 | 0.34 | +0.18 |
| 1990 | -0.02 | +0.15 | 0.31 | 0.32 | +0.22 |
| 2000 | -0.04 | +0.08 | 0.34 | 0.34 | +0.30 |
| 2010 | -0.06 | +0.02 | 0.36 | 0.37 | +0.41 |
| 2020 | -0.08 | -0.05 | 0.38 | 0.40 | +0.52 |

---

### 5. Voter Study Group / Democracy Fund VOTER Survey (no login)

- **Page**: https://www.voterstudygroup.org/data/data-downloads
- **Direct file**: usually `2020_voter_survey.csv` and similar for
  2016/2017/2019 waves.
- **License**: free with attribution.
- **N**: ~5,000–8,000 per wave; panel respondents.
- **Useful because**: panel design lets you measure within-person
  movement (per-tick volatility for the engine's noise calibration).

---

### 6. PRRI American Values Atlas (annual, modern cultural questions)

- **Page**: https://ava.prri.org/
- **Datasets**: per-year crosstabs publicly downloadable; some require
  email for full microdata.
- **Coverage**: 2013–2023, ~50,000 interviews/year, cultural-axis focus.

---

## Cross-checks once raw data is in hand

Once you have GSS or ANES processed into per-decade (var_x, var_y,
corr), three sanity checks:

1. **Sign consistency**: per-decade group means should put Strong-Dem
   respondents at (-x, -y) and Strong-Rep at (+x, +y). If signs flip
   anywhere, the issue-item rescaling has an error.

2. **Trajectory**: var(x) and var(y) should be **roughly equal** at
   every decade (this is what Mason 2018, Levendusky 2009, T-H 2009 all
   imply). The synthetic targets currently have var_y slightly smaller
   than var_x. If raw GSS shows the opposite, the targets need flipping.

3. **Correlation rise**: corr(x, y) should rise monotonically from
   1980 → 2020. The current synthetic shows +0.15 → +0.35 in GSS, +0.18
   → +0.52 in ANES. Real raw data may diverge.

## Specific calibration questions the raw data should answer

- **Is empirical 2020 var_y really ≈ 0.29 (as the synthesized cloud
  says) or is it closer to 0.40 (as the §3.5.1 ANES-only moments
  table says)?** This is the biggest unknown — could be a 35%
  re-calibration in either direction.
- **Does the empirical 2020 corr(x, y) match +0.59 (synthesized loaded
  cloud) or +0.52 (§3.5.1)?** If real corr is closer to +0.4–0.5, our
  best engine config (+0.45) is already correct.
- **What's the actual 1980 var(y)?** Synthesized says 0.21; ANES table
  says 0.34. If the truth is closer to 0.21, the current engine 1980 IC
  is already correct. If closer to 0.34, the IC needs widening.

## Published-paper tables to look up (if microdata is too much hassle)

Even without downloading raw data, three tables would close most of
the uncertainty:

1. **Levendusky 2009, Table 2.1 (p. 47) and 2.2 (p. 48)**: per-decade
   within-party SD on issue scales. JSTOR / U Chicago Press book.
2. **Baldassarri & Gelman 2008, AJS 114(2):408, Tables 2 and 3**:
   per-decade cross-issue correlation (the issue-issue correlation,
   which is close to corr(x, y)). JSTOR.
3. **Mason 2018, Appendix B, Tables B.1-B.3**: standardized
   discrimination coefficients for partisan-sorting on economic vs
   cultural batteries. U Chicago Press.

Cross-check whether the values in `raw_data_synthesis.py` (which were
read from these tables) match exactly. If they were transcribed
wrong, that explains some of the gap.

## Quickest path if Vlad has limited time

1. **GSS Stata zip** (~5 minutes to download): https://gss.norc.org/Documents/stata/GSS_stata.zip
2. Open in R / Python / Stata. ~30 lines of code per the recipe above.
3. Compare GSS per-decade (var_x, var_y, corr) to the table in
   `raw_data_synthesis.GSS_MOMENTS`. If they match to within 10%, the
   synthetic targets are honest and the engine genuinely cannot match
   them. If they differ materially, the targets need updating and the
   engine may already be closer than 46% to truth.
4. Optionally do the same for **Voteview HSall_members.csv** (~30
   seconds to download, ~10 lines of code).

GSS alone would let you bless or correct 70% of the synthetic targets.

---

## Source citations (paper-table fallback)

- Levendusky, M. (2009). *The Partisan Sort: How Liberals Became
  Democrats and Conservatives Became Republicans*. University of
  Chicago Press. **Tables 2.1, 2.2 (per-decade within-party SD)** and
  **chapter 2 figures** are the primary source.
- Baldassarri, D., & Gelman, A. (2008). Partisans without
  Constraint: Political Polarization and Trends in American Public
  Opinion. *American Journal of Sociology* 114(2): 408-446. JSTOR
  https://www.jstor.org/stable/10.1086/590649 . **Tables 2-3** are
  the cross-issue correlation source.
- Mason, L. (2018). *Uncivil Agreement: How Politics Became Our
  Identity*. University of Chicago Press. **Appendix B Tables
  B.1-B.3**.
- Treier, S., & Hillygus, D. S. (2009). The Nature of Political
  Ideology in the Contemporary Electorate. *POQ* 73(4): 679-703.
  https://academic.oup.com/poq/article-abstract/73/4/679/1843470 .
  **Figure 1 + Table 1** report the 2D-IRT correlations directly.
- Hare, C., Liu, T.-P., & Lupton, R. N. (2018). What Ordinary
  Americans (Sometimes) Think About Ideological Labels.
  *Research & Politics* 5(2). https://journals.sagepub.com/doi/10.1177/2053168018787714
- Ansolabehere, S., & Schaffner, B. F. (2022). *2020 CCES Common
  Content Codebook*. Harvard Dataverse.
- Voteview / Lewis et al. (2024). *Voteview: Congressional Roll-Call
  Votes Database*. https://voteview.com
