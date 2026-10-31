extends Node
## MatchStats — per-match pacing telemetry, written to disk (v0.3 prep).
##
## WHY (2026-10-31): the v0.3 Pacing Pass retunes lane speed, AI cadence and
## tower HP against a ~3-minute match. Every number in that retune has to come
## from played matches, not from estimates — the same lesson that caught the
## v0.1 wording ("3-minute match" vs the measured ~30s). This node records
## what actually happened in every match and writes it where it can be pulled
## off the device.
##
## WHERE:
##   user://stats/matches.jsonl  — one JSON object per finished match
##   user://stats/summary.json   — the aggregate over every match on the box
## On Android user:// is the app's internal storage, so it comes off the
## device with:
##   adb shell run-as <pkg> cat files/stats/matches.jsonl
##
## ONE MATCH RECORD:
##   result        VICTORY / DEFEAT
##   duration_s    game seconds from match start to the result screen
##   taps          lane taps that landed inside the deploy band (player ops)
##   deploys       units the player actually deployed
##   card_selects  card taps
##   actions       taps + card_selects + deploys — the "how busy was the
##                 player" number the pacing pass tunes against
##   player_lost   player units that died
##   enemy_lost    enemy units the player killed
##   cards         per card: deployed / lost / alive
##
## The summary aggregates the win/loss DISTRIBUTION over every match on the
## device (victories / defeats / avg duration) and a per-card win rate:
## the card that is deployed in matches the player goes on to win is the card
## the retune should keep; the card that loses its matches is the card to fix.

const SCHEMA := 1

var _dir: String = "user://stats"
var _matches_file: String = "user://stats/matches.jsonl"
var _summary_file: String = "user://stats/summary.json"

# per-match counters
var _active: bool = false
var _elapsed: float = 0.0
var _taps: int = 0
var _deploys: int = 0
var _card_selects: int = 0
var _minerals_spent: int = 0
var _player_lost: int = 0
var _enemy_lost: int = 0
var _cards: Dictionary = {}

## Whether finished matches are written to disk. False in a headless gate
## run — see _ready().
var persist: bool = true


func _ready() -> void:
	# A headless GATE runs the arena with `--script`. Those matches are
	# synthetic (a script taps the lane), and the v0.3 retune reads the real
	# pacing file — so a gate must never add a fake match to it. The gates
	# that test the recorder itself call set_output_dir(), which turns
	# persistence back on for that folder only.
	if OS.get_cmdline_args().has("--script"):
		persist = false


func _process(delta: float) -> void:
	# The autoload is PROCESS_MODE_INHERIT, so it stops when the tree is
	# paused — the result screen pauses the match, which is exactly where the
	# clock has to stop.
	if not _active:
		return
	_elapsed += delta


# ---------------------------------------------------------------- lifecycle

## Start a fresh match. Called by the arena when it appears (and therefore
## again after every RESTART, because the scene is reloaded).
func begin_match() -> void:
	_elapsed = 0.0
	_taps = 0
	_deploys = 0
	_card_selects = 0
	_minerals_spent = 0
	_player_lost = 0
	_enemy_lost = 0
	_cards = {}
	_active = true


## Finish the match and write it out. Returns the record that was written.
func end_match(result: String) -> Dictionary:
	_active = false
	var record := build_record(result)
	if not persist:
		return record
	_append_line(JSON.stringify(record))
	_write_summary()
	return record


## The elapsed game time of the match in progress (0 when no match runs).
func elapsed() -> float:
	return _elapsed


## The record for the match as it stands. Public so the acceptance gate can
## compare the file on disk with the live counters.
func build_record(result: String) -> Dictionary:
	var cards: Dictionary = {}
	for id in _cards.keys():
		var e: Dictionary = _cards[id]
		var deployed: int = int(e.get("deployed", 0))
		var lost: int = int(e.get("lost", 0))
		cards[id] = {
			"deployed": deployed,
			"lost": lost,
			"alive": maxi(deployed - lost, 0),
		}
	return {
		"schema": SCHEMA,
		"ts": Time.get_datetime_string_from_system(true),
		"unix": int(Time.get_unix_time_from_system()),
		"build": ProjectSettings.get_setting("application/config/version", ""),
		"result": result,
		"duration_s": snappedf(_elapsed, 0.01),
		"taps": _taps,
		"deploys": _deploys,
		"card_selects": _card_selects,
		"actions": _taps + _card_selects + _deploys,
		"minerals_spent": _minerals_spent,
		"player_lost": _player_lost,
		"enemy_lost": _enemy_lost,
		"cards": cards,
	}


# ---------------------------------------------------------------- recording

## A lane tap that landed inside the deploy band.
func note_tap() -> void:
	_taps += 1


## A card was tapped (selected or deselected).
func note_card_select() -> void:
	_card_selects += 1


## The player deployed `card_id` for `cost` minerals.
func note_deploy(card_id: String, cost: int) -> void:
	_deploys += 1
	_minerals_spent += cost
	_card_entry(card_id)["deployed"] = int(_card_entry(card_id)["deployed"]) + 1


