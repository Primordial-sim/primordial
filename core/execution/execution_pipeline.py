"""Pipeline único de ejecución de ticks.

El pipeline ejecuta todas las fases de un tick y devuelve los cambios
pendientes. No aplica el commit; esa responsabilidad pertenece a
``WorldState`` y se invoca desde ``SimulationEngine``.

OPTIMIZACIÓN: Reutiliza EnvironmentContext entre ticks para evitar
recalcular el sector_map en cada iteración.
"""

from __future__ import annotations

import logging
from typing import Any, Iterable

from core.config.simulation_config import SimulationConfig
from core.execution.execution_context import ExecutionContext
from core.execution.phase_executor import PhaseDefinition, PhaseExecutor
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext


class ExecutionPipeline:
    """Ejecuta todas las fases configuradas para un tick."""

    def __init__(
        self,
        config: SimulationConfig,
        phases: Iterable[PhaseDefinition],
        phase_executor: PhaseExecutor | None = None,
    ) -> None:
        """Inicializa el pipeline.

        Args:
            config: Configuración compartida de la simulación.
            phases: Fases ordenadas que se ejecutarán en cada tick.
            phase_executor: Ejecutor opcional para cada fase.

        Raises:
            ValueError: Si no se proporciona ninguna fase o hay duplicados.
        """

        self.config = config
        self.phases = list(phases)
        self.phase_executor = phase_executor or PhaseExecutor()
        self.logger = logging.getLogger(self.__class__.__name__)

        if not self.phases:
            raise ValueError("ExecutionPipeline necesita al menos una fase.")

        # CORRECCIÓN: Validar que no haya fases duplicadas
        phase_names = [p.name for p in self.phases]
        if len(phase_names) != len(set(phase_names)):
            duplicates = [name for name in phase_names if phase_names.count(name) > 1]
            raise ValueError(f"Fases duplicadas detectadas en el pipeline: {set(duplicates)}")

        # CORRECCIÓN: Validar que todos los sistemas implementen process()
        for phase in self.phases:
            for system in phase.systems:
                if not hasattr(system, 'process') or not callable(system.process):
                    raise TypeError(
                        f"El sistema {system.__class__.__name__} en fase "
                        f"'{phase.name}' no implementa process()."
                    )

    def execute_tick(
        self,
        state: WorldState,
        delta_days: float,
        current_tick: int,
        current_day: float,
        event_bus: Any = None,
    ) -> PendingChanges:
        """Ejecuta un tick completo de simulación.

        Args:
            state: Estado actual del mundo.
            delta_days: Duración del tick en días simulados.
            current_tick: Número de tick actual.
            current_day: Día simulado actual.
            event_bus: Bus de eventos opcional.

        Returns:
            Cambios pendientes acumulados durante el tick.
        """

        pending = PendingChanges()
        
        # CORRECCIÓN: Reutilizar EnvironmentContext para optimizar rendimiento
        if not hasattr(self, '_environment'):
            self._environment = EnvironmentContext(state=state, config=self.config)
        else:
            # Actualizar sector_map (los agentes se mueven entre ticks)
            self._environment.sector_map = self._environment._build_sector_map(state)
            self._environment.pressure_map.clear()
        
        environment = self._environment

        context = ExecutionContext(
            state=state,
            pending=pending,
            environment=environment,
            config=self.config,
            delta_days=delta_days,
            current_tick=current_tick,
            current_day=current_day,
            event_bus=event_bus,
        )

        for phase in self.phases:
            self.phase_executor.execute(phase, context)

        return pending