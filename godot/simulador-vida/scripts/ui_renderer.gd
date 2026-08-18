extends Control
## Dibuja la interfaz de usuario. NO captura eventos del ratón.
## Los botones se detectan desde websocket_client.gd.

# =============================================================================
# CONFIGURACIÓN GENERAL
# =============================================================================

const COLOR_HEALTHY: Color = Color(0.298, 0.686, 0.314)
const COLOR_SICK: Color = Color(0.957, 0.263, 0.212)
const COLOR_PREGNANT: Color = Color(1.0, 0.757, 0.027)
const COLOR_YOUNG: Color = Color(0.129, 0.588, 0.953)
const COLOR_SENIOR: Color = Color(0.620, 0.620, 0.620)
const BACKGROUND_COLOR: Color = Color(0.1, 0.1, 0.15)
const TOP_BAR_HEIGHT: float = 50.0
const LEGEND_POSITION: Vector2 = Vector2(10, 60)
const LEGEND_SPACING: float = 20.0

# Colores de los botones
const COLOR_BUTTON_ACTIVE: Color = Color(0.2, 0.6, 0.9)
const COLOR_BUTTON_INACTIVE: Color = Color(0.3, 0.3, 0.35)
const COLOR_BUTTON_HOVER: Color = Color(0.4, 0.4, 0.5)
const COLOR_BUTTON_PAUSED: Color = Color(0.9, 0.5, 0.2)

# =============================================================================
# CONFIGURACIÓN DEL INSPECTOR DE AGENTES
# =============================================================================

const INSPECTOR_WIDTH: float = 250.0
const INSPECTOR_PADDING: float = 10.0
const INSPECTOR_LINE_HEIGHT: float = 16.0
const INSPECTOR_BG_COLOR: Color = Color(0.12, 0.12, 0.18, 0.95)
const INSPECTOR_BORDER_COLOR: Color = Color(0.4, 0.4, 0.5)
const INSPECTOR_TITLE_COLOR: Color = Color(0.9, 0.9, 1.0)
const INSPECTOR_LABEL_COLOR: Color = Color(0.7, 0.7, 0.75)
const INSPECTOR_VALUE_COLOR: Color = Color(0.9, 0.9, 0.9)

# =============================================================================
# ESTADO
# =============================================================================

var _is_connected: bool = false
var _tick_count: int = 0
var _current_day: float = 0.0
var _agent_count: int = 0
var _stats: Dictionary = {}
var _overlapping_count: int = 0
var _unique_cells: int = 0

# Estado de controles
var _is_paused: bool = false
var _current_speed: float = 1.0

# Áreas de botones (para detección de clics externa)
var _button_areas: Array = []

# Estado del inspector de agentes
var _inspector_visible: bool = false
var _inspector_agent: Dictionary = {}

# Estado de especies (para leyenda)
var _species_counts: Dictionary = {}

# =============================================================================
# CICLO DE VIDA
# =============================================================================

func _ready() -> void:
    set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    mouse_filter = Control.MOUSE_FILTER_IGNORE

# =============================================================================
# API PÚBLICA
# =============================================================================

func update_connection_status(connected: bool) -> void:
    _is_connected = connected
    queue_redraw()

func update_tick_info(tick: int, day: float, agent_count: int) -> void:
    _tick_count = tick
    _current_day = day
    _agent_count = agent_count
    queue_redraw()

func update_stats(stats: Dictionary) -> void:
    _stats = stats
    queue_redraw()

func update_occupancy_info(overlapping: int, unique_cells: int) -> void:
    _overlapping_count = overlapping
    _unique_cells = unique_cells
    queue_redraw()

func update_control_state(is_paused: bool, speed: float) -> void:
    _is_paused = is_paused
    _current_speed = speed
    queue_redraw()

func update_species_counts(species_counts: Dictionary) -> void:
    """Actualiza el conteo de especies para la leyenda."""
    _species_counts = species_counts
    queue_redraw()

# =============================================================================
# API DEL INSPECTOR DE AGENTES
# =============================================================================

func show_agent_inspector(agent_data: Dictionary) -> void:
    _inspector_visible = true
    _inspector_agent = agent_data
    queue_redraw()

func hide_agent_inspector() -> void:
    _inspector_visible = false
    _inspector_agent = {}
    queue_redraw()

func is_inspector_visible() -> bool:
    return _inspector_visible

func update_selected_agent(agent_data: Dictionary) -> void:
    if _inspector_visible and int(agent_data.get("id", -1)) == int(_inspector_agent.get("id", -1)):
        _inspector_agent = agent_data
        queue_redraw()

