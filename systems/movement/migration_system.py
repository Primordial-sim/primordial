"""Módulo responsable de gestionar las migraciones masivas a larga distancia.

Identifica factores de expulsión (push factors: hambre, epidemias, clima hostil,
superpoblación, TRAUMA EMOCIONAL) y factores de atracción (pull factors: oportunidades de recursos).
Asigna vectores de migración que anulan el comportamiento sedentario normal.

CORRECCIONES APLICADAS (Auditoría):
- Reevaluación periódica del destino migratorio (cada 30 días)
- Invalidación si el destino se vuelve peligroso
- Número de muestras configurable (default 20 en lugar de 5)
- Establecimiento al llegar (memoria positiva + reducción de motivación)
- Integración con trauma_abandonment y trauma_adoption

BLOQUE 3: Trauma Global Sistémico
- El trauma de abandono y adopción actúan como potentes factores de expulsión.
"""

import math
import random
import logging
from typing import Any, Dict, List, Tuple, Optional

from core.state.world_state import WorldState
from core.state.pending_changes import PendingChanges
from systems.behavior.cognitive_memory_system import CognitiveMemorySystem
from systems.environment.environment_context import EnvironmentContext
from core.config.simulation_config import SimulationConfig
from systems.movement.movement_capabilities import MovementCapabilities


