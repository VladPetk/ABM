# How We Sorted — Web Demo Plan

*The pedagogical interactive front-end for polarlab. Plan written
2026-05-28 at the close of Phase 10 (interventions library
finalised). This is the technical-design contract for the MVP
visualization — written before any front-end code. UX detail
design follows this doc once the architecture below is approved.*

For the engine this front-end visualizes, see
[`ENGINE_OVERVIEW.md`](ENGINE_OVERVIEW.md) and
[`INTERVENTIONS_OVERVIEW.md`](INTERVENTIONS_OVERVIEW.md).

> **Working title.** "How We Sorted." Other strong candidates: "Calm
> to Camps" (internal pillar name extended), "Sortlines", "Apart."
> Final name is open; this doc uses "How We Sorted" as a placeholder.

---

## 1. What this is and what it's not

**What it is.** A web demo that lets a non-expert user watch a
US-like society polarize from 1980 to 2025, follow four specific
individual "characters" through that journey, see real historical
events as they happen, and try depolarization interventions at
moments of their choosing — discovering, mostly, that the popular
ones don't work and that two structural ones do.

**What it's not.** A simulator the user runs locally. A sandbox
for arbitrary parameter tweaking. A research tool. A policy
forecasting product. Those are different products on top of the
same engine; this demo is teaching.

### 1.1 The teaching arc the demo carries

1. **Show the drift.** Baseline 1980→2025, no interventions. The
   user watches the camps form.
2. **Make it personal.** Four characters with names, jobs, issues
   they care about, and networks. The user follows one of them and
   sees the macro story through one person's life.
3. **Try to fix it.** A menu of seven literature-grounded
   interventions, each applicable at a user-chosen year. The user
   tries the popular asks first and watches them fail or backfire.
   Then they find the two that work.
4. **Land the lesson.** A summary card per intervention with the
   literature anchor, the bucket label, and the per-knob
   provenance tags — so the user sees *what's empirically grounded
   vs theoretical*.

---

## 2. Architectural decision: Path C — fully static, no stacking

### 2.1 The chosen path

- **Fully precomputed.** All trajectories built offline on Vlad's
  machine.
- **Static hosting.** No server, no API, no Python in the browser.
- **Single intervention at a time.** Users pick one intervention
  per session; no stacking. Defers the 2^7 combinatorial question
  to a future phase.
- **One canonical seed for characters.** Variance bands across the
  9-seed ensemble are an optional toggle for the macro view, not
  the default.

### 2.2 Why Path C for the MVP

| Property | Path C delivers |
|---|---|
| Hosting cost | $0 (Vercel/Netlify/Cloudflare Pages free tier) |
| Server cost | $0 |
| Latency | Instant (lazy-loaded static files) |
| Scalability | Unlimited (CDN) |
| Determinism | Perfect (same precomputed file every time) |
| Pedagogy | Tighter — constraints help the story |
| Future flexibility | Path B (cached API for stacked combos) can be added later without rebuilding |

The cost is flexibility — stacked interventions, per-tick release
timing, and custom seeds are unavailable. Phase 11+ if engagement
data shows demand.

### 2.3 What gets precomputed

- 1 baseline trajectory (1980→2025, 135 ticks)
- 7 interventions × 10 release ticks (1985 / 1990 / ... / 2025) ×
  30-tick counterfactual horizon = **70 counterfactual trajectories**
- 9-seed ensemble for the **baseline only** (used to render
  variance bands in the macro sparkline)
- Per-character supplementary data (per-tick affect dict, network
  neighbour list, etc.) — only for the canonical seed

Total at the canonical seed: 71 trajectories. Precompute time: ~15
seconds offline. Storage: ~15 MB compressed.

Baseline at 9 seeds (for variance bands): another ~5 MB compressed.

**Total dataset shipped: ~20 MB**, all lazily loaded. Initial page
load is just the baseline (~500 KB).

---

## 3. Data architecture

### 3.1 File layout

```
web/data/
  manifest.json                 # Index of all available trajectories
  baseline/
    seed_0.bin                  # Canonical seed (used for characters)
    seed_1.bin .. seed_8.bin    # For variance bands (optional load)
  interventions/
    X1_at_1985.bin
    X1_at_1990.bin
    ...
    X7_at_2025.bin              # 70 files total
  characters/
    linda.json                  # Bio, narrative beats, agent index
    john.json
    maria.json
    bob.json
  events.json                   # Historical event markers
  intervention_metadata.json    # Per-intervention bucket, anchor, tags
```

### 3.2 Binary trajectory format

