"""Capacidades reproductivas derivadas del genoma.

Este módulo consulta el genoma de un organismo y determina cómo se reproduce,
qué tipo de gestación tiene, y qué cuidado parental proporciona.

Es la capa de abstracción entre el núcleo genético (agnóstico a especie)
y los sistemas de reproducción (ConceptionSystem, GestationSystem).

Diseño:
- INMUTABLE: Se crea una vez consultando el genoma, no se modifica
- AGNÓSTICO: No conoce especies, solo consulta rasgos
- EXTENSIBLE: Se pueden añadir nuevas capacidades sin romper existentes

Tipos de reproducción biológica:
- Asexual: Fisión binaria, esporas, clonación (plantas, bacterias)
- Sexual: Requiere dos progenitores (animales)
- Partenogénesis: Hembra sin macho (algunas especies)

Tipos de gestación:
- Vivípara: Gestación interna, crías vivas (mamíferos)
- Ovípara: Pone huevos (aves, peces, insectos, reptiles)
- Sin gestación: Liberación de gametos o esporas (plantas, bacterias)
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entities.person.genome import Genome


@dataclass
class ReproductiveCapabilities:
    """Capacidades reproductivas derivadas del genoma de un organismo.
    
    Esta clase es inmutable y se crea consultando el genoma.
    Determina QUÉ tipo de reproducción tiene un organismo y cómo
    se desarrolla su descendencia.
    
    Atributos:
        can_reproduce: ¿Puede reproducirse en general?
        reproduction_type: Tipo de reproducción (asexual, sexual, parthenogenesis)
        requires_partner: ¿Requiere pareja para reproducirse?
        can_gestate: ¿Puede gestar descendencia?
        gestation_type: Tipo de gestación (viviparous, oviparous, none)
        has_parental_care: ¿Proporciona cuidado parental?
        can_conceive: ¿Puede concebir (quedar embarazada)?
        has_postpartum: ¿Tiene periodo posparto?
        fertility_level: Nivel de fertilidad (0.0 a 1.0)
        litter_size_min: Tamaño mínimo de camada
        litter_size_max: Tamaño máximo de camada
    """
    
    # === CAPACIDADES BÁSICAS ===
    can_reproduce: bool = False           # ¿Puede reproducirse?
    reproduction_type: str = "asexual"    # "asexual", "sexual", "parthenogenesis"
    requires_partner: bool = False        # ¿Requiere pareja?
    
    # === GESTACIÓN ===
    can_gestate: bool = False             # ¿Puede gestar?
    gestation_type: str = "none"          # "viviparous", "oviparous", "none"
    gestation_days: float = 0.0           # Duración de gestación/incubación
    
    # === CUIDADO PARENTAL ===
    has_parental_care: bool = False       # ¿Proporciona cuidado parental?
    care_duration_days: float = 0.0       # Duración del cuidado parental
    
    # === CARACTERÍSTICAS REPRODUCTIVAS ===
    can_conceive: bool = False            # ¿Puede concebir (quedar embarazada)?
    has_postpartum: bool = False          # ¿Tiene periodo posparto?
    fertility_level: float = 0.0          # Nivel de fertilidad (0.0 a 1.0)
    
    # === CAMADA ===
    litter_size_min: int = 1              # Tamaño mínimo de camada
    litter_size_max: int = 1              # Tamaño máximo de camada
    
    @classmethod
    def from_genome(cls, genome: 'Genome') -> 'ReproductiveCapabilities':
        """Crea ReproductiveCapabilities consultando el genoma.
        
        Este método es la única forma de crear ReproductiveCapabilities.
        Consulta el genoma y deriva las capacidades de forma determinista.
        
        Args:
            genome: El genoma del organismo.
            
        Returns:
            ReproductiveCapabilities con las capacidades derivadas.
            
        Note:
            Si un rasgo no existe en el genoma, usa valores por defecto
            apropiados para organismos que no tienen ese rasgo.
            
        Examples:
            >>> caps = ReproductiveCapabilities.from_genome(human_genome)
            >>> caps.gestation_type
            "viviparous"
            >>> caps.has_parental_care
            True
            
            >>> caps = ReproductiveCapabilities.from_genome(plant_genome)
            >>> caps.reproduction_type
            "asexual"
            >>> caps.can_gestate
            False
        """
        # Helper para obtener valor de rasgo de forma segura
        def get_trait(trait_id: str, default: float = 0.0) -> float:
            """Obtiene el valor de un rasgo, retornando default si no existe."""
            if genome.has_trait(trait_id):
                return genome.get_trait_value(trait_id)
            return default
        
        # === OBTENER VALORES DE RASGOS ===
        fertility = get_trait("fertility", 0.5)
        metabolism = get_trait("metabolism", 0.5)
        nervous_system = get_trait("nervous_system", 0.0)
        intelligence = get_trait("intelligence", 0.0)
        sociability = get_trait("sociability", 0.0)
        heterotrophy = get_trait("heterotrophy", 0.0)
        longevity = get_trait("longevity", 1.0)
        
        # === CAPACIDADES BÁSICAS ===
        # Todos los organismos pueden reproducirse de alguna forma
        can_reproduce = fertility > 0.0 and metabolism > 0.1
        
        # Tipo de reproducción
        # Si tiene sistema nervioso, es sexual; si no, es asexual
        if nervous_system > 0.1:
            reproduction_type = "sexual"
            # Requiere pareja solo si es muy social (interacción directa)
            # Peces, anfibios: fertilización externa (no requieren pareja directa)
            # Aves, mamíferos: cópula (requieren pareja)
            requires_partner = sociability >= 0.6
        else:
            reproduction_type = "asexual"
            requires_partner = False
        
        # === GESTACIÓN ===
        # Solo organismos complejos (con sistema nervioso) pueden gestar
        can_gestate = nervous_system > 0.3
        
        # Tipo de gestación
        if not can_gestate:
            gestation_type = "none"
            gestation_days = 0.0
        elif nervous_system >= 0.7 and heterotrophy >= 0.7:
            # Mamíferos: vivíparos
            gestation_type = "viviparous"
            # Duración basada en longevidad (especies longevas = gestación larga)
            # Humanos (longevity=1.0): ~270 días
            # Lobos (longevity=0.5): ~60 días
            # Ratones (longevity=0.2): ~20 días
            gestation_days = max(30.0, min(300.0, longevity * 270.0))
        else:
            # Aves, peces, reptiles, insectos: ovíparos
            gestation_type = "oviparous"
            # Incubación más corta que gestación vivípara
            # Aves (longevity=1.0): ~30 días
            # Peces (longevity=0.5): ~15 días
            gestation_days = max(7.0, min(60.0, longevity * 30.0))
        
        # === CUIDADO PARENTAL ===
        # Solo organismos con inteligencia y sociabilidad altas
        has_parental_care = intelligence > 0.5 and sociability > 0.6
        
        if has_parental_care:
            # Duración basada en inteligencia (más inteligente = más cuidado)
            care_duration_days = intelligence * 365.0 * 2.0  # Hasta 2 años
        else:
            care_duration_days = 0.0
        
        # === CARACTERÍSTICAS REPRODUCTIVAS ===
        # Solo vivíparos pueden concebir (quedar embarazados)
        can_conceive = gestation_type == "viviparous"
        
        # Solo mamíferos tienen periodo posparto
        has_postpartum = gestation_type == "viviparous" and has_parental_care
        
        # Nivel de fertilidad (0.0 a 1.0)
        fertility_level = max(0.0, min(1.0, fertility))
        
        # === CAMADA ===
        # Tamaño basado en estrategia reproductiva
        if not can_reproduce:
            litter_size_min = 0
            litter_size_max = 0
        elif gestation_type == "viviparous":
            # Mamíferos: camadas pequeñas
            litter_size_min = 1
            litter_size_max = max(1, int(3 - longevity))  # Especies longevas = menos crías
        elif gestation_type == "oviparous":
            # Ovíparos: muchos huevos
            litter_size_min = 2
            litter_size_max = max(2, int(10 - longevity * 2))
        else:
            # Asexual: muchos descendientes
            litter_size_min = 1
            litter_size_max = max(1, int(100 / max(0.1, longevity)))
        
        # Asegurar que min <= max
        litter_size_max = max(litter_size_min, litter_size_max)
        
        return cls(
            can_reproduce=can_reproduce,
            reproduction_type=reproduction_type,
            requires_partner=requires_partner,
            can_gestate=can_gestate,
            gestation_type=gestation_type,
            gestation_days=gestation_days,
            has_parental_care=has_parental_care,
            care_duration_days=care_duration_days,
            can_conceive=can_conceive,
            has_postpartum=has_postpartum,
            fertility_level=fertility_level,
            litter_size_min=litter_size_min,
            litter_size_max=litter_size_max,
        )
    
    def is_sexual_reproduction(self) -> bool:
        """Verifica si usa reproducción sexual."""
        return self.reproduction_type in ("sexual", "parthenogenesis")
    
    def is_asexual_reproduction(self) -> bool:
        """Verifica si usa reproducción asexual."""
        return self.reproduction_type == "asexual"
    
    def is_viviparous(self) -> bool:
        """Verifica si es vivíparo."""
        return self.gestation_type == "viviparous"
    
    def is_oviparous(self) -> bool:
        """Verifica si es ovíparo."""
        return self.gestation_type == "oviparous"
    
    def can_form_nucleus(self) -> bool:
        """Verifica si puede formar núcleo residencial (requiere cuidado parental)."""
        return self.has_parental_care
    
    def __str__(self) -> str:
        """Representación legible para debugging."""
        return (
            f"ReproductiveCapabilities("
            f"type={self.reproduction_type}, "
            f"gestation={self.gestation_type}, "
            f"care={self.has_parental_care}, "
            f"fertility={self.fertility_level:.2f}, "
            f"litter={self.litter_size_min}-{self.litter_size_max}"
            f")"
        )
    
    def __repr__(self) -> str:
        """Representación completa para debugging."""
        return (
            f"ReproductiveCapabilities("
            f"can_reproduce={self.can_reproduce}, "
            f"reproduction_type={self.reproduction_type}, "
            f"requires_partner={self.requires_partner}, "
            f"can_gestate={self.can_gestate}, "
            f"gestation_type={self.gestation_type}, "
            f"gestation_days={self.gestation_days}, "
            f"has_parental_care={self.has_parental_care}, "
            f"care_duration_days={self.care_duration_days}, "
            f"can_conceive={self.can_conceive}, "
            f"has_postpartum={self.has_postpartum}, "
            f"fertility_level={self.fertility_level}, "
            f"litter_size_min={self.litter_size_min}, "
            f"litter_size_max={self.litter_size_max}"
            f")"
        )