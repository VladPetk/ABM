"""
State containers — extensible by design.

AgentState holds the canonical ideology vector plus an open `attrs` dict so
scenarios can add fields (party affiliation, stubbornness, media diet, ...)
without modifying the base class.

EnvState mirrors that pattern for the world (party positions, media events,
institutional pressure, ...).

StateDelta is what every Rule returns. Deltas are summed across the rule
pipeline and then applied synchronously, so rule order doesn't bias dynamics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class AgentState:
    ideology: np.ndarray
    attrs: dict[str, Any] = field(default_factory=dict)

    def copy(self) -> AgentState:
        return AgentState(ideology=self.ideology.copy(), attrs=dict(self.attrs))


@dataclass
class EnvState:
    attrs: dict[str, Any] = field(default_factory=dict)


@dataclass
class StateDelta:
    d_ideology: np.ndarray = field(default_factory=lambda: np.zeros(2))
    d_attrs: dict[str, Any] = field(default_factory=dict)
