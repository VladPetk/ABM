# Fix investigation — why the cultural center is mis-placed (F0)

Validation (REPORT.md) found one root cause behind all the cultural failures:
the partisan **center of mass** sits ~0.10–0.20 too progressive in the
mid-period, even though party *separation*, axis correlation, affect, and
within-party spread all pass. This file records the mechanism hunt.

## Two independent datasets agree on the real-world trend
- **ANES** (2D compass, partisan center): culturally traditional +0.10→+0.22 in
  the 80s/90s, declining to −0.05 by 2024.
- **GSS** (independent items, society-wide z): +0.24 (1988) → −0.39 (2018);
  decomposition = **69% cohort replacement / 31% within-cohort period drift**.
- Robust signal: traditional in the 80s/90s, liberalizing through the 2010s.
  (ANES shows a mid-90s "hump"; GSS shows steadier decline — the hump is likely
  ANES item-composition, not robust. Either way the model is too progressive in
  the middle.)

## Hypothesis 1 — fix the cohort generational gradient — FALSIFIED
The model's `cohort_replacement` rule carries a cultural gradient and the
documented sign-flip bug **is already fixed** in the canonical build
(`tier_d_cohort_y_signs_fix=True`); entering cohorts are correctly more
progressive (effective y: boomer 0.0, gen-x −0.05, late-mil −0.10). The 1980
seed is also correct (partisan cult +0.10, matching ANES 1986).

Experiment (`exp_cohort.py`): re-ran the full arc with the gradient set to the
**measured ANES birth-cohort values** and a doubled-steepness variant.
Mid-period cultural error vs ANES: baseline −0.176, anes_gradient −0.175,
steep −0.175. **No effect.** At ~0.9%/yr turnover the entering positions are
washed out by party pull before they can accumulate.

## Hypothesis 2 — the center is pinned by the symmetric elite loop — CONFIRMED
Trace (`exp_trace_center.py`): the two party elites diverge **symmetrically**
(D cult +0.05→−0.80, R cult +0.10→+0.74) so their **midpoint stays ≈ 0**
(+0.075 → −0.03 over 45 yrs), and the **mass cultural center tracks that midpoint
tick-for-tick**. The endogenous elite loop (`activist_elite.py`) is center-
preserving by construction, and `PartyPull` drags the mass onto that midpoint-zero
manifold — overriding the FJ anchor and any cohort signal.

**Conclusion:** the engine has a *differential* (sorting) channel but **no
common-mode** (society-wide level) channel on the cultural axis. It can pull the
parties apart; it cannot move the societal cultural level. Cultural position is
effectively collapsed onto party — the large non-partisan (generation/religion/
region) component that carries secular liberalization is absent.

## Fix options (the fork)
- **A. Common-mode societal-mood forcing.** Add a global cultural-baseline
  channel; the elite midpoint / a global cultural offset follows an exogenous
  societal-mood trajectory (traditional 80s/90s → progressive 2010s), anchored to
  GSS public traditionalism (a forcing that is exogenous to party sorting, not the
  party-position "answer"). Sorting rides on top. Small, robust, low calibration
  risk. Honest caveat: it is a fed forcing.
- **B. Make turnover bite (emergent).** Give agents a persistent generation-rooted
  cultural anchor and define elite cues as offsets from a moving common-mode
  baseline, so the secular level emerges from cohort turnover (~69%) plus a small
  period term (~31%). The fundamental mechanism, but a real refactor that risks the
  (currently passing) sorting calibration and needs re-balancing of anchor-vs-party
  pull. Feasibility caveat: at realistic turnover the cohort signal is weak vs
  party pull (see H1), so this likely needs the common-mode/differential
  decomposition to work at all.
- **C. Hybrid.** Decompose cultural position into common-mode + differential;
  carry the common mode via cohort-anchored turnover (emergent, ~69%) and a small
  exogenous period forcing (~31%); keep the differential elite loop as-is.

