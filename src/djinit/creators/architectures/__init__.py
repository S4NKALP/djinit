from __future__ import annotations

from djinit.creators.architectures.base import ArchitectureHandler
from djinit.creators.architectures.modular_monolith import ModularMonolithHandler

ARCHITECTURE_HANDLERS: dict[str, type[ArchitectureHandler]] = {
    "modular_monolith": ModularMonolithHandler,
}

__all__ = [
    "ARCHITECTURE_HANDLERS",
    "ArchitectureHandler",
    "ModularMonolithHandler",
]
