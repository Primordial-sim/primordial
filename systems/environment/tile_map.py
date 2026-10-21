"""Mapa de tiles del mundo.

Almacena el grid completo de tiles hexagonales y proporciona acceso eficiente.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from systems.environment.tile import Tile


class TileMap:
    """Grid de tiles del mundo con acceso por coordenadas hexagonales.
    
    Attributes:
        width: Ancho del mapa en tiles (q).
        height: Alto del mapa en tiles (r).
        tiles: Diccionario de (q, r) -> Tile.
    """
    
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.tiles: Dict[Tuple[int, int], Tile] = {}
    
    def set_tile(self, q: int, r: int, tile: Tile) -> None:
        """Establece un tile en la posición dada."""
        if 0 <= q < self.width and 0 <= r < self.height:
            self.tiles[(q, r)] = tile
    
    def get_tile(self, q: int, r: int) -> Optional[Tile]:
        """Retorna el tile en la posición dada, o None si no existe."""
        return self.tiles.get((int(q), int(r)))
    
    def has_tile(self, q: int, r: int) -> bool:
        """Verifica si existe un tile en la posición dada."""
        return (int(q), int(r)) in self.tiles
    
    def get_all_tiles(self) -> list[Tile]:
        """Retorna todos los tiles del mapa."""
        return list(self.tiles.values())
    
    def get_tile_count(self) -> int:
        """Retorna el número de tiles en el mapa."""
        return len(self.tiles)
    
    def is_initialized(self) -> bool:
        """Verifica si el mapa ha sido inicializado (tiene tiles)."""
        return len(self.tiles) > 0