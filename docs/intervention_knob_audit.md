# Intervention-page knob audit

*Branch `intervention-knob-audit`. Audit only — no engine/UI behavior changed.
Author: 2026-06-08.*

## Why this audit

The web demo's **Sandbox** ("Build your own America") exposes 5 interactive
dials, each mapped to a `build_engine` kwarg. Two questions per knob:

1. **Does the label describe what the engine actually does?**
2. **When you drag it, does the result match what the empirical literature
   would lead you to expect?**

The trigger was the **Open-mindedness** dial: cranking it to max still leaves
*two tight, cold camps* — the opposite of what the bounded-confidence
literature predicts for "more open-minded." This audit confirms that suspicion,
finds a second counterintuitive knob (Echo chambers), a badly saturated one
(Elite extremism), and proposes 5 additional candidate knobs — 10 audited in
total.

All numbers below are **measured**, not asserted: the existing-knob figures come
from the pre-rendered grid (`web_demo/cf/sandbox/`, seed 0, final tick 135, each
knob swept with the other four held at the shipped center `21211`); the
epsilon/party-pull figures come from live engine runs (`ANES_FULL_KWARGS`, seed
0, tick 135).

---

## Verdict at a glance

| # | Knob (label) | kwarg | What it *actually* does | Label? | Drag behavior vs literature | Verdict |
|---|---|---|---|---|---|---|
| 1 | **Open-mindedness** | `tier_c_bc_strength` | BC *averaging strength* (speed of pull toward already-close in-party neighbours) — **not** the confidence radius ε | ❌ wrong concept | Near-inert; at max still 2 cold camps. HK literature says open-mindedness → consensus | **BROKEN** |
| 2 | **Elite extremism** | `tier_d_anes_drift_multiplier` | Scales per-decade party-centroid drift rate | ✅ | Correct direction but **saturates by 1.5×**; top ¾ of slider is dead | **OK, rescale** |
| 3 | **Partisan animus** | `sandbox_animus_mult` | Scales affect learning-rate (contact + parasocial cooling) | ✅ | Clean, monotonic, orthogonal — the "Cold Peace" lever | **GOOD** |
| 4 | **Mega-identity** | `sandbox_identity_mult` | Scales identity-sorting rate/step + alignment relaxation | ✅ | Strong, monotonic; faithful "diagonal collapse" (Mason) | **GOOD** (super-lever) |
| 5 | **Echo chambers** | `sandbox_rewire_mult` | Scales homophilous tie-rewiring rate | ⚠️ partial | Modularity ↑ correct, but **animus goes the WRONG way** (more echo → *warmer*) | **COUNTERINTUITIVE** |
| 6 | Confidence radius (ε) | *new* `tier_c_bc_epsilon` | The **real** open-mindedness: how far across the divide you'll listen | — | Proven to merge camps + warm + de-segregate (with strength) | **ADD (fixes #1)** |
| 7 | Elite-cue following | `tier_c_party_pull_strength` *(exists)* | How hard the mass follows party elites | — | Clean monotonic sep lever 0.96→1.38 | **ADD (cheapest)** |
| 8 | Partisan media power | *new* `sandbox_media_mult` | Pull toward partisan-outlet centroids | — | Centrifugal (Levendusky 2013). **Already falsely advertised in Methods copy** | **ADD** |
| 9 | Cross-cutting exposure / backfire | *new* `sandbox_backlash_mult` | Affect-gated repulsion from cold out-party contact | — | Bail 2018 backfire — pedagogically rich | **CONSIDER** |
| 10 | Status threat | *new* `sandbox_threat_mult` | Mutz 2018 amplifier on out-party animus | — | The 2016 animus accelerant | **CONSIDER** |

Legend: ✅ accurate · ⚠️ partly · ❌ wrong.

---

## Part A — the 5 existing knobs

### 1. Open-mindedness → `tier_c_bc_strength`  ❌ BROKEN (the headline)

