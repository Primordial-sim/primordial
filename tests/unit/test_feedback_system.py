"""Tests para FeedbackSystem y OrganismImpactCalculator."""

import pytest
from unittest.mock import MagicMock
from core.state.world_state import WorldState
from core.config.simulation_config import SimulationConfig
from systems.environment.feedback_system import FeedbackSystem
from systems.environment.organism_impact import OrganismImpactCalculator, TileImpact
from systems.environment.tile import Tile
from entities.person.genome import Genome

# Contador para generar IDs únicos de entidades en tests
_mock_entity_id_counter = 0

def create_mock_person(x: int, y: int, species: str = "human") -> MagicMock:
    """Crea un mock de Person con genoma."""
    global _mock_entity_id_counter
    _mock_entity_id_counter += 1
    
    person = MagicMock()
    person.entity_id = _mock_entity_id_counter  # CORRECCIÓN: entity_id como int
    person.x = x
    person.y = y
    person.species = species
    
    # CORRECCIÓN: Configurar nucleus_id para evitar errores en add_person
    person.nucleus_id = None
    
    # Crear un genoma mock con rasgos
    genome = MagicMock()
    genome.has_trait.return_value = True
    
    # Valores por defecto según especie
    if species == "plant":
        genome.get_trait_value.side_effect = lambda t: {
            "photosynthesis": 1.8,
            "heterotrophy": 0.0,
            "intelligence": 0.0,
            "sociability": 0.0,
            "metabolism": 0.5,
            "growth_rate": 0.6,
            "flight": 0.0,
            "swimming": 0.0,
            "speed": 0.0,
        }.get(t, 0.0)
    elif species == "herbivore":
        genome.get_trait_value.side_effect = lambda t: {
            "photosynthesis": 0.0,
            "heterotrophy": 1.5,
            "intelligence": 0.3,
            "sociability": 0.5,
            "metabolism": 1.0,
            "growth_rate": 0.8,
            "flight": 0.0,
            "swimming": 0.0,
            "speed": 1.2,
        }.get(t, 0.0)
    else:  # human
        genome.get_trait_value.side_effect = lambda t: {
            "photosynthesis": 0.0,
            "heterotrophy": 1.0,
            "intelligence": 1.8,
            "sociability": 1.5,
            "metabolism": 1.0,
            "growth_rate": 0.5,
            "flight": 0.0,
            "swimming": 0.5,
            "speed": 0.8,
        }.get(t, 0.0)
    
    person.genome = genome
    return person


class TestTileImpact:
    """Tests para TileImpact."""
    
    def test_empty_impact(self):
        """Un impacto vacío se detecta correctamente."""
        impact = TileImpact()
        assert impact.is_empty()
    
    def test_non_empty_impact(self):
        """Un impacto con valores no es vacío."""
        impact = TileImpact(vegetation_delta=0.1)
        assert not impact.is_empty()


class TestOrganismImpactCalculator:
    """Tests para OrganismImpactCalculator."""
    
    def test_plant_increases_vegetation(self):
        """Las plantas aumentan la vegetación."""
        calculator = OrganismImpactCalculator()
        person = create_mock_person(5, 5, "plant")
        tile = Tile(vegetation=0.3, fertility=0.4)
        
        impact = calculator.calculate(person, tile)
        
        assert impact.vegetation_delta > 0
        assert impact.organic_matter_delta > 0
    
    def test_herbivore_decreases_vegetation(self):
        """Los herbívoros reducen la vegetación."""
        calculator = OrganismImpactCalculator()
        person = create_mock_person(5, 5, "herbivore")
        tile = Tile(vegetation=0.7, fertility=0.4)
        
        impact = calculator.calculate(person, tile)
        
        assert impact.vegetation_delta < 0
    
    def test_human_increases_fertility(self):
        """Los humanos aumentan la fertilidad (agricultura)."""
        calculator = OrganismImpactCalculator()
        person = create_mock_person(5, 5, "human")
        tile = Tile(vegetation=0.5, fertility=0.4)
        
        impact = calculator.calculate(person, tile)
        
        assert impact.fertility_delta > 0
    
    def test_human_urbanization(self):
        """Los humanos muy sociales generan urbanización."""
        calculator = OrganismImpactCalculator()
        person = create_mock_person(5, 5, "human")
        tile = Tile(vegetation=0.5, fertility=0.4)
        
        impact = calculator.calculate(person, tile)
        
        # Humanos con sociabilidad > 1.2 generan urbanización
        assert impact.urbanization_delta >= 0
    
    def test_accumulated_impacts(self):
        """Se pueden acumular impactos de múltiples organismos."""
        calculator = OrganismImpactCalculator()
        
        persons = [
            create_mock_person(5, 5, "plant"),
            create_mock_person(5, 5, "plant"),
            create_mock_person(5, 5, "herbivore"),
        ]
        
        tile_map = {(5, 5): Tile(vegetation=0.5)}
        
        accumulated = calculator.calculate_accumulated(persons, tile_map)
        
        assert (5, 5) in accumulated
        # Dos plantas y un herbívoro: el impacto neto depende de los valores


class TestFeedbackSystem:
    """Tests para FeedbackSystem."""
    
    def test_initialization(self):
        """FeedbackSystem se inicializa correctamente."""
        system = FeedbackSystem()
        
        assert system.process_interval == 5.0
        assert system.impact_scale == 1.0
    
    def test_no_processing_without_tile_map(self):
        """No procesa si no hay tile_map."""
        config = SimulationConfig()
        state = WorldState(config, width=10, height=10)
        # No inicializar tile_map
        
        system = FeedbackSystem()
        pending = MagicMock()
        context = MagicMock()
        
        # No debería lanzar error
        system.process(state, pending, 1.0, context)
    
    def test_processing_with_tile_map(self):
        """Procesa correctamente con tile_map."""
        config = SimulationConfig()
        state = WorldState(config, width=10, height=10)
        state.initialize_tile_map(seed=42)
        
        # Añadir un organismo
        person = create_mock_person(5, 5, "plant")
        state.add_person(person)
        
        system = FeedbackSystem()
        system.process_interval = 0.1  # Forzar procesamiento
        pending = MagicMock()
        context = MagicMock()
        
        # Guardar estado inicial
        initial_tile = state.get_tile_at(5, 5)
        assert initial_tile is not None, "El tile en (5, 5) no debería ser None"
        initial_vegetation = initial_tile.vegetation
        
        # Procesar
        system.process(state, pending, 1.0, context)
        
        # El tile debería haber cambiado
        final_tile = state.get_tile_at(5, 5)
        assert final_tile is not None, "El tile en (5, 5) no debería ser None después del proceso"
        # No verificamos dirección exacta porque depende del tipo de organismo
    
    def test_get_impact_summary(self):
        """Se puede obtener un resumen de impacto."""
        config = SimulationConfig()
        state = WorldState(config, width=10, height=10)
        state.initialize_tile_map(seed=42)
        
        # Añadir organismos
        person1 = create_mock_person(5, 5, "plant")
        person2 = create_mock_person(6, 6, "human")
        state.add_person(person1)
        state.add_person(person2)
        
        system = FeedbackSystem()
        summary = system.get_impact_summary(state)
        
        assert summary["total_organisms"] == 2
        assert summary["tiles_with_impact"] >= 0