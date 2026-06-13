# Realism report — does the model reflect reality?

**Measure-then-bless REPORT** (not a CI gate). Canonical shipped config
(`ANES_FULL_KWARGS`), **9 seeds**, **live per-tick party labels** throughout.
Reproduce: `.venv/Scripts/python.exe scripts/audit/realism_battery.py --seeds 9`
→ `docs/results/realism_measurement.json`. Spec: `docs/internal/realism_check_spec.md`.

### Read this first — four caveats that frame every number

1. **Fit ≠ validation.** Tier A re-checks the ANES quantities the model was
   *calibrated on* — that's goodness-of-fit, not independent confirmation.
   Tier B (external maps never fit to) is the independent part, and only
   **scale-free / trajectory-shape** comparisons survive (never absolute coords).
2. **Mass ≠ elite.** Party attractors are ANES **voter** centroids × 1.798, not
   DW-NOMINATE. We compare to mass-survey work; elite maps validate *shape* only.
3. **The compass compresses** (block means of 7 issues) — so a matched 2D
   centroid can still hide wrong per-item means. A6 pierces this with a per-issue
   check (incl. the racial item, otherwise folded invisibly into the y-axis).
4. **No self-blessing.** External criteria (Tier B, A6) come from the literature,
   decided before measuring — not a band frozen around the model's own output.

---

## Headline

**The model is substantially realistic on the checks it was *not* fit to.** It
matches the ANES joint distribution (Wasserstein below the achievable floor),
the **held-out GSS instrument**, the **per-issue trajectories including the
racial item** (emergent — never fit), and the **external overlap-collapse curve**
(near-exact to Pew). It scores **20/24** on the §11 ANES band scorecard. Four
honest gaps remain (below), the chief being a **small, real 2025 `party_sep`
undershoot** (1.056 vs the ANES floor 1.08) — the agreed T-UNDER target.

---

## Tier A — internal ANES fidelity (*goodness-of-fit to the calibration source*)

| ID | Check | Result (9 seeds) | Verdict |
|----|-------|------------------|---------|
| **A1** | per-party centroid endpoints vs ANES voter centroids (±0.07) | 2025 Dem d=(−0.01,+0.03)✓, Rep d=(+0.02,−0.01)✓; 1994 Rep ✓; **1994 Dem d=(−0.09,−0.03) miss** (sim Dems too econ-left early) | **3/4** — late excellent, one early miss |
| **A2** | §11 ANES band scorecard (≥18/24) | **20/24 PASS**. Out: 1990/2000 affect (too cold), **2025 sep 1.056** (<1.08 floor), 1980 variance 0.367 (>0.36) | **PASS** (with named misses) |
| **A3** | per-decade 2D Wasserstein-2 vs ANES pointcloud | per-decade 0.13–0.17, **w2_total 0.73** (achievable floor ~0.20/decade) | **strong** — below floor everywhere |
| **A4** | out-party affect vs ANES thermometer | 1990 −0.270 / 2000 −0.355 **too cold** (band miss); 2010/2020/2025 in band | **early over-animus** (known blindspot) |
| **A5** | sorting faster than constraint vs **held-out GSS** | partisan-align slope +0.0123/yr (GSS +0.0085 ✓); issue-corr slope +0.0086/yr (GSS +0.0057, **marginally hot**); sorting > constraint ✓ | **PASS** (issue-corr a touch steep) |
| **A6** | per-issue trajectory vs ANES item means (**emergent**, not fit) | econ VCF0803 gap sim 0.41→0.79 vs ANES 0.32→0.79; **racial VCF0830 gap sim 0.21→0.72 vs ANES 0.22→0.73** | **strong** — the hidden racial item tracks ANES |

A6 is the standout: the engine is *not* fed per-issue ANES data, yet its racial
issue (VCF0830, "aid to blacks") emergently reproduces the real Democratic
progressive shift and the gap widening 0.22→0.73 — the per-issue story the 2D
compass otherwise hides. It does slightly undershoot the 2020 racial gap
(0.73 vs ANES 0.83) — the same undershoot signature as A2.

