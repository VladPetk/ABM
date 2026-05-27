# polarlab — Second-Round External Review Synthesis

*Unified synthesis of two independent second-round expert reviews
(polarization expert R1; ABM/math-methods expert R2) of the polarlab
project after the Phase 8c + 8d + historical re-run response cycle.
Documentation only. The full critiques are in
`review2_polarization_expert.md` and `review2_abm_math_expert.md`;
the first-round versions are in `review_synthesis.md`,
`review_polarization_expert.md`, `review_abm_math_expert.md`.*

---

## 1. Where they agree (the most robust findings)

- **The response cycle did substantive work.** Both reviewers open with positive verdicts on the majority of items and explicitly call out that the project is "meaningfully more defensible" (R1) / "more empirically defensible" (R2) than before. Discipline held; no forbidden knobs were touched.

- **The X6 `coop_positive_magnitude = +0.05` is an unflagged calibration knob carrying too much load.** Both reviewers' single highest-ranked recommendation is the same: run a sensitivity sweep at {0.02, 0.05, 0.08, 0.10}. R1 frames it as the new headline working lever; R2 frames it as a layered stack of un-anchored choices. Same verdict.

- **The X6 "real on affect" finding is now the most fragile-headlined result.** Both reviewers note the previous critique (edge-mute too conservative) has moved to a new critique (positive-valence add is the new artifact). Both think the headline rides on choices that didn't get sensitivity-tested.

- **The X6 `cooperative_mute` cumulative-vs-per-encounter mapping was not resolved by the agent-level relocation.** Both explicitly say the relocation moved the extrapolation question without answering it.

- **2025-affect-in-band is more compositional than mechanism-driven.** R1: 8d Independents reducing X1 magnitude is only partial vindication; the 0.253 endpoint is still 5-10× larger than Bail. R2 sharper: the 12% Independents trivially pull mean affect less-negative just by being there, and the mechanism contributions can't be separated from compositional shift without an explicit 2×2.

- **The bucket story is still close to the edge.** Both note that at-the-boundary classifications (X5 partial, X6 real-on-affect) would flip under modestly different cutoffs or different calibration.

---

## 2. Where they disagree or diverge in framing

- **What the central remaining problem is.** R1 frames it as *measurement gaps* (X7 not run historically, affect-gate firing rate not reported, partisan-only cross-cutting submetric missing, within-party SD post-2000 deferred). R2 frames it as *attribution / identifiability degradation* (the 12% Independents make per-mechanism attribution harder, not easier; the 2×2 decomposition is the missing primary test).

- **Severity of the X4 result.** R1 lists X4 as "✓" (Levendusky 2021 reimplementation done). R2 lists it as a partial concern: three stacked un-anchored calibration choices may have produced null/null because the literature-faithful mechanism doesn't move macros, OR because the stack adds to "doesn't fire visibly" — the result is uninformative.

- **The 2016 identity-threat amplitude.** R2 identifies a circularity concern (amplitude tuned to reproduce the 2016 spike, then the spike match cited as evidence). R1 just lists the identity-threat mechanism as "✓" — does not engage circularity.

- **The historical-arc framing of X7.** R1 identifies the missing X7 historical run as a major gap (the cleanest experimental literature in the field unmeasured in its meaningful context). R2 does not raise this at all.

---

## 3. Each reviewer's single most important unique insight

**R1:** **X7 perception-correction was never tested in its meaningful context.** The whole point of adding the perception-gap construct + X7 intervention was to test the cleanest experimental depolarization literature in the field (Levendusky & Malhotra 2016, Ahler & Sood 2018, Druckman et al. 2022). The historical re-run only ran baseline — X7 wasn't fired as a historical intervention. The pillar-context null/null measurement doesn't test what the literature actually says. This is a leverage-aligned response gap.

**R2:** **The 4-cell decomposition {Independents on/off} × {augmented engine / 8b baseline} is the missing primary test.** The 2025-affect-in-band finding is most likely *compositional* — 12% null-affect agents pulling mean affect less-negative arithmetically — rather than mechanism-driven. Without the 2×2, the project cannot disambiguate "fixed by the mechanism" from "fixed by changing the population composition," and the per-mechanism attribution claims (8c §2 etc.) are unsupported.

---

## 4. Blind spots

**R1 missed:**
- **Identity-threat circularity.** Did not catch that the 2016 amplitude was tuned to reproduce the very curve it's being scored against. This is exactly the literature-fidelity-vs-fitting question R1 is best positioned to flag.
- **Compositional vs. mechanism decomposition.** Did not push for the 2×2 design, which is the math-methods framing of the same "magnitude only halved" concern R1 raised about X1/Bail. R1 noticed the symptom; R2 named the test.

