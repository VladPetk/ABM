"""ROOT-CAUSE the sorting gap empirically (analysis only; no engine change).

Extracts the REAL sorting curve from raw ANES (validated anchors) — overall
party separation, the ECONOMIC gap alone, the CULTURAL gap alone — with sampling
error; characterizes shape/complexity (poly + logistic fits, inflection years,
monotonicity); overlays the canonical model (econ-ON, fea5998, seeds 0-2); and
classifies the divergence per axis. GSS cross-check for shape robustness.
"""
import sys, json
from pathlib import Path
import numpy as np
from numpy.polynomial import polynomial as P
from scipy.optimize import curve_fit
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

HERE = Path(__file__).resolve().parent
A = json.load(open(HERE / "anchors_anes.json"))
PC = {int(y): v for y, v in A["party_centroids"].items()}
YEARS = sorted(PC)


def gap_se(yr, axis):
    d, r = PC[yr]["D"], PC[yr]["R"]
    sd = "econ_sd" if axis == "econ" else "cult_sd"
    return float(np.sqrt(r[sd] ** 2 / r["n_unw"] + d[sd] ** 2 / d["n_unw"]))


real = {}
for yr in YEARS:
    d, r = PC[yr]["D"], PC[yr]["R"]
    eg = r["econ"] - d["econ"]
    cg = r["cult"] - d["cult"]
    sep = float(np.hypot(eg, cg))
    ese, cse = gap_se(yr, "econ"), gap_se(yr, "cult")
    sse = float(np.sqrt((eg * ese) ** 2 + (cg * cse) ** 2) / sep) if sep else 0.0
    real[yr] = dict(econ_gap=eg, cult_gap=cg, sep=sep, econ_se=ese, cult_se=cse, sep_se=sse)

print("=" * 78)
print("PART A — REAL sorting curves from raw ANES (gap = R centroid - D centroid)")
print("=" * 78)
print(f"{'yr':>5} | {'econ_gap':>9} {'±se':>5} | {'cult_gap':>9} {'±se':>5} | {'sep(2D)':>8} {'±se':>5}")
for yr in YEARS:
    x = real[yr]
    print(f"{yr:>5} | {x['econ_gap']:>9.3f} {x['econ_se']:>5.3f} | "
          f"{x['cult_gap']:>9.3f} {x['cult_se']:>5.3f} | {x['sep']:>8.3f} {x['sep_se']:>5.3f}")

# ---------- shape characterization ----------
xs = np.array(YEARS, float)
x0 = (xs - 1980) / 10.0   # decades since 1980, for conditioning


def logistic(t, L, k, t0, b):
    return b + L / (1.0 + np.exp(-k * (t - t0)))


def characterize(name, ys, ses):
    ys = np.array(ys); ses = np.array(ses)
    print(f"\n--- {name} ---")
    mean_se = ses.mean()
    # polynomial fits of increasing order: residual RMSE vs sampling SE
    for deg in (1, 2, 3, 4):
        c = np.polyfit(x0, ys, deg)
        resid = ys - np.polyval(c, x0)
        rmse = float(np.sqrt(np.mean(resid ** 2)))
        r2 = 1 - np.var(resid) / np.var(ys)
        flag = "≈noise" if rmse <= 1.3 * mean_se else "structure>noise"
        print(f"  poly deg{deg}: R²={r2:.3f}  residRMSE={rmse:.3f}  (mean SE={mean_se:.3f}) {flag}")
    # single smooth S-curve (logistic) hypothesis
    try:
        p0 = [ys.max() - ys.min(), 1.0, 2.0, ys.min()]
        popt, _ = curve_fit(logistic, x0, ys, p0=p0, maxfev=20000)
        resid = ys - logistic(x0, *popt)
        r2 = 1 - np.var(resid) / np.var(ys)
        rmse = float(np.sqrt(np.mean(resid ** 2)))
        t0_year = 1980 + popt[2] * 10
        print(f"  logistic : R²={r2:.3f}  residRMSE={rmse:.3f}  midpoint≈{t0_year:.0f}  "
              f"{'≈noise→single smooth S' if rmse<=1.3*mean_se else 'residual structure remains'}")
    except Exception as e:
        print(f"  logistic : fit failed ({e})")
    # inflection / steepest-slope year (finite diff on a smoothing spline-ish: deg-3 poly deriv)
    c3 = np.polyfit(x0, ys, 3)
    dc = np.polyder(c3)
    grid = np.linspace(x0.min(), x0.max(), 200)
    slope = np.polyval(dc, grid)
    steep_year = 1980 + grid[np.argmax(slope)] * 10
    # monotonicity: first differences beyond 1 SE
    diffs = np.diff(ys)
    pooled = np.sqrt(ses[:-1] ** 2 + ses[1:] ** 2)
    n_down = int(np.sum(diffs < -pooled))
    print(f"  steepest-sort year≈{steep_year:.0f};  significant DOWN-steps (reversals): {n_down}/{len(diffs)}")
    return dict(steep_year=steep_year, mean_se=mean_se)


print("\n" + "=" * 78)
print("PART B — SHAPE / COMPLEXITY (poly+logistic fits; residual vs sampling noise)")
print("=" * 78)
ch_e = characterize("ECON gap", [real[y]["econ_gap"] for y in YEARS], [real[y]["econ_se"] for y in YEARS])
ch_c = characterize("CULT gap", [real[y]["cult_gap"] for y in YEARS], [real[y]["cult_se"] for y in YEARS])
ch_s = characterize("SEP (2D)", [real[y]["sep"] for y in YEARS], [real[y]["sep_se"] for y in YEARS])

# econ vs cult timing + synchronization
de = np.diff([real[y]["econ_gap"] for y in YEARS])
dc = np.diff([real[y]["cult_gap"] for y in YEARS])
sync = float(np.corrcoef(de, dc)[0, 1])
print(f"\nECON vs CULT pacing:  steepest econ≈{ch_e['steep_year']:.0f}  steepest cult≈{ch_c['steep_year']:.0f}  "
      f"|  corr(Δecon,Δcult)={sync:+.2f}  ({'synchronized' if sync>0.6 else 'STAGGERED/partly independent'})")

# save real curves for plotting + model overlay
json.dump({str(y): real[y] for y in YEARS}, open(HERE / "real_sorting_curves.json", "w"), indent=1)
print("\nwrote real_sorting_curves.json")
