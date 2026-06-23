# How US Polarization Actually Works — A Causal Model for the Engine

*The "step 0" truth-model: what the empirical literature says actually drives US
political polarization (1970s→2025), assembled into one causal chain, decomposed
by mechanism and by within-person vs cohort vs compositional change — then mapped
to the current `polarlab` engine so we can decide what the engine's primary
mechanics should be. Written 2026-05-31, branch `web-redesign-ideas`.*

*Method: three independent cited literature passes (cohort-vs-within-person
decomposition; the top-down elite→mass chain; affective-polarization mechanisms
& consequences), reconciled here, then cross-read against the engine's actual
rule inventory (`abm/rules/`, `abm/pillars/historical_arc.py`). Evidence grades
are **STRONG / MIXED / CONTESTED / WEAK**. Companion to
[`web_demo_audit.md`](web_demo_audit.md) (the front-end audit) — this document is
about the **model**, not the website.*

> **The one-sentence answer to the question that started this.** "US
> polarization is mostly cohort replacement" is **false for the part of the
> story this project is about.** Replacement matters for *slow issue-attitude
> liberalization*; but **ideological sorting and affective polarization — the
> spine of the demo — are within-person / period phenomena driven by an
> elite/media environment, not by generational turnover.** So the engine's
> primary mechanic should be **within-person attitude/affect updating under a
> time-varying elite/media period signal**, with party ID near-frozen after
> early adulthood and replacement kept as a *secondary* channel — which is
> **exactly what the engine was already built on.** No rebuild; the changes
> below are targeted refinements.
>
> *Provenance note: the "mostly cohort replacement" claim this document
> investigates originated as an erroneous assertion in an earlier draft of
> [`web_demo_audit.md`](web_demo_audit.md) — it was never a property of the
> engine, which has always been within-person. This pass confirms the engine's
> existing design and retires the bad claim.*

---

## 1. The headline correction: is polarization "mostly cohort replacement"?

The honest answer is **outcome-specific** — it flips depending on which
polarization you mean. Lumping them together is the mistake.

| Outcome | Cohort replacement | Within-person / period | Compositional | Confidence | Anchor |
|---|---|---|---|---|---|
| **Party-ID stability** | — | Individual party ID is *extremely stable* (disattenuated continuity **r ≈ .97**); aggregate change is conversion-resistant | minor | **STRONG** | Green-Palmquist-Schickler |
| **Southern/racial realignment** | A channel, **growing over time** | **Dominant in 1958–1980**: living racially-conservative whites *converted* (race explains ~the entire 17pp Southern Dem decline; income ≈ 0) | minor | **STRONG** (K&W); MIXED on the replacement share | Kuziemko-Washington; Carmines-Stimson; Stoker |
| **Issue-attitude liberalization** (same-sex marriage, marijuana, immigration, racial, gender) | **Real, issue-specific**: ~⅓ for SSM, *minor* for marijuana/immigration, *larger* (~half) for gender roles | **Majority for most** (within-person/period) | education + secularization feed cohort gaps | **MIXED-HIGH** | Rosenfeld; Baunach; Firebaugh-style decompositions |
| **Ideological sorting** (aligning issues/ideology with party) | small | **Dominant: within-person, elite-cue-driven** — people hold party fixed and move their *positions* to match | minor | **MIXED-HIGH** | Levendusky *The Partisan Sort* |
| **Affective polarization** ⭐ | **≈ zero** | **DOMINANT — a true PERIOD effect + mild lifecycle aging.** Out-party warmth fell across *all* cohorts at once, *fastest among the oldest/least-online* | negligible | **STRONG** (3 independent APC studies converge) | Phillips 2022; Stoker 2020; Boxell-Gentzkow-Shapiro |

**Verdict.** "Mostly generational replacement" is true-ish **only** for slow
secular issue-attitude liberalization, and was *a* (growing) channel in the
historical Southern realignment. It is **flatly wrong for affective polarization
and for much of ideological sorting** — the two phenomena that make modern
polarization feel dangerous and that the demo is built around. Affective
polarization is, by the strongest available evidence, an almost pure **period
effect** (everyone got colder toward the out-party at once), which is why it rose
*fastest among the oldest and least-online* — a fact that simultaneously refutes
the "it's the young / it's social media / it's replacement" stories.

> **Implication for the engine, stated plainly.** Do **not** make cohort
> replacement the primary mechanic. The primary mechanic that produces the
> headline phenomena is **within-person updating in response to a period-level
> elite/media signal**, with party ID nearly frozen after formative years.
> Replacement belongs as a *slow secondary channel* that mainly moves long-run
> issue attitudes — not affect.

