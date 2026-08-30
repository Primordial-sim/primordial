# 10 - Mortalidad

## 📋 Resumen

El **Sistema de Mortalidad** modela la muerte de los agentes mediante un modelo **Gompertz-Makeham expandido** que combina senescencia biológica (desgaste por edad), factores fenotípicos (energía, estrés, traumas), presión ambiental, enfermedades activas, protección social y efectos de consanguinidad. Tras la muerte, un filtro de contingencia (`DeathResolver`) purga todas las intenciones pendientes del fallecido para garantizar coherencia transaccional.

**Filosofía fundamental**: *La muerte no es un evento aleatorio simple: emerge de la interacción entre biología, entorno, relaciones y enfermedad. Cada muerte tiene un diagnóstico forense detallado que explica el "por qué" biológico.*

---

## 🎯 Responsabilidad

**Es responsable de:**
- Calcular el riesgo diario de muerte por senescencia (modelo Gompertz)
- Aplicar penalizaciones fenotípicas (energía, estrés, traumas)
- Aplicar penalizaciones ambientales (densidad poblacional)
- Integrar letalidad de infecciones activas (lethality × virulence)
- Aplicar factores de protección social (familia, reputación)
- Penalizar la endogamia (consanguinidad en menores de 1 año)
- Imponer un límite biológico duro (degradación telomérica)
- Diagnosticar la causa de muerte forense
- Notificar a las relaciones cercanas (evento PARTNER_DEATH)
- Purgar todas las intenciones del fallecido del búfer transaccional (`DeathResolver`)

**NO es responsable de:**
- ❌ Procesar enfermedades activas (eso lo hace `DiseaseSystem`, documento 09)
- ❌ Matar agentes por enfermedades directamente (eso lo hace `DiseaseSystem` en fase sintomática)
- ❌ Reasignar huérfanos tras muerte parental (eso lo hace `AdoptionSystem`, documento 06)
- ❌ Eliminar físicamente al agente del mundo (eso lo hace `WorldState.apply_commit`)
- ❌ Gestionar el duelo de los sobrevivientes (eso lo hace `RelationshipExperienceEngine`)

---

## 🌍 Equivalencia con la vida real

| Concepto del sistema | Equivalencia en la vida real | Unidad |
|---------------------|-----------------------------|--------|
| **Gompertz-Makeham** | Modelo actuarial de mortalidad | Hazard rate |
| **Senescencia** | Envejecimiento celular | Degradación biológica |
| **Límite biológico (hard cap)** | Límite de Hayflick / telómeros | Máximo absoluto |
| **Penalización fenotípica** | Estado físico y psicológico | Salud general |
| **Presión ambiental** | Hacinamiento, falta de recursos | Estrés ambiental |
| **Endogamia** | Depresión endogámica | Consanguinidad |
| **Protección social** | Red familiar y comunitaria | Soporte social |
| **Diagnóstico forense** | Autopsia médica | Causa de muerte |
| **DeathResolver** | Procesamiento post-mortem | Cancelación de planes |
| **PARTNER_DEATH event** | Duelo | Trauma por pérdida |

---

## 📁 Archivos que lo componen

| Archivo | Clase principal | Responsabilidad |
|---------|-----------------|-----------------|
| `systems/mortality/mortality_system.py` | `MortalitySystem` | Motor de mortalidad multifactorial |
| `systems/mortality/death_resolver.py` | `DeathResolver` | Filtro de contingencia transaccional |

---

## 🔄 Flujo de ejecución completo