# =============================================================================
# API PARA DETECCIÓN DE BOTONES (usada por websocket_client)
# =============================================================================

func get_button_at_position(pos: Vector2) -> Dictionary:
    """Verifica si una posición está sobre un botón."""
    for button_info in _button_areas:
        if button_info["rect"].has_point(pos):
            return {"action": button_info["action"], "speed": button_info["speed"]}
    return {}

func get_top_bar_height() -> float:
    return TOP_BAR_HEIGHT

# =============================================================================
# DIBUJADO
# =============================================================================

func _draw() -> void:
    var viewport_size: Vector2 = get_viewport_rect().size
    
    _button_areas.clear()
    
    # Barra superior
    draw_rect(
        Rect2(Vector2.ZERO, Vector2(viewport_size.x, TOP_BAR_HEIGHT)),
        Color(0.15, 0.15, 0.2, 0.95)
    )
    
    draw_line(
        Vector2(0, TOP_BAR_HEIGHT),
        Vector2(viewport_size.x, TOP_BAR_HEIGHT),
        Color(0.3, 0.3, 0.4),
        1.0
    )
    
    _draw_status_bar()
    _draw_controls()
    _draw_legend()
    _draw_stats(viewport_size)
    _draw_occupancy_info(viewport_size)
    
    if _inspector_visible:
        _draw_agent_inspector(viewport_size)

func _draw_status_bar() -> void:
    var status_text: String = ""
    var status_color: Color = Color.WHITE
    
    if _is_connected:
        status_text = "✅ Conectado | Tick: %d | Día: %.1f | Agentes: %d" % [
            _tick_count, _current_day, _agent_count
        ]
        status_color = Color(0.5, 1.0, 0.5)
    else:
        status_text = "❌ Desconectado - Intentando reconectar..."
        status_color = Color(1.0, 0.5, 0.5)
    
    draw_string(
        ThemeDB.fallback_font,
        Vector2(10, 20),
        status_text,
        HORIZONTAL_ALIGNMENT_LEFT,
        -1,
        13,
        status_color
    )

func _draw_controls() -> void:
    """Dibuja los botones de control y registra sus áreas."""
    var x_offset: float = 10.0
    var y_offset: float = 28.0
    var button_height: float = 18.0
    var button_spacing: float = 4.0
    
    # Botón Play/Pause
    var pause_label: String = "⏸ PAUSA" if _is_paused else "▶ PLAY"
    var pause_color: Color = COLOR_BUTTON_PAUSED if _is_paused else COLOR_BUTTON_ACTIVE
    var pause_width: float = 80.0
    var pause_rect: Rect2 = Rect2(Vector2(x_offset, y_offset), Vector2(pause_width, button_height))
    _draw_button(pause_rect, pause_label, pause_color)
    _button_areas.append({"rect": pause_rect, "action": "pause", "speed": 0.0})
    x_offset += pause_width + button_spacing
    
    # Separador
    draw_line(
        Vector2(x_offset, y_offset + 2),
        Vector2(x_offset, y_offset + button_height - 2),
        Color(0.5, 0.5, 0.6),
        1.0
    )
    x_offset += 8.0
    
    # Etiqueta "Velocidad:"
    draw_string(
        ThemeDB.fallback_font,
        Vector2(x_offset, y_offset + 14),
        "Vel:",
        HORIZONTAL_ALIGNMENT_LEFT,
        -1,
        11,
        Color(0.7, 0.7, 0.7)
    )
    x_offset += 30.0
    
    # Botones de velocidad
    var speeds: Array = [1.0, 2.0, 5.0, 10.0]
    var button_width: float = 32.0
    
    for speed in speeds:
        var label: String = "%dx" % int(speed)
        var color: Color = COLOR_BUTTON_ACTIVE if abs(_current_speed - speed) < 0.01 else COLOR_BUTTON_INACTIVE
        var rect: Rect2 = Rect2(Vector2(x_offset, y_offset), Vector2(button_width, button_height))
        _draw_button(rect, label, color)
        _button_areas.append({"rect": rect, "action": "speed", "speed": speed})
        x_offset += button_width + button_spacing
    
    # Separador
    draw_line(
        Vector2(x_offset, y_offset + 2),
        Vector2(x_offset, y_offset + button_height - 2),
        Color(0.5, 0.5, 0.6),
        1.0
    )
    x_offset += 8.0
    
    # Etiqueta de atajos
    draw_string(
        ThemeDB.fallback_font,
        Vector2(x_offset, y_offset + 14),
        "[Espacio] Play/Pause  [1-4] Velocidad  [N] Paso  [C] Centrar  [ESC] Deseleccionar",
        HORIZONTAL_ALIGNMENT_LEFT,
        -1,
        11,
        Color(0.6, 0.6, 0.65)
    )

