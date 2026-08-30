# 16 - Sistema de Eventos

## 📋 Resumen

El **Sistema de Eventos** implementa el patrón **Publicación/Suscripción (Pub/Sub)** para desacoplar los sistemas lógicos de las salidas externas (logs, UI, métricas en tiempo real). Su objetivo es permitir que la simulación emita notificaciones sobre eventos importantes sin conocer quién las consume.

**Estado actual**: ⚠️ **Infraestructura implementada, sin suscriptores activos**

El `EventBus` está completamente funcional y los eventos de población se publican correctamente desde `WorldState`, pero **actualmente no existe ningún componente suscrito** que consuma estos eventos. Es una infraestructura preparada para integraciones futuras (UI en tiempo real, logging avanzado, métricas externas).

---

## 🎯 Responsabilidad

**Es responsable de:**
- Proporcionar el bus de eventos central (`EventBus`)
- Definir tipos de eventos para población, simulación y mundo
- Publicar eventos desde `WorldState` cuando ocurren nacimientos, muertes, matrimonios, divorcios y adopciones
- Desacoplar la lógica de simulación de las salidas externas

**NO es responsable de:**
- ❌ Procesar la lógica de los eventos (eso lo hacen los sistemas que los publican)
- ❌ Almacenar el estado del mundo (eso lo hace `WorldState`)
- ❌ Ejecutar lógica de juego (eso lo hacen los sistemas individuales)
- ❌ Ser un requisito para el funcionamiento de la simulación (es opcional)

---

## 🌍 Equivalencia con la vida real

| Concepto del sistema | Equivalencia en la vida real | Unidad |
|---------------------|-----------------------------|--------|
| **EventBus** | Sistema de anuncios públicos | Megafonía |
| **Event** | Notificación de suceso | Comunicado |
| **publish()** | Emitir un anuncio | Publicar |
| **subscribe()** | Registrarse para escuchar | Suscribirse |
| **Handler** | Receptor interesado | Oyente |
| **PersonBornEvent** | Registro de nacimiento | Acta de nacimiento |
| **PersonDiedEvent** | Certificado de defunción | Registro civil |
| **MarriageCreatedEvent** | Acta matrimonial | Registro civil |

---

## 📁 Archivos que lo componen

| Archivo | Estado | Tamaño | Descripción |
|---------|--------|--------|-------------|
| `events/event_bus.py` | ✅ Implementado | 1094 B | Bus de eventos (pub/sub) |
| `events/__init__.py` | ⚠️ Vacío | 0 B | Inicializador del paquete |

### Eventos de población

| Archivo | Estado | Tamaño | Uso |
|---------|--------|--------|-----|
| `events/population/person_born.py` | ✅ Implementado | 250 B | Publicado en `WorldState` |
| `events/population/person_died.py` | ✅ Implementado | 199 B | Publicado en `WorldState` |
| `events/population/marriage_created.py` | ✅ Implementado | 203 B | Publicado en `WorldState` |
| `events/population/divorce_occurred.py` | ✅ Implementado | 283 B | Publicado en `WorldState` |
| `events/population/adoption_completed.py` | ✅ Implementado | 736 B | Publicado en `WorldState` |
| `events/population/relationship_created.py` | ⚠️ Sin uso | 243 B | No publicado en ningún lugar |

### Eventos de simulación (PENDIENTES)

| Archivo | Estado | Tamaño | Descripción prevista |
|---------|--------|--------|---------------------|
| `events/simulation/simulation_started.py` | ❌ Vacío | 0 B | Inicio de simulación |
| `events/simulation/simulation_finished.py` | ❌ Vacío | 0 B | Fin de simulación |
| `events/simulation/simulation_paused.py` | ❌ Vacío | 0 B | Pausa de simulación |
| `events/simulation/simulation_resumed.py` | ❌ Vacío | 0 B | Reanudación de simulación |
| `events/simulation/simulation_collapsed.py` | ❌ Vacío | 0 B | Colapso de simulación |

### Eventos de mundo (PENDIENTES)

