# 03 - Genética Universal

## 📋 Resumen

El sistema de **Genética Universal** es el motor biológico fundamental del Simulador de Vida. Define cómo los organismos heredan, expresan y transmiten sus características a través de generaciones, implementando herencia mendeliana pura con múltiples modelos de expresión genética.

**Filosofía fundamental**: *Los rasgos son completamente neutros. La biología vive en las plantillas y el validador.*

---

## 🎯 Responsabilidad

**Es responsable de:**
- Definir rasgos hereditarios individuales (`Trait`)
- Gestionar el catálogo global de rasgos (`TraitLibrary`)
- Almacenar y expresar la información genética del individuo (`Genome`)
- Implementar herencia mendeliana con múltiples modelos (`Allele`, `Gene`)
- Validar la coherencia biológica de las especies (`BiologicalValidator`)
- Calcular índices de realismo (`RealismIndex`)
- Definir especies mediante plantillas con herencia (`SpeciesDefinition`)
- Registrar y gestionar todas las especies disponibles (`SpeciesRegistry`)

**NO es responsable de:**
- ❌ Decidir el comportamiento de los agentes (lo hacen las capacidades derivadas)
- ❌ Almacenar el estado del mundo (lo hace `WorldState`)
- ❌ Determinar compatibilidad de hábitat (lo hace `HabitatCompatibility`)

---

## 🌍 Equivalencia con la vida real

| Concepto del sistema | Equivalencia en la vida real | Unidad |
|---------------------|-----------------------------|--------|
| **Trait** | Característica heredable | Gen abstracto |
| **Allele** | Variante de un gen | Alelo |
| **Gene** | Par de alelos (diploidía) | Locus genético |
| **Genome** | ADN completo del individuo | Genoma |
| **ExpressionModel** | Mecanismo de expresión | Dominancia/epistasis |
| **SpeciesDefinition** | Blueprint de especie | ADN de referencia |
| **TraitLibrary** | Catálogo universal | Banco de genes |
| **BiologicalValidator** | Biólogo experto | Revisión por pares |
| **RealismIndex** | Índice de plausibilidad | Score científico |

---

## 📁 Archivos que lo componen

| Archivo | Clase principal | Responsabilidad |
|---------|-----------------|-----------------|
| `core/genetics/trait.py` | `Trait`, `TraitCategory`, `ExpressionModel`, `Distribution` | Definición de rasgos |
| `core/genetics/trait_library.py` | `TraitLibrary` | Catálogo global de rasgos |
| `entities/person/allele.py` | `Allele`, `Gene` | Unidades hereditarias |
| `entities/person/genome.py` | `Genome` | Genoma del individuo |
| `core/genetics/species_definition.py` | `SpeciesDefinition`, `SpeciesRegistry`, `TraitConfig` | Definición de especies |
| `core/genetics/biological_validator.py` | `BiologicalValidator`, `ValidationResult` | Validación biológica |
| `core/genetics/realism_index.py` | `RealismIndex` | Índice de realismo |

---

## 🔄 Flujo de ejecución

