# Calm to Camps — Handoff Spec

A pedagogical front-end for **polarlab**: the user watches the US polarize
1980→2025, follows four named characters across the political compass, and
tries interventions to discover which (if any) move the needle.

This package contains a **working reference prototype** (`Calm to Camps Prototype.html`)
driven by the real engine export. This doc is the contract for re-implementing
it cleanly. The prototype is the source of truth for *behavior and feel*; this
doc is the source of truth for *structure and data*.

---

## 1. Files

| File | Role |
|---|---|
| `Calm to Camps Prototype.html` | Shell — loads fonts, React 18, Babel, the data bundle, and the JSX modules. |
| `cc-data.js` | The repacked engine export as `window.CC_DATA` (see §3). **Demo bundle** — baseline + one intervention (X7). Production loads JSON per `manifest.paths`. |
| `cc-shared.jsx` | Design tokens (`CC`, `SANS`/`MONO`/`SERIF`, `TNUM`) + primitives (`Logo`, `Eyebrow`, `FloatCard`, `PartySwatch`, `InfoDot`). |
| `cc-proto-engine.jsx` | Data layer: tick↔year, party/colour maps, fractional-tick interpolation, network lookup, `usePlayhead` hook, metric domains. |
| `cc-proto-compass.jsx` | `<ProtoCompass>` — canvas-rendered agent cloud + spotlight + ego edges + counterfactual ghost/solid. |
| `cc-proto-panels.jsx` | `<ProtoCharacter>`, `<ProtoEgoMini>`, `<ProtoTimeline>`, `<ProtoSparklines>`. |
| `cc-proto.jsx` | `<ProtoApp>` — intro + player, transport, intervention picker, result card, tabs. |

`Calm to Camps Mockups.html` (+ its `cc-*.jsx`) is the **static visual reference**
on a design canvas. Keep for art direction; not part of the running product.

---

## 2. Tokens

```
bg #f3f3f0   bg2 #ebe8df   surface #fff
ink #1a1d23  ink2 #3d4148  ink3 #74797f  ink4 #adb1b5
border #e0ddd3  borderS #cdc9bd
party: D(emocrat) #1f3565 navy · R(epublican) #8b2530 oxblood · I(ndependent) #9a958a grey
fonts: Geist (chrome) · Geist Mono (numbers/labels, with tnum) · Newsreader (titles, bios, beats)
```
Bucket colours (intervention outcomes): null `#74797f` · partial `#c47a2c` · real `#3f7d54` · backfire `#8b2530`.
Intervention accent colours come from `intervention_metadata[id].color`.

---

## 3. Data contract (`window.CC_DATA`)

Repacked from the engine export for the browser. Shapes the prototype actually consumes:

```
meta: { n_agents, n_ticks, tick_0_year, ticks_per_year, axes, release_years, characters }
events: [ { tick, label, description, actual_date, kind } ]      // kind: media|election|faction|crisis|decade_boundary
interventions: { <id>: { id, label, color, effect_buckets:{issue_sorting,affect}, provenance_tags:{ "L:M","L:D","T","C" }, expected_naive_effect } }
runs: {
  baseline:  Run,
  <intervention_id>: Run,        // e.g. X7_perception_correction
}
chars: { <key>: { name, agent_index, job, city, issues:[], bio, beats:[ { tick, prose } ] } }

Run = {
  release_tick,                  // null for baseline
  pos:   [tick][agent] = [x, y], // ideology coords, ~[-1,1]; the crowd. 3-dp rounded.
  party: [tick][agent] = 0|1|2,  // 0 Dem, 1 Rep, 2 Independent
  macro: [tick] = { sep, aff, varr, mod, xc },   // party_sep, mean out-party warmth (neg), variance, modularity, xc_fraction
  net:   { <tick>: [ [src, tgt, cross] ] },      // edge snapshots at event ticks only; cross=1 if cross-party
  charAffect:  { <agent_index>: [tick] },        // per-character out-party warmth (negative)
  charFaction: { <agent_index>: [tick|null] },   // e.g. "MAGA", "Tea_Party"
  replacement_events: [ [tick, agent_id], … ],   // every cohort replacement (slot reuse); drives EMA-reset + ghost-fade
}
```

### Regenerating `cc-data.js`
`scripts/publish_web_data.py` writes the full per-run JSON to `web/data/`;
`scripts/repack_web_demo.py` then compacts the baseline + one intervention
(default X7 @ 2000) into `web_demo/cc-data.js`. Run them in that order.

### Mapping to the raw engine files
- `pos`/`party`/`macro`/`net` ← `seed_0.json` (baseline) and `interventions/{id}_at_{year}.json` (per intervention×release).
  Raw `ticks[t].positions/party/affect/threat/faction`, `macro[t]`, `network_snapshots`.
