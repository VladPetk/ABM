"""
Agent — a thin holder of identity and state.

Deliberately behavior-free: dynamics live in Rules, not on the agent. This
keeps the data model decoupled from any particular interaction model and lets
us swap or compose behaviors without subclassing.
"""
from __future__ import annotations

from dataclasses import dataclass

from .state import AgentState


@dataclass
class Agent:
    id: int
    state: AgentState
