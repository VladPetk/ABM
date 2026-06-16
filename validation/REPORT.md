# Reality-validation report

Model: `web/data/baseline/seed_0.json` (preset anes_full, seed 0). Reality: ANES recomputed from raw, validated against the derived pipeline (max diff 0.0000).

Each fact graded year-by-year over ANES survey years 1986-2024.

## Summary

| sev | id | fact | status | real world | model |
|---|---|---|---|---|---|
| **HIGH** | F0 | Cultural center-of-mass placement (ROOT CAUSE) | FAIL | ANES partisan center stays culturally TRADITIONAL (cult ~ +0.10..+0.22) until ~2016 | model center is ~-0.11 on cult in 1994-2004; worst 2000: -0.15 |
| **HIGH** | F2 | Democratic cultural sorting timing/sign | FAIL | D cult >= ~0 (centrist) until ~2004, then turns progressive | D cult is progressive (<0) from the start; wrong-sign years: [1994, 1996, 2000] |
| **HIGH** | F5 | Republican wrong-quadrant tail (your screenshot) | FAIL | ANES Rs ~8-12% in prog-redist (LL); ~50-72% in trad-laissez (UR) | model over-fills LL in 6 yrs; worst 1994: 14% vs ANES 6% |
| **MEDIUM** | F3 | Economic separation trajectory | FAIL | R-D econ gap 0.32->0.76, rising | model gap 0.37->0.74; mid-period(94-10) mean|err|=0.092 |
| **PASS** | F1 | Republican cultural traditionalism | PASS | R cult > 0 every year (ANES 0.17->0.34) | under-sorted in 0/14 yrs; mean|err|=0.047 |
| **PASS** | F4 | Cultural sorting is back-loaded (timing) | PASS | early cult gap is 33% of late gap (sorting happens LATE) | model early gap is 44% of its late gap (front-loaded by 11pts) |
| **PASS** | F6 | Econ-cult axis correlation (constraint) | PASS | ANES corr 0.36->0.78 | model tracks it; mean|err|=0.051 |
| **PASS** | F7 | Out-party affect cooling (shape) | PASS | ANES thermometer 49->21 (cooling) | model affect monotone=True, corr w/ thermometer r=0.97 |
| **PASS** | F8 | Independents between parties (econ) | PASS | ANES: I econ between D and R every year | model violates ordering in 0 yrs: none |
| **PASS** | F9 | Within-party spread (SD) realism | PASS | ANES within-party SD ~0.30-0.39 per axis | mean|SD err|=0.057 |

## Detail

### [HIGH] F0 — Cultural center-of-mass placement (ROOT CAUSE)  (FAIL)
- **Real world:** ANES partisan center stays culturally TRADITIONAL (cult ~ +0.10..+0.22) until ~2016
- **Model:** model center is ~-0.11 on cult in 1994-2004; worst 2000: -0.15
- **Diagnosis:** Party SEPARATION is ~right but the whole cloud's LOCATION is too progressive (and slightly too redistributive) in the mid-period. Both parties are shifted down-left together, so the Republican cloud's tail spills into the progressive-redistributive quadrant near NYT. F1, F2, F5 are symptoms of this single placement error. Closes by 2020 -> endpoint match hides it from band tests.

### [HIGH] F2 — Democratic cultural sorting timing/sign  (FAIL)
- **Real world:** D cult >= ~0 (centrist) until ~2004, then turns progressive
- **Model:** D cult is progressive (<0) from the start; wrong-sign years: [1994, 1996, 2000]
- **Diagnosis:** In reality the cultural realignment of Democrats is a post-2008 phenomenon. The model bakes progressive Democrats in from 1986 -> the path is wrong even though the 2020s endpoint matches.

### [HIGH] F5 — Republican wrong-quadrant tail (your screenshot)  (FAIL)
- **Real world:** ANES Rs ~8-12% in prog-redist (LL); ~50-72% in trad-laissez (UR)
- **Model:** model over-fills LL in 6 yrs; worst 1994: 14% vs ANES 6%
- **Diagnosis:** Two-sided: model UR is far too sparse and LL too dense -> the red blob near NYT. e.g. 2000 model LL 15% vs ANES 8%, model UR 45% vs ANES 67%.

### [MEDIUM] F3 — Economic separation trajectory  (FAIL)
- **Real world:** R-D econ gap 0.32->0.76, rising
- **Model:** model gap 0.37->0.74; mid-period(94-10) mean|err|=0.092
- **Diagnosis:** Model compresses the economic gap in the 1994-2010 window (Republicans not laissez-faire enough). Monotonic rise OK.

### [PASS] F1 — Republican cultural traditionalism  (PASS)
- **Real world:** R cult > 0 every year (ANES 0.17->0.34)
- **Model:** under-sorted in 0/14 yrs; mean|err|=0.047
- **Diagnosis:** worst 1996: model 0.26 vs ANES 0.37. Model Rs sit near the cultural center mid-period; reality has them clearly traditional.

### [PASS] F4 — Cultural sorting is back-loaded (timing)  (PASS)
- **Real world:** early cult gap is 33% of late gap (sorting happens LATE)
- **Model:** model early gap is 44% of its late gap (front-loaded by 11pts)
- **Diagnosis:** ANES early cult gap 0.24->late 0.72; model early 0.31->late 0.71.

### [PASS] F6 — Econ-cult axis correlation (constraint)  (PASS)
- **Real world:** ANES corr 0.36->0.78
- **Model:** model tracks it; mean|err|=0.051
- **Diagnosis:** The 'over-correlation ~0.78' worry is largely unfounded: 0.78 IS the real 2024 value and the model's correlation path roughly matches ANES.

### [PASS] F7 — Out-party affect cooling (shape)  (PASS)
- **Real world:** ANES thermometer 49->21 (cooling)
- **Model:** model affect monotone=True, corr w/ thermometer r=0.97
- **Diagnosis:** Shape matches; magnitude/mapping is a separate calibration question (affect bands).

### [PASS] F8 — Independents between parties (econ)  (PASS)
- **Real world:** ANES: I econ between D and R every year
- **Model:** model violates ordering in 0 yrs: none

### [PASS] F9 — Within-party spread (SD) realism  (PASS)
- **Real world:** ANES within-party SD ~0.30-0.39 per axis
- **Model:** mean|SD err|=0.057
- **Diagnosis:** Model agents are typically tighter than real respondents (survey noise vs latent position).
