"""Módulo responsable de la integridad transaccional tras eventos de mortalidad.

Actúa como filtro de contingencia que purga todas las intenciones pendientes
de entidades que han fallecido durante el tick actual, evitando estados
inconsistentes en el commit final.

CORRECCIONES APLICADAS (Auditoría):
- Bug crítico: filtrado correcto de tuplas (entity_id, pathogen) en infections
- Limpieza de pending.recoveries
- Limpieza de pending.pregnancy_updates
- Limpieza de pending.births (si la madre muere, se cancela el parto)
- Limpieza de pending.emotion_updates y pending.memory_updates
"""

import logging
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext
from core.config.simulation_config import SimulationConfig


class DeathResolver:
    """Filtro de contingencia para purgar intenciones de entidades fallecidas."""

    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self.logger = logging.getLogger("DeathResolver")

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Ejecuta la purga de acciones en cascada sobre el búfer transaccional."""
        if not pending.deaths:
            return

        muertos_set = set(pending.deaths)

        # 1. Cancelar desplazamientos espaciales
        pending.movements = {
            e_id: coords
            for e_id, coords in pending.movements.items()
            if e_id not in muertos_set
        }

        # 2. Cancelar envejecimiento
        pending.age_increments = {
            e_id: inc
            for e_id, inc in pending.age_increments.items()
            if e_id not in muertos_set
        }

        # 3. CORRECCIÓN CRÍTICA: Cancelar infecciones recientes
        # pending.infections contiene tuplas (entity_id, pathogen), no simples IDs
        pending.infections = [
            (entity_id, pathogen)
            for entity_id, pathogen in pending.infections
            if entity_id not in muertos_set
        ]

        # 4. CORRECCIÓN: Cancelar recuperaciones de enfermedades
        # pending.recoveries contiene tuplas (entity_id, pathogen_id)
        pending.recoveries = [
            (entity_id, pathogen_id)
            for entity_id, pathogen_id in pending.recoveries
            if entity_id not in muertos_set
        ]

        # 5. Cancelar trámites de nupcias
        pending.marriages = {
            p_a: p_b
            for p_a, p_b in pending.marriages.items()
            if p_a not in muertos_set and p_b not in muertos_set
        }

        # 6. Cancelar trámites de divorcio
        pending.divorces = [
            (pa, pb)
            for pa, pb in pending.divorces
            if pa not in muertos_set and pb not in muertos_set
        ]

        # 7. Cancelar procesos de adopción
        if hasattr(pending, "adoptions"):
            pending.adoptions = [
                adop
                for adop in pending.adoptions
                if adop.get("child_id") not in muertos_set
                and adop.get("parent_a") not in muertos_set
                and (adop.get("parent_b") is None or adop.get("parent_b") not in muertos_set)
            ]

        # 8. CORRECCIÓN: Cancelar actualizaciones de embarazo
        if hasattr(pending, "pregnancy_updates"):
            pending.pregnancy_updates = {
                e_id: data
                for e_id, data in pending.pregnancy_updates.items()
                if e_id not in muertos_set
            }

        # 9. CORRECCIÓN: Cancelar nacimientos pendientes si la madre muere
        # Decisión: si la madre muere antes del commit, el parto se cancela
        # (el bebé no nace). Esto evita inconsistencias con huérfanos sin madre.
        if hasattr(pending, "births"):
            pending.births = [
                birth
                for birth in pending.births
                if birth.get("mother_id") not in muertos_set
            ]

        # 10. Cancelar actualizaciones emocionales
        if hasattr(pending, "emotion_updates"):
            pending.emotion_updates = {
                e_id: updates
                for e_id, updates in pending.emotion_updates.items()
                if e_id not in muertos_set
            }

        # 11. Cancelar actualizaciones de memoria
        if hasattr(pending, "memory_updates"):
            pending.memory_updates = {
                e_id: updates
                for e_id, updates in pending.memory_updates.items()
                if e_id not in muertos_set
            }

        # 12. Cancelar actualizaciones de libre albedrío
        if hasattr(pending, "free_will_flags_updates"):
            pending.free_will_flags_updates = {
                e_id: flags
                for e_id, flags in pending.free_will_flags_updates.items()
                if e_id not in muertos_set
            }

        # 13. Cancelar actualizaciones de motivaciones continuas
        if hasattr(pending, "motivation_updates"):
            pending.motivation_updates = {
                e_id: updates
                for e_id, updates in pending.motivation_updates.items()
                if e_id not in muertos_set
            }

        # 14. Cancelar objetivos de migración
        if hasattr(pending, "migration_targets"):
            pending.migration_targets = {
                e_id: target
                for e_id, target in pending.migration_targets.items()
                if e_id not in muertos_set
            }

        self.logger.debug(
            "DeathResolver: Purgadas %d entidades fallecidas del búfer transaccional",
            len(muertos_set),
        )