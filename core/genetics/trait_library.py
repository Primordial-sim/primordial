"""Biblioteca Universal de Rasgos.

Catálogo global de todos los rasgos hereditarios disponibles.
Se puede ampliar indefinidamente sin modificar el Genome.

FILOSOFÍA: Los rasgos son completamente NEUTROS.
- No conocen incompatibilidades (eso va en el Validador)
- No conocen requisitos (eso va en el Validador)
- No conocen biología (eso va en las Plantillas)

Cada rasgo define:
- Identidad: id, nombre, categoría
- Rango: min, max, default
- Expresión: modelo de expresión genética
- Evolución: peso evolutivo, heredabilidad
- Distribución: cómo se genera la población fundadora
"""

from __future__ import annotations

from typing import Dict, List, Optional
import logging

from core.genetics.trait import Trait, TraitCategory, ExpressionModel, Distribution


class TraitLibrary:
    """Biblioteca global de rasgos hereditarios.
    
    Esta clase es un registro estático de todos los rasgos disponibles.
    Se puede extender en tiempo de ejecución mediante register_trait().
    
    Uso:
        library = TraitLibrary.get_default()
        fertility_trait = library.get_trait("fertility")
    """
    
    _default_library: Optional['TraitLibrary'] = None
    _logger = logging.getLogger("TraitLibrary")
    
    def __init__(self) -> None:
        self._traits: Dict[str, Trait] = {}
    
    @classmethod
    def get_default(cls) -> 'TraitLibrary':
        """Retorna la biblioteca por defecto con todos los rasgos predefinidos."""
        if cls._default_library is None:
            cls._default_library = cls._create_default_library()
        return cls._default_library
    
    @classmethod
    def _create_default_library(cls) -> 'TraitLibrary':
        """Crea la biblioteca con todos los rasgos predefinidos."""
        library = cls()
        
        # =================================================================
        # RASGOS BIOLÓGICOS FUNDAMENTALES
        # =================================================================
        
        library.register_trait(Trait(
            trait_id="fertility",
            name="Fertilidad",
            category=TraitCategory.BIOLOGY,
            min_value=0.0,
            max_value=2.0,
            default_value=1.0,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=1.0,
            heritability=0.9,
            initial_distribution=Distribution.NORMAL,
            initial_mean=1.0,
            initial_std=0.15,
            description="Capacidad reproductiva del individuo.",
        ))
        
        library.register_trait(Trait(
            trait_id="immunity",
            name="Inmunidad",
            category=TraitCategory.BIOLOGY,
            min_value=0.0,
            max_value=2.0,
            default_value=1.0,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=1.0,
            heritability=0.8,
            initial_distribution=Distribution.NORMAL,
            initial_mean=1.0,
            initial_std=0.2,
            description="Resistencia general a enfermedades.",
        ))
        
        library.register_trait(Trait(
            trait_id="longevity",
            name="Longevidad",
            category=TraitCategory.BIOLOGY,
            min_value=0.0,
            max_value=2.0,
            default_value=1.0,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=0.9,
            heritability=0.7,
            initial_distribution=Distribution.NORMAL,
            initial_mean=1.0,
            initial_std=0.15,
            description="Esperanza de vida genética.",
        ))
        
        library.register_trait(Trait(
            trait_id="metabolism",
            name="Metabolismo",
            category=TraitCategory.BIOLOGY,
            min_value=0.0,
            max_value=2.0,
            default_value=1.0,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=0.8,
            heritability=0.85,
            initial_distribution=Distribution.NORMAL,
            initial_mean=1.0,
            initial_std=0.2,
            description="Eficiencia metabólica.",
        ))
        
        library.register_trait(Trait(
            trait_id="growth_rate",
            name="Crecimiento",
            category=TraitCategory.BIOLOGY,
            min_value=0.0,
            max_value=2.0,
            default_value=1.0,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=0.7,
            heritability=0.9,
            initial_distribution=Distribution.NORMAL,
            initial_mean=1.0,
            initial_std=0.15,
            description="Velocidad de desarrollo físico.",
        ))
        
        library.register_trait(Trait(
            trait_id="healing",
            name="Regeneración",
            category=TraitCategory.BIOLOGY,
            min_value=0.0,
            max_value=2.0,
            default_value=0.5,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=0.7,
            heritability=0.8,
            initial_distribution=Distribution.NORMAL,
            initial_mean=0.5,
            initial_std=0.2,
            description="Capacidad de recuperación de heridas.",
        ))
        
        library.register_trait(Trait(
            trait_id="nervous_system",
            name="Sistema Nervioso",
            category=TraitCategory.BIOLOGY,
            min_value=0.0,
            max_value=2.0,
            default_value=1.0,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=0.9,
            heritability=0.9,
            initial_distribution=Distribution.NORMAL,
            initial_mean=1.0,
            initial_std=0.2,
            description="Complejidad del sistema nervioso.",
        ))
        
        library.register_trait(Trait(
            trait_id="heterotrophy",
            name="Heterotrofía",
            category=TraitCategory.BIOLOGY,
            min_value=0.0,
            max_value=2.0,
            default_value=1.0,
            expression_model=ExpressionModel.DOMINANT,
            evolutionary_weight=1.0,
            heritability=1.0,
            initial_distribution=Distribution.FIXED,
            description="Capacidad de obtener energía consumiendo otros organismos.",
        ))
        
        # =================================================================
        # RASGOS DE COMPORTAMIENTO
        # =================================================================
        
        library.register_trait(Trait(
            trait_id="sociability",
            name="Sociabilidad",
            category=TraitCategory.BEHAVIOR,
            min_value=0.0,
            max_value=2.0,
            default_value=1.0,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=0.8,
            heritability=0.6,
            initial_distribution=Distribution.NORMAL,
            initial_mean=1.0,
            initial_std=0.25,
            description="Tendencia a buscar interacción social.",
        ))
        
        library.register_trait(Trait(
            trait_id="aggressiveness",
            name="Agresividad",
            category=TraitCategory.BEHAVIOR,
            min_value=0.0,
            max_value=2.0,
            default_value=0.5,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=0.7,
            heritability=0.65,
            initial_distribution=Distribution.NORMAL,
            initial_mean=0.5,
            initial_std=0.25,
            description="Tendencia al conflicto y la confrontación.",
        ))
        
        library.register_trait(Trait(
            trait_id="territoriality",
            name="Territorialidad",
            category=TraitCategory.BEHAVIOR,
            min_value=0.0,
            max_value=2.0,
            default_value=0.5,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=0.6,
            heritability=0.7,
            initial_distribution=Distribution.NORMAL,
            initial_mean=0.5,
            initial_std=0.25,
            description="Tendencia a defender un territorio.",
        ))
        
        library.register_trait(Trait(
            trait_id="empathy",
            name="Empatía",
            category=TraitCategory.BEHAVIOR,
            min_value=0.0,
            max_value=2.0,
            default_value=0.5,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=0.6,
            heritability=0.5,
            initial_distribution=Distribution.NORMAL,
            initial_mean=0.5,
            initial_std=0.25,
            description="Capacidad de comprender las emociones de otros.",
        ))
        
        library.register_trait(Trait(
            trait_id="cooperation",
            name="Cooperación",
            category=TraitCategory.BEHAVIOR,
            min_value=0.0,
            max_value=2.0,
            default_value=0.5,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=0.7,
            heritability=0.6,
            initial_distribution=Distribution.NORMAL,
            initial_mean=0.5,
            initial_std=0.25,
            description="Tendencia a cooperar con otros individuos.",
        ))
        
        library.register_trait(Trait(
            trait_id="curiosity",
            name="Curiosidad",
            category=TraitCategory.BEHAVIOR,
            min_value=0.0,
            max_value=2.0,
            default_value=0.5,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=0.6,
            heritability=0.55,
            initial_distribution=Distribution.NORMAL,
            initial_mean=0.5,
            initial_std=0.25,
            description="Deseo de explorar lo desconocido.",
        ))
        
        library.register_trait(Trait(
            trait_id="impulsivity",
            name="Impulsividad",
            category=TraitCategory.BEHAVIOR,
            min_value=0.0,
            max_value=2.0,
            default_value=0.5,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=0.5,
            heritability=0.6,
            initial_distribution=Distribution.NORMAL,
            initial_mean=0.5,
            initial_std=0.25,
            description="Tendencia a actuar sin pensar.",
        ))
        
        library.register_trait(Trait(
            trait_id="obedience",
            name="Obediencia",
            category=TraitCategory.BEHAVIOR,
            min_value=0.0,
            max_value=2.0,
            default_value=0.5,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=0.5,
            heritability=0.5,
            initial_distribution=Distribution.NORMAL,
            initial_mean=0.5,
            initial_std=0.25,
            description="Tendencia a seguir normas sociales.",
        ))
        
        library.register_trait(Trait(
            trait_id="temperament",
            name="Temperamento",
            category=TraitCategory.BEHAVIOR,
            min_value=0.0,
            max_value=2.0,
            default_value=1.0,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=0.7,
            heritability=0.7,
            initial_distribution=Distribution.NORMAL,
            initial_mean=1.0,
            initial_std=0.2,
            description="Estabilidad emocional.",
        ))
        
        library.register_trait(Trait(
            trait_id="intelligence",
            name="Inteligencia",
            category=TraitCategory.BEHAVIOR,
            min_value=0.0,
            max_value=2.0,
            default_value=1.0,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=0.9,
            heritability=0.7,
            initial_distribution=Distribution.NORMAL,
            initial_mean=1.0,
            initial_std=0.25,
            description="Capacidad cognitiva.",
        ))
        
        # =================================================================
        # RASGOS DE PERCEPCIÓN SENSORIAL
        # =================================================================
        
        library.register_trait(Trait(
            trait_id="vision",
            name="Vista",
            category=TraitCategory.PERCEPTION,
            min_value=0.0,
            max_value=2.0,
            default_value=1.0,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=0.7,
            heritability=0.8,
            initial_distribution=Distribution.NORMAL,
            initial_mean=1.0,
            initial_std=0.2,
            description="Agudeza visual.",
        ))
        
        library.register_trait(Trait(
            trait_id="smell",
            name="Olfato",
            category=TraitCategory.PERCEPTION,
            min_value=0.0,
            max_value=2.0,
            default_value=0.5,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=0.6,
            heritability=0.8,
            initial_distribution=Distribution.NORMAL,
            initial_mean=0.5,
            initial_std=0.25,
            description="Agudeza olfativa.",
        ))
        
        library.register_trait(Trait(
            trait_id="hearing",
            name="Audición",
            category=TraitCategory.PERCEPTION,
            min_value=0.0,
            max_value=2.0,
            default_value=0.5,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=0.6,
            heritability=0.8,
            initial_distribution=Distribution.NORMAL,
            initial_mean=0.5,
            initial_std=0.25,
            description="Agudeza auditiva.",
        ))
        
        library.register_trait(Trait(
            trait_id="night_vision",
            name="Visión Nocturna",
            category=TraitCategory.PERCEPTION,
            min_value=0.0,
            max_value=2.0,
            default_value=0.0,
            expression_model=ExpressionModel.DOMINANT,
            evolutionary_weight=0.5,
            heritability=0.9,
            initial_distribution=Distribution.FIXED,
            description="Capacidad de ver en la oscuridad.",
        ))
        
        library.register_trait(Trait(
            trait_id="echolocation",
            name="Ecolocalización",
            category=TraitCategory.PERCEPTION,
            min_value=0.0,
            max_value=2.0,
            default_value=0.0,
            expression_model=ExpressionModel.DOMINANT,
            evolutionary_weight=0.5,
            heritability=0.9,
            initial_distribution=Distribution.FIXED,
            description="Capacidad de navegar mediante sonido.",
        ))
        
        # =================================================================
        # RASGOS DE MOVIMIENTO
        # =================================================================
        
        library.register_trait(Trait(
            trait_id="speed",
            name="Velocidad",
            category=TraitCategory.MOVEMENT,
            min_value=0.0,
            max_value=2.0,
            default_value=1.0,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=0.8,
            heritability=0.85,
            initial_distribution=Distribution.NORMAL,
            initial_mean=1.0,
            initial_std=0.2,
            description="Velocidad de movimiento.",
        ))
        
        library.register_trait(Trait(
            trait_id="flight",
            name="Vuelo",
            category=TraitCategory.MOVEMENT,
            min_value=0.0,
            max_value=2.0,
            default_value=0.0,
            expression_model=ExpressionModel.DOMINANT,
            evolutionary_weight=0.9,
            heritability=1.0,
            initial_distribution=Distribution.FIXED,
            description="Capacidad de volar.",
        ))
        
        library.register_trait(Trait(
            trait_id="swimming",
            name="Natación",
            category=TraitCategory.MOVEMENT,
            min_value=0.0,
            max_value=2.0,
            default_value=0.0,
            expression_model=ExpressionModel.DOMINANT,
            evolutionary_weight=0.8,
            heritability=1.0,
            initial_distribution=Distribution.FIXED,
            description="Capacidad de nadar.",
        ))
        
        library.register_trait(Trait(
            trait_id="climbing",
            name="Escalada",
            category=TraitCategory.MOVEMENT,
            min_value=0.0,
            max_value=2.0,
            default_value=0.0,
            expression_model=ExpressionModel.DOMINANT,
            evolutionary_weight=0.6,
            heritability=0.9,
            initial_distribution=Distribution.FIXED,
            description="Capacidad de escalar superficies.",
        ))
        
        library.register_trait(Trait(
            trait_id="burrowing",
            name="Excavación",
            category=TraitCategory.MOVEMENT,
            min_value=0.0,
            max_value=2.0,
            default_value=0.0,
            expression_model=ExpressionModel.DOMINANT,
            evolutionary_weight=0.5,
            heritability=0.9,
            initial_distribution=Distribution.FIXED,
            description="Capacidad de excavar y moverse bajo tierra.",
        ))
        
        # =================================================================
        # RASGOS ESPECIALES
        # =================================================================
        
        library.register_trait(Trait(
            trait_id="venom",
            name="Veneno",
            category=TraitCategory.SPECIAL,
            min_value=0.0,
            max_value=2.0,
            default_value=0.0,
            expression_model=ExpressionModel.DOMINANT,
            evolutionary_weight=0.7,
            heritability=1.0,
            initial_distribution=Distribution.FIXED,
            description="Capacidad de producir veneno.",
        ))
        
        library.register_trait(Trait(
            trait_id="photosynthesis",
            name="Fotosíntesis",
            category=TraitCategory.SPECIAL,
            min_value=0.0,
            max_value=2.0,
            default_value=0.0,
            expression_model=ExpressionModel.DOMINANT,
            evolutionary_weight=1.0,
            heritability=1.0,
            initial_distribution=Distribution.FIXED,
            description="Capacidad de obtener energía de la luz solar.",
        ))
        
        library.register_trait(Trait(
            trait_id="camouflage",
            name="Camuflaje",
            category=TraitCategory.SPECIAL,
            min_value=0.0,
            max_value=2.0,
            default_value=0.0,
            expression_model=ExpressionModel.DOMINANT,
            evolutionary_weight=0.6,
            heritability=0.9,
            initial_distribution=Distribution.FIXED,
            description="Capacidad de mimetizarse con el entorno.",
        ))
        
        library.register_trait(Trait(
            trait_id="regeneration",
            name="Regeneración Avanzada",
            category=TraitCategory.SPECIAL,
            min_value=0.0,
            max_value=2.0,
            default_value=0.0,
            expression_model=ExpressionModel.DOMINANT,
            evolutionary_weight=0.7,
            heritability=0.9,
            initial_distribution=Distribution.FIXED,
            description="Capacidad de regenerar miembros o tejidos.",
        ))
        
        library.register_trait(Trait(
            trait_id="bioluminescence",
            name="Bioluminiscencia",
            category=TraitCategory.SPECIAL,
            min_value=0.0,
            max_value=2.0,
            default_value=0.0,
            expression_model=ExpressionModel.DOMINANT,
            evolutionary_weight=0.4,
            heritability=1.0,
            initial_distribution=Distribution.FIXED,
            description="Capacidad de emitir luz propia.",
        ))
        
        library.register_trait(Trait(
            trait_id="division_speed",
            name="Velocidad de División",
            category=TraitCategory.SPECIAL,
            min_value=0.0,
            max_value=2.0,
            default_value=1.0,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=1.0,
            heritability=1.0,
            initial_distribution=Distribution.NORMAL,
            initial_mean=1.0,
            initial_std=0.2,
            description="Velocidad de reproducción asexual.",
        ))
        
        library.register_trait(Trait(
            trait_id="antibiotic_resistance",
            name="Resistencia a Antibióticos",
            category=TraitCategory.SPECIAL,
            min_value=0.0,
            max_value=2.0,
            default_value=0.0,
            expression_model=ExpressionModel.DOMINANT,
            evolutionary_weight=0.9,
            heritability=1.0,
            initial_distribution=Distribution.NORMAL,
            initial_mean=0.1,
            initial_std=0.1,
            description="Resistencia a tratamientos antimicrobianos.",
        ))
        
        library.register_trait(Trait(
            trait_id="mobility",
            name="Movilidad",
            category=TraitCategory.SPECIAL,
            min_value=0.0,
            max_value=2.0,
            default_value=1.0,
            expression_model=ExpressionModel.WEIGHTED_AVERAGE,
            evolutionary_weight=0.7,
            heritability=0.9,
            initial_distribution=Distribution.NORMAL,
            initial_mean=1.0,
            initial_std=0.2,
            description="Capacidad de movimiento autónomo.",
        ))
        
        return library
    
    def register_trait(self, trait: Trait) -> None:
        """Registra un nuevo rasgo en la biblioteca.
        
        Args:
            trait: El rasgo a registrar.
            
        Raises:
            ValueError: Si el trait_id ya existe.
        """
        if trait.trait_id in self._traits:
            raise ValueError(f"El rasgo '{trait.trait_id}' ya está registrado.")
        self._traits[trait.trait_id] = trait
        self._logger.debug("Rasgo registrado: %s", trait.trait_id)
    
    def get_trait(self, trait_id: str) -> Optional[Trait]:
        """Obtiene un rasgo por su ID."""
        return self._traits.get(trait_id)
    
    def has_trait(self, trait_id: str) -> bool:
        """Verifica si un rasgo existe en la biblioteca."""
        return trait_id in self._traits
    
    def get_all_traits(self) -> List[Trait]:
        """Retorna todos los rasgos registrados."""
        return list(self._traits.values())
    
    def get_traits_by_category(self, category: TraitCategory) -> List[Trait]:
        """Retorna todos los rasgos de una categoría."""
        return [t for t in self._traits.values() if t.category == category]
    
    def get_trait_ids(self) -> List[str]:
        """Retorna todos los IDs de rasgos registrados."""
        return list(self._traits.keys())
    
    def __len__(self) -> int:
        return len(self._traits)
    
    def __contains__(self, trait_id: str) -> bool:
        return trait_id in self._traits