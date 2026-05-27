## 1. The question

The engine's 2D ideology space defines `position[0]` (x) as the economic
axis and `position[1]` (y) as the social/cultural axis, both on `[-1, 1]`.
Phase 9 calibration finds `var_y ≈ 0.04` (engine) vs `0.27` (empirical
2020 target) — a 7× under-dispersion — while `var_x ≈ 0.14` vs `0.29` is
only modestly low. Vlad's intuition: the axes are the same kind of object
and the engine should treat them symmetrically. The question is whether
the observed x-dominance is a designed asymmetry (and therefore the
proposed `AnisotropicNoise` fix is honest), or a chain of x-axis-specific
choices that accumulated silently while the docs claim symmetry.

## 2. Codebase audit — asymmetry inventory

All evidence below is from `D:\MyApps\ABM\abm\rules\*.py` and
`D:\MyApps\ABM\abm\pillars\historical_arc.py` (lines cited inline).

**Rules — vector arithmetic only (x and y treated identically):**

| Rule / file | Treatment | Same on x/y? |
|---|---|---|
| `BoundedConfidenceInfluence` (influence.py) | 2-norm distance, mean of neighbours' full 2-vectors | Yes |
| `PartyPull` (party_pull.py:82) | `target - ideology`, full vector | Yes (math); **asymmetry is in the `target`** |
| `FactionAnchor` (faction_anchor.py:65) | full vector pull to `faction_center` | Yes (math); asymmetry is in centroids |
| `MediaConsumption` (media_consumption.py:88-96) | sum of `weight*(outlet.position - ideology)`, full 2-vector | Yes (math); asymmetry is in outlet positions and `media_cue` |
| `AffectiveUpdate` (affective_update.py:242) | `np.linalg.norm(...)` distance | Yes |
| `BacklashRepulsion` (repulsion.py:115-126) | `diff = ideology - n.ideology`, full vector inverse-square | Yes |
| `IdentitySorting` (identity_sorting.py) | operates on `identities` vector, not ideology — not (x,y) at all | n/a |
| `PerceptionUpdate` (perception_update.py:93) | full 2-vector correction | Yes |
| `GaussianNoise` (noise.py:57) | `rng.normal(0, sigma, size=2)` — **identical σ on both axes** | Yes |
| `EliteDrift` (elite_drift.py:50-67) | full-vector direction from centroid; clip to [-1,1]² | Yes |
| `TieRewiring`, `ResidentialMigration`, `CohortReplacement`, `IdentityPrime`, `ThreatDecay`, `ArgumentExchange` | no per-axis branches | Yes |

**Constants and seeds — every place asymmetry actually lives:**

