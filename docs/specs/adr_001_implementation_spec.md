# ADR-001 Implementation Spec — Network-Primary Engine Re-Foundation

*Companion to `adr_001_network_primary_engine.md`. ADR-001 is Accepted; this
spec implements its migration path (Steps 1-5). It is an engine re-foundation:
the social network becomes the substrate of influence, ideology space becomes
state + visualization only. No UI/website file is touched.*

*Like the Phase 3 spec, the post-migration thresholds cannot be pre-measured —
the network-primary engine does not exist yet — so Section 13 is a
measure-then-bless gate with human sign-off, not a table of pinned numbers.*

---

## 1. Scope and decisions pinned

| # | Decision |
|---|----------|
| E1 | The `Rule` / `EnvRule` protocol signatures are **unchanged**. Rules that need the network read it from `env.attrs["network"]`; they resolve neighbour ids to `Agent` objects via the standard accessor (Section 5). The `Engine` is **not** modified. |
| E2 | The network is **first-class**: a `Network` class in `abm/core/network.py`, stored at `env.attrs["network"]`. **Every** scenario `build()` and the pillar `build_engine` place one. |
| E3 | `BoundedConfidenceInfluence` becomes **edge-based**. The confidence filter stays a **hard cutoff** (full weight within `epsilon`, zero outside). This spec changes *where* influence flows (along edges), not the *shape* of the filter. The graded / repulsive filter is Phase 4. |
| E4 | Classic Hegselmann-Krause is recovered as the **complete-graph special case**. The canonical scenario builds `Network.complete(...)`; the canonical tests are the rigor gate (Section 10). |
| E5 | `cross_tie_weight` is **removed** — from `BoundedConfidenceInfluence` and from every intervention bundle. Influence is network-mediated by construction, so S4's exposure-narrowing is now structural. **This supersedes the Phase 3 spec §13 addendum** (the soft-gate recalibration) — the soft-gate problem dissolves with the gate. |
| E6 | `ContinuousSpace2D` is **demoted**: the KD-tree and `neighbors_within` are removed. It keeps positions, the agent roster, an id→Agent index, and `clip()`. |
| E7 | The `Network` carries a voluntary/involuntary edge stratum; `TieRewiring` never drops an involuntary edge. Build functions create **zero** involuntary edges for now — the capability ships **inert** (Phase 4 activates it). |
| E8 | Equivalence is validated at the **test level** (canonical thresholds; pillar directional re-validation), **not bit-identical** — neighbour iteration order changes. Neighbours are always iterated in **ascending id order** so runs stay deterministic. |

This spec decides the **substrate only**. Heterogeneous agents, anchoring,
tapered pulls, the affect channel, repulsion/null-levers, and calibration are
Phase 4+ and are out of scope.

---

## 2. Files

```
modify  abm/core/network.py        # add the Network class + neighbor_agents()
modify  abm/core/space.py          # demote: drop KD-tree/neighbors_within; add agents_by_id
modify  abm/rules/influence.py     # BoundedConfidenceInfluence -> edge-based; drop cross_tie_weight
modify  abm/rules/affective_update.py   # neighbour source -> the network
modify  abm/rules/repulsion.py     # neighbour source -> the network
modify  abm/rules/argument_exchange.py  # neighbour source -> the network
modify  abm/rules/tie_rewiring.py  # operate on the Network class; skip involuntary edges
modify  abm/metrics/network.py     # metrics accept a Network
modify  abm/pillars/calm_to_camps.py    # Network.homophilous in build_engine; drop cross_tie_weight from bundles
modify  abm/scenarios/*.py         # every build() places a Network (complete-graph)
create  tests/test_network.py      # Network class unit tests + the HK-equivalence check
modify  tests/test_pillar_stages.py# delete the cross_tie_weight test; rework the ratchet test; re-bless thresholds
modify  tests/conftest.py          # only if a fixture needs the Network type (expected: no change)
```

`abm/core/engine.py`, `abm/core/rules.py`, `tests/test_canonical.py`,
`tests/test_machinery.py` are expected to need **no change** — verify.

`IdentitySorting` is **not** migrated: it references population-level party
groups (Mason mega-identity), not geometric proximity, and reads the roster,
not a radius query. It is left as-is.

