"""Tests para mecanismos ecológicos."""

import pytest
from unittest.mock import MagicMock

from systems.ecology.mechanisms import (
    BaseMechanism,
    HuntMechanism,
    GrazingMechanism,
    PollinationMechanism,
    ResourceConsumptionMechanism,
    ScavengingMechanism,
    InfectionMechanism,
    MechanismFactory,
)
from systems.ecology.relationship_types import (
    MechanismType,
    InteractionOutcome,
    RelationshipType,
)
from systems.ecology.ecological_relationship import EcologicalRelationship
from systems.ecology.relationship_effect import RelationshipEffect


class TestBaseMechanism:
    """Tests para la clase base abstracta."""
    
    def test_cannot_instantiate_abstract_class(self):
        """BaseMechanism no puede instanciarse directamente."""
        with pytest.raises(TypeError):
            BaseMechanism()  # type: ignore[abstract]
    
    def test_initial_stats_zero(self):
        """Las estadísticas iniciales son cero."""
        mechanism = HuntMechanism()
        stats = mechanism.get_stats()
        
        assert stats["executions"] == 0
        assert stats["successes"] == 0
        assert stats["success_rate"] == 0.0


class TestHuntMechanism:
    """Tests para HuntMechanism (caza activa)."""
    
    @pytest.fixture
    def mechanism(self):
        return HuntMechanism()
    
    @pytest.fixture
    def predator(self):
        """Depredador con tamaño grande."""
        person = MagicMock()
        person.entity_id = 1
        person.species = "wolf"
        person.energy = 50.0
        person.genome.body_size = 0.8
        return person
    
    @pytest.fixture
    def prey(self):
        """Presa con tamaño pequeño."""
        person = MagicMock()
        person.entity_id = 2
        person.species = "rabbit"
        person.energy = 50.0
        person.genome.body_size = 0.3
        return person
    
    @pytest.fixture
    def predation_relationship(self):
        """Relación de depredación."""
        return EcologicalRelationship(
            species_a_id="wolf",
            species_b_id="rabbit",
            relationship_type=RelationshipType.PREDATION,
            mechanism=MechanismType.HUNT,
            intensity=0.7,
            effect_on_a=RelationshipEffect(energy_change=30.0),
            effect_on_b=RelationshipEffect(death_probability=0.6),
        )
    
    @pytest.fixture
    def pending(self):
        """Buffer de cambios pendientes."""
        pending = MagicMock()
        pending.register_death = MagicMock()
        return pending
    
    def test_success_probability_within_bounds(self, mechanism, predator, prey, predation_relationship):
        """La probabilidad de éxito está entre 0.05 y 0.85."""
        prob = mechanism._calculate_success_probability(predator, prey, predation_relationship)
        assert 0.05 <= prob <= 0.85
    
    def test_larger_predator_has_higher_success(self, mechanism, prey, predation_relationship):
        """Depredador más grande tiene mayor probabilidad de éxito."""
        large_predator = MagicMock()
        large_predator.genome.body_size = 0.9
        
        small_predator = MagicMock()
        small_predator.genome.body_size = 0.4
        
        prob_large = mechanism._calculate_success_probability(large_predator, prey, predation_relationship)
        prob_small = mechanism._calculate_success_probability(small_predator, prey, predation_relationship)
        
        assert prob_large > prob_small
    
    def test_successful_hunt_kills_prey(self, mechanism, predator, prey, predation_relationship, pending):
        """Caza exitosa registra la muerte de la presa."""
        # Forzar éxito
        import random
        original_random = random.random
        random.random = lambda: 0.0  # Siempre éxito
        
        try:
            outcome = mechanism.execute(predator, prey, predation_relationship, pending)
            
            assert outcome == InteractionOutcome.SUCCESS
            pending.register_death.assert_called_once_with(
                entity_id=prey.entity_id,
                reason="predation",
            )
        finally:
            random.random = original_random
    
    def test_successful_hunt_gives_energy(self, mechanism, predator, prey, predation_relationship, pending):
        """Caza exitosa da energía al depredador."""
        predator.add_energy = MagicMock()
        
        import random
        original_random = random.random
        random.random = lambda: 0.0  # Siempre éxito
        
        try:
            mechanism.execute(predator, prey, predation_relationship, pending)
            predator.add_energy.assert_called_once_with(30.0)
        finally:
            random.random = original_random
    
    def test_failed_hunt_no_effects(self, mechanism, predator, prey, predation_relationship, pending):
        """Caza fallida no tiene efectos."""
        import random
        original_random = random.random
        random.random = lambda: 0.99  # Siempre fallo
        
        try:
            outcome = mechanism.execute(predator, prey, predation_relationship, pending)
            
            assert outcome == InteractionOutcome.FAILURE
            pending.register_death.assert_not_called()
        finally:
            random.random = original_random


