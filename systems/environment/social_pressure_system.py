"""Sistema de presión social (BLOQUE 4).

Modifica la presión local del entorno basada en eventos sociales del tick anterior.
Esto crea un "campo de presión social" que afecta el movimiento y la migración.

Eventos que aumentan la presión social:
- Adopciones (nueva familia en una zona)
- Matrimonios (unión de agentes)
- Muertes (trauma en la comunidad)

Eventos que disminuyen la presión social:
- Migraciones (agentes que se van)
- Divorcios (ruptura familiar)

Este sistema se ejecuta en la fase 'environment' y modifica el pressure_map
para que otros sistemas (MovementSystem, MigrationSystem) lo consideren.
"""

import logging
from typing import Any

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext


class SocialPressureSystem:
    """Aplica feedback de eventos sociales al mapa de presión del entorno."""

    def __init__(self, config: SimulationConfig) -> None:
        """Inicializa el sistema de presión social."""
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Radio de influencia de los eventos sociales (en celdas)
        self.social_influence_radius = 15.0
        
        # Intensidad de la presión social por evento
        self.adoption_pressure = 0.3  # Adopción aumenta presión (nueva familia)
        self.marriage_pressure = 0.2  # Matrimonio aumenta presión (unión)
        self.death_pressure = 0.4     # Muerte aumenta presión (trauma)
        self.migration_relief = -0.2  # Migración disminuye presión (alivio)
        self.divorce_relief = -0.1    # Divorcio disminuye presión (ruptura)

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Aplica eventos sociales del tick actual al mapa de presión.
        
        Este sistema lee los eventos sociales de pending y modifica
        context.pressure_map para que otros sistemas lo consideren.
        """
        # Solo procesar si hay eventos sociales
        if not self._has_social_events(pending):
            return

        # Aplicar presión por adopciones
        for adoption in getattr(pending, 'adoptions', []):
            child_id = adoption.get('child_id')
            parent_a_id = adoption.get('parent_a')
            
            if parent_a_id is not None:
                parent = state.get_person_by_id(parent_a_id)
                if parent:
                    self._apply_social_pressure(
                        context, parent.x, parent.y, 
                        self.adoption_pressure, delta_days
                    )

        # Aplicar presión por matrimonios
        for marriage in getattr(pending, 'marriages', {}).items():
            person_a_id, person_b_id = marriage
            person_a = state.get_person_by_id(person_a_id)
            if person_a:
                self._apply_social_pressure(
                    context, person_a.x, person_a.y,
                    self.marriage_pressure, delta_days
                )

        # Aplicar presión por muertes (trauma en la comunidad)
        for death_id in pending.deaths:
            deceased = state.get_person_by_id(death_id)
            if deceased:
                self._apply_social_pressure(
                    context, deceased.x, deceased.y,
                    self.death_pressure, delta_days
                )

        # Aplicar alivio por migraciones (agentes que se van)
        # Nota: Las migraciones activas están en pending.migration_targets
        for entity_id, target in getattr(pending, 'migration_targets', {}).items():
            person = state.get_person_by_id(entity_id)
            if person:
                # El alivio se aplica en la posición actual (de donde se van)
                self._apply_social_pressure(
                    context, person.x, person.y,
                    self.migration_relief, delta_days
                )

        # Aplicar alivio por divorcios
        for divorce in getattr(pending, 'divorces', []):
            person_a_id, person_b_id = divorce
            person_a = state.get_person_by_id(person_a_id)
            if person_a:
                self._apply_social_pressure(
                    context, person_a.x, person_a.y,
                    self.divorce_relief, delta_days
                )

    def _has_social_events(self, pending: PendingChanges) -> bool:
        """Verifica si hay eventos sociales en el búfer."""
        return (
            len(getattr(pending, 'adoptions', [])) > 0 or
            len(getattr(pending, 'marriages', {})) > 0 or
            len(pending.deaths) > 0 or
            len(getattr(pending, 'migration_targets', {})) > 0 or
            len(getattr(pending, 'divorces', [])) > 0
        )

    def _apply_social_pressure(
        self,
        context: EnvironmentContext,
        x: float,
        y: float,
        intensity: float,
        delta_days: float,
    ) -> None:
        """Aplica presión social en un radio alrededor de una coordenada.
        
        Args:
            context: Contexto ambiental con pressure_map.
            x: Coordenada X del evento.
            y: Coordenada Y del evento.
            intensity: Intensidad de la presión (positiva o negativa).
            delta_days: Duración del tick en días.
        """
        # Aplicar presión en un radio alrededor del evento
        radius = int(self.social_influence_radius)
        
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                # Calcular distancia al evento
                dist = (dx * dx + dy * dy) ** 0.5
                
                # Solo aplicar dentro del radio y con decaimiento por distancia
                if dist <= self.social_influence_radius:
                    # Decaimiento lineal: máxima presión en el centro, cero en el borde
                    decay_factor = 1.0 - (dist / self.social_influence_radius)
                    
                    # Aplicar presión escalada por delta_days
                    pressure_delta = intensity * decay_factor * delta_days
                    
                    # Modificar pressure_map
                    coord = (int(x) + dx, int(y) + dy)
                    current_pressure = context.pressure_map.get(coord, 1.0)
                    
                    # Asegurar que la presión no baje de 0.5 (mínimo biológico)
                    new_pressure = max(0.5, current_pressure + pressure_delta)
                    context.pressure_map[coord] = new_pressure