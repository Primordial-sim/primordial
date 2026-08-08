"""Módulo responsable del Entorno: Presión espacial, Clima y Recursos.

Calcula la presión espacial basada en densidad poblacional y actúa como 
infraestructura base para futuras expansiones de clima y catástrofes.

OPTIMIZACIÓN: Se elimina la precomputación O(N) de pressure_map. 
Ahora la presión se calcula bajo demanda en O(1) a través de EnvironmentContext.
"""

import logging
import random
from enum import Enum, auto
from typing import Dict, Tuple

from systems.environment.environment_context import EnvironmentContext
from core.state.world_state import WorldState
from core.state.pending_changes import PendingChanges
from core.config.simulation_config import SimulationConfig


class Season(Enum):
    SPRING = auto()
    SUMMER = auto()
    AUTUMN = auto()
    WINTER = auto()


class Weather(Enum):
    CLEAR = auto()
    RAINY = auto()
    STORMY = auto()
    DROUGHT = auto()
    BLIZZARD = auto()


class BiomeType(Enum):
    PLAINS = auto()
    FOREST = auto()
    DESERT = auto()
    TUNDRA = auto()


class EnvironmentSystem:
    """Calcula la presión espacial y gestiona la infraestructura climática."""

    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.current_season: Season = Season.SPRING
        self.current_weather: Weather = Weather.CLEAR
        self.days_in_current_season: float = 0.0
        self.season_duration_days: float = getattr(config.environment, 'season_duration_days', 90.0)
        
        self.biome_map: Dict[Tuple[int, int], BiomeType] = {}
        self.resource_grid: Dict[Tuple[int, int], Dict[str, float]] = {}
        self.danger_zones: Dict[Tuple[int, int], float] = {}

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Actualiza el reloj climático y valida la integridad del contexto."""
        # =====================================================================
        # 1. INFRAESTRUCTURA CLIMÁTICA (Segura contra estados None)
        # =====================================================================
        if self.current_season is None:
            self.current_season = Season.SPRING
            self.logger.warning("current_season era None, reinicializado a SPRING")
            
        self.days_in_current_season += delta_days
        if self.days_in_current_season >= self.season_duration_days:
            self.days_in_current_season = 0.0
            self._advance_season()

        self._update_weather_placeholder(delta_days)

        # Inyectar datos climáticos en el contexto
        context.current_season = self.current_season
        context.current_weather = self.current_weather

    def _advance_season(self) -> None:
        if self.current_season is None:
            self.current_season = Season.SPRING
            
        seasons = list(Season)
        try:
            next_index = (seasons.index(self.current_season) + 1) % len(seasons)
            self.current_season = seasons[next_index]
            self.logger.info(f"🌍 El entorno ha cambiado de estación a: {self.current_season.name}")
        except ValueError as e:
            self.logger.error(f"Error avanzado estación: {e}. Forzando SPRING.")
            self.current_season = Season.SPRING

    def _update_weather_placeholder(self, delta_days: float) -> None:
        if self.current_season is None:
            return
            
        if random.random() < (0.01 * delta_days):
            if self.current_season == Season.WINTER:
                self.current_weather = random.choice([Weather.CLEAR, Weather.RAINY, Weather.BLIZZARD])
            elif self.current_season == Season.SUMMER:
                self.current_weather = random.choice([Weather.CLEAR, Weather.DROUGHT])
            else:
                self.current_weather = random.choice([Weather.CLEAR, Weather.RAINY, Weather.STORMY])

    def get_biome_at(self, x: float, y: float) -> BiomeType:
        return self.biome_map.get((int(x), int(y)), BiomeType.PLAINS)

    def get_resource_level(self, x: float, y: float, resource_type: str) -> float:
        cell_resources = self.resource_grid.get((int(x), int(y)))
        if cell_resources:
            return cell_resources.get(resource_type, 100.0)
        return 100.0

    def get_danger_level(self, x: float, y: float) -> float:
        biome = self.get_biome_at(x, y)
        base_danger = 0.3 if biome in [BiomeType.DESERT, BiomeType.TUNDRA] else 0.0
        return min(1.0, self.danger_zones.get((int(x), int(y)), 0.0) + base_danger)

    def trigger_catastrophe(self, x: float, y: float, radius: float, severity: float) -> None:
        self.logger.warning(f"¡CATÁSTROFE ACTIVADA en ({x}, {y}) con radio {radius}!")
        for dx in range(int(-radius), int(radius) + 1):
            for dy in range(int(-radius), int(radius) + 1):
                target_coord = (int(x + dx), int(y + dy))
                self.danger_zones[target_coord] = severity