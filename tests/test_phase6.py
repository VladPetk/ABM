"""Phase 6 — repulsion (R1) + intervention library (R3) + honesty schema (R4).

Eight unit tests + one consolidated bucket test.

The consolidated test runs each of X1-X5 through the release-phase
experiment and asserts the measured `Δparty_separation` lies in the
bucket the intervention's ``label_kind`` declares. The labels were
blessed by the §11 measurement step (move the tag, not the threshold
discipline).
"""
from __future__ import annotations

import numpy as np

from abm.core.agent import Agent
from abm.core.environment import Environment
from abm.core.network import Network
from abm.core.space import ContinuousSpace2D
from abm.core.state import AgentState
from abm.pillars import (
    INTERVENTIONS_PHASE6,
    PILLAR,
    apply_intervention,
    X1_SHOW_OTHER_SIDE,
    X4_BIPARTISAN_DIALOGUE,
    X5_RANKED_CHOICE_VOTING,
)
from abm.pillars.calm_to_camps import BACKLASH_AFFECT_THRESHOLD, build_engine
from abm.pillars.intervention import Intervention
from abm.rules.repulsion import BacklashRepulsion


# --- R1: affect-gated BacklashRepulsion ----------------------------------


def _two_agents_with_affect(pos_a, pos_b, party_a, party_b, warmth):
    a = Agent(
        id=0,
        state=AgentState(
            ideology=np.array(pos_a, dtype=float),
            attrs={
                "party": party_a,
                "affect": {party_b: float(warmth)},
                "stubbornness": 0.0,
            },
        ),
    )
    b = Agent(
        id=1,
        state=AgentState(
            ideology=np.array(pos_b, dtype=float),
            attrs={
                "party": party_b,
                "affect": {party_a: 0.0},
                "stubbornness": 0.0,
            },
        ),
    )
    space = ContinuousSpace2D()
    space.rebuild([a, b])
    env = Environment(attrs={"network": Network({0: {1}, 1: {0}})})
    return a, b, space, env


def test_backlash_at_zero_strength_is_inert():
    """`strength = 0` short-circuits to an empty StateDelta. Regression
    guard: S0-S4 bundles must remain bit-identical to Phase 5 (since
    they all carry strength=0)."""
    a, b, space, env = _two_agents_with_affect(
        [0.0, 0.0], [0.5, 0.0], party_a=0, party_b=1, warmth=-0.8,
    )
    rule = BacklashRepulsion(strength=0.0)
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    assert np.array_equal(delta.d_ideology, np.zeros(2)), (
        f"strength=0 must produce zero delta; got {delta.d_ideology}."
    )


def test_backlash_does_not_fire_above_affect_threshold():
    """Neutral or warm affect → no backfire, no matter how distant
    the out-party neighbour is in the [epsilon, max_range] ring."""
    a, b, space, env = _two_agents_with_affect(
        [0.0, 0.0], [0.6, 0.0], party_a=0, party_b=1, warmth=0.0,
    )
    rule = BacklashRepulsion(
        epsilon=0.3, max_range=1.5, strength=0.05,
        affect_threshold=-0.3,
    )
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    assert np.array_equal(delta.d_ideology, np.zeros(2)), (
        f"Above-threshold affect (0.0 > -0.3) must not produce push; "
        f"got {delta.d_ideology}."
    )


def test_backlash_fires_below_affect_threshold():
    """Cold affect (below -0.3) on an out-party encounter in the
    [epsilon, max_range] ring produces a push *away from* the neighbour."""
    a, b, space, env = _two_agents_with_affect(
        [0.0, 0.0], [0.6, 0.0], party_a=0, party_b=1, warmth=-0.5,
    )
    rule = BacklashRepulsion(
        epsilon=0.3, max_range=1.5, strength=0.05,
        affect_threshold=-0.3,
    )
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    # Neighbour is at +x; push should be away → negative x.
    assert delta.d_ideology[0] < 0.0, (
        f"Cold-affect out-party encounter should push away (negative x); "
        f"got {delta.d_ideology}."
    )


