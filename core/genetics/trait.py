"""Definición de un rasgo hereditario individual.

FILOSOFÍA: Un rasgo es completamente NEUTRO.
- No conoce especies.
- No conoce biología.
- No conoce incompatibilidades.
- No conoce requisitos.

Toda la biología pertenece a:
- Las Plantillas de Especie (qué rasgos activan)
- El Validador Biológico (qué combinaciones son coherentes)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class TraitCategory(Enum):
    """Categorías de rasgos para organización."""
    BIOLOGY = auto()         # Rasgos biológicos fundamentales
    BEHAVIOR = auto()        # Rasgos de comportamiento
    PERCEPTION = auto()      # Rasgos de percepción sensorial
    MOVEMENT = auto()        # Rasgos de movimiento y locomoción
    SPECIAL = auto()         # Rasgos especiales o fantásticos


class ExpressionModel(Enum):
    """Modelo de expresión genética: cómo se combinan los dos alelos.
    
    Cada rasgo puede definir cómo se expresa su fenotipo.
    Esto permite simular diferentes tipos de herencia:
    
    - DOMINANT: Gana el alelo con mayor dominancia (herencia mendeliana clásica)
    - RECESSIVE: Gana el alelo con menor dominancia
    - CODOMINANT: Ambos alelos se expresan (promedio simple)
    - WEIGHTED_AVERAGE: Promedio ponderado por dominancia
    - ADDITIVE: Suma de ambos alelos (efecto aditivo)
    - MAX_VALUE: Se expresa el valor máximo
    - MIN_VALUE: Se expresa el valor mínimo
    """
    DOMINANT = auto()
    RECESSIVE = auto()
    CODOMINANT = auto()
    WEIGHTED_AVERAGE = auto()
    ADDITIVE = auto()
    MAX_VALUE = auto()
    MIN_VALUE = auto()


class Distribution(Enum):
    """Tipo de distribución inicial para la población fundadora.
    
    Determina cómo se generan los valores iniciales de los alelos
    cuando se crea una población fundadora.
    """
    NORMAL = auto()            # Distribución normal (campana de Gauss)
    UNIFORM = auto()           # Distribución uniforme
    FIXED = auto()             # Valor fijo sin variación


@dataclass(frozen=True)
class Trait:
    """Definición inmutable de un rasgo hereditario.
    
    Un rasgo es completamente NEUTRO. Solo describe:
    - Qué es el rasgo (id, nombre, categoría)
    - Cómo se expresa (modelo de expresión)
    - Qué rango de valores tiene (min, max)
    - Cómo se distribuye inicialmente (distribución, media, desviación)
    - Su peso evolutivo (impacto en selección natural)
    - Su heredabilidad (0.0 = adquirido, 1.0 = completamente genético)
    
    NO describe:
    - Con qué rasgos es incompatible (eso va en el Validador)
    - Qué rasgos requiere (eso va en el Validador)
    - Qué especies lo usan (eso va en las Plantillas)
    
    Attributes:
        trait_id: Identificador único del rasgo (ej: "fertility", "flight").
        name: Nombre legible del rasgo (ej: "Fertilidad", "Vuelo").
        category: Categoría del rasgo.
        min_value: Valor mínimo posible.
        max_value: Valor máximo posible.
        default_value: Valor por defecto para la especie.
        expression_model: Cómo se combinan los dos alelos.
        evolutionary_weight: Peso evolutivo (impacto en selección natural).
        heritability: Grado de heredabilidad (0.0 = adquirido, 1.0 = genético).
        initial_distribution: Tipo de distribución inicial.
        initial_mean: Media de la distribución inicial (None = usar default_value).
        initial_std: Desviación típica de la distribución inicial.
        description: Descripción del rasgo para documentación.
    """
    trait_id: str
    name: str
    category: TraitCategory
    min_value: float = 0.0
    max_value: float = 1.0
    default_value: float = 0.5
    expression_model: ExpressionModel = ExpressionModel.DOMINANT
    evolutionary_weight: float = 1.0
    heritability: float = 1.0
    initial_distribution: Distribution = Distribution.NORMAL
    initial_mean: Optional[float] = None
    initial_std: float = 0.1
    description: str = ""
    
    def clamp_value(self, value: float) -> float:
        """Limita un valor al rango válido del rasgo."""
        return max(self.min_value, min(self.max_value, value))
    
    def get_initial_mean(self) -> float:
        """Retorna la media para la distribución inicial."""
        return self.initial_mean if self.initial_mean is not None else self.default_value
    
    def __repr__(self) -> str:
        return f"Trait({self.trait_id}: {self.name} [{self.category.name}])"