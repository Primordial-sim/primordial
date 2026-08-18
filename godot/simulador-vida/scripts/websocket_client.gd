extends Node2D
## Coordinador principal: recibe datos del servidor WebSocket y los distribuye
## a los nodos de renderizado. Maneja TODOS los inputs (botones + selección + teclado).

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

const SERVER_URL: String = "ws://localhost:8765"

# =============================================================================
# REFERENCIAS A NODOS
# =============================================================================

@onready var world_renderer: Node2D = $World
@onready var ui_renderer: Control = $UI/UIRenderer
@onready var camera: Camera2D = $World/Camera2D

# =============================================================================
# ESTADO
# =============================================================================

var _peer: WebSocketPeer = null
var _agents: Array = []
var _stats: Dictionary = {}
var _tick_count: int = 0
var _current_day: float = 0.0
var _is_connected: bool = false
var _was_connected_before: bool = false
var _cell_size: float = 10.0

# Dimensiones del mundo (dinámicas, recibidas del servidor)
var _world_width: int = 100
var _world_height: int = 100

# Estado de los controles de simulación
var _is_paused: bool = false
var _current_speed: float = 1.0

# =============================================================================
# CICLO DE VIDA
# =============================================================================

func _ready() -> void:
    print("🎮 Iniciando cliente WebSocket...")
    
    # Usar dimensiones por defecto inicialmente
    # Se actualizarán cuando llegue el primer mensaje del servidor
    _cell_size = 1000.0 / float(_world_width)
    world_renderer.set_cell_size(_cell_size)
    world_renderer.set_world_dimensions(_world_width, _world_height)
    camera.set_world_dimensions(_world_width, _world_height)
    
    # Centrar la cámara
    camera.reset_view()
    
    # Conectar señales de selección de agentes
    world_renderer.agent_selected.connect(_on_agent_selected)
    world_renderer.agent_deselected.connect(_on_agent_deselected)
    
    _connect_to_server()

func _process(_delta: float) -> void:
    if _peer != null:
        _peer.poll()
        _check_connection_state()
        _receive_data()

func _unhandled_input(event: InputEvent) -> void:
    """Maneja TODOS los inputs: botones de UI, selección de agentes y teclado."""
    
    # =========================================================================
    # CLIC IZQUIERDO: Botones de UI o selección de agente
    # =========================================================================
    if event is InputEventMouseButton:
        var mouse_event: InputEventMouseButton = event
        
        if mouse_event.button_index == MOUSE_BUTTON_LEFT and mouse_event.pressed:
            # 1. Primero verificar si es un clic en un botón de la barra superior
            var button_hit: Dictionary = ui_renderer.get_button_at_position(mouse_event.position)
            
            if not button_hit.is_empty():
                var action: String = button_hit["action"]
                
                if action == "pause":
                    _toggle_pause()
                elif action == "speed":
                    var speed: float = button_hit["speed"]
                    _set_speed(speed)
                
                return  # Consumir el evento, no buscar agente
            
            # 2. Si no es un botón, verificar si es un clic en la barra superior
            if mouse_event.position.y < ui_renderer.get_top_bar_height():
                return
            
            # 3. Intentar seleccionar un agente
            var selected: bool = world_renderer.try_select_agent_at_position(
                mouse_event.position,
                camera.zoom.x,
                camera.position,
                get_viewport_rect().size
            )
            
            if not selected:
                world_renderer.deselect_agent()
            
            return
    
    # =========================================================================
    # CONTROLES DE TECLADO
    # =========================================================================
    if not (event is InputEventKey):
        return
    if not event.pressed:
        return
    
    var key_event: InputEventKey = event
    
    match key_event.keycode:
        KEY_SPACE:
            _toggle_pause()
        KEY_1:
            _set_speed(1.0)
        KEY_2:
            _set_speed(2.0)
        KEY_3:
            _set_speed(5.0)
        KEY_4:
            _set_speed(10.0)
        KEY_N:
            _step_one_tick()
        KEY_ESCAPE:
            world_renderer.deselect_agent()

# =============================================================================
# COMANDOS DE SIMULACIÓN
# =============================================================================

func _toggle_pause() -> void:
    if not _is_connected:
        return
    
    _is_paused = not _is_paused
    
    var command: Dictionary = {}
    if _is_paused:
        command = {"type": "pause"}
        print("⏸️  Enviando comando: PAUSE")
    else:
        command = {"type": "resume"}
        print("▶️  Enviando comando: RESUME")
    
    _send_command(command)
    ui_renderer.update_control_state(_is_paused, _current_speed)

func _set_speed(speed: float) -> void:
    if not _is_connected:
        return
    
    _current_speed = speed
    var command: Dictionary = {"type": "set_speed", "speed": speed}
    print("⚡ Enviando comando: SET_SPEED %.1fx" % speed)
    _send_command(command)
    ui_renderer.update_control_state(_is_paused, _current_speed)

func _step_one_tick() -> void:
    if not _is_connected:
        return
    
    var command: Dictionary = {"type": "step"}
    print("⏭️  Enviando comando: STEP")
    _send_command(command)

