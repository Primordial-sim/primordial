# 14 - Temporal y Envejecimiento

## 📋 Resumen

El **Sistema Temporal** gestiona dos aspectos fundamentales del paso del tiempo en la simulación: el **reloj global** con su metabolismo basal asociado (`TemporalSystem`), y el **envejecimiento biológico multifactorial** (`AgingSystem`). Introduce trade-offs evolutivos reales: alta inmunidad aumenta supervivencia pero consume más energía, alto temperamento incrementa actividad pero acelera desgaste metabólico, y la vejez afecta tanto la recuperación energética como la velocidad de envejecimiento.

**Filosofía fundamental**: *El tiempo no es solo un contador: es una fuerza biológica que interactúa con la genética, el entorno y el estado fisiológico del agente. Cada día vivido tiene un coste metabólico real, y el envejecimiento se acelera o ralentiza según las condiciones de vida.*

---

## 🎯 Responsabilidad

**Es responsable de:**
- Avanzar el reloj global de la simulación (`pending.register_time_pass`)
- Calcular consumo energético basal de cada agente
- Calcular recuperación energética basada en recursos y estado
- Gestionar hitos biológicos (madurez, senectud) con efectos emocionales
- Calcular envejecimiento biológico multifactorial
- Aplicar desgaste reproductivo con límites de saturación
- Modelar carga del embarazo sobre el envejecimiento
- Considerar estrés crónico como acelerador de envejecimiento
- Considerar enfermedad como acelerador de envejecimiento
- Aplicar factor genético (longevidad) al envejecimiento
- Detectar estados fisiológicos extremos combinados

**NO es responsable de:**
- ❌ Decidir cuándo muere un agente (eso lo hace `MortalitySystem`, doc 10)
- ❌ Gestionar estaciones y clima (eso lo hace `EnvironmentSystem`, doc 04)
- ❌ Procesar enfermedades activas (eso lo hace `DiseaseSystem`, doc 09)
- ❌ Generar recursos en el mapa (eso lo hace `EnvironmentDynamics`, doc 04)
- ❌ Decidir si un agente se reproduce (eso lo hace `ConceptionSystem`, doc 05)

---

## 🌍 Equivalencia con la vida real

| Concepto del sistema | Equivalencia en la vida real | Unidad |
|---------------------|-----------------------------|--------|
| **Reloj global** | Tiempo cronológico | Días |
| **Metabolismo basal** | Gasto energético en reposo | Calorías/día |
| **Coste inmunológico** | Sistema inmune activo | Consumo metabólico |
| **Coste temperamental** | Hiperactividad metabólica | Estrés oxidativo |
| **Recuperación energética** | Descanso + alimentación | Anabolismo |
| **Recursos del entorno** | Disponibilidad de comida | Energía ambiental |
| **Desgaste reproductivo** | Coste de la maternidad/paternidad | Estrés fisiológico |
| **Carga del embarazo** | Gestación | Coste energético adicional |
| **Estrés crónico** | Cortisol elevado | Aceleración telomérica |
| **Enfermedad** | Inflamación sistémica | Daño celular |
| **Baja energía** | Desnutrición | Catabolismo |
| **Longevidad genética** | Genes de reparación del ADN | Potencial de vida |
| **Hitos biológicos** | Pubertad, menopausia | Transiciones vitales |

---

## 📁 Archivos que lo componen

| Archivo | Clase principal | Responsabilidad |
|---------|-----------------|-----------------|
| `systems/temporal/temporal_system.py` | `TemporalSystem` | Reloj global + metabolismo basal |
| `systems/temporal/aging_system.py` | `AgingSystem` | Envejecimiento biológico multifactorial |

---

## 🔄 Flujo de ejecución completo