func _draw_button(rect: Rect2, label: String, color: Color) -> void:
    """Dibuja un botón rectangular con etiqueta."""
    draw_rect(rect, color)
    draw_rect(rect, Color(color.r * 1.5, color.g * 1.5, color.b * 1.5), false, 1.0)
    
    var text_size: int = 11
    var font: Font = ThemeDB.fallback_font
    var text_width: float = font.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, text_size).x
    var text_x: float = rect.position.x + (rect.size.x - text_width) / 2.0
    var text_y: float = rect.position.y + rect.size.y / 2.0 + text_size / 3.0
    
    draw_string(
        font,
        Vector2(text_x, text_y),
        label,
        HORIZONTAL_ALIGNMENT_LEFT,
        -1,
        text_size,
        Color.WHITE
    )

func _draw_legend() -> void:
    var y_offset: float = LEGEND_POSITION.y
    
    draw_string(
        ThemeDB.fallback_font,
        LEGEND_POSITION,
        "LEYENDA",
        HORIZONTAL_ALIGNMENT_LEFT,
        -1,
        12,
        Color.WHITE
    )
    y_offset += LEGEND_SPACING
    
    # Especies presentes
    if not _species_counts.is_empty():
        draw_string(
            ThemeDB.fallback_font,
            LEGEND_POSITION + Vector2(0, y_offset),
            "ESPECIES",
            HORIZONTAL_ALIGNMENT_LEFT,
            -1,
            11,
            Color(0.9, 0.9, 0.5)
        )
        y_offset += LEGEND_SPACING * 0.8
        
        for species_id in _species_counts:
            var count: int = _species_counts[species_id]
            var color: Color = _get_species_color(species_id)
            
            draw_circle(
                Vector2(LEGEND_POSITION.x + 8, y_offset - 4),
                6.0,
                color
            )
            draw_string(
                ThemeDB.fallback_font,
                Vector2(LEGEND_POSITION.x + 20, y_offset),
                "%s (%d)" % [species_id, count],
                HORIZONTAL_ALIGNMENT_LEFT,
                -1,
                11,
                Color.WHITE
            )
            y_offset += LEGEND_SPACING * 0.8
        
        y_offset += LEGEND_SPACING * 0.5
    
    # Estados de salud
    draw_string(
        ThemeDB.fallback_font,
        LEGEND_POSITION + Vector2(0, y_offset),
        "ESTADOS",
        HORIZONTAL_ALIGNMENT_LEFT,
        -1,
        11,
        Color(0.9, 0.9, 0.5)
    )
    y_offset += LEGEND_SPACING * 0.8
    
    var legend_items: Array = [
        {"color": COLOR_SICK, "label": "Enfermo"},
        {"color": COLOR_PREGNANT, "label": "Embarazada"},
        {"color": COLOR_YOUNG, "label": "Joven"},
        {"color": COLOR_SENIOR, "label": "Anciano"},
    ]
    
    for item in legend_items:
        draw_circle(
            Vector2(LEGEND_POSITION.x + 8, y_offset - 4),
            6.0,
            item["color"]
        )
        draw_string(
            ThemeDB.fallback_font,
            Vector2(LEGEND_POSITION.x + 20, y_offset),
            item["label"],
            HORIZONTAL_ALIGNMENT_LEFT,
            -1,
            11,
            Color.WHITE
        )
        y_offset += LEGEND_SPACING * 0.8
    
    # Superposición
    y_offset += LEGEND_SPACING * 0.3
    draw_rect(
        Rect2(Vector2(LEGEND_POSITION.x, y_offset - 8), Vector2(16, 12)),
        Color(1.0, 0.5, 0.0, 0.4)
    )
    draw_rect(
        Rect2(Vector2(LEGEND_POSITION.x, y_offset - 8), Vector2(16, 12)),
        Color(1.0, 0.8, 0.0),
        false,
        1.0
    )
    draw_string(
        ThemeDB.fallback_font,
        Vector2(LEGEND_POSITION.x + 20, y_offset),
        "Superposición",
        HORIZONTAL_ALIGNMENT_LEFT,
        -1,
        11,
        Color.WHITE
    )

