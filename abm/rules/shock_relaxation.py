"""
Shock relaxation — generic decay/revert for exogenous shocks.

Companion env-rule to `abm/pillars/shocks.py`. The shock event applies its
perturbation at onset and (for non-permanent profiles) registers a record in
`env.attrs["active_shocks"]`. This rule walks that ledger each tick and
relaxes / reverts each record per its profile, then retires it — generalizing
the per-event hand-rolled reverts that previously lived as bespoke functions
(ThreatDecay's absolute decay, the COVID learning-rate revert event).

Profiles handled (see `shocks.Persistence`):

  - `transient_affect`  — an injected per-(agent, out-party) warmth delta is
    eroded geometrically (residual ×= 1 - decay_rate) and the decrement is
    applied to live `affect`, so the *injected bump* relaxes toward 0 while
    the background affect dynamics proceed independently. Distinct from
    ThreatDecay, which decays an absolute attr toward 0 (correct only when
    the baseline is 0; affect's baseline is not).
  - `transient_scalar` — same geometric erosion for a clipped [0,1] scalar
    (perceived_threat / identity_alignment).
  - `window_rule` / `window_salience` — a rule attr (or env coupling) is
    restored to its pre-shock value once `tick >= expiry_tick`.
  - `ramp_position` — a POSITION nudge is applied in `ramp_ticks` equal
    increments, one per tick, then the record retires (level holds).

Gating / bit-identity: the rule is added to the historical-arc env_rules
ONLY when `exogenous_shocks=True`. Even when present it self-gates — an empty
or absent ledger short-circuits before any agent iteration — so it is a
strict no-op for any scenario that registers no shocks.

Reads / writes:
  env.attrs["active_shocks"]               -- the ledger (list of records)
  agent.state.attrs["affect"]              -- transient_affect
  agent.state.attrs["perceived_threat"] / ["identity_alignment"]  -- scalar
  agent.state.ideology                     -- ramp_position
  rule attrs / env party_issue_coupling    -- window_* revert
"""
from __future__ import annotations

import numpy as np

from ..core.environment import Environment
from ..core.space import ContinuousSpace2D


class ShockRelaxation:
    """Advances and retires exogenous-shock ledger records each tick.
    Self-gates on a non-empty `env.attrs["active_shocks"]`."""

    # Residual below this (in native units) is treated as fully relaxed.
    _EPS = 1e-4

    def apply(
        self,
        env: Environment,
        agents,
        space: ContinuousSpace2D,
        rng,
        tick: int,
    ) -> None:
        ledger = env.attrs.get("active_shocks")
        if not ledger:
            return
        by_id = {a.id: a for a in agents}
        survivors = []
        for rec in ledger:
            profile = rec.get("profile")
            keep = False
            if profile == "transient_affect":
                keep = self._relax_affect(rec, by_id)
            elif profile == "transient_scalar":
                keep = self._relax_scalar(rec, by_id)
            elif profile in ("window_rule", "window_salience"):
                keep = self._revert_window(rec, env, tick)
            elif profile == "ramp_position":
                keep = self._step_ramp(rec, by_id, space)
            if keep:
                survivors.append(rec)
        env.attrs["active_shocks"] = survivors

    # --- profile handlers ---

    def _relax_affect(self, rec, by_id) -> bool:
        decay = rec["decay_rate"]
        residual = rec["residual"]   # {agent_id: {other_party: applied_delta}}
        any_left = False
        for aid, per_party in list(residual.items()):
            agent = by_id.get(aid)
            for other_party, res in list(per_party.items()):
                new_res = res * (1.0 - decay)
                if agent is not None:
                    affect = agent.state.attrs.get("affect")
                    if affect is not None and other_party in affect:
                        cur = float(np.clip(affect[other_party], -1.0, 1.0))
                        # Remove the eroded fraction of the injected bump.
                        affect[other_party] = float(
                            np.clip(cur + (new_res - res), -1.0, 1.0)
                        )
                if abs(new_res) < self._EPS:
                    del per_party[other_party]
                else:
                    per_party[other_party] = new_res
                    any_left = True
            if not per_party:
                del residual[aid]
        return any_left

    def _relax_scalar(self, rec, by_id) -> bool:
        decay = rec["decay_rate"]
        attr = rec["attr"]
        residual = rec["residual"]   # {agent_id: applied_delta}
        any_left = False
        for aid, res in list(residual.items()):
            agent = by_id.get(aid)
            new_res = res * (1.0 - decay)
            if agent is not None:
                cur = float(np.clip(agent.state.attrs.get(attr, 0.0), 0.0, 1.0))
                agent.state.attrs[attr] = float(
                    np.clip(cur + (new_res - res), 0.0, 1.0)
                )
            if abs(new_res) < self._EPS:
                del residual[aid]
            else:
                residual[aid] = new_res
                any_left = True
        return any_left

    def _revert_window(self, rec, env, tick) -> bool:
        if tick < rec["expiry_tick"]:
            return True  # still inside the window
        if rec["profile"] == "window_rule":
            setattr(rec["rule"], rec["attr"], rec["pre_value"])
        else:  # window_salience
            env.attrs["party_issue_coupling"] = rec["pre_value"]
        return False  # retire

    def _step_ramp(self, rec, by_id, space) -> bool:
        from ..pillars.shocks import _apply_position
        spec = rec["spec"]
        n = rec["ramp_ticks"]
        engine_like = _RampEngineShim(by_id, space)
        _apply_position(engine_like, spec, rec["target_ids"], frac=1.0 / n)
        rec["ticks_done"] += 1
        return rec["ticks_done"] < n


class _RampEngineShim:
    """Minimal engine-like adapter so `_apply_position` (which expects
    `engine.agents` and `engine.space`) can run from within the env-rule."""

    def __init__(self, by_id, space):
        self.agents = list(by_id.values())
        self.space = space
