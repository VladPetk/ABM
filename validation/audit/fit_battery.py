"""INDEPENDENT peer-review fit battery. Does NOT use the author's model_export.py.

Reads validation/run_canonical.json (verified canonical fingerprint 6c5bdb21) and
compares MODEL vs REAL ANES per axis (econ/cult), affect, and distributional shape.

Real targets:
  - centroid gaps + wasserstein from data/phase9_empirical/derived/polarization_series.csv
  - per-issue party means from anes_item_means_by_year.json (build raw centroid gaps)
  - affect from affect_bands.json (out-party, neutral-centered)
"""
import json, csv
from pathlib import Path
import numpy as np

ROOT = Path("D:/MyApps/ABM")
RUN = json.load(open(ROOT / "validation/run_canonical.json"))
DERIVED = ROOT / "data/phase9_empirical/derived"

TPY = RUN["ticks_per_year"]; Y0 = RUN["tick_0_year"]; NT = RUN["n_ticks"]

def yr_to_tick(yr):
    return int(round((yr - Y0) * TPY))

def model_tick(t):
    tk = RUN["ticks"][t]
    return np.array(tk["positions"]), np.array(tk["party"])

# sanity: last tick fingerprint
pos, party = model_tick(135)
m = (party == 0) | (party == 1)
print("=== SANITY (vs fingerprint econ-0.049964 cult-0.047441 sep1.065354) ===")
print(f"  econ_com@135={pos[m,0].mean():.6f}  cult_com@135={pos[m,1].mean():.6f}  "
      f"sep@135={np.hypot(*(pos[party==1].mean(0)-pos[party==0].mean(0))):.6f}")

def model_axis_gaps(yr):
    """RAW centroid gap per axis (R mean - D mean), the natural analog of the
    per-issue means table. Also Wasserstein-1 per axis to match the CSV metric."""
    t = yr_to_tick(yr)
    if t >= NT: return None
    pos, party = model_tick(t)
    D = pos[party == 0]; R = pos[party == 1]
    if len(D) < 3 or len(R) < 3: return None
    def w1(a, b):  # 1D wasserstein
        a = np.sort(a); b = np.sort(b)
        q = np.linspace(0, 1, 200)
        return float(np.mean(np.abs(np.quantile(a, q) - np.quantile(b, q))))
    return {
        "econ_gap_raw": float(R[:,0].mean() - D[:,0].mean()),
        "cult_gap_raw": float(R[:,1].mean() - D[:,1].mean()),
        "econ_w1": w1(D[:,0], R[:,0]),
        "cult_w1": w1(D[:,1], R[:,1]),
        "econ_com": float(pos[(party==0)|(party==1),0].mean()),
        "cult_com": float(pos[(party==0)|(party==1),1].mean()),
        "D_econ": float(D[:,0].mean()), "R_econ": float(R[:,0].mean()),
        "D_cult": float(D[:,1].mean()), "R_cult": float(R[:,1].mean()),
        "D_econ_sd": float(D[:,0].std()), "R_econ_sd": float(R[:,0].std()),
        "D_cult_sd": float(D[:,1].std()), "R_cult_sd": float(R[:,1].std()),
        "all_econ_sd": float(pos[m,0].std()), "all_cult_sd": float(pos[m,1].std()),
    }

# ---- REAL: per-issue raw centroid gaps from anes_item_means ----
items = json.load(open(DERIVED / "anes_item_means_by_year.json"))
ITEM_BLOCK = {k: v["block"] for k, v in items["_meta"]["items"].items()}
def real_axis_gaps(yr):
    yr = str(yr)
    if yr not in items["by_year"]: return None
    d = items["by_year"][yr]
    if not d["dem"] or not d["rep"]: return None
    econ_d, econ_r, cult_d, cult_r = [], [], [], []
    for it, block in ITEM_BLOCK.items():
        if it in d["dem"] and it in d["rep"]:
            axis = "econ" if block == "econ" else "cult"  # cultural_moral + racial -> cult
            (econ_d if axis=="econ" else cult_d).append(d["dem"][it]["mean"])
            (econ_r if axis=="econ" else cult_r).append(d["rep"][it]["mean"])
    if not econ_d or not cult_d: return None
    return {
        "econ_gap_raw": np.mean(econ_r) - np.mean(econ_d),
        "cult_gap_raw": np.mean(cult_r) - np.mean(cult_d),
        "D_econ": np.mean(econ_d), "R_econ": np.mean(econ_r),
        "D_cult": np.mean(cult_d), "R_cult": np.mean(cult_r),
        "econ_com": np.mean(econ_d + econ_r), "cult_com": np.mean(cult_d + cult_r),
    }

# ---- REAL: wasserstein per axis from polarization_series.csv ----
real_w = {}
with open(DERIVED / "polarization_series.csv") as f:
    for row in csv.DictReader(f):
        real_w[int(row["year"])] = {
            "econ_w1": float(row["wasserstein_econ"]),
            "cult_w1": float(row["wasserstein_cult"]),
            "ovl_2d": float(row["ovl_2d"]),
            "dip_econ": float(row["dip_econ"]), "dip_econ_p": float(row["dip_econ_pval"]),
            "dip_cult": float(row["dip_cult"]), "dip_cult_p": float(row["dip_cult_pval"]),
        }

