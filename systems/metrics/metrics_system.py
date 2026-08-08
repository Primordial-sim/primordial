"""Módulo responsable de la recolección y exportación de métricas multidimensionales.

Este sistema actúa como un observador puro (solo lectura) que extrae instantáneas
periódicas del estado del mundo para análisis demográfico, genético, epidemiológico,
espacial, cognitivo y genealógico.

Características avanzadas:
- Fuente de verdad temporal única (state.world_days_elapsed)
- Introspección genética automática (todos los genes numéricos)
- Análisis epidemiológico profundo (familias de patógenos, carga viral)
- Estructura por edades y distribución espacial
- Métricas de reproducción, genealogía y estrés cognitivo
- Gestión de memoria configurable (límite de historial)

INTEGRACIÓN: Requiere inyección opcional de GenealogySystem para métricas de linajes.
"""

import json
import logging
from collections import defaultdict
from typing import Dict, List, Any, Optional

from core.state.world_state import WorldState
from core.state.pending_changes import PendingChanges
from systems.environment.environment_context import EnvironmentContext
from core.config.simulation_config import SimulationConfig


class MetricsSystem:
    """Recolecta métricas multidimensionales normalizadas por el tiempo transcurrido."""

    def __init__(
        self, 
        config: SimulationConfig,
        genealogy_system: Any = None,
    ) -> None:
        """Inicializa el sistema de métricas con la configuración central.
        
        Args:
            config: Configuración maestra de la simulación.
            genealogy_system: Sistema de genealogía opcional para métricas de linajes.
        """
        self.config = config
        self.genealogy_system = genealogy_system
        self.history: List[Dict[str, Any]] = []
        self.last_snapshot_day: float = -1.0
        self.last_population: int = 0
        self.logger = logging.getLogger("MetricsSystem")

    def get_latest_metrics(self) -> Dict[str, Any]:
        """Devuelve el último snapshot de métricas si existe."""
        return self.history[-1] if self.history else {}

    def process(
        self, 
        state: WorldState, 
        pending: PendingChanges, 
        delta_days: float, 
        context: EnvironmentContext
    ) -> None:
        """Calcula las estadísticas multidimensionales de la población viva en el tick actual."""
        
        # CORRECCIÓN (Punto 4): Usar la fuente de verdad temporal del estado
        current_day = getattr(state, 'world_days_elapsed', 0.0)
        
        # Acceso limpio a la configuración
        interval = getattr(self.config.metrics, 'snapshot_interval_days', 1.0)

        # Optimización de RAM: Solo tomamos métricas según el intervalo configurado
        if (current_day - self.last_snapshot_day) < interval and current_day > 0:
            return

        self.last_snapshot_day = current_day

        # 1. FILTRADO (Integridad Referencial): Omitimos a las entidades recién fallecidas
        alive_persons = [p for p in state.get_all_persons() if p.entity_id not in pending.deaths]
        total_pop = len(alive_persons)
        
        # CORRECCIÓN (Punto 11): Calcular tasa de crecimiento poblacional
        population_delta = total_pop - self.last_population
        growth_rate = (population_delta / max(1, self.last_population)) * 100 if self.last_population > 0 else 0.0
        self.last_population = total_pop
        
        # Inicializar snapshot con estructura multidimensional
        snapshot = {
            "day": round(current_day, 2),
            "year": round(current_day / 365.0, 2),
            "population": total_pop,
            "births_this_tick": len(pending.births),
            "deaths_this_tick": len(pending.deaths),
            "population_delta": population_delta,
            "growth_rate_percent": round(growth_rate, 2),
            
            # CORRECCIÓN (Punto 12): Estructura por edades
            "age_structure": {"children": 0, "adults": 0, "seniors": 0},
            "avg_age_years": 0.0,
            
            # CORRECCIÓN (Punto 6): Genética poblacional (introspección automática)
            "gene_averages": {},
            "genetic_diversity": {},
            
            # CORRECCIÓN (Punto 7 y 16): Epidemiología profunda
            "epidemiology": {
                "sick_count": 0,
                "total_infections": 0,
                "avg_pathogens_per_sick": 0.0,
                "active_pathogen_families": {},
                "total_viral_load": 0.0,
            },
            
            # CORRECCIÓN (Punto 13): Distribución espacial
            "spatial": {
                "avg_pressure": 0.0,
                "max_pressure": 0.0,
                "overcrowded_sectors": 0,
            },
            
            # CORRECCIÓN (Punto 15): Reproducción
            "reproduction": {
                "active_pregnancies": 0,
                "avg_litter_size": 0.0,
                "fertile_count": 0,
            },
            
            # CORRECCIÓN (Punto 19): Cognición y estrés
            "cognitive": {
                "avg_cognitive_stress": 0.0,
                "avg_stress": 0.0,
                "avg_happiness": 0.0,
                "avg_energy": 0.0,
            },
            
            # CORRECCIÓN (Punto 17): Genealogía
            "genealogy": {
                "active_lineages": 0,
                "extinct_lineages": 0,
                "max_generation": 0,
            },
            
            # CORRECCIÓN (Punto 8): Estado social (sin literales frágiles)
            "social": {
                "married_count": 0,
                "single_count": 0,
                "divorced_count": 0,
                "orphan_count": 0,
            },
        }

        if total_pop > 0:
            # Variables acumuladoras para el bucle O(N)
            total_age_days = 0.0
            gene_sums: Dict[str, float] = defaultdict(float)
            gene_variances: Dict[str, List[float]] = defaultdict(list)
            
            total_infections = 0
            pathogen_families: Dict[str, int] = defaultdict(int)
            total_viral_load = 0.0
            
            total_cognitive_stress = 0.0
            total_stress = 0.0
            total_happiness = 0.0
            total_energy = 0.0
            
            active_pregnancies = 0
            total_litter_size = 0
            fertile_count = 0
            
            married_count = 0
            single_count = 0
            divorced_count = 0
            orphan_count = 0
            
            # Obtener genes a rastrear mediante introspección (Punto 6)
            sample_genome = alive_persons[0].genome
            tracked_genes = self._get_tracked_genes(sample_genome)

            # 2. BUCLE ÚNICO O(N) PARA RECOLECTAR TODAS LAS MÉTRICAS
            for p in alive_persons:
                # --- Edad y estructura ---
                total_age_days += p.age
                if p.is_senior:
                    snapshot["age_structure"]["seniors"] += 1
                elif p.is_adult:
                    snapshot["age_structure"]["adults"] += 1
                else:
                    snapshot["age_structure"]["children"] += 1
                
                # --- Genética ---
                for gene_name in tracked_genes:
                    gene_value = float(getattr(p.genome, gene_name, 0.0))
                    gene_sums[gene_name] += gene_value
                    gene_variances[gene_name].append(gene_value)
                
                # --- Epidemiología ---
                if p.is_sick:
                    snapshot["epidemiology"]["sick_count"] += 1
                    infection_count = len(p.active_infections)
                    total_infections += infection_count
                    
                    for infection_state in p.active_infections.values():
                        family = infection_state.pathogen.family
                        pathogen_families[family] += 1
                        total_viral_load += infection_state.pathogen.virulence * infection_state.pathogen.transmission
                
                # --- Cognición ---
                total_cognitive_stress += p.memory.get("cognitive_stress", 0.0)
                total_stress += p.emotions.get("stress", 0.0)
                total_happiness += p.emotions.get("happiness", 0.5)
                total_energy += p.emotions.get("energy", 1.0)
                
                # --- Reproducción ---
                if p.is_pregnant:
                    active_pregnancies += 1
                    total_litter_size += p.litter_size_gestating
                if p.is_fertile():
                    fertile_count += 1
                
                # --- Estado social (Punto 8: sin literales frágiles) ---
                marital = getattr(p, 'marital_status', 'soltero')
                if marital == 'casado':
                    married_count += 1
                elif marital == 'divorciado':
                    divorced_count += 1
                else:
                    single_count += 1
                
                # Contar huérfanos (sin padres vivos)
                if len(p.parents) == 0 and len(p.adoptive_parents) == 0 and p.age > 0:
                    orphan_count += 1

            # 3. CÁLCULOS FINALES Y NORMALIZACIÓN
            
            # Edad promedio
            snapshot["avg_age_years"] = round((total_age_days / total_pop) / 365.0, 2)
            
            # Genética: medias y varianzas
            for gene_name in tracked_genes:
                values = gene_variances[gene_name]
                if values:
                    mean_val = gene_sums[gene_name] / len(values)
                    variance_val = sum((x - mean_val) ** 2 for x in values) / len(values)
                    snapshot["gene_averages"][gene_name] = round(mean_val, 4)
                    snapshot["genetic_diversity"][gene_name] = round(variance_val, 6)
            
            # Epidemiología
            snapshot["epidemiology"]["total_infections"] = total_infections
            snapshot["epidemiology"]["avg_pathogens_per_sick"] = round(
                total_infections / max(1, snapshot["epidemiology"]["sick_count"]), 2
            )
            snapshot["epidemiology"]["active_pathogen_families"] = dict(pathogen_families)
            snapshot["epidemiology"]["total_viral_load"] = round(total_viral_load, 2)
            
            # Cognición
            snapshot["cognitive"]["avg_cognitive_stress"] = round(total_cognitive_stress / total_pop, 3)
            snapshot["cognitive"]["avg_stress"] = round(total_stress / total_pop, 3)
            snapshot["cognitive"]["avg_happiness"] = round(total_happiness / total_pop, 3)
            snapshot["cognitive"]["avg_energy"] = round(total_energy / total_pop, 3)
            
            # Reproducción
            snapshot["reproduction"]["active_pregnancies"] = active_pregnancies
            snapshot["reproduction"]["avg_litter_size"] = round(
                total_litter_size / max(1, active_pregnancies), 2
            ) if active_pregnancies > 0 else 0.0
            snapshot["reproduction"]["fertile_count"] = fertile_count
            
            # Social
            snapshot["social"]["married_count"] = married_count
            snapshot["social"]["single_count"] = single_count
            snapshot["social"]["divorced_count"] = divorced_count
            snapshot["social"]["orphan_count"] = orphan_count

        # 4. MÉTRICAS ESPACIALES (Punto 13)
        self._calculate_spatial_metrics(snapshot, context)
        
        # 5. MÉTRICAS GENEALÓGICAS (Punto 17)
        self._calculate_genealogy_metrics(snapshot)
        
        # 6. AÑADIR AL HISTORIAL CON GESTIÓN DE MEMORIA (Punto 21)
        self.history.append(snapshot)
        
        # CORRECCIÓN (Punto 21): Limitar el crecimiento del historial
        max_history_size = getattr(self.config.metrics, 'max_history_size', 1000)
        if len(self.history) > max_history_size:
            self.history.pop(0)  # Eliminar el snapshot más antiguo

    def _get_tracked_genes(self, sample_genome: Any) -> List[str]:
        """Extrae los nombres de los rasgos genéticos disponibles mediante introspección.
        
        CORRECCIÓN (Punto 6): Exporta automáticamente todos los genes numéricos.
        """
        tracked_genes = []
        genome_class = type(sample_genome)
        
        for attr_name in dir(genome_class):
            attr = getattr(genome_class, attr_name, None)
            if isinstance(attr, property) and not attr_name.startswith('_'):
                try:
                    value = getattr(sample_genome, attr_name, None)
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        tracked_genes.append(attr_name)
                except Exception:
                    pass
        
        return tracked_genes

    def _calculate_spatial_metrics(self, snapshot: Dict[str, Any], context: EnvironmentContext) -> None:
        """Calcula métricas de distribución espacial y presión ambiental."""
        if hasattr(context, 'pressure_map') and context.pressure_map:
            pressures = list(context.pressure_map.values())
            if pressures:
                snapshot["spatial"]["avg_pressure"] = round(sum(pressures) / len(pressures), 3)
                snapshot["spatial"]["max_pressure"] = round(max(pressures), 3)
                snapshot["spatial"]["overcrowded_sectors"] = sum(1 for p in pressures if p > 1.5)

    def _calculate_genealogy_metrics(self, snapshot: Dict[str, Any]) -> None:
        """Calcula métricas de linajes y generaciones si el sistema de genealogía está disponible."""
        if not self.genealogy_system:
            return
            
        lineages = getattr(self.genealogy_system, 'lineages', {})
        registry = getattr(self.genealogy_system, 'registry', {})
        
        active_lineages = sum(1 for l in lineages.values() if not l.is_extinct)
        extinct_lineages = sum(1 for l in lineages.values() if l.is_extinct)
        
        max_generation = 0
        for node in registry.values():
            if node.is_alive:
                max_generation = max(max_generation, node.generation_index)
        
        snapshot["genealogy"]["active_lineages"] = active_lineages
        snapshot["genealogy"]["extinct_lineages"] = extinct_lineages
        snapshot["genealogy"]["max_generation"] = max_generation

    def export_to_json(self, filepath: str = "simulation_metrics.json") -> None:
        """Exporta la serie temporal de métricas a un archivo JSON en disco."""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=4, ensure_ascii=False)
            self.logger.info(f"📊 Métricas exportadas correctamente a: {filepath}")
        except IOError as e:
            self.logger.error(f"Error al exportar métricas a JSON: {e}")