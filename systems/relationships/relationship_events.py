"""Definición de eventos relacionales para el motor de experiencias.

Este módulo define el vocabulario común que todos los sistemas de la simulación
(DiseaseSystem, ConceptionSystem, MovementSystem, etc.) utilizarán para 
comunicar experiencias significativas al RelationshipExperienceEngine.

No contiene lógica de procesamiento, solo la estructura de los datos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class RelationshipEventType(Enum):
    """Catálogo de experiencias relacionales significativas."""
    
    # --- INTERACCIONES POSITIVAS ---
    CARE = "care"                    # Un agente cuida a otro (ej: durante enfermedad)
    COOPERATION = "cooperation"      # Trabajo conjunto, caza compartida, defensa mutua
    SHARE_RESOURCE = "share_resource"# Donación o intercambio voluntario de recursos
    INTIMACY = "intimacy"            # Tiempo de calidad, conversación, cercanía prolongada
    RECONCILIATION = "reconciliation"# Resolución de un conflicto previo
    
    # --- INTERACCIONES NEGATIVAS ---
    COMPETITION = "competition"      # Competencia por un recurso limitado (comida, pareja)
    BETRAYAL = "betrayal"            # Robo, abandono, infidelidad, mentira
    CONFLICT = "conflict"            # Pelea física o discusión verbal directa
    NEGLECT = "neglect"              # Ignorar necesidades básicas del otro a propósito
    
    # --- HITOS VITALES (EVENTOS DE ESTADO) ---
    BIRTH = "birth"                  # Nacimiento de un hijo en común
    CHILD_DEATH = "child_death"      # Muerte de un hijo en común
    PARTNER_DEATH = "partner_death"  # Muerte de la pareja
    COHABITATION_START = "cohabitation_start" # Decisión de vivir juntos
    COHABITATION_END = "cohabitation_end"     # Decisión de separar los hogares


@dataclass
class RelationshipEvent:
    """Representa una experiencia compartida entre dos agentes.
    
    Atributos:
        event_type: El tipo de experiencia (del Enum RelationshipEventType).
        agent_a_id: El agente que inicia o es el sujeto principal de la acción.
        agent_b_id: El agente que recibe la acción o es el objeto (puede ser None para eventos grupales).
        intensity: La magnitud emocional del evento [0.0, 1.0]. 
                   Ej: Cuidar una gripe leve = 0.2, salvar la vida = 0.95.
        context: Información adicional específica del evento. 
                 Ej: "Influenza_000001", "comida", "hijo_id_123".
        day: El día de la simulación en que ocurrió el evento.
        metadata: Diccionario opcional para datos adicionales específicos del sistema emisor.
    """
    event_type: RelationshipEventType
    agent_a_id: int
    agent_b_id: int
    intensity: float
    context: str
    day: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validación básica de los rangos de los atributos."""
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError(f"La intensidad debe estar entre 0.0 y 1.0, recibido: {self.intensity}")
        if self.intensity < 0.0:
            self.intensity = 0.0
        elif self.intensity > 1.0:
            self.intensity = 1.0


# ==============================================================================
# EJEMPLOS DE USO (Para que otros sistemas sepan cómo emitir eventos)
# ==============================================================================

# Ejemplo 1: DiseaseSystem emitiendo un evento de cuidado
# event = RelationshipEvent(
#     event_type=RelationshipEventType.CARE,
#     agent_a_id=agente_sano.entity_id,
#     agent_b_id=agente_enfermo.entity_id,
#     intensity=0.8,  # Alto impacto por riesgo de contagio
#     context="Influenza_000001",
#     day=current_day,
#     metadata={"duration_days": 5}
# )

# Ejemplo 2: ConceptionSystem emitiendo un evento de nacimiento
# event = RelationshipEvent(
#     event_type=RelationshipEventType.BIRTH,
#     agent_a_id=madre.entity_id,
#     agent_b_id=padre.entity_id,
#     intensity=0.9,
#     context=f"child_{nuevo_bebe.entity_id}",
#     day=current_day
# )

# Ejemplo 3: ResourceSystem emitiendo un evento de competencia
# event = RelationshipEvent(
#     event_type=RelationshipEventType.COMPETITION,
#     agent_a_id=agente_hambriento_1.entity_id,
#     agent_b_id=agente_hambriento_2.entity_id,
#     intensity=0.6,
#     context="food_node_42",
#     day=current_day
# )