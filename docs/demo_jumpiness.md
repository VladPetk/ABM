# web_demo investigation — jumpy dots

*A working memo, not a spec. Findings on why the prototype's agent
dots jump around, and the plan to tame them.*

---

## 1. What's actually happening

Quantified the baseline run (250 agents × 136 ticks) the prototype
ships with:

- **Per-tick step magnitude** median **0.065**, mean **0.075**, p99
  **0.21**. The compass is only 2 units wide, so the typical agent
  shifts **~3% of the compass every 4 months**, every tick, all
  decade. Even at the polarized end-state the step distribution does
  not shrink — there's no "settling."
- **Total path length** averages **10.2 units** per agent over 60
  years, against a **net displacement** of only **0.60**. Median
  **wandering ratio 18×** — agents take 18 units of path to net 1
  unit of movement.
- **Sharp turns >90°** on **half of step pairs** (median 68 of 134
  per agent). The dots oscillate, they don't drift.
- **39 agent-ticks** in the baseline have a single-tick step **> 1
  unit** (whole-compass teleport). 86 agent-ticks > 0.5.

The user's intuition is right: the dots are way too jumpy. It is
happening in the engine, not the viz, and it does not reflect real
life.

---

## 2. Three sub-problems with different causes

### 2.1 The "Linda" problem — cohort-replacement slot-reuse

Linda (agent 86) goes from (−0.58, 0.15) in 1980 to (+0.85, +0.59)
in 2025 — a full Democrat-to-Republican compass crossing. That
reads as one person flipping. It isn't.

`CohortReplacement` fires at ~0.003/tick (~0.9%/yr) and
**overwrites** an agent's position with a freshly-drawn one from
the new cohort's distribution. Of Linda's 5 biggest jumps, two are
~0.7 each — those aren't per-tick rule deltas, they're slot-reuse.
Across the whole baseline, *virtually every* >0.5 step is
`CohortReplacement` firing (~44% also flip party; the other ~56%
are same-party replacements where the new person lands on the same
side). So Linda's "wild compass tour" is really 2-3 different
people stitched together by slot ID.

The model is saying "this slot now belongs to a different person"
but the viz shows the same dot teleporting from progressive-left to
traditional-right.

### 2.2 Cross-compass wandering among non-characters

Beyond cohort replacement, the slower wandering is the per-tick
rule oscillation accumulated over 135 ticks. Per-tick step ~0.075
is far larger than the noise σ=0.01 alone would produce (~0.014).
The bulk comes from competing pulls firing every tick:

- BC influence: 0.08 × (target − pos), where target is the
  weighted-mean of neighbours, which themselves moved last tick.
- PartyPull: 0.07 × (party_cue − pos). Each agent's `party_cue` is
  noisy around the centroid, so the pull direction is partly random.
- MediaConsumption: 0.04 × (diet_mean − pos).
- FactionAnchor: 0.04 × (faction_center − pos) for tagged agents.
- ElitDrift continually shifts the centroids each tick.

These vectors don't align — they point in different directions,
their targets drift each tick, so the resultant per-tick delta
jitters in angle and accumulates as path length.

The free-mover tail makes this worse. Stubbornness Beta(2, 5) puts
~10% of agents below s = 0.05, with (1−s) ≈ 0.95 damping and a
tiny anchor pull (0.05 × 0.05 = 0.0025 per tick). Over 135 ticks
they can drift halfway across the compass on rule deltas alone.
The aggregate trajectory is robust to this tail per the Phase 8b
sweep, but the tail is visually dominant — those are the agents
that look most chaotic.

### 2.3 Tick-to-tick sharp turns (68 per agent median)

The amplitude problem and the direction-reversal problem are
separable. Lowering noise or smoothing in the viz reduces
amplitude. But the *reversals* persist unless deltas carry inertia
from one tick to the next. Real opinion change has momentum; the
engine currently doesn't — every tick's delta is recomputed from
scratch.

### 2.4 Discrete event spikes (Tea Party, MAGA, 2016 threat)

Faction-emergence events set `faction_center` on a sampled subset;
the subsequent ~5 ticks then pull those agents quickly toward the
new center via FactionAnchor. The 2016 threat event spikes
`perceived_threat` on 60% of party=1 agents, widening their
next-tick deltas. Visible as synchronized clusters of jumps around
1987, 1996, 2008-12, 2015, 2016. Mechanism is intentional —
faction emergence *should* show as a sort. These don't need a fix;
they're the model doing its job.

---

## 3. Plan

In increasing engine-invasiveness. Steps 1-3 are independent and
cheap — ship them together and measure before touching stubbornness
or momentum.

### Step 1 — Viz: EMA + ghost-fade + emit `replacement_events`

Replace linear-interpolation in `posAt` with a 3-5 tick EMA for
crowd dots; longer window (~9 ticks) for the spotlighted character.
Emit a per-tick `replacement_events: [(tick, agent_id)]` array in
the run export when `CohortReplacement` fires, so the viz
ghost-fades on *every* replacement — not just party-flipping ones,
since threshold-on-step-size misses the same-party half.

*~Half day viz + a few lines of engine export. No re-bless.*

