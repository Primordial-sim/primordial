"""Módulo responsable de la concepción y fertilización.

Implementa un modelo de concepción biológicamente realista con:
- Verificación explícita de sexo para gestación
- Prevención de doble embarazo por pareja
- Fertilidad por producto (esterilidad real)
- Infertilidad adquirida por edad, enfermedad y trauma
- Periodo posparto refractario
- Soporte multiespecie con partenogénesis
- Integración con PendingChanges para coherencia transaccional

CORRECCIONES APLICADAS (Auditoría):
- Verificación de sexo antes de procesar embarazo
- Prevención de doble concepción en el mismo tick
- Fertilidad multiplicativa en lugar de promedio
- Infertilidad adquirida por factores fisiológicos
- Periodo refractario posparto configurable
- Llamadas exactas a register_pregnancy_update (is_pregnant, pregnancy_days, failed_increment)
"""

from __future__ import annotations

import logging
import random
from typing import Any, Optional, Dict

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext


class ConceptionSystem:
    """Motor de concepción con restricciones biológicas realistas."""

    def __init__(self, config: SimulationConfig, relationship_engine: Any = None) -> None:
        self.config = config
        self.relationship_engine = relationship_engine
        self.logger = logging.getLogger(self.__class__.__name__)

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Procesa intentos de concepción para todos los agentes elegibles."""
        repro_cfg = self.config.reproduction
        current_day = getattr(state, 'world_days_elapsed', 0.0)

        for person in state.get_all_persons():
            if person.entity_id in pending.deaths:
                continue

            # CORRECCIÓN 1: Verificación explícita de sexo para gestación
            # Solo las hembras pueden gestar (a menos que la especie sea hermafrodita)
            species_traits = self._get_species_traits(person.species)
            can_gestate = species_traits.get("can_gestate_female_only", True)
            
            if can_gestate and getattr(person, 'gender', 'M') != 'F':
                continue

            # Verificar que puede reproducirse
            if not person.can_reproduce():
                continue

            # CORRECCIÓN 6: Periodo posparto refractario
            postpartum_cooldown = getattr(repro_cfg, 'postpartum_cooldown_days', 90.0)
            if hasattr(person, 'memory') and isinstance(person.memory, dict):
                last_birth_day = person.memory.get("last_birth_day", 0.0)
                if current_day - last_birth_day < postpartum_cooldown:
                    continue

            # CORRECCIÓN 4: Infertilidad adquirida por factores fisiológicos
            acquired_fertility_modifier = self._calculate_acquired_fertility(person)
            if acquired_fertility_modifier <= 0.05:
                continue  # Efectivamente estéril por condición adquirida

            # Determinar compañero reproductivo
            partner_id = getattr(person, 'partner_id', None)
            partner = None
            
            if partner_id is not None:
                partner = state.get_person_by_id(partner_id)
                
                # CORRECCIÓN 2: Prevención de doble embarazo
                # Verificar si la pareja ya está embarazada o tiene embarazo pendiente
                if partner and getattr(partner, 'is_pregnant', False):
                    continue
                if partner and partner.entity_id in pending.pregnancy_updates:
                    continue
                # También verificar si la propia persona ya tiene embarazo pendiente
                if person.entity_id in pending.pregnancy_updates:
                    continue

            # Calcular probabilidad de concepción
            conception_chance = self._calculate_conception_chance(
                person=person,
                partner=partner,
                acquired_modifier=acquired_fertility_modifier,
                repro_cfg=repro_cfg,
            )

            if conception_chance <= 0.0:
                continue

            if random.random() < conception_chance:
                # Determinar tamaño de camada
                litter_size = self._determine_litter_size(person.species, repro_cfg)
                
                # CORRECCIÓN: Llamada exacta a register_pregnancy_update
                # Firma: (entity_id, is_pregnant, pregnancy_days, failed_increment=0, litter_size=1)
                pending.register_pregnancy_update(
                    entity_id=person.entity_id,
                    is_pregnant=True,
                    pregnancy_days=0.0,
                    failed_increment=0,
                    litter_size=litter_size,
                )
                
                # Registrar en memoria para cooldown posparto futuro
                pending.register_memory_update(
                    person.entity_id,
                    "last_conception_day",
                    current_day,
                )

    def _calculate_acquired_fertility(self, person: Any) -> float:
        """CORRECCIÓN 4: Calcula la fertilidad adquirida basada en estado fisiológico.
        
        Factores que reducen la fertilidad:
        - Edad avanzada (fuera de ventana óptima)
        - Enfermedad activa
        - Estrés extremo
        - Trauma severo
        - Baja energía (desnutrición)
        """
        modifier = 1.0
        
        # Edad: penalización fuera de la ventana fértil óptima
        repro_cfg = self.config.reproduction
        age = getattr(person, 'age', 0.0)
        optimal_start = getattr(repro_cfg, 'min_fertility_age_days', 5475.0)
        optimal_end = getattr(repro_cfg, 'max_fertility_age_days', 14600.0)
        
        if age < optimal_start:
            # Muy joven: fertilidad reducida
            modifier *= (age / max(1.0, optimal_start)) * 0.5
        elif age > optimal_end:
            # Muy mayor: fertilidad cae rápidamente
            over_age = age - optimal_end
            modifier *= max(0.05, 1.0 - (over_age / 3650.0))
        
        # Enfermedad activa
        if getattr(person, 'is_sick', False):
            modifier *= 0.4  # Enfermedad reduce fertilidad al 40%
        
        # Estrés extremo
        stress = person.emotions.get("stress", 0.0)
        if stress > 0.7:
            modifier *= 1.0 - ((stress - 0.7) / 0.3) * 0.6  # Hasta 60% de reducción
        
        # Baja energía (desnutrición)
        energy = person.emotions.get("energy", 1.0)
        if energy < 0.4:
            modifier *= energy / 0.4  # Reducción proporcional
        
        # Trauma severo
        if hasattr(person, 'memory') and isinstance(person.memory, dict):
            trauma_sickness = person.memory.get("trauma_sickness", 0.0)
            if trauma_sickness > 0.5:
                modifier *= 0.7
        
        return max(0.0, min(1.0, modifier))

    def _calculate_conception_chance(
        self,
        person: Any,
        partner: Optional[Any],
        acquired_modifier: float,
        repro_cfg: Any,
    ) -> float:
        """Calcula la probabilidad de concepción con fertilidad multiplicativa.
        
        CORRECCIÓN 3: Usa producto en lugar de promedio para que
        la esterilidad de un progenitor reduzca realmente la concepción.
        """
        # Fertilidad genética base
        mother_fertility = person.genome.fertility
        
        if partner is not None:
            # CORRECCIÓN 3: Producto de fertilidades (no promedio)
            father_fertility = partner.genome.fertility
            fertility_modifier = mother_fertility * father_fertility
        else:
            # Partenogénesis: solo fertilidad de la madre
            fertility_modifier = mother_fertility * 0.8  # Ligeramente reducida

        # Energía como factor limitante (mínimo de ambos progenitores)
        if partner is not None:
            energy_multiplier = min(
                person.emotions.get("energy", 1.0),
                partner.emotions.get("energy", 1.0)
            )
        else:
            energy_multiplier = person.emotions.get("energy", 1.0)

        # CORRECCIÓN 5: Penalización por longevidad con clamp de seguridad
        if partner is not None:
            avg_longevity = (person.genome.longevity + partner.genome.longevity) / 2.0
        else:
            avg_longevity = person.genome.longevity
        
        # Clamp: evitar división por valores cercanos a cero
        avg_longevity = max(0.3, avg_longevity)
        k_strategy_penalty = avg_longevity

        # Cálculo final
        base_chance = getattr(repro_cfg, 'base_conception_chance', 0.02)
        final_chance = (
            base_chance * 
            fertility_modifier * 
            energy_multiplier * 
            acquired_modifier
        ) / k_strategy_penalty

        return max(0.0, min(0.5, final_chance))  # Cap máximo del 50% por tick

    def _determine_litter_size(self, species: str, repro_cfg: Any) -> int:
        """Determina el tamaño de camada según la especie."""
        species_traits = self._get_species_traits(species)
        base_litter = species_traits.get("litter_size", 1)
        
        # Variación aleatoria pequeña
        variation = random.randint(-1, 1)
        litter_size = max(1, base_litter + variation)
        
        # Cap configurable
        max_litter = getattr(repro_cfg, 'max_litter_size', 8)
        return min(litter_size, max_litter)

    def _get_species_traits(self, species: str) -> Dict[str, Any]:
        """Obtiene rasgos reproductivos de la especie.
        
        CORRECCIÓN 7: Centralizado en un único punto.
        """
        # CORRECCIÓN: Usar configuración centralizada si existe
        species_config = getattr(self.config, 'species', None)
        if species_config and hasattr(species_config, species):
            return getattr(species_config, species).__dict__
        
        # Fallback: rasgos por defecto
        traits = {
            "human": {
                "gestation_days": 270.0,
                "litter_size": 1,
                "can_gestate_female_only": True,
                "fertility_window_start": 5475.0,   # ~15 años
                "fertility_window_end": 14600.0,    # ~40 años
            },
            "goblin": {
                "gestation_days": 120.0,
                "litter_size": 3,
                "can_gestate_female_only": True,
                "fertility_window_start": 2190.0,   # ~6 años
                "fertility_window_end": 7300.0,     # ~20 años
            },
            "default": {
                "gestation_days": 180.0,
                "litter_size": 2,
                "can_gestate_female_only": True,
                "fertility_window_start": 3650.0,
                "fertility_window_end": 10950.0,
            },
        }
        
        return traits.get(species, traits["default"])