```
┌─────────────────────────────────────────────────────────────────┐
│              FLUJO GENÉTICO COMPLETO                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. DEFINICIÓN DE RASGOS (TraitLibrary)                          │
│    ├── Registrar rasgos neutros (id, rango, modelo, etc.)       │
│    ├── Organizar por categorías (BIOLOGY, BEHAVIOR, etc.)       │
│    └── Definir distribución inicial para poblaciones            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. DEFINICIÓN DE ESPECIES (SpeciesDefinition)                   │
│    ├── Crear plantilla base (animal, plant, etc.)               │
│    ├── Activar rasgos específicos (herencia de plantillas)      │
│    ├── Configurar valores por defecto y rangos                  │
│    ├── Definir preferencias de hábitat                          │
│    └── Registrar en SpeciesRegistry                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. VALIDACIÓN BIOLÓGICA (BiologicalValidator)                   │
│    ├── Verificar incompatibilidades                             │
│    ├── Verificar dependencias                                   │
│    ├── Verificar coherencia de categorías                       │
│    └── Calcular score de coherencia                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. CREACIÓN DE GENOMAS FUNDADORES                               │
│    ├── Genome.create_founder(species, library)                  │
│    ├── Generar pares de alelos con diversidad inicial           │
│    └── Asignar inmunidad específica por familia                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. EXPRESIÓN FENOTÍPICA (durante la simulación)                 │
│    ├── genome.get_trait_value("fertility")                      │
│    ├── Consulta modelo de expresión en TraitLibrary             │
│    └── Calcula valor fenotípico (ej: WEIGHTED_AVERAGE)          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. REPRODUCCIÓN (cada concepción)                               │
│    ├── parent1_genome.combine(parent2_genome, mutation_config)  │
│    ├── Meiosis: segregar alelos al azar                         │
│    ├── Mutación: aplicar cambios gaussianos                     │
│    ├── Clampear al rango del trait                              │
│    └── Crear genoma del descendiente                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes del Sistema

---

### 1. Trait - Definición de un Rasgo

**📁 Archivo**: `core/genetics/trait.py`
**🌍 Equivalencia real**: Una característica heredable abstracta (como "velocidad" o "inteligencia").

#### Atributos

| Atributo | Tipo | Equivalencia real | Descripción |
|----------|------|-------------------|-------------|
| `trait_id` | `str` | Nombre del gen | Identificador único ("fertility") |
| `name` | `str` | Nombre legible | "Fertilidad" |
| `category` | `TraitCategory` | Tipo funcional | BIOLOGY, BEHAVIOR, PERCEPTION, MOVEMENT, SPECIAL |
| `min_value` | `float` | Límite inferior | 0.0 |
| `max_value` | `float` | Límite superior | 2.0 |
| `default_value` | `float` | Valor típico | 1.0 |
| `expression_model` | `ExpressionModel` | Mecanismo | DOMINANT, RECESSIVE, CODOMINANT, etc. |
| `evolutionary_weight` | `float` | Presión selectiva | Impacto en supervivencia |
| `heritability` | `float` | Heredabilidad | 0.0=adquirido, 1.0=genético |
| `initial_distribution` | `Distribution` | Distribución inicial | NORMAL, UNIFORM, FIXED |
| `initial_mean` | `Optional[float]` | Media inicial | None usa default_value |
| `initial_std` | `float` | Desviación estándar | 0.1 |

#### Modelos de expresión

| Modelo | Descripción | Equivalencia real |
|--------|-------------|-------------------|
| `DOMINANT` | Gana el alelo con mayor dominancia | Mendel clásico |
| `RECESSIVE` | Gana el alelo con menor dominancia | Rasgos recesivos |
| `CODOMINANT` | Promedio simple | Expresión simultánea |
| `WEIGHTED_AVERAGE` | Promedio ponderado por dominancia | Expresión parcial |
| `ADDITIVE` | Suma de ambos alelos | Efecto aditivo |
| `MAX_VALUE` | Valor máximo | Dominancia total |
| `MIN_VALUE` | Valor mínimo | Recesividad total |

#### Distribuciones iniciales

| Distribución | Uso |
|--------------|-----|
| `NORMAL` | Rasgos cuantitativos continuos (campana de Gauss) |
| `UNIFORM` | Variación uniforme |
| `FIXED` | Sin variación (rasgos todo-o-nada) |

#### Ejemplos

```python
# Rasgo cuantitativo
fertility = Trait(
    trait_id="fertility",
    name="Fertilidad",
    category=TraitCategory.BIOLOGY,
    min_value=0.0,
    max_value=2.0,
    default_value=1.0,
    expression_model=ExpressionModel.WEIGHTED_AVERAGE,
    heritability=0.9,
    initial_distribution=Distribution.NORMAL,
)

# Rasgo cualitativo
flight = Trait(
    trait_id="flight",
    name="Vuelo",
    category=TraitCategory.MOVEMENT,
    min_value=0.0,
    max_value=2.0,
    default_value=0.0,
    expression_model=ExpressionModel.DOMINANT,
    heritability=1.0,
    initial_distribution=Distribution.FIXED,
)
```

---

### 2. TraitLibrary - Catálogo Universal

**📁 Archivo**: `core/genetics/trait_library.py`
**🌍 Equivalencia real**: El banco mundial de genes, con todos los rasgos posibles.

#### Rasgos disponibles (37 rasgos en 5 categorías)

| Categoría | Rasgos |
|-----------|--------|
| **BIOLOGY** (8) | fertility, immunity, longevity, metabolism, growth_rate, healing, nervous_system, heterotrophy |
| **BEHAVIOR** (10) | sociability, aggressiveness, territoriality, empathy, cooperation, curiosity, impulsivity, obedience, temperament, intelligence |
| **PERCEPTION** (5) | vision, smell, hearing, night_vision, echolocation |
| **MOVEMENT** (5) | speed, flight, swimming, climbing, burrowing |
| **SPECIAL** (9) | venom, photosynthesis, camouflage, regeneration, bioluminescence, division_speed, antibiotic_resistance, mobility, **symbiosis** |

#### Entradas

| Método | Equivalencia real | Descripción |
|--------|-------------------|-------------|
| `register_trait(trait)` | Catalogar un gen | Añade rasgo al catálogo |
| `get_trait(id)` | Consultar gen | Obtiene rasgo por ID |
| `has_trait(id)` | ¿Existe este gen? | Verifica existencia |
| `get_all_traits()` | Listar todos los genes | Catálogo completo |
| `get_traits_by_category(cat)` | Filtrar por tipo | Rasgos de categoría |

#### Flujo interno

```
TraitLibrary.get_default()  ← Singleton
    │
    ├── Primera llamada:
    │   └── _create_default_library()
    │       └── Registrar 37 rasgos predefinidos
    │
    └── Llamadas siguientes:
        └── Retornar instancia existente
```

#### Ejemplos

```python
library = TraitLibrary.get_default()

# Consultar rasgo
fertility = library.get_trait("fertility")
print(fertility.min_value, fertility.max_value)

# Verificar existencia
if library.has_trait("flight"):
    flight = library.get_trait("flight")