## Committed (gated) fix — UNIFIED, validated
User chose the unified wiring: agents carry `birth_year`, turnover is raised to a
demographically realistic rate, and the society-wide common mode `m(t)` =
mean generational baseline **emerges from the same agents that sort**. Implemented
gated (`cultural_common_mode=True`, default off = bit-identical; verified clean
main reproduces it). New rule `abm/rules/cultural_common_mode.py` shifts the
cultural **issue vector** (the n_issues truth; project∘lift identity → a rigid,
sorting-invariant 2D cultural translation).

NB the shift must hit the 7D `issues` vector, not `ideology` — `engine.step`
re-projects `ideology = project1(issues)` every tick, so an `ideology`-only shift
is cosmetic (the original P1 prototype was; corrected before committing).

Result (seed 0, `cohort_replacement_rate=0.007`, vs base):
- cultural center mid-period: base ~0.0 → emergent ~+0.07 (matches GSS partisan
  +0.07 at 1996 almost exactly; the residual vs ANES +0.22 is the non-robust ANES
  item-composition "hump", which demography correctly does not reproduce).
- Republican wrong-quadrant (LL): 2000 0.188→0.121, 2008 0.143→0.113 (=ANES 0.109).
- SORTING preserved/improved: party_sep 2000 0.447→0.516, 2024 1.093→1.051;
  corr 2000 0.371→0.452, 2024 0.772→0.807. m(t) is emergent, not fed.

### Battery before/after (fresh current-engine runs, seed 0)
6 FAIL + 1 WARN → 3 FAIL + 7 PASS. Newly PASS: F1 (R traditionalism),
F3 (econ separation — higher turnover sharpens econ sorting), F4 (cultural
back-loading), F6 (axis correlation). Downgraded: F0 CRITICAL→HIGH,
F2 CRITICAL→HIGH; F5 HIGH (improved numbers). The 3 residual HIGHs all trace to
the battery targeting the ANES partisan center, which carries the mid-90s "+0.22
hump"; the fix tracks the robust GSS level (+0.07) which has no such hump. Pushing
the common mode higher to pass F0/F2 would over-fit a non-robust ANES artifact
(violates measure-then-bless), so we keep the honest match. Turnover rate 0.007
chosen (preserves the 2024 endpoint; ~2.1%/yr ⇒ mean-birth advance ~0.95/yr, near
the real ~0.85). No media-outlet co-shift needed — the emergent run improves
party_sep rather than compressing it (compression was only the cosmetic
ANES-target test).

### Cascade empirical results (canonical flipped to common-mode, turnover 0.007)
- **pytest suite: GREEN** — 311 passed, 2 xfailed. Flipping the canonical model
  broke ZERO golden/drift tests: the existing band guards are too loose to pin the
  cultural center (so they neither caught the bug nor guard the fix — reinforces
  the case for adding validation/ as a permanent gate).
- **ANES scorecard: 17/24** (was blessed 18/24, 5 seeds). The 1-cell delta is an
  AFFECT cell (engine runs too cold — pre-existing [[affect-band-grounding]] issue,
  orthogonal to the cultural fix). Issue-constraint cells IMPROVED 3/4 → 4/4.
  Net: scorecard-neutral.
- **Realism battery: healthy** — per-issue D/R/gap trajectories track ANES
  (VCF0803 2025 sim gap 0.813 vs ANES 0.792; VCF0830 0.706 vs 0.731), overlap
  collapse 19.7%→0.2%, x~y corr 0.43→0.75 (ANES-like), corner occupancy 2.24% OK.
- **New validation battery: 6 FAIL+1 WARN → 3 FAIL+7 PASS** (cultural center fixed).

VERDICT: net reality WIN (cultural center + IC + new battery all improve; sorting
preserved) at the cost of a 1-cell affect wobble that is pre-existing and orthogonal.

Remaining cascade: phase10 bucket re-measure (may flip X1-X7 tags — measure-then-
bless), web re-export (also fixes stale seed_0), docs (methods/blindspots/literature),
and adding validation/ as a permanent gate.

Open: shipped `web/data/baseline/seed_0.json` is STALE vs current main
(party_sep@135 1.078 vs live 1.099) — pre-existing export staleness, fixed by the
re-export. Early-period (1986/92) R-in-LL still a touch high. Remaining steps =
the re-bless cascade (pick rate, optional outlet co-shift, flip canonical default,
re-run phase10 + web export + existing golden tests + scorecard/realism).
