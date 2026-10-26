extends SceneTree
## Starforge static-sprite acceptance — engine side (Godot 4.6).
##
## Companion to tools/accept_sprite_import.gd (animated units) and
## tools/sprite_qa.py (pixel side). For art that has no animation track
## (brief §2.2 towers: 40x60, intact/damaged per tower).
##
## Usage (from the repo root):
##   godot --headless --import
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
		print("FAIL  no directory given")
		print("usage: godot --headless --script tools/accept_static_sprites.gd -- res://assets/sprites/towers")
		quit(1)
		return
	var dir := args[0]
	if not dir.ends_with("/"):
		dir += "/"

	var expected := {
		"player_tower_intact": Vector2i(40, 60),
		"player_tower_damaged": Vector2i(40, 60),
		"enemy_tower_intact": Vector2i(40, 60),
		"enemy_tower_damaged": Vector2i(40, 60),
		"king_tower_intact": Vector2i(40, 60),
		"king_tower_damaged": Vector2i(40, 60),
	}

	for key in expected.keys():
		var spr_name: String = String(key)
		var path: String = dir + spr_name + ".png"
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
		chk(spr_name + " size is 40x60", img.get_width() == 40 and img.get_height() == 60,
			"%dx%d" % [img.get_width(), img.get_height()])
		var soft := 0
		for y in range(img.get_height()):
			for x in range(img.get_width()):
				var a := img.get_pixel(x, y).a
				if a > 0.001 and a < 0.999:
					soft += 1
		chk(spr_name + " alpha is binary (0/1)", soft == 0, "soft px: %d" % soft)
		chk(spr_name + " .import present", FileAccess.file_exists(path + ".import"))

	print("=> " + ("FAIL" if fail_count > 0 else "PASS"))
	quit(1 if fail_count > 0 else 0)
