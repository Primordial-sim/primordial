extends Control

# Referencias a los paneles para ocultarlos/mostrarlos
# (Rutas relativas, ya que este script está en GlobalVBox)
@onready var left_panel: PanelContainer = $MiddleArea/LeftPanel
@onready var right_panel: PanelContainer = $MiddleArea/RightPanel
@onready var bottom_panel: PanelContainer = $BottomPanel

# Referencias a los controles temporales
@onready var btn_pause: Button = $MiddleArea/CenterArea/TemporalControls/TemporalHBox/BtnPause
@onready var btn_speed_1: Button = $MiddleArea/CenterArea/TemporalControls/TemporalHBox/BtnSpeed1
@onready var btn_speed_10: Button = $MiddleArea/CenterArea/TemporalControls/TemporalHBox/BtnSpeed10
@onready var lbl_status: Label = $MiddleArea/CenterArea/TemporalControls/TemporalHBox/LblStatus

# Botones de la barra superior
@onready var btn_toggle_left: Button = $TopBar/TopBarHBox/BtnToggleLeft
@onready var btn_toggle_right: Button = $TopBar/TopBarHBox/BtnToggleRight
@onready var btn_toggle_bottom: Button = $TopBar/TopBarHBox/BtnToggleBottom

var _is_paused: bool = false
var _current_speed: float = 1.0

# Variables para recibir las funciones de websocket_client.gd
var notify_pause: Callable = Callable()
var notify_speed: Callable = Callable()

func _ready() -> void:
    # Conectar señales de los botones
    btn_toggle_left.pressed.connect(_on_toggle_left)
    btn_toggle_right.pressed.connect(_on_toggle_right)
    btn_toggle_bottom.pressed.connect(_on_toggle_bottom)
    
    btn_pause.pressed.connect(_on_pause_pressed)
    btn_speed_1.pressed.connect(_on_speed_pressed.bind(1.0))
    btn_speed_10.pressed.connect(_on_speed_pressed.bind(10.0))

func _on_toggle_left() -> void:
    left_panel.visible = not left_panel.visible
    btn_toggle_left.text = "◀ Izq" if left_panel.visible else "▶ Izq"

func _on_toggle_right() -> void:
    right_panel.visible = not right_panel.visible
    btn_toggle_right.text = "Der ▶" if right_panel.visible else "Der ◀"

func _on_toggle_bottom() -> void:
    bottom_panel.visible = not bottom_panel.visible
    btn_toggle_bottom.text = "▼ Abajo" if bottom_panel.visible else "▲ Abajo"

func _on_pause_pressed() -> void:
    _is_paused = not _is_paused
    btn_pause.text = "⏸ Pausa" if _is_paused else "▶ Play"
    if notify_pause.is_valid():
        notify_pause.call(_is_paused)

func _on_speed_pressed(speed: float) -> void:
    _current_speed = speed
    if notify_speed.is_valid():
        notify_speed.call(_current_speed)

# --- Métodos públicos para que websocket_client.gd actualice la UI ---

func update_tick_info(tick: int, day: float, agents: int) -> void:
    lbl_status.text = "Tick: %d | Día: %.1f | Agentes: %d" % [tick, day, agents]

func update_pause_state(is_paused: bool) -> void:
    _is_paused = is_paused
    btn_pause.text = "⏸ Pausa" if _is_paused else "▶ Play"

func update_speed_state(speed: float) -> void:
    _current_speed = speed
