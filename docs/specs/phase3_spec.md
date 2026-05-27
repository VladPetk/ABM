# Phase 3 Implementation Spec — S4, the Co-evolving Homophilous Network

*Companion to `phase3_design.md` (the five S4 decisions) and
`s4_network_research.md` (the evidence). S4 is the one stage that changes the
engine rather than assembling on it. Unlike the Phase 1 and 2 specs, thresholds
cannot be pre-measured here — the network code does not exist yet — so §11
specifies the calibration procedure and a human sign-off gate instead.*

---

## 1. Decisions pinned (the review)

| # | Decision | Choice |
|---|----------|--------|
| D1-D5 | model-level | as `phase3_design.md` §1 — co-evolving; ideology + separate social dimension; soft gate; fixed social coord + slow rewiring; pluggable exposure. |
| E1 | Where the network is built | In `build_engine`, using a **separate RNG** (`default_rng(seed + 9973)`). The main build RNG stream is untouched, so S0-S3 populations stay bit-identical and the Phase 1/2 measured thresholds do not move. |
| E2 | How S4 activates | **No `setup` hook.** The network and `social_coord` are pre-built and inert; `BoundedConfidenceInfluence.cross_tie_weight = 1.0` makes the gate transparent. S4 is a pure parameter bundle, exactly like S1-S3 — it flips `cross_tie_weight` and `rewire_rate`. |
| E3 | The BC refactor | `BoundedConfidenceInfluence` becomes exposure-aware with a `cross_tie_weight == 1.0` fast path that is **bit-identical** to today's plain-mean rule. |
| E4 | Bundle invariant | All five interventions' bundles gain the two new tunables (absolute-bundle rule, phase1 D5). S0-S3 carry the inert values `1.0` / `0.0`. |
| E5 | The rewiring rule | `TieRewiring` is an `EnvRule`, added to `env_rules` at `rewire_rate = 0` (an exact no-op for S0-S3). |

---

## 2. Files

```
create  abm/core/network.py        # adjacency type, homophilous generator, combined_distance
create  abm/rules/tie_rewiring.py   # the TieRewiring EnvRule
create  abm/metrics/network.py      # cross-cutting fraction, party-modularity, ego diversity
modify  abm/rules/influence.py      # exposure-aware BoundedConfidenceInfluence
modify  abm/pillars/calm_to_camps.py# social_coord + network in build_engine; S4; bundle edits
modify  abm/metrics/__init__.py     # export the three network metrics
modify  tests/conftest.py           # network test helpers
modify  tests/test_pillar_stages.py # S4 tests + the inertness regression guard
```

---

## 3. The social coordinate

Each agent gains `social_coord` — a fixed scalar in [-1, 1], a latent "social
position." Added to `build_engine` **after** the existing agent loop, using the
separate RNG (E1) so the main stream is undisturbed:

```python
net_rng = np.random.default_rng(seed + 9973)
SOCIAL_BIAS, SOCIAL_NOISE = 0.30, 0.30
for a in agents:
    sign = -1.0 if a.state.attrs["party"] == 0 else 1.0
    a.state.attrs["social_coord"] = float(np.clip(
        sign * SOCIAL_BIAS + net_rng.normal(0.0, SOCIAL_NOISE), -1.0, 1.0))
```

Partly party-correlated, partly random. **Never updated by any rule** — its
fixedness is what anchors the network (the ratchet).

---

## 4. The tie network (`abm/core/network.py`)

Adjacency as `dict[int, set[int]]`, symmetric (`j in net[i]  iff  i in net[j]`),
stored at `env.attrs["network"]`.

```python
def combined_distance(a, b, w_ideo=1.0, w_soc=1.0) -> float:
    d_ideo = float(np.linalg.norm(a.state.ideology - b.state.ideology))
    d_soc  = abs(a.state.attrs["social_coord"] - b.state.attrs["social_coord"])
    return w_ideo * d_ideo + w_soc * d_soc

def generate_homophilous_network(agents, rng, *, w_ideo=1.0, w_soc=1.0,
                                 tau=0.40, p_local=0.55, p_bridge=0.002):
    """Edge probability decays with combined ideology+social distance,
    plus a tiny distance-independent bridge term."""
    net = {a.id: set() for a in agents}
    for i in range(len(agents)):
        for j in range(i + 1, len(agents)):
            d = combined_distance(agents[i], agents[j], w_ideo, w_soc)
            p = min(1.0, p_local * np.exp(-d / tau) + p_bridge)
            if rng.random() < p:
                net[agents[i].id].add(agents[j].id)
                net[agents[j].id].add(agents[i].id)
    return net
```

