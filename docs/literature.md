# polarlab — literature & data sources

*The consolidated, **annotated** index of every empirical source the model
leans on: what each one is, what it anchors in the engine, and where in the
repo it is used. This is the "where does this number come from?" reference.*

This document exists because polarlab is grounded in the empirical literature —
every calibration choice is anchored to a published finding — but until now the
citations lived scattered across `methods.md`, `polarization_causal_model.md`,
the Phase 10 intervention briefs, the Phase 9 data-source spec, and inline code
comments. This file pulls them together and, crucially, says **what each source
does for the model** rather than just listing it.

**How this relates to the other docs.**
- [`methods.md`](methods.md) holds the formal flat bibliography (the
  alphabetical "Citations" list) plus the per-mechanism calibration writeups.
  This file is the *annotated* companion — read it to find the source for a
  given mechanism; read `methods.md` for the calibration detail.
- [`polarization_causal_model.md`](polarization_causal_model.md) is the home of
  the **causal-decomposition** evidence (cohort vs period, realignment,
  evidence grading of timeline events). §4 below summarises it; that doc has the
  full grading.
- [`phase10_interventions/redesign_briefs.md`](phase10_interventions/redesign_briefs.md)
  is the home of the **intervention** literature (X1–X7 envelopes, with
  provenance tags). §3 below summarises it.
- [`specs/phase9_raw_data_sources.md`](specs/phase9_raw_data_sources.md) has the
  download recipes for the raw survey files. §1 below summarises what each
  calibrates.

**Confidence note.** Phase 6-era anchors (Bail 2018, Iyengar 2019, Mason 2018,
Pettigrew & Tropp 2006, Allport 1954, Mutz, Hetherington, Levendusky, McCarty et
al.) are high-confidence and venue-pinned. A set of post-2020 intervention
citations is still pending venue/year verification — see §5.

---

## 1. Empirical datasets (the calibration anchors)

These are the **data**, not the papers. They are what the engine is actually
fit against. The two that ship in the calibration are ANES (the 2D compass +
the out-party thermometer) and DW-NOMINATE (elite divergence); the rest are
cross-checks and host-machine re-derivation paths.

| Dataset | Coverage | What it calibrates in polarlab | Where used | Access |
|---|---|---|---|---|
| **ANES Time Series Cumulative Data File (CDF)** | 1948–2024; ~70k respondents (weighted, `VCF0009z`) | **Primary fit target.** The 2D ideological compass (1986–2024), per-decade moments (mean/var/corr), and the per-decade Wasserstein-2 distance gate against respondent clouds. The tick→year scalar is anchored here. | `scripts/anes_2d_compass.py`; `data/phase9_empirical/derived/`; methods.md §3.1, §3.6, §5.10 | electionstudies.org (free login) |
| **ANES out-party feeling thermometer** (`VCF0218` Dem party / `VCF0224` Rep party; partisans only; weighted) | 1978–2024 | **Affect bands.** Rebuilt from raw via the principled midpoint map `aff=(deg−50)/50` (1978 47.8° → 2020 19.0° → 2024 20.4°). Replaced the old hand-scaled bands (which ran ~0.2 too cold). Drives the affect re-grade target. | `scripts/affect_band_builder.py`; `data/phase9_empirical/derived/{outparty_thermometer.csv, affect_bands.json}`; `docs/affect_bands_investigation.md`; methods.md §5.10 | same ANES CDF |
| **DW-NOMINATE / Voteview** (party-median roll-call scores; dim1≈economic, dim2≈cultural) | 1789–present (House/Senate) | **Elite divergence.** `EliteDrift.rate` (~0.0026/tick; ~0.4 NOMINATE units over ~50 yrs) and the per-decade asymmetric drift schedule. **S4 (T4.2):** corroborates the **mass-elite gap** — elite (roll-call) separation exceeds ANES voter separation — which anchors the `elite_lead_factor` (the PartyPull cue attractor = voter centroid × L; methods.md §5.25). | `abm/rules/elite_drift.py`; `abm/calibration.py`; methods.md §3.2, §5.25; phase9_raw_data_sources.md §2 | voteview.com/data (CC-BY; `HSall_members.csv`, `HSall_parties.csv`) |
| **GSS Cumulative File** (NORC Release 3) | 1972–2024; ~76k | **Ingested at S4/T4.0** for the per-year constraint + B&G dual series (`scripts/build_gss_constraint_series.py` → `data/mhv/gss_constraint_series.json`; 17-item econ/race/moral battery, WTSSALL-weighted, binary Dem/Rep). The S4 calibration target for emergent `ConstraintOp`. Also cross-checks per-decade 2D ideology moments. | phase9_raw_data_sources.md §1; methods.md (S4) | gss.norc.org `gss7224_r3.dta` (public domain) |
| **CCES / CES 2020 Common Content** | 2020; ~60k | Modern bimodal distribution cross-check; per-issue variance. Highest-N modern source. | phase9_raw_data_sources.md §3 | Harvard Dataverse `doi:10.7910/DVN/E9N6PH` (CC-0) |
| **Democracy Fund Voter Study Group (VOTER Survey)** | 2016/2017/2019/2020 panel; ~5–8k/wave | Within-person movement → per-tick volatility / noise calibration (the panel design is what makes this useful). | phase9_raw_data_sources.md §5 | voterstudygroup.org (attribution) |
| **PRRI American Values Atlas** | 2013–2023; ~50k/yr | Modern cultural-axis trend cross-check. | phase9_raw_data_sources.md §6 | ava.prri.org |