```
┌─────────────────────────────────────────────────────────────────┐
│          FASE 1: EVALUACIÓN DE MORTALIDAD (MortalitySystem)     │
│                                                                 │
│ Para cada agente vivo:                                          │
│  │                                                               │
│  ├── 1. LÍMITE BIOLÓGICO DURO (Hard Cap):                       │
│  │   ├── adjusted_cap = hard_cap_age_days × longevity           │
│  │   └── Si age >= adjusted_cap:                                │
│  │       ├── register_death(reason="Degradación telomérica")    │
│  │       ├── _notify_partner_death (evento PARTNER_DEATH)       │
│  │       └── skip evaluación probabilística                     │
│  │                                                               │
│  ├── 2. RIESGO PROBABILÍSTICO:                                   │
│  │   ├── pressure = context.get_local_pressure(x, y)            │
│  │   ├── daily_rate = _calculate_multifactorial_risk(...)       │
│  │   └── death_chance = 1 - exp(-daily_rate × delta_days)       │
│  │                                                               │
│  └── 3. Si random < death_chance:                                │
│      ├── reason = _diagnose_cause_of_death(person, pressure)    │
│      ├── register_death(entity_id, reason)                      │
│      └── _notify_partner_death (evento PARTNER_DEATH)           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│      FASE 2: PURGA TRANSACCIONAL (DeathResolver)                │
│                                                                 │
│ Si pending.deaths no está vacío:                                │
│  ├── 1. Cancelar movements de fallecidos                        │
│  ├── 2. Cancelar age_increments de fallecidos                   │
│  ├── 3. Cancelar infections de fallecidos (tuplas)              │
│  ├── 4. Cancelar recoveries de fallecidos (tuplas)              │
│  ├── 5. Cancelar marriages donde alguno murió                   │
│  ├── 6. Cancelar divorces donde alguno murió                    │
│  ├── 7. Cancelar adoptions con fallecidos                       │
│  ├── 8. Cancelar pregnancy_updates de fallecidos                │
│  ├── 9. Cancelar births donde la madre murió                    │
│  ├── 10. Cancelar emotion_updates de fallecidos                 │
│  ├── 11. Cancelar memory_updates de fallecidos                  │
│  ├── 12. Cancelar free_will_flags_updates de fallecidos         │
│  ├── 13. Cancelar motivation_updates de fallecidos              │
│  └── 14. Cancelar migration_targets de fallecidos               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
         WorldState.apply_commit() consolida las muertes
```

---

## 🔧 Componentes del Sistema

---

### 1. MortalitySystem - Motor de Mortalidad

**📁 Archivo**: `systems/mortality/mortality_system.py`
**🌍 Equivalencia real**: Un modelo actuarial médico que determina la probabilidad de muerte considerando edad, salud, entorno y relaciones.

#### Entradas

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `state` | `WorldState` | Estado del mundo |
| `pending` | `PendingChanges` | Búfer transaccional |
| `delta_days` | `float` | Días transcurridos |
| `context` | `EnvironmentContext` | Contexto ambiental |
| `relationship_engine` | `RelationshipExperienceEngine` | Motor de experiencias (opcional) |
| `ancestry_queries` | `AncestryQueries` | Consultas de consanguinidad (opcional) |

#### Flujo interno

```
process(state, pending, delta_days, context)
    │
    └── Para cada person en state.get_all_persons():
        ├── Si entity_id en pending.deaths → skip (ya murió)
        │
        ├── 1. LÍMITE BIOLÓGICO DURO:
        │   ├── adjusted_cap = hard_cap_age_days × longevity
        │   └── Si age >= adjusted_cap:
        │       ├── register_death(reason="Degradación telomérica total")
        │       ├── _notify_partner_death(...)
        │       └── continue
        │
        ├── 2. RIESGO PROBABILÍSTICO:
        │   ├── pressure = context.get_local_pressure(x, y)
        │   ├── daily_rate = _calculate_multifactorial_risk(person, pressure)
        │   └── death_chance = 1 - exp(-daily_rate × delta_days)
        │
        └── 3. Si random < death_chance:
            ├── reason = _diagnose_cause_of_death(person, pressure)
            ├── register_death(entity_id, reason)
            └── _notify_partner_death(...)
```

#### Modelo Gompertz-Makeham expandido

```
total_daily_risk = base_hazard × Π(penalizations) × social_protection
```

Donde cada factor se describe a continuación:

##### 1. Riesgo base por senescencia (Gompertz)

```python
adjusted_beta_years = beta_base / max(genome_clamping, longevity)
adjusted_beta_days = adjusted_beta_years / days_per_year
base_hazard = (alpha_base * exp(adjusted_beta_days * age)) / days_per_year
```

**Interpretación**:
- El riesgo crece exponencialmente con la edad
- Agentes con `longevity` alta envejecen más lentamente
- `genome_clamping` evita que valores muy bajos de longevity causen riesgo extremo
- Dividimos por `days_per_year` para convertir de tasa anual a diaria

##### 2. Penalizaciones fenotípicas

