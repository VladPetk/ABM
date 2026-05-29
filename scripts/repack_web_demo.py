"""repack_web_demo.py — build web_demo/cc-data.js from web/data/.

The web_demo reference prototype runs offline from a single bundled
``window.CC_DATA`` object (web_demo/cc-data.js). That bundle is a compact
repack of the full per-run JSON exports under web/data/ (produced by
scripts/publish_web_data.py): the baseline plus one intervention,
decimated to 3-dp positions, with only the fields the prototype consumes.

This script regenerates that bundle so the demo reflects the current
engine. The data contract is documented in web_demo/HANDOFF.md §3.

Usage:

    .venv/Scripts/python.exe scripts/repack_web_demo.py
    # custom intervention to bundle (default X7 @ 2000):
    .venv/Scripts/python.exe scripts/repack_web_demo.py \\
        --intervention X7_perception_correction --intervention-year 2000
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Map web/data macro field names → the compact keys the prototype reads.
MACRO_KEY_MAP = {
    "sep": "party_sep",
    "aff": "affect",
    "varr": "variance",
    "mod": "modularity",
    "xc": "xc_fraction",
}


def _round3(xy):
    return [round(float(xy[0]), 3), round(float(xy[1]), 3)]


def build_run(traj: dict, char_indices: list[int]) -> dict:
    """Convert a full publish_web_data trajectory into the prototype's
    compact Run shape (HANDOFF.md §3)."""
    ticks = traj["ticks"]
    n_ticks = len(ticks)

    pos = [[_round3(p) for p in td["positions"]] for td in ticks]
    party = [list(td["party"]) for td in ticks]

    macro = []
    for m in traj["macro"]:
        macro.append({k: float(m[src]) for k, src in MACRO_KEY_MAP.items()})

    # Network snapshots → [[src, tgt, cross]] with cross-party computed
    # from the parties at that snapshot tick (the raw export stores an
    # involuntary/cooperative bitmask, not a cross-party flag).
    net: dict[str, list] = {}
    for tick_str, snap in traj.get("network_snapshots", {}).items():
        t = int(tick_str)
        party_t = ticks[t]["party"] if t < n_ticks else ticks[-1]["party"]
        edges = []
        for e in snap["edges"]:
            i, j = int(e[0]), int(e[1])
            cross = 1 if party_t[i] != party_t[j] else 0
            edges.append([i, j, cross])
        net[tick_str] = edges

    # Per-character affect + faction series, keyed by agent index.
    char_affect: dict[str, list] = {}
    char_faction: dict[str, list] = {}
    for idx in char_indices:
        char_affect[str(idx)] = [
            round(float(td["affect"][idx]), 4) for td in ticks
        ]
        char_faction[str(idx)] = [td["faction"][idx] for td in ticks]

    return {
        "release_tick": traj.get("release_tick"),
        "pos": pos,
        "party": party,
        "macro": macro,
        "net": net,
        "charAffect": char_affect,
        "charFaction": char_faction,
        # Step 1 (web_demo jumpiness): [tick, agent_id] of every cohort
        # replacement so the viz can ghost-fade on each slot reuse.
        "replacement_events": [
            [int(t), int(a)] for t, a in traj.get("replacement_events", [])
        ],
    }


def build_meta(manifest: dict) -> dict:
    return {
        "n_agents": manifest["n_agents"],
        "n_ticks": manifest["n_ticks"],
        "tick_0_year": manifest["tick_0_year"],
        "ticks_per_year": manifest["ticks_per_year"],
        "axes": manifest["ideology_axes"],
        "release_years": manifest["release_years"],
        "characters": manifest["characters"],
    }


def build_events(events_json: dict) -> list:
    out = []
    for e in events_json["events"]:
        out.append({
            "tick": e["tick"],
            "label": e["label"],
            "description": e["description"],
            "actual_date": e.get("actual_date"),
            "kind": e.get("kind", "other"),
        })
    return out


def build_interventions(iv_meta: dict) -> dict:
    out = {}
    for iv_id, iv in iv_meta["interventions"].items():
        out[iv_id] = {
            "id": iv["id"],
            "label": iv["label"],
            "color": iv.get("color", "#888888"),
            "effect_buckets": iv.get("effect_buckets", {}),
            "provenance_tags": iv.get("provenance_tags", {}),
            "expected_naive_effect": iv.get("expected_naive_effect"),
        }
    return out


def build_chars(char_files: dict[str, dict]) -> dict:
    out = {}
    for char_id, c in char_files.items():
        demo = c.get("demographics", {})
        beats = [
            {"tick": b["tick"], "prose": b.get("text", b.get("prose", ""))}
            for b in c.get("narrative_beats", [])
        ]
        out[char_id] = {
            "name": c["name"],
            "agent_index": c["agent_index"],
            "job": demo.get("occupation", ""),
            "city": demo.get("city_template", ""),
            "issues": c.get("issues_priority", []),
            "bio": c.get("bio", ""),
            "beats": beats,
        }
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default=str(_PROJECT_ROOT / "web" / "data"))
    parser.add_argument("--out", default=str(_PROJECT_ROOT / "web_demo" / "cc-data.js"))
    parser.add_argument("--intervention", default="X7_perception_correction")
    parser.add_argument("--intervention-year", type=int, default=2000)
    args = parser.parse_args()

    data = Path(args.data)
    manifest = json.loads((data / "manifest.json").read_text(encoding="utf-8"))
    events_json = json.loads((data / "events.json").read_text(encoding="utf-8"))
    iv_meta = json.loads(
        (data / "intervention_metadata.json").read_text(encoding="utf-8")
    )

    # Characters → agent indices the runs slice per-character series for.
    char_files: dict[str, dict] = {}
    for char_id in manifest["characters"]:
        p = data / "characters" / f"{char_id}.json"
        char_files[char_id] = json.loads(p.read_text(encoding="utf-8"))
    char_indices = sorted({c["agent_index"] for c in char_files.values()})

    # Baseline run.
    baseline_path = data / "baseline" / f"seed_{manifest['canonical_seed']}.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    # One intervention run (default X7 @ 2000).
    iv_path = (
        data / "interventions"
        / f"{args.intervention}_at_{args.intervention_year}.json"
    )
    if not iv_path.exists():
        sys.exit(f"intervention run not found: {iv_path}")
    iv_run = json.loads(iv_path.read_text(encoding="utf-8"))

    bundle = {
        "meta": build_meta(manifest),
        "events": build_events(events_json),
        "interventions": build_interventions(iv_meta),
        "runs": {
            "baseline": build_run(baseline, char_indices),
            args.intervention: build_run(iv_run, char_indices),
        },
        "chars": build_chars(char_files),
    }

    payload = json.dumps(bundle, separators=(",", ":"), ensure_ascii=False)
    out_path = Path(args.out)
    out_path.write_text(
        f"window.CC_DATA = {payload};\n", encoding="utf-8"
    )
    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"wrote {out_path}  ({size_mb:.2f} MB)")
    print(f"  characters: {[ (k, v['agent_index']) for k,v in char_files.items() ]}")
    print(f"  baseline replacements: {len(baseline.get('replacement_events', []))}")
    print(f"  bundled intervention: {args.intervention} @ {args.intervention_year}")


if __name__ == "__main__":
    main()
