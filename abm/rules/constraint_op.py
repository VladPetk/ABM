"""ConstraintOp — emergent belief-system constraint (the MHV S2 core rule).

Productionizes the S1 pilot's validated operator (scripts/audit/
pilot_cov_signature.py::op_constraint, blessed PASS 2026-06): for each
agent, build the NETWORK-LOCAL consensus direction u_a (normalized mean of
network neighbours' issue vectors) and pull the agent's own issue vector
toward its projection onto that axis:

    v_a += rate * ((v_a · u_a) u_a − v_a)

This is the oil-spill mechanism (DellaPosta 2020): within-person
cross-issue spread collapses onto a locally shared line, raising
inter-attitude correlation (Kozlowski & Murphy 2021) and lowering the
effective dimensionality — *because neighbours reinforce package deals*,
not because anyone is pulled toward a party centroid. The hard anti-
confound property carried over from the pilot (review_math §A2 caveat ii,
enforced by an AST guard in tests): the executable body references **no
party / centroid / corner target**. An agent already on its local axis
does not move, however far it sits from the neighbourhood mean — the
operator is correlation-inducing, never position-herding. Self-
reinforcement is the point: as vectors align, u_a sharpens, which aligns
vectors further. What bounds the collapse (the runaway-to-rank-1 risk,
roadmap §6): the FJ anchor pull toward weakly-correlated 1980 seeds, BC
averaging, and this rule's own dispersion counterweight —

**Residual noise**: per-item Gaussian noise projected onto the block-
RESIDUAL space (its block means are removed), so it disperses items
*within* blocks without moving the compass projection at all. At D=2
every block has one item, the residual space is empty, and the term is
exactly zero — I1-safe by construction. This is the item-level
idiosyncratic noise deliberately deferred from T2.2: it is part of the
collapse/dispersion balance, not of the axis-level GaussianNoise.

Replaces (in emergent mode): `IdentitySorting`'s mean-field operator +
`IDENTITY_SORTING_SCHEDULE` + the ×5 regrade multiplier +
`PARTY_ISSUE_COUPLING_SCHEDULE` — the ~83%-schedule-carried alignment
spine the knob audit flagged. `rate` is a fitted quantity (prior centered
on the B&G/Kozlowski constraint slope; S4 calibrates). Provenance:
**L** (mechanism: DellaPosta 2020; Boutyline & Vaisey 2017) /
**N** (the operator form and rate value).

Native issues-mode only: without the issue substrate the rule is a strict
no-op (and consumes no rng), so every legacy path is bit-identical.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.issues import issues_of
from ..core.network import neighbor_agents
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


class ConstraintOp:
    def __init__(self, rate: float = 0.0, resid_sigma: float = 0.0):
        self.rate = float(rate)
        self.resid_sigma = float(resid_sigma)

    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta:
        if self.rate <= 0.0 and self.resid_sigma <= 0.0:
            return StateDelta()
        v = issues_of(agent, env)
        if v is None:
            return StateDelta()
        rt = env.attrs["issue_runtime"]
        D = rt["D"]

        d = np.zeros(D)
        if self.rate > 0.0:
            neighbours = neighbor_agents(agent, space, env)
            if neighbours:
                m = np.mean([n.state.attrs["issues"] for n in neighbours],
                            axis=0)
                nrm = float(np.linalg.norm(m))
                if nrm > 1e-9:
                    u = m / nrm
                    proj = float(v @ u) * u
                    d = self.rate * (proj - v)

        if self.resid_sigma > 0.0 and D > 2:
            from ..core.issues import lift, project1
            eta = rng.normal(0.0, self.resid_sigma, size=D)
            eta = eta - lift(project1(eta, rt), rt)   # block means removed
            d = d + eta

        if not d.any():
            return StateDelta()
        # F1: Friedkin-Johnsen scaling — stubborn agents move less.
        s = float(agent.state.attrs.get("stubbornness", 0.0))
        return StateDelta(d_attrs={"issues": (1.0 - s) * d})