Generated in `build_engine` with the **same** `net_rng` as §3, after
`social_coord` is set. `tau` / `p_local` are calibrated to a mean degree of
~6-10 (§11); `p_bridge` seeds a handful of long-range "bridge" ties.

---

## 5. Exposure-aware `BoundedConfidenceInfluence` (`abm/rules/influence.py`)

The rule still gathers geometric neighbours within `epsilon`; the **pull target
becomes the exposure-weighted mean**. New attribute `cross_tie_weight`, default
`1.0`.

```python
def apply(self, agent, space, env, rng):
    neighbors = space.neighbors_within(agent.state.ideology, self.epsilon,
                                       exclude_id=agent.id)
    if not neighbors:
        return StateDelta()
    network = env.attrs.get("network")
    if network is None or self.cross_tie_weight == 1.0:
        target = np.mean([n.state.ideology for n in neighbors], axis=0)   # FAST PATH
    else:
        ties = network.get(agent.id, ())
        w = np.array([1.0 if n.id in ties else self.cross_tie_weight
                      for n in neighbors])
        if w.sum() == 0.0:
            return StateDelta()                       # gated agent, no ties in range
        target = np.average([n.state.ideology for n in neighbors], axis=0, weights=w)
    return StateDelta(d_ideology=self.strength * (target - agent.state.ideology))
```

The `cross_tie_weight == 1.0` branch takes the **identical `np.mean` code path**
as today — so S0-S3 are provably unchanged (guarded by a test, §9). S4 sets
`cross_tie_weight` low: tie-neighbours pull at full weight, non-tied neighbours
at the residual.

---

## 6. The `TieRewiring` rule (`abm/rules/tie_rewiring.py`)

An `EnvRule` — it mutates the network (world state). Each tick, each agent with
probability `rewire_rate` drops its most ideologically-distant tie and forms a
new one biased toward low combined distance. Degree stays ~constant.

```python
class TieRewiring:
    def __init__(self, rewire_rate=0.0, w_ideo=1.0, w_soc=1.0, n_candidates=10):
        ...
    def apply(self, env, agents, space, rng, tick):
        if self.rewire_rate <= 0:
            return
        net = env.attrs.get("network")
        if net is None:
            return
        by_id = {a.id: a for a in agents}
        for a in agents:
            if rng.random() > self.rewire_rate:
                continue
            ties = net[a.id]
            if not ties:
                continue
            # drop the most ideologically-distant current tie
            drop = max(ties, key=lambda j: combined_distance(a, by_id[j],
                                                             self.w_ideo, self.w_soc))
            net[a.id].discard(drop); net[drop].discard(a.id)
            # add a tie to the closest of n_candidates random non-neighbours
            pool = [x for x in agents
                    if x.id != a.id and x.id not in net[a.id]]
            if not pool:
                continue
            cand = [pool[k] for k in rng.integers(0, len(pool), self.n_candidates)]
            new = min(cand, key=lambda x: combined_distance(a, x,
                                                            self.w_ideo, self.w_soc))
            net[a.id].add(new.id); net[new.id].add(a.id)
```

Added to `env_rules` alongside `EliteDrift`. `rewire_rate` is the memory knob:
low = ties lag far behind opinion (strong ratchet).

---

## 7. New metrics (`abm/metrics/network.py`)

