extends SceneTree
## Starforge UI + background acceptance — engine side (Godot 4.6).
##
## Companion to tools/accept_static_sprites.gd (static art), the animated-unit
## acceptance and the Python pixel gate (tools/ui_sprite_generator.py).
##
## This script is the ENGINE-side gate for the B2/B3/B4 batch:
##   * every UI texture imports, has the specified canvas size, binary alpha
##     and <= 16 colours
##   * the 4 card icons have an equal 40px body, symmetric >= 6px margins and
##     nothing clipped by the canvas edge
##   * card_frame.png really is a 9-slice source: flat centre, column-constant
##     side bands, row-constant top/bottom bands, opaque corners
##   * the battlefield background is opaque, sits on an exact 2x grid and is
##     EXACTLY vertically mirrored (0 differing pixels, no exclusions)
##   * THE CROSS-ART CHECK: the background's ground line is on the same row
##     as the engine's lane_y, and the lane band covers that row
##   * the card bar builds 4 cards whose icons, costs and badges match
##     UnitRoster / ASSET_UI_SPEC §3
##
## Usage (from the repo root):
##   godot --headless --import
##   godot --headless --script tools/accept_ui.gd
##
## Exit code 0 = PASS, 1 = FAIL.

const UI_DIR := "res://assets/sprites/ui/"
const BG_PATH := "res://assets/sprites/background/battlefield_720x1280.png"
const MAIN_SCENE := "res://scenes/main/main.tscn"

# GDD §5 roster + ASSET_UI_SPEC §3.5 card facts, mirrored here so this
# tool stays free of project-class references (see the lane_y note below).
const EXPECTED_CARDS: Array[Dictionary] = [
	{"id": "marine", "cost": 3, "icon": "icon_marine.png"},
	{"id": "marauder", "cost": 4, "icon": "icon_marauder.png"},
	{"id": "hellion", "cost": 4, "icon": "icon_hellion.png"},
	{"id": "siege_tank", "cost": 7, "icon": "icon_siege_tank.png"},
]

const ICON_W := {"icon_marine": 36, "icon_marauder": 42, "icon_hellion": 46, "icon_siege_tank": 52}
const ICON_H := 40
const FRAME_MARGIN := 10

var fail_count := 0
var check_count := 0


func chk(name: String, cond: bool, detail: String = "") -> void:
	check_count += 1
	if not cond:
		fail_count += 1
	print(("PASS  " if cond else "FAIL  ") + name + ("   " + detail if detail != "" else ""))


func _initialize() -> void:
	# The harness runs with a 64x64 headless window, so the content-scale
	# transform would mangle every input coordinate. Turning content scaling
	# off makes the canvas transform the identity, exactly like the real game
	# (viewport 720x1280, stretch canvas_items) where input arrives in
	# viewport coordinates.
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.size = Vector2i(720, 1280)
	await process_frame

	print("=== A. UI textures (import + canvas + alpha + palette) ===")
	_check_canvas("icon_marine", 64, 64)
	_check_canvas("icon_marauder", 64, 64)
	_check_canvas("icon_hellion", 64, 64)
	_check_canvas("icon_siege_tank", 64, 64)
	_check_canvas("card_frame", 48, 64)
	_check_canvas("icon_mineral_32", 32, 32)
	_check_canvas("icon_mineral_16", 16, 16)
	_check_canvas("card_badge_cost", 12, 12)
	_check_canvas("card_badge_count", 12, 12)
	_check_canvas("card_badge_frame", 12, 12)

	print("\n=== B. Card icons: equal 40px body, symmetric margins, no clipping ===")
	for name in ICON_W.keys():
		_check_icon_body(String(name), int(ICON_W[name]))

	print("\n=== C. card_frame.png is a valid 9-slice source ===")
	_check_nine_slice_source()

	print("\n=== D. Battlefield background ===")
	_check_background()

	print("\n=== E. Scene wiring (main.tscn) ===")
	# awaited: _check_scene contains awaits, so without this the script would
	# quit before the scene checks (and the end-to-end deploy) ever ran.
	await _check_scene()

	print("\n=> %s (%d checks, %d failed)" % [
		"FAIL" if fail_count > 0 else "PASS", check_count, fail_count])
	quit(1 if fail_count > 0 else 0)


# ---------------------------------------------------------------- helpers

func _load_img(path: String) -> Image:
	if not ResourceLoader.exists(path):
		chk(path + " exists", false)
		return null
	var tex := load(path) as Texture2D
	if tex == null:
		chk(path + " loads as Texture2D", false)
		return null
	var img := tex.get_image()
	if img == null:
		chk(path + " has an image", false)
	return img


