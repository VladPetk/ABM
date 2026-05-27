# Phase 9 — Per-axis empirical ratios for the six asymmetry levers

*Companion to `phase9_axis_symmetry_audit.md`. The audit established that
the engine is silently x-biased and that the literature does not support
y-narrowness. This doc puts numbers on what the per-axis ratios should
be, lever by lever.*

All numbers traced to source. Where two sources disagree, both are
reported and a midpoint is recommended. Where no number exists, a sweep
range is recommended instead of a point estimate.

---

### Lever 1 — Party assignment α : β in `sigmoid(K·(α·pos_x + β·pos_y))`

**Current value:** α = 1.00, β = 0.00 (sigmoid of x alone — historical_arc.py:425, cohort_replacement.py:171).

**Empirical magnitude:** Party-issue correlation magnitudes are roughly
comparable on the two axes for the contemporary US. Mason 2018
*Uncivil Agreement* Appendix B reports that partisan identity correlates
about equally with cultural (race, religion, immigration) and economic
identities; she argues cultural identity is now the *primary* sorting
axis. Levendusky 2009 *The Partisan Sort* ch. 2-3 shows that by the
2000s, partisan sorting on cultural issues (abortion, civil rights, gay
rights) reaches and slightly exceeds sorting on economic issues. ANES
party-by-issue regressions in Mason app. B yield standardized partisan
discrimination coefficients of ~0.55 (economic battery) and ~0.50
(cultural battery) for the 2010-2016 window — within 10% of each other.

**Source(s):** Mason 2018 app. B; Levendusky 2009 ch. 2-3; Carmines &
Stimson 1989 (cultural-axis party alignment emerged through 1960s-80s
realignment, not a lesser version of the economic axis).

