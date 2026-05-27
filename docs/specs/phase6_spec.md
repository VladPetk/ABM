# Phase 6 Implementation Spec — Repulsion and the "Null Levers" Library

*Builds on Phase 5 (affect as a first-class channel). Phase 6 is the
honesty phase: it (a) makes **backlash repulsion** a real, affect-gated
mechanism — Bail et al. 2018's backfire effect, conditional on existing
animus — and (b) ships a small library of **named interventions** the
eventual web product will let the user click, each tagged with whether
it actually reduces polarization in the model. The intellectual payoff
is the contrast: most interventions a naive observer expects to help
either do nothing or backfire. The model shows it.*

*Unlike Phases 4-5 (which added mechanisms and rewrote rule semantics),
Phase 6 mostly composes existing rules and adds metadata. The
measure-then-bless gate (§11) is where each intervention's "null /
partial / real" tag is **empirically blessed**, not declared.*

---

## 1. Scope and decisions pinned

Three groups: (R1) affect-gated repulsion; (R2) a library of post-S4
interventions; (R3) an honesty schema on `Intervention`.

| # | Decision | Choice |
|---|----------|--------|
| R1 | **Affect-gated repulsion (Bail backfire).** `BacklashRepulsion` is rewritten to read `agent.state.attrs["affect"]` per out-party neighbour. When the agent's warmth toward that party is below `affect_threshold` (default `-0.3`), the encounter contributes a **repulsive** push proportional to `(-warmth)` and to the existing ring-shaped `strength` (already on the rule). Above the threshold (warmth ≥ -0.3 — neutral or warm), no repulsion fires. In-party neighbours never contribute repulsion. Mechanistically: an already-hostile agent meeting an out-party member doesn't update *toward* them via the graded filter (Phase 5 A4 mutes that pull) — instead, the encounter produces measurable identity-threat-driven push *away*. This is the **honest backfire model**: it fires conditionally, not universally. Existing default `strength = 0.05` carried over; `affect_threshold = -0.3` is new. |
| R2 | **Bundle `BacklashRepulsion` into the pillar superset.** It is added to `build_engine`'s rule list at `strength = 0.0` (an exact no-op). S0-S4 bundles carry `("BacklashRepulsion", "strength", 0.0)` and `("BacklashRepulsion", "affect_threshold", -0.3)`. The repulsion mechanism is **off in the pillar's baseline progression** — it is an *intervention* knob, not a baseline force. (R3 interventions can turn it on selectively.) |
| R3 | **A library of named post-S4 interventions** lives in `abm/pillars/interventions_phase6.py`. Each is an `Intervention` (Phase 1 D5 machinery, unchanged). All operate as **release-phase bundles**: applied at the end of a full S0-S4 polarization run, then run for `TICKS` more. The library ships with **5 interventions**: cross-cutting exposure boost, algorithmic-feed reset, civility nudge, elite cooling, and anchor renewal. (Details in §6.) |
| R4 | **Honesty schema extension on `Intervention`.** `Intervention.label_kind` gains three new permitted values — `"null"`, `"partial"`, `"real"` — alongside the existing `"control"`, `"replication"`, `"illustrative"`. A new optional field `expected_naive_effect` documents the intuitive claim ("would shrink the gap between camps"); the existing `predicted_effect` documents what the model actually produces. The web layer will later render the tag as colour-coded copy. |
| R5 | **What "null / partial / real" mean operationally.** Define a single intervention-effect metric: **`Δparty_separation` after `TICKS` of release**, ensemble mean across `STAGE_SEEDS`. The **helpful direction for `issue_sorting` is negative Δsep** (camps closer). Buckets (Phase 8c D2 sign-convention fix; matches `_classify_sep` in `tests/test_phase6.py`): `|Δsep| < 0.05` → **null**; `−0.15 < Δsep < −0.05` → **partial** (helpful, modest); `Δsep ≤ −0.15` → **real** (helpful, substantial); `Δsep > +0.05` → **backfire** (camps further apart). The `affect` axis adds a second classifier (Phase 7): helpful direction = positive Δaff (warmth recovers — note the sign flip from Δsep). Each intervention's measured bucket is set by the §11 calibration, not declared at design time. |
| R6 | **No new rule classes.** R1 is a `BacklashRepulsion` edit. R3 interventions all express through existing rules. |

**Out of scope.**

- A web/UI builder for custom interventions (the `Intervention` type already supports user-defined bundles; the UI is post-Phase-7).
- Multi-axis interventions targeting specific cohorts (cohort plumbing exists since Phase 1 but is unused; activating it is Phase 7 or 8).
- Real-world calibration of intervention strengths (Phase 7).
- Repulsion as a *symmetric* (two-way) update — the current model only updates the focal agent's position, matching how every other rule operates.

