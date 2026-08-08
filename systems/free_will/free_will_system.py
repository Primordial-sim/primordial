"""Módulo de Libre Albedrío implementado como Sistema de Motivaciones Continuas.

Este sistema reemplaza las antiguas banderas binarias por un modelo de motivaciones
continuas que evolucionan según genética, estado emocional, experiencias previas,
entorno, memoria episódica, enfermedades, edad y trauma sistémico.

RESUELVE TODOS LOS PUNTOS DE LA AUDITORÍA:
- Motivaciones continuas [0.0, 1.0] en lugar de flags binarios
- Decaimiento natural (los impulsos desaparecen si no se materializan)
- Continuidad psicológica vía genética y memoria episódica
- Inhibición competitiva (solo una motivación domina por tick)
- Aprendizaje desde memoria episódica
- Motivaciones definidas en configuración (escalable)

FASE 0: Integración con RelationshipExperienceEngine para emitir eventos
relacionales ligeros cuando los agentes toman decisiones que afectan a otros.
"""

from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.behavior.cognitive_memory_system import CognitiveMemorySystem
from systems.environment.environment_context import EnvironmentContext
from systems.relationships.behavior_influence import BehaviorInfluence
from systems.relationships.relationship_logger import relationship_logger

from systems.relationships.relationship_model import (
    RelationshipEventType,
    RelationshipStatus,
)
from systems.relationships.relationship_experience_engine import RelationshipExperienceEngine


@dataclass
class _FreeWillRelationalEvent:
    """Evento ligero compatible con el RelationshipExperienceEngine de la Fase 0."""
    event_type: RelationshipEventType
    intensity: float
    context: str


