# polarlab — Engine Knobs & Mechanisms Reference

*Comprehensive reference of every rule, every knob, and every
build-time / runtime parameter the engine exposes. Last updated at
the close of Phase 9 (ANES recalibration, 2026-05-28).*

This is the operator's manual for the polarlab engine. Use it when:

- planning new interventions (which rule's strength to flip, what
  range is sensible),
- designing an interactive viz (which knobs are user-exposable, what
  the defaults and ranges should be),
- re-validating existing interventions on the recalibrated engine.

For *why* each value is what it is, see `methods.md`. For *how*
each value was reached in Phase 9, see `results/phase9_results.md`.

## Quick-look index

- §1 — Two scenarios: pillar vs. historical-arc
- §2 — State & domain (what each agent carries, what space they live in)
- §3 — Rules catalogue (every per-tick mechanism, with knobs)
- §4 — Historical-arc parameter constants (per-decade schedules)
- §5 — `build_engine` kwargs (the public surface of the historical arc)
- §6 — Interventions library (X1–X7)
- §7 — Event schedule (per-tick handlers in the historical arc)
- §8 — Calibration & scoring entry-points

---

## 1. Two scenarios

The engine has two top-level callers:

### 1.1 `abm/pillars/calm_to_camps.py` — the pillar
Five-stage canonical journey — the **no-events composition control**
(same rules as the shipped arc, no dated events/schedules, so an arc
regression bisects into rule-interaction vs event-handler). Pinned by
the pillar test families; **do not touch this file** for new
interventions or recalibration work; new mechanisms must default to
no-op for the pillar path. (The old "bit-identity locked" framing was
retired at MHV T2.5 — the pinned tests guard against *accidental*
drift; deliberate, documented rebuilds re-bless them honestly.)

Stages: S0 baseline → S1 bounded confidence → S2 party identity →
S3 partisan media → S4 homophilous network. Each stage adds
mechanisms to the per-tick rule pipeline; positions and affects
carry over continuously.

**MHV S2 T2.5 rebuild:** the pillar runs on the D=7 issues substrate
(stylized uniform-compass IC lifted to items with within-block
residuals; `ideology` = cached block-means projection) with the
emergent rule set — `ConstraintOp` on from S2 (rate 0.02 / resid 0.01,
the arc prior center), `MeasuredAlignment` readout,
`AffectiveUpdate.identity_weight=0.0`; `IdentitySorting` removed (it
was at `sort_rate=0.0` in every stage bundle — never active here).
Scale re-picks for the substrate: BC ε 0.30→0.35, σ_pc 0.25→0.35
(measured: `scripts/audit/t25_pillar_repick.py`; methods §5.22).

### 1.2 `abm/pillars/historical_arc.py` — the historical scenario
Same rules as the pillar, but with time-varying schedules and
empirical anchors that target US 1980-2025. **This is where Phase 9
calibration lives.** Event handlers fire at specific ticks
(Fairness Doctrine 1987, Fox News 1996, Tea Party 2009, Trump 2016,
COVID/Jan6 2020, etc.). Master Phase 9 flag: `tier_d_anes_knobs`.

Tick convention: `TICKS_PER_YEAR = 3.0` (1 tick ≈ 4 months).
Tick 0 = January 1980. Tick 135 = end of 2025.

---

## 2. State & domain

### 2.1 Ideology space (`abm/core/space.py`)
2D continuous compass on `[-1, 1]²`.

- **x ∈ [-1, 1]**: economic axis. −1 = redistributive,
  +1 = laissez-faire.
- **y ∈ [-1, 1]**: cultural axis. −1 = progressive,
  +1 = traditional.

Positions are clipped to the domain after every rule application.

### 2.2 Agent state (`abm/core/state.py`)
Each agent carries:

- `ideology: np.ndarray[2]` — current `(x, y)` position
- `attrs: dict` — heterogeneous mutable bag, used for:
  - `party: int ∈ {0, 1, 2}` — 0 = Democrat, 1 = Republican,
    2 = Independent
  - `party_cue: np.ndarray[2]` — agent's personal cue centroid
    (PartyPull target)
  - `affect: dict[party_id → float ∈ [-1, 1]]` — out-party warmth
  - `stubbornness: float ∈ [0, 1]` — Friedkin-Johnsen anchor strength
  - `anchor: np.ndarray[2]` — FJ anchor position
  - `epsilon: float` — per-agent BC ε (Phase 8b M1 heterogeneity)
  - `fj_alpha: float` — per-agent FJ_ALPHA
  - `learning_rate: float` — per-agent affect learning rate
  - `identities: np.ndarray[3]` — 3-dim social-identity vector
  - `media_diet: dict[outlet_id → weight]`
  - `perceived_other_party: dict[party_id → np.ndarray[2]]` —
    biased perception of out-party centroid
  - `cooperative_share: float ∈ [0, 1]` — Pettigrew-Tropp mute weight
  - `threat: float ∈ [0, 1]` — Mutz status-threat level
  - `faction: str | None` — diagnostic faction label
  - `faction_center: np.ndarray[2] | None` — FactionAnchor target
  - `identity_weight_override: float | None` — X4 prime override
  - `identity_prime_expires_at: int | None` — expiry tick for X4

### 2.3 Environment (`abm/core/environment.py`)
Shared per-tick state:

- `parties: dict[party_id → np.ndarray[2]]` — current party centroids
- `outlets: list[MediaOutlet]` — media outlets in the scenario
- `tick: int`
- `attrs: dict` — scenario-level knobs (e.g.
  `party_issue_coupling`, `tier_d_anes_knobs`, etc.)

### 2.4 Network (`abm/core/network.py`)
Edges have `cooperative: bool` and optional `involuntary: bool` flags
(Phase 8c §2). Neighbour iteration is network-mediated, not radius-
mediated: agents influence each other through edges, not proximity.

---

## 3. Rules catalogue

All rules live in `abm/rules/`. Each is a class with `__init__`
parameters (the knobs) and an `apply` method called per agent (or
per environment) per tick. The pillar bundles them into stages; the
historical arc bundles them into the master `build_engine` pipeline.

### 3.1 `BoundedConfidenceInfluence` (`influence.py`)
Hegselmann-Krause-style influence: average toward neighbours within
ideology distance `ε`. Network-mediated.

| Knob | Default | Type | Range | Notes |
|---|---|---|---|---|
| `epsilon` | 0.3 | float | [0, 2] | Confidence radius. Per-agent override via `attrs["epsilon"]`. |
| `strength` | 0.1 | float | [0, 0.5] | Per-tick averaging strength. 0 = inert. |
| `temperature` | 0.0 | float | [0, 1] | >0 enables graded logistic filter (Phase 4 F2). 0 = canonical hard-cutoff HK. |
| `affect_weight` | 0.0 | float | [0, 1] | Per-neighbour affect modulator (Phase 5). Only active with `temperature > 0`. |