**Published moment-table fallbacks** (used to synthesise the Phase 9 targets
when raw microdata download was blocked): Levendusky 2009 Tables 2.1/2.2
(within-party SD), Baldassarri & Gelman 2008 Tables 2–3 (cross-issue
correlation), Mason 2018 Appendix B (sorting coefficients), Treier & Hillygus
2009 Fig 1/Table 1 (2D-IRT correlations), Hare, Liu & Lupton 2018 (ideological
labels), Ansolabehere & Schaffner 2022 (CCES codebook). See
phase9_raw_data_sources.md §"Published-paper tables."

**Repo data artifacts.** `data/literature/` holds `augmentation_notes.pdf`,
`phase9_empirical_targets_v2.pdf`, and
`phase9_empirical_targets_visualization_v2.pdf` (the visual spec + density
small-multiples for the per-decade distribution targets).
`data/phase9_empirical/derived/` holds the ANES-derived per-decade pointclouds
and KDEs used by the Wasserstein gate. **`data/mhv/issue_loadings.json`**
(MHV S2, 2026-06) is the frozen D=7 issue-battery structure — the 1986-wave
item correlation matrix, party-conditional item moments, 3-block latent map,
and compass-readout definition — derived from the ANES CDF by
`scripts/build_issue_loadings.py` with the same recode recipe as the compass
pipeline; it seeds the S2 issue-vector substrate (`abm/core/issues.py`;
methods.md §5.18).

---

## 2. Core mechanism literature (the engine's spine)

Each engine rule is justified by literature. This is the source-of-record for
"why does this rule exist / where does its magnitude come from." Provenance
tags (**L** literature-supported, **N** new/design choice, **E** extrapolated)
are in methods.md's provenance table.

### 2.1 Opinion dynamics & influence
- **Hegselmann, R., & Krause, U.** (2002). Opinion dynamics and bounded
  confidence. *JASSS* 5(3). — The bounded-confidence core
  (`BoundedConfidenceInfluence`); recovered exactly as the complete-graph
  special case (`compass_basic`, `test_canonical.py`).
- **Deffuant, G., Neau, D., Amblard, F., & Weisbuch, G.** (2000). Mixing
  beliefs among interacting agents. *Advances in Complex Systems* 3:87. —
  Bounded-confidence variant (pairwise mixing).
- **Mäs, M., & Flache** (2013). Differentiation without distancing. *PLOS ONE*
  8:e74516. — Repulsion / differentiation precedent for `BacklashRepulsion`.
- **Kan, U., Porter, M. A., & Mason** (2023). An adaptive bounded-confidence
  model of opinion dynamics on networks. *Journal of Complex Networks*. —
  Network-coupled adaptive BC precedent (ties the BC rule to the network
  substrate).