Each `.bin` file is a single binary blob the front-end reads as
`ArrayBuffer` and slices into typed arrays:

```
Header (32 bytes):
  magic: 'HOWS'                  (4 bytes)
  version: uint16                (2 bytes)
  n_agents: uint16               (2 bytes)
  n_ticks: uint16                (2 bytes)
  seed: uint16                   (2 bytes)
  release_tick: int16            (2 bytes, -1 for baseline)
  intervention_id: uint8         (1 byte, 0 for baseline)
  flags: uint8                   (1 byte)
  reserved: 16 bytes

Body (concatenated arrays, per-tick blocks):
  positions[tick][agent][2]: Float32   (n_ticks * n_agents * 8 bytes)
  party[tick][agent]: Uint8            (n_ticks * n_agents bytes)
  affect[tick][agent]: Float32         (n_ticks * n_agents * 4 bytes)
  threat[tick][agent]: Float32         (n_ticks * n_agents * 4 bytes)

Trailer:
  network_snapshots: variable          (sparse, ~10 ticks)
    For each snapshot tick:
      tick: uint16
      n_edges: uint32
      edges[n_edges]: [agent_a uint16, agent_b uint16, flags uint8]
```

For a canonical 250-agent, 165-tick run: ~830 KB raw, ~250 KB
compressed with gzip. The CDN serves gzipped automatically.

### 3.3 Why not JSON for the bulk data

JSON parse cost for ~50,000 floats per trajectory is non-trivial
(~50ms). `ArrayBuffer` + `Float32Array.view(buffer)` is essentially
free — zero copy, zero parse. JSON only for metadata, characters,
events.

### 3.4 manifest.json shape

```json
{
  "version": 1,
  "n_agents": 250,
  "ticks_per_year": 3.0,
  "tick_0_year": 1980.0,
  "release_ticks": [15, 30, 45, 60, 75, 90, 105, 120, 135],
  "interventions": ["X1", "X2", "X3", "X4", "X5", "X6", "X7"],
  "canonical_seed": 0,
  "variance_band_seeds": [0, 1, 2, 3, 4, 5, 6, 7, 8],
  "characters": ["linda", "john", "maria", "bob"]
}
```

Front-end reads this once on load and builds its UI controls from it.

---

## 4. Visualization design

### 4.1 Layout — one main canvas + one sidebar

