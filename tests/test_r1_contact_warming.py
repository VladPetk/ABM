"""R-phase R1 isolation test — contact→affect warming activation (gated).

The rule-level positive (warming) valence path is already pinned by
`test_phase8c_affect.py::test_positive_valence_on_coop_edge_above_threshold`.
This test pins the *build-level* activation added in R1: `contact_warming`
seeds cooperative cross-party edges (waking the otherwise-dead path) and the
warm threshold/magnitude overrides, and is a strict no-op when off.

See docs/internal/reversibility_spec.md (R1).
"""
from __future__ import annotations

import numpy as np

from abm.core.network import Network, mark_cross_party_cooperative
from abm.pillars.historical_arc import build_engine
from scripts.anes_preset import ANES_FULL_KWARGS


def _coop_edges(eng):
    return eng.env.attrs["network"]._cooperative


def _affect_rule(eng):
    rules = [r for r in eng.rules.rules if type(r).__name__ == "AffectiveUpdate"]
    assert rules, "AffectiveUpdate not found in pipeline"
    return rules[0]


def test_off_path_no_cooperative_edges():
    """Canonical build (contact_warming defaults off) marks zero cooperative
    edges → the warming path stays dead, exactly as head."""
    eng = build_engine(seed=0, **ANES_FULL_KWARGS)
    assert len(_coop_edges(eng)) == 0


def test_off_path_keeps_affectiveupdate_defaults():
    """Off path passes AffectiveUpdate's own defaults (-0.2 / 0.05) → bit-identical."""
    eng = build_engine(seed=0, **ANES_FULL_KWARGS)
    aff = _affect_rule(eng)
    assert aff.coop_positive_threshold == -0.2
    assert aff.coop_positive_magnitude == 0.05


def test_on_path_seeds_cross_party_cooperative_edges():
    k = dict(ANES_FULL_KWARGS)
    k.update(contact_warming=True, contact_coop_frac=0.5)
    eng = build_engine(seed=0, **k)
    coop = _coop_edges(eng)
    assert len(coop) > 0, "contact_warming should seed cooperative edges"
    party = {a.id: a.state.attrs["party"] for a in eng.agents}
    for (i, j) in coop:
        assert party[i] in (0, 1) and party[j] in (0, 1)
        assert party[i] != party[j], "cooperative edges must be cross-party"


def test_on_path_applies_threshold_and_magnitude_overrides():
    k = dict(ANES_FULL_KWARGS)
    k.update(contact_warming=True, contact_warm_threshold=-0.6,
             contact_warm_magnitude=0.07)
    eng = build_engine(seed=0, **k)
    aff = _affect_rule(eng)
    assert aff.coop_positive_threshold == -0.6
    assert aff.coop_positive_magnitude == 0.07


def test_on_path_sets_contact_share_floor():
    k = dict(ANES_FULL_KWARGS)
    k.update(contact_warming=True, contact_coop_share=0.3)
    eng = build_engine(seed=0, **k)
    assert eng.env.attrs["sandbox_contact_share"] >= 0.3


def test_mark_helper_noop_at_frac_zero():
    """The marking helper consumes nothing and marks nothing at frac 0
    (this is why the off path leaves net_rng untouched)."""
    net = Network({0: {1}, 1: {0}})

    class _A:
        def __init__(self, i, p):
            self.id = i
            self.state = type("S", (), {"attrs": {"party": p}})()

    agents = [_A(0, 0), _A(1, 1)]
    n = mark_cross_party_cooperative(net, agents, np.random.default_rng(0), 0.0)
    assert n == 0
    assert len(net._cooperative) == 0


def test_mark_helper_only_marks_cross_party():
    # 0-1 same party (Dem), 0-2 cross party (Dem-Rep); only 0-2 eligible.
    net = Network({0: {1, 2}, 1: {0}, 2: {0}})

    class _A:
        def __init__(self, i, p):
            self.id = i
            self.state = type("S", (), {"attrs": {"party": p}})()

    agents = [_A(0, 0), _A(1, 0), _A(2, 1)]
    n = mark_cross_party_cooperative(net, agents, np.random.default_rng(0), 1.0)
    assert n == 1
    assert (0, 2) in net._cooperative
    assert (0, 1) not in net._cooperative
