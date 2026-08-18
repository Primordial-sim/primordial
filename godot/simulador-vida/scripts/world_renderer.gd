extends Node2D
## Dibuja el mundo (rejilla, agentes, indicadores de superposición).
## Este nodo está bajo la Camera2D, así que el zoom/paneo le afecta.
## También detecta clics sobre agentes y resalta la selección.

# =============================================================================
# SEÑALES
# =============================================================================

signal agent_selected(agent_data: Dictionary)
signal agent_deselected()

# =============================================================================
# CONFIGURACIÓN DEL MUNDO
# =============================================================================

## Dimensiones del mundo (se actualizan dinámicamente desde el servidor)
var _world_width: int = 100
var _world_height: int = 100

## Configuración de la rejilla
const DRAW_GRID: bool = true
const GRID_INTERVAL: int = 1
const GRID_COLOR: Color = Color(0.35, 0.35, 0.45, 0.5)
const GRID_BORDER_COLOR: Color = Color(0.6, 0.6, 0.7, 0.9)
const GRID_LINE_WIDTH: float = 1.5
const GRID_BORDER_WIDTH: float = 3.0

## Configuración del tamaño del agente
const AGENT_FILL_FACTOR: float = 1.0
const AGENT_MARGIN: float = 1.5

## Configuración de detección de superposiciones
const DETECT_OVERLAPS: bool = true
const OVERLAP_COLOR: Color = Color(1.0, 0.5, 0.0, 0.4)
const OVERLAP_BORDER_COLOR: Color = Color(1.0, 0.8, 0.0)

## Colores por estado del agente (sobrescriben el color de especie)
const COLOR_SICK: Color = Color(0.957, 0.263, 0.212)
const COLOR_PREGNANT: Color = Color(1.0, 0.757, 0.027)
const COLOR_YOUNG: Color = Color(0.129, 0.588, 0.953)
const COLOR_SENIOR: Color = Color(0.620, 0.620, 0.620)

## Colores por especie (arquetipo biológico)
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

## Configuración de selección
const SELECTION_RING_COLOR: Color = Color(1.0, 1.0, 1.0)
const SELECTION_RING_WIDTH: float = 2.0
const SELECTION_INNER_COLOR: Color = Color(1.0, 1.0, 1.0, 0.3)

# =============================================================================
# ESTADO
# =============================================================================

var _agents: Array = []
var _cell_occupancy: Dictionary = {}
var _overlapping_cells: Array = []
var _cell_size: float = 10.0
var _agent_radius: float = 5.0

## Estado de selección
var _selected_agent_id: int = -1
var _selected_agent: Dictionary = {}

# =============================================================================
# API PÚBLICA
# =============================================================================

func update_agents(agents: Array) -> void:
    """Actualiza la lista de agentes a dibujar."""
    _agents = agents
    if DETECT_OVERLAPS:
        _update_cell_occupancy()
    queue_redraw()

func set_cell_size(size: float) -> void:
    """Establece el tamaño de cada casilla en píxeles del mundo."""
    _cell_size = size
    _agent_radius = (_cell_size * AGENT_FILL_FACTOR) / 2.0
    queue_redraw()

func set_world_dimensions(width: int, height: int) -> void:
    """Establece las dimensiones del mundo."""
    if width != _world_width or height != _world_height:
        _world_width = width
        _world_height = height
        queue_redraw()

# =============================================================================
# SELECCIÓN DE AGENTES
# =============================================================================

