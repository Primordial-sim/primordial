"""Tests unitarios para Genome.combine() y la genética mendeliana.

Verifica:
- Allele.create_random() produce valores en rango [0.1, 3.0]
- Gene.express() usa dominancia (no promedio)
- Gene.meiosis() segrega alelos al azar
- Genome.combine() produce recombinación mendeliana
- Partenogénesis (combine con None) funciona
"""

import pytest

from entities.person.allele import Allele, Gene
from entities.person.genome import Genome


def _create_test_genome(
    fertility: float = 0.7,
    sociability: float = 0.5,
    temperament: float = 0.5,
    immunity: float = 0.6,
    species: str = "human",
) -> Genome:
    """Crea un genoma de prueba con valores controlados."""
    return Genome(
        fertility=Gene(
            allele_a=Allele.create_random(fertility, 0.05),
            allele_b=Allele.create_random(fertility, 0.05),
        ),
        sociability=Gene(
            allele_a=Allele.create_random(sociability, 0.05),
            allele_b=Allele.create_random(sociability, 0.05),
        ),
        temperament=Gene(
            allele_a=Allele.create_random(temperament, 0.05),
            allele_b=Allele.create_random(temperament, 0.05),
        ),
        immunity=Gene(
            allele_a=Allele.create_random(immunity, 0.05),
            allele_b=Allele.create_random(immunity, 0.05),
        ),
        species_baseline=species,
    )


class TestAllele:
    """Tests de la partícula hereditaria fundamental."""

    def test_create_random_in_range(self):
        """create_random produce valores en [0.1, 3.0]."""
        for _ in range(100):
            allele = Allele.create_random(1.0, 0.5)
            assert 0.1 <= allele.value <= 3.0

    def test_create_random_dominance_in_range(self):
        """La dominancia está en [0.0, 1.0]."""
        for _ in range(100):
            allele = Allele.create_random(1.0, 0.5)
            assert 0.0 <= allele.dominance <= 1.0

    def test_create_random_no_mutation(self):
        """Con mutation_range=0, el valor es exactamente base_value."""
        allele = Allele.create_random(1.5, 0.0)
        assert allele.value == pytest.approx(1.5)

    def test_create_random_clamping_low(self):
        """Valores muy bajos se clampen a 0.1."""
        allele = Allele.create_random(0.01, 0.0)
        assert allele.value == pytest.approx(0.1)

    def test_create_random_clamping_high(self):
        """Valores muy altos se clampen a 3.0."""
        allele = Allele.create_random(5.0, 0.0)
        assert allele.value == pytest.approx(3.0)

    def test_allele_is_immutable(self):
        """Los alelos son inmutables (frozen dataclass)."""
        allele = Allele.create_random(1.0, 0.0)
        with pytest.raises((AttributeError, TypeError)):
            allele.value = 2.0  # type: ignore[misc]


class TestGene:
    """Tests del locus genético diploide."""

    def test_express_uses_dominance(self):
        """express() retorna el alelo con mayor dominancia, no el promedio."""
        dominant = Allele(value=2.0, dominance=0.9)
        recessive = Allele(value=0.5, dominance=0.1)
        gene = Gene(allele_a=dominant, allele_b=recessive)
        
        # Debe expresar el dominante (2.0), no el promedio (1.25)
        assert gene.express() == pytest.approx(2.0)

    def test_express_dominance_order_independent(self):
        """express() funciona igual independientemente del orden de los alelos."""
        dominant = Allele(value=2.0, dominance=0.9)
        recessive = Allele(value=0.5, dominance=0.1)
        
        gene_ab = Gene(allele_a=dominant, allele_b=recessive)
        gene_ba = Gene(allele_a=recessive, allele_b=dominant)
        
        assert gene_ab.express() == gene_ba.express()

    def test_meiosis_returns_one_allele(self):
        """meiosis() retorna exactamente uno de los dos alelos."""
        allele_a = Allele(value=1.0, dominance=0.5)
        allele_b = Allele(value=2.0, dominance=0.5)
        gene = Gene(allele_a=allele_a, allele_b=allele_b)
        
        for _ in range(50):
            result = gene.meiosis()
            assert result in (allele_a, allele_b)

    def test_meiosis_segregates_both_alleles(self):
        """meiosis() segrega ambos alelos con probabilidad ~50%."""
        allele_a = Allele(value=1.0, dominance=0.5)
        allele_b = Allele(value=2.0, dominance=0.5)
        gene = Gene(allele_a=allele_a, allele_b=allele_b)
        
        count_a = sum(1 for _ in range(1000) if gene.meiosis() is allele_a)
        
        # Con 1000 iteraciones, debería estar entre 40% y 60%
        assert 400 <= count_a <= 600, f"Segregación sesgada: {count_a}/1000"


