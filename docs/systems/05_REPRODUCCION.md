# 05 - Reproducción

## 📋 Resumen

El **Sistema de Reproducción** modela el ciclo reproductivo completo de los organismos del simulador: desde la concepción hasta el nacimiento, incluyendo gestación interna (vivíparos), incubación de huevos (ovíparos) y reproducción asexual (plantas, bacterias).

**Filosofía fundamental**: *La reproducción es una capacidad emergente del genoma. El sistema no sabe qué especie es; solo consulta sus rasgos y actúa en consecuencia.*

---

## 🎯 Responsabilidad

**Es responsable de:**
- Detectar oportunidades de concepción entre parejas fértiles (`ConceptionSystem`)
- Procesar la gestación interna de organismos vivíparos (`GestationSystem`)
- Gestionar huevos puestos por organismos ovíparos (`EggSystem`)
- Modelar el ciclo de vida de los huevos (`Egg`)
- Derivar capacidades reproductivas del genoma (`ReproductiveCapabilities`)
- Implementar restricciones biológicas realistas (infertilidad, abortos, mortalidad materna)
- Soportar tres tipos de reproducción: sexual, asexual y partenogénesis
- Soportar dos tipos de gestación: vivípara (embarazo) y ovípara (huevos)
- Integrar con `PendingChanges` para coherencia transaccional

**NO es responsable de:**
- ❌ Decidir qué agentes forman parejas (eso lo hacen `MarriageSystem` y `CompatibilityEngine`)
- ❌ Calcular compatibilidad sexual (eso lo hace `CompatibilityEngine`)
- ❌ Procesar el crecimiento postnatal (eso lo hace `AgingSystem`)
- ❌ Gestionar adopciones (eso lo hace `AdoptionSystem`)
- ❌ Generar el genoma de los descendientes (eso lo hace `Genome.combine()`)

---

## 🌍 Equivalencia con la vida real

| Concepto del sistema | Equivalencia en la vida real | Unidad |
|---------------------|-----------------------------|--------|
| **ConceptionSystem** | Proceso de fertilización | Ovulación/cópula |
| **GestationSystem** | Embarazo en mamíferos | Gestación uterina |
| **EggSystem** | Incubación de huevos | Nido + calor |
| **Egg** | Huevo con embrión | Cigoto encapsulado |
| **ReproductiveCapabilities** | Estrategia reproductiva | r/K selection |
| **conception_chance** | Probabilidad de embarazo | Fertilidad cíclica |
| **litter_size** | Tamaño de camada | Número de crías por parto |
| **gestation_days** | Duración de gestación | Meses de embarazo |
| **miscarriage** | Aborto espontáneo | Pérdida gestacional |
| **maternal_mortality** | Muerte durante el parto | Riesgo obstétrico |
| **postpartum_cooldown** | Periodo de lactancia | Amenorrea posparto |
| **premature_birth** | Parto prematuro | Nacimiento antes de término |

---

## 📁 Archivos que lo componen

| Archivo | Clase principal | Responsabilidad |
|---------|-----------------|-----------------|
| `systems/reproduction/conception_system.py` | `ConceptionSystem` | Motor de concepción |
| `systems/reproduction/gestation_system.py` | `GestationSystem` | Motor de gestación |
| `systems/reproduction/egg_system.py` | `EggSystem` | Procesador de huevos |
| `systems/reproduction/egg_model.py` | `Egg`, `EggStatus` | Modelo de datos de huevo |
| `systems/reproduction/reproductive_capabilities.py` | `ReproductiveCapabilities` | Capacidades derivadas del genoma |

---

## 🔄 Flujo de ejecución completo