## Tier B — external structural / face validity (*independent maps; scale-free*)

| ID | Check | Result (9 seeds) | External benchmark | Verdict |
|----|-------|------------------|--------------------|---------|
| **B1** | overlap collapse: % Rep more liberal than median Dem | 20.9%(1987) → 2.4%(2014) → 0.3%(2025) | **Pew**: 23%(1994) → 4%(2014) | **near-exact shape** |
| **B2** | cross-pressured fraction + x~y slope | 2004 off-diag **33.9%** (✓), corr(x,y) 0.52; 2025 off-diag 19.4%, **corr 0.75 / slope 0.81** | **Treier-Hillygus**: ~30–44% cross-pressured; slope ~0.21 | **fraction OK; axes over-correlate** |

B1's collapse curve lands almost on Pew's (2.4% vs 4% at 2014). B2 is split: the
2004 cross-pressured fraction (34%) sits inside Treier-Hillygus's 30–44%, but the
two compass axes grow **more correlated** than their work implies (corr 0.75,
slope 0.81 by 2025 vs their ~0.21) — the cloud collapses toward a single diagonal
more than the mass-survey literature. This matches A5's slightly-steep issue-corr
slope: the constraint mechanism over-aligns econ and cultural by the late period.

## Tier C — pinned sanity guards (`tests/test_realism_guards.py`, all PASS)

- **C1** per-tick-label discipline — agents realign (~19%); frozen tick-0 labels
  fabricate an undershoot. Pinned so the bug can't return silently.
- **C2** projection parity — `ideology == project1(issues)` for every agent: the
  shipped picture *is* the calibrated 7D substrate.
- **C3** no corner-pin — 2025 boundary occupancy **0.89%** (hard ceiling 5%).

---

## The four honest gaps

1. **2025 `party_sep` undershoot — 1.056 vs ANES floor 1.08** (miss 0.024, stable
   across 9 seeds). The single calibration miss. **Status: T-UNDER** (reopen the
   S4 fit). Small, but real, and it propagates into the A6 racial-gap and B1
   tail undershoots.
2. **Early-period over-animus** — affect at 1990 (−0.270) and 2000 (−0.355) is
   colder than ANES bands. Known blindspot (cold 1980 affect seed + concave
   warmth shape; see the affect-band grounding work). Late period (2010+) is in
   band. **Status: documented blindspot.**
3. **Axes over-correlate late** — econ-x and cultural-y reach corr 0.75 by 2025
   (B2), with the issue-corr slope marginally above GSS (A5): the model sorts the
   two compass dimensions onto one diagonal somewhat faster than the
   cross-pressured literature. **Status: documented; candidate for a future
   constraint-anisotropy pass.**
4. **1980 IC variance slightly high** (0.367 vs ≤0.36) and the **1994 Dem econ
   centroid a touch too left** (A1). Minor initial-condition / early-trajectory
   offsets. **Status: documented.**

## Not covered (named, not hidden)

Within-person panel dynamics (stability *shape*, not just the aggregate switch
rate); in-party affect "scissors"; subgroup heterogeneity (identity strength,
stubbornness tail, media diet); network structure beyond modularity/xc; dated-
shock magnitude/timing; the intervention library's realism (X1–X7). These are
real coverage gaps for a later pass.

## Provenance (external sources used; logged in `docs/literature.md`)

Pew Research Center 2014 (overlap collapse); Treier & Hillygus 2009 (cross-
pressured fraction / dimensional slope); Baldassarri & Gelman 2008 (sorting vs
constraint); GSS 1972–2024 Cumulative (the held-out A5 instrument); ANES CDF
(A1/A2/A3/A4/A6 anchors). DW-NOMINATE, NHB 2025, Hare-Poole, Bafumi-Herron,
Bonica inform the deferred descriptive checks (B3–B6).
