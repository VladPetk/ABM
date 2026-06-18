"""ThermostaticFeedback (R-phase R6) — two-signed negative feedback on the
party-separation overshoot (Wlezien 1995; Erikson-MacKuen-Stimson 2002).

The economic common-mode (#9) is a FED thermostatic forcing on the society LEVEL.
R6 instead makes a genuine FEEDBACK on the DIFFERENTIAL: when the party-centroid
separation overshoots a `reference`, the public reacts against the extremity and
both party clouds drift back toward their midpoint; below the reference they drift
apart toward it — a homeostat around `reference`. Because it is a rigid per-party
translation toward/away from the midpoint, it moves the centroid SEPARATION
without collapsing within-party spread (validated in the isolation test).

It is applied every tick as a counter-push, so it sets a reduced equilibrium
separation by balancing against the polarizing forces (PartyPull / the loop): in
a high-forcing regime the polarizing forces win, in a low-forcing regime the
thermostat dominates and depolarizes — genuinely two-sided.

Provenance: **L** (thermostatic / negative-feedback mechanism) + **N** (the
functional form) + **E** (applying the policy-mood thermostat to party_sep itself,
and the gain). GATED: installed only when `thermostatic_gain > 0` → otherwise not
in the pipeline → bit-identical to head.
"""
from __future__ import annotations

import numpy as np


def _party_centroid(agents, party_id):
    vals = [a.state.ideology for a in agents
            if a.state.attrs.get("party") == party_id]
    return np.mean(vals, axis=0) if vals else None


class ThermostaticFeedback:
    """EnvRule. Restore party-centroid separation toward `reference` each tick."""

    def __init__(self, gain: float = 0.0, reference: float = 0.6,
                 max_step: float = 0.05):
        self.gain = float(gain)
        self.reference = float(reference)
        self.max_step = float(max_step)

    def apply(self, env, agents, space, rng, tick: int) -> None:
        if self.gain <= 0.0:
            return
        c0 = _party_centroid(agents, 0)
        c1 = _party_centroid(agents, 1)
        if c0 is None or c1 is None:
            return
        c0 = np.asarray(c0, dtype=float)
        c1 = np.asarray(c1, dtype=float)
        sep = float(np.linalg.norm(c0 - c1))
        # f > 0 when over-shooting the reference → contract toward the midpoint;
        # f < 0 below it → expand toward the reference. Clipped for stability.
        f = float(np.clip(self.gain * (sep - self.reference),
                          -self.max_step, self.max_step))
        if abs(f) < 1e-12:
            return
        mid = 0.5 * (c0 + c1)
        shift = {0: f * (mid - c0), 1: f * (mid - c1)}  # 2D per-party translation

        rt = env.attrs.get("issue_runtime")
        if rt is not None:
            from ..core.issues import lift, project1
            bump = {0: lift(shift[0], rt), 1: lift(shift[1], rt)}
            for a in agents:
                p = a.state.attrs.get("party")
                if p not in (0, 1):
                    continue
                v = a.state.attrs.get("issues")
                if v is not None:
                    a.state.attrs["issues"] = np.clip(v + bump[p], -1.0, 1.0)
                    a.state.ideology = project1(a.state.attrs["issues"], rt)
                else:
                    a.state.ideology = a.state.ideology + shift[p]
        else:
            for a in agents:
                p = a.state.attrs.get("party")
                if p in (0, 1):
                    a.state.ideology = a.state.ideology + shift[p]
