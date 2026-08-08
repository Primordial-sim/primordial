"""Tests de regresión para bugs críticos encontrados en auditorías.

Cada test verifica que un bug específico no vuelva a ocurrir.
Estos tests son la red de seguridad del proyecto.

Bugs cubiertos:
1. 7.908 rupturas masivas por affinity/estrés (RelationshipSystem)
2. Brotes espontáneos evaluados dentro del bucle de agentes (DiseaseSystem)
3. register_birth con parámetro 'species' inexistente (GestationSystem)
4. Tuplas de infections/recoveries mal filtradas en DeathResolver
5. base_outbreak_chance demasiado bajo (0.02)
"""

import pytest
from unittest.mock import MagicMock, Mock

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from systems.relationships.relationship_system import RelationshipSystem
from systems.mortality.death_resolver import DeathResolver


class TestBug1_MassiveBreakups:
    """REGRESIÓN: RelationshipSystem no debe tener lógica de ruptura por affinity/estrés.
    
    Bug histórico: RelationshipSystem con lógica lineal causaba miles de rupturas
    en pocos ticks. Ahora es un stub vacío.
    """
    
    def test_relationship_system_process_is_noop(self):
        """El método process de RelationshipSystem no debe modificar el estado."""
        config = SimulationConfig()
        system = RelationshipSystem(config)
        
        state = MagicMock()
        state.get_all_persons.return_value = []
        pending = PendingChanges()
        context = MagicMock()
        
        # Ejecutar el sistema
        system.process(state, pending, 1.0, context)
        
        # No debe haber añadido nada a pending (ni divorces, ni rupturas)
        # Si tuviera lógica antigua, podría haber añadido algo
        assert len(pending.deaths) == 0
        # Nota: pending no tiene atributo 'divorces' explícito en la versión actual,
        # pero verificamos que no haya efectos colaterales.

    def test_relationship_system_has_no_check_breakup(self):
        """RelationshipSystem no debe tener el método _check_breakup."""
        config = SimulationConfig()
        system = RelationshipSystem(config)
        
        # Si alguien reintroduce la lógica lineal, volverá a tener este método
        assert not hasattr(system, '_check_breakup'), \
            "RelationshipSystem no debe tener _check_breakup (lógica lineal obsoleta)"
    
    def test_relationship_system_has_no_update_affinity(self):
        """RelationshipSystem no debe tener el método _update_affinity."""
        config = SimulationConfig()
        system = RelationshipSystem(config)
        
        assert not hasattr(system, '_update_affinity'), \
            "RelationshipSystem no debe tener _update_affinity (lógica lineal obsoleta)"


class TestBug4_DeathResolverInfectionsFilter:
    """REGRESIÓN: DeathResolver debe filtrar tuplas (entity_id, pathogen) correctamente.
    
    Bug histórico: DeathResolver filtraba `e_id not in muertos_set` sobre
    pending.infections, pero infections contiene tuplas (entity_id, pathogen),
    no simples IDs. Esto causaba que las infecciones de agentes fallecidos
    nunca se eliminaran, causando errores en fases posteriores.
    """
    
    def test_death_resolver_filters_infection_tuples(self):
        """DeathResolver debe eliminar infecciones de agentes que mueren en el mismo tick."""
        config = SimulationConfig()
        resolver = DeathResolver(config)
        
        state = MagicMock()
        state.get_all_persons.return_value = []
        
        pending = PendingChanges()
        
        # Simular patógenos
        pathogen1 = MagicMock()
        pathogen1.pathogen_id = "virus_1"
        pathogen2 = MagicMock()
        pathogen2.pathogen_id = "virus_2"
        
        # Agregar infecciones como TUPLAS (entity_id, pathogen)
        pending.infections = [
            (15, pathogen1),  # Agente 15 infectado
            (20, pathogen2),  # Agente 20 infectado
            (25, pathogen1),  # Agente 25 infectado
        ]
        
        # Agregar muertes: Agentes 15 y 25 mueren en este tick
        pending.deaths = {15: "causa_1", 25: "causa_2"}
        
        # Ejecutar el resolver
        resolver.process(state, pending, 1.0, MagicMock())
        
        # Verificar que las infecciones de agentes muertos se eliminaron
        remaining_infections = pending.infections
        assert len(remaining_infections) == 1, \
            f"Debería quedar 1 infección (agente 20), pero quedaron {len(remaining_infections)}: {remaining_infections}"
        
        # Verificar que la infección restante es del agente 20
        assert remaining_infections[0][0] == 20, \
            "La infección restante debe ser del agente 20 (el único que no murió)"

    def test_death_resolver_filters_recovery_tuples(self):
        """DeathResolver debe eliminar recoveries de agentes que mueren en el mismo tick."""
        config = SimulationConfig()
        resolver = DeathResolver(config)
        
        state = MagicMock()
        state.get_all_persons.return_value = []
        
        pending = PendingChanges()
        
        # Agregar recoveries como TUPLAS (entity_id, pathogen_id)
        pending.recoveries = [
            (15, "virus_1"),  # Agente 15 se recuperó
            (20, "virus_2"),  # Agente 20 se recuperó
        ]
        
        # Agregar muerte: Agente 15 muere
        pending.deaths = {15: "causa_1"}
        
        # Ejecutar el resolver
        resolver.process(state, pending, 1.0, MagicMock())
        
        # Verificar que las recoveries de agentes muertos se eliminaron
        remaining_recoveries = pending.recoveries
        assert len(remaining_recoveries) == 1, \
            f"Debería quedar 1 recovery (agente 20), pero quedaron {len(remaining_recoveries)}"
        
        assert remaining_recoveries[0][0] == 20, \
            "La recovery restante debe ser del agente 20"


