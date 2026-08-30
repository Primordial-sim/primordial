"""Sistema de retroalimentación organismos-entorno.

Cierra el ciclo de retroalimentación:
1. Organismos impactan el entorno (OrganismImpactCalculator)
2. Entorno cambia (FeedbackSystem aplica los impactos)
3. Nuevas condiciones afectan a los organismos (ciclo se repite)

Principio: "El entorno es un resultado emergente de la vida que contiene."
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from systems.environment.organism_impact import OrganismImpactCalculator, TileImpact

if TYPE_CHECKING:
    from core.state.world_state import WorldState
    from core.state.pending_changes import PendingChanges
    from systems.environment.environment_context import EnvironmentContext


class FeedbackSystem:
    """Sistema que aplica el impacto de los organismos al entorno."""
    
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.impact_calculator = OrganismImpactCalculator()
        
        # Contador para procesamiento periódico (no cada tick)
        self._process_counter: float = 0.0
        self.process_interval: float = 5.0  # Cada 5 días
        
        # Factor de escala para los impactos (ajustable)
        self.impact_scale: float = 1.0
    
    def process(
        self,
        state: 'WorldState',
        pending: 'PendingChanges',
        delta_days: float,
        context: 'EnvironmentContext',
    ) -> None:
        """Procesa la retroalimentación organismos-entorno.
        
        Args:
            state: Estado del mundo con tile_map y persons.
            pending: Búfer de cambios pendientes.
            delta_days: Días transcurridos.
            context: Contexto ambiental.
        """
        if not state.has_tile_map():
            return
        
        # Procesar solo cada N días para optimización
        self._process_counter += delta_days
        if self._process_counter < self.process_interval:
            return
        
        self._process_counter = 0.0
        
        # Calcular impacto acumulado de todos los organismos
        persons = list(state.get_all_persons())
        if not persons:
            return
        
        # CORRECCIÓN: Verificar que tile_map no sea None antes de acceder
        tile_map = state.tile_map
        if tile_map is None:
            return
        
        accumulated_impacts = self.impact_calculator.calculate_accumulated(
            persons=persons,
            tile_map=tile_map.tiles,
        )
        
        # Aplicar impactos al tile_map
        tiles_modified = 0
        for (x, y), impact in accumulated_impacts.items():
            tile = state.get_tile_at(x, y)
            if tile is None:
                continue
            
            self._apply_impact(tile, impact)
            tiles_modified += 1
        
        if tiles_modified > 0:
            self.logger.debug(
                f"🔄 Retroalimentación: {tiles_modified} tiles modificados "
                f"por {len(persons)} organismos"
            )
    
    def _apply_impact(self, tile, impact: TileImpact) -> None:
        """Aplica un impacto acumulado a un tile.
        
        Args:
            tile: El tile a modificar.
            impact: El impacto acumulado a aplicar.
        """
        scale = self.impact_scale
        
        # Aplicar vegetación
        if impact.vegetation_delta != 0.0:
            tile.vegetation += impact.vegetation_delta * scale
            tile.vegetation = max(0.0, min(1.0, tile.vegetation))
        
        # Aplicar materia orgánica
        if impact.organic_matter_delta != 0.0:
            tile.organic_matter += impact.organic_matter_delta * scale
            tile.organic_matter = max(0.0, min(1.0, tile.organic_matter))
        
        # Aplicar fertilidad
        if impact.fertility_delta != 0.0:
            tile.fertility += impact.fertility_delta * scale
            tile.fertility = max(0.0, min(1.0, tile.fertility))
        
        # Aplicar agua
        if impact.water_delta != 0.0:
            tile.water += impact.water_delta * scale
            tile.water = max(0.0, min(1.0, tile.water))
        
        # Aplicar humedad
        if impact.humidity_delta != 0.0:
            tile.humidity += impact.humidity_delta * scale
            tile.humidity = max(0.0, min(1.0, tile.humidity))
        
        # Aplicar altura
        if impact.height_delta != 0.0:
            tile.height += impact.height_delta * scale
            # La altura puede ser negativa (océanos) o positiva (montañas)
        
        # Aplicar pendiente
        if impact.slope_delta != 0.0:
            tile.slope += impact.slope_delta * scale
            tile.slope = max(0.0, min(1.0, tile.slope))
        
        # Aplicar temperatura
        if impact.temperature_delta != 0.0:
            tile.temperature += impact.temperature_delta * scale
            tile.temperature = max(0.0, min(1.0, tile.temperature))
        
        # Aplicar urbanización (si el tile tiene esta variable)
        if impact.urbanization_delta != 0.0:
            if hasattr(tile, 'urbanization'):
                tile.urbanization += impact.urbanization_delta * scale
                tile.urbanization = max(0.0, min(1.0, tile.urbanization))
    
    def get_impact_summary(self, state: 'WorldState') -> dict:
        """Retorna un resumen del impacto actual de los organismos.
        
        Args:
            state: Estado del mundo.
            
        Returns:
            Diccionario con estadísticas de impacto.
        """
        if not state.has_tile_map():
            return {"total_organisms": 0, "tiles_with_impact": 0}
        
        persons = list(state.get_all_persons())
        if not persons:
            return {"total_organisms": 0, "tiles_with_impact": 0}
        
        # Verificar que tile_map no sea None antes de acceder
        tile_map = state.tile_map
        if tile_map is None:
            return {"total_organisms": 0, "tiles_with_impact": 0}
        
        accumulated = self.impact_calculator.calculate_accumulated(
            persons=persons,
            tile_map=tile_map.tiles,
        )
        
        # Calcular estadísticas
        total_vegetation_impact = sum(
            abs(i.vegetation_delta) for i in accumulated.values()
        )
        total_fertility_impact = sum(
            abs(i.fertility_delta) for i in accumulated.values()
        )
        
        return {
            "total_organisms": len(persons),
            "tiles_with_impact": len(accumulated),
            "total_vegetation_impact": total_vegetation_impact,
            "total_fertility_impact": total_fertility_impact,
        }