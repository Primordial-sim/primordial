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
var _cell_size: float = 8.0
var _world_width: int = 100
var _world_height: int = 100
var _is_paused: bool = false
var _current_speed: float = 1.0

var _is_dragging: bool = false
var _drag_start_pos: Vector2 = Vector2.ZERO
var _follow_agent_id: int = -1

func _ready() -> void:
    _cell_size = 800.0 / float(_world_width)
    world_renderer.set_cell_size(_cell_size)
    world_renderer.set_world_dimensions(_world_width, _world_height)
    camera.set_world_dimensions(_world_width, _world_height)
    camera.set_cell_size(_cell_size)
    camera.reset_view()
    world_renderer.agents_selected.connect(_on_agents_selected)
    world_renderer.agents_deselected.connect(_on_agents_deselected)
    _connect_to_server()

func _process(_delta: float) -> void:
    if _peer != null:
        _peer.poll()
        _check_connection_state()
        _receive_data()
    if camera != null:
        ui_renderer.update_zoom_level(camera.zoom.x)
    
    if _follow_agent_id != -1:
        _update_follow_camera()

func _update_follow_camera() -> void:
    for agent in _agents:
        if int(agent.get("id", -1)) == _follow_agent_id:
            var world_x = agent.get("x", 0.0) * _cell_size + _cell_size / 2.0
            var world_y = agent.get("y", 0.0) * _cell_size + _cell_size / 2.0
            camera.position = Vector2(world_x, world_y)
            camera.wrap_camera_position()
            return

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseButton:
        var mouse_event: InputEventMouseButton = event
        if mouse_event.button_index == MOUSE_BUTTON_LEFT:
            if mouse_event.pressed:
                var btn = ui_renderer.get_button_at_position(mouse_event.position)
                if not btn.is_empty():
                    if btn["action"] == "pause":
                        _toggle_pause()
                    elif btn["action"] == "speed":
                        _set_speed(btn["speed"])
                    elif btn["action"] == "center_agent":
                        _center_on_selected_agent()
                    elif btn["action"] == "follow_agent":
                        _toggle_follow_agent()
                    elif btn["action"] == "toggle_section":
                        ui_renderer.toggle_section(btn["section"])
                    return
                
                if world_container.get_global_rect().has_point(mouse_event.position):
                    var local_pos = mouse_event.position - world_container.global_position
                    var world_pos = _screen_to_world(local_pos)
                    _is_dragging = true
                    _drag_start_pos = world_pos
                    world_renderer.start_selection_drag(world_pos)
            else:
                if _is_dragging:
                    _is_dragging = false
                    var local_pos = mouse_event.position - world_container.global_position
                    var world_pos = _screen_to_world(local_pos)
                    var drag_distance = world_pos.distance_to(_drag_start_pos)
                    
                    if drag_distance < 5.0:
                        var clicked_agent = _get_agent_at_world_position(world_pos)
                        if not clicked_agent.is_empty():
                            var add_to_selection = Input.is_key_pressed(KEY_CTRL)
                            world_renderer.select_agent(int(clicked_agent.get("id", -1)), add_to_selection)
                        else:
                            world_renderer.deselect_all()
                    else:
                        var add_to_selection = Input.is_key_pressed(KEY_CTRL)
                        var selected_agents = world_renderer.finish_selection_drag(add_to_selection)
                        if selected_agents.size() > 0:
                            _on_agents_selected(selected_agents)
                    world_renderer.cancel_selection_drag()
    
    elif event is InputEventMouseMotion:
        if _is_dragging:
            var local_pos = event.position - world_container.global_position
            var world_pos = _screen_to_world(local_pos)
            world_renderer.update_selection_drag(world_pos)
            
    elif event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
        world_renderer.deselect_all()

func _center_on_selected_agent() -> void:
    var selected_ids = world_renderer.get_selected_agent_ids()
    if selected_ids.size() == 1:
        var target_id = selected_ids[0]
        for agent in _agents:
            if int(agent.get("id", -1)) == target_id:
                var world_x = agent.get("x", 0.0) * _cell_size + _cell_size / 2.0
                var world_y = agent.get("y", 0.0) * _cell_size + _cell_size / 2.0
                camera.position = Vector2(world_x, world_y)
                camera.wrap_camera_position()
                break

func _toggle_follow_agent() -> void:
    var selected_ids = world_renderer.get_selected_agent_ids()
    if selected_ids.size() == 1:
        var target_id = selected_ids[0]
        if _follow_agent_id == target_id:
            _follow_agent_id = -1
            ui_renderer.set_following_state(false)
        else:
            _follow_agent_id = target_id
            ui_renderer.set_following_state(true)
            _update_follow_camera()

