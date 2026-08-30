# 13 - Evolución

## 📋 Resumen

El **Sistema de Evolución** es un **observador puro** (solo lectura) que monitorea la macroevolución del ecosistema simulado. No modifica el estado de los agentes: en su lugar, extrae instantáneas genéticas a intervalos regulares para analizar diversidad genética, presión de selección, correlaciones entre genes, causas de muerte, éxito de linajes y eventos drásticos como cuellos de botella poblacionales.

**Filosofía fundamental**: *La evolución no se programa: emerge. El EvolutionEngine observa, mide y reporta las presiones selectivas que surgen naturalmente de la interacción entre genética, entorno, enfermedades y comportamiento social.*

---

## 🎯 Responsabilidad

**Es responsable de:**
- Recolectar snapshots genéticos a intervalos regulares
- Detectar eventos drásticos (cuellos de botella, mortalidad masiva)
- Calcular medias y varianzas de todos los genes poblacionales
- Calcular diferenciales de selección (presión evolutiva) ponderados por fitness
- Detectar genes en riesgo de fijación genética (pérdida de diversidad)
- Calcular correlaciones de Pearson entre pares de genes
- Analizar causas de muerte y su correlación con genotipos
- Analizar selección sobre inmunidad (sanos vs enfermos)
- Identificar linajes dominantes (mayor descendencia viva)
- Persistir el historial evolutivo en memoria
- Exportar datos a JSON para análisis externo
- Emitir reportes legibles en logs

**NO es responsable de:**
- ❌ Modificar el genoma de los agentes (eso ocurre por mutación en `Genome.combine()`)
- ❌ Decidir quién sobrevive (eso lo hace `MortalitySystem`, doc 10)
- ❌ Decidir quién se reproduce (eso lo hace `ConceptionSystem`, doc 05)
- ❌ Gestionar el árbol genealógico (eso lo hace `GenealogySystem`, doc 12)
- ❌ Procesar enfermedades (eso lo hace `DiseaseSystem`, doc 09)
- ❌ Almacenar el estado del mundo (eso lo hace `WorldState`, doc 02)

---

## 🌍 Equivalencia con la vida real

