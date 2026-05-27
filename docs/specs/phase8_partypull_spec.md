# Phase 8 Spec — PartyPull and the Single-Attractor Compression

*Engine extension. Phase 8 candidate, not committed scope. Vlad
flagged a concern: `PartyPull`'s single-centroid pull may be
oversimplifying intra-party heterogeneity and contributing to the
over-tight two-blob shape at the polarized end-state. This spec
investigates honestly, lays out the literature picture, measures the
actual compression, and proposes alternatives with explicit
judgment forks. Spec-gated: confirm before any code changes.*

---

## 1. Scope and decisions pinned

**Investigation, then decision, then implementation.** This spec is
the investigation + proposal. The decision is Vlad's. The fork
table in §10 lists what he's choosing between.

| # | Decision | Choice |
|---|----------|--------|
| P1 | **The investigation's question:** does `PartyPull` produce empirically-defensible within-party dispersion at the polarized end-state? **Answer (measured, §3):** no — model SD is ~5× tighter than ANES voter self-placement and ~2× tighter than DW-NOMINATE legislators. Compression is severe. |
| P2 | **The diagnosis is broader than PartyPull alone (§3-4).** `PartyPull` alone (S2) produces SD ~0.15 — at the DW-NOMINATE *legislator* lower bound, but well below ANES voter dispersion. The bigger compression happens when `MediaConsumption` layers on at S3 (SD drops to 0.08). Both rules are single-attractor: PartyPull → centroid, MediaConsumption → diet target. They compound. Any fix must reckon with this. |
| P3 | **Spec scope decision (judgment fork P-Scope):** does Phase 8 fix PartyPull only, or PartyPull + MediaConsumption together, or neither (Option K)? Fixing PartyPull alone helps S2 dispersion but leaves S3/S4 nearly as tight. Fixing both addresses the empirical gap properly. Neither is the "centroid is defensible" reading — the measurement shows the cost. |
| P4 | **Recommended option (§5):** **Option F' — fixed-per-agent personal `party_cue`**, drawn at build time from a normal distribution around the party centroid. Each agent pulls toward their *personal cue*, not the party-wide centroid. Lit-support: Bawn et al. 2012 (coalitional parties); Levendusky 2009 (cue-taking is from specific elites, not the abstract mean); Mason 2018 (identity sub-groups). Produces unimodal-but-wide within-party dispersion (matches ANES). Single new agent attribute, one calibrated parameter, no structural engine change. |
| P5 | **§11 measure-then-bless** discipline applies: σ for the personal cue distribution is calibrated to land within-party SD in the empirical band (target 0.20-0.35; ANES is 0.33-0.47, DW-NOMINATE 0.15-0.20 — the model lands in between). Do not tune past literature-anchored values to chase a target. |

---

## 2. Literature picture

The question: how do partisans actually orient — toward a single
party-wide position, toward factions, toward salient leaders, toward
in-group peers, or toward something else? What does the empirical
within-party dispersion look like, and what should the model match?

### 2.1 What the literature actually says

**Hetherington 2001** (*APSR* 95:619) — "Resurgent Mass Partisanship:
The Role of Elite Polarization." The foundational paper for the
elite-cue interpretation: as elite ideological clarity (DW-NOMINATE
divergence) increases, mass partisanship intensifies. Mechanism:
elites send clear signals, voters take cues. This supports a
centroid-like elite cue (the median legislator's position is a
defensible proxy for "the cue").

**Levendusky 2009** (*The Partisan Sort*) — the cue-taking
mechanism is *plural*: voters take cues from "their" elites
(senators they identify with, media figures they trust, party
spokespersons). The cue signal is noisy and source-specific, not a
unified centroid. Mass sorting follows elite signals, but voters
filter through their personal connection to particular elites.

**Mason 2018** (*Uncivil Agreement*) — partisan *identity* matters
more than ideology. People orient by *team*, not by issue position
on a unidimensional axis. Sub-group identities within parties
(progressive vs centrist Democrats; populist vs business Republicans)
are real and structure cue-taking.

**Bawn, Cohen, Karol, Masket, Noel & Zaller 2012** (*Perspectives on
Politics* 10:571) — "A Theory of Political Parties." The UCLA-school
theory: parties are coalitions of intense policy-demanding groups,
not unitary ideological entities. Party "positions" emerge from
coalitional bargaining, not a single ideological center.

