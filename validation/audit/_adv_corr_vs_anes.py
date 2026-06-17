"""ADVERSARIAL VERIFICATION (read-only scratch): does the model over-couple the
two compass axes relative to the REAL ANES individual-level data?

Compares the model's partisan econ-cult correlation (validation/run_canonical.json,
fingerprint 6c5bdb21, verified to match the shipped engine) against the real ANES
individual-level partisan-pooled correlation from the project's OWN raw respondent
file data/phase9_empirical/derived/respondent_coordinates.csv.

Conclusion: the model matches ANES (MAE ~0.048, endpoint ~0.78 both). The claimed
'ANES ~0.5-0.6' reference in docs is the mid-period / a different statistic
(Treier-Hillygus 2009 slope), not the 2020s endpoint correlation, which is ~0.77.
"""
import csv, json
import numpy as np
from collections import defaultdict

real = defaultdict(lambda: {"econ": [], "cult": []})
with open("data/phase9_empirical/derived/respondent_coordinates.csv") as f:
    for row in csv.DictReader(f):
        if row["party"] not in ("D", "R"):
            continue
        try:
            e = float(row["econ"]); c = float(row["cult"])
        except ValueError:
            continue
        if np.isnan(e) or np.isnan(c):
            continue
        real[int(row["year"])]["econ"].append(e)
        real[int(row["year"])]["cult"].append(c)


def rc(yr):
    if yr not in real:
        return None
    e = np.array(real[yr]["econ"]); c = np.array(real[yr]["cult"])
    if len(e) < 10:
        return None
    return float(np.corrcoef(e, c)[0, 1])


d = json.load(open("validation/run_canonical.json"))
TPY = d["ticks_per_year"]; Y0 = d["tick_0_year"]; NT = d["n_ticks"]


def mc(yr):
    t = int(round((yr - Y0) * TPY))
    if t >= NT:
        return None
    p = np.array(d["ticks"][t]["positions"]); pa = np.array(d["ticks"][t]["party"])
    m = (pa == 0) | (pa == 1)
    return float(np.corrcoef(p[m, 0], p[m, 1])[0, 1])


print("%5s | %8s %8s %8s" % ("year", "model", "realANES", "err"))
errs = []
for yr in sorted(real):
    m = mc(yr); r = rc(yr)
    if m is None or r is None:
        continue
    errs.append(m - r)
    print("%5d | %+8.3f %+8.3f %+8.3f" % (yr, m, r, m - r))
print("\nMAE %.3f  mean signed (model-real) %+.3f" % (np.mean(np.abs(errs)), np.mean(errs)))