# Listar por categoría
biological_traits = library.get_traits_by_category(TraitCategory.BIOLOGY)

# Contar rasgos
print(f"Total: {len(library)} rasgos")
```

---

### 3. Allele y Gene - Unidades Hereditarias

**📁 Archivo**: `entities/person/allele.py`
**🌍 Equivalencia real**: El alelo es una variante de gen; el gen es un locus (par de alelos).

#### Allele (inmutable)

| Atributo | Tipo | Equivalencia real | Descripción |
|----------|------|-------------------|-------------|
| `value` | `float` | Expresión del gen | Valor fenotípico potencial |
| `dominance` | `float` | Fuerza de dominancia | [0.0, 1.0] |

#### Gene (par de alelos)

| Atributo | Tipo | Equivalencia real | Descripción |
|----------|------|-------------------|-------------|
| `allele_a` | `Allele` | Alelo materno | Copia del padre |
| `allele_b` | `Allele` | Alelo paterno | Copia de la madre |

#### Métodos clave

| Método | Equivalencia real | Descripción |
|--------|-------------------|-------------|
| `Allele.create_random(base, range)` | Crear alelo con variación | Genera alelo inicial |
| `Gene.express(model)` | Expresión fenotípica | Calcula valor visible |
| `Gene.meiosis()` | Segregación | Elige alelo al azar para herencia |

#### Flujo interno de express()

```
gene.express(model)
    │
    ├── DOMINANT:     max dominancia → retorna su valor
    ├── RECESSIVE:    min dominancia → retorna su valor
    ├── CODOMINANT:   (a.value + b.value) / 2
    ├── WEIGHTED_AVG: (a.value * a.dom + b.value * b.dom) / (a.dom + b.dom)
    ├── ADDITIVE:     a.value + b.value
    ├── MAX_VALUE:    max(a.value, b.value)
    └── MIN_VALUE:    min(a.value, b.value)
```

#### Ejemplos

```python
# Crear alelos con variación
allele_a = Allele.create_random(base_value=1.0, mutation_range=0.1)
allele_b = Allele.create_random(base_value=1.0, mutation_range=0.1)

# Crear gen
gene = Gene(allele_a, allele_b)

# Expresar fenotipo
value_dominant = gene.express("DOMINANT")
value_codominant = gene.express("CODOMINANT")

# Meiosis (elegir alelo para herencia)
gamete = gene.meiosis()  # Devuelve allele_a o allele_b al azar
```

---

### 4. Genome - El Genoma del Individuo

**📁 Archivo**: `entities/person/genome.py`
**🌍 Equivalencia real**: El ADN completo de un organismo individual.

#### Entradas (constructor)

| Parámetro | Tipo | Equivalencia real | Descripción |
|-----------|------|-------------------|-------------|
| `genes` | `Dict[str, Gene]` | Pares de alelos | Genes activos |
| `species_id` | `str` | Especie | "human", "wolf", etc. |
| `family_specific_immunity` | `Dict[str, Gene]` | Inmunidad genética | Por familia de patógenos |

#### Salidas (consultas)

| Método | Equivalencia real | Descripción |
|--------|-------------------|-------------|
| `get_trait_value(id)` | Fenotipo observable | Valor del rasgo |
| `get_gene(id)` | Gen específico | Par de alelos |
| `has_trait(id)` | ¿Tiene este gen? | Verificación |
| `get_all_trait_ids()` | Listado de genes | Rasgos activos |
| `get_all_trait_values()` | Perfil completo | Todos los valores |
| `get_family_specific_immunity(fam)` | Inmunidad específica | Resistencia a patógeno |

#### Métodos de reproducción

| Método | Equivalencia real | Descripción |
|--------|-------------------|-------------|
| `combine(other, mut_config)` | Reproducción sexual | Cruce de dos genomas |
| `replicate(mut_config)` | Reproducción asexual | Clonación con mutación |
| `create_founder(species)` | Población fundadora | Genoma inicial de especie |

#### Flujo interno de combine()

```
combine(other_genome, mutation_config)
    │
    ├── Determinar todos los genes de ambos progenitores
    │   all_genes = set(self._genes) | set(other._genes)
    │
    ├── Para cada gen:
    │   ├── allele_1 = self._genes[key].meiosis()
    │   ├── allele_2 = other._genes[key].meiosis()
    │   ├── allele_1 = _mutate_allele(allele_1, mut_config)
    │   └── allele_2 = _mutate_allele(allele_2, mut_config)
    │
    ├── Recombinar inmunidad específica por familia
    │
    └── Retornar nuevo Genome(new_genes, species_id)
```

#### Flujo interno de _mutate_allele()

```
_mutate_allele(allele, trait_id, mutation_config)
    │
    ├── if random() >= probability:
    │   └── No mutar (retornar original)
    │
    ├── Obtener rango del trait (TraitLibrary)
    │
    ├── delta = gauss(0, magnitude_std)
    ├── new_value = clamp(allele.value + delta, min, max)
    │
    ├── if mutate_dominance:
    │   └── new_dominance = clamp(allele.dominance + gauss(0, dominance_std))
    │
    └── Retornar Allele(new_value, new_dominance)
