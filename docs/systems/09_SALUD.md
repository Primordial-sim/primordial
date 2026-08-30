# 08 - Salud

## 📋 Resumen

El **Sistema de Salud** modela la epidemiología completa del mundo simulado: patógenos con identidad propia y capacidad de mutación, progresión de infecciones en fases biológicas realistas, inmunidad innata y adaptativa, contagios locales con carga viral acumulativa, y brotes espontáneos. Todo filtrado por las **capacidades inmunológicas** derivadas del genoma de cada organismo.

**Filosofía fundamental**: *Los patógenos son entidades con identidad propia, genealogía trazable y capacidad evolutiva. La enfermedad emerge de la interacción entre el patógeno, la inmunidad del huésped y el contexto espacial.*

---

## 🎯 Responsabilidad

**Es responsable de:**
- Modelar patógenos con identidad, genealogía y mutación (`Pathogen`)
- Gestionar las fases de progresión de infecciones (`InfectionState`, `InfectionPhase`)
- Derivar capacidades inmunológicas del genoma (`ImmunologicalCapabilities`)
- Procesar decaimiento de inmunidad adquirida
- Avanzar infecciones activas y evaluar recuperaciones/muertes
- Propagar contagios locales basados en carga viral sectorial
- Generar brotes espontáneos (paciente cero)
- Mutar patógenos durante infecciones activas (deriva antigénica)
- Notificar eventos relacionales (cuidado durante enfermedad, duelo)
- Integrar recuperaciones con memoria episódica

**NO es responsable de:**
- ❌ Decidir la mortalidad general (eso lo hace `MortalitySystem`)
- ❌ Gestionar el mapa epidemiológico completo (eso lo hace `EpidemiologicalSystem`)
- ❌ Limpiar agentes muertos (eso lo hace `DeathResolver`)
- ❌ Procesar adopciones de huérfanos por muerte parental (eso lo hace `AdoptionSystem`)
- ❌ Generar eventos relacionales no relacionados con salud

---

## 🌍 Equivalencia con la vida real

| Concepto del sistema | Equivalencia en la vida real | Unidad |
|---------------------|-----------------------------|--------|
| **Pathogen** | Cepa viral/bacteriana específica | Variante patogénica |
| **InfectionState** | Estado clínico del paciente | Curso de enfermedad |
| **InfectionPhase** | Fase epidemiológica | Etapa de infección |
| **ImmunologicalCapabilities** | Tipo de sistema inmune | Inmunocompetencia |
| **family_relations** | Similitud antigénica | Reacción cruzada |
| **viral_load sectorial** | Carga ambiental de patógeno | Contagio ambiental |
| **patient_zero** | Caso índice | Paciente cero |
| **mutation** | Deriva antigénica | Evolución viral |
| **generation** | Número de mutaciones desde ancestro | Linaje viral |
| **asymptomatic_chance** | Proporción de asintomáticos | Transmisión silenciosa |
| **lethality** | Tasa de letalidad | Probabilidad de muerte |
| **virulence** | Gravedad de síntomas | Severidad clínica |
| **transmission** | R0 básico | Contagiosidad |
| **innate_immunity** | Inmunidad innata | Defensas inespecíficas |
| **adaptive_immunity** | Inmunidad adaptativa | Linfocitos T/B |
| **immunological_memory** | Memoria inmunológica | Células de memoria |

---

## 📁 Archivos que lo componen

| Archivo | Clase principal | Responsabilidad |
|---------|-----------------|-----------------|
| `systems/diseases/disease_system.py` | `DiseaseSystem` | Motor epidemiológico |
| `systems/diseases/pathogen.py` | `Pathogen`, `InfectionState`, `InfectionPhase` | Modelo de patógenos y estados |
| `systems/diseases/immunological_capabilities.py` | `ImmunologicalCapabilities` | Capacidades inmunes derivadas |

---

## 🔄 Flujo de ejecución completo

