extends Node2D
## Arena — v0.1 single-lane MVP scene root.
##
## Wires the mineral HUD, the card hand, the deploy flow and the MATCH
## RESULT:
##   tap a card  -> the card is selected (its frame badge lights up)
##   tap the lane -> the selected unit is deployed at that x
## Keyboard 1..4 still deploys at the fixed spawn point.
##
## MATCH RESULT (v0.1, added 2026-10-28):
## The two towers are the two ends of the match.
##   * the ENEMY tower (team 1) falls  -> VICTORY
##   * the PLAYER tower (team 0) falls -> DEFEAT
## The AI pushes units down the lane, so a player who does nothing loses,
## and a player who pushes wins. Both outcomes are reachable and both are
## announced (overlay + result sting).

const LANE_TAP_BAND: float = 60.0   # how far from lane_y a tap still counts
const DEPLOY_MIN_X: float = 140.0   # never deploy inside the player tower
const DEPLOY_MAX_X: float = 600.0   # never deploy on top of the enemy tower

@onready var mineral_label: Label = $HUD/MineralLabel
@onready var hint_label: Label = $HUD/HintLabel
@onready var card_bar: CardBar = $HUD/CardBar
@onready var spawner: UnitSpawner = $UnitSpawner
@onready var result_overlay: ResultOverlay = $ResultOverlay
@onready var ai: AiOpponent = $AiOpponent

var _selected_card: String = ""
var _match_over: bool = false


func _ready() -> void:
	MineralField.minerals_changed.connect(_on_minerals_changed)
	card_bar.card_selected.connect(_on_card_selected)
	result_overlay.restart_requested.connect(_on_restart_requested)
	# Pacing recorder (v0.3 prep): every match starts a fresh record, and
	# the spawn signals feed the per-card deploy / loss counters.
	MatchStats.begin_match()
	spawner.unit_spawned.connect(_on_player_unit_spawned)
	ai.unit_spawned.connect(_on_enemy_unit_spawned)
	# The towers add themselves to the "towers" group in their own _ready,
	# which runs before the parent's, so they are all reachable here.
	for node in get_tree().get_nodes_in_group("towers"):
		node.connect("destroyed", _on_tower_destroyed)
	_on_minerals_changed(MineralField.current(), 10)


func _on_minerals_changed(current: int, maximum: int) -> void:
	if mineral_label:
		mineral_label.text = "Minerals: %d / %d" % [current, maximum]
	if card_bar:
		card_bar.refresh_affordability(current)


func _on_card_selected(card_id: String) -> void:
	# Only a PLAYER tapping a card counts as a card action. The deploy path
	# clears the selection itself (it must not be counted as a card tap).
	MatchStats.note_card_select()
	_selected_card = card_id
	_update_hint(card_id)


## Update the hint line for the current selection.
func _update_hint(card_id: String) -> void:
	if hint_label:
		hint_label.text = ("Tap the lane to deploy %s" % card_id.capitalize()) \
			if card_id != "" else "Tap a card, then the lane"


func _unhandled_input(event: InputEvent) -> void:
	if _match_over or _selected_card == "":
		return
	var tap := Vector2.INF
	# TapInput, not a raw event check: on Android one physical tap arrives
	# TWICE (a real screen touch plus the mouse event Godot emulates from
	# it). Without this, a single lane tap deployed TWO units.
	if TapInput.is_press(event):
		if event is InputEventMouseButton:
			tap = _to_world((event as InputEventMouseButton).position)
		elif event is InputEventScreenTouch:
			tap = _to_world((event as InputEventScreenTouch).position)
	if tap == Vector2.INF:
		return
	if absf(tap.y - spawner.lane_y) > LANE_TAP_BAND:
		return
	# The tap landed in the band: that is a player action whatever the
	# outcome (the pacing pass tunes how busy the lane is).
	MatchStats.note_tap()
	var deploy_x: float = clampf(tap.x, DEPLOY_MIN_X, DEPLOY_MAX_X)
	if spawner.spawn_card(_selected_card, deploy_x):
		card_bar.clear_selection()
		_selected_card = ""
		_update_hint("")


func _to_world(screen_pos: Vector2) -> Vector2:
	var xform := get_viewport().get_canvas_transform().affine_inverse()
	return xform * screen_pos


## A tower fell. Which tower decides who won.
func _on_tower_destroyed(tower: Tower) -> void:
	if _match_over:
		return
	_match_over = true
	var victory: bool = int(tower.team) == 1
	_end_match(victory)


func _end_match(victory: bool) -> void:
	ai.stop()
	# Write the match out BEFORE the tree is paused, so the record carries
	# the final elapsed time of the match.
	MatchStats.end_match("VICTORY" if victory else "DEFEAT")
	Sfx.play_result(victory)
	result_overlay.show_result(victory)
	if hint_label:
		hint_label.text = "VICTORY - press RESTART" if victory else "DEFEAT - press RESTART"
	# Freeze the match. The overlay runs in PROCESS_MODE_ALWAYS, so its
	# button still answers while the tree is paused.
	get_tree().paused = true


## Puts the world back into a fresh-match state. Split out from the actual
## scene reload so the acceptance gate can test it without reloading.
func _prepare_restart() -> void:
	get_tree().paused = false
	Sfx.stop_all()
	MineralField.reset()


func _on_restart_requested() -> void:
	_prepare_restart()
	get_tree().reload_current_scene()


# ---------------------------------------------------------------- telemetry

## A player unit appeared. The deploy is counted HERE, not at the tap site,
## so the keyboard deploy (KEY_1..KEY_4) is counted too — every deploy the
## player makes has to show up in the pacing data, or the retune tunes
## against a number that is missing part of the play.
func _on_player_unit_spawned(unit: Node, card_id: String) -> void:
	MatchStats.note_deploy(card_id, UnitRoster.cost(card_id))
	if unit is Unit:
		(unit as Unit).died.connect(_on_player_unit_died.bind(card_id))


func _on_player_unit_died(_unit: Unit, card_id: String) -> void:
	MatchStats.note_player_unit_lost(card_id)


## An enemy unit appeared: its death is a kill for the player.
func _on_enemy_unit_spawned(unit: Node) -> void:
	if unit is Unit:
		(unit as Unit).died.connect(_on_enemy_unit_died)


func _on_enemy_unit_died(_unit: Unit) -> void:
	MatchStats.note_enemy_unit_lost()
