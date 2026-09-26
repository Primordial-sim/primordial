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

    @staticmethod
    def _get_trait(person: 'Person', trait_name: str, default: float = 0.5) -> float:
        """Lee un rasgo del genoma en escala [0, 1] con 0.5 neutro.
        
        Coherente con el uso de ``body_size`` en HuntMechanism y de
        ``get_immunity()`` en InfectionMechanism. Si el rasgo no existe
        o no es numérico, retorna el valor por defecto.
        
        Args:
            person: El organismo cuyo rasgo se consulta.
            trait_name: Identificador del rasgo (ej: "camouflage").
            default: Valor por defecto si el rasgo no existe.
            
        Returns:
            Valor del rasgo acotado a [0.0, 1.0].
        """
        genome = getattr(person, "genome", None)
        value = getattr(genome, trait_name, default)
        if not isinstance(value, (int, float)):
            return default
        return max(0.0, min(1.0, float(value)))
    
class AmbushMechanism(BaseMechanism):
    """Mecanismo de emboscada sigilosa (depredación por sorpresa).
    
    El depredador espera oculto y ataca por sorpresa. A diferencia de la
    caza activa, el éxito depende del sigilo del atacante y de la capacidad
    de detección de la presa, no de la persecución.
    
    La probabilidad de éxito depende de:
    - Intensidad de la relación
    - Camuflaje e instinto depredador del emboscador
    - Visión, oído y olfato de la presa (detección temprana)
    
    Coste: si la emboscada falla, el emboscador pierde la energía invertida
    en el acecho (una fracción de la ganancia potencial).
    """
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        """Probabilidad basada en sigilo del atacante vs detección de la presa."""
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
        """Si éxito: presa muere, depredador gana energía. Si fallo: coste de acecho."""
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
            # La presa escapa: el emboscador pierde lo invertido en el acecho
            if relationship.effect_on_a and relationship.effect_on_a.energy_change > 0:
                stakeout_cost = relationship.effect_on_a.energy_change * 0.1
                person_a.spend_energy(stakeout_cost)


class PackHuntingMechanism(BaseMechanism):
    """Mecanismo de caza coordinada en manada.
    
    La cooperación entre individuos permite abatir presas mayores que las
    que un solo depredador podría cazar. La coordinación se modela mediante
    los rasgos ``pack_behavior`` y ``cooperation`` del atacante.
    
    La probabilidad de éxito depende de:
    - Intensidad de la relación
    - Coordinación de manada del atacante
    - Tamaño relativo, cuya penalización se reduce con la coordinación
    
    Coste: el botín se reparte entre la manada, por lo que la ganancia
    individual es menor que en la caza en solitario.
    """
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        """Probabilidad basada en coordinación de manada y tamaño relativo."""
        pack = (
            self._get_trait(person_a, "pack_behavior")
            + self._get_trait(person_a, "cooperation")
        ) / 2.0
        
        base_prob = relationship.intensity * 0.55 + pack * 0.25
        
        size_a = self._get_trait(person_a, "body_size")
        size_b = self._get_trait(person_b, "body_size")
        size_diff = size_b - size_a  # Positivo si la presa es mayor
        
        if size_diff > 0:
            # La manada compensa el tamaño de la presa
            size_term = -size_diff * 0.30 * (1.0 - 0.75 * pack)
        else:
            size_term = -size_diff * 0.20  # Presa menor: bonus
        
        return max(0.05, min(0.90, base_prob + size_term))
    
    def _apply_effects(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
        pending: 'PendingChanges',
        success: bool,
    ) -> None:
        """Si éxito: presa muere, ganancia individual reducida (botín repartido)."""
        if success:
            pending.register_death(
                entity_id=person_b.entity_id,
                reason="predation",
            )
            if relationship.effect_on_a:
                energy_gain = relationship.effect_on_a.energy_change
                if energy_gain > 0:
                    # El botín se reparte entre los miembros de la manada
                    person_a.add_energy(energy_gain * 0.7)
        # Si falla: la presa escapa, sin efectos