| Factor | Fórmula | Descripción |
|--------|---------|-------------|
| **Energía** | `1 + (1-energy) × 5` | Desnutrición multiplica hasta ×6 |
| **Estrés** | `1 + stress × 2` | Estrés extremo multiplica hasta ×3 |
| **Trauma hacinamiento** | `1 + trauma_overcrowding × 3` | Hasta ×4 |
| **Trauma abandono** | `1 + trauma × (multiplier - 1)` | Hasta ×N |
| **Trauma adopción** | `1 + trauma_adoption × 0.5` | Hasta ×1.5 |

##### 3. Penalización ambiental

```python
excess_pressure = max(0.0, pressure - 1.0)
environmental_penalty = 1.0 + (excess_pressure × density_penalty_multiplier)
```

**Interpretación**: solo el exceso de presión por encima de 1.0 penaliza. Presión moderada (≤1.0) no afecta.

##### 4. Penalización por enfermedades

```python
if is_sick:
    total_infection_risk = Σ(pathogen.lethality × pathogen.virulence)
    raw_penalty = sickness_penalty_multiplier × (1 + total_infection_risk)
    sickness_penalty = max(min_sickness_penalty, raw_penalty)
```

**Interpretación**:
- Cada patógeno activo contribuye con `lethality × virulence`
- Infecciones múltiples se suman
- Hay un mínimo garantizado si el agente está enfermo

##### 5. Factores de protección social (BLOQUE 3)

```python
has_parents = len(person.parents) > 0 or len(person.adoptive_parents) > 0
has_children = person.children_count > 0

if has_parents or has_children:
    protection_factor = 0.2 * reputation_score
    social_protection = max(0.8, 1.0 - protection_factor)
```

**Interpretación**:
- Tener familia (padres o hijos) protege
- Reputación alta = más protección (hasta -20% de riesgo)
- El factor mínimo es 0.8 (máxima protección)

##### 6. Penalización por reputación

```python
reputation_penalty = 1.0 + ((1.0 - reputation_score) × 0.3)
```

**Interpretación**: reputación baja (0.0) multiplica el riesgo por 1.3.

##### 7. Penalización por endogamia

```python
if ancestry_queries and person.age < 365.0:  # Solo primer año de vida
    inbreeding_risk = ancestry_queries.analyze_inbreeding_risk(entity_id)
    if inbreeding_risk > 0.1:
        inbreeding_penalty = 1.0 + (inbreeding_risk × 2.0)
```

**Interpretación**: la consanguinidad solo afecta a menores de 1 año (mortalidad infantil).

##### Fórmula final

```python
total_daily_risk = (
    base_hazard ×
    energy_penalty ×
    stress_penalty ×
    trauma_penalty ×
    abandonment_penalty ×
    adoption_penalty ×
    environmental_penalty ×
    sickness_penalty ×
    social_protection ×
    reputation_penalty ×
    inbreeding_penalty
)
```

#### Diagnóstico forense

```python
def _diagnose_cause_of_death(person, pressure):
    # 1. Si está enfermo: identificar peor patógeno
    if is_sick and energy < 0.2:
        return "Sepsis / Fallo multiorgánico por {pathogen_id}"
    if is_sick:
        return "Infección letal por {pathogen_id}"
    
    # 2. Inanición
    if energy < 0.1:
        return "Agotamiento metabólico extremo (Inanición)"
    
    # 3. Hacinamiento
    if trauma_overcrowding > 0.8 or pressure > 2.0:
        return "Asfixia/Traumatismo severo por hacinamiento"
    
    # 4. Trauma de abandono
    if abandonment_trauma > 0.7 and stress > 0.8:
        return "Colapso sistémico por abandono prolongado"
    
    # 5. Trauma de adopción
    if adoption_trauma > 0.8 and stress > 0.7:
        return "Fallo cardíaco por trauma de reubicación forzada"
    
    # 6. Aislamiento social
    if reputation < 0.2 and stress > 0.7:
        return "Muerte por aislamiento social severo y desnutrición"
    
    # 7. Estrés crónico
    if stress > 0.85:
        return "Colapso cardiovascular inducido por estrés crónico"
    
    # 8. Default
    return "Fallo sistémico por senectud (Causas naturales)"
```

#### Notificación a relaciones

