# Structural-phase survey — adding endogenous depolarization + fixing wrong-direction forces

**Date:** 2026-06-17. **Status:** survey to choose the approach (no code written). Feeds a spec.
**Inputs:** two read-only surveys — an engine latent-capacity inventory and a depolarization
literature review (raw outputs in the session transcript; key citations inline below).
**Goal (agreed):** make depolarization *possible*, and have the 1980→2025 rise emerge because
the polarizing forces *dominated* in that window — **not** because reversal is structurally
impossible. Reversal capacity is empirically real: Boxell-Gentzkow-Shapiro (2024) find 6 of 12
OECD democracies *decreased* in affective polarization (Sweden, Australia significantly);
mid-20th-c US was a low-polarization era.

---

## The reframe that drives the design: get the AXIS right

The literature is unambiguous and it changes the plan: **US mass *issue positions* barely moved
1980→2025** (Fiorina/Abrams/Pope; Baldassarri & Gelman 2008). The "rise" was **sorting**
(issue–party correlation) and **affect** (out-party warmth). So:

> The depolarizing capacity must live primarily on the **AFFECT** and **SORTING/ALIGNMENT**
> channels, not on issue positions. A model whose only reversibility is on the position axis
> would be adding it to the wrong channel.

This is a tension with the engine: its *cheapest* restoring knobs (BC ε, FJ anchor) act on
**positions**. The literature's #1 priority — **cross-pressure damping on sorting** — is the
one thing the engine entirely lacks (ConstraintOp/IdentitySorting only *align*).

---

## Where the engine actually stands (inventory)

| Lever | Axis | Status in canonical build | Restoring? | Cost to activate |
|---|---|---|---|---|
| **Contact → affect warming** (`AffectiveUpdate` positive path) | AFFECT | **DEAD** — cooperative edges never seeded; `cooperative_share`≡0 | yes (high) | low–med |
| **Cross-pressure damping** (cross-cutting identities suppress sorting/affect) | SORTING/AFFECT | **ABSENT** — only the *aligning* direction exists | yes (high) | med (new factor on existing rules, reuses `identities`) |
| **Bounded confidence** (`influence.py`) | POSITION | ACTIVE but constrained (ε=0.30, affect_weight=0) | partial | low (knobs) |
| **Cross-cutting tie formation** (`TieRewiring`) | network→all | ACTIVE but **homophily-locked** (only same-party ties) | partial | low–med |
| **Thermostatic centroid feedback** | POSITION (aggregate) | exists only as a **one-way fed forcing** (#9), not two-signed | partial | med |
| **FJ anchor pull → 1980** (`noise.py`) | POSITION | ACTIVE — genuine ~10–20% damper | yes (working) | trivial (but at fitted limit) |
| ThreatDecay; CohortReplacement | affect / positions | active but non-restoring as wired | weak | med / low |
| Media (`MediaConsumption`) | POSITION | already de-polarizing (inward diet targets) — *wrong direction* per lit | n/a | — |

**Correction to the audit:** the FJ anchor makes the baseline "net one-way," not a literal pure
ratchet — it damps divergence but can never reverse it, and every other rule is divergent.

---

## Recommended approach: HYBRID, leaning activate-latent — with one new factor

The "activate-latent vs new-mechanism" question resolves to a **hybrid**, because the two
highest-priority, best-evidenced levers map onto existing state:

**Tier 1 — the two that matter most (affect + sorting, per the lit):**
1. **Activate the dead contact→affect warming path** (Pettigrew-Tropp r≈−0.21, already your cited
   anchor; the code already exists). Seed cooperative cross-party ties + `cooperative_share`;
   enable BC `affect_weight` so warmth re-opens cross-party influence. **Self-starving:** as
   `TieRewiring` strips cross-party ties, the warming channel starves itself → polarization
   dominates *endogenously*. This is the elegant core — reversibility that's real but dominated
   without hand-tuning. [AFFECT]
2. **Add cross-pressure damping** — agents whose cross-cutting `identities` are misaligned with
   party get a damping factor on the sorting/affect rules (Mutz 2002; Mason 2018; Baldassarri &
   Gelman 2008). This is the *inverse* of IdentitySorting and the literature's #1 omission,
   because sorting is the channel that actually moved. Reuses the existing `identities` vector;
   it's a new *factor* on existing rules, not a wholly new rule. [SORTING]

**Tier 2 — supporting infrastructure (mostly position-axis, cheap):**
3. Make `TieRewiring` form some cross-cutting ties (not only homophilous) — feeds Tier 1.
4. Tune BC (ε≈0.40, affect_weight≈0.05–0.07) so cross-party influence isn't near-inert (also
   addresses the audit's "BC is a 3% no-op" finding).
5. Make the thermostatic centroid forcing genuinely **two-signed** (a feedback, not a one-way
   push). Lowest priority of the three "serious-defect" lit items, since positions moved least.

**Explicitly NOT doing:** reversing ConstraintOp (it's divergence machinery, not convergence);
strengthening FJ (at its fitted limit); leaning on median-voter/elite moderation (would
*contradict* US evidence); activating shocks for marginal convergence.

---

## The four flagged forces (all in scope) — and a twofer

- **MediaConsumption direction** [POSITION]: diet targets sit *inward* of party centroids
  (quantified: Dem target radius 0.18 vs centroid 0.31). Fix = make partisan diets pull toward
  the pole (Levendusky 2013). **Twofer:** if media does real positional sorting, we can *reduce
  the fed mobilization forcing* currently supplying ~72% of `party_sep` → converts fed fit into
  earned fit (directly attacks audit F1).
- **Bounded-confidence revival** [POSITION]: the model's one convergence force is ~inert; Tier-2
  tuning doubles as a force-fix and a (position-axis) depolarizer.
- **Dated-events net-brake**: confirmed not a bug per se — continuous EliteDrift without
  milestones diverges *faster*, so events read as a brake. Fix is *framing* + possibly making
  event effects the actual drivers rather than the smooth forcing.
- **Cross-party tie formation**: Tier-2 #3 above.

---

## Two things the spec must nail

**1. This is a re-calibration, not a bolt-on.** Activating Tier 1+2 is estimated to cut
`party_sep` 15–35%, which *will* break the current fit (calibrated to ~1.08 at 2025). So the
structural phase must **re-calibrate the polarizing forces** to reproduce the 1980→2025 arc with
the new restoring forces present — and that's the *opportunity* to dial down the fed forcing
(fed→earned). The affect recalibration (P3a) folds in here, since contact-warming changes affect.

**2. The falsification test (what makes this scientifically honest).** After calibration, the
model must:
- still reproduce the near-monotone 1980→2025 rise (affect + sorting), AND
- under a counterfactual (e.g. raise contact / cross-pressure, or run a Sweden-like parameterization)
  actually **depolarize** — demonstrating reversal is *possible but was dominated*, not forbidden.
This converts the one-way-ratchet blindspot from "documented limitation" to "tested property,"
and gives the X-interventions something real to push against.

---

## Open decision for the user
Confirm the **hybrid, affect+sorting-first** approach (Tier 1 = contact-warming + cross-pressure
damping; Tier 2 = rewiring/BC/thermostatic + the media-direction fix with fed-forcing reduction),
vs. a narrower or broader scope. On confirmation → a spec (mechanism definitions, calibration
target, falsification test, re-bless plan) for sign-off before any code, per the SPEC→AGREE loop.
