extends Control

const COLOR_BUTTON_ACTIVE: Color = Color(0.2, 0.6, 0.9)
const COLOR_BUTTON_INACTIVE: Color = Color(0.3, 0.3, 0.35)
const COLOR_BUTTON_PAUSED: Color = Color(0.9, 0.5, 0.2)
const COLOR_BUTTON_ACTION: Color = Color(0.2, 0.8, 0.4)

const WORLD_FRAME_SIZE: float = 800.0
const CONTROL_BAR_HEIGHT: float = 45.0

const INSPECTOR_WIDTH: float = 280.0
const INSPECTOR_PADDING: float = 10.0
const INSPECTOR_LINE_HEIGHT: float = 16.0
const INSPECTOR_BG_COLOR: Color = Color(0.12, 0.12, 0.18, 0.95)
const INSPECTOR_BORDER_COLOR: Color = Color(0.4, 0.4, 0.5)
const INSPECTOR_TITLE_COLOR: Color = Color(0.9, 0.9, 1.0)
const INSPECTOR_LABEL_COLOR: Color = Color(0.7, 0.7, 0.75)
const INSPECTOR_VALUE_COLOR: Color = Color(0.9, 0.9, 0.9)
const HEADER_BG_COLOR: Color = Color(0.2, 0.2, 0.28, 1.0)

var _is_connected: bool = false
var _tick_count: int = 0
var _current_day: float = 0.0
var _agent_count: int = 0
var _stats: Dictionary = {}
var _is_paused: bool = false
var _current_speed: float = 1.0
var _button_areas: Array = []
var _group_inspector_visible: bool = false
var _group_agents: Array = []
var _presets: Array = []
var _current_zoom: float = 1.0
var _is_following: bool = false

var _inspector_visible: bool = false
var _inspector_agent_id: int = -1
var _inspector_loading: bool = false
var _inspector_details: Dictionary = {}

var _section_genome_open: bool = false
var _section_psych_open: bool = false
var _section_relations_open: bool = false

const SPEED_OPTIONS = [
    {"label": "1x", "value": 1},
    {"label": "10x", "value": 10},
    {"label": "100x", "value": 100},
    {"label": "1000x", "value": 1000}
]

func _ready() -> void:
    set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    mouse_filter = Control.MOUSE_FILTER_IGNORE

func update_connection_status(c: bool) -> void: _is_connected = c; queue_redraw()
func update_tick_info(t: int, d: float, a: int) -> void: _tick_count = t; _current_day = d; _agent_count = a; queue_redraw()
func update_stats(s: Dictionary) -> void: _stats = s; queue_redraw()
func update_control_state(p: bool, s: float) -> void: _is_paused = p; _current_speed = s; queue_redraw()
func update_presets(p: Array) -> void: _presets = p; queue_redraw()
func update_zoom_level(z: float) -> void: _current_zoom = z; queue_redraw()
func set_following_state(is_following: bool) -> void: _is_following = is_following; queue_redraw()

func show_agent_inspector_loading(agent_id: int) -> void:
    _inspector_visible = true
    _inspector_agent_id = agent_id
    _inspector_loading = true
    _inspector_details = {}
    _group_inspector_visible = false
    queue_redraw()

func show_agent_full_inspector(details: Dictionary) -> void:
    _inspector_visible = true
    _inspector_agent_id = int(details.get("id", -1))
    _inspector_loading = false
    _inspector_details = details
    _group_inspector_visible = false
    queue_redraw()

func hide_agent_inspector() -> void:
    _inspector_visible = false
    _inspector_details = {}
    _inspector_loading = false
    _is_following = false
    queue_redraw()

func show_group_inspector(agents: Array) -> void:
    _group_inspector_visible = true
    _group_agents = agents
    _inspector_visible = false
    _is_following = false
    queue_redraw()

func hide_group_inspector() -> void:
    _group_inspector_visible = false
    _group_agents = []
    queue_redraw()

func toggle_section(section_id: String) -> void:
    if section_id == "section_genome": _section_genome_open = not _section_genome_open
    elif section_id == "section_psych": _section_psych_open = not _section_psych_open
    elif section_id == "section_relations": _section_relations_open = not _section_relations_open
    queue_redraw()

func get_button_at_position(pos: Vector2) -> Dictionary:
    for b in _button_areas:
        if b["rect"].has_point(pos): return b
    return {}

