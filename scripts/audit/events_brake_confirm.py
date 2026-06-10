"""T0.3 confirmation — joint ablation of the named media-brake set.

The per-unit bisection (events_brake_bisection.py) attributed the +0.48
separation overshoot to a REDUNDANT brake: Fox News 1996 (solo restraint
+0.456) and Fairness Doctrine 1987 (solo +0.261) both set
MediaConsumption.strength (0.02 / 0.04) — either alone activates the
inward media tether (outlet anchors sit inward of the party centroids) —
plus a small independent faction-anchor contribution. This script removes /
adds the named set JOINTLY to confirm it accounts for >=80% of the
overshoot, converting the additive residual into a named interaction.

Run:  .venv/Scripts/python.exe scripts/audit/events_brake_confirm.py
Appends a confirmation section to events_brake_bisection.{json,md}.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

import numpy as np

from abm.calibration_parallel import run_seeds_parallel
import events_brake_bisection as B

MEDIA_SET = ("fairness_doctrine_1987", "fox_news_1996")
FULL_SET = MEDIA_SET + ("tea_party_2009", "maga_2015", "bernie_2016", "dsa_2018")


def main():
    work = []
    for name, kind, labels in [
        ("loeo_media_set", "full_minus", MEDIA_SET),
        ("aoeb_media_set", "decade_plus", MEDIA_SET),
        ("loeo_media_plus_factions", "full_minus", FULL_SET),
        ("aoeb_media_plus_factions", "decade_plus", FULL_SET),
    ]:
        for s in B.SEEDS:
            work.append((name, s, kind, labels, False))
    print(f"running {len(work)} confirmation arcs...")
    flat = run_seeds_parallel(B.bisect_worker, work)

    by_cfg = {}
    for r in flat:
        by_cfg.setdefault(r["config"], []).append(r)

    with open(B.OUT_JSON, encoding="utf-8") as f:
        out = json.load(f)
    O = out["overshoot_sep"]
    sep_full = out["ref_full_sep_mean"]
    sep_dec = out["ref_decade_sep_mean"]

    conf = {}
    for cfg, runs in by_cfg.items():
        seps = np.array([r["final"]["party_sep"] for r in runs])
        if cfg.startswith("loeo"):
            d = seps.mean() - sep_full          # joint marginal brake
            share = d / O
        else:
            d = sep_dec - seps.mean()           # joint solo restraint
            share = d / O
        sign_stab = float(np.mean(
            np.sign(seps - (sep_full if cfg.startswith("loeo") else sep_dec))
            == np.sign(seps.mean() - (sep_full if cfg.startswith("loeo") else sep_dec))))
        conf[cfg] = {"dsep_mean": float(d), "dsep_sd": float(seps.std()),
                     "share_of_overshoot": float(share),
                     "sign_stability": sign_stab}
        print(f"{cfg:28s} dsep={d:+.3f} ±{seps.std():.3f}  share={share:+.0%}")

    named_share = conf["loeo_media_plus_factions"]["share_of_overshoot"]
    gate = named_share >= 0.80 and all(
        v["sign_stability"] >= 7 / 8 for v in conf.values())
    out["confirmation"] = {
        "named_set": list(FULL_SET),
        "results": conf,
        "named_share_joint": named_share,
        "GATE_PASS_named_interaction": bool(gate),
    }
    with open(B.OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    md = open(B.OUT_MD, encoding="utf-8").read()
    md += (
        "\n\n## Confirmation — joint ablation of the named brake set\n\n"
        "The additive shortfall is a **named redundancy**: Fairness Doctrine "
        "1987 and Fox News 1996 both set `MediaConsumption.strength` (0.02 / "
        "0.04) — either alone activates the inward media tether (outlet "
        "anchors sit inward of the party centroids; the documented X3-"
        "dependence artifact), so each is nearly inert *marginally* while "
        "braking strongly *solo*. Joint removal:\n\n"
        "| joint set | LOEO Δsep | share of O | AOEB restraint | share |\n"
        "|---|---|---|---|---|\n"
        f"| media events (FD'87 + Fox'96) | "
        f"{conf['loeo_media_set']['dsep_mean']:+.3f} | "
        f"{conf['loeo_media_set']['share_of_overshoot']:+.0%} | "
        f"{conf['aoeb_media_set']['dsep_mean']:+.3f} | "
        f"{conf['aoeb_media_set']['share_of_overshoot']:+.0%} |\n"
        f"| media events + factions | "
        f"{conf['loeo_media_plus_factions']['dsep_mean']:+.3f} | "
        f"{conf['loeo_media_plus_factions']['share_of_overshoot']:+.0%} | "
        f"{conf['aoeb_media_plus_factions']['dsep_mean']:+.3f} | "
        f"{conf['aoeb_media_plus_factions']['share_of_overshoot']:+.0%} |\n\n"
        f"**Named-interaction gate (>=80% jointly attributed, signs stable): "
        f"{'PASS' if gate else 'FAIL'}** "
        f"(joint named share = {named_share:.0%}).\n"
    )
    with open(B.OUT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"\nnamed joint share = {named_share:.0%}  ->  "
          f"{'GATE PASS' if gate else 'GATE FAIL — STOP per spec'}")
    print("updated", B.OUT_JSON, "and", B.OUT_MD)


if __name__ == "__main__":
    main()