```
┌─────────────────────────────────────────────────────────────────┐
│              CICLO REPRODUCTIVO COMPLETO                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 1: CONCEPCIÓN (ConceptionSystem)                           │
│                                                                 │
│ Para cada agente elegible:                                      │
│  1. Consultar ReproductiveCapabilities.from_genome(genome)      │
│  2. Verificar: can_reproduce, edad, salud, energía              │
│  3. Verificar periodo posparto refractario                      │
│  4. Si requiere pareja: buscar partner_id                       │
│  5. Calcular conception_chance (fertilidad multiplicativa)      │
│  6. Si random() < conception_chance:                            │
│     ├── Vivíparos: pending.register_pregnancy_update(...)       │
│     ├── Ovíparos: crear Egg y añadir a pending.new_eggs         │
│     └── Asexuales: pending.register_birth(...) directamente     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
┌─────────────────────────┐   ┌──────────────────────────┐
│ VIVÍPAROS               │   │ OVÍPAROS                 │
│ (Fase 2: GestationSys)  │   │ (Fase 3: EggSystem)      │
│                         │   │                          │
│ Procesa embarazos:      │   │ Procesa huevos:          │
│ ├── Avanza días         │   │ ├── Recoge new_eggs      │
│ ├── Verifica abortos    │   │ ├── Avanza incubación    │
│ ├── Verifica parto      │   │ ├── Verifica mortalidad  │
│ │   prematuro           │   │ └── Eclosiona si procede │
│ └── Si término:         │   │                          │
│     register_birth()    │   │ Al eclosionar:           │
│                         │   │   register_birth()       │
└─────────────────────────┘   └──────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 4: NACIMIENTO                                              │
│                                                                 │
│ pending.register_birth(mother_id, father_id, x, y, genome)      │
│                                                                 │
│ WorldState.apply_commit() procesa:                              │
│ ├── Crear nuevo Person con el genoma combinado                  │
│ ├── Asignar padres (mother_id, father_id)                       │
│ ├── Colocar en posición cercana a la madre                      │
│ ├── Añadir a núcleo residencial                                 │
│ └── Generar recuerdo de nacimiento en la madre                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes del Sistema

---

### 1. ReproductiveCapabilities - Capacidades Derivadas del Genoma

**📁 Archivo**: `systems/reproduction/reproductive_capabilities.py`
**🌍 Equivalencia real**: La estrategia reproductiva de un organismo, determinada por su biología fundamental (continuum r/K).

#### Atributos

| Atributo | Tipo | Equivalencia real | Descripción |
|----------|------|-------------------|-------------|
| `can_reproduce` | `bool` | Fértil o estéril | ¿Puede reproducirse? |
| `reproduction_type` | `str` | Modo reproductivo | "asexual" / "sexual" / "parthenogenesis" |
| `requires_partner` | `bool` | Necesita apareamiento | ¿Requiere pareja directa? |
| `can_gestate` | `bool` | Capacidad gestacional | ¿Puede incubar internamente? |
| `gestation_type` | `str` | Tipo de desarrollo | "viviparous" / "oviparous" / "none" |
| `gestation_days` | `float` | Duración gestación/incubación | Días hasta nacimiento |
| `has_parental_care` | `bool` | Cuidado parental | ¿Cuida a las crías? |
| `care_duration_days` | `float` | Periodo de cuidado | Días de protección |
| `can_conceive` | `bool` | Capacidad de embarazo | Solo vivíparos |
| `has_postpartum` | `bool` | Periodo posparto | Solo mamíferos |
| `fertility_level` | `float` | Fertilidad efectiva | [0.0-1.0] |
| `litter_size_min` | `int` | Mínimo de crías | Tamaño mínimo de camada |
| `litter_size_max` | `int` | Máximo de crías | Tamaño máximo de camada |

#### Reglas de derivación desde el genoma

| Rasgo consultado | Criterio | Resultado |
|------------------|----------|-----------|
| `fertility`, `metabolism` | `fertility > 0` AND `metabolism > 0.1` | `can_reproduce = True` |
| `nervous_system` | `> 0.1` | `reproduction_type = "sexual"` |
| `nervous_system` | `≤ 0.1` | `reproduction_type = "asexual"` |
| `sociability` | `≥ 0.6` | `requires_partner = True` (cópula) |
| `nervous_system`, `heterotrophy` | ambos `≥ 0.7` | `gestation_type = "viviparous"` (mamíferos) |
| `nervous_system` | `> 0.3` pero no mamífero | `gestation_type = "oviparous"` (aves, reptiles) |
| `intelligence`, `sociability` | `> 0.5` y `> 0.6` | `has_parental_care = True` |
| `longevity` | Alta (≥0.7) | Camadas pequeñas, gestación larga (estrategia K) |
| `longevity` | Baja (≤0.3) | Camadas grandes, gestación corta (estrategia r) |

#### Flujo interno

```
from_genome(genome)
    │
    ├── Consultar rasgos: fertility, metabolism, nervous_system,
    │   intelligence, sociability, heterotrophy, longevity
    │
    ├── Determinar tipo de reproducción
    │   ├── nervous_system > 0.1 → "sexual"
    │   └── else → "asexual"
    │
    ├── Determinar tipo de gestación
    │   ├── nervous_system >= 0.7 AND heterotrophy >= 0.7
    │   │   → "viviparous" (mamíferos)
    │   ├── nervous_system > 0.3 → "oviparous"
    │   └── else → "none"
    │
    ├── Calcular duración de gestación
    │   ├── Vivíparos: longevity * 270 días (clamp [30, 300])
    │   └── Ovíparos: longevity * 30 días (clamp [7, 60])
    │
    ├── Calcular tamaño de camada
    │   ├── Vivíparos: max(1, 3 - longevity)
    │   ├── Ovíparos: max(2, 10 - longevity * 2)
    │   └── Asexuales: max(1, 100 / longevity)
    │
    └── Retornar ReproductiveCapabilities(...)
```

#### Ejemplos

```python
# Humano
human_caps = ReproductiveCapabilities.from_genome(human_genome)
print(human_caps.gestation_type)     # "viviparous"
print(human_caps.gestation_days)     # 270.0
print(human_caps.has_parental_care)  # True
print(human_caps.litter_size_min)    # 1
print(human_caps.litter_size_max)    # 2

