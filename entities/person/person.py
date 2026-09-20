"""Módulo de la entidad biológica y social principal.

OPTIMIZACIONES APLICADAS:
- entity_id, x, y son ahora atributos directos (no properties)
- _relationships es ahora Dict[int, Relationship] para búsqueda O(1)
- _get_active_relationships() con caché
- Property 'relationships' retorna lista bajo demanda para compatibilidad

SISTEMA DE ENERGÍA:
- _energy y _max_energy gestionan el nivel de energía del organismo
- La energía se gana por alimentación (según dieta) y se gasta por metabolismo
- Si la energía llega a 0, el organismo entra en estado de inanición
- _starvation_days rastrea cuánto tiempo lleva sin energía
"""

from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Tuple

from core.config.simulation_config import SimulationConfig
from entities.person.genome import Genome
from systems.diseases.pathogen import Pathogen, InfectionState, InfectionPhase
from systems.relationships.relationship_model import (
    Relationship,
    RelationshipStatus,
    RelationshipType,
    SexualOrientation,
)


class Person:
    def __init__(
        self,
        config: SimulationConfig,
        entity_id: int,
        x: int,
        y: int,
        age: float = 0.0,
        genome: Optional[Genome] = None,
        gender: Optional[str] = None,
        species: str = "human",
    ) -> None:
        self._config = config
        self.entity_id = entity_id
        self._species = species

        self.x = x
        self.y = y
        self._age = age
        self._gender = gender if gender else random.choice(["M", "F"])
        self._genome = genome if genome else Genome(species_baseline=species)

        self._health_state = "sano"
        self._is_adult = False
        self._is_senior = False

        # Sistema de energía
        self._max_energy: float = 100.0  # Energía máxima
        self._energy: float = 100.0      # Energía actual (empieza llena)
        self._starvation_days: float = 0.0  # Días sin energía

        self._active_infections: Dict[str, InfectionState] = {}
        self._immune_memory: Dict[str, float] = {}
        self._strain_immunity: Dict[str, float] = {}
        self._strain_metadata: Dict[str, dict] = {}

        self._is_pregnant = False
        self._pregnancy_days = 0.0
        self._failed_pregnancies = 0

        self._children_count = 0
        self._biological_children_count = 0
        self._litter_size_gestating = 1

        self._mother_id: Optional[int] = None
        self._father_id: Optional[int] = None
        self._parents: List[int] = []
        self._adoptive_parents: List[int] = []

        self._adoption_history: List[Dict[str, Any]] = []
        self._reputation_score: float = 0.5

        self._memory: Dict[str, Any] = {
            "trauma_overcrowding": 0.0,
            "trauma_sickness": 0.0,
            "preferred_sector": None,
            "rebellion_cooldown": 0.0,
        }

        self._emotions: Dict[str, float] = {
            "stress": 0.0,
            "happiness": 0.8,
            "energy": 1.0,
        }

        self._motivations: Dict[str, float] = {
            "independence": 0.3,
            "exploration": 0.3,
            "rebellion": 0.2,
            "partnership": 0.5,
            "protection": 0.4,
            "migration": 0.2,
            "cooperation": 0.5,
            "fertility_desire": 0.5,
        }

        self._sexual_orientation: SexualOrientation = self._generate_orientation()
        
        # OPTIMIZACIÓN CRÍTICA: Dict en lugar de List para búsqueda O(1)
        # La clave es partner_id, el valor es el Relationship
        self._relationships: Dict[int, Relationship] = {}
        
        self._partner_id: Optional[int] = None
        self._marital_status: str = "soltero"
        
        # NUEVO: Núcleo residencial al que pertenece el agente
        self.nucleus_id: Optional[int] = None

        self._active_relationships_cache: Optional[List[Relationship]] = None
        self._relationships_cache_dirty: bool = True

        self._check_milestones()

    def _generate_orientation(self) -> SexualOrientation:
        roll = random.random()
        if roll < 0.65: return SexualOrientation.HETEROSEXUAL
        elif roll < 0.80: return SexualOrientation.MOSTLY_HETERO
        elif roll < 0.85: return SexualOrientation.BISEXUAL_HETERO
        elif roll < 0.88: return SexualOrientation.BISEXUAL
        elif roll < 0.90: return SexualOrientation.BISEXUAL_HOMO
        elif roll < 0.95: return SexualOrientation.MOSTLY_HOMO
        else: return SexualOrientation.HOMOSEXUAL

    # ==========================================
    # PROPIEDADES BÁSICAS
    # ==========================================
    @property
    def species(self) -> str: return self._species
    @property
    def age(self) -> float: return self._age
    @property
    def gender(self) -> str: return self._gender
    @property
    def health_state(self) -> str: return self._health_state
    @property
    def genome(self) -> Genome: return self._genome
    @property
    def is_adult(self) -> bool: return self._is_adult
    @property
    def is_senior(self) -> bool: return self._is_senior
    @property
    def is_pregnant(self) -> bool: return self._is_pregnant
    @property
    def children_count(self) -> int: return self._children_count
    @property
    def biological_children_count(self) -> int: return self._biological_children_count
    @property
    def parents(self) -> List[int]: return self._parents
    @property
    def adoptive_parents(self) -> List[int]: return self._adoptive_parents
    @property
    def mother_id(self) -> Optional[int]: return self._mother_id
    @property
    def father_id(self) -> Optional[int]: return self._father_id
    @property
    def pregnancy_days(self) -> float: return float(self._pregnancy_days)
    @property
    def litter_size_gestating(self) -> int: return self._litter_size_gestating
    @property
    def memory(self) -> Dict[str, Any]: return self._memory
    @property
    def emotions(self) -> Dict[str, float]: return self._emotions
    @property
    def motivations(self) -> Dict[str, float]: return self._motivations
    @property
    def active_pathogens(self) -> Dict[str, Pathogen]:
        return {pid: state.pathogen for pid, state in self._active_infections.items()}
    @property
    def active_infections(self) -> Dict[str, InfectionState]: return self._active_infections
    @property
    def is_sick(self) -> bool: return len(self._active_infections) > 0
    @property
    def is_symptomatic(self) -> bool:
        return any(state.phase == InfectionPhase.SYMPTOMATIC for state in self._active_infections.values())
    @property
    def effective_sociability(self) -> float:
        base = self._genome.sociability
        stress_penalty = self._emotions["stress"] * 0.4
        happiness_bonus = (self._emotions["happiness"] - 0.5) * 0.2
        return max(0.1, min(2.0, base - stress_penalty + happiness_bonus))
    @property
    def effective_temperament(self) -> float:
        base = self._genome.temperament
        trauma = min(1.0, self._memory.get("trauma_sickness", 0.0) + self._memory.get("trauma_overcrowding", 0.0))
        return max(0.1, min(2.0, base - (trauma * 0.5)))
    @property
    def sexual_orientation(self) -> SexualOrientation: return self._sexual_orientation
    
    # OPTIMIZACIÓN: Property que retorna lista para compatibilidad hacia atrás
    @property
    def relationships(self) -> List[Relationship]:
        return list(self._relationships.values())

    @property
    def adoption_history(self) -> List[Dict[str, Any]]:
        return self._adoption_history

    @property
    def parental_status(self) -> str:
        adopted_count = self._children_count - self._biological_children_count
        if self._children_count == 0: return "sin_hijos"
        elif self._biological_children_count > 0 and adopted_count == 0: return "padre_biologico"
        elif self._biological_children_count == 0 and adopted_count > 0: return "padre_adoptivo"
        else: return "padre_mixto"

    @property
    def reputation_score(self) -> float:
        return self._reputation_score

    @property
    def adopted_children_count(self) -> int:
        return max(0, self._children_count - self._biological_children_count)

    @property
    def partner_id(self) -> Optional[int]:
        active = self._get_active_relationships()
        if not active: return self._partner_id
        priority = [RelationshipStatus.CONSOLIDATED, RelationshipStatus.COHABITATION, 
                    RelationshipStatus.DATING, RelationshipStatus.CASUAL, 
                    RelationshipStatus.ROMANTIC_INTEREST]
        for status in priority:
            for rel in active:
                if getattr(rel, 'status', None) == status: return rel.partner_id
        return active[0].partner_id if active else self._partner_id

    @property
    def marital_status(self) -> str:
        active = self._get_active_relationships()
        if not active: return self._marital_status
        priority = [RelationshipStatus.CONSOLIDATED, RelationshipStatus.COHABITATION, 
                    RelationshipStatus.DATING, RelationshipStatus.ROMANTIC_INTEREST]
        for status in priority:
            for rel in active:
                if getattr(rel, 'status', None) == status: return "casado"
        for rel in self._relationships.values():
            if getattr(rel, 'status', None) == RelationshipStatus.EX_PARTNER: return "divorciado"
        return "soltero"

    @property
    def relationship_days(self) -> float:
        active = self._get_active_relationships()
        if not active: return 0.0
        priority = [RelationshipStatus.CONSOLIDATED, RelationshipStatus.COHABITATION, RelationshipStatus.DATING]
        for status in priority:
            for rel in active:
                if getattr(rel, 'status', None) == status: 
                    return getattr(rel, 'last_interaction_day', 0.0) - getattr(rel, 'start_day', 0.0)
        return 0.0

    @property
    def has_nucleus(self) -> bool:
        """Verifica si el agente pertenece a un núcleo residencial."""
        return self.nucleus_id is not None

    # ==========================================
    # PROPIEDADES DE ENERGÍA
    # ==========================================

    @property
    def energy(self) -> float:
        """Nivel de energía actual del organismo."""
        return self._energy

    @property
    def max_energy(self) -> float:
        """Nivel máximo de energía del organismo."""
        return self._max_energy

    @property
    def energy_ratio(self) -> float:
        """Proporción de energía actual respecto al máximo (0.0 a 1.0)."""
        if self._max_energy <= 0:
            return 0.0
        return self._energy / self._max_energy

    @property
    def is_starving(self) -> bool:
        """Indica si el organismo está en estado de inanición."""
        return self._energy <= 0.0

    @property
    def starvation_days(self) -> float:
        """Días que el organismo lleva sin energía."""
        return self._starvation_days

    def _get_active_relationships(self) -> List[Relationship]:
        if self._relationships_cache_dirty or self._active_relationships_cache is None:
            self._active_relationships_cache = [
                r for r in self._relationships.values()
                if getattr(r, 'status', RelationshipStatus.UNKNOWN) 
                not in (RelationshipStatus.UNKNOWN, RelationshipStatus.EX_PARTNER)
            ]
            self._relationships_cache_dirty = False
        return self._active_relationships_cache

    def _invalidate_relationships_cache(self) -> None:
        self._relationships_cache_dirty = True

    # ==========================================
    # MÉTODOS DE ENERGÍA
    # ==========================================

    def add_energy(self, amount: float) -> None:
        """Añade energía al organismo (sin exceder el máximo).
        
        Args:
            amount: Cantidad de energía a añadir (puede ser negativa para gastar).
        """
        self._energy = max(0.0, min(self._max_energy, self._energy + amount))
        
        # Si tiene energía, resetear contador de inanición
        if self._energy > 0.0:
            self._starvation_days = 0.0

    def spend_energy(self, amount: float) -> bool:
        """Gasta energía del organismo.
        
        Args:
            amount: Cantidad de energía a gastar.
            
        Returns:
            True si se pudo gastar toda la energía, False si no había suficiente.
        """
        if amount <= 0:
            return True
        
        if self._energy >= amount:
            self._energy -= amount
            return True
        else:
            self._energy = 0.0
            return False

    def advance_starvation(self, delta_days: float) -> None:
        """Avanza el contador de inanición si no hay energía.
        
        Args:
            delta_days: Días transcurridos desde el último tick.
        """
        if self._energy <= 0.0:
            self._starvation_days += delta_days
        else:
            self._starvation_days = 0.0

    def set_energy(self, value: float) -> None:
        """Establece el nivel de energía directamente.
        
        Args:
            value: Nuevo nivel de energía (se clampea al rango [0, max_energy]).
        """
        self._energy = max(0.0, min(self._max_energy, value))
        if self._energy > 0.0:
            self._starvation_days = 0.0

    # ==========================================
    # GESTIÓN DE RELACIONES (OPTIMIZADA)
    # ==========================================
    def get_relationship_with(self, partner_id: int, current_day: float = 0.0) -> Relationship:
        """OPTIMIZACIÓN: Búsqueda O(1) usando dict en lugar de O(N) en lista."""
        rel = self._relationships.get(partner_id)
        if rel is not None:
            return rel
        
        new_rel = Relationship(owner_id=self.entity_id, partner_id=partner_id, start_day=current_day)
        new_rel.status = RelationshipStatus.UNKNOWN
        new_rel.affinity = 0.5
        new_rel.relationship_type = RelationshipType.EXCLUSIVE
        new_rel.shared_children = 0
        self._relationships[partner_id] = new_rel
        self._invalidate_relationships_cache()
        return new_rel

    def add_relationship(self, partner_id: int, status: RelationshipStatus, current_day: float, 
                         affinity: float = 0.5, rel_type: RelationshipType = RelationshipType.EXCLUSIVE) -> Relationship:
        rel = self.get_relationship_with(partner_id, current_day)
        setattr(rel, 'status', status)
        setattr(rel, 'affinity', affinity)
        setattr(rel, 'relationship_type', rel_type)
        setattr(rel, 'last_interaction_day', max(getattr(rel, 'last_interaction_day', current_day), current_day))
        self._invalidate_relationships_cache()
        return rel

    def update_relationship_status(self, partner_id: int, new_status: RelationshipStatus, current_day: float) -> None:
        rel = self.get_relationship_with(partner_id, current_day)
        if rel is not None:
            setattr(rel, 'status', new_status)
            setattr(rel, 'last_interaction_day', max(getattr(rel, 'last_interaction_day', current_day), current_day))
            self._invalidate_relationships_cache()

    # ==========================================
    # MÉTODOS DE SOCIAL MEMORY LAYER
    # ==========================================
    def register_adoption_event(self, event_type: str, entity_id: int, day: float, context: str = "adopcion") -> None:
        event = {"type": event_type, "entity_id": entity_id, "day": day, "context": context}
        self._adoption_history.append(event)
        if event_type == "adopted":
            self._reputation_score = min(1.0, self._reputation_score + 0.05)

    def get_adoption_history(self) -> List[Dict[str, Any]]: return self._adoption_history
    def get_adoptions_as_parent(self) -> List[Dict[str, Any]]: return [e for e in self._adoption_history if e["type"] == "adopted"]
    def get_adoptions_as_child(self) -> List[Dict[str, Any]]: return [e for e in self._adoption_history if e["type"] == "adopted_by"]

    def update_reputation_score(self, delta: float) -> None:
        self._reputation_score = max(0.0, min(1.0, self._reputation_score + delta))

    # ==========================================
    # INMUNIDAD (UNIFICADA)
    # ==========================================
    def get_specific_immunity(self, pathogen: Any) -> float:
        if isinstance(pathogen, str):
            family = pathogen
            pathogen_obj = None
        else:
            family = pathogen.family
            pathogen_obj = pathogen
        
        base_innate = max(0.1, self._genome.immunity - ((1.0 - self._emotions["energy"]) * 0.2))
        genetic_specific = self._genome.get_family_specific_immunity(family)
        acquired_bonus = self._immune_memory.get(family, 0.0)
        
        cross_immunity = 0.0
        for other_family, immunity_level in self._immune_memory.items():
            if other_family != family:
                similarity = Pathogen.get_family_similarity(family, other_family)
                if similarity > 0.0: cross_immunity += immunity_level * similarity * 0.3
        
        if pathogen_obj is not None:
            for other_family in Pathogen.get_related_families(family, min_similarity=0.1):
                other_genetic = self._genome.get_family_specific_immunity(other_family)
                if other_genetic > 0.0:
                    similarity = Pathogen.get_family_similarity(family, other_family)
                    cross_immunity += other_genetic * similarity * 0.2
        
        strain_immunity = 0.0
        if pathogen_obj and hasattr(pathogen_obj, 'pathogen_id'):
            direct_immunity = self._strain_immunity.get(pathogen_obj.pathogen_id, 0.0)
            related_immunity = self._calculate_related_strain_immunity(pathogen_obj)
            strain_immunity = max(direct_immunity, related_immunity)
        
        return min(5.0, base_innate + strain_immunity + genetic_specific + acquired_bonus + cross_immunity)

    def _calculate_related_strain_immunity(self, pathogen: Any) -> float:
        if not hasattr(pathogen, 'pathogen_id') or not hasattr(pathogen, 'generation'): return 0.0
        max_related = 0.0
        for strain_id, immunity in self._strain_immunity.items():
            if not strain_id.startswith(f"{pathogen.family}_"): continue
            metadata = self._strain_metadata.get(strain_id, {})
            known_gen = metadata.get("generation", 1)
            gen_diff = abs(pathogen.generation - known_gen)
            similarity_factor = max(0.0, 1.0 - (gen_diff * 0.15))
            max_related = max(max_related, immunity * similarity_factor)
        return max_related

    # ==========================================
    # ENFERMEDADES
    # ==========================================
    def infect(self, pathogen: Pathogen) -> None:
        pathogens_to_remove = [
            pid for pid, state in self._active_infections.items() 
            if state.pathogen.family == pathogen.family
        ]
        for pid in pathogens_to_remove:
            del self._active_infections[pid]
            
        infection_state = InfectionState(pathogen)
        self._active_infections[pathogen.pathogen_id] = infection_state
        
        if not infection_state.is_asymptomatic:
            self._health_state = "enfermo"
            self.update_emotion("stress", 0.3)
            self.update_emotion("energy", -0.4)

    def recover(self, pathogen_id: str) -> None:
        if pathogen_id in self._active_infections:
            infection_state = self._active_infections.pop(pathogen_id)
            pathogen = infection_state.pathogen
            current_strain_immunity = self._strain_immunity.get(pathogen_id, 0.0)
            self._strain_immunity[pathogen_id] = min(2.0, current_strain_immunity + 0.8)
            self._strain_metadata[pathogen_id] = {
                "family": pathogen.family, "generation": pathogen.generation, 
                "virulence": pathogen.virulence, "transmission": pathogen.transmission, 
                "lethality": pathogen.lethality
            }
            family_immunity = self._immune_memory.get(pathogen.family, 0.0)
            self._immune_memory[pathogen.family] = min(1.5, family_immunity + 0.4)
        if not self._active_infections or not self.is_symptomatic: 
            self._health_state = "sano"

    def advance_infections(self, delta_days: float) -> None:
        for infection_state in self._active_infections.values():
            old_phase = infection_state.phase
            infection_state.advance(delta_days)
            if old_phase != InfectionPhase.SYMPTOMATIC and infection_state.phase == InfectionPhase.SYMPTOMATIC:
                if not infection_state.is_asymptomatic:
                    self._health_state = "enfermo"
                    self.update_emotion("stress", 0.2)
                    self.update_emotion("energy", -0.3)

    def decay_immunity(self, delta_days: float, decay_rate: float = 0.001) -> None:
        strain_decay = math.exp(-decay_rate * 0.5 * delta_days)
        for strain_id in list(self._strain_immunity.keys()):
            self._strain_immunity[strain_id] *= strain_decay
            if self._strain_immunity[strain_id] < 0.01:
                del self._strain_immunity[strain_id]
                self._strain_metadata.pop(strain_id, None)
                
        family_decay = math.exp(-decay_rate * delta_days)
        for family in list(self._immune_memory.keys()):
            self._immune_memory[family] *= family_decay
            if self._immune_memory[family] < 0.01: 
                del self._immune_memory[family]

    def set_health_state(self, new_state: str) -> None:
        if new_state == "sano":
            self._active_infections.clear()
            self._health_state = "sano"

    # ==========================================
    # OTROS MÉTODOS
    # ==========================================
    def get_motivation(self, motivation_name: str) -> float: return self._motivations.get(motivation_name, 0.0)
    def update_motivation(self, motivation_name: str, amount: float) -> None:
        if motivation_name in self._motivations:
            self._motivations[motivation_name] = max(0.0, min(1.0, self._motivations[motivation_name] + amount))
    def get_dominant_motivation(self) -> Tuple[str, float]:
        if not self._motivations: return ('none', 0.0)
        return max(self._motivations.items(), key=lambda x: x[1])
    def decay_motivations(self, delta_days: float, decay_rate: float = 0.005) -> None:
        if not self._motivations: return
        decay_factor = math.exp(-decay_rate * delta_days)
        for motivation_name in list(self._motivations.keys()):
            self._motivations[motivation_name] = max(0.05, self._motivations[motivation_name] * decay_factor)

    def set_position(self, x: int, y: int) -> None: self.x, self.y = x, y
    def add_age(self, increment_days: float) -> None:
        self._age += increment_days
        self._check_milestones()
    def _check_milestones(self) -> None:
        time_cfg = self._config.time
        if self._age >= time_cfg.adult_age_days: self._is_adult = True
        if self._age >= time_cfg.senior_age_days: self._is_senior = True

    def register_marriage(self, partner_id: int, current_day: float = 0.0) -> None:
        self._partner_id = partner_id
        self._marital_status = "casado"
        self.add_relationship(partner_id=partner_id, status=RelationshipStatus.CONSOLIDATED, current_day=current_day, affinity=0.7, rel_type=RelationshipType.EXCLUSIVE)
        self.update_emotion("happiness", 0.4)

    def register_divorce(self, current_day: float = 0.0) -> None:
        old_partner = self._partner_id
        self._partner_id = None
        self._marital_status = "divorciado"
        if old_partner:
            rel = self.get_relationship_with(old_partner, current_day)
            if rel:
                setattr(rel, 'status', RelationshipStatus.EX_PARTNER)
                self._invalidate_relationships_cache()
        self.update_emotion("stress", 0.5)
        self.update_emotion("happiness", -0.5)

    def update_pregnancy(self, status: bool, days: float = 0.0, litter_size: int = 1) -> None:
        self._is_pregnant = bool(status)
        self._pregnancy_days = float(days)
        self._litter_size_gestating = int(litter_size) if status else 1

    def add_failed_pregnancy(self) -> None:
        self._failed_pregnancies += 1
        self.update_emotion("stress", 0.6)

    def add_child(self) -> None:
        self._children_count += 1
        self.update_emotion("happiness", 0.5)
        partner_id = self.partner_id
        if partner_id:
            rel = self.get_relationship_with(partner_id)
            if rel and hasattr(rel, 'shared_children'): rel.shared_children += 1

    def add_biological_child(self) -> None:
        self._biological_children_count += 1
        self.add_child()

    def set_parents(self, mother_id: int, father_id: Optional[int] = None) -> None:
        self._mother_id = mother_id
        self._father_id = father_id
        self._parents = [mother_id]
        if father_id is not None: self._parents.append(father_id)

    def add_adoptive_parent(self, parent_id: int, current_day: float = 0.0) -> None:
        if parent_id not in self._adoptive_parents:
            self._adoptive_parents.append(parent_id)
            self.update_emotion("happiness", 0.3)
            self.register_adoption_event(event_type="adopted_by", entity_id=parent_id, day=current_day, context="adopcion")

    def update_emotion(self, emotion: str, amount: float) -> None:
        if emotion in self._emotions:
            self._emotions[emotion] = max(0.0, min(1.0, self._emotions[emotion] + amount))

    def is_fertile(self) -> bool:
        repo_cfg = self._config.reproduction
        return repo_cfg.min_fertility_age_days <= self._age <= repo_cfg.max_fertility_age_days

    def can_reproduce(self) -> bool:
        return self.is_fertile() and not self._is_pregnant and not self.is_sick

    def get_longevity(self) -> float: return self._genome.longevity
    def get_immunity(self) -> float: return max(0.1, self._genome.immunity - ((1.0 - self._emotions["energy"]) * 0.2))