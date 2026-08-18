"""Fixtures compartidas para todos los tests del simulador.

Proporciona factories para crear objetos de prueba de forma
consistente y reutilizable.
"""

import random
from typing import Optional

import pytest

from systems.relationships.relationship_model import (
    PersonalMemory,
    MemoryCategory,
    MemoryRole,
    Relationship,
    Narrative,
    SexualOrientation,
)


@pytest.fixture
def make_memory():
    """Factory para crear PersonalMemory con valores personalizados."""
    def _make(
        weight: float = 100.0,
        day: float = 0.0,
        half_life: float = 90.0,
        category: MemoryCategory = MemoryCategory.COOPERATION,
        valence: float = 1.0,
        role: MemoryRole = MemoryRole.NORMAL,
        is_landmark: bool = False,
        owner_id: int = 1,
        partner_id: int = 2,
        context: str = "test",
        event_type: str = "cooperation",
    ) -> PersonalMemory:
        return PersonalMemory(
            world_event_id=random.randint(1, 999999),
            owner_id=owner_id,
            partner_id=partner_id,
            perceived_intensity=0.5,
            emotional_valence=valence,
            personal_weight=weight,
            category=category,
            day=day,
            context=context,
            event_type=event_type,
            source_system="test_fixture",
            role=role,
            is_landmark=is_landmark,
            half_life_days=half_life,
        )
    return _make


@pytest.fixture
def make_relationship():
    """Factory para crear Relationship con memorias opcionales."""
    def _make(
        owner_id: int = 1,
        partner_id: int = 2,
        start_day: float = 0.0,
        memories: Optional[list] = None,
    ) -> Relationship:
        rel = Relationship(
            owner_id=owner_id,
            partner_id=partner_id,
            start_day=start_day,
        )
        if memories:
            for mem in memories:
                # CORRECCIÓN: Usar add_memory() para actualizar contadores incrementales
                rel.add_memory(mem, current_day=start_day)
        return rel
    return _make


@pytest.fixture
def make_narrative():
    """Factory para crear Narrative con valores personalizados."""
    def _make(
        pattern: str = "Siempre me ayuda",
        strength: float = 0.8,
        last_confirmed: float = 0.0,
        half_life_days: float = 1825.0,
    ) -> Narrative:
        return Narrative(
            pattern=pattern,
            strength=strength,
            last_confirmed=last_confirmed,
            half_life_days=half_life_days,
        )
    return _make