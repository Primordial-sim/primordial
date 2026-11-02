extends Camera2D

var _world_width: int = 100
var _world_height: int = 100
var _cell_size: float = 8.0
var _is_panning: bool = false
var _pan_start: Vector2 = Vector2.ZERO
var _camera_start: Vector2 = Vector2.ZERO

# Permite hacer zoom-out hasta ver el mundo completo (~0.577)
const MIN_ZOOM: float = 1.00
const MAX_ZOOM: float = 4.0
const ZOOM_STEP: float = 0.25
const VIEWPORT_SIZE: float = 800.0

func set_world_dimensions(w: int, h: int) -> void:
    _world_width = w
    _world_height = h

func set_cell_size(s: float) -> void:
    _cell_size = s

func _get_world_size() -> Vector2:
    return Vector2(
        _cell_size * sqrt(3.0) * float(_world_width),
        _cell_size * 1.5 * float(_world_height)
    )

func _wrap_position(p: Vector2) -> Vector2:
    """Devuelve p envuelto al dominio fundamental del toro."""
    var ws = _get_world_size()
    var center = ws / 2.0

    var offset_x = fmod(p.x - center.x, ws.x)
    var offset_y = fmod(p.y - center.y, ws.y)

    if offset_x > ws.x / 2.0:
        offset_x -= ws.x
    elif offset_x < -ws.x / 2.0:
        offset_x += ws.x

    if offset_y > ws.y / 2.0:
        offset_y -= ws.y
    elif offset_y < -ws.y / 2.0:
        offset_y += ws.y

    return center + Vector2(offset_x, offset_y)

# Función pública para que otros scripts fuercen el wrapping
func wrap_camera_position() -> void:
    position = _wrap_position(position)

func reset_view() -> void:
    position = _get_world_size() / 2.0
    zoom = Vector2.ONE
    wrap_camera_position()

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
        var desired = _camera_start - (motion.position - _pan_start) / zoom
        var wrapped = _wrap_position(desired)
        # Compensar el salto de wrapping para que el arrastre sea continuo
        _camera_start += wrapped - desired
        position = wrapped
    elif event is InputEventKey:
        var key_event: InputEventKey = event
        if key_event.pressed and key_event.keycode == KEY_C:
            reset_view()

func _zoom_at_position(new_zoom: float, screen_pos: Vector2) -> void:
    var old_zoom = zoom.x
    new_zoom = clamp(new_zoom, MIN_ZOOM, MAX_ZOOM)
    if abs(new_zoom - old_zoom) < 0.01: return

    var world_pos_under_cursor = (screen_pos - Vector2(VIEWPORT_SIZE / 2.0, VIEWPORT_SIZE / 2.0)) / old_zoom + position
    zoom = Vector2(new_zoom, new_zoom)
    position = world_pos_under_cursor - (screen_pos - Vector2(VIEWPORT_SIZE / 2.0, VIEWPORT_SIZE / 2.0)) / new_zoom
    wrap_camera_position()
