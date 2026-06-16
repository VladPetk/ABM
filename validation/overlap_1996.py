"""PART 1: quantify the 1996 D-R overlap, model (published seed 1) vs raw ANES.
Formal overlap metrics + decomposition + figure. Analysis only."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "figures"; OUT.mkdir(exist_ok=True)
GRID = np.linspace(-1.05, 1.05, 121)
GX, GY = np.meshgrid(GRID, GRID); GPOS = np.vstack([GX.ravel(), GY.ravel()])
CELL = (GRID[1] - GRID[0]) ** 2
BW = 0.30

# ---- ANES 1996 respondents (weighted) ----
df = pd.read_csv(ROOT / "data/phase9_empirical/derived/respondent_coordinates.csv")
a96 = df[df["year"] == 1996]
aD = a96[a96["party"] == "D"]; aR = a96[a96["party"] == "R"]
anes = {
    "D": (aD[["econ", "cult"]].to_numpy(), aD["weight"].to_numpy()),
    "R": (aR[["econ", "cult"]].to_numpy(), aR["weight"].to_numpy()),
}

# ---- Model 1996 (published canonical seed 1, tick 48) ----
d = json.load(open(ROOT / "web/data/baseline/seed_1.json"))
t = int(round((1996 - d["tick_0_year"]) * d["ticks_per_year"]))
tk = d["ticks"][t]; pos = np.array(tk["positions"]); party = np.array(tk["party"])
model = {
    "D": (pos[party == 0], np.ones((party == 0).sum())),
    "R": (pos[party == 1], np.ones((party == 1).sum())),
}


def wmean(xy, w):
    return np.average(xy, axis=0, weights=w)


def wcov(xy, w):
    m = wmean(xy, w); d = xy - m
    return (w[:, None] * d).T @ d / w.sum()


def kde_eval(xy, w):
    k = gaussian_kde(xy.T, bw_method=BW, weights=w)
    f = k(GPOS).reshape(GX.shape)
    return f / (f.sum() * CELL)


def ovl(fD, fR):
    return float(np.minimum(fD, fR).sum() * CELL)   # overlap coefficient ∈ [0,1]


def bhattacharyya(g):
    mD, cD = wmean(*g["D"]), wcov(*g["D"]); mR, cR = wmean(*g["R"]), wcov(*g["R"])
    C = 0.5 * (cD + cR); dm = (mR - mD)
    Db = 0.125 * dm @ np.linalg.inv(C) @ dm + 0.5 * np.log(
        np.linalg.det(C) / np.sqrt(np.linalg.det(cD) * np.linalg.det(cR)))
    return float(np.exp(-Db)), float(Db)   # BC ∈ [0,1] (1=identical), Db distance


def lda_accuracy(g):
    """Weighted Fisher-LDA in-sample accuracy (a separability measure)."""
    mD, cD = wmean(*g["D"]), wcov(*g["D"]); mR, cR = wmean(*g["R"]), wcov(*g["R"])
    Sw = 0.5 * (cD + cR); w = np.linalg.inv(Sw) @ (mR - mD)
    thr = 0.5 * (mD + mR) @ w
    correct = wtot = 0.0
    for lab, sign in (("D", -1), ("R", +1)):
        xy, ww = g[lab]; s = xy @ w - thr
        pred_R = s > 0
        correct += ww[(pred_R) == (sign > 0)].sum(); wtot += ww.sum()
    return float(correct / wtot)


def quad_shares(g):
    xy, w = g["R"]
    ll = np.average((xy[:, 0] <= 0) & (xy[:, 1] <= 0), weights=w)
    return float(ll)


def r_on_dem_turf(g):
    """Share of R mass in the region where Dem density > Rep density."""
    fD = kde_eval(*g["D"]); fR = kde_eval(*g["R"])
    xy, w = g["R"]
    ix = np.clip(((xy[:, 0] - GRID[0]) / (GRID[1] - GRID[0])).astype(int), 0, len(GRID) - 1)
    iy = np.clip(((xy[:, 1] - GRID[0]) / (GRID[1] - GRID[0])).astype(int), 0, len(GRID) - 1)
    dem_majority = fD[iy, ix] > fR[iy, ix]
    return float(np.average(dem_majority, weights=w))


def analyze(g, name):
    mD, mR = wmean(*g["D"]), wmean(*g["R"])
    sep = float(np.hypot(*(mR - mD)))
    eg = float(mR[0] - mD[0]); cg = float(mR[1] - mD[1])
    fD, fR = kde_eval(*g["D"]), kde_eval(*g["R"])
    o = ovl(fD, fR); bc, db = bhattacharyya(g); acc = lda_accuracy(g)
    rll = quad_shares(g); rdt = r_on_dem_turf(g)
    print(f"\n--- {name} 1996 ---")
    print(f"  centroid sep (2D)     : {sep:.3f}   (econ gap {eg:.3f}, cult gap {cg:.3f})")
    print(f"  OVL overlap coef      : {o:.3f}   (0=disjoint, 1=identical)")
    print(f"  Bhattacharyya BC      : {bc:.3f}   (Db distance {db:.3f})")
    print(f"  LDA separation acc.   : {acc:.3f}   (0.5=no sep, 1=perfect)")
    print(f"  R in lower-left (LL)  : {rll*100:.1f}%")
    print(f"  R on Dem-majority turf: {rdt*100:.1f}%")
    return dict(name=name, sep=sep, eg=eg, cg=cg, ovl=o, bc=bc, acc=acc, rll=rll, rdt=rdt,
                fD=fD, fR=fR, mD=mD, mR=mR)


print("=" * 70)
print("PART 1 — 1996 D-R overlap: MODEL (published seed 1) vs RAW ANES")
print("=" * 70)
A = analyze(anes, "ANES (real)")
M = analyze(model, "MODEL (seed 1)")

print("\n" + "=" * 70)
print("DECOMPOSITION (model vs ANES at 1996)")
print("=" * 70)
print(f"  centroid sep : model {M['sep']:.3f} vs ANES {A['sep']:.3f}  -> gap {M['sep']-A['sep']:+.3f}")
print(f"    econ gap   : model {M['eg']:.3f} vs ANES {A['eg']:.3f}  -> {M['eg']-A['eg']:+.3f}")
print(f"    cult gap   : model {M['cg']:.3f} vs ANES {A['cg']:.3f}  -> {M['cg']-A['cg']:+.3f}")
print(f"  R-in-LL      : model {M['rll']*100:.1f}% vs ANES {A['rll']*100:.1f}%  -> EXCESS {(M['rll']-A['rll'])*100:+.1f} pts")
print(f"  R-on-Dem-turf: model {M['rdt']*100:.1f}% vs ANES {A['rdt']*100:.1f}%  -> EXCESS {(M['rdt']-A['rdt'])*100:+.1f} pts")
print(f"  OVL          : model {M['ovl']:.3f} vs ANES {A['ovl']:.3f}  -> EXCESS overlap {M['ovl']-A['ovl']:+.3f}")
print(f"  LDA acc      : model {M['acc']:.3f} vs ANES {A['acc']:.3f}  -> {M['acc']-A['acc']:+.3f}")
faithful = A['ovl']; excess = M['ovl'] - A['ovl']
print(f"\n  => of the model's {M['ovl']:.2f} overlap, {faithful:.2f} is FAITHFUL (ANES is genuinely "
      f"this overlapped in 1996) and {excess:+.2f} is EXCESS.")
axis = "ECON" if abs(M['eg']-A['eg']) > abs(M['cg']-A['cg']) else "CULTURAL"
print(f"  => the sep shortfall is mostly on the {axis} axis "
      f"(econ {M['eg']-A['eg']:+.3f} vs cult {M['cg']-A['cg']:+.3f}).")

# ---- figure: overlaid density contours, model vs ANES ----
fig, axes = plt.subplots(1, 2, figsize=(12, 6), sharex=True, sharey=True)
for ax, R in zip(axes, (A, M)):
    ax.contour(GRID, GRID, R["fD"], levels=5, colors="#1f3565", linewidths=1.1)
    ax.contour(GRID, GRID, R["fR"], levels=5, colors="#8b2530", linewidths=1.1)
    ax.contourf(GRID, GRID, np.minimum(R["fD"], R["fR"]), levels=6, cmap="Greys", alpha=0.5)
    ax.scatter(*R["mD"], c="#1f3565", s=60, edgecolor="black", zorder=6)
    ax.scatter(*R["mR"], c="#8b2530", s=60, edgecolor="black", zorder=6)
    ax.axhline(0, color="k", lw=0.4, alpha=0.3); ax.axvline(0, color="k", lw=0.4, alpha=0.3)
    ax.set_xlim(-1.05, 1.05); ax.set_ylim(-1.05, 1.05); ax.set_aspect("equal")
    ax.set_xlabel("Economic (← lib   cons →)", fontsize=9)
    ax.set_title(f"{R['name']}  —  OVL={R['ovl']:.2f}  sep={R['sep']:.2f}  "
                 f"R-in-LL={R['rll']*100:.0f}%", fontsize=10)
axes[0].set_ylabel("Cultural (← lib   cons →)", fontsize=9)
fig.suptitle("1996 D–R overlap (grey = overlap region): real ANES was already weakly "
             "sorted; the model adds modest EXCESS overlap", fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.96])
p = OUT / "overlap_1996_model_vs_anes.png"; fig.savefig(p, dpi=150); plt.close(fig)
print(f"\nWROTE {p}")
