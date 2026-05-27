# Phase 5 Implementation Spec — Affective Polarization as a First-Class Channel

*Builds on Phase 4 (realism core: anchored agents, graded confidence filter,
involuntary cross-cutting tie stratum). Phase 5 promotes affect from a
passive metric tracked by `AffectiveUpdate` to a **first-class channel** —
agents' out-party warmth/coolness updates with its own dynamics, drives the
sorting findings the literature requires (Iyengar et al. 2019; Mason 2018;
Finkel et al. 2020), and feeds back into who agents listen to and stay tied
to. The known Phase 4 carry-over — the `AffectiveUpdate` sign issue —
is fixed here.*

*Like Phases 3-4, post-change thresholds cannot be pre-measured (affect
will now have feedback channels into the dynamics); §11 is a
measure-then-bless gate.*

---

## 1. Scope and decisions pinned

Phase 5 adds **one new mechanism (the corrected `AffectiveUpdate` dynamic)**
and gives affect **two feedback channels** (into the confidence filter and
into tie rewiring). The model gains a second polarization channel —
affective — that runs independently of issue position.

| # | Decision | Choice |
|---|----------|--------|
| A1 | **Affect dynamics rewrite.** `AffectiveUpdate` is rewritten so out-party affect *falls* (more coolness) with **identity disagreement and issue disagreement** rather than rising with ideological proximity. The valence becomes a blend: `valence = -(w_id * identity_distance + w_iss * issue_distance - baseline)`. Per-tick affect update: `Δaffect_out = lr * valence` per out-party neighbour seen. No symmetric in-party update — Finkel et al. 2020: in-party warmth is roughly stable, out-party animus is what moves. The sign is now **negative-going**: each interaction with an out-party neighbour pushes affect *toward coolness* unless the neighbour is very close on both ideology and identity. **This is the explicit fix of the known sign issue.** |
| A2 | **Issue-vs-identity weighting.** The blend uses `w_id = 0.5, w_iss = 0.5` to start. The `identity_weight` attribute on `AffectiveUpdate` (already present, set to 0.5 in `build_engine`) plays this role; the formula's shape changes, not the slot. |
| A3 | **Baseline drift.** A small constant `baseline = 0.10` is subtracted so that even a low-distance encounter contributes slight coolness — the Mason mega-identity logic: any out-party encounter is a salience event. Without a baseline term, agents who happen to live near a moderate out-party neighbour would warm steadily, which contradicts the literature. The baseline is the per-encounter "this person is on the other team" cost. |
| A4 | **Affect feeds back into the confidence filter.** `BoundedConfidenceInfluence` reads `agent.state.attrs["affect"]` per neighbour. The graded logistic weight is multiplied by an **affect modulator** `m(affect) = 1 + affect_weight * affect[neighbour_party]`, clipped to `[0.1, 2.0]`. With the pinned `affect_weight = 0.3` and affect in `[-1, 1]`, a hostile (very cold) out-party tie's weight is multiplied by `0.7`; a warm one by `1.3`. Same-party neighbours: no affect entry, multiplier defaults to `1.0`. This makes the channel real but mild: affect doesn't just track polarization, it nudges sorting by muting hostile neighbours' influence — without the cliff behaviour of a stronger weight. |
| A5 | **Affect feeds back into tie rewiring.** `TieRewiring` augments its drop ranking — instead of "drop the most ideologically-distant voluntary tie," it drops the voluntary tie that scores worst on `combined_distance + affect_weight_rewire * (-affect_to_neighbour_party)`. With `affect_weight_rewire = 0.30` and combined distance in roughly `[0, 2]`, a very cold out-party tie is preferred for dropping over an ideologically-distant in-party tie. The candidate-add side is unchanged (still picks the closest of `n_candidates`). |
| A6 | **Stage placement.** The affect channel turns on at **S2** (party identity stage) — that is when out-party exists and affect can be meaningful. S0 has no parties, S1 has parties but no party-driven pull. `AffectiveUpdate.lr` activates at S2 (was already in the S2 bundle at `lr = 0.01`). The two new bundle knobs — `BoundedConfidenceInfluence.affect_weight` and `TieRewiring.affect_weight_rewire` — also activate at S2 (off at `0.0` in S0, S1; on at S2-S4). |
| A7 | **Metric integration.** `affective_polarization` is now a primary readout for S2-S4 alongside `ideological_constraint`. It must rise (in magnitude — affect goes more negative) faster than `ideological_constraint` rises during S2-S3, reproducing Iyengar et al. 2019's headline empirical finding. A new directional test pins this. |
| A8 | **What stays.** `affect` is still a dict `{other_party_id: warmth_in_[-1,1]}` per agent. `affective_polarization` operationalization is unchanged (mean out-party warmth, clipped). `IdentitySorting` is unchanged. No new rule classes; only `AffectiveUpdate` is rewritten and two existing rules gain affect-aware terms. |

