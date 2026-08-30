"""Tests unitarios para DiseaseSystem.

Verifica:
- Los brotes espontáneos se evalúan UNA VEZ por tick (no por agente)
- El contagio local requiere carga viral en el sector
"""

import pytest
from unittest.mock import MagicMock

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from systems.diseases.disease_system import DiseaseSystem
from systems.diseases.pathogen import Pathogen


def _create_mock_person(entity_id: int, is_sick: bool = False, x: float = 50.0, y: float = 50.0):
    """Crea un agente mock para tests de enfermedades."""
    person = MagicMock()
    person.entity_id = entity_id
    person.is_sick = is_sick
    person.x = x
    person.y = y
    person.active_infections = {}
    person.genome = MagicMock()
    
    # GENÉTICA UNIVERSAL: Configurar mocks para ImmunologicalCapabilities
    # has_trait() debe retornar True para que se consulten los rasgos
    person.genome.has_trait.return_value = True
    # get_trait_value() retorna 0.5 por defecto (inmunidad normal, puede enfermarse)
    person.genome.get_trait_value.return_value = 0.5
    
    person.emotions = {"energy": 1.0}
    person.get_specific_immunity = MagicMock(return_value=0.5)
    return person


class TestDiseaseSystemOutbreaks:
    """Tests de brotes espontáneos."""

    def test_outbreak_evaluated_once_per_tick(self):
        """REGRESIÓN: Con 100 agentes y 1.5% de probabilidad, no debe haber ~100 infecciones.
        
        Si el bug del bucle vuelve, se generarían ~1-2 infecciones POR AGENTE.
        Si está fuera del bucle, deberían ser 0-3 infecciones en total.
        """
        config = SimulationConfig()
        config.diseases.base_outbreak_chance = 1.5
        
        system = DiseaseSystem(config)
        
        # Crear estado con 100 agentes sanos
        state = MagicMock()
        state.world_days_elapsed = 0.0
        persons = [_create_mock_person(i) for i in range(100)]
        state.get_all_persons.return_value = persons
        
        pending = PendingChanges()
        context = MagicMock()
        context.get_local_pressure.return_value = 1.0
        
        # Ejecutar el sistema UNA VEZ (1 tick)
        system.process(state, pending, 1.0, context)
        
        # Contar cuántas infecciones se registraron
        infection_count = len(pending.infections)
        
        # Con 100 agentes y 1.5% evaluado UNA VEZ, lo máximo razonable es 1-3 brotes.
        assert infection_count <= 5, (
            f"Se registraron {infection_count} infecciones en 1 tick con 100 agentes. "
            "Esto sugiere que el brote se está evaluando dentro del bucle de agentes."
        )


class TestDiseaseSystemLocalContagion:
    """Tests de contagio local por carga viral."""

    def test_no_contagion_without_viral_load(self):
        """Sin carga viral en el sector, no debe haber contagios."""
        config = SimulationConfig()
        config.environment.sector_size = 10
        config.diseases.base_outbreak_chance = 0.0
        system = DiseaseSystem(config)
        
        state = MagicMock()
        state.world_days_elapsed = 0.0
        # Agente sano en sector sin carga viral
        persons = [_create_mock_person(1, is_sick=False)]
        state.get_all_persons.return_value = persons
        
        pending = PendingChanges()
        context = MagicMock()
        context.get_local_pressure.return_value = 1.0
        
        system.process(state, pending, 1.0, context)
        
        # No debe haber infecciones nuevas
        assert len(pending.infections) == 0

    def test_contagion_with_high_viral_load(self):
        """Con alta carga viral en el sector, debe haber probabilidad de contagio."""
        config = SimulationConfig()
        config.environment.sector_size = 10
        config.diseases.base_transmission_chance = 0.5  # Alta probabilidad para el test
        system = DiseaseSystem(config)
        
        state = MagicMock()
        state.world_days_elapsed = 0.0
        
        # Agente enfermo que genera carga viral
        sick_person = _create_mock_person(1, is_sick=True, x=5.0, y=5.0)
        sick_person.active_infections = {
            "test_pathogen": MagicMock(
                pathogen=Pathogen.create_random_variant("Influenza"),
                is_contagious=MagicMock(return_value=True),
                get_transmission_multiplier=MagicMock(return_value=1.0)
            )
        }
        
        # Agente sano en el mismo sector
                # Agente sano en el mismo sector
        healthy_person = _create_mock_person(2, is_sick=False, x=5.0, y=5.0)
        
        # GENÉTICA UNIVERSAL: Configurar valores específicos por rasgo
        # Usamos side_effect para retornar valores diferentes según el rasgo consultado
        def get_trait_side_effect(trait_id):
            """Retorna valores específicos para cada rasgo."""
            if trait_id == "immunity":
                return 0.1  # Baja inmunidad para facilitar contagio
            elif trait_id == "nervous_system":
                return 0.5  # Necesario para ser susceptible a virus
            elif trait_id == "metabolism":
                return 0.5  # Necesario para poder enfermarse
            elif trait_id == "heterotrophy":
                return 0.5  # Necesario para ser susceptible
            else:
                return 0.5  # Default para otros rasgos
        
        healthy_person.genome.has_trait.return_value = True
        healthy_person.genome.get_trait_value.side_effect = get_trait_side_effect

        state.get_all_persons.return_value = [sick_person, healthy_person]
        
        pending = PendingChanges()
        context = MagicMock()
        context.get_local_pressure.return_value = 2.0  # Alta presión
        
        # Ejecutar varias veces para superar la aleatoriedad
        for _ in range(20):
            pending.infections = []
            system.process(state, pending, 1.0, context)
            if len(pending.infections) > 0:
                break
        
        # Debería haber al menos 1 infección tras 20 intentos con alta probabilidad
        assert len(pending.infections) > 0, "No se produjo contagio a pesar de alta carga viral y baja inmunidad"