```
┌─────────────────────────────────────────────────────────────────┐
│          CICLO TEMPORAL (por tick)                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 1: AVANCE DEL RELOJ GLOBAL                                 │
│                                                                 │
│ TemporalSystem.process():                                       │
│  └── pending.register_time_pass(delta_days)                     │
│      └── WorldState incrementa world_days_elapsed               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 2: METABOLISMO BASAL (TemporalSystem)                      │
│                                                                 │
│ Para cada agente vivo:                                          │
│                                                                 │
│  1. COSTES ENERGÉTICOS (consumo):                               │
│     ├── Coste inmunológico:                                     │
│     │   ├── base = immunity × immune_cost_per_point             │
│     │   └── Si is_sick: × min(5, 2 + Σ virulencia)             │
│     ├── Coste por temperamento: temperament × temp_cost         │
│     ├── Factor de edad:                                         │
│     │   ├── senior: ×1.2                                        │
│     │   ├── niño: ×1.3                                          │
│     │   └── adulto: ×1.0                                        │
│     └── Coste adicional por enfermedad: +0.05 × delta           │
│                                                                 │
│  2. RECUPERACIÓN ENERGÉTICA:                                    │
│     ├── base = base_recovery_rate                               │
│     ├── × resource_factor (0.5 + resources × 0.5)               │
│     ├── × recovery_age_factor:                                  │
│     │   ├── senior: ×0.7                                        │
│     │   ├── niño: ×1.1                                          │
│     │   └── adulto: ×1.0                                        │
│     ├── × sickness_recovery_factor (0.5 si enfermo)             │
│     └── × delta_days                                            │
│                                                                 │
│  3. BALANCE ENERGÉTICO:                                         │
│     └── net_change = recovery - consumption                     │
│         └── register_emotion_update("energy", net_change)       │
│                                                                 │
│  4. HITOS BIOLÓGICOS:                                           │
│     ├── Si no is_adult y age >= adult_age_days:                 │
│     │   ├── happiness +0.1                                      │
│     │   └── stress -0.05                                        │
│     └── Si no is_senior y age >= senior_age_days:               │
│         ├── stress +0.1                                         │
│         └── happiness -0.05                                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 3: ENVEJECIMIENTO BIOLÓGICO (AgingSystem)                  │
│                                                                 │
│ Para cada agente vivo:                                          │
│                                                                 │
│  1. DESGASTE REPRODUCTIVO:                                      │
│     ├── effective_children = min(bio_children, max_for_wear)    │
│     ├── Si female:                                              │
│     │   └── wear = 1 + min(eff × per_child, max_multiplier-1)   │
│     └── Si male:                                                │
│         └── wear = 1 + min(eff × per_child × 0.3, límite)      │
│                                                                 │
│  2. CARGA DEL EMBARAZO (solo madres embarazadas):               │
│     └── burden = pregnancy_burden_multiplier (ej: 1.2)          │
│                                                                 │
│  3. DESGASTE POR ESTRÉS CRÓNICO:                                │
│     └── stress_aging = 1 + stress × stress_aging_factor         │
│                                                                 │
│  4. DESGASTE POR ENFERMEDAD:                                    │
│     └── sickness_aging = 1 + sickness_aging_factor (si sick)    │
│                                                                 │
│  5. DESGASTE POR BAJA ENERGÍA:                                  │
│     └── low_energy_aging = 1 + (1-energy) × factor              │
│                                                                 │
│  6. PENALIZACIÓN POR ESTADOS EXTREMOS:                          │
│     ├── sick + energy < 0.3: ×1.15                              │
│     └── energy < 0.2: ×1.10                                     │
│                                                                 │
│  7. FACTOR GENÉTICO (longevidad):                               │
│     └── genetic_factor = longevity_factor / max(0.1, longevity) │
│                                                                 │
│  8. ENVEJECIMIENTO FINAL:                                       │
│     └── biological_increment = delta × Π(todos los factores)    │
│         └── register_age_increment(entity_id, increment)        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
         WorldState.apply_commit() consolida:
         - world_days_elapsed += delta
         - person.age += biological_increment
         - person.emotions["energy"] += net_change
         - person.is_adult = True (si hito)
         - person.is_senior = True (si hito)
```

---

## 🔧 Componentes del Sistema

---

### 1. TemporalSystem - Reloj Global y Metabolismo

**📁 Archivo**: `systems/temporal/temporal_system.py`
**🌍 Equivalencia real**: El paso del tiempo con su coste fisiológico inevitable: cada día vivido consume energía y requiere recuperación.

#### Configuración relevante

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `immune_energy_cost` | 0.01 | Coste energético por punto de inmunidad |
| `temperament_energy_cost` | 0.005 | Coste por hiperactividad temperamental |
| `base_energy_recovery` | 0.3 | Recuperación base por día |
| `adult_age_days` | ~6570 | Edad de madurez (~18 años) |
| `senior_age_days` | ~21900 | Edad de senectud (~60 años) |

