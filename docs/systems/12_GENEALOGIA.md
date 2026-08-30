# 12 - Genealogía

## 📋 Resumen

El **Sistema de Genealogía** mantiene el registro histórico completo del árbol genealógico del mundo simulado: agentes vivos y fallecidos, relaciones biológicas y adoptivas, linajes fundadores, eventos macro-históricos (extinción de linajes), y consultas analíticas complejas sobre consanguinidad, endogamia y éxito reproductivo. Actúa como la "memoria histórica" del simulador, persistiendo información post-mortem para análisis longitudinal.

**Filosofía fundamental**: *El árbol genealógico es un grafo histórico bidireccional que persiste más allá de la muerte. Los agentes fallecidos siguen siendo nodos activos en el grafo, permitiendo análisis genealógicos, detección de endogamia y trazabilidad evolutiva a lo largo de generaciones.*

---

## 🎯 Responsabilidad

**Es responsable de:**
- Persistir el historial completo de cada agente (vivos y fallecidos)
- Mantener relaciones biológicas y adoptivas bidireccionales
- Registrar matrimonios, divorcios, nacimientos, adopciones y muertes
- Detectar eventos macro-históricos (extinción de linajes)
- Calcular grados de parentesco civil (BFS en el grafo)
- Detectar uniones consanguíneas prohibidas
- Calcular coeficientes de endogamia (inbreeding risk)
- Proveer estadísticas de linaje (supervivencia, esperanza de vida)
- Calcular éxito reproductivo para el motor evolutivo
- Resolver consultas genealógicas complejas sin exponer el grafo

**NO es responsable de:**
- ❌ Almacenar el estado del mundo actual (eso lo hace `WorldState`)
- ❌ Ejecutar lógica de juego (eso lo hacen los sistemas individuales)
- ❌ Calcular compatibilidad de pareja (eso lo hace `CompatibilityEngine`)
- ❌ Decidir matrimonios (eso lo hace `MarriageSystem`)
- ❌ Procesar adopciones (eso lo hace `AdoptionSystem`)
- ❌ Calcular mortalidad (eso lo hace `MortalitySystem`)

---

## 🌍 Equivalencia con la vida real

| Concepto del sistema | Equivalencia en la vida real | Unidad |
|---------------------|-----------------------------|--------|
| **HistoricalPersonNode** | Ficha biográfica completa | Registro civil |
| **GenealogySystem** | Registro civil nacional | Base de datos histórica |
| **AncestryQueries** | Oficina de consultas genealógicas | API de análisis |
| **Lineage** | Familia / clan / dinastía | Linaje fundador |
| **Consanguinity limit** | Ley de matrimonio | Prohibición legal |
| **Degree of kinship** | Grado de parentesco civil | Distancia familiar |
| **Inbreeding risk** | Coeficiente de consanguinidad | Depresión endogámica |
| **Generation index** | Número de generación | Distancia al fundador |
| **Extinct lineage** | Linaje extinto | Fin de una dinastía |
| **Age at death** | Edad al fallecer | Estadística demográfica |
| **Lineage success** | Éxito reproductivo | Fitness evolutivo |

---

## 📁 Archivos que lo componen

| Archivo | Clase principal | Responsabilidad |
|---------|-----------------|-----------------|
| `systems/genealogy/genealogy_system.py` | `HistoricalPersonNode`, `Lineage`, `GenealogySystem` | Registro histórico y motor |
| `systems/genealogy/ancestry_queries.py` | `AncestryQueries` | Fachada de consultas |

---

## 🔄 Flujo de ejecución completo

