# polarlab

An agent-based model of US political polarization over a stylised ~60-year
window (~1960 → ~2020), built to do one thing publicly and honestly: **show
what real depolarization interventions actually do**, with the empirical
literature as the calibration anchor.

The headline finding the model produces: **most depolarization interventions
people loudly demand don't move the macro picture in the model.** Of the
seven-intervention library (re-measured on the R-phase canonical after the
2026-06 intervention-faithfulness pass), **six land null** and one — shared
neighborhoods and workplaces (X6) — lands a **durable partial** on affect; **none
lands "real."** Even cross-party exposure (X1), the lever most feared to
*backfire*, is **null on average**: its backfire is threat-gated, surfacing only
where exposure lands during active identity threat (faithful to the contested
evidence — Bail 2018 found backfire; Guess & Coppock 2020 found none on average).
Each verdict is reached through a mechanism the engine can show — and each null
carries a documented reason. (Workstream record:
[`docs/INTERVENTIONS_OVERVIEW.md`](docs/INTERVENTIONS_OVERVIEW.md).)

## Where to read

The model is documented at three altitudes. Read top-down:

- **[`docs/ENGINE_OVERVIEW.md`](docs/ENGINE_OVERVIEW.md)** — what the engine
  is, what each rule does, and why. Higher-altitude than the citation-pinned
  methods document.
- **[`docs/INTERVENTIONS_OVERVIEW.md`](docs/INTERVENTIONS_OVERVIEW.md)** — the
  seven public-facing interventions (X1–X7), their mechanisms, literature
  anchors, and measured buckets.
- **[`docs/methods.md`](docs/methods.md)** — citation-pinned methods. Every
  number, every knob, every choice anchored to a published paper.
- **[`docs/literature.md`](docs/literature.md)** — annotated index of every
  dataset and paper the model leans on: what each anchors and where it's used.
- **[`docs/ENGINE_KNOBS.md`](docs/ENGINE_KNOBS.md)** — the runtime knob
  registry.

Phase-by-phase results live under [`docs/results/`](docs/results); the
landing summary for the latest phase is
[`docs/results/phase10_results.md`](docs/results/phase10_results.md).

## Architecture

The engine is pure Python — `numpy`, `scipy`, `plotly`. No agent framework.

```
abm/
  core/        state, agent, environment, space, rules engine
  rules/       composable behaviour — influence, repulsion, party-pull,
               affective update, elite drift, perception update, …
  pillars/     the named pillar (calm_to_camps), the historical-arc release
               schedule, and the Phase 10 intervention bundles
  scenarios/   compass_basic — Hegselmann-Krause sanity substrate (tests)
  metrics/     polarization measures (issue sorting, affect, network)
data/
  literature/         primary-source PDFs the calibration is anchored to
  phase9_empirical/   ANES recoded into the model's 2D compass space
docs/
  ENGINE_OVERVIEW.md, INTERVENTIONS_OVERVIEW.md, methods.md, ENGINE_KNOBS.md
  specs/      per-phase design specs (phases 1 → 9)
  research/   expert reviews, investigation reports
  results/    per-phase measurement records + phase10_results.md
scripts/
  phase10_measure.py        the intervention sweep that produces phase10
  phase9_anes_score.py      ANES-band scoring
  phase9_*                  Phase 9 sweep + diagnostic tooling
tests/                      ~240 tests (literature-pinned core + empirical-band gates + drift guards + machinery)
```

## Quickstart (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]

# run the test suite (pins literature targets, ~14 min full run)
.venv\Scripts\python.exe -m pytest

# re-measure the Phase 10 intervention library
.venv\Scripts\python.exe scripts\phase10_measure.py
```

## Status

**Phase 10 complete.** The engine has been ANES-recalibrated (Phase 9) and
the seven-intervention library has been re-measured against that
recalibrated baseline (Phase 10). What's planned next is the public-facing
UI — the engine is a back-end ready to be paired with a teaching artefact.
The model is a teaching artefact, not a policy-prediction tool: every
claim is within a literature citation envelope, every limitation is
documented.
