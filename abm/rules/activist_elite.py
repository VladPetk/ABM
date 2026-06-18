"""
Activist-elite cue — endogenous elite divergence (emergence-recovery E1).

Each tick, each party's elite position **emerges** from its **activist tail**
(the extreme, intensity-weighted minority of the party — distinct from, and more
extreme than, the centroid), passed through a **saturating ceiling** that bounds
the feedback loop to a stable interior fixed point. The elite is written to
``env.attrs["parties"][p]`` and the per-tick shift is propagated to every agent's
``party_cue`` (the quantity ``PartyPull`` reads) — structurally mirroring
:class:`abm.pillars.inputs.PartyCentroidSeries`, except the cue is **generated
from the mass**, not fed from a data series. That closes the endogenous loop::

    mass -> activist tail -> elite -> cue -> (PartyPull) mass -> ...

so positional sorting **amplifies** a small seed rather than replaying fed data.
Elites track the activist tail, not the median voter (Bawn et al. 2012,
*A Theory of Political Parties*; Hacker & Pierson; Zaller receive-accept-sample).
The mass-elite **gap** (mass lags elite) and the bipolarization both emerge;
nothing positional is fed.

Reads (per agent): ``ideology`` (2D position), ``party``, ``identity_strength``,
``party_cue``. Writes: ``env.attrs["parties"][p]`` and each agent's ``party_cue``.

Provenance: **L** (Bawn / Hacker-Pierson / Zaller mechanism) + **N** (functional
form — intensity-weighted tail mean, leapfrog gain, ``tanh`` ceiling; the
load-bearing form was feasibility-mapped at E0, see
``docs/internal/audit/e0_loop_feasibility.md``).
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D


class ActivistEliteCue:
    """EnvRule. Endogenous elite cue from each party's activist tail.

    - ``tail_q``: fraction of each party taken as the activist tail (most extreme
      along the party's own direction).
    - ``gain``: elite leapfrog over the centroid toward the tail (``> 1`` leads).
    - ``ceiling``: saturating elite extremity (the bounding nonlinearity — keeps
      the loop in a stable, partial, non-runaway regime; E0).
    - ``intensity_weight``: weight the tail mean by ``identity_strength``
      (the organized/intense activists carry the cue).
    """

    def __init__(
        self,
        tail_q: float = 0.10,
        gain: float = 2.5,
        ceiling: float = 0.65,
        intensity_weight: bool = True,
        endo_mob_gain: float = 0.0,
    ):
        self.tail_q = float(tail_q)
        self.gain = float(gain)
        self.ceiling = float(ceiling)
        self.intensity_weight = bool(intensity_weight)
        # R-phase R8 — ENDOGENOUS mobilization feedback (the genuine fed→earned
        # lever). The leapfrog gain is `gain · mob`, where `mob` is the EXOGENOUS
        # activist-mobilization schedule (low in 1980 → loop quiescent → low
        # emergent floor). R8 adds an endogenous term: as a party's mass sorts
        # (its centroid extremity along the realignment axis grows), the base
        # SELF-mobilizes — the empirically-real polarization spiral (Mason 2018;
        # the activist base grows with sorting), independent of the exogenous
        # schedule. So `mob_eff = mob_exo + endo_mob_gain · max(0, cent·dir)`.
        # Because this reads the CURRENT (unfrozen) sorting state, it keeps
        # self-reinforcing even when the budget freezes the exogenous drivers →
        # it RAISES the emergent (free_flowing) fraction of party_sep, the share
        # that survives with every fed driver removed. Default 0.0 → no endo
        # term → bit-identical. Provenance: L (self-reinforcing mobilization /
        # polarization spiral) + N (the functional form, gain).
        self.endo_mob_gain = float(endo_mob_gain)

    def apply(
        self,
        env: Environment,
        agents: list[Agent],
        space: ContinuousSpace2D,
        rng: np.random.Generator,
        tick: int,
    ) -> None:
        # Honesty-budget instrument (emergence-recovery E5.2): when the budget
        # harness pins the loop, the elite stays at its 1980 seed and no shift is
        # propagated to party_cue. This is the loop-OFF counterfactual that
        # measures the loop-attributable (emergent) fraction of party_sep.
        if env.attrs.get("_freeze_endogenous_loop"):
            return
        parties = env.attrs.get("parties")
        if not parties:
            return
        # Emergence-recovery E3 — per-party activist mobilization scales the
        # elite leapfrog: the institutional capacity of each party's activist /
        # donor base, the exogenous forcing the loop responds to (ramped over
        # time by the dated events; low in 1980 keeps the loop quiescent).
        # Absent → 1.0 → bit-identical to E2 (the fixed-gain loop).
        mob = env.attrs.get("activist_mobilization")
        # Group only the driven parties (Independents carry no centroid channel,
        # mirroring PartyCentroidSeries — they are left alone).
        members: dict = {pid: [] for pid in parties}
        for a in agents:
            p = a.state.attrs.get("party")
            if p in members:
                members[p].append(a)

        # Each party's amplification AXIS is fixed at the first tick (its initial
        # 1980 centroid direction = the historical realignment direction, D-left /
        # R-right) and reused thereafter. Anchoring the direction is what makes
        # the loop reliably IGNITE rather than bifurcate on the seed: real
        # polarization had a given direction and an emergent magnitude, not a
        # coin-flip direction. Without this the near-origin live centroid gives a
        # noisy direction → some seeds fizzle, some ignite (sep variance ±0.3).
        axes = env.attrs.get("party_axis")
        if axes is None:
            axes = {}
            env.attrs["party_axis"] = axes

        step: dict = {}
        for pid, mem in members.items():
            if not mem:
                continue
            pos = np.array([a.state.ideology for a in mem], dtype=float)
            cent = pos.mean(0)
            if pid not in axes:
                # Realignment direction = the frozen partisan-gap axis (align_u),
                # projected to 2D; R = +axis, D = -axis. This is the established
                # D-R direction from the ANES party moments (right cultural SIGN —
                # D progressive), unlike the noisy/early 1980 mass centroid whose
                # cultural component is spurious. Falls back to the centroid dir.
                base = None
                rt = env.attrs.get("issue_runtime")
                au = rt.get("align_u") if rt else None
                if au is not None:
                    from ..core.issues import project1
                    d2 = np.asarray(project1(np.asarray(au, dtype=float), rt), dtype=float)
                    n2 = float(np.linalg.norm(d2))
                    if n2 > 1e-9:
                        base = d2 / n2
                if base is not None:
                    axes[pid] = (base if pid == 1 else -base).tolist()
                else:
                    nrm0 = float(np.linalg.norm(cent))
                    axes[pid] = ((cent / nrm0).tolist() if nrm0 > 1e-9
                                 else ([1.0, 0.0] if pid == 1 else [-1.0, 0.0]))
            dirv = np.asarray(axes[pid], dtype=float)
            proj = pos @ dirv                       # extremity along the party direction
            if self.intensity_weight:
                w = np.array(
                    [float(a.state.attrs.get("identity_strength", 0.5)) for a in mem])
            else:
                w = np.ones(len(mem))
            k = max(1, int(np.ceil(self.tail_q * len(mem))))
            idx = np.argsort(proj)[-k:]             # the activist tail
            wsum = float(w[idx].sum())
            if wsum <= 0:
                tail_mean = pos[idx].mean(0)
            else:
                tail_mean = np.average(pos[idx], axis=0, weights=w[idx])
            mob_exo = float(mob.get(pid, 1.0)) if mob else 1.0
            # R8 — endogenous self-mobilization: the party's current sorting
            # (centroid extremity along its realignment axis) feeds back into the
            # mobilization, so the loop self-sustains independent of the exogenous
            # schedule. max(0, …) so a party on the wrong side isn't mobilized.
            mob_eff = mob_exo
            if self.endo_mob_gain > 0.0:
                endo = max(0.0, float(cent @ dirv))
                mob_eff = mob_exo + self.endo_mob_gain * endo
            g = self.gain * mob_eff
            raw = cent + g * (tail_mean - cent)
            # Saturating elite ceiling — the bounding nonlinearity (E0).
            elite = self.ceiling * np.tanh(raw / self.ceiling)
            old = np.asarray(parties[pid], dtype=float)
            parties[pid] = elite
            step[pid] = elite - old

        # Propagate the elite shift to each agent's party_cue, preserving the
        # agent's fixed personal offset (so a party translates toward its elite
        # while keeping its within-party spread). Same coupling EliteDrift /
        # PartyCentroidSeries carried.
        for a in agents:
            cue = a.state.attrs.get("party_cue")
            if cue is None:
                continue
            p = a.state.attrs.get("party")
            if p not in step:
                continue
            a.state.attrs["party_cue"] = np.clip(cue + step[p], -1.0, 1.0)
        env.attrs.setdefault("viz", {})["party_centers"] = parties
