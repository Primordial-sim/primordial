"""Módulo que define el motor probabilístico de mortalidad del ecosistema.

Implementa un modelo de Gompertz-Makeham expandido, evaluando no solo el 
desgaste biológico, sino también la energía disponible, el estrés psicológico,
la presión del entorno ambiental, el historial médico de la entidad, el
trauma por abandono en huérfanos sin tutela, y la letalidad de las infecciones
activas.

FASE 0: Integración con RelationshipExperienceEngine para emitir eventos de
PARTNER_DEATH cuando un agente fallece, generando recuerdos de duelo en sus 
seres queridos.
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

# FASE 0: Solo importamos el tipo de evento y el estado legacy para compatibilidad
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
    ) -> None:
        """Inicializa el sistema vinculándolo a la configuración centralizada."""
        self.config = config
        self.relationship_engine = relationship_engine
        self.logger = logging.getLogger(self.__class__.__name__)

    def _calculate_multifactorial_risk(self, person: Any, pressure: float) -> float:
        """Calcula la probabilidad diaria de fallecimiento (Hazard Rate) holística."""
        mortality_cfg = self.config.mortality
        adoptions_cfg = self.config.adoptions
        time_cfg = self.config.time
        
        # 1. RIESGO BASE POR SENESCENCIA
        adjusted_beta_years = mortality_cfg.beta_base / max(mortality_cfg.genome_clamping, person.genome.longevity)
        adjusted_beta_days = adjusted_beta_years / time_cfg.days_per_year
        base_hazard = (mortality_cfg.alpha_base * math.exp(adjusted_beta_days * person.age)) / time_cfg.days_per_year
        
        # 2. PENALIZACIONES FENOTÍPICAS
        energy_level = person.emotions.get("energy", 1.0)
        energy_penalty = 1.0 + ((1.0 - energy_level) * 5.0)
        
        stress_level = person.emotions.get("stress", 0.0)
        stress_penalty = 1.0 + (stress_level * 2.0)
        
        trauma_level = person.memory.get("trauma_overcrowding", 0.0)
        trauma_penalty = 1.0 + (trauma_level * 3.0)

        abandonment_trauma = person.memory.get("trauma_abandonment", 0.0)
        abandonment_penalty = 1.0 + (abandonment_trauma * (adoptions_cfg.abandonment_mortality_multiplier - 1.0))

        # 3. PENALIZACIONES EXTERNAS
        environmental_penalty = 1.0 + (pressure * mortality_cfg.density_penalty_multiplier)
        
        # 4. PENALIZACIÓN POR ENFERMEDADES ACTIVAS
        sickness_penalty = 1.0
        if getattr(person, 'is_sick', False):
            total_infection_risk = 0.0
            for pathogen in person.active_pathogens.values():
                infection_risk = pathogen.lethality * pathogen.virulence
                total_infection_risk += infection_risk
            
            raw_sickness_penalty = mortality_cfg.sickness_penalty_multiplier * (1.0 + total_infection_risk)
            sickness_penalty = max(mortality_cfg.min_sickness_penalty, raw_sickness_penalty)
            
        total_daily_risk = (
            base_hazard * energy_penalty * stress_penalty * trauma_penalty * 
            abandonment_penalty * environmental_penalty * sickness_penalty
        )
            
        return total_daily_risk

    def _diagnose_cause_of_death(self, person: Any, pressure: float) -> str:
        """Realiza una autopsia analítica para determinar la causa forense principal."""
        energy = person.emotions.get("energy", 1.0)
        stress = person.emotions.get("stress", 0.0)
        trauma = person.memory.get("trauma_overcrowding", 0.0)
        abandonment_trauma = person.memory.get("trauma_abandonment", 0.0)
        is_sick = getattr(person, 'is_sick', False)

        if is_sick and energy < 0.2:
            return "Sepsis / Fallo multiorgánico por agotamiento"
        if energy < 0.1:
            return "Agotamiento metabólico extremo (Inanición)"
        if is_sick:
            return "Infección letal aguda"
        if trauma > 0.8 or pressure > 2.0:
            return "Asfixia/Traumatismo severo por hacinamiento"
        if abandonment_trauma > 0.7 and stress > 0.8:
            return "Colapso sistémico por abandono prolongado"
        if stress > 0.85:
            return "Colapso cardiovascular inducido por estrés crónico"

        return "Fallo sistémico por senectud (Causas naturales)"

    def _notify_partner_death(self, deceased: Any, state: WorldState, pending: PendingChanges, current_day: float) -> None:
        """Notifica a las relaciones cercanas sobre la muerte de un agente."""
        if not self.relationship_engine:
            return

        for rel in getattr(deceased, 'relationships', []):
            # Usamos getattr para compatibilidad con el campo legacy 'status' de la Fase 0
            if getattr(rel, 'status', None) != RelationshipStatus.EX_PARTNER:
                survivor = state.get_person_by_id(rel.partner_id)
                if survivor and survivor.entity_id not in pending.deaths:
                    # El apego modula la intensidad del duelo
                    attachment = getattr(rel, 'attachment', 50.0)
                    intensity = min(1.0, 0.5 + (attachment / 100.0) * 0.5)
                    
                    event_death = _MortalityRelationalEvent(
                        event_type=RelationshipEventType.PARTNER_DEATH,
                        intensity=intensity,
                        context="fallecimiento",
                    )
                    # agent_a es el sobreviviente, agent_b es el fallecido
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