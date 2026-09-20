"""Módulo responsable de la concepción y fertilización.

Implementa un modelo de concepción biológicamente realista con:
- Verificación explícita de sexo para gestación
- Prevención de doble embarazo por pareja
- Fertilidad por producto (esterilidad real)
- Infertilidad adquirida por edad, enfermedad y trauma
- Periodo posparto refractario
- Soporte multiespecie con partenogénesis
- Integración con PendingChanges para coherencia transaccional

GENÉTICA UNIVERSAL: Distingue entre reproducción vivípara (embarazo)
y ovípara (huevos) basándose en ReproductiveCapabilities.

CORRECCIONES APLICADAS (Auditoría):
- Verificación de sexo antes de procesar embarazo
- Prevención de doble concepción en el mismo tick
- Fertilidad multiplicativa en lugar de promedio
- Infertilidad adquirida por factores fisiológicos
- Periodo refractario posparto configurable
- Llamadas exactas a register_pregnancy_update (is_pregnant, pregnancy_days, failed_increment)
- OPCIÓN B.2: Ovíparos ponen huevos en lugar de quedar embarazados

SISTEMA DE ENERGÍA:
- Verificación de energía mínima antes de intentar reproducirse
- Gasto de energía al concebir (vivíparos)
- Gasto de energía al poner huevos (ovíparos)
- Gasto de energía en reproducción asexual
"""

from __future__ import annotations

import logging
import random
from typing import Any, Optional, Dict

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext
from systems.reproduction.reproductive_capabilities import ReproductiveCapabilities
from systems.reproduction.egg_model import Egg
from systems.behavior.cognitive_capabilities import CognitiveCapabilities


