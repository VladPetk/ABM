# Calm to Camps — Web Demo Audit & Redesign Spec

*Authoritative audit of the current `web_demo/` build (the new version that
replaced `web_demo/OLD_VERSION/`), produced 2026-05-31 on branch
`web-redesign-ideas`. This document records (1) what the build actually is
today, (2) where it's weak — visually, narratively, and scientifically — and
(3) what to do about it, with firm recommendations where the evidence/expertise
is clear and open options flagged where it isn't.*

*Method: full read of the live source (`cc-*.jsx`, `rc-*.jsx`, `cc-data.js`);
cross-read against the engine docs (`ENGINE_OVERVIEW`, `INTERVENTIONS_OVERVIEW`,
`methods`, `phase10_results`) and the publish/repack scripts; a headless-browser
render of every page and state (20 screenshots saved in
`docs/web_demo_audit_screenshots/`); a cited literature pass
on (a) which real events moved US polarization and (b) what interventions
actually do; and two expert reviews — a narrative/data-viz designer and a
computational social scientist — whose verdicts are folded in. **Nothing in the
build was changed.** This is a spec, not an implementation.*

> **How to read this.** §1 is the headline. §2 is the current-state inventory
> (what exists). §3 is the decision log, organized around the questions in the
> brief, each tagged **[FIRM]** or **[OPEN]**. §4 is the site↔engine fidelity
> matrix. §5 is the engine-feature / engine-science flag list. §6 is the
> claim/guardrail list. §7 is the sequenced backlog. Appendices hold the
> ground-truth tables and sources.

> **Framing note (the demo is intentionally mock).** The current build runs on
> mock/illustrative data by design — that is expected at this stage and is *not*
> itself the criticism. So read every "this is hardcoded / not from the engine"
> note below in two parts: (a) **what real engine output the view will need** to
> become true (the useful part), and (b) whether the *illustrative content is
> directionally right* — i.e. does the placeholder tell the lesson the engine and
> the literature will eventually tell? The serious problems flagged here
> (interventions, affect view) are cases where the mock is **directionally
> wrong**, so it will teach the wrong thing and have to be reworked — not merely
> "not yet wired up." A separate companion document,
> [`polarization_causal_model.md`](polarization_causal_model.md), works out the
> truth the engine itself should encode (the "step 0" model).

---

## 1. Executive summary

The build is **visually strong and narratively promising, but its substance has
drifted badly out of sync with the engine it claims to visualize** — and the two
hardest-working screens (the affect view and the interventions workbench) are
the two most broken.

**The five things that matter most:**

