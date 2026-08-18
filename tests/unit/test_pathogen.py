"""Tests unitarios para el modelo de patógenos (Pathogen).

Verifica:
- Creación de variantes aleatorias en rangos válidos
- Mutación que incrementa generación y mantiene ancestro
- Sistema de inmunidad cruzada entre familias
"""

import pytest
from systems.diseases.pathogen import Pathogen, InfectionPhase, InfectionState


class TestPathogenCreation:
    """Tests de creación de patógenos."""

    def test_create_random_variant_properties(self):
        """create_random_variant genera propiedades en rangos válidos."""
        pathogen = Pathogen.create_random_variant("Influenza")
        
        assert pathogen.family == "Influenza"
        assert pathogen.variant_id == 1
        assert pathogen.generation == 1
        assert pathogen.ancestor_id is None
        assert 0.1 <= pathogen.virulence <= 1.5
        assert 0.01 <= pathogen.transmission <= 0.5
        assert 0.01 <= pathogen.lethality <= 0.5
        assert 0.1 <= pathogen.asymptomatic_chance <= 0.4
        assert 2.0 <= pathogen.incubation_days <= 7.0

    def test_unique_id_generation(self):
        """Cada patógeno recibe un ID único global."""
        p1 = Pathogen.create_random_variant("Coronavirus")
        p2 = Pathogen.create_random_variant("Coronavirus")
        
        assert p1.pathogen_id != p2.pathogen_id
        assert p1.unique_id != p2.unique_id


class TestPathogenMutation:
    """Tests de mutación de patógenos."""

    def test_mutate_increases_generation(self):
        """mutate() incrementa la generación y establece el ancestro."""
        parent = Pathogen.create_random_variant("Poxvirus")
        child = parent.mutate()
        
        assert child.generation == parent.generation + 1
        assert child.ancestor_id == parent.pathogen_id
        assert child.family == parent.family

    def test_mutate_values_stay_in_range(self):
        """Los valores mutados se mantienen en rangos biológicos válidos."""
        parent = Pathogen.create_random_variant("Influenza")
        # Forzamos valores extremos para probar el clamping
        parent.virulence = 0.1
        parent.lethality = 0.9
        
        child = parent.mutate()
        
        assert 0.1 <= child.virulence <= 3.0  # max 0.1 * 1.15 = 0.115, min 0.1
        assert 0.0 <= child.lethality <= 1.0


class TestPathogenCrossImmunity:
    """Tests de inmunidad cruzada entre familias."""

    def test_same_family_full_similarity(self):
        """La misma familia tiene similitud 1.0."""
        assert Pathogen.get_family_similarity("Influenza", "Influenza") == 1.0

    def test_related_families_partial_similarity(self):
        """Familias relacionadas tienen similitud parcial."""
        # Coronavirus y SARS tienen 0.6 de similitud según el código
        assert Pathogen.get_family_similarity("Coronavirus", "SARS") == 0.6
        assert Pathogen.get_family_similarity("SARS", "Coronavirus") == 0.6

    def test_unrelated_families_zero_similarity(self):
        """Familias no relacionadas tienen similitud 0.0."""
        assert Pathogen.get_family_similarity("Influenza", "Poxvirus") == 0.0

    def test_get_related_families(self):
        """get_related_families devuelve las familias con similitud >= umbral."""
        related = Pathogen.get_related_families("Coronavirus", min_similarity=0.1)
        assert "Influenza" in related  # 0.15
        assert "SARS" in related       # 0.6
        assert "Coronavirus" not in related  # Se excluye a sí misma


class TestInfectionState:
    """Tests del estado de infección."""

    def test_initial_state_is_exposed(self):
        """Una nueva infección comienza en fase EXPOSED."""
        pathogen = Pathogen.create_random_variant("Influenza")
        state = InfectionState(pathogen)
        
        assert state.phase == InfectionPhase.EXPOSED
        assert state.days_in_phase == 0.0
        assert state.total_days == 0.0

    def test_advance_progresses_phases(self):
        """advance() progresa correctamente entre fases."""
        pathogen = Pathogen.create_random_variant("Influenza")
        pathogen.incubation_days = 2.0
        state = InfectionState(pathogen)
        
        # Avanzar 1 día: debería seguir en EXPOSED (dura 0.5 días) o pasar a INCUBATING
        state.advance(1.0)
        assert state.phase in (InfectionPhase.EXPOSED, InfectionPhase.INCUBATING)
        
        # Avanzar hasta superar incubación
        state.advance(5.0)
        assert state.phase in (InfectionPhase.CONTAGIOUS, InfectionPhase.SYMPTOMATIC)

    def test_is_contagious_only_in_specific_phases(self):
        """is_contagious() es True solo en CONTAGIOUS y SYMPTOMATIC."""
        pathogen = Pathogen.create_random_variant("Influenza")
        state = InfectionState(pathogen)
        
        assert not state.is_contagious()  # EXPOSED
        
        state.phase = InfectionPhase.CONTAGIOUS
        assert state.is_contagious()
        
        state.phase = InfectionPhase.RECOVERING
        assert not state.is_contagious()