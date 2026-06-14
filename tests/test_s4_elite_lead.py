"""Isolation guard for the MHV S4 elite-lead factor (T4.2).

`elite_lead_factor` scales the data-fed party-centroid (the PartyPull cue
attractor) outward from the origin: cue = voter centroid x L. It is the lever
that closes the de-artifacted party_sep undershoot (voter-centroid attractors
cap mass sep at ~0.81 << ANES ~1.11; see docs/internal/audit/t42_undershoot.md).

emergence-recovery E5.7 note: `elite_lead_factor` only feeds the fed
PartyCentroidSeries, which is GONE on the endogenous canonical config (the loop
replaces it). So this file pins the lever against the preserved FED config
(`ANES_FULL_FED_KWARGS`) — the mechanism still exists in code, just not as the
shipped default.

Guards:
  * L = 1.0 is bit-identical to the default (no silent behaviour change).
  * party_sep is monotone increasing in L (the lever does what it claims).
  * no party coordinate reaches a domain bound at the fitted-range top (the
    S3 accept clause survives the lead).
"""

import numpy as np

from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from scripts.anes_preset import ANES_FULL_FED_KWARGS as ANES_FULL_KWARGS


def _run_to(eng_kwargs, tick, seed=0):
    eng = build_engine(seed=seed, **eng_kwargs)
    sched = build_schedule(
        faction_anchor_events=eng_kwargs.get("faction_anchor_events", True),
        evidence_regrade=eng_kwargs.get("evidence_regrade", False),
        exogenous_shocks=eng_kwargs.get("exogenous_shocks", False),
    )
    run_to(eng, sched, tick)
    return eng


def _party_sep(eng):
    pos = eng.positions()
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    return float(np.linalg.norm(pos[parties == 0].mean(0) - pos[parties == 1].mean(0)))


def test_elite_lead_default_is_bit_identical():
    """elite_lead_factor=1.0 is a no-op == relying on the build default.

    Preset-independent: strip the shipped value (1.798 since T4.3) so this
    pins the *mechanism's* default==1.0 bit-identity, not the calibrated point."""
    base = {k: v for k, v in ANES_FULL_KWARGS.items() if k != "elite_lead_factor"}
    a = _run_to(base, 12)                                   # build default (1.0)
    b = _run_to({**base, "elite_lead_factor": 1.0}, 12)     # explicit 1.0
    assert np.allclose(a.positions(), b.positions(), atol=0, rtol=0)


def test_elite_lead_monotone_widens_party_sep():
    """party_sep at 2020 strictly increases with the lead factor."""
    base = dict(ANES_FULL_KWARGS)
    seps = [_party_sep(_run_to({**base, "elite_lead_factor": L}, 126))
            for L in (1.0, 1.3, 1.6)]
    assert seps[0] < seps[1] < seps[2], seps


def test_elite_lead_with_strong_pull_reaches_anes_sep():
    """elite_lead + elevated party_pull reaches the ANES 2020 sep (~1.04-1.18);
    this is the combination that closes the undershoot (t42_undershoot.md)."""
    eng = _run_to({**ANES_FULL_KWARGS, "elite_lead_factor": 1.6,
                   "tier_c_party_pull_strength": 0.4, "fj_alpha_scale": 1.5}, 126)
    assert _party_sep(eng) > 1.0


def test_elite_lead_no_domain_bound_at_range_top():
    """At the fit-range top (L=2.0) no party centroid coordinate hits +/-1."""
    eng = _run_to({**ANES_FULL_KWARGS, "elite_lead_factor": 2.0}, 126)
    parties = eng.env.attrs.get("parties", {})
    for pid, c in parties.items():
        assert np.all(np.abs(np.asarray(c, float)) < 0.999), (pid, c)
