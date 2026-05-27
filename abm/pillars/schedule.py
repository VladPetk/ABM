"""
Schedule — ordered list of (tick, callable) pairs for the historical
scenario (Phase 8b).

A `Schedule` carries a list of events; each event is a `(tick,
event_fn)` tuple where `event_fn(engine)` mutates engine state
(rule parameters, agent attrs, etc.) at the event's tick. The
scenario's `run_to(target_tick)` advances the engine in chunks
bounded by upcoming events; each event fires once.

This is the historical-replication test's analog of the pillar's
`Intervention` machinery. Like an `Intervention`, each event has a
`description` (for human-readable logging) and a `tick` (when it
fires).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ScheduledEvent:
    tick: int
    label: str
    description: str
    event_fn: Callable


class Schedule:
    """Ordered event sequence. Mutates engine state at each event's tick."""

    def __init__(self, events: list[ScheduledEvent]):
        # Sort by tick — fires events in chronological order.
        self.events: list[ScheduledEvent] = sorted(events, key=lambda e: e.tick)
        self._fired: set[int] = set()

    def fire_due(self, engine, current_tick: int) -> list[ScheduledEvent]:
        """Fire every unfired event whose tick is ≤ current_tick.
        Returns the list of events fired in this call (for logging)."""
        fired_now = []
        for i, evt in enumerate(self.events):
            if i in self._fired:
                continue
            if evt.tick <= current_tick:
                evt.event_fn(engine)
                self._fired.add(i)
                fired_now.append(evt)
        return fired_now

    def next_tick(self, after: int) -> int | None:
        """Return the tick of the next unfired event > `after`, or None
        if no more events."""
        for i, evt in enumerate(self.events):
            if i in self._fired:
                continue
            if evt.tick > after:
                return evt.tick
        return None


def run_to(engine, schedule: Schedule, target_tick: int) -> list[ScheduledEvent]:
    """Advance `engine` until its tick == target_tick, firing
    scheduled events at their ticks along the way.

    Returns the list of events fired during this call."""
    all_fired = []
    # First, fire any events whose tick is at or before the current tick
    # (in case run_to(0) is called before the first run).
    all_fired.extend(schedule.fire_due(engine, engine.tick))
    while engine.tick < target_tick:
        next_event = schedule.next_tick(after=engine.tick)
        if next_event is None or next_event > target_tick:
            # Run straight through to target_tick.
            engine.run(target_tick - engine.tick)
            break
        # Run up to (not including) the event tick — events fire AFTER
        # ticks they're scheduled at (consistent with how Intervention
        # bundles work — applied between runs, not during a tick).
        engine.run(next_event - engine.tick)
        # Fire events that are now due.
        all_fired.extend(schedule.fire_due(engine, engine.tick))
    return all_fired
