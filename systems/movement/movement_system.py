"""Módulo responsable del movimiento táctico inmediato de cada agente.

Evalúa las celdas cercanas a cada individuo y decide el siguiente paso
basándose en un modelo de Utility AI que pondera:
- Recursos disponibles
- Carga viral (evitar epidemias)
- Densidad local (evitar hacinamiento)
- Proximidad social (acercarse a pareja/familia)
- Proximidad al destino migratorio (si existe)
- Personalidad (curiosidad, sociabilidad)

CORRECCIONES APLICADAS (Auditoría):
- Personalidad integrada (curiosity, sociability del genoma)
- Memoria espacial (preferred_sector)
- Penalización migratoria adaptativa (no ×10 fijo)
- Movimiento social ponderado por sociabilidad
- Ruido personal fijo para consistencia entre ticks
"""

import math
import random
import logging
from typing import Any, Dict, List, Tuple, Optional

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext


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
        self.eval_radius = getattr(config.movement, 'eval_radius', 3)
        
        # Umbral de distancia social (para acercarse a pareja/familia)
        self.social_distance = getattr(config.movement, 'social_distance', 10.0)

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
                self._move_towards_target(person, migration_target, max_x, max_y, pending)
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
        
        # Limitar a los bordes del mapa
        step_x = max(0, min(max_x, step_x))
        step_y = max(0, min(max_y, step_y))
        
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
        """Evalúa las celdas cercanas y selecciona la mejor usando Utility AI."""
        best_score = -float('inf')
        best_cell = None
        
        # CORRECCIÓN: Obtener rasgos de personalidad del genoma
        genome = person.genome
        curiosity = min(1.0, genome.curiosity / 2.0) if hasattr(genome, 'curiosity') else 0.5
        sociability = person.effective_sociability if hasattr(person, 'effective_sociability') else 0.5
        
        # CORRECCIÓN: Memoria espacial (preferred_sector)
        preferred_sector = None
        if hasattr(person, 'memory') and isinstance(person.memory, dict):
            preferred_sector = person.memory.get("preferred_sector", None)
        
        # CORRECCIÓN: Penalización migratoria adaptativa (no ×10 fijo)
        migration_target = pending.get_migration_target(person.entity_id)
        if migration_target is not None:
            migration_weight = 3.0  # Reducido de 10 a 3
        else:
            migration_weight = 0.0  # Sin destino migratorio, no hay penalización
        
        # Radio de evaluación
        radius = self.eval_radius
        
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue  # No evaluar la celda actual
                
                nx = person.x + dx
                ny = person.y + dy
                
                # Verificar límites del mapa
                if nx < 0 or nx > max_x or ny < 0 or ny > max_y:
                    continue
                
                # Calcular puntuación de la celda
                score = self._score_cell(
                    person=person,
                    cell_x=nx,
                    cell_y=ny,
                    state=state,
                    context=context,
                    curiosity=curiosity,
                    sociability=sociability,
                    preferred_sector=preferred_sector,
                    migration_weight=migration_weight,
                    migration_target=migration_target,
                )
                
                # CORRECCIÓN: Ruido personal fijo (consistencia entre ticks)
                personal_noise = (person.entity_id % 100) / 10000.0
                score += personal_noise
                
                if score > best_score:
                    best_score = score
                    best_cell = (nx, ny)
        
        return best_cell

    def _score_cell(
        self,
        person: Any,
        cell_x: int,
        cell_y: int,
        state: WorldState,
        context: EnvironmentContext,
        curiosity: float,
        sociability: float,
        preferred_sector: Optional[Tuple[int, int]],
        migration_weight: float,
        migration_target: Optional[Tuple[float, float]],
    ) -> float:
        """Calcula la puntuación de una celda usando Utility AI."""
        score = 0.0
        
        # 1. RECURSOS (atracción)
        resources = getattr(context, 'get_resources_at', lambda x, y: 0.5)(cell_x, cell_y)
        score += resources * 10.0
        
        # 2. CARGA VIRAL (repulsión)
        viral_load = self._get_viral_load(state, cell_x, cell_y)
        score -= viral_load * 15.0
        
        # 3. DENSIDAD LOCAL (repulsión)
        pressure = context.get_local_pressure(cell_x, cell_y)
        excess_pressure = max(0.0, pressure - 1.0)
        score -= excess_pressure * 8.0
        
        # 4. CORRECCIÓN: PROXIMIDAD SOCIAL (ponderada por sociabilidad)
        partner_id = getattr(person, 'partner_id', None)
        if partner_id is not None:
            partner = state.get_person_by_id(partner_id)
            if partner:
                dist_to_partner = math.hypot(person.x - partner.x, person.y - partner.y)
                dist_to_cell = math.hypot(cell_x - partner.x, cell_y - partner.y)
                
                # CORRECCIÓN: Ponderar por sociabilidad
                if dist_to_cell < dist_to_partner:
                    score += sociability * 5.0
                else:
                    score -= sociability * 2.0
        
        # 5. CORRECCIÓN: DISTANCIA AL DESTINO MIGRATORIO (adaptativa)
        if migration_target is not None:
            tx, ty = migration_target
            dist_to_migration = math.hypot(cell_x - tx, cell_y - ty)
            score -= dist_to_migration * migration_weight
        
        # 6. CORRECCIÓN: MEMORIA ESPACIAL (preferred_sector)
        if preferred_sector is not None:
            sector_size = self.config.environment.sector_size
            cell_sector = (cell_x // sector_size, cell_y // sector_size)
            if cell_sector == preferred_sector:
                score += 5.0
        
        # 7. CORRECCIÓN: BONUS POR EXPLORACIÓN (curiosity)
        distance_from_current = math.hypot(cell_x - person.x, cell_y - person.y)
        if curiosity > 0.6:
            score -= distance_from_current * 0.5 * (1.0 - curiosity)
        else:
            score -= distance_from_current * 1.0 * (1.0 - curiosity)
        
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