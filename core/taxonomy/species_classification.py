"""Sistema de Clasificación de Especies.

Unifica la taxonomía y los perfiles biológicos con las especies existentes.
Proporciona consultas unificadas para el sistema ecológico.

Filosofía:
- La taxonomía es INFORMATIVA, no prescriptiva
- Los perfiles describen patrones típicos, no capacidades
- Las capacidades salen del Genome
"""

from __future__ import annotations

from typing import Dict, List, Optional, TYPE_CHECKING
import logging

from core.taxonomy.taxonomic_system import TaxonomicSystem
from core.taxonomy.taxonomic_node import TaxonomicNode, TaxonomicRank
from core.taxonomy.species_profile import SpeciesProfile
from core.taxonomy.profile_inference import ProfileInference
from core.taxonomy.profile_enums import (
    DietType,
    HabitatType,
    LocomotionType,
    SocialStructureType,
    ThermoregulationType,
    BodySizeCategory,
)

if TYPE_CHECKING:
    from core.genetics.species_definition import SpeciesDefinition


class SpeciesClassificationSystem:
    """Sistema que gestiona taxonomía y perfiles de especies.
    
    Uso:
        classification = SpeciesClassificationSystem.get_default()
        
        # Consultas
        profile = classification.get_profile("human")
        taxonomy = classification.get_taxonomy("human")
        is_mammal = classification.is_mammal("human")
        
        # Consultas por categoría
        carnivores = classification.get_species_by_diet(DietType.CARNIVORE)
        aquatic = classification.get_species_by_habitat(HabitatType.AQUATIC)
    """
    
    _default_instance: Optional['SpeciesClassificationSystem'] = None
    _logger = logging.getLogger("SpeciesClassificationSystem")
    
    def __init__(self) -> None:
        self.taxonomy = TaxonomicSystem.get_default()
        self.profile_inference = ProfileInference()
        
        # Mapeo de especies a taxones y perfiles
        self._species_taxonomy: Dict[str, str] = {}  # species_id → taxon_id
        self._species_profiles: Dict[str, SpeciesProfile] = {}  # species_id → profile
    
    # =========================================================================
    # CONSTRUCTOR DE INSTANCIA POR DEFECTO
    # =========================================================================
    
    @classmethod
    def get_default(cls) -> 'SpeciesClassificationSystem':
        """Retorna la instancia por defecto."""
        if cls._default_instance is None:
            cls._default_instance = cls()
        return cls._default_instance
    
    # =========================================================================
    # REGISTRO DE ESPECIES
    # =========================================================================
    
    def register_species(
        self,
        species: SpeciesDefinition,
        taxon_id: Optional[str] = None,
        profile: Optional[SpeciesProfile] = None,
    ) -> None:
        """Registra una especie con su taxonomía y perfil.
        
        Args:
            species: La definición de especie.
            taxon_id: ID del taxón en el árbol taxonómico.
                     Si es None, se usa species_id como taxon_id.
            profile: Perfil biológico. Si es None, se infiere desde rasgos.
        """
        species_id = species.species_id
        
        # Asignar taxonomía
        if taxon_id is None:
            taxon_id = species_id
        self._species_taxonomy[species_id] = taxon_id
        
        # Asignar perfil (inferido o manual)
        if profile is None:
            profile = self.profile_inference.infer(species)
        self._species_profiles[species_id] = profile
        
        self._logger.debug(
            f"Especie clasificada: {species_id} → {taxon_id} "
            f"[{profile.diet.value}, {profile.habitat.value}]"
        )
    
    def register_taxonomy_for_species(
        self,
        species_id: str,
        taxon_id: str,
    ) -> None:
        """Asigna un taxón existente a una especie."""
        if not self.taxonomy.has(taxon_id):
            raise ValueError(f"El taxón '{taxon_id}' no existe")
        self._species_taxonomy[species_id] = taxon_id
    
    def register_profile_for_species(
        self,
        species_id: str,
        profile: SpeciesProfile,
    ) -> None:
        """Asigna un perfil manual a una especie."""
        self._species_profiles[species_id] = profile
    
    # =========================================================================
    # CONSULTAS DE TAXONOMÍA
    # =========================================================================
    
    def get_taxonomy_id(self, species_id: str) -> Optional[str]:
        """Obtiene el ID del taxón de una especie."""
        return self._species_taxonomy.get(species_id)
    
    def get_taxonomy_node(self, species_id: str) -> Optional[TaxonomicNode]:
        """Obtiene el nodo taxonómico de una especie."""
        taxon_id = self._species_taxonomy.get(species_id)
        if taxon_id is None:
            return None
        return self.taxonomy.get(taxon_id)
    
    def get_taxonomy_chain(self, species_id: str) -> List[TaxonomicNode]:
        """Obtiene la cadena taxonómica completa de una especie."""
        taxon_id = self._species_taxonomy.get(species_id)
        if taxon_id is None:
            return []
        return self.taxonomy.get_ancestors(taxon_id)
    
    def is_descendant_of(self, species_id: str, ancestor_id: str) -> bool:
        """Verifica si una especie desciende de un taxón."""
        taxon_id = self._species_taxonomy.get(species_id)
        if taxon_id is None:
            return False
        return self.taxonomy.is_descendant_of(taxon_id, ancestor_id)
    
    def is_mammal(self, species_id: str) -> bool:
        """Verifica si una especie es un mamífero."""
        return self.is_descendant_of(species_id, "mammalia")
    
    def is_bird(self, species_id: str) -> bool:
        """Verifica si una especie es un ave."""
        return self.is_descendant_of(species_id, "aves")
    
    def is_reptile(self, species_id: str) -> bool:
        """Verifica si una especie es un reptil."""
        return self.is_descendant_of(species_id, "reptilia")
    
    def is_fish(self, species_id: str) -> bool:
        """Verifica si una especie es un pez."""
        return self.is_descendant_of(species_id, "pisces")
    
    def is_insect(self, species_id: str) -> bool:
        """Verifica si una especie es un insecto."""
        return self.is_descendant_of(species_id, "insecta")
    
    def is_fungus(self, species_id: str) -> bool:
        """Verifica si una especie es un hongo."""
        return self.is_descendant_of(species_id, "fungi")
    
    def is_plant(self, species_id: str) -> bool:
        """Verifica si una especie es una planta."""
        return self.is_descendant_of(species_id, "plantae")
    
    def is_bacteria(self, species_id: str) -> bool:
        """Verifica si una especie es una bacteria."""
        return self.is_descendant_of(species_id, "bacteria")
    
    # =========================================================================
    # CONSULTAS DE PERFIL
    # =========================================================================
    
    def get_profile(self, species_id: str) -> Optional[SpeciesProfile]:
        """Obtiene el perfil biológico de una especie."""
        return self._species_profiles.get(species_id)
    
    def get_diet(self, species_id: str) -> Optional[DietType]:
        """Obtiene la dieta de una especie."""
        profile = self._species_profiles.get(species_id)
        return profile.diet if profile else None
    
    def get_habitat(self, species_id: str) -> Optional[HabitatType]:
        """Obtiene el hábitat de una especie."""
        profile = self._species_profiles.get(species_id)
        return profile.habitat if profile else None
    
    def get_locomotion(self, species_id: str) -> Optional[LocomotionType]:
        """Obtiene la locomoción de una especie."""
        profile = self._species_profiles.get(species_id)
        return profile.locomotion if profile else None
    
    def is_carnivore(self, species_id: str) -> bool:
        """Verifica si una especie es carnívora."""
        profile = self._species_profiles.get(species_id)
        return profile.is_carnivore() if profile else False
    
    def is_herbivore(self, species_id: str) -> bool:
        """Verifica si una especie es herbívora."""
        profile = self._species_profiles.get(species_id)
        return profile.is_herbivore() if profile else False
    
    def is_predator(self, species_id: str) -> bool:
        """Verifica si una especie es un depredador potencial."""
        profile = self._species_profiles.get(species_id)
        return profile.is_predator() if profile else False
    
    # =========================================================================
    # CONSULTAS POR CATEGORÍA
    # =========================================================================
    
    def get_species_by_diet(self, diet: DietType) -> List[str]:
        """Retorna todas las especies con una dieta específica."""
        return [
            sid for sid, profile in self._species_profiles.items()
            if profile.diet == diet
        ]
    
    def get_species_by_habitat(self, habitat: HabitatType) -> List[str]:
        """Retorna todas las especies con un hábitat específico."""
        return [
            sid for sid, profile in self._species_profiles.items()
            if profile.habitat == habitat
        ]
    
    def get_species_by_locomotion(self, locomotion: LocomotionType) -> List[str]:
        """Retorna todas las especies con una locomoción específica."""
        return [
            sid for sid, profile in self._species_profiles.items()
            if profile.locomotion == locomotion
        ]
    
    def get_species_by_taxonomy(self, ancestor_id: str) -> List[str]:
        """Retorna todas las especies descendientes de un taxón."""
        return [
            sid for sid, taxon_id in self._species_taxonomy.items()
            if self.taxonomy.is_descendant_of(taxon_id, ancestor_id)
        ]
    
    # =========================================================================
    # CONSULTAS PARA ECOLOGÍA
    # =========================================================================
    
    def can_interact(
        self,
        species_a_id: str,
        species_b_id: str,
    ) -> bool:
        """Verifica si dos especies pueden interactuar ecológicamente.
        
        Esta es una verificación básica. El EcologicalRelationshipSystem
        hará verificaciones más detalladas usando genomas y biomas.
        """
        profile_a = self._species_profiles.get(species_a_id)
        profile_b = self._species_profiles.get(species_b_id)
        
        if profile_a is None or profile_b is None:
            return False
        
        # Verificar compatibilidad de hábitat
        if profile_a.habitat != profile_b.habitat:
            # Hábitats incompatibles (excepto anfibio que puede estar en ambos)
            if profile_a.habitat != HabitatType.AMPHIBIOUS and \
               profile_b.habitat != HabitatType.AMPHIBIOUS:
                return False
        
        return True
    
    def get_potential_prey(self, predator_id: str) -> List[str]:
        """Retorna las presas potenciales de un depredador.
        
        Basado en perfiles, no en genomas. El sistema ecológico
        hará la verificación final con genomas y biomas.
        """
        predator_profile = self._species_profiles.get(predator_id)
        if predator_profile is None:
            return []
        
        if not predator_profile.is_predator():
            return []
        
        potential_prey = []
        for species_id, profile in self._species_profiles.items():
            if species_id == predator_id:
                continue
            
            # Presas potenciales: herbívoros u omnívoros más pequeños
            if profile.diet in (DietType.HERBIVORE, DietType.OMNIVORE):
                if profile.body_size_category.value <= predator_profile.body_size_category.value:
                    if self.can_interact(predator_id, species_id):
                        potential_prey.append(species_id)
        
        return potential_prey
    
    # =========================================================================
    # ESTADÍSTICAS
    # =========================================================================
    
    def get_statistics(self) -> Dict[str, object]:
        """Retorna estadísticas del sistema de clasificación."""
        stats: Dict[str, object] = {
            "total_species": len(self._species_taxonomy),
            "species_with_profile": len(self._species_profiles),
        }
        
        # Por dieta
        diet_counts: Dict[str, int] = {}
        for profile in self._species_profiles.values():
            diet_name = profile.diet.value
            diet_counts[diet_name] = diet_counts.get(diet_name, 0) + 1
        stats["by_diet"] = diet_counts
        
        # Por hábitat
        habitat_counts: Dict[str, int] = {}
        for profile in self._species_profiles.values():
            habitat_name = profile.habitat.value
            habitat_counts[habitat_name] = habitat_counts.get(habitat_name, 0) + 1
        stats["by_habitat"] = habitat_counts
        
        return stats
    
    # =========================================================================
    # INICIALIZACIÓN POR DEFECTO
    # =========================================================================
    
    def initialize_defaults(self) -> None:
        """Inicializa la clasificación de especies por defecto."""
        from core.genetics.species_definition import SpeciesRegistry
        
        SpeciesRegistry.initialize_defaults()
        
        # Mapeo de especies a taxones
        taxonomy_mapping = {
            "human": "homo_sapiens",
            "bird": "aves",
            "fish": "pisces",
            "insect": "insecta",
            "reptile": "reptilia",
            "amphibian": "amphibia",
            "grass": "plantae",         
            "fungus": "fungi",
            "bacteria": "bacteria",
        }
        
        for species_id, taxon_id in taxonomy_mapping.items():
            species = SpeciesRegistry.get(species_id)
            if species is not None:
                self.register_species(species, taxon_id=taxon_id)
        
        self._logger.info(
            f"Clasificación por defecto inicializada: {len(self._species_taxonomy)} especies"
        )
    
    # =========================================================================
    # UTILIDADES
    # =========================================================================
    
    def __len__(self) -> int:
        return len(self._species_taxonomy)
    
    def __contains__(self, species_id: str) -> bool:
        return species_id in self._species_taxonomy
    
    def __repr__(self) -> str:
        return f"SpeciesClassificationSystem({len(self._species_taxonomy)} especies)"