---

## 2. Files

```
modify  abm/rules/repulsion.py            # R1: affect-gated repulsion
modify  abm/pillars/calm_to_camps.py      # add BacklashRepulsion to pipeline; bundle entries
modify  abm/pillars/intervention.py       # R4: extend label_kind, add expected_naive_effect
modify  abm/pillars/__init__.py           # export the Phase 6 library
create  abm/pillars/interventions_phase6.py  # R3: 5 named interventions
create  tests/test_phase6.py              # R1 unit + R3 per-intervention effect tests
modify  tests/test_pillar_stages.py       # the affect-channel-inert test updated to include BacklashRepulsion
modify  tests/conftest.py                 # release-phase helper for intervention measurement
create  scripts/phase6_calibration.py     # §11 measure-then-bless harness
```

`abm/core/*`, `abm/rules/influence.py`, `tie_rewiring.py`,
`affective_update.py`, the canonical / machinery / network / Phase 4 /
Phase 5 test modules: **no change** — verify.

---

## 3. R1 — Affect-gated `BacklashRepulsion`

### 3.1 The rule rewrite

```python
class BacklashRepulsion:
    def __init__(
        self,
        epsilon: float = 0.3,
        max_range: float = 1.5,
        strength: float = 0.05,
        affect_threshold: float = -0.3,
    ):
        self.epsilon = epsilon
        self.max_range = max_range
        self.strength = strength
        # Phase 6 R1: out-party neighbours only contribute repulsion
        # when the agent's warmth toward their party is below this
        # threshold. Default -0.3 means "noticeably cold but not extreme."
        # Set to +inf to fire on every out-party encounter (the old
        # un-gated behaviour); -inf to disable.
        self.affect_threshold = affect_threshold

    def apply(self, agent, space, env, rng):
        if self.strength == 0:
            return StateDelta()
        neighbours = neighbor_agents(agent, space, env)
        if not neighbours:
            return StateDelta()

        own_party = agent.state.attrs.get("party")
        own_affect = agent.state.attrs.get("affect") or {}
        push = np.zeros(2)
        count = 0
        for n in neighbours:
            other = n.state.attrs.get("party")
            # In-party neighbours and party-less agents never contribute
            # to backlash — backfire is an out-party identity-threat
            # mechanism.
            if other is None or other == own_party:
                continue
            warmth = float(np.clip(own_affect.get(other, 0.0), -1.0, 1.0))
            if warmth >= self.affect_threshold:
                # Not hot enough — no backfire from this encounter.
                continue
            diff = agent.state.ideology - n.state.ideology
            d = float(np.linalg.norm(diff))
            # Keep the [epsilon, max_range] ring semantics — too-close
            # = below ideological distance threshold; too-far = no
            # exposure. Macy-Flache.
            if d <= self.epsilon or d > self.max_range or d < 1e-9:
                continue
            # Push magnitude scales with how cold the agent feels — a
            # mildly-cold agent pushes a bit, a -1 (clip-floor) agent
            # pushes the most. The (1 / d²) factor preserves the existing
            # inverse-square ring profile.
            magnitude = (-warmth) / (d * d)
            push += magnitude * diff
            count += 1

        if count == 0:
            return StateDelta()
        d = self.strength * push / count
        # F1: Friedkin-Johnsen scaling — stubborn agents move less.
        s = float(agent.state.attrs.get("stubbornness", 0.0))
        return StateDelta(d_ideology=(1.0 - s) * d)
```

### 3.2 Why affect-gated, not universal

The pre-Phase-6 `BacklashRepulsion` fires for every neighbour in the
`[epsilon, max_range]` ring — i.e. it always pushes away from out-party
agents in that distance band, regardless of affect. That is the
Macy-Flache 1997/2003 *theoretical* mechanism; the empirical evidence is
more conditional:

- **Bail et al. 2018 (PNAS):** exposure to opposing partisans on Twitter
  *increases* polarization for Republicans. Reading: backfire is real but
  conditional on prior animus and on the salience of identity threat.
- **Guess et al. 2023 / Nyhan et al. 2023:** the Meta/2020 study found
  no average effect of algorithmic feed reduction on issue or affective
  polarization. Reading: most cross-cutting exposure has *null* effect
  at population scale.
- **Levendusky 2021 (Our Common Bonds):** under the right conditions
  (warm framing, depoliticised commonality), cross-cutting exposure
  *reduces* affective polarization. Reading: backfire is not the default
  — it is conditional.

Affect-gating expresses all three findings in one mechanism: when affect
is hot, backfire fires (Bail); when it isn't, exposure either does
nothing (Guess/Nyhan) or modestly attracts (Levendusky, expressed
through Phase 5's A1 affect dynamics + the BC graded filter — not the
repulsion rule). The default threshold `-0.3` is the modelling judgment;
it's a starting value, calibrated in §11.

