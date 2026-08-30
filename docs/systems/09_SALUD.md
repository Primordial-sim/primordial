# 09 - Salud

## 📋 Resumen

El **Sistema de Salud** modela la epidemiología completa del mundo simulado: patógenos con identidad y mutación, fases de infección (expuesto → incubando → contagioso → sintomático → recuperándose), inmunidad innata y adaptativa, contagios por carga viral ambiental y brotes espontáneos. Cada infección es un objeto con vida propia que progresa por fases.

**Filosofía fundamental**: *Las enfermedades son entidades con identidad propia. Los patógenos mutan, las infecciones progresan por fases biológicamente realistas, y la inmunidad es específica por familia y por cepa. El sistema modela la co-evolución huésped-patógeno en tiempo real.*

---

## 🎯 Responsabilidad

**Es responsable de:**
- Derivar capacidades inmunológicas del genoma (`ImmunologicalCapabilities`)
- Modelar patógenos con identidad, familia, generación y mutación (`Pathogen`)
- Gestionar estados de infección con fases (`InfectionState`, `InfectionPhase`)
- Procesar el ciclo de infección por fases (5 fases biológicas)
- Calcular inmunidad específica por familia y por cepa
- Simular contagios entre agentes cercanos (carga viral)
- Gestionar la inmunidad innata y adaptativa
- Generar brotes espontáneos
- Mutar patógenos durante la replicación
- Emitir eventos relacionales durante enfermedades (CARE)
- Almacenar carga viral ambiental por coordenada (`EpidemiologicalMap`)

**NO es responsable de:**
- ❌ Calcular mortalidad por enfermedades (eso lo hace `MortalitySystem`, documento 10)
- ❌ Procesar emociones por enfermedades (eso lo hace `CognitiveMemorySystem`, documento 08)
- ❌ Decidir aislamiento por enfermedad (eso lo hace `FreeWillSystem`, documento 08)
- ❌ Calcular el coste energético de la enfermedad (eso lo hace `TemporalSystem`, documento 14)

---

## 🌍 Equivalencia con la vida real

| Concepto del sistema | Equivalencia en la vida real | Unidad |
|---------------------|-----------------------------|--------|
| **Pathogen** | Cepa viral/bacteriana específica | Microorganismo |
| **InfectionState** | Estado de infección de un huésped | Diagnóstico |
| **InfectionPhase** | Fase clínica de la infección | Etapa de la enfermedad |
| **Family** | Familia de patógenos (ej: Influenza) | Taxonomía |
| **Generation** | Generación viral | Mutación acumulada |
| **Virulence** | Capacidad de propagación | R0 (tasa básica de reproducción) |
| **Lethality** | Probabilidad de muerte | Tasa de mortalidad |
| **Transmission** | Tasa de contagio | Infectividad |
| **Immunity (innate)** | Inmunidad innata | Barreras naturales |
| **Immunity (acquired)** | Inmunidad adquirida | Anticuerpos |
| **Cross-immunity** | Inmunidad cruzada | Protección entre familias |
| **Viral load** | Carga viral ambiental | Concentración de patógenos |
| **EpidemiologicalMap** | Mapa epidemiológico | Cartografía de contagios |

---

## 📁 Archivos que lo componen

| Archivo | Clase principal | Responsabilidad |
|---------|-----------------|-----------------|
| `systems/diseases/disease_system.py` | `DiseaseSystem` | Motor epidemiológico |
| `systems/diseases/pathogen.py` | `Pathogen`, `InfectionState`, `InfectionPhase` | Modelo de patógenos y estados |
| `systems/diseases/immunological_capabilities.py` | `ImmunologicalCapabilities` | Capacidades inmunológicas derivadas |
| `systems/environment/epidemiological_map.py` | `EpidemiologicalMap` | Estructura espacial de carga viral |

---

## 🔄 Flujo de ejecución completo

