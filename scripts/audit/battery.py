"""Stylized-fact battery + parameterized forward-sim runner.

Deliverable (A) of the calibration-readiness phase: a vector of summary
statistics for pattern-oriented modeling, going well beyond the two aggregate
means the knob audit used. Deliverable (B) imports this to build the
identifiability harness.

The engine is pure-numpy CPU (there is NO GPU forward sim in this repo); we run
on the 28-core CPU parallel harness. `run_seeds_parallel` workers must be
top-level and picklable (Windows spawn).

All stats are computed from ONE arc run: the final-tick agent cloud (2D
position, party, identities, affect, network) + the per-tick macro series
(for shock-response & econ↔cultural lag). Everything is descriptive — no real
target is fitted here; (B) measures how the stat VECTOR responds to parameters.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np

# ---------------------------------------------------------------------------
# Parameter space — the load-bearing knobs the identifiability study varies.
# Each entry: (name, shipped_baseline, kind). kind 'kw:<kwarg>' sets a
# build_engine kwarg; 'kw2:<a>,<b>' sets two; the perturbation is applied
# inside the worker before build_engine.
#
# MHV T0.1 retirements (published phase5/phase6 results predate this):
#   - K_mult ('patch_K' on PARTY_ASSIGNMENT_K_ANES): the constant is deleted
#     — it was dead code (exactly-zero Jacobian, the audit's own finding).
#   - sigma_pc (tier_d_anes_sigma_pc_multiplier): kwarg is now a deprecated
#     no-op; the 1.6 is folded into PARTY_CUE_SIGMA_HISTORICAL_ANES.
# Re-running this battery produces an 8-parameter space; T0.5 reworks the
# stat registry anyway (continuous/discrete tags).
# ---------------------------------------------------------------------------
PARAMS = [
    ("drift_mult",   3.0,   "kw:tier_d_anes_drift_multiplier"),
    ("party_pull",   0.04,  "kw:tier_c_party_pull_strength"),
    ("bc_strength",  0.015, "kw:tier_c_bc_strength"),
    ("idpull_x",     0.020, "kw:tier_c_identity_pull_x"),
    ("idpull_y",     0.040, "kw:tier_c_identity_pull_y"),
    ("noise_sigma",  0.04,  "kw2:tier_d_aniso_noise_sigma_x,tier_d_aniso_noise_sigma_y"),
    ("identity_mult",1.0,   "kw:sandbox_identity_mult"),
    ("animus_mult",  1.0,   "kw:sandbox_animus_mult"),
]
PARAM_NAMES = [p[0] for p in PARAMS]
PARAM_BASE = np.array([p[1] for p in PARAMS], dtype=float)

# MHV T0.5 — known-dead control parameter. kind "noop" is ignored by
# _apply_params, so this knob provably does nothing: its ABC posterior
# shrinkage IS the spurious-contraction floor of the inference pipeline
# (review_math.md §9 P1.4), and all real shrinkages are reported net of
# it. Kept OUT of PARAMS so pairwise/phase3 consumers don't sweep it;
# phase5 appends it explicitly. _apply_params zips against PARAMS_ALL
# (zip truncates), so 8-vector and 9-vector thetas both work.
CONTROL_PARAMS = [("dummy_dead", 1.0, "noop")]
PARAMS_ALL = PARAMS + CONTROL_PARAMS

END_TICK = 135
DECADE_TICKS = {1990: 42, 2000: 72, 2010: 102, 2020: 126, 2025: 135}


# ---------------------------------------------------------------------------
# Forward sim with rich capture
# ---------------------------------------------------------------------------

def _apply_params(theta):
    """theta: array aligned with PARAMS (8) or PARAMS_ALL (9, incl. the
    dummy control). Returns the overrides dict. kind "noop" is skipped
    by construction (the T0.5 dead-control)."""
    from scripts.anes_preset import ANES_FULL_KWARGS
    ov = dict(ANES_FULL_KWARGS)
    for (name, _base, kind), val in zip(PARAMS_ALL, theta):
        if kind == "noop":
            continue
        if kind.startswith("kw2:"):
            a, b = kind[4:].split(",")
            ov[a] = float(val); ov[b] = float(val)
        elif kind.startswith("kw:"):
            ov[kind[3:]] = float(val)
    return ov


def run_arc_rich(theta, seed):
    """Run the shipped arc with parameter vector theta; return
    (series ndarray [T+1, n_macro], final_state dict)."""
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from abm.metrics.affective import affective_polarization, ideological_constraint, sorting_index
    from abm.metrics.polarization import variance, variance_per_axis
    from abm.metrics.network import party_modularity, cross_cutting_tie_fraction

    ov = _apply_params(theta)

    eng = build_engine(seed=seed, **ov)
    sched = build_schedule(faction_anchor_events=True,
                           evidence_regrade=True, exogenous_shocks=True)

    def macro_row():
        pos = eng.positions()
        va = variance_per_axis(pos)
        parties = np.array([a.state.attrs["party"] for a in eng.agents])
        sep = 0.0
        if (parties == 0).any() and (parties == 1).any():
            sep = float(np.linalg.norm(pos[parties == 0].mean(0) - pos[parties == 1].mean(0)))
        ic = ideological_constraint(eng.agents)
        # Elite (party-centroid) positions — the EliteDrift targets, the
        # DW-NOMINATE analogue. Independent of party_pull/idpull (which
        # move the MASS, not the centroids). Captured so the battery can
        # tell mass-tracks-elite (party_pull) from mass-overshoots-elite
        # (idpull) and break the separation ridge.
        ep = eng.env.attrs.get("parties", {})
        e0 = ep.get(0, np.zeros(2)); e1 = ep.get(1, np.zeros(2))
        return [va["x"], va["y"], sep,
                affective_polarization(eng.agents),
                ic["x"], ic["y"],
                float(e0[0]), float(e0[1]), float(e1[0]), float(e1[1])]

    series = [macro_row()]
    for t in range(1, END_TICK + 1):
        run_to(eng, sched, t)
        series.append(macro_row())

    final = _capture_final(eng)
    return np.array(series, dtype=float), final


def _capture_final(eng):
    pos = eng.positions()
    party = np.array([a.state.attrs.get("party", 2) for a in eng.agents], dtype=int)
    ids = np.array([a.state.attrs.get("identities", np.zeros(3)) for a in eng.agents], dtype=float)
    affect = []
    for a in eng.agents:
        af = a.state.attrs.get("affect") or {}
        affect.append(float(np.mean([np.clip(v, -1, 1) for v in af.values()])) if af else np.nan)
    # network edges
    net = eng.env.attrs["network"]
    edges = [(int(i), int(j)) for i, j in net.edges()]
    deg = {i: net.degree(i) for i in net.node_ids}
    # T0.5 APC stat input — per-agent entry tick reconstructed from the
    # arc's replacement log ([tick, agent_id], chronological; the last
    # replacement of a slot is that agent's entry). 0 = 1980 incumbent.
    entry = {}
    for t, aid in (eng.env.attrs.get("replacement_events") or []):
        entry[int(aid)] = int(t)
    entry_tick = np.array([entry.get(int(a.id), 0) for a in eng.agents], dtype=int)
    return {"pos": pos, "party": party, "ids": ids,
            "affect": np.array(affect, dtype=float),
            "entry_tick": entry_tick,
            "edges": edges, "deg": deg, "node_ids": list(net.node_ids)}


# ---------------------------------------------------------------------------
# Numeric helpers (numpy-only substitutes for sklearn/diptest)
# ---------------------------------------------------------------------------

def _moments(x):
    x = np.asarray(x, float)
    m = x.mean(); s = x.std()
    if s < 1e-9:
        return m, s, 0.0, 0.0
    z = (x - m) / s
    return m, s, float((z**3).mean()), float((z**4).mean() - 3.0)


def _participation_ratio(M):
    """Effective dimensionality of a multivariate cloud: PR of the
    correlation-matrix eigenvalues, (sum lam)^2 / sum lam^2 in [1, d].
    Columns are z-scored first (zero-SD columns dropped) so the stat is
    scale-free — the S1 pilot's dimensionality observable, kept stable
    into the S2 multi-issue substrate."""
    M = np.asarray(M, float)
    sd = M.std(0)
    keep = sd > 1e-9
    if keep.sum() < 2:
        return float(keep.sum())
    Z = (M[:, keep] - M[:, keep].mean(0)) / sd[keep]
    ev = np.clip(np.linalg.eigvalsh(np.cov(Z, rowvar=False)), 0.0, None)
    s = ev.sum()
    return float(s * s / ((ev ** 2).sum() + 1e-300)) if s > 0 else 0.0


def _bimodality_coef(x):
    """Sarle's bimodality coefficient; >5/9≈0.555 suggests bimodal."""
    x = np.asarray(x, float); n = len(x)
    if n < 4:
        return 0.0
    s = x.std(ddof=1)
    if s < 1e-9:
        return 0.0
    z = (x - x.mean()) / s
    g = (z**3).mean(); k = (z**4).mean() - 3.0
    denom = k + 3.0 * (n - 1) ** 2 / ((n - 2) * (n - 3))
    return float((g * g + 1.0) / denom) if denom > 0 else 0.0


