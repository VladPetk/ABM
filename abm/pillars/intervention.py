"""Intervention type — a named, absolute bundle of strength changes that
advances a pillar by one stage (or layers in a free-play change). The
bundle is applied to a pre-built superset engine; structural changes go
through the optional ``setup`` callable.

Honesty schema:

- ``label_kind`` describes the *type* of intervention: ``"control"``,
  ``"replication"``, or ``"illustrative"`` for the pillar stages
  S0-S4; ``"intervention"`` for the Phase 6 X-library.
- ``expected_naive_effect`` is the intuitive expectation a lay observer
  would have. The Δ between this and ``predicted_effect`` is the
  educational payoff of the Phase 6 library.
- Phase 7 ``effect_buckets`` carries the **§11 measurement-blessed**
  per-axis labels for X-interventions. Two axes:
  ``"issue_sorting"`` (Δparty_separation) and ``"affect"``
  (Δaffective_polarization). Each axis's value is one of
  ``"null"`` / ``"partial"`` / ``"real"`` / ``"backfire"``. Pillar
  stages S0-S4 leave this empty.

The two-axis schema (Phase 7) replaces Phase 6's single-axis
``label_kind`` repurposing. The literature treats issue sorting and
affective polarization as distinct outcomes (Iyengar et al. 2019;
Gidron, Adams & Horne 2020; Pettigrew & Tropp 2006), so the schema
follows.

``apply_intervention`` itself is unchanged: it reads ``param_bundle``
and calls ``setup``. The new fields are metadata for downstream readers
(the eventual web layer).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

# One parameter change: (rule class name, attribute name, value).
ParamChange = tuple[str, str, float]


@dataclass(frozen=True)
class Intervention:
    id: str
    label: str
    description: str
    param_bundle: tuple[ParamChange, ...]
    # Type tag. Allowed values:
    #   "control" | "replication" | "illustrative"     (pillar stages S0-S4)
    #   "intervention"                                  (Phase 6 X-library)
    label_kind: str = "illustrative"
    citation: str = ""
    predicted_effect: str = ""
    # Phase 6 R4: the intuitive expectation a naive observer would have
    # about an intervention. Optional — pillar stages (S0-S4) don't use it.
    expected_naive_effect: str = ""
    # Phase 7: per-axis bucket labels blessed by §11 measurement.
    # Keyed by axis name ("issue_sorting", "affect"); value in
    # {"null", "partial", "real", "backfire"}. Empty for pillar stages.
    effect_buckets: dict[str, str] = field(default_factory=dict)
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
