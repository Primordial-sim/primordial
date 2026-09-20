"""Mecanismos de ejecución de relaciones ecológicas.

Cada mecanismo encapsula la lógica específica de un tipo de interacción.
El mecanismo describe CÓMO se ejecuta la relación, no QUÉ relación es.

Arquitectura:
    BaseMechanism (abstracta)
    ├── HuntMechanism          → Depredación activa
    ├── GrazingMechanism       → Pastoreo / herbivoría
    ├── PollinationMechanism   → Polinización (mutualismo)
    ├── ResourceConsumptionMechanism → Competencia
    ├── ScavengingMechanism    → Carroñeo
    └── InfectionMechanism     → Parasitismo

Uso:
    mechanism = MechanismFactory.get_mechanism(relationship.mechanism)
    outcome = mechanism.execute(person_a, person_b, relationship, pending)
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Type

from systems.ecology.relationship_types import (
    MechanismType,
    InteractionOutcome,
)

if TYPE_CHECKING:
    from entities.person.person import Person
    from core.state.pending_changes import PendingChanges
    from systems.ecology.ecological_relationship import EcologicalRelationship


class BaseMechanism(ABC):
    """Clase base abstracta para todos los mecanismos de interacción.
    
    Cada mecanismo encapsula:
    - La probabilidad de éxito
    - Los efectos sobre ambos organismos
    - La lógica específica de la interacción
    """
    
    def __init__(self) -> None:
        self._total_executions: int = 0
        self._total_successes: int = 0
    
    @abstractmethod
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        """Calcula la probabilidad de éxito de la interacción.
        
        Args:
            person_a: Organismo que inicia la interacción.
            person_b: Organismo objetivo.
            relationship: La relación ecológica.
            
        Returns:
            Probabilidad de éxito [0.0, 1.0].
        """
        pass
    
    @abstractmethod
    def _apply_effects(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
        success: bool,
    ) -> None:
        """Aplica los efectos de la interacción.
        
        Args:
            person_a: Organismo que inicia la interacción.
            person_b: Organismo objetivo.
            relationship: La relación ecológica.
            pending: Buffer de cambios pendientes.
            success: Si la interacción fue exitosa.
        """
        pass
    
    def execute(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
    ) -> InteractionOutcome:
        """Ejecuta la interacción entre dos organismos.
        
        Args:
            person_a: Organismo que inicia la interacción.
            person_b: Organismo objetivo.
            relationship: La relación ecológica.
            pending: Buffer de cambios pendientes.
            
        Returns:
            El resultado de la interacción.
        """
        self._total_executions += 1
        
        # Calcular probabilidad de éxito
        success_prob = self._calculate_success_probability(person_a, person_b, relationship)
        
        # Tirada aleatoria
        roll = random.random()
        success = roll < success_prob
        
        # Aplicar efectos
        self._apply_effects(person_a, person_b, relationship, pending, success)
        
        if success:
            self._total_successes += 1
            return InteractionOutcome.SUCCESS
        else:
            return InteractionOutcome.FAILURE
    
    @property
    def success_rate(self) -> float:
        """Tasa de éxito histórica."""
        if self._total_executions == 0:
            return 0.0
        return self._total_successes / self._total_executions
    
    def get_stats(self) -> Dict[str, object]:
        """Retorna estadísticas del mecanismo."""
        return {
            "executions": self._total_executions,
            "successes": self._total_successes,
            "success_rate": round(self.success_rate, 3),
        }


class HuntMechanism(BaseMechanism):
    """Mecanismo de caza activa (depredación).
    
    El depredador persigue y captura a la presa.
    La probabilidad de éxito depende de:
    - Intensidad de la relación
    - Tamaño relativo (depredador grande vs presa pequeña)
    """
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        """Probabilidad basada en intensidad y tamaño relativo."""
        base_prob = relationship.intensity * 0.7  # Máximo 70%
        
        # Modificador por tamaño: depredador grande vs presa pequeña
        size_a = getattr(person_a.genome, 'body_size', 0.5)
        size_b = getattr(person_b.genome, 'body_size', 0.5)
        
        if size_a > size_b:
            size_bonus = (size_a - size_b) * 0.2
        else:
            size_bonus = (size_a - size_b) * 0.3  # Penalización mayor si la presa es más grande
        
        return max(0.05, min(0.85, base_prob + size_bonus))
    
    def _apply_effects(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
        success: bool,
    ) -> None:
        """Si éxito: presa muere, depredador gana energía."""
        if success:
            # Registrar muerte de la presa
            pending.register_death(
                entity_id=person_b.entity_id,
                reason="predation",
            )
            
            # Dar energía al depredador
            if relationship.effect_on_a:
                energy_gain = relationship.effect_on_a.energy_change
                if energy_gain > 0:
                    person_a.add_energy(energy_gain)
        # Si fallo: la presa escapa, sin efectos


class GrazingMechanism(BaseMechanism):
    """Mecanismo de pastoreo (herbivoría).
    
    El herbívoro consume parte de la planta.
    Generalmente no mata a la planta, pero la daña.
    """
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        """Probabilidad alta: las plantas no huyen."""
        return relationship.intensity * 0.9  # Máximo 90%
    
    def _apply_effects(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
        success: bool,
    ) -> None:
        """Herbívoro gana energía, planta pierde energía."""
        if success:
            # Herbívoro gana energía
            if relationship.effect_on_a:
                energy_gain = relationship.effect_on_a.energy_change
                if energy_gain > 0:
                    person_a.add_energy(energy_gain)
            
            # Planta pierde energía (daño)
            if relationship.effect_on_b:
                damage = abs(relationship.effect_on_b.energy_change)
                if damage > 0:
                    person_b.spend_energy(damage)
                    
                    # Si la planta se queda sin energía, muere
                    if person_b.energy <= 0:
                        pending.register_death(
                            entity_id=person_b.entity_id,
                            reason="consumed",
                        )


class PollinationMechanism(BaseMechanism):
    """Mecanismo de polinización (mutualismo).
    
    El polinizador obtiene néctar, la planta se reproduce.
    Ambas especies se benefician.
    """
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        """La polinización casi siempre ocurre cuando hay encuentro."""
        return 0.95  # Casi siempre exitosa
    
    def _apply_effects(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
        success: bool,
    ) -> None:
        """Ambos organismos se benefician."""
        if success:
            # Polinizador gana energía (néctar)
            if relationship.effect_on_a:
                energy_gain = relationship.effect_on_a.energy_change
                if energy_gain > 0:
                    person_a.add_energy(energy_gain)
            
            # Planta gana energía (reproducción asistida)
            if relationship.effect_on_b:
                energy_gain = relationship.effect_on_b.energy_change
                if energy_gain > 0:
                    person_b.add_energy(energy_gain)


class ResourceConsumptionMechanism(BaseMechanism):
    """Mecanismo de competencia por recursos.
    
    Ambos organismos compiten por recursos limitados.
    Ambos pierden energía en la competencia.
    """
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        """La competencia siempre ocurre cuando hay encuentro."""
        return 1.0  # Siempre ocurre
    
    def _apply_effects(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
        success: bool,
    ) -> None:
        """Ambos organismos pierden energía."""
        if success:
            # Organismo A pierde energía
            if relationship.effect_on_a:
                energy_loss = abs(relationship.effect_on_a.energy_change)
                if energy_loss > 0:
                    person_a.spend_energy(energy_loss)
            
            # Organismo B pierde energía
            if relationship.effect_on_b:
                energy_loss = abs(relationship.effect_on_b.energy_change)
                if energy_loss > 0:
                    person_b.spend_energy(energy_loss)


class ScavengingMechanism(BaseMechanism):
    """Mecanismo de carroñeo.
    
    El carroñero consume restos de organismos muertos.
    No requiere matar a la presa.
    """
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        """Probabilidad de encontrar carroña."""
        return relationship.intensity * 0.8
    
    def _apply_effects(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
        success: bool,
    ) -> None:
        """Carroñero gana energía, organismo B no se afecta (ya está muerto o es un recurso)."""
        if success:
            if relationship.effect_on_a:
                energy_gain = relationship.effect_on_a.energy_change
                if energy_gain > 0:
                    person_a.add_energy(energy_gain)


class InfectionMechanism(BaseMechanism):
    """Mecanismo de infección parasitaria.
    
    El parásito infecta al huésped.
    El parásito gana energía a expensas del huésped.
    """
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        """Probabilidad basada en intensidad y resistencia del huésped."""
        base_prob = relationship.intensity * 0.6
        
        # Modificador por inmunidad del huésped
        immunity = getattr(person_b, 'get_immunity', lambda: 0.5)()
        resistance_bonus = immunity * 0.3
        
        return max(0.05, min(0.7, base_prob - resistance_bonus))
    
    def _apply_effects(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
        success: bool,
    ) -> None:
        """Parásito gana energía, huésped pierde energía."""
        if success:
            # Parásito gana energía
            if relationship.effect_on_a:
                energy_gain = relationship.effect_on_a.energy_change
                if energy_gain > 0:
                    person_a.add_energy(energy_gain)
            
            # Huésped pierde energía
            if relationship.effect_on_b:
                energy_loss = abs(relationship.effect_on_b.energy_change)
                if energy_loss > 0:
                    person_b.spend_energy(energy_loss)


class MechanismFactory:
    """Fábrica de mecanismos.
    
    Mapea MechanismType a instancias de mecanismo.
    """
    
    _mechanisms: Dict[MechanismType, BaseMechanism] = {}
    
    @classmethod
    def get_mechanism(cls, mechanism_type: MechanismType) -> BaseMechanism:
        """Obtiene el mecanismo correspondiente a un tipo.
        
        Args:
            mechanism_type: El tipo de mecanismo.
            
        Returns:
            Instancia del mecanismo. Si no existe, retorna HuntMechanism por defecto.
        """
        if not cls._mechanisms:
            cls._initialize()
        
        if mechanism_type in cls._mechanisms:
            return cls._mechanisms[mechanism_type]
        
        # Por defecto: usar HuntMechanism para mecanismos no implementados
        return cls._mechanisms[MechanismType.HUNT]
    
    @classmethod
    def _initialize(cls) -> None:
        """Inicializa el registro de mecanismos."""
        cls._mechanisms = {
            MechanismType.HUNT: HuntMechanism(),
            MechanismType.AMBUSH: HuntMechanism(),  # Similar a caza
            MechanismType.PACK_HUNTING: HuntMechanism(),  # Similar a caza
            MechanismType.GRAZING: GrazingMechanism(),
            MechanismType.FILTER_FEEDING: GrazingMechanism(),  # Similar a pastoreo
            MechanismType.POLLINATION: PollinationMechanism(),
            MechanismType.SEED_DISPERSAL: PollinationMechanism(),  # Similar a polinización
            MechanismType.RESOURCE_CONSUMPTION: ResourceConsumptionMechanism(),
            MechanismType.TERRITORIAL_DISPLAY: ResourceConsumptionMechanism(),  # Similar a competencia
            MechanismType.CHEMICAL_SUPPRESSION: ResourceConsumptionMechanism(),  # Similar a competencia
            MechanismType.SCAVENGING: ScavengingMechanism(),
            MechanismType.INFECTION: InfectionMechanism(),
        }
    
    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict[str, int]]:
        """Retorna estadísticas de todos los mecanismos."""
        if not cls._mechanisms:
            cls._initialize()
        
        stats = {}
        for mech_type, mechanism in cls._mechanisms.items():
            stats[mech_type.value] = mechanism.get_stats()
        return stats