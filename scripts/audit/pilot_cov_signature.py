"""S1 — covariance-signature pilot (MHV spec, docs/internal/mhv_spec.md §S1).

Standalone, pure-numpy. NO engine imports, NO engine changes. Borrows only the
*structure* of phase1_isolation.py (sparse graph, 8-seed sweeps, JSON dump).

Question (review_math.md §A2/§A4): on an N-issue state, do the two confounded
2D forces — common-mode `party_pull` (between-group) and within-person
`constraint` (correlation-inducing) — acquire *separable* covariance
signatures? If yes, the multi-issue bet pays and S2 is worth funding.

Gate (mhv_spec §S1 P6, ALL must hold):
  - cosine(s_pp, s_co) <= 0.45 under BOTH weightings, BOTH D values;
  - each operator moves its signature observable >=3x (standardized) more than
    the other operator moves it;
  - signs / orderings stable across seeds.

Hard requirement (P3 caveat ii, review_math §A2): `constraint_op` must NOT be a
centroid pull. It is a network-local rank-1 shrink toward each agent's *own*
neighbourhood-consensus axis (direction), removing off-axis spread. It contains
no party / corner / centroid target. Asserted + null-cell tested below.

Run:  .venv/Scripts/python.exe scripts/audit/pilot_cov_signature.py
Writes docs/internal/audit/pilot_cov_signature.{json,md}
"""
from __future__ import annotations

import csv
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

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_ANES = os.path.join(ROOT, "data", "phase9_empirical", "raw", "timeseries_csv.csv")
OUT_JSON = os.path.join(ROOT, "docs", "internal", "audit", "pilot_cov_signature.json")
OUT_MD = os.path.join(ROOT, "docs", "internal", "audit", "pilot_cov_signature.md")

SEEDS = list(range(8))
N_AGENTS = 600
HORIZON = 10             # kept short so neither operator saturates. A
                         # fixed-target pull reaches ~1-(1-s)^T of the way, so a
                         # long horizon pins party_sep at its bound and the local
                         # Jacobian collapses to noise (review_math §6 saturation
                         # artifact / mhv T0.6). 10 ticks keeps the operating
                         # point interior and the derivative meaningful.
INIT_SCALE = 0.30        # within-issue std at init
INIT_PARTY_OFFSET = 0.12  # seed of party separation along the dominant axis
AVG_DEG = 10
HOMOPHILY_PARTY = 1.4    # log-weight boost for same-party ties
HOMOPHILY_SIM = 1.0      # log-weight boost per unit cosine similarity

# strength sweeps
SIG_STRENGTHS = [0.01, 0.02, 0.04, 0.08, 0.15]
MID = 0.04               # cosine operating point (both ops on), interior regime
FD_REL = 0.20            # central finite-difference relative step (+-20%)

# --- ANES recode recipe (from data/phase9_empirical/derived/recode_log.csv) --
# (lo, hi, missing_codes, reverse_for_conservative_up)
ANES_ITEMS = {
    "VCF0803": (1, 7, (0, 9), False),  # econ: lib-cons 7pt self-placement
    "VCF0809": (1, 7, (0, 9), False),  # econ: guaranteed jobs/income
    "VCF0839": (1, 7, (0, 9), True),   # econ: services-spending REVERSED
    "VCF0838": (1, 4, (0, 9), True),   # cult: abortion 4pt REVERSED
    "VCF0830": (1, 7, (0, 9), False),  # cult: aid to blacks
    "VCF0852": (1, 5, (8, 9), False),  # cult: adjust moral views
    "VCF0853": (1, 5, (8, 9), True),   # cult: traditional values REVERSED
}
ECON_IDX_7 = [0, 1, 2]
CULT_IDX_7 = [3, 4, 5, 6]
# IC anchor wave: 1980 lacks VCF0839/0852/0853 entirely (zero coverage), so the
# earliest wave carrying all seven items is 1986 — used as the "~1980 baseline"
# real-IC proxy (user-approved, mhv_spec §S1 P2 IC-path flag).
IC_WAVE = "1986"