**Out of scope.**

- Affect feeds back into ideology (does feeling cold toward out-party *push*
  your issue position? Bail et al. 2018 says yes for some agents). Phase 6's
  repulsion / backfire territory.
- Asymmetric in-party warming (the literature finds in-party warmth is
  roughly stable; not adding a positive in-party update for now).
- Per-agent heterogeneous `lr` for affect. Phase 7 calibration.
- Replacement of `IdentitySorting` with a more sophisticated identity
  dynamic. Phase 7 if needed.
- Tick-to-real-time calibration. Phase 7.

---

## 2. Files

```
modify  abm/rules/affective_update.py  # rewrite dynamics + fix the sign issue
modify  abm/rules/influence.py         # affect_weight modulator on the graded filter
modify  abm/rules/tie_rewiring.py      # affect_weight_rewire on the drop ranking
modify  abm/pillars/calm_to_camps.py   # bundle knobs + new constants
modify  abm/metrics/affective.py       # docstring; no behavioural change
create  tests/test_phase5.py           # affect-direction and feedback tests
modify  tests/test_pillar_stages.py    # add the Iyengar test (affect outpaces ideology)
modify  tests/conftest.py              # affect helpers if needed (small)
```

`abm/core/engine.py`, `abm/core/network.py`, `abm/pillars/intervention.py`,
the canonical / machinery / network / phase4 test modules are expected to
need **no change** — verify.

---

## 3. A1 — Affect dynamics rewrite

### 3.1 The new `AffectiveUpdate.apply`

The rewrite keeps the existing signature, slots, and three init parameters
(`radius`, `learning_rate`, `identity_weight`) but corrects the valence
formula. The rule now also reads two new attributes (set via the bundle):
none — `identity_weight` already exists. Adds one new init param
`baseline`.

```python
class AffectiveUpdate:
    def __init__(
        self,
        radius: float = 1.5,             # vestigial — kept as state-vector
                                          #   normalization scale only
        learning_rate: float = 0.01,
        identity_weight: float = 0.5,
        baseline: float = 0.10,           # NEW: per-encounter "they're the
                                          #   other team" coolness floor
    ):
        ...

    def apply(self, agent, space, env, rng):
        if self.lr == 0:
            return StateDelta()
        agent_party = agent.state.attrs.get("party")
        if agent_party is None:
            return StateDelta()
        neighbors = neighbor_agents(agent, space, env)
        my_ids = agent.state.attrs.get("identities")
        use_ids = (self.identity_weight > 0
                   and my_ids is not None and len(my_ids) > 0)
        affect_delta = {}
        for neighbor in neighbors:
            other_party = neighbor.state.attrs.get("party")
            if other_party is None or other_party == agent_party:
                continue
            d_iss = float(np.linalg.norm(
                agent.state.ideology - neighbor.state.ideology
            ))
            issue_term = d_iss / self.radius            # normalize to ~[0,1]
            if use_ids:
                their_ids = neighbor.state.attrs.get("identities")
                if their_ids is not None and len(their_ids) == len(my_ids):
                    diffs = np.abs(np.asarray(my_ids) - np.asarray(their_ids))
                    identity_term = float(np.mean(diffs)) / 2.0  # to [0,1]
                else:
                    identity_term = issue_term
            else:
                identity_term = issue_term
            # Disagreement on either axis pushes affect toward coolness;
            # the baseline term ensures any out-party encounter contributes
            # at least mild coolness (Mason: out-party encounters are
            # salience events for partisan identity).
            disagreement = (
                self.identity_weight * identity_term
                + (1.0 - self.identity_weight) * issue_term
            )
            valence = -(disagreement + self.baseline)     # NEGATIVE-going
            affect_delta[other_party] = (
                affect_delta.get(other_party, 0.0) + self.lr * valence
            )
        if not affect_delta:
            return StateDelta()
        return StateDelta(d_attrs={"affect": affect_delta})
```