---

## 3. The `Network` class (`abm/core/network.py`)

Keep `combined_distance` and `generate_homophilous_network` as they are. Add a
`Network` class wrapping the adjacency, and the `neighbor_agents` accessor
(Section 5).

```python
class Network:
    """The social graph over agent ids — the influence substrate (ADR-001).

    Undirected: j in adj[i] iff i in adj[j]. A subset of edges is
    `involuntary` (kin, workplace) and is exempt from homophilous rewiring.
    Build functions create zero involuntary edges for now — the capability
    is inert until Phase 4.
    """

    def __init__(self, adjacency, involuntary=None):
        self._adj = {i: set(ns) for i, ns in adjacency.items()}
        # involuntary edges as canonical (min_id, max_id) pairs
        self._involuntary = set(involuntary) if involuntary else set()

    # --- constructors ---
    @classmethod
    def complete(cls, node_ids):
        ids = list(node_ids)
        idset = set(ids)
        return cls({i: idset - {i} for i in ids})

    @classmethod
    def homophilous(cls, agents, rng, **kwargs):
        return cls(generate_homophilous_network(agents, rng, **kwargs))

    # --- queries ---
    def neighbors(self, i):
        return self._adj.get(i, set())

    def degree(self, i):
        return len(self._adj.get(i, ()))

    def has_edge(self, i, j):
        return j in self._adj.get(i, ())

    def edges(self):
        """Each undirected edge once, as (i, j) with i < j."""
        for i, ns in self._adj.items():
            for j in ns:
                if j > i:
                    yield (i, j)

    def is_involuntary(self, i, j):
        return (min(i, j), max(i, j)) in self._involuntary

    @property
    def node_ids(self):
        return self._adj.keys()

    @property
    def adjacency(self):
        return self._adj

    # --- mutation (TieRewiring only) ---
    def add_edge(self, i, j, involuntary=False):
        self._adj[i].add(j)
        self._adj[j].add(i)
        if involuntary:
            self._involuntary.add((min(i, j), max(i, j)))

    def remove_edge(self, i, j):
        self._adj[i].discard(j)
        self._adj[j].discard(i)
        self._involuntary.discard((min(i, j), max(i, j)))
```

`Network.complete` is the canonical-mode constructor (Section 10).
`Network.homophilous` wraps the existing generator for the pillar.

---

## 4. `ContinuousSpace2D`, demoted (`abm/core/space.py`)

The space stops being the influence substrate. It becomes a coordinate store,
the agent roster, and an id→Agent index.

- **Remove** the `cKDTree` import, the `_tree` attribute, and `neighbors_within`.
  Nothing should call `neighbors_within` after Section 7 — its removal makes any
  missed caller fail loudly.
- `rebuild(agents)` keeps `_agents` and `_positions`, and **adds**
  `self.agents_by_id = {a.id: a for a in agents}`.
- `clip()`, `bounds`, `_lo`/`_hi` are unchanged.

The `Engine` still constructs and `rebuild`s the space every tick (it holds the
roster the rules resolve ids against); no `Engine` change is needed.

---

## 5. `neighbor_agents` — the standard accessor (`abm/core/network.py`)

One helper, used by every network-mediated rule, so the migration is uniform:

```python
def neighbor_agents(agent, space, env):
    """An agent's network neighbours as Agent objects, ascending id order.
    Ascending order keeps every run deterministic (E8). KeyError if no
    network has been placed in env — every build() must place one (E2)."""
    network = env.attrs["network"]
    roster = space.agents_by_id
    return [roster[j] for j in sorted(network.neighbors(agent.id))]
```

---

## 6. The influence core (`abm/rules/influence.py`)

`BoundedConfidenceInfluence` is rewritten edge-based. It loses `cross_tie_weight`
(E5). The candidate set is the agent's **network neighbours**; among them, it
moves toward the mean of those within ideological distance `epsilon` (the
hard-cutoff filter, E3).

