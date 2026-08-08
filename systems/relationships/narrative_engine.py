"""Motor de Narrativas Cognitivas. Fase 2 + Fase 4: Contextos Ricos.

Detecta patrones complejos en la historia de una relación, utilizando
ventanas temporales, evaluaciones condicionales y el contexto específico 
del evento para refinar las narrativas.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from systems.relationships.relationship_model import Relationship, PersonalMemory

class NarrativeEngine:
    """Motor estático para la detección y actualización de narrativas relacionales."""

    RECENT_WINDOW_DAYS = 365.0

    @staticmethod
    def update_narratives(rel: 'Relationship', new_memory: 'PersonalMemory', current_day: float) -> None:
        """Actualiza las narrativas de forma incremental cuando llega un nuevo recuerdo."""
        
        # 1. Obtener recuerdos recientes de forma eficiente
        recent_memories = []
        for mem in reversed(rel.memories):
            if (current_day - mem.day) <= NarrativeEngine.RECENT_WINDOW_DAYS:
                recent_memories.append(mem)
            else:
                break
        
        if not recent_memories:
            recent_memories = [new_memory]

        context_lower = new_memory.context.lower()

        # Patrón A: Tensión reciente acumulada
        conflict_weight_recent = sum(m.current_weight(current_day) for m in recent_memories if m.category.name in ('CONFLICT', 'TRAUMA'))
        if conflict_weight_recent > 80.0:
            rel._strengthen_or_create_narrative("Últimamente hay mucha tensión", current_day, 0.25)

        # Patrón B: Salvador en crisis
        support_weight = sum(m.current_weight(current_day) for m in rel.memories if m.category.name in ('SURVIVAL', 'COOPERATION', 'FAMILY') and m.emotional_valence > 0)
        if support_weight > 150.0:
            rel._strengthen_or_create_narrative("Es mi roca en momentos difíciles", current_day, 0.20)

        # Patrón C: Relación superficial
        social_weight_recent = sum(m.current_weight(current_day) for m in recent_memories if m.category.name == 'SOCIAL')
        deep_weight_recent = sum(m.current_weight(current_day) for m in recent_memories if m.category.name in ('ROMANTIC', 'FAMILY', 'COOPERATION'))
        if social_weight_recent > 100.0 and deep_weight_recent < 50.0:
            rel._strengthen_or_create_narrative("Nuestra relación es superficial", current_day, 0.15)

        # Patrón D: Trauma por traición (MEJORADO CON CONTEXTO - Fase 4)
        if new_memory.category.name in ('TRAUMA', 'CONFLICT') and new_memory.emotional_valence < 0:
            if any(word in context_lower for word in ["traicion", "sabotaje", "ataque_directo"]):
                rel._strengthen_or_create_narrative("Me traicionó y no lo olvido", current_day, 0.60)
            else:
                rel._strengthen_or_create_narrative("Me falló en un momento clave", current_day, 0.40)

        # Patrón E: Patrones clásicos mejorados (MEJORADO CON CONTEXTO - Fase 4)
        if new_memory.category.name == 'CONFLICT' and new_memory.emotional_valence < -0.5:
            if "discusion_acalorada" in context_lower:
                rel._strengthen_or_create_narrative("Siempre terminamos discutiendo", current_day, 0.25)
            else:
                rel._strengthen_or_create_narrative("Siempre me falla", current_day, 0.20)
                
        elif new_memory.category.name == 'COOPERATION' and new_memory.emotional_valence > 0.5:
            if any(word in context_lower for word in ["ayuda_mutua", "apoyo_incondicional", "consejo_sabio"]):
                rel._strengthen_or_create_narrative("Siempre puedo contar con esta persona", current_day, 0.25)
            else:
                rel._strengthen_or_create_narrative("Siempre me ayuda", current_day, 0.15)
                
        # Patrón F: Distanciamiento progresivo
        days_since_last = current_day - rel.last_interaction_day
        if days_since_last > 180.0 and len(recent_memories) < 3:
            rel._strengthen_or_create_narrative("Nos estamos distanciando", current_day, 0.10)
            
        # Patrón G: Narrativas Románticas (NUEVO - Fase 4)
        if new_memory.category.name == 'ROMANTIC' and new_memory.emotional_valence > 0:
            if any(word in context_lower for word in ["noche_romantica", "confesion_amor", "intimidad_profunda"]):
                rel._strengthen_or_create_narrative("Nuestra conexión es profunda", current_day, 0.30)