func _get_species_color(species_id: String) -> Color:
    """Retorna el color de una especie."""
    var species_colors: Dictionary = {
        "human": Color(0.298, 0.686, 0.314),
        "mammal": Color(0.545, 0.765, 0.290),
        "bird": Color(0.255, 0.412, 0.882),
        "fish": Color(0.0, 0.749, 1.0),
        "insect": Color(1.0, 0.647, 0.0),
        "reptile": Color(0.545, 0.271, 0.075),
        "amphibian": Color(0.0, 0.800, 0.500),
        "bacteria": Color(0.855, 0.439, 0.839),
        "plant": Color(0.133, 0.545, 0.133),
        "fungus": Color(0.824, 0.706, 0.549),
        "fantasy_creature": Color(1.0, 0.078, 0.576),
    }
    return species_colors.get(species_id, Color(0.8, 0.8, 0.8))

func _draw_stats(viewport_size: Vector2) -> void:
    if _stats.is_empty():
        return
    
    var x_pos: float = viewport_size.x - 200
    var y_offset: float = 60.0
    
    draw_string(
        ThemeDB.fallback_font,
        Vector2(x_pos, y_offset),
        "ESTADÍSTICAS",
        HORIZONTAL_ALIGNMENT_LEFT,
        -1,
        12,
        Color.WHITE
    )
    y_offset += 18.0
    
    var population: int = _stats.get("total_population", 0)
    draw_string(
        ThemeDB.fallback_font,
        Vector2(x_pos, y_offset),
        "Población: %d" % population,
        HORIZONTAL_ALIGNMENT_LEFT,
        -1,
        12,
        Color(0.8, 0.8, 0.8)
    )
    y_offset += 16.0
    
    var sick_count: int = _stats.get("sick_count", 0)
    var sick_color: Color = Color(0.957, 0.263, 0.212) if sick_count > 0 else Color(0.5, 1.0, 0.5)
    draw_string(
        ThemeDB.fallback_font,
        Vector2(x_pos, y_offset),
        "Enfermos: %d" % sick_count,
        HORIZONTAL_ALIGNMENT_LEFT,
        -1,
        12,
        sick_color
    )
    y_offset += 16.0
    
    var births: int = _stats.get("total_births", 0)
    draw_string(
        ThemeDB.fallback_font,
        Vector2(x_pos, y_offset),
        "Nacimientos: %d" % births,
        HORIZONTAL_ALIGNMENT_LEFT,
        -1,
        12,
        Color(0.8, 0.8, 0.8)
    )
    y_offset += 16.0
    
    var deaths: int = _stats.get("total_deaths", 0)
    draw_string(
        ThemeDB.fallback_font,
        Vector2(x_pos, y_offset),
        "Muertes: %d" % deaths,
        HORIZONTAL_ALIGNMENT_LEFT,
        -1,
        12,
        Color(0.8, 0.8, 0.8)
    )

func _draw_occupancy_info(viewport_size: Vector2) -> void:
    var info_text: String = "📊 Ocupación: %d agentes en %d casillas únicas | ⚠️ Superposiciones: %d" % [
        _agent_count, _unique_cells, _overlapping_count
    ]
    
    var info_color: Color = Color(1.0, 0.5, 0.5) if _overlapping_count > 0 else Color(0.5, 1.0, 0.5)
    
    draw_string(
        ThemeDB.fallback_font,
        Vector2(10, viewport_size.y - 10),
        info_text,
        HORIZONTAL_ALIGNMENT_LEFT,
        -1,
        12,
        info_color
    )

