"""Tests para el ParameterRegistry."""

import pytest

from core.config.parameter_registry import ParameterRegistry, ParameterSpec
from core.config.simulation_config import SimulationConfig


@pytest.fixture
def config():
    return SimulationConfig()


@pytest.fixture
def registry(config):
    return ParameterRegistry(config)


class TestParameterRegistryBasics:
    """Tests de funcionalidad básica."""
    
    def test_auto_discover_finds_parameters(self, registry, config):
        """auto_discover encuentra todos los atributos numéricos/booleanos."""
        discovered = registry.auto_discover("engine")
        
        # EngineConfig tiene total_days y delta_days
        assert discovered >= 2
        assert "engine.total_days" in registry.specs
        assert "engine.delta_days" in registry.specs
    
    def test_auto_discover_skips_non_primitives(self, registry):
        """auto_discover ignora atributos no primitivos (dicts, lists, etc)."""
        discovered = registry.auto_discover("reproduction")
        
        # species_profiles es un dict, no debe descubrirse
        assert "reproduction.species_profiles" not in registry.specs
        assert discovered >= 0
    
    def test_auto_discover_skips_callables(self, registry):
        """auto_discover ignora métodos (callables)."""
        discovered = registry.auto_discover("reproduction")
        
        # Ningún path debe terminar en un método conocido
        for path in registry.specs:
            assert not path.endswith("get_species_profile")
    
    def test_register_manual_spec(self, registry):
        """Se puede registrar manualmente un parámetro con metadata."""
        spec = ParameterSpec(
            path="diseases.transmission_factor",
            category="diseases",
            description="Factor de transmisión",
            value_type=float,
            min_value=0.0,
            max_value=1.0,
            default_value=0.3
        )
        registry.register(spec)
        
        assert "diseases.transmission_factor" in registry.specs
        assert registry.specs["diseases.transmission_factor"].description == "Factor de transmisión"
    
    def test_get_returns_current_value(self, registry, config):
        """get() devuelve el valor actual del parámetro."""
        value = registry.get("engine.total_days")
        
        assert value == config.engine.total_days
    
    def test_get_with_default(self, registry):
        """get() devuelve el default si el path no existe."""
        value = registry.get("nonexistent.param", default=42)
        
        assert value == 42


class TestParameterValidation:
    """Tests de validación de tipos y rangos."""
    
    def test_set_validates_type(self, registry):
        """set() rechaza valores de tipo incorrecto."""
        spec = ParameterSpec(
            path="engine.total_days",
            category="engine",
            description="Total days",
            value_type=float,
            min_value=0.0,
            max_value=10000.0,
            default_value=3650.0
        )
        registry.register(spec)
        
        # Intentar setear un string (tipo incorrecto)
        success = registry.set("engine.total_days", "invalid")
        
        assert success is False
        assert registry.get("engine.total_days") == 3650.0  # Valor sin cambios
    
    def test_set_validates_min_range(self, registry):
        """set() rechaza valores por debajo del mínimo."""
        spec = ParameterSpec(
            path="engine.delta_days",
            category="engine",
            description="Delta days",
            value_type=float,
            min_value=0.1,
            max_value=10.0,
            default_value=1.0
        )
        registry.register(spec)
        
        success = registry.set("engine.delta_days", 0.01)
        
        assert success is False
        assert registry.get("engine.delta_days") == 1.0
    
    def test_set_validates_max_range(self, registry):
        """set() rechaza valores por encima del máximo."""
        spec = ParameterSpec(
            path="engine.delta_days",
            category="engine",
            description="Delta days",
            value_type=float,
            min_value=0.1,
            max_value=10.0,
            default_value=1.0
        )
        registry.register(spec)
        
        success = registry.set("engine.delta_days", 20.0)
        
        assert success is False
        assert registry.get("engine.delta_days") == 1.0
    
    def test_set_accepts_valid_value(self, registry, config):
        """set() acepta valores dentro del rango y tipo correcto."""
        spec = ParameterSpec(
            path="engine.total_days",
            category="engine",
            description="Total days",
            value_type=float,
            min_value=0.0,
            max_value=10000.0,
            default_value=3650.0
        )
        registry.register(spec)
        
        success = registry.set("engine.total_days", 5000.0)
        
        assert success is True
        assert registry.get("engine.total_days") == 5000.0
        assert config.engine.total_days == 5000.0  # Propagado a la config
    
    def test_set_without_spec_still_works(self, registry, config):
        """set() funciona sin spec (sin validación)."""
        success = registry.set("engine.total_days", 7000.0)
        
        assert success is True
        assert config.engine.total_days == 7000.0


