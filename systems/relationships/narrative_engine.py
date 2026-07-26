"""Motor de Narrativas Cognitivas. Fase 2.

Detecta patrones complejos en la historia de una relación, utilizando
ventanas temporales y evaluaciones condicionales. Mantiene la asimetría
completa y la actualización incremental para no afectar el rendimiento.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from systems.relationships.relationship_model import Relationship, PersonalMemory, MemoryCategory

class NarrativeEngine:
    """Motor estático para la detección y actualización de narrativas relacionales."""

    # Ventana temporal para considerar un recuerdo como "reciente" (1 año)
    RECENT_WINDOW_DAYS = 365.0

    @staticmethod
    def update_narratives(rel: 'Relationship', new_memory: 'PersonalMemory', current_day: float) -> None:
        """
        Actualiza las narrativas de forma incremental cuando llega un nuevo recuerdo.
        Coste: O(K) donde K es el número de recuerdos en la ventana reciente (muy rápido).
        """
        
        # 1. Obtener recuerdos recientes de forma eficiente (iteración inversa hasta salir de la ventana)
        recent_memories = []
        for mem in reversed(rel.memories):
            if (current_day - mem.day) <= NarrativeEngine.RECENT_WINDOW_DAYS:
                recent_memories.append(mem)
            else:
                break  # Al estar ordenados por día, podemos cortar la búsqueda
        
        # Si no hay recuerdos recientes, usamos al menos el nuevo
        if not recent_memories:
            recent_memories = [new_memory]

        # 2. Evaluar patrones complejos basados en el nuevo recuerdo y el contexto reciente
        
        # Patrón A: Tensión reciente acumulada
        conflict_weight_recent = sum(
            m.current_weight(current_day) for m in recent_memories 
            if m.category.name in ('CONFLICT', 'TRAUMA')
        )
        if conflict_weight_recent > 80.0:
            rel._strengthen_or_create_narrative("Últimamente hay mucha tensión", current_day, 0.25)

        # Patrón B: Salvador en crisis (Alto peso en SURVIVAL o COOPERATION)
        support_weight = sum(
            m.current_weight(current_day) for m in rel.memories 
            if m.category.name in ('SURVIVAL', 'COOPERATION', 'FAMILY') and m.emotional_valence > 0
        )
        if support_weight > 150.0:
            rel._strengthen_or_create_narrative("Es mi roca en momentos difíciles", current_day, 0.20)

        # Patrón C: Relación superficial (Mucho SOCIAL, poco profundo)
        social_weight_recent = sum(
            m.current_weight(current_day) for m in recent_memories 
            if m.category == 'SOCIAL' # type: ignore
        )
        deep_weight_recent = sum(
            m.current_weight(current_day) for m in recent_memories 
            if m.category.name in ('ROMANTIC', 'FAMILY', 'COOPERATION')
        )
        if social_weight_recent > 100.0 and deep_weight_recent < 50.0:
            rel._strengthen_or_create_narrative("Nuestra relación es superficial", current_day, 0.15)

        # Patrón D: Trauma por traición (Evento específico de alto impacto)
        if new_memory.category.name in ('TRAUMA', 'CONFLICT') and new_memory.event_type in ('betrayal', 'neglect'):
            rel._strengthen_or_create_narrative("Me traicionó y no lo olvido", current_day, 0.50)

        # Patrón E: Patrones clásicos mejorados (Legacy de Fase 1, pero con más matices)
        if new_memory.category.name == 'CONFLICT' and new_memory.emotional_valence < -0.5:
            rel._strengthen_or_create_narrative("Siempre me falla", current_day, 0.20)
        elif new_memory.category.name == 'COOPERATION' and new_memory.emotional_valence > 0.5:
            rel._strengthen_or_create_narrative("Siempre me ayuda", current_day, 0.15)
            
        # Patrón F: Distanciamiento progresivo (Si han pasado muchos días sin interacción significativa)
        days_since_last = current_day - rel.last_interaction_day
        if days_since_last > 180.0 and len(recent_memories) < 3:
            rel._strengthen_or_create_narrative("Nos estamos distanciando", current_day, 0.10)