extends SceneTree
## Starforge static-sprite acceptance — engine side (Godot 4.6).
##
## Companion to tools/accept_sprite_import.gd (animated units) and
## tools/sprite_qa.py (pixel side). For art that has no animation track:
##   brief §2.2 towers (40x60, intact/damaged per tower)
##   brief §2.3 UI icons (16x16 / 32x32 / 64x64 / 12x12), card frame (48x64)
##   brief §2.3 battlefield background (720x1280)
##
## Manifest-driven: the expected set is read from the unit's frames JSON, so the
## same script covers every static batch (it previously hard-coded 6 tower
## names at 40x60 and could not check UI art at all).
##
## Usage (from the repo root):
##   godot --headless --import
##   godot --headless --script tools/accept_static_sprites.gd -- \
##       res://assets/sprites/towers/towers_frames.json
##   # a directory also works — the manifest is auto-discovered:
##   godot --headless --script tools/accept_static_sprites.gd -- \
##       res://assets/sprites/towers
##
## Exit code 0 = PASS, 1 = FAIL.

var fail_count := 0

func chk(name: String, cond: bool, detail: String = "") -> void:
	if not cond:
		fail_count += 1
	print(("PASS  " if cond else "FAIL  ") + name + ("   " + detail if detail != "" else ""))

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.is_empty():
		print("FAIL  no manifest JSON given")
		print("usage: godot --headless --script tools/accept_static_sprites.gd -- res://assets/sprites/<set>/<set>_frames.json")
		quit(1)
		return
	var manifest_path: String = args[0]
	var dir := manifest_path.get_base_dir()
	if not manifest_path.ends_with(".json"):
		# directory given: auto-discover the manifest
		dir = manifest_path if manifest_path.ends_with("/") else manifest_path + "/"
		manifest_path = ""
		var da := DirAccess.open(dir)
		if da != null:
			for file in da.get_files():
				if file.ends_with("_frames.json"):
					manifest_path = dir + file
					break
		if manifest_path == "":
			print("FAIL  no *_frames.json manifest found in " + dir)
			quit(1)
			return

	var f := FileAccess.open(manifest_path, FileAccess.READ)
	if f == null:
		print("FAIL  cannot open manifest " + manifest_path)
		quit(1)
		return
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	var data: Dictionary = parsed
	var frames: Array = data.get("frames", [])
	if frames.is_empty():
		print("FAIL  manifest has no frames: " + manifest_path)
		quit(1)
		return
	print("manifest: " + manifest_path + "  (" + str(frames.size()) + " static sprites)")
	print("")

	for fr_v in frames:
		var fr: Dictionary = fr_v
		var spr_name: String = str(fr["name"])
		var want := Vector2i(int(fr["w"]), int(fr["h"]))
		var path := dir + "/" + spr_name + ".png"

		if not ResourceLoader.exists(path):
			chk(spr_name + " texture loads", false, path)
			continue
		var tex := load(path) as Texture2D
		if tex == null:
			chk(spr_name + " texture loads", false, path)
			continue
		var img := tex.get_image()
		if img == null:
			chk(spr_name + " texture loads", false, path)
			continue
		chk(spr_name + " texture loads", true, "%dx%d" % [img.get_width(), img.get_height()])
		chk(spr_name + " size is " + str(want.x) + "x" + str(want.y),
			img.get_width() == want.x and img.get_height() == want.y,
			"%dx%d" % [img.get_width(), img.get_height()])

		# alpha must be strictly binary: 0 or 1, no feathered/soft edges
		var soft := 0
		for y in range(img.get_height()):
			for x in range(img.get_width()):
				var a := img.get_pixel(x, y).a
				if a > 0.001 and a < 0.999:
					soft += 1
		chk(spr_name + " alpha is binary (0/1)", soft == 0, "soft px: %d" % soft)

		# opaque colour budget: brief §3 caps the shared palette at 16
		var opaque_cols := {}
		for y in range(img.get_height()):
			for x in range(img.get_width()):
				var c := img.get_pixel(x, y)
				if c.a > 0.5:
					opaque_cols[c.r8 * 65536 + c.g8 * 256 + c.b8] = true
		chk(spr_name + " <= 16 opaque colours", opaque_cols.size() <= 16,
			str(opaque_cols.size()) + " colours")

		chk(spr_name + " .import present", FileAccess.file_exists(path + ".import"))

	# container sheets, when the manifest declares them
	if data.has("strip"):
		var strip_path := dir + "/" + str(data["strip"])
		var stex := load(strip_path) as Texture2D
		if stex == null:
			chk("strip texture loads", false, strip_path)
		else:
			var want_s := Vector2i(int(data["strip_size"][0]), int(data["strip_size"][1]))
			chk("strip loads at " + str(want_s.x) + "x" + str(want_s.y),
				stex.get_width() == want_s.x and stex.get_height() == want_s.y,
				"%dx%d" % [stex.get_width(), stex.get_height()])
			chk("strip .import present", FileAccess.file_exists(strip_path + ".import"))
	if data.has("grid"):
		var grid_path := dir + "/" + str(data["grid"])
		var gtex := load(grid_path) as Texture2D
		if gtex == null:
			chk("grid texture loads", false, grid_path)
		else:
			var want_g := Vector2i(int(data["grid_size"][0]), int(data["grid_size"][1]))
			chk("grid loads at " + str(want_g.x) + "x" + str(want_g.y),
				gtex.get_width() == want_g.x and gtex.get_height() == want_g.y,
				"%dx%d" % [gtex.get_width(), gtex.get_height()])
			chk("grid .import present", FileAccess.file_exists(grid_path + ".import"))

	print("\n=> " + ("FAIL (" + str(fail_count) + " checks failed)" if fail_count > 0 else "PASS"))
	quit(1 if fail_count > 0 else 0)
