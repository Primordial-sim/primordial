"""Gestor de evolución relacional. Fase 0.

Orquesta la detección de nuevos encuentros y la evaluación de etiquetas
emergentes. Las variables emocionales se derivan automáticamente de la memoria.

OPTIMIZACIÓN DE RENDIMIENTO:
- Uso de SpatialGrid para reducir búsquedas de vecinos de O(N²) a O(N)
- Reemplazo de math.sqrt por comparaciones al cuadrado
"""

from __future__ import annotations

import logging
import math
import random
import hashlib
from typing import Any, Set

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext
from systems.relationships.compatibility_engine import CompatibilityEngine
from systems.relationships.relationship_model import (
    SexualOrientation,
    MemoryCategory,
    MemoryRole,
    PersonalMemory,
    WorldEvent,
)
from systems.spatial.spatial_grid import SpatialGrid


class RelationshipManager:
    """Orquesta la evolución continua de relaciones entre agentes."""

    def __init__(
        self,
        config: SimulationConfig,
        compatibility_engine: CompatibilityEngine,
    ) -> None:
        self.config = config
        self.rel_cfg = config.relationships
        self.compatibility = compatibility_engine
        self.logger = logging.getLogger(self.__class__.__name__)
        self._relationships_created_this_tick: Set[tuple] = set()
        
        # OPTIMIZACIÓN: Grid espacial para búsquedas de vecinos O(N)
        self.spatial_grid = SpatialGrid(cell_size=35.0)

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Evalúa y actualiza relaciones de todos los agentes vivos."""
        current_day = getattr(state, 'world_days_elapsed', 0.0)
        self._relationships_created_this_tick.clear()
        
        # OPTIMIZACIÓN: Poblar el grid espacial una vez por tick
        self.spatial_grid.populate_from_state(state)
        
        persons = list(state.get_all_persons())
        
        for person in persons:
            if person.entity_id in pending.deaths:
                continue
            
            self._detect_new_relationships(person, pending, current_day, context)

    def _detect_new_relationships(
        self,
        person: Any,
        pending: PendingChanges,
        current_day: float,
        context: EnvironmentContext,
    ) -> None:
        """Detecta agentes cercanos para iniciar relaciones.
        
        OPTIMIZACIÓN: Usa SpatialGrid para limitar la búsqueda a vecinos
        cercanos, reduciendo la complejidad de O(N²) a O(N).
        """
        detection_radius = 35.0
        
        # OPTIMIZACIÓN: Usar el grid espacial para obtener solo vecinos cercanos
        nearby_agents = self.spatial_grid.get_nearby_agents(person, detection_radius)
        
        for other in nearby_agents:
            if other.entity_id in pending.deaths:
                continue
            
            # GENÉTICA UNIVERSAL: Solo crear relaciones si ambos pueden reconocer individuos
            from systems.relationships.social_capabilities import SocialCapabilities
            person_caps = SocialCapabilities.from_genome(person.genome)
            other_caps = SocialCapabilities.from_genome(other.genome)
            
            if not person_caps.can_recognize_individuals or not other_caps.can_recognize_individuals:
                continue
            
            # OPTIMIZACIÓN: Evitar procesar el mismo par dos veces
            if other.entity_id <= person.entity_id:
                continue
            
            # Verificar compatibilidad de orientaciones
            if not self._are_orientations_compatible(person.sexual_orientation, other.sexual_orientation):
                continue
            
            # CORRECCIÓN: get_relationship_with ya crea la relación si no existe.
            rel_person = person.get_relationship_with(other.entity_id, current_day)
            if len(rel_person.memories) > 0:
                continue
            
            relationship_key = (person.entity_id, other.entity_id) if person.entity_id < other.entity_id else (other.entity_id, person.entity_id)
            if relationship_key in self._relationships_created_this_tick:
                continue
            
            # OPTIMIZACIÓN: Calcular distancia real solo si el random pasa el primer filtro
            if random.random() >= 0.15:
                continue
            
            # Ahora sí calcular la distancia real para ajustar la probabilidad
            dx = person.x - other.x
            dy = person.y - other.y
            distance = math.sqrt(dx * dx + dy * dy)
            
            # Ajustar probabilidad según distancia
            adjusted_chance = 1.0 - (distance / detection_radius)
            if random.random() >= adjusted_chance:
                continue
            
            # CORRECCIÓN: ID determinista basado en entidades y día
            event_id_str = f"{person.entity_id}_{other.entity_id}_{int(current_day)}"
            event_id = int(hashlib.md5(event_id_str.encode()).hexdigest()[:8], 16)
            
            world_event = WorldEvent(
                event_id=event_id,
                event_type="met",
                category=MemoryCategory.SOCIAL,
                day=current_day,
                context="proximidad_inicial",
                source_system="RelationshipManager",
                initiator_id=person.entity_id,
                target_id=other.entity_id,
                objective_intensity=0.5,
            )
            
            mem_for_person = self._create_first_impression_memory(world_event, person, other, current_day)
            mem_for_other = self._create_first_impression_memory(world_event, other, person, current_day)
            
            # Añadir recuerdos a las relaciones (que ya existen gracias a get_relationship_with)
            rel_person.add_memory(mem_for_person, current_day)
            rel_other = other.get_relationship_with(person.entity_id, current_day)
            rel_other.add_memory(mem_for_other, current_day)
            
            self._relationships_created_this_tick.add(relationship_key)
            
            affinity = self.compatibility.calculate_compatibility(person, other, current_day)
            self.logger.info(
                "👋 Día %.0f: Agente %s conoce a %s (distancia: %.1f, afinidad: %.2f)",
                current_day, person.entity_id, other.entity_id, distance, affinity
            )

    def _are_orientations_compatible(self, o1: SexualOrientation, o2: SexualOrientation) -> bool:
        """Verifica si dos orientaciones sexuales son compatibles."""
        diff = abs(o1.value - o2.value)
        
        if (o1 == SexualOrientation.HETEROSEXUAL and o2 == SexualOrientation.HOMOSEXUAL) or \
           (o1 == SexualOrientation.HOMOSEXUAL and o2 == SexualOrientation.HETEROSEXUAL):
            return False
        
        if diff > 6.0:
            return False
        
        return True

    def _create_first_impression_memory(
        self,
        world_event: WorldEvent,
        owner: Any,
        partner: Any,
        current_day: float,
    ) -> PersonalMemory:
        """Crea el recuerdo de la primera impresión, modulado por la personalidad."""
        sociability = getattr(owner.genome, 'sociability', 1.0) / 2.0
        temperament = getattr(owner.genome, 'temperament', 1.0) / 2.0
        
        base_valence = 0.2
        base_weight = 15.0
        
        personality_modifier = 1.0 + (sociability * 0.3)
        if temperament > 0.7:
            personality_modifier *= 0.8
        
        uncertainty = random.gauss(1.0, 0.2)
        final_weight = base_weight * personality_modifier * uncertainty
        
        return PersonalMemory(
            world_event_id=world_event.event_id,
            owner_id=owner.entity_id,
            partner_id=partner.entity_id,
            perceived_intensity=0.5,
            emotional_valence=base_valence,
            personal_weight=max(5.0, final_weight),
            category=MemoryCategory.SOCIAL,
            day=current_day,
            context="first_impression",
            event_type="met",
            source_system="RelationshipManager",
            role=MemoryRole.NORMAL,
            half_life_days=30.0,
        )