class TestGrazingMechanism:
    """Tests para GrazingMechanism (pastoreo)."""
    
    @pytest.fixture
    def mechanism(self):
        return GrazingMechanism()
    
    @pytest.fixture
    def herbivore(self):
        person = MagicMock()
        person.entity_id = 1
        person.species = "deer"
        person.energy = 50.0
        return person
    
    @pytest.fixture
    def plant(self):
        person = MagicMock()
        person.entity_id = 2
        person.species = "grass"
        person.energy = 80.0
        return person
    
    @pytest.fixture
    def herbivory_relationship(self):
        return EcologicalRelationship(
            species_a_id="deer",
            species_b_id="grass",
            relationship_type=RelationshipType.HERBIVORY,
            mechanism=MechanismType.GRAZING,
            intensity=0.8,
            effect_on_a=RelationshipEffect(energy_change=15.0),
            effect_on_b=RelationshipEffect(energy_change=-10.0),
        )
    
    @pytest.fixture
    def pending(self):
        pending = MagicMock()
        pending.register_death = MagicMock()
        return pending
    
    def test_success_probability_high(self, mechanism, herbivore, plant, herbivory_relationship):
        """Las plantas no huyen, probabilidad alta."""
        prob = mechanism._calculate_success_probability(herbivore, plant, herbivory_relationship)
        assert prob >= 0.7  # Al menos 70%
    
    def test_grazing_gives_energy_to_herbivore(self, mechanism, herbivore, plant, herbivory_relationship, pending):
        """Pastoreo exitoso da energía al herbívoro."""
        herbivore.add_energy = MagicMock()
        plant.spend_energy = MagicMock()
        
        import random
        original_random = random.random
        random.random = lambda: 0.0
        
        try:
            mechanism.execute(herbivore, plant, herbivory_relationship, pending)
            herbivore.add_energy.assert_called_once_with(15.0)
        finally:
            random.random = original_random
    
    def test_grazing_damages_plant(self, mechanism, herbivore, plant, herbivory_relationship, pending):
        """Pastoreo exitoso daña a la planta."""
        herbivore.add_energy = MagicMock()
        plant.spend_energy = MagicMock()
        
        import random
        original_random = random.random
        random.random = lambda: 0.0
        
        try:
            mechanism.execute(herbivore, plant, herbivory_relationship, pending)
            plant.spend_energy.assert_called_once_with(10.0)
        finally:
            random.random = original_random
    
    def test_plant_death_at_zero_energy(self, mechanism, herbivore, herbivory_relationship, pending):
        """Planta muere si se queda sin energía."""
        plant = MagicMock()
        plant.entity_id = 2
        plant.energy = 5.0  # Energía baja
        plant.spend_energy = MagicMock(side_effect=lambda x: setattr(plant, 'energy', plant.energy - x))
        
        herbivore.add_energy = MagicMock()
        
        import random
        original_random = random.random
        random.random = lambda: 0.0
        
        try:
            mechanism.execute(herbivore, plant, herbivory_relationship, pending)
            
            # La planta perdió 10 de energía, quedó en -5
            assert plant.energy <= 0
            pending.register_death.assert_called_once_with(
                entity_id=plant.entity_id,
                reason="consumed",
            )
        finally:
            random.random = original_random


