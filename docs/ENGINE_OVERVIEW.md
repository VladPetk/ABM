# polarlab — Engine Overview

*A single-day briefing on the polarlab simulation engine at the close
of Phase 7. Higher-altitude companion to `methods.md` (the citation-
pinned methods document) — synthesises, doesn't repeat. Read this for
"what we built and why"; read methods.md for "exactly which paper
each number is anchored to."*

---

## 1. What this is

polarlab is an agent-based model of political polarization in a
US-like, two-party society over a stylised ~60-year window (roughly
the 1950s "quiet" baseline through the mid-2020s). It exists to do
one thing publicly and honestly: show what real depolarization
interventions actually do, with the empirical literature as the
calibration anchor.

The engine is **complete as of the close of Phase 7**. Seven phases
of development (Phases 0–7), one substrate refoundation (ADR-001),
69 tests green, ~14-minute full-suite run. No UI yet; that's the
post-Phase-7 work. The model is a **teaching artifact**, not a
policy-prediction tool — its results are illustrative within a
citation envelope, every claim is grounded in published findings,
and every limitation is documented.

The headline finding the engine produces: **most depolarization
interventions people loudly demand don't work in the model.** The
six-intervention library lands two as backfire on issue sorting, three
as null on issue sorting, one as partial (RCV / electoral reform),
and zero as "real" on either axis. The point isn't despair — it's
calibrated honesty. The lay framing the eventual product will offer
is "this is what the empirical literature says, made visible: the
levers you've heard most about are the weakest."

### 1.1 How to read the model — three layers

Everything below sits in one of three layers, and the discipline of the whole
project is keeping them separate and honest about which one carries each result:

- **Mechanism layer** — the general, science-faithful rules (bounded
  confidence, contact, identity sorting, affect dynamics, cross-pressure,
  thermostatic backlash…) that *in coupling* produce polarization. This is a
  model of **how polarization works** — it must be valid on its own terms,
  capable of both polarizing *and* depolarizing depending on conditions, and
  not tuned to any one country.
- **Forcing layer** — country-specific exogenous drivers (US events, media
  penetration, policy shocks) fed in only as *forcings routed through
  mechanisms*: the input nudges a mechanism, the mechanism produces the
  outcome. Never the input writing the outcome.
- **Calibration layer** — knob tuning that *scales* mechanisms to fit the US
  trajectory within the citation envelope. Tuning, not fabrication.

The honesty budget measures the mechanism-emergent vs forcing-carried split per
metric; the R-phase work is about making the mechanism layer carry more of the
load. Full statement and current numbers: [`methods.md` §1.1](methods.md).

---

## 2. The state of the project

| Phase | Did | Status |
|---|---|---|
| 0 | Decide the pillar; lock the data contract for `Intervention`/`Pillar` | done |
| 1 | Thin vertical slice (S0, S1) of the pillar; test harness; HK canonical replication | done |
| 2 | Widen pillar to S2 (party identity) + S3 (partisan media) | done |
| 3 | Add S4 (homophilous network) — the engine's first real-network capability | done |
| **ADR-001** | Re-found engine: network is the *primary* substrate of influence, not a gate on geometric proximity | done |
| 4 | Realism core: anchored agents (Friedkin-Johnsen), graded confidence filter, involuntary cross-cutting ties | done |
| 5 | Affect as a first-class channel: corrected-sign valence, BC affect-modulator, tie-rewiring affect bias, Iyengar test | done |
| 6 | Repulsion + null-levers library: affect-gated `BacklashRepulsion`, 5 named interventions, honesty schema, §11 measure-then-bless gate | done |
| 7 | Calibration: tick-to-real-time mapping, ANES anchor test, X6 contact-hypothesis intervention, cooperative-conditions abstraction, two-axis bucketing, sensitivity audit, `methods.md` | done |

Everything is reproducible. `python -m pytest` runs the full suite.
`python scripts/phase7_sensitivity.py` runs the calibration sweeps.
`python scripts/phase6_calibration.py` re-measures every intervention's
per-axis bucket. All the §11 measure-then-bless results are
fixtures: change the engine and the consolidated tests fail
loudly, demanding re-blessing rather than silent drift.

---

## 3. What the engine can do

Concretely:

- **Run the canonical journey** (the "pillar"): one society moving
  through five stages, each adding a single named mechanism. Stages
  stack on a continuous population — positions carry over, nothing
  resets.
- **Apply the six interventions** (X1–X6) at the end of S4 and
  measure their effect on issue sorting and on affective polarization,
  separately. Each intervention is named after a real-world lever a
  non-expert recognises.
- **Measure** with eight metrics: variance, mean pairwise distance,
  bimodality, ideological constraint, affective polarization, party
  separation, cross-cutting tie fraction, party modularity. A few
  more diagnostics on top (per-agent radial change, position
  histograms, mean ego-network diversity).
- **Replicate canonical Hegselmann-Krause** as a special case
  (`compass_basic` on a complete-graph network). The canonical
  replication tests are the rigor gate — they pass at the same
  thresholds across every phase.
