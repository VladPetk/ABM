"""Diagnostic: what drives the model's cultural center? Trace per-tick the MASS
cultural center vs the ELITE-centroid midpoint (common mode of the two party
elites). If the elite midpoint drifts progressive, the symmetric loop is actually
asymmetric and is dragging the whole cloud down-left.
"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.publish_web_data import run_trajectory

tr = run_trajectory(seed=0, capture_agents=True)
print(f"{'tick':>4} {'year':>6} {'mass_cult':>10} {'mass_econ':>10} "
      f"{'elite_mid_cult':>15} {'elite_mid_econ':>15} {'eliteD_cult':>11} {'eliteR_cult':>11}")
for t in range(0, 136, 6):
    pos = np.array(tr["ticks"][t]["positions"]); party = np.array(tr["ticks"][t]["party"])
    m = (party == 0) | (party == 1)
    mac = tr["macro"][t]
    eD = mac["party_centroid_0"]; eR = mac["party_centroid_1"]
    emid_c = (eD[1] + eR[1]) / 2; emid_e = (eD[0] + eR[0]) / 2
    print(f"{t:>4} {1980+t/3:>6.1f} {pos[m,1].mean():>10.3f} {pos[m,0].mean():>10.3f} "
          f"{emid_c:>15.3f} {emid_e:>15.3f} {eD[1]:>11.3f} {eR[1]:>11.3f}")
