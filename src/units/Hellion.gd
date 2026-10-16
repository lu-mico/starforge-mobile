class_name Hellion
extends Unit
## Hellion — GDD §5 / mechanics spec.
## Anti-light, dodge-roll charges. 350 HP / 30 DPS / 130 px/s, charge = 3x first contact.

var _has_charged: bool = false
const CHARGE_MULTIPLIER: float = 3.0

func _init() -> void:
	max_hp = 350
	move_speed = 130.0
	damage = 30
	attack_range = 40.0  # melee skirmisher
	attack_interval = 0.25
	team = 0

func _perform_attack() -> void:
	if _target is Unit:
		var real_damage: int = damage
		if not _has_charged:
			real_damage = int(damage * CHARGE_MULTIPLIER)
			_has_charged = true
		(_target as Unit).take_damage(real_damage)
	elif _target.has_method("take_damage"):
		_target.call("take_damage", damage)