1. **The interventions layer misrepresents the engine and the science.** It
   shows 4 of 7 calibrated interventions, with **3 of the 4 buckets wrong**, the
   displayed Δ numbers **hardcoded and ~10× too small** (X1 backfire shows
   `+0.02` vs the engine's measured `+0.33`), and it **drops the single
   intervention that actually works** (X6 — shared neighborhoods/contact, the
   most empirically grounded lever there is) while elevating ranked-choice voting
   to "REAL EFFECT" though the engine says *partial* and the real-world evidence
   is essentially *null/theoretical*. The "reveal" is a cosmetic spread
   animation, not the real counterfactual — even though the engine has already
   computed the real per-tick counterfactual trajectories and they are sitting on
   disk. **This is the #1 fix and most of it is near-zero engine work.**

2. **The affect view is the user's stated #1 complaint, and it's worse than
   "hard to read" — it's self-contradicting.** In affect mode the build throws
   away party color and recolors the whole crowd on a single warm→ash "coldness"
   ramp, so it can only ever produce *one grey smear*. At the "Two Americas"
   (2020) chapter the copy says "two separate masses with almost nothing between
   them" while the picture shows a single elongated blob with no camps. It is
   also a **synthesized mock** (per-agent coldness from a hash function) even
   though the engine exports a real per-agent affect series that the data-pack
   step simply discards.

3. **The chapters are anchored to the wrong mix of events.** Some are well-
   evidenced (Fox/cable, Trump/status-threat). But the story leans on **drivers
   the literature treats as weak or contested** — social media as a *primary*
   cause (polarization rose fastest among the *least*-online; the big Facebook
   deactivation experiment was ~null) and Citizens United as a polarization
   engine (best-identified studies find no polarization effect) — while **missing
   the best-evidenced mechanisms the model can actually showcase**: the
   Southern/racial realignment, Gingrich-era asymmetric elite drift, Mason's
   identity "sorting," and Obergefell as the rare case where individuals
   genuinely changed their minds.

4. **Explore and Watch are ~80% the same screen.** Both render the same compass
   over the same baseline on the same timeline; Watch adds auto-pause beats,
   Explore adds free-scrub + annotations + sparklines. Two tabs for one canvas is
   a navigation tax. **Merge them:** guided story → hand over the controls on the
   same screen.

5. **The "make it personal" layer was dropped.** Four named characters
   (Linda/Bob/James/Maria) with bios, per-tick affect, ego-networks and authored
   beats exist in the data and as a fully-built component — but the live build
   uses none of them; Watch is society-voice only, with a literal "v2 slot"
   placeholder. The personal layer is the thing that turns a stats demo into a
   story; it's recovery, not invention.

**Two things the build gets right and must keep:** the **predict-then-reveal
gate** on interventions (placing a bet before the model answers is excellent
pedagogy and the source of the product's best moment — "exposure *backfires*?"),
and the **editorial craft + named-landmark map** (the Newsreader/warm-paper
aesthetic, one persistent compass as the spine, and real-world anchors like
Sanders/Cruz/Fox that give a layperson somewhere to stand).

**A cross-cutting scientific point (resolved in the companion causal model):**
the demo's core visual is "watch individuals drift across the map." A
literature pass ([`polarization_causal_model.md`](polarization_causal_model.md))
finds this is **mostly the right primary mechanic** — ideological *sorting* and
*affective* polarization are within-person/period phenomena, not generational
replacement, so within-person updating under a period elite/media signal is what
the engine *should* foreground. The narrower issues: (a) individual **party
switching** is on the high side versus the ~0.97 party-ID-stability finding (the
visible movement should be *position* drift toward a near-frozen party, not party
flipping), and (b) **cohort replacement** — which the engine models but the demo
doesn't ship — is the right *secondary* channel for the slower issue-attitude
story and should be surfaced. Net: don't make replacement primary; tighten party
stability and ship replacement. Details and engine mapping in the companion doc.

---

## 2. Current-state inventory — what the build actually is

### 2.1 Architecture

A single static page (`Calm to Camps.html`) loading React 18 UMD +
`@babel/standalone` (in-browser JSX compile, no build step) + a 1.6 MB
`window.CC_DATA` blob (`cc-data.js`). Source files:

| File | Role |
|---|---|
| `cc-unified.jsx` | **The live app.** The whole shell, three postures, static pages, story logic. `ReactDOM.render(<Unified/>)`. |
| `rc-story.jsx` | `STORY_BEATS` (the 6 chapters) + `ConceptStory` (an older standalone story page, **not mounted**). |
| `rc-interventions.jsx` | The interventions tray/rail/bottom + `useInterventions` state. **Hardcoded** intervention table. |
| `rc-shared.jsx` | `Field` (the compass canvas: in-browser KDE, contours, centroids, affect "ash" ramp, named entities), timeline, KDE math, `warmthDegAt`, the affect **mock**. |
| `cc-proto-engine.jsx` | Data layer over `CC_DATA`: `posAt`, `macroAt`, `tickToYear`, interpolation, playhead. |
| `cc-proto-panels.jsx` | `ProtoCharacter` (full character sidebar + ego-network), `ProtoTimeline`, `ProtoSparklines`. **`ProtoCharacter` is built and wired to real data but never mounted.** |
| `cc-pages.jsx` | `About` + `Methods` static pages. |
| `cc-shared.jsx` | Design tokens (`CC` palette, fonts) + **legacy** synthetic-agent model and a third, stale intervention table. |
| `cc-system.jsx` | Type scale, `Tag`/`Caption`/`MonoVal` primitives. |

**Dead/legacy code present in the build:** `ConceptStory` (rc-story),
`ProtoCharacter`/`ProtoEgoMini` (cc-proto-panels), and a legacy intervention
list + synthetic agent model + old event list (Reagan/Cold War/9-11) in
cc-shared. These are loaded but unused; they are also a source of the
**three conflicting intervention tables** in the codebase (see §3.4).

### 2.2 The three postures (Tier-2 mode bar) + a global Position/Affect toggle

- **WATCH** — guided story. Full-bleed editorial collage: floating prose block
  left, compass anchored right, draggable timeline + transport bottom. Plays
  forward and **auto-pauses at each of 6 chapters** (`STORY_BEATS`). Chapter 1 is
  a 5-step staged "orientation" that builds the map element-by-element
  (axes → labels → blobs → party rings → landmarks). Ends with a "that's how the
  camps formed / could anything have stopped it?" card → pushes to Interventions.
- **EXPLORE** — same compass, same timeline, **free scrub**. Prose rail flips
  between "Are they far apart?" (position) and "Do they hate each other?"
  (affect); shows a "what that feels like" calibration anchor (cross-party-
  marriage discomfort tied to live warmth), a live macro sparkline pair, floating
  event annotations that fade near event ticks, and a "Show parties" toggle.
- **INTERVENTIONS** — a workbench. Left tray (tiers: Realistic / What-if /
  Tinker), center compass frozen at 2025, right rail. Flow: pick → **predict**
  (helps / no effect / backfires) → **reveal** (field animates a spread
  multiplier) + guess scored + Δ stats + a "Hope vs what happened" track.
- **Static pages** (Tier-1 nav): **Model** (the app), **Methods**, **About** —
  clean editorial prose, render correctly.

### 2.3 What the shipped data actually contains (`CC_DATA`)

This is the crux of the fidelity problem. The data pack is far thinner than the
UI implies:

| Key | Contents | Note |
|---|---|---|
| `meta` | 250 agents, 136 ticks, 3/yr, 1980 start; `release_years` for ticks 15–120; `characters: [linda,bob,maria,james]` | — |
| `events` | 15 event records, each with tick, label/`description`, date, kind | Real engine events; the *mechanism* (which knob each shocks) lives in the engine handlers, not the data — see Appendix B |
| `interventions` | metadata for **all 7** (X1–X7): label, `effect_buckets`, `provenance_tags`, naive-effect copy | **The UI ignores this and uses its own table** |
| `runs` | **only `baseline` and `X7_perception_correction`** | Per-run: `pos[t][i]`, `party[t][i]`, `macro[t]`, `net{tick:[…]}`, `charAffect{idx:[…]}`, `charFaction` |
| `chars` | linda/bob/james/maria — name, agent_index, job, city, issues, bio, `beats[{tick,prose}]` | **Authored bios; procedural/placeholder beats. Unused by the live app.** |

Consequences: the interventions UI has **no real data** for X1, X3, X5, the
what-if tier, or the tinker mode — only `X7` is a real run, and `charAffect` is
present for only the 4 character indices, which is *why* the affect field falls
back to a synthesized mock for the whole crowd.

### 2.4 Visual read (from rendered screenshots)

- **Landing / editorial pages:** polished, confident typography; strong.
- **Position density:** attractive, but the **contour lines read as busy/noisy**,
  and the two party lumps overlap so heavily in early years that "two camps
  forming" is subtle even here. Named landmarks (Sanders, AOC, Manchin, Romney,
  Cruz; NPR/NYT/MSNBC/Fox; party rings) aid legibility and are a good idea.
- **Affect density:** **fails** — a single grey/ash smear with no camp structure
  (see §1.2), directly contradicting the paired copy.
- **Interventions:** the workbench layout, predict gate and "hope vs happened"
  track are well-designed; the numbers and the reveal are the problem (§3.4).

---

## 3. Decision log

Tagged **[FIRM]** where the call is clear (experts converged) or **[OPEN]**
where it's a genuine taste/strategy choice for Vlad.

### 3.1 User journey & page architecture — merge Explore into Watch **[FIRM]**

**Recommendation.** Kill **Explore** as a separate tab. Make the journey:
*landing → orientation → guided Watch → (on finish) the controls unlock on the
same screen for free exploration.* The Explore-only assets (calibration anchor,
macro sparkline pair, "Show parties" toggle, event annotations) move into the
unlocked end-state, not a parallel tab.

**Why.** Both reviewers independently called this high-confidence. Explore and
Watch are ~80% the same screen over the same baseline; two tabs for one canvas
in two modes makes the user re-orient twice for no payoff, and "guided, then let
go" is the proven museum/scrollytelling pattern — and it matches Vlad's own
instinct in the brief.

**First-30-seconds fix (highest-leverage single change).** Lead with the
**payoff before the lecture**: a ~3-second auto-played "1980 one cluster → 2025
two camps" morph with a six-word caption, *then* the staged orientation. A
non-expert's first question is "why should I care," not "what is the x-axis." Show
the thinning-but-surviving middle, not a vanishing one (honesty caveat from the
science lens).

**Chapters as a device — pattern choice [OPEN].** Auto-pause-on-beat (current)
fights the reader's clock (waits when they're ready, interrupts when they're
reading). The viz designer recommends **scroll-driven scrollytelling with a
persistent chapter rail** for random access. Strong default, but it's a build-
cost and trackpad-feel decision — flagged open. Minimum change regardless: add a
**visible chapter rail / "you are here"** so the story feels structured, not
open-ended. (A chapter rail of diamond pins already exists on the Watch
timeline; promote it.)

