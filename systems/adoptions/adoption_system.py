"""Sistema de adopciones con Utility AI.

MIGRACIÓN HEXAGONAL:
- person.x/y → person.q/r
- math.hypot(dx, dy) → distancia hexagonal
- register_movement(x, y) → register_movement(q, r)
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from entities.person.person import Person
from systems.behavior.cognitive_memory_system import CognitiveMemorySystem
from systems.environment.environment_context import EnvironmentContext
from systems.relationships.relationship_experience_engine import (
    RelationshipExperienceEngine,
)
from systems.relationships.relationship_model import RelationshipEventType


@dataclass
class _AdoptionRelationalEvent:
    """Evento ligero compatible con el RelationshipExperienceEngine."""

    event_type: RelationshipEventType
    intensity: float
    context: str


class AdoptionSystem:
    """Identifica huérfanos y asigna familias mediante Utility AI."""

    def __init__(
        self,
        config: SimulationConfig,
        ancestry_queries: Any = None,
        event_bus: Any = None,
        relationship_engine: Optional[RelationshipExperienceEngine] = None,
    ) -> None:
        """Inicializa el sistema de adopciones."""
        self.config = config
        self.ancestry_queries = ancestry_queries
        self.event_bus = event_bus
        self.relationship_engine = relationship_engine
        self.logger = logging.getLogger("AdoptionSystem")

    def _hex_distance(self, q1: int, r1: int, q2: int, r2: int) -> float:
        """Calcula la distancia hexagonal entre dos celdas axiales."""
        dq = q1 - q2
        dr = r1 - r2
        return float((abs(dq) + abs(dr) + abs(dq + dr)) // 2)

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Ejecuta el ciclo de adopciones con filtrado de idoneidad."""
        adoptions_cfg = self.config.adoptions
        all_persons = state.get_all_persons()
        current_day = getattr(state, "world_days_elapsed", 0.0)

        # 1. DETECCIÓN DE HUÉRFANOS
        orphans: List[Person] = []
        for person in all_persons:
            if self._is_eligible_orphan(person, state, pending, adoptions_cfg):
                orphans.append(person)

        if not orphans:
            return

        # AGRUPACIÓN DE HUÉRFANOS POR HERMANDAD
        sibling_groups = self._group_by_siblinghood(orphans)
        self.logger.debug(
            "Detectados %d grupos de hermanos entre %d huérfanos",
            len(sibling_groups),
            len(orphans),
        )

        # 2. FILTRADO DE FAMILIAS ELEGIBLES
        eligible_parents: List[Person] = []
        seen_couples: Set[int] = set()

        for person in all_persons:
            if person.entity_id in pending.deaths or person.entity_id in seen_couples:
                continue

            is_couple = (
                person.marital_status == "casado" and person.partner_id is not None
            )
            is_single = person.marital_status in ("soltero", "viudo", "divorciado")

            if is_couple:
                if person.age < adoptions_cfg.min_adoptive_age_days:
                    continue
            elif is_single and adoptions_cfg.allow_single_parent_adoption:
                if person.age < adoptions_cfg.min_single_parent_age_days:
                    continue
                if (
                    person.emotions.get("energy", 0.0)
                    < adoptions_cfg.min_single_parent_energy
                ):
                    continue
                if (
                    person.emotions.get("stress", 0.0)
                    > adoptions_cfg.max_single_parent_stress
                ):
                    continue
            else:
                continue

            if person.children_count >= adoptions_cfg.max_children_for_adoption:
                continue
            if person.is_sick:
                continue
            if person.emotions.get("stress", 0.0) > 0.7:
                continue

            # HEX: Usar person.q, person.r en lugar de person.x, person.y
            local_pressure = context.get_local_pressure(person.q, person.r)
            if local_pressure > 0.8:
                continue

            eligible_parents.append(person)
            if person.partner_id is not None:
                seen_couples.add(person.partner_id)

        # 3. ASIGNACIÓN TRANSACCIONAL POR GRUPOS
        min_age_diff = getattr(adoptions_cfg, "min_age_difference_days", 5475.0)
        adopted_orphans: Set[int] = set()

        for sibling_group in sibling_groups:
            if not eligible_parents:
                break

            best_family = self._find_family_for_sibling_group(
                sibling_group, eligible_parents, min_age_diff, context
            )

            if best_family is None:
                self.logger.debug(
                    "No hay familia para grupo de %d hermanos, procesando individualmente",
                    len(sibling_group),
                )
                for orphan in sibling_group:
                    self._process_individual_adoption(
                        orphan,
                        eligible_parents,
                        min_age_diff,
                        context,
                        state,
                        pending,
                        adopted_orphans,
                        current_day,
                    )
            else:
                self._process_group_adoption(
                    sibling_group,
                    best_family,
                    state,
                    pending,
                    adopted_orphans,
                    current_day,
                )
                eligible_parents.remove(best_family)

        # 4. FALLBACK: PENALIZACIONES PROGRESIVAS
        self._apply_abandonment_penalties(
            orphans, adopted_orphans, delta_days, pending
        )

    def _group_by_siblinghood(self, orphans: List[Person]) -> List[List[Person]]:
        """Agrupa huérfanos por hermandad en O(n)."""
        if not orphans:
            return []

        mother_to_orphans: Dict[int, List[Person]] = {}
        father_to_orphans: Dict[int, List[Person]] = {}
        adoptive_to_orphans: Dict[int, List[Person]] = {}

        for orphan in orphans:
            if orphan.mother_id is not None:
                mother_to_orphans.setdefault(orphan.mother_id, []).append(orphan)
            if orphan.father_id is not None:
                father_to_orphans.setdefault(orphan.father_id, []).append(orphan)
            for adoptive_parent_id in orphan.adoptive_parents:
                adoptive_to_orphans.setdefault(adoptive_parent_id, []).append(orphan)

        parent_map: Dict[int, int] = {
            orphan.entity_id: orphan.entity_id for orphan in orphans
        }

        def find(x: int) -> int:
            if parent_map[x] != x:
                parent_map[x] = find(parent_map[x])
            return parent_map[x]

        def union(x: int, y: int) -> None:
            root_x = find(x)
            root_y = find(y)
            if root_x != root_y:
                parent_map[root_x] = root_y

        for orphan_list in mother_to_orphans.values():
            for i in range(len(orphan_list) - 1):
                union(orphan_list[i].entity_id, orphan_list[i + 1].entity_id)

        for orphan_list in father_to_orphans.values():
            for i in range(len(orphan_list) - 1):
                union(orphan_list[i].entity_id, orphan_list[i + 1].entity_id)

        for orphan_list in adoptive_to_orphans.values():
            for i in range(len(orphan_list) - 1):
                union(orphan_list[i].entity_id, orphan_list[i + 1].entity_id)

        groups: Dict[int, List[Person]] = {}
        for orphan in orphans:
            root = find(orphan.entity_id)
            if root not in groups:
                groups[root] = []
            groups[root].append(orphan)

        return list(groups.values())

    def _find_family_for_sibling_group(
        self,
        sibling_group: List[Person],
        eligible_parents: List[Person],
        min_age_diff: float,
        context: EnvironmentContext,
    ) -> Optional[Person]:
        """Busca la mejor familia que pueda adoptar a TODOS los hermanos."""
        group_size = len(sibling_group)
        valid_families: List[Person] = []

        for family in eligible_parents:
            available_slots = (
                self.config.adoptions.max_children_for_adoption - family.children_count
            )
            if available_slots < group_size:
                continue

            all_age_valid = all(
                (family.age - orphan.age) >= min_age_diff for orphan in sibling_group
            )
            if not all_age_valid:
                continue

            valid_families.append(family)

        if not valid_families:
            return None

        def family_suitability(family: Person) -> float:
            total_score = sum(
                self._calculate_suitability(family, orphan, self.ancestry_queries, context)
                for orphan in sibling_group
            )
            sibling_bonus = group_size * 50.0
            return total_score + sibling_bonus

        valid_families.sort(key=family_suitability, reverse=True)
        return valid_families[0]

    def _apply_parent_emotional_impact(
        self,
        parent: Person,
        partner: Optional[Person],
        children_count: int,
        is_group_adoption: bool,
        pending: PendingChanges,
    ) -> None:
        """Registra el impacto emocional en los padres adoptivos."""
        fw_cfg = self.config.free_will
        adopters = [parent]
        if partner is not None:
            adopters.append(partner)

        happiness_gain = (
            0.6 + (children_count * 0.1) if is_group_adoption else 0.5
        )
        stress_gain = 0.3 + (children_count * 0.15)
        energy_loss = 0.1 + (children_count * 0.05)

        for adopter in adopters:
            pending.register_emotion_update(
                adopter.entity_id, "happiness", happiness_gain
            )
            pending.register_emotion_update(adopter.entity_id, "stress", stress_gain)
            pending.register_emotion_update(
                adopter.entity_id, "energy", -energy_loss
            )

            if hasattr(adopter, "get_motivation"):
                pending.register_motivation_update(
                    adopter.entity_id,
                    "protection",
                    fw_cfg.success_reinforcement_rate,
                )
                pending.register_motivation_update(
                    adopter.entity_id,
                    "cooperation",
                    fw_cfg.success_reinforcement_rate * 0.7,
                )

    def _process_group_adoption(
        self,
        sibling_group: List[Person],
        new_parent: Person,
        state: WorldState,
        pending: PendingChanges,
        adopted_orphans: Set[int],
        current_day: float,
    ) -> None:
        """Procesa la adopción de un grupo completo de hermanos."""
        new_partner = None
        if new_parent.partner_id and new_parent.partner_id not in pending.deaths:
            new_partner = state.get_person_by_id(new_parent.partner_id)

        is_single_parent = new_partner is None
        context_str = "adopcion_grupal_familiar"

        if self.ancestry_queries and self.ancestry_queries.get_kinship_degree(
            new_parent.entity_id, sibling_group[0].entity_id
        ) == 0:
            context_str = "adopcion_grupal"

        for orphan in sibling_group:
            orphan.register_adoption_event(
                "adopted_by", new_parent.entity_id, current_day, context_str
            )
            new_parent.register_adoption_event(
                "adopted", orphan.entity_id, current_day, context_str
            )
            if new_partner:
                new_partner.register_adoption_event(
                    "adopted", orphan.entity_id, current_day, context_str
                )

            pending.register_adoption(
                child_id=orphan.entity_id,
                parent_a=new_parent.entity_id,
                parent_b=new_partner.entity_id if new_partner else None,
                is_single_parent=is_single_parent,
            )

            # HEX: Usar new_parent.q, new_parent.r en lugar de x, y
            pending.register_movement(
                orphan.entity_id, new_parent.q, new_parent.r
            )
            pending.register_memory_update(
                orphan.entity_id, "trauma_adoption", 0.7
            )
            pending.register_emotion_update(orphan.entity_id, "stress", 0.4)
            pending.register_emotion_update(orphan.entity_id, "happiness", -0.2)

            if self.relationship_engine:
                event_parent = _AdoptionRelationalEvent(
                    event_type=RelationshipEventType.CARE,
                    intensity=0.8,
                    context=context_str,
                )
                self.relationship_engine.process_event(
                    event_parent, new_parent, orphan, current_day
                )

                if new_partner:
                    event_partner = _AdoptionRelationalEvent(
                        event_type=RelationshipEventType.CARE,
                        intensity=0.8,
                        context=context_str,
                    )
                    self.relationship_engine.process_event(
                        event_partner, new_partner, orphan, current_day
                    )

            # INTEGRACIÓN CON MEMORIA EPISÓDICA
            CognitiveMemorySystem.add_memory(
                person=orphan,
                mem_type=CognitiveMemorySystem.TYPE_ADOPTION,
                target_id=str(new_parent.entity_id),
                intensity=0.7,
                valence=1,
                context=context_str,
                current_day=current_day,
                pending=pending,
            )

            CognitiveMemorySystem.add_memory(
                person=new_parent,
                mem_type=CognitiveMemorySystem.TYPE_ADOPTION,
                target_id=str(orphan.entity_id),
                intensity=0.8,
                valence=1,
                context=context_str,
                current_day=current_day,
                pending=pending,
            )

            if new_partner:
                CognitiveMemorySystem.add_memory(
                    person=new_partner,
                    mem_type=CognitiveMemorySystem.TYPE_ADOPTION,
                    target_id=str(orphan.entity_id),
                    intensity=0.8,
                    valence=1,
                    context=context_str,
                    current_day=current_day,
                    pending=pending,
                )

            adopted_orphans.add(orphan.entity_id)

        self._apply_parent_emotional_impact(
            parent=new_parent,
            partner=new_partner,
            children_count=len(sibling_group),
            is_group_adoption=True,
            pending=pending,
        )

        self.logger.info(
            "Adopción grupal registrada: %d hermanos asignados a familia %s%s",
            len(sibling_group),
            new_parent.entity_id,
            " (monoparental)" if is_single_parent else "",
        )

    def _process_individual_adoption(
        self,
        orphan: Person,
        eligible_parents: List[Person],
        min_age_diff: float,
        context: EnvironmentContext,
        state: WorldState,
        pending: PendingChanges,
        adopted_orphans: Set[int],
        current_day: float,
    ) -> None:
        """Procesa la adopción individual de un huérfano."""
        if not eligible_parents:
            return

        valid_candidates = [
            p for p in eligible_parents if (p.age - orphan.age) >= min_age_diff
        ]

        if not valid_candidates:
            return

        valid_candidates.sort(
            key=lambda p: self._calculate_suitability(
                p, orphan, self.ancestry_queries, context
            ),
            reverse=True,
        )

        new_parent = valid_candidates[0]
        eligible_parents.remove(new_parent)

        new_partner = None
        if new_parent.partner_id and new_parent.partner_id not in pending.deaths:
            new_partner = state.get_person_by_id(new_parent.partner_id)

        is_single_parent = new_partner is None
        context_str = "adopcion_familiar_cercana"

        if self.ancestry_queries and self.ancestry_queries.get_kinship_degree(
            new_parent.entity_id, orphan.entity_id
        ) == 0:
            context_str = "adopcion_individual"

        orphan.register_adoption_event(
            "adopted_by", new_parent.entity_id, current_day, context_str
        )
        new_parent.register_adoption_event(
            "adopted", orphan.entity_id, current_day, context_str
        )
        if new_partner:
            new_partner.register_adoption_event(
                "adopted", orphan.entity_id, current_day, context_str
            )

        pending.register_adoption(
            child_id=orphan.entity_id,
            parent_a=new_parent.entity_id,
            parent_b=new_partner.entity_id if new_partner else None,
            is_single_parent=is_single_parent,
        )

        # HEX: Usar new_parent.q, new_parent.r
        pending.register_movement(orphan.entity_id, new_parent.q, new_parent.r)
        pending.register_memory_update(orphan.entity_id, "trauma_adoption", 1.2)
        pending.register_emotion_update(orphan.entity_id, "stress", 0.7)
        pending.register_emotion_update(orphan.entity_id, "happiness", -0.6)

        if self.relationship_engine:
            event_parent = _AdoptionRelationalEvent(
                event_type=RelationshipEventType.CARE,
                intensity=0.7,
                context=context_str,
            )
            self.relationship_engine.process_event(
                event_parent, new_parent, orphan, current_day
            )

            if new_partner:
                event_partner = _AdoptionRelationalEvent(
                    event_type=RelationshipEventType.CARE,
                    intensity=0.7,
                    context=context_str,
                )
                self.relationship_engine.process_event(
                    event_partner, new_partner, orphan, current_day
                )

        # INTEGRACIÓN CON MEMORIA EPISÓDICA
        CognitiveMemorySystem.add_memory(
            person=orphan,
            mem_type=CognitiveMemorySystem.TYPE_ADOPTION,
            target_id=str(new_parent.entity_id),
            intensity=0.8,
            valence=1,
            context=context_str,
            current_day=current_day,
            pending=pending,
        )

        CognitiveMemorySystem.add_memory(
            person=new_parent,
            mem_type=CognitiveMemorySystem.TYPE_ADOPTION,
            target_id=str(orphan.entity_id),
            intensity=0.9,
            valence=1,
            context=context_str,
            current_day=current_day,
            pending=pending,
        )

        if new_partner:
            CognitiveMemorySystem.add_memory(
                person=new_partner,
                mem_type=CognitiveMemorySystem.TYPE_ADOPTION,
                target_id=str(orphan.entity_id),
                intensity=0.9,
                valence=1,
                context=context_str,
                current_day=current_day,
                pending=pending,
            )

        self._apply_parent_emotional_impact(
            parent=new_parent,
            partner=new_partner,
            children_count=1,
            is_group_adoption=False,
            pending=pending,
        )

        adopted_orphans.add(orphan.entity_id)

        self.logger.info(
            "Adopción individual: Menor %s -> Familia %s%s (Dif. Edad: %.1f días, Contexto: %s)",
            orphan.entity_id,
            new_parent.entity_id,
            " (monoparental)" if is_single_parent else "",
            (new_parent.age - orphan.age),
            context_str,
        )

    def _apply_abandonment_penalties(
        self,
        orphans: List[Person],
        adopted_orphans: Set[int],
        delta_days: float,
        pending: PendingChanges,
    ) -> None:
        """Registra el deterioro de huérfanos no adoptados."""
        adoptions_cfg = self.config.adoptions
        stress_rate = adoptions_cfg.abandonment_stress_rate
        happiness_rate = adoptions_cfg.abandonment_happiness_rate
        trauma_rate = adoptions_cfg.abandonment_trauma_rate

        for orphan in orphans:
            if orphan.entity_id in adopted_orphans:
                continue

            if orphan.entity_id in pending.memory_updates:
                current_trauma = pending.memory_updates[orphan.entity_id].get(
                    "trauma_abandonment",
                    orphan.memory.get("trauma_abandonment", 0.0),
                )
            else:
                current_trauma = orphan.memory.get("trauma_abandonment", 0.0)

            new_trauma = min(1.0, current_trauma + (trauma_rate * delta_days))
            pending.register_memory_update(
                orphan.entity_id, "trauma_abandonment", new_trauma
            )
            pending.register_emotion_update(
                orphan.entity_id, "stress", stress_rate * delta_days
            )
            pending.register_emotion_update(
                orphan.entity_id, "happiness", -happiness_rate * delta_days
            )

            if new_trauma > 0.5:
                self.logger.debug(
                    "Huérfano %s sufre abandono prolongado (Trauma: %.2f)",
                    orphan.entity_id,
                    new_trauma,
                )

    def _is_eligible_orphan(
        self,
        person: Person,
        state: WorldState,
        pending: PendingChanges,
        cfg: Any,
    ) -> bool:
        """Valida si un individuo cumple los requisitos para ser adoptable."""
        if person.entity_id in pending.deaths:
            return False

        if len(person.adoptive_parents) > 0:
            return False

        if person.age > cfg.max_orphan_age_days:
            return False

        father_alive = (
            person.father_id is not None
            and state.get_person_by_id(person.father_id) is not None
        )
        mother_alive = (
            person.mother_id is not None
            and state.get_person_by_id(person.mother_id) is not None
        )

        return (
            person.father_id is not None or person.mother_id is not None
        ) and not father_alive and not mother_alive

    def _calculate_suitability(
        self,
        parent: Person,
        orphan: Person,
        ancestry: Any,
        context: EnvironmentContext,
    ) -> float:
        """Calcula el índice de idoneidad de un adoptante (Utility AI).

        HEX: Usa distancia hexagonal en lugar de euclidiana.
        """
        score = 0.0
        cfg = self.config.adoptions

        # 1. Parentesco
        if ancestry is not None:
            kinship_degree = ancestry.get_kinship_degree(
                parent.entity_id, orphan.entity_id
            )
            if kinship_degree > 0:
                score += getattr(cfg, "kinship_weight", 100.0) / kinship_degree

        # 2. Distancia física
        # HEX: Usar distancia hexagonal en lugar de math.hypot
        distance = self._hex_distance(parent.q, parent.r, orphan.q, orphan.r)
        score -= distance * getattr(cfg, "distance_weight", 0.2)

        # 3. Presión local
        # HEX: Usar parent.q, parent.r
        local_pressure = context.get_local_pressure(parent.q, parent.r)
        score -= local_pressure * getattr(cfg, "pressure_weight", 50.0)

        # 4. Factores emocionales y de reputación
        stress = parent.emotions.get("stress", 0.0)
        happiness = parent.emotions.get("happiness", 0.5)
        reputation = getattr(parent, "reputation_score", 0.5)

        if stress > 0.7:
            score -= (stress - 0.7) * getattr(cfg, "stress_weight", 50.0)

        score += (happiness - 0.5) * getattr(cfg, "happiness_weight", 15.0)
        score += (reputation - 0.5) * 20.0

        # 5. Capacidad familiar
        current_children = parent.children_count
        score -= current_children * getattr(cfg, "children_count_weight", 5.0)

        previous_adoptions = len(parent.get_adoptions_as_parent())
        if previous_adoptions > 0:
            score -= previous_adoptions * 15.0

        # 6. Estabilidad relacional
        stability_years = parent.relationship_days / 365.0
        score += min(15.0, stability_years * getattr(cfg, "stability_weight", 1.5))

        # 7. Edad y estado del padre
        if parent.is_senior:
            score -= getattr(cfg, "senior_penalty", 10.0)

        age_ratio = orphan.age / cfg.max_orphan_age_days
        age_penalty = (
            age_ratio ** cfg.age_penalty_exponent
        ) * cfg.age_penalty_multiplier
        score -= age_penalty

        is_single_parent = (
            parent.marital_status in ("soltero", "viudo", "divorciado")
            and parent.partner_id is None
        )
        if is_single_parent:
            score -= cfg.single_parent_penalty

        # 8. Motivaciones
        if hasattr(parent, "get_motivation"):
            protection = parent.get_motivation("protection")
            cooperation = parent.get_motivation("cooperation")
            score += protection * getattr(cfg, "motivation_protection_weight", 25.0)
            score += cooperation * getattr(cfg, "motivation_cooperation_weight", 15.0)

        return score