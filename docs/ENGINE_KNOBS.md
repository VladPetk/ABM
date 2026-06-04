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
Five-stage canonical journey. Bit-identity locked: 73 sacred tests
defend it. **Do not touch this file** for new interventions or
recalibration work; new mechanisms must default to no-op for the
pillar path.

Stages: S0 baseline → S1 bounded confidence → S2 party identity →
S3 partisan media → S4 homophilous network. Each stage adds
mechanisms to the per-tick rule pipeline; positions and affects
carry over continuously.

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
(0.02 at 1980 → 0.045 at 2020).

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
inert). In the historical-arc pipeline only.

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
| `PARTY_CUE_SIGMA_HISTORICAL_ANES` | `{0: 0.42, 1: 0.57}` | **ANES.** Multiplied by `tier_d_anes_sigma_pc_multiplier` (default 1.6 under `anes_full`). |

### 4.3 Party-assignment sigmoid K (logit slope)
| Constant | Value | Notes |
|---|---|---|
| `PARTY_ASSIGNMENT_K` | Per-decade: 1.5 → 4.5 | Legacy. |
| `PARTY_ASSIGNMENT_K_ANES` | Per-decade: 2.1 → 5.1 | **ANES** back-solved from real `corr(party, axis)`. |

### 4.4 Elite drift schedule
| Constant | Value | Notes |
|---|---|---|
| `ELITE_DRIFT_SCHEDULE` | per-decade rates 0.003-0.008 | Legacy. |
| `ELITE_DRIFT_SCHEDULE_ANES` | per-decade rates ~ANES centroid velocities | x-axis. |
| `ELITE_DRIFT_SCHEDULE_ANES_Y` | 1.3 × x-rate per decade | y-axis (cult sort > econ sort). |
| `ELITE_DRIFT_ASYMMETRIC` | `{0: 0.5, 1: 1.5}` (constant) | Legacy. |
| `ELITE_DRIFT_ASYMMETRIC_ANES_SCHEDULE` | Per-decade: 1980 `{D:0.5, R:1.5}`, balanced 1990-2010, 2010 `{D:1.5, R:0.5}` | **ANES.** Reagan-era R-heavy → modern D-heavy cult sort. |

### 4.5 Identity sorting schedule
| Constant | Value | Notes |
|---|---|---|
| `IDENTITY_SORTING_SCHEDULE` | 1980: 0.02, 1990: 0.025, 2000: 0.03, 2010: 0.04, 2020: 0.045 | Mason 2018 trajectory. |

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
| `tier_d_anes_sigma_pc_multiplier` | 1.0 | 1.6 | Multiplier on `PARTY_CUE_SIGMA_HISTORICAL_ANES` |

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
| `tier_d_ic_sigma` | None | 0.35 | IC position σ (overrides hardcoded 0.45) |
| `tier_d_cue_correlation` | 0.0 | 0.40 | Cue draw (party_cue + media_cue) x-y correlation |

### 5.8 Step-1 evidence re-grade master gate
| Kwarg | Default | anes_full | Notes |
|---|---|---|---|
| `evidence_regrade` | False | **True** | Master gate for the Step-1 truth-pass (Gingrich/CU re-attribution, social-media demotion, identity-alignment → affect). `False` is a strict no-op → default path bit-identical. Pair with `build_schedule(evidence_regrade=...)`. See §7.1. |

### 5.9 Web-demo sandbox dials (illustrative — not a finding)
Three multiplier hooks added for the web demo's interactive sandbox
(`scripts/build_sandbox_data.py`). Each scales one already-present mechanism;
all default to `1.0`, and `×1.0` is exact in IEEE-754, so the default/pillar/
test path stays **bit-identical**. The sandbox cranks these *past* the
calibration envelope, so its outputs are illustrative only — not measured, not
re-blessed (provenance **E**/**N**). See methods.md §5.11.

| Kwarg | Default | Scales | Sandbox label / outcome axis |
|---|---|---|---|
| `sandbox_animus_mult` | 1.0 | per-agent `affect_lr` seed + `MediatedAnimus.learning_rate` | **animus** → out-party warmth |
| `sandbox_identity_mult` | 1.0 | `IdentitySorting` (sort_rate + step), `identity_sorting_multiplier`, `IdentityAlignment.rate` | **identity** → mega-identity stacking |
| `sandbox_rewire_mult` | 1.0 | `TieRewiring.rewire_rate` | **echo** → network modularity |

The other two sandbox dials reuse existing kwargs:
`tier_d_anes_drift_multiplier` (**elite** → party separation, §5.5) and
`tier_c_bc_strength` (**openness** → within-party tightness, §5.6). The five
dials were chosen by a metric-span screen (`scripts/sandbox_knob_screen.py`) so
each owns a distinct outcome axis.

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
`PARTY_CENTERS_*_ANES`, `PARTY_CUE_SIGMA_HISTORICAL_ANES`, and
`PARTY_ASSIGNMENT_K_ANES` constants in `historical_arc.py` are pinned
to this output.

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

1. **Pillar (`calm_to_camps.py`) is bit-identity-locked.** Do not
   touch it. New mechanisms default to no-op so the pillar tests
   stay green.
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
