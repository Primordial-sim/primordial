"""Sistema de núcleos residenciales.

Un núcleo residencial es una estructura lógica que agrupa agentes que
comparten una situación de convivencia. NO es una zona física, sino
una relación estructural que genera preferencias de proximidad.

Principios fundamentales:
1. La posición física de cada agente es individual (1 agente = 1 casilla).
2. El núcleo influye en el movimiento mediante preferencias, no restricciones.
3. Los agentes pueden alejarse del núcleo y establecer nuevas relaciones.

Tipos de núcleo:
- SINGLE: Una persona sola
- COUPLE: Una pareja sin hijos
- FAMILY: Pareja con hijos
- SINGLE_PARENT: Un progenitor con hijos
- DEPENDENT_CARE: Persona con dependientes a su cargo
"""

from __future__ import annotations

import logging
import math
from enum import Enum
from typing import Dict, List, Optional, Tuple


class NucleusType(Enum):
    """Tipos de núcleo residencial."""
    SINGLE = "single"
    COUPLE = "couple"
    FAMILY = "family"
    SINGLE_PARENT = "single_parent"
    DEPENDENT_CARE = "dependent_care"


class NucleusMemberRole(Enum):
    """Rol de un miembro dentro del núcleo."""
    HEAD = "head"              # Cabeza del núcleo
    PARTNER = "partner"        # Pareja del cabeza
    CHILD = "child"            # Hijo/a
    DEPENDENT = "dependent"    # Dependiente (anciano, enfermo, etc.)
    OTHER = "other"            # Otro


