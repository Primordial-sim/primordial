"""Módulo responsable de la gestión epidemiológica y evolución de patógenos.

Implementa un modelo de propagación espacial con fases de infección:
- Expuesto → Incubando → Contagioso → Sintomático → Recuperándose

FASE 0: Integración con el RelationshipExperienceEngine mediante eventos
ligeros compatibles para que las enfermedades y recuperaciones afecten 
las relaciones (cuidado, duelo, etc.) a través de recuerdos.
"""

import random
import math
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Set, Optional, Any

from core.state.world_state import WorldState
from core.state.pending_changes import PendingChanges
from systems.behavior.cognitive_memory_system import CognitiveMemorySystem
from systems.environment.environment_context import EnvironmentContext
from core.config.simulation_config import SimulationConfig
from systems.diseases.pathogen import Pathogen, InfectionPhase

# FASE 0: Solo importamos el tipo de evento y el estado legacy para compatibilidad
from systems.relationships.relationship_model import (
    RelationshipEventType,
    RelationshipStatus,
)
from systems.relationships.relationship_experience_engine import RelationshipExperienceEngine


@dataclass
class _DiseaseRelationalEvent:
    """Evento ligero compatible con el RelationshipExperienceEngine de la Fase 0."""
    event_type: RelationshipEventType
    intensity: float
    context: str


