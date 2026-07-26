"""Módulo responsable de la transición de estado hacia la gestación biológica.

Implementa un modelo multifactorial de concepción que considera:
- Compatibilidad sexual (orientación Kinsey + género)
- Estado de la relación (modificador de probabilidad)
- Fertilidad biológica (edad + genética + salud)
- Deseo de engendrar (motivación continua)
- Épocas de celo (temporalidad por especie)

La concepción NO es binaria: incluso relaciones casuales pueden producir
embarazos (con baja probabilidad), y parejas estables tienen alta probabilidad.

Soporta estrategias reproductivas avanzadas:
- Partenogénesis (especies que la soporten)
- Camadas múltiples (litters)
- Selección de rasgos por especie

FASE 0: Integra con RelationshipExperienceEngine emitiendo eventos ligeros
compatibles de INTIMACY cuando dos agentes conciben juntos, fortaleciendo 
su vínculo a través de recuerdos.
"""

import random
import math
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from core.state.world_state import WorldState
from core.state.pending_changes import PendingChanges
from systems.environment.environment_context import EnvironmentContext
from core.config.simulation_config import SimulationConfig
from systems.relationships.relationship_model import (
    RelationshipStatus,
    SexualOrientation,
    is_orientation_compatible,
    RelationshipEventType,
)
from systems.relationships.relationship_experience_engine import RelationshipExperienceEngine


@dataclass
class _ConceptionRelationalEvent:
    """Evento ligero compatible con el RelationshipExperienceEngine de la Fase 0."""
    event_type: RelationshipEventType
    intensity: float
    context: str