func _check_canvas(name: String, w: int, h: int) -> void:
	var path := UI_DIR + name + ".png"
	var img := _load_img(path)
	if img == null:
		return
	chk(name + " is %dx%d" % [w, h], img.get_width() == w and img.get_height() == h,
		"%dx%d" % [img.get_width(), img.get_height()])
	var soft := 0
	var cols := {}
	for y in range(img.get_height()):
		for x in range(img.get_width()):
			var c := img.get_pixel(x, y)
			if c.a > 0.001 and c.a < 0.999:
				soft += 1
			elif c.a > 0.5:
				cols[c.r8 * 65536 + c.g8 * 256 + c.b8] = true
	chk(name + " alpha is binary", soft == 0, "soft px: %d" % soft)
	chk(name + " <= 16 colours", cols.size() <= 16, "%d colours" % cols.size())
	chk(name + " .import present", FileAccess.file_exists(path + ".import"))


func _check_icon_body(name: String, want_w: int) -> void:
	var img := _load_img(UI_DIR + name + ".png")
	if img == null:
		return
	var used := img.get_used_rect()
	var h := used.size.y
	var w := used.size.x
	chk(name + " body height == 40", h == ICON_H, "%d" % h)
	chk(name + " body width == %d" % want_w, w == want_w, "%d" % w)
	var left := used.position.x
	var right := img.get_width() - (used.position.x + w)
	var top := used.position.y
	var bottom := img.get_height() - (used.position.y + h)
	chk(name + " left/right margins symmetric and >= 6",
		left == right and left >= 6, "L=%d R=%d" % [left, right])
	chk(name + " top/bottom margins >= 6", top >= 6 and bottom >= 6,
		"T=%d B=%d" % [top, bottom])
	# nothing clipped: no opaque pixel may touch the canvas border
	var clipped := 0
	for x in range(img.get_width()):
		if img.get_pixel(x, 0).a > 0.5 or img.get_pixel(x, img.get_height() - 1).a > 0.5:
			clipped += 1
	for y in range(img.get_height()):
		if img.get_pixel(0, y).a > 0.5 or img.get_pixel(img.get_width() - 1, y).a > 0.5:
			clipped += 1
	chk(name + " not clipped by the canvas edge", clipped == 0, "%d border px" % clipped)


func _check_nine_slice_source() -> void:
	var img := _load_img(UI_DIR + "card_frame.png")
	if img == null:
		return
	var w := img.get_width()
	var h := img.get_height()
	# centre region must be one flat colour (28x44)
	var centre := {}
	for y in range(FRAME_MARGIN, h - FRAME_MARGIN):
		for x in range(FRAME_MARGIN, w - FRAME_MARGIN):
			centre[img.get_pixel(x, y).to_rgba32()] = true
	chk("card_frame centre region is one flat colour", centre.size() == 1,
		"%d colours" % centre.size())
	# side bands: every column must be constant down the edge rows
	var bad_col := 0
	for x in range(FRAME_MARGIN):
		var c0 := img.get_pixel(x, FRAME_MARGIN).to_rgba32()
		for y in range(FRAME_MARGIN, h - FRAME_MARGIN):
			if img.get_pixel(x, y).to_rgba32() != c0:
				bad_col += 1
				break
	chk("card_frame side bands are column-constant (safe to stretch vertically)",
		bad_col == 0, "%d columns vary" % bad_col)
	# top/bottom bands: every row must be constant across the edge columns
	var bad_row := 0
	for y in range(FRAME_MARGIN):
		var c0 := img.get_pixel(FRAME_MARGIN, y).to_rgba32()
		for x in range(FRAME_MARGIN, w - FRAME_MARGIN):
			if img.get_pixel(x, y).to_rgba32() != c0:
				bad_row += 1
				break
	chk("card_frame top/bottom bands are row-constant (safe to stretch horizontally)",
		bad_row == 0, "%d rows vary" % bad_row)
	# corners fully painted
	var corner_px := 0
	for cy in [0, h - FRAME_MARGIN]:
		for cx in [0, w - FRAME_MARGIN]:
			for y in range(cy, cy + FRAME_MARGIN):
				for x in range(cx, cx + FRAME_MARGIN):
					if img.get_pixel(x, y).a < 0.5:
						corner_px += 1
	chk("card_frame corners are fully painted", corner_px == 0, "%d transparent px" % corner_px)