**What the user is told.** Stops `closed · low · mid · high · max`; the dial
"owns" *"how much people hear the other side"* (`rc-interventions.jsx:167-173`).
The "Depolarized" preset (`[0,0,0,0,4]`) promises *"one warm cloud."*

**What it actually drives.** `BoundedConfidenceInfluence.strength`
(`influence.py:132`: `d = strength · (target − my_ide)`). This is the *fraction
of the way* an agent moves toward the mean of neighbours **already inside its
confidence radius ε**. ε itself is fixed at **0.30** (`historical_arc.py:1394`,
per-agent jitter around 0.30 at `:496`) and the dial never touches it.

In Hegselmann–Krause terms the literature calls **ε** ("confidence radius")
open-mindedness — *how far apart two people can be and still influence each
other.* Large ε → one consensus cluster; small ε → fragmented clusters. The
`strength` parameter is the *convergence speed* (susceptibility / conformity
pull), and it does **not** set how many clusters form. So the dial is bolted to
the wrong parameter.

**Measured (others at shipped center):**

| value | sep | out-party warmth | modularity |
|---|---|---|---|
| 0.0 (off) | 1.134 | −0.694 | 0.201 |
| 0.015 (shipped) | 1.122 | −0.689 | 0.202 |
| 0.05 | 1.115 | −0.682 | 0.206 |
| 0.10 | 1.092 | −0.672 | 0.202 |
| 0.20 (MAX) | 1.067 | −0.674 | **0.230** |

Across the whole slider, separation moves only −6% and stays at ~1.07 (two
camps ~1.1 apart), warmth stays frigid (~−0.68), and **modularity actually
rises**. Max "open-mindedness" produces a *more* segregated, equally cold,
still-bifurcated society. That is exactly the counterintuitive result observed,
and it directly contradicts the slider's own "Depolarized → one warm cloud"
promise.

**Why** (root cause). With ε = 0.30 fixed but the inter-camp gap at ~1.1, the
two parties sit *far outside each other's confidence radius*, so the cross-party
averaging term essentially never fires. Raising `strength` only speeds up
*within-camp* convergence (slightly tighter, slightly more modular clusters).
The knob can't depolarize because the parameter that would let people "hear the
other side" (ε) is held constant.

**The fix is proven** — see Part B.

---

### 2. Elite extremism → `tier_d_anes_drift_multiplier`  ⚠️ OK but saturated

Drives the per-decade elite-drift schedule (`historical_arc.py:782-785`,
`ELITE_DRIFT_SCHEDULE_ANES × multiplier`), pushing party centroids apart.
Mechanism + label are sound (McCarty/Poole/Rosenthal DW-NOMINATE divergence,
`literature.md`; provenance **L** on magnitude, **L-direction/E-magnitude** on
the asymmetry schedule).

**Measured:**

| value | sep | warmth | modularity |
|---|---|---|---|
| 0.0 | 0.602 | −0.684 | 0.134 |
| 1.5 | 1.072 | −0.689 | 0.182 |
| 3.0 (shipped) | 1.122 | −0.689 | 0.202 |
| 5.0 | 1.155 | −0.679 | 0.218 |
| 8.0 | 1.159 | −0.680 | 0.229 |

Direction correct, but the curve is **saturated**: 0→1.5× delivers almost the
entire effect (0.602→1.072); 1.5×→8.0× barely moves it (→1.159). The top
**three of five** detents are visually dead. For a sandbox whose pitch is
"dialed past anything real," that's a poor experience.

