"""
General exogenous-shock mechanism (web_demo exogenous-shocks workstream).

The historical arc already injects exogenous events, but each one is a
bespoke imperative function (the Obama warmth bump, the 2016 status-threat
spike, the COVID learning-rate window, the Trump centroid nudge). They share
no structure, hand-roll their own decay/revert, and — crucially — almost all
push toward *divergence*. The engine had no vocabulary for *convergence*
(rally-around-the-flag, cross-cutting consensus).

This module makes a shock **declarative data** rather than code:

  ShockSpec(target_state, direction, population, magnitude, persistence, ...)

`make_shock_event(spec)` compiles a spec into the exact `event_fn(engine)`
closure the existing `ScheduledEvent` / `Schedule.fire_due` machinery
already runs (`schedule.py` is untouched). Transient / windowed / ramped
shocks register a record in `env.attrs["active_shocks"]`; the companion
env-rule `abm/rules/shock_relaxation.py::ShockRelaxation` advances and
retires those records each tick — generalizing the per-event hand-rolled
reverts (ThreatDecay, the COVID lr-revert).

Gating / bit-identity discipline: the mechanism is wired into the
historical arc behind the **new, independent `exogenous_shocks` flag**
(default False). With the flag off, no ledger is seeded, `ShockRelaxation`
is not added to the pipeline, and no shock events are appended to the
schedule — so the default path (pillar + Phase 4–9 historical default) is
byte-for-byte identical to head. The flag is turned on only in the
canonical web/ANES preset (`scripts/anes_preset.ANES_FULL_KWARGS`) after
the mandatory re-validate → re-measure Phase 10 → re-bless cycle.

The catalogue (`SHOCK_CATALOGUE`) ships two empirical shocks:

  - **S-911** (9/11 rally-around-the-flag, Sept 2001) — a small *transient*
    out-party AFFECT warming that decays within ~18 months. The convergence
    demonstrator. Graded MED/CONTESTED: the well-documented +35-39pt
    *presidential-approval* rally (Gallup, the largest ever) is NOT an
    out-party thermometer quantity, and there is no firm ANES evidence that
    out-party *warmth* rose; the bipartisanship dissolved into a sharp
    partisan split by the Iraq War. So the affect channel is modeled small
    and flagged.

  - **S-OBERGEFELL** (same-sex-marriage / Obergefell, June 2015) — on the
    *bundled* cultural axis the engine shows **no convergence**: a small
    permanent DIVERGENCE matching the empirically *widening* partisan gap
    (Gallup 2025: record party divide 10 years on), because the genuine SSM
    opinion convergence (27% support 1996 → 60% 2015 → ~71% 2023, driven
    mostly by within-person attitude change — Rosenfeld 2017; Kranjac &
    Wagmiller 2022) was a *single sub-issue*, not the whole culture war
    (abortion ~flat, immigration polarized). Modeling it as whole-axis
    progressive convergence would over-claim. The real convergence numbers
    live in `evidence_note` / the timeline copy, not as a visible
    converging signal on the compass. (Decision A, signed off 2026-06-01.)
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field

import numpy as np

from .schedule import ScheduledEvent


# --- Taxonomy enums ------------------------------------------------------


class TargetState(enum.Enum):
    """Which piece of engine state a shock perturbs. Exhaustive over what
    the existing ad-hoc handlers touch (proof of generality)."""

    AFFECT = "affect"                       # per-agent out-party warmth dict
    THREAT = "threat"                       # per-agent perceived_threat
    POSITION = "position"                   # per-agent ideology (compass)
    IDENTITY_ALIGNMENT = "identity_alignment"  # per-agent mega-identity scalar
    LEARNING_RATE = "learning_rate"         # AffectiveUpdate.lr (rule-level)
    ELITE_DRIFT_RATE = "elite_drift_rate"   # EliteDrift.rate (rule-level)
    SALIENCE = "salience"                   # env party_issue_coupling


class Direction(enum.Enum):
    """Fixes the SIGN/target of the perturbation so the catalogue reads
    honestly. Convergence is the capability the engine previously lacked."""

    CONVERGENCE = "convergence"
    DIVERGENCE = "divergence"


class Persistence(enum.Enum):
    """Decay/revert profile. TRANSIENT/WINDOW/RAMP register a ledger record
    that ShockRelaxation advances; PERMANENT is a one-shot level shift."""

    PERMANENT = "permanent"     # one-shot, never reverted
    TRANSIENT = "transient"     # injected delta relaxes back to 0 (decay_rate)
    WINDOW = "window"           # apply at onset, revert fully after duration
    RAMP = "ramp"               # phase magnitude in over ramp_ticks, then hold


class Axis(enum.Enum):
    X = 0
    Y = 1
    BOTH = 2


# --- Population selector --------------------------------------------------


@dataclass(frozen=True)
class PopulationSelector:
    """Resolves to the set of agent ids a shock hits. Modes compose:
    a party filter AND an identity filter AND a stochastic subsample.

    `mode`:
      "all"          -> every partisan agent (party in {0, 1})
      "by_party"     -> agents whose party is a key of `party_fractions`,
                        each party subsampled to its fraction
      "by_identity"  -> partisan agents passing the identity-axis comparator
    Independents (party=2) are never selected for affect/threat shocks
    (they carry no such state); POSITION shocks may include them via
    `include_independents=True`.
    """

    mode: str = "all"
    party_fractions: tuple | None = None    # tuple of (party_id, fraction) pairs
    identity_axis: int | None = None
    identity_cmp: str | None = None          # ">" or "<"
    identity_threshold: float | None = None
    fraction: float = 1.0
    rng_seed_offset: int = 0
    include_independents: bool = False

    # --- factory helpers (frozen-friendly) ---
    @classmethod
    def all(cls, include_independents: bool = False) -> "PopulationSelector":
        return cls(mode="all", include_independents=include_independents)

    @classmethod
    def by_party(cls, fractions: dict, rng_seed_offset: int = 0) -> "PopulationSelector":
        return cls(
            mode="by_party",
            party_fractions=tuple(sorted(fractions.items())),
            rng_seed_offset=rng_seed_offset,
        )

    @classmethod
    def by_identity(
        cls, axis: int, cmp: str, threshold: float,
        fraction: float = 1.0, rng_seed_offset: int = 0,
    ) -> "PopulationSelector":
        return cls(
            mode="by_identity", identity_axis=axis, identity_cmp=cmp,
            identity_threshold=threshold, fraction=fraction,
            rng_seed_offset=rng_seed_offset,
        )

    def resolve(self, engine) -> set[int]:
        agents = engine.agents

        def _is_partisan(a):
            p = a.state.attrs.get("party")
            if p in (0, 1):
                return True
            return self.include_independents and p == 2

        if self.mode == "by_party":
            fracs = dict(self.party_fractions or ())
            out: set[int] = set()
            base_seed = int(
                engine.env.attrs.get("faction_event_rng_seed", 0)
            ) + int(self.rng_seed_offset)
            for party_id, frac in sorted(fracs.items()):
                ids = sorted(
                    a.id for a in agents if a.state.attrs.get("party") == party_id
                )
                if not ids:
                    continue
                if frac >= 1.0:
                    out.update(ids)
                    continue
                n = int(round(frac * len(ids)))
                if n <= 0:
                    continue
                rng = np.random.default_rng(base_seed + party_id)
                chosen = rng.choice(ids, size=min(n, len(ids)), replace=False)
                out.update(int(i) for i in chosen)
            return out

        if self.mode == "by_identity":
            def _match(a):
                if not _is_partisan(a):
                    return False
                v = float(a.state.ideology[self.identity_axis])
                if self.identity_cmp == ">":
                    return v > self.identity_threshold
                if self.identity_cmp == "<":
                    return v < self.identity_threshold
                return False
            ids = sorted(a.id for a in agents if _match(a))
        else:  # "all"
            ids = sorted(a.id for a in agents if _is_partisan(a))

        if self.fraction >= 1.0 or not ids:
            return set(ids)
        n = int(round(self.fraction * len(ids)))
        if n <= 0:
            return set()
        base_seed = int(
            engine.env.attrs.get("faction_event_rng_seed", 0)
        ) + int(self.rng_seed_offset)
        rng = np.random.default_rng(base_seed)
        chosen = rng.choice(ids, size=min(n, len(ids)), replace=False)
        return set(int(i) for i in chosen)


# --- Shock specification --------------------------------------------------


@dataclass(frozen=True)
class ShockSpec:
    """A declarative exogenous shock. Compiled to a `ScheduledEvent` by
    `make_shock_event` / `shock_scheduled_events`."""

    label: str
    description: str
    actual_date: str            # "YYYY-MM" — for the timeline display
    kind: str                   # timeline category (e.g. "rally", "consensus")
    onset_tick: int
    target_state: TargetState
    direction: Direction
    magnitude: float            # native units of target_state (or multiplier
                                # for LEARNING_RATE / ELITE_DRIFT / SALIENCE)
    population: PopulationSelector
    persistence: Persistence
    evidence_grade: str         # HIGH / MED / LOW / CONTESTED / MARKER
    evidence_source: str
    evidence_note: str
    axis: Axis | None = None            # POSITION shocks
    decay_rate: float | None = None      # TRANSIENT
    duration_ticks: int | None = None    # WINDOW
    ramp_ticks: int | None = None        # RAMP
    consensus_target: tuple | None = None  # POSITION CONVERGENCE attractor (x, y)
    rule_class: str | None = None        # LEARNING_RATE / ELITE_DRIFT rule name

    def signed_magnitude(self) -> float:
        """Magnitude with the sign implied by `direction` for the additive
        targets (AFFECT/THREAT/IDENTITY_ALIGNMENT). For AFFECT, CONVERGENCE
        = warming (+, toward less-negative warmth); DIVERGENCE = cooling
        (-). For THREAT / IDENTITY_ALIGNMENT, DIVERGENCE = up (+),
        CONVERGENCE = down (-). POSITION uses geometry, not this sign."""
        m = abs(self.magnitude)
        if self.target_state == TargetState.AFFECT:
            return +m if self.direction == Direction.CONVERGENCE else -m
        # THREAT / IDENTITY_ALIGNMENT: divergence raises the polarizing state
        return +m if self.direction == Direction.DIVERGENCE else -m


# --- Compilation: ShockSpec -> event_fn ----------------------------------


def _apply_affect(engine, spec, target_ids):
    """Inject a per-(agent, out-party) warmth delta. Returns the residual
    bookkeeping dict {agent_id: {other_party: applied_delta}} for relaxation
    (TRANSIENT) or {} for PERMANENT."""
    delta = spec.signed_magnitude()
    residual: dict[int, dict[int, float]] = {}
    for a in engine.agents:
        if a.id not in target_ids:
            continue
        affect = a.state.attrs.get("affect")
        if not affect:
            continue
        per_party: dict[int, float] = {}
        for other_party in list(affect.keys()):
            before = float(np.clip(affect[other_party], -1.0, 1.0))
            after = float(np.clip(before + delta, -1.0, 1.0))
            affect[other_party] = after
            per_party[int(other_party)] = after - before  # actually applied
        if per_party:
            residual[a.id] = per_party
    return residual


def _apply_threat_or_alignment(engine, spec, target_ids, attr):
    """Add a signed scalar to `attr` (perceived_threat / identity_alignment),
    clipping to [0, 1]. Returns residual {agent_id: applied_delta}."""
    delta = spec.signed_magnitude()
    residual: dict[int, float] = {}
    for a in engine.agents:
        if a.id not in target_ids:
            continue
        before = float(np.clip(a.state.attrs.get(attr, 0.0), 0.0, 1.0))
        after = float(np.clip(before + delta, 0.0, 1.0))
        a.state.attrs[attr] = after
        applied = after - before
        if applied != 0.0:
            residual[a.id] = applied
    return residual


def _apply_position(engine, spec, target_ids, frac=1.0):
    """Apply a position nudge. DIVERGENCE pushes each agent outward along
    the chosen axis by party sign (party 1 = +, party 0 = - — matching the
    engine's R=traditional/+y, D=progressive/-y convention). CONVERGENCE
    pulls each agent a fraction `|magnitude|` toward `consensus_target`.

    `frac` (used by RAMP) scales the applied amount this call (e.g. 1/ramp_ticks).
    """
    m = abs(spec.magnitude) * float(frac)
    if m == 0.0:
        return
    for a in engine.agents:
        if a.id not in target_ids:
            continue
        pos = a.state.ideology
        if spec.direction == Direction.CONVERGENCE and spec.consensus_target is not None:
            target = np.asarray(spec.consensus_target, dtype=float)
            new = pos + m * (target - pos)
        else:
            party = a.state.attrs.get("party")
            sign = 1.0 if party == 1 else (-1.0 if party == 0 else 0.0)
            if sign == 0.0:
                continue
            dvec = np.zeros(2)
            if spec.axis in (Axis.X, Axis.BOTH):
                dvec[0] = sign * m
            if spec.axis in (Axis.Y, Axis.BOTH):
                dvec[1] = sign * m
            new = pos + dvec
        a.state.ideology = engine.space.clip(new)


def _apply_rule_multiplier(engine, spec):
    """Multiply a rule-level attr (AffectiveUpdate.lr for LEARNING_RATE,
    EliteDrift.rate for ELITE_DRIFT_RATE) by `magnitude`. Returns the
    (rule, attr, pre_value) tuple for WINDOW revert, or None."""
    attr = "lr" if spec.target_state == TargetState.LEARNING_RATE else "rate"
    pools = [engine.rules.rules, engine.env_rules]
    for pool in pools:
        for r in pool:
            if type(r).__name__ == spec.rule_class:
                pre = getattr(r, attr)
                setattr(r, attr, pre * spec.magnitude)
                return (r, attr, pre)
    raise KeyError(f"shock rule {spec.rule_class} not in pipeline")


def make_shock_event(spec: ShockSpec):
    """Compile a ShockSpec into an `event_fn(engine)` for ScheduledEvent."""

    def event_fn(engine):
        # Defence-in-depth: the schedule only appends shock events when the
        # flag is on, but guard anyway so a stray spec is inert by default.
        if not engine.env.attrs.get("exogenous_shocks"):
            return
        ledger = engine.env.attrs.setdefault("active_shocks", [])
        target_ids = spec.population.resolve(engine)

        if spec.target_state == TargetState.POSITION:
            if spec.persistence == Persistence.RAMP and spec.ramp_ticks:
                # Ledger drives the per-tick increments; nothing applied now.
                ledger.append({
                    "label": spec.label, "profile": "ramp_position",
                    "spec": spec, "target_ids": set(target_ids),
                    "onset_tick": engine.tick, "ramp_ticks": int(spec.ramp_ticks),
                    "ticks_done": 0,
                })
            else:
                _apply_position(engine, spec, target_ids)  # PERMANENT one-shot
            return

        if spec.target_state in (
            TargetState.LEARNING_RATE, TargetState.ELITE_DRIFT_RATE,
        ):
            rec = _apply_rule_multiplier(engine, spec)
            if spec.persistence == Persistence.WINDOW and spec.duration_ticks:
                rule, attr, pre = rec
                ledger.append({
                    "label": spec.label, "profile": "window_rule",
                    "rule": rule, "attr": attr, "pre_value": pre,
                    "expiry_tick": engine.tick + int(spec.duration_ticks),
                })
            return

        if spec.target_state == TargetState.SALIENCE:
            pre = float(engine.env.attrs.get("party_issue_coupling", 1.0))
            engine.env.attrs["party_issue_coupling"] = pre * spec.magnitude
            if spec.persistence == Persistence.WINDOW and spec.duration_ticks:
                ledger.append({
                    "label": spec.label, "profile": "window_salience",
                    "pre_value": pre,
                    "expiry_tick": engine.tick + int(spec.duration_ticks),
                })
            return

        # Additive scalar/dict targets: AFFECT, THREAT, IDENTITY_ALIGNMENT.
        if spec.target_state == TargetState.AFFECT:
            residual = _apply_affect(engine, spec, target_ids)
            kind = "transient_affect"
        elif spec.target_state == TargetState.THREAT:
            residual = _apply_threat_or_alignment(
                engine, spec, target_ids, "perceived_threat"
            )
            kind = "transient_scalar"
        else:  # IDENTITY_ALIGNMENT
            residual = _apply_threat_or_alignment(
                engine, spec, target_ids, "identity_alignment"
            )
            kind = "transient_scalar"

        if spec.persistence == Persistence.TRANSIENT and spec.decay_rate:
            ledger.append({
                "label": spec.label,
                "profile": kind,
                "attr": (
                    "affect" if spec.target_state == TargetState.AFFECT
                    else "perceived_threat"
                    if spec.target_state == TargetState.THREAT
                    else "identity_alignment"
                ),
                "decay_rate": float(spec.decay_rate),
                "residual": residual,
            })
        # PERMANENT additive shocks (e.g. the Obama-style warmth bump) leave
        # no ledger record — the injected level just persists.

    return event_fn


def shock_scheduled_events(specs) -> list[ScheduledEvent]:
    """Compile a list of ShockSpecs into ScheduledEvents for build_schedule."""
    return [
        ScheduledEvent(
            spec.onset_tick, spec.label, spec.description, make_shock_event(spec),
        )
        for spec in specs
    ]


# --- The empirical catalogue (1980–2025) ---------------------------------
# Tick convention: 1980 = tick 0, TICKS_PER_YEAR = 3.

# S-911 — 9/11 rally-around-the-flag. Sept 2001 ≈ tick 65 (21.67y × 3).
# Small TRANSIENT out-party warming, decay_rate 0.14 → half-life ~4.6 ticks
# (~18 months); injected warmth is ~gone (<1% of Δ) by ~tick 95, so it
# leaves the 2016+ trajectory and the Phase-10 release windows (90/120)
# essentially untouched. Graded MED/CONTESTED (see module docstring).
SHOCK_911_TICK = 65
SHOCK_911_MAGNITUDE = 0.08      # [-1,1] warmth units (~+4 thermometer degrees)
SHOCK_911_DECAY_RATE = 0.14     # half-life ~4.6 ticks ≈ 18 months

S_911 = ShockSpec(
    label="rally_911_2001",
    description=(
        "9/11 rally-around-the-flag (Sept 2001) — a brief national-unity "
        "warming toward the out-party that decays within ~18 months. Modeled "
        "small and flagged contested: the famous +35-39pt rally was "
        "presidential approval (Gallup's largest ever), not an out-party "
        "thermometer effect, and the unity dissolved into a sharp partisan "
        "split by the Iraq War (2003)."
    ),
    actual_date="2001-09",
    kind="rally",
    onset_tick=SHOCK_911_TICK,
    target_state=TargetState.AFFECT,
    direction=Direction.CONVERGENCE,
    magnitude=SHOCK_911_MAGNITUDE,
    population=PopulationSelector.all(),
    persistence=Persistence.TRANSIENT,
    decay_rate=SHOCK_911_DECAY_RATE,
    evidence_grade="MED",
    evidence_source="Gallup 2001-02 (approval rally + decay); Brookings (Iraq split)",
    evidence_note=(
        "Bush approval surged 51%→90% (largest rally Gallup has measured) and "
        "reverted to ~66% within a year. That is APPROVAL, not partisan "
        "warmth; no firm ANES evidence out-party thermometers rose. Included "
        "as a small transient warming so the model can represent convergence "
        "shocks at all — its honest lesson is how shallow and short-lived even "
        "the biggest rally was."
    ),
)

# S-OBERGEFELL — same-sex marriage / Obergefell. June 2015 = tick 105.
# Decision A (signed off 2026-06-01): the genuine SSM opinion convergence is
# a SINGLE sub-issue, not the whole bundled cultural axis, and the partisan
# GAP widened. So on the compass we model a small PERMANENT DIVERGENCE (the
# widening gap), defaulting toward no-impact — NOT convergence. The real
# convergence numbers live in evidence_note / the timeline copy.
SHOCK_OBERGEFELL_TICK = 105
# Slight y-axis (cultural) divergence matching the widening partisan gap.
# Kept tiny so it stays within the ANES band; tunable. Set to 0.0 for a
# pure non-causal marker (like the Citizens-United demotion).
SHOCK_OBERGEFELL_Y_DIVERGENCE = 0.02

S_OBERGEFELL = ShockSpec(
    label="obergefell_2015",
    description=(
        "Obergefell v. Hodges / same-sex marriage (June 2015). On the bundled "
        "cultural axis the model shows NO convergence — at most the slight "
        "partisan-gap widening the data records. The genuine opinion "
        "convergence was a single sub-issue, not the whole culture war."
    ),
    actual_date="2015-06",
    kind="consensus_subissue",
    onset_tick=SHOCK_OBERGEFELL_TICK,
    target_state=TargetState.POSITION,
    direction=Direction.DIVERGENCE,
    magnitude=SHOCK_OBERGEFELL_Y_DIVERGENCE,
    axis=Axis.Y,
    population=PopulationSelector.all(),
    persistence=Persistence.PERMANENT,
    evidence_grade="MARKER",   # the AXIS impact is a marker; the sub-issue
                               # convergence (below) is HIGH but un-mapped
    evidence_source="Gallup 1996-2025; Rosenfeld 2017; Kranjac & Wagmiller 2022",
    evidence_note=(
        "Same-sex-marriage support rose 27% (1996) → majority by 2011 → 60% "
        "(2015, pre-ruling) → ~69-71% (2021-23) — the fastest opinion shift "
        "Gallup has tracked, driven MORE by within-person attitude change than "
        "by cohort replacement (Rosenfeld 2017; Kranjac & Wagmiller 2022). But "
        "this was ONE sub-issue: the rest of the cultural bundle (abortion, "
        "immigration) did not liberalize, and the SSM PARTISAN GAP actually "
        "widened (Gallup 2025: record party divide 10 years on). So the "
        "bundled cultural axis correctly shows no convergence — modeling "
        "whole-axis liberalization here would over-claim. The convergence is "
        "narrated in copy, not drawn as compass movement."
    ),
)

# v1 catalogue. The 2008 recession is deferred (no firm polarization
# magnitude). COVID/threat/Obama stay as their existing hand-rolled handlers
# (Decision B) — mirrored here in spirit only, not refactored.
SHOCK_CATALOGUE = [S_911, S_OBERGEFELL]