class TestPollinationMechanism:
    """Tests para PollinationMechanism (mutualismo)."""
    
    @pytest.fixture
    def mechanism(self):
        return PollinationMechanism()
    
    @pytest.fixture
    def pollinator(self):
        person = MagicMock()
        person.entity_id = 1
        person.species = "bee"
        return person
    
    @pytest.fixture
    def flower(self):
        person = MagicMock()
        person.entity_id = 2
        person.species = "flower"
        return person
    
    @pytest.fixture
    def mutualism_relationship(self):
        return EcologicalRelationship(
            species_a_id="bee",
            species_b_id="flower",
            relationship_type=RelationshipType.MUTUALISM,
            mechanism=MechanismType.POLLINATION,
            intensity=0.9,
            effect_on_a=RelationshipEffect(energy_change=8.0),
            effect_on_b=RelationshipEffect(energy_change=12.0),
        )
    
    @pytest.fixture
    def pending(self):
        return MagicMock()
    
    def test_success_probability_very_high(self, mechanism, pollinator, flower, mutualism_relationship):
        """La polinización casi siempre ocurre."""
        prob = mechanism._calculate_success_probability(pollinator, flower, mutualism_relationship)
        assert prob >= 0.9
    
    def test_both_benefit(self, mechanism, pollinator, flower, mutualism_relationship, pending):
        """Ambos organismos se benefician."""
        pollinator.add_energy = MagicMock()
        flower.add_energy = MagicMock()
        
        import random
        original_random = random.random
        random.random = lambda: 0.0
        
        try:
            outcome = mechanism.execute(pollinator, flower, mutualism_relationship, pending)
            
            assert outcome == InteractionOutcome.SUCCESS
            pollinator.add_energy.assert_called_once_with(8.0)
            flower.add_energy.assert_called_once_with(12.0)
        finally:
            random.random = original_random


class TestResourceConsumptionMechanism:
    """Tests para ResourceConsumptionMechanism (competencia)."""
    
    @pytest.fixture
    def mechanism(self):
        return ResourceConsumptionMechanism()
    
    @pytest.fixture
    def organism_a(self):
        person = MagicMock()
        person.entity_id = 1
        person.species = "lion"
        return person
    
    @pytest.fixture
    def organism_b(self):
        person = MagicMock()
        person.entity_id = 2
        person.species = "hyena"
        return person
    
    @pytest.fixture
    def competition_relationship(self):
        return EcologicalRelationship(
            species_a_id="lion",
            species_b_id="hyena",
            relationship_type=RelationshipType.COMPETITION,
            mechanism=MechanismType.RESOURCE_CONSUMPTION,
            intensity=0.6,
            effect_on_a=RelationshipEffect(energy_change=-5.0),
            effect_on_b=RelationshipEffect(energy_change=-5.0),
        )
    
    @pytest.fixture
    def pending(self):
        return MagicMock()
    
    def test_always_occurs(self, mechanism, organism_a, organism_b, competition_relationship):
        """La competencia siempre ocurre cuando hay encuentro."""
        prob = mechanism._calculate_success_probability(organism_a, organism_b, competition_relationship)
        assert prob == 1.0
    
    def test_both_lose_energy(self, mechanism, organism_a, organism_b, competition_relationship, pending):
        """Ambos organismos pierden energía."""
        organism_a.spend_energy = MagicMock()
        organism_b.spend_energy = MagicMock()
        
        import random
        original_random = random.random
        random.random = lambda: 0.0
        
        try:
            mechanism.execute(organism_a, organism_b, competition_relationship, pending)
            
            organism_a.spend_energy.assert_called_once_with(5.0)
            organism_b.spend_energy.assert_called_once_with(5.0)
        finally:
            random.random = original_random