---

## 2. The whole causal chain (the truth-model)

The system is **top-down in origin, feedback-sustained in operation.** The spark
is structural/elite; the fire is a closed loop among elites, activists/donors,
and media. Read top to bottom; each link carries an evidence grade and a
direction. ⚠ marks a genuinely contested link.

```
[L0] DISTAL STRUCTURAL CAUSE — Racial/Southern realignment (1958–1980)
     Elite civil-rights position-taking aligns RACE × REGION × PARTY.
     Direction: ELITE→MASS (top-down).  Evidence: STRONG (Kuziemko-Washington).
     ⚠ economic-development rival view (Shafer-Johnston); race-primacy better identified.
        │
        ▼
[L1] ELITE POLARIZATION (Congress diverges ~1977→present; Gingrich 1994 inflection)
     ASYMMETRIC: the GOP moved right more than Democrats moved left.
     Direction: endogenous to coalition turnover + activist/donor capture (see loop F1).
     Evidence: STRONG on trend & direction (DW-NOMINATE).  ⚠ magnitude of the
     asymmetry partly a measurement artifact of how the scale handles Southern realignment.
        │
        ▼
[L2] PARTY-POSITION CLARITY / NATIONALIZATION (Hopkins; local-news decline)
     Clear, legible national party brands; cross-pressures stripped out → higher
     signal-to-noise on the elite cue.  Evidence: STRONG (trend); MIXED (independent
     cause vs transmission channel).
        │
        ▼
[L3] MASS IDEOLOGICAL SORTING (Levendusky; Zaller "receive-accept-sample"; Hetherington)
     Voters keep party fixed and bring ISSUE positions into line by cue-taking.
     NOT mass radicalization — re-correlation.  Direction: ELITE→MASS (top-down).
     Evidence: STRONG for direction; MIXED for magnitude — coupling is HETEROGENEOUS
     (strong for the politically engaged, weak for the inattentive).
     ⚠ Fiorina: "sorting ≠ a deeply polarized public."
        │
        ▼
[L4] IDENTITY STACKING / "MEGA-IDENTITY" (Mason)
     Partisan + ideological + racial + religious + geographic identities align;
     cross-cutting ties that used to moderate animosity disappear.
     Evidence: STRONG correlational + experimental; clean exogenous causation NOT
     established (the sorting↔affect link is RECIPROCAL, ~0.37 SD per SD — weak).
        │
        ▼
[L5] AFFECTIVE POLARIZATION — rising OUT-party animus (Iyengar; Mason)
     ANES in-minus-out thermometer gap rose 22.6° (1978) → 40.9° (2016), driven by
     FALLING OUT-PARTY WARMTH with IN-PARTY warmth ~flat (not perfectly monotonic —
     it dipped 2012–16).  A true PERIOD/within-person effect (not cohort).
     Amplified in parallel by:
        • PARTISAN MEDIA — cable/Fox (causal-ish, Martin-Yurukoglu); talk radio.
          ⚠ social media as a cause of AFFECT is WEAK/near-null (BGS by-age; Meta-2020
            deactivation ~zero). Selective exposure → media is an AMPLIFIER on
            already-sorted agents, not an exogenous origin.
        • STATUS/THREAT shocks — Mutz 2016. ⚠ CONTESTED (Morgan: economics matters too).
        • MISPERCEPTION / meta-perception — Ahler-Sood "parties in our heads";
          partly causal, partly downstream; a loop-embedded mediator.
        │
        ▼
[L6] BEHAVIORAL & ANTI-DEMOCRATIC CONSEQUENCES
     Affect → social distance, discrimination (Iyengar-Westwood: partisan
     discrimination exceeds racial), straight-ticket / negative-partisan voting,
     higher turnout.  Evidence: STRONG.
     ⚠ CRITICAL DECOUPLING: reducing affect does NOT reliably reduce ANTI-DEMOCRATIC
     attitudes (Voelkel 2023). Treat affect and anti-democratic attitudes as
     SEPARATE state variables.

  ┌──────────────────────── FEEDBACK LOOPS (the "fire") ────────────────────────┐
  │ F1  activist/donor ↔ elite (primary capture): intense policy demanders      │
  │     control nominations → elites move to the pole to survive primaries →     │
  │     "electoral blind spot" weakens general-election punishment → ratchet     │
  │     outward, asymmetrically stronger on the right. (Bawn et al.; Tea Party.) │
  │ F2  elite → media → mass → activist: clear extreme cues → media amplifies →  │
  │     masses sort & cool → the most affectively polarized become the donor/    │
  │     primary/activist base that re-energizes F1.                              │
  │ F3  nationalization: local-news decline → national brands → straight-ticket  │
  │     voting → fewer cross-pressured moderates survive → elites polarize more. │
  └──────────────────────────────────────────────────────────────────────────────┘

  CROSS-CUTTING CHANNELS (not in the main spine):
   • COHORT REPLACEMENT — slow; moves SECULAR ISSUE ATTITUDES (SSM, marijuana,
     racial, gender), NOT affect. Formative-years imprinting (~ages 14–24) sets a
     near-frozen partisan baseline (Ghitza-Gelman-Auerbach).
   • COMPOSITIONAL — immigration, rising education, secularization; modest, slow.
```

