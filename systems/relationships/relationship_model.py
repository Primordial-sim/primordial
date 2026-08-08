"""Modelo cognitivo de relaciones sociales. Fase 1: Evaluaciones Contextuales y Sesgos.

La memoria es la única fuente de verdad. Las variables emocionales se calculan 
bajo demanda. Se implementan narrativas asimétricas, sesgos cognitivos y 
evaluaciones contextuales.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Set, Tuple
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

@dataclass
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


@dataclass
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
            # Fórmula correcta de vida media
            decay = math.exp(-days_ago * math.log(2) / self.half_life_days)
            weight = self.personal_weight * decay
        
        self._cached_weight = weight
        self._cache_day = current_day
        return weight


@dataclass
class Narrative:
    """Narrativa que envejece (Fase 1, Punto 6)."""
    pattern: str
    strength: float
    last_confirmed: float
    half_life_days: float = 1825.0  # 5 años por defecto

    def current_strength(self, current_day: float) -> float:
        days_since_confirmation = current_day - self.last_confirmed
        # Fórmula correcta de vida media: decae al 50% exacto en half_life_days
        decay = math.exp(-days_since_confirmation * math.log(2) / self.half_life_days)
        return max(0.0, self.strength * decay)


@dataclass
class RelationshipKnowledge:
    owner_id: int
    partner_id: int
    observed_personality: Dict[str, float] = field(default_factory=dict)
    promises_kept: int = 0
    promises_broken: int = 0
    last_updated: float = 0.0
    # FASE 1: Objetivos del propietario que actúan como lentes
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
        
        self._cache_valid: bool = False
        self._cached_metrics: Dict[str, float] = {}
        self._cached_labels: List[str] = []  # FASE 1: Etiquetas como vistas
        
        self._dominant_memories: List[int] = []
        self._trauma_memories: List[int] = []
        self._anchor_memories: List[int] = []

        # FASE 1: Narrativas asimétricas (Punto 4)
        self.my_narratives: List[Narrative] = []
        
        # FASE 1: Estado para idealización post-mortem (Punto 7.5)
        self.partner_is_deceased: bool = False

        # ARCHIVADO
        self.archived_memories: List[PersonalMemory] = []
        self._last_archive_day: float = 0.0

        # LEGACY
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
        self._cache_valid = False
        
        if memory.role == MemoryRole.DOMINANT:
            self._dominant_memories.append(idx)
            self._keep_top_dominants()
        elif memory.role == MemoryRole.TRAUMA:
            self._trauma_memories.append(idx)
        elif memory.role == MemoryRole.ANCHOR:
            self._anchor_memories.append(idx)
            
        if memory.personal_weight > 70 or memory.category == MemoryCategory.LEGAL:
            memory.is_landmark = True

        # FASE 2: Actualización robusta e incremental de narrativas
        # Usamos memory.day como current_day si no se proporciona, para mantener la coherencia temporal
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
        # Ejemplo simplificado: detectar patrones de conflicto o cooperación
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
        
        # Si no existe, crearla
        self.my_narratives.append(Narrative(
            pattern=pattern,
            strength=strength_increment,
            last_confirmed=current_day
        ))

    # =========================================================================
    # ARCHIVADO DE RECUERDOS (Fase 0.1)
    # =========================================================================
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

    # =========================================================================
    # FASE 1: EVALUACIONES CONTEXTUALES Y ETIQUETAS
    # =========================================================================

    def _rebuild_cache(self, current_day: float) -> None:
        self._cached_metrics = {
            'familiarity': self._calc_familiarity(current_day),
            # Las demás métricas ahora son contextuales, pero mantenemos estas para compatibilidad legacy
            'trust': self._calc_trust(current_day),
            'attraction': self._calc_attraction(current_day),
        }
        # FASE 1: Etiquetas como vistas (Punto 2)
        self._cached_labels = LabelGenerator.generate(self, current_day)
        self._cache_valid = True

    def _ensure_cache(self, current_day: float) -> None:
        if not self._cache_valid:
            self._rebuild_cache(current_day)

    def get_labels(self, current_day: float) -> List[str]:
        self._ensure_cache(current_day)
        return self._cached_labels

    def get_familiarity(self, current_day: float) -> float:
        self._ensure_cache(current_day)
        return self._cached_metrics['familiarity']

    def _calc_familiarity(self, current_day: float) -> float:
        count_score = min(50.0, len(self.memories) * 0.5)
        time_score = min(50.0, (current_day - self.start_day) * 0.01)
        return min(100.0, count_score + time_score)

    def _calc_trust(self, current_day: float) -> float:
        # Legacy: suma simple para compatibilidad
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
    
    @staticmethod
    def apply_biases(memory: PersonalMemory, agent: Any, rel: Relationship, current_day: float) -> float:
        weight = memory.personal_weight
        context_lower = memory.context.lower()
        
        # 1. Sesgo de confirmación
        dominant_valence = 0.0
        if rel.my_narratives:
            pos_strength = sum(n.current_strength(current_day) for n in rel.my_narratives if any(w in n.pattern.lower() for w in ["ayuda", "confía", "conexión", "roca"]))
            neg_strength = sum(n.current_strength(current_day) for n in rel.my_narratives if any(w in n.pattern.lower() for w in ["falla", "traición", "tensión", "discutiendo"]))
            dominant_valence = 1.0 if pos_strength > neg_strength else -1.0
        
        if (memory.emotional_valence > 0 and dominant_valence > 0) or (memory.emotional_valence < 0 and dominant_valence < 0):
            confirmation_multiplier = 1.5
            # FASE 4: Contextos de alto impacto amplifican el sesgo de confirmación
            if any(word in context_lower for word in ["traicion", "sabotaje", "noche_romantica", "apoyo_incondicional", "confesion"]):
                confirmation_multiplier = 2.0
            weight *= confirmation_multiplier
            
        # 2. Efecto halo
        overall_impression = rel.get_familiarity(current_day) / 100.0
        if overall_impression > 0.7:
            weight *= 1.3 if memory.emotional_valence > 0 else 0.7
            
        # 3. Recencia
        days_ago = current_day - memory.day
        recency = math.exp(-days_ago / 365.0)
        weight *= (0.5 + recency * 0.5)
        
        # 4. Idealización post-mortem
        post_mortem_applied = False
        if rel.partner_is_deceased and memory.emotional_valence < 0:
            weight *= 0.3
            post_mortem_applied = True
        
        # 5. Negatividad
        if not post_mortem_applied and memory.emotional_valence < 0:
            negativity_multiplier = 1.8
            # FASE 4: Las traiciones en contextos específicos duelen significativamente más
            if any(word in context_lower for word in ["traicion", "sabotaje", "ataque_directo", "hostilidad"]):
                negativity_multiplier = 2.5
            weight *= negativity_multiplier
            
        return weight

class GoalFilter:
    """Objetivos como lentes que modifican la relevancia de un recuerdo (Punto 5)."""
    
    @staticmethod
    def relevance(goal: str, memory: PersonalMemory) -> float:
        goal_lower = goal.lower()
        
        # Ejemplos del documento de diseño
        if goal_lower == "proteger_hija" and memory.category in (MemoryCategory.FAMILY, MemoryCategory.SURVIVAL):
            return 3.0
        if goal_lower == "ser_independiente" and memory.category in (MemoryCategory.FAMILY, MemoryCategory.COOPERATION):
            return 0.5
            
        # Regla general: si el contexto del recuerdo menciona el objetivo, es relevante
        if goal_lower in memory.context.lower():
            return 2.0
            
        return 1.0


class RelationshipEvaluator:
    """Evaluaciones contextuales, no dimensiones fijas (Punto 1)."""
    
    @staticmethod
    def evaluate_reliability(rel: Relationship, context: str, current_day: float) -> float:
        # Activación parcial: solo evaluamos recuerdos relevantes para el contexto
        if context == "pedir_ayuda":
            target_categories = [MemoryCategory.COOPERATION, MemoryCategory.SURVIVAL, MemoryCategory.FAMILY]
            penalty_categories = [MemoryCategory.CONFLICT, MemoryCategory.TRAUMA]
            penalty_multiplier = 1.5
        elif context == "juego":
            target_categories = [MemoryCategory.SOCIAL, MemoryCategory.COOPERATION]
            penalty_categories = []  # Las traiciones son esperadas
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
    
    VALORES DE PRODUCCIÓN: Ajustados para que las etiquetas se alcancen 
    de forma orgánica tras varios meses/años de interacción consistente.
    """
    
    @staticmethod
    def generate(rel: Relationship, current_day: float) -> List[str]:
        labels = []
        
        # Calcular pesos totales por categoría
        romantic_weight = sum(mem.current_weight(current_day) for mem in rel.memories if mem.category == MemoryCategory.ROMANTIC)
        conflict_weight = sum(mem.current_weight(current_day) for mem in rel.memories if mem.category == MemoryCategory.CONFLICT)
        cooperation_weight = sum(mem.current_weight(current_day) for mem in rel.memories if mem.category == MemoryCategory.COOPERATION)
        family_weight = sum(mem.current_weight(current_day) for mem in rel.memories if mem.category == MemoryCategory.FAMILY)

        # --- UMBRALES DE PRODUCCIÓN ---
        
        # Relaciones Románticas
        if romantic_weight > 250:  # ~5-6 eventos románticos significativos
            labels.append("Amante")
        elif romantic_weight > 80:   # ~2 eventos románticos
            labels.append("Interés Romántico")
            
        # Relaciones de Conflicto
        if conflict_weight > 150:    # ~4-5 eventos de conflicto graves
            labels.append("Rival")
        if conflict_weight > 60 and cooperation_weight > 60:  # Relación compleja/competitiva
            labels.append("Rival Respetado")
            
        # Relaciones Positivas
        if cooperation_weight > 200 and conflict_weight < 100:  # ~4-5 eventos positivos, pocos negativos
            labels.append("Amigo")
        elif cooperation_weight > 80:  # ~2 eventos positivos sólidos
            labels.append("Aliado")
            
        # Relaciones Familiares
        if family_weight > 150:  # Lazos familiares fuertes
            labels.append("Familia Elegida")
            
        # Fallback
        if not labels:
            if len(rel.memories) > 0:
                labels.append("Conocido")
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