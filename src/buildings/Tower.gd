class_name Tower
extends StaticBody2D
## Tower — v0.1 tower with the 2-state hit feedback (ASSET_UI_SPEC §6-3).
##
## DECISION (§6-3, taken 2026-10-27): towers ship exactly TWO states
## (intact / damaged). The damaged art is a RECOLOUR, not a shape change
## (measured on the delivered PNGs: 0 px removed from the silhouette,
## 91 px recoloured) and a tower is only 40 px wide on a 720 px screen
## (5.6% of the width), so the texture difference alone is close to
## unreadable at 1x.
##
## => The legibility is the ENGINE's job, and this script is that job:
##   * hp < 50% of max  -> the sprite swaps to <kind>_tower_damaged.png
##   * every hit        -> a short hit tint + a short horizontal shake
##   * hp == 0          -> destroyed: collision off, leaves the "towers"
##                         group so the units stop shooting it
##
## The art side owns the two PNGs per kind; this script owns the feedback.
## A 3rd art state was rejected (see ASSET_UI_SPEC §6-3): it would change
## the silhouette of a 40 px wide object and cost 3 more images for a
## payoff the engine effects already deliver.

signal damaged(tower: Tower, remaining_hp: int)
signal destroyed(tower: Tower)

## The two shipped states per tower kind. Preloaded so a wrong path fails
## at parse time instead of silently rendering nothing.
const TEXTURES: Dictionary = {
	"player": {
		"intact": preload("res://assets/sprites/towers/player_tower_intact.png"),
		"damaged": preload("res://assets/sprites/towers/player_tower_damaged.png"),
	},
	"enemy": {
		"intact": preload("res://assets/sprites/towers/enemy_tower_intact.png"),
		"damaged": preload("res://assets/sprites/towers/enemy_tower_damaged.png"),
	},
	"king": {
		"intact": preload("res://assets/sprites/towers/king_tower_intact.png"),
		"damaged": preload("res://assets/sprites/towers/king_tower_damaged.png"),
	},
}

@export var tower_kind: String = "enemy"    # player | enemy | king
@export var team: int = 1                   # 0 = player, 1 = enemy
@export var max_hp: int = 200
@export var damaged_ratio: float = 0.5      # strictly below this -> damaged art
@export var flash_time: float = 0.12        # seconds of hit tint
@export var flash_color: Color = Color(1.0, 0.55, 0.55, 1.0)
@export var shake_time: float = 0.18        # seconds of shake
@export var shake_amplitude: float = 3.0   # px at the start of the shake

var _hp: int = 200
var _is_damaged: bool = false
var _is_destroyed: bool = false
var _flash_left: float = 0.0
var _shake_left: float = 0.0
var _shake_phase: float = 0.0
var _base_offset: Vector2 = Vector2.ZERO
var _sprite: Sprite2D = null


func _ready() -> void:
	_hp = max_hp
	_sprite = get_node_or_null("TowerSprite") as Sprite2D
	if _sprite == null:
		_sprite = get_node_or_null("Sprite") as Sprite2D
	if _sprite != null:
		_base_offset = _sprite.offset
	add_to_group("towers")
	_apply_texture()


func _process(delta: float) -> void:
	if _sprite == null or _is_destroyed:
		return
	# hit tint: fades back to the untouched white
	if _flash_left > 0.0:
		_flash_left = maxf(0.0, _flash_left - delta)
		var t: float = _flash_left / maxf(flash_time, 0.0001)
		_sprite.modulate = Color.WHITE.lerp(flash_color, t)
	else:
		_sprite.modulate = Color.WHITE
	# shake: a deterministic sine so the acceptance gate can assert on it
	# (a random offset would make the check flaky). The phase restarts at
	# PI/2, so the first frame after a hit is already at full amplitude.
	if _shake_left > 0.0:
		_shake_left = maxf(0.0, _shake_left - delta)
		var amp: float = shake_amplitude * (_shake_left / maxf(shake_time, 0.0001))
		_shake_phase += delta * 40.0
		_sprite.offset = _base_offset + Vector2(sin(_shake_phase) * amp, 0.0)
	else:
		_sprite.offset = _base_offset


## Applies `amount` damage. Returns true when the hit landed.
func take_damage(amount: int) -> bool:
	if _is_destroyed or amount <= 0:
		return false
	_hp = maxi(0, _hp - amount)
	damaged.emit(self, _hp)
	# The hit thud. The tower is the biggest target on screen, so its hits
	# are the loudest combat sound (ASSET_UI_SPEC §5).
	Sfx.play("hit", -1.0)
	_flash_left = flash_time
	_shake_left = shake_time
	_shake_phase = PI / 2.0
	if _hp <= 0:
		_destroy()
	elif not _is_damaged and hp_ratio() < damaged_ratio:
		_set_damaged(true)
	return true


func hp() -> int:
	return _hp


func hp_ratio() -> float:
	return 0.0 if max_hp <= 0 else float(_hp) / float(max_hp)


func is_damaged() -> bool:
	return _is_damaged


func is_destroyed() -> bool:
	return _is_destroyed


func flash_active() -> bool:
	return _flash_left > 0.0


func shake_active() -> bool:
	return _shake_left > 0.0


## The sprite's resting offset (the tower texture is 40x60 and the node
## origin sits on the ground line, so the sprite is offset upwards).
func base_offset() -> Vector2:
	return _base_offset


func _set_damaged(value: bool) -> void:
	_is_damaged = value
	_apply_texture()


func _destroy() -> void:
	_is_destroyed = true
	# The tower falling is the biggest event in a match - it gets its own
	# heavy sound, not the unit-sized death zap.
	Sfx.play("death", 0.0, 0.65)
	# A dead tower always shows the damaged art, even if it died in one hit
	# from full hp (the 50% rule would never have been crossed).
	_set_damaged(true)
	# A dead tower must not keep eating shots.
	remove_from_group("towers")
	var shape := get_node_or_null("CollisionShape2D") as CollisionShape2D
	if shape != null:
		shape.set_deferred("disabled", true)
	if _sprite != null:
		_sprite.modulate = Color(0.45, 0.45, 0.50, 1.0)
	destroyed.emit(self)


func _apply_texture() -> void:
	if _sprite == null:
		return
	var pack: Dictionary = TEXTURES.get(tower_kind, {})
	if pack.is_empty():
		push_warning("Tower: unknown tower_kind '%s'" % tower_kind)
		return
	var key: String = "damaged" if _is_damaged else "intact"
	_sprite.texture = pack.get(key, null)
