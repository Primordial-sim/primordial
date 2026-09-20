"""Inferencia de relaciones ecológicas desde perfil + genoma.

El corazón del sistema: infiere relaciones posibles entre dos especies
basándose en sus perfiles biológicos y rasgos genéticos.

Filosofía:
- Las relaciones EMERGEN de la combinación de perfil + genoma
- No hay tablas fijas de "quién come a quién"
- Las excepciones (ej: koala → eucalipto) se manejan aparte
"""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from systems.ecology.relationship_types import RelationshipType, MechanismType
from systems.ecology.relationship_effect import (
    RelationshipEffect,
    predator_success_effect,
    prey_death_effect,
    herbivore_grazing_effect,
    plant_consumed_effect,
    mutualism_benefit,
)
from systems.ecology.ecological_relationship import EcologicalRelationship
from core.taxonomy.profile_enums import DietType, HabitatType, BodySizeCategory

if TYPE_CHECKING:
    from core.genetics.species_definition import SpeciesDefinition
    from core.taxonomy.species_classification import SpeciesClassificationSystem


class RelationshipInference:
    """Infiere relaciones ecológicas entre dos especies."""
    
    def __init__(self, classification: 'SpeciesClassificationSystem') -> None:
        self.classification = classification
    
    def infer_relationships(
        self,
        species_a: 'SpeciesDefinition',
        species_b: 'SpeciesDefinition',
    ) -> List[EcologicalRelationship]:
        """Infiere todas las relaciones posibles entre dos especies.
        
        Args:
            species_a: Primera especie.
            species_b: Segunda especie.
            
        Returns:
            Lista de relaciones posibles.
        """
        relationships = []
        
        # 1. Depredación: carnívoro + presa adecuada
        predation = self._infer_predation(species_a, species_b)
        if predation:
            relationships.append(predation)
        
        # 2. Herbivoría: herbívoro + planta
        herbivory = self._infer_herbivory(species_a, species_b)
        if herbivory:
            relationships.append(herbivory)
        
        # 3. Mutualismo: symbiosis alto en ambos
        mutualism = self._infer_mutualism(species_a, species_b)
        if mutualism:
            relationships.append(mutualism)
        
        # 4. Competencia: misma dieta y hábitat compatible
        competition = self._infer_competition(species_a, species_b)
        if competition:
            relationships.append(competition)
        
        return relationships
    
    # =========================================================================
    # INFERENCIA DE PREDACIÓN
    # =========================================================================
    
    def _infer_predation(
        self,
        predator: 'SpeciesDefinition',
        prey: 'SpeciesDefinition',
    ) -> Optional[EcologicalRelationship]:
        """Infiere si una especie puede depredar a otra."""
        
        # Obtener perfiles
        predator_profile = self.classification.get_profile(predator.species_id)
        prey_profile = self.classification.get_profile(prey.species_id)
        
        if predator_profile is None or prey_profile is None:
            return None
        
        # Verificar instinto depredador
        # Permite que omnívoros con instinto de caza también depreden
        predator_instinct = self._get_trait(predator, "predatory_instinct", default=0.0)
        if not predator_profile.is_predator() and predator_instinct < 0.5:
            return None
        
        # Verificar que la presa es herbívora u omnívora
        if prey_profile.diet not in (DietType.HERBIVORE, DietType.OMNIVORE):
            return None
        
        # Verificación flexible de hábitat para depredación
        if not self._can_predation_habitat_interact(
            predator_profile.habitat, prey_profile.habitat
        ):
            return None
        
        # Verificar tamaño: la presa no debe ser mucho más grande
        size_diff = self._compare_body_size(
            predator_profile.body_size_category,
            prey_profile.body_size_category,
        )
        if size_diff < -1:  # Presa mucho más grande
            return None
        
        # Calcular intensidad de la relación
        intensity = self._calculate_predation_intensity(predator, prey)
        
        # Si la intensidad es muy baja, no hay relación significativa
        if intensity < 0.5:
            return None
        
        # Determinar mecanismo basado en comportamiento
        pack_behavior = self._get_trait(predator, "pack_behavior", default=0.0)
        if pack_behavior > 1.0:
            mechanism = MechanismType.PACK_HUNTING
        else:
            mechanism = MechanismType.HUNT
        
        # Crear efectos
        effect_on_predator = predator_success_effect(energy_gain=0.6 * intensity)
        effect_on_prey = prey_death_effect(death_probability=0.7 * intensity)
        
        return EcologicalRelationship(
            species_a_id=predator.species_id,
            species_b_id=prey.species_id,
            relationship_type=RelationshipType.PREDATION,
            mechanism=mechanism,
            intensity=intensity,
            biome_requirements=[],
            seasonal_constraints=[],
            effect_on_a=effect_on_predator,
            effect_on_b=effect_on_prey,
            notes="Relación de depredación inferida",
        )
    
    # =========================================================================
    # INFERENCIA DE HERBIVORÍA
    # =========================================================================
    
    def _infer_herbivory(
        self,
        herbivore: 'SpeciesDefinition',
        plant: 'SpeciesDefinition',
    ) -> Optional[EcologicalRelationship]:
        """Infiere si un herbívoro puede consumir una planta."""
        
        herbivore_profile = self.classification.get_profile(herbivore.species_id)
        plant_profile = self.classification.get_profile(plant.species_id)
        
        if herbivore_profile is None or plant_profile is None:
            return None
        
        # Verificar que el herbívoro es herbívoro
        if herbivore_profile.diet != DietType.HERBIVORE:
            return None
        
        # Verificar que la planta es fotosintética o productor
        if plant_profile.diet != DietType.PHOTOSYNTHETIC:
            return None
        
        # Verificar compatibilidad de hábitat
        if not self.classification.can_interact(herbivore.species_id, plant.species_id):
            return None
        
        # Obtener rasgos genéticos
        herbivore_metabolism = self._get_trait(herbivore, "metabolism", default=0.5)
        plant_defense = self._get_trait(plant, "defense_capability", default=0.0)
        
        # Calcular intensidad
        intensity = min(1.0, 0.5 + herbivore_metabolism * 0.2 - plant_defense * 0.1)
        
        if intensity < 0.2:
            return None
        
        # Crear efectos
        effect_on_herbivore = herbivore_grazing_effect(energy_gain=0.3 * intensity)
        effect_on_plant = plant_consumed_effect(damage=0.3 * intensity)
        
        return EcologicalRelationship(
            species_a_id=herbivore.species_id,
            species_b_id=plant.species_id,
            relationship_type=RelationshipType.HERBIVORY,
            mechanism=MechanismType.GRAZING,
            intensity=intensity,
            biome_requirements=[],
            seasonal_constraints=[],
            effect_on_a=effect_on_herbivore,
            effect_on_b=effect_on_plant,
            notes="Relación de herbivoría inferida",
        )
    
    # =========================================================================
    # INFERENCIA DE MUTUALISMO
    # =========================================================================
    
    def _infer_mutualism(
        self,
        species_a: 'SpeciesDefinition',
        species_b: 'SpeciesDefinition',
    ) -> Optional[EcologicalRelationship]:
        """Infiere si dos especies pueden tener mutualismo.
        
        Nota: Mutualism es simétrico. Para evitar duplicados (A→B y B→A),
        ordenamos las especies alfabéticamente.
        """
        # Ordenar alfabéticamente para evitar duplicados
        if species_a.species_id > species_b.species_id:
            species_a, species_b = species_b, species_a
        
        symbiosis_a = self._get_trait(species_a, "symbiosis", default=0.0)
        symbiosis_b = self._get_trait(species_b, "symbiosis", default=0.0)
        
        # Mutualismo requiere symbiosis alto en ambos
        if symbiosis_a < 0.5 or symbiosis_b < 0.5:
            return None
        
        # Verificar compatibilidad de hábitat
        if not self.classification.can_interact(species_a.species_id, species_b.species_id):
            return None
        
        # Calcular intensidad
        intensity = min(1.0, (symbiosis_a + symbiosis_b) / 4.0)
        
        # Crear efectos beneficiosos para ambos
        effect_a = mutualism_benefit(energy_gain=0.2 * intensity)
        effect_b = mutualism_benefit(energy_gain=0.2 * intensity)
        
        return EcologicalRelationship(
            species_a_id=species_a.species_id,
            species_b_id=species_b.species_id,
            relationship_type=RelationshipType.MUTUALISM,
            mechanism=MechanismType.POLLINATION,
            intensity=intensity,
            biome_requirements=[],
            seasonal_constraints=[],
            effect_on_a=effect_a,
            effect_on_b=effect_b,
            notes="Relación de mutualismo inferida (symbiosis alto en ambos)",
        )
    
    # =========================================================================
    # INFERENCIA DE COMPETENCIA
    # =========================================================================
    
    def _infer_competition(
        self,
        species_a: 'SpeciesDefinition',
        species_b: 'SpeciesDefinition',
    ) -> Optional[EcologicalRelationship]:
        """Infiere si dos especies compiten por recursos.
        
        Nota: Competition es simétrico. Para evitar duplicados (A→B y B→A),
        ordenamos las especies alfabéticamente.
        """
        # Ordenar alfabéticamente para evitar duplicados
        if species_a.species_id > species_b.species_id:
            species_a, species_b = species_b, species_a
        
        profile_a = self.classification.get_profile(species_a.species_id)
        profile_b = self.classification.get_profile(species_b.species_id)
        
        if profile_a is None or profile_b is None:
            return None
        
        # No competir consigo mismo
        if species_a.species_id == species_b.species_id:
            return None
        
        # Competencia requiere misma dieta
        if profile_a.diet != profile_b.diet:
            return None
        
        # Verificación flexible de hábitat (solapamiento, no igualdad estricta)
        habitat_overlap = (
            profile_a.habitat == profile_b.habitat or
            self._can_predation_habitat_interact(profile_a.habitat, profile_b.habitat)
        )
        
        if not habitat_overlap:
            return None
        
        # Calcular intensidad basada en similitud de nicho
        intensity = 0.3  # Competencia base
        
        # Aumentar si tienen el mismo tamaño corporal
        if profile_a.body_size_category == profile_b.body_size_category:
            intensity += 0.2
        
        # Aumentar si tienen la misma locomoción
        if profile_a.locomotion == profile_b.locomotion:
            intensity += 0.1
        
        # Aumentar si tienen exactamente el mismo hábitat
        if profile_a.habitat == profile_b.habitat:
            intensity += 0.1
        
        intensity = min(1.0, intensity)
        
        # Crear efectos negativos para ambos
        effect_a = RelationshipEffect(
            energy_change=-0.1 * intensity,
            stress_change=0.1 * intensity,
            description="Competencia por recursos",
        )
        effect_b = RelationshipEffect(
            energy_change=-0.1 * intensity,
            stress_change=0.1 * intensity,
            description="Competencia por recursos",
        )
        
        return EcologicalRelationship(
            species_a_id=species_a.species_id,
            species_b_id=species_b.species_id,
            relationship_type=RelationshipType.COMPETITION,
            mechanism=MechanismType.RESOURCE_CONSUMPTION,
            intensity=intensity,
            biome_requirements=[],
            seasonal_constraints=[],
            effect_on_a=effect_a,
            effect_on_b=effect_b,
            notes="Relación de competencia inferida",
        )
    
    # =========================================================================
    # MÉTODOS AUXILIARES
    # =========================================================================
    
    def _can_predation_habitat_interact(
        self,
        predator_habitat: HabitatType,
        prey_habitat: HabitatType,
    ) -> bool:
        """Verifica si dos hábitats permiten depredación.
        
        Más flexible que can_interact() para reflejar la realidad:
        - Aves aéreas cazan presas terrestres
        - Peces acuáticos cazan presas anfibias
        - Anfibios cazan en ambos medios
        """
        # Mismo hábitat: siempre pueden interactuar
        if predator_habitat == prey_habitat:
            return True
        
        # Matriz de compatibilidad para depredación
        compatible_pairs = {
            # Aves cazan en tierra y agua superficial
            (HabitatType.AERIAL, HabitatType.TERRESTRIAL),
            (HabitatType.AERIAL, HabitatType.AMPHIBIOUS),
            
            # Peces cazan anfibios y organismos acuáticos
            (HabitatType.AQUATIC, HabitatType.AMPHIBIOUS),
            
            # Anfibios cazan en ambos medios
            (HabitatType.AMPHIBIOUS, HabitatType.TERRESTRIAL),
            (HabitatType.AMPHIBIOUS, HabitatType.AQUATIC),
            
            # Terrestres cazan anfibios en la orilla
            (HabitatType.TERRESTRIAL, HabitatType.AMPHIBIOUS),
        }
        
        return (predator_habitat, prey_habitat) in compatible_pairs
    
    def _get_trait(self, species: 'SpeciesDefinition', trait_id: str, default: float = 0.0) -> float:
        """Obtiene el valor de un rasgo de la especie."""
        config = species.get_trait_config(trait_id)
        if config is not None:
            return config.default_value
        return default
    
    def _compare_body_size(
        self,
        size_a: BodySizeCategory,
        size_b: BodySizeCategory,
    ) -> int:
        """Compara el tamaño corporal de dos especies.
        
        Returns:
            -2 si A es mucho más pequeña que B
            -1 si A es más pequeña que B
             0 si son similares
             1 si A es más grande que B
             2 si A es mucho más grande que B
        """
        size_order = [
            BodySizeCategory.MICROSCOPIC,
            BodySizeCategory.SMALL,
            BodySizeCategory.MEDIUM,
            BodySizeCategory.LARGE,
            BodySizeCategory.GIANT,
        ]
        
        idx_a = size_order.index(size_a)
        idx_b = size_order.index(size_b)
        
        diff = idx_a - idx_b
        
        if diff <= -2:
            return -2
        elif diff == -1:
            return -1
        elif diff == 0:
            return 0
        elif diff == 1:
            return 1
        else:
            return 2
    
    def _calculate_predation_intensity(
        self,
        predator: 'SpeciesDefinition',
        prey: 'SpeciesDefinition',
    ) -> float:
        """Calcula la intensidad de una relación de depredación.
    
        Considera:
        - Instinto y velocidad del depredador (ataque)
        - Defensa, velocidad, INTELIGENCIA y SOCIABILIDAD de la presa (defensa)
    
        La inteligencia y sociabilidad son defensas poderosas:
        - Inteligencia alta = herramientas, estrategias de escape, fuego
        - Sociabilidad alta = defensa en grupo, alerta temprana
        """
        # Factores de ataque del depredador
        predator_instinct = self._get_trait(predator, "predatory_instinct", default=0.5)
        predator_speed = self._get_trait(predator, "speed", default=0.5)
    
        # Factores de defensa de la presa
        prey_defense = self._get_trait(prey, "defense_capability", default=0.5)
        prey_speed = self._get_trait(prey, "speed", default=0.5)
        prey_intelligence = self._get_trait(prey, "intelligence", default=0.5)
        prey_sociability = self._get_trait(prey, "sociability", default=0.5)
    
        # Factor de ataque del depredador
        attack_factor = (predator_instinct + predator_speed) / 2.0
    
        # Factor de defensa de la presa
        # CAMBIO: Bonus aumentados para reflejar el poder de la inteligencia
        # Inteligencia 1.8 (humano) = defensa muy fuerte
        # Sociabilidad 1.5 (humano) = defensa en grupo muy efectiva
        intelligence_bonus = prey_intelligence * 0.25   # ← Antes 0.15
        sociability_bonus = prey_sociability * 0.15     # ← Antes 0.10
    
        defense_factor = (prey_defense + prey_speed) / 2.0 + intelligence_bonus + sociability_bonus
    
        # Intensidad = ataque - defensa, normalizada
        intensity = max(0.0, min(1.0, 0.5 + attack_factor * 0.3 - defense_factor * 0.25))
    
        return intensity