**Historical-arc:** strength = 0.08 (overridable via
`tier_c_bc_strength`).

### 3.2 `PartyPull` (`party_pull.py`)
Pulls each partisan agent toward their `party_cue` (per-agent target;
falls back to env centroid).

| Knob | Default | Type | Range | Notes |
|---|---|---|---|---|
| `strength` | 0.05 | float | [0, 0.5] | Per-tick pull magnitude. 0 = inert. |

**Historical-arc:** strength = 0.07 (overridable via
`tier_c_party_pull_strength`).

### 3.3 `MediaConsumption` (`media_consumption.py`)
Pulls each agent toward the centroid of their `media_diet` (weighted
average of outlet positions).

| Knob | Default | Type | Range | Notes |
|---|---|---|---|---|
| `strength` | 0.04 | float | [0, 0.5] | Per-tick pull magnitude. 0 = inert. |

### 3.4 `AffectiveUpdate` (`affective_update.py`)
Per-encounter out-party warmth update. Out-party encounters cool
(negative valence proportional to issue distance + identity weight);
in-party encounters warm modestly (baseline).

| Knob | Default | Type | Range | Notes |
|---|---|---|---|---|
| `radius` | 1.5 | float | [0.1, 5] | Issue-distance normalisation scale (`d / radius`). |
| `learning_rate` | 0.01 | float | [0, 0.1] | Per-encounter step. Per-agent override via `attrs["learning_rate"]`. |
| `identity_weight` | 0.5 | float | [0, 1] | Weight on identity term in valence. Per-agent override via `attrs["identity_weight_override"]` (X4). |
| `baseline` | 0.10 | float | [0, 1] | Floor that ensures negative valence for out-party at proximity 0. |
| `cooperative_mute` | 0.5 | float | [0, 1] | Pettigrew-Tropp mute on negative valence under full cooperative share. |
| `coop_positive_threshold` | -0.2 | float | [-1, 1] | Warmth floor at which cooperative encounters can warm rather than mute. |
| `coop_positive_magnitude` | 0.05 | float | [0, 0.5] | Per-encounter positive nudge under cooperative-warming path. |
| `threat_amplification` | 1.0 | float | [1, 5] | Mutz 2018 threat multiplier on negative valence. |
| `saturation` | 0.0 | float | [0, 5] | **Phase 9 G.** Soft cap: per-step scaled by `max(0, 1 − sat·w²)`. 1.0 ≈ Iyengar saturation curve. |

**Historical-arc with ANES knobs:** saturation = 1.0 — **but under the
affect re-grade (`evidence_regrade`, 2026-06) saturation = 0.0** (it was
fit to the pre-re-grade too-cold bands; it decelerated the late collapse
the grounded bands want). The arc also drops `learning_rate` base 0.01 →
0.003 and seeds 1980 affect at −0.09 (was −0.25) under `evidence_regrade`.

### 3.4b `MediatedAnimus` (`mediated_animus.py`)
Contact-INDEPENDENT (parasocial) out-party animus — the affect re-grade
channel. Each tick a partisan agent cools its out-party warmth by
`-lr · mediated_animus_weight · identity_alignment`, with no network
neighbour required (Mason 2018 mega-identity + partisan media). Supplies
the convex late steepening that the contact-gated `AffectiveUpdate` can't,
because homophilous sorting starves out-party contact.

| Knob | Default | Type | Range | Notes |
|---|---|---|---|---|
| `learning_rate` | 0.0 | float | [0, 0.1] | Channel magnitude. 0 → exact no-op (pillar/non-arc bit-identical). Arc: 0.014 under `evidence_regrade`. |

Env-driven: `env.attrs["mediated_animus_weight"]` (default 0.0; ramped
0.50/0.80/1.00 at the 2008/2010/2012 social-media events under
`evidence_regrade`). Reads `agent.attrs["identity_alignment"]`. No
saturation by design — it must keep biting once contact has starved.

### 3.5 `GaussianNoise` (`noise.py`)
Per-tick i.i.d. position jitter + Friedkin-Johnsen anchor damping.

| Knob | Default | Type | Range | Notes |
|---|---|---|---|---|
| `sigma` | 0.01 | float | [0, 0.5] | x-axis (or isotropic) σ. |
| `sigma_y` | None | float \| None | [0, 0.5] | **Phase 9 §11.4.** Per-axis σ_y. None = isotropic. |
| `rho` | 0.0 | float | [-1, 1] | **Phase 9 §11.7-D5.** Cross-axis correlation via Cholesky. 0 = independent. |

Per-tick FJ damping: `+FJ_ALPHA * stubbornness * (anchor - position)`.
FJ_ALPHA = 0.05 (in `abm/calibration.py`).

**Historical-arc with ANES knobs:** sigma_x = sigma_y = 0.08, rho = 0
(noise rho); the cue rho lives elsewhere (see §3.13).

### 3.6 `EliteDrift` (`elite_drift.py`)
Per-tick drift of party centroids outward. Models DW-NOMINATE
elite divergence.

| Knob | Default | Type | Range | Notes |
|---|---|---|---|---|
| `rate` | 0.0005 | float | [0, 0.05] | Per-tick magnitude (x-axis if `rate_y` set, else isotropic). |
| `rate_y` | None | float \| None | [0, 0.05] | **Phase 9 §11.7-D3.** Per-axis y rate. None = isotropic. |
| `asymmetric` | None | dict[int,float] \| None | each [0, 5] | `{party_id: multiplier}` for asymmetric drift. |

**Historical-arc with ANES knobs:** rate driven by per-decade
schedule `ELITE_DRIFT_SCHEDULE_ANES`, rate_y by
`ELITE_DRIFT_SCHEDULE_ANES_Y`, asymmetric by
`ELITE_DRIFT_ASYMMETRIC_ANES_SCHEDULE`. All multiplied by
`tier_d_anes_drift_multiplier` (default 3.0 under `anes_full`).

### 3.7 `IdentitySorting` (`identity_sorting.py`)
Per-tick probabilistic update of the 3-dim `identities` vector
toward in-party / away-from-out-party.

| Knob | Default | Type | Range | Notes |
|---|---|---|---|---|
| `sort_rate` | 0.02 | float | [0, 1] | Per-tick fire probability per agent. |
| `step` | 0.05 | float | [0, 0.5] | Magnitude of identity-component update. |
| `differentiation` | 0.5 | float | [0, 1] | Weight on "differentiate from out-party" component. |