func _draw() -> void:
    var vp = get_viewport_rect().size
    _button_areas.clear()
    
    var bar_w = WORLD_FRAME_SIZE
    var bar_h = CONTROL_BAR_HEIGHT
    var bar_x = (vp.x - bar_w) / 2.0
    var bar_y = (vp.y / 2.0) + 410.0
    
    var bar_rect = Rect2(bar_x, bar_y, bar_w, bar_h)
    draw_rect(bar_rect, Color(0.12, 0.12, 0.18, 0.95))
    draw_rect(bar_rect, Color(0.35, 0.35, 0.45), false, 1.0)
    
    var x_offset: float = bar_x + 10.0
    var y_center: float = bar_y + bar_h / 2.0
    var button_height: float = 28.0
    var button_y: float = y_center - button_height / 2.0
    var button_spacing: float = 4.0
    
    var pause_label: String = "⏸" if _is_paused else "▶"
    var pause_color: Color = COLOR_BUTTON_PAUSED if _is_paused else COLOR_BUTTON_ACTIVE
    var pause_rect = Rect2(x_offset, button_y, 35.0, button_height)
    _draw_button(pause_rect, pause_label, pause_color)
    _button_areas.append({"rect": pause_rect, "action": "pause", "speed": 0.0})
    x_offset += 35.0 + button_spacing
    
    draw_line(Vector2(x_offset, button_y + 4), Vector2(x_offset, button_y + button_height - 4), Color(0.4, 0.4, 0.5), 1.0)
    x_offset += 8.0
    
    draw_string(ThemeDB.fallback_font, Vector2(x_offset, y_center + 4), "Vel:", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color(0.7, 0.7, 0.7))
    x_offset += 28.0
    
    for option in SPEED_OPTIONS:
        var color: Color = COLOR_BUTTON_ACTIVE if abs(_current_speed - option["value"]) < 0.1 else COLOR_BUTTON_INACTIVE
        var rect = Rect2(x_offset, button_y, 50.0, button_height)
        _draw_button(rect, option["label"], color)
        _button_areas.append({"rect": rect, "action": "speed", "speed": option["value"]})
        x_offset += 50.0 + button_spacing
    
    var status_text: String = "✅ Tick: %d | Día: %.1f | Agentes: %d" % [_tick_count, _current_day, _agent_count] if _is_connected else "❌ Desconectado"
    var status_color: Color = Color(0.5, 1.0, 0.5) if _is_connected else Color(1.0, 0.5, 0.5)
    draw_string(ThemeDB.fallback_font, Vector2(x_offset + 10, y_center + 5), status_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, status_color)
    
    var zoom_text: String = "Zoom: %d%%" % int(_current_zoom * 100)
    var z_font: Font = ThemeDB.fallback_font
    var z_tw: float = z_font.get_string_size(zoom_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 12).x
    draw_string(z_font, Vector2(bar_x + bar_w - z_tw - 15, y_center + 5), zoom_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(0.7, 0.7, 0.7))
    
    if _inspector_visible:
        _draw_agent_inspector(vp)
    elif _group_inspector_visible:
        _draw_group_inspector(vp)

