extends Control # Cambiado de Node2D a Control para que coincida con la raíz de main.tscn

const SERVER_URL: String = "ws://localhost:8765"

# Nuevas rutas coincidentes con el main.tscn actualizado
@onready var ui_layout: Control = $GlobalVBox # El script ui_layout.gd está aquí
@onready var world_container: SubViewportContainer = $GlobalVBox/MiddleArea/CenterArea/WorldContainer
@onready var world_renderer: Node2D = $GlobalVBox/MiddleArea/CenterArea/WorldContainer/WorldViewport/World
@onready var camera: Camera2D = $GlobalVBox/MiddleArea/CenterArea/WorldContainer/WorldViewport/World/Camera2D

var _peer: WebSocketPeer = null
var _agents: Array = []
var _stats: Dictionary = {}
var _tick_count: int = 0
var _current_day: float = 0.0
var _is_connected: bool = false
var _was_connected_before: bool = false
var _cell_size: float = 8.0
var _world_width: int = 100
var _world_height: int = 100
var _is_dragging: bool = false
var _drag_start_pos: Vector2 = Vector2.ZERO
var _follow_agent_id: int = -1

func _ready() -> void:
    _cell_size = min(
        800.0 / (sqrt(3.0) * float(_world_width)),
        800.0 / (1.5 * float(_world_height))
    )
    world_renderer.set_cell_size(_cell_size)
    world_renderer.set_world_dimensions(_world_width, _world_height)
    camera.set_world_dimensions(_world_width, _world_height)
    camera.set_cell_size(_cell_size)
    camera.reset_view()
    camera.position = world_renderer.hex_to_pixel(float(_world_width) / 2.0, float(_world_height) / 2.0)
    camera.wrap_camera_position()

    # Conectar señales del renderer
    world_renderer.agents_selected.connect(_on_agents_selected)
    world_renderer.agents_deselected.connect(_on_agents_deselected)

    # Conectar la UI con este script para enviar mensajes al servidor
    ui_layout.notify_pause = _send_pause
    ui_layout.notify_speed = _send_speed

    _connect_to_server()

func _send_pause(is_paused: bool) -> void:
    if _peer != null and _peer.get_ready_state() == WebSocketPeer.STATE_OPEN:
        var msg = {"action": "pause", "value": is_paused}
        _peer.send_text(JSON.stringify(msg))

func _send_speed(speed: float) -> void:
    if _peer != null and _peer.get_ready_state() == WebSocketPeer.STATE_OPEN:
        var msg = {"action": "speed", "value": speed}
        _peer.send_text(JSON.stringify(msg))

func _process(_delta: float) -> void:
    if _peer != null:
        _peer.poll()
        _check_connection_state()
        _receive_data()

    if _follow_agent_id != -1:
        _update_follow_camera()

func _update_follow_camera() -> void:
    for agent in _agents:
        if int(agent.get("id", -1)) == _follow_agent_id:
            var aq = agent.get("q", 0.0)
            var ar = agent.get("r", 0.0)
            camera.position = world_renderer.hex_to_pixel(aq, ar)
            camera.wrap_camera_position()
            return

