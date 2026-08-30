"""Generador de experiencias relacionales. Fase 4 Avanzada: Contextos Ricos.

OPTIMIZACIONES APLICADAS:
- Corrección de iteración sobre _relationships.values() (Dict en lugar de List)

GENÉTICA UNIVERSAL: Filtra experiencias según SocialCapabilities del organismo.
"""

from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass
from typing import Any, Optional, TYPE_CHECKING

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext
from systems.relationships.relationship_model import RelationshipEventType
from systems.relationships.social_capabilities import SocialCapabilities

if TYPE_CHECKING:
    from systems.relationships.relationship_experience_engine import RelationshipExperienceEngine


@dataclass
class _ExperienceEvent:
    """Evento ligero generado por el ExperienceGenerator."""
    event_type: RelationshipEventType
    intensity: float
    context: str


class ExperienceGenerator:
    """Genera oportunidades de experiencia basadas en etiquetas relacionales."""

    def __init__(
        self,
        config: SimulationConfig,
        relationship_engine: Optional['RelationshipExperienceEngine'] = None,
    ) -> None:
        self.config = config
        self.relationship_engine = relationship_engine
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.experience_probabilities = {
            "Conocido": {"cooperation": 0.005},
            "Aliado": {"cooperation": 0.015, "care": 0.005},
            "Amigo": {"cooperation": 0.025, "care": 0.01},
            "Interés Romántico": {"intimacy": 0.015, "cooperation": 0.01},
            "Amante": {"intimacy": 0.035, "cooperation": 0.02},
            "Familia Elegida": {"care": 0.025, "cooperation": 0.015},
            "Rival Respetado": {"competition": 0.01, "cooperation": 0.005},
            "Rival": {"competition": 0.015, "conflict": 0.005},
            "Enemigo": {"conflict": 0.02, "betrayal": 0.002},
        }
        
        self._tick_counter = 0
        self._log_interval = 365

    def _get_rich_context(self, label: str, experience_type: str) -> str:
        """Obtiene un contexto enriquecido basado en la etiqueta y el tipo de experiencia."""
        rich_contexts = {
            "Amigo": {
                "cooperation": random.choice(["paseo", "ayuda_mutua", "proyecto_compartido"]),
                "care": random.choice(["cuidado_enfermedad", "consejo_sabio", "apoyo_emocional"]),
            },
            "Aliado": {
                "cooperation": random.choice(["alianza_tactica", "intercambio_recursos"]),
                "care": random.choice(["proteccion_mutua"]),
            },
            "Interés Romántico": {
                "intimacy": random.choice(["cita_romantica", "mirada_complice"]),
                "cooperation": random.choice(["regalo_inesperado", "gesto_detallista"]),
            },
            "Amante": {
                "intimacy": random.choice(["noche_romantica", "confesion_amor", "intimidad_profunda"]),
                "cooperation": random.choice(["construir_hogar", "plan_futuro", "apoyo_incondicional"]),
            },
            "Familia Elegida": {
                "care": random.choice(["cena_familiar", "apoyo_incondicional", "tradicion_familiar"]),
                "cooperation": random.choice(["resolucion_problema_familiar"]),
            },
            "Rival Respetado": {
                "competition": random.choice(["duelo_de_habilidades", "reto_deportivo"]),
                "cooperation": random.choice(["tregua_temporal", "respeto_mutuo"]),
            },
            "Rival": {
                "competition": random.choice(["competencia_desleal", "provocacion"]),
                "conflict": random.choice(["discusion_acalorada", "enfrentamiento"]),
            },
            "Enemigo": {
                "conflict": random.choice(["ataque_directo", "hostilidad_abierta"]),
                "betrayal": random.choice(["traicion_calculada", "sabotaje"]),
            },
            "Conocido": {
                "cooperation": random.choice(["saludo_cordial", "favor_pequeño"]),
            }
        }
        
        default_contexts = {
            "cooperation": "interaccion_positiva",
            "care": "gesto_de_cuidado",
            "intimacy": "momento_intimo",
            "competition": "competencia",
            "conflict": "desacuerdo",
            "betrayal": "traicion",
        }
        
        return rich_contexts.get(label, {}).get(experience_type, default_contexts.get(experience_type, "general"))

    def process(self, state: WorldState, pending: PendingChanges, delta_days: float, context: EnvironmentContext) -> None:
        if not self.relationship_engine:
            return
        
        current_day = getattr(state, 'world_days_elapsed', 0.0)
        self._tick_counter += 1
        
        if self._tick_counter % self._log_interval == 0:
            self.logger.info(f"📊 ExperienceGenerator tick {current_day:.0f}: Procesando {len(state.get_all_persons())} agentes")
        
        for person in state.get_all_persons():
            if person.entity_id in pending.deaths:
                continue
            self._generate_opportunities(person, state, pending, current_day)

    def _generate_opportunities(self, agent: Any, state: WorldState, pending: PendingChanges, current_day: float) -> None:
        if not hasattr(agent, '_relationships') or not agent._relationships:
            return
        
        # GENÉTICA UNIVERSAL: Solo generar experiencias si tiene capacidades sociales
        social_caps = SocialCapabilities.from_genome(agent.genome)
        
        # Sin conciencia social, no hay experiencias relacionales
        if not social_caps.has_social_awareness:
            return
        
        should_log = self._tick_counter % self._log_interval == 0
        
        # CORRECCIÓN CRÍTICA: _relationships es ahora Dict[int, Relationship]
        # Hay que usar .values() para obtener los objetos Relationship
        for rel in agent._relationships.values():
            if rel.partner_id in pending.deaths:
                continue
            
            labels = rel.get_labels(current_day)
            
            if should_log and len(labels) > 1:
                self.logger.debug(f"🔍 Agente {agent.entity_id} → {rel.partner_id}: Etiquetas: {labels}, Recuerdos: {len(rel.memories)}")
            
            for label in labels:
                if label not in self.experience_probabilities:
                    continue
                
                experiences = self.experience_probabilities[label]
                for experience_type, probability in experiences.items():
                    # GENÉTICA UNIVERSAL: Verificar si puede participar en este evento
                    if not social_caps.can_participate_in_event(experience_type):
                        continue
                    
                    if random.random() < probability:
                        self._trigger_experience(agent, rel.partner_id, experience_type, label, current_day, state)

    def _trigger_experience(self, agent: Any, partner_id: int, experience_type: str, label: str, current_day: float, state: WorldState) -> None:
        if self.relationship_engine is None:
            return
        
        partner = state.get_person_by_id(partner_id)
        if partner is None:
            return
        
        distance = self._calculate_distance(agent, partner)
        if distance > 20.0:
            return
        
        event_mapping = {
            "cooperation": RelationshipEventType.COOPERATION,
            "care": RelationshipEventType.CARE,
            "intimacy": RelationshipEventType.INTIMACY,
            "competition": RelationshipEventType.COMPETITION,
            "conflict": RelationshipEventType.CONFLICT,
            "betrayal": RelationshipEventType.BETRAYAL,
        }
        
        if experience_type not in event_mapping:
            return
        
        event_type = event_mapping[experience_type]
        intensity = 0.7
        context_str = self._get_rich_context(label, experience_type)
        
        try:
            event = _ExperienceEvent(event_type=event_type, intensity=intensity, context=context_str)
            self.relationship_engine.process_event(event, agent, partner, current_day)
            
            self.logger.info(f"✨ Experiencia generada: Agente {agent.entity_id} y {partner_id} | Tipo: {experience_type} | Contexto: '{context_str}' | Distancia: {distance:.1f}")
        except Exception as e:
            self.logger.error(f"Error al generar experiencia: {e}", exc_info=True)

    def _calculate_distance(self, agent_a: Any, agent_b: Any) -> float:
        dx = agent_a.x - agent_b.x
        dy = agent_a.y - agent_b.y
        return math.sqrt(dx * dx + dy * dy)