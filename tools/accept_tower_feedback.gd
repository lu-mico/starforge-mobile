extends SceneTree
## Starforge tower hit-feedback acceptance — engine side (Godot 4.6).
##
## The gate for ASSET_UI_SPEC §6-3 (decided 2026-10-27): the towers ship
## exactly TWO art states (intact / damaged) and the LEGIBILITY comes from
## the engine — damaged art below 50% hp, a hit tint and a shake on every
## hit, and a destroyed state at 0 hp.
##
## This script is the engine-side proof that the decision is actually
## implemented (not just written down in the spec):
##   A. main.tscn wires the enemy tower to Tower.gd with the right kind/team
##   B. the 2-state swap happens at < 50% hp and NOT at exactly 50%
##   C. every hit produces a tint + a shake, and both decay back to rest
##   D. 0 hp destroys the tower (collision off, leaves the "towers" group)
##   E. end-to-end: a real Marine walks up and shoots the tower, the tower
##      flips to the damaged art and then dies
##
## Usage (from the repo root):
##   godot --headless --import
##   godot --headless --script tools/accept_tower_feedback.gd
##
## Exit code 0 = PASS, 1 = FAIL.

const MAIN_SCENE := "res://scenes/main/main.tscn"
const TOWER_SCRIPT := "res://src/buildings/Tower.gd"
const MARINE_SCENE := "res://scenes/units/marine.tscn"
const LANE_Y := 640.0

var fail_count := 0
var check_count := 0


func chk(name: String, cond: bool, detail: String = "") -> void:
	check_count += 1
	if not cond:
		fail_count += 1
	print(("PASS  " if cond else "FAIL  ") + name + ("   " + detail if detail != "" else ""))


func _initialize() -> void:
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.size = Vector2i(720, 1280)
	await process_frame

	print("=== A. Scene wiring (main.tscn) ===")
	await _check_scene()

	print("\n=== B. Two states, threshold strictly below 50% ===")
	await _check_two_states()

	print("\n=== C. Hit feedback (tint + shake) and its decay ===")
	await _check_feedback()

	print("\n=== D. Destruction ===")
	await _check_destruction()

	print("\n=== E. End-to-end: a Marine shoots the tower ===")
	await _check_end_to_end()

	print("\n=> %s (%d checks, %d failed)" % [
		"FAIL" if fail_count > 0 else "PASS", check_count, fail_count])
	quit(1 if fail_count > 0 else 0)


# ---------------------------------------------------------------- helpers

## Builds a bare tower (StaticBody2D + Tower.gd + a Sprite2D child).
func _make_tower(kind: String, team: int, max_hp: int) -> Node:
	var script: GDScript = load(TOWER_SCRIPT)
	var tower: Node = script.new()
	tower.set("tower_kind", kind)
	tower.set("team", team)
	tower.set("max_hp", max_hp)
	var sprite := Sprite2D.new()
	sprite.name = "TowerSprite"
	tower.add_child(sprite)
	return tower


func _texture_path(tower: Node) -> String:
	var sprite := tower.get_node_or_null("TowerSprite") as Sprite2D
	if sprite == null or sprite.texture == null:
		return "none"
	return sprite.texture.resource_path


func _check_scene() -> void:
	var packed := load(MAIN_SCENE) as PackedScene
	if packed == null:
		chk("main.tscn loads", false)
		return
	chk("main.tscn loads", true)
	var arena := packed.instantiate()
	root.add_child(arena)
	await process_frame

	var tower := arena.get_node_or_null("EnemyTower")
	chk("main.tscn has an EnemyTower", tower != null)
	if tower == null:
		arena.queue_free()
		await process_frame
		return
	var script_path: String = tower.get_script().resource_path if tower.get_script() != null else ""
	chk("EnemyTower runs Tower.gd", script_path == TOWER_SCRIPT, script_path)
	chk("EnemyTower is a StaticBody2D", tower is StaticBody2D)
	chk("EnemyTower kind == enemy", String(tower.get("tower_kind")) == "enemy",
		String(tower.get("tower_kind")))
	chk("EnemyTower team == 1 (enemy)", int(tower.get("team")) == 1,
		str(tower.get("team")))
	chk("EnemyTower is in the 'towers' group", tower.is_in_group("towers"))
	chk("EnemyTower starts on the intact art",
		_texture_path(tower).ends_with("enemy_tower_intact.png"), _texture_path(tower))
	chk("EnemyTower starts at full hp", int(tower.call("hp")) == int(tower.get("max_hp")),
		str(tower.call("hp")))

	arena.queue_free()
	await process_frame