class TestParameterHistory:
    """Tests del historial de cambios."""
    
    def test_history_records_changes(self, registry):
        """Cada set() exitoso se registra en el historial."""
        registry.set("engine.total_days", 4000.0)
        registry.set("engine.delta_days", 2.0)
        
        assert len(registry.history) == 2
        assert registry.history[0]["path"] == "engine.total_days"
        assert registry.history[0]["value"] == 4000.0
        assert registry.history[1]["path"] == "engine.delta_days"
        assert registry.history[1]["value"] == 2.0
    
    def test_history_includes_timestamp(self, registry):
        """El historial incluye timestamp ISO."""
        registry.set("engine.total_days", 4000.0)
        
        assert "timestamp" in registry.history[0]
        assert len(registry.history[0]["timestamp"]) > 0


class TestParameterReset:
    """Tests de reseteo de parámetros."""
    
    def test_reset_restores_default(self, registry):
        """reset() restaura el valor por defecto."""
        spec = ParameterSpec(
            path="engine.total_days",
            category="engine",
            description="Total days",
            value_type=float,
            default_value=3650.0
        )
        registry.register(spec)
        
        registry.set("engine.total_days", 5000.0)
        assert registry.get("engine.total_days") == 5000.0
        
        success = registry.reset("engine.total_days")
        
        assert success is True
        assert registry.get("engine.total_days") == 3650.0
    
    def test_reset_without_spec_fails(self, registry):
        """reset() falla si no hay spec registrado."""
        success = registry.reset("nonexistent.param")
        
        assert success is False
    
    def test_reset_all_resets_all_parameters(self, registry):
        """reset_all() restaura todos los parámetros a sus defaults."""
        spec1 = ParameterSpec(
            path="engine.total_days",
            category="engine",
            description="Total days",
            value_type=float,
            default_value=3650.0
        )
        spec2 = ParameterSpec(
            path="engine.delta_days",
            category="engine",
            description="Delta days",
            value_type=float,
            default_value=1.0
        )
        registry.register(spec1)
        registry.register(spec2)
        
        registry.set("engine.total_days", 5000.0)
        registry.set("engine.delta_days", 2.0)
        
        reset_count = registry.reset_all()
        
        assert reset_count == 2
        assert registry.get("engine.total_days") == 3650.0
        assert registry.get("engine.delta_days") == 1.0


class TestParameterListing:
    """Tests de listado de parámetros."""
    
    def test_list_all_parameters(self, registry):
        """list_parameters() sin filtro devuelve todos los parámetros."""
        registry.auto_discover("engine")
        registry.auto_discover("reproduction")
        
        all_params = registry.list_parameters()
        
        assert len(all_params) > 0
        assert any(p.startswith("engine.") for p in all_params)
        assert any(p.startswith("reproduction.") for p in all_params)
    
    def test_list_by_category(self, registry):
        """list_parameters(category) filtra por categoría."""
        registry.auto_discover("engine")
        registry.auto_discover("reproduction")
        
        engine_params = registry.list_parameters("engine")
        
        assert len(engine_params) > 0
        assert all(p.startswith("engine.") for p in engine_params)
        assert not any(p.startswith("reproduction.") for p in engine_params)
    
    def test_get_spec_returns_spec(self, registry):
        """get_spec() devuelve la ParameterSpec registrada."""
        spec = ParameterSpec(
            path="engine.total_days",
            category="engine",
            description="Total days",
            value_type=float,
            default_value=3650.0
        )
        registry.register(spec)
        
        retrieved = registry.get_spec("engine.total_days")
        
        assert retrieved is not None
        assert retrieved.description == "Total days"
        assert retrieved.default_value == 3650.0
    
    def test_get_spec_returns_none_for_unknown(self, registry):
        """get_spec() devuelve None si el path no está registrado."""
        retrieved = registry.get_spec("nonexistent.param")
        
        assert retrieved is None