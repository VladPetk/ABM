# Phase 4 Implementation Spec — Realism Core

*The first phase to run on the network-primary engine (ADR-001 is implemented;
25 tests are green). Phase 4's job is to make the polarized end-state look
like a real society instead of a bi-pole collapse: most agents barely move,
some involuntary ties cross party lines, and the confidence filter responds
graded rather than as a step function.*

*Like Phase 3 and the ADR-001 impl-spec, the post-change thresholds cannot be
fully pre-measured — every mechanism here changes the dynamics. §13 is a
measure-then-bless gate with human sign-off, not a table of pinned numbers.*

---

## 1. Scope and decisions pinned

Three new mechanisms, all on the network-primary substrate. No new engine
seam — every change lives inside existing rule classes or extends the build
function.

| # | Decision | Choice |
|---|----------|--------|
| F1 | **Anchored agents (Friedkin-Johnsen stubbornness).** Each agent carries `anchor` (an ideology vector) and `stubbornness` (a scalar in `[0, 1]`). Every rule that moves ideology applies the FJ blend at the apply site: the rule's intended ideology delta is multiplied by `(1 - stubbornness)`, then an anchor-pull `α * stubbornness * (anchor - ideology)` is added where `α` is a fixed FJ rate held on a new env attr. `α` is set in `build_engine` from a single constant, not a rule. Stubbornness distribution: a **Beta(2, 5) mean ≈ 0.286** — most agents anchored, a long thin tail of movers. Anchors are seeded at build from initial ideology (so the population looks unchanged at t=0; the anchor is "where this person started"). |
| F2 | **Graded confidence filter (pillar-only).** `BoundedConfidenceInfluence` gains a new attribute `temperature`. With `temperature = 0.0` (the **default**, used by `compass_basic` and every existing scenario) the rule is bit-identical to today's hard cutoff at `epsilon` — so the canonical HK replication test is automatically a literal HK replication, with no fallback path. The **pillar** opts in by constructing the rule with `temperature = 0.05` in `build_engine` and carrying `("BoundedConfidenceInfluence", "temperature", 0.05)` in every bundle. With `temperature > 0` the rule applies a **smooth logistic weighting** of each network neighbour: `w(d) = 1 / (1 + exp((d - epsilon) / temperature))`. At `d = 0` weight ≈ 1; at `d = epsilon` weight = 0.5; at `d >> epsilon` weight → 0. The weighted mean of all network neighbours replaces today's mean over the in-cutoff subset. **No repulsion in Phase 4** — negative weights belong to Phase 6 (`BacklashRepulsion` already exists for that). |
| F3 | **Involuntary cross-cutting tie stratum.** Build creates a fixed share of **involuntary** edges between agents of different parties — exempt from `TieRewiring`. Share: a per-agent target of `involuntary_per_agent = 2`, pinned to Mutz (2006)'s ~20% total cross-cutting-discussion-tie share via a §13 measure-then-bless gate: the implementer reports t=0 cross-cutting fraction and confirms it lands in the **18-25%** target band; drop to `1` if observed > 30% (involuntary stratum overwhelms homophily and the ratchet effect dissolves), bump to `3` if observed < 15% (Mutz's headline figure undershot). Generation: uniform random across cross-party pairs that are not already connected. The capability shipped inert in ADR-001 impl-spec (E7); this activates it. Bundle change: a single new build-time knob, not a per-rule knob, so this is **not** a parameter in any `Intervention` bundle — every stage sees the same involuntary edges. |

The above three together address the "real societies don't collapse" problem:
F1 prevents the collapse by anchoring the bulk of the population; F3 ensures a
visible minority of cross-party connections survive S4; F2 softens the
fragmentation cascade so clusters bleed into each other rather than freezing.

**Out of scope.**

- Affect as a first-class channel (Phase 5).
- Repulsion / null levers and backfire effects (Phase 6).
- Tick-to-real-time calibration (Phase 7).
- A separate `TaperedPull` rule — the briefing explicitly excludes it; the
  FJ blend (F1) already tapers every pull rule uniformly.
- Heterogeneous `epsilon` per agent — F1 alone is enough for Phase 4's
  "fix the overshoot" goal; per-agent `epsilon` is deferred to Phase 7
  calibration if needed.

---

## 2. Files

