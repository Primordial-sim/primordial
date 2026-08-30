# ESPECIFICACIÓN DEL NÚCLEO GENÉTICO

**Versión:** 2.0 (Final)
**Estado:** Documento conceptual atemporal
**Nota:** Este documento describe CÓMO funciona el sistema desde el punto de
vista conceptual. No habla de implementación, tests, ni archivos específicos.
Para el estado actual de la implementación, ver GENETICS_IMPLEMENTATION.md

**ESTADO: CERRADO Y CONGELADO**
 
Este documento es el contrato del núcleo genético.
A partir de este momento, no se modificará salvo que se descubra
un error conceptual. Todo lo demás debe construirse encima del núcleo,
nunca dentro de él.
 
Fecha de cierre: Agosto 2026

## 1. CONCEPTOS FUNDAMENTALES

### 1.1 Trait (Rasgo)

Un rasgo es una definición atómica de una característica hereditaria.

**Un Trait define:**
- QUÉ es la característica (identificador, nombre, categoría)
- El RANGO de valores posibles (min_value, max_value)
- El MODELO DE EXPRESIÓN (cómo se combinan los dos alelos)
- La DISTRIBUCIÓN INICIAL (cómo se generan los valores fundadores)
- El PESO EVOLUTIVO (cuánto influye en la selección natural)
- La HEREDABILIDAD (factor informativo, ver sección 1.2)

**Un Trait NO:**
- Conoce especies
- Conoce biología
- Conoce incompatibilidades (eso va en el Validador)
- Conoce requisitos (eso va en el Validador)
- Conoce capacidades funcionales
- Conoce el entorno

### 1.2 Heredabilidad (heritability)

La heredabilidad es un atributo del Trait que indica el grado en que la
variación fenotípica de un rasgo puede proceder de la información heredada
frente a factores no genéticos.

**Definición operativa:**

heritability: Factor que determina cuánto de la variación fenotípica
de un rasgo procede de la información heredada frente
a factores no genéticos.

La semántica operacional exacta (cómo se usa en cálculos)
se definirá cuando se diseñe el sistema de fenotipo.

**Notas importantes:**
- Es un atributo INFORMATIVO (se almacena, no se usa en cálculos del núcleo)
- En biología real, la heredabilidad es una propiedad estadística poblacional,
  no individual
- NO se implementa ninguna fórmula de combinación genética/ambiente en el
  núcleo genético
- El valor se conserva para uso futuro por otros sistemas

**Valores típicos:**

| Valor | Significado conceptual |
|---|---|
| 1.0 | Variación completamente heredable |
| 0.7-0.9 | Variación mayormente heredable |
| 0.4-0.6 | Variación mixta |
| 0.1-0.3 | Variación mayormente no genética |
| 0.0 | Variación completamente no genética |

### 1.3 Allele (Alelo)

Un alelo es una variante específica de un gen.

**Un Allele contiene:**
- value: El valor numérico que aporta al rasgo
- dominance: La fuerza con la que se expresa frente a otros alelos (0.0 a 1.0)

**Un Allele es:**
- Inmutable tras su creación
- Portador de información, no tomador de decisiones

### 1.4 Gene (Gen)

Un gen es un locus genético compuesto por un par de alelos (diploidía).

**Un Gene contiene:**
- allele_a: Alelo heredado del progenitor 1
- allele_b: Alelo heredado del progenitor 2

**Un Gene puede:**
- express(expression_model): Calcular el valor resultante de combinar sus dos
  alelos usando el modelo de expresión proporcionado

**Nota importante:** El Gene NO decide qué modelo de expresión usar. El modelo
de expresión pertenece al Trait. El Gene simplemente aplica el modelo que se le
proporciona.

### 1.5 Genome (Genoma)

Un genoma es el conjunto completo de genes de un individuo.

**Un Genome:**
- Almacena genes para los rasgos activos de su especie
- Tiene un species_id como identificador (sin conocer el significado biológico)
- NO decide nada (es un almacén pasivo)
- ES inmutable durante la vida del individuo
- Las mutaciones genéticas se producen durante la generación de descendencia,
  no como modificación del Genome existente
