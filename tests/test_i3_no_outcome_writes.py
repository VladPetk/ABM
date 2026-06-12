"""MHV S3 — Invariant I3 enforcement.

I3 (mhv_spec.md §2): no event handler or rule writes outcome variables
(``affect`` / ``issues`` / ``ideology`` / alignment metrics) directly; exogenous
influence enters only via typed input channels (data-fed series + the
declarative ``shocks.py`` channel).

This lint walks every ``_event_*`` / ``_decade_*`` handler in
``historical_arc.py`` and flags any assignment whose target is an outcome
variable. The sanctioned channels (``DataFedSeries`` consumers, ``shocks.py``
applicators) are exempt by construction — they are not bespoke arc handlers.

T3.4 made this a **hard guard**: the Obama-2008 warmth handler (the only direct
``affect`` write in an arc handler) was dropped (D-S3-2). The 2016 status-threat
write targets ``perceived_threat`` — a *mechanism input* to ThreatDecay, not an
I3 outcome variable — so it is out of this lint's scope (its migration to the
declarative shock channel is deferred; see methods §5.24).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

import abm.pillars.historical_arc as arc

OUTCOME_VARS = {"affect", "issues", "ideology", "identity_alignment", "aff_out"}


def _outcome_target(target: ast.AST) -> str | None:
    """Return the offending outcome-variable name if ``target`` writes one."""
    if isinstance(target, ast.Subscript):
        # e.g. affect[other_party] = ...   (base Name is an outcome var)
        if isinstance(target.value, ast.Name) and target.value.id in OUTCOME_VARS:
            return target.value.id
        # e.g. a.state.attrs["affect"] = ...  (string-literal slice)
        sl = target.slice
        if isinstance(sl, ast.Constant) and sl.value in OUTCOME_VARS:
            return str(sl.value)
    if isinstance(target, ast.Attribute) and target.attr in OUTCOME_VARS:
        # e.g. a.state.ideology = ...
        return target.attr
    return None


def _scan_handlers() -> list[tuple[str, int, str]]:
    src = Path(arc.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    violations: list[tuple[str, int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if not (node.name.startswith("_event_") or node.name.startswith("_decade_")):
            continue
        for sub in ast.walk(node):
            targets = []
            if isinstance(sub, ast.Assign):
                targets = sub.targets
            elif isinstance(sub, ast.AugAssign):
                targets = [sub.target]
            for t in targets:
                hit = _outcome_target(t)
                if hit is not None:
                    violations.append((node.name, sub.lineno, hit))
    return violations


def test_no_direct_outcome_writes_in_arc_handlers():
    violations = _scan_handlers()
    assert not violations, (
        "I3 violation — outcome variable written directly in an arc handler:\n"
        + "\n".join(f"  {fn} (line {ln}): writes {var!r}" for fn, ln, var in violations)
    )
