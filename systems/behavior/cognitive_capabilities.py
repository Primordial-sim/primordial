"""Capacidades cognitivas derivadas del genoma.

Este módulo consulta el genoma de un organismo y determina qué tipo de
capacidades cognitivas tiene: si tiene sistema nervioso, emociones,
memoria episódica, conceptos sociales complejos, etc.

Es la capa de abstracción entre el núcleo genético (agnóstico a especie)
y los sistemas cognitivos (CognitiveMemorySystem, FreeWillSystem).

Diseño:
- INMUTABLE: Se crea una vez consultando el genoma, no se modifica
- AGNÓSTICO: No conoce especies, solo consulta rasgos
- EXTENSIBLE: Se pueden añadir nuevas capacidades sin romper existentes

Niveles de cognición biológica (aproximación):
- Nivel 0: Sin sistema nervioso (plantas, bacterias, hongos)
- Nivel 1: Sistema nervioso simple, reflejos (insectos, gusanos)
- Nivel 2: Emociones básicas, memoria simple (peces, anfibios)
- Nivel 3: Memoria episódica, vínculos sociales (lobos, aves, primates)
- Nivel 4: Conceptos sociales complejos (humanos, delfines)
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entities.person.genome import Genome


@dataclass
class CognitiveCapabilities:
    """Capacidades cognitivas derivadas del genoma de un organismo.
    
    Esta clase es inmutable y se crea consultando el genoma.
    Determina QUÉ capacidades cognitivas tiene un organismo, no CÓMO
    las usa (eso lo deciden los sistemas cognitivos).
    
    Atributos:
        has_nervous_system: ¿Tiene sistema nervioso? (nervous_system >= 0.1)
        has_emotions: ¿Tiene emociones básicas? (nervous_system >= 0.3)
        has_complex_brain: ¿Tiene cerebro complejo? (vertebrados)
        has_episodic_memory: ¿Tiene memoria episódica?
        has_complex_motivations: ¿Tiene motivaciones complejas?
        has_basic_motivations: ¿Tiene instintos básicos?
        has_pair_bonding: ¿Forma parejas?
        has_family_structure: ¿Tiene estructura familiar?
        has_social_concepts: ¿Tiene conceptos sociales (matrimonio, etc.)?
        cognitive_level: Nivel general de cognición (0.0 a 1.0)
        emotional_complexity: Complejidad emocional (0.0 a 1.0)
        social_complexity: Complejidad social (0.0 a 1.0)
    """
    
    # === CAPACIDADES BÁSICAS ===
    has_nervous_system: bool = False      # ¿Tiene sistema nervioso?
    has_emotions: bool = False            # ¿Tiene emociones básicas?
    has_complex_brain: bool = False       # ¿Tiene cerebro complejo?
    has_episodic_memory: bool = False     # ¿Tiene memoria episódica?
    
    # === CAPACIDADES MOTIVACIONALES ===
    has_basic_motivations: bool = False       # ¿Tiene instintos básicos?
    has_complex_motivations: bool = False     # ¿Tiene motivaciones complejas?
    
    # === CAPACIDADES SOCIALES ===
    has_pair_bonding: bool = False        # ¿Forma parejas estables?
    has_family_structure: bool = False    # ¿Tiene estructura familiar?
    has_social_concepts: bool = False     # ¿Tiene conceptos sociales complejos?
    
    # === NIVELES CONTINUOS ===
    cognitive_level: float = 0.0          # Nivel general (0.0 a 1.0)
    emotional_complexity: float = 0.0     # Complejidad emocional (0.0 a 1.0)
    social_complexity: float = 0.0        # Complejidad social (0.0 a 1.0)
    
    @classmethod
    def from_genome(cls, genome: 'Genome') -> 'CognitiveCapabilities':
        """Crea CognitiveCapabilities consultando el genoma.
        
        Este método es la única forma de crear CognitiveCapabilities.
        Consulta el genoma y deriva las capacidades de forma determinista.
        
        Args:
            genome: El genoma del organismo.
            
        Returns:
            CognitiveCapabilities con las capacidades derivadas.
            
        Note:
            Si un rasgo no existe en el genoma, usa valores por defecto
            apropiados para organismos que no tienen ese rasgo.
            
        Examples:
            >>> caps = CognitiveCapabilities.from_genome(human_genome)
            >>> caps.has_complex_motivations
            True
            >>> caps.has_social_concepts
            True
            
            >>> caps = CognitiveCapabilities.from_genome(plant_genome)
            >>> caps.has_nervous_system
            False
        """
        # Helper para obtener valor de rasgo de forma segura
        def get_trait(trait_id: str, default: float = 0.0) -> float:
            """Obtiene el valor de un rasgo, retornando default si no existe."""
            if genome.has_trait(trait_id):
                return genome.get_trait_value(trait_id)
            return default
        
        # === OBTENER VALORES DE RASGOS ===
        nervous_system = get_trait("nervous_system", 0.0)
        intelligence = get_trait("intelligence", 0.0)
        sociability = get_trait("sociability", 0.0)
        temperament = get_trait("temperament", 0.0)
        
        # === CAPACIDADES BÁSICAS ===
        # ¿Tiene sistema nervioso? (muy bajo umbral, incluso invertebrados simples)
        has_nervous_system = nervous_system >= 0.1
        
        # ¿Tiene emociones básicas? (requiere sistema nervioso moderado)
        has_emotions = nervous_system >= 0.3
        
        # ¿Tiene cerebro complejo? (vertebrados, requiere sistema nervioso + algo de inteligencia)
        has_complex_brain = nervous_system >= 0.5 and intelligence >= 0.3
        
        # ¿Tiene memoria episódica? (recuerdos específicos, requiere inteligencia media)
        has_episodic_memory = intelligence >= 0.5 and has_complex_brain
        
        # === CAPACIDADES MOTIVACIONALES ===
        # Instintos básicos (supervivencia): cualquier organismo con sistema nervioso mínimo
        has_basic_motivations = nervous_system >= 0.2
        
        # Motivaciones complejas (rebeldía, independencia, partnership): solo cerebros avanzados
        has_complex_motivations = intelligence >= 0.7 and has_complex_brain
        
        # === CAPACIDADES SOCIALES ===
        # Vínculos de pareja (lobos, cisnes, primates): sociabilidad + inteligencia
        has_pair_bonding = sociability >= 0.7 and intelligence >= 0.5
        
        # Estructura familiar compleja (cría prolongada, roles): sociabilidad alta + inteligencia
        has_family_structure = sociability >= 0.8 and intelligence >= 0.6
        
        # Conceptos sociales (matrimonio, divorcio, adopción): solo humanos y muy pocos más
        has_social_concepts = intelligence >= 0.8 and has_episodic_memory
        
        # === NIVELES CONTINUOS ===
        # Nivel cognitivo general: combinación de inteligencia y sistema nervioso
        cognitive_level = max(0.0, min(1.0, (intelligence * 0.7 + nervous_system * 0.3)))
        
        # Complejidad emocional: basada en sistema nervioso y temperamento
        emotional_complexity = max(0.0, min(1.0, (nervous_system * 0.7 + temperament * 0.3)))
        
        # Complejidad social: combinación de sociabilidad e inteligencia
        social_complexity = max(0.0, min(1.0, (sociability * 0.6 + intelligence * 0.4)))
        
        return cls(
            has_nervous_system=has_nervous_system,
            has_emotions=has_emotions,
            has_complex_brain=has_complex_brain,
            has_episodic_memory=has_episodic_memory,
            has_basic_motivations=has_basic_motivations,
            has_complex_motivations=has_complex_motivations,
            has_pair_bonding=has_pair_bonding,
            has_family_structure=has_family_structure,
            has_social_concepts=has_social_concepts,
            cognitive_level=cognitive_level,
            emotional_complexity=emotional_complexity,
            social_complexity=social_complexity,
        )
    
    def can_form_trauma(self, trauma_type: str) -> bool:
        """Verifica si el organismo puede formar un tipo específico de trauma.
        
        Args:
            trauma_type: Tipo de trauma
                - "overcrowding": hacinamiento (requiere emociones)
                - "sickness": enfermedad (requiere emociones)
                - "abandonment": abandono (requiere vínculos de pareja/familia)
                - "adoption": adopción (requiere estructura familiar)
            
        Returns:
            True si el organismo puede formar ese tipo de trauma.
        """
        if trauma_type in ("overcrowding", "sickness"):
            return self.has_emotions
        elif trauma_type == "abandonment":
            return self.has_pair_bonding or self.has_family_structure
        elif trauma_type == "adoption":
            return self.has_family_structure
        else:
            return self.has_emotions
    
    def can_have_memory_type(self, memory_type: str) -> bool:
        """Verifica si el organismo puede formar un tipo específico de memoria episódica.
        
        Args:
            memory_type: Tipo de memoria
                - Tipos básicos: "companion", "conflict", "experience", "event", "disease"
                - Tipos sociales: "marriage", "child", "death", "adoption", "divorce"
                - Tipo especial: "migration"
            
        Returns:
            True si el organismo puede formar ese tipo de memoria.
        """
        # Tipos sociales complejos requieren conceptos sociales
        social_types = {"marriage", "child", "death", "adoption", "divorce"}
        if memory_type in social_types:
            return self.has_social_concepts
        
        # Todos los demás requieren memoria episódica
        return self.has_episodic_memory
    
    def can_have_motivation(self, motivation_name: str) -> bool:
        """Verifica si el organismo puede tener una motivación específica.
        
        Args:
            motivation_name: Nombre de la motivación
                - Básicas: "protection", "cooperation"
                - Complejas: "independence", "exploration", "rebellion",
                             "partnership", "migration"
            
        Returns:
            True si el organismo puede tener esa motivación.
        """
        # Motivaciones complejas requieren cerebro complejo
        complex_motivations = {
            "independence", "rebellion", "partnership", "migration"
        }
        
        if motivation_name in complex_motivations:
            return self.has_complex_motivations
        
        # Exploración requiere emociones (curiosidad)
        if motivation_name == "exploration":
            return self.has_emotions
        
        # Cooperation requiere al menos emociones sociales
        if motivation_name == "cooperation":
            return self.has_emotions and self.social_complexity >= 0.3
        
        # Protection es instintiva (incluso en peces que protegen crías)
        if motivation_name == "protection":
            return self.has_basic_motivations
        
        # Por defecto, requiere motivaciones básicas
        return self.has_basic_motivations
    
    def __str__(self) -> str:
        """Representación legible para debugging."""
        return (
            f"CognitiveCapabilities("
            f"level={self.cognitive_level:.2f}, "
            f"nervous={self.has_nervous_system}, "
            f"emotions={self.has_emotions}, "
            f"episodic={self.has_episodic_memory}, "
            f"complex_motiv={self.has_complex_motivations}, "
            f"social_concepts={self.has_social_concepts}"
            f")"
        )
    
    def __repr__(self) -> str:
        """Representación completa para debugging."""
        return (
            f"CognitiveCapabilities("
            f"has_nervous_system={self.has_nervous_system}, "
            f"has_emotions={self.has_emotions}, "
            f"has_complex_brain={self.has_complex_brain}, "
            f"has_episodic_memory={self.has_episodic_memory}, "
            f"has_basic_motivations={self.has_basic_motivations}, "
            f"has_complex_motivations={self.has_complex_motivations}, "
            f"has_pair_bonding={self.has_pair_bonding}, "
            f"has_family_structure={self.has_family_structure}, "
            f"has_social_concepts={self.has_social_concepts}, "
            f"cognitive_level={self.cognitive_level}, "
            f"emotional_complexity={self.emotional_complexity}, "
            f"social_complexity={self.social_complexity}"
            f")"
        )