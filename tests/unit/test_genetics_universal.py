"""Tests para el sistema de Genética Universal.

Cubre las nuevas funcionalidades añadidas en la refactorización:
- Modelos de expresión genética
- Validador Biológico con reglas declarativas
- Herencia entre plantillas
- Trait neutro con distribuciones y pesos evolutivos
"""

import pytest
from core.genetics.trait import (
    Trait, TraitCategory, ExpressionModel, Distribution
)
from entities.person.allele import Allele, Gene
from core.genetics.species_definition import (
    SpeciesDefinition, SpeciesRegistry
)
from core.genetics.trait_library import TraitLibrary
from core.genetics.biological_validator import (
    BiologicalValidator, ValidationSeverity
)
from core.genetics.realism_index import RealismIndex
from entities.person.genome import Genome


# =============================================================================
# FIXTURES COMPARTIDOS
# =============================================================================

@pytest.fixture(autouse=True)
def init_registry():
    """Inicializa el registro de especies antes de cada test."""
    SpeciesRegistry.initialize_defaults()


@pytest.fixture
def human() -> SpeciesDefinition:
    """Fixture que garantiza obtener la especie humana (no None)."""
    species = SpeciesRegistry.get("human")
    assert species is not None, "Especie 'human' no encontrada en el registro"
    return species


@pytest.fixture
def bird() -> SpeciesDefinition:
    """Fixture que garantiza obtener la especie ave (no None)."""
    species = SpeciesRegistry.get("bird")
    assert species is not None, "Especie 'bird' no encontrada en el registro"
    return species


@pytest.fixture
def fantasy() -> SpeciesDefinition:
    """Fixture que garantiza obtener la especie fantástica (no None)."""
    species = SpeciesRegistry.get("fantasy_creature")
    assert species is not None, "Especie 'fantasy_creature' no encontrada en el registro"
    return species


# =============================================================================
# TESTS: MODELOS DE EXPRESIÓN GENÉTICA
# =============================================================================

class TestExpressionModels:
    """Tests para los 7 modelos de expresión disponibles."""
    
    @pytest.fixture
    def dominant_alleles(self) -> Gene:
        a1 = Allele(value=2.0, dominance=0.9)
        a2 = Allele(value=0.5, dominance=0.2)
        return Gene(a1, a2)
    
    def test_dominant_returns_higher_dominance(self, dominant_alleles: Gene) -> None:
        assert dominant_alleles.express("DOMINANT") == 2.0
    
    def test_recessive_returns_lower_dominance(self, dominant_alleles: Gene) -> None:
        assert dominant_alleles.express("RECESSIVE") == 0.5
    
    def test_codominant_returns_average(self, dominant_alleles: Gene) -> None:
        assert dominant_alleles.express("CODOMINANT") == 1.25
    
    def test_additive_returns_sum(self, dominant_alleles: Gene) -> None:
        assert dominant_alleles.express("ADDITIVE") == 2.5
    
    def test_max_value(self, dominant_alleles: Gene) -> None:
        assert dominant_alleles.express("MAX_VALUE") == 2.0
    
    def test_min_value(self, dominant_alleles: Gene) -> None:
        assert dominant_alleles.express("MIN_VALUE") == 0.5
    
    def test_none_model_uses_dominant(self, dominant_alleles: Gene) -> None:
        """Si no se pasa modelo, usa DOMINANT por defecto (retrocompatibilidad)."""
        assert dominant_alleles.express(None) == 2.0
    
    def test_unknown_model_falls_back_to_dominant(self, dominant_alleles: Gene) -> None:
        """Modelos desconocidos hacen fallback a DOMINANT."""
        assert dominant_alleles.express("UNKNOWN") == 2.0


# =============================================================================
# TESTS: TRAIT NEUTRO
# =============================================================================

class TestTraitNeutrality:
    """Verifica que los Traits son completamente neutros."""
    
    def test_trait_has_no_incompatibilities(self) -> None:
        trait = Trait(
            trait_id="test",
            name="Test",
            category=TraitCategory.BIOLOGY,
        )
        assert not hasattr(trait, "incompatible_with")
        assert not hasattr(trait, "requires_traits")
    
    def test_trait_has_evolutionary_weight(self) -> None:
        trait = Trait(
            trait_id="test",
            name="Test",
            category=TraitCategory.BIOLOGY,
            evolutionary_weight=0.8,
        )
        assert trait.evolutionary_weight == 0.8
    
    def test_trait_has_heritability(self) -> None:
        trait = Trait(
            trait_id="test",
            name="Test",
            category=TraitCategory.BIOLOGY,
            heritability=0.75,
        )
        assert trait.heritability == 0.75
    
    def test_trait_has_expression_model(self) -> None:
        trait = Trait(
            trait_id="test",
            name="Test",
            category=TraitCategory.BIOLOGY,
            expression_model=ExpressionModel.CODOMINANT,
        )
        assert trait.expression_model == ExpressionModel.CODOMINANT
    
    def test_trait_clamp_value(self) -> None:
        trait = Trait(
            trait_id="test",
            name="Test",
            category=TraitCategory.BIOLOGY,
            min_value=0.0,
            max_value=2.0,
        )
        assert trait.clamp_value(-1.0) == 0.0
        assert trait.clamp_value(5.0) == 2.0
        assert trait.clamp_value(1.0) == 1.0
    
    def test_trait_is_frozen(self) -> None:
        """El Trait es inmutable (dataclass frozen)."""
        trait = Trait(
            trait_id="test",
            name="Test",
            category=TraitCategory.BIOLOGY,
        )
        with pytest.raises(Exception):
            trait.trait_id = "modified"  # type: ignore


