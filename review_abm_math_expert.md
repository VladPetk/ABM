# Peer Review: polarlab — Mathematical and Methodological Critique

*Independent external review by a senior expert in agent-based modeling
and social dynamics. Documentation only — no code, tests, or scripts
read. Read: `ENGINE_OVERVIEW.md`, `methods.md`,
`adr_001_network_primary_engine.md`, `adr_001_implementation_spec.md`,
`phase4_spec.md`, `phase5_spec.md`, `phase6_spec.md`, `phase7_spec.md`,
`phase8_partypull_spec.md` (§§1-2),
`phase8b_historical_replication_design.md`,
`phase8b_historical_replication_spec.md`, `phase8b_results.md`,
`phase8b_calibration_results.json`.*

---

## What works

**The ADR-001 reasoning is sound and unusually self-aware.** Recognising that geometric-proximity bounded confidence "defines an echo chamber in terms of the thing it is meant to explain" is the right diagnosis — it is precisely the criticism that Flache et al. (2017 *JASSS*) levelled against the first generation of HK derivatives. Moving to a network-primary substrate with BC re-interpreted as an edge-weight filter is the right move, and the synthesis (DeGroot/FJ on a homophilous, co-evolving graph) sits inside an established class (Kan, Porter & Mason 2023; Holme-Newman style adaptive networks). The decision to treat *complete-graph* as the rigor gate so HK reproduces by construction is a clean compatibility argument.

**The separation of concerns at the rule level is honest.** Phase 4 §3.2's decision to carry the FJ anchor pull on exactly one rule (`GaussianNoise`, the always-on rule) while scaling every other rule's `d_ideology` by `(1−s)` is mathematically the right reading of the FJ recurrence in an additive-delta pipeline. It avoids the obvious bug of summing many anchor pulls per tick.

**The "move the tag, not the threshold" discipline (Phase 6 §11; methods.md §4.2) is genuinely good methodology.** It inverts the usual ABM failure mode (researchers tune until the desired narrative emerges) into a measurement gate that *forces* the project to publish what the model actually does, not what it was hoped to do. The §11 consolidated bucket test will fail loudly under future drift.

**The Phase 8b results document is unusually candid.** Reporting 11 of 20 primary-metric cells out of band, naming the affect-dynamics overshoot as a "real model property," and surfacing the M3 ablation contamination (catching that affect-reset-to-zero was producing a sign-flipped contribution) — these are signs of intellectual honesty that ABM peer reviewers rarely see. The phrase "this is the discipline working" applied to a *caught error*, not a triumph, is the right framing.

**The provenance L/N/E tagging (ENGINE_OVERVIEW §6) is a model practice.** Most ABM papers blur which mechanisms are literature-faithful, which are scaffolding, and which are extrapolation. Naming each component and labelling it explicitly is exemplary.

**The graded logistic filter recovers HK exactly at T=0 by construction** (Phase 4 §4.1 code branches on `temperature <= 0`). The `default = 0` on the rule means canonical tests run literal HK with no fallback path — that is the cleanest possible compatibility design.

---

## What's questionable

### 1. The "(1−s) at every apply site + anchor pull at one rule" FJ realisation is *almost* canonical, but not quite

The Friedkin-Johnsen recurrence is
`x_{t+1} = (1−s) · A x_t + s · x_0`
where `A` is the row-stochastic influence matrix. Phase 4 §3.2 decomposes this into a per-rule scaling and a separate additive anchor pull. The issue: in the canonical FJ formulation, `(1−s) · A x_t` is one operator that already aggregates all neighbour influence and then multiplies by `(1−s)`. polarlab instead applies `(1−s)` to each rule's contribution separately, *and then sums*. If two rules each contribute `d_1` and `d_2`, the agent moves by `(1−s)(d_1 + d_2) + α·s·(anchor−x)`. That is fine *if* you accept the rules as additive linear pulls, which the pipeline contract enforces. But it changes the meaning of `s`: stubbornness is no longer "weight on innate position" inside one update, it is "uniform damping coefficient on the sum of all forces." This is closer to a *weighted FJ* than a canonical FJ. The behaviour is recognisably FJ-like, but a precise equivalence to Friedkin & Johnsen 1999 would require the influence operator to act *once* per tick on the aggregated next position, not per-rule on each delta. **Worth flagging in methods.md §3 — current language ("the FJ recurrence is faithful") is overstated.**

