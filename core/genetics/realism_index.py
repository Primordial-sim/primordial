"""Índice de Realismo.

Calcula un nivel de realismo (0-100%) según la combinación de rasgos.
Este índice NO modifica la simulación; solo informa al usuario.

Se basa en el score del Validador Biológico, que evalúa la coherencia
de la combinación de rasgos.
"""

from __future__ import annotations

from typing import Optional
import logging

from core.genetics.trait import TraitCategory
from core.genetics.trait_library import TraitLibrary
from core.genetics.species_definition import SpeciesDefinition
from core.genetics.biological_validator import BiologicalValidator, ValidationResult


class RealismIndex:
    """Calcula el índice de realismo de una especie.
    
    El índice es un valor entre 0.0 y 1.0 (0% a 100%).
    NO afecta la simulación; es puramente informativo.
    
    Se basa en:
    - Score del Validador Biológico (coherencia de rasgos)
    - Presencia de rasgos fundamentales
    - Ausencia de contradicciones
    """
    
    _logger = logging.getLogger("RealismIndex")
    
    def __init__(
        self,
        library: Optional[TraitLibrary] = None,
        validator: Optional[BiologicalValidator] = None,
    ) -> None:
        self._library = library or TraitLibrary.get_default()
        self._validator = validator or BiologicalValidator(self._library)
    
    def calculate(self, species: SpeciesDefinition) -> float:
        """Calcula el índice de realismo de una especie.
        
        Args:
            species: La especie a evaluar.
            
        Returns:
            Valor entre 0.0 (completamente fantástico) y 1.0 (completamente realista).
        """
        # El score principal viene del validador
        result = self._validator.validate_species(species)
        base_score = result.score
        
        # Ajustes adicionales
        adjustment = 0.0
        
        # Bonus por tener rasgos biológicos fundamentales
        biology_count = self._count_traits_in_category(species, TraitCategory.BIOLOGY)
        if biology_count >= 3:
            adjustment += 0.05
        
        # Penalización por muchos rasgos fantásticos
        special_count = self._count_traits_in_category(species, TraitCategory.SPECIAL)
        adjustment -= special_count * 0.05
        
        # Bonus por diversidad de categorías
        categories = self._count_categories(species)
        if categories >= 3:
            adjustment += 0.03
        
        final_score = max(0.0, min(1.0, base_score + adjustment))
        return final_score
    
    def calculate_with_result(
        self, species: SpeciesDefinition, result: ValidationResult
    ) -> float:
        """Calcula el índice usando un resultado de validación existente."""
        base_score = result.score
        
        adjustment = 0.0
        biology_count = self._count_traits_in_category(species, TraitCategory.BIOLOGY)
        if biology_count >= 3:
            adjustment += 0.05
        
        special_count = self._count_traits_in_category(species, TraitCategory.SPECIAL)
        adjustment -= special_count * 0.05
        
        categories = self._count_categories(species)
        if categories >= 3:
            adjustment += 0.03
        
        return max(0.0, min(1.0, base_score + adjustment))
    
    def _count_traits_in_category(
        self, species: SpeciesDefinition, category: TraitCategory
    ) -> int:
        """Cuenta los rasgos de una categoría en la especie."""
        count = 0
        for trait_id in species.get_all_trait_ids():
            trait = self._library.get_trait(trait_id)
            if trait and trait.category == category:
                count += 1
        return count
    
    def _count_categories(self, species: SpeciesDefinition) -> int:
        """Cuenta cuántas categorías diferentes tiene la especie."""
        categories = set()
        for trait_id in species.get_all_trait_ids():
            trait = self._library.get_trait(trait_id)
            if trait:
                categories.add(trait.category)
        return len(categories)
    
    def get_description(self, score: float) -> str:
        """Retorna una descripción textual del índice de realismo."""
        percentage = int(score * 100)
        
        if percentage >= 90:
            return f"Realismo: {percentage}% - Especie biológicamente coherente."
        elif percentage >= 70:
            return f"Realismo: {percentage}% - Especie mayormente realista con algunas peculiaridades."
        elif percentage >= 50:
            return f"Realismo: {percentage}% - Especie con características mixtas."
        elif percentage >= 30:
            return f"Realismo: {percentage}% - Especie con características fantásticas."
        else:
            return f"Realismo: {percentage}% - Especie completamente fantástica."