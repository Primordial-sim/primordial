"""Tests unitarios para MortalitySystem.

Verifica:
- Cálculo de riesgo multifactorial
- Límite biológico absoluto (hard cap)
- Penalización por enfermedades activas
"""

import pytest
from unittest.mock import MagicMock

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from systems.mortality.mortality_system import MortalitySystem


def _create_mock_person_for_mortality(
    entity_id: int,
    age: float = 10000.0,
    is_sick: bool = False,
    energy: float = 1.0,
    stress: float = 0.0,
):
    """Crea un agente mock para tests de mortalidad."""
    person = MagicMock()
    person.entity_id = entity_id
    person.age = age
    person.is_sick = is_sick
    person.emotions = {"energy": energy, "stress": stress}
    person.memory = {}
    person.parents = []
    person.adoptive_parents = []
    person.children_count = 0
    person.reputation_score = 0.5
    
    genome = MagicMock()
    genome.get_trait_value.return_value = 1.0
    person.genome = genome
    
    if is_sick:
        pathogen = MagicMock()
        pathogen.lethality = 0.5
        pathogen.virulence = 0.5
        pathogen.pathogen_id = "test_virus"
        person.active_pathogens = {"test": pathogen}
    else:
        person.active_pathogens = {}
        
    return person


class TestMortalitySystemRisk:
    """Tests de cálculo de riesgo de mortalidad."""

    def test_calculate_multifactorial_risk_base(self):
        """El riesgo base debe ser > 0 incluso para agentes sanos."""
        config = SimulationConfig()
        system = MortalitySystem(config)
        
        person = _create_mock_person_for_mortality(1, age=10000.0, is_sick=False)
        
        risk = system._calculate_multifactorial_risk(person, pressure=1.0)
        assert risk > 0.0, "El riesgo base de mortalidad debe ser mayor que 0"

    def test_sickness_penalty_increases_risk(self):
        """Estar enfermo debe aumentar significativamente el riesgo."""
        config = SimulationConfig()
        system = MortalitySystem(config)
        
        healthy_person = _create_mock_person_for_mortality(1, age=10000.0, is_sick=False)
        sick_person = _create_mock_person_for_mortality(2, age=10000.0, is_sick=True)
        
        risk_healthy = system._calculate_multifactorial_risk(healthy_person, pressure=1.0)
        risk_sick = system._calculate_multifactorial_risk(sick_person, pressure=1.0)
        
        assert risk_sick > risk_healthy, "El riesgo con enfermedad debe ser mayor que el riesgo sano"

    def test_low_energy_increases_risk(self):
        """Baja energía debe aumentar el riesgo."""
        config = SimulationConfig()
        system = MortalitySystem(config)
        
        person_high_energy = _create_mock_person_for_mortality(1, age=10000.0, energy=1.0)
        person_low_energy = _create_mock_person_for_mortality(2, age=10000.0, energy=0.1)
        
        risk_high = system._calculate_multifactorial_risk(person_high_energy, pressure=1.0)
        risk_low = system._calculate_multifactorial_risk(person_low_energy, pressure=1.0)
        
        assert risk_low > risk_high, "Baja energía debe aumentar el riesgo de mortalidad"


class TestMortalitySystemHardCap:
    """Tests del límite biológico absoluto."""

    def test_hard_cap_age_triggers_death(self):
        """Si la edad supera el hard_cap * longevidad, se registra la muerte."""
        config = SimulationConfig()
        config.mortality.hard_cap_age_days = 40000.0
        system = MortalitySystem(config)
        
        # Persona con longevidad 1.0 y edad 41000 (supera el cap de 40000)
        person = _create_mock_person_for_mortality(1, age=41000.0)
        person.genome.get_trait_value.return_value = 1.0
        
        state = MagicMock()
        state.world_days_elapsed = 0.0
        state.get_all_persons.return_value = [person]
        
        pending = PendingChanges()
        context = MagicMock()
        context.get_local_pressure.return_value = 1.0
        
        system.process(state, pending, 1.0, context)
        
        # Debe haber sido registrada la muerte
        assert 1 in pending.deaths
        assert "Degradación telomérica total" in pending.deaths[1]