# Pez
fish_caps = ReproductiveCapabilities.from_genome(fish_genome)
print(fish_caps.gestation_type)     # "oviparous"
print(fish_caps.requires_partner)   # False (fertilización externa)
print(fish_caps.litter_size_max)    # ~8-10

# Bacteria
bacteria_caps = ReproductiveCapabilities.from_genome(bacteria_genome)
print(bacteria_caps.reproduction_type)  # "asexual"
print(bacteria_caps.can_gestate)        # False
print(bacteria_caps.litter_size_max)    # ~100
```

#### Consideraciones

- **Inmutable**: una vez creada, no se modifica
- **Determinista**: mismo genoma → mismas capacidades
- **No conoce especies**: solo consulta rasgos
- Si un rasgo no existe, usa valores por defecto apropiados

---

### 2. ConceptionSystem - Motor de Concepción

**📁 Archivo**: `systems/reproduction/conception_system.py`
**🌍 Equivalencia real**: El proceso de fertilización: ovulación, cópula, y unión de gametos.

#### Entradas

| Parámetro | Tipo | Equivalencia real | Descripción |
|-----------|------|-------------------|-------------|
| `state` | `WorldState` | Población actual | Todos los agentes |
| `pending` | `PendingChanges` | Búfer transaccional | Donde se registran embarazos/huevos |
| `delta_days` | `float` | Tiempo transcurrido | Días del tick |
| `context` | `EnvironmentContext` | Entorno | Presión social, recursos |

#### Flujo interno por agente

```
Para cada person en state.get_all_persons():
    │
    ├── Si person.entity_id en pending.deaths → skip
    │
    ├── repro_caps = ReproductiveCapabilities.from_genome(genome)
    ├── Si NOT repro_caps.can_reproduce → skip
    │
    ├── Verificar sexo para gestación
    │   ├── Si requiere pareja y can_gestate_female_only:
    │   │   └── Si gender != 'F' → skip
    │   └── Si no requiere pareja → sin restricción
    │
    ├── Verificar periodo posparto (90 días default)
    │   └── Si current_day - last_birth_day < cooldown → skip
    │
    ├── acquired_fertility_modifier = _calculate_acquired_fertility(person)
    ├── Si modifier ≤ 0.05 → skip (estéril adquirido)
    │
    ├── Determinar pareja
    │   ├── Si requiere pareja: buscar partner_id
    │   │   ├── Si partner is_pregnant → skip (doble embarazo)
    │   │   └── Si partner ya en pending.pregnancy_updates → skip
    │   └── Si no requiere pareja: partner = None
    │
    ├── Calcular conception_chance
    │   ├── base_chance (default: 0.02)
    │   ├── × fertility_modifier (genético, multiplicativo)
    │   ├── × energy_multiplier (mínimo de ambos)
    │   ├── × acquired_modifier (edad, salud, estrés)
    │   └── / k_strategy_penalty (longevity promedio)
    │
    └── Si random() < conception_chance:
        ├── litter_size = random(min, max)
        │
        ├── Si vivíparo:
        │   └── pending.register_pregnancy_update(
        │           entity_id, is_pregnant=True, pregnancy_days=0.0,
        │           failed_increment=0, litter_size
        │       )
        │
        ├── Si ovíparo:
        │   └── _lay_eggs(mother, partner, litter_size, ...)
        │       ├── Para cada huevo:
        │       │   ├── child_genome = mother.combine(father) o replicate()
        │       │   └── Crear Egg y añadir a pending.new_eggs
        │       └── Registrar memoria de puesta
        │
        └── Si asexual:
            └── _asexual_reproduction(parent, litter_size, ...)
                ├── Para cada descendiente:
                │   └── child_genome = parent.replicate()
                └── pending.register_birth(...) directamente
```

#### Cálculo de fertilidad adquirida

| Factor | Condición | Modificador |
|--------|-----------|-------------|
| Edad joven | `age < min_fertility_age` | `(age / min_age) * 0.5` |
| Edad avanzada | `age > max_fertility_age` | `max(0.05, 1 - (over / 3650))` |
| Enfermedad | `is_sick == True` | `× 0.4` |
| Estrés extremo | `stress > 0.7` | `1 - ((stress-0.7)/0.3) * 0.6` |
| Baja energía | `energy < 0.4` | `energy / 0.4` |
| Trauma severo | `trauma_sickness > 0.5` | `× 0.7` |

#### Cálculo de probabilidad de concepción

```python
base_chance = 0.02  # 2% base por tick

# Fertilidad genética multiplicativa
mother_fertility = genome.get_trait_value("fertility")
fertility_modifier = mother_fertility * repro_caps.fertility_level

if partner is not None:
    father_fertility = partner.genome.get_trait_value("fertility")
    fertility_modifier *= father_fertility  # Multiplicativo, no promedio
