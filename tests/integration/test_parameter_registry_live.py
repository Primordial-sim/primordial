"""Integración: el ParameterRegistry modifica el motor en caliente.

Demuestra el circuito completo:
    registry.set() -> SimulationConfig -> sistema leyéndolo en el siguiente tick
"""

from unittest.mock import MagicMock

import pytest

from core.config.parameter_registry import ParameterRegistry, ParameterSpec
from core.config.simulation_config import SimulationConfig
from systems.ecology.ecological_relationship_system import EcologicalRelationshipSystem
from systems.energy.energy_system import EnergySystem
from systems.environment.feedback_system import FeedbackSystem
from systems.movement.migration_system import MigrationSystem
from systems.environment.environment_dynamics import EnvironmentDynamics

def make_empty_state():
    """Estado mock con mapa pero sin organismos: cruza la puerta del
    intervalo y retorna antes de tocar rejillas ni tiles."""
    state = MagicMock()
    state.has_tile_map = MagicMock(return_value=True)
    state.get_all_persons = MagicMock(return_value=[])
    return state


class TestLiveParameterEditing:
    """Un set() en caliente altera el comportamiento del sistema."""

    def test_registry_change_alters_ecology_gate(self):
        """Reducir el intervalo en vivo hace que el sistema procese antes."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)
        registry.auto_discover("ecology")
        system = EcologicalRelationshipSystem(config)
        state = make_empty_state()

        # Intervalo por defecto 3.0: con 2 días no cruza la puerta
        system.process(state, MagicMock(), 2.0, MagicMock())
        assert system._process_counter == 2.0

        # Cambio en caliente vía registry
        assert registry.set("ecology.process_interval_days", 1.0) is True

        # El siguiente tick cruza la puerta y resetea el contador
        system.process(state, MagicMock(), 2.0, MagicMock())
        assert system._process_counter == 0.0

    def test_system_without_config_keeps_default(self):
        """Sin config inyectada, el sistema se comporta como antes."""
        system = EcologicalRelationshipSystem()
        state = make_empty_state()

        system.process(state, MagicMock(), 2.0, MagicMock())

        assert system._process_counter == 2.0

    def test_registry_validates_real_parameter(self):
        """Un spec con rango protege un parámetro real del motor."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)
        registry.register(ParameterSpec(
            path="ecology.process_interval_days",
            category="ecology",
            description="Días entre pasadas de procesamiento ecológico",
            value_type=float,
            min_value=0.5,
            max_value=30.0,
            default_value=3.0,
        ))

        assert registry.set("ecology.process_interval_days", 0.1) is False
        assert config.ecology.process_interval_days == 3.0

        assert registry.set("ecology.process_interval_days", 7.0) is True
        assert config.ecology.process_interval_days == 7.0

# ---------------------------------------------------------------------------
# Energía: parámetros vivos de metabolismo
# ---------------------------------------------------------------------------

def make_energy_person():
    """Organismo mock no fotosintético, sano y sin inanición."""
    person = MagicMock()
    person.genome.body_size = 0.5  # size_factor = 0.5 + 0.5*1.5 = 1.25
    person.genome.get_trait_value = MagicMock(return_value=0.8)  # diet > 0.1 → no fotosintético
    person.is_pregnant = False
    person.is_sick = False
    person._emotions = {}
    person.starvation_days = 0.0
    return person


def make_energy_state(persons):
    state = MagicMock()
    state.get_all_persons = MagicMock(return_value=persons)
    return state