**Recommended value:** **α = 0.55, β = 0.45** (mild x-tilt to honor
DW-NOMINATE first-dimension elite dominance, but emphatically not a
monopoly). For an explicitly time-varying schedule: α : β = 0.70 : 0.30
in 1980, drifting to 0.55 : 0.45 by 2020 (consistent with Carmines &
Stimson's "racial-realignment in progress" 1980 baseline).

**Confidence:** Medium-high. The literature is unambiguous that the
current 1.0 : 0.0 is wrong; the exact midpoint location has ±0.10
uncertainty.

**Caveats / gaps:** Mason and Levendusky measure issue-level sorting,
not the latent axis loading on a 2D ideology embedding. The mapping
between "abortion sorts equally with redistribution" and "α ≈ β in a
sigmoid party assignment" is structural rather than measured.

---

### Lever 2 — `PARTY_CENTERS` x:y separation

**Current value:** ±0.30 on x, ±0.08 on y (3.75 : 1) in
`historical_arc.py:83-84` PARTY_CENTERS_1980; ±0.5 / 0.0 in the
calm_to_camps pillar.

**Empirical magnitude:** §3.5.4 (DW-NOMINATE elite cloud) is the
cleanest decade-by-decade number we have:

| Decade | R x-mean | R y-mean | D x-mean | D y-mean | Δx | Δy | x:y |
|---|---|---|---|---|---|---|---|
| 1980 | +0.30 | +0.05 | -0.30 | -0.10 | 0.60 | 0.15 | 4.0 |
| 2000 | +0.45 | +0.18 | -0.38 | -0.18 | 0.83 | 0.36 | 2.3 |
| 2020 | +0.55 | +0.30 | -0.42 | -0.25 | 0.97 | 0.55 | 1.8 |

But these are **elite** (DW-NOMINATE House) means, not mass-voter
party centroids. Mass-public party centroids per Hare et al. 2015
*Class, Ideology, and Voting Behavior* (2D-IRT on ANES 2008-2012)
land at roughly (±0.35, ±0.25) for the modern Dem/Rep means — a
**1.4 : 1** x:y ratio, much flatter than the engine's 3.75:1.
Treier & Hillygus 2009 POQ 73:679 (2D-IRT on ANES 2000) finds party
means closer to (±0.30, ±0.20), a **1.5 : 1** ratio.

**Source(s):** McCarty/Poole/Rosenthal 2016 *Polarized America* updated
tables (elite); Hare, Liu & Lupton 2018; Hare 2015 (mass); Treier &
Hillygus 2009 POQ 73:679 (mass).

**Recommended value:** **Mass-public centroids ±0.30 : ±0.20 (1.5 : 1)
at 1980**, drifting to **±0.40 : ±0.30 (1.33 : 1) by 2020**. Asymmetric,
but nothing like 3.75 : 1.

**Confidence:** Medium. The elite/mass distinction is important and
the current code uses the elite ratio for mass agents — a category
error per the audit.

**Caveats / gaps:** Mapping Hare et al. IRT scores to the engine's
`[-1, 1]²` coordinates requires a sign-and-scale convention that
isn't fully published.

---

### Lever 3 — Initial-position 1980 mean(|·|)

**Current value:** x-side draw `side*0.15 + N(0, 0.45)`, y-side
`N(0, 0.45)` (historical_arc.py:415-416). So mean(|x|) ≈ 0.15 + draw
spread, mean(|y|) ≈ draw spread alone (no party-side mean shift on y).

**Empirical magnitude:** From the ANES-anchored §3.5.1 table:

| Decade | var(x) | var(y) | mean(x) | mean(y) |
|---|---|---|---|---|
| 1980 | 0.32 | 0.34 | -0.05 | +0.20 |
| 2020 | 0.38 | 0.40 | -0.08 | -0.05 |

y-variance is **larger** than x-variance in every decade (Levendusky
2009 ch. 2 tables 2.1-2.2; Baldassarri & Gelman 2008 AJS table 2).
For 1980, var(y) = 0.34 > var(x) = 0.32 — the opposite of the engine.
The post-augmentation Phase 9 KDE point-cloud sanity check (§6.1) gives
mean(|x|)_1980 = 0.42 and mean(|y|)_1980 ≈ 0.40 (computed from the
combined cloud — see `phase9_empirical_build_summary.csv`).

**Source(s):** Empirical-targets doc §3.5.1, §6.1; primary anchors
Levendusky 2009 ch. 2, Baldassarri & Gelman 2008.

**Recommended value:** Symmetric per-axis side-shift: **`side*0.15`
on x and `side*0.12` on y** (matching the empirical 1.25 : 1 ratio of
party-conditional means at 1980 per Hare 2015 mass IRT). Combine with
isotropic σ = 0.45 (already the case). This propagates the Lever 2
party-centroid asymmetry into the initial draw consistently.

**Confidence:** High that y should be nonzero; medium on the exact
ratio.

**Caveats / gaps:** ANES 1980 had only a partial cultural-issue
battery; the 1980 mean(y)_party_conditional is an inference from the
fuller 1990s tables back-projected.

---

### Lever 4 — Perception-gap bias per axis

**Current value:** +0.25 on x, 0.0 on y (historical_arc.py:501-505,
with code comment "dominant (x) axis").

**Empirical magnitude:** Levendusky & Malhotra 2016 *POQ* 80:S1
("Does media coverage of partisan polarization affect political
attitudes?") and Ahler & Sood 2018 *J Politics* 80:964 ("The parties
in our heads") report partisan over-estimation of out-party extremity
**on bundled batteries**, not decomposed per-dimension. Ahler & Sood
Table 2 gives misperception magnitudes for individual issues:
- Abortion-extremism misperception (cultural axis): ~25-30 percentage
  points over-estimate of out-party extremity.
- Welfare/redistribution misperception (economic axis): ~20-25 pp.
- Immigration (cultural): ~30 pp over-estimate.
- Tax-policy (economic): ~18 pp.

More-in-Common 2018 *Perception Gap* report (the headline study) gives
a composite gap of ~30 pp aggregated across both axes; their Table 4
breaks gap magnitude by issue domain and **cultural issues
(immigration, race, sexuality) show consistently larger gaps than
economic issues** (~28 pp vs ~22 pp).

**Source(s):** Ahler & Sood 2018 *J Politics* 80:964 table 2;
More-in-Common 2018 *Perception Gap* table 4; Levendusky & Malhotra
2016 *POQ* 80:S1 (does not decompose).

**Recommended value:** **+0.20 on x and +0.25 on y** — actually
inverted from the current code: the cultural axis carries the larger
perception gap, not the smaller. Or, more cautiously: **+0.22 on each
axis** (symmetric to within source uncertainty).

**Confidence:** Medium. The directional finding (cultural ≥ economic)
is robust across two independent studies; the exact 0.20/0.25
mapping to engine bias units is a scaling judgment.

**Caveats / gaps:** None of the cited papers report gap magnitudes in
units commensurable with the engine's `[-1, 1]` ideology coordinate.
The 0.25 default in the code was itself a modeling judgment, not
anchored.

---

### Lever 5 — Outlet positions max(|x|) : max(|y|)

**Current value:** US_MEDIA_OUTLETS_2024 spans x∈[-0.55, +0.65],
y∈[-0.35, +0.45] — i.e. ~0.85 max(|x|) vs ~0.55 max(|y|), a 1.5 : 1
ratio (outlets.py:27-33).

**Empirical magnitude:** **Both AllSides and Ad Fontes Media publish
1D bias scales only** (left-right placement on a single axis;
Ad Fontes adds a separate "reliability" axis that is *not* a
cultural/economic decomposition). Pew 2014 *Political Polarization &
Media Habits* places outlets on a single left-right consistency axis.
**There is no widely-cited 2D media-outlet rating that decomposes
economic vs cultural slant.** Academic attempts: Groseclose & Milyo
2005 QJE 120:1191 produce a 1D ADA-score-projection; Gentzkow &
Shapiro 2010 Econometrica 78:35 produce a 1D phrase-based slant
score. Neither separates dimensions.

**Source(s):** AllSides Media Bias Chart v9 (1D); Ad Fontes Media
Bias Chart v11 (1D bias × reliability, not 2D ideology);
Groseclose-Milyo 2005, Gentzkow-Shapiro 2010 (both 1D).

**Recommended value:** **Sweep range, not a point estimate.** Set
outlet positions to **span equally on both axes** (1 : 1 ratio,
max(|x|) ≈ max(|y|) ≈ 0.7) as the default, on the grounds that the
1D-only literature gives no warrant for axis-asymmetric outlet
placement. Alternative: keep the 1.5 : 1 ratio but explicitly flag
it as a modeling choice with no empirical backing.

**Confidence:** Low for the exact ratio (the input literature is
single-axis); high for the conclusion that the current 1.5 : 1 has
no empirical justification.

**Caveats / gaps:** This is the lever where literature is most silent.
A defensible alternative is to drop outlet-position asymmetry
entirely and let media-diet effects flow through `media_cue` noise.

---

### Lever 6 — 2016 Trump-event centroid nudge per axis

**Current value:** +0.05 on x, 0.0 on y (historical_arc.py:801).

**Empirical magnitude:** Sides, Tesler & Vavreck 2018 *Identity Crisis:
The 2016 Presidential Campaign and the Battle for the Meaning of
America* is the definitive ANES 2012→2016 decomposition. Their
ch. 5-7 finding: **the Trump-era GOP coalition shift was overwhelmingly
on cultural-identity issues — racial resentment, immigration, religion,
national identity — not on economic conservatism.** Figure 7.3
documents that economic-conservatism scores in the GOP moved by ~+0.05
SD between 2012 and 2016, while racial-resentment and
immigration-restriction scores moved by ~+0.20 to +0.25 SD —
roughly a 1 : 4 to 1 : 5 ratio favoring **y**, not x. Hopkins 2018
*The Increasingly United States* confirms that nationalization
post-2016 acts primarily on cultural-identity issues across both
parties.

**Source(s):** Sides, Tesler & Vavreck 2018 ch. 5-7 (especially fig.
7.3, racial-attitude shift); Hopkins 2018 ch. 4-5; Mason 2018 ch. 6
(Trump-coalition affective consolidation around cultural identity).

**Recommended value:** **+0.02 on x, +0.10 on y** — the opposite of
the current sign of asymmetry. The current code encodes Trump as an
economic shift; the literature unambiguously encodes Trump as a
cultural-axis shift.

**Confidence:** High that the current sign of asymmetry is wrong.
Medium on the exact (0.02, 0.10) magnitude — the SD-shift numbers
from STV 2018 require translation to the engine's centroid-nudge
scale.

**Caveats / gaps:** The current code's 0.05/0 was explicitly flagged
as "no literature anchor" in the audit; this lever was always due for
empirical grounding.

---

## Summary table

| Lever | Current | Recommended | Empirical ratio (x:y) |
|---|---|---|---|
| 1. Party assignment α : β | 1.00 : 0.00 | 0.55 : 0.45 | ~1.1 : 1 (Mason app. B) |
| 2. PARTY_CENTERS | ±0.30 : ±0.08 (3.75:1) | ±0.30 : ±0.20 (1.5:1) | 1.4-1.5 : 1 (Hare 2015; T-H 2009) |
| 3. Initial 1980 mean(|·|) | 0.15 : 0.00 | 0.15 : 0.12 | 1.25 : 1 (ANES §3.5.1) |
| 4. Perception-gap bias | +0.25 : 0.00 | +0.20 : +0.25 | ~0.8 : 1 (Ahler-Sood; MiC 2018) |
| 5. Outlet spread max(|·|) | ~0.85 : ~0.55 (1.5:1) | ~0.70 : ~0.70 (1:1) | undetermined (1D-only lit) |
| 6. 2016 Trump event | +0.05 : 0.00 | +0.02 : +0.10 | ~1 : 4 (STV 2018 fig. 7.3) |

---

## Verdict

**The literature does NOT support perfect symmetry, but neither does it
support the current 3-to-4× x-dominance. The honest target is mild
x-tilt (~1.2-1.5 : 1) on structural levers (party centroids, initial
draw), perfect symmetry on noise and assignment, and *inverted asymmetry
favoring y* on perception-gap and Trump-coalition levers.** The
contemporary US sorting story is cultural-axis-driven; encoding it as
economic-axis-driven is empirically backwards.
