"""
Gaussian noise — small random ideological drift each tick.

Keeps the system from freezing at brittle equilibria and models the fact
that real opinion shifts aren't purely driven by social pressure.

Phase 4 (F1, Friedkin-Johnsen anchoring): this rule also carries the
anchor pull. The FJ recurrence wants the anchor term applied once per
tick regardless of how many other rules fire; pinning it to
``GaussianNoise`` — which is on in every pillar stage including S0 —
keeps it order-independent. Agents without a ``stubbornness`` attr or
without an ``anchor`` attr (every existing non-pillar scenario) bypass
the FJ logic entirely, so canonical / ACTB / compass behaviour is
unchanged.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.issues import issues_of, lift
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


class GaussianNoise:
    def __init__(
        self,
        sigma: float = 0.01,
        sigma_y: float | None = None,
        rho: float = 0.0,
    ):
        self.sigma = sigma
        # Phase 9 §11.4 — optional anisotropic σ_y. None preserves
        # current isotropic behavior bit-identically. When set, the
        # y-axis noise component uses sigma_y while x uses sigma.
        # Audit `phase9_axis_symmetry_audit.md §6` calls this a
        # "band-aid" because the variance lift has no semantic
        # content — agents drift on y for reasons unconnected to
        # identity/faction/media/perception. Documented honestly.
        # Empirically this IS the path that escapes BC compression
        # because the per-tick noise is uncorrelated and BC averages
        # neighbors (which preserves the variance injection).
        self.sigma_y = sigma_y
        # Phase 9 §11.7-D5 — optional ρ-correlated noise on (x, y).
        # Default 0.0 preserves the head behaviour (independent draws).
        # When set, the y-axis component is drawn from a Cholesky'd
        # 2D Gaussian: noise_y = σ_y · (ρ·u + √(1-ρ²)·v) where u, v are
        # independent N(0, 1) and σ_x · u is the x-axis component.
        # ANES corr+0.76 at 2020 needs ρ ≈ 0.5-0.7 to tilt the
        # equilibrium distribution into the NE-SW diagonal.
        self.rho = float(rho)

    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta:
        s = float(agent.state.attrs.get("stubbornness", 0.0))
        anchor = agent.state.attrs.get("anchor")
        # MHV S2 T2.2 — native D-dim path. Noise stays an AXIS-level
        # draw lifted onto the items (same rng consumption as the 2D
        # path — the sigma is calibrated as axis dispersion; item-level
        # idiosyncratic noise is a T2.3 design question, part of the
        # bounded-collapse dynamics). The FJ anchor pull goes native:
        # agents anchor to their initial ITEM positions
        # (attrs["anchor_issues"], seeded at build/replacement). At D=2
        # lift is the identity and anchor_issues equals the 2D anchor,
        # so the reduction is bit-exact.
        _v = issues_of(agent, env)
        if _v is not None:
            anchor = agent.state.attrs.get("anchor_issues")
        # Phase 8b M1: per-agent fj_alpha heterogeneity (engaged
        # partisans more anchored; Achen & Bartels 2016). Falls back
        # to env-level fj_alpha if per-agent not set — bit-identical
        # to Phase 8a for the pillar.
        alpha = float(agent.state.attrs.get(
            "fj_alpha", env.attrs.get("fj_alpha", 0.0)
        ))
        fj_active = s > 0.0 and anchor is not None and alpha > 0.0

        # Anisotropic skip-check: only short-circuit when BOTH sigmas
        # are zero (otherwise we'd miss y-only noise).
        _sy_active = (self.sigma_y is not None and float(self.sigma_y) > 0.0)
        if self.sigma <= 0 and not _sy_active:
            if not fj_active:
                return StateDelta()
            # Anchor pull still fires even when noise is off — F1 is
            # structural, not noise-coupled.
            if _v is not None:
                return StateDelta(
                    d_attrs={"issues": alpha * s * (anchor - _v)})
            return StateDelta(
                d_ideology=alpha * s * (anchor - agent.state.ideology)
            )

        sx = float(self.sigma)
        sy = float(self.sigma_y) if self.sigma_y is not None else sx
        if self.rho == 0.0:
            if self.sigma_y is None:
                noise = rng.normal(0.0, self.sigma, size=2)
            else:
                noise = np.array([
                    rng.normal(0.0, self.sigma),
                    rng.normal(0.0, float(self.sigma_y)),
                ])
        else:
            # Phase 9 §11.7-D5: ρ-correlated draw via Cholesky.
            u = rng.normal(0.0, 1.0)
            v = rng.normal(0.0, 1.0)
            r = self.rho
            noise = np.array([
                sx * u,
                sy * (r * u + float(np.sqrt(max(0.0, 1.0 - r * r))) * v),
            ])
        if _v is not None:
            rt = env.attrs["issue_runtime"]
            if not fj_active:
                return StateDelta(d_attrs={"issues": lift(noise, rt)})
            return StateDelta(d_attrs={"issues": (
                lift((1.0 - s) * noise, rt) + alpha * s * (anchor - _v))})
        if not fj_active:
            return StateDelta(d_ideology=noise)
        # Brownian motion scales with mobility (1 - s); anchor pull adds
        # to it. Stubborn agents jitter less and decay toward their
        # innate position.
        return StateDelta(
            d_ideology=(1.0 - s) * noise + alpha * s * (anchor - agent.state.ideology)
        )
