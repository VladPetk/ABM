# 1996 overlap quantified + blindspot priority ranking (2026-06)

Analysis-only study answering two questions: (1) is the model's heavy 1996 D–R
overlap *correct* or *excess*? and (2) which live blindspots should we fix next,
ranked by consequence × tractability. Reproduce: `validation/overlap_1996.py`
(figure `validation/figures/overlap_1996_model_vs_anes.png`); battery / honesty-budget
inputs as cited.

---

## Part 1 — The 1996 overlap is MOSTLY FAITHFUL, with a modest econ-driven excess

Formal D–R overlap metrics, model (published canonical seed 1, tick 48) vs **raw ANES
1996 respondents** (weighted; `data/phase9_empirical/derived/respondent_coordinates.csv`):

| metric | ANES (real) | model (seed 1) | model − ANES |
|---|---|---|---|
| centroid sep (2D) | 0.540 | 0.478 | −0.063 |
| OVL overlap coef (0=disjoint,1=identical) | 0.482 | 0.541 | **+0.060 excess** |
| Bhattacharyya BC | 0.768 | 0.845 | +0.077 |
| LDA position→party accuracy | **0.760** | 0.695 | −0.065 (less separable) |
| R in lower-left (prog-redist) quadrant | **6.8%** | 18.7% | **+11.9 pts** |
| R on Dem-majority turf | 26.3% | 33.6% | +7.3 pts |

**Answer: it is both — but mostly correct.** Real 1996 *was* genuinely weakly sorted:
ANES OVL is 0.48 (the clouds really overlap ~half), a position→party classifier only
reaches **76%** (≈24% of real partisans sit in the "other side's" region), and **26%
of real Republicans already sat on Dem-majority turf**. So the bulk of the overlap the
eye sees is **faithful**. On top of that the model adds a **modest excess** (+0.06 OVL,
−0.065 LDA), and the most visible symptom is **R-in-LL 18.7% vs 6.8%**.

**Decomposition of that R-in-LL = 18.7%:**
- **6.8% faithful** (real ANES).
- **~5.5 pts model-systematic excess** — the multi-seed ensemble R-in-LL@1996 is
  **12.3%** (range 7–19%), vs ANES 6.8%.
- **~6.4 pts seed-1 realization** — seed 1 (18.7%) sits at the high end of the model's
  range; it was picked as representative on *sep / econ-gap*, but R-in-LL is noisier.

**The residual is ECONOMIC, not cultural.** The sep shortfall (−0.063) is almost all
econ (econ gap model 0.378 vs ANES 0.445 = −0.067; cult gap 0.293 vs 0.307 = −0.014):
the model's Republican cloud sits ~0.05–0.07 too far *left economically* at the mid-90s,
spilling more mass into the redistributive quadrant. Ensemble econ@1996 0.40 vs ANES
0.445 is within ~1.5σ — consistent with "econ matches arc-wide" (#10); this is a small
mid-90s residual, not a structural miss. Figure: `overlap_1996_model_vs_anes.png`.

### Part 1b — Ensemble static-compass convention (presentation-only; abm/ unchanged)

> **SUPERSEDED (2026-06):** the seed-1-animation / ensemble-static split below was
> replaced by the **Method-B published baseline** — the web ANIMATION itself is now
> the ensemble (8 seeds pooled → reproducible uniform 250-agent cross-seed subsample;
> `docs/results/method_ab_verdict.md`, `scripts/methodb_baseline.py`), with the
> character/protection scaffolding removed at source. No more single high-realization
> seed; the published cloud carries the model's true dispersion AND ensemble center.

Because seed 1 sits at the high end of the model's R-in-LL range (a single
realization), the **static/reference compass and the headline overlap/separation
numbers now use the model's ENSEMBLE**: agents **pooled across clean seeds 0-7 into one
representative density** (a legitimate object - the model's own mixture distribution;
the pooled centroids / gaps / R-in-LL share equal the multi-seed ensemble center). The
web **animation keeps representative seed 1** - per-agent trajectory continuity,
characters, and ghost-fade are **not poolable across seeds**, so `cc-data.js` is
unchanged and stays internally self-consistent. This is **representativeness, not
warming toward ANES** - every ensemble metric lands on the model's own center and stays
short of ANES. Reproduce: `validation/render_ensemble_compass.py`; figure
`validation/figures/ensemble_compass_1996_2020.png`.

| year | metric | seed 1 (animation) | **ensemble (static)** | ANES |
|---|---|---|---|---|
| 1996 | econ-gap | 0.378 | **0.401** | 0.445 |
| 1996 | cult-gap | 0.293 | **0.274** | 0.307 |
| 1996 | sep | 0.478 | **0.485** | 0.540 |
| 1996 | **R-in-LL** | 18.7% | **12.4%** | 6.8% |
| 2020 | econ-gap | 0.707 | **0.767** | 0.838 |
| 2020 | cult-gap | 0.645 | **0.637** | 0.783 |
| 2020 | sep | 0.957 | **0.997** | 1.147 |
| 2020 | R-in-LL | 3.6% | **3.7%** | 7.1% |

