"""Tests unitarios para el sistema de presets bidireccional (sin dependencias del Registry)."""

import pytest
from core.config.preset_engine import (
    PresetEngine,
    PresetDefinition,
    ParameterMapping,
    create_fertility_preset
)


class TestParameterMapping:
    """Tests para el mapeo de parámetros individuales."""
    
    def test_from_preset_value_min(self):
        mapping = ParameterMapping("test", 0.0, 1.0, 0.5)
        assert mapping.from_preset_value(0.0) == 0.0
    
    def test_from_preset_value_max(self):
        mapping = ParameterMapping("test", 0.0, 1.0, 0.5)
        assert mapping.from_preset_value(100.0) == 1.0
    
    def test_from_preset_value_middle(self):
        mapping = ParameterMapping("test", 0.0, 1.0, 0.5)
        assert mapping.from_preset_value(50.0) == 0.5
    
    def test_to_preset_value_min(self):
        mapping = ParameterMapping("test", 0.0, 1.0, 0.5)
        assert mapping.to_preset_value(0.0) == 0.0
    
    def test_to_preset_value_max(self):
        mapping = ParameterMapping("test", 0.0, 1.0, 0.5)
        assert mapping.to_preset_value(1.0) == 100.0
    
    def test_bidirectional_conversion(self):
        mapping = ParameterMapping("test", 0.0, 100.0, 50.0)
        param_value = mapping.from_preset_value(75.0)
        preset_value = mapping.to_preset_value(param_value)
        assert abs(preset_value - 75.0) < 0.01


class TestPresetEngine:
    """Tests para el motor de presets en modo aislado (sin Registry)."""
    
    def test_register_preset(self):
        engine = PresetEngine()
        preset = create_fertility_preset()
        engine.register_preset(preset)
        assert engine.get_preset("fertilidad") is not None
    
    def test_set_preset_value_updates_parameters(self):
        engine = PresetEngine()
        engine.register_preset(create_fertility_preset())
        params = engine.set_preset_value("fertilidad", 80.0)
        assert params["reproduction.base_conception_chance"] > 0.15
        assert params["reproduction.min_fertility_age_days"] < 6570.0  # Inverso
        assert params["reproduction.max_fertility_age_days"] > 16425.0
    
    def test_set_parameter_updates_preset_value(self):
        engine = PresetEngine()
        engine.register_preset(create_fertility_preset())
        engine.set_parameter("reproduction.base_conception_chance", 0.4)
        preset_value = engine.get_preset_value("fertilidad")
        assert preset_value > 34.9  # Debe subir respecto al valor inicial calculado
    
    def test_bidirectional_consistency(self):
        engine = PresetEngine()
        engine.register_preset(create_fertility_preset())
        engine.set_preset_value("fertilidad", 70.0)
        engine.set_parameter("reproduction.base_conception_chance", 0.45)
        new_preset_value = engine.get_preset_value("fertilidad")
        assert new_preset_value != 70.0
    
    def test_preset_value_clamping(self):
        engine = PresetEngine()
        engine.register_preset(create_fertility_preset())
        engine.set_preset_value("fertilidad", -10.0)
        assert engine.get_preset_value("fertilidad") == 0.0
        engine.set_preset_value("fertilidad", 150.0)
        assert engine.get_preset_value("fertilidad") == 100.0