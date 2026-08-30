"""Módulo de formación de parejas basado en el sistema emergente de memorias.

NO usa estados lineales (interes_romantico, noviazgo, etc.).
En su lugar:
- Busca candidatos compatibles
- Genera un evento INTIMACY que el RelationshipExperienceEngine procesa
- La etiqueta "Amante" emerge naturalmente de memorias INTIMACY acumuladas
- La monogamia se verifica mediante etiquetas activas

OPTIMIZACIÓN DE RENDIMIENTO:
- Caché de _has_romantic_partner por tick (reduce llamadas a get_labels)
- Limpieza de caché al inicio de cada tick
"""

from __future__ import annotations

import logging
import math
import random
from typing import Any, Dict

from core.config.simulation_config import SimulationConfig
from core.state.pending_changes import PendingChanges
from core.state.world_state import WorldState
from systems.environment.environment_context import EnvironmentContext
from systems.relationships.relationship_model import (
    RelationshipEventType,
    SexualOrientation,
)


class MarriageSystem:
    """Genera eventos de intimidad que llevan a relaciones emergentes."""

    def __init__(
        self,
        config: SimulationConfig,
        compatibility_engine: Any = None,
        relationship_engine: Any = None,
    ) -> None:
        self.config = config
        self.compatibility_engine = compatibility_engine
        self.relationship_engine = relationship_engine
        self.logger = logging.getLogger(self.__class__.__name__)

        self.search_radius = getattr(config.reproduction, 'partner_search_radius', 20.0)
        self.widowhood_duration = getattr(config.reproduction, 'widowhood_duration_days', 365.0)
        self.intimacy_cooldown = getattr(config.reproduction, 'intimacy_cooldown_days', 30.0)
        
        # OPTIMIZACIÓN: Caché de parejas románticas por tick
        self._romantic_partner_cache: Dict[int, bool] = {}

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Procesa intentos de intimidad entre agentes compatibles."""
        current_day = getattr(state, 'world_days_elapsed', 0.0)
        all_persons = state.get_all_persons()

        # OPTIMIZACIÓN: Limpiar caché al inicio de cada tick
        self._romantic_partner_cache.clear()

        for person in all_persons:
            if person.entity_id in pending.deaths:
                continue
            
            # GENÉTICA UNIVERSAL: Solo procesar si puede formar vínculos románticos
            from systems.relationships.social_capabilities import SocialCapabilities
            social_caps = SocialCapabilities.from_genome(person.genome)
            if not social_caps.can_have_romantic_bonds:
                continue
            
            if not getattr(person, 'is_adult', False):
                continue
            if getattr(person, 'is_pregnant', False):
                continue
            if self._is_in_mourning(person, current_day):
                continue
            if self._has_romantic_partner(person, current_day):
                continue

            candidates = self._find_candidates(person, all_persons, pending, current_day)
            if not candidates:
                continue

            partner = self._select_best(person, candidates, current_day)
            if partner is None:
                continue

            self._generate_intimacy_event(person, partner, current_day)

    # ------------------------------------------------------------------
    # FILTROS
    # ------------------------------------------------------------------

    def _is_in_mourning(self, person: Any, current_day: float) -> bool:
        memory = getattr(person, 'memory', None)
        if isinstance(memory, dict):
            widowhood_day = memory.get("widowhood_day", 0.0)
            if widowhood_day > 0 and (current_day - widowhood_day) < self.widowhood_duration:
                return True
        return getattr(person, 'marital_status', 'soltero') == 'viudo'

    def _has_romantic_partner(self, person: Any, current_day: float) -> bool:
        """Verifica monogamia usando etiquetas emergentes.
    
        OPTIMIZACIÓN: Usa caché por tick para evitar llamadas repetidas
        a get_labels() para el mismo agente.
    
        CORRECCIÓN: _relationships es ahora Dict[int, Relationship],
        hay que usar .values() para iterar sobre los objetos Relationship.
        """
        cache_key = person.entity_id
        if cache_key in self._romantic_partner_cache:
            return self._romantic_partner_cache[cache_key]
    
        result = False
        if hasattr(person, '_relationships') and person._relationships:
            romantic_labels = {"Amante", "Interés Romántico"}
            # CORRECCIÓN CRÍTICA: usar .values() porque _relationships es ahora un Dict
            for rel in person._relationships.values():
                if not hasattr(rel, 'get_labels'):
                    continue
                labels = rel.get_labels(current_day)
                if romantic_labels.intersection(labels):
                    result = True
                    break
    
        self._romantic_partner_cache[cache_key] = result
        return result

    # ------------------------------------------------------------------
    # BÚSQUEDA
    # ------------------------------------------------------------------

    def _find_candidates(self, person, all_persons, pending, current_day):
        candidates = []
        orientation = getattr(person, 'sexual_orientation', SexualOrientation.HETEROSEXUAL)
        gender = getattr(person, 'gender', 'M')

        for other in all_persons:
            if other.entity_id == person.entity_id:
                continue
            if other.entity_id in pending.deaths:
                continue
            if not getattr(other, 'is_adult', False):
                continue
            if getattr(other, 'is_pregnant', False):
                continue
            if self._has_romantic_partner(other, current_day):
                continue

            dist = math.hypot(person.x - other.x, person.y - other.y)
            if dist > self.search_radius:
                continue

            if not self._orientation_compatible(orientation, gender, getattr(other, 'gender', 'F')):
                continue

            if self._is_close_relative(person, other):
                continue

            candidates.append(other)

        return candidates

    def _orientation_compatible(self, orientation, seeker_gender, other_gender) -> bool:
        same = seeker_gender == other_gender
        if orientation == SexualOrientation.HETEROSEXUAL:
            return not same
        if orientation == SexualOrientation.HOMOSEXUAL:
            return same
        if orientation == SexualOrientation.BISEXUAL:
            return True
        if orientation == SexualOrientation.MOSTLY_HETERO:
            return (not same) or (random.random() < 0.1)
        if orientation == SexualOrientation.MOSTLY_HOMO:
            return same or (random.random() < 0.1)
        if orientation == SexualOrientation.BISEXUAL_HETERO:
            return (not same) or (random.random() < 0.3)
        if orientation == SexualOrientation.BISEXUAL_HOMO:
            return same or (random.random() < 0.3)
        return not same

    def _is_close_relative(self, a, b) -> bool:
        if b.entity_id in getattr(a, 'parents', []):
            return True
        if a.entity_id in getattr(b, 'parents', []):
            return True
        am = getattr(a, 'mother_id', None)
        af = getattr(a, 'father_id', None)
        bm = getattr(b, 'mother_id', None)
        bf = getattr(b, 'father_id', None)
        if am and am == bm:
            return True
        if af and af == bf:
            return True
        return False

    # ------------------------------------------------------------------
    # SELECCIÓN
    # ------------------------------------------------------------------

    def _select_best(self, person, candidates, current_day):
        if not candidates:
            return None

        if self.compatibility_engine is None:
            return random.choice(candidates)

        best = None
        best_score = -1.0
        for c in candidates:
            score = self.compatibility_engine.calculate_compatibility(person, c, current_day)
            dist = math.hypot(person.x - c.x, person.y - c.y)
            score -= (dist / self.search_radius) * 0.2
            score += (person.entity_id % 100) / 10000.0
            if score > best_score:
                best_score = score
                best = c
        return best

    # ------------------------------------------------------------------
    # EVENTO DE INTIMIDAD
    # ------------------------------------------------------------------

    def _generate_intimacy_event(self, person, partner, current_day):
        """Genera un evento INTIMACY que el RelationshipExperienceEngine procesa."""
        if self.relationship_engine is None:
            return

        intensity = random.uniform(0.4, 0.8)

        event = _IntimacyEvent(intensity=intensity)

        self.relationship_engine.process_event(event, person, partner, current_day)

        self.logger.debug(
            "💕 Agente %s y %s: evento de intimidad (%.2f)",
            person.entity_id, partner.entity_id, intensity,
        )


class _IntimacyEvent:
    """Evento ligero compatible con RelationshipExperienceEngine."""
    event_type = RelationshipEventType.INTIMACY

    __slots__ = ('intensity', 'context')

    def __init__(self, intensity: float):
        self.intensity = intensity
        self.context = "intimidad_romantica"