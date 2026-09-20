"""Efectos de relaciones ecológicas sobre las especies.

Cada relación tiene un efecto sobre ambas especies involucradas.
Los efectos pueden ser positivos (beneficio) o negativos (perjuicio).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RelationshipEffect:
    """Efecto de una relación ecológica sobre una especie.
    
    Attributes:
        energy_change: Cambio de energía [-1.0, 1.0].
        survival_impact: Impacto en supervivencia [-1.0, 1.0].
        reproduction_impact: Impacto en reproducción [-1.0, 1.0].
        growth_impact: Impacto en crecimiento [-1.0, 1.0].
        stress_change: Cambio en estrés [0.0, 1.0].
        death_probability: Probabilidad de muerte [0.0, 1.0].
    """
    
    # Cambios positivos/negativos
    energy_change: float = 0.0          # + si gana energía, - si pierde
    survival_impact: float = 0.0        # + si mejora supervivencia, - si la reduce
    reproduction_impact: float = 0.0    # + si mejora reproducción, - si la reduce
    growth_impact: float = 0.0          # + si mejora crecimiento, - si lo reduce
    
    # Cambios negativos
    stress_change: float = 0.0          # Aumento de estrés
    death_probability: float = 0.0      # Probabilidad de muerte
    
    # Descripción
    description: str = ""
    
    def is_beneficial(self) -> bool:
        """Verifica si el efecto es netamente beneficioso."""
        positive = self.energy_change + self.survival_impact + self.reproduction_impact + self.growth_impact
        negative = self.stress_change + self.death_probability
        return positive > negative
    
    def is_harmful(self) -> bool:
        """Verifica si el efecto es netamente perjudicial."""
        return not self.is_beneficial()
    
    def __repr__(self) -> str:
        if self.death_probability > 0:
            return f"RelationshipEffect(death_prob={self.death_probability:.1%})"
        return f"RelationshipEffect(energy={self.energy_change:+.2f})"


# =============================================================================
# EFECTOS PREDEFINIDOS (para uso rápido)
# =============================================================================

def predator_success_effect(energy_gain: float = 0.6) -> RelationshipEffect:
    """Efecto sobre el depredador cuando la caza es exitosa."""
    return RelationshipEffect(
        energy_change=energy_gain,
        survival_impact=0.1,
        reproduction_impact=0.05,
        description="Depredador obtiene energía de la presa",
    )


def prey_death_effect(death_probability: float = 0.7) -> RelationshipEffect:
    """Efecto sobre la presa cuando es cazada."""
    return RelationshipEffect(
        energy_change=-0.5,
        survival_impact=-0.8,
        death_probability=death_probability,
        description="Presa es cazada por depredador",
    )


def herbivore_grazing_effect(energy_gain: float = 0.3) -> RelationshipEffect:
    """Efecto sobre el herbívoro cuando pasta."""
    return RelationshipEffect(
        energy_change=energy_gain,
        growth_impact=0.05,
        description="Herbívoro consume vegetación",
    )


def plant_consumed_effect(damage: float = 0.3) -> RelationshipEffect:
    """Efecto sobre la planta cuando es consumida."""
    return RelationshipEffect(
        energy_change=-damage,
        growth_impact=-damage * 0.5,
        description="Planta es consumida por herbívoro",
    )


def mutualism_benefit(energy_gain: float = 0.2) -> RelationshipEffect:
    """Efecto beneficioso para mutualismo."""
    return RelationshipEffect(
        energy_change=energy_gain,
        reproduction_impact=0.1,
        description="Beneficio mutuo",
    )