"""Módulo centralizado de configuración de la simulación.

Responsabilidad: 
Proveer una única fuente de verdad (Single Source of Truth) para todas las constantes, 
probabilidades y límites biológicos del motor. Esto elimina números mágicos y asegura 
que todos los sistemas compartan las mismas reglas físicas y temporales.
"""

import logging
from typing import Any


class EngineConfig:
    """Parámetros de ejecución del bucle principal."""
    def __init__(self) -> None:
        self.total_days: float = 3650.0  # 10 años
        self.delta_days: float = 1.0


class AdoptionsConfig:
    """Umbrales biológicos y legales para el sistema de adopciones."""
    def __init__(self) -> None:
        self.max_orphan_age_days: float = 6205.0
        self.min_adoptive_age_days: float = 9125.0
        self.max_children_for_adoption: int = 3
        
        self.abandonment_stress_rate: float = 0.02
        self.abandonment_happiness_rate: float = 0.015
        self.abandonment_trauma_rate: float = 0.01
        self.abandonment_mortality_multiplier: float = 1.8
        
        self.age_penalty_multiplier: float = 50.0
        self.age_penalty_exponent: float = 2.0
        
        self.allow_single_parent_adoption: bool = True
        self.min_single_parent_age_days: float = 12775.0
        self.single_parent_penalty: float = 25.0
        self.min_single_parent_energy: float = 0.7
        self.max_single_parent_stress: float = 0.5

        self.kinship_weight: float = 100.0
        self.distance_weight: float = 0.2
        self.pressure_weight: float = 50.0
        self.sociability_weight: float = 10.0
        self.stress_weight: float = 30.0
        self.happiness_weight: float = 20.0
        self.children_count_weight: float = 5.0
        self.stability_weight: float = 1.5
        self.senior_penalty: float = 10.0
        self.motivation_protection_weight: float = 20.0
        self.motivation_cooperation_weight: float = 15.0


class CognitionConfig:
    """Parámetros de memoria, trauma y psicología de los agentes."""
    def __init__(self) -> None:
        self.base_forgetting_rate: float = 0.2
        self.temperament_modifier: float = 0.5
        self.max_trauma_cap: float = 1.0
        
        self.overcrowding_threshold: float = 1.3
        self.overcrowding_impact: float = 0.1
        self.sickness_impact: float = 0.15
        self.abandonment_impact: float = 0.12
        
        self.episodic_forgetting_rate: float = 0.05
        self.episodic_min_intensity: float = 0.05
        self.max_episodic_memories: int = 50
        self.emotional_importance_factor: float = 0.3
        
        self.sector_preference_probability: float = 0.01
        self.sector_preference_min_days: float = 30.0
        
        self.trauma_to_stress_factor: float = 0.15
        self.nostalgia_buffer_factor: float = 0.1
        self.max_cognitive_stress: float = 0.8


class MutationConfig:
    """Configuración global de mutación genética."""
    def __init__(self) -> None:
        self.probability: float = 0.05
        self.magnitude_std: float = 0.1
        self.mutate_dominance: bool = False
        self.dominance_std: float = 0.05


class ReproductionConfig:
    """Límites, ventanas de fertilidad y probabilidades de reproducción."""
    def __init__(self) -> None:
        self.single_mother_conception_chance: float = 0.03
        self.miscarriage_chance_sick: float = 0.25
        self.pregnancy_duration_days: float = 270.0
        self.mutation_factor: float = 0.05
        self.min_genome_value: float = 0.01
        self.min_fertility_age_days: float = 6570.0
        self.max_fertility_age_days: float = 16425.0
        self.daily_birth_rate: float = 0.0033
        self.base_conception_chance: float = 0.15

        self.species_profiles: dict = {
            "human": {"parthenogenesis_chance": 0.0, "litter_size_min": 1, "litter_size_max": 1, "gestation_days": self.pregnancy_duration_days},
            "elf": {"parthenogenesis_chance": 0.0, "litter_size_min": 1, "litter_size_max": 1, "gestation_days": 730.0},
            "goblin": {"parthenogenesis_chance": 0.05, "litter_size_min": 3, "litter_size_max": 6, "gestation_days": 120.0},
            "dragon": {"parthenogenesis_chance": 0.1, "litter_size_min": 1, "litter_size_max": 3, "gestation_days": 1200.0}
        }