### 3.3 Decision (judgment fork R1a) — affect_threshold

`affect_threshold = -0.3`. Mild-to-moderate animus triggers backfire.
Alternatives:
- `-0.5`: only triggers for strongly cold agents (Bail-like; majority of
  the population wouldn't backfire).
- `-0.1`: triggers easily (any negative affect; closer to universal
  repulsion).

The pillar's S2-S4 calibration showed mean affect lands around -0.85 at
S2/S3 (well past -0.3), so the gate fires *broadly* once the pillar has
run — by design. In the **release phase** of post-S4 interventions, the
gate stays active because affect persists. So R1's effect is felt
strongest when interventions deliberately *expose* agents (R3's
cross-cutting boost).

### 3.4 Decision (judgment fork R1b) — push magnitude scaling

Linear scaling: `magnitude = (-warmth) / d²`. A `-1` (clip floor) agent
pushes at full inverse-square strength; a `-0.3` (just past threshold)
agent pushes at 30%. Alternative: quadratic `(-warmth)² / d²` — sharper
backfire for the angriest agents; the broad-mass effect is small.

---

## 4. R2 — Pillar wiring

### 4.1 `build_engine` adds `BacklashRepulsion` at strength 0

```python
rules = [
    BoundedConfidenceInfluence(...),
    PartyPull(strength=0.0),
    MediaConsumption(strength=0.0),
    AffectiveUpdate(...),
    IdentitySorting(...),
    BacklashRepulsion(strength=0.0, affect_threshold=-0.3),   # NEW
    GaussianNoise(sigma=0.01),
]
```

`strength = 0.0` is an exact no-op (the rule's `if self.strength == 0`
short-circuit). The pillar's S0-S4 *never* turn it on — Phase 6
interventions do, by applying a bundle that sets
`("BacklashRepulsion", "strength", X)`.

### 4.2 All 5 existing S0-S4 bundles add two entries

```python
("BacklashRepulsion", "strength", 0.0),
("BacklashRepulsion", "affect_threshold", -0.3),
```

The absolute-bundle discipline (Phase 1 D5): every bundle lists every
tunable. New entries are required for `apply_intervention` to be able to
turn them on/off cleanly.

### 4.3 No behavioural change to S0-S4

`BacklashRepulsion.strength = 0.0` in every existing stage → existing
pillar tests pass unchanged at the same thresholds. Confirmed via the
"strength == 0 is exact no-op" property of the rule's first line.

---

## 5. R3 — The intervention library

### 5.1 Module layout

`abm/pillars/interventions_phase6.py` exports an immutable
`INTERVENTIONS_PHASE6` tuple of 5 `Intervention` objects, each starting
from the **S4 bundle** (the polarized end-state of the pillar) and
overriding selected entries.

Each carries:

- `id` — stable identifier (e.g. `"X_cross_cutting_exposure"`).
- `label` — human name ("Show people the other side").
- `description` — one plain-English sentence.
- `expected_naive_effect` — the intuitive claim ("People would soften
  toward the out-party once they see them as individuals").
- `predicted_effect` — the model's actual prediction (what §11 will
  measure).
- `citation` — the paper(s).
- `label_kind` — initially `"illustrative"`; **§11 re-blesses it to
  `"null"`, `"partial"`, `"real"`, or `"backfire"`** based on the
  measured `Δparty_separation`.
- `param_bundle` — absolute, full bundle.

### 5.2 Design principle (revised for the public-facing product)

Each intervention must satisfy three constraints:

1. **Public legibility.** Named after a real-world lever a lay reader
   has heard of and would intuitively expect to reduce polarization.
   No "anchor renewal" or "elite cooling" — those are mechanisms, not
   levers. Names map to things people argue about at dinner.
2. **Literature grounding.** Each carries a real, published citation
   from `political_polarization_research.md` or `s4_network_research.md`.
   The empirical record is what blesses the bucket — not the
   implementer's intuition.
3. **Clean model mechanism.** Each toggles existing parameters or uses
   the `Intervention.setup` hook. No engine changes required.

The set is chosen for **bucket diversity** — at least one null, one
partial, one real, one backfire — so the demo isn't all-doom and the
educational contrast is sharp.

### 5.3 The 5 interventions

#### X1 — "Show people the other side"

Cross-partisan exposure: campaigns, social-media outreach, "befriend
someone across the aisle," news feeds that surface opposing voices.

- **What it represents:** the most-discussed depolarization proposal in
  public discourse. Programs like Hidden Brain's "Across Party Lines,"
  algorithmic interventions surfacing out-party content, "exposure
  diets" recommended in popular books.
- **Mechanism (R1 activation):** turn on `BacklashRepulsion` at
  `strength = 0.05`. The R1 affect-gate fires because S2-S4 leaves mean
  out-party affect well below the `-0.3` threshold — so increased
  out-party encounters convert to push-away, not pull-toward.
- **Bundle delta from S4:** `("BacklashRepulsion", "strength", 0.05)`.
- **Expected naive effect:** "Seeing the other side will humanise them
  and reduce out-party hostility."
- **Predicted effect (Bail 2018):** "Backfire. Exposure to opposing
  views *increases* polarization for already-hostile agents — the
  bigger the dose, the worse the backfire."
- **Label after §11:** TBD (expect **backfire**).
- **Citations:** Bail et al. 2018 (*PNAS* 115:9216); Levendusky 2021
  (*Our Common Bonds*); Mutz 2006 (*Hearing the Other Side*).

#### X2 — "Fix the algorithm"

Reset social-media feeds to chronological / non-curated; ban or
constrain algorithmic recommendation. The flagship policy ask of the
last decade.

- **What it represents:** the EU Digital Services Act, the US "Filter
  Bubble Transparency Act," the Meta/Instagram chronological-feed toggle,
  every op-ed about "the algorithm" radicalizing people.
- **Mechanism (A4 deactivation):** zero
  `BoundedConfidenceInfluence.affect_weight` — the model's analog of
  the algorithmic muting of hostile-affect content disappears; agents
  again weight all network neighbours by graded confidence alone.
- **Bundle delta from S4:**
  `("BoundedConfidenceInfluence", "affect_weight", 0.0)`.
- **Expected naive effect:** "Without the algorithm amplifying our
  divisions, polarization will subside."
- **Predicted effect (Guess et al. 2023; Nyhan et al. 2023):** "Null.
  The Meta/US 2020 Election Study switched users to chronological
  feeds for 3 months and found essentially no effect on issue or
  affective polarization. The polarization lives in the *people* and
  the *network structure*, not in the feed."
- **Label after §11:** TBD (expect **null**).
- **Citations:** Guess et al. 2023 (*Science* 381:398); Nyhan et al.
  2023 (*Nature*); Ross Arguedas et al. 2022 (Reuters Institute review).

#### X3 — "Quit cable news"

Disengage from partisan media: stop watching Fox/MSNBC, deactivate
social media, switch to "balanced" sources.

- **What it represents:** the Allcott et al. 2020 "deactivate Facebook
  for a month" experiment; advice columns telling people to detox from
  cable news; the broader "media diet" discourse.
- **Mechanism (S3 reversal):** zero `MediaConsumption.strength` — agents
  stop being pulled toward their partisan diet's centroid. Equivalent
  to "everyone stops following partisan media" at the population level.
- **Bundle delta from S4:** `("MediaConsumption", "strength", 0.0)`.
- **Expected naive effect:** "Without partisan media driving people to
  extremes, the country will heal."
- **Predicted effect (Allcott et al. 2020; Levendusky 2013):**
  "Partial. Heavy-media-diet agents stop extremising further (Allcott
  found small but real effects on Facebook deactivation), but the
  *already-sorted* network and party identities remain — the polarized
  state is sticky. Issue positions slowly relax; affect barely moves."
