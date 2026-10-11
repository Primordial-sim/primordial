extends Camera2D

var _world_width: int = 100
var _world_height: int = 100
var _cell_size: float = 10.0
var _is_panning: bool = false
var _pan_start: Vector2 = Vector2.ZERO
var _camera_start: Vector2 = Vector2.ZERO

# Tamaño del viewport (800x800)
const VIEWPORT_SIZE: float = 800.0

func set_world_dimensions(w: int, h: int) -> void:
    _world_width = w
    _world_height = h

func set_cell_size(s: float) -> void:
    _cell_size = s

func _get_world_size() -> Vector2:
    return Vector2(float(_world_width) * _cell_size, float(_world_height) * _cell_size)

func _clamp_camera_position() -> void:
    """Limita la posición de la cámara para que no muestre fuera del mundo."""
    var world_size = _get_world_size()
    var half_viewport = VIEWPORT_SIZE / 2.0 / zoom.x
    
    # Si el mundo es más pequeño que el viewport, centrar la cámara
    if world_size.x <= VIEWPORT_SIZE / zoom.x:
        position.x = world_size.x / 2.0
    else:
        position.x = clamp(position.x, half_viewport, world_size.x - half_viewport)
    
    if world_size.y <= VIEWPORT_SIZE / zoom.y:
        position.y = world_size.y / 2.0
    else:
        position.y = clamp(position.y, half_viewport, world_size.y - half_viewport)

func reset_view() -> void:
    position = _get_world_size() / 2.0
    zoom = Vector2.ONE
    _clamp_camera_position()

func _ready() -> void:
    make_current()
    reset_view()

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseButton:
        if event.button_index == MOUSE_BUTTON_RIGHT:
            _is_panning = event.pressed
            if _is_panning:
                _pan_start = event.position
                _camera_start = position
    elif event is InputEventMouseMotion and _is_panning:
        position = _camera_start - (event.position - _pan_start) / zoom
        _clamp_camera_position()  # Aplicar límites después de mover
    elif event is InputEventKey and event.pressed and event.keycode == KEY_C:
        reset_view()
    
    # También limitar al hacer zoom
    if event is InputEventMouseButton:
        if event.button_index == MOUSE_BUTTON_WHEEL_UP or event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
            # Esperar un frame para que el zoom se aplique y luego limitar
            call_deferred("_clamp_camera_position")