```
┌─────────────────────────────────────────────────────────────────┐
│              CICLO DE VIDA GENEALÓGICO                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 1: SINCRONIZACIÓN DE CENSO (Altas)                         │
│                                                                 │
│ Para cada person en state.get_all_persons():                    │
│  └── Si entity_id NOT en registry:                              │
│      └── _sync_new_person(person):                              │
│          ├── Crear HistoricalPersonNode                         │
│          ├── Calcular birth_tick (robusto)                      │
│          ├── Capturar rasgos fenotípicos (longevity, etc.)      │
│          ├── Vincular padres biológicos (con reciprocidad)      │
│          ├── Vincular padres adoptivos (con reciprocidad)       │
│          ├── Asignar generation_index (max padres + 1)          │
│          └── Asignar/crear Lineage                              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 2: PROCESAMIENTO DE ADOPCIONES                             │
│                                                                 │
│ Para cada adoption en pending.adoptions:                        │
│  ├── Obtener child_node                                         │
│  ├── Para cada parent (parent_a, parent_b):                     │
│  │   ├── Añadir child_id a adoptive_parents (sin duplicados)    │
│  │   ├── Añadir parent_id a adoptive_children (sin duplicados)  │
│  │   └── Heredar lineage_id del padre adoptivo                  │
│  └── Añadir child a lineage.members                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 3: PROCESAMIENTO DE MATRIMONIOS                            │
│                                                                 │
│ Para cada (person_a_id, person_b_id) en pending.marriages:      │
│  ├── Si ambos en registry:                                      │
│  │   ├── Añadir person_b a spouses de A (sin duplicados)        │
│  │   └── Añadir person_a a spouses de B (sin duplicados)        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 4: PROCESAMIENTO DE DIVORCIOS                              │
│                                                                 │
│ Para cada divorce en pending.divorces:                          │
│  └── Si es tupla de 2 elementos y ambos en registry:            │
│      ├── Eliminar person_b de spouses de A                      │
│      └── Eliminar person_a de spouses de B                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 5: PROCESAMIENTO DE FALLECIMIENTOS (Bajas)                 │
│                                                                 │
│ Para cada dead_id en pending.deaths:                            │
│  └── Si en registry y is_alive:                                 │
│      ├── node.is_alive = False                                  │
│      ├── node.death_tick = total_days_elapsed                   │
│      └── node.age_at_death = person.age (o fallback)            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE 6: MANTENIMIENTO DE LINAJES Y EXTINCIONES                  │
│                                                                 │
│ Para cada lineage en lineages:                                  │
│  └── Si NOT is_extinct:                                         │
│      ├── alive_members = any(m.is_alive for m in members)       │
│      └── Si NO hay miembros vivos:                              │
│          ├── lineage.is_extinct = True                          │
│          └── Log: "📜 Evento Histórico: Linaje X extinguido"     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes del Sistema

---

### 1. HistoricalPersonNode - Nodo Histórico

**📁 Archivo**: `systems/genealogy/genealogy_system.py`
**🌍 Equivalencia real**: La ficha biográfica completa de una persona: datos vitales, relaciones, y rasgos hereditarios.

#### Atributos

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `entity_id` | `int` | Identificador único |
| `name` | `str` | Nombre del agente |
| `gender` | `str` | Género |
| `birth_tick` | `float` | Día de nacimiento |
| `death_tick` | `Optional[float]` | Día de muerte (None si vivo) |
| `age_at_death` | `Optional[float]` | Edad exacta al morir |
| `is_alive` | `bool` | Estado vital |
| `biological_parents` | `List[int]` | IDs de padres biológicos |
| `adoptive_parents` | `List[int]` | IDs de padres adoptivos |
| `children` | `List[int]` | IDs de hijos biológicos |
| `adoptive_children` | `List[int]` | IDs de hijos adoptivos |
| `spouses` | `List[int]` | IDs de cónyuges actuales |
| `lineage_id` | `Optional[int]` | ID del linaje al que pertenece |
| `generation_index` | `int` | Distancia al fundador |
| `longevity` | `float` | Rasgo de longevidad (snapshot) |
| `sociability` | `float` | Rasgo de sociabilidad (snapshot) |
| `temperament` | `float` | Rasgo de temperamento (snapshot) |

#### Consideraciones

- **Inmutable tras la muerte**: solo `is_alive`, `death_tick`, `age_at_death` cambian
- **Grafo bidireccional**: cada relación se refleja en ambos nodos
- **Snapshot fenotípico**: los rasgos se capturan al crear el nodo (para análisis post-mortem)
- **Persistencia**: los nodos de fallecidos permanecen en memoria indefinidamente

---

### 2. Lineage - Linaje

**📁 Archivo**: `systems/genealogy/genealogy_system.py`
**🌍 Equivalencia real**: Una familia/clan/dinastía con un fundador común.

#### Atributos

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `lineage_id` | `int` | Identificador único |
| `founder_id` | `int` | ID del fundador original |
| `members` | `Set[int]` | Todos los miembros (vivos y muertos) |
| `is_extinct` | `bool` | Si todos los miembros han muerto |

#### Ciclo de vida

1. **Creación**: cuando un agente no tiene padres (fundador o primer registro)
2. **Expansión**: cuando nacen hijos o se adoptan
3. **Extinción**: cuando el último miembro muere

---

### 3. GenealogySystem - Motor Genealógico

**📁 Archivo**: `systems/genealogy/genealogy_system.py`
**🌍 Equivalencia real**: El registro civil nacional: mantiene todas las relaciones familiares y detecta eventos macro-históricos.

#### Atributos

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `registry` | `Dict[int, HistoricalPersonNode]` | Todos los agentes (vivos y muertos) |
| `lineages` | `Dict[int, Lineage]` | Todos los linajes |
| `_next_lineage_id` | `int` | Contador para IDs únicos |
| `total_days_elapsed` | `float` | Tiempo total simulado |

#### Flujo interno de `process()`

```
process(state, pending, delta_days, context)
    │
    ├── total_days_elapsed += delta_days
    │
    ├── 1. Altas: sincronizar nuevos agentes
    ├── 2. Adopciones: vincular padres adoptivos
    ├── 3. Matrimonios: registrar cónyuges
    ├── 4. Divorcios: eliminar cónyuges
    ├── 5. Fallecimientos: marcar como muertos
    └── 6. Extinciones: detectar linajes extintos
