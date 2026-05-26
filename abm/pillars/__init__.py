"""Pillar abstraction — ordered, staged journeys layered on a single
superset engine. See `pillar_engine_roadmap.md` for the design.

Phase 6 adds the public-facing intervention library
(`interventions_phase6`); see `phase6_spec.md` §5.
"""
from .calm_to_camps import PILLAR
from .intervention import Intervention, ParamChange, apply_intervention
from .interventions_phase6 import (
    INTERVENTIONS_PHASE6,
    X1_SHOW_OTHER_SIDE,
    X2_FIX_ALGORITHM,
    X3_QUIT_CABLE_NEWS,
    X4_BIPARTISAN_DIALOGUE,
    X5_RANKED_CHOICE_VOTING,
    X6_SHARED_INSTITUTIONS,
)
from .pillar import Pillar, build_at_stage

__all__ = [
    "Intervention",
    "ParamChange",
    "apply_intervention",
    "Pillar",
    "build_at_stage",
    "PILLAR",
    "INTERVENTIONS_PHASE6",
    "X1_SHOW_OTHER_SIDE",
    "X2_FIX_ALGORITHM",
    "X3_QUIT_CABLE_NEWS",
    "X4_BIPARTISAN_DIALOGUE",
    "X5_RANKED_CHOICE_VOTING",
    "X6_SHARED_INSTITUTIONS",
]