def _gmm1d(x, k, iters=80):
    """Tiny 1-D Gaussian-mixture EM. Returns (mus, sigmas, weights, loglik)."""
    x = np.asarray(x, float)
    n = len(x)
    qs = np.linspace(0, 100, k + 2)[1:-1]
    mus = np.percentile(x, qs).astype(float)
    sigmas = np.full(k, max(x.std(), 1e-2))
    w = np.full(k, 1.0 / k)
    ll_old = -np.inf
    for _ in range(iters):
        # E
        comp = np.array([w[j] * _norm_pdf(x, mus[j], sigmas[j]) for j in range(k)])  # k x n
        tot = comp.sum(0) + 1e-300
        resp = comp / tot
        ll = float(np.log(tot).sum())
        # M
        Nk = resp.sum(1) + 1e-9
        w = Nk / n
        mus = (resp * x).sum(1) / Nk
        sigmas = np.sqrt((resp * (x - mus[:, None]) ** 2).sum(1) / Nk)
        sigmas = np.maximum(sigmas, 1e-2)
        if abs(ll - ll_old) < 1e-6:
            break
        ll_old = ll
    return mus, sigmas, w, ll


def _norm_pdf(x, mu, sig):
    return np.exp(-0.5 * ((x - mu) / sig) ** 2) / (sig * np.sqrt(2 * np.pi))