```
┌─────────────────────────────────────────────────────────────────┐
│         FASE 0: DECAIMIENTO DE INMUNIDAD ADQUIRIDA              │
│                                                                 │
│ Para cada agente vivo:                                          │
│  └── Si tiene decay_immunity:                                   │
│      └── Reducir inmunidad específica (decay_rate=0.0003/día)   │
│                                                                 │
│ Equivalencia: La inmunidad se pierde con el tiempo si no hay    │
│ re-exposición al patógeno.                                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│    FASE 1: PROGRESIÓN DE INFECCIONES Y RECUPERACIÓN             │
│                                                                 │
│ Para cada agente infectado (can_get_sick = True):               │
│  ├── advance_infections(delta_days) → avanza fases              │
│  │                                                               │
│  ├── Para cada infección activa:                                │
│  │                                                               │
│  │   ├── Si fase SYMPTOMATIC:                                   │
│  │   │   └── Evaluar letalidad:                                 │
│  │   │       risk = lethality * 0.01 * delta / total_immunity   │
│  │   │       Si random < risk:                                  │
│  │   │         ├── register_death (sepsis/fallo multiorgánico)  │
│  │   │         └── _notify_partner_death (evento relacional)    │
│  │   │                                                           │
│  │   ├── Si fase RECOVERING o SYMPTOMATIC:                      │
│  │   │   └── Evaluar recuperación:                              │
│  │   │       rate = base_recovery * 3 * immunity / virulence    │
│  │   │       chance = 1 - exp(-rate * delta)                    │
│  │   │       Si random < chance:                                │
│  │   │         ├── register_recovery                            │
│  │   │         ├── _notify_recovery_care (evento CARE)          │
│  │   │         └── Si can_form_immunological_memory:            │
│  │   │             └── add_memory(TYPE_DISEASE, valence=-1)     │
│  │   │                                                           │
│  │   ├── Si is_contagious():                                    │
│  │   │   └── Añadir a pathogen_map del sector                   │
│  │   │       (con effective_transmission)                       │
│  │   │                                                           │
│  │   └── Si fase CONTAGIOUS/SYMPTOMATIC:                        │
│  │       └── Intento de mutación (0.5% por día):                │
│  │           ├── new_variant = pathogen.mutate()                │
│  │           ├── Recuperar variantes antiguas de la familia     │
│  │           └── register_infection con la nueva variante       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│    FASE 2: CONTAGIOS LOCALES (CARGA VIRAL ACUMULATIVA)          │
│                                                                 │
│ 1. Calcular carga viral total por sector:                       │
│    sector_viral_load[sector] = Σ effective_transmission         │
│                                                                 │
│ 2. Para cada agente sano (can_get_sick):                        │
│    ├── viral_load = sector_viral_load[sector]                   │
│    ├── Si viral_load <= 0 → skip (no hay riesgo ambiental)      │
│    ├── base_innate = immunity - (1-energy)*0.2                  │
│    ├── crowding = local_pressure                                │
│    ├── immunity_factor = base_innate / 2                        │
│    ├── base_rate = (viral_load * max(1, crowding)) / innate     │
│    ├── daily_rate = base_rate * (1 - immunity_factor*0.8)       │
│    ├── infection_chance = 1 - exp(-daily_rate * delta)          │
│    │                                                               │
│    └── Si random < infection_chance:                             │
│        ├── Filtrar patógenos por is_susceptible_to(family)      │
│        ├── chosen = random.choice(susceptible_pathogens)        │
│        └── register_infection(person, chosen)                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│    FASE 3: BROTES ESPONTÁNEOS (UNA VEZ POR TICK)                │
│                                                                 │
│ outbreak_chance = 1 - exp(-base_outbreak_chance/100 * delta)    │
│                                                                 │
│ Si random < outbreak_chance:                                    │
│  ├── Filtrar agentes vivos, sanos y can_get_sick                │
│  ├── patient_zero = random.choice(susceptible_agents)           │
│  ├── Crear Pathogen.create_random_variant(familia_random)       │
│  ├── Verificaciones:                                            │
│  │   ├── is_susceptible_to(family)                              │
│  │   ├── No ya infectado con esa familia                        │
│  │   └── No ya pendiente en este tick                           │
│  └── register_infection(patient_zero, new_pathogen)             │
│                                                                 │
│ ⚠️ CRÍTICO: Este bloque está FUERA del bucle de agentes         │
│   (evalúa UNA VEZ por tick, no una vez por agente)              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes del Sistema

---

### 1. Pathogen - Modelo de Patógeno

**📁 Archivo**: `systems/diseases/pathogen.py`
**🌍 Equivalencia real**: Una cepa viral específica con identidad única y genealogía trazable.

#### Atributos

| Atributo | Tipo | Equivalencia real | Descripción |
|----------|------|-------------------|-------------|
| `family` | `str` | Familia taxonómica | "Influenza", "Coronavirus", etc. |
| `variant_id` | `int` | Identificador de variante | Contador dentro de la familia |
| `generation` | `int` | Número de mutaciones | Distancia al ancestro original |
| `ancestor_id` | `Optional[str]` | Patógeno padre | ID de la cepa anterior |
| `unique_id` | `int` | ID global único | Contador thread-safe |
| `pathogen_id` | `str` | Identificador completo | "Influenza_000001" |
| `virulence` | `float` | Gravedad de síntomas | 0.1 a ∞ (típicamente 0.3-1.5) |
| `transmission` | `float` | Contagiosidad | 0.01 a ∞ (típicamente 0.05-0.5) |
| `lethality` | `float` | Tasa de letalidad | [0.0, 1.0] |
| `asymptomatic_chance` | `float` | Prob. de ser asintomático | [0.0, 1.0] |
| `incubation_days` | `float` | Periodo de incubación | 1.0 a ∞ (típicamente 2-7 días) |

#### Generación de IDs únicos (thread-safe)

```python
_counter_lock = threading.Lock()
_next_id = 1

with Pathogen._counter_lock:
    self.unique_id = Pathogen._next_id
    Pathogen._next_id += 1

