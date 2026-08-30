"""Modelo de huevos para reproducción ovípara.

Representa un huevo puesto por un organismo ovíparo (aves, peces,
reptiles, insectos, anfibios). Los huevos son entidades independientes
que se incuban fuera del cuerpo de la madre.

GENÉTICA UNIVERSAL: Los huevos contienen el genoma del embrión,
que puede ser resultado de reproducción sexual (combine) o asexual (replicate).

Ciclo de vida de un huevo:
1. Puesta (laid) → 2. Incubación (incubating) → 3. Eclosión (hatched) o Muerte (dead)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class EggStatus(Enum):
    """Estado de un huevo."""
    LAID = "laid"              # Recién puesto
    INCUBATING = "incubating"  # En incubación
    HATCHED = "hatched"        # Eclosionado (nacimiento)
    DEAD = "dead"              # Muerto (depredación, clima, etc.)
    ABANDONED = "abandoned"    # Abandonado por la madre


# Contador de clase para IDs únicos de huevos
_egg_id_counter = 0


def _generate_egg_id() -> int:
    """Genera el siguiente ID único para huevos."""
    global _egg_id_counter
    _egg_id_counter += 1
    return _egg_id_counter


@dataclass
class Egg:
    """Representa un huevo individual.
    
    Attributes:
        egg_id: Identificador único del huevo.
        mother_id: ID de la madre que puso el huevo.
        father_id: ID del padre (None si es partenogénesis/asexual).
        x: Posición X del huevo.
        y: Posición Y del huevo.
        genome: Genoma del embrión (combinado o clonado).
        laid_day: Día en que fue puesto el huevo.
        incubation_days: Duración total de incubación en días.
        status: Estado actual del huevo.
        current_incubation: Días de incubación transcurridos.
        mortality_risk: Riesgo de mortalidad ambiental (0.0 a 1.0).
        clutch_id: ID de la nidada (huevos puestos juntos).
    """
    
    # Identificación
    egg_id: int = 0
    mother_id: int = 0
    father_id: Optional[int] = None
    
    # Posición
    x: float = 0.0
    y: float = 0.0
    
    # Genética
    genome: Any = None
    
    # Temporal
    laid_day: float = 0.0
    incubation_days: float = 30.0
    current_incubation: float = 0.0
    
    # Estado
    status: EggStatus = EggStatus.LAID
    
    # Riesgo
    mortality_risk: float = 0.001  # Riesgo diario base
    
    # Agrupación
    clutch_id: Optional[int] = None
    
    def __post_init__(self):
        """Asigna ID único si no se proporcionó."""
        if self.egg_id == 0:
            self.egg_id = _generate_egg_id()
    
    @property
    def is_incubating(self) -> bool:
        """Verifica si el huevo está en incubación."""
        return self.status == EggStatus.INCUBATING
    
    @property
    def is_alive(self) -> bool:
        """Verifica si el huevo está vivo."""
        return self.status in (EggStatus.LAID, EggStatus.INCUBATING)
    
    @property
    def progress(self) -> float:
        """Progreso de incubación (0.0 a 1.0)."""
        if self.incubation_days <= 0:
            return 1.0
        return min(1.0, self.current_incubation / self.incubation_days)
    
    @property
    def days_until_hatch(self) -> float:
        """Días restantes hasta la eclosión."""
        return max(0.0, self.incubation_days - self.current_incubation)
    
    def start_incubation(self) -> None:
        """Inicia la incubación del huevo."""
        if self.status == EggStatus.LAID:
            self.status = EggStatus.INCUBATING
    
    def advance_incubation(self, delta_days: float) -> None:
        """Avanza la incubación del huevo."""
        if self.status == EggStatus.INCUBATING:
            self.current_incubation += delta_days
    
    def hatch(self) -> None:
        """Marca el huevo como eclosionado."""
        self.status = EggStatus.HATCHED
    
    def die(self) -> None:
        """Marca el huevo como muerto."""
        self.status = EggStatus.DEAD
    
    def abandon(self) -> None:
        """Marca el huevo como abandonado."""
        self.status = EggStatus.ABANDONED
    
    def should_hatch(self) -> bool:
        """Verifica si el huevo debe eclosionar."""
        return self.is_incubating and self.current_incubation >= self.incubation_days
    
    def to_dict(self) -> dict:
        """Serializa el huevo para debugging o guardado."""
        return {
            "egg_id": self.egg_id,
            "mother_id": self.mother_id,
            "father_id": self.father_id,
            "x": self.x,
            "y": self.y,
            "laid_day": self.laid_day,
            "incubation_days": self.incubation_days,
            "current_incubation": self.current_incubation,
            "status": self.status.value,
            "progress": self.progress,
            "clutch_id": self.clutch_id,
        }
    
    def __str__(self) -> str:
        return (
            f"Egg(id={self.egg_id}, mother={self.mother_id}, "
            f"status={self.status.value}, progress={self.progress:.1%})"
        )
    
    def __repr__(self) -> str:
        return (
            f"Egg(egg_id={self.egg_id}, mother_id={self.mother_id}, "
            f"father_id={self.father_id}, x={self.x}, y={self.y}, "
            f"laid_day={self.laid_day}, incubation_days={self.incubation_days}, "
            f"current_incubation={self.current_incubation}, "
            f"status={self.status}, clutch_id={self.clutch_id})"
        )