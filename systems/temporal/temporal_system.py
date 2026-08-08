"""Módulo responsable del avance temporal y el metabolismo basal.

Gestiona el reloj global de la simulación y los costes energéticos
fisiológicos de cada individuo. Introduce trade-offs evolutivos reales:
- Alta inmunidad → mayor supervivencia pero mayor coste energético
- Alto temperamento → mayor actividad pero mayor consumo metabólico
- Enfermedad → aumenta consumo Y reduce recuperación
- Edad avanzada → reduce recuperación energética

CORRECCIONES APLICADAS (Auditoría):
- Coste inmunológico escalado por virulencia del patógeno activo
- Recuperación energética dependiente de recursos, edad y enfermedad
- Enfermedad aumenta consumo y reduce recuperación simultáneamente
- Coste por temperamento documentado (hiperactividad metabólica)
- Hitos biológicos con efectos emocionales reales
- Uso de pending.register_time_pass() para coherencia transaccional
"""

from __future__ import annotations

import logging
from typing import Any

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext


class TemporalSystem:
    """Avanza el reloj global y aplica el metabolismo basal a todos los agentes."""

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
        """Procesa el avance temporal y el metabolismo basal de todos los agentes."""
        time_cfg = self.config.time
        
        # CORRECCIÓN: Usar pending para el reloj global (coherencia transaccional)
        pending.register_time_pass(delta_days)
        
        # CORRECCIÓN: Valores de configuración con fallback seguro
        immune_cost_per_point = getattr(time_cfg, 'immune_energy_cost', 0.01)
        temperament_cost_per_point = getattr(time_cfg, 'temperament_energy_cost', 0.005)
        base_recovery_rate = getattr(time_cfg, 'base_energy_recovery', 0.3)
        
        for person in state.get_all_persons():
            if person.entity_id in pending.deaths:
                continue

            # =================================================================
            # CÁLCULO DE COSTES ENERGÉTICOS
            # =================================================================
            
            # 1. COSTE INMUNOLÓGICO (trade-off evolutivo)
            immunity = person.genome.immunity
            immune_cost = immunity * immune_cost_per_point
            
            # CORRECCIÓN: El coste inmunológico se dispara cuando hay infección activa
            if getattr(person, 'is_sick', False):
                total_virulence = 0.0
                if hasattr(person, 'active_pathogens') and person.active_pathogens:
                    for pathogen in person.active_pathogens.values():
                        total_virulence += pathogen.virulence
                
                sickness_multiplier = min(5.0, 2.0 + total_virulence)
                immune_cost *= sickness_multiplier

            # 2. COSTE POR TEMPERAMENTO (hiperactividad metabólica)
            temperament = person.genome.temperament
            temperament_cost = temperament * temperament_cost_per_point

            # 3. COSTE POR EDAD (metabolismo basal variable)
            age = getattr(person, 'age', 0.0)
            age_factor = 1.0
            if age > time_cfg.senior_age_days:
                age_factor = 1.2
            elif age < time_cfg.adult_age_days:
                age_factor = 1.3

            # 4. COSTE TOTAL DE CONSUMO
            total_consumption = (immune_cost + temperament_cost) * age_factor * delta_days
            
            # La enfermedad aumenta el consumo energético adicional
            if getattr(person, 'is_sick', False):
                sickness_consumption = 0.05 * delta_days
                total_consumption += sickness_consumption

            # =================================================================
            # CÁLCULO DE RECUPERACIÓN ENERGÉTICA
            # =================================================================
            
            # Factor de recursos del entorno
            local_resources = getattr(context, 'get_resources_at', lambda x, y: 0.5)(
                int(person.x), int(person.y)
            )
            resource_factor = 0.5 + (local_resources * 0.5)
            
            # Factor de edad
            recovery_age_factor = 1.0
            if age > time_cfg.senior_age_days:
                recovery_age_factor = 0.7
            elif age < time_cfg.adult_age_days:
                recovery_age_factor = 1.1
            
            # La enfermedad reduce la recuperación
            sickness_recovery_factor = 1.0
            if getattr(person, 'is_sick', False):
                sickness_recovery_factor = 0.5
            
            # Recuperación final
            total_recovery = (
                base_recovery_rate * 
                resource_factor * 
                recovery_age_factor * 
                sickness_recovery_factor * 
                delta_days
            )
            
            net_energy_change = total_recovery - total_consumption

            # Aplicar cambio de energía
            if abs(net_energy_change) > 0.001:
                pending.register_emotion_update(person.entity_id, "energy", net_energy_change)

            # =================================================================
            # HITOS BIOLÓGICOS CON EFECTOS REALES
            # =================================================================
            self._check_milestones(person, pending, time_cfg)

    def _check_milestones(self, person: Any, pending: PendingChanges, time_cfg: Any) -> None:
        """Verifica hitos biológicos y aplica efectos emocionales.
        
        CORRECCIÓN: Los hitos ahora generan efectos reales, no solo logs.
        """
        age = getattr(person, 'age', 0.0)
        
        # Transición a adulto
        if not getattr(person, 'is_adult', False) and age >= time_cfg.adult_age_days:
            # La madurez genera un pequeño boost de felicidad y reduce estrés
            pending.register_emotion_update(person.entity_id, "happiness", 0.1)
            pending.register_emotion_update(person.entity_id, "stress", -0.05)
            self.logger.debug(
                "🎂 Agente %s alcanzó la madurez (edad: %.0f días)",
                person.entity_id, age,
            )
        
        # Transición a anciano
        if not getattr(person, 'is_senior', False) and age >= time_cfg.senior_age_days:
            # La senectud aumenta estrés y reduce felicidad ligeramente
            pending.register_emotion_update(person.entity_id, "stress", 0.1)
            pending.register_emotion_update(person.entity_id, "happiness", -0.05)
            self.logger.debug(
                "👴 Agente %s entró en senectud (edad: %.0f días)",
                person.entity_id, age,
            )