#### Flujo interno

```python
def process(self, state, pending, delta_days, context):
    # 1. Avance del reloj global
    pending.register_time_pass(delta_days)
    
    for person in state.get_all_persons():
        if person.entity_id in pending.deaths:
            continue
        
        # ── COSTES ENERGÉTICOS ──
        # Coste inmunológico (con multiplicador si enfermo)
        immunity = person.genome.get_trait_value("immunity")
        immune_cost = immunity * immune_cost_per_point
        
        if person.is_sick:
            total_virulence = sum(
                pathogen.virulence 
                for pathogen in person.active_pathogens.values()
            )
            sickness_multiplier = min(5.0, 2.0 + total_virulence)
            immune_cost *= sickness_multiplier
        
        # Coste por temperamento
        temperament = person.genome.get_trait_value("temperament")
        temperament_cost = temperament * temperament_cost_per_point
        
        # Factor de edad
        age_factor = 1.0
        if age > senior_age_days: age_factor = 1.2
        elif age < adult_age_days: age_factor = 1.3
        
        # Consumo total
        total_consumption = (immune_cost + temperament_cost) * age_factor * delta_days
        if person.is_sick:
            total_consumption += 0.05 * delta_days
        
        # ── RECUPERACIÓN ENERGÉTICA ──
        local_resources = context.get_resources_at(person.x, person.y)
        resource_factor = 0.5 + (local_resources * 0.5)
        
        recovery_age_factor = 1.0
        if age > senior_age_days: recovery_age_factor = 0.7
        elif age < adult_age_days: recovery_age_factor = 1.1
        
        sickness_recovery_factor = 0.5 if person.is_sick else 1.0
        
        total_recovery = (
            base_recovery_rate *
            resource_factor *
            recovery_age_factor *
            sickness_recovery_factor *
            delta_days
        )
        
        # ── BALANCE ENERGÉTICO ──
        net_energy_change = total_recovery - total_consumption
        if abs(net_energy_change) > 0.001:
            pending.register_emotion_update(person.entity_id, "energy", net_energy_change)
        
        # ── HITOS BIOLÓGICOS ──
        self._check_milestones(person, pending, time_cfg)
```

#### Trade-offs evolutivos implementados

| Rasgo | Beneficio | Coste |
|-------|-----------|-------|
| **Alta inmunidad** | Menos enfermedades, más supervivencia | Mayor consumo energético basal |
| **Alto temperamento** | Más actividad, más exploración | Mayor consumo metabólico |
| **Enfermedad** | (no es rasgo) | +2× a +5× consumo inmunológico, -50% recuperación |
| **Edad senior** | (no es rasgo) | +20% consumo, -30% recuperación |
| **Edad niño** | (no es rasgo) | +30% consumo, +10% recuperación |

#### Hitos biológicos con efectos reales

```python
def _check_milestones(self, person, pending, time_cfg):
    age = getattr(person, 'age', 0.0)
    
    # Transición a adulto
    if not person.is_adult and age >= time_cfg.adult_age_days:
        pending.register_emotion_update(person.entity_id, "happiness", 0.1)
        pending.register_emotion_update(person.entity_id, "stress", -0.05)
    
    # Transición a anciano
    if not person.is_senior and age >= time_cfg.senior_age_days:
        pending.register_emotion_update(person.entity_id, "stress", 0.1)
        pending.register_emotion_update(person.entity_id, "happiness", -0.05)
```

**Efectos emocionales**:
- **Madurez**: ligera felicidad (+0.1), menos estrés (-0.05) — logro vital
- **Senectud**: más estrés (+0.1), menos felicidad (-0.05) — declive vital

---

### 2. AgingSystem - Envejecimiento Biológico

**📁 Archivo**: `systems/temporal/aging_system.py`
**🌍 Equivalencia real**: El envejecimiento celular acelerado o ralentizado por factores fisiológicos, genéticos y ambientales.