### 3.2 Why the change is honest and contained

- **The sign fix.** Today the rule emits positive valence when `d < radius/2`
  (warming on near out-party encounters). At `radius = 1.5`, "near" means
  `d < 0.75`, which is most of the [-1,1]² compass. So today S2-S3 *warm*
  agents toward the out-party — exactly the opposite of Iyengar et al. 2019.
  The rewrite makes the valence always negative-or-near-zero for out-party
  encounters, matching the literature.
- **The baseline is small.** `baseline = 0.10` is one tenth of the maximum
  per-encounter coolness; it ensures the floor effect without dominating
  the issue/identity terms.
- **The clip lives downstream.** Affect is still clipped to `[-1, 1]` by
  the metric reader; the cumulative effect cannot diverge.
- **`radius` becomes vestigial.** Kept as a state-vector normalization
  scale only — not a query radius (that was already true post-ADR-001).
  Could be deleted in Phase 7 if no other rule references it; leave as-is
  to avoid touching every scenario's `AffectiveUpdate(...)` call.

### 3.3 The `radius` normalization choice

`d_iss / radius` puts issue distance into roughly `[0, 1]` for `radius = 1.5`
(the maximum issue distance on `[-1,1]^2` is `2.83`, so the ratio can
exceed 1 for the most extreme pairs — capped indirectly by the affect
clip at the metric layer). This is a deliberate softness: pairs at the
extreme corners contribute extra coolness, which is honest. Alternative:
divide by `2.83` to map exactly to `[0, 1]`. The `radius = 1.5` choice
preserves the existing `build_engine` constant and keeps the formula's
shape close to today's; tuning is a Phase 7 item.

**Phase 8c D3 clarification.** Spelled out for the reader: at the
`[-1, 1]^2` compass, the maximum ideological distance is `2 * sqrt(2)
≈ 2.83`; dividing by `radius = 1.5` makes `issue_term` live in
roughly `[0, 1.89]`, not `[0, 1]`. The `disagreement` term
`identity_weight * identity_term + (1 − identity_weight) * issue_term`
therefore lives in roughly `[0, 1.45]` (because `identity_term` is
genuinely in `[0, 1]`, weighted 0.5; `issue_term` is in `[0, 1.89]`,
also weighted 0.5; the linear combination weighted by 0.5 each gives
a max around `(1 + 1.89) / 2 ≈ 1.45`). The per-encounter valence
`-(disagreement + baseline)` is in roughly `[-1.55, -0.10]` —
clipped downstream by the `[-1, 1]` affect read in metrics. This is
the honest description of the formula's range. Phase 8c §1-A Fork
defaulted to doc-only; rescaling to a literal `[0, 1]` issue_term
would shift the pillar's affect trajectory and force re-blessing of
every threshold; rescaling is deferred to backlog unless Phase 8c §7
re-measurement surfaces a problem traceable to the over-range.

