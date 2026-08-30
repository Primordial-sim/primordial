"""Tests para CognitiveCapabilities.

Valida que las capacidades cognitivas se calculan correctamente
desde el genoma para diferentes tipos de organismos.
"""

import pytest

from entities.person.genome import Genome
from entities.person.allele import Gene, Allele
from systems.behavior.cognitive_capabilities import CognitiveCapabilities


def create_genome_with_traits(traits: dict) -> Genome:
    """Helper para crear un genoma con rasgos específicos."""
    genes = {}
    for trait_id, value in traits.items():
        allele_a = Allele(value=value, dominance=1.0)
        allele_b = Allele(value=value, dominance=0.0)
        genes[trait_id] = Gene(allele_a, allele_b)
    
    return Genome(genes=genes, species_id="test_species")


class TestCognitiveCapabilitiesFromGenome:
    """Tests para CognitiveCapabilities.from_genome()."""
    
    def test_plant_has_no_cognition(self):
        """Las plantas no tienen sistema nervioso ni cognición."""
        genome = create_genome_with_traits({
            "nervous_system": 0.0,
            "intelligence": 0.0,
            "sociability": 0.0,
            "temperament": 0.0,
        })
        
        caps = CognitiveCapabilities.from_genome(genome)
        
        assert caps.has_nervous_system is False
        assert caps.has_emotions is False
        assert caps.has_complex_brain is False
        assert caps.has_episodic_memory is False
        assert caps.has_basic_motivations is False
        assert caps.has_complex_motivations is False
        assert caps.has_pair_bonding is False
        assert caps.has_family_structure is False
        assert caps.has_social_concepts is False
        assert caps.cognitive_level == 0.0
    
    def test_bacteria_has_no_nervous_system(self):
        """Las bacterias no tienen sistema nervioso."""
        genome = create_genome_with_traits({
            "nervous_system": 0.05,  # Muy bajo
            "intelligence": 0.0,
        })
        
        caps = CognitiveCapabilities.from_genome(genome)
        
        assert caps.has_nervous_system is False
        assert caps.has_emotions is False
        assert caps.has_basic_motivations is False
    
    def test_insect_simple_nervous_system(self):
        """Un insecto tiene sistema nervioso simple pero no complejo."""
        genome = create_genome_with_traits({
            "nervous_system": 0.4,  # Moderado
            "intelligence": 0.2,   # Baja
            "sociability": 0.3,
            "temperament": 0.3,
        })
        
        caps = CognitiveCapabilities.from_genome(genome)
        
        assert caps.has_nervous_system is True
        assert caps.has_emotions is True  # > 0.3
        assert caps.has_complex_brain is False  # intelligence < 0.3
        assert caps.has_episodic_memory is False
        assert caps.has_basic_motivations is True
        assert caps.has_complex_motivations is False
        assert caps.has_social_concepts is False
    
    def test_fish_basic_emotions(self):
        """Un pez tiene emociones básicas pero no memoria episódica."""
        genome = create_genome_with_traits({
            "nervous_system": 0.5,
            "intelligence": 0.25,  # Cambiado de 0.3 a 0.25 para quedar claramente por debajo del límite
            "sociability": 0.6,
            "temperament": 0.4,
        })
        
        caps = CognitiveCapabilities.from_genome(genome)
        
        assert caps.has_nervous_system is True
        assert caps.has_emotions is True
        assert caps.has_complex_brain is False  # intelligence < 0.3
        assert caps.has_episodic_memory is False
        assert caps.has_basic_motivations is True
        assert caps.has_pair_bonding is False
    
    def test_wolf_social_bonds(self):
        """Un lobo tiene vínculos sociales pero no conceptos sociales complejos."""
        genome = create_genome_with_traits({
            "nervous_system": 0.8,
            "intelligence": 0.6,
            "sociability": 0.85,  # Alta
            "temperament": 0.5,
        })
        
        caps = CognitiveCapabilities.from_genome(genome)
        
        assert caps.has_nervous_system is True
        assert caps.has_emotions is True
        assert caps.has_complex_brain is True
        assert caps.has_episodic_memory is True
        assert caps.has_complex_motivations is False  # intelligence < 0.7
        assert caps.has_pair_bonding is True
        assert caps.has_family_structure is True  # sociability > 0.8 and intelligence > 0.6
        assert caps.has_social_concepts is False  # intelligence < 0.8
    
    def test_human_full_cognition(self):
        """Un humano tiene cognición completa."""
        genome = create_genome_with_traits({
            "nervous_system": 0.95,
            "intelligence": 0.95,
            "sociability": 0.8,
            "temperament": 0.6,
        })
        
        caps = CognitiveCapabilities.from_genome(genome)
        
        assert caps.has_nervous_system is True
        assert caps.has_emotions is True
        assert caps.has_complex_brain is True
        assert caps.has_episodic_memory is True
        assert caps.has_basic_motivations is True
        assert caps.has_complex_motivations is True
        assert caps.has_pair_bonding is True
        assert caps.has_family_structure is True
        assert caps.has_social_concepts is True
        assert caps.cognitive_level > 0.8
        assert caps.emotional_complexity > 0.7
        assert caps.social_complexity > 0.7
    
    def test_bird_moderate_intelligence(self):
        """Un ave tiene inteligencia moderada."""
        genome = create_genome_with_traits({
            "nervous_system": 0.7,
            "intelligence": 0.55,
            "sociability": 0.5,
            "temperament": 0.5,
        })
        
        caps = CognitiveCapabilities.from_genome(genome)
        
        assert caps.has_complex_brain is True
        assert caps.has_episodic_memory is True  # intelligence > 0.5
        assert caps.has_complex_motivations is False  # intelligence < 0.7
        assert caps.has_pair_bonding is False  # sociability < 0.7
        assert caps.has_social_concepts is False
    
    def test_missing_traits_use_defaults(self):
        """Si faltan rasgos, usa valores por defecto (0.0)."""
        genome = Genome(genes={}, species_id="unknown")
        
        caps = CognitiveCapabilities.from_genome(genome)
        
        # Sin rasgos = sin sistema nervioso = sin cognición
        assert caps.has_nervous_system is False
        assert caps.has_emotions is False
        assert caps.cognitive_level == 0.0
    
    def test_values_are_clamped(self):
        """Los niveles continuos se clampean a [0.0, 1.0]."""
        genome = create_genome_with_traits({
            "nervous_system": 5.0,    # Fuera de rango
            "intelligence": 10.0,     # Fuera de rango
            "sociability": 8.0,
            "temperament": 3.0,
        })
        
        caps = CognitiveCapabilities.from_genome(genome)
        
        assert 0.0 <= caps.cognitive_level <= 1.0
        assert 0.0 <= caps.emotional_complexity <= 1.0
        assert 0.0 <= caps.social_complexity <= 1.0