```
┌─────────────────────────────────────────────────────────────────┐
│       FASE 0: PROPAGACIÓN DE CARGA VIRAL (EpidemiologicalMap)   │
│                                                                 │
│ EpidemiologicalMap:                                             │
│  ├── Para cada agente enfermo y sintomático:                    │
│  │   └── add_viral_load(x, y, amount) en su posición            │
│  ├── decay_viral_load(factor=0.95) en todo el mapa              │
│  └── Las celdas con carga < 0.01 se eliminan automáticamente    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│       FASE 1: PROGRESIÓN DE INFECCIONES                         │
│                                                                 │
│ DiseaseSystem:                                                  │
│  ├── Para cada agente vivo con active_infections:               │
│  │   └── Para cada InfectionState:                              │
│  │       ├── advance(delta_days):                               │
│  │       │   ├── EXPOSED → INCUBATING (tras período latente)    │
│  │       │   ├── INCUBATING → CONTAGIOUS (tras incubación)      │
│  │       │   ├── CONTAGIOUS → SYMPTOMATIC (con probabilidad)    │
│  │       │   └── SYMPTOMATIC → RECOVERING (cuando se cura)      │
│  │       ├── Actualizar health_state según fase                 │
│  │       └── Si RECOVERING completada:                          │
│  │           ├── pending.register_recovery(entity_id, pathogen) │
│  │           ├── Generar inmunidad (familia + cepa)             │
│  │           └── Eliminar InfectionState                        │
│  │                                                              │
│  └── Decaimiento de inmunidad (decay_immunity)                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│       FASE 2: CONTAGIOS ENTRE AGENTES                           │
│                                                                 │
│ DiseaseSystem:                                                  │
│  ├── Para cada agente contagioso (fase CONTAGIOUS o SYMPTOMATIC):│
│  │   ├── Usar SpatialGrid para encontrar vecinos cercanos       │
│  │   ├── Para cada vecino susceptible:                          │
│  │   │   ├── Calcular probabilidad de contagio:                 │
│  │   │   │   ├── Base: pathogen.transmission                    │
│  │   │   │   ├── × (1 - inmunidad_específica)                   │
│  │   │   │   ├── × distancia_factor                             │
│  │   │   │   └── × tiempo_contacto                              │
│  │   │   ├── Si random < probabilidad:                          │
│  │   │   │   ├── Mutar patógeno (10% probabilidad)              │
│  │   │   │   └── pending.register_infection(vecino, new_pathogen)│
│  │   │   └── Emitir evento CARE si es pareja/familia            │
│  │   └── Incrementar carga viral ambiental                      │
│  └── Si vecino ya tiene infección de la misma familia:          │
│      └── Reemplazar por la nueva cepa (si es más virulenta)     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│       FASE 3: BROTES ESPONTÁNEOS                                │
│                                                                 │
│ DiseaseSystem:                                                  │
│  ├── Para cada sector (grid 10x10):                             │
│  │   ├── Calcular densidad poblacional                          │
│  │   ├── Calcular riesgo de brote:                              │
│  │   │   ├── Base: 0.0001 por día                               │
│  │   │   ├── × densidad_poblacional                             │
│  │   │   └── × estacion_factor (invierno = ×3)                  │
│  │   └── Si random < riesgo:                                    │
│  │       ├── Crear nuevo Pathogen aleatorio                     │
│  │       ├── Infectar 1-3 agentes del sector                    │
│  │       └── Log de brote con emoji 🚨                          │
│  └── Emitir eventos para métricas                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes del Sistema

---

### 0. EpidemiologicalMap - Estructura Espacial de Carga Viral

**📁 Archivo**: `systems/environment/epidemiological_map.py`
**🌍 Equivalencia real**: La concentración ambiental de patógenos en cada punto del mapa, como la carga viral en el aire o superficies.

#### Propósito

El mapa epidemiológico almacena la **carga viral ambiental** por coordenada. Es usado por:
- `MovementSystem`: evitar zonas de alta carga viral
- `MigrationSystem`: validar destinos migratorios
- `DiseaseSystem`: propagación de patógenos

#### Implementación

```python
class EpidemiologicalMap:
    """Almacén de datos (Sparse Grid) para cargas virales."""
    
    def __init__(self, max_viral_load: float):
        self.grid = defaultdict(float)  # Sparse grid (ahorra memoria)
        self.max_viral_load = max_viral_load
```

**Diseño clave**: Usa `defaultdict(float)` como **sparse grid**, lo que significa que solo se almacenan las coordenadas con carga viral > 0. Las zonas seguras no consumen memoria.

#### Métodos

| Método | Descripción |
|--------|-------------|
| `add_viral_load(x, y, amount)` | Incrementa carga viral (topada al máximo) |
| `get_viral_load(x, y)` | Obtiene carga viral de una coordenada |
| `decay_viral_load(factor)` | Aplica disipación atmosférica global |

#### Algoritmos

**Añadir carga viral (topada al máximo):**
```python
def add_viral_load(self, x, y, amount):
    coord = (int(x), int(y))
    new_val = self.grid[coord] + amount
    self.grid[coord] = min(new_val, self.max_viral_load)
```

**Decaimiento con limpieza automática:**
```python
def decay_viral_load(self, factor):
    keys_to_delete = []
    for coord in self.grid:
        self.grid[coord] *= factor
        if self.grid[coord] < 0.01:
            keys_to_delete.append(coord)
    
    for coord in keys_to_delete:
        del self.grid[coord]
```

#### Ejemplos

```python
from systems.environment.epidemiological_map import EpidemiologicalMap

# Crear mapa con límite biológico
ep_map = EpidemiologicalMap(max_viral_load=10.0)

# Agregar carga viral (ej: agente contagioso en la zona)
ep_map.add_viral_load(x=50, y=50, amount=1.5)
ep_map.add_viral_load(x=50, y=50, amount=2.0)
print(ep_map.get_viral_load(50, 50))  # 3.5

# Agregar más de lo permitido → topado al máximo
ep_map.add_viral_load(x=50, y=50, amount=20.0)
print(ep_map.get_viral_load(50, 50))  # 10.0 (max_viral_load)

# Decaimiento natural (ej: cada tick)
ep_map.decay_viral_load(factor=0.95)  # 5% de disipación por tick
print(ep_map.get_viral_load(50, 50))  # 9.5
```

#### Uso en otros sistemas

```python
# En MovementSystem: evitar zonas peligrosas
viral_load = state.epidemiological_map.get_viral_load(x, y)
score -= viral_load * 15.0  # Penalización fuerte

# En MigrationSystem: validar destinos
if viral_load > 3.0:
    return False  # Destino no viable

