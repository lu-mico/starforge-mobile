extends SceneTree
## Starforge match-duration measurement (v0.1 deliverable evidence).
##
## The v0.1 deliverable is "a 3-minute match you can finish vs the AI".
## The gates prove the mechanics work; this gate measures how LONG a match
## actually lasts, because that number decides whether the deliverable is
## met, approximated, or not met at all.
##
## Two scenarios, both driven headless with Engine.time_scale = 10:
##   idle    - the player never deploys (what happens if the taps do not land)
##   defender- the player spends every mineral it can on the cheapest unit
##              that can reach the enemy tower (the realistic best case)
##
## Usage:
##   godot --headless --script tools/measure_match.gd
##
## Exit code 0 = both matches ended (the measurement succeeded).

const MAIN_SCENE := "res://scenes/main/main.tscn"
const TIME_SCALE := 10.0
const MAX_GAME_SECONDS := 900.0

## The card the defender buys first. A Siege Tank (7 minerals, 350px range)
## does the most tower damage per mineral; a Marine (3) is the fallback.
const PREFERRED := ["siege_tank", "marauder", "marine", "hellion"]

## Where the defender deploys: far enough up the lane to shoot the enemy
## tower, close enough that the unit arrives before the AI reaches it.
const DEPLOY_X := 260.0

var fail_count := 0


func chk(name: String, cond: bool, detail: String = "") -> void:
	if not cond:
		fail_count += 1
	print(("PASS  " if cond else "FAIL  ") + name + ("   " + detail if detail != "" else ""))


func _initialize() -> void:
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.size = Vector2i(720, 1280)
	Engine.time_scale = TIME_SCALE

	print("=== idle player (never deploys) ===")
	var idle := await _run_match(false)
	print("\n=== defending player (spends every mineral) ===")
	var defend := await _run_match(true)

	print("\n--- summary ---")
	print("idle    : %s after %.1fs of game time" % [idle["result"], idle["seconds"]])
	print("defender: %s after %.1fs of game time" % [defend["result"], defend["seconds"]])

	chk("the idle player loses (the AI can close a match on its own)",
		idle["result"] == "DEFEAT", idle["result"])
	chk("a match ends in a reasonable time (under 5 minutes)",
		idle["seconds"] > 0.0 and idle["seconds"] < 300.0, "%.1fs" % idle["seconds"])
	chk("the defender can win (VICTORY is reachable)",
		defend["result"] == "VICTORY", defend["result"])
	chk("the defender's match is not longer than the idle one",
		defend["seconds"] <= idle["seconds"] + 1.0,
		"%.1fs vs %.1fs" % [defend["seconds"], idle["seconds"]])

	quit(1 if fail_count > 0 else 0)


## Runs one full match to its end. Returns {seconds, result}.
func _run_match(defends: bool) -> Dictionary:
	# The mineral economy is an AUTOLOAD, so it survives between the matches
	# this gate runs. Reset it or the second match starts broke.
	var minerals := root.get_node_or_null("MineralField")
	if minerals != null:
		minerals.call("reset")

	var packed := load(MAIN_SCENE) as PackedScene
	var arena := packed.instantiate()
	root.add_child(arena)
	await process_frame

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

		# The defender buys whenever it can afford something.
		if defends and game_seconds - last_purchase > 1.0:
			for id in PREFERRED:
				if spawner.call("spawn_card", id, DEPLOY_X):
					last_purchase = game_seconds
					break

	paused = false
	arena.queue_free()
	await process_frame
	return {"seconds": game_seconds, "result": result}
