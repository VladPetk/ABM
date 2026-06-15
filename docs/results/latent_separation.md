# Latent separation in the 1980 seed — measured ceiling of party re-sorting

*Emergence-recovery v1 polish. Reproduce: `PYTHONPATH=. .venv/Scripts/python.exe scripts/audit/latent_separation.py`.*

How much `party_sep` is already latent in the seeded 1980 electorate and
recoverable by re-labeling party alone (positions held fixed)? This bounds
the prize of an endogenous party-re-sorting ("great sort") channel and tests
whether the ~62% fitted-forcing share is a framing artifact.

| quantity | party_sep | share of 1980→2025 rise |
|---|---|---|
| engine 1980 baseline (as built) | 0.36 | — (≈ ANES 1980) |
| **optimal** re-label (preserve D/R counts, best direction) | **0.66** ± 0.03 | **+40%** |
| realistic re-label (½ of cross-pressured) | 0.60 | +32% |
| realistic re-label (¾ of cross-pressured) | 0.65 | +38% |
| spontaneous loop, mobilization ramp OFF | 0.565 | +28% |
| **full arc (with the fitted forcing)** | **1.11** | **+100%** |
| ANES 2025 target | 1.11 | +100% |

Cross-pressured (wrong-side-of-position) share of 1980 partisans: **31%**.

*Discrepancy note vs the design memo (emergence_floor_levers_menu.md): the memo's standalone scratchpad reported the spontaneous (ramp-OFF) floor at **0.545**; this blessed script measures **0.565** — the memo pinned a constant base drive on an empty schedule, this pins the mobilization ramp at 1980 while leaving the rest of the arc (media, dated events) intact. The ~0.02 gap is the residual media/event contribution; both land ≈ the 0.66 ceiling and the conclusion is unchanged. Every other number matches the memo to ±0.01.*

## Direction sanity-check — is the latent cleavage the real axis or the fed answer?

- population principal axis re-label: 0.659 (at 26°)
- fed `align_u` (→2D) re-label: 0.658 (at 17°)
- economic x-axis re-label: 0.643
- free angle-sweep maximum: 0.660 (at 22°)

The three fixed directions agree closely, so the unlockable structure is the
population's own (economic) cleavage — **not** the answer re-entering through
the fed amplification axis.

## The reading

- **Re-labeling cannot reach the end-state.** The optimal re-label tops out at
  0.66, while 2025 is 1.11: **60% of the 1980→2025 rise sits above the absolute ceiling** of any re-labeling of the 1980 positions. That share
  ≈ the ~62% fitted-forcing share — the part the forcing makes is almost exactly
  the part re-sorting provably *cannot*.
- **The dynamics already extract most of the latent pool.** The spontaneous
  loop reaches 0.565 on its own — 86% of the 0.66 re-sort ceiling — so an explicit re-sorting channel's headroom
  over what the model already does is small.
- **The latent prize ≈ the emergent floor we already report.** The re-sort
  ceiling as a share of the rise (+40%) lands on the ~38% spontaneous floor the budget quotes. 1980 was genuinely calm; reaching 2025
  required real positional/compositional change whose pace is externally set.

**Verdict:** endogenous party re-sorting is worth building for *realism* (it
faithfully renders the great sort and closes that blindspot), but **not** as an
emergence-floor lever: it is hard-capped well below the end-state, its
incremental gain over the existing spontaneous dynamics is small, and the floor
it would target is already ≈ where the model sits. The saturation-ratchet finding
holds (methods §5.29 / model_blindspots #7).

