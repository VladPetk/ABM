"""Intervention type — a named, absolute bundle of strength changes that
advances a pillar by one stage (or layers in a free-play change). The
bundle is applied to a pre-built superset engine; structural changes (the
exposure provider in Phase 3) go through the optional `setup` callable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

# One parameter change: (rule class name, attribute name, value).
ParamChange = tuple[str, str, float]


@dataclass(frozen=True)
class Intervention:
    id: str
    label: str
    description: str
    param_bundle: tuple[ParamChange, ...]
    label_kind: str = "illustrative"        # "control" | "replication" | "illustrative"
    citation: str = ""
    predicted_effect: str = ""
    setup: Optional[Callable] = None        # structural change; None for S0-S3


def apply_intervention(engine, intervention: Intervention) -> None:
    """Apply an Intervention's bundle to an engine. Raises on any mismatch
    (missing rule class, missing attribute, duplicate rule instances)."""
    by_class: dict[str, object] = {}
    for rule in list(engine.rules.rules) + list(engine.env_rules):
        name = type(rule).__name__
        if name in by_class:
            raise ValueError(f"pipeline has two {name} instances")
        by_class[name] = rule
    for cls_name, attr, value in intervention.param_bundle:
        rule = by_class.get(cls_name)
        if rule is None:
            raise KeyError(f"{intervention.id}: no {cls_name} in pipeline")
        if not hasattr(rule, attr):
            raise AttributeError(f"{intervention.id}: {cls_name}.{attr} missing")
        setattr(rule, attr, value)
    if intervention.setup is not None:
        intervention.setup(engine)