**Historical-arc:** sort_rate driven by `IDENTITY_SORTING_SCHEDULE`
(0.02 at 1980 → 0.045 at 2020). **Honesty relabel (MHV T0.2):** with all
schedules frozen at 1980 values, only ~17% of the arc's alignment rise
remains — treat the alignment trajectory as schedule-carried, not
emergent (methods.md §5.13).

### 3.8 `IdentityToIdeologyPull` (`identity_to_position.py`) — Phase 9 new
Mason 2018 mega-identity → ideology coupling. Per tick, pulls
position toward `mean(identities)` per-axis, scaled by env's
`party_issue_coupling`.

| Knob | Default | Type | Range | Notes |
|---|---|---|---|---|
| `strength_x` | 0.0 | float | [0, 0.2] | Per-axis x coupling. 0 = no-op. |
| `strength_y` | 0.0 | float | [0, 0.2] | Per-axis y coupling. 0 = no-op. |

Pull is also scaled by `(1 - stubbornness)` (FJ).

**Historical-arc with ANES knobs:** strength_x = 0.020,
strength_y = 0.040.

### 3.9 `PerceptionUpdate` (`perception_update.py`)
Per-tick correction of `perceived_other_party` toward observed
neighbour positions.

| Knob | Default | Type | Range | Notes |
|---|---|---|---|---|
| `correction_rate` | 0.01 | float | [0, 0.5] | Per-tick correction magnitude. 0 = inert. |

### 3.10 `BacklashRepulsion` (`repulsion.py`)
Affect-gated Macy-Flache repulsion from cold out-party neighbours.

| Knob | Default | Type | Range | Notes |
|---|---|---|---|---|
| `epsilon` | 0.3 | float | [0, 2] | BC ε threshold for repulsion to fire. |
| `max_range` | 1.5 | float | [0, 3] | Outer cutoff. |
| `strength` | 0.05 | float | [0, 0.5] | Per-encounter repulsion magnitude. 0 = inert. |
| `affect_threshold` | -0.3 | float | [-1, 1] | Cold-only gate (only fires when warmth ≤ threshold). +inf disables gate. |
| `threat_amplification` | 1.0 | float | [1, 5] | Mutz threat multiplier. |
| `asymmetric` | None | dict[int,float] \| None | each [0, 5] | Per-party rate multiplier (X1). |

### 3.11 `TieRewiring` (`tie_rewiring.py`)
Per-tick rewiring of voluntary edges by ideology/affect homophily.

| Knob | Default | Type | Range | Notes |
|---|---|---|---|---|
| `rewire_rate` | 0.05 | float | [0, 1] | Per-tick edge churn rate. |
| `homophily_radius` | 0.5 | float | [0, 2] | Ideology-distance preference. |
| `affect_bias` | 0.5 | float | [0, 2] | Weight on affect-warmth in rewire choice. |

**Pillar S4** uses tighter values; historical arc inherits the pillar's.

### 3.12 `FactionAnchor` (`faction_anchor.py`) — Phase 9 Tier C
Per-agent pull toward `attrs["faction_center"]`. Inert when no
`faction_center` is set (i.e., at t=0 and in the pillar, where the
attr is never tagged).

| Knob | Default | Type | Range | Notes |
|---|---|---|---|---|
| `strength` | 0.04 | float | [0, 0.5] | Per-tick magnitude when faction_center is set. |

**Historical-arc with ANES knobs:** strength = 0.10. Fires on
agents tagged by emergence events (Tea Party, MAGA, Bernie, DSA).

### 3.13 `CohortReplacement` (`cohort_replacement.py`)
Per-tick stochastic replacement of agents (cohort turnover). New
agent's position, party_cue, affect, identities are drawn from the
active cohort's distributions.

| Knob | Default | Type | Range | Notes |
|---|---|---|---|---|
| `replacement_rate` | 0.0 | float | [0, 0.01] | Per-tick replacement rate. 0 = inert. |

**Historical-arc:** rate = 0.003 (~1%/yr at 3 ticks/yr).
Under `tier_d_anes_knobs`, replacement draws position from
`N(party_centroid, σ_anchor=0.30)` and party_cue σ from
`PARTY_CUE_SIGMA_HISTORICAL_ANES`.

### 3.14 `ArgumentExchange`, `MediaShock`, `ResidentialMigration`, `ThreatDecay`, `IdentityPrimeExpiry`
Supporting rules for specific scenario mechanics. Defaults preserve
no-op for paths that don't seed the relevant attrs.

| Rule | Key knob | Default | Range | Used by |
|---|---|---|---|---|
| `ArgumentExchange` | `homophily_radius` | 0.3 | [0, 2] | (not in current pillar / arc pipelines) |
| `MediaShock` | `magnitude` | varies | [0, 1] | One-shot events |
| `ResidentialMigration` | rate | 0.02 | [0, 0.2] | Historical-arc (default 0.02) |
| `ThreatDecay` | `decay_rate` | 0.05 | [0, 0.5] | After 2016 status-threat spike |
| `IdentityPrimeExpiry` | n/a | n/a | n/a | Reverts `identity_weight_override` after X4 |

### 3.15 `IdentityAlignment` (`identity_alignment.py`) — Step 1 (web_demo re-grade)
Maintains an explicit per-agent `identity_alignment ∈ [0,1]` (Mason 2018
mega-identity stacking): how strongly an agent's `identities` point in its
own party's canonical direction. Relaxes toward the identity-derived target
each tick so the state accretes. `AffectiveUpdate` reads it to amplify
out-party animus for stacked agents. **Self-gates on
`env.attrs["evidence_regrade"]` — returns an empty delta WITHOUT drawing
rng when off, so the default path is bit-identical** (rule present but
inert). In the historical-arc pipeline only. **MHV S2 T2.4: on the
emergent-constraint path (`constraint_rate > 0`) this rule is retired —
`identity_alignment` is a measured readout there (`MeasuredAlignment`; see
the MHV S2 paragraphs at the end of §5, and methods §5.21); everything in
this section describes the legacy path.**

| Rule | Key knob | Default | Range | Used by |
|---|---|---|---|---|
| `IdentityAlignment` | `rate` | 0.10 | [0, 1] | Historical-arc when `evidence_regrade=True` |

**Step-2 flag-1 fix (alignment must RISE per Mason).** As shipped in
Step 1, aggregate `identity_alignment` came out flat-to-declining
(~0.21→0.16) because (a) `IdentitySorting` was far too slow to stack
identities and (b) `CohortReplacement` reseeded new arrivals' identities
to a static ~0 base, dragging the mean down. Step 2 fixes both,
**regrade-gated** (default path bit-identical):

