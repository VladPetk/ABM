"""Head-to-head: two candidate 250-agent published clouds vs reality + model truth.

METHOD A (per-index average): for each agent index i, mean its 2D position across
  K=8 clean seeds -> 250 averaged agents/tick. (Hypothesis: collapses within-party
  variance.)
METHOD B (ensemble subsample): pool K*250 agents, draw a uniform 250-agent
  cross-seed subsample (preserves the true dispersion).

References: (1) raw ANES respondents (external realism), (2) the MODEL's full
K*250 ensemble (ground truth for "faithful representation of the model").

Reports CENTROID/location AND DISPERSION/overlap metrics at 1996 + 2020. Analysis
only; abm/ untouched.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.stats import gaussian_kde
import sys

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "figures"; OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT))
from scripts.anes_preset import ANES_FULL_KWARGS
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to

K = 8
TICKS = {1996: 48, 2020: 120}
GRID = np.linspace(-1.05, 1.05, 81); GX, GY = np.meshgrid(GRID, GRID)
GPOS = np.vstack([GX.ravel(), GY.ravel()]); CELL = (GRID[1]-GRID[0])**2; BW = 0.30
PARTY_COLORS = {0: "#1f3565", 1: "#8b2530"}
_RNG = np.random.default_rng(20260616)   # fixed draw seed (reproducible subsample)


def collect():
    """Per-seed (pos, party) at each tick; party is fixed per index within a seed,
    but indices are aligned ACROSS seeds only at build (party can diverge via
    realignment/replacement) -> for Method A we average position per index and take
    the per-index MAJORITY party across seeds."""
    seeds_pos = {t: [] for t in TICKS.values()}
    seeds_party = {t: [] for t in TICKS.values()}
    for s in range(K):
        kw = dict(ANES_FULL_KWARGS)
        eng = build_engine(seed=s, **kw)
        sched = build_schedule(factional_seeding=False, faction_anchor_events=True,
                               evidence_regrade=kw["evidence_regrade"],
                               exogenous_shocks=kw["exogenous_shocks"])
        want = set(TICKS.values())
        for t in range(1, max(want) + 1):
            run_to(eng, sched, t)
            if t in want:
                seeds_pos[t].append(np.array([a.state.ideology for a in eng.agents]))
                seeds_party[t].append(np.array([a.state.attrs.get("party") for a in eng.agents]))
    return seeds_pos, seeds_party


def method_A(pos_list, party_list):
    """Per-index average position; per-index majority party across seeds."""
    P = np.stack(pos_list)        # (K, 250, 2)
    Y = np.stack(party_list)      # (K, 250)
    pos = P.mean(0)               # (250, 2) averaged
    # majority party per index (mode over seeds)
    party = np.array([np.bincount(Y[:, i][Y[:, i] >= 0].astype(int),
                                  minlength=3).argmax() for i in range(Y.shape[1])])
    return pos, party


def method_B(pos_list, party_list):
    """Pool K*250 agents; uniform 250-agent cross-seed subsample."""
    P = np.vstack(pos_list); Y = np.concatenate(party_list)
    idx = _RNG.choice(len(P), size=250, replace=False)
    return P[idx], Y[idx]


def ensemble(pos_list, party_list):
    return np.vstack(pos_list), np.concatenate(party_list)


# ---- ANES respondents ----
df = pd.read_csv(ROOT / "data/phase9_empirical/derived/respondent_coordinates.csv")


def anes_cloud(yr):
    a = df[(df["year"] == yr) & (df["party"].isin(["D", "R"]))]
    pos = a[["econ", "cult"]].to_numpy()
    party = (a["party"] == "R").astype(int).to_numpy()
    w = a["weight"].to_numpy()
    return pos, party, w


# ---- metrics ----
def kde_norm(xy, w=None):
    if len(xy) < 5:
        return None
    f = gaussian_kde(xy.T, bw_method=BW, weights=w)(GPOS).reshape(GX.shape)
    return f / (f.sum() * CELL)


def metrics(pos, party, w=None):
    m = np.isin(party, (0, 1))
    pos, party = pos[m], party[m]
    w = None if w is None else np.asarray(w)[m]
    D, R = pos[party == 0], pos[party == 1]
    wD = None if w is None else w[party == 0]; wR = None if w is None else w[party == 1]

    def avg(x, ww):
        return np.average(x, axis=0, weights=ww)

    def sd(x, ww):
        mu = avg(x, ww); v = np.average((x - mu) ** 2, axis=0, weights=ww); return np.sqrt(v)
    mD, mR = avg(D, wD), avg(R, wR)
    eg, cg = float(mR[0] - mD[0]), float(mR[1] - mD[1])
    sdD, sdR = sd(D, wD), sd(R, wR)
    wp_sd = 0.5 * (sdD + sdR)   # pooled within-party SD per axis
    fD, fR = kde_norm(D, wD), kde_norm(R, wR)
    ovl = float(np.minimum(fD, fR).sum() * CELL)
    # Bhattacharyya (Gaussian)
    cD = np.cov(D.T, aweights=wD); cR = np.cov(R.T, aweights=wR); C = 0.5 * (cD + cR)
    dm = mR - mD
    Db = 0.125 * dm @ np.linalg.inv(C) @ dm + 0.5 * np.log(
        np.linalg.det(C) / np.sqrt(np.linalg.det(cD) * np.linalg.det(cR)))
    bc = float(np.exp(-Db))
    # LDA accuracy (separability)
    Sw = 0.5 * (cD + cR); wv = np.linalg.inv(Sw) @ dm; thr = 0.5 * (mD + mR) @ wv
    corr = wtot = 0.0
    for lab, sub, ww, sign in (("D", D, wD, -1), ("R", R, wR, +1)):
        s = sub @ wv - thr; pred_R = s > 0
        cw = (np.ones(len(sub)) if ww is None else ww)
        corr += cw[(pred_R) == (sign > 0)].sum(); wtot += cw.sum()
    acc = float(corr / wtot)
    rll = float(np.average((R[:, 0] <= 0) & (R[:, 1] <= 0), weights=wR))
    return dict(mD=mD, mR=mR, eg=eg, cg=cg, sep=float(np.hypot(eg, cg)),
                sdR_e=float(sdR[0]), sdR_c=float(sdR[1]), sdD_e=float(sdD[0]), sdD_c=float(sdD[1]),
                wp_sd_e=float(wp_sd[0]), wp_sd_c=float(wp_sd[1]),
                ovl=ovl, bc=bc, acc=acc, rll=rll)


SP, SY = collect()
ANES_REF = {1996: dict(), 2020: dict()}
rows = {}
for yr, t in TICKS.items():
    A = metrics(*method_A(SP[t], SY[t]))
    B = metrics(*method_B(SP[t], SY[t]))
    E = metrics(*ensemble(SP[t], SY[t]))
    ap, ay, aw = anes_cloud(yr)
    AN = metrics(ap, ay, aw)
    rows[yr] = dict(A=A, B=B, E=E, ANES=AN)

# ---------- report ----------
def line(label, key, fmt="{:.3f}"):
    out = f"  {label:<26}"
    for yr in (1996, 2020):
        for who in ("A", "B", "E", "ANES"):
            out += " " + fmt.format(rows[yr][who][key])
    return out

print("=" * 100)
print("HEAD-TO-HEAD  (columns: 1996[A B Ensemble ANES]  |  2020[A B Ensemble ANES])")
print("=" * 100)
print(f"  {'':<26}" + "  A     B    Ens   ANES" + "    A     B    Ens   ANES")
print("--- CENTROID / LOCATION ---")
for lab, k in [("econ gap (R-D)", "eg"), ("cult gap (R-D)", "cg"), ("centroid sep", "sep"),
               ("R econ centroid", None)]:
    if k:
        print(line(lab, k))
print("--- DISPERSION / OVERLAP ---")
for lab, k in [("R within-SD econ", "sdR_e"), ("R within-SD cult", "sdR_c"),
               ("pooled wp-SD econ", "wp_sd_e"), ("pooled wp-SD cult", "wp_sd_c"),
               ("OVL overlap coef", "ovl"), ("Bhattacharyya BC", "bc"),
               ("LDA pos->party acc", "acc"), ("R-in-LL share", "rll")]:
    print(line(lab, k))

print("\n--- VARIANCE-COLLAPSE quantification (pooled within-party SD ratio vs ENSEMBLE truth) ---")
for yr in (1996, 2020):
    for ax, k in (("econ", "wp_sd_e"), ("cult", "wp_sd_c")):
        e = rows[yr]["E"][k]; a = rows[yr]["A"][k]; b = rows[yr]["B"][k]; an = rows[yr]["ANES"][k]
        print(f"  {yr} {ax}: A/Ens {a/e:.2f}  B/Ens {b/e:.2f}  | SDs  A {a:.3f}  B {b:.3f}  Ens {e:.3f}  ANES {an:.3f}")

# ---------- figures ----------
def kde_p(xy):
    if len(xy) < 5:
        return None
    return gaussian_kde(xy.T, bw_method=BW)(GPOS).reshape(GX.shape)


def draw(ax, pos, party, title):
    m = np.isin(party, (0, 1)); pos, party = pos[m], party[m]
    f = kde_p(pos)
    if f is not None:
        ax.contourf(GRID, GRID, f, levels=8, cmap="Greys", alpha=0.30)
    for p in (0, 1):
        sub = pos[party == p]; fp = kde_p(sub)
        if fp is not None:
            ax.contour(GRID, GRID, fp, levels=4, colors=PARTY_COLORS[p], linewidths=0.9, alpha=0.85)
        if len(sub):
            ax.scatter(sub[:, 0], sub[:, 1], s=7, c=PARTY_COLORS[p], alpha=0.45, edgecolor="none")
            ax.scatter(*sub.mean(0), c=PARTY_COLORS[p], s=55, edgecolor="black", linewidth=0.7, zorder=6)
    ax.axhline(0, color="k", lw=0.4, alpha=0.3); ax.axvline(0, color="k", lw=0.4, alpha=0.3)
    ax.set_xlim(-1.05, 1.05); ax.set_ylim(-1.05, 1.05); ax.set_aspect("equal")
    ax.set_title(title, fontsize=10); ax.set_xlabel("Economic", fontsize=8)


for yr, t in TICKS.items():
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.6), sharex=True, sharey=True)
    a_pos, a_party = method_A(SP[t], SY[t]); b_pos, b_party = method_B(SP[t], SY[t])
    rA, rB = rows[yr]["A"], rows[yr]["B"]
    draw(axes[0], a_pos, a_party,
         f"METHOD A per-index avg — {yr}\nwp-SD econ={rA['wp_sd_e']:.3f} OVL={rA['ovl']:.2f} LDA={rA['acc']:.2f}")
    draw(axes[1], b_pos, b_party,
         f"METHOD B subsample — {yr}\nwp-SD econ={rB['wp_sd_e']:.3f} OVL={rB['ovl']:.2f} LDA={rB['acc']:.2f}")
    axes[0].set_ylabel("Cultural", fontsize=8)
    fig.suptitle(f"{yr}: per-index AVERAGE (A, tight) vs ensemble SUBSAMPLE (B, true spread) "
                 f"— dots = the 250 published agents", fontsize=11)
    fig.tight_layout()
    p = OUT / f"method_ab_{yr}.png"; fig.savefig(p, dpi=150); plt.close(fig)
    print("WROTE", p)
