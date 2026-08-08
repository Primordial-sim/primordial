"""Módulo que define la genética y herencia mendeliana de las entidades.

Responsabilidad:
Actuar como el contenedor del genotipo diploide de un individuo.
Define la recombinación por segregación independiente y mutación puntual.

Incluye:
- Genes base: longevidad, sociabilidad, temperamento, fertilidad, inmunidad
- Genes específicos de inmunidad por familia de patógenos (heredable)
- Genes de personalidad para libre albedrío (impulsividad, curiosidad, obediencia, agresividad)

OPTIMIZACIÓN: Método combine() refactorizado con _recombine_genes() auxiliar.
"""

import random
import logging
from typing import Optional, Dict, Set
from .allele import Allele, Gene


class Genome:
    """Conjunto de pares de alelos que determinan los rasgos de una entidad.
    
    Implementa un sistema mendeliano puro con dominancia y recesividad,
    erradicando la pérdida de varianza (convergencia a la media).
    """

    def __init__(
        self,
        longevity: Optional[Gene] = None,
        sociability: Optional[Gene] = None,
        temperament: Optional[Gene] = None,
        fertility: Optional[Gene] = None,
        immunity: Optional[Gene] = None,
        species_baseline: str = "human",
        family_specific_immunity: Optional[Dict[str, Gene]] = None,
        impulsivity: Optional[Gene] = None,
        curiosity: Optional[Gene] = None,
        obedience: Optional[Gene] = None,
        aggressiveness: Optional[Gene] = None,
    ) -> None:
        """Inicializa el genoma, generando genes fundadores si no se proveen."""
        self._species_baseline = species_baseline
        self.logger = logging.getLogger(self.__class__.__name__)

        # Genes base
        self._genes = {
            "longevity": longevity or self._create_founder_gene(1.0),
            "sociability": sociability or self._create_founder_gene(1.0),
            "temperament": temperament or self._create_founder_gene(1.0),
            "fertility": fertility or self._create_founder_gene(1.0),
            "immunity": immunity or self._create_founder_gene(1.0),
            "impulsivity": impulsivity or self._create_founder_gene(0.5),
            "curiosity": curiosity or self._create_founder_gene(0.5),
            "obedience": obedience or self._create_founder_gene(0.5),
            "aggressiveness": aggressiveness or self._create_founder_gene(0.5),
        }

        # Genes específicos por familia de patógenos
        self._family_specific_immunity = family_specific_immunity or {}

    def _create_founder_gene(self, base_val: float) -> Gene:
        """Crea un gen inicial aplicando una ligera diversidad a la especie base."""
        return Gene(
            allele_a=Allele.create_random(base_val, 0.1),
            allele_b=Allele.create_random(base_val, 0.1)
        )

    # ==========================================
    # PROPERTIES FENOTÍPICAS (Interfaz retrocompatible)
    # ==========================================
    @property
    def longevity(self) -> float:
        return self._genes["longevity"].express()

    @property
    def sociability(self) -> float:
        return self._genes["sociability"].express()

    @property
    def temperament(self) -> float:
        return self._genes["temperament"].express()

    @property
    def fertility(self) -> float:
        return self._genes["fertility"].express()

    @property
    def immunity(self) -> float:
        return self._genes["immunity"].express()

    @property
    def impulsivity(self) -> float:
        """Tendencia a actuar sin pensar [0.0, 2.0]."""
        return self._genes["impulsivity"].express()

    @property
    def curiosity(self) -> float:
        """Deseo de explorar lo desconocido [0.0, 2.0]."""
        return self._genes["curiosity"].express()

    @property
    def obedience(self) -> float:
        """Tendencia a seguir normas [0.0, 2.0]."""
        return self._genes["obedience"].express()

    @property
    def aggressiveness(self) -> float:
        """Tendencia al conflicto [0.0, 2.0]."""
        return self._genes["aggressiveness"].express()

    @property
    def species_baseline(self) -> str:
        return self._species_baseline

    # ==========================================
    # INMUNIDAD ESPECÍFICA POR FAMILIA
    # ==========================================
    def get_family_specific_immunity(self, family: str) -> float:
        """Obtiene el nivel de inmunidad genética específica para una familia de patógenos."""
        if family in self._family_specific_immunity:
            return self._family_specific_immunity[family].express()
        return 0.0

    def has_family_specific_immunity(self, family: str) -> bool:
        """Verifica si existe inmunidad genética específica para una familia."""
        return family in self._family_specific_immunity

    def get_all_family_immunities(self) -> Dict[str, float]:
        """Obtiene todos los niveles de inmunidad específica por familia."""
        return {family: gene.express() for family, gene in self._family_specific_immunity.items()}

    # ==========================================
    # MOTOR DE HERENCIA MENDELIANA (REFACTORIZADO)
    # ==========================================
    def _recombine_genes(
        self, 
        gene_dict_1: Dict[str, Gene], 
        gene_dict_2: Dict[str, Gene], 
        all_keys: Set[str], 
        mutation_rate: float = 0.05,
        default_base_value: float = 0.5
    ) -> Dict[str, Gene]:
        """Recombina dos diccionarios de genes aplicando meiosis y mutación.
        
        CORRECCIÓN: Método auxiliar que elimina la duplicación de lógica en combine().
        
        Args:
            gene_dict_1: Diccionario de genes del primer progenitor.
            gene_dict_2: Diccionario de genes del segundo progenitor.
            all_keys: Conjunto de todas las claves a recombinar.
            mutation_rate: Probabilidad de mutación puntual por alelo.
            default_base_value: Valor base para alelos creados de la nada (cuando un 
                               progenitor no tiene el gen).
            
        Returns:
            Nuevo diccionario de genes recombinados.
        """
        new_genes = {}
        for key in all_keys:
            gene_1 = gene_dict_1.get(key)
            gene_2 = gene_dict_2.get(key)
            
            # Obtener alelos por meiosis (o crear uno nuevo si el progenitor no tiene el gen)
            allele_1 = gene_1.meiosis() if gene_1 else Allele.create_random(default_base_value, 0.1)
            allele_2 = gene_2.meiosis() if gene_2 else Allele.create_random(default_base_value, 0.1)
            
            # Aplicar mutación puntual
            if random.random() < mutation_rate:
                allele_1 = Allele.create_random(allele_1.value, 0.15)
            if random.random() < mutation_rate:
                allele_2 = Allele.create_random(allele_2.value, 0.15)
            
            new_genes[key] = Gene(allele_1, allele_2)
        
        return new_genes

    def combine(self, other_genome: Optional['Genome']) -> 'Genome':
        """Cruza este genotipo con el de una pareja mediante meiosis.
        
        OPTIMIZACIÓN: Refactorizado para usar _recombine_genes() y eliminar duplicación.
        """
        if other_genome is None:
            other_genome = self

        if self._species_baseline != other_genome.species_baseline:
            self.logger.warning("Cruce interespecie. El híbrido heredará la línea materna.")

        mutation_rate = 0.05

        # CORRECCIÓN: Recombinar genes base usando método auxiliar
        all_base_genes = set(self._genes.keys()) | set(other_genome._genes.keys())
        new_genes = self._recombine_genes(
            self._genes, 
            other_genome._genes, 
            all_base_genes, 
            mutation_rate,
            default_base_value=0.5
        )

        # CORRECCIÓN: Recombinar genes específicos por familia usando método auxiliar
        all_families = set(self._family_specific_immunity.keys()) | set(other_genome._family_specific_immunity.keys())
        new_family_immunity = self._recombine_genes(
            self._family_specific_immunity, 
            other_genome._family_specific_immunity, 
            all_families, 
            mutation_rate,
            default_base_value=1.0  # Para inmunidad, el valor base es 1.0
        )

        return Genome(
            longevity=new_genes["longevity"],
            sociability=new_genes["sociability"],
            temperament=new_genes["temperament"],
            fertility=new_genes["fertility"],
            immunity=new_genes["immunity"],
            species_baseline=self._species_baseline,
            family_specific_immunity=new_family_immunity,
            impulsivity=new_genes["impulsivity"],
            curiosity=new_genes["curiosity"],
            obedience=new_genes["obedience"],
            aggressiveness=new_genes["aggressiveness"],
        )

    def __repr__(self) -> str:
        """Representación string del genoma para debugging."""
        base_genes = {k: v.express() for k, v in self._genes.items()}
        family_immunity = {k: v.express() for k, v in self._family_specific_immunity.items()}
        return f"Genome(base={base_genes}, family_immunity={family_immunity})"