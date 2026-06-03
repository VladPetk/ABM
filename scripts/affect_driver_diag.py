"""Affect driver-trajectory diagnostic (affect-bands-investigation, step 3).

Runs the canonical shipped arc (seed 0) and traces, over 1980->2025, the
ENDOGENOUS drivers that should shape out-party affect, alongside out-party
network exposure and the affect trajectory itself. Answers: are the
convexity-producing ingredients present and accelerating, and if so why is
the measured affect concave (front-loaded) instead of convex?

Finding (see docs/affect_bands_investigation.md): the drivers accelerate
correctly (identity_alignment 0.21->0.41 convex; threat spikes late; coupling
0.40->1.10), but affect is CONTACT-GATED and out-party exposure ~halves over
the arc (homophilous sorting), and the (1-w^2) saturation term damps late
steps — so the accelerating drivers get multiplied by a shrinking contact
count and shrinking saturation factor, netting deceleration (concave).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(k, "1")
import numpy as np
from scripts.anes_preset import ANES_FULL_KWARGS
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from abm.metrics.affective import affective_polarization


def main(seed=0, every=9):
    kw = dict(ANES_FULL_KWARGS)
    eng = build_engine(seed=seed, **kw)
    sched = build_schedule(
        factional_seeding=kw.get("factional_seeding", False),
        faction_anchor_events=kw.get("faction_anchor_events", True),
        evidence_regrade=kw.get("evidence_regrade", False),
        exogenous_shocks=kw.get("exogenous_shocks", False),
    )

    def snap():
        ag = eng.agents
        net = eng.env.attrs["network"]
        idmap = {x.id: x.state.attrs.get("party") for x in ag}
        part = [a for a in ag if a.state.attrs.get("party") in (0, 1)]
        align = np.mean([a.state.attrs.get("identity_alignment", 0.0) for a in part])
        threat = np.mean([a.state.attrs.get("perceived_threat", 0.0) for a in part])
        coup = eng.env.attrs.get("party_issue_coupling", 1.0)
        aw = eng.env.attrs.get("identity_alignment_affect_weight", 0.0)
        fr, cn = [], []
        for a in part:
            nbrs = net.neighbors(a.id)
            myp = a.state.attrs["party"]
            opn = [j for j in nbrs if idmap.get(j) in (0, 1) and idmap.get(j) != myp]
            if nbrs:
                fr.append(len(opn) / len(nbrs))
            cn.append(len(opn))
        return (affective_polarization(ag), align, threat, coup, aw,
                float(np.mean(fr)), float(np.mean(cn)))

    print(f"{'yr':>6}{'affect':>8}{'align':>7}{'threat':>7}{'coup':>6}"
          f"{'alignW':>7}{'opFrac':>7}{'opCnt':>6}")
    prev = None
    for t in range(0, 136):
        if t > 0:
            run_to(eng, sched, t)
        if t % every == 0 or t == 135:
            aff, al, th, co, aw, fr, cn = snap()
            d = "" if prev is None else f"  dAff={aff-prev:+.3f}"
            print(f"{1980+t/3:6.0f}{aff:8.3f}{al:7.3f}{th:7.3f}{co:6.2f}"
                  f"{aw:7.2f}{fr:7.3f}{cn:6.2f}{d}")
            prev = aff


if __name__ == "__main__":
    main()