class MigrationSystem:
    """Sistema que evalúa la necesidad de emigrar y calcula rutas de escape lejanas."""

    def __init__(self, config: SimulationConfig) -> None:
        """Inicializa el gestor de migraciones."""
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.arrival_threshold: float = 5.0
        
        # CORRECCIÓN: Intervalo de reevaluación del destino (en días simulados)
        self.reevaluation_interval: float = getattr(
            config.free_will, 'migration_reevaluation_days', 30.0
        )
        
        # Los cooldowns se mantienen aquí porque son estado interno del sistema
        self._cooldowns: Dict[int, float] = {}
        
        # CORRECCIÓN: Rastrear cuándo se estableció el destino actual para reevaluación
        self._target_set_day: Dict[int, float] = {}

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Evalúa las condiciones locales de cada agente y asigna destinos de migración."""
        max_x = state.width - 1
        max_y = state.height - 1

        current_day = getattr(state, 'world_days_elapsed', 0.0)
        
        fw_cfg = self.config.free_will
        migration_cooldown = getattr(fw_cfg, 'migration_cooldown_days', 90.0)
        
        # CORRECCIÓN: Número de muestras configurable (antes era 5 fijo)
        migration_samples = getattr(fw_cfg, 'migration_samples', 20)

        for person in state.get_all_persons():
            eid = person.entity_id
            
            # 1. INTEGRIDAD DE ESTADO
            if eid in pending.deaths:
                self._cooldowns.pop(eid, None)
                self._target_set_day.pop(eid, None)
                continue

            # GENÉTICA UNIVERSAL: Consultar capacidades de movimiento del genoma
            # Si no puede moverse o no puede migrar, saltar
            capabilities = MovementCapabilities.from_genome(person.genome)
            if not capabilities.can_move or not capabilities.can_migrate:
                continue

            # 2. VERIFICAR COOLDOWN
            last_migration = self._cooldowns.get(eid, 0.0)
            if (current_day - last_migration) < migration_cooldown:
                continue

            # 3. SEGUIMIENTO DE MIGRACIÓN ACTIVA
            target = pending.get_migration_target(eid)
            if target is not None:
                tx, ty = target
                
                # CORRECCIÓN: Reevaluar destino periódicamente
                target_day = self._target_set_day.get(eid, 0.0)
                if (current_day - target_day) >= self.reevaluation_interval:
                    # Verificar si el destino sigue siendo viable
                    if not self._is_target_still_valid(tx, ty, context, state):
                        # Destino ya no es viable: invalidar y buscar nuevo destino
                        pending.clear_migration_target(eid)
                        self._target_set_day.pop(eid, None)
                        self.logger.debug(
                            "🔄 Agente %s: destino migratorio invalidado, buscando nuevo destino",
                            eid,
                        )
                        # Continuar para buscar un nuevo destino en este tick
                    else:
                        # Destino sigue válido: continuar hacia él
                        dist = math.hypot(person.x - tx, person.y - ty)
                
                        # GENÉTICA UNIVERSAL: Umbral de llegada ajustado por speed
                        arrival_threshold = self.arrival_threshold * capabilities.movement_speed
                
                        if dist <= arrival_threshold:
                            # CORRECCIÓN: Establecimiento al llegar
                            self._handle_arrival(person, tx, ty, current_day, pending, fw_cfg)
                            pending.clear_migration_target(eid)
                            self._target_set_day.pop(eid, None)
                        continue
                else:
                    # Aún no toca reevaluar: continuar hacia el destino
                    dist = math.hypot(person.x - tx, person.y - ty)
                
                    # GENÉTICA UNIVERSAL: Umbral de llegada ajustado por speed
                    arrival_threshold = self.arrival_threshold * capabilities.movement_speed
                
                    if dist <= arrival_threshold:
                        self._handle_arrival(person, tx, ty, current_day, pending, fw_cfg)
                        pending.clear_migration_target(eid)
                        self._target_set_day.pop(eid, None)
                    continue

            # 4. EVALUACIÓN DE DETONANTES (Push Factors)
            mem = person.memory if isinstance(getattr(person, 'memory', None), dict) else {}
            needs_to_migrate = False
            migration_reasons: List[Tuple[str, float]] = []
            
            # A. Superpoblación
            local_pressure = context.get_local_pressure(int(person.x), int(person.y))
            if local_pressure > 1.8:
                needs_to_migrate = True
                migration_reasons.append(("superpoblación", local_pressure))
            
            # B. Hambre
            energy = person.emotions.get("energy", 1.0)
            local_resources = getattr(context, 'get_resources_at', lambda x, y: 0.5)(int(person.x), int(person.y))
            if energy < 0.3 and local_resources < 0.2:
                needs_to_migrate = True
                hunger_intensity = (1.0 - energy) + (1.0 - local_resources)
                migration_reasons.append(("hambre", hunger_intensity))

            # C. Epidemias
            trauma_sickness = mem.get("trauma_sickness", 0.0)
            viral_load = self._get_viral_load(state, person.x, person.y)
            if trauma_sickness > 0.7 or viral_load > 2.0:
                needs_to_migrate = True
                epidemic_intensity = max(trauma_sickness, viral_load / 5.0)
                migration_reasons.append(("epidemia", epidemic_intensity))

            # D. Clima y Entorno Hostil
            env_system = getattr(state, 'environment_system', None)
            if env_system and hasattr(env_system, 'get_danger_level'):
                danger = env_system.get_danger_level(int(person.x), int(person.y))
                if danger > 0.5:
                    needs_to_migrate = True
                    migration_reasons.append(("clima_hostil", danger))

            # ==========================================
            # BLOQUE 3: TRAUMA GLOBAL SISTÉMICO (HUIDA EMOCIONAL)
            # GENÉTICA UNIVERSAL: Estos traumas son específicos de humanos
            # y especies sociales complejas. Solo aplicar si existen.
            # ==========================================
            # E. Trauma por Abandono (solo si existe)
            abandonment_trauma = mem.get("trauma_abandonment", 0.0)
            if abandonment_trauma > 0.6:
                needs_to_migrate = True
                migration_reasons.append(("trauma_abandono_huida", abandonment_trauma * 1.5))

            # F. Trauma por Adopción (solo si existe)
            adoption_trauma = mem.get("trauma_adoption", 0.0)
            if adoption_trauma > 0.7:
                needs_to_migrate = True
                migration_reasons.append(("trauma_adopcion_huida", adoption_trauma * 1.2))

            # G. Determinación Psicológica
            if getattr(person, 'current_goal', None) == "EMIGRATE":
                needs_to_migrate = True
                migration_reasons.append(("objetivo_psicologico", 1.0))
            
            # H. MOTIVACIÓN INTERNA 'migration'
            # GENÉTICA UNIVERSAL: Solo aplicar si el organismo tiene este concepto
            if hasattr(person, 'get_motivation') and hasattr(person, '_motivations'):
                if "migration" in person._motivations:
                    migration_motivation = person.get_motivation("migration")
                    migration_threshold = getattr(fw_cfg, 'migration_action_threshold', 0.85)
                    
                    if migration_motivation >= migration_threshold:
                        needs_to_migrate = True
                        migration_reasons.append(("impulso_interno", migration_motivation))

            # 5. BÚSQUEDA DE OPORTUNIDADES (Pull Factors)
            if needs_to_migrate:
                best_target = self._find_opportunity(
                    current_x=person.x, current_y=person.y,
                    max_x=max_x, max_y=max_y,
                    context=context, env_system=env_system,
                    num_samples=migration_samples,  # CORRECCIÓN: configurable
                )
                if best_target:
                    pending.set_migration_target(eid, best_target)
                    self._cooldowns[eid] = current_day
                    self._target_set_day[eid] = current_day  # CORRECCIÓN: registrar cuándo se estableció
                    
                    reason = self._determine_migration_reason(migration_reasons)
                    
                    self.logger.debug(
                        "🚶 Agente %s inicia migración hacia (%.1f, %.1f) [motivo: %s, cooldown: %d días]",
                        eid, best_target[0], best_target[1], reason, int(migration_cooldown),
                    )

    def _is_target_still_valid(
        self,
        target_x: float,
        target_y: float,
        context: EnvironmentContext,
        state: WorldState,
    ) -> bool:
        """CORRECCIÓN: Verifica si el destino migratorio sigue siendo viable.
        
        Un destino se invalida si:
        - Los recursos han caído por debajo de un umbral
        - La presión local es excesiva
        - Hay carga viral alta
        """
        coord_x = int(target_x)
        coord_y = int(target_y)
        
        # Verificar recursos
        resources = getattr(context, 'get_resources_at', lambda x, y: 0.5)(coord_x, coord_y)
        if resources < 0.15:  # Umbral mínimo de recursos
            return False
        
        # Verificar presión
        pressure = context.get_local_pressure(coord_x, coord_y)
        if pressure > 2.5:  # Presión excesiva
            return False
        
        # Verificar carga viral
        viral_load = self._get_viral_load(state, target_x, target_y)
        if viral_load > 3.0:  # Epidemia activa en el destino
            return False
        
        return True

    def _handle_arrival(
        self,
        person: Any,
        target_x: float,
        target_y: float,
        current_day: float,
        pending: PendingChanges,
        fw_cfg: Any,
    ) -> None:
        """CORRECCIÓN: Gestiona la llegada al destino migratorio.
        
        Genera:
        - Memoria positiva de migración exitosa
        - Reducción de la motivación migratoria (establecimiento)
        - Actualización de preferred_sector
        """
        distance_traveled = math.hypot(person.x - target_x, person.y - target_y)
        
        if distance_traveled < 50:
            intensity = 0.3
        elif distance_traveled < 150:
            intensity = 0.6
        else:
            intensity = 0.9
        
        target_id = f"{int(target_x)}_{int(target_y)}"
        
        # Registrar memoria de migración exitosa
        CognitiveMemorySystem.add_memory(
            person=person,
            mem_type=CognitiveMemorySystem.TYPE_MIGRATION,
            target_id=target_id,
            intensity=intensity,
            valence=1,
            context="migracion_exitosa",
            current_day=current_day,
            pending=pending,
        )
        
        # CORRECCIÓN: Reducir motivación migratoria (establecimiento)
        if hasattr(person, 'get_motivation'):
            pending.register_motivation_update(
                person.entity_id, "migration", fw_cfg.success_reinforcement_rate
            )
        
        # CORRECCIÓN: Actualizar preferred_sector para arraigo territorial
        sector_size = self.config.environment.sector_size
        preferred_sector = (int(target_x) // sector_size, int(target_y) // sector_size)
        pending.register_memory_update(person.entity_id, "preferred_sector", preferred_sector)
        
        self.logger.debug(
            "🏁 Agente %s completó migración a (%d, %d) - establecido",
            person.entity_id, int(target_x), int(target_y),
        )

    def _determine_migration_reason(self, reasons: List[Tuple[str, float]]) -> str:
        """Determina el motivo principal de la migración."""
        if not reasons:
            return "desconocido"
        
        reasons_sorted = sorted(reasons, key=lambda x: x[1], reverse=True)
        return reasons_sorted[0][0]

    def _find_opportunity(
        self,
        current_x: float,
        current_y: float,
        max_x: int,
        max_y: int,
        context: EnvironmentContext,
        env_system: Any,
        num_samples: int = 20,  # CORRECCIÓN: configurable (antes era 5)
    ) -> Optional[Tuple[float, float]]:
        """Muestrea el mapa global para encontrar un sector prometedor.
        
        CORRECCIÓN: Número de muestras configurable para mapas grandes.
        """
        best_score = -float('inf')
        best_coord = None
        
        for _ in range(num_samples):
            tx = random.uniform(0, max_x)
            ty = random.uniform(0, max_y)
            
            # Evitar destinos demasiado cercanos
            if math.hypot(current_x - tx, current_y - ty) < 25.0:
                continue

            coord_x = int(tx)
            coord_y = int(ty)

            resources = getattr(context, 'get_resources_at', lambda x, y: 0.5)(coord_x, coord_y)
            pressure = context.get_local_pressure(coord_x, coord_y)
            
            danger = 0.0
            if env_system and hasattr(env_system, 'get_danger_level'):
                danger = env_system.get_danger_level(coord_x, coord_y)

            score = (resources * 15.0) - (pressure * 8.0) - (danger * 25.0)
            
            if score > best_score:
                best_score = score
                best_coord = (tx, ty)
                
        return best_coord

    @staticmethod
    def _get_viral_load(state: WorldState, x: float, y: float) -> float:
        """Método compartido para obtener carga viral de una celda."""
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