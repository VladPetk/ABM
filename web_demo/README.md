# web_demo — "Calm to Camps"

The pedagogical front-end for polarlab. This folder is a self-contained
**design + working reference prototype** to be productionized.

## What's here

```
Calm to Camps Prototype.html   ← the working reference. Open in a browser, no build step.
  cc-shared.jsx                  tokens + primitives
  cc-proto-engine.jsx            data layer: interpolation, network lookup, usePlayhead
  cc-proto-compass.jsx           canvas compass (crowd + spotlight + counterfactual)
  cc-proto-panels.jsx            character / timeline / sparklines
  cc-proto.jsx                   app: intro + player, transport, picker, tabs
  cc-data.js                     window.CC_DATA — DEMO BUNDLE (see below)

HANDOFF.md                     ← READ THIS. Full spec: tokens, data contract, components, state.
reference-mockups/             ← static art-direction reference on a design canvas (not the product)
```

## Run it
Open `Calm to Camps Prototype.html` directly (it loads React + Babel from CDN).
No install, no bundler. The mockups open the same way.

## About `cc-data.js` (important)
It is **not** hand-authored data and **not** the production data source. It is a
compact repack of two real engine exports — `seed_0.json` (baseline) and
`X7_perception_correction_at_2000.json` — decimated to 3-dp positions so the
prototype runs offline. Regenerate / replace it from real runs per the data
contract in `HANDOFF.md §3`. Production should lazy-`fetch` runs from
`manifest.paths` rather than bundling.

## Four placeholders to replace with real data (all flagged in HANDOFF.md §3)
1. **Narrative beat prose** — authored stand-ins; engine `narrative_beats` are diagnostic strings. Add a real `prose` field per beat.
2. **Tie strength** — ego-graph proximity is faked from the cross/same-party flag; wire a real per-edge weight.
3. **Character indices** — Linda=86 is canonical; Bob/James/Maria (134/5/28) were chosen by scanning seed_0. Replace with canonical `agent_index` per character file.
4. **Only baseline + X7 bundled** — other interventions show real metadata but no counterfactual run; add their precomputed files (or the live loader).

Everything else — agent motion, party/faction/affect, macro metrics, network
edges, events, intervention metadata, the counterfactual — is real engine output.
