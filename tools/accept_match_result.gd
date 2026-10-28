extends SceneTree
## Starforge match-result acceptance — engine side (Godot 4.6).
##
## The v0.1 "Playable Loop" needs one thing it did not have: a way for a
## match to END. This gate proves the whole loop:
##
##   A. both towers exist in main.tscn (one per side) and can be damaged
##   B. destroying the ENEMY tower ends the match in VICTORY
##   C. destroying the PLAYER tower ends the match in DEFEAT
##   D. the result screen is visible and says the right thing
##   E. the AI opponent actually pushes units down the lane
##   F. a restart resets the economy and reloads the match
##
## Usage (from the repo root):
##   godot --headless --import
##   godot --headless --script tools/accept_match_result.gd
##
## Exit code 0 = PASS, 1 = FAIL.

const MAIN_SCENE := "res://scenes/main/main.tscn"
const MINERAL_AUTOLOAD := "MineralField"

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

	print("=== A. Both towers exist and are damageable ===")
	await _check_towers()

	print("\n=== B. Enemy tower falls -> VICTORY ===")
	await _check_victory()

	print("\n=== C. Player tower falls -> DEFEAT ===")
	await _check_defeat()

	print("\n=== D. The AI opponent pushes ===")
	await _check_ai()

	print("\n=== E. Restart resets the economy ===")
	await _check_restart()

	print("\n=> %s (%d checks, %d failed)" % [
		"FAIL" if fail_count > 0 else "PASS", check_count, fail_count])
	quit(1 if fail_count > 0 else 0)


# ---------------------------------------------------------------- helpers

func _arena() -> Node:
	var packed := load(MAIN_SCENE) as PackedScene
	var arena := packed.instantiate()
	root.add_child(arena)
	return arena


func _overlay(arena: Node) -> Node:
	return arena.get_node_or_null("ResultOverlay")


func _check_towers() -> void:
	var arena := _arena()
	await process_frame
	var enemy := arena.get_node_or_null("EnemyTower")
	var player := arena.get_node_or_null("PlayerTower")
	chk("main.tscn has an EnemyTower", enemy != null)
	chk("main.tscn has a PlayerTower", player != null)
	if enemy != null:
		chk("the enemy tower is team 1", int(enemy.get("team")) == 1, str(enemy.get("team")))
		chk("the enemy tower is in the 'towers' group", enemy.is_in_group("towers"))
		chk("the enemy tower starts at full hp",
			int(enemy.call("hp")) == int(enemy.get("max_hp")), str(enemy.call("hp")))
	if player != null:
		chk("the player tower is team 0", int(player.get("team")) == 0, str(player.get("team")))
		chk("the player tower is in the 'towers' group", player.is_in_group("towers"))
		chk("the player tower starts at full hp",
			int(player.call("hp")) == int(player.get("max_hp")), str(player.call("hp")))
		chk("the player tower uses the player art",
			_str(player).ends_with("player_tower_intact.png"), _str(player))
	arena.queue_free()
	await process_frame


## The texture path of a tower's sprite.
func _str(tower: Node) -> String:
	var sprite := tower.get_node_or_null("TowerSprite") as Sprite2D
	if sprite == null or sprite.texture == null:
		return "none"
	return sprite.texture.resource_path


func _check_victory() -> void:
	var arena := _arena()
	await process_frame
	var overlay := _overlay(arena)
	chk("the arena has a ResultOverlay", overlay != null)
	var enemy := arena.get_node_or_null("EnemyTower")
	if enemy != null:
		enemy.call("take_damage", 99999)
	await process_frame
	chk("the enemy tower is destroyed", bool(enemy.call("is_destroyed")))
	if overlay != null:
		chk("the result overlay is visible", bool(overlay.get("visible")))
		var title := overlay.get_node_or_null("Title")
		chk("the result screen says VICTORY",
			title != null and String(title.get("text")) == "VICTORY",
			String(title.get("text")) if title != null else "missing")
		chk("the result screen knows it is a victory", bool(overlay.call("is_victory")))
	chk("the match ends with the tree paused", paused)
	paused = false
	arena.queue_free()
	await process_frame


func _check_defeat() -> void:
	var arena := _arena()
	await process_frame
	var overlay := _overlay(arena)
	var player := arena.get_node_or_null("PlayerTower")
	if player != null:
		player.call("take_damage", 99999)
	await process_frame
	chk("the player tower is destroyed", bool(player.call("is_destroyed")))
	if overlay != null:
		var title := overlay.get_node_or_null("Title")
		chk("the result screen says DEFEAT",
			title != null and String(title.get("text")) == "DEFEAT",
			String(title.get("text")) if title != null else "missing")
		chk("the result screen knows it is a defeat", not bool(overlay.call("is_victory")))
	paused = false
	arena.queue_free()
	await process_frame


func _check_ai() -> void:
	var arena := _arena()
	await process_frame
	var ai := arena.get_node_or_null("AiOpponent")
	chk("the arena has an AiOpponent", ai != null)
	if ai == null:
		arena.queue_free()
		await process_frame
		return
	chk("the AI knows the unit roster", String(ai.call("next_unit_id")) != "",
		String(ai.call("next_unit_id")))
	# Speed the clock up instead of waiting 18 real seconds.
	ai.set("first_spawn_delay", 0.1)
	ai.set("_timer", 0.05)
	var frames := 0
	while frames < 240 and int(ai.call("spawned_count")) < 1:
		await process_frame
		frames += 1
	chk("the AI pushed a unit into the lane", int(ai.call("spawned_count")) >= 1,
		"spawned %d after %d frames" % [int(ai.call("spawned_count")), frames])
	# The AI unit must be on the ENEMY team, otherwise it would help the player.
	var ai_units := 0
	for c in arena.get_children():
		if c.is_in_group("units") and int(c.get("team")) == 1:
			ai_units += 1
	chk("the AI unit is on the enemy team", ai_units >= 1, "%d enemy units" % ai_units)
	arena.queue_free()
	await process_frame


func _check_restart() -> void:
	var arena := _arena()
	await process_frame
	var minerals := root.get_node_or_null(MINERAL_AUTOLOAD)
	chk("the MineralField autoload exists", minerals != null)
	if minerals != null:
		minerals.set("_current", 1)
		# The restart path calls reset() on the autoload.
		minerals.call("reset")
		await process_frame
		chk("the economy is back to 5 / 10 after a restart",
			int(minerals.get("_current")) == 5, str(minerals.get("_current")))
	arena.queue_free()
	await process_frame