- **Friedkin, N. E., & Johnsen, E. C.** (1999). *Social Influence Networks and
  Opinion Change*. — The FJ anchor + stubbornness damping `(1 − stubbornness)`
  applied at every ideology-moving rule's apply-site.

### 2.2 Network structure
- **McPherson, M., Smith-Lovin, L., & Cook, J. M.** (2001). Birds of a feather:
  Homophily in social networks. *Annual Review of Sociology* 27:415. — The
  homophily basis for network-primary design (ADR-001) and `TieRewiring`.

### 2.3 Elite divergence & mass sorting
- **McCarty, N., Poole, K. T., & Rosenthal, H.** (2006). *Polarized America*.
  MIT Press. — DW-NOMINATE elite divergence → `EliteDrift` magnitude (§3.2).
- **Hetherington, M. J.** (2001). Resurgent mass partisanship. *APSR* 95:619. —
  Mass partisanship rises as elite cues clarify → elite-cue → sorting link
  (`EliteDrift`, `PartyPull`).
- **Levendusky, M.** (2009). *The Partisan Sort*. University of Chicago Press. —
  Per-decade within-party SD targets (Phase 9).
- **Levendusky, M.** (2013). Why do partisan media polarize viewers? *AJPS*
  57:611. — Partisan-media drift; heavy-diet agents move further
  (`MediaConsumption`); X3 anchor.
- **Bonica, A.** (2014). Mapping the ideological marketplace. *AJPS* 58:367. —
  Campaign-finance ideal points (CFscores) spanning candidates, donors, and
  officeholders. **Reserved for the MHV S3 elite input series**: a planned
  cross-check on the NOMINATE-anchored elite-position channel (no engine use
  yet; logged at adoption per the log-every-source rule). Dataset: **DIME**
  (Database on Ideology, Money in Politics, and Elections, public v4.0,
  1979–2024), data.stanford.edu/dime — cite the version actually used.
- **MHV S3 elite input series — realized (T3.2, 2026-06).** The data-fed elite
  channel (`data/mhv/party_centroid_series.json`, generator
  `scripts/build_party_centroid_series.py`) is driven by the **ANES voter party
  centroids** (`data/phase9_empirical/derived/party_centroids.csv`, 1986–2024)
  with a pre-Reagan 1980 anchor — **not DW-NOMINATE** (decision D-S3-1): the
  compass is the mass public, and the elite (NOMINATE, R-led ~3:1) and voter
  (ANES, D-led ~2:1) series carry opposite asymmetry. McCarty/Poole/Rosenthal
  (above) + Bafumi & Herron 2010 (leapfrog representation) + Leonard et al. 2021
  (asymmetric feedback) are cited as the **corroborating elite evidence** and the
  basis of the **mass-elite-gap blindspot** the model does not separate
  (`docs/model_blindspots.md` §3, §6; the feedback layer is M6-full, out of
  scope). Replaces the scheduled `EliteDrift` (removing its corner-pin artifact).

### 2.4 Identity & affect
- **Mason, L.** (2018). *Uncivil Agreement: How Politics Became Our Identity*.
  University of Chicago Press. — Mega-identity stacking → affective
  polarization. Anchors `IdentitySorting`, `IdentityAlignment`,
  `IdentityToIdeologyPull`, and the identity term in `MediatedAnimus`.
  Appendix B sorting coefficients are a Phase 9 target.
- **Iyengar, S., Lelkes, Y., Levendusky, M., Malhotra, N., & Westwood, S. J.**
  (2019). The origins and consequences of affective polarization in the United
  States. *ARPS* 22:129. — The out-party thermometer trend; the affective-
  polarization synthesis behind `AffectiveUpdate` + `MediatedAnimus`.
- **Finkel, E. J. et al.** (2020). Political sectarianism in America. *Science*
  370:533. — Out-party thermometer synthesis + in-party warmth stability (the
  flat in-party reference line in the "scissors" viz).
- **Mutz, D. C.** (2018). Status threat, not economic hardship, explains the
  2016 Trump vote. *PNAS* 115:E4330. — Status threat amplifies out-group
  hostility → `threat_dynamics` / `BacklashRepulsion.threat_amplification`.
  Contested (Morgan 2018 economic rival); magnitude tagged **E**.
