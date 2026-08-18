extends Camera2D
## Controlador de cámara: zoom con rueda, paneo con clic derecho, centrar con C.

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

const MIN_ZOOM: float = 0.2
const MAX_ZOOM: float = 10.0
const ZOOM_STEP: float = 0.1
const PAN_SPEED: float = 1.0

# =============================================================================
# ESTADO
# =============================================================================

var _is_panning: bool = false
var _pan_start: Vector2 = Vector2.ZERO
var _camera_start: Vector2 = Vector2.ZERO

# Dimensiones del mundo (dinámicas)
var _world_width: int = 100
var _world_height: int = 100
var _cell_size: float = 10.0

# =============================================================================
# API PÚBLICA
# =============================================================================

func set_world_dimensions(width: int, height: int) -> void:
    """Establece las dimensiones del mundo para centrar correctamente."""
    _world_width = width
    _world_height = height

func set_cell_size(size: float) -> void:
    """Establece el tamaño de celda para calcular el centro del mundo."""
    _cell_size = size

func reset_view() -> void:
    """Centra la cámara y resetea el zoom."""
    var world_pixel_width: float = float(_world_width) * _cell_size
    var world_pixel_height: float = float(_world_height) * _cell_size
    position = Vector2(world_pixel_width / 2.0, world_pixel_height / 2.0)
    zoom = Vector2.ONE

# =============================================================================
# CICLO DE VIDA
# =============================================================================

func _ready() -> void:
    make_current()
    reset_view()

func _unhandled_input(event: InputEvent) -> void:
    """Maneja zoom y paneo."""
    
    # ZOOM: Rueda del ratón
    if event is InputEventMouseButton:
        var mouse_event: InputEventMouseButton = event
        
        if mouse_event.button_index == MOUSE_BUTTON_WHEEL_UP:
            _zoom_in()
        elif mouse_event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
            _zoom_out()
        elif mouse_event.button_index == MOUSE_BUTTON_RIGHT:
            if mouse_event.pressed:
                _is_panning = true
                _pan_start = mouse_event.position
                _camera_start = position
            else:
                _is_panning = false
    
    # PANO: Movimiento del ratón con clic derecho
    if event is InputEventMouseMotion and _is_panning:
        var motion: InputEventMouseMotion = event
        var delta: Vector2 = (motion.position - _pan_start) / zoom
        position = _camera_start - delta * PAN_SPEED
    
    # CENTRAR: Tecla C
    if event is InputEventKey:
        var key_event: InputEventKey = event
        if key_event.pressed and key_event.keycode == KEY_C:
            reset_view()

# =============================================================================
# ZOOM
# =============================================================================

func _zoom_in() -> void:
    var new_zoom: float = zoom.x + ZOOM_STEP
    new_zoom = clamp(new_zoom, MIN_ZOOM, MAX_ZOOM)
    zoom = Vector2(new_zoom, new_zoom)

func _zoom_out() -> void:
    var new_zoom: float = zoom.x - ZOOM_STEP
    new_zoom = clamp(new_zoom, MIN_ZOOM, MAX_ZOOM)
    zoom = Vector2(new_zoom, new_zoom)
