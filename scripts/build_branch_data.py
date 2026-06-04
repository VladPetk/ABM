"""build_branch_data.py — pre-render LAZY per-tick branch files for the web demo.

The interventions page animates the *agent cloud* year-by-year under each
counterfactual. The shipped bundle (cc-data.js) carries the counterfactuals
LEAN — macro series + the 2025 endpoint only — which is enough for the line
chart and the endpoint morph, but NOT enough to play the cloud forward tick by
tick. This script emits the missing per-tick positions as small, lazily-fetched
static files so the base bundle stays ~1 MB and a branch is only downloaded when
the user actually picks that lever + release year.

It is a pure REPACK of the full per-tick exports already on disk under
``web/data/interventions/`` (produced by scripts/publish_web_data.py) — no
engine run is involved.

Output layout (the UNIFIED lazy-run convention — the future sandbox batch drops
its 7^5 runs into the same directory with the same per-file schema, so the
front-end's branch loader serves both)::

    web_demo/cf/<intervention_id>_<release_year>.json   # 56 intervention branches
    web_demo/cf/index.json                              # manifest

Per-file schema (matches the `stitchBranch` adapter in cc-proto-engine.jsx)::

    {
      "release_tick": 45,
      "pos":   [[ [x,y] * 250 ] * (n_ticks - release_tick)],  # 3dp, release->end
      "party": [[ p * 250 ]       * (n_ticks - release_tick)]   # int 0/1/2
    }

``pos[0]`` / ``party[0]`` are the state AT the release tick (the branch point);
index ``k`` maps to absolute tick ``release_tick + k``. Stitching baseline
frames ``0..release_tick-1`` in front of these yields a full-length run the
compass can play from 1980 -> 2025 that visibly diverges at the release year.

Usage::

    .venv/Scripts/python.exe scripts/build_branch_data.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _round3(xy):
    return [round(float(xy[0]), 3), round(float(xy[1]), 3)]


def build_branch(traj: dict) -> dict:
    """Slice one full intervention export into the lean per-tick branch."""
    rt = int(traj["release_tick"])
    branch_ticks = traj["ticks"][rt:]
    pos = [[_round3(p) for p in td["positions"]] for td in branch_ticks]
    party = [[int(p) for p in td["party"]] for td in branch_ticks]
    return {"release_tick": rt, "pos": pos, "party": party}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default=str(_PROJECT_ROOT / "web" / "data"))
    parser.add_argument("--out", default=str(_PROJECT_ROOT / "web_demo" / "cf"))
    args = parser.parse_args()

    data = Path(args.data)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    iv_dir = data / "interventions"
    manifest: dict[str, dict] = {"contract_version": 1, "kind": "branch", "runs": {}}
    total_bytes = 0
    n = 0
    for path in sorted(iv_dir.glob("*.json")):
        # "<intervention_id>_at_<year>.json" → (id, year)
        iv_id, _, year = path.stem.rpartition("_at_")
        traj = json.loads(path.read_text(encoding="utf-8"))
        branch = build_branch(traj)

        key = f"{iv_id}_{year}"
        out_path = out_dir / f"{key}.json"
        payload = json.dumps(branch, separators=(",", ":"), ensure_ascii=False)
        out_path.write_text(payload, encoding="utf-8")

        size = out_path.stat().st_size
        total_bytes += size
        n += 1
        manifest["runs"].setdefault(iv_id, {})[year] = {
            "file": f"{key}.json",
            "release_tick": branch["release_tick"],
            "ticks": len(branch["pos"]),
            "bytes": size,
        }

    (out_dir / "index.json").write_text(
        json.dumps(manifest, separators=(",", ":"), ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"wrote {n} branch files to {out_dir}")
    print(f"  total {total_bytes / 1024 / 1024:.2f} MB "
          f"(avg {total_bytes / max(1, n) / 1024:.0f} KB/file, fetched lazily)")
    print(f"  manifest: {out_dir / 'index.json'}")


if __name__ == "__main__":
    main()