| Concepto del sistema | Equivalencia en la vida real | Unidad |
|---------------------|-----------------------------|--------|
| **EvolutionEngine** | Observatorio evolutivo / biólogo de campo | Científico |
| **Snapshot genético** | Muestreo poblacional | Censo genético |
| **Gene averages** | Media poblacional de rasgos | Fenotipo medio |
| **Gene variance** | Diversidad genética | Varianza alélica |
| **Selection differential** | Presión de selección | S (Breeder's equation) |
| **Gene correlation** | Ligamiento / pleiotropía | Covarianza genética |
| **Fitness score** | Éxito reproductivo | Darwinian fitness |
| **Bottleneck detection** | Cuello de botella poblacional | Evento de deriva |
| **Lineage dominance** | Éxito de dinastías | Selección multinivel |
| **Death analysis** | Estudio de causas de mortalidad | Epidemiología forense |
| **Inbreeding risk** | Depresión endogámica | Coeficiente F |
| **Drastic event** | Evento catastrófico | Extinción masiva |

---

## 📁 Archivos que lo componen

| Archivo | Clase principal | Responsabilidad |
|---------|-----------------|-----------------|
| `systems/evolution/evolution_engine.py` | `EvolutionEngine` | Observador macroevolutivo completo |

---

## 🔄 Flujo de ejecución completo

```
┌─────────────────────────────────────────────────────────────────┐
│          CICLO DE VIDA EVOLUTIVO (por tick)                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 0: ACUMULACIÓN DE MUERTES                                  │
│                                                                 │
│ _accumulate_deaths(pending, state):                             │
│  ├── Para cada muerte en pending.deaths:                        │
│  │   ├── Extraer genoma del fallecido                           │
│  │   ├── Extraer enfermedades activas                           │
│  │   └── Almacenar en death_history                             │
│  └── (persiste entre snapshots)                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 1: FILTRADO DE POBLACIÓN VIVA                              │
│                                                                 │
│ vivos = [p for p in state.get_all_persons()                     │
│          if p.entity_id not in pending.deaths]                  │
│                                                                 │
│ Si no hay vivos → return (población extinta)                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 2: DETECCIÓN DE EVENTOS DRÁSTICOS                          │
│                                                                 │
│ _detect_drastic_event(current_population):                      │
│  ├── Si población cayó >20% desde último snapshot → CUELLO BOTELLA│
│  └── Si hay >10 muertes acumuladas → MORTALIDAD MASIVA          │
│                                                                 │
│ is_drastic = resultado                                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 3: DECISIÓN DE SNAPSHOT                                    │
│                                                                 │
│ should_snapshot si:                                             │
│  ├── current_time == 0.0 (inicio)                               │
│  ├── (current_time - last_snapshot) >= snapshot_interval_days   │
│  └── is_drastic == True (evento extraordinario)                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                      (solo si should_snapshot)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 4: CÓMPUTO DE SNAPSHOT COMPLETO                            │
│                                                                 │
│ _compute_genetic_snapshot(state, vivos, ...):                   │
│                                                                 │
│  1. IDENTIFICACIÓN DE GENES:                                    │
│     └── _get_tracked_genes(genome): inspeccionar properties     │
│                                                                 │
│  2. FITNESS POR DESCENDENCIA VIVA:                              │
│     └── _calculate_fitness_scores(vivos):                       │
│         └── Usa ancestry_queries para descendencia total        │
│                                                                 │
│  3. ANÁLISIS GENÉTICO PROFUNDO:                                 │
│     ├── Medias poblacionales por gen                            │
│     ├── Varianzas poblacionales por gen                         │
│     ├── Genes en riesgo (varianza < threshold → fijación)       │
│     └── Diferenciales de selección (weighted mean - pop mean)   │
│                                                                 │
│  4. CORRELACIONES ENTRE GENES:                                  │
│     └── _calculate_gene_correlations: Pearson entre pares       │
│                                                                 │
│  5. ANÁLISIS DE CAUSAS DE MUERTE:                               │
│     └── _analyze_death_causes: genoma promedio por causa        │
│                                                                 │
│  6. ANÁLISIS DE ENFERMEDADES:                                   │
│     └── _analyze_disease_selection: sanos vs enfermos           │
│                                                                 │
│  7. LINAJES DOMINANTES:                                         │
│     └── Top 5 fundadores por descendencia viva                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 5: PERSISTENCIA Y REPORTE                                  │
│                                                                 │
│  ├── history.append(snapshot)                                   │
│  ├── last_snapshot_time = current_time                          │
│  ├── last_population_size = current_population                  │
│  ├── death_history.clear()                                      │
│  └── _log_evolutionary_insights(snapshot):                      │
│      ├── Población y generación                                 │
│      ├── Presiones de selección (⬆️⬇️⚖️)                          │
│      ├── Genes en riesgo (⚠️)                                    │
│      ├── Correlaciones fuertes                                  │
│      ├── Epidemiología                                          │
│      ├── Causas de muerte                                       │
│      └── Linaje dominante (👑)                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes del Sistema

---

### EvolutionEngine - Observador Macroevolutivo

**📁 Archivo**: `systems/evolution/evolution_engine.py`
**🌍 Equivalencia real**: Un observatorio evolutivo que monitorea la población sin interferir, como un biólogo de campo con instrumentos de medición.

#### Atributos

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `config` | `SimulationConfig` | Configuración centralizada |
| `ancestry_queries` | `AncestryQueries` | Servicio de consultas genealógicas (opcional) |
| `last_snapshot_time` | `float` | Día del último snapshot |
| `last_population_size` | `int` | Población en último snapshot |
| `history` | `List[Dict]` | Historial completo de snapshots |
| `death_history` | `List[Dict]` | Muertes acumuladas entre snapshots |

#### Constructor

```python
def __init__(self, config, ancestry_queries=None):
    self.config = config
    self.ancestry_queries = ancestry_queries
    self.last_snapshot_time = 0.0
    self.last_population_size = 0
    self.history = []           # Dueño de su propio historial
    self.death_history = []     # Persistente entre snapshots
```

**Nota importante**: El motor es dueño de su propio historial, aislando la analítica del `WorldState`. Esto evita acoplamientos y facilita la serialización.

---

### Método principal: `process()`

```python
def process(self, state, pending, delta_days, context):
    # 1. Acumular muertes del tick
    self._accumulate_deaths(pending, state)
    
    # 2. Filtrar población viva
    vivos = [p for p in state.get_all_persons() 
             if p.entity_id not in pending.deaths]
    if not vivos:
        return  # Extinción total
    
    # 3. Detectar eventos drásticos
    current_time = state.world_days_elapsed
    current_population = len(vivos)
    is_drastic = self._detect_drastic_event(current_population)
    
    # 4. Decidir si hacer snapshot
    should_snapshot = (
        current_time == 0.0 or
        (current_time - self.last_snapshot_time) >= evo_cfg.snapshot_interval_days or
        is_drastic
    )
    
    # 5. Si toca, computar snapshot completo
    if should_snapshot:
        generaciones = self._get_generations(vivos)
        avg_gen = sum(generaciones) / len(generaciones)
        max_gen = max(generaciones)
        min_gen = min(generaciones)
        
        snapshot = self._compute_genetic_snapshot(
            state, vivos, avg_gen, max_gen, min_gen,
            current_time, is_drastic
        )
        
        # 6. Persistir y reportar
        self.history.append(snapshot)
        self.last_snapshot_time = current_time
        self.last_population_size = current_population
        self.death_history.clear()
        self._log_evolutionary_insights(snapshot)
```

---

### Acumulación de muertes

```python
def _accumulate_deaths(self, pending, state):
    for entity_id, reason in pending.deaths.items():
        person = state.get_person(entity_id)
        if person and hasattr(person, 'genome'):
            # Extraer genes del fallecido
            genome_data = {}
            for gen in self._get_tracked_genes(person.genome):
                genome_data[gen] = float(getattr(person.genome, gen, 0.0))
            
            # Extraer enfermedades activas
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
```

**Persistencia**: `death_history` se mantiene entre snapshots para análisis agregado.

---

### Detección de eventos drásticos

```python
def _detect_drastic_event(self, current_population):
    if self.last_population_size == 0:
        return False
    
    # Criterio 1: Cuello de botella (caída >20%)
    population_drop = (self.last_population_size - current_population) / self.last_population_size
    if population_drop > 0.20:
        self.logger.warning(
            f"⚠️ CUELLO DE BOTELLA: {population_drop*100:.1f}% "
            f"({self.last_population_size} → {current_population})"
        )
        return True
    
    # Criterio 2: Mortalidad masiva (>10 muertes entre snapshots)
    if len(self.death_history) > 10:
        self.logger.warning(
            f"⚠️ MORTALIDAD MASIVA: {len(self.death_history)} muertes"
        )
        return True
    
    return False
```

**Interpretación**: Un evento drástico dispara un snapshot extraordinario incluso si no ha pasado el intervalo regular.

---

### Identificación de genes a rastrear

```python
def _get_tracked_genes(self, sample_genome):
    tracked_genes = []
    genome_class = type(sample_genome)
    
    for attr_name in dir(genome_class):
        attr = getattr(genome_class, attr_name, None)
        # Solo properties públicas
        if isinstance(attr, property) and not attr_name.startswith('_'):
            try:
                value = getattr(sample_genome, attr_name, None)
                # Solo valores numéricos (no strings, bools)
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    tracked_genes.append(attr_name)
            except Exception:
                pass
    
    return tracked_genes
```

**Característica clave**: El sistema se adapta automáticamente a nuevos genes añadidos al `Genome` sin necesidad de modificar el código.

---

### Cálculo de fitness (éxito reproductivo)

```python
def _calculate_fitness_scores(self, vivos):
    if not self.ancestry_queries:
        # Fallback: solo hijos biológicos directos
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
```

**Innovación**: En lugar de contar solo hijos directos, usa `ancestry_queries` para calcular la descendencia total viva. Esto representa mejor el éxito evolutivo real.

---

### Cómputo del snapshot completo

El método `_compute_genetic_snapshot()` realiza 5 análisis principales:

#### 1. Análisis genético profundo

```python
for gen in nombres_genes:
    valores_poblacion = [float(getattr(p.genome, gen, 0.0)) for p in vivos]
    
    # Media poblacional
    mean_val = sum(valores_poblacion) / len(valores_poblacion)
    
    # Varianza poblacional
    variance_val = sum((x - mean_val)**2 for x in valores_poblacion) / len(valores_poblacion)
    
    snapshot["gene_averages"][gen] = mean_val
    snapshot["gene_variances"][gen] = variance_val
    
    # Detección de fijación genética (pérdida de diversidad)
    if variance_val < evo_cfg.variance_extinction_threshold:
        snapshot["genes_in_extinction_risk"].append({
            "gene": gen,
            "reason": "fijacion_genetica",
            "variance": variance_val,
            "mean": mean_val
        })
    
    # Diferencial de selección (ponderado por fitness)
    if fitness_scores and sum(fitness_scores.values()) > 0:
        weighted_mean = sum(
            float(getattr(p.genome, gen, 0.0)) * fitness_scores.get(p.entity_id, 0)
            for p in vivos
        ) / sum(fitness_scores.values())
        
        # Diferencial = media ponderada por fitness - media poblacional
        snapshot["selection_differentials"][gen] = weighted_mean - mean_val
```

**Interpretación del diferencial de selección (S)**:
- `S > 0`: selección positiva (el rasgo favorece el éxito reproductivo)
- `S < 0`: selección negativa (el rasgo reduce el éxito reproductivo)
- `S ≈ 0`: sin presión selectiva (rasgo neutral)

#### 2. Correlaciones entre genes

```python
def _calculate_gene_correlations(self, gene_values_matrix, nombres_genes):
    correlations = {}
    
    for gen1 in nombres_genes:
        correlations[gen1] = {}
        values1 = gene_values_matrix[gen1]
        
        for gen2 in nombres_genes:
            if gen1 == gen2:
                correlations[gen1][gen2] = 1.0
                continue
            values2 = gene_values_matrix[gen2]
            correlations[gen1][gen2] = self._pearson_correlation(values1, values2)
    
    return correlations

def _pearson_correlation(self, x, y):
    n = len(x)
    if n != len(y) or n < 2:
        return 0.0
    
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator_x = math.sqrt(sum((x[i] - mean_x)**2 for i in range(n)))
    denominator_y = math.sqrt(sum((y[i] - mean_y)**2 for i in range(n)))
    
    if denominator_x == 0 or denominator_y == 0:
        return 0.0
    
    return numerator / (denominator_x * denominator_y)
```

**Interpretación**:
- `r ≈ +1`: correlación positiva fuerte (genes que co-evolucionan)
- `r ≈ -1`: correlación negativa fuerte (trade-off evolutivo)
- `r ≈ 0`: genes independientes

**Patrones emergentes detectables**:
- Alta fertilidad + baja longevidad (estrategia r)
- Alta inmunidad + alto metabolismo (inversión en defensas)
- Alta inteligencia + alta sociabilidad (cerebro social)

#### 3. Análisis de causas de muerte

```python
def _analyze_death_causes(self, nombres_genes):
    # Agrupar muertes por causa
    deaths_by_cause = {}
    for death in self.death_history:
        reason = death['reason']
        deaths_by_cause.setdefault(reason, []).append(death)
    
    analysis = {
        "total_deaths": len(self.death_history),
        "causes": {}
    }
    
    for cause, deaths in deaths_by_cause.items():
        genome_sums = {gen: 0.0 for gen in nombres_genes}
        age_sum = 0.0
        
        for death in deaths:
            age_sum += death['age']
            for gen in nombres_genes:
                genome_sums[gen] += death['genome'].get(gen, 0.0)
        
        n = len(deaths)
        analysis["causes"][cause] = {
            "count": n,
            "percentage": (n / len(self.death_history)) * 100,
            "average_age": age_sum / n,
            "average_genome": {gen: genome_sums[gen] / n for gen in nombres_genes}
        }
    
    return analysis
```

**Interpretación**: Si las muertes por cierta causa tienen un genoma promedio sistemáticamente diferente al poblacional, hay **selección natural** actuando.

#### 4. Análisis de selección sobre enfermedades

```python
def _analyze_disease_selection(self, vivos, nombres_genes):
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
            
            analysis["genome_comparison"][gen] = {
                "healthy_mean": sum(healthy_values) / len(healthy_values),
                "sick_mean": sum(sick_values) / len(sick_values),
                "difference": (sum(sick_values)/len(sick_values)) - (sum(healthy_values)/len(healthy_values))
            }
    
    # Analizar distribución de inmunidad
    if "immunity" in nombres_genes:
        immunity_values = [float(getattr(p.genome, 'immunity', 0.0)) for p in vivos]
        if immunity_values:
            mean_val = sum(immunity_values) / len(immunity_values)
            analysis["immunity_distribution"] = {
                "mean": mean_val,
                "min": min(immunity_values),
                "max": max(immunity_values),
                "variance": sum((x - mean_val)**2 for x in immunity_values) / len(immunity_values)
            }
    
    # Familias de patógenos activos
    pathogen_families = {}
    for person in enfermos:
        if hasattr(person, 'active_infections'):
            for infection_state in person.active_infections.values():
                family = infection_state.pathogen.family
                pathogen_families[family] = pathogen_families.get(family, 0) + 1
    
    analysis["active_pathogen_families"] = pathogen_families
    
    return analysis
```

**Interpretación**: Si los enfermos tienen valores sistemáticamente diferentes en ciertos genes (ej: `immunity` más baja), hay selección por resistencia a enfermedades.

#### 5. Identificación de linajes dominantes

```python
if self.ancestry_queries:
    vivos_ids = {p.entity_id for p in vivos}
    fundadores = self._get_founders(state)  # Generación 0
    
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
```

**Interpretación**: Los linajes dominantes son aquellos cuyos fundadores tienen más descendencia viva actualmente. Sus genomas representan los alelos "ganadores" de la selección natural.

---

### Reporte de insights evolutivos

```python
def _log_evolutionary_insights(self, snapshot):
    t = snapshot["time_days"]
    drastic_tag = " [EVENTO DRÁSTICO]" if snapshot.get("is_drastic_event") else ""
    
    self.logger.info(f"=== INFORME EVOLUTIVO (Día {t:.1f}){drastic_tag} ===")
    self.logger.info(
        f" Población Viva: {snapshot['population_size']} | "
        f"Generación Media: {snapshot['generation_avg']:.2f}"
    )
    
    # Presiones de selección
    diffs = snapshot["selection_differentials"]
    insights = [
        f"{gen}: {'⬆️ Positiva' if val > 0.005 else '⬇️ Negativa' if val < -0.005 else '⚖️ Estable'} ({val:+.4f})"
        for gen, val in diffs.items()
    ]
    self.logger.info(f" Presiones de Selección Activas: {', '.join(insights)}")
    
    # Genes en riesgo (fijación)
    if snapshot["genes_in_extinction_risk"]:
        for risk in snapshot["genes_in_extinction_risk"]:
            self.logger.warning(
                f" ⚠️ Gen {risk['gene']}: {risk['reason']} "
                f"(varianza: {risk['variance']:.4f}, media: {risk['mean']:.2f})"
            )
    
    # Correlaciones fuertes (|r| > 0.5)
    correlations = snapshot.get("gene_correlations", {})
    strong = []
    for gen1, corr_dict in correlations.items():
        for gen2, corr_val in corr_dict.items():
            if gen1 < gen2 and abs(corr_val) > 0.5:
                direction = "positiva" if corr_val > 0 else "negativa"
                strong.append(f"{gen1}↔{gen2}: {corr_val:+.2f} ({direction})")
    if strong:
        self.logger.info(f" Correlaciones Genéticas Fuertes: {', '.join(strong)}")
    
    # Epidemiología
    disease_analysis = snapshot.get("disease_analysis", {})
    if disease_analysis.get("sick_count", 0) > 0:
        self.logger.info(
            f" Epidemiología: {disease_analysis['sick_count']} enfermos "
            f"({disease_analysis['sickness_rate']:.1f}% de la población)"
        )
    
    # Mortalidad
    death_analysis = snapshot.get("death_analysis", {})
    if death_analysis.get("total_deaths", 0) > 0:
        causes = death_analysis.get("causes", {})
        top_causes = sorted(causes.items(), key=lambda x: x[1]['count'], reverse=True)[:3]
        for cause, data in top_causes:
            self.logger.info(
                f"  - {cause}: {data['count']} muertes ({data['percentage']:.1f}%), "
                f"edad media: {data['average_age']:.0f} días"
            )
    
    # Linaje dominante
    if snapshot["dominant_lineages"]:
        ganador = snapshot["dominant_lineages"][0]
        self.logger.info(
            f" 👑 Linaje Dominante: Fundador {ganador['founder_id']} "
            f"({ganador['descendants_alive']} descendientes vivos)."
        )
```

---

### Exportación a JSON

```python
def export_to_json(self, filename="evolution_data.json"):
    if not self.history:
        return
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(self.history, f, indent=4)
```

Permite análisis externo en Python, R, Jupyter notebooks o herramientas de visualización.

---

## 🔗 Interacción entre componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                       WorldState                                │
│   (agentes vivos, sus genomas, enfermedades, muertes)           │
└──────────────────────────┬──────────────────────────────────────┘
                           │ lee (observador puro)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   EvolutionEngine                               │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  history: List[Dict]  (snapshots evolutivos)           │    │
│  │  death_history: List[Dict]  (muertes acumuladas)       │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Métodos principales:                                           │
│    ├── process() → orquesta el ciclo completo                    │
│    ├── _accumulate_deaths() → persiste muertes                  │
│    ├── _detect_drastic_event() → cuellos de botella             │
│    ├── _compute_genetic_snapshot() → análisis completo          │
│    ├── _calculate_fitness_scores() → éxito reproductivo         │
│    ├── _calculate_gene_correlations() → Pearson                 │
│    ├── _analyze_death_causes() → mortalidad por causa           │
│    ├── _analyze_disease_selection() → sanos vs enfermos         │
│    └── export_to_json() → persistencia externa                  │
└──────────┬────────────────────────────────────┬─────────────────┘
           │                                    │
           │ usa                                │ usa
           ▼                                    ▼
┌────────────────────┐              ┌──────────────────────┐
│ AncestryQueries    │              │ Genome               │
│ (doc 12)           │              │ (doc 03)             │
│                    │              │                      │
│ calculate_lineage_ │              │ Properties públicas  │
│ success() → fitness│              │ (fertility, immunity,│
│                    │              │  longevity, etc.)    │
│ _genealogy.registry│              │                      │
│ → generaciones     │              │ get_trait_value()    │
└────────────────────┘              └──────────────────────┘
```

---

## ⚙️ Configuración relevante

```python
# EvolutionConfig (en SimulationConfig)
config.evolution.snapshot_interval_days = 30.0      # Cada 30 días simulados
config.evolution.variance_extinction_threshold = 0.01  # Umbral de fijación

# Otros parámetros usados indirectamente:
config.genealogy.consanguinity_limit = 3  # Para análisis de endogamia
```

### Parámetros implícitos (hardcoded)

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| Umbral de cuello de botella | 20% caída poblacional | Evento drástico |
| Umbral de mortalidad masiva | 10 muertes | Evento drástico |
| Umbral de correlación fuerte | \|r\| > 0.5 | Para logs |
| Umbral de diferencial significativo | \|S\| > 0.005 | Para logs |
| Umbral de diferencia genética significativa | \|Δ\| > 0.05 | Para logs |
| Tamaño mínimo para correlaciones | 10 individuos | Validez estadística |
| Tamaño mínimo para correlaciones de genes | 2 genes | Validez matemática |

---

## 🧪 Tests del sistema

| Archivo | Cobertura |
|---------|-----------|
| `tests/unit/test_evolution_engine.py` | Snapshots, correlaciones, análisis |
| `tests/integration/test_statistical.py` | Evolución realista a largo plazo |
| `tests/integration/test_regression_bugs.py` | Bugs de acumulación de muertes |

---

## 📝 Ejemplos completos

### Ejemplo 1: Snapshot evolutivo típico

```python
# Día 1000 de simulación, población de 150 agentes
# Intervalo configurado: 30 días

# EvolutionEngine detecta:
# - current_time (1000) - last_snapshot_time (970) = 30 → should_snapshot = True

# Computa snapshot:
snapshot = {
    "time_days": 1000.0,
    "population_size": 150,
    "generation_avg": 3.2,
    "generation_max": 5,
    "generation_min": 0,
    "is_drastic_event": False,
    "gene_averages": {
        "fertility": 1.15,
        "immunity": 1.08,
        "longevity": 0.95,
        "intelligence": 1.02,
        # ... otros genes
    },
    "gene_variances": {
        "fertility": 0.12,
        "immunity": 0.15,
        # ...
    },
    "selection_differentials": {
        "fertility": +0.015,   # Selección positiva
        "longevity": -0.008,   # Selección negativa leve
        "immunity": +0.012,    # Selección positiva
        # ...
    },
    "genes_in_extinction_risk": [
        {"gene": "flight", "reason": "fijacion_genetica", "variance": 0.001, "mean": 0.0}
    ],
    "dominant_lineages": [
        {"founder_id": 42, "descendants_alive": 35, ...},
        {"founder_id": 17, "descendants_alive": 28, ...},
    ]
}

# Log generado:
# === INFORME EVOLUTIVO (Día 1000.0) ===
#  Población Viva: 150 | Generación Media: 3.20
#  Presiones de Selección Activas: fertility: ⬆️ Positiva (+0.0150), longevity: ⬇️ Negativa (-0.0080)
#  ⚠️ Gen flight: fijacion_genetica (varianza: 0.0010, media: 0.00)
#  👑 Linaje Dominante: Fundador 42 (35 descendientes vivos)
```

### Ejemplo 2: Detección de cuello de botella

```python
# Snapshot anterior: población 200
# Tick actual: epidemia grave reduce población a 140

# _detect_drastic_event():
# population_drop = (200 - 140) / 200 = 0.30 = 30%
# 0.30 > 0.20 → True (cuello de botella)

# Snapshot extraordinario disparado inmediatamente
# Log:
# ⚠️ CUELLO DE BOTELLA DETECTADO: Población cayó 30.0% (200 → 140)
# === INFORME EVOLUTIVO (Día 1045.0) [EVENTO DRÁSTICO] ===
```

### Ejemplo 3: Correlación genética fuerte

```python
# Después de varios snapshots, se detecta:
snapshot["gene_correlations"] = {
    "fertility": {
        "longevity": -0.72,  # Correlación negativa fuerte
        "metabolism": +0.35,
        # ...
    },
    # ...
}

# Log:
# Correlaciones Genéticas Fuertes: fertility↔longevity: -0.72 (negativa)

# Interpretación biológica:
# Trade-off evolutivo clásico: alta fertilidad ↔ baja longevidad
# Estrategia r (muchas crías, vida corta) vs K (pocas crías, vida larga)
```

### Ejemplo 4: Análisis de causas de muerte

```python
# Entre snapshots hubo 15 muertes
death_analysis = {
    "total_deaths": 15,
    "causes": {
        "Sepsis / Fallo multiorgánico por Influenza_000123": {
            "count": 7,
            "percentage": 46.7,
            "average_age": 18250.0,  # ~50 años
            "average_genome": {
                "immunity": 0.85,  # Bajo en muertos por influenza
                "longevity": 0.92,
                # ...
            }
        },
        "Fallo sistémico por senectud": {
            "count": 5,
            "percentage": 33.3,
            "average_age": 36500.0,  # ~100 años
            "average_genome": {
                "longevity": 1.25,  # Alto en longevos
                # ...
            }
        },
        "Inanición": {
            "count": 3,
            "percentage": 20.0,
            "average_age": 5000.0,
            # ...
        }
    }
}

# Log:
# Mortalidad: 15 muertes entre snapshots
#   - Sepsis / Fallo multiorgánico: 7 muertes (46.7%), edad media: 18250 días
#   - Fallo sistémico por senectud: 5 muertes (33.3%), edad media: 36500 días
#   - Inanición: 3 muertes (20.0%), edad media: 5000 días
```

### Ejemplo 5: Selección sobre inmunidad

```python
# 120 sanos, 30 enfermos en snapshot
disease_analysis = {
    "healthy_count": 120,
    "sick_count": 30,
    "sickness_rate": 20.0,
    "genome_comparison": {
        "immunity": {
            "healthy_mean": 1.15,
            "sick_mean": 0.75,
            "difference": -0.40  # Los enfermos tienen inmunidad más baja
        },
        "longevity": {
            "healthy_mean": 1.02,
            "sick_mean": 0.98,
            "difference": -0.04  # Diferencia pequeña
        }
    },
    "immunity_distribution": {
        "mean": 1.08,
        "min": 0.3,
        "max": 1.8,
        "variance": 0.15
    },
    "active_pathogen_families": {
        "Influenza": 18,
        "Coronavirus": 12
    }
}

# Log:
# Epidemiología: 30 enfermos (20.0% de la población)
# Diferencias Genéticas Sanos vs Enfermos: immunity: -0.400

# Interpretación:
# Selección natural está favoreciendo alelos de alta inmunidad
# Los individuos con immunity < 0.9 tienen mayor probabilidad de enfermar
```

### Ejemplo 6: Linaje dominante

```python
# Varios fundadores compiten, uno gana claramente
snapshot["dominant_lineages"] = [
    {
        "founder_id": 42,
        "descendants_alive": 35,
        "reproductive_efficiency": 11.67,  # 35 descendientes / 3 hijos directos
        "founder_genes": {
            "fertility": 1.35,   # Alta fertilidad del fundador
            "immunity": 1.20,    # Alta inmunidad
            "sociability": 1.15, # Alta sociabilidad
        }
    },
    {
        "founder_id": 17,
        "descendants_alive": 28,
        "reproductive_efficiency": 7.0,
        "founder_genes": {...}
    }
]

# Log:
# 👑 Linaje Dominante: Fundador 42 (35 descendientes vivos)

# Interpretación:
# El genoma del fundador 42 (alta fertilidad + inmunidad + sociabilidad)
# resultó ser el más exitoso evolutivamente
```

### Ejemplo 7: Exportación y análisis externo

```python
# Tras 10 años de simulación (3650 días, ~120 snapshots)
engine.export_to_json("evolution_10years.json")

# Análisis en Python/Jupyter:
import json
import pandas as pd
import matplotlib.pyplot as plt

with open("evolution_10years.json") as f:
    history = json.load(f)

# DataFrame de evolución de fertilidad
df = pd.DataFrame([
    {"day": s["time_days"], "fertility_mean": s["gene_averages"]["fertility"]}
    for s in history
])

# Gráfica de tendencia
plt.plot(df["day"], df["fertility_mean"])
plt.xlabel("Días simulados")
plt.ylabel("Fertilidad media poblacional")
plt.title("Evolución de la fertilidad")
plt.show()

# Detectar tendencia
from scipy import stats
slope, intercept, r_value, p_value, std_err = stats.linregress(df["day"], df["fertility_mean"])
print(f"Tendencia: {slope*365:.4f} por año (p={p_value:.4f})")
```

---

## 🚨 Consideraciones y limitaciones

### Principios fundamentales
- **Observador puro**: nunca modifica el estado de los agentes
- **Análisis poblacional**: trabaja con distribuciones, no individuos
- **Adaptación dinámica**: detecta automáticamente nuevos genes en Genome
- **Eventos extraordinarios**: dispara snapshots en cuellos de botella
- **Fitness real**: descendencia total viva, no solo hijos directos
- **Historial aislado**: no contamina WorldState con datos analíticos

### Arquitectura

```
TICK DE SIMULACIÓN
   ↓
EvolutionEngine.process()
   ↓
├── _accumulate_deaths() → death_history (persistente)
├── _detect_drastic_event() → bool
├── should_snapshot? → interval OR evento drástico
└── Si sí:
    ├── _get_tracked_genes() → introspección
    ├── _calculate_fitness_scores() → con ancestry_queries
    ├── _compute_genetic_snapshot() → análisis completo
    │    ├── Medias y varianzas
    │    ├── Diferenciales de selección
    │    ├── Correlaciones de Pearson
    │    ├── Análisis de causas de muerte
    │    ├── Análisis de enfermedades
    │    └── Top 5 linajes dominantes
    ├── history.append(snapshot)
    └── _log_evolutionary_insights()
```

### Optimizaciones de rendimiento

| Optimización | Descripción |
|--------------|-------------|
| Snapshot por intervalos | No analiza cada tick (costoso) |
| Introspección de properties | Sin hardcodeo de genes |
| Early returns | Población vacía → salir rápido |
| Historial aislado | No carga WorldState |
| Caché de tracked genes | Se calcula una vez por snapshot |
| Pearson vectorizado | Implementación eficiente |

### Limitaciones
- No calcula el coeficiente de Wright real (endogamia)
- No hace análisis filogenético de patógenos
- No detecta selección dependiente de frecuencia
- No analiza mutaciones específicas, solo promedios
- El análisis de correlaciones no implica causalidad
- La varianza sola no detecta genes en extinción por deriva
- No hay análisis de coalescencia (MRCA)
- No hay análisis de haplotipos

### Errores comunes
- ❌ Asumir que correlación implica causalidad
- ❌ Confundir varianza baja con "gen extinto" (puede ser fijación beneficiosa)
- ❌ Usar fitness = hijos directos (subestima éxito real)
- ❌ Olvidar limpiar `death_history` tras snapshot (acumulación infinita)
- ❌ Comparar snapshots sin normalizar por tamaño poblacional
- ❌ Asumir que selección positiva actual = ventaja a largo plazo
- ❌ Ignorar correlaciones entre genes (pleiotropía)

---

## 🎓 Conceptos clave

### ¿Por qué fitness basado en descendencia total viva?

**Principio de fitness inclusivo**:
- Contar solo hijos subestima el éxito evolutivo
- Un agente con 2 hijos pero 50 nietos es más exitoso que uno con 5 hijos y 5 nietos
- La descendencia viva total representa la propagación real de sus genes
- Esto requiere `ancestry_queries.calculate_lineage_success()`

### ¿Por qué observador puro?

**Principio de separación de responsabilidades**:
- La evolución emerge, no se programa
- Si el motor modificara genomas, sería selección artificial
- La observación pura permite estudiar la dinámica natural
- Análogo a un biólogo de campo que no interfiere con la población

### ¿Por qué detección de eventos drásticos?

**Principio de importancia histórica**:
- Los cuellos de botella son eventos evolutivos clave
- La deriva genética es más fuerte en poblaciones pequeñas
- Mortalidad masiva puede indicar presión selectiva intensa
- Capturar estos momentos permite estudiar macroevolución

### ¿Por qué correlaciones de Pearson?

**Principio de pleiotropía y ligamiento**:
- Los genes no evolucionan independientemente
- Trade-offs evolutivos se manifiestan como correlaciones negativas
- La selección conjunta produce correlaciones positivas
- Permite detectar patrones emergentes sin conocerlos a priori

### ¿Por qué introspección de genes?

**Principio de extensibilidad**:
- Si añades un nuevo gen al Genome, el EvolutionEngine lo detecta automáticamente
- No hay que modificar código del motor
- El sistema se adapta a nuevas especies o rasgos
- Reduce el acoplamiento entre componentes

### ¿Por qué análisis de causas de muerte?

**Principio de presión selectiva**:
- Cada causa de muerte representa una presión selectiva diferente
- Comparar el genoma de los fallecidos con el poblacional revela qué alelos son desfavorables
- Ejemplo: si los muertos por inanición tienen bajo metabolismo, hay selección por eficiencia energética

### ¿Por qué análisis de enfermedades?

**Principio de coevolución huésped-patógeno**:
- Las enfermedades son una de las presiones selectivas más fuertes en la naturaleza
- Comparar sanos vs enfermos revela qué genes confieren resistencia
- La distribución de inmunidad muestra si hay selección activa

### ¿Por qué linajes dominantes?

**Principio de selección multinivel**:
- La evolución actúa a nivel de linajes, no solo individuos
- Identificar linajes ganadores permite estudiar qué combinaciones genéticas son más exitosas
- Los genes de los fundadores dominantes son candidatos a "adaptaciones clave"

---

## 📊 Métricas del sistema

| Métrica | Valor |
|---------|-------|
| Archivos del sistema | 1 |
| Atributos del motor | 6 |
| Análisis principales | 5 |
| Métodos de análisis | 8 |
| Métricas por snapshot | ~20 |
| Tests cubriendo evolución | ~10 |

---

## 🔮 Futuras extensiones

### Planificadas
- [ ] Análisis filogenético de patógenos (árbol viral)
- [ ] Coeficiente de Wright real (endogamia)
- [ ] Análisis de selección dependiente de frecuencia
- [ ] Detección de equilibrio evolutivo estable (ESS)

### Posibles
- [ ] Análisis de coalescencia (MRCA - ancestro común más reciente)
- [ ] Análisis de haplotipos y LD (linkage disequilibrium)
- [ ] Detección de sweeps selectivos (fijación rápida de alelos)
- [ ] Análisis de plasticidad fenotípica
- [ ] Reconstrucción de árboles filogenéticos de agentes
- [ ] Análisis de especiación (separación en subpoblaciones)
- [ ] Detección de extinciones masivas
- [ ] Visualización interactiva (exportación a Grafana, Plotly)
- [ ] Análisis de radiación adaptativa
- [ ] Detección de convergencia evolutiva

---

*Documento: 13_EVOLUCION.md*
*Versión: 1.0*