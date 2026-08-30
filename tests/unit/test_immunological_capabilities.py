"""Tests para ImmunologicalCapabilities.

Valida que las capacidades inmunológicas se calculan correctamente
desde el genoma para diferentes tipos de organismos.
"""

import pytest

from entities.person.genome import Genome
from entities.person.allele import Gene, Allele
from systems.diseases.immunological_capabilities import ImmunologicalCapabilities


def create_genome_with_traits(traits: dict) -> Genome:
    """Helper para crear un genoma con rasgos específicos."""
    genes = {}
    for trait_id, value in traits.items():
        # Crear alelos con el valor deseado
        allele_a = Allele(value=value, dominance=1.0)
        allele_b = Allele(value=value, dominance=0.0)
        genes[trait_id] = Gene(allele_a, allele_b)
    
    return Genome(genes=genes, species_id="test_species")


class TestImmunologicalCapabilitiesFromGenome:
    """Tests para ImmunologicalCapabilities.from_genome()."""
    
    def test_plant_cannot_get_sick(self):
        """Las plantas no se enferman (sin sistema inmune complejo)."""
        genome = create_genome_with_traits({
            "immunity": 0.0,
            "photosynthesis": 1.0,
            "nervous_system": 0.0,
            "metabolism": 0.2,
        })
        
        caps = ImmunologicalCapabilities.from_genome(genome)
        
        assert caps.has_immune_system is False
        assert caps.can_get_sick is False
        assert caps.susceptible_to_viruses is False
        assert caps.can_form_immunological_memory is False
    
    def test_human_full_immunity(self):
        """Un humano tiene inmunidad completa (adaptativa + innata)."""
        genome = create_genome_with_traits({
            "immunity": 0.8,
            "nervous_system": 0.9,
            "metabolism": 0.9,
            "heterotrophy": 1.0,
            "longevity": 1.0,
        })
        
        caps = ImmunologicalCapabilities.from_genome(genome)
        
        assert caps.has_immune_system is True
        assert caps.has_adaptive_immunity is True
        assert caps.has_innate_immunity is True
        assert caps.susceptible_to_viruses is True
        assert caps.susceptible_to_bacteria is True
        assert caps.susceptible_to_fungi is True
        assert caps.can_get_sick is True
        assert caps.can_die_from_disease is True
        assert caps.can_form_immunological_memory is True
    
    def test_bacteria_simple_immunity(self):
        """Una bacteria tiene inmunidad simple (innata, no adaptativa)."""
        genome = create_genome_with_traits({
            "immunity": 0.3,
            "nervous_system": 0.0,
            "metabolism": 0.8,
            "heterotrophy": 0.5,
            "antibiotic_resistance": 0.7,
        })
        
        caps = ImmunologicalCapabilities.from_genome(genome)
        
        assert caps.has_immune_system is True
        assert caps.has_adaptive_immunity is False  # Sin sistema nervioso
        assert caps.has_innate_immunity is True
        assert caps.susceptible_to_viruses is False  # Virus de bacterias son diferentes
        assert caps.susceptible_to_bacteria is True
        assert caps.can_get_sick is True
        assert caps.can_form_immunological_memory is False  # Sin memoria adaptativa
    
    def test_insect_innate_immunity(self):
        """Un insecto tiene inmunidad innata (no adaptativa compleja)."""
        genome = create_genome_with_traits({
            "immunity": 0.4,
            "nervous_system": 0.3,  # Justo en el límite
            "metabolism": 0.7,
            "heterotrophy": 0.8,
        })
        
        caps = ImmunologicalCapabilities.from_genome(genome)
        
        assert caps.has_immune_system is True
        assert caps.has_adaptive_immunity is False  # immunity < 0.5
        assert caps.has_innate_immunity is True
        assert caps.susceptible_to_viruses is True
        assert caps.susceptible_to_bacteria is True
        assert caps.can_get_sick is True
        assert caps.can_form_immunological_memory is False
    
    def test_vertebrate_adaptive_immunity(self):
        """Un vertebrado tiene inmunidad adaptativa."""
        genome = create_genome_with_traits({
            "immunity": 0.7,
            "nervous_system": 0.8,
            "metabolism": 0.8,
            "heterotrophy": 1.0,
        })
        
        caps = ImmunologicalCapabilities.from_genome(genome)
        
        assert caps.has_adaptive_immunity is True
        assert caps.can_form_immunological_memory is True
    
    def test_organism_without_nervous_system_no_memory(self):
        """Un organismo sin sistema nervioso no forma memoria inmunológica."""
        genome = create_genome_with_traits({
            "immunity": 0.6,
            "nervous_system": 0.2,  # Muy bajo
            "metabolism": 0.7,
        })
        
        caps = ImmunologicalCapabilities.from_genome(genome)
        
        assert caps.has_immune_system is True
        assert caps.has_adaptive_immunity is False  # nervous_system < 0.3
        assert caps.can_form_immunological_memory is False
    
    def test_missing_traits_use_defaults(self):
        """Si faltan rasgos, usa valores por defecto apropiados."""
        # Genoma vacío (sin rasgos)
        genome = Genome(genes={}, species_id="unknown")
        
        caps = ImmunologicalCapabilities.from_genome(genome)
        
        # Debería tener capacidades básicas por defecto
        assert caps.has_immune_system is True  # immunity default = 0.5
        assert caps.can_get_sick is True  # metabolism default = 0.5
        assert caps.susceptible_to_bacteria is True
    
    def test_is_susceptible_to_virus(self):
        """Verifica susceptibilidad a virus específicos."""
        genome = create_genome_with_traits({
            "immunity": 0.8,
            "nervous_system": 0.9,
            "metabolism": 0.9,
            "heterotrophy": 1.0,
        })
        
        caps = ImmunologicalCapabilities.from_genome(genome)
        
        assert caps.is_susceptible_to("Influenza") is True
        assert caps.is_susceptible_to("Coronavirus") is True
        assert caps.is_susceptible_to("Poxvirus") is True
    
    def test_is_susceptible_to_bacteria(self):
        """Verifica susceptibilidad a bacterias."""
        genome = create_genome_with_traits({
            "immunity": 0.5,
            "metabolism": 0.7,
        })
        
        caps = ImmunologicalCapabilities.from_genome(genome)
        
        assert caps.is_susceptible_to("Bacteria") is True
        assert caps.is_susceptible_to("E_Coli") is True
    
    def test_plant_not_susceptible_to_viruses(self):
        """Las plantas no son susceptibles a virus animales."""
        genome = create_genome_with_traits({
            "immunity": 0.0,
            "photosynthesis": 1.0,
            "nervous_system": 0.0,
            "metabolism": 0.2,
            "heterotrophy": 0.0,
        })
        
        caps = ImmunologicalCapabilities.from_genome(genome)
        
        assert caps.is_susceptible_to("Influenza") is False
        assert caps.is_susceptible_to("Coronavirus") is False
        assert caps.is_susceptible_to("Poxvirus") is False
    
    def test_str_representation(self):
        """La representación string es legible."""
        genome = create_genome_with_traits({
            "immunity": 0.8,
            "nervous_system": 0.9,
            "metabolism": 0.9,
        })
        
        caps = ImmunologicalCapabilities.from_genome(genome)
        str_repr = str(caps)
        
        assert "ImmunologicalCapabilities" in str_repr
        assert "immune=True" in str_repr
        assert "adaptive=True" in str_repr


class TestImmunologicalCapabilitiesIntegration:
    """Tests de integración con diferentes tipos de organismos."""
    
    def test_fungus_capabilities(self):
        """Un hongo tiene capacidades inmunológicas limitadas."""
        genome = create_genome_with_traits({
            "immunity": 0.3,
            "nervous_system": 0.1,
            "metabolism": 0.6,
            "heterotrophy": 0.8,  # Los hongos son heterótrofos
        })
        
        caps = ImmunologicalCapabilities.from_genome(genome)
        
        assert caps.has_immune_system is True
        assert caps.has_adaptive_immunity is False
        assert caps.can_get_sick is True
        assert caps.can_form_immunological_memory is False
    
    def test_extremophile_resistance(self):
        """Un extremófilo tiene alta resistencia pero sin inmunidad compleja."""
        genome = create_genome_with_traits({
            "immunity": 0.9,
            "nervous_system": 0.0,
            "metabolism": 0.5,
            "longevity": 3.0,  # Muy longevo
        })
        
        caps = ImmunologicalCapabilities.from_genome(genome)
        
        assert caps.has_immune_system is True
        assert caps.has_adaptive_immunity is False  # Sin sistema nervioso
        assert caps.can_die_from_disease is False  # longevity > 2.0