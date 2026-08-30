"""Tests para MovementCapabilities.

Valida que las capacidades se calculan correctamente desde el genoma
para diferentes tipos de organismos.
"""

import pytest

from entities.person.genome import Genome
from entities.person.allele import Gene, Allele
from systems.movement.movement_capabilities import MovementCapabilities


def create_genome_with_traits(traits: dict) -> Genome:
    """Helper para crear un genoma con rasgos específicos."""
    genes = {}
    for trait_id, value in traits.items():
        # Crear alelos con el valor deseado
        allele_a = Allele(value=value, dominance=1.0)
        allele_b = Allele(value=value, dominance=0.0)
        genes[trait_id] = Gene(allele_a, allele_b)
    
    return Genome(genes=genes, species_id="test_species")


class TestMovementCapabilitiesFromGenome:
    """Tests para MovementCapabilities.from_genome()."""
    
    def test_plant_cannot_move(self):
        """Las plantas no pueden moverse (mobility = 0)."""
        genome = create_genome_with_traits({
            "mobility": 0.0,
            "photosynthesis": 1.0,
        })
        
        caps = MovementCapabilities.from_genome(genome)
        
        assert caps.can_move is False
        assert caps.can_migrate is False
        assert caps.can_walk is False
        assert caps.can_fly is False
        assert caps.needs_ground_resources is False  # Fotosíntesis
    
    def test_human_basic_capabilities(self):
        """Un humano puede caminar, tiene visión media, es social."""
        genome = create_genome_with_traits({
            "mobility": 1.0,
            "speed": 1.0,
            "vision": 1.5,
            "sociability": 0.8,
            "curiosity": 0.6,
        })
        
        caps = MovementCapabilities.from_genome(genome)
        
        assert caps.can_move is True
        assert caps.can_walk is True
        assert caps.can_fly is False
        assert caps.can_swim is False
        assert caps.is_social is True
        assert caps.movement_speed == 1.0
        assert caps.vision_range == 1.5
        assert caps.needs_ground_resources is True
    
    def test_bird_can_fly(self):
        """Un ave puede volar y tiene visión excelente."""
        genome = create_genome_with_traits({
            "mobility": 1.0,
            "flight": 1.0,
            "vision": 4.0,
            "speed": 2.0,
            "sociability": 0.3,  # Solitario
            "curiosity": 0.7,
        })
        
        caps = MovementCapabilities.from_genome(genome)
        
        assert caps.can_move is True
        assert caps.can_fly is True
        assert caps.can_walk is True  # También puede caminar
        assert caps.vision_range == 4.0
        assert caps.movement_speed == 2.0
        assert caps.is_social is False
        assert caps.can_migrate is True
    
    def test_wolf_is_social(self):
        """Un lobo es social (manada) y tiene buen olfato."""
        genome = create_genome_with_traits({
            "mobility": 1.0,
            "speed": 1.8,
            "smell": 2.5,
            "sociability": 0.9,
            "territoriality": 0.3,
            "curiosity": 0.5,
        })
        
        caps = MovementCapabilities.from_genome(genome)
        
        assert caps.is_social is True
        assert caps.is_territorial is False  # Social override territorial
        assert caps.smell_range == 2.5
        assert caps.movement_speed == 1.8
    
    def test_eagle_is_territorial(self):
        """Un águila es territorial (no social) y tiene visión excelente."""
        genome = create_genome_with_traits({
            "mobility": 1.0,
            "flight": 1.0,
            "vision": 4.5,
            "sociability": 0.2,  # Solitario
            "territoriality": 0.9,
            "curiosity": 0.4,
        })
        
        caps = MovementCapabilities.from_genome(genome)
        
        assert caps.is_social is False
        assert caps.is_territorial is True
        assert caps.vision_range == 4.5
        assert caps.can_fly is True
    
    def test_fish_can_swim(self):
        """Un pez puede nadar pero no caminar."""
        genome = create_genome_with_traits({
            "mobility": 0.4,  # Movilidad moderada (solo en agua)
            "swimming": 1.0,
            "vision": 0.8,
            "sociability": 0.8,  # Cardumen
            "curiosity": 0.3,
        })
    
        caps = MovementCapabilities.from_genome(genome)
    
        assert caps.can_move is True
        assert caps.can_swim is True
        assert caps.can_walk is False  # No puede caminar (swimming > 0.5)
        assert caps.is_social is True
    
    def test_burrowing_animal(self):
        """Un animal excavador puede moverse bajo tierra."""
        genome = create_genome_with_traits({
            "mobility": 0.8,
            "burrowing": 0.9,
            "vision": 0.3,  # Mala visión
            "smell": 1.5,
            "sociability": 0.2,  # Solitario
            "curiosity": 0.4,
        })
        
        caps = MovementCapabilities.from_genome(genome)
        
        assert caps.can_burrow is True
        assert caps.vision_range == 0.5  # Mínimo clampeado
        assert caps.smell_range == 1.5
    
    def test_missing_traits_use_defaults(self):
        """Si faltan rasgos, usa valores por defecto apropiados."""
        # Genoma vacío (sin rasgos)
        genome = Genome(genes={}, species_id="unknown")
        
        caps = MovementCapabilities.from_genome(genome)
        
        # Debería tener capacidades básicas por defecto
        assert caps.can_move is True  # mobility default = 0.5
        assert caps.movement_speed == 1.0  # speed default
        assert caps.vision_range == 1.0  # vision default
        assert caps.needs_ground_resources is True  # photosynthesis default = 0
    
    def test_can_migrate_requires_movement_capacity(self):
        """Solo puede migrar si tiene capacidad de movimiento."""
        # Baja movilidad
        genome_low = create_genome_with_traits({
            "mobility": 0.05,  # Muy bajo
            "speed": 0.1,
            "curiosity": 0.9,
        })
        
        caps_low = MovementCapabilities.from_genome(genome_low)
        assert caps_low.can_migrate is False
        
        # Alta movilidad
        genome_high = create_genome_with_traits({
            "mobility": 1.0,
            "speed": 1.5,
            "curiosity": 0.8,
        })
        
        caps_high = MovementCapabilities.from_genome(genome_high)
        assert caps_high.can_migrate is True
    
    def test_values_are_clamped(self):
        """Los valores se clampean a rangos válidos."""
        genome = create_genome_with_traits({
            "mobility": 10.0,  # Fuera de rango
            "speed": 5.0,      # Fuera de rango (max 2.0)
            "vision": 10.0,    # Fuera de rango (max 5.0)
            "smell": -1.0,     # Fuera de rango (min 0.0)
        })
        
        caps = MovementCapabilities.from_genome(genome)
        
        assert caps.movement_speed == 2.0  # Máximo
        assert caps.vision_range == 5.0    # Máximo
        assert caps.smell_range == 0.0     # Mínimo
    
    def test_str_representation(self):
        """La representación string es legible."""
        genome = create_genome_with_traits({
            "mobility": 1.0,
            "flight": 1.0,
            "speed": 2.0,
            "vision": 3.0,
            "sociability": 0.8,
            "curiosity": 0.7,
        })
        
        caps = MovementCapabilities.from_genome(genome)
        str_repr = str(caps)
        
        assert "MovementCapabilities" in str_repr
        assert "fly" in str_repr
        assert "social" in str_repr


class TestMovementCapabilitiesIntegration:
    """Tests de integración con diferentes tipos de organismos."""
    
    def test_bacteria_capabilities(self):
        """Una bacteria tiene capacidades muy limitadas."""
        genome = create_genome_with_traits({
            "mobility": 0.2,  # Movilidad muy baja
            "division_speed": 1.0,
            "antibiotic_resistance": 0.8,
        })
        
        caps = MovementCapabilities.from_genome(genome)
        
        assert caps.can_move is True  # mobility > 0.1
        assert caps.can_walk is False  # mobility < 0.3
        assert caps.can_migrate is False  # No tiene capacidad de movimiento
        assert caps.movement_speed == 1.0  # Default
    
    def test_tree_capabilities(self):
        """Un árbol es completamente estático."""
        genome = create_genome_with_traits({
            "mobility": 0.0,
            "photosynthesis": 1.0,
            "growth_rate": 0.5,
        })
        
        caps = MovementCapabilities.from_genome(genome)
        
        assert caps.can_move is False
        assert caps.can_migrate is False
        assert caps.needs_ground_resources is False  # Fotosíntesis
        assert caps.movement_speed == 1.0  # Default pero irrelevante