- PUEDE ser consultado para obtener potencial genético

**Un Genome puede:**
- get_genetic_potential(trait_id): Retornar el potencial genético de un rasgo
- has_trait(trait_id): Verificar si un rasgo existe en el genoma
- get_all_trait_ids(): Listar todos los rasgos presentes
- combine(other_genome, mutation_config): Reproducción sexual
- replicate(mutation_config): Reproducción asexual

**Un Genome NO puede:**
- Decidir si un organismo puede hacer algo (eso es capacidad funcional)
- Conocer el entorno (eso es de otros sistemas)
- Modificarse a sí mismo durante la vida
- Conocer el significado biológico de sus genes

### 1.6 Genotipo

El genotipo es la información genética completa de un individuo.

**En nuestro sistema:**
- Genotipo = el objeto Genome completo
- Es inmutable durante la vida del individuo
- Representa el POTENCIAL, no el resultado
- Las mutaciones ocurren durante la generación de descendencia

### 1.7 Valor Genético Expresado / Potencial Genético

El potencial genético es el valor resultante de combinar los dos alelos de un
rasgo mediante el modelo de expresión definido por el Trait.

Representa aquello que el genotipo puede aportar al organismo antes de
considerar factores externos al núcleo genético.

**Cálculo:**

Genotipo
    ↓
Gene (dos alelos)
    ↓
Modelo de expresión del Trait
    ↓
Valor genético expresado (= Potencial genético)

**El potencial genético:**
- Es un valor numérico dentro del rango del rasgo
- Se calcula usando el modelo de expresión del rasgo
- NO es el valor final que usa el sistema (eso será el fenotipo, calculado
  por otros sistemas)
- Es 0.0 si el rasgo no existe en el genoma

**El potencial genético NO:**
- Es la velocidad real del organismo
- Es la capacidad de volar
- Es la fertilidad efectiva
- Considera el entorno, la edad, el estado, etc.

**Flujo conceptual completo:**

Genome
   ↓
Potencial genético
   ↓
[ fisiología / desarrollo / entorno / estado ]
   ↓
Fenotipo
   ↓
Capacidad funcional
   ↓
Sistemas de simulación

Nota: Los pasos después de "Potencial genético" NO pertenecen al núcleo genético.

---

## 2. EXPRESIÓN GENÉTICA

### 2.1 Modelo de Expresión

Cada rasgo define cómo se combinan sus dos alelos para producir el potencial
genético.

**El modelo de expresión pertenece al Trait.** El Gene simplemente aplica el
modelo que se le proporciona.

**Modelos disponibles:**

| Modelo | Comportamiento | Parámetros usados |
|---|---|---|
| DOMINANT | Gana el alelo con mayor dominancia | value, dominance |
| RECESSIVE | Gana el alelo con menor dominancia | value, dominance |
| CODOMINANT | Promedio simple de ambos alelos | value |
| WEIGHTED_AVERAGE | Promedio ponderado por dominancia | value, dominance |
| ADDITIVE | Suma de ambos alelos | value |
| MAX_VALUE | El valor máximo de ambos alelos | value |
| MIN_VALUE | El valor mínimo de ambos alelos | value |

### 2.2 Cálculo del Potencial Genético

El potencial genético se calcula así:

1. Buscar el Gene del rasgo en el Genome
2. Si no existe, retornar 0.0
3. Obtener el modelo de expresión del Trait
4. Aplicar el modelo al Gene (gene.express(model))
5. Clampear al rango del Trait

### 2.3 Consulta de Rasgos Ausentes

**Cuando se consulta un rasgo que no existe en el genoma:**

genome.has_trait("flight")              # Retorna False
genome.get_genetic_potential("flight")  # Retorna 0.0

**Distinción importante:**

| Situación | has_trait() | get_genetic_potential() |
|---|---|---|
| Rasgo no existe | False | 0.0 |
| Rasgo existe con valor 0 | True | 0.0 |
| Rasgo existe con valor > 0 | True | valor > 0.0 |

Los sistemas pueden usar has_trait() para distinguir entre "rasgo ausente" y
"rasgo presente con valor 0".

### 2.4 Rango y Clampeonato