#### Configuración relevante

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `reproductive_wear_per_child` | 0.05 | Desgaste por hijo biológico |
| `max_children_for_aging` | 10 | Límite de saturación |
| `max_reproductive_wear_multiplier` | 2.0 | Máximo multiplicador reproductivo |
| `father_reproductive_wear_ratio` | 0.3 | Proporción del desgaste paterno |
| `pregnancy_burden_multiplier` | 1.2 | Carga del embarazo |
| `stress_aging_factor` | 0.3 | Impacto del estrés |
| `sickness_aging_factor` | 0.2 | Impacto de enfermedad |
| `low_energy_aging_factor` | 0.4 | Impacto de desnutrición |
| `longevity_genetic_factor` | 1.0 | Factor base de longevidad |

#### Factores de envejecimiento

| Factor | Fórmula | Descripción |
|--------|---------|-------------|
| **Reproductivo (madre)** | `1 + min(children × 0.05, 1.0)` | Hasta 2× más rápido con 10+ hijos |
| **Reproductivo (padre)** | `1 + min(children × 0.05 × 0.3, 0.3)` | Hasta 1.3× más rápido |
| **Embarazo** | `1.2` | 20% más rápido durante gestación |
| **Estrés crónico** | `1 + stress × 0.3` | Hasta 1.3× con estrés máximo |
| **Enfermedad** | `1 + 0.2` | 20% más rápido si enfermo |
| **Baja energía** | `1 + (1-energy) × 0.4` | Hasta 1.4× con energía 0 |
| **Estados extremos** | `×1.15` o `×1.10` | Penalización adicional |
| **Genético (longevidad)** | `1.0 / max(0.1, longevity)` | Longevidad alta = envejecimiento lento |

#### Flujo interno

```python
def process(self, state, pending, delta_days, context):
    for person in state.get_all_persons():
        if person.entity_id in pending.deaths:
            continue
        
        # 1. DESGASTE REPRODUCTIVO (con límite de saturación)
        biological_children = person.biological_children_count
        effective_children = min(biological_children, max_children_for_wear)
        
        if is_female:
            base_wear = effective_children * reproductive_wear_per_child
            reproductive_wear = 1.0 + min(base_wear, max_reproductive_wear_multiplier - 1.0)
        else:
            base_wear = effective_children * reproductive_wear_per_child * father_ratio
            reproductive_wear = 1.0 + min(base_wear, (max_reproductive_wear_multiplier - 1.0) * father_ratio)
        
        # 2. CARGA DEL EMBARAZO
        pregnancy_burden = pregnancy_burden_multiplier if person.is_pregnant else 1.0
        
        # 3. DESGASTE POR ESTRÉS CRÓNICO
        stress_aging = 1.0 + (stress_level * stress_aging_factor)
        
        # 4. DESGASTE POR ENFERMEDAD
        sickness_aging = 1.0 + (sickness_aging_factor if person.is_sick else 0.0)
        
        # 5. DESGASTE POR BAJA ENERGÍA
        low_energy_aging = 1.0 + ((1.0 - energy_level) * low_energy_aging_factor)
        
        # 6. PENALIZACIÓN POR ESTADOS EXTREMOS
        extreme_state_penalty = 1.0
        if person.is_sick and energy_level < 0.3:
            extreme_state_penalty = 1.15
        elif energy_level < 0.2:
            extreme_state_penalty = 1.10
        
        # 7. FACTOR GENÉTICO
        genetic_longevity = person.genome.get_trait_value("longevity")
        genetic_factor = longevity_genetic_factor / max(0.1, genetic_longevity)
        
        # 8. ENVEJECIMIENTO FINAL
        total_aging_multiplier = (
            reproductive_wear *
            pregnancy_burden *
            stress_aging *
            sickness_aging *
            low_energy_aging *
            extreme_state_penalty *
            genetic_factor
        )
        
        biological_increment = delta_days * total_aging_multiplier
        pending.register_age_increment(person.entity_id, biological_increment)
```

#### Límite de saturación reproductiva

```python
max_children_for_wear = 10  # Configurado
effective_children = min(biological_children, max_children_for_wear)
```

**Justificación biológica**: El desgaste reproductivo no crece indefinidamente. Después de ~10 hijos, el cuerpo se adapta parcialmente al estrés reproductivo.

#### Asimetría de género en desgaste reproductivo