| Constant (`historical_arc.py`) | Default | Regrade | Effect |
|---|---|---|---|
| `IDENTITY_SORTING_REGRADE_MULTIPLIER` | 1.0 | **5.0** | scales `IdentitySorting.sort_rate` (frequency) |
| `IDENTITY_SORTING_REGRADE_STEP` | 0.05 | **0.15** | per-update identity step (the real rate-limiter) |

Plus `cohort_replacement.py` anchors new arrivals' identities to the
**contemporary same-party identity mean** (rises with the sort) instead
of the static ~0 cohort base — the identity-side twin of the Phase-9
§11.7-D position fix. Net: alignment now rises ~0.22→0.42 (monotone,
≈doubling) while affect stays in the ANES envelope and party_sep moves
*toward* the ANES 1.04+ target. Landed values from a joint-constraint
sweep; see [`results/phase10_results.md`](results/phase10_results.md).

### 3.16 R-phase knobs (reversibility / audit-fix; methods §5.32)

The R-phase added gated knobs to existing rules + one new rule. All default to a
no-op (bit-identical when off). The shipped canonical (`ANES_FULL_RPHASE_KWARGS`)
turns on the **corrections** + R8; the strong restoring forces (R2/R3/R4/R6) stay
off — they are the depolarization *capacity* proven in the G1 generic battery
(`validation/audit/layer1_battery.py`), not shipped brakes.

| Knob (build kwarg) | Rule | Effect | Shipped value |
|---|---|---|---|
| `media_centrifugal` | `diet_for_party` (R5) | sharpens partisan diet onto same-pole outlets → media centrifugal (audit F6 fix) | **0.7** |
| `affect_rest_rate` / `affect_rest_anchor` | `AffectiveUpdate` (R7) | mean-reversion → affect equilibrium (fixes cool-to-floor) | **0.02 / −0.30** |
| `affect_lr_scale` | `_per_agent_heterogeneity` (P3a) | scales per-agent affect cooling rate + its clip floor | **0.30** |
| `affect_saturation` | `AffectiveUpdate` (P3a) | override soft-saturation shape (re-enabled under regrade) | **1.0** |
| `contact_warming` + `contact_coop_frac` / `contact_warm_threshold` / `contact_warm_magnitude` / `contact_coop_share` | `mark_cross_party_cooperative` + `AffectiveUpdate` (R1) | seed cooperative cross-party edges → wake the warming path | **on / 0.3 / −0.6 / 0.04 / 0.15** |
| `endo_mob_gain` | `ActivistEliteCue` (R8) | endogenous self-mobilization (sorting feeds mobilization; the spiral) → emergent fraction 0.28→0.34 (cap ~0.39) | **0.15** |
| `xpressure_sorting_damp` / `xpressure_affect_damp` | `PartyPull`+`ConstraintOp` / `AffectiveUpdate` (R2) | cross-pressure damping (capacity) | off (0.0) |
| `bridge_rewire` | `TieRewiring` (R3) | cross-cutting bridge tie formation (capacity) | off (0.0) |
| `bc_affect_weight_floor` | `BoundedConfidenceInfluence` (R4) | warmth re-opens cross-party BC convergence (capacity) | off (0.0) |
| `thermostatic_gain` / `thermostatic_reference` | `ThermostaticFeedback` (R6, new env rule) | two-signed feedback on party-sep overshoot (capacity) | off (0.0) |

---

## 4. Historical-arc parameter constants

Module-level constants in `abm/pillars/historical_arc.py`. These are
**not** runtime knobs — they're the calibrated values that the
schedules consult. They're documented here so an intervention or viz
designer knows what's load-bearing.

### 4.1 Party centroids (1980 IC)
| Constant | Value | Notes |
|---|---|---|
| `PARTY_CENTERS_1980` | `{0: (-0.30, -0.08), 1: (+0.30, +0.08)}` | Legacy (Phase 8). |
| `PARTY_CENTERS_1980_TIER_D` | `{0: (-0.30, -0.20), 1: (+0.30, +0.20)}` | Tier D. |
| `PARTY_CENTERS_PRE_REAGAN_ANES` | `{0: (-0.05, +0.05), 1: (+0.18, +0.10)}` | **ANES.** Tick 0 IC. |
| `PARTY_CENTERS_1986_ANES` | `{0: (-0.13, -0.02), 1: (+0.20, +0.18)}` | **ANES.** Tick 21 IC. |

### 4.2 Party cue σ
| Constant | Value | Notes |
|---|---|---|
| `PARTY_CUE_SIGMA_HISTORICAL` | `{0: 0.22, 1: 0.30}` | Legacy. |
| `PARTY_CUE_SIGMA_HISTORICAL_ANES` | `{0: 0.672, 1: 0.912}` | **ANES.** MHV T0.1: the old `tier_d_anes_sigma_pc_multiplier=1.6` is folded in (values are `0.42*1.6` / `0.57*1.6`, bit-identical). Note σ_pc is a weak lever — within-party spread is dominated by `noise_sigma` (internal audit notes, `docs/internal/calibration_interpretation.md` §2.2). |

### 4.3 Party-assignment sigmoid K (logit slope)
| Constant | Value | Notes |
|---|---|---|
| `PARTY_ASSIGNMENT_K` | Per-decade: 1.5 → 4.5 | Legacy — live only on the non-ANES sigmoid path. |
| ~~`PARTY_ASSIGNMENT_K_ANES`~~ | *(retired, MHV T0.1)* | Was dead code in the shipped config: under ANES knobs party is pre-committed (§11.7-D6) and cohort replacement uses the centroid-anchor draw, so the K-sigmoid never ran (100× swing = exactly-zero battery change). The sorting-sharpness lever is **`tier_d_ic_sigma`** (σ_ic), not K. See the internal audit notes (`docs/internal/calibration_interpretation.md` §2.1). |

### 4.4 Elite drift schedule
| Constant | Value | Notes |
|---|---|---|
| `ELITE_DRIFT_SCHEDULE` | per-decade rates 0.003-0.008 | Legacy. |
| `ELITE_DRIFT_SCHEDULE_ANES` | per-decade rates ~ANES centroid velocities | x-axis. |
| `ELITE_DRIFT_SCHEDULE_ANES_Y` | 1.3 × x-rate per decade | y-axis (cult sort > econ sort). **MED / N (MHV T0.2):** anchored to ANES *voter*-centroid velocities — a declared proxy, not a legislator series (NOMINATE dim-2 is not a clean cultural axis). The x-anchor stays L/HIGH. |
| `ELITE_DRIFT_ASYMMETRIC` | `{0: 0.5, 1: 1.5}` (constant) | Legacy. |
| `ELITE_DRIFT_ASYMMETRIC_ANES_SCHEDULE` | Per-decade: 1980 `{D:0.5, R:1.5}`, balanced 1990-2010, 2010 `{D:1.5, R:0.5}` | **ANES.** Reagan-era R-heavy → modern D-heavy cult sort. |

