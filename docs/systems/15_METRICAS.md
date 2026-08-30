# 15 - Métricas

## 📋 Resumen

El **Sistema de Métricas** es un **observador puro** (solo lectura) que recolecta instantáneas periódicas multidimensionales del estado del mundo para análisis demográfico, genético, epidemiológico, espacial, cognitivo y genealógico. Actúa como el "dashboard" del simulador: extrae, normaliza y persiste datos sin modificar el estado de los agentes.

**Filosofía fundamental**: *La observación no interfiere con la simulación. El MetricsSystem extrae datos de forma eficiente (bucle único O(N)) y los persiste para análisis longitudinal, visualización externa y debugging, manteniendo el historial bajo control con límites configurables.*

---

## 🎯 Responsabilidad

**Es responsable de:**
- Recolectar snapshots multidimensionales a intervalos regulares
- Calcular métricas demográficas (población, estructura por edades, tasa de crecimiento)
- Calcular métricas genéticas poblacionales (medias y varianzas de todos los genes)
- Calcular métricas epidemiológicas (enfermos, infecciones, familias de patógenos, carga viral)
- Calcular métricas espaciales (presión ambiental, sectores superpoblados)
- Calcular métricas reproductivas (embarazos activos, tamaño de camada, fértiles)
- Calcular métricas cognitivas (estrés cognitivo, emociones promedio)
- Calcular métricas genealógicas (linajes activos/extintos, generación máxima)
- Calcular métricas sociales (estado civil, huérfanos)
- Gestionar el historial con límites de memoria
- Exportar datos a JSON para análisis externo
- Proveer acceso al último snapshot

**NO es responsable de:**
- ❌ Modificar el estado de los agentes (observador puro)
- ❌ Calcular evolución (eso lo hace `EvolutionEngine`, doc 13)
- ❌ Gestionar el árbol genealógico (eso lo hace `GenealogySystem`, doc 12)
- ❌ Procesar enfermedades (eso lo hace `DiseaseSystem`, doc 09)
- ❌ Almacenar el estado del mundo (eso lo hace `WorldState`, doc 02)
- ❌ Visualizar datos (eso lo hace la interfaz externa)

---

## 🌍 Equivalencia con la vida real

| Concepto del sistema | Equivalencia en la vida real | Unidad |
|---------------------|-----------------------------|--------|
| **MetricsSystem** | Instituto nacional de estadística | Observatorio |
| **Snapshot** | Censo poblacional | Instantánea |
| **Population delta** | Crecimiento demográfico | ΔP |
| **Growth rate** | Tasa de crecimiento | % anual |
| **Age structure** | Pirámide poblacional | Distribución etaria |
| **Gene averages** | Fenotipo medio poblacional | Media |
| **Genetic diversity** | Diversidad genética | Varianza |
| **Epidemiology** | Vigilancia epidemiológica | Morbilidad |
| **Pathogen families** | Tipificación de patógenos | Clasificación |
| **Viral load** | Carga ambiental | Contagio potencial |
| **Spatial pressure** | Densidad poblacional | habs/km² |
| **Cognitive stress** | Salud mental poblacional | Bienestar |
| **Active lineages** | Familias activas | Dinastías |
| **Orphan count** | Menores sin tutela | Vulnerabilidad |
| **Marital status** | Estado civil | Estructura familiar |

---

## 📁 Archivos que lo componen

| Archivo | Clase principal | Responsabilidad |
|---------|-----------------|-----------------|
| `systems/metrics/metrics_system.py` | `MetricsSystem` | Observador multidimensional completo |

---

## 🔄 Flujo de ejecución completo