The ensemble matches the model's true center measured earlier (econ@1996 ~0.40,
R-in-LL ~12.3%, sep@2020 ~0.999): the 1996 R-in-LL drops 18.7% -> **12.4%** (removing
seed 1's high realization) yet stays **well above ANES 6.8%** - the model's genuine
mid-90s econ residual is preserved, not papered over.

---

## Part 2 — Blindspots ranked by consequence × tractability

Error attribution from the from-scratch battery, the realism scorecard (15/24; 9
out-cells), and `honesty_budget.json`. The realism failures decompose as **5 AFFECT
cells (cold by 0.10–0.14 every wave) + 4 constraint/sep cells (3 marginal ≤0.01, 1 mild
#10 overshoot)** — i.e. affect dominates the measured error.

| # | Blindspot | Measured consequence | Axis / years | Tractability | Priority |
|---|---|---|---|---|---|
| **1** | **Affect too cold** | **Largest measured error: out-party warmth ~0.10–0.14 too cold at EVERY wave; 5 of 9 realism out-cells; the main scorecard miss (17/24 & 15/24).** Orthogonal to positional overlap. | affect subsystem, whole arc | **EASY–MEDIUM** — isolated subsystem (AffectiveUpdate seed + contact-LR + saturation); fix direction already scoped in the affect-band-grounding work; does **not** touch positions/econ | **HIGH — cheapest big win** |
| **10** | **Cultural mis-pacing (fixed-direction loop)** | Biggest *positional* error: cult gap +0.11–0.16 over-separated 1986–90, **−0.11 undershoot at the 2020 peak** (0.78 real vs ~0.67 model), misses the 2012–2020 surge; the 2010 sep over-shoot cell. | cultural axis; early + 2012–2020 | **HARD** — only honest fix is the **parked structural axis-decoupling** (axis-specific loop direction / 2nd cultural loop); the cue-schedule hybrid is falsified (`ee10451`) | **HIGH consequence, EXPENSIVE** |
| — | 1996 econ residual (loop mid-90s gain) | R-in-LL ensemble 12.3% vs 6.8% (+5.5 pts); econ gap 0.40 vs 0.445 (−0.045). The Part-1 finding. | econ axis, mid-90s | LOW-value — econ matches within 1–2σ arc-wide; touching it risks the S4 sep-ridge, and econ is settled | **LOW (leave)** |
| **7** | Positional sorting forcing-dependent (saturation-ratchet "dark matter") | **Not a reality-error** — endpoints match. `party_sep` & `identity` are 72% forcing-driven (free_flowing 0.28). A documented *property* (latent re-label ceiling 0.66 ≪ 1.11 end-state). | honesty property | HARD & by-design — proven a property, not a shortcut | **LOW (documented, not a fix target)** |
| **6** | Asymmetric elite dynamics | Small aggregate error — per-party 2025 centroids match in the realism battery; a mechanism-fidelity gap, not a measured miss | elite mechanism | MEDIUM | **LOW** |

(#8 cultural common-mode and #9 econ common-mode are **already fixed**; affect's honesty
budget is 0.94 free-flowing, i.e. affect is its own mechanism — recalibrating it does
not perturb the sorting channels.)

### Net recommendation — the two highest-leverage next fixes

1. **#1 affect-too-cold — do this first (cheap, biggest measured error).** It is the
   single largest source of measured model-vs-reality error (5/9 realism out-cells,
   ~0.10–0.14 every wave), it is an **isolated subsystem** with the fix direction
   already scoped, and it is **orthogonal to the settled positional/econ work** — so it
   improves the realism scorecard (15/24 → potentially 19–20/24) at low risk and zero
   blast radius on positions. Caveat: it does **not** change the D–R *overlap* the user
   is looking at (affect ≠ position).

2. **#10 cultural mis-pacing — the real positional fix, but a deliberate larger
   investment.** It is the biggest *positional* error and the only one that moves
   separation/overlap meaningfully (the 2012–2020 cultural surge, −0.11 at the 2020
   peak). Its only honest fix is the **parked structural axis-decoupling** — schedule it
   when there's appetite for an architecture change with its own spec + measure-then-bless.

**On the user's 1996-overlap question specifically:** there is little to "fix" at 1996 —
~6.8% R-in-LL is faithful, the model's systematic excess is only ~5.5 pts (econ, mid-90s,
within 1–2σ), and the rest of the visible 18.7% is seed-1 realization noise. The mid-90s
parties genuinely overlapped; the model is approximately right there. The positional
error worth attacking is **late (2012–2020 cultural, #10)**, and the cheapest overall
win is **affect (#1)**.