- **Label after §11:** TBD (expect **partial**).
- **Citations:** Allcott, Braghieri, Eichmeyer & Gentzkow 2020 (*AER*
  110:629); Levendusky 2013 (*AJPS* 57:611, reverse direction).

#### X4 — "Bipartisan dialogue programs"

Structured cross-party conversations: Braver Angels, More in Common,
Living Room Conversations, depolarization weekends.

- **What it represents:** a real, growing class of NGOs and academic
  interventions. Levendusky (2021, *Our Common Bonds*) — the strongest
  evidence that warmly-framed cross-party contact can reduce affective
  polarization.
- **Mechanism (structural, via `setup`):** add a stratum of
  **voluntary** cross-party ties at intervention time (representing the
  agents who participate in dialogue programs — a small share of the
  population), AND reset those participants' out-party affect toward
  zero (the "warm framing" that distinguishes Levendusky from Bail).
  Two-step:

  ```python
  def setup(engine, n_dialogue=20, rng_seed=42):
      rng = np.random.default_rng(rng_seed)
      net = engine.env.attrs["network"]
      participants = rng.choice(
          [a.id for a in engine.agents], size=n_dialogue * 2, replace=False
      )
      by_id = {a.id: a for a in engine.agents}
      # Pair participants across party; add a tie and zero their affect.
      left = [i for i in participants if by_id[i].state.attrs["party"] == 0]
      right = [i for i in participants if by_id[i].state.attrs["party"] == 1]
      for i, j in zip(left, right):
          if not net.has_edge(i, j):
              net.add_edge(i, j, involuntary=False)
          # Warm framing — reset to neutral, don't make warmer (no in-
          # party update either; honest about Levendusky's modest finding).
          by_id[i].state.attrs["affect"][1] = 0.0
          by_id[j].state.attrs["affect"][0] = 0.0
  ```