func _send_command(command: Dictionary) -> void:
    if _peer == null or _peer.get_ready_state() != WebSocketPeer.STATE_OPEN:
        print("⚠️  No se puede enviar comando: no hay conexión")
        return
    
    var json_text: String = JSON.stringify(command)
    var error: int = _peer.send_text(json_text)
    
    if error != OK:
        print("❌ Error enviando comando: %d" % error)

# =============================================================================
# MANEJADORES DE SEÑALES DE SELECCIÓN DE AGENTES
# =============================================================================

func _on_agent_selected(agent_data: Dictionary) -> void:
    var agent_id: int = int(agent_data.get("id", -1))
    print("👤 Agente seleccionado: ID ", agent_id)
    ui_renderer.show_agent_inspector(agent_data)

func _on_agent_deselected() -> void:
    print("👤 Agente deseleccionado")
    ui_renderer.hide_agent_inspector()

# =============================================================================
# CONEXIÓN
# =============================================================================

func _connect_to_server() -> void:
    _peer = WebSocketPeer.new()
    
    var error: int = _peer.connect_to_url(SERVER_URL)
    if error != OK:
        print("❌ Error al conectar: código %d" % error)
        return
    
    print("🔗 Conectando a ", SERVER_URL, "...")

func _check_connection_state() -> void:
    var state: int = _peer.get_ready_state()
    
    match state:
        WebSocketPeer.STATE_OPEN:
            _is_connected = true
            if not _was_connected_before:
                print("✅ ¡Conectado al servidor!")
                _was_connected_before = true
                ui_renderer.update_connection_status(true)
                ui_renderer.update_control_state(_is_paused, _current_speed)
        
        WebSocketPeer.STATE_CLOSED:
            if _is_connected:
                print("❌ Desconectado del servidor.")
                _is_connected = false
                _was_connected_before = false
                ui_renderer.update_connection_status(false)
                get_tree().create_timer(2.0).timeout.connect(_connect_to_server)

# =============================================================================
# RECEPCIÓN DE DATOS
# =============================================================================

func _receive_data() -> void:
    while _peer.get_available_packet_count() > 0:
        var packet: PackedByteArray = _peer.get_packet()
        var packet_text: String = packet.get_string_from_utf8()
        
        if packet_text.is_empty():
            continue
        
        var json: JSON = JSON.new()
        var parse_result: int = json.parse(packet_text)
        
        if parse_result != OK:
            continue
        
        var data: Dictionary = json.get_data()
        _handle_message(data)

func _handle_message(data: Dictionary) -> void:
    var message_type: String = data.get("type", "")
    
    match message_type:
        "tick":
            _tick_count = data.get("tick", 0)
            _current_day = data.get("day", 0.0)
            _agents = data.get("agents", [])
            _stats = data.get("stats", {})
            
            # Actualizar dimensiones del mundo si cambiaron
            var new_width: int = data.get("world_width", 100)
            var new_height: int = data.get("world_height", 100)
            if new_width != _world_width or new_height != _world_height:
                _world_width = new_width
                _world_height = new_height
                world_renderer.set_world_dimensions(_world_width, _world_height)
                camera.set_world_dimensions(_world_width, _world_height)
                # Recalcular el tamaño de celda para que el mundo ocupe ~1000 píxeles
                _cell_size = 1000.0 / float(_world_width)
                world_renderer.set_cell_size(_cell_size)
                # Recentrar la cámara
                camera.reset_view()
            
            # Actualizar el renderizado del mundo
            world_renderer.update_agents(_agents)
            
            # Actualizar la UI
            ui_renderer.update_tick_info(_tick_count, _current_day, _agents.size())
            ui_renderer.update_stats(_stats)
            
            # Actualizar conteo de especies
            var species_counts: Dictionary = _stats.get("species_counts", {})
            ui_renderer.update_species_counts(species_counts)
            
            # Actualizar el inspector si hay un agente seleccionado
            if ui_renderer.is_inspector_visible():
                var selected_id: int = world_renderer.get_selected_agent_id()
                for agent in _agents:
                    if int(agent.get("id", -1)) == selected_id:
                        ui_renderer.update_selected_agent(agent)
                        break
            
            # Calcular información de ocupación
            var unique_cells: Dictionary = {}
            for agent in _agents:
                var key: String = "%d,%d" % [int(round(agent.get("x", 0.0))), int(round(agent.get("y", 0.0)))]
                unique_cells[key] = true
            
            var overlapping: int = _agents.size() - unique_cells.size()
            ui_renderer.update_occupancy_info(max(0, overlapping), unique_cells.size())
        
        "status":
            var status: String = data.get("status", "")
            print("📡 Estado del servidor: ", status)
            
            if status == "paused":
                _is_paused = true
            elif status == "running":
                _is_paused = false
            elif status.begins_with("speed:"):
                var speed_str: String = status.substr(6)
                _current_speed = float(speed_str)
            
            ui_renderer.update_control_state(_is_paused, _current_speed)
