"""Integración: el ParameterRegistry modifica el motor en caliente.

Demuestra el circuito completo:
    registry.set() -> SimulationConfig -> sistema leyéndolo en el siguiente tick
"""

from unittest.mock import MagicMock

from core.config.parameter_registry import ParameterRegistry, ParameterSpec
from core.config.simulation_config import SimulationConfig
from systems.ecology.ecological_relationship_system import EcologicalRelationshipSystem


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