"""repack_web_demo.py — build web_demo/cc-data.js from web/data/.

The web_demo reference prototype runs offline from a single bundled
``window.CC_DATA`` object (web_demo/cc-data.js). That bundle is a compact
repack of the full per-run JSON exports under web/data/ (produced by
scripts/publish_web_data.py): the baseline plus one intervention,
decimated to 3-dp positions, with only the fields the prototype consumes.

This script regenerates that bundle so the demo reflects the current
engine. The data contract (v1) is documented in docs/web_data_contract.md.

Usage:

    .venv/Scripts/python.exe scripts/repack_web_demo.py
"""
from __future__ import annotations

import argparse
import json
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

# Contract version stamped on the bundle (web_data_contract.md).
CONTRACT_VERSION = 1

# In-party-warmth empirical overlay (contract v1, §2). This is an
# external ANES feeling-thermometer series, NOT engine-produced — a
# gently-declining in-party-warmth line (~72° in 1980 → ~68° in 2025,
# Iyengar et al. 2019 / ANES cumulative). Mapped linearly across the
# macro tick range and shipped alongside the engine-measured out-party
# series (macro `aff`) so the front-end can draw the honest "scissors".
IN_PARTY_WARMTH_START_DEG = 72.0
IN_PARTY_WARMTH_END_DEG = 68.0

# Faction labels are shipped SPARSELY (contract v1, §6): only at the
# emergence ticks + the endpoints, not every tick. Emergence ticks match
# the ANES-knob handlers in abm/pillars/historical_arc.py (Tea Party 87,
# MAGA 105, Bernie 108, DSA 114). Endpoints (0 and the final tick) are
# added per-run in build_run() since the final tick depends on n_ticks.
FACTION_EMERGENCE_TICKS = (87, 105, 108, 114)


def _round3(xy):
    return [round(float(xy[0]), 3), round(float(xy[1]), 3)]


def _in_party_warmth(t: int, n_ticks: int) -> float:
    """Empirical in-party warmth (degrees) at tick ``t`` — linear ramp
    from IN_PARTY_WARMTH_START_DEG to IN_PARTY_WARMTH_END_DEG across the
    full tick range. External ANES overlay, not engine output (§2)."""
    if n_ticks <= 1:
        return round(IN_PARTY_WARMTH_START_DEG, 2)
    frac = t / (n_ticks - 1)
    deg = IN_PARTY_WARMTH_START_DEG + (
        IN_PARTY_WARMTH_END_DEG - IN_PARTY_WARMTH_START_DEG
    ) * frac
    return round(deg, 2)


def build_run(traj: dict, char_indices: list[int]) -> dict:
    """Convert a full publish_web_data trajectory into the prototype's
    compact baseline Run shape (web_data_contract.md)."""
    ticks = traj["ticks"]
    n_ticks = len(ticks)

    pos = [[_round3(p) for p in td["positions"]] for td in ticks]
    party = [list(td["party"]) for td in ticks]

    # Full-crowd per-agent out-party warmth (contract v1, §1): the
    # engine-measured `aff_out` series for ALL agents, every tick, 3dp.
    # ∈ [-1, 1] (more negative = colder toward the other party).
    affect = [[round(float(v), 3) for v in td["affect"]] for td in ticks]

    macro = []
    for t, m in enumerate(traj["macro"]):
        row = {k: float(m[src]) for k, src in MACRO_KEY_MAP.items()}
        # §5: party centroids on the compass, separate from per-agent pos.
        row["pc0"] = _round3(m["party_centroid_0"])
        row["pc1"] = _round3(m["party_centroid_1"])
        # Mean mega-identity alignment (Mason 2018) — the explicit "stacking"
        # state that drives out-party animus. Engine-measured; rises ~0.21
        # (1980) → ~0.36 (2025) under evidence_regrade, 0.0 when off. The
        # source key matches the target, so it's carried directly (not via
        # MACRO_KEY_MAP). Defaults to 0.0 if a run predates the field.
        row["identity_alignment"] = round(
            float(m.get("identity_alignment", 0.0)), 4
        )
        # §2: empirical in-party-warmth overlay (degrees, NOT engine).
        row["aff_in_empirical"] = _in_party_warmth(t, n_ticks)
        macro.append(row)

    # Sparse crowd-level faction labels (§6): emergence ticks + endpoints.
    sparse_ticks = sorted(
        {0, n_ticks - 1, *(t for t in FACTION_EMERGENCE_TICKS if t < n_ticks)}
    )
    faction: dict[str, list] = {
        str(t): list(ticks[t]["faction"]) for t in sparse_ticks
    }

    # Per-character affect + faction series, keyed by agent index (the
    # deferred character layer; cheap to keep for a later version).
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
        "affect": affect,
        "macro": macro,
        "faction": faction,
        "charAffect": char_affect,
        "charFaction": char_faction,
        # Step 1 (web_demo jumpiness): [tick, agent_id] of every cohort
        # replacement so the viz can ghost-fade on each slot reuse.
        "replacement_events": [
            [int(t), int(a)] for t, a in traj.get("replacement_events", [])
        ],
    }


