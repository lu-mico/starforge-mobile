extends SceneTree
## Starforge SFX WIRING acceptance — engine side (Godot 4.6).
##
## `tools/accept_sfx.gd` proves the five WAV files are valid. This gate
## proves the other half: that the five SOUNDS are actually wired to the
## five game events, so a match is audible:
##
##   deploy  -> a unit is deployed (card deploy whoosh)
##   hit     -> something takes damage (impact thud)
##   death   -> a unit dies (death zap) / a tower falls (heavier)
##   mineral -> the mineral economy ticks +1 (pickup)
##   win     -> the match ends (result sting)
##
## It counts the sounds the engine actually played, so a broken connection
## shows up as a count that never moves.
##
## Usage (from the repo root):
##   godot --headless --import
##   godot --headless --script tools/accept_sfx_wiring.gd
##
## Exit code 0 = PASS, 1 = FAIL.
##
## NB: the autoload singletons are NOT referenced by name here on purpose.
## A `--script` run compiles THIS file before the autoloads are registered as
## GDScript globals, so `Sfx.play(...)` would not even compile. The nodes are
## reached through the scene tree instead (same trick as accept_ui.gd).

const MAIN_SCENE := "res://scenes/main/main.tscn"
const SFX_AUTOLOAD := "Sfx"
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

	print("=== A. The autoload exists and knows five sounds ===")
	await _check_bank()

	print("\n=== B. Scene wiring (main.tscn) ===")
	await _check_scene()

	print("\n=== C. deploy -> 'deploy' ===")
	await _check_deploy()

	print("\n=== D. damage -> 'hit' ===")
	await _check_hit()

	print("\n=== E. death -> 'death' ===")
	await _check_death()

	print("\n=== F. mineral regen -> 'mineral' ===")
	await _check_mineral()

	print("\n=== G. match end -> 'win' ===")
	await _check_result()

	print("\n=> %s (%d checks, %d failed)" % [
		"FAIL" if fail_count > 0 else "PASS", check_count, fail_count])
	quit(1 if fail_count > 0 else 0)


# ---------------------------------------------------------------- helpers

## The Sfx autoload node, found through the tree (never by global name).
func _sfx() -> Node:
	return root.get_node_or_null(SFX_AUTOLOAD)


func _count(id: String) -> int:
	var sfx := _sfx()
	if sfx == null:
		return -1
	return int(sfx.call("count_of", id))


## The script constants of a node (STREAMS is a const, not a property).
func _consts(node: Node) -> Dictionary:
	var script: GDScript = node.get_script()
	if script == null:
		return {}
	return script.get_script_constant_map()


func _check_bank() -> void:
	var sfx := _sfx()
	chk("the Sfx autoload is registered", sfx != null, SFX_AUTOLOAD)
	if sfx == null:
		return
	var streams: Dictionary = _consts(sfx).get("STREAMS", {})
	chk("the bank carries five sounds", streams.size() == 5, str(streams.size()))
	for id in ["deploy", "hit", "death", "mineral", "win"]:
		chk("the bank knows '%s'" % id, streams.has(id))
		if streams.has(id):
			var s: AudioStream = streams[id]
			chk("'%s' is a playable AudioStream" % id,
				s != null and s.get_length() > 0.0,
				("%.2fs" % s.get_length()) if s != null else "null")


func _check_scene() -> void:
	var packed := load(MAIN_SCENE) as PackedScene
	chk("main.tscn loads", packed != null)
	if packed == null:
		return
	var arena := packed.instantiate()
	root.add_child(arena)
	await process_frame
	chk("main.tscn has an EnemyTower", arena.get_node_or_null("EnemyTower") != null)
	chk("main.tscn has a PlayerTower", arena.get_node_or_null("PlayerTower") != null)
	chk("main.tscn has an AiOpponent", arena.get_node_or_null("AiOpponent") != null)
	arena.queue_free()
	await process_frame


func _check_deploy() -> void:
	var before := _count("deploy")
	var arena := (load(MAIN_SCENE) as PackedScene).instantiate()
	root.add_child(arena)
	await process_frame
	var spawner := arena.get_node_or_null("UnitSpawner")
	chk("the spawner exists", spawner != null)
	if spawner != null:
		# Give the economy room so the deploy is not refused for cost.
		var minerals := root.get_node_or_null(MINERAL_AUTOLOAD)
		if minerals != null:
			minerals.set("_current", 10)
		var ok: bool = bool(spawner.call("spawn_card", "marine", 300.0))
		chk("a unit deploys", ok)
	await process_frame
	chk("the deploy played the 'deploy' sound", _count("deploy") > before,
		"count %d -> %d" % [before, _count("deploy")])
	arena.queue_free()
	await process_frame


func _check_hit() -> void:
	var before := _count("hit")
	var arena := (load(MAIN_SCENE) as PackedScene).instantiate()
	root.add_child(arena)
	await process_frame
	var tower := arena.get_node_or_null("EnemyTower")
	chk("the enemy tower exists", tower != null)
	if tower != null:
		tower.call("take_damage", 10)
	await process_frame
	chk("a hit on the tower played the 'hit' sound", _count("hit") > before,
		"count %d -> %d" % [before, _count("hit")])
	arena.queue_free()
	await process_frame


func _check_death() -> void:
	var before := _count("death")
	var marine_packed := load("res://scenes/units/marine.tscn") as PackedScene
	var marine := marine_packed.instantiate()
	root.add_child(marine)
	await process_frame
	marine.call("take_damage", 9999)
	await process_frame
	chk("a killed unit played the 'death' sound", _count("death") > before,
		"count %d -> %d" % [before, _count("death")])
	marine.queue_free()
	await process_frame


func _check_mineral() -> void:
	var before := _count("mineral")
	var minerals := root.get_node_or_null(MINERAL_AUTOLOAD)
	chk("the MineralField autoload exists", minerals != null)
	if minerals == null:
		return
	# Drive the economy past its regen interval.
	minerals.set("_current", 5)
	minerals.set("_regen_accumulator", 0.0)
	minerals.call("_process", 2.5)
	await process_frame
	chk("the mineral tick played the 'mineral' sound", _count("mineral") > before,
		"count %d -> %d" % [before, _count("mineral")])


func _check_result() -> void:
	var before := _count("win")
	var arena := (load(MAIN_SCENE) as PackedScene).instantiate()
	root.add_child(arena)
	await process_frame
	var tower := arena.get_node_or_null("EnemyTower")
	if tower != null:
		tower.call("take_damage", 9999)
	await process_frame
	chk("the match end played the 'win' sting", _count("win") > before,
		"count %d -> %d" % [before, _count("win")])
	# The arena pauses the tree when the match ends; undo that so the tool
	# can finish cleanly.
	paused = false
	arena.queue_free()
	await process_frame
