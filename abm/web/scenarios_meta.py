"""
Web-facing scenario metadata.

Plain-English everywhere users see it. Under the hood the Python rule names
stay academic (BoundedConfidenceInfluence, etc.) — the rest of the codebase
shouldn't know about marketing copy. This module is the single translation
layer between the engine and the public site.
"""
from __future__ import annotations

from typing import Any


# ----------------------------------------------------------------------------
# Tooltip copy — plain English, real-world framing, ~1 sentence each.
# ----------------------------------------------------------------------------

_PARAM_INFO = {
    "n_agents": (
        "How many people are in this society. More = smoother story, slower ticks."
    ),
    "epsilon": (
        "How willing each person is to consider opinions different from their own. "
        "Lower = they only listen to people who already agree with them; higher = "
        "they engage across the divide."
    ),
    "attraction": (
        "How strongly people pull toward the average of those they consider reasonable. "
        "High peer influence + low open-mindedness is the textbook echo-chamber recipe."
    ),
    "repulsion": (
        "How much people push back AWAY from views they find unreasonable (the 'backfire' "
        "effect). Empirically contested — the famous 2018 Bail study found it, but later "
        "Meta/2020 work mostly didn't. Off by default."
    ),
    "noise": (
        "Random shifts in personal opinion — life events, mood, a striking conversation. "
        "Keeps the system off brittle equilibria."
    ),
    "party_pull": (
        "How loyal people are to their party — drifts each person toward where their "
        "party's leaders are right now. The 'taking your cue from your team' effect "
        "(Hetherington 2001)."
    ),
    "affect_lr": (
        "How quickly warmth toward the OTHER party shifts based on encounters. Each "
        "interaction nudges your feelings up (if you felt seen) or down (if you didn't)."
    ),
    "n_identities": (
        "How many overlapping identities each person carries (race, religion, geography, "
        "education, lifestyle…). Required for the Mason 'mega-identity' dynamic."
    ),
    "sort_rate": (
        "How fast identities stack on party — each tick a small chance that one identity "
        "dimension drifts toward your party's average AND away from the out-party's. "
        "This is the slow-burn force that turned 'I'm a Democrat' into 'I'm a Democrat AND "
        "secular AND urban AND college-educated' over decades (Mason 2018)."
    ),
    "identity_weight": (
        "How much your IDENTITY overlap with someone (vs your ISSUE distance) drives how "
        "you feel about them. 0 = pure 'we disagree on policy', 1 = pure 'they're not my "
        "kind of people'."
    ),
    "identity_bias": (
        "How aligned identities ALREADY are with party at the start. 0 = totally "
        "cross-cutting; 0.6 = strongly aligned. Real-world 1970s ≈ 0.3."
    ),
    "elite_drift_rate": (
        "How fast party leaders themselves move outward over time. McCarty-Poole-Rosenthal: "
        "elite polarization has risen monotonically in the US since the 1970s, dragging "
        "mass attitudes with it."
    ),
    "media_period": (
        "How often a major media event hits (elections, scandals, crises). Lower = more "
        "frequent shocks."
    ),
    "media_strength": (
        "How much each event pulls the whole population toward a (random) position."
    ),
    "partisan_media_strength": (
        "Legacy partisan-media pull (deprecated in favor of media_consumption_strength)."
    ),
    "media_consumption_strength": (
        "How hard the outlets a person consumes pull them toward those outlets' positions. "
        "Higher = your media diet drags your opinions around more. Click any agent to "
        "see and edit their diet."
    ),
    "homophily_radius": (
        "Argument-cascade only: only people within this ideological distance share "
        "arguments with each other."
    ),
    "step": (
        "Argument-cascade only: how much one adopted argument shifts your view. Tiny + "
        "homophily filter still produces bi-polarization (Mäs–Flache 2013)."
    ),
}