### 4.5 Identity sorting schedule
| Constant | Value | Notes |
|---|---|---|
| `IDENTITY_SORTING_SCHEDULE` | 1980: 0.02, 1990: 0.025, 2000: 0.03, 2010: 0.04, 2020: 0.045 | Direction per Mason 2018; the *values* are tuned (**N**). Carries ~83% of the arc's alignment rise (methods.md §5.13) — an S2 retirement target per the MHV plan. |

### 4.6 Party-issue coupling schedule
| Constant | Value | Notes |
|---|---|---|
| `PARTY_ISSUE_COUPLING_SCHEDULE` | 1980: 0.40 → 2020: 1.10 | Multiplier on `IdentityToIdeologyPull`. |

### 4.7 Perception bias (X7 target)
| Constant | Value | Notes |
|---|---|---|
| `PERCEPTION_EXTREME_BIAS` | 0.25 (x only) | Legacy (Phase 7). |
| `PERCEPTION_EXTREME_BIAS_X_TIER_D` | 0.20 | Tier D x. |
| `PERCEPTION_EXTREME_BIAS_Y_TIER_D` | 0.25 | Tier D y (new). |

### 4.8 Faction stubbornness
| Constant | Value | Notes |
|---|---|---|
| `FACTION_STUBBORNNESS_BOOST` | 0.5 | Added to stubbornness for tagged faction agents. |
| `FACTION_STUBBORNNESS_CAP` | 0.90 | Upper bound after boost. |

### 4.9 Tick layout
| Decade | Boundary tick | ANES snapshot tick |
|---|---|---|
| 1980 | 0 | 21 (≈1987) |
| 1990 | 30 | 42 (1994) |
| 2000 | 60 | 72 (2004) |
| 2010 | 90 | 102 (2014) |
| 2020 | 120 | 126 (2022) |
| 2025 | 135 | 135 |

The bucket-centered snapshot ticks are what `phase9_anes_score.py`
reads. Decade-boundary ticks are when `IdentitySorting` rates step.

---

## 5. `build_engine` kwargs (historical-arc public surface)

`abm/pillars/historical_arc.py::build_engine(...)`. Defaults
preserve pre-Phase-9 behavior bit-identically; the ANES-recalibrated
preset is `phase9_anes_score.PRESETS["anes_full"]`.

### 5.1 Population structure
| Kwarg | Default | anes_full | Range | Notes |
|---|---|---|---|---|
| `seed` | 0 | 0..8 | int | RNG seed |
| `n_agents` | 250 | 250 | [50, 5000] | Population size |
| `independent_fraction` | 0.0 | 0.12 | [0, 0.4] | Klar & Krupnikov 2016 "pure indep" share |
| `phase8e_baseline` | False | False | bool | Phase 8e baseline mode |

### 5.2 Faction seeding (Tier A — abandoned path, still available)
| Kwarg | Default | anes_full | Notes |
|---|---|---|---|
| `factional_seeding` | False | False | Tier A. False under `anes_full`. |
| `faction_stubbornness_boost` | 0.5 | 0.5 | When Tier A on. |
| `faction_center_scale` | 1.0 | 1.0 | When Tier A on. |
| `faction_sigma_within` | 0.05 | 0.05 | When Tier A on. |

### 5.3 Faction-emergence events (Tier C)
| Kwarg | Default | anes_full | Notes |
|---|---|---|---|
| `faction_anchor_strength` | 0.04 | 0.10 | `FactionAnchor` per-tick pull |
| `faction_anchor_events` | True | True | Whether to fire Tea Party / MAGA / Bernie / DSA events |
| `event_stubbornness_bump_multiplier` | 1.0 | 1.0 | Multiplier on per-event stubbornness boost |

### 5.4 Tier D master & ablation
| Kwarg | Default | anes_full | Notes |
|---|---|---|---|
| `tier_d_axis_balance` | False | True | **Master Tier D flag.** Gates everything below. |
| `tier_d_party_center_y` | 0.20 | 0.20 (ignored — ANES centers used) | Lever 2 magnitude |
| `tier_d_coupling_rho` | 0.20 | 0.30 | Lever 3 IC side-draw cross-axis correlation |
| `tier_d_lever1_off` | False | True | Diagnostic ablation — Lever 1 (sigmoid `0.55·x + 0.45·y`) off |
| `tier_d_lever4_off` | False | False | Lever 4 ablation (perception y-bias) |
| `tier_d_lever6_off` | False | False | Lever 6 ablation (Trump 2016 y-nudge) |
| `tier_d_party_cue_sigma_y_mult` | 1.0 | 1.0 | Variance-preserving x/y σ_pc split |
| `tier_d_aniso_noise_sigma_x` | None | 0.08 | **Phase 9 §11.7.** Per-axis x noise σ. |
| `tier_d_aniso_noise_sigma_y` | None | 0.08 | **Phase 9 §11.4.** Per-axis y noise σ. |
| `tier_d_cohort_y_signs_fix` | False | True | **Phase 9 §11.6.** Fixes cohort y_mean sign bug. |

### 5.5 ANES master switch (Phase 9 §11.7-B)
| Kwarg | Default | anes_full | Notes |
|---|---|---|---|
| `tier_d_anes_knobs` | False | True | **ANES recalibration master switch.** When True, swaps the historical constants for `_ANES` variants. Only consulted if `tier_d_axis_balance=True`. |
| `tier_d_anes_drift_multiplier` | 1.0 | 3.0 | Multiplier on `ELITE_DRIFT_SCHEDULE_ANES` |
| `tier_d_anes_sigma_pc_multiplier` | 1.0 | *(removed)* | **DEPRECATED no-op (MHV T0.1).** Accepted for compatibility; any non-1.0 value warns and is ignored — the shipped 1.6 is folded into `PARTY_CUE_SIGMA_HISTORICAL_ANES`. Within-party-spread lever: `tier_d_aniso_noise_sigma_x/y`. |

