# Affect-band grounding investigation (2026-06)

_Branch `affect-bands-investigation`, off `web-redesign-ideas` after the
affect-viz deliverable commit. Status: investigation only — one code change
(the phase9 scorer preset reconciliation) + this writeup. No bands changed, no
engine dynamics changed. "Think about it" material for the affect bands._

This came out of verifying the affect-viz `rewire_rate` 0.02 → 0.03 change. The
verification was fine; the investigation underneath it surfaced two bigger
things about how we measure ANES accuracy.

---

## 1. The phase9 scorer was measuring an engine that doesn't ship (FIXED here)

`scripts/phase9_anes_score.py` had its own `PRESETS["anes_full"]` literal that
**drifted from the canonical shipped config** (`scripts/anes_preset.py::ANES_FULL_KWARGS`,
which `publish_web_data.py` + `phase10_measure.py` import). The scorer preset was
missing `evidence_regrade=True`, `exogenous_shocks=True`, `momentum=0.4`,
`fj_alpha_scale=2.8`, `tier_d_ic_partisan_x_cap=0.45`, and used noise σ=0.08 vs
the canonical 0.04. Its `_worker` also didn't pass `evidence_regrade`/
`exogenous_shocks` to `build_schedule`, so those events never fired.

**The one code change on this branch** reconciles the scorer: it imports
`ANES_FULL_KWARGS` and passes the schedule flags, so the scoreboard now measures
exactly what the web demo serves.

**Consequence of the drift:** the committed `phase9_anes_score_anes_full.json`
(18/24 ANES cells) scored the stale config. Against the real shipped config the
arc scores **14/24** (9 seeds). NOT regenerated here — that's a bless action.

---

## 2. The rewire 0.02 → 0.03 change is ANES-neutral (the headline for the other branch)

Measured against the real shipped config, **both** 0.02 and 0.03 score **14/24
with zero cells flipping band membership**. On the scored cells the change is
mildly positive (2025 affect −0.778 → −0.744, warmer toward reference; late
party_sep nudges up). It delivers the visual's goals: party modularity
0.168 → 0.210 (into the 0.21–0.26 band) and partisan cross-cutting 0.259 → 0.202.

The doc's "18 → 16 regression" was a **stale-scorer artifact**: in that config
party_sep sat right on the band floor (1990: 0.426 vs floor 0.42), so the small
rewire-induced reduction flipped 1990+2000 party_sep out. Under the real config
party_sep has margin, so nothing flips. The doc's §1.3 "everything moves toward
target / 18 PASS" framing is also stale-config; the honest framing is
"ANES-neutral on the real gate, delivers the visual."

---

## 3. How far off is the 14/24? (mostly grazing)

The 10 misses are two small systematic offsets, not 10 independent failures:

- **within_party_sd** (4 cells: 1990/2000/2020/2025) all sit just below the floor
  by 0.007–0.013 (5–9% of band width). Engine within-party spread ≈ 0.27; ANES is
  flat ~0.34. Engine over-tightens parties.
- **constraint** runs slightly hot mid-arc: 2000 +0.030, 2010 +0.030, 2020 +0.008.
- **affect** runs slightly cold early: 1990 −0.044, 2000 −0.031, 2010 −0.006.

6 of 10 are within ≤0.013 of the edge. Lifting within-party dispersion ~0.01–0.02
(a touch more GaussianNoise / ic_sigma) likely recovers ~4 cells → ~18/24, and is
the honest direction (engine is below the ANES center, not gaming a threshold).
That's the pending Step-2 re-bless, separate from rewire.

---

## 4. Are the 24 cells correct? (yes for 3/4 metrics; affect is the soft one)

Recomputed party_sep and within-party SD directly from the ANES respondent
coordinates (weighted) — they match the band centers exactly:

| Bucket | ANES party_sep | band | ANES within-SD | band |
|---|---|---|---|---|
| 1990 | 0.499 | [0.42,0.58] ✓ | 0.342 | [0.27,0.41] ✓ |
| 2000 | 0.664 | [0.59,0.74] ✓ | 0.346 | [0.28,0.41] ✓ |
| 2010 | 0.858 | [0.79,0.93] ✓ | 0.329 | [0.26,0.40] ✓ |
| 2020 | 1.111 | [1.04,1.18] ✓ | 0.346 | [0.28,0.41] ✓ |

`party_sep`, `constraint`, `within_party_sd` are faithfully anchored to the ANES
respondent-coordinate data. Caveats: the **2025 row is extrapolated** (ANES data
ends 2024); band width ±0.07 is a heuristic, not the per-bucket sampling CI; and
the **≥18/24 (75%) pass threshold is arbitrary**.