# En DiseaseSystem: propagación entre vecinos
for neighbor in nearby_agents:
    if ep_map.get_viral_load(neighbor.x, neighbor.y) > threshold:
        # Riesgo de contagio ambiental
        ...
```

#### Consideraciones

- **Sparse grid**: solo celdas con carga viral > 0 ocupan memoria
- **Limpieza automática**: valores insignificantes se eliminan
- **Tope biológico**: hay un máximo de carga viral posible
- **Decaimiento continuo**: la carga se disipa naturalmente
- **No persistente entre sesiones**: parte del estado del mundo

---

### 1. ImmunologicalCapabilities - Capacidades Inmunológicas

**📁 Archivo**: `systems/diseases/immunological_capabilities.py`
**🌍 Equivalencia real**: El sistema inmunológico del organismo: innato, adaptativo, memoria inmunológica.

#### Atributos

| Atributo | Tipo | Descripción | Condición |
|----------|------|-------------|-----------|
| `has_innate_immunity` | `bool` | Inmunidad innata | `immunity > 0.1` |
| `has_adaptive_immunity` | `bool` | Inmunidad adaptativa | `adaptive_immunity > 0.3` |
| `can_form_immunological_memory` | `bool` | Memoria inmunológica | `adaptive_immunity > 0.5` |
| `has_cross_immunity` | `bool` | Inmunidad cruzada | `adaptive_immunity > 0.7` |
| `innate_strength` | `float` | Fuerza innata | `immunity` base |
| `adaptive_strength` | `float` | Fuerza adaptativa | `adaptive_immunity` base |
| `memory_duration` | `float` | Duración de memoria | Calculado |

#### Ejemplos

```python
# Humano: inmunidad completa
human_caps = ImmunologicalCapabilities.from_genome(human_genome)
human_caps.has_innate_immunity           # True
human_caps.has_adaptive_immunity         # True
human_caps.can_form_immunological_memory # True
human_caps.has_cross_immunity            # True

# Pez: inmunidad innata básica
fish_caps = ImmunologicalCapabilities.from_genome(fish_genome)
fish_caps.has_innate_immunity            # True
fish_caps.has_adaptive_immunity          # False (o limitada)
fish_caps.can_form_immunological_memory  # False

# Bacteria: sin inmunidad
bacteria_caps = ImmunologicalCapabilities.from_genome(bacteria_genome)
bacteria_caps.has_innate_immunity        # False
```

---

### 2. Pathogen - Modelo de Patógeno

**📁 Archivo**: `systems/diseases/pathogen.py`
**🌍 Equivalencia real**: Una cepa específica de virus o bacteria con identidad propia.

#### Atributos

| Atributo | Tipo | Rango | Descripción |
|----------|------|-------|-------------|
| `pathogen_id` | `str` | - | ID único (ej: "Influenza_000001") |
| `family` | `str` | - | Familia (ej: "Influenza", "Coronavirus") |
| `generation` | `int` | ≥ 1 | Generación (mutaciones acumuladas) |
| `virulence` | `float` | [0.1, 2.0] | Capacidad de propagación |
| `lethality` | `float` | [0.0, 1.0] | Probabilidad de muerte |
| `transmission` | `float` | [0.1, 2.0] | Tasa de contagio |
| `incubation_days` | `float` | [1, 30] | Período de incubación |
| `symptomatic_probability` | `float` | [0.0, 1.0] | Probabilidad de síntomas |
| `recovery_days` | `float` | [3, 30] | Días hasta recuperación |
| `mutation_rate` | `float` | [0.0, 1.0] | Tasa de mutación |

#### Métodos

| Método | Descripción |
|--------|-------------|
| `create_random_variant(family)` | Crea variante aleatoria de una familia |
| `mutate()` | Genera nueva generación con mutaciones |
| `get_family_similarity(fam1, fam2)` | Similitud entre familias (0-1) |
| `get_related_families(family, min_sim)` | Familias relacionadas |

#### Familias de patógenos

| Familia | Características |
|---------|-----------------|
| `Influenza` | Alta transmisión, síntomas comunes |
| `Coronavirus` | Transmisión media, letalidad variable |
| `CommonCold` | Baja letalidad, síntomas leves |
| `Gastrointestinal` | Transmisión alta, afecta energía |
| `SkinInfection` | Transmisión baja, visible |
| `Poxvirus` | Letalidad media, inmunidad duradera |
| `Bacterial` | Antibióticos podrían ayudar (futuro) |

#### Mutación

```python
def mutate(self) -> "Pathogen":
    """Genera nueva cepa con mutaciones aleatorias."""
    new_generation = self.generation + 1
    
    # Mutar atributos con pequeñas variaciones
    new_virulence = max(0.1, min(2.0, self.virulence + random.gauss(0, 0.1)))
    new_lethality = max(0.0, min(1.0, self.lethality + random.gauss(0, 0.05)))
    new_transmission = max(0.1, min(2.0, self.transmission + random.gauss(0, 0.1)))
    
    new_pathogen_id = f"{self.family}_{new_generation:06d}"
    
    return Pathogen(
        pathogen_id=new_pathogen_id,
        family=self.family,
        generation=new_generation,
        virulence=new_virulence,
        lethality=new_lethality,
        transmission=new_transmission,
        # ... resto igual
    )