```python
def _notify_partner_death(deceased, state, pending, current_day):
    for rel in deceased._relationships.values():
        if rel.status != RelationshipStatus.EX_PARTNER:
            survivor = state.get_person_by_id(rel.partner_id)
            if survivor and survivor not in pending.deaths:
                rel_strength = sum(m.current_weight(current_day) for m in rel.memories)
                base_intensity = 0.5
                relationship_bonus = min(0.5, rel_strength × 0.002)
                intensity = min(1.0, base_intensity + relationship_bonus)
                
                if rel_strength > 200:
                    context = "perdida_de_ser_querido"
                elif rel_strength > 100:
                    context = "duelo_profundo"
                else:
                    context = "fallecimiento"
                
                event = _MortalityRelationalEvent(
                    event_type=RelationshipEventType.PARTNER_DEATH,
                    intensity=intensity,
                    context=context,
                )
                relationship_engine.process_event(event, survivor, deceased, current_day)
```

**Interpretación**:
- La intensidad del duelo depende de la fuerza de la relación
- Contexto más intenso para relaciones profundas
- Ex-parejas no reciben notificación
- El evento alimenta `RelationshipExperienceEngine` que genera memoria episódica

---

### 2. DeathResolver - Purga Transaccional

**📁 Archivo**: `systems/mortality/death_resolver.py`
**🌍 Equivalencia real**: El procesamiento post-mortem: cancelar citas, planes, embarazos, etc.

#### Responsabilidad

Purgar TODAS las intenciones pendientes del búfer transaccional (`PendingChanges`) que involucren a agentes fallecidos durante el tick actual.

#### Entradas

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `state` | `WorldState` | Estado del mundo |
| `pending` | `PendingChanges` | Búfer transaccional |
| `delta_days` | `float` | Días transcurridos |
| `context` | `EnvironmentContext` | Contexto ambiental |

#### Flujo interno

```
process(state, pending, delta_days, context)
    │
    ├── Si pending.deaths está vacío → return
    │
    ├── muertos_set = set(pending.deaths)
    │
    ├── 1. movements: filtrar por entity_id
    ├── 2. age_increments: filtrar por entity_id
    ├── 3. infections: filtrar tuplas (entity_id, pathogen)
    ├── 4. recoveries: filtrar tuplas (entity_id, pathogen_id)
    ├── 5. marriages: filtrar donde p_a o p_b murió
    ├── 6. divorces: filtrar tuplas donde alguno murió
    ├── 7. adoptions: filtrar donde child, parent_a o parent_b murió
    ├── 8. pregnancy_updates: filtrar por entity_id
    ├── 9. births: filtrar donde mother_id murió (cancelar parto)
    ├── 10. emotion_updates: filtrar por entity_id
    ├── 11. memory_updates: filtrar por entity_id
    ├── 12. free_will_flags_updates: filtrar por entity_id
    ├── 13. motivation_updates: filtrar por entity_id
    └── 14. migration_targets: filtrar por entity_id
```

#### Colecciones purgadas

| Colección | Tipo | Regla de purga |
|-----------|------|---------------|
| `movements` | `Dict[int, Tuple]` | Filtrar por entity_id |
| `age_increments` | `Dict[int, float]` | Filtrar por entity_id |
| `infections` | `List[Tuple[int, Pathogen]]` | Filtrar tupla (entity_id, pathogen) |
| `recoveries` | `List[Tuple[int, str]]` | Filtrar tupla (entity_id, pathogen_id) |
| `marriages` | `Dict[int, int]` | Filtrar si p_a o p_b murió |
| `divorces` | `List[Tuple[int, int]]` | Filtrar si alguno murió |
| `adoptions` | `List[Dict]` | Filtrar si child, parent_a o parent_b murió |
| `pregnancy_updates` | `Dict[int, Dict]` | Filtrar por entity_id |
| `births` | `List[Dict]` | Filtrar donde mother_id murió |
| `emotion_updates` | `Dict[int, List]` | Filtrar por entity_id |
| `memory_updates` | `Dict[int, Dict]` | Filtrar por entity_id |
| `free_will_flags_updates` | `Dict[int, Dict]` | Filtrar por entity_id |
| `motivation_updates` | `Dict[int, Dict]` | Filtrar por entity_id |
| `migration_targets` | `Dict[int, Tuple]` | Filtrar por entity_id |

