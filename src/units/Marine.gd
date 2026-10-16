class_name Marine
extends Unit
## Marine — GDD §5 / mechanics spec.
## Ranged, fast, anti-swarm. 200 HP / 25 DPS / 90 px/s.

func _init() -> void:
	max_hp = 200
	move_speed = 90.0
	damage = 25
	attack_range = 60.0
	attack_interval = 0.4
	team = 0
