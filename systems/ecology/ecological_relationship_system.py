"""Sistema Orquestador de Relaciones Ecológicas.

Orquesta la ejecución de relaciones ecológicas durante la simulación:
1. Detecta encuentros entre organismos cercanos (SpatialGrid)
2. Infiere relaciones ecológicas entre las especies (cacheadas)
3. Verifica condiciones ambientales (bioma, estación)
4. Ejecuta el mecanismo de interacción
5. Aplica efectos a los organismos

Filosofía: "Las relaciones ecológicas emergen de la combinación de
perfil + genoma + entorno, y se ejecutan cuando las condiciones lo permiten."
"""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from systems.ecology.relationship_types import (
    RelationshipType,
    MechanismType,
    InteractionOutcome,
)
from systems.ecology.relationship_inference import RelationshipInference
from systems.ecology.biome_condition_checker import BiomeConditionChecker
from core.taxonomy.species_classification import SpeciesClassificationSystem
from systems.ecology.mechanisms import MechanismFactory

if TYPE_CHECKING:
    from core.state.world_state import WorldState
    from core.state.pending_changes import PendingChanges
    from systems.environment.environment_context import EnvironmentContext
    from systems.ecology.ecological_relationship import EcologicalRelationship
    from entities.person.person import Person


class EcologicalRelationshipSystem:
    """Orquestador principal de relaciones ecológicas.
    
    Uso:
        ecology_system = EcologicalRelationshipSystem()
        
        # En cada tick de simulación:
        ecology_system.process(state, pending, delta_days, context)
    """
    
    _logger = logging.getLogger("EcologicalRelationshipSystem")
    
    def __init__(self) -> None:
        # Sistema de clasificación (taxonomía + perfiles)
        self.classification = SpeciesClassificationSystem.get_default()
        
        # Inferidor de relaciones
        self.inference = RelationshipInference(self.classification)
        
        # Verificador de condiciones ambientales
        self.biome_checker = BiomeConditionChecker()
        
        # Contador para procesamiento periódico (no cada tick)
        self._process_counter: float = 0.0
        self.process_interval: float = 3.0  # Cada 3 días
        
        # Cache de relaciones inferidas entre pares de especies
        # Clave: (species_a_id, species_b_id)
        # Valor: List[EcologicalRelationship]
        self._relationship_cache: Dict[Tuple[str, str], List['EcologicalRelationship']] = {}
        
        # Estadísticas
        self._total_encounters: int = 0
        self._total_relationships_executed: int = 0
        self._total_predations: int = 0
        self._total_herbivory: int = 0
        self._total_mutualism: int = 0
        self._total_competition: int = 0
    
    # =========================================================================
    # MÉTODO PRINCIPAL
    # =========================================================================
    
    def process(
        self,
        state: 'WorldState',
        pending: 'PendingChanges',
        delta_days: float,
        context: 'EnvironmentContext',
    ) -> None:
        """Procesa las relaciones ecológicas para el tick actual.
        
        Args:
            state: Estado del mundo con agentes y mapa.
            pending: Buffer de cambios pendientes.
            delta_days: Días transcurridos desde el último tick.
            context: Contexto ambiental (estación, clima, etc.)
        """
        if not state.has_tile_map():
            return
        
        # Procesar solo cada N días para optimización
        self._process_counter += delta_days
        if self._process_counter < self.process_interval:
            return
        
        self._process_counter = 0.0
        
        # Obtener todos los agentes vivos
        persons = list(state.get_all_persons())
        if not persons:
            return
        
        # Obtener SpatialGrid para búsquedas espaciales
        spatial_grid = getattr(state, 'spatial_grid', None)
        if spatial_grid is None:
            return
        
        # Obtener estación actual
        current_season = self._get_current_season(context)
        
        # Procesar cada agente
        relationships_executed = 0
        
        for person in persons:
            # Buscar vecinos cercanos
            nearby_agents = self._get_nearby_agents(spatial_grid, person, radius=2)
            
            for other in nearby_agents:
                if person.entity_id == other.entity_id:
                    continue
                
                # Obtener tile actual
                tile = state.get_tile_at(int(person.x), int(person.y))
                if tile is None:
                    continue
                
                # Inferir relaciones entre las especies (cacheadas)
                relationships = self._get_or_infer_relationships(person, other)
                
                if not relationships:
                    continue
                
                self._total_encounters += 1
                
                # Procesar cada relación
                for relationship in relationships:
                    # Verificar condiciones ambientales
                    if not self.biome_checker.check(relationship, tile, current_season):
                        continue
                    
                    # Ejecutar la relación
                    outcome = self._execute_relationship(
                        person, other, relationship, pending
                    )
                    
                    if outcome == InteractionOutcome.SUCCESS:
                        relationships_executed += 1
                        self._total_relationships_executed += 1
                        
                        # Actualizar estadísticas por tipo
                        self._update_stats(relationship.relationship_type)
        
        if relationships_executed > 0:
            self._logger.debug(
                f"🌿 Ecología: {relationships_executed} relaciones ejecutadas "
                f"de {self._total_encounters} encuentros"
            )
    
    # =========================================================================
    # DETECCIÓN DE ENCUENTROS
    # =========================================================================
    
    def _get_nearby_agents(
        self,
        spatial_grid,
        person: 'Person',
        radius: int = 2,
    ) -> List['Person']:
        """Obtiene agentes cercanos usando SpatialGrid.
        
        Args:
            spatial_grid: El grid espacial del estado.
            person: El agente central.
            radius: Radio de búsqueda en tiles.
            
        Returns:
            Lista de agentes cercanos (excluyendo al propio).
        """
        try:
            nearby = spatial_grid.get_nearby_agents(person, radius)
            # Excluir al propio agente
            return [a for a in nearby if a.entity_id != person.entity_id]
        except (AttributeError, TypeError):
            # Si SpatialGrid no está disponible o falla, retornar vacío
            return []
    
    # =========================================================================
    # INFERENCIA DE RELACIONES (CON CACHÉ)
    # =========================================================================
    
    def _get_or_infer_relationships(
        self,
        person_a: 'Person',
        person_b: 'Person',
    ) -> List['EcologicalRelationship']:
        """Obtiene las relaciones entre dos organismos (usando caché).
        
        Las relaciones se infieren una vez por par de especies y se cachean.
        
        Args:
            person_a: Primer organismo.
            person_b: Segundo organismo.
            
        Returns:
            Lista de relaciones ecológicas posibles.
        """
        species_a_id = person_a.species
        species_b_id = person_b.species
        
        # Generar clave de caché (ordenada para evitar duplicados A→B y B→A)
        sorted_pair = sorted([species_a_id, species_b_id])
        cache_key: Tuple[str, str] = (sorted_pair[0], sorted_pair[1])
        
        # Verificar caché
        if cache_key in self._relationship_cache:
            cached = self._relationship_cache[cache_key]
            # Filtrar relaciones donde person_a es el iniciador correcto
            return [
                r for r in cached
                if r.species_a_id == species_a_id
            ]
        
        # Inferir relaciones (solo una vez por par de especies)
        species_a = self._get_species_definition(species_a_id)
        species_b = self._get_species_definition(species_b_id)
        
        if species_a is None or species_b is None:
            self._relationship_cache[cache_key] = []
            return []
        
                # Inferir en ambas direcciones (A→B y B→A)
        # Necesario para relaciones asimétricas como Predation
        relationships_ab = self.inference.infer_relationships(species_a, species_b)
        relationships_ba = self.inference.infer_relationships(species_b, species_a)
        
        all_relationships = relationships_ab + relationships_ba
        
        # Deduplicar relaciones simétricas (Competition, Mutualism)
        # Usar (species_a, species_b, type) como clave única
        seen = set()
        unique_relationships = []
        for rel in all_relationships:
            # Para relaciones simétricas, ordenar la clave
            if rel.relationship_type in (RelationshipType.COMPETITION, RelationshipType.MUTUALISM):
                pair = tuple(sorted([rel.species_a_id, rel.species_b_id]))
                rel_key = (pair[0], pair[1], rel.relationship_type)
            else:
                rel_key = (rel.species_a_id, rel.species_b_id, rel.relationship_type)
            
            if rel_key not in seen:
                seen.add(rel_key)
                unique_relationships.append(rel)
        
        # Cachear relaciones únicas
        self._relationship_cache[cache_key] = unique_relationships
        
        # Retornar solo las relaciones donde person_a es el iniciador
        return [r for r in unique_relationships if r.species_a_id == species_a_id]
    
    def _get_species_definition(self, species_id: str):
        """Obtiene la SpeciesDefinition desde el SpeciesRegistry."""
        from core.genetics.species_definition import SpeciesRegistry
        return SpeciesRegistry.get(species_id)
    
    # =========================================================================
    # EJECUCIÓN DE RELACIONES
    # =========================================================================
    
    def _execute_relationship(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
    ) -> InteractionOutcome:
        """Ejecuta una relación ecológica entre dos organismos.
        
        Despacha al mecanismo correspondiente según relationship.mechanism.
        
        Args:
            person_a: Organismo que inicia la relación.
            person_b: Organismo objetivo.
            relationship: La relación a ejecutar.
            pending: Buffer de cambios pendientes.
            
        Returns:
            El resultado de la interacción.
        """
        # Obtener el mecanismo correspondiente
        mechanism = MechanismFactory.get_mechanism(relationship.mechanism)
        
        # Ejecutar el mecanismo
        return mechanism.execute(person_a, person_b, relationship, pending)
    
    # =========================================================================
    # MÉTODOS AUXILIARES
    # =========================================================================
    
    def _get_current_season(self, context: 'EnvironmentContext') -> str:
        """Obtiene la estación actual del contexto ambiental."""
        try:
            # Intentar obtener la estación del contexto
            season = getattr(context, 'current_season', None)
            if season is not None:
                # Si es un enum, obtener el valor
                if hasattr(season, 'value'):
                    return str(season.value).lower()
                return str(season).lower()
        except (AttributeError, TypeError):
            pass
        
        # Por defecto: sin estación específica
        return "summer"
    
    def _apply_energy_change(
        self,
        person: 'Person',
        energy_change: float,
        pending: 'PendingChanges',
    ) -> None:
        """Aplica un cambio de energía a un organismo.
        
        Args:
            person: El organismo al que aplicar el cambio.
            energy_change: Cantidad de energía a añadir (positiva) o gastar (negativa).
            pending: Buffer de cambios pendientes (no usado actualmente).
        """
        if energy_change > 0:
            # Ganancia de energía
            person.add_energy(energy_change)
        elif energy_change < 0:
            # Gasto de energía
            person.spend_energy(abs(energy_change))
    
    def _update_stats(self, relationship_type: RelationshipType) -> None:
        """Actualiza las estadísticas de relaciones ejecutadas."""
        if relationship_type == RelationshipType.PREDATION:
            self._total_predations += 1
        elif relationship_type == RelationshipType.HERBIVORY:
            self._total_herbivory += 1
        elif relationship_type == RelationshipType.MUTUALISM:
            self._total_mutualism += 1
        elif relationship_type == RelationshipType.COMPETITION:
            self._total_competition += 1
    
    # =========================================================================
    # MÉTODOS DE CONSULTA
    # =========================================================================
    
    def get_summary(self) -> Dict[str, object]:
        """Retorna un resumen de las relaciones ejecutadas."""
        return {
            "total_encounters": self._total_encounters,
            "total_relationships_executed": self._total_relationships_executed,
            "total_predations": self._total_predations,
            "total_herbivory": self._total_herbivory,
            "total_mutualism": self._total_mutualism,
            "total_competition": self._total_competition,
            "cached_relationship_pairs": len(self._relationship_cache),
            "mechanism_stats": MechanismFactory.get_all_stats(),
        }
    
    def get_relationships_between(self, species_a: str, species_b: str) -> List['EcologicalRelationship']:
        """Obtiene las relaciones cacheadas entre dos especies."""
        sorted_pair = sorted([species_a, species_b])
        cache_key: Tuple[str, str] = (sorted_pair[0], sorted_pair[1])
        return self._relationship_cache.get(cache_key, [])
    
    def clear_cache(self) -> None:
        """Limpia la caché de relaciones (útil para tests)."""
        self._relationship_cache.clear()
    
    def __repr__(self) -> str:
        return (
            f"EcologicalRelationshipSystem("
            f"executed={self._total_relationships_executed}, "
            f"cached={len(self._relationship_cache)})"
        )