#### Casos especiales

**Infecciones (tuplas)**:
```python
# pending.infections es List[Tuple[int, Pathogen]], no Dict
pending.infections = [
    (entity_id, pathogen)
    for entity_id, pathogen in pending.infections
    if entity_id not in muertos_set
]
```

**Matrimonios (simétrico)**:
```python
# Ambos deben estar vivos para que el matrimonio proceda
pending.marriages = {
    p_a: p_b
    for p_a, p_b in pending.marriages.items()
    if p_a not in muertos_set and p_b not in muertos_set
}
```

**Nacimientos (cancelación por muerte materna)**:
```python
# Si la madre muere, el bebé no nace
pending.births = [
    birth
    for birth in pending.births
    if birth.get("mother_id") not in muertos_set
]
```

**Adopciones (múltiples participantes)**:
```python
# Cualquiera de los 3 puede haber muerto
pending.adoptions = [
    adop
    for adop in pending.adoptions
    if adop.get("child_id") not in muertos_set
    and adop.get("parent_a") not in muertos_set
    and (adop.get("parent_b") is None or adop.get("parent_b") not in muertos_set)
]
```

---

## 🔗 Interacción entre componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                  MortalitySystem                                │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Hard cap (determinista)                               │  │
│  │    └── Degradación telomérica absoluta                   │  │
│  │                                                           │  │
│  │ 2. Gompertz-Makeham (probabilístico)                     │  │
│  │    ├── base_hazard (senescencia)                          │  │
│  │    ├── × penalizaciones fenotípicas                       │  │
│  │    ├── × ambiental                                        │  │
│  │    ├── × enfermedades                                     │  │
│  │    ├── × social_protection                                │  │
│  │    ├── × reputación                                       │  │
│  │    └── × endogamia                                        │  │
│  │                                                           │  │
│  │ 3. Diagnóstico forense                                   │  │
│  │    └── Identifica causa de muerte específica             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│         │                          │                             │
│         ▼                          ▼                             │
│  pending.register_death     _notify_partner_death                │
│         │                          │                             │
│         │                          ▼                             │
│         │              RelationshipExperienceEngine              │
│         │              (documento 06)                            │
│         │              Genera memoria episódica en sobreviviente │
└─────────┬────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DeathResolver                                  │
│                                                                  │
│  Itera sobre 14 colecciones de pending:                         │
│    movements, age_increments, infections, recoveries,          │
│    marriages, divorces, adoptions, pregnancy_updates,          │
│    births, emotion_updates, memory_updates,                    │
│    free_will_flags_updates, motivation_updates,                │
│    migration_targets                                            │
│                                                                  │
│  Filtra cualquier entrada que involucre a un fallecido         │
└─────────┬───────────────────────────────────────────────────────┘
          │
          ▼
   WorldState.apply_commit()
   (las muertes se consolidan: agentes eliminados)
```

---

## ⚙️ Configuración relevante

```python
# MortalityConfig
config.mortality.alpha_base = 0.0005          # Riesgo base por día
config.mortality.beta_base = 0.085            # Tasa de envejecimiento exponencial
config.mortality.genome_clamping = 0.1        # Clamping mínimo de longevity
config.mortality.base_life_expectancy_days = 25550.0  # ~70 años
config.mortality.hard_cap_age_days = 41975.0  # ~115 años (máximo absoluto)
config.mortality.sickness_penalty_multiplier = 3.0
config.mortality.min_sickness_penalty = 1.5   # Mínimo garantizado si enfermo
config.mortality.density_penalty_multiplier = 2.0

# AdoptionsConfig (usado para trauma de abandono)
config.adoptions.abandonment_mortality_multiplier = 3.0
config.adoptions.max_orphan_age_days = 6205.0  # ~17 años

