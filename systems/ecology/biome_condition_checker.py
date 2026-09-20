"""Verificador de condiciones ambientales para relaciones ecológicas.

Verifica si las condiciones del bioma y la estación permiten
una relación ecológica específica.

Filosofía: "Las relaciones ecológicas existen únicamente cuando
el entorno las permite."
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from systems.ecology.ecological_relationship import EcologicalRelationship
    from systems.environment.tile import Tile


class BiomeConditionChecker:
    """Verifica si las condiciones ambientales permiten una relación.
    
    Uso:
        checker = BiomeConditionChecker()
        
        # Verificar si la relación es válida en el tile actual
        is_valid = checker.check(relationship, tile, current_season)
    """
    
    _logger = logging.getLogger("BiomeConditionChecker")
    
    def __init__(self) -> None:
        pass
    
    def check(
        self,
        relationship: 'EcologicalRelationship',
        tile: 'Tile',
        current_season: str,
    ) -> bool:
        """Verifica si la relación es válida en las condiciones actuales.
        
        Args:
            relationship: La relación ecológica a verificar.
            tile: El tile donde ocurre la interacción.
            current_season: La estación actual ("spring", "summer", etc.)
            
        Returns:
            True si la relación puede ocurrir, False en caso contrario.
        """
        # Verificar requisitos de bioma
        if not self._check_biome(relationship, tile):
            return False
        
        # Verificar restricciones estacionales
        if not self._check_season(relationship, current_season):
            return False
        
        return True
    
    def _check_biome(
        self,
        relationship: 'EcologicalRelationship',
        tile: 'Tile',
    ) -> bool:
        """Verifica si el bioma del tile permite la relación.
        
        Si la relación no tiene requisitos de bioma, siempre es válida.
        Si tiene requisitos, el tile debe cumplir al menos uno.
        """
        if not relationship.biome_requirements:
            return True  # Sin requisitos = válida en todos los biomas
        
        # Obtener el bioma del tile
        biome_name = self._get_biome_name(tile)
        
        # Verificar si el bioma está en los requisitos
        return biome_name in relationship.biome_requirements
    
    def _check_season(
        self,
        relationship: 'EcologicalRelationship',
        current_season: str,
    ) -> bool:
        """Verifica si la estación actual permite la relación.
        
        Si la relación no tiene restricciones estacionales, siempre es válida.
        """
        if not relationship.seasonal_constraints:
            return True  # Sin restricciones = válida todo el año
        
        return current_season.lower() in relationship.seasonal_constraints
    
    def _get_biome_name(self, tile: 'Tile') -> str:
        """Obtiene el nombre del bioma de un tile.
        
        Simplificación: usa las propiedades del tile para inferir el bioma.
        En el futuro se puede usar el BiomeClassifier completo.
        """
        # Clasificación simplificada basada en propiedades del tile
        if tile.water > 0.7:
            return "ocean"
        elif tile.water > 0.5:
            return "lake"
        elif tile.temperature < 0.2:
            return "tundra"
        elif tile.temperature > 0.8 and tile.water < 0.2:
            return "desert"
        elif tile.temperature > 0.6 and tile.vegetation > 0.6:
            return "rainforest"
        elif tile.vegetation > 0.5:
            return "forest"
        elif tile.vegetation > 0.2:
            return "grassland"
        else:
            return "barren"