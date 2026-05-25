# ABM — Political Polarization Sandbox

A flexible agent-based modeling framework built around a 2D political compass
(`economic left ↔ right`, `libertarian ↔ authoritarian`). Agents drift through
ideology space according to composable rules; polarization patterns emerge.

## Architecture

The simulation core (`abm/core/`, `abm/rules/`, `abm/scenarios/`, `abm/metrics/`)
is **pure Python — zero framework imports**. The Mesa adapter
(`abm/adapters/mesa_adapter.py`) is the only file that touches Mesa, and only
when explicitly loaded. The Solara dashboard (`abm/viz/`) is one of many
possible front-ends.

```
abm/
  core/        state, agent, environment, space, rules, engine
  rules/       composable behavior — influence, repulsion, noise, party_pull, ...
  scenarios/   wirings of env + agents + rules
  metrics/     polarization measures
  adapters/    framework bridges (Mesa, etc.)
  viz/         Solara research dashboard
  web/         FastAPI + WebSocket bridge for the public website
website/       static frontend (HTML/CSS/JS) — talks to abm.web over WebSocket
scripts/
  run_headless.py  text-mode smoke test
  run_web.py       launch the public website locally
  compare.py       literature-validation comparisons
```

## Quickstart (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .

# headless smoke test — pick a scenario
python scripts\run_headless.py --scenario compass_basic       --steps 200
python scripts\run_headless.py --scenario actb                --steps 200
python scripts\run_headless.py --scenario two_party_sorting   --steps 200
python scripts\run_headless.py --scenario multi_party_4       --steps 200
python scripts\run_headless.py --scenario elite_dynamics      --steps 200

# validation comparisons against the literature
python scripts\compare.py sorting    # Mason 2018
python scripts\compare.py parties    # Gidron et al. 2020
python scripts\compare.py elite      # Hetherington 2001

# interactive research dashboard (Solara)
solara run abm.viz.solara_app

# polished public website (FastAPI + WebSocket + static frontend)
python scripts\run_web.py
# then open http://127.0.0.1:8000
```

Open the URL Solara prints (default `http://localhost:8765`).

## Scenarios

Three scenarios let you contrast the major ABM families from the
political-polarization literature:

| Scenario | Rules | Tests |
|---|---|---|
| `compass_basic` | Hegselmann-Krause attraction + noise (+ optional Macy-Flache repulsion) | Family A baseline. Without repulsion: convergence. With repulsion: classic polarization. |
| `actb` | Mäs-Flache argument exchange + noise | Family C-without-negative-influence. Can homophily + argument adoption alone produce bi-polarization? (Yes — and the headless run confirms it.) |
| `two_party_sorting` | HK + party-pull (elite cue) + affective update + noise (+ optional identity sorting) | Two-layer Stage 2 model. Reproduces affective ≠ ideological polarization (Iyengar et al. 2019); identity sorting amplifies affective polarization (Mason 2018). |
| `multi_party_4` | Two-layer Stage 2 + identity sorting, 4 parties at corners | Reproduces Gidron et al. 2020: multiparty shows lower affective polarization than two-party at equal sorting. |
| `elite_dynamics` | Stage 2 + EliteDrift + MediaShock + PartisanMediaExposure | Stage 3.1. Party centers drift outward over time; periodic shocks; heavy-media-diet agents polarize further. Reproduces Hetherington 2001: elite cue divergence drives mass polarization. |

Stage 2 scenarios add identity-based metrics: **affective polarization**
(mean out-party warmth) and **ideological constraint** (party-issue
correlation). These mirror the operationalizations in Reiljan (2020)
and Baldassarri & Gelman (2008).

Why repulsion is off by default: the empirical record for negative
influence is mixed. Mäs-Flache (2013) showed bi-polarization can emerge
*without* it, so we default to the more conservative mechanism and let
repulsion be opt-in for comparison runs.

## Extending

Add a new rule: drop a file in `abm/rules/`, implement `apply(agent, space, env, rng) -> StateDelta`,
register it in your scenario. Add a new scenario: drop a file in `abm/scenarios/`
that builds an `Engine` with whatever rule pipeline + initial conditions you want.
Add a field to agents: stash it in `AgentState.attrs` — no class change required.

## Stage 2 (planned)

- Parties as env state; party-pull rule
- Stubborn / "true believer" agents
- Media-event rule (external shocks)
- Multi-party scenario (EU-style)
- Custom D3/Three.js web front-end fed by headless engine output (for the website)