class MovementConfig:
    """Parámetros de desplazamiento espacial."""
    def __init__(self) -> None:
        self.base_speed: float = 0.5
        self.proximity_threshold: float = 0.1


class DiseasesConfig:
    """Parámetros de propagación y comportamiento epidemiológico."""
    def __init__(self) -> None:
        self.base_outbreak_chance: float = 1.5
        self.base_transmission_chance: float = 0.18
        self.base_recovery_chance: float = 0.15
        self.transmission_radius: int = 2
        self.environmental_transmission_rate: float = 0.15
        
        self.base_virulence: float = 0.5
        self.base_transmission: float = 0.3
        self.base_lethality: float = 0.1
        self.immunity_clamping: float = 0.1


class EvolutionConfig:
    """Parámetros para la analítica macroevolutiva y recolección de métricas."""
    def __init__(self) -> None:
        self.snapshot_interval_days: float = 30.0
        self.variance_extinction_threshold: float = 0.01
        self.mean_extinction_threshold: float = 0.2


class FreeWillConfig:
    """Parámetros del sistema de motivaciones continuas y comportamiento emergente."""
    def __init__(self) -> None:
        self.motivations: list = [
            "independence", "exploration", "rebellion", "partnership",
            "protection", "migration", "cooperation", "fertility_desire"
        ]

        self.action_threshold: float = 0.7
        self.independence_action_threshold: float = 0.75
        self.exploration_action_threshold: float = 0.7
        self.rebellion_action_threshold: float = 0.8
        self.partnership_action_threshold: float = 0.65
        self.protection_action_threshold: float = 0.7
        self.migration_action_threshold: float = 0.85
        self.cooperation_action_threshold: float = 0.6
        
        self.motivation_decay_rate: float = 0.02
        
        self.migration_cooldown_days: float = 90.0
        self.marriage_cooldown_days: float = 180.0
        self.divorce_cooldown_days: float = 365.0
        self.reconciliation_cooldown_days: float = 180.0
        
        self.impulsivity_weight: float = 0.4
        self.curiosity_weight: float = 0.4
        self.obedience_weight: float = 0.4
        self.aggressiveness_weight: float = 0.3
        self.temperament_weight: float = 0.3
        self.sociability_weight: float = 0.3
        
        self.stress_weight: float = 0.3
        self.happiness_weight: float = 0.2
        self.energy_weight: float = 0.2
        self.pressure_weight: float = 0.3
        self.crowding_weight: float = 0.2
        
        self.success_reinforcement_rate: float = 0.15
        self.failure_punishment_rate: float = 0.1
        self.experience_decay_rate: float = 0.01
        self.inhibition_factor: float = 0.2
        
        self.adolescence_start_days: float = 3650.0
        self.adolescence_end_days: float = 6570.0
        self.early_leave_age_min: float = 3650.0
        self.early_leave_age_max: float = 6570.0
        
        self.cognitive_stress_factor: float = 0.3
        self.trauma_factor: float = 0.4
        self.episodic_memory_factor: float = 0.3
        self.sickness_factor: float = 0.3
        
        # Compatibilidad hacia atrás
        self.base_anomaly_chance: float = 0.015
        self.taboo_relation_chance_multiplier: float = 0.5
        self.early_leave_trauma_multiplier: float = 2.0
        self.out_of_wedlock_chance_multiplier: float = 1.0
        self.single_parent_chance_multiplier: float = 1.2
        self.unexpected_migration_chance_multiplier: float = 0.8
        self.cognitive_stress_impulse_factor: float = 1.5
        self.social_bias_influence_factor: float = 0.7
        self.divorce_temperament_threshold: float = 0.75
        self.divorce_chance_multiplier: float = 0.1
        self.migration_density_threshold: float = 1.6
        self.migration_sociability_threshold: float = 0.3
        self.migration_chance_multiplier: float = 0.2
        self.migration_radius: int = 12
        self.fertility_rebellion_children_threshold: int = 3
        self.fertility_rebellion_temperament_threshold: float = 0.7


