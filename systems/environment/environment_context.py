"""Módulo que define el contexto espacial, ambiental y topográfico para la simulación.

Provee a los sistemas de una instantánea (snapshot) de la distribución demográfica,
la presión del entorno y la disponibilidad de recursos en el tick actual.

NOTA: Este módulo NO calcula presión. La presión se calcula en EnvironmentSystem
y se inyecta en pressure_map. Este módulo solo la lee.
"""

import math
from collections import defaultdict
from typing import List, Tuple, Dict, Any, Optional

from core.state.world_state import WorldState
from core.config.simulation_config import SimulationConfig


class EnvironmentContext:
    """Representa el estado del entorno, distribuyendo recursos y agentes."""

    def __init__(self, state: WorldState, config: Optional[SimulationConfig] = None) -> None:
        """Inicializa la topografía y agrupa a los agentes por sectores.
        
        Args:
            state: Referencia al estado del mundo en el tick actual.
            config: Configuración centralizada (opcional, usa valores por defecto si es None).
        """
        if config is not None:
            self.sector_size = config.environment.sector_size
            # CORRECCIÓN: Usar max_agents_per_sector para coherencia con el desgaste de recursos
            self.max_agents_per_sector = config.environment.max_agents_per_sector
        else:
            self.sector_size = 10
            self.max_agents_per_sector = 8
        
        # Calculamos el mapa de sectores al instanciarse (una sola vez por tick)
        self.sector_map = self._build_sector_map(state)
        
        # Mapa de presión espacial (llenado por EnvironmentSystem)
        self.pressure_map: Dict[Tuple[int, int], float] = {}
        
        # Variables climáticas (placeholder, llenadas por EnvironmentSystem)
        self.current_season: Any = None
        self.current_weather: Any = None

    def _build_sector_map(self, state: WorldState) -> Dict[Tuple[int, int], List[Any]]:
        """Agrupa a los agentes por sector espacial para agilizar las consultas (O(1))."""
        sector_map = defaultdict(list)
        for person in state.get_all_persons():
            key = (person.x // self.sector_size, person.y // self.sector_size)
            sector_map[key].append(person)
        return sector_map

    def get_local_pressure(self, x: int, y: int) -> float:
        """Obtiene la presión espacial en una coordenada específica.
        
        La presión es calculada por EnvironmentSystem y almacenada en pressure_map.
        Este método solo la lee.
        """
        return self.pressure_map.get((int(x), int(y)), 1.0)

    def get_agents_in_sector(self, x: int, y: int) -> List[Any]:
        """Devuelve la lista de agentes presentes en el sector correspondiente."""
        return self.sector_map.get((x // self.sector_size, y // self.sector_size), [])

    def get_resources_at(self, x: int, y: int) -> float:
        """Calcula de forma determinista la disponibilidad de recursos (0.0 a 1.0).
        
        Utiliza matemáticas procedimentales (ruido trigonométrico) para generar 
        "biomas" o zonas fértiles persistentes, sin consumir memoria RAM en matrices.
        """
        # 1. Bioma natural (Oasis vs Desiertos)
        ruido = (math.sin(x * 0.15) + math.cos(y * 0.15)) / 2.0
        recurso_base = (ruido + 1.0) / 2.0  # Normalizado entre 0.0 y 1.0
        
        # 2. Desgaste por sobreexplotación (Hambre poblacional)
        sector_key = (x // self.sector_size, y // self.sector_size)
        consumidores = len(self.sector_map.get(sector_key, []))
        
        # CORRECCIÓN: Usar max_agents_per_sector para que el desgaste sea coherente 
        # con la mecánica de presión. Si el sector está lleno, el desgaste es máximo.
        desgaste = (consumidores / max(1, self.max_agents_per_sector)) * 0.8
        
        return max(0.0, min(1.0, recurso_base - desgaste))