# =============================================================================
# TESTS: HERENCIA ENTRE PLANTILLAS
# =============================================================================

class TestTemplateInheritance:
    """Tests para el sistema de herencia entre plantillas."""
    
    def test_empty_template_has_no_traits(self) -> None:
        empty = SpeciesRegistry.get("empty")
        assert empty is not None
        assert empty.get_trait_count() == 0
    
    def test_human_inherits_from_mammal(self, human: SpeciesDefinition) -> None:
        chain = human.get_inheritance_chain()
        assert "mammal" in chain
        assert "vertebrate" in chain
        assert "animal" in chain
        assert "empty" in chain
    
    def test_bird_inherits_from_vertebrate(self, bird: SpeciesDefinition) -> None:
        chain = bird.get_inheritance_chain()
        assert "vertebrate" in chain
        assert "animal" in chain
    
    def test_inherited_traits_are_visible(self, human: SpeciesDefinition) -> None:
        # Hereda de animal (metabolism)
        assert human.has_trait("metabolism")
        # Hereda de vertebrado (nervous_system)
        assert human.has_trait("nervous_system")
        # Local (intelligence)
        assert human.has_trait("intelligence")
    
    def test_local_traits_override_inherited(self, human: SpeciesDefinition) -> None:
        # El humano define localmente intelligence = 1.8
        # Sobrescribe el 0.5 heredado de vertebrado
        config = human.get_trait_config("intelligence")
        assert config is not None
        assert config.default_value == 1.8
    
    def test_from_template_factory(self) -> None:
        wolf = SpeciesDefinition.from_template(
            species_id="test_wolf",
            name="Lobo de prueba",
            base_template="mammal",
        ).add_trait("smell", default_value=1.8)
        
        assert wolf.parent_template == "mammal"
        assert wolf.has_trait("smell")
        assert wolf.has_trait("metabolism")  # heredado
    
    def test_empty_factory_creates_species_without_traits(self) -> None:
        alien = SpeciesDefinition.empty(
            species_id="test_alien",
            name="Alien",
        )
        assert alien.get_trait_count() == 0
        assert alien.parent_template is None


# =============================================================================
# TESTS: VALIDADOR BIOLÓGICO
# =============================================================================

class TestBiologicalValidator:
    """Tests para el validador biológico con reglas declarativas."""
    
    def test_human_is_mostly_coherent(self, human: SpeciesDefinition) -> None:
        validator = BiologicalValidator()
        result = validator.validate_species(human)
        
        assert len(result.errors) == 0
        assert result.is_valid
    
    def test_flight_without_metabolism_warns(self) -> None:
        validator = BiologicalValidator()
        weird = SpeciesDefinition(
            species_id="weird_test",
            name="Test",
        ).add_trait("flight", default_value=1.5)
        
        result = validator.validate_species(weird)
        messages = [m.message for m in result.messages]
        assert any("metabolismo" in m.lower() for m in messages)
    
    def test_empathy_without_nervous_system_is_error(self) -> None:
        validator = BiologicalValidator()
        invalid = SpeciesDefinition(
            species_id="invalid_test",
            name="Test",
        ).add_trait("empathy", default_value=1.5)
        
        result = validator.validate_species(invalid)
        assert len(result.errors) > 0
        assert not result.is_valid
    
    def test_photosynthesis_plus_heterotrophy_is_error(self) -> None:
        validator = BiologicalValidator()
        impossible = SpeciesDefinition(
            species_id="impossible_test",
            name="Test",
        ).add_trait("photosynthesis", default_value=1.5) \
         .add_trait("heterotrophy", default_value=1.5)
        
        result = validator.validate_species(impossible)
        assert len(result.errors) > 0
    
    def test_empty_species_warns(self) -> None:
        validator = BiologicalValidator()
        empty = SpeciesDefinition.empty("empty_test", "Test")
        result = validator.validate_species(empty)
        
        assert len(result.warnings) > 0
    
    def test_score_decreases_with_errors(self, human: SpeciesDefinition) -> None:
        validator = BiologicalValidator()
        
        bad = SpeciesDefinition(
            species_id="bad_test",
            name="Test",
        ).add_trait("empathy", default_value=1.5) \
         .add_trait("photosynthesis", default_value=1.5) \
         .add_trait("heterotrophy", default_value=1.5)
        
        good_score = validator.validate_species(human).score
        bad_score = validator.validate_species(bad).score
        
        assert good_score > bad_score


