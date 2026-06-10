"""MHV S2 — D-dimensional issue state: loadings, seeding, projection, distance.

The S2 substrate (mhv_spec M1; s2_spec.md §1-§3): each agent carries an
issue vector ``v ∈ [-1,1]^D`` seeded from the frozen ANES loadings file
(``data/mhv/issue_loadings.json``, built once by
``scripts/build_issue_loadings.py``); the 2D compass is a fixed linear
readout (block means — the same lens the empirical pipeline uses); all
D-dim rule kernels measure distance with the RMS convention so that D=2
reduces EXACTLY to the existing 2D arithmetic (invariant I1).

Port-ready style (agreed S2 prep for a post-MHV tensor port): every
function here is a pure vectorized numpy kernel — arrays in, arrays out,
no agent objects, no engine imports.
"""
from __future__ import annotations

import json
import os

import numpy as np

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOADINGS_PATH = os.path.join(_ROOT, "data", "mhv", "issue_loadings.json")

_PARTY_TAG = {0: "dem", 1: "rep", 2: "ind"}


def load_loadings(path: str | None = None) -> dict:
    """Read the frozen loadings file. Engine code calls this once per build."""
    with open(path or LOADINGS_PATH, encoding="utf-8") as f:
        return json.load(f)


def chol_corr(loadings: dict) -> np.ndarray:
    """Cholesky factor of the frozen (PSD-corrected) 1986 correlation matrix."""
    C = np.asarray(loadings["corr_1986_psd"], dtype=float)
    return np.linalg.cholesky(C + 1e-12 * np.eye(C.shape[0]))


def seed_issue_vectors(parties: np.ndarray, loadings: dict,
                       rng: np.random.Generator,
                       chol: np.ndarray | None = None) -> np.ndarray:
    """Draw per-agent issue vectors from the party-conditional 1986 structure.

    v_i = mu_party(i) + sd_party(i) * (L z_i),  z ~ N(0, I), clipped [-1, 1].

    The measured marginals carry the wrong-side tails NATIVELY — this is
    what retires the T0.4 soft tail cap (s2_spec.md §1): nobody clips or
    thins the projection; the tail rate is whatever the seeded item
    distributions produce, pinned by test against the measured ANES rates.
    """
    parties = np.asarray(parties, dtype=int)
    L = chol if chol is not None else chol_corr(loadings)
    D = L.shape[0]
    n = len(parties)
    mu = np.zeros((n, D))
    sd = np.zeros((n, D))
    for p, tag in _PARTY_TAG.items():
        m = parties == p
        if not m.any():
            continue
        stats = loadings["party_conditional"][tag]
        mu[m] = np.asarray(stats["item_means"], dtype=float)
        sd[m] = np.asarray(stats["item_sds"], dtype=float)
    z = rng.standard_normal((n, D))
    v = mu + sd * (z @ L.T)
    return np.clip(v, -1.0, 1.0)


def project_compass(V: np.ndarray, loadings: dict) -> np.ndarray:
    """Fixed linear readout: x = econ-block mean, y = cultural-core mean.

    At D=2 with the identity block map (x_idx=[0], y_idx=[1]) this is the
    identity — the I1 reduction. Single-column means are exact copies in
    IEEE, so the reduction is bit-exact, not approximate.
    """
    V = np.asarray(V, dtype=float)
    ro = loadings["compass_readout"]
    x = V[:, ro["x_idx"]].mean(axis=1)
    y = V[:, ro["y_idx"]].mean(axis=1)
    return np.column_stack([x, y])


