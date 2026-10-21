"""Sistema de memoria cognitiva con traumas implícitos y explícitos.

MIGRACIÓN HEXAGONAL:
- person.x/y → person.q/r
- preferred_sector usa (q, r) en lugar de (x, y)
"""

from __future__ import annotations

import logging
import math
from typing import Any, Optional

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.behavior.cognitive_capabilities import CognitiveCapabilities
from systems.environment.environment_context import EnvironmentContext


class CognitiveMemorySystem:
    """Procesa la impronta cognitiva, recuerdos específicos y desgaste psicológico."""

    # Tipos de memoria episódica
    TYPE_COMPANION = "companion"
    TYPE_CONFLICT = "conflict"
    TYPE_EXPERIENCE = "experience"
    TYPE_EVENT = "event"
    TYPE_MARRIAGE = "marriage"
    TYPE_CHILD = "child"
    TYPE_DEATH = "death"
    TYPE_ADOPTION = "adoption"
    TYPE_DIVORCE = "divorce"
    TYPE_DISEASE = "disease"
    TYPE_MIGRATION = "migration"

    def __init__(self, config: SimulationConfig) -> None:
        """Inicializa el sistema de memoria cognitiva."""
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    def _get_current_trauma(
        self, person: Any, pending: PendingChanges, trauma_key: str
    ) -> float:
        """Helper para obtener el valor actual de un trauma, respetando el búfer."""
        if person.entity_id in pending.memory_updates:
            return pending.memory_updates[person.entity_id].get(
                trauma_key, person.memory.get(trauma_key, 0.0)
            )
        return person.memory.get(trauma_key, 0.0)

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Actualiza el estado mental de todos los agentes vivos."""
        cog_cfg = self.config.cognition

        for person in state.get_all_persons():
            if person.entity_id in pending.deaths:
                continue

            # GENÉTICA UNIVERSAL: Consultar capacidades cognitivas
            cognitive_caps = CognitiveCapabilities.from_genome(person.genome)

            # =================================================================
            # PARTE A: MEMORIA IMPLÍCITA (Traumas y Preferencias)
            # =================================================================
            trauma_overcrowding = 0.0
            trauma_sickness = 0.0
            trauma_adoption = 0.0
            trauma_abandonment = 0.0
            rebellion_cooldown = 0.0
            preferred_sector = None

            # Solo procesar traumas si tiene emociones
            if cognitive_caps.has_emotions:
                temperament = person.genome.get_trait_value("temperament")
                adjusted_lambda = cog_cfg.base_forgetting_rate * (
                    temperament + cog_cfg.temperament_modifier
                )
                decay_factor = math.exp(-adjusted_lambda * delta_days)

                # HEX: Usar person.q, person.r en lugar de person.x, person.y
                local_pressure = context.get_local_pressure(person.q, person.r)

                # TRAUMA POR HACINAMIENTO
                trauma_overcrowding = (
                    self._get_current_trauma(person, pending, "trauma_overcrowding")
                    * decay_factor
                )
                if local_pressure > cog_cfg.overcrowding_threshold:
                    trauma_overcrowding += cog_cfg.overcrowding_impact * delta_days

                # TRAUMA POR ENFERMEDAD
                trauma_sickness = (
                    self._get_current_trauma(person, pending, "trauma_sickness")
                    * decay_factor
                )
                if person.is_sick:
                    trauma_sickness += cog_cfg.sickness_impact * delta_days

                # TRAUMA POR ADOPCIÓN
                if cognitive_caps.can_form_trauma("adoption"):
                    trauma_adoption = (
                        self._get_current_trauma(person, pending, "trauma_adoption")
                        * decay_factor
                    )
                    if trauma_adoption > 0.0:
                        delta_trauma = trauma_adoption - (
                            trauma_adoption * decay_factor
                        )
                        pending.register_emotion_update(
                            person.entity_id, "stress", -delta_trauma * 0.6
                        )
                        pending.register_emotion_update(
                            person.entity_id, "happiness", delta_trauma * 0.5
                        )

                # TRAUMA POR ABANDONO
                if cognitive_caps.can_form_trauma("abandonment"):
                    trauma_abandonment = (
                        self._get_current_trauma(
                            person, pending, "trauma_abandonment"
                        )
                        * decay_factor
                    )

                # PREFERENCIA ESPACIAL
                if cognitive_caps.has_episodic_memory:
                    preferred_sector = person.memory.get("preferred_sector", None)
                    if (
                        person.is_adult
                        and not person.is_sick
                        and person.children_count > 0
                    ) or person.is_senior:
                        # HEX: Usar q, r en lugar de x, y
                        preferred_sector = (
                            person.q // context.sector_size,
                            person.r // context.sector_size,
                        )

                # REBELLION COOLDOWN
                if cognitive_caps.has_complex_motivations:
                    rebellion_cooldown = max(
                        0.0,
                        person.memory.get("rebellion_cooldown", 0.0) - delta_days,
                    )

            # Registrar cambios de memoria implícita
            pending.register_memory_update(
                person.entity_id,
                "trauma_overcrowding",
                min(cog_cfg.max_trauma_cap, trauma_overcrowding),
            )
            pending.register_memory_update(
                person.entity_id,
                "trauma_sickness",
                min(cog_cfg.max_trauma_cap, trauma_sickness),
            )
            pending.register_memory_update(
                person.entity_id,
                "trauma_adoption",
                min(cog_cfg.max_trauma_cap, trauma_adoption),
            )
            pending.register_memory_update(
                person.entity_id,
                "trauma_abandonment",
                min(cog_cfg.max_trauma_cap, trauma_abandonment),
            )
            pending.register_memory_update(
                person.entity_id, "rebellion_cooldown", rebellion_cooldown
            )
            pending.register_memory_update(
                person.entity_id, "preferred_sector", preferred_sector
            )

            # =================================================================
            # PARTE B: MEMORIA EXPLÍCITA (Recuerdos episódicos)
            # =================================================================
            if cognitive_caps.has_episodic_memory:
                episodic = person.memory.get("episodic", {})
                if not isinstance(episodic, dict):
                    episodic = {}
                else:
                    episodic = episodic.copy()

                keys_to_delete = []
                total_trauma_episodic = 0.0
                total_nostalgia = 0.0
                current_day = getattr(state, "world_days_elapsed", 0.0)

                for mem_key, mem_data in episodic.items():
                    # Asegurar metadatos
                    mem_data.setdefault("created_day", current_day)
                    mem_data.setdefault("last_reinforced_day", current_day)
                    mem_data.setdefault("times_reinforced", 1)
                    mem_data.setdefault("context", "general")

                    # Decaimiento exponencial con consolidación
                    emotional_importance = (
                        abs(mem_data.get("valence", 0))
                        * cog_cfg.emotional_importance_factor
                    )
                    reinforcement_bonus = min(
                        0.5, mem_data.get("times_reinforced", 1) * 0.05
                    )
                    effective_forgetting_rate = cog_cfg.episodic_forgetting_rate * (
                        1.0 - emotional_importance - reinforcement_bonus
                    )
                    mem_data["intensity"] *= math.exp(
                        -effective_forgetting_rate * delta_days
                    )

                    if mem_data["intensity"] <= cog_cfg.episodic_min_intensity:
                        keys_to_delete.append(mem_key)
                    else:
                        if mem_data.get("valence", 0) < 0:
                            total_trauma_episodic += mem_data["intensity"]
                        else:
                            total_nostalgia += mem_data["intensity"]

                for k in keys_to_delete:
                    del episodic[k]

                # Poda de capacidad máxima
                if len(episodic) > cog_cfg.max_episodic_memories:
                    sorted_memories = sorted(
                        episodic.items(), key=lambda x: x[1]["intensity"]
                    )
                    to_remove = len(episodic) - cog_cfg.max_episodic_memories
                    for i in range(to_remove):
                        del episodic[sorted_memories[i][0]]

                pending.register_memory_update(
                    person.entity_id, "episodic", episodic
                )

                # Cálculo de estrés cognitivo
                if cognitive_caps.has_complex_brain:
                    trauma_penalty = min(
                        cog_cfg.max_cognitive_stress,
                        total_trauma_episodic * cog_cfg.trauma_to_stress_factor,
                    )
                    nostalgia_buff = min(
                        cog_cfg.max_cognitive_stress,
                        total_nostalgia * cog_cfg.nostalgia_buffer_factor,
                    )
                    cognitive_stress = max(0.0, trauma_penalty - nostalgia_buff)
                    pending.register_memory_update(
                        person.entity_id, "cognitive_stress", cognitive_stress
                    )
                else:
                    pending.register_memory_update(
                        person.entity_id, "cognitive_stress", 0.0
                    )
            else:
                pending.register_memory_update(person.entity_id, "episodic", {})
                pending.register_memory_update(
                    person.entity_id, "cognitive_stress", 0.0
                )

    # =====================================================================
    # MÉTODOS ESTÁTICOS
    # =====================================================================

    @staticmethod
    def add_memory(
        person: Any,
        mem_type: str,
        target_id: str,
        intensity: float,
        valence: int,
        context: str = "general",
        current_day: float = 0.0,
        pending: Optional[PendingChanges] = None,
    ) -> None:
        """Graba un suceso en el cerebro del agente con metadatos completos."""
        if not hasattr(person, "memory") or not isinstance(person.memory, dict):
            return

        # GENÉTICA UNIVERSAL: Verificar si puede formar este tipo de memoria
        cognitive_caps = CognitiveCapabilities.from_genome(person.genome)
        if not cognitive_caps.can_have_memory_type(mem_type):
            return

        if "episodic" not in person.memory or not isinstance(
            person.memory["episodic"], dict
        ):
            person.memory["episodic"] = {}

        key = f"{mem_type}_{target_id}"
        episodic = person.memory["episodic"]

        if key in episodic:
            # Reforzar recuerdo existente
            episodic[key]["intensity"] = min(
                1.0, episodic[key]["intensity"] + intensity
            )
            episodic[key]["valence"] = (episodic[key]["valence"] + valence) / 2.0
            episodic[key]["last_reinforced_day"] = current_day
            episodic[key]["times_reinforced"] += 1
        else:
            # Crear nuevo recuerdo
            episodic[key] = {
                "intensity": min(1.0, intensity),
                "valence": valence,
                "created_day": current_day,
                "last_reinforced_day": current_day,
                "times_reinforced": 1,
                "context": context,
            }

        if pending is not None:
            pending.register_memory_update(person.entity_id, "episodic", episodic)

    @staticmethod
    def get_bias_towards(person: Any, target_id: str) -> float:
        """Calcula la afinidad hacia una persona o lugar basada en recuerdos."""
        episodic = person.memory.get("episodic", {})
        if not isinstance(episodic, dict):
            return 0.0

        bias = 0.0
        for mem_type in [
            CognitiveMemorySystem.TYPE_COMPANION,
            CognitiveMemorySystem.TYPE_CONFLICT,
            CognitiveMemorySystem.TYPE_EXPERIENCE,
            CognitiveMemorySystem.TYPE_MARRIAGE,
            CognitiveMemorySystem.TYPE_CHILD,
            CognitiveMemorySystem.TYPE_DEATH,
            CognitiveMemorySystem.TYPE_ADOPTION,
            CognitiveMemorySystem.TYPE_DIVORCE,
            CognitiveMemorySystem.TYPE_DISEASE,
            CognitiveMemorySystem.TYPE_MIGRATION,
        ]:
            key = f"{mem_type}_{target_id}"
            if key in episodic:
                bias += episodic[key]["intensity"] * episodic[key]["valence"]

        return max(-1.0, min(1.0, bias))