else:
    fertility_modifier *= 0.8  # Asexual: ligera penalización

# Energía limitante
energy_multiplier = min(person.energy, partner.energy)  # o solo person

# Estrategia K: especies longevas se reproducen menos
avg_longevity = max(0.3, average(parent1.longevity, parent2.longevity))
k_strategy_penalty = avg_longevity

# Probabilidad final
final_chance = (base_chance * fertility_modifier * 
                energy_multiplier * acquired_modifier) / k_strategy_penalty
final_chance = clamp(0.0, 0.5, final_chance)
```

#### Consideraciones

- **Prevención de doble embarazo**: si el partner ya está embarazada o en pending, se descarta
- **Fertilidad multiplicativa**: la probabilidad es el producto, no el promedio, de las fertilidades
- **Periodo posparto**: 90 días de cooldown después de cada parto
- **Verificación de sexo**: solo las hembras pueden gestar (excepto hermafroditas)
- **Partenogénesis**: reproducción sexual sin macho (algunas especies)

---

### 3. GestationSystem - Motor de Gestación

**📁 Archivo**: `systems/reproduction/gestation_system.py`
**🌍 Equivalencia real**: El embarazo en mamíferos, con todos sus riesgos biológicos.

#### Entradas

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `state` | `WorldState` | Estado del mundo |
| `pending` | `PendingChanges` | Búfer transaccional |
| `delta_days` | `float` | Días transcurridos |
| `context` | `EnvironmentContext` | Contexto ambiental |

#### Flujo interno

```
Para cada person embarazada:
    │
    ├── Si person.entity_id en pending.deaths → skip
    ├── Si NOT is_pregnant → skip
    │
    ├── repro_caps = ReproductiveCapabilities.from_genome(genome)
    ├── Si NOT repro_caps.can_gestate → skip
    ├── Si NOT repro_caps.is_viviparous() → skip
    │   (los ovíparos usan EggSystem)
    │
    ├── gestation_duration = repro_caps.gestation_days
    ├── new_pregnancy_days = pregnancy_days + delta_days
    │
    ├── complication = _check_gestation_complications(...)
    │
    ├── Si complication == "miscarriage":
    │   ├── pending.register_pregnancy_update(
    │   │       entity_id, is_pregnant=False, pregnancy_days=0.0,
    │   │       failed_increment=1
    │   │   )
    │   └── Registrar memoria TYPE_DISEASE (aborto espontáneo)
    │
    ├── Si complication == "premature_birth":
    │   └── _execute_premature_birth(mother, state, pending, current_day)
    │
    ├── Si new_pregnancy_days >= gestation_duration:
    │   └── _execute_full_term_birth(mother, state, pending, current_day)
    │
    └── Else (continúa embarazo):
        └── pending.register_pregnancy_update(
                entity_id, is_pregnant=True,
                pregnancy_days=new_pregnancy_days,
                failed_increment=0, litter_size
            )
```

#### Riesgos de aborto espontáneo

| Factor | Condición | Multiplicador |
|--------|-----------|---------------|
| Riesgo base (1er trimestre) | `pregnancy_days < 25%` | 0.0001 |
| Riesgo base (resto) | `pregnancy_days ≥ 25%` | 0.00005 |
| Desnutrición severa | `energy < 0.2` | ×5 |
| Estrés extremo | `stress > 0.8` | ×2.5 |
| Enfermedad activa | `is_sick == True` | ×3 |
| Múltiples infecciones | `infecciones > 2` | ×2 adicional |
| Edad avanzada | `age > max_fertility_age` | ×3 |

#### Parto prematuro

- **Umbral**: después del 70% de la gestación
- **Desencadenantes**: estrés extremo (>0.9) + múltiples infecciones
- **Consecuencias**: riesgo fetal aumentado (15% mortalidad), riesgo materno ×2

#### Ejecución del parto a término

```
_execute_full_term_birth(mother, state, pending, current_day)
    │
    ├── 1. Calcular riesgo de mortalidad materna
    │   └── base_risk = 0.001 (ajustado por edad, salud, energía, estrés)
    │
    ├── 2. Si random() < maternal_mortality_risk:
    │   └── pending.register_death(mother.entity_id, reason="parto")
    │
    ├── 3. Obtener genoma del padre (si existe)
    │
    └── 4. Para cada descendiente (litter_size):
        ├── Si hay padre: child_genome = mother.combine(father)
        ├── Si no hay padre: child_genome = mother.replicate()
        ├── Posición: cerca de la madre (±2 tiles)
        └── pending.register_birth(mother_id, father_id, x, y, genome)