```

#### Similitud entre familias

```python
# Matriz de similitud (hardcoded)
FAMILY_SIMILARITY = {
    ("Influenza", "Coronavirus"): 0.3,  # Virus respiratorios similares
    ("Coronavirus", "CommonCold"): 0.25,
    ("Gastrointestinal", "Gastrointestinal"): 1.0,
    # ... más pares
}

# Si dos familias son similares, hay inmunidad cruzada
```

---

### 3. InfectionState - Estado de Infección

**📁 Archivo**: `systems/diseases/pathogen.py` (incluido)
**🌍 Equivalencia real**: El estado clínico de un paciente con una enfermedad específica.

#### Fases de infección (enum `InfectionPhase`)

| Fase | Valor | Descripción | Contagioso | Síntomas |
|------|-------|-------------|------------|----------|
| `EXPOSED` | Expuesto | Recién infectado, sin actividad viral | ❌ | ❌ |
| `INCUBATING` | Incubando | Virus replicándose, sin síntomas | ⚠️ Baja | ❌ |
| `CONTAGIOUS` | Contagioso | Alta carga viral, puede infectar | ✅ | ⚠️ Leves |
| `SYMPTOMATIC` | Sintomático | Síntomas visibles, enfermedad activa | ✅ | ✅ |
| `RECOVERING` | Recuperándose | Sistema inmune ganando, bajando carga | ⚠️ Baja | ⚠️ Residuales |

#### Atributos de `InfectionState`

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `pathogen` | `Pathogen` | Patógeno causante |
| `phase` | `InfectionPhase` | Fase actual |
| `days_in_phase` | `float` | Días en la fase actual |
| `total_days_infected` | `float` | Días totales infectado |
| `is_asymptomatic` | `bool` | Si será asintomático |
| `viral_load` | `float` | Carga viral actual |

#### Transiciones de fase

```python
def advance(self, delta_days):
    self.days_in_phase += delta_days
    self.total_days_infected += delta_days
    
    if self.phase == InfectionPhase.EXPOSED:
        if self.days_in_phase >= 1.0:  # 1 día expuesto
            self._transition_to(InfectionPhase.INCUBATING)
    
    elif self.phase == InfectionPhase.INCUBATING:
        if self.days_in_phase >= self.pathogen.incubation_days:
            self._transition_to(InfectionPhase.CONTAGIOUS)
    
    elif self.phase == InfectionPhase.CONTAGIOUS:
        # Probabilidad de volverse sintomático
        if self.days_in_phase >= 2.0:
            if random.random() < self.pathogen.symptomatic_probability:
                self._transition_to(InfectionPhase.SYMPTOMATIC)
            elif self.days_in_phase >= 5.0:
                # Asintomático: recuperación más rápida
                self._transition_to(InfectionPhase.RECOVERING)
    
    elif self.phase == InfectionPhase.SYMPTOMATIC:
        # Duración variable de síntomas
        if self.days_in_phase >= self.pathogen.recovery_days * 0.7:
            self._transition_to(InfectionPhase.RECOVERING)
    
    elif self.phase == InfectionPhase.RECOVERING:
        if self.days_in_phase >= self.pathogen.recovery_days * 0.3:
            # Listo para ser curado por DiseaseSystem
            self.is_cured = True
```

#### Viral load dinámico

```python
# La carga viral varía según la fase
if self.phase == InfectionPhase.EXPOSED:
    self.viral_load = 0.0
elif self.phase == InfectionPhase.INCUBATING:
    self.viral_load = 0.3 * self.pathogen.transmission
elif self.phase == InfectionPhase.CONTAGIOUS:
    self.viral_load = 1.0 * self.pathogen.transmission  # Máximo
elif self.phase == InfectionPhase.SYMPTOMATIC:
    self.viral_load = 0.8 * self.pathogen.transmission
elif self.phase == InfectionPhase.RECOVERING:
    self.viral_load = 0.2 * self.pathogen.transmission  # Bajando
