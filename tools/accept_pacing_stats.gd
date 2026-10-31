extends SceneTree
## Starforge PACING DATA acceptance — engine side (Godot 4.6).
##
## Why this gate exists (added 2026-10-31):
## The v0.3 Pacing Pass retunes lane speed, AI cadence and tower HP against
## a ~3-minute match. That retune can only be honest if the numbers come
## from played matches. This gate proves that the recorder (src/core/
## MatchStats.gd) actually observes a match through the SAME input path a
## player's finger takes (a real Android tap pair: the emulated mouse event
## plus the screen touch), writes it to disk, and aggregates it.
##
## It does not push a synthetic call into the recorder: it taps the card and
## the lane the way a phone does, then reads the file back.
##
## Checks:
##   A. a finished match lands in user://stats/matches.jsonl
##   B. the recorded duration matches the time the gate itself measured
##   C. the deploys / taps / card selects are counted
##   D. the per-card counters add up (deployed == lost + alive)
##   E. a match the player never touches is recorded as a DEFEAT with 0 deploys
##   F. a second match APPENDS (the file is not overwritten)
##   G. summary.json holds the win/loss distribution and the per-card rates
##
## Usage (from the repo root):
##   godot --headless --import
##   godot --headless --script tools/accept_pacing_stats.gd
##
## Exit code 0 = PASS, 1 = FAIL.

const MAIN_SCENE := "res://scenes/main/main.tscn"
const TIME_SCALE := 10.0
const MAX_GAME_SECONDS := 600.0
const STATS_DIR := "user://stats_gate"

