"""Pillar type — an ordered list of Interventions over a single superset
engine. Cold mode (validation) uses `build_at_stage`; live mode (journey)
applies interventions sequentially to a running engine via
`apply_intervention`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .intervention import Intervention, apply_intervention


@dataclass(frozen=True)
class Pillar:
    id: str
    title: str
    build_engine: Callable[[int], "Engine"]    # seed -> fresh superset engine, all forces off
    interventions: tuple[Intervention, ...]    # ordered: S0, S1, ...


def build_at_stage(pillar: Pillar, stage_index: int, seed: int) -> "Engine":
    """Cold mode: fresh engine with stage `stage_index`'s cumulative bundle
    applied. Not stepped — caller runs it."""
    engine = pillar.build_engine(seed)
    apply_intervention(engine, pillar.interventions[stage_index])
    return engine