self.pathogen_id = f"{family}_{self.unique_id:06d}"
```

Esto permite rastrear la **genealogía viral completa**: cada patógeno sabe quién fue su ancestro, permitiendo reconstruir el árbol filogenético.

#### Sistema de inmunidad cruzada

```python
_family_relations = {
    "Influenza":     {"Influenza": 1.0, "Coronavirus": 0.15},
    "Coronavirus":   {"Coronavirus": 1.0, "Influenza": 0.15, "SARS": 0.6},
    "SARS":          {"SARS": 1.0, "Coronavirus": 0.6, "MERS": 0.5},
    "MERS":          {"MERS": 1.0, "SARS": 0.5, "Coronavirus": 0.4},
    "Poxvirus":      {"Poxvirus": 1.0, "Bacteriofago_X": 0.05},
    "Bacteriofago_X": {"Bacteriofago_X": 1.0, "Poxvirus": 0.05},
}
```

**Interpretación**: SARS y Coronavirus comparten 60% de similitud antigénica. La inmunidad contra uno protege parcialmente contra el otro.

#### Métodos clave

| Método | Descripción |
|--------|-------------|
| `create_random_variant(family)` | Crea cepa inicial con valores aleatorios |
| `mutate()` | Genera nueva variante con deriva antigénica |
| `get_family_similarity(f1, f2)` | Grado de similitud [0.0, 1.0] |
| `get_related_families(family, min_sim)` | Familias relacionadas |

#### Mutación (deriva antigénica)

```python
def mutate(self) -> 'Pathogen':
    return Pathogen(
        family=self.family,
        variant_id=self.variant_id + 1,
        virulence=max(0.1, self.virulence * random.uniform(0.85, 1.15)),
        transmission=max(0.01, self.transmission * random.uniform(0.85, 1.15)),
        lethality=max(0.0, min(1.0, self.lethality * random.uniform(0.85, 1.15))),
        generation=self.generation + 1,
        ancestor_id=self.pathogen_id,
        asymptomatic_chance=max(0.0, min(1.0, self.asymptomatic_chance * random.uniform(0.85, 1.15))),
        incubation_days=max(1.0, self.incubation_days * random.uniform(0.85, 1.15)),
    )
```

Cada mutación:
- Incrementa `generation` en 1
- Establece `ancestor_id` apuntando al padre
- Modifica todas las propiedades con factor uniforme [0.85, 1.15]
- Clampea a rangos válidos

#### Ejemplos

```python
# Crear variante aleatoria
virus = Pathogen.create_random_variant("Influenza")
print(virus)
# Pathogen(id=Influenza_000001, family=Influenza, gen=1, vir=0.85, trans=0.23, let=0.12, asym=0.25, inc=4.5d)

# Mutación
mutant = virus.mutate()
print(mutant.generation)   # 2
print(mutant.ancestor_id)  # "Influenza_000001"

# Inmunidad cruzada
sim = Pathogen.get_family_similarity("SARS", "Coronavirus")
print(sim)  # 0.6

related = Pathogen.get_related_families("Coronavirus")
print(related)  # {"Influenza", "SARS", "MERS"}
```

---

### 2. InfectionState - Estado de Infección

**📁 Archivo**: `systems/diseases/pathogen.py`
**🌍 Equivalencia real**: El curso clínico de una infección específica en un huésped.

#### Atributos

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `pathogen` | `Pathogen` | La cepa que infecta |
| `phase` | `InfectionPhase` | Fase actual |
| `days_in_phase` | `float` | Días en la fase actual |
| `total_days` | `float` | Días totales infectado |
| `is_asymptomatic` | `bool` | Si será asintomático |
| `exposed_duration` | `float` | Duración fase EXPOSED (0.5d) |
| `incubation_duration` | `float` | Duración fase INCUBATING |
| `contagious_duration` | `float` | Duración fase contagiosa (5 + virulence×3) |
| `recovering_duration` | `float` | Duración fase RECOVERING (3d) |

#### Determinación de asintomático

```python
self.is_asymptomatic = random.random() < pathogen.asymptomatic_chance
```

Se decide al inicio de la infección y afecta la transición después de incubación.

#### Flujo de fases

```
EXPOSED (0.5d)
    │
    ▼
INCUBATING (incubation_days)
    │
    ├─── Si is_asymptomatic ───► CONTAGIOUS ──► RECOVERING
    │                              (contagious_duration)
    │
    └─── Si sintomático ────────► SYMPTOMATIC ──► RECOVERING
                                   (contagious_duration)
```

#### Duración de fase contagiosa

```python
contagious_duration = 5.0 + (pathogen.virulence * 3.0)
```

Patógenos más virulentos mantienen al huésped contagioso por más tiempo.

#### Multiplicador de transmisión por fase

| Fase | Multiplicador | Descripción |
|------|---------------|-------------|
| EXPOSED | 0.0 | No contagia aún |
| INCUBATING | 0.0 | No contagia aún |
| CONTAGIOUS | 1.0 | Transmisión normal |
| SYMPTOMATIC | 1.2 | Mayor transmisión (tos, estornudos) |
| RECOVERING | 0.3 | Transmisión residual |

---

### 3. InfectionPhase - Enum de Fases

**📁 Archivo**: `systems/diseases/pathogen.py`
**🌍 Equivalencia real**: Las etapas clínicas de una enfermedad infecciosa.

#### Fases

| Fase | Valor | Descripción | Contagioso |
|------|-------|-------------|-----------|
| `EXPOSED` | "expuesto" | Recién expuesto, sin replicación | ❌ |
| `INCUBATING` | "incubando" | Virus replicándose, sin síntomas | ❌ |
| `CONTAGIOUS` | "contagioso" | Asintomático pero contagioso | ✅ |
| `SYMPTOMATIC` | "sintomático" | Síntomas visibles | ✅ (1.2×) |
| `RECOVERING` | "recuperándose" | Resolución, baja transmisión | ✅ (0.3×) |

#### Transiciones

```python
def advance(self, delta_days):
    self.days_in_phase += delta_days
    self.total_days += delta_days
    
    if self.phase == EXPOSED and self.days_in_phase >= 0.5:
        self.phase = INCUBATING
        self.days_in_phase = 0.0
    
    elif self.phase == INCUBATING and self.days_in_phase >= self.incubation_duration:
        if self.is_asymptomatic:
            self.phase = CONTAGIOUS
        else:
            self.phase = SYMPTOMATIC
        self.days_in_phase = 0.0
    
    elif self.phase == CONTAGIOUS and self.days_in_phase >= self.contagious_duration:
        self.phase = RECOVERING
    
    elif self.phase == SYMPTOMATIC and self.days_in_phase >= self.contagious_duration:
        self.phase = RECOVERING
