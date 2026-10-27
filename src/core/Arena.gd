extends Node2D
## Arena — v0.1 single-lane MVP scene root.
##
## Wires the mineral HUD, the card hand and the deploy flow:
##   tap a card  -> the card is selected (its frame badge lights up)
##   tap the lane -> the selected unit is deployed at that x
## Keyboard 1..4 still deploys at the fixed spawn point.

const LANE_TAP_BAND: float = 60.0   # how far from lane_y a tap still counts

@onready var mineral_label: Label = $HUD/MineralLabel
@onready var hint_label: Label = $HUD/HintLabel
@onready var card_bar: CardBar = $HUD/CardBar
@onready var spawner: UnitSpawner = $UnitSpawner

var _selected_card: String = ""


func _ready() -> void:
	MineralField.minerals_changed.connect(_on_minerals_changed)
	card_bar.card_selected.connect(_on_card_selected)
	_on_minerals_changed(MineralField.current(), 10)


func _on_minerals_changed(current: int, maximum: int) -> void:
	if mineral_label:
		mineral_label.text = "Minerals: %d / %d" % [current, maximum]
	if card_bar:
		card_bar.refresh_affordability(current)


func _on_card_selected(card_id: String) -> void:
	_selected_card = card_id
	if hint_label:
		hint_label.text = ("Tap the lane to deploy %s" % card_id.capitalize()) \
			if card_id != "" else "Tap a card, then tap the lane"


func _unhandled_input(event: InputEvent) -> void:
	if _selected_card == "":
		return
	var tap := Vector2.INF
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT:
			tap = _to_world(mb.position)
	elif event is InputEventScreenTouch:
		var st := event as InputEventScreenTouch
		if st.pressed:
			tap = _to_world(st.position)
	if tap == Vector2.INF:
		return
	if absf(tap.y - spawner.lane_y) > LANE_TAP_BAND:
		return
	# never deploy on top of the enemy tower (x=620)
	var deploy_x: float = clampf(tap.x, 40.0, 600.0)
	if spawner.spawn_card(_selected_card, deploy_x):
		card_bar.clear_selection()
		_selected_card = ""
		_on_card_selected("")


func _to_world(screen_pos: Vector2) -> Vector2:
	var xform := get_viewport().get_canvas_transform().affine_inverse()
	return xform * screen_pos
