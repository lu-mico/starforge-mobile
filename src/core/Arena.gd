extends Node2D
## Arena — v0.1 single-lane MVP scene root.
## Wires MineralField HUD, spawner, and the test target dummies.

@onready var mineral_label: Label = $HUD/MineralLabel
@onready var spawner: UnitSpawner = $UnitSpawner

func _ready() -> void:
	MineralField.minerals_changed.connect(_on_minerals_changed)
	# Push initial state to HUD
	_on_minerals_changed(MineralField.current(), 10)

func _on_minerals_changed(current: int, maximum: int) -> void:
	if mineral_label:
		mineral_label.text = "Minerals: %d / %d" % [current, maximum]
