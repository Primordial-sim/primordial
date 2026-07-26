"""Gestor de evolución relacional. Fase 0.

Orquesta la detección de nuevos encuentros y la evaluación de etiquetas
emergentes. Las variables emocionales se derivan automáticamente de la memoria.
"""

from __future__ import annotations

import logging
import math
import random
from typing import Any, Dict, List, Optional, Set

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext
from systems.relationships.compatibility_engine import CompatibilityEngine
from systems.relationships.relationship_model import (
    Relationship,
    RelationshipStatus,
    RelationshipType,
    RelationshipEventType,
    SexualOrientation,
    MemoryCategory,
    MemoryRole,
    PersonalMemory,
    WorldEvent,
)


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
        
        for person in state.get_all_persons():
            if person.entity_id in pending.deaths:
                continue
            
            # Detectar nuevos encuentros (genera recuerdos de "met")
            self._detect_new_relationships(person, state, pending, current_day, context)

    def _detect_new_relationships(
        self,
        person: Any,
        state: WorldState,
        pending: PendingChanges,
        current_day: float,
        context: EnvironmentContext,
    ) -> None:
        """Detecta agentes cercanos para iniciar relaciones."""
        detection_radius = 35.0
        
        for other in state.get_all_persons():
            if other.entity_id == person.entity_id or other.entity_id in pending.deaths:
                continue
            if person.entity_id >= other.entity_id:  # Evitar duplicados simétricos
                continue
            
            # Verificar si ya existe una relación con recuerdos
            rel_person = person.get_relationship_with(other.entity_id, current_day)
            if rel_person is not None and len(rel_person.memories) > 0:
                continue
            
            relationship_key = tuple(sorted([person.entity_id, other.entity_id]))
            if relationship_key in self._relationships_created_this_tick:
                continue
            
            distance = math.hypot(person.x - other.x, person.y - other.y)
            if distance > detection_radius:
                continue
            
            # Verificar compatibilidad de orientaciones
            if not self._are_orientations_compatible(person.sexual_orientation, other.sexual_orientation):
                continue
            
            base_chance = 0.15 * (1.0 - distance / detection_radius)
            if random.random() < base_chance:
                # Crear el evento de encuentro como WorldEvent
                world_event = WorldEvent(
                    event_id=id(person) + id(other) + int(current_day * 1000),
                    event_type="met",
                    category=MemoryCategory.SOCIAL,
                    day=current_day,
                    context="proximidad_inicial",
                    source_system="RelationshipManager",
                    initiator_id=person.entity_id,
                    target_id=other.entity_id,
                    objective_intensity=0.5,
                )
                
                # Crear recuerdos asimétricos para ambos agentes
                mem_for_person = self._create_first_impression_memory(
                    world_event, person, other, current_day
                )
                mem_for_other = self._create_first_impression_memory(
                    world_event, other, person, current_day
                )
                
                # Obtener o crear relaciones de forma segura (con fallback)
                rel_person = person.get_relationship_with(other.entity_id, current_day)
                if rel_person is None:
                    rel_person = Relationship(owner_id=person.entity_id, partner_id=other.entity_id, start_day=current_day)
                    person._relationships.append(rel_person)

                rel_other = other.get_relationship_with(person.entity_id, current_day)
                if rel_other is None:
                    rel_other = Relationship(owner_id=other.entity_id, partner_id=person.entity_id, start_day=current_day)
                    other._relationships.append(rel_other)
                
                # Añadir recuerdos a las relaciones
                rel_person.add_memory(mem_for_person)
                rel_other.add_memory(mem_for_other)
                
                self._relationships_created_this_tick.add(relationship_key)
                
                affinity = self.compatibility.calculate_compatibility(person, other)
                self.logger.info(
                    "👋 Día %.0f: Agente %s conoce a %s (distancia: %.1f, afinidad: %.2f)",
                    current_day, person.entity_id, other.entity_id, distance, affinity
                )

    def _are_orientations_compatible(
        self, 
        o1: SexualOrientation, 
        o2: SexualOrientation
    ) -> bool:
        """Verifica si dos orientaciones sexuales son compatibles."""
        tolerance = getattr(self.rel_cfg, 'orientation_tolerance', 1.5)
        diff = abs(o1.value - o2.value)
        
        # Heterosexual y homosexual puros no son compatibles
        if (o1 == SexualOrientation.HETEROSEXUAL and o2 == SexualOrientation.HOMOSEXUAL) or \
           (o1 == SexualOrientation.HOMOSEXUAL and o2 == SexualOrientation.HETEROSEXUAL):
            return False
        
        # Diferencia mayor a 6 + tolerancia no es compatible
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
        
        # Obtener rasgos de personalidad del owner
        sociability = getattr(owner.genome, 'sociability', 1.0) / 2.0
        temperament = getattr(owner.genome, 'temperament', 1.0) / 2.0
        
        # Primera impresión base: ligera curiosidad positiva
        base_valence = 0.2
        base_weight = 15.0
        
        # Modificadores por personalidad
        # Persona sociable tiene mejor primera impresión
        personality_modifier = 1.0 + (sociability * 0.3)
        
        # Persona con temperamento alto es más desconfiada inicialmente
        if temperament > 0.7:
            personality_modifier *= 0.8
        
        # Introducir un poco de azar
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