class TerritorialDisplayMechanism(BaseMechanism):
    """Mecanismo de exhibición territorial (competencia ritualizada).
    
    Los competidores resuelven el conflicto mediante exhibiciones
    (posturas, vocalizaciones, marcas) sin contacto físico. Nadie muere:
    el perdedor se retira del territorio.
    
    En este mecanismo, ``success`` significa "el organismo A gana la
    exhibición". La probabilidad compara el poder de exhibición de ambos
    (territorialidad, agresividad y tamaño).
    
    Coste: ambos pagan el coste de la exhibición (menor que el combate
    directo); el perdedor añade el coste de retirada y estrés.
    """
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        """Probabilidad de que A gane la exhibición (poder relativo)."""
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
        """Ambos pagan exhibición; el perdedor paga retirada y estrés. Sin muertes."""
        cost_a = abs(relationship.effect_on_a.energy_change) if relationship.effect_on_a else 0.0
        cost_b = abs(relationship.effect_on_b.energy_change) if relationship.effect_on_b else 0.0
        
        display_ratio = 0.4   # Coste de exhibir sin combatir
        retreat_ratio = 0.6   # Coste añadido de retirada y estrés
        
        if success:  # A gana la exhibición
            person_a.spend_energy(cost_a * display_ratio)
            person_b.spend_energy(cost_b * (display_ratio + retreat_ratio))
        else:  # B gana la exhibición
            person_a.spend_energy(cost_a * (display_ratio + retreat_ratio))
            person_b.spend_energy(cost_b * display_ratio)


class ChemicalSuppressionMechanism(BaseMechanism):
    """Mecanismo de supresión química (alelopatía).
    
    El organismo A libera compuestos tóxicos al entorno que inhiben el
    crecimiento o la actividad de B. Es una competencia indirecta: no hay
    contacto ni persecución.
    
    La probabilidad de éxito depende de:
    - Intensidad de la relación
    - Potencia química del productor (rasgo ``venom``)
    - Inmunidad del organismo objetivo
    
    Coste: producir toxinas consume energía siempre; si la supresión falla,
    el productor pierde solo la mitad del coste. La muerte del objetivo no
    se registra aquí: emerge del sistema de energía por inanición.
    """
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        """Probabilidad basada en potencia química vs inmunidad del objetivo."""
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
        """Productor paga coste de toxinas; objetivo pierde energía si hay efecto."""
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
            # Toxinas liberadas pero sin efecto: mitad del coste
            person_a.spend_energy(production_cost * 0.5)
class FilterFeedingMechanism(BaseMechanism):
    """Mecanismo de filtrado (alimentación por filtro).
    
    El organismo A filtra microorganismos y partículas nutritivas del agua
    o del sustrato. Es un mecanismo pasivo: casi siempre obtiene algo de
    alimento cuando hay encuentro con el recurso.
    
    La probabilidad de éxito depende de:
    - Intensidad de la relación
    - Capacidad de desplazamiento en el medio (``swimming``, ``mobility``)
    
    El organismo B (recurso filtrado) pierde energía si la relación define
    un efecto sobre él; si se agota, muere como en el pastoreo.
    """
    
    def _calculate_success_probability(
        self,
        person_a: 'Person',
        person_b: 'Person',
        relationship: 'EcologicalRelationship',
    ) -> float:
        """Probabilidad alta: el filtrado es pasivo y casi siempre obtiene algo."""
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
        """Filtrador gana energía; el recurso pierde energía y puede agotarse."""
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
        # Si falla: corriente sin nutrientes suficientes, sin efectos

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
        """Parásito gana energía, huésped pierde energía y puede infectarse.
        
        Si la infección tiene éxito, además del coste energético, se inocula
        un patógeno real en el huésped. Esto conecta el parasitismo ecológico
        con el sistema epidemiológico (DiseaseSystem).
        
        La familia del patógeno se deriva de la especie del parásito
        (ej: "Parasite_wolf"). Si el huésped ya tiene una infección activa
        de esa familia, no se reinfecta (solo paga el coste energético).
        """
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
            
            # Inocular patógeno si el huésped no está ya infectado
            parasite_family = f"Parasite_{person_a.species}"
            
            # Verificar si el huésped ya tiene una infección activa de esa familia
            already_infected = False
            if hasattr(person_b, 'active_infections'):
                for path_id in person_b.active_infections.keys():
                    if path_id.startswith(f"{parasite_family}_"):
                        already_infected = True
                        break
            
            # Si no está infectado, inocular el patógeno
            if not already_infected:
                pathogen = Pathogen.create_random_variant(parasite_family)
                if hasattr(pending, 'register_infection'):
                    pending.register_infection(person_b.entity_id, pathogen)


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
            MechanismType.AMBUSH: AmbushMechanism(),
            MechanismType.PACK_HUNTING: PackHuntingMechanism(),
            MechanismType.GRAZING: GrazingMechanism(),
            MechanismType.FILTER_FEEDING: FilterFeedingMechanism(),
            MechanismType.POLLINATION: PollinationMechanism(),
            MechanismType.SEED_DISPERSAL: PollinationMechanism(),  # Similar a polinización
            MechanismType.RESOURCE_CONSUMPTION: ResourceConsumptionMechanism(),
            MechanismType.TERRITORIAL_DISPLAY: TerritorialDisplayMechanism(),
            MechanismType.CHEMICAL_SUPPRESSION: ChemicalSuppressionMechanism(),
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