func try_select_agent_at_position(
    screen_pos: Vector2,
    camera_zoom: float,
    camera_position: Vector2,
    viewport_size: Vector2
) -> bool:
    """Intenta seleccionar un agente en la posición de pantalla dada."""
    var world_pos: Vector2 = _screen_to_world(screen_pos, camera_zoom, camera_position, viewport_size)
    
    # Calcular la casilla donde se hizo clic
    var clicked_cell_x: int = int(floor(world_pos.x / _cell_size))
    var clicked_cell_y: int = int(floor(world_pos.y / _cell_size))
    
    # Buscar un agente en esa casilla
    for agent in _agents:
        var agent_x: int = int(floor(agent.get("x", 0.0)))
        var agent_y: int = int(floor(agent.get("y", 0.0)))
        
        if agent_x == clicked_cell_x and agent_y == clicked_cell_y:
            _selected_agent_id = int(agent.get("id", -1))
            _selected_agent = agent
            queue_redraw()
            emit_signal("agent_selected", agent)
            return true
    
    # No se encontró agente en la casilla clickeada
    deselect_agent()
    return false

func deselect_agent() -> void:
    """Deselecciona el agente actual."""
    if _selected_agent_id != -1:
        _selected_agent_id = -1
        _selected_agent = {}
        queue_redraw()
        emit_signal("agent_deselected")

func get_selected_agent_id() -> int:
    return _selected_agent_id

# =============================================================================
# DETECCIÓN DE SUPERPOSICIONES
# =============================================================================

func _update_cell_occupancy() -> void:
    _cell_occupancy.clear()
    _overlapping_cells.clear()
    
    for agent in _agents:
        var x: int = int(round(agent.get("x", 0.0)))
        var y: int = int(round(agent.get("y", 0.0)))
        var cell_key: String = "%d,%d" % [x, y]
        
        if _cell_occupancy.has(cell_key):
            _cell_occupancy[cell_key] += 1
        else:
            _cell_occupancy[cell_key] = 1
    
    for cell_key in _cell_occupancy:
        if _cell_occupancy[cell_key] > 1:
            _overlapping_cells.append(cell_key)

# =============================================================================
# CONVERSIÓN DE COORDENADAS
# =============================================================================

func _world_to_local(world_x: float, world_y: float) -> Vector2:
    """Convierte coordenadas del mundo a coordenadas locales de dibujo."""
    return Vector2((world_x + 0.5) * _cell_size, (world_y + 0.5) * _cell_size)

func _screen_to_world(
    screen_pos: Vector2,
    camera_zoom: float,
    camera_position: Vector2,
    viewport_size: Vector2
) -> Vector2:
    """Convierte coordenadas de pantalla a coordenadas del mundo."""
    var centered: Vector2 = screen_pos - viewport_size / 2.0
    var world: Vector2 = centered / camera_zoom + camera_position
    return world

# =============================================================================
# DIBUJADO
# =============================================================================

func _draw() -> void:
    # 1. Primero los indicadores de superposición
    if DETECT_OVERLAPS:
        _draw_overlap_indicators()
    
    # 2. Luego los agentes
    _draw_agents()
    
    # 3. Después la rejilla (las líneas se dibujan ENCIMA de los agentes)
    if DRAW_GRID:
        _draw_grid()
    
    # 4. Al final la selección (encima de todo)
    _draw_selection_highlight()

func _draw_grid() -> void:
    """Dibuja la rejilla del mundo usando dimensiones dinámicas."""
    var x: int = 0
    while x <= _world_width:
        var start: Vector2 = Vector2(float(x) * _cell_size, 0.0)
        var end: Vector2 = Vector2(float(x) * _cell_size, float(_world_height) * _cell_size)
        
        var is_border: bool = (x == 0 or x == _world_width)
        var color: Color = GRID_BORDER_COLOR if is_border else GRID_COLOR
        var width: float = GRID_BORDER_WIDTH if is_border else GRID_LINE_WIDTH
        
        draw_line(start, end, color, width)
        x += GRID_INTERVAL
    
    var y: int = 0
    while y <= _world_height:
        var start: Vector2 = Vector2(0.0, float(y) * _cell_size)
        var end: Vector2 = Vector2(float(_world_width) * _cell_size, float(y) * _cell_size)
        
        var is_border: bool = (y == 0 or y == _world_height)
        var color: Color = GRID_BORDER_COLOR if is_border else GRID_COLOR
        var width: float = GRID_BORDER_WIDTH if is_border else GRID_LINE_WIDTH
        
        draw_line(start, end, color, width)
        y += GRID_INTERVAL