### Step 2 — Engine: character-immunity flag for spotlighted agents

Agents 5, 28, 86, 134 get `attrs["do_not_replace"] = True`;
`CohortReplacement` skips them. Each character then becomes one
continuous life, ~40-60 years of slow drift, not a 3-person relay.
Highest-payoff single change because the spotlighted character is
what the user actually watches.

*~10 lines, no calibration impact* (replacement just lands on a
different slot).

### Step 3 — Engine: noise σ 0.01 → 0.005 in `historical_arc` only

Reduces jitter amplitude ~30% across the board. Stays within the
Phase 8b sensitivity envelope.

*Quick to verify with the existing sensitivity harness; no full
re-bless needed.*

### Step 4 — Engine: tighten the stubbornness tail

Either shift to Beta(2.5, 5) (mean 0.286 → 0.333, thinner low-s
tail) or bump `FJ_ALPHA` 0.05 → 0.08 (stronger pull back to
anchor). Pick one. Tames the free-mover wanderers without changing
the median agent much.

*Needs a re-bless run of X1-X7 to confirm buckets hold. Phase 8b's
sweep covered ±20% of α and the trajectory was robust, so this
should land in-bucket but the §11 gate has to confirm.*

### Step 5 — Engine: momentum term

One new per-agent attr `prev_delta`; the engine adds
`momentum × prev_delta` (suggest 0.4) to the summed delta before
applying. Half the oscillation cancels out because consecutive
deltas pull in opposite directions ~half the time. Physically
defensible — real opinion change has inertia — and shrinks
tortuosity dramatically. Highest payoff for the sharp-turns
problem once the cheaper fixes are in.

*Bit-changing; needs a full re-bless on X1-X7.*

### Step 6 — Last resort: keyframe-spline rendering

If steps 1-5 leave visible jitter the demo can't carry: snapshot
dot positions at {every 5 years} ∪ {event ticks} and cubic-spline
between them. Network cadence is already at event ticks so nothing
is lost there; macro metrics still computed at full per-tick
resolution. The cost is honesty — the rendered dot position is no
longer the engine's per-tick state, it's a smoothed visualization
of it.

*Treat as the escape hatch.*

---

## 4. Implementation status (2026-05)

Steps 1–5 shipped; step 6 deferred. (Step 4 was implemented in a second
pass after the first review.)

### 4a. Party-follows-position (added in review)

Discovered during review: **party can only change via cohort
replacement** — no rule touches it otherwise. So character immunity
(step 2) *structurally forbids* a spotlighted character from switching
party. The marquee "Linda becomes a Republican" arc was, mechanically,
the slot being reused by different people (exactly §2.1). To keep that
arc as one continuous person, added `abm/rules/party_realignment.py`
(`ProtectedPartyRealignment`): a `do_not_replace` agent's party follows
their *sustained* economic position — once x sits past ±0.12 for 6 ticks
it flips party, remaps the affect key, and re-aims `party_cue`.
Self-gates on `do_not_replace` → bit-identical for every non-demo run.

Character selection now scores on an **all-protected** run (every agent
immune + realigning), so party tracks position during scoring and the
party-keyed archetypes (stable-D, D→R swing, …) come out
position-coherent. The published baseline then protects only the 4
chosen. Result: Linda 86 D→R (drifts left→right), Bob 150 R→MAGA
(drifts right), Maria 117 D (drifts left), James 124 stable-D
(barely moves).

**Correction to §2.2 / step 3.** The memo assumed per-tick noise σ =
0.01. The shipped demo preset (`publish_web_data.ANES_FULL_KWARGS`)
actually overrides `GaussianNoise` to the anisotropic σ = **0.08**
(`tier_d_aniso_noise_sigma_x/y`). With mean stubbornness ~0.29,
`(1−s)·0.08·√(π/2) ≈ 0.07/tick` — which *is* the observed 0.065 median
step. So in the demo, noise is the dominant jitter source, not a minor
contributor. Step 3 was therefore applied to the real lever: **0.08 →
0.04** (halved), not 0.01 → 0.005.

- **Step 1 — EMA + ghost-fade + `replacement_events`.**
  `abm/rules/cohort_replacement.py` appends `[tick, agent_id]` to
  `env.attrs["replacement_events"]` (seeded as `[]` by
  `historical_arc.build_engine`; absent elsewhere → inert).
  `publish_web_data` emits it per run. The viz
  (`web_demo/cc-proto-engine.jsx`) renders an EMA of the position
  series — window 4 for the crowd, 9 for the spotlight — that **resets
  at each replacement tick** so a slot reuse is a cut, not a smear; the
  compass ghost-fades the departing dot over ~6 ticks.
- **Step 2 — character immunity.** `build_engine(protected_agent_ids=…)`
  sets `attrs["do_not_replace"]`; `CohortReplacement` skips those agents.
  `publish_web_data` scores archetypes on an unprotected pass, then
  publishes a protected pass so the 4 spotlighted characters are
  continuous lives. *Note:* this means the dramatic D→R "Linda swing"
  (largely a replacement artifact per §2.1) is gone by design — the
  procedural bios may need a re-read against the new continuous
  trajectories.
