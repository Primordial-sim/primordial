# 21 - Sistema de Energía

## Resumen

El Sistema de Energía gestiona el metabolismo energético de todos los organismos del simulador. La energía es el recurso fundamental de la vida: sin energía, no hay movimiento, reproducción ni supervivencia.

## Filosofía

```
La energía fluye a través del ecosistema:
  Sol → Plantas (fotosíntesis) → Herbívoros (comen plantas) → Carnívoros (cazan)

Cada organismo:
  - Genera energía según su dieta y capacidades
  - Gasta energía por metabolismo, movimiento y reproducción
  - Muere si no puede mantener su balance energético
```

## Componentes Principales

### 1. Atributos de Energía en Person

Cada agente tiene tres atributos de energía:

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `_max_energy` | `float` | Nivel máximo de energía (100.0 por defecto) |
| `_energy` | `float` | Nivel actual de energía (empieza en 100.0) |
| `_starvation_days` | `float` | Días que lleva sin energía |

### 2. Propiedades de Energía

| Propiedad | Retorno | Descripción |
|-----------|---------|-------------|
| `energy` | `float` | Nivel de energía actual |
| `max_energy` | `float` | Nivel máximo de energía |
| `energy_ratio` | `float` | Proporción de energía (0.0 a 1.0) |
| `is_starving` | `bool` | True si energía <= 0 |
| `starvation_days` | `float` | Días sin energía |

### 3. Métodos de Energía

| Método | Descripción |
|--------|-------------|
| `add_energy(amount)` | Añade energía (sin exceder máximo). Resetea inanición si energía > 0 |
| `spend_energy(amount)` | Gasta energía. Retorna True si se pudo gastar toda |
| `advance_starvation(delta_days)` | Avanza contador de inanición si energía = 0 |
| `set_energy(value)` | Establece energía directamente (con clampeo) |

## Flujo de Energía

```
┌─────────────────────────────────────────────────────────────┐
│                     FLUJO DE ENERGÍA                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ☀️ SOL                                                     │
│    │                                                        │
│    ▼                                                        │
│  🌱 PLANTAS (Fotosíntesis)                                  │
│    │  Generan energía del sol                               │
│    │  Factor: luz, agua, temperatura                        │
│    ▼                                                        │
│  🦌 HERBÍVOROS (Comen plantas)                              │
│    │  Obtienen energía al comer plantas                     │
│    │  Transferencia vía EcologicalRelationshipSystem        │
│    ▼                                                        │
│  🐺 CARNÍVOROS (Cazan presas)                               │
│       Obtienen energía al cazar                             │
│       Transferencia vía EcologicalRelationshipSystem        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Fuentes de Energía

### 1. Fotosíntesis

Las plantas y organismos fotosintéticos generan energía del sol.

**Sistema**: `EnergySystem._calculate_photosynthesis()`

**Factores**:
- **Luz**: 80% de luz promedio (simplificado)
- **Agua**: Consultada del tile (0.3 si muy seco, 0.5 si inundado, 1.0 si adecuado)
- **Temperatura**: Consultada del tile (0.2 muy frío, 0.4 muy caliente, 1.0 óptima)

**Detección de organismos fotosintéticos**:
```python
# Por rasgo genético:
diet = person.genome.get_trait_value("diet")
if diet <= 0.1:  # PHOTOSYNTHETIC
    return True

# Por nombre de especie (fallback):
photosynthetic_species = ["grass", "tree", "shrub", "flower", "algae", ...]
```

**Parámetros**:
| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `photosynthesis_rate` | 5.0 | Energía/día en condiciones óptimas |

### 2. Herbivoría

Los herbívoros obtienen energía al comer plantas.

**Sistema**: `EcologicalRelationshipSystem`

**Mecanismo**: Cuando un herbívoro se encuentra con una planta y se ejecuta la relación HERBIVORY, el herbívoro gana energía.

**Transferencia**: `_apply_energy_change()` → `person.add_energy()`

### 3. Depredación

Los carnívoros obtienen energía al cazar presas.

**Sistema**: `EcologicalRelationshipSystem`

**Mecanismo**: Cuando un depredador se encuentra con una presa y se ejecuta la relación PREDATION, el depredador gana energía.

**Transferencia**: `_apply_energy_change()` → `person.add_energy()`

## Gastos de Energía

### 1. Metabolismo Basal

Todos los organismos gastan energía por mantenimiento.

**Sistema**: `EnergySystem._calculate_metabolic_cost()`

**Parámetros**:
| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `basal_metabolic_rate` | 0.1 | Energía/día en reposo |

**Modificadores**:
| Factor | Multiplicador | Condición |
|--------|---------------|-----------|
| Tamaño corporal | 0.5 - 2.0 | Basado en `body_size` del genoma |
| Embarazo | 1.3 | Si `is_pregnant` |
| Enfermedad | 1.2 | Si `is_sick` |
| Estrés alto | 1.15 | Si `stress > 0.7` |

### 2. Movimiento

Cada acción de moverse cuesta energía.

**Sistema**: `MovementResolver._apply_movement_energy_cost()`

**Parámetros**:
| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `energy_cost_per_action` | 0.2 | Energía por moverse 1 casilla |

**Modificadores**:
| Factor | Multiplicador | Condición |
|--------|---------------|-----------|
| Tamaño corporal | 0.5 - 2.0 | Basado en `body_size` del genoma |
| Volar | 1.3 | Si `can_fly` |
| Nadar | 1.1 | Si `can_swim` |

**Nota**: El movimiento es siempre 1 casilla por tick. No se calcula distancia física.

### 3. Reproducción

La reproducción requiere inversión energética.

**Sistema**: `ConceptionSystem`

**Parámetros**:
| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `energy_cost_per_offspring` | 10.0 | Energía por descendiente |
| `energy_cost_per_egg` | 5.0 | Energía por huevo |
| `minimum_energy_to_reproduce` | 20.0 | Energía mínima para reproducirse |

**Costes por tipo**:
| Tipo | Coste | Descripción |
|------|-------|-------------|
| Concepción (vivíparos) | `10 × camada × tamaño` | Preparar el embarazo |
| Puesta de huevos (ovíparos) | `5 × huevos × tamaño` | Producir cáscara y nutrientes |
| Asexual | `5 × descendientes × tamaño` | División celular |

**Restricción**: Si `energy < 20`, el agente no puede reproducirse.

## Inanición

Cuando un organismo se queda sin energía, entra en estado de inanición.

**Sistema**: `EnergySystem._check_starvation_death()`

**Parámetros**:
| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `starvation_death_threshold` | 30.0 | Días sin energía antes de riesgo alto |
| `starvation_damage_rate` | 0.05 | Probabilidad de muerte/día antes del umbral |

**Mecanismo**:
```
Días 0-30: Riesgo creciente
  probabilidad = (días / 30) × 0.05 × delta_days

