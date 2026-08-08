"""Módulo desactivado. La lógica de relaciones es emergente vía experiencias.

Las relaciones evolucionan mediante:
- RelationshipManager: crea relaciones y memorias iniciales
- ExperienceGenerator: genera experiencias (cooperation, care, conflict, intimacy)
- RelationshipExperienceEngine: procesa eventos en memorias con sesgos
- Relationship.get_labels(): etiquetas emergentes (Amigo, Enemigo, Amante, etc.)
- Decaimiento temporal: las memorias pierden peso con el tiempo

NO se usan estados lineales ni affinity. NO se fuerzan rupturas.
"""

from __future__ import annotations

import logging
from typing import Any

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext


class RelationshipSystem:
    """Stub inactivo. Toda la lógica relacional es emergente."""

    def __init__(
        self,
        config: SimulationConfig,
        relationship_engine: Any = None,
    ) -> None:
        self.config = config
        self.relationship_engine = relationship_engine
        self.logger = logging.getLogger(self.__class__.__name__)

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Intencionalmente vacío. Las relaciones evolucionan por experiencias."""
        pass