```

#### Sincronización de nuevos agentes

```python
def _sync_new_person(self, person):
    # Calcular birth_tick robusto
    person_age = getattr(person, 'age', 0.0)
    if person_age <= 1.0:
        birth_tick = self.total_days_elapsed  # Nació este tick
    else:
        birth_tick = max(0.0, self.total_days_elapsed - person_age)  # Fundador
    
    # Crear nodo
    node = HistoricalPersonNode(
        entity_id=person.entity_id,
        name=person.name,
        gender=person.gender,
        birth_tick=birth_tick
    )
    
    # Capturar rasgos fenotípicos
    if hasattr(person, 'genome'):
        node.longevity = person.genome.get_trait_value("longevity") or 1.0
        node.sociability = person.genome.get_trait_value("sociability") or 0.5
        node.temperament = person.genome.get_trait_value("temperament") or 0.5
    
    # Vincular padres biológicos (con reciprocidad)
    father_id = getattr(person, 'father_id', None)
    mother_id = getattr(person, 'mother_id', None)
    
    if father_id is not None and father_id in self.registry:
        node.biological_parents.append(father_id)
        if person.entity_id not in self.registry[father_id].children:
            self.registry[father_id].children.append(person.entity_id)
    
    if mother_id is not None and mother_id in self.registry:
        node.biological_parents.append(mother_id)
        if person.entity_id not in self.registry[mother_id].children:
            self.registry[mother_id].children.append(person.entity_id)
    
    # Asignar generación y linaje
    all_parents = node.biological_parents + node.adoptive_parents
    if not all_parents:
        node.generation_index = 0
        lineage_id = self._next_lineage_id
        self._next_lineage_id += 1
        self.lineages[lineage_id] = Lineage(lineage_id, person.entity_id)
        node.lineage_id = lineage_id
    else:
        parent_gens = [self.registry[p_id].generation_index for p_id in all_parents if p_id in self.registry]
        node.generation_index = max(parent_gens) + 1 if parent_gens else 1
        
        # Heredar linaje del primer padre válido
        assigned_lineage = None
        for p_id in all_parents:
            if p_id in self.registry and self.registry[p_id].lineage_id is not None:
                assigned_lineage = self.registry[p_id].lineage_id
                break
        
        if assigned_lineage is None:
            assigned_lineage = self._next_lineage_id
            self._next_lineage_id += 1
            self.lineages[assigned_lineage] = Lineage(assigned_lineage, person.entity_id)
        
        node.lineage_id = assigned_lineage
        self.lineages[node.lineage_id].members.add(person.entity_id)
    
    self.registry[person.entity_id] = node