# TimeConfig
config.time.days_per_year = 365.0
```

### Parámetros hardcodeados

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| Límite de edad inbreeding | 365 días | Mortalidad infantil (primer año) |
| Umbral inbreeding | 0.1 | Consanguinidad significativa |
| Factor inbreeding | 2.0 | Multiplicador del riesgo |
| Protección social mínima | 0.8 | Máximo -20% de riesgo |
| Factor reputación en protección | 0.2 | Moderado |
| Factor reputación en penalización | 0.3 | Moderado |
| Trauma adopción factor | 0.5 | Moderado |
| Umbral trauma hacinamiento | 0.8 | Solo casos graves |
| Umbral trauma abandono | 0.7 | Solo casos graves |
| Umbral trauma adopción | 0.8 | Solo casos graves |
| Umbral reputación baja | 0.2 | Estigmatización severa |
| Umbral estrés extremo | 0.85 | Muy alto |

---

## 🧪 Tests del sistema

| Archivo | Cobertura |
|---------|-----------|
| `tests/unit/test_mortality_system.py` | Riesgo multifactorial, penalizaciones, hard cap |
| `tests/integration/test_regression_bugs.py` | Bug #4: filtrado correcto de tuples en infections/recoveries |
| `tests/integration/test_statistical.py` | Mortalidad realista a largo plazo |

---

## 📝 Ejemplos completos

### Ejemplo 1: Muerte por senectud (causas naturales)

```python
# Humano de 110 años, buena salud
person.age = 40150  # ~110 años
person.genome.get_trait_value("longevity") = 1.0  # Normal
person.emotions = {"energy": 0.6, "stress": 0.3}

# 1. Hard cap: 41975 * 1.0 = 41975 días
#    person.age (40150) < hard_cap → pasa al riesgo probabilístico

# 2. Riesgo probabilístico:
#    adjusted_beta_years = 0.085 / 1.0 = 0.085
#    adjusted_beta_days = 0.085 / 365 = 0.000233
#    base_hazard = (0.0005 * exp(0.000233 * 40150)) / 365
#                = (0.0005 * exp(9.35)) / 365
#                = (0.0005 * 11548) / 365
#                ≈ 0.0158 (1.58% por día)
#    
#    energy_penalty = 1 + (1-0.6)*5 = 3.0
#    stress_penalty = 1 + 0.3*2 = 1.6
#    (otros factores = 1.0 si no aplican)
#    
#    total_daily_risk ≈ 0.0158 * 3.0 * 1.6 ≈ 0.076 (7.6% por día)
#    
#    death_chance = 1 - exp(-0.076 * 1) ≈ 7.3%

# Si random < 0.073:
#   reason = "Fallo sistémico por senectud (Causas naturales)"
#   (ya que energy > 0.1, no está enfermo, stress < 0.85, etc.)
```

### Ejemplo 2: Muerte por enfermedad grave

```python
# Persona de 35 años con infección grave
person.age = 12775  # ~35 años
person.is_sick = True
person.active_pathogens = {
    "Influenza_000123": pathogen_letal,  # lethality=0.8, virulence=1.2
}
person.emotions = {"energy": 0.15, "stress": 0.7}

# 1. Riesgo base bajo por juventud:
#    base_hazard ≈ 0.0005 * exp(0.000233 * 12775) / 365
#                ≈ 0.0005 * exp(2.98) / 365
#                ≈ 0.0005 * 19.7 / 365 ≈ 0.000027

# 2. Penalizaciones:
#    energy_penalty = 1 + (1-0.15)*5 = 5.25 (desnutrición extrema)
#    stress_penalty = 1 + 0.7*2 = 2.4
#    
#    total_infection_risk = 0.8 * 1.2 = 0.96
#    sickness_penalty = max(1.5, 3.0 * (1 + 0.96)) = 5.88
#    
#    total_daily_risk = 0.000027 * 5.25 * 2.4 * 5.88 ≈ 0.002 (0.2% por día)
#    
#    death_chance = 1 - exp(-0.002) ≈ 0.2%

# Si muere, diagnóstico:
#   energy (0.15) < 0.2 → "Sepsis / Fallo multiorgánico por Influenza_000123"
```

### Ejemplo 3: Muerte por hard cap (degradación telomérica)

```python
# Humano muy longevo alcanza el límite
person.age = 41975  # ~115 años (exactamente hard_cap_age_days)
person.genome.get_trait_value("longevity") = 1.0
person.emotions = {"energy": 0.5, "stress": 0.4}  # Buena salud

# 1. Hard cap:
#    adjusted_cap = 41975 * 1.0 = 41975 días
#    person.age (41975) >= adjusted_cap → MUERTE DETERMINISTA