```
modify  abm/core/state.py              # AgentState gains anchor convention (no class change — anchor is in attrs)
modify  abm/pillars/calm_to_camps.py   # seed anchor + stubbornness + α + involuntary edges in build_engine
modify  abm/rules/influence.py         # graded filter; FJ blend at apply site
modify  abm/rules/party_pull.py        # FJ blend at apply site
modify  abm/rules/media_consumption.py # FJ blend at apply site
modify  abm/rules/noise.py             # FJ blend at apply site (anchor pull only added by one rule — see §4)
modify  abm/core/network.py            # generate_involuntary_edges helper
modify  abm/metrics/network.py         # cross_cutting_tie_fraction reads the involuntary stratum (no behavioural change; doc only)
create  tests/test_phase4.py           # F1/F2/F3 unit + directional tests
modify  tests/test_pillar_stages.py    # re-bless S1-S4 thresholds; do NOT change the canonical / machinery suites
modify  tests/conftest.py              # add stubbornness fixtures if needed
```

`abm/core/engine.py`, `abm/core/rules.py`, `abm/pillars/intervention.py`,
`abm/pillars/pillar.py`, `tests/test_canonical.py`, `tests/test_network.py`,
`tests/test_machinery.py` are expected to need **no change** — verify.

---

## 3. F1 — Anchored agents (Friedkin-Johnsen stubbornness)

### 3.1 Per-agent state

Two new entries in `AgentState.attrs`, seeded once at build time:

| Key | Type | Generation |
|-----|------|------------|
| `anchor` | `np.ndarray` shape `(2,)` | A copy of the agent's initial `ideology` vector. *Rationale:* "where this person started" matches Friedkin-Johnsen's "innate position" cleanly, requires no extra parameter, and keeps the t=0 population unchanged. |
| `stubbornness` | `float` in `[0, 1]` | `rng.beta(2.0, 5.0)`. Mean ≈ 0.286, mode ≈ 0.18, with a thin tail past 0.7. *Rationale:* the empirical pattern (Friedkin 1999; Cohen-Coch et al.) is that most people anchor strongly to their starting view and a minority move freely. Beta(2, 5) gives exactly that shape without a per-population calibration step. |

**Decision (judgment fork F1a):** stubbornness is drawn from `Beta(2, 5)`.
The shape is a modelling choice — alternatives are Beta(2, 2) (symmetric,
mean 0.5, no anchoring tail) and Beta(5, 2) (most agents anchored, very few
free movers). Beta(2, 5) is the middle option and matches the literature's
"most people barely move" language. Flagged for confirmation.

