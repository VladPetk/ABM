"""
Identity-threat dynamics (Phase 8c §5 E5).

Identity-threat is an exogenous-event-driven amplifier on existing
affect-formation and backlash-repulsion intensity. Mutz 2018 (status
threat) is the empirical anchor for the 2016 affect spike: white
Republican voters reported elevated identity threat in response to
demographic and cultural change cues, which amplified out-group
hostility.

The mechanism is two-part:

  - **A scalar `perceived_threat` attribute per agent**, in [0, 1].
    Default 0.0 (no threat). Set by scheduled threat events (e.g.,
    the 2016 election event in the historical arc). The pillar's
    S0-S4 baseline never sets threat — it's an empirical
    mechanism activated only in scenarios that schedule a threat
    event. Pillar-fallback discipline preserved (W4): pillar agents
    don't carry the attribute; the consumer rules
    (`AffectiveUpdate`, `BacklashRepulsion`) read with `.get(...,
    0.0)` and produce `threat_factor = 1.0` (no amplification),
    bit-identical to Phase 8c §4 behaviour.

  - **A decay rule (`ThreatDecay` here)** that runs each tick and
    multiplies every agent's `perceived_threat` by
    `(1 - decay_rate)`. Default `decay_rate = 0.05`: half-life ≈
    14 ticks ≈ 4.7 years. A 2016 spike at `perceived_threat = 0.5`
    decays to ~0.27 by 2020 and to noise by 2025, roughly tracking
    the ANES affect-spike pattern around the Trump era. The
    historical arc opts in at `decay_rate = 0.05`; the pillar wires
    it at `decay_rate = 0.0` (inert no-op).

How the consumers use it:

  Negative valence in `AffectiveUpdate` is scaled by
  `(1 + threat_amplification * perceived_threat)`. Positive valence
  (cooperative-positive path from Phase 8c §2) is **not**
  amplified — threat is identity-defensive, not socially open.
  Backlash push magnitude in `BacklashRepulsion` is also scaled by
  the same factor.

Reads (`ThreatDecay`):
  agent.state.attrs["perceived_threat"]   -- float, optional

Writes (direct env-rule mutation, like other env-rules):
  agent.state.attrs["perceived_threat"] *= (1 - decay_rate)
"""
from __future__ import annotations

from ..core.environment import Environment
from ..core.space import ContinuousSpace2D


class ThreatDecay:
    """Decays every agent's `perceived_threat` each tick by
    multiplicative factor `(1 - decay_rate)`. No-ops on agents
    without the attribute (pillar-fallback)."""

    def __init__(self, decay_rate: float = 0.05):
        self.decay_rate = decay_rate

    def apply(
        self,
        env: Environment,
        agents,
        space: ContinuousSpace2D,
        rng,
        tick: int,
    ) -> None:
        if self.decay_rate == 0:
            return
        factor = 1.0 - self.decay_rate
        for agent in agents:
            threat = agent.state.attrs.get("perceived_threat")
            if threat is None or threat == 0.0:
                continue
            agent.state.attrs["perceived_threat"] = float(threat * factor)
