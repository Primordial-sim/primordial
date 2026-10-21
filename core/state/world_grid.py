"""Módulo responsable de la gestión espacial a nivel de celda (Hexagonal).

Provee una cuadrícula hexagonal para consultar ocupantes exactos, validar 
movimientos y calcular densidades locales de forma acotada y segura.
"""

from typing import Any, Dict, List, Tuple


class WorldGrid:
    """Gestiona la ocupación y densidad en un grid hexagonal."""

    def __init__(self, width: int, height: int, max_occupants_per_cell: int = 1) -> None:
        """Inicializa la cuadrícula hexagonal.
        
        Args:
            width: Ancho del mundo en celdas hexagonales (q).
            height: Alto del mundo en celdas hexagonales (r).
            max_occupants_per_cell: Máximo de agentes permitidos por celda.
        """
        self.width = width
        self.height = height
        self.max_occupants = max_occupants_per_cell
        self._cells: Dict[Tuple[int, int], List[Any]] = {}

    def get_occupants_at(self, q: int, r: int) -> List[Any]:
        """Devuelve la lista de agentes en una coordenada hexagonal específica."""
        return self._cells.get((q, r), [])

    def can_move_to(self, q: int, r: int) -> bool:
        """Verifica si hay espacio en la celda destino (respeta límites y capacidad)."""
        if not (0 <= q < self.width and 0 <= r < self.height):
            return False
        return len(self.get_occupants_at(q, r)) < self.max_occupants

    def place_person(self, person: Any, q: int, r: int) -> None:
        """Coloca a un agente en una coordenada, asegurando límites válidos."""
        q = max(0, min(q, self.width - 1))
        r = max(0, min(r, self.height - 1))
        
        if (q, r) not in self._cells:
            self._cells[(q, r)] = []
            
        self._cells[(q, r)].append(person)
        person.q = q
        person.r = r

    def remove_person(self, person: Any) -> None:
        """Elimina a un agente de su celda actual y limpia la celda si queda vacía."""
        coord = (person.q, person.r)
        if coord in self._cells and person in self._cells[coord]:
            self._cells[coord].remove(person)
            if not self._cells[coord]:
                del self._cells[coord]

    def get_density_at(self, q: int, r: int) -> int:
        """Devuelve cuántas personas hay en una coordenada específica."""
        return len(self.get_occupants_at(q, r))

    def get_area_density(self, q: int, r: int, radius: int) -> int:
        """Devuelve la densidad total en un radio hexagonal alrededor de un punto.
        
        OPTIMIZACIÓN: Acota el bucle a los límites del mapa en forma de hexágono 
        para evitar consultas innecesarias o índices negativos.
        """
        count = 0
        for dq in range(-radius, radius + 1):
            dr_min = max(-radius, -dq - radius)
            dr_max = min(radius, -dq + radius)
            for dr in range(dr_min, dr_max + 1):
                nq = q + dq
                nr = r + dr
                if 0 <= nq < self.width and 0 <= nr < self.height:
                    count += len(self._cells.get((nq, nr), []))
        return count