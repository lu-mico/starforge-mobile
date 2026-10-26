class_name Marauder
extends Unit
## Marauder — GDD §5 / mechanics spec.
## Heavy front-liner. 500 HP / 35 DPS / 55 px/s. Concussive damage.

func _init() -> void:
	max_hp = 500
	move_speed = 55.0
	damage = 35
	attack_range = 50.0
	attack_interval = 0.6
	team = 0