| Género | Fórmula | Máximo multiplicador |
|--------|---------|---------------------|
| **Femenino** | `1 + min(children × 0.05, 1.0)` | 2.0× |
| **Masculino** | `1 + min(children × 0.015, 0.3)` | 1.3× |

**Justificación**: La maternidad tiene costes fisiológicos mayores que la paternidad (embarazo, lactancia).

---

## 🔗 Interacción entre componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                   GENOMA (fuente de verdad)                      │
│   immunity, temperament, longevity                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
┌──────────────────────┐   ┌──────────────────────┐
│ TemporalSystem       │   │ AgingSystem          │
│                      │   │                      │
│ - Reloj global       │   │ - Envejecimiento     │
│ - Metabolismo basal  │   │   biológico          │
│ - Hitos biológicos   │   │ - Desgaste multif.   │
│                      │   │                      │
│ Consume:             │   │ Consume:             │
│ - immunity           │   │ - longevity          │
│ - temperament        │   │ - bio_children_count │
│ - age                │   │ - is_pregnant        │
│ - is_sick            │   │ - stress, energy     │
│ - active_pathogens   │   │ - is_sick            │
└──────────┬───────────┘   └──────────┬───────────┘
           │                          │
           │ register_emotion_update  │ register_age_increment
           │ register_time_pass       │
           ▼                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PendingChanges                                │
│                                                                  │
│  .world_days_elapsed += delta_days                              │
│  .age_increments[entity_id] = biological_increment              │
│  .emotion_updates[entity_id]["energy"] += net_change            │
└──────────────────────────┬──────────────────────────────────────┘
                           │ consolidado por
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   WorldState                                    │
│                                                                  │
│  person.age += biological_increment                             │
│  person.emotions["energy"] += net_change                        │
│  person.is_adult = True (si age >= adult_age_days)              │
│  person.is_senior = True (si age >= senior_age_days)            │
└──────────────────────────┬──────────────────────────────────────┘
                           │ usado por
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MortalitySystem (doc 10)                      │
│                                                                  │
│  Usa person.age para:                                           │
│    - Calcular riesgo base (Gompertz-Makeham)                    │
│    - Detectar hard cap (degradación telomérica)                 │
│    - Penalizar endogamia (solo en < 1 año)                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuración relevante

```python
# TimeConfig
config.time.days_per_year = 365.0
config.time.adult_age_days = 6570.0        # ~18 años
config.time.senior_age_days = 21900.0      # ~60 años
config.time.immune_energy_cost = 0.01
config.time.temperament_energy_cost = 0.005
config.time.base_energy_recovery = 0.3

# AgingConfig
config.aging.reproductive_wear_per_child = 0.05
config.aging.max_children_for_aging = 10
config.aging.max_reproductive_wear_multiplier = 2.0
config.aging.father_reproductive_wear_ratio = 0.3
config.aging.pregnancy_burden_multiplier = 1.2
config.aging.stress_aging_factor = 0.3
config.aging.sickness_aging_factor = 0.2
config.aging.low_energy_aging_factor = 0.4
config.aging.longevity_genetic_factor = 1.0
```

---

## 🧪 Tests del sistema

| Archivo | Cobertura |
|---------|-----------|
| `tests/unit/test_temporal_system.py` | Metabolismo, hitos, balance energético |
| `tests/unit/test_aging_system.py` | Factores de envejecimiento, saturación |
| `tests/integration/test_statistical.py` | Envejecimiento realista a largo plazo |

---

## 📝 Ejemplos completos

### Ejemplo 1: Balance energético de un humano sano

```python
# Humano adulto, sano, en zona con recursos medios
person.genome.get_trait_value("immunity") = 1.2
person.genome.get_trait_value("temperament") = 1.0
person.age = 10950  # ~30 años (adulto)
person.is_sick = False
local_resources = 0.6

# COSTES:
# immune_cost = 1.2 × 0.01 = 0.012
# temperament_cost = 1.0 × 0.005 = 0.005
# age_factor = 1.0 (adulto)
# total_consumption = (0.012 + 0.005) × 1.0 × 1.0 = 0.017 por día

# RECUPERACIÓN:
# resource_factor = 0.5 + 0.6 × 0.5 = 0.8
# recovery_age_factor = 1.0 (adulto)
# sickness_recovery_factor = 1.0 (sano)
# total_recovery = 0.3 × 0.8 × 1.0 × 1.0 × 1.0 = 0.24 por día

# BALANCE:
# net_energy_change = 0.24 - 0.017 = +0.223 por día
# → El agente gana energía lentamente (superávit)
```

