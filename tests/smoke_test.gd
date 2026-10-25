extends Node
## v0.1 skeleton smoke test — headless functional check.
## Run: godot --headless --quit-after 600 res://tests/smoke_test.tscn
##
## Checks the four things that actually exist in the skeleton:
##   1. Mineral economy (start value, max, regen tick)
##   2. Unit stat blocks (Marine / Hellion) survive scene instantiation
##   3. Spawn flow (input -> unit created -> minerals spent)
##   4. Combat flow (two opposing units find each other and deal damage)
##
## Exits 0 on pass, 1 on any failure.

var _fails: int = 0
var _checks: int = 0

var _hp_marine: int = 0
var _hp_hellion: int = 0
var _died_marine: bool = false
var _died_hellion: bool = false


func _ready() -> void:
	print("=== starforge v0.1 skeleton smoke test ===")
	await get_tree().process_frame

	_check_economy()
	await _check_regen()
	_check_unit_stats()
	await _check_spawn()
	await _check_combat()

	print("--- result: %d/%d passed, %d failed ---" % [_checks - _fails, _checks, _fails])
	get_tree().quit(1 if _fails > 0 else 0)


func _ok(label: String, condition: bool, detail: String = "") -> void:
	_checks += 1
	if condition:
		print("  PASS  %s %s" % [label, detail])
	else:
		_fails += 1
		print("  FAIL  %s %s" % [label, detail])


func _check_economy() -> void:
	print("[1] economy")
	_ok("minerals start == 5", MineralField.current() == 5, "(got %d)" % MineralField.current())
	_ok("can_afford(3) == true", MineralField.can_afford(3))


func _check_regen() -> void:
	print("[2] mineral regen (1 per 2.0s)")
	var before: int = MineralField.current()
	await get_tree().create_timer(2.3).timeout
	var after: int = MineralField.current()
	_ok("regen +1 over 2.3s", after == before + 1, "(%d -> %d)" % [before, after])


func _check_unit_stats() -> void:
	print("[3] unit stat blocks")
	var marine: Node = load("res://scenes/units/marine.tscn").instantiate()
	var hellion: Node = load("res://scenes/units/hellion.tscn").instantiate()
	_ok("marine is Unit", marine is Unit)
	_ok("hellion is Unit", hellion is Unit)
	if marine is Unit:
		_ok("marine hp/dmg/spd == 200/25/90",
			marine.max_hp == 200 and marine.damage == 25 and marine.move_speed == 90,
			"(got %d/%d/%d)" % [marine.max_hp, marine.damage, marine.move_speed])
	if hellion is Unit:
		_ok("hellion hp/dmg/spd == 350/30/130",
			hellion.max_hp == 350 and hellion.damage == 30 and hellion.move_speed == 130,
			"(got %d/%d/%d)" % [hellion.max_hp, hellion.damage, hellion.move_speed])
	marine.free()
	hellion.free()


func _check_spawn() -> void:
	print("[4] spawn flow (input -> unit -> minerals spent)")
	# Park the economy at max so regen cannot race the assertion.
	MineralField._current = MineralField.MAX
	var before: int = MineralField.current()

	var marker: Marker2D = Marker2D.new()
	marker.position = Vector2(100, 360)
	add_child(marker)

	var spawner: UnitSpawner = UnitSpawner.new()
	spawner.spawn_point = marker
	spawner.lane_y = 360.0
	add_child(spawner)

	var ev: InputEventKey = InputEventKey.new()
	ev.keycode = KEY_1
	ev.pressed = true
	spawner._unhandled_input(ev)

	var units: Array = get_tree().get_nodes_in_group("units")
	_ok("one unit spawned", units.size() == 1, "(got %d)" % units.size())
	_ok("minerals spent 3", MineralField.current() == before - 3,
		"(%d -> %d)" % [before, MineralField.current()])
	if units.size() == 1:
		var u: Node = units[0]
		_ok("spawned unit is a Marine", u is Marine)
		_ok("spawned unit sits on lane 360", absf((u as Unit).lane_y - 360.0) < 0.5)

	# A unit we cannot afford must not spawn.
	MineralField._current = 0
	var units_before: int = get_tree().get_nodes_in_group("units").size()
	spawner._unhandled_input(ev)
	_ok("no spawn when unaffordable",
		get_tree().get_nodes_in_group("units").size() == units_before)


func _check_combat() -> void:
	print("[5] combat flow (opposing units engage)")
	# Clean slate: remove everything spawned above.
	for n in get_tree().get_nodes_in_group("units"):
		n.queue_free()
	await get_tree().process_frame

	var marine: Node = load("res://scenes/units/marine.tscn").instantiate()
	var hellion: Node = load("res://scenes/units/hellion.tscn").instantiate()
	(marine as Unit).lane_y = 360.0
	(hellion as Unit).lane_y = 360.0
	(marine as Unit).team = 0
	(hellion as Unit).team = 1
	add_child(marine)
	add_child(hellion)
	marine.global_position = Vector2(100, 360)
	hellion.global_position = Vector2(200, 360)
	marine.add_to_group("units")
	hellion.add_to_group("units")

	_hp_marine = (marine as Unit).max_hp
	_hp_hellion = (hellion as Unit).max_hp
	marine.died.connect(func(_u): _died_marine = true)
	hellion.died.connect(func(_u): _died_hellion = true)
	marine.damaged.connect(func(_u, hp): _hp_marine = hp)
	hellion.damaged.connect(func(_u, hp): _hp_hellion = hp)

	await get_tree().create_timer(2.0).timeout

	_ok("combat resolved (damage or death)",
		_hp_marine < 200 or _hp_hellion < 350 or _died_marine or _died_hellion,
		"(marine hp %d, hellion hp %d)" % [_hp_marine, _hp_hellion])
	_ok("hellion charge landed (3x first hit => marine took >=90)",
		_hp_marine <= 110, "(marine hp %d)" % _hp_marine)