```

#### Factores de mortalidad materna

| Factor | Multiplicador |
|--------|---------------|
| Riesgo base | 0.001 (0.1%) |
| Edad avanzada | ×3 |
| Edad muy joven (<30% de max_fertility_age) | ×2 |
| Enfermedad activa | ×2 |
| Desnutrición (energy < 0.3) | ×2.5 |
| Estrés extremo (stress > 0.8) | ×1.5 |
| Camada grande (>2 crías) | ×(1 + (litter-2) * 0.2) |
| **Cap máximo** | **10%** |

#### Consideraciones

- Solo procesa **vivíparos** (los ovíparos usan `EggSystem`)
- El primer trimestre (25% de la gestación) tiene menor riesgo de aborto
- El parto prematuro solo puede ocurrir después del 70% de gestación
- La mortalidad materna es rara pero posible (0.1% base)
- Los nacimientos múltiples son independientes (pueden morir algunos)

---

### 4. EggSystem - Procesador de Huevos

**📁 Archivo**: `systems/reproduction/egg_system.py`
**🌍 Equivalencia real**: Un nido donde los huevos se incuban, con riesgos ambientales de depredación, clima, etc.

#### Entradas

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `state` | `WorldState` | Estado del mundo (contiene `active_eggs`) |
| `pending` | `PendingChanges` | Búfer (contiene `new_eggs`) |
| `delta_days` | `float` | Días transcurridos |
| `context` | `EnvironmentContext` | Presión ambiental |

#### Flujo interno

```
process(state, pending, delta_days, context)
    │
    ├── 1. Recoger huevos nuevos de pending.new_eggs
    │   └── Añadir a state.active_eggs
    │   └── pending.new_eggs = []
    │
    ├── 2. Procesar cada huevo activo:
    │   ├── Si NOT is_alive → marcar para eliminación
    │   ├── Si status == LAID:
    │   │   └── start_incubation() (LAID → INCUBATING)
    │   ├── advance_incubation(delta_days)
    │   ├── _check_environmental_mortality(egg, context, delta_days)
    │   │   └── Si muere: egg.die() → marcar para eliminación
    │   └── Si should_hatch():
    │       ├── _execute_hatch(egg, state, pending, current_day)
    │       │   ├── pending.register_birth(mother, father, x, y, genome)
    │       │   └── Registrar memoria de eclosión en la madre
    │       ├── egg.hatch() (INCUBATING → HATCHED)
    │       └── marcar para eliminación
    │
    └── 3. Eliminar huevos procesados de state.active_eggs
```

#### Factores de mortalidad ambiental

```python
# Riesgo base diario (definido en el Egg)
mortality_chance = egg.mortality_risk * delta_days

# Presión ambiental local
local_pressure = context.get_local_pressure(int(egg.x), int(egg.y))
if local_pressure > 1.5:
    mortality_chance *= 1.5
```

#### Ejemplos

```python
# Consultar huevos activos
egg_count = egg_system.get_egg_count(state)
print(f"Huevos activos: {egg_count}")

# Consultar huevos de una madre
mother_eggs = egg_system.get_eggs_by_mother(state, mother_id=42)
for egg in mother_eggs:
    print(f"Huevo {egg.egg_id}: {egg.progress:.1%} incubado")
```

#### Consideraciones

- Los huevos son entidades independientes almacenadas en `state.active_eggs`
- El buffer `pending.new_eggs` se limpia después de recoger
- La mortalidad ambiental considera presión local (hacinamiento)
- Los huevos muertos se eliminan al final del tick
- Los huevos eclosionados generan `register_birth` igual que vivíparos

---

### 5. Egg - Modelo de Datos

**📁 Archivo**: `systems/reproduction/egg_model.py`
**🌍 Equivalencia real**: Un huevo individual con embrión en desarrollo.

#### Atributos

| Atributo | Tipo | Equivalencia real | Descripción |
|----------|------|-------------------|-------------|
| `egg_id` | `int` | Identificación única | ID auto-generado |
| `mother_id` | `int` | Madre biológica | ID de la madre |
| `father_id` | `Optional[int]` | Padre biológico | None si partenogénesis |
| `x`, `y` | `float` | Posición del nido | Coordenadas |
| `genome` | `Genome` | ADN del embrión | Combinado/clonado |
| `laid_day` | `float` | Día de puesta | Marca temporal |
| `incubation_days` | `float` | Duración incubación | Días totales necesarios |
| `current_incubation` | `float` | Progreso actual | Días transcurridos |
| `status` | `EggStatus` | Estado del ciclo | LAID/INCUBATING/HATCHED/DEAD |
| `mortality_risk` | `float` | Riesgo diario | Default: 0.001 |
| `clutch_id` | `Optional[int]` | Nidada | Huevos puestos juntos |

#### Estados del ciclo de vida (EggStatus)

| Estado | Descripción | Equivalencia real |
|--------|-------------|-------------------|
| `LAID` | Recién puesto | Huevo fresco |
| `INCUBATING` | En incubación | Embrión desarrollándose |
| `HATCHED` | Eclosionado | Cría nacida |
| `DEAD` | Muerto | Pérdida (depredación, clima) |
| `ABANDONED` | Abandonado | Sin cuidado parental |

#### Transiciones de estado

```
LAID ──────► INCUBATING ──────► HATCHED
 │                │
 └───────────────► DEAD
