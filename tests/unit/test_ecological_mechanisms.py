"""Tests para mecanismos ecológicos."""

import random

import pytest
from unittest.mock import MagicMock

from systems.ecology.mechanisms import (
    BaseMechanism,
    HuntMechanism,
    AmbushMechanism,
    PackHuntingMechanism,
    GrazingMechanism,
    FilterFeedingMechanism,
    PollinationMechanism,
    ResourceConsumptionMechanism,
    TerritorialDisplayMechanism,
    ChemicalSuppressionMechanism,
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

class TestAmbushMechanism:
    """Tests para AmbushMechanism (emboscada sigilosa)."""
    
    @pytest.fixture
    def mechanism(self):
        return AmbushMechanism()
    
    @pytest.fixture
    def ambusher(self):
        """Emboscador sigiloso."""
        person = MagicMock()
        person.entity_id = 1
        person.species = "panther"
        person.energy = 50.0
        person.genome.camouflage = 0.9
        person.genome.predatory_instinct = 0.9
        return person
    
    @pytest.fixture
    def prey(self):
        """Presa con detección baja."""
        person = MagicMock()
        person.entity_id = 2
        person.species = "deer"
        person.energy = 50.0
        person.genome.vision = 0.3
        person.genome.hearing = 0.3
        person.genome.smell = 0.3
        return person
    
    @pytest.fixture
    def relationship(self):
        return EcologicalRelationship(
            species_a_id="panther",
            species_b_id="deer",
            relationship_type=RelationshipType.PREDATION,
            mechanism=MechanismType.AMBUSH,
            intensity=0.7,
            effect_on_a=RelationshipEffect(energy_change=30.0),
            effect_on_b=RelationshipEffect(death_probability=1.0),
        )
    
    @pytest.fixture
    def pending(self):
        return MagicMock()
    
    def test_probability_within_bounds(self, mechanism, ambusher, prey, relationship):
        """La probabilidad está acotada a [0.05, 0.90]."""
        prob = mechanism._calculate_success_probability(ambusher, prey, relationship)
        assert 0.05 <= prob <= 0.90
    
    def test_stealthy_ambusher_beats_clumsy(self, mechanism, prey, relationship):
        """Más camuflaje implica mayor probabilidad de éxito."""
        stealthy = MagicMock()
        stealthy.genome.camouflage = 0.9
        stealthy.genome.predatory_instinct = 0.9
        
        clumsy = MagicMock()
        clumsy.genome.camouflage = 0.1
        clumsy.genome.predatory_instinct = 0.1
        
        prob_stealthy = mechanism._calculate_success_probability(stealthy, prey, relationship)
        prob_clumsy = mechanism._calculate_success_probability(clumsy, prey, relationship)
        
        assert prob_stealthy > prob_clumsy
    
    def test_alert_prey_lowers_success(self, mechanism, ambusher, relationship):
        """Presa con sentidos agudos reduce la probabilidad de emboscada."""
        alert_prey = MagicMock()
        alert_prey.genome.vision = 0.9
        alert_prey.genome.hearing = 0.9
        alert_prey.genome.smell = 0.9
        
        oblivious_prey = MagicMock()
        oblivious_prey.genome.vision = 0.1
        oblivious_prey.genome.hearing = 0.1
        oblivious_prey.genome.smell = 0.1
        
        prob_alert = mechanism._calculate_success_probability(ambusher, alert_prey, relationship)
        prob_oblivious = mechanism._calculate_success_probability(ambusher, oblivious_prey, relationship)
        
        assert prob_oblivious > prob_alert
    
    def test_successful_ambush_kills_prey(self, mechanism, ambusher, prey, relationship, pending, monkeypatch):
        """Emboscada exitosa mata a la presa y da energía."""
        monkeypatch.setattr(random, "random", lambda: 0.0)
        
        outcome = mechanism.execute(ambusher, prey, relationship, pending)
        
        assert outcome == InteractionOutcome.SUCCESS
        pending.register_death.assert_called_once_with(
            entity_id=prey.entity_id,
            reason="predation",
        )
        ambusher.add_energy.assert_called_once_with(30.0)
    
    def test_failed_ambush_costs_stakeout(self, mechanism, ambusher, prey, relationship, pending, monkeypatch):
        """Emboscada fallida: la presa vive y el emboscador paga el acecho."""
        monkeypatch.setattr(random, "random", lambda: 1.0)
        
        outcome = mechanism.execute(ambusher, prey, relationship, pending)
        
        assert outcome == InteractionOutcome.FAILURE
        pending.register_death.assert_not_called()
        ambusher.spend_energy.assert_called_once_with(3.0)  # 10% de 30


class TestPackHuntingMechanism:
    """Tests para PackHuntingMechanism (caza en manada)."""
    
    @pytest.fixture
    def mechanism(self):
        return PackHuntingMechanism()
    
    @pytest.fixture
    def coordinated_hunter(self):
        """Depredador social coordinado."""
        person = MagicMock()
        person.entity_id = 1
        person.species = "wolf"
        person.energy = 50.0
        person.genome.pack_behavior = 0.9
        person.genome.cooperation = 0.9
        person.genome.body_size = 0.5
        return person
    
    @pytest.fixture
    def large_prey(self):
        """Presa más grande que el depredador."""
        person = MagicMock()
        person.entity_id = 2
        person.species = "bison"
        person.energy = 50.0
        person.genome.body_size = 0.9
        return person
    
    @pytest.fixture
    def relationship(self):
        return EcologicalRelationship(
            species_a_id="wolf",
            species_b_id="bison",
            relationship_type=RelationshipType.PREDATION,
            mechanism=MechanismType.PACK_HUNTING,
            intensity=0.7,
            effect_on_a=RelationshipEffect(energy_change=30.0),
            effect_on_b=RelationshipEffect(death_probability=1.0),
        )
    
    @pytest.fixture
    def pending(self):
        return MagicMock()
    
    def test_probability_within_bounds(self, mechanism, coordinated_hunter, large_prey, relationship):
        """La probabilidad está acotada a [0.05, 0.90]."""
        prob = mechanism._calculate_success_probability(coordinated_hunter, large_prey, relationship)
        assert 0.05 <= prob <= 0.90
    
    def test_pack_offsets_prey_size(self, mechanism, large_prey, relationship):
        """La coordinación reduce la penalización por presa más grande."""
        pack_hunter = MagicMock()
        pack_hunter.genome.pack_behavior = 0.9
        pack_hunter.genome.cooperation = 0.9
        pack_hunter.genome.body_size = 0.5
        
        lone_hunter = MagicMock()
        lone_hunter.genome.pack_behavior = 0.1
        lone_hunter.genome.cooperation = 0.1
        lone_hunter.genome.body_size = 0.5
        
        prob_pack = mechanism._calculate_success_probability(pack_hunter, large_prey, relationship)
        prob_lone = mechanism._calculate_success_probability(lone_hunter, large_prey, relationship)
        
        assert prob_pack > prob_lone
    
    def test_success_shares_spoils(self, mechanism, coordinated_hunter, large_prey, relationship, pending, monkeypatch):
        """Éxito: presa muere y la ganancia individual es el 70%."""
        monkeypatch.setattr(random, "random", lambda: 0.0)
        
        outcome = mechanism.execute(coordinated_hunter, large_prey, relationship, pending)
        
        assert outcome == InteractionOutcome.SUCCESS
        pending.register_death.assert_called_once()
        coordinated_hunter.add_energy.assert_called_once_with(21.0)  # 30 * 0.7


class TestTerritorialDisplayMechanism:
    """Tests para TerritorialDisplayMechanism (exhibición territorial)."""
    
    @pytest.fixture
    def mechanism(self):
        return TerritorialDisplayMechanism()
    
    @pytest.fixture
    def dominant(self):
        person = MagicMock()
        person.entity_id = 1
        person.species = "lion"
        person.energy = 50.0
        person.genome.territoriality = 0.9
        person.genome.aggressiveness = 0.9
        person.genome.body_size = 0.8
        return person
    
    @pytest.fixture
    def subordinate(self):
        person = MagicMock()
        person.entity_id = 2
        person.species = "lion"
        person.energy = 50.0
        person.genome.territoriality = 0.2
        person.genome.aggressiveness = 0.2
        person.genome.body_size = 0.5
        return person
    
    @pytest.fixture
    def relationship(self):
        return EcologicalRelationship(
            species_a_id="lion",
            species_b_id="lion",
            relationship_type=RelationshipType.COMPETITION,
            mechanism=MechanismType.TERRITORIAL_DISPLAY,
            intensity=0.6,
            effect_on_a=RelationshipEffect(energy_change=-10.0),
            effect_on_b=RelationshipEffect(energy_change=-10.0),
        )
    
    @pytest.fixture
    def pending(self):
        return MagicMock()
    
    def test_probability_within_bounds(self, mechanism, dominant, subordinate, relationship):
        """La probabilidad está acotada a [0.10, 0.90]."""
        prob = mechanism._calculate_success_probability(dominant, subordinate, relationship)
        assert 0.10 <= prob <= 0.90
    
    def test_dominant_favored(self, mechanism, dominant, subordinate, relationship):
        """El organismo con más poder de exhibición tiene probabilidad > 0.5."""
        prob_dominant = mechanism._calculate_success_probability(dominant, subordinate, relationship)
        prob_subordinate = mechanism._calculate_success_probability(subordinate, dominant, relationship)
        
        assert prob_dominant > 0.5
        assert prob_subordinate < 0.5
    
    def test_winner_pays_less_than_loser(self, mechanism, dominant, subordinate, relationship, pending, monkeypatch):
        """El ganador paga solo exhibición; el perdedor paga exhibición + retirada."""
        monkeypatch.setattr(random, "random", lambda: 0.0)  # A gana
        
        mechanism.execute(dominant, subordinate, relationship, pending)
        
        dominant.spend_energy.assert_called_once_with(4.0)    # 10 * 0.4
        subordinate.spend_energy.assert_called_once_with(10.0)  # 10 * (0.4 + 0.6)
    
    def test_no_deaths(self, mechanism, dominant, subordinate, relationship, pending, monkeypatch):
        """La exhibición nunca mata, gane quien gane."""
        monkeypatch.setattr(random, "random", lambda: 0.0)
        mechanism.execute(dominant, subordinate, relationship, pending)
        monkeypatch.setattr(random, "random", lambda: 1.0)
        mechanism.execute(dominant, subordinate, relationship, pending)
        
        pending.register_death.assert_not_called()


class TestChemicalSuppressionMechanism:
    """Tests para ChemicalSuppressionMechanism (alelopatía)."""
    
    @pytest.fixture
    def mechanism(self):
        return ChemicalSuppressionMechanism()
    
    @pytest.fixture
    def producer(self):
        person = MagicMock()
        person.entity_id = 1
        person.species = "toxic_plant"
        person.energy = 50.0
        person.genome.venom = 0.9
        return person
    
    @pytest.fixture
    def target(self):
        person = MagicMock()
        person.entity_id = 2
        person.species = "neighbor_plant"
        person.energy = 50.0
        person.genome.immunity = 0.3
        return person
    
    @pytest.fixture
    def relationship(self):
        return EcologicalRelationship(
            species_a_id="toxic_plant",
            species_b_id="neighbor_plant",
            relationship_type=RelationshipType.AMENSALISM,
            mechanism=MechanismType.CHEMICAL_SUPPRESSION,
            intensity=0.6,
            effect_on_a=RelationshipEffect(energy_change=-2.0),
            effect_on_b=RelationshipEffect(energy_change=-8.0),
        )
    
    @pytest.fixture
    def pending(self):
        return MagicMock()
    
    def test_probability_within_bounds(self, mechanism, producer, target, relationship):
        """La probabilidad está acotada a [0.05, 0.85]."""
        prob = mechanism._calculate_success_probability(producer, target, relationship)
        assert 0.05 <= prob <= 0.85
    
    def test_venom_and_immunity_modulate(self, mechanism, relationship):
        """Más venomo aumenta el éxito; más inmunidad lo reduce."""
        potent = MagicMock()
        potent.genome.venom = 0.9
        weak = MagicMock()
        weak.genome.venom = 0.1
        
        resistant = MagicMock()
        resistant.genome.immunity = 0.9
        vulnerable = MagicMock()
        vulnerable.genome.immunity = 0.1
        
        prob_potent = mechanism._calculate_success_probability(potent, vulnerable, relationship)
        prob_weak = mechanism._calculate_success_probability(weak, resistant, relationship)
        
        assert prob_potent > prob_weak
    
    def test_success_costs_production_and_damages(self, mechanism, producer, target, relationship, pending, monkeypatch):
        """Éxito: productor paga coste completo y objetivo sufre daño."""
        monkeypatch.setattr(random, "random", lambda: 0.0)
        
        outcome = mechanism.execute(producer, target, relationship, pending)
        
        assert outcome == InteractionOutcome.SUCCESS
        producer.spend_energy.assert_called_once_with(2.0)
        target.spend_energy.assert_called_once_with(8.0)
    
    def test_failure_costs_half_production(self, mechanism, producer, target, relationship, pending, monkeypatch):
        """Fallo: productor paga mitad del coste; objetivo intacto."""
        monkeypatch.setattr(random, "random", lambda: 1.0)
        
        outcome = mechanism.execute(producer, target, relationship, pending)
        
        assert outcome == InteractionOutcome.FAILURE
        producer.spend_energy.assert_called_once_with(1.0)
        target.spend_energy.assert_not_called()
    
    def test_never_registers_death(self, mechanism, producer, target, relationship, pending, monkeypatch):
        """La muerte emerge por inanición, no se registra directamente."""
        monkeypatch.setattr(random, "random", lambda: 0.0)
        mechanism.execute(producer, target, relationship, pending)
        
        pending.register_death.assert_not_called()


class TestFilterFeedingMechanism:
    """Tests para FilterFeedingMechanism (filtrado)."""
    
    @pytest.fixture
    def mechanism(self):
        return FilterFeedingMechanism()
    
    @pytest.fixture
    def filter_feeder(self):
        person = MagicMock()
        person.entity_id = 1
        person.species = "mussel"
        person.energy = 50.0
        person.genome.swimming = 0.2
        person.genome.mobility = 0.2
        return person
    
    @pytest.fixture
    def resource(self):
        person = MagicMock()
        person.entity_id = 2
        person.species = "plankton"
        person.energy = 5.0
        return person
    
    @pytest.fixture
    def relationship(self):
        return EcologicalRelationship(
            species_a_id="mussel",
            species_b_id="plankton",
            relationship_type=RelationshipType.HERBIVORY,
            mechanism=MechanismType.FILTER_FEEDING,
            intensity=0.8,
            effect_on_a=RelationshipEffect(energy_change=10.0),
            effect_on_b=RelationshipEffect(energy_change=-5.0),
        )
    
    @pytest.fixture
    def pending(self):
        return MagicMock()
    
    def test_probability_within_bounds(self, mechanism, filter_feeder, resource, relationship):
        """La probabilidad está acotada a [0.10, 0.95]."""
        prob = mechanism._calculate_success_probability(filter_feeder, resource, relationship)
        assert 0.10 <= prob <= 0.95
    
    def test_high_intensity_gives_high_probability(self, mechanism, filter_feeder, resource):
        """Intensidad alta produce probabilidad alta (mecanismo pasivo)."""
        strong = EcologicalRelationship(
            species_a_id="mussel",
            species_b_id="plankton",
            relationship_type=RelationshipType.HERBIVORY,
            mechanism=MechanismType.FILTER_FEEDING,
            intensity=1.0,
            effect_on_a=RelationshipEffect(energy_change=10.0),
        )
        prob = mechanism._calculate_success_probability(filter_feeder, resource, strong)
        assert prob >= 0.9
    
    def test_success_feeds_and_depletes(self, mechanism, filter_feeder, resource, relationship, pending, monkeypatch):
        """Éxito: filtrador gana energía y el recurso pierde."""
        monkeypatch.setattr(random, "random", lambda: 0.0)
        
        outcome = mechanism.execute(filter_feeder, resource, relationship, pending)
        
        assert outcome == InteractionOutcome.SUCCESS
        filter_feeder.add_energy.assert_called_once_with(10.0)
        resource.spend_energy.assert_called_once_with(5.0)
    
    def test_exhausted_resource_dies(self, mechanism, filter_feeder, relationship, pending, monkeypatch):
        """Recurso agotado (energía <= 0) muere como en el pastoreo."""
        exhausted = MagicMock()
        exhausted.entity_id = 2
        exhausted.energy = 0.0
        
        monkeypatch.setattr(random, "random", lambda: 0.0)
        mechanism.execute(filter_feeder, exhausted, relationship, pending)
        
        pending.register_death.assert_called_once_with(
            entity_id=exhausted.entity_id,
            reason="consumed",
        )


class TestMechanismFactorySpecific:
    """Tests para verificar que la fábrica despacha mecanismos específicos."""
    
    @pytest.mark.parametrize("mechanism_type,expected_class", [
        (MechanismType.AMBUSH, AmbushMechanism),
        (MechanismType.PACK_HUNTING, PackHuntingMechanism),
        (MechanismType.FILTER_FEEDING, FilterFeedingMechanism),
        (MechanismType.TERRITORIAL_DISPLAY, TerritorialDisplayMechanism),
        (MechanismType.CHEMICAL_SUPPRESSION, ChemicalSuppressionMechanism),
    ])
    def test_factory_returns_specific_mechanism(self, mechanism_type, expected_class):
        """Cada tipo despacha su mecanismo real, no un placeholder."""
        mechanism = MechanismFactory.get_mechanism(mechanism_type)
        assert isinstance(mechanism, expected_class)