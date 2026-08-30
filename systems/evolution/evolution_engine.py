"""Módulo analítico responsable de monitorear la macroevolución del ecosistema.

Este módulo actúa como un observador puro (solo lectura) que extrae instantáneas
del genoma poblacional para análisis evolutivo. No modifica el estado de los
agentes, sino que calcula métricas de diversidad genética, presión de selección,
correlaciones entre genes, y análisis de causas de muerte y enfermedades.

Características avanzadas:
- Análisis de diversidad genética mediante varianza (no media+varianza)
- Diferencial de selección ponderado por descendencia total viva (no solo hijos)
- Correlaciones entre genes para detectar patrones emergentes
- Análisis de causas de muerte y su correlación con genotipos
- Análisis de selección sobre inmunidad y enfermedades
- Snapshots extraordinarios ante eventos drásticos (cuellos de botella)

Integra con el sistema de genealogía para rastrear generaciones y linajes,
y con el sistema de genoma para analizar la distribución de rasgos fenotípicos.
"""

import logging
import json
import math
from typing import Dict, Any, List
from core.state.world_state import WorldState
from core.state.pending_changes import PendingChanges
from systems.environment.environment_context import EnvironmentContext
from core.config.simulation_config import SimulationConfig


class EvolutionEngine:
    """Calcula métricas evolutivas avanzadas y rastrea las presiones de selección.
    
    Actúa como un observador puro (solo lectura). No modifica el estado de los
    agentes, sino que extrae instantáneas del genoma poblacional para su análisis.
    
    Atributos:
        config: Configuración centralizada de la simulación.
        ancestry_queries: Servicio de consultas genealógicas para rastrear linajes.
        last_snapshot_time: Timestamp del último snapshot genético.
        history: Historial de snapshots evolutivos para análisis temporal.
        death_history: Historial persistente de muertes entre snapshots.
        last_population_size: Tamaño poblacional del último snapshot (para detectar cuellos de botella).
    """

    def __init__(self, config: SimulationConfig, ancestry_queries: Any = None) -> None:
        """Inicializa el motor analítico con la configuración centralizada.
        
        Args:
            config: Configuración maestra de la simulación.
            ancestry_queries: Servicio de consultas genealógicas (opcional).
        """
        self.config = config
        self.ancestry_queries = ancestry_queries
        self.logger = logging.getLogger("EvolutionEngine")
        
        self.last_snapshot_time: float = 0.0
        self.last_population_size: int = 0
        
        # El motor es dueño de su propio historial, aislando la analítica del WorldState
        self.history: List[Dict[str, Any]] = []
        
        # Historial persistente de muertes entre snapshots
        self.death_history: List[Dict[str, Any]] = []

    def process(
        self,
        state: WorldState,
        pending: PendingChanges,
        delta_days: float,
        context: EnvironmentContext,
    ) -> None:
        """Recolecta instantáneas (snapshots) genéticas a intervalos regulares.
        
        Este método se ejecuta en cada tick pero solo procesa datos cuando ha
        transcurrido el intervalo configurado en evolution.snapshot_interval_days,
        O cuando se detecta un evento drástico (cuello de botella poblacional).
        
        Args:
            state: Estado autoritativo del mundo.
            pending: Búfer transaccional de cambios pendientes.
            delta_days: Fracción de tiempo simulado en este tick.
            context: Contexto ambiental actual (no usado en este sistema).
        """
        evo_cfg = self.config.evolution
        
        # Acumular muertes en el historial persistente
        self._accumulate_deaths(pending, state)
        
        # Filtramos la población activa garantizando la integridad referencial
        vivos = [p for p in state.get_all_persons() if p.entity_id not in pending.deaths]
        if not vivos:
            return

        current_time = getattr(state, 'world_days_elapsed', 0.0)
        current_population = len(vivos)
        
        # Detectar eventos drásticos (cuellos de botella o mortalidad masiva)
        is_drastic_event = self._detect_drastic_event(current_population)
        
        # Disparamos el análisis genético si ha transcurrido el intervalo configurado
        # O si hay un evento drástico (snapshot extraordinario)
        should_snapshot = (
            current_time == 0.0 or 
            (current_time - self.last_snapshot_time) >= evo_cfg.snapshot_interval_days or
            is_drastic_event
        )
        
        if should_snapshot:
            # Cálculos generacionales básicos usando el registro genealógico
            generaciones = self._get_generations(vivos)
            avg_generation = sum(generaciones) / len(generaciones) if generaciones else 0.0
            max_generation = max(generaciones) if generaciones else 0
            min_generation = min(generaciones) if generaciones else 0

            # Computamos la instantánea analítica
            snapshot = self._compute_genetic_snapshot(
                state=state,
                vivos=vivos,
                avg_gen=avg_generation,
                max_gen=max_generation,
                min_gen=min_generation,
                current_time=current_time,
                is_drastic=is_drastic_event
            )
            
            # Guardamos la instantánea en el almacén local del motor
            self.history.append(snapshot)
            self.last_snapshot_time = current_time
            self.last_population_size = current_population
            
            # Limpiamos el historial de muertes después de procesarlo
            self.death_history.clear()
            
            # Imprimimos el log para la consola
            self._log_evolutionary_insights(snapshot)

    def _accumulate_deaths(self, pending: PendingChanges, state: WorldState) -> None:
        """Acumula muertes en el historial persistente entre snapshots.
        
        Extrae las causas de muerte del búfer transaccional y las almacena
        junto con el genoma del fallecido para análisis evolutivo posterior.
        
        Args:
            pending: Búfer transaccional con muertes del tick actual.
            state: Estado autoritativo del mundo.
        """
        for entity_id, reason in pending.deaths.items():
            person = state.get_person(entity_id)
            if person and hasattr(person, 'genome'):
                # Extraer genes del fallecido
                genome_data = {}
                nombres_genes = self._get_tracked_genes(person.genome)
                for gen in nombres_genes:
                    genome_data[gen] = float(getattr(person.genome, gen, 0.0))
                
                # Extraer información de enfermedades activas
                diseases = []
                if hasattr(person, 'active_infections'):
                    for infection_state in person.active_infections.values():
                        diseases.append({
                            'family': infection_state.pathogen.family,
                            'virulence': infection_state.pathogen.virulence,
                            'lethality': infection_state.pathogen.lethality
                        })
                
                self.death_history.append({
                    'entity_id': entity_id,
                    'reason': reason,
                    'genome': genome_data,
                    'age': person.age,
                    'diseases': diseases
                })

    def _detect_drastic_event(self, current_population: int) -> bool:
        """Detecta eventos drásticos que requieren snapshot extraordinario.
        
        Un evento se considera drástico si:
        - La población cayó más del 20% desde el último snapshot
        - Hay más de 10 muertes en el historial acumulado
        
        Args:
            current_population: Tamaño poblacional actual.
            
        Returns:
            True si se detecta un evento drástico, False en caso contrario.
        """
        if self.last_population_size == 0:
            return False
        
        # Cuello de botella: caída >20%
        population_drop = (self.last_population_size - current_population) / self.last_population_size
        if population_drop > 0.20:
            self.logger.warning(
                f"⚠️ CUELLO DE BOTELLA DETECTADO: Población cayó {population_drop*100:.1f}% "
                f"({self.last_population_size} → {current_population})"
            )
            return True
        
        # Mortalidad masiva: >10 muertes entre snapshots
        if len(self.death_history) > 10:
            self.logger.warning(
                f"⚠️ MORTALIDAD MASIVA DETECTADA: {len(self.death_history)} muertes entre snapshots"
            )
            return True
        
        return False

    def _get_generations(self, vivos: List[Any]) -> List[int]:
        """Obtiene la generación de cada individuo vivo desde el registro genealógico.
        
        Args:
            vivos: Lista de personas vivas.
            
        Returns:
            Lista de índices de generación para cada persona viva.
        """
        if not self.ancestry_queries:
            return [0] * len(vivos)
        
        genealogy = getattr(self.ancestry_queries, '_genealogy', None)
        if not genealogy:
            return [0] * len(vivos)
        
        registry = getattr(genealogy, 'registry', {})
        generaciones = []
        
        for person in vivos:
            node = registry.get(person.entity_id)
            if node:
                generaciones.append(getattr(node, 'generation_index', 0))
            else:
                generaciones.append(0)
        
        return generaciones

    def _get_tracked_genes(self, sample_genome: Any) -> List[str]:
        """Extrae los nombres de los rasgos genéticos disponibles para rastrear.
        
        Inspecciona las properties públicas del Genome que representan rasgos
        fenotípicos heredables y devuelven valores numéricos. Esto permite que
        el sistema se adapte automáticamente si se añaden nuevos genes al Genome.
        
        Args:
            sample_genome: Instancia de Genome de cualquier individuo vivo.
            
        Returns:
            Lista de nombres de genes (properties) que devuelven valores numéricos.
        """
        tracked_genes = []
        
        # Inspeccionamos la clase para encontrar properties
        genome_class = type(sample_genome)
        for attr_name in dir(genome_class):
            attr = getattr(genome_class, attr_name, None)
            # Es una property si es instancia de property y no empieza con _
            if isinstance(attr, property) and not attr_name.startswith('_'):
                # Verificar que el valor devuelto sea numérico (no string, no bool)
                try:
                    value = getattr(sample_genome, attr_name, None)
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        tracked_genes.append(attr_name)
                except Exception:
                    # Si hay algún error al acceder, ignorar esta property
                    pass
        
        return tracked_genes

    def _compute_genetic_snapshot(
        self,
        state: WorldState,
        vivos: List[Any],
        avg_gen: float,
        max_gen: int,
        min_gen: int,
        current_time: float,
        is_drastic: bool = False
    ) -> Dict[str, Any]:
        """Realiza un escaneo profundo de la diversidad genética y éxito reproductivo.
        
        Analiza la distribución de rasgos genéticos en la población viva, calcula
        diferenciales de selección (presión evolutiva), correlaciones entre genes,
        y análisis de causas de muerte y enfermedades.
        
        Args:
            state: Estado autoritativo del mundo.
            vivos: Lista de personas vivas.
            avg_gen: Generación promedio de la población.
            max_gen: Generación máxima alcanzada.
            min_gen: Generación mínima en la población.
            current_time: Timestamp actual de la simulación.
            is_drastic: True si este snapshot fue disparado por un evento drástico.
            
        Returns:
            Diccionario con métricas evolutivas completas.
        """
        evo_cfg = self.config.evolution
        snapshot = {
            "time_days": current_time,
            "population_size": len(vivos),
            "generation_avg": avg_gen,
            "generation_max": max_gen,
            "generation_min": min_gen,
            "is_drastic_event": is_drastic,
            "gene_averages": {},
            "gene_variances": {},
            "selection_differentials": {},
            "genes_in_extinction_risk": [],
            "gene_correlations": {},
            "death_analysis": {},
            "disease_analysis": {},
            "dominant_lineages": []
        }

        # Extraemos los genes a rastrear a partir de un espécimen vivo
        primer_agente = vivos[0]
        if not hasattr(primer_agente, 'genome'):
            return snapshot
            
        nombres_genes = self._get_tracked_genes(primer_agente.genome)
        
        # =====================================================================
        # CÁLCULO DE FITNESS BASADO EN DESCENDENCIA VIVA (NO SOLO HIJOS)
        # =====================================================================
        fitness_scores = self._calculate_fitness_scores(vivos)

        # =====================================================================
        # 1. ANÁLISIS GENÉTICO PROFUNDO (MEDIAS, VARIANZAS Y SELECCIÓN)
        # =====================================================================
        gene_values_matrix: Dict[str, List[float]] = {}
        
        for gen in nombres_genes:
            valores_poblacion = [float(getattr(p.genome, gen, 0.0)) for p in vivos]
            gene_values_matrix[gen] = valores_poblacion
            
            if valores_poblacion:
                mean_val = sum(valores_poblacion) / len(valores_poblacion)
                variance_val = sum((x - mean_val) ** 2 for x in valores_poblacion) / len(valores_poblacion)
                
                snapshot["gene_averages"][gen] = mean_val
                snapshot["gene_variances"][gen] = variance_val

                # CORRECCIÓN: Solo usar varianza para detectar pérdida de diversidad
                # Si la varianza colapsa, el gen está fijado (no en peligro de extinción)
                if variance_val < evo_cfg.variance_extinction_threshold:
                    snapshot["genes_in_extinction_risk"].append({
                        "gene": gen,
                        "reason": "fijacion_genetica",
                        "variance": variance_val,
                        "mean": mean_val
                    })

                # Diferencial de selección ponderado por fitness total (descendencia viva)
                if fitness_scores:
                    total_fitness = sum(fitness_scores.values())
                    if total_fitness > 0:
                        weighted_mean = sum(
                            float(getattr(p.genome, gen, 0.0)) * fitness_scores.get(p.entity_id, 0)
                            for p in vivos
                        ) / total_fitness
                        
                        # Diferencial = fitness-weighted mean - population mean
                        snapshot["selection_differentials"][gen] = weighted_mean - mean_val
                    else:
                        snapshot["selection_differentials"][gen] = 0.0
                else:
                    snapshot["selection_differentials"][gen] = 0.0

        # =====================================================================
        # 2. ANÁLISIS DE CORRELACIONES ENTRE GENES
        # =====================================================================
        if len(nombres_genes) >= 2 and len(vivos) >= 10:
            snapshot["gene_correlations"] = self._calculate_gene_correlations(gene_values_matrix, nombres_genes)

        # =====================================================================
        # 3. ANÁLISIS DE CAUSAS DE MUERTE (PRESIONES SELECTIVAS)
        # =====================================================================
        if self.death_history:
            snapshot["death_analysis"] = self._analyze_death_causes(nombres_genes)

        # =====================================================================
        # 4. ANÁLISIS DE ENFERMEDADES E INMUNIDAD
        # =====================================================================
        snapshot["disease_analysis"] = self._analyze_disease_selection(vivos, nombres_genes)

        # =====================================================================
        # 5. SUPERVIVENCIA Y ÉXITO DE LINAJES
        # =====================================================================
        if self.ancestry_queries:
            vivos_ids = {p.entity_id for p in vivos}
            fundadores = self._get_founders(state)
            
            top_lineages = []
            for fundador in fundadores:
                metricas = self.ancestry_queries.calculate_lineage_success(
                    fundador.entity_id, vivos_ids
                )
                
                if metricas["total_descendencia_viva"] > 0:
                    f_genome = getattr(fundador, 'genome', None)
                    founder_genes = {
                        g: getattr(f_genome, g, 0.0) 
                        for g in nombres_genes
                    } if f_genome else {}
                    
                    bio_children = getattr(fundador, 'biological_children_count', 1)
                    
                    top_lineages.append({
                        "founder_id": fundador.entity_id,
                        "descendants_alive": metricas["total_descendencia_viva"],
                        "reproductive_efficiency": metricas["total_descendencia_viva"] / max(1, bio_children),
                        "founder_genes": founder_genes
                    })
            
            top_lineages.sort(key=lambda x: x["descendants_alive"], reverse=True)
            snapshot["dominant_lineages"] = top_lineages[:5]

        return snapshot

    def _calculate_fitness_scores(self, vivos: List[Any]) -> Dict[int, float]:
        """Calcula el fitness evolutivo de cada individuo usando descendencia total viva.
        
        En lugar de solo contar hijos directos, usa ancestry_queries para obtener
        descendencia total viva (hijos + nietos + bisnietos + ...), lo que representa
        mejor el éxito evolutivo real.
        
        Args:
            vivos: Lista de personas vivas.
            
        Returns:
            Diccionario {entity_id: fitness_score} donde fitness_score es la
            descendencia total viva del individuo.
        """
        if not self.ancestry_queries:
            # Fallback: usar solo hijos biológicos si no hay ancestry_queries
            return {
                p.entity_id: float(getattr(p, 'biological_children_count', 0))
                for p in vivos
            }
        
        vivos_ids = {p.entity_id for p in vivos}
        fitness_scores = {}
        
        for person in vivos:
            metricas = self.ancestry_queries.calculate_lineage_success(
                person.entity_id, vivos_ids
            )
            # Fitness = descendencia total viva (hijos + nietos + bisnietos + ...)
            fitness_scores[person.entity_id] = float(metricas["total_descendencia_viva"])
        
        return fitness_scores

    def _calculate_gene_correlations(
        self,
        gene_values_matrix: Dict[str, List[float]],
        nombres_genes: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """Calcula la matriz de correlación de Pearson entre genes.
        
        Detecta patrones emergentes como "alta fertilidad + baja longevidad"
        o "alta inmunidad + bajo metabolismo".
        
        Args:
            gene_values_matrix: Diccionario {gen: [valores_poblacion]}.
            nombres_genes: Lista de nombres de genes.
            
        Returns:
            Matriz de correlación {gen1: {gen2: correlation_coefficient}}.
        """
        correlations = {}
        
        for gen1 in nombres_genes:
            correlations[gen1] = {}
            values1 = gene_values_matrix[gen1]
            
            for gen2 in nombres_genes:
                if gen1 == gen2:
                    correlations[gen1][gen2] = 1.0
                    continue
                
                values2 = gene_values_matrix[gen2]
                
                # Calcular correlación de Pearson
                correlation = self._pearson_correlation(values1, values2)
                correlations[gen1][gen2] = correlation
        
        return correlations

    def _pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calcula el coeficiente de correlación de Pearson entre dos listas.
        
        Args:
            x: Primera lista de valores.
            y: Segunda lista de valores.
            
        Returns:
            Coeficiente de correlación [-1.0, 1.0].
        """
        n = len(x)
        if n != len(y) or n < 2:
            return 0.0
        
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator_x = math.sqrt(sum((x[i] - mean_x) ** 2 for i in range(n)))
        denominator_y = math.sqrt(sum((y[i] - mean_y) ** 2 for i in range(n)))
        
        if denominator_x == 0 or denominator_y == 0:
            return 0.0
        
        return numerator / (denominator_x * denominator_y)

    def _analyze_death_causes(self, nombres_genes: List[str]) -> Dict[str, Any]:
        """Analiza las causas de muerte y su correlación con genotipos.
        
        Agrupa las muertes por causa y calcula el genoma promedio de los
        fallecidos por cada causa, permitiendo detectar selección natural.
        
        Args:
            nombres_genes: Lista de nombres de genes para analizar.
            
        Returns:
            Diccionario con análisis de causas de muerte.
        """
        # Agrupar muertes por causa
        deaths_by_cause: Dict[str, List[Dict[str, Any]]] = {}
        
        for death in self.death_history:
            reason = death['reason']
            if reason not in deaths_by_cause:
                deaths_by_cause[reason] = []
            deaths_by_cause[reason].append(death)
        
        analysis = {
            "total_deaths": len(self.death_history),
            "causes": {}
        }
        
        for cause, deaths in deaths_by_cause.items():
            # Calcular genoma promedio de los fallecidos por esta causa
            genome_sums = {gen: 0.0 for gen in nombres_genes}
            age_sum = 0.0
            
            for death in deaths:
                age_sum += death['age']
                for gen in nombres_genes:
                    genome_sums[gen] += death['genome'].get(gen, 0.0)
            
            n = len(deaths)
            avg_genome = {gen: genome_sums[gen] / n for gen in nombres_genes}
            avg_age = age_sum / n
            
            analysis["causes"][cause] = {
                "count": n,
                "percentage": (n / len(self.death_history)) * 100,
                "average_age": avg_age,
                "average_genome": avg_genome
            }
        
        return analysis

    def _analyze_disease_selection(
        self,
        vivos: List[Any],
        nombres_genes: List[str]
    ) -> Dict[str, Any]:
        """Analiza la selección natural sobre inmunidad y enfermedades.
        
        Compara el genoma de individuos sanos vs enfermos, y analiza
        la distribución de inmunidad en la población.
        
        Args:
            vivos: Lista de personas vivas.
            nombres_genes: Lista de nombres de genes para analizar.
            
        Returns:
            Diccionario con análisis de selección sobre enfermedades.
        """
        sanos = [p for p in vivos if not getattr(p, 'is_sick', False)]
        enfermos = [p for p in vivos if getattr(p, 'is_sick', False)]
        
        analysis = {
            "healthy_count": len(sanos),
            "sick_count": len(enfermos),
            "sickness_rate": len(enfermos) / max(1, len(vivos)) * 100,
            "genome_comparison": {},
            "immunity_distribution": {}
        }
        
        # Comparar genoma de sanos vs enfermos
        if sanos and enfermos:
            for gen in nombres_genes:
                healthy_values = [float(getattr(p.genome, gen, 0.0)) for p in sanos]
                sick_values = [float(getattr(p.genome, gen, 0.0)) for p in enfermos]
                
                healthy_mean = sum(healthy_values) / len(healthy_values)
                sick_mean = sum(sick_values) / len(sick_values)
                
                analysis["genome_comparison"][gen] = {
                    "healthy_mean": healthy_mean,
                    "sick_mean": sick_mean,
                    "difference": sick_mean - healthy_mean
                }
        
        # Analizar distribución de inmunidad
        if "immunity" in nombres_genes:
            immunity_values = [float(getattr(p.genome, 'immunity', 0.0)) for p in vivos]
            if immunity_values:
                analysis["immunity_distribution"] = {
                    "mean": sum(immunity_values) / len(immunity_values),
                    "min": min(immunity_values),
                    "max": max(immunity_values),
                    "variance": sum((x - sum(immunity_values) / len(immunity_values)) ** 2 
                                   for x in immunity_values) / len(immunity_values)
                }
        
        # Analizar familias de patógenos activos
        pathogen_families: Dict[str, int] = {}
        for person in enfermos:
            if hasattr(person, 'active_infections'):
                for infection_state in person.active_infections.values():
                    family = infection_state.pathogen.family
                    pathogen_families[family] = pathogen_families.get(family, 0) + 1
        
        analysis["active_pathogen_families"] = pathogen_families
        
        return analysis

    def _get_founders(self, state: WorldState) -> List[Any]:
        """Identifica a los individuos fundadores (Generación 0) en la población actual.
        
        Args:
            state: Estado autoritativo del mundo.
            
        Returns:
            Lista de personas vivas que son fundadoras (Generación 0).
        """
        if not self.ancestry_queries:
            return []
        
        genealogy = getattr(self.ancestry_queries, '_genealogy', None)
        if not genealogy:
            return []
        
        registry = getattr(genealogy, 'registry', {})
        vivos_ids = {p.entity_id for p in state.get_all_persons()}
        
        fundadores = []
        for entity_id, node in registry.items():
            if (getattr(node, 'generation_index', -1) == 0 and 
                entity_id in vivos_ids):
                person = state.get_person(entity_id)
                if person:
                    fundadores.append(person)
        
        return fundadores

    def _log_evolutionary_insights(self, snapshot: Dict[str, Any]) -> None:
        """Imprime una radiografía explicativa clara de las dinámicas evolutivas actuales.
        
        Args:
            snapshot: Diccionario con métricas evolutivas del snapshot actual.
        """
        t = snapshot["time_days"]
        drastic_tag = " [EVENTO DRÁSTICO]" if snapshot.get("is_drastic_event") else ""
        
        self.logger.info(f"=== INFORME EVOLUTIVO (Día {t:.1f}){drastic_tag} ===")
        self.logger.info(
            f" Población Viva: {snapshot['population_size']} | "
            f"Generación Media: {snapshot['generation_avg']:.2f}"
        )
        
        # Presiones de selección
        diffs = snapshot["selection_differentials"]
        insights_seleccion = [
            f"{gen}: {'⬆️ Positiva' if val > 0.005 else '⬇️ Negativa' if val < -0.005 else '⚖️ Estable'} ({val:+.4f})"
            for gen, val in diffs.items()
        ]
        self.logger.info(f" Presiones de Selección Activas: {', '.join(insights_seleccion)}")
        
        # Genes en riesgo (baja diversidad)
        if snapshot["genes_in_extinction_risk"]:
            for risk in snapshot["genes_in_extinction_risk"]:
                self.logger.warning(
                    f" ⚠️ Gen {risk['gene']}: {risk['reason']} "
                    f"(varianza: {risk['variance']:.4f}, media: {risk['mean']:.2f})"
                )
        
        # Correlaciones fuertes
        correlations = snapshot.get("gene_correlations", {})
        strong_correlations = []
        for gen1, corr_dict in correlations.items():
            for gen2, corr_val in corr_dict.items():
                if gen1 < gen2 and abs(corr_val) > 0.5:  # Solo correlaciones fuertes
                    direction = "positiva" if corr_val > 0 else "negativa"
                    strong_correlations.append(f"{gen1}↔{gen2}: {corr_val:+.2f} ({direction})")
        
        if strong_correlations:
            self.logger.info(f" Correlaciones Genéticas Fuertes: {', '.join(strong_correlations)}")
        
        # Análisis de enfermedades
        disease_analysis = snapshot.get("disease_analysis", {})
        if disease_analysis.get("sick_count", 0) > 0:
            self.logger.info(
                f" Epidemiología: {disease_analysis['sick_count']} enfermos "
                f"({disease_analysis['sickness_rate']:.1f}% de la población)"
            )
            
            # Mostrar diferencias genéticas entre sanos y enfermos
            genome_comp = disease_analysis.get("genome_comparison", {})
            significant_diffs = [
                f"{gen}: {diff['difference']:+.3f}"
                for gen, diff in genome_comp.items()
                if abs(diff['difference']) > 0.05
            ]
            if significant_diffs:
                self.logger.info(f" Diferencias Genéticas Sanos vs Enfermos: {', '.join(significant_diffs)}")
        
        # Análisis de causas de muerte
        death_analysis = snapshot.get("death_analysis", {})
        if death_analysis.get("total_deaths", 0) > 0:
            self.logger.info(f" Mortalidad: {death_analysis['total_deaths']} muertes entre snapshots")
            
            # Mostrar causas principales
            causes = death_analysis.get("causes", {})
            top_causes = sorted(causes.items(), key=lambda x: x[1]['count'], reverse=True)[:3]
            for cause, data in top_causes:
                self.logger.info(
                    f"  - {cause}: {data['count']} muertes ({data['percentage']:.1f}%), "
                    f"edad media: {data['average_age']:.0f} días"
                )
        
        # Linajes dominantes
        if snapshot["dominant_lineages"]:
            ganador = snapshot["dominant_lineages"][0]
            self.logger.info(
                f" 👑 Linaje Dominante: Fundador {ganador['founder_id']} "
                f"({ganador['descendants_alive']} descendientes vivos)."
            )

    def export_to_json(self, filename: str = "evolution_data.json") -> None:
        """Persiste el historial macroevolutivo a disco para su análisis visual.
        
        Args:
            filename: Nombre del archivo de salida (por defecto: evolution_data.json).
        """
        if not self.history:
            return
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=4)