"""Tests de integración entre PresetEngine y ParameterRegistry."""

import pytest
from core.config.simulation_config import SimulationConfig
from core.config.parameter_registry import ParameterRegistry, ParameterSpec
from core.config.preset_engine import PresetEngine, create_fertility_preset, create_mortality_preset


class TestPresetRegistryIntegration:
    """Pruebas de que el PresetEngine modifica correctamente el Registry y viceversa."""
    
    @pytest.fixture
    def setup_engine_and_registry(self):
        """Configura un entorno con Config, Registry y PresetEngine conectados."""
        config = SimulationConfig()
        registry = ParameterRegistry(config)
        
        # Registramos las specs en el registry usando los NOMBRES REALES
        registry.register(ParameterSpec(
            path="reproduction.base_conception_chance",
            category="reproduction",
            description="Probabilidad base de concepción",
            value_type=float,
            min_value=0.01,
            max_value=0.5,
            default_value=0.15
        ))
        registry.register(ParameterSpec(
            path="reproduction.min_fertility_age_days",
            category="reproduction",
            description="Edad mínima de fertilidad",
            value_type=float,
            min_value=4000.0,
            max_value=8000.0,
            default_value=6570.0
        ))
        registry.register(ParameterSpec(
            path="reproduction.max_fertility_age_days",
            category="reproduction",
            description="Edad máxima de fertilidad",
            value_type=float,
            min_value=14000.0,
            max_value=20000.0,
            default_value=16425.0
        ))
        
        # Creamos el engine y le pasamos el registry
        engine = PresetEngine(registry=registry)
        engine.register_preset(create_fertility_preset())
        
        return config, registry, engine

    def test_preset_slider_updates_registry_and_config(self, setup_engine_and_registry):
        """Al mover el slider de fertilidad, el registry y la config deben actualizarse."""
        config, registry, engine = setup_engine_and_registry
        
        # 1. Mover slider de fertilidad al 80%
        engine.set_preset_value("fertilidad", 80.0)
        
        # 2. Verificar que el registry recibió los cambios
        assert registry.get("reproduction.base_conception_chance") > 0.15
        assert registry.get("reproduction.min_fertility_age_days") < 6570.0  # Inverso!
        assert registry.get("reproduction.max_fertility_age_days") > 16425.0
        
        # 3. Verificar que el historial del registry se actualizó
        assert len(registry.history) >= 3
        
        # 4. Verificar que la SimulationConfig subyacente tiene los nuevos valores
        assert config.reproduction.base_conception_chance > 0.15

    def test_manual_registry_update_recalculates_preset_slider(self, setup_engine_and_registry):
        """Si el usuario modifica un parámetro manualmente, el slider del preset debe reflejarlo."""
        config, registry, engine = setup_engine_and_registry
        
        # 1. Obtener el valor inicial real del preset (no asumimos 50.0, depende de los defaults de Config)
        initial_preset_value = engine.get_preset_value("fertilidad")
        
        # 2. Usuario modifica manualmente la edad mínima de fertilidad a través del registry (la sube a 7500)
        # Como es inverse=True, un valor alto de edad debe bajar el slider de fertilidad
        registry.set("reproduction.min_fertility_age_days", 7500.0)
        
        # 3. El preset engine debe recalcular el slider al consultarlo
        new_preset_value = engine.get_preset_value("fertilidad")
        
        # Debe ser menor que el valor inicial porque subimos la edad mínima (relación inversa)
        assert new_preset_value < initial_preset_value

    def test_preset_engine_set_parameter_syncs_with_registry(self, setup_engine_and_registry):
        """El método set_parameter del engine debe usar el registry."""
        config, registry, engine = setup_engine_and_registry
        
        # Usamos el método del engine para cambiar un valor
        engine.set_parameter("reproduction.base_conception_chance", 0.4)
        
        # Verificar que el registry lo registró
        assert registry.get("reproduction.base_conception_chance") == 0.4
        assert len(registry.history) == 1
        assert registry.history[0]['path'] == "reproduction.base_conception_chance"