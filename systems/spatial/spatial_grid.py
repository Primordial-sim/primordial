"""Grid espacial para optimización de búsquedas de vecinos.

Reduce la complejidad de búsquedas de vecinos de O(N²) a O(N)
mediante la división del mundo en sectores (celdas).

Cada tick:
1. Se limpia el grid
2. Se insertan todos los agentes según su posición
3. Las búsquedas de vecinos solo revisan celdas adyacentes

Uso:
    grid = SpatialGrid(cell_size=35.0)
    grid.populate_from_state(state)
    nearby = grid.get_nearby_agents(agent, radius=35.0)
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
from collections import defaultdict


class SpatialGrid:
    """Grid espacial para búsquedas O(1) de vecinos cercanos.
    
    Divide el mundo en celdas cuadradas. Cada agente se almacena
    en la celda correspondiente a su posición. Para buscar vecinos,
    solo se revisan las celdas adyacentes.
    """
    
    __slots__ = ('cell_size', 'grid', '_agent_to_cell')
    
    def __init__(self, cell_size: float = 35.0):
        """Inicializa el grid con un tamaño de celda específico.
        
        Args:
            cell_size: Tamaño de cada celda en unidades del mundo.
                       Debe ser >= al radio de búsqueda más grande.
        """
        self.cell_size = cell_size
        self.grid: Dict[Tuple[int, int], List[Any]] = defaultdict(list)
        self._agent_to_cell: Dict[int, Tuple[int, int]] = {}
    
    def clear(self) -> None:
        """Limpia el grid para el nuevo tick."""
        self.grid.clear()
        self._agent_to_cell.clear()
    
    def add_agent(self, agent: Any) -> None:
        """Añade un agente al grid basado en su posición.
        
        Args:
            agent: Agente con atributos x, y y entity_id.
        """
        cell_x = int(agent.x // self.cell_size)
        cell_y = int(agent.y // self.cell_size)
        cell = (cell_x, cell_y)
        
        self.grid[cell].append(agent)
        self._agent_to_cell[agent.entity_id] = cell
    
    def get_nearby_agents(self, agent: Any, radius: float) -> List[Any]:
        """Retorna agentes dentro del radio especificado.
        
        Usa el grid para limitar la búsqueda a celdas adyacentes,
        reduciendo la complejidad de O(N) a O(k) donde k es el
        número de agentes en las celdas cercanas.
        
        Args:
            agent: Agente central para la búsqueda.
            radius: Radio de búsqueda en unidades del mundo.
            
        Returns:
            Lista de agentes dentro del radio (excluyendo al agente central).
        """
        cell_x = int(agent.x // self.cell_size)
        cell_y = int(agent.y // self.cell_size)
        
        # Calcular cuántas celdas buscar en cada dirección
        cells_to_check = int(radius / self.cell_size) + 1
        
        nearby: List[Any] = []
        radius_sq = radius * radius
        agent_x = agent.x
        agent_y = agent.y
        agent_id = agent.entity_id
        
        for dx in range(-cells_to_check, cells_to_check + 1):
            for dy in range(-cells_to_check, cells_to_check + 1):
                cell = (cell_x + dx, cell_y + dy)
                if cell in self.grid:
                    for other in self.grid[cell]:
                        if other.entity_id != agent_id:
                            # Verificación de distancia al cuadrado (sin sqrt)
                            dist_sq = (agent_x - other.x) ** 2 + (agent_y - other.y) ** 2
                            if dist_sq <= radius_sq:
                                nearby.append(other)
        
        return nearby
    
    def populate_from_state(self, state: Any) -> None:
        """Puebla el grid con todos los agentes del estado.
        
        Debe llamarse una vez por tick al inicio de la fase de relaciones.
        
        Args:
            state: WorldState con get_all_persons().
        """
        self.clear()
        for person in state.get_all_persons():
            self.add_agent(person)
    
    def get_agent_cell(self, entity_id: int) -> Tuple[int, int] | None:
        """Retorna la celda donde está un agente.
        
        Args:
            entity_id: ID del agente.
            
        Returns:
            Tupla (cell_x, cell_y) o None si no existe.
        """
        return self._agent_to_cell.get(entity_id)