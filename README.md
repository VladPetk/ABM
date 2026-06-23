# polarlab

An **agent-based model of US political polarization** over a stylised
~1980 → 2025 window, plus a public web demo that visualizes it. It models how a
two-party society sorts into camps across several coupled channels — ideology,
party identity, affect (out-party animus), partisan media, and social-network
structure — and what real-world depolarization interventions actually do when
applied. Every calibration choice is anchored to a published finding.

It is a **teaching artefact, not a policy-prediction tool**: results are
illustrative within a documented citation envelope, and limitations are recorded
([`docs/model_blindspots.md`](docs/model_blindspots.md)) rather than hidden.

## ▶ Live demo

**<https://vladpetk.github.io/ABM/>** — a static, build-free walkthrough of the
model: the 1980→2025 arc, the forces that drive it, and an interactive
intervention playground. *(Served from `web_demo/` via GitHub Pages. If the link
is dark, enable Pages once under **Settings → Pages → Source: GitHub Actions**.)*

## The headline finding

**Most depolarization interventions people loudly demand don't move the macro
picture in the model.** Of the seven-intervention library (re-measured on the
R-phase canonical after the 2026-06 intervention-faithfulness pass), **six land
null** and one — shared neighborhoods and workplaces (X6) — lands a **durable
partial** on affect; **none lands "real."** Even cross-party exposure (X1), the
lever most feared to *backfire*, is **null on average**: its backfire is
threat-gated, surfacing only where exposure lands during active identity threat
(faithful to the contested evidence — Bail 2018 found backfire; Guess & Coppock
2020 found none on average). Each verdict is reached through a mechanism the
engine can show, and each null carries a documented reason. See
[`docs/INTERVENTIONS_OVERVIEW.md`](docs/INTERVENTIONS_OVERVIEW.md).

## Where to read

The model is documented at three altitudes — read top-down:

- **[`docs/ENGINE_OVERVIEW.md`](docs/ENGINE_OVERVIEW.md)** — what the engine is,
  what each rule does, and why.
- **[`docs/INTERVENTIONS_OVERVIEW.md`](docs/INTERVENTIONS_OVERVIEW.md)** — the
  seven interventions (X1–X7), mechanisms, literature anchors, measured buckets.
- **[`docs/methods.md`](docs/methods.md)** — citation-pinned methods: every
  number, knob, and choice anchored to a published paper, plus the provenance and
  limitations tables.
- **[`docs/literature.md`](docs/literature.md)** — annotated index of every
  dataset and paper: what each anchors and where it's used.
- **[`docs/ENGINE_KNOBS.md`](docs/ENGINE_KNOBS.md)** — operator's manual: every
  rule, knob, scenario, and `build_engine` kwarg.
- **[`docs/polarization_causal_model.md`](docs/polarization_causal_model.md)** —
  the evidence-grading / causal story behind the timeline copy.
- **[`docs/web_data_contract.md`](docs/web_data_contract.md)** — the web data
  schema (v1) and the engine → web pipeline.

Measured results live under [`docs/results/`](docs/results); the authoritative
intervention buckets are in
[`docs/results/phase10_results.md`](docs/results/phase10_results.md) and the
realism battery in [`docs/results/realism_report.md`](docs/results/realism_report.md).

## Architecture

Two tracks share one repo:

1. **Engine** — pure Python (`numpy`/`scipy`), no ABM framework. Fully
   reproducible: `python -m pytest` runs the suite.
2. **Web demo** — a static React page (React 18 UMD + `@babel/standalone`
   compiling `.jsx` in-browser). **No build step, no bundler, no npm.** It reads
   a repacked snapshot of the engine's output; it runs no simulation itself.

```
abm/         the engine — core/ rules/ pillars/ scenarios/ metrics/
data/        literature PDFs + ANES/GSS-derived calibration anchors (see NOTICE.md)
docs/        all documentation (see "Where to read")
scripts/     the engine→web data pipeline + calibration/measurement tooling
tests/       367 tests (literature-pinned core + empirical-band gates + drift guards + machinery)
validation/  realism battery + reproducible model-vs-ANES figures
web_demo/    the static, build-free demo served on GitHub Pages
```

## Quickstart (engine)

```bash
python -m venv .venv
# Windows:  .venv\Scripts\Activate.ps1      macOS/Linux:  source .venv/bin/activate
pip install -e .[dev]

python -m pytest                      # full test suite (~14 min)
python scripts/phase10_measure.py     # re-measure the 7-intervention library
```

## Running the web demo locally

The demo must be served over **HTTP**, not opened as `file://` (the sibling
`.jsx`/`.js` files load over relative paths):

```bash
python -m http.server 8137 --directory web_demo
# then open http://localhost:8137/index.html
```

`web_demo/cc-data.js` is **generated** — never hand-edit it. To refresh it,
re-run the data pipeline: `scripts/publish_web_data.py` → `scripts/repack_web_demo.py`
(plus the auxiliary builders `build_branch_data.py`, `build_sandbox_data.py`,
`build_freeflow_data.py`; full spec in
[`docs/web_data_contract.md`](docs/web_data_contract.md)).

## Status

**Phase 10 complete** (Phase 9 = ANES recalibration; Phase 10 = intervention
library re-measured on that baseline), plus the **MHV honest-rebuild (S0–S5)**,
**emergence-recovery (E5)**, and the **R-phase** (audit-fix + reversibility)
pass. The canonical engine substrate is the emergent D=7 build; positional
sorting is written by an endogenous activist→elite→mass loop (~0.34 of the
party-separation rise is forcing-free; the rest rides calibrated forcings that
encode real event timing — quantified in
[`docs/results/honesty_budget.json`](docs/results/honesty_budget.json), not
hidden). The web demo ships the historical-arc run (preset `anes_full`, seed 0).

## License

Code (`abm/`, `scripts/`, `tests/`, `validation/`, `web_demo/`) is **MIT** —
see [`LICENSE`](LICENSE). Documentation and prose (`docs/`, this README, figures)
are **CC-BY-4.0**. Derived data under `data/` carries upstream ANES/GSS
attribution obligations in addition. Full details and data provenance:
[`NOTICE.md`](NOTICE.md).
