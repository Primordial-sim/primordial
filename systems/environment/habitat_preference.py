"""Preferencias ecológicas de una especie.

Cada especie define las condiciones ambientales que necesita para prosperar.
NO define biomas directamente; solo define rangos de variables ambientales.

Ejemplo:
- Humano: temperatura 15-30°C, agua alta, pendiente baja
- Pez: agua muy alta, profundidad alta, salinidad media
- Pino: temperatura baja, altitud alta, suelo pobre

La compatibilidad con un tile se calcula comparando estas preferencias
con las variables reales del tile.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HabitatPreference:
    """Define las preferencias ambientales de una especie.
    
    Cada preferencia tiene un valor ideal [0.0, 1.0] y una tolerancia [0.0, 1.0].
    La tolerancia indica cuánto puede desviarse el ambiente del ideal.
    
    Attributes:
        temperature_ideal: Temperatura ideal [0.0 = frío, 1.0 = calor]
        temperature_tolerance: Tolerancia de temperatura [0.0 = estricto, 1.0 = flexible]
        humidity_ideal: Humedad ideal [0.0 = árido, 1.0 = saturado]
        humidity_tolerance: Tolerancia de humedad
        water_ideal: Nivel de agua ideal [0.0 = seco, 1.0 = acuático]
        water_tolerance: Tolerancia al agua
        vegetation_ideal: Vegetación ideal [0.0 = sin vegetación, 1.0 = selva]
        vegetation_tolerance: Tolerancia de vegetación
        altitude_ideal: Altitud ideal [0.0 = nivel del mar, 1.0 = montaña]
        altitude_tolerance: Tolerancia de altitud
        slope_ideal: Pendiente ideal [0.0 = plano, 1.0 = acantilado]
        slope_tolerance: Tolerancia de pendiente
        fertility_ideal: Fertilidad ideal [0.0 = estéril, 1.0 = fértil]
        fertility_tolerance: Tolerancia de fertilidad
        salinity_ideal: Salinidad ideal [0.0 = dulce, 1.0 = salado]
        salinity_tolerance: Tolerancia de salinidad
    """
    
    # Temperatura
    temperature_ideal: float = 0.5
    temperature_tolerance: float = 0.3
    
    # Humedad
    humidity_ideal: float = 0.5
    humidity_tolerance: float = 0.3
    
    # Agua
    water_ideal: float = 0.2
    water_tolerance: float = 0.3
    
    # Vegetación
    vegetation_ideal: float = 0.4
    vegetation_tolerance: float = 0.3
    
    # Altitud
    altitude_ideal: float = 0.2
    altitude_tolerance: float = 0.4
    
    # Pendiente
    slope_ideal: float = 0.2
    slope_tolerance: float = 0.3
    
    # Fertilidad
    fertility_ideal: float = 0.5
    fertility_tolerance: float = 0.3
    
    # Salinidad
    salinity_ideal: float = 0.1
    salinity_tolerance: float = 0.3
    
    # Rococidad
    rockiness_ideal: float = 0.2
    rockiness_tolerance: float = 0.4
    
    def to_dict(self) -> dict:
        """Serializa las preferencias para debugging."""
        return {
            'temperature': (self.temperature_ideal, self.temperature_tolerance),
            'humidity': (self.humidity_ideal, self.humidity_tolerance),
            'water': (self.water_ideal, self.water_tolerance),
            'vegetation': (self.vegetation_ideal, self.vegetation_tolerance),
            'altitude': (self.altitude_ideal, self.altitude_tolerance),
            'slope': (self.slope_ideal, self.slope_tolerance),
            'fertility': (self.fertility_ideal, self.fertility_tolerance),
            'salinity': (self.salinity_ideal, self.salinity_tolerance),
            'rockiness': (self.rockiness_ideal, self.rockiness_tolerance),
        }


# =============================================================================
# PRESETS DE PREFERENCIAS PARA ESPECIES COMUNES
# =============================================================================

def create_human_habitat() -> HabitatPreference:
    """Humanos: prefieren llanuras templadas con acceso a agua."""
    return HabitatPreference(
        temperature_ideal=0.5,
        temperature_tolerance=0.25,
        humidity_ideal=0.5,
        humidity_tolerance=0.25,
        water_ideal=0.3,
        water_tolerance=0.3,
        vegetation_ideal=0.5,
        vegetation_tolerance=0.3,
        altitude_ideal=0.15,
        altitude_tolerance=0.25,
        slope_ideal=0.1,
        slope_tolerance=0.2,
        fertility_ideal=0.7,
        fertility_tolerance=0.3,
        salinity_ideal=0.05,
        salinity_tolerance=0.1,
    )


def create_fish_habitat() -> HabitatPreference:
    """Peces: necesitan agua abundante (alta profundidad)."""
    return HabitatPreference(
        temperature_ideal=0.5,
        temperature_tolerance=0.3,
        humidity_ideal=0.8,
        humidity_tolerance=0.3,
        water_ideal=0.9,
        water_tolerance=0.15,
        vegetation_ideal=0.2,
        vegetation_tolerance=0.4,
        altitude_ideal=0.1,
        altitude_tolerance=0.2,
        slope_ideal=0.0,
        slope_tolerance=0.5,
        fertility_ideal=0.4,
        fertility_tolerance=0.4,
        salinity_ideal=0.5,
        salinity_tolerance=0.5,  # Alta tolerancia: agua dulce o salada
    )


def create_bird_habitat() -> HabitatPreference:
    """Aves: prefieren áreas abiertas con vegetación moderada."""
    return HabitatPreference(
        temperature_ideal=0.5,
        temperature_tolerance=0.35,
        humidity_ideal=0.4,
        humidity_tolerance=0.35,
        water_ideal=0.2,
        water_tolerance=0.4,
        vegetation_ideal=0.4,
        vegetation_tolerance=0.35,
        altitude_ideal=0.3,
        altitude_tolerance=0.4,
        slope_ideal=0.15,
        slope_tolerance=0.25,
        fertility_ideal=0.5,
        fertility_tolerance=0.35,
        salinity_ideal=0.1,
        salinity_tolerance=0.2,
    )


def create_goat_habitat() -> HabitatPreference:
    """Cabras: prefieren terrenos montañosos con vegetación escasa."""
    return HabitatPreference(
        temperature_ideal=0.45,
        temperature_tolerance=0.3,
        humidity_ideal=0.3,
        humidity_tolerance=0.3,
        water_ideal=0.15,
        water_tolerance=0.25,
        vegetation_ideal=0.25,
        vegetation_tolerance=0.3,
        altitude_ideal=0.6,
        altitude_tolerance=0.3,
        slope_ideal=0.5,
        slope_tolerance=0.3,
        fertility_ideal=0.3,
        fertility_tolerance=0.35,
        salinity_ideal=0.05,
        salinity_tolerance=0.15,
        rockiness_ideal=0.6,
        rockiness_tolerance=0.3,
    )


def create_pine_habitat() -> HabitatPreference:
    """Pinos: prefieren climas fríos y suelos pobres."""
    return HabitatPreference(
        temperature_ideal=0.3,
        temperature_tolerance=0.25,
        humidity_ideal=0.45,
        humidity_tolerance=0.3,
        water_ideal=0.25,
        water_tolerance=0.25,
        vegetation_ideal=0.5,
        vegetation_tolerance=0.3,
        altitude_ideal=0.5,
        altitude_tolerance=0.35,
        slope_ideal=0.2,
        slope_tolerance=0.35,
        fertility_ideal=0.3,
        fertility_tolerance=0.4,
        salinity_ideal=0.0,
        salinity_tolerance=0.1,
    )


def create_desert_plant_habitat() -> HabitatPreference:
    """Plantas desérticas: calor extremo, poca agua."""
    return HabitatPreference(
        temperature_ideal=0.85,
        temperature_tolerance=0.2,
        humidity_ideal=0.1,
        humidity_tolerance=0.15,
        water_ideal=0.05,
        water_tolerance=0.15,
        vegetation_ideal=0.1,
        vegetation_tolerance=0.3,
        altitude_ideal=0.2,
        altitude_tolerance=0.3,
        slope_ideal=0.1,
        slope_tolerance=0.3,
        fertility_ideal=0.2,
        fertility_tolerance=0.4,
        salinity_ideal=0.1,
        salinity_tolerance=0.3,
    )


def create_aquatic_plant_habitat() -> HabitatPreference:
    """Plantas acuáticas: mucha agua, poca pendiente."""
    return HabitatPreference(
        temperature_ideal=0.5,
        temperature_tolerance=0.3,
        humidity_ideal=0.9,
        humidity_tolerance=0.15,
        water_ideal=0.85,
        water_tolerance=0.2,
        vegetation_ideal=0.3,
        vegetation_tolerance=0.4,
        altitude_ideal=0.1,
        altitude_tolerance=0.2,
        slope_ideal=0.0,
        slope_tolerance=0.15,
        fertility_ideal=0.6,
        fertility_tolerance=0.3,
        salinity_ideal=0.2,
        salinity_tolerance=0.5,
    )


def create_fungus_habitat() -> HabitatPreference:
    """Hongos: prefieren humedad alta y materia orgánica."""
    return HabitatPreference(
        temperature_ideal=0.4,
        temperature_tolerance=0.35,
        humidity_ideal=0.7,
        humidity_tolerance=0.25,
        water_ideal=0.3,
        water_tolerance=0.3,
        vegetation_ideal=0.5,
        vegetation_tolerance=0.3,
        altitude_ideal=0.2,
        altitude_tolerance=0.4,
        slope_ideal=0.1,
        slope_tolerance=0.4,
        fertility_ideal=0.7,
        fertility_tolerance=0.3,
        salinity_ideal=0.05,
        salinity_tolerance=0.1,
    )


def create_bacteria_habitat() -> HabitatPreference:
    """Bacterias: muy tolerantes, sobreviven en casi cualquier lugar."""
    return HabitatPreference(
        temperature_ideal=0.5,
        temperature_tolerance=0.6,  # Muy tolerante
        humidity_ideal=0.5,
        humidity_tolerance=0.6,
        water_ideal=0.4,
        water_tolerance=0.5,
        vegetation_ideal=0.3,
        vegetation_tolerance=0.6,
        altitude_ideal=0.2,
        altitude_tolerance=0.6,
        slope_ideal=0.1,
        slope_tolerance=0.6,
        fertility_ideal=0.5,
        fertility_tolerance=0.6,
        salinity_ideal=0.3,
        salinity_tolerance=0.6,
    )


# =============================================================================
# REGISTRO DE PRESETS
# =============================================================================

HABITAT_PRESETS = {
    'human': create_human_habitat,
    'fish': create_fish_habitat,
    'bird': create_bird_habitat,
    'goat': create_goat_habitat,
    'pine': create_pine_habitat,
    'desert_plant': create_desert_plant_habitat,
    'aquatic_plant': create_aquatic_plant_habitat,
    'fungus': create_fungus_habitat,
    'bacteria': create_bacteria_habitat,
}