The exception is **affect** — see §5.

---

## 5. Affect bands: the actual grounding work

The affect bands were **hand-scaled from Iyengar 2019 / Finkel 2020 figure 1**
(phase8b design §95, 122–126: "out-party warmth ~45, scaled" → −0.20 to −0.35) —
eyeballed chart reads, not derived via an explicit thermometer→[−1,1] mapping.
The ANES respondent-coordinate recode never built a thermometer series.

**But the raw ANES cumulative file IS in the repo**
(`data/phase9_empirical/raw/timeseries_csv.csv`). I rebuilt the out-party PARTY
feeling thermometer (VCF0218 = Dem party, VCF0224 = Rep party; 7-pt party id
VCF0301, Independents excluded; weighted by VCF0009z) — the same dataset/universe
as the rest of the calibration:

| Decade | ANES out-therm° (±SE) | aff via **(d−62)/50** *(committed web map)* | aff via **(d−50)/50** *(neutral=50)* | Current band | Engine (0.03) |
|---|---|---|---|---|---|
| 1980 | 45.3 ±0.4 | −0.334 | −0.094 | [−0.35,−0.20] | −0.249 |
| 1990 | 42.4 ±0.2 | −0.391 | −0.151 | [−0.45,−0.30] | −0.494 |
| 2000 | 37.7 ±0.4 | −0.486 | −0.246 | [−0.55,−0.40] | −0.581 |
| 2010 | 26.9 ±0.3 | −0.702 | −0.462 | [−0.65,−0.50] | −0.656 |
| 2020 | 19.6 ±0.3 | −0.848 | −0.608 | [−0.78,−0.60] | −0.724 |

(Per-year series is clean: 1978 47.8 → 2020 19.0 → 2024 20.4.)

### Findings

1. **The mapping, not the band, is the dominant uncertainty.** Sampling SE is tiny
   (±0.2–0.4°). The committed web mapping `aff=(deg−62)/50` (`web_demo/rc-shared.jsx`,
   `deg=(1+aff)*50+12`) vs the principled `aff=(deg−50)/50` (50° = ANES-defined
   neutral) differ by a **constant 0.24 affect units — larger than a whole band
   width**. The `+12°` offset was reverse-engineered to land the engine's 1980
   output at ~50°; it is not theoretically anchored. This is the real soft spot.

2. **Under the committed mapping, the real data wants the modern end COLDER than
   the current bands.** Grounded centers (−0.33/−0.39/−0.49/−0.70/−0.85) match the
   current bands through 2000 but the real thermometer is colder at 2010 (−0.70 vs
   band ceiling −0.65) and 2020 (−0.85 vs −0.78). The hand-scaled bands understate
   modern animus.

3. **The engine's affect curve is too shallow either way** — too cold early, too
   warm late. Partly structural: the metric (`abm/metrics/affective.py`) dilutes
   toward 0 because network-isolated agents never form out-party animus, biasing
   the population mean warm. Hitting a cold modern target may require fixing that
   dilution or steepening `AffectiveUpdate`, i.e. an engine-dynamics change.

4. Even the hand-curated anchor disagrees with the raw file: `affect-symptoms-data.js`
   lists 1980 out = 52.8 (Iyengar POQ), but the raw-file weighted partisan value is
   45.9 — another argument to rebuild from raw, not figures.

### Decision (resolved): use the principled midpoint map; fix the engine, not the transform

The display mapping is a free affine transform — the web demo can remap engine
`aff` onto degrees however it likes to make the overlay line up. *Because it's
free, using it to set scoring bands is circular* (you can pick the transform that
"passes"). So scoring uses the principled midpoint map `aff = (deg − 50)/50`
(50° = ANES-defined neutral; the engine's `affect` is seeded at 0 = neutral, so
this is the natural bijection). The demo keeps whatever display map it wants —
that's independent. What the midpoint map reveals (engine + old bands too cold)
is a real finding to fix in the engine (step 3), not stash in the offset.

### Step 1 + 2 DONE — `scripts/affect_band_builder.py`

Reproducible builder (companion to `phase9_anes_target_builder.py`): reads the
raw ANES cumulative file, extracts the out-party party thermometer
(VCF0218/0224, partisans only, weighted VCF0009z), buckets by the same
`DECADE_WAVES`, maps via the midpoint map, and emits
`data/phase9_empirical/derived/{outparty_thermometer.csv, affect_bands.json}`.
Band half-width = max(across-wave half-range, 0.05 floor), labelled an
instrument/temporal allowance (sampling SE is ~0.005, negligible).