class TestScavengingMechanism:
    """Tests para ScavengingMechanism (carroñeo)."""
    
    @pytest.fixture
    def mechanism(self):
        return ScavengingMechanism()
    
    @pytest.fixture
    def scavenger(self):
        person = MagicMock()
        person.entity_id = 1
        person.species = "vulture"
        return person
    
    @pytest.fixture
    def carcass(self):
        person = MagicMock()
        person.entity_id = 2
        person.species = "dead_animal"
        return person
    
    @pytest.fixture
    def scavenging_relationship(self):
        return EcologicalRelationship(
            species_a_id="vulture",
            species_b_id="dead_animal",
            relationship_type=RelationshipType.PREDATION,
            mechanism=MechanismType.SCAVENGING,
            intensity=0.7,
            effect_on_a=RelationshipEffect(energy_change=20.0),
            effect_on_b=RelationshipEffect(),
        )
    
    @pytest.fixture
    def pending(self):
        return MagicMock()
    
    def test_scavenger_gains_energy(self, mechanism, scavenger, carcass, scavenging_relationship, pending):
        """Carroñero gana energía sin matar."""
        scavenger.add_energy = MagicMock()
        
        import random
        original_random = random.random
        random.random = lambda: 0.0
        
        try:
            outcome = mechanism.execute(scavenger, carcass, scavenging_relationship, pending)
            
            assert outcome == InteractionOutcome.SUCCESS
            scavenger.add_energy.assert_called_once_with(20.0)
            # No se registra muerte (ya estaba muerto)
            pending.register_death.assert_not_called()
        finally:
            random.random = original_random


class TestInfectionMechanism:
    """Tests para InfectionMechanism (parasitismo)."""
    
    @pytest.fixture
    def mechanism(self):
        return InfectionMechanism()
    
    @pytest.fixture
    def parasite(self):
        person = MagicMock()
        person.entity_id = 1
        person.species = "tick"
        return person
    
    @pytest.fixture
    def host(self):
        person = MagicMock()
        person.entity_id = 2
        person.species = "dog"
        person.get_immunity = MagicMock(return_value=0.3)
        return person
    
    @pytest.fixture
    def parasitism_relationship(self):
        return EcologicalRelationship(
            species_a_id="tick",
            species_b_id="dog",
            relationship_type=RelationshipType.PARASITISM,
            mechanism=MechanismType.INFECTION,
            intensity=0.5,
            effect_on_a=RelationshipEffect(energy_change=5.0),
            effect_on_b=RelationshipEffect(energy_change=-8.0),
        )
    
    @pytest.fixture
    def pending(self):
        return MagicMock()
    
    def test_immunity_reduces_infection_probability(self, mechanism, parasite, parasitism_relationship):
        """Mayor inmunidad reduce probabilidad de infección."""
        low_immunity_host = MagicMock()
        low_immunity_host.get_immunity = MagicMock(return_value=0.1)
        
        high_immunity_host = MagicMock()
        high_immunity_host.get_immunity = MagicMock(return_value=0.9)
        
        prob_low = mechanism._calculate_success_probability(parasite, low_immunity_host, parasitism_relationship)
        prob_high = mechanism._calculate_success_probability(parasite, high_immunity_host, parasitism_relationship)
        
        assert prob_low > prob_high
    
    def test_successful_infection_effects(self, mechanism, parasite, host, parasitism_relationship, pending):
        """Infección exitosa transfiere energía."""
        parasite.add_energy = MagicMock()
        host.spend_energy = MagicMock()
        
        import random
        original_random = random.random
        random.random = lambda: 0.0
        
        try:
            outcome = mechanism.execute(parasite, host, parasitism_relationship, pending)
            
            assert outcome == InteractionOutcome.SUCCESS
            parasite.add_energy.assert_called_once_with(5.0)
            host.spend_energy.assert_called_once_with(8.0)
        finally:
            random.random = original_random