**Decision (judgment fork A1):** the valence formula
`valence = -(0.5 * identity_distance + 0.5 * issue_distance + 0.10)`.
This is the *new dynamic*. The judgment is whether the linear blend with
a small baseline is the right shape, or whether we want something
sharper (e.g. `valence = -(max(identity_distance, issue_distance))`,
which says "the worst dimension dominates"), or a Mason-style
identity-only formula. Flagged for confirmation.

---

## 4. A4 — Affect feedback into `BoundedConfidenceInfluence`

### 4.1 The change

Add `affect_weight` (default `0.0` — the rule then behaves exactly as in
Phase 4). With `affect_weight > 0`, the graded logistic weight per
neighbour is multiplied by:

```python
def affect_modulator(agent, neighbour, affect_weight):
    a = agent.state.attrs.get("affect") or {}
    other_party = neighbour.state.attrs.get("party")
    own_party = agent.state.attrs.get("party")
    if other_party is None or other_party == own_party:
        return 1.0                # same-party: no affect modulation
    warmth = float(a.get(other_party, 0.0))    # in [-1, 1]
    m = 1.0 + affect_weight * warmth
    return float(np.clip(m, 0.1, 2.0))
```

At the pillar's `affect_weight = 0.3`, a cold out-party tie (warmth =
-1.0) is muted by `(1 + 0.3 * -1) = 0.7`; a warm tie (warmth = +1.0) is
amplified by `1.3`. The same-party path is a fast no-op (no dict lookup
overhead, returns 1.0).

### 4.2 Integration with the graded filter

In `BoundedConfidenceInfluence.apply`, after computing the per-neighbour
logistic weight `ws`, multiply by an `m` vector:

```python
if self.affect_weight > 0.0:
    ms = np.array([affect_modulator(agent, n, self.affect_weight)
                   for n in neighbours])
    ws = ws * ms
```

`affect_weight = 0.0` is an exact no-op (the multiplier is the constant 1.0
array; the existing logic is unchanged). The pillar's S0 / S1 bundles set
`affect_weight = 0.0`; S2-S4 set it to **`0.3`** (Vlad's override of the
spec draft's 0.5 — deliberately mild to keep the cliff behaviour Phase 4
just removed from creeping back). **Default on the rule:
`affect_weight = 0.0`** — keeps `compass_basic` and all existing scenarios
bit-unchanged, same discipline as F2.

### 4.3 Why this is the cleanest place for affect feedback

Two alternatives were considered and rejected:

- **Affect modifies the candidate set (a hard filter).** Below some warmth
  threshold, the neighbour is dropped from the candidate set. *Rejected* —
  the graded confidence filter is *already* the right machinery for "I
  listen less to people I distrust," and a hard filter would re-introduce
  the cliff behaviour Phase 4 just removed.
- **Affect adds a separate repulsion term.** *Rejected* — that is Phase 6.
  Phase 5's affect channel only modulates *attraction*; the negative-
  valence interpretation (affect pushes you *away*) belongs to repulsion
  and null-levers work.

### 4.4 Decision (judgment fork A4) — settled

`affect_weight = 0.3` (Vlad's override of the spec draft's 0.5). With
`m ∈ [0.7, 1.3]` for warmth `∈ [-1, 1]`, the affect channel nudges
sorting without halving any neighbour's pull. The 0.3 setting keeps the
"affect → sorting" feedback loop real but mild — preserving the Phase 4
graded-filter softness. The clip `[0.1, 2.0]` is a numerical safety;
warmth is already clipped to `[-1, 1]` by the metric reader.

---

## 5. A5 — Affect feedback into `TieRewiring`

### 5.1 The change

Add `affect_weight_rewire` (default `0.0`). The drop ranking becomes:

```python
def drop_score(a, j, by_id, w_ideo, w_soc, affect_weight_rewire):
    nbr = by_id[j]
    base = combined_distance(a, nbr, w_ideo, w_soc)
    if affect_weight_rewire == 0.0:
        return base
    other_party = nbr.state.attrs.get("party")
    own_party = a.state.attrs.get("party")
    if other_party is None or other_party == own_party:
        return base
    affect = a.state.attrs.get("affect") or {}
    warmth = float(affect.get(other_party, 0.0))
    # Cold ties have higher drop scores; warm ties have lower.
    return base + affect_weight_rewire * (-warmth)
```

A voluntary tie to an out-party agent with affect `-1.0` gets +0.30 added
to its drop score, making it a likely candidate. A warm out-party tie
(affect `+1.0`) gets -0.30 subtracted, protecting it.

**Involuntary ties are still excluded from rewiring** (Phase 4 F3 contract
unchanged).

### 5.2 Decision (judgment fork A5)

`affect_weight_rewire = 0.30`. Lower than `affect_weight` (the BC modulator)
because tie rewiring is per-tick stochastic — a small bias amplifies over
many ticks. Flagged for confirmation; measure in §11.

---

## 6. A6 — Stage placement and bundle wiring

### 6.1 Bundle pattern

Every bundle gains two new lines:

```python
("BoundedConfidenceInfluence", "affect_weight", <value>),
("TieRewiring", "affect_weight_rewire", <value>),
```

Stage values:

| Stage | `AffectiveUpdate.lr` | `BC.affect_weight` | `TR.affect_weight_rewire` |
|-------|----------------------|--------------------|---------------------------|
| S0 | 0.00 | 0.00 | 0.00 |
| S1 | 0.00 | 0.00 | 0.00 |
| S2 | 0.01 | 0.30 | 0.30 |
| S3 | 0.01 | 0.30 | 0.30 |
| S4 | 0.01 | 0.30 | 0.30 |

So affect is fully active from S2 onward. The S2 narrative becomes:
"parties form *and* the affective channel turns on" — which matches the
literature (party identity is what makes affect a relevant variable).

`AffectiveUpdate.baseline` is **not** a bundle parameter — it's the
per-encounter floor and is a build-time constant set in `build_engine` via
the `AffectiveUpdate(...)` constructor.

### 6.2 Build constants

In `calm_to_camps.py` at module level:

```python
# Phase 5 — affect as a first-class channel.
AFFECT_LR = 0.01                       # AffectiveUpdate.learning_rate
AFFECT_IDENTITY_WEIGHT = 0.5           # 50/50 blend of issue + identity
AFFECT_BASELINE = 0.10                 # per-encounter floor
BC_AFFECT_WEIGHT = 0.3                 # BoundedConfidenceInfluence multiplier (Vlad: milder than 0.5)
TR_AFFECT_WEIGHT_REWIRE = 0.30         # TieRewiring drop-score bias
```

`AffectiveUpdate(...)` in `build_engine` is constructed with:

```python
AffectiveUpdate(
    radius=1.5,
    learning_rate=0.0,
    identity_weight=AFFECT_IDENTITY_WEIGHT,
    baseline=AFFECT_BASELINE,
),
```

`BoundedConfidenceInfluence(...)` is constructed with `affect_weight=0.0`
(opt-in via bundle, same discipline as `temperature`):

```python
BoundedConfidenceInfluence(
    epsilon=0.30, strength=0.0,
    temperature=BC_TEMPERATURE,
    affect_weight=0.0,                 # turned on at S2
),
```

`TieRewiring(...)` similarly:

```python
TieRewiring(rewire_rate=0.0, affect_weight_rewire=0.0)
```

---

## 7. Untouched / verified-clean

- `compass_basic` and ACTB construct `BoundedConfidenceInfluence` without
  `affect_weight` (defaults to 0). Their agents lack the `affect` attr
  entirely, so even if some future code path triggered the affect-aware
  branch by mistake, the rule would compute `m = 1.0` (no out-party affect
  to read). Canonical tests stay green automatically.
- `IdentitySorting` is untouched. It already uses `identities` and `party`;
  it has no business knowing about affect.