def rms_distance(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """RMS-scaled Euclidean distance: ||a-b|| * sqrt(2/D).

    The S2 distance convention (s2_spec.md §2): at D=2 the factor is
    sqrt(2/2) = 1.0 EXACTLY in IEEE-754, so every distance, epsilon
    threshold, and logistic weight reproduces the current 2D arithmetic
    bit-for-bit. At D=7 a maximally-disagreeing pair still spans the same
    numeric range as the 2D compass diagonal, so epsilon values keep
    their meaning.

    a, b: (..., D) arrays (broadcastable). Returns (...,) distances.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    diff = a - b
    D = diff.shape[-1]
    return np.sqrt((diff * diff).sum(axis=-1)) * np.sqrt(2.0 / D)


# ---------------------------------------------------------------------------
# T2.2 live-mode runtime — precomputed index maps the engine and rules use
# every tick. Stored once in env.attrs["issue_runtime"] by build_engine.
# ---------------------------------------------------------------------------

def build_runtime(loadings: dict) -> dict:
    """Precompute the projection/lift index maps for live issues mode.

    lift_map[i] = which compass axis (0=x, 1=y) item i belongs to, so
    lifting a 2D vector is the O(D) gather `xy[lift_map]`. Lifting adds
    the axis value to EVERY item of the block, which makes lift the exact
    right-inverse of the block-means projection: project(lift(xy)) == xy,
    and a lifted delta moves the projection by exactly that delta. At
    D=2 both maps are the identity."""
    ro = loadings["compass_readout"]
    x_idx = np.asarray(ro["x_idx"], dtype=int)
    y_idx = np.asarray(ro["y_idx"], dtype=int)
    D = len(loadings["items"])
    lift_map = np.zeros(D, dtype=int)
    lift_map[y_idx] = 1
    sd_pooled = np.asarray(
        loadings.get("pooled", {}).get("item_sds", np.ones(D)), dtype=float)
    return {"D": D, "x_idx": x_idx, "y_idx": y_idx, "lift_map": lift_map,
            "chol": chol_corr(loadings), "sd_pooled": sd_pooled}


def lift(xy: np.ndarray, rt: dict) -> np.ndarray:
    """2D compass vector -> D-dim issue vector (block-broadcast)."""
    return np.asarray(xy, dtype=float)[rt["lift_map"]]


def project1(v: np.ndarray, rt: dict) -> np.ndarray:
    """Single agent's issue vector -> 2D compass point (block means)."""
    return np.array([v[rt["x_idx"]].mean(), v[rt["y_idx"]].mean()])


def issues_of(agent, env) -> np.ndarray | None:
    """The rule-side gate: the agent's issue vector when live mode is on
    (env carries the runtime) and the agent carries the state, else None
    (legacy 2D path)."""
    if "issue_runtime" not in env.attrs:
        return None
    return agent.state.attrs.get("issues")


def replacement_draw(pos2d: np.ndarray, rt: dict,
                     rng: np.random.Generator) -> np.ndarray:
    """Issue vector for a cohort-replacement arrival anchored at a drawn
    2D position: realistic item-level residuals from the frozen
    correlation structure, recentered so the projection equals pos2d
    EXACTLY (the 2D anchored-draw semantics are preserved; the items add
    within-block texture). At D=2 the residual term cancels identically
    and this returns pos2d."""
    z = rng.standard_normal(rt["D"])
    raw = rt["sd_pooled"] * (rt["chol"] @ z)
    centered = raw - lift(project1(raw, rt), rt)
    return np.clip(centered + lift(pos2d, rt), -1.0, 1.0)


def identity_loadings_2d() -> dict:
    """Minimal D=2 loadings dict for the I1 reduction path and its tests:
    issue 0 IS the economic axis, issue 1 IS the cultural axis."""
    return {
        "version": 1,
        "items": [{"var": "x", "block": "econ"},
                  {"var": "y", "block": "cultural_moral"}],
        "blocks": {"econ": [0], "cultural_moral": [1], "racial": []},
        "compass_readout": {"x_idx": [0], "y_idx": [1]},
        "corr_1986_psd": [[1.0, 0.0], [0.0, 1.0]],
        "party_conditional": {
            "dem": {"item_means": [0.0, 0.0], "item_sds": [1.0, 1.0]},
            "rep": {"item_means": [0.0, 0.0], "item_sds": [1.0, 1.0]},
            "ind": {"item_means": [0.0, 0.0], "item_sds": [1.0, 1.0]},
        },
    }
