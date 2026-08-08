"""Tests unitarios para CompatibilityEngine.

Verifica el cálculo de compatibilidad multifactorial:
- Orientación sexual
- Edad
- Distancia
- Afinidad basada en memorias
"""

import pytest
from unittest.mock import MagicMock

from core.config.simulation_config import SimulationConfig
from systems.relationships.compatibility_engine import CompatibilityEngine
from systems.relationships.relationship_model import SexualOrientation


def _create_mock_person(
    entity_id: int,
    age: float = 10000.0,  # ~27 años
    x: float = 0.0,
    y: float = 0.0,
    sexual_orientation: SexualOrientation = SexualOrientation.HETEROSEXUAL,
    gender: str = "M",
    effective_sociability: float = 1.0,
    effective_temperament: float = 1.0,
):
    """Crea una persona mock para tests."""
    person = MagicMock()
    person.entity_id = entity_id
    person.age = age
    person.x = x
    person.y = y
    person.sexual_orientation = sexual_orientation
    person.gender = gender
    person.effective_sociability = effective_sociability
    person.effective_temperament = effective_temperament
    person.get_relationship_with.return_value = None
    return person


class TestCompatibilityEngine:
    """Tests del motor de compatibilidad."""

    def test_returns_value_in_range(self):
        """La compatibilidad siempre está en [0.0, 1.0]."""
        config = SimulationConfig()
        engine = CompatibilityEngine(config)
        
        p1 = _create_mock_person(1)
        p2 = _create_mock_person(2)
        
        compatibility = engine.calculate_compatibility(p1, p2, 0.0)
        assert 0.0 <= compatibility <= 1.0

    def test_incompatible_orientations_zero(self):
        """Orientaciones incompatibles producen compatibilidad 0.0."""
        config = SimulationConfig()
        engine = CompatibilityEngine(config)
        
        p1 = _create_mock_person(1, sexual_orientation=SexualOrientation.HETEROSEXUAL, gender="M")
        p2 = _create_mock_person(2, sexual_orientation=SexualOrientation.HOMOSEXUAL, gender="M")
        
        compatibility = engine.calculate_compatibility(p1, p2, 0.0)
        assert compatibility == 0.0

    def test_same_age_higher_compatibility(self):
        """Misma edad produce mayor compatibilidad que edad diferente."""
        config = SimulationConfig()
        engine = CompatibilityEngine(config)
        
        p1 = _create_mock_person(1, age=10000.0)
        p2_same = _create_mock_person(2, age=10000.0)
        p2_diff = _create_mock_person(3, age=20000.0)  # ~27 años de diferencia
        
        comp_same = engine.calculate_compatibility(p1, p2_same, 0.0)
        comp_diff = engine.calculate_compatibility(p1, p2_diff, 0.0)
        
        assert comp_same > comp_diff

    def test_close_distance_higher_compatibility(self):
        """Distancia corta produce mayor compatibilidad que distancia larga."""
        config = SimulationConfig()
        engine = CompatibilityEngine(config)
        
        p1 = _create_mock_person(1, x=0.0, y=0.0)
        p2_close = _create_mock_person(2, x=5.0, y=5.0)
        p2_far = _create_mock_person(3, x=40.0, y=40.0)
        
        comp_close = engine.calculate_compatibility(p1, p2_close, 0.0)
        comp_far = engine.calculate_compatibility(p1, p2_far, 0.0)
        
        assert comp_close > comp_far

    def test_similar_sociability_higher_compatibility(self):
        """Sociabilidad similar produce mayor compatibilidad."""
        config = SimulationConfig()
        engine = CompatibilityEngine(config)
        
        p1 = _create_mock_person(1, effective_sociability=1.0)
        p2_similar = _create_mock_person(2, effective_sociability=1.0)
        p2_different = _create_mock_person(3, effective_sociability=0.2)
        
        comp_similar = engine.calculate_compatibility(p1, p2_similar, 0.0)
        comp_different = engine.calculate_compatibility(p1, p2_different, 0.0)
        
        assert comp_similar > comp_different

    def test_free_will_boost_increases_compatibility(self):
        """El boost de libre albedrío aumenta la compatibilidad."""
        config = SimulationConfig()
        engine = CompatibilityEngine(config)
        
        p1 = _create_mock_person(1)
        p2 = _create_mock_person(2)
        
        comp_base = engine.calculate_compatibility(p1, p2, 0.0, free_will_boost=0.0)
        comp_boosted = engine.calculate_compatibility(p1, p2, 0.0, free_will_boost=0.3)
        
        assert comp_boosted > comp_base
        assert comp_boosted <= 1.0  # No debe exceder 1.0