```

---

### 4. ImmunologicalCapabilities - Capacidades Inmunológicas

**📁 Archivo**: `systems/diseases/immunological_capabilities.py`
**🌍 Equivalencia real**: El tipo de sistema inmune del organismo: innato, adaptativo, memoria.

#### Atributos

| Atributo | Tipo | Equivalencia real | Condición genética |
|----------|------|-------------------|-------------------|
| `has_immune_system` | `bool` | Sistema inmune presente | immunity > 0.1 |
| `has_innate_immunity` | `bool` | Inmunidad innata | = has_immune_system |
| `has_adaptive_immunity` | `bool` | Inmunidad adaptativa (vertebrados) | immunity > 0.5 AND nervous_system > 0.3 |
| `susceptible_to_viruses` | `bool` | Vulnerable a virus complejos | eucariota-like + metabolismo |
| `susceptible_to_bacteria` | `bool` | Vulnerable a bacterias | metabolism > 0.2 |
| `susceptible_to_fungi` | `bool` | Vulnerable a hongos | metabolism > 0.3 AND immunity < 0.95 |
| `can_get_sick` | `bool` | Puede enfermarse | has_immune_system OR metabolism > 0.3 |
| `can_die_from_disease` | `bool` | Puede morir por enfermedad | can_get_sick AND longevity < 2.0 AND metabolism > 0.3 |
| `can_form_immunological_memory` | `bool` | Memoria inmunológica | has_adaptive_immunity AND nervous_system > 0.5 |

#### Reglas de susceptibilidad por familia

```python
def is_susceptible_to(self, pathogen_family: str) -> bool:
    family_lower = pathogen_family.lower()
    
    # Virus complejos
    if "virus" in family_lower or "influenza" in family_lower or 
       "coronavirus" in family_lower or "poxvirus" in family_lower:
        return self.susceptible_to_viruses
    
    # Bacterias y bacteriófagos
    if "bacteria" in family_lower or "bacteriofago" in family_lower:
        return self.susceptible_to_bacteria
    
    # Hongos
    if "fungus" in family_lower or "hongo" in family_lower:
        return self.susceptible_to_fungi
    
    # Por defecto
    return self.can_get_sick
```

#### Ejemplos por organismo

```python
# Humano
human_caps = ImmunologicalCapabilities.from_genome(human_genome)
# immune=True, adaptive=True, viruses=True, bacteria=True, memory=True
human_caps.is_susceptible_to("Influenza")  # True
human_caps.is_susceptible_to("Bacteriofago_X")  # False (es virus de bacterias)

# Planta
plant_caps = ImmunologicalCapabilities.from_genome(plant_genome)
# immune=False, can_get_sick=False
plant_caps.is_susceptible_to("Influenza")  # False

# Pez
fish_caps = ImmunologicalCapabilities.from_genome(fish_genome)
# immune=True, adaptive=True, viruses=True, memory=True

# Insecto
insect_caps = ImmunologicalCapabilities.from_genome(insect_genome)
# immune=True, adaptive=False (solo innata), memory=False

# Bacteria
bacteria_caps = ImmunologicalCapabilities.from_genome(bacteria_genome)
# immune=False, susceptible_to_viruses=False
# Pero: susceptible_to_bacteria=False (las bacterias no se infectan con bacterias)
```

---

### 5. DiseaseSystem - Motor Epidemiológico

**📁 Archivo**: `systems/diseases/disease_system.py`
**🌍 Equivalencia real**: El sistema de salud pública: vigilancia epidemiológica, control de brotes, atención médica.

#### Fases del proceso

| Fase | Nombre | Responsabilidad |
|------|--------|-----------------|
| **Fase 0** | Decaimiento de inmunidad | La inmunidad adquirida se pierde gradualmente |
| **Fase 1** | Progresión y recuperación | Avanzar infecciones, evaluar muertes/recuperaciones, mutación |
| **Fase 2** | Contagios locales | Propagación por carga viral acumulativa en sectores |
| **Fase 3** | Brotes espontáneos | Generación de pacientes cero (una vez por tick) |

#### Fase 0: Decaimiento de inmunidad

```python
for person in state.get_all_persons():
    if hasattr(person, 'decay_immunity'):
        person.decay_immunity(delta_days, decay_rate=0.0003)
