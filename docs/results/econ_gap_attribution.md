# Econ-gap elbow: mechanistic attribution (analysis, 2026-06)

Analysis-only trace of the model's economic GAP (R−D) **elbow** — flat ~1986–2008
then a cliff-jump 2008–2012 — vs ANES's smooth gradual rise. The elbow is the
signature of a **mechanism switching on sharply**, not an honest can't-anticipate
underfit. Reproduce: `validation/econ_gap_analysis.py`; figure
`validation/figures/econ_gap_elbow_attribution.png`. Measured on the **shipped
multi-seed ensemble** (gate-off canonical, 8 seeds) — so this is *not* a warm-seed
artifact (unlike the cultural front-loading; cf. blindspot #10).

## The elbow is real on the ensemble

| year | ANES | model | diff |
|---|---|---|---|
| 1986 | 0.321 | 0.376 | +0.055 |
| 2000 | 0.388 | 0.377 | −0.011 |
| **2008** | **0.584** | **0.510** | **−0.074** (worst early) |
| 2012 | 0.621 | 0.665 | +0.044 |
| **2020** | **0.838** | **0.766** | **−0.072** |

**Slope 1986–2008 = 0.0061/yr (FLAT) vs slope 2008–2012 = 0.0387/yr (CLIFF) — a 6.4×
jump.** ANES instead rises smoothly ~0.012/yr from 1986. (The model's flat period
actually drifts 0.38→0.51, not dead flat, but the slope discontinuity is sharp.)

## Mechanism inventory (what feeds the econ GAP)

| component | role in the gap | evidence |
|---|---|---|
| **ActivistEliteCue loop** (`activist_elite.py`) | owns the gap **MAGNITUDE** — the leapfrog `cent + g·(tail−cent)` amplified by `g = gain·mob` | ablation `elite_gain=0` → gap collapses to **0.22 flat** (1986–2020) |
| **E4 econ mobilization SCHEDULE** (`mob_base/peak/backload/asym`) | owns the gap **TIMING** — `mob = base + (peak−base)·τ^p`, `p = 1+2·backload = 3.71` (strongly back-loaded), plus `·(1±asym·τ)` adding a τ-growing R−D split | **see ablation below** |
| `elite_ceiling` (0.82) | bounds runaway — but **not the elbow** | gap (0.5–0.8) never reaches the ceiling gap (~1.6); not a saturation effect |
| `PartyPull` / FJ damping | transmits the cue to the mass + anchors it | tracks the loop/schedule; not an independent pacing |
| cohort turnover | reshuffles, no gap-timing role | — |
| **econ common-mode mood** (§5.31) | drives the **CENTER, not the gap** | it is a *rigid translation* — sorting-invariant by construction |

## Attribution: `mob_backload` owns the cliff

Ablation (ensemble), cliff-to-flat slope ratio:

| config | 2008 | 2012 | 2020 | flat slope | cliff slope | ratio |
|---|---|---|---|---|---|---|
| **default backload 1.35** | 0.510 | 0.665 | 0.766 | 0.0061 | 0.0387 | **6.4× (sharp elbow)** |
| backload 0.6 | 0.666 | 0.752 | 0.794 | 0.0132 | 0.0213 | 1.6× |
| **backload 0.3 (gradual)** | 0.731 | 0.783 | 0.805 | 0.0162 | 0.0128 | **0.8× (cliff GONE)** |
| loop gain ×0 | 0.223 | 0.245 | 0.294 | — | — | flat-low |

**The cliff is the back-loaded mobilization schedule's shape.** `τ^3.71` is ~flat
through τ=0.5 (year 2000: mob ≈ 0.26) then ramps steeply (2008→2012: mob 0.4→1.1) —
the cliff window aligns exactly with the schedule's steep section (right panel of the
figure). Lowering `backload` 1.35→0.3 collapses the elbow (ratio 6.4×→0.8×). The
**loop** sets the magnitude (gain×0 → gap 0.22 flat); the **schedule** sets the
timing. It is **not** a saturation/ceiling effect and **not** PartyPull.

**But lowering backload over-corrects the early period:** backload 0.3 *removes* the
cliff but **front-loads** the gap (2008 0.73 vs ANES 0.58, the 1990s 0.5–0.7 vs ANES
0.4). The single `τ^p` schedule trades flat-then-cliff for high-early — neither matches
ANES's **gradual** rise. The real econ realignment (Reagan tax revolt → Gingrich 1994 →
2000s polarization) is *gradual and continuous* from the mid-80s; the E4 schedule
instead **defers nearly all econ amplification to 2008–2012**.

## Hypotheses (falsifiable; NOT implemented this round)

- **H1 — re-shape the schedule (lower backload).** Smooths the cliff. *Falsified as a
  clean fix:* backload 0.3 kills the cliff but over-shoots 1990–2008 (a single `τ^p`
  can't be gradual-early *and* match the late level). **e5-holdout RISK: HIGH** — the
  back-loading was E4-fitted precisely to defer the emergent `party_sep` into the 2010s
  to match the ANES late acceleration *and* pass the four-cut holdout temporal cut;
  lowering it would shift sep earlier and likely **break the late acceleration + the
  temporal-cut holdout**. The cliff is, in part, the *price* of passing that cut.
- **H2 — add a GRADUAL early-econ-sorting driver (1986–2008), keep the late ramp.** The
  schedule is currently the *only* econ-gap pacing and is mono-shaped; a gentle early
  driver (documented: Reagan tax-revolt → Gingrich) plus the existing late ramp could
  reproduce the smooth rise. Falsifiable by adding an early econ-mobilization floor /
  a second gentle slope. **e5-holdout RISK: MEDIUM** — adds early sep (could help the
  early waves) but must be checked it doesn't inflate the pre-2010 holdout cut; dual
  parameters add identifiability risk.
- **H3 — the elbow is cohort/IC, not the schedule.** *Rejected:* `gain×0` gives a flat
  0.22 gap, so the loop+schedule (not cohort/IC) own the dynamics.

## Verdict
The econ-gap elbow is a **well-attributed mechanism-shape artifact**: the back-loaded
E4 mobilization schedule (`mob_backload=1.35`, `p=3.71`) defers econ amplification into
2008–2012, producing the flat-then-cliff. It is **robust on the ensemble** (not a
warm-seed artifact). A clean fix needs a **gradual early driver + the existing late
ramp** (not merely lowering `backload`, which over-corrects), and it **must be
validated against the e5-holdout temporal cut**, which the current back-loading was
fitted to pass. This decides that an econ re-pacing is *plausible but holdout-risky* —
worth a separate spec, not a quick knob change.
