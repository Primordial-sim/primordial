"""Mapa de tiles del mundo.

Almacena el grid completo de tiles y proporciona acceso eficiente.
El mapa se genera proceduralmente en la Sesión 3, pero esta clase
define la estructura de almacenamiento.
"""

from __future__ import annotations

from typing import Dict, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from systems.environment.tile import Tile


class TileMap:
    """Grid de tiles del mundo con acceso por coordenadas.
    
    Attributes:
        width: Ancho del mapa en tiles
        height: Alto del mapa en tiles
        tiles: Diccionario de (x, y) -> Tile
    """
    
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.tiles: Dict[Tuple[int, int], Tile] = {}
    
    def set_tile(self, x: int, y: int, tile: Tile) -> None:
        """Establece un tile en la posición dada."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[(x, y)] = tile
    
    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        """Retorna el tile en la posición dada, o None si no existe."""
        return self.tiles.get((int(x), int(y)))
    
    def has_tile(self, x: int, y: int) -> bool:
        """Verifica si existe un tile en la posición dada."""
        return (int(x), int(y)) in self.tiles
    
    def get_all_tiles(self) -> list[Tile]:
        """Retorna todos los tiles del mapa."""
        return list(self.tiles.values())
    
    def get_tile_count(self) -> int:
        """Retorna el número de tiles en el mapa."""
        return len(self.tiles)
    
    def is_initialized(self) -> bool:
        """Verifica si el mapa ha sido inicializado (tiene tiles)."""
        return len(self.tiles) > 0