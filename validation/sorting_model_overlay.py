"""Part C/D + figures: overlay the canonical model (econ-ON, fea5998, seeds 0-2)
on the real ANES sorting curves per axis, classify divergence, and GSS cross-check.
Analysis only."""
import sys, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.anes_preset import ANES_FULL_KWARGS
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to

HERE = Path(__file__).resolve().parent
OUT = HERE / "figures"; OUT.mkdir(exist_ok=True)
real = {int(y): v for y, v in json.load(open(HERE / "real_sorting_curves.json")).items()}
YEARS = sorted(real)
TPY = 3.0


def model_curves(seed):
    kw = dict(ANES_FULL_KWARGS)
    eng = build_engine(seed=seed, **kw)
    sched = build_schedule(
        factional_seeding=kw.get("factional_seeding", False),
        faction_anchor_events=kw.get("faction_anchor_events", True),
        evidence_regrade=kw.get("evidence_regrade", False),
        exogenous_shocks=kw.get("exogenous_shocks", False))
    out = {}
    for t in range(1, 136):
        run_to(eng, sched, t)
        yr = int(round(1980 + t / TPY))
        if yr in YEARS and yr not in out:
            pos = np.array([a.state.ideology for a in eng.agents])
            party = np.array([a.state.attrs.get("party") for a in eng.agents])
            D, R = pos[party == 0], pos[party == 1]
            eg = float(R[:, 0].mean() - D[:, 0].mean())
            cg = float(R[:, 1].mean() - D[:, 1].mean())
            out[yr] = dict(econ_gap=eg, cult_gap=cg, sep=float(np.hypot(eg, cg)))
    return out


SEEDS = [0, 1, 2]
mc = {s: model_curves(s) for s in SEEDS}


def mstat(yr, key):
    vals = [mc[s][yr][key] for s in SEEDS]
    return float(np.mean(vals)), float(np.std(vals))


print("=" * 86)
print("PART C — MODEL (econ-ON canonical, seeds 0-2) vs REAL, per axis. div = model - real")
print("=" * 86)
for key, lab in [("econ_gap", "ECON GAP"), ("cult_gap", "CULT GAP"), ("sep", "SEP 2D")]:
    print(f"\n--- {lab} ---")
    print(f"{'yr':>5} {'real':>7} {'±se':>5} {'model':>7} {'±sd':>5} {'div':>7}")
    for yr in YEARS:
        rv = real[yr][key]; se = real[yr].get(key.split('_')[0] + "_se", real[yr].get("sep_se", 0))
        mm, ms = mstat(yr, key)
        print(f"{yr:>5} {rv:>7.3f} {se:>5.3f} {mm:>7.3f} {ms:>5.3f} {mm-rv:>+7.3f}")

# divergence summary per axis (mean |div| early/mid/late)
def windowed(key):
    res = {}
    for lab, lo, hi in [("early 86-92", 1986, 1992), ("mid 94-04", 1994, 2004),
                        ("late 08-24", 2008, 2024)]:
        ys = [y for y in YEARS if lo <= y <= hi]
        res[lab] = float(np.mean([mstat(y, key)[0] - real[y][key] for y in ys]))
    return res

print("\n=== divergence by window (model - real, mean) ===")
for key, lab in [("econ_gap", "ECON"), ("cult_gap", "CULT"), ("sep", "SEP")]:
    w = windowed(key)
    print(f"  {lab:>4}: early {w['early 86-92']:+.3f} | mid {w['mid 94-04']:+.3f} | late {w['late 08-24']:+.3f}")

# ---------------- GSS cross-check (shape robustness) ----------------
print("\n" + "=" * 86)
print("PART D — GSS cross-check (raw): partisan ECON + CULT gap shapes (normalized)")
print("=" * 86)
try:
    import pandas as pd
    DTA = Path(__file__).resolve().parent.parent / "data/gss_raw/gss7224_r3.dta"
    ECON = {"helppoor": +1, "eqwlth": +1}
    CULT = {"homosex": -1, "premarsx": -1, "abany": +1, "fefam": -1}
    cols = ["year", "partyid", "wtssall"] + list(ECON) + list(CULT)
    df = pd.read_stata(DTA, columns=cols, convert_categoricals=False)
    df["w"] = pd.to_numeric(df["wtssall"], errors="coerce").fillna(0.0)
    pid = pd.to_numeric(df["partyid"], errors="coerce")
    df["dem"] = pid <= 2          # strong/weak Dem
    df["rep"] = (pid >= 4) & (pid <= 6)

    def zindex(items):
        zs = []
        for it, s in items.items():
            v = pd.to_numeric(df[it], errors="coerce").where(lambda x: (x >= 0) & (x < 90))
            zs.append(s * (v - v.mean()) / v.std())
        return np.nanmean(np.vstack([z.values for z in zs]), axis=0)
    df["econR"] = zindex(ECON); df["cultT"] = zindex(CULT)
    years = sorted(int(y) for y in df["year"].dropna().unique() if 1985 <= int(y) <= 2024)

    def wgap(sub, col):
        D = sub[sub["dem"]]; R = sub[sub["rep"]]
        mD = D[col].notna() & (D["w"] > 0); mR = R[col].notna() & (R["w"] > 0)
        if mD.sum() < 30 or mR.sum() < 30:
            return np.nan
        return float(np.average(R.loc[mR, col], weights=R.loc[mR, "w"])
                     - np.average(D.loc[mD, col], weights=D.loc[mD, "w"]))
    print(f"{'yr':>5} {'GSS_econ_gap(z)':>16} {'GSS_cult_gap(z)':>16}")
    gss = {}
    for y in years:
        sub = df[df["year"] == y]
        eg = wgap(sub, "econR"); cg = wgap(sub, "cultT")
        gss[y] = (eg, cg)
        if not (np.isnan(eg) and np.isnan(cg)):
            print(f"{y:>5} {eg:>16.3f} {cg:>16.3f}")
    # steepest-sort comparison: when does each GSS gap rise fastest?
    ge = [(y, gss[y][0]) for y in years if not np.isnan(gss[y][0])]
    gc = [(y, gss[y][1]) for y in years if not np.isnan(gss[y][1])]
    def steep(series):
        ys = np.array([v for _, v in series]); xx = np.array([y for y, _ in series])
        d = np.diff(ys) / np.diff(xx)
        return int(xx[np.argmax(d)])
    print(f"\nGSS steepest-sort: econ≈{steep(ge)}  cult≈{steep(gc)}  "
          f"(ANES: econ≈2008 cult≈2024) — shape robust if same ordering")
    json.dump({str(y): gss[y] for y in years}, open(HERE / "gss_sorting_gaps.json", "w"))
