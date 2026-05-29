"""ProtectedPartyRealignment — let immune characters convert party by drift.

web_demo jumpiness companion to Step 2 (character immunity). Party can
otherwise only change through cohort replacement (a new person in the
slot); an agent flagged ``do_not_replace`` is one continuous person and so
could *never* switch party, even if their ideology drifts clear across the
divide. That makes a spotlighted "Linda becomes a Republican" arc
impossible to render coherently — she stays a Democrat-coloured dot sitting
in the opposite quadrant.

This rule lets a ``do_not_replace`` agent's party follow their *sustained*
economic position: once x has sat past ``±x_threshold`` (into the other
party's half) for ``sustain_ticks`` consecutive ticks, flip party/group,
remap the affect key to the new out-party, and re-aim ``party_cue`` at the
new party centroid so the conversion sticks rather than snapping back.

**Self-gating**: the rule only ever touches agents carrying
``do_not_replace``. Runs without protected agents (every pillar / Phase 8 /
Phase 9 scenario) are a strict no-op → bit-identical to head.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D


class ProtectedPartyRealignment:
    def __init__(self, x_threshold: float = 0.12, sustain_ticks: int = 6):
        # 6 ticks = 2 years at TICKS_PER_YEAR=3 — long enough that a noise
        # excursion across the line doesn't flip party, short enough that a
        # genuine drift converts within a couple years of crossing.
        self.x_threshold = float(x_threshold)
        self.sustain_ticks = int(sustain_ticks)

    def apply(
        self,
        env: Environment,
        agents: list[Agent],
        space: ContinuousSpace2D,
        rng: np.random.Generator,
        tick: int,
    ) -> None:
        parties = env.attrs.get("parties", {})
        for a in agents:
            if not a.state.attrs.get("do_not_replace"):
                continue
            party = a.state.attrs.get("party")
            if party not in (0, 1):
                continue
            x = float(a.state.ideology[0])
            other_side = (
                (party == 0 and x > self.x_threshold)
                or (party == 1 and x < -self.x_threshold)
            )
            cnt = int(a.state.attrs.get("_realign_count", 0))
            cnt = cnt + 1 if other_side else 0
            if cnt >= self.sustain_ticks:
                new_party = 1 - party
                a.state.attrs["party"] = new_party
                a.state.attrs["group"] = new_party
                aff = a.state.attrs.get("affect")
                if aff:
                    val = float(next(iter(aff.values())))
                    a.state.attrs["affect"] = {1 - new_party: val}
                cent = parties.get(new_party)
                if cent is not None:
                    a.state.attrs["party_cue"] = np.array(
                        [float(cent[0]), float(cent[1])]
                    )
                cnt = 0
            a.state.attrs["_realign_count"] = cnt
