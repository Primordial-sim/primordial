"""Test de integración real para el sistema de influencia parental.

Verifica el flujo completo de extremo a extremo sin mocks:
- Creación real de Person y Genome
- Registro real en GenealogySystem
- Ejecución real de ParentalInfluenceSystem
- Verificación de que las emociones del hijo se mueven hacia las del padre
"""

import pytest

from core.config.simulation_config import SimulationConfig
from core.state.world_state import WorldState
from core.state.pending_changes import PendingChanges
from systems.environment.environment_context import EnvironmentContext
from systems.genealogy.genealogy_system import GenealogySystem
from systems.behavior.parental_influence_system import ParentalInfluenceSystem
from entities.person.person import Person
from entities.person.genome import Genome


class TestParentalInfluenceIntegration:
    """Tests de integración del sistema de influencia parental con objetos reales."""

    def test_real_person_influence_flow(self):
        """El sistema modifica las emociones de un hijo real basándose en su padre real."""
        # 1. Configuración y estado inicial
        config = SimulationConfig()
        config.parental_influence.max_influence_age_days = 5000.0
        config.parental_influence.base_personality_plasticity = 0.1
        
        state = WorldState(config=config, width=100, height=100)
        pending = PendingChanges()
        context = EnvironmentContext(state=state, config=config)
        
        # 2. Crear padre real (adulto, calmado y feliz)
        father = Person(
            config=config,
            entity_id=1,
            x=50,
            y=50,
            age=10000.0,  # Adulto
            species="human",
        )
        father._emotions["stress"] = 0.2
        father._emotions["happiness"] = 0.8
        state.add_person(father)
        
        # 3. Crear hijo real (bebé, estresado e infeliz)
        child = Person(
            config=config,
            entity_id=2,
            x=50,
            y=50,
            age=0.0,  # Recién nacido
            species="human",
        )
        child.set_parents(mother_id=99, father_id=1)  # Padre es entity_id=1
        child._emotions["stress"] = 0.7
        child._emotions["happiness"] = 0.3
        state.add_person(child)
        
        # 4. Inicializar y ejecutar GenealogySystem para registrar la relación
        genealogy_system = GenealogySystem(config=config)
        genealogy_system.process(state, pending, delta_days=1.0, context=context)
        
        # Verificar que el genealogy system registró la relación
        child_node = genealogy_system.registry.get(2)
        assert child_node is not None
        assert 1 in child_node.biological_parents
        
        # 5. Inicializar y ejecutar ParentalInfluenceSystem
        influence_system = ParentalInfluenceSystem(
            config=config,
            genealogy_system=genealogy_system,
        )
        
        initial_stress = child._emotions["stress"]
        initial_happiness = child._emotions["happiness"]
        
        influence_system.process(state, pending, delta_days=1.0, context=context)
        
        # 6. Verificar que las emociones del hijo se movieron hacia las del padre
        assert child._emotions["stress"] < initial_stress, \
            f"El estrés del hijo debería bajar, pero fue {initial_stress} -> {child._emotions['stress']}"
        
        assert child._emotions["happiness"] > initial_happiness, \
            f"La felicidad del hijo debería subir, pero fue {initial_happiness} -> {child._emotions['happiness']}"
            
        # 7. Verificar que se generó un evento en pending
        events = getattr(pending, 'parental_influences', [])
        assert len(events) > 0, "Debería haber al menos un evento de influencia parental"
        
        stress_event = next((e for e in events if e.trait_modified == "emotion_stress"), None)
        assert stress_event is not None
        assert stress_event.child_id == 2
        assert stress_event.parent_id == 1
        assert stress_event.delta < 0

    def test_adoptive_parent_real_influence(self):
        """Un padre adoptivo real también influye en las emociones del hijo."""
        # 1. Configuración y estado inicial
        config = SimulationConfig()
        config.parental_influence.max_influence_age_days = 5000.0
        config.parental_influence.base_personality_plasticity = 0.1
        
        state = WorldState(config=config, width=100, height=100)
        pending = PendingChanges()
        context = EnvironmentContext(state=state, config=config)
        
        # Padre adoptivo (muy feliz)
        adoptive_parent = Person(
            config=config,
            entity_id=10,
            x=50,
            y=50,
            age=15000.0,
            species="human",
        )
        adoptive_parent._emotions["happiness"] = 0.9
        state.add_person(adoptive_parent)
        
        # Hijo adoptado (poco feliz)
        child = Person(
            config=config,
            entity_id=11,
            x=50,
            y=50,
            age=500.0,
            species="human",
        )
        child._emotions["happiness"] = 0.3
        child._adoptive_parents.append(10)
        state.add_person(child)
        
        # Genealogy
        genealogy_system = GenealogySystem(config=config)
        genealogy_system.process(state, pending, delta_days=1.0, context=context)
        
        # Influencia
        influence_system = ParentalInfluenceSystem(
            config=config,
            genealogy_system=genealogy_system,
        )
        
        initial_happiness = child._emotions["happiness"]
        influence_system.process(state, pending, delta_days=1.0, context=context)
        
        # La felicidad del hijo debería haber subido
        assert child._emotions["happiness"] > initial_happiness