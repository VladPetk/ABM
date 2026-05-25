"""Canonical replication — Hegselmann-Krause phase behavior.

Independent of the pillar: drives `compass_basic` directly so the engine
itself is pinned to a published result. The three epsilon ensembles are
computed once each in conftest fixtures and reused.
"""
from __future__ import annotations

import numpy as np


def test_hk_loose_epsilon_consensus(hk_loose_finals):
    """Loose epsilon -> single consensus blob."""
    mean_v = float(np.mean(hk_loose_finals))
    assert mean_v < 0.05, (
        f"HK loose (eps=2.0) should converge to ~0 variance; got mean {mean_v:.3f}."
    )


def test_hk_tight_epsilon_fragmentation(hk_tight_finals):
    """Tight epsilon -> persistent multi-cluster fragmentation."""
    mean_v = float(np.mean(hk_tight_finals))
    assert mean_v > 0.45, (
        f"HK tight (eps=0.15) should stay fragmented; got mean {mean_v:.3f}."
    )


def test_hk_monotonic_in_epsilon(hk_loose_finals, hk_mid_finals, hk_tight_finals):
    """Variance increases monotonically as epsilon shrinks."""
    loose = float(np.mean(hk_loose_finals))
    mid = float(np.mean(hk_mid_finals))
    tight = float(np.mean(hk_tight_finals))
    assert loose < mid < tight, (
        f"Expected monotonic loose<mid<tight; got {loose:.3f}, {mid:.3f}, {tight:.3f}."
    )