### 5.6 New rules (Phase 9 §11.7-C onward)
| Kwarg | Default | anes_full | Notes |
|---|---|---|---|
| `tier_c_identity_pull_x` | 0.0 | 0.020 | `IdentityToIdeologyPull.strength_x` |
| `tier_c_identity_pull_y` | 0.0 | 0.040 | `IdentityToIdeologyPull.strength_y` |
| `tier_c_party_pull_strength` | None | 0.04 | Overrides historical PartyPull strength (0.07) |
| `tier_c_bc_strength` | None | 0.015 | Overrides historical BC strength (0.08) |

### 5.7 ANES-derived shape knobs
| Kwarg | Default | anes_full | Notes |
|---|---|---|---|
| `tier_d_ic_sigma` | None | 0.35 | IC position σ (overrides hardcoded 0.45). **The sorting-sharpness knob** under the ANES path: party↔position tightness = σ_ic + centroid separation (MHV T0.1; the K-sigmoid is not in this loop). |
| `tier_d_cue_correlation` | 0.0 | 0.40 | Cue draw (party_cue + media_cue) x-y correlation |

### 5.8 Step-1 evidence re-grade master gate
| Kwarg | Default | anes_full | Notes |
|---|---|---|---|
| `evidence_regrade` | False | **True** | Master gate for the Step-1 truth-pass (Gingrich/CU re-attribution, social-media demotion, identity-alignment → affect). `False` is a strict no-op → default path bit-identical. Pair with `build_schedule(evidence_regrade=...)`. See §7.1. |

### 5.8-bis Demo-physics knobs — T0.4 adjudication (MHV, 2026-06)

The three "web_demo jumpiness/realism" knobs were adjudicated per-knob
(mechanism-with-provenance vs presentation-side; user sign-off 2026-06-10):

| Kwarg | Default | anes_full | Verdict |
|---|---|---|---|
| `momentum` | 0.0 | *(removed — was 0.4)* | **RELOCATED to presentation** (`scripts/repack_web_demo.py` display EMA, β=0.6, reset at replacement splices). It was a display-smoothness knob, not a mechanism; the engine kwarg stays accepted (0.0 = off). |
| `fj_alpha_scale` | 1.0 | 2.8 | **KEPT as mechanism.** L (Friedkin–Johnsen anchoring) / E (the 1–2% lifetime-big-mover target from panel stability — Converse 1964; Green, Palmquist & Schickler) / N (the 2.8 value). Note: α=0.14 sits outside the §5.4 no-collapse sweep (0.02–0.10) — sweep extension queued at T0.6. |
| `tier_d_ic_partisan_x_cap` (+ new `tier_d_ic_wrongside_tail_target`) | None | 0.45 + `{0: 0.0376, 1: 0.0160}` | **RECALIBRATED.** The hard cap forced the wrong-side 1980 econ tail to 0%, but ANES 1980–1990 shows a real tail (D 3.76% / R 1.60% past ±0.45, weighted). The cap is now a *soft* cap: beyond-cap draws kept with analytic probability target/P_gauss(beyond) — L (the rates) / N (the thinning operator). Slated for retirement at MHV S2 (the IC rebuild must reproduce the tail natively). |

Re-bless on the new substrate: ANES scorecard improved 15/24 → **20/24**;
phase10 buckets re-measured (see `docs/results/phase10_results.md`).