def _gmm_bic_nmodes(x, kmax=3):
    """Number of mixture components minimizing BIC (1..kmax) + the 2-comp
    separation |mu1-mu2|/pooled_sigma and min mixing weight."""
    x = np.asarray(x, float); n = len(x)
    best_k, best_bic = 1, np.inf
    sep2, wbal2 = 0.0, 0.0
    for k in range(1, kmax + 1):
        try:
            mus, sigmas, w, ll = _gmm1d(x, k)
        except Exception:
            continue
        n_par = 3 * k - 1  # means + sigmas + (k-1) weights
        bic = -2 * ll + n_par * np.log(n)
        if k == 2:
            pooled = np.sqrt((w * sigmas ** 2).sum())
            sep2 = float(abs(mus[0] - mus[1]) / (pooled + 1e-9))
            wbal2 = float(min(w) / 0.5)
        if bic < best_bic - 1e-6:
            best_bic, best_k = bic, k
    return best_k, sep2, wbal2


def _silhouette(X, labels):
    """Mean silhouette over points with >=2 clusters present. O(n^2)."""
    X = np.asarray(X, float); labels = np.asarray(labels)
    uniq = [u for u in np.unique(labels) if u in (0, 1)]
    mask = np.isin(labels, uniq)
    X = X[mask]; labels = labels[mask]
    if len(np.unique(labels)) < 2 or len(X) < 4:
        return 0.0
    D = np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(-1))
    sil = []
    for i in range(len(X)):
        same = labels == labels[i]; same[i] = False
        a = D[i, same].mean() if same.any() else 0.0
        bs = [D[i, labels == c].mean() for c in np.unique(labels) if c != labels[i]]
        b = min(bs) if bs else 0.0
        denom = max(a, b)
        sil.append((b - a) / denom if denom > 0 else 0.0)
    return float(np.mean(sil))


def _kmeans2(X, iters=40, seed=0):
    X = np.asarray(X, float)
    rng = np.random.default_rng(seed)
    c = X[rng.choice(len(X), 2, replace=False)]
    lab = np.zeros(len(X), int)
    for _ in range(iters):
        d = np.sqrt(((X[:, None, :] - c[None]) ** 2).sum(-1))
        new = d.argmin(1)
        if (new == lab).all():
            break
        lab = new
        for j in range(2):
            if (lab == j).any():
                c[j] = X[lab == j].mean(0)
    return lab


