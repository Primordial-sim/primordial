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

func update_agents(agents: Array) -> void:
    _agents = agents
    queue_redraw()

func set_cell_size(size: float) -> void:
    _cell_size = size
    queue_redraw()

func set_world_dimensions(width: int, height: int) -> void:
    _world_width = width
    _world_height = height
    queue_redraw()

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
    
    # Calcular el rectángulo de selección
    var top_left = Vector2(min(_selection_rect_start.x, _selection_rect_end.x), 
                           min(_selection_rect_start.y, _selection_rect_end.y))
    var bottom_right = Vector2(max(_selection_rect_start.x, _selection_rect_end.x), 
                               max(_selection_rect_start.y, _selection_rect_end.y))
    var selection_rect = Rect2(top_left, bottom_right - top_left)
    
    var selected_agents: Array = []
    
    # Verificar si la CELDA del agente intersecta con el rectángulo de selección
    for agent in _agents:
        var ax = agent.get("x", 0.0) * _cell_size
        var ay = agent.get("y", 0.0) * _cell_size
        
        # Crear el rectángulo de la celda del agente
        var agent_rect = Rect2(ax, ay, _cell_size, _cell_size)
        
        # Si la celda del agente intersecta con el rectángulo de selección, se selecciona
        if selection_rect.intersects(agent_rect) or selection_rect.has_point(agent_rect.get_center()):
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

func _draw() -> void:
    var w = float(_world_width) * _cell_size
    var h = float(_world_height) * _cell_size
    
    # 1. FONDO CONTINUO
    draw_rect(Rect2(Vector2(-w, -h), Vector2(w * 3.0, h * 3.0)), Color(0.12, 0.12, 0.18))
    
    # 2. REJILLA UNIFORME
    for x in range(-_world_width, _world_width * 2 + 1):
        var px = x * _cell_size
        draw_line(Vector2(px, -h), Vector2(px, h * 2.0), GRID_COLOR, GRID_LINE_WIDTH)
    
    for y in range(-_world_height, _world_height * 2 + 1):
        var py = y * _cell_size
        draw_line(Vector2(-w, py), Vector2(w * 2.0, py), GRID_COLOR, GRID_LINE_WIDTH)
    
    # 3. AGENTES
    var offsets = [
        Vector2(-w, -h), Vector2(0, -h), Vector2(w, -h),
        Vector2(-w, 0),  Vector2(0, 0),  Vector2(w, 0),
        Vector2(-w, h),  Vector2(0, h),  Vector2(w, h)
    ]
    
    for agent in _agents:
        var ax = agent.get("x", 0.0) * _cell_size
        var ay = agent.get("y", 0.0) * _cell_size
        var size = _cell_size - 2.0
        var color = _get_agent_color(agent)
        
        for offset in offsets:
            draw_rect(Rect2(offset.x + ax + 1, offset.y + ay + 1, size, size), color)
    
    # 4. SELECCIÓN INDIVIDUAL (en las 9 posiciones del mosaico)
    for agent in _agents:
        if _selected_agent_ids.has(int(agent.get("id", -1))):
            var ax = agent.get("x", 0.0) * _cell_size
            var ay = agent.get("y", 0.0) * _cell_size
            var margin = 2.0
            
            for offset in offsets:
                var top_left = Vector2(offset.x + ax - margin, offset.y + ay - margin)
                draw_rect(Rect2(top_left, Vector2(_cell_size + margin*2.0, _cell_size + margin*2.0)), 
                         SELECTION_RING_COLOR, false, SELECTION_RING_WIDTH)
    
    # 5. RECTÁNGULO DE SELECCIÓN
    if _is_dragging_selection:
        var top_left = Vector2(min(_selection_rect_start.x, _selection_rect_end.x), 
                               min(_selection_rect_start.y, _selection_rect_end.y))
        var size = Vector2(abs(_selection_rect_end.x - _selection_rect_start.x), 
                          abs(_selection_rect_end.y - _selection_rect_start.y))
        var selection_rect = Rect2(top_left, size)
        draw_rect(selection_rect, Color(0.2, 0.6, 0.9, 0.2))
        draw_rect(selection_rect, Color(0.2, 0.6, 0.9), false, 2.0)

func _get_agent_color(agent: Dictionary) -> Color:
    if agent.get("is_sick", false): return COLOR_SICK
    if agent.get("is_pregnant", false): return COLOR_PREGNANT
    if not agent.get("is_adult", true): return COLOR_YOUNG
    if agent.get("is_senior", false): return COLOR_SENIOR
    return SPECIES_COLORS.get(agent.get("species", "human"), DEFAULT_SPECIES_COLOR)