```python
class BoundedConfidenceInfluence:
    """Bounded-confidence attraction, network-mediated (ADR-001).

    The agent is influenced only by its social-network neighbours; among
    those, it shifts a fraction `strength` of the way toward the mean of the
    ones within ideological distance `epsilon`. On a COMPLETE graph this is
    exactly classic Hegselmann-Krause (Section 10) — the network generalizes
    HK, it does not replace it.
    """

    def __init__(self, epsilon: float = 0.3, strength: float = 0.1):
        self.epsilon = epsilon
        self.strength = strength

    def apply(self, agent, space, env, rng):
        if self.strength == 0.0:
            return StateDelta()
        within = [
            n.state.ideology
            for n in neighbor_agents(agent, space, env)
            if np.linalg.norm(agent.state.ideology - n.state.ideology) <= self.epsilon
        ]
        if not within:
            return StateDelta()
        target = np.mean(within, axis=0)
        return StateDelta(d_ideology=self.strength * (target - agent.state.ideology))
```

The only structural change from today's rule: the candidate set is
`neighbor_agents(...)` (the network), not `space.neighbors_within(epsilon)` (the
population). On a complete graph the two are identical sets, so the canonical
behaviour is preserved (Section 10).

---

## 7. The other proximity rules (migration directives)

Each of these rules currently calls `space.neighbors_within(center, R,
exclude_id=agent.id)`. In every case: **replace that call with
`neighbor_agents(agent, space, env)`**; leave the rest of the rule's logic
intact. The radius argument `R` is no longer a query parameter.

- **`AffectiveUpdate`** — neighbour set becomes the network. Keep `self.radius`,
  but only in the valence formula `ideological_sim = 1 - 2*d/radius` as a
  fixed normalisation scale; it is no longer a query radius. **Do not** touch
  the affect sign behaviour — that is a known issue owned by Phase 5.
- **`BacklashRepulsion`** — neighbour set becomes the network. `max_range` is no
  longer a query radius; keep it as an explicit upper cap in the loop
  (`if d <= self.epsilon or d > self.max_range or d < 1e-9: continue`) so the
  ring `[epsilon, max_range]` semantics survive.
- **`ArgumentExchange`** — neighbour set becomes the network;
  `homophily_radius` becomes vestigial (the network already encodes
  homophily). It still picks one neighbour at random — index into the
  `neighbor_agents(...)` list, which is already id-sorted, so the `rng` draw
  stays reproducible.

---

## 8. `TieRewiring` and metrics on the `Network` class

**`TieRewiring`** (`abm/rules/tie_rewiring.py`) currently mutates the raw
adjacency dict. Update it to operate on the `Network`:

- get the network with `env.attrs["network"]`;
- read ties with `network.neighbors(a.id)`, mutate with `network.remove_edge` /
  `network.add_edge`;
- when choosing the tie to drop, consider **only voluntary** ties —
  `[j for j in network.neighbors(a.id) if not network.is_involuntary(a.id, j)]`;
  if an agent has no voluntary tie, skip it.

This keeps `rewire_rate = 0` an exact no-op (S0-S3) and means involuntary
edges, once Phase 4 creates them, are never rewired away.

**Metrics** (`abm/metrics/network.py`) — `cross_cutting_tie_fraction`,
`party_modularity`, `mean_ego_diversity` currently take a raw dict. Update
their signatures to take a `Network`; internally iterate `network.edges()`
(the edge-counting metrics) or `network.neighbors` / `network.adjacency`
(`mean_ego_diversity`). Behaviour is otherwise unchanged.

---

## 9. Scenarios and the pillar

### 9.1 Every scenario build() places a network

All five scenarios (`actb`, `compass_basic`, `elite_dynamics`,
`multi_party_4`, `two_party_sorting`) currently run population-wide /
geometric. Each `build()` adds, into `env.attrs`:

```python
"network": Network.complete(range(n_agents)),
```

A complete graph reproduces their current whole-population behaviour exactly
(Section 10), so no scenario changes its results. This is a one-line edit per
scenario.

### 9.2 The pillar (`abm/pillars/calm_to_camps.py`)

`build_engine` already builds a homophilous adjacency dict with the dedicated
`net_rng`. Change it to construct a `Network`:

```python
network = Network.homophilous(
    agents, net_rng, tau=NET_TAU, p_local=NET_P_LOCAL, p_bridge=NET_P_BRIDGE,
)
```