### 3.2 Which chapters — anchor to evidence-graded mechanisms **[FIRM on the principle; OPEN on final count]**

The brief's worry ("chapters are kind of random") is half-right: the current set
isn't random, but it's anchored to a **mix of strong and contested drivers** and
**misses the best-evidenced mechanisms the engine can model.** The principle both
the science lens and the events research converge on: **build chapters around the
five model-able mechanisms — media environment, elite/party drift, cohort
replacement, threat/animosity shock, identity/network sorting — and anchor each
to its best-evidenced event.**

**Current chapters** (`STORY_BEATS`): orientation (1980) · Fox/cable (1996) ·
social media + Obama (2008) · Citizens United + Tea Party (2010) · Trump/status-
threat (2016, → affect) · COVID/Jan 6 (2020).

**Recommended chapter set** (≈7; evidence grades from the literature pass —
full citations in Appendix C):

| # | Chapter (year) | Mechanism | Primarily moves | Evidence | Status |
|---|---|---|---|---|---|
| 1 | **One country, one cluster** (1980) + the realignment that set it up | elite realignment + cohort | ideological / sorting | **HIGH** (Kuziemko-Washington) | *Add the realignment framing* |
| 2 | **The parties pull apart at the top** — Gingrich / asymmetric elite drift (1994) | elite/party drift (GOP-asymmetric) | ideological (elite) | **HIGH** | **Add** (engine's elite-drift channel belongs here, not at CU) |
| 3 | **Sorting into mega-identities** (1990s–2000s, Mason) | identity/network sorting | the bridge ideological→affective | **HIGH** (Mason) | **Add** — this is the model's actual master mechanism |
| 4 | **Cable picks a side** (1996) | media supply shock | both | **HIGH causal** (DellaVigna-Kaplan; Martin-Yurukoglu) | **Keep** (best media chapter) |
| 5 | **The feed everyone blames** (2008–2012) | environment shift | (claimed affective) | **LOW / contested** | **Keep but reframe** as "the famous suspect the data won't convict" |
| 6 | **It stops being about policy** — Trump / status-threat (2016) | threat/animosity shock | affective | **MED** (Mutz; Morgan critique on magnitude) | **Keep** as the affect pivot, with the status-vs-economics caveat |
| 7 | **The exception: people actually changed their minds** — Obergefell (2015) | cohort replacement + genuine persuasion | ideological | **HIGH** (Rosenfeld; Lee-Mutz) | **Add** — the most valuable *teaching* chapter you're missing |

**Two specific verdicts:**

- **Citizens United (2010) as a polarization driver — drop or demote [FIRM].**
  The best-identified studies find GOP electoral gains but **no clear
  polarization effect**. Featuring it as a cause (and the engine encoding it as
  "doubles elite drift") launders a contested causal story. Fold the Tea Party
  *faction labeling* into the elite-drift chapter; don't claim CU drove the
  split.
- **Social media (2008–2012) as a *primary* cause — reframe, don't headline
  [FIRM].** Polarization rose fastest among the **oldest/least-online**; the
  Facebook deactivation experiment was ~null. Present it as the contested
  accelerant — *more* interesting pedagogically, not less.

**Designer-vs-science tension (resolved):** drama wants villains (CU, "social
media broke America"); science wants honesty. Resolution both reviewers
endorse: **keep the famous events on screen but flip their valence** to "the
suspect the data won't convict," and spend the genuine emotional beat on
**Obergefell** (where people *did* change). Honest *and* engaging.

### 3.3 Copy — proper but brief **[FIRM, light]**

The brief says keep copy brief ("we'll rewrite later"). The current copy is
serviceable placeholder; the fixes are mostly *correctness*, not prose:

- One precision fix everywhere: it's rising **out-party animus**, not in-party
  love. In-party warmth stayed roughly flat while out-party warmth collapsed —
  so "they came to *loathe the other side*," never "tribes that love their own."
- Make event copy match the evidence grade (e.g., the social-media chapter's
  body should signal "contested," not assert causation).
- Keep the two-voice structure (society + person) from the original plan once
  characters return (§3.7). Per the brief, leave full prose polish for a later
  pass; this audit fixes *what is claimed*, not the wordsmithing.

### 3.4 Interventions — the biggest fix **[FIRM]**

This is the most serious integrity problem on the site, and the brief's
instinct ("I don't quite like it... it just shows you two states... do they
actually reflect reality") is exactly right. There are **three conflicting
intervention tables** in the codebase (the engine's real one in `CC_DATA`, the
hardcoded UI one in `rc-interventions`, and a stale one in `cc-shared`), and the
UI uses the wrong one.

**What's wrong, precisely** (engine ground-truth in Appendix A):

| | Engine-measured (Phase 10) | Real-world evidence | **Current site shows** |
|---|---|---|---|
| X1 show the other side | **backfire**, Δsep ≈ **+0.33** | backfires if passive (Bail); *de*polarizes if anonymous/structured (Combs) | backfire, but Δ shown as **+0.02** |
| X2 fix the algorithm | **null/null** | null (Meta-2020/Guess) | **dropped** |
| X3 quit cable news | **null** | quitting weak; *switching* works (Broockman-Kalla) | shown as **"partial"** ✗ |
| X4 dialogue / shared-identity | **null** (dir-correct) | small, non-durable (Voelkel 2024) | **dropped** |
| X5 ranked-choice voting | **partial** on sorting, flagged **[T] theoretical** | **null / theoretical** (Donovan-Bowler; McGhee-Shor) | shown as **"REAL EFFECT"** ✗✗ |
| X6 shared neighborhoods (contact) | **real** on affect, Δaff +0.19…+0.27 | **works** on affect (Pettigrew-Tropp r≈−0.21) | **dropped** ✗✗✗ |
| X7 correct perception gap | **null** (mechanism works, doesn't propagate) | partial, short-lived (Lees-Cikara) | shown as **"partial" / "live model run helps a little"** ✗ |

The net effect: the site **drops its only real win (X6) and its flagship null
(X2)**, **inflates the shakiest lever (X5/RCV) to the headline "real effect,"**
**mislabels two nulls as partial**, and **hides the one big backfire** behind a
hardcoded `+0.02`. It inverts the engine's actual lessons.

**Recommendations:**

1. **Show all 7 calibrated interventions with their TRUE buckets and the real Δ
   numbers.** Restore X2, X4, X6; correct X3, X5, X7. The nulls are the lesson
   ("most popular fixes do nothing or backfire; only structural contact reliably
   helps") — a sharper thesis than a fabricated win.
2. **Replace the cosmetic spread-multiplier with the real counterfactual
   trajectory.** The engine already computes full per-tick counterfactuals for
   every intervention × release-year (they exist on disk; see §5); ship them and
   draw a **branching ghost line** that splits from the baseline at the chosen
   release year and plays to 2025, with the compass morphing to the *real*
   endpoint. This directly answers the brief's "play out the alternate scenarios"
   ask, at **near-zero engine cost**. It also makes the **release-year a real,
   teachable choice** ("try it earlier and it bends more" — a genuine dynamic in
   the data; X5 is strongest pre-cascade).
3. **Keep the predict-then-reveal gate and "Hope vs what happened"** — both are
   good — *but only once "what happened" is the real number.* Right now the
   device animates a value that contradicts the engine.
4. **Two-tier provenance badges, always visible:** "Field-tested" (X1 direction,
   X6) vs **"Theoretical — not yet supported by field evidence"** (X5/RCV and any
   model-only lever). The engine already carries `provenance_tags` per
   intervention; surface them.
5. **Hard-quarantine the invented "What-if" and "Tinker" scenarios** behind a
   visually distinct "Sandbox — not real interventions / this changes the
   *model*, not a policy" wall. They must never share a list with engine-measured
   results, or they teach false mechanisms.
6. **X1 magnitude caveat [FIRM].** Feature the *direction* (cross-party exposure
   can backfire — real, Bail) but **do not** present `+0.33` as "the real-world
   effect of touching grass": it's the engine's own flagged extrapolation, ~3×
   Bail's ~0.1 SD, and exposure flips sign when anonymous/structured. Label it
   model-specific.

### 3.5 Affect visualization — kill the ash blob **[FIRM]**

The user's #1 complaint, and both reviewers agree the current encoding is
fundamentally broken: you cannot show "they came to dislike *each other*" with a
single-luminance colormap that has forgotten *who* "each" is. Affective
polarization is a **relational, two-series** quantity.

**Recommendation (primary):** make the canonical **ANES "scissors" thermometer
chart** the primary, authoritative affect treatment — a flat-ish **in-party
warmth** line and a plunging **out-party warmth** line over time, in degrees
(≈the real 0–100 thermometer, high-40s → mid-20s). It's the most-replicated,
most-legible image in the actual literature; a layperson reads "the lines pull
apart" instantly.

**On the compass (companion, not primary):** keep the two **party-colored**
lumps and **tint each by out-party coldness**, plus an explicit **"felt
distance" tether** between the centroids that stretches as warmth falls. This
preserves the two-camp structure (which the ash ramp destroys) while still
letting you "feel it on the same map." Label it clearly as a *tint*, not a
position (a science caveat: affect is not a location on the economic/cultural
plane).

**Data fix (prerequisite):** replace the **synthesized per-agent coldness mock**
with the **real per-agent affect series** before making any per-agent animus
claim. The engine already computes it for all 250 agents every tick; the
data-pack step throws it away (§5). Recolor specifically by **out-party** warmth
so the asymmetry (cold toward them, warm toward us) survives — that asymmetric
picture is both more accurate and, frankly, more chilling than uniform grey.

### 3.6 Density readability — make calm→camps unmistakable **[FIRM]**

**Recommendation.** (a) Switch the busy **contour lines** to a smooth **filled
heatmap**; (b) render the two parties as **two overlapping party-colored fields**
rather than one blended KDE (the blend actively hides bimodality by melting the
lumps into one color); (c) add a **small-multiples strip** of ~4 years
(1980 / 1996 / 2010 / 2025) as an at-a-glance "unimodal → bimodal" proof that
needs no animation; (d) always show the **centroid-gap tether** widening as the
single scalar the eye can track. Honesty guard: normalize equal-area, show the
overlap zone, don't crush the middle to overstate the split.

### 3.7 Characters — reinstate as a toggleable layer **[FIRM, phased]**

**Recommendation.** Reinstate the "make it personal" layer, but **as a
toggleable overlay, not always-on, and start with 2 of the 4** characters. The
data and the `ProtoCharacter` component already exist — this is recovery. Ride
them as 1–2 highlighted dots that pulse at their relevant beat (e.g., a swing
voter watching cable in '96; a moderate squeezed out in '16), with that
character's thermometer ticking in the rail; let the user dismiss them. Four
bios + ego-networks over a KDE is how you re-introduce the clutter you're trying
to escape — two well-chosen arcs beat four thin ones.

**Honesty guard:** frame each as "one *simulated* American," anchored to an
aggregate stat shown alongside, so readers don't over-generalize. **Also:** the
shipped character "beats" are **procedural telemetry stubs** flagged in the
engine for rewrite — they need an authoring pass before they're public.

**Caveat that ties to §5:** highlighting individuals visibly drifting across the
map is exactly the visual that sits in tension with the individual-stability
literature. Characters are fine, but they make the §5.6 decision more urgent.

### 3.8 Events on the timeline — functional vs cosmetic **[FIRM, light]**

Good news: **every event the engine fires actually shocks state** — none are
cosmetic (Appendix B). The timeline already distinguishes functional shocks
(labeled) from context ticks. Keep that. The events worth *adding* are the ones
that (a) the literature supports and (b) showcase a mechanism the model has:
**Gingrich/1994** (elite drift), **Obergefell/2015** (cohort replacement —
pairs perfectly with the mechanism and the small-multiples view). Do **not** add
cosmetic-only labels; and reconsider the *causal framing* of the social-media
and Citizens-United events (§3.2, §5).

### 3.9 Compass entities (the named landmarks) — make them principled **[FIRM]**

The named points on the compass (Fox News, the politicians, the party/MAGA
markers) are a good *idea* — they give a layperson somewhere to stand on an
abstract plane — but the current set is, as suspected, ad hoc. Here is exactly
how they're placed, whether they move, and what to do instead.

**How positions are determined today.** Two disconnected systems:

- **Figures + media outlets** (`ENTITY_FIXED` in `rc-shared.jsx`): nine
  **hand-eyeballed** points — Bernie Sanders, AOC, Manchin, Romney, Cruz, and
  NPR, NYT, MSNBC, Fox. The code comment is explicit: *"Positions are
  illustrative placements, not engine output. — entities per Vlad."* No data
  source; no derivation.
- **Party aggregates** (`entityAggregates`): Democratic Party, Republican Party,
  and a "MAGA wing" — these *are* computed from the engine's **live party
  centroids** (the MAGA wing is the Rep centroid pushed outward by a constant
  0.46), so they move with the simulation.

**Do they move over time?** Mostly **no.** The figures and outlets are **static**
across the entire 1980→2025 run; only the three party aggregates ride the
centroids. (In Watch/Interventions only the static figures+outlets show; the
moving party aggregates appear only in Explore with "Show parties" on.)

**Why the current set is weak:**

1. **Anachronistic.** Static points are shown at all years — AOC and a Fox News
   marker sit on the 1980 map, years/decades before either existed. Entities that
   blink into existence (Fox 1996, the Tea Party 2009, MAGA 2015) can't be
   honestly drawn as fixed, ever-present anchors.
2. **Not derived from anything.** The figure/outlet coordinates are eyeballed, so
   they don't correspond to any measured ideology — and they **don't match the
   forces in the sim** (next point).
3. **Inconsistent with the engine, which already has better data.** The engine
   ships **calibrated media-outlet positions** (`US_MEDIA_OUTLETS_2024_ANES`,
   anchored to AllSides / Ad Fontes ratings) — and the website's hand-placed
   outlets disagree with them and even use a different roster:

   | Outlet | Site draws at | Engine's actual attractor | In engine? |
   |---|---|---|---|
   | Fox News | (0.60, 0.48) | **(0.85, 0.65)** | yes |
   | MSNBC | (−0.50, −0.56) | **(−0.80, −0.55)** | yes |
   | New York Times | (−0.58, −0.34) | **(−0.50, −0.30)** | yes |
   | NPR | (−0.42, −0.14) | — | **no** (site-invented) |
   | Wall St Journal | — | (0.60, 0.25) | yes (site omits) |
   | Local TV | — | (0.00, 0.05) | yes (site omits) |

   The outlets are the things that actually *pull* agents in the sim, so drawing
   them in the wrong place mislabels the very forces the map is about.
4. **The most informative entities — the engine's named clusters — are missing.**
   The engine carries eight **named ideological factions at 1980** with real
   positions (New Left, Mainstream Dems, Blue Dog Dems, Centrists, Classical
   Liberals, Mainstream Reps, Old Right, New Right Religious) and four
   **emergent factions with emergence ticks and sub-centroids**: **Tea Party
   (2009), MAGA (2015), Bernie Progressives (2016), DSA (2018)**. These are the
   entities that *are* the simulation's dynamics and that tie directly to the
   chapters/events — yet the site shows none of them (it invents a single static
   "MAGA wing" instead).
5. **Individual politicians aren't in the engine at all.** Sanders/AOC/Manchin/
   Romney/Cruz appear nowhere in `abm/`; they're pure illustrative anchors. That's
   allowable, but they're currently un-sourced, timeless, and somewhat arbitrary
   (and count-imbalanced — e.g., 3 left-leaning vs 1 right-leaning outlet).

**Recommendation — an entity system with provenance, movement, and time-gating.**
Define entities by class, each with a positioning source and a motion rule:

| Class | Examples | Position from | Moves? | Time-gated? |
|---|---|---|---|---|
| **Party centroids** | Democratic / Republican | engine live centroids | **yes** (with sim) | always on |
| **Emergent factions** | Tea Party, MAGA, Bernie, DSA | engine faction sub-centroids | **yes** — emerge at tick, drift with their cluster | **appear at emergence year only** |
| **Founding blocs** (optional) | New Right Religious, Blue Dog Dems, New Left | engine 1980 faction centers | mostly static early, fade as they re-sort | from 1980, retire as absorbed |
| **Media outlets** | Fox, MSNBC, NYT, WSJ, Local TV | **engine `outlets.py` (AllSides/Ad Fontes)** | static in engine today; *should phase in at launch* (Fox 1996) | gate by founding/relevance |
| **External reference figures** (optional, illustrative) | a few iconic politicians | external data (Voteview/DW-NOMINATE for economic axis + a documented cultural estimate) | period-appropriate, or omit | only when contemporaneous |

Principles:

- **Prefer engine-derived entities** (parties, factions, outlets) — they're honest
  because they *are* the forces in the sim, and they move correctly for free.
- **Use the engine's real outlet coordinates**, not hand-placed ones, so labeled
  outlets sit where the actual attractors are.
- **Feature the emergent factions** at their emergence years — they're the most
  informative entities and they reinforce the chapter/event story (Tea Party with
  the elite-drift chapter, MAGA with 2015–16, etc.).
- **Time-gate everything.** Nothing pre-dates its existence; entities appear,
  move, and (where appropriate) retire as the years run.
- **Politicians are optional and illustrative-only.** If kept, source their
  coordinates (don't eyeball), label them clearly as external reference points
  (not simulation agents), gate them to their era, and balance left/right and the
  four quadrants. Leaning on factions + outlets (engine-real) is the stronger
  default; a couple of iconic figures can stay as seasoning.
- **Label provenance** in-UI: distinguish *engine-derived* entities (move with the
  sim) from *illustrative external* anchors (fixed reference). The current build's
  legend already separates parties / people / outlets — extend that to say which
  are real sim quantities.
- **A note on the cultural (y) axis.** Most external ratings (Voteview economic
  dim; AllSides/Ad Fontes left–right) are essentially one-dimensional, so any
  *cultural*-axis coordinate for a figure or outlet is an estimate — document the
  source and treat y as approximate (the engine already did this when it widened
  outlet y-positions "proportionally" per Mason 2018).

**Engine note.** Two small truthfulness gaps worth flagging for the model, not
just the site: (a) the engine holds **outlet positions fixed** across 1980→2025
(only media *strength* turns on at the Fairness-Doctrine/Fox events) — real
outlets both launched at different times and drifted, so phasing outlets in (and
optionally drifting Fox rightward) would be more faithful; (b) the emergent
faction sub-centroids and the outlet roster are the natural, already-present
source for a principled entity layer — exposing them to the front-end is a
publish/repack change, not new modeling.

---

## 4. Site ↔ engine fidelity matrix

What's real, what's mock, what's hardcoded, what's wrong:

| Element | Status | Detail |
|---|---|---|
| Position density field | **Real** | In-browser KDE over engine agent positions (`baseline.pos`). |
| Macro sparklines (sep, aff) | **Real** | From `baseline.macro`. Sep 0.26→0.99, aff −0.25→−0.71. |
| Centroid gap / party rings | **Real** | Computed from positions. Gap 0.27→0.99 (verified). |
| Timeline events | **Real** | All 15 carry engine mechanisms (Appendix B). |
| Named landmarks (Sanders, Fox, …) | **Illustrative & ad hoc** | Hand-eyeballed, static, anachronistic; **disagree with the engine's calibrated outlet positions** and ignore the engine's named faction clusters. Full treatment + a principled entity system in **§3.9**. |
| **Per-agent affect / "animus" field** | **MOCK** | Synthesized via hash function. Engine has the real series; data-pack drops it. |
| Out-party "warmth degrees" | **Approximation** | `(1−coldness)·50+12` — synthesized to look right, not an engine thermometer metric. |
| Calibration anchor (marriage %) | **Illustrative** | Hand-written bands "in the spirit of" the finding; not data. |
| **Interventions X1/X3/X5 + what-if + tinker** | **HARDCODED / WRONG** | Made-up Δ numbers; 3 wrong buckets; reveal is a cosmetic spread multiplier. |
| Intervention X7 | **Real run** but **mislabeled** | The only real counterfactual shipped — and it shows **no meaningful effect** (Δsep = 0.00; Δaff ≈ +0.015 on the shipped single seed, i.e. negligible; the 9-seed sweep has it null/marginally-negative). The UI nonetheless sells it as "partial help / a live model run that helps a little." |
| Characters (Linda et al.) | **Real data, unused** | Bios authored, beats procedural; component built but not mounted. |
| Cohort-replacement events | **Computed, not shipped** | `replacement_events` exist in the engine export but are dropped in the repack — so the demo can't show replacement at all. |

---

## 5. Engine-feature gaps & engine-science flags

### 5.1 Aspirational asks — what's already supported vs needs work

The good news the engine mapping turned up: **the two biggest "aspirational"
asks need essentially zero new modeling work** — the data is already computed and
on disk; only the *compaction* step (`repack_web_demo.py`) discards it.

| Aspiration | Engine status | What's needed |
|---|---|---|
| **Play out intervention counterfactuals over time** | **Already supported** | `publish_web_data.py` writes 56 full per-tick counterfactual trajectories (7 × 8 release ticks). Repack ships only `baseline` + `X7`. → bundle the existing files. **No engine work.** |
| **Real per-agent affect field for the whole crowd** | **Already supported** | Engine exports a per-agent affect scalar for all 250 agents every tick into `baseline/seed_0.json`; repack keeps only the 4 character indices. → ~5-line repack change. **No engine work.** |
| **Density at higher agent counts / cleaner field** | **Partial** | `n_agents` is a free parameter (no cap); a `kde_2d_on_grid` helper exists but isn't wired to export. → small export glue; optionally a density-only pass at higher N. |
| **Named characters w/ real per-tick affect + network** | **Mostly supported** | Per-tick affect/party/faction for the 4 characters already export; full network snapshots at 14 ticks. → finer per-character network + an authored-beats pass. |
| **Add new events (Gingrich, Obergefell)** | **Supported, per-event work** | Events are handler functions mutating rules/state. → write a handler per event + re-run publish + re-bless affected fixtures. *Engine change, not UI-only.* |
| **Stacked interventions / custom seeds / per-tick release** | **Not in MVP scope** | Deferred (Path B / API) per the original plan; not needed for this redesign. |

### 5.2 Engine-science flags — where the *model* (not just the site) diverges from the literature

These are for the modeling team to decide on; flag regardless of UI:

1. **Citizens United → "doubles elite-drift rate."** Hard-codes a causal effect
   the best-identified studies don't find. Consider decoupling elite drift from
   CU and attaching it to the Gingrich/1994 chapter.
2. **Social media → real affect shock** (`affect_weight` up, 2008/2012). Treats a
   contested/~null driver as a genuine state shock. Consider making it a tunable,
   off-by-default accelerant rather than an asserted cause.
3. **X1 backfire magnitude (+0.33).** ~3× Bail's ~0.1 SD; flagged internally but
   propagates to a headline. Direction is defensible; magnitude is an
   extrapolation — keep it labeled model-specific.
4. **X5/RCV "partial helpful."** A model-internal artifact of how RCV is encoded;
   direct RCV empirics are null. Already `[T]`-flagged in the engine docs — must
   stay flagged in the UI.
5. **Elite drift asymmetry — verified present and correct.** The engine *does*
   model per-decade asymmetric elite drift (R-heavy early/Reagan, D-heavy late
   under ANES knobs), matching the literature's asymmetry finding. (Not a gap —
   recorded here because the science review asked to confirm it.)
6. **Individual drift vs cohort replacement — now resolved in the causal model.**
   A first draft of this audit called individual drift the wrong primary
   mechanism. The literature pass corrects that: **ideological sorting and
   affective polarization are within-person/period effects, not generational
   replacement** (affect rose across *all* cohorts at once, fastest among the
   *oldest/least-online*) — so within-person drift under a period elite/media
   signal *is* the right primary mechanic. Two narrower fixes remain: (a)
   individual **party switching** is high versus the ~0.97 party-ID-stability
   finding — verified in the shipped baseline, median agent displacement **0.56**
   units on the [−1,1]² plane (p90 1.12) and **39/250 agents change party label**;
   the visible movement should be *position* drift toward a near-frozen party
   (add formative-years imprinting), not party flipping; and (b) the engine runs
   a `CohortReplacement` rule but the demo **doesn't ship `replacement_events`**,
   so the slower *issue-attitude* turnover story can't be shown — surface it as
   the secondary channel. **Do not make replacement primary.** Full reasoning and
   engine mapping: [`polarization_causal_model.md`](polarization_causal_model.md)
   §4.

> Note on doc drift: `ENGINE_OVERVIEW.md §5` quotes intervention Δ magnitudes
> from the *older pillar* engine (e.g., X1 +0.50), which differ from the shipped
> historical-arc numbers in `phase10_results.md` (X1 +0.33). Use **phase10** as
> ground truth for the web build; consider reconciling the overview doc.

---

## 6. Scientific-integrity guardrails

**Honest framing the site should adopt (short):**

> This is a calibrated *teaching model*, not a forecast. Its core, well-supported
> lesson: Americans' *issue positions* barely moved while their *feelings toward
> the other party* curdled — polarization is mostly rising animus, driven by
> identity sorting and an asymmetric elite/media environment acting *within*
> people over time (not by individuals switching parties, and not mainly by
> generational turnover). Where the evidence is strong (partisan
> cable, sorting, realignment, contact as a remedy) we say so; where it's weak or
> contested (social media as cause, Citizens United, ranked-choice voting as a
> fix) we flag it. Read intervention results as *what this model implies* —
> sometimes extrapolated past the field evidence — not as policy proof.

**Claims the site must NOT make:**

- "Social media caused polarization." (contested/weak)
- "Citizens United drove polarization." (null causal evidence)
- "Ranked-choice voting fixes polarization / RCV: real effect." (null/theoretical)
- "Showing people the other side backfires by +0.33" as a real-world magnitude.
- "These four [invented what-if] interventions would work." (no provenance)
- "Watch individuals abandon their party and cross the map" as the literal
  mechanism of aggregate change. (contradicts individual stability)
- Any per-agent animus claim backed by the synthesized mock.
- "Reducing affective polarization protects democracy." (Voelkel 2023: affect
  reduction is easy, small, non-durable, and does *not* reliably reduce
  anti-democratic attitudes — a crucial don't-overclaim.)

---

## 7. Prioritized backlog

Sequenced so the cheapest high-impact fixes land first. "Cost" is web-side
unless noted.

**P0 — integrity, mostly cheap (do first):**

1. **Fix the interventions layer end-to-end** — show all 7 with true buckets,
   restore X6/X2/X4, correct X3/X5/X7, wire the real Δ numbers, badge
   theoretical vs field-tested, quarantine what-if/tinker. *(Cost: medium;
   data already present in `CC_DATA.interventions`.)*
2. **Ship the real counterfactual trajectories** (repack change) and replace the
   spread-multiplier with a branching ghost-line. *(Cost: low; engine: none.)*
3. **Ship the real per-agent affect series** (repack change) and retire the
   coldness mock. *(Cost: low; engine: none.)*

**P1 — the two broken screens:**

4. **Rebuild the affect view** — scissors thermometer primary + party-tinted
   lumps + felt-distance tether (§3.5).
5. **Density readability** — filled heatmap, two-overlay party fields,
   small-multiples strip, centroid tether (§3.6).
6. **Merge Explore into Watch**; lead with the payoff morph; promote a chapter
   rail (§3.1).

**P2 — story & depth:**

7. **Rework chapters** to the evidence-graded set; reframe social-media + CU;
   add Gingrich, Mason-sorting, Obergefell (§3.2). *(Adding Gingrich/Obergefell
   as engine shocks = engine work + re-bless.)*
8. **Reinstate 2 characters** as a toggle layer with an authored-beats pass
   (§3.7).
9. **Resolve the individual-drift vs cohort-replacement framing** (§5.2 #6) —
   ship `replacement_events` and/or add the caveat.
10. **Rebuild the compass entity layer** (§3.9) — drive outlets from the engine's
    calibrated positions, feature the emergent factions (Tea Party/MAGA/Bernie/
    DSA) time-gated to their emergence years, retire/replace the ad-hoc static
    politicians, and label engine-derived vs illustrative anchors.

**P3 — polish & hygiene:**

11. Copy correctness pass (animus-not-love; contested framings).
12. Remove dead/legacy code (`ConceptStory`, unused `ProtoCharacter`, stale
    cc-shared intervention table) to kill the conflicting-table hazard.
13. Label illustrative elements (calibration anchor, any kept reference figures)
    as illustrative in-UI; reconcile `ENGINE_OVERVIEW` Δ numbers with phase10.

---

## 8. Where the experts disagreed / open calls for Vlad

The two reviews converged on almost everything. The only live tension is
**drama vs honesty**, and both pre-resolved it the same way: keep the famous
events and the dramatic what-if levers *on screen* but fence/reframe them
("the suspect the data won't convict"; "Sandbox — not a finding"), and spend the
real emotional budget on the honest beats (the X1 backfire, the nulls, the
Obergefell "people did change" chapter). Genuinely open decisions:

- **Chapter pattern:** auto-pause vs scroll-driven scrollytelling vs chapter-rail
  (§3.1). Recommendation leans scrollytelling; it's a build-cost call.
- **Final chapter count** (6 vs 7–8) and whether to add Gingrich/Obergefell as
  *engine* events now or as narrative-only chapters first.
- **The individual-drift framing** (§5.2 #6) — how far to go in foregrounding
  cohort replacement vs simply adding a caveat.
- **How loud the "theoretical/illustrative" fencing should be** — a UX-tone
  call.

---

## Appendix A — Engine intervention scoreboard (Phase 10 ground truth)

From `docs/results/phase10_results.md` (9 seeds × 4 release decades; Δ vs no-
intervention control). Helpful = negative Δsep / positive Δaff.

> **Step-2 re-measure update (2026-06-01).** Re-measured on the unified
> `evidence_regrade` substrate (incl. the flag-1 alignment fix), the
> representative buckets are **unchanged** — X1 backfire, X6 real, X5
> partial-on-average, the rest null. What moved: X1 magnitude is now
> **+0.28…+0.40** (was +0.32…+0.37) and **X5 is now decade-dependent**
> (null at 1990/2010, partial at 2000/2020; cross-release mean −0.058,
> still partial), so it is no longer "decade-invariant." See
> `phase10_results.md` for the current per-release table.

| ID | Name | Δsep (bucket) | Δaff (bucket) | One-line |
|---|---|---|---|---|
| X1 | Show the other side | **+0.32…+0.37 (backfire)** | ~0 (null) | Exposure activates threat → cascading backfire. Decade-invariant. |
| X2 | Fix the algorithm | 0.000 (null) | 0.000 (null) | Reproduces the Meta-2020 null. |
| X3 | Quit cable news | +0.003…+0.007 (null) | ~0 (null) | At 20% reach, washed out. |
| X4 | Bipartisan dialogue | ~0 (null) | +0.002…+0.006 (null, dir-ok) | Helps participants; doesn't move the macro at 20% reach. |
| X5 | Ranked-choice voting | **−0.056…−0.127 (partial)** | ~0 (null) | Cleanest "structural reform moves it" — but 4/4 knobs **[T] theoretical**; real RCV empirics null. |
| X6 | Shared neighborhoods (contact) | ~0 (null) | **+0.19…+0.27 (real)** | The empirically-grounded win; within Pettigrew-Tropp envelope. |
| X7 | Correct perception gap | 0.000 (null) | −0.002…−0.010 (null) | Mechanism works; doesn't propagate in a homophilous network. |

Headline: only **X5** (structural, theoretical) and **X6** (contact, empirical)
move the needle; **X1** backfires; **X2/X3/X4/X7** are null for distinct,
diagnosable reasons.

## Appendix B — Engine event schedule (all carry real mechanisms)

| Tick | Year | Event | Mechanism |
|---|---|---|---|
| 21 | 1987 | Fairness Doctrine repealed | media strength → 0.02 |
| 30 | 1990 | Decade boundary | identity-sorting / elite-drift / coupling step |
| 48 | 1996 | Fox News | media strength → 0.04 |
| 60 | 2000 | Decade boundary | drift/sorting/coupling step |
| 84 | 2008 | Social media ramp + Obama | affect_weight → 0.10; +0.05 warmth bump |
| 87 | 2009 | Tea Party | relabels ~7% of mainstream Reps → faction |
| 90 | 2010 | Decade + Citizens United | elite-drift rate step (asymmetric) |
| 96 | 2012 | Social media peak | media/affect ramp terminal |
| 105 | 2015 | MAGA | relabels Reps → faction |
| 108 | 2016 | Trump + status threat | `perceived_threat=0.5` for 60% of Reps (Mutz); Bernie faction |
| 114 | 2018 | Trump-bump revert + DSA | sorting revert; faction |
| 120 | 2020 | COVID / Jan 6 | affect learning-rate ×1.5 (3 ticks) |
| 123 | 2021 | Affect revert | learning-rate restored |

*(13 rows for 15 event records: ticks 108 and 114 each bundle two events —
Trump+Bernie, and revert+DSA.)*

## Appendix C — Key sources

*Events / drivers:* Kuziemko & Washington 2018 (AER, Southern realignment);
Mason 2018 *Uncivil Agreement* (identity sorting); DellaVigna & Kaplan 2007
(QJE) and Martin & Yurukoglu 2017 (AER, Fox News, strong causal); Hare & Poole
2014 (elite asymmetry); Hopkins 2018 (nationalization); Mutz 2018 (PNAS, status
threat) w/ Morgan 2018 critique; Rosenfeld 2017 & Lee–Mutz 2019 (same-sex
marriage, cohort vs conversion); Boxell-Gentzkow-Shapiro 2017/2021 (social-media
skepticism; cross-national); Abdul-Razzak/Prato/Wolton & Klumpp et al. (Citizens
United null); Mummolo & Nall 2017 (Big Sort overstated); Green-Palmquist-
Schickler 2002 & Converse 1964 (individual stability).

*Interventions:* Bail et al. 2018 (PNAS) & Combs et al. 2023 (NHB, exposure);
Guess et al. 2023 (Science) & Allcott et al. 2020/2024 (AER/PNAS, social media);
Broockman & Kalla 2024 (cable switching); Voelkel et al. 2024 (Science
megastudy) & Voelkel et al. 2023 (NHB, affect≠democracy) & Santoro & Broockman
2022 (decay); Donovan & Bowler 2023, Atkinson et al. 2023, McGhee & Shor 2017
(RCV/primaries null) vs Drutman 2020 (theoretical); Pettigrew & Tropp 2006,
Mousa 2020, Lowe 2021, Enos 2014 (contact); Ahler & Sood 2018, Lees & Cikara
2020, Druckman & Levendusky 2022 (perception gap).

*In-repo ground truth:* `docs/INTERVENTIONS_OVERVIEW.md`,
`docs/results/phase10_results.md`, `docs/ENGINE_OVERVIEW.md`,
`scripts/publish_web_data.py`, `scripts/repack_web_demo.py`,
`web_demo/cc-data.js`.