### 2. The anchor pull magnitude is plausibly under-scaled

`α = 0.05` with `s ≈ 0.286` (Beta(2,5) mean) means the typical anchor pull per tick is `0.014 × (anchor − ideology)`. Over 200 ticks with no other forces, the half-life back to anchor is on the order of 50 ticks; with other pulls active, the anchor is more a soft tether than a hard restorative force. This is fine, but the sensitivity sweep (methods.md §5.4) shows the no-collapse property *fails* at `α = 0.10` (mid-band fraction drops to 0.773). That's a narrow window of viable α. **Combined with the per-rule (1−s) accounting issue above, the FJ parameters are doing more work than a single anchor coefficient should** — the apparent robustness is partly because `(1−s)` is acting as a hidden second damping channel.

### 3. The graded logistic filter and the "HK as T→0" claim has a subtle phase-behaviour caveat

The logistic `w(d) = 1/(1+exp((d−ε)/T))` does converge pointwise to the HK step function as `T → 0`. But for small T > 0, the weighted mean is computed over *all* network neighbours (Phase 4 §4.1 code: `ds = ...` over all neighbours, not within ε), with the logistic deciding weight. This means agents with no in-ε neighbours but some near-ε neighbours still get pulled — they have a positive (small) target — whereas in canonical HK they would be inert. This is a genuine departure from HK at any T > 0, not merely a smoothing: it removes the *fragmentation phase transition* that defines HK's interesting behaviour at tight ε. **The HK community has explored exactly this question** (Lorenz 2007 reviews several smoothed variants and shows phase diagrams differ from HK). The project's claim that T = 0.05 "still recovers HK convergence" should be tested against the standard HK fragmentation/consolidation phase boundary at tight ε — not just the loose-ε consensus test. If the boundary moves, that is a phenomenon worth reporting.

### 4. The two-axis bucketing thresholds (0.05, 0.15) are not defended quantitatively

methods.md §4.1 lists the cutoffs without justification. Calling them "fixed by the spec and not adjusted to fit a desired narrative" is correct discipline, but it does not establish that *these particular numbers* carry empirical meaning. Why is `Δsep = −0.13` partial and `−0.16` real? The thresholds are dimensionless quantities on a metric whose population-level meaning depends on engine calibration; under a different scenario size, network density, or `STAGE_SEEDS` count, the same cutoffs might bucket entirely different effects. **The thresholds need either an empirical anchor (e.g., a published effect-size scale) or a sensitivity analysis showing the bucket assignments are robust under cutoff perturbation.** Without that, "X5 is partial at −0.14, would be real at −0.15" is arbitrary precision.

The "measurement-blessed, not design-declared" claim is methodologically true for the *label*, but the *threshold scheme* itself is design-declared. That's a meaningful gap.

### 5. Statistical power: 12 seeds for pillar, 5 seeds for historical — both are too few for several claims

For the pillar at 12 seeds, an ensemble mean Δsep of −0.14 (X5, partial) sitting just inside the partial/real boundary at −0.15 needs a confidence interval to be meaningful. With n=12 stochastic trajectories on a noisy population, the standard error on the mean Δsep is likely 0.02–0.05 (no SE is reported in any document I read). That means X5's bucket label is statistically indistinguishable from "real," and the X3 backfire reading (Δsep = +0.27, ostensibly the strongest non-trivial number) needs a published SE to know whether the +0.21 / +0.25 / +0.27 sensitivity-sweep variation is signal or noise. **None of the §5 sensitivity tables in methods.md report uncertainty.**

