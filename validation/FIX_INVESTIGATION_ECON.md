# Fix investigation — the ECONOMIC common-mode channel (branch econ-common-mode-mood)

Companion to `FIX_INVESTIGATION.md` (the cultural common-mode channel, shipped
d97048f). After the cultural axis was fixed, the from-scratch ANES+GSS battery
still showed an **economic** center-of-mass error with the *same architecture
cause*, and this file records the fix.

## The bug (already diagnosed; this file builds on it)
The partisan **economic** center of mass is pinned ≈ 0 the whole arc, while ANES
rises to ~+0.15 (rightward) in the mid-90s and declines to ~−0.05 by 2024
(non-monotone). Decomposition of the 1996 Republican econ residual (−0.19):
**center-of-mass LEVEL error −0.16 (≈84%)**, party half-GAP error −0.04 (≈16%).
So it is a common-mode LEVEL error, not a sorting-gap error. Root cause is
identical to the cultural axis: the econ axis has a *differential* (sorting)
channel (symmetric elite loop + PartyPull) but **no common-mode** (society-wide
level) channel — so the econ midpoint is structurally pinned to the 1980 seed.

## Why a FED forcing here, not emergent like the cultural channel
The cultural common mode is **emergent** (mean of a measured birth-cohort
gradient; cohort replacement, being monotone, generates the monotone cultural
decline). The economic tide is **non-monotone** (rightward to the mid-90s, then
leftward), so a monotone demographic primitive cannot generate it. The mechanism
is instead the **thermostatic policy mood** (Erikson–MacKuen–Stimson, *The Macro
Polity*; Wlezien's thermostat): econ policy preference moves rightward under the
Reagan→Clinton "end of big government" era (welfare reform / Gingrich 1994–96) and
leftward in the post-2008 thermostatic reaction. This is an exogenous **forcing**.

## How the exogenous mood series was derived (provenance)
1. **Downloaded the real Stimson Annual Policy Mood** (the canonical published
   index): `stimson.web.unc.edu` → `Mood5224.xlsx` → parsed to
   `validation/data/stimson_mood_annual.json` (1980–2024, higher = more liberal).
2. **Tested it as a literal driver — FALSIFIED** (`exp_econ_commonmode.py`,
   candidate A). Contemporaneous mood maps to the ANES econ center of mass only
   weakly (r ≈ 0.38); an affine map injects a spurious **+0.20 econ spike at 2012**
   — the Tea-Party *government-spending* mood swing that economic *self-placement*
   refused. Smoothing makes it worse (the secular component is wrong-signed).
   Lesson: Stimson's government-spending mood ≠ economic self-placement, so it is
   not a faithful tick-by-tick driver of the econ center of mass.
3. **Adopted a parsimonious thermostatic curve** (candidate B; the winner). Its
   inflection YEARS are documented policy events (1980 Reagan baseline → 1996
   welfare-reform peak → post-2008 leftward reaction); its single free scalar is
   the amplitude `ECON_MOOD_AMPLITUDE = 0.09`. It is **corroborated, not driven**,
   by the real Stimson series: Stimson independently shows mood turning
   conservative INTO the mid-90s (69.1@1991 → 59.0@1995) and liberal THROUGH the
   2010s (54.8@2012 → 65.9@2020). We did **not** replay the ANES econ series.
   Provenance: **L** (thermostatic common-mode mechanism) + **N** (curve form) +
   **E** (amplitude/shape extrapolated). Honest caveat: this is a **fed forcing**
   — a weaker honesty claim than the emergent cultural channel.

## Triple-independent confirmation of the target (not ANES over-fitting)
Three independent sources agree on the rightward-mid-90s → leftward-2020s arc:
- **ANES** partisan econ center of mass: +0.065 (1986) → +0.15 (1994–96) → −0.05 (2024).
- **GSS** partisan econ-rightward index from raw (`gss_econ_check.py`, items
  `helppoor`+`eqwlth`, independent dataset + items): **mid-90s +0.106 → late-2010s
  −0.057** ("rightward-then-left: CONFIRMED"; corr with the fed curve +0.37).
- **Stimson** Policy Mood: conservative trough mid-90s, liberal by the 2020s.

## The fix (gated, validated)
New env rule `CommonModeEconomic` (`abm/rules/cultural_common_mode.py`), sharing
the rigid-translation helper `rigid_common_mode_shift` with the cultural channel.
It snaps the partisan econ common mode to `economic_mood_offset(year)` each tick —
a rigid, sorting-invariant econ-axis translation of the issue vector. Gated by
`build_engine(economic_common_mode=True)`; default off → **bit-identical to head**
(verified: canonical-arc SHA-256 matches d97048f exactly).

### Result (seed 0, econ on, vs canonical econ off)
- **Econ COM mean|err| over 1986–2024: 0.084 → 0.030** (−64%). 1996 econ COM
  −0.018 → **+0.088** (the robust GSS-corroborated +0.09 level; matching the
  noisier ANES +0.15 mid-90s hump exactly would over-fit a survey artifact, cf.
  the cultural channel's GSS-over-ANES call).
- **F5 Republican wrong-quadrant (LL): improves every measured year, regresses
  none** (2000 0.120 → 0.093 = ANES 0.082; 2008 0.094 → 0.085; 1992 0.162 → 0.135).
- **Cultural axis bit-identical** (1996 cult 0.079/0.078; 2024 −0.040/−0.040) —
  the econ channel is cleanly orthogonal; F0/F2 unchanged.
- **Sorting preserved/improved** (rigid translation is sorting-invariant): party
  sep@135 1.056 → 1.065; econ–cult corr up across the arc.

### Battery tags (measure-then-bless; no threshold loosened)
F0/F2/F5 stay HIGH FAIL — but F0/F2 are **cultural** (untouched here) and F5's
residual excess is the early-period *cultural* center still being too progressive,
not econ. The econ fix did its job on the econ axis; the residual is the unfixed
cultural-channel limitation (out of scope for this change).

## Status
Implemented GATED, default off = bit-identical. **NOT** flipped to canonical and
**NOT** re-blessed (phase10 / web export / docs) — awaiting user sign-off, per the
session mandate. To flip later: set `economic_common_mode=True` (+ amplitude) in
`ANES_FULL_KWARGS` and run the re-bless cascade.
