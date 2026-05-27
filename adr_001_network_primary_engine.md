# ADR-001: The social network as the primary influence substrate

**Status:** Proposed — to be accepted before Phase 4 begins
**Date:** 2026-05-25
**Deciders:** Vlad (project owner)
**Supersedes, in part:** the *substrate assumptions* of `pillar_engine_roadmap.md`
and the Phase 1-3 specs — their measured thresholds, not their staged-pillar
design.

---

## 1. Context

polarlab is being built as an accurate, detailed, realistic simulation of
political polarization — a microfoundation honest enough to teach the public
from. Its subject matter is, specifically, *social structure*: echo chambers,
homophily, cross-cutting ties, partisan sorting.

The engine today represents each agent as a point in a 2D ideology space (the
economic x cultural "compass", [-1, 1]^2) and drives influence by **geometric
proximity**: `BoundedConfidenceInfluence` gathers every agent within ideological
distance `epsilon` and moves the agent toward their mean. The social network,
added in S4 (Phase 3), is a *gate* layered on top of that geometric query — it
attenuates influence, it does not carry it.

This couples two things that should be separate. An agent's position is doing
**two jobs**:

1. **Representing what the agent believes.** Legitimate — ideology is the state
   variable, and the compass is the right place to hold it.
2. **Determining who interacts with whom.** Not legitimate. "You influence me
   iff you are within `epsilon` of me" asserts that everyone in the population
   who happens to think like you automatically influences you. In reality
   influence flows through *social ties*: a like-minded stranger has no effect,
   a disagreeing brother-in-law has a large one. Ideological similarity is an
   *input* to influence — it shapes who you befriend (homophily) and how much
   you discount a friend who disagrees (bounded confidence as a psychological
   filter) — but it is not the *channel*.

The forces at play:

- **Scientific fidelity.** A model whose influence mechanism is geometric
  proximity cannot honestly represent network phenomena. It *defines* an echo
  chamber ("you are connected to people you think like") in terms of the thing
  it is meant to explain. That circularity is real, and is the likely reason
  the S4 results felt unconvincing.
- **The patchwork signal.** Every Phase 4 realism item — cross-divide influence
  ("decouple influence from proximity"), sticky involuntary ties, the S4 gate
  itself — is a *symptom* of one mismatch: the network is subordinate to
  geometry when it should be the substrate. Continuing to patch treats
  symptoms.
- **Rigor must be preserved.** The project's canonical-replication discipline
  (the Hegselmann-Krause phase tests) cannot be sacrificed.
- **Sunk, correct work.** Phase 1-3 produced a sound engine *design* — the
  `Rule`/`EnvRule` protocols, the `RulePipeline`, the `Intervention`/`Pillar`
  superset-and-dial architecture, and the network machinery (`network.py`, the
  homophilous generator, `TieRewiring`, the network metrics). Not all of this
  is at stake.
- **Timing.** No UX has been built. The cost of changing the substrate rises
  monotonically with every subsequent phase and every product surface laid on
  top.

---

## 2. Decision

Re-found the engine so that **a social network is the primary substrate of
influence**. Concretely:

- Ideology space (the 2D compass) is demoted to exactly one job: holding agent
  state and supporting visualization. It is no longer queried to decide who
  influences whom.
- A first-class **social network** (a graph) becomes the influence substrate.
  Influence flows along edges, and only along edges.
- **Bounded confidence becomes a graded filter on edge-level influence** — "how
  much does a tie who disagrees with me still move me" — rather than a
  definition of who is heard. At the far end of disagreement the filter may
  invert into repulsion.
- **Homophily shapes the graph**, not influence directly: ties form and rewire
  toward similarity, so ideology shapes *who you are connected to* over time —
  the real causal path.
- The network is the substrate **from S0 onward**, not an S4 addition. The
  "superset pipeline, strengths as the dial" staging is preserved unchanged; it
  simply runs on a graph.
- **Classic Hegselmann-Krause is preserved as the complete-graph special
  case** (Section 7) — the canonical replication remains valid.

This ADR decides *the substrate only*. It does **not** decide the Phase 4
realism mechanisms (heterogeneous agents, tapered pulls, the affect channel,
calibration). Those become easier once the substrate is right, and are
specified separately.

---

## 3. Formal grounding

The decision is not a leap into unstudied territory. It moves the engine onto
the better-established of the two main formal traditions in opinion dynamics.

- **Bounded confidence / geometric** (Hegselmann & Krause 2002; Deffuant et al.
  2000) — influence gated by opinion distance, classically computed mean-field
  over the whole population. This is what the engine is built on today.
