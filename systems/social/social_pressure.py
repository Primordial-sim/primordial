"""Sistema unificado de presión social.

Este módulo gestiona dos tipos de presión social:

1. PRESIÓN INDIVIDUAL (para movimiento):
   - Calcula la presión que las relaciones personales ejercen sobre un agente
   - Basada en: pareja, hijos, amigos, conflictos
   - Usado por MovementSystem para decidir movimiento

2. PRESIÓN AMBIENTAL (para el entorno):
   - Aplica presión comunitaria basada en eventos sociales
   - Basada en: muertes, matrimonios, adopciones, migraciones
   - Usado por el pipeline para modificar el mapa de presión

Principio: La presión social influye en el comportamiento pero NO lo determina.
"""

from __future__ import annotations

import logging
import math
import random
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# CONSTANTES DE PRESIÓN INDIVIDUAL (relaciones personales)
# =============================================================================

PRESSURE_VALUES = {
    "partner": 10.0,
    "child_0_5": 20.0,
    "child_5_12": 12.0,
    "child_13_17": 6.0,
    "sibling": 3.0,
    "friend": 2.0,
    "acquaintance": 0.0,
    "conflict": -8.0,
    "disease_isolation": -10.0,
}

RADIUS_PRESENCE = 5.0
RADIUS_INTERACTION = 2.0
RADIUS_RELATIONSHIP = 1.0

AGE_CHILD_0_5 = 1825
AGE_CHILD_5_12 = 4380
AGE_CHILD_13_17 = 6205
AGE_ADULT = 6570


# =============================================================================
# CONSTANTES DE PRESIÓN AMBIENTAL (eventos comunitarios)
# =============================================================================

ENVIRONMENTAL_PRESSURE = {
    "adoption": 0.3,
    "marriage": 0.2,
    "death": 0.4,
    "migration": -0.2,
    "divorce": -0.1,
}

SOCIAL_INFLUENCE_RADIUS = 15.0
MIN_PRESSURE = 0.5


# =============================================================================
# CLASE PRINCIPAL
# =============================================================================