**Regla:** El potencial genético SIEMPRE está dentro del rango
[min_value, max_value] del rasgo.

**Comportamiento en casos extremos:**

| Situación | Acción |
|---|---|
| Expresión produce valor > max_value | Clampear a max_value |
| Expresión produce valor < min_value | Clampear a min_value |
| ADDITIVE suma > max_value | Clampear a max_value |
| Mutación produce valor fuera de rango | Clampear al rango |
| Herencia produce valor fuera de rango | Clampear al rango |

---

## 3. REPRODUCCIÓN

### 3.1 Reproducción Sexual

La reproducción sexual combina el material genético de dos progenitores.

**Proceso:**
1. Para cada rasgo presente en ambos progenitores:
   - Meiosis: cada progenitor aporta un alelo aleatorio
   - Mutación: cada alelo puede mutar (ver sección 4)
   - Crear nuevo Gene con los dos alelos
2. Para cada rasgo presente solo en un progenitor:
   - El alelo del progenitor presente se hereda
   - El otro alelo se genera con valor por defecto
3. Retornar nuevo Genome

**Notas:**
- El Genome NO decide si dos organismos pueden reproducirse
- El Genome solo combina información cuando se le pide
- La decisión de compatibilidad es responsabilidad del ReproductionSystem

### 3.2 Reproducción Asexual

La reproducción asexual crea un clon con mutación.

**Proceso:**
1. Copiar todos los genes del progenitor
2. Para cada alelo:
   - Mutación: puede mutar (ver sección 4)
3. Retornar nuevo Genome (sin mezcla con otro progenitor)

**Notas:**
- No hay meiosis (no hay segregación de alelos)
- No hay recombinación (el hijo es genéticamente idéntico salvo mutaciones)
- Aplicable a bacterias, plantas con reproducción asexual, organismos
  unicelulares, etc.

**Diferencia clave con reproducción sexual:**

REPRODUCCIÓN SEXUAL:
Genome A ──┐
           ├── combine() ──→ Genome hijo
Genome B ──┘

REPRODUCCIÓN ASEXUAL:
Genome A ──→ replicate() ──→ Genome hijo
                            + mutación

### 3.3 Responsabilidad de la Decisión de Reproducción

**El Genome NO decide:**
- Si dos organismos pueden reproducirse
- Qué tipo de reproducción usan
- Si hay compatibilidad de especies
- Si hay condiciones especiales (autofecundación, etc.)

**El ReproductionSystem (externo) decide:**
- Si dos organismos son compatibles
- Si usan reproducción sexual o asexual
- Las condiciones y restricciones de la reproducción

---

## 4. MUTACIÓN

### 4.1 Definición

La mutación es un cambio aleatorio en el valor de un alelo durante la
reproducción.

**La mutación:**
- Ocurre durante la creación de un nuevo genoma (hijo)
- Afecta al valor del alelo (y opcionalmente a la dominancia)
- Es pequeña y gradual (no saltos enormes)
- NO modifica el genotipo de un individuo vivo
- NO ocurre fuera de la reproducción

### 4.2 Configuración de Mutación

La configuración de mutación es GLOBAL para la simulación, no por rasgo.

**Parámetros:**
- probability: Probabilidad de que un alelo mute
- magnitude_std: Desviación estándar del cambio
- mutate_dominance: Si la dominancia también muta
- dominance_std: Desviación estándar de mutación de dominancia

**Donde vive:**
- En la configuración de simulación (configuración global)
- O en la definición de especie (configuración por especie, si se desea)

**No vive en:**
- Trait (los rasgos no deberían saber de tasas de mutación)
- Genome (el genoma no decide si muta)

**Razón:** Si un escenario necesita mutaciones más frecuentes, no se deberían
modificar los Traits. Se cambia una configuración global.

### 4.3 Proceso de Mutación

Para cada alelo durante la reproducción:

1. ¿Ocurre mutación? (random < probability)
2. Si sí:
   - Mutar el valor (gaussiano con magnitude_std)
   - Clampear al rango del trait
   - Opcionalmente mutar la dominancia
3. Si no: el alelo se mantiene igual

