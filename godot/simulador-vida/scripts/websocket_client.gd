extends Node2D

const SERVER_URL: String = "ws://localhost:8765"

@onready var ui_renderer: Control = $UI/UIRenderer
@onready var world_container: SubViewportContainer = $UI/WorldContainer
@onready var world_renderer: Node2D = $UI/WorldContainer/WorldViewport/World
@onready var camera: Camera2D = $UI/WorldContainer/WorldViewport/World/Camera2D

var _peer: WebSocketPeer = null
var _agents: Array = []
var _stats: Dictionary = {}
var _tick_count: int = 0
var _current_day: float = 0.0
var _is_connected: bool = false
var _was_connected_before: bool = false
var _cell_size: float = 10.0
var _world_width: int = 100
var _world_height: int = 100
var _is_paused: bool = false
var _current_speed: float = 1.0

func _ready() -> void:
    _cell_size = 1000.0 / float(_world_width)
    world_renderer.set_cell_size(_cell_size)
    world_renderer.set_world_dimensions(_world_width, _world_height)
    camera.set_world_dimensions(_world_width, _world_height)
    camera.reset_view()
    world_renderer.agent_selected.connect(func(d): ui_renderer.show_agent_inspector(d))
    world_renderer.agent_deselected.connect(func(): ui_renderer.hide_agent_inspector())
    _connect_to_server()

func _process(_delta: float) -> void:
    if _peer != null:
        _peer.poll()
        _check_connection_state()
        _receive_data()

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
        if event.pressed:
            # 1. Botones UI
            var btn = ui_renderer.get_button_at_position(event.position)
            if not btn.is_empty():
                if btn["action"] == "pause": _toggle_pause()
                elif btn["action"] == "speed": _set_speed(btn["speed"])
                return
            
            # 2. Clic en el mundo (SubViewport)
            if world_container.get_global_rect().has_point(event.position):
                var local_pos = event.position - world_container.global_position
                var selected = world_renderer.try_select_agent_at_position(local_pos, camera.zoom.x, camera.position)
                if not selected:
                    # Deseleccionar si clic en vacío (necesitaríamos señal para esto, simplificado aquí)
                    pass
            return

func _toggle_pause() -> void:
    _is_paused = not _is_paused
    _send_command({"type": "pause" if _is_paused else "resume"})
    ui_renderer.update_control_state(_is_paused, _current_speed)

func _set_speed(s: float) -> void:
    _current_speed = s
    _send_command({"type": "set_speed", "speed": s})
    ui_renderer.update_control_state(_is_paused, _current_speed)

func _send_command(cmd: Dictionary) -> void:
    if _peer and _peer.get_ready_state() == WebSocketPeer.STATE_OPEN:
        _peer.send_text(JSON.stringify(cmd))

func _connect_to_server() -> void:
    _peer = WebSocketPeer.new()
    _peer.connect_to_url(SERVER_URL)

func _check_connection_state() -> void:
    if _peer.get_ready_state() == WebSocketPeer.STATE_OPEN:
        if not _was_connected_before:
            _is_connected = true
            _was_connected_before = true
            ui_renderer.update_connection_status(true)
            _send_command({"type": "get_presets"})
    elif _peer.get_ready_state() == WebSocketPeer.STATE_CLOSED:
        if _is_connected:
            _is_connected = false
            _was_connected_before = false
            ui_renderer.update_connection_status(false)
            get_tree().create_timer(2.0).timeout.connect(_connect_to_server)

func _receive_data() -> void:
    while _peer.get_available_packet_count() > 0:
        var text = _peer.get_packet().get_string_from_utf8()
        if text.is_empty(): continue
        var json = JSON.new()
        if json.parse(text) == OK:
            _handle_message(json.get_data())

func _handle_message(data: Dictionary) -> void:
    if data.get("type") == "tick":
        _agents = data.get("agents", [])
        _stats = data.get("stats", {})
        world_renderer.update_agents(_agents)
        ui_renderer.update_tick_info(data.get("tick", 0), data.get("day", 0.0), _agents.size())
        ui_renderer.update_stats(_stats)
    elif data.get("type") == "presets_config":
        ui_renderer.update_presets(data.get("presets", []))