```python
def cross_cutting_tie_fraction(agents, network) -> float:
    """Share of edges joining agents of different party."""
    party = {a.id: a.state.attrs.get("party") for a in agents}
    cross = total = 0
    for i, nbrs in network.items():
        for j in nbrs:
            if j > i:
                total += 1
                if party[i] != party[j]:
                    cross += 1
    return cross / total if total else 0.0

def party_modularity(agents, network) -> float:
    """Modularity Q of the network under the party partition.
    Q = sum_c [ L_c/m - (D_c/2m)^2 ]."""
    party = {a.id: a.state.attrs.get("party") for a in agents}
    deg   = {i: len(nbrs) for i, nbrs in network.items()}
    m = sum(deg.values()) / 2.0
    if m == 0:
        return 0.0
    L, D = {}, {}
    for i, nbrs in network.items():
        c = party[i]
        D[c] = D.get(c, 0) + deg[i]
        for j in nbrs:
            if j > i and party[j] == c:
                L[c] = L.get(c, 0) + 1
    return sum(L.get(c, 0) / m - (D[c] / (2 * m)) ** 2 for c in D)

def mean_ego_diversity(agents, network) -> float:
    """Per-agent share of cross-party ties, averaged over agents with >=1 tie."""
    party = {a.id: a.state.attrs.get("party") for a in agents}
    vals = []
    for i, nbrs in network.items():
        if nbrs:
            vals.append(sum(party[j] != party[i] for j in nbrs) / len(nbrs))
    return float(np.mean(vals)) if vals else 0.0
```

Export all three from `abm/metrics/__init__.py`.

---

## 8. The S4 Intervention and bundle edits (`calm_to_camps.py`)

The superset pipeline gains `TieRewiring()` in `env_rules`. **Every** bundle
gains the two new tunables (E4). S0-S3 add the inert pair:

```python
("BoundedConfidenceInfluence", "cross_tie_weight", 1.0),
("TieRewiring", "rewire_rate", 0.0),
```

S4 is S3's bundle with those two flipped on:

```python
S4_HOMOPHILOUS_NETWORK = Intervention(
    id="S4_homophilous_network",
    label="Homophilous network",
    description="People are influenced through a homophilous social network "
                "that rewires slowly; cross-cutting exposure narrows.",
    label_kind="illustrative",
    citation="McPherson et al. 2001; Mutz 2006; Kan, Porter & Mason 2023",
    predicted_effect="Cross-cutting ties fall and the sorted state becomes "
                     "sticky (a ratchet) — amplification, not creation.",
    param_bundle=(
        ("GaussianNoise", "sigma", 0.01),
        ("BoundedConfidenceInfluence", "epsilon", 0.30),
        ("BoundedConfidenceInfluence", "strength", 0.08),
        ("PartyPull", "strength", 0.04),
        ("AffectiveUpdate", "lr", 0.01),
        ("MediaConsumption", "strength", 0.04),
        ("IdentitySorting", "sort_rate", 0.0),
        ("EliteDrift", "rate", 0.0),
        ("BoundedConfidenceInfluence", "cross_tie_weight", 0.10),  # soft gate
        ("TieRewiring", "rewire_rate", 0.02),                      # slow co-evolution
    ),
    setup=None,
)

PILLAR = Pillar(..., interventions=(S0_BASELINE, S1_BOUNDED_CONFIDENCE,
                                    S2_PARTY_IDENTITY, S3_PARTISAN_MEDIA,
                                    S4_HOMOPHILOUS_NETWORK))
```

`cross_tie_weight = 0.10` and `rewire_rate = 0.02` are starting values to be
calibrated (§11).

---

## 9. The tests (`tests/test_pillar_stages.py`)

**test_cross_tie_weight_1_is_inert** — the regression guard. Build at S1, run
`TICKS`, assert the final variance equals the Phase 1 measured value (~0.533)
to tight tolerance. If the exposure-aware refactor perturbed the fast path,
this fails. (The whole Phase 1/2 suite must also still pass — that is the
broader guarantee.)

**test_s4_narrows_exposure** — build at S4, record `cross_cutting_tie_fraction`
and `party_modularity` at t=0 and after `TICKS`. Assert cross-cutting fraction
falls and modularity rises across the ensemble. (Co-evolution rewiring homophily
should hollow out cross-party ties.)

**test_s4_is_a_ratchet** — the headline, a paired release experiment:

```
for seed in STAGE_SEEDS:
    # polarise two identical worlds through S3
    engA = build_at_stage(PILLAR, 3, seed); engA.run(TICKS)
    engB = build_at_stage(PILLAR, 3, seed); engB.run(TICKS)   # identical state
    # release: drop the polarising forces, restore open-mindedness
    for eng, gate in ((engA, 0.10), (engB, 1.0)):
        set PartyPull.strength = 0, MediaConsumption.strength = 0
        set BoundedConfidenceInfluence.epsilon = 1.5      # wide open again
        set BoundedConfidenceInfluence.cross_tie_weight = gate
        set TieRewiring.rewire_rate = (0.02 for A, 0.0 for B)
        eng.run(RELEASE_TICKS)
    sepA = party_separation(engA); sepB = party_separation(engB)
assert mean(sepA) > mean(sepB) + margin
```

