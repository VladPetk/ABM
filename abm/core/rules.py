"""
Rule protocol and pipeline composition.

A Rule reads the current world (agent + space + env) and returns a StateDelta.
Rules MUST NOT mutate anything — the engine sums deltas across the pipeline
and applies them synchronously, so order doesn't bias dynamics.

Attr-delta merging supports:
- numeric + numeric → additive (e.g. cumulative affect change)
- ndarray + ndarray → elementwise additive (identity drift, etc.)
- dict + dict → key-wise recursive merge (affect by party id, etc.)
- anything else → replace
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np

from .agent import Agent
from .environment import Environment
from .space import ContinuousSpace2D
from .state import StateDelta


@runtime_checkable
class Rule(Protocol):
    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta: ...


@runtime_checkable
class EnvRule(Protocol):
    """World-level rule. Runs once per tick *before* agent rules — can mutate
    env state and (deliberately) agent state directly, modeling external
    forces like elite cues, media shocks, or institutional events."""

    def apply(
        self,
        env: Environment,
        agents: list[Agent],
        space: ContinuousSpace2D,
        rng: np.random.Generator,
        tick: int,
    ) -> None: ...


def merge_attr(existing, new):
    """Combine two attr-delta values. Used both when summing rule outputs
    and when applying the total delta to the agent state."""
    if isinstance(new, (int, float)) and isinstance(existing, (int, float)):
        return existing + new
    if isinstance(new, np.ndarray) and isinstance(existing, np.ndarray):
        return existing + new
    if isinstance(new, dict) and isinstance(existing, dict):
        merged = dict(existing)
        for k, v in new.items():
            merged[k] = merge_attr(merged.get(k), v) if k in merged else v
        return merged
    return new


class RulePipeline:
    def __init__(self, rules: list[Rule]):
        self.rules = list(rules)

    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta:
        total = StateDelta()
        for rule in self.rules:
            d = rule.apply(agent, space, env, rng)
            total.d_ideology = total.d_ideology + d.d_ideology
            for k, v in d.d_attrs.items():
                total.d_attrs[k] = merge_attr(total.d_attrs.get(k), v) if k in total.d_attrs else v
        return total