| Archivo | Estado | Tamaño | Descripción prevista |
|---------|--------|--------|---------------------|
| `events/world/movement_resolved.py` | ❌ Vacío | 0 B | Movimiento resuelto |
| `events/world/overcrowding_detected.py` | ❌ Vacío | 0 B | Superpoblación detectada |
| `events/world/stability_changed.py` | ❌ Vacío | 0 B | Cambio de estabilidad |

---

## 🔧 Componente principal: EventBus

**📁 Archivo**: `events/event_bus.py`
**🌍 Equivalencia real**: Una megafonía central donde cualquiera puede emitir un mensaje y cualquiera puede registrarse para escuchar ciertos tipos de mensajes.

### Implementación

```python
class EventBus:
    def __init__(self):
        # Diccionario: TipoDeEvento -> [lista_de_handlers]
        self._subscribers = {}

    def subscribe(self, event_type: type, handler: Callable) -> None:
        """Registra un handler para un tipo de evento específico."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    def publish(self, event: Any) -> None:
        """Emite un evento a todos los suscriptores interesados."""
        event_type = type(event)
        
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                handler(event)
```

### Características

- **Patrón Observer/Pub-Sub** implementado correctamente
- **Tipado por clase de evento**: cada tipo de evento tiene sus propios suscriptores
- **Thread-safe básico**: no usa locks, pero es suficiente para simulación single-thread
- **Sin dependencias externas**: solo usa `typing` de la librería estándar

---

## 🔄 Flujo de eventos actual

```
┌─────────────────────────────────────────────────────────────────┐
│                  WorldState.apply_commit()                      │
│                                                                  │
│  Durante el commit, se publican eventos según el tipo de cambio:│
│                                                                  │
│  ├── Muertes → PersonDiedEvent(entity_id, age, reason, tick)    │
│  ├── Nacimientos → PersonBornEvent(entity_id, parents, ...)     │
│  ├── Adopciones → AdoptionCompletedEvent(child, parents, ...)   │
│  ├── Divorcios → DivorceOccurredEvent(p_a, p_b, reason, tick)   │
│  └── Matrimonios → MarriageCreatedEvent(p_a, p_b, tick)         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
                    event_bus.publish(event)
                           │
                           ▼
              ┌────────────────────────────┐
              │      EventBus._subscribers │
              │                            │
              │  Actualmente: VACÍO ❌      │
              │  (no hay suscriptores)     │
              └────────────────────────────┘
                           │
                           ▼
                    (Nadie recibe los eventos)
```

**Estado actual**: Los eventos se publican correctamente, pero **no hay ningún suscriptor** que los consuma. Los eventos se emiten al vacío.

---

## 📝 Eventos publicados por WorldState

### `PersonDiedEvent` (línea 147)
```python
PersonDiedEvent(
    entity_id=entity_id,
    age=int(p.age),
    reason=reason,
    tick=current_tick
)
```

### `PersonBornEvent` (línea 229)
```python
PersonBornEvent(
    entity_id=child_id,
    mother_id=mother_id,
    father_id=father_id,
    tick=current_tick
)
```

### `AdoptionCompletedEvent` (línea 265)
```python
AdoptionCompletedEvent(
    child_id=child_id,
    parent_a=parent_a,
    parent_b=parent_b,
    is_single_parent=is_single_parent,
    tick=current_tick
)
```

### `DivorceOccurredEvent` (línea 307)
```python
DivorceOccurredEvent(
    p_a_id=p_a_id,
    p_b_id=p_b_id,
    reason="separacion_natural",
    tick=current_tick
)
```

### `MarriageCreatedEvent` (línea 323)
```python
MarriageCreatedEvent(
    p_a_id=p_a_id,
    p_b_id=p_b_id,
    tick=current_tick
)
```

---

## 🚀 Guía para futuros suscriptores

Para conectar el EventBus a un nuevo componente (UI, logger, métricas):

### Paso 1: Crear el EventBus y pasarlo al SimulationEngine

