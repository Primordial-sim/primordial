"""Modelo de partícula hereditaria fundamental (Leyes de Mendel).

ACTUALIZACIÓN: Soporte para múltiples modelos de expresión genética.

Modelos disponibles:
- DOMINANT: Gana el alelo con mayor dominancia (comportamiento original)
- RECESSIVE: Gana el alelo con menor dominancia
- CODOMINANT: Ambos alelos se expresan (promedio simple)
- WEIGHTED_AVERAGE: Promedio ponderado por dominancia
- ADDITIVE: Suma de ambos alelos (efecto aditivo)
- MAX_VALUE: Se expresa el valor máximo
- MIN_VALUE: Se expresa el valor mínimo

El modelo por defecto es DOMINANT (retrocompatible con el código existente).
"""

import random
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Allele:
    """Unidad básica de herencia que codifica una variante de un rasgo.
    
    Es inmutable tras su creación. Contiene tanto la expresión del rasgo 
    como su fuerza de dominancia relativa.
    """
    value: float
    dominance: float

    @classmethod
    def create_random(
        cls, 
        base_value: float, 
        mutation_range: float = 0.0,
        min_value: float = 0.1,
        max_value: float = 3.0,
    ) -> 'Allele':
        """Instancia un alelo aplicando deriva genética inicial.
        
        Args:
            base_value: El valor fenotípico central del rasgo (e.g., 1.0).
            mutation_range: Variación máxima al momento de la creación.
            min_value: Valor mínimo permitido (clampeo inferior).
            max_value: Valor máximo permitido (clampeo superior).
            
        Returns:
            Un nuevo alelo con una fuerza de dominancia estocástica.
        """
        dominance_strength = random.random()
        
        mutated_value = base_value
        if mutation_range > 0:
            mutated_value += random.uniform(-mutation_range, mutation_range)
        
        # Clamping biológico al rango permitido
        final_value = max(min_value, min(max_value, mutated_value))
        
        return cls(value=final_value, dominance=dominance_strength)


class Gene:
    """Locus genético compuesto por un par de alelos (Diploidía)."""

    def __init__(self, allele_a: Allele, allele_b: Allele) -> None:
        """Inicializa un gen con los alelos aportados por los progenitores."""
        self.allele_a = allele_a
        self.allele_b = allele_b

    def express(self, expression_model: Optional[str] = None) -> float:
        """Calcula el fenotipo (rasgo visible) basado en el modelo de expresión.
        
        Args:
            expression_model: Modelo de expresión a usar.
                             Si es None, usa DOMINANT (retrocompatible).
        
        Returns:
            El valor numérico del fenotipo.
        
        Modelos disponibles:
        - DOMINANT: Gana el alelo con mayor dominancia (original)
        - RECESSIVE: Gana el alelo con menor dominancia
        - CODOMINANT: Promedio simple de ambos alelos
        - WEIGHTED_AVERAGE: Promedio ponderado por dominancia
        - ADDITIVE: Suma de ambos alelos
        - MAX_VALUE: El valor máximo de ambos
        - MIN_VALUE: El valor mínimo de ambos
        """
        # Modelo por defecto: DOMINANT (retrocompatible)
        if expression_model is None or expression_model == "DOMINANT":
            if self.allele_a.dominance >= self.allele_b.dominance:
                return self.allele_a.value
            return self.allele_b.value
        
        elif expression_model == "RECESSIVE":
            # Gana el alelo con menor dominancia
            if self.allele_a.dominance <= self.allele_b.dominance:
                return self.allele_a.value
            return self.allele_b.value
        
        elif expression_model == "CODOMINANT":
            # Ambos alelos se expresan (promedio simple)
            return (self.allele_a.value + self.allele_b.value) / 2.0
        
        elif expression_model == "WEIGHTED_AVERAGE":
            # Promedio ponderado por dominancia
            total_dominance = self.allele_a.dominance + self.allele_b.dominance
            if total_dominance == 0:
                return (self.allele_a.value + self.allele_b.value) / 2.0
            return (
                (self.allele_a.value * self.allele_a.dominance +
                 self.allele_b.value * self.allele_b.dominance) / total_dominance
            )
        
        elif expression_model == "ADDITIVE":
            # Suma de ambos alelos (efecto aditivo)
            return self.allele_a.value + self.allele_b.value
        
        elif expression_model == "MAX_VALUE":
            # Se expresa el valor máximo
            return max(self.allele_a.value, self.allele_b.value)
        
        elif expression_model == "MIN_VALUE":
            # Se expresa el valor mínimo
            return min(self.allele_a.value, self.allele_b.value)
        
        else:
            # Modelo desconocido, usar dominancia (fallback seguro)
            if self.allele_a.dominance >= self.allele_b.dominance:
                return self.allele_a.value
            return self.allele_b.value

    def meiosis(self) -> Allele:
        """Segregación independiente: devuelve un alelo al azar para la herencia."""
        return self.allele_a if random.random() < 0.5 else self.allele_b