## One of the player's units died.
func note_player_unit_lost(card_id: String) -> void:
	_player_lost += 1
	_card_entry(card_id)["lost"] = int(_card_entry(card_id)["lost"]) + 1


## One of the enemy's units died.
func note_enemy_unit_lost() -> void:
	_enemy_lost += 1


func _card_entry(card_id: String) -> Dictionary:
	if not _cards.has(card_id):
		_cards[card_id] = {"deployed": 0, "lost": 0}
	return _cards[card_id]


# ---------------------------------------------------------------- reading

## Every match record on disk, oldest first.
func records() -> Array:
	var out: Array = []
	if not FileAccess.file_exists(_matches_file):
		return out
	var f := FileAccess.open(_matches_file, FileAccess.READ)
	if f == null:
		return out
	while not f.eof_reached():
		var line := f.get_line()
		if line.strip_edges() == "":
			continue
		var parsed: Variant = JSON.parse_string(line)
		if parsed is Dictionary:
			out.append(parsed)
	f.close()
	return out


## The aggregate over every match on the device.
func summary() -> Dictionary:
	var recs := records()
	var victories: int = 0
	var defeats: int = 0
	var duration_sum: float = 0.0
	var deploy_sum: int = 0
	var action_sum: int = 0
	var per_card: Dictionary = {}
	for r in recs:
		var result := String(r.get("result", "UNKNOWN"))
		if result == "VICTORY":
			victories += 1
		elif result == "DEFEAT":
			defeats += 1
		duration_sum += float(r.get("duration_s", 0.0))
		deploy_sum += int(r.get("deploys", 0))
		action_sum += int(r.get("actions", 0))
		var cards: Dictionary = r.get("cards", {})
		for id in cards.keys():
			var e: Dictionary = cards[id]
			if not per_card.has(id):
				per_card[id] = {
					"deployed": 0, "lost": 0, "alive": 0,
					"matches_played": 0, "matches_won": 0,
				}
			var c: Dictionary = per_card[id]
			c["deployed"] = int(c["deployed"]) + int(e.get("deployed", 0))
			c["lost"] = int(c["lost"]) + int(e.get("lost", 0))
			c["alive"] = int(c["alive"]) + int(e.get("alive", 0))
			c["matches_played"] = int(c["matches_played"]) + 1
			if result == "VICTORY":
				c["matches_won"] = int(c["matches_won"]) + 1
	var n: int = recs.size()
	for id in per_card.keys():
		var c: Dictionary = per_card[id]
		var played: int = int(c["matches_played"])
		c["win_rate"] = snappedf(float(c["matches_won"]) / float(played), 0.001) if played > 0 else 0.0
	return {
		"schema": SCHEMA,
		"updated": Time.get_datetime_string_from_system(true),
		"matches": n,
		"victories": victories,
		"defeats": defeats,
		"win_rate": snappedf(float(victories) / float(n), 0.001) if n > 0 else 0.0,
		"avg_duration_s": snappedf(duration_sum / float(n), 0.01) if n > 0 else 0.0,
		"avg_deploys": snappedf(float(deploy_sum) / float(n), 0.01) if n > 0 else 0.0,
		"avg_actions": snappedf(float(action_sum) / float(n), 0.01) if n > 0 else 0.0,
		"cards": per_card,
	}


func matches_file() -> String:
	return _matches_file


func summary_file() -> String:
	return _summary_file


## Point the recorder at another folder (used by the acceptance gate so it
## never pollutes the real stats, and by a future "export" flow).
## Explicitly turning persistence ON: a gate run has it off by default.
func set_output_dir(path: String) -> void:
	_dir = path
	_matches_file = path + "/matches.jsonl"
	_summary_file = path + "/summary.json"
	persist = true


## Delete everything this recorder wrote. Used by the acceptance gate to
## start from a clean slate.
func clear() -> void:
	for path in [_matches_file, _summary_file]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))


# ---------------------------------------------------------------- writing

func _ensure_dir() -> void:
	if DirAccess.dir_exists_absolute(ProjectSettings.globalize_path(_dir)):
		return
	DirAccess.make_dir_recursive_absolute(_dir)


func _append_line(json: String) -> void:
	_ensure_dir()
	var mode: int = FileAccess.WRITE
	if FileAccess.file_exists(_matches_file):
		mode = FileAccess.READ_WRITE
	var f := FileAccess.open(_matches_file, mode)
	if f == null:
		push_error("MatchStats: cannot open %s for writing" % _matches_file)
		return
	if mode == FileAccess.READ_WRITE:
		f.seek_end()
	f.store_line(json)
	f.close()


func _write_summary() -> void:
	_ensure_dir()
	var f := FileAccess.open(_summary_file, FileAccess.WRITE)
	if f == null:
		push_error("MatchStats: cannot open %s for writing" % _summary_file)
		return
	f.store_string(JSON.stringify(summary(), "  "))
	f.close()
