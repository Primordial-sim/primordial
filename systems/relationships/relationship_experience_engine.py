"""Motor de experiencias relacionales. Fase 1: Cognición y Sesgos.

Traduce eventos del mundo en recuerdos personales asimétricos,
modulados por la personalidad, el contexto, los objetivos y los sesgos cognitivos.
"""

from __future__ import annotations

import logging
import random
from typing import Any, Optional

from core.config.simulation_config import SimulationConfig
from systems.relationships.relationship_model import (
    RelationshipEventType,
    MemoryCategory,
    MemoryRole,
    PersonalMemory,
    WorldEvent,
    BiasEngine,
    GoalFilter,
)


class RelationshipExperienceEngine:
    """Procesa eventos y genera recuerdos personales con sesgos cognitivos."""

    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.event_profiles = {
            RelationshipEventType.CARE: {"category": MemoryCategory.COOPERATION, "base_weight": 40.0},
            RelationshipEventType.COOPERATION: {"category": MemoryCategory.COOPERATION, "base_weight": 30.0},
            RelationshipEventType.INTIMACY: {"category": MemoryCategory.ROMANTIC, "base_weight": 50.0},
            RelationshipEventType.CONFLICT: {"category": MemoryCategory.CONFLICT, "base_weight": 45.0},
            RelationshipEventType.BETRAYAL: {"category": MemoryCategory.CONFLICT, "base_weight": 80.0},
            RelationshipEventType.BIRTH: {"category": MemoryCategory.FAMILY, "base_weight": 90.0},
            RelationshipEventType.PARTNER_DEATH: {"category": MemoryCategory.TRAUMA, "base_weight": 95.0},
            RelationshipEventType.MET: {"category": MemoryCategory.SOCIAL, "base_weight": 15.0},
        }

    def process_event(
        self,
        event: Any,
        agent_a: Any,
        agent_b: Optional[Any],
        current_day: float,
    ) -> None:
        """Procesa un evento y crea recuerdos asimétricos para A y B."""
        if agent_b is None:
            return

        if hasattr(event, 'event_type'):
            event_type = event.event_type
            intensity = getattr(event, 'intensity', 0.5)
            context = getattr(event, 'context', 'general')
        else:
            event_type = RelationshipEventType.MET
            intensity = 0.5
            context = 'general'

        profile = self.event_profiles.get(event_type, {"category": MemoryCategory.SOCIAL, "base_weight": 20.0})
        
        world_event = WorldEvent(
            event_id=id(event) if hasattr(event, '__hash__') else random.randint(10000, 99999),
            event_type=event_type.value if hasattr(event_type, 'value') else str(event_type),
            category=profile["category"],
            day=current_day,
            context=context,
            source_system="RelationshipExperienceEngine",
            initiator_id=agent_a.entity_id,
            target_id=agent_b.entity_id,
            objective_intensity=intensity,
        )

        # FASE 1: La creación es asimétrica. Cada agente procesa el evento a través de sus propios lentes.
        mem_a = self._create_personal_memory(world_event, agent_a, agent_b, profile["base_weight"], current_day)
        mem_b = self._create_personal_memory(world_event, agent_b, agent_a, profile["base_weight"], current_day)

        rel_a = agent_a.get_relationship_with(agent_b.entity_id, current_day)
        rel_a.add_memory(mem_a)

        rel_b = agent_b.get_relationship_with(agent_a.entity_id, current_day)
        rel_b.add_memory(mem_b)

        self.logger.info(
            "🧠 Experiencia: Agente %s y %s | Evento: %s | Peso A: %.1f | Peso B: %.1f",
            agent_a.entity_id, agent_b.entity_id, world_event.event_type,
            mem_a.personal_weight, mem_b.personal_weight
        )

    def _create_personal_memory(
        self,
        world_event: WorldEvent,
        owner: Any,
        partner: Any,
        base_weight: float,
        current_day: float,
    ) -> PersonalMemory:
        """Crea la interpretación subjetiva de un evento, aplicando sesgos y objetivos."""
        
        # 1. Cálculo base de personalidad (Fase 0)
        sociability = getattr(owner.genome, 'sociability', 1.0) / 2.0
        independence = getattr(owner, 'motivations', {}).get('independence', 0.5) if hasattr(owner, 'motivations') else 0.5
        temperament = getattr(owner.genome, 'temperament', 1.0) / 2.0
        
        valence = 1.0 if world_event.category in (MemoryCategory.COOPERATION, MemoryCategory.ROMANTIC, MemoryCategory.FAMILY) else -1.0
        personality_modifier = 1.0
        
        if world_event.event_type == "care":
            personality_modifier *= (1.0 - (independence * 0.5)) * (1.0 + (sociability * 0.3))
        elif world_event.event_type == "betrayal":
            personality_modifier *= (1.0 + (temperament * 0.5))
        elif world_event.event_type == "birth":
            if world_event.initiator_id == owner.entity_id or world_event.target_id == owner.entity_id:
                personality_modifier *= (1.0 + ((1.0 - independence) * 0.4))

        uncertainty = random.gauss(1.0, 0.15)
        initial_weight = base_weight * world_event.objective_intensity * personality_modifier * uncertainty
        
        # 2. Crear el recuerdo temporal (necesario antes de aplicar filtros)
        temp_memory = PersonalMemory(
            world_event_id=world_event.event_id,
            owner_id=owner.entity_id,
            partner_id=partner.entity_id,
            perceived_intensity=world_event.objective_intensity,
            emotional_valence=valence,
            personal_weight=initial_weight,
            category=world_event.category,
            day=world_event.day,
            context=world_event.context,
            event_type=world_event.event_type,
            source_system=world_event.source_system,
            role=MemoryRole.NORMAL,
            half_life_days=self._get_half_life(world_event.event_type),
        )

        # 3. FASE 1: Aplicar Filtro de Objetivos (GoalFilter)
        #     Ahora pasamos temp_memory (PersonalMemory) en vez de world_event (WorldEvent)
        rel = owner.get_relationship_with(partner.entity_id, current_day)
        goal_multiplier = 1.0
        if hasattr(rel.knowledge, 'owner_goals') and rel.knowledge.owner_goals:
            max_relevance = max(
                (GoalFilter.relevance(goal, temp_memory) for goal in rel.knowledge.owner_goals),
                default=1.0
            )
            goal_multiplier = max_relevance

        temp_memory.personal_weight = initial_weight * goal_multiplier

        # 4. FASE 1: Aplicar Motor de Sesgos (BiasEngine)
        final_weight = BiasEngine.apply_biases(temp_memory, owner, rel, current_day)
        temp_memory.personal_weight = max(0.0, final_weight)
        
        # 5. Determinar rol especial
        if world_event.event_type in ["betrayal", "partner_death", "child_death"]:
            temp_memory.role = MemoryRole.TRAUMA
        elif world_event.event_type in ["birth", "marriage", "cohabitation_start"]:
            temp_memory.role = MemoryRole.ANCHOR

        return temp_memory

    def _get_half_life(self, event_type: str) -> float:
        half_lives = {
            "met": 30.0, "care": 180.0, "cooperation": 180.0, "intimacy": 365.0,
            "conflict": 240.0, "betrayal": 1000.0, "birth": float('inf'), "partner_death": float('inf'),
        }
        return half_lives.get(event_type, 90.0)