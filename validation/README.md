# Independent reality-validation harness

**Branch:** `model-reality-validation`. **Purpose:** test whether the shipped
engine output aligns with real-world survey data, using tests designed *from
scratch* against raw ANES + GSS microdata. This harness deliberately does **not**
import `abm/` or reuse anything in `tests/`. The only engine artefact it reads is
the *output* the public sees — `web/data/baseline/seed_0.json` — treated as an
opaque data file.

Motivation: the existing band/drift suite passed, yet (a) the 4-cut holdout fails
2/3 and (b) the 2000 compass shows Republicans bleeding into the
progressive-redistributive quadrant. We suspect the calibration nailed the 2020s
*endpoint* while getting the *path* wrong, which endpoint-anchored band tests
cannot see.

## Design principles
1. **Reality is recomputed from raw**, not taken from the pipeline's derived
   files. Raw sources: `data/phase9_empirical/raw/timeseries_csv.csv` (ANES
   cumulative file) and `data/gss_raw/gss7224_r3.dta` (GSS 1972-2024).
2. **Cross-check, then mine.** After recomputing independently we compare to the
   existing derived products (`party_centroids.csv`, `gss_constraint_series.json`)
   to (a) validate both and (b) see which existing methodological choices were
   actually good.
3. **Stylized facts, not bands.** Each test is a real-world fact a faithful
   1980->2025 model must reproduce, with severity grading. Endpoint match is not
   enough — trajectory and sign are tested year by year.

## Files
- `anes_from_raw.py`  — recompute ANES 2D party centroids, axis correlation,
  out-party thermometer directly from the raw CSV; cross-check vs derived.
- `gss_from_raw.py`   — recompute issue-constraint series from raw GSS .dta.
- `model_export.py`   — opaque reader for `seed_0.json` (no `abm` import).
- `battery.py`        — the stylized-fact battery: model vs reality, graded.
- `REPORT.md`         — generated findings, ranked by severity.

## Run (Windows PowerShell)
```powershell
.venv\Scripts\python.exe validation\anes_from_raw.py
.venv\Scripts\python.exe validation\gss_from_raw.py
.venv\Scripts\python.exe validation\battery.py
```
