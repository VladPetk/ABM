"""
Identity-prime expiry env-rule (Phase 8c §4 I4).

X4's "shared-identity prime" intervention temporarily downweights
participating agents' identity-distance contribution to valence by
setting `identity_weight_override = 0.1` (the spec default; vs
default `identity_weight = 0.5`) and recording an expiry tick
(`identity_prime_expires_at`). This env-rule, run once per tick,
clears the override and expiry attribute for any agent whose prime
window has elapsed.

The mechanism realises Levendusky 2021 *Our Common Bonds*'
shared-identity priming: agents in the prime condition temporarily
background their partisan identity (lower identity_weight in the
valence formula) under the salience of a superordinate (American
national) identity. After the prime expires, partisan identity
re-asserts (override cleared; valence reverts to `self.identity_weight`).

**Pillar-fallback discipline.** When no agent carries
`identity_prime_expires_at`, the rule is a no-op. Pillar's S0-S4
agents never receive the prime; the rule is inert in pillar
contexts. Historical-arc agents and pillar-release X4 participants
get the prime; this rule clears it after the configured window.

Reads (per agent):
  agent.state.attrs["identity_prime_expires_at"]   -- int (tick), optional

Writes (direct env-rule mutation, like other env-rules):
  agent.state.attrs["identity_weight_override"] = None
  agent.state.attrs["identity_prime_expires_at"] = None
"""
from __future__ import annotations

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D


class IdentityPrimeExpiry:
    """Clears X4 identity-prime overrides whose expiry tick has elapsed."""

    def apply(
        self,
        env: Environment,
        agents,
        space: ContinuousSpace2D,
        rng,
        tick: int,
    ) -> None:
        # Quick scan — most ticks, most populations have no primed
        # agents, so this is effectively a no-op outside the prime
        # window. No env-attr writes; per-agent attribute clear only.
        for agent in agents:
            expiry = agent.state.attrs.get("identity_prime_expires_at")
            if expiry is None:
                continue
            if tick >= int(expiry):
                agent.state.attrs["identity_weight_override"] = None
                agent.state.attrs["identity_prime_expires_at"] = None