**R2 missed:**
- **X7 historical measurement gap.** A perception-correction mechanism added in direct response to a literature complaint, then not run in the historical context where it would matter — this is a methodological/design defect R2 should have caught, not just a literature complaint.
- **Affect-gate firing-rate diagnostic.** R2 raised this in round 1 (gate is doing no discriminative work in polarized regime); R1 flagged that the promised §11 diagnostic didn't appear. R2 did not notice their own round-1 ask went unanswered.
- **Within-party SD post-2000 collapse persists.** R1 flagged this as the deepest structural miss honestly deferred; R2 does not engage it.
- **Cross-cutting metric needs splitting under three-party.** R1 caught a metric-semantics issue (Independent↔partisan ties count as cross-cutting under existing metric, breaking the pre-registered band comparison). R2 missed this entirely despite being a math-methods reviewer.

---

## 5. Ranked action list

1. **Run the {Independents on/off} × {augmented engine / 8b baseline} 4-cell decomposition** *(R2 #1)*. The 2025-affect-in-band finding is likely more compositional than mechanism-driven; this is the only design that disambiguates it. Highest priority because it could reframe the headline empirical improvement of the entire response cycle.

2. **X6 `coop_positive_magnitude` sensitivity sweep** at {0.02, 0.05, 0.08, 0.10} *(both R1 #1 and R2 #2)*. If the X6 affect bucket changes across the sweep, the new headline working lever is fragile. R2 adds: also sweep `cooperative_mute_shape` (linear vs sublinear).

3. **Add X7 historical-arc measurement** — fire X7 at 2010 or 2015 in the historical scenario and measure trajectory delta *(R1 #2)*. Without this, the perception-correction mechanism that was added to address round-1 critique is unmeasured in its meaningful context.

4. **Disambiguate identity-threat magnitude calibration in methods.md** *(R2 #4)*. Either tune the amplitude to a pre-2016 ANES point and let 2016 be a forward prediction, or explicitly state the magnitude is post-hoc fit to the 2016 spike. Current presentation is neither and risks reading as circular.

5. **Per-agent `media_cue` analog** to address the within-party SD post-2000 collapse *(R1 #3)*. The diagnostic is clear and the fix mirrors Phase 8a's `party_cue` pattern exactly. Deferred but the leverage is high.

6. **Add affect-gate firing-rate to standard §11 reporting** *(R1 #4; originally R2 round-1)*. The only direct empirical handle on whether the affect-gated repulsion mechanism is discriminating between regimes. Promised per D6, not delivered.

7. **Tighten SE reporting** to 95% CI bands, document variance source (intra-seed vs cross-seed), explicitly state determinism evidence for the parallel runner via an actual serial-vs-parallel diff *(R2 #3 + #5 + #6)*. Plus add a partisan-only cross-cutting submetric so the historical-arc target comparison is apples-to-apples under three-party *(R1 #5)*.

---

## 6. How this round compares to the first review

**The project moved forward substantively.** Round 1's headline critiques were largely structural: missing positive-going affect, missing perception-gap construct, missing identity threat, X3 category error, asymmetric Bail, FJ realization clarity, sign-convention bugs, statistical power. Both reviewers in round 2 verify most of these are now genuinely addressed. The L→E reclassifications happened. The sign convention is fixed. CIs are reported (R2 partial verdict — tighter than expected but unbanded). Provenance is cleaner. The positive-going affect channel and perception-gap construct were added. Identity threat was added. The X3 category error was fixed via per-outlet exposure. Independents class was added.

**The 2025-affect-in-band result is the genuine empirical milestone.** R1 calls it "the kind of validation milestone the project was missing." R2 confirms the discipline held through the response cycle.

**But the residual concerns are differently severe, not less severe.** Round 1's concerns were broad and structural — point estimates without uncertainty, mechanism inventory gaps, undefended thresholds. Round 2's concerns are narrower but harder to resolve: compositional-vs-mechanism attribution (R2), measurement gaps for newly-added mechanisms (R1's X7-not-historical), and the new X6 calibration knob that quietly carries the post-response headline. The project traded a broad set of structural misses for a smaller set of second-order attribution problems.

**The story arc is now contested in a new way.** R2 flags that the "1 backfire / 4 null / 1 partial / 1 real on affect" story has become "substantially less doom-laden" than round-1's "0 real" headline — but several boundary classifications would flip under modestly tighter cutoffs, meaning the same intervention library tells a much more optimistic story under {0.03/0.10}. This is structurally the *same* bucket-fragility concern from round 1, now operating in the optimistic direction rather than the pessimistic one.

**Overall trajectory:** the project is meaningfully more defensible than at first review, but the headline narrative now requires more disambiguation, not less, before it is peer-publishable. The strongest single round-2 ask — R2's 4-cell decomposition — exists because the round-1 fix (adding Independents) created the round-2 problem (compositional contamination of mechanism attribution). The response cycle was honest and substantive; the next cycle needs to be smaller and surgical.
