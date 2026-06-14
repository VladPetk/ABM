# Model Blindspots Register

This document registers the structural and empirical **blindspots** identified in the `polarlab` / `"Calm to Camps"` Agent-Based Model (ABM) of US political polarization (1980–2025). These blindspots represent areas where mathematically convenient model rules conflict with or fail to represent established peer-reviewed social science literature.

---

## 1. The Media/Internet Paradox (Age-Gradient Mismatch)
*   **The Model Rule:** Bounded confidence influence, selective exposure, and media consumption (e.g., online media-diet algorithms) are modeled as primary drivers of partisan sorting and affective polarization.
*   **The Empirical Finding:** 
    *   US affective polarization grew fastest among older demographics (65+) who are the *least* likely to use the internet or social media (*Boxell, Gentzkow & Shapiro 2017 PNAS*).
    *   Replacing algorithmic social media feeds with chronological feeds changes exposure but has **zero** detectable short-term effect on affective polarization or ideological extremity (*Guess et al. 2023 Science*).
*   **The Blindspot:** A model that relies heavily on internet exposure, social media algorithms, or online echo chambers as drivers will fail to reproduce the observed age gradient (where the old polarized fastest). The model over-represents the causal weight of online media curation.

## 2. Meta-Perception Decoupling (Intervention Durability decay)
*   **The Model Rule:** Correcting agents' misperceptions of the out-party's positions or animus reduces downstream affective polarization.
*   **The Empirical Finding:** 
    *   While informational corrections reliably update *metaperceptions* and reduce support for violence (*Mernyk et al. 2022 PNAS*), their downstream impact on partisan animosity and general affective polarization is small, highly inconsistent, and decays rapidly—frequently showing null results in longitudinal follow-ups (*Voelkel et al. 2024 Science Megastudy*; *Dias et al. 2024 PNAS Nexus*).
*   **The Blindspot:** Modeling informational corrections as a durable or dominant depolarizing force is structurally ungrounded. In reality, correcting out-party beliefs does not translate into stable improvements in affective warmth.

## 3. Mass-Elite Feedback (The Extremist Penalty & Leapfrogging)
*   **The Model Rule:** Candidates and elites shift positions smoothly to track constituent medians or party centers (Hotelling-Downs spatial representation).
*   **The Empirical Finding:** 
    *   Nominating an extremist candidate carries a severe general election penalty of 9–13 percentage points in vote share (*Hall 2015 APSR*).
    *   Representation is characterized by "leapfrogging," where elite members of Congress are systematically more extreme than their constituents, and party flips cause a seat's representative to jump from one ideological extreme to the other (*Bafumi & Herron 2010 APSR*).
*   **The Blindspot:** A spatial candidate selection mechanism that tracks median constituents without modeling the severe electoral cost of extremism or candidate self-selection (moderates opting out of running, *Thomsen 2017*) represents a major structural blindspot.

## 4. Identity Directionality (The Politics-to-Identity Reverse Flow)
*   **The Model Rule:** Social identities (e.g., religious affiliation, ethnicity, lifestyle sorting) are treated as static independent variables that drive political sorting.
*   **The Empirical Finding:** 
    *   Americans change their religious identification, ethnic identity, and class alignment in panel data over time to fit their prior partisan/ideological alignments (*Egan 2020 AJPS*; *Margolis 2018*).
*   **The Blindspot:** Treating social sorting as unidirectional (identity → politics) ignores the reverse-causal feedback loop where partisan identity reshapes social identity. However, the effect size is small (confined to a thin tail of switchers), meaning a model that induces wholesale identity shifting would overstate the effect.

## 5. Economic Inequality Causal Over-attribution
*   **The Model Rule:** Macroeconomic inequality (e.g., Gini index, top income shares) is modeled as a direct causal driver of affective polarization.
*   **The Empirical Finding:** 
    *   While DW-NOMINATE polarization and Gini inequality are highly correlated over the 20th century, the causal arrow is circumstantial (*McCarty, Poole & Rosenthal 2006*).
    *   Cross-national trends show that other OECD countries with similar inequality trends did not experience rising affective polarization; indeed, some depolarized (*Boxell, Gentzkow & Shapiro 2024 REStat*).
