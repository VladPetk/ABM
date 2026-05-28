"""
Identity-prime expiry env-rule (Phase 8c §4 I4; extended Phase 10).

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

**Phase 10 extension.** The Phase 10 X4 redesign (third-pass)
operates via ``cooperative_share`` boost and ``perceived_threat``
reset instead of identity-weight reduction (which Phase 9's
issue-coupling channel inverts). Prior values are snapshotted in
``x4_revert_cooperative_share`` and ``x4_revert_perceived_threat``
when the prime fires; this rule restores them on the same expiry
tick.

The earlier Phase 10 ``identity_pull_strength_y_override`` and
``identity_weight_override`` clears are kept inert (the third-pass
X4 mechanism doesn't set them; they remain available for any future
intervention that does).

**Pillar-fallback discipline.** When no agent carries
`identity_prime_expires_at`, the rule is a no-op. Pillar's S0-S4
agents never receive the prime; the rule is inert in pillar
contexts. Historical-arc agents and pillar-release X4 participants
get the prime; this rule clears it after the configured window.

Reads (per agent):
  agent.state.attrs["identity_prime_expires_at"]   -- int (tick), optional

Writes (direct env-rule mutation, like other env-rules):
  agent.state.attrs["identity_weight_override"] = None
  agent.state.attrs["identity_pull_strength_y_override"] = None  -- Phase 10
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
                # Phase 10 first-pass: also clear the identity-pull
                # y-axis override (inert under third-pass X4 design;
                # kept for any other intervention that sets it).
                agent.state.attrs["identity_pull_strength_y_override"] = None
                # Phase 10 third-pass: restore cooperative_share and
                # perceived_threat to their pre-X4 values, then drop
                # the snapshot attrs.
                prior_coop = agent.state.attrs.pop(
                    "x4_revert_cooperative_share", None,
                )
                if prior_coop is not None:
                    agent.state.attrs["cooperative_share"] = float(prior_coop)
                prior_threat = agent.state.attrs.pop(
                    "x4_revert_perceived_threat", None,
                )
                if prior_threat is not None:
                    agent.state.attrs["perceived_threat"] = float(prior_threat)
                agent.state.attrs["identity_prime_expires_at"] = None