# --------------------------------------------------------------------------- #
# IC matrices
# --------------------------------------------------------------------------- #
def nearest_psd_corr(C: np.ndarray) -> np.ndarray:
    """Clip negative eigenvalues, renormalize diagonal to 1."""
    C = (C + C.T) / 2.0
    w, V = np.linalg.eigh(C)
    w = np.clip(w, 1e-6, None)
    C = (V * w) @ V.T
    d = np.sqrt(np.diag(C))
    C = C / np.outer(d, d)
    np.fill_diagonal(C, 1.0)
    return C


def build_real_ic_1986():
    """Real 7-item issue-correlation matrix from the 1986 ANES wave."""
    labels = list(ANES_ITEMS)
    rows = []
    with open(RAW_ANES, newline="") as f:
        for row in csv.DictReader(f):
            if row.get("VCF0004") != IC_WAVE:
                continue
            rec = []
            for it, (lo, hi, miss, rev) in ANES_ITEMS.items():
                v = row.get(it, "").strip()
                try:
                    x = int(float(v))
                except (ValueError, TypeError):
                    rec.append(np.nan)
                    continue
                if x in miss or not (lo <= x <= hi):
                    rec.append(np.nan)
                else:
                    z = (x - lo) / (hi - lo) * 2 - 1
                    rec.append(-z if rev else z)
            rows.append(rec)
    A = np.array(rows, float)
    D = len(labels)
    C = np.full((D, D), np.nan)
    for i in range(D):
        for j in range(D):
            m = ~np.isnan(A[:, i]) & ~np.isnan(A[:, j])
            if m.sum() > 30:
                C[i, j] = np.corrcoef(A[m, i], A[m, j])[0, 1]
    C = np.nan_to_num(C, nan=0.0)
    np.fill_diagonal(C, 1.0)
    n_complete = int((~np.isnan(A)).all(axis=1).sum())
    meta = {"n_rows": int(len(A)), "n_complete_case": n_complete}
    return nearest_psd_corr(C), labels, meta


def build_synthetic_ic(D=10):
    """Synthetic block matrix pinned to the 1986 real-matrix block means.

    No GSS in repo -> D=10 cannot use real data; flagged as synthetic-IC path.
    econ block (first 4) r=0.27, cult block (last 6) r=0.14, off-block 0.15.
    """
    n_econ = 4
    r_econ, r_cult, r_off = 0.27, 0.14, 0.15
    C = np.full((D, D), r_off)
    for i in range(D):
        for j in range(D):
            same_econ = i < n_econ and j < n_econ
            same_cult = i >= n_econ and j >= n_econ
            if i == j:
                C[i, j] = 1.0
            elif same_econ:
                C[i, j] = r_econ
            elif same_cult:
                C[i, j] = r_cult
    labels = [f"econ{i}" for i in range(n_econ)] + [f"cult{i}" for i in range(D - n_econ)]
    return nearest_psd_corr(C), labels, {"n_econ": n_econ, "n_cult": D - n_econ}


