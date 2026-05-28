from . import compass_basic

REGISTRY = {
    "compass_basic": compass_basic.build,
}

__all__ = [
    "REGISTRY",
    "compass_basic",
]
