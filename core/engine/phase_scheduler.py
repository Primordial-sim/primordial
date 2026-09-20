"""Planificador de fases del motor de simulación.

DOCUMENTACIÓN DEL CICLO DE VIDA (TICK):
-------------------------------------------------------------------------------
La simulación opera en una arquitectura de Tiempo Discreto con Búfer Transaccional.
Cada tick completo procesa las siguientes fases en estricto orden secuencial:

JERARQUÍA DE PRIORIDAD SOCIAL (BLOQUE 4):
1. Muerte (mortalidad) - Prioridad máxima: un agente muerto no puede adoptar ni migrar
2. Nacimiento (reproduction) - Prioridad alta: nuevos agentes necesitan contexto social
3. Adopción (relationships) - Prioridad media-alta: reestructuración familiar
4. Matrimonio/Relaciones (relationships) - Prioridad media: transiciones relacionales
5. Migración (behavior_and_movement) - Prioridad media-baja: movimiento espacial
6. Otros comportamientos (behavior_and_movement) - Prioridad baja

ORDEN DE FASES:
1. Fase Temporal ('temporal'):
   - Actualiza los relojes internos de la simulación.
   - Incrementa la edad biológica de las entidades en el búfer transaccional.

2. Fase Ambiental ('environment'):
   - Propaga variables físicas (cargas virales, degradación de recursos).
   - Calcula el mapa de densidad poblacional.
   - BLOQUE 4: Aplica "Social Pressure Field" (eventos sociales del tick anterior).
   - Actualiza la memoria cognitiva de los agentes según el estrés del entorno.

3. Fase Ecológica ('ecology'):
   - Detecta encuentros entre organismos cercanos (SpatialGrid).
   - Infiere y ejecuta relaciones ecológicas (depredación, herbivoría, mutualismo, competencia).
   - Verifica condiciones ambientales (bioma, estación).

4. Fase Social ('relationships'):
   - Precalcula compatibilidades (CompatibilityEngine).
   - BLOQUE B: Gestiona formación de relaciones (MarriageSystem).
   - BLOQUE B: Gestiona mantenimiento y ruptura (RelationshipSystem).
   - Procesa reasignaciones familiares legales (Adopciones).
   - Genera experiencias basadas en etiquetas (ExperienceGenerator).

5. Fase de Movimiento y Conducta ('behavior_and_movement'):
   - Evalúa decisiones autónomas y rebeldía (FreeWillSystem).
   - Calcula vectores de migración masiva (MigrationSystem).
   - Genera vectores de desplazamiento para el tick (MovementSystem).
   - Resuelve colisiones espaciales físicas (MovementResolver).

6. Fase de Salud ('health'):
   - Resuelve interacciones inmunológicas y calcula contagios/recuperaciones.
   - Emite eventos relacionales (cuidado, duelo) al RelationshipExperienceEngine.

7. Fase Reproductiva ('reproduction'):
   - Verifica las ventanas de fertilidad e inicia concepciones.
   - Procesa los embarazos en curso y encola nacimientos con mutaciones genéticas.

8. Fase de Mortalidad ('mortality'):
   - Calcula las curvas de supervivencia (Gompertz) y decreta fallecimientos.
   - Purga las acciones de los recién fallecidos del búfer (DeathResolver).

9. Fase Observacional ('observers'):
   - Sincroniza el árbol genealógico.
   - Actualiza métricas poblacionales macroscópicas y el motor evolutivo.

[COMMIT]: Al terminar el pipeline, `WorldState.apply_commit()` consolida el 
búfer y altera los objetos de memoria.
-------------------------------------------------------------------------------
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from core.config.simulation_config import SimulationConfig
from core.execution.phase_executor import PhaseDefinition

# Importaciones de los subsistemas del motor
from systems.adoptions.adoption_system import AdoptionSystem
from systems.aging.aging_system import AgingSystem
from systems.behavior.cognitive_memory_system import CognitiveMemorySystem
from systems.diseases.disease_system import DiseaseSystem
from systems.environment.density_system import DensitySystem
from systems.environment.environment_system import EnvironmentSystem
from systems.environment.epidemiological_system import EpidemiologicalSystem
from systems.social.social_pressure import SocialPressureCalculator
from systems.evolution.evolution_engine import EvolutionEngine
from systems.free_will.free_will_system import FreeWillSystem
from systems.genealogy.ancestry_queries import AncestryQueries
from systems.genealogy.genealogy_system import GenealogySystem
from systems.metrics.metrics_system import MetricsSystem
from systems.mortality.death_resolver import DeathResolver
from systems.mortality.mortality_system import MortalitySystem
from systems.movement.migration_system import MigrationSystem
from systems.movement.movement_resolver import MovementResolver
from systems.movement.movement_system import MovementSystem

# Sistemas de relaciones
from systems.relationships.compatibility_engine import CompatibilityEngine
from systems.relationships.marriage_system import MarriageSystem
from systems.relationships.relationship_manager import RelationshipManager
from systems.relationships.relationship_experience_engine import RelationshipExperienceEngine
from systems.relationships.experience_generator import ExperienceGenerator

from systems.reproduction.conception_system import ConceptionSystem
from systems.reproduction.gestation_system import GestationSystem
from systems.reproduction.egg_system import EggSystem  # NUEVO: Sistema de huevos ovíparos
from systems.temporal.temporal_system import TemporalSystem

from systems.ecology.ecological_relationship_system import EcologicalRelationshipSystem 
from systems.energy.energy_system import EnergySystem  # NUEVO: Sistema de energía

class PhaseScheduler:
    """Construye la lista maestra de fases y sistemas activos del motor."""

    def __init__(
        self, 
        config: SimulationConfig, 
        event_bus: Any = None,
        relationship_engine: Optional[RelationshipExperienceEngine] = None,
    ) -> None:
        """Inicializa el planificador orquestando la inyección de dependencias.

        Args:
            config: Configuración compartida de la simulación.
            event_bus: Bus de eventos opcional para sistemas que lo requieran.
            relationship_engine: Motor de experiencias relacionales opcional.
        """
        self.config = config
        self.event_bus = event_bus
        self.relationship_engine = relationship_engine
        self.logger = logging.getLogger(self.__class__.__name__)

    def build_phases(self) -> list[PhaseDefinition]:
        """Ensambla las fases de ejecución en el orden del ciclo principal.
        
        BLOQUE 4: Reordenamiento para establecer jerarquía social clara:
        - relationships va ANTES de behavior_and_movement (adopción antes que migración)
        - Se añade SocialPressureCalculator en environment para feedback social
        
        BLOQUE B: Integración de MarriageSystem y RelationshipSystem
        - MarriageSystem gestiona formación de relaciones (búsqueda bidireccional)
        - RelationshipSystem gestiona mantenimiento y ruptura (estados graduales)
        """
        # Construcción de dependencias compartidas inter-sistema
        genealogy_system = GenealogySystem(self.config)
        ancestry_queries = AncestryQueries(genealogy_system=genealogy_system)

        evolution_engine = EvolutionEngine(
            self.config,
            ancestry_queries=ancestry_queries,
        )

        density_system = DensitySystem(self.config)

        # Sistemas de relaciones
        compatibility_engine = CompatibilityEngine(self.config)
        
        # BLOQUE B: MarriageSystem (formación de relaciones)
        marriage_system = MarriageSystem(
            config=self.config,
            compatibility_engine=compatibility_engine,
            relationship_engine=self.relationship_engine,
        )
        
        # CORRECCIÓN: relationship_system ya no se usa (eliminado del pipeline)
        # relationship_system = RelationshipSystem(
        #     config=self.config,
        #     relationship_engine=self.relationship_engine,
        # )
        
        # RelationshipManager existente (transiciones relacionales)
        relationship_manager = RelationshipManager(
            config=self.config,
            compatibility_engine=compatibility_engine,
        )
        
        # FASE 3: Generador de experiencias basado en etiquetas
        experience_generator = ExperienceGenerator(
            config=self.config,
            relationship_engine=self.relationship_engine,
        )

        # BLOQUE 4: Sistema de presión social unificado
        # CORRECCIÓN: Se usa una sola instancia (antes se creaban dos)
        social_pressure_system = SocialPressureCalculator(self.config)

        # OPCIÓN B.2: Sistema de huevos ovíparos
        # Procesa incubación, mortalidad ambiental y eclosión de huevos
        egg_system = EggSystem(self.config)

        # Sistema de ecología (compartido con MetricsSystem para métricas)
        ecological_system = EcologicalRelationshipSystem()

        # Definición estructurada del ciclo biológico y físico
        phases = [
            # ================================================================
            # FASE 1: TEMPORAL
            # ================================================================
            PhaseDefinition(
                name="temporal",
                systems=[
                    TemporalSystem(self.config),
                    AgingSystem(self.config),
                ],
            ),
            
            # ================================================================
            # FASE 2: AMBIENTAL
            # ================================================================
            PhaseDefinition(
                name="environment",
                systems=[
                    EnvironmentSystem(self.config),
                    density_system,
                    EpidemiologicalSystem(self.config),
                    social_pressure_system,  # CORRECCIÓN: usar la variable existente
                    CognitiveMemorySystem(self.config),
                ],
            ),
            
            # ================================================================
            # FASE 3: ECOLOGÍA (RELACIONES ENTRE ESPECIES Y ENERGÍA)
            # ================================================================
            PhaseDefinition(
                name="ecology",
                systems=[
                    ecological_system,  # Variable compartida para métricas
                    EnergySystem(self.config),
                ],
            ),
            
            # ================================================================
            # FASE 4: SOCIAL (RELACIONES)
            # ================================================================
            PhaseDefinition(
                name="relationships",
                systems=[
                    compatibility_engine,
                    marriage_system,         # Genera eventos de intimidad
                    relationship_manager,    # Crea relaciones iniciales y detecta encuentros
                    AdoptionSystem(
                        config=self.config,
                        ancestry_queries=ancestry_queries,
                        event_bus=self.event_bus,
                        relationship_engine=self.relationship_engine,
                    ),
                    experience_generator,    # Genera experiencias basadas en etiquetas
                ],
            ),
            
            # ================================================================
            # FASE 5: MOVIMIENTO Y CONDUCTA
            # ================================================================
            PhaseDefinition(
                name="behavior_and_movement",
                systems=[
                    FreeWillSystem(
                        config=self.config,
                        relationship_engine=self.relationship_engine,
                    ),
                    MigrationSystem(self.config),
                    MovementSystem(
                        config=self.config,
                        density_system=density_system,
                        relationship_engine=self.relationship_engine,
                    ),
                    MovementResolver(self.config),
                ],
            ),
            
            # ================================================================
            # FASE 6: SALUD
            # ================================================================
            PhaseDefinition(
                name="health",
                systems=[
                    DiseaseSystem(
                        config=self.config,
                        relationship_engine=self.relationship_engine,
                    ),
                ],
            ),
            
            # ================================================================
            # FASE 7: REPRODUCCIÓN
            # ================================================================
            PhaseDefinition(
                name="reproduction",
                systems=[
                    ConceptionSystem(
                        config=self.config,
                        relationship_engine=self.relationship_engine,
                    ),
                    egg_system,  # OPCIÓN B.2: Procesar huevos ovíparos (incubación y eclosión)
                    GestationSystem(
                        config=self.config,
                        evolution_engine=evolution_engine,
                        relationship_engine=self.relationship_engine,
                    ),
                ],
            ),
            
            # ================================================================
            # FASE 8: MORTALIDAD
            # ================================================================
            PhaseDefinition(
                name="mortality",
                systems=[
                    MortalitySystem(
                        config=self.config,
                        relationship_engine=self.relationship_engine,
                        ancestry_queries=ancestry_queries,  # CORRECCIÓN: Para endogamia
                    ),
                    DeathResolver(self.config),
                ],
            ),
            
            # ================================================================
            # FASE 9: OBSERVADORES
            # ================================================================
            PhaseDefinition(
                name="observers",
                systems=[
                    genealogy_system,
                    MetricsSystem(
                        self.config, 
                        genealogy_system=genealogy_system,
                        ecology_system=ecological_system,  # Para métricas de ecología
                    ),
                    evolution_engine,
                ],
            ),
        ]

        self._validate_phases(phases)
        return phases

    def get_registered_system_names(self) -> list[str]:
        """Devuelve los nombres de sistemas registrados para análisis y logging."""
        names: list[str] = []
        for phase in self.build_phases():
            for system in phase.systems:
                names.append(system.__class__.__name__)
        return names

    def _validate_phases(self, phases: list[PhaseDefinition]) -> None:
        """Comprueba en tiempo de arranque que los sistemas cumplan el contrato Protocol.

        Args:
            phases: Fases a validar.

        Raises:
            TypeError: Si algún sistema no implementa el método `process`.
            ValueError: Si existe una fase anónima.
        """
        for phase in phases:
            if not phase.name:
                raise ValueError("Todas las fases deben tener un nombre estricto.")

            for system in phase.systems:
                process = getattr(system, "process", None)
                if not callable(process):
                    system_name = system.__class__.__name__
                    raise TypeError(
                        f"Fallo estructural: El sistema {system_name} no "
                        f"implementa el método requerido process(...)."
                    )