For Phase 8b, 5 seeds across decades is genuinely too few to draw the conclusions the results document draws. The 2025 affect value of −0.90 vs. the band floor −0.85 is a 0.05 difference; with 5 seeds, the SE is plausibly ≥ 0.05. The phrase "real model property, not knob-adjustment miss" requires statistical confidence the seed count cannot provide. The compute argument (5 seeds ≈ 10–12 min/ensemble) is real but not load-bearing — the analysis cannot conclude what it concludes from this sample. **At minimum, every reported decade-end value needs a 95% CI, and the in-band/out-of-band call should be made against the *interval*, not the mean.**

### 6. Identifiability of mechanism contributions in Phase 8b is weak

The ablation table (results §4) reports five mechanisms each contributing a Δ at 2025. The Δs are small (0.001 to 0.099) and the seed count is 5. M3 cohort replacement contributes Δaffect = +0.099 and Δxc = −0.097; M4 asymmetric polarization contributes Δsep = +0.042; the others contribute < 0.02 on every metric. **The smaller Δs (M1, M2, M5) are likely within the noise floor of a 5-seed ensemble, and the attribution to particular mechanisms is unreliable.** Several mechanism combinations may produce statistically indistinguishable trajectories. Without a full factorial design (2^5 = 32 ablation cells) or a sensitivity-analysis decomposition (Sobol indices), claims about per-mechanism contributions are model-fitting artefacts, not causal attributions.

The deeper identifiability issue: M1 heterogeneity (Beta-distributed `epsilon`/`α`/`affect_lr`) overlaps mechanistically with M3 cohort replacement (which also injects heterogeneity across time). The two are unlikely to be jointly identified from 5 trajectories.

### 7. Decade-by-decade calibration is mid-way between pre-registration and curve-fitting

The discipline is well-stated: pillar invariants forbidden, per-decade scope limited, ≤2 retries per decade, accept-miss-and-document. But within that envelope, the calibration loop has at least 7 tunable knobs per decade (spec §10.2) and four primary gating metrics. With ≤2 retries and a knob → metric mapping that pre-selects which knob to adjust, the discipline is real but the *degrees of freedom against the data* are still substantial across 5 decades. The fact that decades 2000+ all miss on all four primary metrics suggests the calibration ran out of usable knob range — but if it had succeeded, the success would have come from ~35 tuning passes across the whole arc, which is on the order of the data points being fit. **Per-decade fitting with bounded retries is not pre-registration; it is bounded curve fitting with honest reporting.** The doc says as much (§1: "calibrated historical reconstruction, not strict out-of-sample forward prediction"), but the "guardrails" language somewhat overstates the protection. The honest framing — which the project mostly accepts — is that 8b is a *consistency check*, not a *validation*.

### 8. Provenance tags that should be E but are tagged L

Reading ENGINE_OVERVIEW §6, two items merit reclassification:

- **"Network is the influence substrate" (ADR-001)** is tagged **L**. The intellectual lineage (DeGroot, FJ) is L; the *specific architectural choice* of a homophilous co-evolving graph with logistic-weighted BC, FJ anchoring, and rule-additive deltas is **E** (extrapolated). The bare "network-based averaging" tradition does not prescribe the synthesis.
- **"Homophilous tie-formation" (Wong et al. 2006)** is tagged **L**. Wong et al. is one of *several* spatial-network construction approaches; the specific edge-probability decay function and the combined ideology+social-coord distance are model-specific. **L→E** would be more honest.

Three items correctly tagged **E** that the project should be more cautious about:
- The graded logistic filter (Phase 4 F2) — see point 3 above; the phase behaviour may differ from HK in ways the project hasn't tested.
- The X6 cooperative-mute as edge-level — flagged as "modelling judgment" honestly, but the X6 backfire reading is one of the more rhetorically loaded findings, and the underlying choice carries the bulk of the result.
- The bucket thresholds (0.05/0.15) — see point 4.

---

## What's wrong

### W1 — methods.md §3.1 contains an arithmetic discrepancy that the doc partly acknowledges but does not resolve