### Ejemplo 2: Humano enfermo con alta inmunidad

```python
# Humano con infección grave (virulencia 1.5)
person.genome.get_trait_value("immunity") = 1.5
person.is_sick = True
person.active_pathogens = {
    "Influenza_000123": Pathogen(virulence=1.5, lethality=0.3)
}
local_resources = 0.4

# COSTES:
# immune_cost_base = 1.5 × 0.01 = 0.015
# sickness_multiplier = min(5.0, 2.0 + 1.5) = 3.5
# immune_cost = 0.015 × 3.5 = 0.0525
# temperament_cost = 1.0 × 0.005 = 0.005
# age_factor = 1.0
# total_consumption = (0.0525 + 0.005) × 1.0 × 1.0 + 0.05 = 0.1075

# RECUPERACIÓN:
# resource_factor = 0.5 + 0.4 × 0.5 = 0.7
# recovery_age_factor = 1.0
# sickness_recovery_factor = 0.5 (enfermo)
# total_recovery = 0.3 × 0.7 × 1.0 × 0.5 × 1.0 = 0.105

# BALANCE:
# net_energy_change = 0.105 - 0.1075 = -0.0025 por día
# → El agente pierde energía lentamente (déficit leve)
```

### Ejemplo 3: Envejecimiento de una madre con 5 hijos

```python
# Mujer de 35 años, 5 hijos biológicos, sana
person.biological_children_count = 5
person.age = 12775  # ~35 años
person.is_pregnant = False
person.emotions = {"stress": 0.3, "energy": 0.8}
person.is_sick = False
person.genome.get_trait_value("longevity") = 1.0

# 1. DESGASTE REPRODUCTIVO:
# effective_children = min(5, 10) = 5
# base_wear = 5 × 0.05 = 0.25
# reproductive_wear = 1.0 + min(0.25, 1.0) = 1.25 (25% más rápido)

# 2. CARGA DEL EMBARAZO:
# pregnancy_burden = 1.0 (no embarazada)

# 3. DESGASTE POR ESTRÉS:
# stress_aging = 1.0 + 0.3 × 0.3 = 1.09

# 4. DESGASTE POR ENFERMEDAD:
# sickness_aging = 1.0 (sana)

# 5. DESGASTE POR BAJA ENERGÍA:
# low_energy_aging = 1.0 + (1 - 0.8) × 0.4 = 1.08

# 6. ESTADOS EXTREMOS:
# extreme_state_penalty = 1.0 (no aplica)

# 7. FACTOR GENÉTICO:
# genetic_factor = 1.0 / max(0.1, 1.0) = 1.0

# 8. ENVEJECIMIENTO FINAL:
# total_aging_multiplier = 1.25 × 1.0 × 1.09 × 1.0 × 1.08 × 1.0 × 1.0
#                        = 1.47 (47% más rápido que lo normal)
#
# biological_increment = 1 día × 1.47 = 1.47 días biológicos
# → En 1 año cronológico, envejece 1.47 años biológicos
```

### Ejemplo 4: Envejecimiento acelerado por estrés y enfermedad

```python
# Hombre enfermo, estresado y desnutrido
person.biological_children_count = 2
person.age = 18250  # ~50 años
person.is_pregnant = False
person.emotions = {"stress": 0.9, "energy": 0.25}
person.is_sick = True
person.genome.get_trait_value("longevity") = 0.8

# 1. DESGASTE REPRODUCTIVO:
# reproductive_wear = 1.0 + min(2 × 0.05 × 0.3, 0.3) = 1.03

# 2. CARGA DEL EMBARAZO:
# pregnancy_burden = 1.0

# 3. DESGASTE POR ESTRÉS:
# stress_aging = 1.0 + 0.9 × 0.3 = 1.27

# 4. DESGASTE POR ENFERMEDAD:
# sickness_aging = 1.0 + 0.2 = 1.2

# 5. DESGASTE POR BAJA ENERGÍA:
# low_energy_aging = 1.0 + (1 - 0.25) × 0.4 = 1.3

# 6. ESTADOS EXTREMOS:
# sick AND energy < 0.3 → extreme_state_penalty = 1.15

# 7. FACTOR GENÉTICO:
# genetic_factor = 1.0 / max(0.1, 0.8) = 1.25 (longevidad baja)

# 8. ENVEJECIMIENTO FINAL:
# total_aging_multiplier = 1.03 × 1.0 × 1.27 × 1.2 × 1.3 × 1.15 × 1.25
#                        = 2.83 (183% más rápido)
#
# biological_increment = 1 día × 2.83 = 2.83 días biológicos
# → En 1 año cronológico, envejece 2.83 años biológicos
# → Envejecimiento acelerado extremo
```

