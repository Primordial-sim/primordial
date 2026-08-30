"""Dinámica ambiental del mundo.

Implementa cambios lentos en el entorno siguiendo tres escalas temporales:
- Rápida: catástrofes naturales (cada tick)
- Media: vegetación y fertilidad (cada 10-30 días)
- Lenta: erosión y geología (cada 100-365 días)

Las catástrofes se delegan al CatastropheSystem.

Principio: "El entorno cambia, no evoluciona."
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, List

from systems.environment.catastrophe_system import CatastropheSystem

if TYPE_CHECKING:
    from core.state.world_state import WorldState
    from systems.environment.world_config import WorldConfig
    from systems.environment.environment_system import Season, Weather
    from systems.environment.catastrophe_model import CatastropheEvent


class EnvironmentDynamics:
    """Gestiona los cambios lentos del entorno."""
    
    def __init__(self, world_config: Optional['WorldConfig'] = None) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.world_config = world_config
        
        # Contadores de tiempo para cada escala
        self._medium_scale_counter: float = 0.0
        self._slow_scale_counter: float = 0.0
        
        # Intervalos de actualización (en días simulados)
        self.medium_scale_interval: float = 15.0  # Cada 15 días
        self.slow_scale_interval: float = 180.0   # Cada 180 días (6 meses)
        
        # Sistema de catástrofes (delegado)
        self.catastrophe_system = CatastropheSystem(world_config)
    
    def process(
        self,
        state: 'WorldState',
        delta_days: float,
        current_season: 'Season',
        current_weather: 'Weather',
        world_config: Optional['WorldConfig'] = None,
    ) -> List['CatastropheEvent']:
        """Procesa los cambios ambientales del mundo.
        
        Args:
            state: Estado del mundo con tile_map.
            delta_days: Días transcurridos desde el último tick.
            current_season: Estación actual.
            current_weather: Clima actual.
            world_config: Configuración física del mundo (opcional).
            
        Returns:
            Lista de catástrofes ocurridas en este tick.
        """
        if not state.has_tile_map():
            return []
        
        if world_config is not None:
            self.world_config = world_config
            self.catastrophe_system.world_config = world_config
        
        # Escala rápida: CATÁSTROFES (delegado a CatastropheSystem)
        occurred_events = self.catastrophe_system.process(
            state=state,
            delta_days=delta_days,
            current_season=current_season,
            world_config=self.world_config,
        )
        
        # Escala media: vegetación y fertilidad
        self._medium_scale_counter += delta_days
        if self._medium_scale_counter >= self.medium_scale_interval:
            self._process_medium_scale(state, current_season)
            self._medium_scale_counter = 0.0
        
        # Escala lenta: erosión y geología
        self._slow_scale_counter += delta_days
        if self._slow_scale_counter >= self.slow_scale_interval:
            self._process_slow_scale(state)
            self._slow_scale_counter = 0.0
        
        return occurred_events
    
    def _process_medium_scale(
        self,
        state: 'WorldState',
        current_season: 'Season',
    ) -> None:
        """Procesa cambios a escala media: vegetación y fertilidad."""
        from systems.environment.environment_system import Season
        
        if state.tile_map is None:
            return
        
        # Factor estacional para crecimiento
        growth_factor = 1.0
        if current_season == Season.SPRING:
            growth_factor = 1.5
        elif current_season == Season.SUMMER:
            growth_factor = 1.2
        elif current_season == Season.AUTUMN:
            growth_factor = 0.8
        elif current_season == Season.WINTER:
            growth_factor = 0.3
        
        # Procesar todos los tiles
        for x in range(state.width):
            for y in range(state.height):
                tile = state.get_tile_at(x, y)
                if tile is None:
                    continue
                
                # Crecimiento vegetal
                if tile.water > 0.2 and tile.temperature > 0.2 and tile.fertility > 0.3:
                    # Condiciones favorables para crecimiento
                    growth_potential = (tile.water + tile.temperature + tile.fertility) / 3.0
                    growth_rate = growth_potential * 0.05 * growth_factor
                    
                    # La vegetación crece más lento cerca de su máximo
                    if tile.vegetation < 0.9:
                        tile.vegetation = min(1.0, tile.vegetation + growth_rate)
                
                elif tile.vegetation > 0.1:
                    # Condiciones desfavorables: la vegetación decae
                    decay_rate = 0.02
                    tile.vegetation = max(0.0, tile.vegetation - decay_rate)
                
                # Acumulación de materia orgánica
                if tile.vegetation > 0.4:
                    # La vegetación alta produce materia orgánica
                    organic_growth = tile.vegetation * 0.01
                    tile.organic_matter = min(1.0, tile.organic_matter + organic_growth)
                
                elif tile.organic_matter > 0.1:
                    # La materia orgánica se descompone lentamente
                    decay_rate = 0.005
                    tile.organic_matter = max(0.0, tile.organic_matter - decay_rate)
                
                # Fertilidad depende de materia orgánica
                if tile.organic_matter > 0.3:
                    # Alta materia orgánica aumenta fertilidad
                    fertility_growth = tile.organic_matter * 0.005
                    tile.fertility = min(1.0, tile.fertility + fertility_growth)
                
                elif tile.fertility > 0.2:
                    # La fertilidad decae sin materia orgánica
                    decay_rate = 0.003
                    tile.fertility = max(0.0, tile.fertility - decay_rate)
    
    def _process_slow_scale(self, state: 'WorldState') -> None:
        """Procesa cambios a escala lenta: erosión y geología."""
        if state.tile_map is None:
            return
        
        # Procesar todos los tiles
        for x in range(state.width):
            for y in range(state.height):
                tile = state.get_tile_at(x, y)
                if tile is None:
                    continue
                
                # Erosión: tiles con pendiente alta pierden altura
                if tile.slope > 0.3 and tile.height > 100.0:
                    # La erosión es más fuerte en pendientes pronunciadas
                    erosion_rate = tile.slope * 5.0  # metros por 180 días
                    
                    # La vegetación protege contra la erosión
                    if tile.vegetation > 0.5:
                        erosion_rate *= 0.3
                    
                    tile.height = max(0.0, tile.height - erosion_rate)
                    
                    # Recalcular pendiente después de erosión
                    self._recalculate_slope(state, x, y)
                
                # Sedimentación: tiles bajos cerca de agua ganan altura
                if tile.height < 50.0 and tile.water > 0.3:
                    sedimentation_rate = 2.0  # metros por 180 días
                    tile.height = min(200.0, tile.height + sedimentation_rate)
    
    def _recalculate_slope(self, state: 'WorldState', x: int, y: int) -> None:
        """Recalcula la pendiente de un tile basándose en sus vecinos."""
        tile = state.get_tile_at(x, y)
        if tile is None:
            return
        
        # Obtener alturas de vecinos
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = state.get_tile_at(x + dx, y + dy)
            if neighbor:
                neighbors.append(neighbor.height)
        
        if not neighbors:
            return
        
        # Calcular diferencia máxima con vecinos
        max_diff = max(abs(tile.height - h) for h in neighbors)
        
        # Normalizar a [0, 1] (asumiendo diferencia máxima de 100m)
        tile.slope = min(1.0, max_diff / 100.0)
    
    def get_catastrophe_summary(self) -> dict:
        """Retorna un resumen de la actividad catastrófica."""
        return self.catastrophe_system.get_summary()
    
    def get_catastrophe_history(self) -> list:
        """Retorna el historial completo de catástrofes."""
        return self.catastrophe_system.get_history()
    
    def get_recent_catastrophes(self, count: int = 10) -> list:
        """Retorna las N catástrofes más recientes."""
        return self.catastrophe_system.get_recent_events(count)