"""Motor temporal principal de la simulación con soporte de persistencia."""

from __future__ import annotations

import csv
import json
import logging
import os
import random
from datetime import datetime
from typing import Any, Optional, List

from core.config.simulation_config import SimulationConfig
from core.engine.phase_scheduler import PhaseScheduler
from core.execution.execution_pipeline import ExecutionPipeline
from core.engine.tick_manager import TickManager
from core.engine.snapshot_manager import SnapshotManager
from core.state.world_state import WorldState
from entities.person.genome import Genome
from entities.person.person import Person

from systems.relationships.relationship_experience_engine import RelationshipExperienceEngine

# GENÉTICA UNIVERSAL
from core.genetics.species_definition import SpeciesRegistry

# SISTEMA DE ESCENARIOS
from core.engine.scenario_loader import Scenario, SpeciesConfig



class SimulationEngine:
    """Controla el ciclo temporal completo, el registro analítico y la persistencia."""

    def __init__(
        self,
        world_state: WorldState,
        config: SimulationConfig,
        pipeline: ExecutionPipeline,
        tick_manager: TickManager,
        snapshot_manager: SnapshotManager,
        event_bus: Any = None,
        max_ticks: Optional[int] = None,
        export_path: Optional[str] = None,
        snapshot_interval: Optional[int] = None,
    ) -> None:
        self.state = world_state
        self.config = config
        self.pipeline = pipeline
        self.tick_manager = tick_manager
        self.snapshot_manager = snapshot_manager
        self.event_bus = event_bus
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.max_ticks = max_ticks
        self.export_path = export_path
        self.snapshot_interval = snapshot_interval
        
        self._total_deaths: int = 0
        self._total_births: int = 0
        self._total_infections: int = 0

    @classmethod
    def create_default(
        cls,
        config_path: Optional[str] = None,
        width: int = 100,
        height: int = 100,
        founding_population_size: int = 50,
        max_ticks: Optional[int] = None,
        export_path: Optional[str] = None,
        snapshot_interval: Optional[int] = None,
        event_bus: Any = None,
    ) -> SimulationEngine:
        """Crea un motor completo usando la configuración por defecto."""
        config = SimulationConfig()
        if config_path:
            cls._load_external_config(config, config_path)

        if snapshot_interval is not None:
            if hasattr(config, 'metrics'):
                config.metrics.snapshot_interval_days = snapshot_interval

        state = WorldState(config=config, width=width, height=height)
        state.initialize_tile_map()

        cls._generate_founding_population(
            config=config, state=state, size=founding_population_size,
        )

        # FASE C: Construir el mapa de ocupación inicial
        state.rebuild_occupancy_map()

        relationship_experience_engine = RelationshipExperienceEngine(config)
        tick_manager = TickManager(initial_days_per_tick=config.engine.delta_days)
        snapshot_manager = SnapshotManager()

        scheduler = PhaseScheduler(
            config=config, 
            event_bus=event_bus,
            relationship_engine=relationship_experience_engine,
        )
        
        pipeline = ExecutionPipeline(
            config=config,
            phases=scheduler.build_phases(),
        )

        return cls(
            world_state=state,
            config=config,
            pipeline=pipeline,
            tick_manager=tick_manager,
            snapshot_manager=snapshot_manager,
            event_bus=event_bus,
            max_ticks=max_ticks,
            export_path=export_path,
            snapshot_interval=snapshot_interval,
        )

    @classmethod
    def create_from_scenario(
        cls,
        scenario: Scenario,
        config_path: Optional[str] = None,
        export_path: Optional[str] = None,
        event_bus: Any = None,
    ) -> SimulationEngine:
        """Crea un motor completo a partir de un escenario definido.
        
        Args:
            scenario: Escenario cargado con ScenarioLoader.
            config_path: Ruta a configuración externa (opcional).
            export_path: Ruta de exportación de métricas (opcional).
            event_bus: Bus de eventos (opcional).
            
        Returns:
            SimulationEngine configurado con el escenario.
        """
        config = SimulationConfig()
        if config_path:
            cls._load_external_config(config, config_path)
        
        # Aplicar parámetros del escenario a la config
        config.engine.delta_days = scenario.simulation.delta_days
        config.engine.total_days = scenario.simulation.total_days
        config.environment.sector_size = scenario.environment.sector_size
        
        state = WorldState(
            config=config,
            width=scenario.world.width,
            height=scenario.world.height,
        )

        # NUEVO: Inicializar mapa de tiles
        state.initialize_tile_map()
        
        # Generar población fundadora multiespecie
        cls._generate_multispecies_population(
            config=config,
            state=state,
            species_configs=scenario.species,
        )
        
        state.rebuild_occupancy_map()
        
        relationship_experience_engine = RelationshipExperienceEngine(config)
        tick_manager = TickManager(initial_days_per_tick=config.engine.delta_days)
        snapshot_manager = SnapshotManager()
        
        scheduler = PhaseScheduler(
            config=config,
            event_bus=event_bus,
            relationship_engine=relationship_experience_engine,
        )
        
        pipeline = ExecutionPipeline(
            config=config,
            phases=scheduler.build_phases(),
        )
        
        return cls(
            world_state=state,
            config=config,
            pipeline=pipeline,
            tick_manager=tick_manager,
            snapshot_manager=snapshot_manager,
            event_bus=event_bus,
            max_ticks=scenario.simulation.max_ticks,
            export_path=export_path,
        )

    def run(self) -> None:
        """Ejecuta la simulación completa gestionada por TickManager."""
        total_days = float(self.config.engine.total_days)
        history: list[dict[str, Any]] = []

        self.logger.info(
            "Iniciando simulación: %s días totales, %s días/tick.",
            total_days, self.tick_manager.days_per_tick,
        )
        if self.max_ticks is not None:
            self.logger.info("🎯 Parada por máximo de ticks: %d", self.max_ticks)
        if self.export_path:
            self.logger.info("📊 Exportación final a: %s", self.export_path)

        try:
            while self.tick_manager.total_simulated_days < total_days:
                if self.max_ticks is not None and self.tick_manager.current_tick >= self.max_ticks:
                    self.logger.info(
                        "🏁 Parada por límite de ticks: %d ejecutados", 
                        self.max_ticks
                    )
                    break
                
                delta_days = self.tick_manager.advance_tick()
                current_tick = self.tick_manager.current_tick
                current_day = self.tick_manager.total_simulated_days

                self.state.world_days_elapsed = current_day

                pending = self.pipeline.execute_tick(
                    state=self.state,
                    delta_days=delta_days,
                    current_tick=current_tick,
                    current_day=current_day,
                    event_bus=self.event_bus,
                )
                
                self._log_visual_events(pending, current_tick)
                self._total_deaths += len(pending.deaths)
                self._total_births += len(pending.births)
                self._total_infections += len(pending.infections)

                self.state.apply_commit(
                    pending,
                    event_bus=self.event_bus,
                    current_tick=current_tick,
                )

                persons = list(self.state.get_all_persons())
                
                if len(persons) == 0 and current_tick > 1:
                    self.logger.warning("⚠️  Población extinta. Fin de la simulación.")
                    history.append({
                        "tick": current_tick,
                        "day": round(current_day, 2),
                        "alive": 0,
                        "sick": 0,
                        "cumulative_deaths": self._total_deaths,
                        "cumulative_births": self._total_births
                    })
                    break
                
                history.append({
                    "tick": current_tick,
                    "day": round(current_day, 2),
                    "alive": len(persons),
                    "sick": sum(1 for p in persons if getattr(p, "is_sick", False)),
                    "cumulative_deaths": self._total_deaths,
                    "cumulative_births": self._total_births
                })

        except KeyboardInterrupt:
            self.logger.warning(
                "\n⚠️  Simulación interrumpida por el usuario (Ctrl+C) en tick %d",
                self.tick_manager.current_tick,
            )

        self._print_simulation_summary(self.tick_manager.current_tick)
        self._export_to_csv(history)
        
        self.logger.info("Simulación finalizada correctamente.")

    # =========================================================================
    # MÉTODOS PARA VISUALIZACIÓN EN TIEMPO REAL
    # =========================================================================

    def initialize(self) -> None:
        """Inicializa la simulación para visualización en tiempo real.
        
        No ejecuta ningún tick. Solo prepara el estado inicial.
        Debe llamarse antes de step().
        """
        self._total_deaths = 0
        self._total_births = 0
        self._total_infections = 0
        
        # FASE C: Reconstruir el mapa de ocupación
        self.state.rebuild_occupancy_map()
        
        self.logger.info(
            "🎬 Simulación inicializada para visualización: %d agentes, mundo %dx%d",
            len(self.state.get_all_persons()),
            self.state.width,
            self.state.height,
        )

    def step(self) -> dict[str, Any]:
        """Ejecuta un solo tick de la simulación para visualización en tiempo real.
        
        Debe llamarse después de initialize().
        
        Returns:
            Diccionario con el estado actual para enviar a Godot.
        """
        delta_days = self.tick_manager.advance_tick()
        current_tick = self.tick_manager.current_tick
        current_day = self.tick_manager.total_simulated_days

        self.state.world_days_elapsed = current_day

        pending = self.pipeline.execute_tick(
            state=self.state,
            delta_days=delta_days,
            current_tick=current_tick,
            current_day=current_day,
            event_bus=self.event_bus,
        )
        
        self._total_deaths += len(pending.deaths)
        self._total_births += len(pending.births)
        self._total_infections += len(pending.infections)

        self.state.apply_commit(
            pending,
            event_bus=self.event_bus,
            current_tick=current_tick,
        )

        return self.get_visualization_state()

    def get_visualization_state(self) -> dict[str, Any]:
        """Obtiene el estado actual en formato compatible con Godot."""
        persons = list(self.state.get_all_persons())
        persons_data = []
        
        for person in persons:
            persons_data.append({
                "id": int(person.entity_id),
                "x": float(person.x),
                "y": float(person.y),
                "age": float(person.age),
                "gender": str(person.gender),
                "species": str(getattr(person, 'species', 'human')),
                "is_sick": bool(person.is_sick),
                "is_adult": bool(person.is_adult),
                "is_senior": bool(person.is_senior),
                "is_pregnant": bool(person.is_pregnant),
            })
        
        sick_count = sum(1 for p in persons if p.is_sick)
        adult_count = sum(1 for p in persons if p.is_adult)
        senior_count = sum(1 for p in persons if p.is_senior)
        
        # Contar por especie
        species_counts = {}
        for p in persons:
            sp = getattr(p, 'species', 'human')
            species_counts[sp] = species_counts.get(sp, 0) + 1
        
        return {
            "type": "tick",
            "tick": int(self.tick_manager.current_tick),
            "day": float(self.tick_manager.total_simulated_days),
            "world_width": int(self.state.width),
            "world_height": int(self.state.height),
            "agents": persons_data,
            "stats": {
                "total_population": len(persons),
                "total_deaths": self._total_deaths,
                "total_births": self._total_births,
                "total_infections": self._total_infections,
                "sick_count": sick_count,
                "adult_count": adult_count,
                "senior_count": senior_count,
                "species_counts": species_counts,
            },
        }

    # =========================================================================
    # MÉTODOS AUXILIARES
    # =========================================================================

    def _find_metrics_system(self) -> Optional[Any]:
        """Localiza el MetricsSystem dentro del pipeline para exportación."""
        try:
            if not hasattr(self.pipeline, 'phases'):
                return None
            for phase in self.pipeline.phases:
                for system in phase.systems:
                    if system.__class__.__name__ == "MetricsSystem":
                        return system
        except Exception as e:
            self.logger.debug(f"No se pudo localizar MetricsSystem: {e}")
        return None

    def _export_metrics_json(self, metrics_system: Any) -> None:
        """Exporta las métricas acumuladas a JSON."""
        try:
            if hasattr(metrics_system, 'export_to_json'):
                metrics_system.export_to_json(self.export_path)
                self.logger.info("📊 Métricas JSON exportadas a: %s", self.export_path)
            else:
                self.logger.warning(
                    "⚠️  MetricsSystem no tiene método export_to_json"
                )
        except Exception as e:
            self.logger.error("❌ Error al exportar métricas JSON: %s", e)

    def export_metrics(self, filepath: str) -> None:
        """Método público para exportar métricas manualmente."""
        metrics_system = self._find_metrics_system()
        if metrics_system:
            self._export_metrics_json(metrics_system)
        else:
            self.logger.warning(
                "⚠️  No se pudo exportar métricas: MetricsSystem no encontrado"
            )

    def save_game(self, filepath: str) -> bool:
        """Guarda el estado actual de la simulación en un archivo."""
        return self.snapshot_manager.create_snapshot(
            state=self.state,
            tick_manager=self.tick_manager,
            filepath=filepath,
        )

    def load_game(self, filepath: str) -> bool:
        """Carga un estado guardado de la simulación."""
        try:
            loaded_state, loaded_tick, loaded_days, loaded_scale = self.snapshot_manager.load_snapshot(filepath)
            
            self.state = loaded_state
            self.tick_manager.load_from_snapshot(loaded_tick, loaded_days)
            self.tick_manager.set_tick_duration(loaded_scale)
            
            relationship_experience_engine = RelationshipExperienceEngine(self.config)
            scheduler = PhaseScheduler(
                config=self.config, 
                event_bus=self.event_bus,
                relationship_engine=relationship_experience_engine,
            )
            self.pipeline = ExecutionPipeline(
                config=self.config,
                phases=scheduler.build_phases(),
            )
            
            # FASE C: Reconstruir el mapa de ocupación tras cargar
            self.state.rebuild_occupancy_map()
            
            self.logger.info("✅ Partida cargada exitosamente desde: %s", filepath)
            return True
        except Exception as e:
            self.logger.error("❌ Fallo al cargar la partida: %s", e)
            return False

    def _log_visual_events(self, pending: Any, tick: int) -> None:
        for data in pending.births:
            mother_id = data.get("mother_id", "Desconocida")
            self.logger.info("👶 [NACIMIENTO] Madre %s dio a luz (Tick: %s).", mother_id, tick)
            
        for entity_id, reason in pending.deaths.items():
            self.logger.info("⚰️ [MUERTE] Agente %s falleció. Causa: %s", entity_id, reason)
            
        for entity_id, pathogen in pending.infections:
            pathogen_id = getattr(pathogen, "pathogen_id", "Desconocido")
            self.logger.info("🤒 [CONTAGIO] Agente %s contrajo %s", entity_id, pathogen_id)

    def _print_simulation_summary(self, total_ticks: int) -> None:
        persons = list(self.state.get_all_persons())
        total_alive = len(persons)
        sick_count = sum(1 for p in persons if getattr(p, "is_sick", False))
        avg_age_years = (sum(p.age for p in persons) / total_alive / 365.0) if total_alive > 0 else 0.0

        self.logger.info("\n" + "=" * 65)
        self.logger.info("📊 RESUMEN EJECUTIVO DE LA SIMULACIÓN")
        self.logger.info("=" * 65)
        self.logger.info(f"{'Métrica':<30} | {'Valor':<10}")
        self.logger.info("-" * 45)
        self.logger.info(f"{'Población Viva Final':<30} | {total_alive:<10}")
        self.logger.info(f"{'Edad Media (Años)':<30} | {avg_age_years:<10.1f}")
        self.logger.info(f"{'Total de Nacimientos Históricos':<30} | {self._total_births:<10}")
        self.logger.info(f"{'Total de Muertes Históricas':<30} | {self._total_deaths:<10}")
        self.logger.info(f"{'Infectados Activos (Fin)':<30} | {sick_count:<10}")
        self.logger.info(f"{'Total Contagios Históricos':<30} | {self._total_infections:<10}")
        self.logger.info(f"{'Ticks Ejecutados':<30} | {total_ticks:<10}")
        self.logger.info("=" * 65 + "\n")

    def _export_to_csv(self, history: list[dict[str, Any]]) -> None:
        if not history:
            return
        filename = f"reporte_simulacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        keys = history[0].keys()
        try:
            with open(filename, "w", newline="", encoding="utf-8") as output_file:
                dict_writer = csv.DictWriter(output_file, fieldnames=keys)
                dict_writer.writeheader()
                dict_writer.writerows(history)
            self.logger.info("💾 Reporte de datos exportado a: %s", filename)
        except OSError as e:
            self.logger.error("Error al exportar el CSV: %s", e)

    @staticmethod
    def _load_external_config(config: SimulationConfig, filepath: str) -> None:
        logger = logging.getLogger("SimulationEngine")
        if not os.path.exists(filepath):
            logger.warning("Archivo de configuración no encontrado: %s.", filepath)
            return
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
        for category, params in data.items():
            if not isinstance(params, dict):
                logger.warning("Se ignora una sección de configuración inválida: %s.", category)
                continue
            for key, value in params.items():
                config.set_parameter(category, key, value)

    @staticmethod
    def _generate_founding_population(config: SimulationConfig, state: WorldState, size: int) -> None:
        """Genera la población fundadora usando el sistema de Genética Universal."""
        logger = logging.getLogger("SimulationEngine")
        logger.info("Generando %s agentes fundadores (solteros).", size)

        # GENÉTICA UNIVERSAL: Inicializar el sistema de especies
        SpeciesRegistry.initialize_defaults()
        
        # Obtener la especie por defecto (humano por ahora)
        species = SpeciesRegistry.get("human")
        if species is None:
            logger.error("❌ Especie 'human' no encontrada en SpeciesRegistry")
            return
        
        logger.info("🧬 Usando especie: %s (%d rasgos)", species.name, species.get_trait_count())

        min_age = config.time.adult_age_days
        max_age = config.time.senior_age_days

        for entity_id in range(1, size + 1):
            # GENÉTICA UNIVERSAL: Crear genoma desde la SpeciesDefinition
            genome = Genome.create_founder(species)

            person = Person(
                config=config,
                entity_id=entity_id,
                x=random.randint(10, 90),
                y=random.randint(10, 90),
                age=random.uniform(min_age, max_age),
                genome=genome,
            )
            person.set_health_state("sano")
            person.update_pregnancy(False, 0.0)
            state.add_person(person)

    @staticmethod
    def _generate_multispecies_population(
        config: SimulationConfig,
        state: WorldState,
        species_configs: List[SpeciesConfig],
    ) -> None:
        """Genera una población fundadora con múltiples especies.
        
        Args:
            config: Configuración de simulación.
            state: Estado del mundo.
            species_configs: Lista de SpeciesConfig del escenario.
        """
        logger = logging.getLogger("SimulationEngine")
        
        SpeciesRegistry.initialize_defaults()
        
        total_count = sum(sc.count for sc in species_configs)
        logger.info("Generando población multiespecie: %d agentes totales", total_count)
        
        entity_id = 1
        min_age = config.time.adult_age_days
        max_age = config.time.senior_age_days
        width = state.width
        height = state.height
        
        for sc in species_configs:
            species = SpeciesRegistry.get(sc.species_id)
            if species is None:
                logger.error("❌ Especie '%s' no encontrada en SpeciesRegistry", sc.species_id)
                continue
            
            logger.info(
                "🧬 %s (%s): %d individuos, %d rasgos",
                species.name, species.archetype, sc.count, species.get_trait_count()
            )
            
            for _ in range(sc.count):
                genome = Genome.create_founder(species)
                
                person = Person(
                    config=config,
                    entity_id=entity_id,
                    x=random.randint(5, max(6, width - 5)),
                    y=random.randint(5, max(6, height - 5)),
                    age=random.uniform(min_age, max_age),
                    genome=genome,
                    species=species.species_id,
                )
                person.set_health_state("sano")
                person.update_pregnancy(False, 0.0)
                state.add_person(person)
                
                entity_id += 1