extends SceneTree
## Starforge ANDROID TAP acceptance — engine side (Godot 4.6).
##
## Why this gate exists (added 2026-10-29):
## The on-device run showed that tapping a card did NOTHING on the emulator:
## no select badge, the hint label never changed, and no unit ever spawned.
## The headless UI gate did not catch it because it pushes a single
## InputEventMouseButton. A real Android tap is NOT one event - Godot
## delivers BOTH:
##
##   1. the real InputEventScreenTouch
##   2. an emulated InputEventMouseButton (device -1)
##      (input_devices/pointing/emulate_mouse_from_touch is ON by default)
##
## Both were treated as a press, so ONE tap selected the card and then
## immediately deselected it again (CardBar treats a second press on the
## already-selected card as a toggle-off). Net result: the card hand was
## dead on a real phone while every headless gate stayed green.
##
## This gate replays the REAL Android event pair and asserts that one
## physical tap does exactly ONE thing:
##
##   A. tapping a card selects it, and it STAYS selected
##   B. tapping the lane deploys EXACTLY ONE unit
##   C. a mouse-only sequence still works (desktop / editor)
##
## NB on the harness: the headless root viewport is 100x100, so the GUI
## picker cannot reach a card that sits at y=1144 and the canvas transform
## is the identity. The card is therefore driven the way the picker drives
## it - `gui_input` emitted on the card node - while the lane is driven with
## a pushed input event, which does reach `_unhandled_input`. This is the
## same split the UI acceptance gate uses.
##
## Usage (from the repo root):
##   godot --headless --import
##   godot --headless --script tools/accept_tap_input.gd
##
## Exit code 0 = PASS, 1 = FAIL.

const MAIN_SCENE := "res://scenes/main/main.tscn"

## A lane tap in the middle of the battlefield (game coordinates).
const LANE_X := 240.0
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

	print("=== A. one Android tap on a card selects it (touch + emulated mouse) ===")
	await _check_android_card_tap()

	print("\n=== B. one Android tap on the lane deploys EXACTLY ONE unit ===")
	await _check_android_lane_tap()

	print("\n=== C. a mouse-only sequence still works (desktop / editor) ===")
	await _check_mouse_only()

	print("\n=> %s (%d checks, %d failed)" % [
		"FAIL" if fail_count > 0 else "PASS", check_count, fail_count])
	quit(1 if fail_count > 0 else 0)


# ---------------------------------------------------------------- helpers

func _arena() -> Node:
	# The mineral economy is an AUTOLOAD, so it survives between the arenas
	# this gate creates. Without this reset, the scenario that runs second
	# starts with whatever the first one spent and cannot afford a unit -
	# a harness leak, not a game bug.
	var minerals := root.get_node_or_null("MineralField")
	if minerals != null:
		minerals.call("reset")
	var packed := load(MAIN_SCENE) as PackedScene
	var arena := packed.instantiate()
	root.add_child(arena)
	return arena


func _card(arena: Node) -> Node:
	var bar := arena.get_node_or_null("HUD/CardBar")
	if bar == null:
		return null
	var cards := bar.get_children()
	return cards[0] if not cards.is_empty() else null


func _selected(arena: Node) -> String:
	var bar := arena.get_node_or_null("HUD/CardBar")
	return "" if bar == null else String(bar.call("selected_id"))


func _count_units(arena: Node) -> int:
	return arena.get_tree().get_nodes_in_group("units").size()


## The emulated mouse event Godot pairs with a screen touch.
func _emulated_mouse(pressed: bool) -> InputEventMouseButton:
	var mb := InputEventMouseButton.new()
	mb.button_index = MOUSE_BUTTON_LEFT
	mb.pressed = pressed
	mb.set_device(InputEvent.DEVICE_ID_EMULATION)
	return mb


## The real finger event.
func _touch(pressed: bool, pos: Vector2 = Vector2.ZERO) -> InputEventScreenTouch:
	var st := InputEventScreenTouch.new()
	st.index = 0
	st.pressed = pressed
	st.position = pos
	st.set_device(0)
	return st


## What the picker hands a Control for one Android finger-down: the emulated
## mouse press AND the real screen touch, in that order.
func _android_card_press(card: Node) -> void:
	card.emit_signal("gui_input", _emulated_mouse(true))
	card.emit_signal("gui_input", _touch(true))


func _android_lane_tap(pos: Vector2) -> void:
	var mb := _emulated_mouse(true)
	mb.position = pos
	mb.global_position = pos
	root.push_input(mb)
	root.push_input(_touch(true, pos))
	await process_frame
	var mb_up := _emulated_mouse(false)
	mb_up.position = pos
	mb_up.global_position = pos
	root.push_input(mb_up)
	root.push_input(_touch(false, pos))


func _mouse_tap(card: Node) -> void:
	var mb := InputEventMouseButton.new()
	mb.button_index = MOUSE_BUTTON_LEFT
	mb.pressed = true
	mb.set_device(0)
	card.emit_signal("gui_input", mb)


# ---------------------------------------------------------------- checks

func _check_android_card_tap() -> void:
	var arena := _arena()
	await process_frame
	var card := _card(arena)
	chk("the card bar has a card", card != null)
	if card == null:
		return

	_android_card_press(card)
	await process_frame

	chk("one Android tap SELECTS the marine card",
		_selected(arena) == "marine", _selected(arena))
	chk("the card STAYS selected (no toggle-off from the duplicate event)",
		_selected(arena) == "marine", _selected(arena))
	chk("the hint label reflects the selection",
		String(arena.get_node_or_null("HUD/HintLabel").get("text")).contains("Marine"),
		String(arena.get_node_or_null("HUD/HintLabel").get("text")))

	arena.queue_free()
	await process_frame


func _check_android_lane_tap() -> void:
	var arena := _arena()
	await process_frame
	var card := _card(arena)
	if card == null:
		chk("the card bar has a card", false)
		return

	_mouse_tap(card)
	await process_frame
	chk("the card is selected before the lane tap",
		_selected(arena) == "marine", _selected(arena))

	var before := _count_units(arena)
	await _android_lane_tap(Vector2(LANE_X, LANE_Y))
	var after := _count_units(arena)
	chk("one Android tap on the lane deploys EXACTLY ONE unit",
		after - before == 1, "spawned %d" % (after - before))

	arena.queue_free()
	await process_frame


func _check_mouse_only() -> void:
	var arena := _arena()
	await process_frame
	var card := _card(arena)
	if card == null:
		chk("the card bar has a card", false)
		return

	_mouse_tap(card)
	await process_frame
	chk("a mouse-only tap selects the card",
		_selected(arena) == "marine", _selected(arena))

	var before := _count_units(arena)
	var lane := InputEventMouseButton.new()
	lane.button_index = MOUSE_BUTTON_LEFT
	lane.pressed = true
	lane.set_device(0)
	lane.position = Vector2(LANE_X, LANE_Y)
	lane.global_position = lane.position
	root.push_input(lane)
	await process_frame
	await process_frame
	chk("a mouse-only lane tap deploys exactly one unit",
		_count_units(arena) - before == 1, "spawned %d" % (_count_units(arena) - before))

	arena.queue_free()
	await process_frame
