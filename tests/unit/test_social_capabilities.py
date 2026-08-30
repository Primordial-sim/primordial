"""Tests para SocialCapabilities."""

import pytest
from entities.person.genome import Genome
from entities.person.allele import Gene, Allele
from systems.relationships.social_capabilities import SocialCapabilities


def create_genome_with_traits(traits: dict) -> Genome:
    """Helper para crear un genoma con rasgos específicos."""
    genes = {}
    for trait_id, value in traits.items():
        allele_a = Allele(value=value, dominance=1.0)
        allele_b = Allele(value=value, dominance=0.0)
        genes[trait_id] = Gene(allele_a, allele_b)
    return Genome(genes=genes, species_id="test_species")


class TestSocialCapabilitiesFromGenome:
    """Tests para SocialCapabilities.from_genome()."""
    
    def test_plant_has_no_social_capabilities(self):
        """Las plantas no tienen capacidades sociales."""
        genome = create_genome_with_traits({
            "nervous_system": 0.0,
            "intelligence": 0.0,
            "sociability": 0.0,
        })
        
        caps = SocialCapabilities.from_genome(genome)
        
        assert caps.has_social_awareness is False
        assert caps.can_recognize_individuals is False
        assert caps.can_form_relationships is False
        assert caps.can_form_cooperation is False
        assert caps.can_form_pair_bond is False
        assert caps.can_have_marriage is False
        assert caps.social_complexity == 0.0
    
    def test_bacteria_no_social(self):
        """Las bacterias no tienen capacidades sociales."""
        genome = create_genome_with_traits({
            "nervous_system": 0.05,
            "sociability": 0.1,
        })
        
        caps = SocialCapabilities.from_genome(genome)
        
        assert caps.has_social_awareness is False
        assert caps.can_form_relationships is False
    
    def test_fish_basic_social(self):
        """Los peces tienen interacciones básicas de proximidad."""
        genome = create_genome_with_traits({
            "nervous_system": 0.4,
            "intelligence": 0.25,
            "sociability": 0.5,
        })
        
        caps = SocialCapabilities.from_genome(genome)
        
        assert caps.has_social_awareness is True
        assert caps.can_recognize_individuals is False  # intelligence < 0.3
        assert caps.can_form_cooperation is False  # intelligence < 0.2 pero requiere recognition
        assert caps.can_form_pair_bond is False
        assert caps.can_have_marriage is False
    
    def test_wolf_pack_bonds(self):
        """Los lobos forman manadas con vínculos complejos."""
        genome = create_genome_with_traits({
            "nervous_system": 0.8,
            "intelligence": 0.6,
            "sociability": 0.85,
            "aggressiveness": 0.7,
        })
        
        caps = SocialCapabilities.from_genome(genome)
        
        assert caps.has_social_awareness is True
        assert caps.can_recognize_individuals is True
        assert caps.can_form_relationships is True
        assert caps.can_form_cooperation is True
        assert caps.can_form_conflict is True
        assert caps.can_form_pair_bond is True
        assert caps.can_form_family_bonds is True
        assert caps.can_form_group_identity is True
        assert caps.can_have_friendship is False  # intelligence < 0.7
        assert caps.can_have_romantic_bonds is False  # intelligence < 0.7
        assert caps.can_have_marriage is False
    
    def test_dolphin_complex_social(self):
        """Los delfines tienen vínculos sociales complejos."""
        genome = create_genome_with_traits({
            "nervous_system": 0.9,
            "intelligence": 0.8,
            "sociability": 0.9,
        })
        
        caps = SocialCapabilities.from_genome(genome)
        
        assert caps.can_form_relationships is True
        assert caps.can_form_cooperation is True
        assert caps.can_form_pair_bond is True
        assert caps.can_form_family_bonds is True
        assert caps.can_have_friendship is True
        assert caps.can_have_romantic_bonds is True
        assert caps.can_have_marriage is True
        assert caps.can_have_social_reputation is True
    
    def test_human_full_social(self):
        """Los humanos tienen capacidades sociales completas."""
        genome = create_genome_with_traits({
            "nervous_system": 0.95,
            "intelligence": 0.95,
            "sociability": 0.9,
            "temperament": 0.6,
        })
        
        caps = SocialCapabilities.from_genome(genome)
        
        assert caps.has_social_awareness is True
        assert caps.can_recognize_individuals is True
        assert caps.can_form_relationships is True
        assert caps.can_form_cooperation is True
        assert caps.can_form_conflict is True
        assert caps.can_form_pair_bond is True
        assert caps.can_form_family_bonds is True
        assert caps.can_form_group_identity is True
        assert caps.can_have_friendship is True
        assert caps.can_have_romantic_bonds is True
        assert caps.can_have_marriage is True
        assert caps.can_have_divorce is True
        assert caps.can_have_social_reputation is True
        assert caps.can_have_social_pressure is True
        assert caps.social_complexity > 0.8
    
    def test_reptile_minimal_social(self):
        """Los reptiles tienen capacidades sociales mínimas."""
        genome = create_genome_with_traits({
            "nervous_system": 0.5,
            "intelligence": 0.25,
            "sociability": 0.3,
            "aggressiveness": 0.6,
        })
        
        caps = SocialCapabilities.from_genome(genome)
        
        assert caps.has_social_awareness is True
        assert caps.can_recognize_individuals is False
        assert caps.can_form_relationships is False
        assert caps.can_form_cooperation is False
        assert caps.can_form_conflict is False  # sin recognition
        assert caps.can_form_pair_bond is False
    
    def test_ant_colony_social(self):
        """Las hormigas son muy sociales pero sin cognición individual."""
        genome = create_genome_with_traits({
            "nervous_system": 0.4,
            "intelligence": 0.2,
            "sociability": 0.95,
        })
        
        caps = SocialCapabilities.from_genome(genome)
        
        # Alta sociabilidad pero baja inteligencia
        assert caps.has_social_awareness is True
        assert caps.can_recognize_individuals is False  # intelligence < 0.3
        assert caps.can_form_relationships is False  # sin recognition
        assert caps.can_form_cooperation is False  # sin recognition


