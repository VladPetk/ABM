# polarlab — project guide for Claude

polarlab is an **agent-based model (ABM) of US political polarization** over a
stylised ~1980 → 2025 window, plus a public-facing web demo that visualizes it.
It models how a two-party society sorts into camps across several coupled
channels — ideology, party identity, affect (out-party animus), partisan media,
and social-network structure — and what real-world depolarization interventions
do when applied. It's grounded in the empirical literature: every calibration
choice is anchored to a published finding, and it's a **teaching artefact, not a
policy-prediction tool** — results are illustrative within a citation envelope,
and limitations are documented rather than hidden.

There are two tracks in this repo, and most sessions touch only one:

1. **Engine** — pure Python (`numpy`/`scipy`), under `abm/`. The simulation,
   rules, calibration, and tests.
2. **Web demo** — a static, build-free React page under `web_demo/`. Reads a
   repacked snapshot of the engine's output; runs no simulation itself.

> **Scope note:** whether a given session may modify the engine is
> session-dependent — confirm from the task if unclear. Many web sessions are
> explicitly *frontend-only* ("the engine is fine as-is"); in those, treat
> `abm/` and the data pipeline as read-only and work only in `web_demo/`. Don't
> assume either way.

---

## Repo map

```
abm/            the engine — core/ rules/ pillars/ scenarios/ metrics/
data/           literature PDFs + phase9 ANES recodes (calibration anchors)
scripts/        measurement sweeps + the web data pipeline
tests/          ~240 tests: small literature-pinned core + band gates + drift guards + machinery (full run ~14 min)
web/data/       full per-tick engine exports (JSON) — pipeline intermediate
web_demo/       the static demo the public sees
docs/           all documentation (see index at the bottom)
```

---

## The engine (`abm/`)

Pure Python, no ABM framework. Fully reproducible — `python -m pytest` runs the
suite. (Honest label, per the T0.2 provenance census: a small literature-pinned
core (~15 tests, e.g. the HK reduction and the ANES thermometer band), a few
empirical-band gates, ~40 blessed-output drift guards, and ~210 machinery
tests. The heavyweight empirical gates — the ANES §11 scorecard and the
Phase 10 bucket measurement — are measure-then-bless *scripts*, not pytest.)
Two top-level scenarios share one rules engine.

### Substrate (ADR-001)
Every agent is **two things at once**: a point in a 2D ideology compass
(`[-1,1]²`, x = economic, y = cultural) **and** a node in a weighted social
network. The defining decision (ADR-001): the **network is the primary
substrate of influence** — interaction rules query "who am I tied to," not "who
is near me in ideology." Ideology space holds state + drives visualization;
influence flows along ties; homophily shapes which ties exist. Classic
Hegselmann–Krause is recovered exactly as the complete-graph special case.

### Agent state
`ideology` (2D), `party` (0 Dem / 1 Rep / Independent), `identity_strength`,
`identities` (cross-cutting race/religion/lifestyle vector), `affect`
(per-out-party warmth, evolves), `media_diet` (weights over outlets), plus the
Friedkin–Johnsen pieces: `anchor` (fixed initial ideology) and `stubbornness`
(most agents barely move; a thin tail moves freely), and `social_coord` (latent
tie-formation anchor).

### Rules pipeline
Each rule emits one `StateDelta` per agent per tick; the engine **sums deltas
across the pipeline and applies them synchronously** — no rule mutates state
directly. Friedkin–Johnsen `(1 − stubbornness)` damping is applied at the
apply-site of every ideology-moving rule. Rules live in `abm/rules/`, e.g.:
`BoundedConfidenceInfluence` (graded logistic neighbour-averaging; affect
modulator), `PartyPull` (elite-cue drift to party centroid), `MediaConsumption`
(drift toward media-diet target), `AffectiveUpdate` (negative-going out-party
valence), `IdentitySorting`/`identity_alignment` (Mason mega-identity stacking),
`BacklashRepulsion` (affect-gated backfire), `TieRewiring` (slow homophilous
network co-evolution), `EliteDrift`, `cohort_replacement`, `threat_dynamics`,
`GaussianNoise` (+ the FJ anchor pull), and the `shocks` mechanism.

### Two scenarios — one rules engine, two jobs
Both run the **same rules** (`abm/rules/`); they differ only in how the rules
are bundled and parameterized.

