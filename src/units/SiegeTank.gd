class_name SiegeTank
extends Unit
## Siege Tank — GDD §5 / mechanics spec.
## Slow siege unit on a 48x48 art canvas. 900 HP / 80 DPS / 30 px/s. Explosive.

func _init() -> void:
	max_hp = 900
	move_speed = 30.0
	damage = 80
	attack_range = 350.0
	attack_interval = 1.0
	team = 0
