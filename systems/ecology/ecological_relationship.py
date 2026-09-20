"""Relación ecológica entre dos especies.

Objeto central del EcologicalRelationshipSystem.
Representa una relación específica entre dos especies, con tipo,
mecanismo, intensidad, condiciones y efectos.

Filosofía:
- Una relación es un OBJETO, no una regla fija
- Las relaciones emergen de la combinación de perfil + genoma + entorno
- La misma relación puede tener diferentes intensidades según el contexto
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from systems.ecology.relationship_types import (
    RelationshipType,
    MechanismType,
    RelationshipIntensity,
)
from systems.ecology.relationship_effect import RelationshipEffect


@dataclass(frozen=True)
class EcologicalRelationship:
    """Una relación ecológica entre dos especies.
    
    Attributes:
        species_a_id: ID de la especie que inicia la relación.
        species_b_id: ID de la especie objetivo.
        relationship_type: Tipo de relación (Predation, Mutualism, etc.).
        mechanism: Mecanismo de interacción (Hunt, Pollination, etc.).
        intensity: Intensidad de la relación [0.0, 1.0].
        biome_requirements: Biomas donde la relación es válida.
        seasonal_constraints: Estaciones donde ocurre.
        effect_on_a: Efecto sobre la especie A.
        effect_on_b: Efecto sobre la especie B.
        notes: Notas opcionales.
    """
    
    # Identidad
    species_a_id: str
    species_b_id: str
    
    # Clasificación
    relationship_type: RelationshipType
    mechanism: MechanismType
    
    # Cuantificación
    intensity: float = 0.5  # [0.0, 1.0]
    
    # Contexto ambiental
    biome_requirements: List[str] = field(default_factory=list)
    seasonal_constraints: List[str] = field(default_factory=list)
    
    # Efectos
    effect_on_a: Optional[RelationshipEffect] = None
    effect_on_b: Optional[RelationshipEffect] = None
    
    # Notas
    notes: str = ""
    
    def __post_init__(self) -> None:
        """Valida la relación tras la creación."""
        if not self.species_a_id:
            raise ValueError("species_a_id no puede estar vacío")
        if not self.species_b_id:
            raise ValueError("species_b_id no puede estar vacío")
        if self.intensity < 0.0 or self.intensity > 1.0:
            raise ValueError(f"intensity debe estar entre 0.0 y 1.0, got {self.intensity}")
    
    @property
    def intensity_level(self) -> RelationshipIntensity:
        """Retorna el nivel de intensidad."""
        return RelationshipIntensity.from_value(self.intensity)
    
    def is_valid_in_biome(self, biome_name: str) -> bool:
        """Verifica si la relación es válida en un bioma específico."""
        if not self.biome_requirements:
            return True  # Sin requisitos = válida en todos
        return biome_name in self.biome_requirements
    
    def is_valid_in_season(self, season_name: str) -> bool:
        """Verifica si la relación es válida en una estación específica."""
        if not self.seasonal_constraints:
            return True  # Sin restricciones = válida todo el año
        return season_name in self.seasonal_constraints
    
    def get_effect_on(self, species_id: str) -> Optional[RelationshipEffect]:
        """Obtiene el efecto sobre una especie específica."""
        if species_id == self.species_a_id:
            return self.effect_on_a
        elif species_id == self.species_b_id:
            return self.effect_on_b
        return None
    
    def is_mutualistic(self) -> bool:
        """Verifica si la relación es mutualista."""
        return self.relationship_type == RelationshipType.MUTUALISM
    
    def is_antagonistic(self) -> bool:
        """Verifica si la relación es antagónica."""
        return self.relationship_type in (
            RelationshipType.PREDATION,
            RelationshipType.HERBIVORY,
            RelationshipType.PARASITISM,
            RelationshipType.AMENSALISM,
        )
    
    def __repr__(self) -> str:
        return (
            f"EcologicalRelationship("
            f"{self.species_a_id} → {self.species_b_id}, "
            f"{self.relationship_type.value}, "
            f"intensity={self.intensity:.2f})"
        )