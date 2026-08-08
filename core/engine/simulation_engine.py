"""Motor temporal principal de la simulación con soporte de persistencia."""

from __future__ import annotations

import csv
import json
import logging
import math
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
from entities.person.allele import Allele, Gene
from entities.person.genome import Genome
from entities.person.person import Person

from systems.relationships.relationship_experience_engine import RelationshipExperienceEngine


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
        max_ticks: Optional[int] = None,        # NUEVO
        export_path: Optional[str] = None,       # NUEVO
        snapshot_interval: Optional[int] = None, # NUEVO
    ) -> None:
        self.state = world_state
        self.config = config
        self.pipeline = pipeline
        self.tick_manager = tick_manager
        self.snapshot_manager = snapshot_manager
        self.event_bus = event_bus
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # NUEVO: Parámetros de control de ejecución
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
        max_ticks: Optional[int] = None,        # NUEVO
        export_path: Optional[str] = None,       # NUEVO
        snapshot_interval: Optional[int] = None, # NUEVO
        event_bus: Any = None,
    ) -> SimulationEngine:
        """Crea un motor completo usando la configuración por defecto.
        
        NUEVO: Parámetros adicionales para control de ejecución:
            max_ticks: Número máximo de ticks a ejecutar (None = hasta total_days)
            export_path: Ruta para exportar métricas JSON al finalizar
            snapshot_interval: Intervalo en días para snapshots de métricas
        """
        config = SimulationConfig()
        if config_path:
            cls._load_external_config(config, config_path)

        # NUEVO: Aplicar snapshot_interval a la configuración de métricas si se especifica
        if snapshot_interval is not None:
            if hasattr(config, 'metrics'):
                config.metrics.snapshot_interval_days = snapshot_interval

        state = WorldState(config=config, width=width, height=height)
        cls._generate_founding_population(
            config=config, state=state, size=founding_population_size,
        )

        # 1. Instanciar motores especializados
        relationship_experience_engine = RelationshipExperienceEngine(config)
        tick_manager = TickManager(initial_days_per_tick=config.engine.delta_days)
        snapshot_manager = SnapshotManager()

        # 2. Inyectar dependencias en el Scheduler
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
            max_ticks=max_ticks,           # NUEVO
            export_path=export_path,        # NUEVO
            snapshot_interval=snapshot_interval, # NUEVO
        )

    def run(self) -> None:
        """Ejecuta la simulación completa gestionada por TickManager.
        
        NUEVO: Condiciones de parada:
        1. total_days alcanzado (config.engine.total_days)
        2. max_ticks alcanzado (si se especificó)
        3. Población extinta
        4. Interrupción manual (Ctrl+C)
        """
        total_days = float(self.config.engine.total_days)
        history: list[dict[str, Any]] = []

        # NUEVO: Localizar MetricsSystem para exportación final
        metrics_system = self._find_metrics_system()

        self.logger.info(
            "Iniciando simulación: %s días totales, %s días/tick.",
            total_days, self.tick_manager.days_per_tick,
        )
        if self.max_ticks is not None:
            self.logger.info("🎯 Parada por máximo de ticks: %d", self.max_ticks)
        if self.export_path:
            self.logger.info("📊 Exportación final a: %s", self.export_path)

        # Bucle controlado por TickManager
        try:
            while self.tick_manager.total_simulated_days < total_days:
                # NUEVO: Condición de parada por max_ticks
                if self.max_ticks is not None and self.tick_manager.current_tick >= self.max_ticks:
                    self.logger.info(
                        "🏁 Parada por límite de ticks: %d ejecutados", 
                        self.max_ticks
                    )
                    break
                
                delta_days = self.tick_manager.advance_tick()
                current_tick = self.tick_manager.current_tick
                current_day = self.tick_manager.total_simulated_days

                # Sincronizar el estado del mundo con el TickManager
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
                
                # NUEVO: Condición de parada por población extinta
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
        
        # # NUEVO: Exportar métricas JSON si se configuró
        # if self.export_path and metrics_system:
        #     self._export_metrics_json(metrics_system)
        
        self.logger.info("Simulación finalizada correctamente.")

    def _find_metrics_system(self) -> Optional[Any]:
        """NUEVO: Localiza el MetricsSystem dentro del pipeline para exportación."""
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
        """NUEVO: Exporta las métricas acumuladas a JSON."""
        try:
            if hasattr(metrics_system, 'export_to_json'):
                metrics_system.export_to_json(self.export_path)
                self.logger.info("📊 Métricas JSON exportadas a: %s", self.export_path)
            else:
                self.logger.warning(
                    "⚠️  MetricsSystem no tiene método export_to_json, "
                    "no se pueden exportar métricas JSON"
                )
        except Exception as e:
            self.logger.error("❌ Error al exportar métricas JSON: %s", e)

    def export_metrics(self, filepath: str) -> None:
        """Método público para exportar métricas manualmente.
        
        Útil cuando la simulación se interrumpe con Ctrl+C desde el launcher.
        
        Args:
            filepath: Ruta del archivo JSON donde exportar las métricas.
        """
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
            
            # Restaurar estado interno del motor
            self.state = loaded_state
            self.tick_manager.load_from_snapshot(loaded_tick, loaded_days)
            self.tick_manager.set_tick_duration(loaded_scale)
            
            # Recrear el pipeline con el estado cargado (necesario para inyecciones)
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
        logger = logging.getLogger("SimulationEngine")
        logger.info("Generando %s agentes fundadores (solteros).", size)

        min_age = config.time.adult_age_days
        max_age = config.time.senior_age_days

        for entity_id in range(1, size + 1):
            base_fertility = random.uniform(0.5, 0.9)
            base_sociability = random.uniform(0.1, 0.9)
            base_temperament = random.uniform(0.1, 0.9)
            base_immunity = random.uniform(0.4, 0.8)

            genome = Genome(
                fertility=Gene(allele_a=Allele.create_random(base_fertility, 0.1), allele_b=Allele.create_random(base_fertility, 0.1)),
                sociability=Gene(allele_a=Allele.create_random(base_sociability, 0.1), allele_b=Allele.create_random(base_sociability, 0.1)),
                temperament=Gene(allele_a=Allele.create_random(base_temperament, 0.1), allele_b=Allele.create_random(base_temperament, 0.1)),
                immunity=Gene(allele_a=Allele.create_random(base_immunity, 0.1), allele_b=Allele.create_random(base_immunity, 0.1)),
                species_baseline="human"
            )

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