```
┌─────────────────────────────────────────────────────────────────┐
│          CICLO DE MÉTRICAS (por tick)                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 0: CONTROL DE INTERVALO                                    │
│                                                                 │
│ current_day = state.world_days_elapsed                          │
│ interval = config.metrics.snapshot_interval_days                │
│                                                                 │
│ Si (current_day - last_snapshot_day) < interval → return        │
│ (no es momento de tomar snapshot)                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                      (solo si toca snapshot)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 1: FILTRADO Y PREPARACIÓN                                  │
│                                                                 │
│ 1. Filtrar población viva:                                      │
│    alive_persons = [p for p in state.get_all_persons()          │
│                     if p.entity_id not in pending.deaths]       │
│                                                                 │
│ 2. Calcular tasa de crecimiento:                                │
│    population_delta = total_pop - last_population               │
│    growth_rate = (delta / last_population) × 100                │
│                                                                 │
│ 3. Inicializar snapshot con estructura multidimensional         │
│    (10 dimensiones: demografía, edad, genética, epidemiología,  │
│     espacial, reproducción, cognición, genealogía, social, tiempo)│
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 2: BUCLE ÚNICO O(N) DE RECOLECCIÓN                         │
│                                                                 │
│ Para cada person en alive_persons:                              │
│                                                                 │
│  1. EDAD Y ESTRUCTURA:                                          │
│     ├── total_age_days += person.age                            │
│     └── Clasificar en children/adults/seniors                   │
│                                                                 │
│  2. GENÉTICA (introspección automática):                        │
│     └── Para cada gene en tracked_genes:                        │
│         ├── gene_sums[gene] += value                            │
│         └── gene_variances[gene].append(value)                  │
│                                                                 │
│  3. EPIDEMIOLOGÍA:                                              │
│     ├── Si is_sick:                                             │
│     │   ├── sick_count += 1                                     │
│     │   ├── total_infections += len(active_infections)          │
│     │   ├── pathogen_families[family] += 1                      │
│     │   └── total_viral_load += virulence × transmission        │
│                                                                 │
│  4. COGNICIÓN:                                                  │
│     ├── total_cognitive_stress += memory.cognitive_stress       │
│     ├── total_stress += emotions.stress                         │
│     ├── total_happiness += emotions.happiness                   │
│     └── total_energy += emotions.energy                         │
│                                                                 │
│  5. REPRODUCCIÓN:                                               │
│     ├── Si is_pregnant: active_pregnancies++, litter_size +=    │
│     └── Si is_fertile(): fertile_count++                        │
│                                                                 │
│  6. ESTADO SOCIAL:                                              │
│     ├── Si marital == 'casado': married_count++                 │
│     ├── Si marital == 'divorciado': divorced_count++            │
│     ├── Else: single_count++                                    │
│     └── Si sin padres (bio ni adoptivos) y age > 0: orphan++    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 3: CÁLCULOS FINALES Y NORMALIZACIÓN                        │
│                                                                 │
│ 1. Edad promedio: total_age_days / total_pop / 365              │
│ 2. Genética: medias y varianzas por gen                         │
│ 3. Epidemiología: avg_pathogens_per_sick, familias activas      │
│ 4. Cognición: promedios de emociones y estrés                   │
│ 5. Reproducción: avg_litter_size, fertile_count                 │
│ 6. Social: conteos por estado civil                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 4: MÉTRICAS ESPACIALES                                     │
│                                                                 │
│ _calculate_spatial_metrics(snapshot, context):                  │
│  ├── avg_pressure = mean(pressure_map.values())                 │
│  ├── max_pressure = max(pressure_map.values())                  │
│  └── overcrowded_sectors = count(pressure > 1.5)                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 5: MÉTRICAS GENEALÓGICAS                                   │
│                                                                 │
│ _calculate_genealogy_metrics(snapshot):                         │
│  ├── active_lineages = count(lineages where NOT is_extinct)     │
│  ├── extinct_lineages = count(lineages where is_extinct)        │
│  └── max_generation = max(generation_index de vivos)            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 6: PERSISTENCIA Y GESTIÓN DE MEMORIA                       │
│                                                                 │
│ 1. history.append(snapshot)                                     │
│ 2. Si len(history) > max_history_size:                          │
│    └── history.pop(0)  # Eliminar el más antiguo                │
│ 3. last_snapshot_day = current_day                              │
│ 4. last_population = total_pop                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes del Sistema

---

### MetricsSystem - Observador Multidimensional

**📁 Archivo**: `systems/metrics/metrics_system.py`
**🌍 Equivalencia real**: Un instituto nacional de estadística que realiza censos periódicos multidimensionales sin interferir con la población.

#### Atributos

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `config` | `SimulationConfig` | Configuración centralizada |
| `genealogy_system` | `GenealogySystem` | Sistema de genealogía (opcional) |
| `history` | `List[Dict]` | Historial de snapshots |
| `last_snapshot_day` | `float` | Día del último snapshot |
| `last_population` | `int` | Población en último snapshot |

#### Constructor

```python
def __init__(self, config, genealogy_system=None):
    self.config = config
    self.genealogy_system = genealogy_system
    self.history = []
    self.last_snapshot_day = -1.0
    self.last_population = 0
