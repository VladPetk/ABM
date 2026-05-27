# Second Peer Review of polarlab — Mathematical and Methodological Perspective

*Follow-up review by the same senior ABM/math-methods expert who
reviewed the project before. Documentation only (no code). Compares
the post-response state (Phase 8c + 8d + historical re-run) to the
first review's critiques.*

---

## Response assessment

| Item | Verdict |
|---|---|
| FJ realization clarity (D5) | ✓ |
| ANES projection note (D4) | ✓ |
| Phase 6 R5 sign-convention fix (D2) | ✓ |
| 8d decade calibration discipline (no per-decade re-tuning on augmented engine — cleaner than 8b) | ✓ |
| Statistical power / CIs at 20 + 15 seeds with ±SE in §4.3 | partial |
| Bucket cutoff defense via sensitivity sweep | partial |
| Provenance L→E reclassifications | partial |
| X6 agent-level cooperative mute (mute scales with cooperative_share) | partial (relocates rather than resolves the cumulative→per-encounter mapping ambiguity) |
| §3.2 normalization | partial (doc-only; rescaling deferred) |
| Historical patterns (affect-in-band etc.) | partial (honest reporting but 2025-affect-in-band is largely *compositional*, not mechanism) |
| HK phase-diagram test (deferred) | defensible deferral — backlog entry good, but methods.md still understates the T=0.05 phase-behavior unknown |
| Identifiability of mechanism contributions | got worse — 8d's half-participating Independents introduce compositional contributions to every aggregate metric |

## Residual critique (ranked)

**1. Compositional vs mechanism contribution to 2025 affect is undecomposed.** The 8d historical re-run reports the affect 2025 endpoint moving from −0.90 (Phase 8b) to −0.82 (in band). The doc attributes this to a mix of: positive-going affect channel (Obama-2008 warmth), 2016 identity-threat spike pattern, and 12% Independents being affect-neutral. But the 12% Independents *trivially* pull the population mean affect less-negative just by being there — they're 12% of agents who don't update affect at all, so they always sit at zero. The mechanism contributions can't be cleanly separated from this compositional shift without running {Independents on/off} × {augmented engine / 8b baseline} as a 2×2.

**2. Two-stage extrapolation on X6.** The original concern was that mapping Pettigrew & Tropp's cumulative r=−0.21 onto a per-encounter mute (`cooperative_mute = 0.5` at edge level) was an undeclared extrapolation. The response moved to agent-level (mute scales linearly with `cooperative_share`). That doesn't resolve the cumulative-vs-per-encounter mapping — it just relocates the extrapolation from "what's the per-encounter scaling" to "what's the relationship between agent-level cooperative share and per-encounter dampening." Plus a new `coop_positive_magnitude = +0.05` knob was added that wasn't in the prior literature anchor at all. The X6 affect re-bless rides on the layered stack of these choices.

**3. 2016 identity-threat magnitude calibrated to the very ANES curve it's scored against.** The identity-threat event amplitude was set so that the 2016 spike pattern appears in the historical re-run. But the same ANES thermometer is the empirical target for the affect trajectory. Tuning the threat amplitude to reproduce the empirical curve, then citing the curve match as evidence the mechanism works, is circular. The mechanism may be right, but the magnitude is post-hoc calibrated.

**4. X4 shared-identity prime has 3 stacked calibration choices** — 20% population, 30-tick window, identity_weight_override = 0.1 — none of which are individually anchored to Levendusky 2021's actual experimental parameters. The "null/null" measured result might be telling us the literature-faithful mechanism doesn't move the macros, or it might be telling us the stack of three modest choices added to "doesn't fire visibly."

**5. Parallel-seed runner's bit-identical determinism claim is asserted, not visibly verified.** A keystone regression test was added (`test_pillar_S4_bit_identical_at_zero_fraction` for the 8d Independents work), but I didn't see equivalent evidence for the parallel runner — just the assertion that "the determinism claim is sound." For a piece of infrastructure that 3.5×-9× compresses the wall clock for the whole project, this deserves an explicit serial-vs-parallel diff in the docs.

**6. SE reporting in §4.3 is much tighter than expected.** The methods.md table reports ±SE values of 0.001-0.007 for Δsep / Δaff across 15-20 seeds. That implies per-seed standard deviations on the order of 0.005-0.03, which is plausible but tight for stochastic ABM ensembles. The source of variance (intra-seed measurement noise vs cross-seed trajectory variance) isn't documented, and the CIs aren't shown as 95% bands. Worth surfacing.

**7. HK phase-diagram test deferred to backlog.** The deferral is defensible (it's a correctness check that probably comes back fine), but methods.md still asserts T=0.05 "recovers HK convergence" without testing against the tight-ε phase boundary. The deferral should be matched by a sharper hedge in methods.md.

## New issues surfaced by the response

- The 8d Independents-pulling-mean-affect-less-negative phenomenon (residual 1) means the most-discussed Phase 8b miss (over-cold affect) was largely solved by adding 12% null-affect agents, not by the new affect-channel mechanism per se. This deserves to be disambiguated honestly.
- The "1 backfire / 4 null / 1 partial / 1 real on affect" story arc has become substantially less doom-laden than the original Phase 7 "0 real" headline. But the X5 partial→partial (at default cutoff) and X6 real-on-affect both sit at-the-boundary. If you tighten cutoffs to {0.03/0.10}, X5 goes to "real on issue" and X6 goes to "partial on issue + real on affect" — i.e. the same intervention library would tell a much more optimistic story under modestly tighter cutoffs.
- The 8d half-participating Independent class affects every aggregate metric. The macro story under 12% Independents and under 0% Independents differs in ways that go beyond the obvious. Per-mechanism attribution claims (like "8c §2 fixed the over-cold affect") now need to disambiguate "fixed by the mechanism" vs "fixed by changing the population composition."

## Top 5 ranked recommendations going forward

1. **Run the 4-cell decomposition** {Independents on/off} × {augmented engine / 8b baseline}. Likely reframes what 8d achieved on the affect endpoint — and either confirms the mechanism contribution or reveals it as mostly compositional.

2. **X6 calibration sensitivity sweep** on both `coop_positive_magnitude` ∈ {0.02, 0.05, 0.08, 0.10} and `cooperative_mute_shape` (linear vs sublinear). If X6's "real on affect" bucket changes under reasonable variations, the headline is fragile.

3. **Add an explicit serial-vs-parallel determinism test** in the test suite, not just an assertion in the docs. For a 3.5×-9× compute-multiplier this deserves more than `# bit-identical to serial` comments.

4. **Disambiguate identity-threat magnitude calibration in methods.md.** Either tune the threat amplitude to a pre-2016 ANES point and let 2016 be a forward prediction, or explicitly state the magnitude is post-hoc fit to the 2016 spike. Both are honest; the current presentation isn't quite either.

5. **Tighten the SE reporting** to show 95% CIs as bands, source of variance, and any inter-seed correlation effects. Especially important for the close-call bucket assignments (X5, X6-on-issue).

---

## Bottom line

The discipline held through the response cycle — pillar bit-identity preserved, no forbidden knobs touched, honest documentation throughout. Several methodological asks (CIs, FJ clarity, sign-convention fix, cleaner 8d calibration) are properly addressed. But the response also introduced new methodological exposure: the X6 "real on affect" headline rides on a layered stack of calibration choices that didn't all get sensitivity-tested; the 2025 affect-in-band finding is more compositional than mechanism-driven; the 8d Independents class makes per-mechanism attribution harder rather than easier. The project is more empirically defensible than before; the headline story arc, however, requires more disambiguation before it's quite peer-publishable.
