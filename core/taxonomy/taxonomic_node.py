"""Nodos del árbol taxonómico.

Define la estructura de un nodo taxonómico y los rangos disponibles.
La taxonomía es INFORMATIVA: clasifica especies pero no decide capacidades.
Las capacidades siguen saliendo de la genética (Genome).

Filosofía: "La taxonomía dice QUÉ ES una especie, no QUÉ PUEDE HACER."
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class TaxonomicRank(Enum):
    """Rangos taxonómicos estándar (9 niveles)."""
    
    DOMAIN = auto()       # Vida
    KINGDOM = auto()      # Animalia, Plantae, Fungi, Bacteria
    PHYLUM = auto()       # Vertebrata, Arthropoda
    CLASS = auto()        # Mammalia, Aves, Reptilia
    ORDER = auto()        # Carnivora, Primates, Rodentia
    FAMILY = auto()       # Canidae, Felidae, Ursidae
    GENUS = auto()        # Canis, Felis, Ursus
    SPECIES = auto()      # Canis lupus, Felis catus
    SUBSPECIES = auto()   # Canis lupus familiaris
    
    def __str__(self) -> str:
        return self.name.lower()
    
    @property
    def level(self) -> int:
        """Nivel numérico del rango (0=DOMAIN, 8=SUBSPECIES)."""
        return list(TaxonomicRank).index(self)


@dataclass(frozen=True)
class TaxonomicNode:
    """Un nodo en el árbol taxonómico.
    
    Attributes:
        taxon_id: Identificador único del taxón (ej: "mammalia").
        name: Nombre legible (ej: "Mamíferos").
        parent_id: ID del taxón padre (None para DOMAIN).
        rank: Rango taxonómico.
        description: Descripción opcional.
        scientific_name: Nombre científico (ej: "Canis lupus").
    """
    
    taxon_id: str
    name: str
    parent_id: Optional[str]
    rank: TaxonomicRank
    description: str = ""
    scientific_name: str = ""
    
    def __post_init__(self) -> None:
        """Valida el nodo tras la creación."""
        if not self.taxon_id:
            raise ValueError("taxon_id no puede estar vacío")
        if not self.name:
            raise ValueError("name no puede estar vacío")
        if self.rank != TaxonomicRank.DOMAIN and not self.parent_id:
            raise ValueError(f"El taxón '{self.taxon_id}' necesita un parent_id")
    
    @property
    def is_root(self) -> bool:
        """Verifica si es el nodo raíz (DOMAIN)."""
        return self.parent_id is None
    
    def __repr__(self) -> str:
        return f"TaxonomicNode({self.taxon_id}: {self.name} [{self.rank.name}])"