```

**Inyección opcional**: `genealogy_system` es opcional. Si no se proporciona, las métricas genealógicas permanecen en 0.

---

### Estructura del Snapshot (10 dimensiones)

```python
snapshot = {
    # 1. TIEMPO
    "day": round(current_day, 2),
    "year": round(current_day / 365.0, 2),
    
    # 2. DEMOGRAFÍA BÁSICA
    "population": total_pop,
    "births_this_tick": len(pending.births),
    "deaths_this_tick": len(pending.deaths),
    "population_delta": population_delta,
    "growth_rate_percent": round(growth_rate, 2),
    
    # 3. ESTRUCTURA POR EDADES
    "age_structure": {
        "children": 0,
        "adults": 0,
        "seniors": 0
    },
    "avg_age_years": 0.0,
    
    # 4. GENÉTICA POBLACIONAL
    "gene_averages": {},
    "genetic_diversity": {},
    
    # 5. EPIDEMIOLOGÍA
    "epidemiology": {
        "sick_count": 0,
        "total_infections": 0,
        "avg_pathogens_per_sick": 0.0,
        "active_pathogen_families": {},
        "total_viral_load": 0.0
    },
    
    # 6. DISTRIBUCIÓN ESPACIAL
    "spatial": {
        "avg_pressure": 0.0,
        "max_pressure": 0.0,
        "overcrowded_sectors": 0
    },
    
    # 7. REPRODUCCIÓN
    "reproduction": {
        "active_pregnancies": 0,
        "avg_litter_size": 0.0,
        "fertile_count": 0
    },
    
    # 8. COGNICIÓN Y EMOCIONES
    "cognitive": {
        "avg_cognitive_stress": 0.0,
        "avg_stress": 0.0,
        "avg_happiness": 0.0,
        "avg_energy": 0.0
    },
    
    # 9. GENEALOGÍA
    "genealogy": {
        "active_lineages": 0,
        "extinct_lineages": 0,
        "max_generation": 0
    },
    
    # 10. ESTADO SOCIAL
    "social": {
        "married_count": 0,
        "single_count": 0,
        "divorced_count": 0,
        "orphan_count": 0
    }
}
```

---

### Introspección Genética Automática

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

**Característica clave**: El sistema se adapta automáticamente a nuevos genes añadidos al `Genome` sin necesidad de modificar código.

---

### Bucle Único O(N) de Recolección

```python
for p in alive_persons:
    # 1. Edad y estructura
    total_age_days += p.age
    if p.is_senior:
        snapshot["age_structure"]["seniors"] += 1
    elif p.is_adult:
        snapshot["age_structure"]["adults"] += 1
    else:
        snapshot["age_structure"]["children"] += 1
    
    # 2. Genética
    for gene_name in tracked_genes:
        gene_value = float(getattr(p.genome, gene_name, 0.0))
        gene_sums[gene_name] += gene_value
        gene_variances[gene_name].append(gene_value)
    
    # 3. Epidemiología
    if p.is_sick:
        snapshot["epidemiology"]["sick_count"] += 1
        infection_count = len(p.active_infections)
        total_infections += infection_count
        
        for infection_state in p.active_infections.values():
            family = infection_state.pathogen.family
            pathogen_families[family] += 1
            total_viral_load += infection_state.pathogen.virulence * infection_state.pathogen.transmission
    
    # 4. Cognición
    total_cognitive_stress += p.memory.get("cognitive_stress", 0.0)
    total_stress += p.emotions.get("stress", 0.0)
    total_happiness += p.emotions.get("happiness", 0.5)
    total_energy += p.emotions.get("energy", 1.0)
    
    # 5. Reproducción
    if p.is_pregnant:
        active_pregnancies += 1
        total_litter_size += p.litter_size_gestating
    if p.is_fertile():
        fertile_count += 1
    
    # 6. Estado social
    marital = getattr(p, 'marital_status', 'soltero')
    if marital == 'casado':
        married_count += 1
    elif marital == 'divorciado':
        divorced_count += 1
    else:
        single_count += 1
    
    # Huérfanos
    if len(p.parents) == 0 and len(p.adoptive_parents) == 0 and p.age > 0:
        orphan_count += 1