func _draw_agent_inspector(viewport_size: Vector2) -> void:
    """Dibuja el panel del inspector de agentes."""
    if _inspector_agent.is_empty():
        return
    
    var panel_x: float = viewport_size.x - INSPECTOR_WIDTH - INSPECTOR_PADDING
    var panel_y: float = viewport_size.y - 320.0
    
    var num_lines: int = 12
    var panel_height: float = float(num_lines) * INSPECTOR_LINE_HEIGHT + INSPECTOR_PADDING * 2.0 + 30.0
    
    var panel_rect: Rect2 = Rect2(
        Vector2(panel_x, panel_y),
        Vector2(INSPECTOR_WIDTH, panel_height)
    )
    draw_rect(panel_rect, INSPECTOR_BG_COLOR)
    draw_rect(panel_rect, INSPECTOR_BORDER_COLOR, false, 1.0)
    
    # Título
    var title_y: float = panel_y + INSPECTOR_PADDING + 14.0
    draw_string(
        ThemeDB.fallback_font,
        Vector2(panel_x + INSPECTOR_PADDING, title_y),
        "👤 INSPECTOR DE INDIVIDUO",
        HORIZONTAL_ALIGNMENT_LEFT,
        -1,
        13,
        INSPECTOR_TITLE_COLOR
    )
    
    # Línea separadora
    var separator_y: float = title_y + 8.0
    draw_line(
        Vector2(panel_x + INSPECTOR_PADDING, separator_y),
        Vector2(panel_x + INSPECTOR_WIDTH - INSPECTOR_PADDING, separator_y),
        INSPECTOR_BORDER_COLOR,
        1.0
    )
    
    # Datos del agente
    var y_offset: float = separator_y + INSPECTOR_LINE_HEIGHT
    
    _draw_inspector_line(panel_x, y_offset, "ID:", str(int(_inspector_agent.get("id", 0))))
    y_offset += INSPECTOR_LINE_HEIGHT
    
    var age_days: float = _inspector_agent.get("age", 0.0)
    var age_years: float = age_days / 365.25
    _draw_inspector_line(panel_x, y_offset, "Edad:", "%.1f años" % age_years)
    y_offset += INSPECTOR_LINE_HEIGHT
    
    var pos_x: float = _inspector_agent.get("x", 0.0)
    var pos_y: float = _inspector_agent.get("y", 0.0)
    _draw_inspector_line(panel_x, y_offset, "Posición:", "(%.0f, %.0f)" % [pos_x, pos_y])
    y_offset += INSPECTOR_LINE_HEIGHT
    
    var gender: String = _inspector_agent.get("gender", "desconocido")
    var gender_text: String = "♂ Masculino" if gender == "M" else ("♀ Femenino" if gender == "F" else gender)
    _draw_inspector_line(panel_x, y_offset, "Sexo:", gender_text)
    y_offset += INSPECTOR_LINE_HEIGHT
    
    var species: String = _inspector_agent.get("species", "human")
    _draw_inspector_line(panel_x, y_offset, "Especie:", species)
    y_offset += INSPECTOR_LINE_HEIGHT
    
    var is_sick: bool = _inspector_agent.get("is_sick", false)
    var health_text: String = "🤒 Enfermo" if is_sick else "✅ Sano"
    var health_color: Color = Color(0.957, 0.263, 0.212) if is_sick else Color(0.5, 1.0, 0.5)
    _draw_inspector_line(panel_x, y_offset, "Salud:", health_text, health_color)
    y_offset += INSPECTOR_LINE_HEIGHT
    
    var is_pregnant: bool = _inspector_agent.get("is_pregnant", false)
    var pregnancy_text: String = "🤰 Embarazada" if is_pregnant else "—"
    _draw_inspector_line(panel_x, y_offset, "Embarazo:", pregnancy_text)
    y_offset += INSPECTOR_LINE_HEIGHT
    
    var is_adult: bool = _inspector_agent.get("is_adult", true)
    var is_senior: bool = _inspector_agent.get("is_senior", false)
    var stage_text: String = "👶 Joven" if not is_adult else ("👴 Anciano" if is_senior else "🧑 Adulto")
    _draw_inspector_line(panel_x, y_offset, "Etapa:", stage_text)
    y_offset += INSPECTOR_LINE_HEIGHT
    
    # Separador
    y_offset += 4.0
    draw_line(
        Vector2(panel_x + INSPECTOR_PADDING, y_offset),
        Vector2(panel_x + INSPECTOR_WIDTH - INSPECTOR_PADDING, y_offset),
        Color(0.3, 0.3, 0.4),
        1.0
    )
    y_offset += INSPECTOR_LINE_HEIGHT
    
    draw_string(
        ThemeDB.fallback_font,
        Vector2(panel_x + INSPECTOR_PADDING, y_offset),
        "[ESC] Cerrar inspector",
        HORIZONTAL_ALIGNMENT_LEFT,
        -1,
        10,
        Color(0.5, 0.5, 0.55)
    )

func _draw_inspector_line(panel_x: float, y: float, label: String, value: String, value_color: Color = INSPECTOR_VALUE_COLOR) -> void:
    """Dibuja una línea del inspector con etiqueta y valor."""
    draw_string(
        ThemeDB.fallback_font,
        Vector2(panel_x + INSPECTOR_PADDING, y),
        label,
        HORIZONTAL_ALIGNMENT_LEFT,
        -1,
        11,
        INSPECTOR_LABEL_COLOR
    )
    
    var font: Font = ThemeDB.fallback_font
    var value_width: float = font.get_string_size(value, HORIZONTAL_ALIGNMENT_LEFT, -1, 11).x
    var value_x: float = panel_x + INSPECTOR_WIDTH - INSPECTOR_PADDING - value_width
    
    draw_string(
        font,
        Vector2(value_x, y),
        value,
        HORIZONTAL_ALIGNMENT_LEFT,
        -1,
        11,
        value_color
    )
