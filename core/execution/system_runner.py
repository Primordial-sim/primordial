"""Ejecución segura de sistemas individuales.

OPTIMIZACIÓN: Logging reducido para evitar saturación en simulaciones largas.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

from core.execution.execution_context import ExecutionContext


class ProcessableSystem(Protocol):
    """Protocolo mínimo que debe cumplir un sistema ejecutable."""

    def process(
        self,
        state: Any,
        pending: Any,
        delta_days: float,
        context: Any,
    ) -> None:
        """Procesa un tick de simulación."""


class SystemRunner:
    """Ejecuta un sistema y registra errores de forma uniforme."""

    def __init__(self) -> None:
        """Inicializa el ejecutor."""

        self.logger = logging.getLogger(self.__class__.__name__)

    def run(
        self,
        system: ProcessableSystem,
        context: ExecutionContext,
        phase_name: str,
    ) -> None:
        """Ejecuta un sistema dentro de una fase concreta.

        Args:
            system: Sistema que implementa ``process``.
            context: Contexto de ejecución del tick.
            phase_name: Nombre de la fase actual.

        Raises:
            TypeError: Si el sistema no implementa ``process``.
            Exception: Relanza cualquier fallo interno del sistema.
        """

        system_name = system.__class__.__name__
        process = getattr(system, "process", None)

        if not callable(process):
            raise TypeError(
                f"El sistema {system_name} no implementa process(...)."
            )

        try:
            # CORRECCIÓN: Eliminado logging DEBUG excesivo por cada sistema
            # PhaseExecutor ya logea el inicio de cada fase
            
            process(
                context.state,
                context.pending,
                context.delta_days,
                context.environment,
            )

        except Exception:
            self.logger.exception(
                "Fallo crítico en %s durante la fase %s, tick %s.",
                system_name,
                phase_name,
                context.current_tick,
            )
            raise