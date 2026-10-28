extends Node
## MineralField — autoload singleton
## Starforge GDD §3: starting 5 / max 10 / regen 1 per 2.0s.
## Single source of truth for the mineral economy. UI / Spawner read from here.

signal minerals_changed(current: int, maximum: int)
signal minerals_spent(amount: int, remaining: int)

const STARTING: int = 5
const MAX: int = 10
const REGEN_INTERVAL: float = 2.0  # seconds per +1

var _current: int = STARTING
var _regen_accumulator: float = 0.0

func _ready() -> void:
	minerals_changed.emit(_current, MAX)

func _process(delta: float) -> void:
	if _current >= MAX:
		return
	_regen_accumulator += delta
	while _regen_accumulator >= REGEN_INTERVAL and _current < MAX:
		_regen_accumulator -= REGEN_INTERVAL
		_current += 1
		# The +1 must be audible: in a fight the mineral tick is the only
		# feedback that the economy is alive (ASSET_UI_SPEC §5).
		Sfx.play("mineral")
		minerals_changed.emit(_current, MAX)

func current() -> int:
	return _current

func can_afford(cost: int) -> bool:
	return _current >= cost

## Returns true on successful spend, false if insufficient.
func spend(cost: int) -> bool:
	if not can_afford(cost):
		return false
	_current -= cost
	minerals_spent.emit(cost, _current)
	minerals_changed.emit(_current, MAX)
	return true


## Puts the economy back to its starting state (5 / 10, no pending regen).
## Used when a match restarts: the autoload outlives the scene, so the
## previous match's minerals would otherwise carry over.
func reset() -> void:
	_current = STARTING
	_regen_accumulator = 0.0
	minerals_changed.emit(_current, MAX)