- **Network-based averaging** (DeGroot 1974, "Reaching a Consensus"; Friedkin &
  Johnsen 1990s) — influence flows over a social network of weighted ties.
  Friedkin-Johnsen adds a per-agent **"stubbornness"** term: each agent's
  opinion is a blend of its neighbours' opinions and its own innate position.
- **Empirical political-network research** (Huckfeldt & Sprague 1995,
  *Citizens, Politics, and Social Communication*; Mutz 2006, *Hearing the
  Other Side*) — the *substantive* finding that political influence in
  US democracies travels through social ties (discussion partners, kin,
  workplace), not through abstract ideological proximity. DeGroot/FJ
  supply the mathematical form; the political-network tradition supplies
  the empirical case that the network IS where political influence
  actually flows. **Provenance note (Phase 8c D1):** earlier drafts of
  this ADR cited DeGroot/FJ alone, which gives the *form* but not the
  empirical *substance*. Mutz and Huckfeldt-Sprague are the political-
  science anchors and are now stated alongside.

The current engine sits entirely in the first tradition. The re-foundation
adopts a **synthesis** that is itself a well-studied class — bounded confidence
*on a network*: a homophilous, co-evolving graph as the substrate, with the
confidence threshold acting as an edge-level filter.

Two consequences worth stating now. First, the synthesis *contains*
Hegselmann-Krause as a special case (Section 7), so nothing is given up.
Second, the Friedkin-Johnsen "stubbornness" term is exactly the per-agent
**anchor** that Phase 4 needs for heterogeneous agents — on the new substrate,
anchoring stops being a patch and becomes a native, canonically-grounded model
parameter.

---

## 4. Options considered

### Option A — Status quo: geometric proximity primary, keep patching

Keep the geometric-proximity influence rule; the network remains an S4 gate;
Phase 4 proceeds as patches that work around the substrate.

| Dimension | Assessment |
|-----------|------------|
| Complexity (now) | Low — no engine change |
| Migration cost | Zero now; compounding later |
| Scientific fidelity | Poor — influence mechanism contradicts the project's subject |
| Canonical replication | Preserved (it is the current basis) |
| Reuse of Phase 1-3 work | Full |
| Risk | High — incoherence accumulates; UX gets built on a known-wrong substrate |

**Pros:** no immediate work; pillar stays validated as-is; canonical tests
untouched.
**Cons:** the influence mechanism is circular for network phenomena; every
realism feature is a patch fighting the substrate; the cost of a later
correction grows with every phase and every UX surface.

### Option B — Network-primary re-foundation, migrating the existing engine *(recommended)*

Promote the network to the primary substrate; rewrite the influence core to be
edge-based; keep the `Rule`/`EnvRule`/`Pillar`/`Intervention` design, the
network machinery, and the staged pillar; re-validate.

| Dimension | Assessment |
|-----------|------------|
| Complexity (now) | Medium — a contained rewrite of the influence core |
| Migration cost | One-time: influence-rule rewrite + full pillar re-validation |
| Scientific fidelity | High — influence flows the way it does in reality |
| Canonical replication | Preserved via the complete-graph special case (Section 7) |
| Reuse of Phase 1-3 work | High — design, machinery and staging survive; only thresholds move |
| Risk | Medium, front-loaded — paid once, now, while the project is small |

**Pros:** the substrate matches the subject matter; Phase 4 items become native
properties, not patches; sits on the DeGroot-Friedkin-Johnsen tradition; HK
retained as a special case; most prior work survives.
**Cons:** the influence core is rewritten; every Phase 1-3 measured threshold
must be re-measured; `ContinuousSpace2D` is demoted; the phase specs need a
revision pass.

### Option C — Network-primary, clean rebuild

Build a new network-primary engine from scratch; port nothing.

| Dimension | Assessment |
|-----------|------------|
| Complexity (now) | High — full rebuild |
| Migration cost | Very high |
| Scientific fidelity | High |
| Canonical replication | Would have to be re-established from zero |
| Reuse of Phase 1-3 work | None — discards sound, working design |
| Risk | High — re-introduces already-fixed bugs for no fidelity gain over B |

**Pros:** a clean slate.
**Cons:** discards the genuinely correct parts of the engine (the rule
protocols, the superset/dial design, the canonical harness, the network code);
maximises risk for no fidelity gain over Option B.

---

## 5. Trade-off analysis

The decisive axis is **scientific fidelity versus the cost of change**, and the
cost of change is **time-dependent**.

