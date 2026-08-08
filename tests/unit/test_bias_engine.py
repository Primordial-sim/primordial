"""Tests unitarios para BiasEngine.apply_biases().

Verifica que los sesgos cognitivos modifican el peso de las memorias:
- Sesgo de confirmación
- Efecto halo
- Recencia
- Idealización post-mortem
- Sesgo de negatividad
"""

import pytest
from typing import Optional
from unittest.mock import MagicMock

from systems.relationships.relationship_model import (
    BiasEngine,
    MemoryCategory,
    MemoryRole,
    PersonalMemory,
    Relationship,
    Narrative,
)


def _create_test_memory(
    weight: float = 50.0,
    valence: float = 1.0,
    category: MemoryCategory = MemoryCategory.COOPERATION,
    day: float = 0.0,
    context: str = "test",
) -> PersonalMemory:
    """Crea una memoria de prueba para los tests de sesgos."""
    return PersonalMemory(
        world_event_id=1,
        owner_id=1,
        partner_id=2,
        perceived_intensity=0.5,
        emotional_valence=valence,
        personal_weight=weight,
        category=category,
        day=day,
        context=context,
        event_type="cooperation",
        source_system="test",
        role=MemoryRole.NORMAL,
        half_life_days=90.0,
    )


def _create_test_relationship(
    memories: Optional[list] = None,
    narratives: Optional[list] = None,
    partner_deceased: bool = False,
    start_day: float = 0.0,
) -> Relationship:
    """Crea una relación de prueba para los tests de sesgos."""
    rel = Relationship(owner_id=1, partner_id=2, start_day=start_day)
    if memories:
        rel.memories = memories
    if narratives:
        rel.my_narratives = narratives
    rel.partner_is_deceased = partner_deceased
    return rel


def _create_test_agent(sociability: float = 0.5, temperament: float = 0.5) -> MagicMock:
    """Crea un agente mock para los tests de sesgos."""
    agent = MagicMock()
    agent.genome.sociability = sociability
    agent.genome.temperament = temperament
    agent.emotions = {"happiness": 0.5, "stress": 0.0, "energy": 1.0}
    agent.memory = {}
    return agent


class TestBiasEngine:
    """Tests del motor de sesgos cognitivos."""

    def test_returns_float(self):
        """apply_biases retorna un valor numérico."""
        memory = _create_test_memory()
        rel = _create_test_relationship()
        agent = _create_test_agent()
        
        result = BiasEngine.apply_biases(memory, agent, rel, current_day=0.0)
        assert isinstance(result, (int, float))

    def test_positive_memory_with_positive_narrative_amplified(self):
        """Sesgo de confirmación: memoria positiva + narrativa positiva = amplificación."""
        memory = _create_test_memory(weight=50.0, valence=1.0)
        narrative = Narrative(
            pattern="Siempre me ayuda",
            strength=0.8,
            last_confirmed=0.0,
        )
        rel = _create_test_relationship(narratives=[narrative])
        agent = _create_test_agent()
        
        result = BiasEngine.apply_biases(memory, agent, rel, current_day=0.0)
        # Con sesgo de confirmación, el peso debería ser mayor que el original
        assert result > 50.0

    def test_negative_memory_with_negative_narrative_amplified(self):
        """Sesgo de confirmación: memoria negativa + narrativa negativa = amplificación."""
        memory = _create_test_memory(
            weight=50.0, valence=-1.0,
            category=MemoryCategory.CONFLICT,
        )
        narrative = Narrative(
            pattern="Siempre me falla",
            strength=0.8,
            last_confirmed=0.0,
        )
        rel = _create_test_relationship(narratives=[narrative])
        agent = _create_test_agent()
        
        result = BiasEngine.apply_biases(memory, agent, rel, current_day=0.0)
        assert result > 50.0

    def test_negativity_bias_amplifies_negative(self):
        """Sesgo de negatividad: las memorias negativas se amplifican."""
        memory_negative = _create_test_memory(weight=50.0, valence=-1.0)
        memory_positive = _create_test_memory(weight=50.0, valence=1.0)
        rel = _create_test_relationship()
        agent = _create_test_agent()
        
        result_negative = BiasEngine.apply_biases(memory_negative, agent, rel, current_day=0.0)
        result_positive = BiasEngine.apply_biases(memory_positive, agent, rel, current_day=0.0)
        
        # La memoria negativa debería tener mayor peso final por el sesgo de negatividad
        assert result_negative > result_positive

    def test_post_mortem_idealization_reduces_negative(self):
        """Idealización post-mortem: memorias negativas se reducen si la pareja falleció."""
        memory_negative = _create_test_memory(weight=50.0, valence=-1.0)
        rel_deceased = _create_test_relationship(partner_deceased=True)
        rel_alive = _create_test_relationship(partner_deceased=False)
        agent = _create_test_agent()
        
        result_deceased = BiasEngine.apply_biases(memory_negative, agent, rel_deceased, current_day=0.0)
        result_alive = BiasEngine.apply_biases(memory_negative, agent, rel_alive, current_day=0.0)
        
        # Con la pareja fallecida, las memorias negativas se reducen
        assert result_deceased < result_alive

    def test_recency_recent_memory_stronger(self):
        """Recencia: memorias más recientes tienen más peso."""
        memory_recent = _create_test_memory(weight=50.0, day=0.0)
        memory_old = _create_test_memory(weight=50.0, day=-300.0)
        rel = _create_test_relationship()
        agent = _create_test_agent()
        
        current_day = 0.0
        result_recent = BiasEngine.apply_biases(memory_recent, agent, rel, current_day=current_day)
        result_old = BiasEngine.apply_biases(memory_old, agent, rel, current_day=current_day)
        
        assert result_recent > result_old

    def test_betrayal_context_extra_negativity(self):
        """Contextos de traición amplifican aún más la negatividad."""
        memory_betrayal = _create_test_memory(
            weight=50.0, valence=-1.0,
            context="traicion_calculada",
        )
        memory_generic_negative = _create_test_memory(
            weight=50.0, valence=-1.0,
            context="desacuerdo",
        )
        rel = _create_test_relationship()
        agent = _create_test_agent()
        
        result_betrayal = BiasEngine.apply_biases(memory_betrayal, agent, rel, current_day=0.0)
        result_generic = BiasEngine.apply_biases(memory_generic_negative, agent, rel, current_day=0.0)
        
        assert result_betrayal > result_generic

    def test_weight_never_negative_after_biases(self):
        """El peso final nunca debe ser negativo tras aplicar sesgos."""
        for valence in [-1.0, -0.5, 0.0, 0.5, 1.0]:
            memory = _create_test_memory(weight=10.0, valence=valence)
            rel = _create_test_relationship()
            agent = _create_test_agent()
            
            result = BiasEngine.apply_biases(memory, agent, rel, current_day=0.0)
            assert result >= 0.0, f"Peso negativo con valencia {valence}: {result}"