### 5.9 Web-demo sandbox dials (illustrative — not a finding)
Hooks for the web demo's interactive sandbox (`scripts/build_sandbox_data.py`).
All default to an exact no-op (`×1.0` / `0.0` / `None`, all exact in IEEE-754),
so the default/pillar/test path stays **bit-identical** (verified to 10 dp). The
sandbox cranks these *past* the calibration envelope — illustrative only, not
measured, not re-blessed (provenance **E**/**N**).

**v2 knob set (audit 2026-06; `docs/intervention_knob_audit.md`).** The five
sandbox dials were rebuilt so every knob is a *cause* (a thing you set) and the
polarization metrics are *readouts* (separation, out-party animus, within-party
spread, mega-identity alignment). The old `animus`/`echo` dials were demoted to
readouts — they were outcome metrics, and `echo` reliably moved warmth the wrong
way. Each surviving knob is sign-stable at every position of the other four
(12/12 in the audit's robustness screen).

| Sandbox knob | build_engine kwarg(s) | Default | Drives | Readout it owns |
|---|---|---|---|---|
| **Mega-identity** | `sandbox_identity_mult` | 1.0 | `IdentitySorting` (sort_rate+step), `identity_sorting_multiplier`, `IdentityAlignment.rate` | mega-identity alignment |
| **Elite extremism** | `tier_d_anes_drift_multiplier` (§5.5) | 1.0 (3.0 arc) | `EliteDrift` per-decade rate | party separation |
| **Open-mindedness** | `tier_c_bc_epsilon` (+ `tier_c_bc_strength`, §5.6) | None | BC confidence radius ε (via `env.attrs["bc_epsilon_scale"]`, applied at apply-time in `BoundedConfidenceInfluence`) co-scaled with influence strength | separation ↓ / warmth ↑ |
| **Contact & mixing** | `sandbox_contact` | 0.0 | population-wide cooperative-share floor (`env.attrs["sandbox_contact_share"]`, read by `AffectiveUpdate`; Pettigrew-Tropp) | out-party animus ↓ |
| **Within-party diversity** | `sandbox_diversity` | None | `GaussianNoise` σ on both axes (overrides `tier_d_aniso_noise_sigma_x/y`) | within-party spread |

New no-op-by-default kwargs added for v2: `tier_c_bc_epsilon` (None → ε scale
1.0), `sandbox_contact` (0.0), `sandbox_diversity` (None). The old
`sandbox_animus_mult` / `sandbox_rewire_mult` kwargs remain in the signature
(still default-1.0 no-ops) but are no longer wired to a sandbox dial.

**MHV S2 (T2.1/T2.2): `n_issues`** (default None → no-op). When set, the
position substrate becomes a D-dim `issues` vector (attrs `issues`) seeded
from the frozen ANES loadings file (`data/mhv/issue_loadings.json`; kernels
in `abm/core/issues.py`) and `ideology` becomes its cached block-means
projection — the BC / PartyPull / Media / Noise / FJ-anchor / Backlash
kernels run natively in issue space (RMS distance `‖Δv‖·√(2/D)`), legacy
emitters are lifted at the apply site. Valid values: **7** (the real-data
ANES battery — the live S2 IC with native wrong-side tails; T0.4's soft cap
is bypassed on this path) and **2** (the I1 reduction: trajectory
bit-identical to the plain 2D run, pinned by test). Not compatible with
`momentum` (retired). **Canonical as of MHV T2.6:** `ANES_FULL_KWARGS`
ships `n_issues=7` + `constraint_rate=0.02` + `constraint_resid_sigma=0.01`
+ the BC wake (ε 0.40 / strength 0.03); the soft-cap kwargs are retired
from the preset (legacy 2D path only). methods.md §5.18–5.19, §5.23.

**MHV S2 (T2.3): `constraint_rate` + `constraint_resid_sigma`** (defaults
0.0 → strict no-op). `constraint_rate > 0` (requires `n_issues`) switches
the alignment spine from scheduled to **emergent**: `ConstraintOp`
(network-local consensus projection, `abm/rules/constraint_op.py`) replaces
`IdentitySorting`; `IDENTITY_SORTING_SCHEDULE`, the ×5 regrade multiplier,
and `PARTY_ISSUE_COUPLING_SCHEDULE` are retired on this path (coupling
pinned 1.0). `constraint_resid_sigma` is the within-block residual noise —
the dispersion counterweight (compass-invisible; zero at D=2). Prior center
0.02 / 0.01 (S4 fits); methods.md §5.20.

**MHV S2 (T2.4, M3-light), same path:** `identity_alignment` becomes a
**measured readout** — `MeasuredAlignment` (`abm/rules/measured_alignment.py`)
replaces the `IdentityAlignment` relaxation; the formula (geometric mean of
identity stacking × issue-package stacking along the frozen 1986 party-gap
axis) is pinned by `tests/test_t24_measured_alignment.py`. The dyadic
identity-distance valence term retires (`AffectiveUpdate.identity_weight`
built at 0.0; identity reaches affect only through the measured alignment,
read by `align_factor` + `MediatedAnimus` unchanged). `IDENTITY_ALIGNMENT`
shocks raise on this path; X1's `identity_weight` lever is skipped (S4
re-mechanization item); `sandbox_identity_mult` is inert here (a
measurement is not a force — S5 dial re-map pending). methods.md §5.21.

**MHV S3 (T3.2/T3.3): `data_fed_elite` + `data_fed_media`** (defaults False →
bit-identical). The forces-as-inputs flip — exogenous forces become typed,
data-fed **input series** (`abm/pillars/inputs.py`) instead of schedules:
- `data_fed_elite=True` replaces the scheduled `EliteDrift` with a
  `PartyCentroidSeries` that sets `env.attrs["parties"][pid]` each tick from the
  ANES voter-centroid series (`data/mhv/party_centroid_series.json`). The
  `ELITE_DRIFT_SCHEDULE*` / Gingrich / Citizens-United rate writes become natural
  no-ops; the Trump-2016 centroid nudge is skipped (series carries it). **Removes
  the corner-pin** (scheduled EliteDrift pinned the attractor at `[±1,±1]` by
  2014); the de-artifacted party_sep is lower (~0.59 vs the artifact 0.94) and
  undershoots the ANES target pending the S4 fit.
- `data_fed_media=True` adds a `MediaPenetrationSeries` writing
  `env.attrs["media_strength"]` and `["bc_affect_weight"]` from the penetration
  series (`data/mhv/media_penetration_series.json`); `MediaConsumption` and
  `BoundedConfidenceInfluence` read those env slots with a fallback to their own
  value. Faithful, near-trajectory-neutral re-expression of the FD/Fox/social
  step events.

Both are **ON in the canonical `ANES_FULL_KWARGS`** as of T3.5. The retired
schedules (`ELITE_DRIFT_SCHEDULE*`) stay live for the legacy non-data-fed path
(kill candidates post-S4). I3 (`tests/test_i3_no_outcome_writes.py`) now forbids
direct outcome writes in arc handlers; the Obama-2008 warmth bump was dropped.
methods.md §5.24.

---

## 6. Interventions library (X1–X7)

In `abm/pillars/interventions_phase6.py`. Each is an `Intervention`
dataclass with a `param_bundle` (tuple of `(rule_class, attr, value)`
overrides) and an optional `setup` function (one-shot mutation of
engine state at intervention time).

| ID | Label | Mechanism | Key parameters | Current bucket (issue / affect) |
|---|---|---|---|---|
| **X1** | "Show people the other side" | Asymmetric `BacklashRepulsion` | `strength=0.05`, `asymmetric={0:0.7, 1:1.3}` | backfire / null |
| **X2** | "Fix the algorithm" | Zero `BoundedConfidenceInfluence.affect_weight` | `affect_weight=0` | null / null |
| **X3** | "Quit cable news" | Zero MSNBC + Fox weights in each agent's `media_diet` | setup-only | null / null |
| **X4** | "Bipartisan dialogue" | Levendusky 2021 identity prime: 20% of agents get `identity_weight_override=0.1` for 30 ticks | `X4_PRIME_SAMPLE_FRACTION=0.20`, `X4_PRIMED_IDENTITY_WEIGHT=0.1`, `X4_PRIME_DURATION_TICKS=30` | (to be re-measured) |
| **X5** | "Ranked-choice voting" | Halve both party centroids + each agent's `party_cue` | setup-only | partial / null |
| **X6** | "Shared neighborhoods" | Add 3 cross-party involuntary cooperative ties per agent + reset out-party affect to 0 | `X6_NEW_INVOLUNTARY_PER_AGENT=3` | (Phase 8c §2 re-bless) |
| **X7** | "Correct perception gap" | Reset every agent's `perceived_other_party` to actual centroid | setup-only | null / null (pillar); meaningful in arc |

**Phase 10 caveat.** All bucket labels above were last blessed on
the pre-Phase-9 engine. Re-validation on the ANES-recalibrated
engine is the next phase of work.

---

## 7. Event schedule (historical-arc)

`abm/pillars/historical_arc.py::build_schedule(...)`. All event ticks
1980-relative; `TICKS_PER_YEAR = 3.0`.

| Tick | Year | Event | Mechanism |
|---|---|---|---|
| 21 | 1987 | Fairness Doctrine repealed | Outlets get partisan-cable weight; reduces broadcast pull |
| 30 | 1990 | Decade boundary | `IdentitySorting.sort_rate` 0.02 → 0.025 |
| **42** | **1994** | **Gingrich elite-drift inflection** *(regrade only)* | **`EliteDrift.rate` step up, R-heavy `{0:0.5, 1:1.5}` — the elite-divergence inflection (Theriault; Hacker-Pierson). Added only when `evidence_regrade=True`.** |
| 48 | 1996 | Fox News launches | Add Fox outlet to diet pool |
| 60 | 2000 | Decade boundary | `sort_rate` 0.025 → 0.03 |
| 84 | 2008 | Obama warmth bump + social media ramp start | Affect bump for D-leaners; `affect_weight` ramp[0] (regrade: 0.02 vs default 0.10) |
| 87 | 2009 | Tea Party emergence | Tag 10% of Mainstream_Reps with sub-centroid (+0.58, +0.32) |
| 90 | 2010 | Decade boundary + Citizens United + ramp mid | `sort_rate` 0.03 → 0.04; `affect_weight` ramp[1]. **Regrade: CU sets NO drift (non-causal marker); the 2010-20 drift transition moves into the decade boundary.** |
| 96 | 2012 | Social media ramp end | `affect_weight` ramp[2] terminal (regrade: 0.05 vs default 0.30) |
| 105 | 2015 | MAGA emergence | Tag 13% Mainstream_Reps + 50% New_Right_Religious with (+0.60, +0.40) |
| 108 | 2016 | Trump election + status threat | Centroid nudge; `threat` set to 0.6 for ~60% of party=1; +stubbornness |
| 108 | 2016 | Bernie surge | Tag 8% of Mainstream_Dems with (-0.60, -0.40) |
| 114 | 2018 | Trump bump revert + DSA emergence | `sort_rate` reverts to 0.04; tag 5% of New_Left with (-0.75, -0.65) |
| 120 | 2020 | COVID + Jan 6 + decade boundary | One-shot affect spike; `sort_rate` 0.04 → 0.045 |
| 123 | 2021 | Affect revert | Affect spike decays |

### 7.1 Step-1 evidence re-grade (`evidence_regrade`)

The web/ANES presets (`scripts/anes_preset.ANES_FULL_KWARGS`) set
`evidence_regrade=True`, which re-grades the period shocks to the
literature (`docs/polarization_causal_model.md` §4.3). **Default `False`
is a strict no-op — the default-path schedule above is unchanged and
bit-identical.** When on:

- **Elite drift → Gingrich/1994 (D1a).** A discrete R-heavy
  `gingrich_1994` event (tick 42) is added; **Citizens United (tick 90)
  no longer sets the drift rate** (non-causal marker), and the 2010-20
  drift transition moves into `_decade_boundary_2010`. Net late-period
  divergence preserved; attribution corrected.
- **Social media demoted (D2a).** The `affect_weight` ramp the 2008/2010/
  2012 events apply is read from
  `env.attrs["social_media_affect_weight_schedule"]` — `[0.02, 0.04, 0.05]`
  under regrade (terminal ≈0.05, a small contested accelerant) vs the
  default `[0.10, 0.20, 0.30]`.
- **Identity stacking → affect (D3b).** An explicit per-agent
  `identity_alignment` state (rule `IdentityAlignment`, seeded at build)
  drives out-party animus: `AffectiveUpdate` amplifies negative valence by
  `1 + identity_alignment_affect_weight · alignment`
  (`identity_alignment_affect_weight = 0.5` under regrade, `0.0` default).
- **2016 status-threat** kept, graded contested (no mechanism change).
- **Step-2 flag-1 fix (alignment rises).** The cohort identity-reseed +
  faster identity sort (regrade-gated; see §3.15) make aggregate
  `identity_alignment` rise ~0.22→0.42 instead of flat-declining, so the
  D3b stacking→animus channel actually grows over the period per Mason.

---

## 8. Calibration & scoring entry-points

### 8.1 Score the engine against ANES
```bash
.venv/Scripts/python.exe scripts/phase9_anes_score.py
```
Runs the `anes_full` preset at 9 seeds, scores W₂ vs real ANES
clouds + §11 cells under both old and new bands. Writes
`docs/results/phase9_anes_score_anes_full.json`.

### 8.2 Rebuild ANES pointclouds from raw respondent CSV
```bash
.venv/Scripts/python.exe scripts/phase9_anes_target_builder.py
```
Reads `data/phase9_empirical/derived/respondent_coordinates.csv`,
weight-samples 1000 points per decade, builds Silverman KDEs, writes
`data/phase9_empirical/phase9_empirical_pointcloud_{decade}.npy` and
`_kde_{decade}.npy`. Re-run if respondent CSV is updated.

### 8.3 Rebuild empirical anchors JSON
```bash
.venv/Scripts/python.exe scripts/phase9_anes_knob_anchors.py
```
Emits per-decade ANES centroid stats, sigmoid K back-solve, centroid
velocities to `docs/results/phase9_anes_knob_anchors.json`. The
`PARTY_CENTERS_*_ANES` and `PARTY_CUE_SIGMA_HISTORICAL_ANES` constants in
`historical_arc.py` are pinned to this output (σ_pc now carries the folded
×1.6; the `sigmoid_K_anchors` output is historical — its consumer
`PARTY_ASSIGNMENT_K_ANES` was retired in MHV T0.1).

### 8.4 Side-by-side ANES vs sim plot
```bash
.venv/Scripts/python.exe scripts/phase9_sim_vs_anes_compass.py
```
Renders engine snapshots at the ANES bucket-centered ticks alongside
ANES respondent clouds.

### 8.5 Shape diagnostics (within-party covariance & axis angle)
```bash
.venv/Scripts/python.exe scripts/phase9_shape_diag.py
```
Compares ANES vs engine within-party eigenvalue ratios and principal
axis angles. Useful for verifying the diagonal tilt and elongation
of partisan clusters matches.

### 8.6 Activist sub-population diagnostics
```bash
.venv/Scripts/python.exe scripts/phase9_activist_diag.py
```
Counts post-2010 faction memberships per seed.

### 8.7 Calibration harness
`abm.calibration_phase9.aggregate(...)` — Wasserstein-2 scoring +
§11 cell-tally aggregator. Used by `phase9_anes_score.py` and any
new sweep scripts.

---

## 9. Discipline summary

1. **Pillar (`calm_to_camps.py`) is drift-guarded, not frozen.** New
   mechanisms default to no-op so the pillar tests stay green;
   deliberate rebuilds (e.g. MHV T2.5) re-bless the pinned tests
   honestly, with the measurement documented.
2. **All Phase 9 changes are gated.** `tier_d_axis_balance=False`
   and `tier_d_anes_knobs=False` reproduce pre-Phase-9 behavior.
3. **Anything outside `calm_to_camps.py` is in-scope for tuning.**
   Per-decade schedules in `historical_arc.py`, rule parameter
   ranges, outlet positions, IC σ — all available for intervention
   work.
4. **Interventions modify rule parameters or run setup hooks** —
   they do not rewrite rules. See §6.
5. **Default reproducibility.** Every per-seed run is deterministic.
   Parallel scoring uses `run_seeds_parallel` in
   `abm/calibration_parallel.py` (cap = `min(N_seeds, N_cores)`).
