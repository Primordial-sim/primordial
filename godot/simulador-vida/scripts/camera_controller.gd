extends Camera2D

var _world_width: int = 100
var _world_height: int = 100
var _cell_size: float = 8.0
var _is_panning: bool = false
var _pan_start: Vector2 = Vector2.ZERO
var _camera_start: Vector2 = Vector2.ZERO

const MIN_ZOOM: float = 1.0
const MAX_ZOOM: float = 4.0
const ZOOM_STEP: float = 0.25
const VIEWPORT_SIZE: float = 800.0

func set_world_dimensions(w: int, h: int) -> void:
    _world_width = w
    _world_height = h

func set_cell_size(s: float) -> void:
    _cell_size = s

func _get_world_size() -> Vector2:
    return Vector2(float(_world_width) * _cell_size, float(_world_height) * _cell_size)

func _wrap_camera_position() -> void:
    var world_w = float(_world_width) * _cell_size
    var world_h = float(_world_height) * _cell_size
    var center_x = world_w / 2.0
    var center_y = world_h / 2.0
    
    var offset_x = position.x - center_x
    var offset_y = position.y - center_y
    
    offset_x = fmod(offset_x, world_w)
    offset_y = fmod(offset_y, world_h)
    
    if offset_x > world_w / 2.0:
        offset_x -= world_w
    elif offset_x < -world_w / 2.0:
        offset_x += world_w
    
    if offset_y > world_h / 2.0:
        offset_y -= world_h
    elif offset_y < -world_h / 2.0:
        offset_y += world_h
    
    position.x = center_x + offset_x
    position.y = center_y + offset_y

func _zoom_at_position(new_zoom: float, screen_pos: Vector2) -> void:
    """Aplica zoom centrado en la posición de pantalla dada (cursor)."""
    var old_zoom = zoom.x
    new_zoom = clamp(new_zoom, MIN_ZOOM, MAX_ZOOM)
    
    if abs(new_zoom - old_zoom) < 0.01:
        return
    
    # Posición del mundo bajo el cursor ANTES del zoom
    var world_pos_under_cursor = (screen_pos - Vector2(VIEWPORT_SIZE / 2.0, VIEWPORT_SIZE / 2.0)) / old_zoom + position
    
    # Aplicar nuevo zoom
    zoom = Vector2(new_zoom, new_zoom)
    
    # Reposicionar cámara para que el mismo punto del mundo siga bajo el cursor
    position = world_pos_under_cursor - (screen_pos - Vector2(VIEWPORT_SIZE / 2.0, VIEWPORT_SIZE / 2.0)) / new_zoom
    
    _wrap_camera_position()

func reset_view() -> void:
    position = _get_world_size() / 2.0
    zoom = Vector2.ONE
    _wrap_camera_position()

func _ready() -> void:
    make_current()
    reset_view()

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseButton:
        var mouse_event: InputEventMouseButton = event
        if mouse_event.button_index == MOUSE_BUTTON_WHEEL_UP:
            _zoom_at_position(zoom.x + ZOOM_STEP, mouse_event.position)
        elif mouse_event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
            _zoom_at_position(zoom.x - ZOOM_STEP, mouse_event.position)
        elif mouse_event.button_index == MOUSE_BUTTON_RIGHT:
            _is_panning = mouse_event.pressed
            if _is_panning:
                _pan_start = mouse_event.position
                _camera_start = position
    elif event is InputEventMouseMotion and _is_panning:
        var motion: InputEventMouseMotion = event
        position = _camera_start - (motion.position - _pan_start) / zoom
        _wrap_camera_position()
    elif event is InputEventKey:
        var key_event: InputEventKey = event
        if key_event.pressed and key_event.keycode == KEY_C:
            reset_view()