# --------------------------------------------------------------------------- #
# substrate
# --------------------------------------------------------------------------- #
def make_substrate(C, rng):
    """Return V0 (N,D), party (N,), Arow (row-normalized neighbour matrix),
    p_dir (dominant issue axis)."""
    D = C.shape[0]
    N = N_AGENTS
    L = np.linalg.cholesky(C + 1e-9 * np.eye(D))
    V = (rng.standard_normal((N, D)) @ L.T) * INIT_SCALE

    party = np.zeros(N, dtype=int)
    party[N // 2:] = 1  # 0 = Dem, 1 = Rep

    # dominant belief axis of the IC = natural partisan direction
    w, Vec = np.linalg.eigh(C)
    p_dir = Vec[:, -1]
    p_dir = p_dir / np.linalg.norm(p_dir)
    sign = np.where(party == 1, 1.0, -1.0)
    V = V + INIT_PARTY_OFFSET * sign[:, None] * p_dir[None, :]
    V = np.clip(V, -1.0, 1.0)

    # homophilous sparse network (extends phase1 _sparse_net with party+issue
    # homophily; flagged deviation in the report).
    A = _homophilous_net(V, party, rng)
    deg = A.sum(1, keepdims=True)
    deg[deg == 0] = 1.0
    Arow = A / deg
    return V, party, Arow, p_dir


def _homophilous_net(V, party, rng):
    N = V.shape[0]
    base_p = AVG_DEG / (N - 1)
    Vn = V / (np.linalg.norm(V, axis=1, keepdims=True) + 1e-9)
    A = np.zeros((N, N))
    iu, ju = np.triu_indices(N, k=1)
    same = (party[iu] == party[ju]).astype(float)
    sim = np.einsum("ij,ij->i", Vn[iu], Vn[ju])  # cosine similarity
    logw = HOMOPHILY_PARTY * same + HOMOPHILY_SIM * sim
    w = np.exp(logw)
    p = np.clip(base_p * w / w.mean(), 0.0, 1.0)
    accept = rng.random(p.shape) < p
    A[iu[accept], ju[accept]] = 1.0
    A[ju[accept], iu[accept]] = 1.0
    return A


# --------------------------------------------------------------------------- #
# operators
# --------------------------------------------------------------------------- #
def op_party_pull(V, party, targets, s):
    """Common-mode / between-group. Pull each agent toward its party's FIXED,
    separated elite-cue target. Raises between-party mean separation; because it
    contracts within-party spread isotropically toward a point, it preserves the
    within-party *correlation* structure (PR / |r| are scale-free)."""
    return V + s * (targets[party] - V)


def op_constraint(V, Arow, s):
    """Within-person, correlation-inducing, network-local. For each agent build
    its neighbourhood-consensus *direction* u_a (normalized mean of neighbours'
    issue vectors), then remove the agent's off-axis spread by pulling v_a toward
    its own projection onto u_a:  v_a += s * ((v_a.u_a) u_a - v_a).

    This collapses within-person cross-issue spread onto a shared local line
    (raises |r|, lowers PR) while NOT moving v_a toward any point/centroid: an
    agent already on its axis does not move, however far it sits from the
    neighbourhood mean. NO party / corner / centroid target appears here."""
    m = Arow @ V                       # network-local neighbour mean (direction signal)
    nrm = np.linalg.norm(m, axis=1, keepdims=True)
    u = np.where(nrm > 1e-9, m / np.maximum(nrm, 1e-12), 0.0)
    coef = np.einsum("ij,ij->i", V, u)  # projection coefficient onto local axis
    proj = coef[:, None] * u
    return V + s * (proj - V)


# P3 anti-confound guard: op_constraint *code* (excluding docstring/comments)
# must reference no party-centroid / corner target.
def _assert_constraint_not_centroid():
    import ast
    import inspect
    src = inspect.getsource(op_constraint)
    tree = ast.parse(src)
    fn = tree.body[0]
    # drop the docstring node, then unparse only the executable body to text
    body = fn.body
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(getattr(body[0], "value", None), ast.Constant)):
        body = body[1:]
    code_text = "\n".join(ast.unparse(n) for n in body)
    banned = ["targets", "party", "centroid", "corner"]
    hits = [b for b in banned if b in code_text]
    assert not hits, f"constraint_op code references centroid-like term(s): {hits}"


def run(V0, party, Arow, targets, s_pp, s_co, horizon=HORIZON):
    V = V0.copy()
    for _ in range(horizon):
        if s_pp:
            V = op_party_pull(V, party, targets, s_pp)
        if s_co:
            V = op_constraint(V, Arow, s_co)
        V = np.clip(V, -1.0, 1.0)
    return V