```

**Optimización**: Un solo bucle O(N) recolecta todas las métricas en lugar de múltiples pasadas.

---

### Cálculos Finales y Normalización

```python
# Edad promedio
snapshot["avg_age_years"] = round((total_age_days / total_pop) / 365.0, 2)

# Genética: medias y varianzas
for gene_name in tracked_genes:
    values = gene_variances[gene_name]
    if values:
        mean_val = gene_sums[gene_name] / len(values)
        variance_val = sum((x - mean_val)**2 for x in values) / len(values)
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
```

---

### Métricas Espaciales

```python
def _calculate_spatial_metrics(self, snapshot, context):
    if hasattr(context, 'pressure_map') and context.pressure_map:
        pressures = list(context.pressure_map.values())
        if pressures:
            snapshot["spatial"]["avg_pressure"] = round(sum(pressures) / len(pressures), 3)
            snapshot["spatial"]["max_pressure"] = round(max(pressures), 3)
            snapshot["spatial"]["overcrowded_sectors"] = sum(1 for p in pressures if p > 1.5)
```

**Interpretación**:
- `avg_pressure`: presión ambiental promedio
- `max_pressure`: zona más densa
- `overcrowded_sectors`: sectores con presión >1.5 (superpoblados)

---

### Métricas Genealógicas

```python
def _calculate_genealogy_metrics(self, snapshot):
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
```

**Interpretación**:
- `active_lineages`: linajes con al menos un miembro vivo
- `extinct_lineages`: linajes completamente extintos
- `max_generation`: profundidad genealógica máxima actual

---

### Gestión de Memoria

```python
# Añadir al historial
self.history.append(snapshot)

# Limitar crecimiento del historial
max_history_size = getattr(self.config.metrics, 'max_history_size', 1000)
if len(self.history) > max_history_size:
    self.history.pop(0)  # Eliminar el snapshot más antiguo
```

**Justificación**: En simulaciones largas (años), el historial podría consumir gigabytes de RAM. El límite configurable previene esto.

---

### Exportación a JSON

```python
def export_to_json(self, filepath="simulation_metrics.json"):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=4, ensure_ascii=False)
        self.logger.info(f"📊 Métricas exportadas correctamente a: {filepath}")
    except IOError as e:
        self.logger.error(f"Error al exportar métricas a JSON: {e}")
```

---

### Acceso al Último Snapshot

```python
def get_latest_metrics(self):
    return self.history[-1] if self.history else {}