```

#### Propiedades computadas

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `is_incubating` | `bool` | `status == INCUBATING` |
| `is_alive` | `bool` | `status in (LAID, INCUBATING)` |
| `progress` | `float` | `current_incubation / incubation_days` [0.0-1.0] |
| `days_until_hatch` | `float` | `incubation_days - current_incubation` |

#### Métodos

| Método | Descripción |
|--------|-------------|
| `start_incubation()` | LAID → INCUBATING |
| `advance_incubation(delta)` | Suma días de incubación |
| `hatch()` | Marca como HATCHED |
| `die()` | Marca como DEAD |
| `abandon()` | Marca como ABANDONED |
| `should_hatch()` | Verifica si debe eclosionar |
| `to_dict()` | Serialización para debugging |

#### Ejemplos

```python
# Crear un huevo
egg = Egg(
    egg_id=0,  # Se auto-asigna
    mother_id=42,
    father_id=43,
    x=50.0,
    y=50.0,
    genome=child_genome,
    laid_day=100.0,
    incubation_days=30.0,
    clutch_id=1,
)

# Ciclo de vida
print(egg.status)  # EggStatus.LAID
egg.start_incubation()
print(egg.status)  # EggStatus.INCUBATING

# Avanzar incubación
egg.advance_incubation(delta_days=15.0)
print(egg.progress)  # 0.5 (50%)
print(egg.days_until_hatch)  # 15.0

# Verificar eclosión
if egg.should_hatch():
    egg.hatch()
    print(egg.status)  # EggStatus.HATCHED
```

#### Consideraciones

- `egg_id` se auto-genera si no se proporciona (contador global)
- Es un `dataclass` con serialización a dict
- El genoma puede venir de `combine()` (sexual) o `replicate()` (asexual)
- `clutch_id` agrupa huevos puestos en el mismo evento

---

## 🔗 Interacción entre componentes

```
┌─────────────────────────────────────────────────────────────────┐
│              GENOMA (fuente de verdad)                          │
│      Genome con rasgos: fertility, metabolism, nervous_system,  │
│      intelligence, sociability, heterotrophy, longevity         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ consultado por
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│         ReproductiveCapabilities (inmutable, derivado)          │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │ can_reproduce, reproduction_type, requires_partner,     │  │
│   │ gestation_type, gestation_days, has_parental_care,      │  │
│   │ litter_size_min, litter_size_max, fertility_level       │  │
│   └─────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ usado por
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  ConceptionSystem                               │
│   Detecta oportunidades de concepción y:                        │
│   ├── Vivíparos → pending.register_pregnancy_update(...)       │
│   ├── Ovíparos → pending.new_eggs.append(Egg)                  │
│   └── Asexuales → pending.register_birth(...)                  │
└────┬───────────────────────────────┬────────────────────────────┘
     │                               │
     │ vivíparos                     │ ovíparos
     ▼                               ▼
┌────────────────────┐     ┌──────────────────────────────┐
│ GestationSystem    │     │         EggSystem            │
│                    │     │                              │
│ Procesa embarazos: │     │ Procesa huevos:              │
│ ├── Avanza días    │     │ ├── Recoge de pending        │
│ ├── Abortos        │     │ ├── Avanza incubación        │
│ ├── Parto premat.  │     │ ├── Mortalidad ambiental     │
│ └── Parto término  │     │ └── Eclosión                 │
│                    │     │                              │
│ Resultado:         │     │ Resultado:                   │
│ pending.register_  │     │ pending.register_            │
│ birth(...)         │     │ birth(...)                   │
└────────┬───────────┘     └─────────────┬────────────────┘
         │                               │
         └───────────────┬───────────────┘
                         │ ambos terminan en
                         ▼
         ┌───────────────────────────────────┐
         │  PendingChanges.register_birth() │
         │  (búfer transaccional)            │
         └───────────────┬───────────────────┘
                         │ consolidado por
                         ▼
         ┌───────────────────────────────────┐
         │ WorldState.apply_commit()         │
         │   Crea nuevo Person con genoma,   │
         │   asigna padres, coloca en mapa   │
         └───────────────────────────────────┘
```

---

## ⚙️ Configuración relevante

```python
# SimulationConfig.reproduction
config.reproduction.base_conception_chance = 0.02    # 2% base por tick
config.reproduction.min_fertility_age_days = 5475.0  # ~15 años
config.reproduction.max_fertility_age_days = 14600.0 # ~40 años
config.reproduction.pregnancy_duration_days = 270.0  # ~9 meses
config.reproduction.postpartum_cooldown_days = 90.0  # ~3 meses
config.reproduction.max_litter_size = 8
config.reproduction.miscarriage_risk = 0.00005       # Por día
config.reproduction.early_miscarriage_risk = 0.0001  # 1er trimestre
config.reproduction.maternal_mortality_risk = 0.001  # Durante parto
config.reproduction.premature_fetal_mortality_risk = 0.15

