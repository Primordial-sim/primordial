"""Evento de nacimiento de una persona.

MIGRACIÓN HEXAGONAL:
- Coordenadas (x, y) → (q, r)
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PersonBornEvent:
    """Evento publicado cuando nace un nuevo agente.

    Attributes:
        entity_id: ID único del nuevo agente.
        mother_id: ID de la madre.
        father_id: ID del padre (puede ser None).
        q: Coordenada Q de nacimiento (hexagonal).
        r: Coordenada R de nacimiento (hexagonal).
        gender: Género del agente ("M" o "F").
        tick: Tick de simulación en que ocurrió el nacimiento.
    """

    entity_id: int
    mother_id: int
    father_id: int
    q: int
    r: int
    gender: str
    tick: int