Option A's cost is zero today and then compounds: each Phase 4-7 mechanism and
each UX surface is another thing built on, and coupled to, a substrate known to
be wrong. A correction later means unwinding all of it. Option A does not avoid
the cost — it defers and inflates it.

Option C pays a fidelity-neutral price: it reaches the same substrate as B
while discarding the parts of the engine that are already correct and tested.
The `Rule`/`EnvRule` protocol, the superset-and-dial `Intervention` design, the
canonical HK harness, and the S4 network machinery are sound and
substrate-independent. Rebuilding them is pure risk.

Option B isolates the change to where the mismatch actually is — the influence
core — and pays the cost once, now, when the project is five engine stages and
zero UX surfaces large. Its one genuine cost, re-validation of the pillar, is
unavoidable under any option that fixes the substrate, and is exactly the
empirical-measurement discipline the project already runs each phase.

The timing argument is decisive: **this is the cheapest this decision will ever
be.** Every phase added under Option A raises the price of eventually doing
Option B. **Option B is recommended.**

---

## 6. The proposed architecture

### 6.1 Two spaces, kept distinct

| Space | What it is | Role |
|-------|-----------|------|
| Ideology space | The 2D compass; each agent's `ideology` vector in [-1,1]^2 | Agent state; the thing the run evolves; the thing the UI plots. **Not** queried for interaction. |
| Social network | A graph over agents (`dict[int, set[int]]`, the S4 representation), held in the environment | The influence substrate. Has structure (degree, clustering, communities); built once, co-evolves; the **only** thing that decides who can influence whom. |

### 6.2 Influence flows along edges

The influence rule no longer asks the space "who is within `epsilon` of me." It
asks the network "who am I tied to," and moves the agent toward those
neighbours:

```python
def apply(self, agent, network, env, rng):
    neighbors = network.neighbors(agent.id)          # the substrate decides this
    if not neighbors:
        return StateDelta()
    weights = [self.confidence(agent, n) for n in neighbors]   # the graded filter
    if sum(weights) <= 0:
        return StateDelta()
    target = weighted_mean([n.state.ideology for n in neighbors], weights)
    return StateDelta(d_ideology=self.strength * (target - agent.state.ideology))
```

The single structural change: the candidate set is `network.neighbors(agent)`,
not `space.neighbors_within(epsilon)`.

### 6.3 Bounded confidence as a graded edge filter

`epsilon` is retained but reinterpreted. It no longer answers "can I hear this
person" — the network answers that. It answers "a tie of mine disagrees with
me; how much do they still move me." The weight a neighbour receives decays
with ideological distance: a like-minded tie pulls at full weight, a distant
tie at a discounted weight, and — past a latitude-of-rejection threshold — the
weight may go negative, i.e. repulsion (Jager & Amblard). The exact functional
form is deliberately left open (Section 10); the decision here is only that the
confidence threshold becomes an *edge weighting*, not a *membership test*.

### 6.4 Homophily shapes the graph; voluntary and involuntary ties

Ideology re-enters the influence path, but through the honest door. Ties form
and rewire preferentially between agents who are similar — on ideology and on
other attributes (the `social_coord` from S4, demographics later). So ideology
shapes *who you are connected to*, over time; it does not directly shape who
influences you. A subset of ties is **involuntary** — kin, workplace (Mutz &
Mondak 2006) — formed without homophily and exempt from homophilous rewiring.
The voluntary/involuntary distinction, a Phase 4 item, becomes a natural
property of a first-class network rather than a patch.

### 6.5 The network as the spine from S0

The network is built at construction time and present in every stage. S0 is a
structured network with influence dialled to zero. The "superset pipeline,
strengths as the dial" design (Phase 1, D5) is unchanged: a stage is still an
absolute parameter bundle; the bundles now also address tie-formation and
rewiring parameters. The staged pillar narrative (S0 baseline -> ... -> S4) is
preserved; what changes is that the network is load-bearing throughout, not
switched on at S4.

---

## 7. Canonical replication is preserved

Run the edge-based influence rule on a **complete graph** — every agent tied to
every other — and grade the edges by the `epsilon` filter: the result is
identical to today's mean-field Hegselmann-Krause update. Classic bounded
confidence is therefore a *configuration* of the new engine, not a casualty of
it. The new model is a strict generalization of the old.

This yields a hard, non-negotiable migration gate (Section 8, Step 3): the
canonical HK phase tests — loose-`epsilon` consensus, tight-`epsilon`
fragmentation, monotonicity in `epsilon` — must pass when the new engine runs
in complete-graph mode. If they do not, the re-foundation has changed the
canon and is wrong.

---

## 8. Migration path

A staged migration, so there is always a runnable, testable artifact.