- **Bundle delta from S4:** none (the change is via `setup`).
- **Expected naive effect:** "Sitting people down with the other side
  in a structured setting will rebuild trust."
- **Predicted effect (Levendusky 2021):** "Partial. Among
  *participants*, affect cools and cross-cutting ties grow. At the
  population level, the effect is small because participation is a
  minority. Issue-position sorting barely moves; affective polarization
  ticks down modestly."
- **Label after §11:** TBD (expect **partial**).
- **Citations:** Levendusky 2021 (*Our Common Bonds*); Mutz 2006
  (*Hearing the Other Side*); also the More in Common / Braver Angels
  reports.

#### X5 — "Ranked-choice voting"

Electoral reform: ranked-choice ballots, open primaries, proportional
representation. Reform proposals widely associated with depolarization
(FairVote, Unite America, the McCoy & Somer 2019 institutional thesis).

- **What it represents:** the "institutions" critique — the US's
  majoritarian/winner-take-all system structurally amplifies polarization
  versus proportional democracies. RCV and open primaries are the most
  legible reform proposals. The model can't simulate elections directly,
  but RCV's *mechanism of action* is "remove the incentive for elites to
  stake out extreme positions" — the elite-divergence channel
  documented by Hetherington 2001 and McCarty/Poole/Rosenthal 2006.
- **Mechanism (elite cooling, via `setup`):** reset both party centroids
  toward the centre. RCV's modelled effect = "elites no longer have to
  cater to ideological primary electorates."

  ```python
  def setup(engine):
      # Pull centroids halfway to centre — RCV doesn't erase party,
      # it removes the *amplification* of extremes.
      for pid, centroid in list(engine.env.attrs["parties"].items()):
          engine.env.attrs["parties"][pid] = 0.5 * centroid
  ```
- **Bundle delta from S4:** none (the change is via `setup`).
- **Expected naive effect:** "Reforming elections will reduce the
  incentive for politicians to play to the extremes, and the mass
  public will follow."
- **Predicted effect (Hetherington 2001 reverse; Gidron, Adams & Horne
  2020; McCoy & Somer 2019):** "Real on issue position. With party
  centroids halved, `PartyPull` now pulls toward more moderate
  centroids; ideological constraint and party separation drop
  meaningfully over the release period. Affective polarization barely
  responds — sticky, as the cross-national evidence predicts (Gidron
  et al. 2020: institutional change moves issue sorting more than
  affect)."
- **Label after §11:** TBD (expect **real** for issue / party
  separation; **null** for affect).
- **Citations:** Hetherington 2001 (*APSR* 95:619); McCarty, Poole &
  Rosenthal 2006 (*Polarized America*); Gidron, Adams & Horne 2020
  (*American Affective Polarization in Comparative Perspective*);
  McCoy, Rahman & Somer 2018; McCoy & Somer 2019 (*Annals of AAPSS*).

### 5.4 Why these five (the bucket spread)

| ID | Lay name | Predicted bucket | Why it's in |
|----|----------|------------------|-------------|
| X1 | "Show people the other side" | backfire | The *most-believed* intervention in popular discourse — and the most thoroughly disproven by Bail 2018. The killer demo. |
| X2 | "Fix the algorithm" | null | The flagship policy proposal of the last decade — and the Meta/2020 study said it doesn't work. The second killer demo. |
| X3 | "Quit cable news" | partial | A self-help-style intervention; honest about modest real effects (Allcott found ~0.04 SD reductions). Shows the demo isn't all-cynical. |
| X4 | "Bipartisan dialogue programs" | partial | Levendusky's evidence that *warmly-framed* contact works — distinguishes X4 from X1's cold exposure. The "what kind of contact matters" story. |
| X5 | "Ranked-choice voting" | real | The institutional critique. Shows that *system-level* reforms can move issue sorting where individual-level interventions can't. The lever that actually has length. |

The set tells a coherent story for a lay audience: **the things people
most loudly demand (X1, X2) don't work; the things people quietly try
themselves (X3, X4) help modestly; the lever with real length (X5)
requires institutional change.** That arc is the intellectual payoff —
not a generic "everything you tried is wrong" cynicism, but a calibrated
picture grounded in the empirical record.

---

## 6. R4 — `Intervention` schema extension

### 6.1 The change