```

---

### 4. DiseaseSystem - Motor Epidemiológico

**📁 Archivo**: `systems/diseases/disease_system.py`
**🌍 Equivalencia real**: El sistema de salud pública que monitorea y procesa epidemias.

#### Entradas

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `state` | `WorldState` | Estado del mundo |
| `pending` | `PendingChanges` | Búfer transaccional |
| `delta_days` | `float` | Días transcurridos |
| `context` | `EnvironmentContext` | Contexto ambiental |
| `spatial_grid` | `SpatialGrid` | Grid espacial para búsquedas |
| `epidemiological_map` | `EpidemiologicalMap` | Mapa de carga viral |
| `relationship_engine` | `RelationshipExperienceEngine` | Motor de eventos |

#### Flujo interno

```python
def process(self, state, pending, delta_days, context):
    # 1. PROPAGACIÓN DE CARGA VIRAL AMBIENTAL
    for person in state.get_all_persons():
        if person.is_symptomatic:
            for infection in person.active_infections.values():
                if infection.phase in (CONTAGIOUS, SYMPTOMATIC):
                    self.epidemiological_map.add_viral_load(
                        person.x, person.y, 
                        infection.viral_load * delta_days
                    )
    
    # Decaimiento natural
    self.epidemiological_map.decay_viral_load(factor=0.95)
    
    # 2. PROGRESIÓN DE INFECCIONES
    for person in state.get_all_persons():
        if not person.active_infections:
            continue
        
        for pathogen_id, infection in list(person.active_infections.items()):
            old_phase = infection.phase
            infection.advance(delta_days)
            
            # Actualizar estado de salud
            if infection.phase == SYMPTOMATIC and old_phase != SYMPTOMATIC:
                pending.register_emotion_update(person.entity_id, "stress", 0.2)
                pending.register_emotion_update(person.entity_id, "energy", -0.3)
            
            # Si se curó
            if getattr(infection, 'is_cured', False):
                pending.register_recovery(person.entity_id, pathogen_id)
                self._generate_immunity(person, infection.pathogen)
                del person.active_infections[pathogen_id]
    
    # 3. DECADENCIA DE INMUNIDAD
    for person in state.get_all_persons():
        person.decay_immunity(delta_days)
    
    # 4. CONTAGIOS ENTRE AGENTES
    for person in state.get_all_persons():
        if not person.is_sick:
            continue
        
        for infection in person.active_infections.values():
            if infection.phase not in (CONTAGIOUS, SYMPTOMATIC):
                continue
            
            # Buscar vecinos cercanos con SpatialGrid
            nearby = self.spatial_grid.get_nearby_agents(person, radius=5.0)
            
            for neighbor in nearby:
                if self._is_susceptible(neighbor, infection.pathogen):
                    contagion_prob = self._calculate_contagion_probability(
                        person, neighbor, infection
                    )
                    if random.random() < contagion_prob:
                        # Mutar con probabilidad
                        new_pathogen = infection.pathogen
                        if random.random() < infection.pathogen.mutation_rate:
                            new_pathogen = infection.pathogen.mutate()
                        
                        pending.register_infection(neighbor.entity_id, new_pathogen)
    
    # 5. BROTES ESPONTÁNEOS
    self._generate_spontaneous_outbreaks(state, pending, context)
```

#### Cálculo de probabilidad de contagio

```python
def _calculate_contagion_probability(self, source, target, infection):
    pathogen = infection.pathogen
    
    # Base: transmisión del patógeno
    base_prob = pathogen.transmission * 0.05  # Normalizar
    
    # Distancia (más cerca = más contagioso)
    dist = math.sqrt((source.x - target.x)**2 + (source.y - target.y)**2)
    distance_factor = max(0.0, 1.0 - dist / 5.0)
    
    # Inmunidad del target
    immunity = target.get_specific_immunity(pathogen)
    immunity_factor = max(0.0, 1.0 - immunity / 3.0)
    
    # Fase de la infección
    if infection.phase == SYMPTOMATIC:
        phase_factor = 1.0
    elif infection.phase == CONTAGIOUS:
        phase_factor = 0.7
    else:
        phase_factor = 0.2
    
    return base_prob * distance_factor * immunity_factor * phase_factor
```

#### Generación de inmunidad post-recuperación

```python
def _generate_immunity(self, person, pathogen):
    # Inmunidad por cepa (específica)
    person._strain_immunity[pathogen.pathogen_id] = 0.8  # Alta
    
    # Metadatos de la cepa
    person._strain_metadata[pathogen.pathogen_id] = {
        "family": pathogen.family,
        "generation": pathogen.generation,
        "virulence": pathogen.virulence,
        "transmission": pathogen.transmission,
        "lethality": pathogen.lethality,
    }
    
    # Inmunidad por familia (parcial)
    current_family_immunity = person._immune_memory.get(pathogen.family, 0.0)
    person._immune_memory[pathogen.family] = min(
        1.5, 
        current_family_immunity + 0.4
    )
```

#### Generación de brotes espontáneos

```python
def _generate_spontaneous_outbreaks(self, state, pending, context):
    # Dividir el mapa en sectores 10x10
    for sector_x in range(0, 100, 10):
        for sector_y in range(0, 100, 10):
            # Calcular densidad poblacional en el sector
            density = self._calculate_sector_density(sector_x, sector_y, state)
            
            # Riesgo base muy bajo
            outbreak_risk = 0.0001 * density
            
            # Estación (invierno = 3x más probabilidad)
            if context.current_season == Season.WINTER:
                outbreak_risk *= 3.0
            
            if random.random() < outbreak_risk * delta_days:
                # Crear nuevo patógeno
                family = random.choice([
                    "Influenza", "Coronavirus", "CommonCold",
                    "Gastrointestinal"
                ])
                new_pathogen = Pathogen.create_random_variant(family)
                
                # Infectar 1-3 agentes del sector
                agents_in_sector = self._get_agents_in_sector(
                    sector_x, sector_y, state
                )
                if agents_in_sector:
                    victims = random.sample(
                        agents_in_sector,
                        min(3, len(agents_in_sector))
                    )
                    for victim in victims:
                        pending.register_infection(victim.entity_id, new_pathogen)
                    
                    self.logger.warning(
                        f"🚨 Brote de {family} en sector ({sector_x},{sector_y}): "
                        f"{len(victims)} infectados"
                    )