`social_coord`, the separate `net_rng` (`seed + 9973`), and storing the network
at `env.attrs["network"]` are unchanged.

The superset pipeline drops `cross_tie_weight`:

```python
BoundedConfidenceInfluence(epsilon=0.30, strength=0.0),   # no cross_tie_weight
```

**Bundle edits.** Remove every `("BoundedConfidenceInfluence", "cross_tie_weight", …)`
line from all five interventions. Keep the `("TieRewiring", "rewire_rate", …)`
lines (S0-S3 = `0.0`, S4 = `0.02`). After this, the pillar stages are:

- S0 — network present (static homophilous), all influence strengths 0.
- S1 — bounded-confidence influence on, network-mediated.
- S2 — + party pull.
- S3 — + partisan media.
- S4 — + `TieRewiring` (the network co-evolves and sorts).

S4's "narrows exposure" is now structural: a homophilous network simply has few
cross-party edges, and rewiring deepens that. No gate parameter is involved.

---

## 10. Canonical replication — the rigor gate

Run the edge-based influence rule on `Network.complete(range(n_agents))` and the
candidate set for every agent is every other agent; the `epsilon` hard cutoff
then selects exactly the agents within `epsilon`; the mean over them is the
classic Hegselmann-Krause update. Classic bounded confidence is therefore a
*configuration* of the new engine.

`compass_basic.build` places a complete-graph `Network` (Section 9.1), so
`tests/test_canonical.py` needs **no change** — it exercises the new path
through the existing fixtures. The three canonical tests — loose-`epsilon`
consensus, tight-`epsilon` fragmentation, monotonicity in `epsilon` — are the
**hard gate**: they must pass before Slice 4 begins. If they do not, the
re-foundation has changed the canon and is wrong.

Equality is at the test-threshold level, not bit-identical (E8): neighbour
iteration order changes from KD-tree order to id order, perturbing floating-point
means at the ULP level. The canonical tests are threshold assertions with wide
margins and are robust to this.

---

## 11. Tests

- **`tests/test_canonical.py`** — unchanged. The rigor gate (Section 10).
- **`tests/test_machinery.py`** — expected to pass unchanged (determinism holds:
  id-sorted iteration; the bundles still apply cleanly). Verify; do not edit
  unless a failure proves a real regression.
- **`tests/test_network.py` (new)** — `Network` unit tests: `complete(n)` gives
  every node degree `n-1`; `homophilous(...)` is symmetric with the expected
  mean degree; `add_edge`/`remove_edge`/`edges()`/`is_involuntary` behave;
  plus an **HK-equivalence test** — a small population under edge-based BC on a
  complete graph produces the same clustering verdict (consensus vs fragmented)
  as the canonical expectation.
- **`tests/test_pillar_stages.py`** —
  - **delete `test_cross_tie_weight_1_is_inert`** — the parameter no longer exists;
  - `test_s4_narrows_exposure` keeps its shape (metrics now take a `Network`);
  - **rework `test_s4_is_a_ratchet`** — the release experiment can no longer
    toggle `cross_tie_weight`. Re-express it on the substrate: polarise through
    S4, then release (drop party pull and media, reopen `epsilon`); **World A**
    keeps its evolved homophilous network, **World B** has its network replaced
    by a homophily-free random graph of matched mean degree. World A stays
    apart, World B re-merges — the ratchet is now "structure," exactly as the
    ADR intends;
  - all S0-S4 numeric thresholds are re-measured and re-blessed in Slice 4.

---

## 12. Build sequencing

