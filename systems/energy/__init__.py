"""Sistema de Energía.

Sistema que gestiona el metabolismo energético de los organismos.
La energía es el recurso fundamental de la vida: sin energía,
no hay movimiento, reproducción ni supervivencia.

Filosofía:
- La energía se gana por alimentación (según dieta)
- La energía se gasta por metabolismo basal y actividad
- Sin energía, el organismo muere por inanición
"""

from systems.energy.energy_system import EnergySystem

__all__ = [
    "EnergySystem",
]