"""Módulo responsable de la gestión espacial a nivel de celda.

Provee una cuadrícula para consultar ocupantes exactos, validar movimientos
y calcular densidades locales de forma acotada y segura.
"""

from typing import List, Dict, Any

class WorldGrid:
    def __init__(self, width: int, height: int, max_occupants_per_cell: int = 1) -> None:
        self.width = width
        self.height = height
        self.max_occupants = max_occupants_per_cell  # Permite configurar si se permite apilamiento
        self._cells: Dict[tuple, List[Any]] = {}

    def get_occupants_at(self, x: int, y: int) -> List[Any]:
        """Devuelve la lista de agentes en una coordenada específica."""
        return self._cells.get((x, y), [])

    def can_move_to(self, x: int, y: int) -> bool:
        """Verifica si hay espacio en la celda destino (respeta límites y capacidad)."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return len(self.get_occupants_at(x, y)) < self.max_occupants

    def place_person(self, person: Any, x: int, y: int) -> None:
        """Coloca a un agente en una coordenada, asegurando límites válidos."""
        # Clamp a los límites del mapa por seguridad
        x = max(0, min(x, self.width - 1))
        y = max(0, min(y, self.height - 1))
        
        if (x, y) not in self._cells:
            self._cells[(x, y)] = []
        self._cells[(x, y)].append(person)
        person.x = x
        person.y = y

    def remove_person(self, person: Any) -> None:
        """Elimina a un agente de su celda actual y limpia la celda si queda vacía."""
        coord = (person.x, person.y)
        if coord in self._cells and person in self._cells[coord]:
            self._cells[coord].remove(person)
            if not self._cells[coord]:
                del self._cells[coord]

    def get_density_at(self, x: int, y: int) -> int:
        """Devuelve cuántas personas hay en una coordenada específica."""
        return len(self.get_occupants_at(x, y))

    def get_area_density(self, x: int, y: int, radius: int) -> int:
        """Devuelve la densidad total en un radio alrededor de un punto.
        
        OPTIMIZACIÓN: Acota el bucle a los límites del mapa para evitar 
        consultas innecesarias o índices negativos.
        """
        count = 0
        min_x = max(0, x - radius)
        max_x = min(self.width - 1, x + radius)
        min_y = max(0, y - radius)
        max_y = min(self.height - 1, y + radius)
        
        for i in range(min_x, max_x + 1):
            for j in range(min_y, max_y + 1):
                count += len(self._cells.get((i, j), []))
        return count