```python
@dataclass(frozen=True)
class Intervention:
    id: str
    label: str
    description: str
    param_bundle: tuple[ParamChange, ...]
    label_kind: str = "illustrative"
    # Phase 6: empirically-blessed honesty tag. Allowed values:
    # "control" | "replication" | "illustrative" |
    # "null" | "partial" | "real" | "backfire"
    citation: str = ""
    predicted_effect: str = ""
    # Phase 6: the intuitive expectation a naive observer would have.
    # The Δ between this and `predicted_effect` is the educational
    # payoff of an intervention. Optional — pillar stages (S0-S4) don't
    # use it.
    expected_naive_effect: str = ""
    setup: Optional[Callable] = None
```

`label_kind` is still a string (no enum), but `apply_intervention` and
`tests/test_machinery.py` don't depend on its value — it's metadata
for downstream readers (the web layer eventually). No validation is
added: a future intervention can label itself anything; the §11
calibration is what blesses the tag.

### 6.2 `expected_naive_effect`

A new optional string. Phase 1-5 `Intervention` objects don't set it;
the pillar stages don't need it (S0-S4 are not "interventions" in the
user-clicks-button sense). Phase 6's library is the first consumer.

### 6.3 No machinery change

`apply_intervention` is unchanged — it still reads `param_bundle` and
calls `setup`. The new fields are read by metadata consumers only.

---

## 7. Tests

### 7.1 New: `tests/test_phase6.py`

Eight tests.

**R1 — affect-gated repulsion.**

- `test_backlash_at_zero_strength_is_inert`: build at S4, set
  `BacklashRepulsion.strength = 0.0`, run TICKS, compare to a Phase 5
  S4 run — positions bit-identical. Regression guard: the new rule
  must remain a no-op at strength 0.
- `test_backlash_does_not_fire_above_affect_threshold`: hand-built
  two-agent setup, agent's affect to out-party = 0.0 (above threshold
  -0.3); `BacklashRepulsion(strength=0.05)` produces zero
  `d_ideology`.
- `test_backlash_fires_below_affect_threshold`: same setup, affect =
  -0.5 (below threshold); `BacklashRepulsion` produces a non-zero
  push *away from* the out-party neighbour.
- `test_backlash_skips_in_party_neighbours`: same hand-built setup with
  an in-party neighbour at the same distance and the agent's affect at
  0; rule produces zero push. (In-party neighbours never trigger
  backfire — Bail's mechanism is identity-threat-driven.)

**R3 — intervention bundles.**

- `test_each_intervention_is_well_formed`: every intervention in
  `INTERVENTIONS_PHASE6` has a non-empty `id`, `label`,
  `expected_naive_effect`, `predicted_effect`, and either a non-empty
  `param_bundle` or a non-None `setup`.
- `test_apply_intervention_preserves_pipeline_structure`: applying any
  X-intervention to a post-S4 engine doesn't add or remove rules; the
  pipeline shape is invariant (Phase 1 D6 ⇒ at most one instance per
  class). Confirmed by checking the rule classes set before and after.

**R4 — honesty schema.**

- `test_intervention_supports_label_kind_null`: construct an
  `Intervention` with `label_kind="null"`; no error. Same for
  `"partial"`, `"real"`, `"backfire"`. Sanity that the schema doesn't
  reject the new values.

**§11 calibration (one consolidated test).**

- `test_intervention_library_directions_hold`: for each intervention,
  run the release-phase experiment (12 seeds, TICKS post-S4); assert
  that the measured `Δparty_separation` lies in the bucket the
  intervention's `label_kind` declares (after §11 has blessed the
  labels). E.g. X2 (feed reset) labeled `"null"` ⇒ |Δsep| < 0.05; X4
  (elite cooling) labeled `"real"` ⇒ Δsep ≥ 0.15 helpful direction.
  This is the empirical assertion that the library's tags match what
  the model does. If a future change shifts an intervention's measured
  effect out of its bucket, this test fails — and the spec calls for
  re-blessing (move the tag, not the threshold).

### 7.2 Regression guards (must still pass)

- **Canonical HK** suite — unchanged. `BacklashRepulsion` is added to
  the pillar's pipeline but not to `compass_basic` (which constructs
  its own pipeline). Non-pillar scenarios untouched.
- **Phase 4 / Phase 5** suites — unchanged. `BacklashRepulsion.strength
  = 0.0` in every S0-S4 bundle makes the rule an exact no-op for
  baseline-progression tests.
- **Machinery** — unchanged. The new rule has no RNG dependency
  (deterministic).
- **`test_positional_fast_path_is_a_faithful_approximation`** — extend
  the fast path to also zero `BacklashRepulsion.strength` (it would be
  zero anyway under the S0-S4 bundles, but a future intervention test
  using `positional_engine` could trip on it).

### 7.3 `tests/conftest.py` — release-phase helper

