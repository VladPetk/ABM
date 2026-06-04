# Calm to Camps — Execution Roadmap

*The sequencing plan for taking the demo from its current mock build to a
truthful, society-level v1. Written 2026-05-31, branch `web-redesign-ideas`.
Sits alongside the two analysis docs and tells you **in what order** to do the
work they describe:*

- *[`polarization_causal_model.md`](polarization_causal_model.md) — the "step 0"
  truth-model the engine should encode (esp. §4.3, the engine change list).*
- *[`web_demo_audit.md`](web_demo_audit.md) — the front-end audit (the §3
  decisions, §4 fidelity matrix, §5 engine/data gaps, §7 backlog).*

---

## 0. Guiding principles

1. **Engine-truth first.** Which chapters, which intervention buckets, where
   entities sit, what the affect map even shows — all are determined by the
   engine. Settle it first so we don't build the frontend twice.
2. **"Within the literature envelope," not "full match."** Several key things are
   genuinely contested (magnitude of elite asymmetry; status-threat vs economics;
   the sorting→affect coefficient). The target is *defensibly within the envelope,
   with contested knobs flagged and tunable* — not a precision that doesn't exist.
   **Timebox the engine pass** so it doesn't become an open-ended sink.
3. **A locked data contract enables parallelism.** Fix the export interface early;
   then the engine track and the frontend track move in parallel instead of
   strictly serial. Most contract additions are near-zero-cost repack changes.
4. **Society-level only for v1** (characters deferred — see §1).

---

## 1. Scope decision: characters deferred (society-level only)

**Decision.** v1 is **society-scale only.** The four named characters
(Linda/Bob/James/Maria), ego-networks, per-character beats, and the "make it
personal" spotlight layer are **deferred to a later version**, not built now.

**What this removes / simplifies:**

- No ego-network mini-graph, no per-character beat authoring, no spotlight overlay
  (drops audit §3.7 entirely for v1).
- The affect view simplifies to the **aggregate** scissors + density — no
  per-person thermometer needed.
- It sidesteps the individual-drift-vs-stability optics (no spotlighted person
  visibly flipping parties), which **lowers the priority of the engine's
  party-stickiness / formative-imprinting fix** for *this* demo — that change
  stays good for truthfulness but is no longer fixing a visible artifact.

**What it costs:** the personal/emotional hook. The society-level scissors +
density + the predict-then-reveal interventions must carry the story alone — which
means **the affect view's legibility rises in priority** (it's now the main way a
viewer *feels* the change). The character layer can return in a later version
without rework, since the engine already exports the per-character data.

---

## 2. The sequence

Same backbone as the original plan, with a data-contract front door,
parallelization, and an explicit re-measure gate.

### Step 0 — Lock the export/data contract + ship the cheap data wins
*Goal: fix the interface so engine and frontend can proceed in parallel.*

- Define the exact series the frontend consumes: **per-agent affect (all
  agents)**, **per-release-year counterfactual trajectories**, **replacement
  events**, **faction positions + emergence ticks**, **outlet positions**, and an
  **in-party-warmth series** (for the honest scissors).
- Ship the **near-zero-cost repack wins now**, against the *current* engine
  output, so the frontend redesign can start immediately: per-agent affect,
  intervention trajectories, replacement events, faction/outlet positions (all
  already computed; only the repack drops them — audit §5.1).
- **Exit criteria:** a published `cc-data.js` (or successor) carrying the full
  contract; a one-page schema the frontend can build against.

### Step 1 — Engine truth pass (timeboxed)
*Goal: make the model defensibly within the literature envelope. Source:
[`polarization_causal_model.md` §4.3](polarization_causal_model.md).*

Split into two buckets:

- **Must-settle (trajectory-changing — gates downstream content):**
  re-grade the period shocks (move elite-drift emphasis to **Gingrich/1994**;
  demote **social-media-as-affect-cause** to small/tunable; reconsider
  **Citizens-United-as-elite-drift**; keep Fox/cable; keep 2016 threat but flag
  contested), and make **identity stacking** explicit so affect is driven by
  alignment (the missing master mechanism).
- **Refinements (can iterate after v1):** coupling-heterogeneity / engagement
  axis + activist→elite feedback loop; party-stickiness / formative imprinting
  (de-prioritized now that characters are deferred); a separate
  anti-democratic-attitude state (only if democracy claims are ever wanted).

- **Exit criteria:** engine output sits within the documented envelope; contested
  knobs are flagged/tunable; the must-settle items are done. *Don't chase the
  refinements before v1 ships.*

### Step 2 — Re-validate → re-measure → re-publish
*Goal: lock the numbers the frontend will display. This is the hazard step.*

- Re-run the test suite (~200 tests pinned to literature targets).
- **Re-measure the Phase-10 intervention buckets** — bit-changing engine edits in
  Step 1 can move X1/X5/X6 numbers; the interventions content (Step 4) cannot be
  finalized until this is done.
- Re-publish all data against the Step-0 contract.
- **Exit criteria:** green test suite; a fresh `phase10` measurement; republished
  data the frontend re-points to.