- **Step 3 — noise 0.08 → 0.04** (see correction above).
- **Step 5 — momentum.** `Engine.step` carries
  `env.attrs["momentum"]` × previous applied step into each tick's
  delta (stores the post-clip step as `prev_delta`; reset on
  replacement). Preset uses 0.4. Default 0.0 → bit-identical, confirmed
  by the existing canonical/pillar/phase4-5 suites (55 passed).
- **Step 4 — `fj_alpha_scale`.** `build_engine(fj_alpha_scale=…)` scales
  the FJ anchor-pull base (per-agent and the env default + cohort
  arrivals). Preset uses 1.6 (≈ 0.05 → 0.08), tightening the free-mover
  tail so agents drift instead of random-walking corner-to-corner.
  1.0 → bit-identical.
- **Step 6 — deferred.**

### 4b. Initial-condition tail truncation (added in review)

Review caught ~5 Democrat dots in the far *traditional-right* corner at
1980 (and the mirror for Republicans). Traced to the ANES IC path: party
is pre-committed 50/50, then position is drawn from a wide Gaussian
(σ≈0.35) around the party centroid (D≈(−0.09,+0.05), R≈(+0.27,+0.23)).
The centroids are only ~0.36 apart on the economic axis, so the tails
reach the opposite corner. The *mean* overlap is ANES-calibrated and
realistic (1980 had conservative Southern Democrats, liberal Rockefeller
Republicans; ~65% econ sign-alignment); the **extreme-corner** outliers
are a Gaussian tail-shape artifact, not a real phenomenon.

`build_engine(tier_d_ic_partisan_x_cap=…)` makes the economic IC draw a
*truncated* normal: a Democrat's pos_x is resampled to stay ≤ +cap, a
Republican's to stay ≥ −cap (bounded retry → clamp fallback). The
cultural axis is untouched — 1980 cultural overlap (traditional
Democrats) is historically real and should persist. Only consulted on
the ANES IC path; `None` → no truncation, and the cap=None code path
consumes the RNG stream identically (same two `rng.normal` draws, same
order) → bit-identical to head. Preset uses **0.45**.

Effect at 1980 (seed 0): Democrats past x>0.45 **8→0**, Republicans
past x<−0.45 **4→0**, far traditional-right corner **5→1** (the
remainder sits right at the cap edge, mildly cross-pressured). Mean
sign-misalignment preserved (~42%→39% of Democrats econ-right) — the
calibrated overlap stays, only the corner tail is removed.

### 4c. Replacement crossfade off-by-one + drift-tail thinning (round 3)

Second round of review found the "dramatic single-tick shifts" persisted.
Data: **82 single-tick steps > 0.5 unit** (up to 2.29 — corner-to-corner)
in the baseline, and **100% are `replacement_events`** (slot reuse — a new
person of the opposite party in the same id). These are turnover, not one
person moving (individual ideology/party-ID is highly stable in panel data:
Converse 1964; Green–Palmquist). The model mechanism is fine (cohort
replacement is a primary driver of aggregate change — Mannheim; Firebaugh
1989); the viz was mis-rendering it.

**Crossfade off-by-one (the actual bug).** A replacement logged at tick *t*
has `pos[t]` = the OLD person; the NEW person first appears at `pos[t+1]`.
But `emaSeries` reset the EMA at *t* (still old), so the *t→t+1* step
smeared across the compass — a visible slide that read as a single-tick
teleport. Fixed: reset the EMA at **t+1** (new track starts clean), and
anchor `replacementFades` at `pos[t]` for the departing dot. Replacements
now read as a true crossfade (departing dot holds + fades out; arriving dot
appears at its own location + fades in). `web_demo/cc-proto-engine.jsx`
only — no data change.

**Drift-tail thinning.** Among *never-replaced* (continuous) agents, 4.2%
drifted >1 unit over 45 yr — too fat a tail for genuine lifetime change.
`fj_alpha_scale` 1.6 → **2.8** brings this to 2.4% (≈ the 1-2% target).
The anchor lever is weak here (the tail is partly intrinsic — even fj=2.8
leaves a max ~1.28), but polarization is robust and within-party SD
improves. Still bit-changing → re-bless owed.

**Character re-selection.** The `linda` scorer rewarded `rightward * 2.0`,
i.e. it cherry-picked the single most extreme traveler (net 1.24). Rewrote
it to require a genuine left→right crossing but target a MODERATE journey
(~0.7 units, penalizing both a static label-flip and a corner-to-corner
odyssey). New Linda: net 0.74, smooth (max step 0.14), center-left D →
center-right R, flips ~2002.

All engine knobs default to their no-op values, so pillars + Phase 8/9
stay bit-identical (canonical/pillar/phase4-5/8b/9 suites pass: 77 +
129 across the two runs); only the demo preset opts in. The
bit-changing changes (momentum, fj_alpha_scale, the halved noise) have
**not** been through the §-gate X1–X7 re-bless — still owed. The demo
bundle is regenerated via `scripts/publish_web_data.py` then
`scripts/repack_web_demo.py` (→ `web_demo/cc-data.js`).
