# Phase 3 Design — S4, the Co-evolving Homophilous Network

*The design decisions for S4, the pillar's final stage. Precursor to
`phase3_spec.md` (which will pin exact code and measured thresholds). Builds
on `s4_network_research.md` (the evidence) and the four decisions taken in
review. This is the "Phase 0 for S4" — it settles shape, not numbers.*

---

## 1. Decisions pinned

| # | Decision | Choice | Source |
|---|----------|--------|--------|
| D1 | Network dynamics | **Co-evolving from the start** — ties rewire as opinions drift. | your call |
| D2 | Tie embedding | **Ideology homophily + a separate social dimension** — each agent carries a stable latent social coordinate; ties depend on both it and ideology. | your call |
| D3 | Influence channel | **Soft gate** — influence flows through ties; non-tied-but-nearby agents keep a small residual weight `cross_tie_weight` (0 = hard chamber). | recommended |
| D4 | Tie memory | The social coordinate is **fixed** (never moves); rewiring is **slow**. Together these are the ratchet — ties lag opinion change. | follows D1+D2 |
| D5 | Engine seam | A pluggable **exposure layer** the influence rules consult; default = today's geometric behaviour, S4 swaps in the network-gated version. | roadmap G4 |

Why soft gate (D3): a pure second channel leaves cross-cutting exposure wide
open, so the "echo chamber" would have no walls and S4 no legible effect; a
full replace discards the bounded-confidence mechanism S1 established. Gating
keeps S1 intact ("bounded confidence over the people you're tied to") and is
the only option under which exposure genuinely narrows. The *soft* part —
`cross_tie_weight` — restores realistic incidental exposure and becomes a
future free-play knob ("how soundproof is the chamber").

---

## 2. The model

Family C from the research note: opinion dynamics on a **co-evolving,
homophily-embedded social network**. Agents remain points in the 2-D ideology
space; on top of that they are nodes in a graph whose edges form by homophily,
persist with memory, and slowly rewire. Grounded in the adaptive
bounded-confidence literature (Kan-Porter-Mason) and the co-evolving
spatial-network models (Chaos 2024); see `s4_network_research.md`.