# Perfiles por especie
config.reproduction.species_profiles = {
    "human": {
        "gestation_days": 270.0,
        "litter_size_min": 1,
        "litter_size_max": 2,
        "can_gestate_female_only": True,
    },
    "wolf": {
        "gestation_days": 63.0,
        "litter_size_min": 4,
        "litter_size_max": 6,
    },
    "bird": {
        "gestation_days": 21.0,  # incubación
        "litter_size_min": 2,
        "litter_size_max": 5,
    },
}

# Mutación durante recombinación
config.mutation.probability = 0.05
config.mutation.magnitude_std = 0.1
config.mutation.mutate_dominance = True
```

---

## 🧪 Tests del sistema

| Archivo | Cobertura |
|---------|-----------|
| `tests/unit/test_reproductive_capabilities.py` | Derivación desde genoma, todos los tipos de organismos |
| `tests/integration/test_regression_bugs.py` | Bug #3: firma de register_birth |
| `tests/integration/test_statistical.py` | Producción de un mundo vivo |

---

## 📝 Ejemplos completos

### Ejemplo 1: Ciclo reproductivo humano completo

```python
# Configuración
engine = SimulationEngine.create_default(width=50, height=50, founding_population_size=20)

# Ejecutar 10 años
engine.run(max_ticks=3650)

# Consultar resultados
state = engine.state
population = state.get_all_persons()
print(f"Población final: {len(population)}")

# Contar nacimientos por generación
generations = {}
for person in population:
    generation = len(person.parents)
    generations[generation] = generations.get(generation, 0) + 1

for gen, count in sorted(generations.items()):
    print(f"Generación {gen}: {count} individuos")
```

### Ejemplo 2: Ecosistema multiespecie

```python
# Escenario con humanos, lobos y pájaros
scenario = {
    "name": "Ecosistema Bosque",
    "species": [
        {"id": "human", "count": 20},
        {"id": "wolf", "count": 8},
        {"id": "bird", "count": 30},
    ],
    "world": {"width": 100, "height": 100},
    "simulation": {"total_days": 3650},
}

# Guardar y ejecutar
with open("scenarios/bosque.json", "w") as f:
    json.dump(scenario, f)

scenario = ScenarioLoader.load("scenarios/bosque.json")
engine = SimulationEngine.create_from_scenario(scenario)
engine.run()
```

### Ejemplo 3: Monitorear huevos activos

```python
# Durante la simulación
for tick in range(100):
    engine.tick()
    
    # Consultar huevos activos
    egg_count = egg_system.get_egg_count(engine.state)
    if egg_count > 0:
        print(f"Tick {tick}: {egg_count} huevos incubándose")
        
        # Ver detalle de una madre específica
        mother_id = 42
        mother_eggs = egg_system.get_eggs_by_mother(engine.state, mother_id)
        for egg in mother_eggs:
            print(f"  Huevo {egg.egg_id}: {egg.progress:.1%} - {egg.days_until_hatch:.0f} días")
```

### Ejemplo 4: Reproducción asexual (bacterias)

```python
from entities.person.genome import Genome
from systems.reproduction.reproductive_capabilities import ReproductiveCapabilities

# Crear bacteria fundadora
bacteria_genome = Genome(species_id="bacteria")
bacteria_genome._genes["fertility"] = Gene(...)
bacteria_genome._genes["division_speed"] = Gene(...)

# Consultar capacidades
caps = ReproductiveCapabilities.from_genome(bacteria_genome)
print(caps.reproduction_type)  # "asexual"
print(caps.can_gestate)        # False
print(caps.litter_size_max)    # ~100 descendientes

# La bacteria se reproduce vía ConceptionSystem → _asexual_reproduction()
# que llama a pending.register_birth(...) directamente (sin embarazo ni huevo)
```

### Ejemplo 5: Simular complicaciones de embarazo

```python
# Crear una hembra humana con condiciones adversas
mother = Person(config=config, entity_id=1, x=50, y=50, gender='F', age=14000)  # ~38 años
mother.emotions["stress"] = 0.9  # Estrés extremo
mother.emotions["energy"] = 0.2  # Desnutrición
mother.infect(severe_pathogen)

# Embarazarla (forzado)
pending = PendingChanges()
pending.register_pregnancy_update(
    entity_id=1,
    is_pregnant=True,
    pregnancy_days=100.0,
    failed_increment=0,
    litter_size=1,
)

# Procesar gestación con condiciones adversas
gestation_system.process(state, pending, delta_days=1.0, context=context)