- **Klar, S., & Krupnikov, Y.** (2016). *Independent Politics*. — Pure
  Independents (~11–12%, ANES 2020) carry no out-party animus → Independent
  handling in `MediatedAnimus` / §4.5.

### 2.5 Contact hypothesis (the X6 anchor family)
- **Allport, G. W.** (1954). *The Nature of Prejudice*. Addison-Wesley. — The
  contact-hypothesis conditions (equal status, common goals, cooperation,
  institutional support).
- **Pettigrew, T. F., & Tropp, L. R.** (2006). A meta-analytic test of
  intergroup contact theory. *JPSP* 90:751. — Contact roughly halves prejudice
  (515 studies, r ≈ −0.21) → `cooperative_mute = 0.5`. Per-encounter scale
  tagged **E**.
- **Pettigrew, T. F.** (2009). Secondary transfer effects of intergroup
  contact. *Annual Review of Psychology* 60:121. — Agent-level cooperative-share
  mute / warmth recovery (the X6b Phase 11 candidate).

### 2.6 Algorithmic / platform null anchors
- **Allcott, H., Braghieri, L., Eichmeyer, S., & Gentzkow, M.** (2020). The
  welfare effects of social media. *AER* 110:629. — Facebook deactivation ≈
  0.04 SD → the X2/X3 quit-analogue null envelope.
- **Guess, A. M. et al.** (2023). How do social media feed algorithms affect
  attitudes…? *Science* 381:398. — Meta-2020: null on attitudes → X2 null
  anchor.
- **Nyhan, B. et al.** (2023). Like-minded sources on Facebook are prevalent but
  not polarizing. *Nature*. — Meta-2020 feed study, null on polarization.
- **Bail, C. A. et al.** (2018). Exposure to opposing views on social media can
  increase political polarization. *PNAS* 115:9216. — Cross-partisan exposure →
  backfire (R-asymmetric, ~0.10–0.12 SD) → `BacklashRepulsion` / X1.
- **Ross Arguedas, A., Robertson, C. T., Fletcher, R., & Nielsen, R. K.**
  (2022). *Echo Chambers, Filter Bubbles, and Polarisation: A Literature
  Review*. Reuters Institute. — Media-polarization synthesis.
- **MHV S3 media penetration series (T3.3, 2026-06).** The data-fed media
  channel (`data/mhv/media_penetration_series.json`, generator
  `scripts/build_media_penetration_series.py`) carries: **Pew Research Center**
  social-media adoption (% of US adults; pre-2012 anchors approximate) and
  internet adoption (% of US adults, verified 2000–2024, "Internet/Broadband"
  fact sheet); and a **partisan-media regime curve** re-expressing the discrete
  Fairness-Doctrine-repeal (Aug 1987) and Fox-News-launch (Oct 1996) steps on
  their documented onset dates (dates HIGH; curve shape N/E). The **weak**
  coupling magnitudes are anchored to the media-paradox cluster — Allcott 2020 /
  Guess 2023 (above), Boxell, Gentzkow & Shapiro 2017 (age-gradient; the model
  has no age structure, a documented limitation), Prior 2013 / Guess 2021
  (heavy-tailed diets) — catalogued in `docs/model_blindspots.md` §1.

### 2.7 Comparative / scope
- **Gidron, N., Adams, J., & Horne, W.** (2020). *American Affective
  Polarization in Comparative Perspective*. Cambridge University Press. —
  Contact works more on affect than other levers; institutional levers move
  issue sorting. Intervention framing + X5 electoral-system context.
- **McCoy, J., & Somer, M.** (2019). Toward a theory of pernicious
  polarization. *Annals AAPSS*. — Cross-national institutional findings;
  two-party / single-country scope caveat (§5.8).
- **Brown, J., & Enos, R.** (2021). The measurement of partisan sorting for 180
  million voters. *Nature Human Behaviour*. — Geographic-sorting measurement
  context.

---

### 2.8 Belief-system structure & constraint (the multi-issue / MHV anchors)

Added at MHV T0.2 (2026-06). These anchor the **multi-issue state rebuild**
(MHV S2): the dimension-parametric issue vector, the emergent constraint
operator replacing the scheduled identity-sorting trajectory, and the
constraint observables added to the audit battery (T0.5). Until S2 lands,
their engine footprint is the S1 covariance-signature pilot
(`scripts/audit/pilot_cov_signature.py`) and the battery design.

