"""Capacidades de movimiento derivadas del genoma.

Este módulo consulta el genoma de un organismo y determina qué puede hacer
en términos de movimiento: si puede moverse, cómo se mueve, qué tan lejos ve,
si es social o territorial, etc.

Es la capa de abstracción entre el núcleo genético (agnóstico a especie)
y los sistemas de movimiento (que necesitan saber capacidades concretas).

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
class MovementCapabilities:
    """Capacidades de movimiento derivadas del genoma de un organismo.
    
    Esta clase es inmutable y se crea consultando el genoma.
    Representa QUÉ puede hacer un organismo en términos de movimiento,
    no CÓMO lo hace (eso lo deciden los sistemas de movimiento).
    
    Atributos:
        can_move: ¿Puede moverse? (mobility > 0.1)
        can_migrate: ¿Puede migrar largas distancias?
        can_walk: ¿Puede caminar? (movilidad terrestre)
        can_fly: ¿Puede volar? (flight > 0.5)
        can_swim: ¿Puede nadar? (swimming > 0.5)
        can_burrow: ¿Puede excavar? (burrowing > 0.5)
        movement_speed: Multiplicador de velocidad (0.5 a 2.0)
        vision_range: Radio de visión (0.5 a 5.0)
        smell_range: Radio de olfato (0.0 a 3.0)
        is_social: ¿Atraído a densidad? (sociability > 0.7)
        is_territorial: ¿Repelido por densidad? (territoriality > 0.7)
        exploration_tendency: Tendencia a explorar (0.0 a 1.0)
        needs_ground_resources: ¿Necesita recursos del suelo?
    """
    
    # === CAPACIDADES BÁSICAS ===
    can_move: bool = False          # ¿Puede moverse? (mobility > 0.1)
    can_migrate: bool = False       # ¿Puede migrar largas distancias?
    
    # === MODALIDADES DE MOVIMIENTO ===
    can_walk: bool = False          # ¿Puede caminar? (movilidad terrestre)
    can_fly: bool = False           # ¿Puede volar? (flight > 0.5)
    can_swim: bool = False          # ¿Puede nadar? (swimming > 0.5)
    can_burrow: bool = False        # ¿Puede excavar? (burrowing > 0.5)
    
    # === PARÁMETROS DE MOVIMIENTO ===
    movement_speed: float = 1.0     # Multiplicador de velocidad (0.5 a 2.0)
    vision_range: float = 1.0       # Radio de visión (0.5 a 5.0)
    smell_range: float = 0.5        # Radio de olfato (0.0 a 3.0)
    
    # === COMPORTAMIENTO SOCIAL ===
    is_social: bool = False         # ¿Atraído a densidad? (sociability > 0.7)
    is_territorial: bool = False    # ¿Repelido por densidad? (territoriality > 0.7)
    exploration_tendency: float = 0.5  # Tendencia a explorar (0.0 a 1.0)
    
    # === NECESIDADES ===
    needs_ground_resources: bool = True  # ¿Necesita recursos del suelo?
    
    @classmethod
    def from_genome(cls, genome: 'Genome') -> 'MovementCapabilities':
        """Crea MovementCapabilities consultando el genoma.
        
        Este método es la única forma de crear MovementCapabilities.
        Consulta el genoma y deriva las capacidades de forma determinista.
        
        Args:
            genome: El genoma del organismo.
            
        Returns:
            MovementCapabilities con las capacidades derivadas.
            
        Note:
            Si un rasgo no existe en el genoma, usa valores por defecto
            apropiados para organismos que no tienen ese rasgo.
            
        Examples:
            >>> caps = MovementCapabilities.from_genome(human_genome)
            >>> caps.can_move
            True
            >>> caps.can_fly
            False
            
            >>> caps = MovementCapabilities.from_genome(plant_genome)
            >>> caps.can_move
            False
        """
        # Helper para obtener valor de rasgo de forma segura
        def get_trait(trait_id: str, default: float = 0.0) -> float:
            """Obtiene el valor de un rasgo, retornando default si no existe."""
            if genome.has_trait(trait_id):
                return genome.get_trait_value(trait_id)
            return default
        
        # === OBTENER VALORES DE RASGOS ===
        mobility = get_trait("mobility", 0.5)
        speed = get_trait("speed", 1.0)
        flight = get_trait("flight", 0.0)
        swimming = get_trait("swimming", 0.0)
        burrowing = get_trait("burrowing", 0.0)
        curiosity = get_trait("curiosity", 0.5)
        vision = get_trait("vision", 1.0)
        smell = get_trait("smell", 0.5)
        sociability = get_trait("sociability", 0.5)
        territoriality = get_trait("territoriality", 0.3)
        photosynthesis = get_trait("photosynthesis", 0.0)
        
        # === CAPACIDADES BÁSICAS ===
        can_move = mobility > 0.1
        
        # === MODALIDADES DE MOVIMIENTO ===
        # Lógica matizada para capacidades de movimiento:
        # - Peces: NO pueden caminar (son nadadores exclusivos)
        # - Aves: SÍ pueden caminar (pueden volar Y caminar)
        # - Humanos: SÍ pueden caminar
        
        # ¿Es principalmente nadador? (swimming muy alto, mobility bajo)
        is_primarily_swimmer = swimming > 0.7 and mobility < 0.5
        
        # Puede caminar si:
        # - Tiene movilidad suficiente (> 0.3)
        # - NO es principalmente nadador (peces)
        can_walk = mobility > 0.3 and not is_primarily_swimmer
        
        can_fly = flight > 0.5
        can_swim = swimming > 0.5
        can_burrow = burrowing > 0.5
        
        # ¿Puede migrar? (necesita poder moverse + capacidad de movimiento fuerte)
        # Requiere:
        # - mobility > 0.5 (no solo > 0.1, porque migrar es esfuerzo grande)
        # - Al menos un modo de movimiento fuerte (> 0.5)
        # - Curiosidad suficiente para explorar
        can_migrate = (
            can_move and 
            mobility > 0.5 and
            (speed > 0.5 or flight > 0.5 or swimming > 0.5) and
            curiosity > 0.3
        )
        
        # === PARÁMETROS DE MOVIMIENTO ===
        # Clampear a rangos válidos
        movement_speed = max(0.5, min(2.0, speed))
        vision_range = max(0.5, min(5.0, vision))
        smell_range = max(0.0, min(3.0, smell))
        
        # === COMPORTAMIENTO SOCIAL ===
        is_social = sociability > 0.7
        is_territorial = territoriality > 0.7 and not is_social  # Territorial si no es social
        exploration_tendency = max(0.0, min(1.0, curiosity))
        
        # === NECESIDADES ===
        # Los organismos fotosintéticos no necesitan recursos del suelo
        needs_ground_resources = photosynthesis < 0.5
        
        return cls(
            can_move=can_move,
            can_migrate=can_migrate,
            can_walk=can_walk,
            can_fly=can_fly,
            can_swim=can_swim,
            can_burrow=can_burrow,
            movement_speed=movement_speed,
            vision_range=vision_range,
            smell_range=smell_range,
            is_social=is_social,
            is_territorial=is_territorial,
            exploration_tendency=exploration_tendency,
            needs_ground_resources=needs_ground_resources,
        )
    
    def __str__(self) -> str:
        """Representación legible para debugging.
        
        Returns:
            String con las capacidades principales en formato compacto.
            
        Examples:
            >>> str(caps)
            "MovementCapabilities(modes=['walk'], speed=1.0, vision=1.5, social=social, can_migrate=True)"
        """
        modes = []
        if self.can_walk:
            modes.append("walk")
        if self.can_fly:
            modes.append("fly")
        if self.can_swim:
            modes.append("swim")
        if self.can_burrow:
            modes.append("burrow")
        
        if not modes:
            modes.append("static")
        
        if self.is_social:
            social = "social"
        elif self.is_territorial:
            social = "territorial"
        else:
            social = "neutral"
        
        return (
            f"MovementCapabilities("
            f"modes={modes}, "
            f"speed={self.movement_speed:.1f}, "
            f"vision={self.vision_range:.1f}, "
            f"social={social}, "
            f"can_migrate={self.can_migrate}"
            f")"
        )
    
    def __repr__(self) -> str:
        """Representación completa para debugging."""
        return (
            f"MovementCapabilities("
            f"can_move={self.can_move}, "
            f"can_migrate={self.can_migrate}, "
            f"can_walk={self.can_walk}, "
            f"can_fly={self.can_fly}, "
            f"can_swim={self.can_swim}, "
            f"can_burrow={self.can_burrow}, "
            f"movement_speed={self.movement_speed}, "
            f"vision_range={self.vision_range}, "
            f"smell_range={self.smell_range}, "
            f"is_social={self.is_social}, "
            f"is_territorial={self.is_territorial}, "
            f"exploration_tendency={self.exploration_tendency}, "
            f"needs_ground_resources={self.needs_ground_resources}"
            f")"
        )