```

#### Ejemplos

```python
# Crear genoma fundador
human = SpeciesRegistry.get("human")
library = TraitLibrary.get_default()
genome = Genome.create_founder(human, library)

# Consultar valores
fertility = genome.get_trait_value("fertility")
print(f"Fertilidad: {fertility:.2f}")

# Reproducción sexual
child_genome = mother_genome.combine(father_genome, mutation_config)

# Reproducción asexual (bacterias, plantas)
clone = original_genome.replicate(mutation_config)

# Retrocompatibilidad (propiedades legacy)
print(genome.fertility)    # Equivalente a get_trait_value("fertility")
print(genome.sociability)  # Equivalente a get_trait_value("sociability")
```

#### Consideraciones

- El genoma es **inmutable** durante la vida del individuo
- `combine()` funciona para reproducción sexual (dos progenitores)
- `replicate()` funciona para reproducción asexual (un progenitor)
- Si `other_genome` es `None` en `combine()`, es partenogénesis (autofecundación)
- Las mutaciones aplican clampeo al rango del trait
- El cruce interespecie es posible pero hereda la línea materna

---

### 5. SpeciesDefinition - Definición de Especies

**📁 Archivo**: `core/genetics/species_definition.py`
**🌍 Equivalencia real**: El ADN de referencia de una especie (como el genoma humano de referencia).

#### Atributos

| Atributo | Tipo | Equivalencia real | Descripción |
|----------|------|-------------------|-------------|
| `species_id` | `str` | Código de especie | "human", "wolf" |
| `name` | `str` | Nombre común | "Humano", "Lobo" |
| `description` | `str` | Descripción | Texto descriptivo |
| `archetype` | `str` | Categoría biológica | "mammal", "bird" |
| `parent_template` | `Optional[str]` | Plantilla padre | Herencia de plantillas |
| `_trait_configs` | `Dict[str, TraitConfig]` | Rasgos activos | Configuraciones |
| `_habitat_preference` | `Optional[HabitatPreference]` | Hábitat ideal | Preferencias ambientales |

#### TraitConfig (configuración de rasgo)

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `default_value` | `float` | Valor por defecto |
| `min_value` | `Optional[float]` | Mínimo (None = del Trait) |
| `max_value` | `Optional[float]` | Máximo (None = del Trait) |
| `weight` | `float` | Importancia para la especie |
| `is_heritable` | `bool` | Si se hereda |

#### Jerarquía de plantillas

```
empty
├── animal
│   ├── vertebrate
│   │   ├── mammal → human
│   │   ├── bird
│   │   ├── reptile
│   │   ├── amphibian
│   │   └── fish
│   └── invertebrate → insect
├── plant
├── fungus
├── bacteria
└── fantasy_creature
```

#### Métodos clave

| Método | Equivalencia real | Descripción |
|--------|-------------------|-------------|
| `from_template(id, name, base)` | Derivar especie | Hereda de plantilla |
| `empty(id, name)` | Especie desde cero | Sin rasgos iniciales |
| `add_trait(id, default, ...)` | Activar rasgo | Añadir configuración |
| `remove_trait(id)` | Desactivar rasgo | Quitar localmente |
| `get_trait_config(id)` | Obtener configuración | Busca en cadena de herencia |
| `get_all_trait_ids()` | Listar rasgos activos | Locales + heredados |
| `set_habitat_preference(pref)` | Definir hábitat | Preferencias ambientales |
| `get_inheritance_chain()` | Ver herencia | Cadena de plantillas |

#### Especies predefinidas con hábitat

| Especie | Hábitat asignado |
|---------|------------------|
| human | create_human_habitat() |
| bird | create_bird_habitat() |
| fish | create_fish_habitat() |
| amphibian | create_aquatic_plant_habitat() |
| insect | create_bacteria_habitat() |
| fungus | create_fungus_habitat() |
| bacteria | create_bacteria_habitat() |

**Nota sobre el hongo**: La plantilla `fungus` incluye los rasgos `heterotrophy` (1.5) y `symbiosis` (1.8) que representan correctamente la biología fúngica:
- **Heterotrophy**: Los hongos son heterótrofos por absorción (descomponen materia orgánica)
- **Symbiosis**: Los hongos forman redes de micelio, micorrizas y asociaciones simbióticas (líquenes)

El rasgo `symbiosis` sustituye al `cooperation` que sería semánticamente incorrecto para organismos no sociales.

#### Ejemplos

```python
# Crear especie desde plantilla
wolf = SpeciesDefinition.from_template(
    species_id="wolf",
    name="Lobo",
    base_template="mammal",
    description="Mamífero social cazador"
)

# Añadir rasgos específicos
wolf.add_trait("speed", default_value=1.5, weight=1.0)
wolf.add_trait("cooperation", default_value=1.3, weight=0.9)
wolf.add_trait("territoriality", default_value=1.4, weight=0.8)

# Definir hábitat
wolf.set_habitat_preference(create_wolf_habitat())

# Registrar
SpeciesRegistry.register(wolf)

