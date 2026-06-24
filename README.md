# The Divide

*An interactive model of how a country pulls apart and a demo that lets you watch it happen.*

**The Divide** is an agent-based model of political polarization: how a public
splits into two camps that disagree on the issues and, more than that, come to
dislike each other more than the disagreement alone would warrant. It simulates
250 people drifting across a political compass over a stylized 1980 → 2025,
sorting into camps under a handful of forces drawn from the polarization
literature — who you talk to, the parties pulling from above, who you live and
work next to, the media you steep in, and the warmth (or chill) you feel toward
the other side. Those forces are fit to decades of US survey data. On top of the
engine sits a public demo that lets you explore the whole thing visually, switch the forces on
one at a time, and try the interventions people argue about.

It's more a teaching artifact/ exploratory tool than a predictive model - in fact it does not predict anything at all. It moves dots on a map and tries to stay honest about how it does that.

## See it live

**<https://vladpetk.github.io/ABM/>**

A static, build-free walkthrough — the 1980→2025 arc, the forces that drive it, a
3-D view of the run, and an intervention playground. (Served from `web_demo/` on
GitHub Pages.)

## How it's built

Two halves, one repo:

- **The engine** is plain Python (`numpy`/`scipy`, no ABM framework). It's the
  actual simulation, and it's meant to be reproducible: `python -m pytest` runs
  the test suite, and most of those pin a number or a behavior to a published
  finding rather than to whatever the code happened to do.
- **The demo** is a static React page — React 18 over UMD with `@babel/standalone`
  compiling the `.jsx` in the browser. It doesn't run the simulation;
   rather it just plays back a saved snapshot of the engine's output.

```
abm/         the engine — core / rules / pillars / scenarios / metrics
data/        literature + ANES/GSS-derived calibration anchors (see NOTICE.md)
docs/        the documentation (see "Where to read")
scripts/     the engine → web data pipeline + calibration/measurement tooling
tests/       ~360 tests: literature-pinned core, empirical-band gates, drift guards
validation/  the realism battery + reproducible model-vs-ANES figures
web_demo/    the static demo that GitHub Pages serves
```

## Run it yourself

The engine:

```bash
python -m venv .venv
# Windows:  .venv\Scripts\Activate.ps1     macOS/Linux:  source .venv/bin/activate
pip install -e .[dev]

python -m pytest                    # the full suite (takes a while — ~15 min)
python scripts/phase10_measure.py   # re-measure the seven interventions
```

The demo — serve it over **HTTP**, don't open it as a `file://` (the sibling
`.jsx`/`.js` files load over relative paths):

```bash
python -m http.server 8137 --directory web_demo
# then open http://localhost:8137
```

One gotcha: `web_demo/cc-data.js` and its siblings are **generated** — never
hand-edit them. Refreshing them runs the data pipeline (`publish_web_data.py` →
`repack_web_demo.py`, plus the builders for the counterfactual branches, the
sandbox grid, and the free-flowing run); the full contract is in
[`docs/web_data_contract.md`](docs/web_data_contract.md).

## Where to read

The model is documented top-down — start at the overview and descend as far as
your curiosity takes you:

- [`docs/ENGINE_OVERVIEW.md`](docs/ENGINE_OVERVIEW.md) — what the engine is, what
  each rule does, and why.
- [`docs/INTERVENTIONS_OVERVIEW.md`](docs/INTERVENTIONS_OVERVIEW.md) — the seven
  interventions, their mechanisms, and what each is anchored to.
- [`docs/methods.md`](docs/methods.md) — the citation-pinned methods: every number
  and knob tied to a paper, with the provenance and limitations tables.
- [`docs/literature.md`](docs/literature.md) — an annotated index of every dataset
  and paper, and where each one is used.
- [`docs/ENGINE_KNOBS.md`](docs/ENGINE_KNOBS.md) — the operator's manual: every
  rule, knob, scenario, and `build_engine` argument.
- [`docs/model_blindspots.md`](docs/model_blindspots.md) — where the model is weak
  or wrong, kept on the record on purpose.

Measured results live under [`docs/results/`](docs/results) — the intervention
buckets in [`phase10_results.md`](docs/results/phase10_results.md), the realism
check in [`realism_report.md`](docs/results/realism_report.md).

## A word on honesty

The thing I most wanted to avoid was a model that quietly feeds itself the answer.
So, for the record: roughly a third of the rise in party separation emerges from
the forces alone, with nothing fed in from the outside world; the rest rides on
calibrated forcings that encode *when* real events actually happened. That split
is written down ([`docs/results/honesty_budget.json`](docs/results/honesty_budget.json)),
not buried. The realistic interventions are calibrated to published field
experiments; the "beyond realism" ones in the sandbox are thought experiments,
dialed past anything I'd defend as a measurement. The aim was never to predict —
it was to make a slow, abstract process visible, and to be straight about every
place I put a thumb on the scale.

## License

The code (`abm/`, `scripts/`, `tests/`, `validation/`, `web_demo/`) is **MIT** —
see [`LICENSE`](LICENSE). The writing and figures (`docs/`, this README) are
**CC-BY-4.0**. Data under `data/` carries upstream ANES/GSS attribution on top of
that. Full provenance and details: [`NOTICE.md`](NOTICE.md).
