"""Configuración física global del mundo.

Define las leyes físicas del mundo antes de generar el terreno:
gravedad, temperatura media, nivel del mar, cantidad de agua, etc.

Estos parámetros son constantes globales que afectan a todo el mapa.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WorldConfig:
    """Parámetros físicos globales del mundo.
    
    Attributes:
        gravity: Gravedad relativa (1.0 = Tierra)
        mean_temperature: Temperatura media global [0.0, 1.0]
        sea_level: Nivel del mar en metros
        water_coverage: Fracción del mundo cubierta por agua [0.0, 1.0]
        radiation: Radiación solar relativa [0.0, 1.0]
        geological_activity: Actividad geológica [0.0, 1.0]
        erosion_rate: Tasa de erosión global [0.0, 1.0]
        global_humidity: Humedad global base [0.0, 1.0]
    """
    
    gravity: float = 1.0
    mean_temperature: float = 0.5
    sea_level: float = 0.0
    water_coverage: float = 0.7
    radiation: float = 0.5
    geological_activity: float = 0.3
    erosion_rate: float = 0.5
    global_humidity: float = 0.5
    
    def to_dict(self) -> dict:
        """Serializa la configuración para debugging."""
        return {
            'gravity': self.gravity,
            'mean_temperature': self.mean_temperature,
            'sea_level': self.sea_level,
            'water_coverage': self.water_coverage,
            'radiation': self.radiation,
            'geological_activity': self.geological_activity,
            'erosion_rate': self.erosion_rate,
            'global_humidity': self.global_humidity,
        }