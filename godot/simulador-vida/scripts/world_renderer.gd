extends Node2D

signal agents_selected(agents_data: Array)
signal agents_deselected()

var _world_width: int = 100
var _world_height: int = 100
var _cell_size: float = 8.0

const GRID_COLOR: Color = Color(0.4, 0.4, 0.5, 0.8)
const GRID_LINE_WIDTH: float = 1.0
const SELECTION_RING_COLOR: Color = Color(1.0, 1.0, 1.0)
const SELECTION_RING_WIDTH: float = 2.0

const COLOR_SICK: Color = Color(0.957, 0.263, 0.212)
const COLOR_PREGNANT: Color = Color(1.0, 0.757, 0.027)
const COLOR_YOUNG: Color = Color(0.129, 0.588, 0.953)
const COLOR_SENIOR: Color = Color(0.620, 0.620, 0.620)

const SPECIES_COLORS: Dictionary = {
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
const DEFAULT_SPECIES_COLOR: Color = Color(0.8, 0.8, 0.8)

var _agents: Array = []
var _selected_agent_ids: Array = []
var _selection_rect_start: Vector2 = Vector2.ZERO
var _selection_rect_end: Vector2 = Vector2.ZERO
var _is_dragging_selection: bool = false

# Caché de la rejilla del dominio fundamental (una sola copia)
var _grid_cache: PackedVector2Array = PackedVector2Array()
var _grid_cache_dirty: bool = true

# =============================================================================
# CONVERSIÓN HEXAGONAL (offset odd-r)
# =============================================================================

func hex_to_pixel(q: float, r: float) -> Vector2:
    var ri = int(round(r))
    var shift = 0.5 if (ri & 1) == 1 else 0.0
    var x = _cell_size * sqrt(3.0) * (q + shift)
    var y = _cell_size * 1.5 * r
    return Vector2(x, y)

func world_size() -> Vector2:
    return Vector2(
        _cell_size * sqrt(3.0) * float(_world_width),
        _cell_size * 1.5 * float(_world_height)
    )

func _hex_corners(center: Vector2, size: float) -> PackedVector2Array:
    var corners = PackedVector2Array()
    for i in range(6):
        var angle_deg = 60.0 * i - 30.0
        var angle_rad = deg_to_rad(angle_deg)
        corners.append(Vector2(
            center.x + size * cos(angle_rad),
            center.y + size * sin(angle_rad)
        ))
    return corners

func _draw_hex(center: Vector2, size: float, color: Color, filled: bool, width: float = 1.0) -> void:
    var corners = _hex_corners(center, size)
    if filled:
        draw_colored_polygon(corners, color)
    else:
        for i in range(6):
            var next_i = (i + 1) % 6
            draw_line(corners[i], corners[next_i], color, width)

func _wrap_offsets() -> Array:
    var ws = world_size()
    var offsets = []
    for i in range(-1, 2):
        for j in range(-1, 2):
            offsets.append(Vector2(ws.x * float(i), ws.y * float(j)))
    return offsets

# =============================================================================
# CACHÉ DE REJILLA
# =============================================================================

func _build_grid_cache() -> void:
    _grid_cache.clear()

    var unit = _hex_corners(Vector2.ZERO, _cell_size)
    var col_w = _cell_size * sqrt(3.0)
    var row_h = _cell_size * 1.5

    for r in range(0, _world_height):
        var shift = 0.5 if (r & 1) == 1 else 0.0
        var y = row_h * float(r)
        for q in range(0, _world_width):
            var cx = col_w * (float(q) + shift)
            for i in range(6):
                var next_i = (i + 1) % 6
                _grid_cache.append(Vector2(cx + unit[i].x, y + unit[i].y))
                _grid_cache.append(Vector2(cx + unit[next_i].x, y + unit[next_i].y))

    _grid_cache_dirty = false

# =============================================================================
# ÁREA VISIBLE
# =============================================================================

func _get_visible_rect() -> Rect2:
    var vp = get_viewport()
    if vp == null:
        return Rect2(-400, -400, 800, 800)
    var vp_size = vp.get_visible_rect().size
    var cam = vp.get_camera_2d()
    var zoom = Vector2.ONE
    var center = Vector2.ZERO
    if cam != null:
        zoom = cam.zoom
        center = cam.global_position
    var half = vp_size / (2.0 * zoom)
    return Rect2(center - half, half * 2.0)

# =============================================================================
# API PÚBLICA
# =============================================================================

func update_agents(agents: Array) -> void:
    _agents = agents
    queue_redraw()

func set_cell_size(size: float) -> void:
    _cell_size = size
    _grid_cache_dirty = true
    queue_redraw()

func set_world_dimensions(width: int, height: int) -> void:
    _world_width = width
    _world_height = height
    _grid_cache_dirty = true
    queue_redraw()

# =============================================================================
# SELECCIÓN
# =============================================================================

func start_selection_drag(world_pos: Vector2) -> void:
    _is_dragging_selection = true
    _selection_rect_start = world_pos
    _selection_rect_end = world_pos
    queue_redraw()

func update_selection_drag(world_pos: Vector2) -> void:
    if _is_dragging_selection:
        _selection_rect_end = world_pos
        queue_redraw()

func finish_selection_drag(add_to_selection: bool) -> Array:
    _is_dragging_selection = false

    var top_left = Vector2(
        min(_selection_rect_start.x, _selection_rect_end.x),
        min(_selection_rect_start.y, _selection_rect_end.y)
    )
    var bottom_right = Vector2(
        max(_selection_rect_start.x, _selection_rect_end.x),
        max(_selection_rect_start.y, _selection_rect_end.y)
    )
    var selection_rect = Rect2(top_left, bottom_right - top_left)

    var selected_agents: Array = []
    var margin = _cell_size * 1.5

    for agent in _agents:
        var agent_pos = hex_to_pixel(agent.get("q", 0.0), agent.get("r", 0.0))
        var expanded = Rect2(
            selection_rect.position - Vector2(margin, margin),
            selection_rect.size + Vector2(margin * 2.0, margin * 2.0)
        )
        if expanded.has_point(agent_pos):
            selected_agents.append(agent)

    if add_to_selection:
        for agent in selected_agents:
            var agent_id = int(agent.get("id", -1))
            if not _selected_agent_ids.has(agent_id):
                _selected_agent_ids.append(agent_id)
    else:
        _selected_agent_ids = []
        for agent in selected_agents:
            _selected_agent_ids.append(int(agent.get("id", -1)))

    queue_redraw()

    var final_selected: Array = []
    for agent in _agents:
        if _selected_agent_ids.has(int(agent.get("id", -1))):
            final_selected.append(agent)

    return final_selected

func cancel_selection_drag() -> void:
    _is_dragging_selection = false
    queue_redraw()

func select_agent(agent_id: int, add_to_selection: bool) -> void:
    if add_to_selection:
        if not _selected_agent_ids.has(agent_id):
            _selected_agent_ids.append(agent_id)
    else:
        _selected_agent_ids = [agent_id]

    var selected_agents: Array = []
    for agent in _agents:
        if _selected_agent_ids.has(int(agent.get("id", -1))):
            selected_agents.append(agent)

    queue_redraw()
    emit_signal("agents_selected", selected_agents)

func deselect_all() -> void:
    _selected_agent_ids = []
    queue_redraw()
    emit_signal("agents_deselected")

func get_selected_agent_ids() -> Array:
    return _selected_agent_ids

func get_agent_at_world_position(world_pos: Vector2) -> Dictionary:
    var best_agent: Dictionary = {}
    var best_distance: float = INF
    var click_radius = _cell_size * 1.5

    for agent in _agents:
        var agent_pos = hex_to_pixel(agent.get("q", 0.0), agent.get("r", 0.0))
        var distance = world_pos.distance_to(agent_pos)
        if distance < click_radius and distance < best_distance:
            best_distance = distance
            best_agent = agent

    return best_agent

# =============================================================================
# RENDERIZADO
# =============================================================================

func _process(_delta: float) -> void:
    queue_redraw()

func _draw() -> void:
    var vis = _get_visible_rect()
    var ws = world_size()
    var offsets = _wrap_offsets()

    # 1. FONDO
    draw_rect(vis.grow(200.0), Color(0.12, 0.12, 0.18))

    # 2. REJILLA: copias envueltas para mundo continuo
    if _grid_cache_dirty:
        _build_grid_cache()

    var cam = get_viewport().get_camera_2d() if get_viewport() != null else null
    var zoom_x = cam.zoom.x if cam != null else 1.0

    if _cell_size * zoom_x >= 2.0:
        var grid_color = Color(GRID_COLOR.r, GRID_COLOR.g, GRID_COLOR.b, 0.35)
        for offset in offsets:
            if not Rect2(offset, ws).intersects(vis.grow(_cell_size * 2.0)):
                continue
            draw_set_transform(offset, 0.0, Vector2.ONE)
            draw_multiline(_grid_cache, grid_color, GRID_LINE_WIDTH)
        draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

    # 3. AGENTES (copias envueltas)
    var vis_grown = vis.grow(_cell_size * 2.0)

    for agent in _agents:
        var agent_pos = hex_to_pixel(agent.get("q", 0.0), agent.get("r", 0.0))
        var color = _get_agent_color(agent)
        var hex_radius = _cell_size * 0.7

        for offset in offsets:
            var pos = agent_pos + offset
            if not vis_grown.has_point(pos):
                continue
            _draw_hex(pos, hex_radius, color, true)

    # 4. ANILLO DE SELECCIÓN
    for agent in _agents:
        if _selected_agent_ids.has(int(agent.get("id", -1))):
            var agent_pos = hex_to_pixel(agent.get("q", 0.0), agent.get("r", 0.0))
            var hex_radius = _cell_size * 0.85

            for offset in offsets:
                var pos = agent_pos + offset
                if not vis_grown.has_point(pos):
                    continue
                _draw_hex(pos, hex_radius, SELECTION_RING_COLOR, false, SELECTION_RING_WIDTH)

    # 5. RECTÁNGULO DE SELECCIÓN (drag)
        if _is_dragging_selection:
            var top_left = Vector2(
                min(_selection_rect_start.x, _selection_rect_end.x),
                min(_selection_rect_start.y, _selection_rect_end.y)
            )
            var size = Vector2(
                abs(_selection_rect_end.x - _selection_rect_start.x),
                abs(_selection_rect_end.y - _selection_rect_start.y)
            )
            draw_rect(Rect2(top_left, size), Color(0.2, 0.6, 0.9, 0.2))
            draw_rect(Rect2(top_left, size), Color(0.2, 0.6, 0.9), false, 2.0)

func _get_agent_color(agent: Dictionary) -> Color:
    if agent.get("is_sick", false): return COLOR_SICK
    if agent.get("is_pregnant", false): return COLOR_PREGNANT
    if not agent.get("is_adult", true): return COLOR_YOUNG
    if agent.get("is_senior", false): return COLOR_SENIOR
    return SPECIES_COLORS.get(agent.get("species", "human"), DEFAULT_SPECIES_COLOR)