YEARS = list(range(1986, 2025, 2))
print("\n=== PER-AXIS RAW CENTROID GAP (R-D): model vs real (per-issue means) ===")
print(f"{'yr':>4} | {'ec_mdl':>7} {'ec_real':>7} {'ec_err':>7} | {'cu_mdl':>7} {'cu_real':>7} {'cu_err':>7} | ratio cu/ec mdl real")
rows = {}
for yr in YEARS:
    mg = model_axis_gaps(yr); rg = real_axis_gaps(yr)
    if mg is None or rg is None: continue
    rows[yr] = (mg, rg)
    rce = mg["cult_gap_raw"]/mg["econ_gap_raw"] if mg["econ_gap_raw"] else 0
    rcr = rg["cult_gap_raw"]/rg["econ_gap_raw"] if rg["econ_gap_raw"] else 0
    print(f"{yr:>4} | {mg['econ_gap_raw']:7.3f} {rg['econ_gap_raw']:7.3f} {mg['econ_gap_raw']-rg['econ_gap_raw']:7.3f} | "
          f"{mg['cult_gap_raw']:7.3f} {rg['cult_gap_raw']:7.3f} {mg['cult_gap_raw']-rg['cult_gap_raw']:7.3f} | {rce:5.2f} {rcr:5.2f}")

print("\n=== PER-AXIS WASSERSTEIN-1: model vs real (polarization_series.csv) ===")
print(f"{'yr':>4} | {'ec_mdl':>7} {'ec_real':>7} {'ec_err':>7} | {'cu_mdl':>7} {'cu_real':>7} {'cu_err':>7}")
for yr in YEARS:
    mg = model_axis_gaps(yr)
    if mg is None or yr not in real_w: continue
    rw = real_w[yr]
    print(f"{yr:>4} | {mg['econ_w1']:7.3f} {rw['econ_w1']:7.3f} {mg['econ_w1']-rw['econ_w1']:7.3f} | "
          f"{mg['cult_w1']:7.3f} {rw['cult_w1']:7.3f} {mg['cult_w1']-rw['cult_w1']:7.3f}")

# ---- center of mass over time ----
print("\n=== CENTER OF MASS (partisan mean) model vs real per-issue ===")
print(f"{'yr':>4} | {'ecCOM_m':>8} {'ecCOM_r':>8} | {'cuCOM_m':>8} {'cuCOM_r':>8}")
for yr in YEARS:
    mg = model_axis_gaps(yr); rg = real_axis_gaps(yr)
    if mg is None or rg is None: continue
    print(f"{yr:>4} | {mg['econ_com']:8.3f} {rg['econ_com']:8.3f} | {mg['cult_com']:8.3f} {rg['cult_com']:8.3f}")

# ---- DISTRIBUTION: variance + dip ----
print("\n=== DISTRIBUTION: model within-party SD vs real dip (bimodality) ===")
print(f"{'yr':>4} | {'mdl_ec_sd_all':>13} {'mdl_cu_sd_all':>13} | real dip_ec(p) dip_cu(p)")
for yr in YEARS:
    mg = model_axis_gaps(yr)
    if mg is None or yr not in real_w: continue
    rw = real_w[yr]
    print(f"{yr:>4} | {mg['all_econ_sd']:13.3f} {mg['all_cult_sd']:13.3f} | "
          f"ec {rw['dip_econ']:.4f}(p{rw['dip_econ_p']:.3f}) cu {rw['dip_cult']:.4f}(p{rw['dip_cult_p']:.3f})")

# ---- model bimodality: compute Hartigan-ish dip proxy via gaussian-fit + 2d overlap ----
print("\n=== MODEL 2D quadrant occupancy + bimodality proxy ===")
def model_bimod(yr):
    t = yr_to_tick(yr)
    if t >= NT: return None
    pos, party = model_tick(t)
    m2 = (party==0)|(party==1)
    e = pos[m2,0]; c = pos[m2,1]
    # overlap: fraction of D within R's central 80% band per axis (cruder OVL proxy)
    D = pos[party==0]; R = pos[party==1]
    # 2d kde overlap via histogram intersection
    H = 25
    hd,_,_ = np.histogram2d(D[:,0],D[:,1],bins=H,range=[[-1,1],[-1,1]],density=True)
    hr,_,_ = np.histogram2d(R[:,0],R[:,1],bins=H,range=[[-1,1],[-1,1]],density=True)
    cell=(2/H)**2
    ovl = float(np.minimum(hd,hr).sum()*cell)
    return ovl, e, c
print(f"{'yr':>4} | {'mdl_ovl2d':>9} {'real_ovl2d':>10} | err")
for yr in YEARS:
    mb = model_bimod(yr)
    if mb is None or yr not in real_w: continue
    ovl,_,_ = mb
    print(f"{yr:>4} | {ovl:9.3f} {real_w[yr]['ovl_2d']:10.3f} | {ovl-real_w[yr]['ovl_2d']:+.3f}")

# ---- AFFECT ----
print("\n=== AFFECT (out-party warmth, neutral-centered) model vs ANES ===")
bands = json.load(open(DERIVED / "affect_bands.json"))["bands"]
# model affect from gen_run macro (out-party affect mean)
for label, byear in [("1980IC",1987),("1990",1994),("2000",2004),("2010",2014),("2020",2022)]:
    t = yr_to_tick(byear)
    mval = RUN["macro"][t]["affect"]
    b = bands[label]
    print(f"  {label:>7} (~{byear}) | model={mval:+.3f}  ANES_center={b['aff_center']:+.3f}  band={b['band']}  "
          f"{'IN' if b['band'][0]<=mval<=b['band'][1] else 'OUT'}")
print("  (model affect = out-party warmth mean over partisans; note sign/scale convention)")