### 2.1 What this changes about the demo's current event framing

The chain re-grades several events the demo currently leans on (detail in the
audit §3.2). In causal terms:

- **Elite drift belongs at L1 (Gingrich/1994, asymmetric)** — *not* at Citizens
  United (2010), whose causal effect on polarization is **null/contested**.
- **Partisan cable (Fox, 1996) is a real L5 amplifier** — keep it.
- **Social media (2008–2012) is a WEAK amplifier of affect** — the engine
  currently encodes it as a real affect shock; that's stronger than the evidence
  supports (flag).
- **Identity sorting (Mason, L3→L4) is the master mechanism the demo never names**
  — it should be the connective tissue between the issue map and the animus
  story, not an unlabeled background process.

---

## 3. Confidence map — what's settled vs contested

**Well-established (build on these):**

- Affective polarization is the headline modern trend, driven by **falling
  out-party warmth** (in-party ~flat), and is a **period/within-person** effect,
  not cohort. *(STRONG)*
- Individual party ID is **highly stable** (~.97); aggregate partisan change runs
  through replacement + the slow conversion of the minority who move. *(STRONG)*
- Sorting is **party-driven and top-down** (positions move to match party,
  following elite cues). *(STRONG on direction)*
- Elite polarization **led** mass polarization and is **GOP-asymmetric**.
  *(STRONG on direction)*
- The contact remedy works on affect; most other interventions are small/null
  (see audit §3.4). *(STRONG)*

