# 19 - Sistema Taxonómico

## 📋 Resumen

El **Sistema Taxonómico** proporciona clasificación jerárquica de especies y perfiles biológicos. Es un sistema **informativo**: clasifica y organiza especies, pero **no decide capacidades**. Las capacidades siguen saliendo de la genética (Genome).

**Filosofía fundamental**: *La taxonomía dice QUÉ ES una especie. El perfil dice CÓMO suele vivir. El genoma dice QUÉ PUEDE HACER.*

---

## 🎯 Responsabilidad

**Es responsable de:**
- Clasificar especies en una jerarquía taxonómica (`TaxonomicSystem`)
- Describir perfiles biológicos de especies (`SpeciesProfile`)
- Inferir perfiles desde rasgos genéticos (`ProfileInference`)
- Unificar taxonomía y perfiles con especies existentes (`SpeciesClassificationSystem`)
- Proporcionar consultas para el sistema ecológico

**NO es responsable de:**
- ❌ Decidir capacidades de las especies (lo hace el Genome)
- ❌ Imponer restricciones basadas en taxonomía
- ❌ Determinar relaciones ecológicas (lo hace el EcologicalRelationshipSystem)
- ❌ Almacenar el estado del mundo (lo hace `WorldState`)

---

## 🌍 Separación de conceptos

```
Taxonomy           → ¿Qué es esta especie?
                      (Animal, Vertebrado, Mamífero, Carnívoro)

SpeciesProfile     → ¿Cómo suele vivir esta especie?
                      (Carnívoro, terrestre, corredor, manada)

Genome             → ¿Qué puede hacer este individuo?
                      (Velocidad=1.6, Olfato=2.1, Agresividad=0.8)

EcologicalRelationship → ¿Cómo interactúan según lo anterior?
                          (Depredación, Mutualismo, Competencia)
```

---

## 📁 Archivos que lo componen

| Archivo | Clase principal | Responsabilidad |
|---------|-----------------|-----------------|
| `core/taxonomy/taxonomic_node.py` | `TaxonomicNode`, `TaxonomicRank` | Nodos del árbol taxonómico |
| `core/taxonomy/taxonomic_system.py` | `TaxonomicSystem` | Árbol taxonómico global |
| `core/taxonomy/profile_enums.py` | `DietType`, `HabitatType`, etc. | Enums del perfil biológico |
| `core/taxonomy/species_profile.py` | `SpeciesProfile` | Perfil biológico de una especie |
| `core/taxonomy/profile_inference.py` | `ProfileInference` | Inferencia desde genética |
| `core/taxonomy/species_classification.py` | `SpeciesClassificationSystem` | Sistema unificado |

---

## 🔄 Flujo de ejecución