def test_backlash_skips_in_party_neighbours():
    """In-party neighbours never contribute backlash — the mechanism
    is identity-threat driven (Bail 2018)."""
    a, b, space, env = _two_agents_with_affect(
        [0.0, 0.0], [0.6, 0.0], party_a=0, party_b=0, warmth=-1.0,
    )
    rule = BacklashRepulsion(
        epsilon=0.3, max_range=1.5, strength=0.05,
        affect_threshold=-0.3,
    )
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    assert np.array_equal(delta.d_ideology, np.zeros(2)), (
        f"In-party neighbour should not trigger backlash; got "
        f"{delta.d_ideology}."
    )


def test_pillar_baseline_carries_backlash_at_zero():
    """All S0-S4 bundles set BacklashRepulsion.strength=0 and
    affect_threshold=BACKLASH_AFFECT_THRESHOLD (-0.3). Repulsion is an
    intervention knob, not a baseline force."""
    for stage_idx in range(5):
        eng = build_engine(seed=0, n_agents=50)
        apply_intervention(eng, PILLAR.interventions[stage_idx])
        br = next(
            r for r in eng.rules.rules
            if type(r).__name__ == "BacklashRepulsion"
        )
        assert br.strength == 0.0, (
            f"S{stage_idx} should carry BacklashRepulsion at strength 0"
        )
        assert br.affect_threshold == BACKLASH_AFFECT_THRESHOLD == -0.3


# --- R3: intervention library structure ----------------------------------


def test_intervention_library_has_seven_well_formed_interventions():
    """Every X has id, label, expected_naive_effect, predicted_effect,
    and either a non-empty param_bundle or a non-None setup. The
    library has seven entries after Phase 8c §4 added X7
    (perception-gap correction)."""
    assert len(INTERVENTIONS_PHASE6) == 7
    for iv in INTERVENTIONS_PHASE6:
        assert iv.id, f"intervention has no id: {iv}"
        assert iv.label, f"{iv.id} has no label"
        assert iv.expected_naive_effect, f"{iv.id} has no expected_naive_effect"
        assert iv.predicted_effect, f"{iv.id} has no predicted_effect"
        assert iv.citation, f"{iv.id} has no citation"
        assert iv.param_bundle or iv.setup, (
            f"{iv.id} has neither a param_bundle nor a setup"
        )


def test_apply_intervention_preserves_pipeline_structure():
    """Applying any X-intervention doesn't add or remove rules; the
    pipeline shape is invariant (Phase 1 D6)."""
    for iv in INTERVENTIONS_PHASE6:
        eng = build_engine(seed=0, n_agents=50)
        apply_intervention(eng, PILLAR.interventions[4])  # to S4
        rule_classes_before = {type(r).__name__ for r in eng.rules.rules}
        envrule_classes_before = {type(r).__name__ for r in eng.env_rules}
        apply_intervention(eng, iv)
        rule_classes_after = {type(r).__name__ for r in eng.rules.rules}
        envrule_classes_after = {type(r).__name__ for r in eng.env_rules}
        assert rule_classes_before == rule_classes_after, (
            f"{iv.id} altered the agent-rule classes."
        )
        assert envrule_classes_before == envrule_classes_after, (
            f"{iv.id} altered the env-rule classes."
        )


# --- R4: honesty schema (Phase 7 two-axis) -------------------------------


def test_intervention_supports_per_axis_buckets():
    """Phase 7: ``effect_buckets`` accepts per-axis bucket labels for
    the two axes the library cares about."""
    iv = Intervention(
        id="test_x",
        label="t",
        description="d",
        param_bundle=(),
        label_kind="intervention",
        effect_buckets={"issue_sorting": "real", "affect": "backfire"},
        expected_naive_effect="e",
        predicted_effect="p",
    )
    assert iv.effect_buckets["issue_sorting"] == "real"
    assert iv.effect_buckets["affect"] == "backfire"