### Ejemplo 5: Hito biológico - transición a adulto

```python
# Agente joven alcanza la madurez
person.age = 6570.0  # Exactamente adult_age_days
person.is_adult = False

# TemporalSystem._check_milestones():
# age >= adult_age_days AND NOT is_adult
# → register_emotion_update("happiness", +0.1)
# → register_emotion_update("stress", -0.05)
# → Log: "🎂 Agente 123 alcanzó la madurez (edad: 6570 días)"

# WorldState.apply_commit():
# person.is_adult = True
# person.emotions["happiness"] += 0.1
# person.emotions["stress"] -= 0.05
```

### Ejemplo 6: Hito biológico - transición a senectud

```python
# Agente adulto entra en senectud
person.age = 21900.0  # Exactamente senior_age_days
person.is_senior = False

# TemporalSystem._check_milestones():
# age >= senior_age_days AND NOT is_senior
# → register_emotion_update("stress", +0.1)
# → register_emotion_update("happiness", -0.05)
# → Log: "👴 Agente 456 entró en senectud (edad: 21900 días)"

# A partir de ahora:
# - age_factor = 1.2 (consume 20% más energía)
# - recovery_age_factor = 0.7 (recupera 30% menos)
# → Mayor riesgo de déficit energético crónico
```

### Ejemplo 7: Efecto de longevidad genética

```python
# Dos agentes con misma edad pero diferente longevidad genética

# Agente A: longevity = 1.5 (genéticamente longevo)
genetic_factor_A = 1.0 / 1.5 = 0.67
# Envejece 33% más lento de lo normal

# Agente B: longevity = 0.5 (genéticamente poco longevo)
genetic_factor_B = 1.0 / 0.5 = 2.0
# Envejece 100% más rápido de lo normal

# Después de 10 años cronológicos:
# Agente A: envejeció 10 × 0.67 = 6.7 años biológicos
# Agente B: envejeció 10 × 2.0 = 20 años biológicos
```

---

## 🚨 Consideraciones y limitaciones

### Principios fundamentales
- **Trade-offs evolutivos**: cada rasgo tiene beneficios y costes
- **Saturación**: los efectos no crecen indefinidamente
- **Coherencia transaccional**: todo pasa por PendingChanges
- **Hitos con efectos reales**: no solo logs, cambios emocionales
- **Asimetría de género**: maternidad más costosa que paternidad
- **Estados extremos combinados**: sinergia de múltiples factores

### Arquitectura

```
TICK DE SIMULACIÓN
   ↓
TemporalSystem.process()
   ├── register_time_pass(delta)
   ├── Para cada agente:
   │   ├── Calcular consumo energético
   │   ├── Calcular recuperación energética
   │   ├── net_change = recovery - consumption
   │   ├── register_emotion_update("energy", net_change)
   │   └── _check_milestones()
   ↓
AgingSystem.process()
   ├── Para cada agente:
   │   ├── 7 factores de envejecimiento
   │   ├── total_multiplier = Π(factores)
   │   └── register_age_increment(biological_increment)
   ↓
WorldState.apply_commit()
```

### Optimizaciones de rendimiento

| Optimización | Descripción |
|--------------|-------------|
| Skip si en pending.deaths | No procesar agentes que mueren |
| Umbrales de hitos | Solo verificar una vez por agente |
| Límite de saturación | Evita cálculos con valores extremos |
| Logging condicional | Solo loguear envejecimientos significativos |
| `max(0.1, longevity)` | Evita división por cero |