def build_counterfactuals(data: Path) -> dict:
    """Build the LEAN counterfactual block (contract v1, §3): all 56
    intervention runs (7 interventions × 8 release years), keyed
    ``counterfactuals[<intervention_id>][<release_year>]``.

    Each entry carries only what the branching-trajectory view needs:

      release_tick : int
      sep, aff     : macro series sliced release_tick → end (4dp). The
                     length is ``n_ticks - release_tick``.
      endpos       : the 250-agent endpoint positions (3dp), [250][2].
    """
    out: dict[str, dict] = {}
    iv_dir = data / "interventions"
    for path in sorted(iv_dir.glob("*.json")):
        # "<intervention_id>_at_<year>.json" → (id, year)
        iv_id, _, year = path.stem.rpartition("_at_")
        traj = json.loads(path.read_text(encoding="utf-8"))
        rt = int(traj["release_tick"])
        macro = traj["macro"]
        sep = [round(float(m["party_sep"]), 4) for m in macro[rt:]]
        aff = [round(float(m["affect"]), 4) for m in macro[rt:]]
        endpos = [_round3(p) for p in traj["ticks"][-1]["positions"]]
        out.setdefault(iv_id, {})[year] = {
            "release_tick": rt,
            "sep": sep,
            "aff": aff,
            "endpos": endpos,
        }
    return out


def build_meta(manifest: dict) -> dict:
    return {
        "contract_version": CONTRACT_VERSION,
        "n_agents": manifest["n_agents"],
        "n_ticks": manifest["n_ticks"],
        "tick_0_year": manifest["tick_0_year"],
        "ticks_per_year": manifest["ticks_per_year"],
        "axes": manifest["ideology_axes"],
        "release_years": manifest["release_years"],
        "characters": manifest["characters"],
        # Affect conventions (contract v1, §8). The engine produces only
        # the OUT-party series; the in-party line is an external overlay.
        "affect_scale": {
            "out_party": {
                "fields": ["runs.baseline.affect", "macro.aff",
                           "counterfactuals.*.aff"],
                "range": [-1.0, 1.0],
                "convention": (
                    "engine-measured mean out-party warmth (aff_out); "
                    "more negative = colder toward the other party"
                ),
                "source": "engine",
            },
            "degrees_note": (
                "To render an ANES-style thermometer, map warmth w∈[-1,1] "
                "to degrees via deg = (1 - coldness) * 50 + 12 where "
                "coldness = -w; this is a display mapping, not an engine "
                "metric."
            ),
            "in_party": {
                "field": "macro.aff_in_empirical",
                "units": "ANES feeling-thermometer degrees (0-100)",
                "trajectory": "~72 (1980) -> ~68 (2025)",
                "source": (
                    "EXTERNAL ANES overlay (Iyengar et al. 2019 / ANES "
                    "cumulative) — NOT engine-produced; ships only as a "
                    "data-layer reference line for the honest scissors"
                ),
            },
        },
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
            # Step-1 evidence grade + provenance note (contract v1, §events):
            # HIGH / MED / LOW / CONTESTED / MARKER / OTHER, so the timeline
            # can badge well-evidenced vs contested vs marker events honestly.
            "evidence": e.get("evidence", "OTHER"),
            "evidence_note": e.get("evidence_note"),
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
    args = parser.parse_args()

    data = Path(args.data)
    manifest = json.loads((data / "manifest.json").read_text(encoding="utf-8"))
    events_json = json.loads((data / "events.json").read_text(encoding="utf-8"))
    iv_meta = json.loads(
        (data / "intervention_metadata.json").read_text(encoding="utf-8")
    )
    entities_json = json.loads(
        (data / "entities.json").read_text(encoding="utf-8")
    )

    # Characters → agent indices the runs slice per-character series for.
    char_files: dict[str, dict] = {}
    for char_id in manifest["characters"]:
        p = data / "characters" / f"{char_id}.json"
        char_files[char_id] = json.loads(p.read_text(encoding="utf-8"))
    char_indices = sorted({c["agent_index"] for c in char_files.values()})

    # Baseline run (the only full per-tick run shipped; the old X7
    # single-intervention full-run path is dropped — interventions now
    # ship LEAN via counterfactuals, contract v1 §3).
    baseline_path = data / "baseline" / f"seed_{manifest['canonical_seed']}.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    counterfactuals = build_counterfactuals(data)

    bundle = {
        "contract_version": CONTRACT_VERSION,
        "meta": build_meta(manifest),
        "events": build_events(events_json),
        "interventions": build_interventions(iv_meta),
        "entities": entities_json,
        "runs": {
            "baseline": build_run(baseline, char_indices),
        },
        "counterfactuals": counterfactuals,
        "chars": build_chars(char_files),
    }

    payload = json.dumps(bundle, separators=(",", ":"), ensure_ascii=False)
    out_path = Path(args.out)
    out_path.write_text(
        f"window.CC_DATA = {payload};\n", encoding="utf-8"
    )
    size_mb = out_path.stat().st_size / 1024 / 1024
    n_cf = sum(len(v) for v in counterfactuals.values())
    print(f"wrote {out_path}  ({size_mb:.2f} MB)")
    print(f"  characters: {[ (k, v['agent_index']) for k,v in char_files.items() ]}")
    print(f"  baseline replacements: {len(baseline.get('replacement_events', []))}")
    print(f"  counterfactuals: {n_cf} ({len(counterfactuals)} interventions)")
    print(f"  entities: {len(entities_json['factions_1980'])} founding / "
          f"{len(entities_json['factions_emergent'])} emergent / "
          f"{len(entities_json['outlets'])} outlets")


if __name__ == "__main__":
    main()
