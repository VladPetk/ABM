# polarlab — methods

*The artifact that backs the project's "intellectually rigorous"
claim. Every calibration choice, every honesty-label, every limitation
recorded here is the one the model actually carries. Last updated at
the close of Phase 7.*

---

## 1. What the model represents

polarlab is an agent-based model of political polarization in a
US-like, two-party society over a ~60-year stylised window — roughly
the post-WW2 / mid-1950s "quiet" baseline through the mid-2020s. The
default `n_agents = 250` is a "village-scale" society chosen for test
speed; the dynamics scale invariantly to larger populations.

The engine is **network-primary** (ADR-001, 2026-05-25): influence
flows along edges of a homophilous social network, not by raw
ideological proximity. Ideology space (the 2D economic × cultural
compass on `[-1, 1]²`) holds agent state and supports visualization;
it does not decide who hears whom. Classic Hegselmann-Krause survives
as the complete-graph special case — `compass_basic` runs it
unchanged, with the canonical replication tests intact.

**One tick ≈ 4 months** of stylised real-world time
(`TICKS_PER_YEAR = 3.0` in `abm/calibration.py`). The default
`TICKS = 200` represents ~67 years; the pillar's S0→S3 progression
maps to roughly the 1955-2020 ANES window.

---

## 2. The five-stage pillar

`abm.pillars.calm_to_camps` defines one canonical journey, a society
moving from neutral baseline through full polarization:

| Stage | Mechanism added | Stylised real-world span | Honesty tag |
|-------|-----------------|--------------------------|-------------|
| S0 Baseline | noise only | ~mid-1950s "calm" | control |
| S1 Bounded confidence | who you listen to | ~1960s–70s | replication (Hegselmann-Krause) |
| S2 Party identity | party cues + affect | ~1970s–90s | illustrative |
| S3 Partisan media | media diets pull diets outward | ~1990s–2010s | illustrative |
| S4 Homophilous network | sticky social-circle sorting | ~2010s onwards | illustrative |

The pillar runs **continuously**: positions carry over between stages.
Validation runs use cold per-stage builds; the journey itself never
resets.

---

## 3. Calibration anchors

The four empirical anchors recorded in `abm/calibration.py`'s
`EMPIRICAL_ANCHORS` registry. Each is the published finding the model
is checked against; the "model_check" line records what the model
actually produces.

### 3.1 ANES out-party thermometer (the tick-to-year scalar)

- **Source:** Iyengar, Lelkes, Levendusky, Malhotra & Westwood 2019,
  *Annual Review of Political Science* 22:129; Finkel et al. 2020,
  *Science* 370:533.
- **Finding:** mean out-party feeling-thermometer scores fell from
  ~48° (1978) to ~20° (2020) — a 28-point drop over 42 years on the
  [0, 100] thermometer, or **−0.56 normalised** to the model's
  [−1, 1] affect axis.
- **Model check:** the pillar's S0→S3 measured Δaffective_polarization
  is ≈ −0.85 over 200 ticks. Under linear scaling, the equivalent
  42-year (126-tick) projection is ~−0.535 — within ~5% of the ANES
  anchor by that arithmetic. The test in
  `tests/test_phase7.py::test_pillar_affect_trajectory_matches_anes_within_band`
  asserts the *full-200-tick* trajectory (~67 years) sits within ±20%
  of the ANES-projected value at that horizon (~−0.89); the measured
  −0.85 is inside the band. The "5% match" is a projection, not a
  measured 126-tick value (which is not run as a separate test — the
  pillar's S2/S3 trajectory is non-linear, so the full-window
  regression is the canonical check).
- **Pinning:** `TICKS_PER_YEAR = 3.0`. The pillar's full 200-tick
  trajectory corresponds to ~67 years of stylised history.

### 3.2 DW-NOMINATE elite divergence (latent — for any scenario that
enables `EliteDrift`)

- **Source:** McCarty, Poole & Rosenthal 2006, *Polarized America*.
- **Finding:** the median Democrat–Republican NOMINATE distance
  diverged by ~0.4 units over ~50 years.
- **Model check:** `EliteDrift.rate ≈ 0.0026` per tick reproduces the
  empirical rate at `TICKS_PER_YEAR = 3.0`. EliteDrift is inert in
  the pillar's S0–S4 baseline; this anchor is a sanity check for any
  scenario that enables it.

