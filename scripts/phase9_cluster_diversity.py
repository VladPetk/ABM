"""Phase 9 cluster-diversity investigation harness."""
from __future__ import annotations

import os
import sys
import json
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from scipy.stats import skew, kurtosis

from abm.calibration_parallel import run_seeds_parallel
from abm.pillars import historical_arc as ha
from abm.pillars.schedule import run_to


SEEDS = tuple(range(int(os.environ.get("PHASE9_NSEEDS", "5"))))
N = int(os.environ.get("PHASE9_N", "250"))
IND = float(os.environ.get("PHASE9_IND", "0.12"))


def participation_ratio(pos):
    cov = np.cov(pos.T)
    eigs = np.linalg.eigvalsh(cov)
    return float(np.sum(eigs) ** 2 / np.sum(eigs ** 2))


def per_quadrant_entropy(pos):
    sx = np.sign(pos[:, 0])
    sy = np.sign(pos[:, 1])
    counts = np.zeros(4)
    for q, (qx, qy) in enumerate([(-1, -1), (-1, 1), (1, -1), (1, 1)]):
        counts[q] = ((sx == qx) & (sy == qy)).sum()
    p = counts / counts.sum()
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def effective_k(pos, k_max=8):
    best_k, best_s = 2, -1
    for k in range(2, min(k_max + 1, len(pos) // 8)):
        try:
            lab = KMeans(n_clusters=k, n_init=10, random_state=0).fit_predict(pos)
            if len(set(lab)) < 2:
                continue
            s = silhouette_score(pos, lab)
            if s > best_s:
                best_s, best_k = s, k
        except Exception:
            pass
    return best_k, float(best_s)


def bimodality(x):
    n = len(x)
    sk = skew(x)
    ku = kurtosis(x)
    return float((sk ** 2 + 1) / (ku + 3 * ((n - 1) ** 2 / ((n - 2) * (n - 3)))))


def within_party_sd(pos, parties, axis):
    sds = []
    for p in (0, 1):
        m = parties == p
        if m.sum() > 1:
            sds.append(float(pos[m, axis].std()))
    return float(np.mean(sds)) if sds else 0.0


def measure_diversity(eng):
    pos = np.array([a.state.ideology for a in eng.agents])
    parties = np.array([a.state.attrs.get("party", 2) for a in eng.agents])
    k, sil = effective_k(pos)
    return {
        "pr": participation_ratio(pos),
        "quad_h": per_quadrant_entropy(pos),
        "k_star": k,
        "sil": sil,
        "bim_x": bimodality(pos[:, 0]),
        "bim_y": bimodality(pos[:, 1]),
        "wp_sd_x": within_party_sd(pos, parties, 0),
        "wp_sd_y": within_party_sd(pos, parties, 1),
        "global_sd_x": float(pos[:, 0].std()),
        "global_sd_y": float(pos[:, 1].std()),
    }


US_FACTIONS = {
    "DSA_socialists":         {"center": (-0.65, -0.50), "weight": 0.06, "party": 0},
    "progressive_liberals":   {"center": (-0.40, -0.55), "weight": 0.13, "party": 0},
    "mainstream_dems":        {"center": (-0.30, -0.10), "weight": 0.18, "party": 0},
    "blue_dog_dems":          {"center": (-0.15, +0.25), "weight": 0.08, "party": 0},
    "evangelical_dems":       {"center": (-0.20, +0.40), "weight": 0.04, "party": 0},
    "libertarian_reps":       {"center": (+0.55, -0.30), "weight": 0.07, "party": 1},
    "classical_liberals":     {"center": (+0.25, -0.10), "weight": 0.08, "party": 1},
    "mainstream_reps":        {"center": (+0.30, +0.15), "weight": 0.14, "party": 1},
    "MAGA_populists":         {"center": (+0.45, +0.50), "weight": 0.13, "party": 1},
    "sovereign_hard_right":   {"center": (+0.70, +0.65), "weight": 0.04, "party": 1},
    "crunchy_centrists":      {"center": (-0.05, +0.10), "weight": 0.05, "party": None},
}


def _seed_us_factions(eng, sd_within=0.08, seed=0):
    rng = np.random.default_rng(int(seed) + 12345)
    fac_names = list(US_FACTIONS.keys())
    fac_centers = np.array([US_FACTIONS[n]["center"] for n in fac_names])
    fac_weights = np.array([US_FACTIONS[n]["weight"] for n in fac_names])
    fac_weights = fac_weights / fac_weights.sum()
    fac_parties = [US_FACTIONS[n]["party"] for n in fac_names]
    for a in eng.agents:
        if a.state.attrs.get("party") == 2:
            continue
        fac_id = int(rng.choice(len(fac_names), p=fac_weights))
        center = fac_centers[fac_id]
        new_pos = np.clip(center + rng.normal(0, sd_within, size=2), -1.0, 1.0)
        if fac_parties[fac_id] is None:
            new_party = 1 if new_pos[0] >= 0 else 0
        else:
            new_party = fac_parties[fac_id]
        a.state.ideology = new_pos
        a.state.attrs["origin"] = new_pos.copy()
        a.state.attrs["anchor"] = new_pos.copy()
        a.state.attrs["party"] = new_party
        a.state.attrs["group"] = new_party
        a.state.attrs["faction_id"] = fac_id
        a.state.attrs["faction_name"] = fac_names[fac_id]
        a.state.attrs["faction_cue"] = center.copy()
        a.state.attrs["party_cue"] = np.clip(
            center + rng.normal(0, 0.04, size=2), -1.0, 1.0
        )
        other_party = 1 - new_party
        if isinstance(a.state.attrs.get("affect"), dict):
            new_val = float(np.clip(rng.normal(-0.25, 0.10), -1.0, 1.0))
            a.state.attrs["affect"] = {other_party: new_val}


def _set_partypull_strength(eng, strength):
    for r in eng.rules.rules:
        if type(r).__name__ == "PartyPull":
            r.strength = strength


def _set_media_strength(eng, strength):
    for r in eng.rules.rules:
        if type(r).__name__ == "MediaConsumption":
            r.strength = strength


def _set_bc_epsilon(eng, eps):
    for r in eng.rules.rules:
        if type(r).__name__ == "BoundedConfidenceInfluence":
            r.epsilon = eps


def _set_identity_sorting_rate(eng, rate):
    for r in eng.rules.rules:
        if type(r).__name__ == "IdentitySorting":
            r.sort_rate = rate


def _bump_stubbornness(eng, factor=1.5, cap=0.85):
    for a in eng.agents:
        if a.state.attrs.get("party") == 2:
            continue
        s = float(a.state.attrs.get("stubbornness", 0.0))
        a.state.attrs["stubbornness"] = float(min(cap, s * factor))


def _bump_faction_stubbornness_by_extremity(eng, base_boost=0.0, edge_boost=0.4, cap=0.90):
    for a in eng.agents:
        if a.state.attrs.get("party") == 2:
            continue
        cue = a.state.attrs.get("faction_cue", a.state.attrs.get("party_cue"))
        if cue is None:
            continue
        d_from_origin = float(np.linalg.norm(cue))
        s_old = float(a.state.attrs.get("stubbornness", 0.0))
        boost = base_boost + edge_boost * d_from_origin
        a.state.attrs["stubbornness"] = float(min(cap, s_old + boost))


def variant_baseline(eng, seed=0):
    pass


def variant_factions_only_central_pp(eng, seed=0):
    _seed_us_factions(eng, seed=seed)
    parties = eng.env.attrs.get("parties", {})
    for a in eng.agents:
        p = a.state.attrs.get("party")
        if p in (0, 1) and p in parties:
            a.state.attrs["party_cue"] = parties[p].copy()


def variant_factions_factional_cues(eng, seed=0):
    _seed_us_factions(eng, seed=seed)


def variant_factions_weakened_pp(eng, seed=0):
    _seed_us_factions(eng, seed=seed)
    _set_partypull_strength(eng, 0.03)


def variant_factions_weak_pp_weak_media(eng, seed=0):
    _seed_us_factions(eng, seed=seed)
    _set_partypull_strength(eng, 0.03)
    _set_media_strength(eng, 0.02)


def variant_factions_weak_pp_zero_media_cue(eng, seed=0):
    _seed_us_factions(eng, seed=seed)
    _set_partypull_strength(eng, 0.03)
    for a in eng.agents:
        if "media_cue" in a.state.attrs:
            a.state.attrs["media_cue"] = np.zeros(2)


def variant_factions_distance_pp(eng, seed=0):
    _seed_us_factions(eng, seed=seed)
    parties = eng.env.attrs.get("parties", {})
    for a in eng.agents:
        p = a.state.attrs.get("party")
        if p not in (0, 1) or p not in parties:
            continue
        centroid = parties[p]
        d = float(np.linalg.norm(a.state.ideology - centroid))
        scale = max(0.2, 1.0 - 1.2 * d)
        a.state.attrs["identity_strength"] = float(
            a.state.attrs.get("identity_strength", 0.5) * scale
        )


def variant_factions_factional_pp_distance(eng, seed=0):
    _seed_us_factions(eng, seed=seed)
    for a in eng.agents:
        cue = a.state.attrs.get("party_cue")
        if cue is None:
            continue
        d = float(np.linalg.norm(a.state.ideology - cue))
        scale = max(0.3, 1.0 - 1.5 * d)
        a.state.attrs["identity_strength"] = float(
            a.state.attrs.get("identity_strength", 0.5) * scale
        )


def variant_no_pp(eng, seed=0):
    _set_partypull_strength(eng, 0.0)


def variant_no_pp_no_media(eng, seed=0):
    _set_partypull_strength(eng, 0.0)
    _set_media_strength(eng, 0.0)


def variant_factions_no_pp(eng, seed=0):
    _seed_us_factions(eng, seed=seed)
    _set_partypull_strength(eng, 0.0)


def variant_factions_factional_cues_no_pp(eng, seed=0):
    _seed_us_factions(eng, seed=seed)
    _set_partypull_strength(eng, 0.0)


def variant_factions_factional_cues_weak_pp_weak_media(eng, seed=0):
    _seed_us_factions(eng, seed=seed)
    _set_partypull_strength(eng, 0.02)
    _set_media_strength(eng, 0.015)


# Phase 9 second wave
def variant_tight_factions(eng, seed=0):
    _seed_us_factions(eng, seed=seed, sd_within=0.05)


def variant_tight_factions_high_stub(eng, seed=0):
    _seed_us_factions(eng, seed=seed, sd_within=0.05)
    _bump_stubbornness(eng, factor=2.0, cap=0.85)


def variant_tight_factions_extremity_stub(eng, seed=0):
    _seed_us_factions(eng, seed=seed, sd_within=0.05)
    _bump_faction_stubbornness_by_extremity(eng, edge_boost=0.5)


def variant_factional_pp_smaller_eps(eng, seed=0):
    _seed_us_factions(eng, seed=seed, sd_within=0.06)
    _set_bc_epsilon(eng, 0.18)


def variant_factional_pp_no_idsort(eng, seed=0):
    _seed_us_factions(eng, seed=seed, sd_within=0.06)
    _set_identity_sorting_rate(eng, 0.0)


def variant_kitchen_sink_v1(eng, seed=0):
    _seed_us_factions(eng, seed=seed, sd_within=0.06)
    _bump_faction_stubbornness_by_extremity(eng, edge_boost=0.45)
    _set_bc_epsilon(eng, 0.18)
    _set_partypull_strength(eng, 0.04)


def variant_kitchen_sink_v2(eng, seed=0):
    _seed_us_factions(eng, seed=seed, sd_within=0.06)
    _bump_stubbornness(eng, factor=1.8, cap=0.85)
    _set_bc_epsilon(eng, 0.20)
    _set_partypull_strength(eng, 0.05)
    _set_media_strength(eng, 0.02)


def variant_kitchen_sink_v3(eng, seed=0):
    _seed_us_factions(eng, seed=seed, sd_within=0.05)
    _bump_faction_stubbornness_by_extremity(eng, edge_boost=0.5)


def variant_kitchen_sink_v4(eng, seed=0):
    _seed_us_factions(eng, seed=seed, sd_within=0.05)
    _bump_faction_stubbornness_by_extremity(eng, edge_boost=0.5)
    _set_bc_epsilon(eng, 0.18)
    _set_partypull_strength(eng, 0.035)
    _set_media_strength(eng, 0.02)


def variant_kitchen_sink_v5(eng, seed=0):
    _seed_us_factions(eng, seed=seed, sd_within=0.05)
    _bump_faction_stubbornness_by_extremity(eng, edge_boost=0.5)
    _set_bc_epsilon(eng, 0.18)


def variant_kitchen_sink_v6(eng, seed=0):
    _seed_us_factions(eng, seed=seed, sd_within=0.05)
    _bump_faction_stubbornness_by_extremity(eng, edge_boost=0.5)
    _set_partypull_strength(eng, 0.035)
    _set_media_strength(eng, 0.02)


def variant_kitchen_sink_v7(eng, seed=0):
    _seed_us_factions(eng, seed=seed, sd_within=0.05)
    _bump_faction_stubbornness_by_extremity(eng, edge_boost=0.5)
    _set_bc_epsilon(eng, 0.18)
    _set_identity_sorting_rate(eng, 0.0)


def variant_kitchen_sink_v8(eng, seed=0):
    _seed_us_factions(eng, seed=seed, sd_within=0.04)
    _bump_faction_stubbornness_by_extremity(eng, edge_boost=0.65, cap=0.92)
    _set_bc_epsilon(eng, 0.15)
    _set_partypull_strength(eng, 0.04)


# Ablation variants on kitchen_sink_v8
def variant_v8_no_stub(eng, seed=0):
    _seed_us_factions(eng, seed=seed, sd_within=0.04)
    _set_bc_epsilon(eng, 0.15)
    _set_partypull_strength(eng, 0.04)


def variant_v8_no_eps(eng, seed=0):
    _seed_us_factions(eng, seed=seed, sd_within=0.04)
    _bump_faction_stubbornness_by_extremity(eng, edge_boost=0.65, cap=0.92)
    _set_partypull_strength(eng, 0.04)


def variant_v8_no_ppwk(eng, seed=0):
    _seed_us_factions(eng, seed=seed, sd_within=0.04)
    _bump_faction_stubbornness_by_extremity(eng, edge_boost=0.65, cap=0.92)
    _set_bc_epsilon(eng, 0.15)


def variant_v8_only_stub(eng, seed=0):
    _seed_us_factions(eng, seed=seed, sd_within=0.04)
    _bump_faction_stubbornness_by_extremity(eng, edge_boost=0.65, cap=0.92)


def variant_v8_only_eps(eng, seed=0):
    _seed_us_factions(eng, seed=seed, sd_within=0.04)
    _set_bc_epsilon(eng, 0.15)


# Even more extreme variants - try faction-cue PartyPull
def variant_v9_faction_pp(eng, seed=0):
    """v8 but PartyPull pulls toward faction_cue not party_cue (party_cue
    same as faction_cue here)."""
    _seed_us_factions(eng, seed=seed, sd_within=0.04)
    _bump_faction_stubbornness_by_extremity(eng, edge_boost=0.65, cap=0.92)
    _set_bc_epsilon(eng, 0.15)
    _set_partypull_strength(eng, 0.06)  # increase since cue is faction-anchored


def variant_v9_no_media(eng, seed=0):
    """v8 + zero MediaConsumption to test the media's role."""
    _seed_us_factions(eng, seed=seed, sd_within=0.04)
    _bump_faction_stubbornness_by_extremity(eng, edge_boost=0.65, cap=0.92)
    _set_bc_epsilon(eng, 0.15)
    _set_partypull_strength(eng, 0.04)
    _set_media_strength(eng, 0.0)


def variant_v9_no_idsort(eng, seed=0):
    """v8 + zero IdentitySorting."""
    _seed_us_factions(eng, seed=seed, sd_within=0.04)
    _bump_faction_stubbornness_by_extremity(eng, edge_boost=0.65, cap=0.92)
    _set_bc_epsilon(eng, 0.15)
    _set_partypull_strength(eng, 0.04)
    _set_identity_sorting_rate(eng, 0.0)


VARIANTS = {
    "baseline": variant_baseline,
    "factions_only_central_pp": variant_factions_only_central_pp,
    "factions_factional_cues": variant_factions_factional_cues,
    "factions_weakened_pp": variant_factions_weakened_pp,
    "factions_weak_pp_weak_media": variant_factions_weak_pp_weak_media,
    "factions_weak_pp_zero_media_cue": variant_factions_weak_pp_zero_media_cue,
    "factions_distance_pp": variant_factions_distance_pp,
    "factions_factional_pp_distance": variant_factions_factional_pp_distance,
    "no_pp": variant_no_pp,
    "no_pp_no_media": variant_no_pp_no_media,
    "factions_no_pp": variant_factions_no_pp,
    "factions_factional_cues_no_pp": variant_factions_factional_cues_no_pp,
    "factions_factional_cues_weak_pp_weak_media": variant_factions_factional_cues_weak_pp_weak_media,
    "tight_factions": variant_tight_factions,
    "tight_factions_high_stub": variant_tight_factions_high_stub,
    "tight_factions_extremity_stub": variant_tight_factions_extremity_stub,
    "factional_pp_smaller_eps": variant_factional_pp_smaller_eps,
    "factional_pp_no_idsort": variant_factional_pp_no_idsort,
    "kitchen_sink_v1": variant_kitchen_sink_v1,
    "kitchen_sink_v2": variant_kitchen_sink_v2,
    "kitchen_sink_v3": variant_kitchen_sink_v3,
    "kitchen_sink_v4": variant_kitchen_sink_v4,
    "kitchen_sink_v5": variant_kitchen_sink_v5,
    "kitchen_sink_v6": variant_kitchen_sink_v6,
    "kitchen_sink_v7": variant_kitchen_sink_v7,
    "kitchen_sink_v8": variant_kitchen_sink_v8,
    "v8_no_stub": variant_v8_no_stub,
    "v8_no_eps": variant_v8_no_eps,
    "v8_no_ppwk": variant_v8_no_ppwk,
    "v8_only_stub": variant_v8_only_stub,
    "v8_only_eps": variant_v8_only_eps,
    "v9_faction_pp": variant_v9_faction_pp,
    "v9_no_media": variant_v9_no_media,
    "v9_no_idsort": variant_v9_no_idsort,
}


def _worker(seed):
    variant_name = os.environ.get("PHASE9_VARIANT", "baseline")
    fn = VARIANTS[variant_name]
    eng = ha.build_engine(seed=seed, n_agents=N, independent_fraction=IND)
    fn(eng, seed=seed)
    sched = ha.build_schedule()
    out = {1980: measure_diversity(eng)}
    for year, tick in [(1990, 30), (2000, 60), (2010, 90), (2020, 120), (2025, 135)]:
        run_to(eng, sched, tick)
        out[year] = measure_diversity(eng)
    return out


def aggregate(trajectories):
    years = [1980, 1990, 2000, 2010, 2020, 2025]
    means = {}
    for year in years:
        per_metric = {}
        for m in trajectories[0][year]:
            per_metric[m] = [t[year][m] for t in trajectories]
        means[year] = {m: float(np.mean(v)) for m, v in per_metric.items()}
    return means


def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    if variant not in VARIANTS:
        print(f"Unknown variant: {variant}")
        print(f"Available: {list(VARIANTS.keys())}")
        sys.exit(1)
    os.environ["PHASE9_VARIANT"] = variant
    print(f"variant={variant}  seeds={len(SEEDS)}  N={N}  ind={IND}")
    trajs = run_seeds_parallel(_worker, SEEDS)
    means = aggregate(trajs)
    print(f"\n=== {variant} ===")
    print(" year   PR  quadH  k*  sil*  bimX  bimY  wpsdX  wpsdY  gsdX  gsdY")
    for y in [1980, 1990, 2000, 2010, 2020, 2025]:
        m = means[y]
        print(f" {y}  {m['pr']:.2f}  {m['quad_h']:.2f}  {m['k_star']:.1f}  "
              f"{m['sil']:.2f}  {m['bim_x']:.2f}  {m['bim_y']:.2f}  "
              f"{m['wp_sd_x']:.3f}  {m['wp_sd_y']:.3f}  "
              f"{m['global_sd_x']:.2f}  {m['global_sd_y']:.2f}")
    out = Path(f"phase9_div_{variant}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"variant": variant, "means": {str(y): means[y] for y in means}},
                  f, indent=2)
    print(f"[dump] {out}")


if __name__ == "__main__":
    main()


# Even more aggressive — push stubbornness cap higher
def variant_v10_max_stub(eng, seed=0):
    _seed_us_factions(eng, seed=seed, sd_within=0.05)
    for a in eng.agents:
        if a.state.attrs.get("party") == 2:
            continue
        cue = a.state.attrs.get("faction_cue", a.state.attrs.get("party_cue"))
        if cue is None:
            continue
        d = float(np.linalg.norm(cue))
        # Map to stubbornness directly: edge -> 0.90, center -> 0.55
        s_new = 0.55 + 0.45 * min(1.0, d)
        a.state.attrs["stubbornness"] = float(s_new)


def variant_v10_max_stub_eps(eng, seed=0):
    variant_v10_max_stub(eng, seed=seed)
    _set_bc_epsilon(eng, 0.18)


def variant_v10_max_stub_eps_weak_pp(eng, seed=0):
    variant_v10_max_stub(eng, seed=seed)
    _set_bc_epsilon(eng, 0.18)
    _set_partypull_strength(eng, 0.035)
    _set_media_strength(eng, 0.025)


VARIANTS["v10_max_stub"] = variant_v10_max_stub
VARIANTS["v10_max_stub_eps"] = variant_v10_max_stub_eps
VARIANTS["v10_max_stub_eps_weak_pp"] = variant_v10_max_stub_eps_weak_pp