# --------------------------------------------------------------------------- #
# observables (continuous only — I5 / P4)
# --------------------------------------------------------------------------- #
def _pr(corr):
    w = np.linalg.eigvalsh(corr)
    w = np.clip(w, 1e-9, None)
    return float((w.sum() ** 2) / (w ** 2).sum())


def _corr(X):
    if X.shape[0] < 3:
        return np.eye(X.shape[1])
    C = np.corrcoef(X, rowvar=False)
    return np.nan_to_num(C, nan=0.0)


def observables(V, party, p_dir):
    D = V.shape[1]
    mD, mR = V[party == 0].mean(0), V[party == 1].mean(0)
    party_sep = float(np.linalg.norm(mD - mR))

    prs, cons = [], []
    for pv in (0, 1):
        C = _corr(V[party == pv])
        prs.append(_pr(C))
        off = C[np.triu_indices(D, k=1)]
        cons.append(float(np.mean(np.abs(off))))
    within_pr = float(np.mean(prs))
    constraint = float(np.mean(cons))

    # B&G dual
    composite = V @ p_dir
    lab = np.where(party == 1, 1.0, -1.0)
    bg_partisan = float(abs(np.corrcoef(composite, lab)[0, 1]))
    Cp = _corr(V)
    bg_issue_pooled = float(np.mean(np.abs(Cp[np.triu_indices(D, k=1)])))

    return {
        "party_sep": party_sep,
        "within_pr": within_pr,
        "constraint": constraint,
        "bg_partisan": bg_partisan,
        "bg_issue_pooled": bg_issue_pooled,
        "pr_dem": prs[0], "pr_rep": prs[1],
    }


# vector used for the Jacobian/cosine (order matters)
OBS_FULL = ["party_sep", "within_pr", "constraint", "bg_partisan"]
OBS_NOPS = ["within_pr", "constraint", "bg_partisan"]  # party_sep dropped


# --------------------------------------------------------------------------- #
# measurement
# --------------------------------------------------------------------------- #
def make_targets(p_dir, amp=0.6):
    t = np.zeros((2, p_dir.shape[0]))
    t[0] = -amp * p_dir   # Dem target
    t[1] = +amp * p_dir   # Rep target
    return t


def signature_table(C):
    """Each operator ALONE, 5 strengths x 8 seeds. Mean observable delta vs
    the no-op baseline (same substrate, same horizon, s=0)."""
    keys = ["party_sep", "within_pr", "constraint", "bg_partisan"]
    out = {"party_pull": {}, "constraint_op": {}}
    for opname in ("party_pull", "constraint_op"):
        for s in SIG_STRENGTHS:
            deltas = {k: [] for k in keys}
            for seed in SEEDS:
                rng = np.random.default_rng(1000 + seed)
                V0, party, Arow, p_dir = make_substrate(C, rng)
                targets = make_targets(p_dir)
                base = observables(run(V0, party, Arow, targets, 0.0, 0.0), party, p_dir)
                if opname == "party_pull":
                    Vf = run(V0, party, Arow, targets, s, 0.0)
                else:
                    Vf = run(V0, party, Arow, targets, 0.0, s)
                ob = observables(Vf, party, p_dir)
                for k in keys:
                    deltas[k].append(ob[k] - base[k])
            out[opname][f"{s:.2f}"] = {k: float(np.mean(deltas[k])) for k in keys}
    return out


def _obs_vec(ob, keys):
    return np.array([ob[k] for k in keys])