The non-redundancy guarantee (the research note's central warning): a network
that is a pure function of *current* ideology distance adds nothing. Two things
here prevent that — the **separate social dimension** (ties depend on a
coordinate distinct from the ideology axes) and **memory** (the social
coordinate is fixed and rewiring is slow, so ties lag opinion change). Either
alone would suffice; D2+D4 give both.

---

## 3. New engine pieces

### 3a. The social coordinate (new agent attribute)

Each agent gains `social_coord` — a fixed scalar (1-D for the first cut) in
[-1, 1], a latent "social position" (neighbourhood, milieu, demographic
stratum). Set at build, **never updated by any rule**. Partly correlated with
`party` (same-party agents cluster socially — the Mason mega-identity flavour),
partly random. Because it is fixed, it anchors the network: ties cannot
perfectly track drifting opinions, which is precisely the ratchet.

### 3b. The tie network

A graph over agents, stored as world state (`env.attrs["network"]` — an
adjacency structure). Generated at build: the probability of an edge between
i and j decreases with a **combined distance**

```
d_combined(i, j) = w_ideo * |ideology_i - ideology_j| + w_soc * |social_i - social_j|
```

— a homophily-biased random graph (Random Geometric Graph / social-distance
attachment). A small distance-independent term seeds a few long-range "bridge"
ties (Flache-Macy: bridges matter and can behave counter-intuitively). Target a
modest mean degree (the spec pins it; ~6-10 is typical).

### 3c. The exposure layer (the seam, D5)

Today every influence rule calls `space.neighbors_within`. Phase 3 introduces
an **exposure weight function** `w(agent, neighbour) -> float`, held in
`env.attrs["exposure"]`:

- **Default (S0-S3):** absent, or constant `1.0` — behaviour is bit-identical
  to today. No regression for the existing stages.
- **S4:** the network-gated function — `1.0` if the two agents share a tie,
  `cross_tie_weight` if not.

`BoundedConfidenceInfluence` is refactored minimally: it still gathers
neighbours within epsilon, but the pull target becomes the **exposure-weighted**
mean instead of the plain mean. At `cross_tie_weight = 1.0` this is exactly the
current rule — so S0-S3 are provably unchanged. S4 therefore = "bounded
confidence ∩ network exposure": you update toward people who are both within
your confidence radius and (mostly) inside your social circle.

### 3d. The co-evolution rule (rewiring)

A new `TieRewiring` rule (an `EnvRule` — it mutates world-level network state).
Each tick, with low per-agent probability set by a `rewire_rate`: an agent
drops one of its most ideologically-distant ties and forms a new one, biased
toward low `d_combined`. `rewire_rate` is the memory knob — low = ties lag far
behind opinion (strong ratchet), high = the network tracks opinion closely.
Added to the superset pipeline at `rewire_rate = 0` (an exact no-op for
S0-S3), turned on by the S4 bundle.

---

## 4. New metrics

S4's effects live in the network, which the current metrics cannot see. Add:

- **Cross-cutting tie fraction** — share of edges joining different parties.
  Trivial to compute, the most legible "echo chamber forming" readout, ties
  directly to Mutz. Primary S4 metric.
- **Party-modularity Q** — modularity of the network using `party` as the
  partition. One number for "how echo-chambered"; computable without external
  libraries. Secondary.
- **Mean ego-network diversity** — per-agent share of cross-party ties,
  averaged. Feeds the "follow one agent" view later.

---

## 5. The S4 Intervention

S4 is the one stage that needs a structural change, so it uses the
`Intervention.setup` hook (built in Phase 1 for exactly this):

- `setup(engine)` — assign `social_coord` to every agent, generate the tie
  network, install the gated exposure function into `env.attrs["exposure"]`.
- `param_bundle` — the usual cumulative strengths (S3's bundle) **plus**
  `("TieRewiring", "rewire_rate", <small>)` and the gate is parameterised by
  `cross_tie_weight` (held on the exposure function / a rule attr).

Because `setup` and `param_bundle` are both already part of the `Intervention`
contract, `PILLAR.interventions` simply gains a fifth entry. `show_pillar.py`
and the test harness pick it up with no change.

---

## 6. Validation — the ratchet test

S4's claim is *amplification, not creation*. The test operationalises it as a
**release experiment**:

1. Run the pillar through to S3 — a polarised society.
2. Enter a "release" phase: set the polarising forces (`PartyPull`,
   `MediaConsumption`) to 0, leave bounded confidence on.
3. Run two worlds from that point — one with the S4 network gate active, one
   without (plain S3 geometry).
4. Measure the de-polarisation rate (how fast variance / party separation
   relaxes back toward centre).

**Assertion:** the world with the homophilous network relaxes *more slowly* —
the network holds the polarised state in place. Plus a direct structural
check: cross-cutting tie fraction falls and party-modularity Q rises once S4
engages. Directional, ensemble, same discipline as Phases 1-2.

---

## 7. Build sequencing

D1 (co-evolving from the start) makes S4 the end state — but the *build* should
still be staged internally, so there is always a runnable artifact:

- **3a — static slice:** `social_coord`, network generation, the exposure
  layer, the soft gate, the new metrics. S4 works with a *fixed* network.
  Validate the gate (cross-cutting exposure drops) and a static-network ratchet.
- **3b — co-evolution:** add the `TieRewiring` rule. Validate the fragmentation
  cascade and the full ratchet test (§6).

The end state is co-evolving as you chose; this is just a safe order to reach
it, not a change of scope.

---

## 8. What `phase3_spec.md` must pin

- Exact signature of the exposure function and the `BoundedConfidenceInfluence`
  refactor; proof S0-S3 stay bit-identical.
- `social_coord` generation — the party-correlation strength and noise.
- Network generation — `w_ideo` / `w_soc`, the distance-decay form, mean
  degree, the bridge-tie fraction.
- `rewire_rate` and `cross_tie_weight` starting values, measured.
- The new metrics' exact definitions.
- The ratchet test's thresholds — measured against the engine, as in §9 of the
  Phase 1 spec.
- The S4 `Intervention` bundle and `setup` function.

Scope is honestly larger than S2/S3 — S4 changes the engine rather than
assembling on it. With these decisions fixed, `phase3_spec.md` can be written
and then implemented in the two slices of §7.

---

*Evidence and citations: `s4_network_research.md`.*