### 3.3 Pettigrew & Tropp contact-hypothesis meta-analysis (cooperative-conditions
mute)

- **Source:** Pettigrew & Tropp 2006, *Journal of Personality and
  Social Psychology* 90:751 (meta-analysis of 515 studies on
  intergroup contact; r ≈ −0.21 between contact and prejudice).
- **Finding:** contact under Allport (1954) conditions — equal
  status, cooperative tasks, institutional support — roughly halves
  prejudice formation.
- **Pinning:** `AffectiveUpdate.cooperative_mute = 0.5`. Out-party
  encounters over edges tagged `cooperative=True` produce
  half-strength negative valence. X6's setup adds cooperative
  involuntary edges; the F3 baseline involuntary stratum (kin /
  workplace) is **not** cooperative — the literature is explicit
  that contact alone is insufficient.
- **Modelling judgment flagged:** the current implementation is the
  *edge-level* mute (only encounters across cooperative edges are
  attenuated). Pettigrew 2009's "secondary transfer effect" suggests
  a broader *agent-level* mute (contact reduces overall prejudice
  formation across out-groups, not just the contact target). The
  edge-level reading is more conservative and is what ships;
  agent-level is flagged as a Phase 7 §5 sensitivity item.

### 3.4 Allcott / Meta-2020 algorithmic interventions (the null anchor
for X2)

- **Source:** Allcott, Braghieri, Eichmeyer & Gentzkow 2020,
  *American Economic Review* 110:629 (Facebook deactivation); Guess
  et al. 2023, *Science* 381:398, and Nyhan et al. 2023, *Nature*
  (Meta/US 2020 chronological-feed studies).
