"""Módulo responsable de arbitrar colisiones espaciales antes del commit global.

CAMBIOS RECIENTES:
- Gasto de energía por movimiento: Cada agente que realmente se mueve
  gasta energía. Como cada movimiento es exactamente una casilla por tick,
  el coste es un valor fijo por "acción" y se modifica por el tamaño y 
  tipo de movimiento de la especie (no por distancia física).
"""

import random
import logging
from typing import Dict, List, Tuple, Set
from core.state.world_state import WorldState
from core.state.pending_changes import PendingChanges
from systems.environment.environment_context import EnvironmentContext
from core.config.simulation_config import SimulationConfig

class MovementResolver:
    """Resuelve cuellos de botella espaciales de forma determinista.
    
    Asegura que dos entidades no ocupen la misma celda si el motor no lo permite,
    operando como un sistema estándar dentro del ciclo de la simulación.
    
    RESPONSABILIDADES:
    - Resolver conflictos de ocupación espacial.
    - Aplicar gasto de energía por la acción de moverse (1 casilla = 1 acción).
    """

    def __init__(self, config: SimulationConfig) -> None:
        """Inicializa el resolutor cumpliendo el contrato de la arquitectura.
        
        Args:
            config (SimulationConfig): Configuración maestra de la simulación.
        """
        self.config = config
        self.logger = logging.getLogger("MovementResolver")
        
        # Parámetros de gasto de energía por movimiento
        # Como cada tick es 1 casilla, es un coste base por la "acción" de moverse.
        self.energy_cost_per_action: float = 0.2  # Energía gastada por moverse 1 casilla

    def process(self, state: WorldState, pending: PendingChanges, 
                delta_days: float, context: EnvironmentContext) -> None:
        """Analiza las intenciones de movimiento y evita solapamientos espaciales.
        
        Args:
            state (WorldState): Estado centralizado del mundo.
            pending (PendingChanges): Búfer transaccional de mutaciones.
            delta_days (float): Paso de tiempo en días.
            context (EnvironmentContext): Contexto espacial y medioambiental.
        """
        
        # Aborto temprano si no hay movimientos solicitados en el búfer
        if not getattr(pending, 'movements', None):
            return 

        # 1. Identificar casillas bloqueadas (ocupadas por individuos estáticos)
        casillas_bloqueadas: Set[Tuple[int, int]] = set()
        for person in state.get_all_persons():
            # Regla de seguridad 1: Nunca considerar a los individuos muertos
            if person.entity_id in pending.deaths:
                continue 
                
            # Si la persona no se mueve en este tick, su casilla actual es un obstáculo duro
            if person.entity_id not in pending.movements:
                casillas_bloqueadas.add((person.x, person.y))

        # 2. Agrupar peticiones por celda destino y aplicar Fail-Safes
        peticiones_por_celda: Dict[Tuple[int, int], List[int]] = {} 
        
        for entity_id, (target_x, target_y) in pending.movements.items():
            # Regla de seguridad 1 (Doble validación): Garantizar que la entidad no ha fallecido
            if entity_id in pending.deaths:
                continue

            # Regla de seguridad 2: Nunca salir de los límites del mapa (Clamping estricto)
            final_x = max(0, min(int(target_x), state.width - 1))
            final_y = max(0, min(int(target_y), state.height - 1))
            destino = (final_x, final_y)
            
            if destino not in peticiones_por_celda:
                peticiones_por_celda[destino] = []
            peticiones_por_celda[destino].append(entity_id)

        # 3. Arbitrar conflictos y respetar ocupaciones (Regla de objetivos y velocidades)
        movimientos_validados: Dict[int, Tuple[int, int]] = {}
        
        for destino, candidatos in peticiones_por_celda.items():
            # REGLA A: Destino bloqueado por una entidad estática
            if destino in casillas_bloqueadas:
                # El movimiento se cancela; las entidades se quedan en su posición de origen
                continue

            # REGLA B: Celda libre o disputa entre varios agentes en movimiento
            if len(candidatos) == 1:
                ganador = candidatos[0]
                movimientos_validados[ganador] = destino
            else:
                # CONFLICTO: Varios agentes quieren la misma celda. Se resuelve al azar para evitar sesgos de ID.
                ganador = random.choice(candidatos)
                movimientos_validados[ganador] = destino

        # 4. REEMPLAZO ATÓMICO: Sobrescribimos el búfer solo con los movimientos validados y aprobados
        pending.movements = movimientos_validados
        
        # 5. Aplicar gasto de energía por la acción de moverse
        self._apply_movement_energy_cost(state, pending)

    def _apply_movement_energy_cost(
        self,
        state: WorldState,
        pending: PendingChanges,
    ) -> None:
        """Aplica el gasto de energía a los agentes que realmente se movieron.
        
        Como cada movimiento aprobado representa exactamente 1 casilla (1 tick),
        no calculamos distancias físicas. Simplemente aplicamos un coste por acción,
        modificado por las capacidades biológicas del agente.
        
        Args:
            state (WorldState): Estado centralizado del mundo.
            pending (PendingChanges): Búfer transaccional de mutaciones.
        """
        if not pending.movements:
            return
        
        for person in state.get_all_persons():
            # Solo procesar agentes cuyo movimiento fue validado
            if person.entity_id not in pending.movements:
                continue
            
            # Calcular coste basado en la especie (tamaño, tipo de movimiento)
            energy_cost = self._calculate_movement_cost(person)
            
            # Aplicar el gasto de energía
            person.spend_energy(energy_cost)

    def _calculate_movement_cost(self, person) -> float:
        """Calcula el coste de energía de moverse 1 casilla.
        
        Args:
            person: El agente que se mueve.
            
        Returns:
            Cantidad de energía a gastar.
        """
        # Coste base por la acción de moverse
        cost = self.energy_cost_per_action
        
        # Modificador por tamaño corporal (más masa = más energía para moverse)
        size_factor = self._get_size_factor(person)
        cost *= size_factor
        
        # Modificador por tipo de movimiento (volar/nadar tiene costes distintos)
        movement_type_factor = self._get_movement_type_factor(person)
        cost *= movement_type_factor
        
        return max(0.0, cost)

    def _get_size_factor(self, person) -> float:
        """Obtiene el factor de tamaño basado en el genoma."""
        try:
            body_size = getattr(person.genome, 'body_size', None)
            if body_size is not None:
                # Rango aproximado: 0.5 (pequeño) a 2.0 (grande)
                return 0.5 + (body_size * 1.5)
        except (AttributeError, TypeError):
            pass
        
        return 1.0  # Por defecto: tamaño medio

    def _get_movement_type_factor(self, person) -> float:
        """Obtiene el factor de tipo de movimiento basado en capacidades."""
        try:
            from systems.movement.movement_capabilities import MovementCapabilities
            capabilities = MovementCapabilities.from_genome(person.genome)
            
            if capabilities.can_fly:
                return 1.3  # Volar requiere más energía constante
            elif capabilities.can_swim:
                return 1.1  # Nadar tiene resistencia del agua
            else:
                return 1.0  # Caminar es el coste base
        except (AttributeError, TypeError, ImportError):
            pass
        
        return 1.0  # Por defecto