```
┌─────────────────────────────────────────────────────────────────┐
│              FLUJO TAXONÓMICO COMPLETO                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. INICIALIZACIÓN DEL ÁRBOL TAXONÓMICO                          │
│    ├── TaxonomicSystem.initialize_default_taxonomy()            │
│    ├── Registrar DOMAIN, KINGDOM, PHYLUM, CLASS, etc.           │
│    └── 30 taxones precargados                                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. CLASIFICACIÓN DE ESPECIES                                    │
│    ├── SpeciesClassificationSystem.initialize_defaults()        │
│    ├── Asignar taxonomía a cada especie                         │
│    └── Inferir perfil biológico desde rasgos genéticos          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. CONSULTAS (durante la simulación)                            │
│    ├── Consultas taxonómicas: is_mammal(), is_descendant_of()   │
│    ├── Consultas de perfil: get_diet(), get_habitat()           │
│    ├── Consultas por categoría: get_species_by_diet()           │
│    └── Consultas ecológicas: can_interact(), get_potential_prey()│
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. USO EN ECOLOGÍA                                              │
│    ├── EcologicalRelationshipSystem consulta perfil + genoma    │
│    ├── Inferencia de relaciones: Predation, Mutualism, etc.     │
│    └── Verificación de condiciones ambientales                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes del Sistema

---

### 1. TaxonomicRank - Rangos Taxonómicos

**📁 Archivo**: `core/taxonomy/taxonomic_node.py`
**🌍 Equivalencia real**: Los niveles de la clasificación biológica de Linneo.

#### Rangos disponibles (9 niveles)

| Rango | Nivel | Ejemplo |
|-------|-------|---------|
| `DOMAIN` | 0 | Life |
| `KINGDOM` | 1 | Animalia, Plantae, Fungi, Bacteria |
| `PHYLUM` | 2 | Vertebrata, Arthropoda |
| `CLASS` | 3 | Mammalia, Aves, Reptilia |
| `ORDER` | 4 | Carnivora, Primates, Rodentia |
| `FAMILY` | 5 | Canidae, Felidae, Ursidae |
| `GENUS` | 6 | Canis, Felis, Ursus |
| `SPECIES` | 7 | Canis lupus, Felis catus |
| `SUBSPECIES` | 8 | Canis lupus familiaris |

---

### 2. TaxonomicNode - Nodo del Árbol

**📁 Archivo**: `core/taxonomy/taxonomic_node.py`
**🌍 Equivalencia real**: Un grupo taxonómico (ej: "Mamíferos").

#### Atributos

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `taxon_id` | `str` | Identificador único ("mammalia") |
| `name` | `str` | Nombre legible ("Mamíferos") |
| `parent_id` | `Optional[str]` | ID del taxón padre |
| `rank` | `TaxonomicRank` | Rango taxonómico |
| `description` | `str` | Descripción opcional |
| `scientific_name` | `str` | Nombre científico ("Canis lupus") |

#### Ejemplos

```python
# Crear un nodo taxonómico
mammalia = TaxonomicNode(
    taxon_id="mammalia",
    name="Mamíferos",
    parent_id="vertebrata",
    rank=TaxonomicRank.CLASS,
    description="Vertebrados de sangre caliente con glándulas mamarias",
)

# Crear una subespecie en runtime (para evolución)
dog = TaxonomicNode(
    taxon_id="canis_lupus_familiaris",
    name="Perro doméstico",
    parent_id="canis_lupus",
    rank=TaxonomicRank.SUBSPECIES,
    description="Subespecie domesticada del lobo",
)
```

---

### 3. TaxonomicSystem - Árbol Taxonómico Global

**📁 Archivo**: `core/taxonomy/taxonomic_system.py`
**🌍 Equivalencia real**: El árbol de la vida completo.

#### Métodos clave

| Método | Descripción |
|--------|-------------|
| `register(node)` | Registra un nuevo taxón (editable en runtime) |
| `unregister(taxon_id)` | Elimina un taxón y sus descendientes |
| `get(taxon_id)` | Obtiene un nodo por ID |
| `has(taxon_id)` | Verifica existencia |
| `get_ancestors(taxon_id)` | Cadena de ancestros |
| `get_descendants(taxon_id)` | Todos los descendientes |
| `is_descendant_of(taxon_id, ancestor_id)` | Verifica descendencia |
| `get_all_by_rank(rank)` | Todos los nodos de un rango |
| `get_kingdom_of(taxon_id)` | Reino de un taxón |
| `get_class_of(taxon_id)` | Clase de un taxón |
| `search_by_name(query)` | Búsqueda por nombre |
| `get_statistics()` | Estadísticas del árbol |

#### Ejemplos

```python
taxonomy = TaxonomicSystem.get_default()

# Consultas jerárquicas
is_mammal = taxonomy.is_descendant_of("canis_lupus", "mammalia")  # True
ancestors = taxonomy.get_ancestors("canis_lupus")
# [canis_lupus, canis, canidae, carnivora, mammalia, vertebrata, animalia, life]

# Consultas por rango
classes = taxonomy.get_all_by_rank(TaxonomicRank.CLASS)
# [mammalia, aves, reptilia, amphibia, pisces, insecta, arachnida]

