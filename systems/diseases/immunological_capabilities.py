"""Capacidades inmunológicas derivadas del genoma.

Este módulo consulta el genoma de un organismo y determina qué tipo de
sistema inmune tiene, a qué patógenos es susceptible, y si puede
formar memoria inmunológica.

Es la capa de abstracción entre el núcleo genético (agnóstico a especie)
y el sistema de enfermedades (que necesita saber susceptibilidades concretas).

Diseño:
- INMUTABLE: Se crea una vez consultando el genoma, no se modifica
- AGNÓSTICO: No conoce especies, solo consulta rasgos
- EXTENSIBLE: Se pueden añadir nuevas capacidades sin romper existentes
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entities.person.genome import Genome


@dataclass
class ImmunologicalCapabilities:
    """Capacidades inmunológicas derivadas del genoma de un organismo.
    
    Esta clase es inmutable y se crea consultando el genoma.
    Determina QUÉ tipo de sistema inmune tiene un organismo y a qué
    patógenos es susceptible.
    
    Atributos:
        has_immune_system: ¿Tiene sistema inmune? (immunity > 0.1)
        has_adaptive_immunity: ¿Tiene inmunidad adaptativa? (vertebrados)
        has_innate_immunity: ¿Tiene inmunidad innata?
        susceptible_to_viruses: ¿Puede infectarse con virus complejos?
        susceptible_to_bacteria: ¿Puede infectarse con bacterias?
        susceptible_to_fungi: ¿Puede infectarse con hongos?
        can_get_sick: ¿Puede enfermarse en general?
        can_die_from_disease: ¿Puede morir por enfermedad?
        can_form_immunological_memory: ¿Puede recordar enfermedades?
    """
    
    # === CAPACIDADES BÁSICAS ===
    has_immune_system: bool = False        # ¿Tiene sistema inmune?
    has_adaptive_immunity: bool = False    # ¿Tiene inmunidad adaptativa?
    has_innate_immunity: bool = False      # ¿Tiene inmunidad innata?
    
    # === SUSCEPTIBILIDAD A PATÓGENOS ===
    susceptible_to_viruses: bool = False   # ¿Puede infectarse con virus?
    susceptible_to_bacteria: bool = False  # ¿Puede infectarse con bacterias?
    susceptible_to_fungi: bool = False     # ¿Puede infectarse con hongos?
    
    # === CAPACIDADES DE ENFERMEDAD ===
    can_get_sick: bool = False             # ¿Puede enfermarse en general?
    can_die_from_disease: bool = False     # ¿Puede morir por enfermedad?
    can_form_immunological_memory: bool = False  # ¿Puede recordar enfermedades?
    
    @classmethod
    def from_genome(cls, genome: 'Genome') -> 'ImmunologicalCapabilities':
        """Crea ImmunologicalCapabilities consultando el genoma.
        
        Este método es la única forma de crear ImmunologicalCapabilities.
        Consulta el genoma y deriva las capacidades de forma determinista.
        
        Args:
            genome: El genoma del organismo.
            
        Returns:
            ImmunologicalCapabilities con las capacidades derivadas.
            
        Note:
            Si un rasgo no existe en el genoma, usa valores por defecto
            apropiados para organismos que no tienen ese rasgo.
            
        Examples:
            >>> caps = ImmunologicalCapabilities.from_genome(human_genome)
            >>> caps.has_adaptive_immunity
            True
            >>> caps.susceptible_to_viruses
            True
            
            >>> caps = ImmunologicalCapabilities.from_genome(plant_genome)
            >>> caps.can_get_sick
            False
        """
        # Helper para obtener valor de rasgo de forma segura
        def get_trait(trait_id: str, default: float = 0.0) -> float:
            """Obtiene el valor de un rasgo, retornando default si no existe."""
            if genome.has_trait(trait_id):
                return genome.get_trait_value(trait_id)
            return default
        
        # === OBTENER VALORES DE RASGOS ===
        immunity = get_trait("immunity", 0.5)
        nervous_system = get_trait("nervous_system", 0.3)
        metabolism = get_trait("metabolism", 0.5)
        heterotrophy = get_trait("heterotrophy", 0.5)
        photosynthesis = get_trait("photosynthesis", 0.0)
        longevity = get_trait("longevity", 1.0)
        
        # === CAPACIDADES BÁSICAS ===
        # ¿Tiene sistema inmune? (immunity > 0.1)
        has_immune_system = immunity > 0.1
        
        # ¿Tiene inmunidad adaptativa? (vertebrados)
        # Requiere: immunity alto + nervous_system desarrollado
        has_adaptive_immunity = immunity > 0.5 and nervous_system > 0.3
        
        # ¿Tiene inmunidad innata? (todos con sistema inmune)
        has_innate_immunity = has_immune_system
        
        # === SUSCEPTIBILIDAD A PATÓGENOS ===
        
        # Virus complejos (Influenza, Coronavirus, etc.):
        # Requieren organismo eucariota (con sistema nervioso al menos básico)
        # Las bacterias NO son susceptibles a virus animales (solo a bacteriófagos)
        is_eukaryote_like = nervous_system > 0.1
        susceptible_to_viruses = (
            is_eukaryote_like and 
            metabolism > 0.3 and 
            not (photosynthesis > 0.7 and heterotrophy < 0.3)
        )
        
        # Bacterias: la mayoría de organismos complejos son susceptibles
        susceptible_to_bacteria = metabolism > 0.2
        
        # Hongos: organismos con metabolismo activo e inmunidad no perfecta
        susceptible_to_fungi = metabolism > 0.3 and immunity < 0.95
        
        # === CAPACIDADES DE ENFERMEDAD ===
        # ¿Puede enfermarse? (tiene sistema inmune O metabolismo activo)
        can_get_sick = has_immune_system or metabolism > 0.3
        
        # ¿Puede morir por enfermedad? (organismos complejos con longevidad limitada)
        can_die_from_disease = can_get_sick and longevity < 2.0 and metabolism > 0.3
        
        # ¿Puede formar memoria inmunológica? (requiere sistema nervioso + inmunidad adaptativa)
        can_form_immunological_memory = has_adaptive_immunity and nervous_system > 0.5
        
        return cls(
            has_immune_system=has_immune_system,
            has_adaptive_immunity=has_adaptive_immunity,
            has_innate_immunity=has_innate_immunity,
            susceptible_to_viruses=susceptible_to_viruses,
            susceptible_to_bacteria=susceptible_to_bacteria,
            susceptible_to_fungi=susceptible_to_fungi,
            can_get_sick=can_get_sick,
            can_die_from_disease=can_die_from_disease,
            can_form_immunological_memory=can_form_immunological_memory,
        )
    
    def is_susceptible_to(self, pathogen_family: str) -> bool:
        """Verifica si el organismo es susceptible a una familia de patógenos.
        
        Args:
            pathogen_family: Nombre de la familia del patógeno
                            (ej: "Influenza", "Coronavirus", "Bacteria", "Fungus")
            
        Returns:
            True si el organismo es susceptible, False en caso contrario.
            
        Examples:
            >>> caps = ImmunologicalCapabilities.from_genome(human_genome)
            >>> caps.is_susceptible_to("Influenza")
            True
            >>> caps.is_susceptible_to("Bacteriofago_X")
            False
        """
        family_lower = pathogen_family.lower()
        
        # Virus complejos (Influenza, Coronavirus, Poxvirus)
        if "virus" in family_lower or "influenza" in family_lower or "coronavirus" in family_lower or "poxvirus" in family_lower:
            return self.susceptible_to_viruses
        
        # Bacterias
        if "bacteria" in family_lower or "bacteriofago" in family_lower:
            return self.susceptible_to_bacteria
        
        # Hongos
        if "fungus" in family_lower or "hongo" in family_lower:
            return self.susceptible_to_fungi
        
        # Por defecto, asumir susceptible si puede enfermarse
        return self.can_get_sick
    
    def __str__(self) -> str:
        """Representación legible para debugging.
        
        Returns:
            String con las capacidades principales en formato compacto.
            
        Examples:
            >>> str(caps)
            "ImmunologicalCapabilities(immune=True, adaptive=True, viruses=True, bacteria=True, memory=True)"
        """
        return (
            f"ImmunologicalCapabilities("
            f"immune={self.has_immune_system}, "
            f"adaptive={self.has_adaptive_immunity}, "
            f"viruses={self.susceptible_to_viruses}, "
            f"bacteria={self.susceptible_to_bacteria}, "
            f"memory={self.can_form_immunological_memory}"
            f")"
        )
    
    def __repr__(self) -> str:
        """Representación completa para debugging."""
        return (
            f"ImmunologicalCapabilities("
            f"has_immune_system={self.has_immune_system}, "
            f"has_adaptive_immunity={self.has_adaptive_immunity}, "
            f"has_innate_immunity={self.has_innate_immunity}, "
            f"susceptible_to_viruses={self.susceptible_to_viruses}, "
            f"susceptible_to_bacteria={self.susceptible_to_bacteria}, "
            f"susceptible_to_fungi={self.susceptible_to_fungi}, "
            f"can_get_sick={self.can_get_sick}, "
            f"can_die_from_disease={self.can_die_from_disease}, "
            f"can_form_immunological_memory={self.can_form_immunological_memory}"
            f")"
        )