class SocialPressureCalculator:
    """Calculadora unificada de presión social.
    
    Proporciona métodos para:
    - Calcular presión individual (para movimiento de agentes)
    - Aplicar presión ambiental (para el mapa de presión del entorno)
    """
    
    def __init__(self, config: Any = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config
    
    # =========================================================================
    # PRESIÓN INDIVIDUAL (para MovementSystem)
    # =========================================================================

    def process(
        self,
        state: Any,
        pending: Any,
        delta_days: float,
        context: Any,
    ) -> None:
        """Método adapter para compatibilidad con el pipeline de ejecución.
        
        El pipeline requiere que todos los sistemas tengan un método process().
        Este método delega en apply_environmental_pressure().
        
        Args:
            state: WorldState con los agentes.
            pending: PendingChanges con eventos del tick.
            delta_days: Duración del tick en días.
            context: EnvironmentContext con pressure_map.
        """
        self.apply_environmental_pressure(state, pending, context, delta_days)
    
    def calculate_pressure_for_cell(
        self,
        person: Any,
        cell_x: int,
        cell_y: int,
        state: Any,
    ) -> float:
        """Calcula la presión social individual para una casilla candidata.
        
        Esta presión afecta SOLO al agente que se está moviendo.
        Se basa en sus relaciones personales.
        
        Args:
            person: El agente evaluando el movimiento.
            cell_x: Coordenada X de la casilla candidata.
            cell_y: Coordenada Y de la casilla candidata.
            state: WorldState para acceder a otros agentes.
            
        Returns:
            Presión social total (positivo = atrae, negativo = repele).
        """
        total_pressure = 0.0
        
        # 1. Presión por relaciones
        total_pressure += self._relationship_pressure(person, cell_x, cell_y, state)
        
        # 2. Presión por núcleo residencial
        total_pressure += self._nucleus_pressure(person, cell_x, cell_y, state)
        
        # 3. Presión por enfermedad
        total_pressure += self._disease_pressure(person)
        
        return total_pressure
    
    def _relationship_pressure(
        self,
        person: Any,
        cell_x: int,
        cell_y: int,
        state: Any,
    ) -> float:
        """Calcula presión basada en relaciones personales."""
        pressure = 0.0
        
        relationships = getattr(person, "_relationships", None)
        if not relationships:
            return pressure
        
        for partner_id, rel in relationships.items():
            partner = state.get_person_by_id(partner_id)
            if partner is None:
                continue
            
            dist_to_partner = math.sqrt(
                (cell_x - partner.x) ** 2 + (cell_y - partner.y) ** 2
            )
            
            if dist_to_partner > RADIUS_PRESENCE:
                continue
            
            base_pressure = self._get_pressure_from_labels(rel, partner, state)
            distance_factor = max(0.0, 1.0 - (dist_to_partner / RADIUS_PRESENCE))
            
            pressure += base_pressure * distance_factor
        
        return pressure
    
    def _get_pressure_from_labels(self, rel: Any, partner: Any, state: Any) -> float:
        """Determina presión base según etiquetas de relación."""
        try:
            labels = rel.get_labels(state.world_days_elapsed)
        except Exception:
            return 0.0
        
        if "Amante" in labels:
            return PRESSURE_VALUES["partner"]
        
        if "Amigo" in labels or "Aliado" in labels:
            return PRESSURE_VALUES["friend"]
        
        if "Rival" in labels or "Rival Respetado" in labels:
            return PRESSURE_VALUES["conflict"]
        
        if partner.age < AGE_ADULT:
            return self._child_pressure_by_age(partner.age)
        
        return PRESSURE_VALUES["acquaintance"]
    
    def _child_pressure_by_age(self, child_age_days: float) -> float:
        """Calcula presión de dependencia según edad del hijo."""
        if child_age_days < AGE_CHILD_0_5:
            return PRESSURE_VALUES["child_0_5"]
        if child_age_days < AGE_CHILD_5_12:
            return PRESSURE_VALUES["child_5_12"]
        if child_age_days < AGE_CHILD_13_17:
            return PRESSURE_VALUES["child_13_17"]
        return PRESSURE_VALUES["acquaintance"]
    
    def _nucleus_pressure(
        self,
        person: Any,
        cell_x: int,
        cell_y: int,
        state: Any,
    ) -> float:
        """Calcula presión basada en proximidad al núcleo residencial."""
        nucleus_id = getattr(person, "nucleus_id", None)
        if nucleus_id is None:
            return 0.0
        
        nucleus = state.get_nucleus(nucleus_id)
        if nucleus is None:
            return 0.0
        
        dist_to_center = nucleus.get_distance_to_center(cell_x, cell_y)
        target_dist = nucleus.target_distance
        
        if dist_to_center <= target_dist:
            return 3.0
        
        excess = dist_to_center - target_dist
        max_penalty = 5.0
        penalty = min(excess * 1.5, max_penalty)
        return -penalty
    
    def _disease_pressure(self, person: Any) -> float:
        """Calcula presión de aislamiento por enfermedad."""
        if getattr(person, "is_sick", False):
            return PRESSURE_VALUES["disease_isolation"] * 0.3
        return 0.0
    
    # =========================================================================
    # PRESIÓN AMBIENTAL (para el pipeline de ejecución)
    # =========================================================================
    
    def apply_environmental_pressure(
        self,
        state: Any,
        pending: Any,
        context: Any,
        delta_days: float,
    ) -> None:
        """Aplica presión ambiental basada en eventos sociales del tick.
        
        Este método modifica el pressure_map del EnvironmentContext.
        Afecta a TODOS los agentes en las zonas afectadas.
        
        Args:
            state: WorldState con los agentes.
            pending: PendingChanges con eventos del tick.
            context: EnvironmentContext con pressure_map.
            delta_days: Duración del tick en días.
        """
        if not self._has_social_events(pending):
            return
        
        # Aplicar presión por adopciones
        for adoption in getattr(pending, 'adoptions', []):
            parent_a_id = adoption.get('parent_a')
            if parent_a_id is not None:
                parent = state.get_person_by_id(parent_a_id)
                if parent:
                    self._apply_pressure_to_area(
                        context, parent.x, parent.y,
                        ENVIRONMENTAL_PRESSURE["adoption"], delta_days
                    )
        
        # Aplicar presión por matrimonios
        for person_a_id, person_b_id in getattr(pending, 'marriages', {}).items():
            person_a = state.get_person_by_id(person_a_id)
            if person_a:
                self._apply_pressure_to_area(
                    context, person_a.x, person_a.y,
                    ENVIRONMENTAL_PRESSURE["marriage"], delta_days
                )
        
        # Aplicar presión por muertes (trauma comunitario)
        for death_id in pending.deaths:
            deceased = state.get_person_by_id(death_id)
            if deceased:
                self._apply_pressure_to_area(
                    context, deceased.x, deceased.y,
                    ENVIRONMENTAL_PRESSURE["death"], delta_days
                )
        
        # Aplicar alivio por migraciones
        for entity_id, target in getattr(pending, 'migration_targets', {}).items():
            person = state.get_person_by_id(entity_id)
            if person:
                self._apply_pressure_to_area(
                    context, person.x, person.y,
                    ENVIRONMENTAL_PRESSURE["migration"], delta_days
                )
        
        # Aplicar alivio por divorcios
        for person_a_id, person_b_id in getattr(pending, 'divorces', []):
            person_a = state.get_person_by_id(person_a_id)
            if person_a:
                self._apply_pressure_to_area(
                    context, person_a.x, person_a.y,      # ✅ CORREGIDO
                    ENVIRONMENTAL_PRESSURE["divorce"], delta_days
                )
    
    def _has_social_events(self, pending: Any) -> bool:
        """Verifica si hay eventos sociales en el buffer."""
        return (
            len(getattr(pending, 'adoptions', [])) > 0 or
            len(getattr(pending, 'marriages', {})) > 0 or
            len(pending.deaths) > 0 or
            len(getattr(pending, 'migration_targets', {})) > 0 or
            len(getattr(pending, 'divorces', [])) > 0
        )
    
    def _apply_pressure_to_area(
        self,
        context: Any,
        x: float,
        y: float,
        intensity: float,
        delta_days: float,
    ) -> None:
        """Aplica presión en un radio alrededor de una coordenada."""
        radius = int(SOCIAL_INFLUENCE_RADIUS)
        
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                dist = math.sqrt(dx * dx + dy * dy)
                
                if dist <= SOCIAL_INFLUENCE_RADIUS:
                    decay_factor = 1.0 - (dist / SOCIAL_INFLUENCE_RADIUS)
                    pressure_delta = intensity * decay_factor * delta_days
                    
                    coord = (int(x) + dx, int(y) + dy)
                    current_pressure = context.pressure_map.get(coord, 1.0)
                    new_pressure = max(MIN_PRESSURE, current_pressure + pressure_delta)
                    context.pressure_map[coord] = new_pressure
    
    # =========================================================================
    # SELECCIÓN PROBABILÍSTICA (para MovementSystem)
    # =========================================================================
    
    @staticmethod
    def probabilistic_selection(
        scored_cells: List[Tuple[Tuple[int, int], float]],
        temperature: float = 2.0,
    ) -> Optional[Tuple[int, int]]:
        """Selecciona una casilla de forma probabilística según puntuaciones."""
        if not scored_cells:
            return None
        
        if len(scored_cells) == 1:
            return scored_cells[0][0]
        
        scores = [score for _, score in scored_cells]
        min_score = min(scores)
        shifted_scores = [s - min_score + 1.0 for s in scores]
        
        weights = []
        for s in shifted_scores:
            weight = math.exp(s / temperature)
            weights.append(weight)
        
        total_weight = sum(weights)
        if total_weight == 0:
            return scored_cells[0][0]
        
        probabilities = [w / total_weight for w in weights]
        
        cells = [cell for cell, _ in scored_cells]
        selected = random.choices(cells, weights=probabilities, k=1)[0]
        
        return selected