```python
def release_run(intervention, seed):
    """Run S0→S4 (TICKS each), then apply intervention, then run TICKS
    more. Returns the engine at the end of the release phase."""
    eng = build_at_stage(PILLAR, 4, seed=seed)
    eng.run(TICKS)
    apply_intervention(eng, intervention)
    eng.run(TICKS)
    return eng
```

Used by the consolidated calibration test and the calibration script.

---

## 8. Build sequencing

- **Slice 1 — R1.** Rewrite `BacklashRepulsion`. Add to pipeline at
  strength 0. Add `("BacklashRepulsion", "strength", 0.0)` and
  `("BacklashRepulsion", "affect_threshold", -0.3)` to every existing
  bundle. Gate: full Phase 5 suite green; R1 unit tests green.
- **Slice 2 — R4.** Extend `Intervention` with
  `expected_naive_effect`. Allow `label_kind` values to include the new
  honesty tags (no enum, no validation). Gate: machinery tests pass;
  schema test passes.
- **Slice 3 — R3.** Create `interventions_phase6.py` with the 5
  interventions. Run the §11 measurement, bless each label_kind, write
  the consolidated bucket test. Gate: full suite green; calibration
  bucket test passes for the blessed labels.

---

## 9. Re-validation — measure, then bless

After Slice 3 is green, the implementer measures and reports, for each
intervention at 12-seed ensemble, TICKS post-S4:

1. **Δparty_separation** (the headline polarization metric — same as the
   ratchet test).
2. **Δcross_cutting_tie_fraction** (does the network re-mix?).
3. **Δaffective_polarization** (does affect cool?).
4. **Δideological_constraint** (does sorting unwind?).
5. **Δvariance** (does the population spread?).

Then assign each intervention a `label_kind`. **Sign convention
(Phase 8c D2 fix):** report `Δsep` as `sep_after − sep_S4_end`. The
helpful direction is **negative** Δsep (separation falls — camps
closer). The buckets are:

- `|Δsep| < 0.05` → `"null"`.
- `−0.15 < Δsep < −0.05` → `"partial"` (helpful, modest).
- `Δsep ≤ −0.15` → `"real"` (helpful, substantial).
- `Δsep > +0.05` → `"backfire"` (separation rises).

(Earlier drafts of this section used the inequalities `effect ≥
0.15` and `Δsep ≥ -0.15` for "real," which are the wrong direction
for the helpful sign convention; the implementation in
`tests/test_phase6.py::_classify_sep` always used `dsep <= -0.15`,
which is correct. Phase 8c D2 brings the spec text in line with the
implementation.)

Then commit the labels into `interventions_phase6.py`'s
`label_kind` fields and into the consolidated bucket test's expected
values. **The labels are blessed by measurement, not declared by
design** — that is the honesty discipline.

**Two extra reports for the user before committing:**