**Decision (judgment fork F1b):** the anchor is the agent's **initial
ideology**, fixed forever. Alternative: anchor = party centre (the FJ
"innate position" interpreted as a deep partisan disposition). Initial
ideology is preferred because (i) it makes t=0 invariant to F1 (the test
suite's S0 regression guard stays meaningful) and (ii) it carries no implicit
claim about *which* anchor matters most — that question is a Phase 7
calibration call. Flagged for confirmation.

### 3.2 The FJ blend at the apply site

The Friedkin-Johnsen model writes opinion update as

```
x_{t+1} = (1 - s) * (rule's intended next position) + s * anchor
```

In rule terms, that decomposes into:

- **Scale the rule's intended `d_ideology` by `(1 - stubbornness)`** — a
  stubborn agent moves less in response to any pull.
- **Add an anchor pull** `α * stubbornness * (anchor - ideology)` —
  a stubborn agent decays back toward its anchor.

To keep the rule pipeline order-independent (every rule contributes one
`StateDelta` per agent, the engine sums them), the anchor pull is added by
**exactly one** rule — `GaussianNoise` (it already runs every tick, even at
S0; it is the only rule guaranteed to be active in every stage). The other
ideology-moving rules each only apply the `(1 - stubbornness)` scaling. This
keeps the FJ recurrence faithful: the anchor pull contributes once per tick
regardless of how many other rules fire.

**`α` (the anchor-pull rate)** is held at `env.attrs["fj_alpha"]`, set in
`build_engine` to `0.05` (the same order as the other pull strengths). It is
not in any `Intervention` bundle — F1 is always on; turning it off would
require deleting the env attr or setting stubbornness to 0, both deliberately
awkward to ensure F1 cannot be silently switched off in a stage.

**Per-rule changes.** Each ideology-moving rule wraps its existing
`d_ideology` output:

```python
# At the end of each apply():
s = float(agent.state.attrs.get("stubbornness", 0.0))
return StateDelta(d_ideology=(1.0 - s) * d_ideology, ...)
```

Rules affected: `BoundedConfidenceInfluence`, `PartyPull`, `MediaConsumption`,
`BacklashRepulsion`, `ArgumentExchange`. **Not** affected: `AffectiveUpdate`
(does not move ideology), `IdentitySorting` (does not move ideology),
`EliteDrift` (moves party centres, not agent ideology), `TieRewiring`
(structural).

**`GaussianNoise` only** also adds the anchor pull. Pseudocode:

```python
def apply(self, agent, space, env, rng):
    if self.sigma <= 0:
        # Anchor pull still fires even when noise is off — F1 is structural.
        s = float(agent.state.attrs.get("stubbornness", 0.0))
        alpha = float(env.attrs.get("fj_alpha", 0.0))
        anchor = agent.state.attrs.get("anchor")
        if alpha == 0.0 or s == 0.0 or anchor is None:
            return StateDelta()
        return StateDelta(d_ideology=alpha * s * (anchor - agent.state.ideology))
    noise = rng.normal(0.0, self.sigma, size=2)
    s = float(agent.state.attrs.get("stubbornness", 0.0))
    alpha = float(env.attrs.get("fj_alpha", 0.0))
    anchor = agent.state.attrs.get("anchor")
    if alpha == 0.0 or s == 0.0 or anchor is None:
        return StateDelta(d_ideology=(1.0 - s) * noise)
    return StateDelta(d_ideology=(1.0 - s) * noise + alpha * s * (anchor - agent.state.ideology))
```

The `(1 - s) * noise` term keeps Brownian motion proportionate to mobility —
stubborn agents jitter less, which is correct under the FJ interpretation.

### 3.3 The seeding step

In `build_engine`, immediately after the agent attrs are populated (before
`social_coord` is added), inside the existing main-RNG loop:

```python
attrs["stubbornness"] = float(rng.beta(2.0, 5.0))
attrs["anchor"] = pos.copy()
```

`fj_alpha` is set in the env construction:

```python
env = Environment(attrs={..., "fj_alpha": 0.05, ...})
```

`fj_alpha = 0.05` and the Beta(2, 5) shape are the F1 **judgment forks** (see
§14). The implementer measures the resulting effect in §13.

---

## 4. F2 — Graded confidence filter

### 4.1 The rule change

`BoundedConfidenceInfluence` keeps `epsilon` and `strength`; adds
`temperature` defaulting to **`0.0`** (the canonical hard cutoff). The
default is `0.0` deliberately: every existing scenario (`compass_basic`,
`actb`, etc.) is unaffected, so the canonical HK replication test runs
genuine Hegselmann-Krause with no special handling. The pillar
explicitly opts into the graded filter by constructing the rule with
`temperature = 0.05` in `build_engine` and carrying that value in every
intervention bundle.

```python
class BoundedConfidenceInfluence:
    def __init__(self, epsilon=0.30, strength=0.1, temperature=0.0):
        self.epsilon = epsilon
        self.strength = strength
        self.temperature = temperature

    def apply(self, agent, space, env, rng):
        if self.strength == 0.0:
            return StateDelta()
        neighbours = neighbor_agents(agent, space, env)
        if not neighbours:
            return StateDelta()
        my_ide = agent.state.ideology
        if self.temperature <= 0.0:
            # Canonical hard cutoff (the default; HK replication path).
            within = [n.state.ideology for n in neighbours
                      if np.linalg.norm(my_ide - n.state.ideology) <= self.epsilon]
            if not within:
                return StateDelta()
            target = np.mean(within, axis=0)
        else:
            # Graded logistic filter (pillar opt-in, Phase 4).
            ds = np.array([np.linalg.norm(my_ide - n.state.ideology) for n in neighbours])
            ws = 1.0 / (1.0 + np.exp((ds - self.epsilon) / self.temperature))
            wsum = ws.sum()
            if wsum < 1e-9:
                return StateDelta()
            positions = np.array([n.state.ideology for n in neighbours])
            target = (ws[:, None] * positions).sum(axis=0) / wsum
        d = self.strength * (target - my_ide)
        s = float(agent.state.attrs.get("stubbornness", 0.0))
        return StateDelta(d_ideology=(1.0 - s) * d)
```

### 4.2 Why a logistic, not a triangular kernel

A logistic is symmetric in log-odds, has one shape parameter (`temperature`),
and recovers the hard cutoff smoothly as `temperature → 0`. A triangular
kernel `max(0, 1 - d / epsilon)` would also taper but does so linearly and
has no natural softness knob. The logistic was picked because the regression
guard "`temperature = 0` = hard cutoff" is exact, which keeps the canonical
HK test honest if we ever want to dial F2 off.

### 4.3 Default value and pillar opt-in

`temperature = 0.0` is the **rule default** — the canonical hard cutoff,
unchanged from today. Every existing scenario constructs
`BoundedConfidenceInfluence(epsilon=..., strength=...)` without a
`temperature` argument, so they all inherit the canonical behaviour and
the canonical HK replication test is genuine HK with no fallback path.

The pillar opts in explicitly:

- `build_engine` constructs the rule with `temperature = 0.05`.
- Every intervention bundle (S0-S4) carries
  `("BoundedConfidenceInfluence", "temperature", 0.05)`, so applying any
  stage's bundle sets the graded filter even on a freshly-built engine
  that happened to be at the default — the absolute-bundle discipline
  (Phase 1 D5).

**Decision (judgment fork F2a):** `temperature = 0.05` is a starting value
("about a sixth of `epsilon`"). The measure-then-bless gate (§13) confirms
the resulting cross-cutting edges still carry non-trivial weight at the
homophilous-network society's final state.

### 4.4 Canonical HK test is unaffected

Because `temperature` defaults to `0.0`, `compass_basic` and every other
scenario run literal hard-cutoff Hegselmann-Krause with no code change
beyond adding the new attribute. The canonical HK suite
(`test_canonical.py`) and the network-class HK-equivalence tests
(`test_network.py`) keep their existing thresholds. The implementer
verifies this in Slice 2 of §10 but no fallback is needed.

---

## 5. F3 — Involuntary cross-cutting tie stratum

### 5.1 Generation

After `Network.homophilous(...)` constructs the voluntary graph, generate
`involuntary_per_agent * n_agents / 2` cross-party edges uniformly at random
across cross-party agent pairs not already connected. The edges are added
with `involuntary=True` so `TieRewiring` (which already filters
`is_involuntary`) never touches them.

```python
def generate_involuntary_edges(network, agents, rng, per_agent=2):
    """Add cross-party involuntary edges (kin, workplace — Mutz & Mondak 2006).
    Targets ``per_agent`` edges per agent on average; the actual count per
    agent varies because edges are sampled uniformly without per-agent
    rejection sampling (keeps generation O(target) and reproducible)."""
    target = (per_agent * len(agents)) // 2
    by_party = {}
    for a in agents:
        by_party.setdefault(a.state.attrs["party"], []).append(a.id)
    parties = list(by_party)
    if len(parties) < 2:
        return
    placed = attempts = 0
    while placed < target and attempts < 20 * target:
        attempts += 1
        p, q = rng.choice(parties, size=2, replace=False)
        i = int(rng.choice(by_party[p]))
        j = int(rng.choice(by_party[q]))
        if network.has_edge(i, j):
            continue
        network.add_edge(i, j, involuntary=True)
        placed += 1
```

Generation uses the existing `net_rng` (the `seed + 9973` stream) so the
main RNG is undisturbed — same discipline as Phase 3 §3.

### 5.2 Build wiring

In `build_engine`, after `Network.homophilous(...)`:

```python
INVOLUNTARY_PER_AGENT = 2
generate_involuntary_edges(network, agents, net_rng, per_agent=INVOLUNTARY_PER_AGENT)
```

### 5.3 Why not a per-stage bundle parameter

Involuntary ties are a property of the population, not a strength to dial.
"Kin and workplace exist" applies to S0 the same as S4. Making it a build-
time constant makes the cross-cutting baseline a known property of the
society we are simulating — and it means the S4 ratchet test is sharper
(World A keeps these ties; World B's random graph does not, so the contrast
isolates *what the structure does*, not "did we hand-construct different
cross-cutting baselines").

**Decision (judgment fork F3a):** `involuntary_per_agent = 2`. With `n = 250`
that's 250 involuntary edges, against a typical voluntary edge count of
~2000 (mean degree ~16; F2 increases the homophilous-network mean degree
because near neighbours now also have positive weight, but the generator
itself is unchanged). So involuntary ties are ~10% of the graph. Mutz &
Mondak (2006) found roughly a third of Americans' political discussion
partners are involuntary; we set it lower because (a) Mutz's number is
political discussion, not all ties, and (b) at 33% the involuntary stratum
overwhelms the homophilous one and S4's structural effect disappears. Two
per agent is a conservative starting point — flagged for confirmation; §13
measures whether it leaves S4's ratchet effect intact.

---

## 6. Pillar wiring

### 6.1 Bundles

Every bundle gains the `temperature` line for `BoundedConfidenceInfluence`.
Bundle pattern after F2 (S1 shown — every other stage follows the same
pattern). Every bundle carries the same `temperature = 0.05` line so that
the pillar's graded filter is on at every stage, including S0 (where
`strength = 0` makes the rule a no-op anyway — but the absolute-bundle
discipline says every tunable is listed, Phase 1 D5):

```python
param_bundle=(
    ("GaussianNoise", "sigma", 0.01),
    ("BoundedConfidenceInfluence", "epsilon", 0.30),
    ("BoundedConfidenceInfluence", "strength", 0.08),
    ("BoundedConfidenceInfluence", "temperature", 0.05),
    ...
)
```

S0's bundle: same `temperature = 0.05` (inert because `strength = 0`).

**No bundle parameter for F1 or F3** — both are build-time constants,
deliberately not per-stage. The bundles are unchanged except for the
`temperature` line.

### 6.2 Build constants

In `calm_to_camps.py` at module level:

```python
# Phase 4 — realism core
FJ_ALPHA = 0.05
STUBBORNNESS_ALPHA, STUBBORNNESS_BETA = 2.0, 5.0
INVOLUNTARY_PER_AGENT = 2
BC_TEMPERATURE = 0.05    # pillar opt-in; rule's own default is 0.0 (canonical HK)
```

### 6.3 The S4 stage stays a ratchet

The structural ratchet (`test_s4_is_a_ratchet`) is sharper after F1/F3:

- F1 means the bulk of agents barely moved between S0 and S4, so the
  "polarized end-state" is now visibly less extreme than the bi-pole — but
  the ratchet test compares World A and World B, not absolute separation,
  so it is unchanged in shape.
- F3 means cross-cutting ties are now structural (not just statistical), so
  World A's cross-cutting fraction has a floor (the involuntary stratum).
  This is the realism payoff: even a sorted echo chamber has *some*
  cross-party ties. The ratchet metric is the **gap** between worlds, which
  survives.

Test thresholds are re-measured in §13.

---

## 7. The other rules

The FJ scaling at the apply site is applied uniformly to ideology-moving
rules. The pattern in each:

```python
# party_pull.py
def apply(self, agent, space, env, rng):
    if self.strength == 0:
        return StateDelta()
    party = agent.state.attrs.get("party")
    parties = env.attrs.get("parties", {})
    if party is None or party not in parties:
        return StateDelta()
    target = parties[party]
    s_id = float(agent.state.attrs.get("identity_strength", 0.5))
    d = self.strength * s_id * (target - agent.state.ideology)
    s = float(agent.state.attrs.get("stubbornness", 0.0))
    return StateDelta(d_ideology=(1.0 - s) * d)
```

Repeated for `MediaConsumption`, `BacklashRepulsion`, `ArgumentExchange`.
`GaussianNoise` also adds the anchor pull (§3.2). No structural changes —
no new rule classes, no engine seam change, no `Intervention` field
additions.

---

## 8. Metrics

### 8.1 No changes to existing metrics

`cross_cutting_tie_fraction` already counts every edge regardless of
voluntariness — that is correct (involuntary cross-cutting ties *count* as
cross-cutting exposure). `party_modularity` likewise. No code change here.

### 8.2 One new helper for tests

```python
# abm/metrics/network.py
def involuntary_tie_count(network) -> int:
    """How many involuntary edges are in the graph (Phase 4 F3 diagnostic)."""
    return sum(1 for (i, j) in network.edges() if network.is_involuntary(i, j))
```

Used by `test_phase4.py` to assert F3's seeding worked and to confirm
involuntary edges are *not* dropped after a long S4 run (`TieRewiring`'s
involuntary-skip behaviour, which already exists, is re-validated under the
new code path).

---

## 9. The tests

### 9.1 New: `tests/test_phase4.py`

Six tests, organised by feature.

**F1 — anchored agents.**

- `test_stubborn_agent_barely_moves`: build a one-off engine with two
  agents — stubbornness 0.95 and stubbornness 0.05 at the same starting
  ideology — and a strong S1 force. Run TICKS. Assert the high-stubbornness
  agent moved < 25% of the distance the low-stubbornness agent did. (The
  exact ratio is `(1 - 0.95) / (1 - 0.05) ≈ 0.053`; the assertion margin is
  loose because the anchor pull also runs.) Pin a measured threshold in
  §13.

- `test_anchor_pull_recovers_displaced_agent`: build with one agent shifted
  away from its anchor (cheat-edit `ideology` after build), strength = 0,
  noise = 0, FJ on. Run TICKS. Assert the agent drifted back toward
  `anchor` — i.e. final distance to anchor < starting distance to anchor,
  monotonically. This is the FJ self-consistency check.

**F2 — graded filter.**

- `test_graded_filter_default_is_hard_cutoff`: construct
  `BoundedConfidenceInfluence(epsilon=0.3, strength=0.08)` (no `temperature`
  arg) and confirm `rule.temperature == 0.0` and the rule takes the
  hard-cutoff branch — the canonical default. Then build two pillar
  engines: one at S1 with `temperature = 0.0` (canonical), one at S1 with
  `temperature = 0.05` (pillar default). Run TICKS; assert their final
  positions **differ** (graded filter has visible effect) but neither
  diverges or NaNs. This locks the default to canonical behaviour and
  documents that the pillar opt-in is non-trivial.

- `test_graded_filter_pulls_proportionally`: a hand-built two-agent setup
  where both agents are equidistant from a target at distance `epsilon +
  delta`. With the old hard cutoff their target weight is exactly 0; with
  the graded filter at `temperature = epsilon / 4` and `delta = epsilon`,
  the agent moves toward the target measurably. Pure unit test of the
  weight formula.

**F3 — involuntary stratum.**

- `test_involuntary_edges_are_seeded`: build at S0 with the default constants,
  assert `involuntary_tie_count(network) > 0` and roughly equals
  `n_agents * INVOLUNTARY_PER_AGENT / 2 ± 10%`.

- `test_involuntary_edges_are_all_cross_party`: every involuntary edge joins
  agents of different `party`. Direct check via `network.edges()` plus
  `is_involuntary`.

- `test_involuntary_edges_survive_rewiring`: build at S4, run TICKS, assert
  every involuntary edge present at t=0 is still present at t=TICKS. (Tests
  that `TieRewiring`'s involuntary-skip works on the activated stratum.)

### 9.2 Re-blessed: `tests/test_pillar_stages.py`

Every existing pillar threshold is measured against the new substrate in
§13. The structural tests (S0 no-drift, S1 variance falls, S2 constraint
rises, S3 paired correlation positive, S4 cross-cutting falls + modularity
rises, ratchet gap > margin) all stand qualitatively — F1 dampens
magnitudes, F2 softens transitions, F3 adds a structural floor on
cross-cutting ties. Expect:

- **S0:** unchanged (no force on; F1's anchor pull at `s = 0.286` mean,
  `α = 0.05` is small enough to land within the 5% drift band — measured).
- **S1:** the variance drop is smaller than today (stubborn agents do not
  converge). Threshold likely needs to relax from < 0.92 of S0 to < 0.97 or
  so — measured.
- **S2:** constraint still rises with `PartyPull` — but more slowly because
  the bulk of agents are anchored near their starting positions. Gap likely
  shrinks from +0.04 to ~+0.02. Measured.
- **S3:** the paired correlation between diet extremity and radial change
  survives (it is the differential effect, not the level); margin likely
  stable at > 0.35. Measured.
- **S4:** cross-cutting drop is now bounded below by the involuntary stratum
  (~10% of edges are structurally cross-cutting), so the absolute drop
  is smaller. Modularity rise is smaller. **Expect the > 0.10 thresholds to
  need relaxing**, probably to > 0.05. Measured.
- **Ratchet:** gap remains comfortably positive. F1 makes both worlds
  converge less in the release phase, so World B's "re-merge" is slower —
  but the *gap* between worlds is what the test measures, and the gap is
  driven by structure, which F1 does not undo. Margin likely stable at
  `> 0.10–0.15`. Measured.

### 9.3 Untouched: `tests/test_canonical.py`, `tests/test_network.py`, `tests/test_machinery.py`

The canonical HK suite stays green at the same thresholds automatically:
`temperature` defaults to `0.0` so `compass_basic` (and the HK-equivalence
tests in `test_network.py`) run literal hard-cutoff HK with no edit. The
machinery suite tests determinism and idempotence — both still hold (F1's
seeding uses the existing main RNG stream; F3's seeding uses the existing
`net_rng` stream).

**Verify, do not edit.**

---

## 10. Build sequencing

Three slices, each leaving the test suite passing on the slice's portion of
the spec. The full re-bless of the pillar thresholds happens at the end of
Slice 3, after all three mechanisms are present.

- **Slice 1 — F1, anchored agents.** Add `stubbornness` / `anchor` /
  `fj_alpha` to `build_engine`; add the `(1 - s)` scaling to each
  ideology-moving rule; add the anchor pull to `GaussianNoise`. Re-bless
  S0–S4 thresholds. Gate: the full suite still passes; F1's two unit tests
  pass; the canonical HK tests still pass (F1 does not affect
  `compass_basic` because that scenario has no `stubbornness` attr —
  `stubbornness = 0.0` is the default, the rule is a no-op).
- **Slice 2 — F2, graded filter (pillar-only).** Add `temperature` to
  `BoundedConfidenceInfluence` with default `0.0` (canonical). Pillar
  `build_engine` and every bundle opt in to `0.05`. Gate:
  `test_graded_filter_*` pass; canonical HK + network-equivalence tests
  still pass at the same thresholds (automatic — defaults are unchanged
  behaviourally); re-bless pillar thresholds.
- **Slice 3 — F3, involuntary stratum.** Add `generate_involuntary_edges`
  and wire it into `build_engine`. Gate: `test_involuntary_*` pass; re-bless
  pillar thresholds; full suite green.

---

## 11. Regression guards (the "did not silently break the engine" suite)

These are tests that **must** pass after every slice. They are the cheapest
way to catch any of F1/F2/F3 breaking a previously-passing invariant.

1. **Canonical HK suite** at the same thresholds. (§4.4 and §10 Slice 2.)
2. **`test_machinery.py`** unchanged — determinism, idempotence, the
   apply_intervention error cases.
3. **`test_graded_filter_default_is_hard_cutoff`** — inside the new test
   module but functions as a regression guard against F2's default
   silently drifting away from the canonical hard cutoff.
4. **`test_s0_baseline_no_organized_motion`** — F1's anchor pull cannot push
   S0 variance outside the 5% noise band (if it does, `α = 0.05` is too
   high; recalibrate).

If any of these fail at any slice boundary, **stop and report** — do not
patch around them.

---

## 12. Behavioural expectations (the qualitative claims F1/F2/F3 make)

These are not test assertions — they are what the implementer reports to the
user after Slice 3 so the human gate (§13) can sign off on whether the
realism objective was actually achieved.

- **F1 fixes the overshoot.** S4 ends with a polarized society that is
  *clearly* less extreme than today's two-tiny-blobs — the position
  histograms should show heavy tails toward the centre instead of two
  delta spikes near the party centroids. The party-separation metric at
  end-of-S4 should be measurably smaller than today's ~1.0+ values.
- **F2 smooths the fragmentation cascade.** S4 still sorts the network
  (cross-cutting fraction falls, modularity rises), but the transition is
  more gradual — there is no "tipping tick" at which the graph splits, and
  some cross-party network edges retain positive weight throughout.
- **F3 floors cross-cutting exposure.** After any S4 run the network still
  carries the involuntary stratum's ~10% cross-party edges; eyeballing the
  edge plot, the two camps are connected by a visible minority of edges
  rather than perfectly disjoint.
- **The story still works.** S0–S3 still produce a *recognisable*
  polarization arc (variance falls, constraint rises, heavy media-diet
  consumers extremize); S4 still acts as a ratchet (World A vs. World B
  gap remains clear). The realism additions soften and ground the pillar
  without dissolving its story.

---

## 13. Re-validation — measure, then bless

After Slice 3 is green, the implementer measures and reports, for the
pillar at the test `N`, `TICKS`, `STAGE_SEEDS` ensemble:

1. **F1 effect on S0.** Run S0 with F1 on. Report variance drift over
   TICKS. Expect within the 5% band; if not, `fj_alpha` is too high.
2. **F1 effect on S1.** Report S1 final variance vs. S0. Expect the
   variance still falls (qualitative direction holds), but by less than
   today's ~0.83 ratio. Pin the new threshold at observed value + a 0.05
   cushion.
3. **Canonical HK suite is untouched (sanity check, not calibration).**
   The rule defaults to `temperature = 0.0`, so `compass_basic` and the
   network-class equivalence tests run literal HK. Confirm both suites
   pass at the same thresholds; if they do not, F1's anchor-pull constant
   has leaked into a non-pillar code path (no agent in `compass_basic`
   has a `stubbornness` attr, so the `(1 - s)` and anchor terms are
   no-ops — this is the contract). Report and fix if violated.
4. **F2 effect on the pillar.** Report variance, constraint, and ratchet
   gap with F2 on (`temperature = 0.05`) vs. F2 off (`temperature = 0.0`,
   recovering Phase 3 pillar behaviour). They should be in the same
   ballpark; if F2 catastrophically changes any direction, surface it.
5. **F3 effect on the network — the calibration gate.** At t=0, report
   mean cross-cutting tie fraction. Target band **18-25%** (Mutz 2006
   ~20% headline figure ± a few points). If observed > 30%, the
   involuntary stratum overwhelms homophily and the ratchet effect will
   not survive — drop `INVOLUNTARY_PER_AGENT` to `1` and re-measure. If
   observed < 15%, Mutz's headline figure is undershot — bump to `3` and
   re-measure. At t=TICKS@S4, report cross-cutting fraction again
   (expect a floor near the involuntary share). Confirm the
   involuntary-edge count is unchanged after the run (`TieRewiring`'s
   involuntary-skip is doing its job). Pin `INVOLUNTARY_PER_AGENT` at
   the value that landed in band and commit.

   **Outcome (2026-05-25):** per_agent=2 produced t=0 cross-cutting
   0.390 (above the 0.30 ceiling). Dropped to per_agent=1, measured
   0.305 — still ~5 points above the spec's tight band but at the
   per_agent floor (per_agent=0 would remove F3 entirely and defeat its
   purpose). Accepted at 1: the S4 ratchet effect is robust (0.305 →
   0.143 cross-cutting drop; 0.191 → 0.352 modularity rise; 0.279
   World-A-vs-B release gap), and the S4 end-state cross-cutting of
   0.143 is plausibly *below* Mutz's contemporary-US ~0.20 figure
   (suggesting rewiring rate is slightly aggressive — a Phase 7
   calibration concern, not F3's).
6. **Re-blessed pillar thresholds.** Report final-S1 variance, S1/S0
   ratio, S2-S1 constraint gap, S3 paired correlation mean, S4 cross-
   cutting drop, S4 modularity rise, ratchet gap. Pin every new threshold
   at observed value − a cushion (the Phase 1 §9 discipline) and commit.
7. **Position histogram, S4 end-state.** A qualitative readout (the
   numbers) of the final-tick position distribution: peak counts, tail
   counts, fraction within 0.2 of party centroid, fraction within 0.2 of
   the centre. The "real societies don't collapse" check.

Report all seven to the user before thresholds are committed. This is the
**human-in-the-loop gate**: at least F1a/F1b, F2a/F2b, and F3a are modelling
judgments that the agent should not bless alone.

---

## 14. Judgment forks — flagged for explicit confirmation

These are the decisions in this spec that are modelling judgment, not code
correctness. The implementer **must not** silently change them mid-build.

| ID | Decision | Default | Alternatives |
|----|----------|---------|--------------|
| F1a | Stubbornness distribution | `Beta(2, 5)` (mean ≈ 0.286, most agents anchored, thin tail of movers) | Beta(2, 2) symmetric; Beta(5, 2) very stubborn; Uniform(0, 1) flat |
| F1b | Anchor seeding | initial ideology (FJ "innate position" = where you started) | party centre (innate position = deep partisan disposition); fixed identity centroid |
| F1c | FJ anchor-pull rate `α` | 0.05 (same order as other pulls; S0 stays within noise band) | 0.02 (gentler, less restorative); 0.10 (stronger anchor) |
| F2a | Confidence filter shape | logistic with `temperature = 0.05` | triangular kernel (no softness knob); Gaussian (heavier tails) |
| F3a | Involuntary tie share | `INVOLUNTARY_PER_AGENT = 2`, pinned to a t=0 cross-cutting target of ~20% (Mutz 2006). §13 confirms in 18-25% band; drop to 1 if >30%; bump to 3 if <15%. | 1 per agent (~5%); 4 per agent (~20%); a population-share parameter instead of per-agent |
| F3b | Involuntary stratum activation | always on at every stage (not bundle-controlled) | bundle-controlled, off at S0–S3 and on at S4 — but this would invalidate the ratchet-test interpretation |

Each fork is also called out at its definition above. If the user does not
override one before implementation begins, the default is taken.

---

## 15. Supersedes, open items, done checklist

**Supersedes.** Nothing — Phase 4 is purely additive. ADR-001 impl-spec
§§7-9 stand; Phase 1-3 specs stand; only the pillar's measured numeric
thresholds (test_pillar_stages.py) are re-blessed in Slice 3.

**Open items (deferred, not in this spec).**

- **Heterogeneous `epsilon` per agent** — possible Phase 7 calibration item.
- **Heterogeneous `α` per agent** — Phase 7. Current spec uses a single
  global FJ rate; per-agent variation does not add explanatory power beyond
  per-agent `stubbornness`.
- **Anchor decay** — a slow drift of `anchor` toward current ideology
  (long-timescale belief updating). Phase 7 if it turns out to matter.
- **`AffectiveUpdate` sign** — a known issue owned by Phase 5; Phase 4 does
  not touch it.
- **Repulsion / null levers** — Phase 6.

**Done checklist.**

- [ ] F1: `stubbornness` and `anchor` seeded in `build_engine`; `fj_alpha`
      in env.attrs; every ideology-moving rule applies `(1 - s)` scaling;
      `GaussianNoise` adds the anchor pull. F1 unit tests pass.
- [ ] F2: `BoundedConfidenceInfluence.temperature` exists; rule default
      `0.0` (canonical); pillar `build_engine` and every bundle opt in
      to `0.05`; default-is-hard-cutoff test passes; canonical HK suite
      stays green automatically.
- [ ] F3: `generate_involuntary_edges` exists; `build_engine` calls it;
      `INVOLUNTARY_PER_AGENT` lands in {1, 2, 3} per §13 calibration band;
      F3 unit tests pass; involuntary edges survive a full S4 run.
- [ ] Pillar thresholds re-measured (§13) and pinned with cushion; test
      suite green.
- [ ] Behavioural expectations (§12) confirmed by the implementer in the
      Slice 3 report.
- [ ] No UI/website file touched.
- [ ] Judgment forks (§14) confirmed by the user or noted as defaulted.

With F1+F2+F3 done and signed off, the engine carries a society that
*doesn't* collapse into two tiny blobs: the polarization arc is still
visible, but the bulk of agents stay near where they started, some
cross-party ties survive structurally, and the confidence filter responds
in degrees rather than as a wall. The substrate is then realistic enough for
Phase 5 (affect as a first-class channel) to ride on top.
