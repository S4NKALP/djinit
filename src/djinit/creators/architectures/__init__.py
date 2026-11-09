from __future__ import annotations

from djinit.creators.architectures.base import ArchitectureHandler

ARCHITECTURE_HANDLERS: dict[str, type[ArchitectureHandler]] = {}

__all__ = [
    "ARCHITECTURE_HANDLERS",
    "ArchitectureHandler",
]