# Consultar herencia
chain = wolf.get_inheritance_chain()
print(chain)  # ["wolf", "mammal", "vertebrate", "animal", "empty"]

# Obtener rasgo efectivo (busca en cadena)
config = wolf.get_trait_config("fertility")
# Hereda de mammal si wolf no lo define
```

---

### 6. SpeciesRegistry - Registro Global

**📁 Archivo**: `core/genetics/species_definition.py`
**🌍 Equivalencia real**: El registro taxonómico mundial.

#### Métodos

| Método | Descripción |
|--------|-------------|
| `register(species)` | Registra especie |
| `get(id)` | Obtiene por ID |
| `has(id)` | Verifica existencia |
| `get_all()` | Todas las especies |
| `get_by_archetype(arch)` | Filtrar por arquetipo |
| `get_templates()` | Solo plantillas base |
| `initialize_defaults()` | Inicializar especies predefinidas |

#### Ejemplos

```python
# Inicializar todas las especies por defecto
SpeciesRegistry.initialize_defaults()

# Consultar especie
human = SpeciesRegistry.get("human")

# Listar arquetipos disponibles
archetypes = SpeciesRegistry.list_archetypes()
# ["animal", "bacteria", "bird", "empty", "fantasy", ...]

# Filtrar por arquetipo
mammals = SpeciesRegistry.get_by_archetype("mammal")
```

---

### 7. BiologicalValidator - Validador Biológico

**📁 Archivo**: `core/genetics/biological_validator.py`
**🌍 Equivalencia real**: Un biólogo experto que revisa la coherencia de una especie.

#### Tipos de reglas

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| **IncompatibilityRule** | Rasgos que raramente coexisten | flight + swimming |
| **DependencyRule** | Rasgos que requieren otros | empathy → nervous_system |
| **CategoryRule** | Coherencia de categorías | SPECIAL → BIOLOGY |

#### Severidad

| Nivel | Símbolo | Significado |
|-------|---------|-------------|
| `INFO` | ℹ️ | Combinación interesante |
| `WARNING` | ⚠️ | Combinación inusual pero posible |
| `ERROR` | ❌ | Biológicamente contradictoria |

#### Reglas predefinidas

**Incompatibilidades:**
- flight + swimming (WARNING)
- photosynthesis + heterotrophy (ERROR)
- venom + empathy (WARNING)
- night_vision + echolocation (INFO)
- longevity + fertility (INFO)
- speed + metabolism bajo (WARNING)

**Excepción para organismos simbióticos:**

Los organismos con `symbiosis` alto (>1.5) quedan **excluidos** de la regla `longevity + fertility`.

**Justificación biológica**: Los organismos simbióticos (hongos, líquenes) no siguen el trade-off longevidad-fertilidad de los animales:
- Los hongos pueden vivir décadas (micelio perenne) Y producir millones de esporas simultáneamente
- La reproducción por esporas no requiere inversión parental que limite la fertilidad
- El trade-off es exclusivo de organismos con reproducción sexual compleja

**Nota**: Esta excepción solo aplica a organismos con `symbiosis > 1.5`. Organismos con simbiosis moderada siguen sujetos a la regla de trade-off.

**Corrección de la regla speed + metabolism:**

La regla `speed + metabolism` solo se dispara cuando `speed > 1.0` Y `metabolism < 0.5` (alta velocidad con metabolismo bajo). No se dispara cuando ambos son altos, ya que un metabolismo alto sostiene la velocidad.

**Dependencias:**
- empathy → nervous_system (ERROR)
- intelligence → nervous_system (ERROR)
- echolocation → hearing (ERROR)
- cooperation → sociability (WARNING)
- obedience → intelligence (WARNING)
- flight → metabolism (WARNING)
- venom → metabolism (INFO)

#### Entradas

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `species` | `SpeciesDefinition` | Especie a validar |

#### Salidas

| Salida | Tipo | Descripción |
|--------|------|-------------|
| `ValidationResult` | Objeto | Resultado completo |

#### ValidationResult

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `is_valid` | `bool` | Sin errores |
| `errors` | `List[Message]` | Errores |
| `warnings` | `List[Message]` | Advertencias |
| `info` | `List[Message]` | Información |
| `score` | `float` | [0.0, 1.0] coherencia |
| `format_report()` | `str` | Reporte legible |

#### Flujo interno

```
validate_species(species)
    │
    ├── _check_incompatibilities()
    │   ├── Detectar si el organismo tiene symbiosis alto
    │   ├── Excluir simbióticos de la regla longevity-fertility
    │   ├── Lógica especial para speed + metabolism
    │   └── Para cada regla: si ambos rasgos presentes → mensaje
    │
    ├── _check_dependencies()
    │   └── Para cada regla: si rasgo presente sin prerrequisito → mensaje
    │
    ├── _check_categories()
    │   └── Si SPECIAL sin BIOLOGY → INFO
    │
    ├── _check_trait_values()
    │   └── Si valor fuera de rango → WARNING
    │
    └── _check_minimum_traits()
        └── Si pocos rasgos → INFO/WARNING
```

#### Ejemplos

```python
validator = BiologicalValidator()
human = SpeciesRegistry.get("human")