# =============================================================================
# TESTS: ÍNDICE DE REALISMO
# =============================================================================

class TestRealismIndex:
    """Tests para el índice de realismo."""
    
    def test_human_has_high_realism(self, human: SpeciesDefinition) -> None:
        realism = RealismIndex()
        score = realism.calculate(human)
        assert score >= 0.8
    
    def test_fantasy_has_lower_realism(
        self, human: SpeciesDefinition, fantasy: SpeciesDefinition
    ) -> None:
        realism = RealismIndex()
        
        fantasy_score = realism.calculate(fantasy)
        human_score = realism.calculate(human)
        
        assert fantasy_score < human_score
    
    def test_description_varies_with_score(self) -> None:
        realism = RealismIndex()
        
        high = realism.get_description(0.95)
        low = realism.get_description(0.2)
        
        assert "coherente" in high.lower()
        assert "fantástica" in low.lower()


# =============================================================================
# TESTS: GENOME CON NUEVOS MODELOS
# =============================================================================

class TestGenomeWithNewModels:
    """Tests del Genome integrado con los nuevos modelos."""
    
    def test_genome_uses_trait_expression_model(self, human: SpeciesDefinition) -> None:
        """El Genome consulta el modelo de expresión del trait."""
        genome = Genome.create_founder(human)
        
        fertility = genome.get_trait_value("fertility")
        assert 0.0 <= fertility <= 2.0
    
    def test_genome_returns_zero_for_missing_trait(self, human: SpeciesDefinition) -> None:
        genome = Genome.create_founder(human)
        
        # flight no está en los rasgos del humano
        assert genome.get_trait_value("flight") == 0.0
    
    def test_genome_has_all_trait_ids(self, human: SpeciesDefinition) -> None:
        genome = Genome.create_founder(human)
        
        trait_ids = genome.get_all_trait_ids()
        assert "fertility" in trait_ids  # heredado
        assert "intelligence" in trait_ids  # local
    
    def test_genome_retrocompatible_properties(self, human: SpeciesDefinition) -> None:
        """Las properties antiguas siguen funcionando (retrocompatibilidad).
        
        Estas son las 9 properties que existían en el Genome original
        y que usan los sistemas existentes.
        """
        genome = Genome.create_founder(human)
        
        # Las 9 properties retrocompatibles (existentes desde el inicio)
        assert isinstance(genome.fertility, float)
        assert isinstance(genome.sociability, float)
        assert isinstance(genome.temperament, float)
        assert isinstance(genome.immunity, float)
        assert isinstance(genome.longevity, float)
        assert isinstance(genome.impulsivity, float)
        assert isinstance(genome.curiosity, float)
        assert isinstance(genome.obedience, float)
        assert isinstance(genome.aggressiveness, float)
        
        # Los rasgos nuevos se consultan con get_trait_value()
        assert isinstance(genome.get_trait_value("intelligence"), float)
        assert isinstance(genome.get_trait_value("cooperation"), float)
        assert isinstance(genome.get_trait_value("empathy"), float)
    
    def test_genome_combine_with_new_model(self, human: SpeciesDefinition) -> None:
        """La reproducción funciona con los nuevos modelos."""
        parent1 = Genome.create_founder(human)
        parent2 = Genome.create_founder(human)
        
        child = parent1.combine(parent2)
        
        assert isinstance(child, Genome)
        assert len(child.get_all_trait_ids()) == len(parent1.get_all_trait_ids())


# =============================================================================
# TESTS: BIBLIOTECA UNIVERSAL
# =============================================================================

class TestTraitLibrary:
    """Tests para la biblioteca universal de rasgos."""
    
    def test_library_has_traits(self) -> None:
        library = TraitLibrary.get_default()
        assert len(library) > 30
    
    def test_library_has_all_categories(self) -> None:
        library = TraitLibrary.get_default()
        categories = set(t.category for t in library.get_all_traits())
        
        assert TraitCategory.BIOLOGY in categories
        assert TraitCategory.BEHAVIOR in categories
        assert TraitCategory.PERCEPTION in categories
        assert TraitCategory.MOVEMENT in categories
        assert TraitCategory.SPECIAL in categories
    
    def test_traits_are_neutral(self) -> None:
        """Ningún trait en la biblioteca tiene incompatibilidades."""
        library = TraitLibrary.get_default()
        
        for trait in library.get_all_traits():
            assert not hasattr(trait, "incompatible_with")
            assert not hasattr(trait, "requires_traits")
    
    def test_traits_have_expression_model(self) -> None:
        library = TraitLibrary.get_default()
        
        for trait in library.get_all_traits():
            assert isinstance(trait.expression_model, ExpressionModel)
    
    def test_traits_have_evolutionary_weight(self) -> None:
        library = TraitLibrary.get_default()
        
        for trait in library.get_all_traits():
            assert 0.0 <= trait.evolutionary_weight <= 2.0