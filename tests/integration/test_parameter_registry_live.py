"""Tests de integración para verificar que el ParameterRegistry funciona en caliente.

Estos tests verifican que cambiar un parámetro en el registry afecta
inmediatamente el comportamiento de los sistemas en el siguiente tick.
"""

import pytest
from unittest.mock import MagicMock

from core.config.simulation_config import SimulationConfig
from core.config.parameter_registry import ParameterRegistry, ParameterSpec
from systems.energy.energy_system import EnergySystem
from systems.ecology.ecological_relationship_system import EcologicalRelationshipSystem
from systems.environment.feedback_system import FeedbackSystem
from systems.movement.migration_system import MigrationSystem
from systems.environment.environment_dynamics import EnvironmentDynamics
from systems.relationships.experience_generator import ExperienceGenerator


class TestLiveParameterEditing:
    """Tests de edición en caliente de parámetros."""

    def test_registry_change_alters_ecology_gate(self):
        """Cambiar process_interval_days afecta el procesamiento ecológico."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)
        registry.auto_discover("ecology")

        system = EcologicalRelationshipSystem(config)

        state = MagicMock()
        state.has_tile_map.return_value = True
        state.get_all_persons.return_value = []
        pending = MagicMock()
        context = MagicMock()

        system.process(state, pending, 1.0, context)
        system.process(state, pending, 1.0, context)

        assert system._process_counter == 2.0

        registry.set("ecology.process_interval_days", 1.0)

        system.process(state, pending, 1.0, context)

        assert system._process_counter == 0.0

    def test_system_without_config_keeps_default(self):
        """Un sistema sin config usa su valor por defecto."""
        system = EcologicalRelationshipSystem(config=None)

        assert system.process_interval == 1.0

        state = MagicMock()
        state.has_tile_map.return_value = True
        state.get_all_persons.return_value = []
        pending = MagicMock()
        context = MagicMock()

        system.process(state, pending, 1.0, context)
        system.process(state, pending, 1.0, context)

        assert system._process_counter == 0.0

    def test_registry_validates_real_parameter(self):
        """El registry valida rangos de parámetros reales."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)

        registry.register(ParameterSpec(
            path="ecology.process_interval_days",
            category="ecology",
            description="Intervalo de procesamiento ecológico",
            value_type=float,
            min_value=0.1,
            max_value=None,
            default_value=3.0
        ))

        success = registry.set("ecology.process_interval_days", -1.0)
        assert not success

        assert config.ecology.process_interval_days == 3.0


class TestLiveEnergyEditing:
    """Tests de edición en caliente de parámetros de energía."""

    def test_auto_discover_energy_parameters(self):
        """El registry descubre los 7 parámetros de EnergyConfig."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)
        registry.auto_discover("energy")

        discovered = len([
            key for key in registry.list_parameters()
            if key.startswith("energy.")
        ])
        assert discovered == 7

    def test_registry_change_alters_metabolic_cost(self):
        """Cambiar basal_metabolic_rate afecta el coste metabólico calculado."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)
        registry.auto_discover("energy")

        system = EnergySystem(config)

        person = MagicMock()
        person.genome.body_size = 0.5
        person.is_pregnant = False
        person.is_sick = False
        person._emotions = {"stress": 0.0}

        first_cost = system._calculate_metabolic_cost(person, delta_days=1.0)
        assert first_cost == pytest.approx(0.0625)

        registry.set("energy.basal_metabolic_rate", 0.2)

        second_cost = system._calculate_metabolic_cost(person, delta_days=1.0)
        assert second_cost == pytest.approx(0.25)

    def test_registry_validates_energy_parameter(self):
        """El registry valida rangos de parámetros de energía."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)

        registry.register(ParameterSpec(
            path="energy.basal_metabolic_rate",
            category="energy",
            description="Tasa metabólica basal",
            value_type=float,
            min_value=0.0,
            max_value=1.0,
            default_value=0.05
        ))

        assert config.energy.basal_metabolic_rate == 0.05

        success = registry.set("energy.basal_metabolic_rate", 5.0)
        assert not success

        assert config.energy.basal_metabolic_rate == 0.05


class TestLiveFeedbackEditing:
    """Tests de edición en caliente de parámetros de feedback."""

    def test_registry_change_alters_feedback_gate(self):
        """Cambiar process_interval_days afecta el procesamiento de feedback."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)
        registry.auto_discover("feedback")

        system = FeedbackSystem(config)

        state = MagicMock()
        state.has_tile_map.return_value = True
        pending = MagicMock()
        context = MagicMock()

        system.process(state, pending, 2.0, context)
        system.process(state, pending, 2.0, context)

        assert system._process_counter == 4.0

        registry.set("feedback.process_interval_days", 1.0)

        system.process(state, pending, 1.0, context)

        assert system._process_counter == 0.0

    def test_feedback_without_config_keeps_default(self):
        """Un sistema sin config usa su valor por defecto."""
        system = FeedbackSystem(SimulationConfig())
        assert system.process_interval == 5.0


