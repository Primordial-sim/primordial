# MAPA DE DEPENDENCIAS DE SISTEMAS

**Versión:** 1.0
**Última actualización:** Agosto 2026
**Propósito:** Documentar qué sistemas consumen el núcleo genético y cuáles asumen humanos implícitamente.

---

## 1. RESUMEN EJECUTIVO

| Clasificación | Sistemas | Estado |
|---|---|---|
| 🟢 Agnósticos a especie | 2 | Funcionan con cualquier especie |
| 🟡 Usan propiedades legacy | 8 | Funcionan, necesitan migración gradual |
| 🔴 Hardcodeados para humanos | 7 | Requieren refactorización profunda |

**Total de sistemas analizados:** 17

---

## 2. CLASIFICACIÓN DETALLADA

### 🟢 AGNÓSTICOS A ESPECIE (2 sistemas)

Estos sistemas ya funcionan correctamente con cualquier especie. No requieren cambios.

| Sistema | Notas |
|---|---|
| `systems/evolution/evolution_engine.py` | Usa genome (37 veces) pero de forma genérica |
| `systems/metrics/metrics_system.py` | Recolecta métricas sin asumir especie |

---

### 🟡 USAN PROPIEDADES LEGACY (8 sistemas)

Estos sistemas funcionan pero usan propiedades del Genome que pertenecen a la API retrocompatible (`.longevity`, `.fertility`, etc.). Deben migrarse gradualmente a `get_trait_value("X")`.

| Sistema | Propiedades usadas | Conceptos humanos |
|---|---|---|
| `systems/aging/aging_system.py` | `.longevity` (2) | pregnancy (4) |
| `systems/behavior/cognitive_memory_system.py` | `.temperament` (2) | marriage (1) |
| `systems/diseases/disease_system.py` | `.immunity` (1) | — |
| `systems/free_will/free_will_system.py` | 6 propiedades | marriage (1) |
| `systems/genealogy/genealogy_system.py` | `.longevity`, `.sociability`, `.temperament` | marriage (1) |
| `systems/mortality/mortality_system.py` | `.longevity` (2) | — |
| `systems/movement/movement_system.py` | `.curiosity` (1) | — |
| `systems/temporal/temporal_system.py` | `.temperament`, `.immunity` | — |

**Propiedades legacy detectadas:**
- `.longevity` - Longevidad
- `.sociability` - Sociabilidad
- `.temperament` - Temperamento
- `.fertility` - Fertilidad
- `.immunity` - Inmunidad
- `.impulsivity` - Impulsividad
- `.curiosity` - Curiosidad
- `.obedience` - Obediencia
- `.aggressiveness` - Agresividad

**Acción recomendada:** Migrar gradualmente a `genome.get_trait_value("X")` para ser agnósticos a especie.

---

### 🔴 HARDCODEADOS PARA HUMANOS (7 sistemas)

Estos sistemas asumen implícitamente que todos los organismos son humanos. Requieren refactorización profunda para ser agnósticos a especie.

| Sistema | Props legacy | Conceptos humanos | Gravedad |
|---|---|---|---|
| `systems/reproduction/conception_system.py` | `.longevity`, `.fertility` | pregnancy (8), gestation (3), human (1) | 🔴 CRÍTICO |
| `systems/reproduction/gestation_system.py` | `.combine()` | pregnancy (19), gestation (13), human (1) | 🔴 CRÍTICO |
| `systems/mortality/death_resolver.py` | — | marriage (2), pregnancy (4) | 🔴 ALTO |
| `systems/free_will/free_will_system.py` | 6 props | marriage (1) | 🟡 MEDIO |
| `systems/social/social_pressure.py` | — | marriage (4) | 🟡 MEDIO |
| `systems/relationships/relationship_experience_engine.py` | — | marriage (1) | 🟡 MEDIO |
| `systems/social/residential_nucleus.py` | — | marriage (1) | 🟢 BAJO |

---

## 3. ANÁLISIS POR MÓDULO

### 3.1 Reproducción (CRÍTICO)

**Archivos:**
- `systems/reproduction/conception_system.py`
- `systems/reproduction/gestation_system.py`

**Problema:** Estos sistemas están completamente hardcodeados para humanos:
- Asumen embarazo (pregnancy) como único mecanismo de concepción
- Asumen gestación (gestation) como único proceso de desarrollo prenatal
- Referencian "human" directamente

**Impacto:**
- ❌ No funciona para bacterias (reproducción asexual)
- ❌ No funciona para plantas (autofecundación, polinización)
- ❌ No funciona para insectos (metamorfosis)
- ❌ No funciona para especies con reproducción múltiple (huevos)