```

La inmunidad adquirida se pierde lentamente (0.03% por día), requiriendo re-exposición para mantenerse.

#### Fase 1: Letalidad y recuperación

**Letalidad (en fase SYMPTOMATIC):**

```python
lethality_risk = pathogen.lethality * 0.01 * delta_days
total_immunity = person.get_specific_immunity(pathogen)
lethality_risk = lethality_risk / max(0.1, total_immunity)

if random.random() < lethality_risk:
    pending.register_death(entity_id, f"Sepsis / Fallo multiorgánico por {pathogen.pathogen_id}")
    self._notify_partner_death(person, state, pending, current_day)
```

**Recuperación:**

```python
daily_recovery_rate = (dis_cfg.base_recovery_chance * 3.0 * total_immunity) / max(0.1, pathogen.virulence)
recovery_chance = 1.0 - math.exp(-daily_recovery_rate * delta_days)

if random.random() < recovery_chance:
    pending.register_recovery(entity_id, path_id)
    self._notify_recovery_care(person, state, pending, current_day, pathogen)
    
    if immune_caps.can_form_immunological_memory:
        intensity = min(1.0, 0.3 + (pathogen.virulence * 0.6))
        CognitiveMemorySystem.add_memory(
            person=person,
            mem_type=CognitiveMemorySystem.TYPE_DISEASE,
            target_id=pathogen.pathogen_id,
            intensity=intensity,
            valence=-1,
            context="recuperacion",
            current_day=current_day,
            pending=pending,
        )
```

La intensidad del recuerdo depende de la virulencia: enfermedades más graves generan memorias más fuertes.

#### Fase 1: Mutación durante infección

```python
if infection_state.phase in (CONTAGIOUS, SYMPTOMATIC):
    mutation_chance = 0.005 * delta_days
    if random.random() < mutation_chance:
        new_variant = pathogen.mutate()
        
        if new_variant.pathogen_id not in person.active_infections:
            # Recuperar variantes antiguas de la misma familia
            for old_path_id in list(person.active_infections.keys()):
                if old_path_id.startswith(f"{pathogen.family}_") and old_path_id != new_variant.pathogen_id:
                    pending.register_recovery(entity_id, old_path_id)
            
            # Registrar la nueva variante
            pending.register_infection(entity_id, new_variant)
```

Esto modela **deriva antigénica**: el virus evoluciona dentro del huésped y escapa parcialmente a la inmunidad existente.

#### Fase 2: Contagio por carga viral sectorial

```python
# Paso 1: Acumular carga viral por sector
for sector, pathogens in pathogen_map.items():
    for _, effective_transmission in pathogens:
        sector_viral_load[sector] += effective_transmission

# Paso 2: Evaluar contagio para cada sano
for person in state.get_all_persons():
    viral_load = sector_viral_load.get(sector, 0.0)
    if viral_load <= 0.0:
        continue
    
    base_innate = max(0.1, genome.get_trait_value("immunity") - ((1.0 - energy) * 0.2))
    crowding_pressure = context.get_local_pressure(person.x, person.y)
    immunity_factor = min(1.0, base_innate / 2.0)
    
    base_rate = (viral_load * max(1.0, crowding_pressure)) / max(0.5, base_innate)
    daily_transmission_rate = base_rate * (1.0 - immunity_factor * 0.8)
    infection_chance = 1.0 - math.exp(-daily_transmission_rate * delta_days)
    
    if random.random() < infection_chance:
        # Filtrar por susceptibilidad
        susceptible = [p for p in local_p if immune_caps.is_susceptible_to(p.family)]
        if susceptible:
            chosen = random.choice(susceptible)
            pending.register_infection(entity_id, chosen)
```

#### Fórmula de probabilidad de contagio

```
base_rate = (viral_load × max(1, crowding)) / max(0.5, innate_immunity)
daily_rate = base_rate × (1 - immunity_factor × 0.8)
infection_chance = 1 - exp(-daily_rate × delta_days)
```

**Factores que aumentan contagio:**
- Alta carga viral en el sector (muchos enfermos)
- Hacinamiento (crowding alto)
- Baja inmunidad innata
- Baja energía (desnutrición reduce inmunidad)

**Factores que disminuyen contagio:**
- Alta inmunidad innata
- Buena energía
- Pocos enfermos en el sector

#### Fase 3: Brotes espontáneos

```python
# ⚠️ EVALUADO UNA VEZ POR TICK (fuera del bucle de agentes)
outbreak_chance = 1.0 - math.exp(-(dis_cfg.base_outbreak_chance / 100.0) * delta_days)

if random.random() < outbreak_chance:
    # Filtrar agentes sanos y susceptibles
    susceptible_agents = [
        p for p in state.get_all_persons()
        if p.entity_id not in pending.deaths
        and not p.is_sick
        and ImmunologicalCapabilities.from_genome(p.genome).can_get_sick
    ]
    
    if susceptible_agents:
        patient_zero = random.choice(susceptible_agents)
        familia_random = random.choice(pathogen_families)
        new_virus = Pathogen.create_random_variant(familia_random)
        
        # Verificaciones exhaustivas
        is_susceptible = immune_caps.is_susceptible_to(new_virus.family)
        already_infected = any(
            inf.pathogen.family == new_virus.family
            for inf in patient_zero.active_infections.values()
        )
        already_pending = any(
            eid == patient_zero.entity_id
            for eid, _ in pending.infections
        )
        
        if is_susceptible and not already_infected and not already_pending:
            pending.register_infection(patient_zero.entity_id, new_virus)