class TestCognitiveCapabilitiesMethods:
    """Tests para métodos auxiliares."""
    
    def test_can_form_trauma_overcrowding(self):
        """Solo organismos con emociones pueden tener trauma por hacinamiento."""
        plant = CognitiveCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.0,
        }))
        insect = CognitiveCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.4,
            "intelligence": 0.2,
        }))
        
        assert plant.can_form_trauma("overcrowding") is False
        assert insect.can_form_trauma("overcrowding") is True
    
    def test_can_form_trauma_abandonment(self):
        """Solo organismos con vínculos pueden tener trauma por abandono."""
        fish = CognitiveCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.5,
            "intelligence": 0.3,
            "sociability": 0.4,
        }))
        wolf = CognitiveCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.8,
            "intelligence": 0.6,
            "sociability": 0.85,
        }))
        
        assert fish.can_form_trauma("abandonment") is False
        assert wolf.can_form_trauma("abandonment") is True
    
    def test_can_form_trauma_adoption(self):
        """Solo organismos con estructura familiar pueden tener trauma por adopción."""
        wolf = CognitiveCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.8,
            "intelligence": 0.6,
            "sociability": 0.85,
        }))
        human = CognitiveCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.95,
            "intelligence": 0.95,
            "sociability": 0.8,
        }))
        
        # Wolf tiene estructura familiar
        assert wolf.can_form_trauma("adoption") is True
        # Humano también
        assert human.can_form_trauma("adoption") is True
    
    def test_can_have_memory_type_basic(self):
        """Tipos básicos de memoria requieren memoria episódica."""
        insect = CognitiveCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.4,
            "intelligence": 0.2,
        }))
        wolf = CognitiveCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.8,
            "intelligence": 0.6,
            "sociability": 0.85,
        }))
        
        assert insect.can_have_memory_type("experience") is False
        assert wolf.can_have_memory_type("experience") is True
        assert wolf.can_have_memory_type("companion") is True
        assert wolf.can_have_memory_type("conflict") is True
    
    def test_can_have_memory_type_social(self):
        """Tipos sociales requieren conceptos sociales (humanos principalmente)."""
        wolf = CognitiveCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.8,
            "intelligence": 0.6,
            "sociability": 0.85,
        }))
        human = CognitiveCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.95,
            "intelligence": 0.95,
            "sociability": 0.8,
        }))
        
        # Lobo NO puede formar memorias de matrimonio, divorcio, etc.
        assert wolf.can_have_memory_type("marriage") is False
        assert wolf.can_have_memory_type("divorce") is False
        assert wolf.can_have_memory_type("adoption") is False
        
        # Humano SÍ puede
        assert human.can_have_memory_type("marriage") is True
        assert human.can_have_memory_type("divorce") is True
        assert human.can_have_memory_type("adoption") is True
    
    def test_can_have_motivation_basic(self):
        """Motivaciones básicas (protection) requieren sistema nervioso mínimo."""
        plant = CognitiveCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.0,
        }))
        fish = CognitiveCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.5,
            "intelligence": 0.3,
        }))
        
        assert plant.can_have_motivation("protection") is False
        assert fish.can_have_motivation("protection") is True
    
    def test_can_have_motivation_complex(self):
        """Motivaciones complejas requieren cerebro avanzado."""
        wolf = CognitiveCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.8,
            "intelligence": 0.6,
            "sociability": 0.85,
        }))
        human = CognitiveCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.95,
            "intelligence": 0.95,
            "sociability": 0.8,
        }))
        
        # Lobo NO tiene rebellion, independence, partnership (como concepto)
        assert wolf.can_have_motivation("rebellion") is False
        assert wolf.can_have_motivation("independence") is False
        assert wolf.can_have_motivation("partnership") is False
        
        # Humano SÍ tiene todas las motivaciones complejas
        assert human.can_have_motivation("rebellion") is True
        assert human.can_have_motivation("independence") is True
        assert human.can_have_motivation("partnership") is True
        assert human.can_have_motivation("migration") is True
    
    def test_can_have_motivation_exploration(self):
        """Exploración requiere emociones (curiosidad)."""
        insect = CognitiveCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.4,
            "intelligence": 0.2,
        }))
        fish = CognitiveCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.5,
            "intelligence": 0.3,
        }))
        
        assert insect.can_have_motivation("exploration") is True  # Tiene emociones
        assert fish.can_have_motivation("exploration") is True
    
    def test_str_representation(self):
        """La representación string es legible."""
        genome = create_genome_with_traits({
            "nervous_system": 0.9,
            "intelligence": 0.9,
            "sociability": 0.8,
            "temperament": 0.6,
        })
        
        caps = CognitiveCapabilities.from_genome(genome)
        str_repr = str(caps)
        
        assert "CognitiveCapabilities" in str_repr
        assert "level=" in str_repr
        assert "nervous=True" in str_repr
        assert "emotions=True" in str_repr
        assert "social_concepts=True" in str_repr