class TestLiveMigrationEditing:
    """Tests de edición en caliente de parámetros de migración."""

    def test_auto_discover_migration_parameters(self):
        """El registry descubre los parámetros de MigrationConfig."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)
        registry.auto_discover("migration")

        discovered = [
            key for key in registry.list_parameters()
            if key.startswith("migration.")
        ]
        assert len(discovered) > 0

    def test_registry_change_alters_migration_threshold(self):
        """Cambiar arrival_threshold actualiza la config correctamente."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)
        registry.auto_discover("migration")

        # Verificar valor por defecto en la config
        assert config.migration.arrival_threshold == 5.0

        # Cambiar parámetro
        registry.set("migration.arrival_threshold", 10.0)

        # Verificar que la config se actualizó
        assert config.migration.arrival_threshold == 10.0

    def test_migration_without_config_keeps_default(self):
        """Un sistema sin config usa su valor por defecto."""
        system = MigrationSystem(SimulationConfig())
        assert system.arrival_threshold == 5.0


class TestLiveEnvironmentDynamicsEditing:
    """Tests de edición en caliente de parámetros de dinámica ambiental."""

    def test_auto_discover_environment_dynamics_parameters(self):
        """El registry descubre los parámetros de EnvironmentDynamicsConfig."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)
        registry.auto_discover("environment_dynamics")

        discovered = [
            key for key in registry.list_parameters()
            if key.startswith("environment_dynamics.")
        ]
        assert len(discovered) > 0

    def test_registry_change_alters_environment_intervals(self):
        """Cambiar intervalos actualiza la config correctamente."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)
        registry.auto_discover("environment_dynamics")

        # Verificar valores por defecto en la config
        assert config.environment_dynamics.medium_scale_interval == 15.0
        assert config.environment_dynamics.slow_scale_interval == 180.0

        # Cambiar parámetros
        registry.set("environment_dynamics.medium_scale_interval", 10.0)
        registry.set("environment_dynamics.slow_scale_interval", 90.0)

        # Verificar que la config se actualizó
        assert config.environment_dynamics.medium_scale_interval == 10.0
        assert config.environment_dynamics.slow_scale_interval == 90.0

    def test_environment_dynamics_without_config_keeps_default(self):
        """Un sistema sin config usa su valor por defecto."""
        system = EnvironmentDynamics(config=SimulationConfig())
        assert system.medium_scale_interval == 15.0
        assert system.slow_scale_interval == 180.0


class TestLiveExperienceEditing:
    """Tests de edición en caliente de parámetros de experiencias."""

    def test_auto_discover_experience_parameters(self):
        """El registry descubre los parámetros de ExperienceConfig."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)
        registry.auto_discover("experience")

        discovered = [
            key for key in registry.list_parameters()
            if key.startswith("experience.")
        ]
        assert len(discovered) > 0

    def test_registry_change_alters_experience_log_interval(self):
        """Cambiar log_interval actualiza la config correctamente."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)
        registry.auto_discover("experience")

        # Verificar valor por defecto en la config
        assert config.experience.log_interval == 365

        # Cambiar parámetro
        registry.set("experience.log_interval", 100)

        # Verificar que la config se actualizó
        assert config.experience.log_interval == 100

    def test_experience_without_config_keeps_default(self):
        """Un sistema sin config usa su valor por defecto."""
        system = ExperienceGenerator(SimulationConfig())
        assert system._log_interval == 365