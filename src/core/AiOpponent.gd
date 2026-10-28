class_name AiOpponent
extends Node
## AiOpponent — the scripted opponent (PROJECT_PLAN v0.1 "Basic AI opponent").
##
## v0.1 is a single lane with two ends. The player end has a tower, the enemy
## end has a tower, and units that reach the enemy tower destroy it. For a
## DEFEAT to be reachable at all, something has to walk at the player's tower
## — that is this node's whole job.
##
## It is deliberately dumb and readable:
##   * a fixed rotation of units, so the pressure curve is predictable
##   * a fixed cadence, so a player can learn it
##   * no economy of its own (it spends no minerals)
##
## The AI respects the arena's pause (the match ends with a paused tree), and
## it stops for good once the match is over.

signal unit_spawned(unit: Node)

## Seconds before the first AI unit arrives.
@export var first_spawn_delay: float = 18.0
## Seconds between AI units.
@export var spawn_interval: float = 9.0
## The lane the AI pushes down.
@export var lane_y: float = 640.0
## Where the AI units appear (just in front of the enemy tower).
@export var spawn_x: float = 560.0
## The roster the AI cycles through (ids from UnitRoster).
@export var rotation: Array[String] = ["hellion", "marine", "marauder", "hellion"]

var _timer: float = 0.0
var _rotation_index: int = 0
var _stopped: bool = false
var _spawned_count: int = 0


func _ready() -> void:
	_timer = first_spawn_delay


func _process(delta: float) -> void:
	if _stopped:
		return
	_timer -= delta
	if _timer > 0.0:
		return
	_timer = spawn_interval
	_spawn_next()


## Stop the AI for good (the match ended).
func stop() -> void:
	_stopped = true


func is_stopped() -> bool:
	return _stopped


func spawned_count() -> int:
	return _spawned_count


## The next unit id in the rotation (exposed for the acceptance gate).
func next_unit_id() -> String:
	if rotation.is_empty():
		return ""
	return rotation[_rotation_index % rotation.size()]


func _spawn_next() -> void:
	var id := next_unit_id()
	if id == "":
		return
	var card := UnitRoster.card(id)
	if card.is_empty():
		push_warning("AiOpponent: unknown unit id '%s'" % id)
		return
	var scene: PackedScene = card["scene"]
	var unit: Node = scene.instantiate()
	if unit is Unit:
		(unit as Unit).lane_y = lane_y
		(unit as Unit).team = 1
	var host := get_parent()
	if host == null:
		return
	host.add_child(unit)
	unit.global_position = Vector2(spawn_x, lane_y)
	unit.add_to_group("units")
	# The AI pushes left, towards the player tower. Without this the unit
	# would spend one frame walking right before it finds its target.
	if unit is Unit:
		(unit as Unit).set_facing(-1)
	_rotation_index = (_rotation_index + 1) % maxi(rotation.size(), 1)
	_spawned_count += 1
	unit_spawned.emit(unit)