- **Validate stochastically**: every directional test runs across a
  12-seed ensemble; assertions are on ensemble means against
  empirically-measured tolerances (no anecdotes, no single-seed
  fragility).
- **Sweep sensitivities** via the Phase 7 harness: outlet-roster
  variation for X3, centroid-pull magnitude for X5, FJ anchor strength,
  involuntary-tie share. Reports, doesn't auto-assert.
- **Read trajectories in years, not ticks**: `TICKS_PER_YEAR = 3.0`
  pins 1 tick ≈ 4 months, anchored to the ANES out-party-thermometer
  fall.

What kinds of questions the engine is suited to:
- "If a society goes through party identity → media fragmentation →
  network sorting, where does it end up, and how stable is that
  end-state?"
- "What happens if at the polarized end-state we [intervention]?"
- "How sensitive is finding *X* to calibration choice *Y*?"
- "Is the Iyengar finding — affective polarization outpacing
  ideological polarization — a stable feature of the model under
  Phase 5's mechanisms?" (Yes, ratio ~5.8×.)
- "Why does cross-partisan exposure backfire?" (Phase 6 R1 makes it
  explicit: affect gates repulsion.)

What it's *not* suited to:
- Policy prediction. The buckets are *illustrative*, not
  forecasts.
- Cross-national comparisons. Two-party / single-country scope.
- Platform-specific calibration (Twitter vs Facebook vs whatever).
- Calendar-accurate timestamps for specific events.

---

## 4. How it works — the conceptual mechanics

### 4.1 The substrate

Every agent is two things at once:
- **a point in 2D ideology space** (the economic × cultural compass,
  `[-1, 1]²`), and
- **a node in a social network** (a graph of weighted ties to other
  agents).