def _assortativity_party(edges, party, node_ids):
    """Newman discrete assortativity coefficient on party labels over edges."""
    pmap = {nid: int(party[k]) for k, nid in enumerate(node_ids)}
    cats = sorted({v for v in pmap.values()})
    idx = {c: i for i, c in enumerate(cats)}
    nc = len(cats)
    if nc < 2 or not edges:
        return 0.0
    e = np.zeros((nc, nc))
    for i, j in edges:
        a, b = idx[pmap[i]], idx[pmap[j]]
        e[a, b] += 1; e[b, a] += 1
    e /= e.sum()
    a = e.sum(1); b = e.sum(0)
    tr = np.trace(e); s = (a * b).sum()
    return float((tr - s) / (1 - s)) if (1 - s) > 1e-9 else 0.0


def _xcorr_lag(a, b, maxlag=24):
    """Peak cross-correlation between two detrended series and its lag.
    Positive lag = a leads b."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    a = a - a.mean(); b = b - b.mean()
    sa, sb = a.std(), b.std()
    if sa < 1e-9 or sb < 1e-9:
        return 0.0, 0
    a /= sa; b /= sb; n = len(a)
    best_r, best_l = -2.0, 0
    for lag in range(-maxlag, maxlag + 1):
        if lag >= 0:
            r = (a[:n - lag] * b[lag:]).mean() if n - lag > 1 else 0.0
        else:
            r = (a[-lag:] * b[:n + lag]).mean() if n + lag > 1 else 0.0
        if r > best_r:
            best_r, best_l = r, lag
    return float(best_r), int(best_l)


# ---------------------------------------------------------------------------
# The battery
# ---------------------------------------------------------------------------
# series columns: 0 var_x, 1 var_y, 2 sep, 3 affect, 4 constraint_x, 5 constraint_y

# T0.5 inference-hygiene registry (review_math.md §9 P0.1): every stat is
# tagged continuous | discrete. Gradient/Fisher paths consume CONTINUOUS
# ONLY — a quantized stat differenced across a ±15% step is either exactly
# 0 or a huge spike, and (floored-SD-standardized) one such stat carried
# ~99% of a Jacobian column in the published phase5/phase6 run. Discrete
# stats remain in ABC/NPE as soft summaries with real prior-variance.
# compute_battery raises on any stat missing here — tag what you add.
_DISCRETE = {
    "nmodes_x", "nmodes_y",            # integer BIC mode counts (the artifact)
    "gmm2_sep_x", "gmm2_sep_y",        # EM mode-switching: jumps with the
    "gmm2_wbal_x", "gmm2_wbal_y",      #   2-comp solution's basin
    "silhouette_kmeans2",              # k-means label flips
    "largest_cluster_frac",            # k-means label flips
    "xcorr_xy_lag",                    # integer lag
}
_CONTINUOUS = {
    "mean_x", "mean_y", "sd_x", "sd_y", "skew_x", "skew_y", "kurt_x", "kurt_y",
    "corr_xy", "var_total", "party_sep",
    "cent0_x", "cent0_y", "cent1_x", "cent1_y",
    "wp_sd_x", "wp_sd_y", "wp_cov_xy",
    "constraint_x", "constraint_y",
    "bg_partisan_align", "constraint_index", "constraint_index_wp",
    "pr_pos", "pr_attitude",
    "bimod_x", "bimod_y",
    "silhouette_party",                # party labels are fixed, not fitted
    "modularity", "xc_fraction", "assortativity_party",
    "affect_mean", "affect_p0", "affect_p1", "sorting_index",
    "aff_cohort_gap", "aff_entry_slope",
    "sep_slope", "aff_slope",
    "sep_jump_2016", "aff_jump_2016", "aff_jump_2020", "aff_recovery_2021",
    "xcorr_xy_peak", "aff_convexity",
    "elite_sep", "elite_sep_slope",
    "elite_sep_1990", "elite_sep_2000", "elite_sep_2010",
    "elite_sep_2020", "elite_sep_2025",
    "mass_elite_gap_x", "mass_elite_gap_y", "mass_extremity_ratio",
    "dwnom_shape_resid",
}
STAT_TAGS = {**{k: "discrete" for k in _DISCRETE},
             **{k: "continuous" for k in _CONTINUOUS}}


def compute_battery(series, final):
    pos = final["pos"]; party = final["party"]; ids = final["ids"]
    aff = final["affect"]
    x, y = pos[:, 0], pos[:, 1]
    p0 = party == 0; p1 = party == 1
    out = {}

    # --- 2D joint distribution moments ---
    mx, sx, skx, kx = _moments(x); my, sy, sky, ky = _moments(y)
    out["mean_x"], out["mean_y"] = mx, my
    out["sd_x"], out["sd_y"] = sx, sy
    out["skew_x"], out["skew_y"] = skx, sky
    out["kurt_x"], out["kurt_y"] = kx, ky
    out["corr_xy"] = float(np.corrcoef(x, y)[0, 1]) if sx > 1e-9 and sy > 1e-9 else 0.0

    # --- dispersion / party-conditional ---
    out["var_total"] = float(np.var(pos, axis=0).sum())
    sep = float(np.linalg.norm(x[p0].mean() - x[p1].mean()
                + 1j * (y[p0].mean() - y[p1].mean()))) if p0.any() and p1.any() else 0.0
    out["party_sep"] = sep
    out["cent0_x"] = float(x[p0].mean()) if p0.any() else 0.0
    out["cent0_y"] = float(y[p0].mean()) if p0.any() else 0.0
    out["cent1_x"] = float(x[p1].mean()) if p1.any() else 0.0
    out["cent1_y"] = float(y[p1].mean()) if p1.any() else 0.0
    wpx, wpy, wpcov = [], [], []
    for m in (p0, p1):
        if m.sum() > 1:
            wpx.append(x[m].std()); wpy.append(y[m].std())
            wpcov.append(np.cov(x[m], y[m])[0, 1])
    out["wp_sd_x"] = float(np.mean(wpx)) if wpx else 0.0
    out["wp_sd_y"] = float(np.mean(wpy)) if wpy else 0.0
    out["wp_cov_xy"] = float(np.mean(wpcov)) if wpcov else 0.0

    # --- constraint (party-issue corr) ---
    pm = p0 | p1
    pf = party[pm].astype(float)
    out["constraint_x"] = float(abs(np.corrcoef(pf, x[pm])[0, 1])) if pm.sum() > 1 and x[pm].std() > 1e-9 else 0.0
    out["constraint_y"] = float(abs(np.corrcoef(pf, y[pm])[0, 1])) if pm.sum() > 1 and y[pm].std() > 1e-9 else 0.0

    # --- T0.5: B&G dual indices + constraint index + dimensionality ---
    # Baldassarri & Gelman 2008 distinction: PARTISAN alignment (issues
    # correlate with party) vs ISSUE alignment / constraint (issues
    # correlate with each other). In 2D the issue-pair set is just
    # {x,y}, so constraint_index = |corr_xy| pooled — trivial today, but
    # this is the instrument that carries unchanged into the S2
    # multi-issue substrate, where the two indices genuinely diverge.
    out["bg_partisan_align"] = float(
        (out["constraint_x"] + out["constraint_y"]) / 2.0)
    out["constraint_index"] = abs(out["corr_xy"])
    wp_ci = []
    for m in (p0, p1):
        if m.sum() > 2 and x[m].std() > 1e-9 and y[m].std() > 1e-9:
            wp_ci.append(abs(np.corrcoef(x[m], y[m])[0, 1]))
    out["constraint_index_wp"] = float(np.mean(wp_ci)) if wp_ci else 0.0
    # participation ratio: effective dimensionality of the position
    # cloud (in [1,2]) and of the full attitude space [x, y, identities]
    out["pr_pos"] = _participation_ratio(pos)
    out["pr_attitude"] = _participation_ratio(np.column_stack([pos, ids]))

    # --- bimodality ---
    out["bimod_x"] = _bimodality_coef(x)
    out["bimod_y"] = _bimodality_coef(y)
    nmx, sep2x, wbalx = _gmm_bic_nmodes(x)
    nmy, sep2y, wbaly = _gmm_bic_nmodes(y)
    out["nmodes_x"] = float(nmx); out["nmodes_y"] = float(nmy)
    out["gmm2_sep_x"] = sep2x; out["gmm2_sep_y"] = sep2y
    out["gmm2_wbal_x"] = wbalx; out["gmm2_wbal_y"] = wbaly

    # --- cluster structure ---
    out["silhouette_party"] = _silhouette(pos, party)
    km = _kmeans2(pos)
    out["silhouette_kmeans2"] = _silhouette(pos, km)
    out["largest_cluster_frac"] = float(max((km == 0).mean(), (km == 1).mean()))

    # --- network ---
    out["modularity"] = _modularity(final)
    out["xc_fraction"] = _xc_fraction(final)
    out["assortativity_party"] = _assortativity_party(final["edges"], party, final["node_ids"])

    # --- affect / subgroup ---
    out["affect_mean"] = float(np.nanmean(aff)) if np.isfinite(aff).any() else 0.0
    out["affect_p0"] = float(np.nanmean(aff[p0])) if p0.any() and np.isfinite(aff[p0]).any() else 0.0
    out["affect_p1"] = float(np.nanmean(aff[p1])) if p1.any() and np.isfinite(aff[p1]).any() else 0.0
    out["sorting_index"] = _sorting_index(party, ids)

    # --- T0.5: APC/cohort affect decomposition (Phillips 2022 axis) ---
    # entry_tick 0 = 1980 incumbent (never replaced); >0 = the tick the
    # current occupant of the slot entered. aff_cohort_gap = recent
    # entrants (2014+, tick>=102) minus incumbents: the COHORT component
    # of affective cooling, separating "new cohorts arrive colder"
    # (replacement-driven) from "everyone cools" (period-driven).
    et = final.get("entry_tick")
    out["aff_cohort_gap"] = 0.0
    out["aff_entry_slope"] = 0.0
    if et is not None and len(et) == len(aff):
        fin = np.isfinite(aff)
        inc = (et == 0) & fin
        rec = (et >= 102) & fin
        if inc.any() and rec.any():
            out["aff_cohort_gap"] = float(aff[rec].mean() - aff[inc].mean())
        if fin.sum() > 2 and et[fin].std() > 1e-9:
            # slope of final affect on entry time, per 30 ticks (~decade)
            out["aff_entry_slope"] = float(
                np.polyfit(et[fin] / 30.0, aff[fin], 1)[0])

    # --- dynamics & shock response (from series) ---
    T = series.shape[0]
    sep_s, aff_s = series[:, 2], series[:, 3]
    vx_s, vy_s = series[:, 0], series[:, 1]
    ticks = np.arange(T)
    out["sep_slope"] = float(np.polyfit(ticks, sep_s, 1)[0])
    out["aff_slope"] = float(np.polyfit(ticks, aff_s, 1)[0])
    # 2016 (tick 108) status-threat / Trump window: change over [105,114]
    out["sep_jump_2016"] = float(sep_s[min(114, T-1)] - sep_s[min(105, T-1)])
    out["aff_jump_2016"] = float(aff_s[min(114, T-1)] - aff_s[min(105, T-1)])
    # 2020 (tick 120) COVID/Jan6 affect spike + 2021 revert
    out["aff_jump_2020"] = float(aff_s[min(123, T-1)] - aff_s[min(117, T-1)])
    out["aff_recovery_2021"] = float(aff_s[min(129, T-1)] - aff_s[min(123, T-1)])
    # econ <-> cultural dispersion lead/lag
    r, lag = _xcorr_lag(vx_s, vy_s)
    out["xcorr_xy_peak"] = r
    out["xcorr_xy_lag"] = float(lag)
    # late-period convexity of affect (accel): 2nd half slope - 1st half slope
    half = T // 2
    s1 = np.polyfit(ticks[:half], aff_s[:half], 1)[0]
    s2 = np.polyfit(ticks[half:], aff_s[half:], 1)[0]
    out["aff_convexity"] = float(s2 - s1)

    # --- elite (party-centroid) facts: DW-NOMINATE analogue (Part 1) ---
    # series cols 6..9 = e0x,e0y,e1x,e1y (env party centroids = elite ideal
    # points). These are moved ONLY by EliteDrift (drift_mult), never by
    # party_pull / idpull (which move the mass). Adding them lets the battery
    # separate the two mass-side channels: party_pull pulls mass TOWARD the
    # elite centroid (mass_elite_gap shrinks; mass tracks elite), idpull pulls
    # mass toward the identity sign which can OVERSHOOT the elite centroid
    # (extremity ratio > 1). DW-NOMINATE (House party-median distance, dim 1;
    # McCarty/Poole/Rosenthal, Voteview) is the real target this matches.
    if series.shape[1] >= 10:
        e0 = series[:, 6:8]; e1 = series[:, 8:10]
        elite_sep_s = np.sqrt(((e0 - e1) ** 2).sum(1))
        out["elite_sep"] = float(elite_sep_s[-1])
        out["elite_sep_slope"] = float(np.polyfit(ticks, elite_sep_s, 1)[0])
        # decade-snapshot elite separation (DW-NOMINATE trajectory shape)
        for yr, t in DECADE_TICKS.items():
            out[f"elite_sep_{yr}"] = float(elite_sep_s[min(t, T - 1)])
        # mass vs elite at final tick: how far the mass party-means sit from
        # the elite centroids (per axis, mean over parties).
        m0 = np.array([out["cent0_x"], out["cent0_y"]])
        m1 = np.array([out["cent1_x"], out["cent1_y"]])
        ge0 = np.abs(m0 - e0[-1]); ge1 = np.abs(m1 - e1[-1])
        out["mass_elite_gap_x"] = float((ge0[0] + ge1[0]) / 2)
        out["mass_elite_gap_y"] = float((ge0[1] + ge1[1]) / 2)
        # extremity ratio: mass separation / elite separation. >1 = mass more
        # polarized than its elites (idpull overshoot); ≈1 = mass tracks elites
        # (party_pull); <1 = mass lags elites.
        out["mass_extremity_ratio"] = float(
            out["party_sep"] / elite_sep_s[-1]) if elite_sep_s[-1] > 1e-6 else 0.0
        # DW-NOMINATE shape residual (scale-free: normalize both to 1980).
        d0 = elite_sep_s[min(DECADE_TICKS[1990], T - 1)]
        if d0 > 1e-6:
            resid = 0.0
            for yr in (1990, 2000, 2010, 2020, 2025):
                sim_growth = elite_sep_s[min(DECADE_TICKS[yr], T - 1)] / d0
                resid += (sim_growth - DWNOM_GROWTH[yr]) ** 2
            out["dwnom_shape_resid"] = float(resid)
        else:
            out["dwnom_shape_resid"] = 0.0

    untagged = [k for k in out if k not in STAT_TAGS]
    if untagged:
        raise KeyError(
            f"stats missing a continuous|discrete tag in STAT_TAGS: {untagged}")
    return out


# DW-NOMINATE House party-median distance (dim 1), normalized to the 1990
# value (Voteview / McCarty-Poole-Rosenthal). Used scale-free: the *shape*
# (growth) of elite divergence, matched against the sim's elite_sep growth.
# Raw approx: 1990 0.63, 2000 0.73, 2010 0.86, 2020 0.93, 2025 ~0.95.
DWNOM_GROWTH = {1990: 1.00, 2000: 1.16, 2010: 1.37, 2020: 1.48, 2025: 1.51}


def _modularity(final):
    from collections import defaultdict
    party = final["party"]; node_ids = final["node_ids"]; deg = final["deg"]
    pmap = {nid: int(party[k]) for k, nid in enumerate(node_ids)}
    m = sum(deg.values()) / 2.0
    if m == 0:
        return 0.0
    D = defaultdict(float); L = defaultdict(float)
    for nid in node_ids:
        D[pmap[nid]] += deg[nid]
    for i, j in final["edges"]:
        if pmap[i] == pmap[j]:
            L[pmap[i]] += 1
    return float(sum(L[c] / m - (D[c] / (2 * m)) ** 2 for c in D))


def _xc_fraction(final):
    party = final["party"]; node_ids = final["node_ids"]
    pmap = {nid: int(party[k]) for k, nid in enumerate(node_ids)}
    edges = final["edges"]
    if not edges:
        return 0.0
    cross = sum(1 for i, j in edges if pmap[i] != pmap[j])
    return float(cross / len(edges))


def _sorting_index(party, ids):
    mask = (party == 0) | (party == 1)
    if mask.sum() < 2 or ids.shape[1] == 0:
        return 0.0
    p = party[mask].astype(float)
    if p.std() < 1e-9:
        return 0.0
    cs = []
    for d in range(ids.shape[1]):
        col = ids[mask, d]
        cs.append(abs(np.corrcoef(p, col)[0, 1]) if col.std() > 1e-9 else 0.0)
    return float(np.mean(cs))


# Canonical ordered stat names (built once from a baseline run by callers).
def stat_names_from(d):
    return list(d.keys())


# ---------------------------------------------------------------------------
# Workers
# ---------------------------------------------------------------------------

def battery_worker(arg):
    """arg = (theta_tuple, seed). Returns (theta_tuple, seed, {stat: val})."""
    theta, seed = arg
    series, final = run_arc_rich(np.array(theta, float), seed)
    return (theta, seed, compute_battery(series, final))