class TestGenomeCombine:
    """Tests de recombinación genética entre genomas."""

    def test_combine_returns_genome(self):
        """combine() retorna un objeto Genome."""
        mother = _create_test_genome()
        father = _create_test_genome()
        child = mother.combine(father)
        assert isinstance(child, Genome)

    def test_combine_has_expected_genes(self):
        """El hijo tiene los mismos genes que los padres."""
        mother = _create_test_genome()
        father = _create_test_genome()
        child = mother.combine(father)
        
        # Verificar que el diccionario _genes tiene todas las claves
        assert "fertility" in child._genes
        assert "sociability" in child._genes
        assert "temperament" in child._genes
        assert "immunity" in child._genes

    def test_combine_values_in_valid_range(self):
        """Los alelos del hijo están en rango [0.1, 3.0]."""
        mother = _create_test_genome()
        father = _create_test_genome()
        child = mother.combine(father)
        
        for gene_name in ['fertility', 'sociability', 'temperament', 'immunity']:
            gene = child._genes[gene_name]
            assert 0.1 <= gene.allele_a.value <= 3.0, \
                f"{gene_name}.allele_a fuera de rango: {gene.allele_a.value}"
            assert 0.1 <= gene.allele_b.value <= 3.0, \
                f"{gene_name}.allele_b fuera de rango: {gene.allele_b.value}"

    def test_parthenogenesis_with_none(self):
        """combine(None) funciona para partenogénesis."""
        mother = _create_test_genome()
        child = mother.combine(None)
        assert isinstance(child, Genome)

    def test_combine_multiple_times_varies(self):
        """Combinar los mismos padres produce hijos genéticamente diferentes."""
        mother = _create_test_genome()
        father = _create_test_genome()
        
        # Generar 10 hijos y verificar que no todos son idénticos
        children = [mother.combine(father) for _ in range(10)]
        
        # Extraer fenotipos de sociabilidad (propiedad que retorna float)
        phenotypes = [child.sociability for child in children]
        
        # Con 10 hijos, debería haber variación (no todos idénticos)
        assert len(set(phenotypes)) > 1, "La recombinación no produce variación"

    def test_child_inherits_species(self):
        """El hijo hereda la especie de la madre."""
        mother = _create_test_genome(species="human")
        father = _create_test_genome(species="human")
        child = mother.combine(father)
        
        assert child.species_baseline == "human"

    def test_child_alleles_in_parent_range(self):
        """Los alelos del hijo están en un rango razonable de los padres."""
        mother = _create_test_genome(fertility=1.0)
        father = _create_test_genome(fertility=2.0)
        child = mother.combine(father)
        
        # Acceder al Gene real a través de _genes
        mother_gene = mother._genes["fertility"]
        father_gene = father._genes["fertility"]
        child_gene = child._genes["fertility"]
        
        # Rango esperado: [min_padres - tolerancia, max_padres + tolerancia]
        min_parent = min(
            mother_gene.allele_a.value,
            mother_gene.allele_b.value,
            father_gene.allele_a.value,
            father_gene.allele_b.value,
        )
        max_parent = max(
            mother_gene.allele_a.value,
            mother_gene.allele_b.value,
            father_gene.allele_a.value,
            father_gene.allele_b.value,
        )
        
        # Tolerancia para mutación (0.15 es el rango máximo de mutación)
        tolerance = 0.2
        
        assert min_parent - tolerance <= child_gene.allele_a.value <= max_parent + tolerance
        assert min_parent - tolerance <= child_gene.allele_b.value <= max_parent + tolerance

    def test_high_value_parents_high_value_children(self):
        """Padres con valores altos tienden a tener hijos con valores altos."""
        mother = _create_test_genome(fertility=2.5)
        father = _create_test_genome(fertility=2.5)
        
        child_phenotypes = []
        for _ in range(20):
            child = mother.combine(father)
            # Usar la propiedad fertility que retorna float (fenotipo)
            child_phenotypes.append(child.fertility)
        
        avg = sum(child_phenotypes) / len(child_phenotypes)
        # Padres con 2.5 → hijos deberían tener > 1.5 en promedio
        assert avg > 1.5, f"Fenotipo medio demasiado bajo: {avg}"

    def test_low_value_parents_low_value_children(self):
        """Padres con valores bajos tienden a tener hijos con valores bajos."""
        mother = _create_test_genome(immunity=0.3)
        father = _create_test_genome(immunity=0.3)
        
        child_phenotypes = []
        for _ in range(20):
            child = mother.combine(father)
            # Usar la propiedad immunity que retorna float (fenotipo)
            child_phenotypes.append(child.immunity)
        
        avg = sum(child_phenotypes) / len(child_phenotypes)
        # Padres con 0.3 → hijos deberían tener < 1.0 en promedio
        assert avg < 1.0, f"Fenotipo medio demasiado alto: {avg}"

    def test_genome_has_all_base_genes(self):
        """El genoma debe tener los 9 genes base."""
        genome = _create_test_genome()
        
        expected_genes = {
            "longevity", "sociability", "temperament", "fertility", "immunity",
            "impulsivity", "curiosity", "obedience", "aggressiveness"
        }
        
        assert set(genome._genes.keys()) == expected_genes

    def test_phenotype_properties_return_float(self):
        """Las propiedades fenotípicas retornan float (resultado de express())."""
        genome = _create_test_genome()
        
        # Todas las propiedades deben retornar float
        assert isinstance(genome.fertility, float)
        assert isinstance(genome.sociability, float)
        assert isinstance(genome.temperament, float)
        assert isinstance(genome.immunity, float)
        assert isinstance(genome.longevity, float)
        assert isinstance(genome.impulsivity, float)
        assert isinstance(genome.curiosity, float)
        assert isinstance(genome.obedience, float)
        assert isinstance(genome.aggressiveness, float)