```

Útil para dashboards en tiempo real o consultas rápidas.

---

## 🔗 Interacción entre componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                       WorldState                                │
│   (agentes vivos, sus genomas, emociones, enfermedades)         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ lee (observador puro)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MetricsSystem                                 │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  history: List[Dict]  (snapshots multidimensionales)   │    │
│  │  last_snapshot_day: float  (control de intervalo)      │    │
│  │  last_population: int  (para tasa de crecimiento)      │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Métodos principales:                                           │
│    ├── process() → orquesta el ciclo completo                    │
│    ├── _get_tracked_genes() → introspección automática          │
│    ├── _calculate_spatial_metrics() → presión ambiental         │
│    ├── _calculate_genealogy_metrics() → linajes                 │
│    ├── export_to_json() → persistencia externa                  │
│    └── get_latest_metrics() → último snapshot                   │
└──────────┬────────────────────────────────────┬─────────────────┘
           │                                    │
           │ usa                                │ usa (opcional)
           ▼                                    ▼
┌────────────────────┐              ┌──────────────────────┐
│ EnvironmentContext │              │ GenealogySystem      │
│ (doc 04)           │              │ (doc 12)             │
│                    │              │                      │
│ pressure_map       │              │ lineages             │
│ (presión espacial) │              │ registry             │
└────────────────────┘              └──────────────────────┘
```

---

## ⚙️ Configuración relevante

```python
# MetricsConfig (en SimulationConfig)
config.metrics.snapshot_interval_days = 1.0      # Cada día simulado
config.metrics.max_history_size = 1000           # Máximo 1000 snapshots en memoria
```

### Parámetros implícitos (hardcoded)

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| Umbral de superpoblación | 1.5 | Presión >1.5 = overcrowded |
| Precisión de redondeo | 2-6 decimales | Según métrica |
| Conversión días→años | 365.0 | Días por año |

---

## 🧪 Tests del sistema

| Archivo | Cobertura |
|---------|-----------|
| `tests/unit/test_metrics_system.py` | Snapshots, introspección, exportación |
| `tests/integration/test_statistical.py` | Métricas realistas a largo plazo |

---

## 📝 Ejemplos completos

### Ejemplo 1: Snapshot típico de población estable

```python
# Día 1000, población de 150 agentes
snapshot = {
    "day": 1000.0,
    "year": 2.74,
    "population": 150,
    "births_this_tick": 2,
    "deaths_this_tick": 1,
    "population_delta": 1,
    "growth_rate_percent": 0.67,
    
    "age_structure": {
        "children": 35,   # 23%
        "adults": 95,     # 63%
        "seniors": 20     # 13%
    },
    "avg_age_years": 28.5,
    
    "gene_averages": {
        "fertility": 1.15,
        "immunity": 1.08,
        "longevity": 0.95,
        "intelligence": 1.02
    },
    "genetic_diversity": {
        "fertility": 0.12,
        "immunity": 0.15,
        "longevity": 0.08,
        "intelligence": 0.10
    },
    
    "epidemiology": {
        "sick_count": 8,
        "total_infections": 10,
        "avg_pathogens_per_sick": 1.25,
        "active_pathogen_families": {
            "Influenza": 6,
            "Coronavirus": 4
        },
        "total_viral_load": 3.45
    },
    
    "spatial": {
        "avg_pressure": 1.2,
        "max_pressure": 2.8,
        "overcrowded_sectors": 3
    },
    
    "reproduction": {
        "active_pregnancies": 5,
        "avg_litter_size": 1.4,
        "fertile_count": 45
    },
    
    "cognitive": {
        "avg_cognitive_stress": 0.35,
        "avg_stress": 0.42,
        "avg_happiness": 0.58,
        "avg_energy": 0.75
    },
    
    "genealogy": {
        "active_lineages": 12,
        "extinct_lineages": 3,
        "max_generation": 4
    },
    
    "social": {
        "married_count": 60,
        "single_count": 85,
        "divorced_count": 5,
        "orphan_count": 2
    }
}
```