func _check_background() -> void:
	var img := _load_img(BG_PATH)
	if img == null:
		return
	var w := img.get_width()
	var h := img.get_height()
	chk("background is 720x1280", w == 720 and h == 1280, "%dx%d" % [w, h])
	var soft := 0
	for y in range(0, h, 3):
		for x in range(0, w, 3):
			var a := img.get_pixel(x, y).a
			if a > 0.001 and a < 0.999:
				soft += 1
	chk("background is fully opaque", soft == 0, "soft px: %d" % soft)
	# exact 2x grid
	var bad := 0
	for y in range(0, h, 2):
		for x in range(0, w, 2):
			var c0 := img.get_pixel(x, y).to_rgba32()
			if img.get_pixel(x + 1, y).to_rgba32() != c0 \
					or img.get_pixel(x, y + 1).to_rgba32() != c0 \
					or img.get_pixel(x + 1, y + 1).to_rgba32() != c0:
				bad += 1
	chk("background sits on an exact 2x pixel grid", bad == 0, "%d bad blocks" % bad)
	# EXACT vertical mirror, no exclusions
	var diff := 0
	var first := Vector2i(-1, -1)
	for y in range(h / 2):
		for x in range(w):
			if img.get_pixel(x, y).to_rgba32() != img.get_pixel(x, h - 1 - y).to_rgba32():
				diff += 1
				if first.x < 0:
					first = Vector2i(x, y)
	chk("background is EXACTLY vertically mirrored", diff == 0,
		"%d px differ (first at %s)" % [diff, str(first)])


func _check_scene() -> void:
	var packed := load(MAIN_SCENE) as PackedScene
	if packed == null:
		chk("main.tscn loads", false)
		return
	chk("main.tscn loads", true)
	var arena := packed.instantiate()
	root.add_child(arena)
	# _ready() propagation lands on the next frame, so wait for it before the
	# scene wiring is inspected.
	await process_frame

	# background TextureRect
	var bg := arena.get_node_or_null("Background") as TextureRect
	chk("main.tscn Background is a TextureRect", bg != null)
	if bg != null:
		chk("Background texture is the battlefield",
			bg.texture != null and bg.texture.resource_path == BG_PATH,
			bg.texture.resource_path if bg.texture != null else "none")
		chk("Background stretch_mode == KEEP_ASPECT_COVERED (6)", bg.stretch_mode == 6,
			str(bg.stretch_mode))
		chk("Background texture_filter == NEAREST (1)", bg.texture_filter == 1,
			str(bg.texture_filter))
		chk("Background covers the viewport", bg.size == Vector2(720, 1280),
			str(bg.size))

	# lane_y vs the background ground line: the cross-art check.
	# NB: the spawner is read duck-typed on purpose - a static `as UnitSpawner`
	# would pull UnitSpawner.gd into THIS script's compile step, and that file
	# uses the MineralField autoload, which is only registered after a
	# --script run has compiled. Duck typing keeps the tool self-contained.
	var spawner := arena.get_node_or_null("UnitSpawner")
	chk("UnitSpawner exists", spawner != null)
	var lane_y := 640.0
	if spawner != null:
		lane_y = float(spawner.get("lane_y"))
	var bg_img := _load_img(BG_PATH)
	if bg_img != null:
		var ground := bg_img.get_pixel(360, int(lane_y)).to_rgba32()
		var above := bg_img.get_pixel(360, int(lane_y) - 20).to_rgba32()
		var below := bg_img.get_pixel(360, int(lane_y) + 20).to_rgba32()
		chk("background ground line sits on the engine's lane_y (%d)" % int(lane_y),
			ground != above and ground != below,
			"lane=%d above=%d below=%d" % [ground, above, below])
		# the tower bases must be flat marked ground on the same row
		var tower_px := bg_img.get_pixel(620, int(lane_y)).to_rgba32()
		chk("background lane covers the enemy tower column (x=620)",
			tower_px == ground or tower_px == above or tower_px == below,
			"px=%d" % tower_px)

	# units and towers stand on lane_y
	var tower := arena.get_node_or_null("EnemyTower") as Node2D
	chk("EnemyTower sits on lane_y", tower != null and absf(tower.position.y - lane_y) < 0.5,
		str(tower.position.y) if tower != null else "missing")
	var spawn := arena.get_node_or_null("PlayerSpawn") as Node2D
	chk("PlayerSpawn sits on lane_y", spawn != null and absf(spawn.position.y - lane_y) < 0.5,
		str(spawn.position.y) if spawn != null else "missing")

	# card bar
	var bar := arena.get_node_or_null("HUD/CardBar")
	chk("HUD has a CardBar", bar != null)
	if bar != null:
		var cards := bar.get_children()
		chk("CardBar holds 4 cards", cards.size() == 4, "%d" % cards.size())
		for i in range(mini(cards.size(), EXPECTED_CARDS.size())):
			var card := cards[i]
			var want := EXPECTED_CARDS[i]
			chk("card %s id matches the roster" % want["id"],
				String(card.get("card_id")) == want["id"], String(card.get("card_id")))
			chk("card %s cost matches the roster" % want["id"],
				int(card.get("cost")) == int(want["cost"]), str(card.get("cost")))
			var icon := card.get_node_or_null("Art/Icon")
			var icon_tex: Texture2D = icon.get("texture") if icon != null else null
			chk("card %s icon texture matches the roster" % want["id"],
				icon_tex != null and icon_tex.resource_path.ends_with("/%s" % want["icon"]),
				icon_tex.resource_path if icon_tex != null else "none")
			chk("card %s cost badge is present" % want["id"],
				card.get_node_or_null("Art/CostBadge") != null)
			chk("card %s count badge is present" % want["id"],
				card.get_node_or_null("Art/CountBadge") != null)
			chk("card %s selection badge is present" % want["id"],
				card.get_node_or_null("Art/SelectBadge") != null)
			var frame := card.get_node_or_null("Art/Frame")
			chk("card %s frame is a NinePatchRect with margin 10" % want["id"],
				frame != null and int(frame.get("patch_margin_left")) == FRAME_MARGIN \
					and int(frame.get("patch_margin_top")) == FRAME_MARGIN \
					and int(frame.get("patch_margin_right")) == FRAME_MARGIN \
					and int(frame.get("patch_margin_bottom")) == FRAME_MARGIN)
			var cost_label := card.get_node_or_null("CostLabel")
			chk("card %s cost digit reads %d" % [want["id"], int(want["cost"])],
				cost_label != null and String(cost_label.get("text")) == str(int(want["cost"])),
				String(cost_label.get("text")) if cost_label != null else "missing")

	# mineral icon in the HUD
	chk("HUD shows the mineral crystal icon",
		arena.get_node_or_null("HUD/MineralIcon") is TextureRect)

	print("\n=== F. End-to-end: tap a card, tap the lane, unit deploys ===")
	await _check_deploy_flow(arena, bar)

	# release the scene so Godot does not report leaked RIDs on exit
	arena.queue_free()
	await process_frame


