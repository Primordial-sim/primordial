"""Ejecución de fases del pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from core.execution.execution_context import ExecutionContext
from core.execution.system_runner import ProcessableSystem, SystemRunner


@dataclass(slots=True)
class PhaseDefinition:
    """Define una fase de ejecución del motor.

    Attributes:
        name: Nombre de la fase.
        systems: Sistemas que se ejecutan dentro de la fase.
    """

    name: str
    systems: list[ProcessableSystem] = field(default_factory=list)


class PhaseExecutor:
    """Ejecuta todos los sistemas de una fase."""

    def __init__(self, runner: SystemRunner | None = None) -> None:
        """Inicializa el ejecutor de fases.

        Args:
            runner: Ejecutor opcional de sistemas individuales.
        """

        self.runner = runner or SystemRunner()
        self.logger = logging.getLogger(self.__class__.__name__)

    def execute(
        self,
        phase: PhaseDefinition,
        context: ExecutionContext,
    ) -> None:
        """Ejecuta una fase completa.

        Args:
            phase: Fase que se va a ejecutar.
            context: Contexto compartido del tick.
        """

        self.logger.debug(
            "Iniciando fase %s con %s sistemas.",
            phase.name,
            len(phase.systems),
        )

        for system in phase.systems:
            self.runner.run(
                system=system,
                context=context,
                phase_name=phase.name,
            )