- **Finding:** algorithmic-feed interventions produce essentially
  null (or small, in Allcott's case) effects on issue + affective
  polarization at the population level.
- **Model check:** X2 "Fix the algorithm" measured Δsep ≈ −0.02,
  Δaff ≈ −0.01 — null on both axes.

---

## 4. The honesty-labels schema

### 4.1 Two-axis bucketing (Phase 7)

The Phase 6 intervention library carries per-axis bucket labels in
`Intervention.effect_buckets`, blessed by §11 measurement:

- **`issue_sorting`** axis: classifies Δparty_separation over the
  release-phase experiment. Helpful direction = negative (camps
  closer). Thresholds: `|Δ| < 0.05` → **null**; `−0.15 < Δ < −0.05`
  → **partial**; `Δ ≤ −0.15` → **real**; `Δ > +0.05` → **backfire**.
- **`affect`** axis: classifies Δaffective_polarization over the
  same window. Helpful direction = positive (out-party warmth
  recovers — note the sign flip from Δsep). Thresholds:
  `|Δ| < 0.05` → **null**; `+0.05 < Δ < +0.15` → **partial**;
  `Δ ≥ +0.15` → **real**; `Δ < −0.05` → **backfire**.

The literature treats these as distinct outcomes (Iyengar et al.
2019; Gidron, Adams & Horne 2020; Pettigrew & Tropp 2006 — affect /
prejudice is what contact reduces; institutional levers move issue
sorting more than affect; etc.), so the schema follows.

### 4.2 The discipline

**Move the tag, not the threshold.** Each intervention's label is
the measured bucket. If a future code change moves an intervention
out of its declared bucket on either axis, the consolidated bucket
test in `tests/test_phase6.py` fails — the calibration script is
re-run, the tag is re-blessed to the new measurement. The
intervention's *mechanism* is what gets locked; the *empirical bucket*
is what the test reports honestly. The thresholds (0.05, 0.15) are
fixed by the spec and are not adjusted to fit a desired narrative.

### 4.3 The current library

Each intervention's measured per-axis label, with the literature
finding it grounds in. Values measured at N=250, 12 seeds, 200-tick
release.

| ID | Lay name | Δsep | issue_sorting | Δaff | affect | Anchor |
|---|---|---|---|---|---|---|
| X1 | Show people the other side | +0.50 | **backfire** | −0.01 | null | Bail et al. 2018 |
| X2 | Fix the algorithm | −0.02 | **null** | −0.01 | null | Guess/Nyhan 2023 |
| X3 | Quit cable news | +0.27 | **backfire** | −0.01 | null | Allcott 2020 |
| X4 | Bipartisan dialogue programs | −0.02 | **null** | −0.00 | null | Levendusky 2021 |
| X5 | Ranked-choice voting | −0.14 | **partial** | −0.01 | null | Hetherington 2001; Gidron et al. 2020 |
| X6 | Shared neighborhoods and workplaces | −0.04 | **null** | −0.23 | **backfire** | Allport 1954; Pettigrew & Tropp 2006 |

### 4.4 The story arc

- **Two backfire** (X1, X3): the most-demanded interventions in
  public discourse — "show the other side," "quit partisan media" —
  *increase* issue sorting at the polarized end-state. X1 because R1
  affect-gated repulsion fires reliably; X3 because the modeled US
  media diet sits inward of the party centroids (a Phase 7
  sensitivity item — see §5.1).
- **Three null** on issue sorting (X2, X4, X6): the platform-
  intervention (X2), the participation-bounded one (X4), and even
  the structural-contact one (X6) fail to move issue positions. F1
  anchoring + active PartyPull tether agents to their starting side.
- **One partial** (X5): RCV / electoral reform moves issue sorting
  meaningfully (−0.14) but doesn't clear "real" (−0.15). Honest
  reading: the most-promoted institutional reform produces only a
  *partial* effect on issue sorting over a 200-tick release.
- **One backfire on affect** (X6): structural shared-life contact
  with Allport-conditions framing *reduces* per-encounter prejudice
  (cooperative_mute halves valence), but the increased volume of
  cross-party encounters exceeds the per-encounter reduction. Affect
  ends up MORE negative, not less, at the population level. A
  defensible (conservative) reading of Pettigrew & Tropp: contact
  reduces per-encounter prejudice but doesn't reverse accumulated
  animus.
- **Zero "real" on either axis.** That is the empirical reading the
  model ships. The lay framing: most depolarization proposals don't
  work, and even the best-evidence ones produce only partial effects.

---

## 5. Known limitations

A short, honest list. Each item is also a Phase 8+ follow-up
candidate.

### 5.1 X3 outlet-roster sensitivity

X3's backfire reading depends on the calibration of
`US_MEDIA_OUTLETS_2024` in `abm/core/outlets.py` — the diet target
sits *inward* of the party centroids because the roster includes
centrist outlets (Local TV, WSJ) at non-trivial weight. The Phase 7
sensitivity sweep in `scripts/phase7_sensitivity.py` measures X3's
Δsep across three rosters:

- **default roster:** Δsep = +0.27 (backfire)
- **polarized roster** (Fox shifted to `[0.85, 0.65]`, MSNBC to
  `[-0.85, -0.65]`): Δsep = +0.25 (still backfire)
- **no Local TV** (remove the centrist anchor): Δsep = +0.21
  (still backfire)

**The backfire reading is robust across these perturbations** — even
shifting Fox/MSNBC substantially outward, X3 still backfires because
the remaining centrist anchors (WSJ, BBC) keep the diet target
inward of party centroids. The X3 backfire claim is stronger than
the spec initially flagged: not just contingent on the 2024 roster's
specific Fox/MSNBC positioning, but on the *general* presence of any
centrist anchor in the diet. A purely partisan roster (Fox + MSNBC
only) would flip X3 to helpful; the default-roster regression guard
in `test_phase7.py::test_x3_still_backfires_at_default_outlets`
pins the current direction.

### 5.2 X5 centroid-pull magnitude

X5 "Ranked-choice voting" halves the party centroids
(`0.5 * centroid`). Sensitivity sweep (`scripts/phase7_sensitivity.py`):

- **pull = 1.00×** (no change, control): Δsep = −0.02 (null)
- **pull = 0.75×** (mild moderation): Δsep = −0.08 (partial)
- **pull = 0.50×** (default RCV): Δsep = −0.14 (partial — just shy of "real")
- **pull = 0.25×** (drastic moderation): Δsep = −0.20 (**real**)
- **pull = 0.00×** (abolish partisan centroids): Δsep = −0.27 (**real**)

The default 0.5× is the literature-faithful "RCV moderates elites,
doesn't erase party" reading (Hetherington 2001 reverse-direction).
A Phase 8 design choice could add `X5b "Drastic electoral reform"`
at 0.25× as a separate intervention — the sweep confirms it would
honestly land in "real" on issue sorting.

### 5.3 X6 cooperative-mute mechanism — edge-level vs agent-level

The current implementation is **edge-level**: only encounters across
edges explicitly tagged `cooperative=True` are muted. Pettigrew 2009
"secondary transfer effect of intergroup contact" suggests a broader
**agent-level** reading: contact reduces prejudice toward multiple
out-groups, not just the contact target. An agent-level mute (per-
agent `lr` reduction for any agent with cooperative ties) would be
more aggressive and might tip X6 into partial or real on affect. The
edge-level reading is the conservative default and is what ships;
agent-level is flagged as a Phase 8 follow-up.

### 5.4 FJ_ALPHA sweep — no-collapse property

`scripts/phase7_sensitivity.py` reports the S4-end position
histogram across `FJ_ALPHA ∈ {0.02, 0.05, 0.08, 0.10}`:

| α | <0.20 | [0.20, 0.50) | ≥0.80 |
|---|---|---|---|
| 0.02 | 0.023 | **0.974** | 0.000 |
| 0.05 (default) | 0.019 | **0.931** | 0.001 |
| 0.08 | 0.014 | 0.836 | 0.002 |
| 0.10 | 0.011 | 0.773 | 0.005 |

The no-collapse property (mid-band fraction > 0.85, extreme fraction
< 0.02) holds at α ∈ {0.02, 0.05}; the band loosens at α=0.08 (still
no-collapse but fewer agents in the mid-band) and looser still at
α=0.10. The default α=0.05 is the comfortable middle.

### 5.5 INVOLUNTARY_PER_AGENT sweep

`scripts/phase7_sensitivity.py` reports t=0 cross-cutting fraction
across `INVOLUNTARY_PER_AGENT ∈ {0, 1, 2, 3}`:

| per_agent | t=0 cross-cutting fraction |
|---|---|
| 0 | 0.193 (cleanly in Mutz band 0.18-0.25) |
| 1 (default) | 0.305 (just above band) |
| 2 | 0.390 (well above band) |
| 3 | 0.456 (well above band) |

Confirms the Phase 4 §13 reading: `per_agent=0` would land *cleanly*
in Mutz's headline 0.20 band, but defeats F3's purpose (no
structural cross-cutting edges that survive rewiring). `per_agent=1`
is the minimum that preserves F3 and lands 0.05 above the band — an
acknowledged but bounded compromise.

### 5.6 Per-agent parameter heterogeneity

F1 ships with per-agent `stubbornness ~ Beta(2, 5)` but every other
agent-level parameter (`epsilon`, FJ `α`, affect `lr`) is
population-uniform. Real populations have heterogeneous receptivity,
elite trust, and identity strength. Adding per-agent jitter on these
parameters is a Phase 8 modelling task; Phase 7 stays global-scalar
to preserve the Phase 4-6 measurement work.

### 5.7 Affect dilution under tie isolation at S4

The Phase 5 §11 measurement showed a non-monotonic affective_polarization
trajectory: S2 ≈ −0.85, S3 ≈ −0.85, S4 ≈ −0.71 (*less* negative).
Cause: S4's tie-rewiring isolates some agents from out-party
neighbours; their affect freezes at the seed value 0.0, diluting the
population mean toward zero. This is documented in the
`affective_polarization` metric's docstring as "S4 sorts so hard that
some agents stop forming animus altogether" — not "S4 reverses the
sign-fix." The honest reading is an honest finding, not a bug.

### 5.8 Two-party / single-country scope

The pillar's two-party structure is fixed; multi-party / proportional-
representation / cross-national dynamics are out of scope. Phase 8
could add an electoral-system parameter and a `multi_party_4` pillar
variant; the cross-national institutional findings (Gidron et al.
2020; McCoy & Somer 2019) would be the calibration anchors.

### 5.9 Timeline is schematic, not literal

The 200 ticks ≈ 67 years mapping at `TICKS_PER_YEAR = 3.0` is a
stylization: the pillar's S0 doesn't claim to be exactly 1955, and
S4 doesn't claim to be exactly 2022. The mapping pins the *rate of
affective cooling* against the ANES headline; it does not claim
calendar-accurate timestamps for specific simulation events.

---

## 6. What the model is for

polarlab is a **teaching artifact** for a public, non-expert
audience. It is not a policy-prediction engine. The six-intervention
library (X1–X6) is the primary public-facing payoff: a calibrated,
literature-anchored demonstration that:

1. The most-demanded depolarization interventions (contact, platform
   reform) don't work or backfire at a sorted end-state.
2. Self-help interventions (quitting cable news, dialogue programs)
   are null at the population level even where they help
   participants.
3. Even institutional reform (RCV) produces only partial issue-
   sorting reductions over realistic timescales.
4. Even structural shared-life contact under Allport conditions
   doesn't reverse accumulated animus — it slows further cooling but
   doesn't undo what's already there.

The model's results are **illustrative within a citation envelope**.
Each intervention's bucket is the model's reading; each is grounded
in a published finding, but each is also subject to the limitations
in §5. Anyone using the model to argue for or against a real-world
policy should read §5 first.

---

## Citations (full list, alphabetical)

- Allcott, H., Braghieri, L., Eichmeyer, S., & Gentzkow, M. (2020).
  The welfare effects of social media. *AER* 110:629.
- Allport, G. W. (1954). *The Nature of Prejudice*. Addison-Wesley.
- Bail, C. A. et al. (2018). Exposure to opposing views on social
  media can increase political polarization. *PNAS* 115:9216.
- Brown, J., & Enos, R. (2021). The measurement of partisan
  sorting for 180 million voters. *Nature Human Behaviour*.
- Deffuant, G., Neau, D., Amblard, F., & Weisbuch, G. (2000). Mixing
  beliefs among interacting agents. *Advances in Complex Systems*
  3:87.
- Finkel, E. J. et al. (2020). Political sectarianism in America.
  *Science* 370:533.
- Friedkin, N. E., & Johnsen, E. C. (1999). *Social Influence Networks
  and Opinion Change*.
- Gidron, N., Adams, J., & Horne, W. (2020). *American Affective
  Polarization in Comparative Perspective*. Cambridge University
  Press.
- Guess, A. M. et al. (2023). How do social media feed algorithms
  affect attitudes and behavior in an election campaign? *Science*
  381:398.
- Hegselmann, R., & Krause, U. (2002). Opinion dynamics and bounded
  confidence. *JASSS* 5(3).
- Hetherington, M. J. (2001). Resurgent mass partisanship. *APSR*
  95:619.
- Iyengar, S., Lelkes, Y., Levendusky, M., Malhotra, N., & Westwood,
  S. J. (2019). The origins and consequences of affective
  polarization in the United States. *ARPS* 22:129.
- Kan, U., Porter, M. A., & Mason, J. (2023). An adaptive
  bounded-confidence model of opinion dynamics on networks. *Journal
  of Complex Networks*.
- Levendusky, M. (2013). Why do partisan media polarize viewers?
  *AJPS* 57:611.
- Levendusky, M. (2021). *Our Common Bonds: Using What Americans Share
  to Help Bridge the Partisan Divide*. University of Chicago Press.
- Mason, L. (2018). *Uncivil Agreement: How Politics Became Our
  Identity*. University of Chicago Press.
- McCarty, N., Poole, K. T., & Rosenthal, H. (2006). *Polarized
  America*. MIT Press.
- McCoy, J., & Somer, M. (2019). Toward a theory of pernicious
  polarization. *Annals of the American Academy of Political and
  Social Science*.
- McPherson, M., Smith-Lovin, L., & Cook, J. M. (2001). Birds of a
  feather: Homophily in social networks. *Annual Review of Sociology*
  27:415.
- Mutz, D. C. (2006). *Hearing the Other Side: Deliberative versus
  Participatory Democracy*. Cambridge University Press.
- Mäs, M., & Flache, A. (2013). Differentiation without distancing.
  *PLOS ONE* 8:e74516.
- Nyhan, B. et al. (2023). Like-minded sources on Facebook are
  prevalent but not polarizing. *Nature*.
- Pettigrew, T. F., & Tropp, L. R. (2006). A meta-analytic test of
  intergroup contact theory. *JPSP* 90:751.
- Pettigrew, T. F. (2009). Secondary transfer effects of intergroup
  contact. *Annual Review of Psychology* 60:121.
- Ross Arguedas, A., Robertson, C. T., Fletcher, R., & Nielsen, R. K.
  (2022). *Echo Chambers, Filter Bubbles, and Polarisation: A
  Literature Review*. Reuters Institute.
