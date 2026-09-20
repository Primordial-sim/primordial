"""Perfil biológico de una especie.

Describe CÓMO suele vivir una especie (no QUÉ puede hacer).
Las capacidades concretas salen del Genome.

Filosofía: "El perfil es una descripción, no una restricción."
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.taxonomy.profile_enums import (
    DietType,
    ReproductionType,
    DevelopmentType,
    HabitatType,
    LocomotionType,
    SocialStructureType,
    ThermoregulationType,
    BodySizeCategory,
    ActivityPattern,
)


@dataclass(frozen=True)
class SpeciesProfile:
    """Perfil biológico de una especie.
    
    Attributes:
        taxonomy_id: ID del taxón en el árbol taxonómico.
        body_size_category: Categoría de tamaño corporal.
        thermoregulation: Tipo de termorregulación.
        diet: Tipo de dieta.
        reproduction: Tipo de reproducción.
        development: Tipo de desarrollo.
        habitat: Hábitat principal.
        locomotion: Locomoción principal.
        social_structure: Estructura social.
        activity_pattern: Patrón de actividad.
        notes: Notas opcionales.
    """
    
    # Taxonomía (referencia al árbol)
    taxonomy_id: str
    
    # Plan corporal
    body_size_category: BodySizeCategory
    thermoregulation: ThermoregulationType
    
    # Dieta
    diet: DietType
    
    # Reproducción
    reproduction: ReproductionType
    development: DevelopmentType
    
    # Hábitat y locomoción
    habitat: HabitatType
    locomotion: LocomotionType
    
    # Estructura social
    social_structure: SocialStructureType
    
    # Patrón de actividad
    activity_pattern: ActivityPattern
    
    # Notas opcionales
    notes: str = ""
    
    def is_carnivore(self) -> bool:
        """Verifica si es carnívoro."""
        return self.diet == DietType.CARNIVORE
    
    def is_herbivore(self) -> bool:
        """Verifica si es herbívoro."""
        return self.diet == DietType.HERBIVORE
    
    def is_predator(self) -> bool:
        """Verifica si es un depredador potencial."""
        return self.diet in (DietType.CARNIVORE, DietType.INSECTIVORE)
    
    def can_fly(self) -> bool:
        """Verifica si su locomoción principal es volar.
        
        Nota: Esto es una descripción del perfil, no una capacidad.
        La capacidad real de volar depende del Genome (trait flight).
        """
        return self.locomotion == LocomotionType.FLYING
    
    def is_terrestrial(self) -> bool:
        """Verifica si es terrestre."""
        return self.habitat == HabitatType.TERRESTRIAL
    
    def is_aquatic(self) -> bool:
        """Verifica si es acuático."""
        return self.habitat == HabitatType.AQUATIC
    
    def is_social(self) -> bool:
        """Verifica si tiene estructura social."""
        return self.social_structure != SocialStructureType.SOLITARY
    
    def __repr__(self) -> str:
        return (
            f"SpeciesProfile({self.taxonomy_id}: "
            f"{self.diet.value}, {self.habitat.value}, "
            f"{self.social_structure.value})"
        )