except Exception as e:
    print("GSS cross-check skipped:", e)

# ---------------- FIGURES ----------------
EVENTS = {1994: "Gingrich /\nRep. Rev.", 2001: "9/11", 2008: "Fin. crisis",
          2010: "Tea Party", 2016: "Trump"}


def annotate_events(ax, ymax):
    for yr, lab in EVENTS.items():
        ax.axvline(yr, color="0.6", lw=0.8, ls=":", alpha=0.7)
        ax.text(yr, ymax * 0.98, lab, rotation=90, va="top", ha="right",
                fontsize=7, color="0.4")


# Figure 1: real curves with SE bands + steepest-sort + events
fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharex=True)
specs = [("econ_gap", "econ_se", "Economic gap (R−D)", "#1b7837", 2008),
         ("cult_gap", "cult_se", "Cultural gap (R−D)", "#762a83", 2024),
         ("sep", "sep_se", "Overall separation (2D)", "#2166ac", 2013)]
for ax, (key, sek, title, col, steep) in zip(axes, specs):
    ys = np.array([real[y][key] for y in YEARS])
    se = np.array([real[y][sek] for y in YEARS])
    ax.fill_between(YEARS, ys - 2 * se, ys + 2 * se, color=col, alpha=0.18)
    ax.plot(YEARS, ys, "-o", color=col, lw=2, ms=4, label="ANES (real)")
    ax.axvline(steep, color=col, lw=1.0, ls="--", alpha=0.5)
    ax.text(steep, ax.get_ylim()[1] * 0.05, f"steepest≈{steep}", rotation=90,
            fontsize=7, color=col, va="bottom")
    annotate_events(ax, max(ys) * 1.05)
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("year"); ax.grid(alpha=0.25)
axes[0].set_ylabel("partisan gap (compass units)")
fig.suptitle("Real sorting curves from raw ANES (1986–2024, ±2 SE) — econ sorts "
             "earlier, cultural is back-loaded", fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.95])
p1 = OUT / "real_sorting_curves.png"; fig.savefig(p1, dpi=150); plt.close(fig)

# Figure 2: model vs real per axis
fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharex=True)
for ax, (key, sek, title, col, _s) in zip(axes, specs):
    ys = np.array([real[y][key] for y in YEARS]); se = np.array([real[y][sek] for y in YEARS])
    mm = np.array([mstat(y, key)[0] for y in YEARS]); msd = np.array([mstat(y, key)[1] for y in YEARS])
    ax.fill_between(YEARS, ys - 2 * se, ys + 2 * se, color="0.5", alpha=0.18)
    ax.plot(YEARS, ys, "-o", color="black", lw=2, ms=4, label="ANES (real)")
    ax.fill_between(YEARS, mm - msd, mm + msd, color=col, alpha=0.2)
    ax.plot(YEARS, mm, "-s", color=col, lw=2, ms=4, label="model (seeds 0–2)")
    ax.fill_between(YEARS, ys, mm, where=(mm < ys), color="red", alpha=0.10)
    annotate_events(ax, max(ys.max(), mm.max()) * 1.05)
    ax.set_title(title, fontsize=11); ax.set_xlabel("year"); ax.grid(alpha=0.25)
    ax.legend(fontsize=8, loc="upper left")
axes[0].set_ylabel("partisan gap (compass units)")
fig.suptitle("Model (econ-ON canonical, fea5998) vs real sorting — divergence shaded "
             "red where model under-separates", fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.95])
p2 = OUT / "model_vs_real_sorting.png"; fig.savefig(p2, dpi=150); plt.close(fig)
print("\nWROTE", p1)
print("WROTE", p2)
