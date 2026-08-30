"""Calculadora de impacto de organismos en el entorno.

Cada organismo modifica el tile donde se encuentra basándose en sus
rasgos genéticos. Este es el primer paso del ciclo de retroalimentación:
organismos → entorno.

Principio: "Los organismos no solo se adaptan al entorno, lo transforman."
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entities.person.person import Person
    from systems.environment.tile import Tile


@dataclass
class TileImpact:
    """Representa las modificaciones que un organismo aplica a un tile.
    
    Todos los valores son deltas (cambios) que se suman a las variables
    actuales del tile. Valores positivos aumentan, negativos reducen.
    
    Attributes:
        vegetation_delta: Cambio en vegetación [-0.1, 0.1]
        organic_matter_delta: Cambio en materia orgánica [-0.1, 0.1]
        fertility_delta: Cambio en fertilidad [-0.1, 0.1]
        water_delta: Cambio en agua [-0.1, 0.1]
        humidity_delta: Cambio en humedad [-0.1, 0.1]
        height_delta: Cambio en altura [-5.0, 5.0] (metros)
        slope_delta: Cambio en pendiente [-0.1, 0.1]
        temperature_delta: Cambio en temperatura [-0.1, 0.1]
        urbanization_delta: Cambio en urbanización [-0.1, 0.1]
    """
    
    vegetation_delta: float = 0.0
    organic_matter_delta: float = 0.0
    fertility_delta: float = 0.0
    water_delta: float = 0.0
    humidity_delta: float = 0.0
    height_delta: float = 0.0
    slope_delta: float = 0.0
    temperature_delta: float = 0.0
    urbanization_delta: float = 0.0
    
    def is_empty(self) -> bool:
        """Verifica si el impacto es nulo."""
        return (
            self.vegetation_delta == 0.0 and
            self.organic_matter_delta == 0.0 and
            self.fertility_delta == 0.0 and
            self.water_delta == 0.0 and
            self.humidity_delta == 0.0 and
            self.height_delta == 0.0 and
            self.slope_delta == 0.0 and
            self.temperature_delta == 0.0 and
            self.urbanization_delta == 0.0
        )


class OrganismImpactCalculator:
    """Calcula el impacto de un organismo en su tile actual."""
    
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def calculate(self, person: 'Person', tile: 'Tile') -> TileImpact:
        """Calcula el impacto de un organismo en un tile.
        
        Args:
            person: El organismo que está en el tile.
            tile: El tile donde está el organismo.
            
        Returns:
            TileImpact con las modificaciones a aplicar.
        """
        genome = person.genome
        
        # Obtener rasgos relevantes
        photosynthesis = genome.get_trait_value("photosynthesis") if genome.has_trait("photosynthesis") else 0.0
        heterotrophy = genome.get_trait_value("heterotrophy") if genome.has_trait("heterotrophy") else 0.0
        intelligence = genome.get_trait_value("intelligence") if genome.has_trait("intelligence") else 0.0
        sociability = genome.get_trait_value("sociability") if genome.has_trait("sociability") else 0.0
        metabolism = genome.get_trait_value("metabolism") if genome.has_trait("metabolism") else 0.5
        growth_rate = genome.get_trait_value("growth_rate") if genome.has_trait("growth_rate") else 0.5
        flight = genome.get_trait_value("flight") if genome.has_trait("flight") else 0.0
        swimming = genome.get_trait_value("swimming") if genome.has_trait("swimming") else 0.0
        
        impact = TileImpact()
        
        # =====================================================================
        # PLANTAS Y ORGANISMOS FOTOSINTÉTICOS
        # =====================================================================
        if photosynthesis > 0.5:
            # Producen vegetación y materia orgánica
            impact.vegetation_delta += 0.02 * photosynthesis
            impact.organic_matter_delta += 0.01 * photosynthesis
            impact.fertility_delta += 0.005 * photosynthesis
            
            # Absorben agua y CO2 (reducen ligeramente el agua)
            impact.water_delta -= 0.005 * photosynthesis
        
        # =====================================================================
        # HERBÍVOROS Y CONSUMIDORES
        # =====================================================================
        if heterotrophy > 0.5 and photosynthesis < 0.3:
            # Consumen vegetación
            consumption_rate = 0.015 * heterotrophy * metabolism
            impact.vegetation_delta -= consumption_rate
            
            # Producen materia orgánica (excrementos, cuerpos)
            impact.organic_matter_delta += 0.008 * heterotrophy
            
            # Erosión por pisoteo (si son grandes/móviles)
            speed = genome.get_trait_value("speed") if genome.has_trait("speed") else 0.5
            if speed > 0.7:
                impact.slope_delta += 0.002 * speed
                impact.height_delta -= 0.1 * speed
        
        # =====================================================================
        # HUMANOS Y ORGANISMOS INTELIGENTES
        # =====================================================================
        if intelligence > 1.0 and sociability > 0.8:
            # Agricultura: aumenta fertilidad pero reduce vegetación natural
            impact.fertility_delta += 0.01 * intelligence
            impact.vegetation_delta -= 0.01 * intelligence
            
            # Urbanización: reduce vegetación y aumenta temperatura (isla de calor)
            if sociability > 1.2:
                impact.urbanization_delta += 0.02 * sociability
                impact.temperature_delta += 0.005 * sociability
                impact.vegetation_delta -= 0.01 * sociability
            
            # Modificación del terreno
            impact.height_delta += 0.5 * intelligence  # Construcciones
        
        # =====================================================================
        # HONGOS Y DESCOMPONEDORES
        # =====================================================================
        if growth_rate > 1.0 and heterotrophy > 0.5 and photosynthesis < 0.2:
            # Descomponen materia orgánica y la convierten en fertilidad
            impact.organic_matter_delta -= 0.01 * growth_rate
            impact.fertility_delta += 0.015 * growth_rate
        
        # =====================================================================
        # ORGANISMOS ACUÁTICOS
        # =====================================================================
        if swimming > 1.0:
            # Movimiento en agua: redistribuyen sedimentos
            impact.water_delta += 0.005 * swimming
            impact.height_delta -= 0.05 * swimming  # Erosión acuática
        
        # =====================================================================
        # AVES Y DISPERSORES DE SEMILLAS
        # =====================================================================
        if flight > 1.0:
            # Dispersan semillas: aumentan vegetación en áreas nuevas
            if tile.vegetation < 0.5:
                impact.vegetation_delta += 0.01 * flight
        
        return impact
    
    def calculate_accumulated(
        self,
        persons: list,
        tile_map: dict,
    ) -> dict:
        """Calcula el impacto acumulado de todos los organismos.
        
        Args:
            persons: Lista de todos los organismos.
            tile_map: Diccionario de tiles del mundo.
            
        Returns:
            Diccionario de (x, y) -> TileImpact acumulado.
        """
        accumulated: dict = {}
        
        for person in persons:
            x, y = int(person.x), int(person.y)
            tile = tile_map.get((x, y))
            
            if tile is None:
                continue
            
            impact = self.calculate(person, tile)
            
            if impact.is_empty():
                continue
            
            # Acumular impacto
            if (x, y) not in accumulated:
                accumulated[(x, y)] = TileImpact()
            
            acc = accumulated[(x, y)]
            acc.vegetation_delta += impact.vegetation_delta
            acc.organic_matter_delta += impact.organic_matter_delta
            acc.fertility_delta += impact.fertility_delta
            acc.water_delta += impact.water_delta
            acc.humidity_delta += impact.humidity_delta
            acc.height_delta += impact.height_delta
            acc.slope_delta += impact.slope_delta
            acc.temperature_delta += impact.temperature_delta
            acc.urbanization_delta += impact.urbanization_delta
        
        return accumulated