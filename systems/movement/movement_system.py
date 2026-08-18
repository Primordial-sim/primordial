"""Módulo responsable del movimiento táctico inmediato de cada agente.

Evalúa las celdas cercanas a cada individuo y decide el siguiente paso
basándose en un modelo de Utility AI que pondera:
- Recursos disponibles
- Carga viral (evitar epidemias)
- Densidad local (evitar hacinamiento)
- Proximidad social (acercarse a pareja/familia)
- Presión social (FASE B)
- Proximidad al núcleo residencial (FASE B)
- Proximidad al destino migratorio (si existe)
- Personalidad (curiosidad, sociabilidad)
- Selección probabilística (FASE B)
- Ocupación de casillas (FASE C)

CORRECCIONES APLICADAS (Auditoría):
- Personalidad integrada (curiosity, sociability del genoma)
- Memoria espacial (preferred_sector)
- Penalización migratoria adaptativa (no ×10 fijo)
- Movimiento social ponderado por sociabilidad
- Ruido personal fijo para consistencia entre ticks

FASE B: Presión social y selección probabilística
FASE C: Ocupación estricta de casillas (1 agente = 1 casilla)
"""

import math
import random
import logging
from typing import Any, Dict, List, Tuple, Optional

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext
from systems.social.social_pressure import SocialPressureCalculator