### Ejemplo 2: Detección de epidemia

```python
# Epidemia de influenza afectando al 30% de la población
snapshot["epidemiology"] = {
    "sick_count": 45,           # 30% de 150
    "total_infections": 52,     # Algunos con múltiples infecciones
    "avg_pathogens_per_sick": 1.16,
    "active_pathogen_families": {
        "Influenza": 48,        # Dominante
        "Coronavirus": 4        # Secundario
    },
    "total_viral_load": 18.7    # Alta carga ambiental
}

# Interpretación:
# - 30% de la población enferma
# - Influenza es el patógeno dominante
# - Alta carga viral sugiere propagación activa
# - Posible necesidad de intervención
```

### Ejemplo 3: Población envejecida

```python
# Población con baja natalidad y alta longevidad
snapshot["age_structure"] = {
    "children": 15,    # 10%
    "adults": 70,      # 47%
    "seniors": 65      # 43%
}
snapshot["avg_age_years"] = 45.2

snapshot["reproduction"] = {
    "active_pregnancies": 2,    # Muy bajo
    "avg_litter_size": 1.0,
    "fertile_count": 20         # Pocos fértiles
}

snapshot["cognitive"] = {
    "avg_cognitive_stress": 0.55,  # Alto (preocupación por futuro)
    "avg_stress": 0.48,
    "avg_happiness": 0.52,
    "avg_energy": 0.65           # Bajo (seniors tienen menos energía)
}

# Interpretación:
# - Población envejecida (43% seniors)
# - Baja natalidad (solo 2 embarazos)
# - Estrés cognitivo alto (preocupación demográfica)
# - Riesgo de colapso poblacional futuro
```

### Ejemplo 4: Superpoblación espacial

```python
# Población concentrada en pocas zonas
snapshot["spatial"] = {
    "avg_pressure": 1.8,        # Alta presión promedio
    "max_pressure": 4.5,        # Zona extremadamente densa
    "overcrowded_sectors": 12   # 12 sectores superpoblados
}

snapshot["cognitive"] = {
    "avg_cognitive_stress": 0.72,  # Muy alto
    "avg_stress": 0.68,
    "avg_happiness": 0.45,         # Bajo
    "avg_energy": 0.60
}

snapshot["epidemiology"] = {
    "sick_count": 35,              # Alta enfermedad
    "total_viral_load": 25.3       # Propagación facilitada por densidad
}

# Interpretación:
# - Hacinamiento severo
# - Estrés y enfermedad altos
# - Posible trigger para migración masiva
# - Riesgo de colapso social
```

### Ejemplo 5: Exportación y análisis externo

```python
# Tras 5 años de simulación (1825 días, ~1825 snapshots)
metrics_system.export_to_json("metrics_5years.json")

# Análisis en Python/Jupyter:
import json
import pandas as pd
import matplotlib.pyplot as plt

with open("metrics_5years.json") as f:
    history = json.load(f)

# DataFrame de evolución poblacional
df = pd.DataFrame([
    {
        "day": s["day"],
        "population": s["population"],
        "avg_age": s["avg_age_years"],
        "sick_count": s["epidemiology"]["sick_count"],
        "avg_stress": s["cognitive"]["avg_stress"]
    }
    for s in history
])

# Gráficas
fig, axes = plt.subplots(2, 2, figsize=(12, 8))

# Población
axes[0,0].plot(df["day"], df["population"])
axes[0,0].set_title("Población")

# Edad promedio
axes[0,1].plot(df["day"], df["avg_age"])
axes[0,1].set_title("Edad Promedio")

# Enfermedad
axes[1,0].plot(df["day"], df["sick_count"])
axes[1,0].set_title("Enfermos")

# Estrés
axes[1,1].plot(df["day"], df["avg_stress"])
axes[1,1].set_title("Estrés Promedio")

plt.tight_layout()
plt.show()

# Detectar tendencias
from scipy import stats
slope, intercept, r_value, p_value, std_err = stats.linregress(df["day"], df["population"])
print(f"Tendencia poblacional: {slope*365:.2f} agentes/año (p={p_value:.4f})")
```

