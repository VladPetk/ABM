# Notices, attribution, and data provenance

## Licensing summary

| Part of the repo | License |
|---|---|
| **Code** — `abm/`, `scripts/`, `tests/`, `validation/`, `web_demo/` | [MIT](LICENSE) |
| **Documentation & prose** — `docs/`, `README.md`, figures, tables | [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) |
| **Derived data** — `data/` | CC-BY-4.0 **plus** the upstream providers' terms (below) |

If you reuse the documentation, findings, or figures, attribute this project
(polarlab). If you reuse the code, the MIT notice is sufficient.

## Data provenance & required upstream attribution

This model is calibrated against, and ships small **derived recodes** of, two
public survey programs. The derived artifacts (e.g.
`data/phase9_empirical/derived/respondent_coordinates.csv`,
`data/mhv/*.json`) are redistributed here **only to make the calibration
reproducible**. The underlying surveys remain the property of their providers
and are subject to their terms — if you use these data, cite the original
sources, not this repository:

- **ANES — American National Election Studies.** Time-series cumulative data
  file and codebook. <https://electionstudies.org>. The raw ANES files
  (~156 MB) are **not** redistributed here; they are regenerable by
  re-downloading from electionstudies.org (see
  `docs/methods.md` / the data-source notes) and re-running
  `scripts/phase9_anes_target_builder.py`.
- **GSS — General Social Survey**, NORC at the University of Chicago.
  <https://gss.norc.org>. The raw GSS cumulative file is **not** redistributed;
  only the small derived constraint series
  (`data/mhv/gss_constraint_series.json`) is committed.

These programs bear no responsibility for, and have not endorsed, the
analyses, recodes, or interpretations in this repository.

## Third-party runtime dependencies (web demo)

The web demo loads three libraries from a CDN (unpkg) at runtime; they are not
vendored in this repo and retain their own licenses:

- **React** / **ReactDOM** 18.3.1 — MIT (Meta Platforms, Inc.)
- **@babel/standalone** 7.29.0 — MIT (the Babel authors)

## Scope & honesty note

polarlab is a **teaching artefact, not a policy-prediction tool**. Results are
illustrative within a documented citation envelope; limitations are recorded in
[`docs/model_blindspots.md`](docs/model_blindspots.md) rather than hidden.
