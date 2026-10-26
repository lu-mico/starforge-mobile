extends SceneTree
## Starforge SFX acceptance — engine side (Godot 4.6).
##
## Companion to tools/accept_sprite_import.gd (units), tools/accept_static_sprites.gd
## (static art) and tools/sfx_generator.py (the producer).
##
## Checks every SFX imports as an AudioStreamWAV with the right mix rate,
## channel count, duration and a peak at or below -6 dBFS (so overlapping
## sounds do not clip), and that the file ends on a fade (no click).
##
## Usage (from the repo root):
##   godot --headless --import
##   godot --headless --script tools/accept_sfx.gd -- res://assets/audio/sfx
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
		print("usage: godot --headless --script tools/accept_sfx.gd -- res://assets/audio/sfx")
		quit(1)
		return
	var dir := args[0]
	if not dir.ends_with("/"):
		dir += "/"

	var expected := {
		"sfx_deploy": [0.6, 1],
		"sfx_hit": [0.4, 1],
		"sfx_death": [0.8, 1],
		"sfx_mineral": [0.5, 1],
		"sfx_win": [2.0, 2],
	}

	for key in expected.keys():
		var sfx_name: String = String(key)
		var path: String = dir + sfx_name + ".wav"
		if not ResourceLoader.exists(path):
			chk(sfx_name + " imports", false, path)
			continue
		var stream := load(path) as AudioStreamWAV
		if stream == null:
			chk(sfx_name + " imports", false, path)
			continue
		chk(sfx_name + " imports as AudioStreamWAV", true)
		chk(sfx_name + " mix rate 44100", stream.mix_rate == 44100, str(stream.mix_rate))
		var want_ch: int = expected[key][1]
		chk(sfx_name + " channels", stream.stereo == (want_ch == 2),
			"stereo=%s" % str(stream.stereo))
		var dur: float = stream.get_length()
		var limit: float = expected[key][0]
		chk(sfx_name + " duration <= %.1fs" % limit, dur <= limit + 0.005, "%.3fs" % dur)
		var data := stream.data
		var n: int = data.size() / 2
		var peak := 0.0
		var last := 0
		for i in range(n):
			var v: int = data[i * 2] | (data[i * 2 + 1] << 8)
			if v >= 32768:
				v -= 65536
			var a: float = abs(float(v)) / 32768.0
			if a > peak:
				peak = a
			last = v
		chk(sfx_name + " peak <= -6 dBFS", peak <= 0.5013, "%.4f" % peak)
		chk(sfx_name + " ends on zero (no click)", abs(float(last)) / 32768.0 < 0.002,
			"%.6f" % (abs(float(last)) / 32768.0))

	print("=> " + ("FAIL" if fail_count > 0 else "PASS"))
	quit(1 if fail_count > 0 else 0)