func _draw_agent_inspector(viewport_size: Vector2) -> void:
    var panel_x: float = viewport_size.x - INSPECTOR_WIDTH - 20.0
    var panel_y: float = 60.0
    
    if _inspector_loading:
        var h = 80.0
        draw_rect(Rect2(panel_x, panel_y, INSPECTOR_WIDTH, h), INSPECTOR_BG_COLOR)
        draw_rect(Rect2(panel_x, panel_y, INSPECTOR_WIDTH, h), INSPECTOR_BORDER_COLOR, false, 1.0)
        draw_string(ThemeDB.fallback_font, Vector2(panel_x + INSPECTOR_PADDING, panel_y + 45), "Cargando datos...", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(0.7, 0.7, 0.7))
        return
        
    if _inspector_details.is_empty():
        hide_agent_inspector()
        return

    var h = 100.0
    if _section_genome_open: h += 130.0
    if _section_psych_open: h += 130.0
    if _section_relations_open: h += 130.0
    
    var panel_rect: Rect2 = Rect2(Vector2(panel_x, panel_y), Vector2(INSPECTOR_WIDTH, h))
    draw_rect(panel_rect, INSPECTOR_BG_COLOR)
    draw_rect(panel_rect, INSPECTOR_BORDER_COLOR, false, 1.0)
    
    var y: float = panel_y + INSPECTOR_PADDING + 14.0
    draw_string(ThemeDB.fallback_font, Vector2(panel_x + INSPECTOR_PADDING, y), "👤 AGENTE #%d" % _inspector_agent_id, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, INSPECTOR_TITLE_COLOR)
    y += 24.0
    
    var d = _inspector_details
    _draw_inspector_line(panel_x, y, "Especie:", d.get("species", "?")); y += INSPECTOR_LINE_HEIGHT
    _draw_inspector_line(panel_x, y, "Edad:", "%.1f años" % (d.get("age", 0.0) / 365.25)); y += INSPECTOR_LINE_HEIGHT
    var g: String = d.get("gender", "?")
    _draw_inspector_line(panel_x, y, "Sexo:", "♂" if g == "M" else ("♀" if g == "F" else g)); y += INSPECTOR_LINE_HEIGHT
    _draw_inspector_line(panel_x, y, "Estado civil:", d.get("marital_status", "?").capitalize()); y += INSPECTOR_LINE_HEIGHT
    _draw_inspector_line(panel_x, y, "Reputación:", "%.2f" % d.get("reputation", 0.5)); y += INSPECTOR_LINE_HEIGHT
    
    y += 8.0
    draw_line(Vector2(panel_x + INSPECTOR_PADDING, y), Vector2(panel_x + INSPECTOR_WIDTH - INSPECTOR_PADDING, y), Color(0.3, 0.3, 0.4), 1.0)
    y += 8.0
    
    y = _draw_collapsible_section(panel_x, y, "🧬 GENOMA", _section_genome_open, "section_genome")
    if _section_genome_open:
        var genome = d.get("genome", {})
        _draw_inspector_line(panel_x, y, "  Longevidad:", "%.2f" % genome.get("longevity", 0.0)); y += INSPECTOR_LINE_HEIGHT
        _draw_inspector_line(panel_x, y, "  Fertilidad:", "%.2f" % genome.get("fertility", 0.0)); y += INSPECTOR_LINE_HEIGHT
        _draw_inspector_line(panel_x, y, "  Metabolismo:", "%.2f" % genome.get("metabolism", 0.0)); y += INSPECTOR_LINE_HEIGHT
        _draw_inspector_line(panel_x, y, "  Inmunidad:", "%.2f" % genome.get("immunity", 0.0)); y += INSPECTOR_LINE_HEIGHT
        _draw_inspector_line(panel_x, y, "  Sociabilidad:", "%.2f" % genome.get("sociability", 0.0)); y += INSPECTOR_LINE_HEIGHT
        _draw_inspector_line(panel_x, y, "  Temperamento:", "%.2f" % genome.get("temperament", 0.0)); y += INSPECTOR_LINE_HEIGHT
        y += 4.0

    y = _draw_collapsible_section(panel_x, y, "🧠 PSICOLOGÍA", _section_psych_open, "section_psych")
    if _section_psych_open:
        var emo = d.get("emotions", {})
        var mot = d.get("motivations", {})
        _draw_inspector_line(panel_x, y, "  Estrés:", "%.2f" % emo.get("stress", 0.0), Color(0.957, 0.263, 0.212) if emo.get("stress", 0.0) > 0.6 else INSPECTOR_VALUE_COLOR); y += INSPECTOR_LINE_HEIGHT
        _draw_inspector_line(panel_x, y, "  Felicidad:", "%.2f" % emo.get("happiness", 0.0), Color(0.2, 0.8, 0.4) if emo.get("happiness", 0.0) > 0.6 else INSPECTOR_VALUE_COLOR); y += INSPECTOR_LINE_HEIGHT
        _draw_inspector_line(panel_x, y, "  Energía:", "%.2f" % emo.get("energy", 0.0)); y += INSPECTOR_LINE_HEIGHT
        y += 4.0
        _draw_inspector_line(panel_x, y, "  Cooperación:", "%.2f" % mot.get("cooperation", 0.0)); y += INSPECTOR_LINE_HEIGHT
        _draw_inspector_line(panel_x, y, "  Exploración:", "%.2f" % mot.get("exploration", 0.0)); y += INSPECTOR_LINE_HEIGHT
        y += 4.0

    y = _draw_collapsible_section(panel_x, y, "❤️ RELACIONES", _section_relations_open, "section_relations")
    if _section_relations_open:
        var fam = d.get("family", {})
        var parents = fam.get("parents", [])
        var adopt = fam.get("adoptive_parents", [])
        var all_parents = parents + adopt
        var p_str = "Ninguno" if all_parents.is_empty() else str(all_parents)
        _draw_inspector_line(panel_x, y, "  Padres:", p_str); y += INSPECTOR_LINE_HEIGHT
        
        var partner = fam.get("partner", null)
        var part_str = "Ninguno" if partner == null else str(partner)
        _draw_inspector_line(panel_x, y, "  Pareja:", part_str); y += INSPECTOR_LINE_HEIGHT
        
        var bio = fam.get("biological_children", 0)
        var total = fam.get("children_count", 0)
        var adopt_count = total - bio
        var child_str = "%d (Bio: %d, Adop: %d)" % [total, bio, adopt_count]
        _draw_inspector_line(panel_x, y, "  Hijos:", child_str); y += INSPECTOR_LINE_HEIGHT
        y += 4.0

    y += 8.0
    draw_line(Vector2(panel_x + INSPECTOR_PADDING, y), Vector2(panel_x + INSPECTOR_WIDTH - INSPECTOR_PADDING, y), Color(0.3, 0.3, 0.4), 1.0)
    y += 8.0
    
    var btn_w = (INSPECTOR_WIDTH - INSPECTOR_PADDING * 3) / 2.0
    var btn_h = 26.0
    
    var center_rect = Rect2(panel_x + INSPECTOR_PADDING, y, btn_w, btn_h)
    _draw_button(center_rect, "🎯 Centrar", COLOR_BUTTON_ACTION)
    _button_areas.append({"rect": center_rect, "action": "center_agent"})
    
    var follow_color = Color(0.9, 0.7, 0.2) if _is_following else COLOR_BUTTON_ACTION
    var follow_label = "✅ Siguiendo" if _is_following else "👁️ Seguir"
    var follow_rect = Rect2(panel_x + INSPECTOR_PADDING * 2 + btn_w, y, btn_w, btn_h)
    _draw_button(follow_rect, follow_label, follow_color)
    _button_areas.append({"rect": follow_rect, "action": "follow_agent"})
    
    y += btn_h + 8.0
    draw_string(ThemeDB.fallback_font, Vector2(panel_x + INSPECTOR_PADDING, y), "[ESC] Cerrar", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color(0.5, 0.5, 0.55))

