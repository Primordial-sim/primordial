"""Módulo que define el motor probabilístico de mortalidad del ecosistema.

Implementa un modelo de Gompertz-Makeham expandido, evaluando no solo el 
desgaste biológico, sino también la energía disponible, el estrés psicológico,
la presión del entorno ambiental, el historial médico de la entidad, el
trauma por abandono en huérfanos sin tutela, y la letalidad de las infecciones
activas.

CORRECCIONES APLICADAS (Auditoría):
- Uso de Pathogen.lethality * Pathogen.virulence por cada infección activa
- Presión ambiental ajustada (exceso sobre 1.0)
- Diagnóstico enriquecido con patógeno específico
- Integración con recursos del entorno (hambre/inanición)
- Efecto de consanguinidad (endogamia) en mortalidad infantil

BLOQUE 3: Trauma Global Sistémico
- Factor de red familiar (efecto protector)
- Factor de reputación social
- Evaluación explícita de trauma_adoption
"""

import random
import math
import logging
from dataclasses import dataclass
from typing import Any, Optional

from systems.environment.environment_context import EnvironmentContext
from core.state.world_state import WorldState
from core.state.pending_changes import PendingChanges
from core.config.simulation_config import SimulationConfig

from systems.relationships.relationship_model import RelationshipEventType, RelationshipStatus
from systems.relationships.relationship_experience_engine import RelationshipExperienceEngine


@dataclass
class _MortalityRelationalEvent:
    """Evento ligero compatible con el RelationshipExperienceEngine de la Fase 0."""
    event_type: RelationshipEventType
    intensity: float
    context: str