- `BacklashRepulsion` is untouched. The repulsion channel (and any
  affect-driven backfire) belongs to Phase 6.
- `MediaConsumption` is untouched. Affect could in principle modulate
  media trust — but that's a Phase 7 mechanism if needed.

---

## 8. Metrics

`affective_polarization` operationalization is unchanged — mean out-party
warmth across the population, clipped to `[-1, 1]`. Under the new
dynamics this will go *negative* (i.e. show cooling) at S2-S4, where today
it goes positive. Update the docstring to record the corrected sign:

```python
def affective_polarization(agents) -> float:
    """Mean out-party warmth across all (agent, other-party) pairs.

    Returns a number in [-1, 1]. **More negative = more affectively
    polarized** (out-party animus is higher). Following Phase 5's
    corrected `AffectiveUpdate` dynamics, this number drops monotonically
    over S2-S4 — the operational mirror of Iyengar et al. 2019's
    "out-party thermometer" trajectory.
    """
```

No new metric is added; the `ideological_constraint` + `affective_polarization`
pair carries the Phase 5 story.

---

## 9. Tests

### 9.1 New: `tests/test_phase5.py`

Six tests.

**A1 — corrected dynamics.**

- `test_affect_update_emits_negative_valence_for_distant_outparty`: a
  hand-built two-agent setup with a far out-party neighbour. After one
  `apply`, the agent's `affect[other_party]` delta is negative. This is
  the headline sign-fix test — fails if the sign issue creeps back.
- `test_affect_update_skips_same_party_neighbours`: same setup but the
  neighbour is in-party. Affect dict delta is empty.
- `test_affect_update_emits_smaller_coolness_for_close_outparty`: two
  out-party neighbours, one at d=0.1, one at d=1.0. The close
  neighbour's contribution is less cool than the far one's, but still
  negative (baseline ensures it). Locks the "warming is impossible from
  any single encounter" property.

**A4 / A5 — feedback channels.**

- `test_bc_affect_modulator_mutes_hostile_outparty`: build at S2; for
  one agent, manually set affect to a target out-party to -1.0; run one
  tick; compare its `d_ideology` against the same engine with the
  agent's affect at 0.0. The hostile-affect version pulls less toward
  its out-party neighbours.
- `test_tie_rewiring_prefers_to_drop_cold_outparty_ties`: build at S4;
  set one out-party tie to be near (low combined distance) but with
  affect at -1.0; assert that within a few rewire-eligible ticks, it
  is the tie that gets dropped, not an in-party tie at higher combined
  distance.
- `test_affect_weight_zero_is_inert`: full pillar S4 engine with both
  affect-weight params at 0.0 vs. the same engine after a run with the
  default 0.5 / 0.30. The 0.0 case must produce identical positions to
  what Phase 4's S4 produced (bit-identical regression guard — the new
  rule paths must be exact no-ops when the bundle parameters are off).

### 9.2 Modified: `tests/test_pillar_stages.py`

Add one new test, the Iyengar test:

- `test_affect_polarizes_faster_than_ideology`: across `STAGE_SEEDS`,
  compute (a) the magnitude of the change in `affective_polarization`
  from S0→S3 and (b) the change in `ideological_constraint` over the
  same span. Assert |Δaffect| > Δconstraint (in their respective
  units — affect runs in `[-1, 1]`, constraint in `[0, 1]`, both
  changes are dimensionless ratios). The Mason / Iyengar finding made
  testable.

The existing S2 / S3 / S4 tests must still pass with re-blessed thresholds
if Phase 5's feedback channels change magnitudes (likely; measured in §11).

### 9.3 Regression guards

- **Canonical HK suite** — must stay green at the same thresholds.
  `compass_basic` doesn't construct `AffectiveUpdate` and doesn't pass
  `affect_weight` to `BoundedConfidenceInfluence`; defaults are zero.
- **Phase 4 tests** — must all still pass. F2's
  `test_graded_filter_default_is_hard_cutoff` continues to verify
  `temperature == 0.0`; F1's anchor tests are independent of affect.
