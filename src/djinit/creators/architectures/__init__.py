from __future__ import annotations

from djinit.creators.architectures.base import ArchitectureHandler
from djinit.creators.architectures.ddd import DDDHandler
from djinit.creators.architectures.fullstack_htmx import FullStackHTMXHandler
from djinit.creators.architectures.lightweight import LightweightHandler
from djinit.creators.architectures.modular_monolith import ModularMonolithHandler
from djinit.creators.architectures.service_layer import ServiceLayerHandler

ARCHITECTURE_HANDLERS: dict[str, type[ArchitectureHandler]] = {
    "modular_monolith": ModularMonolithHandler,
    "service_layer": ServiceLayerHandler,
    "fullstack_htmx": FullStackHTMXHandler,
    "lightweight": LightweightHandler,
    "ddd": DDDHandler,
}

__all__ = [
    "ARCHITECTURE_HANDLERS",
    "ArchitectureHandler",
    "DDDHandler",
    "FullStackHTMXHandler",
    "LightweightHandler",
    "ModularMonolithHandler",
    "ServiceLayerHandler",
]