class TestLiveEnergyEditing:
    """El metabolismo responde a cambios en caliente de EnergyConfig."""

    def test_auto_discover_energy_parameters(self):
        """auto_discover encuentra los 5 parámetros de energía."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)

        discovered = registry.auto_discover("energy")

        assert discovered == 5
        assert "energy.basal_metabolic_rate" in registry.specs
        assert "energy.photosynthesis_light_factor" in registry.specs

    def test_registry_change_alters_metabolic_cost(self):
        """Subir el metabolismo en caliente aumenta el gasto del siguiente tick."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)
        registry.auto_discover("energy")
        system = EnergySystem(config)
        person = make_energy_person()
        state = make_energy_state([person])

        # Tick 1: 0.1 (basal) * 1.0 (delta) * 1.25 (size) = 0.125
        system.process(state, MagicMock(), 1.0, MagicMock())
        first_cost = person.spend_energy.call_args[0][0]
        assert first_cost == pytest.approx(0.125)

        # Cambio en caliente
        assert registry.set("energy.basal_metabolic_rate", 0.4) is True

        # Tick 2: 0.4 * 1.0 * 1.25 = 0.5
        system.process(state, MagicMock(), 1.0, MagicMock())
        second_cost = person.spend_energy.call_args[0][0]
        assert second_cost == pytest.approx(0.5)

    def test_registry_validates_energy_parameter(self):
        """Un spec con rango protege un parámetro real de energía."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)
        registry.register(ParameterSpec(
            path="energy.basal_metabolic_rate",
            category="energy",
            description="Energía gastada por día en reposo",
            value_type=float,
            min_value=0.0,
            max_value=1.0,
            default_value=0.1,
        ))

        assert registry.set("energy.basal_metabolic_rate", 5.0) is False
        assert config.energy.basal_metabolic_rate == 0.1

# ---------------------------------------------------------------------------
# Feedback: intervalo de procesamiento en caliente
# ---------------------------------------------------------------------------

def make_feedback_state():
    """Estado mock con tile_map pero sin organismos."""
    state = MagicMock()
    state.has_tile_map = MagicMock(return_value=True)
    state.tile_map = MagicMock()
    state.tile_map.tiles = {}
    state.get_all_persons = MagicMock(return_value=[])
    return state


class TestLiveFeedbackEditing:
    """El sistema de feedback responde a cambios en caliente de FeedbackConfig."""

    def test_registry_change_alters_feedback_gate(self):
        """Reducir el intervalo en caliente hace que el sistema procese antes."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)
        registry.auto_discover("feedback")
        system = FeedbackSystem(config)
        state = make_feedback_state()

        # Intervalo por defecto 5.0: con 3 días no cruza la puerta
        system.process(state, MagicMock(), 3.0, MagicMock())
        assert system._process_counter == 3.0

        # Cambio en caliente vía registry
        assert registry.set("feedback.process_interval_days", 1.0) is True

        # El siguiente tick cruza la puerta y resetea el contador
        system.process(state, MagicMock(), 3.0, MagicMock())
        assert system._process_counter == 0.0

    def test_feedback_without_config_keeps_default(self):
        """Sin config inyectada, el sistema se comporta como antes."""
        system = FeedbackSystem()
        state = make_feedback_state()

        system.process(state, MagicMock(), 3.0, MagicMock())

        assert system._process_counter == 3.0

# ---------------------------------------------------------------------------
# Migration: umbral de llegada en caliente
# ---------------------------------------------------------------------------

class TestLiveMigrationEditing:
    """El sistema de migración responde a cambios en caliente de MigrationConfig."""

    def test_auto_discover_migration_parameters(self):
        """auto_discover encuentra el parámetro de migración."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)

        discovered = registry.auto_discover("migration")

        assert discovered == 1
        assert "migration.arrival_threshold" in registry.specs

    def test_registry_change_alters_migration_threshold(self):
        """Cambiar el umbral en caliente se refleja en el helper."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)
        registry.auto_discover("migration")
        system = MigrationSystem(config)

        # Valor por defecto
        assert system._get_param('arrival_threshold', 5.0) == 5.0

        # Cambio en caliente vía registry
        assert registry.set("migration.arrival_threshold", 10.0) is True

        # El helper lee el nuevo valor
        assert system._get_param('arrival_threshold', 5.0) == 10.0

    def test_migration_without_config_keeps_default(self):
        """Sin config inyectada, el sistema usa el valor por defecto."""
        # MigrationSystem requiere config, así que simulamos el fallback
        config = SimulationConfig()
        # Eliminamos el atributo migration para simular config incompleta
        delattr(config, 'migration')
        system = MigrationSystem(config)

        # Debe usar el valor por defecto (5.0)
        assert system._get_param('arrival_threshold', 5.0) == 5.0

# ---------------------------------------------------------------------------
# Environment Dynamics: intervalos de escalas temporal en caliente
# ---------------------------------------------------------------------------

class TestLiveEnvironmentDynamicsEditing:
    """La dinámica ambiental responde a cambios en caliente de EnvironmentDynamicsConfig."""

    def test_auto_discover_environment_dynamics_parameters(self):
        """auto_discover encuentra los 2 parámetros de dinámica ambiental."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)

        discovered = registry.auto_discover("environment_dynamics")

        assert discovered == 2
        assert "environment_dynamics.medium_scale_interval" in registry.specs
        assert "environment_dynamics.slow_scale_interval" in registry.specs

    def test_registry_change_alters_environment_intervals(self):
        """Cambiar los intervalos en caliente se refleja en el helper."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)
        registry.auto_discover("environment_dynamics")
        system = EnvironmentDynamics(config=config)

        # Valores por defecto
        assert system._get_param('medium_scale_interval', 15.0) == 15.0
        assert system._get_param('slow_scale_interval', 180.0) == 180.0

        # Cambio en caliente vía registry
        assert registry.set("environment_dynamics.medium_scale_interval", 30.0) is True
        assert registry.set("environment_dynamics.slow_scale_interval", 365.0) is True

        # El helper lee los nuevos valores
        assert system._get_param('medium_scale_interval', 15.0) == 30.0
        assert system._get_param('slow_scale_interval', 180.0) == 365.0

    def test_environment_dynamics_without_config_keeps_default(self):
        """Sin config inyectada, el sistema usa los valores por defecto."""
        system = EnvironmentDynamics()

        # Debe usar los valores por defecto
        assert system._get_param('medium_scale_interval', 15.0) == 15.0
        assert system._get_param('slow_scale_interval', 180.0) == 180.0