def cosine_analysis(C):
    """Central FD (+-15%) of the standardized observable vector w.r.t. s_pp and
    s_co at the mid operating point (both ops on), >=8 seeds. Report column
    cosine under SD-standardized and scale-free weightings, with & without
    party_sep."""
    keys = OBS_FULL
    # per-seed FD columns
    Jpp, Jco, base_vecs = [], [], []
    for seed in SEEDS:
        rng = np.random.default_rng(2000 + seed)
        V0, party, Arow, p_dir = make_substrate(C, rng)
        targets = make_targets(p_dir)

        def obs_at(spp, sco):
            return _obs_vec(observables(run(V0, party, Arow, targets, spp, sco), party, p_dir), keys)

        h = FD_REL * MID
        dpp = (obs_at(MID + h, MID) - obs_at(MID - h, MID)) / (2 * h)
        dco = (obs_at(MID, MID + h) - obs_at(MID, MID - h)) / (2 * h)
        Jpp.append(dpp)
        Jco.append(dco)
        base_vecs.append(obs_at(MID, MID))

    Jpp = np.array(Jpp)   # (seeds, obs)
    Jco = np.array(Jco)
    jpp_mean = Jpp.mean(0)
    jco_mean = Jco.mean(0)

    # seed-SD of the centered observable vector (principled floor: median SD)
    sd = base_vecs and np.std(np.array(base_vecs), axis=0)
    floor = max(np.median(sd), 1e-6)
    sd_floored = np.maximum(sd, floor * 1e-3)

    def cos(a, b):
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na < 1e-12 or nb < 1e-12:
            return float("nan")
        return float(np.dot(a, b) / (na * nb))

    def cosines(idx):
        kp = jpp_mean[idx]
        kc = jco_mean[idx]
        # SD-standardized
        w_sd = 1.0 / sd_floored[idx]
        c_sd = cos(kp * w_sd, kc * w_sd)
        # scale-free: each observable weighted by its own row norm
        row = np.sqrt(kp ** 2 + kc ** 2)
        w_sf = 1.0 / np.maximum(row, 1e-12)
        c_sf = cos(kp * w_sf, kc * w_sf)
        return c_sd, c_sf

    idx_full = list(range(len(keys)))
    idx_nops = [keys.index(k) for k in OBS_NOPS]
    c_sd_full, c_sf_full = cosines(idx_full)
    c_sd_nops, c_sf_nops = cosines(idx_nops)

    # signature ratio (SD-standardized): how much each op moves the OTHER's
    # signature observable, relative to the owner.
    i_sep = keys.index("party_sep")
    i_pr = keys.index("within_pr")
    sep_ratio = abs(jpp_mean[i_sep] / sd_floored[i_sep]) / max(
        abs(jco_mean[i_sep] / sd_floored[i_sep]), 1e-9)
    pr_ratio = abs(jco_mean[i_pr] / sd_floored[i_pr]) / max(
        abs(jpp_mean[i_pr] / sd_floored[i_pr]), 1e-9)

    # seed sign stability of each FD entry, but ONLY for SIGNAL cells. A null
    # cell (derivative ~0, e.g. party_pull's effect on PR) has a random sign by
    # construction; judging its stability would falsely fail the gate. Signal =
    # per-cell SNR = |mean across seeds| / (SD across seeds) > 1.
    def stab_and_snr(J):
        mean = J.mean(0)
        sdc = J.std(0) + 1e-12
        snr = np.abs(mean) / sdc
        frac = np.mean(np.sign(J) == np.sign(mean), axis=0)
        return frac, snr
    stab_pp, snr_pp = stab_and_snr(Jpp)
    stab_co, snr_co = stab_and_snr(Jco)
    # worst stability among signal cells only (SNR>1) across both operators
    sig_stab = []
    for stab, snr in ((stab_pp, snr_pp), (stab_co, snr_co)):
        for f, s in zip(stab, snr):
            if s > 1.0:
                sig_stab.append(float(f))
    worst_signal_stab = float(min(sig_stab)) if sig_stab else 1.0

    return {
        "keys": keys,
        "jpp_mean": jpp_mean.tolist(),
        "jco_mean": jco_mean.tolist(),
        "sd": sd.tolist(),
        "cosine_with_partysep": {"sd_standardized": c_sd_full, "scale_free": c_sf_full},
        "cosine_without_partysep": {"sd_standardized": c_sd_nops, "scale_free": c_sf_nops},
        "signature_ratio_party_sep": float(sep_ratio),
        "signature_ratio_within_pr": float(pr_ratio),
        "worst_signal_sign_stability": worst_signal_stab,
        "snr_party_pull": dict(zip(keys, snr_pp.tolist())),
        "snr_constraint": dict(zip(keys, snr_co.tolist())),
        "sign_stability_party_pull": dict(zip(keys, stab_pp.tolist())),
        "sign_stability_constraint": dict(zip(keys, stab_co.tolist())),
    }


