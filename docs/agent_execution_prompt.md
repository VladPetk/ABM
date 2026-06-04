# Executing the Calm to Camps roadmap — agent task prompt

*A self-contained kickoff prompt for a fresh agent (no prior context) to execute
the redesign roadmap, one step at a time, spec-first. Hand the agent this whole
file, or paste the "PROMPT" block below. After Step 0, reuse the same prompt and
just change which step is "current" (see the last section).*

---

## ▼ PROMPT (give this to the executing agent)

You are picking up an in-progress project called **polarlab / "Calm to Camps"** —
a Python agent-based model (ABM) of US political polarization (1980→2025) plus a
web demo that visualizes it. You are working in an existing repo on the branch
**`web-redesign-ideas`**. Three planning documents already exist and are
authoritative; **read them before doing anything else**, in this order:

1. **`docs/execution_roadmap.md`** — the master plan. The step-by-step sequence
   you are executing. This is your spine.
2. **`docs/web_demo_audit.md`** — the front-end audit: every current-state fact,
   the §3 design decisions, the §4 site↔engine fidelity matrix, the §5 engine/data
   gaps, the §7 backlog. Cited throughout the roadmap.
3. **`docs/polarization_causal_model.md`** — the "truth-model" the engine should
   encode (esp. §4.3, the engine change list). Relevant once you reach engine work.

Then ground yourself in the actual system as needed for the current step:
- Engine: `README.md`, `docs/ENGINE_OVERVIEW.md`, `docs/INTERVENTIONS_OVERVIEW.md`,
  `docs/results/phase10_results.md`, the code in `abm/`, and the data pipeline
  `scripts/publish_web_data.py` + `scripts/repack_web_demo.py`.
- Web demo: `web_demo/` (React 18 + Babel-standalone, no build step; entry is
  `web_demo/Calm to Camps.html`, data is `web_demo/cc-data.js` = `window.CC_DATA`).
  The previous version is in `web_demo/OLD_VERSION/` — ignore it.

### How we work (read this twice — it is the most important instruction)

We move through the roadmap **one step at a time**, and within each step you run
this loop:

1. **SPEC.** Produce a detailed spec/plan **for the current step only** — what
   you'll change, exact file/function targets, the data shapes or UI behavior,
   trade-offs, risks, and how you'll verify. Do **not** write or change any code
   yet.
2. **AGREE.** Present the spec to the user and **stop for explicit sign-off.**
   Iterate on it until they approve. Surface any real decision points as
   questions rather than guessing.
3. **EXECUTE.** Only after approval, implement exactly what was agreed. Keep the
   diff scoped to this step.
4. **VERIFY.** Test it (run the relevant test suite; for front-end work, render
   the page and check it; diff data sizes; etc.) and confirm it does what the
   spec said.
5. **REPORT & STOP.** Summarize what changed and the verification result, then
   **stop and wait.** Do **not** start the next roadmap step until the user
   releases it.

Do not run ahead. Do not batch multiple roadmap steps. Do not make code changes
before the spec is approved.

### Hard rules / guardrails

- **The engine is calibration-sensitive.** It has ~200 tests pinned to literature
  targets, and the realistic interventions are "bit-blessed" against a
  calibration. **Any change that alters engine output is bit-changing and owes a
  re-bless + re-measure cycle.** Do not touch engine logic in steps that are
  supposed to be data/frontend-only. When a step *does* involve the engine, treat
  re-validation and re-measuring the Phase-10 intervention buckets as mandatory.
- **Mock/illustrative data in the web demo is intentional** at this stage — don't
  treat "this is not from the engine yet" as a bug to fix unless the step says so.
- **Keep the realistic-vs-illustrative line bright.** Never let "what-if"/"tinker"
  scenarios or illustrative entities sit in the same list as engine-measured
  results.
- **Stay on `web-redesign-ideas`**; keep each step's changes scoped and reviewable.
- **Don't reintroduce deferred scope.** v1 is **society-level only** — the named
  characters / ego-networks / per-person beats are deferred. Don't build them.
- Use a task list to track sub-tasks, and include a verification sub-task.

### Your current step: STEP 0 — Lock the export/data contract + ship the cheap data wins

*(Full description: `docs/execution_roadmap.md` §2 "Step 0"; supporting facts:
`web_demo_audit.md` §5.1 and §2.3.)*

**Goal.** Define the exact data interface the frontend will consume, and ship the
**near-zero-cost** data that the engine already computes but the repack step
currently discards. **No engine logic changes in this step** — this is
publish/repack + schema work only.

The contract should cover (verify each against the code before speccing):
- **Per-agent affect, all agents, per tick** — already exported to
  `web/data/baseline/seed_0.json` (a 250-length `affect` array per tick); the
  repack (`scripts/repack_web_demo.py`) currently keeps it for only the 4
  character indices. Ship it for the whole crowd.
- **Per-release-year counterfactual trajectories** — 56 files already exist in
  `web/data/interventions/` (7 interventions × 8 release years); the repack ships
  only `baseline` + `X7`. Decide how to bundle/lazy-load them within a sane size
  budget.
- **Replacement events** — exist in the engine export (`replacement_events`),
  dropped by the repack. Ship them.
- **Faction positions + emergence ticks** — the 1980 founding blocs
  (`HISTORICAL_FACTIONS_1980`) and the emergent factions (Tea Party 2009 / MAGA
  2015 / Bernie 2016 / DSA 2018) with their sub-centroids and emergence ticks.
- **Outlet positions** — from `abm/core/outlets.py` (`US_MEDIA_OUTLETS_2024_ANES`).
- **In-party warmth series** — ⚠ the one likely wrinkle: the affect metric
  (`abm/metrics/affective.py`) currently computes **out-party warmth only**. Flag
  this in the spec as a decision point — either add a small in-party metric
  (a minimal engine/metric addition, so note the re-validation implication) or
  document a "flat in-party" assumption for the scissors chart. Don't decide
  unilaterally; put it to the user.

**Deliverable for this step's SPEC (no code yet):**
- The concrete data schema (fields, shapes, dtypes, and the on-disk/in-bundle
  size estimate per series), versioned.
- The exact list of `repack_web_demo.py` (and, if needed, `publish_web_data.py`)
  changes to produce it.
- A bundle-size budget and a load strategy (what's in the initial payload vs
  lazy-loaded).
- An explicit list of anything that needs **more than a repack** (in-party warmth;
  optional precomputed density grids) flagged for a user decision.

Produce that spec, present it, and **stop for sign-off** before implementing.

### Reusing this prompt for later steps

This prompt is step-agnostic except for the "current step" section. For the next
step, the user will point you at it (e.g., "now do Step 1"). When that happens:
re-read `docs/execution_roadmap.md`, identify that step and its dependencies
(note the gates — Step 2 must complete before Steps 4–5; Step 0 unblocks the
parallel frontend track in Step 3), and run the same SPEC → AGREE → EXECUTE →
VERIFY → REPORT & STOP loop. Always spec first; never run ahead.

## ▲ END PROMPT