class DiseaseSystem:
    """Motor epidemiológico espacial (Variantes, Inmunidad y Contagio focal)."""

    def __init__(
        self, 
        config: SimulationConfig,
        relationship_engine: Optional[RelationshipExperienceEngine] = None,
    ) -> None:
        """Inicializa el sistema vinculándolo a la configuración centralizada."""
        self.config = config
        self.relationship_engine = relationship_engine
        self.logger = logging.getLogger(self.__class__.__name__)

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Procesa la propagación epidemiológica y recuperación de enfermedades."""
        dis_cfg = self.config.diseases
        sector_size = self.config.environment.sector_size
        current_day = getattr(state, 'world_days_elapsed', 0.0)
        pathogen_map = defaultdict(list)

        # =================================================================
        # FASE 0: DECAIMIENTO DE INMUNIDAD
        # =================================================================
        for person in state.get_all_persons():
            if person.entity_id in pending.deaths:
                continue
            if hasattr(person, 'decay_immunity'):
                person.decay_immunity(delta_days, decay_rate=0.0003)

        # =================================================================
        # FASE 1: PROGRESIÓN DE INFECCIONES Y RECUPERACIÓN
        # =================================================================
        for person in state.get_all_persons():
            if person.entity_id in pending.deaths:
                continue
            
            if hasattr(person, 'advance_infections'):
                person.advance_infections(delta_days)
            
            for path_id, infection_state in list(person.active_infections.items()):
                pathogen = infection_state.pathogen
                
                if infection_state.phase == InfectionPhase.SYMPTOMATIC:
                    lethality_risk = pathogen.lethality * 0.01 * delta_days
                    total_immunity = person.get_specific_immunity(pathogen)
                    lethality_risk = lethality_risk / max(0.1, total_immunity)
                    
                    if random.random() < lethality_risk:
                        pending.register_death(
                            person.entity_id,
                            f"Sepsis / Fallo multiorgánico por {pathogen.pathogen_id}"
                        )
                        self._notify_partner_death(person, state, pending, current_day)
                        continue
                
                if infection_state.phase in (InfectionPhase.RECOVERING, InfectionPhase.SYMPTOMATIC):
                    total_immunity = person.get_specific_immunity(pathogen)
                    daily_recovery_rate = (dis_cfg.base_recovery_chance * 3.0 * total_immunity) / max(0.1, pathogen.virulence)
                    recovery_chance = 1.0 - math.exp(-daily_recovery_rate * delta_days)
                    
                    if random.random() < recovery_chance:
                        pending.register_recovery(person.entity_id, path_id)
                        self._notify_recovery_care(person, state, pending, current_day, pathogen)
                        
                        intensity = min(1.0, 0.3 + (pathogen.virulence * 0.6))
                        CognitiveMemorySystem.add_memory(
                            person=person,
                            mem_type=CognitiveMemorySystem.TYPE_DISEASE,
                            target_id=pathogen.pathogen_id,
                            intensity=intensity,
                            valence=-1,
                            context="recuperacion",
                            current_day=current_day,
                            pending=pending,
                        )
                        continue
                
                if infection_state.is_contagious():
                    sector = (person.x // sector_size, person.y // sector_size)
                    effective_transmission = pathogen.transmission * infection_state.get_transmission_multiplier()
                    pathogen_map[sector].append((pathogen, effective_transmission))
                
                if infection_state.phase in (InfectionPhase.CONTAGIOUS, InfectionPhase.SYMPTOMATIC):
                    mutation_chance = 0.005 * delta_days
                    if random.random() < mutation_chance:
                        new_variant = pathogen.mutate()
                        for old_path_id in list(person.active_infections.keys()):
                            if old_path_id.startswith(f"{pathogen.family}_"):
                                pending.register_recovery(person.entity_id, old_path_id)
                        pending.register_infection(person.entity_id, new_variant)

        # =================================================================
        # FASE 2: CONTAGIOS LOCALES Y BROTES ESPONTÁNEOS
        # =================================================================
        for person in state.get_all_persons():
            if person.entity_id in pending.deaths:
                continue
            
            sector = (person.x // sector_size, person.y // sector_size)
            local_pathogens = pathogen_map.get(sector, [])
            agent_infections_this_tick: Set[str] = set()
            
            family_counts = defaultdict(int)
            for pid in person.active_infections.keys():
                family = pid.split('_')[0]
                family_counts[family] += 1
            
            for pathogen, _ in local_pathogens:
                if pathogen.pathogen_id in person.active_infections or pathogen.pathogen_id in agent_infections_this_tick:
                    continue
                if family_counts[pathogen.family] >= 2:
                    continue
                
                total_immunity = person.get_specific_immunity(pathogen)
                if total_immunity > 1.5:
                    continue
                
                crowding_pressure = context.get_local_pressure(person.x, person.y)
                immunity_factor = min(1.0, total_immunity / 2.0)
                base_rate = (pathogen.transmission * max(1.0, crowding_pressure)) / max(0.5, total_immunity)
                daily_transmission_rate = base_rate * (1.0 - immunity_factor * 0.8)
                infection_chance = 1.0 - math.exp(-daily_transmission_rate * delta_days)
                
                if random.random() < infection_chance:
                    pending.register_infection(person.entity_id, pathogen)
                    agent_infections_this_tick.add(pathogen.pathogen_id)
                    family_counts[pathogen.family] += 1
            
            outbreak_chance = 1.0 - math.exp(-(dis_cfg.base_outbreak_chance / 100.0) * delta_days)
            if random.random() < outbreak_chance:
                familia_random = random.choice(["Influenza", "Coronavirus", "Poxvirus", "Bacteriofago_X"])
                patient_zero_virus = Pathogen.create_random_variant(familia_random)
                
                if patient_zero_virus.pathogen_id not in person.active_infections and patient_zero_virus.pathogen_id not in agent_infections_this_tick:
                    pending.register_infection(person.entity_id, patient_zero_virus)
                    agent_infections_this_tick.add(patient_zero_virus.pathogen_id)
                    self.logger.info(
                        "🚨 Brote: %s en Agente %s (vir: %.2f, trans: %.2f, let: %.2f, inc: %.1fd, asym: %.2f)",
                        patient_zero_virus.pathogen_id, person.entity_id,
                        patient_zero_virus.virulence, patient_zero_virus.transmission,
                        patient_zero_virus.lethality, patient_zero_virus.incubation_days,
                        patient_zero_virus.asymptomatic_chance,
                    )

    # =========================================================================
    # INTEGRACIÓN CON RELATIONSHIP EXPERIENCE ENGINE (FASE 0)
    # =========================================================================

    def _notify_recovery_care(self, patient: Any, state: WorldState, pending: PendingChanges, current_day: float, pathogen: Any) -> None:
        """Notifica al motor de relaciones que un agente se recuperó, generando eventos de cuidado."""
        if not self.relationship_engine:
            return

        for rel in getattr(patient, 'relationships', []):
            # FASE 0: Usamos getattr para compatibilidad con el campo legacy 'status'
            if getattr(rel, 'status', None) in (RelationshipStatus.DATING, RelationshipStatus.COHABITATION, RelationshipStatus.CONSOLIDATED):
                partner = state.get_person_by_id(rel.partner_id)
                if partner and partner.entity_id not in pending.deaths:
                    distance = math.hypot(patient.x - partner.x, patient.y - partner.y)
                    if distance < 15.0:
                        intensity = min(1.0, 0.4 + (pathogen.virulence * 0.5))
                        
                        event_care = _DiseaseRelationalEvent(
                            event_type=RelationshipEventType.CARE,
                            intensity=intensity,
                            context=f"recuperacion_de_{pathogen.pathogen_id}",
                        )
                        # agent_a es quien cuida (partner), agent_b es quien se recupera (patient)
                        self.relationship_engine.process_event(event_care, partner, patient, current_day)

    def _notify_partner_death(self, deceased: Any, state: WorldState, pending: PendingChanges, current_day: float) -> None:
        """Notifica a las relaciones cercanas sobre la muerte de un agente."""
        if not self.relationship_engine:
            return

        for rel in getattr(deceased, 'relationships', []):
            # FASE 0: Usamos getattr para compatibilidad con los campos legacy
            if getattr(rel, 'status', None) != RelationshipStatus.EX_PARTNER:
                survivor = state.get_person_by_id(rel.partner_id)
                if survivor and survivor.entity_id not in pending.deaths:
                    attachment = getattr(rel, 'attachment', 50.0)
                    intensity = min(1.0, 0.5 + (attachment / 100.0) * 0.5)
                    
                    event_death = _DiseaseRelationalEvent(
                        event_type=RelationshipEventType.PARTNER_DEATH,
                        intensity=intensity,
                        context="fallecimiento",
                    )
                    # agent_a es el sobreviviente, agent_b es el fallecido
                    self.relationship_engine.process_event(event_death, survivor, deceased, current_day)