func _draw_collapsible_section(panel_x: float, y: float, title: String, is_open: bool, section_id: String) -> float:
    var header_rect = Rect2(panel_x, y, INSPECTOR_WIDTH, 22.0)
    draw_rect(header_rect, HEADER_BG_COLOR)
    draw_rect(header_rect, INSPECTOR_BORDER_COLOR, false, 1.0)
    
    var icon: String = "▶" if not is_open else "▼"
    draw_string(ThemeDB.fallback_font, Vector2(panel_x + 8.0, y + 15.0), "%s %s" % [icon, title], HORIZONTAL_ALIGNMENT_LEFT, -1, 11, INSPECTOR_TITLE_COLOR)
    
    _button_areas.append({"rect": header_rect, "action": "toggle_section", "section": section_id})
    return y + 24.0

func _draw_group_inspector(viewport_size: Vector2) -> void:
    if _group_agents.is_empty(): return
    var panel_x: float = viewport_size.x - INSPECTOR_WIDTH - 20.0
    var panel_y: float = 60.0
    var panel_height: float = 10.0 * INSPECTOR_LINE_HEIGHT + INSPECTOR_PADDING * 2.0 + 30.0
    var panel_rect: Rect2 = Rect2(Vector2(panel_x, panel_y), Vector2(INSPECTOR_WIDTH, panel_height))
    
    draw_rect(panel_rect, INSPECTOR_BG_COLOR)
    draw_rect(panel_rect, INSPECTOR_BORDER_COLOR, false, 1.0)
    
    var title_y: float = panel_y + INSPECTOR_PADDING + 14.0
    draw_string(ThemeDB.fallback_font, Vector2(panel_x + INSPECTOR_PADDING, title_y), "👥 GRUPO (%d)" % _group_agents.size(), HORIZONTAL_ALIGNMENT_LEFT, -1, 13, INSPECTOR_TITLE_COLOR)
    
    var sep_y: float = title_y + 8.0
    draw_line(Vector2(panel_x + INSPECTOR_PADDING, sep_y), Vector2(panel_x + INSPECTOR_WIDTH - INSPECTOR_PADDING, sep_y), INSPECTOR_BORDER_COLOR, 1.0)
    
    var total_age: float = 0.0
    var males: int = 0; var females: int = 0; var sick_count: int = 0
    var adults: int = 0; var seniors: int = 0
    var species_count: Dictionary = {}
    
    for agent in _group_agents:
        total_age += agent.get("age", 0.0)
        if agent.get("gender", "") == "M": males += 1
        elif agent.get("gender", "") == "F": females += 1
        if agent.get("is_sick", false): sick_count += 1
        if agent.get("is_adult", true): adults += 1
        if agent.get("is_senior", false): seniors += 1
        var species = agent.get("species", "unknown")
        species_count[species] = species_count.get(species, 0) + 1
    
    var avg_age: float = total_age / _group_agents.size() / 365.25
    var y: float = sep_y + INSPECTOR_LINE_HEIGHT
    _draw_inspector_line(panel_x, y, "Total:", str(_group_agents.size())); y += INSPECTOR_LINE_HEIGHT
    _draw_inspector_line(panel_x, y, "Edad media:", "%.1f años" % avg_age); y += INSPECTOR_LINE_HEIGHT
    _draw_inspector_line(panel_x, y, "Sexo:", "♂%d | ♀%d" % [males, females]); y += INSPECTOR_LINE_HEIGHT
    _draw_inspector_line(panel_x, y, "Salud:", "🤒 %d" % sick_count, Color(0.957, 0.263, 0.212) if sick_count > 0 else Color(0.5, 1.0, 0.5)); y += INSPECTOR_LINE_HEIGHT
    _draw_inspector_line(panel_x, y, "Adultos:", "%d" % adults); y += INSPECTOR_LINE_HEIGHT
    _draw_inspector_line(panel_x, y, "Ancianos:", "%d" % seniors); y += INSPECTOR_LINE_HEIGHT
    
    y += 4.0
    draw_line(Vector2(panel_x + INSPECTOR_PADDING, y), Vector2(panel_x + INSPECTOR_WIDTH - INSPECTOR_PADDING, y), Color(0.3, 0.3, 0.4), 1.0)
    y += INSPECTOR_LINE_HEIGHT
    draw_string(ThemeDB.fallback_font, Vector2(panel_x + INSPECTOR_PADDING, y), "Especies:", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, INSPECTOR_LABEL_COLOR)
    y += INSPECTOR_LINE_HEIGHT
    for species in species_count:
        _draw_inspector_line(panel_x, y, "  %s:" % species, str(species_count[species])); y += INSPECTOR_LINE_HEIGHT
    
    y += 4.0
    draw_line(Vector2(panel_x + INSPECTOR_PADDING, y), Vector2(panel_x + INSPECTOR_WIDTH - INSPECTOR_PADDING, y), Color(0.3, 0.3, 0.4), 1.0)
    y += INSPECTOR_LINE_HEIGHT
    draw_string(ThemeDB.fallback_font, Vector2(panel_x + INSPECTOR_PADDING, y), "[ESC] Cerrar", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color(0.5, 0.5, 0.55))

func _draw_inspector_line(panel_x: float, y: float, label: String, value: String, value_color: Color = INSPECTOR_VALUE_COLOR) -> void:
    draw_string(ThemeDB.fallback_font, Vector2(panel_x + INSPECTOR_PADDING, y), label, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, INSPECTOR_LABEL_COLOR)
    var vw: float = ThemeDB.fallback_font.get_string_size(value, HORIZONTAL_ALIGNMENT_LEFT, -1, 11).x
    draw_string(ThemeDB.fallback_font, Vector2(panel_x + INSPECTOR_WIDTH - INSPECTOR_PADDING - vw, y), value, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, value_color)

func _draw_button(rect: Rect2, label: String, color: Color) -> void:
    draw_rect(rect, color)
    draw_rect(rect, Color(color.r * 1.5, color.g * 1.5, color.b * 1.5), false, 1.0)
    var ts: int = 10
    var font: Font = ThemeDB.fallback_font
    var tw: float = font.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, ts).x
    draw_string(font, Vector2(rect.position.x + (rect.size.x - tw) / 2.0, rect.position.y + rect.size.y / 2.0 + ts / 3.0), label, HORIZONTAL_ALIGNMENT_LEFT, -1, ts, Color.WHITE)