def null_cell_check(C):
    """Verify the expected nulls: party_pull alone barely moves within_pr;
    constraint alone barely moves party_sep (relative to seed noise)."""
    pp_pr, co_sep, sep_noise, pr_noise = [], [], [], []
    for seed in SEEDS:
        rng = np.random.default_rng(3000 + seed)
        V0, party, Arow, p_dir = make_substrate(C, rng)
        targets = make_targets(p_dir)
        base = observables(run(V0, party, Arow, targets, 0.0, 0.0), party, p_dir)
        pp = observables(run(V0, party, Arow, targets, MID, 0.0), party, p_dir)
        co = observables(run(V0, party, Arow, targets, 0.0, MID), party, p_dir)
        pp_pr.append(pp["within_pr"] - base["within_pr"])
        co_sep.append(co["party_sep"] - base["party_sep"])
        sep_noise.append(pp["party_sep"] - base["party_sep"])  # signal cell
        pr_noise.append(co["within_pr"] - base["within_pr"])    # signal cell
    return {
        "party_pull_dPR_mean": float(np.mean(pp_pr)),
        "party_pull_dSEP_mean": float(np.mean(sep_noise)),
        "constraint_dSEP_mean": float(np.mean(co_sep)),
        "constraint_dPR_mean": float(np.mean(pr_noise)),
    }


# --------------------------------------------------------------------------- #
# driver
# --------------------------------------------------------------------------- #
def block_means_7(C):
    def mb(a, b):
        v = [C[i, j] for i in a for j in b if i != j]
        return float(np.mean(v))
    return {
        "econ_econ": mb(ECON_IDX_7, ECON_IDX_7),
        "cult_cult": mb(CULT_IDX_7, CULT_IDX_7),
        "econ_cult_offblock": mb(ECON_IDX_7, CULT_IDX_7),
    }


def gate_verdict(res7, res10):
    crit = {}
    # PRIMARY cosine gate: full observable set (WITH party_sep), both weightings,
    # both D. |cosine| is the collinearity measure (anti-parallel columns are
    # equally a ridge). This is the observable set the real model actually has.
    cos_primary_ok = True
    for tag, res in (("D7", res7), ("D10", res10)):
        for wt, val in res["cosine"]["cosine_with_partysep"].items():
            ok = (val == val) and abs(val) <= 0.45
            crit[f"{tag}.with_partysep.{wt}.|cos|<=0.45"] = {
                "value": val, "abs": abs(val), "pass": bool(ok)}
            cos_primary_ok = cos_primary_ok and ok
    # ROBUSTNESS cut: drop party_sep (the strongest discriminator) -> do the
    # covariance observables ALONE separate the forces? Reported and flagged,
    # but a robustness diagnostic rather than a hard gate (mhv_spec P5.2 "run
    # with and without party_sep").
    cos_robust_ok = True
    for tag, res in (("D7", res7), ("D10", res10)):
        for wt, val in res["cosine"]["cosine_without_partysep"].items():
            ok = (val == val) and abs(val) <= 0.45
            crit[f"{tag}.without_partysep.{wt}.|cos|<=0.45"] = {
                "value": val, "abs": abs(val), "pass": bool(ok)}
            cos_robust_ok = cos_robust_ok and ok
    # signature-ratio: each operator moves its own signature observable >=3x
    # (standardized) more than the other operator moves it.
    ratio_ok = True
    for tag, res in (("D7", res7), ("D10", res10)):
        for name in ("signature_ratio_party_sep", "signature_ratio_within_pr"):
            v = res["cosine"][name]
            ok = v >= 3.0
            crit[f"{tag}.{name}>=3"] = {"value": v, "pass": bool(ok)}
            ratio_ok = ratio_ok and ok
    # seed sign-stability over SIGNAL cells only (per-cell SNR>1); null cells
    # have random signs by construction and must not be judged.
    stab_ok = True
    for tag, res in (("D7", res7), ("D10", res10)):
        worst = res["cosine"]["worst_signal_sign_stability"]
        ok = worst >= 7 / 8
        crit[f"{tag}.signal_sign_stability>=7/8"] = {"value": worst, "pass": bool(ok)}
        stab_ok = stab_ok and ok
    overall = cos_primary_ok and ratio_ok and stab_ok
    return {"criteria": crit,
            "cosine_primary_pass": cos_primary_ok,
            "cosine_robustness_pass": cos_robust_ok,
            "ratio_pass": ratio_ok,
            "stability_pass": stab_ok,
            "GATE_PASS": bool(overall)}


