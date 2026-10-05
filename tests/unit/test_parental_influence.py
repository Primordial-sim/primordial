"""Tests unitarios para el sistema de influencia parental."""

from unittest.mock import Mock
import pytest

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
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
        young_agent._emotions = {"stress": 0.5, "happiness": 0.5}
        young_agent._learned_traits = {}
        young_agent.get_relationship_with.return_value = None
        young_agent.biological_parents = [2]
        
        # Crear padre
        parent = Mock()
        parent.entity_id = 2
        parent._emotions = {"stress": 0.2, "happiness": 0.8}
        parent.stress_level = 0.2
        parent._genome = Mock()
        parent.is_alive = True
        
        state = Mock()
        state.world_days_elapsed = 100.0  # Edad joven, alta plasticidad
        state.get_all_persons.return_value = [young_agent]
        state.get_person_by_id.return_value = parent
        
        pending = PendingChanges()
        context = Mock()
        
        initial_stress = young_agent._emotions["stress"]
        
        # Ejecutar
        system.process(state, pending, delta_days=1.0, context=context)
        
        # El agente joven debería haber cambiado sus emociones
        assert young_agent._emotions["stress"] < initial_stress

    def test_traits_move_toward_parent(self):
        """Los rasgos emocionales del hijo se mueven hacia los del padre."""
        config = SimulationConfig()
        config.parental_influence.max_influence_age_days = 5000.0
        config.parental_influence.base_personality_plasticity = 0.1
        
        system = ParentalInfluenceSystem(config=config)
        
        # Hijo con emociones bajas
        child = Mock()
        child.entity_id = 1
        child.birth_tick = 0.0
        child._emotions = {"stress": 0.7, "happiness": 0.3}
        child._learned_traits = {}
        child.get_relationship_with.return_value = None
        child.biological_parents = [2]
        
        # Padre con emociones altas
        parent = Mock()
        parent.entity_id = 2
        parent._emotions = {"stress": 0.2, "happiness": 0.8}
        parent.stress_level = 0.2
        parent._genome = Mock()
        parent._genome.diet_preference = 0.9
        parent.is_alive = True
        
        state = Mock()
        state.world_days_elapsed = 100.0
        state.get_all_persons.return_value = [child]
        state.get_person_by_id.return_value = parent
        
        pending = PendingChanges()
        context = Mock()
        
        initial_stress = child._emotions["stress"]
        initial_happiness = child._emotions["happiness"]
        
        # Ejecutar
        system.process(state, pending, delta_days=1.0, context=context)
        
        # El estrés debería bajar (hacia el padre) y la felicidad subir
        assert child._emotions["stress"] < initial_stress
        assert child._emotions["happiness"] > initial_happiness

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
        child._emotions = {"stress": 0.5, "happiness": 0.5}
        child._learned_traits = {}
        child.biological_parents = [2]
        
        # Padre con clima cálido (etiqueta "Familia Elegida")
        parent_warm = Mock()
        parent_warm.entity_id = 2
        parent_warm._emotions = {"stress": 0.2, "happiness": 0.8}
        parent_warm.stress_level = 0.2
        parent_warm._genome = Mock()
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
        
        initial_happiness = child._emotions["happiness"]
        
        # Ejecutar con clima cálido
        system.process(state, pending, delta_days=1.0, context=context)
        
        # Con clima cálido, la influencia debería ser mayor
        warm_delta = child._emotions["happiness"] - initial_happiness
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
        child._emotions = {"stress": 0.6, "happiness": 0.4}
        child._learned_traits = {}
        child.biological_parents = []
        child.adoptive_parents = [3]
        child.get_relationship_with.return_value = None
        
        # Padre adoptivo
        adoptive_parent = Mock()
        adoptive_parent.entity_id = 3
        adoptive_parent._emotions = {"stress": 0.3, "happiness": 0.8}
        adoptive_parent.stress_level = 0.3
        adoptive_parent._genome = Mock()
        adoptive_parent.is_alive = True
        
        state = Mock()
        state.world_days_elapsed = 100.0
        state.get_all_persons.return_value = [child]
        state.get_person_by_id.return_value = adoptive_parent
        
        pending = PendingChanges()
        context = Mock()
        
        initial_stress = child._emotions["stress"]
        
        # Ejecutar
        system.process(state, pending, delta_days=1.0, context=context)
        
        # El hijo debería haberse movido hacia el padre adoptivo
        assert child._emotions["stress"] < initial_stress

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
        adult._emotions = {"stress": 0.5, "happiness": 0.5}
        adult._learned_traits = {}
        adult.biological_parents = [2]
        adult.get_relationship_with.return_value = None
        
        # Padre
        parent = Mock()
        parent.entity_id = 2
        parent._emotions = {"stress": 0.2, "happiness": 0.8}
        parent.stress_level = 0.2
        parent._genome = Mock()
        parent.is_alive = True
        
        state = Mock()
        state.world_days_elapsed = 2000.0  # Muy por encima del límite
        state.get_all_persons.return_value = [adult]
        state.get_person_by_id.return_value = parent
        
        pending = PendingChanges()
        context = Mock()
        
        initial_stress = adult._emotions["stress"]
        initial_happiness = adult._emotions["happiness"]
        
        # Ejecutar
        system.process(state, pending, delta_days=1.0, context=context)
        
        # Los rasgos NO deberían haber cambiado
        assert adult._emotions["stress"] == initial_stress
        assert adult._emotions["happiness"] == initial_happiness

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
        child._emotions = {"stress": 0.5, "happiness": 0.5}
        child._learned_traits = {}
        child.biological_parents = [2]
        child.get_relationship_with.return_value = None
        
        # Padre
        parent = Mock()
        parent.entity_id = 2
        parent._emotions = {"stress": 0.3, "happiness": 0.7}
        parent.stress_level = 0.3
        parent._genome = Mock()
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