class TestSocialCapabilitiesMethods:
    """Tests para métodos auxiliares."""
    
    def test_can_have_label_basic(self):
        """Etiquetas básicas requieren capacidades específicas."""
        wolf = SocialCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.8,
            "intelligence": 0.6,
            "sociability": 0.85,
        }))
        
        assert wolf.can_have_label("Conocido") is True
        assert wolf.can_have_label("Aliado") is True
        assert wolf.can_have_label("Rival") is True
        assert wolf.can_have_label("Amigo") is False  # sin friendship
        assert wolf.can_have_label("Amante") is False  # sin romantic
        assert wolf.can_have_label("Familia Elegida") is True
    
    def test_can_have_label_human(self):
        """Humanos pueden tener todas las etiquetas."""
        human = SocialCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.95,
            "intelligence": 0.95,
            "sociability": 0.9,
        }))
        
        assert human.can_have_label("Conocido") is True
        assert human.can_have_label("Aliado") is True
        assert human.can_have_label("Amigo") is True
        assert human.can_have_label("Familia Elegida") is True
        assert human.can_have_label("Interés Romántico") is True
        assert human.can_have_label("Amante") is True
        assert human.can_have_label("Rival") is True
        assert human.can_have_label("Enemigo") is True
    
    def test_can_have_label_plant(self):
        """Plantas no pueden tener etiquetas sociales."""
        plant = SocialCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.0,
            "sociability": 0.0,
        }))
        
        assert plant.can_have_label("Desconocido") is True  # todos pueden
        assert plant.can_have_label("Conocido") is False
        assert plant.can_have_label("Amigo") is False
        assert plant.can_have_label("Amante") is False
    
    def test_can_participate_in_event(self):
        """Eventos requieren capacidades específicas."""
        wolf = SocialCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.8,
            "intelligence": 0.6,
            "sociability": 0.85,
        }))
        
        assert wolf.can_participate_in_event("met") is True
        assert wolf.can_participate_in_event("cooperation") is True
        assert wolf.can_participate_in_event("conflict") is True
        assert wolf.can_participate_in_event("birth") is True
        assert wolf.can_participate_in_event("intimacy") is False  # sin romantic
        assert wolf.can_participate_in_event("cohabitation_start") is False  # sin marriage
    
    def test_can_participate_in_event_human(self):
        """Humanos pueden participar en todos los eventos."""
        human = SocialCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.95,
            "intelligence": 0.95,
            "sociability": 0.9,
        }))
        
        assert human.can_participate_in_event("met") is True
        assert human.can_participate_in_event("cooperation") is True
        assert human.can_participate_in_event("intimacy") is True
        assert human.can_participate_in_event("betrayal") is True
        assert human.can_participate_in_event("cohabitation_start") is True
        assert human.can_participate_in_event("cohabitation_end") is True
    
    def test_can_form_nucleus_type(self):
        """Tipos de núcleo requieren capacidades específicas."""
        wolf = SocialCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.8,
            "intelligence": 0.6,
            "sociability": 0.85,
        }))
        
        assert wolf.can_form_nucleus_type("single") is True
        assert wolf.can_form_nucleus_type("couple") is True
        assert wolf.can_form_nucleus_type("family") is True
        assert wolf.can_form_nucleus_type("single_parent") is True
    
    def test_can_form_nucleus_type_plant(self):
        """Plantas solo pueden estar solas."""
        plant = SocialCapabilities.from_genome(create_genome_with_traits({
            "nervous_system": 0.0,
        }))
        
        assert plant.can_form_nucleus_type("single") is True
        assert plant.can_form_nucleus_type("couple") is False
        assert plant.can_form_nucleus_type("family") is False


class TestSocialCapabilitiesIntegration:
    """Tests de integración con diferentes especies."""
    
    def test_eagle_territorial_social(self):
        """Las águilas son territoriales pero no muy sociales."""
        genome = create_genome_with_traits({
            "nervous_system": 0.8,
            "intelligence": 0.6,
            "sociability": 0.3,
            "territoriality": 0.9,
            "aggressiveness": 0.8,
        })
        
        caps = SocialCapabilities.from_genome(genome)
        
        assert caps.has_social_awareness is True
        assert caps.can_recognize_individuals is True
        assert caps.can_form_relationships is True
        assert caps.can_form_cooperation is False  # sociability < 0.4
        assert caps.can_form_conflict is True
        assert caps.can_form_pair_bond is False  # sociability < 0.7
        assert caps.can_form_group_identity is False
    
    def test_bird_pair_bonding(self):
        """Muchas aves forman parejas estables."""
        genome = create_genome_with_traits({
            "nervous_system": 0.7,
            "intelligence": 0.55,
            "sociability": 0.75,
        })
        
        caps = SocialCapabilities.from_genome(genome)
        
        assert caps.can_form_pair_bond is True
        assert caps.can_form_family_bonds is False  # intelligence < 0.6
        assert caps.can_have_romantic_bonds is False  # intelligence < 0.7
    
    def test_str_representation(self):
        """La representación string es legible."""
        genome = create_genome_with_traits({
            "nervous_system": 0.9,
            "intelligence": 0.9,
            "sociability": 0.8,
        })
        
        caps = SocialCapabilities.from_genome(genome)
        str_repr = str(caps)
        
        assert "SocialCapabilities" in str_repr
        assert "level=" in str_repr
        assert "marriage=True" in str_repr