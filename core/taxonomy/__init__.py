"""Sistema Taxonómico.

Proporciona clasificación jerárquica de especies y perfiles biológicos.
La taxonomía es INFORMATIVA: no decide capacidades.
Las capacidades salen de la genética (Genome).
"""

from core.taxonomy.taxonomic_node import TaxonomicNode, TaxonomicRank
from core.taxonomy.taxonomic_system import TaxonomicSystem
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
from core.taxonomy.species_profile import SpeciesProfile
from core.taxonomy.profile_inference import ProfileInference
from core.taxonomy.species_classification import SpeciesClassificationSystem

__all__ = [
    "TaxonomicNode",
    "TaxonomicRank",
    "TaxonomicSystem",
    "DietType",
    "ReproductionType",
    "DevelopmentType",
    "HabitatType",
    "LocomotionType",
    "SocialStructureType",
    "ThermoregulationType",
    "BodySizeCategory",
    "ActivityPattern",
    "SpeciesProfile",
    "ProfileInference",
    "SpeciesClassificationSystem",
]