ADR-001 (2026-05-25) re-founded the engine so the network is the
**primary substrate of influence**: every interaction rule queries
"who am I tied to," not "who is within ε of me in ideology." Ideology
space is for state (the agent's actual position) and visualization
(the dots in the eventual UI). It's no longer queried for influence.

This sounds obvious but it's the project's most consequential
architectural decision. Before ADR-001, "you influence me iff you're
close to me in ideology" meant the engine *defined* an echo chamber
in terms of the thing it was supposed to explain. Now influence
flows along ties; homophily shapes which ties exist; ties survive
opinion change with lag; structure is real. Classic Hegselmann-Krause
is recovered exactly as the **complete-graph special case** — the
canonical replication still holds.

### 4.2 What an agent carries

Each agent's state is open. The pillar's agents carry:

- `ideology`: 2D position, initialised uniformly in `[-1, 1]²`.
- `party`: one of {0, 1}, assigned by which side of `x = 0` the
  initial ideology sits on.
- `identity_strength`: scalar in [0, 1], drawn from Beta(2, 2).
  Modulates `PartyPull`.
- `identities`: 3-vector of cross-cutting identity dimensions
  (race/religion/lifestyle), centred at `±0.3` by party.
- `affect`: `{other_party_id: warmth}` dict, evolves under
  `AffectiveUpdate`.
- `media_diet`: weights over named outlets (Fox, MSNBC, NYT, etc.).
- `anchor` (F1): the agent's *initial* ideology, fixed forever.
  Friedkin-Johnsen anchor.
- `stubbornness` (F1): scalar in [0, 1], drawn from Beta(2, 5).
  Most agents barely move; a thin tail moves freely.
- `social_coord`: 1D latent social position, partly party-correlated.
  Shapes tie formation but never updates — the "ratchet anchor" for
  the network.

### 4.3 The network

The substrate. Built once at construction:
- **Voluntary edges** generated homophilously: edge probability
  decays with combined ideology + social distance (Wong et al.
  2006 spatial network construction).
- **Involuntary edges** (F3, Phase 4): a small cross-party stratum
  (~1 edge per agent) representing kin/workplace ties that exist
  regardless of homophily. Exempt from `TieRewiring`.
- **Cooperative edges** (Phase 7): edges X6 adds during the
  intervention's `setup`, tagged `cooperative=True`. The
  `AffectiveUpdate` rule mutes negative valence on these edges,
  representing Allport conditions.

Mean degree lands at ~7-10 at the default `n_agents = 250` — close
to a real-world political-discussion network (GSS "important
matters").

### 4.4 The rules

A rule produces one `StateDelta` per agent per tick, the engine
sums them across the pipeline and applies them synchronously. No
rule mutates state directly. Rules in the pillar:

- **`BoundedConfidenceInfluence`**: gathers an agent's network
  neighbours, gives each a graded logistic weight `w(d) = 1 / (1 +
  exp((d − ε) / T))`, weighted-mean target, agent shifts a fraction
  `strength` toward it. Hard-cutoff at `temperature = 0` recovers
  canonical HK (this is the rule `compass_basic` uses).
  - Phase 5 adds an **affect modulator**: hostile out-party
    neighbours' weight is multiplied by `1 + affect_weight * warmth`,
    clipped to [0.1, 2.0].
- **`PartyPull`**: agents drift toward their party's centroid in
  ideology space, scaled by `identity_strength`. Hetherington 2001
  elite-cue mechanism, abstracted.
- **`MediaConsumption`**: agents drift toward the weighted-mean
  position of the outlets in their `media_diet`. Levendusky 2013
  abstracted.
- **`AffectiveUpdate`** (Phase 5 rewrite): per out-party network
  neighbour, valence = `-(identity_distance + issue_distance +
  baseline)`. Negative-going. Phase 7: muted by `cooperative_mute`
  on cooperative edges (Allport conditions). *Contact-mediated* —
  fires only on a direct out-party tie.
- **`MediatedAnimus`** (affect re-grade, 2026-06; arc only, gated
  behind `evidence_regrade`): the *contact-independent* (parasocial)
  animus channel. Each tick, a partisan agent's out-party warmth cools
  by `-lr · mediated_animus_weight · identity_alignment`, with NO
  network neighbour required — modelling animus bred by aligned
  identity + partisan media toward out-partisans one never meets
  (Mason 2018; Iyengar et al. 2019). Supplies the late steepening the
  contact channel can't, because homophilous sorting starves out-party
  contact. Off by default (`lr=0` / `weight=0`) → pillar bit-identical.
- **`IdentitySorting`** (Mason mega-identity): with low probability
  per tick, an agent updates one identity-axis toward the in-party
  modal value.
- **`BacklashRepulsion`** (Phase 6 R1): off in the pillar's
  baseline; turned on by intervention X1. Affect-gated — push only
  fires for out-party neighbours when the agent's warmth toward
  their party is below `-0.3`. Bail 2018 backfire conditioned on
  prior animus.
- **`GaussianNoise`** + **Friedkin-Johnsen anchor pull** (F1, Phase
  4): every tick adds small noise scaled by `(1 - stubbornness)` +
  an anchor-pull `α * stubbornness * (anchor - ideology)`. Stubborn
  agents move less; the noise rule carries the anchor mechanic
  because it's the only rule guaranteed to fire in every stage.
- **`TieRewiring`** (env rule, Phase 3): slow homophilous
  co-evolution. Each tick with probability `rewire_rate = 0.02` at
  S4, each agent drops its highest-distance voluntary tie and forms
  a new one biased toward low combined distance. Phase 5 (A5)
  augments the drop ranking with an affect bias. Involuntary ties
  are never dropped.
- **`EliteDrift`** (env rule): currently inert in the pillar
  (`rate = 0`). Capability ships for any scenario that wants
  exogenous elite divergence.

The Friedkin-Johnsen `(1 - stubbornness)` scaling lives on the
**apply site of every ideology-moving rule**. Stubborn agents see
every pull damped uniformly. The anchor pull is added only by
`GaussianNoise` (the once-per-tick guarantee), so the FJ recurrence
fires exactly once regardless of how many other rules are active.

### 4.5 The pillar — stages on a single population

The "calm to camps" pillar is one continuous society moving through
five stages. Each stage *adds one mechanism* by an absolute
parameter bundle:

- **S0 Baseline** — only `GaussianNoise`. Society sits at the
  uniform initial condition, drifting noise-only. Variance stable.
- **S1 Bounded confidence** — `BoundedConfidenceInfluence.strength
  = 0.08`. Agents shift toward their network neighbours. Variance
  falls; the canonical Hegselmann-Krause story.
- **S2 Party identity** — `PartyPull.strength = 0.04` and
  `AffectiveUpdate.lr = 0.01` turn on. Clusters align to party
  centroids, affect deepens (out-party warmth falls to ~-0.85).
  Ideological constraint rises.
- **S3 Partisan media** — `MediaConsumption.strength = 0.04`.
  Heavy-media-diet agents drift further out than light-diet agents;
  the Iyengar-style affect/ideology gap stays open.
- **S4 Homophilous network co-evolution** — `TieRewiring.rewire_rate
  = 0.02`. The network sorts: cross-cutting ties fall, modularity
  rises. Polarization becomes *sticky* (the ratchet).

The pillar runs *continuously*: positions carry over between stages,
nothing resets. Validation runs use cold per-stage builds; the
journey itself never resets.

The post-S4 state is the model's "polarized society." It's where
every Phase 6/7 intervention is applied — the "release-phase"
experiment.

### 4.6 The intervention library

Six release-phase interventions, applied at the end of S4. Each is
a named, public-facing lever (not a knob name), backed by
literature, mapping to a clean engine mechanism, and labelled by
**measurement** on two axes:

- **X1 Show people the other side** — turns on `BacklashRepulsion`
  at strength 0.05. The R1 affect-gate fires because post-S4 affect
  is well below -0.3. Bail 2018 backfire.
- **X2 Fix the algorithm** — zeroes `BoundedConfidenceInfluence.
  affect_weight`. Removes the model's algorithmic affect-muting
  channel. Guess/Nyhan 2023 null.
- **X3 Quit cable news** — zeroes `MediaConsumption.strength`.
  Allcott 2020 + Levendusky 2013 (reverse).
- **X4 Bipartisan dialogue programs** — `setup` adds 20 cross-party
  voluntary ties + resets participants' out-party affect to 0.
  Levendusky 2021.
- **X5 Ranked-choice voting** — `setup` halves both party
  centroids. Hetherington 2001 reverse + Gidron 2020.
- **X6 Shared neighborhoods and workplaces** — `setup` adds 3
  cross-party involuntary edges per agent, **tagged
  `cooperative=True`** (Phase 7's Allport-conditions abstraction),
  + resets every agent's out-party affect to 0. Allport 1954 +
  Pettigrew & Tropp 2006.

Each intervention's label is set by §11 measurement after a 12-seed
release run. The discipline is "move the tag, not the threshold" —
if a future change shifts an intervention out of its declared
bucket, the consolidated test fails and the tag is re-blessed
honestly.

### 4.7 Three kinds of force — emergent, exogenous, tuned

A natural question on reading the rule list: which of these are
*mechanisms* (the outcome emerges from interaction) and which are just
*pressures* applied on a schedule to everyone? There are three kinds,
and the distinction governs how much weight to put on any one result.

1. **Emergent / endogenous** — the per-agent change depends on the
   agent's own evolving state and/or its network neighbours. The
   outcome isn't written in; it falls out of interaction.
   `BoundedConfidenceInfluence`, `AffectiveUpdate` (cools *on contact*),
   `TieRewiring` (drops cold/distant ties → echo chambers),
   `IdentitySorting`, `BacklashRepulsion`, `PerceptionUpdate`. These
   behave the way an ABM is supposed to.

2. **Exogenous drivers on a calendar clock** — the same pressure
   applied to everyone (or a fixed group) at dated times. This is **not
   a flaw**: polarlab models the **mass public**, so elite behaviour,
   the media environment, and dated shocks are genuinely *outside* the
   250 agents and enter as boundary conditions. `EliteDrift` (a discrete
   R-heavy step at the Gingrich/1994 Republican Revolution);
   `MediaConsumption` switching on at the Fairness-Doctrine repeal
   (1987) and Fox News (1996); the social-media affect ramp
   (2008/2010/2012); the `MediatedAnimus` media-exposure ramp; the 2016
   status-threat shock (`THREAT_2016_MAGNITUDE = 0.5` for 60% of
   Republican agents, then decaying). You would not want a mass-public
   model to "emergently produce Newt Gingrich."

3. **Tuned constants** — fixed scalars (and a couple of calendar
   curves) applied uniformly, calibrated so the arc tracks ANES. The
   most load-bearing is the **party-issue coupling schedule (0.40 in
   1980 → 1.10 in 2025)**, which scales both `PartyPull` and the
   issue term in `AffectiveUpdate`. Others: learning rates, affect
   thresholds, step sizes, noise σ, `cooperative_mute = 0.5`. These are
   unavoidable — you cannot read a learning rate off a paper — and they
   are exactly what §6's provenance tags mark **N**: the *mechanism* can
   be **L** (literature-supported) while the *magnitude* is still the
   model's.

**The dated-referent test.** A calendar schedule is admissible only if
it maps to a real dated external change. A uniform curve tuned *only* to
reproduce the target trajectory is curve-fitting — "painting the target
on." The project enforces this: in the 2026-06 affect re-grade a
time-ramped `affect_lr` was **rejected** for having "no real-world
referent," and the late steepening of out-party animus was instead
sourced from *endogenous* identity-alignment × a *dated* media driver
(which does have a referent). The principle is stated in methods.md.

**Emergent vs scripted — why the pillar exists.** Because the historical
arc carries all of kind 2 and kind 3, a fair worry is that its
trajectory is *driven* to the empirics rather than *generated*. The
pillar is the answer: it runs the same mechanisms with **no dated events
at all**, so it tests whether the dynamics compound on their own. If the
arc looked right only because the schedules drag it there, the pillar
would expose it. That separation — eventless composition control vs
empirically-driven build — is the structural reason the two scenarios
are kept distinct.

Two honest tensions worth naming: (a) the coupling curve straddles kinds
2 and 3 — it maps to Mason's "great sort" timeline (a real referent) but
its *shape* is tuned; and (b) "applied uniformly" erases exposure
heterogeneity (not everyone watched Fox or is online).

> This force-type axis (emergent / exogenous / tuned) is **a different
> question** from §6's L/N/E axis. L/N/E asks *how well-evidenced* a
> choice is; this asks *where the force comes from*. They are orthogonal
> — a constant can be well-evidenced in direction (**L**) yet
> imposed-and-tuned in magnitude (**N**). See methods.md.

---

## 5. The intervention findings

> **⚠ Superseded numbers — see the authoritative sources.** The table
> below is the **original six-intervention pillar** library, measured at
> the end of S4 on the *pre-Phase-8c* engine. It is stale on two counts:
> (a) X3 was later re-blessed backfire→**null** and X6 affect
> backfire→**real** (Phase 8c cooperative-share mute — see
> [`methods.md §4`](methods.md) for the current **pillar** buckets), and
> (b) the **shipped / web-facing** interventions are the *seven*-lever
> **historical-arc** library measured on the ANES substrate, not the
> pillar — those are the ground truth for anything user-facing and live
> in [`results/phase10_results.md`](results/phase10_results.md)
> (Step-2 re-measure, 2026-06-01: X1 backfire +0.28…+0.40, X5 partial
> on cross-release average, X6 affect **real** +0.19…+0.24, the rest
> null). Use phase10 for the web build; the table below is retained only
> as the historical pillar-engine record.

| ID | Lay name | Δsep | **Issue sorting** | Δaff | **Affect** | Literature anchor |
|---|---|---|---|---|---|---|
| X1 | Show people the other side | +0.50 | **backfire** | −0.01 | null | Bail et al. 2018 |
| X2 | Fix the algorithm | −0.02 | **null** | −0.01 | null | Guess/Nyhan 2023 |
| X3 | Quit cable news | +0.27 | **backfire** | −0.01 | null | Allcott 2020 |
| X4 | Bipartisan dialogue programs | −0.02 | **null** | −0.00 | null | Levendusky 2021 |
| X5 | Ranked-choice voting | −0.14 | **partial** | −0.01 | null | Hetherington 2001; Gidron 2020 |
| X6 | Shared neighborhoods and workplaces | −0.04 | **null** | −0.23 | **backfire** | Allport 1954; Pettigrew & Tropp 2006 |

Bucket cutoffs: `|Δ| < 0.05` → null; `0.05–0.15` (helpful direction)
→ partial; `≥ 0.15` (helpful direction) → real; opposite-direction
> 0.05 → backfire.

Sign convention: helpful on issue sorting = **negative** Δsep
(camps closer); helpful on affect = **positive** Δaff (warmth
recovers — note the metric itself reads more-negative as more
polarized).

**The headline result is honest, calibrated cynicism:**

- **The two most-demanded interventions backfire** (X1 cross-
  partisan exposure, X3 quit-cable-news). Exposure to the other side
  fires R1's affect-gated repulsion. Quitting cable news at the
  polarized end-state removes a quiet centripetal force (the modeled
  diet target sits inward of the party centroids), letting `PartyPull`
  drag the camps further apart.
- **The flagship policy ask is null** (X2 fix the algorithm).
  Reproduces the Meta/2020 study's finding directly.
- **Two interventions are null at population scale** (X4 dialogue,
  X6 shared institutions). Dialogue's effect is real at the
  participant level but participation is a minority, so the
  population-level Δsep doesn't move.
- **One intervention is partial** (X5 ranked-choice voting). The
  only lever that moves issue sorting at all over the release period
  — and only by Δsep = −0.14, just shy of the −0.15 "real" threshold.
- **Zero interventions are "real" on either axis.** The honest
  reading: in this model, no single intervention reverses the
  polarized end-state cleanly. Even the strongest-evidence contact
  intervention (X6) backfires on affect because per-encounter
  prejudice reduction doesn't reverse population-level accumulated
  animus on its own.

**The X6 finding deserves its own paragraph.** X6 is the
contact-hypothesis lever: shared neighborhoods, integrated workplaces,
public schools, civic institutions. The literature (Allport 1954;
Pettigrew & Tropp 2006 meta-analysis of 515 studies, r ≈ −0.21
between contact and prejudice) is some of the strongest evidence
for a depolarization effect anywhere in social psychology. The
engine implements it with the cooperative-conditions abstraction
calibrated to Pettigrew & Tropp's "halving" reading
(`cooperative_mute = 0.5`). And yet X6 measures **backfire on
affect**, not real. Why? Because X6 also quadruples the cross-party
edge count (+0.25 XC fraction). Per-encounter halving × tripled
encounter volume still nets a deeper negative drift in accumulated
affect. The model is saying something defensible: *contact reduces
per-encounter prejudice but doesn't reverse what's already there at
the population level*. Pettigrew & Tropp's r = −0.21 is on
*individual prejudice change*; population-level Δaff over a 200-tick
release isn't the same quantity. Whether this is a deep limitation
of the model or a deep finding about contact-hypothesis claims is
the most interesting open question in the project.

---

## 6. Provenance — what's literature, what's new, what's extrapolated

This is the table Vlad most wanted. For each major mechanism in the
engine, the category is:

- **(L) Literature-supported** — directly traceable to a published
  finding, often with a specific empirical magnitude in the model's
  anchored zone.
- **(N) New** — the model's own design choice. Mostly architectural
  scaffolding (the pipeline, the `Intervention` schema, the
  staging) and conventions (sign conventions, normalisations).
- **(E) Extrapolated** — informed by literature but goes beyond
  direct evidence: compounded multi-mechanism dynamics, abstracted
  rules, calibration mappings, intervention bucket predictions.

| Mechanism | Provenance | Notes |
|---|---|---|
| **Network is the influence substrate** (ADR-001) | **L** | DeGroot 1974; Friedkin & Johnsen 1990s — network-based averaging tradition. The model picks this over geometric proximity for the principled reason it's named for. |
| **BoundedConfidenceInfluence** (`compass_basic`, hard-cutoff) | **L** | Hegselmann & Krause 2002, *JASSS* 5(3). Faithful replication; canonical phase-behavior tests pass at the published thresholds. |
| **BoundedConfidenceInfluence (graded logistic filter, Phase 4)** | **E** | The hard cutoff is HK 2002; the smooth logistic shape is the model's own choice — picked because it recovers HK exactly at `temperature = 0` and gives a single softness knob. No specific published model uses this exact functional form, but smoothed bounded-confidence variants are well-precedented. |
| **Affect modulator on BC (Phase 5 A4)** | **E** | The *concept* — that affect modulates listening — is empirically grounded (Iyengar et al. 2019; Druckman). The specific multiplicative form `(1 + affect_weight × warmth)` is the model's design. |
| **Homophilous tie-formation** (network generator) | **L** | McPherson, Smith-Lovin & Cook 2001 (homophily review); Wong, Pattison & Robins 2006 (spatial social-network construction). Distance-decay edge probability is standard. |
| **TieRewiring (slow homophilous co-evolution)** | **L** | Centola et al. 2007; Kan, Porter & Mason 2023 (adaptive bounded-confidence). The fragmentation-cascade story is theirs. |
| **TieRewiring affect bias (Phase 5 A5)** | **E** | Extends co-evolution literature with an affect-driven dropping signal. Mutz 2006 supports the qualitative claim ("cross-cutting ties wither under hostility"); the specific bias term is the model's. |
| **Involuntary tie stratum (F3)** | **L** | Mutz & Mondak 2006 (workplace cross-cutting); Mutz 2006 *Hearing the Other Side*. The *existence* and *cross-cutting character* of involuntary ties is the empirical finding. |
| **Involuntary tie share** (`per_agent = 1`) | **E** | Mutz's headline is ~33% of political-discussion partners involuntary. The Phase 4 §13 calibration landed at `per_agent = 1` (t=0 cross-cutting ~0.30), just above Mutz's band — a known compromise (per_agent=0 lands in band but defeats F3's purpose). Documented as a limitation. |
| **PartyPull (elite-cue mechanism)** | **L** | Hetherington 2001, *APSR* 95:619; Levendusky 2009 *The Partisan Sort*. The mechanism (elite cues shift mass partisans) is theirs; the specific functional form (linear pull toward centroid scaled by identity_strength) is the model's abstraction. |
| **MediaConsumption** (per-agent diet × outlet positions) | **L** | Levendusky 2013, *AJPS* 57:611; Martin & Yurukoglu 2017 *AER*. Heavy-diet drift is the literature finding. The pillar reproduces it. |
| **Media-diet pulls inward of party centroids** | **E** | An *artefact* of `US_MEDIA_OUTLETS_2024`'s specific calibration (centrist anchors dilute partisan outlets). The X3 backfire reading depends on it. Phase 7 §5.1 sensitivity sweep shows the reading is robust to roster perturbation but contingent on having *any* centrist anchor. |
| **AffectiveUpdate (negative-going valence, Phase 5 A1)** | **E** | The *sign* (out-party encounters increase animus) is empirically established (Iyengar et al. 2019; Mason 2018). The specific valence formula `-(0.5 × identity_distance + 0.5 × issue_distance + 0.10)` is the model's. The "baseline coolness floor" is a modelling judgment, not a published number. |
| **IdentitySorting** (Mason mega-identity) | **L (mechanism) / N (arc trajectory)** | Mason 2018 *Uncivil Agreement*. Reproduces the qualitative mega-identity-stacking story. Inert in the default pillar (sort_rate = 0); available as an optional intensifier. **Honesty relabel (MHV T0.2):** in the shipped arc the 1980→2025 `identity_alignment` rise is ~83% schedule-carried (`IDENTITY_SORTING_SCHEDULE` + ×5 regrade multiplier + coupling schedule; only ~17% survives with schedules frozen) — endogenous in form, scheduled in trajectory until the planned emergent-sorting rebuild. See methods.md §5.13. |
| **Friedkin-Johnsen anchoring (Phase 4 F1)** | **L** | Friedkin & Johnsen 1999. The stubbornness term and anchor-pull recurrence are theirs, by name. |
| **Stubbornness distribution** (Beta(2, 5)) | **E** | The *shape* (most people barely move, thin tail of free movers) matches descriptive findings in panel data; the specific Beta parameters are a calibration choice. |
| **FJ anchor rate `α = 0.05`** | **E** | Magnitude is a calibration choice. Sensitivity-sweep (§5.4 in methods.md) confirms the no-collapse property survives across α ∈ {0.02-0.10}. |
| **Graded confidence filter `temperature = 0.05`** | **E** | Pillar opt-in value. Calibrated to give visible softening without breaking the loose-ε HK convergence. |
| **BacklashRepulsion affect-gated (Phase 6 R1)** | **L (concept) + E (form)** | Bail et al. 2018 (PNAS) is the source of "exposure backfires *conditionally*." The specific affect-threshold (-0.3) and the `(-warmth)/d²` push are the model's. |
| **Cooperative-conditions edge stratum (Phase 7)** | **E** | Allport 1954's conditions are the empirical concept; representing them as an edge tag with a per-encounter valence multiplier is the model's abstraction. The `cooperative_mute = 0.5` value is anchored to Pettigrew & Tropp 2006's "halving" meta-analytic reading. |
| **The five-stage pillar staging** (S0→S4) | **N** | The ordering — baseline / BC / party / media / network — is the model's narrative choice. Each stage corresponds to a real historical phase (rough mapping in methods.md §2), but the staging itself is a teaching artifact, not a literature claim. |
| **`Intervention` data contract; superset-and-dial design** | **N** | Phase 1 D5. Architectural scaffolding — the engine's way of expressing "a stage is a parameter bundle, a release is also a parameter bundle." |
| **Two-axis bucketing schema** (Phase 7) | **N + E** | The *schema* (separate issue-sorting and affect axes) is supported by literature (Iyengar et al. 2019; Gidron et al. 2020 treat these as distinct). The specific bucket thresholds (0.05 / 0.15) and the `Δparty_separation` / `Δaffective_polarization` as the chosen metrics are the model's design. |
| **Tick-to-real-time mapping (`TICKS_PER_YEAR = 3.0`)** | **E** | The *anchoring procedure* is principled — pin the pillar's affect trajectory to ANES. The *specific value* (3 ticks/year) is the rounding that gives clean conversions. Methods.md §3.1 spells out the projection that justifies it. |
| **Position histogram "no-collapse" property** | **L (the empirical fact) + N (the metric)** | Real populations don't collapse into delta spikes — empirically obvious. The specific operationalisation (>85% in [0.20, 0.50] from centre, <2% past 0.80) is the model's regression guard. |
| **Iyengar test threshold** (|Δaffect| > 2× Δconstraint) | **L (direction) + N (threshold)** | The *direction* (affect outpaces ideology) is Iyengar et al. 2019. The 2× ratio and the absolute floor (Δaff > 0.20) are the model's regression guards. |
| **The pillar-specific calibrated step sizes** (BC 0.08, PartyPull 0.04, Media 0.04, etc.) | **E** | Calibration choices. None is a published number directly; they were tuned (in Phases 1-2) to produce qualitative directional effects within an empirical envelope, then locked. Phase 7 §C2 verified they project to within ~5% of the ANES anchor under linear scaling — but the choices themselves were made by the implementer. |
| **The intervention bucket predictions** (X1 = backfire, X2 = null, etc.) | **L (each cited paper) + E (the simulation's reading)** | Each intervention's literature anchor predicts a *direction* (Bail says exposure backfires; Allcott says quit-Facebook has small effects; etc.). The model's bucket reading — including the surprise re-blessings (X3 from partial → backfire; X4 from partial → null; X5 from real → partial; X6 from real → backfire on affect) — is the model's own measurement, faithful to the literature anchor but not a literal magnitude-replication. |
| **X6's cooperative-mute as edge-level vs agent-level** | **E (judgment)** | This is the live modeling judgment that produced the X6 backfire. Edge-level is the conservative literature reading (Allport conditions reduce prejudice on contact targets); agent-level (Pettigrew 2009 secondary transfer) would be broader and likely flip X6 to partial or real. The edge-level choice is principled; the alternative is the most important Phase 8 follow-up. |
| **The pillar's bundle of S2-S4 effects compounded** | **E** | No single empirical study measures "what happens when a society goes through all of S2 + S3 + S4 over ~60 years." The pillar's trajectory is the model's compounded prediction. It lands consistent with ANES + DW-NOMINATE + Iyengar headlines (Phase 7 §C2 verifies), but the *full-arc claim* is extrapolation, not replication. |

### Summary in one line

**The mechanisms are mostly literature-anchored; the magnitudes are
mostly the model's; the compounded multi-mechanism arc is
extrapolation; the architectural design is the model's own.** The
honesty discipline shipped is that every E entry above is
documented as such, and the §11 measure-then-bless gate means the
bucket reading on each intervention is the model's *actual*
behaviour, not an authored claim.

---

## 7. Honest limitations

A compressed version of `methods.md §5` — read that for the full
list. The five that most matter:

1. **Edge-level vs agent-level cooperative mute.** The current
   implementation mutes negative valence only on cooperative edges
   themselves. Pettigrew 2009's "secondary transfer effect" suggests
   contact reduces prejudice *generally*, not just toward contact
   targets. An agent-level mute (each agent with cooperative ties
   has their `AffectiveUpdate.lr` reduced for *all* out-party
   encounters) would be a broader, more aggressive reading and
   would likely flip X6 to partial or real. The edge-level choice
   is the conservative default; the alternative is the most
   substantive Phase 8 question.
2. **X3 outlet-roster sensitivity.** The "quit cable news backfires"
   reading depends on the diet target sitting inward of the party
   centroids — a property of `US_MEDIA_OUTLETS_2024`. Phase 7 §5.1
   shows the backfire is *robust* to roster perturbation (still
   +0.21 even with no Local TV), but a purely-partisan roster (Fox
   + MSNBC only, no centrist anchors at all) would flip the reading.
   The model's claim is about *this calibration of the 2024 US media
   landscape*, not a universal partisan-media-effects claim.
3. **Per-agent heterogeneity.** Only `stubbornness` is heterogeneous
   per agent; `epsilon`, FJ `α`, affect `lr`, BC `temperature`, etc.
   are all population-uniform. Real populations have wide variance
   on receptivity, identity strength, and elite trust. Phase 8 work.
4. **Two-party / single-country.** Pillar's two-party structure is
   fixed. Multi-party / proportional-representation / cross-national
   institutional dynamics (Gidron 2020; McCoy & Somer 2019) are out
   of scope.
5. **Schematic timeline.** 200 ticks ≈ 67 years is a *stylization*
   — the pillar's S0 doesn't claim to be exactly 1955. The mapping
   pins the *rate of affective cooling* to the ANES headline; it
   does not claim calendar-accurate timestamps for specific events.

And four more flagged honestly in methods.md but worth a sentence
here: affect dilution under S4 tie-isolation (a finding, not a bug —
isolated agents stop forming animus); X5 setup non-idempotency
(double-applying halves twice — fine for §11, awkward for an
interactive UI); `AffectiveUpdate.radius` is vestigial in name;
the involuntary-tie share (per_agent=1) is acknowledged as just
above Mutz's band.

---

## 8. Open follow-up

Phase 8 candidates, in rough order of substantive importance:

1. **Agent-level cooperative-mute** (Pettigrew 2009 secondary
   transfer). The X6 backfire-on-affect reading depends on the
   edge-level choice; agent-level is a defensible literature-faithful
   alternative and may flip X6 to partial or real. If it flips, the
   demo gains a clearly-working lever and the public story changes
   from "no real interventions" to "structural shared-life contact
   under right conditions actually works."
2. **X5b "Drastic electoral reform"** at centroid-pull 0.25×.
   Sensitivity sweep confirms it would land "real" on issue
   sorting. Worth shipping as a separate intervention so users see
   "RCV is partial; abolishing the partisan binary is real" as
   distinct claims.
3. **Per-agent heterogeneity** on `epsilon`, `α`, affect `lr`. Adds
   realism; cost is another full §11 re-measurement and possibly
   new judgment forks.
4. **Residential / network rewiring** (Schelling 1971; Brown & Enos
   2021). The current model has rewiring but not migration.
5. **Cross-national scenario** with electoral-system parameter.
   Calibration anchors: Gidron 2020; McCoy & Somer 2019.
6. **First-class outlets as network nodes** (rather than separate
   attractor). Would tighten the partisan-media model.

None of these block the UI work. Phase 7 closes the engine; Phase 8
is engine extension if needed after the UI surfaces specific gaps.

---

## 9. What the engine is for

A teaching artifact for a public, non-expert audience. Not a
policy-prediction tool. The eventual product will let a user click
through the pillar, watch the society sort, then try interventions
and watch them mostly fail. The pedagogical value is the contrast
between **what people loudly demand** and **what the empirical
literature, made visible through the model, says happens**. That
contrast is the project's whole reason to exist.

Three things keep the project honest as it heads into the UI phase:

- The honesty schema. Every intervention carries a per-axis bucket
  blessed by measurement, not by design. If the model's behaviour
  changes, the consolidated bucket test fails — re-bless honestly,
  don't fudge the threshold.
- `methods.md`. Every calibration choice is recorded with a
  citation and a model-check. The UI can link to it for any user who
  wants to know "why is RCV the only one that helps?"
- The published-literature ground. Every E in the provenance table
  is *informed* by literature; every L is *directly* traceable to a
  paper. The model is not making up its findings.

This document — `ENGINE_OVERVIEW.md` — is the highest-altitude
synthesis. `methods.md` is the citation-pinned reference. The seven
phase specs are the implementation contracts. The 69 tests are the
behavioural lock.

The engine is closed. The story it tells, in one sentence: *in this
calibrated US-like society, the depolarization interventions people
most loudly demand fail or backfire; even the best-evidence
mechanisms produce only partial effects over realistic timescales;
the model exists to make that visible, not to deny that the problem
matters.*