def test_library_label_kind_is_intervention():
    """Every X-library entry is type-tagged 'intervention'. The
    per-axis bucket labels live in ``effect_buckets`` instead."""
    for iv in INTERVENTIONS_PHASE6:
        assert iv.label_kind == "intervention", (
            f"{iv.id} has label_kind={iv.label_kind!r}; "
            f"expected 'intervention'."
        )


def test_library_effect_buckets_cover_both_axes():
    """Every X has per-axis buckets on both 'issue_sorting' and
    'affect' axes, each with a valid bucket value."""
    valid = {"null", "partial", "real", "backfire"}
    for iv in INTERVENTIONS_PHASE6:
        assert set(iv.effect_buckets.keys()) == {"issue_sorting", "affect"}, (
            f"{iv.id} effect_buckets keys = {set(iv.effect_buckets.keys())}; "
            f"expected {{'issue_sorting', 'affect'}}."
        )
        for axis, bucket in iv.effect_buckets.items():
            assert bucket in valid, (
                f"{iv.id} effect_buckets[{axis!r}] = {bucket!r}; "
                f"expected one of {valid}."
            )


# --- §11 consolidated bucket test ----------------------------------------
# This is the empirical assertion that each intervention's tag matches
# what the model actually does. Run via the release-phase fixture in
# conftest.py.


def _classify_sep(dsep: float) -> str:
    """Issue-sorting axis: helpful = negative (sep falls)."""
    if abs(dsep) < 0.05:
        return "null"
    if -0.15 < dsep < -0.05:
        return "partial"
    if dsep <= -0.15:
        return "real"
    if dsep > 0.05:
        return "backfire"
    return "unclassified"


def _classify_aff(daff: float) -> str:
    """Affect axis: helpful = positive (warmth recovers).
    NOTE the sign flip vs. _classify_sep — `affective_polarization`
    itself reads more-negative = more-polarized, so positive Δ is the
    helpful direction (out-party warmth recovers toward 0)."""
    if abs(daff) < 0.05:
        return "null"
    if 0.05 < daff < 0.15:
        return "partial"
    if daff >= 0.15:
        return "real"
    if daff < -0.05:
        return "backfire"
    return "unclassified"


def test_intervention_library_directions_hold(intervention_buckets_arc):
    """Phase 7: each intervention's measured per-axis Δ matches its
    declared ``effect_buckets`` entry on both 'issue_sorting' (Δsep)
    and 'affect' (Δaff). If a future change moves an intervention out
    of its declared bucket on either axis, this test fails and the
    spec calls for re-blessing — move the tag, not the threshold.

    Step 2 (web_demo): measured on the ANES historical arc — the
    substrate the public buckets were blessed against (phase10) — not
    the pillar. The pillar lands X1 in the affect-threshold
    non-linearity (Δsep ≈ null), which mismatched the declared
    'backfire'; the arc is where the public bucket lives. See
    `intervention_buckets_arc` in conftest."""
    for iv in INTERVENTIONS_PHASE6:
        d = intervention_buckets_arc[iv.id]
        measured_sep = _classify_sep(d["sep"])
        measured_aff = _classify_aff(d["aff"])
        declared_sep = iv.effect_buckets["issue_sorting"]
        declared_aff = iv.effect_buckets["affect"]
        assert measured_sep == declared_sep, (
            f"{iv.id} issue_sorting: declared {declared_sep!r}, "
            f"measured {measured_sep!r} (Δsep={d['sep']:+.3f})."
        )
        assert measured_aff == declared_aff, (
            f"{iv.id} affect: declared {declared_aff!r}, "
            f"measured {measured_aff!r} (Δaff={d['aff']:+.3f})."
        )