```
┌──────────────────────────────────────────────────────────────────┐
│  HEADER: title + intervention picker + release-year slider       │
├─────────────────────────────────────────────┬────────────────────┤
│                                             │  CHARACTER PANEL   │
│                                             │  ┌──────────────┐  │
│                                             │  │  Linda       │  │
│       MAIN COMPASS                          │  │  Age 32 (1985)│  │
│       (250 agents on 2D ideology plane,     │  │  Mom of two  │  │
│        Linda highlighted, her edges shown)  │  │  Ohio        │  │
│                                             │  └──────────────┘  │
│                                             │                    │
│                                             │  ISSUES SHE CARES  │
│                                             │  • Education       │
│                                             │  • Healthcare      │
│                                             │  • Taxes           │
│                                             │                    │
│                                             │  HER NETWORK       │
│                                             │  ┌──────────────┐  │
│                                             │  │ (mini force-  │  │
│                                             │  │  directed     │  │
│                                             │  │  ego-network) │  │
│                                             │  └──────────────┘  │
│                                             │                    │
├─────────────────────────────────────────────┴────────────────────┤
│  TIMELINE: 1980 ──── Reagan ── Cold War ends ── 9/11 ── … 2025  │
│            playhead at March 1996                                │
│  MACRO SPARKLINES: party separation │ affective polarization    │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Main compass

- Canvas-rendered (not SVG) for 60fps with 250 dots.
- 2D ideology plane, `[-1, 1]²`, x = economic, y = cultural.
- Each dot coloured by party (D blue, R red, I neutral).
- Selected character's dot is **larger and outlined in white** for
  visibility.
- Selected character's network edges drawn from their node:
  - 100% opacity to immediate neighbours (~7–10 edges)
  - 30% opacity for second-degree edges (edges among neighbours)
  - All other edges hidden — keeps the compass uncluttered.
- Faction-tagged agents (Tea Party, MAGA, Bernie, DSA emergent
  clusters from Phase 9 events) get a thin outline ring in their
  faction color *only when active in the current tick*.

### 4.3 Character profile sidebar

- Bio paragraph (hand-written, ~50 words; ages with timeline).
- Issues she cares about (3–5 items from her `identities` vector
  + her ideology position).
- Party affiliation and out-party affect (live values, e.g.,
  "Votes Democrat. Warmth toward Republicans: −0.32").
- Mini ego-network — force-directed mini-graph, ~7–10 nodes,
  showing topology (not compass coordinates). Updates at
  network-snapshot ticks.
- Narrative beats appear inline as the timeline crosses authored
  moments ("By 1992, Linda's social circle has shifted...").

### 4.4 Timeline

- Single horizontal track at the bottom.
- Year labels at decade boundaries, finer ticks at 5-year marks.
- **Event markers** with hover tooltips (Fox News launches Oct 1996,
  9/11 Sep 2001, Obama elected Nov 2008, Trump elected Nov 2016,
  Jan 6 2021, etc. — sourced from
  `historical_arc.py::build_schedule`).
- **Playhead** scrubs at sub-tick (monthly) precision; see §6.
- Play/pause/speed controls (1×, 2×, 4×).
- **Release-year selector** appears as a separate marker on the
  timeline once a user picks an intervention.

### 4.5 Macro sparklines

A small two-line chart strip below the compass:

- Line 1: `party_separation` (Iyengar issue-sorting metric) over time.
- Line 2: `affective_polarization` (Iyengar affect metric) over time.

In counterfactual mode: baseline drawn in light grey, counterfactual
drawn in colour. This carries the macro-society signal so the main
compass can focus on the spotlight character without losing the
"what's happening to everyone else" story.

---

## 5. Character design

### 5.1 Four characters

Hand-picked agent indices in the canonical seed (seed 0). Selection
criteria: trajectories that span the interesting story space.

| Slot | Name | Archetype | Arc |
|---|---|---|---|
| 1 | **Linda** | Suburban swing voter | Centrist D in 1985 → late-life R partisan by 2025. The headline arc. |
| 2 | **James** | Stable left-leaner | D throughout, but his affect toward Rs cools dramatically post-2008. Position barely moves; warmth collapses. Shows the "affect drifts faster than ideology" Iyengar finding made personal. |
| 3 | **Maria** | Independent → Bernie-curious | Independent in the 90s, leans D in 2000s, drawn into the post-2016 DSA faction by 2018. The leftward emergence story. |
| 4 | **Bob** | Tea Party / MAGA arc | Mainstream R in 1985 → Tea Party in 2009 → MAGA in 2015 → stable in faction by 2025. The factional-emergence story from the right. |

(Final agent indices to be picked after running the publish script
once and inspecting trajectories programmatically.)

### 5.2 Character data file shape

```json
{
  "id": "linda",
  "name": "Linda",
  "agent_index": 42,
  "birth_year": 1953,
  "city_template": "suburban Ohio",
  "job_template": "school district administrator",
  "issues_priority": ["education", "healthcare", "taxes"],
  "bio": "Linda is a school administrator and mother of two...",
  "narrative_beats": [
    { "year": 1985, "text": "In 1985, Linda is 32, married, and...", "trigger": "tick_15" },
    { "year": 1996, "text": "By '96, she's noticed that the dinner-table arguments...", "trigger": "tick_48" },
    { "year": 2001, "text": "After 9/11, she finds herself...", "trigger": "tick_63" },
    { "year": 2016, "text": "Linda votes Republican for the first time...", "trigger": "tick_108" },
    { "year": 2023, "text": "Now in her seventies, she watches MSNBC and Fox both...", "trigger": "tick_129" }
  ]
}
```

### 5.3 Counterfactual narration

For non-baseline runs, narrative beats are **not** hand-written.
Instead, a small procedural template:

- Compute the divergence between Linda's baseline state and her
  counterfactual state at the playhead.
- Render a small inline callout: "In this counterfactual, Linda's
  warmth toward Republicans in 2025 is −0.58, vs −0.72 in the
  actual timeline. Her position has moved 0.18 units less."

LLM-generated counterfactual narrative is a Phase 2 nicety. The
divergence numbers + visual trails (see §7.2) carry enough story
for MVP.

### 5.4 Switching characters

A tab strip above the character panel lets users swap between the
four. Switching is instant — same agent indices, just different
narrative + spotlight target. The compass re-draws edges from the
newly-selected node.

---

## 6. Sub-tick interpolation — monthly granularity

### 6.1 The mechanics

Engine runs at 3 ticks/year. Tick 0 = January 1980. Tick t covers
months `[t × 4, t × 4 + 4)` of sim time. Front-end renders at
arbitrary fractional ticks:

```
t = (year - 1980 + month / 12) * 3
pos(t) = lerp(pos(floor(t)), pos(ceil(t)), t - floor(t))
```

- **Positions**: linear interpolation between adjacent ticks.
- **Affect, threat**: linear interpolation (continuous quantities).
- **Party**: snaps to the closer tick (discrete; party switches are
  rare and shouldn't blur).
- **Network edges**: snap to the nearest tick (discrete events; no
  visual sense in interpolating edges).
- **Faction tags**: snap to the nearest tick.

### 6.2 Event timing

Engine events fire at integer ticks; visualization shows them at
their *true historical months*. Event lookup table:

```json
{
  "fox_news_launch": { "tick": 50, "actual": "1996-10" },
  "nine_eleven":     { "tick": 65, "actual": "2001-09" },
  "obama_election":  { "tick": 87, "actual": "2008-11" },
  "tea_party":       { "tick": 87, "actual": "2009-04" },
  "trump_election":  { "tick": 110, "actual": "2016-11" },
  "covid_start":     { "tick": 120, "actual": "2020-03" },
  "jan_6":           { "tick": 124, "actual": "2021-01" }
}
```

Engine-side ticks stay integer; the visualization just uses the
"actual" timestamp for the timeline marker.

### 6.3 Playback speed

Default: **1 wall-clock second = 1 sim year.** Full 1980→2025 plays
in 45 seconds. Speed controls at 0.5× / 1× / 2× / 4×.

At 1× and 60fps, that's 60 interpolated frames per sim year — very
smooth. The interpolation is what makes this feel like a documentary
rather than a step-function chart.

---

## 7. Intervention UX

### 7.1 Picking an intervention

A menu (top of header) lists the seven interventions by lay name:

1. Show people the other side (X1)
2. Fix the algorithm (X2)
3. Quit cable news (X3)
4. Bipartisan dialogue programs (X4)
5. Ranked-choice voting (X5)
6. Shared neighborhoods and workplaces (X6)
7. Correct the perception gap (X7)

Plus "No intervention (baseline)" as the default.

### 7.2 Picking a release year

Once an intervention is selected, the timeline shows the **10
allowed release years** (1985, 1990, ..., 2025) as larger
clickable markers. The user clicks one; the playhead jumps to that
year; the counterfactual trajectory loads (lazy fetch, ~200 KB).

### 7.3 Counterfactual rendering

- **Trails.** Each agent draws a thin (1px, 30% opacity, grey) line
  from "where they would have been in the baseline at this tick" to
  "where they are now in the counterfactual." Trails grow as
  divergence accumulates.
- **Character spotlight.** Non-character-network agents drop to ~20%
  opacity. The character + their ~10 neighbours stay at full
  opacity with thick coloured trails.
- **Macro sparkline overlay.** Baseline sparkline in grey,
  counterfactual sparkline in the intervention's colour. Bucket
  label appears as a badge on the chart.
- **Result card.** Once the counterfactual reaches its endpoint
  (30 ticks past release), a small card slides in with:
  - The bucket label (null / partial / real / backfire)
  - Δsep and Δaff values
  - One-line literature anchor
  - Per-knob provenance tag tally (e.g., "X5: 0 [L:M] / 4 [T]")
  - "What this means" — one sentence pedagogical framing

### 7.4 Returning to baseline

A clear "Reset" button or clicking "No intervention" returns to
baseline. The counterfactual trajectory unloads; trails fade out.

---

## 8. Tech stack

| Layer | Choice | Why |
|---|---|---|
| Front-end framework | **Svelte + SvelteKit** | Smaller bundle, faster reactivity for timeline scrubbing, less boilerplate. React + Vite is the alternative if the team prefers a larger ecosystem. |
| Bundler | Vite | Standard. |
| Rendering | Canvas 2D | 250 dots × 60fps trivial. WebGL would be overkill. |
| Mini ego-network | D3 force-directed (or `d3-force` standalone) | 7–10 nodes; standard. |
| State | Svelte stores (or Zustand if React) | Lightweight. |
| Hosting | Vercel / Netlify / Cloudflare Pages | Free tier sufficient. |
| Data hosting | Same CDN, in repo `/web/data/` | Or Cloudflare R2 if dataset grows. |
| TypeScript | Yes | Avoid runtime surprises with the binary format. |

### 8.1 Bundle size budget

- Initial JS: < 200 KB gzipped
- Initial data load (baseline): ~500 KB gzipped
- Per intervention lazy fetch: ~200 KB gzipped
- Per character JSON: ~10 KB

Page should be interactive (first compass render) in under 1.5
seconds on a 4G connection.

---

## 9. Build pipeline

### 9.1 The publish script

`scripts/publish_web_data.py`:

1. Load the historical arc engine with `tier_d_anes_knobs=True`.
2. Run baseline at 9 seeds; serialize each to `web/data/baseline/seed_N.bin`.
3. For each of 7 interventions × 10 release ticks: build the
   intervention config, run for `release_tick + 30` ticks at the
   canonical seed, serialize to `web/data/interventions/<X>_at_<year>.bin`.
4. For each of 4 characters: extract the agent's per-tick trajectory
   from the canonical baseline; compute "issues she cares about"
   from her `identities` vector + ideology position; merge with
   hand-written `narrative_beats.json` (authored separately);
   write `web/data/characters/<name>.json`.
5. Emit `manifest.json`, `events.json`, `intervention_metadata.json`.
6. Total runtime: ~30 seconds.

### 9.2 When to re-publish

- Any engine change that affects trajectories → re-run publish.
- Any change to character narrative beats → re-run (cheap step).
- Any change to intervention parameters → re-run (cheap step).

### 9.3 CI integration

A GitHub Action runs the publish script on push to `main` and
commits the output to `/web/data/`. The front-end build picks up
the new data automatically.

### 9.4 Character picking workflow

Selecting the four canonical agent indices is a **one-time
authoring step**:

1. Run the canonical baseline at seed 0.
2. Generate a per-agent CSV summary: starting ideology, ending
   ideology, party switches, max-affect-change, faction-tagged-when.
3. Sort/filter for candidate archetypes per §5.1.
4. Pick four; commit the agent indices to a `characters.lock.json`
   so future publish runs use the same agents.

If the engine changes such that agent index 42 no longer has
Linda's arc, the lock file flags the mismatch and authoring re-runs
the selection.

---

## 10. Known limitations and Phase-2 candidates

| Limitation | Phase-2 path |
|---|---|
| No intervention stacking | Add Path B (cached API for combos) |
| Fixed 4 characters | LLM-generated character profiles from arbitrary agent indices |
| Fixed 10 release years | Per-tick release timing (only feasible via API path) |
| No custom-seed exploration | API path with seed parameter |
| Counterfactual narrative is procedural | LLM-generated character narration for counterfactuals |
| No mobile-first design | Responsive layout in Phase 2 — MVP targets desktop |
| English only | i18n in Phase 2 |
| No accessibility audit | a11y pass in Phase 2 (colour-blind palette, screen-reader for timeline) |

---

## 11. Open decisions

Locked from the previous round of discussion:

- ✅ Path C (fully static, no stacking) for MVP
- ✅ 4 characters
- ✅ Monthly interpolation
- ✅ 5-year release granularity (10 release ticks)
- ✅ Trails + character-network spotlight for counterfactuals
- ✅ One main compass + one character sidebar (no split-screen)
- ✅ Single-intervention-at-a-time UX

Still open:

- 🟡 Public name — current placeholder "How We Sorted"
- 🟡 Final character agent-index picks (requires one canonical run + inspection)
- 🟡 Narrative voice for character bios — first person, third person, journalistic
- 🟡 Colour palette — accessible diverging palette for D/R required
- 🟡 Mobile / tablet scope — desktop-only MVP, or responsive at launch
- 🟡 Telemetry — do we want anonymous analytics on which interventions / release years get explored most

---

## 12. Suggested build sequence

1. **Publish script first.** Get the binary trajectory format
   nailed down and verify it round-trips correctly. Run once,
   inspect output sizes.
2. **Static front-end skeleton.** Svelte + Vite + Canvas 2D
   rendering the baseline trajectory. No characters, no
   interventions. Just dots moving 1980→2025 with timeline
   scrubbing.
3. **Sub-tick interpolation + event markers.** Get the timeline
   feeling smooth and historically grounded.
4. **One character.** Pick Linda, write her bio + 5 narrative
   beats, render her in the sidebar with her edges on the
   compass.
5. **Intervention picker + counterfactual trails.** Wire up the
   intervention menu, the release-year selector, the counterfactual
   trajectory loader, and the trails rendering.
6. **Remaining three characters + ego-network mini.**
7. **Macro sparklines + result card.**
8. **Polish, palette, copy edit, deploy.**

Each step is a few days of work; the whole MVP is ~3–4 weeks at
focused pace.

---

## 13. What this doc is for

This is the **architecture and scope contract** for the front-end
MVP. The UX detail design (screen-by-screen mockups, copy, exact
interaction patterns) follows once this is signed off. The
engineering implementation follows once both are signed off.

The discipline is: change this doc before changing the build. If
the build diverges from this doc, the doc is wrong or the build
is — decide which, then re-align.