- **Step 0 — Accept this ADR.** The substrate decision is committed before any
  code moves.
- **Step 1 — Make the network first-class.** A graph substrate object built in
  `build_engine`; a complete-graph constructor for canonical mode; the existing
  homophilous generator promoted to build the pillar's network at S0.
- **Step 2 — Rewrite the influence core.** `BoundedConfidenceInfluence` becomes
  edge-based (Section 6.2); the `epsilon` threshold becomes the graded filter
  (Section 6.3). `ContinuousSpace2D` is demoted to a coordinate store and
  homophily-distance helper.
- **Step 3 — RIGOR GATE: canonical replication.** Run the HK phase tests in
  complete-graph mode; they must pass. **No later step proceeds until this is
  green.**
- **Step 4 — Re-validate the pillar.** Re-measure the S0-S4 directional
  thresholds on the new substrate; update the phase specs' numbers. The pillar's
  qualitative behaviour (variance falls, constraint rises, the network sorts)
  must survive; only the magnitudes move.
- **Step 5 — Homophily and tie strata.** Tie formation and rewiring on the new
  substrate; the voluntary/involuntary tie distinction. (This overlaps the
  Phase 4 cross-cutting-tie work; the handoff is noted in the Phase 4 spec.)
- **Then — Phase 4 realism work resumes**, now on the correct substrate:
  heterogeneous anchored agents, the affect channel, repulsion/null levers,
  calibration.

---

## 9. Consequences

**What becomes easier**

- The Phase 4 realism items stop being patches. Cross-divide influence is just
  "an edge exists." Sticky involuntary ties are a non-rewireable edge stratum.
  Anchoring is the Friedkin-Johnsen stubbornness term — a native parameter.
- Echo chambers become honestly demonstrable: structure *causes* them, rather
  than being a circular re-description of ideological proximity.
- Repulsion / backfire and the "null levers" become natural — an edge can carry
  negative influence; "expose people to the other side" can honestly wash out.
- Affective polarization attaches cleanly: out-party animus rides on ties and
  nodes, a channel separate from position.
- Generational replacement becomes network-native: a new agent inherits a
  position *in the network*, not just an opinion.

**What becomes harder / the costs**

- The influence core is rewritten and the pillar must be fully re-validated.
- `ContinuousSpace2D` loses its central role.
- Performance characteristics change — edge iteration replaces KDTree queries;
  generally comparable or better for sparse graphs, to be confirmed.

**What we will need to revisit**

- Every Phase 1-3 measured threshold (re-measured in Step 4).
- The canonical test harness gains a complete-graph mode.
- `pillar_engine_roadmap.md` and the Phase 1/2/3 specs need a revision pass —
  their staged-pillar design survives; their substrate assumptions and measured
  numbers do not.
- `show_pillar.py` — already network-aware; expected to need only minor changes.

---

## 10. Open questions (deliberately not decided here)

This ADR scopes tightly to the substrate. The following are acknowledged and
deferred to the Phase 4 spec or a follow-up ADR:

- The exact functional form of the graded confidence filter — hard cutoff,
  smooth decay, or decay-then-repulsion.
- Whether media outlets become first-class nodes in the network or remain a
  separate attractor.
- Network-generator realism — calibrating degree distribution and clustering to
  empirical social-network statistics.
- Per-agent heterogeneity of `epsilon` and stubbornness — a Phase 4 decision.
- Dimensionality of ideology space — assumed to remain 2D; not reopened here.

---

## 11. Action items

1. [ ] Accept this ADR (Step 0) — sign-off before Phase 4.
2. [ ] Promote the network to a first-class substrate; add the complete-graph
   constructor (Step 1).
3. [ ] Rewrite `BoundedConfidenceInfluence` as edge-based with the graded filter
   (Step 2).
4. [ ] Pass the canonical HK tests in complete-graph mode — the rigor gate
   (Step 3).
5. [ ] Re-validate the S0-S4 pillar; update the phase specs' thresholds
   (Step 4).
6. [ ] Implement homophilous tie formation/rewiring and the voluntary/
   involuntary strata (Step 5).
7. [ ] Revise `pillar_engine_roadmap.md` and the Phase 1/2/3 specs for the new
   substrate.
8. [ ] Write the Phase 4 spec (realism core) against the network-primary engine.

---

*Big picture: the substrate decision is the highest-leverage choice in the
project. Influence either flows the way it does in the real world, or it does
not — and every later mechanism, every validation target, and the eventual
public-facing tool inherit that choice. Getting it honest now, before the UX
and before Phases 4-7, is what lets everything built on top be honest too.*
