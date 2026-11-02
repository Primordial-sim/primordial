"""Mecanismos de ejecución de relaciones ecológicas.

Cada mecanismo encapsula la lógica específica de un tipo de interacción.
El mecanismo describe CÓMO se ejecuta la relación, no QUÉ relación es.

Arquitectura:
    BaseMechanism (abstracta)
    ├── HuntMechanism          → Depredación activa
    ├── AmbushMechanism        → Emboscada sigilosa
    ├── PackHuntingMechanism   → Caza coordinada en manada
    ├── GrazingMechanism       → Pastoreo / herbivoría
    ├── FilterFeedingMechanism → Filtrado de agua
    ├── PollinationMechanism   → Polinización (mutualismo)
    ├── ResourceConsumptionMechanism → Competencia
    ├── TerritorialDisplayMechanism  → Exhibición territorial
    ├── ChemicalSuppressionMechanism → Supresión química (alelopatía)
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

from systems.diseases.pathogen import Pathogen

if TYPE_CHECKING:
    from entities.person.person import Person
    from core.state.pending_changes import PendingChanges
    from systems.ecology.ecological_relationship import EcologicalRelationship


class BaseMechanism(ABC):
    """Clase base abstracta para todos los mecanismos de interacción."""
    
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
        pass
    
    def execute(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
    ) -> InteractionOutcome:
        self._total_executions += 1
        
        success_prob = self._calculate_success_probability(person_a, person_b, relationship)
        
        roll = random.random()
        success = roll < success_prob
        
        self._apply_effects(person_a, person_b, relationship, pending, success)
        
        if success:
            self._total_successes += 1
            return InteractionOutcome.SUCCESS
        else:
            return InteractionOutcome.FAILURE
    
    @property
    def success_rate(self) -> float:
        if self._total_executions == 0:
            return 0.0
        return self._total_successes / self._total_executions
    
    def get_stats(self) -> Dict[str, object]:
        return {
            "executions": self._total_executions,
            "successes": self._total_successes,
            "success_rate": round(self.success_rate, 3),
        }

    @staticmethod
    def _get_trait(person: 'Person', trait_name: str, default: float = 0.5) -> float:
        genome = getattr(person, "genome", None)
        value = getattr(genome, trait_name, default)
        if not isinstance(value, (int, float)):
            return default
        return max(0.0, min(1.0, float(value)))


class AmbushMechanism(BaseMechanism):
    """Mecanismo de emboscada sigilosa."""
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        base_prob = relationship.intensity * 0.75
        
        stealth = (
            self._get_trait(person_a, "camouflage")
            + self._get_trait(person_a, "predatory_instinct")
        ) / 2.0
        detection = (
            self._get_trait(person_b, "vision")
            + self._get_trait(person_b, "hearing")
            + self._get_trait(person_b, "smell")
        ) / 3.0
        
        prob = base_prob + stealth * 0.15 - detection * 0.15
        return max(0.05, min(0.90, prob))
    
    def _apply_effects(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
        success: bool,
    ) -> None:
        if success:
            pending.register_death(
                entity_id=person_b.entity_id,
                reason="predation",
            )
            if relationship.effect_on_a:
                energy_gain = relationship.effect_on_a.energy_change
                if energy_gain > 0:
                    person_a.add_energy(energy_gain)
        else:
            if relationship.effect_on_a and relationship.effect_on_a.energy_change > 0:
                stakeout_cost = relationship.effect_on_a.energy_change * 0.1
                person_a.spend_energy(stakeout_cost)


class PackHuntingMechanism(BaseMechanism):
    """Mecanismo de caza coordinada en manada."""
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        pack = (
            self._get_trait(person_a, "pack_behavior")
            + self._get_trait(person_a, "cooperation")
        ) / 2.0
        
        base_prob = relationship.intensity * 0.55 + pack * 0.25
        
        size_a = self._get_trait(person_a, "body_size")
        size_b = self._get_trait(person_b, "body_size")
        size_diff = size_b - size_a
        
        if size_diff > 0:
            size_term = -size_diff * 0.30 * (1.0 - 0.75 * pack)
        else:
            size_term = -size_diff * 0.20
        
        return max(0.05, min(0.90, base_prob + size_term))
    
    def _apply_effects(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
        success: bool,
    ) -> None:
        if success:
            pending.register_death(
                entity_id=person_b.entity_id,
                reason="predation",
            )
            if relationship.effect_on_a:
                energy_gain = relationship.effect_on_a.energy_change
                if energy_gain > 0:
                    person_a.add_energy(energy_gain * 0.7)


class TerritorialDisplayMechanism(BaseMechanism):
    """Mecanismo de exhibición territorial."""
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        power_a = (
            self._get_trait(person_a, "territoriality")
            + self._get_trait(person_a, "aggressiveness")
            + self._get_trait(person_a, "body_size")
        ) / 3.0
        power_b = (
            self._get_trait(person_b, "territoriality")
            + self._get_trait(person_b, "aggressiveness")
            + self._get_trait(person_b, "body_size")
        ) / 3.0
        
        prob = 0.5 + (power_a - power_b) * 0.4
        return max(0.10, min(0.90, prob))
    
    def _apply_effects(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
        success: bool,
    ) -> None:
        cost_a = abs(relationship.effect_on_a.energy_change) if relationship.effect_on_a else 0.0
        cost_b = abs(relationship.effect_on_b.energy_change) if relationship.effect_on_b else 0.0
        
        display_ratio = 0.4
        retreat_ratio = 0.6
        
        if success:
            person_a.spend_energy(cost_a * display_ratio)
            person_b.spend_energy(cost_b * (display_ratio + retreat_ratio))
        else:
            person_a.spend_energy(cost_a * (display_ratio + retreat_ratio))
            person_b.spend_energy(cost_b * display_ratio)


class ChemicalSuppressionMechanism(BaseMechanism):
    """Mecanismo de supresión química."""
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        base_prob = relationship.intensity * 0.7
        potency = self._get_trait(person_a, "venom")
        resistance = self._get_trait(person_b, "immunity")
        
        prob = base_prob + potency * 0.15 - resistance * 0.15
        return max(0.05, min(0.85, prob))
    
    def _apply_effects(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
        success: bool,
    ) -> None:
        if relationship.effect_on_a and relationship.effect_on_a.energy_change < 0:
            production_cost = abs(relationship.effect_on_a.energy_change)
        else:
            production_cost = 0.5
        
        if success:
            person_a.spend_energy(production_cost)
            if relationship.effect_on_b:
                damage = abs(relationship.effect_on_b.energy_change)
                if damage > 0:
                    person_b.spend_energy(damage)
        else:
            person_a.spend_energy(production_cost * 0.5)


class FilterFeedingMechanism(BaseMechanism):
    """Mecanismo de filtrado."""
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        base_prob = relationship.intensity * 0.9
        flow_access = (
            self._get_trait(person_a, "swimming")
            + self._get_trait(person_a, "mobility")
        ) / 2.0
        
        prob = base_prob + flow_access * 0.05
        return max(0.10, min(0.95, prob))
    
    def _apply_effects(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
        success: bool,
    ) -> None:
        if success:
            if relationship.effect_on_a:
                energy_gain = relationship.effect_on_a.energy_change
                if energy_gain > 0:
                    person_a.add_energy(energy_gain)
            
            if relationship.effect_on_b:
                damage = abs(relationship.effect_on_b.energy_change)
                if damage > 0:
                    person_b.spend_energy(damage)
                    
                    if person_b.energy <= 0:
                        pending.register_death(
                            entity_id=person_b.entity_id,
                            reason="consumed",
                        )


class HuntMechanism(BaseMechanism):
    """Mecanismo de caza activa (depredación)."""
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        base_prob = relationship.intensity * 0.7
        
        size_a = getattr(person_a.genome, 'body_size', 0.5)
        size_b = getattr(person_b.genome, 'body_size', 0.5)
        
        if size_a > size_b:
            size_bonus = (size_a - size_b) * 0.2
        else:
            size_bonus = (size_a - size_b) * 0.3
        
        return max(0.05, min(0.85, base_prob + size_bonus))
    
    def _apply_effects(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
        success: bool,
    ) -> None:
        if success:
            pending.register_death(
                entity_id=person_b.entity_id,
                reason="predation",
            )
            
            if relationship.effect_on_a:
                energy_gain = relationship.effect_on_a.energy_change
                if energy_gain > 0:
                    person_a.add_energy(energy_gain)


class GrazingMechanism(BaseMechanism):
    """Mecanismo de pastoreo (herbivoría)."""
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        return relationship.intensity * 0.9
    
    def _apply_effects(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
        success: bool,
    ) -> None:
        if success:
            if relationship.effect_on_a:
                energy_gain = relationship.effect_on_a.energy_change
                if energy_gain > 0:
                    person_a.add_energy(energy_gain)
            
            if relationship.effect_on_b:
                damage = abs(relationship.effect_on_b.energy_change)
                if damage > 0:
                    person_b.spend_energy(damage)
                    
                    if person_b.energy <= 0:
                        pending.register_death(
                            entity_id=person_b.entity_id,
                            reason="consumed",
                        )


class PollinationMechanism(BaseMechanism):
    """Mecanismo de polinización (mutualismo)."""
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        return 0.95
    
    def _apply_effects(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
        success: bool,
    ) -> None:
        if success:
            if relationship.effect_on_a:
                energy_gain = relationship.effect_on_a.energy_change
                if energy_gain > 0:
                    person_a.add_energy(energy_gain)
            
            if relationship.effect_on_b:
                energy_gain = relationship.effect_on_b.energy_change
                if energy_gain > 0:
                    person_b.add_energy(energy_gain)


class ResourceConsumptionMechanism(BaseMechanism):
    """Mecanismo de competencia por recursos."""
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        return 1.0
    
    def _apply_effects(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
        success: bool,
    ) -> None:
        if success:
            if relationship.effect_on_a:
                energy_loss = abs(relationship.effect_on_a.energy_change)
                if energy_loss > 0:
                    person_a.spend_energy(energy_loss)
            
            if relationship.effect_on_b:
                energy_loss = abs(relationship.effect_on_b.energy_change)
                if energy_loss > 0:
                    person_b.spend_energy(energy_loss)


class ScavengingMechanism(BaseMechanism):
    """Mecanismo de carroñeo."""
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        return relationship.intensity * 0.8
    
    def _apply_effects(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
        success: bool,
    ) -> None:
        if success:
            if relationship.effect_on_a:
                energy_gain = relationship.effect_on_a.energy_change
                if energy_gain > 0:
                    person_a.add_energy(energy_gain)


class InfectionMechanism(BaseMechanism):
    """Mecanismo de infección parasitaria."""
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        base_prob = relationship.intensity * 0.6
        
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
        if success:
            if relationship.effect_on_a:
                energy_gain = relationship.effect_on_a.energy_change
                if energy_gain > 0:
                    person_a.add_energy(energy_gain)
            
            if relationship.effect_on_b:
                energy_loss = abs(relationship.effect_on_b.energy_change)
                if energy_loss > 0:
                    person_b.spend_energy(energy_loss)
            
            parasite_family = f"Parasite_{person_a.species}"
            
            already_infected = False
            if hasattr(person_b, 'active_infections'):
                for path_id in person_b.active_infections.keys():
                    if path_id.startswith(f"{parasite_family}_"):
                        already_infected = True
                        break
            
            if not already_infected:
                pathogen = Pathogen.create_random_variant(parasite_family)
                if hasattr(pending, 'register_infection'):
                    pending.register_infection(person_b.entity_id, pathogen)


class MechanismFactory:
    """Fábrica de mecanismos."""
    
    _mechanisms: Dict[MechanismType, BaseMechanism] = {}
    
    @classmethod
    def get_mechanism(cls, mechanism_type: MechanismType) -> BaseMechanism:
        if not cls._mechanisms:
            cls._initialize()
        
        if mechanism_type in cls._mechanisms:
            return cls._mechanisms[mechanism_type]
        
        return cls._mechanisms[MechanismType.HUNT]
    
    @classmethod
    def _initialize(cls) -> None:
        cls._mechanisms = {
            MechanismType.HUNT: HuntMechanism(),
            MechanismType.AMBUSH: AmbushMechanism(),
            MechanismType.PACK_HUNTING: PackHuntingMechanism(),
            MechanismType.GRAZING: GrazingMechanism(),
            MechanismType.FILTER_FEEDING: FilterFeedingMechanism(),
            MechanismType.POLLINATION: PollinationMechanism(),
            MechanismType.SEED_DISPERSAL: PollinationMechanism(),
            MechanismType.RESOURCE_CONSUMPTION: ResourceConsumptionMechanism(),
            MechanismType.TERRITORIAL_DISPLAY: TerritorialDisplayMechanism(),
            MechanismType.CHEMICAL_SUPPRESSION: ChemicalSuppressionMechanism(),
            MechanismType.SCAVENGING: ScavengingMechanism(),
            MechanismType.INFECTION: InfectionMechanism(),
        }
    
    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict[str, int]]:
        if not cls._mechanisms:
            cls._initialize()
        
        stats = {}
        for mech_type, mechanism in cls._mechanisms.items():
            stats[mech_type.value] = mechanism.get_stats()
        return stats