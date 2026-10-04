"""Tests unitarios para el sistema de influencia parental."""

from unittest.mock import Mock, MagicMock
import pytest

from core.config.simulation_config import SimulationConfig
from core.state.world_state import WorldState
from core.state.pending_changes import PendingChanges
from systems.environment.environment_context import EnvironmentContext
from systems.behavior.parental_influence_system import ParentalInfluenceSystem


class TestParentalInfluenceSystem:
    """Tests del sistema de influencia parental."""

    def test_system_initialization(self):
        """El sistema se instancia correctamente con config y genealogy."""
        config = SimulationConfig()
        genealogy = Mock()
        system = ParentalInfluenceSystem(config=config, genealogy_system=genealogy)
        
        assert system.config is config
        assert system.genealogy_system is genealogy
        assert system._log_counter == 0.0
        assert system._log_interval == 365

    def test_plasticity_decreases_with_age(self):
        """La plasticidad decrece linealmente con la edad."""
        config = SimulationConfig()
        config.parental_influence.max_influence_age_days = 1000.0
        config.parental_influence.base_personality_plasticity = 0.1
        
        system = ParentalInfluenceSystem(config=config)
        
        # Crear agente joven (alta plasticidad)
        young_agent = Mock()
        young_agent.entity_id = 1
        young_agent.birth_tick = 0.0
        young_agent.temperament = 0.5
        young_agent.sociability = 0.5
        young_agent.stress_level = 0.5
        young_agent.get_relationship_with.return_value = None
        
        # Crear padre
        parent = Mock()
        parent.entity_id = 2
        parent.temperament = 0.8
        parent.sociability = 0.9
        parent.stress_level = 0.3
        parent.is_alive = True
        young_agent.biological_parents = [2]
        
        state = Mock()
        state.world_days_elapsed = 100.0  # Edad joven, alta plasticidad
        state.get_all_persons.return_value = [young_agent]
        state.get_person_by_id.return_value = parent
        
        pending = PendingChanges()
        context = Mock()
        
        initial_temperament = young_agent.temperament
        
        # Ejecutar
        system.process(state, pending, delta_days=1.0, context=context)
        
        # El agente joven (edad 100, límite 1000) debería tener plasticidad alta
        # y sus rasgos deberían haber cambiado
        assert young_agent.temperament > initial_temperament

    def test_traits_move_toward_parent(self):
        """Los rasgos del hijo se mueven hacia los del padre."""
        config = SimulationConfig()
        config.parental_influence.max_influence_age_days = 5000.0
        config.parental_influence.base_personality_plasticity = 0.1
        
        system = ParentalInfluenceSystem(config=config)
        
        # Hijo con valores bajos
        child = Mock()
        child.entity_id = 1
        child.birth_tick = 0.0
        child.temperament = 0.3
        child.sociability = 0.4
        child.stress_level = 0.6
        child.get_relationship_with.return_value = None
        child.biological_parents = [2]
        
        # Padre con valores altos
        parent = Mock()
        parent.entity_id = 2
        parent.temperament = 0.8
        parent.sociability = 0.9
        parent.stress_level = 0.2
        parent.is_alive = True
        
        state = Mock()
        state.world_days_elapsed = 100.0
        state.get_all_persons.return_value = [child]
        state.get_person_by_id.return_value = parent
        
        pending = PendingChanges()
        context = Mock()
        
        initial_temperament = child.temperament
        initial_sociability = child.sociability
        
        # Ejecutar
        system.process(state, pending, delta_days=1.0, context=context)
        
        # Los rasgos deberían haberse movido hacia el padre
        assert child.temperament > initial_temperament
        assert child.sociability > initial_sociability

    def test_emotional_climate_affects_influence(self):
        """El clima emocional afecta la magnitud de la influencia."""
        config = SimulationConfig()
        config.parental_influence.max_influence_age_days = 5000.0
        config.parental_influence.base_personality_plasticity = 0.1
        
        system = ParentalInfluenceSystem(config=config)
        
        # Hijo
        child = Mock()
        child.entity_id = 1
        child.birth_tick = 0.0
        child.temperament = 0.5
        child.sociability = 0.5
        child.stress_level = 0.5
        child.biological_parents = [2]
        
        # Padre con clima cálido (etiqueta "Familia Elegida")
        parent_warm = Mock()
        parent_warm.entity_id = 2
        parent_warm.temperament = 0.9
        parent_warm.sociability = 0.9
        parent_warm.stress_level = 0.2
        parent_warm.is_alive = True
        
        # Mock de relación con etiqueta positiva
        rel_warm = Mock()
        rel_warm.get_labels.return_value = ["Familia Elegida"]
        child.get_relationship_with.return_value = rel_warm
        
        state = Mock()
        state.world_days_elapsed = 100.0
        state.get_all_persons.return_value = [child]
        state.get_person_by_id.return_value = parent_warm
        
        pending = PendingChanges()
        context = Mock()
        
        initial_temperament = child.temperament
        
        # Ejecutar con clima cálido
        system.process(state, pending, delta_days=1.0, context=context)
        
        # Con clima cálido, la influencia debería ser mayor
        warm_delta = child.temperament - initial_temperament
        assert warm_delta > 0

    def test_adoptive_parents_also_influence(self):
        """Los padres adoptivos también influyen en el hijo."""
        config = SimulationConfig()
        config.parental_influence.max_influence_age_days = 5000.0
        config.parental_influence.base_personality_plasticity = 0.1
        
        system = ParentalInfluenceSystem(config=config)
        
        # Hijo con padres adoptivos
        child = Mock()
        child.entity_id = 1
        child.birth_tick = 0.0
        child.temperament = 0.4
        child.sociability = 0.4
        child.stress_level = 0.6
        child.biological_parents = []
        child.adoptive_parents = [3]
        child.get_relationship_with.return_value = None
        
        # Padre adoptivo
        adoptive_parent = Mock()
        adoptive_parent.entity_id = 3
        adoptive_parent.temperament = 0.8
        adoptive_parent.sociability = 0.8
        adoptive_parent.stress_level = 0.3
        adoptive_parent.is_alive = True
        
        state = Mock()
        state.world_days_elapsed = 100.0
        state.get_all_persons.return_value = [child]
        state.get_person_by_id.return_value = adoptive_parent
        
        pending = PendingChanges()
        context = Mock()
        
        initial_temperament = child.temperament
        
        # Ejecutar
        system.process(state, pending, delta_days=1.0, context=context)
        
        # El hijo debería haberse movido hacia el padre adoptivo
        assert child.temperament > initial_temperament

    def test_no_influence_on_adults(self):
        """Los agentes adultos (fuera de max_influence_age) no son afectados."""
        config = SimulationConfig()
        config.parental_influence.max_influence_age_days = 1000.0
        config.parental_influence.base_personality_plasticity = 0.1
        
        system = ParentalInfluenceSystem(config=config)
        
        # Agente adulto
        adult = Mock()
        adult.entity_id = 1
        adult.birth_tick = 0.0
        adult.temperament = 0.5
        adult.sociability = 0.5
        adult.stress_level = 0.5
        adult.biological_parents = [2]
        adult.get_relationship_with.return_value = None
        
        # Padre
        parent = Mock()
        parent.entity_id = 2
        parent.temperament = 0.9
        parent.sociability = 0.9
        parent.stress_level = 0.2
        parent.is_alive = True
        
        state = Mock()
        state.world_days_elapsed = 2000.0  # Muy por encima del límite
        state.get_all_persons.return_value = [adult]
        state.get_person_by_id.return_value = parent
        
        pending = PendingChanges()
        context = Mock()
        
        initial_temperament = adult.temperament
        initial_sociability = adult.sociability
        
        # Ejecutar
        system.process(state, pending, delta_days=1.0, context=context)
        
        # Los rasgos NO deberían haber cambiado
        assert adult.temperament == initial_temperament
        assert adult.sociability == initial_sociability

    def test_events_stored_in_pending(self):
        """Los eventos de influencia se almacenan en pending."""
        config = SimulationConfig()
        config.parental_influence.max_influence_age_days = 5000.0
        config.parental_influence.base_personality_plasticity = 0.1
        
        system = ParentalInfluenceSystem(config=config)
        
        # Hijo
        child = Mock()
        child.entity_id = 1
        child.birth_tick = 0.0
        child.temperament = 0.5
        child.sociability = 0.5
        child.stress_level = 0.5
        child.biological_parents = [2]
        child.get_relationship_with.return_value = None
        
        # Padre
        parent = Mock()
        parent.entity_id = 2
        parent.temperament = 0.8
        parent.sociability = 0.8
        parent.stress_level = 0.3
        parent.is_alive = True
        
        state = Mock()
        state.world_days_elapsed = 100.0
        state.get_all_persons.return_value = [child]
        state.get_person_by_id.return_value = parent
        
        pending = PendingChanges()
        context = Mock()
        
        # Ejecutar
        system.process(state, pending, delta_days=1.0, context=context)
        
        # Debería haber eventos en pending
        events = getattr(pending, 'parental_influences', [])
        assert len(events) > 0
        assert events[0].child_id == 1
        assert events[0].parent_id == 2