```

#### Cálculo de grado de parentesco (BFS)

```python
def get_degree_of_kinship(self, id_a, id_b):
    if id_a not in self.registry or id_b not in self.registry:
        return -1
    if id_a == id_b:
        return 0
    
    visited = {id_a}
    queue = deque([(id_a, 0)])
    
    while queue:
        current_id, dist = queue.popleft()
        if current_id == id_b:
            return dist
        
        node = self.registry[current_id]
        relatives = (node.biological_parents + node.adoptive_parents + 
                     node.children + node.adoptive_children)
        
        for relative_id in relatives:
            if relative_id not in visited:
                visited.add(relative_id)
                queue.append((relative_id, dist + 1))
    
    return -1  # No relacionados
```

**Interpretación**:
- Grado 0 = misma persona
- Grado 1 = padre/hijo
- Grado 2 = abuelo/nieto o hermanos
- Grado 3 = tío/sobrino o bisabuelo/bisnieto
- Grado 4 = primos hermanos
- `-1` = no relacionados

#### Detección de consanguinidad

```python
def is_consanguineous(self, id_a, id_b, limit):
    degree = self.get_degree_of_kinship(id_a, id_b)
    if degree == -1:
        return False
    return degree <= limit
```

#### Descendientes completos

```python
def get_all_descendants(self, entity_id):
    if entity_id not in self.registry:
        return set()
    
    descendants = set()
    queue = deque(self.registry[entity_id].children)
    
    while queue:
        current = queue.popleft()
        if current not in descendants:
            descendants.add(current)
            if current in self.registry:
                queue.extend(self.registry[current].children)
    
    return descendants
```

#### Descendientes adoptivos

```python
def get_adoptive_descendants(self, entity_id):
    if entity_id not in self.registry:
        return set()
    
    descendants = set()
    queue = deque(self.registry[entity_id].adoptive_children)
    
    while queue:
        current = queue.popleft()
        if current not in descendants:
            descendants.add(current)
            if current in self.registry:
                queue.extend(self.registry[current].children)
                queue.extend(self.registry[current].adoptive_children)
    
    return descendants
```

---

### 4. AncestryQueries - Fachada de Consultas

**📁 Archivo**: `systems/genealogy/ancestry_queries.py`
**🌍 Equivalencia real**: Oficina de consultas genealógicas: API limpia para análisis complejos sin exponer el grafo.

#### Métodos principales

| Método | Descripción | Retorno |
|--------|-------------|---------|
| `is_forbidden_marriage(id_a, id_b)` | ¿Matrimonio prohibido por consanguinidad? | `bool` |
| `get_kinship_degree(id_a, id_b)` | Grado exacto de parentesco | `int` |
| `calculate_lineage_success(founder_id, vivos_ids)` | Éxito reproductivo | `Dict` |
| `get_lineage_statistics(lineage_id)` | Estadísticas del linaje | `Dict` |
| `analyze_inbreeding_risk(entity_id)` | Coeficiente de endogamia | `float` [0, 1] |
| `get_all_ancestors_recursive_safe(entity_id, max_depth)` | Ancestros con límite | `Set[int]` |

#### Validación de matrimonio

```python
def is_forbidden_marriage(self, id_a, id_b):
    limit = self._genealogy.config.genealogy.consanguinity_limit
    return self._genealogy.is_consanguineous(id_a, id_b, limit=limit)
```

#### Éxito reproductivo (para EvolutionEngine)

```python
def calculate_lineage_success(self, founder_id, vivos_ids):
    descendants = self._genealogy.get_all_descendants(founder_id)
    adoptive_descendants = self._genealogy.get_adoptive_descendants(founder_id)
    all_descendants = descendants | adoptive_descendants
    descendencia_viva = len([d for d in all_descendants if d in vivos_ids])
    
    return {
        "total_descendencia_historica": len(all_descendants),
        "total_descendencia_viva": descendencia_viva,
        "tasa_supervivencia": descendencia_viva / max(1, len(all_descendants))
    }
