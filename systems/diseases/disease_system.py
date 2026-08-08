"""Módulo responsable de la gestión epidemiológica y evolución de patógenos.

Implementa un modelo de propagación espacial con fases de infección:
- Expuesto → Incubando → Contagioso → Sintomático → Recuperándose

FASE 0: Integración con el RelationshipExperienceEngine mediante eventos
ligeros compatibles para que las enfermedades y recuperaciones afecten 
las relaciones (cuidado, duelo, etc.) a través de recuerdos.

FASE 1: Progresión de infecciones, recuperación y mutación
FASE 2: Contagios locales con CARGA VIRAL ACUMULATIVA por sector
FASE 3: Brotes espontáneos (evaluados UNA VEZ por tick, no por agente)

CORRECCIONES APLICADAS:
- Alineado con el nuevo sistema de relaciones (Fases 0-4)
- Prioridad 9: Carga viral del sector acumulativa (no binaria)
- BUG CRÍTICO CORREGIDO: Brotes fuera del bucle de agentes
- Integración con memoria episódica (recuperaciones)
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
                
                # Riesgo de muerte por síntomas graves
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
                
                # Intento de recuperación
                if infection_state.phase in (InfectionPhase.RECOVERING, InfectionPhase.SYMPTOMATIC):
                    total_immunity = person.get_specific_immunity(pathogen)
                    daily_recovery_rate = (dis_cfg.base_recovery_chance * 3.0 * total_immunity) / max(0.1, pathogen.virulence)
                    recovery_chance = 1.0 - math.exp(-daily_recovery_rate * delta_days)
                    
                    if random.random() < recovery_chance:
                        pending.register_recovery(person.entity_id, path_id)
                        self._notify_recovery_care(person, state, pending, current_day, pathogen)
                        
                        # Memoria episódica de la recuperación
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
                
                # Contribuir a la carga viral del sector si es contagioso
                if infection_state.is_contagious():
                    sector = (person.x // sector_size, person.y // sector_size)
                    effective_transmission = pathogen.transmission * infection_state.get_transmission_multiplier()
                    pathogen_map[sector].append((pathogen, effective_transmission))
                
                # Intento de mutación
                if infection_state.phase in (InfectionPhase.CONTAGIOUS, InfectionPhase.SYMPTOMATIC):
                    mutation_chance = 0.005 * delta_days
                    if random.random() < mutation_chance:
                        new_variant = pathogen.mutate()
                        
                        # Verificar que la nueva variante no esté ya activa
                        if new_variant.pathogen_id not in person.active_infections:
                            # Marcar las variantes antiguas para recuperación
                            for old_path_id in list(person.active_infections.keys()):
                                if old_path_id.startswith(f"{pathogen.family}_") and old_path_id != new_variant.pathogen_id:
                                    pending.register_recovery(person.entity_id, old_path_id)
                            
                            # Registrar la nueva variante
                            pending.register_infection(person.entity_id, new_variant)

        # =================================================================
        # FASE 2: CONTAGIOS LOCALES (CARGA VIRAL ACUMULADA)
        # =================================================================
        
        # 1. Calcular carga viral total por sector
        sector_viral_load: Dict[tuple, float] = defaultdict(float)
        sector_pathogens: Dict[tuple, list] = defaultdict(list)
        
        for sector, pathogens in pathogen_map.items():
            sector_pathogens[sector] = [p for p, _ in pathogens]
            for _, effective_transmission in pathogens:
                sector_viral_load[sector] += effective_transmission

        # 2. Evaluar contagio para cada agente sano
        for person in state.get_all_persons():
            if person.entity_id in pending.deaths:
                continue
            if getattr(person, 'is_sick', False):
                continue
            
            sector = (person.x // sector_size, person.y // sector_size)
            viral_load = sector_viral_load.get(sector, 0.0)
            
            # Si no hay carga viral en el sector, no hay riesgo de contagio ambiental
            if viral_load <= 0.0:
                continue
            
            # Inmunidad innate base como defensa general
            base_innate_immunity = max(
                0.1, 
                person.genome.immunity - ((1.0 - person.emotions.get("energy", 1.0)) * 0.2)
            )
            crowding_pressure = context.get_local_pressure(person.x, person.y)
            immunity_factor = min(1.0, base_innate_immunity / 2.0)
            
            # La tasa de transmisión escala con la CARGA VIRAL TOTAL del sector
            base_rate = (viral_load * max(1.0, crowding_pressure)) / max(0.5, base_innate_immunity)
            daily_transmission_rate = base_rate * (1.0 - immunity_factor * 0.8)
            infection_chance = 1.0 - math.exp(-daily_transmission_rate * delta_days)
            
            if random.random() < infection_chance:
                # Seleccionar un patógeno aleatorio de los presentes en el sector
                local_p = sector_pathogens.get(sector, [])
                if local_p:
                    chosen_pathogen = random.choice(local_p)
                    # Verificar que no lo tenga ya (doble chequeo de seguridad)
                    if chosen_pathogen.pathogen_id not in person.active_infections:
                        pending.register_infection(person.entity_id, chosen_pathogen)

        # =================================================================
        # FASE 3: BROTES ESPONTÁNEOS (CORREGIDO: FUERA DEL BUCLE DE AGENTES)
        # =================================================================
        # Se evalúa UNA VEZ por tick para toda la población, no una vez por agente.
        
        outbreak_chance = 1.0 - math.exp(-(dis_cfg.base_outbreak_chance / 100.0) * delta_days)
        
        if random.random() < outbreak_chance:
            # Seleccionar un paciente cero aleatorio de entre todos los agentes vivos y sanos
            alive_and_healthy = [
                p for p in state.get_all_persons() 
                if p.entity_id not in pending.deaths 
                and not getattr(p, 'is_sick', False)
            ]
            
            if alive_and_healthy:
                patient_zero = random.choice(alive_and_healthy)
                
                # Crear un patógeno aleatorio
                pathogen_families = getattr(
                    dis_cfg, 
                    'pathogen_families', 
                    ["Influenza", "Coronavirus", "Poxvirus", "Bacteriofago_X"]
                )
                familia_random = random.choice(pathogen_families)
                patient_zero_virus = Pathogen.create_random_variant(familia_random)
                
                # Verificar que el paciente cero no esté ya infectado con esta familia
                already_infected = any(
                    inf_state.pathogen.family == patient_zero_virus.family 
                    for inf_state in patient_zero.active_infections.values()
                )
                
                # Verificar que no tenga ya una infección pendiente en este tick
                already_pending = any(
                    eid == patient_zero.entity_id 
                    for eid, _ in pending.infections
                )
                
                if not already_infected and not already_pending:
                    pending.register_infection(patient_zero.entity_id, patient_zero_virus)
                    
                    self.logger.info(
                        "🚨 Brote: %s en Agente %s (vir: %.2f, trans: %.2f, let: %.2f, inc: %.1fd, asym: %.2f)",
                        patient_zero_virus.pathogen_id, 
                        patient_zero.entity_id,
                        patient_zero_virus.virulence, 
                        patient_zero_virus.transmission,
                        patient_zero_virus.lethality, 
                        patient_zero_virus.incubation_days,
                        patient_zero_virus.asymptomatic_chance,
                    )

    # =========================================================================
    # INTEGRACIÓN CON RELATIONSHIP EXPERIENCE ENGINE (FASE 0 + CORRECCIONES)
    # =========================================================================

    def _notify_recovery_care(
        self, 
        patient: Any, 
        state: WorldState, 
        pending: PendingChanges, 
        current_day: float, 
        pathogen: Any
    ) -> None:
        """Notifica al motor de relaciones que un agente se recuperó, generando eventos de cuidado."""
        if not self.relationship_engine:
            return

        for rel in patient._relationships:
            if getattr(rel, 'status', None) in (
                RelationshipStatus.DATING, 
                RelationshipStatus.COHABITATION, 
                RelationshipStatus.CONSOLIDATED
            ):
                partner = state.get_person_by_id(rel.partner_id)
                if partner and partner.entity_id not in pending.deaths:
                    distance = math.hypot(patient.x - partner.x, patient.y - partner.y)
                    if distance < 15.0:
                        # Calcular intensidad basada en la fuerza real de la relación
                        rel_strength = sum(m.current_weight(current_day) for m in rel.memories)
                        base_intensity = min(1.0, 0.4 + (pathogen.virulence * 0.5))
                        relationship_bonus = min(0.3, rel_strength * 0.001)
                        intensity = min(1.0, base_intensity + relationship_bonus)
                        
                        # Contexto rico que el BiasEngine pueda reconocer
                        context = "cuidado_enfermedad" if rel_strength > 100 else f"recuperacion_de_{pathogen.pathogen_id}"
                        
                        event_care = _DiseaseRelationalEvent(
                            event_type=RelationshipEventType.CARE,
                            intensity=intensity,
                            context=context,
                        )
                        self.relationship_engine.process_event(event_care, partner, patient, current_day)

    def _notify_partner_death(
        self, 
        deceased: Any, 
        state: WorldState, 
        pending: PendingChanges, 
        current_day: float
    ) -> None:
        """Notifica a las relaciones cercanas sobre la muerte de un agente."""
        if not self.relationship_engine:
            return

        for rel in deceased._relationships:
            if getattr(rel, 'status', None) != RelationshipStatus.EX_PARTNER:
                survivor = state.get_person_by_id(rel.partner_id)
                if survivor and survivor.entity_id not in pending.deaths:
                    rel_strength = sum(m.current_weight(current_day) for m in rel.memories)
                    
                    base_intensity = 0.5
                    relationship_bonus = min(0.5, rel_strength * 0.002)
                    intensity = min(1.0, base_intensity + relationship_bonus)
                    
                    if rel_strength > 200:
                        context = "perdida_de_ser_querido"
                    elif rel_strength > 100:
                        context = "duelo_profundo"
                    else:
                        context = "fallecimiento"
                    
                    event_death = _DiseaseRelationalEvent(
                        event_type=RelationshipEventType.PARTNER_DEATH,
                        intensity=intensity,
                        context=context,
                    )
                    self.relationship_engine.process_event(event_death, survivor, deceased, current_day)