# --- Manejo de Input (Selección y Paneo) ---
# Nota: El paneo con botón derecho ahora lo maneja camera_controller.gd en _unhandled_input.
# Aquí solo manejamos la selección con clic izquierdo en el mundo.
func _input(event: InputEvent) -> void:
    if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
        if event.pressed:
            if world_container.get_global_rect().has_point(event.position):
                var local_pos = event.position - world_container.global_position
                var world_pos = _screen_to_world(local_pos)
                _is_dragging = true
                _drag_start_pos = world_pos
                world_renderer.start_selection_drag(world_pos)
        else:
            if _is_dragging:
                _is_dragging = false
                var local_pos = event.position - world_container.global_position
                var world_pos = _screen_to_world(local_pos)
                var drag_distance = world_pos.distance_to(_drag_start_pos)

                if drag_distance < 5.0:
                    var clicked_agent = world_renderer.get_agent_at_world_position(world_pos)
                    if not clicked_agent.is_empty():
                        var add_to_selection = Input.is_key_pressed(KEY_CTRL)
                        world_renderer.select_agent(int(clicked_agent.get("id", -1)), add_to_selection)
                    else:
                        if not Input.is_key_pressed(KEY_CTRL):
                            world_renderer.deselect_all()
                else:
                    var add_to_selection = Input.is_key_pressed(KEY_CTRL)
                    var selected_agents = world_renderer.finish_selection_drag(add_to_selection)
                    if selected_agents.size() > 0:
                        _on_agents_selected(selected_agents)
    elif event is InputEventMouseMotion and _is_dragging:
        var local_pos = event.position - world_container.global_position
        var world_pos = _screen_to_world(local_pos)
        world_renderer.update_selection_drag(world_pos)
    elif event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
        world_renderer.deselect_all()

func _screen_to_world(screen_pos: Vector2) -> Vector2:
    # Ajustado para funcionar dentro del CenterArea
    var viewport_center = Vector2(400, 400) # Asumiendo SubViewport de 800x800
    return (screen_pos - viewport_center) / camera.zoom.x + camera.position

func _on_agents_selected(agents_data: Array) -> void:
    # Aquí iría la lógica para mostrar datos en el Panel Inferior
    print("Agentes seleccionados: ", agents_data.size())

func _on_agents_deselected() -> void:
    print("Selección limpiada")

func _center_on_selected_agent() -> void:
    var selected_ids = world_renderer.get_selected_agent_ids()
    if selected_ids.size() > 0:
        for agent in _agents:
            if int(agent.get("id", -1)) == selected_ids[0]:
                var aq = agent.get("q", 0.0)
                var ar = agent.get("r", 0.0)
                camera.position = world_renderer.hex_to_pixel(aq, ar)
                camera.wrap_camera_position()
                return

func _connect_to_server() -> void:
    _peer = WebSocketPeer.new()
    var error = _peer.connect_to_url(SERVER_URL)
    if error != OK:
        print("Error conectando al servidor WebSocket: ", error)

func _check_connection_state() -> void:
    var state = _peer.get_ready_state()
    if state == WebSocketPeer.STATE_OPEN:
        if not _was_connected_before:
            _is_connected = true
            _was_connected_before = true
    elif state == WebSocketPeer.STATE_CLOSED:
        if _was_connected_before:
            _is_connected = false
            _was_connected_before = false
            await get_tree().create_timer(3.0).timeout
            _connect_to_server()

func _receive_data() -> void:
    while _peer.get_available_packet_count() > 0:
        var packet = _peer.get_packet()
        var json_string = packet.get_string_from_utf8()
        var json = JSON.new()
        var parse_result = json.parse(json_string)

        if parse_result == OK:
            var data = json.get_data()
            if data is Dictionary:
                _process_server_message(data)

func _process_server_message(data: Dictionary) -> void:
    if data.has("type"):
        var msg_type = data["type"]

        if msg_type == "tick":
            _tick_count = data.get("tick", 0)
            _current_day = data.get("day", 0.0)
            _agents = data.get("agents", [])
            _stats = data.get("stats", {})

            world_renderer.update_agents(_agents)
            # Actualizar la nueva UI
            ui_layout.update_tick_info(_tick_count, _current_day, _agents.size())

        elif msg_type == "agent_died":
            var dead_id = data.get("id", -1)
            if _follow_agent_id == dead_id:
                _follow_agent_id = -1
            var selected = world_renderer.get_selected_agent_ids()
            if selected.has(dead_id):
                world_renderer.deselect_all()

        elif msg_type == "connection_ack":
            _is_connected = true
            _was_connected_before = true
            print("Conectado al servidor de simulación")

        elif msg_type == "error":
            print("Error del servidor: ", data.get("message", "desconocido"))