- **Machinery / determinism tests** — must still pass. Affect is now a
  bigger writer to `d_attrs`, but the merge protocol is unchanged.

---

## 10. Build sequencing

Three slices, each leaving the suite green at the slice's checkpoint.

- **Slice 1 — A1 dynamics rewrite + sign fix.** Rewrite
  `AffectiveUpdate.apply` per §3; add `baseline` to `__init__`; update
  `affective_polarization` docstring; add the three A1 tests. Gate: A1
  tests pass; canonical / machinery / Phase 4 tests still pass.
- **Slice 2 — A4 confidence-filter feedback.** Add `affect_weight` to
  `BoundedConfidenceInfluence.__init__` (default `0.0`); thread the
  modulator into `apply` (§4); update pillar `build_engine` and every
  bundle (§6); add the A4 tests + the bit-identical-when-zero regression
  guard. Gate: A4 tests pass; canonical tests green; Phase 4 tests
  green; the regression guard (`affect_weight=0` is exact no-op) passes.
- **Slice 3 — A5 rewiring feedback + Iyengar test.** Add
  `affect_weight_rewire` to `TieRewiring.__init__` (default `0.0`);
  update its apply (§5); add the A5 test + the Iyengar/Mason test;
  re-bless pillar thresholds per §11. Gate: full suite green.

---

## 11. Re-validation — measure, then bless

After Slice 3 is green, the implementer measures and reports:

1. **A1 sign fix.** At end of S2, S3, S4 (12-seed ensemble): mean
   `affective_polarization`. Today it sits around `+0.0` (probably
   slightly positive — the bug). Phase 5: expect strongly negative at
   S2 and S3 (around `-0.5` to `-0.9`). **S4 may read *less* negative
   than S2/S3** — TieRewiring isolates some agents from out-party
   neighbours, freezing their affect at the seed value (0.0) while
   still-connected agents stay at the clip floor (-1). The population
   mean is then diluted toward zero. This is honest model behaviour
   ("isolation halts animus formation"), not a regression of the sign
   fix. Numbers are first observations, not targets — report and bless.
