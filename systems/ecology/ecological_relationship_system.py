"""Sistema Orquestador de Relaciones Ecológicas.

Orquesta la ejecución de relaciones ecológicas durante la simulación:
1. Detecta encuentros entre organismos cercanos (SpatialGrid)
2. Infiere relaciones ecológicas entre las especies (cacheadas)
3. Verifica condiciones ambientales (bioma, estación)
4. Ejecuta el mecanismo de interacción
5. Aplica efectos a los organismos

Filosofía: "Las relaciones ecológicas emergen de la combinación de
perfil + genoma + entorno, y se ejecutan cuando las condiciones lo permiten."

MIGRACIÓN HEXAGONAL:
- person.x/y → person.q/r
- state.get_tile_at(x, y) → state.get_tile_at(q, r)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from core.taxonomy.species_classification import SpeciesClassificationSystem
from systems.ecology.biome_condition_checker import BiomeConditionChecker
from systems.ecology.mechanisms import MechanismFactory
from systems.ecology.relationship_inference import RelationshipInference
from systems.ecology.relationship_types import (
    InteractionOutcome,
    RelationshipType,
)

if TYPE_CHECKING:
    from core.config.simulation_config import SimulationConfig
    from core.state.pending_changes import PendingChanges
    from core.state.world_state import WorldState
    from entities.person.person import Person
    from systems.ecology.ecological_relationship import EcologicalRelationship
    from systems.environment.environment_context import EnvironmentContext


class EcologicalRelationshipSystem:
    """Orquestador principal de relaciones ecológicas."""

    _logger = logging.getLogger("EcologicalRelationshipSystem")

    def __init__(self, config: Optional['SimulationConfig'] = None) -> None:
        """Inicializa el sistema de relaciones ecológicas."""
        self.config = config
        self.classification = SpeciesClassificationSystem.get_default()
        self.inference = RelationshipInference(self.classification)
        self.biome_checker = BiomeConditionChecker()
        
        self._process_counter: float = 0.0
        self.process_interval: float = 1.0  # Cada 1 día (optimizado)

        self._relationship_cache: Dict[
            Tuple[str, str], List['EcologicalRelationship']
        ] = {}

        self._total_encounters: int = 0
        self._total_relationships_executed: int = 0
        self._total_predations: int = 0
        self._total_herbivory: int = 0
        self._total_mutualism: int = 0
        self._total_competition: int = 0

    def _get_process_interval(self) -> float:
        """Devuelve el intervalo de procesamiento leyendo la config en caliente."""
        if self.config is not None:
            ecology_cfg = getattr(self.config, 'ecology', None)
            if ecology_cfg is not None:
                return getattr(ecology_cfg, 'process_interval_days', self.process_interval)
        return self.process_interval

    def process(
        self,
        state: 'WorldState',
        pending: 'PendingChanges',
        delta_days: float,
        context: 'EnvironmentContext',
    ) -> None:
        """Procesa las relaciones ecológicas para el tick actual."""
        if not state.has_tile_map():
            return

        self._process_counter += delta_days
        if self._process_counter < self._get_process_interval():
            return

        self._process_counter = 0.0

        persons = list(state.get_all_persons())
        if not persons:
            return

        spatial_grid = getattr(state, 'spatial_grid', None)
        if spatial_grid is None:
            return

        current_season = self._get_current_season(context)
        relationships_executed = 0

        for person in persons:
            nearby_agents = self._get_nearby_agents(spatial_grid, person, radius=2)

            for other in nearby_agents:
                if person.entity_id == other.entity_id:
                    continue

                # HEX: Usar coordenadas hexagonales q, r
                tile = state.get_tile_at(int(person.q), int(person.r))
                if tile is None:
                    continue

                relationships = self._get_or_infer_relationships(person, other)
                if not relationships:
                    continue

                self._total_encounters += 1

                for relationship in relationships:
                    if not self.biome_checker.check(relationship, tile, current_season):
                        continue

                    outcome = self._execute_relationship(person, other, relationship, pending)

                    if outcome == InteractionOutcome.SUCCESS:
                        relationships_executed += 1
                        self._total_relationships_executed += 1
                        self._update_stats(relationship.relationship_type)

        if relationships_executed > 0:
            self._logger.debug(
                "🌿 Ecología: %d relaciones ejecutadas de %d encuentros",
                relationships_executed,
                self._total_encounters,
            )

    def _get_nearby_agents(
        self,
        spatial_grid: Any,
        person: 'Person',
        radius: int = 2,
    ) -> List['Person']:
        """Obtiene agentes cercanos usando SpatialGrid."""
        try:
            nearby = spatial_grid.get_nearby_agents(person, radius)
            return [a for a in nearby if a.entity_id != person.entity_id]
        except (AttributeError, TypeError):
            return []

    def _get_or_infer_relationships(
        self,
        person_a: 'Person',
        person_b: 'Person',
    ) -> List['EcologicalRelationship']:
        """Obtiene las relaciones entre dos organismos (usando caché)."""
        species_a_id = person_a.species
        species_b_id = person_b.species

        sorted_pair = sorted([species_a_id, species_b_id])
        cache_key: Tuple[str, str] = (sorted_pair[0], sorted_pair[1])

        if cache_key in self._relationship_cache:
            cached = self._relationship_cache[cache_key]
            return [r for r in cached if r.species_a_id == species_a_id]

        species_a = self._get_species_definition(species_a_id)
        species_b = self._get_species_definition(species_b_id)

        if species_a is None or species_b is None:
            self._relationship_cache[cache_key] = []
            return []

        relationships_ab = self.inference.infer_relationships(species_a, species_b)
        relationships_ba = self.inference.infer_relationships(species_b, species_a)
        all_relationships = relationships_ab + relationships_ba

        seen = set()
        unique_relationships = []

        for rel in all_relationships:
            if rel.relationship_type in (RelationshipType.COMPETITION, RelationshipType.MUTUALISM):
                pair = tuple(sorted([rel.species_a_id, rel.species_b_id]))
                rel_key = (pair[0], pair[1], rel.relationship_type)
            else:
                rel_key = (rel.species_a_id, rel.species_b_id, rel.relationship_type)

            if rel_key not in seen:
                seen.add(rel_key)
                unique_relationships.append(rel)

        self._relationship_cache[cache_key] = unique_relationships

        return [r for r in unique_relationships if r.species_a_id == species_a_id]

    def _get_species_definition(self, species_id: str):
        """Obtiene la SpeciesDefinition desde el SpeciesRegistry."""
        from core.genetics.species_definition import SpeciesRegistry
        return SpeciesRegistry.get(species_id)

    def _execute_relationship(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
    ) -> InteractionOutcome:
        """Ejecuta una relación ecológica entre dos organismos."""
        mechanism = MechanismFactory.get_mechanism(relationship.mechanism)
        return mechanism.execute(person_a, person_b, relationship, pending)

    def _get_current_season(self, context: 'EnvironmentContext') -> str:
        """Obtiene la estación actual del contexto ambiental."""
        try:
            season = getattr(context, 'current_season', None)
            if season is not None:
                if hasattr(season, 'value'):
                    return str(season.value).lower()
                return str(season).lower()
        except (AttributeError, TypeError):
            pass
        return "summer"

    def _apply_energy_change(
        self,
        person: 'Person',
        energy_change: float,
        pending: 'PendingChanges',
    ) -> None:
        """Aplica un cambio de energía a un organismo."""
        if energy_change > 0:
            person.add_energy(energy_change)
        elif energy_change < 0:
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

    def get_relationships_between(
        self, species_a: str, species_b: str
    ) -> List['EcologicalRelationship']:
        """Obtiene las relaciones cacheadas entre dos especies."""
        sorted_pair = sorted([species_a, species_b])
        cache_key: Tuple[str, str] = (sorted_pair[0], sorted_pair[1])
        return self._relationship_cache.get(cache_key, [])

    def clear_cache(self) -> None:
        """Limpia la caché de relaciones."""
        self._relationship_cache.clear()

    def __repr__(self) -> str:
        return (
            f"EcologicalRelationshipSystem("
            f"executed={self._total_relationships_executed}, "
            f"cached={len(self._relationship_cache)})"
        )