- **Pillar** (`abm/pillars/calm_to_camps.py`) — the *eventless composition
  control*. The canonical 5-stage journey on one continuous, path-dependent
  population (**S0** baseline → **S1** bounded confidence → **S2** party
  identity → **S3** partisan media → **S4** homophilous network co-evolution,
  the "ratchet"). Each stage turns on one more mechanism, but the stages
  *compound* — by S4 the whole stack runs together — and there are **no dated
  events/shocks**, so any trajectory change is attributable to rule
  *interaction*, not an exogenous handler. Since MHV S2 (T2.5) it runs on the
  D=7 issues substrate with the emergent rule set (`ConstraintOp` from S2,
  `MeasuredAlignment`, no `IdentitySorting`). Pinned by ~73 tests; stable **by
  design, not by decree** (the tests guard against *accidental* drift, not a
  claim it's beyond question). It *can* change — deliberately, for a documented
  reason, with the pinned tests re-validated (expect them to fail and need
  honest re-blessing; precedent: the T2.5 rebuild, methods §5.22). Don't bolt
  unrelated new mechanisms onto its stages: that breaks it as a fixed control
  *and* still wouldn't isolation-test them (see the three layers below).
- **Historical arc** (`abm/pillars/historical_arc.py`, public surface
  `build_engine`) — the *empirical build that ships*. The same rules under
  time-varying schedules + ANES anchors targeting US 1980→2025, with dated event
  /shock handlers (Fox News '96, Tea Party '09, Trump '16, COVID/Jan6 '20…) and
  the 7-intervention library. **Where Phase 9 calibration lives, and what the
  web demo serves** (engine `phase10`, preset `anes_full`, seed 0). Since MHV
  S2 (T2.6) the canonical preset builds the **emergent** engine (`n_issues=7`
  issue substrate + `ConstraintOp`; methods §5.23). Since **emergence-recovery
  E5** the canonical `ANES_FULL_KWARGS` is the **endogenous** build
  (`endogenous_elite=True`, `data_fed_elite=False`, the adopted E4 ABC point):
  positional sorting now *emerges* from the activist→elite→mass loop instead of
  replaying fed centroids (blindspot #7 resolved; methods §5.29). Phase-10 +
  web are re-blessed on it (E5.5/E5.6). The pre-E5 fed config is preserved as
  `ANES_FULL_FED_KWARGS`.

### How rules are drift-guarded — three test layers
A rule's behavior is (or should be) pinned at three distinct levels; each
catches what the others miss, so they don't collapse into one another:

| Layer | Runs | Answers | Where |
|---|---|---|---|
| **Isolation** | one rule, clean substrate | does each rule work *alone*? | `compass_basic` + `test_canonical.py` — today only the Hegselmann–Krause / bounded-confidence reduction; **a systematic per-rule layer is missing** |
| **Composition** | all rules together, continuous, **no events** | do the rules *compound* into the calibrated trajectory? | the pillar (`test_pillar_stages.py`, ~73 tests) |
| **Empirical** | composition **+ dated events/shocks** | the shippable 1980→2025 arc | the historical arc (phase9/phase10 golden tests) — what the web serves |

The pillar's irreducible job is the **middle** layer: it's the only place an arc
regression can be bisected into "rule-interaction bug" vs "event-handler bug,"
because it has the same rules with no exogenous shocks. That's why it can't fold
into the per-rule suite (single-rule ≠ composition) and why new mechanisms
shouldn't pile into it — they belong in the *isolation* layer.

**Two honest caveats.** (1) The isolation layer is incomplete — a few *active*
rules have no behavioral drift-guard, notably **`IdentityAlignment`** (it ships
in the web build and emits the `identity_alignment` metric), plus
`IdentityToIdeologyPull` and `ProtectedPartyRealignment`. The fix is a per-rule
isolation suite (the `compass_basic` pattern), not adding them to the pillar.
(2) The pillar's original teaching/narrative role has largely **migrated to the
arc** now that the arc is what ships; its live justification today is this test
role alone. If the arc's own golden tests were judged sufficient and bisecting
rule-vs-event drift weren't valued, the pillar would be a legitimate
**retirement candidate** — an open call, not a settled fact.

### Metrics (`abm/metrics/`)
Party separation (`sep`), affective polarization (`aff_out`, out-party warmth ∈
[-1,1]), identity alignment, position variance, network modularity, cross-party
tie fraction, plus diagnostics.

### Interventions & the honesty discipline
Seven public-facing levers (**X1–X7**), each a lay-recognisable intervention
mapped to one engine mechanism and labelled by **measurement** on two
independent axes (issue sorting / affect) into buckets
(`null` / `partial` / `real` / `backfire`).

Four honesty rules run through the whole engine and matter when reading or
presenting results:
- **Measure-then-bless.** Bucket tags are set by measurement, not authored.
  Change the engine and the consolidated tests fail loudly — re-bless honestly;
  *"move the tag, not the threshold."* Ground truth for shipped numbers:
  [`docs/results/phase10_results.md`](docs/results/phase10_results.md).
- **Provenance tags.** Each mechanism is tagged **L** (literature-supported),
  **N** (new/design choice), or **E** (extrapolated beyond direct evidence).
  Mechanisms are mostly L; magnitudes mostly the model's; the compounded arc is
  E. See `methods.md` for the full table.
- **Evidence grades on events.** Timeline events carry HIGH/MED/LOW/CONTESTED/
  MARKER grades — present them honestly (e.g. Citizens United is a non-causal
  **MARKER**, not a cause; elite drift is attributed to **Gingrich/1994**,
  HIGH). See `docs/polarization_causal_model.md`.
- **Log every source.** Whenever a new method/mechanism is introduced, a paper
  is cited, or a dataset/survey is shown, record it where appropriate **in the
  same change** — the calibration detail + provenance tag in
  [`docs/methods.md`](docs/methods.md), and the annotated entry (what it anchors,
  where it's used) in [`docs/literature.md`](docs/literature.md). Don't let
  citations accumulate only in code comments, commit messages, or one-off briefs.

### Time & status
Time maps via `ticks_per_year = 3` (1 tick ≈ 4 months), anchored to the ANES
out-party thermometer; the shipped run is ticks `0…135` = 1980 → ~end 2025.
**Status: Phase 10 complete** (Phase 9 = ANES recalibration; Phase 10 =
intervention library re-measure on that baseline), **MHV S0–S5 done**, and
**emergence-recovery E5 done**. The canonical engine substrate is the emergent
D=7 build (S2/T2.6). Media coupling is still a **data-fed input series**
(penetration curves; `data_fed_media`, methods §5.24). The elite channel,
however, is no longer fed: since **emergence-recovery E5** the canonical
`ANES_FULL_KWARGS` runs the **endogenous activist→elite→mass loop**
(`endogenous_elite=True`, `data_fed_elite=False`, the adopted E4 ABC point;
`abm/rules/activist_elite.py`, methods §5.29), so positional sorting **emerges**
rather than replaying fed ANES voter centroids (**blindspot #7 resolved** — the
honesty budget flips party_sep to ~1.00 emergent / ~0 input-carried). The whole
re-bless cascade ran on it (scorecard 18/24, realism 18/24, phase-10 buckets
unchanged, web re-exported). **Honest open caveat:** the loop's late-period
*timing* is an exogenously-calibrated forcing, not out-of-sample predictable —
the four-cut holdout fails the temporal + instrument cuts (1/3;
`docs/results/e5_holdout.md`), and the single-axis loop over-correlates the
compass axes (corr~0.78). The pre-E5 fed config is preserved as
`ANES_FULL_FED_KWARGS`. I3 (no direct outcome writes outside the delta pipeline)
is enforced by test.

### Engine quickstart (Windows PowerShell)
```powershell
.venv\Scripts\Activate.ps1
.venv\Scripts\python.exe -m pytest                       # full test suite (~14 min)
.venv\Scripts\python.exe scripts\phase10_measure.py      # re-measure the intervention library
```

---

## The web demo (`web_demo/`)

A static page loaded over HTTP — React 18 UMD + `@babel/standalone` compiling
the `.jsx` in-browser. **No build step, no bundler, no npm.** It must be served
over HTTP, **not opened as `file://`** (the sibling `.jsx`/`.js` files load over
relative paths).

### Running it
- Preview server is defined in `.claude/launch.json` as **`web_demo`**
  (`python -m http.server 8137 --directory web_demo`).
- Entry URL: **`http://localhost:8137/Calm%20to%20Camps.html`** (note the space
  in the filename; the server is rooted at `web_demo/`, so the path is just
  `/Calm%20to%20Camps.html`, *not* `/web_demo/...`).

### Verification gotcha (important)
`requestAnimationFrame` is **paused in the headless preview tab.** Anything
RAF-driven — morph/cross-fade tweens, snap-to-chapter glides, autoplay motion,
the fast-forward intro — **cannot be verified headlessly.** Deterministic,
static state *can* be: scroll→tick math, clamps, label/layout geometry (static
SVG), DOM bounding-box overlap tests, console errors. For motion, state the
limitation and let the user eyeball it in a real browser. (`preview_eval` also
returns `{}` for nested `setTimeout` inside a returned Promise — use
`async/await` with `await new Promise(r => setTimeout(r, ms))` instead.)

### Data pipeline (engine → web)
The demo never runs the engine. It loads one generated file,
`web_demo/cc-data.js`, which assigns the whole dataset to `window.CC_DATA`.

```
engine (Python)
  → scripts/publish_web_data.py   → web/data/*.json   (full per-tick exports)
  → scripts/repack_web_demo.py    → web_demo/cc-data.js (compact, ~1.06 MB)
```

- **`cc-data.js` is generated — never hand-edit it.** To change the data,
  re-run the pipeline.
- Schema is frozen as **`contract_version: 1`**. Full spec:
  [`docs/web_data_contract.md`](docs/web_data_contract.md).
- Provenance is flagged in the data: notably `macro.aff_in_empirical` is an
  **external ANES reference line, NOT an engine metric** — never present it as a
  simulation output (it's the flat in-party line in the honest "scissors").

### File map (load order in `Calm to Camps.html`)
| File | Role |
|---|---|
| `cc-data.js` | generated dataset → `window.CC_DATA` (only plain `.js`) |
| `cc-shared.jsx` | palette/tokens (`CC`), fonts, small UI primitives, seeded RNG |
| `cc-proto-engine.jsx` | thin read layer over `CC_DATA`: `posAt`/`macroAt`, party colors, fractional-tick interpolation, constants (`LAST`, `TPY`, `Y0`) |
| `cc-proto-panels.jsx` | timeline (`ProtoTimeline`), sparklines, ego-mini, character panels |
| `rc-shared.jsx` | redesign helpers: KDE `<Field>` canvas, affect ramp, centroid-gap motif, `useTick` hook |
| `cc-system.jsx` | design system (`DS`): type ladder, radii, spacing — use ONLY these |
| `rc-interventions.jsx` | Interventions view; all Δ/buckets computed LIVE from `D.counterfactuals` (no hardcoded numbers) |
| `rc-story.jsx` | `STORY_BEATS` (the guided chapters) + story copy |
| `cc-pages.jsx` | static About / Methods pages |
| `cc-unified.jsx` | **main shell** — the unified one-page app (Watch / Explore / Interventions postures, header, timeline bar, story scroll logic) |

### Core data model (front-end)
- **Time:** `tick` is the single source of truth. `n_ticks = 136` → ticks
  `0…135`; `LAST = 135`. `year = 1980 + tick/3` (tick 0 = 1980, tick 135 ≈ end
  of 2025).
- **`window.CC_DATA`** keys: `meta`, `events`, `interventions`, `entities`,
  `runs.baseline` (the only full per-tick run), `counterfactuals` (56
  intervention runs, lean), `chars`.
- **Compass:** x = economic, y = cultural; `party` 0 = Dem (navy) / 1 = Rep
  (oxblood) / 2 = Independent (warm grey).
- **Story mode:** `STORY_BEATS` are tick-anchored chapters; the active chapter
  is derived purely from `tick`. Some beats switch the field `layer`
  (`position` → `affect`).

---

## Where to read (docs/)

- [`README.md`](README.md) — top-level orientation + architecture.
- [`docs/ENGINE_OVERVIEW.md`](docs/ENGINE_OVERVIEW.md) — what the engine is and
  why each rule exists (high altitude).
- [`docs/methods.md`](docs/methods.md) — citation-pinned methods (every number
  anchored to a paper) + the full provenance and limitations tables.
- [`docs/literature.md`](docs/literature.md) — annotated index of every dataset
  and paper: what each anchors and where in the repo it's used (the "where does
  this number come from?" reference).
- [`docs/ENGINE_KNOBS.md`](docs/ENGINE_KNOBS.md) — operator's manual: every
  rule, knob, scenario, and `build_engine` kwarg.
- [`docs/INTERVENTIONS_OVERVIEW.md`](docs/INTERVENTIONS_OVERVIEW.md) — the 7
  interventions (X1–X7), mechanisms, and measured buckets.
- [`docs/polarization_causal_model.md`](docs/polarization_causal_model.md) — the
  evidence grading / causal story behind the timeline copy.
- [`docs/web_data_contract.md`](docs/web_data_contract.md) — the web data schema
  (v1).
- [`docs/results/phase10_results.md`](docs/results/phase10_results.md) — the
  authoritative measured intervention buckets (ground truth for the web build).
- [`docs/model_blindspots.md`](docs/model_blindspots.md) — the register of
  known structural/empirical blindspots (incl. #7: positional sorting is
  input-carried, not emergent).
- [`docs/results/realism_report.md`](docs/results/realism_report.md) +
  [`docs/results/honesty_budget.json`](docs/results/honesty_budget.json) — the
  realism battery and the emergent/input/hand-drawn budget split.

**Project history.** The model was built in phases (engine phases 1–10, then the
MHV S0–S5 honest-rebuild) and via a knob audit. The per-phase design specs,
intermediate results, and review reports were removed in a June 2026 cleanup —
the *current* state is documented in the live docs above; the detailed build
trail lives in git history (and in the gitignored `docs/internal/`).
</content>
