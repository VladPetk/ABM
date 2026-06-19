"""RacializationSalience — the racialization onset as a single, time-profiled
cultural-axis salience forcing.

Spec: docs/internal/racialization_spillover_spec.md (§9, §10). This is the
ONSET build: it writes ``env.attrs["racialization_salience_y"]`` each tick —

    0                         before the 2008 onset (tick < onset_tick)
    linear ramp 0 -> 1.0      onset_tick -> peak_tick (2008 -> 2016; Tesler spillover)
    1.0 (HOLD)                after peak_tick

``IdentityToIdeologyPull`` multiplies its ``racialization_pull_y`` (the peak
magnitude) by this salience, ADDING the racialization pull on top of the baseline
Mason mega-identity channel. So the racialization carrier is a single named
cultural forcing whose timing is the only thing fed.

The OPTIONAL ``decay_frac`` enables the DERACIALIZATION sensitivity probe (the
2020->2024 Latino/minority dealignment): salience relaxes from 1.0 to
``decay_frac`` between ``hold_end_tick`` and ``decay_end_tick``. Per the spec's
expert review (§10) this is **off by default** for the onset build, graded LOW,
and must be PRE-REGISTERED from the dealignment literature rather than tuned to
the (noisy, both-axes) 2024 ANES point — keep ``decay_frac=None`` for the onset.

Provenance: forcing layer (Layer 2). **E** (single-carrier choice) + **N**
(functional form). Onset grade **MED** (Tesler), decay grade **LOW** (contested,
2020-2024). Does NOT resolve blindspot #7 — it makes the forced share legible,
not emergent.
"""
from __future__ import annotations

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D


class RacializationSalience:
    """EnvRule. Writes the per-tick racialization salience ∈ [decay_frac, 1].

    onset_tick / peak_tick — the 2008->2016 spillover ramp (default ticks 84/108).
    hold_end_tick / decay_end_tick / decay_frac — the OPTIONAL deracialization
    decay (default decay_frac=None → ramp-and-HOLD, the onset build).
    """

    def __init__(
        self,
        onset_tick: int = 84,
        peak_tick: int = 108,
        hold_end_tick: int = 120,
        decay_end_tick: int = 132,
        decay_frac: float | None = None,
    ):
        self.onset_tick = int(onset_tick)
        self.peak_tick = int(peak_tick)
        self.hold_end_tick = int(hold_end_tick)
        self.decay_end_tick = int(decay_end_tick)
        self.decay_frac = None if decay_frac is None else float(decay_frac)

    def salience(self, tick: int) -> float:
        if tick < self.onset_tick:
            return 0.0
        if tick < self.peak_tick:
            return (tick - self.onset_tick) / float(self.peak_tick - self.onset_tick)
        # ramped in; HOLD unless the deracialization decay is enabled.
        if self.decay_frac is None or tick < self.hold_end_tick:
            return 1.0
        if tick <= self.decay_end_tick:
            frac = (tick - self.hold_end_tick) / float(
                self.decay_end_tick - self.hold_end_tick)
            return 1.0 - (1.0 - self.decay_frac) * frac
        return self.decay_frac

    def apply(self, env: Environment, agents: list[Agent],
              space: ContinuousSpace2D, rng, tick: int) -> None:
        env.attrs["racialization_salience_y"] = float(self.salience(tick))