**Recommend:** rescale the stops to a band where each detent visibly bites
(e.g. `0 · 0.5 · 1 · 2 · 3×`), or fold elite drift together with elite-cue
following (#7) so "elites pull apart" also strengthens how hard the mass
follows. Minor: the Methods page calls this **"elite extremity"**
(`cc-pages.jsx:120`) while the dial says **"Elite extremism"** — unify.

---

### 3. Partisan animus → `sandbox_animus_mult`  ✅ GOOD

Scales the per-agent affect learning rate (`historical_arc.py:1022`) **and**
`MediatedAnimus.learning_rate` (`:1452`) — both out-party-cooling channels.

**Measured:**

| value | warmth | sep | modularity |
|---|---|---|---|
| 0.5 | −0.504 | 1.123 | 0.200 |
| 1.0 (shipped) | −0.689 | 1.122 | 0.202 |
| 2.0 | −0.891 | 1.124 | 0.202 |
| 4.0 | −0.987 | 1.123 | 0.208 |
| 8.0 | −0.998 | 1.093 | 0.192 |

Monotonic on its dedicated axis (warmth), and cleanly **orthogonal** to issue
separation — this is precisely the "Cold Peace" idea (affective polarization
*without* issue sorting; Iyengar et al. 2019, Mason 2018). Saturation near the
−1.0 floor at the top is just the affect bound. Keep. (Optional copy nuance:
it's the *speed of cooling*, not a static animus level.)

---

### 4. Mega-identity → `sandbox_identity_mult`  ✅ GOOD (a super-lever)

Scales `IdentitySorting.sort_rate` + `.step`, the env
`identity_sorting_multiplier`, and `IdentityAlignment.rate`
(`historical_arc.py:1460-1473`).

**Measured:**

| value | align | sep | warmth |
|---|---|---|---|
| 0.0 | 0.215 | 0.968 | −0.549 |
| 0.5 | 0.244 | 0.988 | −0.554 |
| 1.0 (shipped) | 0.406 | 1.122 | −0.689 |
| 2.0 | 0.938 | 1.459 | −0.898 |
| 3.0 | 0.990 | 1.542 | −0.940 |

Strong and monotonic on alignment (0.22→0.99) and faithfully **spills into both
issue separation and affect** — Mason's mega-identity "diagonal collapse,"
where identity stacking does work the issue axis alone doesn't. Good and
literature-true. Honest caveat for the copy: this dial moves *three* outcome
readouts at once, so it isn't an isolated lever — that's faithful to Mason, but
users comparing dials should know it's the broadest one.

---

### 5. Echo chambers → `sandbox_rewire_mult`  ⚠️ COUNTERINTUITIVE

Scales `TieRewiring.rewire_rate` (`historical_arc.py:1552`): faster homophilous
rewiring → higher network modularity.

**Measured:**

| value | modularity | out-party warmth | sep |
|---|---|---|---|
| 0.0 | 0.047 | −0.778 | 1.087 |
| 1.0 (shipped) | 0.202 | −0.689 | 1.122 |
| 3.0 | 0.291 | −0.548 | 1.099 |
| 6.0 | 0.296 | −0.516 | 1.106 |
| 10.0 | **0.369** | **−0.426** | 1.072 |

Modularity responds correctly (0.05→0.37). **But out-party warmth moves the
wrong way: more echo chambers → *warmer* toward the other side** (−0.778 →
−0.426). A user dragging "Echo chambers" to max, watching the "Out-party
animus" readout *fall*, will reasonably conclude the model is broken.

**Why** (and it's mechanically real). Out-party cooling here is *contact-gated*
(`AffectiveUpdate` fires on out-party encounters). More homophilous rewiring
*starves* out-party contact, so there's less cooling — warmth drifts back up.
The contact-*independent* parasocial channel (`MediatedAnimus`) is driven by
`identity_alignment`, **not** by network modularity, so cranking echo chambers
never engages it. The engine docs already acknowledge this tension
(`ENGINE_KNOBS.md` §3.4b: "homophilous sorting starves out-party contact").

**Note:** the *causal* echo-chamber → animus link is genuinely contested in the
literature (Boxell/Gentzkow/Shapiro; Bail 2018), so "echo chambers make you
colder" is not a settled empirical fact. The problem is purely that the
**sandbox tells a story its own numbers contradict.** Two honest fixes:

- **(a) Make the sign match the mental model:** add a small parasocial-animus
  term that scales with isolation/modularity (or cross-party-tie scarcity), so
  net warmth falls as echo chambers rise.
- **(b) Teach the counterintuitive truth:** keep the mechanics, but change the
  copy to surface "walling yourself off removes the contact that would have
  cooled you — affect is driven by identity + media here, not by isolation,"
  and stop implying echo → animus on the readout.

(b) is the more honest, lower-risk move and fits the project's "measure-then-
bless" discipline.

---

## Part B — the fix for Open-mindedness (proven)

I re-pointed open-mindedness at the conceptually-correct parameter (ε, the
confidence radius) and measured live runs.

**ε alone, strength held at shipped 0.015:** still near-inert (sep 1.13→1.10).
**strength alone, ε held at 0.30:** near-inert (Part A, table 1).
**Both opened together:**

| ε | strength | sep | warmth | modularity |
|---|---|---|---|---|
| 0.30 | 0.015 (shipped) | 1.124 | −0.688 | 0.202 |
| 0.30 | 0.20 | 1.082 | −0.679 | 0.225 |
| 1.00 | 0.08 | 0.936 | −0.650 | 0.190 |
| 1.00 | 0.20 | 0.757 | −0.636 | 0.189 |
| 3.00 | 0.20 | **0.729** | **−0.633** | **0.189** |

Open the radius *and* give it enough influence and the camps finally converge:
sep 1.124 → 0.729 (−35%), warmth warms, modularity falls — the
literature-consistent "people hear the other side → one warmer, less-segregated
cloud" behavior the slider has always promised.

**Root cause restated:** "open-mindedness" is a *two-parameter* phenomenon here
(how widely you'll listen × how much you let it move you). The current knob
turns only the second; with ε pinned narrower than the inter-camp gap, no
amount of the second matters.

**Recommended implementation.** Make the dial drive **ε**, co-scaling strength
so it actually bites — e.g. a single "openness" parameter `o ∈ [0,1]` mapped to
`ε = 0.2 + 2.8·o` and `strength = 0.015 + 0.185·o`, low end = closed
(narrow + inert), high end = open (wide + strong). Add a kwarg
(`tier_c_bc_epsilon`, mirroring the existing `tier_c_bc_strength`) so
`build_sandbox_data.py` can sweep it. **Re-validate the "Depolarized" preset**
afterward — it currently fails to deliver "one warm cloud."

---

## Part C — 5 candidate new knobs

### 6. Confidence radius / "open-mindedness done right" (ε)
- **Mechanism:** `BoundedConfidenceInfluence.epsilon` — how far across the
  divide an agent will still be influenced. **L** (Hegselmann–Krause 2002).
- **Wiring:** needs a new kwarg `tier_c_bc_epsilon` (today ε is hard-set 0.30).
- **Behavior:** proven in Part B. This is the **fix for #1**, not really an
  "extra" knob — either replace #1 with it or merge the two into one honest
  openness dial. **Priority: P0.**

### 7. Elite-cue following / party pull (`tier_c_party_pull_strength`)
- **Mechanism:** `PartyPull.strength` — how hard the mass follows party elites
  (distinct from #2: elite *drift* moves the targets apart; *pull* sets how
  hard agents chase them). Hetherington 2001, Levendusky 2009 (**L**).
- **Wiring:** **kwarg already exists** — cheapest possible addition.
- **Measured (live):**

  | strength | sep | warmth | modularity |
  |---|---|---|---|
  | 0.0 | 0.962 | −0.682 | 0.178 |
  | 0.02 | 1.062 | −0.684 | 0.196 |
  | 0.04 (shipped) | 1.122 | −0.689 | 0.202 |
  | 0.08 | 1.242 | −0.684 | 0.218 |
  | 0.15 | 1.377 | −0.684 | 0.248 |

  Clean, monotonic separation lever; warmth flat. **Priority: P1.**

### 8. Partisan media power (`sandbox_media_mult` → `MediaConsumption.strength`)
- **Mechanism:** pull toward the agent's partisan-outlet centroid; heavy
  partisan-media diets drift viewers outward (Levendusky 2013; Martin &
  Yurukoglu 2017) (**L**).
- **Wiring:** needs a new multiplier kwarg (no override today).
- **Note:** the Methods page **already advertises "media power" as a real engine
  knob** (`cc-pages.jsx:120`) — but no such dial exists. Adding it also resolves
  that false-advertisement. **Priority: P2.**

### 9. Cross-cutting exposure / backfire (`sandbox_backlash_mult` → `BacklashRepulsion`)
- **Mechanism:** affect-gated repulsion from cold out-party contact — Bail 2018
  (forcing people to see the other side can *increase* separation) (**L**
  concept / **E** form). This is the engine mechanism behind intervention X1.
- **Wiring:** needs a multiplier kwarg.
- **Why interesting:** it's the one knob that makes "exposure" *backfire* — a
  high-value teaching counterpoint to the (fixed) open-mindedness dial.
  **Priority: P2.**

### 10. Status threat (`sandbox_threat_mult` → `AffectiveUpdate.threat_amplification`)
- **Mechanism:** Mutz 2018 status-threat amplifier on out-party animus; the
  modeled 2016 accelerant (**L** direction / **E** magnitude).
- **Wiring:** needs a multiplier kwarg.
- **Why interesting:** lets users see the affect spike that threat produces,
  distinct from steady-state cooling (#3). **Priority: P2/P3.**

**Alternative depolarizing lever (worth considering instead of #10):**
**Contact / shared neighbourhoods** (X6, Pettigrew–Tropp 2006) would give a
*second* genuinely depolarizing dial besides open-mindedness — pedagogically
valuable, since the sandbox currently has only one lever that points toward
peace (and it's the broken one).

---

## Part E — empirical search for a robust set of 5 (the answer)

Part C listed *plausible* knobs. The real test (per the project goal) is harder:
**five levers that each move their outcome in the intuitive direction no matter
where the other four sit.** I ran the live engine (not the cached web grid),
sweeping each candidate low→high across **randomized positions of all the other
candidates**, and counted sign-flips. Two screens: a wide 7-knob screen, then a
definitive screen on the finalists with backgrounds drawn *only from each
other*. (seed 0, tick 135, scripts in `/tmp`, not committed.)

### What survived, what didn't

| Candidate | Lay framing | Own-target robustness | Verdict |
|---|---|---|---|
| **Mega-identity** | "how much race/religion/lifestyle line up with party" | align ↑ **12/12** | **KEEP** |
| **Elite extremism** | "how far apart the parties pull" | sep ↑ **12/12** | **KEEP** (rescale stops) |
| **Partisan animus** | "how fast they learn to hate each other" | warmth ↓ **12/12** | **KEEP** |
| **Echo chambers** | "how walled-off the social networks are" | modularity ↑ **12/12** | **KEEP** (segregation only — see caveat) |
| **Open-mindedness** *(ε+strength)* | "how much people hear the other side" | sep ↓ **12/12**, warmth ↑ 10/12 | **KEEP (rewired)** — fixes Part A/B |
| "Set in their ways" (stubbornness) | "how stuck / unpersuadable people are" | sep ↓ **11/12** | **strong bench** (novel; robust) |
| Party loyalty / follow-the-leader (party pull) | "how hard people fall in line" | sep ↑ **9/12** | **REJECT** — sign-flips |
| Partisan media power (`MediaConsumption`) | "how strong partisan media is" | sep ↑ **3/12** | **REJECT** — inert (rule off in arc) |

### Why the two "obvious" ones fail
- **Party pull flips sign when elite drift is low.** With elites not diverged,
  the party centroids sit nearly on top of each other, so "follow your party
  harder" pulls *everyone toward a shared center* → separation **drops**
  (observed −0.31 in one background). Its sign is contingent on another knob —
  the exact non-robustness to avoid.
- **Media is inert.** `MediaConsumption.strength = 0.0` in the shipped arc;
  switching it on up to 0.08 moved separation in only 3/12 backgrounds and
  never meaningfully. Media power would need the outlet/diet machinery
  re-engaged before it could be a lever — it's not a cheap add.

### The honest conclusion
**The five *axes* the sandbox already chose were right** (separation, animus,
network segregation, identity, openness). The failures weren't the axis choice —
they were **wiring**: open-mindedness on the wrong parameter, and echo's affect
coupling pointing the wrong way. The tempting *alternative* levers (party pull,
media) are actually **less** robust than what's there. So the recommended set is
the same five, **with two repairs**:

1. **Open-mindedness → drive ε (co-scaled with strength).** Proven 12/12 sep↓.
2. **Echo chambers → present as segregation only.** It owns modularity cleanly
   (12/12) but *reliably warms* the out-party (0/12 the other way, median
   +0.19), because homophily starves the contact that does the cooling. Either
   (a) re-label/teach it as "how walled-off the networks are" and keep the
   animus readout off this dial, or (b) wire a parasocial-animus term to
   isolation so the sign matches the public mental model. Do **not** ship it
   coupled to an "animus" readout as-is.

### Second exploration round (after dropping echo)

Echo was dropped (its modularity dial reliably *warms* the out-party — see Part
A.5). To replace the lost axis and add outcome diversity, three more intuitive
candidates were screened across randomized backgrounds of
`{openness, elite, animus, identity, stubborn}`:

| Candidate | Lay framing | Robustness | Verdict |
|---|---|---|---|
| **Within-party diversity** (`GaussianNoise.sigma`) | "free-thinking individuals vs lockstep partisans" | within-party spread ↑ **12/12** | **KEEP** — owns a brand-new *visible* axis (camp tightness/fuzz); also mildly lowers sep |
| **Contact / mixing** (`cooperative_share` + cross-party cooperative ties) | "how much the two sides mix (neighbourhoods, workplaces, friends)" | warmth ↑ **10/12** (2 floored, **0 backfire**) | **KEEP** — a second depolarizer on the *affect* channel (warms even with issues still split; Pettigrew–Tropp) |
| Status threat (`perceived_threat`) | "how under-siege people feel" | warmth ↓ 9/12, **median only +0.02** | **REJECT** — too weak (agents already maxed-cold late; redundant with animus) |
| "Set in their ways" (stubbornness) | "how stuck / unpersuadable people are" | sep ↓ **11/12** | bench (robust but a 2nd sep-reducer, abstract) |

### The robust lever pool (all sign-stable across the others)

| Lever | Owns (visible outcome) | Direction | Robustness |
|---|---|---|---|
| Mega-identity | identity diagonal-collapse | polarizing | 12/12 |
| Elite extremism | camps move apart (sep) | polarizing | 12/12 |
| Partisan animus | camps get colder (warmth) | polarizing | 12/12 |
| Open-mindedness *(ε+strength)* | camps merge + warm | **de**polarizing | 12/12 |
| Contact / mixing | camps warm (issues stay) | **de**polarizing | 10/12 (no backfire) |
| Within-party diversity | camp tightness / fuzz | mixed | 12/12 |
| Stubbornness | global freeze (sep ↓) | **de**polarizing | 11/12 |

Rejected: **echo** (counterintuitive warmth), **party pull** (sign-flips on
elite drift), **media** (inert), **status threat** (too weak), **backfire**
(a consequence, not a lever).

### The design principle: knobs = causes, readouts = outcomes

The two knobs that failed the audit's *intuition* test — **Partisan animus** and
**Echo chambers** — share a root cause: **they are outcome metrics dressed up as
knobs.** The sandbox even shows "Out-party animus" and "Echo chambers
(modularity)" as *readouts* at the bottom of the panel, so dialing them directly
double-counts and invites the counterintuitive behaviors found above (echo's
warmth sign; animus being a thing you set rather than cause). The clean rule:
**a knob should be a cause a person would plausibly *set*; the polarization
metrics are outcomes you *watch*.**

### Recommended final five (all causes)

Applying that rule — animus and echo demoted to **readouts**, their slots given
to genuine causes:

1. **Mega-identity** — race/religion/lifestyle stack onto party *(cause)*.
2. **Elite extremism** — the parties' leaders pull apart *(cause)*.
3. **Open-mindedness** *(ε+strength)* — willingness to hear the other side *(trait/cause)*.
4. **Contact / mixing** — how much the two sides mix in daily life *(cause)*.
5. **Within-party diversity** — free-thinking individuals vs lockstep partisans *(trait/cause)*.

**Readouts** (watched, not set): party separation, **out-party animus**,
identity alignment, network modularity, within-party spread.

**Mutual robustness (definitive screen, backgrounds drawn only from the other
four):** every knob is correct-signed in **12/12** with **zero sign-flips**:

| Knob | Target readout | correct | flips |
|---|---|---|---|
| Mega-identity | alignment ↑ | 12/12 | 0 |
| Elite extremism | separation ↑ | 12/12 | 0 |
| Open-mindedness | separation ↓ | 12/12 | 0 |
| Contact / mixing | warmth ↑ | 12/12 | 0 |
| Within-party diversity | spread ↑ | 12/12 | 0 |

And the demoted readouts stay rich and controllable through the causes alone:
across the screen, warmth spans **[−0.97, −0.39]** and separation **[0.29,
1.58]**. Demoting animus to a readout costs nothing.

*(Bench, if a swap is ever wanted: **stubbornness** — robust 11/12 — for a "how
stuck are people" flavor; overlaps open-mindedness on the sep axis.)*

---

## Part D — recommendations, in priority order

1. **P0 — Fix open-mindedness.** Re-point the dial at ε (co-scaled with
   strength per Part B), add `tier_c_bc_epsilon`, re-render the grid, and
   re-validate the **"Depolarized"** preset (it does not currently deliver "one
   warm cloud").
2. **P0/P1 — Resolve the Echo-chambers sign.** Either tie a parasocial-animus
   term to isolation (so net warmth falls), or — preferably — rewrite the copy
   to teach the real "homophily starves contact" mechanism and stop implying
   echo → animus.
3. **P1 — Rescale Elite-extremism stops** to a band where each detent bites
   (the top ¾ is currently dead); unify the "extremism / extremity" naming.
4. **P1 — Add Elite-cue following** (`tier_c_party_pull_strength`) — the kwarg
   already exists; near-zero cost, clean behavior.
5. **P2 — Add Partisan media power** (also fixes the Methods-page false claim),
   then **Backfire** and/or **Status threat** / **Contact** as the model's
   appetite allows.
6. **Keep** Partisan animus (#3) and Mega-identity (#4) as-is; add a one-line
   note that Mega-identity is a broad, multi-axis lever.

### Architectural reality check (read before "expanding to 10 live dials")
The sandbox is a **pre-rendered full-factorial grid**: 5 knobs × 5 stops =
3,125 files. It does **not** scale — 6 knobs = 15,625, 10 knobs ≈ 9.7M files.
"Audit 10 knobs" (this document) is cheap; *shipping* 10 live dials is not.
Practical options if more than ~5 live dials are wanted:
- swap in the **right** 5 (fix #1/#5, add #6/#7) and keep the rest as **fixed
  presets** rather than free dials;
- reduce stops per knob (3 stops × 6 knobs = 729);
- one-knob-at-a-time sweeps around the center (loses interaction effects —
  note the ε×strength interaction in Part B is exactly the kind of effect that
  would be lost);
- or move to an in-browser engine (large undertaking).

---

## Appendix — provenance & honesty notes
- The sandbox is explicitly flagged **"not a finding"** and cranks mechanisms
  past calibration; nothing here changes that. But "illustrative" still
  requires **directionally honest** — a dial whose label and readout point
  opposite ways (Open-mindedness, Echo chambers) fails that bar even for an
  illustrative tool.
- All existing-knob figures: `web_demo/cf/sandbox/sandbox_<key>.json`, center
  `21211`. ε and party-pull figures: live `build_engine` runs, seed 0,
  `ANES_FULL_KWARGS`, tick 135 (scripts left in `/tmp`, not committed).
- Engine refs cited inline as `file:line`. No files outside this document were
  modified.