- `charAffect`/`charFaction` are just `ticks[t].affect[idx]` / `faction[idx]` sliced for the 4 character indices (kept small).
- `replacement_events` ← the run export's `replacement_events` (emitted by `CohortReplacement`); `cross` in `net` is recomputed from the two endpoints' parties at the snapshot tick.
- Axes (`manifest.ideology_axes`): **x** Economic — lo Redistributive (left) → hi Laissez-faire (right);
  **y** Cultural — lo Progressive (bottom) → hi Traditional (top). The compass plots y with hi at top.
- `release_years` maps release tick → calendar year (15→1985 … 120→2020).

### Decisions baked in (swap when real data lands)
1. **`beats[].prose`** — authored journalistic prose, *placeholder*. Engine's `narrative_beats` are diagnostic strings; add a real `prose` field per beat in `characters/{id}.json`.
2. **Tie strength** — ego-graph proximity currently faked from `cross` flag (cross=0.28, same=0.85). Replace with a real per-edge weight (4th element of the edge tuple) when emitted.
3. **Character indices** — Linda=86 (given). Bob=134, James=5, Maria=28 were chosen by scanning seed_0 for matching archetypes; replace with the canonical `agent_index` from each `characters/{id}.json`.
4. **Network cadence** — event-tick snapshots only (per your call). Edges hold/step between events; dots interpolate continuously.

---

## 4. Engine helpers (`cc-proto-engine.jsx`)

```
tickToYear(t) / yearToTick(y)            // Y0=1980, TPY=3, LAST=135
partyColor(0|1|2) / partyName(...)       // → token / label
posAt(run, f)        → [agent][x,y]      // linear interp between floor(f), floor(f)+1
agentPosAt(run,f,i)  → [x,y]
partyAt / factionAt / affectAt(run,f,i)  // step (party/faction) or interp (affect)
macroAt(run, f, key)                     // interp metric
egoEdges(run, f, idx)                    // edges touching idx at the at-or-before snapshot
METRICS.{sep,aff}                        // { label, transform, domain } — aff plotted as -warmth
usePlayhead({initial,autoplay,baseTicksPerSec}) → { tick, setTick, playing, setPlaying, toggle, speed, setSpeed }
```
`usePlayhead` owns play/pause/scrub/speed, advances `tick` via rAF
(`baseTicksPerSec * speed`, default 6 → full sweep ~22s at 1×), clamps to
`[0, LAST]`, auto-pauses at the end, and **persists `tick` to localStorage**
(`cc_tick`) so a refresh — or moving intro→player — resumes in place.

---

## 5. Components

- **`<ProtoCompass tick run baselineRun spotlightIdx mode>`** — canvas, internal 1100², `aspect-ratio 1/1`. Draws grid/axes/quadrant labels, the crowd (party colour, alpha .46 when a spotlight is set), the spotlight ego network (edges + emphasised neighbours), and the spotlighted character (white-ringed). `mode="counterfactual"` overlays `baselineRun` as hollow ghosts under the solid intervention cloud. Redraws on any prop change. *Canvas (not SVG) is deliberate — 250 dots at 60fps.*
- **`<ProtoCharacter tick run charKey tabs onTab>`** — tab strip, identity (name/city/year/faction), bio, votes + warmth bar, issues, `<ProtoEgoMini>`, and the current narrative beat (latest beat with `tick ≤ playhead`).
- **`<ProtoTimeline tick setTick releaseTick showReleases color>`** — 1980→2025 track, decade ticks, curated event labels (row-staggered; minor events are bare ticks — see `LABELLED` map), draggable playhead (pointer scrub), and in intervention mode the release-year candidates + chosen release marker.
- **`<ProtoSparklines tick run cfRun color>`** — the two Iyengar metrics. With `cfRun`, baseline draws dashed-grey and the counterfactual solid in the intervention colour.

---

## 6. App state (`<ProtoApp>`)

```
screen: 'intro' | 'player'        // intro CTA → player; logo → intro. Playhead is NOT reset.
playhead: usePlayhead()           // single shared instance — the carry-over source
charKey: 'linda'|'bob'|'james'|'maria'
intervention: null | <id>         // null = baseline; set → counterfactual mode (if run bundled)
```
Derived: `run = intervention ? runs[id] : runs.baseline`; `isCF = intervention has a bundled run`;
`idx = chars[charKey].agent_index`. Everything downstream reads `tick` + `run` + `idx`.

**Counterfactual** = compare `runs[id]` against `runs.baseline` at the same tick:
compass ghost/solid, sparklines overlay, result card Δs (`macroAt(cf) − macroAt(baseline)`),
timeline release marker. Δ sign → bucket colour (down = green/helpful, up = oxblood/backfire).

### Production notes
- Replace `cc-data.js` with lazy `fetch` of `manifest.paths`: baseline once; each intervention run on first selection (they're ~3.5 MB raw — stream/compress, or pre-decimate positions to 3-dp as the bundle does, ~0.75 MB/run).
- Variance band: `manifest.variance_band_seeds` are macro-only runs → optional confidence band behind the baseline sparkline.
- Header nav (Story/Characters/Methods/About) and "About this model" are intentionally static stubs.
