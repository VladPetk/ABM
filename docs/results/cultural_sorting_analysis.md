# Cultural-axis sorting: empirical root-cause + literature synthesis (2026-06)

Analysis-only study (no engine change) that root-caused the partisan **sorting**
gap empirically and reviewed the causal literature behind the one real divergence
it found — the **cultural-axis mis-pacing**. Companion to blindspot
[#10](../model_blindspots.md) and methods §5.30/§5.31. Reproduce:
`validation/sorting_curve_analysis.py` + `validation/sorting_model_overlay.py`
(figures: `validation/figures/real_sorting_curves.png`,
`validation/figures/model_vs_real_sorting.png`).

---

## 1. The real sorting curve (raw ANES, ±SE; GSS-confirmed)

Partisan gap = R centroid − D centroid, per axis, from the validated ANES anchors
(`validation/anchors_anes.json`; the harness reproduces the ANES derivation exactly).

| year | econ gap ±se | cult gap ±se | sep (2D) ±se |
|---|---|---|---|
| 1986 | 0.321 ±.027 | **0.122** ±.029 | 0.343 |
| 1992 | 0.408 ±.019 | 0.295 ±.022 | 0.503 |
| 1996 | **0.445** ±.021 | 0.307 ±.023 | 0.540 |
| 2000 | 0.388 ±.040 | 0.284 ±.048 | 0.481 |
| 2008 | 0.584 ±.031 | 0.401 ±.035 | 0.708 |
| 2012 | 0.621 ±.011 | 0.519 ±.012 | 0.809 |
| 2016 | 0.702 ±.014 | 0.629 ±.017 | 0.943 |
| 2020 | 0.838 ±.010 | **0.783** ±.011 | **1.147** |
| 2024 | 0.760 ±.013 | 0.734 ±.013 | 1.056 |

**The two axes sort on different schedules.** Economics starts already divided
(0.32 in 1986, post-Reagan) and is steepest ≈**2008**; culture starts near-zero
(0.12) and is **back-loaded**, steepest ≈**2024** with the big jump **2012→2020**.
A raw-GSS cross-check (`helppoor`+`eqwlth` for econ; `homosex`/`premarsx`/`abany`/
`fefam` for culture) independently confirms both shapes (GSS econ gap 0.49→0.85,
steepest ~2006; GSS cultural gap 0.10→0.44, accelerating late) — so this is **not
an ANES artifact**, and the low early cultural gap is robust across both datasets.

## 2. Shape / complexity — smooth backbone, NOT idiosyncratic

A single logistic S-curve already explains **R²≈0.95** on every axis (econ 0.948,
cult 0.943, sep 0.953). Polynomial residuals sit at ~1.5–2× the sampling SE
(residRMSE 0.037–0.054 vs SE 0.023–0.025): a smooth backbone **plus modest
event-locked structure**, not a high-order polynomial. Significant reversals: econ
**3** (notably the real **2020→2024 de-sort, −0.078 = 4.6σ**), cultural just **1**
(near-monotone). **Matching the curve does not require overfitting** — the
"idiosyncratic property" hypothesis is ruled out.

## 3. Model overlay — where it diverges (clean canonical econ-ON, fea5998, seeds 0–2)

Divergence (model − real), averaged by window:

| axis | early 86–92 | mid 94–04 | late 08–24 |
|---|---|---|---|
| **ECON** | +0.013 | **−0.009** | −0.005 |
| **CULT** | **+0.113** | +0.038 | +0.030 |
| **SEP** | +0.074 | +0.018 | +0.017 |

Two specific, robust divergences (per-year):

- **Cultural OVER-separation early (1986–1990): +0.11 to +0.16.** Real cult gap is
  0.12 (1986) / 0.17 (1990); model is 0.25 / 0.34. The model starts the parties far
  too culturally divided — contradicting **both** ANES and GSS.
- **2020-peak UNDERSHOOT (both axes):** real sep peaks 1.147 in 2020, model 1.010;
  real cult 0.783 vs model **0.675** (−0.108); real econ 0.838 vs model 0.750
  (−0.088). The model produces a smooth rise to 2024 and **misses the sharp
  2016→2020 spike-then-revert**.

**Econ is fine — calibration, within 1–2σ** (windowed div ≤0.013; worst per-year
−0.071 @2008, −0.088 @2020, both event spikes). The widely-assumed "mid-90s under-
separation" is **not** supported on the clean model: sep@1996 = 0.549 ≈ real 0.540;
econ@1996 div = −0.032 (~1.5σ).

**Diagnosis:** the model's single smooth mobilization schedule **cannot be
low-early and spike-late on the cultural axis while pacing economics correctly.**
Reality back-loads culture (2012–2020 acceleration); the model front-loads it.

## 4. Presentation caveat (NOT model dynamics)

The **shipped web export runs cooler** than the clean engine, so part of the
*perceived* under-separation is a publish-path / display-EMA artifact, not the
model:

| metric | shipped export | clean engine | real ANES |
|---|---|---|---|
| econ gap @1996 | **0.307** | 0.413 | 0.445 |
| sep @1996 | 0.496 | 0.549 | 0.540 |
| sep @2020 | **0.972** | 1.010 | 1.147 |

The cc-data.js repack also applies a display EMA (smoothing) that further compresses
visible motion. A cheaper, non-mechanism lever on the user's visual complaint is the
export/presentation path itself.

## 5. Literature synthesis — causes of the 2012+ cultural accelerant ("Great Awokening" / "Racing Apart")

**The effect is well-established** (the sharp 2012→2020 liberalization of racial/
cultural attitudes, concentrated on the Democratic/white-liberal side; documented by
Goldberg, coined "Great Awokening" by Yglesias; quantified as partisan "Racing Apart"
by the Voter Study Group). **The CAUSE is not a single consensus** — it is a
consensus **contributing set** with two genuinely unresolved debates.

| Account | Evidence | Cause/correlate | Primacy agreement |
|---|---|---|---|
| **Racialization under Obama** (Tesler, *Post-Racial or Most-Racial?* 2016; *Pol. Psych.* 2015) | Strong panel evidence; race↔party tightened 2008–16 ("spillover of racialization") | Cause (race→party), reciprocal | A driver, not sole |
| **Top-down party→race cue-taking** (Engelhardt, *BJPS* 2021) | Strong cross-lagged panels: whites **align racial attitudes to party**, more over time | Cause, **opposite direction** | **Contests** Tesler → live debate |
| **Media / activist agenda-setting** (~2011–12 social-media inflection; Goldberg's NYT/WaPo "racism" word-frequency +700–1000% 2011→2019) | Strong correlational time-series | Contested cause vs correlate | Possibly *the* prime mover (top-down camp); unsettled |
| **Ferguson 2014 / BLM catalyst** | Strong event-locked (2012→2014 jump) | Proximate trigger | Broad agreement it was a catalyst |
| **Trump activator vs reinforcer** | Acceleration **predates** Trump (2012–14) | Reinforcer, not trigger | Near-consensus |
| **Generational / cohort** (JREP, *White Democrats, Racial Liberalism, and Generational Change*) | Real but secondary; shift too fast for cohort | Contributor | Agreed minor |
| **Affective-sorting feedback** (Mason, *POQ* 2016; *Uncivil Agreement* 2018) | Strong as amplifier | Amplifier, not trigger | Agreed amplifier |
| **Measurement-artifact challenge** (Engelhardt, *AJPS* 2021, "Observational Equivalence") | Shift is observationally equivalent to social-desirability / expressive responding / changing measures | — | Live caveat: part of the magnitude may not be genuine |

**Net:** no consensus single primary cause; a consensus contributing set (Obama
racialization + 2014 Ferguson/BLM + 2011–12 media/social-media salience, amplified by
social sorting, predating Trump). Two unresolved: **causal direction** (Tesler
race→party vs Engelhardt party→race; likely reciprocal) and **how much is real**
(Engelhardt's artifact challenge).

Sources: [NPR](https://www.npr.org/2019/10/01/763383478/how-white-liberals-became-woke-radically-changing-their-outlook-on-race) ·
[Tesler, *Post-Racial or Most-Racial?*](https://press.uchicago.edu/ucp/books/book/chicago/P/bo22961444.html) ·
[Engelhardt, *Racial Attitudes Through a Partisan Lens* (BJPS)](https://www.cambridge.org/core/journals/british-journal-of-political-science/article/abs/racial-attitudes-through-a-partisan-lens/33EF852999B363C20D5A38BA51E57948) ·
[Engelhardt, *Observational Equivalence* (AJPS)](https://ajps.org/2021/10/11/observational-equivalence-in-explaining-attitude-change-have-white-racial-attitudes-genuinely-changed/) ·
[Mason, *A Cross-Cutting Calm* (POQ)](https://academic.oup.com/poq/article/80/S1/351/2223236) ·
[Voter Study Group, *Racing Apart*](https://www.voterstudygroup.org/publication/racing-apart) ·
[JREP, *Generational Change*](https://www.cambridge.org/core/journals/journal-of-race-ethnicity-and-politics/article/white-democrats-racial-liberalism-and-generational-change-progressive-racial-attitudes-and-persistent-contradictions/A554EDE724AA74895071C7FA7995A1AC) ·
[Tablet, Goldberg word-frequency data](https://www.tabletmag.com/sections/news/articles/media-great-racial-awakening)

## 6. Modelability conclusion

The mechanism the top-down literature invokes (**elite/activist cue-taking on
race/culture**) is **endogenous in this engine** — the activist→elite→mass loop
(`ActivistEliteCue` + the activist-mobilization schedule) IS that mechanism. So the
cultural sort *could* emerge from intensifying the **cultural-axis** elite cue. **But
the trigger and timing (why 2012? why the cultural axis?) live outside the model**
(Obama, Ferguson, the social-media inflection). Setting a cultural surge at 2012 and
tuning its amplitude to the observed cultural-gap series would be **timing it by the
answer** — (B) exogenous wearing an (A)-endogenous costume.

**The honest path is a HYBRID** (same bar as the econ mood curve, methods §5.31):
an **exogenous, documented driver whose timing is independent of the ANES cultural
series** (candidates: a Ferguson-2014-anchored mobilization step; an independent
national race-salience series such as the Goldberg word-frequency curve; or the
existing `data_fed_media` penetration series) → fed through the **existing endogenous
cultural cue-loop** → cultural sort **emerges**, with **one fitted amplitude** and
matching a **robust core, not the full (possibly artifact-inflated) magnitude**.
Provenance **L** (elite-cue mechanism) + **E** (exogenously-timed driver) + **N**
(amplitude). It is a *forced, driven* mechanism — strictly better than a bare
hand-drawn cultural forcing (it routes through a real mechanism) but **not** genuine
spontaneous emergence, and should not be sold as such. Any cultural re-pacing must be
**paired with lowering the early (1986–90) cultural differential**, or it overshoots.
The empirical falsify-first test of this hybrid is in `validation/exp_cultural_hybrid.py`
(see its header / the methods note for the verdict).
