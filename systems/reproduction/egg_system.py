"""Sistema de procesamiento de huevos ovíparos.

Procesa la incubación, mortalidad ambiental y eclosión de huevos
puestos por organismos ovíparos (aves, peces, reptiles, insectos).

GENÉTICA UNIVERSAL: Este sistema solo procesa huevos; la decisión de
poner huevos vs gestar internamente se toma en ConceptionSystem
basándose en ReproductiveCapabilities.

Flujo:
1. ConceptionSystem registra huevos nuevos en pending.new_eggs
2. EggSystem los recoge y los añade a state.active_eggs
3. Cada tick: avanza incubación, verifica mortalidad, eclosiona
4. Al eclosionar: register_birth y elimina el huevo
"""

from __future__ import annotations

import logging
import random
from typing import List

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext
from systems.reproduction.egg_model import Egg, EggStatus
from systems.behavior.cognitive_capabilities import CognitiveCapabilities


class EggSystem:
    """Sistema de procesamiento de huevos ovíparos."""

    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._clutch_counter = 0

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Procesa todos los huevos activos.
        
        1. Recoge huevos nuevos de pending
        2. Avanza incubación
        3. Verifica mortalidad ambiental
        4. Eclosiona huevos maduros
        """
        current_day = getattr(state, 'world_days_elapsed', 0.0)
        
        # 1. Recoger huevos nuevos del buffer de pending
        self._collect_new_eggs(state, pending, current_day)
        
        # 2. Procesar huevos activos
        active_eggs = self._get_active_eggs(state)
        eggs_to_remove = []
        
        for egg in active_eggs:
            if not egg.is_alive:
                eggs_to_remove.append(egg)
                continue
            
            # Iniciar incubación si está recién puesto
            if egg.status == EggStatus.LAID:
                egg.start_incubation()
            
            # Avanzar incubación
            egg.advance_incubation(delta_days)
            
            # Verificar mortalidad ambiental
            if self._check_environmental_mortality(egg, context, delta_days):
                egg.die()
                eggs_to_remove.append(egg)
                self.logger.debug(
                    "🥚 Huevo %d murió por causas ambientales (madre: %d)",
                    egg.egg_id, egg.mother_id,
                )
                continue
            
            # Verificar eclosión
            if egg.should_hatch():
                self._execute_hatch(egg, state, pending, current_day)
                egg.hatch()
                eggs_to_remove.append(egg)
                self.logger.debug(
                    "🐣 Huevo %d eclosionó (madre: %d)",
                    egg.egg_id, egg.mother_id,
                )
        
        # 3. Eliminar huevos procesados (eclosionados o muertos)
        self._remove_eggs(state, eggs_to_remove)

    def _collect_new_eggs(
        self,
        state: WorldState,
        pending: PendingChanges,
        current_day: float,
    ) -> None:
        """Recoge huevos nuevos del buffer de pending y los añade al estado."""
        new_eggs = getattr(pending, 'new_eggs', [])
        
        if not new_eggs:
            return
        
        # Asegurar que state tiene la lista de huevos activos
        if not hasattr(state, 'active_eggs'):
            state.active_eggs = []
        
        for egg_data in new_eggs:
            if isinstance(egg_data, Egg):
                egg = egg_data
            else:
                # Si viene como dict, crear Egg
                egg = Egg(
                    egg_id=egg_data.get('egg_id', 0),
                    mother_id=egg_data.get('mother_id', 0),
                    father_id=egg_data.get('father_id', None),
                    x=egg_data.get('x', 0.0),
                    y=egg_data.get('y', 0.0),
                    genome=egg_data.get('genome', None),
                    laid_day=current_day,
                    incubation_days=egg_data.get('incubation_days', 30.0),
                    clutch_id=egg_data.get('clutch_id', None),
                )
            
            state.active_eggs.append(egg)
        
        # Limpiar el buffer
        pending.new_eggs = []
        
        self.logger.debug(
            "🥚 Se recogieron %d huevos nuevos (total activos: %d)",
            len(new_eggs), len(state.active_eggs),
        )

    def _get_active_eggs(self, state: WorldState) -> List[Egg]:
        """Obtiene la lista de huevos activos del estado."""
        if not hasattr(state, 'active_eggs'):
            state.active_eggs = []
        return state.active_eggs

    def _check_environmental_mortality(
        self,
        egg: Egg,
        context: EnvironmentContext,
        delta_days: float,
    ) -> bool:
        """Verifica si el huevo muere por causas ambientales.
        
        Factores de mortalidad:
        - Riesgo base (depredación, clima)
        - Presión ambiental local (hacinamiento)
        """
        # Riesgo base
        mortality_chance = egg.mortality_risk * delta_days
        
        # Presión ambiental local puede aumentar la mortalidad
        try:
            local_pressure = context.get_local_pressure(int(egg.x), int(egg.y))
            if local_pressure > 1.5:
                mortality_chance *= 1.5
        except (AttributeError, TypeError):
            pass
        
        return random.random() < mortality_chance

    def _execute_hatch(
        self,
        egg: Egg,
        state: WorldState,
        pending: PendingChanges,
        current_day: float,
    ) -> None:
        """Ejecuta la eclosión de un huevo: registra el nacimiento."""
        if egg.genome is None:
            self.logger.warning(
                "⚠️ Huevo %d no tiene genoma, no se puede registrar nacimiento",
                egg.egg_id,
            )
            return
        
        # Registrar el nacimiento
        pending.register_birth(
            mother_id=egg.mother_id,
            father_id=egg.father_id,
            x=int(egg.x),
            y=int(egg.y),
            genome=egg.genome,
        )
        
        # Registrar memoria de nacimiento para la madre (si tiene capacidades cognitivas)
        mother = state.get_person_by_id(egg.mother_id)
        if mother is not None:
            cognitive_caps = CognitiveCapabilities.from_genome(mother.genome)
            
            if cognitive_caps.can_have_memory_type("child"):
                from systems.behavior.cognitive_memory_system import CognitiveMemorySystem
                CognitiveMemorySystem.add_memory(
                    person=mother,
                    mem_type=CognitiveMemorySystem.TYPE_CHILD,
                    target_id=f"egg_hatch_{egg.egg_id}",
                    intensity=0.7,
                    valence=1,
                    context="eclosion",
                    current_day=current_day,
                    pending=pending,
                )

    def _remove_eggs(self, state: WorldState, eggs_to_remove: List[Egg]) -> None:
        """Elimina huevos procesados del estado."""
        if not eggs_to_remove:
            return
        
        if not hasattr(state, 'active_eggs'):
            return
        
        eggs_to_remove_ids = {egg.egg_id for egg in eggs_to_remove}
        state.active_eggs = [
            egg for egg in state.active_eggs
            if egg.egg_id not in eggs_to_remove_ids
        ]

    def get_egg_count(self, state: WorldState) -> int:
        """Retorna el número de huevos activos."""
        if not hasattr(state, 'active_eggs'):
            return 0
        return len([e for e in state.active_eggs if e.is_alive])

    def get_eggs_by_mother(self, state: WorldState, mother_id: int) -> List[Egg]:
        """Retorna los huevos activos de una madre específica."""
        if not hasattr(state, 'active_eggs'):
            return []
        return [
            egg for egg in state.active_eggs
            if egg.mother_id == mother_id and egg.is_alive
        ]