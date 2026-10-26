class_name Unit
extends CharacterBody2D
## Unit — base class for Starforge troops (GDD §5 card roster).
## Subclasses (Marine, Marauder, Hellion, SiegeTank) set stats via _init.
##
## Animation: the Sprite child is an AnimatedSprite2D bound to the unit's
## SpriteFrames resource (idle / walk / attack / death). Art faces RIGHT (+X);
## left-facing is the same texture with flip_h, per ASSET_OUTSOURCING_BRIEF §2.1.
## Ground alignment: the scene sets Sprite.offset so the figure's feet land on
## lane_y (see docs/ASSET_UI_SPEC.md §2 for the per-unit offsets).

signal died(unit: Unit)
signal damaged(unit: Unit, remaining_hp: int)

@export var max_hp: int = 100
@export var move_speed: float = 90.0   # px/s
@export var damage: int = 25
@export var attack_range: float = 60.0
@export var attack_interval: float = 0.4
@export var team: int = 0              # 0 = player, 1 = enemy
@export var lane_y: float = 0.0        # locked lane (GDD §4 — 3 lanes, but v0.1 MVP uses 1)

var _hp: int = 0
var _attack_cooldown: float = 0.0
var _target: Node2D = null
var _facing: int = 1                  # +1 right, -1 left
var _dying: bool = false
var sprite: AnimatedSprite2D = null    # bound in _ready (may be absent in tests)

func _ready() -> void:
	_hp = max_hp
	# Lock to lane: preserve spawn Y, only X moves.
	position.y = lane_y
	sprite = get_node_or_null("Sprite") as AnimatedSprite2D
	_update_facing()

func _update_facing() -> void:
	# Art faces right; left-facing is a flip (BRIEF §2.1: right-facing only).
	if sprite != null:
		sprite.flip_h = _facing < 0

func _play_anim(anim_name: String, restart: bool = false) -> void:
	if sprite == null:
		return
	if restart or sprite.animation != anim_name:
		sprite.play(anim_name)

func _physics_process(delta: float) -> void:
	if _dying:
		velocity = Vector2.ZERO
		return
	if is_instance_valid(_target):
		var to_target: Vector2 = _target.global_position - global_position
		var dist: float = to_target.length()
		if dist <= attack_range:
			# In range — stop and shoot
			velocity = Vector2.ZERO
			_attack_cooldown -= delta
			if _attack_cooldown <= 0.0:
				_perform_attack()
				_attack_cooldown = attack_interval
				_play_anim("attack", true)
			else:
				_play_anim("attack")
		else:
			# Walk toward target
			_facing = 1 if to_target.x > 0 else -1
			_update_facing()
			velocity = Vector2(_facing * move_speed, 0.0)
			_play_anim("walk")
	else:
		# No target — advance along lane
		velocity = Vector2(_facing * move_speed, 0.0)
		_acquire_target()
		_play_anim("walk")

	move_and_slide()

func take_damage(amount: int) -> void:
	_hp -= amount
	damaged.emit(self, _hp)
	if _hp <= 0:
		_die()

func _die() -> void:
	if _dying:
		return
	_dying = true
	died.emit(self)
	if sprite != null:
		sprite.play("death")
		# Let the death animation read before the node disappears.
		# Timer + callback (not await) so teardown never leaks a pending coroutine.
		var t := get_tree().create_timer(0.8)
		t.timeout.connect(queue_free)
	else:
		queue_free()

func _perform_attack() -> void:
	# v0.1 skeleton: damage applied via simple HP subtraction on enemy Units / towers.
	# Real projectile / VFX comes in v0.3 polish pass.
	if _target is Unit:
		(_target as Unit).take_damage(damage)
	elif _target.has_method("take_damage"):
		_target.call("take_damage", damage)

func _acquire_target() -> void:
	# Simplistic: nearest enemy Unit in attack_range, else nearest enemy Unit on lane.
	# v0.1 MVP single-lane — full priority (troops > towers > king) wired in v0.3.
	_target = null
	var best_dist: float = INF
	for node in get_tree().get_nodes_in_group("units"):
		if node == self:
			continue
		var u := node as Unit
		if u == null or u.team == team:
			continue
		# Same lane check (lane_y within tolerance)
		if absf(u.lane_y - lane_y) > 4.0:
			continue
		var d: float = global_position.distance_to(u.global_position)
		if d < best_dist:
			best_dist = d
			_target = u
