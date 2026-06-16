# Phase 10 — Landing Summary

*Status: shipped. Intervention library (X1–X7) redesigned against
the Phase 9 ANES-recalibrated engine. Last updated 2026-06-16
(reality-validation — re-measured on the COMMON-MODE + ECON canonical config).*

> **✅ reality-validation ECON common-mode — RE-MEASURED on the econ-channel canonical
> config (2026-06-16; methods §5.31).** The reality-validation workstream added a
> second common-mode channel — an **economic** one driven by an exogenous thermostatic
> policy-mood forcing (`ANES_FULL_COMMONMODE_ECON_KWARGS`, `economic_common_mode=True`,
> amplitude 0.09) that fixes the mid-period econ center-of-mass error. X1–X7 were
> re-measured (9 seeds × 4 release decades). **Every bucket is UNCHANGED** — the
> library is robust to the econ fix too: **X1 backfire** (Δsep +0.14→+0.23 across
> decades), **X6 affect partial@1990 → real@2000/2010/2020** (Δaff +0.11→+0.21),
> **X5 null/null**, **X2/X3/X4/X7 null**. No tag moved (the econ channel is a rigid,
> sorting-invariant translation, so intervention Δsep/Δaff are unaffected).
> Falsification: same pre-existing X7 misses (1990/2000/2020). The §2 scoreboard
> remains valid.
>
> **✅ reality-validation — RE-MEASURED on the common-mode canonical config
> (2026-06-15; methods §5.30).** The reality-validation workstream added an
> emergent common-mode cultural channel (`ANES_FULL_COMMONMODE_KWARGS`,
> `cultural_common_mode=True`, turnover 0.007) that fixes the mid-period cultural
> center-of-mass error. X1–X7 were re-measured (9 seeds × 4 release decades, 288
> runs). **Every bucket is UNCHANGED** — the library is robust to the cultural fix:
> **X1 backfire** (Δsep +0.13→+0.22 across decades), **X6 affect real**
> (Δaff partial@1990 → real@2000/2010/2020, +0.11→+0.22), **X5 null/null**,
> **X2/X3/X4/X7 null**. No tag moved. Falsification: same pre-existing X7 misses
> (now 1990/2000/2020 — the known "perception-correction too weak" limitation,
> not a tag change). The §2 scoreboard remains valid.
>
> **✅ emergence-recovery E5.5 — RE-MEASURED on the endogenous canonical config
> (2026-06-14).** After the E5 canonical flip (positional sorting now EMERGES
> from the activist→elite→mass loop instead of replaying fed centroids —
> `ANES_FULL_KWARGS`, `endogenous_elite`, the adopted E4 ABC point), X1–X7 were
> re-measured (9 seeds × 4 release decades, 288 runs). **Every bucket is
> UNCHANGED** — the intervention library's honest story is robust to the engine
> flip: **X1 backfire** (cross-release Δsep +0.158, was +0.129), **X6 affect real**
> (Δaff +0.169, was +0.165), **X5 deprogramming null/null** (Δsep −0.009 / Δaff
> +0.001 — same targeted-tail-doesn't-scale finding), **X2/X3/X4/X7 null**. No tag
> moved; magnitudes shifted only slightly. Falsification: 26/28 pass (the same
> pre-existing X7 1990/2000 early-decade null). The §2 scoreboard below is updated
> to the endogenous numbers; the lower banners are pre-E5 history.

> **✅ MHV S5 T5.0 — X5 REPLACED: "Ranked-choice voting" → "Deprogramming &
> exit programs" (2026-06-12).** The T4.5 X5 backfire (below) was a dangling-
> lever artifact: X5's durable arm halved `tier_d_anes_drift_multiplier`, which
> scales the *scheduled* `EliteDrift` — gone on the S3 data-fed elite path, so
> the lever was inert and the residual faction-strength halve spuriously raised
> separation. Rather than re-wire RCV onto an arbitrary `[T]` magnitude, X5 was
> **replaced** with the library's only *targeted-tail* intervention:
> deradicalization / exit programs applied to a treated **50%** of faction-tagged
> agents via **two levers** — they exit the faction (clear `faction_center` →
> `FactionAnchor` self-gates off) **and** have their extremist identity moderated
> (`identity_strength` ×0.5 → weaker `PartyPull`). Both are live shipped levers.
> **Re-measured (9 seeds × 4 release decades, fitted config): X5 → null / null**
> (cross-release mean Δsep −0.0062, Δaff +0.0004) — exact no-op at 1990/2000 (no
> factions emerged yet; decade-gated), correctly signed but sub-threshold at 2010
> (−0.0037) / 2020 (−0.0212). Robust across an escalation ladder (exit-only,
> +identity, +50% reach — all null). Honest finding: targeted counter-extremism
> on the organized extreme does **not** scale to aggregate separation.
> **All other buckets unchanged:** X1 backfire, X6 affect real, X2/X3/X4/X7 null.
> The directions test (`test_intervention_library_directions_hold`) re-blessed
> and **passes**. Provenance [N] (deradicalization efficacy contested; methods
> §5.26). Web demo still serves the pre-flip export until the **S5 re-export
> (T5.1)**.
>
> *Superseded banner (MHV T4.5 — the X5 backfire that motivated this replacement):*
>
> > **✅ RE-MEASURED on the S4-calibrated canonical engine (MHV T4.5, 2026-06-12).**
> The stale-banner (below, from S2 T2.6) is now **RESOLVED**: X1–X7 were
> re-measured on the fitted preset (`scripts/anes_preset.py`: the S4 ABC point
> — party_pull 0.297, fj 2.195, constraint_rate 0.0348, animus 0.655, noise
> 0.0478, **elite_lead 1.798**; methods §5.25). 9 seeds × 4 release decades.
> **Only one bucket moved: X5 (ranked-choice voting) issue_sorting partial →
> BACKFIRE** (Δsep +0.117 cross-decade mean). Cause: X5's primary lever halves
> `tier_d_anes_drift_multiplier`, which is **inert on the S3 data-fed elite path**
> (the scheduled EliteDrift it scaled is gone), so RCV no longer damps divergence
> and the residual FactionAnchor halving slightly *raises* separation. X5 needs
> re-mechanization onto the elite-lead / party-centroid series — **deferred to S5**.
> All others hold: **X1 backfire** (Δsep +0.129), **X6 affect real** (Δaff +0.165),
> X2/X3/X4/X7 null. The directions test (`test_intervention_library_directions_hold`)
> is un-xfailed and **passes**. Falsification: 6 cells fail — X5 at all 4 decades
> (RCV backfires: a measured, reportable finding, not luck) + the pre-existing X7
> null at 1990/2000. ANES §11 scorecard on the fitted config: **18/24 PASS**;
> four-cut holdout battery **PASS 3/3** ([s4_holdout.md](s4_holdout.md)).
> Web demo still serves the pre-flip export until the **S5 re-export**.
>
> *Superseded historical banner (S2 T2.6 — pre-S4):* the preset had flipped to
> the emergent substrate (`n_issues=7` + `ConstraintOp` + BC wake; §5.23) but
> phase-10 was not yet re-blessed; X6 affect had been re-blessed partial→real at
> T2.6. That re-measure is now done (this banner).

> **MHV T0.4 re-measure (demo-physics knob adjudication, 2026-06-10).**
> Re-measured after the canonical substrate changed: **momentum (0.4)
> relocated** to a presentation-side EMA in the repack (it was a display
> knob, not a mechanism), and the **hard IC x-cap recalibrated** to an
> ANES-anchored soft cap (wrong-side 1980 econ tail thinned to the
> measured 3.76%/1.60% instead of clipped to 0%); `fj_alpha_scale=2.8`
> kept and provenance-tagged L/E/N. (methods.md §5.15.) **All public
> buckets unchanged**: X1 backfire at every decade (cross-release mean
> **+0.188**, was +0.203 — momentum had been mildly amplifying the
> repulsion cascade), X5 partial-on-average with the same decade pattern
> (partial 2000/2020: −0.119/−0.070; null 1990/2010), X6 affect partial
> 1990–2010 / real 2020 (+0.091/+0.140/+0.146/+0.218 — numerically
> indistinguishable from the prior table), X2/X3/X4/X7 null.
> Falsification 27/28 with the same pre-existing (1990, X7) miss. ANES
> §11 scorecard on the new substrate: **20/24** (up from 15/24). No tag
> re-bless required; the scoreboard below stands with the X1 magnitude
> note above superseded by the T0.4 numbers.

> **Step 2 re-measure (web_demo evidence re-grade).** The numbers below
> were re-measured on the **unified Step-1 substrate** — the single
> canonical preset [`scripts/anes_preset.py`](../../scripts/anes_preset.py)
> with `evidence_regrade=True` (Gingrich/CU re-attribution, social-media
> demotion, explicit identity-alignment → animus) plus the web-demo
> realism knobs (momentum 0.4, fj_alpha_scale 2.8, x_cap 0.45, noise
> 0.04) and the Step-2 flag-1 fix (cohort identity-reseed + faster
> identity sort, so aggregate `identity_alignment` rises ~0.22→0.42 per
> Mason). Previously (pre-Step-1) the buckets were measured on a
> *different* substrate than the demo shipped. **Net effect on the
> public lanes: unchanged at the representative (cross-release) level —
> X1 still backfires, X6 still real, X5 still partial-on-average, the
> rest null.** What moved: X1 magnitude (now +0.28…+0.40, was
> +0.32…+0.37) and, most notably, **X5 is now sharply decade-dependent**
> — null at 1990/2010, partial at 2000/2020 (see §3.2).

> **Exogenous-shocks re-measure (2026-06-01).** Re-measured again after the
> general exogenous-shock mechanism (`abm/pillars/shocks.py`) was enabled in
> the canonical preset (`exogenous_shocks=True`): the empirical catalogue
> S-911 (transient out-party warming, Sept 2001 ≈ tick 65) and S-Obergefell
> (slight cultural-axis divergence, June 2015 = tick 105). **All buckets are
> unchanged** — X1 backfire (cross-release mean +0.351), X5 partial-on-average
> (−0.0585), X6 real (+0.218 aff), the rest null; falsification 27/28 with the
> same pre-existing (1990, X7) fail. This is structural, not luck: Δ is
> `intervention.post − control.post` at the *same* (release, seed), and both
> arms carry the same shocks, so shocks cancel in the difference. S-911 also
> decays to <0.02 warmth by the 2010 window, and S-Obergefell only touches the
> 2020 window. No tag re-bless required; the scoreboard below stands.

> **Affect re-grade re-measure (2026-06, `affect-bands-investigation`).** The
> affect bands were re-grounded against the raw ANES out-party thermometer (the
> old bands were hand-scaled and ~0.2 too cold), and the engine's affect channel
> was re-calibrated to match — warm 1980 seed, softer contact `affect_lr`, retired
> saturation, plus a new contact-independent `MediatedAnimus` channel (parasocial
> animus via aligned identity × a dated media ramp). Net effect on the public
> lanes: **one tag moved — X6 affect `real` → `partial`** (Δaff +0.218 → **+0.149**,
> a hair under the 0.15 "real" floor). Mechanistically honest: the re-grounded
> baseline is *less* polarized, so a contact lever has less animus to undo. X6
> remains the strongest affect lever, now sitting on the real/partial boundary.
> X1 (backfire), X5 (partial-on-average), and the rest are unchanged
> (`test_phase6` green). See [`affect_bands_investigation.md`](../affect_bands_investigation.md).

Phase 10 re-validated the seven public-facing interventions (X1–X7)
against the Phase 9 engine. Phase 6's library was blessed on the
pre-Phase-9 engine and didn't survive the recalibration — three
substantive redesigns (X1, X4, X5) and several refinements were
needed. The design contract is
[`docs/phase10_interventions/redesign_briefs.md`](../phase10_interventions/redesign_briefs.md);
this document records the landed measurement.

---

## 1. Sweep configuration

Measurement script:
[`scripts/phase10_measure.py`](../../scripts/phase10_measure.py).

- **Preset:** the unified canonical
  [`scripts/anes_preset.py`](../../scripts/anes_preset.py) `ANES_FULL_KWARGS`
  (`evidence_regrade=True`; Phase-9 ANES knobs + web-demo realism knobs).
  Shared byte-for-byte with `publish_web_data.py`, so the Δ a user sees
  is measured on exactly the trajectory the demo ships.
- **Release ticks:** 30 / 60 / 90 / 120 (= 1990 / 2000 / 2010 / 2020).
- **Counterfactual horizon:** 30 ticks (~10 years) post-intervention.
- **Ensemble:** 9 seeds; 288 total simulation runs.
- **Parallelism:** `run_seeds_parallel`; 60s wall.
- **Δ metric:** intervention.post − control.post at the same
  (release, seed). Measures additional effect beyond natural drift.

Raw JSON at
[`docs/results/phase10_measurement.json`](phase10_measurement.json).

---

## 2. Scoreboard (9 seeds, anes_full)

Δsep = Δparty_separation (helpful = negative).
Δaff = Δaffective_polarization (helpful = positive).
Buckets: |Δ| < 0.05 → null; 0.05–0.15 helpful → partial; ≥ 0.15
helpful → real; > 0.05 opposite → backfire.

_(**emergence-recovery E5.5 — re-measured 2026-06-14 on the ENDOGENOUS config**;
9 seeds, anes_full = endogenous canonical. Supersedes the S4 fed-config table.
X5 = "deprogramming & exit programs" (T5.0 replacement), not RCV.)_

| release | X1 sep | X2 sep | X3 sep | X4 sep | X5 sep | X6 sep | X7 sep |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1990 | **+0.103 BF** | +0.000 | +0.003 | +0.000 | +0.000 | -0.007 | +0.000 |
| 2000 | **+0.175 BF** | +0.000 | +0.007 | -0.000 | +0.000 | -0.009 | +0.000 |
| 2010 | **+0.181 BF** | +0.000 | +0.007 | -0.000 | -0.005 | -0.008 | +0.000 |
| 2020 | **+0.174 BF** | +0.000 | +0.006 | +0.000 | -0.032 | -0.005 | +0.000 |

| release | X1 aff | X2 aff | X3 aff | X4 aff | X5 aff | X6 aff | X7 aff |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1990 | -0.006 | +0.000 | -0.000 | +0.006 | +0.000 | **+0.103 P** | -0.001 |
| 2000 | -0.009 | +0.000 | -0.000 | +0.005 | +0.000 | **+0.151 R** | -0.004 |
| 2010 | -0.008 | +0.000 | -0.000 | +0.003 | +0.000 | **+0.177 R** | -0.008 |
| 2020 | -0.007 | +0.000 | -0.000 | +0.002 | +0.002 | **+0.244 R** | -0.006 |

Legend: **BF** = backfire, **P** = partial, **R** = real. (Cells with no
tag are null, |Δ| < 0.05.) Cross-release means: **X1 +0.158 (backfire)**,
**X6 aff +0.169 (real)**, **X5 −0.009 sep / +0.001 aff (null/null)**;
X2/X3/X4/X7 null. **Every bucket matches the FED config** (X1 +0.129→+0.158,
X6 +0.165→+0.169) — the library is robust to the endogenous flip. X5 stays
null/null (the T5.0 "targeted counter-extremism doesn't scale to aggregate
separation" finding holds on the endogenous substrate too; X5 trends slightly
more negative late — 2020 −0.032 — but stays sub-threshold).

**Falsification (per brief §0.3):** 26/28 pass.
Two fails at (1990, X7) and (2000, X7) on the "Δsep and Δaff both ≈ 0"
sub-rule (pre-existing early-decade null — correction-rate boost insufficient
before the late-period animus builds; Phase 11 bias-maintenance candidate);
X7 at 2010/2020 passes the looser ±0.10 envelope.

---

## 3. Three lanes (the public-facing story)

> **⚠ Narrative below is pre-S4 (the prose lanes predate the T4.5 re-measure).**
> On the S4-calibrated config (§2 table + top banner are authoritative): **X5
> moved partial → backfire** (its drift_mult lever is inert on the data-fed elite
> path) and **X6 affect is `real`** (not the partial/boundary the prose describes).
> The three-lane framing is refreshed in S5's doc sweep; the buckets here are
> superseded by §2.

The seven interventions land in three honest categories:

### 3.1 The popular-but-backfires — X1

**X1 (cross-partisan exposure)** produces Δsep ≈ +0.33 at every
release decade. Naive expectation: showing people the other side
humanises them. Engine output: at population scale and sustained
intervention, exposure activates identity threat and triggers
Bail-style backfire that *cascades* through the affect-gated
`BacklashRepulsion` mechanism. The result is decade-invariant —
unlike X5 and X6, X1's effect doesn't depend on what state the
society started in.

### 3.2 The empirically-supported workers — X5 and X6

**X5 (ranked-choice voting + open primaries + multi-member
districts)** produces helpful Δsep that is now **sharply
decade-dependent** on the Step-2 substrate: **partial** at 2000
(-0.106) and 2020 (-0.063), but **null** at 1990 (-0.036) and 2010
(-0.029); the cross-release mean (-0.058) keeps the single public
bucket at **partial**. Drutman's *Breaking the Two-Party Doom Loop*
mechanism — elite-incentive change → less primary-driven divergence —
lands as a contingent effect: the redesign halves `EliteDrift` rate
AND `FactionAnchor.strength` AND centroids+cues, so it bites hardest
when the drift it suppresses is itself large (the faster Step-1
Gingrich/identity-alignment substrate makes the off-peak decades
recover less). This decade-contingency is *itself* the honest
finding — "structural reform helps, but only in some windows."
Direct RCV empirics (Donovan & Bowler 2023) are mostly null; the
engine reports the *theoretical* mechanism's prediction, flagged
`[T]`-heavy in provenance.

**X6 (shared neighborhoods / workplaces / institutions)** produces
helpful Δaff that, on the affect-re-graded substrate (2026-06), is now
**decade-dependent**: **partial** at 1990–2010 (+0.092 / +0.140 / +0.146)
and **real** at 2020 (+0.218); the cross-release mean (+0.149) sits right
on the real/partial boundary, so the single public bucket is now
**partial** (was real). This is an honest consequence of re-grounding
affect to the real ANES thermometer: the baseline is less polarized
(especially early), so a contact lever has less animus to undo — and the
effect is largest in 2020 when animus is highest, exactly where contact
has the most to recover. Still within the Pettigrew-Tropp `r ≈ -0.21` and
Mousa 2020 `~0.10 SD` envelopes; X6 remains the strongest affect lever.
The mechanism: +1 cross-party involuntary cooperative tie per agent
(Mousa / Lowe envelope) + `cooperative_share` boost for participants
(Pettigrew 2009 secondary-transfer) + threat reset for participants
(Mutz 2006). Restricting the affect/threat reset to agents who actually
received a new tie was the key calibration: the prior "reset everyone"
mechanism overshot by 3-4×.

### 3.3 The popular-but-doesn't-work — X2, X3, X4, X7

**X2 (fix the algorithm)** lands exactly null on both axes.
Faithful to the Meta-2020 megastudy (Guess et al. 2023; Allcott et
al. 2024 deactivation).

**X3 (quit cable news)** lands small-backfire-direction null
(+0.003 to +0.007). At Allcott et al. 2020's `~5pp / ~0.04 SD`
individual envelope, applied to a 20% treated fraction
(speculative), the population-level effect is below the null
threshold.

**X4 (bipartisan dialogue programs)** lands at the floor of the
Voelkel 2024 ~0.04 SD envelope (Δaff ≈ +0.004). The Phase 10
third-pass mechanism (`cooperative_share` boost + threat reset
for primed agents) gives the correct direction; the magnitude
is small because reach is 20% and the engine has powerful
centripetal-to-polarization forces.

**X7 (perception correction campaign)** lands null. The mechanism
*works* (treated agents' perceptions correct fast toward actual
centroids during the campaign) but the population-level affect
follow-through is small. The interpretive finding: even when
perception is sustainably corrected for 20% of agents, the
affect signal only propagates at cross-party encounters, which
are rare in a homophilous network. Lay framing: *the perception
gap is real, correcting it works, but most people rarely
encounter the out-party in a way the corrected perception
matters.*

---

## 4. What changed from Phase 6/7

Phase 6's library was blessed at end-of-S4 on the pillar; the
Phase 9 recalibration broke several mechanism assumptions.

### 4.1 Substantive mechanism redesigns

- **X1.** Dropped hard-coded `asymmetric={0:0.7, 1:1.3}` — Phase
  9's post-2016 `threat=0.6` event encodes the asymmetry
  endogenously, so hard-coding double-counts. Boosts
  `threat_amplification` 1.0→1.5 and `identity_weight` 0.5→0.6
  for a sustained 60-tick window. Direction-faithful to Bail 2018
  via the threat channel; magnitude calibrated to land at clear
  backfire without runaway.

- **X4.** *Mechanism swap* — dropped the Phase 6
  `identity_weight_override` path. Phase 9's
  `(1 − identity_weight) × party_issue_coupling × issue_term`
  channel inverts the prediction (lower identity_weight slightly
  *increases* cooling at modern decades). Replaced with
  `cooperative_share` boost (Pettigrew 2009 secondary-transfer)
  and `perceived_threat` reset (Mutz 2006 / Levendusky 2021 *We
  Need to Talk*). Direction is now empirically faithful.

- **X5.** Added halving of `tier_d_anes_drift_multiplier`
  (`EliteDrift` rate) and `FactionAnchor.strength`, ongoing.
  Without these, Phase 6's one-shot centroid+cue halve was
  transient — Phase 9's amplified drift schedule re-diverged
  centroids within ~5 years.

- **X7.** Added a new perception-target channel: per-agent
  `perception_target_override = "actual_centroid"` switches
  `PerceptionUpdate` from pulling toward observed-neighbour mean
  to pulling toward the actual env-level centroid. The
  "campaign reaches the agent with external information"
  reading. Without this, the rule's pull-toward-observed-neighbour
  was too slow to correct perception in a homophilous network
  even at boosted `correction_rate`.

### 4.2 Refinements

- **X1, X4, X7 durations.** Originally 4 / 6 / 3 ticks (read from
  literature follow-up windows). Revised to 60 ticks each
  (sustained policy framing) — durations match the lay
  intervention story rather than the literature's one-shot
  durability windows.

- **X3 reach.** Phase 6 zeroed cable for 100% of agents (implicit
  full-population intervention). Phase 10 applies to a treated
  20% (Allcott 2020 envelope).

- **X6 reset scope.** Phase 6 reset out-party affect for *every*
  agent. Phase 10 restricts the reset to agents who actually
  received a new cross-party cooperative tie (~50% of
  population). Brings Δaff from +0.5 overshoot down into the
  +0.2 Mousa/Pettigrew envelope.

### 4.3 Engine plumbing added in Phase 10

- Per-agent override `identity_pull_strength_y_override` on
  `IdentityToIdeologyPull` (built for the original X4 design;
  retained for any future intervention).
- Per-agent override `correction_rate_override` on
  `PerceptionUpdate`.
- Per-agent `perception_target_override` on `PerceptionUpdate`
  (Phase 10 third-pass).
- New env-rule `PerceptionBoostExpiry` for X7.
- New env-rule `X1ExposureExpiry` for X1 (handles rule-level
  attr reverts).
- `IdentityPrimeExpiry` extended for X4's new
  `cooperative_share` / `perceived_threat` restore path.

### 4.4 Bugs found and fixed during Phase 10

Two bug-classes surfaced during the first measurement sweep:

1. **`_S4_BASE` clobber.** Every Phase 10 intervention initially
   used `param_bundle=_S4_BASE` (inherited from Phase 6 pillar
   design). On the historical arc, `apply_intervention` was
   unconditionally overwriting the calibrated rule attributes
   with pillar defaults — silently killing `EliteDrift` and
   forcing `BC.strength` back to 0.08. Fix: all Phase 10
   interventions use `param_bundle = ()` and route all rule-attr
   mutations through `setup` functions.
2. **Inert env-attr knobs.** X5 initially mutated
   `env.attrs["tier_d_anes_drift_multiplier"]` post-build — that
   knob is only read at build time. The runtime drift schedule
   lives in `env.attrs["elite_drift_schedule_active"]` and on the
   `EliteDrift` rule directly. Fix: X5 now mutates both. The
   same family bit X1 (BacklashRepulsion needed `strength` set,
   not just `threat_amplification`).

Both classes are documented in
[`redesign_briefs.md §0.5`](../phase10_interventions/redesign_briefs.md)
for the writeup record.

---

## 5. Provenance roll-up

Knob-value provenance tags across the seven interventions
(see brief §0.1):

| tag | count | share |
|---|---:|---:|
| `[L:M]` literature magnitude | 6 | 25.0% |
| `[L:D]` literature direction | 7 | 29.2% |
| `[T]` theoretical / mechanism-pin | 10 | 41.7% |
| `[C]` calibration choice | 1 | 4.2% |
| **total** | 24 | |

**X5 carries the most `[T]` weight** (4/4 knobs theoretical —
direct RCV empirics are mostly null; the engine reports the
Drutman 2020 mechanism's prediction). **X6 is `[L:M]`-heaviest**
(within Mousa 2020 / Pettigrew-Tropp envelope). **X2 is the
single-knob null lever** (1/1 `[L:M]`).

---

## 6. Honest limitations

1. **Sustained-policy framing.** X1, X4, X7 are measured as
   sustained-for-60-ticks interventions. The literature's
   one-shot dose / short-follow-up envelopes don't directly
   translate; the magnitudes here are extrapolations from
   measured individual-level effects to "what if this were a
   20-year sustained policy."
2. **20% treated-fraction speculation.** X3, X4, X7 use 20%
   reach as a `[T]` speculation. The brief's sensitivity sweep
   at 5% / 20% / 50% is deferred to Phase 11.
3. **X7 propagation limit.** X7's null reading depends on the
   homophilous-network assumption being strong. A less-sorted
   network would propagate perception correction further.
4. **X1 magnitude is on the high side** (+0.33 vs Bail 2018's
   ~0.10-0.12 SD individual). The non-linearity in the
   affect-threshold cascade means no clean "moderate backfire"
   strength exists between 0.05 (null) and 0.06 (backfire). The
   measured value is the engine's honest extrapolation.
5. **X5 evidence is theoretical.** Donovan & Bowler 2023 found
   null direct US RCV effects on voter polarization; Atkinson
   et al. 2023 Maine likewise. The engine reports the Drutman
   mechanism's *theoretical* prediction. Flagged `[T]`-heavy
   in §5 above.

---

## 7. Phase 11 candidates

Identified in the brief §3 scope collapse, deferred from Phase 10:

- **X1b "anonymous cross-partisan deliberation"** (Combs et al.
  2023) — `identity_weight = 0.2`, `threat_amplification = 1.0`
  on a treated subset. Tests whether anonymity flips Bail's
  backfire to helpful.
- **X2b "bridging-based ranking"** (Stray 2022) — per-agent
  `BC.epsilon += 0.2`. Position-paper-only literature; small-
  magnitude `[T]`.
- **X3b "switching"** (Broockman & Kalla 2024) — partisan-
  outlet swap at ~0.5 SD individual envelope, distinct from X3a
  "quit."
- **X6b "agent-level cooperative mute via secondary transfer
  alone"** (Pettigrew 2009) — already in the engine's
  `cooperative_share` mechanism; X6b would isolate it from the
  +1 tie + affect/threat reset to measure the secondary-transfer
  effect alone.
- **X3/X4/X7 treated-fraction sensitivity sweep** at 5% / 20% /
  50% per brief §0.2 discipline.

---

## 8. The headline finding

*In the Phase 9 ANES-recalibrated engine, only structural
electoral reform (X5) and structural shared-life contact (X6)
move the needle. Cross-partisan exposure (X1) backfires hard.
Algorithm-fixing (X2), quitting cable (X3), dialogue programs
(X4), and perception-correction campaigns (X7) produce null
population-level effects — for distinct, diagnosable reasons.*

That is the Phase 10 story. Whether each null is "the
intervention doesn't work" or "the literature's individual-level
effect doesn't propagate to population scale" varies by
intervention, and the engine's per-mechanism diagnostics let
the user see which it is.
