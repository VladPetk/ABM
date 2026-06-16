# Calm to Camps — Web Data Contract (v1)

*The export/data interface the web demo consumes. Locked as
`contract_version: 1` on branch `web-redesign-ideas` (Step 0 of
[`execution_roadmap.md`](execution_roadmap.md)). This is the one-page schema
the front-end builds against while the engine track proceeds in parallel.*

The demo loads a single static file, `web_demo/cc-data.js`, which assigns one
JSON object to `window.CC_DATA`. It is a compact repack
(`scripts/repack_web_demo.py`) of the full per-tick engine exports under
`web/data/` (`scripts/publish_web_data.py`).

- **Engine version:** `phase10`, preset `anes_full`, canonical seed 0.
- **Bundle size (v1):** **1.06 MB** (was 1.52 MB pre-Step-0).
- **No engine logic is involved in this contract** — it is publish/repack only.
  Every series here is either the engine's own output or, where noted, an
  explicitly-flagged external overlay.

---

## Top-level shape

```js
window.CC_DATA = {
  contract_version: 1,
  meta,              // run constants + axis labels + affect conventions
  events,            // timeline event records
  interventions,     // per-intervention metadata (all 7)
  entities,          // engine-derived entity layer (factions + outlets)
  runs,              // { baseline } — the only full per-tick run (Method-B subsample)
  counterfactuals,   // all 56 intervention runs, LEAN
}
```

`contract_version` appears both at top level and inside `meta`.

Constants for the canonical run: **`n_agents = 250`**, **`n_ticks = 136`**
(ticks `0…135`), **`ticks_per_year = 3`**, **`tick_0_year = 1980`** (so
`year = 1980 + tick/3`; tick 135 ≈ end of 2025).

---

## `meta` (~1 KB)

| Field | Type | Notes |
|---|---|---|
| `contract_version` | int | `1` |
| `n_agents` | int | `250` |
| `n_ticks` | int | `136` |
| `tick_0_year` | float | `1980.0` |
| `ticks_per_year` | float | `3.0` |
| `axes` | object | `{x:{label,lo,hi}, y:{label,lo,hi}}` — economic (x) / cultural (y) |
| `release_years` | object | `{"<tick>": <year>}` for the 8 counterfactual release ticks |
| `affect_scale` | object | affect conventions — see below |

> **Retired:** named characters were retired; as of the Method-B baseline
> (2026-06) the `chars` top-level key and the `charAffect` / `charFaction`
> per-run keys are **removed entirely** (not just empty), along with the publish
> character-selection + agent-protection machinery. Older bundles may still carry
> them; they are not part of the live contract.
>
> **Baseline representation (2026-06):** `runs.baseline` is the model's faithful
> **ensemble center** — K=8 clean seeds pooled, a reproducible uniform 250-agent
> cross-seed subsample (deterministic given `meta`/manifest `subsample_rng_seed`).
> It preserves the model's true within-party dispersion (validated vs per-index
> averaging: `docs/results/method_ab_verdict.md`). `runs.baseline.macro` is the
> **ensemble mean**; `runs.baseline.macro_ctrl` is the single-seed
> (`intervention_seed`) macro the **single-seed intervention Δ is differenced
> against** (so the blessed phase10 buckets are preserved). The
> single-canonical-seed convention is retired.

### `meta.affect_scale`

Affective polarization is a **two-series** quantity, and the two series have
**different provenance** — this is the single most important honesty note in
the contract.

- `out_party` — **engine-measured.** Fields `runs.baseline.affect`,
  `macro.aff`, and `counterfactuals.*.aff`. Range `[-1, 1]`; more negative =
  colder toward the other party (`aff_out` semantics, mean out-party warmth).
- `degrees_note` — display-only mapping to an ANES-style thermometer:
  `deg = (1 - coldness) * 50 + 12` where `coldness = -w`. **Not** an engine
  metric.
- `in_party` — **EXTERNAL ANES overlay, NOT engine-produced.** Field
  `macro.aff_in_empirical`. Units: ANES feeling-thermometer degrees (0–100),
  trajectory ~72 (1980) → ~68 (2025). Ships only as a data-layer reference
  line so the front-end can draw the honest "scissors" (a flat-ish in-party
  line against the plunging out-party line). The engine does **not** model an
  in-party-warmth metric; do not present this line as a simulation output.

---

## `events` (~2 KB)