# Edición en runtime (para evolución)
taxonomy.register(TaxonomicNode(
    taxon_id="canis_lupus_familiaris",
    name="Perro doméstico",
    parent_id="canis_lupus",
    rank=TaxonomicRank.SUBSPECIES,
))
```

---

### 4. SpeciesProfile - Perfil Biológico

**📁 Archivo**: `core/taxonomy/species_profile.py`
**🌍 Equivalencia real**: La ecología descriptiva de una especie.

#### Atributos

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `taxonomy_id` | `str` | ID del taxón en el árbol |
| `body_size_category` | `BodySizeCategory` | Tamaño corporal |
| `thermoregulation` | `ThermoregulationType` | Termorregulación |
| `diet` | `DietType` | Tipo de dieta |
| `reproduction` | `ReproductionType` | Tipo de reproducción |
| `development` | `DevelopmentType` | Tipo de desarrollo |
| `habitat` | `HabitatType` | Hábitat principal |
| `locomotion` | `LocomotionType` | Locomoción principal |
| `social_structure` | `SocialStructureType` | Estructura social |
| `activity_pattern` | `ActivityPattern` | Patrón de actividad |

#### Métodos de consulta

| Método | Descripción |
|--------|-------------|
| `is_carnivore()` | ¿Es carnívoro? |
| `is_herbivore()` | ¿Es herbívoro? |
| `is_predator()` | ¿Es depredador potencial? |
| `can_fly()` | ¿Su locomoción es volar? (descripción, no capacidad) |
| `is_terrestrial()` | ¿Es terrestre? |
| `is_aquatic()` | ¿Es acuático? |
| `is_social()` | ¿Tiene estructura social? |

#### Ejemplos

```python
# Crear perfil manual
wolf_profile = SpeciesProfile(
    taxonomy_id="canis_lupus",
    body_size_category=BodySizeCategory.MEDIUM,
    thermoregulation=ThermoregulationType.HOMEOTHERM,
    diet=DietType.CARNIVORE,
    reproduction=ReproductionType.SEXUAL,
    development=DevelopmentType.VIVIPAROUS,
    habitat=HabitatType.TERRESTRIAL,
    locomotion=LocomotionType.RUNNING,
    social_structure=SocialStructureType.PACK,
    activity_pattern=ActivityPattern.CREPUSCULAR,
)

# Consultas
wolf_profile.is_carnivore()  # True
wolf_profile.is_predator()   # True
wolf_profile.is_social()     # True
```

---

### 5. ProfileInference - Inferencia desde Genética

**📁 Archivo**: `core/taxonomy/profile_inference.py`
**🌍 Equivalencia real**: Un biólogo que observa los rasgos de una especie y deduce su ecología.

#### Lógica de inferencia

| Componente | Rasgos usados | Lógica |
|-----------|---------------|--------|
| **Dieta** | photosynthesis, heterotrophy, symbiosis, division_speed, diet | Fotosintético si photosynthesis > 1.0, carnívoro si diet > 1.5 |
| **Hábitat** | swimming, flight, burrowing, healing | Acuático si swimming > 1.0, anfibio si swimming + healing alto |
| **Locomoción** | flight, swimming, burrowing, climbing, speed, mobility | Sésil si fungus/plant, flying si flight > 1.0 |
| **Estructura social** | sociability, cooperation, territoriality, pack_behavior | Colonia si sociability > 1.5, manada si pack_behavior > 1.0 |
| **Termorregulación** | metabolism, nervous_system, flight | Homeotermo si nervous_system > 0.8 + metabolism > 1.0 |
| **Tamaño** | body_size, growth_rate, division_speed | Microscópico si division_speed > 0.5 |
| **Reproducción** | division_speed, photosynthesis, symbiosis, swimming | Asexual si division_speed > 0.5, esporas si planta/hongo |
| **Actividad** | night_vision | Nocturno si night_vision > 1.0 |

#### Ejemplos

```python
inference = ProfileInference()

# Inferir perfil desde rasgos genéticos
human_species = SpeciesRegistry.get("human")
human_profile = inference.infer(human_species)

