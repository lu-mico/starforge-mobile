extends Node
## SfxBank — the engine-side SFX player (ASSET_UI_SPEC §5).
##
## The five SFX WAVs are delivered and accepted by `tools/accept_sfx.gd`, but
## until something PLAYS them they are just files on disk. This autoload
## (`Sfx` in project.godot) is that "something": the single place that owns
## the AudioStreamPlayers and the volume policy, so gameplay code only ever
## says `Sfx.play("hit")`.
##
## Policy (ASSET_UI_SPEC §5):
##   * plain AudioStreamPlayer, no bus routing
##   * engine-side `volume_db`, nothing baked into the files
##   * one-shot, non-looping
##   * a small player pool, so two hits in the same frame both sound
##
## The counters exist so the acceptance gate can assert that an EVENT fired
## a sound, without anybody having to listen to it.

const STREAMS: Dictionary = {
	"deploy": preload("res://assets/audio/sfx/sfx_deploy.wav"),
	"hit": preload("res://assets/audio/sfx/sfx_hit.wav"),
	"death": preload("res://assets/audio/sfx/sfx_death.wav"),
	"mineral": preload("res://assets/audio/sfx/sfx_mineral.wav"),
	"win": preload("res://assets/audio/sfx/sfx_win.wav"),
}

## Per-sound engine gain. Loudness is balanced HERE, not in the files.
const VOLUME_DB: Dictionary = {
	"deploy": -9.0,
	"hit": -11.0,
	"death": -8.0,
	"mineral": -15.0,
	"win": -4.0,
}

const POOL_SIZE: int = 8

## sfx id -> how many times it was played (read by the acceptance gate).
var play_counts: Dictionary = {}
## The id of the most recently played sound (read by the acceptance gate).
var last_played: String = ""

var _players: Array[AudioStreamPlayer] = []
var _next: int = 0


func _ready() -> void:
	for key in STREAMS.keys():
		play_counts[key] = 0
	_ensure_players()


## Play the sound `id`. Returns false for an unknown id.
func play(id: String, volume_db: float = 0.0, pitch: float = 1.0) -> bool:
	if not STREAMS.has(id):
		push_warning("SfxBank: unknown sfx id '%s'" % id)
		return false
	_ensure_players()
	var player := _claim_player()
	player.stream = STREAMS[id]
	player.volume_db = float(VOLUME_DB.get(id, -10.0)) + volume_db
	player.pitch_scale = pitch
	player.play()
	play_counts[id] = int(play_counts.get(id, 0)) + 1
	last_played = id
	return true


## The match-end sting. The spec ships ONE result sound ("胜负 sting"), so a
## defeat plays it a fifth lower — the sting is the same, the mood is not.
func play_result(victory: bool) -> bool:
	return play("win", 0.0, 1.0 if victory else 0.75)


## How many times `id` was played.
func count_of(id: String) -> int:
	return int(play_counts.get(id, 0))


## The id of the most recently played sound.
func last_played_id() -> String:
	return last_played


## Silence everything (used when the match restarts).
func stop_all() -> void:
	for p in _players:
		p.stop()


## Picks a player that is idle, or steals the oldest one when they are all
## busy (so a burst of hits never goes silent).
func _claim_player() -> AudioStreamPlayer:
	_ensure_players()
	for p in _players:
		if not p.playing:
			return p
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	return p


## Builds the player pool on demand. The pool lives under the autoload, so
## it survives a scene reload (the match-restart path) and never leaks.
func _ensure_players() -> void:
	if not _players.is_empty():
		return
	for i in POOL_SIZE:
		var p := AudioStreamPlayer.new()
		p.name = "SfxPlayer%d" % i
		add_child(p)
		_players.append(p)
