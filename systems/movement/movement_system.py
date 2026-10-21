"""Módulo responsable del movimiento táctico inmediato de cada agente.

Evalúa las celdas hexagonales cercanas a cada individuo y decide el siguiente 
paso basándose en un modelo de Utility AI que pondera recursos, carga viral, 
densidad local, proximidad social y personalidad.
"""

import logging
import math
from typing import Any, List, Optional, Tuple

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from core.taxonomy.profile_enums import DietType
from core.taxonomy.species_classification import SpeciesClassificationSystem
from systems.environment.environment_context import EnvironmentContext
from systems.movement.movement_capabilities import MovementCapabilities
from systems.social.social_pressure import SocialPressureCalculator
from systems.spatial.spatial_grid import SpatialGrid


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

        self.eval_radius = getattr(config.movement, "eval_radius", 1)
        self.social_distance = getattr(config.movement, "social_distance", 10.0)
        self.sector_size = getattr(config.environment, "sector_size", 10)
        self.social_pressure = SocialPressureCalculator(config)
        self.spatial_grid = SpatialGrid(cell_size=10.0)
        self.species_classification = SpeciesClassificationSystem.get_default()
        self.selection_temperature = getattr(config.movement, "selection_temperature", 2.0)
        
        self._threat_cache: dict = {}
        self._prey_cache: dict = {}
        self._vegetation_cache: dict = {}
        self._diet_cache: dict = {}

        # Direcciones hexagonales axiales (q, r)
        self.hex_directions = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Calcula el siguiente paso para cada agente activo."""
        max_q = state.width - 1
        max_r = state.height - 1

        self._threat_cache.clear()
        self._prey_cache.clear()
        self._vegetation_cache.clear()
        self._diet_cache.clear()
        
        self.spatial_grid.populate_from_state(state)

        for person in state.get_all_persons():
            if person.entity_id in pending.deaths:
                continue

            capabilities = MovementCapabilities.from_genome(person.genome)
            if not capabilities.can_move:
                continue

            if person.entity_id in pending.movements:
                continue

            migration_target = pending.get_migration_target(person.entity_id)
            if migration_target is not None:
                self._move_towards_target(
                    person, migration_target, max_q, max_r, pending, state, capabilities
                )
                continue

            best_move = self._evaluate_nearby_cells(
                person, state, context, max_q, max_r, pending, capabilities
            )

            if best_move is not None:
                pending.register_movement(person.entity_id, best_move[0], best_move[1])

    def _move_towards_target(
        self,
        person: Any,
        target: Tuple[float, float],
        max_q: int,
        max_r: int,
        pending: PendingChanges,
        state: WorldState,
        capabilities: MovementCapabilities,
    ) -> None:
        """Mueve al agente hacia su destino migratorio."""
        tq, tr = target
        dq = tq - person.q
        dr = tr - person.r

        # Distancia hexagonal
        distance = (abs(dq) + abs(dr) + abs(dq + dr)) // 2
        if distance < 1.0:
            return

        max_step = capabilities.movement_speed
        if capabilities.can_fly:
            max_step *= 1.5
        
        if distance <= max_step:
            step_q = int(round(tq))
            step_r = int(round(tr))
        else:
            step_q = int(round(person.q + (dq / max(distance, 1)) * max_step))
            step_r = int(round(person.r + (dr / max(distance, 1)) * max_step))

        # Wrapping toroidal en paralelogramo
        step_q = step_q % (max_q + 1)
        step_r = step_r % (max_r + 1)

        if state.is_cell_occupied(step_q, step_r):
            for d_q, d_r in self.hex_directions:
                alt_q = (step_q + d_q) % (max_q + 1)
                alt_r = (step_r + d_r) % (max_r + 1)
                if not state.is_cell_occupied(alt_q, alt_r):
                    pending.register_movement(person.entity_id, alt_q, alt_r)
                    return
            return

        pending.register_movement(person.entity_id, step_q, step_r)

    def _evaluate_nearby_cells(
        self,
        person: Any,
        state: WorldState,
        context: EnvironmentContext,
        max_q: int,
        max_r: int,
        pending: PendingChanges,
        capabilities: MovementCapabilities,
    ) -> Optional[Tuple[int, int]]:
        """Evalúa celdas cercanas y selecciona la mejor casilla disponible."""
        scored_cells: List[Tuple[Tuple[int, int], float]] = []
        radius = max(1, int(capabilities.vision_range))
        
        person_q = int(person.q)
        person_r = int(person.r)

        genome = person.genome
        curiosity = (
            min(1.0, genome.get_trait_value("curiosity") / 2.0)
            if genome.has_trait("curiosity")
            else 0.5
        )
        curiosity_factor = (
            0.5 * (1.0 - curiosity) if curiosity > 0.6 else 1.0 * (1.0 - curiosity)
        )

        memory = getattr(person, "memory", None)
        preferred_sector = memory.get("preferred_sector", None) if isinstance(memory, dict) else None

        migration_target = pending.get_migration_target(person.entity_id)
        migration_weight = 3.0 if migration_target else 0.0

        scored_cells.append(((person_q, person_r), 5.0))

        # Bucle de rango hexagonal
        for dq in range(-radius, radius + 1):
            dr_min = max(-radius, -dq - radius)
            dr_max = min(radius, -dq + radius)
            for dr in range(dr_min, dr_max + 1):
                if dq == 0 and dr == 0:
                    continue

                nq = (person_q + dq) % (max_q + 1)
                nr = (person_r + dr) % (max_r + 1)
                
                hex_dist = (abs(dq) + abs(dr) + abs(dq + dr)) // 2
                
                score = self._score_cell(
                    cell_q=nq,
                    cell_r=nr,
                    context=context,
                    state=state,
                    person=person,
                    migration_target=migration_target,
                    migration_weight=migration_weight,
                    preferred_sector=preferred_sector,
                    hex_dist=hex_dist,
                    curiosity_factor=curiosity_factor,
                    capabilities=capabilities,
                )
                scored_cells.append(((nq, nr), score))

        scored_cells.sort(key=lambda x: x[1], reverse=True)

        available_cells = []
        for cell, score in scored_cells:
            if cell == (person_q, person_r):
                available_cells.append((cell, score))
            elif not state.is_cell_occupied(cell[0], cell[1]):
                available_cells.append((cell, score))

        if not available_cells:
            return None

        selected = SocialPressureCalculator.probabilistic_selection(
            available_cells, temperature=self.selection_temperature
        )

        if selected == (person_q, person_r):
            return None

        return selected

    def _score_cell(
        self,
        cell_q: int,
        cell_r: int,
        context: EnvironmentContext,
        state: WorldState,
        person: Any,
        migration_target: Optional[Tuple[float, float]] = None,
        migration_weight: float = 0.0,
        preferred_sector: Optional[Tuple[int, int]] = None,
        hex_dist: int = 0,
        curiosity_factor: float = 1.0,
        capabilities: Optional[MovementCapabilities] = None,
    ) -> float:
        """Calcula la puntuación de una celda usando Utility AI."""
        score = 0.0

        score += context.get_resources_at(cell_q, cell_r) * 10.0
        score -= self._get_viral_load(state, cell_q, cell_r) * 15.0
        
        pressure = context.get_local_pressure(cell_q, cell_r)
        score -= max(0.0, pressure - 1.0) * 8.0

        score += self.social_pressure.calculate_pressure_for_cell(
            person, cell_q, cell_r, state
        )

        if migration_target is not None:
            mt_q, mt_r = migration_target
            dist_to_migration = (
                abs(cell_q - mt_q) + abs(cell_r - mt_r) + abs((cell_q - mt_q) + (cell_r - mt_r))
            ) // 2
            score -= dist_to_migration * migration_weight

        if preferred_sector is not None:
            cell_sector = (cell_q // self.sector_size, cell_r // self.sector_size)
            if cell_sector == preferred_sector:
                score += 5.0

        score -= hex_dist * curiosity_factor

        if capabilities is not None:
            diet = self._get_diet(person)
            
            if diet in ("herbivore", "omnivore"):
                threats = self._count_nearby_threats(person, state, capabilities)
                if threats > 0:
                    score -= threats * 25.0
            
            if diet in ("carnivore", "omnivore"):
                prey = self._count_nearby_prey(person, state, capabilities)
                if prey > 0:
                    score += prey * 15.0
            
            if diet == "herbivore":
                vegetation = self._count_nearby_vegetation(person, state, capabilities)
                if vegetation > 0:
                    score += vegetation * 20.0

        return score

    def _get_diet(self, person: Any) -> str:
        """Determina la dieta de un agente usando SpeciesClassificationSystem."""
        cached = self._diet_cache.get(person.entity_id)
        if cached is not None:
            return cached
        
        result = "omnivore"
        species_id = person.species
        diet_type = self.species_classification.get_diet(species_id)
        
        if diet_type is not None:
            diet_map = {
                DietType.CARNIVORE: "carnivore",
                DietType.HERBIVORE: "herbivore",
                DietType.OMNIVORE: "omnivore",
                DietType.PHOTOSYNTHETIC: "photosynthetic",
                DietType.INSECTIVORE: "carnivore",
                DietType.FILTER_FEEDER: "herbivore",
                DietType.PARASITE: "carnivore",
                DietType.DETRITIVORE: "omnivore",
                DietType.CHEMOSYNTHETIC: "photosynthetic",
            }
            result = diet_map.get(diet_type, "omnivore")
        else:
            try:
                diet_value = person.genome.get_trait_value("diet")
                if diet_value is not None:
                    if diet_value <= 0.1:
                        result = "photosynthetic"
                    elif diet_value <= 1.33:
                        result = "herbivore"
                    elif diet_value <= 2.33:
                        result = "omnivore"
                    else:
                        result = "carnivore"
            except (AttributeError, TypeError):
                pass
        
        self._diet_cache[person.entity_id] = result
        return result

    def _is_predator_of(self, predator: Any, prey: Any) -> bool:
        """Verifica si un agente es depredador de otro."""
        if predator.species == prey.species:
            return False
        
        predator_is_predator = self.species_classification.is_predator(predator.species)
        if not predator_is_predator:
            if self._get_diet(predator) not in ("carnivore", "omnivore"):
                return False
        
        if self._get_diet(prey) == "photosynthetic":
            return False
        
        return True

    def _count_nearby_threats(
        self, person: Any, state: WorldState, capabilities: MovementCapabilities
    ) -> int:
        """Cuenta depredadores cercanos a un agente."""
        detection_range = max(capabilities.vision_range, capabilities.smell_range)
        threats = 0
        person_q = int(person.q)
        person_r = int(person.r)
        
        for other in state.get_all_persons():
            if other.entity_id == person.entity_id:
                continue
            
            dq = int(other.q) - person_q
            dr = int(other.r) - person_r
            distance = (abs(dq) + abs(dr) + abs(dq + dr)) // 2
            
            if distance <= detection_range:
                if self._is_predator_of(other, person):
                    threats += 1
        
        return threats

    def _count_nearby_prey(
        self, person: Any, state: WorldState, capabilities: MovementCapabilities
    ) -> int:
        """Cuenta presas cercanas a un agente carnívoro/omnívoro."""
        cached = self._prey_cache.get(person.entity_id)
        if cached is not None:
            return cached
        
        detection_range = max(capabilities.vision_range, capabilities.smell_range)
        prey_count = 0
        nearby_agents = self.spatial_grid.get_nearby_agents(person, radius=detection_range)
        
        for other in nearby_agents:
            if self._is_predator_of(person, other):
                prey_count += 1
        
        self._prey_cache[person.entity_id] = prey_count
        return prey_count

    def _count_nearby_vegetation(
        self, person: Any, state: WorldState, capabilities: MovementCapabilities
    ) -> int:
        """Cuenta vegetación cercana a un agente herbívoro."""
        cached = self._vegetation_cache.get(person.entity_id)
        if cached is not None:
            return cached
        
        detection_range = max(capabilities.vision_range, capabilities.smell_range)
        veg_count = 0
        nearby_agents = self.spatial_grid.get_nearby_agents(person, radius=detection_range)
        
        for other in nearby_agents:
            if self._get_diet(other) == "photosynthetic":
                veg_count += 1
        
        self._vegetation_cache[person.entity_id] = veg_count
        return veg_count

    @staticmethod
    def _get_viral_load(state: WorldState, q: int, r: int) -> float:
        """Obtiene la carga viral de una celda específica."""
        ep_map = getattr(state, "epidemiological_map", None)
        if not ep_map:
            return 0.0

        try:
            raw_val = None
            if hasattr(ep_map, "get_load_at"):
                raw_val = ep_map.get_load_at(q, r)
            elif hasattr(ep_map, "_cells") and isinstance(ep_map._cells, dict):
                raw_val = ep_map._cells.get((int(q), int(r)), 0)

            if isinstance(raw_val, (int, float)):
                return float(raw_val)
        except Exception:
            pass

        return 0.0