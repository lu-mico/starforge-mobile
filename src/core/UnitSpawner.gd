class_name UnitSpawner
extends Node
## UnitSpawner — deploys units for the player.
##
## Two entry points, one cost table (UnitRoster, which mirrors GDD §5):
##   * KEY_1..KEY_4 spawn at the fixed player spawn point (v0.1 shortcut)
##   * spawn_card(id, world_x) deploys at a tapped lane position — this is the
##     card-hand flow: tap a card, then tap the lane.

@export var spawn_point: Node2D
@export var lane_y: float = 640.0
@export var player_team: int = 0


func _unhandled_input(event: InputEvent) -> void:
	# NB: keycode only exists on key events. Reading it on a mouse/touch event
	# raises "Invalid access to property 'keycode'" and kills the handler, so
	# the event type is checked first.
	if not (event is InputEventKey):
		return
	var key := (event as InputEventKey)
	if not key.pressed or key.echo:
		return
	match key.keycode:
		KEY_1:
			_spawn_at(UnitRoster.ids()[0], spawn_point.global_position.x)
		KEY_2:
			_spawn_at(UnitRoster.ids()[1], spawn_point.global_position.x)
		KEY_3:
			_spawn_at(UnitRoster.ids()[2], spawn_point.global_position.x)
		KEY_4:
			_spawn_at(UnitRoster.ids()[3], spawn_point.global_position.x)


## Deploy the card `id` at world x = world_x. Returns true when a unit spawned.
func spawn_card(id: String, world_x: float) -> bool:
	return _spawn_at(id, world_x)


func _spawn_at(id: String, world_x: float) -> bool:
	var card := UnitRoster.card(id)
	if card.is_empty():
		return false
	var cost := int(card["cost"])
	if not MineralField.can_afford(cost):
		return false
	MineralField.spend(cost)
	var scene: PackedScene = card["scene"]
	var unit: Node = scene.instantiate()
	if unit is Unit:
		(unit as Unit).lane_y = lane_y
		(unit as Unit).team = player_team
	# The unit is added to the ARENA (the spawner's parent), not to
	# get_tree().current_scene: current_scene is null when the game is driven
	# by a --script harness, and the arena is the correct host either way.
	host().add_child(unit)
	unit.global_position = Vector2(world_x, lane_y)
	unit.add_to_group("units")
	return true


## Where spawned units are parented. Defaults to the spawner's parent (the
## arena root); overridable for tests.
func host() -> Node:
	return get_parent() if get_parent() != null else get_tree().current_scene