class FreeWillSystem:
    """Sistema de motivaciones continuas para comportamiento emergente."""

    def __init__(
        self, 
        config: SimulationConfig,
        relationship_engine: Optional[RelationshipExperienceEngine] = None,
    ) -> None:
        """Inicializa el sistema vinculándolo a la configuración centralizada."""
        self.config = config
        self.relationship_engine = relationship_engine
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self._action_cooldowns: Dict[int, Dict[str, float]] = {}

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Procesa la evolución de motivaciones y decisiones de todos los agentes."""
        fw_cfg = self.config.free_will
        current_day = getattr(state, 'world_days_elapsed', 0.0)
        
        for person in state.get_all_persons():
            if person.entity_id in pending.deaths:
                self._action_cooldowns.pop(person.entity_id, None)
                continue
            
            if not hasattr(person, '_motivations'):
                continue
            
            # 1. DECAIMIENTO NATURAL (resuelve "impulsos que nunca desaparecen")
            if hasattr(person, 'decay_motivations'):
                person.decay_motivations(delta_days, fw_cfg.motivation_decay_rate)
            
            # 2. CÁLCULO MULTIFACTORIAL DE AJUSTES
            genetic_motivations = self._calculate_genetic_motivations(person, fw_cfg)
            emotional_adjustments = self._calculate_emotional_adjustments(person, fw_cfg)
            environmental_adjustments = self._calculate_environmental_adjustments(person, context, fw_cfg)
            memory_adjustments = self._calculate_memory_adjustments(person, fw_cfg)
            sickness_adjustments = self._calculate_sickness_adjustments(person, fw_cfg)
            age_adjustments = self._calculate_age_adjustments(person, fw_cfg)
            systemic_adjustments = self._calculate_systemic_adjustments(person, fw_cfg)
            
            # 3. APLICAR AJUSTES A LAS MOTIVACIONES CONTINUAS
            for motivation_name in fw_cfg.motivations:
                base = genetic_motivations.get(motivation_name, 0.3)
                
                adjustment = (
                    emotional_adjustments.get(motivation_name, 0.0) +
                    environmental_adjustments.get(motivation_name, 0.0) +
                    memory_adjustments.get(motivation_name, 0.0) +
                    sickness_adjustments.get(motivation_name, 0.0) +
                    age_adjustments.get(motivation_name, 0.0) +
                    systemic_adjustments.get(motivation_name, 0.0)
                )
                
                target_value = max(0.0, min(1.0, base + adjustment))
                current_value = person.get_motivation(motivation_name)
                delta = target_value - current_value
                
                if abs(delta) > 0.01:
                    pending.register_motivation_update(person.entity_id, motivation_name, delta)
            
            # 4. INHIBICIÓN COMPETITIVA (solo una motivación domina)
            dominant_motivation, dominant_value = self._get_dominant_motivation(person, fw_cfg)
            action_threshold = self._get_action_threshold(dominant_motivation, fw_cfg)
            
            if dominant_value >= action_threshold:
                can_trigger = self._can_trigger_action(person.entity_id, dominant_motivation, current_day, fw_cfg)
                
                if can_trigger:
                    self.logger.debug(
                        "🎯 Agente %s: motivación dominante '%s' (%.2f) supera umbral",
                        person.entity_id, dominant_motivation, dominant_value,
                    )
                    
                    pending.register_memory_update(
                        person.entity_id,
                        "dominant_action",
                        {"motivation": dominant_motivation, "intensity": dominant_value, "tick": current_day},
                    )
                    
                    if self.relationship_engine:
                        self._emit_relationship_events(person, dominant_motivation, dominant_value, state, current_day)
                    
                    self._register_action(person.entity_id, dominant_motivation, current_day)
                    
                    # CONSUMO DE MOTIVACIÓN tras ejecutar la acción
                    consumption = self._get_motivation_consumption(dominant_motivation, fw_cfg)
                    if consumption > 0:
                        pending.register_motivation_update(person.entity_id, dominant_motivation, -consumption)
                else:
                    # Si no puede actuar por cooldown, la motivación se acumula (frustración)
                    consumption = self._get_motivation_consumption(dominant_motivation, fw_cfg) * 2.0
                    if consumption > 0:
                        pending.register_motivation_update(person.entity_id, dominant_motivation, -consumption)

    # =================================================================
    # CÁLCULOS DE AJUSTE MULTIFACTORIAL
    # =================================================================

    def _calculate_genetic_motivations(self, person: Any, fw_cfg: Any) -> Dict[str, float]:
        """Calcula la base genética de cada motivación usando rasgos del genoma."""
        genome = person.genome
        impulsivity = min(1.0, genome.impulsivity / 2.0)
        curiosity = min(1.0, genome.curiosity / 2.0)
        obedience = min(1.0, genome.obedience / 2.0)
        aggressiveness = min(1.0, genome.aggressiveness / 2.0)
        temperament = min(1.0, genome.temperament / 2.0)
        sociability = min(1.0, genome.sociability / 2.0)
        
        return {
            "independence": impulsivity * fw_cfg.impulsivity_weight + aggressiveness * fw_cfg.aggressiveness_weight * 0.5 + (1.0 - obedience) * fw_cfg.obedience_weight * 0.5,
            "exploration": curiosity * fw_cfg.curiosity_weight + impulsivity * fw_cfg.impulsivity_weight * 0.3,
            "rebellion": aggressiveness * fw_cfg.aggressiveness_weight + impulsivity * fw_cfg.impulsivity_weight * 0.5 + (1.0 - obedience) * fw_cfg.obedience_weight,
            "partnership": sociability * fw_cfg.sociability_weight + temperament * fw_cfg.temperament_weight * 0.5,
            "protection": temperament * fw_cfg.temperament_weight + (1.0 - impulsivity) * fw_cfg.impulsivity_weight * 0.3,
            "migration": curiosity * fw_cfg.curiosity_weight + impulsivity * fw_cfg.impulsivity_weight * 0.4,
            "cooperation": sociability * fw_cfg.sociability_weight + obedience * fw_cfg.obedience_weight + temperament * fw_cfg.temperament_weight * 0.3,
        }

    def _calculate_emotional_adjustments(self, person: Any, fw_cfg: Any) -> Dict[str, float]:
        """Ajusta motivaciones según el estado emocional actual."""
        emotions = person.emotions
        stress = emotions.get("stress", 0.0)
        happiness = emotions.get("happiness", 0.5)
        energy = emotions.get("energy", 1.0)
        
        adjustments = {
            "independence": stress * fw_cfg.stress_weight * 0.5,
            "exploration": (happiness - 0.5) * fw_cfg.happiness_weight * 0.3,
            "rebellion": stress * fw_cfg.stress_weight,
            "partnership": (happiness - 0.5) * fw_cfg.happiness_weight,
            "protection": (1.0 - happiness) * fw_cfg.happiness_weight * 0.5,
            "migration": stress * fw_cfg.stress_weight * 0.7,
            "cooperation": (happiness - 0.5) * fw_cfg.happiness_weight * 0.5,
        }
        
        energy_factor = energy * fw_cfg.energy_weight
        for motivation in adjustments:
            adjustments[motivation] *= energy_factor
        
        return adjustments

    def _calculate_environmental_adjustments(self, person: Any, context: EnvironmentContext, fw_cfg: Any) -> Dict[str, float]:
        """Ajusta motivaciones según la presión ambiental local."""
        pressure = context.get_local_pressure(person.x, person.y)
        excess_pressure = max(0.0, pressure - 1.0)
        
        return {
            "independence": excess_pressure * fw_cfg.crowding_weight,
            "exploration": 0.0,
            "rebellion": excess_pressure * fw_cfg.pressure_weight * 0.5,
            "partnership": -excess_pressure * fw_cfg.pressure_weight * 0.3,
            "protection": excess_pressure * fw_cfg.pressure_weight * 0.3,
            "migration": excess_pressure * fw_cfg.pressure_weight,
            "cooperation": -excess_pressure * fw_cfg.pressure_weight * 0.2,
        }

    def _calculate_memory_adjustments(self, person: Any, fw_cfg: Any) -> Dict[str, float]:
        """APRENDIZAJE: Ajusta motivaciones según la memoria episódica acumulada."""
        adjustments = {mot: 0.0 for mot in fw_cfg.motivations}
        if not hasattr(person, 'memory') or not isinstance(person.memory, dict):
            return adjustments
        
        episodic = person.memory.get("episodic", {})
        if not isinstance(episodic, dict):
            return adjustments
        
        for key, mem in episodic.items():
            intensity = mem.get('intensity', 0.0)
            valence = mem.get('valence', 0)
            
            if key.startswith("migration_") and valence > 0:
                adjustments["migration"] += intensity * fw_cfg.episodic_memory_factor
                adjustments["exploration"] += intensity * fw_cfg.episodic_memory_factor * 0.5
            if key.startswith("conflict_"):
                if valence < 0:
                    adjustments["rebellion"] += intensity * fw_cfg.episodic_memory_factor * 0.5
                    adjustments["cooperation"] -= intensity * fw_cfg.episodic_memory_factor * 0.3
                else:
                    adjustments["cooperation"] += intensity * fw_cfg.episodic_memory_factor * 0.3
            if key.startswith("marriage_") or key.startswith("companion_"):
                if valence > 0:
                    adjustments["partnership"] += intensity * fw_cfg.episodic_memory_factor
                    adjustments["protection"] += intensity * fw_cfg.episodic_memory_factor * 0.4
                else:
                    adjustments["partnership"] -= intensity * fw_cfg.episodic_memory_factor * 0.5
            if key.startswith("divorce_") and valence < 0:
                adjustments["partnership"] -= intensity * fw_cfg.episodic_memory_factor * 0.6
                adjustments["independence"] += intensity * fw_cfg.episodic_memory_factor * 0.4
            if key.startswith("adoption_") and valence > 0:
                adjustments["protection"] += intensity * fw_cfg.episodic_memory_factor * 0.5
                adjustments["cooperation"] += intensity * fw_cfg.episodic_memory_factor * 0.3
            if key.startswith("death_") and valence < 0:
                adjustments["independence"] += intensity * fw_cfg.episodic_memory_factor * 0.4
                adjustments["cooperation"] -= intensity * fw_cfg.episodic_memory_factor * 0.2
                adjustments["migration"] += intensity * fw_cfg.episodic_memory_factor * 0.3
            if key.startswith("child_") and valence > 0:
                adjustments["protection"] += intensity * fw_cfg.episodic_memory_factor * 0.6
                adjustments["partnership"] += intensity * fw_cfg.episodic_memory_factor * 0.3
            if key.startswith("disease_") and valence < 0:
                adjustments["independence"] += intensity * fw_cfg.episodic_memory_factor * 0.2
        
        return adjustments

    def _calculate_sickness_adjustments(self, person: Any, fw_cfg: Any) -> Dict[str, float]:
        """Ajusta motivaciones cuando el agente está enfermo."""
        adjustments = {mot: 0.0 for mot in fw_cfg.motivations}
        if not getattr(person, 'is_sick', False):
            return adjustments
        
        sickness_factor = min(1.0, len(person.active_infections) * 0.3)
        return {
            "independence": -sickness_factor * fw_cfg.sickness_factor,
            "exploration": -sickness_factor * fw_cfg.sickness_factor,
            "rebellion": -sickness_factor * fw_cfg.sickness_factor * 0.5,
            "partnership": sickness_factor * fw_cfg.sickness_factor * 0.3,
            "protection": sickness_factor * fw_cfg.sickness_factor,
            "migration": -sickness_factor * fw_cfg.sickness_factor,
            "cooperation": sickness_factor * fw_cfg.sickness_factor * 0.5,
        }

    def _calculate_age_adjustments(self, person: Any, fw_cfg: Any) -> Dict[str, float]:
        """Ajusta motivaciones según la etapa vital del agente."""
        adjustments = {mot: 0.0 for mot in fw_cfg.motivations}
        age = getattr(person, 'age', 0)
        
        if fw_cfg.adolescence_start_days <= age < fw_cfg.adolescence_end_days:
            adjustments["independence"] = 0.3
            adjustments["rebellion"] = 0.3
            adjustments["exploration"] = 0.2
        elif fw_cfg.adolescence_end_days <= age < 10950.0:
            adjustments["partnership"] = 0.2
        
        if getattr(person, 'children_count', 0) > 0:
            adjustments["protection"] = 0.3
        
        if getattr(person, 'is_senior', False):
            adjustments["exploration"] = -0.2
            adjustments["migration"] = -0.3
            adjustments["protection"] = 0.2
        
        return adjustments

    def _calculate_systemic_adjustments(self, person: Any, fw_cfg: Any) -> Dict[str, float]:
        """BLOQUE 3: Ajusta motivaciones según trauma sistémico y reputación social."""
        adjustments = {mot: 0.0 for mot in fw_cfg.motivations}
        
        memory = getattr(person, 'memory', {})
        if not isinstance(memory, dict):
            memory = {}
            
        trauma_abandonment = memory.get("trauma_abandonment", 0.0)
        trauma_adoption = memory.get("trauma_adoption", 0.0)
        reputation = getattr(person, 'reputation_score', 0.5)
        
        # Trauma por abandono: impulsa huida y reduce confianza social
        if trauma_abandonment > 0.3:
            adjustments["migration"] += trauma_abandonment * 0.6
            adjustments["cooperation"] -= trauma_abandonment * 0.4
            adjustments["partnership"] -= trauma_abandonment * 0.3
            
        # Trauma por adopción: impulsa independencia y rebelión
        if trauma_adoption > 0.3:
            adjustments["independence"] += trauma_adoption * 0.5
            adjustments["rebellion"] += trauma_adoption * 0.4
            adjustments["protection"] -= trauma_adoption * 0.3
            
        # Reputación social baja: dificulta cooperación y emparejamiento
        if reputation < 0.5:
            deficit = 0.5 - reputation
            adjustments["cooperation"] -= deficit * 0.5
            adjustments["partnership"] -= deficit * 0.4
            
        return adjustments

    # =================================================================
    # INHIBICIÓN COMPETITIVA Y EJECUCIÓN DE ACCIONES
    # =================================================================

    def _get_dominant_motivation(self, person: Any, fw_cfg: Any) -> Tuple[str, float]:
        """Obtiene la motivación dominante aplicando inhibición competitiva.
        
        RESUELVE: "Las probabilidades son independientes"
        Solo una motivación puede dominar y ejecutar una acción por tick.
        Las demás son inhibidas proporcionalmente.
        """
        if not hasattr(person, '_motivations') or not person._motivations:
            return ('none', 0.0)
        
        # Encontrar la motivación máxima
        max_name, max_value = max(person._motivations.items(), key=lambda x: x[1])
        
        # Aplicar inhibición a las demás motivaciones
        inhibited_motivations = {}
        for name, value in person._motivations.items():
            if name == max_name:
                inhibited_motivations[name] = value
            else:
                inhibition = max_value * fw_cfg.inhibition_factor
                inhibited_motivations[name] = max(0.0, value - inhibition)
        
        # Retornar la motivación dominante tras inhibición
        if inhibited_motivations:
            dominant_name, dominant_value = max(inhibited_motivations.items(), key=lambda x: x[1])
            return (dominant_name, dominant_value)
        
        return (max_name, max_value)

    def _get_action_threshold(self, motivation_name: str, fw_cfg: Any) -> float:
        """Obtiene el umbral de activación para una motivación específica."""
        threshold_attr = f"{motivation_name}_action_threshold"
        return getattr(fw_cfg, threshold_attr, fw_cfg.action_threshold)

    def _can_trigger_action(self, entity_id: int, motivation_name: str, current_day: float, fw_cfg: Any) -> bool:
        """Verifica si una acción puede ser desencadenada (respeta cooldown)."""
        if entity_id not in self._action_cooldowns:
            return True
        
        cooldowns = self._action_cooldowns[entity_id]
        if motivation_name not in cooldowns:
            return True
        
        last_action_day = cooldowns[motivation_name]
        days_since_last = current_day - last_action_day
        cooldown_days = self._get_action_cooldown(motivation_name, fw_cfg)
        
        return days_since_last >= cooldown_days

    def _register_action(self, entity_id: int, motivation_name: str, current_day: float) -> None:
        """Registra que se ejecutó una acción (para cooldown)."""
        if entity_id not in self._action_cooldowns:
            self._action_cooldowns[entity_id] = {}
        self._action_cooldowns[entity_id][motivation_name] = current_day

    def _get_action_cooldown(self, motivation_name: str, fw_cfg: Any) -> float:
        """Cooldowns específicos por tipo de motivación."""
        cooldowns = {
            "independence": 30.0, "exploration": 15.0, "rebellion": 60.0,
            "partnership": 30.0, "protection": 7.0, "migration": 90.0, "cooperation": 15.0,
        }
        return cooldowns.get(motivation_name, 30.0)

    def _get_motivation_consumption(self, motivation_name: str, fw_cfg: Any) -> float:
        """Consumo de motivación tras ejecutar una acción."""
        consumptions = {
            "independence": 0.2, "exploration": 0.15, "rebellion": 0.25,
            "partnership": 0.2, "protection": 0.15, "migration": 0.3, "cooperation": 0.15,
        }
        return consumptions.get(motivation_name, 0.2)

    # =================================================================
    # INTEGRACIÓN CON SISTEMA DE RELACIONES
    # =================================================================

    def _emit_relationship_events(
        self,
        person: Any,
        motivation: str,
        motivation_value: float,
        state: WorldState,
        current_day: float,
    ) -> None:
        """Emite eventos relacionales basados en la motivación dominante."""
        if not self.relationship_engine:
            return
        
        nearby_agents = self._find_nearby_agents(person, state, radius=15.0)
        if not nearby_agents:
            return
        
        # Filtrar targets según el tipo de motivación usando etiquetas relacionales
        required_labels = None
        excluded_labels = None
        
        if motivation == "cooperation":
            required_labels = ["Amigo", "Aliado", "Familia Elegida", "Conocido"]
            excluded_labels = ["Rival", "Enemigo"]
        elif motivation == "protection":
            required_labels = ["Familia Elegida", "Amigo", "Amante"]
        elif motivation == "rebellion":
            excluded_labels = ["Familia Elegida", "Amante"]
        elif motivation == "partnership":
            excluded_labels = ["Enemigo", "Rival"]
        
        # Filtrar candidatos
        filtered_targets = BehaviorInfluence.filter_targets_by_labels(
            person, nearby_agents, current_day,
            required_labels=required_labels,
            excluded_labels=excluded_labels
        )
        
        if not filtered_targets:
            filtered_targets = nearby_agents
        
        # Ponderar targets por prioridad relacional
        weighted_targets = []
        for target in filtered_targets:
            priority = BehaviorInfluence.get_target_priority(person, target, current_day)
            weighted_targets.append((target, priority))
        
        # Seleccionar target ponderado
        total_weight = sum(w for _, w in weighted_targets)
        if total_weight <= 0:
            target = random.choice(filtered_targets)
        else:
            r = random.uniform(0, total_weight)
            cumulative = 0.0
            target = filtered_targets[0]
            for t, w in weighted_targets:
                cumulative += w
                if cumulative >= r:
                    target = t
                    break
        
        # Determinar tipo de evento
        event_type = None
        intensity = 0.0
        context_str = ""
        
        if motivation == "cooperation":
            event_type = RelationshipEventType.COOPERATION
            intensity = min(1.0, motivation_value * 0.7)
            context_str = "cooperacion_motivada"
        elif motivation == "protection":
            event_type = RelationshipEventType.CARE
            intensity = min(1.0, motivation_value * 0.8)
            context_str = "proteccion_motivada"
        elif motivation == "rebellion":
            event_type = RelationshipEventType.CONFLICT
            intensity = min(1.0, motivation_value * 0.6)
            context_str = "rebelion_motivada"
        elif motivation == "partnership":
            event_type = RelationshipEventType.INTIMACY
            intensity = min(1.0, motivation_value * 0.5)
            context_str = "busqueda_pareja"
        
        if event_type is None:
            return
        
        try:
            event = _FreeWillRelationalEvent(
                event_type=event_type,
                intensity=intensity,
                context=context_str,
            )
            self.relationship_engine.process_event(event, person, target, current_day)
            
            # Logging del evento con contexto de etiquetas
            rel = person.get_relationship_with(target.entity_id, current_day)
            labels = rel.get_labels(current_day) if rel else ["Desconocido"]
            relationship_logger.log_significant_event(
                person.entity_id, target.entity_id,
                event_type.value, labels, labels,
                current_day
            )
        except Exception as e:
            self.logger.debug(f"Error al emitir evento relacional: {e}")

    def _find_nearby_agents(self, person: Any, state: WorldState, radius: float) -> List[Any]:
        """Encuentra agentes dentro de un radio específico (optimizado con bounding box)."""
        nearby = []
        radius_sq = radius * radius
        px, py = person.x, person.y
        
        for other in state.get_all_persons():
            if other.entity_id == person.entity_id:
                continue
            
            dx = abs(px - other.x)
            if dx > radius:
                continue
            dy = abs(py - other.y)
            if dy > radius:
                continue
            
            dist_sq = dx * dx + dy * dy
            if dist_sq <= radius_sq:
                nearby.append(other)
        
        return nearby

    # =================================================================
    # MÉTODOS ESTÁTICOS DE UTILIDAD (compatibilidad legacy)
    # =================================================================

    @staticmethod
    def has_impulse(person: Any, flag_name: str) -> bool:
        """Verifica si un agente tiene un impulso activo (compatibilidad legacy)."""
        if not hasattr(person, 'memory') or not isinstance(person.memory, dict):
            return False
        flags = person.memory.get("free_will_flags")
        if not isinstance(flags, dict):
            return False
        return flags.get(flag_name, False)

    @staticmethod
    def consume_impulse(person: Any, flag_name: str, pending: Optional[PendingChanges] = None) -> None:
        """Consume un impulso activo (compatibilidad legacy)."""
        if hasattr(person, 'memory') and isinstance(person.memory, dict):
            flags = person.memory.get("free_will_flags")
            if isinstance(flags, dict) and flag_name in flags:
                flags[flag_name] = False
                if pending is not None:
                    pending.consume_free_will_flag(person.entity_id, flag_name)