```python
from events.event_bus import EventBus

# En el launcher o punto de entrada
event_bus = EventBus()
engine = SimulationEngine.create_default(
    width=100,
    height=100,
    founding_population_size=50,
    event_bus=event_bus  # ← Pasar el EventBus aquí
)
```

### Paso 2: Crear un handler

```python
from events.population.person_born import PersonBornEvent
from events.population.person_died import PersonDiedEvent

def on_person_born(event: PersonBornEvent):
    print(f"🎂 Nació agente {event.entity_id} (tick {event.tick})")

def on_person_died(event: PersonDiedEvent):
    print(f"⚰️ Murió agente {event.entity_id}: {event.reason}")
```

### Paso 3: Suscribir los handlers

```python
event_bus.subscribe(PersonBornEvent, on_person_born)
event_bus.subscribe(PersonDiedEvent, on_person_died)

# Ahora los eventos serán entregados a los handlers
```

### Paso 4: Ejecutar la simulación

```python
engine.run()
# Los handlers se ejecutarán automáticamente cuando ocurran eventos
```

---

## 🔮 Casos de uso futuros

| Caso de uso | Evento útil | Implementación sugerida |
|-------------|-------------|------------------------|
| **UI en tiempo real (Godot)** | Todos los de población | WebSocket server → Godot |
| **Logging avanzado** | Todos | Handler que escribe a archivo |
| **Métricas externas** | Todos | Handler que envía a Prometheus/Grafana |
| **Análisis post-simulación** | Todos | Handler que acumula en memoria |
| **Alertas de superpoblación** | `OvercrowdingDetectedEvent` | Implementar el evento primero |
| **Control de simulación** | Eventos de simulación | Implementar los eventos primero |

---

## 🚨 Consideraciones y limitaciones

### Estado actual

| Aspecto | Estado |
|---------|--------|
| EventBus implementado | ✅ Sí |
| Eventos de población publicados | ✅ Sí |
| Suscriptores activos | ❌ Ninguno |
| Eventos de simulación implementados | ❌ No (archivos vacíos) |
| Eventos de mundo implementados | ❌ No (archivos vacíos) |

### Limitaciones conocidas

- **Sin suscriptores**: Los eventos se emiten pero nadie los consume actualmente
- **Sin thread-safety**: El EventBus no usa locks (suficiente para single-thread)
- **Sin persistencia**: Los eventos no se almacenan, solo se emiten en tiempo real
- **Sin eventos de simulación**: Los archivos están vacíos, no hay eventos para start/finish/pause
- **Sin eventos de mundo**: No hay eventos para superpoblación, movimiento, estabilidad

### Recomendaciones para el futuro

1. **Implementar eventos de simulación**: Para controlar el ciclo de vida desde la UI
2. **Implementar eventos de mundo**: Para alertas y visualización en tiempo real
3. **Crear un logger suscrito**: Para depuración y análisis post-simulación
4. **Integrar con Godot**: El proyecto ya tiene `godot/scripts/websocket_client.gd` preparado
5. **Añadir thread-safety**: Si se planea usar con múltiples hilos

---

## 📊 Métricas del sistema

| Métrica | Valor |
|---------|-------|
| Archivos totales | 15 |
| Archivos implementados | 6 |
| Archivos vacíos | 8 |
| Archivos sin uso | 1 |
| Eventos publicados activamente | 5 |
| Suscriptores activos | 0 |

---

## 🔮 Próximos pasos sugeridos

### Corto plazo (si se necesita pronto)
- [ ] Implementar un suscriptor de logging básico
- [ ] Documentar el formato de los eventos de población

### Medio plazo (para integración con UI)
- [ ] Implementar eventos de simulación (start/finish/pause)
- [ ] Crear un WebSocket server que publique eventos a Godot
- [ ] Implementar `OvercrowdingDetectedEvent` para alertas visuales

### Largo plazo (análisis avanzado)
- [ ] Implementar eventos de mundo para visualización
- [ ] Crear un sistema de replay basado en eventos
- [ ] Integrar con herramientas de análisis externas (Grafana, Prometheus)

---

*Documento: 16_EVENTOS.md*
*Versión: 1.0*
*Última actualización: Agosto 2026*