Array of the engine's timeline events (deduplicated by label). Each:

| Field | Type | Notes |
|---|---|---|
| `tick` | int | engine tick the event fires |
| `label` | string | engine event id (e.g. `fox_news_1996`) |
| `description` | string | human description |
| `actual_date` | string\|null | true `YYYY-MM` of history |
| `kind` | string | `media` / `decade_boundary` / `election` / `faction` / `elite_drift` / `crisis` / `other` |
| `evidence` | string | Step-1 evidence grade: `HIGH` / `MED` / `LOW` / `CONTESTED` / `MARKER` / `OTHER` |
| `evidence_note` | string\|null | one-line provenance / re-grade note |

Each event shocks real engine state; the mechanism lives in the engine
handlers (see audit Appendix B), not in the data.

**Step-1 evidence re-grade (engine `evidence_regrade=True`).** The web/ANES
build now attributes elite divergence to a discrete **`gingrich_1994`**
event (`kind: elite_drift`, `evidence: HIGH`), **demotes Citizens United** to a
non-causal era marker (`decade_2010_and_citizens_united` → `evidence: MARKER`;
late-period drift moves to the decade boundary), and **demotes the
social-media** affect coupling to a small contested accelerant
(`evidence: LOW`). The 2016 status-threat event is kept but graded
`CONTESTED`. Use `evidence` to badge the timeline honestly (well-evidenced
vs contested vs marker). See `docs/polarization_causal_model.md` §2.1/§4.3.

---

## `interventions` (~2 KB)

Metadata for **all 7** interventions (X1–X7), keyed by full intervention id
(e.g. `"X1_show_other_side"`). The `counterfactuals` block is keyed by the
same ids, so the two cross-reference directly.

| Field | Type | Notes |
|---|---|---|
| `id` | string | full intervention id |
| `label` | string | lay label |
| `color` | string | hex hint (FE may override) |
| `effect_buckets` | object | engine-measured bucket per metric (`sep`/`aff`) |
| `provenance_tags` | object | `{L:M, L:D, T, C}` literature/theoretical tag counts |
| `expected_naive_effect` | string\|null | the naive prior the predict-gate tests against |

---

## `entities` (~1 KB)

The engine-derived entity layer (audit §3.9). Sourced from engine constants in
`scripts/publish_web_data.build_entities_json()` → `web/data/entities.json`.

- **`factions_1980`** (8) — founding ideological blocs, from
  `HISTORICAL_FACTIONS_1980`. Each `{name, center:[x,y], weight, party}` where
  `party` is `0` (Dem) / `1` (Rep) / `null` (Centrist, party drawn).
- **`factions_emergent`** (4) — mid-run factions, hardcoded to mirror the
  ANES-knob emergence-event handlers in `abm/pillars/historical_arc.py`. Each
  `{name, emergence_tick, emergence_year, sub_centroid:[x,y], source_faction}`:

  | name | tick | year | sub_centroid | source |
  |---|---|---|---|---|
  | Tea_Party | 87 | 2009 | (0.58, 0.32) | Mainstream_Reps |
  | MAGA | 105 | 2015 | (0.60, 0.40) | Mainstream_Reps + New_Right_Religious |
  | Bernie_Progressives | 108 | 2016 | (-0.60, -0.40) | Mainstream_Dems |
  | DSA | 114 | 2018 | (-0.75, -0.65) | New_Left |

- **`outlets`** (5) — calibrated media outlets, from
  `US_MEDIA_OUTLETS_2024_ANES` (AllSides / Ad Fontes). Each
  `{id, name, pos:[x,y], color}`. Roster: MSNBC, New York Times, Local TV,
  Wall St Journal, Fox News.

Entities are **time-gated** by `emergence_tick` (emergent factions) and
should be drawn at the engine's real coordinates, not eyeballed placements.

---

## `runs.baseline` (~806 KB)

The canonical baseline trajectory — the **only** full per-tick run in the
bundle. (The old single-intervention X7 full run is dropped; interventions
now ship LEAN via `counterfactuals`.)

