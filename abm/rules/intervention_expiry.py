"""
Intervention expiry env-rules (Phase 10).

Two env-rules that revert time-bounded Phase 10 interventions after
their literature-grounded durability window elapses. They share the
same "watch a tick threshold, restore the prior state" shape as
``IdentityPrimeExpiry`` (Phase 8c §4 I4) but cover the new Phase 10
intervention bundles whose durations don't fit that rule's
per-agent identity-prime contract.

``PerceptionBoostExpiry`` — Phase 10 X7 sustained perception
campaign. X7's setup boosts each treated agent's
``PerceptionUpdate.correction_rate`` (per-agent override
``correction_rate_override``) for a short window (3 ticks ≈ 1 year
per Druckman et al. 2022 durability pessimism on perception
corrections). After ``perception_boost_expires_at`` elapses, this
rule clears the override and the expiry attribute.

``X1ExposureExpiry`` — Phase 10 X1 cross-partisan-exposure
environment. X1's setup boosts ``BacklashRepulsion.threat_amplification``
and ``AffectiveUpdate.identity_weight`` at the rule level (a
population-environment change, not a per-agent prime). Revert info
is stored in ``env.attrs["x1_revert"]`` as a dict with keys
``expires_at`` and ``reverts`` (a list of
``(rule_instance, attr_name, prior_value)`` tuples). When the
window elapses this rule restores each rule attribute and clears
the env entry. Storing rule instances directly avoids needing to
look the rules up via the engine, which env-rules don't have
access to.

**Pillar-fallback discipline.** Both rules no-op when their watched
state is absent. The pillar's S0-S4 baseline never sets
``perception_boost_expires_at`` (no X7 setup runs in the pillar
release-phase prior to Phase 10) or ``env.attrs["x1_revert"]``,
so the rules are inert in pillar contexts. The X-interventions
populate the watched state when they fire; the expiry rules then
clean up after the window.

Reads (per agent / per env):
  agent.state.attrs["perception_boost_expires_at"]   -- int (tick), optional
  env.attrs["x1_revert"]                              -- dict, optional

Writes (direct mutation, like other env-rules):
  agent.state.attrs["correction_rate_override"] = None
  agent.state.attrs["perception_boost_expires_at"] = None
  rule.threat_amplification, rule.identity_weight  -- restored
  env.attrs.pop("x1_revert", None)
"""
from __future__ import annotations

from ..core.environment import Environment
from ..core.space import ContinuousSpace2D


class PerceptionBoostExpiry:
    """Phase 10 X7 — clears per-agent perception correction-rate
    overrides AND the perception-target override
    (``perception_target_override``) whose expiry tick has elapsed.
    No-op outside the X7 window."""

    def apply(
        self,
        env: Environment,
        agents,
        space: ContinuousSpace2D,
        rng,
        tick: int,
    ) -> None:
        for agent in agents:
            expiry = agent.state.attrs.get("perception_boost_expires_at")
            if expiry is None:
                continue
            if tick >= int(expiry):
                agent.state.attrs["correction_rate_override"] = None
                # Phase 10 X7 third-pass: also clear the campaign-mode
                # target override so the agent reverts to pulling toward
                # observed-neighbour mean post-campaign.
                agent.state.attrs["perception_target_override"] = None
                agent.state.attrs["perception_boost_expires_at"] = None


class X1ExposureExpiry:
    """Phase 10 X1 — restores rule-level attrs to their
    pre-intervention values when the X1 window elapses. No-op
    outside the X1 window (env.attrs lacks the ``x1_revert``
    entry). Storing rule instances directly in the revert payload
    sidesteps the lack of engine access from env-rules.
    """

    def apply(
        self,
        env: Environment,
        agents,
        space: ContinuousSpace2D,
        rng,
        tick: int,
    ) -> None:
        revert = env.attrs.get("x1_revert")
        if revert is None:
            return
        if tick < int(revert.get("expires_at", 1 << 30)):
            return
        for rule, attr, prior in revert.get("reverts", ()):
            if hasattr(rule, attr):
                setattr(rule, attr, prior)
        env.attrs.pop("x1_revert", None)