### Limitaciones
- No hay ritmos circadianos (día/noche)
- No hay estaciones que afecten el metabolismo directamente
- No hay hibernación o estivalción
- El envejecimiento es continuo (no hay saltos bruscos)
- No hay rejuvenecimiento (el envejecimiento es irreversible)
- No hay telómeros explícitos (solo efecto agregado)
- El límite de saturación reproductiva es arbitrario

### Errores comunes
- ❌ Modificar `person.age` directamente (usar `register_age_increment`)
- ❌ Olvidar el límite de saturación (desgaste infinito)
- ❌ Aplicar carga del embarazo a padres (solo madres)
- ❌ Contar hijos adoptivos en desgaste reproductivo
- ❌ Olvidar el factor genético (longevidad)
- ❌ No considerar estados extremos combinados
- ❌ Asumir que envejecimiento = tiempo cronológico

---

## 🎓 Conceptos clave

### ¿Por qué trade-offs evolutivos?

**Principio de asignación de recursos**:
- La energía es finita
- Invertir en un sistema (inmunidad) reduce recursos para otros
- Esto crea presión selectiva real
- Sin costes, todos los agentes serían "perfectos"

### ¿Por qué saturación en desgaste reproductivo?

**Principio de adaptación fisiológica**:
- El cuerpo se adapta parcialmente al estrés repetido
- Después de muchos hijos, el coste marginal disminuye
- Sin saturación, madres con 20 hijos envejecerían 100% más rápido (irreal)
- La saturación modela la plasticidad fisiológica

### ¿Por qué asimetría de género?

**Principio de inversión parental**:
- La maternidad tiene costes biológicos directos (embarazo, lactancia)
- La paternidad tiene costes indirectos (provisión, protección)
- En mamíferos, la asimetría es pronunciada
- Esto afecta estrategias reproductivas evolutivas

### ¿Por qué estados extremos combinados?

**Principio de sinergia patológica**:
- Enfermedad + desnutrición es peor que la suma de ambos
- El sistema inmune necesita energía para funcionar
- Sin energía, la enfermedad progresa más rápido
- Esto modela la vulnerabilidad de poblaciones marginadas

### ¿Por qué hitos con efectos emocionales?

**Principio de transiciones vitales**:
- La madurez y la senectud son eventos psicológicos significativos
- Generan cambios emocionales reales (no solo logs)
- Afectan decisiones futuras (motivaciones, movimiento)
- Hacen la simulación más narrativamente rica

### ¿Por qué longevidad genética como divisor?

**Principio de potencial de vida**:
- Longevidad alta = genes de reparación eficientes = envejecimiento lento
- Longevidad baja = genes de reparación deficientes = envejecimiento rápido
- Relación inversa: más longevidad → menos envejecimiento
- Fórmula: `factor = 1.0 / longevity`

---

## 📊 Métricas del sistema

| Métrica | Valor |
|---------|-------|
| Archivos del sistema | 2 |
| Factores de consumo energético | 4 |
| Factores de recuperación | 4 |
| Factores de envejecimiento | 7 |
| Hitos biológicos | 2 |
| Tests cubriendo temporal | ~15 |

---

## 🔮 Futuras extensiones

### Planificadas
- [ ] Ritmos circadianos (día/noche afecta metabolismo)
- [ ] Estaciones que afectan recuperación (invierno más duro)
- [ ] Hibernación para ciertas especies
- [ ] Menopausia (fin de desgaste reproductivo)

### Posibles
- [ ] Rejuvenecimiento (en mundos con magia o tecnología avanzada)
- [ ] Telómeros explícitos (medición directa)
- [ ] Estrés oxidativo como variable separada
- [ ] Ejercicio físico que ralentiza envejecimiento
- [ ] Dieta específica que afecta longevidad
- [ ] Cirugías estéticas (reducen edad percibida, no biológica)
- [ ] Criopreservación (pausar envejecimiento)
- [ ] Transhumanismo (cuerpos sintéticos sin envejecimiento)
- [ ] Enfermedades que aceleran envejecimiento (progeria)
- [ ] Síndrome de Down (envejecimiento acelerado)

---

*Documento: 14_TEMPORAL.md*
*Versión: 1.0*