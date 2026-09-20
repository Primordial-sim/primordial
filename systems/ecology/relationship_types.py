"""Tipos de relaciones ecológicas y mecanismos de interacción.

Filosofía:
- El tipo describe QUÉ relación es (Predation, Mutualism, etc.)
- El mecanismo describe CÓMO se ejecuta (Hunt, Pollination, etc.)
- La intensidad cuantifica la fuerza de la relación
"""

from __future__ import annotations

from enum import Enum, auto


class RelationshipType(Enum):
    """Tipos de relaciones ecológicas entre especies."""
    
    PREDATION = "predation"           # A se come a B
    HERBIVORY = "herbivory"           # A consume B (planta/alga)
    COMPETITION = "competition"       # A y B compiten por recursos
    MUTUALISM = "mutualism"           # A y B se benefician mutuamente
    PARASITISM = "parasitism"         # A vive a expensas de B
    COMMENSALISM = "commensalism"     # A se beneficia, B no se afecta
    AMENSALISM = "amensalism"         # A perjudica a B sin afectarse
    NEUTRALISM = "neutralism"         # Sin interacción significativa


class MechanismType(Enum):
    """Mecanismos de ejecución de relaciones ecológicas."""
    
    HUNT = "hunt"                             # Caza activa (persecución, emboscada)
    GRAZING = "grazing"                       # Pastoreo (consumo de plantas)
    FILTER_FEEDING = "filter_feeding"         # Filtrado (ballenas, mejillones)
    POLLINATION = "pollination"               # Polinización (abejas + flores)
    SEED_DISPERSAL = "seed_dispersal"         # Dispersión de semillas
    INFECTION = "infection"                   # Infección parasitaria
    RESOURCE_CONSUMPTION = "resource_consumption"  # Competencia por recursos
    TERRITORIAL_DISPLAY = "territorial_display"    # Exhibición territorial
    CHEMICAL_SUPPRESSION = "chemical_suppression"  # Supresión química (alelopatía)
    SCAVENGING = "scavenging"                 # Carroñeo
    AMBUSH = "ambush"                         # Emboscada (depredadores sigilosos)
    PACK_HUNTING = "pack_hunting"             # Caza en manada


class InteractionOutcome(Enum):
    """Resultado de una interacción ecológica."""
    
    SUCCESS = "success"               # La interacción fue exitosa
    FAILURE = "failure"               # La interacción falló
    PARTIAL = "partial"               # Éxito parcial
    AVOIDED = "avoided"               # Evitada (presa escapó)
    NOT_ATTEMPTED = "not_attempted"   # No se intentó


class RelationshipIntensity(Enum):
    """Niveles de intensidad de una relación."""
    
    WEAK = "weak"                     # 0.0 - 0.3
    MODERATE = "moderate"             # 0.3 - 0.6
    STRONG = "strong"                 # 0.6 - 0.8
    EXTREME = "extreme"               # 0.8 - 1.0
    
    @classmethod
    def from_value(cls, value: float) -> 'RelationshipIntensity':
        """Convierte un valor numérico a nivel de intensidad."""
        if value < 0.3:
            return cls.WEAK
        elif value < 0.6:
            return cls.MODERATE
        elif value < 0.8:
            return cls.STRONG
        else:
            return cls.EXTREME