class MovementSystem:
    """Sistema de movimiento táctico que decide el paso inmediato de cada agente."""

    def __init__(
        self,
        config: SimulationConfig,
        density_system: Any = None,
        relationship_engine: Any = None,
    ) -> None:
        """Inicializa el sistema de movimiento táctico."""
        self.config = config
        self.density_system = density_system
        self.relationship_engine = relationship_engine
        self.logger = logging.getLogger(self.__class__.__name__)

        # Radio de evaluación de celdas cercanas
        self.eval_radius = getattr(config.movement, 'eval_radius', 1)

        # Umbral de distancia social (para acercarse a pareja/familia)
        self.social_distance = getattr(config.movement, 'social_distance', 10.0)

        # Tamaño de sector para memoria espacial
        self.sector_size = getattr(config.environment, 'sector_size', 10)

        # FASE B: Calculadora de presión social
        self.social_pressure = SocialPressureCalculator(config)

        # Temperatura para selección probabilística
        # Baja (0.5) → comportamiento más determinista
        # Alta (5.0) → comportamiento más aleatorio
        self.selection_temperature = getattr(config.movement, 'selection_temperature', 2.0)

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Calcula el siguiente paso para cada agente activo."""
        max_x = state.width - 1
        max_y = state.height - 1

        for person in state.get_all_persons():
            if person.entity_id in pending.deaths:
                continue

            # Si ya tiene un movimiento registrado por otro sistema, no sobrescribir
            if person.entity_id in pending.movements:
                continue

            # Si tiene un destino migratorio activo, moverse hacia él
            migration_target = pending.get_migration_target(person.entity_id)
            if migration_target is not None:
                self._move_towards_target(person, migration_target, max_x, max_y, pending, state)
                continue

            # Evaluar celdas cercanas usando Utility AI
            best_move = self._evaluate_nearby_cells(person, state, context, max_x, max_y, pending)

            if best_move is not None:
                pending.register_movement(person.entity_id, best_move[0], best_move[1])

    def _move_towards_target(
        self,
        person: Any,
        target: Tuple[float, float],
        max_x: int,
        max_y: int,
        pending: PendingChanges,
        state: WorldState,
    ) -> None:
        """Mueve al agente hacia su destino migratorio."""
        tx, ty = target

        # Calcular dirección hacia el destino
        dx = tx - person.x
        dy = ty - person.y

        # Normalizar a un paso unitario
        distance = math.hypot(dx, dy)
        if distance < 1.0:
            return  # Ya está muy cerca

        # Paso unitario hacia el destino
        step_x = int(round(person.x + dx / distance))
        step_y = int(round(person.y + dy / distance))

        # Envolver como toroide (esfera): si sale por un lado, aparece por el otro
        step_x = step_x % (max_x + 1)
        step_y = step_y % (max_y + 1)

        # FASE C: Verificar que la casilla destino no esté ocupada
        if state.is_cell_occupied(step_x, step_y):
            # Intentar casillas adyacentes al destino
            for offset_x, offset_y in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]:
                alt_x = (step_x + offset_x) % (max_x + 1)
                alt_y = (step_y + offset_y) % (max_y + 1)
                if not state.is_cell_occupied(alt_x, alt_y):
                    pending.register_movement(person.entity_id, alt_x, alt_y)
                    return
            # Si todas están ocupadas, no moverse
            return

        pending.register_movement(person.entity_id, step_x, step_y)

    def _evaluate_nearby_cells(
        self,
        person: Any,
        state: WorldState,
        context: EnvironmentContext,
        max_x: int,
        max_y: int,
        pending: PendingChanges,
    ) -> Optional[Tuple[int, int]]:
        """Evalúa celdas cercanas y selecciona la mejor casilla disponible.

        FASE C: Verifica ocupación antes de seleccionar.
        Incluye la opción de quedarse quieto (casilla actual).
        """
        scored_cells: List[Tuple[Tuple[int, int], float]] = []

        radius = self.eval_radius
        person_x = int(person.x)
        person_y = int(person.y)

        # Precalcular valores constantes
        # GENÉTICA UNIVERSAL: API genérica agnóstica a especie
        genome = person.genome
        curiosity = min(1.0, genome.get_trait_value("curiosity") / 2.0) if genome.has_trait("curiosity") else 0.5
        curiosity_factor = 0.5 * (1.0 - curiosity) if curiosity > 0.6 else 1.0 * (1.0 - curiosity)
        
        # TODO (Fase 3): Consultar rasgos específicos de movimiento
        # - flight > 0.3: puede saltar obstáculos o moverse a mayor radio
        # - swimming > 0.3: puede atravesar zonas acuáticas
        # - burrowing > 0.3: puede moverse bajo tierra
        # - speed: factor de multiplicación de distancia de movimiento
        # Estos se implementarán cuando se diseñen los biomas/terrenos.

        preferred_sector = None
        memory = getattr(person, 'memory', None)
        if memory is not None and isinstance(memory, dict):
            preferred_sector = memory.get("preferred_sector", None)

        migration_target = pending.get_migration_target(person.entity_id)
        migration_weight = 3.0 if migration_target else 0.0

        # FASE C: Incluir la casilla actual como opción (quedarse quieto)
        # La casilla actual tiene una puntuación ligeramente positiva
        # para que el agente no se mueva innecesariamente
        current_cell_score = 5.0  # Bonus por no moverse (inercia)
        scored_cells.append(((person_x, person_y), current_cell_score))

        # Evaluar casillas vecinas
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue  # La casilla actual ya fue añadida arriba

                nx = person_x + dx
                ny = person_y + dy

                # Envolver coordenadas como toroide
                nx = nx % (max_x + 1)
                ny = ny % (max_y + 1)
                
                score = self._score_cell(
                    cell_x=nx,
                    cell_y=ny,
                    context=context,
                    state=state,
                    person=person,
                    migration_target=migration_target,
                    migration_weight=migration_weight,
                    preferred_sector=preferred_sector,
                    dx=dx,
                    dy=dy,
                    curiosity_factor=curiosity_factor,
                )

                scored_cells.append(((nx, ny), score))

        # FASE C: Ordenar por puntuación (mayor primero)
        scored_cells.sort(key=lambda x: x[1], reverse=True)

        # FASE C: Filtrar casillas ocupadas (excepto la actual del agente)
        available_cells = []
        for cell, score in scored_cells:
            if cell == (person_x, person_y):
                # La casilla actual siempre está disponible para este agente
                available_cells.append((cell, score))
            elif not state.is_cell_occupied(cell[0], cell[1]):
                available_cells.append((cell, score))
            # Si está ocupada por otro agente, la descartamos

        if not available_cells:
            # No hay casillas disponibles, el agente se queda quieto
            return None

        # FASE B: Selección probabilística entre las casillas disponibles
        selected = SocialPressureCalculator.probabilistic_selection(
            available_cells, temperature=self.selection_temperature
        )

        # Si la casilla seleccionada es la actual, retornar None (quedarse quieto)
        if selected == (person_x, person_y):
            return None

        return selected

    def _score_cell(
        self,
        cell_x: int,
        cell_y: int,
        context: EnvironmentContext,
        state: WorldState,
        person: Any,
        migration_target: Optional[Tuple[float, float]] = None,
        migration_weight: float = 0.0,
        preferred_sector: Optional[Tuple[int, int]] = None,
        dx: int = 0,
        dy: int = 0,
        curiosity_factor: float = 1.0,
    ) -> float:
        """Calcula la puntuación de una celda usando Utility AI.

        FASE B: Incluye presión social y proximidad al núcleo.
        """
        score = 0.0

        # 1. RECURSOS (atracción)
        resources = context.get_resources_at(cell_x, cell_y)
        score += resources * 10.0

        # 2. CARGA VIRAL (repulsión)
        viral_load = self._get_viral_load(state, cell_x, cell_y)
        score -= viral_load * 15.0

        # 3. DENSIDAD LOCAL (repulsión)
        pressure = context.get_local_pressure(cell_x, cell_y)
        excess_pressure = max(0.0, pressure - 1.0)
        score -= excess_pressure * 8.0

        # 4. PRESIÓN SOCIAL (FASE B)
        social_press = self.social_pressure.calculate_pressure_for_cell(
            person, cell_x, cell_y, state
        )
        score += social_press

        # 5. DISTANCIA AL DESTINO MIGRATORIO (adaptativa)
        if migration_target is not None:
            mt_x, mt_y = migration_target
            dist_to_migration = math.sqrt((cell_x - mt_x) ** 2 + (cell_y - mt_y) ** 2)
            score -= dist_to_migration * migration_weight

        # 6. MEMORIA ESPACIAL (preferred_sector)
        if preferred_sector is not None:
            cell_sector = (cell_x // self.sector_size, cell_y // self.sector_size)
            if cell_sector == preferred_sector:
                score += 5.0

        # 7. COSTE POR DISTANCIA (curiosity)
        distance_from_current = math.sqrt(dx * dx + dy * dy)
        score -= distance_from_current * curiosity_factor

        return score

    @staticmethod
    def _get_viral_load(state: WorldState, x: int, y: int) -> float:
        """Obtiene la carga viral de una celda específica."""
        ep_map = getattr(state, 'epidemiological_map', None)
        if not ep_map:
            return 0.0

        try:
            raw_val = None
            if hasattr(ep_map, 'get_load_at'):
                raw_val = ep_map.get_load_at(x, y)
            elif hasattr(ep_map, '_cells') and isinstance(ep_map._cells, dict):
                raw_val = ep_map._cells.get((int(x), int(y)), 0)

            if isinstance(raw_val, (int, float)):
                return float(raw_val)
        except Exception:
            pass

        return 0.0