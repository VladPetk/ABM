"""
Environment — world-level state shared by all agents.

Like AgentState, kept open via an `attrs` dict so a scenario can stash
arbitrary structure (party list, active media event, institutional positions)
without changing the type.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Environment:
    attrs: dict[str, Any] = field(default_factory=dict)