| Field | Type | Shape | dtype | Size | Notes |
|---|---|---|---|---|---|
| `release_tick` | int\|null | — | — | — | `null` for baseline |
| `pos` | array | `[136][250][2]` | float 3dp | ~488 KB | per-agent (x,y) ideology each tick |
| `party` | array | `[136][250]` | int | ~67 KB | `0`=Dem, `1`=Rep, `2`=Independent |
| `affect` | array | `[136][250]` | float 3dp | ~209 KB | **§1** full-crowd out-party warmth ∈ [-1,1] (`aff_out`) |
| `macro` | array | `[136]` | object | ~25 KB | per-tick macro metrics — see below |
| `faction` | object | `{tick: [250]}` | string\|null | ~8 KB | **§6** SPARSE crowd faction labels |
| `macro_ctrl` | array | `[136]` | object | ~25 KB | single-seed (`intervention_seed`) macro — the control the intervention Δ is differenced against (buckets preserved). Baseline only. |
| `replacement_events` | array | `[N][2]` | int | ~1 KB | `[tick, agent_id]` of every cohort replacement (ghost-fade) |

**Dropped in v1:** `net` (network snapshots, ~218 KB) — no v1 society-level
view consumes them.

### `runs.baseline.macro[t]`

| Key | Type | Notes |
|---|---|---|
| `sep` | float | party separation (centroid gap proxy), ~0.30 → ~0.99 |
| `aff` | float | engine out-party warmth (`aff_out`), ∈ [-1,1], ~-0.25 → ~-0.71 |
| `varr` | float | position variance |
| `mod` | float | network modularity |
| `xc` | float | cross-party edge fraction |
| `pc0` | [x,y] | **§5** party-0 (Dem) centroid, 3dp |
| `pc1` | [x,y] | **§5** party-1 (Rep) centroid, 3dp |
| `identity_alignment` | float | Mean mega-identity alignment across partisans, ∈ [0,1]; the explicit "stacking" state that drives out-party animus (Mason 2018). **Step-2 flag-1 fix: now RISES ~0.22 (1980) → ~0.42 (2025), monotone, ~doubling** — the cohort identity-reseed + faster identity-sort (regrade-gated) corrected the prior flat-to-declining trajectory. `0.0` when `evidence_regrade` is off. |
| `aff_in_empirical` | float | **§2** external ANES in-party warmth (degrees); NOT engine |

### `runs.baseline.faction` (sparse)

Keyed by tick string; value is the full 250-length faction label array.
Shipped only at the emergence ticks + endpoints:
**`{0, 87, 105, 108, 114, 135}`** (6 keys). Other ticks are not shipped —
the front-end interpolates membership from emergence events if needed.

---

## `counterfactuals` (~260 KB)

All **56** intervention runs (7 interventions × 8 release years), shipped
LEAN. Shape: `counterfactuals[<intervention_id>][<release_year>]`, where
`<intervention_id>` matches the `interventions` keys and `<release_year>` is a
string (e.g. `"2010"`). Each entry:

| Field | Type | Shape | dtype | Notes |
|---|---|---|---|---|
| `release_tick` | int | — | — | tick the intervention was applied |
| `sep` | array | `[136 - release_tick]` | float 4dp | macro party-separation, sliced `release_tick → end` |
| `aff` | array | `[136 - release_tick]` | float 4dp | macro out-party warmth, sliced `release_tick → end` |
| `endpos` | array | `[250][2]` | float 3dp | per-agent endpoint (tick-135) positions |

The `sep`/`aff` series start at the release tick (the branch point) so the FE
can draw a ghost line splitting from the baseline. To align a counterfactual
sample at index `k` to an absolute tick: `tick = release_tick + k`.

Release ticks/years: 15/1985, 30/1990, 45/1995, 60/2000, 75/2005, 90/2010,
105/2015, 120/2020.

---

## Provenance summary (what is and isn't the engine)

| Series | Provenance |
|---|---|
| `pos`, `party`, `affect`, `macro.{sep,aff,varr,mod,xc,pc0,pc1}`, `macro_ctrl`, `faction`, `replacement_events`, all `counterfactuals` | **engine** (phase10 / anes_full; baseline = Method-B 8-seed ensemble subsample; interventions = `intervention_seed`) |
| `entities.factions_1980`, `entities.outlets` | **engine constants** (`HISTORICAL_FACTIONS_1980`, `US_MEDIA_OUTLETS_2024_ANES`) |
| `entities.factions_emergent` | **engine-mirroring constants** (hardcoded from the ANES-knob emergence handlers) |
| `macro.aff_in_empirical` | **EXTERNAL ANES overlay — not engine** |
| `meta.affect_scale.degrees_note` mapping | **display-only**, not an engine metric |