| Constant / mechanism | x value | y value | Symmetric? | Source / justification |
|---|---|---|---|---|
| `PARTY_CENTERS_1980` (historical_arc.py:83-84) | ±0.30 | ±0.08 | **No (3.75:1)** | Phase 8f §1.1 fix to unblock constraint plateau. Justified retroactively by Carmines & Stimson 1989. |
| `PARTY_CENTERS` (calm_to_camps.py:43-46) | ±0.5 | 0.0 | **No (∞:0)** | Pillar; y-axis literally inert. |
| Initial position draw (historical_arc.py:415-416) | `side*0.15 + N(0, 0.45)` | `N(0, 0.45)` | **No** — x has party-side mean shift; y is zero-mean | Sigmoid party assignment is on x only. |
| Party assignment sigmoid (historical_arc.py:425; cohort_replacement.py:171) | `P(party=1) = 1/(1+exp(-K·pos_x))` | not used | **No** — party is a deterministic function of x only | Phase 8f §2. **This is the smoking gun.** |
| Identity → ideology mapping | `party_identity_centers = ±0.20 * ones(3)` (historical_arc.py:368-371) — but this seeds `identities`, not (x,y) | symmetric inside `identities` space | n/a | IdentitySorting operates in a separate latent space; only PartyPull's centroid couples back to (x,y). |
| `PARTY_CUE_SIGMA_HISTORICAL` (historical_arc.py:90-93) | σ scalar, applied isotropically `rng.normal(0, σ, size=2)` | same σ both axes | Yes | Phase 8b M4. |
| `MEDIA_CUE_SIGMA` (historical_arc.py:227) | 0.40, isotropic | 0.40, isotropic | Yes | Phase 8f. |
| `US_MEDIA_OUTLETS_2024` (outlets.py:27-33) | x range [-0.55, +0.65] (span 1.20) | y range [-0.35, +0.45] (span 0.80) | **No (1.5:1)** | Approximated from AllSides/Ad Fontes; empirical. |
| `ELITE_DRIFT_SCHEDULE` (historical_arc.py:124-137) | drifts along the centroid-deviation direction; with two parties placed on x, drift is **almost entirely on x** | same rule | **No (in effect)** | Two centroids placed at ±x → `direction = parties[pid]-centroid` is ~x-aligned → drift adds on x and accumulates. |
| Tea Party (historical_arc.py:942) | sub_centroid x=+0.55 | y=+0.30 | No | Skocpol & Williamson 2012 |
| MAGA (historical_arc.py:963) | x=+0.50 | y=+0.55 | Roughly symmetric | Sides, Tesler & Vavreck 2018 |
| Bernie (historical_arc.py:980) | x=-0.55 | y=-0.30 | No | Heaney & Rojas 2015 |
| DSA (historical_arc.py:997) | x=-0.70 | y=-0.55 | Roughly symmetric | Schwartz 2017 |
| HISTORICAL_FACTIONS_1980 centroids (lines 239-247) | |x| range 0.00-0.55 | |y| range 0.00-0.55 | **Roughly symmetric** | Phase 9 Tier A — literature-anchored faction map. |
| `Cohort` x/y means+SD (cohort_replacement.py:38-58) | μ_x, σ_x | μ_y, σ_y | Symmetric distributions, drift means slightly asymmetric | Phillips 2022 |
| Perception-gap bias (historical_arc.py:501-505) | `+ bias_sign * 0.25` on x | unbiased on y | **No** | Phase 8c §4 E4.1: "bias toward extremity on the dominant (x) axis". Explicit. |
| 2016 Trump-event centroid nudge (historical_arc.py:801) | `+0.05` on x | `0.0` on y | **No** | Modeling choice (no literature anchor). |
| `SOCIAL_BIAS / SOCIAL_NOISE` (calm_to_camps.py:52-53) | applied to `social_coord` based on party sign (which is x-derived) | n/a | x-derived | Phase 3 latent layer. |

**Synthesis of the codebase audit.** Every rule's *math* is rotationally
symmetric (Euclidean norms, isotropic Gaussian draws, full-vector pulls).
But the *targets and seeds those rules consume* are systematically
x-biased:

1. Party identity is a sigmoid of x alone, so the party label is
   effectively the sign of x. Every party-conditional mechanism
   (PartyPull, AffectiveUpdate's out-party detection, BacklashRepulsion,
   media diet, perception, threat) therefore inherits an x-centric
   sorting signal.
2. Party centroids are placed ±0.30 on x and only ±0.08 on y (1980;
   the pillar is even worse — 0 on y). PartyPull, EliteDrift,
   MediaConsumption (through `diet_for_party`), and the perception
   seeding all use these centroids as targets, so each one's net
   pull is ~3.75× larger on x than on y.
3. Media outlets span 1.5× more on x than on y.
4. The perception-gap bias is explicitly x-only.

Conclusion of Part 1: **the math is symmetric; the inputs are not.**
GaussianNoise is the only isotropic randomness source; every signal
the model integrates is x-dominant.

## 3. Substantive literature: are the axes the "same kind of thing"?

The literature is unambiguous: economic and cultural ideology are
**distinct latent dimensions of voter ideology**, not two slices of one
construct.

- **Treier & Hillygus 2009** (*POQ* 73:679-703) — two-dimensional Bayesian
  IRT on ANES 2000 issue battery recovers two dimensions with
  `corr(econ, social) ≈ 0.30`. Two dimensions, not one — and the
  correlation is moderate, not unitary.
- **Hare, Highton & Jones 2024** / **Hare et al. 2015** — replicate
  2D structure on contemporary ANES; second dimension is substantively
  about race, culture, immigration, not "noise on the first".
- **Bafumi & Herron 2010** (*APSR*) — district-level "leapfrog"
  representation requires both dimensions to interpret cross-pressure.