**Karol 2009** (*Party Position Change in American Politics*) —
parties shift policy positions in response to coalition dynamics,
not just median-voter pressure. Multiple internal voices.

**Noel 2013** (*Political Ideologies and Political Parties in
America*) — ideology-party alignment is constructed by elite
political entrepreneurs over time. Strong alignment is recent
(~1970s onward) and varies by issue domain.

**Masket 2009** (*No Middle Ground*) — informal party networks
(donors, activists, allied interest groups) shape candidate
selection. Polarization comes from this network structure, not
median-voter pressure.

**Hacker & Pierson 2020** (*Let Them Eat Tweets*) — the GOP has
moved further right than Dems have moved left. Asymmetric
polarization. Implies party shifts are not symmetric and not
centroid-uniform — internal coalitional dynamics matter.

**Hill 2015**, **Hill & Tausanovitch 2018**, **McGhee et al. 2014**
— the primaries-as-discipline literature. Primary electorates are
*not* systematically more extreme than general electorates;
nomination systems don't strongly cause legislator extremism. The
"primaries radicalize voters" intuition is empirically weak.

### 2.2 Empirical within-party dispersion

| Source | Within-party SD | On model's [-1, 1] axis |
|---|---|---|
| DW-NOMINATE caucus (Lewis et al., voteview.com) | ~0.15-0.20 NOMINATE units | 0.15-0.20 |
| ANES self-placement, 7-point lib-cons scale, strong partisans | SD ~1.0-1.1 | ~0.33-0.37 |
| ANES self-placement, all party identifiers | SD ~1.2-1.4 | ~0.40-0.47 |

Voters are *much more* dispersed than legislators (filtered by
selection). The model represents voters; the appropriate anchor is
ANES, not DW-NOMINATE.

### 2.3 The literature's collective picture

Three claims that the published record supports:

1. **Parties are coalitions, not monoliths.** Bawn et al., Karol,
   Masket, Noel. The *party position* is whichever faction is
   dominant; the *party identifiers* hold heterogeneous views.
2. **Elite cues drive mass sorting, but cues are plural.** Levendusky,
   Mason, Hetherington. Voters orient toward "their" elites, not an
   abstract party centroid.
3. **Empirical within-party voter distributions are unimodal but
   wide.** ANES SD ~0.33-0.47 on the model's axis. Wide enough that
   the current model's 0.08 is a 4-6× under-dispersion.

