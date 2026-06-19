"""
IdentityToIdeologyPull — Mason 2018 "mega-identity" → position channel.

Each agent has an ``identities`` 1-d ndarray (e.g., 3 dimensions for
race, religion, urban/rural). Mason 2018 ch. 4 argues that mass-public
ideology aligns with these cross-cutting identities rather than the
reverse — identity is the carrier of partisan sort, and policy
positions follow.

This rule emits a small ``d_ideology`` aligned with each agent's
mean identity coordinate. Because identity vectors are seeded with
party-aligned mean ± per-agent dispersion (σ ≈ 0.3 / √n_dims), the
pull has TWO load-bearing pieces folded together:

  1. A party-aligned systematic component (strength * party_id_mean,
     ≈ ±0.20 in 1980), which lifts party_sep and corr in line with
     Mason's "identity drives ideology" thesis (Mason 2018 ch. 4-5).
  2. A within-party variance component (strength * agent_deviation,
     ≈ ±0.17 per dim), which injects wp_sd dispersion. This is the
     literature-faithful Mason channel — within-party identity
     heterogeneity persists post-sort and feeds ideology dispersion.

The wp_sd ceiling is set by per-tick variance INJECTION vs BC
compression. Identity-deviation injection rate ≈ (strength × σ_id)²,
which is small relative to GaussianNoise (σ ≈ 0.01-0.02) at any
reasonable strength. So this rule alone won't lift wp_sd to ANES
0.34 — it pairs with a modest GaussianNoise σ bump under ANES knobs.

Reads:
  agent.state.attrs["identities"]
  agent.state.attrs["stubbornness"]
Writes (delta):
  d_ideology = (1 - stubbornness) * (sx, sy) * mean(identities)

At strength_x = strength_y = 0 (default) the rule is a bit-identical
no-op — every existing scenario stays unchanged unless it opts in.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


class IdentityToIdeologyPull:
    def __init__(self, strength_x: float = 0.0, strength_y: float = 0.0):
        self.strength_x = float(strength_x)
        self.strength_y = float(strength_y)

    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta:
        rac_pull_y = float(env.attrs.get("racialization_pull_y", 0.0))
        if self.strength_x == 0.0 and self.strength_y == 0.0 and rac_pull_y == 0.0:
            return StateDelta()
        identities = agent.state.attrs.get("identities")
        if identities is None or len(identities) == 0:
            return StateDelta()
        # Phase 9 §11.7-E — scale the pull by the env's party-issue
        # coupling (which already runs a per-decade schedule 0.40 at
        # 1980 → 1.10 at 2020 per Mason 2018's "gradual great sort").
        # Mason 2018 places identity → ideology coupling mostly
        # post-1990; multiplying by party_issue_coupling makes IDPP
        # weak pre-1990 and strong post-2000, matching the literature.
        # Default 1.0 preserves the prior constant-strength behaviour
        # for any caller that doesn't set party_issue_coupling.
        coupling = float(env.attrs.get("party_issue_coupling", 1.0))
        # Per-agent identity signal: mean across identity dims.
        # In historical_arc the 3 dims share a party-aligned center
        # (Dems ~ -0.20, Reps ~ +0.20 in 1980, drifting via
        # IdentitySorting), so the mean carries both the systematic
        # party-aligned component and per-agent deviation.
        signal = float(np.mean(identities))
        # Phase 10 X4 — per-agent override for the y-axis pull
        # magnitude (Levendusky 2018 identity prime dampens the
        # cultural-axis identity → ideology coupling for primed
        # agents). Default `None` reads the rule's `strength_y`,
        # preserving bit-identity for any scenario that doesn't seed
        # the override.
        sy_override = agent.state.attrs.get(
            "identity_pull_strength_y_override"
        )
        eff_strength_y = (
            float(sy_override) if sy_override is not None
            else self.strength_y
        )
        # Racialization onset (spec §10): a time-profiled cultural-axis pull added
        # ON TOP of the baseline Mason channel (baseline = generic identity
        # sorting; this = the extra post-2008 racial spillover, Tesler). The peak
        # `racialization_pull_y` and the per-tick 2008->2016 ramp
        # `racialization_salience_y` (written by RacializationSalience) are absent
        # on every existing path → +0 → bit-identical. Routed through the same
        # coupling + FJ stubbornness damping below.
        eff_strength_y = eff_strength_y + rac_pull_y * float(
            env.attrs.get("racialization_salience_y", 0.0))
        d = np.array([
            coupling * self.strength_x * signal,
            coupling * eff_strength_y * signal,
        ])
        # Friedkin-Johnsen anchoring: stubborn agents resist the pull,
        # matching the rest of the historical-arc pipeline.
        s = float(agent.state.attrs.get("stubbornness", 0.0))
        return StateDelta(d_ideology=(1.0 - s) * d)
