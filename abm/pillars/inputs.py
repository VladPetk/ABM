"""
Typed input channels — MHV S3 (M6-lite).

Exogenous forces enter the historical arc as **data-fed series** read from
committed files, not hand-tuned per-decade schedules or ad-hoc state pokes.

A *series* is a bundle of named float **channels**, each a table of
``(year, value)`` anchor points, carried with a provenance header (units,
source, and an L/N/E tag). A :class:`DataFedSeries` env-rule interpolates the
channels to the current tick's year every tick and writes them into the world.

Two S3 consumers subclass :class:`DataFedSeries`:

* :class:`PartyCentroidSeries` (T3.2) — sets ``env.attrs["parties"][pid]`` from
  the measured ANES voter centroids and propagates the per-tick shift to each
  agent's ``party_cue`` (replacing the scheduled ``EliteDrift``).
* :class:`EnvAttrSeries` / media coupling (T3.3) — writes interpolated channels
  straight into ``env.attrs`` typed slots that rules read.

**Invariant I3.** These channels are the sanctioned path for exogenous
influence; no bespoke event handler writes outcome variables
(``affect`` / ``issues`` / ``ideology`` / alignment) directly. The transient
one-shot nudges that remain ride the declarative ``shocks.py`` channel.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

# Standard arc time anchor (CLAUDE.md: tick 0 = 1980, 3 ticks/year).
DEFAULT_YEAR0 = 1980.0
DEFAULT_TICKS_PER_YEAR = 3

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# Committed S3 input series (generators under scripts/).
PARTY_CENTROID_SERIES_PATH = os.path.join(
    _ROOT, "data", "mhv", "party_centroid_series.json")
MEDIA_PENETRATION_SERIES_PATH = os.path.join(
    _ROOT, "data", "mhv", "media_penetration_series.json")

REQUIRED_META = ("name", "unit", "source", "lne_tag")
_LNE = ("L", "N", "E")


class Series:
    """A bundle of named float channels with a provenance header.

    Each channel is a ``(k, 2)`` array of ``(x, value)`` anchor rows (sorted
    ascending on x at construction). :meth:`at` linearly interpolates every
    channel, clamping to the endpoint values outside the anchor range
    (``np.interp`` semantics — no extrapolation, so a data-fed series can never
    runaway past its measured envelope).
    """

    def __init__(self, channels: dict, meta: dict):
        self.channels: dict[str, np.ndarray] = {}
        for name, rows in channels.items():
            a = np.asarray(rows, dtype=float)
            if a.ndim != 2 or a.shape[1] != 2:
                raise ValueError(
                    f"channel {name!r} must be a (k, 2) table of (x, value); "
                    f"got shape {a.shape}"
                )
            if a.shape[0] < 1:
                raise ValueError(f"channel {name!r} has no anchor rows")
            self.channels[name] = a[np.argsort(a[:, 0])]
        self.meta = dict(meta)

    def at(self, x: float) -> dict:
        """Interpolated ``{channel_name: value}`` at coordinate ``x``."""
        return {
            name: float(np.interp(x, a[:, 0], a[:, 1]))
            for name, a in self.channels.items()
        }

    @property
    def names(self) -> list:
        return list(self.channels.keys())


def load_series(path) -> Series:
    """Load a committed series JSON.

    Schema::

        {
          "name": "...", "description": "...", "unit": "...",
          "source": "...", "lne_tag": "L" | "N" | "E", "x": "year",
          "channels": {"<name>": [[year, value], ...], ...}
        }

    The four ``REQUIRED_META`` keys must be present and ``lne_tag`` must be one
    of L/N/E — the honesty discipline (I6) refuses an un-provenanced input.
    """
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    for k in REQUIRED_META:
        if k not in raw:
            raise ValueError(f"series {path}: missing required meta key {k!r}")
    if raw["lne_tag"] not in _LNE:
        raise ValueError(
            f"series {path}: lne_tag must be one of {_LNE}, got {raw['lne_tag']!r}"
        )
    channels = raw.get("channels")
    if not channels:
        raise ValueError(f"series {path}: no channels")
    meta = {k: v for k, v in raw.items() if k != "channels"}
    return Series(channels, meta)


def tick_to_year(
    tick: int, year0: float = DEFAULT_YEAR0,
    ticks_per_year: int = DEFAULT_TICKS_PER_YEAR,
) -> float:
    return float(year0) + tick / float(ticks_per_year)


class DataFedSeries:
    """EnvRule base. Each tick: map tick → year, interpolate the series, and
    hand the channel values to :meth:`_apply` (subclasses decide where they
    go). Matches the ``EnvRule`` protocol (``apply(env, agents, space, rng,
    tick)``)."""

    def __init__(
        self, series: Series,
        year0: float = DEFAULT_YEAR0,
        ticks_per_year: int = DEFAULT_TICKS_PER_YEAR,
    ):
        self.series = series
        self.year0 = float(year0)
        self.ticks_per_year = int(ticks_per_year)

    def apply(self, env, agents, space, rng, tick) -> None:
        year = tick_to_year(tick, self.year0, self.ticks_per_year)
        self._apply(env, agents, self.series.at(year), tick)

    def _apply(self, env, agents, values, tick):  # pragma: no cover
        raise NotImplementedError


class EnvAttrSeries(DataFedSeries):
    """Writes each interpolated channel straight into ``env.attrs`` under its
    own name — the simplest typed-input slot (a rule reads ``env.attrs[name]``
    with a fallback so non-arc scenarios stay bit-identical). Optional
    ``rename`` maps a channel name to a different env-attr key."""

    def __init__(self, series: Series, rename: dict | None = None, **kw):
        super().__init__(series, **kw)
        self.rename = dict(rename or {})

    def _apply(self, env, agents, values, tick):
        for name, v in values.items():
            env.attrs[self.rename.get(name, name)] = v


class PartyCentroidSeries(DataFedSeries):
    """Elite channel (T3.2). Sets each party's 2D centroid in
    ``env.attrs["parties"]`` from the measured ANES voter-centroid series and
    propagates the per-tick shift to every agent's ``party_cue`` (the quantity
    ``PartyPull`` actually reads — mirroring the retired ``EliteDrift``).

    Channels required, per party id ``p``: ``p{p}_econ`` (x / economic) and
    ``p{p}_cult`` (y / cultural). Only parties present both in
    ``env.attrs["parties"]`` and in the series are driven (Independents have no
    centroid channel and are left alone).
    """

    def _apply(self, env, agents, values, tick):
        parties = env.attrs.get("parties")
        if not parties:
            return
        per_party_step: dict = {}
        for pid in list(parties.keys()):
            ex, cy = f"p{pid}_econ", f"p{pid}_cult"
            if ex not in values or cy not in values:
                continue
            target = np.array([values[ex], values[cy]], dtype=float)
            old = np.asarray(parties[pid], dtype=float).copy()
            new = np.clip(target, -1.0, 1.0)
            parties[pid] = new
            per_party_step[pid] = new - old
        # Propagate the shift to per-agent cues (PartyPull reads party_cue;
        # an input that only moved env centroids would silently fail to reach
        # mass behaviour — the same coupling EliteDrift carried).
        for a in agents:
            cue = a.state.attrs.get("party_cue")
            if cue is None:
                continue
            party = a.state.attrs.get("party")
            if party not in per_party_step:
                continue
            a.state.attrs["party_cue"] = np.clip(
                cue + per_party_step[party], -1.0, 1.0
            )
        viz = env.attrs.setdefault("viz", {})
        viz["party_centers"] = parties


class MediaPenetrationSeries(DataFedSeries):
    """Media channel (T3.3). Writes two typed coupling slots into ``env.attrs``
    from the penetration curves, with **weak** coefficients (media-paradox
    blindspot cluster — Boxell/Guess/Allcott/Prior):

    * ``media_strength`` = ``media_strength_max`` × ``partisan_media`` — read by
      ``MediaConsumption`` (the partisan-media diet pull). The default max
      (0.04) reproduces the FD-1987→0.02 / Fox-1996→0.04 step values as a
      penetration ramp.
    * ``bc_affect_weight`` = ``bc_aw_per_adoption`` × ``social_media`` — read by
      ``BoundedConfidenceInfluence`` (the homophilous echo amplifier). The
      default coefficient (0.094) reproduces the demoted evidence-regrade ramp
      (~0.02 @2008 / ~0.04 @2010 / ~0.05 @2012) from the Pew adoption curve.

    Both slots are read with a fallback to the rule's own value, so a scenario
    that doesn't install this series stays bit-identical.
    """

    def __init__(self, series: Series, media_strength_max: float = 0.04,
                 bc_aw_per_adoption: float = 0.094, **kw):
        super().__init__(series, **kw)
        self.media_strength_max = float(media_strength_max)
        self.bc_aw_per_adoption = float(bc_aw_per_adoption)

    def _apply(self, env, agents, values, tick):
        if "partisan_media" in values:
            env.attrs["media_strength"] = (
                self.media_strength_max * values["partisan_media"])
        if "social_media" in values:
            env.attrs["bc_affect_weight"] = (
                self.bc_aw_per_adoption * values["social_media"])
