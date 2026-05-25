"""
Mesa adapter — optional shim wrapping our Engine in a mesa.Model.

Provided so the simulation can plug into Mesa's batch tools, DataCollector,
and SolaraViz components without modifying core code. The core has zero
Mesa imports; the adapter lives here so swapping Mesa for any other
runtime (FastAPI streaming, Ray, custom batch runner) is a single-file
replacement.

Mesa is an *optional* dependency: install with `pip install abm[mesa]`.
"""
from __future__ import annotations

from ..core.engine import Engine


def wrap(engine: Engine):
    """Return a mesa.Model subclass instance that ticks our Engine."""
    try:
        import mesa
    except ImportError as e:
        raise RuntimeError(
            "Mesa is not installed. Install it with `pip install abm[mesa]`."
        ) from e

    class _AdaptedModel(mesa.Model):
        def __init__(self):
            super().__init__()
            self.engine = engine

        def step(self):
            self.engine.step()

        @property
        def positions(self):
            return self.engine.positions()

    return _AdaptedModel()
