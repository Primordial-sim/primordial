"""Tests para CatastropheSystem."""

import pytest
from core.state.world_state import WorldState
from core.config.simulation_config import SimulationConfig
from systems.environment.catastrophe_system import CatastropheSystem
from systems.environment.catastrophe_model import (
    CatastropheType,
    CatastropheSeverity,
    CatastropheEvent,
    severity_from_intensity,
)
from systems.environment.world_config import WorldConfig
from systems.environment.environment_system import Season


class TestCatastropheModel:
    """Tests para el modelo de catástrofes."""
    
    def test_severity_from_intensity(self):
        """La severidad se calcula correctamente desde la intensidad."""
        assert severity_from_intensity(0.9) == CatastropheSeverity.CATASTROPHIC
        assert severity_from_intensity(0.7) == CatastropheSeverity.MAJOR
        assert severity_from_intensity(0.5) == CatastropheSeverity.MODERATE
        assert severity_from_intensity(0.2) == CatastropheSeverity.MINOR
    
    def test_catastrophe_event_to_dict(self):
        """Los eventos se serializan correctamente."""
        event = CatastropheEvent(
            event_id=1,
            catastrophe_type=CatastropheType.EARTHQUAKE,
            severity=CatastropheSeverity.MAJOR,
            epicenter_x=50,
            epicenter_y=50,
            radius=10,
            intensity=0.7,
            occurred_day=100.0,
            tiles_affected=150,
            description="Terremoto de prueba",
        )
        
        data = event.to_dict()
        assert data["event_id"] == 1
        assert data["type"] == "EARTHQUAKE"
        assert data["severity"] == "major"
        assert data["tiles_affected"] == 150


