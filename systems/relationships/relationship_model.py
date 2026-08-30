"""Modelo cognitivo de relaciones sociales. Fase 1: Evaluaciones Contextuales y Sesgos.

La memoria es la única fuente de verdad. Las variables emocionales se calculan 
bajo demanda. Se implementan narrativas asimétricas, sesgos cognitivos y 
evaluaciones contextuales.

OPTIMIZACIÓN DE RENDIMIENTO:
- Caché de etiquetas separada de la caché de métricas
- get_labels() ahora retorna la caché si ya se calculó para el día actual
- add_memory() invalida la caché de etiquetas
- Contadores incrementales por categoría eliminan los sum() en LabelGenerator
- Uso de strings en lugar de enums para claves de dict (evita enum.__hash__)
- Eliminada la lógica automática de landmark en add_memory()
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Tuple
from systems.relationships.narrative_engine import NarrativeEngine


# =============================================================================
# ENUMS
# =============================================================================

class SexualOrientation(IntEnum):
    HETEROSEXUAL = 0
    MOSTLY_HETERO = 1
    BISEXUAL_HETERO = 2
    BISEXUAL = 3
    BISEXUAL_HOMO = 4
    MOSTLY_HOMO = 5
    HOMOSEXUAL = 6


class RelationshipStatus(Enum):
    UNKNOWN = "desconocido"
    ACQUAINTANCE = "conocido"
    FRIENDSHIP = "amistad"
    ROMANTIC_INTEREST = "interes_romantico"
    CASUAL = "relacion_esporadica"
    DATING = "noviazgo"
    COHABITATION = "convivencia"
    CONSOLIDATED = "relacion_larga_duracion"
    EX_PARTNER = "ex_pareja"


class RelationshipType(Enum):
    EXCLUSIVE = "exclusiva"
    CASUAL = "esporadica"
    OPEN = "abierta"


class RelationshipEventType(Enum):
    CARE = "care"
    COOPERATION = "cooperation"
    SHARE_RESOURCE = "share_resource"
    INTIMACY = "intimacy"
    RECONCILIATION = "reconciliation"
    COMPETITION = "competition"
    BETRAYAL = "betrayal"
    CONFLICT = "conflict"
    NEGLECT = "neglect"
    BIRTH = "birth"
    CHILD_DEATH = "child_death"
    PARTNER_DEATH = "partner_death"
    COHABITATION_START = "cohabitation_start"
    COHABITATION_END = "cohabitation_end"
    MET = "met"


class MemoryCategory(Enum):
    SOCIAL = "social"
    ROMANTIC = "romantic"
    FAMILY = "family"
    TRAUMA = "trauma"
    COOPERATION = "cooperation"
    CONFLICT = "conflict"
    SURVIVAL = "survival"
    LEGAL = "legal"


class MemoryRole(Enum):
    NORMAL = "normal"
    DOMINANT = "dominant"
    TRAUMA = "trauma"
    ANCHOR = "anchor"


# =============================================================================
# ESTRUCTURAS DE DATOS DE MEMORIA Y COGNICIÓN (Fase 1)
# =============================================================================

@dataclass(slots=True)
class WorldEvent:
    event_id: int
    event_type: str
    category: MemoryCategory
    day: float
    context: str
    source_system: str
    initiator_id: int
    target_id: int
    objective_intensity: float
    location: Optional[Tuple[int, int]] = None


@dataclass(slots=True)
class PersonalMemory:
    world_event_id: int
    owner_id: int
    partner_id: int
    
    perceived_intensity: float
    emotional_valence: float
    personal_weight: float
    
    category: MemoryCategory
    day: float
    context: str
    event_type: str
    source_system: str
    
    role: MemoryRole = MemoryRole.NORMAL
    is_landmark: bool = False
    importance: float = 0.5
    forgettable: bool = True
    half_life_days: float = 90.0
    
    _cached_weight: Optional[float] = field(default=None, repr=False)
    _cache_day: Optional[float] = field(default=None, repr=False)

    def current_weight(self, current_day: float) -> float:
        if self._cache_day == current_day:
            return self._cached_weight or self.personal_weight
        
        if self.is_landmark or self.role in (MemoryRole.TRAUMA, MemoryRole.ANCHOR):
            weight = self.personal_weight
        else:
            days_ago = current_day - self.day
            decay = math.exp(-days_ago * math.log(2) / self.half_life_days)
            weight = self.personal_weight * decay
        
        self._cached_weight = weight
        self._cache_day = current_day
        return weight


@dataclass(slots=True)
class Narrative:
    """Narrativa que envejece (Fase 1, Punto 6)."""
    pattern: str
    strength: float
    last_confirmed: float
    half_life_days: float = 1825.0

    def current_strength(self, current_day: float) -> float:
        days_since_confirmation = current_day - self.last_confirmed
        decay = math.exp(-days_since_confirmation * math.log(2) / self.half_life_days)
        return max(0.0, self.strength * decay)


@dataclass(slots=True)
class RelationshipKnowledge:
    owner_id: int
    partner_id: int
    observed_personality: Dict[str, float] = field(default_factory=dict)
    promises_kept: int = 0
    promises_broken: int = 0
    last_updated: float = 0.0
    owner_goals: List[str] = field(default_factory=list)


# =============================================================================
# CONTENEDOR DE RELACIÓN
# =============================================================================

class Relationship:
    def __init__(self, owner_id: int, partner_id: int, start_day: float):
        self.owner_id = owner_id
        self.partner_id = partner_id
        self.start_day = start_day
        
        self.memories: List[PersonalMemory] = []
        self.knowledge = RelationshipKnowledge(owner_id, partner_id)
        self.last_interaction_day: float = start_day
        
        self._idx_category: Dict[MemoryCategory, List[int]] = {}
        self._idx_type: Dict[str, List[int]] = {}
        self._idx_role: Dict[MemoryRole, List[int]] = {}
        
        # OPTIMIZACIÓN: Caché de métricas (trust, attraction, familiarity)
        self._cache_valid: bool = False
        self._cached_metrics: Dict[str, float] = {}
        
        # OPTIMIZACIÓN: Caché de etiquetas SEPARADA de la caché de métricas
        self._labels_cache_valid: bool = False
        self._cached_labels: List[str] = []
        self._labels_cache_day: float = -1.0
        
        # OPTIMIZACIÓN CRÍTICA: Contadores incrementales por categoría
        self._category_weights: Dict[str, float] = {cat.value: 0.0 for cat in MemoryCategory}
        self._category_weights_day: float = start_day
        
        self._dominant_memories: List[int] = []
        self._trauma_memories: List[int] = []
        self._anchor_memories: List[int] = []

        self.my_narratives: List[Narrative] = []
        self.partner_is_deceased: bool = False

        self.archived_memories: List[PersonalMemory] = []
        self._last_archive_day: float = 0.0

        self.status: RelationshipStatus = RelationshipStatus.UNKNOWN
        self.affinity: float = 0.5
        self.relationship_type: RelationshipType = RelationshipType.EXCLUSIVE
        self.shared_children: int = 0

    def add_memory(self, memory: PersonalMemory, current_day: float | None = None) -> None:
        idx = len(self.memories)
        self.memories.append(memory)
        
        self._idx_category.setdefault(memory.category, []).append(idx)
        self._idx_type.setdefault(memory.event_type, []).append(idx)
        self._idx_role.setdefault(memory.role, []).append(idx)
        
        self.last_interaction_day = max(self.last_interaction_day, memory.day)
        
        # OPTIMIZACIÓN: Invalidar AMBAS cachés cuando cambia una memoria
        self._cache_valid = False
        self._labels_cache_valid = False
        
        # OPTIMIZACIÓN CRÍTICA: Actualizar contador de categoría en O(1)
        # CORRECCIÓN: Usar string en lugar de enum para evitar enum.__hash__
        day = current_day if current_day is not None else memory.day
        weight = memory.current_weight(day)
        self._category_weights[memory.category.value] += weight
        self._category_weights_day = day
        
        if memory.role == MemoryRole.DOMINANT:
            self._dominant_memories.append(idx)
            self._keep_top_dominants()
        elif memory.role == MemoryRole.TRAUMA:
            self._trauma_memories.append(idx)
        elif memory.role == MemoryRole.ANCHOR:
            self._anchor_memories.append(idx)
        
        # CORRECCIÓN CRÍTICA: Eliminar la lógica automática de landmark.
        # La decisión de si una memoria es landmark debe tomarla el código que
        # crea la memoria, no el método que la añade.

        # FASE 2: Actualización robusta e incremental de narrativas
        confirmation_day = current_day if current_day is not None else memory.day
        NarrativeEngine.update_narratives(self, memory, confirmation_day)

    def _keep_top_dominants(self, max_dominants: int = 3) -> None:
        self._dominant_memories.sort(
            key=lambda i: self.memories[i].personal_weight * self.memories[i].perceived_intensity,
            reverse=True
        )
        for i in self._dominant_memories[max_dominants:]:
            self.memories[i].role = MemoryRole.NORMAL
        self._dominant_memories = self._dominant_memories[:max_dominants]

    def _update_narratives_incremental(self, new_memory: PersonalMemory) -> None:
        """Actualiza narrativas de forma O(1) cuando llega un nuevo recuerdo."""
        if new_memory.category == MemoryCategory.CONFLICT and new_memory.emotional_valence < 0:
            self._strengthen_or_create_narrative("Siempre me falla", new_memory.day, 0.2)
        elif new_memory.category == MemoryCategory.COOPERATION and new_memory.emotional_valence > 0:
            self._strengthen_or_create_narrative("Siempre me ayuda", new_memory.day, 0.15)

    def _strengthen_or_create_narrative(self, pattern: str, current_day: float, strength_increment: float) -> None:
        for narrative in self.my_narratives:
            if narrative.pattern == pattern:
                narrative.strength = min(1.0, narrative.strength + strength_increment)
                narrative.last_confirmed = current_day
                return
        
        self.my_narratives.append(Narrative(
            pattern=pattern,
            strength=strength_increment,
            last_confirmed=current_day
        ))

    def archive_old_memories(self, current_day: float, archive_age_days: float = 3650.0, min_weight_threshold: float = 5.0, archive_interval_days: float = 365.0) -> int:
        if current_day - self._last_archive_day < archive_interval_days:
            return 0
        self._last_archive_day = current_day
        
        to_archive: List[int] = []
        for i, mem in enumerate(self.memories):
            if mem.is_landmark or mem.role in (MemoryRole.TRAUMA, MemoryRole.ANCHOR, MemoryRole.DOMINANT) or not mem.forgettable:
                continue
            if current_day - mem.day > archive_age_days and mem.current_weight(current_day) < min_weight_threshold:
                to_archive.append(i)
        
        if not to_archive:
            return 0
        
        for i in sorted(to_archive, reverse=True):
            self.archived_memories.append(self.memories.pop(i))
        
        self._rebuild_indices()
        self._cache_valid = False
        self._labels_cache_valid = False
        self._rebuild_category_weights(current_day)
        return len(to_archive)

    def _rebuild_indices(self) -> None:
        self._idx_category.clear()
        self._idx_type.clear()
        self._idx_role.clear()
        self._dominant_memories.clear()
        self._trauma_memories.clear()
        self._anchor_memories.clear()
        
        for i, mem in enumerate(self.memories):
            self._idx_category.setdefault(mem.category, []).append(i)
            self._idx_type.setdefault(mem.event_type, []).append(i)
            self._idx_role.setdefault(mem.role, []).append(i)
            if mem.role == MemoryRole.DOMINANT: self._dominant_memories.append(i)
            elif mem.role == MemoryRole.TRAUMA: self._trauma_memories.append(i)
            elif mem.role == MemoryRole.ANCHOR: self._anchor_memories.append(i)

    def _rebuild_category_weights(self, current_day: float) -> None:
        """Reconstruye los contadores de categoría desde cero.
        
        CORRECCIÓN: Usar strings en lugar de enums para evitar enum.__hash__
        """
        for cat in MemoryCategory:
            self._category_weights[cat.value] = 0.0
        
        for mem in self.memories:
            weight = mem.current_weight(current_day)
            self._category_weights[mem.category.value] += weight
        
        self._category_weights_day = current_day

    def _rebuild_cache(self, current_day: float) -> None:
        self._cached_metrics = {
            'familiarity': self._calc_familiarity(current_day),
            'trust': self._calc_trust(current_day),
            'attraction': self._calc_attraction(current_day),
        }
        self._cache_valid = True

    def _ensure_cache(self, current_day: float) -> None:
        if not self._cache_valid:
            self._rebuild_cache(current_day)

    def get_labels(self, current_day: float, owner: Any = None) -> List[str]:
        """Retorna las etiquetas de la relación.
        
        OPTIMIZACIÓN: Si las etiquetas ya se calcularon para el día actual,
        retorna la caché sin recalcular. Usa contadores incrementales para
        evitar los 4 sum() en LabelGenerator.generate().
        
        GENÉTICA UNIVERSAL: Acepta owner para filtrar etiquetas por capacidades.
        
        Args:
            current_day: Día actual de la simulación.
            owner: El agente dueño de la relación (para consultar capacidades).
        """
        if self._labels_cache_valid and self._labels_cache_day == current_day:
            return self._cached_labels
        
        # Actualizar contadores si han pasado más de 30 días
        if current_day - self._category_weights_day > 30.0:
            self._rebuild_category_weights(current_day)
        
        self._cached_labels = LabelGenerator.generate(self, current_day, owner)
        self._labels_cache_valid = True
        self._labels_cache_day = current_day
        return self._cached_labels

    def get_familiarity(self, current_day: float) -> float:
        self._ensure_cache(current_day)
        return self._cached_metrics['familiarity']

    def _calc_familiarity(self, current_day: float) -> float:
        count_score = min(50.0, len(self.memories) * 0.5)
        time_score = min(50.0, (current_day - self.start_day) * 0.01)
        return min(100.0, count_score + time_score)

    def _calc_trust(self, current_day: float) -> float:
        total = 0.0
        for mem in self.memories:
            w = mem.current_weight(current_day)
            if mem.category in (MemoryCategory.COOPERATION, MemoryCategory.SURVIVAL, MemoryCategory.SOCIAL):
                total += w * max(0, mem.emotional_valence)
            elif mem.category == MemoryCategory.CONFLICT:
                total -= w * abs(mem.emotional_valence) * 0.6
        return max(0.0, min(100.0, total))

    def _calc_attraction(self, current_day: float) -> float:
        total = 0.0
        for mem in self.memories:
            if mem.category == MemoryCategory.ROMANTIC:
                total += mem.current_weight(current_day) * max(0, mem.emotional_valence)
        return max(0.0, min(100.0, total))

    def count_memories(self, categories: Optional[List[MemoryCategory]] = None, min_weight: float = 0.0, current_day: Optional[float] = None) -> int:
        indices = []
        if categories:
            for cat in categories:
                indices.extend(self._idx_category.get(cat, []))
        else:
            indices = range(len(self.memories))
            
        count = 0
        day = current_day or self.last_interaction_day
        for i in set(indices):
            if self.memories[i].current_weight(day) >= min_weight:
                count += 1
        return count

    def has_event_type(self, event_type: str) -> bool:
        return len(self._idx_type.get(event_type, [])) > 0


# =============================================================================
# FASE 1: MOTORES COGNITIVOS Y DE EXPRESIÓN
# =============================================================================

class BiasEngine:
    """Aplica sesgos cognitivos al peso de un recuerdo (Fase 1 + Fase 4: Contextos)."""
    
    _CONFIRMATION_KEYWORDS = frozenset(["traicion", "sabotaje", "noche_romantica", "apoyo_incondicional", "confesion"])
    _NEGATIVITY_KEYWORDS = frozenset(["traicion", "sabotaje", "ataque_directo", "hostilidad"])
    _POSITIVE_NARRATIVE_KEYWORDS = frozenset(["ayuda", "confía", "conexión", "roca"])
    _NEGATIVE_NARRATIVE_KEYWORDS = frozenset(["falla", "traición", "tensión", "discutiendo"])
    
    @staticmethod
    def apply_biases(memory: PersonalMemory, agent: Any, rel: Relationship, current_day: float) -> float:
        weight = memory.personal_weight
        context_lower = memory.context.lower()
        
        dominant_valence = 0.0
        if rel.my_narratives:
            pos_strength = sum(n.current_strength(current_day) for n in rel.my_narratives if any(w in n.pattern.lower() for w in BiasEngine._POSITIVE_NARRATIVE_KEYWORDS))
            neg_strength = sum(n.current_strength(current_day) for n in rel.my_narratives if any(w in n.pattern.lower() for w in BiasEngine._NEGATIVE_NARRATIVE_KEYWORDS))
            dominant_valence = 1.0 if pos_strength > neg_strength else -1.0
        
        if (memory.emotional_valence > 0 and dominant_valence > 0) or (memory.emotional_valence < 0 and dominant_valence < 0):
            confirmation_multiplier = 1.5
            if any(word in context_lower for word in BiasEngine._CONFIRMATION_KEYWORDS):
                confirmation_multiplier = 2.0
            weight *= confirmation_multiplier
            
        overall_impression = rel.get_familiarity(current_day) / 100.0
        if overall_impression > 0.7:
            weight *= 1.3 if memory.emotional_valence > 0 else 0.7
            
        days_ago = current_day - memory.day
        recency = math.exp(-days_ago / 365.0)
        weight *= (0.5 + recency * 0.5)
        
        post_mortem_applied = False
        if rel.partner_is_deceased and memory.emotional_valence < 0:
            weight *= 0.3
            post_mortem_applied = True
        
        if not post_mortem_applied and memory.emotional_valence < 0:
            negativity_multiplier = 1.8
            if any(word in context_lower for word in BiasEngine._NEGATIVITY_KEYWORDS):
                negativity_multiplier = 2.5
            weight *= negativity_multiplier
            
        return weight

class GoalFilter:
    """Objetivos como lentes que modifican la relevancia de un recuerdo (Punto 5)."""
    
    @staticmethod
    def relevance(goal: str, memory: PersonalMemory) -> float:
        goal_lower = goal.lower()
        
        if goal_lower == "proteger_hija" and memory.category in (MemoryCategory.FAMILY, MemoryCategory.SURVIVAL):
            return 3.0
        if goal_lower == "ser_independiente" and memory.category in (MemoryCategory.FAMILY, MemoryCategory.COOPERATION):
            return 0.5
            
        if goal_lower in memory.context.lower():
            return 2.0
            
        return 1.0


class RelationshipEvaluator:
    """Evaluaciones contextuales, no dimensiones fijas (Punto 1)."""
    
    @staticmethod
    def evaluate_reliability(rel: Relationship, context: str, current_day: float) -> float:
        if context == "pedir_ayuda":
            target_categories = [MemoryCategory.COOPERATION, MemoryCategory.SURVIVAL, MemoryCategory.FAMILY]
            penalty_categories = [MemoryCategory.CONFLICT, MemoryCategory.TRAUMA]
            penalty_multiplier = 1.5
        elif context == "juego":
            target_categories = [MemoryCategory.SOCIAL, MemoryCategory.COOPERATION]
            penalty_categories = []
            penalty_multiplier = 0.5
        else:
            target_categories = [MemoryCategory.COOPERATION, MemoryCategory.SOCIAL]
            penalty_categories = [MemoryCategory.CONFLICT]
            penalty_multiplier = 1.0

        score = 0.0
        for mem in rel.memories:
            w = mem.current_weight(current_day)
            if mem.category in target_categories:
                score += w * max(0, mem.emotional_valence)
            elif mem.category in penalty_categories:
                score -= w * abs(mem.emotional_valence) * penalty_multiplier
        
        return max(0.0, min(100.0, score))


class LabelGenerator:
    """Etiquetas como vistas, no estado. Basado en pesos, no conteos (Puntos 2 y 3).
    
    OPTIMIZACIÓN CRÍTICA: Usa contadores incrementales precalculados en Relationship
    en lugar de hacer 4 sum() sobre todas las memorias.
    Reduce complejidad de O(N) a O(1) donde N es el número de memorias.
    
    CORRECCIÓN: Usar strings en lugar de enums para evitar enum.__hash__
    
    GENÉTICA UNIVERSAL: Filtra etiquetas según SocialCapabilities del organismo.
    """
    
    @staticmethod
    def generate(rel: Relationship, current_day: float, owner: Any = None) -> List[str]:
        """Genera etiquetas relacionales filtradas por capacidades sociales.
        
        Args:
            rel: La relación a evaluar.
            current_day: Día actual de la simulación.
            owner: El agente dueño de la relación (para consultar capacidades).
                   Si es None, usa comportamiento legacy (todas las etiquetas).
        """
        labels = []
        
        # GENÉTICA UNIVERSAL: Consultar capacidades sociales si tenemos el owner
        social_caps = None
        if owner is not None and hasattr(owner, 'genome'):
            from systems.relationships.social_capabilities import SocialCapabilities
            social_caps = SocialCapabilities.from_genome(owner.genome)
        
        # OPTIMIZACIÓN CRÍTICA: Leer contadores precalculados en O(1)
        romantic_weight = rel._category_weights["romantic"]
        conflict_weight = rel._category_weights["conflict"]
        cooperation_weight = rel._category_weights["cooperation"]
        family_weight = rel._category_weights["family"]

        # --- UMBRALES DE PRODUCCIÓN ---
        
        # Etiquetas románticas (requieren romantic_bonds)
        if social_caps is None or social_caps.can_have_romantic_bonds:
            if romantic_weight > 250:
                labels.append("Amante")
            elif romantic_weight > 80:
                labels.append("Interés Romántico")
        
        # Etiquetas de conflicto (requieren can_form_conflict)
        if social_caps is None or social_caps.can_form_conflict:
            if conflict_weight > 150:
                labels.append("Rival")
            if conflict_weight > 60 and cooperation_weight > 60:
                labels.append("Rival Respetado")
        
        # Etiquetas de amistad (requieren friendship)
        if social_caps is None or social_caps.can_have_friendship:
            if cooperation_weight > 200 and conflict_weight < 100:
                labels.append("Amigo")
        
        # Etiquetas de alianza (requieren cooperation)
        if social_caps is None or social_caps.can_form_cooperation:
            if cooperation_weight > 80 and "Amigo" not in labels:
                labels.append("Aliado")
        
        # Etiquetas de familia (requieren family_bonds)
        if social_caps is None or social_caps.can_form_family_bonds:
            if family_weight > 150:
                labels.append("Familia Elegida")
        
        # Etiquetas básicas
        if not labels:
            if len(rel.memories) > 0:
                # "Conocido" requiere reconocimiento individual
                if social_caps is None or social_caps.can_recognize_individuals:
                    labels.append("Conocido")
                else:
                    labels.append("Desconocido")
            else:
                labels.append("Desconocido")
                
        return labels


# =============================================================================
# FUNCIONES DE UTILIDAD (Compatibilidad)
# =============================================================================

def is_orientation_compatible(o1: SexualOrientation, o2: SexualOrientation, tolerance: float = 1.5) -> float:
    diff = abs(o1.value - o2.value)
    if (o1 == SexualOrientation.HETEROSEXUAL and o2 == SexualOrientation.HOMOSEXUAL) or \
       (o1 == SexualOrientation.HOMOSEXUAL and o2 == SexualOrientation.HETEROSEXUAL):
        return 0.0
    if diff > 6.0:
        return 0.0
    return max(0.0, 1.0 - (diff / (tolerance + 3.0)))