**Refactorización necesaria:**
1. Separar "reproducción sexual" de "reproducción asexual"
2. Consultar `species_profiles` de ReproductionConfig
3. Usar `genome.combine()` para sexual
4. Usar `genome.replicate()` para asexual
5. Implementar gestación variable por especie (no solo 270 días humanos)

**Nota:** El método `genome.combine()` ya es genérico y usa MutationConfig. Solo los sistemas de reproducción necesitan adaptarse.

---

### 3.2 Mortalidad

**Archivos:**
- `systems/mortality/mortality_system.py`
- `systems/mortality/death_resolver.py`

**Problema:**
- `mortality_system.py` usa `.longevity` (propiedad legacy) → necesita migración
- `death_resolver.py` asume `marriage` y `pregnancy` (conceptos humanos)

**Refactorización necesaria:**
1. Migrar `.longevity` a `get_trait_value("longevity")`
2. Hacer que `death_resolver` consulte rasgos genéricos en vez de estados humanos
3. Considerar que la muerte puede tener causas diferentes según la especie

---

### 3.3 Envejecimiento

**Archivo:** `systems/aging/aging_system.py`

**Problema:**
- Usa `.longevity` (propiedad legacy)
- Asume `pregnancy` como causa de desgaste (solo aplica a mamíferos)

**Refactorización necesaria:**
1. Migrar `.longevity` a `get_trait_value("longevity")`
2. Consultar si la especie tiene embarazo antes de aplicar desgaste
3. Considerar que algunas especies no envejecen igual (bacterias, plantas)

---

### 3.4 Enfermedades

**Archivo:** `systems/diseases/disease_system.py`

**Problema:**
- Usa `.immunity` (propiedad legacy)

**Refactorización necesaria:**
1. Migrar `.immunity` a `get_trait_value("immunity")`
2. Considerar que algunas especies tienen inmunidad muy diferente (bacterias no tienen sistema inmune)

---

### 3.5 Movimiento

**Archivo:** `systems/movement/movement_system.py`

**Problema:**
- Usa `.curiosity` (propiedad legacy)
- NO consulta rasgos de movimiento específicos (flight, swimming, burrowing)

**Refactorización necesaria:**
1. Migrar `.curiosity` a `get_trait_value("curiosity")`
2. Consultar `get_trait_value("flight")` para saber si puede volar
3. Consultar `get_trait_value("swimming")` para saber si puede nadar
4. Consultar `get_trait_value("burrowing")` para saber si puede excavar
5. Modificar la lógica de movimiento según capacidades de la especie

**Impacto:** Este es uno de los sistemas más importantes de migrar, porque el movimiento debería variar enormemente según la especie (un ave vuela, un pez nada, una planta no se mueve).

---

### 3.6 Libre Albedrío (Free Will)

**Archivo:** `systems/free_will/free_will_system.py`

**Problema:**
- Usa 6 propiedades legacy: `.sociability`, `.temperament`, `.impulsivity`, `.curiosity`, `.obedience`, `.aggressiveness`
- Asume `marriage` (concepto humano)

**Refactorización necesaria:**
1. Migrar las 6 propiedades a `get_trait_value("X")`
2. Consultar si la especie tiene matrimonio antes de aplicar acciones
3. Considerar que algunas especies no tienen motivaciones humanas (bacterias, plantas)

---

### 3.7 Relaciones Sociales

**Archivos:**
- `systems/relationships/relationship_experience_engine.py`
- `systems/relationships/relationship_manager.py`
- `systems/social/social_pressure.py`
- `systems/social/residential_nucleus.py`

**Problema:**
- Asumen `marriage` como única relación formal
- No consultan si la especie tiene capacidad de relaciones sociales

**Refactorización necesaria:**
1. Consultar `get_trait_value("sociability")` para saber si la especie puede tener relaciones
2. Consultar `get_trait_value("cooperation")` para saber si coopera
3. Hacer que el matrimonio sea opcional según la especie
4. Considerar que algunas especies son solitarias

---

### 3.8 Genealogía

**Archivo:** `systems/genealogy/genealogy_system.py`

**Problema:**
- Usa `.longevity`, `.sociability`, `.temperament` (propiedades legacy)
- Asume `marriage`

**Refactorización necesaria:**
1. Migrar propiedades a `get_trait_value("X")`
2. Considerar que algunas especies no tienen matrimonio
3. Considerar que la genealogía es diferente para reproducción asexual (bacterias)

---

### 3.9 Temporal

**Archivo:** `systems/temporal/temporal_system.py`

**Problema:**
- Usa `.temperament` y `.immunity` (propiedades legacy)

