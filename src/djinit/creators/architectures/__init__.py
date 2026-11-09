from __future__ import annotations

from djinit.creators.architectures.base import ArchitectureHandler
from djinit.creators.architectures.fullstack_htmx import FullStackHTMXHandler
from djinit.creators.architectures.lightweight import LightweightHandler
from djinit.creators.architectures.modular_monolith import ModularMonolithHandler
from djinit.creators.architectures.service_layer import ServiceLayerHandler

ARCHITECTURE_HANDLERS: dict[str, type[ArchitectureHandler]] = {
    "modular_monolith": ModularMonolithHandler,
    "service_layer": ServiceLayerHandler,
    "fullstack_htmx": FullStackHTMXHandler,
    "lightweight": LightweightHandler,
}

__all__ = [
    "ARCHITECTURE_HANDLERS",
    "ArchitectureHandler",
    "FullStackHTMXHandler",
    "LightweightHandler",
    "ModularMonolithHandler",
    "ServiceLayerHandler",
]
