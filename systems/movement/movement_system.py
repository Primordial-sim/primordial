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
- Penalización migratoria adaptativa
- Movimiento social ponderado por sociabilidad
- Ruido personal fijo para consistencia entre ticks

FASE B: Presión social y selección probabilística
FASE C: Ocupación estricta de casillas (1 agente = 1 casilla)
"""

import math
import logging
from typing import Any, List, Tuple, Optional, Dict

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext
from systems.social.social_pressure import SocialPressureCalculator
from systems.movement.movement_capabilities import MovementCapabilities
from systems.spatial.spatial_grid import SpatialGrid
from core.taxonomy.species_classification import SpeciesClassificationSystem
from core.taxonomy.profile_enums import DietType
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
        
        # OPTIMIZACIÓN: Grid espacial para búsquedas de vecinos O(k)
        self.spatial_grid = SpatialGrid(cell_size=10.0)
        
        # Sistema de clasificación de especies (consulta perfiles biológicos)
        self.species_classification = SpeciesClassificationSystem.get_default()

        # Temperatura para selección probabilística
        self.selection_temperature = getattr(config.movement, 'selection_temperature', 2.0)
        
        # Caché de detección ecológica por tick (evita recalcular por cada celda)
        self._threat_cache = {}
        self._prey_cache = {}
        self._vegetation_cache = {}
        self._diet_cache = {}

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

            # NUEVO: Resetear caché de detección ecológica cada tick
        self._threat_cache.clear()
        self._prey_cache.clear()
        self._vegetation_cache.clear()
        self._diet_cache.clear()
        
        # OPTIMIZACIÓN: Poblar el grid espacial una vez por tick
        self.spatial_grid.populate_from_state(state)

        for person in state.get_all_persons():
            if person.entity_id in pending.deaths:
                continue

            # GENÉTICA UNIVERSAL: Consultar capacidades de movimiento del genoma
            # Si no puede moverse (plantas, organismos sésiles), saltar
            capabilities = MovementCapabilities.from_genome(person.genome)
            if not capabilities.can_move:
                continue

            # Si ya tiene un movimiento registrado por otro sistema, no sobrescribir
            if person.entity_id in pending.movements:
                continue

            # Si tiene un destino migratorio activo, moverse hacia él
            migration_target = pending.get_migration_target(person.entity_id)
            if migration_target is not None:
                self._move_towards_target(person, migration_target, max_x, max_y, pending, state, capabilities)
                continue

            # Evaluar celdas cercanas usando Utility AI
            best_move = self._evaluate_nearby_cells(person, state, context, max_x, max_y, pending, capabilities)

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
        capabilities: MovementCapabilities,
    ) -> None:
        """Mueve al agente hacia su destino migratorio.
        
        GENÉTICA UNIVERSAL: Usa capabilities.movement_speed para determinar
        la distancia máxima de movimiento por tick.
        """
        tx, ty = target

        # Calcular dirección hacia el destino
        dx = tx - person.x
        dy = ty - person.y

        # Normalizar a un paso unitario
        distance = math.hypot(dx, dy)
        if distance < 1.0:
            return  # Ya está muy cerca

        # GENÉTICA UNIVERSAL: Distancia máxima según speed del genoma
        max_step = capabilities.movement_speed
        
        # Si puede volar, puede moverse más lejos por tick
        if capabilities.can_fly:
            max_step *= 1.5
        
        # Si la distancia es menor que el paso máximo, moverse directamente
        if distance <= max_step:
            step_x = int(round(tx))
            step_y = int(round(ty))
        else:
            # Paso proporcional a la distancia máxima
            step_x = int(round(person.x + (dx / distance) * max_step))
            step_y = int(round(person.y + (dy / distance) * max_step))

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
        capabilities: MovementCapabilities,
    ) -> Optional[Tuple[int, int]]:
        """Evalúa celdas cercanas y selecciona la mejor casilla disponible.

        FASE C: Verifica ocupación antes de seleccionar.
        Incluye la opción de quedarse quieto (casilla actual).
        
        GENÉTICA UNIVERSAL: Usa capabilities.vision_range para determinar
        el radio de evaluación.
        """
        scored_cells: List[Tuple[Tuple[int, int], float]] = []

        # GENÉTICA UNIVERSAL: Radio de evaluación según visión del genoma
        # Visión alta = evalúa más lejos, visión baja = evalúa más cerca
        radius = max(1, int(capabilities.vision_range))
        
        person_x = int(person.x)
        person_y = int(person.y)

        # Precalcular valores constantes
        # GENÉTICA UNIVERSAL: API genérica agnóstica a especie
        genome = person.genome
        curiosity = min(1.0, genome.get_trait_value("curiosity") / 2.0) if genome.has_trait("curiosity") else 0.5
        curiosity_factor = 0.5 * (1.0 - curiosity) if curiosity > 0.6 else 1.0 * (1.0 - curiosity)

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
                    capabilities=capabilities,
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
        capabilities: Optional[MovementCapabilities] = None,
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

        # 8. ECOLOGÍA - Detección de amenazas, presas y vegetación
        if capabilities is not None:
            diet = self._get_diet(person)
            
            # 8a. REPULSIÓN POR DEPREDADORES (para presas)
            # Si el agente es herbívoro u omnívoro, evita depredadores
            if diet in ("herbivore", "omnivore"):
                threats = self._count_nearby_threats(person, state, capabilities)
                if threats > 0:
                    # Repulsión fuerte: los depredadores son peligrosos
                    score -= threats * 25.0
            
            # 8b. ATRACCIÓN POR PRESAS (para carnívoros)
            # Si el agente es carnívoro u omnívoro, busca presas
            if diet in ("carnivore", "omnivore"):
                prey = self._count_nearby_prey(person, state, capabilities)
                if prey > 0:
                    # Atracción moderada: las presas son comida
                    score += prey * 15.0
            
            # 8c. ATRACCIÓN POR VEGETACIÓN (para herbívoros)
            # Si el agente es herbívoro, busca plantas
            if diet == "herbivore":
                vegetation = self._count_nearby_vegetation(person, state, capabilities)
                if vegetation > 0:
                    # Atracción fuerte: la vegetación es comida principal
                    score += vegetation * 20.0

        return score

    # =========================================================================
    # DETECCIÓN ECOLÓGICA (DEPREDADORES, PRESAS, VEGETACIÓN)
    # =========================================================================

    def _get_diet(self, person: Any) -> str:
        """Determina la dieta de un agente usando SpeciesClassificationSystem.
        
        Prioridad:
        1. Perfil biológico de la especie (SpeciesClassificationSystem)
        2. Rasgo genético "diet" (fallback)
        3. Omnívoro por defecto
        
        Args:
            person: El agente.
            
        Returns:
            String: "herbivore", "carnivore", "omnivore", "photosynthetic"
        """
        # Verificar caché primero
        cached = self._diet_cache.get(person.entity_id)
        if cached is not None:
            return cached
        
        result = "omnivore"  # Default
        
        # 1. Intentar obtener del perfil biológico de la especie
        species_id = person.species
        diet_type = self.species_classification.get_diet(species_id)
        
        if diet_type is not None:
            # Convertir DietType enum a string
            if diet_type == DietType.CARNIVORE:
                result = "carnivore"
            elif diet_type == DietType.HERBIVORE:
                result = "herbivore"
            elif diet_type == DietType.OMNIVORE:
                result = "omnivore"
            elif diet_type == DietType.PHOTOSYNTHETIC:
                result = "photosynthetic"
            elif diet_type == DietType.INSECTIVORE:
                result = "carnivore"  # Insectívoros son carnívoros especializados
            elif diet_type == DietType.FILTER_FEEDER:
                result = "herbivore"  # Filtradores consumen plancton
            elif diet_type == DietType.PARASITE:
                result = "carnivore"  # Parásitos consumen otros organismos
            elif diet_type == DietType.DETRITIVORE:
                result = "omnivore"  # Descomponedores consumen materia orgánica
            elif diet_type == DietType.CHEMOSYNTHETIC:
                result = "photosynthetic"  # Similar a fotosintéticos
        else:
            # 2. Fallback: consultar rasgo genético "diet"
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
        
        # Guardar en caché y retornar
        self._diet_cache[person.entity_id] = result
        return result

    def _is_predator_of(self, predator: Any, prey: Any) -> bool:
        """Verifica si un agente es depredador de otro.
        
        Usa SpeciesClassificationSystem para verificar:
        1. Si el predador es un depredador (perfil biológico)
        2. Si la presa no es fotosintética
        3. Si son de especies diferentes
        
        Args:
            predator: El posible depredador.
            prey: La posible presa.
            
        Returns:
            True si el primero puede depredar al segundo.
        """
        # No se depredan a sí mismos (misma especie)
        if predator.species == prey.species:
            return False
        
        # Verificar si el predador es un depredador según su perfil biológico
        predator_is_predator = self.species_classification.is_predator(predator.species)
        
        # Si el perfil no está disponible, usar la dieta
        if not predator_is_predator:
            predator_diet = self._get_diet(predator)
            if predator_diet not in ("carnivore", "omnivore"):
                return False
        
        # No pueden depredar plantas
        prey_diet = self._get_diet(prey)
        if prey_diet == "photosynthetic":
            return False
        
        return True

    def _count_nearby_threats(
        self,
        person: Any,
        state: WorldState,
        capabilities: MovementCapabilities,
    ) -> int:
        """Cuenta depredadores cercanos a un agente.
        
        Args:
            person: El agente que busca amenazas.
            state: Estado del mundo.
            capabilities: Capacidades de movimiento (para rango de visión/olfato).
            
        Returns:
            Número de depredadores detectados.
        """
        # Rango de detección basado en visión y olfato
        detection_range = max(capabilities.vision_range, capabilities.smell_range)
        
        threats = 0
        person_x = int(person.x)
        person_y = int(person.y)
        
        # Buscar agentes cercanos iterando sobre todos (O(N) pero seguro)
        for other in state.get_all_persons():
            if other.entity_id == person.entity_id:
                continue
            
            # Calcular distancia
            dx = int(other.x) - person_x
            dy = int(other.y) - person_y
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance <= detection_range:
                if self._is_predator_of(other, person):
                    threats += 1
        
        return threats

    def _count_nearby_prey(
        self,
        person: Any,
        state: WorldState,
        capabilities: MovementCapabilities,
    ) -> int:
        """Cuenta presas cercanas a un agente carnívoro/omnívoro (con caché y SpatialGrid)."""
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
        self,
        person: Any,
        state: WorldState,
        capabilities: MovementCapabilities,
    ) -> int:
        """Cuenta vegetación cercana a un agente herbívoro (con caché y SpatialGrid)."""
        cached = self._vegetation_cache.get(person.entity_id)
        if cached is not None:
            return cached
        
        detection_range = max(capabilities.vision_range, capabilities.smell_range)
        
        veg_count = 0
        nearby_agents = self.spatial_grid.get_nearby_agents(person, radius=detection_range)
        
        for other in nearby_agents:
            other_diet = self._get_diet(other)
            if other_diet == "photosynthetic":
                veg_count += 1
        
        self._vegetation_cache[person.entity_id] = veg_count
        return veg_count

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