```

#### Estadísticas de linaje

```python
def get_lineage_statistics(self, lineage_id):
    if lineage_id not in self._genealogy.lineages:
        return {"error": "Linaje no encontrado"}
    
    lineage = self._genealogy.lineages[lineage_id]
    miembros_ids = lineage.members
    
    vivos = 0
    muertos = 0
    edades_al_morir = []
    generaciones_alcanzadas = set()
    
    for m_id in miembros_ids:
        if m_id in self._genealogy.registry:
            node = self._genealogy.registry[m_id]
            generaciones_alcanzadas.add(node.generation_index)
            
            if node.is_alive:
                vivos += 1
            else:
                muertos += 1
                if node.age_at_death is not None:
                    edades_al_morir.append(node.age_at_death)
                elif node.death_tick is not None and node.birth_tick is not None:
                    edades_al_morir.append(node.death_tick - node.birth_tick)
    
    avg_lifespan = sum(edades_al_morir) / len(edades_al_morir) if edades_al_morir else 0.0
    
    return {
        "lineage_id": lineage_id,
        "founder_id": lineage.founder_id,
        "is_extinct": lineage.is_extinct,
        "total_members": len(miembros_ids),
        "alive_members": vivos,
        "deceased_members": muertos,
        "generations_span": max(generaciones_alcanzadas) if generaciones_alcanzadas else 0,
        "average_historical_lifespan_days": avg_lifespan
    }
```

#### Análisis de endogamia (inbreeding risk)

```python
def analyze_inbreeding_risk(self, entity_id):
    if entity_id not in self._genealogy.registry:
        return 0.0
    
    node = self._genealogy.registry[entity_id]
    if len(node.biological_parents) != 2:
        return 0.0
    
    padre_id, madre_id = node.biological_parents
    
    # Obtener todos los ancestros de cada padre
    ancestros_padre = self._get_all_ancestors(padre_id)
    ancestros_madre = self._get_all_ancestors(madre_id)
    
    if not ancestros_padre or not ancestros_madre:
        return 0.0
    
    # Coeficiente = solapamiento / unión
    solapamiento = ancestros_padre.intersection(ancestros_madre)
    total_unicos = ancestros_padre.union(ancestros_madre)
    
    return len(solapamiento) / max(1, len(total_unicos))
```

**Interpretación**:
- `0.0` = sin endogamia (padres no relacionados)
- `0.125` = primos hermanos (12.5% de genes compartidos)
- `0.25` = medio hermanos o tío-sobrina
- `0.5` = hermanos completos o padre-hija
- `1.0` = clonación (mismos padres)

#### Obtención de ancestros (BFS iterativo)

```python
def _get_all_ancestors(self, entity_id):
    ancestors = set()
    queue = deque([entity_id])
    visited = {entity_id}  # Protección contra ciclos
    
    while queue:
        current_id = queue.popleft()
        
        if current_id not in self._genealogy.registry:
            continue
        
        node = self._genealogy.registry[current_id]
        
        # Solo padres biológicos (no adoptivos) para análisis genético
        for parent_id in node.biological_parents:
            if parent_id not in visited:
                visited.add(parent_id)
                ancestors.add(parent_id)
                queue.append(parent_id)
    
    return ancestors
```

#### Versión recursiva con límite de profundidad

```python
def get_all_ancestors_recursive_safe(self, entity_id, max_depth=10):
    return self._get_ancestors_recursive(entity_id, max_depth, set())

def _get_ancestors_recursive(self, entity_id, depth, visited):
    if depth <= 0 or entity_id in visited:
        return set()
    
    visited.add(entity_id)
    ancestors = set()
    
    if entity_id not in self._genealogy.registry:
        return ancestors
    
    node = self._genealogy.registry[entity_id]
    
    for parent_id in node.biological_parents:
        ancestors.add(parent_id)
        ancestors.update(self._get_ancestors_recursive(parent_id, depth - 1, visited))
    
    return ancestors
