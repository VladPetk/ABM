"""Diagnostic: run the realism battery on the econ-OFF (cultural-only) config to
isolate whether the econ flip or the un-re-blessed cultural fix moved the tally."""
import os, sys
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scripts.audit.realism_battery as rb

# Point the battery at the pre-econ canonical (cultural common-mode only).
from scripts.anes_preset import ANES_FULL_COMMONMODE_KWARGS
rb.ANES_FULL_KWARGS = dict(ANES_FULL_COMMONMODE_KWARGS)

sys.argv = ["realism_battery", "--seeds", "9",
            "--out", str(Path(__file__).resolve().parent / "realism_econ_off.json")]
rb.main()
