"""Modelo de Tile con variables ambientales continuas.

Cada tile del mundo almacena variables físicas continuas (altura, temperatura,
humedad, agua, vegetación, etc.). Los biomas NO se almacenan, se calculan
dinámicamente a partir de estas variables.

Principio fundamental: "El bioma es una consecuencia, no un dato."
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Tile:
    """Representa una casilla del mundo con variables ambientales continuas.
    
    Todas las variables están normalizadas en el rango [0.0, 1.0] excepto
    'height' que usa una escala absoluta (metros sobre el nivel del mar).
    
    Attributes:
        height: Altitud en metros (puede ser negativa para océanos)
        slope: Pendiente del terreno [0.0 = plano, 1.0 = acantilado]
        temperature: Temperatura relativa [0.0 = helado, 1.0 = extremo calor]
        humidity: Humedad ambiental [0.0 = árido, 1.0 = saturado]
        water: Presencia de agua superficial [0.0 = seco, 1.0 = lago profundo]
        fertility: Fertilidad del suelo [0.0 = estéril, 1.0 = muy fértil]
        vegetation: Cobertura vegetal [0.0 = sin vegetación, 1.0 = selva densa]
        organic_matter: Materia orgánica [0.0 = sin materia, 1.0 = suelo rico]
        rockiness: Rococidad [0.0 = sin rocas, 1.0 = terreno rocoso]
        salinity: Salinidad [0.0 = dulce, 1.0 = salado como océano]
    """
    
    # Topografía
    height: float = 0.0           # Metros sobre nivel del mar
    slope: float = 0.0            # [0.0, 1.0]
    
    # Clima
    temperature: float = 0.5      # [0.0, 1.0]
    humidity: float = 0.5         # [0.0, 1.0]
    
    # Hidrología
    water: float = 0.0            # [0.0, 1.0]
    salinity: float = 0.0         # [0.0, 1.0]
    
    # Suelo y vegetación
    fertility: float = 0.5        # [0.0, 1.0]
    vegetation: float = 0.0       # [0.0, 1.0]
    organic_matter: float = 0.0   # [0.0, 1.0]
    rockiness: float = 0.0        # [0.0, 1.0]

    # Urbanización (impacto humano)
    urbanization: float = 0.0
    
    def normalize(self) -> None:
        """Asegura que todas las variables estén en [0.0, 1.0]."""
        for attr in ['slope', 'temperature', 'humidity', 'water', 'salinity',
                     'fertility', 'vegetation', 'organic_matter', 'rockiness']:
            value = getattr(self, attr)
            setattr(self, attr, max(0.0, min(1.0, value)))
    
    def to_dict(self) -> dict:
        """Serializa el tile para debugging o exportación."""
        return {
            'height': self.height,
            'slope': self.slope,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'water': self.water,
            'fertility': self.fertility,
            'vegetation': self.vegetation,
            'organic_matter': self.organic_matter,
            'rockiness': self.rockiness,
            'salinity': self.salinity,
            'urbanization': self.urbanization,
        }