# Phase 8c Implementation Spec — Review-Anchored Engine Extensions, Honesty Re-Audit, Statistical-Robustness Pass

*Compound spec covering all seven Phase 8c sub-phases under one roof
(per Vlad's workflow change). The roadmap (`phase8c_roadmap.md`) gives
the high-level ordering and forks; this document is the
implementation contract. Each §N is a self-contained spec for that
sub-phase in the house style: decisions pinned, files listed,
mechanism math, judgment forks flagged, tests defined, measure-then-
bless gate where labels can't be pre-measured.*

*Phase 8c addresses the must-do + high-value items from the two
external expert reviews (`review_synthesis.md`,
`review_polarization_expert.md`, `review_abm_math_expert.md`).
Out-of-scope items (HK phase-diagram test, income/inequality channel,
demographic stratification beyond cohort replacement, formal Sobol
identifiability) are explicitly deferred to a hypothetical 8d.*

---

## 0. Whole-phase decisions pinned

| # | Decision | Choice |
|---|----------|--------|
| W1 | **Sub-phase ordering.** §1 → §2 → §3 → §4 → §5 → §6 → §7. The order reflects dependencies — D3 (§1) feeds the §2 affect rewrite; §2's new `AffectiveUpdate` is the substrate every later engine extension (§3-§6) wires into; §7 is the statistical pass that re-measures the final library. §3-§6 can in principle interleave once §2 lands; the proposed sequence reflects work-size and narrative ordering. |
| W2 | **One compound spec, one round of confirm.** Vlad confirms this whole document up-front. Per-sub-phase confirms happen only if a section's implementation surfaces a genuinely new fork the spec didn't anticipate — in that case, hard-stop and flag. The standard cadence per section is: implement → independent review → test-verify → SHORT result post → next section. |
| W3 | **Forbidden knobs preserved.** Pillar S0-S4 bundle values, TICKS_PER_YEAR, FJ_ALPHA, BC_TEMPERATURE, BC_AFFECT_WEIGHT, TR_AFFECT_WEIGHT_REWIRE, BACKLASH_AFFECT_THRESHOLD, COOPERATIVE_MUTE, PARTY_CUE_SIGMA, HK canonical thresholds, X1-X6 bucket labels (until §7 re-blesses them) — all stay pinned through every section. If a section's implementation pressures one of these, hard-stop and flag. The §1 D-fixes touch documentation and math display, not the knobs. |
| W4 | **Pillar-fallback discipline preserved.** Every new agent attribute introduced in §2-§6 must be read by rules with rule-level fallback (`agent.state.attrs.get(KEY, DEFAULT)`) so non-pillar scenarios (`compass_basic`, `actb`, etc.) remain bit-identical to Phase 8b. The 73-test pillar invariant suite must stay green through every section. |
| W5 | **Pillar attribute additions guarded.** Any new agent attribute added by the historical-arc builder (`build_engine` in `historical_arc.py`) is also added to the pillar's builder (`calm_to_camps.build_engine`) only when needed to keep §11 measurement coherent. If a new mechanism is meant to be inert in the pillar's baseline progression (e.g. identity-threat is pillar-inert), the pillar builder does NOT seed the attribute — the rule's pillar-fallback default carries the no-op behaviour. |
| W6 | **Honesty discipline preserved.** No section is allowed to tune past a literature-anchored value to chase a bucket. If a re-measurement produces a label different from the prior reading, the LABEL changes — not the threshold and not the mechanism's literature-anchored parameter. The new label is documented and committed. (This is the "move the tag, not the threshold" discipline that survived Phases 6/7/8a/8b.) |
| W7 | **Tests grow, never shrink.** The 73-test pillar suite grows as 8c adds mechanism tests with pillar-fallback assertions. No test currently passing in 8b is allowed to be deleted or weakened in 8c. New tests added in 8c follow the same discipline (unit tests for mechanism, regression tests for bit-identical non-pillar scenarios, §11-style bucket tests for re-measured interventions). |
| W8 | **Compute budget.** §7's statistical pass is the bulk of compute (pillar 12→20 seeds, historical 5→15 seeds, cutoff sensitivity sweep over 7-intervention library at three cutoff configurations). Estimated 8-15 hours. Vlad approved this budget per the brief; the actual compute is reported at §7-start before execution. |

---

## §1 — Docs, tags, math fixes (D1–D6)

*No engine logic. Low-risk doc + math-display + provenance fixes. Lands
first so the §3.2 normalization correction is on record before §2's
affect rewrite reads its corrected baseline; and the provenance audit
informs how new mechanisms in §2-§6 are labelled when introduced.*

### §1.1 Scope and decisions pinned

| # | Decision | Choice |
|---|----------|--------|
| D1 | **Provenance L/N/E audit.** Re-audit the L/N/E tags across all spec / methods / ADR documents. Specific reclassifications: (a) cooperative-mute L→E in `methods.md §3.3` and `phase7_spec.md §5` (R1: edge-level mute is an *extrapolation* of Pettigrew & Tropp's per-encounter `r ≈ −0.21`, not a literature value); (b) ADR-001 substrate L tag: keep L but add empirical political-network citations (Mutz 2006; Huckfeldt & Sprague 1995) alongside DeGroot/FJ — R2's point that DeGroot/FJ supply mathematical form, not political-network empirical substance; (c) Wong et al. tie-formation citation in `s4_network_research.md` flagged E (R2 reading); (d) graded logistic filter explicitly flagged as departing from canonical HK at T > 0 (in `phase4_spec.md F2` and `methods.md §3`); (e) X4 anchor re-stated as Mutz 2006 / Allport / Pettigrew & Tropp until §4 implements the Levendusky 2021 shared-identity-prime variant (then anchor flips to Levendusky 2021 *Our Common Bonds* — see §4); (f) Iyengar / Finkel thermometer attribution tightened in `methods.md §3.1` to "Iyengar et al. 2019 (review of the 1978-2020 ANES trend) + Finkel et al. 2020 (Science synthesis)" — R1's "loose attribution" catch. |
| D2 | **Phase 6 R5 sign-convention contradiction (§1 R5 vs §9 §11 thresholds).** Replace `phase6_spec.md` R5 + §9 sign-convention text with the canonical form: "Helpful direction for `issue_sorting` is **negative** Δsep (camps closer). Helpful direction for `affect` is **positive** Δaff (warmth recovers — note the sign flip)." Both §1 R5 and §9 currently use `effect ≥ 0.15` / `Δsep ≥ -0.15` for "real," which is the wrong inequality for the helpful direction; the implementation in `_classify_sep` uses `dsep <= -0.15`, which is correct. Doc-fix only: bring the spec text in line with the implementation. R2's specific catch. |
| D3 | **Phase 5 §3.2 normalization in `affective_update.py` valence formula.** R2's catch: `issue_term = d_iss / self.radius` uses `self.radius = 1.5`, but max `d_iss` in `[-1, 1]^2` is `2*sqrt(2) ≈ 2.83`, so `issue_term` can reach `~1.89`, not `1.0`. The `disagreement` is therefore in roughly `[0, 1.45]` (because `identity_term` is genuinely in `[0, 1]`, weighted), not `[0, 1]`. **Two changes:** (a) update `phase5_spec.md §3.2` and the `affective_update.py` docstring to state the true range; (b) optionally rescale the formula so `issue_term` is genuinely in `[0, 1]` — e.g. divide by `2*sqrt(2)` or `sqrt(8)` (the geometric max in the 2D unit square). **Decision pinned:** (a) is doc-only and lands in §1. (b) is a behavioural change that would shift the pillar's affect trajectory and re-bless every pillar threshold; (b) is **deferred to backlog** unless the §11 re-measurement in §7 surfaces a problem traceable to the over-range. Rationale: the existing pillar is calibrated against the actual `issue_term` distribution, not the theoretical [0, 1]; rescaling would force a re-calibration just to clean up a math-display issue. R1 + R2 both flagged this; the doc-only fix preserves correctness and surfaces the issue for the reader. |
| D4 | **methods.md §3.1 ANES projection explicit note.** Replace the current "model_check" paragraph in `methods.md §3.1` with explicit text: "The Phase 7 test (`tests/test_phase7.py::test_pillar_affect_trajectory_matches_anes_within_band`) guards the trajectory **shape** at the 200-tick / ~67-year horizon (the band ±20% around `-0.56 * (200/126) ≈ -0.89`). It does **not** assert that the 126-tick (42-year ANES window) projection equals `-0.56` — the pillar's S2/S3 trajectory is non-linear, so the 126-tick value is not a simple linear scaling. The 'within ~5%' projection is an arithmetic projection from the full-window measurement, not a separate measurement." R2's catch about implicit linearity. |
| D5 | **FJ realization clarity in `methods.md §3`.** Add a short paragraph clarifying the FJ realization: "polarlab implements the Friedkin-Johnsen anchoring via a per-rule `(1 − stubbornness)` scaling on each ideology-moving rule's delta, plus an additional `FJ_ALPHA * stubbornness` damping pull toward `anchor` in `GaussianNoise`. This sums multiple per-rule pulls before damping, which is a slight departure from canonical FJ (where the anchor pull and the social pull are combined in a single update). The departure is small at the pillar's stubbornness distribution (Beta(2, 5), mean ≈ 0.29) but is noted here for transparency — anchored agents move less per rule, not less in absolute terms across rules." R2's "almost canonical but not quite" catch. |
| D6 | **Affect-gate firing-rate diagnostic.** Add a §11-time diagnostic to `scripts/phase6_calibration.py` (and the equivalent for §7) that reports, at S4-end + release: (a) the fraction of out-party encounters at which the BacklashRepulsion affect-gate threshold (-0.3) fires, (b) the median post-S4 warmth toward each out-party (per-agent), (c) the count of agents whose median out-party warmth is below -0.3. R2's concern: in the shipped calibration, the gate may effectively always be open (warmth post-S4 is uniformly below -0.3), making it a constant rather than a conditional. The diagnostic reports the firing-rate so the reader can see whether the gate is doing work. The diagnostic is read-only — it does NOT change any thresholds or magnitudes. |

### §1.2 Files

```
modify  methods.md                           # D1, D4, D5 — tag re-audit + projection note + FJ note
modify  phase4_spec.md                       # D1 (graded logistic flag)
modify  phase5_spec.md                       # D3 (normalization range note)
modify  phase6_spec.md                       # D2 (sign-convention fix)
modify  phase7_spec.md                       # D1 (cooperative-mute reclassification)
modify  adr_001_network_primary_engine.md    # D1 (Mutz/Huckfeldt-Sprague citations)
modify  s4_network_research.md               # D1 (Wong et al. reclassification)
modify  abm/rules/affective_update.py        # D3 (docstring only — no behavioural change)
modify  scripts/phase6_calibration.py        # D6 — add affect-gate firing-rate diagnostic
create  scripts/phase8c_diagnostics.py       # D6 — standalone harness for affect-gate firing
```

No tests change in §1 (no behavioural changes).

### §1.3 Judgment forks

**§1 — Fork A: Phase 5 §3.2 normalization (D3 part b).** Rescale the
formula so `issue_term` is genuinely in `[0, 1]`, or leave it as-is
(doc-only correction)? **Default: leave as-is.** Rationale: pillar
calibration is against the actual `issue_term` distribution; rescaling
forces re-calibration for a cosmetic fix. The §7 re-measurement under
larger ensembles will surface whether the over-range causes any
*empirical* problem; if not, the doc-only fix is sufficient.
**Open** to reversing to "rescale" if Vlad wants the formula bounded.

### §1.4 Tests

No new tests; no test changes. The existing suite must remain green
(73-test pillar invariant + 13 mechanism tests = 86 tests total).

### §1.5 Measure-then-bless gate

Not applicable — §1 has no behavioural changes. The §1 gate is:
documentation diff reviewed by an independent reviewer subagent for
factual accuracy (especially the cooperative-mute reclassification
text and the FJ note). On reviewer pass, §1 is closed.

---

## §2 — AffectiveUpdate rewrite: positive-going channel + agent-level cooperative mute + X6 re-measure (E2, E3, I2)

*The keystone section. Every later engine extension in §3-§6 wires into
the rewritten `AffectiveUpdate`, so this section must land first.
Substantial mechanism rewrite + pillar re-measurement + X6 re-bless.*

### §2.1 Scope and decisions pinned

| # | Decision | Choice |
|---|----------|--------|
| E2.1 | **Positive-going valence channel.** `AffectiveUpdate.apply` is rewritten so valence is **no longer structurally monotonic-negative**. Two new sources of positive valence: (a) **exogenous warmth shocks** — Schedule events fire one-shot positive bumps to agents' affect dicts (Obama 2008 thermometer rise, post-9/11 unity bump if added in §5, etc.); (b) **cooperative-encounter positive valence** — when an out-party encounter is over a `cooperative=True` edge AND the agent's current warmth is above a "cooperative-positive threshold" (call it `coop_positive_threshold = -0.2`), the encounter produces a *small positive* valence (warming toward 0), not just attenuated negative. Below the threshold, the cooperative edge still mutes negative valence (existing edge-level behaviour preserved for cold-affect agents). Rationale per Fork 5 default: empirical reversals in the ANES record (Obama 2008, post-9/11) are tied to discrete events, not continuous mechanisms; the cooperative-positive path is Pettigrew 2009 secondary-transfer for the cold-but-not-extreme zone. **Pinned constants:** `coop_positive_threshold = -0.2`; cooperative-positive valence magnitude = `+0.5 * baseline = +0.05` per encounter (half the floor coolness, sign-flipped). |
| E3.1 | **Replace edge-level cooperative mute with agent-level cooperative mute (Fork 1 → a).** Per Pettigrew 2009 secondary-transfer, contact reduces *agent-level* prejudice formation across all out-party encounters, not just at the contact target. Mechanism: each agent carries `agent.state.attrs["cooperative_share"] = 0.0` (default; pillar-fallback for non-pillar scenarios). At apply-time, AffectiveUpdate reads `cooperative_share` and **multiplies the negative-going valence by `(1 - cooperative_share * (1 - COOPERATIVE_MUTE))`** for ALL out-party encounters (not just cooperative-edge ones). The edge-level mute is removed — `network.is_cooperative()` no longer affects the rule (the property stays on the network for §2 backwards-compat but is unused by AffectiveUpdate; can be removed in 8d cleanup). |
| E3.2 | **`cooperative_share` source.** When X6 fires (or any future X that adds cooperative ties), each participating agent's `cooperative_share` is incremented based on the count of new cooperative ties they receive: `cooperative_share += k_new_coop / k_total_ties`, clipped to `[0, 1]`. So an agent who receives 2 new cooperative ties out of 10 total ties has `cooperative_share = 0.2`, meaning their negative-going valence on every out-party encounter is muted by `0.2 * (1 - 0.5) = 0.10` (10% reduction). An agent with no cooperative ties has `cooperative_share = 0.0` (no muting). |
| I2.1 | **X6 re-measurement under agent-level cooperative mute.** With agent-level mute replacing edge-level, X6 redistributes the mute across ALL out-party encounters of participating agents (not just the new cooperative-edge encounters). Predicted direction: X6's affect-backfire from `Δaff = -0.23` shrinks toward `Δaff ≈ -0.10 to -0.15` (still negative, because the new edges multiply encounter volume; but agent-level mute is broader than edge-level). The §11 measure-then-bless decides the new bucket. **Spec does NOT pre-bless the new X6 affect bucket** — that's the §2.5 gate. |
| E2.2 | **In-party warmth deferred to 8d.** Per Fork 5: the `affect` dict currently keys on out-party only. Adding an in-party warmth channel would restructure the dict (keys would become both 0 and 1 for every agent), break read-paths in BC/TieRewiring/BacklashRepulsion, and is out of 8c scope. Documented in BACKLOG.md. |
| E2.3 | **Schedule-fired warmth shocks: which events?** §2's deliverable is the MECHANISM (Schedule events can fire warmth bumps via a setter on `AffectiveUpdate` or by directly writing to agents' affect dicts). §5 (identity-threat) and §4 (perception-gap) consume the mechanism. For §2 alone, add ONE test event to the historical-arc Schedule: `_event_2008_obama_warmth` at tick 84 (overlaps with the existing social-media-ramp-start event — combine via `_combined(...)`). The event fires a one-shot `+0.05` bump to every agent's out-party affect (small; documented as illustrative of the Obama-2008 ANES thermometer rise). This is the test case for the warmth-shock mechanism. |
| E2.4 | **AffectiveUpdate.apply signature unchanged.** The rule's `apply(self, agent, space, env, rng)` signature stays; the rewrite is internal. Constructor gets two new kwargs: `coop_positive_threshold: float = -0.2` and `coop_positive_magnitude: float = 0.05`. Both default values are calibration-anchored; documented in the `AffectiveUpdate` docstring. The historical-arc and pillar builders pass them at the new defaults explicitly. |

### §2.2 Files

```
modify  abm/rules/affective_update.py        # E2, E3 — rewrite valence + agent-level mute
modify  abm/pillars/calm_to_camps.py         # COOPERATIVE_MUTE constant doc updated; pillar builder passes coop_positive_threshold = -0.2 (or omits, default OK)
modify  abm/pillars/historical_arc.py        # Schedule: add _event_2008_obama_warmth at tick 84 (combine with existing ramp-start event)
modify  abm/pillars/interventions_phase6.py  # X6 setup: replace edge-level cooperative=True with agent-level cooperative_share bump
modify  tests/test_phase5.py                 # extend Iyengar/affect test to cover positive-going under cooperative_share > 0
modify  tests/test_phase6.py                 # X6 setup test updated to assert cooperative_share increments (not just network.is_cooperative)
modify  tests/test_phase7.py                 # cooperative mute test updated to test agent-level path
modify  tests/test_phase8b_mechanisms.py     # historical_arc Schedule test: assert _event_2008_obama_warmth fires positive bump at tick 84
create  tests/test_phase8c_affect.py         # new unit tests for positive-going valence + agent-level mute fallback
modify  methods.md                           # §3.3 updated to describe agent-level mute (replaces edge-level note)
```

### §2.3 Mechanism math (the rewrite)

```python
def apply(self, agent, space, env, rng) -> StateDelta:
    if self.lr == 0:
        return StateDelta()
    agent_party = agent.state.attrs.get("party")
    if agent_party is None:
        return StateDelta()
    neighbors = neighbor_agents(agent, space, env)
    if not neighbors:
        return StateDelta()

    lr = float(agent.state.attrs.get("affect_lr", self.lr))
    if lr == 0:
        return StateDelta()

    # Agent-level cooperative-mute factor (E3). Falls back to 0.0 for
    # non-pillar scenarios — pillar-fallback discipline.
    coop_share = float(agent.state.attrs.get("cooperative_share", 0.0))
    coop_share = float(np.clip(coop_share, 0.0, 1.0))
    # The mute factor: a fully-cooperative agent (coop_share=1.0) has
    # their negative valence multiplied by COOPERATIVE_MUTE (=0.5);
    # a non-cooperative agent (coop_share=0.0) has it multiplied by 1.0.
    neg_mute = 1.0 - coop_share * (1.0 - self.cooperative_mute)

    # ... identity/issue distance calculation (unchanged) ...

    affect_delta = {}
    for neighbor in neighbors:
        other_party = neighbor.state.attrs.get("party")
        if other_party is None or other_party == agent_party:
            continue
        # ... distance calculation (unchanged) ...

        own_warmth = float(np.clip(
            agent.state.attrs.get("affect", {}).get(other_party, 0.0),
            -1.0, 1.0,
        ))

        # Positive-going path: cooperative edge AND warmth above the
        # cooperative-positive threshold. Note: edge-level coop check
        # is preserved as a *trigger* for the positive path, NOT for
        # negative muting (the agent-level mute handles the negative
        # path). A cooperative-tagged edge is what makes the warming
        # encounter possible at all.
        is_coop_edge = (
            (network := env.attrs.get("network")) is not None
            and network.is_cooperative(agent.id, neighbor.id)
        )
        if is_coop_edge and own_warmth >= self.coop_positive_threshold:
            valence = +self.coop_positive_magnitude
        else:
            # Negative-going path (sign fix from Phase 5; default).
            disagreement = (
                self.identity_weight * identity_term
                + (1.0 - self.identity_weight) * issue_term
            )
            valence = -(disagreement + self.baseline)
            # Agent-level cooperative mute (E3) — replaces edge-level
            # mute. Applies to every out-party encounter, scaled by
            # the agent's cooperative_share.
            valence *= neg_mute

        affect_delta[other_party] = (
            affect_delta.get(other_party, 0.0) + lr * valence
        )

    if not affect_delta:
        return StateDelta()
    return StateDelta(d_attrs={"affect": affect_delta})
```

### §2.4 Judgment forks

**§2 — Fork A: warmth-shock magnitude calibration.** The Obama-2008
test event fires `+0.05` per agent. Is that the right magnitude? The
ANES 2008 thermometer rise toward Obama was real but modest (~3-5
points on the [0, 100] scale = ~0.06-0.10 normalised). **Default
+0.05.** Sensitivity sweep at +0.03, +0.05, +0.10 deferred to §7's
robustness pass.

**§2 — Fork B: agent-level mute formula.** The formula
`neg_mute = 1.0 - coop_share * (1.0 - COOPERATIVE_MUTE)` is one
reading; alternatives include `neg_mute = COOPERATIVE_MUTE ** coop_share`
(exponential decay) or `neg_mute = COOPERATIVE_MUTE if coop_share > 0
else 1.0` (binary). **Default: linear interpolation** (the formula
above). Anchored by: when `coop_share = 1.0`, the mute equals
`COOPERATIVE_MUTE = 0.5` (Pettigrew & Tropp's anchor); when
`coop_share = 0.0`, the mute is `1.0` (no muting). Linear between is
the parsimonious choice; alternatives are not literature-anchored
more strongly than this.

**§2 — Fork C: cooperative-positive valence: include identity_distance?**
The positive path uses a constant `coop_positive_magnitude = 0.05`
regardless of identity distance. Should it scale with proximity? The
literature (Mason 2018; Levendusky 2021) doesn't anchor either way.
**Default: constant magnitude.** Scaling with proximity adds a
parameter without literature support. Documented in `methods.md §3.3`.

### §2.5 Tests

**Unit tests** (`tests/test_phase8c_affect.py`):

1. `test_positive_valence_on_coop_edge_above_threshold` — agent with
   warmth = -0.1 (above coop_positive_threshold=-0.2), cooperative
   edge to out-party neighbour: valence is positive (+0.05 default).
2. `test_negative_valence_on_coop_edge_below_threshold` — agent with
   warmth = -0.5 (below threshold), cooperative edge: valence is
   negative, muted by agent's coop_share.
3. `test_agent_level_mute_on_non_coop_edge` — agent with
   coop_share = 0.5, non-cooperative edge to out-party: valence is
   negative, muted by `1 - 0.5 * (1 - 0.5) = 0.75`.
4. `test_agent_level_mute_pillar_fallback` — agent without
   coop_share attr defaults to coop_share=0.0, no muting (identical
   to Phase 5 baseline behaviour).
5. `test_warmth_shock_event_fires_positive_bump` —
   `_event_2008_obama_warmth` event applied to engine: every agent's
   out-party affect is bumped by +0.05.

**Pillar regression tests** (extend `tests/test_phase5.py`):

6. `test_pillar_affect_trajectory_unchanged_at_zero_coop_share` —
   pillar S0→S3 affect trajectory bit-identical (within 1e-9) to
   Phase 8b when all agents have `coop_share = 0.0`. (This is the
   pillar-fallback discipline check.)

**Mechanism test** (extend `tests/test_phase8b_mechanisms.py`):

7. `test_obama_warmth_event_at_tick_84` — historical-arc Schedule
   fires the warmth event at tick 84; out-party affect rises by ~0.05
   between tick 83 and tick 85.

### §2.6 Measure-then-bless gate

After Slice §2 is implemented and unit tests pass:

1. **Pillar S0-S4 invariant**: run the full 73-test pillar suite + 13
   Phase 8b mechanism tests + new §2 tests. All must pass at current
   thresholds. If any pillar threshold shifts (positive or negative),
   the implementer hard-stops, reports the shift, and proposes either
   (a) re-blessing the threshold to the new value, or (b) reverting
   the change. The default is (a) if the shift is within ±5% and (b)
   if larger.
2. **X6 §11 re-measurement**: re-run `intervention_buckets` for X6
   only. Report measured `Δsep` and `Δaff`. Apply the §11 bucket
   classifier (`_classify_sep`, `_classify_aff`). Bless the new
   `effect_buckets` entry for X6. The bucket may stay "backfire" on
   affect (if accumulation across all out-party encounters still
   exceeds the agent-level mute), shift to "partial" (mute is large
   enough), or shift to "null" (cooperative-positive valence + mute
   together neutralise). **Bless whichever bucket is measured.**
3. **Historical-arc qualitative check**: run the historical_arc
   scenario (1 seed for speed) and visualise the affect trajectory
   from 1980→2025. The 2008 Obama bump should be visible as a small
   positive perturbation in the otherwise monotonically-decreasing
   trajectory; the affect at 2025 should still be in the documented
   target band (the warmth bump is small).

---

## §3 — Per-outlet, per-agent media exposure + X3 re-implementation (E1, I1)

*Refactor `MediaConsumption` from "diet-target weighted-mean pull"
(centripetal AND centrifugal collapsed into one target) to "per-outlet
pull" (each outlet exerts its own force on each agent). R1's
"category error" fix for X3.*

### §3.1 Scope and decisions pinned

| # | Decision | Choice |
|---|----------|--------|
| E1.1 | **Per-outlet pull mechanism.** `MediaConsumption.apply` is rewritten so each outlet in the agent's `media_diet` exerts its own per-tick pull: `d_ideology = strength * sum(weight_i * (outlet_i.position - agent.ideology) for i in diet)`. This is mathematically equivalent to the current diet-target pull *when computed unnormalised over all outlets simultaneously* — the change is that each outlet's contribution is computed and visible separately, enabling per-outlet interventions like X3. **Engine-level behaviour unchanged for the pillar** (the sum equals the current `strength * (diet_target - ideology)` when `diet` weights are normalised). |
| E1.2 | **Per-outlet media-exposure attribute.** `agent.state.attrs["media_diet"]` already keys on `{outlet_id: weight}`. **No new agent attribute needed for E1.** The "category error" fix is in how interventions modify `media_diet` (X3 can now zero specific outlet weights instead of disabling the whole rule), not in the data structure. |
| E1.3 | **Pillar-fallback preserved.** Non-pillar scenarios (`compass_basic`, `actb`) don't seed `media_diet`; `MediaConsumption.apply` returns empty StateDelta if `media_diet` or `outlets` missing — unchanged. Pillar scenarios continue to seed `media_diet` via `diet_for_party()`. Bit-identical to Phase 8b for the pillar. |
| I1.1 | **X3 re-implementation: "Quit cable news" zeros partisan-cable outlet weights.** X3 currently zeros `MediaConsumption.strength` (kills all media pull). The re-implementation: X3 zeros each agent's exposure to partisan-cable outlets (Fox News id=4, MSNBC id=0 in `US_MEDIA_OUTLETS_2024`), leaving centrist/broadcast outlets (Local TV id=2, WSJ id=3, NYT id=1) at their existing weights. Effect: the *centripetal* pull of broadcast/local survives; the *centrifugal* pull of partisan cable is removed. Per R1's diagnosis: the X3 backfire in Phase 7 was driven by removing the (small but centripetal) inner-mean pull of broadcast outlets, not by anything specific to partisan cable. Under the new X3, broadcast still pulls inward, partisan cable doesn't pull outward — so the predicted direction is "small partial reduction in issue sorting," not "backfire." |
| I1.2 | **X3 setup function.** New `_x3_setup(engine)`: for each agent, iterate `agent.state.attrs["media_diet"]`, zero weights for outlet ids in `PARTISAN_CABLE_OUTLET_IDS = {0, 4}` (MSNBC, Fox News). Re-normalise remaining weights (or leave un-normalised — the per-outlet rule handles either). `param_bundle` removes the `("MediaConsumption", "strength", 0.0)` override (strength stays at S4 default). |
| I1.3 | **The §11-blessed X3 bucket is re-measured, not pre-declared.** Spec does NOT pre-bless. The direction predicted (partial helpful, not backfire) is documented in the spec for transparency, but the actual `effect_buckets` entry comes from the §11 measurement. |
| E1.4 | **Outlet-by-outlet diagnostic in §11.** §11 measurement script reports, in addition to overall Δsep, the contribution of each outlet's pull to the agent population at S4-end vs. release-end (sum of `weight_i * (outlet_i.position - agent.ideology)` across agents). This is read-only; surfaces whether the centripetal/centrifugal forces are really separating, or whether the new X3 lands in the same bucket as the old X3 because of some other dynamic. |

### §3.2 Files

```
modify  abm/rules/media_consumption.py       # rewrite apply for per-outlet pull
modify  abm/pillars/interventions_phase6.py  # X3 setup function + param_bundle change
modify  tests/test_phase6.py                 # update X3 test (no longer tests strength=0 zeroing)
create  tests/test_phase8c_media.py          # new unit tests for per-outlet pull behaviour
modify  scripts/phase6_calibration.py        # outlet-by-outlet contribution diagnostic
modify  methods.md                           # §5.1 limitation updated; new per-outlet description
```

### §3.3 Mechanism math (the rewrite)

```python
def apply(self, agent, space, env, rng) -> StateDelta:
    if self.strength == 0:
        return StateDelta()
    diet = agent.state.attrs.get("media_diet")
    outlets = env.attrs.get("outlets")
    if not diet or not outlets:
        return StateDelta()
    # Per-outlet pull — each outlet contributes independently.
    # Mathematically equivalent to the current diet-target pull when
    # weights are normalised, but separates each outlet's contribution
    # for per-outlet interventions (X3).
    pull = np.zeros(2)
    total_weight = sum(diet.values())
    if total_weight < 1e-9:
        return StateDelta()
    for outlet_id, weight in diet.items():
        outlet = outlets.get(outlet_id)
        if outlet is None:
            continue
        pull += (weight / total_weight) * (outlet.position - agent.state.ideology)
    d = self.strength * pull
    # F1: Friedkin-Johnsen scaling.
    s = float(agent.state.attrs.get("stubbornness", 0.0))
    return StateDelta(d_ideology=(1.0 - s) * d)
```

### §3.4 Judgment forks

**§3 — Fork A: which outlets count as "partisan cable"?** The roster
labels MSNBC + Fox News as partisan cable (positions [-0.55, -0.35]
and [0.65, 0.45]). NYT and WSJ are also partisan-leaning by some
classifications. **Default: only MSNBC + Fox News.** Anchored by:
"cable news" is a specific empirical category in the literature
(Levendusky 2013; Allcott et al. 2020), distinct from "partisan
newspapers." NYT/WSJ stay in the diet. Open to including
NYT/WSJ if Vlad wants the broader "partisan media" definition.

**§3 — Fork B: re-normalise weights after zeroing?** When X3 zeros
MSNBC + Fox News, the remaining outlet weights sum to less than 1.
**Default: do NOT re-normalise.** The agent's total media intake
goes down (they "consume less media"), matching the lay framing of
"quit cable news." Re-normalising would mean the agent's broadcast
exposure goes UP to compensate, which is the wrong lay reading.

### §3.5 Tests

**Unit tests** (`tests/test_phase8c_media.py`):

1. `test_per_outlet_pull_equals_diet_target_for_normalized_diet` —
   with normalised diet weights, the new per-outlet pull
   mathematically equals the old `diet_target` pull. Regression
   guard.
2. `test_per_outlet_pull_separates_outlet_contributions` — agent with
   `media_diet = {0: 0.5, 4: 0.5}` (MSNBC + Fox News only); pull is
   the mean of the two outlet positions (small, near origin). After
   zeroing outlet 4 (Fox), pull is toward MSNBC only.
3. `test_x3_zeros_only_cable_outlets` — `_x3_setup` is applied to a
   test engine; agents' `media_diet` weights for outlet ids {0, 4}
   are zero; weights for {1, 2, 3} are unchanged.
4. `test_x3_pillar_fallback_compass_basic_unchanged` — compass_basic
   without `media_diet` is bit-identical to Phase 8b (the rule
   returns empty StateDelta for non-pillar scenarios).

### §3.6 Measure-then-bless gate

1. **Pillar S0-S4 invariant**: same as §2 (full suite passes).
2. **X3 §11 re-measurement**: re-run `intervention_buckets` for X3
   only. Report measured Δsep and Δaff. Apply the §11 bucket
   classifier. Bless the new bucket.
3. **Outlet-contribution diagnostic**: the §11 script's
   outlet-by-outlet contribution at S4-end + release-end is reported.
   The diagnostic confirms that broadcast/local outlets contribute
   inward pull, partisan cable contributes outward pull, when both
   are active.
4. **methods.md §5.1 update**: the X3-outlet-sensitivity limitation
   is updated to reflect the new mechanism. (X3 is no longer
   sensitive to the *aggregate* roster shifting outward — it's
   sensitive to which outlets the roster classifies as partisan
   cable. The new sensitivity is more directly stated.)

---

## §4 — Perception-gap construct + X7 + X4 shared-identity prime re-implementation (E4, I5, I4)

*Three pieces in one section: a new agent attribute
(`perceived_other_party`); a new intervention (X7, "Correct the
perception gap"); a re-implementation of X4 as the Levendusky 2021
shared-identity prime (the override Vlad confirmed). The shared theme
is psychological mechanisms modulating how agents process out-party
encounters.*

### §4.1 Scope and decisions pinned

| # | Decision | Choice |
|---|----------|--------|
| E4.1 | **`perceived_other_party` attribute.** Each agent carries `agent.state.attrs["perceived_other_party"]: dict[int, np.ndarray]` — the agent's belief about each out-party's centroid. **Initial seeding (pillar + historical_arc):** at build time, perceived position is the actual centroid + Gaussian noise with a *biased-extreme* mean. Formula: `perceived_other_party[p] = parties[p] + extreme_bias * sign(parties[p][0]) * np.array([1.0, 0.0]) + N(0, 0.15)`. The `extreme_bias = 0.25` represents the perception-gap finding (Levendusky & Malhotra 2016; Ahler & Sood 2018; Druckman et al. 2022): agents misperceive the out-party as ~25% more extreme on the dominant axis than reality. |
| E4.2 | **Pillar-fallback for the attribute.** Non-pillar scenarios (`compass_basic`, `actb`) don't seed `perceived_other_party`. The rule that reads it (the updated `AffectiveUpdate` from §2 — see §4.3) falls back to the actual env-level centroid. Bit-identical to Phase 8b for non-pillar scenarios. |
| E4.3 | **Perception-gap drives valence in `AffectiveUpdate`.** §2's rewritten `apply` is extended to read perceived rather than actual out-party position when computing `issue_term`: `d_iss = ||agent.state.ideology - perceived_other_party[other_party]||` (for an *agent who has the perception* — pillar-fallback to actual centroid for non-pillar). The hooked formula amplifies the negative valence for misperceiving agents: an agent who thinks the other party is at [+0.75, 0] (with extreme_bias) has a larger `d_iss` than reality (other party actually at [+0.50, 0]), producing more coolness per encounter. |
| E4.4 | **Perception-gap dynamic update (slow correction).** New rule `PerceptionUpdate` (or method on `AffectiveUpdate`; spec choice — see Fork below) updates `perceived_other_party` each tick by averaging toward the agent's actual neighbour-positions: `perceived_other_party[other] += correction_rate * (mean_observed_other_position - perceived_other_party[other])`. `correction_rate = 0.01` (default; slow). For agents with no out-party neighbours observed, no update. |
| E4.5 | **Implementation choice: standalone rule or AffectiveUpdate extension?** **Decision pinned: standalone `PerceptionUpdate` rule.** Rationale: keeps `AffectiveUpdate` focused on the affect update; perception-update is conceptually separate (cognition vs. emotion). Adds a new file `abm/rules/perception_update.py`. The pillar builder includes it at strength=0 by default (S0-S2 inert); strength=0.01 at S3+ as part of the homophilous/partisan-media stages where misperception becomes empirically relevant. **Pillar bundle change**: this is a new mechanism that the pillar's S0-S4 bundles need to acknowledge (S0-S2: strength=0; S3-S4: strength=0.01). Affects §11 measurement — the pillar's S3/S4 affect trajectory may shift because misperception now amplifies coolness. **Re-bless required.** |
| I5.1 | **X7 — "Correct the perception gap."** New intervention: one-shot reset of every agent's `perceived_other_party` to the actual env-level centroid (zeroing the misperception). After the reset, the perception-update dynamic continues, so misperception can re-accumulate if other dynamics push perceived positions outward (TieRewiring → homophilous neighbour observations → if neighbour positions remain extreme, perception drifts back). X7 is a one-shot setup, not a continuous force. Citation: Levendusky & Malhotra 2016; Ahler & Sood 2018; Druckman et al. 2022. |
| I4.1 | **X4 re-implementation as Levendusky 2021 shared-identity prime (Fork 2 → b override).** X4's mechanism is replaced with a temporary downweighting of `AffectiveUpdate`'s `identity_distance` contribution to valence, representing backgrounding of partisan categorization under superordinate national-identity salience. **Mechanism:** new `AffectiveUpdate` attribute `identity_weight_overrides: dict[int, float]` keyed by agent id — agents in the override dict have `identity_weight` reduced (e.g. from 0.5 to 0.1) for `prime_duration_ticks = 30` (10 years, the standard release-phase window). After expiration, identity_weight reverts. **Population scope:** **20% sampled subset** (Vlad's §4-B override from the 40% default). Vlad's framing: this models a more targeted civic program rather than a broad national rollout. **`prime_duration_ticks = 30`** matches the 10-year release-window discipline (also confirmed unchanged). |
| I4.2 | **X4 setup function `_x4_shared_identity_prime`.** Samples `int(0.2 * n_agents)` agents using `np.random.default_rng(X4_DIALOGUE_RNG_SEED)` (existing seed preserved for reproducibility). Adds them to `engine.env.attrs["identity_prime_active_until"] = {agent_id: tick + 30 for agent_id in sampled}`. **A new env-rule `IdentityPrimeExpiry` (or `AffectiveUpdate`-side read) reads this dict at apply-time** and uses the reduced `identity_weight` for active agents. After tick > expiry, the agent reverts to global `identity_weight`. **The old `_x4_setup`** (cross-party voluntary ties + affect reset) is removed. X4 no longer adds network ties. |
| I4.3 | **X4 measure-then-bless.** Spec does NOT pre-bless. The expected direction is "small partial helpful on affect" (Levendusky 2021 finds modest effects); the §11 re-measurement decides. |

### §4.2 Files

```
modify  abm/rules/affective_update.py        # read perceived_other_party with fallback; read identity_weight overrides
create  abm/rules/perception_update.py       # E4.4 — slow correction dynamic
modify  abm/pillars/calm_to_camps.py         # build_engine seeds perceived_other_party; bundles for S0-S2 strength=0, S3-S4 strength=0.01
modify  abm/pillars/historical_arc.py        # same: seed perceived_other_party in builder; activate PerceptionUpdate at S3-equivalent point in the schedule (around 1990 / tick 30)
modify  abm/pillars/interventions_phase6.py  # X4 setup replaced; X7 added
modify  abm/pillars/__init__.py              # export X7
modify  tests/test_phase8b_mechanisms.py     # new PerceptionUpdate tests
modify  tests/test_phase6.py                 # X4 setup test updated for prime mechanism; X7 added
create  tests/test_phase8c_perception.py     # new unit tests for perception attribute + update dynamic
modify  methods.md                           # §3 add perception-gap anchor; §4.3 add X7; §5 add limitations
```

### §4.3 Mechanism math (the rule)

```python
class PerceptionUpdate:
    """Slow correction of agents' perceived out-party positions toward
    their observed neighbour-positions.

    Misperception is seeded at build time (extreme_bias=0.25 by
    default). Each tick, the agent observes its out-party neighbours
    and shifts perceived_other_party[their_party] toward the mean
    observed position by `correction_rate * (mean - perceived)`.

    Reads:
      agent.state.attrs["party"]
      agent.state.attrs["perceived_other_party"]: dict[int, np.ndarray]
      neighbour.state.attrs["party"]
      neighbour.state.ideology

    Writes (delta):
      d_attrs["perceived_other_party"] = {other_party: delta_ndarray}
    """

    def __init__(self, correction_rate: float = 0.01):
        self.correction_rate = correction_rate

    def apply(self, agent, space, env, rng) -> StateDelta:
        if self.correction_rate == 0:
            return StateDelta()
        agent_party = agent.state.attrs.get("party")
        if agent_party is None:
            return StateDelta()
        perceived = agent.state.attrs.get("perceived_other_party")
        if perceived is None:
            return StateDelta()
        neighbors = neighbor_agents(agent, space, env)
        if not neighbors:
            return StateDelta()
        # Group out-party neighbours by their actual party.
        by_party = {}
        for n in neighbors:
            np_ = n.state.attrs.get("party")
            if np_ is None or np_ == agent_party:
                continue
            by_party.setdefault(np_, []).append(n.state.ideology)
        if not by_party:
            return StateDelta()
        deltas = {}
        for other_party, positions in by_party.items():
            current = perceived.get(other_party)
            if current is None:
                continue
            mean_obs = np.mean(positions, axis=0)
            delta = self.correction_rate * (mean_obs - current)
            deltas[other_party] = delta
        if not deltas:
            return StateDelta()
        return StateDelta(d_attrs={"perceived_other_party": deltas})
```

`AffectiveUpdate.apply` reads `perceived_other_party[other_party]` if
present, otherwise falls back to `env.attrs["parties"][other_party]`
(actual centroid):

```python
# Inside AffectiveUpdate.apply (modified from §2):
perceived = agent.state.attrs.get("perceived_other_party") or {}
target_position = perceived.get(other_party)
if target_position is None:
    target_position = env.attrs.get("parties", {}).get(other_party)
if target_position is None:
    # No perception, no centroid — fall back to neighbour's actual
    # ideology (compass_basic / actb path; bit-identical to Phase 8b).
    target_position = neighbor.state.ideology
d_iss = float(np.linalg.norm(agent.state.ideology - target_position))
```

`identity_weight` override (X4 prime):

```python
# Inside AffectiveUpdate.apply (modified for I4):
identity_prime_active_until = env.attrs.get(
    "identity_prime_active_until", {}
) or {}
prime_expiry = identity_prime_active_until.get(agent.id)
current_tick = env.attrs.get("tick", 0)
if prime_expiry is not None and current_tick < prime_expiry:
    effective_identity_weight = 0.1  # I4 prime: backgrounded partisan id
else:
    effective_identity_weight = self.identity_weight
```

### §4.4 Judgment forks

**§4 — Fork A: standalone PerceptionUpdate rule or merged into
AffectiveUpdate?** Standalone (default — see E4.5) keeps the rules
single-purpose and easier to ablate. Merged is fewer files and
guarantees same-tick consistency between perception and affect
updates. **Default: standalone.** Vlad's brief implied independent
construction (Fork 4 → a, perception-gap and identity-threat
independent), which suggests independent rules too.

**§4 — Fork B: X4 prime population scope.** **Vlad override → 20%
sampled subset** (models a targeted civic program, not a broad
national rollout). Original spec default was 40% (middle of
Levendusky's experimental range); Vlad's confirmed override is 20%.
The 30-tick prime window stays.

**§4 — Fork C: extreme_bias initial value.** Default 0.25 (25%
overestimate of out-party extremity). Anchored by Levendusky &
Malhotra 2016's reported 17-25% range (varies by issue). Open to 0.20
or 0.30 if Vlad has a specific target in mind. Sensitivity sweep
deferred to §7.

### §4.5 Tests

**Unit tests** (`tests/test_phase8c_perception.py`):

1. `test_perception_seeded_at_build_with_extreme_bias` — at pillar
   build time, every agent's `perceived_other_party[other]` is more
   extreme on the dominant axis than the actual centroid by ~0.25.
2. `test_perception_update_corrects_toward_observed_neighbours` —
   agent with biased perception, run 50 ticks of PerceptionUpdate
   only; perceived position should drift toward observed neighbours'
   mean.
3. `test_perception_pillar_fallback` — compass_basic doesn't seed
   `perceived_other_party`; `PerceptionUpdate.apply` returns empty
   StateDelta. AffectiveUpdate falls back to `env.attrs["parties"]`
   centroid. Bit-identical to Phase 8b for compass_basic.
4. `test_x7_perception_reset` — `_x7_setup` zeros every agent's
   `perceived_other_party` to actual centroids. After setup, no agent
   has a biased perception.
5. `test_x4_prime_active_at_setup_expires_after_30_ticks` — X4 setup
   adds 40% of agents to `identity_prime_active_until`; at tick t,
   their effective `identity_weight` is 0.1; at tick t+31, it reverts.
6. `test_x4_prime_pillar_fallback` — pillar S0-S4 (X4 not applied):
   no agent has `identity_prime_active_until` entry; effective
   `identity_weight` equals the rule's `self.identity_weight` for
   every agent.

### §4.6 Measure-then-bless gate

1. **Pillar invariant**: 73-test pillar + 13 mechanism tests + §2 +
   §3 + §4 unit tests pass. The pillar S3/S4 affect trajectory may
   shift because PerceptionUpdate now amplifies coolness via biased
   perception. If the trajectory shifts outside the existing test
   bounds, the implementer re-blesses the bounds (move the tag,
   not the threshold; W6 discipline preserved).
2. **§11 re-measurement**: X4 and X7 measured under the new mechanism.
   X1, X2, X3, X5, X6 (the unchanged interventions in this section)
   are NOT re-measured here — they will be in §7's robustness pass.
3. **Historical-arc qualitative check**: run with the new perception
   mechanism active; the 1990-2010 era should show widening
   misperception (TieRewiring drives observed-neighbours more
   in-party, perception drifts outward); the 2010-2025 era should
   show plateau or continued widening.

---

## §5 — Identity-threat mechanism (E5)

*New mechanism, no new intervention. Identity-threat amplifies
existing AffectiveUpdate + BacklashRepulsion intensity in response to
exogenous threat events (Mutz 2018 status-threat — the empirical
anchor for the 2016 affect spike).*

### §5.1 Scope and decisions pinned

| # | Decision | Choice |
|---|----------|--------|
| E5.1 | **`perceived_threat` attribute.** Each agent carries `agent.state.attrs["perceived_threat"]: float` in `[0, 1]`. Default 0.0 (no threat). Pillar-fallback: non-pillar scenarios don't seed; rules read with `agent.state.attrs.get("perceived_threat", 0.0)`. Pillar S0-S4: threshold seeded at 0.0; no threat events fired in the pillar. Historical arc: threshold seeded at 0.0; threat events fire at scheduled ticks (see §5.3). |
| E5.2 | **Threat amplifies AffectiveUpdate.** When `perceived_threat > 0`, the negative-going valence in AffectiveUpdate is multiplied by `(1 + threat_amplification * perceived_threat)`. `threat_amplification = 1.0` (default; doubles negative valence at full threat). Positive-going valence (cooperative-positive path from §2) is NOT amplified by threat — threat is identity-defensive, not socially open. |
| E5.3 | **Threat amplifies BacklashRepulsion.** When `perceived_threat > 0`, `BacklashRepulsion`'s push magnitude is multiplied by `(1 + threat_amplification * perceived_threat)`. Same amplification factor. |
| E5.4 | **Threat decay.** Threat is event-triggered but not permanent. A new env-rule `ThreatDecay` runs each tick: `perceived_threat *= (1 - threat_decay_rate)` for every agent. `threat_decay_rate = 0.05` (default; half-life ~14 ticks ≈ 4.7 years). This means a 2016 spike decays to ~half-strength by 2020 and to noise by 2025. |
| E5.5 | **Historical schedule: 2016 status-threat event.** New event `_event_2016_status_threat` at tick 108 (combine with existing Trump election event via `_combined(...)`). The event sets `perceived_threat = 0.5` for a sampled subset of agents (specifically: 60% of party=1 (Republican) agents — Mutz 2018's finding that white Republican respondents drove the status-threat response). The 60% / 0.5 magnitude combo is the Mutz 2018 mapping: ~60% of Mutz's threatened-identity group + a "moderate threat" magnitude. Decays naturally via ThreatDecay. |
| E5.6 | **No threat events in pillar.** Pillar's S0-S4 baseline never fires a threat event. The mechanism is inert in the pillar; activates only in historical_arc. |
| E5.7 | **No new intervention in §5.** Identity-threat is a mechanism extension that fuels the 2016 affect spike in the historical arc; it is not a depolarization lever. The X-library does NOT add an "identity-threat reduction" intervention. (Could be a Phase 8d candidate.) |
| E5.8 | **Independent from perception-gap (Fork 4 → a).** `perceived_threat` is a separate scalar from `perceived_other_party`. They do not feed each other. The 2016 event sets `perceived_threat` directly; perception-gap dynamics run independently. |

### §5.2 Files

```
create  abm/rules/threat_dynamics.py         # E5.4 — ThreatDecay env-rule
modify  abm/rules/affective_update.py        # threat amplification on negative valence
modify  abm/rules/repulsion.py               # threat amplification on push magnitude
modify  abm/pillars/calm_to_camps.py         # seed perceived_threat=0.0 (no-op); ThreatDecay at rate=0 in S0-S4
modify  abm/pillars/historical_arc.py        # seed perceived_threat=0.0; ThreatDecay at rate=0.05; 2016 threat event
modify  tests/test_phase8b_mechanisms.py     # 2016 threat event test
create  tests/test_phase8c_threat.py         # new unit tests for threat amplification + decay
modify  methods.md                           # add status-threat anchor and Mutz 2018 citation; update §5 limitations
```

### §5.3 Mechanism math

```python
# Inside AffectiveUpdate.apply (modified from §2 + §4):
threat = float(agent.state.attrs.get("perceived_threat", 0.0))
threat = float(np.clip(threat, 0.0, 1.0))
threat_factor = 1.0 + self.threat_amplification * threat

# ... (compute valence as in §2) ...
if valence < 0:  # negative-going path
    valence *= threat_factor
# Positive-going path unchanged — threat is identity-defensive, not
# socially open.
```

```python
# Inside BacklashRepulsion.apply (modified):
threat = float(agent.state.attrs.get("perceived_threat", 0.0))
threat = float(np.clip(threat, 0.0, 1.0))
threat_factor = 1.0 + self.threat_amplification * threat
# ... (compute push as in Phase 6) ...
d = self.strength * threat_factor * push / count
```

```python
class ThreatDecay:
    """Env-rule: decay every agent's perceived_threat each tick."""

    def __init__(self, decay_rate: float = 0.05):
        self.decay_rate = decay_rate

    def apply(self, env, agents, space, rng):
        if self.decay_rate == 0:
            return
        for agent in agents:
            threat = agent.state.attrs.get("perceived_threat")
            if threat is None:
                continue
            agent.state.attrs["perceived_threat"] = float(
                threat * (1.0 - self.decay_rate)
            )
```

### §5.4 Judgment forks

**§5 — Fork A: amplification multiplier value.** Default 1.0 (doubles
negative valence at full threat). Mutz 2018 doesn't pin a magnitude;
this is calibrated to "noticeable but not dominant" — the 2016 affect
spike in the historical arc should be visible against the trend
without overwhelming it. **Open** to 0.5 or 1.5 if §5.5 measurement
shows over/under-strong effect.

**§5 — Fork B: 2016 threat magnitude / population scope.** Default
0.5 magnitude × 60% of party=1 agents. Alternative: smaller magnitude
+ wider population (e.g. 0.3 × 100% of all agents — universalised
threat) or larger magnitude + narrower (e.g. 0.7 × 30%). **Default
preserves Mutz 2018's asymmetric finding** (R-leaning identity
threat). Open to symmetric if Vlad has a specific empirical anchor.

**§5 — Fork C: threat decay rate.** Default 0.05 (half-life ~14
ticks). Alternative: 0.10 (~7-tick half-life, decays through one
decade) or 0.02 (~35-tick half-life, persists). Anchored by: ANES
affect data shows the 2016 spike persisting through 2020 but
narrowing by 2024 — 0.05 gives roughly that decay pattern. **Open**
to alternative if §5.5 measurement shows different decay shape.

### §5.5 Tests

**Unit tests** (`tests/test_phase8c_threat.py`):

1. `test_threat_amplifies_negative_valence` — agent with
   perceived_threat=1.0 vs. agent with perceived_threat=0.0 (else
   identical): negative valence is doubled for threatened agent.
2. `test_threat_does_not_amplify_positive_valence` — same setup but
   in cooperative-positive path: positive valence is unchanged
   regardless of threat.
3. `test_threat_amplifies_backlash_push` — backlash push magnitude
   doubles for threatened agent.
4. `test_threat_decay_halves_in_14_ticks` — agent with
   perceived_threat=0.5, ThreatDecay at 0.05 for 14 ticks:
   perceived_threat ≈ 0.25.
5. `test_threat_pillar_fallback` — agent without
   `perceived_threat` attr; AffectiveUpdate and BacklashRepulsion
   read 0.0; valence/push unchanged from Phase 8b.

**Historical-arc tests** (extend `tests/test_phase8b_mechanisms.py`):

6. `test_2016_status_threat_event_fires_at_tick_108` — historical-arc
   schedule fires `_event_2016_status_threat`; 60% of party=1 agents
   have `perceived_threat = 0.5`; party=0 agents unchanged.
7. `test_threat_decays_by_2025` — by tick 135 (2025), the mean
   perceived_threat across initially-threatened agents is below 0.05
   (decayed to noise floor).

### §5.6 Measure-then-bless gate

1. **Pillar invariant**: full suite green. Pillar S0-S4 must produce
   bit-identical affect trajectory to §4 (because threat=0.0
   everywhere in the pillar). This is the §5.5 test #5 expanded to
   the ensemble level.
2. **Historical-arc qualitative check**: 2016 affect spike should be
   visible and larger with threat mechanism on than off. The 2020
   affect should still show the COVID/Jan6 spike (existing event)
   layered on top of the 2016 threat decay.
3. **No bucket re-bless in §5** — §5 doesn't introduce or modify an
   intervention. §7's robustness pass measures the X-library under
   the cumulative §2-§6 mechanism set.

---

## §6 — Asymmetric BacklashRepulsion + X1 re-measure (E6, I3)

*The asymmetric-polarization fix Bail 2018 anchors. R-leaning users
more susceptible to backfire on cross-cutting exposure; X4 already
moved to §4 (Vlad's confirmed override).*

### §6.1 Scope and decisions pinned

| # | Decision | Choice |
|---|----------|--------|
| E6.1 | **Per-party asymmetric multiplier on `BacklashRepulsion`.** New constructor kwarg `asymmetric: dict[int, float] | None = None`. When None, all parties get multiplier 1.0 (current behaviour). When set (e.g. `{0: 0.7, 1: 1.3}` for D-half/R-heavy), each agent's backlash push is multiplied by `asymmetric[agent.party]`. The shipped default for the pillar is None (symmetric); historical_arc sets `{0: 0.7, 1: 1.3}` per Bail 2018 / Hacker & Pierson 2020 reading. Pillar-fallback: agent without `party` attr or asymmetric=None preserves Phase 6 behaviour. |
| E6.2 | **X1 re-implementation under asymmetric push.** X1 currently sets `BacklashRepulsion.strength = 0.05` (symmetric). The re-implementation: X1 sets `strength = 0.05` AND `asymmetric = {0: 0.7, 1: 1.3}` (per Bail 2018: R-users showed +0.13 SD shift toward conservatism on exposure to liberal content; D-users showed +0.04 SD shift toward liberalism — roughly a 3.25× ratio, simplified to 1.86× here for parsimony). |
| I3.1 | **X1 magnitude correction.** Currently X1 produces `Δsep = +0.50`. R1's catch: Bail 2018's actual cross-platform effect was much smaller — roughly 1-7% of the standard deviation of pre-test attitudes. The +0.50 magnitude is the model's volume effect combined with the gate-fires-always issue (D6 diagnostic addresses the latter). The asymmetric correction alone won't bring it to <0.10 (Bail's headline); it will likely move it from +0.50 to ~+0.30-0.40. **Spec does not pre-bless** the new bucket. The §11 re-measurement decides whether X1 stays "backfire" (likely) or shifts to "partial-backfire" or even to "null" if the gate firing rate drops enough across §2-§5 changes (the gate may fire less under §2's positive-going channel + §4's perception-gap amplification offsetting). **Honest acceptance**: X1's magnitude is allowed to remain larger than Bail's empirical anchor as long as the bucket is honestly labelled and the gap is documented in `methods.md §5`. |
| E6.3 | **Threat-aware asymmetry (deferred).** A possible coupling: when `perceived_threat > 0`, the asymmetric multiplier is itself amplified (threatened party becomes even more reactive). Per Fork 4 default (independence), this coupling is NOT implemented in 8c. Documented in BACKLOG.md. |

### §6.2 Files

```
modify  abm/rules/repulsion.py               # E6.1 — asymmetric kwarg + per-agent multiplier
modify  abm/pillars/calm_to_camps.py         # bundle entries for asymmetric=None (preserve pillar)
modify  abm/pillars/historical_arc.py        # asymmetric={0: 0.7, 1: 1.3} for historical_arc
modify  abm/pillars/interventions_phase6.py  # X1 setup adds asymmetric to bundle
modify  tests/test_phase6.py                 # X1 test updated for asymmetric path
create  tests/test_phase8c_asymmetric.py     # new unit tests for asymmetric backlash
modify  methods.md                           # §5 X1-magnitude limitation honestly documented
```

### §6.3 Mechanism math

```python
# Inside BacklashRepulsion.apply (modified from Phase 6):
own_party = agent.state.attrs.get("party")
# E6.1: per-party asymmetric multiplier. Pillar-fallback: None or
# missing party → 1.0 (Phase 6 symmetric).
asym = (self.asymmetric or {}).get(own_party, 1.0) if self.asymmetric else 1.0
# ... (compute push as in Phase 6 + §5 threat) ...
d = self.strength * threat_factor * asym * push / count
```

### §6.4 Judgment forks

**§6 — Fork A: asymmetric ratio.** Default {0: 0.7, 1: 1.3} ≈ 1.86×.
Bail 2018's actual effect ratio is ~3.25× but with very small absolute
magnitudes. Choices: {0: 0.7, 1: 1.3} (default, parsimonious); {0:
0.5, 1: 1.5} (3× ratio, closer to Bail's relative magnitude); {0:
0.8, 1: 1.2} (more conservative). **Default: 1.86×.** Open to Vlad's
preference; documented as a sensitivity item in §7.

**§6 — Fork B: pillar uses asymmetric or stays symmetric?** Pillar is
intentionally stylised; the historical arc is the place for empirical
asymmetry. **Default: pillar stays symmetric** (asymmetric=None);
historical_arc uses asymmetric={0: 0.7, 1: 1.3}. Open to changing if
Vlad wants the asymmetry baked into the pillar's stylised story.

### §6.5 Tests

**Unit tests** (`tests/test_phase8c_asymmetric.py`):

1. `test_asymmetric_none_preserves_phase6_behaviour` — bit-identical
   to Phase 6 BacklashRepulsion when asymmetric=None.
2. `test_asymmetric_dict_scales_per_party_push` — Party 0 agent with
   identical setup as Party 1 agent: Party 0 push smaller by 0.7/1.3
   ratio.
3. `test_x1_with_asymmetric_changes_per_party_drift` — run X1 with
   asymmetric: Party 1 agents drift further from center than Party 0
   over the release window.

### §6.6 Measure-then-bless gate

1. **Pillar invariant**: full suite green; pillar stays
   symmetric (asymmetric=None) per E6.2 default; bit-identical to §5
   pillar trajectory.
2. **X1 §11 re-measurement**: re-run `intervention_buckets` for X1.
   Report Δsep and Δaff. The asymmetric multiplier changes the *per-
   party drift* but the population mean separation may not change
   dramatically (the two parties drift apart at different rates, but
   their separation depends on both rates). Bless the measured bucket.
3. **methods.md §5 update**: X1-magnitude limitation explicitly
   documented if it remains substantially larger than Bail 2018's
   anchor.

---

## §7 — Statistical-robustness pass (S1, S2, S3)

*Last section. Re-measures the entire intervention library at larger
ensembles, sweeps the bucket cutoffs, and adds SE reporting to every
published metric. This is where every label gets re-blessed under the
new ensemble sizes.*

### §7.1 Scope and decisions pinned

| # | Decision | Choice |
|---|----------|--------|
| S1.1 | **Pillar seed count 12 → 20.** `STAGE_SEEDS = tuple(range(20))` in `tests/conftest.py`. Every §11 measurement, every pillar test, every fixture-cached engine ensemble runs at 20 seeds. Compute multiplier: 20/12 = 1.67×. |
| S1.2 | **Historical-arc seed count 5 → 15.** `HISTORICAL_SEEDS = tuple(range(15))` in `scripts/phase8b_calibration.py` and `tests/test_phase8b_mechanisms.py`. Compute multiplier: 15/5 = 3×. |
| S1.3 | **Re-bless any labels that shift under 20/15 seeds.** Every X1-X7 intervention bucket re-measured at the new seeds. If a measurement crosses a bucket boundary (e.g. X5 at Δsep = -0.14 ± 0.02 at 12 seeds might shift to -0.13 ± 0.015 at 20 seeds, staying "partial"; or could shift to -0.16, becoming "real"), the LABEL changes. Move the tag, not the threshold. |
| S2.1 | **Bucket-cutoff sensitivity sweep.** Three cutoff configurations are run end-to-end through the §11 release-phase experiment: {0.03/0.10}, {0.05/0.15} (default), {0.08/0.20}. For each, report each X-intervention's bucket label under that cutoff scheme. Result table goes in `methods.md §4` as the "sensitivity-of-labels" report. |
| S2.2 | **Defend or replace 0.05/0.15.** If the sweep shows the labels at default cutoffs are stable (most interventions stay in the same bucket across all three cutoff schemes), the default 0.05/0.15 stays. If the labels are heavily cutoff-dependent (e.g. 3+ interventions flip buckets across the sweep), then the spec recommends replacing the cutoffs with an empirically-anchored scheme (e.g. published effect-size scale). **Decision pinned: report first, decide after.** The §7.6 gate is where the decision is made based on data. |
| S3.1 | **SE reporting in methods.md.** Every per-metric report (in `methods.md §3` empirical anchors, §4.3 the library table, §5 limitations) gets point ± SE notation. SE is computed as `np.std(per_seed_values, ddof=1) / np.sqrt(n_seeds)`. The table format becomes: `Δsep = -0.14 ± 0.02 (20 seeds)`. |
| S3.2 | **SE reporting in test assertions.** Where a test asserts a metric is in a band (e.g. `test_pillar_affect_trajectory_matches_anes_within_band`), the band stays the band; the test does NOT require SE-based statistical significance. The SE goes into `methods.md`, not test assertions. (Adding statistical significance gates to assertions would force re-engineering test infrastructure; the value of SE in the report is the same.) |
| S3.3 | **CI for bucket boundaries.** Where a bucket assignment is close to a boundary (e.g. X5 at Δsep = -0.14, boundary at -0.15), report the 95% CI alongside the point: `Δsep = -0.14 ± 0.02 (CI ≈ [-0.18, -0.10])` — this lets the reader see whether the CI crosses the boundary. Honesty about close calls. |

### §7.2 Files

```
modify  tests/conftest.py                    # STAGE_SEEDS = tuple(range(20))
modify  abm/pillars/historical_arc.py        # documentation of HISTORICAL_SEEDS=15
modify  scripts/phase8b_calibration.py       # HISTORICAL_SEEDS=15
modify  scripts/phase6_calibration.py        # SE reporting in output
create  scripts/phase8c_cutoff_sweep.py      # S2 cutoff sensitivity sweep
modify  abm/pillars/interventions_phase6.py  # update effect_buckets to re-blessed values
modify  tests/test_phase6.py                 # _classify_sep/_classify_aff helpers may need adjusting if cutoffs change (default: stay)
modify  methods.md                           # SE reporting; cutoff-sweep table; updated library section
```

### §7.3 Mechanism math

```python
# SE for an ensemble.
def standard_error(values: list[float]) -> float:
    return float(np.std(values, ddof=1) / np.sqrt(len(values)))

# 95% CI from t-distribution (n_seeds is small; t not z).
from scipy.stats import t
def ci_95(values: list[float]) -> tuple[float, float]:
    mean = float(np.mean(values))
    se = standard_error(values)
    n = len(values)
    crit = t.ppf(0.975, n - 1)
    return (mean - crit * se, mean + crit * se)
```

### §7.4 Judgment forks

**§7 — Fork A: keep 0.05/0.15 default or replace.** Default: keep
unless sweep shows heavy cutoff-dependence (defined: 3+ interventions
flip buckets across {0.03/0.10}, {0.05/0.15}, {0.08/0.20}). **The
sweep results inform the decision** — this fork resolves at §7.6
gate, not now.

**§7 — Fork B: SE reporting in tests too?** Default: no — tests
report bands, SE goes in methods.md. **Open** to adding SE-based
significance gates if Vlad wants tests to themselves report
statistical claims; this is a larger refactor and likely Phase 8d.

**§7 — Fork C: 20/15 seed counts.** Default per Vlad's brief (pillar
12→20, historical 5→15). **Open** to smaller (16/10 = ~33% compute
saving) or larger (24/20 = ~67% more) if §7 compute budget proves
tight or generous. Vlad's brief approved 8-15 hours of total compute;
the realised compute will be reported at §7.6.

### §7.5 Tests

**No new unit tests** — §7 is statistical re-measurement. The
existing pillar suite + mechanism suite + §2-§6 unit tests all run
at the new seed counts. Their pass/fail tells us whether the larger
ensemble changes pillar behaviour.

**Re-bless tests**: the consolidated `test_intervention_library_directions_hold`
test in `tests/test_phase6.py` uses each intervention's
`effect_buckets`. After §7's re-measurement, each `effect_buckets`
entry is updated to the new measurement; the test then passes at the
new ensemble. (Or fails — if the new measurement doesn't match the
declared bucket, the implementer re-blesses.)

### §7.6 Measure-then-bless gate

1. **Pillar S0-S4 invariant at 20 seeds.** All 73 pillar tests pass.
   Any test that was within ±5% of its band at 12 seeds is re-blessed
   to the 20-seed measurement.
2. **§11 re-measurement of every X-intervention.** X1-X7 all
   re-measured at 20 pillar seeds. New `effect_buckets` entries
   committed. The consolidated bucket test passes.
3. **Cutoff sweep result table.** `scripts/phase8c_cutoff_sweep.py`
   runs the §11 experiment under each of the three cutoff
   configurations; outputs a table. Sensitivity is reported in
   `methods.md §4`.
4. **SE columns added to methods.md library table.** Every Δsep /
   Δaff entry gets point ± SE.
5. **CI for close-call buckets**: any intervention whose bucket
   assignment is within 1 SE of a boundary gets the full CI reported
   in `methods.md`.
6. **Historical-arc 15-seed ensemble.** Re-run; report mean ± SE for
   each 1980, 1990, 2000, 2010, 2020, 2025 decade-end metric (party
   sep, affect, constraint, within-party SD). The "honest miss"
   documentation in `phase8b_results.md` is updated with the new SE
   data.

---

## Tests summary

```
Section    Unit tests added    Suite tests modified    Total green target
§1         0                   0                       86 (current)
§2         5 + 1 regression    3                       92
§3         4                   1                       96
§4         6                   2                       104
§5         5 + 2 historical    1                       112
§6         3                   1                       116
§7         0 (re-bless only)   ~5 (effect_buckets)     116 — all green at 20 seeds
```

The pillar invariant **never drops below 73 tests** through every
section. The historical-arc and Phase 8b mechanism suite grows from
13 → 17 over §2-§5. The §11 consolidated bucket test stays at one
test that grows as X7 is added in §4. Total green target at §7 end:
~116 tests.

---

## Build sequencing (one chapter per section)

```
§1 (D1-D6, docs only)
  → independent review → manual diff check → close

§2 (E2, E3, I2)
  Slice 1: AffectiveUpdate rewrite (positive-going + agent-level mute)
  Slice 2: cooperative_share attribute + X6 setup update
  Slice 3: Schedule warmth shock + Obama-2008 test event
  → review → test-verify (86 → 92 green) → X6 §11 re-bless → close

§3 (E1, I1)
  Slice 1: MediaConsumption per-outlet pull rewrite
  Slice 2: X3 setup function + bundle update
  → review → test-verify (92 → 96) → X3 §11 re-bless → close

§4 (E4, I5, I4)
  Slice 1: perceived_other_party attribute + initial bias seeding
  Slice 2: PerceptionUpdate rule + AffectiveUpdate read with fallback
  Slice 3: X7 intervention + X4 prime re-implementation
  → review → test-verify (96 → 104) → X4 + X7 §11 bless → close

§5 (E5)
  Slice 1: perceived_threat attribute + AffectiveUpdate amplification
  Slice 2: BacklashRepulsion amplification + ThreatDecay rule
  Slice 3: 2016 threat event in historical-arc schedule
  → review → test-verify (104 → 112) → historical-arc qualitative → close

§6 (E6, I3)
  Slice 1: asymmetric BacklashRepulsion (per-party multiplier)
  Slice 2: X1 setup updated; pillar stays symmetric
  → review → test-verify (112 → 116) → X1 §11 re-bless → close

§7 (S1, S2, S3)
  Slice 1: STAGE_SEEDS=20 + HISTORICAL_SEEDS=15
  Slice 2: cutoff sensitivity sweep
  Slice 3: SE reporting in methods.md + close-call CIs
  → review → test-verify (116 all green at 20 seeds) → final bless → 8c close
```

Each section's "close" is a SHORT result post to Vlad, the same
discipline as Phase 4-8b. On result post → Vlad confirms or flags →
next section starts. If a section's implementation surfaces a
genuinely new judgment fork the spec didn't anticipate, the section
hard-stops and the fork is flagged before proceeding.

---

## Re-validation — whole-phase gate

After §7 closes:

1. **Test count**: ≥ 116 green at 20 pillar seeds and 15 historical
   seeds.
2. **`methods.md` updated end-to-end**: tag re-audit, projection note,
   FJ note, X7 added, X4 shared-identity-prime documented, X1
   asymmetric correction documented, agent-level cooperative-mute
   documented (edge-level note removed), per-outlet media
   documented, perception-gap section added, status-threat anchor
   added, sensitivity-of-labels table, SE columns.
3. **`phase8b_results.md` updated**: historical-arc honest-miss
   documentation refreshed with the 15-seed SE data.
4. **All seven §11 re-bless tags committed** in
   `interventions_phase6.py`'s `effect_buckets` entries.
5. **Independent review (subagent)** of the entire 8c diff before
   final close: spot-check that every D-fix really fixed what it
   claimed; every new attribute has pillar-fallback; every new rule
   reads the env/attrs with fallback; every intervention has
   re-blessed buckets.
6. **One closing summary** to Vlad: what landed, what shifted in
   labels, what compute was burned, what got documented as a 8d
   candidate.

---

## Supersedes, open items, done checklist

**Supersedes:**
- `phase6_spec.md §1 R5` + `§9 sign-convention text` (D2 fixes).
- `methods.md §3.3 "edge-level mute"` paragraph (replaced with
  agent-level mute in §2).
- `methods.md §3.1 ANES projection paragraph` (D4 fix).
- `methods.md §4.3 library table` (re-blessed in §7).
- The X3 setup in `interventions_phase6.py` (replaced in §3).
- The X4 setup in `interventions_phase6.py` (replaced in §4 with the
  Levendusky 2021 shared-identity-prime mechanism per Vlad's Fork 2
  override).

**Open items / 8d candidates** (deferred, documented in BACKLOG.md):
- HK phase-diagram test at T > 0 (Lorenz 2007 reading).
- Income/inequality channel.
- Detailed demographic stratification (race × religion × education).
- In-party warmth as a separate affect channel.
- Threat × asymmetry coupling.
- Full factorial / Sobol identifiability decomposition.
- Phase 5 §3.2 normalisation rescale (D3 part b) — if §7 surfaces an
  over-range problem.
- Edge-level cooperative-mute machinery cleanup (now unused after §2;
  `network.is_cooperative` API stays for §2 positive-path trigger
  but the edge-level negative mute is gone).

**Done checklist (whole 8c):**
- [ ] §1 D1-D6 docs/math fixes.
- [ ] §2 E2 positive-going + E3 agent-level coop + I2 X6 re-bless.
- [ ] §3 E1 per-outlet media + I1 X3 re-implementation.
- [ ] §4 E4 perception-gap + I5 X7 + I4 X4 shared-identity-prime.
- [ ] §5 E5 identity-threat mechanism.
- [ ] §6 E6 asymmetric backlash + I3 X1 re-measure.
- [ ] §7 S1 seed bump + S2 cutoff sweep + S3 SE reporting.
- [ ] Whole-phase review + final close summary.

**Standing by for Vlad's confirm on the whole compound spec.** On
confirm, §1 starts.