# Razón: "Degradación telomérica total (Límite biológico)"
# No importa qué tan sano esté: es un límite absoluto
```

### Ejemplo 4: Mortalidad infantil por endogamia

```python
# Bebé de 100 días, padres primos hermanos
person.age = 100  # < 365 días
ancestry_queries.analyze_inbreeding_risk(person.entity_id) = 0.25

# Penalización por endogamia:
#    inbreeding_penalty = 1.0 + (0.25 * 2.0) = 1.5 (50% más riesgo)

# Si los padres son hermanos (inbreeding_risk = 0.5):
#    inbreeding_penalty = 1.0 + (0.5 * 2.0) = 2.0 (100% más riesgo)
```

### Ejemplo 5: Protección social

```python
# Persona casada con 2 hijos, reputación alta
person.parents = [101, 102]  # Padres vivos
person.children_count = 2
person.reputation_score = 0.9

# Protección social:
#    has_parents = True
#    has_children = True
#    protection_factor = 0.2 * 0.9 = 0.18
#    social_protection = max(0.8, 1.0 - 0.18) = 0.82 (18% de protección)

# Penalización por reputación:
#    reputation_penalty = 1 + (1-0.9) * 0.3 = 1.03 (casi sin efecto)
```

### Ejemplo 6: DeathResolver purgando infecciones

```python
# Tres agentes murieron este tick
pending.deaths = {101: "reason1", 102: "reason2", 103: "reason3"}

# Infecciones pendientes (tuplas)
pending.infections = [
    (101, influenza_pathogen),  # Muerto → purgar
    (200, coronavirus_pathogen), # Vivo → mantener
    (102, poxvirus_pathogen),   # Muerto → purgar
]

# Después de DeathResolver:
pending.infections = [
    (200, coronavirus_pathogen),
]
```

### Ejemplo 7: DeathResolver cancelando parto

```python
# Madre muere durante el embarazo
pending.deaths = {101: "Complicaciones"}
pending.births = [
    {"mother_id": 101, "father_id": 200, "x": 50, "y": 50, "genome": ...},
    {"mother_id": 300, "father_id": 400, "x": 60, "y": 60, "genome": ...},
]
pending.pregnancy_updates = {
    101: {"is_pregnant": True, "pregnancy_days": 200.0, ...},
    300: {"is_pregnant": True, "pregnancy_days": 150.0, ...},
}

# Después de DeathResolver:
pending.births = [
    {"mother_id": 300, "father_id": 400, ...},  # Madre viva
]
pending.pregnancy_updates = {
    300: {"is_pregnant": True, ...},  # Madre viva
}

# El bebé de la madre 101 no nace
```

---

## 🚨 Consideraciones y limitaciones

### Principios fundamentales
- **Modelo Gompertz-Makeham**: estándar actuarial + factores adicionales
- **Límite biológico duro**: nadie supera `hard_cap_age_days × longevity`
- **Muerte multifactorial**: nunca una sola causa, siempre combinación
- **Diagnóstico forense**: cada muerte tiene una razón específica
- **Transaccionalidad**: las muertes afectan el búfer pendiente
- **Notificación social**: los sobrevivientes reciben evento de duelo

### Arquitectura de decisión

```
GENOMA (longevity)
   ↓
HARD CAP (determinista)
   ↓ (si no supera)
GOMPERTZ (riesgo base exponencial)
   ↓
× FACTORES MULTIPLICATIVOS
   ↓
RANDOM (probabilístico)
   ↓ (si muere)
DIAGNÓSTICO FORENSE
   ↓
NOTIFICACIÓN SOCIAL
   ↓
PURGA TRANSACCIONAL (DeathResolver)
   ↓
