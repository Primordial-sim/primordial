"""Motor de compatibilidad multifactorial para relaciones sociales.

Integra orientación Kinsey, afinidad genética/emocional, distancia,
edad, recuerdos compartidos y modificadores de libre albedrío.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext
from systems.relationships.relationship_model import is_orientation_compatible


class CompatibilityEngine:
    """Calcula puntuaciones de compatibilidad entre dos agentes."""

    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self.rel_cfg = config.relationships
        self.logger = logging.getLogger(self.__class__.__name__)

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Fase de precalculación. Se mantiene vacío para cumplir el protocolo del PhaseScheduler."""
        pass

    def calculate_compatibility(
        self,
        p1: Any,
        p2: Any,
        current_day: float,
        free_will_boost: float = 0.0,
    ) -> float:
        """Calcula compatibilidad [0.0, 1.0] entre dos personas."""
        cfg = self.rel_cfg
        
        orientation_score = is_orientation_compatible(
            p1.sexual_orientation,
            p2.sexual_orientation,
            tolerance=cfg.orientation_tolerance,
        )
        if orientation_score <= 0.0:
            return 0.0
        
        age_diff_years = abs(p1.age - p2.age) / 365.0
        age_score = max(0.0, 1.0 - (age_diff_years / 20.0))
        
        distance = math.hypot(p1.x - p2.x, p1.y - p2.y)
        distance_score = max(0.0, 1.0 - (distance / 50.0))
        
        affinity = self._calculate_base_affinity(p1, p2, current_day)
        
        raw_score = (
            affinity * cfg.affinity_weight +
            age_score * cfg.age_weight +
            distance_score * cfg.distance_weight
        )
        
        base_compatibility = raw_score * orientation_score
        final_score = min(1.0, base_compatibility + free_will_boost)
        
        return max(0.0, final_score)

    def _calculate_base_affinity(self, p1: Any, p2: Any, current_day: float) -> float:
        """Afinidad basada en rasgos dinámicos y memoria relacional compartida.
        
        CORRECCIÓN: Ahora lee de Relationship.memories en lugar de p1.memory['episodic']
        para mantener la coherencia con la nueva arquitectura de relaciones.
        """
        soc_diff = abs(p1.effective_sociability - p2.effective_sociability)
        soc_score = max(0.0, 1.0 - (soc_diff / 2.0))
        
        temp_diff = abs(p1.effective_temperament - p2.effective_temperament)
        temp_score = min(1.0, temp_diff / 1.5)
        
        base = (soc_score * 0.5) + (temp_score * 0.5)
        
        # CORRECCIÓN: Usar el sistema de relaciones nuevo
        rel = p1.get_relationship_with(p2.entity_id, current_day)
        if rel is not None and hasattr(rel, 'memories'):
            # Sumar pesos actuales (que ya incluyen decaimiento temporal)
            shared_positive = sum(m.current_weight(current_day) for m in rel.memories if m.emotional_valence > 0)
            shared_negative = sum(m.current_weight(current_day) for m in rel.memories if m.emotional_valence < 0)
            
            # Factores de ajuste para que el impacto sea significativo pero no dominante
            base += min(0.3, shared_positive * 0.002)
            base -= min(0.3, shared_negative * 0.003)
        
        return max(0.0, min(1.0, base))