- **Carmines & Stimson 1989** *Issue Evolution* — the cultural-racial
  dimension *emerged independently* through the 1960s realignment; it
  did not derive from the economic axis. The two were uncorrelated in
  the mass public for much of the 20th century and only began co-aligning
  with the post-1965 realignment.
- **DW-NOMINATE (Poole-Rosenthal; McCarty, Poole & Rosenthal 2006).**
  The 1st dimension explains the bulk of roll-call variance in modern
  Congress; the 2nd dimension is *historically* race/civil-rights and
  has shrunk in importance over the late 20th century **for elites**.
  Hare & Poole 2014 (*Pol Analysis*) document this elite trajectory.
  But: voter-level 2D recoveries (Treier-Hillygus, Hare et al. 2015)
  do **not** show the 2nd dimension as a "lesser version" of the 1st.
  The mass and elite second-dimension stories diverge.
- **Mason 2018** *Uncivil Agreement* — partisan identity binds to
  *both* economic and cultural identities (the "mega-identity"); the
  cultural ones (race, religion, urban/rural) are if anything the
  *primary* sorting axes in the post-1990s great sort.

**Implication.** The literature backs treating the axes as substantively
distinct constructs with different historical dynamics, but it does
**not** support the engine's effective treatment, which is "x is
ideology and y is a vestigial co-variate." The literature actually
flags the cultural axis as the *more* active sorting dimension in the
contemporary US.

## 4. Empirical literature: do they polarize symmetrically?

The empirical answer is: **no — the cultural axis disperses more, not
less.** Direct numbers from `phase9_empirical_targets.md` §3.5.1
(ANES-anchored moments, source: Levendusky 2009, Baldassarri & Gelman
2008, Mason 2018, Treier-Hillygus 2009):

| Decade | var(x) | var(y) |
|---|---|---|
| 1980 | 0.32 | **0.34** |
| 1990 | 0.31 | 0.32 |
| 2000 | 0.34 | 0.34 |
| 2010 | 0.36 | **0.37** |
| 2020 | 0.38 | **0.40** |

In ANES and GSS data, y-variance is **equal to or larger than**
x-variance at every decade. The augmented Phase 9 cloud (combining
typologies + raw-style synthesis) shows `var(y) ≈ var(x)` to within
~10% at every decade. There is no empirical regime in which the
cultural axis is *less* dispersed than the economic axis at the
mass-public level. (DW-NOMINATE legislator-level data is the only
place the 2nd dimension is smaller, and that is an elite phenomenon —
mass voters and legislators diverge here.)

Sorting-rate evidence:

- **Levendusky 2009** *The Partisan Sort* — panel evidence that *both*
  economic and cultural issue positions sort to party from the 1970s
  on; cultural issues (abortion, civil rights, gay rights) actually
  sort *faster* in the 1980s-90s than economic issues.
- **Baldassarri & Gelman 2008** (*AJS* 114:408) — within-population
  `corr(x,y)` rises from ~0.18 (1980) to ~0.52 (2020); both dimensions
  retain real variance throughout (constraint is "alignment", not
  collapse to a 1D subspace).
- **Mason 2018** — affective polarization binds to cultural identities
  (race, religion) at least as strongly as to economic.
- **Hopkins 2018** *The Increasingly United States* — nationalization
  acts on *both* dimensions, with cultural issues arguably the more
  nationalized channel.

There is **no empirical literature** that I can find or that is cited in
our existing notes claiming that the cultural axis should disperse *less*
than the economic axis in the US mass public. The opposite is closer to
the truth.

## 5. Verdict

**(C) Mixed, but heavily weighted toward bug.**

What's real (small justified asymmetry):

- The **±0.30 vs ±0.08 party-centroid placement** is partially defensible
  on Hare-and-Poole grounds (elite DW-NOMINATE first dimension dominates)
  and on the "parties sort economically before culturally" historical
  reading (Carmines-Stimson). A small y-axis party gap at 1980 is
  literature-consistent.
- **Outlet positions** spanning more on x than y is roughly defensible
  against AllSides/Ad Fontes — though those raters themselves are
  contested.

What's bug (silent x-dominance with no literature backing):