func _screen_to_world(screen_pos: Vector2) -> Vector2:
    var viewport_center = Vector2(400, 400)
    return (screen_pos - viewport_center) / camera.zoom.x + camera.position

func _get_agent_at_world_position(world_pos: Vector2) -> Dictionary:
    var world_px_w = float(_world_width) * _cell_size
    var world_px_h = float(_world_height) * _cell_size
    
    var logical_x = fmod(world_pos.x, world_px_w)
    var logical_y = fmod(world_pos.y, world_px_h)
    if logical_x < 0: logical_x += world_px_w
    if logical_y < 0: logical_y += world_px_h
    
    var cell_x = int(logical_x / _cell_size)
    var cell_y = int(logical_y / _cell_size)
    
    for agent in _agents:
        if int(agent.get("x", 0)) == cell_x and int(agent.get("y", 0)) == cell_y:
            return agent
    return {}

func _on_agents_selected(agents_data: Array) -> void:
    if _follow_agent_id != -1:
        _follow_agent_id = -1
        ui_renderer.set_following_state(false)
        
    if agents_data.size() == 1:
        var agent_id = int(agents_data[0].get("id", -1))
        ui_renderer.show_agent_inspector_loading(agent_id)
        _send_command({"type": "request_agent_details", "agent_id": agent_id})
    elif agents_data.size() > 1:
        ui_renderer.show_group_inspector(agents_data)

func _on_agents_deselected() -> void:
    _follow_agent_id = -1
    ui_renderer.set_following_state(false)
    ui_renderer.hide_agent_inspector()
    ui_renderer.hide_group_inspector()

func _toggle_pause() -> void:
    if not _is_connected: return
    _is_paused = not _is_paused
    _send_command({"type": "pause" if _is_paused else "resume"})
    ui_renderer.update_control_state(_is_paused, _current_speed)

func _set_speed(multiplier: float) -> void:
    if not _is_connected: return
    _current_speed = multiplier
    _send_command({"type": "set_speed", "multiplier": int(multiplier)})
    ui_renderer.update_control_state(_is_paused, _current_speed)

func _send_command(cmd: Dictionary) -> void:
    if _peer == null or _peer.get_ready_state() != WebSocketPeer.STATE_OPEN: return
    _peer.send_text(JSON.stringify(cmd))

func _connect_to_server() -> void:
    _peer = WebSocketPeer.new()
    _peer.connect_to_url(SERVER_URL)

func _check_connection_state() -> void:
    var state: int = _peer.get_ready_state()
    match state:
        WebSocketPeer.STATE_OPEN:
            _is_connected = true
            if not _was_connected_before:
                _was_connected_before = true
                ui_renderer.update_connection_status(true)
                ui_renderer.update_control_state(_is_paused, _current_speed)
                _send_command({"type": "get_presets"})
        WebSocketPeer.STATE_CLOSED:
            if _is_connected:
                _is_connected = false
                _was_connected_before = false
                ui_renderer.update_connection_status(false)
                get_tree().create_timer(2.0).timeout.connect(_connect_to_server)

func _receive_data() -> void:
    while _peer.get_available_packet_count() > 0:
        var text: String = _peer.get_packet().get_string_from_utf8()
        if text.is_empty(): continue
        var json: JSON = JSON.new()
        if json.parse(text) == OK:
            _handle_message(json.get_data())

func _handle_message(data: Dictionary) -> void:
    var message_type: String = data.get("type", "")
    match message_type:
        "tick":
            _tick_count = data.get("tick", 0)
            _current_day = data.get("day", 0.0)
            _agents = data.get("agents", [])
            _stats = data.get("stats", {})
            world_renderer.update_agents(_agents)
            ui_renderer.update_tick_info(_tick_count, _current_day, _agents.size())
            ui_renderer.update_stats(_stats)
            
            var selected_ids = world_renderer.get_selected_agent_ids()
            if selected_ids.size() == 1:
                var still_alive = false
                for agent in _agents:
                    if int(agent.get("id", -1)) == selected_ids[0]:
                        still_alive = true
                        break
                if not still_alive:
                    world_renderer.deselect_all()
                    
        "agent_details":
            var details: Dictionary = data.get("data", {})
            ui_renderer.show_agent_full_inspector(details)
            
        "agent_details_error":
            ui_renderer.hide_agent_inspector()
            
        "status":
            var status: String = data.get("status", "")
            if status == "paused": _is_paused = true
            elif status == "running": _is_paused = false
            elif status.begins_with("speed:"): _current_speed = float(status.substr(6))
            ui_renderer.update_control_state(_is_paused, _current_speed)
        "presets_config":
            ui_renderer.update_presets(data.get("presets", []))