class TestMechanismFactory:
    """Tests para MechanismFactory."""
    
    def test_get_hunt_mechanism(self):
        """HuntMechanism se obtiene correctamente."""
        mechanism = MechanismFactory.get_mechanism(MechanismType.HUNT)
        assert isinstance(mechanism, HuntMechanism)
    
    def test_get_grazing_mechanism(self):
        """GrazingMechanism se obtiene correctamente."""
        mechanism = MechanismFactory.get_mechanism(MechanismType.GRAZING)
        assert isinstance(mechanism, GrazingMechanism)
    
    def test_get_pollination_mechanism(self):
        """PollinationMechanism se obtiene correctamente."""
        mechanism = MechanismFactory.get_mechanism(MechanismType.POLLINATION)
        assert isinstance(mechanism, PollinationMechanism)
    
    def test_get_resource_consumption_mechanism(self):
        """ResourceConsumptionMechanism se obtiene correctamente."""
        mechanism = MechanismFactory.get_mechanism(MechanismType.RESOURCE_CONSUMPTION)
        assert isinstance(mechanism, ResourceConsumptionMechanism)
    
    def test_get_scavenging_mechanism(self):
        """ScavengingMechanism se obtiene correctamente."""
        mechanism = MechanismFactory.get_mechanism(MechanismType.SCAVENGING)
        assert isinstance(mechanism, ScavengingMechanism)
    
    def test_get_infection_mechanism(self):
        """InfectionMechanism se obtiene correctamente."""
        mechanism = MechanismFactory.get_mechanism(MechanismType.INFECTION)
        assert isinstance(mechanism, InfectionMechanism)
    
    def test_ambush_maps_to_hunt(self):
        """Ambush usa HuntMechanism como fallback."""
        mechanism = MechanismFactory.get_mechanism(MechanismType.AMBUSH)
        assert isinstance(mechanism, HuntMechanism)
    
    def test_pack_hunting_maps_to_hunt(self):
        """PackHunting usa HuntMechanism como fallback."""
        mechanism = MechanismFactory.get_mechanism(MechanismType.PACK_HUNTING)
        assert isinstance(mechanism, HuntMechanism)
    
    def test_get_all_stats(self):
        """Estadísticas de todos los mecanismos están disponibles."""
        stats = MechanismFactory.get_all_stats()
        
        assert "hunt" in stats
        assert "grazing" in stats
        assert "pollination" in stats
        assert "resource_consumption" in stats
        assert "scavenging" in stats
        assert "infection" in stats
    
    def test_stats_structure(self):
        """Las estadísticas tienen la estructura correcta."""
        stats = MechanismFactory.get_all_stats()
        
        for mechanism_name, mechanism_stats in stats.items():
            assert "executions" in mechanism_stats
            assert "successes" in mechanism_stats
            assert "success_rate" in mechanism_stats


class TestMechanismStatistics:
    """Tests para las estadísticas de mecanismos."""
    
    def test_stats_update_on_execution(self):
        """Las estadísticas se actualizan tras ejecutar."""
        mechanism = HuntMechanism()
        
        predator = MagicMock()
        predator.genome.body_size = 0.8
        
        prey = MagicMock()
        prey.genome.body_size = 0.3
        prey.entity_id = 2
        
        relationship = EcologicalRelationship(
            species_a_id="wolf",
            species_b_id="rabbit",
            relationship_type=RelationshipType.PREDATION,
            mechanism=MechanismType.HUNT,
            intensity=0.7,
        )
        
        pending = MagicMock()
        
        import random
        original_random = random.random
        random.random = lambda: 0.0  # Siempre éxito
        
        try:
            mechanism.execute(predator, prey, relationship, pending)
            
            stats = mechanism.get_stats()
            assert stats["executions"] == 1
            assert stats["successes"] == 1
            assert stats["success_rate"] == 1.0
        finally:
            random.random = original_random
    
    def test_stats_track_failures(self):
        """Las estadísticas rastrean fallos correctamente."""
        mechanism = HuntMechanism()
        
        predator = MagicMock()
        predator.genome.body_size = 0.8
        
        prey = MagicMock()
        prey.genome.body_size = 0.3
        prey.entity_id = 2
        
        relationship = EcologicalRelationship(
            species_a_id="wolf",
            species_b_id="rabbit",
            relationship_type=RelationshipType.PREDATION,
            mechanism=MechanismType.HUNT,
            intensity=0.7,
        )
        
        pending = MagicMock()
        
        import random
        original_random = random.random
        random.random = lambda: 0.99  # Siempre fallo
        
        try:
            mechanism.execute(predator, prey, relationship, pending)
            
            stats = mechanism.get_stats()
            assert stats["executions"] == 1
            assert stats["successes"] == 0
            assert stats["success_rate"] == 0.0
        finally:
            random.random = original_random