- **Baldassarri, D., & Gelman, A.** (2008). Partisans without constraint:
  Political polarization and trends in American public opinion. *AJS* 114:408. —
  Through 2004, Americans polarized via *partisan alignment* of issues, not
  rising *issue–issue constraint*. Anchors (a) the Phase 9 published-table
  fallbacks (Tables 2–3 cross-issue correlations, §1 above) and (b) — extended
  role at T0.2 — the **B&G dual-index target**: partisan alignment and issue
  alignment tracked as *separate* observables (S1 pilot `bg_partisan` /
  `bg_issue_pooled`; T0.5 battery; the S2 calibration target pair). **Realized
  at S4/T4.0:** the published-table fallback is now *replaced* by a per-year
  series computed from the raw GSS cumulative file —
  `scripts/build_gss_constraint_series.py` → `data/mhv/gss_constraint_series.json`,
  the same `|corr|` definitions as the engine battery (issue alignment
  `constraint_index`; partisan alignment `bg_partisan_align`). Measured trend
  reproduces the paper's headline — party sorting rises faster than issue
  constraint (1980→2020: partisan 0.25→0.61, +0.0085/yr; constraint 0.28→0.60,
  +0.0057/yr) — and is the S4 calibration target for the emergent `ConstraintOp`.
- **Treier, S., & Hillygus, D. S.** (2009). The nature of political ideology in
  the contemporary electorate. *POQ* 73:679. — Bayesian IRT: mass ideology is
  2-dimensional (economic ≠ social); cross-pressured citizens self-label
  "moderate". Anchors the 2-axis compass justification (§1 fallback tables) and
  — extended role at T0.2 — the **2-factor loading design** for the MHV issue
  vector and the econ/cultural item blocks used in the S1 pilot's real-IC path
  (ANES VCF items).
- **Boutyline, A., & Vaisey, S.** (2017). Belief network analysis: A relational
  approach to understanding the structure of attitudes. *AJS* 122:1371. —
  Attitude networks have measurable structure with political identity at the
  center. Anchors the **constraint-index observable** (mean |pairwise issue r|,
  within-party PR) in the S1 pilot and the T0.5 battery v2 stat registry.
- **DellaPosta, D.** (2020). Pluralistic collapse: The "oil spill" model of
  mass opinion polarization. *ASR* 85:507. — 44 years of GSS as an evolving
  belief network: polarization spread by absorbing previously cross-cutting
  attitudes ("oil spill"), not by deepening existing divides. **The design
  anchor for the S2 `constraint_op`** (network-local, self-reinforcing
  correlation growth — the operator piloted in S1).
- **Kozlowski, A. C., & Murphy, J. P.** (2021). Issue alignment and partisanship
  in the American public: Revisiting the "partisans without constraint" thesis.
  *Social Science Research* 94:102498. — Documents a marked rise in
  inter-attitude correlation 2004–2016, revising B&G's picture. Anchors the
  **constraint-slope target** the S2 emergent operator must reproduce (rate
  prior for bounded collapse).
