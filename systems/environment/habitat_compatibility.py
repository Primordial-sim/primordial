"""Calculador de compatibilidad entre especies y tiles.

Determina qué tan adecuado es un tile para una especie específica,
basándose en las preferencias de hábitat de la especie y las variables
ambientales reales del tile.

La compatibilidad es un valor [0.0, 1.0]:
- 1.0 = Perfecto: el tile cumple todas las preferencias de la especie
- 0.5 = Aceptable: el tile es habitable pero no ideal
- 0.0 = Inhabitable: el tile no cumple las necesidades mínimas
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from systems.environment.tile import Tile
    from systems.environment.habitat_preference import HabitatPreference


class HabitatCompatibility:
    """Calcula la compatibilidad entre una especie y un tile."""
    
    @staticmethod
    def calculate(
        tile: 'Tile',
        preference: 'HabitatPreference',
    ) -> float:
        """Calcula la compatibilidad entre un tile y las preferencias de hábitat.
        
        Usa una función gaussiana ponderada para cada variable:
        - Cuanto más cerca del ideal, mayor puntuación
        - La tolerancia determina qué tan rápido cae la puntuación
        
        Args:
            tile: El tile a evaluar.
            preference: Las preferencias de hábitat de la especie.
            
        Returns:
            Puntuación de compatibilidad [0.0, 1.0].
        """
        # Calcular puntuación para cada variable
        scores = []
        weights = []
        
        # Temperatura (peso alto: muy importante)
        scores.append(HabitatCompatibility._score_variable(
            tile.temperature,
            preference.temperature_ideal,
            preference.temperature_tolerance,
        ))
        weights.append(1.5)
        
        # Humedad (peso medio-alto)
        scores.append(HabitatCompatibility._score_variable(
            tile.humidity,
            preference.humidity_ideal,
            preference.humidity_tolerance,
        ))
        weights.append(1.2)
        
        # Agua (peso alto: crítico para muchas especies)
        scores.append(HabitatCompatibility._score_variable(
            tile.water,
            preference.water_ideal,
            preference.water_tolerance,
        ))
        weights.append(1.5)
        
        # Vegetación (peso medio)
        scores.append(HabitatCompatibility._score_variable(
            tile.vegetation,
            preference.vegetation_ideal,
            preference.vegetation_tolerance,
        ))
        weights.append(1.0)
        
        # Altitud (peso medio-bajo)
        scores.append(HabitatCompatibility._score_variable(
            HabitatCompatibility._normalize_altitude(tile.height),
            preference.altitude_ideal,
            preference.altitude_tolerance,
        ))
        weights.append(0.8)
        
        # Pendiente (peso medio-bajo)
        scores.append(HabitatCompatibility._score_variable(
            tile.slope,
            preference.slope_ideal,
            preference.slope_tolerance,
        ))
        weights.append(0.8)
        
        # Fertilidad (peso medio)
        scores.append(HabitatCompatibility._score_variable(
            tile.fertility,
            preference.fertility_ideal,
            preference.fertility_tolerance,
        ))
        weights.append(1.0)
        
        # Salinidad (peso alto para especies acuáticas)
        scores.append(HabitatCompatibility._score_variable(
            tile.salinity,
            preference.salinity_ideal,
            preference.salinity_tolerance,
        ))
        weights.append(1.3)
        
        # Rococidad (peso bajo)
        scores.append(HabitatCompatibility._score_variable(
            tile.rockiness,
            preference.rockiness_ideal,
            preference.rockiness_tolerance,
        ))
        weights.append(0.7)
        
        # Media ponderada
        total_score = sum(s * w for s, w in zip(scores, weights))
        total_weight = sum(weights)
        
        return total_score / total_weight
    
    @staticmethod
    def _score_variable(
        actual: float,
        ideal: float,
        tolerance: float,
    ) -> float:
        """Calcula la puntuación de una variable individual.
        
        Usa una función gaussiana: score = exp(-((actual - ideal) / tolerance)^2)
        - Si actual == ideal: score = 1.0
        - Si |actual - ideal| == tolerance: score ≈ 0.37
        - Si |actual - ideal| == 2 * tolerance: score ≈ 0.018
        
        Args:
            actual: Valor real de la variable en el tile.
            ideal: Valor ideal para la especie.
            tolerance: Tolerancia de la especie a esta variable.
            
        Returns:
            Puntuación [0.0, 1.0].
        """
        if tolerance <= 0.0:
            # Sin tolerancia: solo el valor ideal es aceptable
            return 1.0 if abs(actual - ideal) < 0.01 else 0.0
        
        import math
        deviation = (actual - ideal) / tolerance
        score = math.exp(-deviation * deviation)
        
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def _normalize_altitude(height: float) -> float:
        """Convierte altitud en metros a un valor [0.0, 1.0].
        
        Asume que:
        - -500m (océano profundo) = 0.0
        - 0m (nivel del mar) = 0.2
        - 3000m (montaña alta) = 1.0
        """
        # Normalizar: -500 → 0.0, 0 → 0.2, 3000 → 1.0
        normalized = (height + 500.0) / 3500.0
        return max(0.0, min(1.0, normalized))
    
    @staticmethod
    def get_compatibility_level(score: float) -> str:
        """Convierte un score numérico en una categoría legible.
        
        Args:
            score: Puntuación de compatibilidad [0.0, 1.0].
            
        Returns:
            Categoría: "inhabitable", "poor", "acceptable", "good", "ideal"
        """
        if score >= 0.85:
            return "ideal"
        elif score >= 0.65:
            return "good"
        elif score >= 0.45:
            return "acceptable"
        elif score >= 0.25:
            return "poor"
        else:
            return "inhabitable"