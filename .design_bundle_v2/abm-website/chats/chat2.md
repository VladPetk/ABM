# Parameter Panel Layout

_Started 2026-05-24 06:36 UTC_

---

## User

So the sim is no longer square, and the parameters are covering a bunch of it. Should we try making the parameters a pane that can be hidden? I dunno what makes sense. The current approach also looks good but maybe hiding it is a good idea? Think it through

## Assistant

_[tool: list_files]_

_[tool: read_file]_

_[tool: read_file]_

_[tool: write_file]_

Thinking it through before I build:

**Why the current Parameters card feels heavy:** The sim used to be square so the card sat to the side of the action. Now the sim is wide, the card eats the top-left quadrant — which is also the quadrant your eye lands on first when scanning left-to-right. Of the four floating cards, Parameters is the biggest and the only one that's pure UI (sparkline/legend/inspector all carry info that earns its keep).

**Hide-by-default is the right move** — for three reasons:
1. Most viewers will look first, tweak second. The current panel demands attention before the sim has had a chance to make its point.
2. The KPI strip + scenarios on the left already advertise that this thing is interactive. Discoverability isn't gated by the slider card being visible.
3. Once a slider IS open, you want it spacious — currently it's cramped at 244px because we're trying to balance "visible" with "small." Hiding by default lets the open state breathe.

**What the collapsed state should be:** a small pill in the same top-left position. Not just an icon — it should advertise *what's tweakable* with a one-line summary so users understand the affordance before clicking. Something like "Parameters · 4 set · ▾" or with tiny live readouts.

Let me build two new artboards: collapsed (default) + expanded (with explicit close), so you can compare both states side-by-side. I'll also do a third — parameters as a docked bottom rail — so we can compare "hide entirely" vs. "always visible but out of the way."

_[tool: read_file]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: read_file]_

_[tool: write_file]_

_[tool: done]_

_[tool: fork_verifier_agent]_

Added three new artboards next to the current one so you can compare directly:

- **params open (current)** — the existing version, for reference
- **params hidden (proposal)** — sim is fully visible; the top-left has a slim glass pill that names the parameter and shows live values (`homophily 0.72  tolerance 0.28  …`) with a ▾ to expand. Roughly 1/4 the footprint and one line tall. This is my recommendation.
- **params expanded (with close)** — what the open state looks like once you click in: same card as today plus an explicit × so it's clear it's dismissable.
- **params docked as bottom rail** — alternative: parameters never overlap the sim, they live as a slim horizontal strip between the sim and the transport bar. Always visible, sim is unobstructed — but the sim does lose ~88px of vertical space.

My take: the **collapsed pill** is the right default. It keeps the discoverability promise (the values are right there, advertising "you can change these") without eating the top-left quadrant. The rail is a fine fallback if you don't like a click-to-expand interaction, but the sim gets shorter and slightly squarer, which fights the "wide hero" feel you just established.

## User

"E · Hero split — params hidden (proposal)" - one with collapsed pill -  is great! Can we just reduce the width of the sim a bit? not a full 50-50 left-right, but a bit more equal that it is now

## Assistant

_[tool: read_file]_

_[tool: grep]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

Updating the original `wf-e-hero-split.jsx` too so the comparison stays apples-to-apples:

_[tool: done]_

Bumped the left column from 500→600px, so the sim shrinks from ~820 to ~720px wide. Ratio went from 38/62 to roughly 45/55 — more balanced without going full 50/50. Applied to both hero-split artboards so the comparison stays clean.

