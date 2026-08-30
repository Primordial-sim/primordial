"""Tests para ReproductiveCapabilities.

Valida que las capacidades reproductivas se calculan correctamente
desde el genoma para diferentes tipos de organismos.
"""

import pytest

from entities.person.genome import Genome
from entities.person.allele import Gene, Allele
from systems.reproduction.reproductive_capabilities import ReproductiveCapabilities


def create_genome_with_traits(traits: dict) -> Genome:
    """Helper para crear un genoma con rasgos específicos."""
    genes = {}
    for trait_id, value in traits.items():
        allele_a = Allele(value=value, dominance=1.0)
        allele_b = Allele(value=value, dominance=0.0)
        genes[trait_id] = Gene(allele_a, allele_b)
    
    return Genome(genes=genes, species_id="test_species")


class TestReproductiveCapabilitiesFromGenome:
    """Tests para ReproductiveCapabilities.from_genome()."""
    
    def test_plant_asexual_reproduction(self):
        """Las plantas se reproducen asexualmente (semillas/esporas)."""
        genome = create_genome_with_traits({
            "fertility": 0.8,
            "metabolism": 0.6,
            "photosynthesis": 1.0,
            "nervous_system": 0.0,
            "intelligence": 0.0,
            "sociability": 0.0,
        })
        
        caps = ReproductiveCapabilities.from_genome(genome)
        
        assert caps.can_reproduce is True
        assert caps.reproduction_type == "asexual"
        assert caps.requires_partner is False
        assert caps.can_gestate is False
        assert caps.gestation_type == "none"
        assert caps.has_parental_care is False
        assert caps.can_conceive is False
        assert caps.has_postpartum is False
        assert caps.is_asexual_reproduction() is True
    
    def test_bacteria_binary_fission(self):
        """Las bacterias se reproducen por fisión binaria."""
        genome = create_genome_with_traits({
            "fertility": 0.9,
            "metabolism": 0.8,
            "nervous_system": 0.0,
            "intelligence": 0.0,
        })
        
        caps = ReproductiveCapabilities.from_genome(genome)
        
        assert caps.can_reproduce is True
        assert caps.reproduction_type == "asexual"
        assert caps.requires_partner is False
        assert caps.can_gestate is False
        assert caps.has_parental_care is False
    
    def test_fish_oviparous(self):
        """Los peces son ovíparos (ponen huevos)."""
        genome = create_genome_with_traits({
            "fertility": 0.7,
            "metabolism": 0.7,
            "nervous_system": 0.5,
            "intelligence": 0.3,
            "sociability": 0.5,
        })
        
        caps = ReproductiveCapabilities.from_genome(genome)
        
        assert caps.can_reproduce is True
        assert caps.reproduction_type == "sexual"
        assert caps.requires_partner is False  # sociability < 0.6
        assert caps.can_gestate is True
        assert caps.gestation_type == "oviparous"
        assert caps.has_parental_care is False
        assert caps.can_conceive is False
        assert caps.has_postpartum is False
        assert caps.is_oviparous() is True
    
    def test_bird_oviparous_with_care(self):
        """Las aves son ovíparas con cuidado parental."""
        genome = create_genome_with_traits({
            "fertility": 0.6,
            "metabolism": 0.8,
            "nervous_system": 0.7,
            "intelligence": 0.6,
            "sociability": 0.8,
        })
        
        caps = ReproductiveCapabilities.from_genome(genome)
        
        assert caps.can_reproduce is True
        assert caps.reproduction_type == "sexual"
        assert caps.requires_partner is True
        assert caps.can_gestate is True
        assert caps.gestation_type == "oviparous"
        assert caps.has_parental_care is True
        assert caps.can_conceive is False  # Ovíparos no conciben
        assert caps.care_duration_days > 0
    
    def test_wolf_viviparous(self):
        """Los lobos son vivíparos con cuidado parental."""
        genome = create_genome_with_traits({
            "fertility": 0.7,
            "metabolism": 0.9,
            "nervous_system": 0.8,
            "intelligence": 0.6,
            "sociability": 0.85,
            "heterotrophy": 1.0,
        })
        
        caps = ReproductiveCapabilities.from_genome(genome)
        
        assert caps.can_reproduce is True
        assert caps.reproduction_type == "sexual"
        assert caps.requires_partner is True
        assert caps.can_gestate is True
        assert caps.gestation_type == "viviparous"
        assert caps.has_parental_care is True
        assert caps.can_conceive is True
        assert caps.has_postpartum is True
        assert caps.is_viviparous() is True
    
    def test_human_full_reproduction(self):
        """Los humanos tienen reproducción completa."""
        genome = create_genome_with_traits({
            "fertility": 0.8,
            "metabolism": 0.9,
            "nervous_system": 0.95,
            "intelligence": 0.95,
            "sociability": 0.9,
            "heterotrophy": 1.0,
            "longevity": 1.0,
        })
        
        caps = ReproductiveCapabilities.from_genome(genome)
        
        assert caps.can_reproduce is True
        assert caps.reproduction_type == "sexual"
        assert caps.requires_partner is True
        assert caps.can_gestate is True
        assert caps.gestation_type == "viviparous"
        assert caps.has_parental_care is True
        assert caps.can_conceive is True
        assert caps.has_postpartum is True
        assert caps.gestation_days > 200  # Gestación humana ~270 días
        assert caps.litter_size_min == 1
        assert caps.litter_size_max >= 1
    
    def test_insect_oviparous_no_care(self):
        """Los insectos son ovíparos sin cuidado parental."""
        genome = create_genome_with_traits({
            "fertility": 0.9,
            "metabolism": 0.7,
            "nervous_system": 0.4,
            "intelligence": 0.2,
            "sociability": 0.3,
        })
        
        caps = ReproductiveCapabilities.from_genome(genome)
        
        assert caps.can_reproduce is True
        assert caps.reproduction_type == "sexual"
        assert caps.requires_partner is False
        assert caps.can_gestate is True
        assert caps.gestation_type == "oviparous"
        assert caps.has_parental_care is False
        assert caps.litter_size_max > 5  # Muchos huevos
    
    def test_no_reproduction_when_infertile(self):
        """Organismos infértiles no pueden reproducirse."""
        genome = create_genome_with_traits({
            "fertility": 0.0,
            "metabolism": 0.5,
        })
        
        caps = ReproductiveCapabilities.from_genome(genome)
        
        assert caps.can_reproduce is False
        assert caps.litter_size_min == 0
        assert caps.litter_size_max == 0
    
    def test_missing_traits_use_defaults(self):
        """Si faltan rasgos, usa valores por defecto."""
        genome = Genome(genes={}, species_id="unknown")
        
        caps = ReproductiveCapabilities.from_genome(genome)
        
        # Con valores por defecto (fertility=0.5, metabolism=0.5)
        assert caps.can_reproduce is True
        assert isinstance(caps.reproduction_type, str)
        assert isinstance(caps.gestation_type, str)
    
    def test_litter_size_bounds(self):
        """El tamaño de camada tiene límites razonables."""
        genome = create_genome_with_traits({
            "fertility": 0.8,
            "metabolism": 0.8,
            "nervous_system": 0.8,
            "intelligence": 0.7,
            "sociability": 0.8,
            "heterotrophy": 0.9,
        })
        
        caps = ReproductiveCapabilities.from_genome(genome)
        
        assert caps.litter_size_min >= 0
        assert caps.litter_size_max >= caps.litter_size_min
        assert caps.litter_size_max <= 100  # Límite razonable
    
    def test_gestation_days_reasonable(self):
        """La duración de gestación es razonable."""
        genome = create_genome_with_traits({
            "fertility": 0.8,
            "metabolism": 0.8,
            "nervous_system": 0.9,
            "intelligence": 0.8,
            "sociability": 0.8,
            "heterotrophy": 0.9,
            "longevity": 1.5,
        })
        
        caps = ReproductiveCapabilities.from_genome(genome)
        
        if caps.gestation_type != "none":
            assert caps.gestation_days > 0
            assert caps.gestation_days < 400  # Menos de 400 días
    
    def test_is_sexual_reproduction(self):
        """Verifica el método is_sexual_reproduction()."""
        human = ReproductiveCapabilities.from_genome(create_genome_with_traits({
            "fertility": 0.8,
            "metabolism": 0.9,
            "nervous_system": 0.95,
            "intelligence": 0.95,
            "sociability": 0.9,
        }))
        
        plant = ReproductiveCapabilities.from_genome(create_genome_with_traits({
            "fertility": 0.8,
            "metabolism": 0.6,
            "photosynthesis": 1.0,
            "nervous_system": 0.0,
        }))
        
        assert human.is_sexual_reproduction() is True
        assert plant.is_sexual_reproduction() is False
    
    def test_can_form_nucleus(self):
        """Solo organismos con cuidado parental pueden formar núcleo."""
        human = ReproductiveCapabilities.from_genome(create_genome_with_traits({
            "fertility": 0.8,
            "metabolism": 0.9,
            "nervous_system": 0.95,
            "intelligence": 0.95,
            "sociability": 0.9,
        }))
        
        fish = ReproductiveCapabilities.from_genome(create_genome_with_traits({
            "fertility": 0.7,
            "metabolism": 0.7,
            "nervous_system": 0.5,
            "intelligence": 0.3,
            "sociability": 0.5,
        }))
        
        assert human.can_form_nucleus() is True
        assert fish.can_form_nucleus() is False
    
    def test_str_representation(self):
        """La representación string es legible."""
        genome = create_genome_with_traits({
            "fertility": 0.8,
            "metabolism": 0.9,
            "nervous_system": 0.9,
            "intelligence": 0.8,
            "sociability": 0.8,
            "heterotrophy": 0.9,
        })
        
        caps = ReproductiveCapabilities.from_genome(genome)
        str_repr = str(caps)
        
        assert "ReproductiveCapabilities" in str_repr
        assert "type=" in str_repr
        assert "gestation=" in str_repr
        assert "care=" in str_repr


