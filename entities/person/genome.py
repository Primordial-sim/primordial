"""Módulo que define la genética y herencia mendeliana de las entidades.

GENÉTICA UNIVERSAL:
- El Genome es completamente genérico y no conoce especies.
- Solo almacena los rasgos activos definidos por la SpeciesDefinition.
- La herencia mendeliana funciona exactamente igual para cualquier rasgo.
- El Genome es inmutable durante la vida del individuo.
- El Genome es pasivo: solo proporciona información, nunca decide.

RETROCOMPATIBILIDAD:
- Acepta el constructor antiguo con parámetros individuales.
- Acepta el constructor nuevo con diccionario genérico de genes.
- Mantiene todas las properties existentes como wrappers.
"""

from __future__ import annotations

import random
import logging
from typing import Optional, Dict, Set, List, TYPE_CHECKING

from .allele import Allele, Gene

# TYPE_CHECKING: Imports solo para type hints, no en tiempo de ejecución
# Esto evita dependencias circulares mientras mantenemos type hints completos
if TYPE_CHECKING:
    from core.genetics.species_definition import SpeciesDefinition
    from core.genetics.trait_library import TraitLibrary
    from core.config.simulation_config import MutationConfig


class Genome:
    """Conjunto de pares de alelos que determinan los rasgos de una entidad.
    
    GENÉTICA UNIVERSAL:
    - No conoce especies.
    - No conoce biología.
    - No conoce el significado de los genes.
    - Únicamente almacena información genética.
    
    Implementa un sistema mendeliano puro con dominancia y recesividad,
    erradicando la pérdida de varianza (convergencia a la media).
    """

    def __init__(
        self,
        # ── Constructor nuevo (genético universal) ──
        genes: Optional[Dict[str, Gene]] = None,
        species_id: str = "human",
        family_specific_immunity: Optional[Dict[str, Gene]] = None,
        # ── Constructor antiguo (retrocompatibilidad) ──
        longevity: Optional[Gene] = None,
        sociability: Optional[Gene] = None,
        temperament: Optional[Gene] = None,
        fertility: Optional[Gene] = None,
        immunity: Optional[Gene] = None,
        species_baseline: Optional[str] = None,
        impulsivity: Optional[Gene] = None,
        curiosity: Optional[Gene] = None,
        obedience: Optional[Gene] = None,
        aggressiveness: Optional[Gene] = None,
    ) -> None:
        """Inicializa el genoma. Acepta ambos constructores.
        
        CONSTRUCTOR NUEVO (preferido):
            Genome(genes={"fertility": Gene(...), ...}, species_id="human")
        
        CONSTRUCTOR ANTIGUO (retrocompatible):
            Genome(fertility=Gene(...), sociability=Gene(...), species_baseline="human")
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Determinar qué constructor se está usando
        self._species_id = species_baseline or species_id
        
        if genes is not None:
            # ── Constructor nuevo ──
            self._genes: Dict[str, Gene] = dict(genes)
        else:
            # ── Constructor antiguo (retrocompatibilidad) ──
            self._genes = {}
            legacy_genes = {
                "longevity": longevity,
                "sociability": sociability,
                "temperament": temperament,
                "fertility": fertility,
                "immunity": immunity,
                "impulsivity": impulsivity,
                "curiosity": curiosity,
                "obedience": obedience,
                "aggressiveness": aggressiveness,
            }
            for trait_id, gene in legacy_genes.items():
                if gene is not None:
                    self._genes[trait_id] = gene
                else:
                    # Crear gen fundador con valor por defecto
                    default_value = 0.5 if trait_id in (
                        "impulsivity", "curiosity", "obedience", "aggressiveness"
                    ) else 1.0
                    self._genes[trait_id] = self._create_founder_gene(default_value)
        
        # Inmunidad específica por familia de patógenos
        self._family_specific_immunity: Dict[str, Gene] = family_specific_immunity or {}

    @classmethod
    def create_founder(
        cls, 
        species: SpeciesDefinition, 
        library: Optional[TraitLibrary] = None,
    ) -> Genome:
        """Crea un genoma fundador para una especie.
        
        GENÉTICA UNIVERSAL: Genera genes para todos los rasgos definidos
        en la SpeciesDefinition con diversidad inicial.
        
        Args:
            species: La definición de la especie.
            library: La biblioteca de rasgos (opcional, usa la por defecto).
            
        Returns:
            Un nuevo Genome con genes para todos los rasgos de la especie.
        """
        # Import diferido para evitar dependencias circulares
        from core.genetics.trait_library import TraitLibrary
        
        if library is None:
            library = TraitLibrary.get_default()
        
        genes: Dict[str, Gene] = {}
        
        for trait_id in species.get_all_trait_ids():
            config = species.get_trait_config(trait_id)
            trait = library.get_trait(trait_id)
            
            if trait is None:
                continue
            
            # Usar el valor por defecto de la especie o del rasgo
            base_value = config.default_value if config else trait.default_value
            
            # Crear gen con diversidad inicial
            genes[trait_id] = Gene(
                allele_a=Allele.create_random(base_value, 0.1),
                allele_b=Allele.create_random(base_value, 0.1),
            )
        
        return cls(genes=genes, species_id=species.species_id)

    def _create_founder_gene(self, base_val: float) -> Gene:
        """Crea un gen inicial aplicando una ligera diversidad."""
        return Gene(
            allele_a=Allele.create_random(base_val, 0.1),
            allele_b=Allele.create_random(base_val, 0.1),
        )

    # ==========================================
    # ACCESO A RASGOS (INTERFAZ GENÉRICA)
    # ==========================================
    
    def get_trait_value(self, trait_id: str) -> float:
        """Obtiene el valor fenotípico de un rasgo.
        
        Utiliza el modelo de expresión definido para el rasgo.
        Si el rasgo no está en la biblioteca, usa dominancia por defecto.
        """
        gene = self._genes.get(trait_id)
        if gene is None:
            return 0.0
        
        # Obtener el modelo de expresión del rasgo
        expression_model = self._get_expression_model(trait_id)
        return gene.express(expression_model)
    
    def _get_expression_model(self, trait_id: str) -> Optional[str]:
        """Obtiene el modelo de expresión para un rasgo.
        
        Consulta la Biblioteca Universal. Si no encuentra el rasgo,
        retorna None (usa dominancia por defecto).
        """
        from core.genetics.trait_library import TraitLibrary
        
        library = TraitLibrary.get_default()
        trait = library.get_trait(trait_id)
        if trait is None:
            return None
        
        return trait.expression_model.name

    def has_trait(self, trait_id: str) -> bool:
        """Verifica si el genoma tiene un rasgo específico."""
        return trait_id in self._genes
    
    def get_all_trait_ids(self) -> List[str]:
        """Retorna todos los IDs de rasgos presentes en el genoma."""
        return list(self._genes.keys())
    
    def get_all_trait_values(self) -> Dict[str, float]:
        """Retorna todos los valores fenotípicos de los rasgos."""
        return {trait_id: gene.express() for trait_id, gene in self._genes.items()}
    
    def get_gene(self, trait_id: str) -> Optional[Gene]:
        """Obtiene el gen (par de alelos) de un rasgo."""
        return self._genes.get(trait_id)
    
    # ==========================================
    # PROPERTIES FENOTÍPICAS (RETROCOMPATIBILIDAD)
    # ==========================================
    # Estas properties permiten que el código existente siga funcionando
    # sin modificaciones. Internamente usan get_trait_value().
    
    @property
    def longevity(self) -> float:
        return self.get_trait_value("longevity")

    @property
    def sociability(self) -> float:
        return self.get_trait_value("sociability")

    @property
    def temperament(self) -> float:
        return self.get_trait_value("temperament")

    @property
    def fertility(self) -> float:
        return self.get_trait_value("fertility")

    @property
    def immunity(self) -> float:
        return self.get_trait_value("immunity")

    @property
    def impulsivity(self) -> float:
        return self.get_trait_value("impulsivity")

    @property
    def curiosity(self) -> float:
        return self.get_trait_value("curiosity")

    @property
    def obedience(self) -> float:
        return self.get_trait_value("obedience")

    @property
    def aggressiveness(self) -> float:
        return self.get_trait_value("aggressiveness")

    @property
    def species_baseline(self) -> str:
        """Alias retrocompatible para species_id."""
        return self._species_id
    
    @property
    def species_id(self) -> str:
        return self._species_id

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
    # MOTOR DE HERENCIA MENDELIANA
    # ==========================================
    
    def _recombine_genes(
        self, 
        gene_dict_1: Dict[str, Gene], 
        gene_dict_2: Dict[str, Gene], 
        all_keys: Set[str], 
        mutation_config: Optional['MutationConfig'] = None,
        default_base_value: float = 0.5
    ) -> Dict[str, Gene]:
        """Recombina dos diccionarios de genes aplicando meiosis y mutación.
        
        GENÉTICA UNIVERSAL: Este método es completamente genérico.
        Usa MutationConfig para controlar la mutación (probability, magnitude_std, etc).
        Aplica clampeo al rango del trait (consultando TraitLibrary).
        """
        if mutation_config is None:
            from core.config.simulation_config import MutationConfig
            mutation_config = MutationConfig()
        
        new_genes = {}
        for key in all_keys:
            gene_1 = gene_dict_1.get(key)
            gene_2 = gene_dict_2.get(key)
            
            allele_1 = gene_1.meiosis() if gene_1 else Allele.create_random(default_base_value, 0.1)
            allele_2 = gene_2.meiosis() if gene_2 else Allele.create_random(default_base_value, 0.1)
            
            # Aplicar mutación con configuración
            allele_1 = self._mutate_allele(allele_1, key, mutation_config)
            allele_2 = self._mutate_allele(allele_2, key, mutation_config)
            
            new_genes[key] = Gene(allele_1, allele_2)
        
        return new_genes

    def _mutate_allele(
        self, 
        allele: Allele, 
        trait_id: str, 
        mutation_config: 'MutationConfig'
    ) -> Allele:
        """Aplica mutación gaussiana a un alelo con clampeo al rango del trait.
        
        Según GENETICS_CORE_SPEC.md (sección 4.3):
        - probability: probabilidad de que ocurra mutación
        - magnitude_std: desviación estándar del cambio gaussiano
        - mutate_dominance: si la dominancia también muta
        """
        # ¿Ocurre mutación?
        if random.random() >= mutation_config.probability:
            return allele  # Sin mutación
        
        # Obtener rango del trait para clampeo
        try:
            from core.genetics.trait_library import TraitLibrary
            library = TraitLibrary.get_default()
            trait = library.get_trait(trait_id)
            if trait:
                min_val = trait.min_value
                max_val = trait.max_value
            else:
                min_val, max_val = 0.0, 3.0  # fallback
        except Exception:
            min_val, max_val = 0.0, 3.0  # fallback
        
        # Mutar valor (gaussiano)
        delta = random.gauss(0, mutation_config.magnitude_std)
        new_value = allele.value + delta
        new_value = max(min_val, min(max_val, new_value))  # clampeo
        
        # Mutar dominancia opcionalmente
        if mutation_config.mutate_dominance:
            dom_delta = random.gauss(0, mutation_config.dominance_std)
            new_dominance = max(0.0, min(1.0, allele.dominance + dom_delta))
        else:
            new_dominance = allele.dominance
        
        return Allele(value=new_value, dominance=new_dominance)

    def combine(
        self, 
        other_genome: Optional['Genome'],
        mutation_config: Optional['MutationConfig'] = None,
    ) -> 'Genome':
        """Cruza este genotipo con el de una pareja mediante meiosis.
        
        GENÉTICA UNIVERSAL: Recombina todos los rasgos presentes en ambos progenitores.
        Usa MutationConfig para controlar la mutación.
        
        Args:
            other_genome: El genoma del otro progenitor (None = partenogénesis).
            mutation_config: Configuración de mutación (None = defecto).
        """
        if other_genome is None:
            other_genome = self

        if self._species_id != other_genome.species_id:
            self.logger.warning("Cruce interespecie. El híbrido heredará la línea materna.")

        if mutation_config is None:
            from core.config.simulation_config import MutationConfig
            mutation_config = MutationConfig()

        # Recombinar todos los genes presentes en ambos progenitores
        all_base_genes = set(self._genes.keys()) | set(other_genome._genes.keys())
        new_genes = self._recombine_genes(
            self._genes, 
            other_genome._genes, 
            all_base_genes, 
            mutation_config,
            default_base_value=0.5
        )

        # Recombinar genes específicos por familia
        all_families = set(self._family_specific_immunity.keys()) | set(other_genome._family_specific_immunity.keys())
        new_family_immunity = self._recombine_genes(
            self._family_specific_immunity, 
            other_genome._family_specific_immunity, 
            all_families, 
            mutation_config,
            default_base_value=1.0
        )

        return Genome(
            genes=new_genes,
            species_id=self._species_id,
            family_specific_immunity=new_family_immunity,
        )

    def replicate(
        self, 
        mutation_config: Optional['MutationConfig'] = None,
    ) -> 'Genome':
        """Reproducción asexual: crea un clon con mutación.
        
        GENÉTICA UNIVERSAL (sección 3.2 del spec):
        - Copia todos los genes del progenitor
        - Aplica mutación a cada alelo según MutationConfig
        - No hay meiosis ni recombinación
        - Aplicable a bacterias, plantas asexuales, organismos unicelulares
        
        Diferencia clave con combine():
        - combine(): dos progenitores → recombinación + mutación
        - replicate(): un progenitor → clon + mutación
        
        Args:
            mutation_config: Configuración de mutación (None = defecto).
            
        Returns:
            Un nuevo Genome clonado con mutaciones aplicadas.
        """
        if mutation_config is None:
            from core.config.simulation_config import MutationConfig
            mutation_config = MutationConfig()
        
        # Clonar genes con mutación
        new_genes = {}
        for trait_id, gene in self._genes.items():
            new_allele_a = self._mutate_allele(gene.allele_a, trait_id, mutation_config)
            new_allele_b = self._mutate_allele(gene.allele_b, trait_id, mutation_config)
            new_genes[trait_id] = Gene(new_allele_a, new_allele_b)
        
        # Clonar inmunidad específica con mutación
        new_family_immunity = {}
        for family, gene in self._family_specific_immunity.items():
            new_allele_a = self._mutate_allele(gene.allele_a, family, mutation_config)
            new_allele_b = self._mutate_allele(gene.allele_b, family, mutation_config)
            new_family_immunity[family] = Gene(new_allele_a, new_allele_b)
        
        return Genome(
            genes=new_genes,
            species_id=self._species_id,
            family_specific_immunity=new_family_immunity,
        )

    def __repr__(self) -> str:
        """Representación string del genoma para debugging."""
        base_genes = {k: round(v.express(), 2) for k, v in self._genes.items()}
        family_immunity = {k: round(v.express(), 2) for k, v in self._family_specific_immunity.items()}
        return f"Genome(species={self._species_id}, traits={base_genes}, family_immunity={family_immunity})"