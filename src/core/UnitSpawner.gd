class_name UnitSpawner
extends Node
## UnitSpawner — handles keypress 1/2 spawning for v0.1 MVP.
## Real drag-to-lane deploy is v0.3 polish; this proves the spawn + economy wiring.

const MARINE_SCENE := preload("res://scenes/units/marine.tscn")
const HELLION_SCENE := preload("res://scenes/units/hellion.tscn")
const MARAUDER_SCENE := preload("res://scenes/units/marauder.tscn")
const SIEGE_TANK_SCENE := preload("res://scenes/units/siege_tank.tscn")

# Costs from GDD §5 v0.1 MVP card roster.
const MARINE_COST: int = 3
const HELLION_COST: int = 4
const MARAUDER_COST: int = 4
const SIEGE_TANK_COST: int = 7

@export var spawn_point: Node2D
@export var lane_y: float = 360.0
@export var player_team: int = 0

func _unhandled_input(event: InputEvent) -> void:
	if not event.is_pressed():
		return
	match event.keycode:
		KEY_1:
			_try_spawn(MARINE_SCENE, MARINE_COST)
		KEY_2:
			_try_spawn(HELLION_SCENE, HELLION_COST)
		KEY_3:
			_try_spawn(MARAUDER_SCENE, MARAUDER_COST)
		KEY_4:
			_try_spawn(SIEGE_TANK_SCENE, SIEGE_TANK_COST)

func _try_spawn(scene: PackedScene, cost: int) -> void:
	if not MineralField.can_afford(cost):
		return
	MineralField.spend(cost)
	var unit: Node = scene.instantiate()
	if unit is Unit:
		(unit as Unit).lane_y = lane_y
		(unit as Unit).team = player_team
	get_tree().current_scene.add_child(unit)
	unit.global_position = spawn_point.global_position
	unit.add_to_group("units")
