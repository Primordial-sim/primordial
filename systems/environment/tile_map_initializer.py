"""Inicializador procedural del mapa de tiles.

Genera un mapa coherente de tiles basándose en WorldConfig.
Usa ruido pseudo-aleatorio determinista para crear terreno realista:
montañas, océanos, llanuras, etc.

Este inicializador es simple pero funcional. En sesiones futuras
puede mejorarse con algoritmos más sofisticados (Perlin noise, etc.)
"""

from __future__ import annotations

import math
import random
from typing import Optional, TYPE_CHECKING

from systems.environment.tile import Tile
from systems.environment.tile_map import TileMap
from systems.environment.world_config import WorldConfig

if TYPE_CHECKING:
    pass


class TileMapInitializer:
    """Genera proceduralmente el mapa de tiles del mundo."""
    
    def __init__(self, world_config: Optional[WorldConfig] = None, seed: int = 42) -> None:
        self.world_config = world_config or WorldConfig()
        self.seed = seed
        random.seed(seed)
    
    def initialize(self, width: int, height: int) -> TileMap:
        """Genera un mapa de tiles coherente.
        
        Algoritmo simplificado:
        1. Generar campo de altura usando ruido pseudo-aleatorio
        2. Aplicar nivel del mar para determinar agua/tierra
        3. Generar temperatura basada en latitud y altitud
        4. Generar humedad basada en proximidad al agua
        5. Generar vegetación basada en temperatura + humedad + fertilidad
        """
        tile_map = TileMap(width, height)
        
        # 1. Generar campo de altura
        height_field = self._generate_height_field(width, height)
        
        # 2. Crear tiles con todas las variables
        for x in range(width):
            for y in range(height):
                tile = self._create_tile(
                    x=x,
                    y=y,
                    width=width,
                    map_height=height,
                    height_field=height_field,
                )
                tile_map.set_tile(x, y, tile)
        
        return tile_map
    
    def _generate_height_field(self, width: int, height: int) -> list[list[float]]:
        """Genera un campo de altura usando múltiples octavas de ruido.
        
        Combina varias frecuencias para crear terreno realista:
        - Baja frecuencia: continentes y océanos
        - Alta frecuencia: montañas y valles
        """
        field = [[0.0] * height for _ in range(width)]
        
        # Múltiples octavas de ruido para detalle progresivo
        octaves = [
            (0.05, 0.5),   # Frecuencia baja, amplitud alta (continentes)
            (0.1, 0.3),    # Frecuencia media (cordilleras)
            (0.2, 0.15),   # Frecuencia alta (montañas)
            (0.4, 0.05),   # Frecuencia muy alta (colinas)
        ]
        
        for freq, amp in octaves:
            offset_x = random.uniform(0, 1000)
            offset_y = random.uniform(0, 1000)
            
            for x in range(width):
                for y in range(height):
                    # Ruido pseudo-aleatorio determinista usando sin/cos
                    noise = (
                        math.sin((x + offset_x) * freq) *
                        math.cos((y + offset_y) * freq)
                    )
                    # Normalizar a [0, 1]
                    noise = (noise + 1.0) / 2.0
                    field[x][y] += noise * amp
        
        return field
    
    def _create_tile(
        self,
        x: int,
        y: int,
        width: int,
        map_height: int,
        height_field: list[list[float]],
    ) -> Tile:
        """Crea un tile individual con todas sus variables.
        
        Args:
            x: Coordenada X del tile.
            y: Coordenada Y del tile.
            width: Ancho del mapa en tiles.
            map_height: Alto del mapa en tiles (renombrado para evitar colisión
                        con la variable local 'height' que es altitud en metros).
            height_field: Campo de alturas generado proceduralmente.
        """
        # Altura base del campo de ruido
        raw_height = height_field[x][y]
        
        # Convertir a metros: [-500m, 3000m]
        # Ajustar según water_coverage del WorldConfig
        sea_level_threshold = 1.0 - self.world_config.water_coverage
        is_ocean = raw_height < sea_level_threshold
        
        # CORRECCIÓN: Usar 'elevation' para la altitud del tile en metros
        # y evitar confusión con parámetros del mapa
        if is_ocean:
            # Océano: altura negativa proporcional a la profundidad
            elevation = -500.0 * (1.0 - raw_height / sea_level_threshold)
        else:
            # Tierra: altura positiva
            land_height = (raw_height - sea_level_threshold) / (1.0 - sea_level_threshold)
            elevation = land_height * 3000.0
        
        # Aplicar nivel del mar del WorldConfig
        elevation -= self.world_config.sea_level
        
        # Pendiente: calcular gradiente con vecinos
        slope = self._calculate_slope(x, y, width, map_height, height_field)
        
        # Agua: basada en si está bajo el nivel del mar
        if is_ocean:
            water = 0.8 + 0.2 * (1.0 - raw_height / sea_level_threshold)
            salinity = 0.9  # Agua salada
        else:
            # Lagos y ríos (probabilidad baja)
            water = 0.1 if raw_height > sea_level_threshold + 0.1 else 0.3
            salinity = 0.1  # Agua dulce
        
        # Temperatura: basada en latitud (y) y altitud
        # Latitud: 0.0 en ecuador (centro), 1.0 en polos (bordes)
        latitude_factor = abs(y - map_height / 2) / (map_height / 2)
        # Altitud: cada 1000m reduce temperatura en 0.1
        altitude_factor = max(0.0, elevation / 10000.0)
        
        base_temp = self.world_config.mean_temperature
        temperature = base_temp - (latitude_factor * 0.3) - (altitude_factor * 0.3)
        temperature = max(0.0, min(1.0, temperature))
        
        # Humedad: mayor cerca del agua, menor en montañas
        humidity = self.world_config.global_humidity
        if water > 0.3:
            humidity += 0.3  # Cerca del agua
        if elevation > 1500:
            humidity -= 0.2  # Montañas son más secas
        humidity = max(0.0, min(1.0, humidity))
        
        # Fertilidad: mayor en llanuras cerca del agua
        fertility = 0.3
        if not is_ocean and elevation < 500 and slope < 0.3:
            fertility = 0.7  # Llanuras fértiles
        if water > 0.3 and not is_ocean:
            fertility += 0.2  # Cerca del agua
        fertility = max(0.0, min(1.0, fertility))
        
        # Vegetación: basada en temperatura + humedad + fertilidad
        if is_ocean:
            vegetation = 0.0  # Sin vegetación en océanos
        else:
            veg_potential = (temperature + humidity + fertility) / 3.0
            # Reducir en pendientes pronunciadas
            veg_potential *= (1.0 - slope)
            vegetation = max(0.0, min(1.0, veg_potential))
        
        # Materia orgánica: correlacionada con vegetación
        organic_matter = vegetation * 0.8 if not is_ocean else 0.0
        
        # Rococidad: mayor en montañas y pendientes
        rockiness = slope * 0.7
        if elevation > 1500:
            rockiness += 0.3
        rockiness = max(0.0, min(1.0, rockiness))
        
        return Tile(
            height=elevation,
            slope=slope,
            temperature=temperature,
            humidity=humidity,
            water=water,
            salinity=salinity,
            fertility=fertility,
            vegetation=vegetation,
            organic_matter=organic_matter,
            rockiness=rockiness,
        )
    
    def _calculate_slope(
        self,
        x: int,
        y: int,
        width: int,
        map_height: int,
        height_field: list[list[float]],
    ) -> float:
        """Calcula la pendiente en un punto usando el gradiente.
        
        Args:
            x: Coordenada X del tile.
            y: Coordenada Y del tile.
            width: Ancho del mapa en tiles.
            map_height: Alto del mapa en tiles (para wrapping).
            height_field: Campo de alturas generado proceduralmente.
        """
            
        # Obtener valores de vecinos (con wrapping)
        left = height_field[(x - 1) % width][y]
        right = height_field[(x + 1) % width][y]
        up = height_field[x][(y - 1) % map_height]
        down = height_field[x][(y + 1) % map_height]
        
        # Gradiente en X e Y
        dx = abs(right - left) / 2.0
        dy = abs(down - up) / 2.0
        
        # Magnitud del gradiente
        gradient = math.sqrt(dx * dx + dy * dy)
        
        # Normalizar a [0, 1] (asumiendo gradiente máximo ~0.5)
        slope = min(1.0, gradient / 0.5)
        
        return slope