class MortalitySystem:
    """Motor de mortalidad multifactorial con diagnósticos detallados."""

    def __init__(
        self, 
        config: SimulationConfig,
        relationship_engine: Optional[RelationshipExperienceEngine] = None,
        ancestry_queries: Any = None,
    ) -> None:
        self.config = config
        self.relationship_engine = relationship_engine
        self.ancestry_queries = ancestry_queries  # CORRECCIÓN: Para endogamia
        self.logger = logging.getLogger(self.__class__.__name__)

    def _calculate_multifactorial_risk(self, person: Any, pressure: float) -> float:
        """Calcula la probabilidad diaria de fallecimiento (Hazard Rate) holística.
        
        CORRECCIONES:
        - Uso de lethality * virulence por cada patógeno activo
        - Presión ambiental como exceso sobre 1.0
        - Integración con recursos del entorno
        """
        mortality_cfg = self.config.mortality
        adoptions_cfg = self.config.adoptions
        time_cfg = self.config.time
        
        # 1. RIESGO BASE POR SENESCENCIA (Gompertz)
        adjusted_beta_years = mortality_cfg.beta_base / max(mortality_cfg.genome_clamping, person.genome.longevity)
        adjusted_beta_days = adjusted_beta_years / time_cfg.days_per_year
        base_hazard = (mortality_cfg.alpha_base * math.exp(adjusted_beta_days * person.age)) / time_cfg.days_per_year
        
        # 2. PENALIZACIONES FENOTÍPICAS
        energy_level = person.emotions.get("energy", 1.0)
        energy_penalty = 1.0 + ((1.0 - energy_level) * 5.0)
        
        stress_level = person.emotions.get("stress", 0.0)
        stress_penalty = 1.0 + (stress_level * 2.0)
        
        trauma_overcrowding = person.memory.get("trauma_overcrowding", 0.0)
        trauma_penalty = 1.0 + (trauma_overcrowding * 3.0)

        abandonment_trauma = person.memory.get("trauma_abandonment", 0.0)
        abandonment_penalty = 1.0 + (abandonment_trauma * (adoptions_cfg.abandonment_mortality_multiplier - 1.0))
        
        # BLOQUE 3: Trauma de adopción
        adoption_trauma = person.memory.get("trauma_adoption", 0.0)
        adoption_penalty = 1.0 + (adoption_trauma * 0.5)

        # 3. CORRECCIÓN: PENALIZACIÓN AMBIENTAL (exceso sobre 1.0, no valor absoluto)
        excess_pressure = max(0.0, pressure - 1.0)
        environmental_penalty = 1.0 + (excess_pressure * mortality_cfg.density_penalty_multiplier)
        
        # 4. CORRECCIÓN: PENALIZACIÓN POR ENFERMEDADES ACTIVAS (usando lethality y virulence)
        sickness_penalty = 1.0
        if getattr(person, 'is_sick', False):
            total_infection_risk = 0.0
            for pathogen in person.active_pathogens.values():
                # CORRECCIÓN: Cada patógeno contribuye con su lethality * virulence
                infection_risk = pathogen.lethality * pathogen.virulence
                total_infection_risk += infection_risk
            
            raw_sickness_penalty = mortality_cfg.sickness_penalty_multiplier * (1.0 + total_infection_risk)
            sickness_penalty = max(mortality_cfg.min_sickness_penalty, raw_sickness_penalty)
            
        # ==========================================
        # BLOQUE 3: FACTORES DE PROTECCIÓN SOCIAL
        # ==========================================
        social_protection = 1.0
        has_parents = len(person.parents) > 0 or len(person.adoptive_parents) > 0
        has_children = person.children_count > 0
        
        if has_parents or has_children:
            reputation = getattr(person, 'reputation_score', 0.5)
            protection_factor = 0.2 * reputation 
            social_protection = max(0.8, 1.0 - protection_factor)
            
        reputation = getattr(person, 'reputation_score', 0.5)
        reputation_penalty = 1.0 + ((1.0 - reputation) * 0.3)
        
        # CORRECCIÓN: PENALIZACIÓN POR ENDGAMIA (consanguinidad)
        inbreeding_penalty = 1.0
        if self.ancestry_queries and person.age < 365.0:  # Solo en el primer año de vida
            inbreeding_risk = self.ancestry_queries.analyze_inbreeding_risk(person.entity_id)
            if inbreeding_risk > 0.1:
                inbreeding_penalty = 1.0 + (inbreeding_risk * 2.0)
            
        total_daily_risk = (
            base_hazard * 
            energy_penalty * 
            stress_penalty * 
            trauma_penalty * 
            abandonment_penalty * 
            adoption_penalty *
            environmental_penalty * 
            sickness_penalty *
            social_protection *
            reputation_penalty *
            inbreeding_penalty
        )
            
        return total_daily_risk

    def _diagnose_cause_of_death(self, person: Any, pressure: float) -> str:
        """Realiza una autopsia analítica para determinar la causa forense principal.
        
        CORRECCIÓN: Enriquecido con información específica del patógeno activo.
        """
        energy = person.emotions.get("energy", 1.0)
        stress = person.emotions.get("stress", 0.0)
        trauma_overcrowding = person.memory.get("trauma_overcrowding", 0.0)
        abandonment_trauma = person.memory.get("trauma_abandonment", 0.0)
        adoption_trauma = person.memory.get("trauma_adoption", 0.0)
        is_sick = getattr(person, 'is_sick', False)
        reputation = getattr(person, 'reputation_score', 0.5)

        # CORRECCIÓN: Identificar el patógeno más letal activo
        if is_sick and hasattr(person, 'active_pathogens') and person.active_pathogens:
            # Encontrar el patógeno con mayor lethality * virulence
            worst_pathogen = max(
                person.active_pathogens.values(),
                key=lambda p: p.lethality * p.virulence,
                default=None
            )
            
            if worst_pathogen and energy < 0.2:
                return f"Sepsis / Fallo multiorgánico por {worst_pathogen.pathogen_id}"
            if worst_pathogen:
                return f"Infección letal por {worst_pathogen.pathogen_id} (let: {worst_pathogen.lethality:.2f})"
        
        if energy < 0.1:
            return "Agotamiento metabólico extremo (Inanición)"
        if trauma_overcrowding > 0.8 or pressure > 2.0:
            return "Asfixia/Traumatismo severo por hacinamiento"
        if abandonment_trauma > 0.7 and stress > 0.8:
            return "Colapso sistémico por abandono prolongado"
        if adoption_trauma > 0.8 and stress > 0.7:
            return "Fallo cardíaco por trauma de reubicación forzada"
        if reputation < 0.2 and stress > 0.7:
            return "Muerte por aislamiento social severo y desnutrición"
        if stress > 0.85:
            return "Colapso cardiovascular inducido por estrés crónico"

        return "Fallo sistémico por senectud (Causas naturales)"

    def _notify_partner_death(self, deceased: Any, state: WorldState, pending: PendingChanges, current_day: float) -> None:
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
                    
                    event_death = _MortalityRelationalEvent(
                        event_type=RelationshipEventType.PARTNER_DEATH,
                        intensity=intensity,
                        context=context,
                    )
                    self.relationship_engine.process_event(event_death, survivor, deceased, current_day)

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Procesa el ciclo estocástico de mortalidad para todos los agentes activos."""
        mortality_cfg = self.config.mortality
        current_day = getattr(state, 'world_days_elapsed', 0.0)

        for person in state.get_all_persons():
            if person.entity_id in pending.deaths:
                continue
            
            # 1. SELECCIÓN NATURAL ESTRICTA (Límite Biológico Determinista)
            adjusted_cap = mortality_cfg.hard_cap_age_days * person.genome.longevity
            if person.age >= adjusted_cap:
                pending.register_death(person.entity_id, reason="Degradación telomérica total (Límite biológico)")
                self.logger.debug(f"Muerte natural absoluta (Límite): Agente {person.entity_id}")
                self._notify_partner_death(person, state, pending, current_day)
                continue

            # 2. RIESGO PROBABILÍSTICO
            pressure = context.get_local_pressure(person.x, person.y)
            daily_rate = self._calculate_multifactorial_risk(person, pressure)
            total_death_chance = 1.0 - math.exp(-daily_rate * delta_days)

            if random.random() < total_death_chance:
                reason = self._diagnose_cause_of_death(person, pressure)
                pending.register_death(person.entity_id, reason=reason)
                self._notify_partner_death(person, state, pending, current_day)