# S4 Research Note — Combining a Network Graph with the Geometry

*Background research for the Phase 3 design of S4 (the homophilous network /
"echo chamber" stage). Question put to it: does it make ABM sense to give
agents both a position in the 2-D ideology space and a graph of edges, where
edges affect pull and are shaped by distance — and what would be genuinely
informative to observe? Short answer: yes, and the idea is a recognised model
family, not a novelty. Detail and a design recommendation below.*

---

## 1. Verdict

The instinct is sound. "Agents that are points in a continuous space **and**
nodes in a graph" is exactly how the modern opinion-dynamics literature models
social structure. The current engine's geometric proximity (the
`BoundedConfidence` radius) is really a *stand-in* for a social network —
"you talk to people near you in views." S4 makes that structure explicit and
relational. Three established model families are relevant, and the one the
idea describes sits squarely inside them.

## 2. The three model families

**A. Co-evolving / adaptive networks** — opinions and ties update each other.
Agents rewire toward opinion-similar others; opinions then move toward
tie-neighbours. The canonical recent reference is the adaptive
bounded-confidence model of Kan, Porter & Mason (2023): agents break a tie and
rewire it toward someone whose neighbourhood opinion is closer to their own
("transitive homophily"). The reported outcome is directly what S4 wants — *"a
cascade of fragmentation of the social network into echo chambers,"* with
*"irreversible changes in topology."* That irreversibility is the **ratchet**:
once the network has split, it does not re-merge when the polarising forces
ease. Earlier roots: Centola et al. (2007) co-evolution of cultural similarity
and ties; Holme-Newman-style adaptive networks.

