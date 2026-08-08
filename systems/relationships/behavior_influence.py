"""Motor de influencia conductual. Fase 3: Expresión.

Determina cómo las etiquetas relacionales influyen en las decisiones
de los agentes, tanto en la selección de targets para interacción
como en la evaluación de utilidad espacial.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from systems.relationships.relationship_model import Relationship


class BehaviorInfluence:
    """Motor estático que traduce etiquetas relacionales en influencia conductual."""
    
    # ========================================================================
    # INFLUENCIA EN SELECCIÓN DE TARGETS (FreeWillSystem)
    # ========================================================================
    
    @staticmethod
    def get_target_priority(agent: Any, target: Any, current_day: float) -> float:
        """Calcula la prioridad de un target para interacción social.
        
        Retorna un multiplicador [0.0, 2.0] que indica cuán probable es
        que el agente elija a este target para interactuar.
        """
        rel = agent.get_relationship_with(target.entity_id, current_day)
        if rel is None:
            return 0.5
        
        labels = rel.get_labels(current_day)
        
        if "Amante" in labels:
            return 2.0
        if "Amigo" in labels:
            return 1.8
        if "Familia Elegida" in labels:
            return 1.7
        if "Interés Romántico" in labels:
            return 1.6
        if "Aliado" in labels:
            return 1.5
        if "Conocido" in labels:
            return 1.0
        if "Rival Respetado" in labels:
            return 0.8
        if "Rival" in labels:
            return 0.6
        if "Enemigo" in labels:
            return 0.3
            
        return 1.0
    
    @staticmethod
    def filter_targets_by_labels(
        agent: Any,
        candidates: List[Any],
        current_day: float,
        required_labels: Optional[List[str]] = None,
        excluded_labels: Optional[List[str]] = None,
    ) -> List[Any]:
        """Filtra candidatos basándose en etiquetas relacionales."""
        if not candidates:
            return []
        
        filtered = []
        for candidate in candidates:
            rel = agent.get_relationship_with(candidate.entity_id, current_day)
            if rel is None:
                if not required_labels:
                    filtered.append(candidate)
                continue
            
            labels = rel.get_labels(current_day)
            
            if required_labels:
                if not any(label in labels for label in required_labels):
                    continue
            
            if excluded_labels:
                if any(label in labels for label in excluded_labels):
                    continue
            
            filtered.append(candidate)
        
        return filtered
    
    # ========================================================================
    # INFLUENCIA EN MOVIMIENTO (MovementSystem)
    # ========================================================================
    
    @staticmethod
    def get_social_attraction(
        agent: Any,
        target: Any,
        current_day: float,
    ) -> float:
        """Calcula la atracción social hacia un target para evaluación de celdas.
        
        Retorna un valor [-5.0, 10.0]. Positivo = atracción, negativo = repulsión.
        """
        rel = agent.get_relationship_with(target.entity_id, current_day)
        if rel is None:
            return 0.0
        
        labels = rel.get_labels(current_day)
        
        if "Amante" in labels:
            return 10.0
        if "Familia Elegida" in labels:
            return 8.0
        if "Amigo" in labels:
            return 7.0
        if "Interés Romántico" in labels:
            return 6.0
        if "Aliado" in labels:
            return 5.0
        if "Conocido" in labels:
            return 2.0
        if "Rival Respetado" in labels:
            return -1.0
        if "Rival" in labels:
            return -3.0
        if "Enemigo" in labels:
            return -5.0
            
        return 0.0
    
    @staticmethod
    def get_multiple_social_anchors(
        agent: Any,
        all_agents: List[Any],
        current_day: float,
        max_anchors: int = 3,
    ) -> List[tuple[Any, float]]:
        """Obtiene múltiples anclas sociales ordenadas por importancia.
        
        Retorna los N agentes más importantes basándose en etiquetas.
        """
        anchors = []
        
        for other in all_agents:
            if other.entity_id == agent.entity_id:
                continue
            
            rel = agent.get_relationship_with(other.entity_id, current_day)
            if rel is None:
                continue
            
            labels = rel.get_labels(current_day)
            
            weight = 0.0
            if "Amante" in labels:
                weight = 10.0
            elif "Familia Elegida" in labels:
                weight = 8.0
            elif "Amigo" in labels:
                weight = 7.0
            elif "Interés Romántico" in labels:
                weight = 6.0
            elif "Aliado" in labels:
                weight = 5.0
            elif "Conocido" in labels:
                weight = 2.0
            
            if weight > 0:
                anchors.append((other, weight))
        
        anchors.sort(key=lambda x: x[1], reverse=True)
        return anchors[:max_anchors]