"""Clasificador de biomas basado en variables de tile.

El bioma NO se almacena en el tile, se calcula dinámicamente a partir
de las variables ambientales. Esto permite que los biomas emerjan
naturalmente y cambien cuando cambian las condiciones.

Principio: "El bioma es una consecuencia, no un dato."
"""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from systems.environment.tile import Tile


class Biome(Enum):
    """Tipos de biomas derivados de variables ambientales."""
    OCEAN = auto()
    DEEP_OCEAN = auto()
    LAKE = auto()
    BEACH = auto()
    DESERT = auto()
    SAVANNA = auto()
    GRASSLAND = auto()
    FOREST = auto()
    RAINFOREST = auto()
    TUNDRA = auto()
    TAIGA = auto()
    MOUNTAIN = auto()
    SNOW_PEAK = auto()
    WETLAND = auto()
    URBAN = auto()
    
    def __str__(self) -> str:
        return self.name.lower().replace('_', ' ')


class BiomeClassifier:
    """Clasifica tiles en biomas basándose en variables ambientales."""
    
    @staticmethod
    def classify(tile: Tile) -> Biome:
        """Determina el bioma de un tile basándose en sus variables.
        
        Reglas de clasificación (simplificadas):
        - Agua alta + profundidad → Océano
        - Agua alta + poca profundidad → Lago
        - Temperatura alta + agua baja → Desierto
        - Temperatura alta + agua alta → Selva
        - Temperatura baja + altitud alta → Tundra
        - Vegetación alta → Bosque
        """

        # Zonas urbanas (alta urbanización)
        if hasattr(tile, 'urbanization') and tile.urbanization > 0.7:
            return Biome.URBAN

        # Océanos profundos
        if tile.water > 0.9 and tile.height < -50:
            return Biome.DEEP_OCEAN
        
        # Océanos y mares
        if tile.water > 0.8 and tile.salinity > 0.7:
            return Biome.OCEAN
        
        # Lagos (agua dulce)
        if tile.water > 0.7 and tile.salinity < 0.3:
            return Biome.LAKE
        
        # Playas (transición tierra-agua)
        if tile.water > 0.3 and tile.water < 0.7 and tile.slope < 0.2:
            return Biome.BEACH
        
        # Humedales
        if tile.water > 0.4 and tile.vegetation > 0.3 and tile.slope < 0.1:
            return Biome.WETLAND
        
        # Picos nevados
        if tile.height > 2000 and tile.temperature < 0.2:
            return Biome.SNOW_PEAK
        
        # Montañas
        if tile.height > 1500 or tile.slope > 0.8:
            return Biome.MOUNTAIN
        
        # Desiertos (calor + sequedad)
        if tile.temperature > 0.7 and tile.humidity < 0.3 and tile.vegetation < 0.1:
            return Biome.DESERT
        
        # Selvas tropicales (calor + humedad alta)
        if tile.temperature > 0.7 and tile.humidity > 0.7 and tile.vegetation > 0.8:
            return Biome.RAINFOREST
        
        # Sabanas (calor + vegetación media)
        if tile.temperature > 0.6 and tile.vegetation > 0.3 and tile.vegetation < 0.6:
            return Biome.SAVANNA
        
        # Tundra (frío extremo)
        if tile.temperature < 0.3 and tile.vegetation < 0.3:
            return Biome.TUNDRA
        
        # Taiga (bosques boreales)
        if tile.temperature < 0.4 and tile.vegetation > 0.5:
            return Biome.TAIGA
        
        # Bosques (vegetación alta)
        if tile.vegetation > 0.6:
            return Biome.FOREST
        
        # Praderas (vegetación media, temperatura moderada)
        if tile.vegetation > 0.2 and tile.vegetation < 0.6:
            return Biome.GRASSLAND
        
        # Por defecto: pradera
        return Biome.GRASSLAND
    
    @staticmethod
    def get_biome_name(tile: Tile) -> str:
        """Retorna el nombre del bioma como string."""
        return str(BiomeClassifier.classify(tile))