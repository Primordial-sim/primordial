"""Modelos de datos para eventos catastróficos.

Cada catástrofe es un evento puntual que altera drásticamente el entorno
en una zona específica. Las catástrofes son la fuerza principal de cambio
geológico y ecológico a gran escala.

Principio: "Las catástrofes no son errores del sistema, son el motor
de la transformación del mundo."
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class CatastropheType(Enum):
    """Tipos de catástrofes disponibles."""
    EARTHQUAKE = auto()        # Terremoto
    VOLCANIC_ERUPTION = auto() # Erupción volcánica
    FLOOD = auto()             # Inundación
    METEORITE = auto()         # Impacto de meteorito
    FIRE = auto()              # Incendio
    DROUGHT = auto()           # Sequía
    STORM = auto()             # Tormenta / huracán
    LANDSLIDE = auto()         # Deslizamiento de tierra


class CatastropheSeverity(Enum):
    """Niveles de severidad de una catástrofe."""
    MINOR = "minor"          # Menor: efectos locales
    MODERATE = "moderate"    # Moderada: efectos regionales
    MAJOR = "major"          # Mayor: efectos extensos
    CATASTROPHIC = "catastrophic"  # Catastrófica: efectos masivos


@dataclass
class CatastropheEvent:
    """Representa un evento catastrófico ocurrido en el mundo.
    
    Attributes:
        event_id: Identificador único del evento.
        catastrophe_type: Tipo de catástrofe.
        severity: Nivel de severidad.
        epicenter_x: Coordenada X del epicentro.
        epicenter_y: Coordenada Y del epicentro.
        radius: Radio de efecto en tiles.
        intensity: Intensidad del evento [0.0, 1.0].
        occurred_day: Día simulado en que ocurrió.
        tiles_affected: Número de tiles afectados.
        description: Descripción legible del evento.
    """
    
    event_id: int
    catastrophe_type: CatastropheType
    severity: CatastropheSeverity
    epicenter_x: int
    epicenter_y: int
    radius: int
    intensity: float
    occurred_day: float
    tiles_affected: int = 0
    description: str = ""
    
    def to_dict(self) -> dict:
        """Serializa el evento para logging o exportación."""
        return {
            "event_id": self.event_id,
            "type": self.catastrophe_type.name,
            "severity": self.severity.value,
            "epicenter": (self.epicenter_x, self.epicenter_y),
            "radius": self.radius,
            "intensity": self.intensity,
            "occurred_day": self.occurred_day,
            "tiles_affected": self.tiles_affected,
            "description": self.description,
        }
    
    def __str__(self) -> str:
        return (
            f"[{self.severity.value.upper()}] {self.catastrophe_type.name} "
            f"en ({self.epicenter_x}, {self.epicenter_y}) "
            f"radio={self.radius}, intensidad={self.intensity:.2f}, "
            f"tiles={self.tiles_affected}"
        )


# Contador global para IDs únicos de eventos
_catastrophe_id_counter = 0


def generate_catastrophe_id() -> int:
    """Genera el siguiente ID único para catástrofes."""
    global _catastrophe_id_counter
    _catastrophe_id_counter += 1
    return _catastrophe_id_counter


def severity_from_intensity(intensity: float) -> CatastropheSeverity:
    """Determina la severidad a partir de la intensidad.
    
    Args:
        intensity: Intensidad [0.0, 1.0].
        
    Returns:
        Nivel de severidad correspondiente.
    """
    if intensity >= 0.85:
        return CatastropheSeverity.CATASTROPHIC
    elif intensity >= 0.6:
        return CatastropheSeverity.MAJOR
    elif intensity >= 0.35:
        return CatastropheSeverity.MODERATE
    else:
        return CatastropheSeverity.MINOR