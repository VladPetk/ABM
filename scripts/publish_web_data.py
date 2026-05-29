"""publish_web_data.py — generate the web demo data bundle.

Runs the real Phase 10 engine (historical arc, ANES-recalibrated)
and dumps the per-tick trajectories the web demo consumes:

  - 1 canonical baseline at the canonical seed (full per-tick capture)
  - N-1 baseline runs at additional seeds for variance bands (macro-
    metrics only by default; agent-level data with --variance-detail)
  - 7 interventions × M release ticks at the canonical seed
  - 4 character data files derived from the canonical baseline
  - manifest.json, events.json, intervention_metadata.json

Default output layout (matches docs/web_demo_plan.md §3.1):

    web/data/
      manifest.json
      events.json
      intervention_metadata.json
      baseline/seed_0.json .. seed_8.json
      interventions/<intervention_id>_at_<year>.json   (56 files)
      characters/linda.json, james.json, maria.json, bob.json

Usage:

    # Full publish (~10-15 min serial, much faster with -j 8):
    .venv/Scripts/python.exe scripts/publish_web_data.py

    # Quick prototype (baseline + X1 + X5 + X6 at tick 90, n=80):
    .venv/Scripts/python.exe scripts/publish_web_data.py --quick

    # Specific subset:
    .venv/Scripts/python.exe scripts/publish_web_data.py \\
        --interventions X1 X5 X6 \\
        --release-ticks 30 60 90 120 \\
        --skip-variance

The script is intentionally JSON-only (not binary) for the prototype
phase. Switching to packed binary trajectory blobs is a Phase 2
optimization once the FE schema is locked.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

import numpy as np


# --- Configuration -----------------------------------------------------

# anes_full preset (copied from scripts/phase10_measure.py so this
# script is self-contained against future preset edits).
ANES_FULL_KWARGS = {
    "n_agents": 250,
    "independent_fraction": 0.12,
    "factional_seeding": False,
    "faction_anchor_strength": 0.10,
    "faction_anchor_events": True,
    "event_stubbornness_bump_multiplier": 1.0,
    "tier_d_axis_balance": True,
    "tier_d_lever1_off": True,
    "tier_d_cohort_y_signs_fix": True,
    "tier_d_anes_knobs": True,
    "tier_d_anes_drift_multiplier": 3.0,
    "tier_d_anes_sigma_pc_multiplier": 1.6,
    "tier_c_identity_pull_x": 0.020,
    "tier_c_identity_pull_y": 0.040,
    # web_demo jumpiness Step 3: halved from 0.08. The per-tick Gaussian
    # noise is the dominant jitter source in the demo (with mean
    # stubbornness ~0.29, (1-s)*0.08*sqrt(pi/2) ~ 0.07/tick, matching the
    # observed median step of 0.065). Halving it ~halves crowd jitter.
    "tier_d_aniso_noise_sigma_x": 0.04,
    "tier_d_aniso_noise_sigma_y": 0.04,
    "tier_c_party_pull_strength": 0.04,
    "tier_c_bc_strength": 0.015,
    "tier_d_coupling_rho": 0.30,
    "tier_d_cue_correlation": 0.40,
    "tier_d_ic_sigma": 0.35,
    # web_demo jumpiness Step 5: opinion momentum. Carries 0.4 of the
    # previous applied step into each tick so consecutive deltas stop
    # cancelling — kills the tick-to-tick reversals (median 68 sharp
    # turns/agent in the baseline). See Engine.step.
    "momentum": 0.4,
    # web_demo jumpiness Step 4: tighten the free-mover tail. Stronger
    # anchor pull so low-stubbornness agents drift instead of random-
    # walking. 2.8 (≈ 0.05 → 0.14) thins the tail of continuous agents
    # making implausibly large lifetime journeys: frac drifting >1 unit
    # over 45 yr falls 4.2%→2.4% (~the 1-2% target), while polarization
    # holds (party_sep 0.907→0.917) and within-party SD improves toward
    # the ANES band (0.242→0.259). See historical_arc.build_engine.
    "fj_alpha_scale": 2.8,
    # web_demo realism: truncate the 1980 economic IC tail so a partisan
    # can't initialize deep in the opposite half (a Democrat past x>+0.45
    # in the laissez-faire corner, or vice-versa). Keeps the calibrated
    # mean party overlap and the (historically real) cultural overlap;
    # removes only the implausible diagonal-corner outliers.
    "tier_d_ic_partisan_x_cap": 0.45,
}

CANONICAL_SEED = 0
TICKS_PER_YEAR = 3.0
TICK_0_YEAR = 1980.0
END_TICK = 135  # tick 135 ≈ end of 2025

# 5-year release granularity. Skipping 2025 (tick 135) since it
# leaves zero counterfactual room within the engine horizon.
DEFAULT_RELEASE_TICKS = [15, 30, 45, 60, 75, 90, 105, 120]

# Snapshot the network at these ticks (so the FE can render edges at
# event-meaningful moments without paying full per-tick network cost).
DEFAULT_NETWORK_SNAPSHOT_TICKS = [
    0, 21, 30, 48, 60, 84, 87, 90, 96, 105, 108, 114, 120, 135,
]

# Historical events with their true (year, month) for the timeline.
# Engine ticks fire integer-aligned; the timeline displays the actual
# month-of-history per ENGINE_KNOBS.md §7 and the redesign brief.
EVENT_ACTUAL_DATES = {
    "fairness_doctrine_1987": "1987-08",
    "decade_1990": "1990-01",
    "fox_news_1996": "1996-10",
    "decade_2000": "2000-01",
    "social_media_ramp_start_and_obama_2008": "2008-11",
    "tea_party_2009": "2009-04",
    "decade_2010_and_citizens_united": "2010-01",
    "social_media_ramp_end_2012": "2012-11",
    "maga_2015": "2015-06",
    "trump_2016_and_status_threat": "2016-11",
    "bernie_2016": "2016-07",
    "trump_bump_revert_2018": "2018-11",
    "dsa_2018": "2018-11",
    "covid_jan6_2020": "2020-03",
    "affect_revert_2021": "2021-06",
}

EVENT_KIND = {
    "fairness_doctrine_1987": "media",
    "decade_1990": "decade_boundary",
    "fox_news_1996": "media",
    "decade_2000": "decade_boundary",
    "social_media_ramp_start_and_obama_2008": "election",
    "tea_party_2009": "faction",
    "decade_2010_and_citizens_united": "decade_boundary",
    "social_media_ramp_end_2012": "media",
    "maga_2015": "faction",
    "trump_2016_and_status_threat": "election",
    "bernie_2016": "faction",
    "trump_bump_revert_2018": "decade_boundary",
    "dsa_2018": "faction",
    "covid_jan6_2020": "crisis",
    "affect_revert_2021": "decade_boundary",
}


# --- Capture helpers ---------------------------------------------------

def capture_tick_state(eng) -> dict:
    """Per-agent state at the current tick, as compact column arrays.

    Output columns (all length = n_agents):

      positions : list[[x, y]]          float, 2D ideology compass
      party     : list[int]             0 = Dem, 1 = Rep, 2 = Independent
      affect    : list[float]           mean out-party warmth (∈ [-1, 1])
      threat    : list[float]           Mutz 2018 status-threat level
      coop_share: list[float]           cooperative-disposition share
      identity_strength : list[float]
      faction   : list[str | null]      current faction label (sticky)
    """
    n = len(eng.agents)
    positions = []
    party = []
    affect = []
    threat = []
    coop_share = []
    id_strength = []
    faction = []
    for a in eng.agents:
        pos = a.state.ideology
        positions.append([float(pos[0]), float(pos[1])])
        party.append(int(a.state.attrs.get("party", 2)))
        a_aff = a.state.attrs.get("affect") or {}
        if a_aff:
            affect.append(float(np.mean(list(a_aff.values()))))
        else:
            affect.append(0.0)
        threat.append(float(a.state.attrs.get("threat", 0.0)))
        coop_share.append(float(a.state.attrs.get("cooperative_share", 0.0)))
        id_strength.append(float(a.state.attrs.get("identity_strength", 0.5)))
        f = a.state.attrs.get("faction")
        faction.append(str(f) if f else None)
    return {
        "positions": positions,
        "party": party,
        "affect": affect,
        "threat": threat,
        "cooperative_share": coop_share,
        "identity_strength": id_strength,
        "faction": faction,
    }


def capture_macro_metrics(eng) -> dict:
    """Macro polarization metrics at the current tick."""
    from scripts.phase8f_lib import measure_all
    metrics = measure_all(eng)
    parties = eng.env.attrs.get("parties", {})
    out = {}
    for k, v in metrics.items():
        if isinstance(v, (int, float, np.floating, np.integer)):
            out[k] = float(v)
        elif isinstance(v, dict):
            # e.g., constraint returns {"x": ..., "y": ...}
            out[k] = {kk: float(vv) for kk, vv in v.items()}
        else:
            out[k] = v
    # Party centroids — current env positions, useful for compass
    # visualization (separate from the per-agent positions).
    def _pt(v):
        if v is None:
            return [0.0, 0.0]
        return [float(v[0]), float(v[1])]
    out["party_centroid_0"] = _pt(parties.get(0))
    out["party_centroid_1"] = _pt(parties.get(1))
    return out


def capture_network_snapshot(eng) -> dict:
    """Network edges + flags at the current tick.

    Returns ``{"n_edges": int, "edges": [[i, j, flags], ...]}``
    where ``flags`` is a bitmask: 1 = involuntary, 2 = cooperative.
    """
    net = eng.env.attrs["network"]
    edges = []
    for i, j in net.edges():
        flags = 0
        if net.is_involuntary(i, j):
            flags |= 1
        if net.is_cooperative(i, j):
            flags |= 2
        edges.append([int(i), int(j), int(flags)])
    return {"n_edges": len(edges), "edges": edges}


def capture_agent_static(eng) -> list[dict]:
    """One-time static per-agent metadata at the current engine state.

    Captured at tick 0 (initial conditions) for stable agent identity
    across the timeline — e.g., "agent #42 is always Linda."
    """
    out = []
    for i, a in enumerate(eng.agents):
        attrs = a.state.attrs
        anchor = attrs.get("anchor")
        anchor_xy = (
            [float(anchor[0]), float(anchor[1])]
            if anchor is not None else None
        )
        identities = attrs.get("identities")
        identities_list = (
            [float(v) for v in identities]
            if identities is not None else None
        )
        out.append({
            "id": int(i),
            "social_coord": float(attrs.get("social_coord", 0.0)),
            "stubbornness": float(attrs.get("stubbornness", 0.0)),
            "epsilon": float(attrs.get("epsilon", 0.0)),
            "fj_alpha": float(attrs.get("fj_alpha", 0.0)),
            "learning_rate": float(attrs.get("learning_rate", 0.0)),
            "anchor": anchor_xy,
            "identities": identities_list,
            "initial_party": int(attrs.get("party", 2)),
            "initial_position": [
                float(a.state.ideology[0]),
                float(a.state.ideology[1]),
            ],
        })
    return out


# --- Trajectory runner -------------------------------------------------

def run_trajectory(
    seed: int,
    intervention_id: str | None = None,
    release_tick: int | None = None,
    n_agents: int | None = None,
    end_tick: int = END_TICK,
    snapshot_ticks: list[int] | None = None,
    capture_agents: bool = True,
    protected_agent_ids=None,
) -> dict:
    """Build engine, run to end_tick, capture per-tick state.

    Parameters
    ----------
    seed: RNG seed.
    intervention_id: optional intervention id (e.g., "X5_ranked_choice_voting").
        If None, runs the no-intervention baseline.
    release_tick: tick at which to apply the intervention. Ignored if
        intervention_id is None.
    n_agents: optional override for the population size (anes_full
        default is 250). Lower values speed up prototype runs.
    end_tick: tick to stop at (default END_TICK = 135 = end of 2025).
    snapshot_ticks: ticks at which to capture full network snapshots.
    capture_agents: if False, only macro metrics are captured (used for
        variance-band runs to keep file sizes small).

    Returns the trajectory dict ready for JSON serialization.
    """
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from abm.pillars.intervention import apply_intervention
    from abm.pillars.interventions_phase6 import INTERVENTIONS_PHASE6

    if snapshot_ticks is None:
        snapshot_ticks = DEFAULT_NETWORK_SNAPSHOT_TICKS
    snapshot_set = set(snapshot_ticks)

    kwargs = dict(ANES_FULL_KWARGS)
    if n_agents is not None:
        kwargs["n_agents"] = int(n_agents)
    if protected_agent_ids is not None:
        # Step 2: spotlighted characters are immune to cohort replacement.
        kwargs["protected_agent_ids"] = set(int(i) for i in protected_agent_ids)

    eng = build_engine(seed=seed, **kwargs)
    sched = build_schedule(
        factional_seeding=kwargs.get("factional_seeding", False),
        faction_anchor_events=kwargs.get("faction_anchor_events", True),
    )

    iv_by_id = {iv.id: iv for iv in INTERVENTIONS_PHASE6}
    intervention = iv_by_id.get(intervention_id) if intervention_id else None
    if intervention_id and intervention is None:
        raise KeyError(
            f"intervention id {intervention_id!r} not in INTERVENTIONS_PHASE6"
        )

    ticks_data: list[dict] = []
    macro_data: list[dict] = []
    network_snapshots: dict[str, dict] = {}
    events_fired: list[dict] = []

    # Capture tick 0 BEFORE any run_to call so we get pristine ICs.
    if capture_agents:
        ticks_data.append(capture_tick_state(eng))
    macro_data.append(capture_macro_metrics(eng))
    if 0 in snapshot_set:
        network_snapshots["0"] = capture_network_snapshot(eng)

    agent_static = capture_agent_static(eng) if capture_agents else None

    # Step tick by tick (each call advances exactly 1 tick + fires
    # any due scheduled events).
    intervention_applied_at = None
    for t in range(1, end_tick + 1):
        fired = run_to(eng, sched, t)
        for evt in fired:
            events_fired.append({
                "tick": int(evt.tick),
                "label": str(evt.label),
                "description": str(evt.description),
            })

        # Apply the intervention at the release tick (after the tick
        # has run; matches the Phase 10 measurement convention).
        if (
            intervention is not None
            and t == release_tick
            and intervention_applied_at is None
        ):
            apply_intervention(eng, intervention)
            intervention_applied_at = int(t)

        if capture_agents:
            ticks_data.append(capture_tick_state(eng))
        macro_data.append(capture_macro_metrics(eng))
        if t in snapshot_set:
            network_snapshots[str(t)] = capture_network_snapshot(eng)

    return {
        "n_agents": len(eng.agents),
        "n_ticks": end_tick + 1,
        "seed": int(seed),
        "intervention_id": intervention_id,
        "release_tick": release_tick,
        "intervention_applied_at": intervention_applied_at,
        "tick_0_year": TICK_0_YEAR,
        "ticks_per_year": TICKS_PER_YEAR,
        "agent_static": agent_static,
        "ticks": ticks_data if capture_agents else None,
        "macro": macro_data,
        "network_snapshots": network_snapshots,
        "events_fired": events_fired,
        # Step 1: [tick, agent_id] for every cohort replacement, so the
        # viz can ghost-fade on each slot reuse (party-flipping or not).
        "replacement_events": list(eng.env.attrs.get("replacement_events", [])),
    }


# --- Character selection ----------------------------------------------

CHARACTER_ARCHETYPES = {
    "linda": {
        "name": "Linda",
        "bio_template": (
            "Linda is a school district administrator in suburban Ohio. "
            "Married, two kids, voted Democrat through the 80s and 90s. "
            "Drifted right over the years — by 2025 she's a steady "
            "Republican voter who watches both MSNBC and Fox and trusts "
            "neither completely."
        ),
        "issues_priority": ["education", "healthcare", "taxes"],
        "demographics": {"city_template": "suburban Ohio", "occupation": "school administrator"},
        # Scoring: starts D (party=0), ends R (party=1), moderate position drift.
        "score_fn": "linda",
    },
    "james": {
        "name": "James",
        "bio_template": (
            "James is a software engineer who came up in Seattle. "
            "Lifelong Democrat. His positions barely budged over forty "
            "years — but his warmth toward Republicans collapsed after "
            "2008. By 2020 he'd cooled completely. Same beliefs, "
            "different temperature."
        ),
        "issues_priority": ["climate", "tech regulation", "civil liberties"],
        "demographics": {"city_template": "Seattle", "occupation": "software engineer"},
        # Scoring: stable D, position barely moves, affect collapses.
        "score_fn": "james",
    },
    "maria": {
        "name": "Maria",
        "bio_template": (
            "Maria works as a nurse in Phoenix. Independent through "
            "the 90s, leaned Democrat through Obama, found her politics "
            "after 2016 — she's been part of the DSA-aligned left since "
            "2018. The Bernie campaigns radicalized her where the "
            "Clintons hadn't."
        ),
        "issues_priority": ["healthcare", "wages", "housing"],
        "demographics": {"city_template": "Phoenix", "occupation": "nurse"},
        # Scoring: starts Independent or moderate D, drifts left (negative x), DSA-ish.
        "score_fn": "maria",
    },
    "bob": {
        "name": "Bob",
        "bio_template": (
            "Bob runs a small construction business in Alabama. "
            "Lifelong Republican. Voted Reagan, Bush, Bush, McCain — "
            "got pulled into the Tea Party in 2009 and never left. "
            "MAGA from the 2015 primary on. Doesn't talk politics with "
            "his old college roommates anymore."
        ),
        "issues_priority": ["taxes", "immigration", "guns"],
        "demographics": {"city_template": "Alabama", "occupation": "small business owner"},
        # Scoring: starts R, factional movement (Tea Party / MAGA), drifts further right.
        "score_fn": "bob",
    },
}


def _score_agent_for_archetype(
    archetype: str, idx: int, baseline: dict
) -> float:
    """Score a candidate agent index against an archetype. Higher = better fit.

    Reads the canonical baseline trajectory and computes simple
    aggregate signals (initial vs final party, position drift,
    affect collapse, faction membership history).
    """
    n_ticks = baseline["n_ticks"]
    ticks = baseline["ticks"]
    static = baseline["agent_static"][idx]

    # Party trajectory
    party_series = [tick_data["party"][idx] for tick_data in ticks]
    initial_party = party_series[0]
    final_party = party_series[-1]

    # Position trajectory
    pos_series = np.array([tick_data["positions"][idx] for tick_data in ticks])
    initial_pos = pos_series[0]
    final_pos = pos_series[-1]
    position_drift = float(np.linalg.norm(final_pos - initial_pos))
    x_drift = float(final_pos[0] - initial_pos[0])
    y_drift = float(final_pos[1] - initial_pos[1])

    # Affect trajectory
    affect_series = np.array([tick_data["affect"][idx] for tick_data in ticks])
    initial_affect = float(affect_series[0])
    final_affect = float(affect_series[-1])
    affect_collapse = initial_affect - final_affect  # positive = cooled

    # Faction history
    faction_history = [tick_data["faction"][idx] for tick_data in ticks]
    factions_visited = set(f for f in faction_history if f)

    if archetype == "linda":
        # Centrist D → R swing — a MODEST crosser, not a corner-to-corner
        # odyssey. The old scorer rewarded `rightward * 2.0`, i.e. it
        # cherry-picked the single most extreme traveler (net drift 1.24,
        # top ~3% of all agents) — implausible for one continuous person.
        # Now: require the D→R flip, then reward a gentle journey from
        # ~center-left to ~center-right with SMALL total displacement.
        if initial_party != 0 or final_party != 1:
            return -1.0
        if initial_pos[0] > -0.1:              # must start clearly left
            return -1.0
        if final_pos[0] < 0.1:                 # must end clearly right (real crossing)
            return -1.0
        # Target a MODERATE journey (~0.7 units) — penalize both a static
        # label-flip (net≈0) and a corner-to-corner odyssey (net>1).
        journey_fit = 1.0 - min(1.0, abs(position_drift - 0.7) / 0.6)
        end_moderation = 1.0 - min(1.0, max(0.0, abs(final_pos[0]) - 0.5))  # not far corner
        return journey_fit * 2.0 + end_moderation
    if archetype == "james":
        # Stable D, low position drift, high affect collapse
        if initial_party != 0 or final_party != 0:
            return -1.0
        stability = 1.0 - min(1.0, position_drift)
        cooling = max(0.0, affect_collapse)
        return stability * 1.5 + cooling * 2.0
    if archetype == "maria":
        # Independent or D, drifts left (negative x), DSA-ish
        if initial_party not in (0, 2):
            return -1.0
        leftward = max(0.0, -x_drift)
        dsa_fit = 1.0 if "DSA" in factions_visited or "Bernie_Progressives" in factions_visited else 0.0
        return leftward * 1.5 + dsa_fit * 2.0
    if archetype == "bob":
        # Stable R, factional involvement, rightward drift
        if initial_party != 1 or final_party != 1:
            return -1.0
        rightward = max(0.0, x_drift)
        factional = 1.0 if (
            "Tea_Party" in factions_visited or "MAGA" in factions_visited
        ) else 0.0
        return rightward * 1.0 + factional * 3.0
    return 0.0


def select_character_indices(baseline: dict) -> dict[str, int]:
    """Score every agent against each archetype on the given baseline and
    return ``{archetype_id: agent_index}`` for the best non-overlapping fit.

    Step 2 (web_demo jumpiness): this runs on an UNPROTECTED baseline so
    archetype fit is judged on the natural dynamics; the chosen indices
    are then flagged `do_not_replace` for the published (protected) runs.
    """
    n_agents = baseline["n_agents"]
    chosen: dict[str, int] = {}
    used: set[int] = set()
    for archetype in ("linda", "bob", "maria", "james"):
        scored = []
        for idx in range(n_agents):
            if idx in used:
                continue
            score = _score_agent_for_archetype(archetype, idx, baseline)
            if score > 0:
                scored.append((score, idx))
        scored.sort(reverse=True)
        if not scored:
            print(f"  WARNING: no agent matched archetype {archetype!r} — skipping")
            continue
        _, idx = scored[0]
        used.add(idx)
        chosen[archetype] = idx
    return chosen


def build_character_payload(
    archetype: str, idx: int, baseline: dict
) -> dict:
    """Build the per-character export dict (trajectory summary + beats)
    for a known agent index, read off the given (published) baseline."""
    meta = CHARACTER_ARCHETYPES[archetype]
    trajectory = []
    for t in range(baseline["n_ticks"]):
        td = baseline["ticks"][t]
        trajectory.append({
            "tick": t,
            "position": td["positions"][idx],
            "party": td["party"][idx],
            "affect": td["affect"][idx],
            "threat": td["threat"][idx],
            "faction": td["faction"][idx],
        })
    # Derive narrative beats — light procedural annotation. Real
    # hand-written beats can replace this once an author reads the
    # trajectory.
    beats = _build_narrative_beats(archetype, trajectory)
    return {
        "id": archetype,
        "name": meta["name"],
        "agent_index": idx,
        "bio": meta["bio_template"],
        "issues_priority": meta["issues_priority"],
        "demographics": meta["demographics"],
        "narrative_beats": beats,
        "trajectory_summary": _summarize_trajectory(trajectory),
    }


def _summarize_trajectory(trajectory: list[dict]) -> dict:
    """Compact summary stats for the FE to render at-a-glance."""
    initial = trajectory[0]
    final = trajectory[-1]
    party_switches = sum(
        1 for i in range(1, len(trajectory))
        if trajectory[i]["party"] != trajectory[i - 1]["party"]
    )
    factions_visited = sorted({
        t["faction"] for t in trajectory if t["faction"]
    })
    return {
        "initial_party": initial["party"],
        "final_party": final["party"],
        "initial_position": initial["position"],
        "final_position": final["position"],
        "initial_affect": initial["affect"],
        "final_affect": final["affect"],
        "party_switches": party_switches,
        "factions_visited": factions_visited,
    }


def _build_narrative_beats(archetype: str, trajectory: list[dict]) -> list[dict]:
    """Procedural narrative beats keyed off the agent's per-tick state.

    These are placeholders an author should rewrite for the public
    demo. The structure is what the FE consumes: an ordered list of
    {tick, year, text} entries.
    """
    beats = []
    # Beat 1: 1985 baseline
    t15 = trajectory[15] if len(trajectory) > 15 else trajectory[-1]
    beats.append({
        "tick": 15,
        "year": 1985,
        "text": _beat_1985(archetype, t15),
    })
    # Beat 2: 1996 / 2000 transition
    t60 = trajectory[60] if len(trajectory) > 60 else trajectory[-1]
    beats.append({
        "tick": 60,
        "year": 2000,
        "text": _beat_2000(archetype, t60),
    })
    # Beat 3: 2009 / Tea Party era
    t87 = trajectory[87] if len(trajectory) > 87 else trajectory[-1]
    beats.append({
        "tick": 87,
        "year": 2009,
        "text": _beat_2009(archetype, t87),
    })
    # Beat 4: 2016 / Trump
    t108 = trajectory[108] if len(trajectory) > 108 else trajectory[-1]
    beats.append({
        "tick": 108,
        "year": 2016,
        "text": _beat_2016(archetype, t108),
    })
    # Beat 5: 2025 endpoint
    tend = trajectory[-1]
    beats.append({
        "tick": tend["tick"],
        "year": int(TICK_0_YEAR + tend["tick"] / TICKS_PER_YEAR),
        "text": _beat_endpoint(archetype, tend),
    })
    return beats


def _party_word(p):
    return {0: "Democratic", 1: "Republican", 2: "Independent"}.get(int(p), "?")


def _beat_1985(archetype, state):
    return (
        f"In 1985, {CHARACTER_ARCHETYPES[archetype]['name']} is voting "
        f"{_party_word(state['party'])}. Out-party warmth: {state['affect']:+.2f}."
    )


def _beat_2000(archetype, state):
    return (
        f"By 2000, position has shifted to ({state['position'][0]:+.2f}, "
        f"{state['position'][1]:+.2f}). Still {_party_word(state['party'])}."
    )


def _beat_2009(archetype, state):
    faction = state["faction"]
    if faction:
        return f"By 2009, joined the {faction.replace('_', ' ')} cluster. Position ({state['position'][0]:+.2f}, {state['position'][1]:+.2f})."
    return (
        f"In the Tea Party era. Still {_party_word(state['party'])}; "
        f"warmth at {state['affect']:+.2f}."
    )


def _beat_2016(archetype, state):
    faction = state["faction"]
    threat = state["threat"]
    extra = f" Faction: {faction.replace('_', ' ')}." if faction else ""
    return (
        f"Trump election. {_party_word(state['party'])}; warmth "
        f"{state['affect']:+.2f}; threat level {threat:.2f}.{extra}"
    )


def _beat_endpoint(archetype, state):
    return (
        f"At end of 2025: {_party_word(state['party'])}, position "
        f"({state['position'][0]:+.2f}, {state['position'][1]:+.2f}), "
        f"warmth {state['affect']:+.2f}."
    )


# --- Manifest + metadata builders --------------------------------------

def build_events_json(events_fired_in_baseline: list[dict]) -> dict:
    """The events.json the FE consumes for timeline markers."""
    seen = {}
    for evt in events_fired_in_baseline:
        label = evt["label"]
        if label in seen:
            continue
        seen[label] = {
            "tick": int(evt["tick"]),
            "label": label,
            "description": evt["description"],
            "actual_date": EVENT_ACTUAL_DATES.get(label),
            "kind": EVENT_KIND.get(label, "other"),
        }
    return {
        "version": 1,
        "events": list(seen.values()),
    }


def build_intervention_metadata() -> dict:
    """One JSON entry per intervention with everything the FE result
    card needs: lay label, mechanism summary, citation, current bucket
    label, provenance-tag summary."""
    from abm.pillars.interventions_phase6 import INTERVENTIONS_PHASE6

    # Provenance tags from scripts/phase10_measure.py (pinned summary).
    provenance_tags = {
        "X1_show_other_side":     {"L:M": 1, "L:D": 2, "T": 1, "C": 0},
        "X2_fix_algorithm":       {"L:M": 1, "L:D": 0, "T": 0, "C": 0},
        "X3_quit_cable_news":     {"L:M": 0, "L:D": 1, "T": 1, "C": 0},
        "X4_bipartisan_dialogue": {"L:M": 2, "L:D": 1, "T": 2, "C": 0},
        "X5_ranked_choice_voting":{"L:M": 0, "L:D": 0, "T": 4, "C": 0},
        "X6_shared_institutions": {"L:M": 1, "L:D": 2, "T": 0, "C": 1},
        "X7_perception_correction":{"L:M": 1, "L:D": 1, "T": 2, "C": 0},
    }
    # Lay color hint per intervention (FE can override).
    colors = {
        "X1_show_other_side":      "#d04a3a",
        "X2_fix_algorithm":        "#7a7a7a",
        "X3_quit_cable_news":      "#8a6a3a",
        "X4_bipartisan_dialogue":  "#3a8a6a",
        "X5_ranked_choice_voting": "#3a6ad0",
        "X6_shared_institutions":  "#5a3ad0",
        "X7_perception_correction":"#aa3a8a",
    }
    out = {}
    for iv in INTERVENTIONS_PHASE6:
        out[iv.id] = {
            "id": iv.id,
            "label": iv.label,
            "description": iv.description,
            "citation": iv.citation,
            "expected_naive_effect": iv.expected_naive_effect,
            "predicted_effect": iv.predicted_effect,
            "effect_buckets": dict(iv.effect_buckets),
            "provenance_tags": provenance_tags.get(iv.id, {}),
            "color": colors.get(iv.id, "#888888"),
        }
    return {"version": 1, "interventions": out}


def build_manifest(
    n_agents: int,
    release_ticks: list[int],
    intervention_ids: list[str],
    variance_seeds: list[int],
    character_ids: list[str],
    end_tick: int,
) -> dict:
    return {
        "version": 1,
        "engine_version": "phase10",
        "preset": "anes_full",
        "n_agents": int(n_agents),
        "n_ticks": int(end_tick + 1),
        "tick_0_year": TICK_0_YEAR,
        "ticks_per_year": TICKS_PER_YEAR,
        "end_tick": int(end_tick),
        "canonical_seed": CANONICAL_SEED,
        "variance_band_seeds": [int(s) for s in variance_seeds],
        "release_ticks": [int(t) for t in release_ticks],
        "release_years": {
            str(t): int(TICK_0_YEAR + t / TICKS_PER_YEAR)
            for t in release_ticks
        },
        "interventions": list(intervention_ids),
        "characters": list(character_ids),
        "ideology_axes": {
            "x": {"label": "Economic", "lo": "Redistributive", "hi": "Laissez-faire"},
            "y": {"label": "Cultural", "lo": "Progressive", "hi": "Traditional"},
        },
        "paths": {
            "events": "events.json",
            "intervention_metadata": "intervention_metadata.json",
            "baseline": "baseline/seed_{seed}.json",
            "intervention": "interventions/{intervention_id}_at_{year}.json",
            "character": "characters/{character_id}.json",
        },
    }


# --- File writers ------------------------------------------------------

def write_json(path: Path, payload, indent: int | None = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=indent, separators=(",", ":") if indent is None else None)


# --- Parallel worker --------------------------------------------------
#
# Top-level worker for multiprocessing. Windows uses the `spawn` start
# method, which pickles the worker by reference — so it must be
# importable at module level (no closures / lambdas / inner functions).
#
# The worker writes the trajectory to disk directly and returns a
# small metadata dict — this avoids pickling 1–5 MB trajectory payloads
# across the IPC boundary.

def _publish_worker(args: tuple) -> dict:
    """Build a single trajectory and write it to disk.

    args = (
        out_path_str,        # absolute path of the destination JSON file
        seed,                # int RNG seed
        intervention_id,     # str | None
        release_tick,        # int | None
        n_agents,            # int | None
        capture_agents,      # bool
        end_tick,            # int
        snapshot_ticks,      # list[int] | None
        protected_agent_ids, # list[int] | None
    )

    Returns ``{"path", "elapsed_s", "size_bytes", "intervention_id",
    "release_tick", "seed"}`` — small metadata the parent can log
    without re-loading the file.
    """
    import time as _time
    (
        out_path_str, seed, intervention_id, release_tick,
        n_agents, capture_agents, end_tick, snapshot_ticks,
        protected_agent_ids,
    ) = args
    t0 = _time.time()
    traj = run_trajectory(
        seed=seed,
        intervention_id=intervention_id,
        release_tick=release_tick,
        n_agents=n_agents,
        end_tick=end_tick,
        snapshot_ticks=snapshot_ticks,
        capture_agents=capture_agents,
        protected_agent_ids=protected_agent_ids,
    )
    out_path = Path(out_path_str)
    write_json(out_path, traj)
    return {
        "path": out_path_str,
        "elapsed_s": _time.time() - t0,
        "size_bytes": out_path.stat().st_size,
        "intervention_id": intervention_id,
        "release_tick": release_tick,
        "seed": int(seed),
    }


def _pool_initializer():
    """Force single-threaded BLAS in worker processes — matches
    abm.calibration_parallel discipline (correctness + perf).
    Env vars are read by numpy/MKL/OpenBLAS at import time, so they
    only take effect in spawned worker processes (where numpy is
    imported fresh)."""
    for k, v in (
        ("OMP_NUM_THREADS", "1"),
        ("OPENBLAS_NUM_THREADS", "1"),
        ("MKL_NUM_THREADS", "1"),
        ("NUMEXPR_NUM_THREADS", "1"),
    ):
        os.environ[k] = v


def _run_pool(
    work_items: list[tuple],
    n_processes: int,
    label: str,
) -> list[dict]:
    """Run ``_publish_worker`` over ``work_items`` in a process pool.
    Logs each completed job as it lands."""
    import multiprocessing as mp
    if not work_items:
        return []
    if n_processes <= 1:
        results = []
        for i, item in enumerate(work_items, 1):
            r = _publish_worker(item)
            results.append(r)
            print(
                f"     ↳ [{i}/{len(work_items)}] "
                f"{Path(r['path']).name}: "
                f"{r['elapsed_s']:.1f}s ({r['size_bytes']/1024:.0f} KB)"
            )
        return results
    # spawn ctx — Windows default, also safest for numpy + multiprocessing.
    ctx = mp.get_context("spawn")
    with ctx.Pool(
        processes=n_processes,
        initializer=_pool_initializer,
    ) as pool:
        results: list[dict] = []
        n_total = len(work_items)
        # imap_unordered streams results as workers finish — gives live
        # progress while still hitting full parallelism.
        for i, r in enumerate(pool.imap_unordered(_publish_worker, work_items), 1):
            results.append(r)
            print(
                f"     ↳ [{i}/{n_total}] {label} "
                f"{Path(r['path']).name}: "
                f"{r['elapsed_s']:.1f}s ({r['size_bytes']/1024:.0f} KB)"
            )
        return results


# --- Intervention id resolution ----------------------------------------

INTERVENTION_FULL_IDS = (
    "X1_show_other_side",
    "X2_fix_algorithm",
    "X3_quit_cable_news",
    "X4_bipartisan_dialogue",
    "X5_ranked_choice_voting",
    "X6_shared_institutions",
    "X7_perception_correction",
)


def resolve_intervention_ids(specs: list[str] | None) -> list[str]:
    if not specs:
        return list(INTERVENTION_FULL_IDS)
    out = []
    for spec in specs:
        matches = [
            iv for iv in INTERVENTION_FULL_IDS
            if iv == spec or iv.startswith(spec + "_")
        ]
        if not matches:
            raise SystemExit(
                f"intervention id {spec!r} doesn't match any of "
                f"{INTERVENTION_FULL_IDS}"
            )
        out.append(matches[0])
    return out


# --- Main --------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", default="web/data",
        help="Output directory (default web/data/).",
    )
    parser.add_argument(
        "--n-agents", type=int, default=None,
        help="Override n_agents (default 250 from anes_full).",
    )
    parser.add_argument(
        "--interventions", nargs="+", default=None,
        help="Intervention ids to run (default all 7). Accepts 'X1' shorthand.",
    )
    parser.add_argument(
        "--release-ticks", type=int, nargs="+", default=None,
        help=f"Release ticks (default {DEFAULT_RELEASE_TICKS}).",
    )
    parser.add_argument(
        "--variance-seeds", type=int, nargs="+", default=None,
        help="Additional seeds to run for baseline variance bands (default 1..8).",
    )
    parser.add_argument(
        "--skip-variance", action="store_true",
        help="Skip the variance-band seed runs (canonical only).",
    )
    parser.add_argument(
        "--quick", action="store_true",
        help=(
            "Quick prototype mode: n_agents=80, X1+X5+X6 only at tick 90, "
            "no variance bands. ~30s wall time."
        ),
    )
    parser.add_argument(
        "-j", "--processes", type=int, default=None,
        help=(
            "Number of worker processes for the parallel phase "
            "(variance-band baselines + intervention trajectories). "
            "Default = min(work_units, os.cpu_count()). "
            "Pass -j 1 for serial (debug / comparison)."
        ),
    )
    parser.add_argument(
        "--serial", action="store_true",
        help="Force fully serial execution (equivalent to -j 1).",
    )
    args = parser.parse_args()

    # Resolve config
    if args.quick:
        n_agents = args.n_agents or 80
        intervention_ids = ["X1_show_other_side", "X5_ranked_choice_voting", "X6_shared_institutions"]
        release_ticks = args.release_ticks or [90]
        variance_seeds: list[int] = []
    else:
        n_agents = args.n_agents
        intervention_ids = resolve_intervention_ids(args.interventions)
        release_ticks = args.release_ticks or DEFAULT_RELEASE_TICKS
        if args.skip_variance:
            variance_seeds = []
        else:
            variance_seeds = args.variance_seeds or list(range(1, 9))

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "baseline").mkdir(exist_ok=True)
    (out_dir / "interventions").mkdir(exist_ok=True)
    (out_dir / "characters").mkdir(exist_ok=True)

    # Resolve process count for the parallel phase.
    n_jobs_parallel = len(variance_seeds) + len(intervention_ids) * len(release_ticks)
    if args.serial:
        n_processes = 1
    elif args.processes is not None:
        n_processes = max(1, args.processes)
    else:
        n_processes = min(n_jobs_parallel, os.cpu_count() or 1) if n_jobs_parallel else 1

    print("=" * 78)
    print("polarlab — publish web data")
    print(f"  out_dir:         {out_dir}")
    print(f"  n_agents:        {n_agents or 'default (250)'}")
    print(f"  interventions:   {intervention_ids}")
    print(f"  release_ticks:   {release_ticks}")
    print(f"  variance_seeds:  {variance_seeds or 'none (canonical only)'}")
    print(f"  end_tick:        {END_TICK}")
    print(f"  parallel:        {n_processes} worker process(es) for {n_jobs_parallel} job(s)")
    print("=" * 78)

    t_start = time.time()

    # --- 1. Character selection pass (ALL agents protected) ------------
    # Step 2 (web_demo jumpiness): archetype fit must be scored on the
    # SAME dynamics the characters will ship under — continuous lives
    # (no cohort-replacement relay) whose party follows sustained
    # ideological position (ProtectedPartyRealignment). So we score on a
    # run where EVERY agent is protected: party then tracks position, and
    # the party-keyed archetype scores (stable-D, D→R swing, …) become
    # position-coherent automatically. The 4 chosen indices are then the
    # only ones protected in the published runs.
    n_eff = int(n_agents) if n_agents else ANES_FULL_KWARGS["n_agents"]
    print(f"\n[1] Character-selection pass (seed={CANONICAL_SEED}, all protected) …")
    t0 = time.time()
    scoring_baseline = run_trajectory(
        seed=CANONICAL_SEED,
        intervention_id=None,
        release_tick=None,
        n_agents=n_agents,
        end_tick=END_TICK,
        capture_agents=True,
        protected_agent_ids=range(n_eff),
    )
    chosen_indices = select_character_indices(scoring_baseline)
    protected_ids = sorted(set(chosen_indices.values()))
    print(f"     ↳ {time.time() - t0:.1f}s  chosen={chosen_indices}  protected={protected_ids}")

    # --- 2. Published canonical baseline (protected) -------------------
    print(f"\n[2] Canonical baseline (seed={CANONICAL_SEED}, protected) …")
    t0 = time.time()
    baseline = run_trajectory(
        seed=CANONICAL_SEED,
        intervention_id=None,
        release_tick=None,
        n_agents=n_agents,
        end_tick=END_TICK,
        capture_agents=True,
        protected_agent_ids=protected_ids,
    )
    print(
        f"     ↳ {time.time() - t0:.1f}s  "
        f"({len(baseline['replacement_events'])} cohort replacements)"
    )
    write_json(out_dir / "baseline" / f"seed_{CANONICAL_SEED}.json", baseline)

    # Characters derived from the PUBLISHED (protected) baseline so beats
    # / summaries reflect the continuous-life trajectory the demo shows.
    characters = {
        arch: build_character_payload(arch, idx, baseline)
        for arch, idx in chosen_indices.items()
    }
    for char_id, char_data in characters.items():
        write_json(out_dir / "characters" / f"{char_id}.json", char_data, indent=2)

    # --- 3 + 4 in parallel. Build one work list for both ---------------
    # Each work item is a tuple consumed by _publish_worker. We batch
    # variance-band baselines (macro-only) and intervention trajectories
    # (full per-tick) into the same pool so the slowest job gates the
    # wall-clock, not the sum of two serial phases.
    print(
        f"\n[3+4] Variance bands + interventions (parallel, "
        f"{n_processes} processes) …"
    )

    work_items: list[tuple] = []

    # Variance-band baseline jobs.
    for seed in variance_seeds:
        out_path = out_dir / "baseline" / f"seed_{seed}.json"
        work_items.append((
            str(out_path),
            int(seed),
            None,         # intervention_id
            None,         # release_tick
            n_agents,
            False,        # capture_agents = False (macro-only)
            END_TICK,
            DEFAULT_NETWORK_SNAPSHOT_TICKS,
            protected_ids,
        ))

    # Intervention × release-tick jobs.
    for iv_id in intervention_ids:
        for rt in release_ticks:
            year = int(TICK_0_YEAR + rt / TICKS_PER_YEAR)
            fname = f"{iv_id}_at_{year}.json"
            out_path = out_dir / "interventions" / fname
            work_items.append((
                str(out_path),
                CANONICAL_SEED,
                iv_id,
                int(rt),
                n_agents,
                True,         # capture_agents = True (full)
                END_TICK,
                DEFAULT_NETWORK_SNAPSHOT_TICKS,
                protected_ids,
            ))

    if work_items:
        t_parallel = time.time()
        results = _run_pool(work_items, n_processes, label="")
        parallel_elapsed = time.time() - t_parallel
        sum_serial = sum(r["elapsed_s"] for r in results)
        if parallel_elapsed > 0:
            speedup = sum_serial / parallel_elapsed
            print(
                f"     ↳ parallel phase: {parallel_elapsed:.1f}s wall, "
                f"{sum_serial:.1f}s sum-of-workers "
                f"(speedup {speedup:.1f}×)"
            )

    # --- 5. Events + intervention metadata + manifest ------------------
    # (Serial — these are tiny and depend on the baseline's events list.)
    print(f"\n[5] Events / intervention metadata / manifest …")
    events_json = build_events_json(baseline["events_fired"])
    write_json(out_dir / "events.json", events_json, indent=2)

    iv_metadata = build_intervention_metadata()
    write_json(out_dir / "intervention_metadata.json", iv_metadata, indent=2)

    manifest = build_manifest(
        n_agents=baseline["n_agents"],
        release_ticks=release_ticks,
        intervention_ids=intervention_ids,
        variance_seeds=variance_seeds,
        character_ids=list(characters.keys()),
        end_tick=END_TICK,
    )
    write_json(out_dir / "manifest.json", manifest, indent=2)

    # --- Summary -------------------------------------------------------
    elapsed = time.time() - t_start
    print("\n" + "=" * 78)
    print(f"DONE in {elapsed:.1f}s wall time.")
    print(f"  Output:  {out_dir.resolve()}")

    # Quick directory sizing
    total_bytes = 0
    for p in out_dir.rglob("*.json"):
        total_bytes += p.stat().st_size
    print(f"  Total:   {total_bytes / 1024 / 1024:.1f} MB across {len(list(out_dir.rglob('*.json')))} JSON files")
    print("=" * 78)


if __name__ == "__main__":
    main()