```

---

## 🔗 Interacción entre componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                  GenealogySystem                                │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ registry: Dict[int, HistoricalPersonNode]                │  │
│  │   - Todos los agentes (vivos y muertos)                  │  │
│  │   - Relaciones bidireccionales                           │  │
│  │   - Snapshot fenotípico                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ lineages: Dict[int, Lineage]                             │  │
│  │   - founder_id, members, is_extinct                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Métodos principales:                                           │
│    ├── process() → sincroniza con pending                       │
│    ├── get_degree_of_kinship() → BFS                            │
│    ├── is_consanguineous() → validación                         │
│    ├── get_all_descendants() → BFS                              │
│    └── get_lineage_members() → consulta directa                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │ usado por
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  AncestryQueries (fachada)                      │
│                                                                  │
│  Métodos de alto nivel:                                         │
│    ├── is_forbidden_marriage() → MarriageSystem                 │
│    ├── calculate_lineage_success() → EvolutionEngine            │
│    ├── get_lineage_statistics() → analytics                     │
│    └── analyze_inbreeding_risk() → MortalitySystem              │
└──────────────────────────┬──────────────────────────────────────┘
                           │ usado por
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐
│ Marriage     │  │ Adoption     │  │ Mortality            │
│ System       │  │ System       │  │ System               │
│ (doc 06)     │  │ (doc 06)     │  │ (doc 10)             │
│              │  │              │  │                      │
│ Valida       │  │ Prioriza     │  │ Penaliza             │
│ consanguini- │  │ parientes    │  │ endogamia en         │
│ dad antes    │  │ en adopcio-  │  │ menores de 1 año     │
│ de casar     │  │ nes          │  │                      │
└──────────────┘  └──────────────┘  └──────────────────────┘
```

---

## ⚙️ Configuración relevante

```python
# GenealogyConfig (en SimulationConfig)
config.genealogy.consanguinity_limit = 3  # Grado máximo permitido para matrimonio
```

### Interpretación de `consanguinity_limit`

| Límite | Permite | Prohíbe |
|--------|---------|---------|
| `1` | Solo no relacionados | Padres/hijos |
| `2` | Primos lejanos | Hermanos, abuelos/nietos |
| `3` (default) | Primos segundos | Primos hermanos, tíos/sobrinos |
| `4` | Primos hermanos | Tíos/sobrinos, bisabuelos |

---

## 🧪 Tests del sistema

| Archivo | Cobertura |
|---------|-----------|
| `tests/unit/test_genealogy_system.py` | Registro, sincronización, extinciones |
| `tests/unit/test_ancestry_queries.py` | Consultas, inbreeding, estadísticas |
| `tests/integration/test_regression_bugs.py` | Bug de duplicados en children/spouses |

---

## 📝 Ejemplos completos

### Ejemplo 1: Registro de una familia completa

```python
# 1. Nacen los fundadores (sin padres)
state.add_person(Person(entity_id=101, name="Adam", age=6570))  # 18 años
state.add_person(Person(entity_id=102, name="Eve", age=6570))

# GenealogySystem.process():
# - Crea HistoricalPersonNode para 101 y 102
# - generation_index = 0 (fundadores)
# - Crea Lineage(1, founder=101) para Adam
# - Crea Lineage(2, founder=102) para Eve

# 2. Se casan
pending.marriages = {101: 102}
# GenealogySystem: node_101.spouses = [102], node_102.spouses = [101]

# 3. Nace su hijo
state.add_person(Person(entity_id=201, name="Cain", age=0, 
                        father_id=101, mother_id=102))

# GenealogySystem._sync_new_person():
# - birth_tick = total_days_elapsed (nació hoy)
# - biological_parents = [101, 102]
# - node_101.children.append(201)
# - node_102.children.append(201)
# - generation_index = max(0, 0) + 1 = 1
# - Hereda Lineage(1) de Adam (primer padre)
# - Lineage(1).members.add(201)
```

### Ejemplo 2: Detección de matrimonio consanguíneo

```python
# Dos primos hermanos quieren casarse
# Árbol:
#   Abuelo (1)
#     ├── Padre_A (10)
#     │     └── Primo_A (100)
#     └── Padre_B (20)
#           └── Primo_B (200)

# Consulta:
queries = AncestryQueries(genealogy_system)
degree = queries.get_kinship_degree(100, 200)
# BFS: 100 → 10 → 1 → 20 → 200 = grado 4

# Validación:
forbidden = queries.is_forbidden_marriage(100, 200)
# consanguinity_limit = 3
# degree (4) > limit (3) → False (permitido)

# Si fueran hermanos (grado 2):
forbidden = queries.is_forbidden_marriage(100, 101)  # hermano
# degree (2) <= limit (3) → True (prohibido)
```

