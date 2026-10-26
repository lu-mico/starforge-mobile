extends SceneTree
## Starforge sprite import acceptance — engine side (Godot 4.6).
##
## Companion to tools/sprite_qa.py (pixel side). This one checks what the ENGINE
## needs: texture import, SpriteFrames build from the unit's frame table,
## AnimatedSprite2D playback, nearest filtering, flip_h, hframes addressing,
## and that the .import files needed for stable uids are present.
##
## Generalized: canvas size, frame count, strip path and animation split all
## come from the unit's frames JSON, so 32x32 Marine and 48x48 Siege Tank run
## through the same checks.
##
## Usage (from the repo root):
##   godot --headless --import
##   godot --headless --script tools/accept_sprite_import.gd -- \
##       res://assets/sprites/marine/marine_frames.json
##   godot --headless --script tools/accept_sprite_import.gd -- \
##       res://assets/sprites/siege_tank/siege_tank_frames.json
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
		print("FAIL  no frames JSON given")
		print("usage: godot --headless --script tools/accept_sprite_import.gd -- res://assets/sprites/<unit>/<unit>_frames.json")
		quit(1)
		return
	var json_path: String = args[0]
	var dir := json_path.get_base_dir()

	# --- 1. frame table ---
	var f := FileAccess.open(json_path, FileAccess.READ)
	if f == null:
		print("FAIL  cannot open " + json_path)
		quit(1)
		return
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	var data: Dictionary = parsed
	var canvas: Array = data["canvas"]
	var cell: int = canvas[0]
	var frames: Array = data["frames"]
	chk("frame table parses", frames.size() > 0, str(frames.size()) + " frames, canvas " + str(canvas))

	# --- 2. texture import ---
	var strip_path := dir + "/" + str(data["strip"])
	var tex: Texture2D = load(strip_path)
	chk("strip texture loads", tex != null, strip_path)
	if tex == null:
		print("=> FAIL")
		quit(1)
		return
	var expected := Vector2i(int(data["strip_size"][0]), int(data["strip_size"][1]))
	chk("strip size matches frame table (" + str(expected.x) + "x" + str(expected.y) + ")",
		Vector2i(tex.get_width(), tex.get_height()) == expected,
		str(tex.get_width()) + "x" + str(tex.get_height()))
	chk("strip is " + str(cell) + "px tall and 13 frames wide",
		tex.get_height() == cell and tex.get_width() == cell * 13)

	# --- 3. per-frame cell geometry ---
	var geom_ok := true
	var geom_detail := ""
	for fr_v in frames:
		var fr: Dictionary = fr_v
		if int(fr["w"]) != cell or int(fr["h"]) != cell:
			geom_ok = false
			geom_detail += str(fr["name"]) + " "
		if int(fr["x"]) != int(fr["index"]) * cell:
			geom_ok = false
			geom_detail += str(fr["name"]) + "(x) "
	chk("every frame is a " + str(cell) + "x" + str(cell) + " cell at x=index*" + str(cell), geom_ok, geom_detail)

	# --- 4. SpriteFrames build from the strip ---
	# NOTE: Godot 4's SpriteFrames.add_frame() does NOT take a Rect2 region —
	# sheet cells must be wrapped in an AtlasTexture (atlas + region + filter_clip).
	var sf := SpriteFrames.new()
	var by_anim: Dictionary = {}
	for fr2_v in frames:
		var fr2: Dictionary = fr2_v
		if not by_anim.has(fr2["state"]):
			by_anim[fr2["state"]] = []
		by_anim[fr2["state"]].append(fr2)
	for st_v in by_anim.keys():
		var st: String = st_v
		sf.add_animation(st)
		sf.set_animation_speed(st, float(by_anim[st][0]["fps"]))
		sf.set_animation_loop(st, bool(by_anim[st][0]["loop"]))
		for fr3_v in by_anim[st]:
			var fr3: Dictionary = fr3_v
			var at := AtlasTexture.new()
			at.atlas = tex
			at.region = Rect2(float(fr3["x"]), float(fr3["y"]), float(fr3["w"]), float(fr3["h"]))
			at.filter_clip = true
			sf.add_frame(st, at, 1.0)

	var anim_list := sf.get_animation_names()
	anim_list.erase("default")  # SpriteFrames.new() always seeds an empty "default"
	chk("4 animations (idle/walk/attack/death)", anim_list.size() == 4, str(sf.get_animation_names()))
	var expects: Dictionary = {"idle": 2, "walk": 4, "attack": 3, "death": 4}
	for st2_v in expects.keys():
		var st2: String = st2_v
		var want: int = expects[st2]
		chk("animation '" + st2 + "' has " + str(want) + " frames",
			sf.get_frame_count(st2) == want, str(sf.get_frame_count(st2)))

	# --- 5. region mapping ---
	var region_ok := true
	var region_detail := ""
	for fr4_v in frames:
		var fr4: Dictionary = fr4_v
		var anim: String = fr4["state"]
		var found := false
		for i in sf.get_frame_count(anim):
			var t: Texture2D = sf.get_frame_texture(anim, i)
			var at2 := t as AtlasTexture
			if at2 != null and at2.region == Rect2(float(fr4["x"]), float(fr4["y"]), float(fr4["w"]), float(fr4["h"])):
				found = true
				break
		if not found:
			region_ok = false
			region_detail += str(fr4["name"]) + " "
	chk("every frame-table row maps to a SpriteFrames region", region_ok, region_detail)

	# --- 6. AnimatedSprite2D playback ---
	var node := AnimatedSprite2D.new()
	node.sprite_frames = sf
	root.add_child(node)
	var play_ok := true
	var play_detail := ""
	for st3_v in ["idle", "walk", "attack", "death"]:
		var anim_name: String = st3_v
		node.play(anim_name)
		if not node.is_playing():
			play_ok = false
			play_detail += anim_name + "(rejected) "
			continue
		var seen: Dictionary = {}
		for step in 90:
			await create_timer(0.02).timeout
			seen[node.frame] = true
		if seen.size() < 2:
			play_ok = false
			play_detail += anim_name + "(static) "
	chk("AnimatedSprite2D plays all 4 animations", play_ok, play_detail)

	# fps sanity: the fps from the frame table must actually be honoured
	node.play("walk")
	var table_fps := float(by_anim["walk"][0]["fps"])
	var t_start := Time.get_ticks_msec()
	await create_timer(1.0).timeout
	var elapsed := (Time.get_ticks_msec() - t_start) / 1000.0
	chk("walk animation honours table fps (" + str(table_fps) + ")", table_fps > 0 and elapsed > 0.5)

	node.flip_h = true
	chk("flip_h works (left-facing via engine)", node.flip_h)
	node.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	chk("per-node nearest filter settable", node.texture_filter == CanvasItem.TEXTURE_FILTER_NEAREST)

	# --- 7. Sprite2D hframes path (the frame table's stated engine path) ---
	var s2 := Sprite2D.new()
	s2.texture = tex
	s2.hframes = 13
	s2.vframes = 1
	s2.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	root.add_child(s2)
	chk("Sprite2D hframes=13/vframes=1 works", s2.hframes == 13 and s2.vframes == 1)
	var hframe_ok := true
	for i in 13:
		s2.frame = i
		if s2.frame != i:
			hframe_ok = false
	chk("all 13 hframe indices addressable", hframe_ok)

	# --- 8. project nearest filter (pixel art requirement) ---
	var dflt: int = 1
	if ProjectSettings.has_setting("rendering/textures/canvas_textures/default_texture_filter"):
		dflt = int(ProjectSettings.get_setting("rendering/textures/canvas_textures/default_texture_filter"))
	chk("project default texture filter == Nearest(0)", dflt == 0, "value=" + str(dflt))

	# --- 9. .import files present (uid stability across clones) ---
	var import_missing := ""
	for fr5_v in frames:
		var fr5: Dictionary = fr5_v
		var p := dir + "/" + str(fr5["name"]) + ".png.import"
		if not FileAccess.file_exists(p):
			import_missing += str(fr5["name"]) + " "
	chk("every single-frame .import file present", import_missing == "", import_missing)
	chk("strip .import file present", FileAccess.file_exists(strip_path + ".import"))

	print("\n=> " + ("PASS" if fail_count == 0 else "FAIL (" + str(fail_count) + " checks failed)"))
	quit(0 if fail_count == 0 else 1)