### Ejemplo 6: Acceso al último snapshot

```python
# Dashboard en tiempo real
latest = metrics_system.get_latest_metrics()

if latest:
    print(f"Día {latest['day']:.0f} (Año {latest['year']:.2f})")
    print(f"Población: {latest['population']}")
    print(f"Crecimiento: {latest['growth_rate_percent']:+.2f}%")
    print(f"Enfermos: {latest['epidemiology']['sick_count']}")
    print(f"Estrés: {latest['cognitive']['avg_stress']:.2f}")
```

### Ejemplo 7: Comparación de diversidad genética

```python
# Dos poblaciones aisladas
snapshot_A = metrics_A.get_latest_metrics()
snapshot_B = metrics_B.get_latest_metrics()

# Comparar diversidad genética
for gene in ["fertility", "immunity", "longevity"]:
    var_A = snapshot_A["genetic_diversity"][gene]
    var_B = snapshot_B["genetic_diversity"][gene]
    
    print(f"{gene}:")
    print(f"  Población A: varianza = {var_A:.6f}")
    print(f"  Población B: varianza = {var_B:.6f}")
    
    if var_A < 0.01:
        print(f"  ⚠️ Población A tiene baja diversidad en {gene}")
    if var_B < 0.01:
        print(f"  ⚠️ Población B tiene baja diversidad en {gene}")
```

---

## 🚨 Consideraciones y limitaciones

### Principios fundamentales
- **Observador puro**: nunca modifica el estado de los agentes
- **Bucle único O(N)**: eficiencia máxima en recolección
- **Introspección automática**: se adapta a nuevos genes
- **Gestión de memoria**: límite configurable de historial
- **Fuente de verdad temporal única**: `state.world_days_elapsed`
- **Integridad referencial**: filtra agentes recién fallecidos

### Arquitectura

```
TICK DE SIMULACIÓN
   ↓
MetricsSystem.process()
   ├── Control de intervalo
   ├── Filtrado de población viva
   ├── Inicialización de snapshot (10 dimensiones)
   ├── Bucle O(N) de recolección:
   │   ├── Edad y estructura
   │   ├── Genética (introspección)
   │   ├── Epidemiología
   │   ├── Cognición
   │   ├── Reproducción
   │   └── Estado social
   ├── Cálculos finales y normalización
   ├── Métricas espaciales (EnvironmentContext)
   ├── Métricas genealógicas (GenealogySystem)
   ├── Gestión de memoria (pop si excede límite)
   └── Actualización de last_snapshot_day
```

### Optimizaciones de rendimiento

| Optimización | Descripción |
|--------------|-------------|
| Control de intervalo | No procesa cada tick |
| Bucle único O(N) | Una pasada para todas las métricas |
| Introspección cacheada | `_get_tracked_genes` una vez por snapshot |
| Filtrado temprano | Skip agentes en `pending.deaths` |
| `max(1, divisor)` | Evita división por cero |
| Gestión de memoria | `pop(0)` cuando excede límite |

### Limitaciones
- No calcula percentiles (solo medias y varianzas)
- No hace análisis de correlación (eso lo hace `EvolutionEngine`)
- No detecta eventos drásticos (eso lo hace `EvolutionEngine`)
- El historial se pierde al cerrar la simulación (a menos que se exporte)
- No hay métricas de movimiento o migración
- No hay métricas de relaciones sociales complejas (solo estado civil)
- La introspección genética puede incluir propiedades no relevantes