```

**CRÍTICO**: Este bloque está fuera del bucle de agentes. Si estuviera dentro, un brote ocurriría por cada agente por tick, causando epidemias instantáneas masivas (bug crítico corregido).

#### Integración con Sistema de Relaciones

**Evento de cuidado durante recuperación:**

```python
def _notify_recovery_care(patient, state, pending, current_day, pathogen):
    for rel in patient._relationships.values():
        if rel.status in (DATING, COHABITATION, CONSOLIDATED):
            partner = state.get_person_by_id(rel.partner_id)
            if partner and distance < 15.0:
                rel_strength = sum(m.current_weight(current_day) for m in rel.memories)
                base_intensity = min(1.0, 0.4 + (pathogen.virulence * 0.5))
                relationship_bonus = min(0.3, rel_strength * 0.001)
                intensity = min(1.0, base_intensity + relationship_bonus)
                
                context = "cuidado_enfermedad" if rel_strength > 100 else f"recuperacion_de_{pathogen.pathogen_id}"
                
                event = _DiseaseRelationalEvent(
                    event_type=RelationshipEventType.CARE,
                    intensity=intensity,
                    context=context,
                )
                self.relationship_engine.process_event(event, partner, patient, current_day)
```

**Evento de duelo por muerte:**

```python
def _notify_partner_death(deceased, state, pending, current_day):
    for rel in deceased._relationships.values():
        survivor = state.get_person_by_id(rel.partner_id)
        if survivor:
            rel_strength = sum(m.current_weight(current_day) for m in rel.memories)
            base_intensity = 0.5
            relationship_bonus = min(0.5, rel_strength * 0.002)
            intensity = min(1.0, base_intensity + relationship_bonus)
            
            if rel_strength > 200:
                context = "perdida_de_ser_querido"
            elif rel_strength > 100:
                context = "duelo_profundo"
            else:
                context = "fallecimiento"
            
            event = _DiseaseRelationalEvent(
                event_type=RelationshipEventType.PARTNER_DEATH,
                intensity=intensity,
                context=context,
            )
            self.relationship_engine.process_event(event, survivor, deceased, current_day)
```

---

## 🔗 Interacción entre componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                    GENOMA (fuente de verdad)                     │
│   immunity, nervous_system, metabolism, heterotrophy,          │
│   photosynthesis, longevity                                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │ consultado por
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│           ImmunologicalCapabilities                             │
│   - has_immune_system, has_adaptive_immunity                   │
│   - susceptible_to_viruses/bacteria/fungi                      │
│   - can_get_sick, can_die_from_disease                         │
│   - can_form_immunological_memory                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │ usado por
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DiseaseSystem                                │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Fase 0: Decaimiento inmunidad                            │  │
│  │ Fase 1: Progresión infecciones + mutación                │  │
│  │ Fase 2: Contagios locales (carga viral acumulativa)      │  │
│  │ Fase 3: Brotes espontáneos (UNA VEZ por tick)            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│         │                    │                    │              │
│         ▼                    ▼                    ▼              │
│   InfectionState        Pathogen          Pathogen.mutate()     │
│   (avance de fases)    (cepa específica)  (deriva antigénica)   │
└─────────┬─────────────────────┬───────────────────┬─────────────┘
          │                     │                   │
          │ emite eventos       │ notifica          │ registra
          ▼                     ▼                   ▼
┌─────────────────┐   ┌──────────────────┐   ┌────────────────┐
│ Relationship    │   │ Cognitive        │   │ PendingChanges │
│ ExperienceEngine│   │ MemorySystem     │   │                │
│                 │   │                  │   │ register_      │
│ Eventos:        │   │ Memoria:         │   │ infection()    │
│ - CARE (cuidado)│   │ TYPE_DISEASE     │   │ register_      │
│ - PARTNER_DEATH │   │ (recuperación)   │   │ recovery()     │
└─────────────────┘   └──────────────────┘   │ register_      │
                                              │ death()        │
                                              └────────────────┘
```

---

## ⚙️ Configuración relevante

```python
# DiseasesConfig
config.diseases.base_transmission_chance = 0.18
config.diseases.base_recovery_chance = 0.15
config.diseases.base_outbreak_chance = 5.0  # Por 100 (evaluada como x/100)
config.diseases.pathogen_families = [
    "Influenza",
    "Coronavirus",
    "Poxvirus",
    "Bacteriofago_X"
]

# EnvironmentConfig (usado en contagios)
config.environment.sector_size = 10

# MutationConfig (afecta deriva antigénica indirectamente)
config.mutation.probability = 0.05
config.mutation.magnitude_std = 0.1
```

### Parámetros hardcodeados

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| `exposed_duration` | 0.5 días | Periodo muy corto tras exposición |
| `recovering_duration` | 3.0 días | Convalecencia estándar |
| `lethality multiplier` | 0.01 | Letalidad base por día |
| `recovery multiplier` | 3.0 | Recuperación acelerada |
| `mutation_chance` | 0.005 por día | ~0.5% de mutar por día |
| `immunity decay_rate` | 0.0003 por día | Pérdida lenta de inmunidad |
| `transmission multipliers` | CONTAGIOUS=1.0, SYMPTOMATIC=1.2, RECOVERING=0.3 | Más transmisión con síntomas |