class MortalityConfig:
    """Reglas de la curva de Gompertz y selección natural."""
    def __init__(self) -> None:
        self.base_life_expectancy_days: float = 25550.0
        self.infant_threshold_days: float = 1095.0
        self.infant_mortality_rate: float = 0.02
        self.hard_cap_age_days: float = 41975.0
        self.density_penalty_threshold: float = 1.2
        self.density_penalty_multiplier: float = 1.5
        self.alpha_base: float = 0.0001
        self.beta_base: float = 0.08
        self.sickness_penalty_multiplier: float = 2.5
        self.min_sickness_penalty: float = 1.1
        self.genome_clamping: float = 0.01


class RelationshipsConfig:
    """Parámetros de dinámica social, compatibilidad y transiciones relacionales."""
    def __init__(self) -> None:
        self.affinity_weight: float = 0.60
        self.age_weight: float = 0.15
        self.distance_weight: float = 0.10
        self.orientation_tolerance: float = 1.5
        
        self.min_affinity_for_dating: float = 0.50
        self.min_affinity_for_cohabitation: float = 0.55
        self.min_affinity_for_consolidated: float = 0.60
        self.min_days_for_cohabitation: float = 180.0
        self.min_days_for_consolidated: float = 730.0
               
        self.breakup_affinity_threshold: float = 0.30
        self.casual_affinity_threshold: float = 0.50
        self.friendship_recovery_threshold: float = 0.40
        self.max_days_unknown: float = 548.0

        self.environmental_asymptomatic_chance: float = 0.3
        self.environmental_incubation_days: float = 5.0
        self.pathogen_families: list = ["Influenza", "Coronavirus", "Poxvirus", "Bacteriofago_X"]
                
        self.min_marriage_age_days: float = 6570.0
        self.ideal_marriage_age_days: float = 8395.0
        self.courtship_radius: int = 20
        self.base_marriage_chance: float = 0.01
        self.daily_marriage_rate: float = 0.00137
        self.love_at_first_sight_chance: float = 0.001


class EnvironmentConfig:
    """Restricciones espaciales y de capacidad de carga de recursos."""
    def __init__(self) -> None:
        self.sector_size: int = 10
        self.carrying_capacity: int = 200
        self.max_agents_per_sector: int = 8
        
        self.max_viral_load: float = 10.0
        self.viral_decay_factor: float = 0.90
        self.environmental_transmission_rate: float = 0.15
        
        self.viral_load_threshold: float = 0.1
        self.viral_to_risk_factor: float = 0.033
        self.viral_exhalation_rate: float = 0.5


class TimeConfig:
    """Parámetros para la progresión temporal macroscópica y ciclos vitales."""
    def __init__(self) -> None:
        self.adult_age_days: float = 6570.0
        self.senior_age_days: float = 21900.0
        self.days_per_month: float = 30.0
        self.days_per_year: float = 365.0


class GenealogyConfig:
    """Parámetros de rastreo histórico y restricciones de parentesco."""
    def __init__(self) -> None:
        self.consanguinity_limit: int = 3


class MetricsConfig:
    """Parámetros para la recolección de métricas poblacionales."""
    def __init__(self) -> None:
        self.snapshot_interval_days: float = 1.0


class AgingConfig:
    """Parámetros de envejecimiento y desgaste biológico multifactorial."""
    def __init__(self) -> None:
        self.reproductive_wear_per_child: float = 0.015
        self.max_children_for_aging: int = 10
        self.max_reproductive_wear_multiplier: float = 2.0
        self.pregnancy_burden_multiplier: float = 1.2
        self.stress_aging_factor: float = 0.5
        self.sickness_aging_factor: float = 0.3
        self.low_energy_aging_factor: float = 0.4
        self.longevity_genetic_factor: float = 1.0
        self.father_reproductive_wear_ratio: float = 0.5


