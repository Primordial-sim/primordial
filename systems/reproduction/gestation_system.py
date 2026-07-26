"""Módulo responsable del avance de la gestación y partos múltiples dentro de la simulación.

Este sistema controla los ciclos biológicos de preñez de las distintas especies,
evalúa el progreso temporal de los embarazos y ejecuta los partos consolidando
la herencia genética a través del motor evolutivo.

FASE 0: Integra con RelationshipExperienceEngine emitiendo eventos ligeros
compatibles para fortalecer el vínculo entre los padres mediante recuerdos.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext
from systems.evolution.evolution_engine import EvolutionEngine

# FASE 0: Solo importamos el tipo de evento, no la clase antigua RelationshipEvent
from systems.relationships.relationship_model import RelationshipEventType
from systems.relationships.relationship_experience_engine import RelationshipExperienceEngine


@dataclass
class _GestationRelationalEvent:
    """Evento ligero compatible con el RelationshipExperienceEngine de la Fase 0."""
    event_type: RelationshipEventType
    intensity: float
    context: str


class GestationSystem:
    """Gestiona el tiempo de gestación y la ejecución de partos múltiples (camadas)."""

    def __init__(
        self,
        config: SimulationConfig,
        evolution_engine: EvolutionEngine,
        relationship_engine: Optional[RelationshipExperienceEngine] = None,
    ) -> None:
        """Inicializa el sistema de gestación orquestando sus dependencias."""
        self.config = config
        self.evolution_engine = evolution_engine
        self.relationship_engine = relationship_engine
        self.logger = logging.getLogger(self.__class__.__name__)

    def _get_species_traits(self, species: str) -> dict[str, float]:
        """Recupera el perfil reproductivo local y específico de una especie."""
        profiles = {
            "human": {"gestation_days": float(self.config.reproduction.pregnancy_duration_days)},
            "elf": {"gestation_days": 730.0},
            "goblin": {"gestation_days": 120.0},
            "dragon": {"gestation_days": 1200.0}
        }
        return profiles.get(species, profiles["human"])

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Avanza los embarazos activos y dispara los nacimientos múltiples (camadas)."""
        current_day = getattr(state, 'world_days_elapsed', 0.0)

        for person in state.get_all_persons():
            if person.entity_id in pending.deaths or not getattr(person, "is_pregnant", False):
                continue

            traits = self._get_species_traits(person.species)
            current_days = getattr(person, "pregnancy_days", 0.0)
            new_days = current_days + delta_days

            if new_days >= traits["gestation_days"]:
                litter_size = getattr(person, "litter_size_gestating", 1)

                for _ in range(litter_size):
                    self._execute_birth(person, state, pending, current_day)

                pending.register_pregnancy_update(
                    person.entity_id,
                    is_pregnant=False,
                    pregnancy_days=0.0,
                    failed_increment=0,
                    litter_size=1,
                )
            else:
                pending.register_pregnancy_update(
                    person.entity_id,
                    is_pregnant=True,
                    pregnancy_days=new_days,
                    failed_increment=0,
                    litter_size=person.litter_size_gestating,
                )

    def _execute_birth(
        self,
        mother: Any,
        state: WorldState,
        pending: PendingChanges,
        current_day: float,
    ) -> None:
        """Culmina la meiosis individual de una sola cría de la camada."""
        partner = state.get_person_by_id(mother.partner_id) if mother.partner_id else None

        father_genome = partner.genome if partner else None
        baby_genome = mother.genome.combine(father_genome)

        pending.register_birth(
            mother_id=mother.entity_id,
            father_id=mother.partner_id,
            genome=baby_genome,
            x=mother.x,
            y=mother.y,
        )
        
        # FASE 0: Emitir evento relacional de nacimiento usando la clase compatible
        if self.relationship_engine is not None and partner is not None:
            birth_event = _GestationRelationalEvent(
                event_type=RelationshipEventType.BIRTH,
                intensity=0.8,
                context="nacimiento",
            )
            self.relationship_engine.process_event(birth_event, mother, partner, current_day)

        self.logger.info(
            "👶 [NACIMIENTO] Madre %s dio a luz (Especie: %s)",
            mother.entity_id,
            mother.species,
        )