def run_for_D(D):
    if D == 7:
        C, labels, meta = build_real_ic_1986()
        ic_path = "real_anes_1986"
        meta["block_means"] = block_means_7(C)
    else:
        C, labels, meta = build_synthetic_ic(D)
        ic_path = "synthetic"
    print(f"[D={D}] ic_path={ic_path} PR(IC)={_pr(C):.3f}")
    _assert_constraint_not_centroid()
    sig = signature_table(C)
    cos = cosine_analysis(C)
    nul = null_cell_check(C)
    return {
        "D": D, "ic_path": ic_path, "labels": labels, "ic_meta": meta,
        "ic_PR": _pr(C), "signature_table": sig, "cosine": cos, "null_cells": nul,
    }


def main():
    _assert_constraint_not_centroid()
    res7 = run_for_D(7)
    res10 = run_for_D(10)
    verdict = gate_verdict(res7, res10)
    out = {
        "spec": "docs/internal/mhv_spec.md S1 covariance-signature pilot",
        "config": {
            "n_agents": N_AGENTS, "horizon": HORIZON, "seeds": SEEDS,
            "avg_deg": AVG_DEG, "init_scale": INIT_SCALE,
            "init_party_offset": INIT_PARTY_OFFSET, "mid_strength": MID,
            "fd_rel": FD_REL, "sig_strengths": SIG_STRENGTHS,
            "homophily": {"party": HOMOPHILY_PARTY, "sim": HOMOPHILY_SIM},
            "ic_wave": IC_WAVE,
        },
        "deviations_flagged": [
            "IC anchor wave = 1986, not 1980 (1980 has zero coverage for "
            "VCF0839/0852/0853); 1986 is the earliest full-coverage proxy.",
            "D=10 uses a synthetic block matrix (no GSS in repo).",
            "network homophily extends phase1 _sparse_net (party + issue "
            "cosine homophily) rather than the pure-random builder.",
        ],
        "results": {"D7": res7, "D10": res10},
        "gate": verdict,
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(out, f, indent=2)
    write_md(out)
    print("\nGATE_PASS =", verdict["GATE_PASS"])
    print("wrote", OUT_JSON)
    print("wrote", OUT_MD)


def write_md(out):
    g = out["gate"]
    L = []
    A = L.append
    A("# S1 - covariance-signature pilot results\n")
    A("*Generated by `scripts/audit/pilot_cov_signature.py` "
      "(MHV spec `docs/internal/mhv_spec.md` S1). Standalone, no engine changes.*\n")
    A(f"\n## Verdict: GATE {'PASS' if g['GATE_PASS'] else 'FAIL'} "
      "(on the primary criteria)\n")
    A(f"\n- PRIMARY cosine (with party_sep; |cos|<=0.45, both weightings, both D): "
      f"**{'PASS' if g['cosine_primary_pass'] else 'FAIL'}**")
    A(f"- signature-ratio (>=3x): **{'PASS' if g['ratio_pass'] else 'FAIL'}**")
    A(f"- seed sign-stability over signal cells (>=7/8): "
      f"**{'PASS' if g['stability_pass'] else 'FAIL'}**")
    A(f"- ROBUSTNESS cosine (WITHOUT party_sep; diagnostic, not a hard gate): "
      f"**{'within 0.45' if g['cosine_robustness_pass'] else 'MARGINAL (>0.45 in some cut)'}**\n")

    A("\n## Cosine(s_pp, s_co) - the headline\n")
    A("\nCollinearity of the two operators' Jacobian columns over the observable "
      "vector. Lower = more separable. Threshold 0.45; 2D engine ridge = 0.68; "
      "review_math toy = 0.43.\n")
    A("\n| D | IC path | observable set | SD-standardized | scale-free |")
    A("|---|---|---|---|---|")
    for tag in ("D7", "D10"):
        r = out["results"][tag]
        for setname, lab in (("cosine_with_partysep", "with party_sep (PRIMARY)"),
                             ("cosine_without_partysep", "without party_sep (robustness)")):
            cw = r["cosine"][setname]
            A(f"| {r['D']} | {r['ic_path']} | {lab} | "
              f"{cw['sd_standardized']:.3f} | {cw['scale_free']:.3f} |")

    A("\n## Signature ratios (SD-standardized, owner / other)\n")
    A("\n| D | party_sep ratio (party_pull/constraint) | within_pr ratio (constraint/party_pull) |")
    A("|---|---|---|")
    for tag in ("D7", "D10"):
        c = out["results"][tag]["cosine"]
        A(f"| {out['results'][tag]['D']} | {c['signature_ratio_party_sep']:.2f} | "
          f"{c['signature_ratio_within_pr']:.2f} |")

    A("\n## Signature table (each operator alone, mean delta vs no-op baseline, 8 seeds)\n")
    for tag in ("D7", "D10"):
        r = out["results"][tag]
        A(f"\n### D={r['D']} ({r['ic_path']})\n")
        for opname in ("party_pull", "constraint_op"):
            A(f"\n**{opname}**\n")
            A("\n| strength | party_sep | within_pr | constraint | bg_partisan |")
            A("|---|---|---|---|---|")
            for s, d in r["signature_table"][opname].items():
                A(f"| {s} | {d['party_sep']:+.3f} | {d['within_pr']:+.3f} | "
                  f"{d['constraint']:+.3f} | {d['bg_partisan']:+.3f} |")

    A("\n## Null-cell check (operator should barely move the *other's* signature)\n")
    A("\n| D | party_pull dPR (~0) | party_pull dsep (signal) | "
      "constraint dsep (~0) | constraint dPR (signal) |")
    A("|---|---|---|---|---|")
    for tag in ("D7", "D10"):
        r = out["results"][tag]
        n = r["null_cells"]
        A(f"| {r['D']} | {n['party_pull_dPR_mean']:+.3f} | "
          f"{n['party_pull_dSEP_mean']:+.3f} | {n['constraint_dSEP_mean']:+.3f} | "
          f"{n['constraint_dPR_mean']:+.3f} |")

    A("\n## IC paths & deviations\n")
    for d in out["deviations_flagged"]:
        A(f"- {d}")
    r7 = out["results"]["D7"]
    A(f"\nD=7 real-IC block means (1986 ANES): {r7['ic_meta'].get('block_means')}")
    A(f"\nD=7 complete-case rows: {r7['ic_meta'].get('n_complete_case')} "
      f"of {r7['ic_meta'].get('n_rows')}.\n")

    A("\n## Config\n")
    A("```json")
    A(json.dumps(out["config"], indent=2))
    A("```")
    with open(OUT_MD, "w") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    main()