The story it encodes: when open-mindedness returns, world B (no gate) lets the
two camps re-merge; world A's homophilous network keeps them apart. That is
"amplifies, does not create" made into a test. `party_separation` = distance
between the two parties' mean positions; `margin` is measured in §11.

All positional tests use the Phase 2 `positional_engine` fast path
(`AffectiveUpdate.lr = 0`, still bit-identical) and the shared-ensemble fixture.

---

## 10. Build sequencing

Even though the end state is co-evolving (D1), build it in two slices so there
is always a runnable artifact:

- **3a — static slice.** `social_coord`, `abm/core/network.py`, the
  exposure-aware BC, `abm/metrics/network.py`, the bundle edits, the S4
  intervention with `rewire_rate = 0`. S4 now runs on a *fixed* network.
  Validate `test_cross_tie_weight_1_is_inert` and `test_s4_narrows_exposure`
  (the static network still narrows exposure via the gate), and a static-network
  ratchet.
- **3b — co-evolution.** Add `TieRewiring`, set `rewire_rate = 0.02`. Validate
  the full `test_s4_is_a_ratchet` and the fragmentation behaviour.

---

## 11. Calibration — measure, then bless (the human gate)

The network code does not exist yet, so unlike Phases 1-2 the thresholds are
**not** pre-measured. The implementer measures them during the build and you
sign off. Procedure:

1. **Network generation.** Tune `tau` / `p_local` so mean degree lands in
   6-10; report the degree distribution.
2. **The gate.** With the static network, sweep `cross_tie_weight`; pick the
   value where S4's `cross_cutting_tie_fraction` is clearly below S3's but the
   society does not freeze solid. Report S3-vs-S4 cross-cutting fraction and
   modularity.
3. **Co-evolution.** Sweep `rewire_rate`; pick the slowest rate that still
   produces a visible fragmentation over the run (slow = strong ratchet).
4. **The ratchet margin.** Run `test_s4_is_a_ratchet`'s release experiment;
   report `sepA` and `sepB`; set the test `margin` at (observed gap − a safety
   cushion), the Phase 1 §9 discipline.

Report all four to the user before the thresholds are committed. This is a
genuine human-in-the-loop checkpoint — the calibration is a modelling judgment,
not a number an agent should bless alone.

---

## 12. Done checklist

- [ ] `social_coord` + the homophilous network built in `build_engine` via the
      separate RNG; Phase 1/2 tests still pass bit-identically.
- [ ] `BoundedConfidenceInfluence` exposure-aware; `cross_tie_weight = 1.0`
      proven inert by `test_cross_tie_weight_1_is_inert`.
- [ ] `TieRewiring` rule; `abm/core/network.py`; `abm/metrics/network.py`.
- [ ] All five bundles carry the two new tunables; `S4_HOMOPHILOUS_NETWORK`
      added; `PILLAR.interventions` has five stages.
- [ ] Three S4 tests pass; calibration (§11) measured and signed off.
- [ ] `pytest` green across the whole suite.
- [ ] `show_pillar.py` shows five stages with no edit (`stages` and `journey`).
- [ ] No UI/website file touched.

With S4 done and green, the engine has one full validated pillar — the
roadmap's definition of done. Phase 4 (hardening) and then the product/UI work
follow.

---

## 13. Addendum (2026-05-25) — keep the soft gate, recalibrate the release test

*This addendum supersedes the `cross_tie_weight` value in §8's S4 bundle and the
`epsilon = 1.5` step in §9's `test_s4_is_a_ratchet`. Everything else in the spec
stands. It follows an assessment of the first Phase 3 build.*

### 13.1 Why