- **Party assignment is sigmoid(x) only.** This is the load-bearing
  asymmetry. It hard-wires "party = sign of economic position" into the
  build, despite literature (Mason 2018, Carmines & Stimson 1989) that
  insists party is at least as much about cultural identity. Every
  downstream party-conditional rule inherits this asymmetry.
- **Initial-position draws** add `side*0.15` to x but nothing to y,
  compounding the above.
- **Perception-gap seeding** is `+bias_sign*0.25` on x only, with the
  in-code comment "the dominant (x) axis" — i.e., the asymmetry is
  acknowledged in the code itself, not anchored to literature
  (Levendusky & Malhotra 2016 do not specify which dimension the
  perception gap operates on).
- **2016 Trump-event centroid nudge** is +0.05 on x and 0 on y, but
  Sides/Tesler/Vavreck 2018's Trump-coalition story is *fundamentally
  about the y-axis* (race, immigration, status threat). The model
  encodes Trump as an economic shift.
- **Phase 8f added ±0.08 y-bias** explicitly to unblock the
  `(cx+cy)/2` constraint metric — i.e., it's a metric-driven patch,
  not a literature-anchored centroid placement.

In short: the math is symmetric; the geometry isn't; the geometry's
asymmetry has at best partial elite-DW-NOMINATE justification and at
worst is a silent accumulation of x-centric defaults.

## 6. Implications for Direction D (AnisotropicNoise)

Direction D — adding a noise rule with σ_y > σ_x — would be a **band-aid**
applied to the wrong layer. It would lift var(y) by injecting variance
that has no semantic content: agents drift on y for reasons unconnected
to identity, faction, media, or perception. That's literature-unfaithful
even relative to Levendusky's slow-sorting story.

A literature-faithful y-axis rehabilitation, in priority order:

1. **Symmetrize party-centroid placement** at the build site. Move from
   `(±0.30, ±0.08)` toward `(±0.25, ±0.20)` or similar; the elite
   first-dimension dominance argument supports asymmetry but not at the
   current 3.75:1 ratio. The Hare et al. 2015 2D voter recoveries
   suggest ~1.2-1.5:1 at most.
2. **Two-dimensional party assignment.** Replace `sigmoid(K·pos_x)` with
   `sigmoid(K·(a·pos_x + b·pos_y))` with `a≈b` (Mason 2018 mega-identity:
   party reflects both economic and cultural identity). This breaks the
   x-monopoly on sorting at the root.
3. **Make `PARTY_CUE_SIGMA` carry y-dispersion intentionally** — the σ
   is already isotropic, so this is automatically picked up once the
   centroids are pulled apart on y.
4. **Decompose ELITE_DRIFT** so it explicitly schedules per-axis rates;
   the cultural-axis realignment (Carmines-Stimson) and the post-1990
   cultural-issue sort (Levendusky) need distinct per-decade rates.
5. **Two-axis perception gap.** Levendusky & Malhotra 2016 do not name
   a dimension; remove the "dominant (x)" branch and bias both axes
   away from origin.

If Direction D ships, it should ship *alongside* at least (1) and (2),
not as a substitute. AnisotropicNoise alone would hide the structural
gap behind a parameter and make the next investigation harder.

## 7. Open questions

1. Per-dimension within-party SD targets are not in our existing
   trajectory bands — we calibrate `within_party_sd` as a scalar
   (`(σ_x + σ_y)/2` effectively). A per-axis target would catch this
   class of bug at the metric layer.
2. Whether the elite DW-NOMINATE first/second-dimension *ratio*
   maps cleanly to a mass-population centroid-placement ratio is an
   inference, not a measurement. Hare et al. 2015 give voter-level
   moments; mapping those to (x,y) centroid coordinates requires a
   convention.
3. The cultural axis at the 1980 baseline is the trickiest period.
   Carmines-Stimson says cultural-axis party alignment was already
   underway, but the magnitude is contested (some scholars place
   the bulk of cultural sorting in the 1990s-2000s). The 1980
   centroid placement on y is therefore the place where literature
   under-determines the choice.
4. `IdentitySorting` operates on a 3-vector `identities` attribute,
   not on (x,y); it is the rule most plausibly carrying "cultural
   identity dynamics", but it doesn't directly couple back to the
   ideology y-axis. Whether the intended Mason mega-identity story
   should have `identities` *project to* y at all is a design call
   the spec doesn't make.
