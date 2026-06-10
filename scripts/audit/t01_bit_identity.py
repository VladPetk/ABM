"""T0.1 bit-identity probe (MHV spec S0/T0.1).

Runs the canonical shipped config (ANES_FULL_KWARGS, seed 0, full 0..135
arc) and hashes the full per-tick macro series at full float repr. Run once
BEFORE the K-retirement/sigma_pc-fold change and once AFTER; the digests
must match bit-for-bit ("K is provably inert" — if any bit moves, STOP:
the dead-code diagnosis was wrong).

Usage:
  .venv/Scripts/python.exe scripts/audit/t01_bit_identity.py before
  .venv/Scripts/python.exe scripts/audit/t01_bit_identity.py after
Writes docs/internal/audit/t01_hash_<tag>.json and prints the digest. With tag
'after', also compares against the 'before' file and exits 1 on mismatch.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
os.environ.setdefault("OMP_NUM_THREADS", "1")

from scripts.audit.audit_lib import run_arc  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(ROOT, "docs", "internal", "audit")


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "before"
    res = run_arc(seed=0, capture="series")
    # canonical serialization: sorted keys, full repr floats
    blob = json.dumps(res["series"], sort_keys=True, default=repr)
    digest = hashlib.sha256(blob.encode()).hexdigest()
    out = {"tag": tag, "seed": 0, "n_ticks": len(res["series"]),
           "sha256": digest}
    path = os.path.join(OUT_DIR, f"t01_hash_{tag}.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"[{tag}] sha256={digest}")
    print("wrote", path)
    if tag == "after":
        with open(os.path.join(OUT_DIR, "t01_hash_before.json")) as f:
            before = json.load(f)
        if before["sha256"] != digest:
            print("BIT-IDENTITY FAIL — STOP (dead-code diagnosis wrong)")
            sys.exit(1)
        print("BIT-IDENTITY PASS — identical to pre-change run")


if __name__ == "__main__":
    main()