class TestCatastropheSystem:
    """Tests para CatastropheSystem."""
    
    def test_initialization(self):
        """El sistema se inicializa correctamente."""
        system = CatastropheSystem()
        
        assert system.get_event_count() == 0
        assert len(system.base_probabilities) == 8
    
    def test_no_catastrophes_without_tile_map(self):
        """No ocurren catástrofes sin tile_map."""
        config = SimulationConfig()
        state = WorldState(config, width=10, height=10)
        # No inicializar tile_map
        
        system = CatastropheSystem()
        events = system.process(
            state=state,
            delta_days=1.0,
            current_season=Season.SPRING,
        )
        
        assert events == []
    
    def test_earthquake_execution(self):
        """Un terremoto se ejecuta correctamente."""
        config = SimulationConfig()
        state = WorldState(config, width=20, height=20)
        state.initialize_tile_map(seed=42)
        
        system = CatastropheSystem()
        event = system._execute_earthquake(state, 10, 10, 100.0)
        
        assert event is not None
        assert event.catastrophe_type == CatastropheType.EARTHQUAKE
        assert event.epicenter_x == 10
        assert event.epicenter_y == 10
        assert event.tiles_affected > 0
        assert 0.0 <= event.intensity <= 1.0
    
    def test_volcanic_eruption_execution(self):
        """Una erupción volcánica se ejecuta correctamente."""
        config = SimulationConfig()
        state = WorldState(config, width=20, height=20)
        state.initialize_tile_map(seed=42)
        
        system = CatastropheSystem()
        event = system._execute_volcanic_eruption(state, 10, 10, 100.0)
        
        assert event is not None
        assert event.catastrophe_type == CatastropheType.VOLCANIC_ERUPTION
        assert event.tiles_affected > 0
    
    def test_meteorite_execution(self):
        """Un impacto de meteorito se ejecuta correctamente."""
        config = SimulationConfig()
        state = WorldState(config, width=20, height=20)
        state.initialize_tile_map(seed=42)
        
        system = CatastropheSystem()
        event = system._execute_meteorite(state, 10, 10, 100.0)
        
        assert event is not None
        assert event.catastrophe_type == CatastropheType.METEORITE
        assert event.tiles_affected > 0
    
    def test_flood_execution(self):
        """Una inundación se ejecuta correctamente."""
        config = SimulationConfig()
        state = WorldState(config, width=20, height=20)
        state.initialize_tile_map(seed=42)
        
        system = CatastropheSystem()
        event = system._execute_flood(state, 10, 10, 100.0)
        
        assert event is not None
        assert event.catastrophe_type == CatastropheType.FLOOD
    
    def test_fire_execution(self):
        """Un incendio se ejecuta correctamente."""
        config = SimulationConfig()
        state = WorldState(config, width=20, height=20)
        state.initialize_tile_map(seed=42)
        
        system = CatastropheSystem()
        event = system._execute_fire(state, 10, 10, 100.0)
        
        assert event is not None
        assert event.catastrophe_type == CatastropheType.FIRE
    
    def test_storm_execution(self):
        """Una tormenta se ejecuta correctamente."""
        config = SimulationConfig()
        state = WorldState(config, width=20, height=20)
        state.initialize_tile_map(seed=42)
        
        system = CatastropheSystem()
        event = system._execute_storm(state, 10, 10, 100.0)
        
        assert event is not None
        assert event.catastrophe_type == CatastropheType.STORM
    
    def test_drought_execution(self):
        """Una sequía se ejecuta correctamente."""
        config = SimulationConfig()
        state = WorldState(config, width=20, height=20)
        state.initialize_tile_map(seed=42)
        
        system = CatastropheSystem()
        event = system._execute_drought(state, 10, 10, 100.0)
        
        assert event is not None
        assert event.catastrophe_type == CatastropheType.DROUGHT
    
    def test_history_registration(self):
        """Los eventos se registran en el historial."""
        config = SimulationConfig()
        state = WorldState(config, width=20, height=20)
        state.initialize_tile_map(seed=42)
        
        system = CatastropheSystem()
        
        # Ejecutar varias catástrofes manualmente
        for _ in range(5):
            system._execute_fire(state, 10, 10, 100.0)
            event = system._execute_fire(state, 10, 10, 100.0)
            system._register_event(event)
        
        assert system.get_event_count() == 5
    
    def test_get_events_by_type(self):
        """Se pueden filtrar eventos por tipo."""
        config = SimulationConfig()
        state = WorldState(config, width=20, height=20)
        state.initialize_tile_map(seed=42)
        
        system = CatastropheSystem()
        
        # Registrar eventos de diferentes tipos
        fire_event = system._execute_fire(state, 10, 10, 100.0)
        system._register_event(fire_event)
        
        storm_event = system._execute_storm(state, 10, 10, 100.0)
        system._register_event(storm_event)
        
        fire_events = system.get_events_by_type(CatastropheType.FIRE)
        assert len(fire_events) == 1
        
        storm_events = system.get_events_by_type(CatastropheType.STORM)
        assert len(storm_events) == 1
    
    def test_geological_activity_affects_earthquakes(self):
        """La actividad geológica afecta la probabilidad de terremotos."""
        # Mundo con alta actividad geológica
        high_geo_config = WorldConfig(geological_activity=1.0)
        system_high = CatastropheSystem(world_config=high_geo_config)
        
        # Mundo con baja actividad geológica
        low_geo_config = WorldConfig(geological_activity=0.0)
        system_low = CatastropheSystem(world_config=low_geo_config)
        
        prob_high = system_high._calculate_probability(
            CatastropheType.EARTHQUAKE, 1.0, Season.SPRING
        )
        prob_low = system_low._calculate_probability(
            CatastropheType.EARTHQUAKE, 1.0, Season.SPRING
        )
        
        # Alta actividad debe dar mayor probabilidad
        assert prob_high > prob_low
    
    def test_summer_increases_fire_probability(self):
        """El verano aumenta la probabilidad de incendios."""
        system = CatastropheSystem()
        
        prob_summer = system._calculate_probability(
            CatastropheType.FIRE, 1.0, Season.SUMMER
        )
        prob_winter = system._calculate_probability(
            CatastropheType.FIRE, 1.0, Season.WINTER
        )
        
        # Verano debe tener mayor probabilidad de incendios
        assert prob_summer > prob_winter
    
    def test_summary_structure(self):
        """El resumen tiene la estructura correcta."""
        config = SimulationConfig()
        state = WorldState(config, width=20, height=20)
        state.initialize_tile_map(seed=42)
        
        system = CatastropheSystem()
        
        # Registrar algunos eventos
        for _ in range(3):
            event = system._execute_fire(state, 10, 10, 100.0)
            system._register_event(event)
        
        summary = system.get_summary()
        
        assert "total_events" in summary
        assert "by_type" in summary
        assert "recent" in summary
        assert summary["total_events"] == 3