The first build set `cross_tie_weight = 0.0` (a hard gate) because the spec's
soft-gate value (`0.10`) "leaked" during the release test. The leak was real but
it was an artefact of §9's release step, not of the gate. §9 reopens bounded
confidence to `epsilon = 1.5`; at that radius almost every agent is an in-range
neighbour, so ~240 non-tie neighbours at weight `0.10` swamp ~6 tie neighbours
at weight `1.0`. epsilon and the gate are **coupled** — maximising epsilon
mathematically forces the gate toward `0`. D3's soft gate and §9's release
design were never compatible.

The resolution is to keep the soft gate (D3 is a genuine modelling decision) and
fix the release test, not the model. Choosing release epsilon by "as wide as
possible" is the wrong principle. "Open-minded again" does not mean "willing to
average toward the most extreme opposite" — it means willing to listen across a
meaningful range. The release epsilon should be the **smallest** value at which
the *ungated* world reliably re-merges. At that epsilon the in-range non-tie
count is modest and a true soft gate has real bite.

This is also the stronger test. A hard gate makes the ratchet near-tautological
(if you only ever hear your own camp, of course you stay apart). The soft-gate
version shows the real claim: even when agents are open-minded enough that they
*would* merge absent a network, and even when they *do* still hear the other
side (attenuated), the homophilous structure alone keeps the camps apart.

### 13.2 The change

**S4 bundle (§8).** `cross_tie_weight` returns to a soft value — start at
`0.10`. The hard-gate `0.0` is retired. At S4's own `epsilon = 0.30` the leak
does not occur (the in-range non-tie count is modest), so the soft gate has bite
during S4 proper.

```python
("BoundedConfidenceInfluence", "cross_tie_weight", 0.10),  # soft gate (D3)
("TieRewiring", "rewire_rate", 0.02),
```

**`_release_run` (§9).** Replace the fixed `epsilon = 1.5` with a calibrated
`RELEASE_EPSILON`. World A keeps the S4 bundle's soft gate; world B sets the
gate to `1.0` (gate off):

```python
elif name == "BoundedConfidenceInfluence":
    r.epsilon = RELEASE_EPSILON      # calibrated, not maximised
    r.cross_tie_weight = gate        # A: soft (0.10); B: 1.0
```

`test_s4_is_a_ratchet` calls world A with `gate = 0.10, rewire = 0.02` and
world B with `gate = 1.0, rewire = 0.0`.

**Unaffected.** `test_s4_narrows_exposure` measures network *structure* (driven
by `TieRewiring`), independent of `cross_tie_weight` — no change.
`test_cross_tie_weight_1_is_inert` and S0-S3 are unaffected; `cross_tie_weight`
only ever differs from `1.0` in the S4 bundle.

### 13.3 Calibration (extends §11)

Two numbers to measure and bless, in order:

5. **Release epsilon.** Sweep `RELEASE_EPSILON` over e.g. `{0.6, 0.8, 1.0, 1.2}`.
   For each, run **world B only** (gate `1.0`, `rewire 0`) across `STAGE_SEEDS`
   and record mean `party_separation`. Pick the smallest epsilon at which world
   B reliably collapses — mean sep `< 0.05`, every seed clearly merging — then
   round up one step as a cushion. If world B does not collapse at any tested
   epsilon, stop and report it: the release design needs rethinking.

6. **Ratchet margin.** With `RELEASE_EPSILON` fixed, run the full paired
   experiment (world A soft gate, world B gate off). Report `sepA`, `sepB`, and
   the gap. Set `RATCHET_MARGIN = gap − cushion`.

Expect a smaller gap than the hard gate's ~0.52-vs-0.00. A soft gate should let
world A drift somewhat closer — a *partial* hold (e.g. `sepA ~0.25-0.40`) is
acceptable and is the more accurate result, provided the gap clears a meaningful
margin.

If the soft gate at `0.10` does not hold — world A also re-merges, leaving no
usable gap — the implementer may lower `cross_tie_weight` toward `0.05`, but
**not** to `0.0`: it must stay an audible soft gate. Any value below `0.10` is a
reported deviation, not a silent one.

### 13.4 Sign-off

Report `RELEASE_EPSILON`, the final `cross_tie_weight`, `sepA`, `sepB`, the gap,
and `RATCHET_MARGIN` to the user before committing — the §11 human-in-the-loop
gate. The gate value and the release epsilon are modelling judgments, not
numbers an agent blesses alone.