func _check_two_states() -> void:
	var tower := _make_tower("enemy", 1, 200)
	root.add_child(tower)
	await process_frame
	chk("fresh tower shows the intact art",
		_texture_path(tower).ends_with("enemy_tower_intact.png"), _texture_path(tower))
	chk("fresh tower is not flagged damaged", not bool(tower.call("is_damaged")))

	# exactly 50% must NOT flip (the rule is "strictly below 50%")
	tower.call("take_damage", 100)
	await process_frame
	chk("at exactly 50% hp the art is still intact",
		_texture_path(tower).ends_with("enemy_tower_intact.png"), _texture_path(tower))
	chk("at exactly 50% hp the tower is not flagged damaged",
		not bool(tower.call("is_damaged")))

	tower.call("take_damage", 1)
	await process_frame
	chk("below 50% hp the art flips to damaged",
		_texture_path(tower).ends_with("enemy_tower_damaged.png"), _texture_path(tower))
	chk("below 50% hp the tower is flagged damaged", bool(tower.call("is_damaged")))
	chk("hp after two hits is 99", int(tower.call("hp")) == 99, str(tower.call("hp")))

	# a 0 damage hit must not change anything
	tower.call("take_damage", 0)
	await process_frame
	chk("a 0 damage hit changes nothing", int(tower.call("hp")) == 99, str(tower.call("hp")))

	tower.queue_free()
	await process_frame


func _check_feedback() -> void:
	var tower := _make_tower("enemy", 1, 200)
	root.add_child(tower)
	await process_frame
	var sprite := tower.get_node_or_null("TowerSprite") as Sprite2D
	var base: Vector2 = tower.call("base_offset")

	chk("a fresh tower is not flashing", not bool(tower.call("flash_active")))
	chk("a fresh tower is not shaking", not bool(tower.call("shake_active")))
	chk("a fresh tower is at rest", sprite.modulate == Color.WHITE, str(sprite.modulate))

	tower.call("take_damage", 25)
	await process_frame
	chk("a hit starts the flash", bool(tower.call("flash_active")))
	chk("a hit tints the sprite", sprite.modulate != Color.WHITE, str(sprite.modulate))
	chk("a hit starts the shake", bool(tower.call("shake_active")))
	chk("a hit moves the sprite off its rest offset", sprite.offset != base,
		"%s vs %s" % [str(sprite.offset), str(base)])

	# let the effects expire
	for i in range(30):
		await process_frame
	chk("the flash expires", not bool(tower.call("flash_active")))
	chk("the shake expires", not bool(tower.call("shake_active")))
	chk("the sprite returns to white", sprite.modulate == Color.WHITE, str(sprite.modulate))
	chk("the sprite returns to its rest offset", sprite.offset == base,
		"%s vs %s" % [str(sprite.offset), str(base)])

	tower.queue_free()
	await process_frame


func _check_destruction() -> void:
	var tower := _make_tower("enemy", 1, 100)
	root.add_child(tower)
	await process_frame
	var shape := CollisionShape2D.new()
	shape.name = "CollisionShape2D"
	tower.add_child(shape)

	var destroyed_seen := [false]
	tower.connect("destroyed", func(_t): destroyed_seen[0] = true)

	tower.call("take_damage", 100)
	await process_frame
	chk("0 hp destroys the tower", bool(tower.call("is_destroyed")))
	chk("the destroyed signal fires", destroyed_seen[0])
	chk("a destroyed tower leaves the 'towers' group", not tower.is_in_group("towers"))
	chk("a destroyed tower disables its collision", shape.disabled)
	chk("a destroyed tower shows the damaged art",
		_texture_path(tower).ends_with("enemy_tower_damaged.png"), _texture_path(tower))

	# further hits are ignored
	tower.call("take_damage", 50)
	await process_frame
	chk("a destroyed tower ignores further damage", int(tower.call("hp")) == 0,
		str(tower.call("hp")))

	tower.queue_free()
	await process_frame


func _check_end_to_end() -> void:
	# A bare arena: one enemy tower at the far end, one Marine next to it.
	var arena := Node2D.new()
	root.add_child(arena)
	var tower := _make_tower("enemy", 1, 100)
	tower.set_position(Vector2(620, LANE_Y))
	arena.add_child(tower)
	await process_frame

	var marine_packed := load(MARINE_SCENE) as PackedScene
	if marine_packed == null:
		chk("marine.tscn loads", false)
		arena.queue_free()
		await process_frame
		return
	chk("marine.tscn loads", true)
	var marine := marine_packed.instantiate()
	marine.set("lane_y", LANE_Y)
	marine.set("team", 0)
	arena.add_child(marine)
	marine.global_position = Vector2(565, LANE_Y)
	marine.add_to_group("units")
	await process_frame

	chk("the Marine is next to the tower", absf(marine.global_position.x - 620.0) < 60.0,
		str(marine.global_position))

	# The Marine shoots every 0.4s for 25 damage: 3 hits take the tower
	# below 50% (damaged art), the 4th kills it.
	var flipped := false
	var frames := 0
	while frames < 240:
		await physics_frame
		frames += 1
		if bool(tower.call("is_damaged")) and not flipped:
			flipped = true
		if bool(tower.call("is_destroyed")):
			break
	chk("the Marine damages the tower", int(tower.call("hp")) < 100,
		"hp=%d after %d frames" % [int(tower.call("hp")), frames])
	chk("the tower flips to the damaged art under fire", flipped)
	chk("the tower dies under sustained fire", bool(tower.call("is_destroyed")),
		"hp=%d after %d frames" % [int(tower.call("hp")), frames])
	chk("the destroyed tower left the 'towers' group", not tower.is_in_group("towers"))

	arena.queue_free()
	await process_frame