**Genuinely contested (model as uncertain / tunable, don't assert):**

- The **magnitude** of elite asymmetry (partly a DW-NOMINATE artifact). ⚠
- **Sorting → affect** causal strength (reciprocal, weak coefficient). ⚠
- **Status threat** vs economic interest (Mutz vs Morgan). ⚠
- **Media: cause vs demand** (selective exposure). Model as amplifier on
  already-sorted agents. ⚠
- **"Sorting = a polarized public?"** (Fiorina): model masses as *sorting*, not
  *radicalizing*. ⚠

**Weak / largely refuted (do not feature as causal):**

- **Social media as a primary cause of affect** (BGS by-age; Meta-2020 null). ✗
- **Citizens United as a polarization driver** (best-identified studies: null). ✗
- **"It's all generational replacement"** — false for affect and sorting. ✗

---

## 4. Engine-design implications

### 4.1 The core principle

> **Primary mechanic = within-person attitude/affect updating under a
> time-varying elite/media PERIOD signal.** Party ID is **near-frozen** after
> formative years; **sorting** = agents move their *issue positions* to match a
> fixed party in response to clarified elite cues; **affect** emerges from
> identity alignment + the contemporaneous hostile-cue environment, applied
> population-wide as a period forcing with a mild aging gradient. **Cohort
> replacement is a slow secondary channel** for issue attitudes, not the engine
> of affect.

This vindicates the engine's existing within-person design. It also rules out a
tempting wrong turn: a *replacement-primary* engine would generate the affect
trend by turning over agents, which the APC evidence says is *not* how it
happened.

### 4.2 How the current engine maps to the truth-model

The good news from the audit's engine read: the architecture is **already mostly
right.** The engine's primary loop *is* within-person updating under a
period-forced elite/media schedule. Mapping each causal element to the existing
`abm/rules/`:

| Causal element (truth-model) | Engine status today | Assessment / what's needed |
|---|---|---|
| **Within-person updating as primary loop** (L3/L5) | `influence` (bounded-confidence), `party_pull`, `affective_update`, `identity_to_position` | **Right architecture — keep.** This is the correct primary mechanic. |
| **Period forcing via asymmetric elite drift** (L1) | `elite_drift` with per-decade **asymmetric** schedule (R-heavy early / D-heavy late) | **Good — matches the asymmetry finding.** Confirm the asymmetry direction tracks the *elite* (GOP-right) story, not just ANES voter shifts. |
| **Party-driven sorting** (L3) | `party_pull` + `identity_sorting` pull agents toward party positions | **Right.** This is Levendusky's "positions move to match party." Keep. |
| **Near-frozen party ID + formative imprinting** | party can change (`party_realignment`); ~16% of agents switch over 45y; **no explicit formative-years imprinting** | **Tighten.** Make party ID stickier and add a formative-years (~ages 14–24) imprint so the baseline is set young and rarely flips (Ghitza-Gelman; GPS r≈.97). Current individual drift (median 0.56 units; 39/250 party switches) is on the high side for *party*; *position* drift to align with party is fine. |
| **Identity stacking / mega-identity** (L4) | `identities` vector, `party_issue_coupling`, `faction_anchor` | **Partial.** Alignment is implicit. Consider an explicit identity-alignment state so affect can be driven by *stacking*, per Mason — the demo's missing master mechanism. |
| **Affect from out-party animus, in-party flat** (L5) | `affective_update`; metric tracks **out-party warmth only** | **Mostly right** (out-party is the quantity that moved). To draw the honest "scissors" the front-end wants, either export a (near-flat) in-party series or state the flat-in-party assumption explicitly. |
| **Media as amplifier on already-sorted agents** (L5) | `media_consumption` (homophilous diet), `shocks` | **Right pattern** (selective exposure). But the **2008/2012 social-media events are coded as a real affect shock** — stronger than evidence supports. Make social-media affect forcing **small / off-by-default / tunable**; keep cable (Fox 1996) as the real amplifier. |
| **Status/threat shocks** (L5) | `threat_dynamics`; 2016 `perceived_threat=0.5` for 60% of Reps | **Reasonable but contested** (Mutz vs Morgan). Keep, but label as a contested channel; don't over-weight. |
| **Misperception / meta-perception** (L5) | `perception_update`, `perceived_other_party` | **Present — good.** This is also the X7 intervention substrate. |
| **Coupling heterogeneity / activist tail** (L3, F1) | per-agent `epsilon`/`stubbornness`/`identity_strength`; **no explicit attention/engagement dimension** | **Gap.** The literature is clear that elite-cue coupling is *strong for the engaged, weak for the inattentive*, and the asymmetry/persistence live in the activist tail. Add an engagement/attention axis that gates how strongly each agent follows elite cues and feeds the F1 primary-capture loop. |
| **Elite ↔ activist/donor feedback** (F1) | `faction_anchor`, faction-emergence events (Tea Party/MAGA/Bernie/DSA) | **Partial** — factions exist as labels/anchors but don't *push elites back outward*. To get realistic asymmetric persistence, close the loop: activists → elite drift. |
| **Cohort replacement (secondary, issue attitudes)** | `cohort_replacement` (M3) + `residential_migration` (M2), active | **Keep as secondary — do NOT promote to primary.** But **ship it to the front-end** (the demo currently drops `replacement_events`), so the *issue-attitude* story can show turnover while *affect* stays period-driven. |
| **Anti-democratic attitudes as a separate state** (L6) | **not modeled** | **Gap, optional.** If the project ever claims anything about democracy, add a *separate* anti-democratic-attitude state — affect must **not** automatically move it (Voelkel 2023 decoupling). Until then, simply **don't claim** democratic consequences. |
| **Compositional (immigration/education/secularization)** | not explicit | Low priority; slow second-order channel. |

### 4.3 The targeted change list (priority order)

1. **Keep the within-person-primary architecture; do not make replacement
   primary.** *(The single most important design decision — and it's a "don't.")*
2. **Make party ID stickier + add formative-years imprinting** so individual
   *party* switching matches the ~.97-stability evidence; let *position* drift
   (sorting) carry the visible movement. *(Targets the audit's individual-drift-
   vs-stability tension at the source.)*
3. **Re-grade the period shocks:** move the elite-drift emphasis to
   Gingrich/1994; demote social-media-as-affect-cause to small/tunable; keep
   Fox/cable; keep the 2016 threat shock but label it contested; reconsider
   Citizens-United-as-elite-drift. *(Aligns the engine's event mechanisms with
   the evidence grades in §2.1/§3.)*
4. **Add a coupling-heterogeneity / engagement axis** and close the
   activist→elite feedback loop, so asymmetric, self-reinforcing polarization
   emerges from the right subsystem rather than from uniform mass radicalization.
5. **Make identity stacking explicit** so affect is driven by alignment (Mason),
   the demo's missing master mechanism.
6. **Expose the data the truthful story needs** (this is mostly a publish/repack
   change, not modeling): ship `replacement_events`, the full per-agent affect
   series, and — if you want the honest scissors — an in-party warmth series or a
   stated flat-in-party assumption.
7. **Keep affect and any future anti-democratic-attitude state separate**, and
   until the latter exists, don't make democratic-consequence claims.

### 4.4 What the engine already gets right (don't lose it)

- The **primary loop is correct** — within-person updating under a period elite/
  media signal, not agent turnover.
- **Asymmetric elite drift** is modeled (rare and correct).
- **Selective-exposure media** (homophilous diet) is the right pattern.
- **Misperception** is a first-class construct (and the substrate for the one
  honest perception-correction intervention).
- The **affective spine** ("they didn't move on issues, they came to dislike each
  other") is the scientifically correct thesis.

---

## 5. How this reconciles with the web-demo audit

Three updates flow back to [`web_demo_audit.md`](web_demo_audit.md):

1. The audit's "aggregate change is mostly cohort replacement" line was **too
   blunt** and is corrected here: cohort replacement is secondary; sorting and
   affect are within-person/period. The audit's §5.2 #6 tension (the demo
   foregrounds individual drift while hiding replacement) is **still valid but
   re-framed**: the fix is not "make replacement primary," it's (a) keep
   within-person drift as the visible mechanism but make *party* switching rarer,
   and (b) *ship* replacement so the issue-attitude story can show it.
2. The **affective spine is confirmed correct** and is a *period* phenomenon —
   good news for the demo's whole framing.
3. The engine-science flags in the audit (social-media-as-cause,
   Citizens-United-as-elite-drift, asymmetry) are **upheld and sharpened** by the
   causal chain here.

And per the project's framing that **the website is intentionally mock/illustrative
for now**, the value of this document is less "the website is wrong" and more
**"here is the truth the engine should encode, and the specific engine outputs the
real website will need"** — namely: a period-forced within-person trajectory, a
real full-crowd affect series (and ideally an in-party series), shippable
replacement events, an engagement/activist axis, and event mechanisms re-graded
to the evidence.

---

## Appendix — key sources (grouped)

**Decomposition / cohort vs within-person:** Green, Palmquist & Schickler
*Partisan Hearts and Minds* (party-ID r≈.97); Kuziemko & Washington 2018 (AER,
Southern realignment = conversion, race-driven); Ghitza, Gelman & Auerbach 2023
(AJPS, formative-years imprinting); Rosenfeld 2017 (Socius) & Baunach 2011 (SSM
~⅓ replacement); Phillips 2022 (*Political Behavior*, APC — affect is period, not
cohort); Stoker 2020 (APC accounting); Boxell, Gentzkow & Shapiro 2017/2021
(by-age; cross-national); Firebaugh (linear decomposition method).

**Top-down chain:** McCarty, Poole & Rosenthal *Polarized America* (DW-NOMINATE);
Hacker & Pierson "Confronting Asymmetric Polarization"; Mann & Ornstein; Theriault
*The Gingrich Senators*; Carmines & Stimson *Issue Evolution*; Levendusky *The
Partisan Sort*; Zaller *Nature and Origins of Mass Opinion* (RAS); Hetherington
"Resurgent Mass Partisanship"; Hopkins *The Increasingly United States*; Bawn et
al. "A Theory of Political Parties"; Fiorina *Culture War?* (sorting≠polarized).

**Affective polarization:** Iyengar, Sood & Lelkes 2012 ("Affect, Not Ideology");
Iyengar et al. 2019 (ARPS review; 22.6°→40.9° trend); Mason 2015/2016/2018
(sorting/identity stacking); Abramowitz & Webster 2016 (negative partisanship);
Martin & Yurukoglu 2017 (cable causal); Allcott et al. 2024 (Meta-2020
deactivation ~null); Mutz 2018 + Morgan 2018 (status threat, contested);
Ahler & Sood 2018 (misperception); Iyengar & Westwood 2015 (discrimination);
Voelkel et al. 2023 (affect ≠ anti-democratic attitudes).

*(Full URLs are in the three underlying research briefs; this is the
consolidated reference list.)*