class EnergyConfig:
    """Parámetros del sistema de metabolismo energético."""
    def __init__(self) -> None:
        # Metabolismo basal (REDUCIDO para dar más margen)
        self.basal_metabolic_rate: float = 0.05
        self.starvation_death_threshold: float = 30.0
        self.starvation_damage_rate: float = 0.05
        
        # Fotosíntesis (AUMENTADO para plantas más productivas)
        self.photosynthesis_rate: float = 8.0
        self.photosynthesis_light_factor: float = 1.0
        
        # NUEVO: Forrajeo pasivo para heterótrofos
        self.passive_foraging_rate: float = 0.05
        self.foraging_vegetation_threshold: float = 0.3


class ExperienceConfig:
    """Parámetros del generador de experiencias relacionales."""
    def __init__(self) -> None:
        self.log_interval: int = 365


class EnvironmentDynamicsConfig:
    """Parámetros de la dinámica ambiental del mundo."""
    def __init__(self) -> None:
        self.medium_scale_interval: float = 15.0
        self.slow_scale_interval: float = 180.0


class MigrationConfig:
    """Parámetros del sistema de migraciones a larga distancia."""
    def __init__(self) -> None:
        self.arrival_threshold: float = 5.0


class FeedbackConfig:
    """Parámetros del sistema de retroalimentación organismos-entorno."""
    def __init__(self) -> None:
        self.process_interval_days: float = 5.0


class EcologyConfig:
    """Parámetros del sistema de relaciones ecológicas."""
    def __init__(self) -> None:
        self.process_interval_days: float = 3.0


class ParentalInfluenceConfig:
    """Parámetros del sistema de influencia parental."""
    def __init__(self) -> None:
        self.max_influence_age_days: float = 5000.0
        self.base_personality_plasticity: float = 0.05
        self.log_interval_days: float = 365.0


class SimulationConfig:
    """Configuración maestra que agrupa y expone todos los subsistemas."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("SimulationConfig")
        self.engine = EngineConfig()
        self.time = TimeConfig()
        self.reproduction = ReproductionConfig()
        self.diseases = DiseasesConfig()
        self.mortality = MortalityConfig()
        self.environment = EnvironmentConfig()
        self.adoptions = AdoptionsConfig()
        self.cognition = CognitionConfig()
        self.evolution = EvolutionConfig()
        self.free_will = FreeWillConfig()
        self.genealogy = GenealogyConfig()
        self.metrics = MetricsConfig()
        self.movement = MovementConfig()
        self.relationships = RelationshipsConfig()
        self.aging = AgingConfig()
        self.ecology = EcologyConfig()
        self.energy = EnergyConfig()
        self.feedback = FeedbackConfig()
        self.migration = MigrationConfig()
        self.environment_dynamics = EnvironmentDynamicsConfig()
        self.experience = ExperienceConfig()
        self.parental_influence = ParentalInfluenceConfig()

    def set_parameter(self, category: str, key: str, value: Any) -> bool:
        """Modifica un parámetro en caliente durante la ejecución."""
        target_obj = getattr(self, category, None)
        if not target_obj or not hasattr(target_obj, key):
            self.logger.warning(f"[CONFIG] Error: No existe la propiedad {category}.{key}")
            return False
            
        old_val = getattr(target_obj, key)
        setattr(target_obj, key, value)
        self.logger.info(f"[CONFIG] {category}.{key} actualizado dinámicamente: {old_val} -> {value}")
        return True

    def get_parameter(self, category: str, key: str, default: Any = None) -> Any:
        """Recupera un parámetro de forma segura."""
        target_obj = getattr(self, category, None)
        if not target_obj:
            self.logger.error(f"[CONFIG] Categoría '{category}' no encontrada en el sistema.")
            return default
        return getattr(target_obj, key, default)