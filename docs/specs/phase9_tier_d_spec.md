# Phase 9 Tier D — Axis-symmetry rebalance

*Date: 2026-05-27. Authors: Vlad + Claude (paired). Builds on
`phase9_axis_symmetry_audit.md` and `phase9_axis_ratios.md` (both
under `docs/research/`).*

---

## 0. Problem

Tier A (factional ICs) and Tier C (FactionAnchor rule) both failed to
move the Phase 9 Wasserstein metric meaningfully toward the empirical
KDE targets, despite Tier C passing the §11 cells gate. Diagnosis: the
y-axis dispersion in the simulated cloud (`var(y) ≈ 0.045`) is roughly
6× too small relative to empirical (`var(y) ≈ 0.27`), and no amount of
faction-anchor tuning recovers it because the gap is **upstream of the
faction mechanism** — the engine is silently x-biased on six
independent levers in `historical_arc.py` and the surrounding
build-time configuration. The rule-level math is axis-symmetric; the
**inputs** are not.

The audit (`phase9_axis_symmetry_audit.md`) catalogued the six levers.
The ratios doc (`phase9_axis_ratios.md`) put empirical numbers on what
each lever's x:y ratio *should* be, lever by lever, with source
citations. This spec is the implementation plan that translates those
numbers into code.

**Headline finding from the ratios doc:** the literature does not
support perfect axis symmetry, but neither does it support the current
3–4× x-dominance. Of the six levers, four want mild x-tilt (~1.25–1.5
: 1), one is undetermined (lever 5 — outlets, swept rather than fixed),
and two want **inverted asymmetry favoring y** (lever 4 — perception
gap; lever 6 — 2016 Trump-coalition shift, which the literature pins
firmly on the cultural axis).

---

## 1. Central-estimate substitutions

All six levers, with current vs new values. Lever 5 (outlets) is left
untouched in the central run and reserved for a follow-up sweep — the
underlying media-bias literature is 1D-only, so a point estimate would
be invented.

| # | Lever | Location | Current | Tier-D central | Empirical anchor |
|---|---|---|---|---|---|
| 1 | Party assignment sigmoid | `historical_arc.py:425`, `cohort_replacement.py:171` | `sigmoid(K · x)` | `sigmoid(K · (0.55 x + 0.45 y))` | Mason 2018 app. B (~1.1:1) |
| 2 | `PARTY_CENTERS_1980` | `historical_arc.py:83-84` | `(±0.30, ±0.08)` | `(±0.30, ±0.20)` | Hare 2015; Treier-Hillygus 2009 (~1.5:1) |
| 3 | Initial-position side draw | `historical_arc.py:415-416` | `side · 0.15` on x; zero on y | `side · 0.15` on x; `side_y · 0.12` on y with ρ≈+0.20 coupling | ANES §3.5.1 (~1.25:1) |
| 4 | Perception-gap bias | `historical_arc.py:147, 501-505` | `+0.25` on x; zero on y | `+0.20` on x; `+0.25` on y (inverted!) | Ahler & Sood 2018; MiC 2018 (~0.8:1) |
| 5 | Outlet y-spread | `outlets.py:27-33` | max y / max x ≈ 0.65 | *(left at default; sweep planned)* | undetermined (1D-only literature) |
| 6 | 2016 Trump centroid nudge | `historical_arc.py:801` | `(+0.05, 0.00)` | `(+0.02, +0.10)` | Sides/Tesler/Vavreck 2018 fig. 7.3 (~1:4) |

### Lever 3 — coupling fork resolution

The ratios doc flagged whether the y-side draw should be independent of
the x-side draw or weakly coupled (ρ ≈ +0.20, matching the empirical
ANES correlation between economic and cultural placement at 1980).