### Ejemplo 3: Análisis de endogamia

```python
# Hijo de primos hermanos
# Árbol:
#   Bisabuelo (1)
#     ├── Abuelo_A (10)
#     │     └── Padre (100)
#     └── Abuelo_B (20)
#           └── Madre (200)
# Padre (100) + Madre (200) → Hijo (300)

# Análisis:
risk = queries.analyze_inbreeding_risk(300)

# Ancestros del padre: {100, 10, 1}
# Ancestros de la madre: {200, 20, 1}
# Solapamiento: {1} (bisabuelo común)
# Unión: {100, 10, 1, 200, 20}
# Coeficiente: 1 / 5 = 0.2 (20% de endogamia)
```

### Ejemplo 4: Estadísticas de linaje

```python
# Linaje con 10 miembros: 7 vivos, 3 muertos
stats = queries.get_lineage_statistics(lineage_id=1)

# Resultado:
{
    "lineage_id": 1,
    "founder_id": 101,
    "is_extinct": False,
    "total_members": 10,
    "alive_members": 7,
    "deceased_members": 3,
    "generations_span": 3,  # 4 generaciones (0, 1, 2, 3)
    "average_historical_lifespan_days": 25550.0  # ~70 años
}
```

### Ejemplo 5: Éxito reproductivo para EvolutionEngine

```python
# Fundador con 20 descendientes históricos, 15 vivos
vivos_ids = {p.entity_id for p in state.get_all_persons()}
success = queries.calculate_lineage_success(founder_id=101, vivos_ids=vivos_ids)

# Resultado:
{
    "total_descendencia_historica": 20,
    "total_descendencia_viva": 15,
    "tasa_supervivencia": 0.75  # 75% de supervivencia
}

# EvolutionEngine usa esto para:
# - Seleccionar linajes exitosos para análisis
# - Detectar presión selectiva
# - Generar reportes macroevolutivos
```

### Ejemplo 6: Detección de extinción de linaje

```python
# Linaje 5 tiene 3 miembros, todos mueren este tick
pending.deaths = {501: "reason", 502: "reason", 503: "reason"}

# GenealogySystem.process():
# - Marca los 3 como is_alive = False
# - En fase 6:
#   lineage = lineages[5]
#   alive_members = any(registry[m].is_alive for m in lineage.members)
#   # Todos False → alive_members = False
#   lineage.is_extinct = True
#   log: "📜 Evento Histórico: El linaje 5 (Fundador 500) se ha extinguido."
```

### Ejemplo 7: Adopción y herencia de linaje

```python
# Huérfano 300 es adoptado por pareja (101, 102) del linaje 1
pending.adoptions = [{
    "child_id": 300,
    "parent_a": 101,
    "parent_b": 102,
    "is_single_parent": False
}]

# GenealogySystem.process():
# - node_300.adoptive_parents = [101, 102]
# - node_101.adoptive_children.append(300)
# - node_102.adoptive_children.append(300)
# - node_300.lineage_id = 1 (hereda de parent_a)
# - lineages[1].members.add(300)
```

---

## 🚨 Consideraciones y limitaciones

### Principios fundamentales
- **Persistencia post-mortem**: los fallecidos siguen en el grafo
- **Grafo bidireccional**: cada relación se refleja en ambos nodos
- **Prevención de duplicados**: checks antes de añadir a listas
- **BFS iterativo**: evita recursión infinita en ciclos
- **Linajes emergentes**: se crean automáticamente para fundadores

### Arquitectura

```
PENDING (eventos del tick)
   ↓
GenealogySystem.process()
   ↓
├── Altas (nuevos agentes)
├── Adopciones
├── Matrimonios
├── Divorcios
├── Fallecimientos
└── Extinciones
   ↓
REGISTRY (grafo histórico)
   ↓
AncestryQueries (API de consultas)
   ↓
Sistemas consumidores (Marriage, Adoption, Mortality, Evolution)
```

### Optimizaciones de rendimiento