**Grounded affect bands (vs the current hand-scaled ones):**

| Panel | out-therm° | grounded band | current (hand-scaled) |
|---|---|---|---|
| 1980 | 45.3 | [−0.14, −0.04] | [−0.35, −0.20] |
| 1990 | 42.4 | [−0.21, −0.10] | [−0.45, −0.30] |
| 2000 | 37.7 | [−0.31, −0.18] | [−0.55, −0.40] |
| 2010 | 26.9 | [−0.51, −0.41] | [−0.65, −0.50] |
| 2020 | 19.6 | [−0.66, −0.56] | [−0.78, −0.60] |
| 2025 | (19.6) | [−0.71, −0.51] *extrapolated, no ANES past 2024* | [−0.85, −0.65] |

The old bands run ~0.2 too cold at every decade. The shape is also different:
reality is **flat-and-warm early** (1980 out-therm 45° ≈ −0.09; barely cold) and
**collapses late** (most of the fall is 2008→2020). The current bands (and the
engine) ramp animus too early.

### Step 3 — root cause found + fix direction validated

Engine `affect` (canonical config, measured at the ANES bucket-centre ticks):

| panel | engine baseline | grounded band |
|---|---|---|
| 1980 (t21) | −0.39 | [−0.14,−0.04] |
| 1990 | −0.49 | [−0.21,−0.10] |
| 2000 | −0.58 | [−0.31,−0.18] |
| 2010 | −0.65 | [−0.51,−0.41] |
| 2020 | −0.72 | [−0.66,−0.56] |
| 2025 | −0.74 | [−0.71,−0.51] |

Two root causes (NOT a band edit — engine dynamics):

1. **The 1980 affect seed is too cold.** `historical_arc.py:1049` seeds
   `initial_affect = normal(−0.25, 0.10)`; the comment assumes "~40°", but the real
   1986–88 out-party thermometer is **45.3° → −0.09** under the principled map. The
   seed corresponds to ~37.5° — ~8–10° too cold. `affect_lr` scaling (uniform OR
   ramped) **cannot** warm the 1980 panel below ~−0.29 — it's a seed floor, not a
   dynamics effect.
2. **The engine front-loads animus (concave); reality back-loads it (convex).**
   Real out-party warmth is flat-and-warm through 2000 (45°→38°) then collapses
   (38°→20° by 2020). The engine drops fastest early and tapers. So a *uniform*
   `affect_lr` cut can't work: it warms late into the band but leaves early too cold,
   or (at strong cuts) overshoots late warm while early stays cold.

**Validated fix direction (5-seed sweep, `scripts/_affect_recal_sweep.py`, since
removed):** warm the seed to ~−0.09 **and** time-ramp `affect_lr` (floor ~0.35–0.5
→ 1.0 by 2020, so early animus is suppressed and the late collapse preserved). This
flips the shape to convex and lands the 2010/2020/2025 panels in the grounded bands
with 1980 moving −0.39 → −0.18 (e.g. warm+ramp0.5: −0.18/−0.28/−0.39/−0.51/−0.61/−0.65,
3/6 panels in-band, rest close). A lower early floor + seed ~−0.07 should close
1990/2000.

Remaining for the implementation pass (needs sign-off — it changes the shipped web
build and the affect "scissors" narrative):
- Pick the seed mean + the `affect_lr` ramp schedule; wire as arc constants/schedule
  (pillar untouched).
- Re-run the **full 9-seed scoreboard** — affect feeds back into ideology via the BC
  affect modulator, the affect-gated `BacklashRepulsion`, and affect-weighted
  `TieRewiring`, so party_sep / modularity / xc must be re-checked, not just affect.
- Note the **isolated-agent dilution** in `affective_polarization` biases the mean
  *warm*; it currently helps, but if the seed/ramp fix is tuned against the diluted
  mean, decide whether to keep or fix the dilution explicitly.
- Wire the grounded bands into `phase8f_lib` and re-bless the affect cells by
  measurement.

---

## What's on this branch

- `scripts/phase9_anes_score.py` — preset reconciliation.
- `scripts/affect_band_builder.py` — the affect-band builder (step 1).
- `data/phase9_empirical/derived/affect_bands.json`, `outparty_thermometer.csv`
  — the grounded bands + thermometer series (step 2 output).
- `docs/affect_bands_investigation.md` — this writeup.

The builder writes derived data and prints the bands; it does NOT wire them into
`phase8f_lib` or change engine behaviour. The `rewire_rate` change and the
affect-viz deliverable live on `web-redesign-ideas`.
