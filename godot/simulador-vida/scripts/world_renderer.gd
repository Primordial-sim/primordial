extends Node2D

signal agent_selected(agent_data: Dictionary)
signal agent_deselected()

var _world_width: int = 100
var _world_height: int = 100
var _cell_size: float = 10.0

const GRID_COLOR: Color = Color(0.5, 0.5, 0.6, 1.0)
const GRID_BORDER_COLOR: Color = Color(0.8, 0.8, 0.9, 1.0)
const SPECIES_COLORS: Dictionary = {
    "human": Color(0.298, 0.686, 0.314),
    "mammal": Color(0.545, 0.765, 0.290)
}

var _agents: Array = []
var _selected_agent_id: int = -1

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

func _draw() -> void:
    var w = float(_world_width) * _cell_size
    var h = float(_world_height) * _cell_size
    
    # Fondo del mundo
    draw_rect(Rect2(0, 0, w, h), Color(0.12, 0.12, 0.18))
    
    # Rejilla
    for x in range(_world_width + 1):
        var color = GRID_BORDER_COLOR if (x == 0 or x == _world_width) else GRID_COLOR
        draw_line(Vector2(x * _cell_size, 0), Vector2(x * _cell_size, h), color, 2.0 if (x == 0 or x == _world_width) else 1.0)
    
    for y in range(_world_height + 1):
        var color = GRID_BORDER_COLOR if (y == 0 or y == _world_height) else GRID_COLOR
        draw_line(Vector2(0, y * _cell_size), Vector2(w, y * _cell_size), color, 2.0 if (y == 0 or y == _world_height) else 1.0)
    
    # Agentes
    for agent in _agents:
        var ax = agent.get("x", 0.0) * _cell_size
        var ay = agent.get("y", 0.0) * _cell_size
        var size = _cell_size - 2.0
        draw_rect(Rect2(ax + 1, ay + 1, size, size), SPECIES_COLORS.get(agent.get("species", "human"), Color.WHITE))

func try_select_agent_at_position(local_pos: Vector2, camera_zoom: float, camera_pos: Vector2) -> bool:
    # Convertir posición local del viewport a posición del mundo
    var world_pos = (local_pos - Vector2(400, 400)) / camera_zoom + camera_pos
    
    var cell_x = int(world_pos.x / _cell_size)
    var cell_y = int(world_pos.y / _cell_size)
    
    for agent in _agents:
        if int(agent.get("x", 0)) == cell_x and int(agent.get("y", 0)) == cell_y:
            _selected_agent_id = int(agent.get("id", -1))
            queue_redraw()
            emit_signal("agent_selected", agent)
            return true
    return false