| Optimización | Descripción |
|--------------|-------------|
| BFS iterativo | Evita stack overflow en árboles profundos |
| Conjunto de visitados | Previene ciclos infinitos |
| Early returns | Skip si ID no en registry |
| Snapshots fenotípicos | No consulta genoma post-mortem |
| Lineage.members como Set | O(1) para membership checks |

### Limitaciones
- No hay "olvido" histórico: el grafo crece indefinidamente
- No hay poda de linajes extintos antiguos
- No hay análisis de haplogrupos o ADN mitocondrial
- No hay migración entre linajes (solo herencia del primer padre)
- El coeficiente de endogamia es simplificado (no usa coeficiente de Wright)
- No hay distinción entre consanguinidad biológica y civil

### Errores comunes
- ❌ Asumir que `biological_parents` siempre tiene 2 elementos (puede tener 0, 1 o 2)
- ❌ Iterar sobre `pending.marriages` como lista (es Dict)
- ❌ No verificar `is_alive` antes de procesar fallecimientos
- ❌ Usar recursión sin límite de profundidad (stack overflow)
- ❌ Olvidar reciprocidad al vincular relaciones
- ❌ Calcular `age_at_death` desde ticks (usar `person.age` explícito)

---

## 🎓 Conceptos clave

### ¿Por qué persistir agentes fallecidos?

**Principio de memoria histórica**:
- Los muertos siguen siendo parte del árbol genealógico
- Permiten análisis longitudinales (esperanza de vida por generación)
- Habilitan detección de endogamia en uniones futuras
- Sin persistencia, no habría genealogía real

### ¿Por qué grafo bidireccional?

**Principio de integridad referencial**:
- Si A es padre de B, entonces B es hijo de A
- Facilita consultas en ambas direcciones
- Evita inconsistencias (un padre sin hijo registrado)
- Permite BFS en cualquier dirección

### ¿Por qué BFS en lugar de DFS?

**Principio de distancia mínima**:
- BFS encuentra el camino más corto primero
- El grado de parentesco es la distancia mínima
- DFS podría encontrar caminos largos primero
- BFS es más eficiente para grafos anchos

### ¿Por qué coeficiente de endogamia simplificado?

**Principio de pragmática**:
- El coeficiente de Wright real es computacionalmente costoso
- Requiere rastrear todas las rutas entre ancestros comunes
- Nuestra aproximación (solapamiento/unión) es O(n)
- Suficiente para detectar casos graves de endogamia

### ¿Por qué linajes emergentes?

**Principio de auto-organización**:
- Los fundadores inician linajes automáticamente
- Los hijos heredan el linaje del primer padre
- No requiere configuración manual
- Permite análisis de dinastías sin intervención

### ¿Por qué detectar extinciones?

**Principio de eventos macro-históricos**:
- La extinción de un linaje es un evento significativo
- Puede indicar presión selectiva extrema
- Útil para reportes evolutivos
- Marca el fin de una rama genealógica

---

## 📊 Métricas del sistema

| Métrica | Valor |
|---------|-------|
| Archivos del sistema | 2 |
| Clases principales | 4 |
| Atributos de HistoricalPersonNode | 16 |
| Métodos de GenealogySystem | 8 |
| Métodos de AncestryQueries | 6 |
| Tests cubriendo genealogía | ~20 |

---

## 🔮 Futuras extensiones

### Planificadas
- [ ] Poda de linajes extintos antiguos (liberar memoria)
- [ ] Coeficiente de Wright real (más preciso)
- [ ] Análisis de haplogrupos (ADN mitocondrial, cromosoma Y)
- [ ] Migración entre linajes (cambio de apellido)

### Posibles
- [ ] Apellidos y herencia de nombres
- [ ] Heráldica y escudos familiares
- [ ] Títulos nobiliarios (duque, conde, barón)
- [ ] Herencia de propiedades (tierras, riquezas)
- [ ] Feudos y vasallaje
- [ ] Dinastías reinantes
- [ ] Árboles genealógicos visuales (exportación a Graphviz)
- [ ] Análisis de cuellos de botella poblacionales
- [ ] Efecto fundador (deriva genética en linajes pequeños)
- [ ] Genealogía mítica (ancestros legendarios)

---

*Documento: 12_GENEALOGIA.md*
*Versión: 1.0*