### Step 3 — Frontend structural redesign *(parallel with Steps 1–2)*
*Goal: fix the architecture and the two broken screens. Builds against the
contract, re-points to final data when Step 2 lands. Source: audit §3.1, §3.5,
§3.6, §3.9.*

- **Merge Watch + Explore** into one canvas (guided → unlock controls); lead with
  the payoff morph; promote a chapter rail (§3.1).
- **Rebuild the affect view** — aggregate **scissors** thermometer primary +
  party-tinted density + felt-distance tether; retire the ash-blob mock (§3.5).
  *(Highest priority now that the demo is society-level only.)*
- **Density readability** — filled heatmap, two-overlay party fields,
  small-multiples strip, centroid tether (§3.6).
- **Entity-class architecture** — the framework that drives entities from the
  engine (§3.9), ready to receive final faction/outlet positions from Step 2.
- **Exit criteria:** the new shell runs on contract data; affect + density read
  clearly; entity framework in place (content filled in Step 5).

### Step 4 — Interventions
*Goal: the demo's interactive payoff, made honest. Content gated on Steps 1–2;
UX shell can be built during Step 3. Source: audit §3.4.*

- Show **all 7 interventions with their true (re-measured) buckets**; restore
  X2/X4/X6; correct X3/X5/X7.
- Replace the cosmetic spread-animation with the **real counterfactual
  trajectory** (branching ghost-line from the chosen release year).
- Keep the **predict-then-reveal gate** and "Hope vs what happened" (now wired to
  real numbers); add **field-tested vs theoretical** provenance badges;
  **quarantine** the what-if / tinker sandbox.
- **Exit criteria:** every displayed number traces to the re-measured engine;
  sandbox is visibly walled off.

### Step 5 — Chapters + entities
*Goal: apply the right content once the engine's events/factions/outlets are
final. Source: audit §3.2, §3.9.*

- Re-anchor chapters to the **evidence-graded set** (audit §3.2): keep Fox/cable
  and Trump/threat; reframe social-media as contested; move elite-drift to
  Gingrich; add identity-sorting (Mason) and Obergefell-as-counter-example;
  demote Citizens United.
- Fill the entity layer: outlets from engine positions, **emergent factions
  (Tea Party/MAGA/Bernie/DSA) time-gated to their emergence years**, retire the
  ad-hoc static politicians (or keep a few as sourced, era-gated, clearly-labeled
  reference anchors).
- **Exit criteria:** chapters map to events the engine models; entities are
  engine-derived and time-gated; provenance labeled.

### Step 6 — Polish & hygiene
*Source: audit §7 P3.*

- Copy correctness pass (animus-not-love; contested framings).
- Remove dead/legacy code (`ConceptStory`, unused `ProtoCharacter`, stale
  cc-shared intervention table — the conflicting-table hazard).
- Label illustrative elements; reconcile `ENGINE_OVERVIEW` Δ numbers with phase10.

---

## 3. Dependencies & what runs in parallel

```
Step 0 (contract + cheap data)  ──┬─────────────────────────────────────────────┐
                                  │                                              │
   ENGINE TRACK                   │            FRONTEND TRACK (parallel)         │
   Step 1 (engine truth pass)     │   Step 3 (shell redesign: merge, affect,     │
        │                         │            density, entity framework)        │
        ▼                         │            — builds on the contract,          │
   Step 2 (re-validate,           │              re-points to final data ────────┘
           re-MEASURE buckets,    │                         │
           re-publish) ───────────┴──────────► gates ──────►│
                                                            ▼
                                              Step 4 (interventions: true buckets,
                                                      real trajectories)
                                                            │
                                                            ▼
                                              Step 5 (chapters + entities, final data)
                                                            │
                                                            ▼
                                              Step 6 (polish & hygiene)
```

**The gates that matter:**

- **Step 2 gates Steps 4 and 5** — intervention buckets and entity/event content
  can't be final until the engine is settled and re-measured.
- **Step 0 unblocks Step 3** — once the contract exists, the frontend shell builds
  in parallel with the engine track; only the *final data re-point* waits on Step 2.
- **Step 3's UX shells** (intervention workbench, entity framework) can be built
  before their *content* lands from Steps 4–5.

---

## 4. Hazards to watch

1. **Re-measuring interventions is mandatory, not optional.** Any bit-changing
   engine edit invalidates the Phase-10 buckets; treat Step 2's re-measure as a
   hard gate before touching intervention content.
2. **Re-bless discipline.** The realistic interventions are bit-blessed against
   the calibration; engine edits owe the re-bless gate. Budget for it.
3. **Timebox the engine pass.** "Within envelope, contested knobs flagged" — not
   "perfect." Don't let Step 1 block everything chasing unreachable precision.
4. **Affect view is now load-bearing.** Society-level-only means the affect view
   is the main emotional payload — prioritize its legibility (Step 3) accordingly.
5. **Keep the realistic vs illustrative line bright.** As engine and mock content
   converge, never let what-if/tinker scenarios or illustrative entities sit in
   the same list as engine-measured results.

---

## 5. One-line summary

*Lock the data contract and ship the cheap wins; settle the engine to within the
literature envelope and re-measure; rebuild the frontend shell in parallel; then
pour in honest interventions, evidence-graded chapters, and engine-derived
entities — all society-level, characters deferred.*