result = validator.validate_species(human)

print(f"Válido: {result.is_valid}")
print(f"Score: {result.score:.0%}")
print(f"Errores: {len(result.errors)}")
print(f"Advertencias: {len(result.warnings)}")

# Reporte completo
print(result.format_report())
```

---

### 8. RealismIndex - Índice de Realismo

**📁 Archivo**: `core/genetics/realism_index.py`
**🌍 Equivalencia real**: Un índice científico de plausibilidad biológica.

#### Entradas

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `species` | `SpeciesDefinition` | Especie a evaluar |

#### Salidas

| Salida | Tipo | Descripción |
|--------|------|-------------|
| `float` | [0.0, 1.0] | 0%=fantástico, 100%=realista |

#### Flujo interno

```
calculate(species)
    │
    ├── Validar especie (BiologicalValidator)
    ├── base_score = result.score
    │
    ├── Bonus:
    │   ├── +0.05 si ≥3 rasgos biológicos
    │   └── +0.03 si ≥3 categorías diferentes
    │
    ├── Penalización:
    │   └── -0.05 por cada rasgo especial
    │
    └── clamp(0.0, 1.0, base_score + adjustment)
```

#### Descripciones

| Rango | Descripción |
|-------|-------------|
| ≥90% | Biológicamente coherente |
| ≥70% | Mayormente realista con peculiaridades |
| ≥50% | Características mixtas |
| ≥30% | Características fantásticas |
| <30% | Completamente fantástica |

#### Ejemplos

```python
realism = RealismIndex()

human = SpeciesRegistry.get("human")
score = realism.calculate(human)
print(f"Realismo humano: {score:.0%}")  # ~85%

fantasy = SpeciesRegistry.get("fantasy_creature")
score = realism.calculate(fantasy)
print(f"Realismo fantasía: {score:.0%}")  # ~45%

print(realism.get_description(score))
# "Realismo: 85% - Especie biológicamente coherente."
```

---

## 🔗 Interacción entre componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                    TraitLibrary (Singleton)                     │
│         Catálogo global de 37 rasgos neutros                    │
└────────────────────────┬────────────────────────────────────────┘
                         │ consultado por
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              SpeciesDefinition + SpeciesRegistry                │
│      Plantillas de especies con rasgos activos + hábitat        │
└─────┬───────────────────────┬──────────────────────────────────┘
      │ validado por          │ usado para crear
      ▼                       ▼
┌─────────────────┐   ┌──────────────────────────────────────────┐
│ Biological      │   │              Genome                      │
│ Validator       │   │   Genoma del individuo (inmutable)       │
│                 │   │                                          │
│ + RealismIndex  │   │   ┌──────────────────────────────────┐  │
│                 │   │   │ _genes: Dict[str, Gene]          │  │
└─────────────────┘   │   │   cada Gene = (Allele, Allele)   │  │
                      │   └──────────────────────────────────┘  │
                      │                                          │
                      │   métodos:                               │
                      │   ├── create_founder()                   │
                      │   ├── combine() [sexual]                 │
                      │   └── replicate() [asexual]              │
                      └──────────────────────────────────────────┘
```

---

## ⚙️ Configuración relevante

```python
# Desde SimulationConfig
config.mutation.probability = 0.05       # 5% probabilidad de mutar
config.mutation.magnitude_std = 0.1      # Desviación gaussiana
config.mutation.dominance_std = 0.05     # Mutación de dominancia
config.mutation.mutate_dominance = True  # ¿Mutar dominancia?
```

---

## 🧪 Tests del sistema

**Total: 342 tests pasando**

| Archivo | Tests | Cobertura |
|---------|-------|-----------|
| `tests/unit/test_genetics_universal.py` | 40 | Trait, TraitLibrary, SpeciesDefinition, BiologicalValidator, RealismIndex |
| `tests/unit/test_mutation.py` | 22 | Mutación de alelos, replicación |
| `tests/unit/test_genome_combine.py` | 21 | Genome.combine(), Allele, Gene |
| `tests/unit/test_catastrophe_system.py` | 16 | Catástrofes naturales |
| `tests/unit/test_habitat_compatibility.py` | 14 | Compatibilidad de hábitats |
| `tests/unit/test_immunological_capabilities.py` | 13 | Capacidades inmunológicas |
| `tests/unit/test_cognitive_capabilities.py` | 22 | Capacidades cognitivas |
| `tests/unit/test_movement_capabilities.py` | 14 | Capacidades de movimiento |
| `tests/unit/test_reproductive_capabilities.py` | 18 | Capacidades reproductivas |
| `tests/unit/test_social_capabilities.py` | 18 | Capacidades sociales |
| `tests/integration/test_regression_bugs.py` | 9 | Regresiones |
| `tests/integration/test_statistical.py` | 3 | Estadística |
| `tests/integration/test_tile_integration.py` | 11 | Integración de tiles |
| Otros tests de sistemas | 121 | Comportamiento, relaciones, memoria, etc. |

---

## 🔒 Estado del núcleo genético

**Estado: CONGELADO** (Agosto 2026)