The pillar's full-200-tick Δaff is −0.85; the projection to a 42-year (126-tick) window via linear scaling gives `−0.85 × (42/67) = −0.533`. The ANES anchor is −0.56. The document calls this "within ~5%" — fine in magnitude. But the test (`test_pillar_affect_trajectory_matches_anes_within_band`) asserts the *200-tick* trajectory against an ANES-projected value of −0.89 with ±20% band, i.e. checks [−0.71, −1.07]. The actual ANES anchor is on the 42-year window, not the 67-year window. **The projection from 42-year to 67-year is non-linear by the document's own admission** ("the pillar's S2/S3 trajectory is non-linear"), so the ±20% band on the 67-year endpoint is being checked against a *linearly-extrapolated* −0.89 that the document itself says is the wrong scaling. The test is a regression guard, not an ANES-anchor check. This should be stated cleanly in methods.md: the test guards *trajectory shape*, not anchor agreement.

### W2 — Phase 6 R5 sign convention is genuinely confused in the spec text

Phase 6 §1, R5: `effect ≥ 0.15 (in the helpful direction) → "real"; effect ≤ -0.05 (polarization rises) → "backfire"`. Then §9: `Δsep ≥ -0.15 (sep falls by at least 0.15 — interventions help) → "real"`. The two passages use *opposite* sign conventions for the helpful direction. methods.md §4.1 finally settles it: helpful = negative Δsep. But the Phase 6 spec leaves a literal contradiction on the page; if a future implementer reads only §1, they will get the wrong direction. Minor but real.

### W3 — Phase 5 §3.2 normalisation note is mathematically loose

`d_iss / radius` with `radius = 1.5` "puts issue distance into roughly [0,1]" — but the maximum issue distance on `[−1,1]²` is `2√2 ≈ 2.83`, so the ratio can reach 1.89. The spec notes this. The `identity_term` is divided by `2.0` to map to `[0,1]`. So the blended `disagreement` term is a mix of one quantity in `[0, 1.89]` and one in `[0, 1]`, and the linear `0.5*identity + 0.5*issue` blend is not a true convex combination — the issue axis dominates at extreme pairs. The baseline of 0.10 is calibrated relative to the assumption that both terms are bounded in [0,1], but the issue term breaks that assumption. **The valence formula is not numerically bounded in the way the spec describes.** The downstream affect clip at [−1, 1] catches it, but the *contribution-per-encounter* can exceed `lr * (0.5*1.89 + 0.5*1.0 + 0.10) ≈ lr * 1.145` instead of the implied `lr * 1.10`. Small absolute error; structurally wrong.

### W4 — The X6 finding's mathematical reading is plausible but the cited literature does not support the model's specific quantitative inference

ENGINE_OVERVIEW §5 explains X6's backfire as "per-encounter halving × tripled encounter volume nets a deeper negative drift." That's an arithmetic identity in the model. But ENGINE_OVERVIEW then writes: "The model is saying something defensible: contact reduces per-encounter prejudice but doesn't reverse what's already there." That inference relies on the Pettigrew & Tropp `r ≈ −0.21` being a *per-encounter* effect that compounds linearly. In the meta-analysis, `r = −0.21` is the *cumulative* effect of contact on prejudice across the studies' time windows; the rate is not specified, and there is no warrant for treating it as a per-encounter multiplier on a per-tick affect update. The "halving" interpretation is the model's choice, not Pettigrew & Tropp's reading. The X6 backfire result is then an *artefact* of mapping a cumulative effect onto a per-encounter operator. **The project flags this honestly as the "most interesting open question" — that is good — but the rhetorical framing in §5 ("the model is saying something defensible about contact-hypothesis claims") is stronger than the citation chain supports.**

### W5 — Phase 6 affect-gating + Phase 5 sign-fix interaction is a hidden coupling

