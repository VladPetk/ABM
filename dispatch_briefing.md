polarlab — Phases 4-7, spec-gated autonomous run

You are continuing "polarlab," an agent-based model of political polarization
that will become a public-facing interactive website. It must stay
research-rigorous: calibrated to published findings, intellectually honest,
every decision pinned before implementation, no overclaiming. The codebase is
at D:\MyApps\ABM and you have file access there.

GET FULL CONTEXT FIRST. Read these files in the project folder:
- pillar_engine_roadmap.md — the overall plan
- adr_001_network_primary_engine.md + adr_001_implementation_spec.md — the
  latest architecture decision and how it was built
- pillar_spec.md, phase1_spec.md, phase2_spec.md, phase3_design.md,
  phase3_spec.md, s4_network_research.md — earlier specs and research
Then skim abm/ (the engine) and tests/ for current state.

CURRENT STATE. The engine has been re-founded so the social network is the
primary substrate of influence (ADR-001): influence flows along social ties,
not raw ideological proximity. It is implemented, reviewed, and all 25 tests
pass. The five-stage "calm to camps" pillar — S0 baseline -> S1 bounded
confidence -> S2 party identity -> S3 partisan media -> S4 homophilous network —
runs on the new substrate. scripts/show_pillar_mpl.py renders a quick visual
check. Phases 4-7 remain.

WHAT NEEDS DOING — Phases 4 to 7:
- Phase 4, realism core: fix the overshoot (the model collapses into two tiny
  blobs; real societies don't). Add heterogeneous anchored agents
  (Friedkin-Johnsen stubbornness — most people barely move), activate the
  involuntary cross-cutting tie stratum, make the confidence filter graded.
  No separate tapering rule — the pull rules already taper.
- Phase 5: affective polarization as a first-class channel, separate from
  issue position.
- Phase 6: repulsion and "null levers" — interventions that look like they
  would cut polarization but do not, shown honestly.
- Phase 7: calibration — pin what a tick represents in real time; tune step
  sizes against real panel data.

WORKFLOW — spec-gated, one phase at a time:
1. Write the phase's full implementation spec into the folder (phaseN_spec.md),
   in the house style of the existing specs: every decision pinned, tests
   defined, a measure-then-bless gate where thresholds can't be pre-measured.
2. Post a SHORT summary flagging the "judgment forks" — modeling decisions that
   aren't pure code-correctness.
3. STOP and wait for my confirm or adjustments (I send them through Dispatch).
4. On confirm: run implement -> independent review (a separate review
   subagent) -> test-verify.
5. Post a short result, then move to the next phase.

Do not touch any UI/website files. Flag anything that is a genuine modeling
judgment rather than a code detail — never silently guess.

NEXT ACTION: determine the current phase from the specs already in the folder
and continue the loop. If no phase4_spec.md exists, start there — write it,
post its short summary, and stop for my confirmation.