# Alta probabilidad de aborto espontáneo o parto prematuro
```

---

## 🚨 Consideraciones y limitaciones

### Principios fundamentales
- **Capacidades derivadas del genoma**: no hay hardcodeo por especie
- **Tres tipos de reproducción**: sexual, asexual, partenogénesis
- **Dos tipos de gestación**: vivípara (embarazo) y ovípara (huevos)
- **Coherencia transaccional**: todos los cambios pasan por PendingChanges

### Estrategias r/K

| Estrategia | Características | Ejemplos |
|-----------|-----------------|----------|
| **r-selection** | Muchas crías, poco cuidado, vida corta | Bacterias, insectos, peces |
| **K-selection** | Pocas crías, mucho cuidado, vida larga | Humanos, elefantes, ballenas |

El sistema deriva automáticamente la estrategia de la `longevity` y otros rasgos.

### Restricciones biológicas implementadas

| Restricción | Propósito |
|-------------|-----------|
| Verificación de sexo | Solo hembras gestan (salvo hermafroditas) |
| Prevención de doble embarazo | Una hembra no puede tener dos embarazos simultáneos |
| Fertilidad multiplicativa | Ambos padres deben ser fértiles |
| Infertilidad adquirida | Enfermedad/estrés/edad reducen fertilidad |
| Periodo posparto | 90 días de descanso tras el parto |
| Aborto espontáneo | Condiciones adversas interrumpen el embarazo |
| Parto prematuro | Estrés extremo después del 70% de gestación |
| Mortalidad materna | Riesgo real durante el parto |
| Mortalidad fetal | Crías pueden morir en parto prematuro |

### Rendimiento
- `ReproductiveCapabilities` se crea bajo demanda (no se cachea)
- Los sistemas iteran sobre `state.get_all_persons()` una vez por tick
- `EggSystem` mantiene `state.active_eggs` como lista

### Limitaciones
- No hay selección de pareja activa durante concepción (usa `partner_id` existente)
- No hay cuidado parental activo (solo se registra la capacidad)
- Los huevos no se mueven ni son defendidos activamente
- No hay lactancia explícita (implícita en el periodo posparto)

### Errores comunes
- ❌ Asumir que `register_birth` acepta `species` (se deriva del genoma)
- ❌ Crear embarazos para ovíparos (usan huevos)
- ❌ Procesar gestación en organismos sin `can_gestate`
- ❌ Olvidar el `failed_increment` al registrar abortos
- ❌ Modificar `person.is_pregnant` directamente (usar `PendingChanges`)

---

## 🎓 Conceptos clave

### ¿Por qué capacidades derivadas y no por especie?

**Principio de abstracción**:
- El genoma es la fuente de verdad
- Las capacidades son una vista derivada
- Esto permite que especies con rasgos similares tengan reproducción similar
- Y que nuevas especies funcionen sin añadir casos especiales

### ¿Por qué tres tipos de reproducción?

**Principio de completitud biológica**:
- **Sexual**: mamíferos, aves (requiere apareamiento)
- **Asexual**: bacterias, plantas (clonación con mutación)
- **Partenogénesis**: algunos reptiles, insectos (hembra sin macho)

Cada uno usa un mecanismo diferente en `ConceptionSystem`.

### ¿Por qué vivíparos vs ovíparos?

**Principio de realismo ecológico**:
- **Vivíparos**: invierten mucho en pocas crías, protección interna
- **Ovíparos**: invierten poco en muchas crías, vulnerabilidad ambiental

Esto genera estrategias reproductivas muy diferentes y presiones selectivas distintas.

### ¿Por qué complicaciones biológicas?

**Principio de presión selectiva**:
- Los embarazos no son seguros: pueden fallar
- El parto es riesgoso: puede morir la madre
- Esto crea trade-offs evolutivos reales
- Y hace que las decisiones reproductivas tengan consecuencias

### ¿Por qué PendingChanges para todo?

**Principio de coherencia temporal**:
- Si la concepción ocurre en fase 6, el nacimiento no se aplica hasta el commit
- Esto evita que agentes "nacidos a mitad de tick" participen en fases posteriores
- Y permite que mortalidad y reproducción coexistan sin inconsistencias

---

## 📊 Métricas del sistema

| Métrica | Valor |
|---------|-------|
| Archivos del sistema | 5 |
| Clases principales | 5 |
| Estados del huevo | 5 |
| Tipos de reproducción | 3 |
| Tipos de gestación | 3 |
| Rasgos consultados | 7 |
| Tests cubriendo reproducción | ~20 |

---

## 🔮 Futuras extensiones

### Planificadas
- [ ] Selección activa de pareja durante celo
- [ ] Cuidado parental activo (alimentación, protección)
- [ ] Lactancia explícita para mamíferos
- [ ] Territorialidad reproductiva (nidos defendidos)

### Posibles
- [ ] Menstruación/celo cíclico
- [ ] Infanticidio y competencia reproductiva
- [ ] Crianza cooperativa (ayudantes)
- [ ] Poliginia, poliandria, monogamia flexible
- [ ] Hermafroditismo secuencial
- [ ] Cambio de sexo ambiental

---

*Documento: 05_REPRODUCCION.md*
*Versión: 1.0*