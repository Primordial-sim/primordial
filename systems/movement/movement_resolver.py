"""Módulo responsable de arbitrar colisiones espaciales antes del commit global.

CAMBIOS RECIENTES:
- Gasto de energía por movimiento: Cada agente que realmente se mueve
  gasta energía. Como cada movimiento es exactamente una casilla por tick,
  el coste es un valor fijo por "acción" y se modifica por el tamaño y
  tipo de movimiento de la especie (no por distancia física).

MIGRACIÓN HEXAGONAL:
- person.x/y → person.q/r
- target_x/y → target_q/r
- casillas_bloqueadas usa (q, r)
"""

import logging
import random
from typing import Dict, List, Set, Tuple

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext


class MovementResolver:
    """Resuelve cuellos de botella espaciales de forma determinista."""

    def __init__(self, config: SimulationConfig) -> None:
        """Inicializa el resolutor cumpliendo el contrato de la arquitectura."""
        self.config = config
        self.logger = logging.getLogger("MovementResolver")

        # Parámetros de gasto de energía por movimiento (REDUCIDO: 0.2 → 0.05)
        self.energy_cost_per_action: float = 0.05

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Analiza las intenciones de movimiento y evita solapamientos espaciales."""
        if not getattr(pending, "movements", None):
            return

        # 1. Identificar casillas bloqueadas (ocupadas por individuos estáticos)
        casillas_bloqueadas: Set[Tuple[int, int]] = set()
        for person in state.get_all_persons():
            if person.entity_id in pending.deaths:
                continue

            if person.entity_id not in pending.movements:
                # HEX: Usar q, r en lugar de x, y
                casillas_bloqueadas.add((int(person.q), int(person.r)))

        # 2. Agrupar peticiones por celda destino y aplicar Fail-Safes
        peticiones_por_celda: Dict[Tuple[int, int], List[int]] = {}
        for entity_id, (target_q, target_r) in pending.movements.items():
            if entity_id in pending.deaths:
                continue

            # HEX: Usar q, r en lugar de x, y
            final_q = max(0, min(int(target_q), state.width - 1))
            final_r = max(0, min(int(target_r), state.height - 1))
            destino = (final_q, final_r)

            if destino not in peticiones_por_celda:
                peticiones_por_celda[destino] = []
            peticiones_por_celda[destino].append(entity_id)

        # 3. Arbitrar conflictos y respetar ocupaciones
        movimientos_validados: Dict[int, Tuple[int, int]] = {}
        for destino, candidatos in peticiones_por_celda.items():
            if destino in casillas_bloqueadas:
                continue

            if len(candidatos) == 1:
                ganador = candidatos[0]
                movimientos_validados[ganador] = destino
            else:
                ganador = random.choice(candidatos)
                movimientos_validados[ganador] = destino

        # 4. REEMPLAZO ATÓMICO
        pending.movements = movimientos_validados

        # 5. Aplicar gasto de energía por la acción de moverse
        self._apply_movement_energy_cost(state, pending)

    def _apply_movement_energy_cost(
        self,
        state: WorldState,
        pending: PendingChanges,
    ) -> None:
        """Aplica el gasto de energía a los agentes que realmente se movieron."""
        if not pending.movements:
            return

        for person in state.get_all_persons():
            if person.entity_id not in pending.movements:
                continue

            energy_cost = self._calculate_movement_cost(person)
            person.spend_energy(energy_cost)

    def _calculate_movement_cost(self, person) -> float:
        """Calcula el coste de energía de moverse 1 casilla."""
        cost = self.energy_cost_per_action
        size_factor = self._get_size_factor(person)
        cost *= size_factor

        movement_type_factor = self._get_movement_type_factor(person)
        cost *= movement_type_factor

        return max(0.0, cost)

    def _get_size_factor(self, person) -> float:
        """Obtiene el factor de tamaño basado en el genoma."""
        try:
            body_size = getattr(person.genome, "body_size", None)
            if body_size is not None:
                return 0.5 + (body_size * 1.5)
        except (AttributeError, TypeError):
            pass
        return 1.0

    def _get_movement_type_factor(self, person) -> float:
        """Obtiene el factor de tipo de movimiento basado en capacidades."""
        try:
            from systems.movement.movement_capabilities import MovementCapabilities
            capabilities = MovementCapabilities.from_genome(person.genome)
            if capabilities.can_fly:
                return 1.3
            elif capabilities.can_swim:
                return 1.1
            else:
                return 1.0
        except (AttributeError, TypeError, ImportError):
            pass
        return 1.0