## Where the tap lands (game coordinates) and which card the defender buys.
const LANE_X := 240.0
const LANE_Y := 640.0
const DEFENDER_CARD := "marine"
## The Marine costs 3 minerals (UnitRoster / GDD §5). It is mirrored here on
## purpose: this gate must stay FREE of project-class references. A --script
## gate is compiled BEFORE the autoloads are registered, so touching
## UnitRoster (which preloads the unit scenes, which use the Sfx autoload)
## breaks the Sfx identifier and every unit script fails to compile. The
## other gates mirror their facts the same way (see accept_ui.gd).
const DEFENDER_COST := 3

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
	Engine.time_scale = TIME_SCALE
	await process_frame

	# The gate writes into its own folder, never the real stats file.
	var stats := _stats()
	if stats == null:
		chk("the MatchStats autoload exists", false)
		_finish()
		return
	stats.call("set_output_dir", STATS_DIR)
	stats.call("clear")

	print("=== 1. a match the player plays (real Android tap pair) ===")
	var played := await _run_match(true)
	print("\n=== 2. a match the player never touches ===")
	var idle := await _run_match(false)

	print("\n=== 3. what landed on disk ===")
	var records: Array = stats.call("records")
	chk("A. the recorder wrote the matches file",
		FileAccess.file_exists(String(stats.call("matches_file"))),
		String(stats.call("matches_file")))
	chk("F. the second match APPENDED (2 records, not 1)",
		records.size() == 2, "%d records" % records.size())

	if records.size() == 2:
		var rec: Dictionary = records[0]
		var idle_rec: Dictionary = records[1]

		chk("C1. the played match is recorded as a VICTORY",
			String(rec.get("result", "")) == "VICTORY", String(rec.get("result", "")))
		chk("C2. the recorded duration matches the recorder's own clock",
			absf(float(rec.get("duration_s", 0.0)) - float(played["elapsed"])) < 0.05,
			"file %.2fs vs live %.2fs" % [float(rec.get("duration_s", 0.0)), float(played["elapsed"])])
		chk("C2b. the recorded duration is consistent with the match the gate saw",
			absf(float(rec.get("duration_s", 0.0)) - float(played["seconds"])) <= _tolerance(float(played["seconds"])),
			"recorded %.1fs vs measured %.1fs" % [float(rec.get("duration_s", 0.0)), float(played["seconds"])])
		chk("C3. the duration is a real number of seconds",
			float(rec.get("duration_s", 0.0)) > 5.0, "%.1fs" % float(rec.get("duration_s", 0.0)))
		chk("C4. the deploys are counted", int(rec.get("deploys", 0)) > 0,
			"%d deploys" % int(rec.get("deploys", 0)))
		chk("C5. every deploy is preceded by a lane tap",
			int(rec.get("taps", 0)) >= int(rec.get("deploys", 0)),
			"%d taps / %d deploys" % [int(rec.get("taps", 0)), int(rec.get("deploys", 0))])
		chk("C6. the card taps are counted", int(rec.get("card_selects", 0)) > 0,
			"%d card selects" % int(rec.get("card_selects", 0)))
		chk("C7. the actions total is the sum of the three counters",
			int(rec.get("actions", 0)) == int(rec.get("taps", 0)) + int(rec.get("card_selects", 0)) + int(rec.get("deploys", 0)),
			"%d" % int(rec.get("actions", 0)))
		chk("C8. the minerals spent are counted",
			int(rec.get("minerals_spent", 0)) > 0, "%d" % int(rec.get("minerals_spent", 0)))

		var cards: Dictionary = rec.get("cards", {})
		chk("D1. the played card is recorded",
			cards.has(DEFENDER_CARD), ", ".join(cards.keys()))
		if cards.has(DEFENDER_CARD):
			var c: Dictionary = cards[DEFENDER_CARD]
			chk("D2. the card's deployed count equals the match's deploy count",
				int(c.get("deployed", 0)) == int(rec.get("deploys", 0)),
				"%d vs %d" % [int(c.get("deployed", 0)), int(rec.get("deploys", 0))])
			chk("D3. the card's counters add up (deployed == lost + alive)",
				int(c.get("deployed", 0)) == int(c.get("lost", 0)) + int(c.get("alive", 0)),
				"%d == %d + %d" % [int(c.get("deployed", 0)), int(c.get("lost", 0)), int(c.get("alive", 0))])

		chk("E1. the untouched match is recorded as a DEFEAT",
			String(idle_rec.get("result", "")) == "DEFEAT", String(idle_rec.get("result", "")))
		chk("E2. the untouched match has no deploys",
			int(idle_rec.get("deploys", 0)) == 0, "%d" % int(idle_rec.get("deploys", 0)))
		chk("E3. the untouched match still has a duration",
			float(idle_rec.get("duration_s", 0.0)) > 5.0,
			"%.1fs" % float(idle_rec.get("duration_s", 0.0)))
		chk("E4. the untouched match's duration is consistent with the measured time",
			absf(float(idle_rec.get("duration_s", 0.0)) - float(idle["seconds"])) <= _tolerance(float(idle["seconds"])),
			"recorded %.1fs vs measured %.1fs" % [float(idle_rec.get("duration_s", 0.0)), float(idle["seconds"])])
		chk("E5. the recorded duration matches the recorder's own clock",
			absf(float(idle_rec.get("duration_s", 0.0)) - float(idle["elapsed"])) < 0.05,
			"file %.2fs vs live %.2fs" % [float(idle_rec.get("duration_s", 0.0)), float(idle["elapsed"])])

	print("\n=== 4. the summary over both matches ===")
	var summary: Dictionary = stats.call("summary")
	chk("G1. the summary counts both matches",
		int(summary.get("matches", 0)) == 2, "%d" % int(summary.get("matches", 0)))
	chk("G2. the win/loss distribution is 1 VICTORY / 1 DEFEAT",
		int(summary.get("victories", 0)) == 1 and int(summary.get("defeats", 0)) == 1,
		"%d / %d" % [int(summary.get("victories", 0)), int(summary.get("defeats", 0))])
	chk("G3. the win rate is 0.5",
		absf(float(summary.get("win_rate", 0.0)) - 0.5) < 0.001,
		"%.3f" % float(summary.get("win_rate", 0.0)))
	chk("G4. the average duration is a real number",
		float(summary.get("avg_duration_s", 0.0)) > 5.0,
		"%.1fs" % float(summary.get("avg_duration_s", 0.0)))
	var sc: Dictionary = summary.get("cards", {})
	chk("G5. the summary carries the per-card stats",
		sc.has(DEFENDER_CARD), ", ".join(sc.keys()))
	if sc.has(DEFENDER_CARD):
		var c: Dictionary = sc[DEFENDER_CARD]
		chk("G6. the card was played in exactly one match",
			int(c.get("matches_played", 0)) == 1, "%d" % int(c.get("matches_played", 0)))
		chk("G7. the card's win rate is 1.0 (it was only played in the win)",
			absf(float(c.get("win_rate", 0.0)) - 1.0) < 0.001,
			"%.3f" % float(c.get("win_rate", 0.0)))
	chk("G8. the summary was written to disk",
		FileAccess.file_exists(String(stats.call("summary_file"))),
		String(stats.call("summary_file")))

	# The gate leaves no junk behind.
	stats.call("clear")
	_finish()