*   **The Blindspot:** Treating inequality as a direct driver of agent-level affect oversimplifies US-specific institutional and racial dynamics, turning a correlational macro-statistic into an ungrounded agent-level rule.

## 6. Asymmetric Elite Dynamics
*   **The Model Rule:** Political parties polarize symmetrically in issue space.
*   **The Empirical Finding:** 
    *   Congressional polarization is highly asymmetric, with Republicans moving significantly further from the center than Democrats in DW-NOMINATE space. This is driven by self-reinforcing intraparty feedback rather than symmetric external drift (*Leonard et al. 2021 PNAS*).
*   **The Blindspot:** Modeling symmetric drift rules ignores the asymmetric feedback mechanisms unique to the party institutions.

## 7. Positional Sorting Is Imposed, Not Emergent (The "Constant Pushing" Problem)
*   **The Model Rule:** Party separation and identity alignment over 1980→2025 are produced by the `PartyPull` rule dragging agents toward party centers that are **supplied exogenously** as an empirical ANES voter-centroid time series (`data/mhv/party_centroid_series.json`, scaled by `elite_lead_factor`). Agents are Friedkin–Johnsen–anchored, so most barely move from their 1980 position.
*   **The Diagnostic Finding:**
    *   A freeze decomposition on the fitted shipped config (`docs/results/honesty_budget.json`; `scripts/audit/t35_budget_brake.py`, 6 seeds) shows that with the data-fed series frozen at its 1980 value, **party separation does not rise at all** (emergent fraction ≈ 0% / ≈100% input-carried) and **identity alignment is ≈2% emergent / 95% input-carried**. Only **affective polarization is genuinely emergent (≈87%)** — it collapses even when positional separation is held flat, consistent with the empirical fact that affect polarized far more than issue positions did.
*   **The Blindspot (as originally diagnosed):** The model **did not demonstrate that positional sorting self-organizes** — it reproduced the empirical party trajectory it was handed. Because the fed series was *voter* centroids and the measured metric is *voter* separation, the positional reproduction was close to a **conditional replay**. Two roots: (1) a deliberate S3 design choice to feed *real data* rather than hand-draw the elite trajectory; (2) a deeper tension — individual-level **stability** (FJ anchoring) structurally limits self-organized macro change, so the change had to be imposed or arrive via cohort turnover.
*   **RESOLVED (emergence-recovery E5, 2026-06; methods §5.29).** Positional sorting now **emerges** from an endogenous activist→elite→mass feedback loop (`abm/rules/activist_elite.py::ActivistEliteCue`): the fed `PartyCentroidSeries` and the cohort-reseed-at-centroid are both gone (`endogenous_elite=True`, `data_fed_elite=False` in the canonical `ANES_FULL_KWARGS`; the pre-E5 config is preserved as `ANES_FULL_FED_KWARGS`). Re-measured honesty budget (`honesty_budget.json`, 6 seeds): **party_sep emergent 1.00** (loop-attributable — freezing the loop collapses sep to the 1980 seed), **identity_alignment 0.95**, both ~0% input-carried (were ≈0% / 2% emergent). Affect unchanged (0.87, its own mechanism). The ANES scorecard (18/24) and the intervention buckets are preserved; the web honesty panel now reports the emergence.
*   **Residual caveats (the honest cost — now the open part of this entry):** (a) the loop's **timing** is set by an exogenously-calibrated activist-mobilization schedule, not predicted — the four-cut **holdout fails the temporal cut** (`e5_holdout.md`, 1/3; the FED config passed 3/3 only by feeding the answer), and the budget shows only ~38% of party_sep is the spontaneous loop floor (~62% rides the fitted forcing). So the model now **explains the mechanism but not the timing**. (b) The single-axis (`align_u`) amplification direction **over-correlates the compass axes** (corr(x,y)~0.78 vs ANES ~0.5–0.6; holdout cut-2 issue-corr slope 1.62× GSS) and runs the 2010 bucket slightly hot. **Status: the bottom-up-emergence question is RESOLVED; the open follow-on is the late-timing exogeneity + the axis over-correlation — both candidates for a time-evolving / balanced realignment-direction refinement.**
