"""Módulo responsable de la progresión temporal y desgaste biológico multifactorial.

Implementa un modelo de envejecimiento que considera múltiples factores:
- Desgaste reproductivo (SOLO hijos biológicos, con límite de saturación)
- Carga del embarazo (solo para la madre, configurable)
- Estrés crónico y enfermedades (aceleran el envejecimiento celular)
- Baja energía (desnutrición, pobreza)
- Factor genético (longevidad heredada)
"""

from __future__ import annotations

import logging

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext


class AgingSystem:
    """Calcula el envejecimiento biológico basado en múltiples factores de desgaste."""

    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Aplica el desgaste biológico multifactorial a todas las entidades activas."""
        aging_cfg = self.config.aging
        
        for person in state.get_all_persons():
            if person.entity_id in pending.deaths:
                continue
            
            # =================================================================
            # CÁLCULO DE FACTORES DE DESGASTE
            # =================================================================
            
            # 1. DESGASTE REPRODUCTIVO (Solo hijos biológicos, CON LÍMITE DE SATURACIÓN)
            # CORRECCIÓN: Usar biological_children_count para que las adopciones no envejezcan
            biological_children = getattr(person, 'biological_children_count', 0)
            is_female = getattr(person, 'gender', 'M') == 'F'
            
            # Límite de saturación: el desgaste no crece indefinidamente
            max_children_for_wear = getattr(aging_cfg, 'max_children_for_aging', 10)
            effective_children = min(biological_children, max_children_for_wear)
            
            if is_female:
                # Madre: desgaste completo
                base_wear = effective_children * aging_cfg.reproductive_wear_per_child
                reproductive_wear = 1.0 + min(base_wear, aging_cfg.max_reproductive_wear_multiplier - 1.0)
            else:
                # Padre: desgaste reducido (ej. 30% del de la madre, configurable)
                father_ratio = getattr(aging_cfg, 'father_reproductive_wear_ratio', 0.3)
                base_wear = effective_children * aging_cfg.reproductive_wear_per_child * father_ratio
                reproductive_wear = 1.0 + min(base_wear, (aging_cfg.max_reproductive_wear_multiplier - 1.0) * father_ratio)
            
            # 2. CARGA DEL EMBARAZO (Solo para la madre)
            # CORRECCIÓN: Leer de configuración en lugar de hardcodear
            pregnancy_burden = getattr(aging_cfg, 'pregnancy_burden_multiplier', 1.2) if person.is_pregnant else 1.0
            
            # 3. DESGASTE POR ESTRÉS CRÓNICO
            stress_level = person.emotions.get("stress", 0.0)
            stress_aging = 1.0 + (stress_level * aging_cfg.stress_aging_factor)
            
            # 4. DESGASTE POR ENFERMEDAD
            sickness_aging = 1.0 + (aging_cfg.sickness_aging_factor if person.is_sick else 0.0)
            
            # 5. DESGASTE POR BAJA ENERGÍA Y ESTADOS EXTREMOS (NUEVO)
            energy_level = person.emotions.get("energy", 1.0)
            low_energy_aging = 1.0 + ((1.0 - energy_level) * aging_cfg.low_energy_aging_factor)
            
            # Penalización adicional por estados fisiológicos extremos combinados
            extreme_state_penalty = 1.0
            if person.is_sick and energy_level < 0.3:
                extreme_state_penalty = 1.15  # 15% más de envejecimiento por enfermedad grave + agotamiento
            elif energy_level < 0.2:
                extreme_state_penalty = 1.10  # 10% por agotamiento extremo (inanición)
            
            # 6. FACTOR GENÉTICO (Longevidad)
            # GENÉTICA UNIVERSAL: API genérica agnóstica a especie
            genetic_longevity = person.genome.get_trait_value("longevity")
            genetic_factor = aging_cfg.longevity_genetic_factor / max(0.1, genetic_longevity)
            
            # =================================================================
            # CÁLCULO FINAL DEL ENVEJECIMIENTO
            # =================================================================
            total_aging_multiplier = (
                reproductive_wear *
                pregnancy_burden *
                stress_aging *
                sickness_aging *
                low_energy_aging *
                extreme_state_penalty *
                genetic_factor
            )
            
            biological_increment = delta_days * total_aging_multiplier
            
            pending.register_age_increment(person.entity_id, biological_increment)
            
            # Logging detallado para debugging (solo si el envejecimiento es significativo)
            if total_aging_multiplier > 1.5 or total_aging_multiplier < 0.7:
                self.logger.debug(
                    "Envejecimiento %s: %.2f días (multiplicador: %.2f) "
                    "[repro: %.2f, preg: %.2f, stress: %.2f, sick: %.2f, energy: %.2f, ext: %.2f, gen: %.2f]",
                    person.entity_id,
                    biological_increment,
                    total_aging_multiplier,
                    reproductive_wear,
                    pregnancy_burden,
                    stress_aging,
                    sickness_aging,
                    low_energy_aging,
                    extreme_state_penalty,
                    genetic_factor,
                )