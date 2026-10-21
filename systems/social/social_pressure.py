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

GENÉTICA UNIVERSAL: Filtra presión social según SocialCapabilities del organismo.
Principio: La presión social influye en el comportamiento pero NO lo determina.

MIGRACIÓN HEXAGONAL:
- person.x/y → person.q/r
- cell_x/y → cell_q/r
- partner.x/y → partner.q/r
- math.sqrt(dx² + dy²) → distancia hexagonal axial
- Bucle cuadrado → bucle hexagonal en _apply_pressure_to_area
"""

from __future__ import annotations

import logging
import math
import random
from typing import Any, List, Optional, Tuple

from systems.relationships.social_capabilities import SocialCapabilities


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

    def __init__(self, config: Any = None) -> None:
        """Inicializa la calculadora de presión social."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config

    def _hex_distance(self, q1: int, r1: int, q2: int, r2: int) -> float:
        """Calcula la distancia hexagonal entre dos celdas axiales.

        Fórmula: (abs(dq) + abs(dr) + abs(dq + dr)) // 2
        Retorna float para compatibilidad con cálculos de distance_factor.
        """
        dq = q1 - q2
        dr = r1 - r2
        return float((abs(dq) + abs(dr) + abs(dq + dr)) // 2)

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
        """
        self.apply_environmental_pressure(state, pending, context, delta_days)

    def calculate_pressure_for_cell(
        self,
        person: Any,
        cell_q: int,
        cell_r: int,
        state: Any,
    ) -> float:
        """Calcula la presión social individual para una casilla candidata.

        Esta presión afecta SOLO al agente que se está moviendo.
        Se basa en sus relaciones personales.

        GENÉTICA UNIVERSAL: Solo aplica si el organismo tiene capacidades sociales.

        Args:
            person: El agente evaluando el movimiento.
            cell_q: Coordenada Q de la casilla candidata (hexagonal).
            cell_r: Coordenada R de la casilla candidata (hexagonal).
            state: WorldState para acceder a otros agentes.

        Returns:
            Presión social total (positivo = atrae, negativo = repele).
        """
        # GENÉTICA UNIVERSAL: Solo aplicar si puede sentir presión social
        social_caps = SocialCapabilities.from_genome(person.genome)
        if not social_caps.can_have_social_pressure:
            return 0.0

        total_pressure = 0.0

        # 1. Presión por relaciones
        total_pressure += self._relationship_pressure(
            person, cell_q, cell_r, state
        )

        # 2. Presión por núcleo residencial
        total_pressure += self._nucleus_pressure(
            person, cell_q, cell_r, state
        )

        # 3. Presión por enfermedad
        total_pressure += self._disease_pressure(person)

        return total_pressure

    def _relationship_pressure(
        self,
        person: Any,
        cell_q: int,
        cell_r: int,
        state: Any,
    ) -> float:
        """Calcula presión basada en relaciones personales.

        HEX: Usa distancia hexagonal en lugar de euclidiana.
        """
        pressure = 0.0

        relationships = getattr(person, "_relationships", None)
        if not relationships:
            return pressure

        for partner_id, rel in relationships.items():
            partner = state.get_person_by_id(partner_id)
            if partner is None:
                continue

            # HEX: Usar distancia hexagonal en lugar de euclidiana
            dist_to_partner = self._hex_distance(
                cell_q, cell_r, partner.q, partner.r
            )

            if dist_to_partner > RADIUS_PRESENCE:
                continue

            base_pressure = self._get_pressure_from_labels(rel, partner, state)
            distance_factor = max(
                0.0, 1.0 - (dist_to_partner / RADIUS_PRESENCE)
            )
            pressure += base_pressure * distance_factor

        return pressure

    def _get_pressure_from_labels(
        self, rel: Any, partner: Any, state: Any
    ) -> float:
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
        cell_q: int,
        cell_r: int,
        state: Any,
    ) -> float:
        """Calcula presión basada en proximidad al núcleo residencial.

        HEX: Usa distancia hexagonal al centro del núcleo.
        """
        nucleus_id = getattr(person, "nucleus_id", None)
        if nucleus_id is None:
            return 0.0

        nucleus = state.get_nucleus(nucleus_id)
        if nucleus is None:
            return 0.0

        # HEX: Usar distancia hexagonal al centro
        dist_to_center = nucleus.get_distance_to_center(cell_q, cell_r)
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

        HEX: Usa coordenadas q, r para todos los agentes.
        """
        if not self._has_social_events(pending):
            return

        # Aplicar presión por adopciones
        for adoption in getattr(pending, "adoptions", []):
            parent_a_id = adoption.get("parent_a")
            if parent_a_id is not None:
                parent = state.get_person_by_id(parent_a_id)
                if parent:
                    self._apply_pressure_to_area(
                        context,
                        parent.q,
                        parent.r,
                        ENVIRONMENTAL_PRESSURE["adoption"],
                        delta_days,
                    )

        # Aplicar presión por matrimonios
        for person_a_id in getattr(pending, "marriages", {}).items():
            person_a = state.get_person_by_id(person_a_id)
            if person_a:
                self._apply_pressure_to_area(
                    context,
                    person_a.q,
                    person_a.r,
                    ENVIRONMENTAL_PRESSURE["marriage"],
                    delta_days,
                )

        # Aplicar presión por muertes (trauma comunitario)
        for death_id in pending.deaths:
            deceased = state.get_person_by_id(death_id)
            if deceased:
                self._apply_pressure_to_area(
                    context,
                    deceased.q,
                    deceased.r,
                    ENVIRONMENTAL_PRESSURE["death"],
                    delta_days,
                )

        # Aplicar alivio por migraciones
        for entity_id in getattr(pending, "migration_targets", {}).items():
            person = state.get_person_by_id(entity_id)
            if person:
                self._apply_pressure_to_area(
                    context,
                    person.q,
                    person.r,
                    ENVIRONMENTAL_PRESSURE["migration"],
                    delta_days,
                )

        # Aplicar alivio por divorcios
        for person_a_id, person_b_id in getattr(pending, "divorces", []):
            person_a = state.get_person_by_id(person_a_id)
            if person_a:
                self._apply_pressure_to_area(
                    context,
                    person_a.q,
                    person_a.r,
                    ENVIRONMENTAL_PRESSURE["divorce"],
                    delta_days,
                )

    def _has_social_events(self, pending: Any) -> bool:
        """Verifica si hay eventos sociales en el buffer."""
        return (
            len(getattr(pending, "adoptions", [])) > 0
            or len(getattr(pending, "marriages", {})) > 0
            or len(pending.deaths) > 0
            or len(getattr(pending, "migration_targets", {})) > 0
            or len(getattr(pending, "divorces", [])) > 0
        )

    def _apply_pressure_to_area(
        self,
        context: Any,
        q: float,
        r: float,
        intensity: float,
        delta_days: float,
    ) -> None:
        """Aplica presión en un radio alrededor de una coordenada hexagonal.

        HEX: Usa coordenadas q, r y distancia hexagonal.
        Bucle hexagonal en lugar de cuadrado.
        """
        radius = int(SOCIAL_INFLUENCE_RADIUS)

        # HEX: Iterar en patrón hexagonal en lugar de cuadrado
        for dq in range(-radius, radius + 1):
            dr_min = max(-radius, -dq - radius)
            dr_max = min(radius, -dq + radius)
            for dr in range(dr_min, dr_max + 1):
                # HEX: Distancia hexagonal
                dist = self._hex_distance(0, 0, dq, dr)

                if dist <= SOCIAL_INFLUENCE_RADIUS:
                    decay_factor = 1.0 - (dist / SOCIAL_INFLUENCE_RADIUS)
                    pressure_delta = intensity * decay_factor * delta_days
                    coord = (int(q) + dq, int(r) + dr)
                    current_pressure = context.pressure_map.get(coord, 1.0)
                    new_pressure = max(
                        MIN_PRESSURE, current_pressure + pressure_delta
                    )
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