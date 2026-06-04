# Affective-polarization visual: faithful data + cross-cutting recalibration

_Status: 2026-06. Branch `web-redesign-ideas`. Engine change applied + spot-tested;
full literature-pinned suite + Phase 10 re-measure + web pipeline re-run are the
final bless (see Runbook). Deliverable per request: **data + spec** (the visual
itself is not wired into `web_demo/` in this pass)._

This document does three things:
1. Explains and applies the **cross-cutting tie recalibration** (engine) and reconciles the metric definitions.
2. Collects **faithful, cited empirical data** on symptoms of partisan animus (machine-readable in `web_demo/affect-symptoms-data.js`).
3. Specifies the **"thermometer + bars" affective-polarization visual**.

---

## 1. The cross-cutting recalibration

### 1.1 Metric reconciliation (the "26.7% -> 20.6%" question)

The brief cited `xc` falling 26.7% -> 20.6%. Measured against the *current* working
tree (seed 0, `anes_full`), no metric matches that exactly. There are three different
"cross-party tie" numbers, and it matters which one the visual shows:

| Metric | What it counts | 1980 | 2025 (old, rewire=0.02) |
|---|---|---|---|
| `xc` = `cross_cutting_tie_fraction` (**shipped/`cc-data.js`**) | share of **all** edges joining different party, **Independents included** | 0.508 | 0.455 |
| `partisan_cross_cutting_fraction` | share of **partisan-partisan** edges that are Dem-Rep (Independents excluded) | 0.357 | 0.264 |
| (brief's figure) | -- | 0.267 | 0.206 |

The brief's 26.7->20.6 is almost certainly an **older / different-seed** partisan-style
reading; the live engine sits higher. **The literature-comparable metric is the
partisan one** (random mixing is a clean 50% for partisan-partisan edges, ~67% all-edge).
The brief's qualitative diagnosis still holds against the live numbers:

- **1980 too low?** Partisan `xc` = 0.357 sits well below the random-mixing ceiling of
  0.50, i.e. homophily is already "baked in" at 1980. This is partly *real* (ties were
  never randomly mixed) and partly the `social_coord` party-correlation in the initial
  build. The shipped **all-edge** 1980 value (0.508) is essentially **on** the Phase 9
  reference (0.53), so the IC was left unchanged -- see 1.4.
- **2025 too high / slope too compressed?** Yes. The old end (partisan 0.264) and shallow
  slope under-state the empirical collapse, and party **modularity undershoots its
  empirical target by ~0.05-0.10 from 2010 on** (`docs/BACKLOG.md`). This is what the
  change fixes.

### 1.2 What changed

One line, arc only: `abm/pillars/historical_arc.py`, `TieRewiring.rewire_rate` **0.02 -> 0.03**.

The pillar sets its **own** S4 `rewire_rate` (0.02) in `calm_to_camps.py` and is
**intentionally not changed**, so the composition-layer drift-guard
(`test_pillar_stages.py`) stays bit-identical.

### 1.3 Why this value, and why it is honest

A `rewire_rate` sweep {0.02, 0.025, 0.03, 0.035, 0.04, 0.05, 0.07, 0.10} (seeds 0-2)
showed `rewire_rate` is the dominant lever on the slope, and that the three target
families move **together**, not in tension, once the goal is a steeper decline:

| 2025 endpoint | old 0.02 | **new 0.03** | Phase 9 reference | empirical anchor |
|---|---|---|---|---|
| partisan `xc` | 0.264 | **0.207** | -- | ego-networks ~0.12-0.18 (PRRI 2013); marriage-style ~42% relative drop |
| all-edge `xc` | 0.445 | **0.416** | 0.459 | -- |
| party modularity | 0.165 | **0.198** | 0.158 (flagged as undershoot) | true target ~0.21-0.26 |
| party_sep | 1.153 | **1.114** | 0.995 | closer to reference |
| out-party affect | -0.767 | **-0.733** | **-0.725** | **onto the blessed reference** |

Key point for the visual: **affect is the spine, and 0.03 improves it.** Because
affect-weighted rewiring sheds cold out-party ties slightly faster, more rewiring
*reduces* accumulated animus; the old 0.02 over-shot the Phase 9 reference (-0.767 vs
-0.725), and 0.03 lands almost exactly on it (-0.733). So the change steepens
cross-cutting **and** pulls affect, sep, and modularity all *toward* their
empirical/blessed targets simultaneously.

The empirical justification for the steeper slope is the **co-partisan-marriage series**
-- the firmest long-run cross-party-tie measure: co-partisan spouses rose 54% (1973) ->
74% (~2013) [Iyengar, Konitzer & Tedin 2018], i.e. cross-party marriage fell 46% -> 26%,
a ~43% relative drop. The recalibrated partisan `xc` drops 0.357 -> 0.207, a ~42%
relative drop -- in line, while staying *above* the marriage floor (friendship/discussion
ties are less selective than marriage, so a higher cross-party share is correct).

Full new trajectory (seed 0):

```
year  all-xc  part-xc  mod    sep     aff
1980  0.508   0.357    0.097  0.304  -0.249
1992  0.471   0.308    0.132  0.441  -0.456
2004  0.457   0.278    0.150  0.616  -0.581
2010  0.462   0.282    0.148  0.746  -0.586
2016  0.441   0.245    0.172  0.965  -0.654
2025  0.416   0.207    0.198  1.114  -0.733
```

### 1.4 What was deliberately NOT changed (and why)

- **1980 initial conditions (`SOCIAL_BIAS`, `NET_TAU`).** Raising the 1980 partisan
  start toward random mixing would require loosening the initial homophily, but the
  shipped **all-edge** 1980 value (0.508) already matches the Phase 9 reference (0.53),
  and the IC is constrained by the heavily-tested `w2` distribution fit ("geometric
  limitation of the sigmoid-Gaussian generator", `docs/BACKLOG.md`). Disturbing it to
  chase a partisan-only start risks the ideology-distribution calibration -- not worth it
  for the spine. Documented as a known, defensible feature: even in 1980, ties were not
  randomly mixed.
- **The involuntary cross-party stratum (`INVOLUNTARY_PER_AGENT = 1`).** It is a *shared*
  constant (pillar + arc) and is empirically motivated (Mutz & Mondak 2006: kin/workplace
  are involuntary cross-cutting contexts that persist). It sets a floor of ~0.15-0.20 on
  partisan `xc`, which matches the empirical ego-network floor (~0.12-0.18). Lowering it
  was unnecessary once `rewire_rate` did the work, and would have weakened a
  literature-supported mechanism.

### 1.5 Full-fit alternative (documented, not applied)

If a fuller modularity fit is wanted (squarely in 0.21-0.26) **without** giving back
affect, the tested two-knob option is `rewire_rate = 0.04` **plus an arc-only**
`affect_weight_rewire = 0.15` (down from the shared 0.30). Measured (seed 0): partisan
`xc` 0.164, modularity 0.243, sep 1.176, affect -0.718. This needs a *separate* arc
constant so the pillar's `affect_weight_rewire` (0.30) is untouched. Not applied here
because it changes a second tuned mechanism for a marginal gain; 0.03 already lands every
metric in/near band while keeping the change to one line.

### 1.6 Provenance (per the honesty discipline)

- Mechanism (homophilous tie rewiring): **L** -- network sorting / homophily literature.
- `rewire_rate = 0.03` magnitude: **N** -- the model's calibration choice, now anchored
  to the marriage-series relative drop (was already **N** at 0.02).
- The compounded 1980->2025 arc remains **E** (extrapolated).
- "Measure-then-bless" still applies: this change moves the network/affect/sep numbers,
  so the Phase 9 reference means, the Phase 10 intervention buckets, and `cc-data.js`
  must be re-generated and any moved bucket tag re-blessed by **measurement** (move the
  tag, not the threshold). See Runbook.

---

## 2. Faithful empirical animus data

Machine-readable: **`web_demo/affect-symptoms-data.js`** -> `window.ANIMUS_DATA`
(schema v1; every series carries `source` + `url` + an honesty `flag`).

**Strongest spine + bars (ranked for the visual):**
1. ANES in vs out thermometer (spine) -- in ~flat 70-76; out ~48 (1978) -> ~20 (2020). [Iyengar 2012; Boxell/Gentzkow/Shapiro 2024; Finkel 2020]
2. Pew "very unfavorable" -- ~16% (1994) -> 55/58% (2016) -> 62/54% (2022). Cleanest bars.
3. "Child marries out-party" upset -- ~4-5% (1960) -> 49/33% (2010). The wow stat (snapshots; wording changed).
4. "Very cold" (0-24) -- 10/14% (1964) -> 44/50% (2012). Same instrument as the spine.
5. "Other party more immoral" -- 35/47% (2016) -> 63/72% (2022). "Evil not just wrong."
6. Cross-party marriage -- co-partisan spouse 54% (1973) -> 74% (2013); D-R marriages 9% -> 3.6%. The real-world `xc` analogue.
7. Siloed media -- 47% of consistent conservatives name Fox as their main source (2014).

**Kicker:** Thanksgiving dinners across party precincts ran 30-50 min shorter in 2016;
tripled in heavy-ad markets [Chen & Rohla 2018, Science].

**Honest gaps (label in the UI; do not fabricate):** no cross-party *friendship* series
back to 1980 (Pew/PRRI start ~2013-16); split-ticket and partisan-dating series not
cleanly sourced; Mutz 2025 exact cross-cutting %s paywalled.

**Comparability caveats:** ANES thermometer ("the party") and Pew thermometer
("Democrats/Republicans" as people) are different instruments -- separate panels. The
marriage item's wording/scale changed across waves -- show as snapshots, not a line. The
thermometer *gap trend* is robust, but the *level* of animus toward ordinary voters is
contested (Druckman & Levendusky; 2024 APSR) -- footnote it.

---

## 3. Visualization spec: "thermometer + bars"

**Goal.** One honest panel that makes affective polarization legible to an enthusiast:
a literal thermometer for the ANES in/out warmth gap (the spine), a row of symptom bars,
and -- the honest move -- the **engine's `aff` series overlaid on the empirical
thermometer** so sim vs reality is visible side by side.

**Layout.**
- **Left / hero: the thermometer.** Two stacked mercury columns or a single 0-100 scale
  with two markers: in-party (~75, ~flat) and out-party (falls 48 -> 20s). A year scrubber
  (1978-2024) drives both. Show the **gap** as the headline number. Overlay the polarlab
  engine out-party `aff` (mapped to 0-100) as a dashed "model" marker next to the
  empirical out-party marker -- label clearly "simulation" vs "ANES". (Engine `aff` in
  [-1,1]; pick the display mapping used by `cc-data.js`'s thermometer panel and reuse it
  so the two are commensurable. Do NOT present `macro.aff_in_empirical` as engine output
  -- it is the external ANES in-party reference line.)
- **Right / bars: symptom row.** 5-7 horizontal bars from `window.ANIMUS_DATA.bars`, each
  animating between its earliest and latest anchor as the scrubber moves (or two-state
  "then vs now" if the series is snapshots). Color by party where the series splits
  (Dem navy / Rep oxblood, matching `CC` palette). Each bar shows its source on hover and
  its honesty flag (a small dot: solid / snapshot / wording-break / gap).
- **Footer kicker:** the Thanksgiving line as a one-sentence callout.

**Data wiring.**
- Empirical layer: `window.ANIMUS_DATA` (this deliverable).
- Engine layer: `window.CC_DATA.runs.baseline.macro[t].aff` (out-party warmth) and `.xc`
  (cross-cutting) -- after the pipeline is re-run so they reflect rewire=0.03. The
  recalibrated cross-party-tie collapse is itself a great bar: show partisan `xc`
  0.36 -> 0.21 next to the empirical cross-party-marriage 46% -> 26%.

**Honesty requirements (non-negotiable, per repo discipline).**
- Separate ANES vs Pew thermometers; never blend instruments on one axis.
- Snapshot/wording-break series rendered as discrete points, not smooth trends.
- Any 1980 friendship value labeled "extrapolated" (no measured data).
- The sim line labeled as model output, the ANES line as empirical; never imply the
  engine produced the empirical reference.

---

## 4. Runbook -- full bless (run on the dev machine; ~14 min suite)

```powershell
.venv\Scripts\Activate.ps1

# 1. Literature-pinned suite (expected: green; affect/sep/network tests have margin).
.venv\Scripts\python.exe -m pytest

# 2. Re-measure the intervention library against the new baseline.
.venv\Scripts\python.exe scripts\phase10_measure.py
#    -> compare to docs/results/phase10_results.md. If any X1-X7 bucket moved,
#       RE-BLESS BY MEASUREMENT (move the tag, not the threshold).

# 3. Regenerate the web data so cc-data.js reflects rewire=0.03.
.venv\Scripts\python.exe scripts\publish_web_data.py
.venv\Scripts\python.exe scripts\repack_web_demo.py
#    -> cc-data.js xc/aff/mod series now match section 1.3.

# 4. (optional) refresh the Phase 9 reference means JSON if used as a scoreboard.
.venv\Scripts\python.exe scripts\phase9_*  # whichever produces phase9_anes_score_anes_full.json
```

**Verified in this session (Linux sandbox, fresh compile, rewire=0.03):** all tests that
run the historical arc to completion pass -- `test_phase8b_mechanisms`,
`test_phase8c_affect`, `test_phase8c_threat`, `test_phase8e_coupling`, `test_shocks`,
`test_phase9_faction_anchor`, `test_phase9_factional_seeding`, and the
`test_phase8d_independents` network/cross-cutting tests (81 tests green). The remaining
files are pillar-ensemble or isolated-rule tests that do not exercise the arc's
`TieRewiring` and cannot be affected by this change; they were not re-run here only
because 20-seed multiprocessing ensembles are slow on the 2-core sandbox.

## Sources
- Iyengar, Konitzer & Tedin 2018, J of Politics (co-partisan marriage 54->74%): https://pcl.sites.stanford.edu/sites/g/files/sbiybj22066/files/media/file/iyengar-moderating-effects.pdf
- Iyengar, Sood & Lelkes 2012, POQ (thermometer 1980/82; child-marriage 1960->2008): https://pcl.sites.stanford.edu/sites/g/files/sbiybj22066/files/media/file/iyengar-poq-affect-not-ideology.pdf
- Iyengar et al. 2019, Annual Review of Pol Sci (gap 22.6->40.9): https://pcl.sites.stanford.edu/sites/g/files/sbiybj22066/files/media/file/iyengar-ar-origins.pdf
- Boxell, Gentzkow & Shapiro 2024, REStat (slopes; gap 27.4->56.3): https://web.stanford.edu/~gentzkow/research/cross-polar.pdf
- Finkel et al. 2020, Science (in ~75 / out ~48->20; cross-national): https://www.science.org/doi/10.1126/science.abe1715
- Pew 2016 / 2022 (very-unfavorable, very-cold, afraid, immoral): https://www.pewresearch.org/politics/2016/06/22/1-feelings-about-partisans-and-the-parties/ ; https://www.pewresearch.org/politics/2022/08/09/as-partisan-hostility-grows-signs-of-frustration-with-the-two-party-system/
- Pew 2014, Political Polarization & Media Habits (Fox 47%): https://www.pewresearch.org/journalism/2014/10/21/political-polarization-media-habits/
- PRRI 2013 American Values Survey (network composition): https://prri.org/research/poll-race-religion-politics-americans-social-networks/
- Brown & Enos 2021, Nature Human Behaviour (residential segregation): https://www.nature.com/articles/s41562-021-01066-z
- Mutz & Mondak 2006, J of Politics (workplace cross-cutting / involuntary stratum): https://www.polisci.upenn.edu/sites/default/files/mutz_mondak_2006.pdf
- Chen & Rohla 2018, Science (Thanksgiving): https://www.science.org/doi/abs/10.1126/science.aaq1433
- IFS / Hersh-Ghitza & Wang (D-R marriage share): https://ifstudies.org/blog/marriages-between-democrats-and-republicans-are-extremely-rare