```

---

## 🔗 Interacción entre componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                    GENOMA (fuente de verdad)                    │
│   immunity, adaptive_immunity                                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ consultado por
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│         ImmunologicalCapabilities (inmutable, derivada)         │
│   - has_innate_immunity, has_adaptive_immunity                  │
│   - can_form_immunological_memory, has_cross_immunity           │
└──────────────────────────┬──────────────────────────────────────┘
                           │ usado por
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DiseaseSystem                                │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 1. Propagación de carga viral ambiental                 │    │
│  │    └── EpidemiologicalMap.add_viral_load()              │    │
│  │    └── EpidemiologicalMap.decay_viral_load()            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 2. Progresión de infecciones                            │    │
│  │    └── InfectionState.advance()                         │    │
│  │    └── InfectionPhase: EXPOSED→INCUBATING→CONTAGIOUS    │    │
│  │                              →SYMPTOMATIC→RECOVERING    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 3. Contagios entre agentes                              │    │
│  │    └── SpatialGrid.get_nearby_agents()                  │    │
│  │    └── Pathogen.mutate() (10% probabilidad)             │    │
│  │    └── pending.register_infection()                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 4. Brotes espontáneos                                   │    │
│  │    └── Pathogen.create_random_variant()                 │    │
│  │    └── Infectar 1-3 agentes del sector                  │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PendingChanges                               │
│   - .infections: List[Tuple[entity_id, Pathogen]]               │
│   - .recoveries: List[Tuple[entity_id, pathogen_id]]            │
│   - .emotion_updates: Dict[entity_id, Dict[str, float]]         │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuración relevante

```python
# DiseaseConfig (en SimulationConfig)
config.diseases.base_outbreak_risk = 0.0001
config.diseases.winter_multiplier = 3.0
config.diseases.mutation_rate = 0.1
config.diseases.viral_load_decay = 0.95
config.diseases.max_viral_load = 10.0
config.diseases.contact_radius = 5.0
config.diseases.immunity_decay_rate = 0.001
```

### Parámetros hardcodeados importantes

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| Duración EXPOSED | 1 día | Período de latencia |
| Probabilidad asintomático | `1 - symptomatic_probability` | Variabilidad clínica |
| Factor inmunidad cruzada | 0.3 | Protección parcial entre familias |
| Inmunidad por cepa post-recuperación | 0.8 | Alta protección específica |
| Inmunidad por familia post-recuperación | 0.4 | Protección parcial |
| Máximo inmunidad por cepa | 2.0 | Evita inmunidad infinita |
| Máximo inmunidad por familia | 1.5 | Evita inmunidad infinita |

---

## 🧪 Tests del sistema

| Archivo | Cobertura |
|---------|-----------|
| `tests/unit/test_dessease_system.py` | DiseaseSystem completo (nota: typo en nombre) |
| `tests/unit/test_pathogen.py` | Pathogen, mutación, familias |
| `tests/unit/test_immunological_capabilities.py` | Capacidades inmunológicas |
| `tests/integration/test_statistical.py` | Epidemiología a largo plazo |

---

## 📝 Ejemplos completos

### Ejemplo 1: Ciclo de vida completo de una infección

```python
# Día 0: Agente 101 se expone a Influenza
pathogen = Pathogen.create_random_variant("Influenza")
# pathogen.pathogen_id = "Influenza_000042"
# pathogen.virulence = 1.3
# pathogen.lethality = 0.15
# pathogen.transmission = 1.1

# DiseaseSystem registra la infección
pending.register_infection(101, pathogen)

# Día 0-1: Fase EXPOSED
infection = person.active_infections["Influenza_000042"]
print(infection.phase)  # InfectionPhase.EXPOSED
print(person.is_sick)   # False (aún no se considera enfermo)

# Día 1-5: Fase INCUBATING
infection.advance(delta_days=4.0)
print(infection.phase)  # InfectionPhase.INCUBATING
print(infection.viral_load)  # 0.3 * 1.1 = 0.33

# Día 5-7: Fase CONTAGIOUS
infection.advance(delta_days=2.0)
print(infection.phase)  # InfectionPhase.CONTAGIOUS
print(infection.viral_load)  # 1.0 * 1.1 = 1.1 (máximo)
# En esta fase puede contagiar a vecinos
# Emite carga viral al EpidemiologicalMap

# Día 7-10: Fase SYMPTOMATIC (si symptomatic_probability lo permite)
# pending.register_emotion_update(101, "stress", 0.2)
# pending.register_emotion_update(101, "energy", -0.3)
print(person.is_symptomatic)  # True
print(person.health_state)    # "enfermo"

# Día 10-13: Fase RECOVERING
infection.advance(delta_days=3.0)
print(infection.phase)  # InfectionPhase.RECOVERING
print(infection.viral_load)  # 0.2 * 1.1 = 0.22

# Día 13: Curación
# pending.register_recovery(101, "Influenza_000042")
# person._strain_immunity["Influenza_000042"] = 0.8
# person._immune_memory["Influenza"] += 0.4
# Eliminada de active_infections
```

### Ejemplo 2: Contagio con mutación

```python
# Agente 101 tiene Influenza_000042 en fase SYMPTOMATIC
# Agente 202 está a 2 tiles de distancia

# DiseaseSystem evalúa contagio:
base_prob = 1.1 * 0.05 = 0.055
distance_factor = 1 - (2/5) = 0.6
immunity_factor = 1 - (0.3/3) = 0.9  # inmunidad base del target
phase_factor = 1.0  # SYMPTOMATIC

contagion_prob = 0.055 * 0.6 * 0.9 * 1.0 = 0.0297 (~3%)

