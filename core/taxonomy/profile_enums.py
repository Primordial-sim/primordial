"""Enums para el perfil biológico de especies.

El perfil biológico describe CÓMO suele vivir una especie.
No determina capacidades (eso es del Genome).
Solo describe patrones típicos.
"""

from __future__ import annotations

from enum import Enum, auto


class DietType(Enum):
    """Tipo de dieta."""
    CARNIVORE = "carnivore"              # Carnívoro
    HERBIVORE = "herbivore"              # Herbívoro
    OMNIVORE = "omnivore"                # Omnívoro
    INSECTIVORE = "insectivore"          # Insectívoro
    DETRITIVORE = "detritivore"          # Detritívoro (descomponedor)
    FILTER_FEEDER = "filter_feeder"      # Filtrador
    PARASITE = "parasite"                # Parásito
    PHOTOSYNTHETIC = "photosynthetic"    # Fotosintético
    CHEMOSYNTHETIC = "chemosynthetic"    # Quimiosintético


class ReproductionType(Enum):
    """Tipo de reproducción."""
    SEXUAL = "sexual"
    ASEXUAL = "asexual"
    BOTH = "both"                        # Algunas plantas, bacterias


class DevelopmentType(Enum):
    """Tipo de desarrollo."""
    OVIPAROUS = "oviparous"              # Ponen huevos
    VIVIPAROUS = "viviparous"            # Crías vivas
    OVOVIVIPAROUS = "ovoviviparous"      # Huevos dentro del cuerpo
    METAMORPHOSIS = "metamorphosis"      # Insectos, anfibios
    BINARY_FISSION = "binary_fission"    # Bacterias
    SPORES = "spores"                    # Hongos, plantas
    BUDDING = "budding"                  # Gemación (levaduras, corales)


class HabitatType(Enum):
    """Tipo de hábitat principal."""
    TERRESTRIAL = "terrestrial"
    AQUATIC = "aquatic"
    AERIAL = "aerial"
    AMPHIBIOUS = "amphibious"
    SUBTERRANEAN = "subterranean"
    ARBOREAL = "arboreal"                # Vive en árboles


class LocomotionType(Enum):
    """Tipo de locomoción principal."""
    WALKING = "walking"
    RUNNING = "running"
    SWIMMING = "swimming"
    FLYING = "flying"
    CRAWLING = "crawling"
    BURROWING = "burrowing"
    CLIMBING = "climbing"
    SESSILE = "sessile"                  # No se mueve (plantas, corales)
    DRIFTING = "drifting"                # A la deriva (plancton)


class SocialStructureType(Enum):
    """Estructura social."""
    SOLITARY = "solitary"
    PAIR = "pair"                        # Pareja monógama
    HERD = "herd"                        # Manada herbívora
    PACK = "pack"                        # Manada cazadora
    COLONY = "colony"                    # Colonia (insectos, bacterias)
    FLOCK = "flock"                      # Bandada (aves)
    SCHOOL = "school"                    # Banco (peces)
    SWARM = "swarm"                      # Enjambre


class ThermoregulationType(Enum):
    """Tipo de termorregulación."""
    HOMEOTHERM = "homeotherm"            # Sangre caliente
    POIKILOTHERM = "poikilotherm"        # Sangre fría
    HETEROTHERM = "heterotherm"          # Mixto (murciélagos, colibríes)


class BodySizeCategory(Enum):
    """Categoría de tamaño corporal."""
    MICROSCOPIC = "microscopic"          # Bacterias, protistas
    SMALL = "small"                      # Insectos, ratones
    MEDIUM = "medium"                    # Perros, ciervos, humanos
    LARGE = "large"                      # Elefantes, ballenas
    GIANT = "giant"                      # Ballena azul, sequoia


class ActivityPattern(Enum):
    """Patrón de actividad."""
    DIURNAL = "diurnal"                  # Activo de día
    NOCTURNAL = "nocturnal"              # Activo de noche
    CREPUSCULAR = "crepuscular"          # Activo al amanecer/atardecer
    CONTINUOUS = "continuous"            # Activo continuamente