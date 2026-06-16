"""Method-B published baseline builder (commit 411de22 verdict): pool K clean
seeds, draw a reproducible uniform 250-agent cross-seed subsample, carry each
sampled agent's trajectory + ghost-fade through, and attach the ensemble-mean macro
(plus a single-seed macro_ctrl for intervention-Δ differencing). No protection, no
characters — the published baseline is the model's faithful ensemble center.
"""
from __future__ import annotations
import numpy as np

# Reproducible subsample RNG seed (recorded in the manifest). Do NOT change without
# re-blessing the published cloud — the subsample is deterministic given this seed.
SUBSAMPLE_RNG_SEED = 20260616
ENSEMBLE_SEEDS = tuple(range(8))   # K = 8 clean seeds pooled


def build_methodb_baseline(per_seed_trajs: list[dict], n_per_seed: int | None = None,
                           n_sample: int | None = None,
                           rng_seed: int = SUBSAMPLE_RNG_SEED) -> dict:
    """per_seed_trajs: list of K full run_trajectory dicts (capture_agents=True),
    seed s at list index s. Returns one published baseline dict with n_sample agents
    (defaults to the per-seed population size)."""
    K = len(per_seed_trajs)
    n_ticks = per_seed_trajs[0]["n_ticks"]
    if n_per_seed is None:
        n_per_seed = len(per_seed_trajs[0]["ticks"][0]["positions"])
    if n_sample is None:
        n_sample = n_per_seed
    rng = np.random.default_rng(rng_seed)

    # ---- uniform cross-seed subsample of global indices g = s*n_per_seed + i ----
    total = K * n_per_seed
    sampled = np.sort(rng.choice(total, size=n_sample, replace=False))
    seed_of = sampled // n_per_seed       # which seed each published agent came from
    local_of = sampled % n_per_seed       # its local index within that seed
    g2pub = {int(g): p for p, g in enumerate(sampled)}   # global -> published idx

    # ---- per-tick state: gather each sampled agent from its source seed ----
    ticks = []
    for t in range(n_ticks):
        pos, party, affect, faction = [], [], [], []
        for s, li in zip(seed_of, local_of):
            tk = per_seed_trajs[int(s)]["ticks"][t]
            pos.append(tk["positions"][int(li)])
            party.append(tk["party"][int(li)])
            affect.append(tk["affect"][int(li)])
            faction.append(tk["faction"][int(li)])
        ticks.append({"positions": pos, "party": party, "affect": affect, "faction": faction})

    # ---- replacement_events: concat per-seed with global offset, restrict + remap ----
    repl = []
    for s in range(K):
        for ev in per_seed_trajs[s].get("replacement_events", []):
            tick, li = int(ev[0]), int(ev[1])
            g = s * n_per_seed + li
            if g in g2pub:
                repl.append([tick, g2pub[g]])
    repl.sort()

    # ---- agent_static for the sampled agents (republished ids 0..n_sample-1) ----
    base_static = per_seed_trajs[0].get("agent_static")
    agent_static = None
    if base_static is not None:
        agent_static = []
        for p, (s, li) in enumerate(zip(seed_of, local_of)):
            st = dict(per_seed_trajs[int(s)]["agent_static"][int(li)])
            st["id"] = p
            agent_static.append(st)

    # ---- macro: ensemble MEAN across the K seeds (per-tick, per-field) ----
    macro_keys = list(per_seed_trajs[0]["macro"][0].keys())
    macro = []
    for t in range(n_ticks):
        row = {}
        for k in macro_keys:
            vals = [per_seed_trajs[s]["macro"][t][k] for s in range(K)]
            v0 = vals[0]
            if isinstance(v0, (list, tuple)):   # e.g. party_centroid_0/1 = [x, y]
                row[k] = [float(np.mean([v[j] for v in vals])) for j in range(len(v0))]
            else:
                row[k] = float(np.mean(vals))
        macro.append(row)
    # macro_ctrl: seed-0's own macro — the single-seed control the single-seed
    # intervention Δ is differenced against (preserves the blessed phase10 buckets;
    # the displayed `macro` above is the ensemble mean).
    macro_ctrl = list(per_seed_trajs[0]["macro"])

    return {
        "n_agents": n_sample,
        "n_ticks": n_ticks,
        "seed": "methodB_ensemble_subsample",
        "subsample_rng_seed": rng_seed,
        "ensemble_seeds": list(ENSEMBLE_SEEDS),
        "intervention_seed": int(ENSEMBLE_SEEDS[0]),   # single-seed Δ control
        "tick_0_year": per_seed_trajs[0]["tick_0_year"],
        "ticks_per_year": per_seed_trajs[0]["ticks_per_year"],
        "agent_static": agent_static,
        "ticks": ticks,
        "macro": macro,
        "macro_ctrl": macro_ctrl,
        "network_snapshots": per_seed_trajs[0].get("network_snapshots", {}),
        "events_fired": per_seed_trajs[0].get("events_fired", []),
        "replacement_events": repl,
    }