**Decision: weak coupling ρ ≈ +0.20.** Implemented as a 60/40 draw:
`side_y = side_x` with probability 0.60, `-side_x` with probability
0.40. This gives empirical corr(side_x, side_y) = 0.20 exactly. The
alternative (independent draw, ρ = 0) would understate the 1980
correlation; full coupling (ρ = 1, `side_y = side_x` always) would
overstate it. The 60/40 split is the cleanest one-line implementation
of the empirical anchor.

---

## 2. Cohort replacement (lever 1 mirror)

`cohort_replacement.py:171` carries the same `sigmoid(K · new_x)` party-
assignment line that historical_arc:425 uses for the 1980 build. The
ratios-doc verdict on lever 1 applies equally to new arrivals — keeping
build-time sigmoid asymmetric while leaving the cohort sigmoid x-only
would just re-import the bias every decade as boomers age out.

**Tier D substitution:** when env carries
`tier_d_axis_balance=True`, the cohort sigmoid reads
`sigmoid(K · (0.55 · new_x + 0.45 · new_y))`. When false, behavior is
bit-identical to head.

---

## 3. Gating discipline

The standing constraint is that the **73 sacred pillar tests must stay
green bit-identically**. None of the six levers may change pillar
runtime behavior. Implementation discipline:

- A new build_engine kwarg `tier_d_axis_balance: bool = False`. When
  False, every code path is bit-identical to current head.
- The kwarg is propagated to the env (`env.attrs["tier_d_axis_balance"]
  = True`) so downstream rules and event handlers can read it.
- Cohort replacement (lever 1 mirror) and the 2016 Trump event (lever
  6) read the env flag; when False, they execute the pre-Tier-D code
  path.
- `PARTY_CENTERS_1980` (lever 2) is read at build time only; a new
  constant `PARTY_CENTERS_1980_TIER_D` carries the rebalanced values.
- Perception-gap constants (lever 4) get sister constants
  `PERCEPTION_EXTREME_BIAS_X` and `PERCEPTION_EXTREME_BIAS_Y`. The
  legacy `PERCEPTION_EXTREME_BIAS = 0.25` is preserved unchanged for
  the False path.

---

## 4. Sweep plan (post-central)

After the central run reports per-decade Wasserstein and §11 tally, we
identify levers that look off (either over- or under-shooting their
contribution) and run targeted ±30% sweeps. Anticipated candidates:

- **Lever 2** (party centers): sweep y at {0.15, 0.20, 0.25}.
- **Lever 4** (perception gap): sweep y at {0.20, 0.25, 0.30}.
- **Lever 5** (outlets): sweep y-spread multiplier at {0.7, 1.0, 1.3}
  applied to the y-coordinates of `US_MEDIA_OUTLETS_2024`.
- **Lever 6** (Trump nudge): sweep y at {0.05, 0.10, 0.15}.

Single-lever sweeps at 5 seeds each, holding the other levers at
central. Blessed winner re-run at 9 seeds.

---

## 5. Gates

Tier D is considered to have shipped when:

1. **Pillar bit-identity:** 73 sacred tests green at `tier_d_axis_balance=False` default.
2. **§11 cells gate:** ≥18/24 cells in band at the central or blessed-sweep config.
3. **Wasserstein improvement:** total w2 (sum across 5 decades) drops by ≥15%
   vs the Tier C blessed config (`phase9_tier_c_blessed_score.json`).
4. **No regression on 1980:** 1980 initial-condition §11 cells stay all-in-band
   (4/4 — variance, constraint, party_sep, within_party_sd).

If any of (2)–(4) fails after the sweep, the result is recorded as
`tier_d_best_effort` rather than `tier_d_blessed`, with the
shortfall documented in `docs/results/phase9_results.md`.

---

## 6. Rollout

1. Spec (this doc).
2. Code changes in `historical_arc.py` + `cohort_replacement.py` (gated on flag).
3. `scripts/phase9_tier_d_central.py` — 9 seeds at central estimates.
4. Pillar regression check.
5. Run central, inspect output.
6. Sweep outlier levers (only if step 5 indicates).
7. Bless winner, update `docs/methods.md` + `docs/results/phase9_results.md`.