### 4.4 Diferencia entre probabilidad y magnitud

**Es crucial distinguir:**

| Parámetro | Significado |
|---|---|
| probability | ¿OCURRE una mutación? (0.05 = 5% de alelos mutan) |
| magnitude_std | ¿CUÁNTO cambia el alelo si muta? (desviación estándar) |

**Ejemplo de configuraciones:**

# Mutación rara pero fuerte
MutationConfig(probability=0.01, magnitude_std=0.3)

# Mutación frecuente pero suave
MutationConfig(probability=0.10, magnitude_std=0.05)

# Mutación equilibrada
MutationConfig(probability=0.05, magnitude_std=0.1)

---

## 5. RANGOS

### 5.1 Definición de Rango

Cada rasgo tiene un rango [min_value, max_value] que define los valores posibles.

**El rango:**
- Es una propiedad del Trait
- Puede ser sobrescrito por la definición de especie
- Es el MISMO para todos los individuos de la especie

### 5.2 Comportamiento con Rangos

**Regla general:** Cualquier operación que produzca un valor fuera de rango
debe clampearlo.

**Puntos de aplicación:**
- Creación de alelos fundadores
- Mutación
- Expresión genética
- Herencia

---

## 6. LÍMITES DEL NÚCLEO GENÉTICO

### 6.1 Lo que pertenece al núcleo

✓ Trait (definición de rasgos)
✓ TraitLibrary (biblioteca de rasgos)
✓ SpeciesDefinition (plantillas y especies)
✓ SpeciesRegistry (registro de especies)
✓ Genome (genotipo de un individuo)
✓ Gene (par de alelos)
✓ Allele (variante de un gen)
✓ ExpressionModel (cómo se combinan alelos)
✓ MutationConfig (configuración de mutación)
✓ BiologicalValidator (reglas de coherencia)
✓ RealismIndex (índice de realismo)
✓ Herencia mendeliana (combine, meiosis)
✓ Reproducción asexual (replicate)
✓ Mutación (durante reproducción)
✓ Rangos y clampeonato

### 6.2 Lo que NO pertenece al núcleo

✗ Fenotipo (valor final que usa el sistema)
✗ Capacidades funcionales (¿puede volar?)
✗ Entorno (temperatura, humedad, terreno)
✗ Fisiología (metabolismo, energía, edad)
✗ Comportamiento (movimiento, decisiones)
✗ Ecología (depredación, competencia)
✗ Selección natural (eso es del EvolutionSystem)
✗ Expresión condicionada (por edad, sexo, ambiente)
✗ Epigenética (modificaciones no genéticas)
✗ Rasgos poligénicos (un rasgo, múltiples genes)

### 6.3 Regla de oro

**El Genome proporciona POTENCIAL GENÉTICO.**
**Otros sistemas lo convierten en COMPORTAMIENTO REAL.**

---

## 7. ARQUITECTURA CONCEPTUAL

### 7.1 Estructura del núcleo

                    TRAIT
              ┌────────────────┐
              │ Qué rasgo es   │
              │ Rango          │
              │ Expresión      │
              │ Heredabilidad  │
              │ Evolución      │
              └───────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │      GENE       │
             │                 │
             │  Allele A       │
             │  Allele B       │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │     GENOME      │
             │                 │
             │  Genes          │
             │  species_id     │
             └────────┬────────┘
                      │
                      ▼
             POTENCIAL GENÉTICO
                      │
                      │
              ┌───────┴────────┐
              │                │
              ▼                ▼
         COMBINE()        REPLICATE()
              │                │
              ▼                ▼
          descendencia      descendencia
              │                │
              └────── MUTACIÓN ┘

### 7.2 Flujo hacia otros sistemas

POTENCIAL GENÉTICO
        ↓
   BIOLOGÍA DEL
   ORGANISMO
        ↓
     FENOTIPO
        ↓
 CAPACIDADES / ESTADO
        ↓
 SISTEMAS DE SIMULACIÓN

**Nota:** Todo lo que está después de "POTENCIAL GENÉTICO" NO pertenece al
núcleo genético.

---

**FIN DE LA ESPECIFICACIÓN**