El núcleo genético está cerrado. No se modificará salvo que una necesidad real de otro sistema lo requiera. Todo lo demás debe construirse encima del núcleo, nunca dentro de él.

### Lo que está cerrado ✅
- Trait (definición de rasgos)
- TraitLibrary (biblioteca de rasgos)
- SpeciesDefinition (plantillas y especies)
- SpeciesRegistry (registro de especies)
- Genome (genotipo de un individuo)
- Gene / Allele
- ExpressionModel (7 modelos)
- MutationConfig
- BiologicalValidator
- RealismIndex
- Herencia mendeliana (combine, meiosis)
- Reproducción asexual (replicate)
- Mutación con clampeo
- Rangos definidos

### Lo que está pendiente ⏸
- Taxonomía y compatibilidad reproductiva
- Biomas y terrenos
- Movimiento por rasgos (flight, swimming)
- Interacciones entre especies
- Conceptos humanos opcionales

**Nota**: Para la especificación conceptual detallada, ver `docs/specs/GENETICS_CORE_SPEC.md`.

### Adiciones recientes (Agosto 2026)

Aunque el núcleo está congelado, se han realizado las siguientes adiciones compatibles:
- ✅ **Nuevo rasgo `symbiosis`** (categoría SPECIAL): Capacidad de formar asociaciones simbióticas con otros organismos. Usado por hongos (1.8) y disponible para líquenes, plantas y bacterias simbióticas.
- ✅ **Plantilla `fungus` actualizada**: Añadido `heterotrophy` (1.5) y `symbiosis` (1.8), eliminado `cooperation` (semánticamente incorrecto para hongos).
- ✅ **Excepción de validación para organismos simbióticos**: Los organismos con `symbiosis > 1.5` quedan excluidos de la regla `longevity + fertility`.
- ✅ **Corrección de regla speed + metabolism**: La regla ahora solo se dispara cuando hay alta velocidad con metabolismo bajo, no cuando ambos son altos.
- ✅ **Rasgo `symbiosis` en TraitLibrary**: Total de rasgos actualizado de 36 a 37.

---

## 🔄 Sistemas migrados a API genérica

Todos los sistemas de simulación han sido migrados para usar `get_trait_value()` en lugar de propiedades legacy.

| Sistema | Propiedades migradas |
|---------|---------------------|
| `systems/diseases/disease_system.py` | immunity |
| `systems/temporal/temporal_system.py` | temperament, immunity |
| `systems/mortality/mortality_system.py` | longevity |
| `systems/behavior/cognitive_memory_system.py` | temperament |
| `systems/genealogy/genealogy_system.py` | longevity, sociability, temperament |
| `systems/free_will/free_will_system.py` | impulsivity, curiosity, obedience, aggressiveness, temperament, sociability |
| `systems/aging/aging_system.py` | longevity |
| `systems/movement/movement_system.py` | curiosity |
| `systems/reproduction/conception_system.py` | fertility, longevity |
| `systems/reproduction/gestation_system.py` | Soporte para asexual con replicate() |

**Nota**: Las propiedades legacy (`.longevity`, `.fertility`, etc.) se mantienen por retrocompatibilidad pero internamente llaman a `get_trait_value()`.

---

## 📝 Ejemplos completos

### Crear una nueva especie completa

```python
from core.genetics.species_definition import SpeciesDefinition, SpeciesRegistry
from systems.environment.habitat_preference import HabitatPreference

# 1. Crear especie derivada
wolf = SpeciesDefinition.from_template(
    species_id="wolf",
    name="Lobo",
    base_template="mammal",
    description="Mamífero social cazador de manada",
)

# 2. Añadir rasgos específicos
wolf.add_trait("speed", default_value=1.5, weight=1.0)
wolf.add_trait("cooperation", default_value=1.5, weight=1.0)
wolf.add_trait("territoriality", default_value=1.4, weight=0.9)
wolf.add_trait("pack_hunting", default_value=1.8, weight=1.0)

# 3. Definir hábitat
wolf_pref = HabitatPreference(
    temperature_ideal=0.35,
    temperature_tolerance=0.3,
    water_ideal=0.3,
    vegetation_ideal=0.5,
)
wolf.set_habitat_preference(wolf_pref)

# 4. Validar
validator = BiologicalValidator()
result = validator.validate_species(wolf)
print(result.format_report())

# 5. Registrar
SpeciesRegistry.register(wolf)
```

### Reproducción sexual

```python
from entities.person.genome import Genome
from core.config.simulation_config import MutationConfig

# Genomas de los padres
mother_genome = Genome.create_founder(human_species, library)
father_genome = Genome.create_founder(human_species, library)

# Configurar mutación
mut_config = MutationConfig(
    probability=0.05,
    magnitude_std=0.1,
    mutate_dominance=True,
)

# Cruzar
child_genome = mother_genome.combine(father_genome, mut_config)

# Consultar rasgos
print(f"Fertilidad: {child_genome.fertility:.2f}")
print(f"Inteligencia: {child_genome.get_trait_value('intelligence'):.2f}")
```

### Reproducción asexual (bacterias)