- **Hare, C.** (2022). Constrained citizens? Ideological structure and conflict
  extension in the US electorate, 1980–2016. *BJPS* 52:1602. — Dynamic IRT:
  mass attitudes became markedly more structured via conflict extension.
  Companion constraint-trend target to Kozlowski & Murphy. *(Correction logged
  at T0.2: the MHV planning docs cited "Kozlowski et al., Constrained
  Citizens?" — that title is Hare's; the two papers are split here.)*

### 2.9 Methodology (simulation-based inference)

- **Talts, S., Betancourt, M., Simpson, D., Vehtari, A., & Gelman, A.** (2018).
  Validating Bayesian inference algorithms with simulation-based calibration.
  arXiv:1804.06788. — The SBC rank-uniformity check. Anchors the MHV T0.5
  inference-hygiene gate: no posterior shrinkage from the identifiability
  harness is quoted without an SBC + coverage pass
  (`scripts/audit/sbc_harness.py`; `methods.md` §5.16).

## 3. Intervention literature (X1–X7)

Full envelopes, mismatch analyses, and knob-level provenance tags live in
[`phase10_interventions/redesign_briefs.md`](phase10_interventions/redesign_briefs.md).
This is the compact map of which sources anchor which lever. Measured buckets:
[`results/phase10_results.md`](results/phase10_results.md).

| Lever | Mechanism | Primary anchors | Supporting / envelope |
|---|---|---|---|
| **X1** Show the other side | `BacklashRepulsion` + identity weight | Bail 2018 (backfire) — **grade LOW/CONTESTED (T0.2)** | Combs et al. 2023 (anonymous reduces); Mutz 2018 (threat); Settle 2018; Levendusky & Stecula 2021; Yeomans et al. 2020. **Counterweights:** Guess & Coppock 2020 (*BJPS* 50:1497 — no backlash in 3 experiments); Wood & Porter 2019 (*Political Behavior* 41:135 — backfire "elusive" across 52 issues, 10k+ subjects). These two anchor the LOW/CONTESTED grade on X1's backfire reading (methods.md §5.13); beside it sits the 99.8% affect-gate firing rate (methods.md §5.4.bis). |
| **X2** Fix the algorithm | `BC.affect_weight = 0` (null) | Guess et al. 2023 (Meta-2020); Allcott et al. 2024 | Stray 2022 (bridging, theoretical); Hangartner et al. 2021; Munger 2017 |
| **X3** Quit cable news | zero Fox/MSNBC `media_diet` | Allcott et al. 2020 (quit-analogue); Levendusky 2013 | Broockman & Kalla 2024 (switching, X3b candidate); DellaVigna & Kaplan 2007; Levendusky & Malhotra 2016 |
| **X4** Bipartisan dialogue | identity-prime + threat reset | Voelkel et al. 2024 (best single anchor); Levendusky 2018 | Bursztyn & Yang 2023; Santoro & Broockman 2022; Kalla & Broockman 2020; Mutz 2006; Levendusky 2021; Mason 2018 (resistance) |
| **X5** Deprogramming & exit programs | treated 50% of faction-tagged agents exit (clear `faction_center` → FactionAnchor self-gates off) **and** have `identity_strength` halved (weaker PartyPull) | Horgan 2009; Koehler 2017; Berger 2018 (deradicalization mechanism) | Gielen 2019 (program-efficacy review — modest/contested); Bjørgo & Horgan 2009. *[N] magnitude; replaces the retired "ranked-choice voting" lever (drift-multiplier arm inert on the S3 data-fed path; MHV S5 T5.0). Measures null — targeted-tail counter-extremism doesn't scale to the aggregate* |
| **X6** Shared neighborhoods/workplaces | +1 cross-party cooperative tie + affect/threat reset | Pettigrew & Tropp 2006; Mousa 2020; Allport 1954 | Lowe 2021; Paluck et al. 2021; Enos 2014 (backfire under threat); Scacco & Warren 2018; Mutz 2006 |
| **X7** Correct the perception gap | `PerceptionUpdate` reset + accelerated correction | Ahler & Sood 2018; Voelkel et al. 2024 | Lees & Cikara 2020; Druckman et al. 2022 (decay); Moore-Berg et al. 2020; Yudkin et al. 2019 (More in Common) |

---

## 4. Causal-model & decomposition evidence

These sources back the **timeline copy** and the evidence grading
(HIGH/MED/LOW/CONTESTED/MARKER), not the engine rules directly. Full grading and
confidence map: [`polarization_causal_model.md`](polarization_causal_model.md).

**Cohort vs period vs within-person decomposition.** Green, Palmquist &
Schickler *Partisan Hearts and Minds* (party-ID continuity r ≈ .97); Kuziemko &
Washington 2018 (*AER*, Southern realignment = race-driven conversion); Ghitza,
Gelman & Auerbach 2023 (*AJPS*, formative-years imprinting ~ages 14–24);
Rosenfeld 2017 (*Socius*) & Baunach 2011 (*SSM*, issue-attitude liberalization ~⅓
replacement); Phillips 2022 (*Political Behavior*), Stoker 2020, Boxell,
Gentzkow & Shapiro 2017/2021 — three independent APC studies converging that
**affective polarization is a period effect** (out-party warmth fell across all
cohorts at once, fastest among the oldest/least-online); Firebaugh (linear
decomposition method).

**Top-down elite→mass chain.** McCarty, Poole & Rosenthal *Polarized America*;
Hacker & Pierson "Confronting Asymmetric Polarization"; Mann & Ornstein;
Theriault *The Gingrich Senators*; Carmines & Stimson *Issue Evolution*;
Levendusky *The Partisan Sort*; Zaller *Nature and Origins of Mass Opinion*
(receive-accept-sample); Hetherington "Resurgent Mass Partisanship"; Hopkins
*The Increasingly United States* (nationalization); Bawn et al. "A Theory of
Political Parties" (elite↔activist/donor feedback). Contested framing: Fiorina
*Culture War?* (sorting ≠ a deeply polarized public).

**Affective polarization & media.** Iyengar, Sood & Lelkes 2012 ("Affect, Not
Ideology"); Iyengar et al. 2019 (ARPS review); Mason 2015/2016/2018; Abramowitz
& Webster 2016 (negative partisanship); Martin & Yurukoglu 2017 (cable causal
effect); Allcott et al. 2024 (Meta-2020 deactivation ~null); Mutz 2018 + Morgan
2018 (status threat, contested); Ahler & Sood 2018 (misperception); Iyengar &
Westwood 2015 (partisan discrimination); Voelkel et al. 2023 (affect ≠
anti-democratic attitudes — the decoupling finding).

**Contested / rival explanations carried honestly.** Shafer & Johnston
(economic-development rival to race-primacy on Southern realignment); Morgan 2018
(economics vs Mutz status threat); Fiorina (sorting vs radicalization).

---

## 5. Citation verification status

High-confidence, venue-pinned (safe to cite anywhere): Allport 1954, Bail 2018,
Iyengar 2019, Mason 2018, Pettigrew & Tropp 2006, McCarty et al. 2006,
Hetherington 2001, Levendusky 2013/2018/2021, Mutz 2006/2018, Drutman 2020,
Ahler & Sood 2018, Druckman 2022, Lees & Cikara 2020, Enos 2014, Paluck et al.
2021, McGhee & Shor 2017, Reilly 2018, DellaVigna & Kaplan 2007, Hangartner
2021, Munger 2017, Settle 2018, Bursztyn & Yang 2023, Gidron/Adams/Horne 2020,
Moore-Berg 2020, Finkel 2020, Guess 2023, Nyhan 2023, Allcott 2020.

Verified at MHV T0.2 (2026-06, DOI-pinned): DellaPosta 2020 (*ASR* 85:507),
Guess & Coppock 2020 (*BJPS* 50:1497), Wood & Porter 2019 (*Political
Behavior* 41:135), Boutyline & Vaisey 2017 (*AJS* 122:1371), Treier &
Hillygus 2009 (*POQ* 73:679), Bonica 2014 (*AJPS* 58:367) + DIME v4.0,
Kozlowski & Murphy 2021 (*SSR* 94:102498), Hare 2022 (*BJPS* 52:1602),
Baldassarri & Gelman 2008 (*AJS* 114:408). Note the §2.8 correction: the
title "Constrained Citizens?" belongs to Hare 2022, not Kozlowski.

**Pending venue/year verification** (flagged in redesign_briefs.md §"Citation
verification TODO" — pin before treating as load-bearing): Voelkel et al. 2024
(*Science Advances*?), Allcott et al. 2024 (venue), Combs et al. 2023 (*PNAS*?),
Broockman & Kalla 2024 (NBER WP / forthcoming venue), Lowe 2021 (*AER*?),
Atkinson et al. 2023 (Maine RCV venue), Santoro & Broockman 2022, Kalla &
Broockman 2020 (*APSR*?), Yeomans et al. 2020 (*OBHDP*), Yudkin et al. 2019
(More in Common, *Perception Gap*).

---

*This index is descriptive bookkeeping — it records sources the model already
uses. The formal flat bibliography is in [`methods.md`](methods.md) §"Citations".
When you add a new anchor to the engine, add it here (with what it anchors) and
to the methods.md list.*