**Refactorización necesaria:**
1. Migrar a `get_trait_value("X")`

---

### 3.10 Memoria Cognitiva

**Archivo:** `systems/behavior/cognitive_memory_system.py`

**Problema:**
- Usa `.temperament` (propiedad legacy)
- Asume `marriage`

**Refactorización necesaria:**
1. Migrar a `get_trait_value("temperament")`
2. Considerar que algunas especies no tienen memoria compleja

---

## 4. RASGOS GENÉTICOS USADOS POR CADA SISTEMA

Resumen de qué rasgos consulta cada sistema (detectado en el análisis):

| Rasgo | Sistemas que lo usan |
|---|---|
| `longevity` | aging, genealogy, mortality, conception |
| `sociability` | free_will, genealogy |
| `temperament` | cognitive_memory, free_will, genealogy, temporal |
| `fertility` | conception |
| `immunity` | diseases, temporal |
| `impulsivity` | free_will |
| `curiosity` | free_will, movement |
| `obedience` | free_will |
| `aggressiveness` | free_will |

**Rasgos NO usados actualmente (deberían usarse):**
- `flight` - Debería usarlo MovementSystem
- `swimming` - Debería usarlo MovementSystem
- `burrowing` - Debería usarlo MovementSystem
- `climbing` - Debería usarlo MovementSystem
- `division_speed` - Debería usarlo ReproductionSystem para bacterias
- `photosynthesis` - Debería usarlo un sistema de energía
- `metabolism` - Debería usarlo un sistema de energía
- `nervous_system` - Debería usarlo CognitionSystem

---

## 5. PLAN DE MIGRACIÓN RECOMENDADO

### Fase 1: Migración de propiedades legacy (2-3 sesiones)

**Objetivo:** Reemplazar todas las propiedades legacy por `get_trait_value("X")`.

**Orden sugerido:**
1. `systems/diseases/disease_system.py` - Solo 1 propiedad, fácil
2. `systems/movement/movement_system.py` - Solo 1 propiedad + añadir rasgos de movimiento
3. `systems/temporal/temporal_system.py` - Solo 2 propiedades
4. `systems/mortality/mortality_system.py` - Solo 1 propiedad
5. `systems/behavior/cognitive_memory_system.py` - Solo 1 propiedad
6. `systems/genealogy/genealogy_system.py` - 3 propiedades
7. `systems/free_will/free_will_system.py` - 6 propiedades (el más grande)
8. `systems/aging/aging_system.py` - 1 propiedad + embarazo

### Fase 2: Refactorización de reproducción (2-3 sesiones)

**Objetivo:** Hacer que la reproducción funcione con cualquier especie.

**Pasos:**
1. Separar reproducción sexual de asexual
2. Consultar `species_profiles` de ReproductionConfig
3. Usar `genome.combine()` para sexual
4. Usar `genome.replicate()` para asexual
5. Implementar gestación variable por especie

### Fase 3: Movimiento por rasgos (1-2 sesiones)

**Objetivo:** Hacer que el movimiento consulte rasgos específicos.

**Pasos:**
1. Consultar `flight`, `swimming`, `burrowing`, `climbing`
2. Modificar lógica de movimiento según capacidades
3. Las plantas no se mueven (mobility = 0)

### Fase 4: Conceptos humanos opcionales (1-2 sesiones)

**Objetivo:** Hacer que marriage, pregnancy, etc. sean opcionales según especie.

**Pasos:**
1. Consultar si la especie tiene capacidad de matrimonio
2. Consultar si la especie tiene embarazo
3. Adaptar sistemas sociales

---

## 6. CONCEPTOS HUMANOS DETECTADOS

Conceptos que están hardcodeados y necesitan hacerse opcionales:

| Concepto | Apariciones | Sistemas afectados |
|---|---|---|
| `marriage` | 15 | free_will, genealogy, death_resolver, social_pressure, residential_nucleus, relationships |
| `pregnancy` | 39 | aging, death_resolver, conception, gestation |
| `gestation` | 16 | conception, gestation |
| `human` | 2 | conception, gestation |

---

## 7. CONCLUSIÓN

El núcleo genético está **completamente agnóstico a especie**, pero los sistemas que lo consumen aún asumen humanos implícitamente. Los cambios más críticos están en:

1. **Reproducción** (CRÍTICO) - No funciona para bacterias, plantas, insectos
2. **Movimiento** (ALTO) - No consulta flight, swimming, etc.
3. **Sistemas sociales** (MEDIO) - Asumen matrimonio humano

La migración debe ser gradual, empezando por los sistemas más simples y terminando con reproducción (el más complejo).

---

**FIN DEL DOCUMENTO**