Días 30+: Muerte casi segura
  probabilidad = 0.5 + (días_extra × 0.1)
```

**Resultado**: Si la tirada aleatoria supera la probabilidad, el agente muere con razón `"inanicion"`.

## Conexión con Emociones

El nivel de energía física se sincroniza con la emoción de energía.

**Sistema**: `EnergySystem._sync_energy_with_emotions()`

**Mecanismo**:
```python
# Cada tick:
target = person.energy_ratio  # 0.0 a 1.0
current = person.emotions["energy"]
delta = (target - current) * 0.2  # Transición suave (20%)
person.update_emotion("energy", delta)
```

**Impacto en otros sistemas**:
- **Fertilidad**: `ConceptionSystem` usa `_emotions["energy"]` como factor limitante
- **Inmunidad**: `Person.get_immunity()` reduce inmunidad si energía emocional es baja
- **Enfermedad**: `Person.infect()` reduce energía emocional al enfermarse

## Integración en el Pipeline

El sistema de energía se ejecuta en la **FASE 3: ECOLOGÍA** del `PhaseScheduler`:

```python
PhaseDefinition(
    name="ecology",
    systems=[
        EcologicalRelationshipSystem(),  # Relaciones entre especies
        EnergySystem(self.config),        # Metabolismo y energía
    ],
),
```

**Orden de ejecución**:
1. `EcologicalRelationshipSystem`: Detecta encuentros y aplica cambios de energía
2. `EnergySystem`: Aplica metabolismo, fotosíntesis, inanición y sincronización

## Estadísticas del Sistema

El `EnergySystem` mantiene estadísticas:

| Métrica | Descripción |
|---------|-------------|
| `total_energy_processed` | Total de organismos procesados |
| `total_starvation_deaths` | Total de muertes por inanición |
| `total_photosynthesis_events` | Total de eventos de fotosíntesis |

**Acceso**: `energy_system.get_summary()`

## Ejemplos de Uso

### Consultar energía de un agente
```python
if person.energy_ratio < 0.3:
    print(f"El agente {person.entity_id} tiene poca energía")
```

### Añadir energía (comer)
```python
person.add_energy(20.0)  # Ganar 20 de energía
```

### Gastar energía (acción costosa)
```python
success = person.spend_energy(15.0)
if not success:
    print("No tenía suficiente energía")
```

### Verificar inanición
```python
if person.is_starving:
    print(f"Lleva {person.starvation_days} días sin energía")
```

## Archivos Relacionados

| Archivo | Descripción |
|---------|-------------|
| `entities/person/person.py` | Atributos y métodos de energía en Person |
| `systems/energy/energy_system.py` | Sistema principal de energía |
| `systems/energy/__init__.py` | Módulo de energía |
| `systems/movement/movement_resolver.py` | Gasto de energía por movimiento |
| `systems/reproduction/conception_system.py` | Gasto de energía por reproducción |
| `systems/ecology/ecological_relationship_system.py` | Transferencia de energía por relaciones ecológicas |

## Notas de Diseño

1. **Valores conservadores**: Los parámetros actuales son conservadores (`basal_metabolic_rate = 0.1`) para no afectar significativamente la dinámica actual hasta que se implementen fuentes de comida más detalladas.

2. **Fotosíntesis simplificada**: Actualmente asume luz diurna promedio. En el futuro se puede consultar la hora del día, estación y nubosidad.

3. **Movimiento = 1 casilla**: El gasto de energía por movimiento es fijo por acción (1 casilla), no por distancia física. Las casillas son unidades lógicas de organización, no superficie.

4. **Transición suave de emociones**: La sincronización energía → emoción usa un factor de 0.2 para evitar cambios bruscos que podrían causar inestabilidad.