class ConceptionSystem:
    """Motor de concepción con restricciones biológicas realistas."""

    def __init__(self, config: SimulationConfig, relationship_engine: Any = None) -> None:
        self.config = config
        self.relationship_engine = relationship_engine
        self.logger = logging.getLogger(self.__class__.__name__)
        self._clutch_counter = 0
        
        # Parámetros de coste energético por reproducción
        self.energy_cost_per_offspring: float = 10.0  # Energía por cada descendiente
        self.energy_cost_per_egg: float = 5.0         # Energía por cada huevo puesto
        self.minimum_energy_to_reproduce: float = 20.0  # Energía mínima para intentar reproducirse

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

            # GENÉTICA UNIVERSAL: Consultar capacidades reproductivas del genoma
            repro_caps = ReproductiveCapabilities.from_genome(person.genome)
            
            # Solo procesar si puede reproducirse
            if not repro_caps.can_reproduce:
                continue

            # CORRECCIÓN 1: Verificación explícita de sexo para gestación
            # Solo las hembras pueden gestar (a menos que la especie sea hermafrodita)
            # GENÉTICA UNIVERSAL: Solo verificar si requiere pareja (reproducción sexual)
            if repro_caps.requires_partner:
                species_traits = self._get_species_traits(person.species)
                can_gestate = species_traits.get("can_gestate_female_only", True)
                
                if can_gestate and getattr(person, 'gender', 'M') != 'F':
                    continue
            else:
                # Reproducción asexual: no hay restricción de sexo
                pass

            # Verificar que puede reproducirse (método legacy)
            if hasattr(person, 'can_reproduce') and not person.can_reproduce():
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
            
            # NUEVO: Verificación de energía mínima para reproducirse
            # Sin energía suficiente, el organismo no puede invertir en reproducción
            current_energy = getattr(person, 'energy', self.minimum_energy_to_reproduce)
            if current_energy < self.minimum_energy_to_reproduce:
                continue  # No tiene energía suficiente para reproducirse

            # Determinar compañero reproductivo
            # GENÉTICA UNIVERSAL: Solo buscar pareja si la requiere
            partner_id = None
            partner = None
            
            if repro_caps.requires_partner:
                partner_id = getattr(person, 'partner_id', None)
                
                if partner_id is not None:
                    partner = state.get_person_by_id(partner_id)
                    
                    # CORRECCIÓN 2: Prevención de doble embarazo
                    if partner and getattr(partner, 'is_pregnant', False):
                        continue
                    if partner and partner.entity_id in pending.pregnancy_updates:
                        continue
                    if person.entity_id in pending.pregnancy_updates:
                        continue
            else:
                # Reproducción asexual: no hay pareja
                pass

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
                litter_size = self._determine_litter_size(person, repro_cfg)
                
                # GENÉTICA UNIVERSAL: Distinguir entre vivíparos y ovíparos
                if repro_caps.is_viviparous():
                    # VIVÍPAROS: Registrar embarazo
                    pending.register_pregnancy_update(
                        entity_id=person.entity_id,
                        is_pregnant=True,
                        pregnancy_days=0.0,
                        failed_increment=0,
                        litter_size=litter_size,
                    )
                    
                    # NUEVO: Gasto de energía por concepción
                    # El acto de concebir y preparar el cuerpo cuesta energía
                    energy_cost = self._calculate_conception_energy_cost(person, litter_size)
                    if hasattr(person, 'spend_energy'):
                        person.spend_energy(energy_cost)
                    
                    # Registrar en memoria para cooldown posparto futuro
                    pending.register_memory_update(
                        person.entity_id,
                        "last_conception_day",
                        current_day,
                    )
                    
                elif repro_caps.is_oviparous():
                    # OVÍPAROS: Poner huevos
                    self._lay_eggs(
                        mother=person,
                        partner=partner,
                        litter_size=litter_size,
                        repro_caps=repro_caps,
                        state=state,
                        pending=pending,
                        current_day=current_day,
                    )
                    
                    # NUEVO: Gasto de energía por puesta de huevos
                    # Poner huevos requiere mucha energía (cáscara, nutrientes)
                    energy_cost = self._calculate_egg_laying_energy_cost(person, litter_size)
                    if hasattr(person, 'spend_energy'):
                        person.spend_energy(energy_cost)
                    
                else:
                    # ASEXUAL / SIN GESTACIÓN: Reproducción directa
                    self._asexual_reproduction(
                        parent=person,
                        litter_size=litter_size,
                        state=state,
                        pending=pending,
                        current_day=current_day,
                    )
                    
                    # NUEVO: Gasto de energía por división/clonación
                    energy_cost = self._calculate_asexual_energy_cost(person, litter_size)
                    if hasattr(person, 'spend_energy'):
                        person.spend_energy(energy_cost)

    def _lay_eggs(
        self,
        mother: Any,
        partner: Optional[Any],
        litter_size: int,
        repro_caps: ReproductiveCapabilities,
        state: WorldState,
        pending: PendingChanges,
        current_day: float,
    ) -> None:
        """Pone huevos para organismos ovíparos.
        
        GENÉTICA UNIVERSAL: Los huevos se registran en pending.new_eggs
        y serán procesados por EggSystem en ticks posteriores.
        """
        from core.config.simulation_config import MutationConfig
        mutation_config = MutationConfig()
        
        # Obtener genoma del padre (si existe)
        father_genome = None
        father_id = None
        if partner is not None:
            father_genome = partner.genome
            father_id = partner.entity_id
        
        # Generar ID de nidada
        self._clutch_counter += 1
        clutch_id = self._clutch_counter
        
        # Asegurar que pending tiene la lista de huevos nuevos
        if not hasattr(pending, 'new_eggs'):
            pending.new_eggs = []
        
        # Crear huevos
        for i in range(litter_size):
            # Combinar genomas
            if father_genome is not None:
                child_genome = mother.genome.combine(father_genome, mutation_config)
            else:
                child_genome = mother.genome.replicate(mutation_config)
            
            # Posición cerca de la madre
            spawn_x = mother.x + random.randint(-2, 2)
            spawn_y = mother.y + random.randint(-2, 2)
            
            egg = Egg(
                egg_id=0,  # Se asignará automáticamente
                mother_id=mother.entity_id,
                father_id=father_id,
                x=spawn_x,
                y=spawn_y,
                genome=child_genome,
                laid_day=current_day,
                incubation_days=repro_caps.gestation_days,
                clutch_id=clutch_id,
            )
            
            pending.new_eggs.append(egg)
        
        # Registrar en memoria para cooldown
        pending.register_memory_update(
            mother.entity_id,
            "last_conception_day",
            current_day,
        )
        
        # Registrar memoria de puesta (si tiene capacidades cognitivas)
        cognitive_caps = CognitiveCapabilities.from_genome(mother.genome)
        if cognitive_caps.can_have_memory_type("child"):
            from systems.behavior.cognitive_memory_system import CognitiveMemorySystem
            CognitiveMemorySystem.add_memory(
                person=mother,
                mem_type=CognitiveMemorySystem.TYPE_CHILD,
                target_id=f"clutch_{clutch_id}",
                intensity=0.5,
                valence=1,
                context="puesta_huevos",
                current_day=current_day,
                pending=pending,
            )
        
        self.logger.debug(
            "🥚 Agente %s puso %d huevos (nidada %d)",
            mother.entity_id, litter_size, clutch_id,
        )

    def _asexual_reproduction(
        self,
        parent: Any,
        litter_size: int,
        state: WorldState,
        pending: PendingChanges,
        current_day: float,
    ) -> None:
        """Reproducción asexual directa (plantas, bacterias).
        
        GENÉTICA UNIVERSAL: Los descendientes se registran directamente
        como nacimientos sin gestación ni huevos.
        """
        from core.config.simulation_config import MutationConfig
        mutation_config = MutationConfig()
        
        for _ in range(litter_size):
            # Clonar genoma con mutación
            child_genome = parent.genome.replicate(mutation_config)
            
            # Posición cerca del progenitor
            spawn_x = parent.x + random.randint(-3, 3)
            spawn_y = parent.y + random.randint(-3, 3)
            
            # Registrar nacimiento directamente
            pending.register_birth(
                mother_id=parent.entity_id,
                father_id=None,
                x=spawn_x,
                y=spawn_y,
                genome=child_genome,
            )
        
        # Registrar en memoria para cooldown
        pending.register_memory_update(
            parent.entity_id,
            "last_birth_day",
            current_day,
        )

    def _calculate_acquired_fertility(self, person: Any) -> float:
        """CORRECCIÓN 4: Calcula la fertilidad adquirida basada en estado fisiológico.
        
        GENÉTICA UNIVERSAL: Solo aplica factores fisiológicos si tiene emociones.
        """
        # GENÉTICA UNIVERSAL: Solo aplicar factores fisiológicos si tiene emociones
        cognitive_caps = CognitiveCapabilities.from_genome(person.genome)
        
        if not cognitive_caps.has_emotions:
            return 1.0  # Sin emociones, no hay factores fisiológicos adquiridos 
        
        modifier = 1.0
        
        # Edad: penalización fuera de la ventana fértil óptima
        repro_cfg = self.config.reproduction
        age = getattr(person, 'age', 0.0)
        optimal_start = getattr(repro_cfg, 'min_fertility_age_days', 5475.0)
        optimal_end = getattr(repro_cfg, 'max_fertility_age_days', 14600.0)
        
        if age < optimal_start:
            modifier *= (age / max(1.0, optimal_start)) * 0.5
        elif age > optimal_end:
            over_age = age - optimal_end
            modifier *= max(0.05, 1.0 - (over_age / 3650.0))
        
        # Enfermedad activa
        if getattr(person, 'is_sick', False):
            modifier *= 0.4
        
        # Estrés extremo
        stress = person.emotions.get("stress", 0.0)
        if stress > 0.7:
            modifier *= 1.0 - ((stress - 0.7) / 0.3) * 0.6
        
        # Baja energía (desnutrición)
        energy = person.emotions.get("energy", 1.0)
        if energy < 0.4:
            modifier *= energy / 0.4
        
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
        
        GENÉTICA UNIVERSAL: Ajusta según capacidades reproductivas.
        """
        # GENÉTICA UNIVERSAL: Consultar capacidades reproductivas
        repro_caps = ReproductiveCapabilities.from_genome(person.genome)
        
        # Fertilidad genética base
        mother_fertility = person.genome.get_trait_value("fertility")
        
        # Aplicar nivel de fertilidad de las capacidades
        fertility_modifier = mother_fertility * repro_caps.fertility_level
        
        if partner is not None:
            # CORRECCIÓN 3: Producto de fertilidades (no promedio)
            father_fertility = partner.genome.get_trait_value("fertility")
            fertility_modifier *= father_fertility
        else:
            # Reproducción asexual: solo fertilidad de la madre
            fertility_modifier *= 0.8

        # GENÉTICA UNIVERSAL: Solo aplicar emociones si tiene capacidades cognitivas
        cognitive_caps = CognitiveCapabilities.from_genome(person.genome)
        
        if cognitive_caps.has_emotions:
            # Energía como factor limitante
            if partner is not None:
                energy_multiplier = min(
                    person.emotions.get("energy", 1.0),
                    partner.emotions.get("energy", 1.0)
                )
            else:
                energy_multiplier = person.emotions.get("energy", 1.0)
        else:
            energy_multiplier = 1.0

        # CORRECCIÓN 5: Penalización por longevidad con clamp de seguridad
        if partner is not None:
            avg_longevity = (
                person.genome.get_trait_value("longevity") + 
                partner.genome.get_trait_value("longevity")
            ) / 2.0
        else:
            avg_longevity = person.genome.get_trait_value("longevity")
        
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

        return max(0.0, min(0.5, final_chance))

    def _determine_litter_size(self, person: Any, repro_cfg: Any) -> int:
        """Determina el tamaño de camada según las capacidades reproductivas.
        
        GENÉTICA UNIVERSAL: Usa litter_size_min y litter_size_max de las capacidades.
        """
        repro_caps = ReproductiveCapabilities.from_genome(person.genome)
        
        min_size = repro_caps.litter_size_min
        max_size = repro_caps.litter_size_max
        
        if min_size == max_size:
            litter_size = min_size
        else:
            litter_size = random.randint(min_size, max_size)
        
        max_litter = getattr(repro_cfg, 'max_litter_size', 8)
        return min(litter_size, max_litter)

    # =========================================================================
    # CÁLCULOS DE COSTE ENERGÉTICO POR REPRODUCCIÓN
    # =========================================================================

    def _calculate_conception_energy_cost(self, person: Any, litter_size: int) -> float:
        """Calcula el coste energético de concebir y preparar el embarazo.
        
        El coste depende de:
        - Tamaño de la camada (más bebés = más preparación)
        - Tamaño corporal del progenitor
        
        Args:
            person: El agente que concibe.
            litter_size: Tamaño de la camada.
            
        Returns:
            Energía a gastar.
        """
        # Coste base por cada descendiente
        cost = self.energy_cost_per_offspring * litter_size
        
        # Modificador por tamaño corporal
        size_factor = self._get_size_factor(person)
        cost *= size_factor
        
        return max(0.0, cost)

    def _calculate_egg_laying_energy_cost(self, person: Any, litter_size: int) -> float:
        """Calcula el coste energético de poner huevos.
        
        Poner huevos requiere producir cáscara, nutrientes y el esfuerzo físico.
        Es más costoso que la concepción vivípara porque es un esfuerzo inmediato.
        
        Args:
            person: El agente que pone huevos.
            litter_size: Número de huevos.
            
        Returns:
            Energía a gastar.
        """
        # Coste base por cada huevo
        cost = self.energy_cost_per_egg * litter_size
        
        # Modificador por tamaño corporal
        size_factor = self._get_size_factor(person)
        cost *= size_factor
        
        return max(0.0, cost)

    def _calculate_asexual_energy_cost(self, person: Any, litter_size: int) -> float:
        """Calcula el coste energético de reproducción asexual.
        
        La división celular o clonación requiere energía metabólica.
        
        Args:
            person: El agente que se divide.
            litter_size: Número de descendientes.
            
        Returns:
            Energía a gastar.
        """
        # Coste reducido comparado con reproducción sexual (no hay búsqueda de pareja)
        cost = self.energy_cost_per_offspring * 0.5 * litter_size
        
        # Modificador por tamaño corporal
        size_factor = self._get_size_factor(person)
        cost *= size_factor
        
        return max(0.0, cost)

    def _get_size_factor(self, person: Any) -> float:
        """Obtiene el factor de tamaño basado en el genoma."""
        try:
            body_size = getattr(person.genome, 'body_size', None)
            if body_size is not None:
                return 0.5 + (body_size * 1.5)
        except (AttributeError, TypeError):
            pass
        
        return 1.0  # Por defecto: tamaño medio

    def _get_species_traits(self, species: str) -> Dict[str, Any]:
        """Obtiene rasgos reproductivos de la especie."""
        repro_cfg = self.config.reproduction
        species_profiles = getattr(repro_cfg, 'species_profiles', {})
        profile = species_profiles.get(species, {})
        
        defaults = {
            "gestation_days": 180.0,
            "litter_size_min": 1,
            "litter_size_max": 2,
            "parthenogenesis_chance": 0.0,
            "can_gestate_female_only": True,
            "fertility_window_start": 3650.0,
            "fertility_window_end": 10950.0,
        }
        
        traits = {**defaults, **profile}
        
        if "litter_size" not in traits:
            traits["litter_size"] = (traits["litter_size_min"] + traits["litter_size_max"]) // 2
        
        return traits