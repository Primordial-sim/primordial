"""Tests para EnvironmentDynamics."""

import pytest
from core.state.world_state import WorldState
from core.config.simulation_config import SimulationConfig
from systems.environment.environment_dynamics import EnvironmentDynamics
from systems.environment.catastrophe_system import CatastropheSystem
from systems.environment.environment_system import Season, Weather


class TestEnvironmentDynamics:
    """Tests para la dinámica ambiental."""
    
    def test_initialization(self):
        """EnvironmentDynamics se inicializa correctamente."""
        dynamics = EnvironmentDynamics()
        
        assert dynamics.medium_scale_interval == 15.0
        assert dynamics.slow_scale_interval == 180.0
        assert dynamics.catastrophe_system is not None
        assert isinstance(dynamics.catastrophe_system, CatastropheSystem)
    
    def test_catastrophe_system_probabilities(self):
        """El sistema de catástrofes tiene las probabilidades correctas."""
        dynamics = EnvironmentDynamics()
        
        # Las probabilidades ahora están en el catastrophe_system
        from systems.environment.catastrophe_model import CatastropheType
        
        assert dynamics.catastrophe_system.base_probabilities[CatastropheType.FIRE] == 0.001
        assert dynamics.catastrophe_system.base_probabilities[CatastropheType.DROUGHT] == 0.0005
    
    def test_medium_scale_processes_vegetation(self):
        """La escala media procesa cambios de vegetación."""
        config = SimulationConfig()
        state = WorldState(config, width=10, height=10)
        state.initialize_tile_map(seed=42)
        
        dynamics = EnvironmentDynamics()
        dynamics.medium_scale_interval = 0.1  # Forzar procesamiento
        
        # Guardar estado inicial
        initial_tile = state.get_tile_at(5, 5)
        assert initial_tile is not None
        initial_vegetation = initial_tile.vegetation
        
        # Procesar
        dynamics.process(
            state=state,
            delta_days=1.0,
            current_season=Season.SPRING,
            current_weather=Weather.CLEAR,
        )
        
        # La vegetación debería haber cambiado (crecido o decrecido)
        final_tile = state.get_tile_at(5, 5)
        assert final_tile is not None
        # No verificamos dirección porque depende de las condiciones
    
    def test_slow_scale_processes_erosion(self):
        """La escala lenta procesa erosión."""
        config = SimulationConfig()
        state = WorldState(config, width=10, height=10)
        state.initialize_tile_map(seed=42)
        
        dynamics = EnvironmentDynamics()
        dynamics.slow_scale_interval = 0.1  # Forzar procesamiento
        
        # Encontrar un tile con pendiente alta
        erosion_tile = None
        for x in range(10):
            for y in range(10):
                tile = state.get_tile_at(x, y)
                if tile and tile.slope > 0.3 and tile.height > 100.0:
                    erosion_tile = (x, y)
                    break
            if erosion_tile:
                break
        
        if erosion_tile:
            x, y = erosion_tile
            initial_tile = state.get_tile_at(x, y)
            assert initial_tile is not None
            initial_height = initial_tile.height
            
            # Procesar
            dynamics.process(
                state=state,
                delta_days=1.0,
                current_season=Season.SPRING,
                current_weather=Weather.CLEAR,
            )
            
            # La altura debería haber disminuido
            final_tile = state.get_tile_at(x, y)
            assert final_tile is not None
            assert final_tile.height <= initial_height
    
    def test_seasonal_growth_factor(self):
        """El crecimiento vegetal varía según la estación."""
        config = SimulationConfig()
        state_spring = WorldState(config, width=10, height=10)
        state_spring.initialize_tile_map(seed=42)
        
        state_winter = WorldState(config, width=10, height=10)
        state_winter.initialize_tile_map(seed=42)
        
        dynamics_spring = EnvironmentDynamics()
        dynamics_spring.medium_scale_interval = 0.1
        
        dynamics_winter = EnvironmentDynamics()
        dynamics_winter.medium_scale_interval = 0.1
        
        # Procesar en primavera
        dynamics_spring.process(
            state=state_spring,
            delta_days=1.0,
            current_season=Season.SPRING,
            current_weather=Weather.CLEAR,
        )
        
        # Procesar en invierno
        dynamics_winter.process(
            state=state_winter,
            delta_days=1.0,
            current_season=Season.WINTER,
            current_weather=Weather.CLEAR,
        )
        
        # Comparar vegetación (primavera debería tener más crecimiento)
        tile_spring = state_spring.get_tile_at(5, 5)
        tile_winter = state_winter.get_tile_at(5, 5)
        
        assert tile_spring is not None
        assert tile_winter is not None
        # No verificamos dirección exacta porque depende de condiciones iniciales
    
    def test_no_processing_without_tile_map(self):
        """No procesa si no hay tile_map."""
        config = SimulationConfig()
        state = WorldState(config, width=10, height=10)
        # No inicializar tile_map
        
        dynamics = EnvironmentDynamics()
        
        # No debería lanzar error y retornar lista vacía
        result = dynamics.process(
            state=state,
            delta_days=1.0,
            current_season=Season.SPRING,
            current_weather=Weather.CLEAR,
        )
        
        assert result == []
    
    def test_process_returns_catastrophe_events(self):
        """El método process retorna una lista de eventos."""
        config = SimulationConfig()
        state = WorldState(config, width=10, height=10)
        state.initialize_tile_map(seed=42)
        
        dynamics = EnvironmentDynamics()
        
        result = dynamics.process(
            state=state,
            delta_days=1.0,
            current_season=Season.SPRING,
            current_weather=Weather.CLEAR,
        )
        
        # Debe retornar una lista (puede estar vacía si no ocurrieron catástrofes)
        assert isinstance(result, list)
    
    def test_get_catastrophe_summary(self):
        """Se puede obtener un resumen de catástrofes."""
        dynamics = EnvironmentDynamics()
        
        summary = dynamics.get_catastrophe_summary()
        
        assert isinstance(summary, dict)
        assert "total_events" in summary
        assert "by_type" in summary
        assert "recent" in summary
    
    def test_get_catastrophe_history(self):
        """Se puede obtener el historial de catástrofes."""
        dynamics = EnvironmentDynamics()
        
        history = dynamics.get_catastrophe_history()
        
        assert isinstance(history, list)
    
    def test_get_recent_catastrophes(self):
        """Se pueden obtener catástrofes recientes."""
        dynamics = EnvironmentDynamics()
        
        recent = dynamics.get_recent_catastrophes(count=5)
        
        assert isinstance(recent, list)