print(human_profile.diet)              # DietType.OMNIVORE
print(human_profile.habitat)           # HabitatType.TERRESTRIAL
print(human_profile.locomotion)        # LocomotionType.WALKING
print(human_profile.thermoregulation)  # ThermoregulationType.HOMEOTHERM
```

---

### 6. SpeciesClassificationSystem - Sistema Unificado

**📁 Archivo**: `core/taxonomy/species_classification.py`
**🌍 Equivalencia real**: Un registro biológico completo que une taxonomía, perfiles y especies.

#### Métodos de registro

| Método | Descripción |
|--------|-------------|
| `register_species(species, taxon_id, profile)` | Registra especie con taxonomía y perfil |
| `register_taxonomy_for_species(species_id, taxon_id)` | Asigna taxón |
| `register_profile_for_species(species_id, profile)` | Asigna perfil manual |
| `initialize_defaults()` | Inicializa especies por defecto |

#### Métodos de consulta taxonómica

| Método | Descripción |
|--------|-------------|
| `get_taxonomy_id(species_id)` | ID del taxón |
| `get_taxonomy_node(species_id)` | Nodo taxonómico |
| `get_taxonomy_chain(species_id)` | Cadena completa |
| `is_descendant_of(species_id, ancestor_id)` | Verifica descendencia |
| `is_mammal(species_id)` | ¿Es mamífero? |
| `is_bird(species_id)` | ¿Es ave? |
| `is_reptile(species_id)` | ¿Es reptil? |
| `is_fish(species_id)` | ¿Es pez? |
| `is_insect(species_id)` | ¿Es insecto? |
| `is_fungus(species_id)` | ¿Es hongo? |
| `is_plant(species_id)` | ¿Es planta? |
| `is_bacteria(species_id)` | ¿Es bacteria? |

#### Métodos de consulta de perfil

| Método | Descripción |
|--------|-------------|
| `get_profile(species_id)` | Perfil completo |
| `get_diet(species_id)` | Dieta |
| `get_habitat(species_id)` | Hábitat |
| `get_locomotion(species_id)` | Locomoción |
| `is_carnivore(species_id)` | ¿Es carnívoro? |
| `is_herbivore(species_id)` | ¿Es herbívoro? |
| `is_predator(species_id)` | ¿Es depredador? |

#### Métodos de consulta por categoría

| Método | Descripción |
|--------|-------------|
| `get_species_by_diet(diet)` | Especies con dieta específica |
| `get_species_by_habitat(habitat)` | Especies con hábitat específico |
| `get_species_by_locomotion(locomotion)` | Especies con locomoción específica |
| `get_species_by_taxonomy(ancestor_id)` | Especies descendientes de un taxón |

#### Métodos para ecología

| Método | Descripción |
|--------|-------------|
| `can_interact(species_a_id, species_b_id)` | ¿Pueden interactuar? |
| `get_potential_prey(predator_id)` | Presas potenciales |

#### Ejemplos

```python
classification = SpeciesClassificationSystem.get_default()
classification.initialize_defaults()

# Consultas taxonómicas
classification.is_mammal("human")       # True
classification.is_bird("bird")          # True
classification.is_fungus("fungus")      # True

# Consultas de perfil
classification.get_diet("human")        # DietType.OMNIVORE
classification.is_carnivore("human")    # False
classification.get_habitat("fish")      # HabitatType.AQUATIC

# Consultas por categoría
omnivores = classification.get_species_by_diet(DietType.OMNIVORE)
# ['human', 'bird', 'fish', 'insect', 'reptile', 'amphibian']

aquatic = classification.get_species_by_habitat(HabitatType.AQUATIC)
# ['fish']

# Consultas para ecología
classification.can_interact("human", "bird")    # False (hábitats incompatibles)
classification.can_interact("human", "fish")    # False (hábitats incompatibles)
classification.can_interact("human", "reptile") # True (ambos terrestres)
```

---

## 🔗 Interacción con otros sistemas

```
┌────────────────────────────────────────────────────────────────┐
│                  SpeciesClassificationSystem                   │
│      Taxonomía + Perfiles + Especies existentes                │
└────────────────────┬───────────────────────────────────────────┘
                     │ consultado por
                     ▼
