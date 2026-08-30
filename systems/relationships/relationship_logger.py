"""Sistema de logging específico para relaciones. Fase 3: Expresión.

Registra eventos relacionales significativos, cambios de etiquetas y
patrones detectados para análisis y debugging.
"""

from __future__ import annotations

import logging
from typing import List, Set


class RelationshipLogger:
    """Logger especializado para eventos relacionales."""
    
    def __init__(self) -> None:
        self.logger = logging.getLogger("Relationships")
    
    def log_label_change(
        self,
        agent_id: int,
        partner_id: int,
        old_labels: Set[str],
        new_labels: Set[str],
        current_day: float,
    ) -> None:
        """Registra cambios en las etiquetas de una relación."""
        added = new_labels - old_labels
        removed = old_labels - new_labels
        
        if added:
            self.logger.info(
                "🏷️  Día %.0f: Agente %s → %s | Etiquetas añadidas: %s",
                current_day, agent_id, partner_id, ", ".join(added)
            )
        
        if removed:
            self.logger.info(
                "🏷️  Día %.0f: Agente %s → %s | Etiquetas eliminadas: %s",
                current_day, agent_id, partner_id, ", ".join(removed)
            )
    
    def log_significant_event(
        self,
        agent_a_id: int,
        agent_b_id: int,
        event_type: str,
        labels_a: List[str],
        labels_b: List[str],
        current_day: float,
    ) -> None:
        """Registra eventos relacionales significativos con contexto de etiquetas."""
        self.logger.info(
            "💞 Día %.0f: Evento %s entre %s y %s | Etiquetas A: %s | Etiquetas B: %s",
            current_day, event_type, agent_a_id, agent_b_id,
            ", ".join(labels_a), ", ".join(labels_b)
        )
    
    def log_narrative_detection(
        self,
        agent_id: int,
        partner_id: int,
        narrative_pattern: str,
        strength: float,
        current_day: float,
    ) -> None:
        """Registra detección de nuevas narrativas."""
        self.logger.info(
            "📖 Día %.0f: Agente %s → %s | Narrativa detectada: '%s' (fuerza: %.2f)",
            current_day, agent_id, partner_id, narrative_pattern, strength
        )
    
    def log_relationship_milestone(
        self,
        agent_id: int,
        partner_id: int,
        milestone: str,
        current_day: float,
    ) -> None:
        """Registra hitos relacionales importantes."""
        self.logger.info(
            "🎯 Día %.0f: Agente %s → %s | Hito: %s",
            current_day, agent_id, partner_id, milestone
        )


# Instancia global del logger
relationship_logger = RelationshipLogger()