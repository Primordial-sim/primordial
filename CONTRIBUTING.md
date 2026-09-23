# Contributing to Primordial

¡Gracias por tu interés en contribuir a **Primordial**! Este proyecto es open source y agradecemos cualquier forma de contribución, desde reportes de bugs hasta nuevas funcionalidades.

## 🤝 Formas de contribuir

### 🐛 Reportar bugs

Si encuentras un error:

1. Busca en [Issues](https://github.com/primordial-sim/primordial/issues) para ver si ya fue reportado
2. Si no existe, crea un nuevo issue usando la plantilla **"Bug Report"**
3. Incluye:
   - Descripción clara del problema
   - Pasos para reproducirlo
   - Comportamiento esperado vs actual
   - Versión de Python y sistema operativo
   - Logs o capturas si aplica

### 💡 Proponer nuevas funcionalidades

¿Tienes una idea para mejorar Primordial?

1. Abre un issue usando la plantilla **"Feature Request"**
2. Describe:
   - El problema que resuelve
   - Tu solución propuesta
   - Alternativas consideradas
   - Ejemplos de uso

### 🔧 Enviar código (Pull Requests)

#### Antes de empezar

1. **Busca un issue existente** o crea uno nuevo para discutir la funcionalidad
2. **Comenta en el issue** que vas a trabajar en ello (evita duplicación de esfuerzos)
3. **Espera feedback** antes de implementar cambios grandes

#### Proceso de desarrollo

1. **Fork** el repositorio
2. **Crea una rama** desde `main`:
   ```bash
   git checkout -b feature/nombre-descriptivo
   git checkout -b fix/descripcion-del-bug
   ```
3. **Desarrolla** tu cambio:
   - Sigue el estilo de código existente
   - Añade tests si aplica
   - Actualiza documentación si es necesario
4. **Testea** localmente:
   ```bash
   python -m pytest tests/ --tb=short -q
   ```
5. **Commit** con mensajes descriptivos:
   ```bash
   git commit -m "Add grazing mechanism for herbivores"
   git commit -m "Fix energy calculation in predation events"
   ```
6. **Push** a tu fork:
   ```bash
   git push origin feature/nombre-descriptivo
   ```
7. **Abre un Pull Request** en GitHub

#### Requisitos del Pull Request

- ✅ Todos los tests pasan (`pytest`)
- ✅ Código sigue PEP 8
- ✅ Documentación actualizada si aplica
- ✅ Descripción clara de los cambios
- ✅ Referencia al issue que resuelve (ej: "Fixes #42")

#### Convenciones de código

- **Python**: 3.13+
- **Estilo**: PEP 8 (usamos type hints extensivamente)
- **Testing**: pytest con cobertura mínima del 80% para código nuevo
- **Documentación**: Docstrings en Google style
- **Imports**: Agrupados y ordenados (stdlib, third-party, local)

### 📚 Mejorar documentación

La documentación es tan importante como el código:

- Corrige errores tipográficos
- Añade ejemplos
- Mejora explicaciones confusas
- Traduce a otros idiomas

### 🧪 Añadir tests

Los tests son críticos para mantener la calidad:

- Tests unitarios para funciones nuevas
- Tests de integración para interacciones entre sistemas
- Tests de regresión para bugs corregidos

---

## 🏗️ Estructura del proyecto

```
primordial/
├── core/                    # Núcleo del motor
│   ├── engine/              # Motor de simulación
│   ├── genetics/            # Sistema genético
│   ├── taxonomy/            # Clasificación de especies
│   ├── state/               # Estado del mundo
│   └── config/              # Configuración
│
├── systems/                 # Sistemas de simulación
│   ├── ecology/             # Relaciones ecológicas
│   ├── energy/              # Sistema de energía
│   ├── movement/            # Movimiento
│   ├── relationships/       # Relaciones sociales
│   ├── reproduction/        # Reproducción
│   ├── mortality/           # Mortalidad
│   ├── diseases/            # Epidemiología
│   ├── environment/         # Biomas, estaciones
│   └── metrics/             # Métricas
│
├── entities/                # Entidades del mundo
├── tests/                   # Suite de tests
├── docs/                    # Documentación técnica
└── godot/                   # Frontend visual
```

---

## 🔄 Proceso de review

1. **Maintainers revisarán** tu PR en 1-7 días
2. **Feedback constructivo**: Pueden pedir cambios
3. **Aprobación**: Al menos 1 maintainer debe aprobar
4. **Merge**: Se hará squash merge a `main`

---

## ❓ Preguntas frecuentes

### ¿Puedo contribuir sin saber programar?

¡Sí! Puedes:
- Reportar bugs
- Proponer ideas
- Mejorar documentación
- Traducir
- Crear tutoriales
- Hacer testing

### ¿Qué pasa si mi PR no es aceptado?

A veces una propuesta no encaja con la visión del proyecto. No te desanimes:
- Pide feedback específico
- Considera alternativas
- Abre un issue para discutir antes de implementar

### ¿Cómo puedo convertirme en maintainer?

Los contributors activos y consistentes pueden ser invitados a ser maintainers. Esto incluye:
- Múltiples PRs aceptados
- Participación en reviews
- Ayuda a otros contribuidores
- Compromiso a largo plazo

---

## 📜 Licencia

Al contribuir, aceptas que tus contribuciones se licencien bajo la [MIT License](LICENSE) del proyecto.

---

## 🙏 Agradecimientos

Cada contribución, grande o pequeña, es valiosa. ¡Gracias por ayudar a hacer Primordial mejor!

---

<div align="center">

**¿Dudas? Abre un issue o únete a la discusión en GitHub**

</div>