---

## 🧪 Tests del sistema

| Archivo | Cobertura |
|---------|-----------|
| `tests/unit/test_pathogen.py` | Pathogen, InfectionState, mutación, inmunidad cruzada |
| `tests/unit/test_immunological_capabilities.py` | Derivación desde genoma |
| `tests/unit/test_dessease_system.py` | Brotes, contagios locales |
| `tests/integration/test_regression_bugs.py` | Bug #2: brotes fuera de bucle, Bug #4: filtros de tuples |

---

## 📝 Ejemplos completos

### Ejemplo 1: Ciclo completo de una epidemia

```python
# 1. Brote espontáneo (Fase 3)
# DiseaseSystem elige paciente cero aleatorio
# Crea Pathogen.create_random_variant("Influenza")
# Registra infección

# 2. Progresión (Fase 1)
# Día 0.0-0.5: EXPOSED
# Día 0.5-4.5: INCUBATING
# Día 4.5-9.5: SYMPTOMATIC (contagioso 1.2×)
# Día 9.5-12.5: RECOVERING (contagioso 0.3×)

# 3. Durante SYMPTOMATIC (Fase 2)
# El agente contribuye a la carga viral de su sector
# Vecinos sanos con baja inmunidad se infectan

# 4. Posible mutación (Fase 1)
# Día 7: 0.5% probabilidad de mutar
# Nueva variante Influenza_000002 con generation=2
# Vieja variante se recupera

# 5. Recuperación (Fase 1)
# Memoria episódica: TYPE_DISEASE, valence=-1, intensity=0.6
# Evento CARE para pareja cercana (RelationshipExperienceEngine)

# 6. Inmunidad adquirida
# El agente tiene inmunidad específica contra Influenza_000002
# Inmunidad parcial contra variantes relacionadas (ej: Influenza_000003)
# Decae 0.03% por día sin re-exposición
```

### Ejemplo 2: Inmunidad cruzada

```python
# Agente se recuperó de Coronavirus
person.family_specific_immunity["Coronavirus"] = 0.8

# Llega SARS (similitud 0.6 con Coronavirus)
# Inmunidad efectiva contra SARS = 0.8 * 0.6 = 0.48

# Llega Influenza (similitud 0.15 con Coronavirus)
# Inmunidad efectiva contra Influenza = 0.8 * 0.15 = 0.12 (casi nula)

# Llega Poxvirus (similitud 0.0)
# Inmunidad efectiva = 0 (nula)
```

### Ejemplo 3: Organismo resistente

```python
# Planta (no puede enfermarse)
plant_caps = ImmunologicalCapabilities.from_genome(plant_genome)
print(plant_caps.can_get_sick)  # False

# DiseaseSystem la ignora en todas las fases
# No puede ser paciente cero
# No se infecta por carga viral ambiental
# No progresa infecciones

# Bacteria (solo susceptible a bacteriófagos)
bacteria_caps = ImmunologicalCapabilities.from_genome(bacteria_genome)
bacteria_caps.is_susceptible_to("Influenza")      # False
bacteria_caps.is_susceptible_to("Bacteriofago_X") # True
```

### Ejemplo 4: Carga viral sectorial

```python
# Sector (5, 5) tiene 3 agentes infectados:
# - Agente A: Influenza_000001, transmission=0.3, fase SYMPTOMATIC (1.2×)
# - Agente B: Influenza_000002, transmission=0.4, fase CONTAGIOUS (1.0×)
# - Agente C: Coronavirus_000001, transmission=0.25, fase CONTAGIOUS (1.0×)

# Carga viral total del sector:
# 0.3 * 1.2 + 0.4 * 1.0 + 0.25 * 1.0 = 0.36 + 0.4 + 0.25 = 1.01

# Agente D sano entra al sector:
# base_innate = 1.2 (inmunidad alta)
# crowding = 0.8
# base_rate = (1.01 * max(1, 0.8)) / max(0.5, 1.2) = 0.84
# immunity_factor = 1.2 / 2 = 0.6
# daily_rate = 0.84 * (1 - 0.6 * 0.8) = 0.44
# infection_chance = 1 - exp(-0.44 * 1) = 0.36 (36% en 1 día)
```

### Ejemplo 5: Árbol filogenético

```python
# Paciente cero con Influenza_000001
ancestor = Pathogen.create_random_variant("Influenza")

# Tras mutación en huésped A
variant_a = ancestor.mutate()  # Influenza_000002, ancestor_id=Influenza_000001

# Tras mutación en huésped B
variant_b = variant_a.mutate()  # Influenza_000003, ancestor_id=Influenza_000002

# Árbol filogenético:
# Influenza_000001
#    └── Influenza_000002
#         └── Influenza_000003
```

---

## 🚨 Consideraciones y limitaciones

### Principios fundamentales
- **Patógenos como entidades**: cada cepa tiene ID único y genealogía
- **Inmunidad cruzada**: familias relacionadas comparten protección parcial
- **Deriva antigénica**: los patógenos mutan dentro del huésped
- **Carga viral acumulativa**: más infectados = mayor riesgo ambiental
- **Brotes una vez por tick**: evita epidemias masivas instantáneas

### Arquitectura de propagación