2. **Iyengar gap.** Compare `|ΔaffectivePolarization|` vs.
   `Δideological_constraint` across S0 → S3. Expect affect to move
   more (Iyengar et al. 2019's headline). Set the test threshold at
   observed gap − a cushion.
3. **A4 modulator effect.** Compare S4 final variance and party
   separation with `affect_weight = 0.3` vs. `affect_weight = 0.0`
   (the no-op regression guard already runs this — report the
   numbers). Confirm the milder 0.3 still produces the intended
   affect→sorting loop: with affect on, cross-party BC pulls are
   muted to ~0.7× and S4's cross-cutting drop / modularity rise
   should both be moderately stronger than Phase 4.
4. **A5 rewiring effect.** Compare cross-cutting tie fraction at S4
   end with `affect_weight_rewire = 0.30` vs. `0.0`. Expect the
   affect-aware rewiring to drop *cross-party* ties faster (because
   they accumulate cold affect), so cross-cutting falls further.
5. **Phase 4 thresholds re-blessed.** S0 drift, S1/S0 ratio, S2-S1
   constraint gap, S3 paired correlation, S4 cross-cutting drop /
   modularity rise, ratchet gap. Affect's feedback into BC and
   TieRewiring will shift these (likely intensifying S4's sorting).
6. **Canonical HK unchanged (sanity).** `compass_basic` has no affect
   attr; canonical tests must pass at the same thresholds.
7. **Final position histogram (Phase 4 §13 carryover).** Confirm the
   "no collapse" property survives — Phase 4 fixed it; Phase 5's
   tighter sorting via the affect channel should not undo F1's work.
   Report the bucket counts as in Phase 4.

Report all seven to the user. **A1 valence formula, A4 affect_weight,
A5 affect_weight_rewire, and the baseline `0.10`** are all modelling
judgments — confirm before committing.

---

## 12. Judgment forks — flagged for explicit confirmation

| ID | Decision | Default | Alternatives |
|----|----------|---------|--------------|
| A1 | Affect valence formula | `-(0.5 * identity_distance + 0.5 * issue_distance + 0.10)` — linear blend with small baseline | (a) `-max(issue_d, identity_d)` (worst dimension dominates); (b) Mason-only: `-identity_d`; (c) no baseline (warming possible from any close encounter) |
| A2 | issue-vs-identity weight | 0.5 / 0.5 split | 0.7 / 0.3 (issue-heavy); 0.3 / 0.7 (Mason-heavy) |
| A3 | Baseline drift | 0.10 | 0.05 (less aggressive); 0.20 (every encounter is significantly cooling); 0.0 (no floor — current rule's structure, but with sign fixed) |
| A4 | BC affect_weight | **0.3** (Vlad-pinned; pillar uses this; rule default stays 0.0) — multiplier `m ∈ [0.7, 1.3]`; mild nudge without cliff behaviour | 0.5 (the draft default; tested but rejected as too cliff-like); 1.0 (a fully-hostile tie pulls at 0% weight — would undo Phase 4's softness gains) |
| A5 | TieRewiring affect_weight_rewire | 0.30 — combined-distance-comparable bias | 0.10 (subtle); 0.50 (dominant) |
| A6 | Stage placement | affect channel on at S2 with `lr = 0.01`, BC/TR weights at S2-S4 | Affect on at S3 (with media); affect always-on like F1 — but S0/S1 have no parties so it would be inert |
| A7 | Asymmetric in-party warmth | no in-party update (Finkel et al. 2020) | Add a symmetric in-party warming term — Mason 2018 suggests in-party warmth is roughly stable, so the omission is principled |

If the user does not override one before implementation begins, the
default is taken.

---

## 13. Supersedes, open items, done checklist

**Supersedes.** Nothing — Phase 5 is additive. The Phase 4 spec's
mention "the affect sign issue belongs to Phase 5" is resolved here.

**Open items (deferred).**

- Affect feeds back into ideology (the Bail backfire mechanism). Phase 6.
- Heterogeneous per-agent `lr` for affect. Phase 7.
- Tick-to-real-time calibration. Phase 7.
- Media-trust modulation via affect. Phase 7 if needed.

**Done checklist.**

- [ ] A1: `AffectiveUpdate` rewritten with corrected sign; `baseline`
      added; the three A1 unit tests pass.
- [ ] A4: `BoundedConfidenceInfluence.affect_weight` exists; rule default
      `0.0`; pillar bundles set 0.0 at S0/S1 and **0.3** at S2-S4; A4 test +
      `affect_weight=0` regression guard pass.
- [ ] A5: `TieRewiring.affect_weight_rewire` exists; rule default `0.0`;
      pillar bundles set 0.0 at S0/S1 and 0.30 at S2-S4; A5 test passes;
      involuntary ties still never rewired.
- [ ] Iyengar test passes: |Δaffective_polarization| > Δideological_constraint
      across S0 → S3.
- [ ] Pillar Phase 4 thresholds re-measured (§11) and re-blessed.
- [ ] Canonical HK suite and Phase 4 tests still pass at the same
      thresholds.
- [ ] Position histogram still shows "no collapse" (Phase 4 §12).
- [ ] Behavioural expectations confirmed: `affective_polarization` is
      negative-going, monotonically through S2-S4; affect outpaces
      ideology.
- [ ] Judgment forks confirmed by the user or noted as defaulted.
- [ ] No UI / website file touched.

With Phase 5 done and signed off, the engine carries two polarization
channels — affective and ideological — that move at different rates and
feed back into each other through the social network. Phase 6 (repulsion
and null levers) then builds on a substrate where "exposure to the other
side increases hostility" can be honestly tested.