if random.random() < 0.0297:
    # ¡Contagio!
    if random.random() < 0.1:  # 10% probabilidad de mutación
        new_pathogen = pathogen.mutate()
        # new_pathogen.pathogen_id = "Influenza_000043"
        # new_pathogen.generation = 43
        # new_pathogen.virulence = 1.32 (ligero cambio)
    else:
        new_pathogen = pathogen  # Misma cepa
    
    pending.register_infection(202, new_pathogen)
```

### Ejemplo 3: Inmunidad cruzada entre familias

```python
# Agente 101 se recuperó de Influenza_000042
# person._immune_memory["Influenza"] = 0.4

# Nuevo patógeno: Coronavirus_000015
coronavirus = Pathogen.create_random_variant("Coronavirus")

# Calcular inmunidad contra Coronavirus
immunity = person.get_specific_immunity(coronavirus)

# Componentes:
# - base_innate: genome.immunity (ajustada por energía)
# - genetic_specific: inmunidad genética específica a Coronavirus
# - acquired_bonus: 0 (nunca infectado por Coronavirus)
# - cross_immunity: 0.4 (Influenza) * 0.3 (similitud) * 0.3 (factor)
#                 = 0.036 (inmunidad cruzada pequeña)
# - strain_immunity: 0 (nunca infectado por esta cepa)

# Total: ~0.036 de inmunidad adicional por infección previa
# La inmunidad cruzada es débil pero significativa
```

### Ejemplo 4: Propagación de carga viral ambiental

```python
# Tick con 5 agentes sintomáticos en diferentes ubicaciones
for person in sick_agents:
    for infection in person.active_infections.values():
        if infection.phase in (CONTAGIOUS, SYMPTOMATIC):
            ep_map.add_viral_load(
                person.x, person.y,
                infection.viral_load * delta_days
            )

# Decaimiento
ep_map.decay_viral_load(factor=0.95)

# MovementSystem consulta el mapa al evaluar celdas:
viral_load = ep_map.get_viral_load(candidate_x, candidate_y)
score -= viral_load * 15.0  # Penalización fuerte

# MigrationSystem valida destinos:
if ep_map.get_viral_load(target_x, target_y) > 3.0:
    return False  # Destino no viable

# Con el tiempo, zonas muy transitadas por enfermos
# acumulan alta carga viral, creando "zonas rojas"
```

### Ejemplo 5: Brote espontáneo

```python
# Sector (50, 50) con alta densidad poblacional
# densidad = 25 agentes en el sector

# Cálculo de riesgo
outbreak_risk = 0.0001 * 25 = 0.0025 (0.25% por día)
# En invierno: 0.0025 * 3.0 = 0.0075 (0.75% por día)

if random.random() < 0.0075:
    # ¡Brote!
    family = "Influenza"  # aleatorio
    new_pathogen = Pathogen.create_random_variant("Influenza")
    
    # Seleccionar 3 agentes aleatorios del sector
    victims = random.sample(agents_in_sector, 3)
    
    for victim in victims:
        pending.register_infection(victim.entity_id, new_pathogen)
    
    logger.warning(f"🚨 Brote de Influenza en sector (50,50): 3 infectados")
    
    # A partir de aquí, los 3 infectados progresarán por fases
    # y contagiarán a sus vecinos
```

### Ejemplo 6: Decaimiento de inmunidad

```python
# Agente se recuperó de Influenza_000042 hace 365 días
# person._strain_immunity["Influenza_000042"] = 0.8 (inicial)
# person._immune_memory["Influenza"] = 0.4 (inicial)

# Cada día:
decay_rate = 0.001
strain_decay = exp(-0.001 * 0.5 * 365) = exp(-0.1825) ≈ 0.833
family_decay = exp(-0.001 * 365) = exp(-0.365) ≈ 0.694

# Después de 365 días:
# strain_immunity = 0.8 * 0.833 ≈ 0.666 (baja lentamente)
# immune_memory = 0.4 * 0.694 ≈ 0.278 (baja más rápido)

# La inmunidad por cepa dura más que la de familia
# Tras ~3 años, la inmunidad decae significativamente
```

---

## 🚨 Consideraciones y limitaciones

### Principios fundamentales
- **Patógenos con identidad**: cada cepa es un objeto único
- **Fases biológicas realistas**: EXPOSED → INCUBATING → CONTAGIOUS → SYMPTOMATIC → RECOVERING
- **Inmunidad multinivel**: innata, adquirida, por familia, por cepa, cruzada
- **Mutación viral**: los patógenos evolucionan al transmitirse
- **Carga viral ambiental**: EpidemiologicalMap modela contaminación ambiental
- **Brotes emergentes**: surgen naturalmente en zonas densas

### Arquitectura de decisión

```
GENOMA
   ↓
ImmunologicalCapabilities (qué puede inmunizar)
   ↓
DiseaseSystem (motor epidemiológico)
   ├── EpidemiologicalMap (carga ambiental)
   ├── SpatialGrid (búsquedas eficientes)
   ├── InfectionState (progresión)
   └── Pathogen (modelo viral)
   ↓
PendingChanges
   ↓
