"""Estructura de datos espacial para el rastreo de cargas virales ambientales.

MIGRACIÓN HEXAGONAL:
- Coordenadas (x, y) → (q, r)
- El grid sigue siendo un sparse grid, pero usa coordenadas hexagonales
"""

from collections import defaultdict
import logging


class EpidemiologicalMap:
    """Almacén de datos (Sparse Grid) para la concentración de patógenos en el mapa.
    
    HEX: Usa coordenadas hexagonales (q, r) en lugar de cartesianas (x, y).
    """

    def __init__(self, max_viral_load: float) -> None:
        """Inicializa la cuadrícula dispersa con el límite biológico del virus."""
        # defaultdict permite no consumir memoria RAM en zonas seguras (vacías)
        self.grid = defaultdict(float)
        self.max_viral_load = max_viral_load
        self.logger = logging.getLogger("EpidemiologicalMap")

    def add_viral_load(self, q: int, r: int, amount: float) -> None:
        """Incrementa la carga viral de una coordenada hexagonal, topada por el límite máximo.
        
        Args:
            q: Coordenada Q (hexagonal).
            r: Coordenada R (hexagonal).
            amount: Cantidad de carga viral a añadir.
        """
        coord = (int(q), int(r))
        new_val = self.grid[coord] + amount
        self.grid[coord] = min(new_val, self.max_viral_load)

    def get_viral_load(self, q: int, r: int) -> float:
        """Devuelve la carga viral presente en una coordenada hexagonal específica.
        
        Args:
            q: Coordenada Q (hexagonal).
            r: Coordenada R (hexagonal).
            
        Returns:
            Carga viral en esa coordenada, o 0.0 si no hay.
        """
        return self.grid.get((int(q), int(r)), 0.0)

    def decay_viral_load(self, factor: float) -> None:
        """Aplica disipación atmosférica reduciendo la carga de todo el mapa.
        
        Elimina las coordenadas cuya carga es insignificante para liberar memoria.
        
        Args:
            factor: Factor de decaimiento (0.0 a 1.0). Ej: 0.95 = 5% de disipación.
        """
        keys_to_delete = []
        for coord in self.grid:
            self.grid[coord] *= factor
            if self.grid[coord] < 0.01:
                keys_to_delete.append(coord)

        for coord in keys_to_delete:
            del self.grid[coord]