"""Sistema de Relaciones Ecológicas.

Sistema que gestiona las relaciones ecológicas entre especies.
Las relaciones emergen de la combinación de perfil biológico,
rasgos genéticos y condiciones ambientales.

Filosofía:
- Las relaciones son OBJETOS, no reglas fijas
- El tipo describe QUÉ relación es
- El mecanismo describe CÓMO se ejecuta
- La intensidad cuantifica la fuerza de la relación
"""

from systems.ecology.relationship_types import (
    RelationshipType,
    MechanismType,
    InteractionOutcome,
    RelationshipIntensity,
)
from systems.ecology.relationship_effect import RelationshipEffect
from systems.ecology.ecological_relationship import EcologicalRelationship
from systems.ecology.relationship_inference import RelationshipInference
from systems.ecology.biome_condition_checker import BiomeConditionChecker
from systems.ecology.ecological_relationship_system import EcologicalRelationshipSystem

__all__ = [
    "RelationshipType",
    "MechanismType",
    "InteractionOutcome",
    "RelationshipIntensity",
    "RelationshipEffect",
    "EcologicalRelationship",
    "RelationshipInference",
    "BiomeConditionChecker",
    "EcologicalRelationshipSystem",
]