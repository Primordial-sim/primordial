"""Sistema de Genética Universal.

Proporciona una arquitectura genética completamente desacoplada de especies:
- Biblioteca Universal de Rasgos: catálogo global de rasgos hereditarios.
- Definición de Especie: cada especie elige qué rasgos utiliza.
- Genome genérico: almacena solo los rasgos activos de la especie.
- Validación Biológica: advierte sobre combinaciones incoherentes.
- Índice de Realismo: informa el nivel de realismo de una especie.
"""

from core.genetics.trait import Trait, TraitCategory
from core.genetics.trait_library import TraitLibrary
from core.genetics.species_definition import SpeciesDefinition
from core.genetics.biological_validator import BiologicalValidator, ValidationResult
from core.genetics.realism_index import RealismIndex

__all__ = [
    "Trait",
    "TraitCategory",
    "TraitLibrary",
    "SpeciesDefinition",
    "BiologicalValidator",
    "ValidationResult",
    "RealismIndex",
]