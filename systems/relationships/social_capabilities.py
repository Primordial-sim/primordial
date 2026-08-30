"""Capacidades sociales derivadas del genoma.

Este módulo determina qué tipo de vínculos sociales puede formar un organismo
basándose en sus capacidades cognitivas y rasgos sociales.

Niveles de complejidad social:
- Nivel 0: Sin interacciones sociales (plantas, bacterias)
- Nivel 1: Proximidad básica (peces, reptiles)
- Nivel 2: Vínculos grupales simples (lobos, aves sociales)
- Nivel 3: Vínculos complejos (primates, delfines)
- Nivel 4: Conceptos sociales abstractos (humanos)
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entities.person.genome import Genome


@dataclass
class SocialCapabilities:
    """Capacidades sociales derivadas del genoma."""
    
    # Capacidades básicas
    has_social_awareness: bool = False      # ¿Reconoce otros individuos?
    can_recognize_individuals: bool = False # ¿Distingue individuos específicos?
    can_form_relationships: bool = False    # ¿Puede formar vínculos?
    
    # Capacidades de vínculo
    can_form_cooperation: bool = False      # ¿Puede cooperar?
    can_form_conflict: bool = False         # ¿Puede tener conflictos?
    can_form_pair_bond: bool = False        # ¿Forma parejas estables?
    can_form_family_bonds: bool = False     # ¿Tiene vínculos familiares?
    can_form_group_identity: bool = False   # ¿Identidad grupal (manada, tribu)?
    
    # Capacidades complejas (humanas)
    can_have_friendship: bool = False       # ¿Puede tener amistades?
    can_have_romantic_bonds: bool = False   # ¿Puede tener vínculos románticos?
    can_have_marriage: bool = False         # ¿Puede "casarse"?
    can_have_divorce: bool = False          # ¿Puede "divorciarse"?
    can_have_social_reputation: bool = False # ¿Tiene reputación social?
    can_have_social_pressure: bool = False  # ¿Siente presión social?
    
    # Nivel continuo
    social_complexity: float = 0.0          # 0.0 a 1.0
    
    @classmethod
    def from_genome(cls, genome: 'Genome') -> 'SocialCapabilities':
        """Crea SocialCapabilities consultando el genoma."""
        
        def get_trait(trait_id: str, default: float = 0.0) -> float:
            if genome.has_trait(trait_id):
                return genome.get_trait_value(trait_id)
            return default
        
        # Obtener rasgos relevantes
        sociability = get_trait("sociability", 0.0)
        intelligence = get_trait("intelligence", 0.0)
        nervous_system = get_trait("nervous_system", 0.0)
        aggressiveness = get_trait("aggressiveness", 0.5)
        
        # === CAPACIDADES BÁSICAS ===
        # Reconocimiento social requiere sistema nervioso mínimo
        has_social_awareness = nervous_system >= 0.2 and sociability >= 0.2
        
        # Reconocimiento individual requiere más inteligencia
        can_recognize_individuals = (
            nervous_system >= 0.4 and 
            intelligence >= 0.3 and 
            sociability >= 0.3
        )
        
        # Formar relaciones requiere conciencia social + reconocimiento
        can_form_relationships = has_social_awareness and can_recognize_individuals
        
        # === CAPACIDADES DE VÍNCULO ===
        # Cooperación: sociabilidad media + reconocimiento individual
        can_form_cooperation = (
            sociability >= 0.4 and 
            intelligence >= 0.2 and 
            can_recognize_individuals
        )
        
        # Conflicto: requiere reconocimiento de individuos
        can_form_conflict = can_recognize_individuals and aggressiveness >= 0.3
        
        # Vínculos de pareja: sociabilidad alta + inteligencia media
        can_form_pair_bond = (
            sociability >= 0.7 and 
            intelligence >= 0.5 and 
            can_recognize_individuals
        )
        
        # Vínculos familiares: sociabilidad muy alta + inteligencia alta
        can_form_family_bonds = (
            sociability >= 0.8 and 
            intelligence >= 0.6 and 
            can_form_pair_bond
        )
        
        # Identidad grupal: sociabilidad alta + capacidad de cooperación
        can_form_group_identity = (
            sociability >= 0.6 and 
            can_form_cooperation and 
            intelligence >= 0.4
        )
        
        # === CAPACIDADES COMPLEJAS (HUMANAS) ===
        # Amistad: sociabilidad alta + inteligencia alta
        can_have_friendship = (
            sociability >= 0.7 and 
            intelligence >= 0.7 and 
            can_form_cooperation
        )
        
        # Vínculos románticos: inteligencia muy alta + sociabilidad alta
        can_have_romantic_bonds = (
            intelligence >= 0.7 and 
            sociability >= 0.7 and 
            can_form_pair_bond
        )
        
        # Matrimonio: concepto social abstracto (solo humanos y similares)
        can_have_marriage = (
            intelligence >= 0.8 and 
            can_have_romantic_bonds and 
            sociability >= 0.8
        )
        
        # Divorcio: requiere capacidad de matrimonio
        can_have_divorce = can_have_marriage
        
        # Reputación social: requiere memoria de individuos
        can_have_social_reputation = (
            intelligence >= 0.6 and 
            sociability >= 0.5 and 
            can_recognize_individuals
        )
        
        # Presión social: requiere conciencia de grupo
        can_have_social_pressure = (
            intelligence >= 0.6 and 
            sociability >= 0.7 and 
            can_form_group_identity
        )
        
        # === NIVEL CONTINUO ===
        social_complexity = max(0.0, min(1.0, 
            (sociability * 0.6 + intelligence * 0.4) * 
            (nervous_system if nervous_system > 0.1 else 0.0)
        ))
        
        return cls(
            has_social_awareness=has_social_awareness,
            can_recognize_individuals=can_recognize_individuals,
            can_form_relationships=can_form_relationships,
            can_form_cooperation=can_form_cooperation,
            can_form_conflict=can_form_conflict,
            can_form_pair_bond=can_form_pair_bond,
            can_form_family_bonds=can_form_family_bonds,
            can_form_group_identity=can_form_group_identity,
            can_have_friendship=can_have_friendship,
            can_have_romantic_bonds=can_have_romantic_bonds,
            can_have_marriage=can_have_marriage,
            can_have_divorce=can_have_divorce,
            can_have_social_reputation=can_have_social_reputation,
            can_have_social_pressure=can_have_social_pressure,
            social_complexity=social_complexity,
        )
    
    def can_have_label(self, label: str) -> bool:
        """Verifica si el organismo puede tener una etiqueta relacional específica."""
        label_map = {
            "Desconocido": True,  # Todos pueden reconocer desconocidos
            "Conocido": self.can_recognize_individuals,
            "Aliado": self.can_form_cooperation,
            "Amigo": self.can_have_friendship,
            "Familia Elegida": self.can_form_family_bonds,
            "Interés Romántico": self.can_have_romantic_bonds,
            "Amante": self.can_have_romantic_bonds,
            "Rival": self.can_form_conflict,
            "Rival Respetado": self.can_form_conflict and self.can_form_cooperation,
            "Enemigo": self.can_form_conflict,
        }
        return label_map.get(label, False)
    
    def can_participate_in_event(self, event_type: str) -> bool:
        """Verifica si puede participar en un tipo de evento relacional."""
        event_map = {
            "met": self.has_social_awareness,
            "care": self.can_form_cooperation,
            "cooperation": self.can_form_cooperation,
            "share_resource": self.can_form_cooperation,
            "intimacy": self.can_have_romantic_bonds,
            "reconciliation": self.can_form_cooperation and self.can_form_conflict,
            "competition": self.can_form_conflict,
            "betrayal": self.can_have_social_reputation,
            "conflict": self.can_form_conflict,
            "neglect": self.has_social_awareness,
            "birth": self.can_form_family_bonds,
            "child_death": self.can_form_family_bonds,
            "partner_death": self.can_form_pair_bond,
            "cohabitation_start": self.can_have_marriage,
            "cohabitation_end": self.can_have_divorce,
        }
        return event_map.get(event_type, False)
    
    def can_form_nucleus_type(self, nucleus_type: str) -> bool:
        """Verifica si puede formar un tipo de núcleo residencial."""
        nucleus_map = {
            "single": True,  # Todos pueden estar solos
            "couple": self.can_form_pair_bond,
            "family": self.can_form_family_bonds,
            "single_parent": self.can_form_family_bonds,
            "dependent_care": self.can_form_family_bonds,
        }
        return nucleus_map.get(nucleus_type, False)
    
    def __str__(self) -> str:
        return (
            f"SocialCapabilities("
            f"level={self.social_complexity:.2f}, "
            f"awareness={self.has_social_awareness}, "
            f"relationships={self.can_form_relationships}, "
            f"pair_bond={self.can_form_pair_bond}, "
            f"marriage={self.can_have_marriage}"
            f")"
        )
    
    def __repr__(self) -> str:
        return (
            f"SocialCapabilities("
            f"has_social_awareness={self.has_social_awareness}, "
            f"can_recognize_individuals={self.can_recognize_individuals}, "
            f"can_form_relationships={self.can_form_relationships}, "
            f"can_form_cooperation={self.can_form_cooperation}, "
            f"can_form_conflict={self.can_form_conflict}, "
            f"can_form_pair_bond={self.can_form_pair_bond}, "
            f"can_form_family_bonds={self.can_form_family_bonds}, "
            f"can_form_group_identity={self.can_form_group_identity}, "
            f"can_have_friendship={self.can_have_friendship}, "
            f"can_have_romantic_bonds={self.can_have_romantic_bonds}, "
            f"can_have_marriage={self.can_have_marriage}, "
            f"can_have_divorce={self.can_have_divorce}, "
            f"can_have_social_reputation={self.can_have_social_reputation}, "
            f"can_have_social_pressure={self.can_have_social_pressure}, "
            f"social_complexity={self.social_complexity}"
            f")"
        )