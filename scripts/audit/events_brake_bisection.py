"""T0.3 — events-as-a-brake bisection (MHV spec docs/internal/mhv_spec.md S0/T0.3).

The Phase 2 freeze test found that dropping the dated punctuated events
(keeping the smooth decade schedules) makes 2025 party separation OVERSHOOT
1.13 -> 1.61 (+0.48) and warms affect — the event layer is partly a BRAKE.
The obvious explanation (event stubbornness bumps) was falsified (+0.03).
This script attributes the overshoot:

  - decomposes the shipped schedule into one ScheduledEvent per handler
    (same-tick insertion order preserved; Schedule's sort is stable), with a
    BIT-IDENTITY validation gate against the shipped build_schedule before
    any ablation runs;
  - leave-one-event-out (LOEO): full schedule minus one unit -> the unit's
    marginal brake contribution c_u = sep(loeo_u) - sep(full);
  - add-one-event-back (AOEB): decade-only schedule plus one unit -> the
    unit's solo restraint b_u = sep(decade_only) - sep(aoeb_u);
  - 8 seeds, per-seed signs for stability; reverts are paired with the
    spikes they revert (no orphaned-revert states).

Gate (mhv_spec T0.3): >=80% of the overshoot attributed to named events /
named interactions with seed-stable signs; else STOP — blocks S4's holdout
claim.

Run:  .venv/Scripts/python.exe scripts/audit/events_brake_bisection.py
Writes docs/internal/audit/events_brake_bisection.{json,md}
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
os.environ.setdefault("OMP_NUM_THREADS", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

import numpy as np

import abm.pillars.historical_arc as H
from abm.calibration_parallel import run_seeds_parallel
from abm.pillars.schedule import Schedule, ScheduledEvent, run_to
from abm.pillars.shocks import SHOCK_CATALOGUE, shock_scheduled_events
from scripts.anes_preset import ANES_FULL_KWARGS
from scripts.audit.audit_lib import _macro, END_TICK, DECADE_TICKS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_JSON = os.path.join(ROOT, "docs", "internal", "audit", "events_brake_bisection.json")
OUT_MD = os.path.join(ROOT, "docs", "internal", "audit", "events_brake_bisection.md")

SEEDS = list(range(8))
METRICS = ["party_sep", "affect", "identity_alignment", "constraint",
           "modularity", "within_party_sd", "xc_fraction"]


# --------------------------------------------------------------------------- #
# Decomposed schedule — one ScheduledEvent per handler, in the SAME insertion
# sequence as build_schedule (core list with _combined split inline, then
# gingrich, then factions, then shocks). Schedule sorts stably by tick, so
# same-tick firing order is preserved exactly.
# --------------------------------------------------------------------------- #
def _decomposed_entries():
    e = [
        (21, "fairness_doctrine_1987", H._event_1987_fairness_doctrine),
        (30, "decade_1990", H._decade_boundary_1990),
        (48, "fox_news_1996", H._event_1996_fox_news),
        (60, "decade_2000", H._decade_boundary_2000),
        (84, "sm_ramp_start_2008", H._event_2008_social_media_ramp_start),
        (84, "obama_warmth_2008", H._event_2008_obama_warmth),
        (90, "decade_2010", H._decade_boundary_2010),
        (90, "citizens_united_2010", H._event_2010_citizens_united),
        (90, "sm_ramp_mid_2010", H._event_2010_social_media_ramp_mid),
        (96, "sm_ramp_end_2012", H._event_2012_social_media_ramp_end),
        (108, "trump_election_2016", H._event_2016_trump_election),
        (108, "status_threat_2016", H._event_2016_status_threat),
        (114, "trump_bump_revert_2018", H._event_2018_trump_bump_revert),
        (120, "decade_2020", H._decade_boundary_2020),
        (120, "covid_jan6_2020", H._event_2020_covid_jan6),
        (123, "affect_revert_2021", H._event_2021_affect_revert),
        # appended after the core list in build_schedule (stable sort):
        (42, "gingrich_1994", H._event_1994_gingrich),
        (87, "tea_party_2009", H._event_2009_tea_party),
        (105, "maga_2015", H._event_2015_maga),
        (108, "bernie_2016", H._event_2016_bernie),
        (114, "dsa_2018", H._event_2018_dsa),
    ]
    entries = [ScheduledEvent(t, lab, lab, fn) for t, lab, fn in e]
    entries.extend(shock_scheduled_events(SHOCK_CATALOGUE))  # rally_911_2001, obergefell_2015
    return entries


DECADE_LABELS = {"decade_1990", "decade_2000", "decade_2010", "decade_2020"}

# Ablation units: unit name -> set of decomposed labels removed/added together.
# Reverts are PAIRED with the spikes they revert.
UNITS = {
    "fairness_doctrine_1987": {"fairness_doctrine_1987"},
    "gingrich_1994": {"gingrich_1994"},
    "fox_news_1996": {"fox_news_1996"},
    "social_media_ramp": {"sm_ramp_start_2008", "sm_ramp_mid_2010", "sm_ramp_end_2012"},
    "obama_warmth_2008": {"obama_warmth_2008"},
    "citizens_united_2010": {"citizens_united_2010"},
    "trump_election_2016": {"trump_election_2016", "trump_bump_revert_2018"},
    "status_threat_2016": {"status_threat_2016"},
    "covid_jan6_2020": {"covid_jan6_2020", "affect_revert_2021"},
    "factions": {"tea_party_2009", "maga_2015", "bernie_2016", "dsa_2018"},
    "shock_911": {"rally_911_2001"},
    "shock_obergefell": {"obergefell_2015"},
}


def make_schedule(kind: str, labels: tuple) -> Schedule:
    """kind='full_minus' -> decomposed minus labels;
    kind='decade_plus' -> decade boundaries plus labels."""
    entries = _decomposed_entries()
    labels = set(labels)
    if kind == "full_minus":
        keep = [ev for ev in entries if ev.label not in labels]
    elif kind == "decade_plus":
        keep = [ev for ev in entries if ev.label in (DECADE_LABELS | labels)]
    else:
        raise ValueError(kind)
    return Schedule(keep)


# --------------------------------------------------------------------------- #
# Worker (top-level, picklable under spawn)
# --------------------------------------------------------------------------- #
def bisect_worker(arg):
    """arg = (config_name, seed, kind, labels_tuple, capture_series:bool)."""
    name, seed, kind, labels, capture_series = arg
    eng = H.build_engine(seed=seed, **ANES_FULL_KWARGS)
    sched = make_schedule(kind, labels)
    series = [_macro(eng)]
    for t in range(1, END_TICK + 1):
        run_to(eng, sched, t)
        series.append(_macro(eng))
    out = {"config": name, "seed": seed, "final": series[-1],
           "snaps": {str(t): series[t] for t in DECADE_TICKS.values()}}
    if capture_series:
        out["series"] = series
    return out


def shipped_worker(arg):
    """Reference run on the SHIPPED build_schedule (bit-identity check)."""
    seed, = arg
    eng = H.build_engine(seed=seed, **ANES_FULL_KWARGS)
    sched = H.build_schedule(faction_anchor_events=True, evidence_regrade=True,
                             exogenous_shocks=True)
    series = [_macro(eng)]
    for t in range(1, END_TICK + 1):
        run_to(eng, sched, t)
        series.append(_macro(eng))
    return {"series": series}


def _hash_series(series) -> str:
    return hashlib.sha256(
        json.dumps(series, sort_keys=True, default=repr).encode()).hexdigest()


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def main():
    # ---- validation gate: decomposed == shipped, bit-for-bit (seed 0) ----
    print("bit-identity gate: shipped vs decomposed schedule (seed 0)...")
    shipped = shipped_worker((0,))
    decomp = bisect_worker(("ref_full_check", 0, "full_minus", (), True))
    h1, h2 = _hash_series(shipped["series"]), _hash_series(decomp["series"])
    if h1 != h2:
        print(f"FAIL: shipped {h1[:16]} != decomposed {h2[:16]} — "
              "decomposition changed behavior; STOP.")
        sys.exit(1)
    print(f"PASS: {h1[:16]}... identical. Proceeding to ablations.")

    # ---- ablation batch ----
    configs = [("ref_full", "full_minus", ())]
    configs.append(("ref_decade", "decade_plus", ()))
    for u, labels in UNITS.items():
        configs.append((f"loeo_{u}", "full_minus", tuple(sorted(labels))))
        configs.append((f"aoeb_{u}", "decade_plus", tuple(sorted(labels))))

    work = [(name, s, kind, labels, False)
            for name, kind, labels in configs for s in SEEDS]
    print(f"running {len(work)} arcs ({len(configs)} configs x {len(SEEDS)} seeds)...")
    flat = run_seeds_parallel(bisect_worker, work)

    by_cfg = {}
    for r in flat:
        by_cfg.setdefault(r["config"], []).append(r)

    def finals(cfg, metric):
        return np.array([r["final"][metric] for r in
                         sorted(by_cfg[cfg], key=lambda x: x["seed"])])

    sep_full = finals("ref_full", "party_sep")
    sep_dec = finals("ref_decade", "party_sep")
    aff_full = finals("ref_full", "affect")
    aff_dec = finals("ref_decade", "affect")
    O = float((sep_dec - sep_full).mean())           # the overshoot
    O_aff = float((aff_dec - aff_full).mean())

    rows = []
    for u in UNITS:
        c = finals(f"loeo_{u}", "party_sep") - sep_full      # marginal brake
        b = sep_dec - finals(f"aoeb_{u}", "party_sep")       # solo restraint
        ca = finals(f"loeo_{u}", "affect") - aff_full
        c_m, b_m = float(c.mean()), float(b.mean())
        stab_c = float(np.mean(np.sign(c) == np.sign(c_m))) if abs(c_m) > 1e-9 else None
        stab_b = float(np.mean(np.sign(b) == np.sign(b_m))) if abs(b_m) > 1e-9 else None
        rows.append({
            "unit": u,
            "loeo_dsep_mean": c_m, "loeo_dsep_sd": float(c.std()),
            "loeo_sign_stability": stab_c,
            "aoeb_restraint_mean": b_m, "aoeb_restraint_sd": float(b.std()),
            "aoeb_sign_stability": stab_b,
            "loeo_daffect_mean": float(ca.mean()),
            "share_of_overshoot_loeo": c_m / O if O else None,
            "interaction_gap": c_m - b_m,   # marginal vs solo — large gap = interacts
        })
    rows.sort(key=lambda r: -abs(r["loeo_dsep_mean"]))

    sum_loeo = float(sum(r["loeo_dsep_mean"] for r in rows))
    sum_aoeb = float(sum(r["aoeb_restraint_mean"] for r in rows))
    residual_loeo = O - sum_loeo
    # named-attribution share: additive LOEO sum over the overshoot
    share_named = sum_loeo / O if O else float("nan")

    # major contributors (|c_u| > 5% of O) must be seed-sign-stable >= 7/8
    majors = [r for r in rows if abs(r["loeo_dsep_mean"]) > 0.05 * abs(O)]
    stable = all((r["loeo_sign_stability"] or 0) >= 7 / 8 for r in majors)

    gate_pass = (share_named >= 0.80) and stable
    # If additive LOEO under-attributes, the AOEB direction + interaction
    # gaps name where the rest lives; verdict text handles that case.

    out = {
        "spec": "mhv T0.3 events-as-a-brake bisection",
        "seeds": SEEDS, "end_tick": END_TICK,
        "bit_identity_gate": {"hash": h1, "pass": True},
        "overshoot_sep": O, "overshoot_affect": O_aff,
        "ref_full_sep_mean": float(sep_full.mean()),
        "ref_decade_sep_mean": float(sep_dec.mean()),
        "units": rows,
        "sum_loeo": sum_loeo, "sum_aoeb": sum_aoeb,
        "residual_loeo": residual_loeo,
        "share_named_additive": share_named,
        "majors_sign_stable": stable,
        "GATE_PASS_80pct": bool(gate_pass),
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(out, f, indent=2)
    write_md(out)
    print(f"\novershoot O = {O:+.3f} (affect {O_aff:+.3f})")
    print(f"sum LOEO = {sum_loeo:+.3f} ({share_named:.0%} of O), "
          f"residual (interactions) = {residual_loeo:+.3f}")
    print(f"sum AOEB solo restraints = {sum_aoeb:+.3f}")
    print(f"GATE (>=80% additive, majors sign-stable): "
          f"{'PASS' if gate_pass else 'NOT MET (see interaction analysis)'}")
    print("wrote", OUT_JSON, "and", OUT_MD)


def write_md(out):
    L = []
    A = L.append
    A("# T0.3 — events-as-a-brake bisection\n")
    A("*Generated by `scripts/audit/events_brake_bisection.py` (MHV spec "
      "T0.3). 8 seeds, full shipped config. Decomposed schedule validated "
      "bit-identical to `build_schedule` before ablation "
      f"(sha256 {out['bit_identity_gate']['hash'][:16]}...).*\n")
    A(f"\n## Verdict: {'GATE PASS' if out['GATE_PASS_80pct'] else 'ADDITIVE GATE NOT MET'}\n")
    A(f"- overshoot (decade-only − full): **{out['overshoot_sep']:+.3f}** sep, "
      f"{out['overshoot_affect']:+.3f} affect")
    A(f"- additive LOEO attribution: **{out['sum_loeo']:+.3f}** "
      f"(**{out['share_named_additive']:.0%}** of the overshoot); "
      f"interaction residual {out['residual_loeo']:+.3f}")
    A(f"- sum of AOEB solo restraints: {out['sum_aoeb']:+.3f}")
    A(f"- major contributors sign-stable (>=7/8 seeds): "
      f"{out['majors_sign_stable']}\n")
    A("\n## Per-unit attribution (sorted by |LOEO|)\n")
    A("\n| unit | LOEO Δsep (remove from full) | sign-stab | AOEB restraint "
      "(add to decade-only) | sign-stab | share of O | interaction gap "
      "(LOEO−AOEB) | LOEO Δaffect |")
    A("|---|---|---|---|---|---|---|---|")
    for r in out["units"]:
        A(f"| {r['unit']} | {r['loeo_dsep_mean']:+.3f} ± {r['loeo_dsep_sd']:.3f} "
          f"| {r['loeo_sign_stability'] if r['loeo_sign_stability'] is not None else '—'} "
          f"| {r['aoeb_restraint_mean']:+.3f} ± {r['aoeb_restraint_sd']:.3f} "
          f"| {r['aoeb_sign_stability'] if r['aoeb_sign_stability'] is not None else '—'} "
          f"| {r['share_of_overshoot_loeo']:+.0%} "
          f"| {r['interaction_gap']:+.3f} | {r['loeo_daffect_mean']:+.3f} |")
    A("\nReading: **LOEO** = how much separation rises when the unit is "
      "removed from the full schedule (its *marginal* brake). **AOEB** = how "
      "much the unit alone restrains the decade-only overshoot (its *solo* "
      "brake). A large LOEO−AOEB gap means the unit's braking depends on the "
      "other events (interaction); LOEO≈AOEB means independent braking.\n")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    main()
