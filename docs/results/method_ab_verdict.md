# Publish representation: Method A vs B head-to-head (2026-06)

Empirical comparison of two candidate 250-agent published clouds from the canonical
econ-ON config (merged `model-reality-validation` HEAD), against two references.
Analysis only; `abm/` untouched. Reproduce: `validation/method_ab_headtohead.py`
(figures `validation/figures/method_ab_1996.png`, `…_2020.png`).

- **Method A — per-index average:** for each agent index *i*, mean its 2D position
  across K=8 clean seeds (per-index majority party).
- **Method B — ensemble subsample:** pool K×250 = 2000 agents, draw a **uniform**
  250-agent cross-seed subsample (fixed RNG for reproducibility; **no nudge** — the
  task allowed nudging toward the *model's* center, but uniform is the honest default).
- **Ensemble (truth):** the full 2000-agent pool — the ground truth for "faithful
  representation of the model."
- **ANES:** raw weighted respondents — the external realism check.

## Side-by-side (A · B · Ensemble · ANES)

| metric | 1996 A | B | **Ens** | ANES | 2020 A | B | **Ens** | ANES |
|---|---|---|---|---|---|---|---|---|
| **CENTROID** econ gap | 0.268 | 0.367 | **0.401** | 0.445 | 0.351 | 0.796 | **0.767** | 0.838 |
| cult gap | 0.186 | 0.184 | **0.274** | 0.307 | 0.283 | 0.664 | **0.637** | 0.783 |
| centroid sep | 0.326 | 0.410 | **0.485** | 0.540 | **0.451** | 1.037 | **0.997** | 1.147 |
| **DISPERSION** R wp-SD econ | 0.145 | 0.396 | **0.408** | 0.329 | 0.122 | 0.287 | **0.295** | 0.347 |
| R wp-SD cult | 0.149 | 0.395 | **0.411** | 0.347 | 0.127 | 0.275 | **0.282** | 0.395 |
| pooled wp-SD econ | **0.136** | 0.383 | **0.382** | 0.318 | **0.139** | 0.290 | **0.298** | 0.335 |
| pooled wp-SD cult | **0.140** | 0.384 | **0.394** | 0.361 | **0.130** | 0.284 | **0.292** | 0.381 |
| OVL overlap | 0.296 | 0.580 | **0.589** | 0.482 | 0.190 | 0.147 | **0.179** | 0.215 |
| Bhattacharyya | 0.589 | 0.885 | **0.852** | 0.769 | 0.428 | 0.306 | **0.346** | 0.410 |
| LDA pos→party acc | **0.862** | 0.653 | **0.704** | 0.760 | **0.898** | 0.929 | **0.915** | 0.904 |
| R-in-LL share | 1.7% | 9.9% | **12.4%** | 6.8% | 2.9% | 7.1% | **3.7%** | 7.0% |

## Variance-collapse quantification (pooled within-party SD ÷ ensemble truth)

| | 1996 econ | 1996 cult | 2020 econ | 2020 cult |
|---|---|---|---|---|
| **Method A / Ens** | **0.36** | **0.35** | **0.47** | **0.44** |
| Method B / Ens | 1.00 | 0.97 | 0.97 | 0.97 |

**Method A collapses within-party SD to ~0.35–0.47× the truth — the published cloud
is ~2–3× too tight.** Method B preserves it within 3%. The collapse is worst where
the hypothesis predicted, but is severe at both years.

## Verdict — Method B. Method A fails on BOTH spread AND centroids; do not use it.

Applying the stated criterion (faithfully reproduce the **model's own** distribution,
centroid AND spread, with ANES as the realism check on spread — **never** "centroid
closest to ANES"):

- **Method A is unfaithful on dispersion** — it averages out the seed-to-seed spread,
  collapsing within-party SD to ~0.13–0.15 vs the model's true ~0.29–0.41 and ANES's
  lifelike ~0.32–0.40. The artifact makes the parties look **artificially tight and
  over-sorted**: OVL 0.30 and LDA **0.86** at 1996 (vs ANES OVL 0.48 / LDA 0.76 and
  Ensemble 0.59 / 0.70) — i.e. A shows the parties as *more cleanly separable than
  either the model or reality*, the exact opposite of the heavy overlap both exhibit.
- **Method A also fails on centroids** — and crucially it is *not* "deceptively good
  on location": per-index averaging across seeds that have **diverged** in where each
  index sits pulls every agent toward the cross-seed mean, collapsing the **centroid
  separation** too. At 2020 (max seed divergence) Method A's sep is **0.451 vs the
  ensemble's 0.997** — it halves the separation. So A is bad on both axes of the test.
- **Method B faithfully reproduces the ensemble** — centroids within 250-agent
  sampling noise (sep 0.410/1.037 vs Ens 0.485/0.997) and **dispersion within 3%**
  (wp-SD ratio 0.97–1.00). Its spread matches ANES's lifelike width, so the realism
  check passes: B's overlap (OVL 0.58 @1996) is genuine, not collapsed.

**Honest caveat on B:** a single 250-subsample carries real ~250-agent sampling noise
around the ensemble (e.g. 2020 R-in-LL 7.1% vs ensemble 3.7%, a high draw) — this is
*honest* distributional noise, not a systematic artifact like A's collapse, and its
dispersion stays faithful. If a single representative realization closer to the
ensemble center is wanted, one may draw a few uniform subsamples and keep the one
nearest the **model's** center (never ANES) — optional; uniform is the unbiased default.

**Recommendation: publish Method B (uniform ensemble subsample).** It is the only
250-agent representation that carries the model's true dispersion *and* sits at the
ensemble center — strictly better than a single representative seed (which is one
realization) and categorically better than Method A (which collapses variance into a
deceptively tight, over-sorted cloud that misrepresents both the model and reality).
Nothing shipped — this decides the representation only.