6. **Phase 5 thresholds unchanged.** S0-S4 pillar suite must still pass
   at the same thresholds (BacklashRepulsion stays off during the
   pillar's baseline progression).
7. **Canonical HK unchanged.** `compass_basic` doesn't include
   `BacklashRepulsion` in its pipeline (it has its own pipeline with
   `BacklashRepulsion(epsilon, max_range, repulsion=0.0)`); the
   affect-gated path is only taken when `strength > 0`. Verify the
   `repulsion=0` default produces the same outputs.

---

## 10. Judgment forks — flagged for explicit confirmation

| ID | Decision | Default | Alternatives |
|----|----------|---------|--------------|
| R1a | `affect_threshold` for repulsion firing | `-0.3` (mildly cold) | `-0.5` (only strongly cold agents backfire); `-0.1` (almost any negative affect triggers); off (universal repulsion — pre-Phase-6 behaviour) |
| R1b | Push magnitude scaling | linear `(-warmth)/d²` | quadratic `(-warmth)² /d²`; binary on/off |
| R2a | `BacklashRepulsion` in the pillar's S0-S4 bundles | at strength 0 (off) — repulsion is an intervention knob, not a baseline force | at low non-zero strength in S2-S4 (treat backfire as a baseline reality); leave the rule out of the pipeline (then interventions can't activate it cleanly) |
| R3a | Which 5 interventions ship in v1 | **REVISED** for public-facing legibility: X1 "Show people the other side" (backfire), X2 "Fix the algorithm" (null), X3 "Quit cable news" (partial), X4 "Bipartisan dialogue programs" (partial), X5 "Ranked-choice voting" (real) — each a recognisable real-world lever; each with a published citation; bucket spread covers null/partial/real/backfire | Drop X3 or X4 to keep four; add a 6th "do nothing" control; add a "geographic mixing" (Bishop's Big Sort reversal — would map to lower-homophily rewiring) |
| R3b | X1's mechanism for "show people the other side" | turn on `BacklashRepulsion` at `strength = 0.05` (the R1 affect-gated path then converts the increased exposure to backfire — Bail 2018) | raise `n_candidates` in `TieRewiring` (more random encounters); add cross-party involuntary edges at runtime; both achieve "more exposure" but lose the R1 backfire mechanism — the chosen mechanism is the cleanest test of R1 |
| R3c | X4 "Bipartisan dialogue programs" — number of participants | 20 pairs (40 agents, ~16% of n=250); 1× tie added per pair; affect reset to 0.0 (warm framing — neutral, not warm) | More pairs (population-level effect grows); fewer (more honest about minority-participation reality); add an in-party warmth bump (departs from Finkel's "in-party warmth is stable" finding) |
| R3d | X5 "Ranked-choice voting" — centroid pull strength | half-way to centre (`0.5 * centroid`) — RCV doesn't erase party, it moderates elites | all the way (centroids to [0, 0] — extreme reform); 0.75 × (mild reform); per-axis (only the economic axis cools, leaving culture salient) |
| R4a | Honesty schema | extend `label_kind` with new strings | add a separate `honesty: str` field (more explicit but uglier); add an enum (more rigid; the project has been string-typed throughout) |
| R5a | Effect-bucket thresholds (null / partial / real / backfire) | 0.05 / 0.15 cutoffs on `Δparty_separation` | tighter (0.03 / 0.10); looser (0.10 / 0.25); per-intervention thresholds (defeats the schema) |
| R5b | The metric used to assign buckets | `Δparty_separation` post-release vs. S4-end | average of party_separation + affective_polarization + ideological_constraint; multi-metric bucketing |

If the user does not override one before implementation begins, the
default is taken.

---

## 11. Supersedes, open items, done checklist

**Supersedes.** Nothing — Phase 6 is purely additive. Phase 5 invariants
all preserved (Phase 5 unit tests must still pass).

**Open items (deferred).**

- Custom user-built interventions (the `Intervention` machinery
  already supports it; spec-ing the UI is post-Phase-7).
- Multi-step / sequential interventions (apply X1, run, apply X4, run).
- Cohort-targeted interventions (only intervene on the most-extreme
  10% of agents). Phase 7 or 8.
- Tick-to-real-time calibration. Phase 7.

**Done checklist.**

- [ ] R1: `BacklashRepulsion` rewritten with `affect_threshold`; defaults
      `0.05` strength + `-0.3` threshold; in-party skip; F1 scaling.
      Four R1 unit tests pass.
- [ ] R2: `BacklashRepulsion` added to `build_engine`'s rule list at
      strength 0; every S0-S4 bundle carries the two new entries; all
      Phase 5 tests still pass at unchanged thresholds.
- [ ] R3: `interventions_phase6.py` exists with 5 well-formed
      `Intervention` objects; export from `abm/pillars/__init__.py`.
- [ ] R4: `Intervention` dataclass extended with `expected_naive_effect`;
      `label_kind` accepts the new tags; schema sanity test passes.
- [ ] §11 measure-then-bless: each intervention's `Δparty_separation`
      (+ four secondary metrics) measured; `label_kind` blessed by
      measurement; consolidated bucket test passes with the blessed
      labels.
- [ ] Canonical HK / machinery / Phase 4 / Phase 5 tests still pass at
      the same thresholds.
- [ ] Position histogram still shows "no collapse" at S4 end (Phase 4
      §12). Repulsion is off during the baseline, so this is automatic
      but worth confirming.
- [ ] Behavioural expectations confirmed: the bucket spread holds —
      X1 ("Show people the other side") is **backfire** (Bail 2018);
      X2 ("Fix the algorithm") is **null** (Guess/Nyhan 2023);
      X3 ("Quit cable news") and X4 ("Bipartisan dialogue") are
      **partial** (Allcott 2020; Levendusky 2021); X5 ("Ranked-choice
      voting") is **real** on issue sorting and **null** on affect
      (Gidron et al. 2020). If any intervention's measured bucket
      doesn't match its citation's empirical finding, surface it as a
      modelling issue — the calibration is what blesses the tag, but a
      direction inversion against Bail/Guess/Levendusky would be a
      finding worth flagging.
- [ ] Judgment forks (R1a, R1b, R2a, R3a, R3b, R4a, R5a, R5b)
      confirmed by the user or noted as defaulted.
- [ ] No UI / website file touched.

With Phase 6 done and signed off, the engine carries an empirical
library of named interventions — each tagged honestly with what it
*actually does* in the model, not what an observer expects. Phase 7
(calibration of tick-to-real-time and per-agent step sizes) then comes
on top of a model that already produces the right *qualitative*
catalog of polarization mechanisms, sorting dynamics, and intervention
outcomes.