class TestCognitiveCapabilitiesIntegration:
    """Tests de integración con diferentes tipos de organismos."""
    
    def test_dolphin_high_cognition(self):
        """Un delfín tiene cognición alta (casi humana)."""
        genome = create_genome_with_traits({
            "nervous_system": 0.9,
            "intelligence": 0.85,
            "sociability": 0.9,
            "temperament": 0.7,
        })
        
        caps = CognitiveCapabilities.from_genome(genome)
        
        assert caps.has_complex_motivations is True
        assert caps.has_social_concepts is True
        assert caps.cognitive_level > 0.8
    
    def test_reptile_low_cognition(self):
        """Un reptil tiene cognición baja."""
        genome = create_genome_with_traits({
            "nervous_system": 0.5,
            "intelligence": 0.25,
            "sociability": 0.2,
            "temperament": 0.4,
        })
        
        caps = CognitiveCapabilities.from_genome(genome)
        
        assert caps.has_nervous_system is True
        assert caps.has_emotions is True
        assert caps.has_complex_brain is False  # intelligence < 0.3
        assert caps.has_episodic_memory is False
        assert caps.has_complex_motivations is False
        assert caps.has_pair_bonding is False
    
    def test_ant_colony_social_but_simple(self):
        """Una hormiga es social pero sin cognición compleja."""
        genome = create_genome_with_traits({
            "nervous_system": 0.4,
            "intelligence": 0.15,
            "sociability": 0.95,  # Muy alta (colonia)
            "temperament": 0.2,
        })
        
        caps = CognitiveCapabilities.from_genome(genome)
        
        # A pesar de ser muy social, no tiene cerebro para conceptos
        assert caps.has_complex_brain is False
        assert caps.has_pair_bonding is False  # intelligence < 0.5
        assert caps.has_family_structure is False
        assert caps.has_social_concepts is False
        # Pero sí tiene motivaciones básicas
        assert caps.has_basic_motivations is True