def _slider(name: str, label: str, lo: float, hi: float, step: float) -> dict:
    return {"name": name, "label": label, "min": lo, "max": hi, "step": step, "info": _PARAM_INFO[name]}


# ----------------------------------------------------------------------------
# Scenarios — friendly story names + plain-English slider labels.
# ----------------------------------------------------------------------------

SCENARIOS: dict[str, dict[str, Any]] = {
    "two_party_sorting": {
        "lead": "Two-party",
        "tail": "America",
        "title": "Two-party America",
        "tagline": "Two big tents. Identities stack on party. Out-party warmth collapses.",
        "default_params": {
            "n_agents": 600,
            "epsilon": 0.3,
            "attraction": 0.05,
            "party_pull": 0.04,
            "affect_lr": 0.01,
            "n_identities": 3,
            "sort_rate": 0.05,
            "identity_weight": 0.5,
            "identity_bias": 0.3,
            "noise": 0.01,
        },
        "params": [
            _slider("epsilon",         "open-mindedness",   0.05, 1.0, 0.05),
            _slider("attraction",      "peer influence",    0.0,  0.5, 0.01),
            _slider("party_pull",      "party loyalty",     0.0,  0.2, 0.01),
            _slider("affect_lr",       "warmth shift rate", 0.0,  0.05, 0.005),
            _slider("sort_rate",       "identity tribalism",0.0,  0.2, 0.01),
            _slider("identity_weight", "identity vs issues",0.0,  1.0, 0.05),
            _slider("noise",           "random life events",0.0,  0.05, 0.002),
        ],
        "rule_param_map": {
            "epsilon": [("BoundedConfidenceInfluence", "epsilon"), ("AffectiveUpdate", "radius")],
            "attraction": [("BoundedConfidenceInfluence", "strength")],
            "party_pull": [("PartyPull", "strength")],
            "affect_lr": [("AffectiveUpdate", "lr")],
            "sort_rate": [("IdentitySorting", "sort_rate")],
            "identity_weight": [("AffectiveUpdate", "identity_weight")],
            "noise": [("GaussianNoise", "sigma")],
        },
    },

    "multi_party_4": {
        "lead": "European",
        "tail": "multiparty",
        "title": "European multiparty",
        "tagline": "Four parties in the four corners. Cross-cutting affect keeps the heat lower.",
        "default_params": {
            "n_agents": 700,
            "epsilon": 0.3,
            "attraction": 0.05,
            "party_pull": 0.04,
            "affect_lr": 0.01,
            "n_identities": 3,
            "sort_rate": 0.05,
            "identity_weight": 0.5,
            "identity_bias": 0.3,
            "noise": 0.01,
        },
        "params": [
            _slider("epsilon",         "open-mindedness",   0.05, 1.0, 0.05),
            _slider("attraction",      "peer influence",    0.0,  0.5, 0.01),
            _slider("party_pull",      "party loyalty",     0.0,  0.2, 0.01),
            _slider("affect_lr",       "warmth shift rate", 0.0,  0.05, 0.005),
            _slider("sort_rate",       "identity tribalism",0.0,  0.2, 0.01),
            _slider("identity_weight", "identity vs issues",0.0,  1.0, 0.05),
            _slider("noise",           "random life events",0.0,  0.05, 0.002),
        ],
        "rule_param_map": {
            "epsilon": [("BoundedConfidenceInfluence", "epsilon"), ("AffectiveUpdate", "radius")],
            "attraction": [("BoundedConfidenceInfluence", "strength")],
            "party_pull": [("PartyPull", "strength")],
            "affect_lr": [("AffectiveUpdate", "lr")],
            "sort_rate": [("IdentitySorting", "sort_rate")],
            "identity_weight": [("AffectiveUpdate", "identity_weight")],
            "noise": [("GaussianNoise", "sigma")],
        },
    },

    "elite_dynamics": {
        "lead": "Cable news",
        "tail": "era",
        "title": "Cable news era",
        "tagline": "Parties drift outward; media shocks shake the crowd; heavy partisan-media consumers polarize further.",
        "default_params": {
            "n_agents": 600,
            "epsilon": 0.3,
            "attraction": 0.05,
            "party_pull": 0.04,
            "affect_lr": 0.01,
            "n_identities": 3,
            "sort_rate": 0.05,
            "identity_weight": 0.5,
            "identity_bias": 0.3,
            "elite_drift_rate": 0.0008,
            "media_period": 120,
            "media_strength": 0.06,
            "media_consumption_strength": 0.04,
            "noise": 0.01,
        },
        "params": [
            _slider("epsilon",                    "open-mindedness",     0.05, 1.0, 0.05),
            _slider("party_pull",                 "party loyalty",       0.0,  0.2, 0.01),
            _slider("media_consumption_strength", "media-diet pull",     0.0,  0.15, 0.005),
            _slider("elite_drift_rate",           "elite divergence",    0.0,  0.003, 0.0001),
            _slider("media_period",               "event interval",      20,   500, 10),
            _slider("media_strength",             "event impact",        0.0,  0.2, 0.01),
            _slider("noise",                      "random life events",  0.0,  0.05, 0.002),
        ],
        "rule_param_map": {
            "epsilon": [("BoundedConfidenceInfluence", "epsilon"), ("AffectiveUpdate", "radius")],
            "party_pull": [("PartyPull", "strength")],
            "media_consumption_strength": [("MediaConsumption", "strength")],
            "elite_drift_rate": [("EliteDrift", "rate")],
            "media_period": [("MediaShock", "period")],
            "media_strength": [("MediaShock", "strength")],
            "noise": [("GaussianNoise", "sigma")],
        },
    },

    "actb": {
        "lead": "Social-media",
        "tail": "echoes",
        "title": "Social-media echoes",
        "tagline": "No parties, no leaders — just homophily plus argument-sharing. Bi-polarization still emerges (Mäs-Flache).",
        "default_params": {
            "n_agents": 600,
            "homophily_radius": 0.3,
            "step": 0.02,
            "noise": 0.01,
        },
        "params": [
            _slider("homophily_radius", "filter-bubble radius", 0.05, 1.0, 0.05),
            _slider("step",             "share strength",       0.0,  0.1, 0.005),
            _slider("noise",            "random life events",   0.0,  0.05, 0.002),
        ],
        "rule_param_map": {
            "homophily_radius": [("ArgumentExchange", "homophily_radius")],
            "step": [("ArgumentExchange", "step")],
            "noise": [("GaussianNoise", "sigma")],
        },
    },
}


DEFAULT_SCENARIO = "two_party_sorting"


def list_for_ui() -> list[dict]:
    return [
        {
            "key": key,
            "lead": meta["lead"],
            "tail": meta["tail"],
            "title": meta["title"],
            "tagline": meta["tagline"],
        }
        for key, meta in SCENARIOS.items()
    ]


def detail_for_ui(key: str) -> dict:
    meta = SCENARIOS[key]
    return {
        "key": key,
        "title": meta["title"],
        "tagline": meta["tagline"],
        "params": meta["params"],
        "defaults": meta["default_params"],
    }


def apply_param(engine, scenario_key: str, name: str, value) -> bool:
    """Mutate the relevant rule attribute(s) on a running engine."""
    meta = SCENARIOS.get(scenario_key)
    if not meta:
        return False
    targets = meta.get("rule_param_map", {}).get(name, [])
    if not targets:
        return False
    changed = False
    for cls_name, attr_name in targets:
        for rule in list(engine.env_rules) + list(engine.rules.rules):
            if type(rule).__name__ == cls_name and hasattr(rule, attr_name):
                v = value
                if cls_name == "MediaShock" and attr_name == "period":
                    v = int(round(value))
                setattr(rule, attr_name, v)
                changed = True
    return changed