CONSOLIDACIÓN (WorldState.apply_commit)
```

### Optimizaciones de rendimiento

| Optimización | Descripción |
|--------------|-------------|
| Skip si ya en pending.deaths | Evita doble procesamiento |
| Hard cap primero (determinista) | Evita cálculo probabilístico |
| Early return en DeathResolver | Si no hay muertes, no hacer nada |
| Set para búsquedas | `muertos_set` en O(1) |
| Filtros por lista | `hasattr` antes de filtrar colecciones opcionales |

### Limitaciones
- No hay muerte por depredación (no hay depredadores)
- No hay muerte por accidentes (caídas, ahogamientos)
- No hay muerte por violencia directa (guerras, asesinatos)
- No hay muerte por hambruna aguda (solo por inanición progresiva)
- No hay resurrección (las muertes son permanentes)
- No hay medicina avanzada que evite muertes

### Errores comunes

| Error | Consecuencia | Solución |
|-------|-------------|----------|
| ❌ Olvidar DeathResolver | Inconsistencias en commit | Ejecutar tras MortalitySystem |
| ❌ Tratar infections como Dict | Error al filtrar tuplas | Usar comprensión de tuplas |
| ❌ Notificar a ex-parejas | Duelo no deseado | Filtrar `EX_PARTNER` |
| ❌ Notificar a también fallecidos | Error en RelationshipEngine | Filtrar `pending.deaths` |
| ❌ Permitir partos de madres muertas | Huérfanos instantáneos | Cancelar en DeathResolver |
| ❌ Calcular riesgo con longevity=0 | División por cero | Usar `max(genome_clamping, longevity)` |

---

## 🎓 Conceptos clave

### ¿Por qué Gompertz-Makeham?

**Principio actuarial**:
- Gompertz describe el crecimiento exponencial del riesgo con la edad
- Makeham añade un término constante (riesgo basal)
- Es el modelo estándar usado por compañías de seguros
- Captura la senescencia biológica de forma realista

### ¿Por qué límite biológico duro?

**Principio del límite de Hayflick**:
- Los telómeros se acortan con cada división celular
- Existe un límite absoluto a la vida humana (~115-125 años)
- Sin este límite, agentes con longevity alta vivirían miles de años
- Garantiza rotación generacional

### ¿Por qué diagnóstico forense?

**Principio de transparencia**:
- Cada muerte tiene una razón legible
- Permite análisis epidemiológico post-mortem
- Ayuda a depurar el simulador
- Hace el mundo más narrativo

### ¿Por qué DeathResolver es necesario?

**Principio de coherencia transaccional**:
- Durante un tick, múltiples sistemas registran intenciones
- Si un agente muere a mitad del tick, esas intenciones son inválidas
- Sin purga, el commit crearía estados inconsistentes
- Ejemplos: movimientos de agentes muertos, partos de madres muertas

### ¿Por qué protección social reduce mortalidad?

**Principio de salud social**:
- Estudios reales muestran que personas con redes sociales fuertes viven más
- Cuidado mutuo, detección temprana de enfermedades
- Apoyo psicológico reduce estrés
- La soledad es un factor de riesgo comparable al tabaquismo

### ¿Por qué penalizar endogamia solo en menores?

**Principio biológico**:
- La depresión endogámica afecta principalmente a recién nacidos
- Malformaciones congénitas, sistemas inmunes débiles
- Los adultos con consanguinidad sobreviven pero pueden transmitirla
- En la vida real, mortalidad infantil por endogamia es significativa

### ¿Por qué notificar PARTNER_DEATH?

**Principio de continuidad relacional**:
- La muerte de un ser querido es uno de los eventos más traumáticos
- Genera duelo en el sobreviviente
- Puede desencadenar depresión, cambios conductuales
- En casos extremos: "morir de pena" (broken heart syndrome)

---

## 📊 Métricas del sistema

| Métrica | Valor |
|---------|-------|
| Archivos del sistema | 2 |
| Factores de riesgo | 11 |
| Colecciones purgadas | 14 |
| Tipos de diagnóstico | 8+ |
| Tests cubriendo mortalidad | ~10 |

---

## 🔮 Futuras extensiones

### Planificadas
- [ ] Muerte por depredación (interacción entre especies)
- [ ] Muerte por accidentes (caídas, ahogamientos)
- [ ] Muerte por violencia (guerras, asesinatos)
- [ ] Medicina preventiva (reduce riesgo base)

### Posibles
- [ ] Resucitación (en mundos con magia)
- [ ] Cryopreservación (animación suspendida)
- [ ] Transhumanismo (upload de conciencia)
- [ ] Sacrificios rituales (cultura)
- [ ] Suicidio (en casos extremos de depresión)
- [ ] Eutanasia (enfermedades terminales)
- [ ] Epidemias masivas (peste negra)
- [ ] Hambrunas globales (sequías prolongadas)
- [ ] Efecto viudedad (morir poco después de la pareja)

---

*Documento: 10_MORTALIDAD.md*
*Versión: 1.0*