Four slices; each leaves a runnable artifact. This implements ADR-001 Steps 1-5
(Step 5's tie-strata capability is folded into Slices 1-2, shipped inert).

- **Slice 1 — the `Network` class.** Section 3 + `neighbor_agents` (Section 5) +
  `tests/test_network.py`. The engine is not yet wired to it. Gate: new tests
  pass; the full existing suite still passes (nothing in the engine path
  changed).
- **Slice 2 — migrate to network-primary.** Demote the space (Section 4);
  rewrite `BoundedConfidenceInfluence` (Section 6); migrate `AffectiveUpdate`,
  `BacklashRepulsion`, `ArgumentExchange` (Section 7); migrate `TieRewiring` and
  the metrics (Section 8); every `build()` places a network and the pillar
  drops `cross_tie_weight` (Section 9). Gate: the engine runs end-to-end without
  error and `test_machinery.py` passes (determinism). Canonical and pillar
  thresholds are **not** expected to be re-blessed yet.
- **Slice 3 — RIGOR GATE.** Run `tests/test_canonical.py`. The three HK phase
  tests must pass. **No further step proceeds until this is green.**
- **Slice 4 — re-validate the pillar.** Run the measure-then-bless procedure
  (Section 13); update the `test_pillar_stages.py` thresholds; delete and rework
  the two tests named in Section 11. Gate: the full suite is green and the
  re-validation is signed off.

---

## 13. Re-validation — measure, then bless

The network-primary pillar runs S1-S3 on a homophilous network (local, not
population-wide, consensus), so the Phase 1-3 measured thresholds will move.
After Slice 3 is green, the implementer measures and reports, for the pillar at
the test `N` / `TICKS` / seed ensemble:

1. **Network shape.** Mean degree of the homophilous pillar network — confirm it
   still lands ~6-10; report the degree distribution.
2. **S0** — variance drift over the run (expect < ~5%; baseline is inert).
3. **S1** — final variance vs S0 (expect a clear fall: local consensus still
   reduces global variance).
4. **S2** — ideological constraint vs S1 (expect a rise).
5. **S3** — paired correlation of diet extremity with radial change vs S2
   (expect > 0).
6. **S4** — cross-cutting tie fraction (expect a fall) and party modularity
   (expect a rise) over the run; and the reworked ratchet gap (World A vs
   World B separation).

Report all six to the user. The **qualitative directions must hold** — if any
direction flips (e.g. S1 no longer reduces variance, or the homophilous network
fragments the society before party pull can sort it), that is a finding to
surface, not a number to paper over. Once the directions are confirmed and the
magnitudes reported, the new test thresholds are set at (observed value − a
safety cushion), the Phase 1 §9 discipline, and committed.

---

## 14. Supersedes, open items, done checklist

**Supersedes.** The Phase 3 spec §13 addendum (soft-gate recalibration) is
mooted — `cross_tie_weight` is gone. The measured thresholds in the Phase 1/2/3
specs are superseded by Section 13. The staged-pillar *design* of those specs
survives. `pillar_engine_roadmap.md` and the phase specs still need the
documentation revision pass (ADR-001 action item 7) — that is separate from
this implementation.

**Open items (deferred, not in this spec).** The graded / repulsive confidence
filter; heterogeneous agents and anchoring; activating the involuntary tie
stratum; media as first-class nodes; calibrating the network generator to
empirical degree/clustering statistics. All are Phase 4+.

**Done checklist.**

- [ ] `Network` class + `neighbor_agents`; `test_network.py` passes.
- [ ] `ContinuousSpace2D` demoted; `neighbors_within` and the KD-tree removed;
      `agents_by_id` added.
- [ ] `BoundedConfidenceInfluence` edge-based; `cross_tie_weight` gone from the
      rule and from all five bundles.
- [ ] `AffectiveUpdate`, `BacklashRepulsion`, `ArgumentExchange` migrated to
      `neighbor_agents`.
- [ ] `TieRewiring` and the network metrics operate on the `Network`; involuntary
      edges are never rewired.
- [ ] Every scenario `build()` and the pillar place a `Network`;
      `compass_basic` uses `Network.complete`, the pillar `Network.homophilous`.
- [ ] RIGOR GATE: `test_canonical.py` passes in complete-graph mode.
- [ ] Pillar re-validated (Section 13), thresholds re-blessed, `test_pillar_stages.py`
      updated; full suite green.
- [ ] `show_pillar.py` still runs both modes (it is already network-aware).
- [ ] No UI/website file touched.

With this done, the engine is network-primary: influence flows along social
ties, ideology space is state and visualization, and Hegselmann-Krause survives
as the complete-graph special case. Phase 4 — the realism core — then builds on
a substrate that no longer fights it.