```python
# Una bacteria se divide
parent = Genome(species_id="bacteria")

# Clonar con mutación
daughter = parent.replicate(mut_config)

# Comparar
print(f"Original: {parent.get_trait_value('division_speed'):.2f}")
print(f"Clon: {daughter.get_trait_value('division_speed'):.2f}")
```

---

## 🚨 Consideraciones y limitaciones

### Principios fundamentales
- **Rasgos neutros**: los rasgos no saben de especies ni biología
- **Separación de responsabilidades**: TraitLibrary (qué existe) vs SpeciesDefinition (qué usa) vs BiologicalValidator (qué es coherente)
- **Genoma inmutable**: una vez creado, el genoma no cambia
- **Herencia mendeliana pura**: dominancia, segregación, mutación

### Rendimiento
- `TraitLibrary` es singleton (se crea una vez)
- `SpeciesRegistry` es clase estática (sin instancias)
- `Genome.get_trait_value()` es O(1)
- `Genome.combine()` es O(n) donde n = número de rasgos

### Limitaciones
- No hay epigenética (los cambios durante la vida no se heredan)
- No hay epistasis (interacción entre genes)
- No hay ligamiento genético (los genes se heredan independientemente)
- Las mutaciones son gaussianas (no dirigidas)

### Errores comunes
- ❌ Modificar el genoma después de creado
- ❌ Usar `combine()` para organismos asexuales (usar `replicate()`)
- ❌ Olvidar registrar la especie en `SpeciesRegistry`
- ❌ Asumir que `BiologicalValidator` impide configuraciones (solo informa)

---

## 🎓 Conceptos clave

### ¿Por qué los rasgos son neutros?

**Principio de separación de responsabilidades**:
- `Trait` solo describe QUÉ es (id, rango, modelo)
- `SpeciesDefinition` describe QUÉ RASGOS usa cada especie
- `BiologicalValidator` describe QUÉ COMBINACIONES son coherentes
- `Genome` describe QUÉ ALELOS tiene cada individuo

Esto permite añadir nuevos rasgos sin tocar nada más.

### ¿Por qué múltiples modelos de expresión?

La naturaleza tiene muchos tipos de herencia:
- **DOMINANT**: Mendel clásico (guisantes)
- **CODOMINANT**: Tipos de sangre ABO
- **WEIGHTED_AVERAGE**: Rasgos poligénicos (altura)
- **ADDITIVE**: Efecto aditivo (pigmentación)

Cada rasgo elige el modelo que mejor lo representa.

### ¿Por qué validate pero no impide?

**Filosofía del simulador**: el usuario tiene libertad absoluta. El validador es un asesor, no un policía. Si quieres crear un mamífero con fotosíntesis, el sistema te avisará pero no te impedirá hacerlo.

### ¿Por qué un rasgo symbiosis separado de cooperation?

**Principio de precisión semántica**:
- `cooperation` representa cooperación SOCIAL (animales que cazan juntos, se defienden mutuamente)
- `symbiosis` representa cooperación QUÍMICA/ESTRUCTURAL (redes de micelio, micorrizas, líquenes)
- Los hongos no son sociales en el sentido animal, pero son los organismos simbióticos más importantes del planeta
- Usar el rasgo correcto permite que el validador aplique reglas específicas (ej: excepción longevity-fertility para simbióticos)

---

## 📊 Métricas del sistema

| Métrica | Valor |
|---------|-------|
| Rasgos disponibles | 37 |
| Categorías de rasgos | 5 |
| Modelos de expresión | 7 |
| Especies predefinidas | 15 |
| Plantillas base | 9 |
| Reglas de validación | 13 |
| Excepciones de validación | 1 (organismos simbióticos) |
| Tests cubriendo genética | ~342 |

---

## 🔮 Futuras extensiones

### Planificadas (corto plazo)
- [ ] Taxonomía y compatibilidad reproductiva (evitar cruces imposibles)
- [ ] Diseño de sistema de biomas/terrenos
- [ ] Movimiento por rasgos (flight, swimming, burrowing)
- [ ] Interacciones entre especies (depredación, parasitismo)
- [ ] Conceptos humanos opcionales (marriage, pregnancy según especie)
- [ ] Mecánica del rasgo `symbiosis`: efecto en FeedbackSystem (hongos mejoran crecimiento de plantas cercanas)

### Planificadas (medio plazo)
- [ ] Epigenética (marcadores que afectan expresión sin cambiar ADN)
- [ ] Epistasis (interacciones entre genes)
- [ ] Ligamiento genético (genes cercanos se heredan juntos)
- [ ] Recombinación cromosómica (crossing-over)
- [ ] Plantillas para líquenes y bacterias simbióticas usando `symbiosis`

### Posibles (largo plazo)
- [ ] Mutación dirigida por estrés ambiental
- [ ] Transferencia horizontal de genes (bacterias)
- [ ] Hibridación entre especies
- [ ] Edición genética (CRISPR simulado)

---

*Documento: 03_GENETICA.md*
*Versión: 2.1 (actualizado con rasgo symbiosis y correcciones del validador)*
*Última actualización: Agosto 2026*