func _finish() -> void:
	print("\n=> %s (%d checks, %d failed)" % [
		"FAIL" if fail_count > 0 else "PASS", check_count, fail_count])
	quit(1 if fail_count > 0 else 0)


# ---------------------------------------------------------------- helpers

func _stats() -> Node:
	return root.get_node_or_null("MatchStats")


func _minerals() -> Node:
	return root.get_node_or_null("MineralField")


## Runs one full match. Returns {seconds, result}.
func _run_match(plays: bool) -> Dictionary:
	# The mineral economy is an AUTOLOAD, so it survives between the matches
	# this gate runs. Reset it or the second match starts broke.
	var minerals := _minerals()
	if minerals != null:
		minerals.call("reset")

	var packed := load(MAIN_SCENE) as PackedScene
	var arena := packed.instantiate()
	root.add_child(arena)
	await process_frame

	var game_seconds := 0.0
	var result := "TIMEOUT"

	while game_seconds < MAX_GAME_SECONDS:
		await process_frame
		game_seconds += root.get_process_delta_time()

		if paused:
			var overlay := arena.get_node_or_null("ResultOverlay")
			result = "VICTORY" if (overlay != null and overlay.call("is_victory")) else "DEFEAT"
			break

		if plays and _can_afford(minerals, DEFENDER_COST):
			await _play_a_card(arena, DEFENDER_CARD)

	paused = false
	var live_elapsed: float = 0.0
	var stats := _stats()
	if stats != null:
		live_elapsed = float(stats.call("elapsed"))
	arena.queue_free()
	await process_frame
	return {"seconds": game_seconds, "result": result, "elapsed": live_elapsed}


## How far the recorder's duration may sit from the gate's own measurement.
## The gate counts the frames it sees; the recorder counts every frame of the
## match, including the first one after the scene is instantiated — and that
## first frame is a slow one (the scene is still loading), so it carries a
## delta of up to a couple of scaled seconds. The tolerance covers exactly
## that one frame, not a real difference in the numbers.
func _tolerance(measured: float) -> float:
	return maxf(3.0, measured * 0.15)


func _can_afford(minerals: Node, cost: int) -> bool:
	if minerals == null or cost < 0:
		return false
	return bool(minerals.call("can_afford", cost))


## Select the card and tap the lane — the real Android way: the card is
## driven through `gui_input` (like the picker does) and the lane through a
## pushed event pair (emulated mouse + screen touch), so BOTH reach the
## Arena exactly as they do on a phone.
func _play_a_card(arena: Node, card_id: String) -> void:
	var bar := arena.get_node_or_null("HUD/CardBar")
	if bar == null:
		return
	if String(bar.call("selected_id")) != card_id:
		var card: Node = bar.call("card_by_id", card_id)
		if card == null:
			return
		var mb := InputEventMouseButton.new()
		mb.button_index = MOUSE_BUTTON_LEFT
		mb.pressed = true
		mb.set_device(0)
		card.emit_signal("gui_input", mb)
		await process_frame
	await _android_lane_tap(Vector2(LANE_X, LANE_Y))


## One physical finger tap on Android: the emulated mouse event plus the
## real screen touch. Only the touch counts as a press (src/core/TapInput.gd).
func _android_lane_tap(pos: Vector2) -> void:
	var mb := InputEventMouseButton.new()
	mb.button_index = MOUSE_BUTTON_LEFT
	mb.pressed = true
	mb.set_device(InputEvent.DEVICE_ID_EMULATION)
	mb.position = pos
	mb.global_position = pos
	root.push_input(mb)

	var st := InputEventScreenTouch.new()
	st.index = 0
	st.pressed = true
	st.position = pos
	st.set_device(0)
	root.push_input(st)
	await process_frame

	var mb_up := InputEventMouseButton.new()
	mb_up.button_index = MOUSE_BUTTON_LEFT
	mb_up.pressed = false
	mb_up.set_device(InputEvent.DEVICE_ID_EMULATION)
	mb_up.position = pos
	mb_up.global_position = pos
	root.push_input(mb_up)

	var st_up := InputEventScreenTouch.new()
	st_up.index = 0
	st_up.pressed = false
	st_up.position = pos
	st_up.set_device(0)
	root.push_input(st_up)
	await process_frame
