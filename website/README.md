# polarlab — public website

Static HTML/CSS/vanilla-JS frontend that talks to the Python ABM engine
over a WebSocket (see `abm/web/server.py`). Implements wireframe E from
the design bundle.

## Files

- `index.html` — top nav, hero, full-bleed playground, scenario row,
  How-to-read / How-to-play, footer, fullscreen top strip
- `styles.css` — design tokens (off-white #f3f3f0, oxblood #8b2530,
  navy #1f3565), Geist throughout, FT-style underlines, dark mode
- `js/sim_client.js` — WebSocket client with auto-reconnect
- `js/canvas.js` — `<canvas>` renderer for the political compass:
  agent dots, party stars, hover ring, media-shock marker
- `js/app.js` — DOM orchestration: scenarios, sliders, transport,
  inspector, dark mode, fullscreen toggle

## Run

```powershell
python scripts\run_web.py
# open http://127.0.0.1:8000
```

The Python `abm.web.server` mounts this directory as the static root and
exposes a WebSocket at `/api/ws` plus REST helpers at `/api/scenarios`.

## Implementation notes

The wireframe specified a 60×22 lattice for visual variety; the actual
implementation places agents at their real 2D compass position
(ideology.x, ideology.y) since that's what the Python engine produces
and it carries more meaning (you can see emergent spatial clustering
rather than just opinion-colored lattice cells).

Param sliders mutate the corresponding rule attribute live via WebSocket
(`{type: param, name, value}`) — no engine rebuild required. Resetting
rebuilds with the *current* slider values, so a tweak then Reset gives
you a fresh run with your tuned parameters.

Inspector neighbourhood map shows the 6 nearest agents on the compass,
colored by their party. "Diversity" is the mean distance to those six.
