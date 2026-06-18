# Realism report — does the model reflect reality?

**Measure-then-bless REPORT** (not a CI gate). Canonical shipped config
(`ANES_FULL_KWARGS` — since emergence-recovery E5 the **endogenous** activist→
elite→mass loop, since reality-validation the **common-mode cultural + economic
channels**), **9 seeds**, **live per-tick party labels** throughout.
Reproduce: `.venv/Scripts/python.exe scripts/audit/realism_battery.py --seeds 9`
→ `docs/results/realism_measurement.json`. Spec: `docs/internal/realism_check_spec.md`.

> **⚠ RE-BLESSED on the R-PHASE canonical config (2026-06-18; methods §5.32).**
> `ANES_FULL_KWARGS` is now `ANES_FULL_RPHASE_KWARGS` (the common-mode-econ build +
> R5 media-direction + R7 affect rest state + P3a affect recal + mild R1 contact +
> R8 endogenous mobilization). The §11 ANES band scorecard now measures **18/24**
> (15/20 mainframe + 3/4 IC) — a **PASS** (≥18), up from the **15/24 FAIL** on the
> pre-R-phase common-mode config. The gain is the **affect fix** (R7 rest state +
> P3a recal + re-enabled saturation): out-party affect now lands **in band at 2010
> and 2025** (2025 −0.57 vs band [−0.71,−0.51]); 1990/2000/2020 are still a touch
> out (affect ~2/5 strict realism cells, ~3/5 on the 5-seed scorecard — the narrow
> early-decade bands bind, the long-standing blindspot #1 residual). No band was
> loosened. Honesty-budget fractions re-blessed on this config (`honesty_budget.json`,
> 6 seeds): `party_sep` **0.34 free-flowing / 0.66 empirical** (up from 0.28/0.72 —
> R8 endogenous mobilization; fit-compatible emergence is capped ~0.39–0.56
> depending on the per-decade fit tolerance, because US polarization timing is
> event-paced — see methods §5.32 / blindspot #7), `identity_alignment` **0.36 /
> 0.64**, `affect` **0.83 / 0.17**. The 5-seed `phase9_anes_score` reads 19/24 (it
> and the 9-seed realism A2 differ by ~1 cell from seed sampling; both PASS). Numbers
> in the body below predate the R-phase — read this box as the current state.

### Read this first — four caveats that frame every number

1. **Fit ≠ validation.** Tier A re-checks the ANES quantities the model was
   *calibrated on* — that's goodness-of-fit, not independent confirmation.
   Tier B (external maps never fit to) is the independent part, and only
   **scale-free / trajectory-shape** comparisons survive (never absolute coords).
   This includes the §11 cell tally and `w2_total`: scored against the same recode
   that set the knobs, they are calibration-recovery, not validation — and the one
   genuinely held-out *temporal* cut **fails on `party_sep`** (`e5_holdout.md`).
2. **Positions are now EMERGENT, not fed.** Until E5 the party attractors were the
   ANES **voter** centroids × 1.798, replayed into the agents (positional sorting
   was input-carried — blindspot #7). Since E5 the party positions **emerge** from
   each party's activist tail through the saturating elite→mass loop; the ANES
   voter centroids are now a **calibration target the loop's gain was tuned to
   reach**, not a series fed in. So A1 below is "did the emergent cloud land where
   ANES voters are?" — a genuine outcome, not an identity. (Comparisons are still
   to mass-survey work, not DW-NOMINATE; elite maps validate *shape* only.)
3. **The compass compresses** (block means of 7 issues) — so a matched 2D
   centroid can still hide wrong per-item means. A6 pierces this with a per-issue
   check (incl. the racial item, otherwise folded invisibly into the y-axis).
4. **No self-blessing.** External criteria (Tier B, A6) come from the literature,
   decided before measuring — not a band frozen around the model's own output.

---

## Headline

**The loop *writes* positional sorting, but the rise is mostly forcing-carried.**
Party separation and identity alignment are produced by the endogenous loop, not
replayed from fed centroids — freezing the loop collapses `party_sep` to the 1980
seed (the loop is the generative mechanism) and the fed-POSITION channel is ~0.
**But proximate-writing is not emergence:** the loop's pace is set by an
ANES-calibrated mobilization forcing, so the honest budget (`honesty_budget.json`,
current common-mode config) splits each rise into free-flowing vs empirical input:
`party_sep` **0.28 free-flowing / 0.72 empirical**, `identity_alignment`
**0.28 / 0.72**, `affect` **0.94 / 0.06**. So only **affect** is substantially
emergent; **~72% of the positional rise rides the forcing** (peer-review audit
F1/F4). The panel does not claim "wholly emergent" — the mechanism is the model's,
the timing/magnitude is largely calibrated.

The realism **cost** of dropping the fed answer is real, modest, and documented:
the §11 scorecard goes **21/24 → 18/24** (still PASS ≥18), the joint-distribution
Wasserstein rises **0.73 → 0.92** (still ≈ the ~0.18–0.20/decade floor), and the
emergent cloud **lags ANES early** (1994 centroids behind) where the fed version
matched trivially. The late magnitude that the fed config *undershot* is now
**reached** (2025 `party_sep` in band); the new miss is a **mild 2010 overshoot**
plus a marginally tight late within-party spread. The model still tracks the
held-out GSS instrument, the emergent per-issue racial trajectory, and the
external Pew overlap-collapse curve.

---

## Tier A — internal ANES fidelity (*goodness-of-fit to the calibration source*)

| ID | Check | Result (9 seeds, endogenous) | Verdict |
|----|-------|------------------------------|---------|
| **A1** | per-party centroid endpoints vs ANES voter centroids (±0.07) | **2025 Dem d=(−0.01,+0.03)✓, Rep d=(+0.05,+0.02)✓** (emergent cloud lands on the ANES voters); **1994 Dem & Rep both miss** (sim less separated than ANES early — the loop is still climbing) | **2/4** — late on-target, early lag |
| **A2** | §11 ANES band scorecard (≥18/24) | **15/24** (11/20 mainframe + 4/4 IC) on the common-mode canonical config (re-bless banner above; was a stale 18/24, NOT the econ flip — econ-neutral). Out: 1990/2000/2010/2020/2025 affect (too cold, blindspot #1), 1990 constraint 0.362, 2000 sep 0.585, 2010 constraint 0.729 + sep 0.953 (mild overshoot). within_sd now **in band** | **FAIL ≥18 (with named misses)** — affect blindspot dominates; no band loosened |
| **A3** | per-decade 2D Wasserstein-2 vs ANES pointcloud | per-decade 0.165–0.211, **w2_total 0.92** (was 0.73 fed; achievable floor ~0.20/decade) | **still below floor** — looser than fed |
| **A4** | out-party affect vs ANES thermometer | 1990 −0.268 / 2000 −0.355 **too cold** (band miss); 2010/2020/2025 in band | **early over-animus** (known blindspot) |
| **A5** | sorting faster than constraint vs **held-out GSS** | partisan-align slope +0.0140/yr (GSS +0.0085); issue-corr slope +0.0101/yr (GSS +0.0057); sorting > constraint ✓ | **PASS** (both slopes a touch hot) |
| **A6** | per-issue trajectory vs ANES item means (**emergent**, not fit) | econ VCF0803 gap sim 0.38→0.82 vs ANES 0.32→0.79; **racial VCF0830 gap sim 0.27→0.75 vs ANES 0.22→0.73** | **strong** — the hidden racial item tracks ANES |

A6 is the standout and is now doubly emergent: the engine is *not* fed per-issue
ANES data *and* its party positions self-organise, yet the racial issue (VCF0830,
"aid to blacks") reproduces the real Democratic progressive shift and the gap
widening 0.22→0.73 (sim 0.27→0.75). A1's late match is the headline upgrade — the
2025 party centroids land on the ANES voters within ±0.07 having **emerged**
there, not been placed. The price is the **1994 lag**: both early centroids are
under-separated because the loop has not yet ramped (the fed config matched 1994
only because it was told those coordinates).

## Tier B — external structural / face validity (*independent maps; scale-free*)

| ID | Check | Result (9 seeds) | External benchmark | Verdict |
|----|-------|------------------|--------------------|---------|
| **B1** | overlap collapse: % Rep more liberal than median Dem | 20.3%(1987) → 0.3%(2014) → 0.1%(2025) | **Pew**: 23%(1994) → 4%(2014) | **near-exact shape** |
| **B2** | cross-pressured fraction + x~y slope | 2004 off-diag **33.9%** (✓), corr(x,y) 0.51; 2025 off-diag 18.8%, **corr 0.78 / slope 0.83** | **Treier-Hillygus**: ~30–44% cross-pressured; slope ~0.21 | **fraction OK; axes over-correlate** |

B1's collapse curve still lands near Pew's. B2 is split as before: the 2004
cross-pressured fraction (34%) sits inside Treier-Hillygus's 30–44%, but the two
compass axes grow **more correlated** than their work implies (corr 0.78, slope
0.83 by 2025 vs their ~0.21). This is marginally worse than the fed config (0.75)
— the single-axis (`align_u`) realignment direction the loop amplifies along
collapses econ and cultural onto one diagonal slightly more. Documented as gap 2.

## Tier C — pinned sanity guards (`tests/test_realism_guards.py`, all PASS)

- **C1** per-tick-label discipline — agents realign; frozen tick-0 labels
  fabricate an undershoot. Pinned so the bug can't return silently.
- **C2** projection parity — `ideology == project1(issues)` for every agent: the
  shipped picture *is* the calibrated 7D substrate.
- **C3** no corner-pin — 2025 boundary occupancy **1.07%** (hard ceiling 5%).

---

## Gaps — the late undershoot resolved by emergence; four documented

### The fed "2025 undershoot" is gone — replaced by a mild 2010 overshoot

On the fed config the 9-seed 2025 `party_sep` sat just under the ANES floor (a
flatter-than-ANES trajectory that caught up only at 2024). The endogenous loop
**reaches the late magnitude** — 2025 `party_sep` ≈ 1.10, comfortably in the
[1.04, 1.18] band, and the 2020 value is in band too. The trajectory's residual
mismatch has moved **earlier**: the loop climbs a touch fast in the **2010
bucket** (sep 0.960 vs band top 0.93; constraint 0.732 vs 0.72), the documented
cost of the econ-dominant single-axis amplification direction. The deeper fix (a
**time-evolving / balanced realignment direction** instead of the frozen
econ-dominant `align_u`) would lower the mid-period climb *and* the axis
over-correlation; logged as a refinement, not done here.

### Four documented gaps (open)

1. **Early-period over-animus** — affect at 1990 (−0.268) and 2000 (−0.355) is
   colder than ANES bands. Known blindspot (cold 1980 affect seed + concave
   warmth shape; see the affect-band grounding work). Late period (2010+) is in
   band. Unchanged by E5 — affect is loop-independent. **Status: documented blindspot.**
2. **Axes over-correlate late** — econ-x and cultural-y reach corr 0.78 by 2025
   (B2), slightly worse than the fed config (0.75): the loop amplifies along one
   (econ-dominant) direction, sorting the two compass dimensions onto one diagonal
   faster than the cross-pressured literature. **Status: documented; the
   time-evolving-direction refinement is the candidate fix.**
3. **Mid-period overshoot + tight late spread** — the 2010 bucket runs slightly
   hot (sep 0.960 / constraint 0.732) and the 2020/2025 within-party spread is
   marginally tight (0.276 vs 0.28 floor, −0.004). Both are E4-ABC-point residuals
   on the single-axis loop. **Status: documented; the adopted ABC point is not
   re-tuned (a user decision).**
4. **Emergence lags ANES early** — the 1994 party centroids are under-separated
   (A1) because the loop has not yet ramped; the fed config matched them only by
   construction. This is the honest signature of *emerging* the answer rather than
   feeding it. **Status: documented; intrinsic to the emergence approach.**

## Not covered (named, not hidden)

**Within-person panel dynamics** remain unvalidated — the only individual-level
number we have is the C1 aggregate realignment rate; the loop's per-agent
position-stability *shape* has not been checked against ANES/GSS panels or the
Green within-person party-ID stability (r≈.97). Also not covered: in-party affect
"scissors"; subgroup heterogeneity (identity strength, stubbornness tail, media
diet); network structure beyond modularity/xc; dated-shock magnitude/timing; the
intervention library's realism (X1–X7). Real coverage gaps for a later pass.

## Provenance (external sources used; logged in `docs/literature.md`)

Pew Research Center 2014 (overlap collapse); Treier & Hillygus 2009 (cross-
pressured fraction / dimensional slope); Baldassarri & Gelman 2008 (sorting vs
constraint); GSS 1972–2024 Cumulative (the held-out A5 instrument); ANES CDF
(A1/A2/A3/A4/A6 anchors). The endogenous loop's elite-follows-activist mechanism
is anchored to Bawn et al. 2012, Hacker & Pierson, and Zaller (see methods §5.28
/ `docs/literature.md`). DW-NOMINATE, NHB 2025, Hare-Poole, Bafumi-Herron, Bonica
inform the deferred descriptive checks (B3–B6).
