"""Módulo que define el contexto espacial, ambiental y topográfico para la simulación.

Provee a los sistemas de una instantánea (snapshot) de la distribución demográfica,
la presión del entorno y la disponibilidad de recursos en el tick actual.

OPTIMIZACIONES APLICADAS:
- @lru_cache en get_resources_at para evitar recalcular trigonometría
- sector_key precachado por coordenada
"""

from __future__ import annotations

import math
from collections import defaultdict
from functools import lru_cache
from typing import List, Tuple, Dict, Any, Optional

from core.state.world_state import WorldState
from core.config.simulation_config import SimulationConfig

from systems.environment.biome_classifier import BiomeClassifier, Biome


class EnvironmentContext:
    """Representa el estado del entorno, distribuyendo recursos y agentes."""

    def __init__(self, state: WorldState, config: Optional[SimulationConfig] = None) -> None:
        if config is not None:
            self.sector_size = config.environment.sector_size
            self.max_agents_per_sector = config.environment.max_agents_per_sector
        else:
            self.sector_size = 10
            self.max_agents_per_sector = 8
        
        self.sector_map = self._build_sector_map(state)
        self.pressure_map: Dict[Tuple[int, int], float] = {}
        self.current_season: Any = None
        self.current_weather: Any = None
        
        # OPTIMIZACIÓN: Precalcular conteo de agentes por sector (para get_resources_at)
        self._sector_consumer_counts: Dict[Tuple[int, int], int] = {
            sector: len(agents) for sector, agents in self.sector_map.items()
        }

        # Referencia al mapa de tiles (si existe)
        self.tile_map = getattr(state, 'tile_map', None)

    def _build_sector_map(self, state: WorldState) -> Dict[Tuple[int, int], List[Any]]:
        """Agrupa a los agentes por sector espacial para agilizar las consultas (O(1))."""
        sector_map = defaultdict(list)
        for person in state.get_all_persons():
            # HEX: Usar q y r en lugar de x e y
            key = (person.q // self.sector_size, person.r // self.sector_size)
            sector_map[key].append(person)
        return sector_map

    def get_local_pressure(self, q: int, r: int) -> float:
        """Obtiene la presión espacial en una coordenada específica."""
        return self.pressure_map.get((int(q), int(r)), 1.0)

    def get_agents_in_sector(self, q: int, r: int) -> List[Any]:
        """Devuelve la lista de agentes presentes en el sector correspondiente."""
        return self.sector_map.get((q // self.sector_size, r // self.sector_size), [])

    # =====================================================================
    # OPTIMIZACIÓN CRÍTICA: Caché LRU para get_resources_at
    # =====================================================================
    # Se llama ~1M veces por simulación. Los cálculos trigonométricos son
    # costosos y deterministas (misma coordenada = mismo resultado).
    @lru_cache(maxsize=4096)
    def _get_base_resource(self, q: int, r: int) -> float:
        """Calcula el recurso base determinista (Oasis vs Desiertos)."""
        ruido = (math.sin(q * 0.15) + math.cos(r * 0.15)) / 2.0
        return (ruido + 1.0) / 2.0

    def get_resources_at(self, q: int, r: int) -> float:
        """Calcula la disponibilidad de recursos (0.0 a 1.0).
        
        OPTIMIZACIÓN: Usa @lru_cache para el cálculo trigonométrico base,
        y un dict precalculado para el conteo de consumidores por sector.
        """
        # 1. Recurso base (CACHÉ LRU - evita recalcular trigonometría)
        recurso_base = self._get_base_resource(int(q), int(r))
        
        # 2. Desgaste por sobreexplotación (O(1) gracias al dict precalculado)
        sector_key = (int(q) // self.sector_size, int(r) // self.sector_size)
        consumidores = self._sector_consumer_counts.get(sector_key, 0)
        desgaste = (consumidores / max(1, self.max_agents_per_sector)) * 0.8
        
        return max(0.0, min(1.0, recurso_base - desgaste))

    # =====================================================================
    # API DE TILES Y BIOMAS
    # =====================================================================
    
    def get_tile_at(self, q: int, r: int) -> Optional[Any]:
        """Retorna el tile en la posición dada."""
        if self.tile_map is None:
            return None
        return self.tile_map.get_tile(int(q), int(r))
    
    def get_biome_at(self, q: int, r: int) -> Optional[Biome]:
        """Retorna el bioma en la posición dada.
        
        El bioma se calcula dinámicamente a partir de las variables del tile.
        """
        tile = self.get_tile_at(q, r)
        if tile is None:
            return None
        return BiomeClassifier.classify(tile)
    
    def get_biome_name_at(self, q: int, r: int) -> str:
        """Retorna el nombre del bioma en la posición dada como string."""
        biome = self.get_biome_at(q, r)
        return str(biome) if biome is not None else "unknown"
    
    def has_tile_map(self) -> bool:
        """Verifica si hay un mapa de tiles disponible."""
        return self.tile_map is not None