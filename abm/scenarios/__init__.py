from . import actb, compass_basic, elite_dynamics, multi_party_4, two_party_sorting

REGISTRY = {
    "compass_basic": compass_basic.build,
    "actb": actb.build,
    "two_party_sorting": two_party_sorting.build,
    "multi_party_4": multi_party_4.build,
    "elite_dynamics": elite_dynamics.build,
}

__all__ = [
    "REGISTRY",
    "actb",
    "compass_basic",
    "elite_dynamics",
    "multi_party_4",
    "two_party_sorting",
]
