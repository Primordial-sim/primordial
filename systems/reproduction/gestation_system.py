"""Módulo responsable de la gestación y el parto.

Implementa un modelo de gestación biológicamente realista con:
- Progresión temporal del embarazo
- Abortos espontáneos por condiciones adversas
- Mortalidad fetal por enfermedad/desnutrición
- Parto prematuro bajo estrés extremo
- Mortalidad materna durante el parto
- Integración genética vía genome.combine()
- Soporte para camadas con recombinación independiente
- Registro de nacimientos en PendingChanges

CORRECCIONES APLICADAS (Auditoría):
- Abortos espontáneos por estado fisiológico adverso
- Mortalidad fetal durante la gestación
- Parto prematuro por estrés extremo
- Mortalidad materna asociada al parto
- Efectos de la edad en complicaciones
- Configuración de especies centralizada
- Llamadas exactas a register_pregnancy_update y register_birth
"""

from __future__ import annotations

import logging
import random
from typing import Any, Optional, Dict, List

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext
from systems.behavior.cognitive_memory_system import CognitiveMemorySystem


class GestationSystem:
    """Motor de gestación con complicaciones biológicas realistas."""

    def __init__(
        self, 
        config: SimulationConfig,
        evolution_engine: Any = None,
        relationship_engine: Any = None,
    ) -> None:
        self.config = config
        self.evolution_engine = evolution_engine
        self.relationship_engine = relationship_engine
        self.logger = logging.getLogger(self.__class__.__name__)

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Procesa la progresión de todos los embarazos activos."""
        current_day = getattr(state, 'world_days_elapsed', 0.0)

        for person in state.get_all_persons():
            if person.entity_id in pending.deaths:
                continue

            if not getattr(person, 'is_pregnant', False):
                continue

            species_traits = self._get_species_traits(person.species)
            gestation_duration = species_traits.get("gestation_days", 270.0)
            
            # Avanzar el embarazo
            new_pregnancy_days = person.pregnancy_days + delta_days
            
            # Verificar complicaciones durante la gestación
            complication_result = self._check_gestation_complications(
                person=person,
                pregnancy_days=new_pregnancy_days,
                gestation_duration=gestation_duration,
                delta_days=delta_days,
            )
            
            if complication_result == "miscarriage":
                # Aborto espontáneo: finalizar embarazo con failed_increment=1
                pending.register_pregnancy_update(
                    entity_id=person.entity_id,
                    is_pregnant=False,
                    pregnancy_days=0.0,
                    failed_increment=1,
                    litter_size=1,
                )
                
                # Registrar memoria traumática
                CognitiveMemorySystem.add_memory(
                    person=person,
                    mem_type=CognitiveMemorySystem.TYPE_DISEASE,
                    target_id="miscarriage",
                    intensity=0.6,
                    valence=-1,
                    context="aborto_espontaneo",
                    current_day=current_day,
                    pending=pending,
                )
                
                self.logger.debug(
                    "⚠️ Agente %s sufrió aborto espontáneo (día %.0f de gestación)",
                    person.entity_id, new_pregnancy_days,
                )
                continue
            
            elif complication_result == "premature_birth":
                # Parto prematuro: ejecutar nacimiento con penalizaciones
                self._execute_premature_birth(
                    mother=person,
                    state=state,
                    pending=pending,
                    current_day=current_day,
                )
                continue
            
            # Verificar si el embarazo ha llegado a término
            if new_pregnancy_days >= gestation_duration:
                self._execute_full_term_birth(
                    mother=person,
                    state=state,
                    pending=pending,
                    current_day=current_day,
                )
            else:
                # Actualizar progreso del embarazo (sin failed_increment)
                pending.register_pregnancy_update(
                    entity_id=person.entity_id,
                    is_pregnant=True,
                    pregnancy_days=new_pregnancy_days,
                    failed_increment=0,
                    litter_size=person.litter_size_gestating,
                )

    def _check_gestation_complications(
        self,
        person: Any,
        pregnancy_days: float,
        gestation_duration: float,
        delta_days: float,
    ) -> str:
        """Verifica complicaciones durante la gestación.
        
        Returns:
            "normal" - El embarazo continúa normalmente
            "miscarriage" - Aborto espontáneo
            "premature_birth" - Parto prematuro
        """
        repro_cfg = self.config.reproduction
        
        # No verificar complicaciones en el primer trimestre (25% de la gestación)
        first_trimester_end = gestation_duration * 0.25
        if pregnancy_days < first_trimester_end:
            base_miscarriage_risk = getattr(repro_cfg, 'early_miscarriage_risk', 0.0001)
        else:
            base_miscarriage_risk = getattr(repro_cfg, 'miscarriage_risk', 0.00005)
        
        # --- FACTORES DE RIESGO DE ABORTO ---
        miscarriage_risk = base_miscarriage_risk
        
        # Desnutrición severa
        energy = person.emotions.get("energy", 1.0)
        if energy < 0.2:
            miscarriage_risk *= 5.0
        
        # Enfermedad activa
        if getattr(person, 'is_sick', False):
            miscarriage_risk *= 3.0
            if len(getattr(person, 'active_infections', {})) > 2:
                miscarriage_risk *= 2.0
        
        # Estrés extremo
        stress = person.emotions.get("stress", 0.0)
        if stress > 0.8:
            miscarriage_risk *= 2.5
        
        # Edad avanzada (complicaciones)
        age = getattr(person, 'age', 0.0)
        max_fertility_age = getattr(repro_cfg, 'max_fertility_age_days', 14600.0)
        if age > max_fertility_age:
            miscarriage_risk *= 3.0
        
        # Verificar aborto
        daily_miscarriage_chance = 1.0 - (1.0 - miscarriage_risk) ** delta_days
        if random.random() < daily_miscarriage_chance:
            return "miscarriage"
        
        # --- PARTO PREMATURO (solo después del 70% de la gestación) ---
        premature_threshold = gestation_duration * 0.70
        if pregnancy_days >= premature_threshold:
            premature_risk = 0.0
            
            if stress > 0.9:
                premature_risk += 0.001
            
            if person.is_sick and len(person.active_infections) > 1:
                premature_risk += 0.0005
            
            daily_premature_chance = 1.0 - (1.0 - premature_risk) ** delta_days
            if random.random() < daily_premature_chance:
                return "premature_birth"
        
        return "normal"

    def _execute_full_term_birth(
        self,
        mother: Any,
        state: WorldState,
        pending: PendingChanges,
        current_day: float,
    ) -> None:
        """Ejecuta un parto a término completo con riesgo de mortalidad materna."""
        repro_cfg = self.config.reproduction
        litter_size = mother.litter_size_gestating
        
        # Riesgo de mortalidad materna durante el parto
        maternal_mortality_risk = self._calculate_maternal_mortality_risk(mother, repro_cfg)
        
        if random.random() < maternal_mortality_risk:
            pending.register_death(
                mother.entity_id,
                reason="Complicaciones durante el parto (mortalidad materna)"
            )
            self.logger.debug(
                "⚰️ Agente %s falleció durante el parto",
                mother.entity_id,
            )
        
        # Obtener el genoma del padre (si existe)
        father_genome = None
        father_id = getattr(mother, 'partner_id', None)
        if father_id:
            father = state.get_person_by_id(father_id)
            if father and father.entity_id not in pending.deaths:
                father_genome = father.genome
        
        # Ejecutar nacimientos de la camada
        for _ in range(litter_size):
            self._execute_single_birth(
                mother=mother,
                father_genome=father_genome,
                father_id=father_id,
                state=state,
                pending=pending,
                current_day=current_day,
            )
        
        # Finalizar embarazo (sin failed_increment)
        pending.register_pregnancy_update(
            entity_id=mother.entity_id,
            is_pregnant=False,
            pregnancy_days=0.0,
            failed_increment=0,
            litter_size=1,
        )
        
        # Registrar memoria del nacimiento
        CognitiveMemorySystem.add_memory(
            person=mother,
            mem_type=CognitiveMemorySystem.TYPE_CHILD,
            target_id="birth",
            intensity=0.9,
            valence=1,
            context="nacimiento",
            current_day=current_day,
            pending=pending,
        )
        
        # Registrar día del parto para cooldown posparto
        pending.register_memory_update(
            mother.entity_id,
            "last_birth_day",
            current_day,
        )

    def _execute_premature_birth(
        self,
        mother: Any,
        state: WorldState,
        pending: PendingChanges,
        current_day: float,
    ) -> None:
        """Ejecuta un parto prematuro con mayor riesgo de mortalidad."""
        repro_cfg = self.config.reproduction
        litter_size = mother.litter_size_gestating
        
        # Riesgo aumentado en parto prematuro
        maternal_mortality_risk = self._calculate_maternal_mortality_risk(mother, repro_cfg) * 2.0
        
        if random.random() < maternal_mortality_risk:
            pending.register_death(
                mother.entity_id,
                reason="Complicaciones por parto prematuro"
            )
        
        # Obtener genoma del padre
        father_genome = None
        father_id = getattr(mother, 'partner_id', None)
        if father_id:
            father = state.get_person_by_id(father_id)
            if father and father.entity_id not in pending.deaths:
                father_genome = father.genome
        
        # En parto prematuro, hay riesgo de mortalidad fetal
        fetal_mortality_risk = getattr(repro_cfg, 'premature_fetal_mortality_risk', 0.15)
        
        for _ in range(litter_size):
            if random.random() < fetal_mortality_risk:
                self.logger.debug(
                    "⚠️ Mortalidad fetal en parto prematuro de Agente %s",
                    mother.entity_id,
                )
                continue
            
            self._execute_single_birth(
                mother=mother,
                father_genome=father_genome,
                father_id=father_id,
                state=state,
                pending=pending,
                current_day=current_day,
            )
        
        # Finalizar embarazo (sin failed_increment)
        pending.register_pregnancy_update(
            entity_id=mother.entity_id,
            is_pregnant=False,
            pregnancy_days=0.0,
            failed_increment=0,
            litter_size=1,
        )
        
        pending.register_memory_update(
            mother.entity_id,
            "last_birth_day",
            current_day,
        )

    def _execute_single_birth(
        self,
        mother: Any,
        father_genome: Optional[Any],
        father_id: Optional[int],
        state: WorldState,
        pending: PendingChanges,
        current_day: float,
    ) -> None:
        """Ejecuta el nacimiento de un individuo con recombinación genética.
        
        GENÉTICA UNIVERSAL:
        - Si hay padre: reproducción sexual con combine()
        - Si no hay padre: reproducción asexual con replicate()
        """
        from core.config.simulation_config import MutationConfig
        mutation_config = MutationConfig()
        
        if father_genome is not None:
            # REPRODUCCIÓN SEXUAL
            child_genome = mother.genome.combine(father_genome, mutation_config)
        else:
            # REPRODUCCIÓN ASEXUAL (partenogénesis/clonación)
            child_genome = mother.genome.replicate(mutation_config)
        
        # Determinar posición (cerca de la madre)
        spawn_x = mother.x + random.randint(-2, 2)
        spawn_y = mother.y + random.randint(-2, 2)
        
        # CORRECCIÓN: register_birth NO acepta species (se deriva del genome)
        pending.register_birth(
            mother_id=mother.entity_id,
            father_id=father_id,
            x=spawn_x,
            y=spawn_y,
            genome=child_genome,
        )

    def _calculate_maternal_mortality_risk(self, mother: Any, repro_cfg: Any) -> float:
        """Calcula el riesgo de mortalidad materna durante el parto.
        
        Factores de riesgo:
        - Edad avanzada
        - Enfermedad activa
        - Desnutrición
        - Estrés extremo
        - Embarazo múltiple (camada grande)
        """
        base_risk = getattr(repro_cfg, 'maternal_mortality_risk', 0.001)
        
        # Edad: mayor riesgo en edades extremas
        age = getattr(mother, 'age', 0.0)
        max_fertility_age = getattr(repro_cfg, 'max_fertility_age_days', 14600.0)
        if age > max_fertility_age:
            base_risk *= 3.0
        elif age < max_fertility_age * 0.3:
            base_risk *= 2.0
        
        # Enfermedad activa
        if getattr(mother, 'is_sick', False):
            base_risk *= 2.0
        
        # Desnutrición
        energy = mother.emotions.get("energy", 1.0)
        if energy < 0.3:
            base_risk *= 2.5
        
        # Estrés extremo
        stress = mother.emotions.get("stress", 0.0)
        if stress > 0.8:
            base_risk *= 1.5
        
        # Camada grande (mayor riesgo)
        litter_size = getattr(mother, 'litter_size_gestating', 1)
        if litter_size > 2:
            base_risk *= (1.0 + (litter_size - 2) * 0.2)
        
        return min(0.1, base_risk)  # Cap del 10%

    def _get_species_traits(self, species: str) -> Dict[str, Any]:
        """Configuración de especies centralizada.
        
        GENÉTICA UNIVERSAL: Usa species_profiles de ReproductionConfig
        como fuente única de verdad.
        """
        repro_cfg = self.config.reproduction
        species_profiles = getattr(repro_cfg, 'species_profiles', {})
        
        # Perfil específico de especie
        profile = species_profiles.get(species, {})
        
        # Valores por defecto universales
        defaults = {
            "gestation_days": 180.0,
            "litter_size_min": 1,
            "litter_size_max": 2,
            "parthenogenesis_chance": 0.0,
            "can_gestate_female_only": True,
            "fertility_window_start": 3650.0,
            "fertility_window_end": 10950.0,
        }
        
        # Combinar con defaults
        traits = {**defaults, **profile}
        
        # Calcular litter_size promedio para compatibilidad con código legacy
        if "litter_size" not in traits:
            traits["litter_size"] = (traits["litter_size_min"] + traits["litter_size_max"]) // 2
        
        return traits