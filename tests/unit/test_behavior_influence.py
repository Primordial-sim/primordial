"""Tests unitarios para BehaviorInfluence.

Verifica que las etiquetas relacionales influyen correctamente en:
- Prioridad de targets para interacción social
- Atracción/repulsión social para movimiento
- Anclas sociales para decisiones de movimiento
"""

import pytest
from unittest.mock import MagicMock

from systems.relationships.behavior_influence import BehaviorInfluence


def _create_mock_agent(entity_id: int):
    """Crea un agente mock para tests."""
    agent = MagicMock()
    agent.entity_id = entity_id
    agent.x = 0.0
    agent.y = 0.0
    return agent


def _create_mock_relationship(labels: list):
    """Crea una relación mock con etiquetas específicas."""
    rel = MagicMock()
    rel.get_labels.return_value = labels
    return rel


class TestBehaviorInfluenceTargetPriority:
    """Tests de influencia en selección de targets."""

    def test_no_relationship_returns_default(self):
        """Sin relación, retorna prioridad por defecto (0.5)."""
        agent = _create_mock_agent(1)
        target = _create_mock_agent(2)
        agent.get_relationship_with.return_value = None
        
        priority = BehaviorInfluence.get_target_priority(agent, target, 0.0)
        assert priority == 0.5

    def test_amante_highest_priority(self):
        """La etiqueta 'Amante' tiene la máxima prioridad (2.0)."""
        agent = _create_mock_agent(1)
        target = _create_mock_agent(2)
        rel = _create_mock_relationship(["Amante"])
        agent.get_relationship_with.return_value = rel
        
        priority = BehaviorInfluence.get_target_priority(agent, target, 0.0)
        assert priority == 2.0

    def test_amigo_high_priority(self):
        """La etiqueta 'Amigo' tiene prioridad alta (1.8)."""
        agent = _create_mock_agent(1)
        target = _create_mock_agent(2)
        rel = _create_mock_relationship(["Amigo"])
        agent.get_relationship_with.return_value = rel
        
        priority = BehaviorInfluence.get_target_priority(agent, target, 0.0)
        assert priority == 1.8

    def test_enemigo_low_priority(self):
        """La etiqueta 'Enemigo' tiene prioridad baja (0.3)."""
        agent = _create_mock_agent(1)
        target = _create_mock_agent(2)
        rel = _create_mock_relationship(["Enemigo"])
        agent.get_relationship_with.return_value = rel
        
        priority = BehaviorInfluence.get_target_priority(agent, target, 0.0)
        assert priority == 0.3

    def test_multiple_labels_uses_highest(self):
        """Con múltiples etiquetas, usa la de mayor prioridad."""
        agent = _create_mock_agent(1)
        target = _create_mock_agent(2)
        rel = _create_mock_relationship(["Amigo", "Aliado", "Conocido"])
        agent.get_relationship_with.return_value = rel
        
        priority = BehaviorInfluence.get_target_priority(agent, target, 0.0)
        assert priority == 1.8  # Amigo es la más alta


class TestBehaviorInfluenceSocialAttraction:
    """Tests de influencia en movimiento (atracción social)."""

    def test_no_relationship_zero_attraction(self):
        """Sin relación, atracción social es 0.0."""
        agent = _create_mock_agent(1)
        target = _create_mock_agent(2)
        agent.get_relationship_with.return_value = None
        
        attraction = BehaviorInfluence.get_social_attraction(agent, target, 0.0)
        assert attraction == 0.0

    def test_amante_strong_attraction(self):
        """'Amante' produce fuerte atracción (10.0)."""
        agent = _create_mock_agent(1)
        target = _create_mock_agent(2)
        rel = _create_mock_relationship(["Amante"])
        agent.get_relationship_with.return_value = rel
        
        attraction = BehaviorInfluence.get_social_attraction(agent, target, 0.0)
        assert attraction == 10.0

    def test_enemigo_repulsion(self):
        """'Enemigo' produce repulsión (-5.0)."""
        agent = _create_mock_agent(1)
        target = _create_mock_agent(2)
        rel = _create_mock_relationship(["Enemigo"])
        agent.get_relationship_with.return_value = rel
        
        attraction = BehaviorInfluence.get_social_attraction(agent, target, 0.0)
        assert attraction == -5.0

    def test_conocido_mild_attraction(self):
        """'Conocido' produce atracción leve (2.0)."""
        agent = _create_mock_agent(1)
        target = _create_mock_agent(2)
        rel = _create_mock_relationship(["Conocido"])
        agent.get_relationship_with.return_value = rel
        
        attraction = BehaviorInfluence.get_social_attraction(agent, target, 0.0)
        assert attraction == 2.0


class TestBehaviorInfluenceSocialAnchors:
    """Tests de anclas sociales para decisiones de movimiento."""

    def test_empty_agents_returns_empty(self):
        """Sin agentes, retorna lista vacía."""
        agent = _create_mock_agent(1)
        anchors = BehaviorInfluence.get_multiple_social_anchors(agent, [], 0.0)
        assert anchors == []

    def test_excludes_self(self):
        """Excluye al propio agente de las anclas."""
        agent = _create_mock_agent(1)
        other = _create_mock_agent(1)  # Mismo ID
        anchors = BehaviorInfluence.get_multiple_social_anchors(agent, [other], 0.0)
        assert anchors == []

    def test_returns_top_anchors_sorted(self):
        """Retorna las N anclas más importantes ordenadas."""
        agent = _create_mock_agent(1)
        
        # Crear 5 agentes con diferentes etiquetas
        agents = []
        for i, label in enumerate(["Amante", "Amigo", "Conocido", "Enemigo", "Aliado"]):
            other = _create_mock_agent(i + 10)
            rel = _create_mock_relationship([label])
            other.get_relationship_with = lambda eid, day, r=rel: r
            agents.append(other)
        
        # El agente 1 necesita get_relationship_with para cada uno
        def mock_get_rel(target_id, day):
            for other in agents:
                if other.entity_id == target_id:
                    return other.get_relationship_with(target_id, day)
            return None
        agent.get_relationship_with = mock_get_rel
        
        anchors = BehaviorInfluence.get_multiple_social_anchors(agent, agents, 0.0, max_anchors=3)
        
        assert len(anchors) == 3
        # Deben estar ordenados por peso (Amante > Amigo > Aliado)
        assert anchors[0][1] >= anchors[1][1] >= anchors[2][1]