func _draw_overlap_indicators() -> void:
    """Dibuja indicadores en las casillas donde hay más de un agente."""
    for cell_key in _overlapping_cells:
        var parts: PackedStringArray = cell_key.split(",")
        if parts.size() != 2:
            continue
        
        var cell_x: int = int(parts[0])
        var cell_y: int = int(parts[1])
        var count: int = _cell_occupancy[cell_key]
        
        var cell_top_left: Vector2 = Vector2(float(cell_x) * _cell_size, float(cell_y) * _cell_size)
        
        var cell_rect: Rect2 = Rect2(cell_top_left, Vector2(_cell_size, _cell_size))
        draw_rect(cell_rect, OVERLAP_COLOR)
        draw_rect(cell_rect, OVERLAP_BORDER_COLOR, false, 2.0)
        
        if _cell_size >= 12.0:
            draw_string(
                ThemeDB.fallback_font,
                cell_top_left + Vector2(2, _cell_size - 2),
                str(count),
                HORIZONTAL_ALIGNMENT_LEFT,
                -1,
                int(_cell_size * 0.7),
                Color.WHITE
            )

func _draw_agents() -> void:
    """Dibuja cada agente como un cuadrado dentro de su casilla."""
    for agent in _agents:
        var world_x: float = agent.get("x", 0.0)
        var world_y: float = agent.get("y", 0.0)
        var center: Vector2 = _world_to_local(world_x, world_y)
        var color: Color = _get_agent_color(agent)
        
        var agent_size: float = _cell_size - AGENT_MARGIN * 2.0
        var top_left: Vector2 = center - Vector2(agent_size / 2.0, agent_size / 2.0)
        var rect: Rect2 = Rect2(top_left, Vector2(agent_size, agent_size))
        
        draw_rect(rect, color)
        
        if _cell_size >= 8.0:
            draw_rect(rect, Color(0, 0, 0, 0.3), false, 1.0)

func _draw_selection_highlight() -> void:
    """Dibuja un borde de resaltado alrededor del agente seleccionado."""
    if _selected_agent_id == -1:
        return
    
    for agent in _agents:
        if int(agent.get("id", -1)) == _selected_agent_id:
            var world_x: float = agent.get("x", 0.0)
            var world_y: float = agent.get("y", 0.0)
            var center: Vector2 = _world_to_local(world_x, world_y)
            
            var selection_margin: float = 2.0
            var top_left: Vector2 = center - Vector2(
                _cell_size / 2.0 + selection_margin,
                _cell_size / 2.0 + selection_margin
            )
            var rect: Rect2 = Rect2(
                top_left,
                Vector2(
                    _cell_size + selection_margin * 2.0,
                    _cell_size + selection_margin * 2.0
                )
            )
            
            draw_rect(rect, SELECTION_RING_COLOR, false, SELECTION_RING_WIDTH)
            
            var inner_top_left: Vector2 = center - Vector2(
                _cell_size / 2.0 + selection_margin + 3.0,
                _cell_size / 2.0 + selection_margin + 3.0
            )
            var inner_rect: Rect2 = Rect2(
                inner_top_left,
                Vector2(
                    _cell_size + (selection_margin + 3.0) * 2.0,
                    _cell_size + (selection_margin + 3.0) * 2.0
                )
            )
            draw_rect(inner_rect, SELECTION_INNER_COLOR, false, 1.0)
            
            _selected_agent = agent
            break

func _get_agent_color(agent: Dictionary) -> Color:
    """Determina el color del agente según su especie y estado."""
    if agent.get("is_sick", false):
        return COLOR_SICK
    if agent.get("is_pregnant", false):
        return COLOR_PREGNANT
    if not agent.get("is_adult", true):
        return COLOR_YOUNG
    if agent.get("is_senior", false):
        return COLOR_SENIOR
    
    var species: String = agent.get("species", "human")
    return SPECIES_COLORS.get(species, DEFAULT_SPECIES_COLOR)