**B. Spatial / geometric social networks** — the network is *embedded* in a
space and edge probability is a decreasing function of distance (Random
Geometric Graphs; Wong, Pattison & Robins, "A spatial model for social
networks," 2006). This is the formal version of "edges shaped by distance."
There is work specifically on generating distance-and-homophily-dependent
networks *for opinion-dynamics ABMs*, including reusable implementations
(comses.net), and on baseline homophily in spatially-embedded networks for ABM.

**Provenance note (Phase 8c D1):** Wong, Pattison & Robins (2006)
supply the formal *mathematical* class of spatially-embedded random
graphs. The specific tie-formation parameters polarlab uses
(`generate_homophilous_network` in `abm/core/network.py`: edge
probability `p_local * exp(-d / tau) + p_bridge`; `tau = 0.40`,
`p_local = 0.35`, `p_bridge = 0.002`) are **E (extrapolation):**
calibrated empirically against the pillar's mean-degree target
(~6-10) rather than fit to Wong et al.'s reported parameter
distributions. The form is literature-supported; the specific
parameters are calibration-fit and so are flagged E.

**C. The combination — opinion dynamics on a co-evolving, spatially/homophily-
embedded network.** This is essentially the idea as described. Schweighofer-
style and the 2024 *Chaos* model "Co-evolving networks for opinion and social
dynamics" put agents in a space, let them move by stochastic dynamics, and form
a *time-evolving* interaction network whose ties depend on **both** social and
opinion similarity. So "agents on an X-Y space that are also graph nodes, with
edges shaped by distance and feeding back into pull" is a published, studied
construction — not a leap.

## 3. What fits this project specifically

The engine already has the opinion state (2-D ideology) and a geometric
influence channel. S4 should add a **tie network embedded in that space**:

- **Tie formation — homophily-biased.** Probability of an edge between *i* and
  *j* decreases with their ideological distance (RGG / social-distance-
  attachment). Add a small distance-independent random component so a few
  long-range "bridge" ties exist — Flache & Macy (2011) show bridges matter and
  can behave counter-intuitively, and it keeps the graph from being a literal
  restatement of geometry.
- **Influence through ties.** Agents update toward the mean opinion of their
  tie-neighbours (a graph-restricted bounded confidence), either replacing or
  composing with the geometric channel. This is the roadmap's "exposure
  provider."
- **Static first, co-evolving second.** Generate the network once for the
  first cut; add slow homophilous rewiring later. Co-evolution is where the
  ratchet genuinely lives.

**The one trap to avoid — redundancy.** If ties are a pure function of
*current* ideological distance, the network adds nothing: it is geometric
proximity under a new name. The network earns its place through one of two
things, and ideally both:

1. **Memory / persistence.** A tie formed in the past *persists* even after the
   two agents' opinions drift apart. The lag between opinion change and tie
   change is the actual engine of amplification — it is why a social circle
   *insulates* an opinion rather than tracking it. This is the cheapest way to
   get the "ratchet, not engine" behaviour the S4 claim promised.
2. **A partly-independent embedding.** Ties depend not only on the 2 ideology
   axes but also on something else — a geographic/social coordinate, or
   identity. The *Chaos* 2024 model uses a separate social space exactly for
   this reason.

Recommendation: lead with **memory** (simplest, and it *is* the ratchet); treat
the independent-embedding option as a later enrichment.

## 4. What would be genuinely informative to observe

Adding a network unlocks a whole layer of structure the current dot-cloud
cannot show:

- **Network modularity Q** — one number for "how echo-chambered is this
  society." It climbs stage by stage; real online-discourse data sits around
  0.7. A clean, citable headline metric.
- **The fragmentation cascade** — the tick at which the graph tips from one
  connected component into two near-disjoint camps. A visible, dramatic event,
  not a slow drift.
- **Cross-cutting tie fraction** — the share of edges that cross party. Its
  collapse is the most legible "echo chamber forming" readout, and it ties
  directly to Mutz's cross-cutting-exposure work.
- **The ratchet, made visible** — run S0-S3 to a polarised state, then switch
  the forces *off*. With the network the society stays split; without it the
  society relaxes. Two panels side by side — this is the proof of "amplifies,
  doesn't create."
- **One agent's ego-network closing** — follow a single person; watch their
  circle lose its cross-cutting ties over time. The humanising view.
- **Bridge agents / brokers** — the few who keep cross-party ties; what happens
  to them, and whether adding bridges actually de-polarises (Flache-Macy say:
  not always).
- **Visually** — edges drawn between dots. The animation goes from a hairball
  of crossing lines to two separate webs. That is a far stronger thing to watch
  than dots drifting, and it is the natural visual centrepiece for the eventual
  product.

## 5. How this feeds Phase 3

This research resolves the open shape of the S4 design. The Phase 3 design doc
still has to *pin* the specifics — roughly five decisions: the exposure-provider
interface; the tie-generation rule and its homophily parameter; static vs.
co-evolving (and the rewiring rate if co-evolving); how the network composes
with the geometric channel (gate vs. replace vs. add); and the tie-memory /
persistence rule that produces the ratchet. The new network metrics (modularity,
cross-cutting fraction) also need adding. None of that is blocked — the model
family is clear and well-grounded.

---

## Sources

- [Co-evolving networks for opinion and social dynamics in agent-based models — *Chaos* 34, 093116 (2024)](https://pubs.aip.org/aip/cha/article/34/9/093116/3312999/Co-evolving-networks-for-opinion-and-social)
- [An adaptive bounded-confidence model of opinion dynamics on networks — Kan, Porter & Mason, *Journal of Complex Networks* (2023)](https://academic.oup.com/comnet/article/11/1/cnac055/7031227)
- [Bounded-Confidence Models of Opinion Dynamics with Neighborhood Effects (arXiv:2402.05368)](https://arxiv.org/abs/2402.05368)
- [A spatial model for social networks — Wong, Pattison & Robins (arXiv:physics/0505128)](https://arxiv.org/pdf/physics/0505128)
- [Considering baseline homophily when generating spatial social networks for agent-based modelling](https://ideas.repec.org/a/spr/comaot/v19y2013i2d10.1007_s10588-012-9145-7.html)
- [Homophily and Distance-Depending Network Generation for Modelling Opinion Dynamics (comses.net)](https://www.comses.net/codebases/3125/releases/1.1.0/)
- [Modeling Echo Chambers and Polarization Dynamics in Social Networks (arXiv:1906.12325)](https://arxiv.org/pdf/1906.12325)
