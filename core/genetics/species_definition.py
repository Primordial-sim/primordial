"""Definición de una especie con soporte para herencia entre plantillas.

FILOSOFÍA:
- Las plantillas son puntos de partida, NO categorías cerradas.
- Una especie puede heredar rasgos de otra plantilla.
- La plantilla "empty" permite crear especies completamente desde cero.
- El usuario siempre tiene libertad absoluta para modificar.
- Las especies pueden definir preferencias de hábitat (condiciones ambientales).

Jerarquía por defecto:
    empty
    animal
    ├── vertebrate
    │   ├── mammal → human
    │   ├── bird
    │   ├── reptile
    │   ├── amphibian
    │   └── fish
    └── invertebrate → insect
    plant
    fungus
    bacteria
    fantasy
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
import logging

from core.genetics.trait_library import TraitLibrary
from systems.environment.habitat_preference import HabitatPreference


@dataclass
class TraitConfig:
    """Configuración de un rasgo para una especie específica.
    
    Attributes:
        default_value: Valor por defecto para esta especie.
        min_value: Valor mínimo permitido.
        max_value: Valor máximo permitido.
        weight: Importancia del rasgo para esta especie.
        is_heritable: Si este rasgo se hereda en esta especie.
    """
    default_value: float = 0.5
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    weight: float = 1.0
    is_heritable: bool = True


class SpeciesDefinition:
    """Define una especie mediante los rasgos que utiliza.
    
    Soporta herencia: una especie puede tener un parent_template del que
    hereda rasgos. Los rasgos locales sobrescriben los heredados.
    
    Attributes:
        species_id: Identificador único de la especie.
        name: Nombre legible de la especie.
        description: Descripción de la especie.
        archetype: Categoría biológica base.
        parent_template: ID de la plantilla de la que hereda (None si no hereda).
        trait_configs: Diccionario de trait_id -> TraitConfig (solo rasgos locales).
        habitat_preference: Preferencias ambientales de la especie.
    """
    
    _logger = logging.getLogger("SpeciesDefinition")
    
    def __init__(
        self,
        species_id: str,
        name: str,
        description: str = "",
        trait_configs: Optional[Dict[str, TraitConfig]] = None,
        archetype: str = "custom",
        parent_template: Optional[str] = None,
        habitat_preference: Optional[HabitatPreference] = None,
    ) -> None:
        self.species_id = species_id
        self.name = name
        self.description = description
        self.archetype = archetype
        self.parent_template = parent_template
        self._trait_configs: Dict[str, TraitConfig] = trait_configs or {}
        self._habitat_preference: Optional[HabitatPreference] = habitat_preference
    
    # =================================================================
    # CONSTRUCTORES ALTERNATIVOS (FACTORIES)
    # =================================================================
    
    @classmethod
    def from_template(
        cls,
        species_id: str,
        name: str,
        base_template: str,
        description: str = "",
        archetype: str = "custom",
        habitat_preference: Optional[HabitatPreference] = None,
    ) -> 'SpeciesDefinition':
        """Crea una especie heredando de una plantilla existente.
        
        Args:
            species_id: ID único de la nueva especie.
            name: Nombre legible.
            base_template: ID de la plantilla de la que hereda.
            description: Descripción.
            archetype: Categoría biológica.
            habitat_preference: Preferencias de hábitat opcionales.
            
        Returns:
            Nueva SpeciesDefinition con parent_template establecido.
        """
        return cls(
            species_id=species_id,
            name=name,
            description=description,
            archetype=archetype,
            parent_template=base_template,
            habitat_preference=habitat_preference,
        )
    
    @classmethod
    def empty(
        cls,
        species_id: str,
        name: str,
        description: str = "Especie creada desde cero",
    ) -> 'SpeciesDefinition':
        """Crea una especie vacía sin rasgos iniciales.
        
        Punto de partida para especies completamente personalizadas.
        """
        return cls(
            species_id=species_id,
            name=name,
            description=description,
            archetype="empty",
            parent_template=None,
        )
    
    # =================================================================
    # GESTIÓN DE RASGOS
    # =================================================================
    
    def add_trait(
        self,
        trait_id: str,
        default_value: float = 0.5,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        weight: float = 1.0,
        is_heritable: bool = True,
    ) -> 'SpeciesDefinition':
        """Añade o sobrescribe un rasgo. Retorna self para encadenamiento."""
        self._trait_configs[trait_id] = TraitConfig(
            default_value=default_value,
            min_value=min_value,
            max_value=max_value,
            weight=weight,
            is_heritable=is_heritable,
        )
        return self
    
    def remove_trait(self, trait_id: str) -> 'SpeciesDefinition':
        """Elimina un rasgo local (no afecta al heredado). Retorna self."""
        if trait_id in self._trait_configs:
            del self._trait_configs[trait_id]
        return self
    
    def has_local_trait(self, trait_id: str) -> bool:
        """Verifica si la especie define LOCALMENTE un rasgo (sin contar herencia)."""
        return trait_id in self._trait_configs
    
    def has_trait(self, trait_id: str) -> bool:
        """Verifica si la especie tiene un rasgo (local o heredado)."""
        return trait_id in self.get_all_trait_ids()
    
    def get_trait_config(self, trait_id: str) -> Optional[TraitConfig]:
        """Obtiene la configuración efectiva de un rasgo (local o heredado)."""
        # Primero buscar en los rasgos locales
        if trait_id in self._trait_configs:
            return self._trait_configs[trait_id]
        
        # Si hay padre, buscar en la cadena de herencia
        parent = self._get_parent()
        if parent is not None:
            return parent.get_trait_config(trait_id)
        
        return None
    
    def get_local_trait_ids(self) -> Set[str]:
        """Retorna solo los IDs de rasgos definidos localmente."""
        return set(self._trait_configs.keys())
    
    def get_all_trait_ids(self) -> Set[str]:
        """Retorna todos los IDs de rasgos (locales + heredados)."""
        local = set(self._trait_configs.keys())
        
        parent = self._get_parent()
        if parent is not None:
            inherited = parent.get_all_trait_ids()
            return local | inherited
        
        return local
    
    def get_trait_count(self) -> int:
        """Retorna el número total de rasgos (locales + heredados)."""
        return len(self.get_all_trait_ids())
    
    def get_local_trait_count(self) -> int:
        """Retorna el número de rasgos definidos localmente."""
        return len(self._trait_configs)
    
    def get_default_value(self, trait_id: str, library: TraitLibrary) -> float:
        """Obtiene el valor por defecto efectivo de un rasgo."""
        config = self.get_trait_config(trait_id)
        if config is not None:
            return config.default_value
        
        trait = library.get_trait(trait_id)
        if trait is not None:
            return trait.default_value
        
        return 0.5
    
    def get_effective_range(self, trait_id: str, library: TraitLibrary) -> tuple:
        """Obtiene el rango efectivo (min, max) de un rasgo."""
        config = self.get_trait_config(trait_id)
        trait = library.get_trait(trait_id)
        
        if trait is None:
            return (0.0, 1.0)
        
        min_val = config.min_value if config and config.min_value is not None else trait.min_value
        max_val = config.max_value if config and config.max_value is not None else trait.max_value
        
        return (min_val, max_val)
    
    # =================================================================
    # PREFERENCIAS DE HÁBITAT (NUEVO)
    # =================================================================
    
    def set_habitat_preference(self, preference: HabitatPreference) -> 'SpeciesDefinition':
        """Establece las preferencias de hábitat para esta especie.
        
        Args:
            preference: Las preferencias de hábitat.
            
        Returns:
            self para encadenamiento.
        """
        self._habitat_preference = preference
        return self
    
    def get_habitat_preference(self) -> Optional[HabitatPreference]:
        """Obtiene las preferencias de hábitat de esta especie.
        
        Si la especie no tiene preferencias propias, hereda del padre.
        """
        # Primero verificar si tiene preferencias propias
        if self._habitat_preference is not None:
            return self._habitat_preference
        
        # Si hay padre, heredar preferencias
        parent = self._get_parent()
        if parent is not None:
            return parent.get_habitat_preference()
        
        return None
    
    def has_habitat_preference(self) -> bool:
        """Verifica si la especie tiene preferencias de hábitat (propia o heredada)."""
        return self.get_habitat_preference() is not None
    
    # =================================================================
    # HERENCIA
    # =================================================================
    
    def _get_parent(self) -> Optional['SpeciesDefinition']:
        """Obtiene la plantilla padre del registro (si existe)."""
        if self.parent_template is None:
            return None
        
        # Evitar acceso circular al registro durante la inicialización
        if not SpeciesRegistry.has(self.parent_template):
            return None
        
        return SpeciesRegistry.get(self.parent_template)
    
    def get_inheritance_chain(self) -> List[str]:
        """Retorna la cadena completa de herencia (de más específica a más general)."""
        chain = [self.species_id]
        current = self
        visited = {self.species_id}
        
        while current.parent_template is not None:
            if current.parent_template in visited:
                break  # Evitar bucles infinitos
            chain.append(current.parent_template)
            visited.add(current.parent_template)
            
            parent = SpeciesRegistry.get(current.parent_template)
            if parent is None:
                break
            current = parent
        
        return chain
    
    def __repr__(self) -> str:
        parent_str = f" <- {self.parent_template}" if self.parent_template else ""
        habitat_str = " [habitat]" if self.has_habitat_preference() else ""
        return (
            f"SpeciesDefinition({self.species_id}: {self.name} "
            f"[{self.archetype}]{parent_str}{habitat_str}, "
            f"{self.get_trait_count()} traits)"
        )


# =============================================================================
# PLANTILLAS BIOLÓGICAS (CON HERENCIA)
# =============================================================================

def create_empty_template() -> SpeciesDefinition:
    """Plantilla vacía: punto de partida para especies completamente personalizadas."""
    return SpeciesDefinition(
        species_id="empty",
        name="Vacía",
        description="Plantilla vacía. Punto de partida para crear especies desde cero.",
        archetype="empty",
        parent_template=None,
    )


def create_animal_template() -> SpeciesDefinition:
    """Plantilla base para todos los animales.
    
    Contiene los rasgos mínimos comunes a cualquier animal:
    metabolismo, inmunidad, longevidad, reproducción, movimiento.
    """
    from systems.environment.habitat_preference import create_human_habitat
    
    return SpeciesDefinition(
        species_id="animal",
        name="Animal",
        description="Plantilla base para todos los animales.",
        archetype="animal",
        parent_template="empty",
    ).add_trait("fertility", default_value=1.0, weight=1.0) \
     .add_trait("immunity", default_value=1.0, weight=1.0) \
     .add_trait("longevity", default_value=1.0, weight=1.0) \
     .add_trait("metabolism", default_value=1.0, weight=1.0) \
     .add_trait("growth_rate", default_value=1.0, weight=0.8) \
     .add_trait("healing", default_value=0.7, weight=0.7) \
     .add_trait("speed", default_value=1.0, weight=0.8) \
     .add_trait("vision", default_value=0.8, weight=0.7) \
     .add_trait("heterotrophy", default_value=1.0, weight=1.0) \
     .set_habitat_preference(create_human_habitat())


def create_vertebrate_template() -> SpeciesDefinition:
    """Plantilla base para vertebrados.
    
    Hereda de animal y añade sistema nervioso y percepción avanzada.
    """
    return SpeciesDefinition(
        species_id="vertebrate",
        name="Vertebrado",
        description="Plantilla base para vertebrados.",
        archetype="vertebrate",
        parent_template="animal",
    ).add_trait("nervous_system", default_value=1.0, weight=1.0) \
     .add_trait("hearing", default_value=0.7, weight=0.6) \
     .add_trait("smell", default_value=0.8, weight=0.7) \
     .add_trait("intelligence", default_value=0.5, weight=0.6)


def create_invertebrate_template() -> SpeciesDefinition:
    """Plantilla base para invertebrados.
    
    Hereda de animal pero con sistema nervioso mínimo.
    """
    return SpeciesDefinition(
        species_id="invertebrate",
        name="Invertebrado",
        description="Plantilla base para invertebrados.",
        archetype="invertebrate",
        parent_template="animal",
    ).add_trait("nervous_system", default_value=0.3, weight=0.8) \
     .add_trait("smell", default_value=1.2, weight=0.8) \
     .add_trait("intelligence", default_value=0.1, weight=0.4)


def create_mammal_template() -> SpeciesDefinition:
    """Plantilla base para mamíferos.
    
    Hereda de vertebrado y añade sociabilidad, cuidado parental.
    """
    return SpeciesDefinition(
        species_id="mammal",
        name="Mamífero",
        description="Plantilla base para mamíferos: vivíparos, sangre caliente.",
        archetype="mammal",
        parent_template="vertebrate",
    ).add_trait("sociability", default_value=1.0, weight=0.9) \
     .add_trait("temperament", default_value=1.0, weight=0.8) \
     .add_trait("aggressiveness", default_value=0.7, weight=0.7) \
     .add_trait("territoriality", default_value=1.0, weight=0.8) \
     .add_trait("cooperation", default_value=0.8, weight=0.7) \
     .add_trait("curiosity", default_value=0.7, weight=0.6) \
     .add_trait("empathy", default_value=0.6, weight=0.6) \
     .add_trait("nervous_system", default_value=1.3, weight=1.0) \
     .add_trait("metabolism", default_value=1.2, weight=0.9)


def create_human_species() -> SpeciesDefinition:
    """Humano: mamífero con inteligencia y sociabilidad extremas."""
    from systems.environment.habitat_preference import create_human_habitat
    
    return SpeciesDefinition(
        species_id="human",
        name="Humano",
        description="Mamífero altamente inteligente con comportamiento social complejo.",
        archetype="mammal",
        parent_template="mammal",
    ).add_trait("fertility", default_value=1.0, weight=1.0) \
     .add_trait("sociability", default_value=1.5, weight=1.0) \
     .add_trait("curiosity", default_value=1.3, weight=0.9) \
     .add_trait("impulsivity", default_value=0.5, weight=0.7) \
     .add_trait("obedience", default_value=0.7, weight=0.7) \
     .add_trait("aggressiveness", default_value=0.5, weight=0.7) \
     .add_trait("intelligence", default_value=1.8, weight=1.0) \
     .add_trait("empathy", default_value=1.0, weight=0.9) \
     .add_trait("cooperation", default_value=1.3, weight=0.9) \
     .add_trait("nervous_system", default_value=1.8, weight=1.0) \
     .set_habitat_preference(create_human_habitat())


def create_bird_species() -> SpeciesDefinition:
    """Ave: vertebrado volador con visión excelente."""
    from systems.environment.habitat_preference import create_bird_habitat
    
    return SpeciesDefinition(
        species_id="bird",
        name="Ave",
        description="Vertebrado volador con excelente visión y metabolismo alto.",
        archetype="bird",
        parent_template="vertebrate",
    ).add_trait("fertility", default_value=0.5, weight=1.0) \
     .add_trait("metabolism", default_value=1.6, weight=1.0) \
     .add_trait("flight", default_value=1.8, weight=1.0) \
     .add_trait("vision", default_value=1.8, weight=1.0) \
     .add_trait("speed", default_value=1.5, weight=0.9) \
     .add_trait("territoriality", default_value=1.5, weight=0.9) \
     .add_trait("aggressiveness", default_value=1.0, weight=0.7) \
     .add_trait("cooperation", default_value=0.6, weight=0.5) \
     .set_habitat_preference(create_bird_habitat())


def create_reptile_species() -> SpeciesDefinition:
    """Reptil: vertebrado de sangre fría, longevo."""
    return SpeciesDefinition(
        species_id="reptile",
        name="Reptil",
        description="Vertebrado de sangre fría, longevo, metabolismo lento.",
        archetype="reptile",
        parent_template="vertebrate",
    ).add_trait("fertility", default_value=0.6, weight=1.0) \
     .add_trait("longevity", default_value=1.6, weight=1.0) \
     .add_trait("metabolism", default_value=0.5, weight=1.0) \
     .add_trait("territoriality", default_value=1.6, weight=0.9) \
     .add_trait("aggressiveness", default_value=1.2, weight=0.8) \
     .add_trait("sociability", default_value=0.3, weight=0.5) \
     .add_trait("venom", default_value=0.2, weight=0.3)


def create_fish_species() -> SpeciesDefinition:
    """Pez: vertebrado acuático."""
    from systems.environment.habitat_preference import create_fish_habitat
    
    return SpeciesDefinition(
        species_id="fish",
        name="Pez",
        description="Vertebrado acuático con alta fertilidad.",
        archetype="fish",
        parent_template="vertebrate",
    ).add_trait("fertility", default_value=1.8, weight=1.0) \
     .add_trait("longevity", default_value=0.7, weight=0.9) \
     .add_trait("metabolism", default_value=0.8, weight=0.8) \
     .add_trait("swimming", default_value=1.8, weight=1.0) \
     .add_trait("smell", default_value=1.3, weight=0.9) \
     .add_trait("territoriality", default_value=0.5, weight=0.5) \
     .add_trait("cooperation", default_value=0.4, weight=0.4) \
     .add_trait("intelligence", default_value=0.3, weight=0.5) \
     .set_habitat_preference(create_fish_habitat())


def create_amphibian_species() -> SpeciesDefinition:
    """Anfibio: vertebrado de vida dual."""
    from systems.environment.habitat_preference import create_aquatic_plant_habitat
    
    return SpeciesDefinition(
        species_id="amphibian",
        name="Anfibio",
        description="Vertebrado de vida dual (agua/tierra), regenerador.",
        archetype="amphibian",
        parent_template="vertebrate",
    ).add_trait("fertility", default_value=1.5, weight=1.0) \
     .add_trait("immunity", default_value=0.6, weight=1.0) \
     .add_trait("longevity", default_value=0.8, weight=0.9) \
     .add_trait("metabolism", default_value=0.7, weight=0.8) \
     .add_trait("swimming", default_value=1.5, weight=1.0) \
     .add_trait("healing", default_value=1.3, weight=0.9) \
     .add_trait("venom", default_value=0.3, weight=0.4) \
     .add_trait("intelligence", default_value=0.3, weight=0.4) \
     .set_habitat_preference(create_aquatic_plant_habitat())


def create_insect_species() -> SpeciesDefinition:
    """Insecto: invertebrado con fertilidad extrema."""
    from systems.environment.habitat_preference import create_bacteria_habitat
    
    return SpeciesDefinition(
        species_id="insect",
        name="Insecto",
        description="Invertebrado con fertilidad extrema, vida breve.",
        archetype="insect",
        parent_template="invertebrate",
    ).add_trait("fertility", default_value=2.0, weight=1.0) \
     .add_trait("longevity", default_value=0.1, weight=1.0) \
     .add_trait("metabolism", default_value=1.8, weight=1.0) \
     .add_trait("growth_rate", default_value=2.0, weight=1.0) \
     .add_trait("flight", default_value=1.0, weight=0.7) \
     .add_trait("mobility", default_value=1.5, weight=0.9) \
     .add_trait("venom", default_value=0.2, weight=0.3) \
     .set_habitat_preference(create_bacteria_habitat())


def create_plant_template() -> SpeciesDefinition:
    """Plantilla base para plantas: fotosintéticas, sésiles."""
    return SpeciesDefinition(
        species_id="plant",
        name="Planta",
        description="Plantilla base para plantas: fotosintéticas, sésiles.",
        archetype="plant",
        parent_template="empty",
    ).add_trait("photosynthesis", default_value=1.8, weight=1.0) \
     .add_trait("growth_rate", default_value=0.6, weight=1.0) \
     .add_trait("longevity", default_value=2.0, weight=1.0) \
     .add_trait("immunity", default_value=0.8, weight=0.9) \
     .add_trait("healing", default_value=0.9, weight=0.8) \
     .add_trait("metabolism", default_value=0.5, weight=0.7) \
     .add_trait("fertility", default_value=1.0, weight=1.0)


def create_fungus_template() -> SpeciesDefinition:
    """Plantilla base para hongos: descomponedores."""
    from systems.environment.habitat_preference import create_fungus_habitat
    
    return SpeciesDefinition(
        species_id="fungus",
        name="Hongo",
        description="Plantilla base para hongos: descomponedores, simbióticos.",
        archetype="fungus",
        parent_template="empty",
    ).add_trait("heterotrophy", default_value=1.5, weight=1.0) \
     .add_trait("growth_rate", default_value=1.3, weight=1.0) \
     .add_trait("metabolism", default_value=1.0, weight=1.0) \
     .add_trait("immunity", default_value=1.2, weight=1.0) \
     .add_trait("longevity", default_value=1.5, weight=1.0) \
     .add_trait("healing", default_value=1.0, weight=0.8) \
     .add_trait("fertility", default_value=1.5, weight=1.0) \
     .add_trait("cooperation", default_value=1.2, weight=0.6) \
     .set_habitat_preference(create_fungus_habitat())


def create_bacteria_template() -> SpeciesDefinition:
    """Plantilla base para bacterias: unicelulares, asexuales."""
    from systems.environment.habitat_preference import create_bacteria_habitat
    
    return SpeciesDefinition(
        species_id="bacteria",
        name="Bacteria",
        description="Plantilla base para bacterias: unicelulares, asexuales.",
        archetype="bacteria",
        parent_template="empty",
    ).add_trait("division_speed", default_value=1.8, weight=1.0) \
     .add_trait("metabolism", default_value=1.3, weight=1.0) \
     .add_trait("antibiotic_resistance", default_value=0.2, weight=1.0) \
     .add_trait("mobility", default_value=0.6, weight=0.7) \
     .add_trait("immunity", default_value=0.3, weight=0.5) \
     .add_trait("growth_rate", default_value=2.0, weight=1.0) \
     .set_habitat_preference(create_bacteria_habitat())


def create_fantasy_template() -> SpeciesDefinition:
    """Plantilla para criaturas fantásticas: combinación especulativa."""
    return SpeciesDefinition(
        species_id="fantasy_creature",
        name="Criatura Fantástica",
        description="Plantilla para especies especulativas con combinaciones no naturales.",
        archetype="fantasy",
        parent_template="empty",
    ).add_trait("photosynthesis", default_value=1.0, weight=0.8) \
     .add_trait("venom", default_value=0.8, weight=0.8) \
     .add_trait("empathy", default_value=1.2, weight=0.7) \
     .add_trait("flight", default_value=1.5, weight=0.9) \
     .add_trait("regeneration", default_value=1.8, weight=1.0) \
     .add_trait("bioluminescence", default_value=1.0, weight=0.6) \
     .add_trait("nervous_system", default_value=1.0, weight=0.8) \
     .add_trait("heterotrophy", default_value=0.5, weight=0.5)


# =============================================================================
# REGISTRO DE ESPECIES
# =============================================================================

class SpeciesRegistry:
    """Registro global de especies y plantillas definidas."""
    
    _registry: Dict[str, SpeciesDefinition] = {}
    _logger = logging.getLogger("SpeciesRegistry")
    
    @classmethod
    def register(cls, species: SpeciesDefinition) -> None:
        """Registra una nueva especie o plantilla."""
        cls._registry[species.species_id] = species
        cls._logger.debug(
            "Especie registrada: %s [%s] (%d rasgos)",
            species.species_id, species.archetype, species.get_trait_count(),
        )
    
    @classmethod
    def get(cls, species_id: str) -> Optional[SpeciesDefinition]:
        """Obtiene una especie por su ID."""
        return cls._registry.get(species_id)
    
    @classmethod
    def has(cls, species_id: str) -> bool:
        """Verifica si una especie está registrada."""
        return species_id in cls._registry
    
    @classmethod
    def get_all(cls) -> Dict[str, SpeciesDefinition]:
        """Retorna todas las especies registradas."""
        return dict(cls._registry)
    
    @classmethod
    def get_by_archetype(cls, archetype: str) -> List[SpeciesDefinition]:
        """Retorna todas las especies de un arquetipo determinado."""
        return [s for s in cls._registry.values() if s.archetype == archetype]
    
    @classmethod
    def get_templates(cls) -> List[SpeciesDefinition]:
        """Retorna solo las plantillas base (no especies concretas)."""
        templates = ["empty", "animal", "vertebrate", "invertebrate",
                    "mammal", "plant", "fungus", "bacteria", "fantasy_creature"]
        return [cls._registry[t] for t in templates if t in cls._registry]
    
    @classmethod
    def list_archetypes(cls) -> List[str]:
        """Retorna los arquetipos únicos presentes en el registro."""
        return sorted(set(s.archetype for s in cls._registry.values()))
    
    @classmethod
    def initialize_defaults(cls) -> None:
        """Registra todas las plantillas y especies por defecto.
        
        ORDEN IMPORTANTE: Las plantillas deben registrarse antes que las
        especies que heredan de ellas, porque los hijos consultan a los padres.
        """
        if cls._registry:
            return
        
        # 1. Plantillas base (en orden de dependencia)
        cls.register(create_empty_template())
        cls.register(create_animal_template())
        cls.register(create_vertebrate_template())
        cls.register(create_invertebrate_template())
        cls.register(create_mammal_template())
        cls.register(create_plant_template())
        cls.register(create_fungus_template())
        cls.register(create_bacteria_template())
        cls.register(create_fantasy_template())
        
        # 2. Especies concretas (heredan de las plantillas)
        cls.register(create_human_species())
        cls.register(create_bird_species())
        cls.register(create_fish_species())
        cls.register(create_insect_species())
        cls.register(create_reptile_species())
        cls.register(create_amphibian_species())