class ConceptionSystem:
    """Gestiona la iniciación de la gestación con modelo multifactorial."""

    def __init__(
        self, 
        config: SimulationConfig,
        relationship_engine: Optional[RelationshipExperienceEngine] = None,
    ) -> None:
        self.config = config
        self.relationship_engine = relationship_engine
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # =====================================================================
        # MODIFICADORES POR ESTADO DE RELACIÓN
        # =====================================================================
        self.relationship_modifiers: Dict[RelationshipStatus, float] = {
            RelationshipStatus.CONSOLIDATED: 1.0,
            RelationshipStatus.COHABITATION: 0.85,
            RelationshipStatus.DATING: 0.50,
            RelationshipStatus.ROMANTIC_INTEREST: 0.25,
            RelationshipStatus.CASUAL: 0.08,
            RelationshipStatus.FRIENDSHIP: 0.02,
            RelationshipStatus.ACQUAINTANCE: 0.01,
            RelationshipStatus.UNKNOWN: 0.005,
        }
        
        # =====================================================================
        # CURVA DE FERTILIDAD POR EDAD (Humanos)
        # =====================================================================
        self.age_fertility_curve: Dict[Tuple[float, float], float] = {
            (0, 5475): 0.0,
            (5475, 7300): 0.50,
            (7300, 10950): 1.0,
            (10950, 12775): 0.80,
            (12775, 14600): 0.50,
            (14600, 16425): 0.20,
            (16425, 99999): 0.0,
        }
        
        # =====================================================================
        # PENALIZADORES POR ENFERMEDADES
        # =====================================================================
        self.disease_fertility_penalties: Dict[str, float] = {
            "impotence": 0.0,
            "low_libido": 0.3,
            "std_chlamydia": 0.4,
            "std_gonorrhea": 0.3,
            "std_hiv": 0.2,
            "pcos": 0.5,
            "endometriosis": 0.4,
            "genetic_infertility": 0.1,
        }
        
        # =====================================================================
        # ÉPOCAS DE CELO POR ESPECIE
        # =====================================================================
        self.mating_seasons: Dict[str, list] = {
            "human": ["SPRING", "SUMMER", "AUTUMN", "WINTER"],
            "elf": ["SPRING"],
            "goblin": ["SUMMER", "AUTUMN"],
            "dragon": ["WINTER"],
        }
        
        self.off_season_multiplier: float = 0.3

    def _get_species_traits(self, species: str) -> dict:
        """Provee los perfiles reproductivos por especie."""
        profiles = {
            "human": {
                "parthenogenesis_chance": 0.0,
                "litter_size_min": 1,
                "litter_size_max": 1,
                "gestation_days": self.config.reproduction.pregnancy_duration_days
            },
            "elf": {
                "parthenogenesis_chance": 0.0,
                "litter_size_min": 1,
                "litter_size_max": 1,
                "gestation_days": 730.0
            },
            "goblin": {
                "parthenogenesis_chance": 0.05,
                "litter_size_min": 3,
                "litter_size_max": 6,
                "gestation_days": 120.0
            },
            "dragon": {
                "parthenogenesis_chance": 0.1,
                "litter_size_min": 1,
                "litter_size_max": 3,
                "gestation_days": 1200.0
            }
        }
        return profiles.get(species, profiles["human"])

    def _is_sexually_compatible(self, person1: Any, person2: Any) -> bool:
        """Verifica compatibilidad sexual (orientación + género)."""
        orientation_score = is_orientation_compatible(
            person1.sexual_orientation,
            person2.sexual_orientation,
            tolerance=self.config.relationships.orientation_tolerance,
        )
        if orientation_score <= 0.0:
            return False
        
        genders = {person1.gender, person2.gender}
        if genders == {"M", "F"} or genders == {"F", "M"}:
            return True
        
        return False

    def _get_relationship_status(self, person: Any, partner_id: int) -> RelationshipStatus:
        """Obtiene el estado de la relación con un partner específico."""
        if not hasattr(person, 'get_relationship_with'):
            return RelationshipStatus.CONSOLIDATED
        
        rel = person.get_relationship_with(partner_id)
        if rel:
            # FASE 0: Usamos getattr para compatibilidad con el campo legacy 'status'
            return getattr(rel, 'status', RelationshipStatus.UNKNOWN)
        return RelationshipStatus.UNKNOWN

    def _get_age_fertility_modifier(self, age: float) -> float:
        """Calcula el modificador de fertilidad según la edad."""
        for (min_age, max_age), modifier in self.age_fertility_curve.items():
            if min_age <= age < max_age:
                return modifier
        return 0.0

    def _get_health_modifier(self, person: Any) -> float:
        """Calcula el modificador de fertilidad según la salud."""
        if not getattr(person, 'is_sick', False):
            return 1.0
        
        penalty = 1.0
        for infection_id in person.active_infections.keys():
            disease_name = infection_id.split('_')[0].lower()
            if disease_name in self.disease_fertility_penalties:
                penalty *= self.disease_fertility_penalties[disease_name]
        
        return max(0.0, penalty)

    def _get_fertility_desire(self, person: Any) -> float:
        """Obtiene el deseo de engendrar (motivación)."""
        if hasattr(person, 'get_motivation'):
            desire = person.get_motivation("fertility_desire")
            if desire > 0:
                return desire
        
        age = person.age
        if 7300 <= age <= 14600:
            return 0.5
        elif 5475 <= age <= 7300 or 14600 < age <= 16425:
            return 0.3
        else:
            return 0.1

    def _get_seasonal_modifier(self, person: Any, current_season: str) -> float:
        """Calcula el modificador de fertilidad según la estación."""
        species = person.species
        mating_seasons = self.mating_seasons.get(species, [])
        
        if current_season in mating_seasons:
            return 1.0
        else:
            return self.off_season_multiplier

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Evalúa posibilidades de concepción para todos los agentes fértiles."""
        rep_cfg = self.config.reproduction
        time_cfg = self.config.time
        
        current_day = getattr(state, 'world_days_elapsed', 0.0)
        
        daily_rate = rep_cfg.base_conception_chance / time_cfg.days_per_year
        base_prob_period = 1.0 - math.exp(-daily_rate * delta_days)
        
        current_season = getattr(context, 'current_season', 'SPRING')

        for person in state.get_all_persons():
            if person.entity_id in pending.deaths or getattr(person, 'is_pregnant', False):
                continue

            traits = self._get_species_traits(person.species)
            
            # =================================================================
            # 1. REPRODUCCIÓN ASEXUAL (Partenogénesis)
            # =================================================================
            if traits["parthenogenesis_chance"] > 0:
                if random.random() < traits["parthenogenesis_chance"]:
                    litter_size = random.randint(traits["litter_size_min"], traits["litter_size_max"])
                    pending.register_pregnancy_update(
                        person.entity_id, True, 0.0, failed_increment=0, litter_size=litter_size
                    )
                    self.logger.debug(
                        "🧬 Concepción asexual: Agente %s (Camada: %d)",
                        person.entity_id, litter_size
                    )
                continue

            # =================================================================
            # 2. REPRODUCCIÓN SEXUAL (modelo multifactorial)
            # =================================================================
            
            age_modifier = self._get_age_fertility_modifier(person.age)
            if age_modifier <= 0.0:
                continue
            
            fertility_desire = self._get_fertility_desire(person)
            if fertility_desire <= 0.0:
                continue
            
            potential_partners = []
            for other in state.get_all_persons():
                if other.entity_id == person.entity_id:
                    continue
                if other.entity_id in pending.deaths:
                    continue
                if not self._is_sexually_compatible(person, other):
                    continue
                
                partner_age_modifier = self._get_age_fertility_modifier(other.age)
                if partner_age_modifier <= 0.0:
                    continue
                
                rel_status = self._get_relationship_status(person, other.entity_id)
                rel_modifier = self.relationship_modifiers.get(rel_status, 0.01)
                
                if rel_status == RelationshipStatus.UNKNOWN and rel_modifier < 0.01:
                    continue
                
                potential_partners.append((other, rel_status, rel_modifier))
            
            if not potential_partners:
                continue
            
            for partner, rel_status, rel_modifier in potential_partners:
                health_modifier = self._get_health_modifier(person) * self._get_health_modifier(partner)
                seasonal_modifier = self._get_seasonal_modifier(person, current_season)
                
                genetic_fertility = (person.genome.fertility + partner.genome.fertility) / 2.0
                
                energy_multiplier = min(person.emotions["energy"], partner.emotions["energy"])
                
                final_chance = (
                    base_prob_period *
                    rel_modifier *
                    age_modifier *
                    genetic_fertility *
                    health_modifier *
                    fertility_desire *
                    seasonal_modifier *
                    energy_multiplier
                )
                
                final_chance = max(0.0, min(1.0, final_chance))
                
                if random.random() < final_chance:
                    litter_size = random.randint(traits["litter_size_min"], traits["litter_size_max"])
                    pending.register_pregnancy_update(
                        person.entity_id, True, 0.0, failed_increment=0, litter_size=litter_size
                    )
                    
                    # FASE 0: Emitir evento de INTIMACY usando la clase compatible
                    if self.relationship_engine:
                        intimacy_event = _ConceptionRelationalEvent(
                            event_type=RelationshipEventType.INTIMACY,
                            intensity=0.6,
                            context=f"concepcion_en_{rel_status.value}",
                        )
                        self.relationship_engine.process_event(
                            intimacy_event, person, partner, current_day
                        )
                    
                    self.logger.debug(
                        "👶 Concepción: %s y %s (relación: %s, prob: %.4f, camada: %d)",
                        person.entity_id, partner.entity_id,
                        rel_status.value, final_chance, litter_size
                    )
                    
                    break