```
Brote espontáneo
      │
      ▼
Paciente cero infectado
      │
      ▼
Progresión de fases (EXPOSED → INCUBATING → CONTAGIOUS/SYMPTOMATIC → RECOVERING)
      │
      ├──► Mutación ocasional → nueva variante
      │
      └──► Aporte a carga viral del sector
              │
              ▼
         Contagio de vecinos sanos
              │
              ▼
         Nueva iteración del ciclo
```

### Optimizaciones de rendimiento

| Optimización | Descripción |
|--------------|-------------|
| **Brotes fuera del bucle** | Evaluación global, no por agente |
| **Pathogen_map por sector** | Acumulación eficiente de carga viral |
| **defaultdict** | Evita checks de existencia |
| **Thread-safe counter** | Permite paralelización futura |
| **Lazy evaluation** | Inmunidad cruzada bajo demanda |

### Limitaciones
- No hay vacunación (solo inmunidad natural)
- No hay cuarentena activa (solo aislamiento natural por síntomas)
- No hay tratamientos médicos (recuperación natural)
- No hay diagnóstico (agentes no "saben" que están enfermos)
- No hay transmisión vertical (madre-hijo durante gestación)
- La mutación es aleatoria sin presión selectiva dirigida

### Errores comunes

| Error | Consecuencia | Solución |
|-------|-------------|----------|
| ❌ Brotes dentro del bucle de agentes | Epidemias masivas en 1 tick | Evaluar UNA VEZ por tick |
| ❌ No filtrar por susceptibilidad | Plantas infectándose con influenza | Usar `ImmunologicalCapabilities` |
| ❌ Carga viral binaria (sí/no) | Irrealista | Acumular effective_transmission |
| ❌ Ignorar inmunidad cruzada | Reinfecciones poco realistas | Usar `_family_relations` |
| ❌ Mutación en fase EXPOSED | Variantes prematuras | Solo en CONTAGIOUS/SYMPTOMATIC |
| ❌ Olvidar notificar muertes | Relaciones no actualizan duelo | `_notify_partner_death` |

---

## 🎓 Conceptos clave

### ¿Por qué patógenos con identidad única?

**Principio de trazabilidad evolutiva**:
- Cada cepa tiene un ID único global
- Sabe quién fue su ancestro (`ancestor_id`)
- Esto permite reconstruir árboles filogenéticos
- Y estudiar la evolución viral en tiempo real

### ¿Por qué inmunidad cruzada?

**Principio de reacción cruzada**:
- En la vida real, anticuerpos contra un virus pueden reconocer virus similares
- SARS y Coronavirus comparten antígenos
- Esto explica por qué algunas personas tienen protección parcial
- Y por qué las vacunas contra una cepa pueden proteger contra otras

### ¿Por qué carga viral acumulativa?

**Principio de dosis infecciosa**:
- No basta con "estar cerca de un enfermo"
- La probabilidad depende de la CANTIDAD de virus en el aire
- Más enfermos + más transmisibles = más carga
- Esto modela superpropagadores y eventos masivos

### ¿Por qué los brotes son UNA VEZ por tick?

**Principio de rareza epidemiológica**:
- Un brote nuevo es un evento raro
- Si se evaluara por agente, habría N brotes por tick
- Esto causaría pandemias instantáneas irreales
- El bug crítico fue corregido moviendo el bloque fuera del bucle

### ¿Por qué mutación en CONTAGIOUS/SYMPTOMATIC?

**Principio de replicación activa**:
- Los virus mutan cuando se están replicando activamente
- En EXPOSED e INCUBATING aún hay pocas copias
- En RECOVERING el sistema inmune está ganando
- La máxima replicación (y mutación) ocurre durante síntomas

### ¿Por qué asintomáticos?

**Principio de transmisión silenciosa**:
- En la vida real, muchos contagios vienen de asintomáticos
- Esto hace las epidemias más difíciles de controlar
- Agente no "sabe" que está enfermo, sigue socializando
- Genera dinámicas epidemiológicas más realistas

---

## 📊 Métricas del sistema

| Métrica | Valor |
|---------|-------|
| Archivos del sistema | 3 |
| Fases de infección | 5 |
| Familias de patógenos | 4+ |
| Relaciones entre familias | 7 pares |
| Atributos de Pathogen | 11 |
| Capacidad inmunológica | 9 atributos |
| Tests cubriendo salud | ~15 |

---

## 🔮 Futuras extensiones

### Planificadas
- [ ] Vacunación (inmunidad artificial)
- [ ] Cuarentena activa (agentes se aíslan si sintomáticos)
- [ ] Tratamientos médicos (reduce letalidad, acelera recuperación)
- [ ] Transmisión vertical (madre-hijo durante gestación)

### Posibles
- [ ] Vectores de transmisión (mosquitos, garrapatas)
- [ ] Zoonosis (patógenos que saltan entre especies)
- [ ] Resistencia antimicrobiana (bacterias resistentes)
- [ ] Pandemias globales (patógenos que cruzan continentes)
- [ ] Diagnóstico y conocimiento (agentes "saben" que están enfermos)
- [ ] Comportamiento preventivo (distanciamiento, higiene)
- [ ] Inmunidad de rebaño (umbral crítico)
- [ ] Estacionalidad (algunos virus más activos en invierno)

---

*Documento: 08_SALUD.md*
*Versión: 1.0*