What the literature does NOT clearly settle:
- Whether the within-party distribution is best modeled as 2-3
  discrete factions (Bawn et al.'s coalitional reading) or as a
  continuous distribution (the empirical ANES distribution is
  unimodal, not multimodal).
- Whether the cue source is a fixed-per-voter elite/sub-group (Mason
  identity reading) or a per-encounter noisy signal (Levendusky
  noisy-cue reading).

These open questions are the source of the spec's judgment forks.

### 2.4 The honest reading

The single-centroid `PartyPull` is **partially defensible**: it
captures Hetherington's elite-signaling mechanism cleanly, and its
implied within-party SD (~0.15 at S2 alone) lands at the
DW-NOMINATE *legislator* lower bound. But it is **not** consistent
with ANES voter dispersion (0.33-0.47), and at S3/S4 — once
`MediaConsumption` compounds — the model's blobs are far below even
the legislator band.

Vlad's hypothesis is right in substance: the single-attractor pull
is contributing to over-tight collapse. The literature supports
moving away from "every party-X agent pulls toward the same point"
in favor of either factional, personal-cue, or peer-sampling
mechanisms.

---

## 3. Diagnosis from measurement

Measured by `scripts/partypull_diagnostic.py` (12 seeds, N=250,
TICKS=200). Within-party SD on the x-axis (the party-aligned axis):

| Stage | Mechanisms active | SD_x party-0 | SD_x party-1 |
|---|---|---|---|
| S0 baseline | noise only | 0.286 | 0.290 |
| S1 BC | + bounded confidence | 0.235 | 0.253 |
| **S2 party identity** | + **PartyPull** + AffectiveUpdate | **0.142** | **0.152** |
| **S3 partisan media** | + **MediaConsumption** | **0.079** | **0.078** |
| S4 homophilous net | + TieRewiring | 0.078 | 0.082 |

The biggest single-stage compression is S2 → S3: SD halves from 0.14
to 0.08 just from adding MediaConsumption. PartyPull contributes
roughly half the total compression; MediaConsumption contributes
the other half (and pushes the result well below the empirical band).

S4's centroid sits at x ≈ ±0.32 — *inward* of the party centroids
±0.5 (a property of `US_MEDIA_OUTLETS_2024`'s diet target sitting
inward, the Phase 6 X3 finding).

**Two compounding single-attractor rules.** PartyPull pulls every
party-X agent toward the same centroid. MediaConsumption pulls
every party-X agent toward a similar diet target (since diets within
a party are similar). They sum.

---

## 4. Options considered

Five candidate options + an honest "as-is" baseline.

### Option K — defend the centroid as-is

**Mechanism:** unchanged. PartyPull continues to pull every in-party
agent toward the party centroid.

**Literature support:** Hetherington 2001 (elite-signaling reading
supports a centroid-like cue).

**Effect on dispersion:** S2 within-party SD ~0.15 (at DW-NOMINATE
legislator lower bound); S3/S4 ~0.08 (well below empirical).

**Honest reading:** defensible *only* if we restrict the empirical
anchor to legislators (DW-NOMINATE), not voters (ANES). The model
represents voters; ANES is the appropriate anchor. Option K
under-disperses voter populations by 4-6×.

### Option D — per-tick noise around the centroid

**Mechanism:** `PartyPull` target = centroid + `N(0, σ_d)` redrawn
per tick.

**Literature support:** thin. Levendusky 2009 "cues are noisy" is
the closest, but per-tick noise is closer to *additive measurement
noise* than to *plural cue sources*.

**Effect:** equilibrium SD ≈ σ_d / sqrt(decay) — modest dispersion
addition. To get from 0.08 to 0.30 would require σ_d ≈ 0.15 per
tick, which is large noise.

**Cost:** trivial implementation.

### Option F' — fixed-per-agent personal `party_cue` *(RECOMMENDED)*

**Mechanism:** at build time, each agent gets a `party_cue` attribute
= `centroid + N(0, σ_pc)`, sampled once and fixed. PartyPull pulls
toward `agent.state.attrs["party_cue"]`, not the abstract party
centroid.

**Literature support:** strongest of all options.
- Levendusky 2009: agents take cues from specific elites/leaders
  they identify with, not the abstract party mean. The fixed
  per-agent cue is "the elite you follow."
- Mason 2018: identity sub-groups within parties are real;
  different agents identify with different sub-group positions.
- Bawn et al. 2012: parties are coalitions; the "party position"
  experienced by any single agent depends on which coalition member
  they're aligned with.

**Effect on dispersion:** within-party SD at equilibrium ≈ σ_pc +
small anchor contribution. With σ_pc = 0.25, expected within-party
SD ~0.25-0.30 — in the lower part of the ANES band, comfortably above
the DW-NOMINATE band.

**Cost:** one new agent attribute (`party_cue`), one new build
constant (`PARTY_CUE_SIGMA`). No new rules. One-line change to
`PartyPull.apply`.

**Why this over the alternatives:**
- Over Option K: Option K under-disperses; this fixes it.
- Over Option D: per-tick noise represents *signal noise*, not
  *source plurality*. Voters following different elites is the
  empirically-supported mechanism.
- Over Option A (multi-faction): continuous personal cues produce
  unimodal within-party distributions, matching ANES. Discrete
  factions produce multimodal distributions, which ANES does *not*
  show.
- Over Option B (peer sampling): peer sampling has mean-reverting
  dynamics (sampling from a wide distribution and pulling toward
  the sample is a variance-reducing process at long horizons).
  Fixed per-agent cues do not mean-revert; they preserve dispersion.

### Option A — multi-faction centroids

**Mechanism:** each party has 2-3 faction centroids (e.g.
progressive/moderate Dems; populist/establishment Reps). Each agent
assigned to a faction at build; PartyPull pulls toward faction
centroid.

**Literature support:** directly Bawn et al. 2012 coalitional theory.

**Effect:** within-party SD ≈ faction-mean spread + within-faction
dispersion. Produces multimodal within-party position distribution.

**Cost:** larger structural change. Needs faction count, positions,
assignment logic, possibly asymmetric (Dems have 2 factions, Reps
have 3?). Adds parameters and modeling judgments.

**Why not chosen:** **empirical within-party distributions are
unimodal, not multimodal.** ANES self-placement within Democrats
shows a single broad peak, not two narrow ones. Multi-faction
over-corrects: it would produce a *qualitatively wrong* distribution
shape even if the dispersion magnitude were right.

### Option B — stochastic in-party peer sampling

**Mechanism:** per tick, PartyPull target = randomly sampled
in-party peer's current ideology.

**Literature support:** Mason 2018 identity reading; conformity-to-
in-group interpretation.

**Effect:** initially preserves population dispersion (sampling from
a wide distribution); long-horizon dynamics are mean-reverting
(sample-and-shift is variance-reducing). Equilibrium SD harder to
predict analytically.

**Cost:** per-tick RNG draw, more expensive than F'. Equilibrium
behavior less predictable; needs §11 measurement to verify it
actually produces empirical dispersion (it might still under-disperse
at long horizons).

**Why not recommended:** less analytically tractable than F';
similar lit-support but weaker mechanism (it's "conform to a random
peer" rather than "follow your specific elite cue"). F' captures
the "different agents follow different elites" claim more directly.

### Option E — salient-leader pull

**Mechanism:** at each tick, identify the most-extreme in-party
agent (highest `identity_strength`, most far-from-centre, etc.) and
have *that* agent be the cue for all in-party. Hetherington/
Levendusky's elite-cue mechanism most literally.

**Literature support:** Hetherington 2001 directly (elite signaling).

**Effect:** pulls *outward*, not inward. Produces *more* extreme
populations, not more dispersed. Doesn't address the compression
problem.

**Why not chosen:** wrong direction. The model is currently
under-dispersed AND not extreme enough (centroids settle at ±0.32
instead of ±0.5); E would amplify extremity without adding
dispersion.

---

## 5. Recommended option — F' personal `party_cue`

### 5.1 The change

```python
# In build_engine, inside the agent loop:
party_centroid = PARTY_CENTERS[party]   # ±0.5, 0
agent_attrs["party_cue"] = (
    party_centroid + rng.normal(0.0, PARTY_CUE_SIGMA, size=2)
)

# In PartyPull.apply:
target = agent.state.attrs.get("party_cue", env.attrs["parties"][party])
# (fallback to centroid keeps non-pillar scenarios working unchanged)
ident = float(agent.state.attrs.get("identity_strength", 0.5))
d = self.strength * ident * (target - agent.state.ideology)
stubbornness = float(agent.state.attrs.get("stubbornness", 0.0))
return StateDelta(d_ideology=(1.0 - stubbornness) * d)
```

### 5.2 Why this captures the literature

- **Each agent has a personal cue source** (the specific elite /
  leader / sub-group they identify with). Levendusky 2009; Mason
  2018.
- **The cue is fixed** (the elite you identified with at age 20 is
  the one you keep identifying with). Mason's identity-stability
  claim.
- **Cues are dispersed around the party position** (different
  elites send different signals; some moderate, some extreme). Bawn
  et al. 2012; Hacker & Pierson 2020 (asymmetric and dispersed
  rightward shift).
- **The pull mechanism is unchanged** — agents still drift toward
  their cue at strength × identity_strength × (1 − stubbornness).
  The qualitative S2 effect (constraint rises with PartyPull active)
  is preserved.

### 5.3 What stays as-is

- **Scenarios that don't set `party_cue`** (compass_basic, actb,
  multi_party_4, two_party_sorting, elite_dynamics) fall through to
  `env.attrs["parties"][party]` — the centroid. Bit-identical
  behaviour for everything outside the pillar. Backward-compatible.
- **`env.attrs["parties"]`** remains the centroid registry; X5's
  setup (which halves centroids) still works because it modifies
  the env-level centroids, and downstream code that reads
  `env.attrs["parties"]` (viz, EliteDrift) is unaffected.
- **The Phase 5 affect channel** is unaffected; affect dynamics
  don't depend on PartyPull's target.

### 5.4 Calibration target

§11 measure-then-bless. Target band: within-party SD_x at S2-end
in **[0.20, 0.35]** — between the DW-NOMINATE legislator upper
bound and the ANES voter lower bound, where the model arguably
belongs (voters but stylised).

Starting `PARTY_CUE_SIGMA = 0.25`; measure; bless or adjust within
±0.10. Do not push past 0.40 (would put cues beyond the centroid in
some cases — model integrity).

### 5.5 What this does NOT fix

**S3/S4 compression from `MediaConsumption`.** The diet-target
pull is its own single-attractor mechanism, with parallel structure
to PartyPull. F' on PartyPull alone will lift S2 dispersion into
the empirical band, but S3/S4 will compress again (probably to
~0.12-0.15 instead of 0.08 — improved but not at empirical level).

A fully-honest fix would also disperse `MediaConsumption`'s pull,
e.g., per-agent variance in the diet target or per-tick noise. This
is flagged as **judgment fork P-MediaScope** in §10.

---

## 6. Files

```
modify  abm/rules/party_pull.py            # read agent.state.attrs["party_cue"] with centroid fallback
modify  abm/pillars/calm_to_camps.py       # seed party_cue per agent at build; PARTY_CUE_SIGMA constant
create  tests/test_phase8_partypull.py     # within-party SD regression + cue-distribution unit tests
modify  scripts/partypull_diagnostic.py    # cleanup, optional — kept around as a re-measurement tool
create  scripts/phase8_partypull_calibration.py  # the §11 measure-then-bless harness
```

The Phase 8 spec is **PartyPull-only** by default scope. If
**P-MediaScope = include**, also:

```
modify  abm/rules/media_consumption.py     # similar dispersion mechanism on diet target
modify  scripts/phase8_partypull_calibration.py  # measure both axes
```

No changes to canonical / machinery / Phase 4-7 tests, the
intervention library, or any UI/website file.

---

## 7. Implementation sketch

### 7.1 `abm/rules/party_pull.py`

```python
def apply(self, agent, space, env, rng):
    if self.strength == 0:
        return StateDelta()
    party = agent.state.attrs.get("party")
    parties = env.attrs.get("parties", {})
    if party is None or party not in parties:
        return StateDelta()
    # Phase 8 F': prefer the agent's personal party_cue if set;
    # fall back to the env-level centroid for scenarios that don't
    # carry per-agent cues (compass_basic, etc.).
    target = agent.state.attrs.get("party_cue")
    if target is None:
        target = parties[party]
    ident = float(agent.state.attrs.get("identity_strength", 0.5))
    d = self.strength * ident * (target - agent.state.ideology)
    stubbornness = float(agent.state.attrs.get("stubbornness", 0.0))
    return StateDelta(d_ideology=(1.0 - stubbornness) * d)
```

### 7.2 `abm/pillars/calm_to_camps.py`

Add module-level constant:

```python
# Phase 8 F': per-agent personal party-cue dispersion. Each agent's
# party_cue is sampled at build from N(centroid, PARTY_CUE_SIGMA²)
# — representing the specific elite / sub-group / leader they
# identify with (Levendusky 2009; Mason 2018; Bawn et al. 2012).
# Calibrated to push within-party SD_x at S2-end into the
# [0.20, 0.35] empirical-defensible band (between DW-NOMINATE
# legislators and ANES voters).
PARTY_CUE_SIGMA = 0.25
```

Inside the build-time agent loop, after `party` is assigned:

```python
attrs["party_cue"] = (
    PARTY_CENTERS[party] + rng.normal(0.0, PARTY_CUE_SIGMA, size=2)
)
```

### 7.3 `tests/test_phase8_partypull.py`

Four tests:

1. **`test_party_cue_seeded_at_build`** — every agent has a
   `party_cue` attr; the mean across party-0 agents is ≈ −0.5 on x
   (within tolerance); mean across party-1 agents is ≈ +0.5.
2. **`test_party_cue_dispersion_matches_sigma`** — empirical SD of
   `party_cue[:, 0]` within each party ≈ PARTY_CUE_SIGMA ± 0.05.
3. **`test_party_pull_falls_back_to_centroid`** — an agent without
   a `party_cue` attr is pulled toward the env centroid (the
   compass_basic / non-pillar fallback path).
4. **`test_party_cue_pulls_toward_personal_cue`** — a hand-built
   two-agent setup where one agent has a `party_cue` at x = 0
   (despite party = 0); after several ticks of PartyPull, that
   agent has moved *less* toward x = −0.5 than an agent with
   `party_cue` at −0.5. Pins the mechanism.

Plus a directional regression in `tests/test_pillar_stages.py`:

5. **`test_within_party_dispersion_in_band`** — within-party SD_x
   at S2-end is in the empirical band [0.18, 0.35]. The band is
   wider than the spec's calibration target [0.20, 0.35] to allow
   cushion. If a future change pushes SD outside the band, the
   test fails and PARTY_CUE_SIGMA needs re-blessing.

### 7.4 Regression guards (must still pass)

- **Canonical HK** tests at the same thresholds (compass_basic
  has no `party_cue` attr; PartyPull falls back to centroid;
  bit-identical).
- **Machinery** tests (determinism, idempotence).
- **Phase 4-7 tests** — including the consolidated bucket test for
  X1-X6.

The Phase 4-7 pillar thresholds may shift. The S2 constraint test
in particular: F' adds noise to where each agent ends up, which may
slightly affect ideological_constraint. Re-measure in §11.

---

## 8. Build sequencing

Two slices.

- **Slice 1 — implement F' minimally.** Add `PARTY_CUE_SIGMA`
  constant, seed `party_cue` in `build_engine`, modify `PartyPull.
  apply` to read it with centroid fallback. Add the four F' unit
  tests + the within-party dispersion regression. Gate: F' tests
  pass; canonical / machinery / Phase 4-7 tests still pass at the
  same thresholds *or* with documented re-blessings.
- **Slice 2 — §11 calibration sweep.** Run
  `scripts/phase8_partypull_calibration.py` (sweeps PARTY_CUE_SIGMA
  ∈ {0.10, 0.15, 0.20, 0.25, 0.30, 0.35}); report within-party SD
  at S2-end + intervention buckets for X1-X6 under each value;
  pick the σ that lands within-party SD in [0.20, 0.35] *and*
  preserves the X1-X6 bucket spread (no bucket flips). Bless and
  commit.

---

## 9. Re-validation — measure, then bless

After Slice 2 the implementer reports:

1. **Within-party SD by stage** under PARTY_CUE_SIGMA candidates.
   Confirm S2-end SD_x lands in [0.20, 0.35] at the chosen σ.
2. **Pillar threshold re-bless if needed.** S1/S0 variance ratio,
   S2 constraint gap, S3 paired correlation, S4 cross-cutting drop
   / modularity rise, ratchet gap. None expected to fail
   qualitatively, but the S2 constraint gap may shift (dispersed
   cues = more dispersion in party position correlation with x;
   constraint may rise less).
3. **Intervention bucket stability.** All six X-interventions
   re-measured under the new dynamics. The honesty discipline:
   if any intervention shifts bucket, re-bless honestly, don't
   adjust σ to preserve.
4. **Canonical HK unchanged.** compass_basic has no `party_cue`;
   PartyPull's fallback to centroid keeps the canonical scenario
   bit-identical.
5. **Position histogram at S4-end.** The Phase 4 "no-collapse"
   property — confirm it still holds with the wider dispersion.
6. **Empirical anchor: does the within-party SD now land in the
   ANES band [0.33, 0.47]?** Probably not at S3/S4 (MediaConsumption
   still compresses). At S2 alone, yes. Honest: a partial fix.

---

## 10. Judgment forks — Vlad's calls

| ID | Decision | Default | Alternatives |
|----|----------|---------|--------------|
| **P-Option** | Which option ships | **F' (personal `party_cue`)** | K (defend as-is); D (per-tick noise around centroid); A (multi-faction centroids); B (peer sampling); E (salient leader) |
| **P-Scope** | Phase 8 fixes only PartyPull, or PartyPull + MediaConsumption | PartyPull only — keeps scope tight, addresses the spec's specific question; MediaConsumption fix is its own follow-up | both — fully addresses S3/S4 over-tightness; bigger change, two parallel mechanisms; neither (Option K) |
| **P-Sigma** | `PARTY_CUE_SIGMA` starting value | **0.25** — gives expected within-party SD ~0.25-0.30, at the lower edge of ANES voter dispersion | 0.15 (closer to DW-NOMINATE legislator band); 0.35 (closer to ANES voter band); 0.20 (a middle compromise) |
| **P-FallbackBehavior** | What non-pillar scenarios see when they don't set `party_cue` | **fallback to `env.attrs["parties"][party]` (centroid)** — bit-identical to current behaviour for compass_basic etc. | always read party_cue (would require updating every scenario); raise if missing (would break compass_basic) |
| **P-Asymmetry** | Should the two parties have different `PARTY_CUE_SIGMA` values | **no — symmetric default** (σ_dem = σ_rep = 0.25) | Hacker & Pierson 2020 asymmetric polarization claim says the GOP is more dispersed and more rightward-skewed; per-party σ values would represent this. But adds parameters and modeling judgments. |
| **P-CueShape** | Distribution of personal cues around centroid | **normal (Gaussian) per-axis** — matches ANES's unimodal pattern | uniform on an interval (sharper cutoff); skewed (one-sided tail toward extremity); per-axis correlated noise |
| **P-Identity-Strength-Interaction** | Does `party_cue` interact with `identity_strength` | **no — `party_cue` is independent of `identity_strength`** (each agent's strength of identification with their cue is separate from where the cue is) | correlate them — high-identity-strength agents get cues closer to the centroid, weak identifiers get more dispersed cues. Theoretically defensible but adds correlation parameter. |

---

## 11. Honest limitations and follow-ups

- **MediaConsumption is the bigger compressor.** F' on PartyPull
  alone will only partially address S3/S4 over-tightness. The
  S3 compression from 0.14 → 0.08 is mostly MediaConsumption.
  Phase 8.2 (or a P-Scope=both choice) is needed to fully match
  ANES dispersion at S3/S4.
- **The `party_cue` is fixed for life.** Real-world voters do
  shift their elite identifications over time (a voter who liked
  Reagan in 1984 may not like Trump in 2024). Phase 9+ could add
  slow drift on `party_cue` — but the literature supports identity
  stability over multi-decade timescales (Mason 2018), so fixed is
  defensible at this engine's timescale.
- **Continuous Gaussian assumes voters are normally distributed
  around the centroid.** ANES distributions are roughly unimodal
  but have heavy tails and slight skew. A more faithful
  parameterisation would be a t-distribution or a small mixture.
  Engineering trade-off: Gaussian is the cleanest first cut.
- **Does NOT make the model more extreme.** F' adds dispersion but
  preserves the population *mean* at the party centroid. So the
  party_separation metric (mean-of-camp - mean-of-camp) doesn't
  move. The under-extremity (centroids settle at ±0.32 instead of
  ±0.5) is a separate issue, driven by MediaConsumption's
  centripetal diet target.

---

## 12. Done checklist (if Vlad confirms F')

- [ ] `PARTY_CUE_SIGMA` constant added; `party_cue` seeded per
      agent at build via the main RNG stream.
- [ ] `PartyPull.apply` reads `agent.state.attrs["party_cue"]`
      with centroid fallback for non-pillar scenarios.
- [ ] F' unit tests pass (cue seeded; dispersion matches σ;
      fallback works; pull mechanic intact).
- [ ] §11 calibration sweep run; PARTY_CUE_SIGMA blessed; within-
      party SD at S2-end lands in [0.20, 0.35].
- [ ] Phase 4-7 thresholds re-measured; any shifts re-blessed.
- [ ] Intervention bucket stability confirmed; any flips reported.
- [ ] Canonical HK, machinery, Phase 4-7 unit tests still pass.
- [ ] Judgment forks (P-Option, P-Scope, P-Sigma,
      P-FallbackBehavior, P-Asymmetry, P-CueShape,
      P-Identity-Strength-Interaction) confirmed or noted as
      defaulted.
- [ ] No UI / website file touched.

---

## 13. Sign-off

This spec proposes Option F' (personal `party_cue`) as the
engine-coherent, literature-faithful, minimally-invasive fix for
the single-attractor compression in `PartyPull`. The diagnosis is
that the bigger compressor is `MediaConsumption`, flagged as
P-Scope fork. The honest reading: zero-engineering Vlad's hypothesis
gives a real model improvement, but **doesn't fully reach ANES voter
dispersion** unless MediaConsumption is also addressed (P-Scope =
both).

Standing by for Vlad's confirm or adjustments on the seven judgment
forks before any implementation.
