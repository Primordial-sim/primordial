extends Control

var _is_connected: bool = false
var _tick_count: int = 0
var _current_day: float = 0.0
var _agent_count: int = 0
var _stats: Dictionary = {}
var _is_paused: bool = false
var _current_speed: float = 1.0
var _button_areas: Array = []
var _inspector_visible: bool = false
var _inspector_agent: Dictionary = {}
var _presets: Array = []

func _ready() -> void:
    set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    mouse_filter = Control.MOUSE_FILTER_IGNORE

func update_connection_status(c: bool) -> void: _is_connected = c; queue_redraw()
func update_tick_info(t: int, d: float, a: int) -> void: _tick_count = t; _current_day = d; _agent_count = a; queue_redraw()
func update_stats(s: Dictionary) -> void: _stats = s; queue_redraw()
func update_control_state(p: bool, s: float) -> void: _is_paused = p; _current_speed = s; queue_redraw()
func update_presets(p: Array) -> void: _presets = p; queue_redraw()
func show_agent_inspector(d: Dictionary) -> void: _inspector_visible = true; _inspector_agent = d; queue_redraw()
func hide_agent_inspector() -> void: _inspector_visible = false; queue_redraw()

func get_button_at_position(pos: Vector2) -> Dictionary:
    for b in _button_areas:
        if b["rect"].has_point(pos): return b
    return {}

func _draw() -> void:
    var vp = get_viewport_rect().size
    _button_areas.clear()
    
    # Barra de controles (800px ancho, centrada, debajo del mundo)
    var bar_w = 800.0
    var bar_h = 40.0
    var bar_x = (vp.x - bar_w) / 2.0
    var bar_y = (vp.y / 2.0) + 410.0 # Justo debajo del WorldContainer (que termina en +390)
    
    var bar_rect = Rect2(bar_x, bar_y, bar_w, bar_h)
    draw_rect(bar_rect, Color(0.2, 0.2, 0.25))
    _button_areas.append({"rect": bar_rect, "action": "pause"})
    
    # CORREGIDO: Se añaden HORIZONTAL_ALIGNMENT_LEFT y -1 antes del color
    draw_string(ThemeDB.fallback_font, Vector2(bar_x + 20, bar_y + 25), "PLAY/PAUSE", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.WHITE)
    
    # Stats
    draw_string(ThemeDB.fallback_font, Vector2(20, 30), "Tick: %d | Agentes: %d" % [_tick_count, _agent_count], HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.WHITE)