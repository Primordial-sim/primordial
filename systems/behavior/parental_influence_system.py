"""Sistema de influencia parental.

Modela cómo el carácter de los padres (biológicos o adoptivos) afecta 
la personalidad del hijo con el tiempo, considerando:
- Temperamento, sociabilidad y niveles de estrés.
- Clima emocional del hogar (basado en la calidad de la relación).
- Plasticidad developmental (mayor influencia en la infancia/adolescencia).

Principio: "La crianza moldea el carácter, la genética solo da la base."
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, List, Optional, TYPE_CHECKING

from core.config.simulation_config import SimulationConfig
from core.state.world_state import WorldState
from core.state.pending_changes import PendingChanges
from systems.environment.environment_context import EnvironmentContext

if TYPE_CHECKING:
    from systems.genealogy.genealogy_system import GenealogySystem
    from entities.person.person import Person


@dataclass
class ParentalInfluenceEvent:
    """Registro ligero de un cambio de personalidad por influencia parental."""
    child_id: int
    parent_id: int
    trait_modified: str  # 'temperament', 'sociability', 'stress'
    delta: float
    reason: str


class ParentalInfluenceSystem:
    """Transmite rasgos de personalidad de padres a hijos durante la crianza."""

    def __init__(
        self,
        config: SimulationConfig,
        genealogy_system: Optional['GenealogySystem'] = None,
    ) -> None:
        self.config = config
        self.genealogy_system = genealogy_system
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Contador para logs periódicos (evita spam)
        self._log_counter = 0
        self._log_interval = 365  # Días simulados entre logs

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Evalúa y aplica la influencia parental en agentes jóvenes."""
        self._log_counter += delta_days
        events: List[ParentalInfluenceEvent] = []
        
        current_day = getattr(state, 'world_days_elapsed', 0.0)
        
        # Configuración de influencia desde ParentalInfluenceConfig
        parental_cfg = getattr(self.config, 'parental_influence', None)
        if parental_cfg:
            max_influence_age = getattr(parental_cfg, 'max_influence_age_days', 5000.0)
            base_plasticity = getattr(parental_cfg, 'base_personality_plasticity', 0.05)
        else:
            max_influence_age = 5000.0
            base_plasticity = 0.05
        
        for person in state.get_all_persons():
            # 1. FILTRO DE EDAD: Solo agentes en etapa de desarrollo son altamente plásticos
            age = current_day - getattr(person, 'birth_tick', 0.0)
            if age > max_influence_age:
                continue
                
            # Plasticidad decrece linealmente con la edad (1.0 al nacer, 0.0 al llegar a max_influence_age)
            plasticity = base_plasticity * max(0.0, 1.0 - (age / max_influence_age))
            if plasticity <= 0.01:
                continue

            # 2. IDENTIFICAR PADRES (Biológicos o Adoptivos)
            parents = self._get_parents(person, state)
            if not parents:
                continue

            # 3. APLICAR INFLUENCIA POR CADA PADRE
            for parent in parents:
                # Calcular clima emocional (simplificado: basado en proximidad y estado general del padre)
                emotional_climate = self._calculate_emotional_climate(person, parent, current_day)
                
                # Factor de influencia: plasticidad * clima emocional
                influence_factor = plasticity * emotional_climate
                
                if influence_factor < 0.001:
                    continue

                # Aplicar cambios en rasgos de personalidad (ejemplo: temperamento y sociabilidad)
                events.extend(self._apply_trait_influence(
                    person, parent, influence_factor, current_day
                ))

        # 4. LOGGING PERIÓDICO
        if self._log_counter >= self._log_interval and events:
            self.logger.info(
                "🌱 Influencia parental: %d rasgos modificados en el último ciclo",
                len(events)
            )
            self._log_counter = 0.0

        # Registrar eventos en pending para otros sistemas (ej: métricas, logging)
        if events:
            existing = getattr(pending, 'parental_influences', [])
            setattr(pending, 'parental_influences', existing + events)

    def _get_parents(self, child: Any, state: WorldState) -> List[Any]:
        """Obtiene la lista de padres (biológicos o adoptivos) de un hijo."""
        parents = []
        
        # Opción A: Si la entidad Person ya tiene referencias directas
        bio_parents = getattr(child, 'biological_parents', None)
        if bio_parents and isinstance(bio_parents, (list, tuple)):
            for p_id in bio_parents:
                p = state.get_person_by_id(p_id)
                if p and getattr(p, 'is_alive', True):
                    parents.append(p)
                    
        adopt_parents = getattr(child, 'adoptive_parents', None)
        if adopt_parents and isinstance(adopt_parents, (list, tuple)):
            for p_id in adopt_parents:
                p = state.get_person_by_id(p_id)
                if p and getattr(p, 'is_alive', True):
                    parents.append(p)
                    
        # Opción B: Fallback al GenealogySystem si está disponible y Person no tiene las listas
        if not parents and self.genealogy_system is not None:
            node = self.genealogy_system.registry.get(child.entity_id)
            if node:
                for p_id in node.biological_parents + node.adoptive_parents:
                    p = state.get_person_by_id(p_id)
                    if p and getattr(p, 'is_alive', True) and p not in parents:
                        parents.append(p)
                        
        return parents

    def _calculate_emotional_climate(self, child: Any, parent: Any, current_day: float) -> float:
        """
        Calcula el clima emocional del hogar [0.0, 1.5].
        1.0 = neutro, >1.0 = hogar cálido/apoyo, <1.0 = hogar tenso/estrés.
        """
        base_climate = 1.0
        
        # Si existe sistema de relaciones, ajustar por calidad del vínculo
        if hasattr(child, 'get_relationship_with'):
            rel = child.get_relationship_with(parent.entity_id, current_day)
            if rel:
                labels = rel.get_labels(current_day)
                if "Familia Elegida" in labels or "Amigo" in labels:
                    base_climate = 1.3  # Clima cálido, mayor influencia positiva
                elif "Rival" in labels or "Enemigo" in labels:
                    base_climate = 0.5  # Clima tenso, influencia distorsionada (estrés)
                    
        # Penalizar si el padre tiene alto estrés (se contagia)
        parent_stress = getattr(parent, 'stress_level', 0.5)
        if parent_stress > 0.7:
            base_climate *= 0.8  # El estrés parental reduce la calidad del clima
            
        return max(0.1, min(1.5, base_climate))

    def _apply_trait_influence(
        self, 
        child: Any, 
        parent: Any, 
        influence_factor: float, 
        current_day: float
    ) -> List[ParentalInfluenceEvent]:
        """Aplica la deriva de rasgos emocionales del hijo hacia los del padre.
        
        Como el Genome es inmutable, la influencia parental afecta:
        - emotions["stress"] (nivel de estrés actual)
        - emotions["happiness"] (nivel de felicidad actual)
        - _learned_traits (nuevo diccionario para rasgos adquiridos)
        """
        events = []
        
        # 1. Influencia en emociones (stress y happiness)
        if hasattr(child, '_emotions') and hasattr(parent, '_emotions'):
            for emotion_key in ['stress', 'happiness']:
                child_val = child._emotions.get(emotion_key, 0.5)
                parent_val = parent._emotions.get(emotion_key, 0.5)
                
                delta = (parent_val - child_val) * influence_factor
                
                if abs(delta) > 0.001:
                    new_val = max(0.0, min(1.0, child_val + delta))
                    child._emotions[emotion_key] = new_val
                    
                    events.append(ParentalInfluenceEvent(
                        child_id=child.entity_id,
                        parent_id=parent.entity_id,
                        trait_modified=f"emotion_{emotion_key}",
                        delta=delta,
                        reason=f"parental_influence_{emotion_key}"
                    ))
        
                # 2. Influencia en rasgos aprendidos (nuevo mecanismo)
        if not hasattr(child, '_learned_traits'):
            child._learned_traits = {}
        
        # Rasgos que pueden aprenderse (ej: preferencias, hábitos)
        learned_traits = ['diet_preference', 'migration_affinity', 'social_comfort']
        
        for trait in learned_traits:
            child_val = child._learned_traits.get(trait, 0.5)
            
            # El padre transmite su valor genético como referencia
            parent_val = 0.5
            if hasattr(parent, '_genome'):
                genome_val = getattr(parent._genome, trait, None)
                if isinstance(genome_val, (int, float)):
                    parent_val = float(genome_val)
            
            delta = (parent_val - child_val) * influence_factor
            
            if abs(delta) > 0.001:
                new_val = max(0.0, min(1.0, child_val + delta))
                child._learned_traits[trait] = new_val
                
                events.append(ParentalInfluenceEvent(
                    child_id=child.entity_id,
                    parent_id=parent.entity_id,
                    trait_modified=f"learned_{trait}",
                    delta=delta,
                    reason=f"parental_influence_{trait}"
                ))
                
        return events