class TestReproductiveCapabilitiesIntegration:
    """Tests de integración con diferentes tipos de organismos."""
    
    def test_reptile_oviparous(self):
        """Los reptiles son ovíparos."""
        genome = create_genome_with_traits({
            "fertility": 0.6,
            "metabolism": 0.7,
            "nervous_system": 0.5,
            "intelligence": 0.3,
            "sociability": 0.4,
        })
        
        caps = ReproductiveCapabilities.from_genome(genome)
        
        assert caps.can_reproduce is True
        assert caps.gestation_type == "oviparous"
        assert caps.has_parental_care is False
    
    def test_amphibian_oviparous(self):
        """Los anfibios son ovíparos."""
        genome = create_genome_with_traits({
            "fertility": 0.7,
            "metabolism": 0.6,
            "nervous_system": 0.4,
            "intelligence": 0.25,
            "sociability": 0.4,
        })
        
        caps = ReproductiveCapabilities.from_genome(genome)
        
        assert caps.can_reproduce is True
        assert caps.gestation_type == "oviparous"
        assert caps.can_conceive is False
    
    def test_hermaphrodite_self_fertilization(self):
        """Organismos hermafroditas pueden autofecundarse."""
        genome = create_genome_with_traits({
            "fertility": 0.7,
            "metabolism": 0.7,
            "nervous_system": 0.2,  # Sistema nervioso muy simple
            "intelligence": 0.1,
            "sociability": 0.2,
        })
        
        caps = ReproductiveCapabilities.from_genome(genome)
        
        assert caps.can_reproduce is True
        assert caps.reproduction_type == "sexual"
        assert caps.requires_partner is False  # Hermafrodita