Phase 5 A1 made affect strongly negative-going. Phase 6 R1 then made repulsion fire only when `warmth < −0.3`. Methods §4.1 reports the pillar's S2 affect lands at ≈ −0.85 — *well past −0.3* — so R1's gate is essentially always open in the polarized end-state. The "affect-gated" mechanism is presented as adding nuance (Bail-style conditional backfire) but operationally fires for ~all out-party encounters in the regime where it's tested. This is the right *direction* (Bail's conditional finding is preserved as a possibility) but in practice the gate is not gating; it's a constant pass-through. **The model's "X1 backfires because R1 affect-gate fires" claim is true, but the affect-gate is doing no discriminative work in the relevant regime.** If R1 were tested at a less-cooled scenario (early-stage release, or a less-sorted population), the gate would actually matter; in the shipped regime it does not. The project should report the gate's *firing rate* as a diagnostic, not just the bucket label.

---

## Top 5 ranked recommendations

**1. Report confidence intervals everywhere, and re-evaluate bucket assignments against intervals, not point estimates.** This is the single most important methodological fix. The 12-seed and 5-seed ensembles need standard errors on every reported metric; the bucket assignments need to be made against the lower/upper CI bound, not the mean. The bucket cutoffs (0.05, 0.15) need empirical anchoring or a robustness check. Without this, the headline finding "two backfire, three null, one partial, zero real" is more confident than the data supports.

**2. Replace 5-seed Phase 8b with a larger ensemble before drawing any "real model property" inference.** The compute argument (~8 hours) is not load-bearing for a one-time validation exercise; ~24-48 hours at 15-20 seeds would let the project make the inferences it currently makes only conditionally. The ablation table specifically needs a higher seed count — the M1/M2/M5 contributions are below the plausible noise floor at n=5.

**3. Make explicit the departure of polarlab's FJ realisation from canonical FJ, and the departure of the graded logistic filter from canonical HK.** Methods.md §3 should add a paragraph stating that (a) the per-rule `(1−s)` scaling sums multiple pulls before damping, which differs from the standard "damped influence operator" form, and (b) at any `T > 0`, the logistic filter pulls agents toward out-of-ε neighbours with small weight, which moves the HK fragmentation phase boundary. Neither is wrong; both are extrapolation that the L tagging currently obscures.

**4. Run an HK phase-diagram test for the graded filter, not just loose-ε consensus.** The canonical HK suite checks ε regimes far from the fragmentation boundary. The interesting question is whether `T = 0.05` shifts the consolidation/fragmentation transition at tight ε. A single-figure ε-T sweep would answer this and either validate the "HK as T→0" claim more strongly or expose a known phenomenon worth surfacing.

**5. Re-classify several L tags as E, and add a quantitative defense of the 0.05/0.15 bucket cutoffs.** The provenance discipline is good; tightening it would make the project more credible. The bucket thresholds in particular are dimensional choices that need a sensitivity analysis (how do the X1-X6 bucket labels move under cutoffs of {0.03/0.10}, {0.05/0.15}, {0.08/0.20}?) to defend the chosen cutoffs as robust.

---

## Bottom line

This is a more methodologically self-aware ABM than most. The ADR-001 reasoning is sound; the honesty schema, measure-then-bless gate, and L/N/E provenance tagging are good practice; the Phase 8b results document is candid about misses in ways the field usually isn't. The project is closer to a peer-publishable artefact than its "teaching tool" framing suggests.

But the project also asks readers to accept several quantitative claims (X3 robustly backfires; X5 is partial-but-not-real; X6 backfires on affect; the model tracks ANES within 5%) that rest on point-estimate ensemble means without reported uncertainty, on bucket thresholds without empirical defense, and on a graded-confidence formulation whose phase behaviour has not been mapped against the HK literature it claims to generalise. The Phase 8b inferences in particular are reaching beyond what 5 seeds can support. None of these are fatal; all are addressable. The fixes are: report uncertainty, defend the cutoffs, test the phase diagram, and let the L/N/E discipline cut deeper.

The X6 paragraph in ENGINE_OVERVIEW §5 is the most striking piece of writing in the documentation — it asks the right hard question. The reviewer's question back: does the model warrant the inference, given the cumulative-vs-per-encounter mapping ambiguity in Pettigrew & Tropp? That deserves more space, not less.
