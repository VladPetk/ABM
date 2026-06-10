"""Phase 1 — isolation behavior of each rule on a clean substrate.

For each active rule we build a minimal substrate carrying exactly the
attrs that rule reads, run ONLY that rule, sweep its primary knob, and
check the sign + monotonicity match the rule's theoretical role.

Neighbour-iterating rules (BC, affect, backlash, perception, rewiring) run
on a sparse random graph so cost is O(n·k) not O(n²); per-agent rules
(PartyPull, Media, IdentityPull, Faction, EliteDrift) are graph-insensitive.
All (rule, knob_value, seed) cells run in one parallel batch.

Run:  .venv/Scripts/python.exe scripts/audit/phase1_isolation.py
Writes docs/internal/audit/phase1_isolation.json
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

import numpy as np

from abm.calibration_parallel import run_seeds_parallel
from abm.core.agent import Agent
from abm.core.engine import Engine
from abm.core.environment import Environment
from abm.core.network import Network
from abm.core.rules import RulePipeline
from abm.core.space import ContinuousSpace2D
from abm.core.state import AgentState

from abm.rules.influence import BoundedConfidenceInfluence
from abm.rules.party_pull import PartyPull
from abm.rules.media_consumption import MediaConsumption
from abm.rules.affective_update import AffectiveUpdate
from abm.rules.mediated_animus import MediatedAnimus
from abm.rules.noise import GaussianNoise
from abm.rules.elite_drift import EliteDrift
from abm.rules.identity_sorting import IdentitySorting
from abm.rules.identity_to_position import IdentityToIdeologyPull
from abm.rules.identity_alignment import IdentityAlignment
from abm.rules.repulsion import BacklashRepulsion
from abm.rules.tie_rewiring import TieRewiring
from abm.rules.perception_update import PerceptionUpdate
from abm.rules.party_realignment import ProtectedPartyRealignment
from abm.rules.faction_anchor import FactionAnchor
from abm.rules.cohort_replacement import CohortReplacement

from abm.metrics.polarization import variance
from abm.metrics.affective import affective_polarization, sorting_index
from abm.metrics.network import party_modularity

from abm.core.outlets import US_MEDIA_OUTLETS_2024

SEEDS = list(range(8))
BOUNDS = ((-1.0, 1.0), (-1.0, 1.0))
_OUTLETS = list(US_MEDIA_OUTLETS_2024)
_OUTLETS_BY_ID = {o.id: o for o in _OUTLETS}
_XS = {o.id: float(o.position[0]) for o in _OUTLETS}
_LEFT = min(_XS, key=_XS.get)
_RIGHT = max(_XS, key=_XS.get)


# --- helpers ---------------------------------------------------------------

def _engine(agents, env_rules, agent_rules, env_attrs, seed):
    return Engine(agents=agents, env=Environment(attrs=env_attrs),
                  space=ContinuousSpace2D(bounds=BOUNDS),
                  rules=RulePipeline(agent_rules), env_rules=env_rules, seed=seed)


def _sparse_net(n, rng, avg_deg=10):
    p = min(1.0, avg_deg / (n - 1))
    net = Network({i: set() for i in range(n)})
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                net.add_edge(i, j)
    return net


def _party_sep_pos(eng):
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    if (parties == 0).sum() == 0 or (parties == 1).sum() == 0:
        return 0.0
    return float(np.linalg.norm(pos[parties == 0].mean(0) - pos[parties == 1].mean(0)))


def _env_centroid_sep(eng):
    p = eng.env.attrs["parties"]
    return float(np.linalg.norm(p[0] - p[1]))


def _mean_align(eng):
    a = [float(x.state.attrs.get("identity_alignment", 0.0))
         for x in eng.agents if x.state.attrs.get("party") in (0, 1)]
    return float(np.mean(a)) if a else 0.0


# --- builders: return scalar metric for one (val, seed) -------------------

def b_bc_epsilon(val, seed):
    rng = np.random.default_rng(seed)
    n = 120
    agents = [Agent(id=i, state=AgentState(ideology=rng.uniform(-1, 1, 2), attrs={}))
              for i in range(n)]
    eng = _engine(agents, [], [BoundedConfidenceInfluence(epsilon=val, strength=0.1),
                  GaussianNoise(sigma=0.005)],
                  {"network": Network.complete(range(n))}, seed)
    eng.run(100)
    return variance(eng.positions())


def b_bc_strength(val, seed):
    rng = np.random.default_rng(seed)
    n = 120
    agents = [Agent(id=i, state=AgentState(ideology=rng.uniform(-1, 1, 2), attrs={}))
              for i in range(n)]
    eng = _engine(agents, [], [BoundedConfidenceInfluence(epsilon=2.0, strength=val)],
                  {"network": Network.complete(range(n))}, seed)
    eng.run(60)
    return variance(eng.positions())


def b_party_pull(val, seed):
    rng = np.random.default_rng(seed)
    agents = []
    for i in range(200):
        party = 0 if i < 100 else 1
        cue = np.array([-0.5 if party == 0 else 0.5, 0.0])
        agents.append(Agent(id=i, state=AgentState(
            ideology=np.array([rng.normal(0, 0.15), rng.normal(0, 0.15)]),
            attrs={"party": party, "party_cue": cue, "stubbornness": 0.0})))
    eng = _engine(agents, [], [PartyPull(strength=val)],
                  {"network": Network.complete(range(200)),
                   "parties": {0: np.array([-0.5, 0.0]), 1: np.array([0.5, 0.0])}}, seed)
    eng.run(60)
    return _party_sep_pos(eng)


def b_media(val, seed):
    rng = np.random.default_rng(seed)
    agents = []
    for i in range(200):
        party = 0 if i < 100 else 1
        diet = {_LEFT: 1.0} if party == 0 else {_RIGHT: 1.0}
        agents.append(Agent(id=i, state=AgentState(
            ideology=np.array([rng.normal(0, 0.15), rng.normal(0, 0.15)]),
            attrs={"party": party, "media_diet": diet, "stubbornness": 0.0})))
    eng = _engine(agents, [], [MediaConsumption(strength=val)],
                  {"network": Network.complete(range(200)), "outlets": _OUTLETS_BY_ID}, seed)
    eng.run(60)
    return _party_sep_pos(eng)


def b_affective(val, seed):
    rng = np.random.default_rng(seed)
    n = 200
    agents = []
    for i in range(n):
        party = 0 if i < n // 2 else 1
        agents.append(Agent(id=i, state=AgentState(
            ideology=np.array([-0.5 if party == 0 else 0.5, 0.0]) + rng.normal(0, 0.1, 2),
            attrs={"party": party, "affect": {1 - party: 0.0}, "identities": np.zeros(3)})))
    eng = _engine(agents, [], [AffectiveUpdate(learning_rate=val)],
                  {"network": _sparse_net(n, rng, 10),
                   "parties": {0: np.array([-0.5, 0.0]), 1: np.array([0.5, 0.0])}}, seed)
    eng.run(60)
    return affective_polarization(eng.agents)


def b_mediated_animus(val, seed):
    rng = np.random.default_rng(seed)
    n = 200
    agents = []
    for i in range(n):
        party = 0 if i < n // 2 else 1
        agents.append(Agent(id=i, state=AgentState(
            ideology=np.zeros(2),
            attrs={"party": party, "affect": {1 - party: 0.0}, "identity_alignment": 0.5})))
    eng = _engine(agents, [], [MediatedAnimus(learning_rate=val)],
                  {"network": _sparse_net(n, rng, 6), "mediated_animus_weight": 1.0}, seed)
    eng.run(60)
    return affective_polarization(eng.agents)


def b_noise(val, seed):
    rng = np.random.default_rng(seed)
    n = 200
    agents = [Agent(id=i, state=AgentState(ideology=np.zeros(2), attrs={"stubbornness": 0.0}))
              for i in range(n)]
    eng = _engine(agents, [], [GaussianNoise(sigma=val)], {"network": Network.complete(range(n))}, seed)
    eng.run(40)
    return variance(eng.positions())


def b_elite_drift(val, seed):
    rng = np.random.default_rng(seed)
    n = 100
    agents = []
    for i in range(n):
        party = 0 if i < n // 2 else 1
        cue = np.array([-0.2 if party == 0 else 0.2, 0.0])
        agents.append(Agent(id=i, state=AgentState(
            ideology=cue.copy(), attrs={"party": party, "party_cue": cue.copy()})))
    eng = _engine(agents, [EliteDrift(rate=val)], [],
                  {"network": Network.complete(range(n)),
                   "parties": {0: np.array([-0.2, 0.0]), 1: np.array([0.2, 0.0])}}, seed)
    eng.run(60)
    return _env_centroid_sep(eng)


def b_identity_sorting(val, seed):
    rng = np.random.default_rng(seed)
    n = 200
    agents = []
    for i in range(n):
        party = 0 if i < n // 2 else 1
        base = -0.1 if party == 0 else 0.1
        ids = np.clip(np.array([base + rng.normal(0, 0.3) for _ in range(3)]), -1, 1)
        agents.append(Agent(id=i, state=AgentState(
            ideology=np.zeros(2), attrs={"party": party, "identities": ids})))
    eng = _engine(agents, [], [IdentitySorting(sort_rate=val, step=0.15, differentiation=0.5)],
                  {"network": Network.complete(range(n))}, seed)
    eng.run(100)
    return sorting_index(eng.agents)


def b_identity_pull(val, seed):
    rng = np.random.default_rng(seed)
    n = 200
    agents = []
    for i in range(n):
        party = 0 if i < n // 2 else 1
        base = -0.5 if party == 0 else 0.5
        ids = np.clip(np.array([base + rng.normal(0, 0.2) for _ in range(3)]), -1, 1)
        agents.append(Agent(id=i, state=AgentState(
            ideology=np.array([rng.normal(0, 0.05), rng.normal(0, 0.05)]),
            attrs={"party": party, "identities": ids, "stubbornness": 0.0})))
    eng = _engine(agents, [], [IdentityToIdeologyPull(strength_x=val, strength_y=val)],
                  {"network": Network.complete(range(n)), "party_issue_coupling": 1.0}, seed)
    eng.run(60)
    return _party_sep_pos(eng)


def b_identity_alignment(val, seed):
    rng = np.random.default_rng(seed)
    n = 200
    agents = []
    for i in range(n):
        party = 0 if i < n // 2 else 1
        sign = -1.0 if party == 0 else 1.0
        ids = np.clip(np.array([sign * 0.6 + rng.normal(0, 0.1) for _ in range(3)]), -1, 1)
        agents.append(Agent(id=i, state=AgentState(
            ideology=np.zeros(2),
            attrs={"party": party, "identities": ids, "identity_alignment": 0.0})))
    eng = _engine(agents, [], [IdentityAlignment(rate=val)],
                  {"network": Network.complete(range(n)), "evidence_regrade": True,
                   "party_identity_centers": {0: np.array([-0.6, -0.6, -0.6]),
                                              1: np.array([0.6, 0.6, 0.6])}}, seed)
    eng.run(10)
    return _mean_align(eng)


def b_backlash(val, seed):
    rng = np.random.default_rng(seed)
    n = 200
    agents = []
    for i in range(n):
        party = 0 if i < n // 2 else 1
        agents.append(Agent(id=i, state=AgentState(
            ideology=np.array([rng.normal(0, 0.1), rng.normal(0, 0.1)]),
            attrs={"party": party, "affect": {1 - party: -0.6}, "stubbornness": 0.0})))
    eng = _engine(agents, [], [BacklashRepulsion(epsilon=0.3, max_range=1.5,
                  strength=val, affect_threshold=-0.3)],
                  {"network": _sparse_net(n, rng, 10)}, seed)
    eng.run(40)
    return _party_sep_pos(eng)


def b_tie_rewiring(val, seed):
    rng = np.random.default_rng(seed)
    n = 150
    agents = []
    for i in range(n):
        party = 0 if i < n // 2 else 1
        cx = -0.5 if party == 0 else 0.5
        agents.append(Agent(id=i, state=AgentState(
            ideology=np.array([cx + rng.normal(0, 0.1), rng.normal(0, 0.1)]),
            attrs={"party": party, "affect": {1 - party: -0.3},
                   "social_coord": float(rng.normal(0, 1))})))
    eng = _engine(agents, [TieRewiring(rewire_rate=val, affect_weight_rewire=0.5)], [],
                  {"network": _sparse_net(n, rng, 10)}, seed)
    eng.run(80)
    return party_modularity(eng.agents, eng.env.attrs["network"])


def b_perception(val, seed):
    rng = np.random.default_rng(seed)
    n = 200
    agents = []
    for i in range(n):
        party = 0 if i < n // 2 else 1
        actual_other = np.array([0.5 if party == 0 else -0.5, 0.0])
        biased = actual_other * 1.6
        agents.append(Agent(id=i, state=AgentState(
            ideology=np.array([-0.5 if party == 0 else 0.5, 0.0]),
            attrs={"party": party, "perceived_other_party": {1 - party: biased}})))
    eng = _engine(agents, [], [PerceptionUpdate(correction_rate=val)],
                  {"network": _sparse_net(n, rng, 12),
                   "parties": {0: np.array([-0.5, 0.0]), 1: np.array([0.5, 0.0])}}, seed)
    eng.run(40)
    es = []
    for a in eng.agents:
        p = a.state.attrs["party"]
        perc = a.state.attrs["perceived_other_party"][1 - p]
        actual = np.array([0.5 if p == 0 else -0.5, 0.0])
        es.append(float(np.linalg.norm(perc - actual)))
    return float(np.mean(es))


def b_protected_realign(val, seed):
    n = 100
    agents = []
    for i in range(n):
        agents.append(Agent(id=i, state=AgentState(
            ideology=np.array([0.5, 0.0]),
            attrs={"party": 0, "do_not_replace": True, "affect": {1: -0.3},
                   "party_cue": np.array([-0.5, 0.0])})))
    eng = _engine(agents, [ProtectedPartyRealignment(x_threshold=val, sustain_ticks=6)], [],
                  {"network": Network.complete(range(n)),
                   "parties": {0: np.array([-0.5, 0.0]), 1: np.array([0.5, 0.0])}}, seed)
    eng.run(20)
    return float(sum(1 for a in eng.agents if a.state.attrs["party"] == 1))


_FACTION_CENTER = np.array([0.7, 0.4])


def b_faction_anchor(val, seed):
    rng = np.random.default_rng(seed)
    n = 150
    agents = []
    for i in range(n):
        agents.append(Agent(id=i, state=AgentState(
            ideology=np.array([rng.normal(0, 0.1), rng.normal(0, 0.1)]),
            attrs={"party": 1, "faction": "X", "faction_center": _FACTION_CENTER.copy(),
                   "stubbornness": 0.0})))
    eng = _engine(agents, [], [FactionAnchor(strength=val)],
                  {"network": Network.complete(range(n))}, seed)
    eng.run(40)
    d = [float(np.linalg.norm(a.state.ideology - _FACTION_CENTER)) for a in eng.agents]
    return float(np.mean(d))


def b_cohort(val, seed):
    rng = np.random.default_rng(seed)
    n = 200
    agents = []
    for i in range(n):
        party = 0 if i < n // 2 else 1
        c = np.array([-0.3 if party == 0 else 0.3, 0.0])
        agents.append(Agent(id=i, state=AgentState(
            ideology=c.copy(),
            attrs={"party": party, "party_cue": c.copy(), "affect": {1 - party: -0.2},
                   "identities": np.zeros(3), "stubbornness": 0.5, "anchor": c.copy(),
                   "media_diet": {}})))
    eng = _engine(agents, [CohortReplacement(replacement_rate=val)], [],
                  {"network": Network.complete(range(n)),
                   "parties": {0: np.array([-0.3, 0.0]), 1: np.array([0.3, 0.0])},
                   "replacement_events": []}, seed)
    eng.run(60)
    return float(len(eng.env.attrs.get("replacement_events", [])))


# --- registry: name -> (builder, knob_values, expect, target_desc) --------

REGISTRY = {
    "BoundedConfidenceInfluence.epsilon": (b_bc_epsilon, [0.10, 0.20, 0.35, 0.6, 2.0],
        "dec", "final variance (loose eps -> consensus)"),
    "BoundedConfidenceInfluence.strength": (b_bc_strength, [0.0, 0.02, 0.05, 0.1, 0.25],
        "dec", "final variance (more influence -> faster consensus)"),
    "PartyPull.strength": (b_party_pull, [0.0, 0.02, 0.05, 0.1, 0.25],
        "inc", "mass party separation"),
    "MediaConsumption.strength": (b_media, [0.0, 0.02, 0.05, 0.1, 0.25],
        "inc", "separation toward partisan diets"),
    "AffectiveUpdate.learning_rate": (b_affective, [0.0, 0.005, 0.01, 0.03, 0.08],
        "neg", "out-party warmth"),
    "MediatedAnimus.learning_rate": (b_mediated_animus, [0.0, 0.005, 0.014, 0.03, 0.08],
        "neg", "out-party warmth (parasocial)"),
    "GaussianNoise.sigma": (b_noise, [0.0, 0.01, 0.05, 0.1, 0.2],
        "inc", "position variance"),
    "EliteDrift.rate": (b_elite_drift, [0.0, 0.003, 0.009, 0.013, 0.03],
        "inc", "party centroid separation"),
    "IdentitySorting.sort_rate": (b_identity_sorting, [0.0, 0.01, 0.03, 0.05, 0.1],
        "inc", "mega-identity sorting_index"),
    "IdentityToIdeologyPull.strength": (b_identity_pull, [0.0, 0.01, 0.02, 0.04, 0.1],
        "inc", "party separation"),
    "IdentityAlignment.rate": (b_identity_alignment, [0.0, 0.02, 0.05, 0.1, 0.3],
        "inc", "alignment @ fixed horizon"),
    "BacklashRepulsion.strength": (b_backlash, [0.0, 0.02, 0.05, 0.1, 0.25],
        "inc", "separation (backfire)"),
    "TieRewiring.rewire_rate": (b_tie_rewiring, [0.0, 0.02, 0.05, 0.1, 0.2],
        "inc", "party modularity"),
    "PerceptionUpdate.correction_rate": (b_perception, [0.0, 0.01, 0.05, 0.1, 0.3],
        "dec", "perception error"),
    "ProtectedPartyRealignment.x_threshold": (b_protected_realign, [0.05, 0.12, 0.3, 0.6],
        "dec", "# party flips"),
    "FactionAnchor.strength": (b_faction_anchor, [0.0, 0.02, 0.05, 0.1, 0.25],
        "dec", "distance to faction center"),
    "CohortReplacement.replacement_rate": (b_cohort, [0.0, 0.001, 0.003, 0.01, 0.03],
        "inc", "# replacement events"),
}


def p1_worker(arg):
    """arg = (name, val, seed). Dispatch via REGISTRY; return scalar metric."""
    name, val, seed = arg
    builder = REGISTRY[name][0]
    try:
        return (name, val, seed, float(builder(val, seed)))
    except Exception as e:  # noqa: BLE001
        return (name, val, seed, None, f"{type(e).__name__}: {e}")


def verdict(pairs, expect):
    ys = [p[1] for p in pairs]
    lo, hi = ys[0], ys[-1]
    diffs = [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]
    if expect == "inc":
        mono = all(d >= -1e-6 for d in diffs); ok = hi > lo + 1e-6
    elif expect in ("dec", "neg"):
        mono = all(d <= 1e-6 for d in diffs); ok = hi < lo - 1e-6
    else:
        mono = ok = None
    return {"endpoints": [lo, hi], "expect": expect,
            "sign_ok": bool(ok), "monotonic": bool(mono)}


def main():
    work = []
    for name, (builder, vals, expect, target) in REGISTRY.items():
        for v in vals:
            for s in SEEDS:
                work.append((name, v, s))
    print(f"{len(work)} isolation cells across {len(REGISTRY)} rules x {len(SEEDS)} seeds...")
    flat = run_seeds_parallel(p1_worker, work)

    by = {}
    errors = {}
    for rec in flat:
        name, val = rec[0], rec[1]
        if len(rec) == 5:
            errors[name] = rec[4]
            continue
        by.setdefault(name, {}).setdefault(val, []).append(rec[3])

    results = {}
    for name, (builder, vals, expect, target) in REGISTRY.items():
        if name not in by:
            results[name] = {"target": target, "error": errors.get(name, "no data")}
            print(f"[ERROR  ] {name:42s} {errors.get(name)}")
            continue
        pairs = [(v, float(np.mean(by[name][v]))) for v in vals if v in by[name]]
        ver = verdict(pairs, expect)
        results[name] = {"target": target, "sweep": pairs, **ver}
        flag = "OK" if (ver["sign_ok"] and ver["monotonic"]) else (
            "SIGN?" if not ver["sign_ok"] else "NONMONO")
        print(f"[{flag:7}] {name:42s} {target:40s} {[round(y,4) for _,y in pairs]}")

    outp = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                        "docs", "internal", "audit", "phase1_isolation.json"))
    with open(outp, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nwrote {outp}")


if __name__ == "__main__":
    main()