┌────────────────────────────────────────────────────────────────┐
│              EcologicalRelationshipSystem                      │
│    Infiere relaciones usando:                                  │
│    ├── Perfil: ¿Es carnívoro? ¿Es presa adecuada?              │
│    ├── Genoma: ¿Tiene instinto de caza? ¿Tiene defensa?        │
│    └── Bioma: ¿El entorno lo permite?                          │
└────────────────────────────────────────────────────────────────┘
```

---

## 📊 Métricas del sistema

| Métrica | Valor |
|---------|-------|
| Niveles taxonómicos | 9 |
| Taxones registrados | 30 |
| Enums de perfil | 8 |
| Especies clasificadas | 8 |
| Consultas taxonómicas | 12 métodos |
| Consultas de perfil | 7 métodos |
| Consultas por categoría | 4 métodos |
| Consultas ecológicas | 2 métodos |

---

## 🚨 Consideraciones y limitaciones

### Principios fundamentales
- **Taxonomía informativa**: La taxonomía nunca decide capacidades
- **Perfiles descriptivos**: Los perfiles describen patrones típicos, no restricciones
- **Inferencia desde genética**: Los perfiles se infieren desde rasgos genéticos
- **Editable en runtime**: El árbol taxonómico puede modificarse para soportar evolución

### Limitaciones
- Los perfiles inferidos pueden no ser perfectos para todas las especies
- La taxonomía por defecto incluye solo 30 taxones (ampliable)
- Las consultas de ecología (`can_interact`) son básicas; el EcologicalRelationshipSystem hará verificaciones más detalladas

### Errores comunes
- ❌ Asumir que la taxonomía decide capacidades (las capacidades salen del Genome)
- ❌ Usar `is_mammal()` para determinar si una especie puede volar (usar `Genome.get_trait_value("flight")`)
- ❌ Modificar el árbol taxonómico sin actualizar las especies clasificadas
- ❌ Crear perfiles manuales que contradigan los rasgos genéticos

---

## 🎓 Conceptos clave

### ¿Por qué separar Taxonomy, Profile y Genome?

**Tres preguntas distintas**:
- **Taxonomy**: ¿Qué es? → Clasificación jerárquica
- **Profile**: ¿Cómo vive? → Descripción ecológica
- **Genome**: ¿Qué puede hacer? → Capacidades individuales

### ¿Por qué la taxonomía no decide capacidades?

**Ejemplo**: ¿Un mamífero puede volar? Normalmente no… pero un murciélago sí.

Si la taxonomía dijera "los mamíferos no vuelan", romperíamos la flexibilidad del núcleo genético. La capacidad de volar sale del trait `flight` en el Genome, no de la clasificación taxonómica.

### ¿Por qué inferir perfiles desde genética?

**Coherencia con el núcleo genético**: Los rasgos son la fuente de verdad. Si una especie tiene `swimming = 1.8`, el perfil debe inferir hábitat acuático, no lo contrario.

---

## 🔮 Futuras extensiones

### Planificadas (corto plazo)
- [ ] Integración con EcologicalRelationshipSystem
- [ ] Más taxones en el árbol por defecto
- [ ] Más especies clasificadas (wolf, deer, plant, etc.)

### Planificadas (medio plazo)
- [ ] Evolución: nuevas especies aparecen y se clasifican automáticamente
- [ ] Subespecies dinámicas (especiación)
- [ ] Árbol filogenético visual

### Posibles (largo plazo)
- [ ] Taxonomía basada en genética (cladística computacional)
- [ ] Migración de especies entre taxones (evolución dirigida)
- [ ] Registro de extinciones y especiación

---

*Documento: 19_TAXONOMIA.md*
*Versión: 1.0*
*Última actualización: Agosto 2026*