### Errores comunes
- ❌ Asumir que el historial persiste entre ejecuciones (exportar a JSON)
- ❌ No configurar `max_history_size` (consumo de RAM en simulaciones largas)
- ❌ Usar `pending.births` como fuente de nacimientos totales (solo son los del tick)
- ❌ Confundir `population_delta` con tasa de crecimiento (delta es absoluto, rate es %)
- ❌ Asumir que `genealogy_system` siempre está disponible (es opcional)
- ❌ No verificar `hasattr(context, 'pressure_map')` antes de usar métricas espaciales

---

## 🎓 Conceptos clave

### ¿Por qué bucle único O(N)?

**Principio de eficiencia**:
- Múltiples pasadas sobre la población serían O(k×N)
- Con 10 dimensiones, serían 10 pasadas
- Un solo bucle recolecta todo en O(N)
- Crítico para poblaciones grandes (>1000 agentes)

### ¿Por qué introspección automática?

**Principio de extensibilidad**:
- Si añades un nuevo gen al Genome, el MetricsSystem lo detecta automáticamente
- No hay que modificar código del sistema
- El sistema se adapta a nuevas especies o rasgos
- Reduce el acoplamiento entre componentes

### ¿Por qué gestión de memoria?

**Principio de escalabilidad**:
- En simulaciones de años, el historial puede tener miles de snapshots
- Cada snapshot con 10 dimensiones y múltiples genes puede ser ~1KB
- 10000 snapshots = 10MB (manejable)
- 100000 snapshots = 100MB (problemático)
- El límite configurable previene problemas de RAM

### ¿Por qué fuente de verdad temporal única?

**Principio de coherencia**:
- `state.world_days_elapsed` es la fuente autoritativa
- Evita desincronización entre sistemas
- Todos los timestamps son consistentes
- Facilita debugging y análisis

### ¿Por qué filtrar `pending.deaths`?

**Principio de integridad referencial**:
- Los agentes en `pending.deaths` morirán al final del tick
- Incluirlos en métricas sería inconsistente
- Las métricas deben reflejar el estado post-commit
- Evita contar agentes "zombie"

### ¿Por qué métricas espaciales desde `pressure_map`?

**Principio de separación de responsabilidades**:
- El `EnvironmentContext` ya calcula la presión espacial
- El MetricsSystem solo la consume
- No duplica lógica de cálculo
- Mantiene coherencia con otros sistemas

### ¿Por qué genealogía opcional?

**Principio de modularidad**:
- No todas las simulaciones necesitan métricas genealógicas
- La inyección opcional permite configuraciones ligeras
- Si no se proporciona, las métricas permanecen en 0
- Facilita testing y configuraciones mínimas

---

## 📊 Métricas del sistema

| Métrica | Valor |
|---------|-------|
| Archivos del sistema | 1 |
| Dimensiones del snapshot | 10 |
| Atributos del sistema | 5 |
| Métodos principales | 6 |
| Campos por snapshot | ~50 |
| Tests cubriendo métricas | ~10 |

---

## 🔮 Futuras extensiones

### Planificadas
- [ ] Percentiles (P25, P50, P75, P95) en lugar de solo medias
- [ ] Métricas de movimiento y migración
- [ ] Métricas de relaciones sociales complejas
- [ ] Exportación incremental (append-only)

### Posibles
- [ ] Métricas de felicidad por linaje
- [ ] Análisis de segregación espacial
- [ ] Métricas de movilidad social
- [ ] Índices de Gini (desigualdad)
- [ ] Métricas de red social (centralidad, clustering)
- [ ] Análisis de correlación entre dimensiones
- [ ] Detección automática de anomalías
- [ ] Alertas configurables (ej: "alertar si mortalidad >10%")
- [ ] Dashboard web en tiempo real (WebSocket)
- [ ] Integración con Grafana/Prometheus
- [ ] Métricas de sostenibilidad (huella ecológica)
- [ ] Análisis de equidad intergeneracional

---

*Documento: 15_METRICAS.md*
*Versión: 1.0*