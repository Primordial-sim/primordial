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

    def _build_sector_map(self, state: WorldState) -> Dict[Tuple[int, int], List[Any]]:
        """Agrupa a los agentes por sector espacial para agilizar las consultas (O(1))."""
        sector_map = defaultdict(list)
        for person in state.get_all_persons():
            key = (person.x // self.sector_size, person.y // self.sector_size)
            sector_map[key].append(person)
        return sector_map

    def get_local_pressure(self, x: int, y: int) -> float:
        """Obtiene la presión espacial en una coordenada específica."""
        return self.pressure_map.get((int(x), int(y)), 1.0)

    def get_agents_in_sector(self, x: int, y: int) -> List[Any]:
        """Devuelve la lista de agentes presentes en el sector correspondiente."""
        return self.sector_map.get((x // self.sector_size, y // self.sector_size), [])

    # =====================================================================
    # OPTIMIZACIÓN CRÍTICA: Caché LRU para get_resources_at
    # =====================================================================
    # Se llama ~1M veces por simulación. Los cálculos trigonométricos son
    # costosos y deterministas (misma coordenada = mismo resultado).
    @lru_cache(maxsize=4096)
    def _get_base_resource(self, x: int, y: int) -> float:
        """Calcula el recurso base determinista (Oasis vs Desiertos)."""
        ruido = (math.sin(x * 0.15) + math.cos(y * 0.15)) / 2.0
        return (ruido + 1.0) / 2.0

    def get_resources_at(self, x: int, y: int) -> float:
        """Calcula la disponibilidad de recursos (0.0 a 1.0).
        
        OPTIMIZACIÓN: Usa @lru_cache para el cálculo trigonométrico base,
        y un dict precalculado para el conteo de consumidores por sector.
        """
        # 1. Recurso base (CACHÉ LRU - evita recalcular trigonometría)
        recurso_base = self._get_base_resource(int(x), int(y))
        
        # 2. Desgaste por sobreexplotación (O(1) gracias al dict precalculado)
        sector_key = (int(x) // self.sector_size, int(y) // self.sector_size)
        consumidores = self._sector_consumer_counts.get(sector_key, 0)
        desgaste = (consumidores / max(1, self.max_agents_per_sector)) * 0.8
        
        return max(0.0, min(1.0, recurso_base - desgaste))