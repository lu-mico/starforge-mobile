class_name ResultOverlay
extends CanvasLayer
## ResultOverlay — the end-of-match screen (VICTORY / DEFEAT).
##
## The match result is the one piece of v0.1 feedback that used to be missing
## entirely: units could die and a tower could fall, but nothing ever said who
## won. This overlay is that voice.
##
## Built in code (not a .tscn) on purpose: it is a scrim, a title, a line of
## text and a button, and a code-built node cannot drift out of sync with the
## script that fills it in.
##
## The overlay is PROCESS_MODE_ALWAYS, because the arena pauses the tree when
## the match ends — the screen still has to animate and its button still has
## to answer.

signal restart_requested

const TITLE_SIZE: int = 72
const BODY_SIZE: int = 28

var _scrim: ColorRect
var _title: Label
var _body: Label
var _button: Button
var _victory: bool = false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	layer = 10
	_build()
	hide_result()


func _build() -> void:
	_scrim = ColorRect.new()
	_scrim.name = "Scrim"
	_scrim.color = Color(0.02, 0.03, 0.06, 0.78)
	_scrim.set_anchors_preset(Control.PRESET_FULL_RECT)
	_scrim.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_scrim)

	_title = Label.new()
	_title.name = "Title"
	_title.anchor_left = 0.0
	_title.anchor_right = 1.0
	_title.anchor_top = 0.0
	_title.anchor_bottom = 1.0
	_title.offset_left = 0.0
	_title.offset_right = 0.0
	_title.offset_top = -60.0
	_title.offset_bottom = 60.0
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_title.add_theme_font_size_override("font_size", TITLE_SIZE)
	_title.add_theme_color_override("font_color", Color(0.95, 0.96, 1.0))
	_title.add_theme_color_override("font_outline_color", Color(0.02, 0.02, 0.05))
	_title.add_theme_constant_override("outline_size", 8)
	_title.text = ""
	add_child(_title)

	_body = Label.new()
	_body.name = "Body"
	_body.anchor_left = 0.0
	_body.anchor_right = 1.0
	_body.anchor_top = 0.0
	_body.anchor_bottom = 1.0
	_body.offset_left = 0.0
	_body.offset_right = 0.0
	_body.offset_top = 120.0
	_body.offset_bottom = 190.0
	_body.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_body.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_body.add_theme_font_size_override("font_size", BODY_SIZE)
	_body.add_theme_color_override("font_color", Color(0.78, 0.83, 0.92))
	_body.add_theme_color_override("font_outline_color", Color(0.02, 0.02, 0.05))
	_body.add_theme_constant_override("outline_size", 5)
	_body.text = ""
	add_child(_body)

	_button = Button.new()
	_button.name = "RestartButton"
	_button.text = "RESTART"
	_button.anchor_left = 0.5
	_button.anchor_right = 0.5
	_button.anchor_top = 0.5
	_button.anchor_bottom = 0.5
	_button.offset_left = -140.0
	_button.offset_right = 140.0
	_button.offset_top = 250.0
	_button.offset_bottom = 334.0
	_button.add_theme_font_size_override("font_size", 32)
	_button.pressed.connect(_on_restart_pressed)
	add_child(_button)


## Show the result screen. `victory` picks the wording and the colour.
func show_result(victory: bool) -> void:
	_victory = victory
	if _title != null:
		_title.text = "VICTORY" if victory else "DEFEAT"
		_title.add_theme_color_override("font_color",
			Color(0.55, 0.95, 0.62) if victory else Color(0.98, 0.48, 0.48))
	if _body != null:
		_body.text = "Enemy tower destroyed" if victory else "Your tower fell"
	if _button != null:
		_button.visible = true
	visible = true


func hide_result() -> void:
	visible = false


func is_victory() -> bool:
	return _victory


func _on_restart_pressed() -> void:
	restart_requested.emit()
