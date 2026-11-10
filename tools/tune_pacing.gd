extends SceneTree
## Starforge v0.3 pacing sweep — a tuning HARNESS, not a gate.
##
## Why it exists (2026-11-07, v0.3 Pacing Pass kickoff):
## The frozen-unit bug fix changes who wins, so every v0.1 number has to be
## re-measured before it can be tuned. This harness runs the real arena
## scene headless with the tower HP and the AI cadence overridden, and
## prints the two scenarios that matter:
##
##   idle     - the player never deploys (the AI has to be able to close a
##               match on its own)
##   defender - the player spends every mineral on the best unit it can
##               afford (the realistic best case)
##
## It prints the duration and the result for each, so the retune is driven
## by measurements and not by estimates — the same discipline that caught
## the v0.1 "3-minute" wording.
##
## Usage:
##   godot --headless --script tools/tune_pacing.gd
##
## Exit code 0 = the sweep ran (the verdict is the table, not the exit code).

const MAIN_SCENE := "res://scenes/main/main.tscn"
const TIME_SCALE := 10.0
const MAX_GAME_SECONDS := 420.0
const DEPLOY_X := 260.0

## The card order the defender buys in: the siege tank out-ranges the AI and
## does the most tower damage per mineral; the marine is the fallback.
const PREFERRED := ["siege_tank", "marauder", "marine", "hellion"]

## The sweep grid. Each entry is {tower_hp, ai_first, ai_interval}.
const CONFIGS: Array[Dictionary] = [
	{"tower_hp": 3600, "ai_first": 30.0, "ai_interval": 18.0},
	{"tower_hp": 4200, "ai_first": 30.0, "ai_interval": 18.0},
	{"tower_hp": 4200, "ai_first": 36.0, "ai_interval": 18.0},
	{"tower_hp": 4800, "ai_first": 36.0, "ai_interval": 21.0},
]


func _initialize() -> void:
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.size = Vector2i(720, 1280)
	Engine.time_scale = TIME_SCALE

	# Watchdog: a harness that throws mid-sweep leaves the SceneTree running
	# with nothing left to do, and the process then hangs instead of exiting.
	# The 11-07 run did exactly that (22 minutes of "Process still running").
	# This timer guarantees the harness always terminates.
	var watchdog := Timer.new()
	watchdog.wait_time = 900.0
	watchdog.one_shot = true
	watchdog.autostart = true
	root.add_child(watchdog)
	watchdog.timeout.connect(func() -> void:
		print("=== sweep ABORTED: watchdog fired (900s) ===")
		quit(2))

	print("=== Starforge v0.3 pacing sweep (tower HP x AI cadence) ===")
	print("tower_hp  ai_first  ai_interval | idle            | defender       | marine-only")
	for cfg in CONFIGS:
		var hp := int(cfg["tower_hp"])
		var first := float(cfg["ai_first"])
		var interval := float(cfg["ai_interval"])
		var idle := await _run_match("idle", hp, first, interval)
		var defend := await _run_match("defender", hp, first, interval)
		var marine := await _run_match("marine", hp, first, interval)
		print("%d  %s  %s | %s  %6.1fs | %s  %6.1fs | %s  %6.1fs" % [
			hp,
			"%5.1f" % first,
			"%5.1f" % interval,
			idle["result"],
			float(idle["seconds"]),
			defend["result"],
			float(defend["seconds"]),
			marine["result"],
			float(marine["seconds"])])

	print("\n=== sweep done ===")
	quit(0)


## Runs one full match with the tuning knobs applied. Returns
## {seconds, result}.
##
## `mode` says what the player does. It is a STRING, always:
##   "idle"    - the player never deploys (the idle player)
##   "defender"- the player spends every mineral, best unit first (the realistic
##             best case, and what tools/measure_match.gd drives)
##   "marine"  - the player only ever buys Marines (the line the pacing gate
##             drives, i.e. the weakest realistic card)
##
## The mode used to be a bool for idle/defender and the string "marine" for
## the third case, and GDScript compares a bool with a String by raising
## "Invalid operands 'bool' and 'String' in operator '=='" at runtime. The
## error aborted the function, the returned Dictionary was never built, and the
## harness hung instead of quitting (11-07 session, 22 minutes of nothing).
## One type for all three cases; no mixed-type comparison.
func _run_match(mode: String, tower_hp: int, ai_first: float, ai_interval: float) -> Dictionary:
	# The mineral economy is an AUTOLOAD and outlives the scene, so it has to
	# be reset or the second match starts broke.
	var minerals := root.get_node_or_null("MineralField")
	if minerals != null:
		minerals.call("reset")

	var packed := load(MAIN_SCENE) as PackedScene
	var arena := packed.instantiate()
	root.add_child(arena)
	await process_frame

	# Apply the tuning knobs to the LIVE scene (duck-typed on purpose: a
	# --script harness must not reference project classes).
	for node in get_nodes_in_group("towers"):
		node.set("max_hp", tower_hp)
		node.set("_hp", tower_hp)
	var ai := arena.get_node_or_null("AiOpponent")
	if ai != null:
		ai.set("first_spawn_delay", ai_first)
		ai.set("spawn_interval", ai_interval)
		ai.set("_timer", ai_first)

	var spawner := arena.get_node_or_null("UnitSpawner")
	if spawner == null:
		return {"seconds": -1.0, "result": "ERROR: no UnitSpawner"}

	var game_seconds := 0.0
	var result := "TIMEOUT"
	var last_purchase := -99.0

	while game_seconds < MAX_GAME_SECONDS:
		await process_frame
		game_seconds += root.get_process_delta_time()

		if paused:
			var overlay := arena.get_node_or_null("ResultOverlay")
			result = "VICTORY" if (overlay != null and overlay.call("is_victory")) else "DEFEAT"
			break

		if mode == "marine":
			if game_seconds - last_purchase > 1.0:
				if spawner.call("spawn_card", "marine", DEPLOY_X):
					last_purchase = game_seconds
		elif mode == "defender":
			if game_seconds - last_purchase > 1.0:
				for id in PREFERRED:
					if spawner.call("spawn_card", id, DEPLOY_X):
						last_purchase = game_seconds
						break

	paused = false
	arena.queue_free()
	await process_frame
	return {"seconds": game_seconds, "result": result}
