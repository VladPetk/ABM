"""
Bounded-confidence attraction, network-mediated (ADR-001).

The candidate set for each agent is its **social-network neighbours**, not
a spatial radius query. Among the network neighbours, the agent shifts a
fraction ``strength`` of the way toward the mean of those within ideological
distance ``epsilon`` (the canonical hard-cutoff filter).

On a **complete graph** every agent is everyone else's neighbour, so the
hard-cutoff filter then picks the same set as classic Hegselmann-Krause:
the network generalises HK, it does not replace it (ADR-001 §7).

Phase 4 adds two attrs:

- ``temperature`` — the F2 graded confidence filter. Defaults to ``0.0``,
  the canonical hard-cutoff behaviour, so every existing scenario
  (``compass_basic``, ``actb``, etc.) and the canonical HK replication
  tests are unchanged. The pillar opts in to ``temperature = 0.05`` via
  ``build_engine`` and every intervention bundle. With ``temperature > 0``
  the candidate set is *every* network neighbour, weighted by the
  logistic ``w(d) = 1 / (1 + exp((d - epsilon) / temperature))``.
- Friedkin-Johnsen ``stubbornness`` scaling (F1) is applied uniformly at
  the apply site: the rule's intended ``d_ideology`` is multiplied by
  ``(1 - stubbornness)``. Agents without a stubbornness attr (every
  non-pillar scenario) see ``s = 0`` and the scaling is a no-op.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.issues import issues_of, rms_distance
from ..core.network import neighbor_agents
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


class BoundedConfidenceInfluence:
    def __init__(
        self,
        epsilon: float = 0.3,
        strength: float = 0.1,
        temperature: float = 0.0,
        affect_weight: float = 0.0,
        affect_weight_floor: float = 0.0,
    ):
        self.epsilon = epsilon
        self.strength = strength
        self.temperature = temperature
        # Phase 5 (A4): per-neighbour affect modulator. Default 0.0
        # preserves canonical / non-pillar behaviour exactly. The pillar
        # opts in via bundles (BC_AFFECT_WEIGHT in calm_to_camps.py).
        self.affect_weight = affect_weight
        # R-phase R4 — BC revival. A FLOOR on the affect modulator so that
        # warmth re-opens cross-party influence (Hegselmann-Krause 2002 graded
        # ε; affect modulation, Phase 5). The modulator is two-sided: cold
        # out-party neighbours are down-weighted (echo chamber), WARM ones are
        # up-weighted (1 + aw·warmth > 1) → cross-party position convergence.
        # So with the floor on, R1/R3 warming converts into depolarizing BC
        # convergence on the position axis. Default 0.0 → max(x, 0.0)=x →
        # bit-identical (only applied when > 0). Requires temperature > 0.
        self.affect_weight_floor = float(affect_weight_floor)

    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta:
        if self.strength == 0.0:
            return StateDelta()
        neighbours = neighbor_agents(agent, space, env)
        if not neighbours:
            return StateDelta()
        # MHV S3 T3.3 — data-fed media channel: when MediaPenetrationSeries is
        # installed it writes env.attrs["bc_affect_weight"] each tick from the
        # social-media adoption curve; absent that key, fall back to the rule's
        # own (event-set) affect_weight → bit-identical for every other path.
        affect_weight = float(env.attrs.get("bc_affect_weight", self.affect_weight))
        # R4: floor so warmth can re-open cross-party influence even when the
        # media-driven bc_affect_weight is low. Only applied when > 0 → the
        # default path is byte-identical.
        if self.affect_weight_floor > 0.0:
            affect_weight = max(affect_weight, self.affect_weight_floor)
        # MHV S2 T2.2 — native D-dim path. In live issues mode the rule
        # measures distances and averages targets over the FULL issue
        # vectors (RMS distance convention), emitting d_attrs["issues"].
        # At D=2 every quantity below is arithmetically identical to the
        # 2D path (rms factor = 1.0 exactly; vectors == ideology), so the
        # reduction is bit-exact. Legacy scenarios (no issue runtime)
        # never enter this branch.
        from ..core.issues import issues_of, rms_distance
        my_issues = issues_of(agent, env)
        my_ide = my_issues if my_issues is not None else agent.state.ideology
        # Phase 8b M1: per-agent epsilon heterogeneity (engaged-partisan
        # fat-tail; Taber & Lodge 2006). Falls back to the rule's
        # `self.epsilon` for any scenario that doesn't seed per-agent
        # epsilon — bit-identical to Phase 8a behaviour for the pillar.
        epsilon = float(agent.state.attrs.get("epsilon", self.epsilon))
        # Web-demo sandbox "open-mindedness" dial: a global confidence-radius
        # scale read from the environment (applied to both the hard-cutoff and
        # graded branches, and to cohort-replaced agents since it's read at
        # apply-time). Default 1.0 is exact in IEEE-754 → bit-identical for the
        # pillar and canonical Hegselmann-Krause tests, which never set it.
        epsilon *= float(env.attrs.get("bc_epsilon_scale", 1.0))
        if self.temperature <= 0.0:
            # Canonical hard-cutoff Hegselmann-Krause. Default; HK
            # replication path. The affect modulator is a feature of
            # the graded filter only — surface the misconfiguration
            # rather than silently ignoring it.
            if affect_weight > 0.0:
                raise ValueError(
                    "BoundedConfidenceInfluence: affect_weight > 0 requires "
                    "temperature > 0 (affect feedback applies on the graded "
                    "filter, not the hard-cutoff branch). Set temperature "
                    "before enabling affect_weight."
                )
            if my_issues is not None:
                within = [
                    n.state.attrs["issues"]
                    for n in neighbours
                    if rms_distance(my_issues, n.state.attrs["issues"]) <= epsilon
                ]
            else:
                within = [
                    n.state.ideology
                    for n in neighbours
                    if np.linalg.norm(my_ide - n.state.ideology) <= epsilon
                ]
            if not within:
                return StateDelta()
            target = np.mean(within, axis=0)
        else:
            # Graded logistic filter — pillar opt-in (Phase 4 F2).
            if my_issues is not None:
                positions = np.array([n.state.attrs["issues"] for n in neighbours])
                ds = rms_distance(positions, my_issues)
            else:
                positions = np.array([n.state.ideology for n in neighbours])
                ds = np.linalg.norm(positions - my_ide, axis=1)
            # Clip the exponent to keep np.exp safe under extreme params
            # (e.g. tiny temperature). Logistic saturates well before 50;
            # this is a numerical-safety guard, not a behavioural change.
            arg = np.clip((ds - epsilon) / self.temperature, -50.0, 50.0)
            ws = 1.0 / (1.0 + np.exp(arg))
            # Phase 5 (A4): affect modulator. For each out-party
            # neighbour, multiply the logistic weight by
            # (1 + affect_weight * warmth_toward_their_party), clipped
            # to [0.1, 2.0]. Same-party neighbours: multiplier 1.0.
            # affect_weight = 0.0 → ms is all 1.0 → no behavioural change
            # (the multiplication is a pure scalar 1.0, leaving ws
            # bit-identical to the Phase 4 path).
            if affect_weight > 0.0:
                own_affect = agent.state.attrs.get("affect") or {}
                own_party = agent.state.attrs.get("party")
                ms = np.empty(len(neighbours))
                for k, n in enumerate(neighbours):
                    other = n.state.attrs.get("party")
                    if other is None or other == own_party:
                        ms[k] = 1.0
                    else:
                        # Underlying affect can drift past [-1, 1] —
                        # AffectiveUpdate accumulates additively. Clip
                        # the read here to keep the modulator's range
                        # interpretable; the [0.1, 2.0] outer clip is a
                        # numerical safety net, this is the model clip.
                        warmth = float(np.clip(
                            own_affect.get(other, 0.0), -1.0, 1.0
                        ))
                        m = 1.0 + affect_weight * warmth
                        ms[k] = float(np.clip(m, 0.1, 2.0))
                ws = ws * ms
            wsum = float(ws.sum())
            if wsum < 1e-9:
                return StateDelta()
            target = (ws[:, None] * positions).sum(axis=0) / wsum
        d = self.strength * (target - my_ide)
        # F1: Friedkin-Johnsen scaling — stubborn agents move less.
        s = float(agent.state.attrs.get("stubbornness", 0.0))
        if my_issues is not None:
            return StateDelta(d_attrs={"issues": (1.0 - s) * d})
        return StateDelta(d_ideology=(1.0 - s) * d)