class TestBug3_RegisterBirthSignature:
    """REGRESIÓN: register_birth no debe aceptar parámetro 'species'.
    
    Bug histórico: GestationSystem llamaba a pending.register_birth()
    con un parámetro 'species' que no existe en la firma de PendingChanges,
    causando TypeError.
    """
    
    def test_register_birth_no_species_parameter(self):
        """register_birth no debe tener 'species' en su firma."""
        import inspect
        from core.state.pending_changes import PendingChanges
        
        pending = PendingChanges()
        sig = inspect.signature(pending.register_birth)
        params = list(sig.parameters.keys())
        
        assert 'species' not in params, \
            "register_birth no debe aceptar parámetro 'species' (causa TypeError)"
    
    def test_register_birth_accepts_required_parameters(self):
        """register_birth debe aceptar los parámetros básicos requeridos."""
        import inspect
        from core.state.pending_changes import PendingChanges
        
        pending = PendingChanges()
        sig = inspect.signature(pending.register_birth)
        params = list(sig.parameters.keys())
        
        # Estos son los parámetros que SÍ debe tener
        required_params = ['mother_id', 'father_id', 'x', 'y', 'genome']
        for param in required_params:
            assert param in params, \
                f"register_birth debe aceptar parámetro '{param}'"


class TestBug5_OutbreakChanceTooLow:
    """REGRESIÓN: base_outbreak_chance debe ser suficientemente alto.
    
    Bug histórico: base_outbreak_chance = 0.02 causaba que en 500 ticks
    con 200 agentes no se generara ningún brote. El valor debe ser >= 1.0.
    """
    
    def test_default_outbreak_chance_is_reasonable(self):
        """El valor por defecto de base_outbreak_chance debe ser >= 1.0."""
        config = SimulationConfig()
        
        outbreak_chance = getattr(config.diseases, 'base_outbreak_chance', None)
        
        assert outbreak_chance is not None, \
            "SimulationConfig.diseases debe tener atributo base_outbreak_chance"
        
        assert outbreak_chance >= 1.0, \
            f"base_outbreak_chance debe ser >= 1.0 para generar brotes razonables, " \
            f"pero es {outbreak_chance}"


class TestBug2_OutbreaksOutsideLoop:
    """REGRESIÓN: Los brotes espontáneos deben evaluarse UNA VEZ por tick.
    
    Bug histórico: El bloque de brotes estaba dentro del bucle `for person`,
    causando que se evaluara N veces por tick (una por agente) en lugar de 1 vez.
    """
    
    def test_disease_system_does_not_spam_infections(self):
        """Con 100 agentes y 1.5% de probabilidad, no debe haber ~100 infecciones en 1 tick.
        
        Si el bug del bucle vuelve, se generarían ~1-2 infecciones POR AGENTE,
        resultando en ~100-200 infecciones en un solo tick.
        Si está fuera del bucle, deberían ser 0-3 infecciones en total.
        """
        from systems.diseases.disease_system import DiseaseSystem
        
        config = SimulationConfig()
        # Forzamos un valor conocido y razonable
        config.diseases.base_outbreak_chance = 1.5
        
        system = DiseaseSystem(config)
        
        # Crear estado con 100 agentes sanos
        state = MagicMock()
        persons = []
        for i in range(100):
            p = MagicMock()
            p.entity_id = i
            p.is_sick = False
            p.active_infections = {}
            p.x = 50.0
            p.y = 50.0
            persons.append(p)
            
        state.get_all_persons.return_value = persons
        
        pending = PendingChanges()
        context = MagicMock()
        context.get_local_pressure.return_value = 1.0
        
        # Ejecutar el sistema UNA VEZ (1 tick)
        system.process(state, pending, 1.0, context)
        
        # Contar cuántas infecciones se registraron
        infection_count = len(pending.infections)
        
        # Con 100 agentes y 1.5% de probabilidad EVALUADA UNA VEZ,
        # lo máximo razonable es 1 o 2 brotes (cada brote infecta a 1 paciente cero).
        # Si el bug del bucle vuelve, infection_count sería ~1 a 2 POR AGENTE (100+).
        assert infection_count <= 5, \
            f"Se registraron {infection_count} infecciones en 1 tick con 100 agentes. " \
            f"Esto sugiere que el brote se está evaluando dentro del bucle de agentes."