class ResidentialNucleus:
    """Representa un núcleo residencial (convivencia).

    Un núcleo agrupa agentes que comparten residencia. Genera
    preferencias de proximidad pero NO restringe el movimiento.

    Attributes:
        nucleus_id: Identificador único del núcleo.
        nucleus_type: Tipo de núcleo (single, couple, family, etc.).
        members: Dict de entity_id -> NucleusMemberRole.
        center: Centro aproximado del núcleo (x, y).
        target_distance: Distancia objetivo entre miembros (en casillas).
    """

    _next_id: int = 1  # Contador estático para IDs únicos

    def __init__(
        self,
        nucleus_type: NucleusType = NucleusType.SINGLE,
        target_distance: float = 2.0,
    ) -> None:
        self.nucleus_id: int = ResidentialNucleus._next_id
        ResidentialNucleus._next_id += 1

        self.nucleus_type: NucleusType = nucleus_type
        self.members: Dict[int, NucleusMemberRole] = {}
        self.center: Tuple[float, float] = (0.0, 0.0)
        self.target_distance: float = target_distance

        self.logger = logging.getLogger(f"Nucleus_{self.nucleus_id}")

    # =========================================================================
    # FACTORIES
    # =========================================================================

    @classmethod
    def create_single(cls, agent_id: int) -> "ResidentialNucleus":
        """Crea un núcleo para una persona sola."""
        nucleus = cls(nucleus_type=NucleusType.SINGLE, target_distance=0.0)
        nucleus.add_member(agent_id, NucleusMemberRole.HEAD)
        return nucleus

    @classmethod
    def create_couple(cls, agent_a_id: int, agent_b_id: int) -> "ResidentialNucleus":
        """Crea un núcleo para una pareja."""
        nucleus = cls(nucleus_type=NucleusType.COUPLE, target_distance=1.5)
        nucleus.add_member(agent_a_id, NucleusMemberRole.HEAD)
        nucleus.add_member(agent_b_id, NucleusMemberRole.PARTNER)
        return nucleus

    @classmethod
    def create_family(
        cls,
        parent_a_id: int,
        parent_b_id: Optional[int],
        children_ids: List[int],
    ) -> "ResidentialNucleus":
        """Crea un núcleo familiar."""
        nucleus = cls(nucleus_type=NucleusType.FAMILY, target_distance=2.0)
        nucleus.add_member(parent_a_id, NucleusMemberRole.HEAD)
        if parent_b_id is not None:
            nucleus.add_member(parent_b_id, NucleusMemberRole.PARTNER)
        for child_id in children_ids:
            nucleus.add_member(child_id, NucleusMemberRole.CHILD)
        return nucleus

    # =========================================================================
    # GESTIÓN DE MIEMBROS
    # =========================================================================

    def add_member(self, agent_id: int, role: NucleusMemberRole) -> None:
        """Añade un miembro al núcleo."""
        self.members[agent_id] = role
        self._update_type()

    def remove_member(self, agent_id: int) -> None:
        """Elimina un miembro del núcleo."""
        if agent_id in self.members:
            del self.members[agent_id]
            self._update_type()

    def get_members(self) -> List[int]:
        """Retorna la lista de IDs de todos los miembros."""
        return list(self.members.keys())

    def get_member_role(self, agent_id: int) -> Optional[NucleusMemberRole]:
        """Retorna el rol de un miembro específico."""
        return self.members.get(agent_id)

    def has_member(self, agent_id: int) -> bool:
        """Verifica si un agente pertenece al núcleo."""
        return agent_id in self.members

    @property
    def size(self) -> int:
        """Número de miembros del núcleo."""
        return len(self.members)

    @property
    def is_empty(self) -> bool:
        """Verifica si el núcleo está vacío."""
        return len(self.members) == 0

    # =========================================================================
    # CÁLCULOS ESPACIALES
    # =========================================================================

    def update_center(self, positions: Dict[int, Tuple[float, float]]) -> None:
        """Actualiza el centro del núcleo basándose en las posiciones actuales.

        Args:
            positions: Dict de entity_id -> (x, y) para todos los miembros.
        """
        member_positions = []
        for agent_id in self.members:
            if agent_id in positions:
                member_positions.append(positions[agent_id])

        if member_positions:
            avg_x = sum(p[0] for p in member_positions) / len(member_positions)
            avg_y = sum(p[1] for p in member_positions) / len(member_positions)
            self.center = (avg_x, avg_y)

    def get_distance_to_center(self, x: float, y: float) -> float:
        """Calcula la distancia desde un punto al centro del núcleo."""
        dx = x - self.center[0]
        dy = y - self.center[1]
        return math.sqrt(dx * dx + dy * dy)

    # =========================================================================
    # LÓGICA DE TIPOS
    # =========================================================================

    def _update_type(self) -> None:
        """Actualiza el tipo de núcleo basándose en sus miembros."""
        if self.is_empty:
            return

        roles = list(self.members.values())
        has_head = NucleusMemberRole.HEAD in roles
        has_partner = NucleusMemberRole.PARTNER in roles
        has_children = NucleusMemberRole.CHILD in roles

        if self.size == 1:
            self.nucleus_type = NucleusType.SINGLE
            self.target_distance = 0.0
        elif has_partner and not has_children:
            self.nucleus_type = NucleusType.COUPLE
            self.target_distance = 1.5
        elif has_partner and has_children:
            self.nucleus_type = NucleusType.FAMILY
            self.target_distance = 2.0
        elif not has_partner and has_children:
            self.nucleus_type = NucleusType.SINGLE_PARENT
            self.target_distance = 2.0
        else:
            self.nucleus_type = NucleusType.SINGLE
            self.target_distance = 1.0

    # =========================================================================
    # EVENTOS DE CICLO DE VIDA
    # =========================================================================

    def on_marriage(self, agent_a_id: int, agent_b_id: int) -> None:
        """Se llama cuando dos agentes forman una pareja."""
        if self.has_member(agent_a_id):
            self.add_member(agent_b_id, NucleusMemberRole.PARTNER)
        elif self.has_member(agent_b_id):
            self.add_member(agent_a_id, NucleusMemberRole.PARTNER)
        else:
            self.add_member(agent_a_id, NucleusMemberRole.HEAD)
            self.add_member(agent_b_id, NucleusMemberRole.PARTNER)

        self.logger.info(
            "💍 Matrimonio: agentes %d y %d → Núcleo %d (%s)",
            agent_a_id, agent_b_id, self.nucleus_id, self.nucleus_type.value,
        )

    def on_birth(self, child_id: int) -> None:
        """Se llama cuando nace un hijo en este núcleo."""
        self.add_member(child_id, NucleusMemberRole.CHILD)
        self.logger.info(
            "👶 Nacimiento: agente %d → Núcleo %d (%s)",
            child_id, self.nucleus_id, self.nucleus_type.value,
        )

    def on_death(self, agent_id: int) -> None:
        """Se llama cuando un miembro del núcleo fallece."""
        role = self.get_member_role(agent_id)
        self.remove_member(agent_id)

        self.logger.info(
            "⚰️ Muerte: agente %d (rol: %s) → Núcleo %d (%d miembros restantes)",
            agent_id, role.value if role else "unknown", self.nucleus_id, self.size,
        )

    def on_child_independence(self, child_id: int) -> Optional["ResidentialNucleus"]:
        """Se llama cuando un hijo se independiza.

        Returns:
            Un nuevo núcleo para el hijo, o None si no procede.
        """
        role = self.get_member_role(child_id)
        if role != NucleusMemberRole.CHILD:
            return None

        self.remove_member(child_id)
        new_nucleus = ResidentialNucleus.create_single(child_id)

        self.logger.info(
            "🏠 Independización: agente %d deja Núcleo %d → nuevo Núcleo %d",
            child_id, self.nucleus_id, new_nucleus.nucleus_id,
        )

        return new_nucleus

    # =========================================================================
    # SERIALIZACIÓN
    # =========================================================================

    def to_dict(self) -> Dict:
        """Serializa el núcleo para enviar a Godot o guardar."""
        return {
            "nucleus_id": self.nucleus_id,
            "type": self.nucleus_type.value,
            "members": {str(k): v.value for k, v in self.members.items()},
            "center": list(self.center),
            "size": self.size,
            "target_distance": self.target_distance,
        }

    def __repr__(self) -> str:
        return (
            f"Nucleus(id={self.nucleus_id}, type={self.nucleus_type.value}, "
            f"members={self.size}, center={self.center})"
        )