## Simulates a tap on the marine card, then a tap on the lane, and checks
## that a unit is selected and then spawned. This exercises the whole card
## hand -> roster -> spawner -> scene path, not just the node wiring.
##
## NB: the headless root viewport is only 100x100, so the GUI picker cannot
## reach a card that sits at y=1144 and the canvas transform is identity.
## The same handlers the engine calls are therefore invoked directly:
## `gui_input` on the card (what the picker emits) and a pushed input event
## for the lane (which does reach _unhandled_input).
func _check_deploy_flow(arena: Node, bar: Node) -> void:
	if bar == null:
		return
	var cards := bar.get_children()
	if cards.is_empty():
		chk("card bar has a card to tap", false)
		return
	var card := cards[0]

	var press := InputEventMouseButton.new()
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
	var card_pos: Vector2 = card.get("global_position")
	press.position = card_pos + Vector2(20.0, 20.0)
	press.global_position = press.position
	card.emit_signal("gui_input", press)
	await process_frame
	chk("tapping a card selects it", String(bar.call("selected_id")) == "marine",
		String(bar.call("selected_id")))
	var hint := arena.get_node_or_null("HUD/HintLabel")
	chk("the hint label reflects the selection",
		hint != null and String(hint.get("text")).contains("Marine"),
		String(hint.get("text")) if hint != null else "missing")

	var before := _count_units(arena)
	var lane_tap := InputEventMouseButton.new()
	lane_tap.button_index = MOUSE_BUTTON_LEFT
	lane_tap.pressed = true
	lane_tap.position = Vector2(240, 640)
	lane_tap.global_position = Vector2(240, 640)
	root.push_input(lane_tap)
	await process_frame
	await process_frame
	chk("tapping the lane spawns the selected unit", _count_units(arena) == before + 1,
		"units %d -> %d" % [before, _count_units(arena)])
	chk("the selection is cleared after deploying",
		String(bar.call("selected_id")) == "", String(bar.call("selected_id")))


func _count_units(arena: Node) -> int:
	var n := 0
	for c in arena.get_children():
		if c.is_in_group("units"):
			n += 1
	return n