WorldState.apply_commit()
```

### Optimizaciones de rendimiento

| Optimización | Archivo | Beneficio |
|--------------|---------|-----------|
| SpatialGrid para contagios | DiseaseSystem | Búsquedas O(k) vs O(N) |
| Sparse grid en EpidemiologicalMap | EpidemiologicalMap | Solo celdas activas |
| Limpieza automática de carga viral | EpidemiologicalMap | Evita acumulación infinita |
| Decaimiento por lotes | DiseaseSystem | Un cálculo para todos |
| Early return si sin infecciones | DiseaseSystem | Skip agentes sanos |

### Limitaciones
- No hay tratamientos médicos (antibióticos, antivirales)
- No hay vacunas (inmunización preventiva)
- No hay cuarentenas forzadas
- No hay transmisión por vectores (mosquitos, etc.)
- No hay enfermedades crónicas (todas se curan)
- La mutación es aleatoria (no hay selección viral)
- No hay enfermedades genéticas
- No hay resistencia antibiótica (porque no hay antibióticos)

### Errores comunes
- ❌ Asumir que `is_sick` significa síntomas visibles (usar `is_symptomatic`)
- ❌ Modificar `active_infections` directamente (usar `infect()` y `recover()`)
- ❌ Olvidar el `decay_immunity()` (inmunidad eterna)
- ❌ No considerar inmunidad cruzada (protección entre familias)
- ❌ Confundir `strain_immunity` con `immune_memory` (cepa vs familia)
- ❌ Asumir que todos los patógenos son iguales (tienen identidad propia)
- ❌ Olvidar propagar carga viral al `EpidemiologicalMap`

---

## 🎓 Conceptos clave

### ¿Por qué patógenos con identidad?

**Principio de epidemiología real**:
- Cada cepa viral es única
- Las mutaciones crean nuevas cepas
- La inmunidad es específica por cepa
- Permite rastrear brotes y evolución viral
- Más realista que "el agente tiene gripe"

### ¿Por qué 5 fases biológicas?

**Principio de realismo clínico**:
- **EXPOSED**: virus entrando al cuerpo
- **INCUBATING**: replicándose sin síntomas
- **CONTAGIOUS**: alta carga viral, puede contagiar
- **SYMPTOMATIC**: síntomas visibles, malestar
- **RECOVERING**: sistema inmune ganando
- Cada fase tiene contagiosidad y letalidad diferentes

### ¿Por qué inmunidad multinivel?

**Principio de inmunología real**:
- **Innata**: defensas generales (barreras físicas)
- **Adaptativa**: respuesta específica
- **Por familia**: protección parcial contra parientes
- **Por cepa**: protección específica contra una variante
- **Cruzada**: familias relacionadas comparten antígenos
- Esto crea dinámicas epidemiológicas complejas

### ¿Por qué mutación durante transmisión?

**Principio de evolución viral**:
- Los virus mutan al replicarse
- La transmisión es un evento de replicación
- Cada contagio es oportunidad de mutación
- Genera diversidad viral
- Permite escape inmunológico (cepas nuevas evitan inmunidad previa)

### ¿Por qué carga viral ambiental (EpidemiologicalMap)?

**Principio de transmisión ambiental**:
- Muchas enfermedades se transmiten por aire o superficies
- Zonas con enfermos acumulan carga viral
- Los agentes evitan zonas contaminadas (MovementSystem)
- Crea "zonas rojas" emergentes
- La carga decae naturalmente con el tiempo

### ¿Por qué brotes espontáneos?

**Principio de origen de epidemias**:
- Las epidemias surgen naturalmente
- Zonas densas son focos de brotes
- El invierno aumenta riesgo (estacionalidad)
- Genera patógenos nuevos (patient zero)
- Sin brotes, solo habría transmisión de cepas existentes

### ¿Por qué decaimiento de inmunidad?

**Principio de memoria inmunológica**:
- La inmunidad no es eterna
- Los anticuerpos decaen con el tiempo
- La memoria inmunológica se desvanece
- Permite reinfecciones (realista)
- Crea ciclos epidémicos naturales

---

## 📊 Métricas del sistema

| Métrica | Valor |
|---------|-------|
| Archivos del sistema | 4 |
| Atributos de Pathogen | 10 |
| Fases de infección | 5 |
| Familias de patógenos | 7+ |
| Niveles de inmunidad | 5 |
| Tests cubriendo salud | ~10 |

---

## 🔮 Futuras extensiones

### Planificadas
- [ ] Tratamientos médicos (antibióticos, antivirales)
- [ ] Vacunas (inmunización preventiva)
- [ ] Cuarentenas forzadas por agentes inteligentes
- [ ] Hospitales y centros de salud

### Posibles
- [ ] Enfermedades crónicas (diabetes, hipertensión)
- [ ] Transmisión por vectores (mosquitos, garrapatas)
- [ ] Zoonosis (transmisión animal-humano)
- [ ] Resistencia antibiótica
- [ ] Pandemias globales (propagación mundial)
- [ ] Mutación dirigida (virus que escapan inmunidad)
- [ ] Enfermedades genéticas hereditarias
- [ ] Sistema de salud pública (cuarentenas, vacunación masiva)
- [ ] Medicina tradicional vs moderna
- [ ] Plagas que afectan cultivos
- [ ] Epidemiología histórica (peste negra, viruela)

---

*Documento: 09_SALUD.md*
*Versión: 2.0 (actualizado con EpidemiologicalMap)*
*Última actualización: Agosto 2026*