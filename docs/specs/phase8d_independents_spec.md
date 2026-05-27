# Phase 8d Implementation Spec — Independent / unaffiliated agents

*Compound spec, house style: every decision pinned; routine forks
defaulted + documented per Vlad's "don't hard-stop on routine
forks" directive (Vlad offline). Six sections, single deliverable.*

*Phase 8d adds a third agent category for **pure independents /
unaffiliated voters**. Currently `party ∈ {0, 1}`; 8d extends to
`party ∈ {0, 1, 2}` with 2 = independent. The empirical anchor is
ANES "pure independents" at ~10-15% of the US electorate (Klar &
Krupnikov 2016 *Independent Politics*; Petrocik 2009). Pillar
stays binary-party bit-identical (`independent_fraction = 0.0`
default); the independents-enabled build is opt-in via a new
constructor kwarg.*

---

## 0. Whole-phase decisions pinned

| # | Decision | Choice |
|---|----------|--------|
| W1 | **Representation: integer party=2 extension.** `party ∈ {0, 1}` becomes `party ∈ {0, 1, 2}`. Cleaner than `party=None` (no Optional/None checks needed in numpy / dict iteration), cleaner than continuous `partisan_lean ∈ [-1, 1]` (would require refactoring every rule). The literature distinguishes "partisan" (0, 1) from "pure independent" (2); the integer extension matches that categorical reading. Klar & Krupnikov 2016 + Petrocik 2009 are the anchors. |
| W2 | **Default fraction: 0.12 (12%).** Midpoint of the 10-15% "pure independents" band Vlad's brief flagged. Matches ANES 2020 "pure independent" share (about 11.5% at that wave). The `independent_fraction` kwarg makes this tunable per scenario. **Alternative: 0.10 or 0.15** — routine fork, deferred to §7 sensitivity sweep if needed. |
| W3 | **Pillar default: `independent_fraction = 0.0`.** Pillar S0-S4 stays binary-party. The 73 sacred pillar tests + the 53 §2-§6 tests all pass at the existing thresholds **bit-identical to Phase 8c §7**. Independents only appear in opt-in builds (pillar-variant fixture for §11 re-measurement + historical_arc). |
| W4 | **PartyPull skips independents.** `party=2` agents have no party_cue (not seeded at build) → PartyPull's existing `if cue is None: return` branch already handles them as no-ops. No code change to PartyPull. |
| W5 | **AffectiveUpdate: affect-neutral for independents.** Per Klar & Krupnikov 2016: pure independents are *not* affectively engaged with parties (low or zero out-party animus). Mechanism: AffectiveUpdate's existing `if agent_party is None: return StateDelta()` guard is extended to also short-circuit when `agent_party == 2`. Independents don't carry an `affect` dict; their out-party warmth never updates. **Alternative**: weak-proximity affect where independents develop small affect toward each party based on ideological distance. Routine fork; affect-neutral is the literature-faithful default. Documented as deferred. |
| W6 | **BacklashRepulsion skips independents.** Same guard: `agent_party == 2` short-circuits to empty StateDelta. Independents have no in-party identity threat to defend, so no backlash. |
| W7 | **PerceptionUpdate skips independents.** Independents don't carry `perceived_other_party` (no "other party" to perceive when you're not in either camp). The existing `perceived is None` guard handles this. |
| W8 | **BoundedConfidenceInfluence + MediaConsumption + TieRewiring + GaussianNoise + IdentitySorting: independents fully participate.** They're influenced by ideologically-near neighbours via BC, by media via MediaConsumption (centrist diet by default), form homophilous ties via TieRewiring, anchor via GaussianNoise's FJ damping. IdentitySorting's identity-position alignment also fires for them (their multi-dim identities have no partisan center bias). |
| W9 | **Independent initial position distribution.** Not centrist by definition. Initial `ideology ∈ [-1, 1]²` drawn from `N(0, 0.4)` (broad spread, centered at origin). Some independents are ideological extremists who don't fit either party (e.g., libertarians, greens); some are moderates. The N(0, 0.4) spread matches that empirical heterogeneity. **Alternative**: bimodal (one cluster of moderates at origin + one cluster of fringe-ideological at edges). Routine fork; centred Gaussian is the parsimonious default. |
| W10 | **Independent multi-dim identities.** `identities` array drawn from `N(0, 0.3)`, zero-mean (no party-aligned center). Matches a "not strongly aligned on any partisan-coded identity" reading. |
| W11 | **Independent media_diet.** Default: `diet_for_party(party_pos=origin, outlets, rng)`. The diet target sits at the centroid of outlets (which already trends inward in the 2024 roster); independents consume a centrist-balanced diet. **Alternative**: party-agnostic uniform diet across outlets. Routine fork; centroid-anchored diet matches the existing `diet_for_party` interface. |
| W12 | **Independent stubbornness.** Drawn from `Beta(2, 5)` like partisans (same anchoring distribution; literature doesn't suggest independents are systematically more/less stubborn than partisans). |
| W13 | **§11 measurement: re-measure all 7 X-buckets under the pillar-variant build with `independent_fraction = 0.12`.** New fixture `intervention_buckets_with_independents` parallel to `intervention_buckets`. Both fixtures run; the canonical headline buckets stay at the binary-party measurement (Phase 8c §7 numbers). The variant buckets are added to `methods.md §4.5` as a sensitivity reading: "what happens when 12% of the population is independent." Expected direction: X1 macro Δsep comes down (12% of agents don't fire BacklashRepulsion); X4 prime hits fewer "useful" targets (independents are already low-identity); X6 affect warming still applies to partisans (Independents don't get a cooperative_share bump since their out-party is None). |
| W14 | **Historical_arc opt-in.** Historical_arc's `build_engine` adopts `independent_fraction = 0.12` from 1980 onward. ANES historical data shows independents have been ~30-40% (broad category) since the 1970s, with pure independents ~10-15% steadily. **Constant 12% across decades** is the simplest seeding; per-decade variation is deferred (rich-generations work is parked in BACKLOG per Vlad's call). |
| W15 | **Pillar `party_separation` metric.** The current `party_separation` reads `parties[parties == 0]` and `parties[parties == 1]` party-mean centroids. With party=2 present, `np.linalg.norm(pos[parties==0].mean(...) - pos[parties==1].mean(...))` still computes correctly (it filters to partisans). The current metric is **party-aware by construction**; no change needed. Similarly for `affective_polarization` (which iterates `affect` dicts — independents have no `affect` dict, so they're excluded). |
| W16 | **Pillar `cross_cutting_tie_fraction` metric.** Currently counts edges where `party_a != party_b`. With party=2 present, edges from 2-to-0 and 2-to-1 count as cross-cutting (which is honest — those ARE cross-cutting ties from a partisan perspective). No change needed. |
| W17 | **No new X-intervention in 8d.** Mechanism-only (mirrors §5 discipline). A potential X8 "Mobilize Independents" intervention is a 8e+ candidate. |

---

## §1 — Agent build changes

### §1.1 New build kwarg

`abm/pillars/calm_to_camps.py::build_engine` gains kwarg
`independent_fraction: float = 0.0`. Default 0.0 → bit-identical to
Phase 8c §7 behaviour. When non-zero, `int(independent_fraction *
n_agents)` agents are randomly assigned `party = 2` instead of
`party ∈ {0, 1}`.

`abm/pillars/historical_arc.py::build_engine` gains the same kwarg
with default `0.12` (12% pure independents).

### §1.2 Independent agent attributes (at build)

For each independent agent:
- `party = 2`
- `group = 2`
- `identities = np.clip(rng.normal(0, 0.3, size=n_identities), -1, 1)` (zero-mean, broader spread, no partisan center).
- `identity_strength = float(rng.beta(2, 2))` (same distribution as partisans; not weaker by construction).
- `ideology = clipped N(0, 0.4) draw` (broader centered Gaussian — not pinned to either party's region).
- `anchor = ideology.copy()` (F1 stubbornness anchor).
- `stubbornness = float(rng.beta(2, 5))` (same as partisans).
- `media_diet = diet_for_party(party_pos=np.zeros(2), outlets, rng)` (centrist diet).
- **No** `party_cue`. **No** `affect` dict. **No** `perceived_other_party`. **No** `cooperative_share`. **No** `identity_weight_override`. **No** `perceived_threat`.
- For historical_arc agents: also no per-agent heterogeneity attrs (`epsilon`, `fj_alpha`, `affect_lr`) — they'd be unused for independents anyway.

### §1.3 Sampling

Independents are sampled uniformly: `n_indep = int(independent_fraction * n_agents)`; the first `n_indep` integers in `rng.permutation(n_agents)` get assigned party=2. The remaining agents follow the existing partisan assignment logic (sign-based for pillar; sigmoid-probabilistic for historical_arc).

---

## §2 — Rule guards

Most rules already handle the `party is None` no-data case. §2 extends each guard to also short-circuit on `party == 2`:

### §2.1 `AffectiveUpdate.apply`

```python
agent_party = agent.state.attrs.get("party")
if agent_party is None or agent_party == 2:
    return StateDelta()
```

### §2.2 `BacklashRepulsion.apply`

```python
own_party = agent.state.attrs.get("party")
if own_party is None or own_party == 2:
    return StateDelta()
```

### §2.3 `PartyPull.apply`

PartyPull already checks `if cue is None: return StateDelta()`.
Independents have no `party_cue` → already a no-op. No change.

### §2.4 `PerceptionUpdate.apply`

Already guards `if perceived is None or not perceived: return StateDelta()`. Independents have no `perceived_other_party` → already a no-op. No change.

### §2.5 `IdentityPrimeExpiry`

Iterates agents; for each, reads `identity_prime_expires_at`. Independents don't carry this attr → already a no-op per-agent.

### §2.6 `ThreatDecay`

Same: reads `perceived_threat` per agent. Independents don't carry it → already a no-op per-agent.

### §2.7 Other rules (BC, MediaConsumption, TieRewiring, GaussianNoise, IdentitySorting, ResidentialMigration, CohortReplacement)

These are partisan-agnostic by design. Independents participate normally:
- **BC**: independents pull toward ideologically-near neighbours regardless of party.
- **MediaConsumption**: independents have a `media_diet` (centrist), pulled toward outlet centroid.
- **TieRewiring**: homophilous rewiring by `(ideology, social_coord)` distance; party affects nothing.
- **GaussianNoise**: anchor damping via F1 stubbornness; partisan-agnostic.
- **IdentitySorting**: aligns `identities` toward party centroid (`party_identity_centers`). Independents have `identities` but no `party_identity_centers[2]` mapping; the rule's existing fallback handles missing keys.
- **ResidentialMigration**: updates `social_coord` based on neighbourhood composition; partisan-agnostic.
- **CohortReplacement**: replaces a fraction of agents per tick with new agents. Independents are treated like other agents for replacement; new agents are partisan by the current sigmoid logic (does not preserve independent fraction across cohort replacement — flagged as a §3 follow-up).

### §2.8 IdentitySorting — check the existing implementation

Need to verify `IdentitySorting` handles `party=2` without throwing. If it reads `env.attrs["parties"][party]`, party=2 would raise KeyError. Need to inspect during implementation and add a guard if needed.

---

## §3 — Cohort dynamics (historical-arc-only follow-up)

When `CohortReplacement` fires (per Phase 8b M3), it currently replaces old agents with new partisan agents. With independents in the population, the long-run fraction of independents would decay toward zero (cohort replacement always adds partisans).

**Mitigation: preserve independent fraction at cohort-replacement time.** Modify the replacement logic so new agents respect `independent_fraction` — i.e., the cohort replacement RNG also samples `party=2` at the configured rate. Implementation detail in `abm/rules/cohort_replacement.py` (env_rule). Minimal change.

This keeps the independent population stable at ~12% across the 1980-2025 historical arc.

---

## §4 — Metrics

### §4.1 `party_separation` (`tests/conftest.py::party_separation`)

Reads `parties[parties == 0]` and `parties[parties == 1]` separately. With party=2 present, party=2 agents are automatically excluded from both filters. **No change needed.** The metric measures partisan separation, which stays comparable across the binary-party vs. with-independents builds (just operates on a smaller partisan subset).

### §4.2 `affective_polarization` (`abm/metrics/affective.py`)

Iterates agents and reads `affect` dicts. Independents have no `affect` dict → loop skips them. **No change needed.**

### §4.3 `ideological_constraint` (`abm/metrics/affective.py`)

Computes Pearson correlation between party (0/1) and ideology (x, y). With party=2 agents in the mix, they'd be included in the array as party=2 — would distort the correlation. **Need to filter to partisans only.** Single edit in the metric.

### §4.4 `cross_cutting_tie_fraction` (`abm/metrics/network.py`)

Counts edges where `party_a != party_b`. With party=2 present, party=2-to-party=0 and party=2-to-party=1 ties count as cross-cutting. This is honest — those ARE cross-cutting from a partisan perspective. **No change needed**, but the interpretation shifts: the metric becomes "fraction of edges that cross partisan boundaries" rather than "fraction of edges between two specific parties."

### §4.5 `party_modularity` (`abm/metrics/network.py`)

Computes modularity treating each party as a community. With party=2 present, modularity gains a third community. The numeric value will shift (modularity is sensitive to community count), but the qualitative reading stays meaningful. **No change needed.**

---

## §5 — §11 X-intervention re-measurement under independents

### §5.1 New fixture `intervention_buckets_with_independents`

Parallel to the existing `intervention_buckets`, but builds with
`independent_fraction = 0.12`. Same X-interventions, same seeds,
same release-phase window. Results go into `methods.md §4.5`
sensitivity table.

### §5.2 Predicted directions

- **X1 (cross-cutting exposure)**: macro Δsep should come DOWN (12% of agents don't fire BacklashRepulsion). Bucket may shift from `backfire` to `partial` or `null`.
- **X2 (algorithm reset)**: still null/null (X2 just zeros affect_weight, not affected by independents).
- **X3 (quit cable news)**: still null/null (independents have centrist diet by default, X3 zeroes cable outlets — small effect on partisans, no effect on independents).
- **X4 (shared-identity prime)**: still null/null at population level. Primed independents are a wasted prime (they already have low partisan identity weighting). Bucket unchanged.
- **X5 (RCV)**: still partial/null (halving centroids affects only partisans; independents don't have party_cue to halve). Macro Δsep might come down slightly.
- **X6 (shared institutions)**: still null/real on affect. Independents don't get cooperative_share bump (they have no out-party affect to mute), but they participate in new cooperative ties.
- **X7 (perception correction)**: still null/null in pillar release. Independents have no perception to correct.

### §5.3 Predicted X8+ candidates (deferred)

A potential X8 "Mobilize Independents" or "Reach the persuadables" intervention — not in 8d. Documented in BACKLOG.md as 8e candidate.

---

## §6 — Tests

### §6.1 New test file `tests/test_phase8d_independents.py`

~15-18 tests covering:

1. `test_default_no_independents` — `build_engine()` without the kwarg produces 0 party=2 agents.
2. `test_independent_fraction_seeds_correct_count` — `build_engine(independent_fraction=0.12, n_agents=250)` produces 30 party=2 agents.
3. `test_independents_lack_party_cue` — party=2 agents have no `party_cue` attr.
4. `test_independents_lack_affect_dict` — party=2 agents have no `affect` attr.
5. `test_independents_lack_perceived_other_party` — party=2 agents have no perception attr.
6. `test_independents_have_identities_and_anchor` — party=2 agents DO carry identities + anchor + stubbornness + media_diet (full participation in BC + media + GaussianNoise + IdentitySorting).
7. `test_partypull_no_op_on_independents` — PartyPull.apply on a party=2 agent returns empty StateDelta.
8. `test_affective_update_no_op_on_independents` — AffectiveUpdate.apply on a party=2 agent returns empty StateDelta.
9. `test_backlash_repulsion_no_op_on_independents` — BacklashRepulsion.apply on a party=2 agent returns empty StateDelta.
10. `test_independents_move_via_bc` — A party=2 agent surrounded by ideologically-near party=0 agents drifts toward them via BC.
11. `test_independents_move_via_media` — A party=2 agent with `media_diet` drifts toward outlet centroid.
12. `test_pillar_default_bit_identical` — Pillar S4 trajectory with `independent_fraction=0.0` is bit-identical to Phase 8c §7 (compare positions array post-200-tick run).
13. `test_pillar_with_independents_runs_clean` — Pillar S4 with `independent_fraction=0.12` runs without exceptions for 200 ticks.
14. `test_party_modularity_with_independents` — `party_modularity` returns a numeric value with party=2 present (no exception).
15. `test_ideological_constraint_filters_partisans` — `ideological_constraint` returns the same value with and without party=2 present (filters to partisans only).
16. `test_x1_bucket_under_independents` — X1's measured Δsep with 12% independents is strictly less in magnitude than the binary-party measurement (because 12% of agents don't fire backlash).

### §6.2 Existing tests must stay green at 20 seeds

The full pre-8d suite (139 tests) runs at `independent_fraction = 0.0` and must stay green bit-identically. The §11 consolidated bucket test uses the existing `intervention_buckets` fixture (binary party), so it's unaffected.

---

## §7 — Build sequencing + close

```
§1 (build kwarg + Independent agent attrs)
  → smoke test
§2 (rule guards — AffectiveUpdate + BacklashRepulsion)
  → smoke test
§3 (CohortReplacement preserves independent fraction)
  → smoke test
§4 (metric edits — ideological_constraint filter)
  → smoke test
§5 (new intervention_buckets_with_independents fixture)
  → §11 re-measurement under independents
  → bless variant buckets in methods.md §4.5
§6 (tests)
  → independent review subagent
  → full suite green
  → post §8d result
```

Each section closes by running the suite (139 + new tests). Pillar bit-identity is the keystone gate: any threshold drift means I hard-stop and flag.

**Standing by — no confirm needed per the autonomous brief; the routine forks (W2, W5, W9, W11, W14) are defaulted and documented above.** Beginning §1 implementation immediately after writing this spec.
